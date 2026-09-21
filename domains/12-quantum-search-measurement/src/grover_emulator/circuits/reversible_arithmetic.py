"""Reversible arithmetic blocks, built directly in the IR.

These are hand-built rather than imported from a framework, and that is a decision with a reason
behind it rather than a preference. Two framework candidates were tried first and both failed the
API probe: ``WeightedSumGate`` cannot be synthesised inside its own declared width (it demands three
undocumented clean ancillas), and ``CDKMRippleCarryAdder`` — although present and correct — carries
no ``.definition``, so it cannot be expanded into IR gates and would have to be counted as an opaque
blob. An opaque blob is exactly what this project exists to avoid: the whole point is that the gate
count describes the circuit that ran.

Every block here is verified **exhaustively** — applied to every basis state at small widths and
compared against Python's own integer arithmetic — and the verify functions are in this module so
that the test suite and the build call the same code.

The constructions
-----------------
``add_constant`` uses the fact that adding a constant is adding powers of two, and adding ``2**i``
is incrementing the sub-register above bit ``i``. An increment of ``n`` bits is ``n``
multi-controlled X gates applied from the top down, because a bit flips exactly when every bit below
it is set. So the adder is a composition of increments, correct by the associativity of addition,
and auditable by reading it.

This costs ``O(n**2)`` multi-controlled gates rather than the ``O(n)`` of a carry-chain adder. That
is a real cost and it is reported as one — an optimised constant-adder is available and would reduce
it, and when that substitution is made the gate count will change, which is the point of counting it.

``less_than_constant`` builds a running "all higher bits matched" chain in fresh ancillas, one
Toffoli per bit, and marks the flag at each position where the constant has a 1 and the register has
a 0. Those positions are mutually exclusive, so XOR-marking them is the same as OR-marking them.

``sample_intervals`` lives here rather than in the relation's own module because the interval
computation is a *lowering* of the relation and not a part of it. The relation says "round to
nearest and reduce"; the intervals are what that becomes when the only thing available is a
comparator. Keeping the two apart is what lets the test suite check the lowering against the
relation rather than against itself.
"""

from __future__ import annotations

from .ir import GateList, GateName

__all__ = [
    "multi_controlled_x",
    "add_constant",
    "less_than_constant",
    "equal_to_constant",
    "sample_intervals",
    "verify_add_constant",
    "verify_less_than_constant",
    "verify_equal_to_constant",
]


def multi_controlled_x(gl: GateList, controls: tuple[int, ...], target: int) -> None:
    """Append the multi-controlled X that fits the control count.

    One control is a CX, two is a Toffoli, three or more is the IR's ``mcx``. Emitting the smallest
    gate that fits matters for the accounting: a two-control X counted as a multi-controlled one
    would inflate every Toffoli-equivalent number in the project.
    """
    if not controls:
        gl.append(GateName.X, target)
    elif len(controls) == 1:
        gl.append(GateName.CX, controls[0], target)
    elif len(controls) == 2:
        gl.append(GateName.CCX, controls[0], controls[1], target)
    else:
        gl.append(GateName.MCX, *controls, target)


def _increment_subregister(gl: GateList, reg: list[int], start: int, control: int | None) -> None:
    """Add 1 to the sub-register ``reg[start:]``, optionally controlled.

    Bits are processed from the top of the sub-register down, so that when bit ``j`` is flipped the
    bits below it still hold their pre-increment values — which is what "flip ``j`` iff every lower
    bit is set" requires. Processing upward instead would read already-flipped bits and compute the
    wrong function; it is a one-line change with no symptom other than wrong answers.
    """
    for j in range(len(reg) - 1, start - 1, -1):
        controls = tuple(reg[start:j])
        if control is not None:
            controls = (control,) + controls
        multi_controlled_x(gl, controls, reg[j])


