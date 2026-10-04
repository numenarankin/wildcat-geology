"""Borehole condition, per depth: `hole_quality` (#25).

Destination module `tools/borehole.py`. Spec: `specs/25-hole_quality.md`.

Four decisions here are load-bearing and none of them is visible from the
equations, which are trivial.

**Rugosity is a separate gate from the caliper, and it is the one that matters.**
`beg#40` is explicit: "The sidewall tool (density) is more prone to be incorrect
when the hole size is changing than when the hole size is large but constant."
A smoothly enlarged 12-inch hole can give a good density; a 9-inch hole with half
an inch of rugosity per foot cannot. An implementation that only compares caliper
to bit size passes a naive test and is wrong on real rock, so the two are
computed independently and reported independently, and neither substitutes for
the other. The rugosity of a sample is the **maximum** gradient over every 2-ft
window containing it, not a centred difference: a washout that opens and closes
inside 2 ft has equal endpoints and a centred difference of exactly zero, which
is the one feature the gate must never miss.

**Every hit says whose authority it rests on.** `tool-catalog.md:112` requires it:
DRHO > 0.20 g/cm3 is SOURCED (`asquith#18`) and can be told to an operator as the
density log's own verdict on itself; the caliper and rugosity cutoffs are ours
and are marked PROVISIONAL wherever they appear. `refusal_at()` therefore returns
a Refusal only for a SOURCED gate. Suppressing a porosity on a number nobody
published is a flag, not a refusal.

**Undergauge is a distinct condition and is not bad hole by default.** Everywhere
the corpus reads an undergauge caliper it reads it as good news - `asquith#8`
attributes it to "porous and permeable formations", `asquith#37` and `#75` both
use it as evidence of permeability. Marking a permeable pay sand bad because it
has mudcake on it would cost the operator a zone. Mudcake already has a sourced
gate: DRHO exists to correct for "borehole effects (primarily mudcake thickness)"
(`asquith#18`). So undergauge fires in its own gate, with `bad=False` unless the
caller says otherwise.

**Per-sample numbers are floats; operator-facing numbers are Quantities.** A
Quantity per sample per gate on a 7,000-sample log is tens of thousands of objects
carrying provenance the record already carries once. `null_scrub` sets the
precedent (`ScrubbedCurve.values` is `list[float | None]`); cutoffs, interval
tops and bases, extremes and fractions are Quantities.

DRHO_SUSPECT is **imported** from `.petrophysics`, never restated. Three copies of
one threshold is the reconcile failure this build keeps finding; there is one copy
and two importers (`quality.py` is the other).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .petrophysics import DRHO_SUSPECT
from .result import Quantity, Refusal

try:  # one source of truth for which mnemonic carries the bit size
    from .header import RRC_HEADER_ITEMS
except Exception:  # pragma: no cover - header (#4) is shipped; this is belt-and-braces
    RRC_HEADER_ITEMS = {}

# --- anchors ---------------------------------------------------------------

ASQUITH_DRHO = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#18"
ASQUITH_HOLE_DIAM = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#8"
ASQUITH_PAD = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#32"
ASQUITH_MUDCAKE = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#37"
ASQUITH_DIFFCAL = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#66"
ASQUITH_DIFFCAL_SIGN = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#69"
BEG_BADHOLE = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#40"

# The house rules are ours. They cite the line that settled them, not a corpus
# anchor, because claiming a corpus anchor for a number the corpus never printed
# is exactly the miscitation this layer exists to prevent.
OURS_WASHOUT = ("ours - tool-catalog.md:107 'Washout flag | DiffCal = caliper - "
                "bit size > +1.0 in | PROVISIONAL'; quantity sourced at " + ASQUITH_DIFFCAL)
OURS_RUGOSITY = ("ours - tool-catalog.md:108 '|d(CAL)/dz| > 0.5 in/ft over 2 ft | "
                 "PROVISIONAL'; quantity sourced at " + BEG_BADHOLE)
OURS_UNDERGAUGE = ("ours, with basis - " + ASQUITH_MUDCAKE + " reads 8.5 in in an "
                   "8.75 in hole as mudcake, i.e. DiffCal -0.25 in; sign and cause "
                   "sourced at " + ASQUITH_HOLE_DIAM)

# --- the threshold table ---------------------------------------------------
# Every entry marked SOURCED / PROVISIONAL / CALLER with its anchor, per
# `tool-catalog.md`'s "Thresholds the corpus does not supply". Every PROVISIONAL
# value is a keyword argument of `hole_quality`.

STATUS_SOURCED = "SOURCED"
STATUS_PROVISIONAL = "PROVISIONAL"
STATUS_CALLER = "CALLER"


@dataclass(frozen=True)
class GateSpec:
    """One gate's default cutoff, its status, and where the number came from."""

    key: str
    label: str
    unit: str
    relation: str          # ">" or "<"
    default: float
    status: str
    source: str
    basis: str
    bad_by_default: bool


GATE_SPECS: dict[str, GateSpec] = {
    # SOURCED. asquith#18: "Whenever the correction curve (DRHO) exceeds
    # 0.20 g/cm3, the value of the bulk density obtained from the bulk-density
    # curve (RHOB) should be considered suspect and possibly invalid."
    # The number is imported, not written here.
    "drho": GateSpec(
        key="drho", label="density correction (DRHO)", unit="g/cm3", relation=">",
        default=DRHO_SUSPECT, status=STATUS_SOURCED, source=ASQUITH_DRHO,
        basis="asquith#18 p.40, the only numeric log-quality threshold the corpus states",
        bad_by_default=True,
    ),
    # PROVISIONAL. DiffCal itself is sourced; the cutoff is ours.
    "washout": GateSpec(
        key="washout", label="washout (DiffCal = caliper - bit size)", unit="in",
        relation=">", default=1.0, status=STATUS_PROVISIONAL, source=ASQUITH_DIFFCAL,
        basis=OURS_WASHOUT, bad_by_default=True,
    ),
    # PROVISIONAL, with basis. Not bad hole by default - see the module docstring.
    "undergauge": GateSpec(
        key="undergauge", label="undergauge (mudcake / swelling shale / bit worn to gauge)",
        unit="in", relation="<", default=-0.25, status=STATUS_PROVISIONAL,
        source=ASQUITH_HOLE_DIAM, basis=OURS_UNDERGAUGE, bad_by_default=False,
    ),
    # PROVISIONAL. beg#40 names the quantity - "the rate of change of the
    # caliper" - and no source states a cutoff or a window.
    "rugosity": GateSpec(
        key="rugosity", label="rugosity |d(CAL)/dz|", unit="in/ft", relation=">",
        default=0.5, status=STATUS_PROVISIONAL, source=BEG_BADHOLE,
        basis=OURS_RUGOSITY, bad_by_default=True,
    ),
}

