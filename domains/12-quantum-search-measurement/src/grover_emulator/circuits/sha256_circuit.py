"""SHA-256 as a reversible circuit of X, CNOT and Toffoli — built, verified, and then counted.

**Why this exists.** Every hash-based ledger in the audit corpus this project's questions come from
charges a quantum adversary ``2^18`` gates per hash-oracle query and cites a published T-count for
it. No circuit is built anywhere in that corpus, and the oracles this emulator runs Grover against
are lowered from truth tables: the hash is evaluated classically and its answers are wired in, so
their gate counts say nothing about a hash. This module is the missing object — the one-block
SHA-256 compression as an actual gate list, checked bit for bit against :mod:`hashlib`, so that
"gates per query" is a number read off a circuit rather than a number assumed.

**What is built.** FIPS 180-4 SHA-256 for a single 512-bit block from the standard initial value,
which is every message of at most 55 bytes — including the LM-OTS chain step the corpus's firmware
ledger prices, whose input ``I || q || i || j || x`` is 16 + 4 + 2 + 1 + 32 = 55 bytes *by design*.
The construction is the in-place one (Parent, Roetteler and Svore; Amy et al.): a round never
copies the state, it adds into ``h`` and ``d`` and then relabels the registers::

    h += Ch(e,f,g);  h += S1(e);  h += K_t;  h += W_t        # h is now T1
    d += h                                                   # d is now the new e
    h += Maj(a,b,c); h += S0(a)                              # h is now the new a
    (a,b,c,d,e,f,g,h) <- (h,a,b,c,d,e,f,g)                   # a relabelling: no gates

``Ch``, ``Maj`` and the linear ``S``/``s`` functions are computed into one shared 32-qubit scratch
register, added, and uncomputed, so the scratch is clean between uses. The message schedule runs in
place on a 16-word window (``W_t`` overwrites ``W_{t-16}``), which is why the circuit is 801 qubits
where a schedule that kept all 64 words would need 2,048 more.

**The adder is the cost.** Additions mod ``2^32`` are Cuccaro-Draper-Kutin-Moulton ripple-carry
adders: in place, one clean ancilla, ``2(n-1)`` Toffolis. Seven per round and three per schedule
step account for some four fifths of the Toffolis; ``Ch`` and ``Maj`` are the rest.

**What the count is and is not.** It is exact for *this* construction, which is a straightforward
one. It is an upper bound on what SHA-256 costs, not a lower bound: Amy et al. (SAC 2016, Table 1)
report 401,584 T before and 228,992 T after T-par optimisation at 2,402 qubits, trading width for
T-count. The gate list here is the input such an optimiser would take. Converting Toffolis to T
gates uses the IR's named assumption (seven T per Toffoli); nothing here is a fault-tolerant cost.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from .ir import GateList, GateName

__all__ = [
    "IV",
    "K",
    "Sha256Layout",
    "ripple_carry_add",
    "build_sha256_compression",
    "build_sha256_preimage_predicate",
    "pad_single_block",
    "PUBLISHED_AMY_2016",
]

WORD = 32

IV = (
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
)
"""FIPS 180-4 section 5.3.3: the first 32 bits of the fractional parts of the square roots of the
first eight primes."""

K = (
    0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
    0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3, 0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
    0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
    0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
    0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13, 0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
    0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
    0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
    0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208, 0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
)
"""FIPS 180-4 section 4.2.2: the first 32 bits of the fractional parts of the cube roots of the
first sixty-four primes. The tests recompute both tables from the primes rather than trust this
transcription."""

PUBLISHED_AMY_2016 = {
    "source": "Amy, Di Matteo, Gheorghiu, Mosca, Parent, Schanck: Estimating the cost of generic "
              "quantum pre-image attacks on SHA-2 and SHA-3, SAC 2016 (arXiv:1603.09383)",
    "sha256_t_count_unoptimised": 401_584,      # Table 1, row "SHA-256"
    "sha256_t_count_optimised": 228_992,        # Table 1, row "SHA-256 (Opt.)"
    "sha256_qubits": 2_402,                     # Table 1 caption
    "sha256_oracle_t_count": 466_092,           # eq. (9): 2 * 228992 + 8108
    "sha3_256_t_count_optimised": 499_200,      # Table 2, row "SHA3-256 (Opt.)"
}
"""Reference values, read from the paper's tables and recorded as published — not derived here."""


