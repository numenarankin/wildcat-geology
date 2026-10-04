"""Bypassed pay: `bypassed_pay_scan` (#110).

Destination module `tools/recompletion.py` (§17). Spec:
`specs/110-bypassed_pay_scan.md`.

The catalog entry asks for "relaxed cutoffs" and its own correction says why that
cannot be built: *"those are base cutoffs, not relaxed ones; 'relaxed' is
unsourceable as written"*. `beg#40` publishes a **net-pay** triple - Vsh 50%,
phi 4%, Sw 60% - and nothing in the corpus relaxes it. A second document,
`petrophysical-evaluation-chapter4#2`, publishes 50% / 10% / 70% for its own
field. Two internally-correct sets that disagree is the proof these are
parameters, so:

  * cutoffs are a **required argument** with no default anywhere in this module;
  * both published sets live in `PUBLISHED_CUTOFFS` with their anchors, so a
    caller can name one explicitly and the result records which;
  * relaxation is the **caller's** (tool-catalog.md marks "cutoff relaxation
    factor" CALLER). Ask for a relaxed scan without declaring the relaxation and
    this tool refuses rather than inventing one.

The other half - "never perforated" - needs the perforation record as an input,
because without it the tool can report *pay* and not *bypassed*. That comparison
is ours, not published (the catalog records that `completion_history_compare`
#111 has "no comparison rule, no depth tolerance, no pay cutoff in corpus"); the
+/-2 ft depth-registry tolerance it runs at is PROVISIONAL with a basis in
`asquith#64`, and every result says so.

Hole quality is consumed, not reimplemented: pass `hole_quality` (#25) itself, or
its per-sample verdicts. A sample inside a washout is not evidence of pay -
`beg#40` p. C.26 is explicit that bad hole makes the density "read very high
porosities", which is the direction that manufactures pay that is not there."""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence
from .result import Quantity, Range, Refusal
from typing import Any, Sequence
from .geometry import normalize_reference
from datetime import date, datetime
from typing import Any, Iterable, Mapping, Sequence
from .geometry import Crs, WellLocation, offset_geometry
from .dst import dst_recovery_volume

# --- anchors ---------------------------------------------------------------

BEG_CUTOFFS = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#40"
CH4_CUTOFFS = "01-curve-reading/petrophysical-evaluation-chapter4#2"
ASQUITH_REGISTRY = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#64"
CATALOG_THRESHOLDS = 'tool-catalog.md, "Thresholds the corpus does not supply"'
CATALOG_110 = "tool-catalog.md, section 17, bypassed_pay_scan [#110]"

# The catalog's own finding on this tool, quoted so a refusal can hand the
# operator the sentence rather than a paraphrase of it.
RELAXED_UNSOURCEABLE = (
    "tool-catalog.md #110: \"those are base cutoffs, not relaxed ones; 'relaxed' "
    "is unsourceable as written\""
)

STATUS_PUBLISHED = "PUBLISHED"
STATUS_CALLER = "CALLER"
STATUS_PROVISIONAL = "PROVISIONAL"

METHOD = (
    "bypassed-pay scan: per-sample Vsh/phi/Sw net-pay cutoffs (beg#40 'Summations' "
    "and 'Cutoffs', pp. C.29-C.31) grouped into contiguous intervals, minus the "
    "perforated intervals at a depth-registry tolerance (asquith#64)"
)

# --- the two published cutoff sets -----------------------------------------


@dataclass(frozen=True)
class CutoffSet:
    """A published (or caller-stated) net-pay cutoff triple, with its provenance.

    `porosity_kind` is what the *source* states the porosity cutoff is measured
    on. Boonsville does not say: its analysis computes both PHIT and
    PHIE = PHIT(1 - VSH) (Eq. C-13) and then refers only to "a porosity cutoff",
    while its 4% came off a core porosity/permeability crossplot. Chapter 4 says
    PHIE outright. Recording "unstated" is the honest answer, not a guess.
    """

    key: str
    label: str
    vsh_max: float
    phi_min: float
    sw_max: float
    porosity_kind: str
    source: str
    field_note: str
    rationale: str

    @property
    def status(self) -> str:
        return STATUS_PUBLISHED if self.key in PUBLISHED_CUTOFFS else STATUS_CALLER


# beg#40 p. C.31: "A value of 50 percent was chosen for the shale cutoff. ... From
# the crossplots, this value corresponds to a porosity of 4 percent for both the E
# and the E2 facies. A value of 4 percent was therefore chosen for the porosity
# cutoff. A water-saturation cutoff of 60 percent was also used in the net pay
# summation calculations."
#
# petrophysical-evaluation-chapter4#2 sec. 4.3.7 p. 54: "Based on the log
# interpretation and DST, as well as the previous study results, the following
# Cutoffs can be adopted: Vsh = 50.0%, PHIE = 10.0%, Sw = 70.0%."
#
# Both are here so a caller can name one explicitly. Neither is a default: no
# function in this module supplies a cutoff the caller did not ask for.
from .pay import PUBLISHED_CUTOFF_SETS as _PAY_SETS

PUBLISHED_CUTOFFS: dict[str, CutoffSet] = {
    "boonsville": CutoffSet(
        key="boonsville",
        label="Boonsville / Bend Conglomerate net-pay cutoffs (BEG-GRI SGR)",
        # Numbers, anchor and porosity basis read from #39's table, not
        # restated. Two copies of one published triple is how the Fig. 7-9
        # transcription error survived this build - each looked corroborated
        # by the other. The richer fields below are this tool's own.
        vsh_max=_PAY_SETS["boonsville_bend_conglomerate"].vsh_max,
        phi_min=_PAY_SETS["boonsville_bend_conglomerate"].phi_min,
        sw_max=_PAY_SETS["boonsville_bend_conglomerate"].sw_max,
        porosity_kind=_PAY_SETS["boonsville_bend_conglomerate"].porosity_basis,
        source=_PAY_SETS["boonsville_bend_conglomerate"].source,
        field_note=("field-local to the Bend Conglomerate, Fort Worth Basin; "
                    "applying it elsewhere is the caller's extrapolation"),
        rationale=("the 4% porosity cutoff is derived, not adopted: core "
                   "porosity/permeability crossplots put the producible E and E2 "
                   "facies down to about 0.05 md, which corresponds to 4% porosity. "
                   "The 50% shale cutoff exists 'to remove any shaly sections that "
                   "may have too high a porosity calculation due to bad-hole "
                   "conditions'"),
    ),
    "sharaf": CutoffSet(
        key="sharaf",
        label="Sharaf-1 reservoir/pay cutoffs (Petrophysical Evaluation, ch. 4)",
        vsh_max=_PAY_SETS["sharaf_1_abu_gabra"].vsh_max,
        phi_min=_PAY_SETS["sharaf_1_abu_gabra"].phi_min,
        sw_max=_PAY_SETS["sharaf_1_abu_gabra"].sw_max,
        porosity_kind=_PAY_SETS["sharaf_1_abu_gabra"].porosity_basis,
        source=_PAY_SETS["sharaf_1_abu_gabra"].source,
        field_note=("field-local to the Sharaf-1 study wells (Abu Gabra); applying "
                    "it elsewhere is the caller's extrapolation"),
        rationale=("adopted, not derived: 'Based on the log interpretation and DST, "
                   "as well as the previous study results, the following Cutoffs can "
                   "be adopted'. No crossplot or permeability basis is given"),
    ),
}

# Depth-registry allowance on perforation membership. tool-catalog.md, "Thresholds
# the corpus does not supply", marks this PROVISIONAL *with a basis*: asquith#64
# p. 170 states a log suite "generally requires more than one logging 'run' out of
# the borehole, [so] some logs differ slightly in depth-registry of beds". The
# tolerance absorbs that, so it is set by log mechanics rather than by taste. Same
# number, same reason, as PERF_IN_ZONE_TOLERANCE_FT in tools/perforation.py.
PERF_IN_ZONE_TOLERANCE_FT = 2.0

# A run of passing samples is broken by a spacing wider than this multiple of the
# slab thickness. Mechanical de-aliasing of a gap in the index - it keeps an
# interval from being reported across 100 ft of missing data - not a
# petrophysical threshold. Overridable; every split is flagged.
GAP_BREAK_FACTOR = 1.5

# Anything at or beyond this magnitude is an unscrubbed sentinel (-999.25, -9999,
# 9999), not a reading. Deliberately clear of the 0-100 band a percent-scaled
# curve occupies, so the two checks cannot mask each other.
SENTINEL_ABS = 900.0
# A fraction above this cannot be v/v. Vsh and porosity are hard-capped; Archie
# can legitimately return Sw > 1 in a wet or badly-parameterised zone, so Sw is
# judged on its median instead of its maximum.
FRACTION_ABS_MAX = 1.5

EPS = 1e-9

# Mnemonics `bypassed_pay_scan_from_las` will accept as an already-interpreted
# curve. DPHI/NPHI/SPHI are single-tool porosities, not an interpreted PHIE/PHIT:
# they still need a matrix, a gas correction and a shale correction before a
# 4%-or-10% cutoff means anything, so they are named in the refusal rather than
# silently used.
VSH_MNEMONICS = ("VSH", "VSHL", "VSHG", "VSHS", "VCL", "VWCL", "VCLAY")
PHI_MNEMONICS = ("PHIE", "PHIT", "PHI", "PHIA", "POR", "PORE", "PIGN")
SW_MNEMONICS = ("SW", "SWE", "SWT", "SWA", "SUWI", "SWARCH")
RAW_POROSITY_MNEMONICS = ("DPHI", "NPHI", "SPHI", "PHID", "PHIN", "PHIS", "CNC")


# --- caller-declared relaxation --------------------------------------------


@dataclass(frozen=True)
class Relaxation:
    """A relaxation of the cutoffs, declared by the caller and attributed.

    Applied as `value * factor + delta` per cutoff. There is no default and no
    "standard" relaxation: tool-catalog.md's threshold table marks the cutoff
    relaxation factor **CALLER**, and the corpus publishes base cutoffs only.
    `stated_by` is required so the result can say whose judgement it was.
    """

    stated_by: str
    vsh_max_factor: float = 1.0
    vsh_max_delta: float = 0.0
    phi_min_factor: float = 1.0
    phi_min_delta: float = 0.0
    sw_max_factor: float = 1.0
    sw_max_delta: float = 0.0
    note: str = ""

    def __post_init__(self) -> None:
        if not str(self.stated_by).strip():
            raise ValueError(
                "a Relaxation must name who declared it; an unattributed relaxation "
                "is exactly the unsourceable number this tool exists to refuse")
        for name in ("vsh_max_factor", "phi_min_factor", "sw_max_factor",
                     "vsh_max_delta", "phi_min_delta", "sw_max_delta"):
            v = getattr(self, name)
            if not isinstance(v, (int, float)) or not math.isfinite(float(v)):
                raise ValueError(f"{name}={v!r} is not a finite number")

    @property
    def is_noop(self) -> bool:
        return (self.vsh_max_factor == 1.0 and self.vsh_max_delta == 0.0
                and self.phi_min_factor == 1.0 and self.phi_min_delta == 0.0
                and self.sw_max_factor == 1.0 and self.sw_max_delta == 0.0)

    def describe(self) -> str:
        parts = []
        if self.vsh_max_factor != 1.0 or self.vsh_max_delta != 0.0:
            parts.append(f"Vsh_max*{self.vsh_max_factor:g}{self.vsh_max_delta:+g}")
        if self.phi_min_factor != 1.0 or self.phi_min_delta != 0.0:
            parts.append(f"phi_min*{self.phi_min_factor:g}{self.phi_min_delta:+g}")
        if self.sw_max_factor != 1.0 or self.sw_max_delta != 0.0:
            parts.append(f"Sw_max*{self.sw_max_factor:g}{self.sw_max_delta:+g}")
        return ", ".join(parts) or "no-op"


@dataclass(frozen=True)
class AppliedCutoffs:
    """The three cutoffs as actually applied, each with status and anchor."""

    vsh_max: Quantity
    phi_min: Quantity
    sw_max: Quantity
    provenance: str          # published | caller | published+caller-relaxation
    base: CutoffSet
    relaxation: Relaxation | None = None

    @property
    def triple(self) -> tuple[float, float, float]:
        return (self.vsh_max.value, self.phi_min.value, self.sw_max.value)

    @property
    def published(self) -> bool:
        return self.provenance == "published"


# --- output records --------------------------------------------------------


@dataclass(frozen=True)
class Interval:
    """One depth interval and its summations, in the shape of the source's tables.

    `kind`: pay | bypassed | thin | sliver.
    `classification` (pay intervals only): bypassed | partly_perforated | perforated.
    """

    kind: str
    top_ft: Quantity
    base_ft: Quantity
    thickness_ft: Quantity
    n_samples: int
    classification: str = ""
    perforated_ft: Quantity | None = None
    unperforated_ft: Quantity | None = None
    mean_vsh: Quantity | None = None
    mean_phi: Quantity | None = None
    mean_sw: Quantity | None = None
    phi_h_ft: Quantity | None = None
    phi_so_h_ft: Quantity | None = None
    flags: tuple[str, ...] = ()

    def __repr__(self) -> str:  # keeps test failures readable
        tail = f" {self.classification}" if self.classification else ""
        return (f"Interval({self.kind} {self.top_ft.value:g}-{self.base_ft.value:g} ft, "
                f"{self.thickness_ft.value:g} ft{tail})")


@dataclass(frozen=True)
class SampleTest:
    """One sample against the three cutoffs. `failed` names which fired."""

    depth_ft: float
    verdict: str                    # pass | fail | null | bad-hole
    failed: tuple[str, ...] = ()
    vsh: float | None = None
    phi: float | None = None
    sw: float | None = None


@dataclass(frozen=True)
class BypassedPayScan:
    """The scan. Every number is a Quantity; nothing here is a bare float."""

    bypassed: tuple[Interval, ...]
    pay_intervals: tuple[Interval, ...]
    thin_intervals: tuple[Interval, ...]
    dropped_slivers: tuple[Interval, ...]
    total_bypassed_ft: Quantity
    total_pay_ft: Quantity
    bypassed_fraction: Quantity
    total_phi_h_ft: Quantity
    total_phi_so_h_ft: Quantity
    cutoffs: AppliedCutoffs
    tolerance_ft: Quantity
    min_thickness_ft: Quantity
    samples: tuple[SampleTest, ...]
    n_samples: int
    n_pass: int
    n_fail: int
    n_null: int
    n_bad_hole: int
    method: str = METHOD
    source: str = BEG_CUTOFFS
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    def __repr__(self) -> str:
        return (f"BypassedPayScan({len(self.bypassed)} bypassed, "
                f"{self.total_bypassed_ft.value:g} ft of "
                f"{self.total_pay_ft.value:g} ft pay)")


# --- helpers ---------------------------------------------------------------


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _median(values: Sequence[float]) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        raise ValueError("median of an empty sequence")
    mid = n // 2
    return s[mid] if n % 2 else 0.5 * (s[mid - 1] + s[mid])


def _q(value: float, unit: str, method: str, source: str, **kw: Any) -> Quantity:
    return Quantity(value=value, unit=unit, method=method, source=source, **kw)


def _merge(intervals: Iterable[Sequence[float]], name: str) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for item in intervals:
        if len(tuple(item)) != 2:
            raise ValueError(f"{name} takes (top, base) pairs; got {item!r}")
        top, base = (float(x) for x in item)
        if top > base:
            raise ValueError(
                f"{name} interval ({top:g}, {base:g}) has its top below its base; "
                "depth increases downward")
        pairs.append((top, base))
    pairs.sort()
    merged: list[tuple[float, float]] = []
    for top, base in pairs:
        if merged and top <= merged[-1][1] + EPS:
            merged[-1] = (merged[-1][0], max(merged[-1][1], base))
        else:
            merged.append((top, base))
    return merged


def _overlap_ft(a: tuple[float, float], intervals: Sequence[tuple[float, float]]) -> float:
    return sum(max(0.0, min(a[1], base) - max(a[0], top)) for top, base in intervals)


def _subtract(a: tuple[float, float],
              intervals: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    """`a` minus a merged, sorted set of intervals. The bypassed remainder."""
    pieces: list[tuple[float, float]] = []
    cursor = a[0]
    for top, base in intervals:
        if base <= cursor + EPS:
            continue
        if top >= a[1] - EPS:
            break
        if top > cursor + EPS:
            pieces.append((cursor, min(top, a[1])))
        cursor = max(cursor, base)
        if cursor >= a[1] - EPS:
            break
    if cursor < a[1] - EPS:
        pieces.append((cursor, a[1]))
    return [(t, b) for t, b in pieces if b - t > EPS]


def _clean_series(name: str, values: Sequence[Any] | None, n: int,
                  flags: list[str]) -> tuple[list[float | None], Refusal | None]:
    """Nulls, unscrubbed sentinels and percent-scale detection, per curve."""
    if values is None:
        return [None] * n, None
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be a sequence, got {type(values).__name__}")
    if len(values) != n:
        raise ValueError(
            f"{name} has {len(values)} samples but the depth index has {n}; "
            "the curves are not on the same frame")
    out: list[float | None] = []
    sentinels = 0
    for v in values:
        f = _as_float(v)
        if f is None:
            out.append(None)
        elif abs(f) >= SENTINEL_ABS:
            out.append(None)
            sentinels += 1
        else:
            out.append(f)
    if sentinels:
        flags.append(
            f"unscrubbed-sentinel: {sentinels} {name} sample(s) at |value| >= "
            f"{SENTINEL_ABS:g} were treated as nulls, not as readings. Run "
            "null_scrub (#12) first")
    present = [v for v in out if v is not None]
    if present:
        if name == "sw":
            suspicious = _median(present) > FRACTION_ABS_MAX
            detail = f"median Sw = {_median(present):g}"
        else:
            suspicious = max(present) > FRACTION_ABS_MAX
            detail = f"max {name} = {max(present):g}"
        if suspicious:
            return out, Refusal(
                reason=(f"{name} does not look like a v/v fraction ({detail}). The "
                        "cutoffs are fractions (beg#40 states them as percent: 50%, "
                        "4%, 60%), so a percent-scaled curve would pass every cutoff "
                        "silently - a 100x scale error that looks entirely plausible"),
                needed=(f"{name} in v/v decimal fraction - convert with "
                        "unit_convert (#11)",),
                source=BEG_CUTOFFS)
    return out, None


def _resolve_cutoffs(cutoffs: Any) -> CutoffSet:
    """A CutoffSet, a mapping, or a key of PUBLISHED_CUTOFFS. Never a default."""
    if isinstance(cutoffs, CutoffSet):
        base = cutoffs
    elif isinstance(cutoffs, str):
        key = cutoffs.strip().lower()
        if key not in PUBLISHED_CUTOFFS:
            raise ValueError(
                f"unknown cutoff set {cutoffs!r}; published sets are "
                f"{sorted(PUBLISHED_CUTOFFS)}. This tool does not guess a cutoff.")
        base = PUBLISHED_CUTOFFS[key]
    elif isinstance(cutoffs, dict):
        missing = [k for k in ("vsh_max", "phi_min", "sw_max") if k not in cutoffs]
        if missing:
            raise ValueError(
                f"cutoffs mapping is missing {missing}; beg#40 needs all three for a "
                "*net pay* summation - shale volume and porosity alone give net "
                "reservoir, which is a different quantity")
        base = CutoffSet(
            key="caller", label=str(cutoffs.get("label", "caller-stated cutoffs")),
            vsh_max=float(cutoffs["vsh_max"]), phi_min=float(cutoffs["phi_min"]),
            sw_max=float(cutoffs["sw_max"]),
            porosity_kind=str(cutoffs.get("porosity_kind", "unstated")),
            source=str(cutoffs.get("source", "caller-stated; no corpus anchor")),
            field_note=str(cutoffs.get("field_note", "stated by the caller")),
            rationale=str(cutoffs.get("rationale", "not stated by the caller")))
    else:
        raise TypeError(
            "cutoffs must be a CutoffSet, a mapping with vsh_max/phi_min/sw_max, or "
            f"one of {sorted(PUBLISHED_CUTOFFS)}; got {type(cutoffs).__name__}")
    for label, value in (("vsh_max", base.vsh_max), ("phi_min", base.phi_min),
                         ("sw_max", base.sw_max)):
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"cutoff {label}={value!r} is not a finite number")
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError(
                f"cutoff {label}={value:g} is outside [0, 1]. Cutoffs are v/v "
                "fractions here; beg#40's 50/4/60 percent are 0.50/0.04/0.60")
    return base


def _apply_relaxation(base: CutoffSet, relaxation: Relaxation | None,
                      flags: list[str]) -> AppliedCutoffs:
    if relaxation is None:
        provenance = "published" if base.key in PUBLISHED_CUTOFFS else "caller"
        vsh, phi, sw = base.vsh_max, base.phi_min, base.sw_max
        status = STATUS_PUBLISHED if provenance == "published" else STATUS_CALLER
        note = ("as published" if provenance == "published"
                else "stated by the caller; no corpus anchor")
    else:
        vsh = base.vsh_max * relaxation.vsh_max_factor + relaxation.vsh_max_delta
        phi = base.phi_min * relaxation.phi_min_factor + relaxation.phi_min_delta
        sw = base.sw_max * relaxation.sw_max_factor + relaxation.sw_max_delta
        provenance = ("published+caller-relaxation" if base.key in PUBLISHED_CUTOFFS
                      else "caller")
        status = STATUS_CALLER
        note = (f"caller-declared relaxation ({relaxation.describe()}) stated by "
                f"{relaxation.stated_by}; the corpus publishes base cutoffs only "
                f"({RELAXED_UNSOURCEABLE})")
        for label, was, now, direction in (("Vsh_max", base.vsh_max, vsh, "up"),
                                           ("phi_min", base.phi_min, phi, "down"),
                                           ("Sw_max", base.sw_max, sw, "up")):
            tightened = (now < was - EPS) if direction == "up" else (now > was + EPS)
            if tightened:
                flags.append(
                    f"relaxation-tightens: {label} moved {was:g} -> {now:g}, which "
                    "tightens rather than relaxes. Reported, not corrected - the "
                    "numbers are the caller's")
        for label, value in (("Vsh_max", vsh), ("phi_min", phi), ("Sw_max", sw)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"the declared relaxation puts {label} at {value:g}, outside "
                    "[0, 1]; a cutoff outside the range of a v/v fraction is not a "
                    "cutoff")

    def cq(value: float, label: str) -> Quantity:
        return _q(value, "v/v", f"{label} cutoff [{status}]", base.source,
                  inputs={"published_value": {"Vsh_max": base.vsh_max,
                                              "phi_min": base.phi_min,
                                              "Sw_max": base.sw_max}[label]},
                  assumptions={"status": status, "set": base.label,
                               "basis": note, "field_note": base.field_note,
                               "rationale": base.rationale,
                               "porosity_kind": base.porosity_kind})

    return AppliedCutoffs(
        vsh_max=cq(vsh, "Vsh_max"), phi_min=cq(phi, "phi_min"), sw_max=cq(sw, "Sw_max"),
        provenance=provenance, base=base, relaxation=relaxation)


def _quality_usable(quality: Any, n: int) -> tuple[list[str], int, int, str]:
    """Per-sample quality verdicts from hole_quality (#25) or a plain sequence."""
    if quality is None:
        return ["unevaluated"] * n, 0, 0, "none supplied"
    verdicts: list[str]
    if hasattr(quality, "samples") and hasattr(quality, "mask"):
        samples = tuple(quality.samples)
        if len(samples) != n:
            raise ValueError(
                f"hole_quality has {len(samples)} samples but the depth index has {n}; "
                "the quality mask is not on this frame")
        verdicts = [str(getattr(s, "verdict", "unknown")) for s in samples]
        how = "hole_quality (#25) per-sample verdicts"
    else:
        if isinstance(quality, (str, bytes)) or not isinstance(quality, Sequence):
            raise TypeError(
                "quality must be a hole_quality result (#25) or a per-sample "
                f"sequence; got {type(quality).__name__}")
        if len(quality) != n:
            raise ValueError(
                f"quality has {len(quality)} samples but the depth index has {n}")
        verdicts = []
        for v in quality:
            if isinstance(v, bool):
                verdicts.append("good" if v else "bad")
            elif v is None:
                verdicts.append("unknown")
            else:
                s = str(v).strip().lower()
                if s not in ("good", "bad", "unknown"):
                    raise ValueError(
                        f"quality verdict {v!r} is not one of good/bad/unknown")
                verdicts.append(s)
        how = "caller-supplied per-sample verdicts"
    return verdicts, verdicts.count("bad"), verdicts.count("unknown"), how


# --- the per-sample test (net_pay_cutoffs #39 should own this) --------------