# PROVISIONAL, ours: tool-catalog.md:108 says the gradient is taken "over 2 ft".
RUGOSITY_WINDOW_FT = 2.0

# CALLER. No default bit size, ever. RRC log-header item D supplies it
# (`tools/header.py`); absent it, the DiffCal half refuses and says so.
BIT_SIZE_MIN_IN = 3.0
BIT_SIZE_MAX_IN = 36.0   # tools/raster.py:1144, the item-D plausibility band

# A caliper reading outside this band is not a hole, it is an unscrubbed
# sentinel or a units error. asquith#8: "Common borehole sizes normally vary from
# 7-7/8 in. to 12 in."; widened to the item-D band so a 26 in surface hole and a
# 3-3/4 in slimhole both survive.
CALIPER_MIN_IN = BIT_SIZE_MIN_IN
CALIPER_MAX_IN = BIT_SIZE_MAX_IN
# A density correction outside this band is likewise not a reading. The tool
# corrects for mudcake; a correction of a whole g/cm3 is a sentinel.
DRHO_ABS_MAX = 1.0

_DEPTH_TOL = 1e-6

METHOD = ("per-depth borehole-condition gates: DRHO (asquith#18), DiffCal washout "
          "and undergauge (asquith#66/#8), caliper rugosity (beg#40)")

# Curve mnemonics tried by `hole_quality_from_las` when the caller names none.
CALIPER_MNEMONICS = ("CALI", "CAL", "CALS", "CALX", "HCAL", "CALD", "CALN")
DRHO_MNEMONICS = ("DRHO", "DRH", "HDRA", "DCOR")


# --- output records --------------------------------------------------------


@dataclass(frozen=True)
class Gate:
    """A gate as applied on one call: its cutoff, its status, its provenance."""

    key: str
    label: str
    status: str            # SOURCED | PROVISIONAL | CALLER
    cutoff: Quantity
    relation: str
    source: str
    basis: str
    bad: bool
    overridden: bool

    @property
    def defensible(self) -> bool:
        """True only where the number itself is published. A house rule is not."""
        return self.status == STATUS_SOURCED


@dataclass(frozen=True)
class GateHit:
    """One gate firing at one depth. `status` is what the operator is owed."""

    gate: str
    status: str
    bad: bool
    observed: float
    cutoff: float
    unit: str
    source: str
    detail: str


@dataclass(frozen=True)
class SampleVerdict:
    depth_ft: float
    verdict: str                              # "good" | "bad" | "unknown"
    hits: tuple[GateHit, ...] = ()
    undetermined: tuple[str, ...] = ()
    caliper_in: float | None = None
    diffcal_in: float | None = None
    rugosity_in_per_ft: float | None = None
    drho: float | None = None
    bit_size_in: float | None = None
    notes: tuple[str, ...] = ()

    @property
    def gates_fired(self) -> tuple[str, ...]:
        return tuple(h.gate for h in self.hits)

    @property
    def sourced_gate_fired(self) -> bool:
        return any(h.status == STATUS_SOURCED for h in self.hits)


@dataclass(frozen=True)
class QualityInterval:
    top_ft: Quantity
    base_ft: Quantity
    thickness_ft: Quantity
    verdict: str
    gates: tuple[str, ...]
    statuses: dict[str, str]
    sourced_gate_fired: bool
    worst: dict[str, Quantity]
    n_samples: int
    undetermined: tuple[str, ...] = ()

    def __repr__(self) -> str:  # keeps test failures readable
        g = ",".join(self.gates) or "-"
        return (f"QualityInterval({self.top_ft.value:g}-{self.base_ft.value:g} ft "
                f"{self.verdict} [{g}])")


@dataclass(frozen=True)
class HoleQuality:
    """Depth-indexed borehole condition. The consumer is a per-depth mask."""

    samples: tuple[SampleVerdict, ...]
    intervals: tuple[QualityInterval, ...]
    gates: dict[str, Gate]
    declined: dict[str, Refusal]
    n_good: int
    n_bad: int
    n_unknown: int
    bad_fraction: Quantity
    evaluated_fraction: Quantity
    method: str = METHOD
    source: str = BEG_BADHOLE
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()
    depth_step_ft: float | None = None

    # -- the contract density_porosity (#26) codes against ------------------

    def verdict_at(self, depth_ft: float, *, tol_ft: float | None = None
                   ) -> SampleVerdict | None:
        """Nearest sample within half the median step. `None` is not "good"."""
        if not self.samples:
            return None
        if tol_ft is None:
            step = self.depth_step_ft or 0.0
            tol_ft = (step / 2.0) if step > 0 else _DEPTH_TOL
        best = min(self.samples, key=lambda s: abs(s.depth_ft - depth_ft))
        return best if abs(best.depth_ft - depth_ft) <= tol_ft + _DEPTH_TOL else None

    def mask(self, *, reject: Sequence[str] = ("bad",)) -> tuple[bool, ...]:
        """One bool per input sample, True = usable. Positionally aligned."""
        bad = set(reject)
        return tuple(s.verdict not in bad for s in self.samples)

    def refusal_at(self, depth_ft: float,
                   statuses: Sequence[str] = (STATUS_SOURCED,)) -> Refusal | None:
        """A ready-made Refusal, but only where a gate of `statuses` fired.

        Default is SOURCED only: a porosity suppressed by a number nobody
        published is a flag on the answer, not a refusal to answer.
        """
        s = self.verdict_at(depth_ft)
        if s is None:
            return None
        wanted = set(statuses)
        hits = [h for h in s.hits if h.status in wanted]
        if not hits:
            return None
        return Refusal(
            reason=(f"bad hole at {s.depth_ft:g} ft: "
                    + "; ".join(h.detail for h in hits)),
            needed=tuple(f"a reading from an interval where the {h.gate} gate is clear"
                         for h in hits),
            source=hits[0].source,
        )

    def bad_intervals(self) -> tuple[QualityInterval, ...]:
        return tuple(i for i in self.intervals if i.verdict == "bad")

    def gate_counts(self) -> dict[str, int]:
        out = {k: 0 for k in self.gates}
        for s in self.samples:
            for h in s.hits:
                out[h.gate] = out.get(h.gate, 0) + 1
        return out


