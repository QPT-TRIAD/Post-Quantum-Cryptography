"""Seeding: reproducible, extensible, and re-derivable from what a run records."""

from __future__ import annotations

import numpy as np
import pytest

from qlwr_lattice_stress.utils.seeding import RunSeeds, derive_seed, rng_for


def test_derivation_is_deterministic():
    a = derive_seed(20260913, "instance", "base", 0)
    b = derive_seed(20260913, "instance", "base", 0)
    assert a == b


def test_different_paths_give_different_seeds():
    assert derive_seed(1, "base") != derive_seed(1, "secret")


def test_different_roots_give_different_seeds():
    assert derive_seed(1, "base") != derive_seed(2, "base")


def test_parts_are_delimited_not_concatenated():
    """Otherwise ``("ab", "c")`` and ``("a", "bc")`` collide, and two different draws silently
    share a seed — which looks exactly like a reproducible run."""
    assert derive_seed(1, "ab", "c") != derive_seed(1, "a", "bc")


def test_an_integer_part_is_not_confused_with_its_string_form():
    assert derive_seed(1, 7) != derive_seed(1, "7")


def test_a_negative_index_does_not_collide_with_a_large_unsigned_one():
    """A signed fixed-width encoding, so the two are distinct rather than equal modulo 2**64."""
    assert derive_seed(1, -1) != derive_seed(1, (1 << 64) - 1)


def test_adding_a_trailing_part_does_not_change_earlier_seeds():
    """The property that makes the pipeline safe to extend: a new draw appended after an existing
    one must not renumber it, or adding a feature would silently change every recorded result."""
    before = [derive_seed(5, "sweep", i) for i in range(4)]
    after = [derive_seed(5, "sweep", i) for i in range(4)]
    assert before == after
    _ = derive_seed(5, "sweep", "new", "draw")  # a new branch
    assert [derive_seed(5, "sweep", i) for i in range(4)] == before


def test_rng_for_is_reproducible_and_seeded():
    a = rng_for(99, "base").integers(0, 1 << 30, size=8).tolist()
    b = rng_for(99, "base").integers(0, 1 << 30, size=8).tolist()
    c = rng_for(99, "other").integers(0, 1 << 30, size=8).tolist()
    assert a == b and a != c


def test_a_bad_seed_part_is_refused():
    """Silently stringifying an arbitrary object would make the derivation depend on repr, which is
    not stable across runs for every type."""
    with pytest.raises(TypeError, match="use str, int or bytes"):
        derive_seed(1, {"not": "hashable into a seed"})


def test_run_seeds_records_every_derivation():
    rs = RunSeeds(root=7)
    a = rs.derive("instance", "base")
    b = rs.derive("instance", "secret")
    assert a != b
    recorded = rs.to_dict()["derived"]
    # A list of {parts, seed}, not a mapping: a JSON object key must be a string, and stringifying
    # the parts is exactly the type loss that makes an integer index re-derive differently.
    assert [entry["parts"] for entry in recorded] == [
        ["instance", "base"],
        ["instance", "secret"],
    ]
    assert all(isinstance(entry["seed"], int) for entry in recorded)


def test_an_integer_part_survives_the_record():
    rs = RunSeeds(root=5)
    seed = rs.derive("sweep", 3)
    entry = next(e for e in rs.to_dict()["derived"] if e["parts"] == ["sweep", 3])
    assert entry["seed"] == seed
    # and the restored object re-derives that exact seed rather than the string-keyed one
    assert RunSeeds.from_dict(rs.to_dict()).derive("sweep", 3) == seed


def test_rederiving_the_same_path_is_stable():
    rs = RunSeeds(root=7)
    assert rs.derive("x", 1) == rs.derive("x", 1)


def test_verify_passes_for_an_untampered_record():
    rs = RunSeeds(root=11)
    for i in range(5):
        rs.derive("sweep", i)
    rs.verify()


def test_verify_catches_a_tampered_record():
    """The check that a results file can be turned back into the run it describes. Without it the
    record is a claim, not a guarantee."""
    rs = RunSeeds(root=11)
    rs.derive("sweep", 0)
    rs._used["sweep/0"] = 12345
    with pytest.raises(AssertionError, match="no longer reproducible"):
        rs.verify()


def test_round_trip_through_a_results_record():
    rs = RunSeeds(root=13)
    rs.derive("a", 1)
    rs.derive("b", 2)
    restored = RunSeeds.from_dict(rs.to_dict())
    restored.verify()
    assert restored.derive("a", 1) == rs.derive("a", 1)


def test_a_negative_root_is_refused():
    with pytest.raises(ValueError, match="non-negative"):
        RunSeeds(root=-1)


def test_the_rng_is_actually_seeded_not_ambient():
    """Two fresh generators from the same path must agree, which they cannot if the seed came from
    the entropy pool."""
    x = RunSeeds(root=3).rng("k").random(4)
    y = RunSeeds(root=3).rng("k").random(4)
    assert np.array_equal(x, y)
