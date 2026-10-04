"""Pressure: fluid gradients, compartment tests, Horner extrapolation.

Three catalog tools (#44, #45, #46) whose sources are unusually explicit about
what they do *not* support, so the shape of this module is mostly the shape of
those limits.

**Gradients are sourced; gradient-to-fluid-type is not.** Earlougher's Example
8.1 spells out the density-to-gradient conversion constant by constant, and
Ahmed states the same constant twice more in other units — one number, three
forms, not a disagreement to average. No document in this corpus carries a
gradient-to-fluid discriminator table, so `fluid_type_from_gradient` refuses
without a caller-supplied band table. The catalog's provisional bands are
exported as `PROVISIONAL_FLUID_BANDS`, which a caller must pass explicitly; a
result built from them carries `tool-catalog.md` as its source instead of a
corpus anchor, because that is the truth about where the number came from.

**Compartment identification is measured-versus-original, and the tolerance is
the caller's.** Boonsville infers undrained compartments from recent pressures
"at or very near the expected original reservoir pressure", and never says how
near. The tool always reports the fraction of original; it issues a verdict only
against a tolerance the caller states. The tempting adjacent tool - inferring
connectivity from two *measured* pressures with no original - is not in the
source at all and is a refusal.

**The Horner tool returns p\*, not average reservoir pressure.** The
extrapolation to (t_p + dt)/dt = 1 is p_i only for a short test in an
infinite-acting reservoir; the drainage-shape (MBH) correction that would close
the gap for a long test in a bounded, depleted drainage area is not in this
corpus, so the difference is flagged and left unquantified rather than guessed.
The straight-line window is required rather than detected, because the source
requires a log-log wellbore-storage screen before the line is chosen and an
automatic change-point detector would be a method the source does not contain.

Time units in the Horner path are hours throughout and t_p must share the unit
of dt: N_p/Q_o comes out in days, which is why `producing_time` converts rather
than returning the ratio.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

from .result import Quantity, Refusal

# --- corpus anchors -------------------------------------------------------
GRADIENT = "03-dst/earlougher-well-test-analysis-part2-1977#4"       # Example 8.1, p. 94
POTENTIAL = "00-reference/ahmed-reservoir-engineering-handbook#71"   # Eqs. 6-15/6-16, pp. 336-337
API_GRAVITY = "00-reference/ahmed-reservoir-engineering-handbook#20"  # Eq. 2-68
COMPARTMENT = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#24"
PZ = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#28"
HORNER = "00-reference/ahmed-reservoir-engineering-handbook#100"     # Eq. 6-177, pp. 458-465
DST_HORNER = "03-dst/earlougher-well-test-analysis-part2-1977#3"     # p. 93

# Not a corpus anchor, and deliberately shaped so it cannot be mistaken for one.
HOUSE_BANDS = "tool-catalog.md 'Thresholds the corpus does not supply' — PROVISIONAL house rule, not from the corpus"

# --- constants ------------------------------------------------------------
# All four are the same physical constant in different units, and the corpus
# states each of them; 62.3664/144 = 0.43310 and 7.4805/144 = 0.05194792 exactly.
FRESH_WATER_LB_FT3 = 62.3664        # Earlougher #4
FRESH_WATER_GRAD_PSI_FT = 0.43310   # Earlougher #4; Ahmed Eq. 6-16 prints it rounded to 0.433
LB_FT3_PER_LB_GAL = 7.4805          # Earlougher #4
PSI_FT_PER_LB_FT3 = 1.0 / 144.0     # Ahmed Eq. 6-15

API_NUM = 141.5                     # Ahmed Eq. 2-68
API_OFFSET = 131.5                  # Ahmed Eq. 2-68

# PROVISIONAL, from tool-catalog.md's threshold table. Never a default: a caller
# must pass this in to get a fluid type at all. ((upper bound psi/ft, label), ...)
PROVISIONAL_FLUID_BANDS: tuple[tuple[float, str], ...] = (
    (0.25, "gas"),
    (0.40, "oil"),
    (float("inf"), "water"),
)
_BOUNDARY_PROXIMITY_PSI_FT = 0.005  # presentation-only: when to warn that a typed value sat on a boundary

# beg#28: "a reservoir permeability of greater than 5 to 10 md is typically
# required for 24-h shut-in pressures to build up sufficiently to represent
# average reservoir pressure."
PZ_PERM_FLOOR_MD = 5.0
PZ_PERM_CEILING_MD = 10.0

# Earlougher #3: two shut-in extrapolations differing by more than "a typical
# value" of 5 percent indicate a very small reservoir or a bad test.
SHUTIN_SIGNIFICANT_FRACTION = 0.05

# Ahmed p. 461: dt > 170,000 C e^(0.14 s) / (kh/mu) starts the semilog line.
STORAGE_COEFF = 170_000.0
STORAGE_SKIN_COEFF = 0.14

_PZ_ALTERNATIVE_CAUSES = (
    "flattening is necessary, not sufficient: water drive, compaction drive, commingled "
    "multi-layer production and operational changes all produce it (beg#28); confirm with "
    "supporting geological and geophysical interpretation"
)


# --- internal helpers -----------------------------------------------------
def _fit_line(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float, float, float]:
    """Least squares y = a + b x. Returns (slope, intercept, r2, max |residual|)."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0.0:
        raise ZeroDivisionError("no spread in x")
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    sse = sum(r * r for r in resid)
    sst = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - sse / sst if sst > 0 else 1.0
    return b, a, r2, max(abs(r) for r in resid)