# --- bit-size profile ------------------------------------------------------


@dataclass(frozen=True)
class _BitProfile:
    """Bit size as a function of depth. One section, or an item-D record."""

    sections: tuple[tuple[float | None, float], ...]  # (bottom_ft or None, size_in)
    constant: bool

    def at(self, depth_ft: float) -> float | None:
        if self.constant:
            return self.sections[0][1]
        for bottom, size in self.sections:
            if bottom is not None and depth_ft <= bottom + _DEPTH_TOL:
                return size
        return None


def _as_float(v: Any) -> float | None:
    """Unwrap a Quantity, a bare number, or a numeric string. None otherwise."""
    if v is None:
        return None
    if isinstance(v, Quantity):
        v = v.value
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else None
    if isinstance(v, str):
        try:
            f = float(v.strip())
        except ValueError:
            return None
        return f if math.isfinite(f) else None
    return None


def _bit_profile(bit_size_in: Any) -> _BitProfile | Refusal | None:
    """Build a depth->bit-size profile from item D in any of its shipped shapes."""
    if bit_size_in is None:
        return None

    scalar = _as_float(bit_size_in)
    if scalar is not None:
        if not (BIT_SIZE_MIN_IN <= scalar <= BIT_SIZE_MAX_IN):
            return Refusal(
                reason=(f"bit size {scalar:g} in is outside the {BIT_SIZE_MIN_IN:g}-"
                        f"{BIT_SIZE_MAX_IN:g} in band a bit can occupy; this is a bad "
                        "parse of RRC log-header item D, not a hole"),
                needed=("a bit size from ~P BS, or from the scanned borehole record",),
                source=ASQUITH_HOLE_DIAM,
            )
        return _BitProfile(((None, scalar),), constant=True)

    if isinstance(bit_size_in, (str, bytes)) or not isinstance(bit_size_in, Iterable):
        raise TypeError(
            f"bit_size_in must be a number, a Quantity, or an item-D record, got "
            f"{type(bit_size_in).__name__}; this is a wiring fault at the call site"
        )

    entries = list(bit_size_in)
    if not entries:
        return None
    rows: list[tuple[float | None, float]] = []
    for e in entries:
        if isinstance(e, dict):
            size = _as_float(e.get("size", e.get("bit_size_in")))
            bottom = _as_float(e.get("to", e.get("bottom", e.get("base"))))
        elif isinstance(e, (tuple, list)) and len(e) == 2:
            bottom, size = _as_float(e[0]), _as_float(e[1])
        else:
            size, bottom = _as_float(getattr(e, "size", None)), _as_float(getattr(e, "to", None))
        if size is None:
            continue
        if not (BIT_SIZE_MIN_IN <= size <= BIT_SIZE_MAX_IN):
            return Refusal(
                reason=(f"the borehole record carries a bit size of {size:g} in, outside "
                        f"the {BIT_SIZE_MIN_IN:g}-{BIT_SIZE_MAX_IN:g} in band; a bad OCR "
                        "of item D, not a hole"),
                needed=("a corrected item-D borehole record",),
                source=ASQUITH_HOLE_DIAM,
            )
        rows.append((bottom, size))
    if not rows:
        return None
    if len(rows) == 1:
        return _BitProfile(((None, rows[0][1]),), constant=True)
    if any(b is None for b, _ in rows):
        return Refusal(
            reason=("the borehole record lists more than one bit size but not every "
                    "section states its bottom depth, so which bit was in the hole at "
                    "which depth cannot be resolved. DiffCal against the wrong section "
                    "is wrong everywhere in it"),
            needed=("a section bottom depth for each bit size in RRC item D",),
            source=ASQUITH_HOLE_DIAM,
        )
    rows.sort(key=lambda r: r[0])  # type: ignore[arg-type,return-value]
    return _BitProfile(tuple(rows), constant=False)


# --- rugosity --------------------------------------------------------------


def _rugosity(depths: Sequence[float], cal: Sequence[float | None],
              window_ft: float) -> list[float | None]:
    """Max |dCAL/dz| over every complete `window_ft` window containing each sample.

    Not a centred difference. A washout that opens and closes inside the window
    has equal endpoints and a centred difference of exactly zero; taking the
    maximum over all windows containing the sample catches the up-ramp and the
    down-ramp separately. `beg#40` names the quantity and defines nothing else,
    so this definition is ours and is stated in `specs/25-hole_quality.md`.
    """
    n = len(depths)
    out: list[float | None] = [None] * n
    if n < 2 or window_ft <= 0:
        return out
    tol = max(_DEPTH_TOL, window_ft * 1e-6)
    max_step = window_ft / 2.0
    j = 0
    for i in range(n):
        if cal[i] is None:
            continue
        if j < i:
            j = i
        # widen to the furthest sample still inside the window
        while j + 1 < n and depths[j + 1] - depths[i] <= window_ft + tol:
            j += 1
        span = depths[j] - depths[i]
        if span < window_ft - tol:
            continue                       # window runs off the end of the log
        if cal[j] is None:
            continue
        bad = False
        for k in range(i, j):
            if cal[k] is None or cal[k + 1] is None:
                bad = True
                break
            if depths[k + 1] - depths[k] > max_step + tol:
                bad = True                 # the window spans a logging gap
                break
        if bad:
            continue
        grad = abs(cal[j] - cal[i]) / span  # type: ignore[operator]
        for k in range(i, j + 1):
            prev = out[k]
            out[k] = grad if prev is None else max(prev, grad)
    return out


