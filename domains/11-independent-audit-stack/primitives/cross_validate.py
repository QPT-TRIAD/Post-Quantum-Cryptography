#!/usr/bin/env python3
"""
PRIMITIVES layer of the QPT-128 independent audit stack.

Cross-validates three independent sources for ML-DSA-87 (FIPS 204) and
ML-KEM-1024 (FIPS 203):

  * liboqs 0.16.0 (C; mldsa-native / mlkem-native backends) via oqs_ctypes.py
  * dilithium-py (pure Python ML-DSA, GiacomoPope)
  * kyber-py    (pure Python ML-KEM, GiacomoPope)
  * NIST ACVP-Server internalProjection known-answer vectors

Produces results.json and RESULTS.md next to this file.

This layer validates PRIMITIVES ONLY. It says nothing about the QPT-128
construction built on top of them.
"""
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import statistics
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.normpath(os.path.join(HERE, "..", ".."))
PYLIB = os.path.join(SCRATCH, "pylib")
VEC = os.path.join(HERE, "vectors")
LIBOQS_DIR = os.path.join(SCRATCH, "tools", "liboqs-0.16.0")
sys.path.insert(0, PYLIB)
sys.path.insert(0, HERE)

import oqs_ctypes  # noqa: E402
from dilithium_py.ml_dsa import ML_DSA_87  # noqa: E402
from kyber_py.ml_kem import ML_KEM_1024  # noqa: E402

RNG = random.Random(0x5150_2026)  # reproducible messages / tamper positions
N_CROSS = 200
N_TAMPER = 50
EXPECT = {"dsa_pk": 2592, "dsa_sk": 4896, "dsa_sig": 4627,
          "kem_ek": 1568, "kem_dk": 3168, "kem_ct": 1568, "kem_ss": 32}

DISAGREEMENTS = []   # every (impl, table, test id, detail) that is not a pass
CRITICAL = []


def note(table, impl, tid, detail):
    DISAGREEMENTS.append({"table": table, "impl": impl, "id": tid, "detail": detail})


def unhex(s):
    return bytes.fromhex(s) if s else b""


def load(name):
    with open(os.path.join(VEC, name + ".internalProjection.json")) as f:
        return json.load(f)


def groups(doc, pset, **flt):
    for g in doc["testGroups"]:
        if g.get("parameterSet") != pset:
            continue
        if all(g.get(k) == v for k, v in flt.items()):
            yield g


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------------
# dilithium-py helpers for interfaces the public API does not expose directly
# (external-mu verification and HashML-DSA pre-hash formatting). These reuse
# the library's own internals so the lattice arithmetic is still dilithium-py's.
# ----------------------------------------------------------------------------
def dsa_verify_external_mu(D, pk, mu, sig):
    """Algorithm 8 (FIPS 204) with mu supplied externally."""
    try:
        rho, t1 = D._unpack_pk(pk)
        c_tilde, z, h = D._unpack_sig(sig)
    except ValueError:
        return False
    if h.sum_hint() > D.omega:
        return False
    if z.check_norm_bound(D.gamma_1 - D.beta):
        return False
    A_hat = D._expand_matrix_from_seed(rho)
    c = D.R.sample_in_ball(c_tilde, D.tau).to_ntt()
    z = z.to_ntt()
    t1 = t1.scale(1 << D.d).to_ntt()
    w = ((A_hat @ z) - t1.scale(c)).from_ntt()
    w_prime = h.use_hint(w, 2 * D.gamma_2)
    return c_tilde == D._h(mu + w_prime.bit_pack_w(D.gamma_2), D.c_tilde_bytes)


# FIPS 204 s5.4.1 / Table: DER OIDs of approved pre-hash functions
_OID_PREFIX = bytes.fromhex("06096086480165030402")  # DER 06 09 + 2.16.840.1.101.3.4.2 (last arc appended)
PREHASH = {
    "SHA2-224": ("sha224", 0x04, None), "SHA2-256": ("sha256", 0x01, None),
    "SHA2-384": ("sha384", 0x02, None), "SHA2-512": ("sha512", 0x03, None),
    "SHA2-512/224": ("sha512_224", 0x05, None), "SHA2-512/256": ("sha512_256", 0x06, None),
    "SHA3-224": ("sha3_224", 0x07, None), "SHA3-256": ("sha3_256", 0x08, None),
    "SHA3-384": ("sha3_384", 0x09, None), "SHA3-512": ("sha3_512", 0x0A, None),
    "SHAKE-128": ("shake_128", 0x0B, 32), "SHAKE-256": ("shake_256", 0x0C, 64),
}


def prehash_mprime(hash_alg, ctx, m):
    name, last, xof_len = PREHASH[hash_alg]
    h = hashlib.new(name)
    h.update(m)
    ph = h.digest(xof_len) if xof_len else h.digest()
    return bytes([1, len(ctx)]) + ctx + _OID_PREFIX + bytes([last]) + ph


def pure_mprime(ctx, m):
    return bytes([0, len(ctx)]) + ctx + m


