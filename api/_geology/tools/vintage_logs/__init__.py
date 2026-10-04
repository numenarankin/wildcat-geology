"""Vintage electric logs: the ES suite, Rt, formation factor. Tools #96-#100.

Catalog section 14 --- "the largest addition, and the one that decides whether a
client's file cabinet is usable at all." A 1950s ES log has no gamma ray, no
density and no neutron: it has SP, two normals and a lateral, and everything
downstream depends on knowing precisely which curve is which.

The suite composition is one of the better-sourced facts in this corpus, stated
twice independently --- `trieste#0` and `beg-boonsville#34` --- with identical
spacings: SP, 16-in. normal, 64-in. normal, 18-ft 8-in. (224-in.) lateral.

**Where this section stops.** `rt_from_long_normal` has three branches keyed on
R16"/Rm, and only the lowest computes. Fig. 7-9 Part A survived OCR as a table;
**Part B lost its entire response column to an image**, and Parts 2 and 3 both
terminate there. Branch 3 additionally needs Chart B-2, absent from the corpus.
So the catalog's "must refuse above 50" understates it: two of three branches are
unreachable, not one. All six of the source's inequalities are strict, so ratios
of exactly 10 and exactly 50 belong to no branch at all and refuse with distinct
labels --- at 50 that ambiguity is harmless (both candidates refuse anyway), at 10
it has teeth, because branch 1 would otherwise return a number.

`departure_correction` answers "is this reading usable, and how is the bed
geometry distorting it" --- never "here is the corrected Rt", which only the chart
families could give. It holds a worked borehole correction from its own source
(60 ohm-m, Rm 0.5, 9-in hole -> 97.5) and **refuses with all three inputs
present**, because the step between them is a curve on a chart. That case is kept
in its docstring as a free test for whoever digitises the charts.

Two independent transcriptions agree. #97 and #98 each read Fig. 7-9 Part A out of
the OCR without seeing the other, and every multiplier matches (1.0, 2.0, 1.0,
2.0, 2.0). #97 found a second, internal corroboration: the table routes 5-10 ft
beds to the *short* normal, and the long normal's reversal threshold derived
separately from the EPA prose is 5.33 ft --- the device switch lands exactly where
the geometric rule says the long normal dies.

**Open reconciles between #97 and #98**, neither agent able to see the other:

- Fig. 7-9 Part A is transcribed **twice**, once per module. Pick one owner.
- The bed-thickness snap tolerances are *disjoint*: +/-2.5 ft absolute in #97,
  +/-15% fractional in #98. A 12.6 ft bed matches one and refuses under the other.
  Both PROVISIONAL; they cannot both stand.
- The same OCR slip is read two ways: the Short Normal row prints `R_18`, which
  #97 reads as `R_16` from the short-normal definition and #98 flags as the
  lateral's symbol.

And one seam between #99 and #100: `formation_factor_field` records its provenance
as `assumptions["route"]`, while `porosity_from_formation_factor` takes the route
via an `f_source` argument. A harness passing the `Quantity` straight through will
therefore **not** trip #100's circularity check on a porosity-route F --- which is
the exact case that check exists for, since deriving porosity from an F that was
itself derived from porosity is circular. Wire the route through at the call site
until the seam is closed.

Both tools carry a permanent flag that their answer is not a measurement: F from a
hydrocarbon-bearing interval is too high, so the porosity comes out too low, with
no outward sign. `formation_factor_field` therefore refuses a caller who offers
"the resistivity profile looks wet" as evidence --- Asquith only claims that
profile implies Sw *much greater than 60%*, which is not 100%, and Ro means 100%.
"""
from .es_curves import es_curve_identify
from .departure import bed_geometry, departure_correction, usability_verdict
from .rt_normal import es_rt_branch, rt_from_long_normal
from .formation_factor import (
    formation_factor_field,
    formation_factor_from_porosity,
    local_archie_constants,
)
from .porosity_from_f import (
    lithology_am_pair,
    porosity_from_formation_factor,
    porosity_spread_from_formation_factor,
)

__all__ = [
    "es_curve_identify",
    "departure_correction",
    "usability_verdict",
    "bed_geometry",
    "rt_from_long_normal",
    "es_rt_branch",
    "formation_factor_field",
    "formation_factor_from_porosity",
    "local_archie_constants",
    "porosity_from_formation_factor",
    "porosity_spread_from_formation_factor",
    "lithology_am_pair",
]
