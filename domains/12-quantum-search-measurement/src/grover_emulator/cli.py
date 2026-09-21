"""The command line: one config in, one results directory out.

What a run does
---------------
``run`` loads and validates a configuration, generates the instance the configuration describes,
measures its marked set by enumeration, builds the oracle circuit in both lowerings, executes the
Grover circuit that the truth-table lowering produces, and writes ``results/{run_id}/`` containing
the configuration it validated, the results mapping (``metrics.json``), the figures, and
``report.md``. ``sweep`` does the same for circuit cost across the sweep's widths, without a curve.
``report`` re-renders the report from a finished results directory, which is the whole reason the
report is a view of a stored mapping rather than a side effect of computing one.

Three properties are load-bearing and each of them is a decision rather than a default.

**The iteration range is derived per instance.** ``sweep.iteration_range`` is ``null`` and stays
that way: the range comes from the spec's own optimum, ``range(0, k_opt + 2)``, so the window is
known to contain the peak. A fixed range is a way to produce a monotone rising curve that supports
no conclusion, so this module does not accept one from the configuration.

**A point that exceeds the memory budget is refused, never attempted.** The cost of a statevector is
``16 * 2**width`` bytes and it is computed before anything is allocated. An over-budget point is
recorded as a refusal with its reason and its size, and appears in the report's refusal table.
Attempting it and relying on the machine to swap or to die is the failure mode this check exists to
prevent — and it is what makes the arithmetic lowering's 50-qubit minimum a *measured* limitation
that the report states rather than a bug it hides.

**The result is the mapping, not the objects.** Everything the report and the figures read comes out
of one JSON-safe mapping, which is written to ``metrics.json`` before the report is rendered. A run
that crashed during rendering therefore still has its numbers, and a report can be regenerated,
diffed, or re-plotted without repeating a single simulation.

Optional collaborators
----------------------
:mod:`grover_emulator.backends` and :mod:`grover_emulator.analysis` own engine selection and the
statistical/structural analyses. They are imported lazily, by name, and their absence is recorded as
a reason rather than raised: a section whose collaborator is missing is printed as "not run" with
that reason. The CLI's own execution path calls the statevector engine directly through the project's
IR compiler, so a run always has something real to report.
"""

from __future__ import annotations

import importlib
import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import typer

from .circuits.compilers import relabel, to_qiskit
from .circuits.diffuser import build_diffuser
from .circuits.grover_circuit_builder import build_grover_circuit, derive_iteration_range
from .circuits.ir import GateList
from .circuits.phase_oracle import build_phase_oracle, oracle_width
from .config.schema import ExperimentConfig, OracleType, dump_config, load_config
from .problem.corpus_oracles import KeyMapMode, LMOtsChainSpec, ModeBKeyMapSpec
from .problem.oracle_spec import (
    HiddenPeriodOracleSpec,
    Lowering,
    OracleSpec,
    QLWROracleSpec,
    RandomControlOracleSpec,
)
from .problem.search_space import theoretical_optimal_iterations
from .reporting import plots
from .reporting.report_generator import (
    SCOPE_BOUNDARY,
    generate_report,
    generate_report_from_run_dir,
)
from .utils.logging_config import configure_logging
from .utils.seeding import RunSeeds

__all__ = ["app", "run_experiment", "run_sweep", "regenerate_report", "main_run", "main_sweep"]

DEFAULT_CONFIG = "config/default_experiment.yaml"
"""Where a run looks when it is not told otherwise."""

BYTES_PER_AMPLITUDE = 16
"""complex128: one real and one imaginary double, per amplitude."""

VALIDATION_ELEMENT_BUDGET = 2.0e9
"""Element operations a single exhaustive predicate check may cost before it is refused.

The check applies every gate to every reachable basis state, so its cost is ``gates * 2**n_search``
before the sandwich doubles it. The budget is where that stops being a couple of seconds: a check
that already costs more is recorded as not run with its estimate, rather than quietly turning a
two-minute run into an hour-long one.
"""

MAX_CLASSICAL_TRIAL_STATES = 1 << 22
"""Search spaces above this are not brute-forced for the baseline: the trial is a measurement, and a
measurement that takes longer than the simulation it is a baseline for is not worth taking."""

SCALING_TARGET_WIDTH = 128
"""The search width the scaling fit is projected to: the ``n = 128`` the scaled instances stand in for.

Nothing at this width is simulated, certified or counted, so every number reported for it is a
prediction and is keyed ``extrapolated_`` — the fit's gate count because it is a model evaluated
outside its measured range, the Grover query count because it is the closed form evaluated at a
width where no ``M`` was measured."""

CERTIFICATION_ELEMENT_BUDGET = 1 << 23
"""Predicate evaluations one instance certification may spend before the point is refused.

Certifying an instance means enumerating the whole search register and evaluating the relation on
every value — that is what makes ``M`` measured rather than assumed, and it costs ``2**n_search``
evaluations per candidate draw at roughly 8 microseconds each, measured. A draw that fails the
``M == 1`` test is not free, and the generator retries, so the cost of a point is the cost of a draw
times however many draws it takes.

That is unbounded in the worst case, and an unbounded cost is a refusal the sweep has to make *in
advance* rather than a run that never returns: this module's memory budget exists for the same
reason and fails for the same reason if it is only applied after the work. So the budget is spent
before the enumeration starts — the point is either affordable at a declared number of draws or it
is recorded as refused, with the per-draw cost and the budget in the reason.

The value is where a sweep point stops being interactive: 8.4 million evaluations is about a minute
of enumeration for one draw, and it admits the sweep's widths through 22 while refusing 24. The
refusal at 24 is a *cost* refusal, not a memory one, and the reason string says which.
"""