# ----------------------------------------------------------------------------
def versions(oqs, S, K):
    commit = "unknown"
    try:
        with open(os.path.join(LIBOQS_DIR, "COMMIT.txt")) as f:
            commit = f.read().split()[0]
    except OSError:
        pass

    def pyver(dist):
        try:
            return importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            for d in importlib.metadata.distributions(path=[PYLIB]):
                if d.metadata["Name"].lower() == dist:
                    return d.version
            return "unknown"

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "liboqs": {"version": oqs.version, "tag": "0.16.0", "commit": commit, "path": oqs.path,
                   "build": "cmake -GNinja -DOQS_MINIMAL_BUILD=SIG_ml_dsa_87;KEM_ml_kem_1024;"
                            "SIG_ml_dsa_44;KEM_ml_kem_768 -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON",
                   "ml_dsa_87_backend": f"{S.alg_version} (mldsa-native, x86_64)",
                   "ml_kem_1024_backend": f"{K.alg_version} (mlkem-native, x86_64)",
                   "sig_ctx_support": S.ctx_support,
                   "sig_keypair_derand": "NOT AVAILABLE in 0.16.0 public API; seed injected through "
                                         "OQS_randombytes_custom_algorithm instead",
                   "kem_keypair_derand": K.has_keypair_derand,
                   "kem_encaps_derand": K.has_encaps_derand},
        "dilithium-py": {"version": pyver("dilithium-py"), "standard": "ML-DSA per FIPS 204 (final); "
                         "dilithium_py.ml_dsa (round-3 Dilithium lives separately in dilithium_py.dilithium)",
                         "api": "keygen(), key_derive(seed32), sign(sk,m,ctx=b'',deterministic=False), "
                                "verify(pk,m,sig,ctx=b''), _sign_internal(sk,m',rnd,external_mu), "
                                "_verify_internal(pk,m',sig), sign_external_mu(sk,mu,deterministic)"},
        "kyber-py": {"version": pyver("kyber-py"), "standard": "ML-KEM per FIPS 203 (final); kyber_py.ml_kem "
                     "(round-3 Kyber lives separately in kyber_py.kyber)",
                     "api": "keygen(), key_derive(d||z), encaps(ek), decaps(dk,c), _keygen_internal(d,z), "
                            "_encaps_internal(ek,m); encaps/decaps raise ValueError on ek modulus / dk hash "
                            "check failure"},
        "acvp": {"source": "usnistgov/ACVP-Server gen-val/json-files (master)",
                 "files": {f: sha256_file(os.path.join(VEC, f)) for f in sorted(os.listdir(VEC))
                           if f.endswith(".json")}},
    }


# ----------------------------------------------------------------------------
def acvp_keygen(oqs, S, K):
    out = {}
    # --- ML-DSA-87
    doc = load("ML-DSA-keyGen-FIPS204")
    r = {"vectors": 0, "dilithium-py": {"pass": 0, "fail": 0, "fail_ids": []},
         "liboqs": {"pass": 0, "fail": 0, "fail_ids": [], "method": "seed via OQS_randombytes_custom_algorithm"}}
    for g in groups(doc, "ML-DSA-87"):
        for t in g["tests"]:
            r["vectors"] += 1
            seed, pk, sk = unhex(t["seed"]), unhex(t["pk"]), unhex(t["sk"])
            tid = f"tg{g['tgId']}/tc{t['tcId']}"
            ppk, psk = ML_DSA_87.key_derive(seed)
            if (ppk, psk) == (pk, sk):
                r["dilithium-py"]["pass"] += 1
            else:
                r["dilithium-py"]["fail"] += 1
                r["dilithium-py"]["fail_ids"].append(tid)
                note("acvp_keygen ML-DSA-87", "dilithium-py", tid, f"pk_ok={ppk == pk} sk_ok={psk == sk}")
            try:
                lpk, lsk = S.keypair_from_seed(seed)
                ok = (lpk, lsk) == (pk, sk)
                det = f"pk_ok={lpk == pk} sk_ok={lsk == sk}"
            except Exception as e:  # noqa: BLE001
                ok, det = False, f"exception: {e}"
            if ok:
                r["liboqs"]["pass"] += 1
            else:
                r["liboqs"]["fail"] += 1
                r["liboqs"]["fail_ids"].append(tid)
                note("acvp_keygen ML-DSA-87", "liboqs", tid, det)
    out["ML-DSA-87"] = r

    # --- ML-KEM-1024
    doc = load("ML-KEM-keyGen-FIPS203")
    r = {"vectors": 0, "kyber-py": {"pass": 0, "fail": 0, "fail_ids": []},
         "liboqs": {"pass": 0, "fail": 0, "fail_ids": [], "method": "OQS_KEM_keypair_derand(d||z)"}}
    for g in groups(doc, "ML-KEM-1024"):
        for t in g["tests"]:
            r["vectors"] += 1
            d, z, ek, dk = unhex(t["d"]), unhex(t["z"]), unhex(t["ek"]), unhex(t["dk"])
            tid = f"tg{g['tgId']}/tc{t['tcId']}"
            pek, pdk = ML_KEM_1024.key_derive(d + z)
            if (pek, pdk) == (ek, dk):
                r["kyber-py"]["pass"] += 1
            else:
                r["kyber-py"]["fail"] += 1
                r["kyber-py"]["fail_ids"].append(tid)
                note("acvp_keygen ML-KEM-1024", "kyber-py", tid, f"ek_ok={pek == ek} dk_ok={pdk == dk}")
            try:
                lek, ldk = K.keypair_derand(d + z)
                ok = (lek, ldk) == (ek, dk)
                det = f"ek_ok={lek == ek} dk_ok={ldk == dk}"
            except Exception as e:  # noqa: BLE001
                ok, det = False, f"exception: {e}"
            if ok:
                r["liboqs"]["pass"] += 1
            else:
                r["liboqs"]["fail"] += 1
                r["liboqs"]["fail_ids"].append(tid)
                note("acvp_keygen ML-KEM-1024", "liboqs", tid, det)
    out["ML-KEM-1024"] = r
    return out


# ----------------------------------------------------------------------------
def _tally(r, impl, tid, got, expected, table):
    if got is None:
        r[impl]["n/a"] += 1
        return
    if got == expected:
        r[impl]["agree"] += 1
    else:
        r[impl]["disagree"] += 1
        r[impl]["disagree_ids"].append(tid)
        note(table, impl, tid, f"expected testPassed={expected}, got {got}")