def add_constant(
    gl: GateList,
    reg: list[int],
    constant: int,
    control: int | None = None,
) -> None:
    """``reg += constant``, or ``reg += constant`` iff ``control`` is set.

    The register is little-endian: ``reg[0]`` is the least significant bit. The addition is modulo
    ``2**len(reg)``; callers that need a modulus reduce explicitly, and the whole point of the
    surrounding module is that the reduction is carried rather than assumed away.
    """
    if constant < 0:
        raise ValueError(f"constant must be non-negative, got {constant}")
    if len(reg) < 1:
        raise ValueError("reg must have at least one qubit")
    if constant >= (1 << len(reg)):
        raise ValueError(f"constant {constant} does not fit in {len(reg)} qubits")

    for bit in range(len(reg)):
        if (constant >> bit) & 1:
            _increment_subregister(gl, reg, bit, control)


def less_than_constant(
    gl: GateList,
    reg: list[int],
    constant: int,
    flag: int,
    work: list[int],
) -> None:
    """``flag ^= [reg < constant]``.

    ``work`` must supply ``len(reg)`` clean ancillas. They are returned to ``|0>`` before this
    returns, so the block is safe to compose: it leaves no trace except the flag.

    The chain ``work[i]`` holds "[every bit of ``reg`` strictly above ``i`` equals the corresponding
    bit of ``constant``]". At each ``i`` where the constant has a 1 and the register has a 0, the
    first difference is at ``i`` and the register is the smaller one — so the flag is XORed. Only
    the highest such position can be reached, which is why XORing is sound where ORing was meant.
    """
    n = len(reg)
    if len(work) < n:
        raise ValueError(f"need {n} work ancillas, got {len(work)}")
    if constant < 0:
        raise ValueError(f"constant must be non-negative, got {constant}")
    if constant >= (1 << n):
        # The register is always < 2**n, so the comparison is decided by the register's width alone.
        if constant > 0:
            gl.append(GateName.X, flag)
        return

    # Build the equality chain from the top down. work[n-1] is "the empty prefix matches" == 1.
    #
    # Each step needs the qubit to read 1 when it *matches* the constant bit, i.e. XNOR — so the
    # conjugation is applied where the constant bit is 0, not where it is 1. Conjugating on the
    # wrong sense builds a chain that means "differs" instead of "matches", and the comparison then
    # comes out inverted only for some constants, which is the shape of bug that survives a
    # spot-check.
    gl.append(GateName.X, work[n - 1])
    for i in range(n - 2, -1, -1):
        # work[i] = work[i+1] AND (reg[i+1] == constant[i+1])
        hi = reg[i + 1]
        if not (constant >> (i + 1)) & 1:
            gl.append(GateName.X, hi)
        gl.append(GateName.CCX, work[i + 1], hi, work[i])
        if not (constant >> (i + 1)) & 1:
            gl.append(GateName.X, hi)

    for i in range(n):
        if (constant >> i) & 1:
            gl.append(GateName.X, reg[i])
            gl.append(GateName.CCX, work[i], reg[i], flag)
            gl.append(GateName.X, reg[i])

    # Uncompute the chain, so the block leaves nothing behind but the flag. This is the exact
    # reverse of the build above, with the same conjugation sense; the two must move together.
    for i in range(0, n - 1):
        hi = reg[i + 1]
        if not (constant >> (i + 1)) & 1:
            gl.append(GateName.X, hi)
        gl.append(GateName.CCX, work[i + 1], hi, work[i])
        if not (constant >> (i + 1)) & 1:
            gl.append(GateName.X, hi)
    gl.append(GateName.X, work[n - 1])


def equal_to_constant(gl: GateList, reg: list[int], value: int, flag: int) -> None:
    """``flag ^= [reg == value]``.

    One multi-controlled X with X-conjugation on the register bits where ``value`` has a 0, and no
    ancillas at all — the conjunction of bit equalities *is* a multi-controlled X once each bit is
    conjugated into the sense that makes a 1 mean "matches".
    """
    if value < 0 or value >= (1 << len(reg)):
        raise ValueError(f"value {value} does not fit in {len(reg)} qubits")
    zero_bits = [reg[i] for i in range(len(reg)) if not (value >> i) & 1]
    for q in zero_bits:
        gl.append(GateName.X, q)
    multi_controlled_x(gl, tuple(reg), flag)
    for q in zero_bits:
        gl.append(GateName.X, q)


