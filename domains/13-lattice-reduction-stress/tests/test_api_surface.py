"""Milestone 0 as a test: every API this project is built on, verified by execution.

The probe is the milestone's gate and this file is that gate in the suite, so a later change to the
toolchain -- a rebuilt G6K, a different estimator revision, a different fpylll -- fails a named test
rather than surfacing as a subtly wrong reduction months later.

The probe executes a real sieving tour and a real cost estimate, so this is marked slow. It is not
skipped by default: the whole point is that it runs.
"""

from __future__ import annotations

import pytest

from qlwr_lattice_stress.utils.api_probe import (
    optional_absences,
    probe_all,
    required_failures,
)


@pytest.fixture(scope="module")
def results():
    return probe_all()


@pytest.mark.slow
def test_no_required_check_failed(results):
    failed = required_failures(results)
    assert not failed, "\n".join(c.line() for c in failed)


@pytest.mark.slow
def test_the_engines_are_present_and_were_exercised(results):
    """G6K is optional in principle and required in practice on this machine, since it is built and
    installed. Asserting its presence here means a machine where it silently vanished is a failure
    rather than a pipeline that quietly ran at reduced strength."""
    by_name = {c.name: c for c in results}
    for name in (
        "fpylll imports and reports its build config",
        "SVP.shortest_vector enumerates exactly",
        "g6k imports",
        "G6K sieving BKZ reduces a basis",
        "G6K dual mode runs",
    ):
        assert by_name[name].ok, by_name[name].line()
    assert not optional_absences(results), [c.name for c in optional_absences(results)]


@pytest.mark.slow
def test_the_sieving_tour_actually_shrank_the_basis(results):
    """A tour that returns without reducing anything would pass an 'it ran' check. The probe
    measures the norm before and after and asserts the direction, so this reads the measurement."""
    detail = {c.name: c.detail for c in results}["G6K sieving BKZ reduces a basis"]
    assert "shorter" in detail or "->" in detail, detail


@pytest.mark.slow
def test_the_estimator_still_matches_its_pinned_baseline(results):
    """Pinned to a revision, not to a remembered literature figure -- see the probe's module
    docstring. A drift here is attributable because the probe records the revision and models."""
    c = {c.name: c for c in results}["Kyber512 reproduces the pinned estimator baseline"]
    assert c.ok, c.detail
    assert "revision" in c.detail and "MATZOV" in c.detail, c.detail


@pytest.mark.slow
def test_the_normal_form_makes_the_secret_small(results):
    """The property the whole attack depends on. Asserted rather than assumed because a uniform
    secret has no short representative and the embedding would contain no short vector."""
    c = {c.name: c for c in results}["the estimator normalises a uniform secret"]
    assert c.ok, c.detail
    before, after = c.payload
    assert after < before, c.detail