# -- linear word functions -----------------------------------------------------------------------
# Each is an XOR of rotations and shifts, so each output bit is an XOR of at most three input bits:
# a CNOT per term, no Toffolis. ``rotr(x, r)`` bit i is x bit (i + r) mod 32; ``shr(x, r)`` bit i is
# x bit (i + r) when that is below 32, and nothing otherwise.

_BIG_SIGMA_0 = (("rotr", 2), ("rotr", 13), ("rotr", 22))
_BIG_SIGMA_1 = (("rotr", 6), ("rotr", 11), ("rotr", 25))
_SMALL_SIGMA_0 = (("rotr", 7), ("rotr", 18), ("shr", 3))
_SMALL_SIGMA_1 = (("rotr", 17), ("rotr", 19), ("shr", 10))


def _xor_linear(gl: GateList, source: list[int], scratch: list[int], terms) -> None:
    """``scratch ^= L(source)`` for a rotate/shift XOR ``L``. Self-inverse, so it also uncomputes."""
    for kind, r in terms:
        for i in range(WORD):
            j = i + r
            if kind == "rotr":
                gl.append(GateName.CX, source[j % WORD], scratch[i])
            elif j < WORD:
                gl.append(GateName.CX, source[j], scratch[i])


# -- the adder ------------------------------------------------------------------------------------


def ripple_carry_add(gl: GateList, a: list[int], b: list[int], ancilla: int) -> None:
    """``b <- (a + b) mod 2^n`` in place; ``a`` and the ancilla are returned unchanged.

    The Cuccaro-Draper-Kutin-Moulton adder without its carry-out. ``MAJ`` ripples the carry up
    through the ``a`` register, the top bit is finished with two CNOTs, and ``UMA`` ripples back
    down restoring ``a`` and leaving the sum in ``b``::

        MAJ(c, b, a):  CX a,b   CX a,c   CCX c,b,a        # a now holds the carry out of this bit
        UMA(c, b, a):  CCX c,b,a   CX a,c   CX c,b        # a restored, b holds the sum bit

    ``2(n - 1)`` Toffolis and ``4(n - 1) + 2`` CNOTs. The ancilla must arrive clean and leaves
    clean, which the tests check rather than assume. Dropping the carry-out is what makes it
    addition mod ``2^n``, which is the only addition SHA-256 performs.
    """
    n = len(a)
    if len(b) != n or n < 1:
        raise ValueError(f"registers of {len(a)} and {len(b)} qubits cannot be added")
    if len({*a, *b, ancilla}) != 2 * n + 1:
        raise ValueError("the adder's registers and its ancilla must be disjoint")
    if n == 1:
        gl.append(GateName.CX, a[0], b[0])
        return
    carry = [ancilla] + a[:-1]          # carry[i] is the wire holding the carry *into* bit i
    for i in range(n - 1):
        gl.append(GateName.CX, a[i], b[i])
        gl.append(GateName.CX, a[i], carry[i])
        gl.append(GateName.CCX, carry[i], b[i], a[i])
    gl.append(GateName.CX, a[n - 2], b[n - 1])      # a[n-2] holds the carry into the top bit
    gl.append(GateName.CX, a[n - 1], b[n - 1])
    for i in reversed(range(n - 1)):
        gl.append(GateName.CCX, carry[i], b[i], a[i])
        gl.append(GateName.CX, a[i], carry[i])
        gl.append(GateName.CX, carry[i], b[i])


# -- layout ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Sha256Layout:
    """Which qubits are which. Every register is little-endian: ``reg[i]`` carries bit ``i``.

    Attributes:
        message: the sixteen 32-bit message words ``W_0..W_15`` of the block, as FIPS reads them —
            word ``j`` is bytes ``4j..4j+3`` of the block, big-endian. After the circuit runs these
            hold ``W_48..W_63``: the schedule is in place, and an oracle gets its input back by
            running the inverse, not by keeping a copy.
        digest: eight 32-bit words; after the circuit, ``H_0..H_7`` of the digest.
        scratch: the shared 32-qubit register ``Ch``/``Maj``/``S`` and constants pass through.
        ancilla: the adder's carry ancilla.
    """

    message: tuple[tuple[int, ...], ...]
    digest: tuple[tuple[int, ...], ...]
    scratch: tuple[int, ...]
    ancilla: int
    num_qubits: int

    @classmethod
    def standard(cls, extra: int = 0) -> "Sha256Layout":
        words = lambda base, count: tuple(  # noqa: E731 - a local shape, used twice
            tuple(range(base + WORD * j, base + WORD * (j + 1))) for j in range(count)
        )
        message = words(0, 16)
        digest = words(16 * WORD, 8)
        scratch = tuple(range(24 * WORD, 25 * WORD))
        return cls(message, digest, scratch, 25 * WORD, 25 * WORD + 1 + extra)

    def message_bit(self, byte_offset: int, bit: int) -> int:
        """The qubit carrying bit ``bit`` (0 = least significant) of block byte ``byte_offset``."""
        if not (0 <= byte_offset < 64 and 0 <= bit < 8):
            raise ValueError(f"byte {byte_offset} bit {bit} is outside a 64-byte block")
        word, position = divmod(byte_offset, 4)
        return self.message[word][(3 - position) * 8 + bit]


