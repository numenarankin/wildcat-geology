"""Gas-well deliverability. Ahmed Chapter 8, plus the Texas RRC test rules.

A package rather than a module because the five tools here (#82-#86) each carry
their own constant tables and those tables collide by name while differing in
shape: three of them define `FORMS`, two define `FORM_PRESSURE_LIMITS`, and
`METHODS` is a tuple of fit procedures in one and a dict of rate equations in
another. Flattening them would have meant renaming constants inside five sets of
carefully-sourced tables, so each tool keeps its own namespace and this file
re-exports the public surface. `import tools.deliverability as dl` works exactly
as it did when this was one file.

Two things are load-bearing across the whole package:

**Every coefficient is form-specific.** Ahmed fits the same three-point test four
ways and the laminar coefficients come out 318, 0.06 and 22.28e3 — six orders of
magnitude apart, in three different units. So `form` is a required argument
everywhere, it travels on every result, and a C or an `a` without its form is a
unit bug waiting to happen.

**There is exactly one fit-to-rate path.** `rate.deliverability_rate` is it.
`aof_compute` is that evaluator at p_wf = 0 and `gas_ipr_curve` is it over a
grid, so the curve's zero point *is* the AOF by construction rather than by two
implementations happening to agree.

The four methods disagree by **26.8%** on Ahmed's own test data, which is why no
result here is ever returned without its method label. The catalog quotes 23.5%,
which is the spread across three of them (LIT p-squared 8763 to LIT
pressure-approximation 10827); the pseudopressure method's 8536 is lower than
all three, so the full four-method spread is 8536 to 10827.
"""
from .backpressure import backpressure_fit
from .houpeurt import houpeurt_fit, lit_fit
from .rate import (
    aof_compare,
    aof_compute,
    backpressure_rate,
    deliverability_rate,
    lit_rate,
)
from .ipr import gas_ipr, gas_ipr_curve
from .testing import deliverability_test_interpret, g10_compliance_check

__all__ = [
    "backpressure_fit",
    "houpeurt_fit",
    "lit_fit",
    "deliverability_rate",
    "aof_compute",
    "aof_compare",
    "backpressure_rate",
    "lit_rate",
    "gas_ipr",
    "gas_ipr_curve",
    "deliverability_test_interpret",
    "g10_compliance_check",
]