def apply_cutoffs(vsh: Sequence[Any], phi: Sequence[Any], sw: Sequence[Any],
                  cutoffs: Any, *, depth_ft: Sequence[Any] | None = None
                  ) -> tuple[SampleTest, ...]:
    """The `beg#40` net-pay test, per sample. Exposed for `net_pay_cutoffs` (#39).

    `vsh <= vsh_max and phi >= phi_min and sw <= sw_max`, inclusive at the cutoff
    (see the spec's open question 1). Any null makes the sample undetermined -
    never passing. #39 does not exist in `tools/` yet; when it lands it should own
    this function and `bypassed_pay_scan` should import it rather than keep a
    second copy of the test.
    """
    base = _resolve_cutoffs(cutoffs)
    n = len(vsh)
    if len(phi) != n or len(sw) != n:
        raise ValueError("vsh, phi and sw must be the same length")
    depths = [float(d) for d in depth_ft] if depth_ft is not None else [float("nan")] * n
    if len(depths) != n:
        raise ValueError("depth_ft must be the same length as the curves")
    out: list[SampleTest] = []
    for i in range(n):
        v, p, s = _as_float(vsh[i]), _as_float(phi[i]), _as_float(sw[i])
        if v is None or p is None or s is None:
            out.append(SampleTest(depths[i], "null", (), v, p, s))
            continue
        failed = []
        if v > base.vsh_max + EPS:
            failed.append("vsh")
        if p < base.phi_min - EPS:
            failed.append("phi")
        if s > base.sw_max + EPS:
            failed.append("sw")
        out.append(SampleTest(depths[i], "fail" if failed else "pass",
                              tuple(failed), v, p, s))
    return tuple(out)


# --- the tool --------------------------------------------------------------


def bypassed_pay_scan(
    depth_ft: Sequence[Any],
    *,
    cutoffs: Any = None,
    perforated_intervals_ft: Sequence[Sequence[float]] | None = None,
    min_thickness_ft: float | None = None,
    vsh: Sequence[Any] | None = None,
    phi: Sequence[Any] | None = None,
    sw: Sequence[Any] | None = None,
    net_pay_intervals_ft: Sequence[Sequence[float]] | None = None,
    relaxed: bool = False,
    relaxation: Relaxation | None = None,
    quality: Any = None,
    reject_unknown_quality: bool = False,
    depth_registry_tolerance_ft: float = PERF_IN_ZONE_TOLERANCE_FT,
    step_ft: float | None = None,
    gap_break_factor: float = GAP_BREAK_FACTOR,
    porosity_kind: str | None = None,
    depth_unit: str = "ft",
) -> BypassedPayScan | Refusal:
    """Intervals that pass net-pay cutoffs and were never perforated.

    Cutoffs are required and never defaulted - two published sets disagree
    (Boonsville 50/4/60, Sharaf 50/10/70) and both are field-local, which is the
    proof they are parameters. Perforations are required too: without them the
    tool can report *pay* and not *bypassed*.

    A relaxed scan needs the relaxation declared. The catalog's own correction on
    this tool is that "'relaxed' is unsourceable as written", so `relaxed=True`
    with no `Relaxation` returns a Refusal rather than a manufactured number.

    Depths increase downward, in feet, in one consistent reference. Curves are
    expected post-`null_scrub` (#12): `None` marks a null. Hole quality comes
    from `hole_quality` (#25) - pass the result itself or its verdicts.
    """
    flags: list[str] = []

    # -- programmer-error guards (raise; these are wiring faults) -----------
    if isinstance(depth_ft, (str, bytes)) or not isinstance(depth_ft, Sequence):
        raise TypeError(f"depth_ft must be a sequence, got {type(depth_ft).__name__}")
    if float(depth_registry_tolerance_ft) < 0:
        raise ValueError("depth_registry_tolerance_ft must not be negative")
    if min_thickness_ft is not None and float(min_thickness_ft) < 0:
        raise ValueError("min_thickness_ft must not be negative")
    if step_ft is not None and float(step_ft) <= 0:
        raise ValueError("step_ft must be positive")
    if float(gap_break_factor) < 1.0:
        raise ValueError("gap_break_factor below 1.0 would split adjacent samples")
    if relaxation is not None and not isinstance(relaxation, Relaxation):
        raise TypeError("relaxation must be a Relaxation")

    # -- R1: a relaxed scan with nothing declared to relax by ---------------
    if relaxed and (relaxation is None or relaxation.is_noop):
        return Refusal(
            reason=(
                "a relaxed scan was requested but no relaxation was declared. The "
                f"corpus publishes base cutoffs only - {RELAXED_UNSOURCEABLE} - and "
                "tool-catalog.md's threshold table marks the cutoff relaxation "
                "factor CALLER. beg#40's 50% / 4% / 60% are the net-pay cutoffs "
                "themselves, not a relaxed version of anything. This tool will not "
                "manufacture a relaxation"),
            needed=("relaxation=Relaxation(stated_by=..., phi_min_factor=..., ...), "
                    "or relaxed cutoffs passed outright as the cutoffs argument",),
            source=CATALOG_110)

    # -- R2: cutoffs ---------------------------------------------------------
    if cutoffs is None:
        return Refusal(
            reason=(
                "no cutoffs were supplied. Two published sets disagree - Boonsville "
                "Vsh 50% / phi 4% / Sw 60% (beg#40, the only one with a stated "
                "rationale: 4% comes off a core porosity/permeability crossplot at "
                "0.05 md) and Sharaf-1 Vsh 50% / PHIE 10% / Sw 70% "
                "(petrophysical-evaluation-chapter4#2) - and both are field-local. "
                "Cutoffs are parameters, so this tool has no default"),
            needed=(f"cutoffs=... one of {sorted(PUBLISHED_CUTOFFS)}, a CutoffSet, or "
                    "a mapping with vsh_max/phi_min/sw_max as v/v fractions",),
            source=BEG_CUTOFFS)
    base = _resolve_cutoffs(cutoffs)
    applied = _apply_relaxation(base, relaxation, flags)

    # -- R3: perforations ----------------------------------------------------
    if perforated_intervals_ft is None:
        return Refusal(
            reason=(
                "no perforated intervals were supplied. Without the completion "
                "record this tool can report pay and cannot report *bypassed* pay - "
                "'never perforated' is the whole claim. Pass an empty sequence to "
                "state positively that the well was never perforated"),
            needed=("perforated_intervals_ft=[(top_ft, base_ft), ...] from the "
                    "completion record, or [] to state that there are none",),
            source=CATALOG_110)

    # -- R4: minimum thickness ----------------------------------------------
    if min_thickness_ft is None:
        return Refusal(
            reason=(
                "no minimum net-pay thickness was supplied and no source in the "
                "corpus states one. beg#40 summed by mapped layer, not by contiguous "
                "run, so it never needed a minimum; asquith's 'at least 6 ft thick' "
                "is about a long normal reading true resistivity, not a pay minimum, "
                "and substituting it here would be an adjacent-equation swap. A "
                "single 0.5 ft sample is not a recompletion target, so the tool will "
                "not run without the number"),
            needed=("min_thickness_ft, stated by the caller",),
            source=CATALOG_THRESHOLDS)

    # -- unit gate -----------------------------------------------------------
    if str(depth_unit).strip().lower() not in ("ft", "f", "feet"):
        return Refusal(
            reason=(f"depth is in {depth_unit!r}. The depth-registry tolerance and "
                    "the minimum thickness are both in feet; converting the index "
                    "silently is how a factor of 3.28 gets buried in an interval "
                    "list an operator perforates against"),
            needed=("depth in feet - convert with unit_convert (#11)",),
            source=ASQUITH_REGISTRY)

    perfs = _merge(perforated_intervals_ft, "perforated_intervals_ft")
    tol = float(depth_registry_tolerance_ft)
    expanded = _merge([(t - tol, b + tol) for t, b in perfs], "perforated_intervals_ft")
    if not perfs:
        flags.append(
            "no-perforations-on-record: an empty perforation list was supplied, so "
            "every pay interval below is reported as bypassed on the caller's "
            "statement that nothing was ever perforated")
    min_h = float(min_thickness_ft)

    tolerance_q = _q(tol, "ft", f"depth-registry tolerance [{STATUS_PROVISIONAL}]",
                     ASQUITH_REGISTRY,
                     assumptions={
                         "status": STATUS_PROVISIONAL,
                         "basis": ("asquith#64 p. 170: a log suite 'generally requires "
                                   "more than one logging run out of the borehole, "
                                   "[so] some logs differ slightly in depth-registry "
                                   "of beds'. tool-catalog.md sets +/-2 ft on that "
                                   "basis - PROVISIONAL, with basis"),
                         "widen_when": "the runs on this well are known to disagree"})
    min_h_q = _q(min_h, "ft", f"minimum net-pay thickness [{STATUS_CALLER}]",
                 CATALOG_THRESHOLDS,
                 assumptions={"status": STATUS_CALLER,
                              "basis": "no source in the corpus states one"})

    # -- the two ways in -----------------------------------------------------
    samples: tuple[SampleTest, ...] = ()
    n_bad = n_unknown = 0
    depths: list[float] = []
    slab = float(step_ft) if step_ft else 0.0
    candidates: list[tuple[float, float, list[int]]] = []

    if net_pay_intervals_ft is not None:
        # Consume net_pay_cutoffs (#39) directly; skip the curve half entirely.
        pay_pairs = _merge(net_pay_intervals_ft, "net_pay_intervals_ft")
        candidates = [(t, b, []) for t, b in pay_pairs]
        flags.append(
            "net-pay-intervals-supplied: the cutoff half was not run here. The "
            "intervals came from net_pay_cutoffs (#39) and the cutoffs recorded on "
            "this result are the caller's statement of what #39 applied")
    else:
        # -- R5 / R6: the curves --------------------------------------------
        missing = [name for name, series in (("vsh", vsh), ("phi", phi), ("sw", sw))
                   if series is None]
        if len(missing) == 3:
            return Refusal(
                reason=(
                    "no interpreted curves and no net-pay intervals were supplied. "
                    "There are two ways in: the three curves beg#40's net-pay "
                    "summation needs (shale volume, porosity, water saturation), or "
                    "net-pay intervals already computed by net_pay_cutoffs (#39)"),
                needed=("vsh, phi and sw as v/v per-sample series",
                        "or net_pay_intervals_ft from net_pay_cutoffs (#39)"),
                source=BEG_CUTOFFS)
        if missing:
            return Refusal(
                reason=(
                    f"the {', '.join(missing)} curve(s) are absent. beg#40 p. C.29 "
                    "needs all three for a *net pay* summation - 'net reservoir "
                    "(using a shale volume cutoff and a porosity cutoff) and net pay "
                    "(using shale volume, porosity, and water saturation cutoffs)'. "
                    "Two of three gives net reservoir, which is a weaker claim and a "
                    "different tool"),
                needed=tuple(f"a {m} curve, v/v, on this depth frame" for m in missing),
                source=BEG_CUTOFFS)

        n = len(depth_ft)
        if n == 0:
            return Refusal(
                reason="no depth samples; a scan over zero depths is undefined",
                needed=("a depth index from the ~A section",), source=BEG_CUTOFFS)
        depths_raw = [_as_float(d) for d in depth_ft]
        if any(d is None for d in depths_raw):
            return Refusal(
                reason=("the depth index carries nulls. Interval thickness is measured "
                        "against depth, so a hole in the index is a hole in the frame"),
                needed=("an index column with no nulls - null_scrub (#12) flags these "
                        "as 'index-null'",),
                source=BEG_CUTOFFS)
        depths = [float(d) for d in depths_raw]  # type: ignore[arg-type]

        # Frame check before anything is reordered, so a mismatch reads as the
        # wiring fault it is rather than as an IndexError three frames down.
        for nm, series in (("vsh", vsh), ("phi", phi), ("sw", sw)):
            if isinstance(series, (str, bytes)) or not isinstance(series, Sequence):
                raise TypeError(f"{nm} must be a sequence, got "
                                f"{type(series).__name__}")
            if len(series) != n:
                raise ValueError(
                    f"{nm} has {len(series)} samples but the depth index has {n}; "
                    "the curves are not on the same frame")

        order = list(range(n))
        if n > 1:
            ups = sum(1 for i in range(n - 1) if depths[i + 1] > depths[i])
            downs = sum(1 for i in range(n - 1) if depths[i + 1] < depths[i])
            if ups and downs:
                return Refusal(
                    reason=("the depth index is not monotonic; an interval measured "
                            "across a fold in the index has no thickness"),
                    needed=("a monotonic depth index",), source=BEG_CUTOFFS)
            if downs and not ups:
                order = list(range(n - 1, -1, -1))
                depths = [depths[i] for i in order]
                flags.append("depth-index-descending: the file is indexed bottom-up; "
                             "it was reversed internally")

        v_clean, ref = _clean_series("vsh", [vsh[i] for i in order], n, flags)
        if ref is not None:
            return ref
        p_clean, ref = _clean_series("phi", [phi[i] for i in order], n, flags)
        if ref is not None:
            return ref
        s_clean, ref = _clean_series("sw", [sw[i] for i in order], n, flags)
        if ref is not None:
            return ref
        if all(v is None for v in v_clean) or all(v is None for v in p_clean) \
                or all(v is None for v in s_clean):
            empty = [nm for nm, ser in (("vsh", v_clean), ("phi", p_clean),
                                        ("sw", s_clean)) if all(v is None for v in ser)]
            return Refusal(
                reason=(f"every sample of {', '.join(empty)} is null, so the net-pay "
                        "test cannot be evaluated anywhere in this interval"),
                needed=tuple(f"a {m} curve with at least one reading" for m in empty),
                source=BEG_CUTOFFS)

        # -- slab thickness --------------------------------------------------
        if slab <= 0:
            if n < 2:
                return Refusal(
                    reason=("a single sample has no derivable depth step, so it has "
                            "no thickness and cannot be summed"),
                    needed=("step_ft, or a depth index with at least two samples",),
                    source=BEG_CUTOFFS)
            steps = [depths[i + 1] - depths[i] for i in range(n - 1)]
            slab = _median(steps)
            if slab <= 0:
                return Refusal(
                    reason="the median depth step is zero; the index does not advance",
                    needed=("a depth index with a positive step",), source=BEG_CUTOFFS)
            ragged = sum(1 for s in steps if abs(s - slab) > 0.01 * slab)
            if ragged:
                flags.append(
                    f"non-uniform-spacing: {ragged} of {len(steps)} depth steps differ "
                    f"from the median {slab:g} ft by more than 1%. Every sample is "
                    f"still summed as one {slab:g} ft slab")

        # -- per-sample test + evidence gates --------------------------------
        raw = apply_cutoffs(v_clean, p_clean, s_clean, applied_as_set(applied),
                            depth_ft=depths)
        # Quality arrives in the caller's array order, like the curves, so it is
        # reordered with them when the index runs bottom-up.
        verdicts, n_bad, n_unknown, how = _quality_usable(quality, n)
        verdicts = [verdicts[i] for i in order]
        gated: list[SampleTest] = []
        for i, st in enumerate(raw):
            qv = verdicts[i]
            if qv == "bad" or (reject_unknown_quality and qv == "unknown"):
                gated.append(SampleTest(st.depth_ft, "bad-hole", st.failed,
                                        st.vsh, st.phi, st.sw))
            else:
                gated.append(st)
        samples = tuple(gated)
        if quality is None:
            flags.append(
                "no-hole-quality: no borehole-condition evidence was supplied, so a "
                "sample inside a washout is being taken at face value. beg#40 p. C.26: "
                "the density 'tends to read very high porosities (low bulk densities) "
                "when the tool pad cannot make good contact with the side of the hole' "
                "- the direction that manufactures pay. Pass hole_quality (#25)")
        else:
            note = f"hole-quality: {how}; {n_bad} sample(s) excluded as bad hole"
            if n_unknown:
                fate = ("also excluded" if reject_unknown_quality
                        else "kept and counted, not assumed good")
                note += f"; {n_unknown} unknown, {fate}"
            flags.append(note)

        # -- group contiguous passing samples --------------------------------
        run: list[int] = []
        splits = 0
        for i, st in enumerate(samples):
            if st.verdict == "pass":
                if run and (depths[i] - depths[run[-1]]) > gap_break_factor * slab + EPS:
                    candidates.append(_run_extent(depths, run, slab))
                    run = []
                    splits += 1
                run.append(i)
            elif run:
                candidates.append(_run_extent(depths, run, slab))
                run = []
        if run:
            candidates.append(_run_extent(depths, run, slab))
        if splits:
            flags.append(
                f"gap-split: {splits} run(s) were broken by a depth gap wider than "
                f"{gap_break_factor:g}x the {slab:g} ft slab. A pay interval is not "
                "reported across missing data")

    # -- minimum thickness, then subtract the perforations -------------------
    pay: list[Interval] = []
    thin: list[Interval] = []
    bypassed: list[Interval] = []
    slivers: list[Interval] = []

    for top, bot, idx in candidates:
        thickness = bot - top
        if thickness < min_h - EPS:
            thin.append(_interval("thin", top, bot, idx, samples, slab, applied,
                                  flags=(f"below the {min_h:g} ft minimum net-pay "
                                         f"thickness (CALLER; no source states one)",)))
            continue
        perf_ft = _overlap_ft((top, bot), expanded)
        pieces = _subtract((top, bot), expanded)
        if perf_ft <= EPS:
            classification = "bypassed"
        elif not pieces:
            classification = "perforated"
        else:
            classification = "partly_perforated"
        iv_flags: list[str] = []
        if classification != "bypassed" and tol > 0:
            iv_flags.append(
                f"perforation membership allows +/-{tol:g} ft of depth registry "
                f"(PROVISIONAL, basis asquith#64)")
        for pt, pb in pieces:
            if (pb - pt) < min_h - EPS:
                slivers.append(_interval(
                    "sliver", pt, pb, idx, samples, slab, applied,
                    flags=(f"unperforated remainder of the {top:g}-{bot:g} ft pay "
                           f"interval, below the {min_h:g} ft minimum",)))
                iv_flags.append(
                    f"a {pb - pt:g} ft unperforated remainder at {pt:g}-{pb:g} ft was "
                    f"dropped by the {min_h:g} ft minimum thickness")
            else:
                bypassed.append(_interval("bypassed", pt, pb, idx, samples, slab,
                                          applied))
        pay.append(_interval("pay", top, bot, idx, samples, slab, applied,
                             classification=classification,
                             perforated_ft=perf_ft,
                             unperforated_ft=thickness - perf_ft,
                             flags=tuple(iv_flags)))

    total_bypassed = sum(iv.thickness_ft.value for iv in bypassed)
    total_pay = sum(iv.thickness_ft.value for iv in pay)
    phi_h = sum(iv.phi_h_ft.value for iv in bypassed if iv.phi_h_ft is not None)
    phi_so_h = sum(iv.phi_so_h_ft.value for iv in bypassed if iv.phi_so_h_ft is not None)

    if porosity_kind is not None and base.porosity_kind != "unstated" \
            and str(porosity_kind).strip().lower() != base.porosity_kind:
        flags.append(
            f"porosity-kind-mismatch: the {base.label} porosity cutoff is stated on "
            f"{base.porosity_kind} porosity and the curve was declared "
            f"{porosity_kind!r}. Not the published test")
    elif porosity_kind is None:
        flags.append(
            "porosity-kind-undeclared: the curve's porosity kind was not stated. "
            f"This set's cutoff is stated on {base.porosity_kind} porosity")
    if base.key in PUBLISHED_CUTOFFS:
        flags.append(f"published-cutoffs-are-field-local: {base.field_note}")
    if applied.relaxation is not None:
        flags.append(
            f"caller-relaxation: {applied.relaxation.describe()}, stated by "
            f"{applied.relaxation.stated_by}. {RELAXED_UNSOURCEABLE}")
    flags.append(
        "perforation-comparison-unsourced: the cutoff half is published (beg#40); "
        "the never-perforated half is this build's, at a PROVISIONAL tolerance. "
        "tool-catalog.md records that no comparison rule, depth tolerance or pay "
        "cutoff for it exists in the corpus (see completion_history_compare #111)")

    n_pass = sum(1 for s in samples if s.verdict == "pass")
    n_fail = sum(1 for s in samples if s.verdict == "fail")
    n_null = sum(1 for s in samples if s.verdict == "null")
    n_bad_hole = sum(1 for s in samples if s.verdict == "bad-hole")

    def sq(value: float, unit: str, label: str) -> Quantity:
        return _q(value, unit, label, BEG_CUTOFFS,
                  inputs={"cutoffs": applied.triple,
                          "tolerance_ft": tol, "min_thickness_ft": min_h},
                  assumptions={"cutoff_provenance": applied.provenance})

    return BypassedPayScan(
        bypassed=tuple(bypassed),
        pay_intervals=tuple(pay),
        thin_intervals=tuple(thin),
        dropped_slivers=tuple(slivers),
        total_bypassed_ft=sq(total_bypassed, "ft", "sum of bypassed interval thickness"),
        total_pay_ft=sq(total_pay, "ft", "sum of net-pay interval thickness"),
        bypassed_fraction=sq(total_bypassed / total_pay if total_pay > 0 else 0.0,
                             "v/v", "bypassed thickness / net pay thickness"),
        total_phi_h_ft=sq(phi_h, "ft", "sum of phi*h over the bypassed intervals"),
        total_phi_so_h_ft=sq(phi_so_h, "ft",
                             "sum of phi*(1-Sw)*h over the bypassed intervals"),
        cutoffs=applied,
        tolerance_ft=tolerance_q,
        min_thickness_ft=min_h_q,
        samples=samples,
        n_samples=len(samples),
        n_pass=n_pass, n_fail=n_fail, n_null=n_null, n_bad_hole=n_bad_hole,
        inputs={"n_perforated_intervals": len(perfs),
                "perforated_intervals_ft": tuple(perfs),
                "cutoffs": {"vsh_max": applied.vsh_max.value,
                            "phi_min": applied.phi_min.value,
                            "sw_max": applied.sw_max.value},
                "min_thickness_ft": min_h,
                "depth_registry_tolerance_ft": tol,
                "slab_ft": slab},
        assumptions={
            "cutoff_set": base.label,
            "cutoff_source": base.source,
            "cutoff_provenance": applied.provenance,
            "cutoff_boundary": ("inclusive: vsh <= vsh_max, phi >= phi_min, "
                                "sw <= sw_max. beg#40 states the values, not the "
                                "boundary; see the spec's open question 1"),
            "sample_extent": ("each sample is one slab of the median depth step, "
                              "centred on its depth"),
            "perforation_comparison": ("ours, not published; perforations expanded by "
                                       "the depth-registry tolerance, then subtracted"),
            "minimum_thickness": "CALLER; applied to pay intervals and to remainders",
            "hole_quality": "consumed from hole_quality (#25); not reimplemented here",
        },
        flags=tuple(flags))


def applied_as_set(applied: AppliedCutoffs) -> CutoffSet:
    """The applied numbers as a CutoffSet, so `apply_cutoffs` sees the relaxation."""
    b = applied.base
    return CutoffSet(key="applied", label=b.label,
                     vsh_max=applied.vsh_max.value, phi_min=applied.phi_min.value,
                     sw_max=applied.sw_max.value, porosity_kind=b.porosity_kind,
                     source=b.source, field_note=b.field_note, rationale=b.rationale)


def _run_extent(depths: Sequence[float], idx: Sequence[int],
                slab: float) -> tuple[float, float, list[int]]:
    return (depths[idx[0]] - slab / 2.0, depths[idx[-1]] + slab / 2.0, list(idx))


def _interval(kind: str, top: float, bot: float, idx: Sequence[int],
              samples: Sequence[SampleTest], slab: float, applied: AppliedCutoffs,
              *, classification: str = "", perforated_ft: float | None = None,
              unperforated_ft: float | None = None,
              flags: tuple[str, ...] = ()) -> Interval:
    """Summations over the samples whose centres lie inside (top, bot)."""
    inside = [samples[i] for i in idx
              if samples[i].vsh is not None
              and top - EPS <= samples[i].depth_ft <= bot + EPS]
    n = len(inside)
    src = applied.base.source
    m = "arithmetic mean over the samples in the interval (beg#40 'Summations')"

    def q(value: float, unit: str, label: str) -> Quantity:
        return _q(value, unit, label, src, inputs={"n_samples": n})

    mean_vsh = mean_phi = mean_sw = phi_h = phi_so_h = None
    if n:
        mean_vsh = q(sum(s.vsh for s in inside) / n, "v/v", f"mean Vsh, {m}")
        mean_phi = q(sum(s.phi for s in inside) / n, "v/v", f"mean porosity, {m}")
        mean_sw = q(sum(s.sw for s in inside) / n, "v/v", f"mean Sw, {m}")
        phi_h = q(sum(s.phi for s in inside) * slab, "ft",
                  "phi*h, summed sample by sample (beg#40 'Summations')")
        phi_so_h = q(sum(s.phi * (1.0 - s.sw) for s in inside) * slab, "ft",
                     "phi*(1-Sw)*h, hydrocarbon pore thickness")
    return Interval(
        kind=kind,
        top_ft=q(top, "ft", "interval top"),
        base_ft=q(bot, "ft", "interval base"),
        thickness_ft=q(bot - top, "ft", "interval thickness"),
        n_samples=n,
        classification=classification,
        perforated_ft=None if perforated_ft is None else q(
            perforated_ft, "ft", "thickness within a perforation, at the tolerance"),
        unperforated_ft=None if unperforated_ft is None else q(
            unperforated_ft, "ft", "thickness outside every perforation"),
        mean_vsh=mean_vsh, mean_phi=mean_phi, mean_sw=mean_sw,
        phi_h_ft=phi_h, phi_so_h_ft=phi_so_h, flags=flags)


