"""What this tester can establish, stated once and printed before every result.

The boundary is structural, not framing: :data:`SCOPE_BOUNDARY` is emitted verbatim at the top of
every report, before any table, and the tests check that it is.
"""

SCOPE_BOUNDARY = (
    "This tester runs real classical attacks — exhaustive search, Groebner-basis algebraic solving, "
    "collision finding, lattice reduction — against scaled-down instances of the QPT-128 "
    "primitives, and measures how the attacker's work grows with the size parameter. It cannot run "
    "any of them at production size; that is the point of the design being tested. A workload "
    "curve measured at small sizes can do two things. It can FALSIFY: if an attack's work grows "
    "polynomially where the security argument needs it to grow exponentially, that is a shortcut, "
    "and it is a finding at any size. And it can CALIBRATE: it checks that an attack costs what "
    "the record's formula says it costs, at sizes where that can be checked. It cannot VALIDATE "
    "production security. Exponential growth over the sizes measured here does not mathematically "
    "prove exponential growth at n = 256: algebraic attacks change regime as the solving degree "
    "steps up, lattice reduction is polynomial (LLL suffices) across the whole toy range, and the "
    "record's own attack lab found small-size fits mis-extrapolating by +4.6, -12.4 and -38.1 "
    "bits. It also says nothing about attacks that were not run. Every number below is labelled "
    "measured, fitted, or extrapolated, and the three are never mixed."
)

MEASURED = "measured"
FITTED = "fitted (to measured points; not a measurement)"
EXTRAPOLATED = "extrapolated (model-based; not measured)"
