"""The experiment configuration: what a run is allowed to be told, and what it must never be told.

Why a typed schema rather than ``yaml.safe_load``
-------------------------------------------------
A configuration file is an interface with no compiler. A typo in a key name is not a syntax error;
it is a key that nothing reads, and the run then proceeds with a default that nobody chose. The
distribution of that failure is the worst possible one: silent, plausible, and only visible in a
number that looks slightly off. Every model here therefore sets ``extra="forbid"``, so an unknown
key is a load failure that names the key and the nearest legal ones.

Why the iteration range is a special case
-----------------------------------------
``sweep.iteration_range`` defaults to ``null``, which means *derived per instance* from the spec's
own optimum (:func:`grover_emulator.circuits.grover_circuit_builder.derive_iteration_range`). The
plan document this project was built from carried ``iteration_range: [0, 40]`` as a fixed default;
at the smallest structurally faithful QLWR instance the optimum is ``k = 50`` and at
``n_search = 24`` it is ``3216``, so ``[0, 40]`` truncates the curve before its peak and returns a
smooth, monotone, entirely plausible rising curve that supports no conclusion — with nothing
raising. A fixed range is therefore not forbidden (a deliberately narrow exploratory window is a
legitimate thing to ask for) but it is never silent: :func:`load_config` warns, and the warning
quotes the optimum this configuration's own ``M`` and ``N`` imply.

Why the widths are search-register widths
-----------------------------------------
``oracle.target_qubits`` and ``sweep.qubit_range`` are **search-register** widths. The circuit's
total width is derived per lowering as ``n_search + ancilla_width(lowering)``, and for the QLWR
arithmetic lowering that difference is 38 qubits — enough to decide whether a run is possible at
all, and not a number any config should be allowed to state independently of the lowering it
applies to.
"""

from __future__ import annotations

import warnings
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..problem.search_space import theoretical_optimal_iterations

__all__ = [
    "OracleType",
    "RunSettings",
    "OracleSettings",
    "SweepSettings",
    "BackendSettings",
    "ProbeSettings",
    "OutputSettings",
    "ExperimentConfig",
    "load_config",
    "dump_config",
    "expected_optimal_iterations",
]


class OracleType(str, Enum):
    """Which :class:`~grover_emulator.problem.oracle_spec.OracleSpec` the run is about.

    ``RANDOM_CONTROL`` and ``HIDDEN_PERIOD`` are not alternatives to the real target; they are what
    make a negative result mean something. A probe suite that has never once fired is
    indistinguishable from a broken one, and a suite that fires on a uniformly random marked set is
    detecting its own implementation. Both controls exist to be run against the same harness.
    """

    QLWR = "qlwr"
    """The real relation: secret recovery against a scaled QLWR instance."""

    RANDOM_CONTROL = "random_control"
    """A uniformly random marked set of the requested fraction — the negative control."""

    HIDDEN_PERIOD = "hidden_period"
    """A marked set with a planted XOR-period — the positive control."""

    LMOTS_CHAIN = "lmots_chain"
    """The audit corpus's own reduced-size LM-OTS game: preimage of a keyed chain value.

    Selected the same way as the three above. The relation is the corpus's, so its gate count is
    comparable with every other number this project reports, and ``chain_length`` decides which of
    the two readings of "chain" the run is about — see :class:`~grover_emulator.problem.
    corpus_oracles.ChainConvention`. Every run pins the reading it used in its report, because a
    marked-set size, a curve and a gate count all change with it.
    """

    KEY_MAP = "key_map"
    """The corpus's expanding quadratic key map over ``F2``, one equation per output bit.

    ``key_map_mode`` picks which register is searched — the map's own variables (``A``, ``2n``
    qubits) or twice them (``B``, ``4n``) — and ``key_map_outputs`` how many equations the flag
    takes the conjunction over.
    """