def sample_intervals(q_l: int, p: int, a: int, v_max: int | None = None) -> tuple[tuple[int, int], ...]:
    """The accumulator values whose sample equals ``a``, as inclusive ``(low, high)`` intervals.

    ``round_half_up(v * p, q_l) == a`` rearranges to ``q_l*(2a-1) <= 2*v*p < q_l*(2a+1)``, so the
    bucket for ``a`` over one period is a single interval — **except for ``a = 0``, whose bucket is
    the union of the bottom interval and the top one**, because the raw rounded value ``p`` reduces
    to ``0`` mod ``p``. That wrap is the trap this function exists to make impossible to forget: it
    fires only for accumulator values in the top ``1/p`` of the range, which no random instance
    reaches, and a circuit that omits it still agrees with the relation on all but a handful of rows
    while usually still producing ``M = 1`` and the right peak. It would not look like a bug.

    Args:
        v_max: if given, the intervals are repeated across every period up to this accumulator
            value and intersected with ``[0, v_max]``.

    **Why ``v_max`` exists, and what it removes from the circuit.** ``round_half_up((v + k*q_l)*p,
    q_l) == round_half_up(v*p, q_l) + k*p``, so the sample is periodic in the accumulator with
    period ``q_l``. A caller that passes ``v_max`` is therefore comparing the *raw* accumulator
    against a precomputed table instead of reducing it mod ``q_l`` first — which means the QLWR
    lowering needs **no modular reduction circuit at all**. The reduction is not skipped; it is
    absorbed into the table, where it costs nothing. Passing ``v_max=None`` gives the single-period
    buckets, which is what a caller that *did* reduce would use.
    """
    if not 0 <= a < p:
        raise ValueError(f"a={a} is not a residue mod p={p}")

    def bucket(value: int) -> tuple[int, int] | None:
        lo = -((-q_l * (2 * value - 1)) // (2 * p))  # ceil
        hi = -((-q_l * (2 * value + 1)) // (2 * p)) - 1  # ceil, minus one
        if hi < lo:
            return None
        return (lo, hi)

    # One period first, clipped to [0, q_l - 1]. Clipping is what makes the period a partition:
    # the wrap bucket for a = 0 extends past q_l - 1, and repeating an unclipped bucket across
    # periods double-counts the values where it overlaps the next period's primary bucket.
    period: list[tuple[int, int]] = []
    for value in [a] + ([p] if a == 0 else []):
        base = bucket(value)
        if base is None:
            continue
        lo, hi = max(base[0], 0), min(base[1], q_l - 1)
        if hi >= lo:
            period.append((lo, hi))

    period.sort()
    merged: list[tuple[int, int]] = []
    for lo, hi in period:
        if merged and lo <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))

    if v_max is None:
        return tuple(merged)

    out: list[tuple[int, int]] = []
    for lo0, hi0 in merged:
        k = 0
        while lo0 + k * q_l <= v_max:
            lo, hi = max(lo0 + k * q_l, 0), min(hi0 + k * q_l, v_max)
            if hi >= lo:
                out.append((lo, hi))
            k += 1
    out.sort()
    return tuple(out)


# -----------------------------------------------------------------------------------------------
# exhaustive verification
# -----------------------------------------------------------------------------------------------