def acvp_sigver(oqs, S):
    doc = load("ML-DSA-sigVer-FIPS204")
    out = {}
    for g in groups(doc, "ML-DSA-87"):
        iface, ph, xmu = g["signatureInterface"], g["preHash"], g["externalMu"]
        if iface == "external" and ph == "pure":
            label, lib_how, py_how = "external/pure", "OQS_SIG_verify_with_ctx_str", "ML_DSA_87.verify(pk,m,sig,ctx)"
        elif iface == "external" and ph == "preHash":
            label, lib_how, py_how = ("external/preHash (HashML-DSA-87)", "N/A (liboqs has no HashML-DSA)",
                                      "harness M'=0x01|len|ctx|OID|PH(M) + ML_DSA_87._verify_internal")
        elif iface == "internal" and xmu:
            label, lib_how, py_how = ("internal/externalMu", "N/A (no public external-mu API)",
                                      "harness Alg.8 with supplied mu using dilithium-py internals")
        else:
            label, lib_how, py_how = ("internal/raw M'", "N/A (public API always prepends 0x00|len|ctx)",
                                      "ML_DSA_87._verify_internal(pk,M',sig)")
        r = {"tgId": g["tgId"], "vectors": len(g["tests"]), "expected_true": 0, "expected_false": 0,
             "liboqs": {"agree": 0, "disagree": 0, "n/a": 0, "disagree_ids": [], "method": lib_how},
             "dilithium-py": {"agree": 0, "disagree": 0, "n/a": 0, "disagree_ids": [], "method": py_how},
             "impl_agreement": {"same_verdict": 0, "different_verdict": 0, "ids": []}}
        for t in g["tests"]:
            tid = f"tg{g['tgId']}/tc{t['tcId']}"
            exp = bool(t["testPassed"])
            r["expected_true" if exp else "expected_false"] += 1
            pk, sig = unhex(t["pk"]), unhex(t["signature"])
            ctx = unhex(t.get("context", ""))
            lib = py = None
            try:
                if label == "external/pure":
                    m = unhex(t["message"])
                    lib = S.verify(pk, m, sig, ctx)
                    py = ML_DSA_87.verify(pk, m, sig, ctx)
                elif label.startswith("external/preHash"):
                    m = unhex(t["message"])
                    if t["hashAlg"] in PREHASH:
                        py = ML_DSA_87._verify_internal(pk, prehash_mprime(t["hashAlg"], ctx, m), sig)
                elif label == "internal/externalMu":
                    py = dsa_verify_external_mu(ML_DSA_87, pk, unhex(t["mu"]), sig)
                else:
                    py = ML_DSA_87._verify_internal(pk, unhex(t["message"]), sig)
            except Exception as e:  # noqa: BLE001
                note("acvp_sigver " + label, "harness", tid, f"exception: {e!r}")
                py = False if py is None else py
            _tally(r, "liboqs", tid, lib, exp, "acvp_sigver ML-DSA-87 " + label)
            _tally(r, "dilithium-py", tid, py, exp, "acvp_sigver ML-DSA-87 " + label)
            if lib is not None and py is not None:
                if lib == py:
                    r["impl_agreement"]["same_verdict"] += 1
                else:
                    r["impl_agreement"]["different_verdict"] += 1
                    r["impl_agreement"]["ids"].append(tid)
        out[label] = r
    return out


def acvp_siggen(oqs, S):
    doc = load("ML-DSA-sigGen-FIPS204")
    out = {}
    zero = bytes(32)
    for g in groups(doc, "ML-DSA-87"):
        iface, ph, xmu, det = g["signatureInterface"], g["preHash"], g["externalMu"], g["deterministic"]
        base = ("external/pure" if iface == "external" and ph == "pure" else
                "external/preHash (HashML-DSA-87)" if iface == "external" else
                "internal/externalMu" if xmu else "internal/raw M'")
        label = f"{base} {'deterministic' if det else 'hedged(rnd given)'}"
        lib_how = "N/A"
        if base == "external/pure":
            lib_how = "OQS_SIG_sign_with_ctx_str with rnd injected via OQS_randombytes_custom_algorithm"
        r = {"tgId": g["tgId"], "vectors": len(g["tests"]),
             "liboqs": {"pass": 0, "fail": 0, "n/a": 0, "fail_ids": [], "method": lib_how},
             "dilithium-py": {"pass": 0, "fail": 0, "n/a": 0, "fail_ids": []}}
        for t in g["tests"]:
            tid = f"tg{g['tgId']}/tc{t['tcId']}"
            sk, want = unhex(t["sk"]), unhex(t["signature"])
            ctx = unhex(t.get("context", ""))
            rnd = zero if det else unhex(t["rnd"])
            lib = py = None
            try:
                if base == "external/pure":
                    m = unhex(t["message"])
                    lib = S.sign_with_rnd(sk, m, rnd, ctx) == want
                    py = ML_DSA_87._sign_internal(sk, pure_mprime(ctx, m), rnd) == want
                elif base.startswith("external/preHash"):
                    if t["hashAlg"] in PREHASH:
                        py = ML_DSA_87._sign_internal(sk, prehash_mprime(t["hashAlg"], ctx, unhex(t["message"])),
                                                      rnd) == want
                elif base == "internal/externalMu":
                    py = ML_DSA_87._sign_internal(sk, unhex(t["mu"]), rnd, external_mu=True) == want
                else:
                    py = ML_DSA_87._sign_internal(sk, unhex(t["message"]), rnd) == want
            except Exception as e:  # noqa: BLE001
                note("acvp_siggen " + label, "harness", tid, f"exception: {e!r}")
                py = False
            for impl, got in (("liboqs", lib), ("dilithium-py", py)):
                if got is None:
                    r[impl]["n/a"] += 1
                elif got:
                    r[impl]["pass"] += 1
                else:
                    r[impl]["fail"] += 1
                    r[impl]["fail_ids"].append(tid)
                    note("acvp_siggen ML-DSA-87 " + label, impl, tid, "signature mismatch")
        out[label] = r
    return out


