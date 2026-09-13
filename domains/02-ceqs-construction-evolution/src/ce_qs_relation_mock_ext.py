#!/usr/bin/env python3
"""
CE-QS relation-mock, extension pass (post-v0.3).

NOT CRYPTOGRAPHIC SOFTWARE and NOT ZERO KNOWLEDGE. This is explicitly
NOT the "CE-QS v0.4" milestone that PQ_CE_QS_finalized_construction_v0_3.md
Section 30 defines (actual VOLE-in-the-Head relation implementation +
measured proof bytes + first formal reductions). That work requires a
real VOLEitH library and is out of scope for a Python mock.

Purpose of this file: v0.3's own Section 22 lists 11 required security
games. The shipped ce_qs_relation_mock_v0_3.py exercises pieces of
games 2 (threshold unforgeability, via forged/wrong-mask rejection),
6 (extraction completeness), 9 (key-binding/no duplicate counting)
and 10 (post-trace unforgeability, partially). This extension closes
the remaining mock-level-checkable gaps before WP1 (the real relation
circuit) starts, so the circuit spec inherits a fully exercised
reference relation rather than a partially exercised one:

  - game 5 (cross-topic unlinkability)      -> new
  - game 4 / Section 4.4 (same-message
    linkability without secret exposure)    -> new
  - identity impersonation (wrong index
    with otherwise-real secrets)            -> new, feeds game 2 & 9
  - below-threshold public rejection        -> new, feeds game 2
  - bounded preimage-guess probe against
    G_mask, post-exposure of x_i            -> new, feeds game 10

Games 3 (quorum anonymity), 7 (trace soundness, formal form), 8
(non-frameability, formal form) and 11 (QROM) are NOT mock-testable:
they are statements about a real proof system's distributions and
about an adversary interacting with the actual VOLEitH transcript,
which does not exist yet. They are listed as still-open in the report,
not silently skipped.
"""
import hashlib
import random

P = 2**255 - 19


def H(data):
    return hashlib.sha256(data).digest()


def Hf(data):
    return int.from_bytes(H(data), "big") % P or 1


def G_trace(x):
    return H(b"TRACE-v3" + x.to_bytes(32, "big"))


def G_mask(k):
    return H(b"MASK-BIND-v3" + k)


def pub_from_sk(sk):
    return H(b"AUTH-v3" + sk)


def prf(k, topic):
    return Hf(b"PRF-v3" + k + topic)


def challenge(topic, msg):
    return Hf(b"CHAL-v3" + topic + H(msg))


def cet(x, k, topic, msg):
    return (prf(k, topic) + challenge(topic, msg) * x) % P


def make_registry(n=64, seed=20260908):
    rng = random.Random(seed)
    reg = []
    sec = []
    for i in range(n):
        sk = bytes(rng.randrange(256) for _ in range(32))
        x = rng.randrange(1, P)
        k = bytes(rng.randrange(256) for _ in range(32))
        reg.append((pub_from_sk(sk), G_trace(x), G_mask(k)))
        sec.append((sk, x, k))
    return reg, sec


def relation(reg, idx, sk, x, k, topic, msg, tag):
    if idx < 0 or idx >= len(reg):
        return False
    pk, X, K = reg[idx]
    return (
        pub_from_sk(sk) == pk
        and G_trace(x) == X
        and G_mask(k) == K
        and cet(x, k, topic, msg) == tag
    )


def contribution(reg, sec, idx, topic, msg):
    sk, x, k = sec[idx]
    e = cet(x, k, topic, msg)
    assert relation(reg, idx, sk, x, k, topic, msg, e)
    return e, (idx, sk, x, k)


def verify_mock_contribution(reg, topic, msg, tag, witness):
    idx, sk, x, k = witness
    return relation(reg, idx, sk, x, k, topic, msg, tag)


def verify_certificate_mock(reg, topic, msg, contributions, q):
    tags = []
    for tag, wit in contributions:
        if not verify_mock_contribution(reg, topic, msg, tag, wit):
            return False, "invalid-relation"
        tags.append(tag)
    if len(tags) < q:
        return False, "below-threshold"
    if len(set(tags)) != len(tags):
        return False, "duplicate-tag"
    return True, "ok"


def extract_x(e0, e1, c0, c1):
    denom = (c0 - c1) % P
    if denom == 0:
        return None
    return ((e0 - e1) * pow(denom, P - 2, P)) % P


def fail(name, msg):
    print(f"FAIL {name:34s} {msg}")
    raise SystemExit(1)


def ok(name, msg=""):
    print(f"PASS {name:34s} {msg}")


def eok(name, msg=""):
    print(f"EXPECTED-FAIL {name:26s} {msg}")