# --- helpers ---------------------------------------------------------------


def _clean(values: Sequence[Any] | None, n: int, name: str,
           lo: float, hi: float) -> tuple[list[float | None], int]:
    """Coerce one curve to float|None and reject values outside a physical band.

    `null_scrub` (#12) is the supplier and marks nulls with `None`. A value
    outside the band is an unscrubbed sentinel or a units error, so it is treated
    as *not a reading* - undetermined - rather than gated on. A raw -999.25
    caliper would otherwise report a DiffCal of -1007 in and an undergauge flag
    on every null in the file.
    """
    if values is None:
        return [None] * n, 0
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be a sequence of numbers or None, got "
                        f"{type(values).__name__}; a wiring fault at the call site")
    if len(values) != n:
        raise ValueError(
            f"{name} has {len(values)} samples against {n} depths; a curve that is "
            "not depth-aligned would put every verdict at the wrong depth"
        )
    out: list[float | None] = []
    n_out_of_band = 0
    for v in values:
        f = _as_float(v)
        if f is None:
            out.append(None)
        elif lo <= f <= hi:
            out.append(f)
        else:
            out.append(None)
            n_out_of_band += 1
    return out, n_out_of_band


def _fires(spec_relation: str, observed: float, cutoff: float) -> bool:
    return observed > cutoff if spec_relation == ">" else observed < cutoff


def _q(value: float, unit: str, method: str, source: str, **kw: Any) -> Quantity:
    return Quantity(value=value, unit=unit, method=method, source=source, **kw)


# --- the tool --------------------------------------------------------------