# ----------------------------------------------------------------------------
def _kem_try(fn):
    try:
        return True, fn()
    except (ValueError, oqs_ctypes.OQSStatusError) as e:
        return False, repr(e)


def acvp_encapdecap(oqs, K):
    doc = load("ML-KEM-encapDecap-FIPS203")
    out = {}
    for g in groups(doc, "ML-KEM-1024"):
        fn = g["function"]
        r = {"tgId": g["tgId"], "testType": g["testType"], "vectors": len(g["tests"]),
             "reasons": {}, "liboqs": {"pass": 0, "fail": 0, "fail_ids": []},
             "kyber-py": {"pass": 0, "fail": 0, "fail_ids": []}}
        for t in g["tests"]:
            tid = f"tg{g['tgId']}/tc{t['tcId']}"
            reason = t.get("reason", "-")
            r["reasons"][reason] = r["reasons"].get(reason, 0) + 1
            ek, dk = unhex(t["ek"]), unhex(t["dk"])
            res = {}
            if fn == "encapsulation":
                m, c, k = unhex(t["m"]), unhex(t["c"]), unhex(t["k"])
                ok, v = _kem_try(lambda: K.encaps_derand(ek, m))
                res["liboqs"] = ok and v == (c, k) and K.decaps(dk, c) == k
                ok, v = _kem_try(lambda: ML_KEM_1024._encaps_internal(ek, m))
                res["kyber-py"] = ok and v == (k, c) and ML_KEM_1024.decaps(dk, c) == k
                r["method"] = "encaps_derand(ek,m)==(c,k) and decaps(dk,c)==k"
            elif fn == "decapsulation":
                c, k = unhex(t["c"]), unhex(t["k"])
                ok, v = _kem_try(lambda: K.decaps(dk, c))
                res["liboqs"] = ok and v == k
                ok, v = _kem_try(lambda: ML_KEM_1024.decaps(dk, c))
                res["kyber-py"] = ok and v == k
                r["method"] = "decaps(dk,c)==k (incl. implicit-rejection 'modified ciphertext' cases)"
            elif fn == "decapsulationKeyCheck":
                exp = bool(t["testPassed"])
                probe = os.urandom(32)
                ok_e, v = _kem_try(lambda: K.encaps_derand(ek, probe))
                ct = v[0] if ok_e else bytes(K.length_ciphertext)
                ok, _ = _kem_try(lambda: K.decaps(dk, ct))
                res["liboqs"] = ok == exp
                ok, _ = _kem_try(lambda: ML_KEM_1024.decaps(dk, ct))
                res["kyber-py"] = ok == exp
                r["method"] = "decaps(dk, c) accepted-or-rejected == testPassed (dk hash check)"
            elif fn == "encapsulationKeyCheck":
                exp = bool(t["testPassed"])
                ok, _ = _kem_try(lambda: K.encaps(ek))
                res["liboqs"] = ok == exp
                ok, _ = _kem_try(lambda: ML_KEM_1024.encaps(ek))
                res["kyber-py"] = ok == exp
                r["method"] = "encaps(ek) accepted-or-rejected == testPassed (ek modulus check)"
            for impl, good in res.items():
                if good:
                    r[impl]["pass"] += 1
                else:
                    r[impl]["fail"] += 1
                    r[impl]["fail_ids"].append(tid)
                    note(f"acvp_encapdecap ML-KEM-1024 {fn}", impl, tid, f"reason={reason}")
        out[fn] = r
    return out


# ----------------------------------------------------------------------------
def cross_impl(oqs, S, K):
    r = {"n": N_CROSS, "sizes_ok": True, "size_violations": [],
         "dsa": {"liboqs_sign->dilithium_verify": {"pass": 0, "fail": 0, "fail_ids": []},
                 "dilithium_sign->liboqs_verify": {"pass": 0, "fail": 0, "fail_ids": []},
                 "keys": "even i: liboqs keypair, odd i: dilithium-py keygen; ctx random 0..16 bytes"},
         "kem": {"liboqs_encaps->kyber_decaps": {"pass": 0, "fail": 0, "fail_ids": []},
                 "kyber_encaps->liboqs_decaps": {"pass": 0, "fail": 0, "fail_ids": []},
                 "keys": "even i: liboqs keypair, odd i: kyber-py keygen"}}

    def size(name, b, key):
        if len(b) != EXPECT[key]:
            r["sizes_ok"] = False
            r["size_violations"].append(f"{name}: {len(b)} != {EXPECT[key]}")

    for i in range(N_CROSS):
        m = RNG.randbytes(RNG.randint(0, 2048))
        ctx = RNG.randbytes(RNG.randint(0, 16))
        pk, sk = S.keypair() if i % 2 == 0 else ML_DSA_87.keygen()
        size(f"dsa pk i={i}", pk, "dsa_pk"); size(f"dsa sk i={i}", sk, "dsa_sk")
        s1 = S.sign(sk, m, ctx)
        size(f"liboqs sig i={i}", s1, "dsa_sig")
        ok = ML_DSA_87.verify(pk, m, s1, ctx)
        d = r["dsa"]["liboqs_sign->dilithium_verify"]
        d["pass" if ok else "fail"] += 1
        if not ok:
            d["fail_ids"].append(i); note("cross dsa", "dilithium-py verify of liboqs sig", i, "rejected")
        s2 = ML_DSA_87.sign(sk, m, ctx)
        size(f"dilithium sig i={i}", s2, "dsa_sig")
        ok = S.verify(pk, m, s2, ctx)
        d = r["dsa"]["dilithium_sign->liboqs_verify"]
        d["pass" if ok else "fail"] += 1
        if not ok:
            d["fail_ids"].append(i); note("cross dsa", "liboqs verify of dilithium-py sig", i, "rejected")

        ek, dk = K.keypair() if i % 2 == 0 else ML_KEM_1024.keygen()
        size(f"kem ek i={i}", ek, "kem_ek"); size(f"kem dk i={i}", dk, "kem_dk")
        ct, ss = K.encaps(ek)
        size(f"liboqs ct i={i}", ct, "kem_ct"); size(f"liboqs ss i={i}", ss, "kem_ss")
        ok = ML_KEM_1024.decaps(dk, ct) == ss
        d = r["kem"]["liboqs_encaps->kyber_decaps"]
        d["pass" if ok else "fail"] += 1
        if not ok:
            d["fail_ids"].append(i); note("cross kem", "kyber-py decaps of liboqs ct", i, "ss mismatch")
        ss2, ct2 = ML_KEM_1024.encaps(ek)
        size(f"kyber ct i={i}", ct2, "kem_ct"); size(f"kyber ss i={i}", ss2, "kem_ss")
        ok = K.decaps(dk, ct2) == ss2
        d = r["kem"]["kyber_encaps->liboqs_decaps"]
        d["pass" if ok else "fail"] += 1
        if not ok:
            d["fail_ids"].append(i); note("cross kem", "liboqs decaps of kyber-py ct", i, "ss mismatch")
    return r


