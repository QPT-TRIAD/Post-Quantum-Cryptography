"""Seeding, tested directly: the derivation is stable, injective, and the record catches tampering.

``RunSeeds`` is covered elsewhere through the things that use it — a CLI run, a corpus spec — and
every one of those tests would still pass if ``derive_seed`` were quietly replaced by ``hash()``,
because they only ever compare a run with itself inside one process. The claim the module makes is
about *other* processes: the same description gives the same integer under a different
``PYTHONHASHSEED``, on another machine, next year. The only test of that is a literal, so the golden
values below are literals, cross-checked against a second spelling of the digest written out here
from the module's documented encoding, and re-derived once in a subprocess with a different hash salt.

The second half is the record. ``verify()`` is what turns a results file from a log into a check, and
a check that has never been seen to fail is not known to be one — so the record is edited three ways
(a seed, a part, the root) and each edit has to be caught.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from grover_emulator.utils.seeding import DOMAIN, SEED_BITS, RunSeeds, derive_seed, rng_for

SRC = Path(__file__).resolve().parents[1] / "src"

# Computed once and written down. If either changes, every seed in every published record changes
# with it, and ``DOMAIN`` is what should have been bumped instead.
GOLDEN_LMOTS_10_2 = 13207396178030619722  # derive_seed("lmots_chain", 10, 2)
GOLDEN_EMPTY = 10482138899018809496  # derive_seed()


def spelled_out(*parts) -> int:
    """The documented derivation written a second time: blake2b-64 over tag, 8-byte length, payload.

    The domain separator is a literal here, not the imported constant, so a changed ``DOMAIN`` is a
    failure rather than something both sides silently follow.
    """
    h = hashlib.blake2b(digest_size=8)
    h.update(b"grover-oracle-emulator/seed/v1")
    for part in parts:
        if isinstance(part, bool):
            tag, payload = b"l", (b"1" if part else b"0")
        elif isinstance(part, int):
            tag, payload = b"i", str(part).encode("ascii")
        elif isinstance(part, str):
            tag, payload = b"s", part.encode("utf-8")
        elif isinstance(part, bytes):
            tag, payload = b"b", part
        else:
            assert part is None
            tag, payload = b"n", b""
        h.update(tag + len(payload).to_bytes(8, "big") + payload)
    return int.from_bytes(h.digest(), "big")


parts_strategy = st.lists(
    st.one_of(st.integers(-(2**70), 2**70), st.text(max_size=12), st.binary(max_size=12), st.none(), st.booleans()),
    max_size=5,
)


# -----------------------------------------------------------------------------------------------
# derive_seed
# -----------------------------------------------------------------------------------------------


def test_the_derivation_is_pinned_to_golden_values():
    assert DOMAIN == b"grover-oracle-emulator/seed/v1"
    assert SEED_BITS == 64
    assert derive_seed("lmots_chain", 10, 2) == GOLDEN_LMOTS_10_2
    assert derive_seed() == GOLDEN_EMPTY
    assert spelled_out("lmots_chain", 10, 2) == GOLDEN_LMOTS_10_2


def test_the_derivation_does_not_depend_on_the_hash_salt():
    """A fresh interpreter under a different ``PYTHONHASHSEED`` derives the same integer.

    This is the failure the module's docstring is written against: ``hash("lmots_chain")`` differs
    between these two processes, and a seed built on it would too.
    """
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]);"
        "from grover_emulator.utils.seeding import derive_seed;"
        "print(derive_seed('lmots_chain', 10, 2), hash('lmots_chain'))"
    )
    outputs = []
    for salt in ("1", "2"):
        env = {**os.environ, "PYTHONHASHSEED": salt}
        result = subprocess.run(
            [sys.executable, "-c", code, str(SRC)], capture_output=True, text=True, env=env, check=True
        )
        outputs.append(result.stdout.split())
    assert outputs[0][0] == outputs[1][0] == str(GOLDEN_LMOTS_10_2)
    assert outputs[0][1] != outputs[1][1], "the two interpreters were meant to have different hash salts"


@settings(deadline=None, max_examples=200)
@given(parts_strategy)
def test_every_seed_is_the_documented_digest_and_fits_in_a_machine_word(parts):
    seed = derive_seed(*parts)
    assert seed == spelled_out(*parts)
    assert 0 <= seed < 2**64
    assert derive_seed(*parts) == seed


def test_moving_a_part_boundary_changes_the_seed():
    """``("ab", "c")`` is not ``("a", "bc")`` — the case the length prefix exists for."""
    assert derive_seed("ab", "c") != derive_seed("a", "bc")
    assert derive_seed("ab", "c") != derive_seed("abc")
    assert derive_seed("abc") != derive_seed("abc", "")
    assert derive_seed(12, 3) != derive_seed(1, 23)


@settings(deadline=None, max_examples=200)
@given(st.text(min_size=2, max_size=20), st.data())
def test_no_two_splits_of_one_string_share_a_seed(text, data):
    i = data.draw(st.integers(0, len(text)))
    j = data.draw(st.integers(0, len(text)).filter(lambda v: v != i))
    assert derive_seed(text[:i], text[i:]) != derive_seed(text[:j], text[j:])


@settings(deadline=None, max_examples=200)
@given(parts_strategy, parts_strategy)
def test_different_descriptions_give_different_seeds(a, b):
    """Injective encoding plus a 64-bit digest: distinct part sequences do not collide in practice.

    Equality of descriptions is type-aware — ``1``, ``True`` and ``"1"`` are three descriptions —
    which is why the comparison is on ``(type, value)`` pairs rather than on the lists themselves.
    """
    typed_a = [(type(p).__name__, p) for p in a]
    typed_b = [(type(p).__name__, p) for p in b]
    assert (derive_seed(*a) == derive_seed(*b)) is (typed_a == typed_b)


def test_the_type_of_a_part_is_part_of_the_description():
    spellings = [1, "1", b"1", True]
    assert len({derive_seed(v) for v in spellings}) == 4
    assert len({derive_seed(v) for v in (None, "", b"", 0, False)}) == 5
    assert derive_seed(b"ab") == derive_seed(bytearray(b"ab"))


def test_order_matters():
    assert derive_seed("spec", 10, 2) != derive_seed("spec", 2, 10)
    assert derive_seed(10, "spec") != derive_seed("spec", 10)


@pytest.mark.parametrize("part", [1.5, (1, 2), [1], {"n": 1}, object(), np.int64(3)])
def test_a_part_that_has_no_stable_spelling_is_a_type_error(part):
    """A float's ``repr`` is a property of the platform's printing, and a NumPy integer is not an ``int``.

    Refusing both is the point: a seed derived from either could not be re-derived from the JSON
    record, which holds neither type.
    """
    with pytest.raises(TypeError, match="parts must be int, str, bytes, or None"):
        derive_seed("spec", part)


# -----------------------------------------------------------------------------------------------
# rng_for
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [-1, -(2**63)])
def test_a_negative_seed_is_refused_with_its_value(seed):
    with pytest.raises(ValueError, match=f"seed must be non-negative, got {seed}"):
        rng_for(seed)


@pytest.mark.parametrize("seed", [0, 20260913, GOLDEN_LMOTS_10_2, 2**64 - 1])
def test_the_same_seed_replays_the_same_stream(seed):
    """Two generators, not one shared one: each call is fresh, and each is NumPy's default stream."""
    a, b = rng_for(seed), rng_for(seed)
    assert a is not b
    first = a.integers(0, 2**63, size=16)
    assert np.array_equal(first, b.integers(0, 2**63, size=16))
    assert np.array_equal(first, np.random.default_rng(seed).integers(0, 2**63, size=16))


