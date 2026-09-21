"""Report and figure generation, with the scope boundary applied structurally."""

from .plots import figure_paths, plot_block_size_curve, plot_measured_vs_extrapolated
from .report_generator import (
    SCOPE_BOUNDARY,
    assert_boundary_precedes_first_table,
    generate_report,
    generate_report_from_run_dir,
    load_results,
)

__all__ = [
    "SCOPE_BOUNDARY",
    "assert_boundary_precedes_first_table",
    "figure_paths",
    "generate_report",
    "generate_report_from_run_dir",
    "load_results",
    "plot_block_size_curve",
    "plot_measured_vs_extrapolated",
]