def hole_quality(
    depth_ft: Sequence[Any],
    *,
    caliper_in: Sequence[Any] | None = None,
    drho: Sequence[Any] | None = None,
    bit_size_in: Any = None,
    casing_shoe_ft: Any = None,
    washout_diffcal_in: float = GATE_SPECS["washout"].default,
    undergauge_diffcal_in: float = GATE_SPECS["undergauge"].default,
    rugosity_in_per_ft: float = GATE_SPECS["rugosity"].default,
    rugosity_window_ft: float = RUGOSITY_WINDOW_FT,
    drho_suspect: float = DRHO_SUSPECT,
    drho_use_magnitude: bool = False,
    undergauge_is_bad: bool = False,
    depth_unit: str = "ft",
    caliper_unit: str = "in",
) -> HoleQuality | Refusal:
    """Per-depth borehole condition, with the gate that fired named on every flag.

    Four independent gates - DRHO (SOURCED), washout, undergauge and rugosity
    (ours) - each evaluable or not at each sample. A gate that cannot be
    evaluated is *undetermined*, never assumed to pass, so a clean caliper with
    no DRHO curve returns "unknown", not "good".

    Curves are expected post-`null_scrub` (#12): `None` marks a null and nothing
    else does.
    """
    # -- programmer-error guards (raise; these are wiring faults) -----------
    if isinstance(depth_ft, (str, bytes)) or not isinstance(depth_ft, Sequence):
        raise TypeError(f"depth_ft must be a sequence, got {type(depth_ft).__name__}")
    for name, v in (("washout_diffcal_in", washout_diffcal_in),
                    ("undergauge_diffcal_in", undergauge_diffcal_in),
                    ("rugosity_in_per_ft", rugosity_in_per_ft),
                    ("rugosity_window_ft", rugosity_window_ft),
                    ("drho_suspect", drho_suspect)):
        if not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            raise ValueError(f"{name}={v!r} is not a finite number; nothing can be "
                             "compared against it")
    if rugosity_in_per_ft < 0 or rugosity_window_ft <= 0:
        raise ValueError("rugosity cutoff must be >= 0 and the window > 0")

    # -- unit gates (refuse; converting silently is how a factor gets buried)
    if str(depth_unit).strip().lower() not in ("ft", "f", "feet"):
        return Refusal(
            reason=(f"depth is in {depth_unit!r}. The rugosity cutoff is in in/ft and "
                    "the washout cutoff in inches; converting the index silently is how "
                    "a factor of 3.28 gets buried in a per-depth mask"),
            needed=("depth in feet - convert with unit_convert (#11)",),
            source=BEG_BADHOLE,
        )
    if caliper_in is not None and str(caliper_unit).strip().lower() not in ("in", "inch", "inches"):
        return Refusal(
            reason=(f"caliper is in {caliper_unit!r}. DiffCal = caliper - bit size is an "
                    "inch quantity (asquith#66) and the bit size arrives in inches from "
                    "RRC item D; mixing the two is a silent 25.4x error"),
            needed=("a caliper in inches - convert with unit_convert (#11)",),
            source=ASQUITH_DIFFCAL,
        )

    n = len(depth_ft)
    if n == 0:
        return Refusal(
            reason="no depth samples; a per-depth verdict over zero depths is undefined",
            needed=("a depth index from the ~A section",),
            source=BEG_BADHOLE,
        )
    if caliper_in is None and drho is None:
        return Refusal(
            reason=("neither a caliper nor a density-correction curve was supplied. "
                    "beg#40: 'The presence of bad hole is determined by looking at the "
                    "caliper, rugosity, and density curves' - with none of them there is "
                    "no basis for any gate"),
            needed=("a caliper curve (CALI) and/or a density correction curve (DRHO)",),
            source=BEG_BADHOLE,
        )

    depths_raw = [_as_float(d) for d in depth_ft]
    if any(d is None for d in depths_raw):
        return Refusal(
            reason=("the depth index carries nulls. Every gate here is measured against "
                    "depth, so a hole in the index is a hole in the frame, not in a curve"),
            needed=("an index column with no nulls - null_scrub_columns (#12) flags these "
                    "as 'index-null'",),
            source=BEG_BADHOLE,
        )
    depths: list[float] = [float(d) for d in depths_raw]  # type: ignore[arg-type]

    cal, cal_oob = _clean(caliper_in, n, "caliper_in", CALIPER_MIN_IN, CALIPER_MAX_IN)
    dr, drho_oob = _clean(drho, n, "drho", -DRHO_ABS_MAX, DRHO_ABS_MAX)

    flags: list[str] = []
    reversed_index = False
    if n > 1:
        ups = sum(1 for i in range(n - 1) if depths[i + 1] > depths[i])
        downs = sum(1 for i in range(n - 1) if depths[i + 1] < depths[i])
        if ups and downs:
            return Refusal(
                reason=("the depth index is not monotonic; a rugosity window across a fold "
                        "in the index compares two depths that are not 2 ft apart"),
                needed=("a monotonic depth index",),
                source=BEG_BADHOLE,
            )
        if downs and not ups:
            reversed_index = True
            order = list(range(n - 1, -1, -1))
            depths = [depths[i] for i in order]
            cal = [cal[i] for i in order]
            dr = [dr[i] for i in order]
            flags.append("depth-index-descending: the file is indexed bottom-up; it was "
                         "reversed internally and the output is re-reversed to match the "
                         "caller's array order")

    if all(v is None for v in cal) and all(v is None for v in dr):
        return Refusal(
            reason=("every caliper and density-correction sample is null; there is no "
                    "verdict anywhere in this file"),
            needed=("a caliper or DRHO curve with at least one reading",),
            source=BEG_BADHOLE,
        )
    if cal_oob:
        flags.append(f"unscrubbed-sentinel: {cal_oob} caliper sample(s) outside "
                     f"{CALIPER_MIN_IN:g}-{CALIPER_MAX_IN:g} in were treated as not a "
                     "reading, not as a hole. Run null_scrub (#12) first")
    if drho_oob:
        flags.append(f"unscrubbed-sentinel: {drho_oob} DRHO sample(s) outside "
                     f"+/-{DRHO_ABS_MAX:g} g/cm3 were treated as not a reading. Run "
                     "null_scrub (#12) first")

    # -- the applied gate table --------------------------------------------
    overrides = {"washout": washout_diffcal_in, "undergauge": undergauge_diffcal_in,
                 "rugosity": rugosity_in_per_ft, "drho": drho_suspect}
    gates: dict[str, Gate] = {}
    for key, spec in GATE_SPECS.items():
        value = float(overrides[key])
        overridden = not math.isclose(value, spec.default, rel_tol=0.0, abs_tol=0.0)
        status = spec.status
        source = spec.source
        basis = spec.basis
        if overridden and spec.status == STATUS_SOURCED:
            # A gate cannot claim asquith#18's authority for a number Asquith
            # did not write.
            status = STATUS_CALLER
            basis = (f"caller override of the SOURCED {spec.default:g} {spec.unit} at "
                     f"{spec.source}; this cutoff is the caller's, not the corpus's")
            flags.append(f"{key}-cutoff-overridden: {value:g} {spec.unit} replaces the "
                         f"SOURCED {spec.default:g}; the gate now reports as CALLER")
        elif overridden:
            basis = spec.basis + f" - overridden by the caller to {value:g} {spec.unit}"
        bad = spec.bad_by_default
        if key == "undergauge" and undergauge_is_bad:
            bad = True
        gates[key] = Gate(
            key=key, label=spec.label, status=status,
            cutoff=_q(value, spec.unit,
                      f"{spec.label} cutoff [{status}]", source,
                      assumptions={"status": status, "basis": basis,
                                   "relation": spec.relation}),
            relation=spec.relation, source=source, basis=basis, bad=bad,
            overridden=overridden,
        )
    if drho_use_magnitude:
        flags.append("drho-magnitude-test: |DRHO| is being gated, not DRHO. asquith#18 "
                     "says 'exceeds 0.20 g/cm3'; the magnitude test is the caller's rule")

    # -- what each gate can run on -----------------------------------------
    declined: dict[str, Refusal] = {}
    have_cal = any(v is not None for v in cal)
    if caliper_in is None or not have_cal:
        why = ("no caliper curve was supplied" if caliper_in is None
               else "every caliper sample is null")
        for key in ("washout", "undergauge", "rugosity"):
            declined[key] = Refusal(
                reason=f"the {key} gate needs a caliper and {why}",
                needed=("a caliper curve (CALI), post-null_scrub",),
                source=ASQUITH_DIFFCAL if key != "rugosity" else BEG_BADHOLE,
            )
    if drho is None or all(v is None for v in dr):
        declined["drho"] = Refusal(
            reason=("the SOURCED gate could not run: "
                    + ("no DRHO curve was supplied" if drho is None
                       else "every DRHO sample is null")
                    + ". The remaining gates are house rules (tool-catalog.md:112), so "
                      "nothing in this result is defensible as the density log's own "
                      "verdict on itself"),
            needed=("a density-correction curve (DRHO), post-null_scrub",),
            source=ASQUITH_DRHO,
        )

    profile = _bit_profile(bit_size_in)
    if isinstance(profile, Refusal):
        for key in ("washout", "undergauge"):
            declined.setdefault(key, profile)
        profile = None
    elif profile is None and "washout" not in declined:
        no_bit = Refusal(
            reason=("no bit size. DiffCal is 'the caliper value minus the bit size' "
                    "(asquith#66) and nothing here supplies the bit size, so the washout "
                    "and undergauge gates are refused rather than run against an assumed "
                    "hole. The rugosity gate needs no bit size and still ran"),
            needed=("RRC log-header item D (bit size) - ~P BS, or the scanned "
                    "borehole-record table",),
            source=ASQUITH_DIFFCAL,
        )
        declined["washout"] = no_bit
        declined["undergauge"] = no_bit

    rug: list[float | None] = [None] * n
    if "rugosity" not in declined:
        rug = _rugosity(depths, cal, rugosity_window_ft)
        if all(v is None for v in rug):
            declined["rugosity"] = Refusal(
                reason=(f"no complete {rugosity_window_ft:g} ft window free of nulls and "
                        "logging gaps exists in this log, so the rate of change of the "
                        "caliper (beg#40) cannot be measured anywhere"),
                needed=(f"at least {rugosity_window_ft:g} ft of continuous caliper",),
                source=BEG_BADHOLE,
            )

    shoe = _as_float(casing_shoe_ft)

    # -- per-sample evaluation ---------------------------------------------
    # Every gate is requested at every sample. A gate that declined wholesale is
    # *undetermined everywhere*, not dropped from the verdict: spec 25, Procedure
    # ("a gate that cannot be evaluated at a sample is undetermined there - never
    # assumed to pass") and the Verdict section ("a sample with an in-gauge
    # caliper and no DRHO curve has not been shown to be good hole; it has been
    # shown not to be a washout, which is a weaker claim and the difference
    # matters to #26"). Dropping a declined gate would return "good" for a hole
    # the SOURCED gate never looked at.
    requested = tuple(GATE_SPECS)
    evaluable = tuple(k for k in GATE_SPECS if k not in declined)
    declined_note = ("gate(s) " + ", ".join(sorted(declined)) + " declined for the whole "
                     "log, so they are undetermined at every sample and no sample here can "
                     "be shown good on them") if declined else None
    samples: list[SampleVerdict] = []
    n_good = n_bad = n_unknown = 0
    for i in range(n):
        z = depths[i]
        notes: list[str] = []
        hits: list[GateHit] = []
        undet: list[str] = [k for k in GATE_SPECS if k in declined]
        if declined_note:
            notes.append(declined_note)

        cased = shoe is not None and z <= shoe + _DEPTH_TOL
        if cased:
            notes.append(f"inside-casing: {z:g} ft is at or above the casing shoe at "
                         f"{shoe:g} ft (RRC item E), so the caliper is reading casing ID, "
                         "not the open hole")

        bit = profile.at(z) if profile is not None else None
        c = cal[i]
        diffcal = None if (c is None or bit is None) else c - bit

        # gate: drho (SOURCED)
        if "drho" in evaluable:
            g = gates["drho"]
            v = dr[i]
            if v is None:
                undet.append("drho")
            else:
                observed = abs(v) if drho_use_magnitude else v
                if _fires(g.relation, observed, g.cutoff.value):
                    hits.append(GateHit(
                        gate="drho", status=g.status, bad=g.bad, observed=observed,
                        cutoff=g.cutoff.value, unit=g.cutoff.unit, source=g.source,
                        detail=(f"DRHO {observed:.5g} g/cm3 exceeds "
                                f"{g.cutoff.value:g} g/cm3, so the bulk density here is "
                                f"suspect and possibly invalid [{g.status}, {g.source}]"),
                    ))

        # gates: washout / undergauge (DiffCal)
        for key in ("washout", "undergauge"):
            if key not in evaluable:
                continue
            g = gates[key]
            if cased or diffcal is None:
                undet.append(key)
                continue
            if _fires(g.relation, diffcal, g.cutoff.value):
                if key == "washout":
                    detail = (f"DiffCal {diffcal:+.5g} in exceeds {g.cutoff.value:+g} in "
                              f"(caliper {c:.5g} in, bit {bit:g} in): hole enlarged by "
                              f"washout or collapse [{g.status}, {g.basis}]")
                else:
                    detail = (f"DiffCal {diffcal:+.5g} in is below {g.cutoff.value:+g} in "
                              f"(caliper {c:.5g} in, bit {bit:g} in): hole undergauge - "
                              "mudcake on a porous and permeable formation, swelling "
                              f"shale, or a bit worn to gauge [{g.status}, {g.basis}]")
                hits.append(GateHit(
                    gate=key, status=g.status, bad=g.bad, observed=diffcal,
                    cutoff=g.cutoff.value, unit=g.cutoff.unit, source=g.source,
                    detail=detail,
                ))
                if key == "undergauge":
                    notes.append("undergauge is evidence of permeability (asquith#37), "
                                 "and thick mudcake degrades pad contact (asquith#32); "
                                 "the DRHO gate is what says whether the density survived")

        # gate: rugosity
        if "rugosity" in evaluable:
            g = gates["rugosity"]
            r = rug[i]
            if cased or r is None:
                undet.append("rugosity")
            elif _fires(g.relation, r, g.cutoff.value):
                hits.append(GateHit(
                    gate="rugosity", status=g.status, bad=g.bad, observed=r,
                    cutoff=g.cutoff.value, unit=g.cutoff.unit, source=g.source,
                    detail=(f"caliper changing at {r:.5g} in/ft over "
                            f"{rugosity_window_ft:g} ft, above {g.cutoff.value:g} in/ft: "
                            "the sidewall tool is more prone to be incorrect when the "
                            "hole size is changing than when it is large but constant "
                            f"[{g.status}, {g.basis}]"),
                ))

        if any(h.bad for h in hits):
            verdict = "bad"
            n_bad += 1
        elif undet:
            verdict = "unknown"
            n_unknown += 1
        else:
            verdict = "good"
            n_good += 1

        # keep `undetermined` in gate-table order whether a key got there from a
        # whole-log decline or from this sample, so the tuple is assertable
        undet = [k for k in GATE_SPECS if k in set(undet)]
        samples.append(SampleVerdict(
            depth_ft=z, verdict=verdict, hits=tuple(hits), undetermined=tuple(undet),
            caliper_in=c, diffcal_in=diffcal, rugosity_in_per_ft=rug[i], drho=dr[i],
            bit_size_in=bit, notes=tuple(notes),
        ))

    if not evaluable:
        return Refusal(
            reason=("every gate declined: " + "; ".join(
                f"{k}: {r.reason}" for k, r in declined.items())),
            needed=tuple(sorted({x for r in declined.values() for x in r.needed})),
            source=BEG_BADHOLE,
        )

    step = _median_step(depths)
    intervals = _merge(samples, gates, step)

    if reversed_index:
        samples.reverse()

    evaluated = n_good + n_bad
    denom = max(1, evaluated)
    src_fired = any(s.sourced_gate_fired for s in samples)
    if not src_fired and n_bad and "drho" in declined:
        flags.append("house-rules-only: every bad-hole call in this result rests on a "
                     "PROVISIONAL cutoff of ours. No SOURCED gate ran (tool-catalog.md:112)")

    return HoleQuality(
        samples=tuple(samples),
        intervals=intervals,
        gates=gates,
        declined=declined,
        n_good=n_good, n_bad=n_bad, n_unknown=n_unknown,
        bad_fraction=_q(n_bad / denom, "v/v",
                        "bad samples / samples where every requested gate was evaluable",
                        BEG_BADHOLE,
                        inputs={"n_bad": n_bad, "n_evaluated": evaluated},
                        flags=("a fraction of evaluated samples, not of the well; it mixes "
                               "SOURCED and PROVISIONAL gates. confidence_score (#71) is "
                               "where a score belongs",)),
        evaluated_fraction=_q(evaluated / n, "v/v",
                              "samples with every requested gate evaluable / all samples",
                              BEG_BADHOLE,
                              inputs={"n_evaluated": evaluated, "n_samples": n}),
        inputs={"n_samples": n,
                "depth_range_ft": (min(depths), max(depths)),
                "has_caliper": have_cal, "has_drho": any(v is not None for v in dr),
                "bit_size_in": (None if profile is None
                                else [s[1] for s in profile.sections]),
                "casing_shoe_ft": shoe},
        assumptions={"gate_status": {k: g.status for k, g in gates.items()},
                     "cutoffs": {k: g.cutoff.value for k, g in gates.items()},
                     "rugosity_window_ft": rugosity_window_ft,
                     "rugosity_definition": ("max |dCAL/dz| over every complete window "
                                             "containing the sample; ours, spec 25"),
                     "drho_use_magnitude": drho_use_magnitude,
                     "undergauge_is_bad": gates["undergauge"].bad,
                     "declined_gates": sorted(declined)},
        flags=tuple(flags),
        depth_step_ft=step,
    )


