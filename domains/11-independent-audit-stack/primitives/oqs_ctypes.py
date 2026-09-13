"""
Thin ctypes wrapper around a locally built liboqs (0.16.0) shared library.

Only the public OQS_SIG / OQS_KEM API is used (no python `oqs` package).
Additionally exposes a *seed injection* helper built on
OQS_randombytes_custom_algorithm so that ACVP seeded vectors can be replayed
through liboqs for ML-DSA (liboqs 0.16.0 has no OQS_SIG_keypair_derand).
"""
import ctypes
import os
import threading

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LIB = os.path.normpath(
    os.path.join(_HERE, "..", "..", "tools", "liboqs-0.16.0", "build", "lib", "liboqs.so")
)


class OQSStatusError(RuntimeError):
    pass


class _OQS_SIG(ctypes.Structure):
    # Layout from liboqs 0.16.0 src/sig/sig.h (typedef struct OQS_SIG)
    _fields_ = [
        ("method_name", ctypes.c_char_p),
        ("alg_version", ctypes.c_char_p),
        ("claimed_nist_level", ctypes.c_uint8),
        ("euf_cma", ctypes.c_bool),
        ("suf_cma", ctypes.c_bool),
        ("sig_with_ctx_support", ctypes.c_bool),
        ("length_public_key", ctypes.c_size_t),
        ("length_secret_key", ctypes.c_size_t),
        ("length_signature", ctypes.c_size_t),
        ("keypair", ctypes.c_void_p),
        ("sign", ctypes.c_void_p),
        ("sign_with_ctx_str", ctypes.c_void_p),
        ("verify", ctypes.c_void_p),
        ("verify_with_ctx_str", ctypes.c_void_p),
    ]


class _OQS_KEM(ctypes.Structure):
    # Layout from liboqs 0.16.0 src/kem/kem.h (typedef struct OQS_KEM)
    _fields_ = [
        ("method_name", ctypes.c_char_p),
        ("alg_version", ctypes.c_char_p),
        ("claimed_nist_level", ctypes.c_uint8),
        ("ind_cca", ctypes.c_bool),
        ("length_public_key", ctypes.c_size_t),
        ("length_secret_key", ctypes.c_size_t),
        ("length_ciphertext", ctypes.c_size_t),
        ("length_shared_secret", ctypes.c_size_t),
        ("length_keypair_seed", ctypes.c_size_t),
        ("length_encaps_seed", ctypes.c_size_t),
        ("keypair_derand", ctypes.c_void_p),
        ("keypair", ctypes.c_void_p),
        ("encaps_derand", ctypes.c_void_p),
        ("encaps", ctypes.c_void_p),
        ("decaps", ctypes.c_void_p),
    ]


_RNG_CB_T = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t)