def test_different_seeds_give_different_streams():
    draws = {tuple(rng_for(seed).integers(0, 2**63, size=4).tolist()) for seed in range(50)}
    assert len(draws) == 50


# -----------------------------------------------------------------------------------------------
# RunSeeds: handing out seeds
# -----------------------------------------------------------------------------------------------


def test_a_derived_seed_is_the_root_followed_by_the_parts_and_is_recorded():
    seeds = RunSeeds(root=20260913)
    seed = seeds.derive("spec", 10, 2)
    assert seed == derive_seed(20260913, "spec", 10, 2) == spelled_out(20260913, "spec", 10, 2)
    assert seeds.derived == {"spec.10.2": {"parts": ["spec", 10, 2], "seed": seed}}
    # Idempotent: asking again returns the same integer and does not grow the record.
    assert seeds.derive("spec", 10, 2) == seed
    assert len(seeds.derived) == 1
    assert RunSeeds(root=20260914).derive("spec", 10, 2) != seed


def test_the_recorded_generator_is_the_generator_of_the_recorded_seed():
    seeds = RunSeeds(root=5)
    drawn = seeds.rng("instance", 12).integers(0, 2**63, size=8)
    recorded = seeds.derived["instance.12"]["seed"]
    assert np.array_equal(drawn, rng_for(recorded).integers(0, 2**63, size=8))


def test_two_descriptions_that_share_a_label_are_refused_not_merged():
    seeds = RunSeeds(root=7)
    seeds.derive("a.b", "c")
    with pytest.raises(ValueError, match="'a.b.c' is already recorded with a different seed"):
        seeds.derive("a", "b.c")
    assert seeds.derived["a.b.c"]["parts"] == ["a.b", "c"]


def test_a_root_drawn_from_the_os_is_recorded_as_drawn():
    drawn, again = RunSeeds.new(), RunSeeds.new()
    assert drawn.auto_root is True
    assert 0 <= drawn.root < 2**SEED_BITS
    assert drawn.root != again.root
    assert drawn.to_dict()["auto_root"] is True
    assert "drawn" in str(drawn)

    # The drawn root is all a reader needs: a record rebuilt from it re-derives the same seeds.
    seed = drawn.derive("spec", 8)
    replay = RunSeeds.new(drawn.root)
    assert replay.derive("spec", 8) == seed