def _check_finite(**kwargs: float) -> None:
    for name, v in kwargs.items():
        if not math.isfinite(v):
            raise ValueError(f"{name} must be finite, got {v!r}")


# =========================================================================
# 44 - pressure_gradient
# =========================================================================
def pressure_gradient(p_upper_psia: float, depth_upper_ft: float,
                      p_lower_psia: float, depth_lower_ft: float,
                      depths_are_tvd: bool = True):
    """Fluid gradient from two pressures at two depths. psi/ft.

    grad = (p_lower - p_upper) / (depth_lower - depth_upper), the hydrostatic
    relation of Earlougher Example 8.1 differenced over one column segment -
    the direction the source itself uses when it turns a 110 psi rise into
    315 ft of 0.349 psi/ft oil.

    Both pressures must be on the same base (both psia or both psig). A gradient
    is a difference, so it is base-independent; the tool cannot check it and
    records the assumption.
    """
    _check_finite(p_upper_psia=p_upper_psia, p_lower_psia=p_lower_psia,
                  depth_upper_ft=depth_upper_ft, depth_lower_ft=depth_lower_ft)
    if not depths_are_tvd:
        return Refusal(
            reason="a fluid gradient is pressure per vertical foot; measured depth will "
                   "understate it in any deviated hole",
            needed=("true vertical depth for both points (tools/geometry.py minimum curvature)",),
            source=GRADIENT)
    dz = depth_lower_ft - depth_upper_ft
    if dz < 0:
        raise ValueError("depth_lower_ft is above depth_upper_ft; the arguments are swapped")
    if dz == 0:
        return Refusal(
            reason="the two points are at the same true vertical depth; there is no vertical "
                   "separation to divide the pressure difference by",
            needed=("two pressures at different TVDs",), source=GRADIENT)
    dp = p_lower_psia - p_upper_psia
    grad = dp / dz
    flags: list[str] = ["same pressure base assumed for both gauges (psia vs psig not checkable)"]
    if dp < 0:
        flags.append("pressure decreases downward — not a static hydrostatic column")
    if grad > FRESH_WATER_GRAD_PSI_FT:
        flags.append(f"gradient exceeds the fresh-water {FRESH_WATER_GRAD_PSI_FT} psi/ft base — "
                     "brine, mud or a moving/mixed column, not a static formation fluid")
    return Quantity(grad, "psi/ft",
                    "fluid gradient from a pressure pair (Earlougher Example 8.1, dp = grad x dz)",
                    GRADIENT,
                    inputs={"p_upper_psia": p_upper_psia, "depth_upper_ft": depth_upper_ft,
                            "p_lower_psia": p_lower_psia, "depth_lower_ft": depth_lower_ft,
                            "delta_p_psi": dp, "delta_depth_ft": dz},
                    assumptions={"depth_basis": "TVD", "same_pressure_base": True},
                    flags=tuple(flags))


