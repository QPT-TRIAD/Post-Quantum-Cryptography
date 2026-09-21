"""The reductions: each result the campaign reports, pinned as a test — including the failure.

The point of this file is that the headline finding is not an accident of one run. The as-written
reduction of Theorem 1 *must* convert every win of an adversary that asks for the approval first,
and *must* be unable to proceed against one that looks the challenge up first; the guessing repair
*must* pay the loss it is predicted to pay; the salted scheme *must* restore the as-written
reduction. And the reduction must never be handed the answer it is supposed to be finding.
"""

from __future__ import annotations

import random
from dataclasses import fields, replace

import pytest

from qpt_rr.adversaries import (BruteForceFramer, CollisionEvader, HonestDoubleSigner, LazyFramer,
                                PreQueryFramer)
from qpt_rr.frame_game import RealFrameGame
from qpt_rr.problems import AF1Instance, is_collision, sample_af1, solves_af1
from qpt_rr.reductions import (EvasionToCollision, FrameToAF1, FrameToAF1Guessing,
                               FrameToAF1WrongSeat, SimulationFailed)
from qpt_rr.scheme import HandleCoincidence, Opening, Params, Scheme

PARAMS = Params(n=8)
SCHEME = Scheme(PARAMS)


def play(make, adversary, seed, params=PARAMS):
    """One simulated game: ``(reduction, instance, outcome or the SimulationFailed raised)``."""
    instance, _ = sample_af1(Scheme(params), random.Random(seed ^ 0x5EED))
    reduction = make(params, instance, seed)
    try:
        return reduction, instance, reduction.judge(adversary.run(reduction, random.Random(seed)))
    except SimulationFailed as failure:
        return reduction, instance, failure


def trials(make, adversary, count, params=PARAMS):
    seed, done = 0, []
    while len(done) < count:
        seed += 1
        try:
            done.append(play(make, adversary, seed, params))
        except HandleCoincidence:
            continue                                   # the toy-width artefact; see scheme.py
    return done


# -- the hard problems' referees --------------------------------------------------------------------


def test_the_af1_checker_accepts_the_secret_and_rejects_anything_else():
    instance, secret = sample_af1(SCHEME, random.Random(1))
    assert solves_af1(SCHEME, instance, secret)
    assert not solves_af1(SCHEME, instance, Opening(secret.s ^ 1, secret.r))
    assert not solves_af1(SCHEME, instance, None)
    assert SCHEME.handle(secret, instance.triple) == instance.handle and SCHEME.is_invertible(instance.triple)


def test_a_reduction_is_never_handed_the_answer():
    """The instance type has no field that could carry the opening, and the reduction's own state
    does not contain it either — it holds openings for every seat *except* the embedded one."""
    assert {f.name for f in fields(AF1Instance)} == {"public_key", "handle", "triple"}
    instance, secret = sample_af1(SCHEME, random.Random(2))
    reduction = FrameToAF1(PARAMS, instance, seed=2)
    assert reduction.honest_seat not in reduction._openings
    assert secret not in reduction._openings.values()
    assert reduction.registry.keys[reduction.honest_seat] == instance.public_key


def test_the_collision_checker_wants_two_different_inputs_with_one_output():
    a = Opening(1, 2)
    assert not is_collision(SCHEME, (a, a)) and not is_collision(SCHEME, None)
    assert not is_collision(SCHEME, (a, Opening(1, 3)))


# -- Theorem 1, as written --------------------------------------------------------------------------


def test_as_written_the_reduction_converts_every_win_of_an_approval_first_adversary():
    for reduction, instance, outcome in trials(FrameToAF1, BruteForceFramer(), 25):
        assert outcome.adversary_won
        assert solves_af1(SCHEME, instance, reduction.solve(outcome))


def test_as_written_the_reduction_cannot_proceed_against_a_challenge_first_adversary():
    """The finding. The same adversary wins the *real* game every time."""
    adversary = PreQueryFramer()
    for reduction, _, outcome in trials(FrameToAF1, adversary, 25):
        assert isinstance(outcome, SimulationFailed)
        assert "programs c(m) := c*" in str(outcome) and "already" in str(outcome)
    wins, seed = 0, 0
    while wins < 25:
        seed += 1
        game = RealFrameGame(PARAMS, seed)
        try:
            assert game.judge(adversary.run(game, random.Random(seed))).adversary_won
        except HandleCoincidence:
            continue
        wins += 1


def test_the_pre_querying_adversary_does_nothing_the_game_forbids():
    """It queries a public oracle, requests one approval, and submits two certificates — the same
    moves as the adversary the reduction handles, in a different order."""
    game = RealFrameGame(PARAMS, seed=5)
    PreQueryFramer().run(game, random.Random(5))
    askers = [who for who, _ in game.oracle.log]
    first_honest = askers.index("honest seat")
    assert "adversary" in askers[:first_honest], "the challenge was looked up before the approval"
    assert len(game._approved) == 1, "one approval in the domain, as the game allows"


