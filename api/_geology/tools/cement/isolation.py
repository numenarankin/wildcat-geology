"""#104 isolation_length_check - Pilkington's minimum cemented length.

Merge target: `tools/cement.py`. This SUPERSEDES the scalar-only
`isolation_length_check` already there and adds three helpers that
`behind_pipe_isolation_check` (#107) is specified to reuse rather than re-derive:
`pilkington_required_length_ft`, `sustained_bi_runs` and `gap_scan`. #107 needs
the same threshold applied between the perforations and the nearest water zone,
so it differs from this tool only in which window it scans - it should import
these, not copy the table.

`tool-verification.md:82` claims there is "no minimum-length or BI threshold
anywhere". That row is stale: the rule is plain text in the source markdown
(html2text preserved it - only the BI *equations* were images), and the catalog
re-sourced it. Verified directly at
`knowledge-base/13-cement-integrity/drillingmanual-cement-bond-log.md:12-16`.

The source gives TWO casing sizes and ONE bond index. No line is fitted through
them. Interpolating or extrapolating is an assumption the caller declares, and
the result then says so on its own face.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

from ..result import Quantity, Refusal

DRILLINGMANUAL = "13-cement-integrity/drillingmanual-cement-bond-log"
PILKINGTON_ANCHOR = "13-cement-integrity/drillingmanual-cement-bond-log#0"

# ---------------------------------------------------------------------------
# The rule, as published. Pilkington 1992 (SPE-20314-PA) at second hand, via
# `drillingmanual-cement-bond-log.md:12-16`:
#
#   "Pilkington reported the amount of footage required for vertical isolation
#    was
#      * 5 ft of cement of 80% bond index for a 5 in. OD casing and
#      * 15 ft of 80% bond index for 9-5/8 in. OD casing.
#      * The height values for a 60% bond index will be slightly higher."
#
# That is the whole rule. Two points, one bond index, one qualitative remark.
# ---------------------------------------------------------------------------
PILKINGTON_BI_BASIS = 0.80

PILKINGTON_REQUIRED_FT_AT_80PCT: dict[float, float] = {
    5.0: 5.0,      # 5 in. OD casing   -> 5 ft of 80% BI
    9.625: 15.0,   # 9-5/8 in. OD      -> 15 ft of 80% BI
}

# The source's only statement about any other bond index. Not a number, and it
# is not turned into one anywhere in this module.
PILKINGTON_60PCT_NOTE = (
    "the source says only that 'the height values for a 60% bond index will be "
    "slightly higher' - it publishes no footage for any bond index but 80%"
)

_OD_TOL_IN = 1e-6      # float-equality tolerance on the published casing sizes
_DEPTH_NOISE_FT = 1e-3  # float wobble in LAS depth arrays; not a domain threshold


@dataclass(frozen=True)
class BiRun:
    """One continuous interval over which bond index held at or above threshold.

    `length_ft` is base - top: the span between the first and last qualifying
    SAMPLES. Ten samples on a 1 ft step span 9 ft, not 10. This under-reports
    bonded footage by up to one sample interval, deliberately - for an isolation
    test, under-crediting the cement is the safe direction.
    """

    top_ft: float
    base_ft: float
    length_ft: float
    n_samples: int


# ---------------------------------------------------------------------------
# Piece 1: the rule itself. casing OD in, required footage out.
# ---------------------------------------------------------------------------
def pilkington_required_length_ft(
    casing_od_in: float | None,
    *,
    bi_threshold: float = PILKINGTON_BI_BASIS,
    allow_interpolation: bool = False,
    allow_extrapolation: bool = False,
) -> Quantity | Refusal:
    """Footage of sustained bond index required for vertical isolation.

    Exact on the two published points. Between them, or past them, it refuses
    unless the caller declares the assumption - and then flags the answer as
    assumed rather than published.
    """
    if bi_threshold is None or not (0.0 < float(bi_threshold) <= 1.0):
        raise ValueError("bi_threshold must be a fraction in (0, 1]")
    bi_threshold = float(bi_threshold)

    if casing_od_in is None:
        return Refusal(
            reason="casing OD is required and has no default: the published "
                   "requirement triples from 5 ft to 15 ft between 5 in. and "
                   "9-5/8 in. casing, so a default would be a guess on a factor of three",
            needed=("casing outside diameter, in inches",),
            source=PILKINGTON_ANCHOR,
        )
    casing_od_in = float(casing_od_in)
    if casing_od_in <= 0 or not math.isfinite(casing_od_in):
        raise ValueError("casing_od_in must be a positive, finite diameter in inches")

    if abs(bi_threshold - PILKINGTON_BI_BASIS) > 1e-9:
        detail = PILKINGTON_60PCT_NOTE if abs(bi_threshold - 0.60) <= 1e-9 else (
            "the source publishes footage at an 80% bond index only"
        )
        return Refusal(
            reason=f"no published footage at a bond index of {bi_threshold:.2f}: {detail}",
            needed=(f"a footage requirement at BI {bi_threshold:.2f} - "
                    "Pilkington 1992 (SPE-20314-PA) itself, which the corpus cites but does not hold",),
            source=PILKINGTON_ANCHOR,
        )

    published = sorted(PILKINGTON_REQUIRED_FT_AT_80PCT)
    lo_od, hi_od = published[0], published[-1]

    for od, required_ft in PILKINGTON_REQUIRED_FT_AT_80PCT.items():
        if abs(casing_od_in - od) <= _OD_TOL_IN:
            return Quantity(
                required_ft, "ft", "Pilkington isolation length (published point)",
                PILKINGTON_ANCHOR,
                inputs={"casing_od_in": od, "bi_threshold": PILKINGTON_BI_BASIS},
            )

    inside = lo_od < casing_od_in < hi_od
    mode = "interpolated" if inside else "extrapolated"
    permitted = allow_interpolation if inside else allow_extrapolation
    if not permitted:
        where = (f"between the published {lo_od} in. and {hi_od} in."
                 if inside else
                 f"outside the published {lo_od} in. - {hi_od} in.")
        return Refusal(
            reason=f"{casing_od_in} in. casing is {where}; the source gives two casing "
                   f"sizes and nothing between or beyond them. Fitting a line through two "
                   f"points would look like knowledge and is not.",
            needed=(f"allow_{'interpolation' if inside else 'extrapolation'}=True to declare "
                    "the assumption and own it, or a source covering this casing size",),
            source=PILKINGTON_ANCHOR,
        )

    # Caller declared the assumption. Straight line between the only two points
    # there are - this is the caller's assumption, not the published rule, and
    # every returned value says so.
    lo_ft = PILKINGTON_REQUIRED_FT_AT_80PCT[lo_od]
    hi_ft = PILKINGTON_REQUIRED_FT_AT_80PCT[hi_od]
    slope = (hi_ft - lo_ft) / (hi_od - lo_od)
    required_ft = lo_ft + (casing_od_in - lo_od) * slope

    if required_ft <= 0:
        return Refusal(
            reason=f"extrapolating to {casing_od_in} in. casing gives {required_ft:.2f} ft, "
                   "which is not a length; the two published points do not reach this size",
            needed=("a source covering casing below "
                    f"{lo_od - lo_ft / slope:.2f} in.",),
            source=PILKINGTON_ANCHOR,
        )

    return Quantity(
        required_ft, "ft",
        f"Pilkington isolation length ({mode}, caller-declared)",
        PILKINGTON_ANCHOR,
        inputs={"casing_od_in": casing_od_in, "bi_threshold": PILKINGTON_BI_BASIS},
        assumptions={
            "casing_od": f"{mode} from the two published points "
                         f"({lo_od} in. -> {lo_ft} ft, {hi_od} in. -> {hi_ft} ft); "
                         "caller-declared, not published",
            "shape": "straight line between the two points; two points cannot establish one",
        },
        flags=(f"required footage {mode} for {casing_od_in} in. casing - assumption, not source",),
    )


# ---------------------------------------------------------------------------
# Piece 2: sampling continuity. A run through unmeasured hole is not a run.
# ---------------------------------------------------------------------------
def gap_scan(depth_ft: Sequence[float],
             max_gap_ft: float | None = None) -> list[tuple[float, float]]:
    """Depth steps larger than one sample interval, as (from, to) pairs.

    `max_gap_ft` defaults to the median step of the array: one missing sample is
    a gap. That default is measured from the data, not chosen - there is no
    domain threshold here to invent. `_DEPTH_NOISE_FT` absorbs float wobble in
    LAS depth arrays and is far below any real sampling interval.
    """
    if len(depth_ft) < 2:
        return []
    steps = [depth_ft[i + 1] - depth_ft[i] for i in range(len(depth_ft) - 1)]
    if max_gap_ft is None:
        ordered = sorted(steps)
        mid = len(ordered) // 2
        max_gap_ft = ordered[mid] if len(ordered) % 2 else 0.5 * (ordered[mid - 1] + ordered[mid])
    return [(depth_ft[i], depth_ft[i + 1])
            for i, s in enumerate(steps) if s > max_gap_ft + _DEPTH_NOISE_FT]


# ---------------------------------------------------------------------------
# Piece 3: the sustained-run scanner. The core of the tool.
# ---------------------------------------------------------------------------
def sustained_bi_runs(depth_ft: Sequence[float],
                      bond_index: Sequence[float],
                      bi_threshold: float = PILKINGTON_BI_BASIS) -> list[BiRun]:
    """Every continuous run over which BI >= threshold at EVERY sample.

    Not an average. A 20 ft zone averaging 0.80 can be 10 ft at 1.00 and 10 ft
    at 0.60, which is a channel; averaging lets it through and this does not.
    One sample below threshold ends the run.
    """
    runs: list[BiRun] = []
    start = None
    for i, bi in enumerate(bond_index):
        ok = bi is not None and isinstance(bi, (int, float)) and \
            not (isinstance(bi, float) and math.isnan(bi)) and bi >= bi_threshold
        if ok and start is None:
            start = i
        elif not ok and start is not None:
            runs.append(_make_run(depth_ft, start, i - 1))
            start = None
    if start is not None:
        runs.append(_make_run(depth_ft, start, len(bond_index) - 1))
    return runs


def _make_run(depth_ft: Sequence[float], i0: int, i1: int) -> BiRun:
    top, base = depth_ft[i0], depth_ft[i1]
    return BiRun(top_ft=top, base_ft=base, length_ft=base - top, n_samples=i1 - i0 + 1)


# ---------------------------------------------------------------------------
# The tool.
# ---------------------------------------------------------------------------
def isolation_length_check(
    casing_od_in: float | None,
    bond_index: Sequence[float] | float | None = None,
    depth_ft: Sequence[float] | float | None = None,
    *,
    bi_threshold: float = PILKINGTON_BI_BASIS,
    zone_top_ft: float | None = None,
    zone_base_ft: float | None = None,
    max_gap_ft: float | None = None,
    allow_interpolation: bool = False,
    allow_extrapolation: bool = False,
    cement_sheath_thickness_in: float | None = None,
) -> Quantity | Refusal:
    """Is there enough continuously well-bonded cement to call the zone isolated?

    Curve form (preferred):
        isolation_length_check(9.625, bi_curve, depths)
    Scalar form (a run the caller already measured - #107 will use this):
        isolation_length_check(9.625, 0.85, 20.0)   # 20 ft SUSTAINED at 0.85

    The scalar form asserts a sustained run; it is not a place to pass an
    interval average, and the result records that the tool did not scan.

    "Not isolated" comes back as a Quantity of 0.0, not a Refusal. The source
    supported the question completely - we looked up a published footage and
    measured the run - and "there is a channel" must not be indistinguishable
    from "we cannot tell".
    """
    required = pilkington_required_length_ft(
        casing_od_in,
        bi_threshold=bi_threshold,
        allow_interpolation=allow_interpolation,
        allow_extrapolation=allow_extrapolation,
    )
    if isinstance(required, Refusal):
        return required

    scalar_form = isinstance(bond_index, (int, float)) and not isinstance(bond_index, bool)
    if scalar_form:
        result = _scalar_verdict(bond_index, depth_ft, bi_threshold)
    else:
        result = _scan_verdict(bond_index, depth_ft, bi_threshold,
                               zone_top_ft, zone_base_ft, max_gap_ft)
    if isinstance(result, Refusal):
        return result
    run_ft, extra_inputs, assumptions = result

    isolated = run_ft >= required.value
    flags: list[str] = list(required.flags)
    if not isolated:
        flags.append(
            f"longest sustained run {run_ft:.1f} ft is short of the "
            f"{required.value:.1f} ft required for {casing_od_in} in. casing"
        )
    if cement_sheath_thickness_in is not None and cement_sheath_thickness_in < 0.75:
        flags.append(
            f"cement sheath {cement_sheath_thickness_in} in. is below the 3/4 in. the source "
            "says is needed for complete attenuation - the bond index feeding this check "
            "may not be a correct cement evaluation"
        )

    return Quantity(
        1.0 if isolated else 0.0, "bool",
        "Pilkington isolation length, sustained-run basis",
        PILKINGTON_ANCHOR,
        inputs={
            "casing_od_in": casing_od_in,
            "bi_threshold": bi_threshold,
            "required_ft": required.value,
            "longest_run_ft": run_ft,
            **extra_inputs,
        },
        assumptions={
            "basis": "continuous sustained bond index, never an interval average - "
                     "a 20 ft zone averaging 0.80 can be 10 ft at 1.00 and 10 ft at 0.60",
            **dict(required.assumptions),
            **assumptions,
        },
        flags=tuple(flags),
    )


def _scalar_verdict(sustained_bi: float, length_ft: Any,
                    bi_threshold: float) -> tuple[float, dict, dict] | Refusal:
    """Caller asserts: 'I have L ft over which BI held at or above X.'"""
    if length_ft is None or isinstance(length_ft, (list, tuple)):
        raise ValueError("scalar bond_index requires the sustained length in ft as depth_ft")
    length_ft = float(length_ft)
    if length_ft < 0 or not math.isfinite(length_ft):
        raise ValueError("sustained length must be a non-negative, finite number of feet")
    if sustained_bi > 2.0:
        raise ValueError("bond index is a fraction; a value above 2 suggests percent was passed")
    if sustained_bi < bi_threshold:
        return Refusal(
            reason=f"asserted sustained bond index {sustained_bi:.2f} is below the "
                   f"{bi_threshold:.2f} the rule is stated at; {PILKINGTON_60PCT_NOTE}",
            needed=("a footage requirement at this bond index",),
            source=PILKINGTON_ANCHOR,
        )
    return length_ft, {"sustained_bi": sustained_bi}, {
        "sustained_run": "caller-asserted; the tool did not scan a curve",
    }


def _scan_verdict(bond_index: Any, depth_ft: Any, bi_threshold: float,
                  zone_top_ft: float | None, zone_base_ft: float | None,
                  max_gap_ft: float | None) -> tuple[float, dict, dict] | Refusal:
    if bond_index is None or depth_ft is None:
        return Refusal(
            reason="no bond-index curve supplied; the check needs a bond index over depth, "
                   "or an explicitly asserted sustained run",
            needed=("a bond-index curve and its depth array",),
            source=PILKINGTON_ANCHOR,
        )
    bond_index = list(bond_index)
    depth_ft = list(depth_ft)
    if len(bond_index) != len(depth_ft):
        raise ValueError("bond_index and depth_ft must be the same length")
    if any(bi is not None and isinstance(bi, (int, float)) and bi > 2.0 for bi in bond_index):
        raise ValueError("bond index is a fraction; values above 2 suggest percent was passed")

    if len(depth_ft) >= 2 and depth_ft[0] > depth_ft[-1]:
        depth_ft, bond_index = depth_ft[::-1], bond_index[::-1]
    if any(depth_ft[i + 1] <= depth_ft[i] for i in range(len(depth_ft) - 1)):
        return Refusal(
            reason="depth array is not monotonic; a continuous run cannot be measured "
                   "against depths that reverse or repeat",
            needed=("a monotonic depth array (see null_scrub / depth_resample)",),
            source=PILKINGTON_ANCHOR,
        )

    top = zone_top_ft if zone_top_ft is not None else -math.inf
    base = zone_base_ft if zone_base_ft is not None else math.inf
    window = [i for i, d in enumerate(depth_ft) if top <= d <= base]
    if len(window) < 2:
        return Refusal(
            reason=f"the scanned window holds {len(window)} bond-index sample(s); "
                   "a sustained length cannot be measured",
            needed=("bond-index samples spanning the interval of interest",),
            source=PILKINGTON_ANCHOR,
        )
    w_depth = [depth_ft[i] for i in window]
    w_bi = [bond_index[i] for i in window]

    missing = [w_depth[i] for i, bi in enumerate(w_bi)
               if bi is None or not isinstance(bi, (int, float))
               or (isinstance(bi, float) and math.isnan(bi))]
    if missing:
        return Refusal(
            reason=f"the bond-index curve has {len(missing)} null sample(s) in the scanned "
                   f"window (first at {missing[0]:.1f} ft); continuous isolation cannot be "
                   "certified through hole that was not measured",
            needed=("a gap-free bond-index curve over the interval, "
                    "or a narrower zone_top_ft/zone_base_ft window",),
            source=PILKINGTON_ANCHOR,
        )

    gaps = gap_scan(w_depth, max_gap_ft)
    if gaps:
        return Refusal(
            reason=f"the depth sampling has {len(gaps)} gap(s) in the scanned window "
                   f"(first {gaps[0][0]:.1f} -> {gaps[0][1]:.1f} ft); continuous isolation "
                   "cannot be certified through hole that was not measured",
            needed=("continuous sampling over the interval, a wider max_gap_ft if the "
                    "sampling is legitimately coarse, or a narrower window",),
            source=PILKINGTON_ANCHOR,
        )

    runs = sustained_bi_runs(w_depth, w_bi, bi_threshold)
    best = max(runs, key=lambda r: r.length_ft) if runs else None
    run_ft = best.length_ft if best else 0.0
    mean_bi = sum(w_bi) / len(w_bi)
    extra = {
        "run_top_ft": best.top_ft if best else None,
        "run_base_ft": best.base_ft if best else None,
        "n_samples": best.n_samples if best else 0,
        "window_top_ft": w_depth[0],
        "window_base_ft": w_depth[-1],
        "window_mean_bi": mean_bi,  # reported so the run can be reconciled against it
    }
    return run_ft, extra, {
        "run_length": "span between the first and last qualifying samples; under-reports "
                      "by up to one sample interval, which is the safe direction here",
        "sustained": "every sample in the run is at or above the threshold; the source "
                     "does not say whether a momentary dip may be tolerated",
    }