# --- the LAS entry point ---------------------------------------------------


def bypassed_pay_scan_from_las(las_file: Any, **kwargs: Any):
    """Locate the interpreted curves in a parsed LAS, then scan.

    This only *locates* curves. It never computes Vsh, porosity or Sw - `vshale`
    (#31), the porosity tools (#26-#29) and `archie_sw` (#35) own those, and
    `archie_sw` in particular refuses without Rw provenance for good reason.
    A raw DPHI or NPHI is not an interpreted porosity and is not accepted as one.
    """
    curves = {str(c.mnemonic).strip().upper(): i
              for i, c in enumerate(getattr(las_file, "curves", ()))}
    cols = getattr(las_file, "columns", ())

    def pick(names: Sequence[str]) -> tuple[str, Sequence[Any]] | None:
        for nm in names:
            if nm in curves:
                return nm, cols[curves[nm]]
        return None

    found = {"vsh": pick(VSH_MNEMONICS), "phi": pick(PHI_MNEMONICS),
             "sw": pick(SW_MNEMONICS)}
    missing = [k for k, v in found.items() if v is None]
    if missing:
        raw = [m for m in RAW_POROSITY_MNEMONICS if m in curves]
        extra = ("" if not raw else
                 f" The file carries {', '.join(raw)}, which are single-tool "
                 "porosities, not an interpreted PHIE/PHIT: they still need a matrix, "
                 "a gas correction and a shale correction before a 4%-or-10% cutoff "
                 "means anything, so they are not used here.")
        return Refusal(
            reason=(f"the {', '.join(missing)} curve(s) are not in this file's curve "
                    f"inventory (present: {', '.join(sorted(curves))}). beg#40's "
                    "net-pay summation needs shale volume, porosity and water "
                    "saturation, and a LAS file that was never interpreted carries "
                    f"none of them.{extra}"),
            needed=tuple(
                [f"a {m} curve on this frame" for m in missing]
                + ["vshale (#31) from GR, a porosity tool (#26-#29), and archie_sw "
                   "(#35) with Rw provenance - then call bypassed_pay_scan directly",
                   "and a perforation record, which no LAS file carries"]),
            source=BEG_CUTOFFS)
    depth = cols[0] if cols else ()
    return bypassed_pay_scan(depth, vsh=found["vsh"][1], phi=found["phi"][1],
                             sw=found["sw"][1], **kwargs)



# ======================================================================
# Tool #111 completion_history_compare
# ======================================================================

# --- anchors ---------------------------------------------------------------

CATALOG_111 = (
    "tool-catalog.md, section 17, completion_history_compare [#111]: "
    "\"Source: none - no source in corpus. no comparison rule, no depth "
    "tolerance, no pay cutoff in corpus\"")

# The manual ancestor of this tool. A drafting convention, not a method: it says
# to note the discrepancy, not how to measure it.
TEARPOCK_ANNOTATION = (
    "06-fort-worth-basin/tearpock-bischke-applied-subsurface-geological-mapping#46")
TEARPOCK_QUOTE = (
    "tearpock#46: a log's annotation carries \"the name of each pay zone, "
    "perforation intervals, well status, cumulative production from each interval "
    "produced... Any intervals that appear productive on the log but have not been "
    "produced should be noted\". The corpus's only perf-versus-pay practice, and "
    "it is a drafting convention - no tolerance, no criterion, no classification")

# The one perf-to-log depth tolerance the corpus states. Job-time gun placement
# with a live GR/CCL correlation pass, NOT reconciliation of a paper record, so it
# is quoted and offered, never defaulted.
PERF_MANUAL_DEPTH_CONTROL = "10-perforating/fundamentals-of-well-perforating-manual#4"
CCL_DEPTH_CONTROL_TOLERANCE_FT = 1.0
CCL_RECALCULATE_ABOVE_FT = 3.0
CCL_QUOTE = (
    "fundamentals-of-well-perforating-manual#4, 'PRE & POST GUN FIRING "
    "CONSIDERATIONS': \"CCL should be run across(above and below) the interval to "
    "be perforated, depth recorded must be < 1.0 feet difference from the "
    "reference log\"; \"If there are discrepancies larger than 3 feet, repeat the "
    "calculations\". This governs gun placement at job time on a wireline-conveyed "
    "gun with a live GR/CCL pass. It is not a tolerance for reconciling a "
    "historical completion record against a log, and it is not this tool's default")

DATUM_RESOLVE = "datum_resolve (#15), tools/geometry.py"
DATUM_RECONCILE = "datum_reconcile (#16), tools/geometry.py"

STATUS_UNSOURCED = "UNSOURCED"

METHOD_111 = (
    "completion history vs log pay: merged perforation and pay interval sets, each "
    "expanded by the depth-registry tolerance and intersected with the other. "
    "Interval arithmetic is this build's - no comparison rule exists in the corpus "
    "(see CATALOG_111); the tolerance is asquith#64 via tool-catalog.md, the "
    "cutoffs (curve route) are beg#40 or petrophysical-evaluation-chapter4#2")

# The three incompatible explanations for a perforation that lands outside
# everything the log calls pay. Attached verbatim and unranked to every such
# perforation. Nothing in the data distinguishes them, so the tool must not pick
# one - and in particular must not quietly widen the tolerance until the
# perforation "matches", which is explanation 3 being assumed rather than found.
OUTSIDE_PAY_EXPLANATIONS: tuple[str, ...] = (
    "a mis-set gun: the interval was shot in the wrong place",
    "operator knowledge the log does not show: the original operator perforated on "
    "cuttings, a show, a DST, a mud log or an offset correlation, and the cutoffs "
    "applied here do not see it",
    "a depth-registry error between the completion record and the log: the "
    "perforation is in the right rock and the paperwork is on a different depth",
)
OUTSIDE_PAY_NOTE = (
    "perforation outside every pay interval at the stated tolerance. Nothing in "
    "the data distinguishes the three explanations below, so all three are "
    "reported and none is chosen: " + "; ".join(
        f"({i + 1}) {e}" for i, e in enumerate(OUTSIDE_PAY_EXPLANATIONS)))

NO_GRADE_NOTE = (
    "this result is a comparison, not a grade. The corpus states no benchmark for "
    "what fraction of pay a completion should cover, so the fractions here are "
    "arithmetic and carry no verdict. 'This completion was poor' is a judgement "
    "the corpus does not license")


# --- output records --------------------------------------------------------


@dataclass(frozen=True)
class DepthPiece:
    """One bare depth interval, as a category-2 or category-3 finding."""

    top_ft: Quantity
    base_ft: Quantity
    length_ft: Quantity
    origin: str = ""                 # which perforation or pay interval it came from
    flags: tuple[str, ...] = ()

    def __repr__(self) -> str:
        return (f"DepthPiece({self.top_ft.value:g}-{self.base_ft.value:g} ft, "
                f"{self.length_ft.value:g} ft)")


@dataclass(frozen=True)
class PerforationRecord:
    """One merged perforation from the completion record, against the pay set.

    `classification` is in_pay | partly_in_pay | outside_pay. It is a statement of
    geometry at the stated tolerance and nothing more; `outside_pay` is not a
    finding of error.
    """

    top_ft: Quantity
    base_ft: Quantity
    length_ft: Quantity
    in_pay_ft: Quantity
    outside_pay_ft: Quantity
    classification: str
    outside_pieces: tuple[DepthPiece, ...] = ()
    matched_pay: tuple[tuple[float, float], ...] = ()
    nearest_pay_ft: Quantity | None = None
    flags: tuple[str, ...] = ()

    def __repr__(self) -> str:
        return (f"PerforationRecord({self.top_ft.value:g}-{self.base_ft.value:g} ft, "
                f"{self.classification})")


@dataclass(frozen=True)
class PayRecord:
    """One merged pay interval, against the perforation record.

    `classification` is perforated | partly_perforated | not_perforated.
    """

    top_ft: Quantity
    base_ft: Quantity
    thickness_ft: Quantity
    perforated_ft: Quantity
    unperforated_ft: Quantity
    classification: str
    unperforated_pieces: tuple[DepthPiece, ...] = ()
    flags: tuple[str, ...] = ()

    def __repr__(self) -> str:
        return (f"PayRecord({self.top_ft.value:g}-{self.base_ft.value:g} ft, "
                f"{self.classification})")


@dataclass(frozen=True)
class CompletionHistoryComparison:
    """The three-way comparison. No score, no verdict, and none may be added."""

    perforations: tuple[PerforationRecord, ...]
    pay: tuple[PayRecord, ...]
    pay_not_perforated: tuple[DepthPiece, ...]
    perforations_outside_pay: tuple[DepthPiece, ...]
    total_pay_ft: Quantity
    total_perforated_ft: Quantity
    pay_perforated_ft: Quantity
    pay_unperforated_ft: Quantity
    perf_in_pay_ft: Quantity
    perf_outside_pay_ft: Quantity
    tolerance_slack_ft: Quantity
    fraction_of_pay_perforated: Quantity
    fraction_of_perf_in_pay: Quantity
    tolerance_ft: Quantity
    tolerance_provenance: str
    datum_reference: str
    cutoffs: AppliedCutoffs | None = None
    scan: BypassedPayScan | None = None
    method: str = METHOD_111
    source: str = CATALOG_111
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    def __repr__(self) -> str:
        return (f"CompletionHistoryComparison({len(self.perforations)} perf, "
                f"{len(self.pay)} pay, {self.pay_unperforated_ft.value:g} ft pay "
                f"unperforated, {self.perf_outside_pay_ft.value:g} ft perf outside pay)")


# --- helpers ---------------------------------------------------------------


