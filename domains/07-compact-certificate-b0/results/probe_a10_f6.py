"""Build-time probes for this domain. Run with the repository copy of the reference module:

    python3 results/probe_a10_f6.py [path/to/sidecar_free_certificate.py]

Two probes, both read-only:

1.  Finding A.10 -- the two B0 tests that mutate the frame at CEQS29 body offsets while their
    names claim CQ44 header checks. Each mutation is replayed twice: at the offset the test
    actually writes, and at the offset its name implies. The rejection each one produces is
    printed, which shows that the two named checks are never exercised.

2.  Finding F6 -- the encode-side size bound. `encode_b0` with a provider wider than the gate
    emits an oversize frame without raising, while `verify_b0` rejects that same frame. The wire
    specification makes the encode-side refusal normative; the reference does not implement it.
"""
import importlib.util
import pathlib
import struct
import sys

DEFAULT = pathlib.Path(__file__).resolve().parent.parent / 'src' / 'sidecar_free_certificate.py'
SRC = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT)

sys.dont_write_bytecode = True          # never leave a __pycache__ next to the probed file
spec = importlib.util.spec_from_file_location('sidecar_probe', SRC)
mod = importlib.util.module_from_spec(spec)
sys.modules['sidecar_probe'] = mod          # the module looks itself up in sys.modules
spec.loader.exec_module(mod)

provider = mod.SymbolicSignatures(width=128)
registry, sks = mod._b0_registry(provider)
cfg = mod.cfg_b0(registry)
m0, m1 = mod._msg(0), mod._msg((1 << 400) | 7)
seats0 = list(range(mod.QUORUM))
frame0 = mod.encode_b0(registry, provider, mod._DOMAIN, m0, sks, seats0)

# Name the probed file without printing any absolute path.
probed = pathlib.Path(SRC).resolve()
label = probed.name
for parent in probed.parents:
    if parent.name == 'domains' and (parent / '07-compact-certificate-b0').is_dir():
        label = str(probed.relative_to(parent.parent))
        break
print('module under probe:', label)
print('header struct offsets: magic 0-3, version 4-5, suite 6-7, cfg 8-71, domain 72-135, '
      'message 136-199, count 200-201, width 202-203, payload_len 204-207; calcsize',
      mod.HEADER_BYTES)

print()
print('--- 1. the two mutations of A.10, replayed ---------------------------------------')

t = bytearray(frame0)
t[144:208] = m1                                     # what test_wrong_message_rejected writes
try:
    mod.verify_b0(bytes(t), registry, provider, cfg)
    print('misaligned message mutation (writes 144:208): ACCEPTED (unexpected)')
except mod.CertError as exc:
    print('misaligned message mutation (writes 144:208): %s: %s' % (type(exc).__name__, exc))
t = bytearray(frame0)
t[136:200] = m1                                     # the header message field 136-199
try:
    mod.verify_b0(bytes(t), registry, provider, cfg)
    print('aligned message mutation     (writes 136:200): ACCEPTED (unexpected)')
except mod.CertError as exc:
    print('aligned message mutation     (writes 136:200): %s: %s' % (type(exc).__name__, exc))

t = bytearray(frame0)
struct.pack_into('>H', t, 206, provider.width + 1)  # what test_width_mismatch_rejected writes
try:
    mod.verify_b0(bytes(t), registry, provider, cfg)
    print('misaligned width mutation     (packs u16 at 206): ACCEPTED (unexpected)')
except mod.CertError as exc:
    print('misaligned width mutation     (packs u16 at 206): %s: %s' % (type(exc).__name__, exc))
t = bytearray(frame0)
struct.pack_into('>H', t, 202, provider.width + 1)  # the header width field 202-203
try:
    mod.verify_b0(bytes(t), registry, provider, cfg)
    print('aligned width mutation        (packs u16 at 202): ACCEPTED (unexpected)')
except mod.CertError as exc:
    print('aligned width mutation        (packs u16 at 202): %s: %s' % (type(exc).__name__, exc))

print()
print('--- 2. the encode-side size bound (finding F6) ------------------------------------')

wide = mod.SymbolicSignatures(width=758)
wide_registry, wide_sks = mod._b0_registry(wide)
wide_cfg = mod.cfg_b0(wide_registry)
frame = mod.encode_b0(wide_registry, wide, mod._DOMAIN, m0, wide_sks, seats0)
print('encode_b0 width=758: emitted %d bytes (gate is %d); b0_fits(758)=%s'
      % (len(frame), mod.MAX_FRAME_BYTES, mod.b0_fits(758)))
try:
    mod.verify_b0(frame, wide_registry, wide, wide_cfg)
    print('verify_b0 of the oversize frame: ACCEPTED (unexpected)')
except mod.CertError as exc:
    print('verify_b0 of the oversize frame: %s: %s' % (type(exc).__name__, exc))
