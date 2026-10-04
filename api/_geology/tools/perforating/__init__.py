"""Perforating: skin, productivity, underbalance, gun configuration. Tools #87-#90.

A package for the same reason as `deliverability` — #88 and #89 both define a
module-level `SOURCE`, and each tool's constant tables are quoted from a
different document.

**Not to be confused with `tools/perforation.py`**, which is a different agent's
module for #50/#51 — *where* to perforate (optimum interval, partial-penetration
rate). This package is *how* the perforations behave once made. The two names
are one letter apart and that is worth fixing; `perforating` won the rename only
because a package silently shadows a same-named module and this one arrived
second. Raised for the three agents to settle rather than decided here.

The section is unusual in how little of it is arithmetic:

- **#87 `perforation_skin`** is the only real equation, Karakas-Tariq. Its source
  carries the procedure and all three constant tables intact, but its *worked
  example* is arithmetically corrupt in five separate ways (feet added to inches
  throughout, a shot density substituted for a spacing, two tables disagreeing by
  1000x on one gun). The published skin numbers are therefore not oracles and are
  not used as such. One number in that paper is self-consistent — the
  crushed-zone skin, 3.766428 — and it is the sourced anchor.
- **#88 `productivity_ratio`** implements a substitute, not its specified method.
  Locke (SPE 8804) is a bibliography line corpus-wide. The replacement,
  PR = ln(re/rw)/[ln(re/rw)+s], is itself sourced — it falls out of Ahmed Eq.
  6-145 — but it is blind to the shot density and phasing Locke's nomograph was
  for, so a Locke-shaped call refuses instead of quietly answering.
- **#89 `underbalance_recommend`** refuses unconditionally. Its chart is an image
  and the only numeric content that survived conversion is a ratio, so
  `underbalance_range` returns a 2-4x band around a caller-supplied King baseline
  and permeability never enters an expression at all.
- **#90 `perf_config_evaluate`** emits no merit score, because the source ranks
  four factors and publishes no weights. Its value is a count of source-stated
  rules violated; zero means "nothing published objects", not "good".

Three of the four exist mainly to decline, which is what this section actually
is once its images are subtracted.
"""
from .skin import crushed_zone_skin, perforation_skin
from .productivity import locke_productivity_ratio, productivity_ratio
from .underbalance import (
    underbalance_from_chart_point,
    underbalance_range,
    underbalance_recommend,
)
from .config import perf_config_evaluate

__all__ = [
    "perforation_skin",
    "crushed_zone_skin",
    "productivity_ratio",
    "locke_productivity_ratio",
    "underbalance_range",
    "underbalance_recommend",
    "underbalance_from_chart_point",
    "perf_config_evaluate",
]