def _draws_affordable(n_search: int) -> int | None:
    """How many candidate draws a certification at this width may spend, or None if it may not.

    ``None`` means a single draw already exceeds the budget: the point is refused from the width,
    before a state is enumerated.
    """
    per_draw = 1 << n_search
    if per_draw > CERTIFICATION_ELEMENT_BUDGET:
        return None
    return max(1, CERTIFICATION_ELEMENT_BUDGET // per_draw)


def _certification_refusal(n_search: int) -> str:
    per_draw = 1 << n_search
    return (
        f"certifying an instance at n_search={n_search} costs one exhaustive pass over "
        f"2**{n_search} = {per_draw:,} basis states per candidate draw, over the "
        f"{CERTIFICATION_ELEMENT_BUDGET:,}-evaluation budget for a single certified instance. The "
        "relation's size could be reported from an uncertified candidate, but a row whose instance "
        "was never certified would sit in the same table as rows whose instances were, which is the "
        "one thing this project does not do. Refused rather than attempted."
    )


def _enumeration_refusal(label: str, width: int) -> str | None:
    """Why the relation at ``width`` cannot be built inside a run, or None when it can.

    The two corpus oracles have no generator to draw an instance from: each *is* its relation, and
    building one means enumerating the whole search register and evaluating the relation on every
    value — which is the same operation :data:`CERTIFICATION_ELEMENT_BUDGET` is spent on, since it is
    what makes ``M`` measured rather than assumed. A width whose enumeration is over that budget is
    therefore refused from the width, before the enumeration starts, exactly as the QLWR branch
    refuses an unaffordable certification. The alternative is a run that appears to hang, which is
    the failure mode the budget exists to prevent.
    """
    evaluations = 1 << width
    if evaluations <= CERTIFICATION_ELEMENT_BUDGET:
        return None
    return (
        f"{label} fixes its marked set by evaluating the relation on every one of the {width}-qubit "
        f"register's 2**{width} = {evaluations:,} values, over the {CERTIFICATION_ELEMENT_BUDGET:,}"
        "-evaluation budget this project spends before refusing a point. Refused from the width, "
        "before the enumeration starts."
    )


BACKEND_REGISTRY = {
    "qiskit_aer": ("grover_emulator.backends.qiskit_aer_backend", "QiskitAerBackend"),
    "cirq_qsim": ("grover_emulator.backends.cirq_qsim_backend", "CirqQsimBackend"),
}
"""Configuration name to engine, for the names ``backend.preference`` can carry."""


def _make_backend(config: ExperimentConfig, budget: float) -> tuple[Any | None, list[str]]:
    """The first engine this checkout can construct, and why each earlier one could not be.

    The order is the configuration's: a preference list is a preference, and an engine that is
    present and constructible wins over one further down. The reasons are returned rather than
    swallowed — "no engine" and "the preferred engine refused to construct" are different outcomes,
    and a run that reported the first when the second happened would send a reader to the wrong file.
    """
    reasons: list[str] = []
    for name in config.backend.preference:
        entry = BACKEND_REGISTRY.get(name)
        if entry is None:
            reasons.append(f"{name}: no engine is registered under that name")
            continue
        module = _optional_module(entry[0])
        constructor = getattr(module, entry[1], None) if module is not None else None
        if constructor is None:
            reasons.append(f"{name}: {entry[0]} does not provide {entry[1]} in this checkout")
            continue
        try:
            engine = constructor(ram_budget_gb=budget)
        except Exception as error:
            reasons.append(f"{name}: the engine could not be constructed: {type(error).__name__}: {error}")
            continue
        return _AmplitudeAdapter(engine), reasons
    return None, reasons


class _AmplitudeAdapter:
    """A backends-layer engine, presented as the analysis layer's one-method protocol.

    The two layers were written to different contracts. The analysis layer asks an engine for
    ``statevector(circuit)`` and for nothing else — deliberately, so that a curve, a probe and a
    baseline all depend on what an engine computes and not on how it is driven. The backends layer's
    engines expose ``run_statevector``, which returns a result carrying the amplitudes alongside the
    metrics, the budget the run was allowed, and the memory the kernel reported at the time.

    Neither contract is wrong, and neither is this module's to change, so the seam is adapted here —
    in the CLI, which is the one place both layers are in scope. Everything else the engine offers is
    delegated unchanged, including ``require_within_budget``, so the budget the analysis layer's runs
    are held to is the engine's own and not a second opinion.

    Each run's estimate and elapsed time are kept: a report can say what the engine was budgeted at
    even when the section that used it came back "not run".
    """

    def __init__(self, engine: Any):
        self._engine = engine
        self.engine_class = type(engine).__name__
        self.runs: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        return str(getattr(self._engine, "name", "engine"))

    def statevector(self, circuit: GateList) -> Any:
        result = self._engine.run_statevector(circuit)
        self.runs.append(
            {
                "circuit": getattr(circuit, "label", ""),
                "num_qubits": getattr(circuit, "num_qubits", None),
                "estimate_bytes": getattr(result, "estimate_bytes", None),
                "elapsed_s": getattr(result, "elapsed_s", None),
                "backend": getattr(result, "backend", self.name),
            }
        )
        return result.statevector

    def __getattr__(self, item: str) -> Any:
        if item == "_engine":  # pragma: no cover - only reachable before __init__ completes
            raise AttributeError(item)
        return getattr(self._engine, item)



# -----------------------------------------------------------------------------------------------
# small helpers
# -----------------------------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _logger() -> "Any":
    """The package logger, configured at the level a run should log at.

    :func:`configure_logging`'s own default is that level — the environment variable when it names
    a usable level, else ``INFO`` — so the call is left at the bare default rather than repeating
    the resolution here, where the two copies could drift apart.
    """
    log = configure_logging()
    # The framework logs its transpilation passes at INFO, one line per pass per circuit. Over a
    # sweep that is a screen of transpiler bookkeeping around the run's own few lines, and the run's
    # lines are the ones a reader is looking for. Quieted here rather than in the logging setup:
    # this is a decision about this command's output, not about how the project logs.
    import logging

    for noisy in ("qiskit", "matplotlib", "stevedore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    return log


def _optional_module(name: str) -> Any | None:
    """Import an optional collaborator, or return None when this checkout does not have it.

    Broad on purpose: the two collaborators are being written alongside this module, and a
    half-finished one must slow a run down with a recorded reason, not stop it with a traceback.
    """
    try:
        return importlib.import_module(name)
    except Exception:  # pragma: no cover - depends on what is present in the tree
        return None


def _hook(module: Any | None, *names: str) -> Any | None:
    """The first of ``names`` the module actually defines, or None."""
    if module is None:
        return None
    for name in names:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate
    return None


def _statevector_bytes(width: int) -> int:
    return BYTES_PER_AMPLITUDE * (1 << width)


def _get_in(mapping: Mapping[str, Any] | None, *keys: str) -> Any:
    """A value from a nested mapping, or None the moment the path stops existing.

    Used for the reads that are convenience rather than contract — a gate count handed to the
    baseline so its work ratio can be computed, say. A missing key there means the baseline reports
    fewer quantities, not that the run stops.
    """
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current


def _gb(n_bytes: float) -> float:
    return n_bytes / 1024.0**3


def _budget_check(label: str, width: int, budget_gb: float) -> str | None:
    """The reason ``label`` at ``width`` cannot be allocated, or None when it fits.

    Called before anything is allocated. The point of a budget is to decide *before* the allocation,
    and a check that runs afterwards is a post-mortem.
    """
    needed = _statevector_bytes(width)
    if _gb(needed) > budget_gb:
        return (
            f"{label} is {width} qubits: one statevector is {needed:,} bytes "
            f"({_gb(needed):.3g} GB), over the {budget_gb:g} GB budget for a single simulation. "
            "Refused before allocating, not attempted."
        )
    return None


def _budget_refusal(label: str, width: int, budget_gb: float, backend: Any | None) -> str | None:
    """The same check, asked of the engine when there is one.

    The backends layer owns the budget for the engines it knows: it carries the engine's own
    bytes-per-amplitude — qsim's CPU state vector is single precision, so it holds half what Aer
    holds — and its working-copy reserve, which a width-only check by the caller cannot know. Asking
    the engine is therefore the more accurate answer, and the local check is what remains for a
    checkout without that layer. Both are called before any allocation; neither is a post-mortem.
    """
    if backend is None:
        return _budget_check(label, width, budget_gb)
    try:
        backend.require_within_budget(width)
    except Exception as error:
        return f"{label}: {error}"
    return None


# -----------------------------------------------------------------------------------------------
# the instance, and what it actually marks
# -----------------------------------------------------------------------------------------------


def _build_spec(config: ExperimentConfig, seeds: RunSeeds) -> tuple[OracleSpec | None, dict | None, str | None]:
    """The spec this configuration describes, plus the instance behind it where there is one.

    Returns ``(spec, instance_description, refusal_reason)``. A refusal is a string, not an
    exception: an inadmissible width is a recorded outcome of the sweep this configuration asked
    for, and a sweep that crashed on ``n_search = 4`` would never reach ``n_search = 24``.

    The QLWR branch checks what certifying the instance will cost before it starts, so a width whose
    certification is over :data:`CERTIFICATION_ELEMENT_BUDGET` is refused from the width rather than
    from a run that does not come back. The two corpus branches do the same for the enumeration that
    fixes their marked set, and each surfaces the spec's own construction refusal — an inadmissible
    fold width, a chain index that will not fit, a map whose equation marks nothing — as the reason
    string rather than as an exception, so a sweep records it as a row.
    """
    settings = config.oracle
    n = settings.target_qubits
    if settings.type is OracleType.QLWR:
        from .problem.qlwr_instance import generate_scaled_instance

        draws = _draws_affordable(n)
        if draws is None:
            return None, None, _certification_refusal(n)
        try:
            instance = generate_scaled_instance(
                n_search=n,
                nu=settings.nu,
                seed=settings.seed,
                min_rounding_gap=settings.min_rounding_gap,
                max_attempts=draws,
            )
        except (ValueError, RuntimeError) as error:
            return None, None, (
                f"no admissible QLWR instance at n_search={n} within the sweep's construction "
                f"budget of {draws} candidate draw(s): {error}"
            )
        spec = QLWROracleSpec(instance)
        return spec, instance.describe(), None

    if settings.type is OracleType.RANDOM_CONTROL:
        n_items = 1 << n
        n_marked = max(1, min(n_items - 1, round(settings.marked_fraction * n_items)))
        return RandomControlOracleSpec(n_qubits=n, n_marked=n_marked, seed=settings.seed), None, None

    if settings.type is OracleType.HIDDEN_PERIOD:
        rng = seeds.rng("hidden_period", n, settings.seed)
        # An even period, so that the planted XOR-closure of the marked half-space holds; see
        # HiddenPeriodOracleSpec for why the low bit has to be clear.
        period = int(rng.integers(1, max(2, 1 << (n - 1)))) << 1
        return HiddenPeriodOracleSpec(n_qubits=n, period=period, seed=settings.seed), None, None

    # The two corpus oracles are selected exactly as the three above are, and they differ in one
    # respect that matters here: there is no generator to draw an instance from, because each *is*
    # its relation. Building one evaluates the relation over the whole search register — which is
    # what makes M measured — so the width is what decides whether the point is affordable, and the
    # budget check comes first. Neither takes a marked fraction: the chain's marked set is the
    # preimages of a chain value drawn from the spec's own description, and the key map's is a
    # quadratic form's zero set. Both are recorded in the run's seed record and reported.
    if settings.type is OracleType.LMOTS_CHAIN:
        n_bits = n if settings.chain_image_bits is None else settings.chain_image_bits
        refusal = _enumeration_refusal(f"the LM-OTS chain at n_bits={n_bits}", n)
        if refusal is not None:
            return None, None, refusal
        try:
            spec = LMOtsChainSpec(
                n_bits=n_bits,
                chain_length=settings.chain_length,
                fold_bits=n,
                seed=settings.seed,
                seeds=seeds,
            )
        except (ValueError, TypeError) as error:
            return None, None, (
                f"the LM-OTS chain at n_bits={n_bits} with a {n}-bit search register and "
                f"chain_length={settings.chain_length} could not be built: {error}"
            )
        return spec, None, None

    if settings.type is OracleType.KEY_MAP:
        mode = KeyMapMode(settings.key_map_mode)
        per_variable = 2 if mode is KeyMapMode.A else 4
        if n % per_variable:
            return None, None, (
                f"the key map in mode {mode.value} searches one register of {per_variable} bits per "
                f"map variable, so its search width must be a multiple of {per_variable}; {n} is not. "
                "A configuration's width is always the search register's width, never the map's own "
                "n, so that a sweep's points are comparable across oracles."
            )
        refusal = _enumeration_refusal(f"the key map at n_variables={n}", n)
        if refusal is not None:
            return None, None, refusal
        try:
            spec = ModeBKeyMapSpec(
                n=n // per_variable,
                mode=mode,
                n_outputs=settings.key_map_outputs,
                seeds=seeds,
            )
        except (ValueError, TypeError) as error:
            return None, None, (
                f"the key map over {n} variables in mode {mode.value} with "
                f"{settings.key_map_outputs} equation(s) could not be built: {error}"
            )
        return spec, None, None

    raise ValueError(f"unhandled oracle type {settings.type!r}")  # pragma: no cover - enum is closed


def _spec_facts(spec: OracleSpec) -> dict:
    """Everything the spec says about itself, including the facts only it can state.

    ``describe()`` is the shape every spec reports. The corpus's two add ``report()`` on top of it:
    their numbers mean different things under different readings, so the facts that pin the reading
    — which chain convention, over how many applications, and which register the map was searched
    over — travel with the numbers they qualify rather than being left for a reader to infer from a
    default. A marked-set size or a gate count quoted without them could belong to two different
    problems, which is the failure the upstream game this project replaces actually had.
    """
    facts = spec.describe()
    reporter = getattr(spec, "report", None)
    if callable(reporter):
        facts.update(reporter())
    return facts


def _circuit_section(spec: OracleSpec, lowering: Lowering, *, with_arithmetic: bool) -> dict[str, dict]:
    """Every circuit this run is about, counted from the IR.

    The truth-table oracle and the full Grover circuit at the optimum are what ran. The arithmetic
    oracle is the same predicate compiled as the relation, and it is included because the comparison
    between the two is the finding: for a single marked state the truth-table oracle is one
    multi-controlled Z, and the circuit that computes the same predicate is thousands of gates. Its
    gate count is a count of the gate list, which needs no simulation and no memory.
    """
    out: dict[str, dict] = {}
    out[f"oracle ({lowering.value})"] = build_phase_oracle(spec, lowering).to_dict()
    k_opt = spec.space().optimal_iterations
    out[f"grover k={k_opt} ({lowering.value})"] = build_grover_circuit(spec, k_opt, lowering).to_dict()
    if with_arithmetic and lowering is not Lowering.ARITHMETIC and spec.supports_arithmetic_lowering:
        out["oracle (arithmetic)"] = build_phase_oracle(spec, Lowering.ARITHMETIC).to_dict()
    return out


def _classical_baseline(spec: OracleSpec, seeds: RunSeeds, *, oracle_gate_count: int | None = None) -> dict:
    """What an unstructured classical search costs on this instance, measured rather than assumed.

    The comparison is the analysis layer's where it is present: it carries the expectation as an
    exact rational, the worst case, the per-query cost of the relation, and the caveat that the trial
    is a plain scan rather than the best attack known. The local trial below is the fallback for a
    checkout without that module, and it is deliberately the same measurement — one seeded
    random-order scan to the first marked value — so the number does not change with which path was
    taken, only the amount of context around it.
    """
    module = _optional_module("grover_emulator.analysis")
    construct = _hook(module, "classical_baseline")
    if construct is not None:
        try:
            return _as_mapping(construct(spec, ("cli", spec.name), oracle_gate_count))
        except TypeError:
            try:
                return _as_mapping(construct(spec, ("cli", spec.name)))
            except Exception as error:  # pragma: no cover - recorded as a reason by the caller
                raise RuntimeError(f"the analysis layer could not measure the baseline: {error}") from error
        except Exception as error:  # pragma: no cover
            raise RuntimeError(f"the analysis layer could not measure the baseline: {error}") from error

    space = spec.space()
    n_items, n_marked = space.n_items, space.n_marked
    if n_items > MAX_CLASSICAL_TRIAL_STATES:
        return {
            "status": "not run",
            "reason": (
                f"the search space is {n_items:,} states; a random-order trial would take longer "
                "than the simulation it is a baseline for"
            ),
            "queries_expected": n_items / n_marked,
        }
    rng = seeds.rng("classical_baseline", n_items, n_marked)
    queries = 0
    while True:
        candidate = int(rng.integers(0, n_items))
        queries += 1
        if spec.is_marked(candidate):
            break
        if queries > 64 * n_items:  # pragma: no cover - a failure mode, not a path
            raise RuntimeError("the classical trial did not find a marked value it must find")
    return {
        "queries": queries,
        "queries_expected": n_items / n_marked,
        "queries_worst_case": n_items - n_marked + 1,
        "grover_iterations": space.optimal_iterations,
        "evaluator": "random-order trial, seeded",
        "n_items": n_items,
        "n_marked": n_marked,
        "sampled_from": "the CLI's own fallback trial; the analysis layer was not present",
    }


def _validation_rows(spec: OracleSpec, *, lowerings: Sequence[Lowering]) -> list[dict]:
    """Exhaustive predicate checks: each lowering against the marked set, and the sandwich identity.

    These are the checks that keep the gate counts attached to a circuit that computes the right
    function. They are exact — the circuit is permutation-plus-phase, so the check is a bit-string
    permutation and an integer phase, with no tolerance anywhere — and they cost one machine word per
    basis state rather than a statevector, which is why they are available at widths a statevector
    engine cannot reach.

    A check whose estimated cost is over :data:`VALIDATION_ELEMENT_BUDGET` is recorded as not run with
    its estimate, so the table says what was and was not verified at this width.
    """
    from .utils.validation import assert_predicate_matches_spec

    rows: list[dict] = []
    n = spec.search_width()
    for lowering in lowerings:
        if not spec.supports_arithmetic_lowering and lowering is Lowering.ARITHMETIC:
            continue
        try:
            predicate = spec.build_predicate(lowering)
        except Exception as error:  # pragma: no cover - a build failure is itself the finding
            rows.append(
                {
                    "name": f"predicate == marked set ({lowering.value})",
                    "ok": False,
                    "n_search": n,
                    "detail": f"the predicate could not be built: {type(error).__name__}: {error}",
                }
            )
            continue
        estimated = len(predicate) * 2 * (1 << n)
        if estimated > VALIDATION_ELEMENT_BUDGET:
            rows.append(
                {
                    "name": f"predicate == marked set ({lowering.value})",
                    "ok": None,
                    "n_search": n,
                    "n_states": 2**n,
                    "memory_bytes": 8 * (1 << n),
                    "detail": (
                        f"not run: the exhaustive check costs about {estimated:.3g} element "
                        "operations at this width (every gate on every reachable state, twice for "
                        "the sandwich), over the budget for a check inside a run"
                    ),
                }
            )
            continue
        started = time.perf_counter()
        try:
            assert_predicate_matches_spec(spec, lowering)
            ok, detail = True, f"all {2**n:,} reachable basis states"
        except Exception as error:
            ok, detail = False, f"{type(error).__name__}: {error}"
        rows.append(
            {
                "name": f"predicate == marked set ({lowering.value})",
                "ok": ok,
                "n_search": n,
                "n_states": 2**n,
                "memory_bytes": 8 * (1 << n),
                "seconds": round(time.perf_counter() - started, 3),
                "detail": detail,
            }
        )
    return rows


# -----------------------------------------------------------------------------------------------
# execution
# -----------------------------------------------------------------------------------------------


class ExecutionRefused(RuntimeError):
    """The point cannot be executed within the run's memory budget."""


def _round_gate_list(spec: OracleSpec, lowering: Lowering) -> GateList:
    """One Grover iteration: the phase oracle, then the diffuser over the search register."""
    n = spec.search_width()
    total = oracle_width(spec, lowering)
    gl = GateList(total, label=f"grover_round[{spec.name}:{lowering.value}]")
    gl.extend(build_phase_oracle(spec, lowering))
    gl.extend(relabel(build_diffuser(n), {q: q for q in range(n)}, total))
    return gl


def _exact_statevector_curve(
    spec: OracleSpec,
    lowering: Lowering,
    iterations: range,
    *,
    budget_gb: float,
    shots: int,
    seeds: RunSeeds,
    backend: Any | None = None,
) -> tuple[list[dict], dict]:
    """The measured success curve, from the exact statevector of the circuit that produces it.

    One round of (oracle, diffuser) is compiled once and applied to the evolving state, with the
    statevector read back after each application. That is the same simulation as building the
    k-round circuit and running it: the state after k applications *is* the state the k-round circuit
    produces, and the test suite asserts the two agree point by point — through the analysis layer's
    from-scratch curve, at a width where both fit — to within a few units in the last place, which is
    what two compositions of the same unitary round can differ by in binary floating point. It is what
    makes the curve affordable: building and running 800 circuits from scratch costs the square of
    what applying 800 rounds costs.

    This is a measurement and it is labelled as one. It is also, as the report says, a *control*: a
    diagonal phase oracle leaves the success probability a function of ``(M, N)`` alone, so agreement
    with the closed form checks the harness rather than the physics. What the circuit contributes is
    that it certifies ``M`` and that it costs gates.

    Args:
        backend: an engine from the backends layer, when one could be constructed. Its
            ``require_within_budget`` is what refuses an over-budget width, so the budget policy has
            one definition rather than one per caller; the local check is the fallback for a checkout
            without that layer.

    Raises:
        ExecutionRefused: if the circuit is wider than the budget allows. Raised before anything is
            allocated, never after.
    """
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator

    import numpy as np

    width = oracle_width(spec, lowering)
    if backend is not None:
        try:
            backend.require_within_budget(width)
        except Exception as error:
            raise ExecutionRefused(str(error)) from None
    else:
        reason = _budget_check(f"{spec.name}/{lowering.value}", width, budget_gb)
        if reason is not None:
            raise ExecutionRefused(reason)

    n = spec.search_width()
    total = width
    round_qc = to_qiskit(_round_gate_list(spec, lowering))
    marked = np.array(sorted(spec.marked_set()), dtype=np.int64)

    # The engine's seed, kept inside the range the simulator accepts: a derived seed is a full 64-bit
    # value and Aer's option takes a narrower integer, so passing it unmasked is a construction error
    # rather than a seed.
    simulator = AerSimulator(
        method="statevector", device="CPU", seed_simulator=seeds.derive("aer", width) % (1 << 31)
    )

    prep = QuantumCircuit(total)
    for q in range(n):
        prep.h(q)
    prep.save_statevector()
    state = np.asarray(simulator.run(prep).result().get_statevector())
    norm = float(np.sum(np.abs(state) ** 2))
    if abs(norm - 1.0) > 1e-9:  # pragma: no cover - a broken engine, reported not swallowed
        raise ExecutionRefused(
            f"the engine returned a statevector with total probability {norm!r}; an exact "
            "simulation must be normalised"
        )

    space = spec.space()
    point_type = _curve_point_type()
    at_record = set(iterations)

    def point(k: int, amplitudes: "Any") -> Any:
        probabilities = np.abs(amplitudes) ** 2
        measured = _marked_probability(probabilities, spec)
        if point_type is None:
            return {
                "iteration": k,
                "empirical_p_success": measured,
                "theoretical_p_success": space.success_probability(k),
            }
        return point_type(
            iteration=k,
            measured=measured,
            closed_form=space.success_probability(k),
            sampled=None,
            shots=0,
        )

    records: list[Any] = []
    if 0 in at_record:
        records.append(point(0, state))

    for k in range(1, max(iterations) + 1):
        step = QuantumCircuit(total)
        step.set_statevector(state)
        step.compose(round_qc, inplace=True)
        step.save_statevector()
        state = np.asarray(simulator.run(step).result().get_statevector())
        if k in at_record:
            records.append(point(k, state))

    # The shot-based estimator at the final iteration, drawn from the exact distribution the same
    # circuit produced. It is recorded beside the exact number and never instead of it: at these
    # widths the exact value is available, so shots are a check on the sampling path and not a
    # substitute for a measurement that could not be made.
    if shots > 0 and records:
        final = np.abs(state) ** 2
        sampled = _sample_probability(final, shots, spec)
        last = records[-1]
        if point_type is None:
            last["sampled_p_success"] = sampled
            last["shots"] = shots
        else:
            last = _replace_point(last, sampled=sampled, shots=shots)
            records[-1] = last

    records = [record if point_type is None else record.to_dict() for record in records]

    backend_record = {
        "name": getattr(backend, "name", "qiskit_aer"),
        "engine": getattr(backend, "engine_class", type(backend).__name__ if backend else "AerSimulator"),
        "method": "statevector",
        "device": "CPU",
        "shots": shots,
        "sampled_at": int(max(iterations)),
        "exact_statevector_bytes": _statevector_bytes(width),
        "budget_gb": float(budget_gb),
        "source": "the CLI's incremental execution path, through the IR compiler",
        "agreement": (
            "asserted point by point against a from-scratch run through the analysis layer by the "
            "suite, to within a few units in the last place"
        ),
    }
    return records, backend_record


def _curve_point_type() -> Any | None:
    """The analysis layer's curve-point type, or None when that layer is not present.

    Building the layer's own record type rather than a dictionary keeps the two ends of the contract
    in one place: its ``to_dict`` is what the report renders, and using it here means a change to the
    record is a change in one module rather than two.
    """
    module = _optional_module("grover_emulator.analysis")
    return _hook(module, "CurvePoint")


def _replace_point(point: Any, **changes: Any) -> Any:
    """A frozen dataclass with fields replaced, so a sampled value can be attached after the fact."""
    import dataclasses

    return dataclasses.replace(point, **changes)


def _marked_probability(probabilities: "Any", spec: OracleSpec) -> float:
    """The total probability of the marked set, over the search register alone.

    The statevector is indexed with the search register over its low bits and the flag over the
    highest, so the amplitudes of the marked values are the amplitudes at those indices. Nothing is
    marginalised: the marked set is a set of search-register values, and the oracle leaves the
    ancillas clean by construction.
    """
    import numpy as np

    marked = np.array(sorted(spec.marked_set()), dtype=np.int64)
    return float(np.sum(probabilities[marked]))


def _sample_probability(probabilities: "Any", shots: int, spec: OracleSpec) -> float:
    """The sampled success probability at this iteration, through the analysis layer's own sampler.

    The layer's sampler derives its seed from the parts it is handed rather than from a generator
    passed in, so the statistics of a run are reproducible from the run's record alone. That is the
    property worth having, and it is why this is not a local ``rng.choice``.

    The index a draw returns covers the whole circuit, flag and ancillas included; it is reduced to
    the search register before it is asked whether it is marked. Those high bits are zero everywhere
    in this circuit's support — the oracle's second half is the first half's inverse — so the masking
    changes nothing, and it is written anyway so that the assumption is visible where it is used.
    """
    import numpy as np

    mask = (1 << spec.search_width()) - 1
    module = _optional_module("grover_emulator.analysis")
    draw = _hook(module, "sample_counts")
    if draw is not None:
        counts = draw(probabilities, shots, "cli", spec.name, spec.search_width(), int(shots))
        return sum(
            count for value, count in counts.items() if spec.is_marked(int(value) & mask)
        ) / shots
    rng = np.random.default_rng(shots)
    draws = rng.choice(probabilities.shape[0], size=shots, p=probabilities)
    return float(sum(1 for value in draws if spec.is_marked(int(value) & mask)) / shots)


# -----------------------------------------------------------------------------------------------
# the run
# -----------------------------------------------------------------------------------------------


def _oracle_variant(config: ExperimentConfig) -> str:
    """The part of a run's identity its oracle *type* does not carry, as a name segment.

    Two configurations that differ only in the LM-OTS chain length, or in which of the key map's
    registers is searched, are two different search problems: the marked set, the curve and the gate
    count all change with the variant, and the reports say so. Without this segment they would share
    a directory name, and the second run would silently overwrite the first one's report — the same
    class of failure as a marked-set size that no longer belongs to the numbers beside it.
    """
    oracle = config.oracle
    if oracle.type is OracleType.LMOTS_CHAIN:
        return f"-k{oracle.chain_length}"
    if oracle.type is OracleType.KEY_MAP:
        return f"-mode{oracle.key_map_mode}-eq{oracle.key_map_outputs}"
    return ""


def _run_id_for(config: ExperimentConfig, override: str | None) -> str:
    """A deterministic name for a run, so the same configuration lands in the same directory.

    A timestamp would make every invocation a new directory and every report a new artefact to
    compare by hand. The name carries what identifies the run — oracle, variant, width, lowering,
    seed — and is overridable for the case where two runs of the same configuration are wanted side
    by side.
    """
    if override:
        return override
    oracle = config.oracle.type.value
    variant = _oracle_variant(config)
    return (
        f"{oracle}{variant}-n{config.oracle.target_qubits}-{config.run.lowering}-s{config.run.seed}"
    )


def _prepare_run_dir(root: Path, run_id: str, config: ExperimentConfig, config_path: Path) -> Path:
    """Create the results directory and write the configuration the run validated."""
    import yaml

    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    echo = yaml.safe_dump(dump_config(config), sort_keys=True, default_flow_style=None)
    (run_dir / "config.yaml").write_text(
        "# The configuration this run validated, as loaded from "
        f"{config_path}.\n# Written before anything is built: a report must be able to say what it "
        "was asked for\n# even when the run stops early.\n" + echo,
        encoding="utf-8",
    )
    return run_dir


def run_experiment(
    config_path: Path | str = DEFAULT_CONFIG,
    *,
    run_id: str | None = None,
    output_dir: Path | str | None = None,
    with_sweep: bool = True,
    budget_gb: float | None = None,
) -> tuple[Path, dict]:
    """Execute one configuration and write its results directory.

    Returns:
        The results directory, and the results mapping that was written.
    """
    log = _logger()
    config_path = Path(config_path)
    config = load_config(config_path)
    budget = float(config.backend.ram_budget_gb if budget_gb is None else budget_gb)
    root = Path(output_dir if output_dir is not None else config.output.dir)
    run_id = _run_id_for(config, run_id)
    run_dir = _prepare_run_dir(root, run_id, config, config_path)

    seeds = RunSeeds.new(config.run.seed)
    notes: list[str] = []
    not_run: dict[str, str] = {}
    start = time.perf_counter()

    results: dict[str, Any] = {
        "run_id": run_id,
        "kind": "experiment",
        "config": dump_config(config),
        "created_utc": _utc_now(),
        "config_path": str(config_path),
        "seed": config.run.seed,
        "lowering": config.run.lowering,
    }

    lowering = Lowering(config.run.lowering)
    engine, engine_reasons = _make_backend(config, budget)
    if engine is None:
        # Not fatal: the circuits, the sweep and the exhaustive checks need no engine, and a run
        # whose execution is refused still owes a report that says so. The reasons travel with it.
        not_run["engine"] = (
            "no engine from backend.preference could be constructed: "
            + "; ".join(engine_reasons or ["the preference list is empty"])
        )
    spec, instance, refusal = _build_spec(config, seeds)
    results["instance"] = instance or {}

    if spec is None:
        not_run["spec"] = refusal or "the instance could not be generated"
        log.warning("%s", not_run["spec"])
        results["not_run"] = not_run
        results["notes"] = [f"the run stopped at instance generation: {not_run['spec']}"]
        results["seed_record"] = seeds.to_dict()
        results["wall_seconds"] = round(time.perf_counter() - start, 3)
        return _finalise(run_dir, config, results, budget=budget, figures_enabled="png" in config.output.formats)

    space = spec.space()
    n_marked = space.n_marked
    seeds.record("marked_set_size", n_marked)
    k_opt = space.optimal_iterations
    iteration_range = derive_iteration_range(spec)
    seeds.record("iteration_range", [iteration_range.start, iteration_range.stop - 1])

    results.update(
        {
            "spec": _spec_facts(spec),
            "marked_set_size": n_marked,
            "search_width": spec.search_width(),
            "n_items": space.n_items,
            "optimal_iterations": k_opt,
            "iteration_range": [iteration_range.start, iteration_range.stop - 1],
            "marked_set": sorted(spec.marked_set()) if space.n_items <= (1 << 20) else None,
        }
    )
    log.info(
        "%s: n_search=%d, M=%d of N=%d, k_opt=%d, iterations %s",
        spec.name, spec.search_width(), n_marked, space.n_items, k_opt,
        f"[{iteration_range.start}, {iteration_range.stop - 1}]",
    )

    # -- circuits, always countable, no simulation and no statevector memory ---------------------
    try:
        results["circuits"] = _circuit_section(
            spec, lowering, with_arithmetic=spec.supports_arithmetic_lowering
        )
    except Exception as error:
        not_run["circuits"] = f"the circuits could not be built: {type(error).__name__}: {error}"

    # -- the curve ------------------------------------------------------------------------------
    if lowering is not Lowering.TRUTH_TABLE:
        not_run["curve"] = (
            "the configured lowering is the arithmetic one, which is not statevector-simulable at "
            "any width this project builds; its cost is reported from the IR and its predicate is "
            "checked classically instead. Set run.lowering: truth_table for a curve."
        )
    else:
        try:
            curve, backend_record = _exact_statevector_curve(
                spec, lowering, iteration_range, budget_gb=budget,
                shots=config.backend.shots, seeds=seeds, backend=engine,
            )
            results["curve"] = curve
            results["backend"] = backend_record
        except ExecutionRefused as error:
            not_run["curve"] = str(error)
        except Exception as error:  # pragma: no cover - engine failure is recorded, not raised
            not_run["curve"] = f"the statevector execution failed: {type(error).__name__}: {error}"

    # -- the classical baseline ------------------------------------------------------------------
    gate_count = _get_in(results, "circuits", "oracle (arithmetic)", "gate_count")
    try:
        results["classical_baseline"] = _classical_baseline(spec, seeds, oracle_gate_count=gate_count)
    except Exception as error:  # pragma: no cover
        not_run["classical_baseline"] = f"{type(error).__name__}: {error}"

    # -- the exhaustive classical checks ---------------------------------------------------------
    lowerings = [lowering]
    if Lowering.ARITHMETIC not in lowerings:
        lowerings.append(Lowering.ARITHMETIC)
    try:
        results["validation"] = _validation_rows(spec, lowerings=lowerings)
    except Exception as error:  # pragma: no cover
        not_run["validation"] = f"{type(error).__name__}: {error}"

    # -- the sweep, so the fit has measured points to stand on ------------------------------------
    if with_sweep:
        sweep, sweep_not_run = _sweep_rows(config, seeds, budget=budget, reuse=spec, backend=engine)
        results["sweep"] = sweep
        not_run.update(sweep_not_run)
    else:
        not_run["sweep"] = "this run was told not to sweep; run scripts/sweep_scaling.py for it"

    # -- the sections the analysis layer owns ------------------------------------------------------
    _attach_analysis(results, config, seeds, spec, not_run, backend=engine)

    notes.extend(_provenance_notes(config, spec, results, budget=budget))
    results["notes"] = notes
    results["not_run"] = not_run
    results["seed_record"] = seeds.to_dict()
    results["wall_seconds"] = round(time.perf_counter() - start, 3)

    return _finalise(run_dir, config, results, budget=budget, figures_enabled="png" in config.output.formats)


def _provenance_notes(
    config: ExperimentConfig, spec: OracleSpec, results: Mapping[str, Any], *, budget: float
) -> list[str]:
    """What a reader of the numbers needs in order to know how they were produced."""
    notes = [
        f"every stochastic choice is derived from the run seed {config.run.seed}; the derivation is "
        "recorded in seed_record and re-derives from the recorded root",
        f"M = {results.get('marked_set_size')} was measured by enumerating the search register and "
        "evaluating the relation on every value, not read from the configuration's target density",
        f"the iteration range is derived from this instance's own optimum "
        f"(k_opt = {results.get('optimal_iterations')}, plus two so the curve is seen to turn over); "
        "it is not set in the configuration",
        f"the memory budget is {budget:g} GB per simulation, checked before any allocation",
    ]
    if "curve" in results:
        notes.append(
            "the curve was produced by applying one round of (oracle, diffuser) to the evolving "
            "statevector and reading the state back at every iteration; the state after k rounds is "
            "the state the k-round circuit produces, which the test suite asserts point by point "
            "against a from-scratch curve to within a few units in the last place. The "
            "success probability is exact and shot-free; a single shot-based draw at "
            f"k = {results.get('backend', {}).get('sampled_at', '-')} is recorded as "
            "sampled_p_success beside it"
        )
    if isinstance(results.get("classical_baseline"), Mapping):
        baseline = results["classical_baseline"]
        queries = baseline.get("queries")
        expected = baseline.get("queries_expected_float", baseline.get("queries_expected"))
        if queries and expected is not None:
            notes.append(
                f"the classical baseline is one seeded random-order scan: {queries} predicate "
                f"evaluations to the first marked value, against an expectation of {float(expected):.0f}. "
                "It is a plain exhaustive scan and not the best attack known; the caveat that "
                "travels with it is in the baseline section"
            )
        elif baseline.get("reason"):
            notes.append(f"the classical baseline was not measured: {baseline['reason']}")
    notes.extend(_relation_notes(results.get("spec") or {}))
    return notes


def _relation_notes(facts: Mapping[str, Any]) -> list[str]:
    """The reading the numbers above were measured under, said in words rather than in a column.

    The spec table carries these as facts, which is where a reader who knows what to look for finds
    them. This is the same statement in a sentence, because "chain_convention = iterated_chain" is a
    name and what a reader needs is which problem that name picks out. It is emitted only for the
    oracles whose numbers change with the reading: for the rest the type name is the whole of it.
    """
    notes: list[str] = []
    convention = facts.get("chain_convention")
    if convention:
        applications = facts.get("chain_applications", facts.get("chain_length"))
        if applications == 1:
            reading = (
                "one truncated hash per candidate, which is the corpus's own game reproduced call "
                "for call: the target is that single node's value and the search is its preimage"
            )
        else:
            reading = (
                f"the node function applied {applications} times with the chain index advancing by "
                "one per application, the RFC 8554 chain — the same node function as the single "
                "hash, applied a different number of times, and a different search problem"
            )
        notes.append(
            f"the chain numbers above were measured under the {convention} convention: {reading}"
        )
    if facts.get("n_variables") is not None and "mode" in facts:
        register = (
            "the map's own variables"
            if facts.get("mode") == "A"
            else "twice the map's variables, the register the corpus's production key map is "
            "instantiated in"
        )
        notes.append(
            f"the key map above was searched over {register}: {facts['n_variables']} variables, "
            f"with the flag taken over {facts.get('n_outputs')} equation(s) of the map"
        )
    return notes


def _attach_analysis(
    results: dict,
    config: ExperimentConfig,
    seeds: RunSeeds,
    spec: OracleSpec,
    not_run: dict[str, str],
    *,
    backend: Any | None = None,
) -> None:
    """Ask the analysis layer for the sections it owns, and record why when it cannot answer.

    Three sections belong to that layer and are taken from it rather than reimplemented here: the
    residual summary of the measured curve against the closed form, the structural probes, and the
    scaling fit. Each call is guarded and each failure becomes a reason in ``not_run``, so a run in
    which the layer was absent or raised still produces a report that says which section is missing
    and why — rather than a report that reads as complete while carrying less.

    The probes need an engine: they sample the oracle circuit, and the samples are what the
    constraint system is built from. Without one they are recorded as not run, which is a statement
    about this run rather than about the relation.
    """
    module = _optional_module("grover_emulator.analysis")
    if module is None:
        not_run["probes"] = (
            "the structural probes live in grover_emulator.analysis, which is not present in this "
            "checkout; the curve above is a measurement, but it carries no information about the "
            "relation's algebraic structure"
        )
        not_run["scaling"] = (
            "the scaling fit lives in grover_emulator.analysis, which is not present in this "
            "checkout; the sweep table below is measured from the IR, and no model was fitted to it"
        )
        not_run["curve_fit"] = (
            "the residual summary lives in grover_emulator.analysis, which is not present in this "
            "checkout; the curve above is measured, and its departure from the closed form was not "
            "summarised"
        )
        return

    curve = results.get("curve")

    fit = _hook(module, "fit_residuals")
    if fit is None:
        not_run["curve_fit"] = "grover_emulator.analysis defines no residual fit"
    elif curve:
        try:
            results["curve_fit"] = _as_mapping(fit(curve))
        except Exception as error:
            not_run["curve_fit"] = f"{type(error).__name__}: {error}"
    else:
        not_run.setdefault(
            "curve_fit", "there is no measured curve to compare against the closed form"
        )

    probes = _hook(module, "run_probes")
    if probes is None:
        not_run["probes"] = "grover_emulator.analysis defines no probe suite"
    elif backend is None:
        not_run["probes"] = (
            "the structural probes sample the oracle circuit through an engine, and no engine could "
            "be constructed from backend.preference in this checkout"
        )
    else:
        try:
            results["probes"] = _as_records(
                probes(
                    spec,
                    backend,
                    lowering=Lowering(config.run.lowering),
                    run_simon_style=config.probes.run_simon_style,
                    run_qft_period=config.probes.run_qft_period,
                    seed_parts=("cli", spec.name),
                )
            )
        except Exception as error:
            not_run["probes"] = f"{type(error).__name__}: {error}"

    _attach_scaling(results, module, not_run)


def _attach_scaling(results: dict, module: Any, not_run: dict[str, str]) -> None:
    """Fit the relation's cost against width, from the sweep's measured rows only.

    The fit is given the sweep records and turns them into measured points itself, which is where the
    refusal happens: a sweep row that was not run has no gate count, and a fit that accepted one
    would place its intercept wherever the zero landed. The points that were refused are reported
    beside the fit through :func:`sweep_provenance`, so a fit over part of a sweep says which part.

    The fit is projected to :data:`SCALING_TARGET_WIDTH`, and the theoretical Grover query count at
    that width is recorded beside it. Both are keyed ``extrapolated_``: neither is a measurement.
    """
    points_from = _hook(module, "measured_points_from_sweep")
    fit_gates = _hook(module, "fit_gate_scaling")
    sweep = results.get("sweep")
    if not sweep:
        not_run["scaling"] = "there is no sweep to fit; this run did not measure any width"
        return
    if points_from is None or fit_gates is None:
        not_run["scaling"] = "grover_emulator.analysis defines no scaling fit"
        return
    try:
        points = points_from(sweep)
        if not points:
            not_run["scaling"] = (
                "no sweep point was measured, so there is nothing to fit; every width was refused "
                "for the reason recorded in the refusal table"
            )
            return
        # The fit exists in order to be projected: the measured widths stop at what a statevector
        # holds, and the question the sweep is asked is what the relation costs at the real width.
        # Without a target the record held an exponent and a scale and left that arithmetic to the
        # reader — who would then have had a number with no provenance attached to it.
        fitted = fit_gates(points, target_widths=(SCALING_TARGET_WIDTH,))
        record = _as_mapping(fitted)
        # The other half of the cost at that width: how many times the oracle is called. This is the
        # textbook floor(pi/4 * sqrt(N)) at N = 2**128 and M = 1 — theory, not a fit and not a
        # measurement, and M = 1 there is an assumption (uniqueness was certified only at the
        # simulated widths). It carries the `extrapolated_` prefix because the report's rule is that
        # every number in this table is one nobody measured, and says which kind it is beside it.
        # A float on purpose: the closed form goes through a double, so the integer's trailing
        # digits would be precision the value does not have.
        record[f"extrapolated_theoretical_grover_query_count_n_search_{SCALING_TARGET_WIDTH}"] = float(
            theoretical_optimal_iterations(1 << SCALING_TARGET_WIDTH, 1)
        )
        # Prefixed like the number it explains: the report's fit table admits no unlabelled key.
        record[f"extrapolated_theoretical_grover_query_count_basis_n_search_{SCALING_TARGET_WIDTH}"] = (
            f"closed form floor(pi/4 * sqrt(N/M)) at N = 2**{SCALING_TARGET_WIDTH}, assuming M = 1; "
            "theoretical, not fitted and not measured. Multiplied by the extrapolated gate count "
            "of one iteration it gives a projected total, which is then a prediction twice over"
        )
        provenance = _hook(module, "sweep_provenance")
        if provenance is not None:
            record["sweep_provenance"] = provenance(sweep)
        results["scaling"] = record
    except Exception as error:
        not_run["scaling"] = f"{type(error).__name__}: {error}"


def _as_mapping(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    describe = getattr(value, "describe", None)
    if callable(describe):
        return dict(describe())
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return dict(value.to_dict())
    raise TypeError(f"cannot read a mapping out of {type(value).__name__}")


def _as_records(value: Any) -> list:
    """A sequence of records from whatever a collaborator returns.

    A collaborator may hand back a DataFrame, a list of mappings, or a list of its own record objects.
    The last case is the common one here — the probe suite returns its own result type, whose
    ``to_dict`` is what the report's table renders — and reading it through that method rather than
    through its repr is the difference between a table of numbers and a table of dashes.
    """
    if value is None:
        return []
    if hasattr(value, "to_dict") and hasattr(value, "columns"):
        return [dict(row) for row in value.to_dict(orient="records")]
    if isinstance(value, Mapping):
        return [dict(value)]
    import dataclasses

    records: list = []
    for row in value:
        if isinstance(row, Mapping):
            records.append(dict(row))
        elif callable(getattr(row, "to_dict", None)):
            records.append(dict(row.to_dict()))
        elif callable(getattr(row, "describe", None)):
            records.append(dict(row.describe()))
        elif dataclasses.is_dataclass(row):
            records.append(dataclasses.asdict(row))
        else:
            records.append({"value": row})
    return records


# -----------------------------------------------------------------------------------------------
# the sweep
# -----------------------------------------------------------------------------------------------


def _sweep_rows(
    config: ExperimentConfig,
    seeds: RunSeeds,
    *,
    budget: float,
    reuse: OracleSpec | None = None,
    backend: Any | None = None,
) -> tuple[list[dict], dict[str, str]]:
    """One row per sweep width: what the circuits cost, and what could not be run.

    A width is never skipped silently. A width with no admissible instance, a width whose arithmetic
    lowering cannot exist, and a width whose statevector would not fit are three different outcomes
    and each is recorded with its own reason. The refusal is decided from the width *before* anything
    is allocated, which is the difference between a sweep that records a limitation and a sweep that
    swaps.

    Returns:
        The rows, and the ``not_run`` entries describing the passes that were refused.
    """
    log = _logger()
    rows: list[dict] = []
    not_run: dict[str, str] = {}
    for n_search in config.sweep.qubit_range:
        row: dict[str, Any] = {"n_search": n_search}
        started = time.perf_counter()
        try:
            if reuse is not None and reuse.search_width() == n_search:
                spec = reuse
            else:
                spec, _instance, refusal = _build_spec(
                    config.model_copy(
                        update={"oracle": config.oracle.model_copy(update={"target_qubits": n_search})}
                    ),
                    seeds,
                )
                if spec is None:
                    row.update({"status": "not run", "reason": refusal, "wall_seconds": 0.0})
                    rows.append(row)
                    log.warning("n_search=%d refused: %s", n_search, refusal)
                    continue

            # Widths are counts, and in this project counts come from the gate list — the same rule
            # the gate counts below follow, and for the same reason. ``oracle_width`` composes the
            # width from the spec's ancilla count plus a flag term, which double-counts the flag for
            # the arithmetic lowering: that lowering's own layout carries its flag, so its declared
            # total is one short of what the formula produces. Reading the width off the gate list
            # answers the question the column asks — how wide is this circuit — and keeps the width,
            # the byte cost and the budget refusal in one row describing one object.
            table = build_phase_oracle(spec, Lowering.TRUTH_TABLE).to_dict()
            counted_arithmetic = (
                build_phase_oracle(spec, Lowering.ARITHMETIC).to_dict()
                if spec.supports_arithmetic_lowering
                else None
            )
            width_table = table["num_qubits"]
            width_arithmetic = (
                counted_arithmetic["num_qubits"]
                if counted_arithmetic is not None
                else oracle_width(spec, Lowering.ARITHMETIC)
            )
            row["n_qubits_truth_table"] = width_table
            row["statevector_bytes_truth_table"] = _statevector_bytes(width_table)
            row["n_qubits_arithmetic"] = width_arithmetic
            row["statevector_bytes_arithmetic"] = _statevector_bytes(width_arithmetic)
            row["optimal_iterations"] = spec.space().optimal_iterations
            # The truth-table oracle is one multi-controlled X per marked state, so its gate count
            # is a count of the width's marked set and nothing else: a row that reports the gates
            # without the M they were built from leaves its largest column uninterpretable. Measured
            # here exactly as it is in the single run, by the spec that enumerates it.
            row["n_marked"] = spec.space().n_marked
            row["spec_name"] = spec.name

            row["oracle_gates_truth_table"] = table["gate_count"]
            row["oracle_depth_truth_table"] = table["ir_depth"]
            circuit = build_grover_circuit(
                spec, spec.space().optimal_iterations, Lowering.TRUTH_TABLE
            ).to_dict()
            row["grover_gates_truth_table"] = circuit["gate_count"]
            row["grover_depth_truth_table"] = circuit["ir_depth"]

            # ``gate_count`` and ``ir_depth`` are the arithmetic oracle: they are the columns the
            # report's scaling table prints and the series the cost figure draws, and the relation's
            # size is the finding. Absent where the oracle has no arithmetic form, so the row is
            # still marked measured while those columns stay empty — rather than quietly carrying
            # the truth-table numbers under an arithmetic heading.
            if counted_arithmetic is not None:
                counted = counted_arithmetic
                row["gate_count"] = counted["gate_count"]
                row["ir_depth"] = counted["ir_depth"]
                row["toffoli_count"] = counted["toffoli_count"]
                row["t_count_with_toffolis"] = counted["t_count_with_toffolis"]
                row["ancilla_peak"] = counted["ancilla_peak"]
                # ``n_qubits`` and ``lowering`` are the names the analysis layer's measured-point
                # reader uses; the widths above stay under their own names because a row reports
                # both lowerings and a single ``n_qubits`` would hide which one it meant.
                row["n_qubits"] = width_arithmetic
                row["lowering"] = Lowering.ARITHMETIC.value

            row["status"] = "measured"
            row["wall_seconds"] = round(time.perf_counter() - started, 3)

            # What a statevector *could* be allocated here, decided from the width. Named "fits
            # budget" rather than "simulable" on purpose: it answers the memory question and not the
            # time question, and at the top of the range the binding constraint is the number of
            # rounds, which this sweep does not spend.
            for label, width in (("truth_table", width_table), ("arithmetic", width_arithmetic)):
                reason = _budget_refusal(
                    f"the {label.replace('_', '-')} lowering at n_search={n_search}", width, budget, backend
                )
                row[f"statevector_fits_budget_{label}"] = reason is None
                if reason is not None:
                    not_run[f"statevector pass, {label} lowering at n_search={n_search}"] = reason
        except Exception as error:
            row.update({"status": "not run", "reason": f"{type(error).__name__}: {error}"})
            row["wall_seconds"] = round(time.perf_counter() - started, 3)
            log.warning("n_search=%d could not be built: %s", n_search, error)
        rows.append(row)
    return rows, not_run


def run_sweep(
    config_path: Path | str = DEFAULT_CONFIG,
    *,
    run_id: str | None = None,
    output_dir: Path | str | None = None,
    budget_gb: float | None = None,
) -> tuple[Path, dict]:
    """The scaling sweep: circuit cost per width, with every refusal recorded.

    The sweep builds and counts circuits. It does not execute them: its question is what the relation
    costs, and a gate count is a property of the gate list, computable at widths no engine can
    simulate. Where a statevector pass *would* be needed it is refused by the budget, from the width,
    before allocation.
    """
    log = _logger()
    config_path = Path(config_path)
    config = load_config(config_path)
    budget = float(config.backend.ram_budget_gb if budget_gb is None else budget_gb)
    root = Path(output_dir if output_dir is not None else config.output.dir)
    run_id = run_id or (
        f"sweep-{config.oracle.type.value}-nu{config.oracle.nu}{_oracle_variant(config)}"
        f"-s{config.run.seed}"
    )
    run_dir = _prepare_run_dir(root, run_id, config, config_path)

    seeds = RunSeeds.new(config.run.seed)
    not_run: dict[str, str] = {}
    start = time.perf_counter()
    engine, engine_reasons = _make_backend(config, budget)
    if engine is None:
        not_run["engine"] = (
            "no engine from backend.preference could be constructed: "
            + "; ".join(engine_reasons or ["the preference list is empty"])
        )
    rows, sweep_not_run = _sweep_rows(config, seeds, budget=budget, backend=engine)
    not_run.update(sweep_not_run)

    measured = [row for row in rows if row.get("status") == "measured"]
    refused = [row for row in rows if row.get("status") != "measured"]
    results: dict[str, Any] = {
        "run_id": run_id,
        "kind": "sweep",
        "config": dump_config(config),
        "created_utc": _utc_now(),
        "config_path": str(config_path),
        "seed": config.run.seed,
        "lowering": config.run.lowering,
        "sweep": rows,
        "not_run": not_run,
        "seed_record": seeds.to_dict(),
        "wall_seconds": round(time.perf_counter() - start, 3),
        "notes": [
            f"{len(measured)} of {len(rows)} widths produced circuits; the other {len(refused)} are "
            "recorded as refusals with their reasons, including the widths whose circuit could not "
            "be built at all",
            "gate counts are computed from the gate-list IR, never from a framework circuit object",
            "no statevector was allocated by this sweep: a pass that would exceed the budget is "
            "refused from its width, before allocation",
            "this sweep does not execute anything, so its rows are circuit sizes and not "
            "measurements of a running machine",
        ],
    }

    _attach_scaling(results, _optional_module("grover_emulator.analysis"), not_run)

    return _finalise(run_dir, config, results, budget=budget, figures_enabled="png" in config.output.formats)


# -----------------------------------------------------------------------------------------------
# writing
# -----------------------------------------------------------------------------------------------


def _finalise(
    run_dir: Path, config: ExperimentConfig, results: dict, *, budget: float, figures_enabled: bool
) -> tuple[Path, dict]:
    """Write the figures, the results mapping, and the report — in that order, and always.

    The mapping is written before the report so that a failure while rendering leaves the numbers
    behind, and the report is rendered from the mapping that was written rather than from live
    objects, so regenerating it produces the same bytes.
    """
    log = _logger()
    figures: dict[str, Path] = {}
    if figures_enabled:
        try:
            figures = plots.plot_all(results, run_dir / "figures", budget_gb=budget)
        except Exception as error:  # pragma: no cover - a plotting failure must not lose the run
            log.warning("figures could not be drawn: %s: %s", type(error).__name__, error)
            results.setdefault("not_run", {})["figures"] = f"{type(error).__name__}: {error}"
    results["figures"] = plots.figure_table(results, figures)

    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(results, indent=2, sort_keys=True, default=str), encoding="utf-8")
    stored = json.loads(metrics_path.read_text(encoding="utf-8"))

    if "markdown" in config.output.formats:
        generate_report(run_dir, config, stored, figures=figures)
    return run_dir, stored


def _stored_figure_map(run_dir: Path, results: Mapping[str, Any]) -> dict[str, Path]:
    """The figures a run recorded, as ``{caption: path}`` for the ones still on disk.

    Regeneration has to reproduce the figure *table* and not just the figure files, and the captions
    are part of the table. A renderer that found the figures by scanning the directory would derive
    its captions from the filenames — ``success curve`` where the run wrote ``success probability
    against iteration`` — so the regenerated report would differ from the original in exactly the
    place it is meant to be a copy of it. The mapping the run stored is therefore what is replayed,
    and the directory scan stays where it belongs: as the fallback for a directory whose mapping
    records no figures.
    """
    figures_dir = run_dir / "figures"
    out: dict[str, Path] = {}
    for record in results.get("figures") or []:
        if not isinstance(record, Mapping):
            continue
        caption, name = record.get("caption"), record.get("path")
        if not caption or not name:
            continue
        path = figures_dir / Path(str(name)).name
        if path.is_file():
            out[str(caption)] = path
    return out


def regenerate_report(
    run_dir: Path | str, *, filename: str = "report.md", redraw: bool = False
) -> Path:
    """Re-render ``report.md`` from a finished results directory.

    Nothing is re-simulated and nothing is re-measured: the report is a view of the stored mapping,
    so re-rendering it after a formatting change costs a file read. Figures are redrawn only when
    asked, and either way the result is byte-identical to the report the run wrote — the figures
    because a deterministic renderer replays them, the rest because the mapping is unchanged.
    """
    run_dir = Path(run_dir)
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.is_file():
        raise FileNotFoundError(
            f"{metrics_path} does not exist; a report is rendered from a finished run's results, "
            "and this directory does not hold one"
        )
    if redraw:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = json.loads(metrics_path.read_text(encoding="utf-8"))
            figures = plots.plot_all(
                results, run_dir / "figures", budget_gb=float(results.get("config", {}).get("backend", {}).get("ram_budget_gb", 6.0))
            )
            generate_report(run_dir, results.get("config"), results, figures=figures, filename=filename)
        return run_dir / filename
    stored = json.loads(metrics_path.read_text(encoding="utf-8"))
    figures = _stored_figure_map(run_dir, stored)
    return generate_report_from_run_dir(run_dir, figures=figures or None, filename=filename)


# -----------------------------------------------------------------------------------------------
# the command line
# -----------------------------------------------------------------------------------------------

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Grover/oracle emulator: real reversible oracle circuits, exact statevector runs, and the "
    "resource extrapolation that follows from them.",
)


@app.command()
def run(
    config: Path = typer.Option(
        Path(DEFAULT_CONFIG), "--config", "-c", help="the experiment configuration"
    ),
    run_id: str | None = typer.Option(None, "--run-id", help="override the run's directory name"),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="where results/ lives"),
    sweep: bool = typer.Option(True, "--sweep/--no-sweep", help="also sweep the configured widths"),
    ram_budget_gb: float | None = typer.Option(
        None, "--ram-budget-gb", help="override the memory budget"
    ),
) -> None:
    """Run the configured experiment and write results/{run_id}/."""
    try:
        run_dir, results = run_experiment(
            config, run_id=run_id, output_dir=output_dir, with_sweep=sweep, budget_gb=ram_budget_gb
        )
    except Exception as error:
        _logger().error("%s: %s", type(error).__name__, error)
        raise typer.Exit(code=1)
    _summarise(run_dir, results)