def gradient_from_density(density: float, unit: str):
    """Fluid gradient from density. psi/ft.

    Earlougher Example 8.1 writes the lb/gal chain out in full:
    (lb_m/gal)(7.4805 (lb_m/cu ft)/(lb_m/gal))(0.43310 psi/ft / 62.3664 lb_m/cu ft).
    Ahmed Eq. 6-15 gives rho/144 for lb/ft3 and Eq. 6-16 gives 0.433*gamma for
    specific gravity. They are one constant: 62.3664/144 = 0.43310.
    """
    _check_finite(density=density)
    if density <= 0:
        raise ValueError("density must be positive")
    if unit == "lb/gal":
        grad = density * LB_FT3_PER_LB_GAL * FRESH_WATER_GRAD_PSI_FT / FRESH_WATER_LB_FT3
        method = "gradient from mud weight (Earlougher Example 8.1, p. 94)"
        source = GRADIENT
    elif unit == "lb/ft3":
        grad = density * PSI_FT_PER_LB_FT3
        method = "gradient from density, rho/144 (Ahmed Eq. 6-15)"
        source = POTENTIAL
    elif unit in ("g/cc", "sg"):
        grad = density * FRESH_WATER_GRAD_PSI_FT
        method = "gradient from specific gravity, 0.433*gamma (Ahmed Eq. 6-16)"
        source = POTENTIAL
    else:
        raise ValueError("unit must be one of 'lb/gal', 'lb/ft3', 'g/cc', 'sg'")
    flags = ()
    if grad > FRESH_WATER_GRAD_PSI_FT:
        flags = (f"gradient exceeds the fresh-water {FRESH_WATER_GRAD_PSI_FT} psi/ft base — "
                 "brine or mud, not a static formation fluid",)
    return Quantity(grad, "psi/ft", method, source,
                    inputs={"density": density, "density_unit": unit},
                    assumptions={"fresh_water_basis": f"{FRESH_WATER_GRAD_PSI_FT} psi/ft "
                                                      f"at {FRESH_WATER_LB_FT3} lb/ft3"},
                    flags=flags)


def gradient_from_api(api_deg: float):
    """Oil gradient from API gravity. psi/ft.

    Ahmed Eq. 2-68 inverted for gamma_o, then Ahmed Eq. 6-16. Earlougher's
    Example 8.1 works the same chain in prose: 44 API -> 0.806 SG -> 0.349 psi/ft.
    """
    _check_finite(api_deg=api_deg)
    denom = api_deg + API_OFFSET
    if denom <= 0:
        raise ValueError("api_deg <= -131.5 gives a non-positive specific gravity (Eq. 2-68)")
    gamma_o = API_NUM / denom
    grad = gamma_o * FRESH_WATER_GRAD_PSI_FT
    return Quantity(grad, "psi/ft",
                    "oil gradient from API gravity (Ahmed Eq. 2-68 then Eq. 6-16)",
                    # Eq. 2-68 lives in ahmed#20; ahmed#71 holds the 0.433 gamma of
                    # Eq. 6-16. Earlougher#4 holds neither - its 44 API -> 0.806 ->
                    # 0.349 prose is in #5 - so it is not this result's anchor.
                    API_GRAVITY,
                    inputs={"api_deg": api_deg, "gamma_o": gamma_o},
                    assumptions={"gradient_constant_source": POTENTIAL,
                                 "worked_precedent": "Earlougher Example 8.1 "
                                                     "(03-dst/earlougher-well-test-analysis-"
                                                     "part2-1977#5): 44 API -> 0.806 -> "
                                                     "0.349 psi/ft"})


