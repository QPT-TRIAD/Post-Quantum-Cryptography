#!/usr/bin/env python3
"""Synthetic participant simulation with real crypto; no MPC or succinct proof.

Only public audit data and aggregate results are saved. New private keys/trace
seeds stay in process memory; Python does not promise secure erasure.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import secrets
import time
import authorization as a


def run(out):
    t0 = time.perf_counter()
    checks = {}
    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)
    def rejected(name, fn):
        try:
            fn()
        except (ValueError, IndexError, TypeError):
            check(name, True)
        except Exception as exc:
            from cryptography.exceptions import InvalidTag
            if isinstance(exc, InvalidTag):
                check(name, True)
            else:
                raise
        else:
            check(name, False)

    seeds, sigkeys, kemkeys, registry = [], [], [], []
    for i in range(a.N):
        seeds.append(secrets.token_bytes(48))
        pk, sk = a.dsa.generate_keypair()
        ek, dk = a.kem.generate_keypair()
        registry.append(dict(trace=a.trace_key(seeds[i]), vote=pk, kem=ek))
        sigkeys.append(sk)
        kemkeys.append(dk)
    check('standard_parameter_widths', (len(registry[0]['vote']), len(sigkeys[0]),
          len(registry[0]['kem']), len(kemkeys[0]), a.dsa.SIGNATURE_SIZE,
          a.kem.CIPHERTEXT_SIZE) == (2592,4896,1568,3168,4627,1568))
    domain = a.H(b'CEQS29/synthetic/epoch-height-view')
    messages = [bytes(64), ((1 << 511) + 17).to_bytes(64,'big')]
    seatsets = [list(range(43)), list(range(22)) + list(range(43,64))]
    cases, privwitness, bodies, all_wires, sessions = [], [], [], [], []
    recipient = 63
    crypto_start = time.perf_counter()
    for case, seats in enumerate(seatsets):
        body, order = a.make_body(registry,domain,messages[case],seats,seeds)
        handles = a.parse_body(body)[3]
        approvals = [(i,a.dsa.sign(sigkeys[i],a.approval_message(body,i,h)))
                     for i,h in zip(order,handles)]
        witness = [(i,seeds[i],sig) for i,sig in approvals]
        check(f'case{case}_exact_43_approval_signatures',a.check_public_approvals(registry,body,approvals))
        check(f'case{case}_full_reference_relation',a.check_witness(registry,body,witness))
        session = secrets.token_bytes(32)
        wires = [a.seal(registry,body,i,recipient,session,sig,sigkeys[i]) for i,sig in approvals]
        seen = set()
        received = [a.receive(registry,body,recipient,session,kemkeys[recipient],w,seen) for w in wires]
        check(f'case{case}_43_encrypted_approvals_received',received == approvals and len(seen)==43)
        check(f'case{case}_42_is_not_quorum',not a.check_public_approvals(registry,body,received[:-1]))
        cases.append({'body_hex':body.hex(), 'approvals':[{'seat':i,'signature_hex':s.hex()} for i,s in approvals]})
        privwitness.append(witness); bodies.append(body); all_wires.append(wires); sessions.append(session)
    crypto_seconds = time.perf_counter()-crypto_start
    check('conflict_algebra_recovers_22_actual_test_signers',a.extract_algebra(*bodies)==list(range(22)))

    body, witness, wire, session = bodies[0],privwitness[0],all_wires[0][0],sessions[0]
    sender = witness[0][0]
    def receive(w=wire, b=body, r=recipient, sid=session, dk=None, seen=None):
        return a.receive(registry,b,r,sid,kemkeys[r] if dk is None else dk,w,set() if seen is None else seen)
    seen=set(); receive(seen=seen)
    rejected('replayed_envelope_rejected',lambda:receive(seen=seen))
    rejected('fresh_encryption_same_origin_not_extra_vote',lambda:receive(
        a.seal(registry,body,sender,recipient,session,witness[0][2],sigkeys[sender]),seen=seen))
    rejected('wrong_recipient_rejected',lambda:receive(r=62))
    rejected('wrong_recipient_secret_rejected',lambda:receive(dk=kemkeys[62]))
    rejected('wrong_session_rejected',lambda:receive(sid=secrets.token_bytes(32)))
    rejected('cross_message_replay_rejected',lambda:receive(b=bodies[1]))
    rejected('truncated_wire_rejected',lambda:receive(wire[:-1]))
    rejected('trailing_wire_rejected',lambda:receive(wire+b'x'))
    for name, position in [('header',0),('sender',8),('kem_ciphertext',a.TRANSPORT_HEADER),
                           ('nonce',a.TRANSPORT_HEADER+a.kem.CIPHERTEXT_SIZE),
                           ('aead_ciphertext',a.TRANSPORT_HEADER+a.kem.CIPHERTEXT_SIZE+12),
                           ('outer_signature',len(wire)-1)]:
        bad=bytearray(wire); bad[position]^=1
        rejected(f'changed_{name}_rejected',lambda bad=bytes(bad):receive(bad))
    # A valid transport signature must not hide a broken KEM/AEAD path.
    unsigned=bytearray(wire[:-a.dsa.SIGNATURE_SIZE]); unsigned[a.TRANSPORT_HEADER]^=1
    bad=bytes(unsigned)+a.dsa.sign(sigkeys[sender],b'CEQS29/TRANSPORT/v1'+bytes(unsigned))
    rejected('reauthenticated_bad_kem_ciphertext_fails_aead',lambda:receive(bad))
    invalid_approval=bytes(a.dsa.SIGNATURE_SIZE)
    bad=a.seal(registry,body,sender,recipient,session,invalid_approval,sigkeys[sender])
    rejected('authenticated_encryption_of_invalid_approval_rejected',lambda:receive(bad))
    bad=a.seal(registry,body,sender,recipient,session,witness[0][2],sigkeys[(sender+1)%64])
    rejected('wrong_sender_transport_key_rejected',lambda:receive(bad))
    after_invalid=set()
    rejected('invalid_envelope_does_not_reserve_origin',lambda:receive(bad,seen=after_invalid))
    check('valid_envelope_accepted_after_invalid_one',receive(seen=after_invalid)==(sender,witness[0][2]))

    broken=list(witness); broken[0]=(sender,seeds[sender],invalid_approval)
    check('trace_seed_possession_without_approval_rejected',not a.check_witness(registry,body,broken))
    broken=list(witness); broken[0]=(sender,secrets.token_bytes(48),witness[0][2])
    check('approval_without_registered_trace_opening_rejected',not a.check_witness(registry,body,broken))
    broken=list(witness); broken[1]=broken[0]
    check('duplicate_seat_cannot_count_twice',not a.check_witness(registry,body,broken))
    broken=list(witness); broken[0]=((sender+1)%64,witness[0][1],witness[0][2])
    check('relabelled_authorizer_rejected',not a.check_witness(registry,body,broken))
    broken=list(witness); broken[0]=(sender,witness[0][1],
        a.dsa.sign(sigkeys[(sender+1)%64],a.approval_message(body,sender,a.parse_body(body)[3][0])))
    check('different_seat_key_cannot_authorize_handle',not a.check_witness(registry,body,broken))
    for name,position in [('configuration',16),('domain',80),('message',144),('link',208),('mask',272)]:
        changed=bytearray(body);changed[position]^=1
        check(f'approval_reuse_after_{name}_change_rejected',not a.check_witness(registry,bytes(changed),witness))
    check('cross_message_witness_reuse_rejected',not a.check_witness(registry,bodies[1],witness))
    check('extra_body_byte_rejected',not a.check_witness(registry,body+b'x',witness))
    changed=bytearray(body);changed[0]^=1
    check('cross_suite_body_rejected',not a.check_witness(registry,bytes(changed),witness))
    for column in ('trace','vote','kem'):
        bad_registry=copy.deepcopy(registry);bad_registry[1][column]=bad_registry[0][column]
        rejected(f'duplicate_registered_{column}_key_rejected',lambda reg=bad_registry:a.config_id(reg))
    rejected('same_message_is_not_a_conflict',lambda:a.extract_algebra(body,body))
    other=bytearray(bodies[1]);other[80]^=1
    rejected('different_domain_is_not_same_conflict',lambda:a.extract_algebra(body,bytes(other)))

    # Intentional false statement authorized by its actual synthetic signers.
    # This isolates the missing predicate in "signatures + handles" wrappers.
    bad_body=bytearray(body);bad_body[272]^=1;bad_body=bytes(bad_body)
    bad_hs=a.parse_body(bad_body)[3]
    bad_approvals=[(i,a.dsa.sign(sigkeys[i],a.approval_message(bad_body,i,h)))
                   for (i,_,_),h in zip(witness,bad_hs)]
    bad_witness=[(i,seeds[i],sig) for i,sig in bad_approvals]
    check('valid_signatures_can_approve_false_trace_equation',a.check_public_approvals(registry,bad_body,bad_approvals))
    check('full_relation_rejects_that_false_trace_equation',not a.check_witness(registry,bad_body,bad_witness))
    # Standard KEM is public-key encapsulation, not proof of sender identity.
    ct,shared=a.kem.encrypt(registry[recipient]['kem'])
    check('kem_alone_needs_no_sender_signing_key',a.kem.decrypt(kemkeys[recipient],ct)==shared)
    check('shared_kem_secret_expands_same_private_tape',
          hashlib.shake_256(b'CEQS29/tape'+shared).digest(1<<20)==
          hashlib.shake_256(b'CEQS29/tape'+a.kem.decrypt(kemkeys[recipient],ct)).digest(1<<20))
    # No final QC entry is provided: this experiment supplies no succinct proof.
    result={
      'scope':'Real-primitive authorization/transport and ordinary witness checking; NOT a QC or MPC proof',
      'suite':a.SUITE.decode(), 'participants':64,'approvals_per_case':43,
      'withholding_scope':'21 absent submission ports; no Byzantine network or robust MPC is simulated',
      'cases':2,'actual_approval_signatures':86,'encrypted_approvals_received':86,
      'actual_conflict_intersection':list(range(22)),
      'complete_body_bytes':a.BODY_BYTES,'proof_position_remaining_bytes':32768-a.BODY_BYTES,
      'transport_envelope_bytes':a.WIRE_BYTES,'transport_envelopes_are_not_final_QC_bytes':True,
      'transport_recipient_learns_signers':True,'private_witnesses_centralized_in_test_harness':True,
      'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),
      'measured_crypto_seconds':crypto_seconds,'measured_total_seconds':time.perf_counter()-t0,
      'blockers':{'complete_32KiB_certificate':'OPEN','QPT128_composition':'OPEN',
        'distributed_private_robust_proving':'OPEN','MLDSA_verification_inside_succinct_proof':'OPEN'},
      'accepted_complete_original_goal_QCs':0,
      'runtime':{'python':__import__('sys').version,'pqcrypto':'0.3.4',
        'cryptography':__import__('cryptography').__version__}
    }
    out.mkdir(parents=True,exist_ok=True)
    public={'warning':'TRANSPARENT SYNTHETIC APPROVAL AUDIT: discloses seats; not a quorum proof',
            'registry':[{k:v.hex() for k,v in row.items()} for row in registry],
            'cases':cases}
    (out/'public_approval_audit.json').write_text(json.dumps(public,indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'results'/'replay-evidence')
    run(parser.parse_args().out)