def run():
    n, f, q = 64, 21, 43
    topic0 = b"epoch=8|height=1200|view=4|phase=vote"
    topic1 = b"epoch=8|height=1201|view=0|phase=vote"
    m0, m1 = b"A", b"B"

    reg, sec = make_registry(n)

    # --- Reproduce the v0.3 baseline first, unmodified, as a regression gate ---
    S = list(range(q))
    C = [contribution(reg, sec, i, topic0, m0) for i in S]
    good, why = verify_certificate_mock(reg, topic0, m0, C, q)
    if not good:
        fail("regression_valid_quorum", why)
    ok("regression_valid_quorum", "v0.3 baseline still holds")

    # --- New 1: below-threshold public rejection ---
    short = C[: q - 1]
    good, why = verify_certificate_mock(reg, topic0, m0, short, q)
    if good or why != "below-threshold":
        fail("below_threshold_rejection", f"got ok={good} why={why}")
    eok("below_threshold_rejection", f"{q-1} distinct valid contributions correctly rejected (need >= {q})")

    # --- New 2: cross-topic unlinkability at the relation-mock level ---
    # Same signer, two different topics, same message text is irrelevant here --
    # what matters is that subtracting tags from two DIFFERENT topics must not
    # cancel the PRF mask and must not recover x_i.
    signer = 7
    e_t0, _ = contribution(reg, sec, signer, topic0, m0)
    e_t1, _ = contribution(reg, sec, signer, topic1, m0)
    c_t0 = challenge(topic0, m0)
    c_t1 = challenge(topic1, m0)
    if c_t0 == c_t1:
        fail("cross_topic_unlinkability", "test construction error: challenges collided")
    x_guess = extract_x(e_t0, e_t1, c_t0, c_t1)
    if x_guess is not None and G_trace(x_guess) == reg[signer][1]:
        fail("cross_topic_unlinkability", "cross-topic subtraction falsely recovered the trace secret")
    eok("cross_topic_unlinkability", f"signer={signer} cross-topic tags did not cancel to x_i (as required by Section 15)")

    # --- New 3: same-message linkability without secret exposure (Section 4.4 / anonymity game) ---
    # Same signer, same topic, same message signed "twice" (e.g. re-broadcast):
    # deterministic tags MUST be equal (linkable) but that equality alone must
    # NOT hand the extractor a usable (c0 - c1) pair, since c0 == c1.
    e_again, _ = contribution(reg, sec, signer, topic0, m0)
    if e_again != e_t0:
        fail("same_message_linkability", "deterministic CET was not deterministic -- construction bug")
    same_msg_extract = extract_x(e_t0, e_again, c_t0, challenge(topic0, m0))
    if same_msg_extract is not None:
        fail("same_message_linkability", "same-message repeat incorrectly yielded a defined extraction")
    eok("same_message_linkability", "repeat tag is linkable (equal) but extraction is correctly undefined (c0==c1), matching Section 4.4/14")

    # --- New 4: identity impersonation with an otherwise-valid witness ---
    # Attacker holds their OWN real (sk, x, k) for index `signer`, but claims
    # to be a different registered index `claimed`. The relation must reject
    # this even though every individual secret is genuine and self-consistent.
    claimed = (signer + 5) % n
    sk_s, x_s, k_s = sec[signer]
    tag_s = cet(x_s, k_s, topic0, m1)
    if relation(reg, claimed, sk_s, x_s, k_s, topic0, m1, tag_s):
        fail("identity_impersonation", "relation accepted a real witness bound to the wrong registry index")
    eok("identity_impersonation", f"real secrets of signer={signer} correctly rejected against claimed index={claimed}")

    # --- New 5: bounded preimage-guess probe against G_mask after x_i exposure ---
    # Mirrors v0.2's bounded challenge-collision probe: this is a sanity check
    # on the failure MODE (can a cheap guess forge k_i once x_i is public?),
    # not an attempted cryptanalysis of SHA-256. Finding nothing is the
    # expected and correct outcome.
    exposed_signer = 3
    e0x, _ = contribution(reg, sec, exposed_signer, topic0, m0)
    e1x, _ = contribution(reg, sec, exposed_signer, topic0, m1)
    recovered_x = extract_x(e0x, e1x, challenge(topic0, m0), challenge(topic0, m1))
    if recovered_x is None or G_trace(recovered_x) != reg[exposed_signer][1]:
        fail("post_exposure_probe", "setup error: baseline extraction of exposed_signer failed")
    K_target = reg[exposed_signer][2]
    forged_ok = False
    probe_rng = random.Random(999)
    for _ in range(200000):
        guess_k = bytes(probe_rng.randrange(256) for _ in range(32))
        if G_mask(guess_k) == K_target:
            forged_ok = True
            break
    if forged_ok:
        fail("post_exposure_probe", "found a mask-key preimage within probe budget -- would be a real break, not expected")
    eok("post_exposure_probe", "200000 random guesses for k_i found no G_mask preimage; x_i exposure alone did not yield a forgeable contribution (Section 16)")

    print()
    print("ALL EXTENSION-PASS CHECKS PASSED (5 new + 1 regression gate)")
    print("NOTE: relation mock only. Games 3 (quorum anonymity, formal),")
    print("7 (trace soundness, formal), 8 (non-frameability, formal) and")
    print("11 (QROM) are NOT exercised by this file or by v0.3's script --")
    print("they require the real VOLEitH proof system and are not mockable.")


if __name__ == "__main__":
    run()