def fluid_type_from_gradient(grad_psi_ft: float,
                             bands: Sequence[tuple[float, str]] | None = None,
                             ambiguity_margin_psi_ft: float = 0.0):
    """Fluid type implied by a gradient — only against a caller-supplied table.

    No gradient-to-fluid-type table exists anywhere in this corpus; the catalog
    says so on this tool's own source line. Pass `PROVISIONAL_FLUID_BANDS` to
    opt in to the house rule, or a table of your own. There is no default.

    Returns a Quantity whose *value is the gradient it was given* - a fluid type
    is not a number - with the verdict in assumptions["fluid_type"].
    """
    _check_finite(grad_psi_ft=grad_psi_ft, ambiguity_margin_psi_ft=ambiguity_margin_psi_ft)
    if ambiguity_margin_psi_ft < 0:
        raise ValueError("ambiguity_margin_psi_ft must be >= 0")
    if bands is None:
        return Refusal(
            reason="no gradient-to-fluid-type table exists in this corpus: the cited source "
                   "supports the density-to-gradient conversion only. Nothing here justifies "
                   "a gas/oil/water cutoff.",
            needed=("a caller-supplied band table",
                    "or an explicit opt-in to tools.pressure.PROVISIONAL_FLUID_BANDS, the "
                    "catalog's PROVISIONAL house rule (gas < 0.25 / oil 0.25-0.40 / water > 0.40 psi/ft)",
                    "to make it SOURCED: a pressure-gradient interpretation chart added to the corpus"),
            source=GRADIENT)

    bands = tuple(bands)
    if not bands:
        raise ValueError("bands must be non-empty")
    bounds = [b for b, _ in bands]
    if any(b2 <= b1 for b1, b2 in zip(bounds, bounds[1:])):
        raise ValueError("band upper bounds must ascend")
    if not math.isinf(bounds[-1]):
        raise ValueError("the last band's upper bound must be inf, so every gradient lands somewhere")

    provisional = bands == PROVISIONAL_FLUID_BANDS
    finite_bounds = [b for b in bounds[:-1]]
    flags: list[str] = []

    label = None
    # A margin of 0 is a zero-WIDTH ambiguous zone, not the absence of one: a
    # gradient sitting exactly on a boundary is still ambiguous. tool-catalog.md
    # "Gradient -> fluid type": the tool "returns ambiguous in the overlaps rather
    # than picking - a gas/oil boundary at 0.25 is a convention, not a measurement,
    # and gas-cut oil sits right on it." The bands are contiguous, so the boundary
    # value IS the whole overlap.
    if any(abs(grad_psi_ft - b) <= ambiguity_margin_psi_ft for b in finite_bounds):
        label = "ambiguous"
    else:
        for upper, name in bands:
            if grad_psi_ft < upper:
                label = name
                break
        if ambiguity_margin_psi_ft == 0 and any(
                abs(grad_psi_ft - b) <= _BOUNDARY_PROXIMITY_PSI_FT for b in finite_bounds):
            flags.append("no ambiguity margin set; a value sitting on a band boundary was typed anyway")

    if provisional:
        flags.append("fluid type is a PROVISIONAL house rule (tool-catalog.md), not a corpus threshold")
    return Quantity(grad_psi_ft, "psi/ft",
                    "fluid type from gradient against a caller-supplied band table",
                    HOUSE_BANDS if provisional else "caller-supplied band table",
                    inputs={"grad_psi_ft": grad_psi_ft, "bands": bands},
                    assumptions={"fluid_type": label,
                                 "threshold_status": "PROVISIONAL" if provisional else "CALLER",
                                 "ambiguity_margin_psi_ft": ambiguity_margin_psi_ft},
                    flags=tuple(flags))


