"""The config schema, and the one thing it deliberately cannot express.

The load-bearing test here is :func:`test_corpus_source_is_unrepresentable`. Everything else checks
that a validated config means what it says; that one checks that a config *cannot* mean something
this build is not allowed to do. The difference matters because the excluded run is not forbidden by
a comment or a convention — a later edit cannot enable it by accident, because there is no value to
set.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from qlwr_lattice_stress.config.schema import (
    AttackSettings,
    EngineSettings,
    ExperimentConfig,
    InstanceSource,
    SweepSettings,
    dump_config,
    load_config,
)

REPO = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------------------------
# the boundary, as a property of the type system
# ---------------------------------------------------------------------------------------------


def test_corpus_source_is_unrepresentable():
    """The recorded production parameter set has no member in ``InstanceSource``.

    This is the build's hard constraint expressed structurally rather than remembered. A future
    edit that adds the option will fail *this* test, which is the point: the decision to leave the
    corpus unread should have to be made deliberately, not drift in.
    """
    members = {m.value for m in InstanceSource}
    assert members == {"synthetic_scaled", "random_lattice_control", "published_reference"}
    assert not any("corpus" in m or "qlwr" == m for m in members), members


def test_a_config_naming_the_corpus_is_rejected_with_the_legal_values():
    """The refusal has to be informative — a caller who tries should learn what is allowed."""
    with pytest.raises(ValidationError) as exc:
        ExperimentConfig.model_validate({"instance": {"source": "corpus_recorded"}})
    message = str(exc.value)
    assert "synthetic_scaled" in message and "random_lattice_control" in message


@pytest.mark.parametrize("bogus", ["qlwr", "corpus", "production", "qpt128"])
def test_plausible_alternative_spellings_are_also_rejected(bogus):
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate({"instance": {"source": bogus}})


def test_no_source_file_names_the_research_tree():
    """A companion guard: the schema cannot express the corpus, and no module may reach for it by
    path either. Both halves are needed — the type system stops the config, this stops the code."""
    offenders = []
    for path in (REPO / "src").rglob("*.py"):
        text = path.read_text()
        if "Documents/PQT" in text or "PQT/" in text:
            offenders.append(str(path.relative_to(REPO)))
    assert not offenders, offenders


# ---------------------------------------------------------------------------------------------
# validation actually validates
# ---------------------------------------------------------------------------------------------


def test_unknown_keys_are_refused():
    """``extra="forbid"``: a typo'd key would otherwise be ignored and the run would silently use
    the default, which is the failure mode a typed config exists to prevent."""
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate({"instnace": {"seed": 1}})


def test_block_sizes_must_be_ascending():
    with pytest.raises(ValidationError, match="strictly ascending"):
        AttackSettings(block_size_range=(20, 10))


def test_block_sizes_must_be_at_least_two():
    """Block size 2 is LLL; below that is not a reduction."""
    with pytest.raises(ValidationError, match="at least 2"):
        AttackSettings(block_size_range=(1, 10))


def test_unknown_cost_models_are_refused():
    """A typo here would silently drop an attack family from the minimum-over-models, and the
    minimum is the number that gets reported as the security level."""
    from qlwr_lattice_stress.config.schema import CostModelSettings

    with pytest.raises(ValidationError, match="unknown cost models"):
        CostModelSettings(models=("primal_usvp", "duall"))


def test_a_long_run_needs_explicit_opt_in():
    """The guard exists because on this host an over-budget run does not raise — it makes the
    machine stop responding, since swap is already nearly full."""
    with pytest.raises(ValidationError, match="long_run_opt_in"):
        ExperimentConfig.model_validate({"sweep": {"dimension_range": (40, 250)}})


def test_a_long_run_is_allowed_once_opted_into():
    cfg = ExperimentConfig.model_validate(
        {"sweep": {"dimension_range": (40, 250), "long_run_opt_in": True}}
    )
    assert cfg.sweep.long_run_opt_in


def test_a_block_size_above_the_ceiling_needs_opt_in_too():
    """The ceiling is a *time* limit, not a memory one — calibration showed memory is not binding —
    so it is stated alongside the dimension limit rather than derived from it."""
    with pytest.raises(ValidationError, match="long_run_opt_in"):
        ExperimentConfig.model_validate({"attack": {"block_size_range": (10, 100)}})


# ---------------------------------------------------------------------------------------------
# the measured defaults
# ---------------------------------------------------------------------------------------------


def test_the_thread_default_is_the_reproducible_one():
    """1. Calibration found 4 to be 2.1x faster at block size 90, and this test pinned 4 until
    2026-09-20 — but notes/09 then measured four identical four-thread processes returning three
    distinct root-Hermite factors, so the fast default was a default of single draws. The shipped
    YAML already said 1; the schema now agrees with it."""
    assert EngineSettings().threads == 1


def test_the_ram_budget_matches_the_sibling_project():
    """6 GiB. It never fired in calibration — block size 90 peaks at ~231 MiB — and it is retained
    as a runaway guard rather than as the thing that sets the ceiling."""
    assert EngineSettings().ram_budget_gb == 6.0


def test_the_default_config_validates():
    cfg = ExperimentConfig()
    assert cfg.instance.source is InstanceSource.SYNTHETIC_SCALED
    assert cfg.instance.target_dimension == 100


def test_configs_are_frozen():
    cfg = ExperimentConfig()
    with pytest.raises(ValidationError):
        cfg.engine.threads = 8  # type: ignore[misc]


# ---------------------------------------------------------------------------------------------
# the shipped yaml
# ---------------------------------------------------------------------------------------------


def test_the_shipped_config_loads():
    cfg = load_config(REPO / "config" / "default_experiment.yaml")
    assert cfg.attack.block_size_range == (10, 20, 30, 40, 50, 60, 70, 80)
    # **One thread, pinned because it is a correctness setting rather than a preference.** G6K is
    # bit-reproducible at one thread and is not above it: measured at dimension 80, block size 10,
    # four processes at four threads returned three distinct root-Hermite factors, one of which
    # recovered the planted vector and three of which did not. The config said 4 while the sweep was
    # run, so every minimum above block size 10 was one draw rather than a measurement. An edit that
    # raises this back to 4 re-introduces that silently, which is why it is asserted here.
    assert cfg.engine.threads == 1
    # True, because the shipped range reaches 80 and the no-opt-in ceiling is the design document's
    # 60. This pinned False while the ceiling was 90 — the old rule, under which 80 needed nothing.
    assert cfg.engine.sieve_block_size_max == 60
    assert cfg.sweep.long_run_opt_in is True


def test_the_shipped_config_round_trips_through_a_dump():
    """A run writes its config beside its results, and the report regenerates from that directory —
    so the dump has to reload to the same object, or a report would describe a different run than
    the one that produced it."""
    cfg = load_config(REPO / "config" / "default_experiment.yaml")
    again = ExperimentConfig.model_validate(dump_config(cfg))
    assert again == cfg


def test_the_dumped_config_is_json_safe():
    """It is written into ``metrics.json`` and must survive that round trip."""
    import json

    cfg = load_config(REPO / "config" / "default_experiment.yaml")
    json.dumps(dump_config(cfg))  # raises if anything is not serialisable