def _median_step(depths: Sequence[float]) -> float | None:
    if len(depths) < 2:
        return None
    steps = sorted(abs(depths[i + 1] - depths[i]) for i in range(len(depths) - 1))
    return steps[len(steps) // 2]


def _merge(samples: Sequence[SampleVerdict], gates: dict[str, Gate],
           step: float | None) -> tuple[QualityInterval, ...]:
    """Runs of identical (verdict, fired-gate set).

    Merged on the gate set and not on the verdict alone, because
    `tool-catalog.md:112` requires the output to say *which* gate fired; a run
    that silently mixed a SOURCED DRHO call with a PROVISIONAL caliper call would
    lose exactly the distinction the tool exists to preserve.
    """
    out: list[QualityInterval] = []
    if not samples:
        return ()
    run: list[SampleVerdict] = [samples[0]]

    def key(s: SampleVerdict) -> tuple[str, tuple[str, ...]]:
        return (s.verdict, tuple(sorted(s.gates_fired)))

    def flush(run: list[SampleVerdict]) -> None:
        top, base = run[0].depth_ft, run[-1].depth_ft
        lo, hi = min(top, base), max(top, base)
        fired = tuple(sorted({h.gate for s in run for h in s.hits}))
        worst: dict[str, Quantity] = {}
        for g in fired:
            spec = GATE_SPECS[g]
            vals = [h.observed for s in run for h in s.hits if h.gate == g]
            extreme = max(vals) if spec.relation == ">" else min(vals)
            worst[g] = _q(extreme, spec.unit,
                          f"most extreme {g} reading in the interval [{gates[g].status}]",
                          gates[g].source,
                          inputs={"cutoff": gates[g].cutoff.value,
                                  "n_samples_fired": len(vals)})
        undet = tuple(sorted({u for s in run for u in s.undetermined}))
        out.append(QualityInterval(
            top_ft=_q(lo, "ft", "top of a run of identical borehole verdict", BEG_BADHOLE),
            base_ft=_q(hi, "ft", "base of a run of identical borehole verdict", BEG_BADHOLE),
            thickness_ft=_q(hi - lo, "ft",
                            "base - top; sample-to-sample, not bed boundaries", BEG_BADHOLE,
                            inputs={"n_samples": len(run), "depth_step_ft": step}),
            verdict=run[0].verdict,
            gates=fired,
            statuses={g: gates[g].status for g in fired},
            sourced_gate_fired=any(gates[g].status == STATUS_SOURCED for g in fired),
            worst=worst,
            n_samples=len(run),
            undetermined=undet,
        ))

    for s in samples[1:]:
        if key(s) == key(run[-1]):
            run.append(s)
        else:
            flush(run)
            run = [s]
    flush(run)
    return tuple(out)


# --- LAS adapter -----------------------------------------------------------


def _item_d_mnemonics() -> tuple[str, ...]:
    """Item D's bit-size mnemonics, from `tools/header.py`. Never copied."""
    item = RRC_HEADER_ITEMS.get("D") if RRC_HEADER_ITEMS else None
    if item is not None:
        for f in getattr(item, "fields", ()):
            if getattr(f, "name", "") == "bit_size_in":
                return tuple(getattr(f, "mnemonics", ()) or ())
    return ("BS", "BIT", "BITSIZE", "HSIZ")


def _item_e_depth_mnemonics() -> tuple[str, ...]:
    item = RRC_HEADER_ITEMS.get("E") if RRC_HEADER_ITEMS else None
    if item is not None:
        for f in getattr(item, "fields", ()):
            if getattr(f, "name", "") == "casing_depth_ft":
                return tuple(getattr(f, "mnemonics", ()) or ())
    return ("CSGD", "CSGL", "CASINGD")


_LAS_LINE = re.compile(r"^\s*([^.\s]+)\s*\.\s*(\S*)\s*(.*?)\s*:\s*(.*)$")


def _param(las_file: Any, wanted: Sequence[str]) -> tuple[float | None, bool]:
    """First finite value among `wanted` in ~P then ~W. Returns (value, recovered).

    `recovered` is True when the value had to be read out of
    `LasFile.unknown_sections`. On both real fixtures `las_parse` (#1) files the
    `~Params` section there rather than under `~P`, which leaves RRC item D - the
    bit size - invisible to `header_extract` (#4) and to this tool. Rather than
    silently declining DiffCal on every LAS file in the corpus, the raw `~P`
    lines are read here and the result is flagged so nobody mistakes a fallback
    for a parse. Remove this when las_parse recognises `~Params`.
    """
    lines = tuple(getattr(las_file, "parameters", ())) + tuple(getattr(las_file, "well", ()))
    for name in wanted:
        for line in lines:
            if str(getattr(line, "mnemonic", "")).strip().upper() == name.upper():
                v = _as_float(getattr(line, "value", None))
                if v is not None:
                    return v, False
    unknown = getattr(las_file, "unknown_sections", None) or {}
    for key, raw in unknown.items():
        if not str(key).strip().upper().startswith("P"):
            continue
        for name in wanted:
            for text in raw:
                m = _LAS_LINE.match(str(text))
                if m and m.group(1).strip().upper() == name.upper():
                    v = _as_float(m.group(3))
                    if v is not None:
                        return v, True
    return None, False


def _column(las_file: Any, scrubbed: Any, mnemonics: Sequence[str],
            explicit: str | None) -> tuple[Sequence[Any] | None, str | None]:
    names = [m.upper() for m in getattr(las_file, "mnemonics", ())]
    cols = getattr(scrubbed, "columns", None) or getattr(las_file, "columns", ())
    order = [explicit.upper()] if explicit else list(mnemonics)
    for want in order:
        if want in names:
            i = names.index(want)
            if i < len(cols):
                return cols[i], want
    return None, None


def hole_quality_from_las(las_file: Any, *, header: Any = None,
                          bit_size_in: Any = None, casing_shoe_ft: Any = None,
                          caliper_mnemonic: str | None = None,
                          drho_mnemonic: str | None = None,
                          scrubbed: Any = None, **kw: Any) -> HoleQuality | Refusal:
    """`hole_quality` over a parsed LAS file, nulls scrubbed on the way in.

    Bit size and casing shoe come from RRC log-header items D and E - an
    explicit argument first, then a `header_extract` (#4) result, then the LAS
    `~P` mnemonics item D itself declares. Nothing is assumed: with no bit size
    anywhere the DiffCal gates refuse and the rugosity gate still runs.
    """
    if isinstance(las_file, Refusal):
        return las_file
    if scrubbed is None:
        from .curves import null_scrub_las  # local: avoids a cycle at import time
        scrubbed = null_scrub_las(las_file)
        if isinstance(scrubbed, Refusal):
            return scrubbed

    cols = getattr(scrubbed, "columns", None) or getattr(las_file, "columns", ())
    if not cols:
        return Refusal(reason="the LAS file carries no ~A data columns",
                       needed=("a populated ~A section",), source=BEG_BADHOLE)
    depth = cols[0]
    cal, cal_name = _column(las_file, scrubbed, CALIPER_MNEMONICS, caliper_mnemonic)
    dr, dr_name = _column(las_file, scrubbed, DRHO_MNEMONICS, drho_mnemonic)

    if bit_size_in is None and header is not None:
        getter = getattr(header, "value", None)
        bit_size_in = getter("bit_size_in") if callable(getter) else None
    recovered = False
    if bit_size_in is None:
        bit_size_in, recovered = _param(las_file, _item_d_mnemonics())
    if casing_shoe_ft is None and header is not None:
        getter = getattr(header, "value", None)
        casing_shoe_ft = getter("casing_depth_ft") if callable(getter) else None
    if casing_shoe_ft is None:
        # CSGL (logger) before CSGD (driller): the logger's shoe is the one the
        # caliper actually passed.
        ordered = sorted(_item_e_depth_mnemonics(),
                         key=lambda m: (m.upper() != "CSGL", m.upper() != "CSGD"))
        casing_shoe_ft, rec_e = _param(las_file, ordered)
        recovered = recovered or rec_e

    depth_unit = kw.pop("depth_unit", None)
    if depth_unit is None:
        curves = getattr(las_file, "curves", ())
        depth_unit = (str(getattr(curves[0], "unit", "ft")) or "ft") if curves else "ft"
    caliper_unit = kw.pop("caliper_unit", None)
    if caliper_unit is None and cal_name:
        curves = getattr(las_file, "curves", ())
        for c in curves:
            if str(getattr(c, "mnemonic", "")).upper() == cal_name:
                caliper_unit = str(getattr(c, "unit", "in")) or "in"
                break
    r = hole_quality(depth, caliper_in=cal, drho=dr, bit_size_in=bit_size_in,
                     casing_shoe_ft=casing_shoe_ft,
                     depth_unit=depth_unit or "ft", caliper_unit=caliper_unit or "in", **kw)
    if isinstance(r, HoleQuality):
        r.inputs["caliper_mnemonic"] = cal_name
        r.inputs["drho_mnemonic"] = dr_name
        r.inputs["source_file"] = getattr(las_file, "path", None)
        if recovered:
            object.__setattr__(r, "flags", r.flags + (
                "item-D-recovered-from-unknown-section: las_parse (#1) filed the ~Params "
                "section under unknown_sections, so the bit size and casing shoe were read "
                "from the raw ~P lines here. header_extract (#4) reports items D and E "
                "missing on the same file. Report to group A",))
    return r