# =========================================================================
# 45 - pressure_system_compare
# =========================================================================
def pressure_system_compare(p_measured_psi: float,
                            p_original_psi: float | None = None,
                            near_original_tolerance: float | None = None,
                            label: str = ""):
    """Is this interval drained? Measured pressure against its original pressure.

    beg#24: pressures "at or very near the expected original reservoir pressure"
    indicate poorly drained or compartmented reserves; the Vineyard, where the
    best recent measurement is 1,500 psi against a 2,200 psi original, is the
    source's own example of the opposite.

    Refuses without an original pressure: the corpus contains no test for
    connectivity between two *measured* pressures alone.
    """
    if p_original_psi is None:
        return Refusal(
            reason="the corpus's compartment test is measured pressure versus that interval's "
                   "ORIGINAL pressure (beg#24). It states no test, and no threshold, for "
                   "inferring connectivity from two measured pressures alone — differential "
                   "depletion between connected layers of contrasting permeability produces "
                   "the same signature (beg#28).",
            needed=("the interval's original/expected initial reservoir pressure, psi",),
            source=COMPARTMENT)
    _check_finite(p_measured_psi=p_measured_psi, p_original_psi=p_original_psi)
    if p_original_psi <= 0:
        raise ValueError("p_original_psi must be positive")

    fraction = p_measured_psi / p_original_psi
    # beg#24 compares a pressure with "the expected original reservoir pressure
    # FOR THAT INTERVAL", reading originals off 1950's completions and measured
    # values off "wells drilled since 1990". Two scalars carry none of that, and
    # the corpus contains no datum correction to apply, so the precondition is
    # disclosed rather than checked: an uncorrected datum difference is the
    # classic false near-original.
    flags: list[str] = [
        "unverified by this tool: both pressures must be for the SAME stratigraphic "
        "interval and referenced to a COMMON DATUM (an uncorrected datum difference "
        "reads as a false near-original), and the measured pressure must be recent "
        "relative to the original — beg#24 compares wells drilled since 1990 against "
        "1950's originals. The tool receives two scalars and can check none of these."
    ]
    assumptions: dict[str, Any] = {"label": label}

    if near_original_tolerance is None:
        flags.append("no tolerance supplied: fraction of original reported, not classified")
    else:
        _check_finite(near_original_tolerance=near_original_tolerance)
        if near_original_tolerance < 0:
            raise ValueError("near_original_tolerance must be >= 0")
        near = (1.0 - fraction) <= near_original_tolerance
        assumptions["verdict"] = ("near_original_isolated_or_poorly_drained" if near
                                  else "depleted_or_in_communication")
        assumptions["near_original_tolerance"] = near_original_tolerance
        flags.append('verdict tolerance is CALLER-supplied; the corpus states no boundary for '
                     '"at or very near" original pressure')
    if fraction > 1.0:
        flags.append("measured pressure exceeds the stated original — either the original "
                     "estimate is low or this is not a stabilised reservoir pressure")
    return Quantity(fraction, "fraction of original pressure",
                    "measured vs original interval pressure (BEG Boonsville, Figs. B4-B7)",
                    COMPARTMENT,
                    inputs={"p_measured_psi": p_measured_psi, "p_original_psi": p_original_psi,
                            "depletion_psi": p_original_psi - p_measured_psi,
                            "depletion_fraction": 1.0 - fraction},
                    assumptions=assumptions, flags=tuple(flags))