@app.command()
def sweep(
    config: Path = typer.Option(
        Path(DEFAULT_CONFIG), "--config", "-c", help="the experiment configuration"
    ),
    run_id: str | None = typer.Option(None, "--run-id", help="override the results directory name"),
    output_dir: Path | None = typer.Option(None, "--output-dir", help="where results/ lives"),
    ram_budget_gb: float | None = typer.Option(
        None, "--ram-budget-gb", help="override the memory budget"
    ),
) -> None:
    """Measure circuit cost across the configured widths, refusing what will not fit.

    A width whose circuits cannot be built, or whose statevector pass would exceed the budget, is
    recorded as a refusal with its reason and its size. Refusals are a result: the exit status is
    zero unless the run could not be attempted at all.
    """
    try:
        run_dir, results = run_sweep(
            config, run_id=run_id, output_dir=output_dir, budget_gb=ram_budget_gb
        )
    except Exception as error:
        _logger().error("%s: %s", type(error).__name__, error)
        raise typer.Exit(code=1)
    _summarise(run_dir, results)


@app.command()
def report(
    run_dir: Path = typer.Option(..., "--run-dir", help="a finished results directory"),
    filename: str = typer.Option("report.md", "--filename", help="the report's filename"),
    redraw: bool = typer.Option(False, "--redraw", help="redraw the figures from the stored results"),
) -> None:
    """Re-render a report from a finished results directory, without re-running anything."""
    try:
        path = regenerate_report(run_dir, filename=filename, redraw=redraw)
    except Exception as error:
        _logger().error("%s: %s", type(error).__name__, error)
        raise typer.Exit(code=1)
    typer.echo(str(path))