def _gap_ft(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Separation between two intervals; 0 when they touch or overlap."""
    return max(0.0, b[0] - a[1], a[0] - b[1])


def _nearest_gap(a: tuple[float, float],
                 intervals: Sequence[tuple[float, float]]) -> float | None:
    if not intervals:
        return None
    return min(_gap_ft(a, iv) for iv in intervals)


def _expand(intervals: Sequence[tuple[float, float]], tol: float,
            name: str) -> list[tuple[float, float]]:
    if tol <= 0:
        return list(intervals)
    return _merge([(t - tol, b + tol) for t, b in intervals], name)


def _datum_gate(datum: Any) -> Refusal | None:
    """The resolved-datum flag from `datum_resolve` (#15), or an explicit True.

    The datum trap has already produced two defects in group A. A perforation
    record compared against a log hung on a different reference produces a wrong
    answer that looks entirely plausible, so this tool will not run without the
    flag rather than assume the two agree.
    """
    need = (f"datum=<DatumResolution from {DATUM_RESOLVE}> with resolved=True",
            "or datum=True to state positively that the reference was resolved "
            "outside this call")
    if datum is None:
        return Refusal(
            reason=("no resolved-datum flag was supplied. This tool compares two "
                    "depth records - a completion record and a log - and an "
                    "unresolved depth reference makes every interval comparison "
                    "below meaningless while still returning plausible numbers. "
                    f"{DATUM_RESOLVE} exists to settle it"),
            needed=need, source=DATUM_RESOLVE)
    if isinstance(datum, Refusal):
        return Refusal(
            reason=(f"the datum is unresolved: {DATUM_RESOLVE} refused with "
                    f"\"{datum.reason}\". The comparison cannot run against an "
                    "unresolved depth reference"),
            needed=tuple(datum.needed) or need, source=DATUM_RESOLVE)
    if hasattr(datum, "resolved"):
        if not datum.resolved:
            detail = getattr(getattr(datum, "refusal", None), "reason", "")
            return Refusal(
                reason=(f"{DATUM_RESOLVE} returned an unresolved datum"
                        + (f": \"{detail}\"" if detail else "")
                        + ". The comparison cannot run against an unresolved "
                          "depth reference"),
                needed=need, source=DATUM_RESOLVE)
        return None
    if datum is True:
        return None
    if datum is False:
        return Refusal(
            reason=("the caller stated the datum is not resolved. The comparison "
                    "cannot run against an unresolved depth reference"),
            needed=need, source=DATUM_RESOLVE)
    raise TypeError(
        "datum must be a DatumResolution from datum_resolve (#15), a Refusal from "
        f"it, or an explicit bool; got {type(datum).__name__}")


def _reference_gate(log_ref: Any, perf_ref: Any) -> tuple[str, Refusal | None]:
    """Both depth references named, recognised, and the same one.

    A perforation record on driller's depth compared against a log on KB is the
    same datum trap one level down: `datum_resolve` settles what the *log* hangs
    on, and nothing in a LAS says what the completion paperwork hangs on.
    """
    missing = [name for name, v in (("log_depth_reference", log_ref),
                                    ("perforation_depth_reference", perf_ref))
               if v is None or not str(v).strip()]
    if missing:
        return "", Refusal(
            reason=(f"{' and '.join(missing)} not stated. The log's reference comes "
                    f"from {DATUM_RESOLVE}; the completion record's is on the "
                    "completion form and nothing in a LAS file carries it. Comparing "
                    "intervals across two unstated references is the datum trap that "
                    "has already produced two defects in this build"),
            needed=tuple(f"{m}, e.g. 'KB' or 'DF'" for m in missing),
            source=DATUM_RESOLVE)
    log_key, perf_key = normalize_reference(log_ref), normalize_reference(perf_ref)
    unknown = [f"{n}={v!r}" for n, v, k in
               (("log_depth_reference", log_ref, log_key),
                ("perforation_depth_reference", perf_ref, perf_key)) if k is None]
    if unknown:
        return "", Refusal(
            reason=(f"unrecognised depth reference: {', '.join(unknown)}. A "
                    "reference this tool cannot name is one it cannot check for "
                    "agreement, and 'driller's depth' or 'tubing measured' on an old "
                    "completion form is exactly the case that needs checking"),
            needed=("a recognised depth reference on both records (KB, DF, GL, TKB, "
                    "RT, CH, MSL)",
                    f"or a reconciled pair from {DATUM_RECONCILE}"),
            source=DATUM_RESOLVE)
    if log_key != perf_key:
        return "", Refusal(
            reason=(f"the log's depths are on {log_key} and the perforation record's "
                    f"are on {perf_key}. These are different depth references, so "
                    "every overlap computed below would be offset by the difference "
                    "between them - a wrong answer that looks entirely plausible. "
                    "This tool does not apply the shift itself"),
            needed=(f"both records on one reference - resolve with {DATUM_RESOLVE} "
                    f"and reconcile the two wells' references with {DATUM_RECONCILE}",
                    "or a perforation record already shifted onto the log's reference",),
            source=DATUM_RECONCILE)
    return log_key, None


def _pieces(intervals: Sequence[tuple[float, float]], origin: str, source: str,
            method: str, flags: tuple[str, ...] = ()) -> tuple[DepthPiece, ...]:
    out = []
    for top, base in intervals:
        out.append(DepthPiece(
            top_ft=_q(top, "ft", f"{method}: piece top", source),
            base_ft=_q(base, "ft", f"{method}: piece base", source),
            length_ft=_q(base - top, "ft", f"{method}: piece length", source),
            origin=origin, flags=flags))
    return tuple(out)


# --- the tool --------------------------------------------------------------


def completion_history_compare(
    *,
    perforated_intervals_ft: Sequence[Sequence[float]] | None = None,
    pay_intervals_ft: Sequence[Sequence[float]] | None = None,
    datum: Any = None,
    log_depth_reference: Any = None,
    perforation_depth_reference: Any = None,
    depth_ft: Sequence[Any] | None = None,
    vsh: Sequence[Any] | None = None,
    phi: Sequence[Any] | None = None,
    sw: Sequence[Any] | None = None,
    cutoffs: Any = None,
    relaxed: bool = False,
    relaxation: Relaxation | None = None,
    depth_registry_tolerance_ft: float | None = None,
    min_thickness_ft: float | None = None,
    quality: Any = None,
    reject_unknown_quality: bool = False,
    step_ft: float | None = None,
    gap_break_factor: float | None = None,
    porosity_kind: str | None = None,
    depth_unit: str = "ft",
) -> CompletionHistoryComparison | Refusal:
    """What was shot versus what the log calls pay. Reports; does not grade.

    Two ways to state the pay: `pay_intervals_ft` from `net_pay_cutoffs` (#39), or
    the interpreted curves plus a cutoff set, in which case the pay intervals are
    derived by `bypassed_pay_scan` (#110) - the cutoff table lives there and there
    is deliberately no second copy of it here.

    Nothing is inferred. The perforation record, the pay, the resolved datum and
    both depth references are all required; the tolerance defaults to the
    catalog's +/-2 ft, which is PROVISIONAL *with a basis* in `asquith#64` and is
    labelled as such on the result.
    """
    flags: list[str] = []

    # -- programmer-error guards (raise; these are wiring faults) -----------
    # Provenance is who supplied the number, not what the number is: a caller who
    # states 2.0 has made a decision, and reporting that as "default" attributes
    # their decision to the tool. So the default is a sentinel, not the value.
    tolerance_provenance = "default" if depth_registry_tolerance_ft is None else "caller"
    tol = (PERF_IN_ZONE_TOLERANCE_FT if depth_registry_tolerance_ft is None
           else float(depth_registry_tolerance_ft))
    if not math.isfinite(tol) or tol < 0:
        raise ValueError("depth_registry_tolerance_ft must be finite and non-negative")
    if min_thickness_ft is not None and float(min_thickness_ft) < 0:
        raise ValueError("min_thickness_ft must not be negative")
    if relaxation is not None and not isinstance(relaxation, Relaxation):
        raise TypeError("relaxation must be a Relaxation")

    # -- R7: units, before any depth is trusted -----------------------------
    if str(depth_unit).strip().lower() not in ("ft", "f", "feet"):
        return Refusal(
            reason=(f"depth is in {depth_unit!r}. The depth-registry tolerance is in "
                    "feet, and a silent factor of 3.28 buried in an interval list is "
                    "one an operator perforates against"),
            needed=("depth, perforations and pay in feet - convert with "
                    "unit_convert (#11)",),
            source=ASQUITH_REGISTRY)

    # -- R5 / R6: the datum gates, before any interval is compared ----------
    refusal = _datum_gate(datum)
    if refusal is not None:
        return refusal
    datum_reference, refusal = _reference_gate(log_depth_reference,
                                               perforation_depth_reference)
    if refusal is not None:
        return refusal

    # -- R1: the completion record ------------------------------------------
    if perforated_intervals_ft is None:
        return Refusal(
            reason=("no perforation record was supplied. 'What was shot' is half of "
                    "this comparison and no LAS file carries it - it comes off the "
                    "completion form, a state completion report or the well file. "
                    "Pass an empty sequence to state positively that the well was "
                    "never perforated"),
            needed=("perforated_intervals_ft=[(top_ft, base_ft), ...] from the "
                    "completion record, or [] to state that there are none",),
            source=CATALOG_111)
    perfs = _merge(perforated_intervals_ft, "perforated_intervals_ft")
    if not perfs:
        flags.append(
            "no-perforations-on-record: an empty perforation record was supplied, so "
            "every pay interval below is reported as unperforated on the caller's "
            "statement that nothing was ever shot. With nothing to compare against, "
            "this is bypassed_pay_scan (#110)'s question, not this tool's")

    # -- R2 / R3 / R4: the pay half ------------------------------------------
    scan: BypassedPayScan | None = None
    applied: AppliedCutoffs | None = None
    have_curves = any(c is not None for c in (vsh, phi, sw))

    if pay_intervals_ft is not None:
        if have_curves or cutoffs is not None:
            flags.append(
                "pay-intervals-supplied: the curve/cutoff half was not run. The "
                "intervals are taken as given - from net_pay_cutoffs (#39) or the "
                "caller - and any curves or cutoffs passed alongside were ignored")
        if relaxed or relaxation is not None:
            return Refusal(
                reason=("a relaxation was declared but the cutoff half is not running "
                        "here: pay_intervals_ft was supplied, so no cutoff is applied "
                        "by this tool and there is nothing for a relaxation to act "
                        "on. Relaxing after the fact would be this tool inventing a "
                        "pay interval the caller did not state"),
                needed=("either drop relaxed/relaxation, or pass the curves and "
                        "cutoffs so bypassed_pay_scan (#110) applies the relaxation "
                        "where it belongs",),
                source=CATALOG_111)
        pay_pairs = _merge(pay_intervals_ft, "pay_intervals_ft")
    elif have_curves or depth_ft is not None:
        if cutoffs is None:
            return Refusal(
                reason=("the curve route was taken and no cutoffs were supplied. Two "
                        "published sets disagree - Boonsville Vsh 50% / phi 4% / Sw "
                        "60% (beg#40) and Sharaf-1 Vsh 50% / PHIE 10% / Sw 70% "
                        "(petrophysical-evaluation-chapter4#2) - and both are "
                        "field-local, which is the proof they are parameters. Neither "
                        "this tool nor bypassed_pay_scan (#110) has a default, and "
                        "this tool keeps no second cutoff table"),
                needed=(f"cutoffs=... one of {sorted(PUBLISHED_CUTOFFS)}, a CutoffSet, "
                        "or a mapping with vsh_max/phi_min/sw_max as v/v fractions",
                        "or pay_intervals_ft from net_pay_cutoffs (#39)"),
                source=BEG_CUTOFFS)
        if relaxed and (relaxation is None or relaxation.is_noop):
            return Refusal(
                reason=("a relaxed comparison was requested but no relaxation was "
                        f"declared. {RELAXED_UNSOURCEABLE}, and tool-catalog.md's "
                        "threshold table marks the cutoff relaxation factor CALLER. "
                        "This tool will not manufacture one"),
                needed=("relaxation=Relaxation(stated_by=..., phi_min_factor=..., "
                        "...), or relaxed cutoffs passed outright as cutoffs",),
                source=CATALOG_111)
        if depth_ft is None:
            return Refusal(
                reason=("interpreted curves were supplied without a depth index. "
                        "Interval thickness is measured against depth"),
                needed=("depth_ft, the index column from the ~A section",),
                source=BEG_CUTOFFS)
        scan_kwargs: dict[str, Any] = {}
        if gap_break_factor is not None:
            scan_kwargs["gap_break_factor"] = float(gap_break_factor)
        scan = bypassed_pay_scan(
            depth_ft,
            cutoffs=cutoffs,
            perforated_intervals_ft=perfs,
            min_thickness_ft=0.0 if min_thickness_ft is None else float(min_thickness_ft),
            vsh=vsh, phi=phi, sw=sw,
            relaxed=relaxed, relaxation=relaxation,
            quality=quality, reject_unknown_quality=reject_unknown_quality,
            depth_registry_tolerance_ft=tol,
            step_ft=step_ft,
            porosity_kind=porosity_kind,
            depth_unit=depth_unit,
            **scan_kwargs)
        if isinstance(scan, Refusal):
            return scan
        applied = scan.cutoffs
        pay_pairs = _merge([(iv.top_ft.value, iv.base_ft.value)
                            for iv in scan.pay_intervals], "pay_intervals_ft")
        flags.append(
            "pay-derived-from-curves: net pay came from bypassed_pay_scan (#110) at "
            f"the {applied.base.label} cutoffs; this tool applied no cutoff of its own")
        flags.extend(scan.flags)
        if scan.thin_intervals:
            flags.append(
                f"thin-pay-excluded: {len(scan.thin_intervals)} pay interval(s) fell "
                f"below the {float(min_thickness_ft):g} ft minimum thickness and are "
                "not in this comparison. That minimum is the caller's; no source "
                "states one")
    else:
        return Refusal(
            reason=("no pay was supplied. 'What the log calls pay' is the other half "
                    "of this comparison and there are two ways to state it: net-pay "
                    "intervals already computed by net_pay_cutoffs (#39), or the "
                    "three interpreted curves beg#40's net-pay summation needs (shale "
                    "volume, porosity, water saturation) plus a cutoff set, which "
                    "bypassed_pay_scan (#110) turns into intervals"),
            needed=("pay_intervals_ft=[(top_ft, base_ft), ...] from net_pay_cutoffs "
                    "(#39)",
                    "or depth_ft + vsh + phi + sw + cutoffs"),
            source=CATALOG_111)

    if min_thickness_ft is None:
        flags.append(
            "no-minimum-thickness: every pay interval is reported, including "
            "single-sample ones. Unlike bypassed_pay_scan (#110), which refuses "
            "without a minimum because a 0.5 ft sliver is not a recompletion target, "
            "this tool is describing rather than recommending and a comparison that "
            "hides thin pay is a wrong comparison")

    # -- the comparison ------------------------------------------------------
    perf_exp = _expand(perfs, tol, "perforated_intervals_ft")
    pay_exp = _expand(pay_pairs, tol, "pay_intervals_ft")

    src = CATALOG_111
    pay_method = ("pay thickness within +/-tol of a perforation "
                  "(pay INTERSECT expanded perforations)")
    perf_method = ("perforated length within +/-tol of net pay "
                   "(perforation INTERSECT expanded pay)")

    # category 1 + 2, from the pay side
    pay_records: list[PayRecord] = []
    unperforated_all: list[DepthPiece] = []
    for top, base in pay_pairs:
        thickness = base - top
        perforated = _overlap_ft((top, base), perf_exp)
        remainder = _subtract((top, base), perf_exp)
        if perforated <= EPS:
            classification = "not_perforated"
        elif not remainder:
            classification = "perforated"
        else:
            classification = "partly_perforated"
        origin = f"pay {top:g}-{base:g} ft"
        pieces = _pieces(remainder, origin, src, "pay not perforated")
        unperforated_all.extend(pieces)
        iv_flags: list[str] = []
        if classification != "not_perforated" and tol > 0:
            iv_flags.append(
                f"perforation membership allows +/-{tol:g} ft of depth registry "
                "(PROVISIONAL, basis asquith#64)")
        pay_records.append(PayRecord(
            top_ft=_q(top, "ft", "pay interval top", src),
            base_ft=_q(base, "ft", "pay interval base", src),
            thickness_ft=_q(thickness, "ft", "pay interval thickness", src),
            perforated_ft=_q(perforated, "ft", pay_method, src,
                             inputs={"tolerance_ft": tol}),
            unperforated_ft=_q(thickness - perforated, "ft",
                               "pay thickness outside every perforation at +/-tol", src,
                               inputs={"tolerance_ft": tol}),
            classification=classification,
            unperforated_pieces=pieces,
            flags=tuple(iv_flags)))

    # category 3, from the perforation side
    perf_records: list[PerforationRecord] = []
    outside_all: list[DepthPiece] = []
    for top, base in perfs:
        length = base - top
        in_pay = _overlap_ft((top, base), pay_exp)
        outside = _subtract((top, base), pay_exp)
        if in_pay <= EPS:
            classification = "outside_pay"
        elif not outside:
            classification = "in_pay"
        else:
            classification = "partly_in_pay"
        origin = f"perforation {top:g}-{base:g} ft"
        pieces = _pieces(outside, origin, src, "perforation outside pay",
                         flags=(OUTSIDE_PAY_NOTE,))
        outside_all.extend(pieces)
        matched = tuple(p for p in pay_pairs
                        if _overlap_ft((top, base), _expand([p], tol, "pay")) > EPS)
        gap = _nearest_gap((top, base), pay_pairs)
        iv_flags = []
        if classification != "in_pay":
            iv_flags.append(OUTSIDE_PAY_NOTE)
        perf_records.append(PerforationRecord(
            top_ft=_q(top, "ft", "perforation top, as recorded", src),
            base_ft=_q(base, "ft", "perforation base, as recorded", src),
            length_ft=_q(length, "ft", "perforated length, as recorded", src),
            in_pay_ft=_q(in_pay, "ft", perf_method, src, inputs={"tolerance_ft": tol}),
            outside_pay_ft=_q(length - in_pay, "ft",
                              "perforated length outside every pay interval at "
                              "+/-tol", src, inputs={"tolerance_ft": tol}),
            classification=classification,
            outside_pieces=pieces,
            matched_pay=matched,
            nearest_pay_ft=None if gap is None else _q(
                gap, "ft", "separation from the nearest pay interval, untoleranced",
                src, assumptions={"interpretation": (
                    "reported as a bare fact. No source states a distance at which a "
                    "perforation outside pay becomes a registry error rather than a "
                    "mis-set gun, and this tool draws no such line")}),
            flags=tuple(iv_flags)))

    # -- totals ---------------------------------------------------------------
    total_pay = sum(r.thickness_ft.value for r in pay_records)
    total_perf = sum(r.length_ft.value for r in perf_records)
    pay_perforated = sum(r.perforated_ft.value for r in pay_records)
    pay_unperforated = total_pay - pay_perforated
    perf_in_pay = sum(r.in_pay_ft.value for r in perf_records)
    perf_outside = total_perf - perf_in_pay
    slack = pay_perforated - perf_in_pay

    if abs(slack) > EPS:
        flags.append(
            f"tolerance-applied-both-ways: {pay_perforated:g} ft of pay lies within "
            f"+/-{tol:g} ft of a perforation while {perf_in_pay:g} ft of perforation "
            f"lies within +/-{tol:g} ft of pay. These answer different questions and "
            "are not a discrepancy; the difference is reported as tolerance_slack_ft "
            "and is identically zero at tolerance 0")
    if tol > CCL_RECALCULATE_ABOVE_FT:
        flags.append(
            f"tolerance-above-the-perforating-manual's-recalculate-threshold: "
            f"{tol:g} ft. {CCL_QUOTE}")

    def tq(value: float, unit: str, method: str) -> Quantity:
        return _q(value, unit, method, src,
                  inputs={"tolerance_ft": tol,
                          "n_perforations": len(perf_records),
                          "n_pay_intervals": len(pay_records)},
                  assumptions={"status": STATUS_UNSOURCED,
                               "basis": "interval arithmetic; no published rule"})

    frac_pay = pay_perforated / total_pay if total_pay > EPS else 0.0
    frac_perf = perf_in_pay / total_perf if total_perf > EPS else 0.0
    ratio_assumptions = {"status": STATUS_UNSOURCED, "no_threshold": NO_GRADE_NOTE}

    flags.append(
        "comparison-rule-unsourced: the interval arithmetic here is this build's. "
        f"{CATALOG_111}. The corpus's only perf-versus-pay practice is a drafting "
        f"convention: {TEARPOCK_QUOTE}")
    flags.append(f"no-grade: {NO_GRADE_NOTE}")
    if total_pay <= EPS:
        flags.append(
            "no-pay-intervals: the pay set is empty, so fraction_of_pay_perforated is "
            "reported as 0 by convention rather than computed. Every perforation "
            "below is outside pay by construction")
    if total_perf <= EPS:
        flags.append(
            "no-perforated-length: the perforation record is empty, so "
            "fraction_of_perf_in_pay is reported as 0 by convention rather than "
            "computed")

    tolerance_q = _q(
        tol, "ft", f"depth-registry tolerance [{STATUS_PROVISIONAL}]", ASQUITH_REGISTRY,
        inputs={"provenance": tolerance_provenance},
        assumptions={
            "status": STATUS_PROVISIONAL,
            "provenance": tolerance_provenance,
            "basis": ("asquith#64 p. 170: \"because a suite of logs generally requires "
                      "more than one logging 'run' out of the borehole, some logs "
                      "differ slightly in depth-registry of beds\". tool-catalog.md's "
                      "threshold table sets +/-2 ft on that basis - PROVISIONAL, with "
                      "basis - so the tolerance is set by log mechanics, not taste"),
            "corpus_alternative": CCL_QUOTE,
            "ccl_job_time_tolerance_ft": CCL_DEPTH_CONTROL_TOLERANCE_FT,
            "widen_when": "the runs on this well are known to disagree, or the "
                          "completion record is on tubing-measured or driller's depth",
            "applied": "expanded onto BOTH sets, each in favour of a match for its "
                       "own question; see tolerance_slack_ft"})

    return CompletionHistoryComparison(
        perforations=tuple(perf_records),
        pay=tuple(pay_records),
        pay_not_perforated=tuple(unperforated_all),
        perforations_outside_pay=tuple(outside_all),
        total_pay_ft=tq(total_pay, "ft", "sum of pay interval thickness"),
        total_perforated_ft=tq(total_perf, "ft",
                               "sum of perforated length, as recorded"),
        pay_perforated_ft=tq(pay_perforated, "ft", pay_method),
        pay_unperforated_ft=tq(pay_unperforated, "ft",
                               "total pay minus pay within +/-tol of a perforation"),
        perf_in_pay_ft=tq(perf_in_pay, "ft", perf_method),
        perf_outside_pay_ft=tq(perf_outside, "ft",
                               "total perforated length minus length within +/-tol of "
                               "pay"),
        tolerance_slack_ft=_q(slack, "ft",
                              "pay_perforated_ft - perf_in_pay_ft; the tolerance "
                              "applied in both directions, zero at tolerance 0", src,
                              inputs={"tolerance_ft": tol},
                              assumptions={"status": STATUS_UNSOURCED}),
        fraction_of_pay_perforated=_q(
            frac_pay, "v/v", "pay_perforated_ft / total_pay_ft", src,
            inputs={"pay_perforated_ft": pay_perforated, "total_pay_ft": total_pay},
            assumptions=ratio_assumptions),
        fraction_of_perf_in_pay=_q(
            frac_perf, "v/v", "perf_in_pay_ft / total_perforated_ft", src,
            inputs={"perf_in_pay_ft": perf_in_pay, "total_perforated_ft": total_perf},
            assumptions=ratio_assumptions),
        tolerance_ft=tolerance_q,
        tolerance_provenance=tolerance_provenance,
        datum_reference=datum_reference,
        cutoffs=applied,
        scan=scan,
        inputs={"perforated_intervals_ft": tuple(perfs),
                "pay_intervals_ft": tuple(pay_pairs),
                "depth_registry_tolerance_ft": tol,
                "min_thickness_ft": min_thickness_ft,
                "log_depth_reference": datum_reference,
                "perforation_depth_reference": datum_reference},
        assumptions={
            "comparison_rule": ("this build's, not published. Merged interval sets, "
                                "each expanded by the tolerance and intersected with "
                                "the other"),
            "comparison_status": STATUS_UNSOURCED,
            "tolerance_status": STATUS_PROVISIONAL,
            "tolerance_provenance": tolerance_provenance,
            "cutoff_source": (None if applied is None else applied.base.source),
            "cutoff_provenance": (None if applied is None else applied.provenance),
            "datum": ("resolved reference confirmed by the caller; both records "
                      f"declared on {datum_reference}"),
            "grading": NO_GRADE_NOTE,
            "outside_pay": ("reported with all three explanations attached and none "
                            "chosen: " + "; ".join(OUTSIDE_PAY_EXPLANATIONS)),
            "motivation": TEARPOCK_QUOTE,
        },
        flags=tuple(flags))


# --- the LAS entry point ---------------------------------------------------


def completion_history_compare_from_las(las_file: Any, **kwargs: Any):
    """Refuses. No LAS file carries a perforation record.

    Kept as a named entry point because the harness looks for one per tool, and
    because the refusal is the useful answer: it tells the caller the comparison
    needs the completion form, which is a different document class entirely. Both
    real fixtures were checked - neither contains "PERF", "SHOT", "CCL" or "SPF"
    anywhere in the file.
    """
    curves = sorted({str(c.mnemonic).strip().upper()
                     for c in getattr(las_file, "curves", ())})
    if kwargs.get("perforated_intervals_ft") is not None:
        # The caller brought the record from elsewhere; nothing to refuse about.
        return completion_history_compare(**kwargs)
    return Refusal(
        reason=("a LAS file carries no perforation record. The ~C section of this "
                f"file holds {', '.join(curves) or 'no curves'}, and the LAS "
                "specification has no place for a completion history: perforated "
                "intervals live on the completion form (a Texas W-2/G-1, a state "
                "completion report) or in the well file. Half of this comparison "
                "cannot come out of a log, so calling it with a log alone is a "
                "refusal, not a gap"),
        needed=("perforated_intervals_ft=[(top_ft, base_ft), ...] transcribed from "
                "the completion record",
                "pay_intervals_ft from net_pay_cutoffs (#39), or vsh/phi/sw curves "
                "plus a cutoff set - a raw LAS carries none of the three either",
                f"a resolved datum from {DATUM_RESOLVE} and the depth reference the "
                "completion record was measured on"),
        source=CATALOG_111)



# ======================================================================
# Tool #112 production_indicator
# ======================================================================

# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #

SWARM_ANCHOR = (
    "15-recompletion-screening/netl-advanced-technologies-stripper-gas-wells#0"
)

#: The document names the program twice and not identically: results bullet 1 says
#: "Stripper Well Remediation Methodology (SWARM)", the method paragraph says
#: "Stripper Well Analysis Remediation Methodology (SWARM)". The five-word form is
#: the one that fits the acronym and the one attached to the method statement.
SWARM_NAME = "Stripper Well Analysis Remediation Methodology (SWARM)"
SWARM_NAME_VARIANT = "Stripper Well Remediation Methodology (SWARM), results bullet 1"

#: The method, verbatim. Quoted rather than paraphrased because every clause of it
#: is a design decision below and a paraphrase loses the "and/or" and the "user
#: chooses", which are the two places this tool refuses instead of deciding.
SWARM_METHOD_QUOTE = (
    "The PC-based program developed under this project, Stripper Well Analysis "
    "Remediation Methodology (SWARM), utilizes cumulative production and normalized "
    "production rates (average monthly production for a desired year) as "
    '"indicators" or short-term gauges to assist in predicting long-term '
    "performance. Each of these indicators is related to date of first production "
    '(DOFP) and plots of "x-year" Cumulative Production vs. DOFP and/or Normalized '
    "Production Rate vs. DOFP, and are generated using input production data. The "
    "software generates indicators for every well within a field, and then compares "
    'each well with each offset within its "domain" (specified radius of '
    "investigation). The user chooses a target percentage of the production "
    "indicator (PI) of the wells in a given domain that a target well's PI must "
    "fall below in order to be recognized as a low-performer (e.g., 50 percent). "
    "The entire well list is processed and all qualifying target wells that meet "
    "the chosen criteria are listed."
)

#: The other direction, same paragraph.
SWARM_OVERPERFORMER_QUOTE = (
    'Although the primary objective of the program is to screen for underperformers, '
    'it is important to note that SWARM can also distinguish "overperformers," by '
    "selecting a user-defined percentage of 125 percent or 150 percent."
)

#: Why offsets are mandatory: the premise of the method is a local trend, so an
#: indicator computed against nothing is not an indicator.
SWARM_PREMISE_QUOTE = (
    "The approach in this project was to assume that general, localized production "
    "trends exist within a field, and that any abrupt change exhibited by an "
    "individual well relative to an established trend in its vicinity can be used "
    "to identify that well as a potential remediation candidate requiring "
    "additional study."
)

#: What the screen hands off to (`recompletion_rank`, #113). This tool does not
#: diagnose a cause and does not recommend a treatment.
SWARM_HANDOFF_QUOTE = (
    "After this phase is completed, a review of each selected candidate well's "
    "completion data, geologic information, production history, and operating "
    "environment should be conducted to determine the most likely cause for its "
    "relatively poorer performance. The appropriate remediation treatment can then "
    "be recommended, based on the economics of the situation."
)

METHOD_CUMULATIVE = 'SWARM "x-year" cumulative production, measured from date of first production'
METHOD_RATE = (
    "SWARM normalized production rate (average monthly production for a desired "
    "year of producing life)"
)
METHOD_DOMAIN = "SWARM domain aggregate of offset production indicators"
METHOD_RATIO = "SWARM production indicator as a percentage of the domain indicator"

# --------------------------------------------------------------------------- #
# Constants and vocabularies. No threshold here: the source fixes none.
# --------------------------------------------------------------------------- #

#: Months in one year of producing life. The divisor in the normalized rate, and
#: the window length multiplier in the x-year cumulative. Not a tunable.
MONTHS_PER_YEAR = 12

INDICATOR_CUMULATIVE = "cumulative"
INDICATOR_RATE = "normalized_rate"
INDICATORS = (INDICATOR_CUMULATIVE, INDICATOR_RATE)

STATISTIC_MEAN = "mean"
STATISTIC_MEDIAN = "median"
STATISTICS = (STATISTIC_MEAN, STATISTIC_MEDIAN)

#: Verdicts. Exactly one of these rides on `ratio_percent.flags`; #113 reads it.
LOW_PERFORMER = "low_performer"
OVER_PERFORMER = "over_performer"
WITHIN_TREND = "within_domain_trend"

#: The percentage at which the source's two screens meet. Below it the source says
#: the PI "must fall below" the target percentage; above it ("125 percent or 150
#: percent") the screen is for overperformers. Exactly 100 is not stated either way.
SCREEN_PIVOT_PERCENT = 100.0

#: Advisory only, never a refusal. "an established trend in its vicinity" is the
#: source's premise; one offset is a comparison but not a trend. No minimum domain
#: size is printed anywhere, so nothing is enforced from it.
FLAG_SINGLE_OFFSET = "single_offset_domain"
FLAG_PIVOT = "pi_percent_at_100_direction_assumed"

#: Month index 1 is the calendar month CONTAINING the DOFP, so it can be partial.
#: The source does not discuss proration and none is applied. Stated on results.
PARTIAL_FIRST_MONTH_NOTE = (
    "producing-month index 1 is the calendar month containing DOFP and may be a "
    "partial month; the source describes no proration and none is applied"
)

# Where a real SWARM run gets its coordinates. Not a formula, and never used in
# arithmetic: it exists to be quoted in the refusal when a caller tries to feed
# this tool from LAS headers, which carry no coordinate at all.
RRC_LATLON_FIELD = "09-gas-deliverability/rrc-section-f-completions-electric-logs#2"
RRC_LATLON_NOTE = (
    "well coordinates come from RRC Form W-2/G-1 field 6, 'Well Latitude/Longitude "
    "(minimum five decimal places required)' with its separate 'Latitude/Longitude "
    "type:' field; LAS headers in this corpus carry a survey footage call and no "
    "coordinate, so a radius query cannot be fed from a log"
)


# --------------------------------------------------------------------------- #
# Input records
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class WellProduction:
    """One well's production history, its DOFP and its location.

    `dofp` has no default and no derivation. It is tempting to take the first month
    in `monthly` as the date of first production, and it is wrong: a history handed
    to this tool routinely starts after first production (records bought with the
    well, a regulator's filings that begin mid-life, a series trimmed by an export).
    Assuming the first row is month 1 shifts the producing-age window for that well
    only, which is precisely the comparison the method depends on. So it refuses.
    """

    name: str
    dofp: date | None = None
    monthly: tuple[tuple[tuple[int, int], float], ...] = ()
    volume_unit: str = ""
    location: Any = None


def _as_month(value: Any, well: str) -> tuple[int, int]:
    """Coerce a month label to (year, month). Bad shapes are programmer error."""
    if isinstance(value, datetime):
        return (value.year, value.month)
    if isinstance(value, date):
        return (value.year, value.month)
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        return (int(value[0]), int(value[1]))
    if isinstance(value, str):
        text = value.strip()
        parts = text.replace("/", "-").split("-")
        if len(parts) >= 2:
            try:
                return (int(parts[0]), int(parts[1]))
            except ValueError:
                pass
    raise ValueError(f"{well}: cannot read {value!r} as a production month")


def _as_dofp(value: Any, well: str) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        return date(int(value[0]), int(value[1]), int(value[2]) if len(value) > 2 else 1)
    if isinstance(value, str):
        text = value.strip().replace("/", "-")
        parts = text.split("-")
        try:
            if len(parts) == 2:
                return date(int(parts[0]), int(parts[1]), 1)
            if len(parts) >= 3:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            pass
    raise ValueError(f"{well}: cannot read {value!r} as a date of first production")


def _as_well(obj: Any, label: str) -> WellProduction:
    if isinstance(obj, WellProduction):
        name = obj.name or label
        monthly = tuple(
            (_as_month(m, name), float(v)) for m, v in _iter_monthly(obj.monthly, name)
        )
        return WellProduction(
            name=name,
            dofp=_as_dofp(obj.dofp, name),
            monthly=monthly,
            volume_unit=obj.volume_unit,
            location=obj.location,
        )
    if isinstance(obj, Mapping):
        name = str(obj.get("name", label))
        monthly = tuple(
            (_as_month(m, name), float(v))
            for m, v in _iter_monthly(obj.get("monthly", ()), name)
        )
        return WellProduction(
            name=name,
            dofp=_as_dofp(obj.get("dofp"), name),
            monthly=monthly,
            volume_unit=str(obj.get("volume_unit", "") or ""),
            location=obj.get("location"),
        )
    raise TypeError(
        f"{label} must be a WellProduction or a mapping, got {type(obj).__name__}"
    )


def _iter_monthly(monthly: Any, well: str) -> Iterable[tuple[Any, Any]]:
    """Accept a mapping {month: volume} or a sequence of (month, volume) pairs."""
    if monthly is None:
        return ()
    if isinstance(monthly, Mapping):
        return list(monthly.items())
    if isinstance(monthly, Sequence) and not isinstance(monthly, (str, bytes)):
        out = []
        for row in monthly:
            if not isinstance(row, Sequence) or isinstance(row, (str, bytes)) or len(row) < 2:
                raise ValueError(f"{well}: production row {row!r} is not (month, volume)")
            out.append((row[0], row[1]))
        return out
    raise TypeError(f"{well}: monthly must be a mapping or a sequence of pairs")


# --------------------------------------------------------------------------- #
# Producing-age arithmetic
# --------------------------------------------------------------------------- #


def producing_month_index(dofp: date, month: tuple[int, int]) -> int:
    """1-based month of producing life: the DOFP month is 1.

    i = 12*(y - y0) + (m - m0) + 1
    """
    return MONTHS_PER_YEAR * (month[0] - dofp.year) + (month[1] - dofp.month) + 1


def _indexed(well: WellProduction) -> dict[int, float]:
    return {producing_month_index(well.dofp, m): v for m, v in well.monthly}


def _missing_months(series: dict[int, float], first: int, last: int) -> list[int]:
    return [i for i in range(first, last + 1) if i not in series]


def _negative_months(series: dict[int, float], first: int, last: int) -> list[int]:
    return [i for i in range(first, last + 1) if series.get(i, 0.0) < 0.0]


def _window_gate(well: WellProduction, first: int, last: int, what: str) -> Refusal | None:
    """The per-well data gate, shared by both indicators.

    Every branch names the well. A well that cannot produce an indicator is never
    dropped from the comparison set: the set is what the answer is relative to, so
    quietly shrinking it changes the verdict with nothing on screen to show for it.
    """
    if well.dofp is None:
        return Refusal(
            reason=(
                f"{well.name} has no date of first production, so its {what} has no "
                "producing-age window. The SWARM indicators are defined from DOFP "
                "('Each of these indicators is related to date of first production "
                "(DOFP)'), and this well cannot be silently excluded: the offset set "
                "is what the target is measured against."
            ),
            needed=(f"date of first production for {well.name}",),
            source=SWARM_ANCHOR,
        )
    if not well.monthly:
        return Refusal(
            reason=(
                f"{well.name} has no monthly production history, so no {what} can be "
                "computed. Excluding it would change the comparison set."
            ),
            needed=(f"monthly production history for {well.name}",),
            source=SWARM_ANCHOR,
        )
    series = _indexed(well)
    missing = _missing_months(series, first, last)
    if missing:
        return Refusal(
            reason=(
                f"{well.name} is missing {len(missing)} of the {last - first + 1} "
                f"months of its {what} window (producing months {first}-{last}; first "
                f"missing is month {missing[0]}). A truncated window understates the "
                "indicator by truncation alone, which is a wrong number rather than "
                "an approximate one."
            ),
            needed=(
                f"production for producing months {first}-{last} of {well.name} "
                f"(DOFP {well.dofp.isoformat()})",
            ),
            source=SWARM_ANCHOR,
        )
    negative = _negative_months(series, first, last)
    if negative:
        return Refusal(
            reason=(
                f"{well.name} has negative production in producing month(s) "
                f"{negative[:5]}. Negative monthly volumes are corrections or errors; "
                "summing them silently understates the indicator, so the caller "
                "decides what they mean."
            ),
            needed=(f"non-negative monthly volumes for {well.name}",),
            source=SWARM_ANCHOR,
        )
    return None


# --------------------------------------------------------------------------- #
# The two indicators
# --------------------------------------------------------------------------- #


def cumulative_indicator(well: Any, *, window_years: int | None) -> Quantity | Refusal:
    """SWARM indicator 1: "x-year" Cumulative Production, x = `window_years`.

    Summed over producing months 1 .. 12x, i.e. the first x years of the well's
    life, NOT the first x calendar years and NOT lifetime-to-date.
    """
    w = _as_well(well, "well")
    if window_years is None:
        return Refusal(
            reason=(
                'the x in "x-year Cumulative Production" is the user\'s and the '
                "source fixes no value; state window_years"
            ),
            needed=("window_years (years of producing life)",),
            source=SWARM_ANCHOR,
        )
    if int(window_years) < 1:
        raise ValueError(f"window_years must be >= 1, got {window_years!r}")
    last = MONTHS_PER_YEAR * int(window_years)
    gate = _window_gate(w, 1, last, f"{window_years}-year cumulative production")
    if gate is not None:
        return gate
    series = _indexed(w)
    total = math.fsum(series[i] for i in range(1, last + 1))
    return Quantity(
        value=total,
        unit=w.volume_unit,
        method=METHOD_CUMULATIVE,
        source=SWARM_ANCHOR,
        inputs={
            "well": w.name,
            "dofp": w.dofp.isoformat(),
            "window_years": int(window_years),
            "producing_months": (1, last),
        },
        assumptions={
            "window": "producing months 1..12x counted from DOFP, not calendar years",
            "partial_first_month": PARTIAL_FIRST_MONTH_NOTE,
            "quote": SWARM_METHOD_QUOTE,
        },
    )


def normalized_rate_indicator(well: Any, *, year: int | None) -> Quantity | Refusal:
    """SWARM indicator 2: "average monthly production for a desired year".

    `year` is the year of PRODUCING LIFE (1 = the first twelve months from DOFP),
    which is what makes wells of different vintage comparable.

    The divisor is twelve, not "months present". A year's production spread over a
    year is what the source's phrase means; a month absent from the record is a
    data gap and has already refused in the gate, while a month present and zero is
    a real shut-in month and belongs in the average as a zero.
    """
    w = _as_well(well, "well")
    if year is None:
        return Refusal(
            reason=(
                'the "desired year" of the normalized production rate is the user\'s '
                "and the source fixes no value; state normalized_year"
            ),
            needed=("normalized_year (1-based year of producing life)",),
            source=SWARM_ANCHOR,
        )
    if int(year) < 1:
        raise ValueError(f"year must be >= 1 (1 = first year of producing life), got {year!r}")
    first = MONTHS_PER_YEAR * (int(year) - 1) + 1
    last = MONTHS_PER_YEAR * int(year)
    gate = _window_gate(w, first, last, f"year-{year} normalized rate")
    if gate is not None:
        return gate
    series = _indexed(w)
    total = math.fsum(series[i] for i in range(first, last + 1))
    return Quantity(
        value=total / MONTHS_PER_YEAR,
        unit=f"{w.volume_unit}/month" if w.volume_unit else "per month",
        method=METHOD_RATE,
        source=SWARM_ANCHOR,
        inputs={
            "well": w.name,
            "dofp": w.dofp.isoformat(),
            "producing_year": int(year),
            "producing_months": (first, last),
            "year_total": total,
        },
        assumptions={
            "divisor": f"{MONTHS_PER_YEAR} months, not months-present",
            "zero_months": "a reported zero month is a real zero and averages in",
            "partial_first_month": PARTIAL_FIRST_MONTH_NOTE,
            "quote": SWARM_METHOD_QUOTE,
        },
    )


_INDICATOR_FUNCS = {
    INDICATOR_CUMULATIVE: "cumulative_indicator",
    INDICATOR_RATE: "normalized_rate_indicator",
}


def _indicator_for(well: WellProduction, indicator: str, window_years: Any,
                   normalized_year: Any) -> Quantity | Refusal:
    if indicator == INDICATOR_CUMULATIVE:
        return cumulative_indicator(well, window_years=window_years)
    return normalized_rate_indicator(well, year=normalized_year)


# --------------------------------------------------------------------------- #
# The domain: offsets within the specified radius of investigation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DomainMember:
    """One offset that passed the radius test, with the distance that admitted it."""

    well: WellProduction
    distance: Quantity


def domain_within_radius(target: Any, offsets: Sequence[Any], *, radius: float | None,
                         radius_unit: str = "ft") -> list[DomainMember] | Refusal:
    """Offsets inside the target's "domain (specified radius of investigation)".

    Distance is `offset_geometry` (#19) and nothing else. That tool owns the
    coordinate-frame gate (declared CRS, matching datum and zone, a declared point
    on each well, survey calls rejected as not-coordinates), and its refusal is
    propagated verbatim rather than re-decided here.
    """
    t = _as_well(target, "target")
    members: list[DomainMember] = []
    nearest: tuple[str, float] | None = None
    for i, off in enumerate(offsets):
        o = _as_well(off, f"offset[{i}]")
        if t.location is None or o.location is None:
            missing = t.name if t.location is None else o.name
            return Refusal(
                reason=(
                    f"{missing} has no location, so the domain (the "
                    '"specified radius of investigation") cannot be formed. '
                    + RRC_LATLON_NOTE
                ),
                needed=(f"a declared coordinate and CRS for {missing}",),
                source=SWARM_ANCHOR,
            )
        geom = offset_geometry(t.location, o.location, distance_unit=radius_unit)
        if isinstance(geom, Refusal):
            return Refusal(
                reason=(
                    f"cannot place {o.name} relative to {t.name}, so the domain "
                    f"cannot be formed: {geom.reason}"
                ),
                needed=geom.needed or (f"resolvable coordinates for {t.name} and {o.name}",),
                source=geom.source or SWARM_ANCHOR,
            )
        distance = geom["distance"]
        if isinstance(distance, Refusal):  # defensive; #19 returns a bare Refusal instead
            return distance
        d = float(distance.value)
        if nearest is None or d < nearest[1]:
            nearest = (o.name, d)
        if d <= float(radius):
            members.append(DomainMember(well=o, distance=distance))
    if not members:
        near = (
            f" Nearest offset is {nearest[0]} at {nearest[1]:.6g} {radius_unit}."
            if nearest else ""
        )
        return Refusal(
            reason=(
                f"no offset falls within {radius:g} {radius_unit} of {t.name}, so "
                "there is no domain to compare against. The SWARM indicator is "
                "relative: it 'compares each well with each offset within its "
                "domain (specified radius of investigation)'." + near
            ),
            needed=("offsets inside the radius, or a larger radius",),
            source=SWARM_ANCHOR,
        )
    return members


# --------------------------------------------------------------------------- #
# The screen
# --------------------------------------------------------------------------- #


# _median is defined once, above with #110's helpers. #112 shipped its own copy
# and, being later in the merged module, it shadowed the first one for every
# caller - silently dropping the empty-sequence ValueError that #110 relies on,
# so an empty input raised IndexError instead. One definition, guard kept.


def _aggregate(values: Sequence[float], statistic: str) -> float:
    if statistic == STATISTIC_MEAN:
        return math.fsum(values) / len(values)
    return _median(values)


def _classify(ratio_percent: float, pi_percent: float) -> tuple[str, str]:
    """Verdict and the direction of the screen, both from the source's wording.

    Below the pivot the source is explicit that the PI "must fall below" the chosen
    percentage, so the test is strict. Above it ("125 percent or 150 percent") the
    source gives no operator at all; `>=` is used and the choice is flagged.
    """
    if pi_percent > SCREEN_PIVOT_PERCENT:
        direction = "overperformer screen: flagged at or above the chosen percentage"
        return (OVER_PERFORMER if ratio_percent >= pi_percent else WITHIN_TREND, direction)
    direction = 'low-performer screen: flagged strictly below ("must fall below")'
    return (LOW_PERFORMER if ratio_percent < pi_percent else WITHIN_TREND, direction)


def production_indicator(
    target: Any,
    offsets: Sequence[Any] | None,
    *,
    indicator: str | None = None,
    radius: float | None = None,
    radius_unit: str = "ft",
    pi_percent: float | None = None,
    domain_statistic: str | None = None,
    window_years: int | None = None,
    normalized_year: int | None = None,
    min_offsets: int | None = None,
) -> dict[str, Quantity | Range] | Refusal:
    """SWARM: one well's production indicator against its offsets in a radius (#112).

    Returns either a single `Refusal` (the screen cannot be run) or a dict:

        {"indicator": Quantity,          # the target's PI
         "domain_indicator": Quantity,   # the offsets' PI, aggregated
         "offset_indicators": Range,     # spread across offsets, members per well
         "ratio_percent": Quantity}      # 100 * target/domain; verdict in .flags

    `ratio_percent.flags` carries exactly one of `low_performer`, `over_performer`
    or `within_domain_trend`. That flag is the "hit" `recompletion_rank` (#113)
    consumes; this tool screens and stops there, because the source hands the cause
    and the treatment to a later review step.
    """
    # --- R1: the method is a comparison, so offsets are not optional -----------
    if not offsets:
        return Refusal(
            reason=(
                "no offset wells supplied. The SWARM production indicator is defined "
                "only relative to offsets: " + SWARM_PREMISE_QUOTE + " Without "
                "offsets this would return a production number, not an indicator."
            ),
            needed=("at least one offset well with a location, DOFP and history",),
            source=SWARM_ANCHOR,
        )

    # --- R2-R6: everything the source leaves to the user ----------------------
    if indicator is None:
        return Refusal(
            reason=(
                "no indicator chosen. The source offers two and joins them with "
                '"and/or": "x-year" Cumulative Production and Normalized Production '
                "Rate. They are separate screens over the same offsets and are never "
                f"blended; choose one of {INDICATORS}."
            ),
            needed=(f"indicator, one of {INDICATORS}",),
            source=SWARM_ANCHOR,
        )
    if indicator not in INDICATORS:
        raise ValueError(f"indicator must be one of {INDICATORS}, got {indicator!r}")
    if radius is None:
        return Refusal(
            reason=(
                'no radius supplied. The source says the domain is a "specified '
                'radius of investigation" and prints no distance, no default and no '
                "units anywhere in the corpus, so the radius is the caller's."
            ),
            needed=(f"radius (in {radius_unit})",),
            source=SWARM_ANCHOR,
        )
    if float(radius) <= 0.0:
        raise ValueError(f"radius must be positive, got {radius!r}")
    if pi_percent is None:
        return Refusal(
            reason=(
                "no PI percentage supplied. \"The user chooses a target percentage of "
                "the production indicator (PI) of the wells in a given domain that a "
                "target well's PI must fall below\"; 50, 125 and 150 are the source's "
                "examples, not defaults."
            ),
            needed=("pi_percent (percent of the domain indicator)",),
            source=SWARM_ANCHOR,
        )
    if domain_statistic is None:
        return Refusal(
            reason=(
                'the source says "the production indicator (PI) of the wells in a '
                'given domain" without naming a statistic, so mean and median are '
                "both readable and they disagree on real data; state "
                f"domain_statistic as one of {STATISTICS}."
            ),
            needed=(f"domain_statistic, one of {STATISTICS}",),
            source=SWARM_ANCHOR,
        )
    if domain_statistic not in STATISTICS:
        raise ValueError(f"domain_statistic must be one of {STATISTICS}, got {domain_statistic!r}")
    if indicator == INDICATOR_CUMULATIVE and window_years is None:
        return Refusal(
            reason=(
                'the x in "x-year Cumulative Production" is the user\'s; the source '
                "fixes no number of years. A default would silently change the "
                "producing-age window and so the verdict."
            ),
            needed=("window_years",),
            source=SWARM_ANCHOR,
        )
    if indicator == INDICATOR_RATE and normalized_year is None:
        return Refusal(
            reason=(
                'the normalized production rate is the "average monthly production '
                'for a desired year" and the source fixes no year. A default would '
                "silently change which year of producing life is compared."
            ),
            needed=("normalized_year (1-based year of producing life)",),
            source=SWARM_ANCHOR,
        )

    t = _as_well(target, "target")
    offs = [_as_well(o, f"offset[{i}]") for i, o in enumerate(offsets)]

    # --- R7: units, before any arithmetic -------------------------------------
    units = {w.volume_unit for w in [t] + offs}
    if len(units) > 1:
        return Refusal(
            reason=(
                "production volumes are reported in different units across the wells "
                f"({sorted(units)!r}). A ratio across mixed units is wrong by the "
                "conversion factor and looks entirely plausible."
            ),
            needed=("one volume unit for the target and every offset",),
            source=SWARM_ANCHOR,
        )
    unit = t.volume_unit

    # --- R8, R9: the domain ---------------------------------------------------
    members = domain_within_radius(t, offs, radius=radius, radius_unit=radius_unit)
    if isinstance(members, Refusal):
        return members

    # --- R10: the caller's own floor -----------------------------------------
    if min_offsets is not None and len(members) < int(min_offsets):
        return Refusal(
            reason=(
                f"{len(members)} offset(s) inside {radius:g} {radius_unit}, fewer than "
                f"the {int(min_offsets)} the caller requires. The source prints no "
                "minimum domain size, so this floor is the caller's, not the method's."
            ),
            needed=(f"at least {int(min_offsets)} offsets inside the radius",),
            source=SWARM_ANCHOR,
        )

    # --- R11-R14: per-well indicators, refusing by name ----------------------
    target_pi = _indicator_for(t, indicator, window_years, normalized_year)
    if isinstance(target_pi, Refusal):
        return target_pi

    offset_pis: dict[str, float] = {}
    distances: dict[str, float] = {}
    for m in members:
        pi = _indicator_for(m.well, indicator, window_years, normalized_year)
        if isinstance(pi, Refusal):
            return pi  # names the well; never silently dropped from the domain
        offset_pis[m.well.name] = float(pi.value)
        distances[m.well.name] = float(m.distance.value)

    values = list(offset_pis.values())
    domain_value = _aggregate(values, domain_statistic)

    common_inputs = {
        "target": t.name,
        "offsets_in_domain": sorted(offset_pis),
        "offset_distances": {k: distances[k] for k in sorted(distances)},
        "radius": float(radius),
        "radius_unit": radius_unit,
        "indicator": indicator,
        "window_years": int(window_years) if window_years is not None else None,
        "normalized_year": int(normalized_year) if normalized_year is not None else None,
        "domain_statistic": domain_statistic,
        "dofp": {w.name: w.dofp.isoformat() for w in [t] + [m.well for m in members]},
    }
    pi_unit = target_pi.unit

    domain_quantity = Quantity(
        value=domain_value,
        unit=pi_unit,
        method=f"{METHOD_DOMAIN} ({domain_statistic} of {len(values)} offsets)",
        source=SWARM_ANCHOR,
        inputs={**common_inputs, "offset_indicators": dict(sorted(offset_pis.items()))},
        assumptions={
            "statistic": (
                "the source says 'the production indicator (PI) of the wells in a "
                "given domain' and does not name a statistic; this is the caller's "
                "declared choice, not a default"
            ),
            "distance_source": "offset_geometry (#19), planar or great-circle per the declared CRS",
        },
    )

    offset_range = Range(
        low=min(values),
        high=max(values),
        unit=pi_unit,
        method=f"per-offset {METHOD_CUMULATIVE if indicator == INDICATOR_CUMULATIVE else METHOD_RATE}",
        source=SWARM_ANCHOR,
        members=dict(sorted(offset_pis.items())),
        inputs=dict(common_inputs),
        assumptions={
            "members": "one entry per offset inside the radius, keyed by well name",
            "partial_first_month": PARTIAL_FIRST_MONTH_NOTE,
        },
    )

    # --- R15: the ratio -------------------------------------------------------
    if domain_value == 0.0:
        return Refusal(
            reason=(
                f"the domain indicator is zero ({domain_statistic} of "
                f"{len(values)} offsets), so the target's percentage of it is "
                "undefined. A domain of dead offsets is not an established trend."
            ),
            needed=("offsets with non-zero production in the indicator window",),
            source=SWARM_ANCHOR,
        )

    ratio = 100.0 * float(target_pi.value) / domain_value
    verdict, direction = _classify(ratio, float(pi_percent))

    flags: list[str] = [verdict]
    if len(members) == 1:
        flags.append(FLAG_SINGLE_OFFSET)
    if float(pi_percent) == SCREEN_PIVOT_PERCENT:
        flags.append(FLAG_PIVOT)

    ratio_quantity = Quantity(
        value=ratio,
        unit="%",
        method=METHOD_RATIO,
        source=SWARM_ANCHOR,
        inputs={
            **common_inputs,
            "target_indicator": float(target_pi.value),
            "domain_indicator": domain_value,
            "pi_percent": float(pi_percent),
        },
        assumptions={
            "screen_direction": direction,
            "pivot": (
                "percentages at or below 100 screen for low performers ('must fall "
                "below'); above 100 they screen for overperformers ('125 percent or "
                "150 percent'). Exactly 100 is not stated either way and is treated "
                "as the low screen, flagged."
            ),
            "single_offset": (
                "one offset is a comparison but not the 'established trend in its "
                "vicinity' the method assumes"
            ) if len(members) == 1 else None,
            "normalisation": (
                "both indicators are measured from each well's own DOFP, so wells of "
                "different vintage are compared at equal producing age rather than "
                "equal calendar date"
            ),
            "swarm": SWARM_NAME,
            "handoff": SWARM_HANDOFF_QUOTE,
        },
        flags=tuple(flags),
    )

    return {
        "indicator": target_pi,
        "domain_indicator": domain_quantity,
        "offset_indicators": offset_range,
        "ratio_percent": ratio_quantity,
    }


def production_indicator_both(
    target: Any,
    offsets: Sequence[Any] | None,
    **kwargs: Any,
) -> dict[str, dict[str, Quantity | Range] | Refusal]:
    """The "and" branch of the source's "and/or": run both indicators, side by side.

    Returned as two independent screens under `"cumulative"` and
    `"normalized_rate"`, never merged into one score. Nothing in the source combines
    them, and a weighted blend would be an invented method: they can legitimately
    disagree, and that disagreement (strong early cumulative, weak current rate) is
    information the reviewer is supposed to see.
    """
    kwargs.pop("indicator", None)
    return {
        INDICATOR_CUMULATIVE: production_indicator(
            target, offsets, indicator=INDICATOR_CUMULATIVE, **kwargs
        ),
        INDICATOR_RATE: production_indicator(
            target, offsets, indicator=INDICATOR_RATE, **kwargs
        ),
    }



# ======================================================================
# Tool #113 recompletion_rank
# ======================================================================

# --- anchors ---------------------------------------------------------------

NETL_MIDCONTINENT = (
    "15-recompletion-screening/netl-stripper-gas-well-selection-midcontinent#0"
)
NETL_SWARM = (
    "15-recompletion-screening/netl-advanced-technologies-stripper-gas-wells#0"
)
CATALOG_113 = "tool-catalog.md, section 17, recompletion_rank [#113]"
# CATALOG_THRESHOLDS is declared once, at the top of this module.


#: The document's own dates. Everything monetary below is in these dollars.
STUDY_PERIOD = "project start 08/08/2000, project end 09/30/2003"
STUDY_FIELD = "Mocane-Laverne field, central Anadarko basin, Oklahoma (Oneok Resources)"
STUDY_PRECEDENT = (
    "builds on GRI work of the late 1990s and a tight-sand restimulation "
    "demonstration concluded in 2001 that added 2.9 Bcf at an average cost of "
    "$0.26/Mcf"
)

# --- the criteria list, verbatim -------------------------------------------

#: The one sentence that defines every criterion a candidate can hit. The hit
#: count is meaningless without it, so it is carried on every criterion below
#: and on every result this module returns.
CRITERIA_SENTENCE = (
    "The criteria for selection included the results of the data exploration, "
    "the type-curve analysis, the artificial intelligence analysis, and also the "
    "most recent producing rate (prior R&D indicated that the better the most "
    "recent rate, the better the candidate a well is for production enhancement)."
)

#: The sentence is stated as *open* - "included" - and names four things. Four is
#: taken as the published, closed-by-default set; an extension must be declared
#: by the caller and flags every result built on it, because >=4/>=3 were
#: calibrated against these four over that well population.
CRITERIA_SET_IS_OPEN = (
    'the source says the criteria "included" these four and names no others; a '
    "fifth would make the A list attainable without hitting everything"
)


@dataclass(frozen=True)
class Criterion:
    """One criterion a candidate can hit, with the sentence it comes from."""

    key: str
    label: str          # as the source names it
    quote: str          # the sentence, or the clause defining a hit
    source: str
    operational: str    # what the source says a hit *is*, or "" when it says nothing
    published: bool = True

    @property
    def has_operational_definition(self) -> bool:
        return bool(self.operational)


SELECTION_CRITERIA: tuple[Criterion, ...] = (
    Criterion(
        key="data_exploration",
        label="the results of the data exploration",
        quote=CRITERIA_SENTENCE,
        source=NETL_MIDCONTINENT,
        operational="",  # the source names the analysis and never defines its verdict
    ),
    Criterion(
        key="type_curve",
        label="the type-curve analysis",
        quote=CRITERIA_SENTENCE,
        source=NETL_MIDCONTINENT,
        operational=(
            "a well performance cross-plot was created to relate normalized well "
            "performance (ultimate recovery divided by reservoir drawdown) to a "
            "reservoir volume and transmissibility function (the product of "
            "effective reservoir volume and permeability. This resulted in a "
            "simple model of well performance, with wells falling below the trend "
            "line highlighted as sub-performers."
        ),
    ),
    Criterion(
        key="artificial_intelligence",
        label="the artificial intelligence analysis",
        quote=CRITERIA_SENTENCE,
        source=NETL_MIDCONTINENT,
        operational=(
            "The magnitude of any differences between actual well performance "
            "(EUR) and predicted performance with optimized stimulation "
            "parameters was the ranking criteria for restimulation opportunity."
        ),
    ),
    Criterion(
        key="recent_rate",
        label="the most recent producing rate",
        quote=CRITERIA_SENTENCE,
        source=NETL_MIDCONTINENT,
        operational=(
            "prior R&D indicated that the better the most recent rate, the better "
            "the candidate a well is for production enhancement"
        ),
    ),
)

PUBLISHED_CRITERIA_KEYS: tuple[str, ...] = tuple(c.key for c in SELECTION_CRITERIA)

# --- the published thresholds ----------------------------------------------

#: "Based on these criteria, two lists were created: the "A" list represented
#: wells that had at least four "hits" of the above criteria, and the "B" list
#: were wells with at least three "hits" each. List A had 5 wells and list B had
#: 17 wells."
LIST_SENTENCE = (
    'Based on these criteria, two lists were created: the "A" list represented '
    'wells that had at least four "hits" of the above criteria, and the "B" list '
    'were wells with at least three "hits" each. List A had 5 wells and list B '
    "had 17 wells."
)

A_LIST_MIN_HITS = 4   # "at least four hits"
B_LIST_MIN_HITS = 3   # "at least three hits each"

#: What the study itself produced, for a caller comparing their own run to it.
PUBLISHED_LIST_COUNTS = {"A": 5, "B": 17}
PUBLISHED_TOP_PRIORITY_COUNTS = {"A": 1, "B": 6}

#: "two lists were created" with counts 5 and 17 reads exclusive; "at least three
#: hits each" reads inclusive. Taken as exclusive, A first. Spec open question 6.
B_LIST_INCLUDES_A = False

#: Four published criteria and an A list at ">=4" means an A placement is
#: necessarily fully evaluated. The unevaluated problem bites the B list and any
#: extended set, not the A list.
A_LIST_IMPLIES_FULLY_EVALUATED = len(SELECTION_CRITERIA) == A_LIST_MIN_HITS

# --- within-list prioritization (reported, never scored) --------------------

PRIORITY_SENTENCE = (
    "Within each candidate group the wells were further prioritized based on the "
    "presence of an unstimulated horizon in the well, the rank within the top 45 "
    "based on both artificial intelligence and most recent producing rate, and "
    "rank within the top 30 for at least one of the above criteria."
)

TOP45_RANK = 45
TOP30_RANK = 30


@dataclass(frozen=True)
class PriorityFactor:
    key: str
    label: str
    quote: str
    source: str


PRIORITY_FACTORS: tuple[PriorityFactor, ...] = (
    PriorityFactor("unstimulated_horizon",
                   "the presence of an unstimulated horizon in the well",
                   PRIORITY_SENTENCE, NETL_MIDCONTINENT),
    PriorityFactor("top45_ai_and_recent_rate",
                   "the rank within the top 45 based on both artificial "
                   "intelligence and most recent producing rate",
                   PRIORITY_SENTENCE, NETL_MIDCONTINENT),
    PriorityFactor("top30_any",
                   "rank within the top 30 for at least one of the above criteria",
                   PRIORITY_SENTENCE, NETL_MIDCONTINENT),
)

#: The source gives three factors, then reports that "certain wells (one in list A
#: and six in list B) were highlighted as the top priority candidates". 1 of 5 and
#: 6 of 17 is consistent with all-three, with any-two, and with judgment. No
#: `top_priority` boolean is emitted and no ordering is drawn from these.
PRIORITY_COMBINATION_UNSTATED = (
    "the source does not state how the three prioritization factors combine; each "
    "is reported and none is scored"
)

#: 45 and 30 are absolute ranks over the study population - Oneok "operates over
#: 100 wells in the field", and the ANN models used 61+31 and 9+4 wells. They do
#: not transfer to a candidate set of six.
RANK_CUTOFFS_ARE_POPULATION_BOUND = (
    "the top-45 and top-30 cutoffs are absolute ranks over a study population of "
    "roughly a hundred wells; nothing in the source states them as a fraction"
)

# --- the economic benchmark (an outcome test, not a criterion) --------------

BENCHMARK_SENTENCE = (
    'Workovers on the two selected candidates were considered "successful" based '
    "on the benchmark of an added reserve cost of < $0.50/Mcfe. The other four "
    'were deemed "unsuccessful" by the same measure. The two candidate wells '
    "provided almost 1 Bcf of added reserves as a result of the workovers at a "
    "cost of about $20,000, for an average reserve cost of < $0.02/Mcfe."
)

#: US$ per Mcfe of *added reserve*: workover cost divided by the reserves that
#: workover added. Not a finding cost, not a development cost, not an operating
#: cost. Overridable, and it carries its vintage everywhere it goes.
ADDED_RESERVE_COST_BENCHMARK_USD_PER_MCFE = 0.50

BENCHMARK_IS_STRICT = True  # the source writes "< $0.50/Mcfe", not "<="

BENCHMARK_VINTAGE = (
    f"$0.50/Mcfe is a {STUDY_PERIOD} dollar figure ({STUDY_PRECEDENT}). It is NOT "
    "inflation-adjusted and the corpus supplies no deflator, index or escalation "
    "to any later year, so none is applied. Override "
    "`benchmark_usd_per_mcfe` with a number of your own vintage if you need one"
)

BENCHMARK_IS_EX_POST = (
    "the < $0.50/Mcfe benchmark is how the source judged six workovers that had "
    "already happened, in order to validate the selection procedure. It is an "
    "outcome test, not a selection criterion: it never enters the hit count and "
    "never orders a list"
)

#: The source's own caveat on its validation, carried on every benchmark result.
BENCHMARK_VALIDATION_CAVEAT = (
    "An aspect of these results that must be considered is that the workovers "
    'performed on the four "non-candidate" wells were not identical to those '
    "performed on the candidate wells."
)

#: The two worked examples the document publishes, kept for the oracle.
PUBLISHED_COST_EXAMPLES = {
    "midcontinent_candidates": {
        "workover_cost_usd": 20_000.0,       # "a cost of about $20,000"
        "added_reserves_mcfe": 1_000_000.0,  # "almost 1 Bcf"
        "published_usd_per_mcfe": 0.02,      # "< $0.02/Mcfe"
        "source": NETL_MIDCONTINENT,
    },
    "gri_tight_sand_demo": {
        "added_reserves_mcfe": 2_900_000.0,  # "2.9 Bcf of reserves"
        "published_usd_per_mcfe": 0.26,      # "an average cost of $0.26/Mcf"
        "source": NETL_MIDCONTINENT,
    },
}

# --- verdict vocabulary -----------------------------------------------------

HIT = "hit"
MISS = "miss"
UNEVALUATED = "unevaluated"

PLACEMENT_A = "A"
PLACEMENT_B = "B"
PLACEMENT_NONE = "none"
PLACEMENT_INDETERMINATE = "indeterminate"

UNEVALUATED_IS_NOT_A_MISS = (
    "an unevaluated criterion is not a miss. Counting one as a miss ranks a "
    "well with thin records below a well with complete records for reasons that "
    "have nothing to do with the reservoir"
)

METHOD_HITS = (
    'NETL midcontinent heuristic candidate selection: count of published '
    'selection criteria "hit" (unweighted; the source publishes no weights and no '
    "scoring formula)"
)
METHOD_PLACEMENT = (
    'NETL midcontinent A/B candidate lists: A at >=%d hits, B at >=%d hits'
    % (A_LIST_MIN_HITS, B_LIST_MIN_HITS)
)
METHOD_COST = "added reserve cost = workover cost / added reserves"

HOUSE_ORDERING = (
    "ordering within this module is (1) descending hit count, which is published, "
    "then (2) fully-evaluated before partly-evaluated at equal hits, which is "
    "OURS, then (3) input order. Rule 2 never moves a well between lists. The "
    "source publishes lists and a hit count, not a rank order, and its own "
    "within-list prioritization is not used to order because it does not say how "
    "its three factors combine"
)


# --- caller-supplied evidence ----------------------------------------------


@dataclass(frozen=True)
class CriterionEvidence:
    """A caller's verdict on one criterion, with what it rests on.

    `hit is None` means **unevaluated** - the datum needed to judge this
    criterion was not available - and is not the same as `hit=False`.
    """

    hit: bool | None
    basis: str = ""
    source: str = ""


@dataclass(frozen=True)
class CriterionResult:
    key: str
    label: str
    verdict: str          # HIT / MISS / UNEVALUATED
    basis: str
    source: str
    quote: str
    published_criterion: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {"key": self.key, "label": self.label, "verdict": self.verdict,
                "basis": self.basis, "source": self.source, "quote": self.quote,
                "published_criterion": self.published_criterion}


@dataclass(frozen=True)
class PriorityFactorResult:
    key: str
    label: str
    verdict: str
    basis: str
    quote: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {"key": self.key, "label": self.label, "verdict": self.verdict,
                "basis": self.basis, "source": self.source}


@dataclass(frozen=True)
class CandidateScore:
    """One well's hit count, its list placement, and what the count was out of."""

    name: str
    hits: Quantity                      # unit "hits" - the floor, unknowns as misses
    hits_ceiling: Quantity              # unknowns as hits
    misses: int
    evaluated: int
    unevaluated: int
    n_criteria: int
    placement: str
    placement_floor: str
    placement_ceiling: str
    determinate: bool
    criteria: tuple[CriterionResult, ...]
    priority_factors: tuple[PriorityFactorResult, ...]
    added_reserve_cost: Any = None      # Quantity | Refusal | None - never scored
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    @property
    def unevaluated_keys(self) -> tuple[str, ...]:
        return tuple(c.key for c in self.criteria if c.verdict == UNEVALUATED)

    @property
    def fully_evaluated(self) -> bool:
        return self.unevaluated == 0


@dataclass(frozen=True)
class RecompletionRanking:
    a_list: tuple[CandidateScore, ...]
    b_list: tuple[CandidateScore, ...]
    unlisted: tuple[CandidateScore, ...]
    indeterminate: tuple[CandidateScore, ...]
    refused: dict[str, Refusal]
    n_a_list: Quantity
    n_b_list: Quantity
    thresholds: dict[str, int]
    published_study: dict[str, Any]
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    @property
    def ranked(self) -> tuple[CandidateScore, ...]:
        """A list then B list, each in this module's order. Not a published rank."""
        return self.a_list + self.b_list


# --- small helpers ----------------------------------------------------------


def _q(value: float, unit: str, method: str, source: str, **kw: Any) -> Quantity:
    return Quantity(value=value, unit=unit, method=method, source=source, **kw)


def _get(obj: Any, name: str) -> Any:
    """Read `name` off a dataclass, an object or a mapping. Missing -> None."""
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        return obj.get(name)
    return getattr(obj, name, None)


def _is_refusal(obj: Any) -> bool:
    return isinstance(obj, Refusal) or (
        obj is not None and not isinstance(obj, Mapping)
        and getattr(obj, "reason", None) is not None
        and getattr(obj, "value", "missing") is None
    )


def _as_int(v: Any) -> int | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _as_float(v: Any) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f  # NaN is not a number a caller meant


def _placement(hits: int, a_min: int, b_min: int) -> str:
    if hits >= a_min:
        return PLACEMENT_A
    if hits >= b_min:
        return PLACEMENT_B
    return PLACEMENT_NONE


# --- the economic benchmark -------------------------------------------------


def added_reserve_cost(
    workover_cost_usd: Any,
    added_reserves_mcfe: Any,
    *,
    basis: str,
    benchmark_usd_per_mcfe: float = ADDED_RESERVE_COST_BENCHMARK_USD_PER_MCFE,
    benchmark_vintage: str = BENCHMARK_VINTAGE,
    well: str = "",
) -> Quantity | Refusal:
    """Added reserve cost in US$/Mcfe, tested against the published benchmark.

    `basis` is required and has no default: `"actual"` is the source's own use -
    a workover that happened, reserves that were added. `"forecast"` applies the
    benchmark to a projection, which is a prospective extension the source never
    makes, and is flagged as one.

    Returns a `Quantity` whose flags say pass or fail. It is deliberately a
    separate entry point: this number is an outcome test on the selection
    procedure, not a selection criterion, and nothing in the ranking reads it.
    """
    if basis not in ("actual", "forecast"):
        # Programmer error, not a source limitation: the caller must say which.
        raise ValueError(
            'basis must be "actual" (the source\'s use: a workover that happened) '
            'or "forecast" (a prospective application the source does not make)')

    cost = _as_float(workover_cost_usd)
    reserves = _as_float(added_reserves_mcfe)
    missing: list[str] = []
    if cost is None:
        missing.append("workover_cost_usd (US$)")
    if reserves is None:
        missing.append("added_reserves_mcfe (Mcfe)")
    if missing:
        return Refusal(
            reason=(
                f"the < ${benchmark_usd_per_mcfe:.2f}/Mcfe benchmark is a cost per "
                "unit of added reserve; without both the workover cost and the "
                "added reserves there is no quantity to compare to it"
                + (f" (well {well})" if well else "")
                + f". Missing: {', '.join(missing)}"),
            needed=tuple(missing),
            source=NETL_MIDCONTINENT)
    if reserves <= 0:
        return Refusal(
            reason=(
                f"added_reserves_mcfe is {reserves:g}; a cost per unit of added "
                "reserve is undefined when the workover added no reserves"
                + (f" (well {well})" if well else "")
                + ". A workover that added nothing is unsuccessful by inspection, "
                  "not by this benchmark"),
            needed=("added_reserves_mcfe > 0 (Mcfe)",),
            source=NETL_MIDCONTINENT)
    if cost < 0:
        raise ValueError(f"workover_cost_usd must not be negative, got {cost!r}")

    value = cost / reserves
    passes = value < benchmark_usd_per_mcfe if BENCHMARK_IS_STRICT \
        else value <= benchmark_usd_per_mcfe

    flags = [
        ("benchmark-pass: " if passes else "benchmark-fail: ")
        + f"${value:.4f}/Mcfe against the published < "
          f"${benchmark_usd_per_mcfe:.2f}/Mcfe. The source's test is strict "
          '("< $0.50/Mcfe"), so exactly the benchmark does not pass',
        "benchmark-vintage: " + benchmark_vintage,
        "benchmark-role: " + BENCHMARK_IS_EX_POST,
        "source-caveat: " + BENCHMARK_VALIDATION_CAVEAT,
        'benchmark-definition-thin: the source says only "added reserve cost" - '
        "it does not say whether the Mcfe is gross or net of royalty, nor what is "
        "in the cost beyond the workover. Compare to your own economics with care",
    ]
    if basis == "forecast":
        flags.append(
            "prospective-application: the benchmark is applied to forecast added "
            "reserves. The source applies it only to workovers that had already "
            "happened, with the reserves observed")
    if benchmark_usd_per_mcfe != ADDED_RESERVE_COST_BENCHMARK_USD_PER_MCFE:
        flags.append(
            f"benchmark-overridden: caller set ${benchmark_usd_per_mcfe:.4f}/Mcfe "
            f"in place of the published ${ADDED_RESERVE_COST_BENCHMARK_USD_PER_MCFE:.2f}"
            "/Mcfe")

    return _q(value, "USD/Mcfe", METHOD_COST, NETL_MIDCONTINENT,
              inputs={"workover_cost_usd": cost,
                      "added_reserves_mcfe": reserves,
                      "basis": basis,
                      "well": well or None},
              assumptions={"benchmark_usd_per_mcfe": benchmark_usd_per_mcfe,
                           "benchmark_quote": BENCHMARK_SENTENCE,
                           "benchmark_vintage": benchmark_vintage,
                           "comparison": "strict less-than",
                           "role": "outcome test, not a selection criterion"},
              flags=tuple(flags))


def benchmark_passes(result: Any) -> bool | None:
    """True / False / None(unknown) from an `added_reserve_cost` result."""
    if not isinstance(result, Quantity):
        return None
    for f in result.flags:
        if f.startswith("benchmark-pass:"):
            return True
        if f.startswith("benchmark-fail:"):
            return False
    return None


# --- production_indicator (#112) ------------------------------------------


@dataclass(frozen=True)
class PIRead:
    """What this module took out of a `production_indicator` (#112) result.

    Field names are the contract with #112 and are listed in the spec. Anything
    absent stays `None` and makes a criterion **unevaluated**, never a miss.
    """

    available: bool
    refused: bool
    refusal_reason: str
    underperformer: bool | None
    pi_ratio: float | None
    target_pct: float | None
    indicator_kind: str | None
    rate_value: float | None
    rate_unit: str | None
    year: int | None
    n_offsets: int | None
    radius: Any
    dofp: Any
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {"available": self.available, "refused": self.refused,
                "underperformer": self.underperformer, "pi_ratio": self.pi_ratio,
                "target_pct": self.target_pct, "indicator_kind": self.indicator_kind,
                "rate_value": self.rate_value, "rate_unit": self.rate_unit,
                "year": self.year, "n_offsets": self.n_offsets,
                "radius": self.radius, "dofp": self.dofp,
                "refusal_reason": self.refusal_reason or None}


def read_production_indicator(pi: Any) -> PIRead:
    """Duck-typed read of a #112 result. Never imports #112, never calls it."""
    if pi is None:
        return PIRead(False, False, "", None, None, None, None, None, None, None,
                      None, None, None,
                      "no production_indicator (#112) result was supplied")
    if _is_refusal(pi):
        reason = str(_get(pi, "reason") or "")
        return PIRead(False, True, reason, None, None, None, None, None, None,
                      None, None, None, None,
                      "production_indicator (#112) refused; every criterion it "
                      "would have supplied is unevaluated, not a miss")

    under = _get(pi, "underperformer")
    if under is not None and not isinstance(under, bool):
        under = bool(under)
    pi_ratio = _as_float(_get(pi, "pi_ratio"))
    target_pct = _as_float(_get(pi, "target_pct"))
    note = ""

    # A real #112 result is the dict {"indicator", "domain_indicator",
    # "offset_indicators", "ratio_percent"} and carries NONE of the field names
    # read above. Its verdict rides on `ratio_percent.flags` - #112's own
    # docstring: "That flag is the 'hit' recompletion_rank (#113) consumes" - its
    # percentage is `ratio_percent.value`, and the caller's chosen target is
    # `ratio_percent.inputs["pi_percent"]`. Read that shape too, or
    # `use_production_indicator_for` can never fire against the tool it names.
    ratio_q = _get(pi, "ratio_percent")
    if ratio_q is not None:
        ratio_value = _as_float(_get(ratio_q, "value"))
        if pi_ratio is None and ratio_value is not None:
            pi_ratio = ratio_value / 100.0
        if target_pct is None:
            target_pct = _as_float(_get(_get(ratio_q, "inputs") or {}, "pi_percent"))
        verdicts = tuple(_get(ratio_q, "flags") or ())
        stated = [v for v in (LOW_PERFORMER, OVER_PERFORMER, WITHIN_TREND)
                  if v in verdicts]
        if under is None and stated:
            under = LOW_PERFORMER in stated
            note = (f"SWARM verdict {stated[0]!r} on production_indicator (#112)'s "
                    f"ratio_percent"
                    + (f" of {ratio_value:g}%" if ratio_value is not None else "")
                    + (f" against the user-set target of {target_pct:g}%"
                       if target_pct is not None else ""))

    if under is None and pi_ratio is not None and target_pct is not None:
        under = (pi_ratio * 100.0) < target_pct
        note = (f"underperformer derived from pi_ratio {pi_ratio:g} vs the "
                f"user-set target of {target_pct:g}% of the domain's wells")

    rate = _as_float(_get(pi, "normalized_rate"))
    if rate is None:
        rate = _as_float(_get(pi, "value"))
    return PIRead(
        available=True, refused=False, refusal_reason="",
        underperformer=under, pi_ratio=pi_ratio, target_pct=target_pct,
        indicator_kind=(str(_get(pi, "indicator_kind"))
                        if _get(pi, "indicator_kind") is not None else None),
        rate_value=rate,
        rate_unit=(str(_get(pi, "unit")) if _get(pi, "unit") is not None else None),
        year=_as_int(_get(pi, "year")),
        n_offsets=_as_int(_get(pi, "n_offsets")),
        radius=_get(pi, "radius"),
        dofp=_get(pi, "dofp"),
        note=note or "production_indicator (#112) result read")


# --- scoring one candidate --------------------------------------------------


def score_candidate(
    name: str,
    criteria: Mapping[str, Any] | None = None,
    *,
    production_indicator: Any = None,
    use_production_indicator_for: Sequence[str] = (),
    recent_rate_rank: Any = None,
    recent_rate_rank_cutoff: Any = None,
    ai_rank: Any = None,
    unstimulated_horizon: Any = None,
    population_size: Any = None,
    extra_criteria: Sequence[Criterion] = (),
    economics: Mapping[str, Any] | None = None,
    benchmark_usd_per_mcfe: float = ADDED_RESERVE_COST_BENCHMARK_USD_PER_MCFE,
    a_list_min_hits: int = A_LIST_MIN_HITS,
    b_list_min_hits: int = B_LIST_MIN_HITS,
    min_evaluated_criteria: int | None = None,
) -> CandidateScore | Refusal:
    """Count one well's criteria hits and place it on the A list, the B list, or
    neither - or refuse, when too little of the criteria list could be evaluated
    for a placement to mean what the source's placement means."""
    criteria = dict(criteria or {})
    min_eval = b_list_min_hits if min_evaluated_criteria is None \
        else int(min_evaluated_criteria)

    # -- assemble the criteria set ------------------------------------------
    catalog: list[Criterion] = list(SELECTION_CRITERIA)
    extra = tuple(extra_criteria or ())
    for c in extra:
        if not isinstance(c, Criterion):
            raise ValueError("extra_criteria must be Criterion instances")
        if c.key in PUBLISHED_CRITERIA_KEYS:
            raise ValueError(f"{c.key!r} is already a published criterion")
        catalog.append(Criterion(c.key, c.label, c.quote, c.source, c.operational,
                                 published=False))
    by_key = {c.key: c for c in catalog}
    unknown = [k for k in criteria if k not in by_key]
    if unknown:
        # Programmer error: an undeclared key would silently change what the
        # published >=4/>=3 thresholds are counting against.
        raise ValueError(
            f"unknown criterion key(s) {unknown!r}. The published criteria are "
            f"{list(PUBLISHED_CRITERIA_KEYS)}; declare anything else through "
            "extra_criteria so the result can be flagged as an extended set")

    pi_for = tuple(use_production_indicator_for or ())
    if "recent_rate" in pi_for:
        raise ValueError(
            "production_indicator (#112) must not supply the 'recent_rate' "
            "criterion: SWARM flags wells whose indicator falls BELOW their "
            "offsets, while this criterion is 'the better the most recent rate, "
            "the better the candidate'. The directions are opposite")
    for k in pi_for:
        if k not in by_key:
            raise ValueError(f"use_production_indicator_for names unknown criterion {k!r}")

    pi = read_production_indicator(production_indicator)
    flags: list[str] = []

    # -- evaluate every criterion -------------------------------------------
    results: list[CriterionResult] = []
    for crit in catalog:
        verdict, basis, src = _evaluate_criterion(
            crit, criteria.get(crit.key, None), pi, pi_for,
            recent_rate_rank, recent_rate_rank_cutoff)
        results.append(CriterionResult(
            key=crit.key, label=crit.label, verdict=verdict, basis=basis,
            source=src or crit.source, quote=crit.quote,
            published_criterion=crit.published))

    hits = sum(1 for r in results if r.verdict == HIT)
    misses = sum(1 for r in results if r.verdict == MISS)
    unev = sum(1 for r in results if r.verdict == UNEVALUATED)
    evaluated = hits + misses
    n = len(results)
    unev_keys = tuple(r.key for r in results if r.verdict == UNEVALUATED)

    # -- refusals R2 and R3 --------------------------------------------------
    if evaluated == 0:
        return Refusal(
            reason=(f"no criteria data for well {name!r}: none of "
                    f"{', '.join(c.key for c in catalog)} carries a verdict"
                    + (f". production_indicator (#112) refused: {pi.refusal_reason}"
                       if pi.refused else "")
                    + ". The hit count is a count over this criteria list and "
                      "there is nothing to count"),
            needed=tuple(f"a verdict for {c.key} ({c.label})" for c in catalog),
            source=NETL_MIDCONTINENT)
    if evaluated < min_eval:
        return Refusal(
            reason=(f"well {name!r} was evaluated on only {evaluated} of {n} "
                    f"criteria; the published B list requires at least "
                    f"{b_list_min_hits} hits, so a placement drawn from "
                    f"{evaluated} verdict(s) cannot mean what the source's "
                    f"placement means. Unevaluated: {', '.join(unev_keys)}. "
                    + UNEVALUATED_IS_NOT_A_MISS),
            needed=tuple(f"a verdict for {k} ({by_key[k].label})" for k in unev_keys),
            source=NETL_MIDCONTINENT)

    # -- placement at its floor and its ceiling ------------------------------
    floor = _placement(hits, a_list_min_hits, b_list_min_hits)
    ceiling = _placement(hits + unev, a_list_min_hits, b_list_min_hits)
    determinate = floor == ceiling
    placement = floor if determinate else PLACEMENT_INDETERMINATE

    if unev:
        flags.append(
            f"unevaluated-criteria: {unev} of {n} criteria could not be evaluated "
            f"({', '.join(unev_keys)}). Hits are {hits} of {evaluated} evaluated; "
            f"placement is {floor} on the evaluated criteria and could be "
            f"{ceiling} if every unevaluated one is a hit. "
            + UNEVALUATED_IS_NOT_A_MISS)
    if not determinate:
        flags.append(
            f"indeterminate-placement: this well is on neither list. Its "
            f"placement is {floor} at worst and {ceiling} at best, and the source "
            f"publishes no third list and no rule for a partly-evaluated "
            f"candidate. Supply {', '.join(unev_keys)} to place it")
    if extra:
        flags.append(
            "criteria-set-extended: "
            f"{len(extra)} caller-declared criterion(s) "
            f"({', '.join(c.key for c in extra)}) were counted alongside the "
            f"{len(SELECTION_CRITERIA)} published ones. The >= "
            f"{a_list_min_hits}/>= {b_list_min_hits} thresholds were calibrated "
            f"against the published four over that study population, so a hit "
            f"count out of {n} is NOT the published quantity. " + CRITERIA_SET_IS_OPEN)
    if a_list_min_hits != A_LIST_MIN_HITS or b_list_min_hits != B_LIST_MIN_HITS:
        flags.append(
            f"thresholds-overridden: A>={a_list_min_hits}, B>={b_list_min_hits} in "
            f"place of the published A>={A_LIST_MIN_HITS}, B>={B_LIST_MIN_HITS}")
    for r in results:
        if r.verdict != UNEVALUATED and not by_key[r.key].has_operational_definition:
            flags.append(
                f"caller-defined-hit: the source names {r.key!r} as a criterion "
                f'("{r.label}") and never defines its per-well test. The verdict '
                f"is the caller's: {r.basis or 'no basis stated'}")
    if pi.available and pi_for:
        flags.append(
            "pi-mapping-is-ours: SWARM's underperformer verdict is being read as "
            f"the {', '.join(pi_for)} criterion. SWARM ({NETL_SWARM}, western "
            "Pennsylvania, 1999-2005) and the midcontinent selection procedure "
            "are different projects and no source states that equivalence")
    if pi.refused:
        flags.append(
            f"production-indicator-refused: {pi.refusal_reason}. Every criterion "
            "it would have supplied is unevaluated, not a miss")

    # -- prioritization factors: reported, never scored ----------------------
    factors, factor_flags = _priority_factors(
        unstimulated_horizon, ai_rank, recent_rate_rank, population_size)
    flags.extend(factor_flags)
    flags.append("priority-combination-unstated: " + PRIORITY_COMBINATION_UNSTATED)

    # -- economics: computed, attached, and kept out of the count ------------
    cost_result: Any = None
    if economics is not None:
        cost_result = added_reserve_cost(
            economics.get("workover_cost_usd"),
            economics.get("added_reserves_mcfe"),
            basis=str(economics.get("basis", "actual")),
            benchmark_usd_per_mcfe=benchmark_usd_per_mcfe,
            well=name)
        flags.append("benchmark-role: " + BENCHMARK_IS_EX_POST)

    common = {
        "well": name,
        "criteria": tuple(r.as_dict() for r in results),
        "n_criteria": n,
        "evaluated": evaluated,
        "unevaluated": unev,
        "unevaluated_keys": unev_keys,
        "production_indicator": pi.as_dict(),
    }
    assumptions = {
        "criteria_sentence": CRITERIA_SENTENCE,
        "criteria_set": tuple(c.key for c in catalog),
        "criteria_set_is_open": CRITERIA_SET_IS_OPEN,
        "list_sentence": LIST_SENTENCE,
        "a_list_min_hits": a_list_min_hits,
        "b_list_min_hits": b_list_min_hits,
        "b_list_includes_a": B_LIST_INCLUDES_A,
        "unweighted": ("the source counts criteria met; it publishes no weights, "
                       "no coefficients and no scoring formula"),
        "unevaluated_handling": UNEVALUATED_IS_NOT_A_MISS,
        "benchmark_role": BENCHMARK_IS_EX_POST,
        "study": f"{STUDY_FIELD}; {STUDY_PERIOD}",
    }

    return CandidateScore(
        name=name,
        hits=_q(float(hits), "hits", METHOD_HITS, NETL_MIDCONTINENT,
                inputs=dict(common), assumptions=dict(assumptions),
                flags=tuple(flags)),
        hits_ceiling=_q(float(hits + unev), "hits",
                        METHOD_HITS + " - ceiling: every unevaluated criterion "
                                      "resolved as a hit",
                        NETL_MIDCONTINENT,
                        inputs=dict(common), assumptions=dict(assumptions)),
        misses=misses,
        evaluated=evaluated,
        unevaluated=unev,
        n_criteria=n,
        placement=placement,
        placement_floor=floor,
        placement_ceiling=ceiling,
        determinate=determinate,
        criteria=tuple(results),
        priority_factors=factors,
        added_reserve_cost=cost_result,
        inputs=common,
        assumptions=assumptions,
        flags=tuple(flags))


def _evaluate_criterion(crit: Criterion, supplied: Any, pi: PIRead,
                        pi_for: Sequence[str], recent_rate_rank: Any,
                        recent_rate_rank_cutoff: Any) -> tuple[str, str, str]:
    """One criterion -> (verdict, basis, source). Absent evidence -> UNEVALUATED."""
    if isinstance(supplied, CriterionEvidence):
        if supplied.hit is None:
            return (UNEVALUATED,
                    supplied.basis or "the caller supplied no verdict", supplied.source)
        return (HIT if supplied.hit else MISS,
                supplied.basis or "caller-supplied verdict", supplied.source)
    if isinstance(supplied, bool):
        return (HIT if supplied else MISS, "caller-supplied verdict", "")
    if supplied is not None:
        raise ValueError(
            f"criterion {crit.key!r} takes True, False, None or CriterionEvidence, "
            f"got {type(supplied).__name__}. A number is not a verdict: the "
            "published method counts hits, it does not weight them")

    # No verdict supplied. Two sourced fallbacks, both narrow.
    if crit.key in pi_for and pi.available and pi.underperformer is not None:
        basis = (f"production_indicator (#112) underperformer="
                 f"{pi.underperformer}; {pi.note}")
        return (HIT if pi.underperformer else MISS, basis, NETL_SWARM)

    if crit.key == "recent_rate":
        rank = _as_int(recent_rate_rank)
        cutoff = _as_int(recent_rate_rank_cutoff)
        if rank is not None and cutoff is not None:
            return (HIT if rank <= cutoff else MISS,
                    f"most-recent-rate rank {rank} against a caller-stated cutoff "
                    f"of {cutoff}. No cutoff is published: the source gives a "
                    f'direction only ("the better the most recent rate, the '
                    f'better the candidate"), so the cutoff is CALLER '
                    f"({CATALOG_THRESHOLDS})", NETL_MIDCONTINENT)
        if rank is not None and cutoff is None:
            return (UNEVALUATED,
                    f"a most-recent-rate rank of {rank} was supplied with no "
                    "cutoff. The source publishes a direction, not a threshold, "
                    "and this module will not default one", NETL_MIDCONTINENT)
        if pi.available and pi.rate_value is not None:
            magnitude = f"{pi.rate_value:g} {pi.rate_unit or ''}".strip()
            return (UNEVALUATED,
                    f"production_indicator (#112) supplies a rate magnitude "
                    f"({magnitude}, indicator_kind={pi.indicator_kind!r}, "
                    f"year={pi.year!r}) but no rank and no cutoff. A magnitude "
                    'alone cannot decide "the better the most recent rate" - and '
                    "#112's underperformer verdict runs the opposite way, so it "
                    "is not used here", NETL_MIDCONTINENT)
    return (UNEVALUATED, "no verdict and no evidence were supplied", crit.source)


def _priority_factors(unstimulated_horizon: Any, ai_rank: Any,
                      recent_rate_rank: Any, population_size: Any
                      ) -> tuple[tuple[PriorityFactorResult, ...], list[str]]:
    ai = _as_int(ai_rank)
    rr = _as_int(recent_rate_rank)
    pop = _as_int(population_size)
    flags: list[str] = []
    out: list[PriorityFactorResult] = []

    def add(factor: PriorityFactor, verdict: str, basis: str) -> None:
        out.append(PriorityFactorResult(factor.key, factor.label, verdict, basis,
                                        factor.quote, factor.source))

    f_unstim, f_top45, f_top30 = PRIORITY_FACTORS
    if isinstance(unstimulated_horizon, bool):
        add(f_unstim, HIT if unstimulated_horizon else MISS,
            "caller-supplied completion record")
    else:
        add(f_unstim, UNEVALUATED,
            "no completion record was supplied; whether an unstimulated horizon "
            "is present is unknown")

    if ai is not None and rr is not None:
        add(f_top45, HIT if (ai <= TOP45_RANK and rr <= TOP45_RANK) else MISS,
            f"artificial-intelligence rank {ai} and most-recent-rate rank {rr} "
            f"against the published top {TOP45_RANK}, which the source requires "
            f"on both")
    else:
        add(f_top45, UNEVALUATED,
            "the source requires the top 45 on BOTH artificial intelligence and "
            "most recent producing rate; "
            + ("no rank was supplied" if ai is None and rr is None
               else "only one of the two ranks was supplied"))

    ranks = [r for r in (ai, rr) if r is not None]
    if ranks:
        add(f_top30, HIT if min(ranks) <= TOP30_RANK else MISS,
            f"best available rank {min(ranks)} against the published top "
            f"{TOP30_RANK} for at least one criterion"
            + ("" if len(ranks) == 2 else " (only one of the two ranks supplied, "
                                          "so a miss here is provisional)"))
    else:
        add(f_top30, UNEVALUATED, "no rank was supplied")

    if ai is not None or rr is not None:
        if pop is None:
            flags.append("rank-population-unstated: " + RANK_CUTOFFS_ARE_POPULATION_BOUND
                         + ". State population_size so the cutoffs can be judged")
        elif pop < TOP45_RANK:
            flags.append(
                f"rank-population-too-small: {pop} wells is fewer than the top-45 "
                f"cutoff itself, so 'top 45' selects the whole population and the "
                f"factor carries no information. " + RANK_CUTOFFS_ARE_POPULATION_BOUND)
        elif pop < 2 * TOP45_RANK:
            flags.append(
                f"rank-population-small: {pop} wells against a study population of "
                f"roughly a hundred. " + RANK_CUTOFFS_ARE_POPULATION_BOUND)
    return tuple(out), flags


# --- ranking a set ----------------------------------------------------------


def recompletion_rank(
    candidates: Iterable[Any],
    *,
    benchmark_usd_per_mcfe: float = ADDED_RESERVE_COST_BENCHMARK_USD_PER_MCFE,
    a_list_min_hits: int = A_LIST_MIN_HITS,
    b_list_min_hits: int = B_LIST_MIN_HITS,
    min_evaluated_criteria: int | None = None,
    extra_criteria: Sequence[Criterion] = (),
) -> RecompletionRanking | Refusal:
    """Place a set of wells on the NETL A and B candidate lists.

    Each candidate is a mapping of the `score_candidate` keyword arguments (or an
    object carrying them). Candidates that cannot be scored are refused
    individually and returned in `refused`; candidates whose placement is
    indeterminate are on neither list and returned in `indeterminate`.
    """
    items = list(candidates or ())
    if not items:
        return Refusal(
            reason=("no candidates were supplied; the A and B lists are a "
                    "partition of a candidate set and there is nothing to "
                    "partition"),
            needed=("at least one candidate, each with verdicts on the criteria "
                    f"{list(PUBLISHED_CRITERIA_KEYS)}",),
            source=NETL_MIDCONTINENT)

    scored: list[tuple[int, CandidateScore]] = []
    refused: dict[str, Refusal] = {}
    for i, raw in enumerate(items):
        kw = dict(raw) if isinstance(raw, Mapping) else dict(_get(raw, "__dict__") or {})
        name = str(kw.pop("name", None) or f"candidate[{i}]")
        kw.setdefault("extra_criteria", extra_criteria)
        kw.setdefault("benchmark_usd_per_mcfe", benchmark_usd_per_mcfe)
        kw.setdefault("a_list_min_hits", a_list_min_hits)
        kw.setdefault("b_list_min_hits", b_list_min_hits)
        kw.setdefault("min_evaluated_criteria", min_evaluated_criteria)
        result = score_candidate(name, kw.pop("criteria", None), **kw)
        if isinstance(result, Refusal):
            refused[name] = result
        else:
            scored.append((i, result))

    def order(entry: tuple[int, CandidateScore]) -> tuple[float, int, int]:
        i, s = entry
        # (1) published: descending hit count. (2) HOUSE: fully-evaluated first at
        # equal hits. (3) stable input order.
        return (-s.hits.value, 0 if s.fully_evaluated else 1, i)

    scored.sort(key=order)
    a = tuple(s for _, s in scored if s.placement == PLACEMENT_A)
    b = tuple(s for _, s in scored if s.placement == PLACEMENT_B)
    none_ = tuple(s for _, s in scored if s.placement == PLACEMENT_NONE)
    indet = tuple(s for _, s in scored if s.placement == PLACEMENT_INDETERMINATE)

    if not a and not b and not none_:
        return Refusal(
            reason=(f"no candidate could be placed: {len(refused)} refused, "
                    f"{len(indet)} indeterminate. " + UNEVALUATED_IS_NOT_A_MISS),
            needed=tuple(
                f"{s.name}: verdicts for {', '.join(s.unevaluated_keys)}"
                for s in indet) or ("criteria verdicts for at least one candidate",),
            source=NETL_MIDCONTINENT)

    flags = [
        "hit-count-not-a-score: " + (
            "the published method counts criteria met. It publishes no weights, "
            "no coefficients and no composite, so none are emitted"),
        "house-ordering: " + HOUSE_ORDERING,
        "priority-combination-unstated: " + PRIORITY_COMBINATION_UNSTATED,
        "benchmark-role: " + BENCHMARK_IS_EX_POST,
        "benchmark-vintage: " + BENCHMARK_VINTAGE,
    ]
    if indet:
        flags.append(
            f"indeterminate-candidates: {len(indet)} well(s) "
            f"({', '.join(s.name for s in indet)}) are on neither list because "
            "their placement depends on criteria that could not be evaluated")
    if refused:
        flags.append(
            f"refused-candidates: {len(refused)} well(s) could not be scored "
            f"({', '.join(refused)})")

    counts = {"a_list": len(a), "b_list": len(b), "unlisted": len(none_),
              "indeterminate": len(indet), "refused": len(refused),
              "candidates": len(items)}
    published = {
        "list_counts": dict(PUBLISHED_LIST_COUNTS),
        "top_priority_counts": dict(PUBLISHED_TOP_PRIORITY_COUNTS),
        "note": ("the study's own result over its well set: List A had 5 wells and "
                 "list B had 17; one on A and six on B were highlighted as top "
                 "priority. These are that field's numbers, not a target"),
        "study": f"{STUDY_FIELD}; {STUDY_PERIOD}",
    }
    q_kw = dict(inputs=dict(counts), assumptions={"list_sentence": LIST_SENTENCE,
                                                  "published_study": published},
                flags=tuple(flags))
    return RecompletionRanking(
        a_list=a, b_list=b, unlisted=none_, indeterminate=indet, refused=refused,
        n_a_list=_q(float(len(a)), "wells",
                    f"A list: candidates with >= {a_list_min_hits} criteria hits",
                    NETL_MIDCONTINENT, **q_kw),
        n_b_list=_q(float(len(b)), "wells",
                    f"B list: candidates with >= {b_list_min_hits} criteria hits",
                    NETL_MIDCONTINENT, **q_kw),
        thresholds={"a_list_min_hits": a_list_min_hits,
                    "b_list_min_hits": b_list_min_hits,
                    "min_evaluated_criteria": (b_list_min_hits
                                               if min_evaluated_criteria is None
                                               else int(min_evaluated_criteria)),
                    "n_published_criteria": len(SELECTION_CRITERIA)},
        published_study=published,
        inputs=counts,
        assumptions={"criteria_sentence": CRITERIA_SENTENCE,
                     "list_sentence": LIST_SENTENCE,
                     "priority_sentence": PRIORITY_SENTENCE,
                     "benchmark_sentence": BENCHMARK_SENTENCE,
                     "ordering": HOUSE_ORDERING,
                     "b_list_includes_a": B_LIST_INCLUDES_A,
                     "a_list_implies_fully_evaluated": A_LIST_IMPLIES_FULLY_EVALUATED},
        flags=tuple(flags))


# ======================================================================
# Tool #115 dst_recompletion_screen
# ======================================================================

# --- anchors ---------------------------------------------------------------

#: Sec. 8.1 Introduction, p. 90-91. The catalog's anchor for #115; it states the
#: logic verbatim.
EARLOUGHER_SEC_81 = "03-dst/earlougher-well-test-analysis-part2-1977#1"
#: Eq. 8.3, damage ratio, p. 94.
EARLOUGHER_EQ_83 = "03-dst/earlougher-well-test-analysis-part2-1977#3"
#: Example 8.1, pp. 95-96. Rate from the recovered column, and its own reading of
#: the damage ratio.
EARLOUGHER_EX_81 = "03-dst/earlougher-well-test-analysis-part2-1977#5"
#: Sec. 8.4 named chart signatures - where dst_validate's verdicts come from.
EARLOUGHER_TROUBLE = "03-dst/earlougher-well-test-analysis-part2-1977#8"

#: The economics half has no corpus source. This line is where the decision that
#: it has none is recorded, so it is what the refusal cites.
COMMERCIAL_TODAY_SOURCE = (
    'tool-catalog.md, "Thresholds the corpus does not supply" - "Commercial '
    'today", status CALLER'
)

COMMERCIAL_TODAY_SENTENCE = (
    '"Commercial today" - no default, ever. dst_recompletion_screen requires gas '
    "price, per-well operating cost, workover cost and a discount rate as "
    "explicit inputs. Nothing in the corpus establishes an economic threshold, "
    "and a wrong one recommends spending money. It refuses rather than assumes."
)

# --- the sourced logic, quoted ---------------------------------------------

#: EARLOUGHER_SEC_81. The sentence the catalog means by "states the logic
#: verbatim". Three things in it are load-bearing and all three are enforced
#: below: two evidence channels joined by "and"; the claim is *possibility* of
#: commercial production, never commerciality; and the DST rate is a damaged,
#: open-hole, short-duration rate that understates a stimulated completion.
SEC_81_LOGIC = (
    "A good DST yields a sample of the type of reservoir fluid present, an "
    "indication of flow rates, a measurement of static and flowing bottom-hole "
    "pressure, and a short-term pressure transient test. The DST helps determine "
    "the possibility of commercial production by virtue of the types of fluids "
    "recovered and the flow rates observed. Analysis of the DST transient "
    "pressure data can provide an estimate of formation properties and wellbore "
    "damage. Those data may be used to estimate the well's flow potential with a "
    "regular completion that uses stimulation techniques to remove damage and "
    "increase effective wellbore size."
)

#: EARLOUGHER_EX_81, closing paragraph. Why the volume route exists at all, and
#: the boundary at which it stops applying.
EX_81_RATE_PROBLEM = (
    "The problem of estimating flow rate is a real one, and must be dealt with by "
    "using pressures, densities, volumes of the various fluids produced, and pipe "
    "capacities - if flow does not occur at the surface."
)

#: EARLOUGHER_EX_81, same paragraph. A flag on the initial period, never a
#: refusal: Example 8.1 works the initial period itself and uses the number.
EX_81_FIRST_PERIOD = (
    "Normally, one does not analyze pressure data from the first flow and shut-in "
    "periods. Results from analyzing those data tend to be less accurate than "
    "results from analyzing the second flow and shut-in periods because of longer "
    "flow duration and likely absence of mud production during the second flow "
    "period."
)

#: EARLOUGHER_EX_81. The source reading its own damage ratio out loud. This is
#: the oracle for fraction_of_ideal_capacity: 1/17.3 = 0.0578.
EX_81_DAMAGE_READING = (
    "From Eq. 8.3, the damage ratio is (1,722 - 145)/(1,722 - 145 - 1,486) = "
    "17.3. This indicates the well is producing at only about 6 percent of its "
    "ideal capacity. Stimulation would be required for a successful completion."
)

#: EARLOUGHER_EQ_83. Damage ratio is a ratio of productivity indices, which is
#: what licenses q_ideal = q_dst x DR.
EQ_83 = (
    "DST analyses commonly report damage ratio: J_ideal/J_actual = "
    "(p_bar - p_wf)/(p_bar - p_wf - delta_p_s)  (Eq. 8.3)"
)

#: Sec. 8.4, via dst_validate. The two signatures under which the source itself
#: says the data cannot be used - quoted so a caller who passes validation=None
#: is told exactly what has not been ruled out.
SEC_84_INVALIDATING = (
    'Fig. 8.13 "Such test data cannot be analyzed", and Fig. 8.11 confirmed by an '
    'abnormally large mud recovery, "In this case test data must be disregarded"'
)

VINTAGE_ASYMMETRY = (
    "a DST recovery is evidence about the ROCK and does not age; the economics "
    "that made the zone uncommercial when it was tested do not carry forward. "
    "Nothing historical - not the test year, not a price of that vintage, not a "
    "published benchmark of that vintage - may be used to default a price, an "
    "operating cost, a workover cost or a discount rate"
)

# --- constants --------------------------------------------------------------

#: Example 8.1: "(0.407 bbl/5 min)(1,440 min/D)". SOURCED.
MINUTES_PER_DAY = 1440.0

#: Days a rate is held for one year of revenue. OURS - the perpetuity below is
#: house arithmetic over caller numbers and 365 is a calendar fact, not a corpus
#: claim. No downtime or uptime fraction is applied, because none is sourced and
#: applying one would move the answer in the operator's favour or against it
#: without a basis either way.
DAYS_PER_YEAR = 365.0

STATUS_SOURCED_115 = "SOURCED"
STATUS_CALLER_115 = "CALLER"
STATUS_HOUSE_115 = "HOUSE"

RATE_UNIT_STB = "STB/D"
RATE_UNIT_MCF = "Mcf/D"
RATE_UNITS_115 = (RATE_UNIT_STB, RATE_UNIT_MCF)

PRICE_UNIT_STB = "$/STB"
PRICE_UNIT_MCF = "$/Mcf"

#: A $/Mcf price against an STB/D rate is a unit error, not a judgment call.
#: psia-versus-psig has already cost this codebase real time.
PRICE_UNIT_FOR_RATE = {RATE_UNIT_STB: PRICE_UNIT_STB, RATE_UNIT_MCF: PRICE_UNIT_MCF}

FLOW_PERIOD_INITIAL = "initial"
FLOW_PERIOD_FINAL = "final"
FLOW_PERIODS_115 = (FLOW_PERIOD_INITIAL, FLOW_PERIOD_FINAL)

ROUTE_VOLUME = "recovered-column volume (Example 8.1)"
ROUTE_SURFACE = "surface-gauged rate"

#: The screen's two possible verdicts. There is no third, and in particular there
#: is no "commercial".
RULED_OUT = "ruled_out"
NOT_RULED_OUT = "not_ruled_out"

VERDICT_MEANINGS = {
    RULED_OUT: (
        "a flat, never-declining stream at the most favourable rate this DST "
        "supports does not repay the caller's own numbers. Conclusive against, "
        "and conclusive under any decline, because every Arps stream starting at "
        "the same rate is worth strictly less than the flat perpetuity"
    ),
    NOT_RULED_OUT: (
        "NOT a finding that the zone is commercial. The screen eliminates; it "
        "never endorses. Turning this into a recommendation needs a decline "
        "forecast (#116) and an EUR to an economic limit (#117), neither of which "
        "a DST supplies and neither of which is fabricated here"
    ),
}

METHOD_INDICATION = (
    "DST-indicated flow rate: recovered column to barrels by string section, "
    "q = V x 1,440 min/D / t_flow (Example 8.1), against the Sec. 8.1 two-channel "
    "test (fluids recovered AND flow rates observed)"
)

METHOD_SCREEN = (
    "recompletion screen: flat-perpetuity break-even rate "
    "q_be = (opex_per_year + r x workover) / (price x 365), reported as "
    "q_screen / q_be. HOUSE ARITHMETIC over four caller-supplied numbers - "
    "elementary finance, not a corpus equation"
)

HOUSE_ARITHMETIC_NOTE = (
    "the break-even is house arithmetic, not a corpus equation. Every input is "
    "the caller's; the perpetuity form was chosen because it consumes all four "
    "inputs and needs no evaluation life and no decline model, both of which "
    "would have to be invented. It is deliberately the most generous defensible "
    "standard, which is what fixes the direction of the tool's only claim"
)

ONE_SIDED_NOTE = (
    "this screen can only rule a candidate OUT. A screen that cannot recommend "
    "spending money cannot commit the harm the catalog names"
)

#: The one economic number anywhere in knowledge-base/, recorded here so the
#: search is not repeated, and explicitly NOT used. It is a cost-per-added-reserve
#: measure of a workover already performed (an ex-post outcome test), it needs an
#: added-reserve volume this tool does not have, the catalog assigns it to
#: recompletion_rank (#113), and it is a ~2001 dollar figure - the vintage problem
#: again. Importing it as a default here would be the "never substitute an
#: adjacent equation" failure in its economic form.
NOT_A_SUBSTITUTE_BENCHMARK = (
    'NETL\'s "< $0.50/Mcfe" added-reserve-cost benchmark '
    "(15-recompletion-screening/netl-stripper-gas-well-selection-midcontinent) is "
    "the only economic number in the corpus. It is an ex-post test of workovers "
    "already performed, it needs an added-reserve volume, it belongs to "
    "recompletion_rank (#113), and it is a ~2001 dollar figure. It is not a "
    "price, not an operating cost, not a discount rate, and it is not used here"
)

#: Declaration order. The refusal names missing inputs in this order.
ECONOMIC_INPUTS: tuple[tuple[str, str], ...] = (
    ("price_usd_per_unit",
     "wellhead price at the evaluation date, $/Mcf or $/STB (state price_unit)"),
    ("operating_cost_usd_per_well_per_year",
     "per-well operating cost, $/well/yr, for this well as a producer"),
    ("workover_cost_usd",
     "all-in cost of the re-entry and recompletion, $"),
    ("discount_rate_fraction",
     "discount rate as a fraction of 1 (0.10 for 10%/yr)"),
)

NO_CONSERVATIVE_DEFAULT = (
    "a conservative assumption is not a safe one. A low price and a high cost "
    "still produce a number, that number still arrives with provenance attached, "
    "and an operator can still act on it. A conservative default does not fail "
    "safe; it fails quietly. Three of four supplied refuses exactly as zero of "
    "four does"
)


# --- small helpers ----------------------------------------------------------


def _dst_is_refusal(obj) -> bool:
    """Duck-typed so a Refusal from any tools module is recognised on merge."""
    if isinstance(obj, Refusal):
        return True
    return (obj is not None and hasattr(obj, "reason") and hasattr(obj, "needed")
            and getattr(obj, "value", "sentinel") is None)


def _dst_float(name: str, value, *, allow_negative: bool = False):
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric, got {value!r}") from exc
    if out != out:
        raise ValueError(f"{name} must be a real number, got {value!r}")
    if not allow_negative and out < 0:
        raise ValueError(f"{name} must not be negative, got {out}")
    return out


def _dst_findings(validation):
    """The Sec. 8.4 findings dst_validate recorded, or an empty tuple."""
    inputs = getattr(validation, "inputs", None) or {}
    return tuple(inputs.get("findings") or ())


# --- part 1: the sourced half -----------------------------------------------


def dst_zone_indication(
    validation,
    *,
    fluid_recovered=None,
    flow_period_min=None,
    recovered_len_ft=None,
    string_sections=None,
    prior_fill_len_ft=0.0,
    surface_gauged_rate=None,
    rate_unit=RATE_UNIT_STB,
    zone_depth_ft=None,
    zone_top_ft=None,
    zone_bottom_ft=None,
    p_isi_psig=None,
    p_fsi_psig=None,
    pressure_unit="psig",
    flow_period=FLOW_PERIOD_FINAL,
    damage_ratio=None,
    gas_cut=False,
    test_year=None,
):
    """What the DST says about the zone. Earlougher Sec. 8.1 and Example 8.1.

    Answers "did this zone test as though it holds producible hydrocarbon, and at
    what rate", and never answers "is it commercial" - the source's own claim is
    "the *possibility* of commercial production", which is why this function is
    not named for a verdict.

    `validation` is the result of `dst_validate` (#42) and is required to be
    passed. `None` is accepted and means "the chart was never assessed", which is
    flagged loudly rather than refused: a scout ticket often outlives the chart,
    and refusing every such test would make the tool useless for exactly the
    vintage DSTs it exists to screen. A `Refusal` from `dst_validate` propagates,
    and a `dst_validate` verdict of 0.0 (not analysable) refuses here.

    Rate comes either from a surface gauge or from the recovered column via
    `dst_recovery_volume` (#43), which is consumed, never reimplemented: the
    column crosses the drill-collar/drillpipe transition and a single capacity
    over the whole column is wrong by about 46% on the rate.
    """
    # --- programmer errors first --------------------------------------------
    if pressure_unit != "psig":
        raise ValueError(
            "DST chart pressures are psig, temperature-corrected (Fig. 8.5 column "
            f"heading); got pressure_unit={pressure_unit!r}")
    if rate_unit not in RATE_UNITS_115:
        raise ValueError(f"rate_unit must be one of {RATE_UNITS_115}, got {rate_unit!r}")
    if flow_period not in FLOW_PERIODS_115:
        raise ValueError(
            f"flow_period must be one of {FLOW_PERIODS_115}, got {flow_period!r}")

    flow_period_min = _dst_float("flow_period_min", flow_period_min)
    if flow_period_min is not None and flow_period_min <= 0:
        raise ValueError(f"flow_period_min must be positive, got {flow_period_min}")
    recovered_len_ft = _dst_float("recovered_len_ft", recovered_len_ft)
    prior_fill_len_ft = _dst_float("prior_fill_len_ft", prior_fill_len_ft) or 0.0
    surface_gauged_rate = _dst_float("surface_gauged_rate", surface_gauged_rate)
    zone_depth_ft = _dst_float("zone_depth_ft", zone_depth_ft)
    zone_top_ft = _dst_float("zone_top_ft", zone_top_ft)
    zone_bottom_ft = _dst_float("zone_bottom_ft", zone_bottom_ft)
    p_isi_psig = _dst_float("p_isi_psig", p_isi_psig)
    p_fsi_psig = _dst_float("p_fsi_psig", p_fsi_psig)
    damage_ratio = _dst_float("damage_ratio", damage_ratio)
    if damage_ratio is not None and damage_ratio < 1.0:
        raise ValueError(
            "damage_ratio is J_ideal/J_actual (Eq. 8.3) and cannot be below 1 for a "
            f"damaged well; got {damage_ratio}. A stimulated well reporting DR < 1 is "
            "outside what Eq. 8.3 describes")
    if zone_top_ft is not None and zone_bottom_ft is not None and \
            zone_bottom_ft < zone_top_ft:
        raise ValueError(
            f"zone_bottom_ft ({zone_bottom_ft}) is above zone_top_ft ({zone_top_ft}); "
            "depths increase downward")

    flags: list[str] = []
    assumptions: dict = {
        "sec_8_1_logic": SEC_81_LOGIC,
        "claim": "the possibility of commercial production, per the source's own "
                 "wording. This function never returns a commercial verdict",
        "vintage_asymmetry": VINTAGE_ASYMMETRY,
        "status": STATUS_SOURCED_115,
    }

    # --- refusal 1 and 2: the chart ----------------------------------------
    if _dst_is_refusal(validation):
        return Refusal(
            reason="the chart was not assessed: " + getattr(validation, "reason", ""),
            needed=tuple(getattr(validation, "needed", ()) or ()),
            source=getattr(validation, "source", EARLOUGHER_TROUBLE) or EARLOUGHER_TROUBLE)

    findings = _dst_findings(validation)
    if validation is None:
        flags.append(
            "the DST chart was never assessed (validation=None). Sec. 8.4 names two "
            "signatures under which the source itself says the data cannot be used - "
            + SEC_84_INVALIDATING + " - and neither has been ruled out for this test")
    else:
        verdict = getattr(validation, "value", None)
        if verdict is not None and float(verdict) == 0.0:
            invalidating = [f for f in findings if f.get("severity") == "invalidating"]
            named = "; ".join(
                f"Fig. {f.get('figure')}: {f.get('verdict') or f.get('wording')}"
                for f in invalidating) or "an invalidating Sec. 8.4 signature"
            return Refusal(
                reason="dst_validate found the chart not analysable, so there is no "
                       f"rate and no pressure to screen on: {named}",
                needed=("a re-test, or a re-read of the chart that does not carry an "
                        "invalidating Sec. 8.4 signature",),
                source=EARLOUGHER_TROUBLE)
        for f in findings:
            if f.get("severity") not in (None, "not_a_failure"):
                flags.append(
                    f"chart finding [{f.get('severity')}] Fig. {f.get('figure')}: "
                    f"{f.get('wording')}"
                    + (f" VERDICT: {f['verdict']}" if f.get("verdict") else ""))

    # --- refusal 7: the fluid channel --------------------------------------
    described = isinstance(fluid_recovered, str) and fluid_recovered.strip() != ""
    if not described:
        return Refusal(
            reason="no description of the fluid recovered. Sec. 8.1 makes the DST "
                   "evidence two channels joined by AND - \"the types of fluids "
                   "recovered and the flow rates observed\" - so a bare rate is half "
                   "the evidence and is not reported as though it were the whole",
            needed=("fluid_recovered: the verbatim recovery description from the DST "
                    "ticket or data sheet (Fig. 8.6's 'description of the recovery'), "
                    "recorded as written and never classified",),
            source=EARLOUGHER_SEC_81)

    # --- refusal 3, 4, 5, 9: the rate channel -------------------------------
    volume_args = {"recovered_len_ft": recovered_len_ft,
                   "string_sections": string_sections,
                   "flow_period_min": flow_period_min}
    have_volume_route = all(v is not None for v in volume_args.values())
    recovery_bbl = None
    per_section: tuple = ()
    recovery_quantity = None

    if surface_gauged_rate is not None:
        route = ROUTE_SURFACE
        q = surface_gauged_rate
        flags.append(
            "rate is surface-gauged, so the Example 8.1 volume route does not apply: "
            + EX_81_RATE_PROBLEM)
        if any(v is not None for v in volume_args.values()):
            flags.append(
                "recovered-column arguments were also supplied and are not used; a "
                "gauged surface rate is a measurement and the column volume is an "
                "inference from it")
    elif not have_volume_route:
        missing = [k for k, v in volume_args.items() if v is None]
        return Refusal(
            reason="no flow-rate evidence. Sec. 8.1's second channel is \"the flow "
                   "rates observed\", and neither route to one is available: "
                   f"surface_gauged_rate was not given and the Example 8.1 volume "
                   f"route is missing {', '.join(missing)}",
            needed=("surface_gauged_rate (with rate_unit), or all of recovered_len_ft, "
                    "string_sections (bottom-first, with capacity_bbl_per_ft) and "
                    "flow_period_min",),
            source=EARLOUGHER_EX_81)
    else:
        route = ROUTE_VOLUME
        if rate_unit == RATE_UNIT_MCF:
            return Refusal(
                reason="the recovered column gives barrels of liquid standing in the "
                       "drillstring. Chapter 8 states no conversion from a DST liquid "
                       "recovery to a gas rate, and none is invented here",
                needed=("surface_gauged_rate in Mcf/D - a gas rate must be gauged at "
                        "surface; or rate_unit='STB/D' if the recovery was liquid",),
                source=EARLOUGHER_EX_81)
        recovery_quantity = dst_recovery_volume(
            recovered_len_ft, string_sections,
            prior_fill_len_ft=prior_fill_len_ft, gas_cut=gas_cut)
        if _dst_is_refusal(recovery_quantity):
            return recovery_quantity          # propagated unchanged, by design
        recovery_bbl = float(recovery_quantity.value)
        per_section = tuple(recovery_quantity.inputs.get("per_section") or ())
        flags.extend(recovery_quantity.flags)
        if recovery_bbl <= 0.0:
            return Refusal(
                reason="the recovered column is zero barrels. Both of Sec. 8.1's "
                       "evidence channels are then empty - there is no fluid recovered "
                       "and no flow rate observed - and a zone that recovered nothing "
                       "is not a recompletion candidate on this evidence",
                needed=("a recovered column length greater than zero, or a "
                        "surface-gauged rate",),
                source=EARLOUGHER_EX_81)
        q = recovery_bbl * MINUTES_PER_DAY / flow_period_min

    if flow_period == FLOW_PERIOD_INITIAL:
        flags.append("initial flow period: " + EX_81_FIRST_PERIOD)

    # --- refusal 6: the pressure channel ------------------------------------
    if p_isi_psig is None and p_fsi_psig is None:
        return Refusal(
            reason="no shut-in pressure. Sec. 8.1 counts \"a measurement of static and "
                   "flowing bottom-hole pressure\" among what a good DST yields, and "
                   "the limited-data route takes p_i ~= p_bar ~= p_isi; with neither "
                   "shut-in pressure there is no reservoir pressure for the zone",
            needed=("p_isi_psig (initial shut-in pressure, psig), or p_fsi_psig",),
            source=EARLOUGHER_SEC_81)
    if p_isi_psig is not None:
        reservoir_pressure_psig = p_isi_psig
        pressure_basis = "p_isi (initial shut-in), per p_i ~= p_bar ~= p_isi"
    else:
        reservoir_pressure_psig = p_fsi_psig
        pressure_basis = "p_fsi (final shut-in); p_isi was not supplied"
        flags.append(
            "reservoir pressure taken from the final shut-in because the initial "
            "shut-in was not supplied; the source extrapolates p_i from either but "
            "expects the two to agree within about 5 percent")

    # --- refusal 8: the depth -----------------------------------------------
    if zone_depth_ft is None:
        if zone_top_ft is not None and zone_bottom_ft is not None:
            zone_depth_ft = 0.5 * (zone_top_ft + zone_bottom_ft)
            flags.append(
                f"zone depth taken as the midpoint of {zone_top_ft:g}-"
                f"{zone_bottom_ft:g} ft")
        else:
            return Refusal(
                reason="no zone depth. The output of this screen is an instruction to "
                       "re-enter a well at a depth, and the depth cannot be derived "
                       "from the DST: Chapter 8 names the tested interval only by its "
                       "thickness h, and for a single-packer test with tail pipe the "
                       "tested interval runs packer-to-bottom, which the source does "
                       "not define",
                needed=("zone_depth_ft, or both zone_top_ft and zone_bottom_ft, from "
                        "the completion record or the driller's log",),
                source=EARLOUGHER_SEC_81)

    # --- the damage correction (Eq. 8.3) ------------------------------------
    ideal_rate = None
    fraction_of_ideal = None
    if damage_ratio is not None:
        ideal_rate = q * damage_ratio
        fraction_of_ideal = 1.0 / damage_ratio
        flags.append(
            f"damage ratio {damage_ratio:g}: the well tested at "
            f"{100.0 * fraction_of_ideal:.1f} percent of its ideal capacity, so the "
            f"ideal (undamaged) rate is {ideal_rate:.3g} {rate_unit}. " +
            EX_81_DAMAGE_READING)
    else:
        flags.append(
            "no damage ratio supplied, so the as-tested rate is all there is. A DST is "
            "a damaged, open-hole, short-duration temporary completion; Sec. 8.1 says "
            "its data \"may be used to estimate the well's flow potential with a "
            "regular completion that uses stimulation techniques to remove damage\". "
            "A rule-out computed on this rate alone is NOT conclusive, because a "
            "stimulated recompletion would make more")

    flags.append("vintage asymmetry: " + VINTAGE_ASYMMETRY)
    if test_year is not None:
        flags.append(
            f"tested in {int(test_year)}; that year dates the ECONOMICS of the "
            "original decision not to complete, and dates nothing about the rock")

    assumptions.update({
        "route": route,
        "rate_equation": "q = V [bbl] x 1,440 [min/D] / t_flow [min] (Example 8.1)",
        "damage_ratio_definition": EQ_83,
        "ideal_rate_basis": "the damage ratio is a ratio of productivity indices, so "
                            "q_ideal = q_dst x DR at the same drawdown",
        "pressure_basis": pressure_basis,
        "fluid_classification": "none. The recovery description is carried verbatim "
                                "and never classified; Chapter 8 enumerates no fluid "
                                "taxonomy and dst_validate's rule is that an "
                                "observation the source does not name is refused "
                                "rather than classified",
        "flow_period": flow_period,
    })

    return Quantity(
        float(q), rate_unit, METHOD_INDICATION, EARLOUGHER_SEC_81,
        inputs={
            "route": route,
            "recovery_bbl": recovery_bbl,
            "per_section": per_section,
            "recovery_volume_result": recovery_quantity,
            "flow_period_min": flow_period_min,
            "flow_period": flow_period,
            "fluid_recovered": fluid_recovered,
            "evidence_channels": {
                "types_of_fluids_recovered": {"satisfied": True,
                                              "value": fluid_recovered},
                "flow_rates_observed": {"satisfied": True, "value": float(q),
                                        "unit": rate_unit, "route": route},
            },
            "damage_ratio": damage_ratio,
            "ideal_rate": ideal_rate,
            "fraction_of_ideal_capacity": fraction_of_ideal,
            "reservoir_pressure_psig": reservoir_pressure_psig,
            "p_isi_psig": p_isi_psig,
            "p_fsi_psig": p_fsi_psig,
            "zone_depth_ft": zone_depth_ft,
            "zone_top_ft": zone_top_ft,
            "zone_bottom_ft": zone_bottom_ft,
            "test_year": test_year,
            "chart_assessed": validation is not None,
            "chart_findings": findings,
        },
        assumptions=assumptions,
        flags=tuple(flags))


# --- part 2: the caller half ------------------------------------------------


def dst_recompletion_screen(
    indication,
    *,
    price_usd_per_unit=None,
    price_unit=None,
    operating_cost_usd_per_well_per_year=None,
    workover_cost_usd=None,
    discount_rate_fraction=None,
    evaluation_year=None,
    use_damage_corrected=True,
):
    """Screen a DST-indicated rate against the caller's own economics.

    Refuses unless all four of gas/oil price, per-well operating cost, workover
    cost and discount rate are supplied. That refusal is the headline behaviour of
    this tool, not an edge case: nothing in the corpus establishes an economic
    threshold, and a wrong one recommends spending money.

    Returns `q_screen / q_breakeven` as a ratio. `ratio < 1` is `ruled_out` and is
    conclusive; `ratio >= 1` is `not_ruled_out` and is NOT a finding of
    commerciality. There is no third verdict and no yes/no.
    """
    if indication is None:
        raise ValueError(
            "indication is required: pass the result of dst_zone_indication. This "
            "tool screens a DST-indicated rate and does not derive one")
    if _dst_is_refusal(indication):
        return Refusal(
            reason="no DST indication to screen: " + getattr(indication, "reason", ""),
            needed=tuple(getattr(indication, "needed", ()) or ()),
            source=getattr(indication, "source", EARLOUGHER_SEC_81) or EARLOUGHER_SEC_81)
    if not isinstance(indication, Quantity):
        raise ValueError(
            "indication must be the Quantity or Refusal returned by "
            f"dst_zone_indication, got {type(indication).__name__}")

    # --- refusal 12: the four inputs, checked before anything else ----------
    #
    # Deliberately ahead of the unit-consistency check. A caller who has not
    # supplied the economics should be told that, not handed a lecture about
    # units on the one number they did supply.
    supplied = {
        "price_usd_per_unit": price_usd_per_unit,
        "operating_cost_usd_per_well_per_year": operating_cost_usd_per_well_per_year,
        "workover_cost_usd": workover_cost_usd,
        "discount_rate_fraction": discount_rate_fraction,
    }
    missing = [(name, desc) for name, desc in ECONOMIC_INPUTS if supplied[name] is None]
    if missing:
        names = ", ".join(name for name, _ in missing)
        return Refusal(
            reason=f"Missing: {names}. Each has no default in this tool and none may "
                   "be inferred from the DST, from the test year, or from any "
                   "published figure in the corpus. " + COMMERCIAL_TODAY_SENTENCE
                   + " " + NO_CONSERVATIVE_DEFAULT,
            needed=tuple(f"{name}: {desc}" for name, desc in missing),
            source=COMMERCIAL_TODAY_SOURCE)

    # --- programmer errors --------------------------------------------------
    rate_unit = indication.unit
    if rate_unit not in RATE_UNITS_115:
        raise ValueError(
            f"the indication is in {rate_unit!r}; this screen prices "
            f"{RATE_UNITS_115}")
    expected_price_unit = PRICE_UNIT_FOR_RATE[rate_unit]
    if price_unit is None:
        raise ValueError(
            "price_unit is required whenever a price is given; an unlabelled price "
            f"is a unit error. Expected {expected_price_unit!r} for an indication in "
            f"{rate_unit!r}")
    if price_unit != expected_price_unit:
        raise ValueError(
            f"price_unit {price_unit!r} does not match the indicated rate unit "
            f"{rate_unit!r}; expected {expected_price_unit!r}. A $/Mcf price against "
            "an STB/D rate is a unit error, not a judgment call")

    price = _dst_float("price_usd_per_unit", price_usd_per_unit)
    if price <= 0:
        raise ValueError(f"price_usd_per_unit must be positive, got {price}")
    opex = _dst_float("operating_cost_usd_per_well_per_year",
                      operating_cost_usd_per_well_per_year)
    workover = _dst_float("workover_cost_usd", workover_cost_usd)
    rate = _dst_float("discount_rate_fraction", discount_rate_fraction)

    # --- which rate is screened --------------------------------------------
    flags: list[str] = []
    ideal_rate = indication.inputs.get("ideal_rate")
    damage_ratio = indication.inputs.get("damage_ratio")
    if use_damage_corrected and ideal_rate is not None:
        q_screen = float(ideal_rate)
        rate_basis = (f"damage-corrected ideal rate, q_dst x DR = "
                      f"{indication.value:g} x {damage_ratio:g}")
        flags.append(
            "screening on the damage-corrected ideal rate. A screen that can only "
            "rule OUT must rule out on the most favourable rate the DST supports, or "
            "it discards zones a stimulated recompletion would have made - which is "
            "the case Sec. 8.1 explicitly contemplates. Whether the ideal rate is "
            "achievable is a judgment, not a source claim; set "
            "use_damage_corrected=False to screen on the as-tested rate")
    else:
        q_screen = float(indication.value)
        rate_basis = "as-tested DST rate"
        if ideal_rate is None:
            flags.append(
                "screening on the as-tested rate because no damage ratio was "
                "available. A ruled_out verdict on this basis is NOT conclusive: a "
                "stimulated recompletion would make more than the DST did")
        else:
            flags.append(
                "screening on the as-tested rate at the caller's request "
                "(use_damage_corrected=False), although a damage ratio was available")

    # --- the arithmetic -----------------------------------------------------
    revenue_per_unit_rate_per_year = price * DAYS_PER_YEAR      # $ / (unit/D) / yr
    q_operating = opex / revenue_per_unit_rate_per_year
    q_breakeven = (opex + rate * workover) / revenue_per_unit_rate_per_year
    net_margin_usd_per_year = q_screen * DAYS_PER_YEAR * price - opex

    if rate == 0.0:
        pv_of_margin = None
        pv_minus_workover = None
        flags.append(
            "discount_rate_fraction is zero: the perpetuity annuitizes the workover "
            "to nothing, so the workover cost drops out of the break-even entirely "
            f"and q_breakeven collapses to the operating break-even "
            f"({q_operating:.4g} {rate_unit}). Legal and degenerate. The present-value "
            "reconciliation is undefined at r = 0 and is checked against the annual "
            "net margin instead")
        reconcile_positive = net_margin_usd_per_year >= 0.0
    else:
        pv_of_margin = net_margin_usd_per_year / rate
        pv_minus_workover = pv_of_margin - workover
        reconcile_positive = pv_minus_workover >= 0.0

    ratio = q_screen / q_breakeven
    verdict = NOT_RULED_OUT if ratio >= 1.0 else RULED_OUT

    # Two independent derivations of one quantity. If they ever disagree, that IS
    # the bug, and it is a programmer error rather than a refusal.
    if (ratio >= 1.0) != reconcile_positive and abs(ratio - 1.0) > 1e-9:
        raise RuntimeError(
            "internal inconsistency: the rate test and the dollar test disagree "
            f"(ratio={ratio!r}, pv_minus_workover={pv_minus_workover!r}, "
            f"net_margin={net_margin_usd_per_year!r})")

    flags.insert(0, f"verdict {verdict}: {VERDICT_MEANINGS[verdict]}")
    flags.append("house arithmetic: " + HOUSE_ARITHMETIC_NOTE)
    flags.append(ONE_SIDED_NOTE)
    flags.append("vintage asymmetry: " + VINTAGE_ASYMMETRY)
    flags.append(NOT_A_SUBSTITUTE_BENCHMARK)
    if q_screen < q_operating:
        flags.append(
            f"the zone does not even clear the operating break-even "
            f"({q_operating:.4g} {rate_unit}); it would lose money before the "
            "workover is counted")
    elif verdict == RULED_OUT:
        flags.append(
            f"the zone clears the operating break-even ({q_operating:.4g} "
            f"{rate_unit}) but does not repay the workover. A screen tested only "
            "against operating cost would have passed it")
    test_year = indication.inputs.get("test_year")
    if test_year is not None and evaluation_year is not None:
        flags.append(
            f"the DST is {int(evaluation_year) - int(test_year)} years older than the "
            f"economics screening it ({int(test_year)} test, {int(evaluation_year)} "
            "evaluation). That gap is the reason this tool exists and the reason none "
            "of the four inputs may be defaulted from anything historical")
    for f in indication.flags:
        flags.append("indication: " + f)

    return Quantity(
        float(ratio), "ratio", METHOD_SCREEN, COMMERCIAL_TODAY_SOURCE,
        inputs={
            "verdict": verdict,
            "q_screen": q_screen,
            "rate_basis": rate_basis,
            "rate_unit": rate_unit,
            "q_breakeven": q_breakeven,
            "q_operating": q_operating,
            "net_margin_usd_per_year": net_margin_usd_per_year,
            "pv_of_margin_usd": pv_of_margin,
            "pv_minus_workover_usd": pv_minus_workover,
            "price_usd_per_unit": price,
            "price_unit": price_unit,
            "operating_cost_usd_per_well_per_year": opex,
            "workover_cost_usd": workover,
            "discount_rate_fraction": rate,
            "evaluation_year": evaluation_year,
            "days_per_year": DAYS_PER_YEAR,
            "indication": indication,
            "zone_depth_ft": indication.inputs.get("zone_depth_ft"),
            "fluid_recovered": indication.inputs.get("fluid_recovered"),
        },
        assumptions={
            "status": STATUS_CALLER_115,
            "economics_source": "the caller. " + COMMERCIAL_TODAY_SENTENCE,
            "arithmetic_status": STATUS_HOUSE_115,
            "break_even": "q_be = (opex_per_year + r x workover) / (price x 365)",
            "perpetuity": "PV = (q x 365 x price - opex) / r, a flat never-declining "
                          "stream. Every Arps stream starting at the same rate is "
                          "worth strictly less, so a ruled_out verdict survives any "
                          "decline model",
            "reconciliation": "ratio >= 1 and pv_minus_workover >= 0 are the same test "
                              "for r > 0 and are both computed; disagreement raises",
            "no_endorsement": VERDICT_MEANINGS[NOT_RULED_OUT],
            "not_a_substitute": NOT_A_SUBSTITUTE_BENCHMARK,
            "vintage_asymmetry": VINTAGE_ASYMMETRY,
        },
        flags=tuple(flags))

