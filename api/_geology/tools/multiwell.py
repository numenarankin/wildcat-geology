"""Group O: correlation, thickness and structure across an offset set.

These six exist because `offsets_within_radius` now returns a real offset
population. Until it did, the harness had wells to correlate against and nothing
to correlate them with.

**Subsea is the whole game.** A depth is measured from its own well's datum, so
two wells' depths are not comparable until both are hung on sea level. A KB/GL
mix is a constant elevation offset that reads as dip, and over the well spacing
in a stripper field it can invert the structure. `structure_map` and
`offset_consistency` therefore place every pick through `geometry.subsea_convert`
(#18), and a well whose datum will not resolve is EXCLUDED and COUNTED in the
result. It is never defaulted, and it is never quietly dropped either: the count
is what tells the operator the surface was fitted from six wells and not nine.

`isopach` is the deliberate exception, and the reason is worth stating because it
looks like an inconsistency. A thickness is the difference of two depths in the
SAME well, so that well's datum cancels exactly. Requiring a datum there would be
a false refusal on the one structural number that does not need one.

**Why this fits a plane where `structural_dip` refuses to.** `geometry.
true_dip_from_picks` refuses on three or more picks because the three-point
construction, a plane forced exactly through three points, is named in the corpus
(`tearpock#219`) with no procedure. That refusal stands. What is published is
something else: `wermund-1975#3` states the trend-surface method, "the sum of the
squares of all points is best fitted to a curved surface, algebraically defined",
with points above the surface as positive residuals and below as negative, and
`tearpock#16` lists Least squares among the methods for estimating a surface from
control points. A regression needs more equations than unknowns. A plane has
three, so three picks make the residuals identically zero and the fit is the
unpublished three-point construction under a new name, with an r-squared of 1 for
a surface nothing tested. Four is the first honest fit and is the refusal
boundary, matching the sibling TypeScript tool `rrc_structure_surface`.

**What has no corpus method.** `curve_normalize` refuses. `beg-boonsville#36` is
the only multi-well normalization account in the corpus, it describes shifting a
well's crossplot clusters onto a standard well's by eye, publishes no statistic,
and explicitly declines to normalize the gamma ray at all. A tool that guessed
the industry two-point percentile transform and hung `beg#36` on it would pass
`provenance_audit` while citing a page that says the opposite.
"""
from __future__ import annotations

import math
from bisect import bisect_left
from collections.abc import Mapping, Sequence
from typing import Any

# Cross-module imports bind the MODULE, never its functions. `registry()` walks
# `tools.*` and the first module alphabetically to expose a public name owns it,
# so `from .geometry import subsea_convert` would silently re-home a working tool
# onto this file: `multiwell` sorts before `geometry`, nothing raises, and the
# only symptom is the wrong module name in the catalog. Anything imported here by
# value must be a non-callable (a constant) or aliased private.
from . import geometry
from .curves import BEG_DATA_PREP  # a str anchor, not a callable
from .result import Quantity, Range, Refusal

# --------------------------------------------------------------------------- #
# Corpus anchors. Every one resolves to a key in geology-corpus/toc/
# .segments.jsonl, and `test_multiwell.py` asserts that on every anchor here.
# --------------------------------------------------------------------------- #

_TEARPOCK = "06-fort-worth-basin/tearpock-bischke-applied-subsurface-geological-mapping"

#: Chap. 2, gridding. "Linear data are unsuitable for surface fitting" (the
#: collinearity refusal), Least squares and Polynomial fit listed among the
#: methods for estimating a surface from control points, and the tolerance rule
#: this module's residual test rests on: "Gridding can never guarantee maps that
#: honor all of the data points ... the non-honoring of data may be acceptable
#: if ... the calculated value and the observed value at a data point location
#: differ by an amount that is within the accuracy of the data."
TEARPOCK_GRIDDING = f"{_TEARPOCK}#16"

#: Chap. 4. "We suggest that all detailed electric log correlation be undertaken
#: by concentrating on shale sections."
TEARPOCK_CORRELATION = f"{_TEARPOCK}#28"

#: Chap. 4. "In order to ensure confidence in the fault, Well No. 3 should be
#: correlated with at least one more nearby well." A single machine match is not
#: a correlation, and this is the corpus saying so.
TEARPOCK_CORRELATION_CHECK = f"{_TEARPOCK}#29"

#: Chap. 14 p. 723. "An isochore map delineates the true vertical thickness of a
#: stratigraphic interval, whereas an isopach map illustrates the true
#: stratigraphic thickness."
TEARPOCK_ISOCHORE_ISOPACH = f"{_TEARPOCK}#225"

#: Chap. 14, Eq. (14-10): TST = (TVT)(cos phi), phi = true bed dip.
TEARPOCK_TST = f"{_TEARPOCK}#239"

#: Chap. 14, Eq. (14-11): TST = TVT / (sin alpha tan phi + cos alpha), for an
#: interval whose upper (alpha) and lower (phi) surfaces dip differently.
TEARPOCK_TST_TWO_DIPS = f"{_TEARPOCK}#240"

#: Wermund 1975, North-Central Texas. The trend surface: "Related to a selected
#: polynomial function, the sum of the squares of all points is best fitted to a
#: curved surface, algebraically defined ... Values that fall above the best
#: fitted surface are positive residuals, and those below the surface are
#: negative residuals." Order 1 of that family is a plane.
WERMUND_TREND_SURFACE = "06-fort-worth-basin/wermund-1975-upper-penn-limestone-banks#3"

#: The datum gate, shared with `subsea_convert` (#18) and `structural_dip` (#20).
TEARPOCK_DATUM = geometry.TEARPOCK_DATUM

#: `beg-boonsville#36`, imported from `curves` so the anchor has one definition.
#: Its "### Depth Shift" section is the depth-shift rule: "For wells than had
#: multiple runs, the various runs were depth-shifted to match the resistivity
#: suite to the nearest foot." Its "## Normalization" section is the whole of
#: what the corpus says about normalizing across a well set, and is why
#: `curve_normalize` refuses.
BEG_DEPTH_SHIFT = BEG_DATA_PREP

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

#: SOURCED by arithmetic, not by threshold: a plane has three coefficients, so a
#: three-pick fit has zero degrees of freedom. See the module docstring.
MIN_PLANE_PICKS = 4

FT_PER_MILE = geometry.FT_PER_MILE

#: HOUSE RULE, and geometry's number rather than a second one. Scale-free:
#: largest perpendicular offset from the widest-separated pair, over that pair's
#: separation. Permitted only because it selects a REFUSAL and can never reach a
#: returned value.
COLLINEAR_TOLERANCE_RATIO = geometry.DEFAULT_COLLINEAR_TOLERANCE_RATIO