def verify_add_constant(n: int, constant: int, controlled: bool) -> None:
    """Apply the block to every basis state and compare against Python integer addition.

    Both control values are exercised, and the control qubit is checked to have *survived* — a
    controlled adder that quietly overwrites its control would pass a register-only comparison.
    """
    capacity = 1 << n
    width = n + (1 if controlled else 0)
    for control_value in ((0, 1) if controlled else (None,)):
        for value in range(capacity):
            gl = GateList(width)
            reg = list(range(n))
            control = n if controlled else None
            state = value
            if controlled and control_value:
                state |= 1 << control
            # Only the block is applied. Preparing the control qubit by appending an X to the same
            # list would apply that X too, and the block would look as though it had flipped its
            # own control — a verifier artefact, not a circuit defect.
            start = len(gl.gates)
            add_constant(gl, reg, constant, control)
            block = GateList(width, gl.gates[start:], "add")

            out = _apply_classical(block, state, width)
            got_reg = out & (capacity - 1)
            enabled = True if not controlled else bool(control_value)
            want_reg = (value + constant) % capacity if enabled else value
            if got_reg != want_reg:
                raise AssertionError(
                    f"add_constant(n={n}, c={constant}, controlled={controlled}): "
                    f"register |{value}> -> {got_reg}, want {want_reg}"
                )
            if controlled and ((out >> control) & 1) != control_value:
                raise AssertionError(
                    f"add_constant(n={n}, c={constant}) overwrote its control qubit"
                )


def verify_less_than_constant(n: int, constant: int) -> None:
    """Apply the comparator to every basis state and compare against Python's ``<``."""
    for value in range(1 << n):
        gl = GateList(n + n + 1)
        reg = list(range(n))
        work = list(range(n, 2 * n))
        flag = 2 * n
        less_than_constant(gl, reg, constant, flag, work)
        state = _apply_classical(gl, value, 2 * n + 1)
        got = (state >> flag) & 1
        want = int(value < constant)
        if got != want:
            raise AssertionError(
                f"less_than_constant(n={n}, c={constant}): |{value}> gave flag={got}, want {want}"
            )
        residue = state & ((1 << (2 * n)) - 1)
        if residue != value:
            raise AssertionError(
                f"less_than_constant(n={n}, c={constant}) left work qubits dirty on |{value}>: "
                f"{residue} != {value}"
            )


def verify_equal_to_constant(n: int, value: int) -> None:
    """Apply the equality block to every basis state and compare against Python's ``==``."""
    for x in range(1 << n):
        gl = GateList(n + 1)
        reg = list(range(n))
        flag = n
        equal_to_constant(gl, reg, value, flag)
        state = _apply_classical(gl, x, n + 1)
        got = (state >> flag) & 1
        want = int(x == value)
        if got != want:
            raise AssertionError(
                f"equal_to_constant(n={n}, v={value}): |{x}> gave flag={got}, want {want}"
            )


def _apply_classical(gl: GateList, state: int, width: int) -> int:
    """Apply a permutation-only gate list to one basis-state integer.

    A local copy of what :mod:`grover_emulator.utils.validation` does at scale, kept here so the
    verify functions depend on nothing but the IR — a verifier that shares a simulator with the
    thing it verifies is not verifying as much as it looks like.
    """
    if not gl.is_classically_simulable():
        raise AssertionError("a verification block must be permutation-only")
    s = state
    for gate in gl.gates:
        if gate.name is GateName.X:
            s ^= 1 << gate.qubits[0]
        elif gate.name is GateName.CX:
            if (s >> gate.qubits[0]) & 1:
                s ^= 1 << gate.qubits[1]
        elif gate.name is GateName.CCX:
            if ((s >> gate.qubits[0]) & 1) and ((s >> gate.qubits[1]) & 1):
                s ^= 1 << gate.qubits[2]
        elif gate.name is GateName.MCX:
            controls, target = gate.qubits[:-1], gate.qubits[-1]
            if all((s >> c) & 1 for c in controls):
                s ^= 1 << target
        else:
            # Not "is not a permutation": PERM is one, and is classically simulable, but it is not
            # a gate the arithmetic is built from, and this local copy deliberately knows only those.
            raise AssertionError(
                f"{gate.name} is not one of the permutation gates (X, CX, CCX, MCX) a verification "
                "block is built from"
            )
    return s
