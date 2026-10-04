"""Microannulus versus channel, from a pair of CBL passes at different casing
pressures (#105).

The whole tool is one sentence of PetroWiki: pressuring the casing expands it
against the cement and closes a microannulus, so the casing signal drops on the
second pass; "if only channeling exists, pressuring the casing will not
significantly change the log."

Three decisions in here are not obvious from that sentence.

**The metric is a dimensionless ratio, not an absolute amplitude change.** An
8 mV drop is a diagnosis at one gain and noise at another. The verdict runs on
(A_free - A_pressured)/A_free, which is invariant to the amplitude scale as long
as both passes share it. That is also why `cbl_calibration` (#102) is optional
here rather than required: the free-pipe anchor is needed to judge the source's
"and the log indicates poor bond" precondition, not to compute the comparison.
When it is supplied the ratios are reported; when it is not, a flag says the
precondition went unchecked. It never enters the verdict.

**"Significantly" is a caller input.** The source says "significantly" and stops,
and the only place a number could have lived - Fig. 5 - is an image in every copy
of the document in this corpus. So `min_drop_fraction` is CALLER per the
catalog's "Thresholds the corpus does not supply" convention: no default, refuse
without it, and label it as caller-supplied on the way out.

**Depth alignment is required, not performed.** Two CBL passes are two logging
runs, and Asquith p. 170 says runs "differ slightly in depth-registry of beds".
Comparing them sample-by-sample off-register compares different beds. This tool
demands exact depth agreement unless the caller declares a tolerance, and it
never shifts, stretches or interpolates a curve to make a comparison work -
that is `depth_resample`'s job (#13), upstream, where the caller can see it.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

from ..result import Quantity, Range, Refusal

# --- sources -----------------------------------------------------------------

PETROWIKI = "13-cement-integrity/petrowiki-cement-bond-logs#2"
DRILLINGMANUAL = "13-cement-integrity/drillingmanual-cement-bond-log"
ASQUITH_DEPTH_REGISTRY = (
    "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#64"
)

METHOD = "microannulus discrimination by pressured-vs-unpressured CBL amplitude"

# --- constants, each with the sentence it came from ---------------------------

# drillingmanual-cement-bond-log.md:71 - "The logs are run without wellhead
# pressure and with 800-1000 psi wellhead pressure to identify microcannulas".
# Advisory, not a validity limit: the same document's field example
# (line 79) ran zero and 2000 psi and was a valid microannulus call. Outside
# this band the tool flags; it never refuses on magnitude.
PRACTICE_WELLHEAD_PRESSURE_PSI = (800.0, 1000.0)

# petrowiki-cement-bond-logs#2 - "Formations with transit times less than casing
# (57 microsec/ft) can cause problems when interpreting the amplitude curves
# because the formation signal can arrive in the amplitude gate."
CASING_TRANSIT_TIME_US_FT = 57.0

# drillingmanual-cement-bond-log.md:59 - "a cement sheath less than 3/4 in. will
# not provide complete attenuation for the acoustic signal and hence will not
# give correct cement evaluation". Corroborated by Table 3C.8, "Cement
# variability | Thickness (< 0.75 in. (2 cm)), voids (foam)"
# (onepetro-cement-bond-logs-print.md:209).
MIN_CEMENT_SHEATH_IN = 0.75

# petrowiki-cement-bond-logs#2 - "foam cements, which intentionally create void
# spaces in the cured cement, can be misinterpreted as partial bond if normal
# cement is assumed." The two-class test is unsound for these.
# Keys are normalised (lower-cased, spaces and hyphens -> underscore) before
# lookup, the way vdl_classify (#106) normalises its CEMENT_TYPES table, so
# "Class A", "class-a" and "class_a" are one key. Anything in neither tuple is
# refused: "information on the type of cement used is essential", and the
# failure the source names is a foam job "misinterpreted as partial bond if
# normal cement is assumed" - which is what defaulting an unknown label to
# conventional does.
INVALID_CEMENT_TYPES = ("foam", "foamed", "foam_cement", "lightweight", "light_weight")
VALID_CEMENT_TYPES = ("conventional", "neat", "class_a", "class_c", "class_g",
                      "class_h", "portland", "standard")

# Floating-point slack on a depth comparison. Not an alignment tolerance - the
# alignment tolerance is `depth_tolerance_ft` and defaults to zero.
_DEPTH_EPS_FT = 1e-6

VERDICT_MICROANNULUS = "microannulus"
VERDICT_CHANNEL = "channel_or_partial_bond"


# --- helpers -----------------------------------------------------------------

def _as_pair(depth: Sequence[float] | None,
             amplitude: Sequence[float] | None,
             label: str) -> tuple[list[float], list[float]] | None:
    """Return (depths, amplitudes) or None when the pass is absent."""
    if depth is None or amplitude is None:
        return None
    d = [float(x) for x in depth]
    a = [float(x) for x in amplitude]
    if len(d) != len(a):
        raise ValueError(
            f"{label}: depth and amplitude arrays differ in length "
            f"({len(d)} vs {len(a)})")
    if not d:
        return None
    return d, a


def _monotonic(depths: Sequence[float]) -> bool:
    return all(b > a for a, b in zip(depths, depths[1:]))


def _mean(xs: Sequence[float]) -> float:
    return math.fsum(xs) / len(xs)


# --- the tool ----------------------------------------------------------------

def microannulus_discriminate(
    free_depth_ft: Sequence[float] | None,
    free_amplitude_mv: Sequence[float] | None,
    pressured_depth_ft: Sequence[float] | None = None,
    pressured_amplitude_mv: Sequence[float] | None = None,
    *,
    applied_pressure_psi: float | None = None,
    min_drop_fraction: float | None = None,
    cement_type: str | None = None,
    free_pass_pressure_psi: float = 0.0,
    depth_tolerance_ft: float = 0.0,
    interval_ft: tuple[float, float] | None = None,
    free_pipe_amplitude_mv: float | None = None,
    formation_transit_time_us_ft: float | None = None,
    cement_sheath_thickness_in: float | None = None,
    free_tr_spacing_ft: float | None = None,
    pressured_tr_spacing_ft: float | None = None,
) -> Quantity | Refusal:
    """Tell a microannulus from a channel by comparing two CBL passes.

    `13-cement-integrity/petrowiki-cement-bond-logs#2`:

        "If the initial log run was not under pressure and the log indicates
        poor bond, the presence of a microannulus can be evaluated by running a
        second bond log under pressure to see if there is a difference.
        Pressuring the casing improves the acoustic coupling to the formation
        and the casing signal will decrease and the formation signal will become
        more obvious. However, if only channeling exists, pressuring the casing
        will not significantly change the log."

    Returns a `Quantity` whose value is the mean fractional amplitude drop and
    whose `assumptions["verdict"]` is `"microannulus"` or
    `"channel_or_partial_bond"`.

    The negative verdict is deliberately not "channel". Channelling and
    microannulus are sub-cases of the source's *partial bond* class, and a single
    amplitude curve cannot identify channelling on its own. What a null pressure
    response establishes is that the poor bond is *not* a microannulus.
    """
    # --- R1: both passes, or nothing ----------------------------------------
    free = _as_pair(free_depth_ft, free_amplitude_mv, "unpressured pass")
    pressured = _as_pair(pressured_depth_ft, pressured_amplitude_mv,
                         "pressured pass")
    if free is None or pressured is None:
        missing = []
        if free is None:
            missing.append("an unpressured (free) CBL amplitude pass")
        if pressured is None:
            missing.append("a CBL amplitude pass logged with the casing under pressure")
        return Refusal(
            reason=(
                "a microannulus cannot be diagnosed from a single pass. The source's "
                "procedure is to evaluate it 'by running a second bond log under "
                "pressure to see if there is a difference' - with only one pass there "
                "is no difference to measure, and a high amplitude is equally "
                "consistent with a microannulus and with a channel"),
            needed=tuple(missing),
            source=PETROWIKI,
        )

    free_d, free_a = free
    pres_d, pres_a = pressured

    # --- R11/R12: cement type -----------------------------------------------
    if cement_type is None:
        return Refusal(
            reason=("cement type not stated. The source: 'When conducting a cement "
                    "evaluation, information on the type of cement used is essential'"),
            needed=("the cement type used on this job (e.g. 'conventional', 'foam')",),
            source=PETROWIKI,
        )
    ct = str(cement_type).strip().lower().replace(" ", "_").replace("-", "_")
    if ct in INVALID_CEMENT_TYPES:
        return Refusal(
            reason=(
                f"cement type {cement_type!r}: the pressure-pass comparison is a "
                "two-class test and this cement supplies a third cause of high "
                "amplitude. The source: 'foam cements, which intentionally create void "
                "spaces in the cured cement, can be misinterpreted as partial bond if "
                "normal cement is assumed'"),
            needed=("a cement evaluation method valid for foam or lightweight cement "
                    "(ultrasonic / radial), not a CBL amplitude comparison",),
            source=PETROWIKI,
        )
    if ct not in VALID_CEMENT_TYPES:
        return Refusal(
            reason=(
                f"cement type {cement_type!r} is not a system this comparison is known "
                "to be valid for. The source: 'When conducting a cement evaluation, "
                "information on the type of cement used is essential' - and the failure "
                "it names is a foam job 'misinterpreted as partial bond if normal cement "
                "is assumed', which is exactly what treating an unrecognised label as "
                "conventional would do"),
            needed=("cement_type, one of " + ", ".join(sorted(VALID_CEMENT_TYPES))
                    + " (foam and lightweight systems are refused separately)",),
            source=PETROWIKI,
        )

    # --- R13: fast formation -------------------------------------------------
    if (formation_transit_time_us_ft is not None
            and formation_transit_time_us_ft < CASING_TRANSIT_TIME_US_FT):
        return Refusal(
            reason=(
                f"formation transit time {formation_transit_time_us_ft:g} us/ft is below "
                f"the casing's {CASING_TRANSIT_TIME_US_FT:g} us/ft. The source: "
                "'Formations with transit times less than casing (57 microsec/ft) can "
                "cause problems when interpreting the amplitude curves because the "
                "formation signal can arrive in the amplitude gate'. Both passes are "
                "contaminated, so their difference is not a bond measurement"),
            needed=("a VDL check that the formation arrival is outside the amplitude "
                    "gate, or a radial/ultrasonic evaluation instead",),
            source=PETROWIKI,
        )

    # --- R14: thin sheath ----------------------------------------------------
    if (cement_sheath_thickness_in is not None
            and cement_sheath_thickness_in < MIN_CEMENT_SHEATH_IN):
        return Refusal(
            reason=(
                f"cement sheath {cement_sheath_thickness_in:g} in. is below "
                f"{MIN_CEMENT_SHEATH_IN:g} in. The source: 'a cement sheath less than "
                "3/4 in. will not provide complete attenuation for the acoustic signal "
                "and hence will not give correct cement evaluation' - neither pass is a "
                "valid bond reading, so neither is their difference"),
            needed=("an evaluation method valid for a thin cement sheath",),
            source=DRILLINGMANUAL,
        )

    # --- R2/R3/R4: the pressure itself --------------------------------------
    if applied_pressure_psi is None:
        return Refusal(
            reason=("applied casing pressure not stated. The verdict rests entirely on "
                    "the second pass having been logged 'with the casing under "
                    "pressure'; without the magnitude there is no evidence the casing "
                    "was ever expanded against the cement"),
            needed=("the wellhead pressure applied to the casing during the second pass, "
                    "in psi",),
            source=PETROWIKI,
        )
    if applied_pressure_psi <= 0:
        return Refusal(
            reason=(f"applied casing pressure is {applied_pressure_psi:g} psi; a pass at "
                    "zero or negative pressure is not a pressured pass. The procedure "
                    "requires pressure 'to expand the casing against the cement, thereby "
                    "decreasing any microannulus that might exist'"),
            needed=("a second pass logged under positive casing pressure",),
            source=PETROWIKI,
        )
    if free_pass_pressure_psi != 0.0:
        return Refusal(
            reason=(
                f"the reference pass was logged at {free_pass_pressure_psi:g} psi. The "
                "source states the procedure for an unpressured first run - 'If the "
                "initial log run was not under pressure and the log indicates poor "
                "bond' - because a microannulus already closed on the reference pass "
                "leaves nothing for the second pass to close, and the resulting null "
                "difference reads as a channel"),
            needed=("an unpressured reference pass",),
            source=PETROWIKI,
        )

    # --- R5/R6: the caller's threshold ---------------------------------------
    if min_drop_fraction is None:
        return Refusal(
            reason=(
                "no discrimination threshold. The source quantifies nothing: it says "
                "only that a channel 'will not significantly change the log' and that a "
                "microannulus is evaluated by looking 'to see if there is a difference'. "
                "The one place a magnitude could have been read - Fig. 5 - is an image "
                "in every copy of this document in the corpus. This threshold is "
                "CALLER-supplied by the catalog's convention; the tool will not pick it"),
            needed=("min_drop_fraction: the fractional amplitude drop the caller counts "
                    "as a significant change, 0 < f < 1",),
            source=PETROWIKI,
        )
    if not (0.0 < min_drop_fraction < 1.0):
        return Refusal(
            reason=(f"min_drop_fraction {min_drop_fraction:g} is outside (0, 1); a "
                    "fractional drop from the unpressured amplitude cannot equal or "
                    "exceed 1 (that is the amplitude vanishing entirely) nor be "
                    "non-positive (that is no drop at all)"),
            needed=("a threshold strictly between 0 and 1",),
            source=PETROWIKI,
        )

    # --- R15: same measurement on both passes --------------------------------
    if (free_tr_spacing_ft is not None and pressured_tr_spacing_ft is not None
            and free_tr_spacing_ft != pressured_tr_spacing_ft):
        return Refusal(
            reason=(f"the passes were run at different transmitter-receiver spacings "
                    f"({free_tr_spacing_ft:g} ft vs {pressured_tr_spacing_ft:g} ft). "
                    "Amplitude at 3 ft and at 5 ft are different measurements, so their "
                    "ratio is not a pressure response"),
            needed=("two passes recorded at the same TR spacing",),
            source=PETROWIKI,
        )

    # --- R9: usable depth indices -------------------------------------------
    for label, d in (("unpressured", free_d), ("pressured", pres_d)):
        if not _monotonic(d):
            return Refusal(
                reason=(f"the {label} pass depth index is not strictly increasing; the "
                        "two passes cannot be put on a common depth register"),
                needed=(f"a monotonically increasing depth index on the {label} pass",),
                source=ASQUITH_DEPTH_REGISTRY,
            )

    # --- R7/R17: overlap window ---------------------------------------------
    lo = max(free_d[0], pres_d[0])
    hi = min(free_d[-1], pres_d[-1])
    if hi < lo:
        return Refusal(
            reason=(f"the passes do not overlap in depth: unpressured covers "
                    f"{free_d[0]:.2f}-{free_d[-1]:.2f} ft, pressured covers "
                    f"{pres_d[0]:.2f}-{pres_d[-1]:.2f} ft"),
            needed=("two passes covering a common depth interval",),
            source=PETROWIKI,
        )
    if interval_ft is not None:
        top, base = float(interval_ft[0]), float(interval_ft[1])
        if base < top:
            raise ValueError("interval_ft must be (top, base) with base >= top")
        lo, hi = max(lo, top), min(hi, base)
        if hi < lo:
            return Refusal(
                reason=(f"the requested interval {top:.2f}-{base:.2f} ft is disjoint "
                        "from the depth range the two passes share"),
                needed=("an interval inside the overlap of the two passes",),
                source=PETROWIKI,
            )

    tol = max(float(depth_tolerance_ft), _DEPTH_EPS_FT)
    win_free = [(d, a) for d, a in zip(free_d, free_a) if lo - tol <= d <= hi + tol]
    win_pres = [(d, a) for d, a in zip(pres_d, pres_a) if lo - tol <= d <= hi + tol]

    # --- R8: alignment -------------------------------------------------------
    if len(win_free) != len(win_pres):
        return Refusal(
            reason=(
                f"the passes are not depth-aligned over {lo:.2f}-{hi:.2f} ft: "
                f"{len(win_free)} unpressured samples against {len(win_pres)} pressured. "
                "Asquith p. 170: 'because a suite of logs generally requires more than "
                "one logging run out of the borehole, some logs differ slightly in "
                "depth-registry of beds'. Compared sample-by-sample off-register these "
                "are two different beds"),
            needed=("both passes resampled onto a common depth index (depth_resample, "
                    "#13), or an explicit depth_tolerance_ft the caller owns",),
            source=ASQUITH_DEPTH_REGISTRY,
        )
    if not win_free:
        return Refusal(
            reason=(f"no samples fall in the compared window {lo:.2f}-{hi:.2f} ft"),
            needed=("passes with samples inside the compared interval",),
            source=PETROWIKI,
        )
    for (df, _), (dp, _) in zip(win_free, win_pres):
        if abs(df - dp) > tol:
            return Refusal(
                reason=(
                    f"the passes are not depth-aligned: unpressured sample at "
                    f"{df:.3f} ft pairs with a pressured sample at {dp:.3f} ft, "
                    f"{abs(df - dp):.3f} ft away, against a tolerance of "
                    f"{depth_tolerance_ft:g} ft. Asquith p. 170: logging runs 'differ "
                    "slightly in depth-registry of beds'. This tool will not shift, "
                    "stretch or interpolate a pass to force a comparison"),
                needed=("both passes on a common depth index (depth_resample, #13), or "
                        "a depth_tolerance_ft the caller declares and owns",),
                source=ASQUITH_DEPTH_REGISTRY,
            )

    # --- R10: usable amplitudes ---------------------------------------------
    for label, win in (("unpressured", win_free), ("pressured", win_pres)):
        for d, a in win:
            if not math.isfinite(a) or a <= 0.0:
                return Refusal(
                    reason=(f"the {label} pass carries a null or non-positive amplitude "
                            f"({a!r}) at {d:.2f} ft inside the compared window; an "
                            "amplitude ratio is undefined there"),
                    needed=(f"nulls scrubbed from the {label} amplitude curve "
                            "(null_scrub, #12) or a compared interval that excludes them",),
                    source=PETROWIKI,
                )

    # --- the comparison ------------------------------------------------------
    a_free = [a for _, a in win_free]
    a_pres = [a for _, a in win_pres]
    n = len(a_free)
    mean_free = _mean(a_free)
    mean_pres = _mean(a_pres)
    drop_fraction = (mean_free - mean_pres) / mean_free

    per_sample_drop = [(f - p) / f for f, p in zip(a_free, a_pres)]
    k_over = sum(1 for x in per_sample_drop if x >= min_drop_fraction)

    # --- R16: a rise is backwards -------------------------------------------
    if drop_fraction <= -min_drop_fraction:
        return Refusal(
            reason=(
                f"the pressured pass amplitude ROSE by {abs(drop_fraction) * 100:.1f}% "
                f"({mean_free:.3f} -> {mean_pres:.3f} mV over {lo:.2f}-{hi:.2f} ft), "
                "which is physically backwards. The source: 'Pressuring the casing "
                "improves the acoustic coupling to the formation and the casing signal "
                "will decrease'. Pressure closes gaps; it cannot open new ones. A "
                "material rise is not evidence against a microannulus - it is evidence "
                "the two passes are not comparable: the passes may be swapped, the "
                "depth shift wrong, the gain or amplitude gate changed between runs, or "
                "the 'pressured' pass not actually pressured"),
            needed=("the acquisition checked - pass order, depth registration, tool gain "
                    "and gate settings, and the pressure actually held during the second "
                    "run",),
            source=PETROWIKI,
        )

    verdict = (VERDICT_MICROANNULUS if drop_fraction >= min_drop_fraction
               else VERDICT_CHANNEL)

    # --- flags ---------------------------------------------------------------
    flags: list[str] = [f"verdict={verdict}"]

    p_lo, p_hi = PRACTICE_WELLHEAD_PRESSURE_PSI
    if not (p_lo <= applied_pressure_psi <= p_hi):
        flags.append(
            f"applied pressure {applied_pressure_psi:g} psi is outside the "
            f"{p_lo:g}-{p_hi:g} psi practice range the drilling manual states for this "
            "test; that figure is practice, not a validity limit (its own field example "
            "ran 2000 psi), but a low pressure may not fully close the gap")

    if 0 < k_over < n:
        flags.append(
            f"nonuniform pressure response: {k_over} of {n} samples clear the threshold. "
            "The source: 'When channeling occurs, it is generally localized and "
            "nonuniform; that is, it occurs over relatively short intervals and can "
            "frequently be identified by variations in the amplitude response' - a mixed "
            "response can be a channel inside an otherwise microannulus-affected section")

    if free_pipe_amplitude_mv is None:
        flags.append(
            "the source's precondition 'and the log indicates poor bond' was not "
            "checked: no free-pipe amplitude supplied, so the unpressured amplitude "
            "cannot be placed on the bond scale. Supply cbl_calibration's (#102) "
            "free-pipe anchor to have it reported")

    flags.append(
        "half the source's signature: it also expects 'the formation signal will become "
        "more obvious' on the pressured pass. This tool sees only the amplitude curve; "
        "the formation-arrival half is vdl_classify (#106)")

    flags.append(
        "assumes both passes were recorded by the same tool at the same TR spacing, "
        "amplitude gate and gain; a gain change between runs invalidates the ratio and "
        "is not detectable from depth and amplitude alone")

    # --- result --------------------------------------------------------------
    inputs: dict[str, Any] = {
        "mean_unpressured_amplitude_mv": mean_free,
        "mean_pressured_amplitude_mv": mean_pres,
        "n_compared_samples": n,
        "compared_interval_ft": (win_free[0][0], win_free[-1][0]),
        "applied_pressure_psi": applied_pressure_psi,
        "free_pass_pressure_psi": free_pass_pressure_psi,
        "samples_clearing_threshold": k_over,
        "min_per_sample_drop_fraction": min(per_sample_drop),
        "max_per_sample_drop_fraction": max(per_sample_drop),
    }
    if free_pipe_amplitude_mv is not None:
        if not math.isfinite(free_pipe_amplitude_mv) or free_pipe_amplitude_mv <= 0:
            raise ValueError("free_pipe_amplitude_mv must be a positive amplitude")
        inputs["free_pipe_amplitude_mv"] = free_pipe_amplitude_mv
        inputs["unpressured_fraction_of_free_pipe"] = mean_free / free_pipe_amplitude_mv
        inputs["drop_as_fraction_of_free_pipe"] = (
            (mean_free - mean_pres) / free_pipe_amplitude_mv)
    if free_tr_spacing_ft is not None:
        inputs["tr_spacing_ft"] = free_tr_spacing_ft
    if formation_transit_time_us_ft is not None:
        inputs["formation_transit_time_us_ft"] = formation_transit_time_us_ft
    if cement_sheath_thickness_in is not None:
        inputs["cement_sheath_thickness_in"] = cement_sheath_thickness_in

    return Quantity(
        drop_fraction, "fraction", METHOD, PETROWIKI,
        inputs=inputs,
        assumptions={
            "verdict": verdict,
            "verdict_basis": (
                "mean fractional amplitude drop over the compared interval, "
                "(A_unpressured - A_pressured)/A_unpressured"),
            "min_drop_fraction": min_drop_fraction,
            "threshold_status": "CALLER - the source states no numeric change threshold",
            "cement_type": cement_type,
            "pressure_applied_to": "casing (internal / wellhead), not the annulus",
            "practice_pressure_psi": PRACTICE_WELLHEAD_PRESSURE_PSI,
            "practice_pressure_source": DRILLINGMANUAL,
            "depth_alignment": (
                f"required within {depth_tolerance_ft:g} ft; no shifting or "
                "interpolation performed"),
            "negative_verdict_meaning": (
                "channel_or_partial_bond means 'not a microannulus'. Channelling and "
                "microannulus are sub-cases of the source's partial-bond class and a "
                "single amplitude curve cannot identify channelling on its own"),
            "calibration_role": (
                "cbl_calibration (#102) is optional and reporting-only here; the "
                "verdict runs on a dimensionless ratio and does not use it"),
        },
        flags=tuple(flags),
    )