#: Decimation for the correlation search. Cross-correlating a 20,000-sample log
#: at every lag is minutes of pure Python, so the search runs coarse then refines
#: locally, and the decimation actually used is reported in `assumptions`.
#: The coarse sweep's node-times-lag budget, from which the coarse lattice
#: spacing is derived; the refinement's node cap is fixed because its lag range
#: is only a few coarse steps wide.
MAX_COARSE_EVALUATIONS = 200_000
FINE_NODES = 2048

#: Below this a correlation coefficient is computed from too few pairs to mean
#: anything. HOUSE RULE, and it gates a REFUSAL only.
MIN_CORRELATION_PAIRS = 8

_FLAG_NOTES: dict[str, str] = {
    "excluded_unresolved_datum": (
        "One or more offsets could not be placed in subsea and were left out of "
        "the fit. They are counted in inputs.excluded, never defaulted to zero: "
        "a pick hung on an unknown zero is an elevation error the map cannot "
        "distinguish from structure."
    ),
    "one_degree_of_freedom": (
        "Four picks against three plane coefficients leaves one degree of "
        "freedom. The residuals are real but a single bad pick still moves the "
        "surface a long way; r-squared is not evidence at this n."
    ),
    "order_1_trend_surface": (
        "wermund#3 fits polynomials of any order; this is order 1, a plane. A "
        "real horizon that folds will show that folding as residual, not as a "
        "worse plane."
    ),
    "residual_exceeds_tolerance": (
        "tearpock#16: a surface need not honor every point, but only where the "
        "miss is within the accuracy of the data. These picks are outside the "
        "accuracy the caller declared, and the usual cause is a datum error "
        "rather than geology. Run datum_reconcile (#16) on them before "
        "reinterpreting the structure."
    ),
    "correlation_is_interpretive": (
        "tearpock#28 correlates on shale sections and character across several "
        "markers; tearpock#29 requires the result be confirmed against at least "
        "one more nearby well. A single curve-shape match is a proposal, not a "
        "pick."
    ),
    "no_coefficient_threshold_in_corpus": (
        "No corpus source states the coefficient at which a shape match becomes "
        "a correlation. The coefficient is reported and no verdict is reached "
        "unless the caller supplied min_coefficient."
    ),
    "thickness_needs_no_datum": (
        "Top and base come off the same well, so that well's datum cancels "
        "exactly. Unlike structure_map, this tool neither needs nor asks for a "
        "resolved datum."
    ),
    "shift_at_search_limit": (
        "The best lag sits at the edge of the +/-max_shift_ft search, so the "
        "true shift may be larger and outside it. Widen max_shift_ft and rerun "
        "before applying this correction."
    ),
    "measured_thickness_not_vertical": (
        "depth_basis is MD, so these thicknesses carry hole deviation. "
        "tearpock#232 Eq. (4-3): TVT = MLT cos(psi). Convert with md_to_tvd "
        "(#17) before mapping."
    ),
}


# --------------------------------------------------------------------------- #
# Pick placement: the datum gate, applied per well rather than to the set
# --------------------------------------------------------------------------- #


def _number(value: Any, field: str, well: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"pick {well!r}: {field} must be a number in feet, got {type(value).__name__}"
        )
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"pick {well!r}: {field} is not finite ({value!r})")
    return out


def _place(pick: Mapping[str, Any]) -> dict[str, Any]:
    """One pick to `{well, x_ft, y_ft, sstvd_ft, depth_reference}` or a reason.

    Two accepted shapes. Already subsea: `sstvd_ft` plus `datum_resolved` and
    `depth_reference`, the field set `structural_dip` (#20) takes. Raw: `tvd_ft`
    plus `datum`, which is handed to `subsea_convert` (#18) so the conversion is
    done in one place and against the reference the depths are actually hung on.
    """
    well = pick.get("well", "unnamed")
    out: dict[str, Any] = {
        "well": well,
        "x_ft": _number(pick["x_ft"], "x_ft", well),
        "y_ft": _number(pick["y_ft"], "y_ft", well),
    }

    if pick.get("sstvd_ft") is not None:
        if not pick.get("datum_resolved"):
            out["excluded"] = (
                "datum_resolved is not set, so this subsea depth is hung on an "
                "unknown zero"
            )
            return out
        reference = pick.get("depth_reference")
        if not reference:
            out["excluded"] = (
                "no depth_reference, so which elevation this subsea depth was "
                "measured from is unknown"
            )
            return out
        out["sstvd_ft"] = _number(pick["sstvd_ft"], "sstvd_ft", well)
        out["depth_reference"] = str(reference)
        return out

    if pick.get("tvd_ft") is None:
        out["excluded"] = "no sstvd_ft and no tvd_ft; this pick carries no depth"
        return out

    converted = geometry.subsea_convert(
        _number(pick["tvd_ft"], "tvd_ft", well),
        datum=pick.get("datum"),
        depth_reference=pick.get("depth_reference"),
        deviated=bool(pick.get("deviated", False)),
    )
    if isinstance(converted, Refusal):
        out["excluded"] = f"subsea_convert refused: {converted.reason}"
        return out
    out["sstvd_ft"] = float(converted.value)
    out["depth_reference"] = str(converted.inputs.get("reference", ""))
    return out


def _population(picks: Sequence[Mapping[str, Any]]) -> tuple[list[dict], list[dict]] | Refusal:
    """Split the offsets into placed and excluded, and refuse a mixed reference."""
    if not isinstance(picks, Sequence) or isinstance(picks, (str, bytes)):
        raise ValueError("picks must be a sequence of pick mappings")

    placed: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    seen: set[Any] = set()
    for i, pick in enumerate(picks):
        if not isinstance(pick, Mapping):
            raise ValueError(f"pick {i} is not a mapping; got {type(pick).__name__}")
        row = _place(pick)
        if row["well"] in seen:
            return Refusal(
                reason=(
                    f"well {row['well']!r} appears twice in the pick set; a "
                    "duplicate weights one control point double in a least-squares "
                    "fit and signals a merge defect upstream"
                ),
                needed=("one pick per well",),
                source=TEARPOCK_GRIDDING,
            )
        seen.add(row["well"])
        (excluded if "excluded" in row else placed).append(row)

    references = sorted({p["depth_reference"] for p in placed if p["depth_reference"]})
    if len(references) > 1:
        return Refusal(
            reason=(
                f"the placed picks are hung on different depth references "
                f"{references}; a KB-versus-GL mix is a constant elevation offset "
                "between wells that reads as dip, and no residual test can "
                "separate it from structure once it is in the fit"
            ),
            needed=(
                "datum_reconcile (#16) to confirm one reference across the set, "
                "and the correction where there is not",
            ),
            source=TEARPOCK_DATUM,
        )
    return placed, excluded


