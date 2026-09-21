"""Typed, validated experiment configuration.

Modelled on the sibling Grover project's schema — pydantic v2, ``extra="forbid"``, frozen — because
the reasoning carries over unchanged and matters more here. Lattice parameters are easy to get
subtly wrong and a lattice attack will happily "succeed" against the wrong lattice without
complaint, so an unvalidated config is not a convenience, it is a silent-wrong-answer generator.

One structural rule in this file is not like the others, and is the reason it is written the way it
is: **:class:`InstanceSource` has no member for the corpus's recorded parameter set.** The build is
validated on synthetic instances and published reference parameter sets only. Leaving the option out
makes the excluded run *unrepresentable* rather than merely un-run — a config file cannot express
it, so no future edit can enable it by accident, and ``test_config_schema.py`` asserts the refusal.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = [
    "InstanceSource",
    "EngineName",
    "AttackType",
    "InstanceSettings",
    "EngineSettings",
    "AttackSettings",
    "SweepSettings",
    "CostModelSettings",
    "OutputSettings",
    "ExperimentConfig",
    "BLOCK_SIZE_HARD_MAX",
    "load_config",
    "dump_config",
]


#: No block size above this is accepted, **with or without** ``sweep.long_run_opt_in``. It is the
#: largest the hardware calibration ever ran (~193 s at four threads, ~405 s at one), and it is the
#: bound the G6K engine's reading of ``MAX_SIEVING_DIM`` leans on — see
#: ``engines/g6k_sieve_engine.py``. The opt-in buys the range from the default ceiling (60) up to
#: here; it does not buy the unmeasured range beyond.
BLOCK_SIZE_HARD_MAX = 90


class InstanceSource(str, Enum):
    """Which kind of instance a run builds.

    **There is deliberately no ``CORPUS_RECORDED`` member.** The recorded production parameter set
    is not available to this build; adding it is a two-line change (this member plus a
    ``ParameterSet`` constructor) and is gated on explicit confirmation. Until then, a config that
    asks for it fails validation with a message naming the legal values, which is the intended
    behaviour rather than an obstacle to be worked around.
    """

    SYNTHETIC_SCALED = "synthetic_scaled"
    RANDOM_LATTICE_CONTROL = "random_lattice_control"
    PUBLISHED_REFERENCE = "published_reference"


class EngineName(str, Enum):
    G6K = "g6k"
    FPYLLL_BKZ = "fpylll_bkz"


class AttackType(str, Enum):
    PRIMAL = "primal"
    DUAL = "dual"


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InstanceSettings(_Frozen):
    source: InstanceSource = InstanceSource.SYNTHETIC_SCALED
    #: Target *lattice* dimension, not a register width. The sibling project's sweep parameter was
    #: a qubit count; here the natural axis is the dimension of the lattice the attack reduces.
    target_dimension: int = Field(default=100, ge=8, le=400)
    seed: int = Field(default=20260913, ge=0)
    #: Only meaningful for ``published_reference``; ignored otherwise.
    reference_scheme: str | None = None
    #: ``nu / m`` for synthetic instances. Defaults to the recorded production shape as a *ratio*;
    #: the ratio is what the scaling rule preserves, so it is the thing worth stating.
    nu_over_m: tuple[int, int] = Field(default=(256, 608))

    @field_validator("nu_over_m")
    @classmethod
    def _a_ratio_that_describes_an_instance(cls, v: tuple[int, int]) -> tuple[int, int]:
        # Validated here because nowhere downstream can: ``build_instance`` computes
        # ``nu = max(2, round(m * num / den))`` and then draws bases until one has column rank
        # ``nu``. A zero denominator is a ZeroDivisionError there; a negative numerator is silently
        # clamped to ``nu = 2`` by the ``max``, which runs a plausible experiment on a shape nobody
        # asked for; and a ratio at or above one asks for at least as many unknowns as samples, so
        # full column rank is unreachable (above one) or the normal form — which consumes ``nu``
        # samples — is left with none (at one). The middle case did not raise. It hung.
        numerator, denominator = v
        if numerator < 1 or denominator < 1:
            raise ValueError(f"nu_over_m must be two positive integers, got {v}")
        if numerator >= denominator:
            raise ValueError(
                f"nu_over_m={v} is a ratio of {numerator / denominator:.3g}; it must be below 1, "
                "because the attack needs more samples (m) than unknowns (nu)"
            )
        return v


class EngineSettings(_Frozen):
    preference: tuple[EngineName, ...] = (EngineName.G6K, EngineName.FPYLLL_BKZ)
    #: OpenMP threads for the reduction engine. **Default 1, as a correctness setting.** Four is
    #: faster where it matters — calibration found it 1.6x faster than one at block size 80 and 2.1x
    #: at 90 (notes/01-hardware.md) — and was the default until 2026-09-20. But G6K is
    #: bit-reproducible at one thread and is not above it: notes/09-scaling-and-the-sweep.md measured
    #: four identical four-thread processes returning three distinct root-Hermite factors, one
    #: recovering the planted vector and three not. The shipped YAML already pinned 1 for that
    #: reason; a config built without the YAML — ``ExperimentConfig()`` — swept single draws.
    threads: int = Field(default=1, ge=1, le=12)
    #: Refusal threshold. Never fired in calibration (block size 90 peaks at ~231 MiB); retained as
    #: a guard against a genuine runaway, which on this host means a machine that stops responding
    #: rather than an exception, because swap is already nearly full.
    ram_budget_gb: float = Field(default=6.0, gt=0)
    #: Block sizes above this need ``sweep.long_run_opt_in``. Not a memory limit —
    #: calibration showed memory is not the binding constraint — but a *time* one. 60 is the design
    #: document's figure (section 4: exceeding "dimension 200 / block size 60" must be explicitly
    #: opted into); this was 90 until 2026-09-20, which let the shipped range reach 80 with the
    #: opt-in off. 90 survives as :data:`BLOCK_SIZE_HARD_MAX`, the ceiling the opt-in itself stops
    #: at: block size 90 already costs ~193 s, and the growth from there is steep.
    sieve_block_size_max: int = Field(default=60, ge=10, le=BLOCK_SIZE_HARD_MAX)
    #: The sieving dimension below which G6K uses its Gauss sieve rather than its default one —
    #: ``SieverParams.gauss_crossover``, handed to the G6K engine by the pipeline. 50 is G6K's own
    #: default, so the shipped value changes nothing; it is here so that a run which does change it
    #: records that it did. The enumeration engine has no sieve and never sees it.
    gauss_crossover: int = Field(default=50, ge=1)


class AttackSettings(_Frozen):
    types: tuple[AttackType, ...] = (AttackType.PRIMAL, AttackType.DUAL)
    #: Stops at 60 — the no-opt-in ceiling — so that ``ExperimentConfig()`` is a config its own
    #: validator accepts. It ran to 80 while the ceiling was 90. The shipped YAML still runs to 80,
    #: and says ``long_run_opt_in: true`` to do it; a default cannot opt in on anyone's behalf.
    block_size_range: tuple[int, ...] = (10, 20, 30, 40, 50, 60)
    #: How far past the model's predicted block size the primal sweep keeps trying before giving
    #: up and recording a failure: block sizes above ``beta_usvp + search_beyond_prediction`` are
    #: not attempted, and if nothing at or below that recovered the secret they are recorded as not
    #: run, with this as the reason (``pipeline.run_experiment``). It bounds the search only where
    #: there is a prediction — with the estimator off, or no ``beta_usvp``, the whole range is tried.
    search_beyond_prediction: int = Field(default=15, ge=0)
    #: A wall-clock guard per block-size point, projected from the *measured* previous point. Not a
    #: budget to be trusted but a backstop against an unbounded run: enumeration cost grows steeply
    #: enough that a sweep trying every size to the top of its range is not slow but unfinishable.
    #: Measured in M1, dimension 160 costs 58.6 s at block size 40 and roughly 5.5x more per ten.
    #: A point that would exceed this is recorded as not attempted, with the projection.
    max_seconds_per_block_size: float = Field(default=600.0, gt=0)

    @field_validator("block_size_range")
    @classmethod
    def _ascending_and_positive(cls, v: tuple[int, ...]) -> tuple[int, ...]:
        if not v:
            raise ValueError("block_size_range must not be empty")
        if any(b < 2 for b in v):
            raise ValueError(f"block sizes must be at least 2 (LLL), got {v}")
        if list(v) != sorted(set(v)):
            raise ValueError(f"block_size_range must be strictly ascending, got {v}")
        return v


class SweepSettings(_Frozen):
    dimension_range: tuple[int, ...] = (40, 60, 80, 100, 130, 160)
    #: Must be set explicitly to exceed ``engine.sieve_block_size_max`` (60 by default) or dimension
    #: 200. Deliberate friction: a long run should be a decision, not a typo. It does not lift
    #: :data:`BLOCK_SIZE_HARD_MAX`.
    long_run_opt_in: bool = False

    @field_validator("dimension_range")
    @classmethod
    def _ascending(cls, v: tuple[int, ...]) -> tuple[int, ...]:
        if not v:
            raise ValueError("dimension_range must not be empty")
        if list(v) != sorted(set(v)):
            raise ValueError(f"dimension_range must be strictly ascending, got {v}")
        return v


class CostModelSettings(_Frozen):
    use_lattice_estimator: bool = True
    models: tuple[str, ...] = ("primal_usvp", "dual")
    quantum_sieving_speedup: bool = True

    @field_validator("models")
    @classmethod
    def _known_models(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        # The estimator's own attack-family names. A typo here would silently drop a family from
        # the minimum-over-models, and the minimum is the number that gets reported.
        allowed = {"primal_usvp", "dual", "dual_hybrid"}
        unknown = set(v) - allowed
        if unknown:
            raise ValueError(f"unknown cost models {sorted(unknown)}; legal values are {sorted(allowed)}")
        return v


class OutputSettings(_Frozen):
    dir: Path = Path("results")
    formats: tuple[Literal["markdown", "json", "png"], ...] = ("markdown", "json")


class ExperimentConfig(_Frozen):
    run_id: str | None = None
    instance: InstanceSettings = InstanceSettings()
    engine: EngineSettings = EngineSettings()
    attack: AttackSettings = AttackSettings()
    sweep: SweepSettings = SweepSettings()
    cost_model: CostModelSettings = CostModelSettings()
    output: OutputSettings = OutputSettings()

    @model_validator(mode="after")
    def _long_runs_are_opted_into(self) -> ExperimentConfig:
        """Refuse a silently over-budget sweep rather than attempting and swapping.

        The failure this prevents is not an exception. On this host swap is already ~90% consumed,
        so a run that overshoots does not raise — it makes the machine stop responding while the
        sieve walks a nearly-full swap file. That is why the check is here, at load, rather than
        inside the engine where it would fire after the work had started.
        """
        over_dimension = [d for d in self.sweep.dimension_range if d > 200]
        over_block = [b for b in self.attack.block_size_range
                      if b > self.engine.sieve_block_size_max]
        if (over_dimension or over_block) and not self.sweep.long_run_opt_in:
            raise ValueError(
                f"this configuration exceeds the default limits "
                f"(dimensions {over_dimension} > 200, block sizes {over_block} > "
                f"{self.engine.sieve_block_size_max}). Set sweep.long_run_opt_in: true to proceed "
                "deliberately; the limits are time and memory guards, not decoration."
            )
        beyond_measured = [b for b in self.attack.block_size_range if b > BLOCK_SIZE_HARD_MAX]
        if beyond_measured:
            raise ValueError(
                f"block sizes {beyond_measured} exceed {BLOCK_SIZE_HARD_MAX}, the largest this "
                "project has measured; sweep.long_run_opt_in does not extend past it"
            )
        return self


def load_config(path: str | Path) -> ExperimentConfig:
    """Read and validate a YAML config. Raises on anything the schema does not recognise."""
    raw = yaml.safe_load(Path(path).read_text())
    if raw is None:
        raise ValueError(f"{path} is empty")
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a mapping at the top level, got {type(raw).__name__}")
    return ExperimentConfig.model_validate(_coerce_tuples(raw))


def dump_config(config: ExperimentConfig) -> dict[str, Any]:
    """The config as a plain mapping, with paths as strings, for writing beside a run's results."""
    data = config.model_dump(mode="json")
    data["output"]["dir"] = str(config.output.dir)
    return data


def _coerce_tuples(node: Any) -> Any:
    """YAML has no tuples, and pydantic will not widen a list to a tuple field on its own here.

    Converting lists to tuples keeps the schema's immutability honest — a list field could be
    mutated after validation, which would defeat the point of freezing the model.
    """
    if isinstance(node, dict):
        return {k: _coerce_tuples(v) for k, v in node.items()}
    if isinstance(node, list):
        return tuple(_coerce_tuples(v) for v in node)
    return node
