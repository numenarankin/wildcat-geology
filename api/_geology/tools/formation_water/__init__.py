"""Formation water: NaCl equivalence, Rw, salinity, the Hingle plot. Tools #91-#95.

Catalog section 13. A package because each tool quotes a different document and
two of them define a module-level `SOURCE`.

**Most of this section cannot be computed, and that is the finding.** The
ppm<->Rw relation exists in the corpus only as Schlumberger chart Gen-9, an
image. So `rw_from_tds` and `salinity_from_rw` refuse in every branch that
crosses between a concentration and a resistivity, in both directions --- the
inverse of a chart is still a chart. A matched pair of honest refusals is the
correct outcome here, and a `Quantity` appearing on either of those paths would
mean somebody fitted the chart from memory.

What *is* computable and sourced:

- **The Arps temperature conversion**, R2 = R1 (T1+X)/(T2+X). Not in the section's
  own anchor --- it lives at `asquith#9` and `mosul#1` --- but real, and it is the
  whole of `resistivity_at_temperature`. `salinity_from_rw` proved that Gen-9's
  temperature axis *is* the Arps family, by reading two of the chart's own points
  out of the prose (2.5 ohm-m at 70F -> 1.3 at 140F; Arps gives 1.3077) and
  matching at the chart's two significant figures. So normalising to a chart-entry
  temperature is exact, not an approximation of a chart read.
- **`hingle_plot`**, which has a genuine published worked example --- not at the
  catalog's anchor but two segments later, at `asquith#51`, with a ten-zone
  dataset at `#48`.
- **`nacl_equivalent`**, for exactly two ions at exactly one salinity. Its
  multiplier chart (Fig-3) is not merely undigitised, it is **absent from the
  corpus entirely**; only k(Cl)=1 and k(Mg)=1.32 at 7,000 ppm survive as printed
  numbers. The multiplier is a function of total solids, so one point per curve is
  not a curve --- including for the sulfate-heavy water the catalog says this tool
  exists to fix. It refuses everything else.
- **`produced_water_query`**, whose dataset AND documentation are both absent; the
  corpus document is the USGS landing page, two-thirds of it a staff directory.
  The release is CC0, so vendoring the CSV would delete that refusal outright.

Two corpus conflicts recorded here rather than silently resolved:

**The Arps Celsius constant.** Asquith prints 21.0, Mosul prints 21.5, ~0.7% over
20-80C. Found independently by two agents. Neither is averaged; the Fahrenheit
constant 6.77 is unanimous and is the default path.

**`resistivity_at_temperature` exists twice** --- here and in `petrophysics.py`.
They agree numerically; this one adds the refusals (an Rwe handed in where an Rw
is wanted, the Arps pole, the disputed Celsius constant as an argument). That is a
one-source-of-truth violation and it is deliberate only until group D lands: the
`petrophysics.py` copy is another agent's module and folding them mid-round would
have collided. **Fold them, keeping this one's refusals.**
"""
from .nacl import nacl_equivalent, normalize_ion
from .rw_tds import resistivity_at_temperature, rw_from_tds
from .produced_water import produced_water_query, produced_water_spread
from .salinity import salinity_from_rw
from .hingle import hingle_plot

__all__ = [
    "nacl_equivalent",
    "normalize_ion",
    "rw_from_tds",
    "resistivity_at_temperature",
    "produced_water_query",
    "produced_water_spread",
    "salinity_from_rw",
    "hingle_plot",
]