def _population_inputs(placed: Sequence[Mapping[str, Any]],
                       excluded: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "wells_supplied": len(placed) + len(excluded),
        "placed_in_subsea": len(placed),
        "excluded_no_datum": len(excluded),
        "excluded": [{"well": e["well"], "reason": e["excluded"]} for e in excluded],
    }


# --------------------------------------------------------------------------- #
# The plane. wermund#3 order 1, solved on centred coordinates.
# --------------------------------------------------------------------------- #


def _collinear_ratio(points: Sequence[Mapping[str, Any]]) -> tuple[float, float, tuple[Any, Any]]:
    """(ratio, base_ft, base_wells) using `structural_dip`'s own measure.

    Largest perpendicular offset from the widest-separated pair, over that
    pair's separation. Same measure and same threshold constant as
    `geometry.true_dip_from_picks`, so the two tools cannot disagree about
    whether a well set has map width.
    """
    base, pair = 0.0, (points[0], points[1])
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = math.hypot(points[j]["x_ft"] - points[i]["x_ft"],
                           points[j]["y_ft"] - points[i]["y_ft"])
            if d > base:
                base, pair = d, (points[i], points[j])
    if base == 0.0:
        return 0.0, 0.0, (pair[0]["well"], pair[1]["well"])

    p, q = pair
    ux, uy = q["x_ft"] - p["x_ft"], q["y_ft"] - p["y_ft"]
    offset = 0.0
    for r in points:
        cross = abs(ux * (r["y_ft"] - p["y_ft"]) - uy * (r["x_ft"] - p["x_ft"]))
        offset = max(offset, cross / base)
    return offset / base, base, (p["well"], q["well"])


