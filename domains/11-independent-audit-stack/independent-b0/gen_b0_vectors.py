#!/usr/bin/env python3
"""Generate B0 cross-validation vectors with the REFERENCE implementation (v1.44) and the
toy provider of B0_wire_spec_v1.44.md §5. The independent implementer never sees this
file or the reference; it sees only the spec and the vectors."""
import hashlib
import importlib.util
import json
import os
import random
import sys

# Reference source tree: the read-only inputs this layer audits. The verification
# environment exports PQT_SRC; see docs/inputs-and-provenance.md.
PQT = os.environ.get('PQT_SRC')
if not PQT or not os.path.isdir(PQT):
    raise SystemExit('PQT_SRC is not set: source the environment activation script '
                     '(tooling/), or point PQT_SRC at a local copy of the research tree')
spec = importlib.util.spec_from_file_location('sidecar44_vec', f'{PQT}/sidecar_free_certificate_v1.44.py')
b0 = importlib.util.module_from_spec(spec)
sys.modules['sidecar44_vec'] = b0          # v1.44 looks itself up in sys.modules during import
spec.loader.exec_module(b0)


class ToyShake:
    name, category, width = 'toy-shake-32', 0, 32

    def keygen_for(self, i):
        return b'PK' + i.to_bytes(2, 'big'), b'SK' + i.to_bytes(2, 'big')

    def sign(self, sk, msg):
        return hashlib.shake_256(b'TOYSIG' + sk + msg).digest(32)

    def verify(self, pk, msg, sig):
        return type(sig) is bytes and len(sig) == 32 and sig == self.sign(b'SK' + pk[2:], msg)


def main():
    rng = random.Random(4444)
    prov = ToyShake()
    keys = [prov.keygen_for(i) for i in range(64)]
    registry = b0.RegistryB0(tuple(pk for pk, _ in keys), b'toy-shake-32')
    sks = [sk for _, sk in keys]
    cfg = b0.cfg_b0(registry)
    cases = []
    for k in range(400):
        domain = hashlib.shake_256(b'dom%d' % (k % 7)).digest(64)
        m0 = hashlib.shake_256(b'm0-%d' % k).digest(64)
        m1 = hashlib.shake_256(b'm1-%d' % k).digest(64)
        perm = list(range(64)); rng.shuffle(perm)
        overlap = rng.choice([22, 22, 23, 30, 43, 25])
        s0 = sorted(perm[:43]); s1 = sorted(perm[:overlap] + perm[43:43 + 43 - overlap])
        f0 = b0.encode_b0(registry, prov, domain, m0, sks, s0)
        f1 = b0.encode_b0(registry, prov, domain, m1, sks, s1)
        ext = [(bl.seat, bl.position0, bl.position1) for bl in b0.extract_b0(f0, f1, registry, prov, cfg)]
        blames = {str(s): b0.verify_blame_b0(f0, f1, registry, prov, cfg, s) for s in rng.sample(range(64), 8)}
        case = {'id': k, 'domain': domain.hex(), 'message0': m0.hex(), 'message1': m1.hex(), 'seats0': s0, 'seats1': s1,
                'frame0': f0.hex(), 'frame1': f1.hex(), 'extract': ext, 'blame': blames, 'kind': 'conflict'}
        cases.append(case)
        # adversarial variants
        if k % 4 == 0:
            same = b0.encode_b0(registry, prov, domain, m0, sks, s1)
            cases.append({'id': f'{k}-same-message', 'domain': domain.hex(), 'frame0': f0.hex(), 'frame1': same.hex(),
                          'kind': 'same-message', 'expected_extract': 'reject'})
        if k % 4 == 1:
            b = bytearray(f1); pos = rng.randrange(len(b)); b[pos] ^= 1 << rng.randrange(8)
            cases.append({'id': f'{k}-mutated', 'frame': bytes(b).hex(), 'kind': 'mutated', 'expected_verify': False})
        if k % 4 == 2:
            other = hashlib.shake_256(b'other-domain').digest(64)
            fo = b0.encode_b0(registry, prov, other, m1, sks, s1)
            cases.append({'id': f'{k}-other-domain', 'frame0': f0.hex(), 'frame1': fo.hex(), 'kind': 'other-domain', 'expected_extract': 'reject'})
        if k % 4 == 3:
            cases.append({'id': f'{k}-truncated', 'frame': f0[:-1].hex(), 'kind': 'truncated', 'expected_verify': False})
            cases.append({'id': f'{k}-trailing', 'frame': (f0 + b'\x00').hex(), 'kind': 'trailing', 'expected_verify': False})
    out = {'spec': 'B0_wire_spec_v1.44.md', 'registry': {'public_keys': [pk.hex() for pk, _ in keys], 'scheme_id': 'toy-shake-32'},
           'cfg': cfg.hex(), 'cases': cases}
    json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else 'b0_vectors.json', 'w'))
    print('cases', len(cases))


if __name__ == '__main__':
    main()