class LibOQS:
    def __init__(self, path=DEFAULT_LIB):
        self.path = path
        self.lib = ctypes.CDLL(path)
        L = self.lib
        L.OQS_init.restype = None
        L.OQS_version.restype = ctypes.c_char_p
        L.OQS_init()
        self.version = L.OQS_version().decode()

        u8p = ctypes.POINTER(ctypes.c_uint8)
        L.OQS_SIG_new.restype = ctypes.POINTER(_OQS_SIG)
        L.OQS_SIG_new.argtypes = [ctypes.c_char_p]
        L.OQS_SIG_free.argtypes = [ctypes.POINTER(_OQS_SIG)]
        L.OQS_SIG_keypair.argtypes = [ctypes.POINTER(_OQS_SIG), u8p, u8p]
        L.OQS_SIG_sign.argtypes = [ctypes.POINTER(_OQS_SIG), u8p, ctypes.POINTER(ctypes.c_size_t),
                                   u8p, ctypes.c_size_t, u8p]
        L.OQS_SIG_sign_with_ctx_str.argtypes = [ctypes.POINTER(_OQS_SIG), u8p, ctypes.POINTER(ctypes.c_size_t),
                                                u8p, ctypes.c_size_t, u8p, ctypes.c_size_t, u8p]
        L.OQS_SIG_verify.argtypes = [ctypes.POINTER(_OQS_SIG), u8p, ctypes.c_size_t, u8p, ctypes.c_size_t, u8p]
        L.OQS_SIG_verify_with_ctx_str.argtypes = [ctypes.POINTER(_OQS_SIG), u8p, ctypes.c_size_t, u8p, ctypes.c_size_t,
                                                  u8p, ctypes.c_size_t, u8p]
        for f in (L.OQS_SIG_keypair, L.OQS_SIG_sign, L.OQS_SIG_sign_with_ctx_str,
                  L.OQS_SIG_verify, L.OQS_SIG_verify_with_ctx_str):
            f.restype = ctypes.c_int

        L.OQS_KEM_new.restype = ctypes.POINTER(_OQS_KEM)
        L.OQS_KEM_new.argtypes = [ctypes.c_char_p]
        L.OQS_KEM_free.argtypes = [ctypes.POINTER(_OQS_KEM)]
        L.OQS_KEM_keypair.argtypes = [ctypes.POINTER(_OQS_KEM), u8p, u8p]
        L.OQS_KEM_keypair_derand.argtypes = [ctypes.POINTER(_OQS_KEM), u8p, u8p, u8p]
        L.OQS_KEM_encaps.argtypes = [ctypes.POINTER(_OQS_KEM), u8p, u8p, u8p]
        L.OQS_KEM_encaps_derand.argtypes = [ctypes.POINTER(_OQS_KEM), u8p, u8p, u8p, u8p]
        L.OQS_KEM_decaps.argtypes = [ctypes.POINTER(_OQS_KEM), u8p, u8p, u8p]
        for f in (L.OQS_KEM_keypair, L.OQS_KEM_keypair_derand, L.OQS_KEM_encaps,
                  L.OQS_KEM_encaps_derand, L.OQS_KEM_decaps):
            f.restype = ctypes.c_int

        L.OQS_randombytes_custom_algorithm.argtypes = [_RNG_CB_T]
        L.OQS_randombytes_custom_algorithm.restype = None
        L.OQS_randombytes_switch_algorithm.argtypes = [ctypes.c_char_p]
        L.OQS_randombytes_switch_algorithm.restype = ctypes.c_int

        self._rng_lock = threading.Lock()
        self._rng_cb = None  # keep the CFUNCTYPE object alive while installed

    # ----------------------------------------------------------------- RNG
    def inject_randomness(self, chunks):
        """Install a custom RNG that returns the given byte chunks in order.

        Each OQS_randombytes(buf, n) call consumes the next chunk, which must
        be exactly n bytes long; otherwise the call is recorded as a mismatch.
        Returns a dict that records the calls. Always pair with restore_rng().
        """
        state = {"calls": [], "mismatch": False, "exhausted": False}
        queue = list(chunks)

        def cb(buf, n):
            state["calls"].append(int(n))
            if not queue:
                state["exhausted"] = True
                ctypes.memset(buf, 0, n)
                return
            chunk = queue.pop(0)
            if len(chunk) != n:
                state["mismatch"] = True
                chunk = (chunk + b"\x00" * n)[:n]
            ctypes.memmove(buf, chunk, n)

        self._rng_lock.acquire()
        self._rng_cb = _RNG_CB_T(cb)
        self.lib.OQS_randombytes_custom_algorithm(self._rng_cb)
        return state

    def restore_rng(self):
        try:
            self.lib.OQS_randombytes_switch_algorithm(b"system")
        finally:
            self._rng_cb = None
            self._rng_lock.release()

    # ----------------------------------------------------------------- SIG
    def sig(self, name):
        return Sig(self, name)

    def kem(self, name):
        return Kem(self, name)


def _buf(b):
    return (ctypes.c_uint8 * len(b)).from_buffer_copy(b) if len(b) else (ctypes.c_uint8 * 1)()