def _fit_plane(points: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Least-squares plane z = a*x + b*y + c over subsea picks.

    Centred before solving, which reduces the 3x3 normal equations to a 2x2 with
    a determinant that means something. The caller has already refused collinear
    sets, so the determinant here is non-zero.
    """
    n = len(points)
    mx = sum(p["x_ft"] for p in points) / n
    my = sum(p["y_ft"] for p in points) / n
    mz = sum(p["sstvd_ft"] for p in points) / n

    sxx = sxy = syy = sxz = syz = szz = 0.0
    for p in points:
        dx, dy = p["x_ft"] - mx, p["y_ft"] - my
        dz = p["sstvd_ft"] - mz
        sxx += dx * dx
        sxy += dx * dy
        syy += dy * dy
        sxz += dx * dz
        syz += dy * dz
        szz += dz * dz

    det = sxx * syy - sxy * sxy
    a = (sxz * syy - syz * sxy) / det
    b = (syz * sxx - sxz * sxy) / det
    c = mz - a * mx - b * my

    residuals = {str(p["well"]): p["sstvd_ft"] - (a * p["x_ft"] + b * p["y_ft"] + c)
                 for p in points}
    ssres = sum(r * r for r in residuals.values())
    grad = math.hypot(a, b)
    return {
        "a": a,
        "b": b,
        "c": c,
        "n": n,
        "dip_deg": math.degrees(math.atan(grad)),
        # The gradient points up-dip, so down-dip is its negative, and
        # atan2(east, north) is a compass bearing rather than the mathematical
        # convention. None where the surface is flat and has no down-dip.
        "dip_azimuth_deg": (None if grad == 0.0
                            else math.degrees(math.atan2(-a, -b)) % 360.0),
        "dip_ft_per_mile": grad * FT_PER_MILE,
        "rmse_ft": math.sqrt(ssres / n),
        "r2": None if szz == 0.0 else 1.0 - ssres / szz,
        "residuals_ft": residuals,
    }


def _surface(picks: Sequence[Mapping[str, Any]]
             ) -> tuple[dict[str, Any], list[dict], list[dict]] | Refusal:
    """Population, gates and fit, shared by `structure_map` and `offset_consistency`."""
    split = _population(picks)
    if isinstance(split, Refusal):
        return split
    placed, excluded = split

    if len(placed) < MIN_PLANE_PICKS:
        return Refusal(
            reason=(
                f"{len(placed)} offset(s) carry this pick AND a resolvable datum; "
                f"a least-squares surface needs {MIN_PLANE_PICKS}. A plane has "
                "three coefficients, so three picks fit it exactly, report an "
                "r-squared of 1 and have tested nothing. wermund#3's trend "
                "surface is a regression and needs more control points than "
                "coefficients; the exact three-point construction is a different "
                "method, and tearpock#219 names it without publishing it"
            ),
            needed=(
                f"{MIN_PLANE_PICKS} or more picks on one horizon with a resolved datum",
                "datum_resolve (#15) on the offsets that were excluded",
            ),
            source=WERMUND_TREND_SURFACE,
        )

    ratio, base, base_wells = _collinear_ratio(placed)
    if ratio < COLLINEAR_TOLERANCE_RATIO:
        return Refusal(
            reason=(
                f"the {len(placed)} placed picks are collinear in map view "
                f"(perpendicular spread ratio {ratio:.5f} over a {base:.1f} ft "
                f"base, below {COLLINEAR_TOLERANCE_RATIO}). tearpock#16: 'Linear "
                "data are unsuitable for surface fitting.' Wells on one section "
                "line sample one direction, so a fit through them returns a "
                "precise and meaningless dip azimuth"
            ),
            needed=(
                "a pick from a well off the line joining "
                f"{base_wells[0]!r} and {base_wells[1]!r}",
                "or apparent dip along the section line via structural_dip (#20)",
            ),
            source=TEARPOCK_GRIDDING,
        )

    return _fit_plane(placed), placed, excluded


# --------------------------------------------------------------------------- #
# Curve sampling for the correlation search
# --------------------------------------------------------------------------- #


def _clean(depth_ft: Sequence[float], values: Sequence[Any], null_value: float | None,
           label: str) -> tuple[list[float], list[float]]:
    """Ascending depth, live samples only. Raises on a malformed call."""
    if len(depth_ft) != len(values):
        raise ValueError(
            f"{label}: {len(values)} values for {len(depth_ft)} depths; a curve "
            "and its index must be the same length"
        )
    rows = []
    for z, v in zip(depth_ft, values):
        if z is None or not isinstance(z, (int, float)) or not math.isfinite(float(z)):
            continue
        if v is None or isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        fv = float(v)
        if not math.isfinite(fv):
            continue
        if null_value is not None and fv == float(null_value):
            continue
        rows.append((float(z), fv))
    rows.sort(key=lambda r: r[0])
    return [r[0] for r in rows], [r[1] for r in rows]


def _median_step(depths: Sequence[float]) -> float:
    steps = sorted(depths[i + 1] - depths[i] for i in range(len(depths) - 1))
    return steps[len(steps) // 2] if steps else 0.0


def _at(depths: Sequence[float], values: Sequence[float], z: float,
        max_gap: float) -> float | None:
    """Linear interpolation at `z`, or None across a gap wider than `max_gap`.

    A lookup inside a search, not a resampling product: `depth_resample` (#13) is
    the tool that builds a grid, states what it cost and refuses on upsampling,
    and nothing here is returned to a caller as a curve.
    """
    i = bisect_left(depths, z)
    if i == 0:
        return values[0] if depths[0] == z else None
    if i >= len(depths):
        return values[-1] if depths[-1] == z else None
    z0, z1 = depths[i - 1], depths[i]
    if z1 - z0 > max_gap:
        return None
    if z1 == z0:
        return values[i]
    t = (z - z0) / (z1 - z0)
    return values[i - 1] + t * (values[i] - values[i - 1])


def _coefficient(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Pearson coefficient. A definition, not a corpus correlation."""
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0.0 or syy <= 0.0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def _score(nodes: Sequence[float], ref_vals: Sequence[float],
           tz: Sequence[float], tv: Sequence[float], lag: float,
           max_gap: float) -> tuple[float | None, int]:
    """Coefficient between the reference at `nodes` and the target lagged by `lag`.

    `lag` is the correction: a feature the reference sees at z is expected in the
    unshifted target at z - lag, so adding `lag` to the target's depths aligns it.
    """
    xs: list[float] = []
    ys: list[float] = []
    for z, rv in zip(nodes, ref_vals):
        v = _at(tz, tv, z - lag, max_gap)
        if v is None:
            continue
        xs.append(rv)
        ys.append(v)
    return _coefficient(xs, ys), len(xs)


def _grid(lo: float, hi: float, cap: int, floor_step: float) -> list[float]:
    span = hi - lo
    step = max(span / cap, floor_step)
    n = max(2, int(span / step) + 1)
    return [lo + i * step for i in range(n)]


def _coarse_step(span: float, max_shift: float, fine_step: float) -> float:
    """The largest sample multiple whose full sweep fits the evaluation budget.

    Chosen from the budget rather than from a fixed node count, because the
    coarse LAG step is what has to stay short, not the node spacing. A node cap
    of 512 put the coarse lags 19.5 ft apart on a 10,000 ft log, and a curve
    whose shortest bed was 17 ft has correlation maxima every 17 ft: sampling
    that surface every 19.5 ft picked a neighbouring maximum, and a +12.5 ft
    shift came back as -21.0 ft. Cost is (span/s)(2 max_shift/s + 1), so
    doubling s quarters it and a few doublings buys a step of a few feet even on
    a very long log.
    """
    step = fine_step
    while step < span:
        nodes = span / step
        lags = 2.0 * max_shift / step + 1.0
        if nodes * lags <= MAX_COARSE_EVALUATIONS:
            return step
        step *= 2.0
    return max(step, fine_step)


def _blocks(depths: Sequence[float], values: Sequence[float], origin: float,
            step: float, j0: int, j1: int) -> tuple[list[float], list[float | None]]:
    """Block means on the lattice `origin + j*step`, for j in [j0, j1).

    Averaged, not point-sampled. A block mean is a low-pass filter, so the
    coarse correlation surface is smooth at the coarse lag spacing, which is the
    property the coarse pass needs and point sampling does not give it. Both
    curves are put on the SAME lattice so a coarse lag is an index shift and the
    two sides carry identical filtering.
    """
    centres: list[float] = []
    means: list[float | None] = []
    lo_i = 0
    for j in range(j0, j1):
        a = origin + j * step
        b = a + step
        lo_i = bisect_left(depths, a, lo_i)
        hi_i = bisect_left(depths, b, lo_i)
        centres.append(a + 0.5 * step)
        means.append(sum(values[lo_i:hi_i]) / (hi_i - lo_i) if hi_i > lo_i else None)
    return centres, means


def _best_shift(ref_depth_ft: Sequence[float], ref_values: Sequence[Any],
                target_depth_ft: Sequence[float], target_values: Sequence[Any],
                *, max_shift_ft: float, null_value: float | None,
                window: tuple[float, float] | None) -> dict[str, Any] | Refusal:
    """Coarse cross-correlation over the whole overlap, then a local refinement."""
    if not isinstance(max_shift_ft, (int, float)) or not math.isfinite(float(max_shift_ft)) \
            or float(max_shift_ft) <= 0.0:
        raise ValueError(f"max_shift_ft must be a positive finite number, got {max_shift_ft!r}")
    max_shift = float(max_shift_ft)

    rz, rv = _clean(ref_depth_ft, ref_values, null_value, "reference")
    tz, tv = _clean(target_depth_ft, target_values, null_value, "target")
    if len(rz) < 2 or len(tz) < 2:
        return Refusal(
            reason=(f"the reference has {len(rz)} live sample(s) and the target "
                    f"{len(tz)}; a shape match needs a curve on both"),
            needed=("at least two live samples on each curve",),
            source=BEG_DEPTH_SHIFT,
        )

    lo = max(rz[0], tz[0] - max_shift)
    hi = min(rz[-1], tz[-1] + max_shift)
    if window is not None:
        lo, hi = max(lo, window[0]), min(hi, window[1])
    if hi - lo <= 0.0:
        return Refusal(
            reason=(f"the reference ({rz[0]:g}-{rz[-1]:g} ft) and the target "
                    f"({tz[0]:g}-{tz[-1]:g} ft) share no interval within a "
                    f"{max_shift:g} ft shift, so there is no common rock to match"),
            needed=("two logs over an overlapping depth interval",
                    "or a larger max_shift_ft",),
            source=BEG_DEPTH_SHIFT,
        )

    span = hi - lo
    # A repeated depth makes the median increment zero, which would divide by
    # zero in the lattice below. Fall back to the finest grid the refinement
    # would use anyway rather than refusing over a duplicated row.
    steps = [s for s in (_median_step(rz), _median_step(tz)) if s > 0.0]
    fine_step = min(steps) if steps else span / FINE_NODES
    ref_step = _median_step(rz) or fine_step
    tgt_step = _median_step(tz) or fine_step
    max_gap = 4.0 * tgt_step

    # --- Stage 1: block-averaged lattice, lags are index shifts on it ---------
    coarse_step = _coarse_step(span, max_shift, fine_step)
    n_ref = max(1, int(math.ceil(span / coarse_step)))
    reach_j = int(math.ceil(max_shift / coarse_step))
    _, ref_blocks = _blocks(rz, rv, lo, coarse_step, 0, n_ref)
    _, tgt_blocks = _blocks(tz, tv, lo, coarse_step, -reach_j, n_ref + reach_j)

    coarse_best: tuple[float, float, int] | None = None
    for m in range(-reach_j, reach_j + 1):
        xs: list[float] = []
        ys: list[float] = []
        for j, a in enumerate(ref_blocks):
            b = tgt_blocks[j - m + reach_j]
            if a is None or b is None:
                continue
            xs.append(a)
            ys.append(b)
        coef = _coefficient(xs, ys) if len(xs) >= MIN_CORRELATION_PAIRS else None
        if coef is not None and (coarse_best is None or coef > coarse_best[1]):
            coarse_best = (m * coarse_step, coef, len(xs))

    if coarse_best is None:
        return Refusal(
            reason=(f"no lag in +/-{max_shift:g} ft produced "
                    f"{MIN_CORRELATION_PAIRS} paired samples with a defined "
                    f"coefficient over {lo:g}-{hi:g} ft; one of the two curves is "
                    "flat, too short or too sparse over the overlap"),
            needed=("curves with character over the shared interval",),
            source=BEG_DEPTH_SHIFT,
        )

    # --- Stage 2: sample-rate lags, near the coarse winner --------------------
    # Node decimation here only reduces the number of pairs; it does not move the
    # peak, because every pair is a true sample of both curves at matched depth.
    fine_nodes = _grid(lo, hi, FINE_NODES, fine_step)
    fine = [(z, _at(rz, rv, z, 4.0 * ref_step)) for z in fine_nodes]
    fn = [z for z, v in fine if v is not None]
    fv = [v for _, v in fine if v is not None]
    centre = round(coarse_best[0] / fine_step)
    # Two coarse steps either side: the coarse peak locates the basin, not the
    # summit, and it is only resolved to the wavelength the block average left.
    reach = 2 * int(math.ceil(coarse_step / fine_step)) + 1
    fine_best: tuple[float, float, int] | None = None
    for i in range(-reach, reach + 1):
        lag = (centre + i) * fine_step
        if abs(lag) > max_shift:
            continue
        coef, pairs = _score(fn, fv, tz, tv, lag, max_gap)
        if coef is None or pairs < MIN_CORRELATION_PAIRS:
            continue
        if fine_best is None or coef > fine_best[1]:
            fine_best = (lag, coef, pairs)
    best = fine_best or coarse_best

    return {
        "shift_ft": best[0],
        "coefficient": best[1],
        "n_pairs": best[2],
        "overlap_ft": [lo, hi],
        "coarse_shift_ft": coarse_best[0],
        "coarse_coefficient": coarse_best[1],
        "assumptions": {
            "search": "block-averaged cross-correlation over the whole overlap, "
                      "then sample-rate lags within two coarse steps of the winner",
            "decimation": (
                f"both curves block-AVERAGED onto a {coarse_step:g} ft lattice "
                f"({n_ref} nodes) for the coarse pass, from a {ref_step:g} ft "
                f"sample interval; the refinement uses at most {FINE_NODES} "
                f"point samples at {fine_step:g} ft lag resolution"
            ),
            "coarse_lag_step_ft": coarse_step,
            "fine_lag_step_ft": fine_step,
            "max_shift_ft": max_shift,
            "statistic": "Pearson correlation coefficient of the paired samples",
            "interpolation": "linear, never across a gap wider than "
                             f"{max_gap:g} ft (4 x the target sample interval)",
            "sign": "shift is ADDED to the target's depths to align it with the "
                    "reference",
        },
    }


# --------------------------------------------------------------------------- #
# 1. curve_normalize - refuses. See the module docstring.
# --------------------------------------------------------------------------- #


def curve_normalize(wells: Any = None, curve: str = "", *,
                    reference_well: Any = None) -> Refusal:
    """Normalize a curve across a well set. Always a `Refusal`.

    The return type is `Refusal` and not `Quantity | Refusal` on purpose, the
    same way `geometry.true_dip_from_picks` declares its own: the absence of a
    method belongs in the signature, not in a comment.

    Multi-well normalization is practice literature and the three reference works
    in this corpus are not it. The one account present, `beg-boonsville#36`,
    normalized neutron and density by shifting each well's crossplot clusters
    onto a standard well's, chose the standard by eye, published no statistic for
    either the cluster position or the shift, and says of the curve this tool
    would most often be asked for: "No attempt was made to normalize the
    gamma-ray logs."
    """
    return Refusal(
        reason=(
            f"no corpus source publishes a curve normalization transform"
            + (f" for {curve!r}" if curve else "")
            + ". beg-boonsville#36 is the corpus's only multi-well "
            "normalization, and it is an account rather than a method: neutron "
            "and density crossplots were 'shifted linearly along the density "
            "axis and/or the neutron axis to fit the standard', with the "
            "standard chosen by inspection and no statistic given for the "
            "shift. On the gamma ray it states the opposite of what this tool "
            "would do: 'No attempt was made to normalize the gamma-ray logs ... "
            "the normalization of the gamma-ray curve was deemed unnecessary' "
            "because shale and clean-sand values were picked per well at "
            "analysis time. Applying a two-point percentile transform here and "
            "citing that page would rewrite every Vsh downstream, and would "
            "pass provenance_audit while contradicting its own source"
        ),
        needed=(
            "a corpus source publishing a normalization transform: which "
            "statistic of the curve is aligned (percentile, clean-sand and "
            "shale line, or cluster), how the reference is chosen, and whether "
            "the correction is a shift or a shift and a scale",
            "meanwhile, beg#36's own route: pick the shale and clean-sand "
            "values per well at analysis time, so Vsh is computed against each "
            "well's own tool response and no transform is needed",
            "for depth registry between runs of one well rather than "
            "calibration between wells, use depth_shift or overlap_offset (#14)",
        ),
        source=BEG_DEPTH_SHIFT,
    )


# --------------------------------------------------------------------------- #
# 2. depth_shift
# --------------------------------------------------------------------------- #


def depth_shift(reference_depth_ft: Sequence[float],
                reference_values: Sequence[Any],
                target_depth_ft: Sequence[float],
                target_values: Sequence[Any],
                *,
                max_shift_ft: float,
                null_value: float | None = None,
                curve: str = "") -> Quantity | Refusal:
    """The depth correction to apply to a target run, by cross-correlation.

    Returns the shift in feet to ADD to `target_depth_ft` so the target aligns
    with the reference. `curve_splice_detect` (#14) locates run boundaries and
    measures the discontinuity across them and nothing corrects it; this is the
    correction.

    Distinct from `overlap_offset` (#14), which is about the LEVEL: it removes a
    lag bounded by `asquith#64`'s +/-1 ft tool-to-tool registry allowance as a
    nuisance parameter and returns the calibration difference. Here the shift is
    the answer, it is not bounded by the registry allowance, and `max_shift_ft`
    is the caller's declaration of how far a run may plausibly be out.

    The rule is `beg-boonsville#36`: "the various runs were depth-shifted to
    match the resistivity suite to the nearest foot", i.e. one run is chosen as
    the reference and the others are moved onto it. The correlation coefficient
    is a statistical definition, not a corpus correlation.
    """
    found = _best_shift(reference_depth_ft, reference_values,
                        target_depth_ft, target_values,
                        max_shift_ft=max_shift_ft, null_value=null_value, window=None)
    if isinstance(found, Refusal):
        return found

    flags: list[str] = []
    if abs(found["shift_ft"]) >= float(max_shift_ft) - 1e-9:
        flags.append("shift_at_search_limit")
    return Quantity(
        found["shift_ft"],
        "ft",
        "depth shift by cross-correlation, coarse then locally refined; the "
        "rule is beg-boonsville#36 (runs depth-shifted onto a reference suite), "
        "the statistic is the Pearson coefficient and is not a corpus correlation",
        BEG_DEPTH_SHIFT,
        inputs={
            "curve": curve or None,
            "coefficient": found["coefficient"],
            "n_pairs": found["n_pairs"],
            "overlap_ft": found["overlap_ft"],
            "coarse_shift_ft": found["coarse_shift_ft"],
            "coarse_coefficient": found["coarse_coefficient"],
        },
        assumptions=dict(
            found["assumptions"],
            reference_run="not moved; the target is shifted onto it, per beg#36",
            flag_notes={f: _FLAG_NOTES[f] for f in flags},
        ),
        flags=tuple(flags),
    )


# --------------------------------------------------------------------------- #
# 3. auto_correlate
# --------------------------------------------------------------------------- #


def auto_correlate(reference_depth_ft: Sequence[float],
                   reference_values: Sequence[Any],
                   reference_pick_ft: float,
                   target_depth_ft: Sequence[float],
                   target_values: Sequence[Any],
                   *,
                   window_ft: float,
                   max_shift_ft: float,
                   min_coefficient: float | None = None,
                   null_value: float | None = None,
                   curve: str = "") -> Quantity | Refusal:
    """Propose where a picked horizon lands in an offset, by curve shape.

    Matches the reference's shape over `window_ft` centred on `reference_pick_ft`
    against the offset, and returns the proposed depth in the offset's own index
    together with the coefficient and the interval that was matched. A depth
    alone would hide both.

    This is a proposal and the flags say so: `tearpock#28` correlates on shale
    sections and character across several markers, and `tearpock#29` requires the
    result be confirmed against at least one more nearby well. No corpus source
    states a coefficient at which a machine match becomes a correlation, so a
    verdict is reached only where the caller supplies `min_coefficient`.
    """
    if not isinstance(window_ft, (int, float)) or not math.isfinite(float(window_ft)) \
            or float(window_ft) <= 0.0:
        raise ValueError(f"window_ft must be a positive finite number, got {window_ft!r}")
    pick = float(reference_pick_ft)
    if not math.isfinite(pick):
        raise ValueError(f"reference_pick_ft is not a finite depth ({reference_pick_ft!r})")
    half = float(window_ft) / 2.0

    found = _best_shift(reference_depth_ft, reference_values,
                        target_depth_ft, target_values,
                        max_shift_ft=max_shift_ft, null_value=null_value,
                        window=(pick - half, pick + half))
    if isinstance(found, Refusal):
        return found

    shift = found["shift_ft"]
    coefficient = found["coefficient"]
    proposed = pick - shift  # the target reads the horizon this much shallower

    if min_coefficient is not None and coefficient < float(min_coefficient):
        return Refusal(
            reason=(
                f"the best shape match over {found['overlap_ft'][0]:g}-"
                f"{found['overlap_ft'][1]:g} ft scores {coefficient:.3f}, below "
                f"the {float(min_coefficient):.3f} the caller required. The "
                "window matched is not the same character in both wells, which "
                "is what a facies change or a faulted-out section looks like"
            ),
            needed=("a wider window_ft, a curve with more character, or a "
                    "correlation picked by hand on shale markers (tearpock#28)",),
            source=TEARPOCK_CORRELATION,
        )

    flags = ["correlation_is_interpretive"]
    if min_coefficient is None:
        flags.append("no_coefficient_threshold_in_corpus")
    return Quantity(
        proposed,
        "ft",
        "proposed correlation: best-coefficient depth shift of the reference "
        "window onto the offset (beg-boonsville#36 shape matching), reported in "
        "the offset's own depth index. tearpock#28/#29 hold the interpretation",
        TEARPOCK_CORRELATION,
        inputs={
            "curve": curve or None,
            "reference_pick_ft": pick,
            "coefficient": coefficient,
            "shift_ft": shift,
            "n_pairs": found["n_pairs"],
            "reference_window_ft": [pick - half, pick + half],
            "matched_interval_ft": [proposed - half, proposed + half],
            "min_coefficient": None if min_coefficient is None else float(min_coefficient),
        },
        assumptions=dict(
            found["assumptions"],
            verdict=("no verdict: no corpus threshold" if min_coefficient is None
                     else "meets the caller's min_coefficient"),
            confirmation_required=TEARPOCK_CORRELATION_CHECK,
            flag_notes={f: _FLAG_NOTES[f] for f in flags},
        ),
        flags=tuple(flags),
    )


# --------------------------------------------------------------------------- #
# 4. isopach
# --------------------------------------------------------------------------- #


def isopach(picks: Sequence[Mapping[str, Any]],
            *,
            upper_dip_deg: float | None = None,
            lower_dip_deg: float | None = None,
            formation: str = "") -> Range | Refusal:
    """Formation thickness across the offset set, per well and as a band.

    Each pick is a mapping with `well`, `top_ft`, `base_ft` and `depth_basis`.
    Top and base come off the SAME well, so that well's datum cancels and none
    is asked for. That is the one structural number in this module that needs no
    datum, and requiring one would be a false refusal.

    `tearpock#225`: an isochore is true VERTICAL thickness, an isopach is true
    STRATIGRAPHIC thickness, and the two are different numbers for the same rock.
    With no dip supplied this returns the vertical thickness and says so. With
    `upper_dip_deg` it applies Eq. (14-10), TST = TVT cos(phi) (`tearpock#239`);
    with both dips it applies Eq. (14-11), TST = TVT / (sin a tan p + cos a)
    (`tearpock#240`), which reduces to (14-10) when the two dips are equal.
    """
    if not isinstance(picks, Sequence) or isinstance(picks, (str, bytes)):
        raise ValueError("picks must be a sequence of pick mappings")
    if lower_dip_deg is not None and upper_dip_deg is None:
        raise ValueError("lower_dip_deg needs upper_dip_deg; Eq. (14-11) takes both")

    rows: list[dict[str, Any]] = []
    bases: set[str] = set()
    for i, pick in enumerate(picks):
        if not isinstance(pick, Mapping):
            raise ValueError(f"pick {i} is not a mapping; got {type(pick).__name__}")
        well = pick.get("well", "unnamed")
        for field in ("top_ft", "base_ft", "depth_basis"):
            if pick.get(field) is None:
                return Refusal(
                    reason=(f"pick {i} ({well!r}) has no {field}; a thickness needs "
                            "a top, a base and the basis they are measured on"),
                    needed=(field,),
                    source=TEARPOCK_ISOCHORE_ISOPACH,
                )
        top = _number(pick["top_ft"], "top_ft", well)
        base = _number(pick["base_ft"], "base_ft", well)
        if base <= top:
            return Refusal(
                reason=(f"{well!r} has base {base:g} ft at or above top {top:g} ft; "
                        "a negative thickness is a correlation error, not a thin "
                        "interval"),
                needed=("base_ft deeper than top_ft, or the two picks swapped back",),
                source=TEARPOCK_ISOCHORE_ISOPACH,
            )
        bases.add(str(pick["depth_basis"]).strip().upper())
        rows.append({"well": str(well), "tvt_ft": base - top})

    if not rows:
        return Refusal(
            reason="no picks supplied; a thickness map needs at least one well",
            needed=("one or more wells with a top and a base for this interval",),
            source=TEARPOCK_ISOCHORE_ISOPACH,
        )
    if len(bases) > 1:
        return Refusal(
            reason=(f"the picks mix depth bases {sorted(bases)}; measured, vertical "
                    "and subsea thicknesses are different numbers and a map that "
                    "mixes them thickens wherever the hole deviated"),
            needed=("one depth_basis across the set",),
            source=TEARPOCK_ISOCHORE_ISOPACH,
        )
    basis = next(iter(bases))

    flags = ["thickness_needs_no_datum"]
    if basis == "MD":
        flags.append("measured_thickness_not_vertical")

    if upper_dip_deg is None:
        kind, unit = "isochore (true vertical thickness)", "ft TVT"
        method = ("interval thickness per well, base minus top on one well's own "
                  "index; tearpock#225 defines this as the isochore value. No dip "
                  "supplied, so no stratigraphic correction is applied and this is "
                  "NOT an isopach")
        source = TEARPOCK_ISOCHORE_ISOPACH
        factor, equation = 1.0, "TST not computed"
    else:
        upper = math.radians(float(upper_dip_deg))
        if lower_dip_deg is None:
            factor = math.cos(upper)
            equation = "Eq. (14-10) TST = TVT cos(phi)"
            source = TEARPOCK_TST
        else:
            lower = math.radians(float(lower_dip_deg))
            denominator = math.sin(upper) * math.tan(lower) + math.cos(upper)
            if denominator <= 0.0:
                return Refusal(
                    reason=(f"Eq. (14-11) denominator is {denominator:g} for an upper "
                            f"dip of {float(upper_dip_deg):g} deg and a lower dip of "
                            f"{float(lower_dip_deg):g} deg; the two surfaces are not "
                            "bounding one interval at those attitudes"),
                    needed=("dips of one interval's upper and lower surfaces, "
                            "each below 90 deg",),
                    source=TEARPOCK_TST_TWO_DIPS,
                )
            factor = 1.0 / denominator
            equation = "Eq. (14-11) TST = TVT / (sin a tan p + cos a)"
            source = TEARPOCK_TST_TWO_DIPS
        kind, unit = "isopach (true stratigraphic thickness)", "ft TST"
        method = (f"interval thickness per well, base minus top, corrected to true "
                  f"stratigraphic thickness by {equation} (tearpock#225: an isopach "
                  f"contours TST, an isochore contours TVT)")

    members = {r["well"]: r["tvt_ft"] * factor for r in rows}
    values = sorted(members.values())
    return Range(
        low=values[0],
        high=values[-1],
        unit=unit,
        method=method,
        source=source,
        members=members,
        inputs={
            "formation": formation or None,
            "wells": len(rows),
            "depth_basis": basis,
            "vertical_thickness_ft": {r["well"]: r["tvt_ft"] for r in rows},
            "upper_dip_deg": None if upper_dip_deg is None else float(upper_dip_deg),
            "lower_dip_deg": None if lower_dip_deg is None else float(lower_dip_deg),
        },
        assumptions={
            "map_kind": kind,
            "equation": equation,
            "correction_factor": factor,
            "isochore_vs_isopach": TEARPOCK_ISOCHORE_ISOPACH,
            "datum": "not required; top and base are from one well",
            "flag_notes": {f: _FLAG_NOTES[f] for f in flags},
        },
        flags=tuple(flags),
    )


# --------------------------------------------------------------------------- #
# 5. structure_map
# --------------------------------------------------------------------------- #


def structure_map(picks: Sequence[Mapping[str, Any]],
                  *,
                  target_x_ft: float | None = None,
                  target_y_ft: float | None = None,
                  formation: str = "") -> Quantity | Refusal:
    """A subsea top surface fitted from four or more offset picks.

    Extends `structural_dip` (#20) from a dip between two wells to a surface over
    a population: an order-1 trend surface, the least-squares plane of
    `wermund#3`, in subsea feet positive upward. The returned value is the true
    dip in degrees, so it is directly comparable with `structural_dip`'s apparent
    dip, which it must equal or exceed.

    Each pick is a mapping with `well`, `x_ft`, `y_ft` and either `sstvd_ft`
    with `datum_resolved` and `depth_reference`, or `tvd_ft` with `datum` (the
    `datum_resolve` (#15) result), which is placed here through `subsea_convert`
    (#18). A well whose datum will not resolve is excluded and counted in
    `inputs.excluded`.

    Refuses on fewer than four placed picks and on a collinear population. Pass
    `target_x_ft` and `target_y_ft` for the surface's value at an undrilled
    location.
    """
    built = _surface(picks)
    if isinstance(built, Refusal):
        return built
    fit, placed, excluded = built

    flags = ["order_1_trend_surface"]
    if excluded:
        flags.append("excluded_unresolved_datum")
    if fit["n"] == MIN_PLANE_PICKS:
        flags.append("one_degree_of_freedom")

    predicted = None
    if target_x_ft is not None and target_y_ft is not None:
        predicted = (fit["a"] * float(target_x_ft)
                     + fit["b"] * float(target_y_ft) + fit["c"])

    inputs = {
        "formation": formation or None,
        "plane": {"a_ft_per_ft_east": fit["a"], "b_ft_per_ft_north": fit["b"],
                  "c_ft_ss": fit["c"]},
        "dip_azimuth_deg": fit["dip_azimuth_deg"],
        "dip_ft_per_mile": fit["dip_ft_per_mile"],
        "rmse_ft": fit["rmse_ft"],
        "r2": fit["r2"],
        "residuals_ft": fit["residuals_ft"],
        "wells_used": [p["well"] for p in placed],
        "target": (None if predicted is None
                   else {"x_ft": float(target_x_ft), "y_ft": float(target_y_ft),
                         "predicted_sstvd_ft": predicted}),
    }
    inputs.update(_population_inputs(placed, excluded))

    return Quantity(
        fit["dip_deg"],
        "deg",
        "true dip of the least-squares plane through the subsea picks; the "
        "method is wermund#3's trend surface at order 1 ('the sum of the squares "
        "of all points is best fitted to a curved surface'), listed as Least "
        "squares among tearpock#16's surface estimators",
        WERMUND_TREND_SURFACE,
        inputs=inputs,
        assumptions={
            "depth_basis": "SSTVD, positive upward, sea level zero",
            "depth_reference": next((p["depth_reference"] for p in placed
                                     if p["depth_reference"]), None),
            "coordinates": geometry.CONVENTIONS["coordinates"],
            "dip_azimuth": geometry.CONVENTIONS["dip_azimuth"],
            "surface_order": 1,
            "min_picks": MIN_PLANE_PICKS,
            "collinearity_rule": TEARPOCK_GRIDDING,
            "flag_notes": {f: _FLAG_NOTES[f] for f in flags},
        },
        flags=tuple(flags),
    )


# --------------------------------------------------------------------------- #
# 6. offset_consistency
# --------------------------------------------------------------------------- #


def offset_consistency(picks: Sequence[Mapping[str, Any]],
                       *,
                       tolerance_ft: float | None = None,
                       formation: str = "") -> Range | Refusal:
    """Which offsets' picks the fitted surface cannot honor, and by how much.

    Fits the same surface `structure_map` does and returns the residual band,
    with every well's residual in `members` and the offenders in
    `inputs.inconsistent_wells`. `wermund#3`: values above the best fitted
    surface are positive residuals, below it negative.

    `tolerance_ft` is required and has no default, because the corpus states no
    number. What `tearpock#16` does state is the RULE: a surface need not honor
    every point, and the miss is acceptable where "the calculated value and the
    observed value at a data point location differ by an amount that is within
    the accuracy of the data". Only the caller knows that accuracy, so a default
    here would invent the verdict rather than compute it.

    A residual well outside that accuracy is usually a datum error and not
    geology: real relief is IN the surface and leaves no residual behind, while a
    KB read as GL displaces one well and nothing else.
    """
    if tolerance_ft is None:
        return Refusal(
            reason=(
                "tolerance_ft was not supplied. tearpock#16 states that a fitted "
                "surface need not honor every control point and that the miss is "
                "acceptable where the calculated and observed values 'differ by "
                "an amount that is within the accuracy of the data', but no "
                "corpus source states what that accuracy is for a formation "
                "pick. Defaulting it would decide which offsets are wrong on a "
                "number nothing published"
            ),
            needed=("tolerance_ft: the accuracy of a pick in this area, in feet "
                    "(pick repeatability plus the elevation uncertainty on the "
                    "depth reference)",),
            source=TEARPOCK_GRIDDING,
        )
    tolerance = abs(float(tolerance_ft))
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError(f"tolerance_ft must be a positive finite number, got {tolerance_ft!r}")

    built = _surface(picks)
    if isinstance(built, Refusal):
        return built
    fit, placed, excluded = built

    residuals = fit["residuals_ft"]
    inconsistent = sorted(
        ({"well": w, "residual_ft": r, "direction": "high" if r > 0 else "low"}
         for w, r in residuals.items() if abs(r) > tolerance),
        key=lambda row: -abs(row["residual_ft"]),
    )

    flags = ["order_1_trend_surface"]
    if excluded:
        flags.append("excluded_unresolved_datum")
    if fit["n"] == MIN_PLANE_PICKS:
        flags.append("one_degree_of_freedom")
    if inconsistent:
        flags.append("residual_exceeds_tolerance")

    inputs = {
        "formation": formation or None,
        "tolerance_ft": tolerance,
        "inconsistent_wells": inconsistent,
        "consistent_wells": sorted(w for w, r in residuals.items() if abs(r) <= tolerance),
        "rmse_ft": fit["rmse_ft"],
        "r2": fit["r2"],
        "dip_deg": fit["dip_deg"],
        "dip_azimuth_deg": fit["dip_azimuth_deg"],
    }
    inputs.update(_population_inputs(placed, excluded))

    values = sorted(residuals.values())
    return Range(
        low=values[0],
        high=values[-1],
        unit="ft",
        method=("residual of each pick from the least-squares plane through all "
                "of them, observed minus calculated (wermund#3: above the fitted "
                "surface positive, below negative); flagged against the caller's "
                "declared pick accuracy per tearpock#16"),
        source=WERMUND_TREND_SURFACE,
        members=dict(residuals),
        inputs=inputs,
        assumptions={
            "sign": "positive means the pick sits ABOVE the fitted surface",
            "tolerance_status": "CALLER - no corpus source states a pick accuracy",
            "tolerance_rule": TEARPOCK_GRIDDING,
            "likely_cause": ("a residual beyond pick accuracy is usually a datum "
                             "error: run datum_reconcile (#16) on the flagged "
                             "wells before reinterpreting the structure"),
            "surface_order": 1,
            "flag_notes": {f: _FLAG_NOTES[f] for f in flags},
        },
        flags=tuple(flags),
    )
