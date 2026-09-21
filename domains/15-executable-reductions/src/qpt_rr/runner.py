"""Run a reduction against an adversary, many times, in both worlds, and judge what happened.

For one (reduction, adversary) pair, each trial plays the adversary twice from the same random
seed: once in the **real** game, once inside the **reduction's simulation**, which has been handed
a fresh hard-problem instance whose answer only the runner knows. Four questions are then asked, in
order of how damning a "no" is:

1. **Sound?** Did the reduction ever output something that is *not* a solution? One such output and
   the reduction is wrong, whatever else is true.
2. **Did the simulation run?** A reduction that has to stop because it cannot do what its proof
   says — :class:`~qpt_rr.reductions.SimulationFailed` — has not simulated the game for that
   adversary. The proof's claim is about *every* adversary the game allows.
3. **Indistinguishable?** Does the adversary win as often in the simulation as in the real game?
   (Compared with a pooled two-proportion z-score; a failed simulation counts as a loss, because
   from the adversary's side that is what it is.)
4. **As tight as claimed?** The conversion rate — how often the reduction solves its instance,
   relative to how often the adversary wins the real game — against the rate the theorem claims.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Callable

from .frame_game import RealFrameGame
from .problems import is_collision, sample_af1, solves_af1
from .reductions import EvasionToCollision, SimulationFailed
from .scheme import HandleCoincidence, Params, Scheme

__all__ = ["Experiment", "Result", "run_frame_experiment", "run_evasion_experiment", "HOLDS",
           "HOLDS_WITH_LOSS", "FAILS", "VACUOUS"]

HOLDS, HOLDS_WITH_LOSS, FAILS, VACUOUS = "HOLDS", "HOLDS, WITH LOSS", "FAILS", "NOT EXERCISED"
Z_LIMIT = 4.0          # a real-versus-simulated gap this many standard errors wide is not noise
RATE_SLACK = 0.12      # absolute tolerance on a measured conversion rate


@dataclass
class Experiment:
    key: str
    theorem: str
    reduction_name: str
    adversary_name: str
    expect: str                     # what a correct runner should report, fixed before running
    role: str = "subject"           # or "control"
    note: str = ""


@dataclass
class Result:
    experiment: Experiment
    trials: int
    real_wins: int
    simulated_wins: int
    simulation_failures: int
    solved: int
    invalid_outputs: int
    claimed_conversion: float
    aborting_is_claimed: bool = False
    """True for a reduction whose *statement* includes giving up — a guessing reduction claims to
    succeed one time in q, so its aborts are the claim and not a failure of it. Such a reduction is
    judged on soundness and on its conversion rate, and can at best hold *with loss*."""
    verdict: str = ""
    reasons: list[str] = field(default_factory=list)
    failure_messages: dict[str, int] = field(default_factory=dict)
    params: dict = field(default_factory=dict)

    @property
    def conversion(self) -> float | None:
        return self.solved / self.real_wins if self.real_wins else None

    @property
    def z_score(self) -> float:
        a, b, n = self.real_wins, self.simulated_wins, self.trials
        pooled = (a + b) / (2 * n)
        spread = math.sqrt(max(pooled * (1 - pooled) * 2 / n, 1e-12))
        return (a - b) / n / spread

    def to_dict(self) -> dict:
        return asdict(self) | {"conversion": self.conversion, "z_score": self.z_score}


def _judge(result: Result) -> None:
    reasons = []
    if result.invalid_outputs:
        reasons.append(f"UNSOUND: {result.invalid_outputs} output(s) did not solve the hard problem")
    if result.simulation_failures and not result.aborting_is_claimed:
        reasons.append(f"the simulation could not be carried out in {result.simulation_failures} of "
                       f"{result.trials} trials")
    if result.real_wins and abs(result.z_score) > Z_LIMIT and not result.aborting_is_claimed:
        reasons.append(f"distinguishable: the adversary wins {result.real_wins}/{result.trials} real "
                       f"games but {result.simulated_wins}/{result.trials} simulated ones "
                       f"(z = {result.z_score:.1f})")
    if result.real_wins and result.conversion is not None \
            and result.conversion < result.claimed_conversion - RATE_SLACK:
        reasons.append(f"conversion {result.conversion:.2f} is below the claimed "
                       f"{result.claimed_conversion:.2f}")
    if reasons:
        result.verdict = FAILS
    elif not result.real_wins:
        result.verdict = VACUOUS
        reasons.append("the adversary never won, so the conversion was never exercised; what this "
                       "shows is only that the reduction output nothing wrong")
    elif result.aborting_is_claimed:
        result.verdict = HOLDS_WITH_LOSS
        reasons.append(f"sound, and converts at {result.conversion:.2f} against the {result.claimed_conversion:.2f} "
                       f"it claims — a loss factor of about {1 / max(result.conversion, 1e-9):.1f}, paid "
                       f"in {result.simulation_failures} aborted simulations of {result.trials}")
    else:
        result.verdict = HOLDS
        reasons.append(f"sound, simulated in every trial, indistinguishable (z = {result.z_score:.1f}), "
                       f"conversion {result.conversion:.2f} against a claimed "
                       f"{result.claimed_conversion:.2f}")
    result.reasons = reasons


def run_frame_experiment(experiment: Experiment, params: Params, make_reduction: Callable,
                         adversary, trials: int, seed: int = 0) -> Result:
    scheme, master = Scheme(params), random.Random(seed)
    counts, failures, claimed = Counter(), Counter(), 1.0
    done = 0
    while done < trials:
        trial_seed = master.getrandbits(48)
        instance, _secret = sample_af1(scheme, random.Random(trial_seed ^ 0x5EED))
        reduction = make_reduction(params, instance, trial_seed)
        claimed = reduction.claimed_success_given_win
        real = RealFrameGame(params, trial_seed)
        try:
            real_won = real.judge(adversary.run(real, random.Random(trial_seed))).adversary_won
            try:
                outcome = reduction.judge(adversary.run(reduction, random.Random(trial_seed)))
            except SimulationFailed as error:
                outcome, failure = None, str(error)
        except HandleCoincidence:
            counts["redrawn"] += 1          # a toy-width artefact, in either world: redraw the pair
            continue
        done += 1
        counts["real"] += real_won
        if outcome is None:
            counts["failed"] += 1
            failures[failure] += 1
            continue
        counts["simulated"] += outcome.adversary_won
        answer = reduction.solve(outcome)
        if answer is not None:
            counts["solved" if solves_af1(scheme, instance, answer) else "invalid"] += 1

    result = Result(experiment, trials, counts["real"], counts["simulated"], counts["failed"],
                    counts["solved"], counts["invalid"], claimed,
                    aborting_is_claimed=claimed < 1.0, failure_messages=dict(failures),
                    params=asdict(params) | {"trials_redrawn_for_handle_coincidence": counts["redrawn"]})
    _judge(result)
    return result


def run_evasion_experiment(experiment: Experiment, params: Params, adversary, trials: int,
                           seed: int = 0) -> Result:
    """A-F2 needs no embedding, so the reduction's world is the real one and the two win counts are
    the same number by construction; soundness and conversion are what is tested."""
    master, counts = random.Random(seed), Counter()
    done = 0
    while done < trials:
        trial_seed = master.getrandbits(48)
        reduction = EvasionToCollision(params, trial_seed)
        try:
            outcome = reduction.judge(adversary.run(reduction, random.Random(trial_seed)))
        except HandleCoincidence:
            counts["redrawn"] += 1
            continue
        done += 1
        counts["wins"] += outcome.adversary_won
        answer = reduction.solve(outcome)
        if answer is not None:
            counts["solved" if is_collision(reduction.scheme, answer) else "invalid"] += 1
        counts["named"] += len(outcome.named)
    result = Result(experiment, trials, counts["wins"], counts["wins"], 0, counts["solved"],
                    counts["invalid"], EvasionToCollision.claimed_success_given_win,
                    params=asdict(params) | {"seats_named_in_total": counts["named"],
                                             "trials_redrawn_for_handle_coincidence": counts["redrawn"]})
    _judge(result)
    return result