def pad_single_block(message: bytes) -> bytes:
    """FIPS 180-4 padding, refused unless the result is exactly one block."""
    if len(message) > 55:
        raise ValueError(f"{len(message)} bytes need two blocks; this circuit is the one-block hash")
    return message + b"\x80" + b"\x00" * (55 - len(message)) + struct.pack(">Q", 8 * len(message))


# -- the compression function ---------------------------------------------------------------------


def _load_constant(gl: GateList, register, value: int) -> None:
    """XOR a classical constant into a register: one X per set bit. Self-inverse."""
    for i in range(WORD):
        if (value >> i) & 1:
            gl.append(GateName.X, register[i])


def _add_via_scratch(gl: GateList, lay: Sha256Layout, target, compute) -> None:
    """``target += f`` where ``compute`` XORs ``f`` into clean scratch and is its own inverse."""
    scratch = list(lay.scratch)
    compute(scratch)
    ripple_carry_add(gl, scratch, list(target), lay.ancilla)
    compute(scratch)


def _ch(gl: GateList, e, f, g, scratch) -> None:
    """``scratch ^= Ch(e,f,g) = g ^ (e & (f ^ g))``: 32 Toffolis, and ``f`` is restored."""
    for i in range(WORD):
        gl.append(GateName.CX, g[i], scratch[i])
        gl.append(GateName.CX, g[i], f[i])
        gl.append(GateName.CCX, e[i], f[i], scratch[i])
        gl.append(GateName.CX, g[i], f[i])


def _maj(gl: GateList, a, b, c, scratch) -> None:
    """``scratch ^= Maj(a,b,c) = c ^ ((a ^ c) & (b ^ c))``: 32 Toffolis, ``a`` and ``b`` restored."""
    for i in range(WORD):
        gl.append(GateName.CX, c[i], scratch[i])
        gl.append(GateName.CX, c[i], a[i])
        gl.append(GateName.CX, c[i], b[i])
        gl.append(GateName.CCX, a[i], b[i], scratch[i])
        gl.append(GateName.CX, c[i], b[i])
        gl.append(GateName.CX, c[i], a[i])


def build_sha256_compression(
    layout: Sha256Layout | None = None, *, rounds: int = 64, gl: GateList | None = None
) -> tuple[GateList, Sha256Layout]:
    """The one-block SHA-256 of whatever the message register holds, into the digest register.

    The digest register must arrive as ``|0>``: the circuit loads the initial value itself, so that
    "the hash circuit" includes every gate the hash needs. ``rounds`` exists for the tests, which
    check reduced-round outputs against a reference implementation so that a defect is localised to
    a round instead of being a wrong digest after sixty-four of them; anything but 64 is not SHA-256.

    Args:
        layout: where the registers live; the standard 801-qubit layout if omitted.
        rounds: number of rounds, 1..64.
        gl: append to this gate list instead of a fresh one (the oracle builder does).
    """
    if not 1 <= rounds <= 64:
        raise ValueError(f"rounds={rounds} is outside 1..64")
    lay = layout or Sha256Layout.standard()
    gl = gl if gl is not None else GateList(lay.num_qubits, label=f"sha256_compression/{rounds}")

    state = [list(word) for word in lay.digest]
    for word, value in zip(state, IV):
        _load_constant(gl, word, value)
    window = [list(word) for word in lay.message]

    for t in range(rounds):
        if t >= 16:
            # W_t = s1(W_{t-2}) + W_{t-7} + s0(W_{t-15}) + W_{t-16}, written over W_{t-16}.
            slot = window[t % 16]
            _add_via_scratch(gl, lay, slot, lambda s, x=window[(t - 2) % 16]:
                             _xor_linear(gl, x, s, _SMALL_SIGMA_1))
            ripple_carry_add(gl, window[(t - 7) % 16], slot, lay.ancilla)
            _add_via_scratch(gl, lay, slot, lambda s, x=window[(t - 15) % 16]:
                             _xor_linear(gl, x, s, _SMALL_SIGMA_0))
        a, b, c, d, e, f, g, h = state
        _add_via_scratch(gl, lay, h, lambda s: _ch(gl, e, f, g, s))
        _add_via_scratch(gl, lay, h, lambda s: _xor_linear(gl, e, s, _BIG_SIGMA_1))
        _add_via_scratch(gl, lay, h, lambda s, k=K[t]: _load_constant(gl, s, k))
        ripple_carry_add(gl, window[t % 16], h, lay.ancilla)
        ripple_carry_add(gl, h, d, lay.ancilla)
        _add_via_scratch(gl, lay, h, lambda s: _maj(gl, a, b, c, s))
        _add_via_scratch(gl, lay, h, lambda s: _xor_linear(gl, a, s, _BIG_SIGMA_0))
        state = [h, a, b, c, d, e, f, g]            # the relabelling: no gates

    # Feed-forward from a *constant* initial value: H_i = IV_i + state_i, added as a constant. A
    # chained block would need the previous chaining value kept in a register instead.
    for word, value in zip(state, IV):
        _add_via_scratch(gl, lay, word, lambda s, v=value: _load_constant(gl, s, v))

    # The relabelling has permuted which physical word is H_0; report the digest in FIPS order.
    final = Sha256Layout(lay.message, tuple(tuple(w) for w in state), lay.scratch, lay.ancilla,
                         lay.num_qubits)
    return gl, final