def pz_flattening_test(points: Sequence[tuple[float, float]],
                       permeability_md: float,
                       straight_line_n: int | None = None,
                       pressures_are_average: bool = False,
                       gp_unit: str = "MMscf",
                       flattening_tolerance: float | None = None):
    """Does the p/z line flatten — i.e. is a second compartment feeding this one?

    beg#28: p/z vs cumulative gas is a straight line in a volumetric reservoir,
    x-intercept = OGIP; later flattening "may suggest communication with an
    adjacent, supporting reservoir volume or compartment". Refuses below 5 md
    unless the caller warrants the pressures are true average reservoir
    pressures, because below that band the flattening "reflects nothing other
    than" short shut-ins failing to reach average pressure.
    """
    _check_finite(permeability_md=permeability_md)
    pts = [(float(g), float(pz)) for g, pz in points]
    if len(pts) < 3:
        return Refusal(reason="p/z flattening needs at least three points: a line to fit and a "
                              "later point to test against it",
                       needed=("three or more (cumulative gas, p/z) pairs",), source=PZ)
    if any(g2 <= g1 for (g1, _), (g2, _) in zip(pts, pts[1:])):
        return Refusal(reason="points are not ascending in cumulative production; the tool will "
                              "not sort a series whose order may itself be the error",
                       needed=("(cumulative gas, p/z) pairs ascending in cumulative gas",),
                       source=PZ)
    if any(pz <= 0 for _, pz in pts):
        raise ValueError("p/z values must be positive")

    if permeability_md < PZ_PERM_FLOOR_MD and not pressures_are_average:
        return Refusal(
            reason=f"permeability {permeability_md:g} md is below the {PZ_PERM_FLOOR_MD:g} to "
                   f"{PZ_PERM_CEILING_MD:g} md the source says is typically required for 24-h "
                   "shut-in pressures to represent average reservoir pressure. Below it the p/z "
                   "plot flattens for that reason alone — the Bend Conglomerate's own case, where "
                   "the technique was found not useful.",
            needed=("pressures that are true average reservoir pressures (set pressures_are_average=True "
                    "with their provenance)",
                    "or longer shut-ins / analysed buildups",),
            source=PZ)
    if straight_line_n is None:
        return Refusal(
            reason="the early straight line is the analyst's pick off the plot; the source does "
                   "not automate it and neither does this tool",
            needed=("straight_line_n: how many leading points form the straight line",), source=PZ)
    if straight_line_n < 2 or straight_line_n >= len(pts):
        raise ValueError("straight_line_n must be >= 2 and leave at least one point to test")

    head = pts[:straight_line_n]
    slope, intercept, r2, max_resid = _fit_line([g for g, _ in head], [pz for _, pz in head])
    if slope >= 0:
        return Refusal(reason="the early p/z line does not fall with cumulative production; that "
                              "is a data problem, not a compartment",
                       needed=("a declining p/z trend over the fitted window",), source=PZ)

    gp_last, pz_last = pts[-1]
    predicted = intercept + slope * gp_last
    if predicted <= 0:
        return Refusal(reason="the early straight line extrapolates to p/z <= 0 at the last "
                              "point; there is nothing to measure a deviation against",
                       needed=("a later point inside the line's positive range, or a shorter "
                               "straight-line window",), source=PZ)
    deviation = (pz_last - predicted) / predicted
    ogip = -intercept / slope

    flags = [_PZ_ALTERNATIVE_CAUSES]
    assumptions: dict[str, Any] = {"straight_line_n": straight_line_n,
                                   "pressures_are_average": pressures_are_average,
                                   "gp_unit": gp_unit}
    if PZ_PERM_FLOOR_MD <= permeability_md <= PZ_PERM_CEILING_MD:
        flags.append(f"permeability {permeability_md:g} md is inside the source's marginal "
                     f"{PZ_PERM_FLOOR_MD:g}-{PZ_PERM_CEILING_MD:g} md band — short shut-in "
                     "pressures may not represent average reservoir pressure")
    if pressures_are_average:
        flags.append("permeability gate waived: caller asserts these are average reservoir pressures")
    if flattening_tolerance is None:
        flags.append("no tolerance supplied: deviation reported, not classified")
    else:
        _check_finite(flattening_tolerance=flattening_tolerance)
        if flattening_tolerance < 0:
            raise ValueError("flattening_tolerance must be >= 0")
        assumptions["verdict"] = ("flattening_consistent_with_a_secondary_compartment"
                                  if deviation > flattening_tolerance else "on_the_volumetric_line")
        assumptions["flattening_tolerance"] = flattening_tolerance
        flags.append("flattening threshold is CALLER-supplied; the corpus states no numeric boundary")
    return Quantity(deviation, "fraction",
                    "p/z deviation above the early volumetric straight line (BEG Boonsville, Fig. B21)",
                    PZ,
                    inputs={"slope_pz_per_gp": slope, "intercept_pz": intercept,
                            "ogip": ogip, "ogip_unit": gp_unit,
                            "gp_last": gp_last, "pz_last": pz_last, "pz_predicted": predicted,
                            "deviation_pz": pz_last - predicted,
                            "r_squared": r2, "max_residual_pz": max_resid,
                            "permeability_md": permeability_md},
                    assumptions=assumptions, flags=tuple(flags))


# =========================================================================
# 46 - formation_pressure_estimate
# =========================================================================
def producing_time(np_stb: float, q_stb_d: float):
    """t_p = N_p / Q_o (Ahmed, #100), returned in HOURS.

    N_p/Q_o is days; the Horner ratio needs t_p in the same unit as dt, which is
    hours. The conversion is here so it cannot be forgotten at the call site.
    """
    _check_finite(np_stb=np_stb, q_stb_d=q_stb_d)
    if q_stb_d <= 0:
        raise ValueError("q_stb_d must be positive")
    if np_stb < 0:
        raise ValueError("np_stb must be >= 0")
    days = np_stb / q_stb_d
    return Quantity(days * 24.0, "hr", "producing time t_p = N_p/Q_o (Ahmed, Eq. above 6-176)",
                    HORNER,
                    inputs={"np_stb": np_stb, "q_stb_d": q_stb_d, "t_p_days": days},
                    assumptions={"stabilized_rate_assumed": True})


