"""Classical Attack Reduction Tester for the QPT-128 primitives.

Exposes the raw mathematical primitives of the QPT-128 record as standalone objects with no network,
framing or proof layer around them, runs classical attacks against scaled-down instances, and maps
how the attacker's workload grows with the size parameter. See :mod:`qpt_cart.scope` for what a
workload curve can and cannot establish — it is stated before any result this package prints.
"""

__version__ = "0.1.0"
