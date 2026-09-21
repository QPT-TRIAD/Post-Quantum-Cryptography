"""What every attack returns: work, time, and whether it actually won.

**Work is counted, not only timed.** Wall-clock on a shared desktop carries cache effects,
interpreter overhead and other processes; a count of the attack's own basic operation does not. So
each attack reports ``work`` in a named unit (candidates tried, row operations, difference vectors
tried) wherever it can, and the curve is fitted to that. Seconds are always recorded too, and are
the only measure for the tools that do not expose a count (a Groebner engine, BKZ).

**A loss is a result.** ``success=False`` with a reason is recorded and reported; an attack that
ran out of budget is not evidence that the primitive held, and the report keeps the two apart.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

__all__ = ["AttackResult"]


@dataclass
class AttackResult:
    attack: str
    primitive: str
    size: int                       # the size parameter the curve is drawn against
    seed: int
    success: bool
    work: float | None              # None when the tool exposes no operation count
    work_unit: str
    seconds: float
    verified: bool = False          # the recovered secret was checked with the primitive's verify
    detail: dict[str, Any] = field(default_factory=dict)
    not_run_reason: str | None = None
    provenance: str = "measured"

    def to_dict(self) -> dict:
        return asdict(self)