class _Section(BaseModel):
    """Base for every section: no unknown keys, no mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class RunSettings(_Section):
    """Things true of the whole run, independent of the oracle."""

    seed: int = 20260913
    """Seeds every stochastic choice this run makes, and is recorded in the report."""

    lowering: Literal["truth_table", "arithmetic"] = "truth_table"
    """Which oracle lowering the reported circuit is. ``truth_table`` is the oracle of record at
    simulable widths and the only one that is statevector-simulable at scale; ``arithmetic`` is the
    circuit the gate-count extrapolation is about, and it is validated classically rather than
    simulated. See :mod:`grover_emulator.problem.oracle_spec`."""


class OracleSettings(_Section):
    """The oracle spec to build, and the parameters it takes."""

    type: OracleType = OracleType.QLWR
    target_qubits: int = Field(default=20, ge=2, le=30)
    """Search-register width for the single run. Not the total circuit width."""

    marked_fraction: float = Field(default=1.0e-6, gt=0.0, lt=1.0)
    """The marked-set density the instance is *aimed* at, ``M/N``.

    It is a design target, never an input to a computation. Every number in a report comes from the
    measured marked set: for QLWR the marked set is enumerated and required to have exactly one
    element, and for the random control exactly this many items are drawn. A config that could
    declare ``M`` and have the circuit mark something else would be a config whose success curve and
    whose circuit describe different problems.

    The ``lmots_chain`` and ``key_map`` types ignore it for the same reason: their ``M`` is fixed by
    the relation itself — the preimages of a drawn chain value, the zero set of a quadratic form —
    and is measured when the spec is built.
    """

    seed: int = 20260913
    """Seeds instance generation specifically, so an instance is reproducible on its own."""

    nu: int = Field(default=2, ge=1, le=4)
    """Dimension of the secret. 2 is the smallest value with genuine matrix structure."""

    min_rounding_gap: float = Field(default=3.0, ge=1.5)
    """Minimum ``q_l / p`` for a generated instance. This is the knob that decides which search
    widths are *admissible* at all: below ``n_search = 12`` at ``nu = 2`` no generic prime pair fits
    in ``n_search / nu`` bits per component, and the generator refuses rather than returning an
    instance whose rounding discards nothing. A sweep records that refusal as a row; see
    :mod:`grover_emulator.experiment`."""

    chain_length: int = Field(default=1, ge=1, le=254)
    """``lmots_chain`` only: how many times the corpus's node function is applied, ``k``.

    The default is 1 and it is the corpus's own behaviour, reproduced gate for gate: one truncated
    SHA-256 over the domain-separated node, and the search is that node's preimage. Above 1 the chain
    index advances by one per application, which is the RFC 8554 chain function and a *different*
    search problem — the same function applied a different number of times. Both are stated in the
    run's report, since neither a marked-set size nor a gate count means anything without it.

    The upper bound is the ``u8`` chain index the corpus writes: the chain runs to ``j + k - 1``
    with ``j = 2``, so a length over 254 has nowhere to advance to.
    """

    chain_image_bits: int | None = Field(default=None, ge=2)
    """``lmots_chain`` only: the width the chain value is compared at — the corpus's ``n``.

    ``null`` (the default) is the corpus's reduced-size arrangement, and the one that reproduces its
    game gate for gate: ``target_qubits`` is the search register *and* the compared image, which is
    the same width. The two come apart on the real object, where a chain node takes a wide input
    while the comparison is over a truncated image — set this below ``target_qubits`` for that
    arrangement. ``target_qubits`` stays the search-register width either way, so a sweep's widths
    mean the same thing here as for every other oracle.

    The searched register must still fit the ``ceil(chain_image_bits / 8)`` bytes the digest takes,
    and every value in it must be a preimage candidate. A combination that cannot be built is
    recorded as a refusal naming the bound the spec gave, rather than silently clamped.
    """

    key_map_mode: Literal["A", "B"] = "B"
    """``key_map`` only: which of the corpus's two registers the search is over.

    ``A`` is the map's own variables, ``2n`` qubits; ``B`` is twice that register, ``4n`` qubits, the
    mode the corpus's production key map is instantiated in and therefore the default. The search
    width is read from the mode, so ``target_qubits`` must be divisible by 2 for ``A`` and by 4 for
    ``B`` — a width that does not divide is refused with that reason and recorded as a sweep row.
    """

    key_map_outputs: int = Field(default=1, ge=1, le=64)
    """``key_map`` only: how many of the map's equations the predicate takes the conjunction over.

    One equation is the default, and it is the honest one to start from: the map's own equations are
    what the corpus has, and one of them marks roughly half the register — a real property of a
    quadratic form rather than a search problem Grover can amplify, which the report states through
    the measured marked fraction. Raising it shrinks the marked set toward a preimage-sized one and
    costs one work qubit per equation in the compiled lowering.
    """


class SweepSettings(_Section):
    """The scaling sweep: which search widths, and over which iteration counts."""

    qubit_range: list[int] = Field(default_factory=lambda: [4, 8, 12, 16, 20, 24], min_length=1)
    """Search-register widths to sweep, in order."""

    iteration_range: list[int] | None = None
    """``[lo, hi]`` inclusive, or ``null`` to derive per instance from the spec's optimum.

    ``null`` is the default and the only value that is correct for a reported curve. A fixed value
    is accepted, and warns at load, because a deliberately narrow window is a legitimate
    exploratory request — but it is a bug in any configuration whose results are quoted, which is
    why it can never be set silently.
    """

    @field_validator("qubit_range")
    @classmethod
    def _check_qubit_range(cls, value: list[int]) -> list[int]:
        if any(n < 2 for n in value):
            raise ValueError(f"every sweep width must be at least 2, got {value}")
        if len(set(value)) != len(value):
            raise ValueError(f"sweep widths repeat: {value}")
        if value != sorted(value):
            raise ValueError(f"sweep widths must be ascending: {value}")
        return value

    @field_validator("iteration_range")
    @classmethod
    def _check_iteration_range(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if len(value) != 2:
            raise ValueError(
                f"iteration_range must be null or [lo, hi], got {value!r}; a single number is "
                "ambiguous between a count and a bound"
            )
        lo, hi = value
        if lo < 0:
            raise ValueError(f"iteration_range starts below 0: {value!r}")
        if hi < lo:
            raise ValueError(f"iteration_range is empty: {value!r}")
        return value

    def to_range(self) -> range | None:
        """The Python ``range`` this section means, or None for "derive per instance"."""
        if self.iteration_range is None:
            return None
        lo, hi = self.iteration_range
        return range(lo, hi + 1)


class BackendSettings(_Section):
    """Which engines may run, and the resources they may use."""

    preference: list[str] = Field(default_factory=lambda: ["qiskit_aer", "cirq_qsim"], min_length=1)
    """Engine names in preference order, passed through to ``backends.select_backend``."""

    ram_budget_gb: float = Field(default=6.0, gt=0.0)
    """Ceiling on what a single simulation may allocate. A run over it is refused, not attempted:
    an allocation failure under memory pressure takes the machine with it rather than the run."""

    shots: int = Field(default=20000, ge=1)
    """Shots per iteration count for the sampled curve. The statevector pass is exact; this is what
    the sampled curve is compared against, and the only place a statistical error enters."""

    @field_validator("preference")
    @classmethod
    def _check_preference(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError(f"backend preference repeats an engine: {value}")
        return value


class ProbeSettings(_Section):
    """Which structural probes run against the oracle circuit.

    Probing an oracle for structure is the one thing in this project that is not an amplitude
    recursion over ``(M, N)``: a different algorithm run against the *same* circuit asks whether the
    relation's algebraic structure is there to be used, which no ``sin^2`` curve can answer.
    """

    run_simon_style: bool = True
    run_qft_period: bool = True


class OutputSettings(_Section):
    """Where a run writes, and in which formats."""

    dir: str = "results/"
    formats: list[Literal["markdown", "json", "png"]] = Field(
        default_factory=lambda: ["markdown", "json", "png"], min_length=1
    )

    @field_validator("formats")
    @classmethod
    def _check_formats(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError(f"output formats repeat: {value}")
        return value


class ExperimentConfig(_Section):
    """One validated experiment configuration.

    Immutable after validation: a run records the configuration it used, and a configuration that
    can be edited mid-run is a report that cannot be reproduced from its own config echo.
    """

    run: RunSettings = Field(default_factory=RunSettings)
    oracle: OracleSettings = Field(default_factory=OracleSettings)
    sweep: SweepSettings = Field(default_factory=SweepSettings)
    backend: BackendSettings = Field(default_factory=BackendSettings)
    probes: ProbeSettings = Field(default_factory=ProbeSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)

    @model_validator(mode="after")
    def _check_width_is_sweepable(self) -> "ExperimentConfig":
        if self.oracle.target_qubits not in self.sweep.qubit_range:
            warnings.warn(
                f"oracle.target_qubits={self.oracle.target_qubits} is not in "
                f"sweep.qubit_range={self.sweep.qubit_range}; the single run and the sweep would "
                "not share a width, so no sweep point is a check on the run",
                stacklevel=2,
            )
        return self


def expected_optimal_iterations(config: ExperimentConfig) -> int | None:
    """The iteration count this configuration's ``M`` and ``N`` imply, from the config alone.

    Used to say out loud what a fixed ``iteration_range`` would truncate. It is deliberately the
    *theory* value: no circuit has been built yet, and the function must be usable at the moment the
    config is loaded. For QLWR the marked set is 1 by construction; for the two controls it is the
    fraction the config asks for.

    Returns:
        The optimum, or ``None`` for the two corpus oracles, whose ``M`` is not a function of
        anything in the configuration: the chain's marked set is the preimages of a drawn chain
        value and the key map's is a quadratic form's zero set. Both are measured when the spec is
        built. Quoting the configured fraction there would be quoting a design target that enters no
        computation, which is the one thing this function exists not to do.
    """
    n = config.oracle.target_qubits
    n_items = 1 << n
    if config.oracle.type is OracleType.QLWR:
        n_marked = 1
    elif config.oracle.type in (OracleType.LMOTS_CHAIN, OracleType.KEY_MAP):
        return None
    else:
        n_marked = max(1, min(n_items - 1, round(config.oracle.marked_fraction * n_items)))
    return theoretical_optimal_iterations(n_items, n_marked)


def load_config(path: str | Path) -> ExperimentConfig:
    """Read and validate a YAML configuration.

    Raises:
        FileNotFoundError: if the file is not there. Raised rather than defaulted: a run that
            silently used built-in defaults because the path was mistyped is a run nobody can
            reproduce.
        yaml.YAMLError: if the file is not parseable YAML.
        pydantic.ValidationError: if a key is unknown, missing, or of the wrong type. This is the
            schema's reason to exist.

    Warns:
        UserWarning: if a fixed ``sweep.iteration_range`` is set. See the module docstring.
    """
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: the top level of a config must be a mapping, got {type(raw).__name__}")
    config = ExperimentConfig.model_validate(raw)

    if config.sweep.iteration_range is not None:
        optimum = expected_optimal_iterations(config)
        lo, hi = config.sweep.iteration_range
        if optimum is None:
            # The corpus oracles take no M from the configuration, so there is no number to compare
            # the window against here. The warning still fires: a fixed window is a bug in any
            # configuration whose results are quoted, whatever the oracle.
            warnings.warn(
                f"{path}: sweep.iteration_range is fixed at [{lo}, {hi}], but {config.oracle.type.value} "
                "takes its marked-set size from the relation rather than from the configuration, so no "
                "optimum can be quoted at load time and the window cannot be checked against one. Leave "
                "it null to derive the range from the instance's own optimum.",
                stacklevel=2,
            )
            return config
        warnings.warn(
            f"{path}: sweep.iteration_range is fixed at [{lo}, {hi}]; this configuration's own M and "
            f"N imply an optimum near k={optimum}. If {hi} < {optimum} the curve is truncated before "
            "its peak, rises monotonically for the whole window, and supports no conclusion while "
            "looking like a result. Leave it null to derive the range per instance.",
            stacklevel=2,
        )
    return config


def dump_config(config: ExperimentConfig) -> dict[str, Any]:
    """The configuration as a JSON-safe mapping, for the config echo a run writes out."""
    return config.model_dump(mode="json")