def test_programming_lays_down_the_counter_sequence_a_real_oracle_would_have():
    """Every draw before the programmed triple is non-invertible, so the counter the adversary sees
    for the programmed message is distributed as for any other message."""
    instance, _ = sample_af1(SCHEME, random.Random(3))
    lengths = []
    for seed in range(200):
        reduction = FrameToAF1(PARAMS, instance, seed)
        reduction.request_approval(b"m")
        assert reduction.challenge(b"m") == instance.triple
        points = [p for _, p in reduction.oracle.log if p[3] == b"m"]
        lengths.append(len(points))
    fresh = []
    for seed in range(200):
        game = RealFrameGame(PARAMS, seed)
        game.challenge(b"m")
        fresh.append(len(game.oracle.log))
    assert abs(sum(lengths) / 200 - sum(fresh) / 200) < 0.6, "same mean counter in both worlds"
    assert max(lengths) > 1, "and it is not always zero"


def test_the_reduction_stays_silent_for_an_adversary_that_does_not_win():
    for reduction, _, outcome in trials(FrameToAF1, LazyFramer(), 10):
        assert not outcome.adversary_won and reduction.solve(outcome) is None


def test_a_probabilistic_adversary_wins_at_its_budget_in_both_worlds():
    adversary = BruteForceFramer(budget=0.25)
    simulated = sum(o.adversary_won for _, _, o in trials(FrameToAF1, adversary, 120))
    real, seed, count = 0, 0, 0
    while count < 120:
        seed += 1
        game = RealFrameGame(PARAMS, seed)
        try:
            real += game.judge(adversary.run(game, random.Random(seed))).adversary_won
        except HandleCoincidence:
            continue
        count += 1
    assert 12 <= simulated <= 50 and 12 <= real <= 50, "about a quarter, in each"


# -- the repairs, and the control ---------------------------------------------------------------------


def test_the_guessing_repair_is_sound_and_pays_the_predicted_loss():
    decoys = 3
    make = lambda p, i, s: FrameToAF1Guessing(p, i, s, max_messages=decoys + 1)      # noqa: E731
    solved = aborted = 0
    for reduction, instance, outcome in trials(make, PreQueryFramer(decoys=decoys), 200):
        if isinstance(outcome, SimulationFailed):
            aborted += 1
            continue
        answer = reduction.solve(outcome)
        assert answer is None or solves_af1(SCHEME, instance, answer), "never a wrong answer"
        solved += answer is not None
    assert reduction.claimed_success_given_win == pytest.approx(1 / (decoys + 2))
    assert 0.11 <= solved / 200 <= 0.30, "about one in five"
    assert aborted == 200 - solved


def test_salting_the_challenge_restores_the_as_written_reduction():
    salted = replace(PARAMS, salted=True)
    for reduction, instance, outcome in trials(FrameToAF1, PreQueryFramer(), 25, salted):
        assert not isinstance(outcome, SimulationFailed) and outcome.adversary_won
        assert solves_af1(Scheme(salted), instance, reduction.solve(outcome))


def test_the_broken_control_outputs_an_opening_that_does_not_solve_the_instance():
    for reduction, instance, outcome in trials(FrameToAF1WrongSeat, BruteForceFramer(), 15):
        answer = reduction.solve(outcome)
        assert outcome.adversary_won and answer is not None
        assert not solves_af1(SCHEME, instance, answer)


# -- Theorem 2 step 2 -----------------------------------------------------------------------------------


def _evasion(adversary, seed, n=5):
    reduction = EvasionToCollision(Params(n=n), seed)
    return reduction, reduction.judge(adversary.run(reduction, random.Random(seed)))


def test_an_evader_with_two_openings_escapes_and_its_escape_is_a_collision():
    escaped = 0
    for seed in range(1, 40):
        try:
            reduction, outcome = _evasion(CollisionEvader(), seed)
        except HandleCoincidence:
            continue
        if outcome.adversary_won:
            escaped += 1
            assert "were not named" in outcome.reason
            assert is_collision(reduction.scheme, reduction.solve(outcome))
    assert escaped >= 10


def test_a_plain_double_signer_is_always_named_and_gives_the_reduction_nothing():
    checked = 0
    for seed in range(1, 40):
        try:
            reduction, outcome = _evasion(HonestDoubleSigner(), seed, n=8)
        except HandleCoincidence:
            continue
        checked += 1
        assert not outcome.adversary_won and reduction.solve(outcome) is None
        assert {entry.seat for entry in outcome.named} >= set(range(reduction.scheme.params.overlap))
    assert checked >= 20