def formation_pressure_estimate(points: Sequence[tuple[float, float]],
                                t_p_hr: float,
                                delta_t_min_hr: float | None = None,
                                delta_t_max_hr: float | None = None,
                                storage: dict[str, float] | None = None,
                                rate_stabilized: bool = True,
                                test_type: str = "buildup"):
    """Horner extrapolation of a buildup straight line to (t_p + dt)/dt = 1. psi.

    Ahmed Eq. 6-177: p_ws = p_i - m log[(t_p + dt)/dt], so a least-squares fit of
    p_ws against log10((t_p + dt)/dt) over the straight-line portion has the
    extrapolated pressure as its intercept at a ratio of one.

    The window is required, not detected. Ahmed: "In all pressure buildup test
    analyses, the log-log data plot should be made before the straight line is
    chosen on the semilog data plot."
    """
    _check_finite(t_p_hr=t_p_hr)
    if t_p_hr <= 0:
        raise ValueError("t_p_hr must be positive")
    if test_type not in ("buildup", "dst"):
        raise ValueError("test_type must be 'buildup' or 'dst'")
    if not rate_stabilized:
        return Refusal(
            reason="the well was not produced at a stabilized constant rate before shut-in; "
                   "Ahmed states standard buildup analysis then 'may provide erroneous "
                   "information about the formation'",
            needed=("Odeh and Selig's modified t_p* and q* (Earlougher Eqs. 5.29/5.30, "
                    "03-dst/earlougher-well-test-analysis-part2-1977#3)",
                    "or a multiple-rate analysis",),
            source=HORNER)

    pts = [(float(dt), float(p)) for dt, p in points]
    for dt, p in pts:
        _check_finite(delta_t_hr=dt, p_ws_psi=p)
        if dt < 0:
            raise ValueError("shut-in times must be >= 0")
    flags: list[str] = []
    p_wf = None
    zero_rows = [p for dt, p in pts if dt == 0.0]
    if zero_rows:
        p_wf = zero_rows[-1]
        pts = [(dt, p) for dt, p in pts if dt > 0.0]
        flags.append("flowing pressure p_wf (dt = 0) excluded from the fit")

    # --- straight-line window -------------------------------------------
    lo = delta_t_min_hr
    screen = "caller window"
    storage_start = None
    if storage is not None:
        try:
            c = float(storage["C_bbl_psi"]); s = float(storage["s"])
            k = float(storage["k_md"]); h = float(storage["h_ft"]); mu = float(storage["mu_cp"])
        except KeyError as exc:
            raise ValueError(f"storage needs C_bbl_psi, s, k_md, h_ft, mu_cp; missing {exc}") from exc
        if c <= 0 or k <= 0 or h <= 0 or mu <= 0:
            raise ValueError("storage C, k, h and mu must be positive")
        storage_start = STORAGE_COEFF * c * math.exp(STORAGE_SKIN_COEFF * s) / (k * h / mu)
        lo = storage_start if lo is None else max(lo, storage_start)
        screen = "Ahmed 170000*C*exp(0.14*s)/(kh/mu)"
    elif lo is None:
        return Refusal(
            reason="the semilog straight line must be chosen after a log-log wellbore-storage "
                   "screen (Ahmed, p. 461); fitting every point handed over would draw the line "
                   "through storage-dominated data",
            needed=("delta_t_min_hr, the start of the straight line off the log-log plot",
                    "or storage={'C_bbl_psi','s','k_md','h_ft','mu_cp'} for Ahmed's "
                    "dt > 170000*C*e^(0.14 s)/(kh/mu)",),
            source=HORNER)

    hi = math.inf if delta_t_max_hr is None else delta_t_max_hr
    window = [(dt, p) for dt, p in pts if lo <= dt <= hi]
    n_excluded = len(pts) - len(window)
    if len(window) < 2:
        return Refusal(
            reason=f"only {len(window)} buildup point(s) fall inside the straight-line window "
                   f"[{lo:g}, {hi:g}] hr; a line needs two",
            needed=("a wider window, or more late-time buildup data",), source=HORNER)

    xs = [math.log10((t_p_hr + dt) / dt) for dt, _ in window]
    ys = [p for _, p in window]
    # R6 before the fit: _fit_line's guard is an exact sxx == 0 test, which
    # identical x values do not reach in floating point (sxx lands around
    # 1e-31), so a degenerate window would otherwise be fitted as if it had
    # spread and return a p* of several thousand psi off a slope in the
    # thousands of psi/cycle.
    if max(xs) - min(xs) <= 0.0:
        return Refusal(reason="every point in the window shares one Horner time ratio; there is "
                              "no spread to fit a line through",
                       needed=("buildup points at different shut-in times",), source=HORNER)
    try:
        slope, p_star, r2, max_resid = _fit_line(xs, ys)
    except ZeroDivisionError:
        return Refusal(reason="every point in the window shares one Horner time ratio; there is "
                              "no spread to fit a line through",
                       needed=("buildup points at different shut-in times",), source=HORNER)
    m = -slope
    if m <= 0:
        return Refusal(
            reason="the fitted line does not rise toward the extrapolation intercept (slope "
                   f"{m:.4g} psi/cycle); these are not buildup data on a Horner straight line",
            needed=("shut-in pressures that increase with shut-in time",), source=HORNER)

    p_1hr = p_star - m * math.log10((t_p_hr + 1.0) / 1.0)

    if test_type != "dst":
        flags.append("p* is the extrapolated (false) pressure; it equals average reservoir "
                     "pressure only for a short-duration test in an infinite-acting reservoir. "
                     "A long test in a bounded drainage area needs the drainage-shape (MBH) "
                     "correction of Earlougher Ch. 6, which is not in this corpus.")
    else:
        flags.append("short-duration DST: 'generally no need to correct the extrapolated pressure "
                     "for drainage shape' (Earlougher #3, p. 93)")
    if storage_start is not None:
        flags.append(f"wellbore-storage window start {storage_start:.4g} hr from Ahmed's "
                     f"170000*C*e^(0.14s)/(kh/mu); {n_excluded} point(s) excluded")
    else:
        flags.append(f"no storage screen performed: window supplied by caller; "
                     f"{n_excluded} point(s) excluded")
    if len(window) == 2:
        flags.append("only two points in the straight line: the fit is exact and unverifiable")
    if max_resid > 0.1 * m:
        flags.append(f"residual up to {max_resid:.1f} psi against a slope of {m:.1f} psi/cycle — "
                     "check the straight-line window (house presentation rule; the corpus states "
                     "no goodness-of-fit criterion)")

    return Quantity(p_star, "psi",
                    "Horner extrapolation to (t_p + dt)/dt = 1 (Ahmed Eq. 6-177)", HORNER,
                    inputs={"t_p_hr": t_p_hr, "n_points_used": len(window),
                            "delta_t_window_hr": (lo, hi),
                            "slope_m_psi_per_cycle": m, "p_1hr_psi": p_1hr,
                            "r_squared": r2, "max_residual_psi": max_resid,
                            "p_wf_psi": p_wf},
                    assumptions={"rate_stabilized": rate_stabilized,
                                 "storage_screen": screen,
                                 "test_type": test_type,
                                 "pressure_meaning": "p* (extrapolated/false pressure)"},
                    flags=tuple(flags))


