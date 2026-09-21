"""Configuration models for an experiment, and the loader that validates them.

The models live in the package rather than beside the YAML because the installed package cannot
import from a directory that is not installed: ``config/`` at the repository root holds the plan
document, ``default_experiment.yaml``, and nothing else — a second copy of the models there would be
the copy the CLI never uses, and the two would drift silently in favour of whichever copy nothing
reads. See :mod:`grover_emulator.config.schema`.
"""

from .schema import (
    BackendSettings,
    ExperimentConfig,
    OracleSettings,
    OracleType,
    OutputSettings,
    ProbeSettings,
    RunSettings,
    SweepSettings,
    dump_config,
    expected_optimal_iterations,
    load_config,
)

__all__ = [
    "BackendSettings",
    "ExperimentConfig",
    "OracleSettings",
    "OracleType",
    "OutputSettings",
    "ProbeSettings",
    "RunSettings",
    "SweepSettings",
    "dump_config",
    "expected_optimal_iterations",
    "load_config",
]
