"""The standard campaign: which reductions, against which adversaries, expecting what.

Every expectation is written down *before* the run, so the report can say where the run disagreed
with it. Controls are included on purpose: an adversary that never wins (the reduction must stay
silent), and a reduction that is broken (the runner must say so).
"""

from __future__ import annotations

from dataclasses import replace

from .adversaries import (BruteForceFramer, CollisionEvader, HonestDoubleSigner, LazyFramer,
                          PreQueryFramer)
from .reductions import FrameToAF1, FrameToAF1Guessing, FrameToAF1WrongSeat
from .runner import (FAILS, HOLDS, HOLDS_WITH_LOSS, VACUOUS, Experiment, Result,
                     run_evasion_experiment, run_frame_experiment)
from .scheme import Params

__all__ = ["run_campaign", "NOT_RUNNABLE", "DECOYS"]

DECOYS = 3
T1, T2 = "Theorem 1 (non-frameability, 'tight')", "Theorem 2 step 2 (binding / evasion)"

#: Parts of the record's argument for which this runner has nothing to execute, and why. Listed in
#: every report: an untested step passed over in silence reads as a tested one.
NOT_RUNNABLE = [
    ("Theorem 3 — QROM soundness of the proof system",
     "A quantum random-oracle bound, and by the record's own account transplanted from FAEST v2 "
     "Lemma 9.39 rather than re-derived. There is no classical program to run; here the proof "
     "system is replaced by an ideal prover whose soundness error is zero by construction."),
    ("Theorem 2 step 2 — obtaining the two openings",
     "The record runs a QROM online extractor on both proofs (DFMS22, time O(q^2)). This runner "
     "reads the openings the ideal prover was shown instead. The collision logic is tested; the "
     "extraction that feeds it is not."),
    ("Assumption A-P — privacy from one-wayness",
     "The record says: 'We do not claim a tight decision-to-search reduction.' No constructive "
     "reduction is given, so there is nothing to run. Theorem 4 (privacy) rests on A-P as a "
     "separate assumption."),
    ("Theorem 4 — privacy",
     "A simulation argument in the QROM (GHHM21 adaptive reprogramming) over the real proof system; "
     "not executable against an ideal prover."),
]


def run_campaign(n: int = 8, trials: int = 60, seed: int = 20260921, progress=None) -> list[Result]:
    params = Params(n=n)
    salted = replace(params, salted=True)
    evasion_params = Params(n=min(n, 7) if min(n, 7) % 3 else 5)     # the collision costs 2^(2n)
    plan = [
        (Experiment("t1_plain", T1, FrameToAF1.name, BruteForceFramer().name, HOLDS),
         params, FrameToAF1, BruteForceFramer()),
        (Experiment("t1_quarter", T1, FrameToAF1.name,
                    "brute-force framer with a quarter of the search budget", HOLDS,
                    note="A probabilistic winner: the real and simulated win rates must match."),
         params, FrameToAF1, BruteForceFramer(budget=0.25)),
        (Experiment("t1_lazy", T1, FrameToAF1.name, LazyFramer().name, VACUOUS, role="control",
                    note="The reduction must output nothing at all."),
         params, FrameToAF1, LazyFramer()),
        (Experiment("t1_prequery", T1, FrameToAF1.name, PreQueryFramer().name, FAILS,
                    note="The adversary looks the challenge up before asking for the approval."),
         params, FrameToAF1, PreQueryFramer()),
        (Experiment("t1_guessing", T1, FrameToAF1Guessing.name,
                    f"pre-querying framer hiding its target among {DECOYS} decoys", HOLDS_WITH_LOSS,
                    note=f"Holds only at the reduced rate 1/{DECOYS + 2}: the guessing loss."),
         params, lambda p, i, s: FrameToAF1Guessing(p, i, s, max_messages=DECOYS + 1),
         PreQueryFramer(decoys=DECOYS)),
        (Experiment("t1_salted", T1, FrameToAF1.name + " — on a SALTED scheme (not in the record)",
                    PreQueryFramer().name, HOLDS,
                    note="Candidate repair: the approving seat adds a random salt to the challenge."),
         salted, FrameToAF1, PreQueryFramer()),
        (Experiment("control_broken", T1, FrameToAF1WrongSeat.name, BruteForceFramer().name, FAILS,
                    role="control", note="The runner must catch this."),
         params, FrameToAF1WrongSeat, BruteForceFramer()),
    ]
    results = []
    for experiment, p, make, adversary in plan:
        if progress:
            progress(f"{experiment.key}: {experiment.reduction_name}  vs  {experiment.adversary_name}")
        results.append(run_frame_experiment(experiment, p, make, adversary, trials, seed))

    for experiment, adversary, count in [
        (Experiment("t2_evader", T2, "Theorem 2 step 2: evasion -> collision of F",
                    CollisionEvader().name, HOLDS,
                    note="Openings come from the ideal prover, standing in for the online extractor."),
         CollisionEvader(), max(6, trials // 6)),
        (Experiment("t2_plain", T2, "Theorem 2 step 2: evasion -> collision of F",
                    HonestDoubleSigner().name, VACUOUS, role="control",
                    note="Forensic completeness: every double-signing seat must be named."),
         HonestDoubleSigner(), trials),
    ]:
        if progress:
            progress(f"{experiment.key}: {experiment.reduction_name}  vs  {experiment.adversary_name}")
        results.append(run_evasion_experiment(experiment, evasion_params, adversary, count, seed))
    return results