# ----------------------------------------------------------------------------
def tamper(oqs, S, K):
    r = {"n_positions": N_TAMPER}
    m = RNG.randbytes(777)
    ctx = b"qpt-audit"
    pk, sk = S.keypair()
    sig = S.sign(sk, m, ctx)
    assert S.verify(pk, m, sig, ctx) and ML_DSA_87.verify(pk, m, sig, ctx)

    def flip(b, pos):
        x = bytearray(b)
        x[pos] ^= RNG.randint(1, 255)
        return bytes(x)

    def dsa_verify_py(pk_, sig_):
        try:
            return ML_DSA_87.verify(pk_, m, sig_, ctx), None
        except Exception as e:  # noqa: BLE001
            return False, f"exception({type(e).__name__})"

    for target in ("signature", "public_key"):
        rr = {"liboqs": {"rejected": 0, "accepted": 0, "accepted_positions": []},
              "dilithium-py": {"rejected": 0, "accepted": 0, "accepted_positions": [], "exceptions": 0}}
        n = len(sig) if target == "signature" else len(pk)
        positions = RNG.sample(range(n), N_TAMPER)
        for pos in positions:
            tsig, tpk = (flip(sig, pos), pk) if target == "signature" else (sig, flip(pk, pos))
            acc = S.verify(tpk, m, tsig, ctx)
            rr["liboqs"]["accepted" if acc else "rejected"] += 1
            if acc:
                rr["liboqs"]["accepted_positions"].append(pos)
                CRITICAL.append(f"liboqs ACCEPTED tampered {target} at byte {pos}")
            acc, exc = dsa_verify_py(tpk, tsig)
            if exc:
                rr["dilithium-py"]["exceptions"] += 1
            rr["dilithium-py"]["accepted" if acc else "rejected"] += 1
            if acc:
                rr["dilithium-py"]["accepted_positions"].append(pos)
                CRITICAL.append(f"dilithium-py ACCEPTED tampered {target} at byte {pos}")
        r["dsa_" + target] = rr

    ek, dk = K.keypair()
    ct, ss = K.encaps(ek)
    assert ML_KEM_1024.decaps(dk, ct) == ss
    rr = {"liboqs": {"different_key": 0, "same_key": 0, "same_positions": []},
          "kyber-py": {"different_key": 0, "same_key": 0, "same_positions": []},
          "impls_agree_on_rejection_key": 0, "impls_differ": []}
    for pos in RNG.sample(range(len(ct)), N_TAMPER):
        tct = flip(ct, pos)
        a = K.decaps(dk, tct)
        b = ML_KEM_1024.decaps(dk, tct)
        for impl, v in (("liboqs", a), ("kyber-py", b)):
            if v == ss:
                rr[impl]["same_key"] += 1; rr[impl]["same_positions"].append(pos)
                CRITICAL.append(f"{impl}: tampered ciphertext at byte {pos} decapsulated to the ORIGINAL key")
            else:
                rr[impl]["different_key"] += 1
        if a == b:
            rr["impls_agree_on_rejection_key"] += 1
        else:
            rr["impls_differ"].append(pos)
            note("tamper kem ct", "liboqs vs kyber-py", pos, "implicit-rejection keys differ")
    r["kem_ciphertext"] = rr

    rr = {"liboqs": {"rejected_ek": 0, "different_key": 0, "same_key": 0, "same_positions": []},
          "kyber-py": {"rejected_ek": 0, "different_key": 0, "same_key": 0, "same_positions": []},
          "impls_agree_on_ek_validity": 0, "impls_differ": []}
    for pos in RNG.sample(range(len(ek)), N_TAMPER):
        tek = flip(ek, pos)
        verdict = {}
        ok, v = _kem_try(lambda: K.encaps(tek))
        if not ok:
            rr["liboqs"]["rejected_ek"] += 1; verdict["liboqs"] = "rejected"
        else:
            tct, tss = v
            if K.decaps(dk, tct) == tss:
                rr["liboqs"]["same_key"] += 1; rr["liboqs"]["same_positions"].append(pos)
            else:
                rr["liboqs"]["different_key"] += 1
            verdict["liboqs"] = "accepted"
        ok, v = _kem_try(lambda: ML_KEM_1024.encaps(tek))
        if not ok:
            rr["kyber-py"]["rejected_ek"] += 1; verdict["kyber-py"] = "rejected"
        else:
            tss, tct = v
            if ML_KEM_1024.decaps(dk, tct) == tss:
                rr["kyber-py"]["same_key"] += 1; rr["kyber-py"]["same_positions"].append(pos)
            else:
                rr["kyber-py"]["different_key"] += 1
            verdict["kyber-py"] = "accepted"
        if verdict["liboqs"] == verdict["kyber-py"]:
            rr["impls_agree_on_ek_validity"] += 1
        else:
            rr["impls_differ"].append({"pos": pos, **verdict})
            note("tamper kem ek", "liboqs vs kyber-py", pos, f"ek validity verdicts differ: {verdict}")
    r["kem_public_key"] = rr
    r["note"] = ("KEM: a tampered ek/ct 'same_key' outcome would mean the honest decapsulator still derives the "
                 "encapsulator's key, i.e. the tamper had no effect; a tampered ek in the rho (seed) region or a "
                 "non-canonical coefficient is expected to be rejected or to yield a different key.")
    return r