class Sig:
    def __init__(self, oqs, name):
        self.oqs = oqs
        self.L = oqs.lib
        self.p = self.L.OQS_SIG_new(name.encode())
        if not self.p:
            raise OQSStatusError(f"OQS_SIG_new({name}) returned NULL (algorithm not enabled)")
        s = self.p.contents
        self.name = s.method_name.decode()
        self.alg_version = s.alg_version.decode()
        self.claimed_nist_level = int(s.claimed_nist_level)
        self.ctx_support = bool(s.sig_with_ctx_support)
        self.length_public_key = int(s.length_public_key)
        self.length_secret_key = int(s.length_secret_key)
        self.length_signature = int(s.length_signature)

    def __del__(self):
        try:
            if self.p:
                self.L.OQS_SIG_free(self.p)
                self.p = None
        except Exception:
            pass

    def keypair(self):
        pk = (ctypes.c_uint8 * self.length_public_key)()
        sk = (ctypes.c_uint8 * self.length_secret_key)()
        rc = self.L.OQS_SIG_keypair(self.p, pk, sk)
        if rc != 0:
            raise OQSStatusError(f"OQS_SIG_keypair rc={rc}")
        return bytes(pk), bytes(sk)

    def keypair_from_seed(self, xi):
        """Seeded keygen through the RNG hook (xi = 32-byte FIPS 204 seed)."""
        st = self.oqs.inject_randomness([xi])
        try:
            pk, sk = self.keypair()
        finally:
            self.oqs.restore_rng()
        if st["mismatch"] or st["exhausted"] or st["calls"] != [len(xi)]:
            raise OQSStatusError(f"unexpected RNG consumption during keypair: {st}")
        return pk, sk

    def sign(self, sk, msg, ctx=None):
        sig = (ctypes.c_uint8 * self.length_signature)()
        siglen = ctypes.c_size_t(0)
        m = _buf(msg)
        if ctx is None:
            rc = self.L.OQS_SIG_sign(self.p, sig, ctypes.byref(siglen), m, len(msg), _buf(sk))
        else:
            rc = self.L.OQS_SIG_sign_with_ctx_str(self.p, sig, ctypes.byref(siglen), m, len(msg),
                                                  _buf(ctx), len(ctx), _buf(sk))
        if rc != 0:
            raise OQSStatusError(f"OQS_SIG_sign rc={rc}")
        return bytes(sig)[: siglen.value]

    def sign_with_rnd(self, sk, msg, rnd, ctx=None):
        """Hedged signing with a chosen 32-byte rnd via the RNG hook
        (rnd = 32 zero bytes gives FIPS 204 deterministic signing)."""
        st = self.oqs.inject_randomness([rnd])
        try:
            sig = self.sign(sk, msg, ctx)
        finally:
            self.oqs.restore_rng()
        if st["mismatch"] or st["exhausted"] or st["calls"] != [len(rnd)]:
            raise OQSStatusError(f"unexpected RNG consumption during sign: {st}")
        return sig

    def verify(self, pk, msg, sig, ctx=None):
        m = _buf(msg)
        if ctx is None:
            rc = self.L.OQS_SIG_verify(self.p, m, len(msg), _buf(sig), len(sig), _buf(pk))
        else:
            rc = self.L.OQS_SIG_verify_with_ctx_str(self.p, m, len(msg), _buf(sig), len(sig),
                                                    _buf(ctx), len(ctx), _buf(pk))
        return rc == 0