@app.command()
def probe() -> None:
    """Milestone 0: verify every framework API this project is built on."""
    from .utils.api_probe import format_report, probe_all

    results = probe_all()
    typer.echo(format_report(results))
    if any(not result.ok and result.required for result in results):
        raise typer.Exit(code=1)


def _summarise(run_dir: Path, results: Mapping[str, Any]) -> None:
    """What a run prints: where it went, what it produced, and what it refused."""
    log = _logger()
    not_run = results.get("not_run") or {}
    log.info(
        "wrote %s: run id %s, %d section(s) reported, %d refused",
        run_dir, results.get("run_id"), _section_count(results), len(not_run),
    )
    for section, reason in not_run.items():
        log.warning("not run: %s: %s", section, reason)
    typer.echo(str(run_dir / "report.md"))


def _section_count(results: Mapping[str, Any]) -> int:
    names = ("spec", "circuits", "curve", "probes", "sweep", "scaling", "validation", "classical_baseline")
    return sum(1 for name in names if results.get(name))


def main_run() -> int:
    """Entry point for ``scripts/run_experiment.py``: the same run, without the argument parser."""
    _require_scope_boundary()
    try:
        run_dir, results = run_experiment(DEFAULT_CONFIG)
    except Exception as error:
        _logger().error("%s: %s", type(error).__name__, error)
        return 1
    _summarise(run_dir, results)
    return 0


def main_sweep() -> int:
    """Entry point for ``scripts/sweep_scaling.py``."""
    try:
        run_dir, results = run_sweep(DEFAULT_CONFIG)
    except Exception as error:
        _logger().error("%s: %s", type(error).__name__, error)
        return 1
    _summarise(run_dir, results)
    return 0


def _require_scope_boundary() -> None:
    """Fail loudly if the boundary this project reports under has gone missing from the report code.

    Checked here, at the entry point, because the boundary is the one statement every report must
    carry and a run that produced a report without it would be a run that claimed more than it
    measured.
    """
    if not SCOPE_BOUNDARY or not SCOPE_BOUNDARY.startswith("This system does not and cannot"):
        raise RuntimeError("the report module's scope boundary is missing or altered")


if __name__ == "__main__":  # pragma: no cover - exercised as a subprocess by the test suite
    app()