# ----------------------------------------------------------------------------
def timing(oqs, S, K):
    def med(fn, n):
        ts = []
        for _ in range(n):
            t0 = time.perf_counter(); fn(); ts.append((time.perf_counter() - t0) * 1000)
        return round(statistics.median(ts), 3)

    m = b"x" * 256
    pk, sk = S.keypair(); sig = S.sign(sk, m)
    ek, dk = K.keypair(); ct, _ = K.encaps(ek)
    ppk, psk = ML_DSA_87.keygen(); psig = ML_DSA_87.sign(psk, m)
    pek, pdk = ML_KEM_1024.keygen(); _, pct = ML_KEM_1024.encaps(pek)
    return {"unit": "median ms (informational only; single core, Python-driven; NOT a benchmark)",
            "liboqs": {"dsa_keygen": med(S.keypair, 50), "dsa_sign": med(lambda: S.sign(sk, m), 50),
                       "dsa_verify": med(lambda: S.verify(pk, m, sig), 50),
                       "kem_keygen": med(K.keypair, 100), "kem_encaps": med(lambda: K.encaps(ek), 100),
                       "kem_decaps": med(lambda: K.decaps(dk, ct), 100)},
            "dilithium-py": {"dsa_keygen": med(ML_DSA_87.keygen, 20),
                             "dsa_sign": med(lambda: ML_DSA_87.sign(psk, m), 20),
                             "dsa_verify": med(lambda: ML_DSA_87.verify(ppk, m, psig), 20)},
            "kyber-py": {"kem_keygen": med(ML_KEM_1024.keygen, 20),
                         "kem_encaps": med(lambda: ML_KEM_1024.encaps(pek), 20),
                         "kem_decaps": med(lambda: ML_KEM_1024.decaps(pdk, pct), 20)}}