class Kem:
    def __init__(self, oqs, name):
        self.oqs = oqs
        self.L = oqs.lib
        self.p = self.L.OQS_KEM_new(name.encode())
        if not self.p:
            raise OQSStatusError(f"OQS_KEM_new({name}) returned NULL (algorithm not enabled)")
        k = self.p.contents
        self.name = k.method_name.decode()
        self.alg_version = k.alg_version.decode()
        self.claimed_nist_level = int(k.claimed_nist_level)
        self.length_public_key = int(k.length_public_key)
        self.length_secret_key = int(k.length_secret_key)
        self.length_ciphertext = int(k.length_ciphertext)
        self.length_shared_secret = int(k.length_shared_secret)
        self.length_keypair_seed = int(k.length_keypair_seed)
        self.length_encaps_seed = int(k.length_encaps_seed)
        self.has_keypair_derand = bool(k.keypair_derand)
        self.has_encaps_derand = bool(k.encaps_derand)

    def __del__(self):
        try:
            if self.p:
                self.L.OQS_KEM_free(self.p)
                self.p = None
        except Exception:
            pass

    def keypair(self):
        pk = (ctypes.c_uint8 * self.length_public_key)()
        sk = (ctypes.c_uint8 * self.length_secret_key)()
        rc = self.L.OQS_KEM_keypair(self.p, pk, sk)
        if rc != 0:
            raise OQSStatusError(f"OQS_KEM_keypair rc={rc}")
        return bytes(pk), bytes(sk)

    def keypair_derand(self, seed):
        if len(seed) != self.length_keypair_seed:
            raise ValueError(f"seed must be {self.length_keypair_seed} bytes")
        pk = (ctypes.c_uint8 * self.length_public_key)()
        sk = (ctypes.c_uint8 * self.length_secret_key)()
        rc = self.L.OQS_KEM_keypair_derand(self.p, pk, sk, _buf(seed))
        if rc != 0:
            raise OQSStatusError(f"OQS_KEM_keypair_derand rc={rc}")
        return bytes(pk), bytes(sk)

    def encaps(self, pk):
        ct = (ctypes.c_uint8 * self.length_ciphertext)()
        ss = (ctypes.c_uint8 * self.length_shared_secret)()
        rc = self.L.OQS_KEM_encaps(self.p, ct, ss, _buf(pk))
        if rc != 0:
            raise OQSStatusError(f"OQS_KEM_encaps rc={rc}")
        return bytes(ct), bytes(ss)

    def encaps_derand(self, pk, m):
        if len(m) != self.length_encaps_seed:
            raise ValueError(f"encaps seed must be {self.length_encaps_seed} bytes")
        ct = (ctypes.c_uint8 * self.length_ciphertext)()
        ss = (ctypes.c_uint8 * self.length_shared_secret)()
        rc = self.L.OQS_KEM_encaps_derand(self.p, ct, ss, _buf(pk), _buf(m))
        if rc != 0:
            raise OQSStatusError(f"OQS_KEM_encaps_derand rc={rc}")
        return bytes(ct), bytes(ss)

    def decaps(self, sk, ct):
        ss = (ctypes.c_uint8 * self.length_shared_secret)()
        rc = self.L.OQS_KEM_decaps(self.p, ss, _buf(ct), _buf(sk))
        if rc != 0:
            raise OQSStatusError(f"OQS_KEM_decaps rc={rc}")
        return bytes(ss)


if __name__ == "__main__":
    o = LibOQS()
    print("liboqs", o.version, o.path)
    s = o.sig("ML-DSA-87")
    print(s.name, s.alg_version, "ctx", s.ctx_support, s.length_public_key, s.length_secret_key, s.length_signature)
    pk, sk = s.keypair()
    sig = s.sign(sk, b"hello", b"ctx")
    print("sign/verify ctx:", s.verify(pk, b"hello", sig, b"ctx"), "wrong ctx:", s.verify(pk, b"hello", sig, b"xtc"))
    k = o.kem("ML-KEM-1024")
    print(k.name, k.alg_version, k.length_public_key, k.length_secret_key, k.length_ciphertext,
          k.length_shared_secret, "seeds", k.length_keypair_seed, k.length_encaps_seed,
          "derand", k.has_keypair_derand, k.has_encaps_derand)
    ek, dk = k.keypair()
    ct, ss = k.encaps(ek)
    print("kem roundtrip:", ss == k.decaps(dk, ct))