# -- the preimage predicate ------------------------------------------------------------------------


def build_sha256_preimage_predicate(
    prefix: bytes, search_bytes: int, target: bytes, image_bits: int = 256
) -> tuple[GateList, Sha256Layout, list[int], int]:
    """``flag ^= [ SHA-256(prefix || x) agrees with target on its first image_bits bits ]``.

    The full-width form of the corpus's LM-OTS chain game: ``prefix`` is the public
    ``I || q || i || j``, ``x`` is the ``search_bytes``-byte value being inverted, and ``image_bits``
    is the digest truncation (256 for ``n = 32``, 192 for the ``n = 24`` parameter sets). This is
    the oracle sandwich a Grover iteration calls — hash, compare, **un-hash** — so its cost is two
    hashes and one wide comparison, which is the number a "gates per oracle query" figure has to be
    compared with; one hash is half of it.

    Returns ``(gate list, layout, search qubits, flag qubit)``. The search qubits are the bits of
    ``x`` in message order (byte 0 first, least significant bit first within a byte).
    """
    if len(target) != 32:
        raise ValueError("target must be a 32-byte SHA-256 digest (it is truncated by image_bits)")
    if not 1 <= image_bits <= 256:
        raise ValueError(f"image_bits={image_bits} is outside 1..256")
    if search_bytes < 1:
        raise ValueError("search_bytes must be at least 1")
    block = pad_single_block(prefix + b"\x00" * search_bytes)

    lay = Sha256Layout.standard(extra=1)
    flag = lay.num_qubits - 1
    gl = GateList(lay.num_qubits, label=f"sha256_preimage/{len(prefix)}+{search_bytes}/{image_bits}")

    search = [lay.message_bit(len(prefix) + byte, bit)
              for byte in range(search_bytes) for bit in range(8)]
    fixed = GateList(lay.num_qubits)
    for offset, value in enumerate(block):
        if len(prefix) <= offset < len(prefix) + search_bytes:
            continue                                  # these bits are the search register
        for bit in range(8):
            if (value >> bit) & 1:
                fixed.append(GateName.X, lay.message_bit(offset, bit))

    hash_part = GateList(lay.num_qubits)
    hash_part.extend(fixed)
    _, final = build_sha256_compression(lay, gl=hash_part)

    # Digest bit k (0 = the first, most significant bit of H_0) against the target's bit k.
    target_value = int.from_bytes(target, "big")
    controls, flips = [], []
    for k in range(image_bits):
        qubit = final.digest[k // WORD][WORD - 1 - (k % WORD)]
        controls.append(qubit)
        if not (target_value >> (255 - k)) & 1:
            flips.append(qubit)                       # compare-to-zero: flip, control, flip back

    gl.extend(hash_part)
    for qubit in flips:
        gl.append(GateName.X, qubit)
    gl.append(GateName.MCX, *controls, flag)
    for qubit in flips:
        gl.append(GateName.X, qubit)
    gl.extend(hash_part.inverse())
    return gl, final, search, flag
