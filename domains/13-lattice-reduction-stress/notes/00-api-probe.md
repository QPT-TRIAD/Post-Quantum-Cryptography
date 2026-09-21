# Milestone 0 — the API probe, and the toolchain relocation

**Gate passed:** 19 checks, 0 required failures, 0 optional absences.

## Why this milestone exists

Three C++-backed libraries with thin Python surfaces, at versions pinned by what happens to be
built rather than by a resolver. The sibling Grover project's probe found five behaviours that
contradicted the documentation, three of which would have failed silently. The same discipline
applies with more force here: the failure mode of a wrong lattice is that it reduces *perfectly*.

## What the probe caught before anything was built on it

**`LWEParameters` is not exported from `estimator`.** The package's `__all__` is
`['ND','Logging','RC','Simulator','LWE','NTRU','SIS','schemes']`. It lives in
`estimator.lwe_parameters`. An import written from the documentation would have failed at the first
call rather than at import, which is the worse of the two.

**A misattributed figure — mine, not the tool's.** The first probe asserted Kyber512 `usvp` β = 387
and failed at 406. The 387 belongs to `dual_hybrid`; the real values are:

| attack | β | log₂(rop) |
|---|---:|---:|
| `usvp` | **406** | 143.8 |
| `dual` | 424 | 149.9 |
| `dual_hybrid` | **387** | 139.7 |

I had read the `dual_hybrid` block out of an earlier interactive run and attributed it to `usvp`.
That error would have put the *wrong attack family's* number into the theoretical half of the
project's central comparison, and nothing downstream could have detected it. This is the single
strongest argument for building the probe before the pipeline.

**The probe now pins a revision, not a remembered constant.** The estimator is at
`53da5982597709ba0fdf94ea37a84d822310fd84` (2026-08-19), defaulting to the MATZOV cost model and the
GSA shape model. The check records the revision and the models alongside the measured betas, and
distinguishes "the revision differs from the baseline" from "the same revision, so a dependency
moved underneath" when the numbers shift. Asserting a literature figure as equality would either
fail on a legitimate model change or — worse — match by coincidence and hide one.

**Dilithium is a SIS instance, not an LWE one.** The plan's verification step pairs "Kyber512 and a
Dilithium set"; the estimator ships `Dilithium*_MSIS_*`, which go through `SIS.estimate`. The probe
now exercises that path so the published-reference comparison is built against both estimators
rather than two LWE calls.

**`normalize()` moves the small distribution onto the secret.** Measured: a uniform `Xs` at
σ = 18918.6 and a rounding `Xe` at σ = 73.90 come back as `Xs` σ = 73.90, `Xe` σ = 18918.6. That
swap is the whole reason a Kannan embedding contains a short vector at all — a uniform secret has no
short representative, so an embedding built on it directly would contain nothing to find. The probe
asserts the *swap*, not merely that `normalize` exists, because the existence of the method is not
the property the attack depends on. The 73.90 is exactly `sqrt((256² − 1)/12)`, the standard
deviation of the uniform distribution on `[−128, 127]` — the QLWR rounding error, derived and not
fitted.

## The exactness budget, measured

`int64` holds the production inner product with **8.39×10⁶ times headroom** (`ν·q² = 1.1×10¹²`
against `int64` max). Arbitrary-precision Python ints remain the fallback path. Nothing in the
construction needs to reach for floats, which matters because a float in basis construction
produces a basis for a different lattice without any error being raised.

## The relocation, and why a `.pth` rather than an editable install

The two checkouts were built inside the read-only research tree and imported only from there, so
the project could not depend on them where they sat. They now live in
`the lattice-tools directory`, byte-identical (347 + 91 files, extension modules included), with the
originals removed.

**The binaries are location-independent; the build system is not.** `readelf -d` shows no
RPATH/RUNPATH on `siever.so`, `siever_params.so` or `libg6k.so` — they link only
`libstdc++/libm/libc/libgcc`, and the kernel is compiled *into* the extension rather than linked as
`libg6k.so`. The only absolute-path strings are Cython `__pyx_f[]` traceback filenames. But
`Makefile` bakes the original path for `ACLOCAL`/`AUTOCONF` and `config.status` records `ac_pwd`,
and an editable install's `build_ext` runs `make` unconditionally — so `pip install -e` would likely
fail on a stale aux-script path. A path entry suffices and touches nothing.

**One real ordering requirement:** G6K's extensions resolve `cysignals` symbols through the loaded
Python global symbol table, so `import cysignals.signals` must precede `import g6k`. The probe
asserts the order.

**A mistake worth recording.** The first install wrote the `.pth` into
`~/.local/lib/python3.12/site-packages` — the user-site directory — because the helper took the
first `site-packages` on `sys.path`. That would have put G6K on the path of *every* Python 3.12 on
the box, including the system interpreter and an unrelated project's venv. It now resolves through
`sysconfig` and refuses to write anywhere but the sage environment.

## What this milestone changes downstream

- The estimator's pinned baseline is a **golden per revision**, so the theoretical half of the
  comparison is anchored to something that can be re-baselined deliberately.
- The published-reference instances must use **both** `LWE.estimate` and `SIS.estimate`.
- The attack's normal form is not optional, and the probe's assertion of the σ-swap is the evidence.
