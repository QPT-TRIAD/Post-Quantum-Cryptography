#!/usr/bin/env python3
"""Seed corpus for fuzz_verify: the genuine certificate plus structured variants.

usage: gen_corpus.py genuine.bin corpus_dir B TAU
cert = m(64) || handles(43*32) || proof;  proof layout (verify() order):
  h_com(64) | corrections((tau-1)*1912) | d(1912) | u~(32) | v~(32) | A(6*32) | ctr(4) | openings(tau*(b*32+64))
"""
import os, sys, hashlib

src, out, B, TAU = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
g = open(src, "rb").read()
EHB, QUORUM, DEG = 1912, 43, 6
PRE = 64 + QUORUM * 32
o_hcom = PRE
o_corr = o_hcom + 64
o_d = o_corr + (TAU - 1) * EHB
o_ut = o_d + EHB
o_hv = o_ut + 32
o_A = o_hv + 32
o_ctr = o_A + DEG * 32
o_open = o_ctr + 4
open_len = B * 32 + 64
assert o_open + TAU * open_len == len(g), (o_open + TAU * open_len, len(g))
os.makedirs(out, exist_ok=True)

def det(n, tag):  # deterministic filler bytes
    b = b""
    while len(b) < n:
        b += hashlib.sha256(tag.encode() + len(b).to_bytes(4, "big")).digest()
    return b[:n]

def flip(off, bit=0):
    x = bytearray(g); x[off] ^= (1 << bit); return bytes(x)

def swap(a, b, n):
    x = bytearray(g); x[a:a+n], x[b:b+n] = g[b:b+n], g[a:a+n]; return bytes(x)

seeds = {
    "genuine": g,
    "empty": b"",
    "one_byte": b"\x00",
    "prefix_only_m_handles": g[:PRE],
    "trunc_half": g[: len(g) // 2],
    "trunc_minus1": g[:-1],
    "trunc_proof_minus_last_opening": g[: len(g) - open_len],
    "dup_cert_twice": g + g,
    "oversized_plus1": g + b"\x00",
    "oversized_plus1000": g + det(1000, "pad"),
    "proof_duplicated_hcom_prepended": g[:PRE] + g[o_hcom:o_hcom+64] + g[PRE:],
    "reorder_handles_swap_0_1": swap(64, 64 + 32, 32),
    "reorder_handles_reversed": g[:64] + b"".join(g[64 + 32*k: 64 + 32*(k+1)] for k in reversed(range(QUORUM))) + g[PRE:],
    "handles_all_equal": g[:64] + g[64:96] * QUORUM + g[PRE:],
    "reorder_corrections_swap_0_1": swap(o_corr, o_corr + EHB, EHB) if TAU >= 3 else g,
    "reorder_openings_swap_0_1": swap(o_open, o_open + open_len, open_len) if TAU >= 2 else g,
    "reorder_opening0_siblings_swap": swap(o_open, o_open + 32, 32),
    "flip_m_byte0": flip(0),
    "flip_m_byte63": flip(63, 7),
    "flip_handle0_lsb": flip(64 + 31),
    "flip_handle42_msb": flip(64 + 42*32, 7),
    "flip_hcom": flip(o_hcom),
    "flip_corr0": flip(o_corr) if TAU >= 2 else g,
    "flip_d_first": flip(o_d),
    "flip_d_last": flip(o_ut - 1, 7),
    "flip_ut": flip(o_ut),
    "flip_hv": flip(o_hv + 31),
    "flip_A0": flip(o_A),
    "flip_A5": flip(o_A + 5*32 + 31),
    "flip_ctr_lsb": flip(o_ctr + 3),
    "flip_ctr_msb": flip(o_ctr, 7),
    "ctr_plus_one": g[:o_ctr] + (int.from_bytes(g[o_ctr:o_ctr+4], "big") + 1).to_bytes(4, "big") + g[o_open:],
    "ctr_zero": g[:o_ctr] + b"\0\0\0\0" + g[o_open:],
    "flip_opening0_sib0": flip(o_open),
    "flip_opening0_com": flip(o_open + B*32),
    "flip_last_byte": flip(len(g) - 1),
    "proof_all_zero": g[:PRE] + b"\0" * (len(g) - PRE),
    "proof_all_ff": g[:PRE] + b"\xff" * (len(g) - PRE),
    "all_zero_same_len": b"\0" * len(g),
    "random_same_len": det(len(g), "rnd"),
    "m_and_handles_zero_proof_genuine": b"\0" * PRE + g[PRE:],
    "ut_hv_zero": g[:o_ut] + b"\0" * 64 + g[o_A:],
    "A_zero": g[:o_A] + b"\0" * (DEG*32) + g[o_ctr:],
}
n = 0
for name, data in seeds.items():
    open(os.path.join(out, name), "wb").write(data); n += 1
print(f"wrote {n} seeds to {out}; genuine len {len(g)}; proof offsets: hcom={o_hcom} corr={o_corr} d={o_d} ut={o_ut} hv={o_hv} A={o_A} ctr={o_ctr} openings={o_open}")
