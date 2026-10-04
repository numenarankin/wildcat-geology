"""Scanned-log tools: header reading, depth registration, curve digitizing.

None of these three performs optical character recognition or image processing,
and that is the design rather than a shortfall. No LLM call may appear in a tool
implementation, and the build's rule is that a tool which needs a model to decide
something has a missing input. So the pixels-to-symbols step is an **input** to
each of these tools and the deterministic remainder is what they own:

- `raster_header_ocr` takes OCR text and locates the RRC's mandatory A-P header
  items in it, against the same contract `header_extract` uses. It reports
  disagreement between Permanent Datum and Log Measured From; it does not resolve
  it, because that is `datum_resolve`'s job and it is the gate the structural math
  depends on. Every field carries its evidence class, since a value read off a
  blueline is not the same evidence as one declared in a LAS file.
- `raster_depth_register` takes observed tie points and fits the pixel-to-depth
  mapping. It refuses to register tie points from two different logging runs into
  one mapping: `asquith#64` states that runs differ in depth registry of beds, so
  blending them is wrong rather than merely uncertain.
- `raster_curve_digitize` takes an already-traced polyline and maps it through a
  declared track scale. A four-decade resistivity scale is logarithmic, and
  reading it linearly is a silent order-of-magnitude error, so scale kind and
  direction are declared and never assumed. Wrapped and backup curves refuse:
  nothing in the corpus states how they are drawn.

The plausibility bands in the header reader are house rules, declared as such,
and they only ever raise a flag. None of them rejects or corrects a value.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Protocol, Sequence, runtime_checkable
from typing import Any, Iterable, Mapping, Sequence
from typing import Sequence
import math
import re

from .header import RRC_HEADER_ITEMS
from .result import Quantity, Range, Refusal
from .result import Quantity, Range, Refusal  # noqa: F401  (Range re-exported for the module)

# ---------------------------------------------------------------------------
# 08_raster_depth_register
# Pixel-to-depth registration for a scanned raster log. Tool #8, group A.
# ---------------------------------------------------------------------------

ASQUITH_GRID = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#11"
ASQUITH_RUNS = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#64"

# asquith#64: "depth is indicated by a fine line every 2 ft, a medium-thick line
# every 10 ft, and a heavy line every 50 ft" — stated of the Chapter 10 case-study
# logs. asquith#11 gives the fine level only ("each vertical increment equal to
# 2 ft"). NEITHER names a vertical scale, so this is a lookup for a caller that
# has decided its scan is an Asquith-style API-format log. It is never applied as
# a default: see `grid_increment_ft`, which is None unless the caller declares it.
ASQUITH_GRID_FT: dict[str, float] = {"fine": 2.0, "medium": 10.0, "heavy": 50.0}

# asquith#64: log values "may be peak or trough values from as much as 1 ft above
# or below the listed depths", attributed to differing vertical resolutions and
# to multi-run depth-registry. The source's literal number for depths compared
# across runs. tool-catalog.md widens it to +/-2 ft for perf-in-zone; that
# widening is the catalog's decision for a different question and is not made here.
CROSS_RUN_REGISTRY_FT = 1.0

_DEPTH_REFERENCE_NOTE = "as supplied on the tie points; datum not resolved here"
_EPS_GRID_FT = 1e-6


def _check_finite(name: str, value: float) -> float:
    """Non-finite input is programmer error, not a refusal."""
    v = float(value)
    if not math.isfinite(v):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    return v


@dataclass(frozen=True)
class TiePoint:
    """One observed correspondence between an image row and a measured depth.

    `pixel_row` counts from the TOP of the image and increases DOWNWARD, which is
    the raster row order of every image format. Depth increases downward too, so
    depth increases with `pixel_row`. `run_id` has no default: keeping runs apart
    is the point (asquith#64).
    """

    pixel_row: float
    depth_ft: float
    run_id: str
    label: str = ""

    def __post_init__(self) -> None:
        _check_finite("pixel_row", self.pixel_row)
        _check_finite("depth_ft", self.depth_ft)
        if not isinstance(self.run_id, str):
            raise TypeError("TiePoint.run_id must be a string naming the logging run")


@dataclass(frozen=True)
class DepthRegistration:
    """The pixel-to-depth mapping for ONE logging run, with its misfit and span.

    This is the object `raster_curve_digitize` consumes. Contract:
      1. one registration per run; never pool tie points across runs
      2. clip the trace to `pixel_span` / `depth_span` — there is no
         extrapolation switch and there will not be one
      3. propagate `flags` onto every digitized sample
      4. `residual_rms_ft is None` means a two-point fit whose accuracy is
         unverified — it does not mean the residual was zero
    """

    run_id: str
    depth_per_pixel: Quantity
    depth_at_row_zero: Quantity
    depth_span: Range
    pixel_span: tuple[float, float]
    residual_rms_ft: Quantity | None
    residual_max_ft: Quantity | None
    implied_scan_dpi: Quantity | None
    n_tie_points: int
    tie_points: tuple[TiePoint, ...]
    flags: tuple[str, ...] = ()
    source: str = ASQUITH_RUNS
    assumptions: dict[str, object] = field(default_factory=dict)

    # -- the mapping ------------------------------------------------------

    def covers(self, pixel_row: float) -> bool:
        """Cheap predicate for clipping, so a digitizer need not build refusals."""
        lo, hi = self.pixel_span
        return lo <= float(pixel_row) <= hi

    def covers_depth(self, depth_ft: float) -> bool:
        return self.depth_span.low <= float(depth_ft) <= self.depth_span.high

    def depth_at_pixel(self, pixel_row: float) -> Quantity | Refusal:
        """Depth at an image row. Refuses outside the registered span."""
        row = _check_finite("pixel_row", pixel_row)
        lo, hi = self.pixel_span
        if not (lo <= row <= hi):
            return Refusal(
                reason=(
                    f"pixel row {row:g} lies outside the registered span "
                    f"[{lo:g}, {hi:g}]; this tool does not extrapolate a depth "
                    "beyond the outermost tie point"
                ),
                needed=(
                    f"a tie point on run {self.run_id!r} at or beyond row {row:g}",
                ),
                source=self.source,
            )
        m = self.depth_per_pixel.value
        b = self.depth_at_row_zero.value
        return Quantity(
            value=b + m * row,
            unit="ft",
            method="affine pixel-to-depth registration (least-squares tie-point fit)",
            source=self.source,
            inputs={
                "pixel_row": row,
                "depth_per_pixel_ft": m,
                "depth_at_row_zero_ft": b,
                "run_id": self.run_id,
            },
            assumptions=self._depth_assumptions(),
            flags=self.flags,
        )

    def pixel_at_depth(self, depth_ft: float) -> Quantity | Refusal:
        """Image row for a depth. Refuses outside the registered span."""
        d = _check_finite("depth_ft", depth_ft)
        if not (self.depth_span.low <= d <= self.depth_span.high):
            return Refusal(
                reason=(
                    f"depth {d:g} ft lies outside the registered span "
                    f"[{self.depth_span.low:g}, {self.depth_span.high:g}] ft on run "
                    f"{self.run_id!r}; this tool does not extrapolate"
                ),
                needed=(f"a tie point on run {self.run_id!r} at or beyond {d:g} ft",),
                source=self.source,
            )
        m = self.depth_per_pixel.value
        b = self.depth_at_row_zero.value
        return Quantity(
            value=(d - b) / m,
            unit="px",
            method="affine depth-to-pixel registration (least-squares tie-point fit)",
            source=self.source,
            inputs={
                "depth_ft": d,
                "depth_per_pixel_ft": m,
                "depth_at_row_zero_ft": b,
                "run_id": self.run_id,
            },
            assumptions=self._depth_assumptions(),
            flags=self.flags,
        )

    def _depth_assumptions(self) -> dict[str, object]:
        out = dict(self.assumptions)
        out["residual_rms_ft"] = (
            None if self.residual_rms_ft is None else self.residual_rms_ft.value
        )
        out["residual_max_ft"] = (
            None if self.residual_max_ft is None else self.residual_max_ft.value
        )
        out["cross_run_depth_allowance_ft"] = CROSS_RUN_REGISTRY_FT
        out["depth_reference"] = _DEPTH_REFERENCE_NOTE
        return out


def cross_run_depth_allowance() -> Quantity:
    """The depth-registry allowance between logging runs. asquith#64.

    For a caller comparing a depth registered on one run with a depth registered
    on another. Not part of the within-run fit uncertainty.
    """
    return Quantity(
        value=CROSS_RUN_REGISTRY_FT,
        unit="ft",
        method="multi-run depth-registry allowance (Asquith Ch. 10 work table)",
        source=ASQUITH_RUNS,
        inputs={},
        assumptions={
            "quote": (
                "log values recorded at each depth actually may be peak or trough "
                "values from as much as 1 ft above or below the listed depths ... "
                "a suite of logs generally requires more than one logging run ... "
                "some logs differ slightly in depth-registry of beds"
            ),
            "covers": "differing vertical resolutions AND multi-run registry, jointly",
        },
        flags=(
            "tool-catalog.md widens this to +/-2 ft for perf-in-zone; that widening "
            "is a different decision and is not applied here",
        ),
    )


def raster_depth_register(
    tie_points: Sequence[TiePoint],
    run_id: str,
    *,
    grid_increment_ft: float | None = None,
    scale_inches_per_100ft: float | None = None,
    scan_dpi: float | None = None,
    scale_disagreement_tolerance_ft: float = CROSS_RUN_REGISTRY_FT,
) -> DepthRegistration | Refusal:
    """Fit the pixel-to-depth mapping for one logging run from observed tie points.

    See `specs/08-raster_depth_register.md`. Refuses on: one tie point (no scale
    derivable), an unnamed run, tie points from more than one run (asquith#64),
    duplicate or contradictory tie points, and a mapping that comes out inverted.
    `depth_at_pixel` / `pixel_at_depth` refuse outside the registered span.
    """
    if not isinstance(run_id, str):
        raise TypeError("run_id must be a string naming the logging run")
    pts = list(tie_points)
    for p in pts:
        if not isinstance(p, TiePoint):
            raise TypeError(f"tie_points must contain TiePoint instances, got {type(p).__name__}")
    for name, val in (
        ("grid_increment_ft", grid_increment_ft),
        ("scale_inches_per_100ft", scale_inches_per_100ft),
        ("scan_dpi", scan_dpi),
    ):
        if val is not None:
            v = _check_finite(name, val)
            if v <= 0:
                raise ValueError(f"{name} must be positive, got {val!r}")
    _check_finite("scale_disagreement_tolerance_ft", scale_disagreement_tolerance_ft)

    # R2 — the run must be named. asquith#64: registry is per run, so an unnamed
    # run cannot be kept apart from another.
    if not run_id.strip():
        return Refusal(
            reason="the logging run this scan belongs to was not stated",
            needed=("run_id, and the same run_id on every tie point",),
            source=ASQUITH_RUNS,
        )

    # R3 — one run per mapping. The core asquith#64 refusal: fitting across runs
    # blends two depth references and the answer is wrong, not merely uncertain.
    foreign = sorted({p.run_id for p in pts if p.run_id != run_id})
    if foreign:
        return Refusal(
            reason=(
                f"tie points from run(s) {foreign} cannot be registered into a "
                f"mapping for run {run_id!r}: a log suite generally requires more "
                "than one logging run and the runs differ in depth-registry of beds"
            ),
            needed=(f"tie points observed on run {run_id!r} only",),
            source=ASQUITH_RUNS,
        )

    # R1 — a single tie point fixes an offset but not a scale. A declared scale is
    # metadata about the paper, not a measurement of this scan, so it does not
    # rescue this case and is not consulted here.
    if len(pts) < 2:
        return Refusal(
            reason=(
                f"{len(pts)} tie point(s) supplied; a single tie point fixes an "
                "offset but not a depth-per-pixel scale, and a declared log scale "
                "is not a measurement of this scan"
            ),
            needed=("a second tie point at a different pixel row on the same run",),
            source=ASQUITH_GRID,
        )

    ordered = sorted(pts, key=lambda p: p.pixel_row)

    # R4 / R5 — contradictory or duplicated observations.
    for a, b in zip(ordered, ordered[1:]):
        if a.pixel_row == b.pixel_row:
            return Refusal(
                reason=(
                    f"two tie points sit at pixel row {a.pixel_row:g} "
                    f"({a.depth_ft:g} ft and {b.depth_ft:g} ft); one image row "
                    "carries one depth"
                ),
                needed=("tie points at distinct pixel rows",),
                source=ASQUITH_GRID,
            )
    by_depth = sorted(pts, key=lambda p: p.depth_ft)
    for a, b in zip(by_depth, by_depth[1:]):
        if a.depth_ft == b.depth_ft:
            return Refusal(
                reason=(
                    f"depth {a.depth_ft:g} ft is claimed at two pixel rows "
                    f"({a.pixel_row:g} and {b.pixel_row:g}); one depth sits at one row"
                ),
                needed=("tie points at distinct depths",),
                source=ASQUITH_GRID,
            )

    # R6 — depth increases downward, and image rows count downward from the top.
    # An inverted pair is a coordinate-convention error or a mislabelled grid
    # line. This tool does not flip the sign to accommodate it.
    for a, b in zip(ordered, ordered[1:]):
        if b.depth_ft < a.depth_ft:
            return Refusal(
                reason=(
                    f"depth decreases downward between rows {a.pixel_row:g} "
                    f"({a.depth_ft:g} ft) and {b.pixel_row:g} ({b.depth_ft:g} ft); "
                    "pixel_row is counted from the top of the image and increases "
                    "downward, so depth must increase with row. This tool does not "
                    "invert the sign convention for you"
                ),
                needed=(
                    "pixel rows measured from the top of the image, or a corrected "
                    "depth label on the offending tie point",
                ),
                source=ASQUITH_GRID,
            )

    n = len(ordered)
    xs = [p.pixel_row for p in ordered]
    ys = [p.depth_ft for p in ordered]
    x_bar = sum(xs) / n
    y_bar = sum(ys) / n
    sxy = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, ys))
    sxx = sum((x - x_bar) ** 2 for x in xs)
    if sxx == 0.0:  # every tie point on one row; R4 already caught the pairs
        return Refusal(
            reason="all tie points sit on one pixel row; no depth-per-pixel scale exists",
            needed=("tie points at distinct pixel rows",),
            source=ASQUITH_GRID,
        )
    slope = sxy / sxx
    intercept = y_bar - slope * x_bar

    # R7 — defensive. Unreachable given R6 (strictly increasing y in x forces
    # sxy > 0), kept so the invariant is enforced where the number is made.
    if slope <= 0:
        return Refusal(
            reason=(
                f"the fitted mapping inverts depth (slope {slope:g} ft/px); depth "
                "must increase downward with pixel row"
            ),
            needed=("tie points whose depths increase with pixel row",),
            source=ASQUITH_GRID,
        )

    # Centered form: algebraically identical to y - (slope*x + intercept), but it
    # does not round-trip through the intercept, so a sub-foot residual is not
    # reported from the difference of two five-figure depths.
    residuals = [y - y_bar - slope * (x - x_bar) for x, y in zip(xs, ys)]
    row_min, row_max = xs[0], xs[-1]
    span_px = row_max - row_min

    flags: list[str] = []
    assumptions: dict = {
        "run_id": run_id,
        "fit": "ordinary least squares, tie points weighted equally",
        "pixel_convention": "row 0 at top of image, increasing downward",
        "depth_reference": _DEPTH_REFERENCE_NOTE,
        "n_tie_points": n,
    }

    # Residual statistics. Two tie points always fit exactly; reporting residual
    # zero there would read as a quality statement and it is not one.
    if n >= 3:
        rms = math.sqrt(sum(r * r for r in residuals) / n)
        rmax = max(abs(r) for r in residuals)
        residual_rms = Quantity(
            value=rms,
            unit="ft",
            method="RMS residual of the tie-point fit (denominator n, not n-2)",
            source=ASQUITH_GRID,
            inputs={"residuals_ft": tuple(residuals), "n": n},
            assumptions={"note": "a descriptive misfit, not a regression standard error"},
        )
        residual_max = Quantity(
            value=rmax,
            unit="ft",
            method="largest absolute residual of the tie-point fit",
            source=ASQUITH_GRID,
            inputs={"residuals_ft": tuple(residuals), "n": n},
            assumptions={
                "meaning": "worst disagreement between a read depth and the fitted line",
            },
        )
        if rmax > 0:
            flags.append(
                f"tie points are not collinear: worst residual {rmax:.3g} ft, "
                f"RMS {rms:.3g} ft — the scan is skewed, the paper stretched, or a "
                "tie point is misread"
            )
    else:
        residual_rms = None
        residual_max = None
        flags.append(
            "two tie points: the mapping is exactly determined, so the residual is "
            "not measurable and scan skew or paper stretch is undetectable"
        )

    depth_per_pixel = Quantity(
        value=slope,
        unit="ft/px",
        method="least-squares slope of depth against pixel row",
        source=ASQUITH_GRID,
        inputs={
            "pixel_rows": tuple(xs),
            "depths_ft": tuple(ys),
            "n": n,
            "run_id": run_id,
        },
        assumptions=dict(assumptions),
    )
    depth_at_row_zero = Quantity(
        value=intercept,
        unit="ft",
        method="least-squares intercept of depth against pixel row",
        source=ASQUITH_GRID,
        inputs={"depth_per_pixel_ft": slope, "x_bar": x_bar, "y_bar": y_bar},
        assumptions=dict(assumptions),
        flags=(
            ()
            if row_min <= 0 <= row_max
            else ("row 0 lies outside the tie-point span; this intercept is a "
                  "mapping parameter, not a registered depth",)
        ),
    )
    depth_top = intercept + slope * row_min
    depth_bottom = intercept + slope * row_max
    depth_span = Range(
        low=depth_top,
        high=depth_bottom,
        unit="ft",
        method="registered depth span (fitted mapping over the tie-point rows)",
        source=ASQUITH_GRID,
        members={"pixel_row_top": row_min, "pixel_row_bottom": row_max},
    )

    # -- checks. All flags. None of these refuse: the tie points are the
    # observations and the declared scale/grid is metadata, so the mapping stands
    # and the declaration is what gets doubted.
    implied_dpi: Quantity | None = None
    ft_per_paper_inch: float | None = None
    if scale_inches_per_100ft is not None:
        ft_per_paper_inch = 100.0 / float(scale_inches_per_100ft)
        assumptions["scale_inches_per_100ft"] = float(scale_inches_per_100ft)
        assumptions["ft_per_paper_inch"] = ft_per_paper_inch
        implied_dpi = Quantity(
            value=ft_per_paper_inch / slope,
            unit="px/in",
            method="scan resolution implied by the fit and the declared vertical scale",
            source=ASQUITH_GRID,
            inputs={
                "ft_per_paper_inch": ft_per_paper_inch,
                "depth_per_pixel_ft": slope,
            },
            assumptions={
                "scale_declared_as": f"{scale_inches_per_100ft:g} in = 100 ft",
                "note": "a second expression of the fitted slope; compare with a known scan_dpi",
            },
        )

    if grid_increment_ft is not None:
        grid = float(grid_increment_ft)
        assumptions["grid_increment_ft"] = grid
        grid_px = grid / slope
        assumptions["grid_spacing_px"] = grid_px
        # Tie points read off the depth track sit on grid lines, so their depth
        # differences must be whole multiples of the increment. Not a refusal: a
        # caller may legitimately tie to a casing collar or a bed top.
        off_grid = []
        base = ys[0]
        for p in ordered[1:]:
            steps = (p.depth_ft - base) / grid
            if abs(steps - round(steps)) * grid > _EPS_GRID_FT:
                off_grid.append(p)
        if off_grid:
            named = ", ".join(
                f"{p.depth_ft:g} ft" + (f" ({p.label})" if p.label else "")
                for p in off_grid
            )
            flags.append(
                f"tie point depth(s) {named} are not whole multiples of the declared "
                f"{grid:g} ft grid measured from {base:g} ft — these ties were not "
                "grid lines, or the declared increment is wrong"
            )
        if grid_px < 1.0:
            flags.append(
                f"the declared {grid:g} ft grid is {grid_px:.3g} px in this scan; "
                "below one pixel per interval the grid lines are not resolvable and "
                "cannot have been read"
            )
    else:
        flags.append(
            "no grid increment declared; grid consistency was not checked "
            "(ASQUITH_GRID_FT holds the 2/10/50 ft fine/medium/heavy grid of "
            "asquith#64, which is stated of those figures and is not scale-independent)"
        )

    if scale_inches_per_100ft is not None and scan_dpi is not None:
        expected_m = ft_per_paper_inch / float(scan_dpi)  # type: ignore[operator]
        span_error_ft = abs(expected_m - slope) * span_px
        assumptions["expected_depth_per_pixel_ft"] = expected_m
        assumptions["scale_span_error_ft"] = span_error_ft
        assumptions["scan_dpi"] = float(scan_dpi)
        if span_error_ft > scale_disagreement_tolerance_ft:
            flags.append(
                f"declared scale ({scale_inches_per_100ft:g} in = 100 ft at "
                f"{scan_dpi:g} px/in) implies {expected_m:.4g} ft/px but the tie "
                f"points give {slope:.4g} ft/px — {span_error_ft:.4g} ft of "
                f"disagreement over the registered span, past the "
                f"{scale_disagreement_tolerance_ft:g} ft allowance; the tie points "
                "are the observation and the declared scale is metadata"
            )
    elif scale_inches_per_100ft is not None:
        flags.append(
            "scan_dpi not supplied; the declared vertical scale could not be "
            "checked against the tie points (any slope is consistent with any "
            "scale at some resolution)"
        )

    assumptions["cross_run_depth_allowance_ft"] = CROSS_RUN_REGISTRY_FT

    return DepthRegistration(
        run_id=run_id,
        depth_per_pixel=depth_per_pixel,
        depth_at_row_zero=depth_at_row_zero,
        depth_span=depth_span,
        pixel_span=(row_min, row_max),
        residual_rms_ft=residual_rms,
        residual_max_ft=residual_max,
        implied_scan_dpi=implied_dpi,
        n_tie_points=n,
        tie_points=tuple(ordered),
        flags=tuple(flags),
        source=ASQUITH_RUNS,
        assumptions=assumptions,
    )

# ---------------------------------------------------------------------------
# 07_raster_curve_digitize
# Tool #7 `raster_curve_digitize` — pixel coordinates to curve values.
# ---------------------------------------------------------------------------

# --- Corpus anchors -------------------------------------------------------
# trieste#3 "Scales": the logarithmic grid, the hybrid scale, and the backup
# trace whose grid position the corpus never states.
TRIESTE_SCALES = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#3"
# trieste#11: linear on tracks 2/3 for one tool, four-decade log for the next --
# the same track carries either, so track number never implies scale kind.
TRIESTE_TRACKS = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#11"
# asquith#15 Figure 3.1: GR/RHOB/DRHO left-to-right, NPHI right-to-left.
ASQUITH_FIG31 = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#15"
# asquith#11: "Resistivity increases from left to right" on a log grid; also the
# 2 ft depth increment, which belongs to raster_depth_register (#8), not here.
ASQUITH_LOGGRID = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#11"
# The verification finding that wrapped-curve handling has no source at all.
VERIFICATION_ADDENDUM = "tool-verification.md addendum, raster_curve_digitize row"

# trieste#3, p. 7-10: "Its standard form is a split four-cycle grid covering the
# range from 0.2 to 2000 ohm-m". log10(2000/0.2) == 4.0 exactly, so the source's
# "four-cycle" and its endpoints agree -- neither is an OCR corruption.
TRIESTE_STANDARD_LOG_GRID = (0.2, 2000.0)

# trieste#3: the backup range that exists but has no stated grid position.
TRIESTE_BACKUP_RANGE = (2000.0, 40000.0)

# asquith#15, Figure 3.1 caption. ONE published example log, not a standard --
# every scale drawn from here is flagged as such. It is written down so the NPHI
# direction is cited once rather than retyped from memory at each call site.
# (left_value, right_value, unit, track, note)
ASQUITH_FIG31_SCALES: dict[str, dict[str, Any]] = {
    "GR": {"left": 0.0, "right": 150.0, "unit": "API", "track": "1",
           "note": "scale increases from left to right, increments of 15 API"},
    "RHOB": {"left": 2.0, "right": 3.0, "unit": "g/cm3", "track": "2-3",
             "note": "increasing from left to right"},
    "NPHI": {"left": 0.30, "right": -0.10, "unit": "v/v", "track": "2-3",
             "note": "increasing from RIGHT TO LEFT"},
    "DRHO": {"left": -0.25, "right": 0.25, "unit": "g/cm3", "track": "3",
             "note": "increasing from left to right, track 3 only"},
}

LINEAR = "linear"
LOGARITHMIC = "logarithmic"
_SOURCED_KINDS = (LINEAR, LOGARITHMIC)

_TRACE_CAVEAT = "trace supplied by an external vectorizer; this tool did not follow the ink"


# --- The depth-register contract (tool #8) --------------------------------

@runtime_checkable
class DepthRegister(Protocol):
    """The minimum this tool assumes of `raster_depth_register` (#8).

    `y_px` is an image row increasing downward. The return is #8's own
    `Quantity` (depth, usually ft, carrying #8's method and source) or a
    `Refusal` when the row lies outside the registered span. Range handling is
    #8's business and this tool propagates the answer unchanged.

    Optional attributes read with `getattr` and never required: `datum`,
    `source`, `unit`. A missing `datum` is flagged, not refused -- the RRC
    header item M problem is #8's to carry, but a caller must be told.
    """

    def depth_at_pixel(self, y_px: float) -> Quantity | Refusal: ...


def _resolve_register(reg: Any) -> Callable[[float], Quantity | Refusal]:
    """Accept an object with `.depth_at_pixel` or a bare callable."""
    fn = getattr(reg, "depth_at_pixel", None)
    if callable(fn):
        return fn
    if callable(reg):
        return reg
    raise ValueError(
        "depth_register must expose depth_at_pixel(y_px) or be callable; "
        f"got {type(reg).__name__}"
    )


# --- The declared scale ---------------------------------------------------

@dataclass(frozen=True)
class TrackScale:
    """A track scale as the log's own heading declares it.

    Direction is carried by (`left_value`, `right_value`) and by nothing else.
    NPHI per asquith#15 is left=+0.30, right=-0.10. There is deliberately no
    `direction` flag: a second encoding of the same fact could disagree with the
    first, and that disagreement would be the bug.

    `x_left_px` must be the smaller pixel column. Image columns increase
    rightward, so "left" is unambiguous; a mirrored span would be a competing way
    to express direction.
    """

    kind: str
    left_value: float
    right_value: float
    x_left_px: float
    x_right_px: float
    unit: str
    source: str

    def __post_init__(self) -> None:
        # Programmer error, not a source limitation -> exceptions, per house rule.
        if self.x_right_px <= self.x_left_px:
            raise ValueError(
                "x_left_px must be strictly less than x_right_px; pixel columns "
                "increase rightward. Scale direction belongs in "
                "(left_value, right_value), not in the pixel order."
            )
        if self.left_value == self.right_value:
            raise ValueError("a scale whose two edges carry the same value spans nothing")
        if self.kind == LOGARITHMIC and (self.left_value <= 0.0 or self.right_value <= 0.0):
            raise ValueError(
                "a logarithmic scale needs strictly positive endpoints; "
                f"got {self.left_value} .. {self.right_value}"
            )

    @property
    def direction(self) -> str:
        """Derived for the record. Never used to compute anything."""
        return ("increases left to right" if self.right_value > self.left_value
                else "increases right to left")

    @property
    def decades(self) -> float | None:
        if self.kind != LOGARITHMIC:
            return None
        return math.log10(self.right_value / self.left_value)

    def fraction_at(self, x_px: float) -> float:
        return (x_px - self.x_left_px) / (self.x_right_px - self.x_left_px)


def published_scale_for(mnemonic: str, x_left_px: float, x_right_px: float) -> TrackScale:
    """The scale Asquith Figure 3.1 prints for a curve, on caller-supplied pixels.

    ONE example log, not a standard: results built from it are flagged. Refuses
    to guess -- an unknown mnemonic raises, on the same principle as
    `matrix_constant_lookup`.
    """
    key = mnemonic.strip().upper()
    if key not in ASQUITH_FIG31_SCALES:
        raise ValueError(
            f"no published scale for {mnemonic!r} in Asquith Figure 3.1; known: "
            f"{sorted(ASQUITH_FIG31_SCALES)}. This tool does not guess a scale."
        )
    row = ASQUITH_FIG31_SCALES[key]
    return TrackScale(
        kind=LINEAR,
        left_value=row["left"], right_value=row["right"],
        x_left_px=x_left_px, x_right_px=x_right_px,
        unit=row["unit"],
        source=f"{ASQUITH_FIG31} (Figure 3.1 example log, {key}: {row['note']})",
    )


def trieste_standard_resistivity_scale(x_left_px: float, x_right_px: float) -> TrackScale:
    """The published four-cycle grid, 0.2 to 2000 ohm-m (trieste#3)."""
    lo, hi = TRIESTE_STANDARD_LOG_GRID
    return TrackScale(
        kind=LOGARITHMIC, left_value=lo, right_value=hi,
        x_left_px=x_left_px, x_right_px=x_right_px,
        unit="ohm-m",
        source=f"{TRIESTE_SCALES} (standard split four-cycle grid, 0.2-2000 ohm-m)",
    )


# --- The atomic sourced operation -----------------------------------------

def curve_value_at_pixel(x_px: float, scale: TrackScale,
                         edge_tolerance_px: float = 0.0) -> Quantity | Refusal:
    """Pixel column -> curve value, through the declared scale.

    linear:      v = left + f * (right - left)
    logarithmic: v = left * (right / left) ** f

    The ratio form is used rather than 10 ** (log10(left) + f * span) because it
    returns the declared endpoint exactly at f = 0 and f = 1, where the
    log/antilog round trip does not.
    """
    refusal = _scale_refusal(scale)
    if refusal is not None:
        return refusal
    if edge_tolerance_px < 0.0:
        raise ValueError("edge_tolerance_px cannot be negative")

    if x_px < scale.x_left_px - edge_tolerance_px or x_px > scale.x_right_px + edge_tolerance_px:
        side = "left" if x_px < scale.x_left_px else "right"
        return Refusal(
            reason=(
                f"pixel x={x_px:g} is off the declared scale "
                f"[{scale.x_left_px:g}, {scale.x_right_px:g}] px past the {side} edge; "
                f"the trace is off-scale or clipped and is not extrapolated"
            ),
            needed=("a scale span that contains the trace, or a backup-trace convention",),
            source=scale.source,
        )

    f = scale.fraction_at(x_px)
    if scale.kind == LINEAR:
        value = scale.left_value + f * (scale.right_value - scale.left_value)
        method = f"linear track scale, {scale.direction}"
        source = f"{TRIESTE_TRACKS}; direction convention {ASQUITH_FIG31}"
    else:
        value = scale.left_value * (scale.right_value / scale.left_value) ** f
        # abs(): `decades` is signed because it is log10(right/left), and a
        # right-to-left grid gives a negative. A "-1.30103 decades" label is
        # nonsense in a provenance string; direction is already stated beside it.
        method = (f"logarithmic track scale ({abs(scale.decades):g} decades), "
                  f"{scale.direction}")
        source = f"{TRIESTE_SCALES}; direction convention {ASQUITH_LOGGRID}"

    flags: list[str] = [_TRACE_CAVEAT]
    if x_px <= scale.x_left_px or x_px >= scale.x_right_px:
        flags.append("sample sits at the scale edge - possible pegged/clipped trace")

    return Quantity(
        value=value, unit=scale.unit, method=method, source=source,
        inputs={"x_px": x_px, "x_left_px": scale.x_left_px,
                "x_right_px": scale.x_right_px, "fraction": f,
                "left_value": scale.left_value, "right_value": scale.right_value},
        assumptions={"scale_kind": scale.kind, "direction": scale.direction,
                     "unit": scale.unit, "scale_source": scale.source},
        flags=tuple(flags),
    )


def _scale_refusal(scale: TrackScale) -> Refusal | None:
    """Whole-scale refusals shared by both entry points."""
    if scale.kind == "hybrid":
        return Refusal(
            reason=(
                "hybrid scale: trieste#3 describes the LL3 hybrid grid as linear "
                "resistivity over the first half of the track and linear "
                "conductivity over the second, but prints no value at the "
                "breakpoint, so the pixel-to-value map does not exist"
            ),
            needed=("the resistivity value at the hybrid grid's midpoint (Fig. 7-15a)",),
            source=TRIESTE_SCALES,
        )
    if scale.kind not in _SOURCED_KINDS:
        return Refusal(
            reason=f"unrecognised scale kind {scale.kind!r}; only {list(_SOURCED_KINDS)} are sourced",
            needed=("a scale kind the corpus describes",),
            source=TRIESTE_SCALES,
        )
    if not scale.source:
        return Refusal(
            reason=(
                "the track scale has no stated provenance; an undeclared scale is "
                "the order-of-magnitude error this tool exists to prevent"
            ),
            needed=("the scale as printed on the log heading, or a raster_header_ocr result",),
            source=TRIESTE_TRACKS,
        )
    if not scale.unit:
        return Refusal(
            reason="the track scale declares no unit; a curve value without a unit is not a Quantity",
            needed=("the curve unit from the log heading",),
            source=TRIESTE_TRACKS,
        )
    return None


# --- Output ---------------------------------------------------------------

@dataclass(frozen=True)
class CurveSample:
    x_px: float
    y_px: float
    depth: Quantity | Refusal
    value: Quantity | Refusal

    @property
    def ok(self) -> bool:
        return isinstance(self.depth, Quantity) and isinstance(self.value, Quantity)


@dataclass(frozen=True)
class DigitizedCurve:
    """A container, not a physical value. Every number inside it is a Quantity."""

    mnemonic: str
    unit: str
    samples: tuple[CurveSample, ...]
    method: str
    source: str
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    @property
    def n_samples(self) -> int:
        return len(self.samples)

    @property
    def n_off_scale(self) -> int:
        return sum(1 for s in self.samples if isinstance(s.value, Refusal))

    @property
    def n_unregistered(self) -> int:
        return sum(1 for s in self.samples if isinstance(s.depth, Refusal))

    def arrays(self) -> tuple[list[float | None], list[float | None]]:
        """Parallel (depth, value) lists, None where a sample refused."""
        depths = [s.depth.value if isinstance(s.depth, Quantity) else None for s in self.samples]
        values = [s.value.value if isinstance(s.value, Quantity) else None for s in self.samples]
        return depths, values

    def __repr__(self) -> str:
        return (f"DigitizedCurve({self.mnemonic} {self.unit}, {self.n_samples} samples, "
                f"{self.n_off_scale} off-scale)")


# --- The tool -------------------------------------------------------------

def raster_curve_digitize(
    polyline_px: Sequence[tuple[float, float]],
    scale: TrackScale,
    depth_register: Any,
    trace_source: str,
    mnemonic: str = "",
    is_backup: bool = False,
    edge_tolerance_px: float = 0.0,
) -> DigitizedCurve | Refusal:
    """Traced polyline + declared scale + depth register -> depth-registered values.

    `polyline_px` is (x_px, y_px) with y increasing downward. It comes from
    outside; `trace_source` states from where, and a blank one refuses.
    """
    if edge_tolerance_px < 0.0:
        raise ValueError("edge_tolerance_px cannot be negative")

    # R1 -- unsourced, and the reason is recorded rather than worked around.
    if is_backup:
        lo, hi = TRIESTE_BACKUP_RANGE
        return Refusal(
            reason=(
                "wrapped / backup curve handling is not covered anywhere in the corpus. "
                f"trieste#3 states only that a DLL-Rxo backup trace covers {lo:g} to "
                f"{hi:g} ohm-m; it never states where on the four-decade grid that "
                "trace is drawn, what decade offset it carries, or how backup ink is "
                "told from primary ink. Without that convention the pixel-to-value map "
                "for a backup trace does not exist, and inventing one would be "
                "indistinguishable downstream from a cited one"
            ),
            needed=(
                "a log-presentation source stating the backup trace's grid convention "
                "(decade offset or wrap factor) and its line style",
            ),
            source=f"{TRIESTE_SCALES}; {VERIFICATION_ADDENDUM}",
        )

    if depth_register is None:
        return Refusal(
            reason=(
                "no depth register supplied; curve values without depths referenced to a "
                "stated datum are not usable, and this tool does not compute depth itself"
            ),
            needed=("a raster_depth_register (#8) result for this image",),
            source=ASQUITH_LOGGRID,
        )
    if not trace_source:
        return Refusal(
            reason=(
                "the traced polyline has no stated provenance. This tool does not "
                "vectorize the image: the trace is an input, and an unsourced input "
                "must not become a sourced-looking output"
            ),
            needed=("the vectorizer, digitizer or operator that produced the polyline",),
            source=VERIFICATION_ADDENDUM,
        )
    if not polyline_px:
        return Refusal(
            reason="the traced polyline is empty; nothing was traced",
            needed=("a traced curve polyline in pixel coordinates",),
            source=VERIFICATION_ADDENDUM,
        )

    refusal = _scale_refusal(scale)
    if refusal is not None:
        return refusal

    # R2 -- two x at one y is the geometric signature of a wrapped trace or of a
    # vectorizer that jumped curves. The tool will not pick one ink over another.
    seen: dict[float, float] = {}
    for x_px, y_px in polyline_px:
        prior = seen.get(y_px)
        if prior is not None and prior != x_px:
            return Refusal(
                reason=(
                    f"the traced polyline has more than one x at y={y_px:g} px "
                    f"(x={prior:g} and x={x_px:g}). That is either a wrapped/backup "
                    "trace or a vectorization that crossed between two curves; no "
                    "source states how to resolve either, so neither x is chosen"
                ),
                needed=("one x per traced depth row, or a backup-trace convention",),
                source=f"{TRIESTE_SCALES}; {VERIFICATION_ADDENDUM}",
            )
        seen[y_px] = x_px

    depth_at = _resolve_register(depth_register)

    samples: list[CurveSample] = []
    n_at_edge = 0
    for x_px, y_px in polyline_px:
        value = curve_value_at_pixel(x_px, scale, edge_tolerance_px)
        if isinstance(value, Quantity) and any("scale edge" in f for f in value.flags):
            n_at_edge += 1
        samples.append(CurveSample(x_px=float(x_px), y_px=float(y_px),
                                   depth=depth_at(y_px), value=value))

    curve = _assemble(samples, scale, trace_source, mnemonic, edge_tolerance_px,
                      depth_register, n_at_edge)
    return curve


def _assemble(samples: list[CurveSample], scale: TrackScale, trace_source: str,
              mnemonic: str, edge_tolerance_px: float, depth_register: Any,
              n_at_edge: int) -> DigitizedCurve:
    n = len(samples)
    n_off = sum(1 for s in samples if isinstance(s.value, Refusal))
    n_unreg = sum(1 for s in samples if isinstance(s.depth, Refusal))

    flags: list[str] = [_TRACE_CAVEAT]

    if "Figure 3.1 example log" in scale.source:
        flags.append("example scale from Asquith Figure 3.1, not a standard - "
                     "verify against this log's own heading")

    key = mnemonic.strip().upper()
    if key in ASQUITH_FIG31_SCALES:
        published = ASQUITH_FIG31_SCALES[key]
        published_rising = published["right"] > published["left"]
        declared_rising = scale.right_value > scale.left_value
        if published_rising != declared_rising:
            flags.append(
                f"declared direction ({scale.direction}) disagrees with the published "
                f"example for {key} ({published['note']}); the log's own heading "
                "outranks Asquith Figure 3.1, but check it"
            )

    if scale.kind == LOGARITHMIC:
        if (scale.left_value, scale.right_value) == TRIESTE_STANDARD_LOG_GRID:
            flags.append("logarithmic grid matches the trieste#3 standard split "
                         "four-cycle 0.2-2000 ohm-m form")
        # Strictly greater: trieste#3 puts the *primary* grid's top at exactly
        # 2000 ohm-m, so a top of 2000 is the standard form, not a backup.
        # max(): the top of the grid is left_value on a right-to-left scale, and
        # reading only right_value missed the mirrored declaration entirely.
        scale_top = max(scale.left_value, scale.right_value)
        if scale_top > TRIESTE_BACKUP_RANGE[0]:
            flags.append(
                f"declared scale top {scale_top:g} ohm-m reaches the range "
                "trieste#3 assigns to a backup trace (2000-40000); confirm this is a "
                "primary grid and not a backup"
            )

    if n_off:
        flags.append(f"{n_off} of {n} samples off the declared scale - not extrapolated")
    if n_at_edge:
        flags.append(f"{n_at_edge} of {n} samples at the scale edge - possible "
                     "pegged/clipped trace")
    if n_unreg:
        flags.append(f"{n_unreg} of {n} samples outside the depth register's span")
    if not getattr(depth_register, "datum", ""):
        flags.append("depth reference datum not stated by the depth register")

    method = (f"pixel-to-value through a declared {scale.kind} track scale "
              f"({scale.direction})")
    source = (f"{TRIESTE_SCALES}; {TRIESTE_TRACKS}; {ASQUITH_FIG31}")

    return DigitizedCurve(
        mnemonic=mnemonic or "UNNAMED",
        unit=scale.unit,
        samples=tuple(samples),
        method=method,
        source=source,
        inputs={"n_polyline_points": n, "trace_source": trace_source,
                "x_left_px": scale.x_left_px, "x_right_px": scale.x_right_px,
                "left_value": scale.left_value, "right_value": scale.right_value,
                "depth_register_source": getattr(depth_register, "source", "")},
        assumptions={"scale_kind": scale.kind, "direction": scale.direction,
                     "scale_source": scale.source, "unit": scale.unit,
                     "edge_tolerance_px": edge_tolerance_px,
                     "decades": scale.decades,
                     "depth_datum": getattr(depth_register, "datum", "")},
        flags=tuple(flags),
    )


def digitize_from_image(image_path: str, **_: Any) -> Refusal:
    """Grid detection and trace vectorization from raw pixels. Always refuses.

    The catalog asks for this. It exists as a named refusal rather than as an
    absence so that a caller who reads the catalog and looks for it finds a
    stated reason instead of nothing.
    """
    return Refusal(
        reason=(
            "grid detection and trace vectorization from raw pixels are not "
            "implemented and cannot be in this layer: the tools are standard-library "
            "only (no image-processing library is available), and no LLM call may "
            "appear in a tool implementation. Supply an already-traced polyline "
            "with its provenance and call raster_curve_digitize"
        ),
        needed=(
            "a traced curve polyline in pixel coordinates, with a trace_source",
            "the track scale from the log heading (raster_header_ocr, #6)",
            "a pixel-to-depth mapping (raster_depth_register, #8)",
        ),
        source=VERIFICATION_ADDENDUM,
    )

# ---------------------------------------------------------------------------
# 06_raster_header_ocr
# `raster_header_ocr` (#6, group A) — read the RRC A-P header items off a
# scanned log, from the TEXT of that scan.
#
# The non-obvious decision: this tool does not perform character recognition.
# `well-log-agent.md:184` files "reading unstructured evidence" under what needs
# the model; recognising a smudge as an 8 rather than a 3 is judgement under
# ambiguity and would yield a number with no method and no anchor. So the OCR
# pass is an argument, and what happens here is the deterministic half — locate
# the items, parse values and units, tag the evidence class, cross-check, flag
# the implausible, name the absent. See specs/06-raster_header_ocr.md.
#
# Two header LAYOUTS are handled and normalise to one cell tuple:
#   table       `|  Permanent Datum  |  |  Ground Level  |`   (rrc#16's shape)
#   plain line  `Permanent Datum: Ground Level      Elev.: 2873`
# The plain form is what an OCR pass over a scanned blueline normally emits; the
# table form is what a table-aware conversion emits and is the only shape we
# have a real specimen of. Supporting only the specimen would have meant a tool
# that works on the test case and fails on the input.
#
# Disagreement is reported, never resolved: a header whose Permanent Datum is GL
# and whose Log Measured From is KB is 15 ft of structural error waiting to
# happen, and resolving it is `datum_resolve` (#15).
# ---------------------------------------------------------------------------

# `header_extract` (#4) owns the A-P contract. If this import fails the tool is
# unusable by design: two copies of a shared contract are two contracts.

RRC_ITEMS_A_P = "09-gas-deliverability/rrc-section-f-completions-electric-logs#15"
RRC_REAL_HEADER = "09-gas-deliverability/rrc-section-f-completions-electric-logs#16"

# --------------------------------------------------------------------------
# Evidence classes. An OCR'd value and a digitally-declared one are not the
# same fact and a consumer must be able to tell them apart.
# --------------------------------------------------------------------------
EVIDENCE_DIGITAL = "digital"          # from a machine-readable header
EVIDENCE_OCR_CONFIRMED = "ocr-confirmed"  # OCR value agreeing with a digital one
EVIDENCE_OCR = "ocr"                  # read off the scan, once
EVIDENCE_DERIVED = "derived"          # computed here from OCR'd values

# --------------------------------------------------------------------------
# Plausibility bands. HOUSE RULES, NOT CORPUS - declared here in the open the
# same way `tool-catalog.md`'s "Thresholds the corpus does not supply" declares
# its five. Every one is PROVISIONAL and caller-overridable, and none of them
# rejects or corrects a value: they only set a flag.
# --------------------------------------------------------------------------
PLAUSIBLE: dict[str, tuple[float, float]] = {
    "C": (0.0, 40_000.0),        # depths logged, ft
    "D": (3.0, 36.0),            # bit size, in
    "E": (2.0, 30.0),            # casing OD, in
    "E.weight": (5.0, 200.0),    # casing weight, lb/ft
    "H": (6.0, 25.0),            # mud density, lb/gal
    "K": (-300.0, 15_000.0),     # elevation above sea level, ft
    "L": (0.0, 200.0),           # Kelly bushing height, ft
    "N": (32.0, 500.0),          # max recorded temperature, degF
}
PLAUSIBLE_UNIT = {
    "C": "ft", "D": "in", "E": "in", "E.weight": "lb/ft",
    "H": "lb/gal", "K": "ft", "L": "ft", "N": "degF",
}

# Depth-row labels whose meaning is known. A row printing any other "Depth ..."
# label is still collected under item C, under its printed label, with an
# `unrecognized-depth-label` flag - guessing that "Depth Onset" is an OCR
# corruption of "Depth Driller" would be exactly the guess this tool forbids.
_KNOWN_DEPTH_KEYS = ("top log interval", "bottom logged interval",
                     "depth logger", "depth driller")

_DATUM_ROLES = ("permanent datum", "log measured from", "drilling measured from",
                "measured from")
_DATUM_REFERENCES = ("ground level", "kelly bushing", "derrick floor",
                     "rotary table", "casing head", "mean sea level",
                     "casing flange", "ground elevation")
_REFERENCE_ALIASES = {
    "gl": "ground level", "kb": "kelly bushing", "df": "derrick floor",
    "rt": "rotary table", "msl": "mean sea level",
}


# --------------------------------------------------------------------------
# Result types. Containers only - every physical number inside is a Quantity or
# a Range carrying its method and source.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class HeaderField:
    item: str                       # RRC item letter, "A".."P"
    label: str                      # the contract label, from RRC_HEADER_ITEMS
    evidence: str                   # one of the four classes above
    value: Any                      # Quantity | Range | str | dict | list
    raw: str = ""                   # verbatim OCR substring it came from
    confidence: float | None = None  # min recogniser confidence, if reported
    flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class MissingItem:
    item: str
    label: str
    reason: str                     # "label-not-found" | "value-blank"


@dataclass(frozen=True)
class Conflict:
    kind: str
    items: tuple[str, ...]
    detail: str
    values: dict[str, Any] = field(default_factory=dict)
    derived: Quantity | None = None


@dataclass(frozen=True)
class RasterHeader:
    items: dict[str, HeaderField] = field(default_factory=dict)
    missing_mandatory: tuple[MissingItem, ...] = ()
    conflicts: tuple[Conflict, ...] = ()
    derived: dict[str, Quantity] = field(default_factory=dict)
    flags: tuple[str, ...] = ()
    source: str = RRC_ITEMS_A_P

    def conflict(self, kind: str) -> Conflict | None:
        for c in self.conflicts:
            if c.kind == kind:
                return c
        return None

    def missing(self, item: str) -> MissingItem | None:
        for m in self.missing_mandatory:
            if m.item == item:
                return m
        return None


# --------------------------------------------------------------------------
# RRC_HEADER_ITEMS accessor. `tools/header.py` is being written concurrently and
# its exact shape is not fixed, so read it tolerantly: a plain label string, a
# mapping with label/name/description, or an object with those attributes. At
# merge this should collapse to direct field access.
# --------------------------------------------------------------------------
def _label(item: str) -> str:
    spec = RRC_HEADER_ITEMS.get(item)
    if spec is None:
        raise ValueError(f"RRC_HEADER_ITEMS has no item {item!r}; the A-P "
                         "contract is owned by header_extract (#4)")
    if isinstance(spec, str):
        return spec
    # `rrc_text` first: specs/04-header_extract.md:75 says each entry carries the
    # regulation's own wording under that key.
    if isinstance(spec, Mapping):
        for key in ("rrc_text", "label", "name", "description", "title", "field"):
            if spec.get(key):
                return str(spec[key])
        return str(spec)
    for attr in ("rrc_text", "label", "name", "description", "title", "field"):
        got = getattr(spec, attr, None)
        if got:
            return str(got)
    return str(spec)


def _letters() -> tuple[str, ...]:
    return tuple(sorted(k for k in RRC_HEADER_ITEMS if isinstance(k, str) and len(k) == 1))


# --------------------------------------------------------------------------
# Line normalisation
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class _Line:
    index: int
    text: str
    cells: tuple[str, ...]
    confidence: float | None = None
    bbox: tuple[float, float, float, float] | None = None
    page: int | None = None


_SEP_ROW = re.compile(r"^[\s|:-]+$")


def _split_cells(text: str) -> tuple[str, ...]:
    """Two header layouts, one cell tuple.

    **Table form.** A pipe-delimited row, which is what a flattened header table
    converts to and what the only real header in the corpus (`rrc#16`) is.

    **Plain-line form.** `Label: value`, or `Label` and value separated by a run
    of two or more spaces. This is what an OCR pass over a scanned blueline
    normally emits, since the ruled boxes of the header become whitespace. One
    line may carry several such pairs (`Permanent Datum: Ground Level    Elev.:
    2873`), so split on the wide gaps first and on the colon within each chunk;
    that yields `("Permanent Datum", "Ground Level", "Elev.", "2873")` and the
    rest of the machinery reads it exactly as it reads a table row.

    The plain split is only accepted when the leading chunk actually reads as a
    header label. Prose that happens to contain a colon stays one cell, because
    treating "Note: the tool was rerun" as a labelled field would manufacture
    header items out of comments.
    """
    if "|" in text:
        return tuple(c.strip() for c in text.strip().strip("|").split("|"))
    stripped = text.strip()
    if not stripped:
        return (stripped,)
    cells: list[str] = []
    for chunk in re.split(r"\s{2,}", stripped):
        chunk = chunk.strip()
        if not chunk:
            continue
        label, sep, value = chunk.partition(":")
        if sep and label.strip():
            cells.extend([label.strip(), value.strip()])
        else:
            cells.append(chunk)
    if len(cells) < 2:
        return (stripped,)
    if not (_matches_item(cells[0]) or _datum_roles(cells[0])):
        return (stripped,)
    return tuple(cells)


def _normalise(ocr_text: str | None,
               ocr_lines: Sequence[Mapping[str, Any]] | None) -> list[_Line]:
    out: list[_Line] = []
    if ocr_lines is not None:
        for i, raw in enumerate(ocr_lines):
            if not isinstance(raw, Mapping) or "text" not in raw:
                # programmer error, not a refusal
                raise ValueError(f"ocr_lines[{i}] has no 'text' key: {raw!r}")
            text = str(raw["text"])
            conf = raw.get("confidence")
            out.append(_Line(index=i, text=text, cells=_split_cells(text),
                             confidence=None if conf is None else float(conf),
                             bbox=tuple(raw["bbox"]) if raw.get("bbox") else None,
                             page=raw.get("page")))
    else:
        for i, text in enumerate((ocr_text or "").splitlines()):
            out.append(_Line(index=i, text=text, cells=_split_cells(text)))
    return [ln for ln in out if ln.text.strip() and not _SEP_ROW.match(ln.text)]


# --------------------------------------------------------------------------
# Value parsing. Feet marks, inch marks, mixed fractions.
# --------------------------------------------------------------------------
_FEET = re.compile(r"(\d+(?:\.\d+)?)\s*(?:'|’|ft\b|feet\b)", re.I)
_INCH = re.compile(r"(\d+(?:\.\d+)?)(?:\s+(\d+)\s*/\s*(\d+))?\s*(?:\"|”|in\b|inch(?:es)?\b)", re.I)
_BARE = re.compile(r"^(\d+(?:\.\d+)?)$")
_TEMP = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:deg\s*)?(?:°\s*)?F\b", re.I)


def _q(value: float, unit: str, method: str, *, inputs: dict[str, Any] | None = None,
       assumptions: dict[str, Any] | None = None,
       flags: tuple[str, ...] = (), source: str = RRC_ITEMS_A_P) -> Quantity:
    return Quantity(value=value, unit=unit, method=method, source=source,
                    inputs=inputs or {}, assumptions=assumptions or {}, flags=flags)


def _read_feet(text: str) -> float | None:
    m = _FEET.search(text)
    return float(m.group(1)) if m else None


def _read_inches(text: str) -> float | None:
    """`14 3/4"` -> 14.75.  Mixed fractions are the normal form on a header."""
    m = _INCH.search(text)
    if not m:
        return None
    whole = float(m.group(1))
    if m.group(2) and m.group(3) and float(m.group(3)) != 0:
        whole += float(m.group(2)) / float(m.group(3))
    return whole


def _read_bare(text: str) -> float | None:
    m = _BARE.match(text.strip())
    return float(m.group(1)) if m else None


# The plain-line layout normally drops the unit mark the table layout carries:
# `Bit Size: 7 7/8` and `Depth-Driller: 5120` where a ruled header would print
# `7 7/8"` and `5120'`. These read the number and the caller records that the
# unit was NOT stated - no unit is assumed from context.
_UNMARKED = re.compile(r"^\s*(-?\d+(?:\.\d+)?)(?:\s+(\d+)\s*/\s*(\d+))?\s*$")
_LEADING = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([A-Za-z/°%.]*)")


def _read_unmarked(text: str) -> float | None:
    """`7 7/8` -> 7.875, `5120` -> 5120.0. No unit mark, so no unit."""
    m = _UNMARKED.match(text)
    if not m:
        return None
    whole = float(m.group(1))
    if m.group(2) and m.group(3) and float(m.group(3)) != 0:
        whole += float(m.group(2)) / float(m.group(3))
    return whole


def _read_leading(text: str) -> tuple[float, str] | None:
    """`9.6 ppg` -> (9.6, "ppg"). The unit text is kept verbatim, never mapped."""
    m = _LEADING.match(text)
    if not m:
        return None
    return float(m.group(1)), m.group(2).strip(" .")


_UNSTATED = "unit-unstated on the scan; no unit assumed"

# `KB Elevation`, `Elev. G.L.`, `Ground Level Elevation` -> the short key the
# table layout files elevations under, so both layouts land in one place.
_HEAD_ELEV = (
    (re.compile(r"\b(?:k\.?\s*b\.?|kelly\s+bushing)\b", re.I), "KB"),
    (re.compile(r"\b(?:g\.?\s*l\.?|ground\s+level|ground)\b", re.I), "GL"),
    (re.compile(r"\b(?:d\.?\s*f\.?|derrick\s+floor)\b", re.I), "DF"),
    (re.compile(r"\b(?:r\.?\s*t\.?|rotary\s+table)\b", re.I), "RT"),
)


def _head_elev_key(head: str) -> str | None:
    for pat, key in _HEAD_ELEV:
        if pat.search(head):
            return key
    return None


def _min_conf(lines: Iterable[_Line]) -> float | None:
    vals = [ln.confidence for ln in lines if ln.confidence is not None]
    return min(vals) if vals else None


def _norm_reference(text: str) -> str:
    t = re.sub(r"[.\s]+", " ", text.strip().lower()).strip()
    return _REFERENCE_ALIASES.get(t.replace(" ", ""), t)


# --------------------------------------------------------------------------
# The label lexicon - owned here, not by RRC_HEADER_ITEMS. These are the strings
# an item is printed as on a service-company header, keyed by RRC item letter.
# --------------------------------------------------------------------------
_LEXICON: dict[str, tuple[str, ...]] = {
    "A": (r"company\b", r"^well\b", r"^field\b", r"^county\b", r"^location\b", r"api\s*#"),
    "B": (r"other\s+services", r"type\s+of\s+log", r"^log\s+type", r"^services\b",
          r"log\s+measurements"),
    "C": (r"^depth\b", r"^bottom\s+log", r"^top\s+log", r"^total\s+depth", r"^t\.?d\.?\b",
          r"^logged\s+interval"),
    "D": (r"bit\s*size", r"open\s+hole\s+size", r"^hole\s+size", r"^borehole\s+record", r"^bit\b"),
    "E": (r"^casing\s+record", r"casing\s*size", r"^surface\s+string", r"^prot",
          r"^protection\s+string", r"^liner\b", r"^intermediate\s+string"),
    "F": (r"^date\b", r"^time\b", r"logging\s+started", r"logging\s+finished",
          r"time\s+logger", r"time\s+well", r"time\s+circulation"),
    "G": (r"type\s+fluid", r"type\s+of\s+mud", r"^mud\s+type", r"fluid\s+in\s+hole",
          r"fluid\s+type", r"^type\s+of\s+fluid"),
    "H": (r"mud\s+density", r"^density\b", r"mud\s+weight", r"^wt\.?\s*/?\s*gal"),
    # not anchored: a header commonly prints one combined box, "Density /
    # Viscosity", which must register as BOTH item H and item I so that a blank
    # box is reported as two blank mandatory items rather than one.
    "I": (r"\bviscosity\b", r"\bvisc\.", r"\bvis\b"),
    "J": (r"^rm\b", r"^rmf\b", r"^rmc\b", r"resistivity\s+of\s+mud",
          r"mud\s+resistivity", r"source\s+of\s+sample"),
    # both orders: the table layout prints `Elevation K.B. 2888'`, the plain
    # layout prints `KB Elevation: 2888`.
    "K": (r"^elevation", r"elev\.?\s*(?:k\.?\s*b\.?|g\.?\s*l\.?|d\.?\s*f\.?|r\.?\s*t\.?)",
          r"(?:k\.?\s*b\.?|g\.?\s*l\.?|d\.?\s*f\.?|r\.?\s*t\.?)\s*elev",
          r"(?:ground\s+level|kelly\s+bushing|derrick\s+floor|rotary\s+table)\s*elev",
          r"ground\s+elevation", r"above\s+sea\s+level"),
    "L": (r"kelly\s+bushing\s+height", r"^k\.?\s*b\.?\s+height", r"apd\b"),
    "M": (r"permanent\s+datum", r"log\s+measured\s+from", r"drilling\s+measured\s+from",
          r"measured\s+from", r"depth\s+reference"),
    "N": (r"max\.?\s*(?:imum)?\s*record", r"max\.?\s*temp", r"maximum\s+temperature"),
    "O": (r"service\s+company", r"logging\s+company", r"^company\s+name"),
    "P": (r"recorded\s+by", r"witnessed\s+by", r"^engineer\b", r"logged\s+by",
          r"company\s+employee"),
}
_LEXICON_RE = {k: tuple(re.compile(p, re.I) for p in v) for k, v in _LEXICON.items()}

# Item O is branding, not a labelled field, on most vintage headers.
_SERVICE_CO = re.compile(
    r"((?:[A-Z][A-Za-z&.\-]*\s+)*[A-Z][A-Za-z&.\-]*)\s+"
    r"(Wireline|Well\s+Services|Wireline\s+Services|Logging(?:\s+Services)?)\b")
_KB_INLINE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:'|’)?\s*(?:K\.?B\.?|kelly\s+bushing)\b", re.I)
_APD = re.compile(r"(\d+(?:\.\d+)?)\s*(?:'|’)?\s*(?:APD\b|above\s+permanent\s+datum)", re.I)
_ELEV_SUB = re.compile(r"\b(K\.?\s?B\.?|D\.?\s?F\.?|G\.?\s?L\.?|R\.?\s?T\.?)\s*"
                       r"(\d+(?:\.\d+)?)\s*(?:'|’|ft\b)", re.I)
_API_NO = re.compile(r"API\s*#?\s*:?\s*(\d{2}\s*-\s*\d{3}\s*-\s*\d{4,5})", re.I)

# A few items are printed inline inside a cell rather than as a row label, so
# the row scan (which reads cell 0 as the label) never sees them. Kept to a
# short explicit list rather than scanning every cell for every label, because a
# general inline scan matches prose.
_INLINE = {
    "B": (re.compile(r"other\s+services\s*:?\s*([A-Za-z0-9][A-Za-z0-9 ,/&.\-]*)", re.I),
          re.compile(r"type\s+of\s+log\s*:?\s*([A-Za-z0-9][A-Za-z0-9 ,/&.\-]*)", re.I)),
}


def _matches_item(cell: str) -> list[str]:
    """Which RRC items a cell's text reads as a label for. May be several."""
    hits: list[str] = []
    for letter, pats in _LEXICON_RE.items():
        if any(p.search(cell) for p in pats):
            hits.append(letter)
    return hits


# --------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------
def raster_header_ocr(ocr_text: str | None = None, *,
                      ocr_lines: Sequence[Mapping[str, Any]] | None = None,
                      las_header: Mapping[str, Any] | None = None,
                      image_path: str | None = None,
                      plausibility_overrides: Mapping[str, tuple[float, float]] | None = None,
                      min_confidence: float | None = None) -> RasterHeader | Refusal:
    """Locate the RRC A-P header items in the recognised text of a scanned log.

    Takes the OUTPUT of an OCR pass, never an image: recognition is judgement
    under ambiguity and belongs to the model half of the system
    (`well-log-agent.md:184`), not to a deterministic tool. See the module
    docstring and `specs/06-raster_header_ocr.md`.
    """
    needed_ocr = (
        "ocr_text: the recognised text of the header block, newline-separated; or",
        "ocr_lines: [{text, confidence?, bbox?, page?}, ...] from an OCR pass "
        "(engine, vision model or human transcription)",
    )
    if ocr_text is None and ocr_lines is None:
        if image_path is not None:
            return Refusal(
                reason=(f"raster_header_ocr does not perform character recognition, so "
                        f"{image_path!r} cannot be read here. Run an OCR pass over the "
                        "header block and pass its text."),
                needed=needed_ocr, source=RRC_ITEMS_A_P)
        return Refusal(
            reason="no OCR output supplied; this tool reads the text of a scanned "
                   "header, it does not perform the recognition itself",
            needed=needed_ocr, source=RRC_ITEMS_A_P)

    lines = _normalise(ocr_text, ocr_lines)
    if not lines:
        return Refusal(reason="OCR output is empty", needed=needed_ocr,
                       source=RRC_ITEMS_A_P)

    bands = dict(PLAUSIBLE)
    if plausibility_overrides:
        bands.update({k: (float(v[0]), float(v[1])) for k, v in plausibility_overrides.items()})

    fields: dict[str, HeaderField] = {}
    blank: dict[str, str] = {}          # item -> raw label text, value box empty
    flags: list[str] = []
    derived: dict[str, Quantity] = {}
    conflicts: list[Conflict] = []

    _scan_rows(lines, fields, blank, flags)
    _scan_freetext(lines, fields, flags)

    if not fields and not blank:
        return Refusal(
            reason="no RRC log-header item label was found in the OCR output; this "
                   "text does not read as a log header block",
            needed=("OCR output covering the header block of the log, not the curve "
                    "tracks or the body of the page",),
            source=RRC_ITEMS_A_P)

    _cross_check(fields, derived, conflicts, flags)
    _plausibility(fields, bands, flags)
    _apply_digital(fields, blank, las_header, flags)
    if min_confidence is not None:
        _confidence_flags(fields, float(min_confidence))

    missing = _missing(fields, blank)
    return RasterHeader(items=fields, missing_mandatory=missing,
                        conflicts=tuple(conflicts), derived=derived,
                        flags=tuple(flags), source=RRC_ITEMS_A_P)


def require_item(header: RasterHeader | Refusal, item: str) -> Any | Refusal:
    """The downstream gate: a value, or a Refusal naming the absent item.

    A consumer that cannot proceed without item M (the depth reference datum)
    must get a Refusal it can render, not a KeyError and not a None.
    """
    if isinstance(header, Refusal):
        return header
    got = header.items.get(item)
    if got is not None:
        return got.value
    reason = "not present in the scanned header"
    miss = header.missing(item)
    if miss is not None:
        reason = ("label found on the scan but its value box is blank"
                  if miss.reason == "value-blank" else
                  "no label for this item was found on the scan")
    return Refusal(
        reason=f"RRC log-header item {item} ({_label(item)}): {reason}",
        needed=(f"item {item} from another source - the LAS ~W section, the RRC "
                f"W-2/G-1 completion filing, or a better scan",),
        source=RRC_ITEMS_A_P)


# --------------------------------------------------------------------------
# Row scanning
# --------------------------------------------------------------------------
def _set(fields: dict[str, HeaderField], item: str, value: Any, raw: str,
         used: Iterable[_Line], flags: tuple[str, ...] = ()) -> None:
    fields[item] = HeaderField(item=item, label=_label(item), evidence=EVIDENCE_OCR,
                               value=value, raw=raw, confidence=_min_conf(used),
                               flags=flags)


def _merge_sub(fields: dict[str, HeaderField], item: str, key: str, value: Any,
               raw: str, used: Iterable[_Line], flags: tuple[str, ...] = ()) -> None:
    cur = fields.get(item)
    sub = dict(cur.value) if cur is not None and isinstance(cur.value, dict) else {}
    sub[key] = value
    old_raw = f"{cur.raw}; " if cur is not None and cur.raw else ""
    old_flags = cur.flags if cur is not None else ()
    conf = _min_conf(used)
    if cur is not None and cur.confidence is not None:
        conf = cur.confidence if conf is None else min(conf, cur.confidence)
    fields[item] = HeaderField(item=item, label=_label(item), evidence=EVIDENCE_OCR,
                               value=sub, raw=old_raw + raw, confidence=conf,
                               flags=tuple(dict.fromkeys(old_flags + flags)))


def _append(fields: dict[str, HeaderField], item: str, entry: Any, raw: str,
            used: Iterable[_Line]) -> None:
    cur = fields.get(item)
    seq = list(cur.value) if cur is not None and isinstance(cur.value, list) else []
    seq.append(entry)
    old_raw = f"{cur.raw}; " if cur is not None and cur.raw else ""
    conf = _min_conf(used)
    if cur is not None and cur.confidence is not None:
        conf = cur.confidence if conf is None else min(conf, cur.confidence)
    fields[item] = HeaderField(item=item, label=_label(item), evidence=EVIDENCE_OCR,
                               value=seq, raw=old_raw + raw, confidence=conf,
                               flags=cur.flags if cur is not None else ())


def _first_value_cell(cells: Sequence[str]) -> tuple[int, str]:
    for i, c in enumerate(cells[1:], start=1):
        if c:
            return i, c
    return -1, ""


def _scan_rows(lines: list[_Line], fields: dict[str, HeaderField],
               blank: dict[str, str], flags: list[str]) -> None:
    mode: str | None = None   # None | "borehole" | "casing"
    for ln in lines:
        cells = ln.cells
        head = cells[0].strip()
        low = head.lower()

        # --- table-section modes ------------------------------------------
        if re.match(r"^borehole\s+record", low):
            mode = "borehole"
            continue
        if re.match(r"^casing\s+record", low):
            mode = "casing"
            continue
        if mode == "borehole":
            if _casing_string_name(low) or re.match(r"^casing\b", low):
                mode = "casing"
            else:
                if _borehole_row(ln, fields):
                    continue
                if head and _matches_item(head) and not re.match(r"^(run\s+number|one|two|three|four|five)\b", low):
                    mode = None
                else:
                    continue
        if mode == "casing":
            if _casing_row(ln, fields):
                continue
            if head and _matches_item(head) and not _casing_string_name(low):
                mode = None
            else:
                continue

        if not head:
            continue

        # --- the datum row (item M) ---------------------------------------
        roles = _datum_roles(head)
        if roles:
            refs = _datum_row(ln, roles, fields, flags)
            # the same physical row usually carries the elevations and the APD.
            # A keyed block (`K.B. 2888' G.L. 2873'`, the table layout) wins; the
            # loose `Elev.: 2873` form is only consulted when there is no keyed
            # block to read, which is the plain-line layout's case.
            if not _elevation_row(ln, fields):
                _attach_datum_elevations(ln, refs, fields)
            _apd_row(ln, fields)
            continue

        hits = _matches_item(head)
        if not hits:
            continue
        vi, val = _first_value_cell(cells)
        if not val:
            for letter in hits:
                blank.setdefault(letter, head)
            continue
        used = (ln,)

        # A label cell reading as several items (e.g. "Density / Viscosity")
        # registers for each of them.
        for letter in hits:
            _row_value(letter, head, val, cells, vi, ln, fields, used)

        # elevations and APD can appear in any row
        _elevation_row(ln, fields)
        _apd_row(ln, fields)


def _row_value(letter: str, head: str, val: str, cells: Sequence[str], vi: int,
               ln: _Line, fields: dict[str, HeaderField], used: tuple[_Line, ...]) -> None:
    low = head.lower().rstrip(":").strip()
    if letter == "C":
        ft, stated = _read_feet(val), True
        if ft is None:
            ft, stated = _read_unmarked(val), False
        if ft is None:
            return
        key = re.sub(r"[^a-z0-9 ]", " ", low)
        key = re.sub(r"\s+", " ", key).strip()
        fl = () if key in _KNOWN_DEPTH_KEYS else (f"unrecognized-depth-label: {head}",)
        fl += () if stated else (_UNSTATED,)
        _merge_sub(fields, "C", key,
                   _q(ft, "ft" if stated else "",
                      f"depth read from scanned header row {head!r}",
                      inputs={"raw": val},
                      assumptions={"unit_stated_on_scan": stated}), val, used, fl)
        return
    if letter == "D":
        inch, stated = _read_inches(val), True
        if inch is None:
            inch, stated = _read_unmarked(val), False
        if inch is None:
            return
        _append(fields, "D", {"label": head, "size": _q(
            inch, "in" if stated else "",
            f"bit/hole size read from scanned header row {head!r}",
            inputs={"raw": val}, assumptions={"unit_stated_on_scan": stated},
            flags=() if stated else (_UNSTATED,))}, val, used)
        return
    if letter in ("H", "I", "N"):
        num, unit_text = None, ""
        if letter == "N":
            num = _read_temp(val)
            unit_text = "degF" if num is not None else ""
        if num is None:
            got = _read_leading(val)
            if got is None:
                return
            num, unit_text = got
        stated = bool(unit_text)
        # The stated unit is kept VERBATIM. A header reading "72 pcf" is not a
        # mud density in lb/gal, and mapping it to the house unit because the
        # item's house unit happens to be lb/gal would be a silent conversion.
        _set(fields, letter, _q(num, unit_text,
                                f"read from scanned header row {head!r}",
                                inputs={"raw": val},
                                assumptions={"unit_stated_on_scan": stated}),
             val, used, () if stated else (_UNSTATED,))
        return
    if letter == "A":
        _identity_row(ln, fields, used)
        return
    if letter in ("F", "P", "J"):
        key = re.sub(r"\s+", " ", low)
        _merge_sub(fields, letter, key, val, val, used)
        return
    if letter == "K":
        if not _elevation_row(ln, fields):
            ft, stated = _read_feet(val), True
            if ft is None:
                ft, stated = _read_unmarked(val), False
            if ft is not None:
                # `KB Elevation: 2888` in the plain layout: the reference is in
                # the label, so file it under the same short key the table
                # layout uses rather than under the raw label text.
                key = _head_elev_key(low) or re.sub(r"\s+", " ", low)
                _merge_sub(fields, "K", key,
                           _q(ft, "ft" if stated else "",
                              f"elevation read from scanned header row {head!r}",
                              inputs={"raw": val},
                              assumptions={"unit_stated_on_scan": stated}),
                           val, used, () if stated else (_UNSTATED,))
        return
    if letter == "L":
        num, stated = _read_feet(val), True
        if num is None:
            num, stated = _read_unmarked(val), False
        if num is not None:
            _set(fields, "L", _q(num, "ft" if stated else "",
                                 f"Kelly bushing height read from scanned header row {head!r}",
                                 inputs={"raw": val},
                                 assumptions={"unit_stated_on_scan": stated}),
                 val, used, () if stated else (_UNSTATED,))
        return
    if letter in ("B", "G", "O", "E", "M"):
        if letter == "E":
            return          # item E comes from the casing-record table only
        _set(fields, letter, val, val, used)
        return


def _read_temp(text: str) -> float | None:
    m = _TEMP.search(text)
    return float(m.group(1)) if m else None


# --- item A ---------------------------------------------------------------
_IDENT_KEYS = re.compile(r"\b(Company|Well|Field|County|State|Location)\b")


def _identity_row(ln: _Line, fields: dict[str, HeaderField],
                  used: tuple[_Line, ...]) -> None:
    text = " ".join(c for c in ln.cells if c)
    api = _API_NO.search(text)
    if api:
        _merge_sub(fields, "A", "api", re.sub(r"\s+", "", api.group(1)),
                   api.group(0), used)
    marks = list(_IDENT_KEYS.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        val = text[m.end():end].strip(" :|")
        if val and not val.lower().startswith("api"):
            _merge_sub(fields, "A", m.group(1).lower(), val, val, used)


# --- item M, the datum row -------------------------------------------------
_ROLE_RE = re.compile("|".join(sorted((re.escape(r) for r in _DATUM_ROLES),
                                      key=len, reverse=True)), re.I)
_REF_RE = re.compile("|".join(sorted((re.escape(r) for r in _DATUM_REFERENCES),
                                     key=len, reverse=True)), re.I)


def _datum_roles(cell: str) -> list[str]:
    return [m.group(0).lower() for m in _ROLE_RE.finditer(cell)]


def _datum_row(ln: _Line, roles: list[str], fields: dict[str, HeaderField],
               flags: list[str]) -> list[str]:
    """Pair N stacked role labels with N stacked reference values, positionally.

    Serves both layouts. A flattened header table collapses a three-row block
    into one cell of labels and one cell of values, which is what `#16` does and
    which gives N=3; the plain-line layout gives one role and one reference per
    line, N=1. Pair by index when the counts match and refuse to pair when they
    do not, rather than assuming.

    Returns the references it paired, so the caller can attribute an elevation
    printed on the same line to the right one.
    """
    refs: list[str] = []
    for cell in ln.cells[1:]:
        if not cell or re.search(r"\d", cell):
            continue                    # value cell for M carries no digits
        found = [m.group(0).lower() for m in _REF_RE.finditer(cell)]
        if found:
            refs = found
            raw = cell
            break
    else:
        raw = ""
    if not refs:
        _merge_sub(fields, "M", "unpaired-labels", "; ".join(roles), ln.text, (ln,),
                   ("pairing-ambiguous: labels found with no reference values",))
        return []
    if len(refs) != len(roles):
        _merge_sub(fields, "M", "unpaired-labels",
                   f"labels {roles} vs values {refs}", ln.text, (ln,),
                   (f"pairing-ambiguous: {len(roles)} labels against {len(refs)} values",))
        return []
    for role, ref in zip(roles, refs):
        _merge_sub(fields, "M", role, ref.title(), raw, (ln,))
    return refs


# `Elev.: 2873` / `Elev 2873` / `Elevation: 2873` - the loose form the plain
# layout prints after a datum name. Only ever applied to a line that already
# named a datum reference, because on its own it says nothing about WHICH datum.
_ELEV_LOOSE = re.compile(r"\bElev(?:ation)?\b\.?\s*:?\s*(-?\d+(?:\.\d+)?)\s*(?:'|’|ft\b)?", re.I)


def _attach_datum_elevations(ln: _Line, refs: list[str],
                             fields: dict[str, HeaderField]) -> None:
    """`Permanent Datum: Ground Level   Elev.: 2873` -> item K, key GL.

    The plain layout prints the elevation next to the datum it belongs to rather
    than in a keyed `K.B. 2888' G.L. 2873'` block, so the reference named on the
    line is what keys it. Attribute only when the pairing is unambiguous - one
    elevation to one reference, or N to N in order. Anything else is flagged and
    left unattributed, because guessing which datum a loose number belongs to is
    exactly the error item M exists to prevent.
    """
    if not refs:
        return
    elevs = [float(m.group(1)) for m in _ELEV_LOOSE.finditer(ln.text)]
    if not elevs:
        return
    if len(elevs) == 1 and len(set(refs)) == 1:
        pairs = [(refs[0], elevs[0])]
    elif len(elevs) == len(refs):
        pairs = list(zip(refs, elevs))
    else:
        _merge_sub(fields, "M", "unattributed-elevations", elevs, ln.text, (ln,),
                   (f"elevation-attribution-ambiguous: {len(elevs)} elevations "
                    f"against {len(refs)} datum references on one line",))
        return
    for ref, elev in pairs:
        key = _ELEV_KEY.get(ref, ref.upper())
        _merge_sub(fields, "K", key,
                   _q(elev, "ft",
                      f"elevation above sea level read from the scanned header, "
                      f"attributed to {ref} by the datum label on the same line",
                      inputs={"raw": ln.text.strip()},
                      assumptions={"datum_reference": ref}), ln.text.strip(), (ln,))


def _elevation_row(ln: _Line, fields: dict[str, HeaderField]) -> bool:
    """`Elevation K.B. 2888' D.F. 2888' G.L. 2873'` -> sub-keyed item K."""
    hit = False
    for cell in ln.cells:
        for m in _ELEV_SUB.finditer(cell):
            key = re.sub(r"[.\s]", "", m.group(1)).upper()
            _merge_sub(fields, "K", key,
                       _q(float(m.group(2)), "ft",
                          f"elevation above sea level read from scanned header ({key})",
                          inputs={"raw": m.group(0)}), m.group(0), (ln,))
            hit = True
    return hit


def _apd_row(ln: _Line, fields: dict[str, HeaderField]) -> bool:
    for cell in ln.cells:
        m = _APD.search(cell)
        if m and "L" not in fields:
            _set(fields, "L", _q(float(m.group(1)), "ft",
                                 "height above permanent datum, read from scanned "
                                 "header ('APD')", inputs={"raw": m.group(0)}),
                 m.group(0), (ln,))
            return True
    return False


# --- items D and E, the record tables --------------------------------------
def _casing_string_name(low: str) -> bool:
    return bool(re.match(r"^(surface|prot|protection|intermediate|production|"
                         r"liner|short\s+joint|conductor)\b", low))


def _borehole_row(ln: _Line, fields: dict[str, HeaderField]) -> bool:
    inch = None
    for cell in ln.cells[1:]:
        inch = _read_inches(cell)
        if inch is not None:
            break
    if inch is None:
        return False
    depths = [_read_feet(c) for c in ln.cells]
    depths = [d for d in depths if d is not None]
    entry: dict[str, Any] = {
        "label": ln.cells[0] or "borehole record",
        "size": _q(inch, "in", "bit size read from the scanned borehole-record table",
                   inputs={"row": ln.text.strip()}),
    }
    if depths:
        entry["to"] = _q(depths[-1], "ft",
                         "hole-section bottom read from the scanned borehole-record table",
                         inputs={"row": ln.text.strip()})
    _append(fields, "D", entry, ln.text.strip(), (ln,))
    return True


def _casing_row(ln: _Line, fields: dict[str, HeaderField]) -> bool:
    cells = ln.cells
    od = None
    od_i = -1
    for i, cell in enumerate(cells[1:], start=1):
        od = _read_inches(cell)
        if od is not None:
            od_i = i
            break
    if od is None:
        return False
    weight = None
    for cell in cells[od_i + 1:]:
        weight = _read_bare(cell)
        if weight is not None:
            break
    depths = [d for d in (_read_feet(c) for c in cells) if d is not None]
    entry: dict[str, Any] = {
        "string": cells[0] or "casing",
        "od": _q(od, "in", "casing OD read from the scanned casing-record table",
                 inputs={"row": ln.text.strip()}),
    }
    if weight is not None:
        entry["weight"] = _q(weight, "lb/ft",
                             "casing weight read from the scanned casing-record table",
                             inputs={"row": ln.text.strip()},
                             assumptions={"unit_stated_on_scan": False})
    if depths:
        entry["bottom"] = _q(depths[-1], "ft",
                             "casing bottom read from the scanned casing-record table",
                             inputs={"row": ln.text.strip()})
    _append(fields, "E", entry, ln.text.strip(), (ln,))
    return True


# --- free text -------------------------------------------------------------
def _scan_freetext(lines: list[_Line], fields: dict[str, HeaderField],
                   flags: list[str]) -> None:
    for ln in lines:
        for item, pats in _INLINE.items():
            if item in fields:
                continue
            for cell in ln.cells:
                hit = next((p.search(cell) for p in pats if p.search(cell)), None)
                if hit and hit.group(1).strip():
                    _set(fields, item, hit.group(1).strip(), hit.group(0), (ln,),
                         ("read from an inline label, not from a labelled row",))
                    break
        if "O" not in fields:
            m = _SERVICE_CO.search(ln.text)
            if m:
                _set(fields, "O", f"{m.group(1)} {m.group(2)}".strip(), m.group(0), (ln,),
                     ("service company read from branding text, not from a labelled "
                      "field",))
        m = _KB_INLINE.search(ln.text)
        if m:
            got = float(m.group(1))
            cur = fields.get("L")
            if cur is None:
                _set(fields, "L", _q(got, "ft",
                                     "Kelly bushing height read from a free-text note "
                                     "on the scanned header", inputs={"raw": m.group(0)}),
                     m.group(0), (ln,))
            elif isinstance(cur.value, Quantity) and abs(cur.value.value - got) < 1e-9:
                fields["L"] = replace(cur, flags=tuple(dict.fromkeys(
                    cur.flags + (f"corroborated-in-text: {m.group(0).strip()!r}",))))


# --------------------------------------------------------------------------
# Cross-checks. Report, never resolve.
# --------------------------------------------------------------------------
def _cross_check(fields: dict[str, HeaderField], derived: dict[str, Quantity],
                 conflicts: list[Conflict], flags: list[str]) -> None:
    elevations = {}
    if "K" in fields and isinstance(fields["K"].value, dict):
        elevations = {k: v.value for k, v in fields["K"].value.items()
                      if isinstance(v, Quantity)}

    # 1. datum agreement (item M) --------------------------------------------
    perm = log_from = None
    if "M" in fields and isinstance(fields["M"].value, dict):
        m = {k: _norm_reference(str(v)) for k, v in fields["M"].value.items()}
        perm = m.get("permanent datum")
        log_from = m.get("log measured from") or m.get("measured from")
        drill_from = m.get("drilling measured from")
        distinct = {v for v in (perm, log_from, drill_from) if v}
        if len(distinct) > 1:
            offset = _datum_offset(perm, log_from, elevations)
            if offset is not None:
                derived["log_datum_offset"] = offset
            conflicts.append(Conflict(
                kind="datum-mismatch", items=("M",),
                detail=("the permanent datum and the datum the log is measured from "
                        "are different references; every depth on this log is offset "
                        "from the permanent datum. NOT resolved here - resolution is "
                        "datum_resolve (#15)"),
                values={"permanent datum": perm, "log measured from": log_from,
                        "drilling measured from": drill_from},
                derived=offset))

    # 2. KB height vs elevation arithmetic (item L vs K) ----------------------
    kb_from_elev = _kb_above_datum(perm, elevations)
    if kb_from_elev is not None:
        derived["kb_height_from_elevations"] = kb_from_elev
    cur = fields.get("L")
    if kb_from_elev is not None and cur is not None and isinstance(cur.value, Quantity):
        stated = cur.value.value
        if abs(stated - kb_from_elev.value) > 1e-9:
            conflicts.append(Conflict(
                kind="kb-height-mismatch", items=("L", "K"),
                detail=(f"the header states a Kelly bushing height of {stated:g} ft "
                        f"but its own elevations give {kb_from_elev.value:g} ft; "
                        "both are reported and neither is averaged away"),
                values={"stated_apd": stated,
                        "elevation_difference": kb_from_elev.value},
                derived=kb_from_elev))
            fields["L"] = replace(
                cur,
                value=Range(low=min(stated, kb_from_elev.value),
                            high=max(stated, kb_from_elev.value), unit="ft",
                            method=("Kelly bushing height: stated value and "
                                    "elevation-difference value disagree, reported as "
                                    "a band rather than a point"),
                            source=RRC_ITEMS_A_P,
                            members={"stated_apd": stated,
                                     "elevation_difference": kb_from_elev.value}),
                flags=tuple(dict.fromkeys(
                    cur.flags + ("kb-height-mismatch",) + kb_from_elev.flags)))
        elif kb_from_elev.flags:
            fields["L"] = replace(cur, flags=tuple(dict.fromkeys(
                cur.flags + kb_from_elev.flags)))
    elif kb_from_elev is not None and cur is None:
        fields["L"] = HeaderField("L", _label("L"), EVIDENCE_DERIVED, kb_from_elev,
                                  raw="", confidence=fields["K"].confidence,
                                  flags=kb_from_elev.flags)

    # 3. depth ordering (item C) ---------------------------------------------
    if "C" in fields and isinstance(fields["C"].value, dict):
        d = {k: v.value for k, v in fields["C"].value.items() if isinstance(v, Quantity)}
        seq = [d.get(k) for k in _KNOWN_DEPTH_KEYS]
        known = [(k, v) for k, v in zip(_KNOWN_DEPTH_KEYS, seq) if v is not None]
        bad = [f"{a[0]}={a[1]:g} > {b[0]}={b[1]:g}"
               for a, b in zip(known, known[1:]) if a[1] > b[1]]
        if bad:
            fields["C"] = replace(fields["C"], flags=tuple(dict.fromkeys(
                fields["C"].flags + (f"depth-order-implausible: {'; '.join(bad)}",))))

    # 4. casing fits the hole it was run in (E vs D) --------------------------
    _casing_vs_bit(fields)


def _datum_offset(perm: str | None, log_from: str | None,
                  elev: Mapping[str, float]) -> Quantity | None:
    a = _elev_for(log_from, elev)
    b = _elev_for(perm, elev)
    if a is None or b is None:
        return None
    return _q(a - b, "ft",
              f"log datum above permanent datum = {log_from} elevation {a:g} ft "
              f"minus {perm} elevation {b:g} ft",
              inputs={"log_datum_elevation_ft": a, "permanent_datum_elevation_ft": b},
              assumptions={"log_datum": log_from, "permanent_datum": perm})


def _kb_above_datum(perm: str | None, elev: Mapping[str, float]) -> Quantity | None:
    kb = elev.get("KB")
    base = _elev_for(perm, elev) if perm else elev.get("GL")
    if kb is None or base is None or perm == "kelly bushing":
        return None
    name = perm or "ground level"
    # RRC item M is what states which reference the permanent datum is. With no
    # item M on the scan there is no recorded permanent datum, and taking ground
    # level is a guess at a mandatory item - which `specs/06-raster_header_ocr.md`
    # forbids doing quietly ("name the mandatory items that are absent, and never
    # guess one"). So the height is still computed, because the elevation
    # difference is a real fact, and the guess is stated on the value itself
    # rather than left in `assumptions` for a reader who thinks to look.
    assumed = () if perm else (
        "permanent-datum-assumed: RRC item M is absent from this header, so this "
        "Kelly bushing height is reported above Ground Level; no permanent datum "
        "is recorded on the scan and that reference did not come from it",)
    return _q(kb - base, "ft",
              f"Kelly bushing height = KB elevation {kb:g} ft minus {name} "
              f"elevation {base:g} ft",
              inputs={"kb_elevation_ft": kb, "permanent_datum_elevation_ft": base},
              assumptions={"permanent_datum": name,
                           "permanent_datum_stated_on_scan": bool(perm)},
              flags=assumed)


_ELEV_KEY = {"kelly bushing": "KB", "ground level": "GL", "derrick floor": "DF",
             "rotary table": "RT", "ground elevation": "GL"}


def _elev_for(reference: str | None, elev: Mapping[str, float]) -> float | None:
    if not reference:
        return None
    return elev.get(_ELEV_KEY.get(reference, reference.upper()))


def _casing_vs_bit(fields: dict[str, HeaderField]) -> None:
    if "E" not in fields or "D" not in fields:
        return
    casings = fields["E"].value
    bits = fields["D"].value
    if not isinstance(casings, list) or not isinstance(bits, list):
        return
    sections = [(b["to"].value, b["size"].value) for b in bits
                if isinstance(b, dict) and "to" in b and "size" in b]
    bad: list[str] = []
    for c in casings:
        if not isinstance(c, dict) or "bottom" not in c or "od" not in c:
            continue
        depth, od = c["bottom"].value, c["od"].value
        # the hole section this string bottoms in is the SHALLOWEST section whose
        # bottom reaches that depth, not the smallest bit on the record
        fits = sorted((to, size) for to, size in sections if to >= depth - 1e-9)
        if not fits:
            continue
        bit = fits[0][1]
        if od >= bit:
            bad.append(f"{c.get('string', 'casing')} OD {od:g} in at {depth:g} ft "
                       f"vs bit {bit:g} in")
    if bad:
        fields["E"] = replace(fields["E"], flags=tuple(dict.fromkeys(
            fields["E"].flags + (f"casing-exceeds-bit: {'; '.join(bad)}",))))


# --------------------------------------------------------------------------
# Plausibility. Flags only - the value is returned unchanged.
# --------------------------------------------------------------------------
def _band_flag(item: str, q: Quantity, band: tuple[float, float]) -> Quantity:
    lo, hi = band
    house = PLAUSIBLE_UNIT.get(item, "")
    # A band stated in lb/gal says nothing about a number the scan stated in
    # pcf. Judging it anyway would produce a confident wrong verdict, so say
    # instead that it cannot be judged. Conversion is `unit_convert` (#11).
    if q.unit and house and q.unit.lower() != house.lower():
        return replace(q, flags=tuple(dict.fromkeys(q.flags + (
            f"plausibility-not-checked: value is in {q.unit!r} but the house band "
            f"for RRC item {item} is in {house}; convert before judging",))))
    if lo <= q.value <= hi:
        return q
    return replace(q, flags=tuple(dict.fromkeys(q.flags + (
        f"implausible: {q.value:g} {q.unit or house} outside "
        f"the house plausibility band {lo:g}-{hi:g} for RRC item {item}; value "
        "returned unchanged, not corrected",))))


def _plausibility(fields: dict[str, HeaderField],
                  bands: Mapping[str, tuple[float, float]], flags: list[str]) -> None:
    for item, f in list(fields.items()):
        band = bands.get(item)
        val = f.value
        if isinstance(val, Quantity) and band:
            fields[item] = replace(f, value=_band_flag(item, val, band))
        elif isinstance(val, dict) and band:
            fields[item] = replace(f, value={
                k: (_band_flag(item, v, band) if isinstance(v, Quantity) else v)
                for k, v in val.items()})
        elif isinstance(val, list):
            new = []
            for entry in val:
                if not isinstance(entry, dict):
                    new.append(entry)
                    continue
                e = dict(entry)
                for key, q in list(e.items()):
                    if not isinstance(q, Quantity):
                        continue
                    sub = bands.get(f"{item}.{key}")
                    if sub is not None:
                        e[key] = _band_flag(f"{item}.{key}", q, sub)
                    elif key in ("size", "od") and band:
                        e[key] = _band_flag(item, q, band)
                new.append(e)
            fields[item] = replace(f, value=new)


# --------------------------------------------------------------------------
# Digital cross-check. Promotes evidence; never backfills an absent field.
# --------------------------------------------------------------------------
def _agrees(value: Any, digital: Any) -> bool:
    if isinstance(value, Quantity):
        return isinstance(digital, (int, float)) and abs(value.value - float(digital)) < 1e-6
    if isinstance(value, Range):
        return (isinstance(digital, (int, float))
                and value.low - 1e-6 <= float(digital) <= value.high + 1e-6)
    if isinstance(value, str):
        return isinstance(digital, str) and value.strip().lower() == digital.strip().lower()
    if isinstance(value, dict):
        return any(_agrees(v, digital) for v in value.values())
    if isinstance(value, list):
        return any(_agrees(v, digital) for v in value)
    return False


def _apply_digital(fields: dict[str, HeaderField], blank: Mapping[str, str],
                   las_header: Mapping[str, Any] | None, flags: list[str]) -> None:
    if not las_header:
        return
    for item, digital in las_header.items():
        f = fields.get(item)
        if f is None:
            # A digital value never fills an absent OCR field. Say it is
            # available and leave the item missing.
            flags.append(f"digital-value-available-for-absent-item-{item}; not "
                         "used to fill the scan - call header_extract (#4) for it")
            continue
        if _agrees(f.value, digital):
            fields[item] = replace(f, evidence=EVIDENCE_OCR_CONFIRMED)
        else:
            fields[item] = replace(f, flags=tuple(dict.fromkeys(f.flags + (
                f"disagrees-with-digital-header: scan reads {f.raw!r}, digital "
                f"header declares {digital!r}",))))


def _confidence_flags(fields: dict[str, HeaderField], threshold: float) -> None:
    for item, f in list(fields.items()):
        if f.confidence is not None and f.confidence < threshold:
            fields[item] = replace(f, flags=tuple(dict.fromkeys(f.flags + (
                f"ocr-low-confidence: {f.confidence:.2f} below the caller's "
                f"threshold {threshold:.2f}",))))


# --------------------------------------------------------------------------
def _missing(fields: Mapping[str, HeaderField],
             blank: Mapping[str, str]) -> tuple[MissingItem, ...]:
    out: list[MissingItem] = []
    for letter in _letters():
        if letter in fields:
            continue
        reason = "value-blank" if letter in blank else "label-not-found"
        out.append(MissingItem(item=letter, label=_label(letter), reason=reason))
    return tuple(out)


__all__ = ["raster_header_ocr", "require_item", "RasterHeader", "HeaderField",
           "MissingItem", "Conflict", "PLAUSIBLE", "EVIDENCE_DIGITAL",
           "EVIDENCE_OCR_CONFIRMED", "EVIDENCE_OCR", "EVIDENCE_DERIVED"]
