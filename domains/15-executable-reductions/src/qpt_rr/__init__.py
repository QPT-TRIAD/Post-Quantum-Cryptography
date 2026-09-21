"""Reduction runner for the QPT-128 Mode B security proofs.

A security proof by reduction is a *program*: it takes any adversary that breaks the scheme and
turns it into a solver for a hard problem. On paper that program is prose. Here it is code, and it
is run — against adversaries that really do break toy-sized instances — to check that what comes
out the other end is a genuine solution of the hard problem, as often as the theorem says it is.
See :mod:`qpt_rr.scope` for what that can and cannot establish.
"""

__version__ = "0.1.0"