def test_a_supplied_root_is_recorded_as_supplied():
    seeds = RunSeeds.new(0)  # 0 is a root, not "no root"
    assert (seeds.root, seeds.auto_root) == (0, False)
    assert "supplied" in str(seeds)
    assert RunSeeds.new(20260913) == RunSeeds(root=20260913)


def test_measured_facts_are_stored_in_a_form_json_can_write():
    seeds = RunSeeds(root=1)
    seeds.record("m", np.int64(3))
    seeds.record("fraction", np.float64(0.25))
    seeds.record("unique", np.bool_(True))
    seeds.record("marked", (np.int32(7), [np.int64(9)]))
    seeds.record("nested", {1: np.int64(2)})
    assert seeds.facts == {"m": 3, "fraction": 0.25, "unique": True, "marked": [7, [9]], "nested": {"1": 2}}
    assert [type(v) for v in (seeds.facts["m"], seeds.facts["fraction"], seeds.facts["unique"])] == [int, float, bool]
    assert json.loads(json.dumps(seeds.to_dict()))["facts"] == seeds.facts


def test_describe_summarises_the_record():
    seeds = RunSeeds(root=3)
    seeds.derive("b")
    seeds.derive("a", 1)
    seeds.record("m", 1)
    assert seeds.describe() == {
        "root": 3,
        "auto_root": False,
        "n_derived": 2,
        "labels": ["a.1", "b"],
        "facts": {"m": 1},
    }


# -----------------------------------------------------------------------------------------------
# RunSeeds: the record as a check
# -----------------------------------------------------------------------------------------------


def record_with_three_entries() -> RunSeeds:
    seeds = RunSeeds(root=20260913)
    seeds.derive("instance", 12, 2)
    seeds.derive("control", 8, None, True)
    seeds.derive("sampler")
    return seeds


def test_an_untouched_record_verifies_before_and_after_a_json_round_trip():
    seeds = record_with_three_entries()
    seeds.verify()
    replay = RunSeeds.from_dict(json.loads(json.dumps(seeds.to_dict())))
    replay.verify()
    assert replay == seeds
    # from_dict copies: editing the replay does not reach back into the original.
    replay.derived["sampler"]["seed"] += 1
    seeds.verify()


def test_an_edited_seed_is_caught_and_named():
    seeds = record_with_three_entries()
    seeds.derived["control.8.None.True"]["seed"] ^= 1
    with pytest.raises(ValueError, match=r"'control\.8\.None\.True' does not re-derive"):
        seeds.verify()


def test_an_edited_part_is_caught():
    """The run said width 12; the record now says 14 with the seed of 12."""
    seeds = record_with_three_entries()
    seeds.derived["instance.12.2"]["parts"][1] = 14
    with pytest.raises(ValueError, match="'instance.12.2' does not re-derive"):
        seeds.verify()


def test_a_part_whose_type_was_changed_is_caught():
    """``12`` rewritten as ``"12"`` reads the same in a report and is a different description."""
    seeds = record_with_three_entries()
    seeds.derived["instance.12.2"]["parts"][1] = "12"
    with pytest.raises(ValueError, match="does not re-derive"):
        seeds.verify()


def test_an_edited_root_invalidates_every_entry():
    record = record_with_three_entries().to_dict()
    record["root"] += 1
    with pytest.raises(ValueError, match="from root 20260914"):
        RunSeeds.from_dict(record).verify()


def test_a_record_from_another_derivation_does_not_verify():
    """A seed produced by some other scheme — here Python's own ``hash`` — is not accepted as ours."""
    seeds = RunSeeds(root=1)
    seeds.derived["spec.10"] = {"parts": ["spec", 10], "seed": hash(("spec", 10)) % 2**64}
    with pytest.raises(ValueError, match="does not re-derive"):
        seeds.verify()


def test_an_external_seed_is_recorded_and_is_exempt_from_re_derivation():
    seeds = record_with_three_entries()
    seeds.mark("user_supplied", np.int64(424242))
    entry = seeds.derived["user_supplied"]
    assert entry == {"parts": ["<external>"], "seed": 424242}
    assert type(entry["seed"]) is int
    seeds.verify()

    replay = RunSeeds.from_dict(json.loads(json.dumps(seeds.to_dict())))
    assert replay.derived["user_supplied"]["seed"] == 424242
    replay.verify()
    assert "user_supplied" in seeds.describe()["labels"]

    # The exemption is for marked entries only: the derived ones beside it are still checked.
    seeds.derived["sampler"]["seed"] += 1
    with pytest.raises(ValueError, match="'sampler' does not re-derive"):
        seeds.verify()


def test_a_record_with_a_bytes_part_verifies():
    """``bytes`` is a documented part type, so a record that used one must still check out."""
    seeds = RunSeeds(root=7)
    seed = seeds.derive(b"abc", 3)
    assert seed == derive_seed(7, b"abc", 3)
    seeds.verify()