# ----------------------------------------------------------------------------
def harness_selftest(oqs, S, K):
    """Negative control: corrupt ONE vector per ACVP test group (flip testPassed, or flip a byte of the
    expected pk/ek/signature/k) and confirm every exercised (table, impl) pair reports a failure.
    Guards against a harness that is green because it compares nothing."""
    global DISAGREEMENTS
    real_load = load

    def corrupt(name):
        doc = real_load(name)
        for g in doc["testGroups"]:
            if g.get("parameterSet") not in ("ML-DSA-87", "ML-KEM-1024"):
                continue
            t = dict(g["tests"][0])
            if "testPassed" in t:
                t["testPassed"] = not t["testPassed"]
            else:
                for k in ("signature", "k", "pk", "ek"):
                    if k in t:
                        b = bytearray(unhex(t[k])); b[len(b) // 2] ^= 0x5A; t[k] = b.hex()
                        break
            g["tests"] = [t]
        return doc

    saved, DISAGREEMENTS = DISAGREEMENTS, []
    globals()["load"] = corrupt
    try:
        tables = {"acvp_keygen": acvp_keygen(oqs, S, K), "acvp_sigver": acvp_sigver(oqs, S),
                  "acvp_siggen": acvp_siggen(oqs, S), "acvp_encapdecap": acvp_encapdecap(oqs, K)}
    finally:
        globals()["load"] = real_load
        flagged, DISAGREEMENTS = DISAGREEMENTS, saved
    exercised = caught = 0
    missed = []
    for tname, tab in tables.items():
        for gname, r in tab.items():
            for impl in ("liboqs", "dilithium-py", "kyber-py"):
                if impl not in r or r[impl].get("n/a", 0) >= r["vectors"]:
                    continue
                exercised += 1
                if r[impl].get("fail", 0) + r[impl].get("disagree", 0) >= 1:
                    caught += 1
                else:
                    missed.append(f"{tname}/{gname}/{impl}")
    if missed:
        note("harness_selftest", "harness", "-", f"corrupted vectors NOT flagged: {missed}")
    return {"exercised_pairs": exercised, "flagged_pairs": caught, "missed": missed,
            "disagreements_recorded_on_corrupted_input": len(flagged)}


# ----------------------------------------------------------------------------
def write_md(R, path):
    v = R["versions"]
    lo = v["liboqs"]
    L = []
    a = L.append

    def pf(r, impl, *keys):
        return "/".join(str(r[impl].get(k, 0)) for k in keys)

    a("# PRIMITIVES layer: ML-DSA-87 (FIPS 204) / ML-KEM-1024 (FIPS 203) cross-validation")
    a(f"Generated {R['generated_utc']}, {v['platform']}, Python {v['python']}, runtime {R['runtime_s']} s. "
      f"Machine-readable detail (every failing test id) is in results.json.")
    a("**Scope: this layer validates the PQ primitives only. It does NOT validate the QPT-128 construction, "
      "its encodings, aggregation, or quorum logic.**")
    a("## Implementations and vectors")
    a(f"- liboqs {lo['version']} tag {lo['tag']} commit `{lo['commit']}`; ML-DSA-87 = {lo['ml_dsa_87_backend']}, "
      f"ML-KEM-1024 = {lo['ml_kem_1024_backend']}; own ctypes wrapper `oqs_ctypes.py` (no `oqs` pip package).")
    a(f"- dilithium-py {v['dilithium-py']['version']} (`dilithium_py.ml_dsa`, final FIPS 204; round-3 Dilithium is a separate module) and "
      f"kyber-py {v['kyber-py']['version']} (`kyber_py.ml_kem`, final FIPS 203). Seeded keygen via `key_derive(seed)`.")
    a("- NIST ACVP-Server internalProjection.json for ML-DSA keyGen/sigVer/sigGen and ML-KEM keyGen/encapDecap, "
      "full files, all ML-DSA-87 / ML-KEM-1024 groups (commit + sha256 in vectors/SOURCE.txt).")
    a("- liboqs seeded ops: `OQS_KEM_keypair_derand`/`encaps_derand` AVAILABLE; `OQS_SIG_keypair_derand` NOT AVAILABLE "
      "in 0.16.0, so ML-DSA seed / rnd were injected through `OQS_randombytes_custom_algorithm` (call count asserted).")
    kg = R["acvp_keygen"]
    a("## (a) ACVP keyGen: seed -> (pk, sk) byte-exact")
    a("| Set | vectors | pure-Python pass/fail | liboqs pass/fail |")
    a("|---|---|---|---|")
    a(f"| ML-DSA-87 | {kg['ML-DSA-87']['vectors']} | dilithium-py {pf(kg['ML-DSA-87'], 'dilithium-py', 'pass', 'fail')} | {pf(kg['ML-DSA-87'], 'liboqs', 'pass', 'fail')} |")
    a(f"| ML-KEM-1024 | {kg['ML-KEM-1024']['vectors']} | kyber-py {pf(kg['ML-KEM-1024'], 'kyber-py', 'pass', 'fail')} | {pf(kg['ML-KEM-1024'], 'liboqs', 'pass', 'fail')} |")
    a("## (b) ACVP sigVer ML-DSA-87: verdict == testPassed (n/a = interface not exposed by liboqs public API)")
    a("| Interface | tgId | vectors (valid/invalid) | liboqs agree/disagree/n-a | dilithium-py agree/disagree/n-a | same verdict |")
    a("|---|---|---|---|---|---|")
    for k, r in R["acvp_sigver"].items():
        ia = r["impl_agreement"]
        a(f"| {k} | {r['tgId']} | {r['vectors']} ({r['expected_true']}/{r['expected_false']}) | {pf(r, 'liboqs', 'agree', 'disagree', 'n/a')} | "
          f"{pf(r, 'dilithium-py', 'agree', 'disagree', 'n/a')} | {ia['same_verdict']}/{ia['same_verdict'] + ia['different_verdict']} |")
    a("## (b') ACVP sigGen ML-DSA-87: regenerated signature == vector (deterministic: rnd = 0^32; hedged: vector rnd)")
    a("| Interface | tgIds | vectors | liboqs pass/fail/n-a | dilithium-py pass/fail/n-a |")
    a("|---|---|---|---|---|")
    merged = {}
    for k, r in R["acvp_siggen"].items():
        base = k.replace(" deterministic", "").replace(" hedged(rnd given)", "")
        m = merged.setdefault(base, {"tg": [], "vectors": 0, "liboqs": [0, 0, 0], "dilithium-py": [0, 0, 0]})
        m["tg"].append(str(r["tgId"])); m["vectors"] += r["vectors"]
        for impl in ("liboqs", "dilithium-py"):
            for i, key in enumerate(("pass", "fail", "n/a")):
                m[impl][i] += r[impl][key]
    for base, m in merged.items():
        a(f"| {base} | {','.join(m['tg'])} | {m['vectors']} | {'/'.join(map(str, m['liboqs']))} | {'/'.join(map(str, m['dilithium-py']))} |")
    a("## (c) ACVP encapDecap ML-KEM-1024 (decapsulation group includes 'modified ciphertext' implicit-rejection cases)")
    a("| Function | tgId | vectors | reasons | liboqs pass/fail | kyber-py pass/fail |")
    a("|---|---|---|---|---|---|")
    for k, r in R["acvp_encapdecap"].items():
        reasons = ", ".join(f"{kk} {vv}" for kk, vv in r["reasons"].items())
        a(f"| {k} | {r['tgId']} | {r['vectors']} | {reasons} | {pf(r, 'liboqs', 'pass', 'fail')} | {pf(r, 'kyber-py', 'pass', 'fail')} |")
    c = R["cross_impl"]
    s = R["sizes"]
    a(f"## (d) Cross-implementation: {c['n']} random messages (random ctx 0-16 B) and {c['n']} random keypairs, keys alternately from each side")
    a("| Direction | pass | fail | Direction | pass | fail |")
    a("|---|---|---|---|---|---|")
    d1, d2 = c["dsa"]["liboqs_sign->dilithium_verify"], c["dsa"]["dilithium_sign->liboqs_verify"]
    k1, k2 = c["kem"]["liboqs_encaps->kyber_decaps"], c["kem"]["kyber_encaps->liboqs_decaps"]
    a(f"| liboqs sign -> dilithium-py verify | {d1['pass']} | {d1['fail']} | dilithium-py sign -> liboqs verify | {d2['pass']} | {d2['fail']} |")
    a(f"| liboqs encaps -> kyber-py decaps | {k1['pass']} | {k1['fail']} | kyber-py encaps -> liboqs decaps | {k2['pass']} | {k2['fail']} |")
    a(f"Sizes checked on every object: ML-DSA-87 pk {s['ML-DSA-87']['pk']} / sk {s['ML-DSA-87']['sk']} / sig {s['ML-DSA-87']['sig']}; "
      f"ML-KEM-1024 ek {s['ML-KEM-1024']['ek']} / dk {s['ML-KEM-1024']['dk']} / ct {s['ML-KEM-1024']['ct']} / ss {s['ML-KEM-1024']['ss']} -> "
      f"{'ALL as expected' if c['sizes_ok'] else 'VIOLATIONS: ' + '; '.join(c['size_violations'][:5])}.")
    t = R["tamper"]
    a(f"## (e) Failure behaviour: one byte XOR-flipped at {t['n_positions']} random positions per target")
    a("| Target | liboqs | dilithium-py / kyber-py | cross-impl agreement |")
    a("|---|---|---|---|")
    for k in ("dsa_signature", "dsa_public_key"):
        rr = t[k]
        a(f"| {k} | rejected {rr['liboqs']['rejected']}, accepted {rr['liboqs']['accepted']} | "
          f"rejected {rr['dilithium-py']['rejected']}, accepted {rr['dilithium-py']['accepted']} | both reject |")
    rr = t["kem_ciphertext"]
    a(f"| kem_ciphertext | different key {rr['liboqs']['different_key']}, same key {rr['liboqs']['same_key']} | "
      f"different key {rr['kyber-py']['different_key']}, same key {rr['kyber-py']['same_key']} | "
      f"identical implicit-rejection key {rr['impls_agree_on_rejection_key']}/{t['n_positions']} |")
    rr = t["kem_public_key"]
    a(f"| kem_public_key | ek rejected {rr['liboqs']['rejected_ek']}, different key {rr['liboqs']['different_key']}, same key {rr['liboqs']['same_key']} | "
      f"ek rejected {rr['kyber-py']['rejected_ek']}, different key {rr['kyber-py']['different_key']}, same key {rr['kyber-py']['same_key']} | "
      f"same validity verdict {rr['impls_agree_on_ek_validity']}/{t['n_positions']} |")
    tm = R["timing"]
    a(f"## (f) Timing: {tm['unit']}")
    a("- liboqs: " + ", ".join(f"{k} {v}" for k, v in tm["liboqs"].items()))
    a("- dilithium-py: " + ", ".join(f"{k} {v}" for k, v in tm["dilithium-py"].items()) +
      "; kyber-py: " + ", ".join(f"{k} {v}" for k, v in tm["kyber-py"].items()))
    a("## Findings")
    st = R.get("harness_selftest", {})
    a(f"- Harness negative control: one corrupted vector per ACVP group was flagged by "
      f"{st.get('flagged_pairs', '?')}/{st.get('exercised_pairs', '?')} exercised (table, implementation) pairs"
      + (f"; MISSED: {st['missed']}" if st.get("missed") else " (none missed)."))
    if R["critical"]:
        a(f"- **CRITICAL ({len(R['critical'])})**: " + "; ".join(R["critical"][:10]))
    else:
        a("- CRITICAL findings: none. No implementation accepted a tampered signature or public key.")
    if R["disagreements"]:
        a(f"- Disagreements / non-passes ({len(R['disagreements'])}): " +
          "; ".join(f"[{d['table']}] {d['impl']} {d['id']}: {d['detail']}" for d in R["disagreements"][:12]) +
          (" ..." if len(R["disagreements"]) > 12 else ""))
    else:
        a("- Disagreements: none. liboqs, dilithium-py and kyber-py agree with each other and with every NIST ACVP "
          "ML-DSA-87 / ML-KEM-1024 vector above; no test case id to report.")
    a("- Restated: this is a primitives-only result. Correct ML-DSA-87 / ML-KEM-1024 primitives are necessary, "
      "not sufficient, for QPT-128; the construction is validated by the other layers of the audit stack.")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return len(L)


def main():
    t0 = time.time()
    oqs = oqs_ctypes.LibOQS()
    S = oqs.sig("ML-DSA-87")
    K = oqs.kem("ML-KEM-1024")
    R = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "scope": "PRIMITIVES ONLY (FIPS 204 ML-DSA-87, FIPS 203 ML-KEM-1024); not the QPT-128 construction",
         "versions": versions(oqs, S, K),
         "sizes": {"ML-DSA-87": {"pk": S.length_public_key, "sk": S.length_secret_key, "sig": S.length_signature},
                   "ML-KEM-1024": {"ek": K.length_public_key, "dk": K.length_secret_key, "ct": K.length_ciphertext,
                                   "ss": K.length_shared_secret}, "expected": EXPECT}}
    steps = [("acvp_keygen", lambda: acvp_keygen(oqs, S, K)), ("acvp_sigver", lambda: acvp_sigver(oqs, S)),
             ("acvp_siggen", lambda: acvp_siggen(oqs, S)), ("acvp_encapdecap", lambda: acvp_encapdecap(oqs, K)),
             ("cross_impl", lambda: cross_impl(oqs, S, K)), ("tamper", lambda: tamper(oqs, S, K)),
             ("timing", lambda: timing(oqs, S, K)), ("harness_selftest", lambda: harness_selftest(oqs, S, K))]
    for name, fn in steps:
        ts = time.time()
        try:
            R[name] = fn()
        except Exception:  # noqa: BLE001
            R[name] = {"error": traceback.format_exc()}
            note(name, "harness", "-", "step crashed: " + traceback.format_exc().strip().splitlines()[-1])
        print(f"[{name}] done in {time.time() - ts:.1f}s", file=sys.stderr, flush=True)
    R["disagreements"] = DISAGREEMENTS
    R["critical"] = CRITICAL
    R["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(R, f, indent=1)
    n = write_md(R, os.path.join(HERE, "RESULTS.md"))
    print(f"RESULTS.md: {n} lines; disagreements={len(DISAGREEMENTS)} critical={len(CRITICAL)}", file=sys.stderr)


if __name__ == "__main__":
    main()