def shutin_consistency_check(p_star_a_psi: float, p_star_b_psi: float,
                             significant_fraction: float = SHUTIN_SIGNIFICANT_FRACTION):
    """Do two shut-in periods extrapolate to the same pressure? Earlougher #3, p. 93.

    "The extrapolated p_i should be about the same for both the initial and final
    shut-in periods. If it is significantly different, a very small reservoir or
    a bad test is indicated... a typical value might be 5 percent." One of the
    few genuinely sourced thresholds in this group, so it is the default here.
    """
    _check_finite(p_star_a_psi=p_star_a_psi, p_star_b_psi=p_star_b_psi,
                  significant_fraction=significant_fraction)
    if p_star_a_psi <= 0 or p_star_b_psi <= 0:
        raise ValueError("extrapolated pressures must be positive")
    if significant_fraction < 0:
        raise ValueError("significant_fraction must be >= 0")
    diff = abs(p_star_a_psi - p_star_b_psi) / max(p_star_a_psi, p_star_b_psi)
    significant = diff > significant_fraction
    flags = ("a very small reservoir or a bad test is indicated; repeat with a longer final "
             "flow period if possible (Earlougher #3)",) if significant else ()
    return Quantity(diff, "fraction",
                    "initial vs final shut-in extrapolation agreement (Earlougher, p. 93)",
                    DST_HORNER,
                    inputs={"p_star_a_psi": p_star_a_psi, "p_star_b_psi": p_star_b_psi,
                            "difference_psi": abs(p_star_a_psi - p_star_b_psi)},
                    flags=flags,
                    assumptions={"verdict": "significant_difference" if significant else "consistent",
                                 "significant_fraction": significant_fraction,
                                 "threshold_status": "SOURCED (Earlougher #3: 'a typical value "
                                                     "might be 5 percent')"})
