"""Water and gas coning. Ahmed, Chapter 9; onepetro SPE "Water and gas coning".

Three decisions here are not obvious from the equations, and each is the reason a
whole branch of this module exists.

**The units reconcile (catalog note on #47, RESOLVED).** Ahmed states Meyer-Garder
with 0.246e-4 and rho in lb/ft3; the JAS restatement of the *same* correlation
uses 0.001535 with rho in gm/cc. They are one correlation, not two:
0.001535 / 62.428 = 0.246e-4. The catalog resolves it to **Ahmed's lb/ft3 form**
because the rest of the coning and gas tools are Ahmed-based, so one convention
holds across the section. Every density argument is therefore named `rho_*_lb_ft3`,
and the gm/cc coefficients live in `*_COEFF_G_CC` as documented conversion checks
that no formula uses. They are never averaged.

**A spread, not a number.** The four correlations were fitted from different
physics and disagree materially on identical input: on Ahmed's Example 9-10
reservoir made isotropic they give 12.78 / 16.09 / 17.98 STB/day for
Meyer-Garder / Chaperon / Schols, a factor of 1.41 across the extremes.
(Do not read a bigger spread out of Ahmed's printed answers - his Examples 9-2,
9-9 and 9-10 use different h and r_e, so 8.13 / 20.16 / 18.0 spans three
reservoirs, not three correlations.) `coning_critical_rate` therefore returns a
`Range` over whichever correlations could answer; collapsing that to one number
would invent a confidence the literature does not have.

**Bottom water in a gas well is refused by four of the five.** The corpus is
explicit that no gas-water critical-rate correlation exists
(`04-coning/jas-water-coning-iranian-gas-field`: "For gas-water system, however,
no correlation has been published calculating critical rate, yet"), and the one
gas-well coning paper in the corpus, SPE 12068, is an OSTI abstract with no full
text. The single sourced route is Chaney's Eq. 9-15, which prints the gas-water
form outright in Mscf/day - and needs a chart reading. Substituting mu_g/B_g/k_g
into Meyer-Garder or Schols would change the output units with no source saying
the coefficient survives, so those refuse by name instead.

**The Sobocinski-Cornelius exponent is a step and is encoded as one.** alpha = 0.5
for M <= 1 and 0.6 for 1 < M <= 10, from Ahmed Eq. 9-24. It is a lookup table, not
an interpolation, and M > 10 refuses rather than extrapolating - the source stops
at 10. Ahmed's Examples 9-11 and 9-13 print the substitution as "(1 + 3.6)" and
"(1 + 3^6)"; both are OCR corruptions of 3^0.6 = 1.933182, which is the only
reading that reproduces his published 123 and 57.2 days.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

from .result import Quantity, Range, Refusal

# --------------------------------------------------------------------------
# Corpus anchors
# --------------------------------------------------------------------------

MEYER_GARDER = "00-reference/ahmed-reservoir-engineering-handbook#118"   # Eqs. 9-1..9-3, pp. 574-577
MG_EXAMPLES = "00-reference/ahmed-reservoir-engineering-handbook#119"    # Examples 9-1..9-4
CHIERICI = "00-reference/ahmed-reservoir-engineering-handbook#120"       # Eqs. 9-5..9-10, pp. 581-584
CHIERICI_EXAMPLE = "00-reference/ahmed-reservoir-engineering-handbook#121"
CHANEY_CHAPERON_SCHOLS = "00-reference/ahmed-reservoir-engineering-handbook#122"  # Eqs. 9-14..9-25, pp. 598-608
SOBOCINSKI = "00-reference/ahmed-reservoir-engineering-handbook#122"     # Eqs. 9-21..9-25, pp. 606-608
BOURNAZEL = "00-reference/ahmed-reservoir-engineering-handbook#123"      # Eqs. 9-26/9-27, pp. 609-610
ONEPETRO = "04-coning/onepetro-water-and-gas-coning-print#1"             # the rate-falls-with-time rule
ONEPETRO_CORRELATIONS = "04-coning/onepetro-water-and-gas-coning-print#3"  # "both apply to water and gas coning"
JAS_GAS_WATER = "04-coning/jas-water-coning-iranian-gas-field"           # "no correlation has been published"

# --------------------------------------------------------------------------
# Coefficients.  UNIT SYSTEM for every *_LB_FT3 constant below:
#   rho lb/ft3 | k md | h, r ft | mu cp | B bbl/STB (bbl/Mscf for gas) | q STB/day
# The *_G_CC values are the same correlations restated on a gm/cc density basis.
# They are conversion checks only - no formula in this module uses them.
# --------------------------------------------------------------------------

LB_FT3_PER_G_CC = 62.428  # density unit conversion, for the reconcile check only

MEYER_GARDER_COEFF_LB_FT3 = 0.246e-4   # Ahmed Eqs. 9-1/9-2/9-3, #118 pp. 575-576
MEYER_GARDER_COEFF_G_CC = 0.001535     # JAS restatement, 04-coning/jas-...#p3 Eq. 2.1
CHIERICI_COEFF_LB_FT3 = 0.492e-4       # Ahmed Eqs. 9-9/9-10, #120 p. 583
CHIERICI_COEFF_G_CC = 0.003073         # onepetro Eq. 8, #3
CHAPERON_COEFF_LB_FT3 = 0.0783e-4      # Ahmed Eq. 9-17, #122 p. 604
CHAPERON_COEFF_G_CC = 4.888e-4         # onepetro Eq. 1, #1
SCHOLS_COEFF_LB_FT3 = 0.0783e-4        # Ahmed Eq. 9-20, #122 p. 605
CHANEY_COEFF_OIL_WATER = 0.5288e-4     # Ahmed Eq. 9-14, #122 p. 598
CHANEY_COEFF_GAS_WATER = 0.5288e-4     # Ahmed Eq. 9-15, #122 p. 603  -> Mscf/day
CHANEY_COEFF_GAS_OIL = 0.2676e-4       # Ahmed Eq. 9-16, #122 p. 603

CHAPERON_QC_INTERCEPT = 0.7311         # Ahmed Eq. 9-18 (Joshi 1991), #122 p. 604
CHAPERON_QC_SLOPE = 1.943              # Ahmed's value.  onepetro Eq. 2 prints 1.843 on a
#                                        different length basis (h_c, not h - h_p); the two
#                                        do NOT reconcile and are not averaged.  Ahmed's is
#                                        implemented because it reproduces Example 9-9.
CHAPERON_QC_SLOPE_ONEPETRO = 1.843     # recorded, unused - see spec 47 "unresolved"

SCHOLS_A = 0.432                       # Ahmed Eq. 9-20 bracket
SCHOLS_B = 3.142                       # = pi; onepetro Eq. 9 prints pi
SCHOLS_EXPONENT = 0.14                 # (h/r_e)^0.14

SOBOCINSKI_Z_COEFF = 0.492e-4          # Ahmed Eq. 9-21, #122 p. 607
SOBOCINSKI_TIME_COEFF = 20325.0        # Ahmed Eq. 9-23, #122 p. 607 -> days
SOBOCINSKI_Z_MAX = 3.5                 # Joshi: no breakthrough at or above, #122 p. 608
BOURNAZEL_Z_MAX = 4.286                # Joshi as printed: no breakthrough at or above, #123 p. 609
# Joshi's printed 4.286 is 30/7 = 4.2857142857... rounded UP, and Eq. 9-26's
# denominator (3 - 0.7 Z) vanishes at exactly 30/7.  Between 30/7 and 4.286 the
# printed threshold is too permissive: (t_D)_BT comes out NEGATIVE and Eq. 9-23
# returns a negative time to breakthrough.  Ahmed's own Eq. 9-27 shows he derived
# it from the exact singularity, not from the rounded print:
#     0.492e-4 / (30/7) = 0.1148e-4 exactly, the printed coefficient
#     0.492e-4 / 4.286  = 0.11479235e-4
# so the operative ceiling is 30/7 and 4.286 is only what the refusal text quotes.
BOURNAZEL_Z_SINGULAR = 30.0 / 7.0      # = 4.2857142857..., root of 3 - 0.7 Z
SOBOCINSKI_QOC_COEFF_PRINTED = 0.141e-4    # Ahmed Eq. 9-25 as printed (rounded)
BOURNAZEL_QOC_COEFF_PRINTED = 0.1148e-4    # Ahmed Eq. 9-27 as printed (rounded)

# Sobocinski-Cornelius mobility exponent, Ahmed Eq. 9-24, #122 p. 608:
#   alpha = 0.5 for M <= 1;  alpha = 0.6 for 1 < M <= 10.
# A step, printed as a step.  Encoded as (M_upper_inclusive, alpha) so that no
# later edit can smooth it into an interpolation.  Nothing is published above 10.
MOBILITY_ALPHA_TABLE: tuple[tuple[float, float], ...] = ((1.0, 0.5), (10.0, 0.6))
MOBILITY_M_MAX = MOBILITY_ALPHA_TABLE[-1][0]

# Chierici chart validity, Ahmed #120 pp. 582-583 (the OCR renders "<=" as "''")
CHIERICI_RDE_RANGE = (5.0, 80.0)
CHIERICI_EPSILON_RANGE = (0.0, 0.75)
CHIERICI_DELTA_RANGE = (0.07, 0.9)
CHIERICI_CHART_FAMILIES = (5, 10, 20, 30, 40, 60, 80)   # Figures 9-8 .. 9-14
CHANEY_CHART_THICKNESSES = (12.5, 25.0, 50.0, 75.0, 100.0)  # Figures 9-19 .. 9-23

# A density is only ever handed to #47 in one of these.  The default is Ahmed's
# lb/ft3, per the catalog's RESOLVED reconcile; a gm/cc density is *converted*
# at LB_FT3_PER_G_CC and said so, and anything else raises rather than being
# consumed as if it were lb/ft3 - a mis-united density here is a wrong rate an
# operator produces against.  Same shape as pressure.gradient_from_density's
# `unit` argument; the gm/cc spellings are quality._DENSITY_UNITS'.
DENSITY_UNIT_LB_FT3 = "lb/ft3"
DENSITY_UNITS_G_CC = frozenset({"g/cm3", "g/cc", "gm/cc"})
DENSITY_UNITS = (DENSITY_UNIT_LB_FT3,) + tuple(sorted(DENSITY_UNITS_G_CC))
_DENSITY_ARGS = ("rho_o_lb_ft3", "rho_w_lb_ft3", "rho_g_lb_ft3")

OIL_WATER = "oil_water"
GAS_OIL = "gas_oil"
GAS_AND_WATER = "gas_and_water"
GAS_WATER = "gas_water"
SYSTEMS = (OIL_WATER, GAS_OIL, GAS_AND_WATER, GAS_WATER)

_NO_GAS_WATER = (
    "no gas-water (bottom water in a gas well) form of this correlation is published: "
    "it is an oil rate in STB/day built on mu_o and B_o. "
    "04-coning/jas-water-coning-iranian-gas-field: \"For gas-water system, however, no "
    "correlation has been published calculating critical rate, yet.\" "
    "Chaney Eq. 9-15 is the only sourced gas-water route and needs a chart reading."
)


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _missing(**kwargs: Any) -> tuple[str, ...]:
    """Names of the arguments that were left as None."""
    return tuple(name for name, value in kwargs.items() if value is None)


def _positive(**kwargs: Any) -> None:
    """Impossible arguments are programmer error, not a refusal."""
    for name, value in kwargs.items():
        if value is None:
            continue
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value!r}")


def _isotropy_refusal(correlation: str, quote: str, source: str,
                      k_h_md: float | None, k_v_md: float | None) -> Refusal | None:
    """Meyer-Garder, Schols and Chaney are stated valid only for k_h = k_v."""
    if k_h_md is None or k_v_md is None:
        return None
    if math.isclose(k_h_md, k_v_md, rel_tol=1e-9):
        return None
    return Refusal(
        reason=(f"{correlation} is valid only for an isotropic formation "
                f"(k_h = k_v); k_h = {k_h_md} md, k_v = {k_v_md} md. {quote}"),
        needed=("an anisotropic correlation - Chaperon (Ahmed Eq. 9-17) or "
                "Chierici (Eqs. 9-9/9-10)",),
        source=source)


def _isotropy_flag(k_v_md: float | None) -> tuple[str, ...]:
    if k_v_md is None:
        return ("assumes k_h = k_v; k_v not supplied, so isotropy was not checked",)
    return ()


# --------------------------------------------------------------------------
# #47 - the correlations, one function each.  Quantity or Refusal.
# --------------------------------------------------------------------------

def meyer_garder_critical_rate(
    system: str,
    h_ft: float,
    h_p_ft: float | None = None,
    *,
    k_o_md: float | None = None,
    mu_o_cp: float | None = None,
    b_o_bbl_stb: float | None = None,
    r_e_ft: float | None = None,
    r_w_ft: float | None = None,
    rho_o_lb_ft3: float | None = None,
    rho_w_lb_ft3: float | None = None,
    rho_g_lb_ft3: float | None = None,
    d_t_ft: float | None = None,
    k_h_md: float | None = None,
    k_v_md: float | None = None,
    **_ignored: Any,
) -> Quantity | Refusal:
    """Meyer-Garder (1954). Ahmed Eqs. 9-1 (gas), 9-2 (water), 9-3 (Pirson, both).

    Refuses on a gas well with bottom water: Eqs. 9-1..9-3 are oil rates and the
    corpus prints no gas-water form.
    """
    if system == GAS_WATER:
        return Refusal(reason=f"Meyer-Garder: {_NO_GAS_WATER}",
                       needed=("Chaney Eq. 9-15 with a Q_curve reading off Figures 9-19..9-23",),
                       source=MEYER_GARDER)

    iso = _isotropy_refusal(
        "Meyer-Garder", "Ahmed, #118 p. 574: \"Meyer and Garder assume a homogeneous "
        "system with a uniform permeability throughout the reservoir, i.e., k_h = k_v.\"",
        MEYER_GARDER, k_h_md, k_v_md)
    if iso is not None:
        return iso

    need = _missing(k_o_md=k_o_md, mu_o_cp=mu_o_cp, b_o_bbl_stb=b_o_bbl_stb,
                    r_e_ft=r_e_ft, r_w_ft=r_w_ft, rho_o_lb_ft3=rho_o_lb_ft3)
    if system in (OIL_WATER, GAS_AND_WATER):
        need += _missing(rho_w_lb_ft3=rho_w_lb_ft3)
    if system in (GAS_OIL, GAS_AND_WATER):
        need += _missing(rho_g_lb_ft3=rho_g_lb_ft3)
    if system == GAS_OIL:
        need += _missing(d_t_ft=d_t_ft)
    else:
        need += _missing(h_p_ft=h_p_ft)
    if need:
        return Refusal(reason=f"Meyer-Garder needs {', '.join(need)}",
                       needed=need, source=MEYER_GARDER)

    mobility = k_o_md / (mu_o_cp * b_o_bbl_stb)
    ln_ratio = math.log(r_e_ft / r_w_ft)
    flags = _isotropy_flag(k_v_md)

    if system == GAS_OIL:
        h_p = h_ft - d_t_ft
        thickness = h_ft ** 2 - (h_ft - d_t_ft) ** 2
        drho = rho_o_lb_ft3 - rho_g_lb_ft3
        q = MEYER_GARDER_COEFF_LB_FT3 * (drho / ln_ratio) * mobility * thickness
        eq, extra = "9-1 (gas coning)", {"D_t_ft": d_t_ft, "h_p_ft": h_p, "delta_rho": drho}
    elif system == OIL_WATER:
        thickness = h_ft ** 2 - h_p_ft ** 2
        drho = rho_w_lb_ft3 - rho_o_lb_ft3
        q = MEYER_GARDER_COEFF_LB_FT3 * (drho / ln_ratio) * mobility * thickness
        eq, extra = "9-2 (water coning)", {"h_p_ft": h_p_ft, "delta_rho": drho}
    else:  # GAS_AND_WATER - Pirson's (1977) combination
        d_wo = rho_w_lb_ft3 - rho_o_lb_ft3
        d_og = rho_o_lb_ft3 - rho_g_lb_ft3
        d_wg = rho_w_lb_ft3 - rho_g_lb_ft3
        ratio = d_og / d_wg
        bracket = d_wo * ratio ** 2 + d_og * (1.0 - ratio) ** 2
        thickness = h_ft ** 2 - h_p_ft ** 2
        q = MEYER_GARDER_COEFF_LB_FT3 * mobility * (thickness / ln_ratio) * bracket
        eq = "9-3 (simultaneous gas and water coning, Pirson 1977)"
        extra = {"h_p_ft": h_p_ft, "delta_rho_wo": d_wo, "delta_rho_og": d_og,
                 "delta_rho_wg": d_wg, "bracket": bracket}

    return Quantity(
        q, "STB/day", f"Meyer-Garder critical oil rate (Ahmed Eq. {eq})", MEYER_GARDER,
        inputs={"system": system, "h_ft": h_ft, "k_o_md": k_o_md, "mu_o_cp": mu_o_cp,
                "b_o_bbl_stb": b_o_bbl_stb, "r_e_ft": r_e_ft, "r_w_ft": r_w_ft,
                "ln_re_over_rw": ln_ratio, **extra},
        assumptions={"coefficient": MEYER_GARDER_COEFF_LB_FT3,
                     "density_unit": "lb/ft3 (catalog reconcile: Ahmed's form, not the "
                                     "0.001535 gm/cc restatement)",
                     "k_h_equals_k_v": True},
        flags=flags)


def chierici_critical_rate(
    system: str,
    h_ft: float,
    h_p_ft: float | None = None,
    *,
    psi: float | None = None,
    k_o_md: float | None = None,
    k_h_md: float | None = None,
    k_v_md: float | None = None,
    mu_o_cp: float | None = None,
    b_o_bbl_stb: float | None = None,
    r_e_ft: float | None = None,
    rho_o_lb_ft3: float | None = None,
    rho_w_lb_ft3: float | None = None,
    rho_g_lb_ft3: float | None = None,
    d_t_ft: float | None = None,
    d_b_ft: float | None = None,
    **_ignored: Any,
) -> Quantity | Refusal:
    """Chierici-Ciucci-Pizzi (1964). Ahmed Eqs. 9-9 (water) / 9-10 (gas-oil).

    Psi has no closed form - it is read off Figures 9-8..9-14, which are images in
    this corpus. It is a required caller input and its absence is a refusal that
    tells the caller which chart to enter and where.
    """
    if system == GAS_WATER:
        return Refusal(reason=f"Chierici: {_NO_GAS_WATER} Eqs. 9-9/9-10 return Q_ow and "
                              "Q_og, both oil rates.",
                       needed=("Chaney Eq. 9-15 with a Q_curve reading",), source=CHIERICI)
    if system == GAS_AND_WATER:
        return Refusal(
            reason=("Chierici treats simultaneous coning as two separate limits: Ahmed "
                    "#120 p. 584 requires Q_o <= Q_ow and Q_o <= Q_og, which needs two "
                    "chart reads (Psi_w at delta_w and Psi_g at delta_g). Call this tool "
                    "twice, as oil_water and as gas_oil, and take the smaller."),
            needed=("Psi_w and Psi_g read separately off Figures 9-8..9-14",),
            source=CHIERICI)

    need = _missing(psi=psi, k_o_md=k_o_md, k_h_md=k_h_md, k_v_md=k_v_md,
                    mu_o_cp=mu_o_cp, b_o_bbl_stb=b_o_bbl_stb, r_e_ft=r_e_ft,
                    h_p_ft=h_p_ft, rho_o_lb_ft3=rho_o_lb_ft3)
    need += _missing(rho_w_lb_ft3=rho_w_lb_ft3) if system == OIL_WATER \
        else _missing(rho_g_lb_ft3=rho_g_lb_ft3)
    if need and psi is None:
        # the chart read is the interesting omission - report the entry point for it
        reason = ("Chierici's dimensionless function Psi has no closed form; it is read "
                  f"off Figures 9-8..9-14 (r_De = {CHIERICI_CHART_FAMILIES}), which are "
                  "images in this corpus.")
        if None not in (r_e_ft, k_h_md, k_v_md):
            r_de = (r_e_ft / h_ft) * math.sqrt(k_h_md / k_v_md)
            reason += f" Enter the chart(s) bracketing r_De = {r_de:.2f}"
            if h_p_ft is not None:
                reason += f" at epsilon = {h_p_ft / h_ft:.3f}"
            reason += "."
        others = [n for n in need if n != "psi"]
        if others:
            reason += f" Also missing: {', '.join(others)}."
        return Refusal(reason=reason, needed=need, source=CHIERICI)
    if need:
        return Refusal(reason=f"Chierici needs {', '.join(need)}", needed=need,
                       source=CHIERICI)

    r_de = (r_e_ft / h_ft) * math.sqrt(k_h_md / k_v_md)          # Eq. 9-5
    epsilon = h_p_ft / h_ft                                       # Eq. 9-6
    if system == GAS_OIL:
        if d_t_ft is None:
            return Refusal(reason="Chierici gas-oil needs d_t_ft for delta_g = D_t/h (Eq. 9-7)",
                           needed=("d_t_ft",), source=CHIERICI)
        delta, delta_name = d_t_ft / h_ft, "delta_g"
        drho = rho_o_lb_ft3 - rho_g_lb_ft3
        eq = "9-10"
    else:
        d_b = d_b_ft
        if d_b is None and d_t_ft is not None:
            d_b = h_ft - d_t_ft - h_p_ft
        if d_b is None:
            return Refusal(reason="Chierici oil-water needs d_b_ft (WOC to the bottom of the "
                                  "perforations) for delta_w = D_b/h (Eq. 9-8)",
                           needed=("d_b_ft",), source=CHIERICI)
        delta, delta_name = d_b / h_ft, "delta_w"
        drho = rho_w_lb_ft3 - rho_o_lb_ft3
        eq = "9-9"

    lo, hi = CHIERICI_RDE_RANGE
    if not lo <= r_de <= hi:
        return Refusal(reason=f"r_De = {r_de:.2f} is outside the {lo}-{hi} range Ahmed "
                              f"(#120 p. 582) states the chart correlation is valid for",
                       needed=("a correlation valid outside 5 <= r_De <= 80",), source=CHIERICI)
    lo, hi = CHIERICI_EPSILON_RANGE
    if not lo <= epsilon <= hi:
        return Refusal(reason=f"epsilon = h_p/h = {epsilon:.3f} is outside the {lo}-{hi} "
                              f"range stated at #120 p. 582",
                       needed=("a shorter perforated interval, or another correlation",),
                       source=CHIERICI)
    lo, hi = CHIERICI_DELTA_RANGE
    if not lo <= delta <= hi:
        return Refusal(reason=f"{delta_name} = {delta:.3f} is outside the {lo}-{hi} range "
                              f"stated at #120 p. 583",
                       needed=("perforations repositioned within the chart range",),
                       source=CHIERICI)

    q = CHIERICI_COEFF_LB_FT3 * (h_ft ** 2 * drho / (b_o_bbl_stb * mu_o_cp)) * k_o_md * psi
    return Quantity(
        q, "STB/day", f"Chierici-Ciucci-Pizzi critical oil rate (Ahmed Eq. {eq})", CHIERICI,
        inputs={"system": system, "h_ft": h_ft, "h_p_ft": h_p_ft, "r_De": r_de,
                "epsilon": epsilon, delta_name: delta, "psi": psi, "k_o_md": k_o_md,
                "delta_rho": drho, "mu_o_cp": mu_o_cp, "b_o_bbl_stb": b_o_bbl_stb},
        assumptions={"coefficient": CHIERICI_COEFF_LB_FT3,
                     "density_unit": "lb/ft3",
                     "psi_source": "caller's reading off Figures 9-8..9-14",
                     "homogeneous_formation": "Ahmed #120 p. 584: 'This set of curves "
                                              "should be only applied to homogeneous formations.'"},
        flags=("Psi is a caller-supplied chart reading, not computed",))


def chaperon_critical_rate(
    system: str,
    h_ft: float,
    h_p_ft: float | None = None,
    *,
    k_h_md: float | None = None,
    k_v_md: float | None = None,
    mu_o_cp: float | None = None,
    b_o_bbl_stb: float | None = None,
    r_e_ft: float | None = None,
    rho_o_lb_ft3: float | None = None,
    rho_w_lb_ft3: float | None = None,
    rho_g_lb_ft3: float | None = None,
    **_ignored: Any,
) -> Quantity | Refusal:
    """Chaperon (1986) with Joshi's (1991) coefficient. Ahmed Eqs. 9-17/9-18/9-19.

    The one correlation here that is valid for k_v != k_h. Ahmed's 1.943 is used,
    not onepetro's 1.843 - see the module spec; the two do not reconcile and are
    never averaged.
    """
    if system == GAS_WATER:
        return Refusal(reason=f"Chaperon: {_NO_GAS_WATER}",
                       needed=("Chaney Eq. 9-15 with a Q_curve reading",),
                       source=CHANEY_CHAPERON_SCHOLS)
    if system == GAS_AND_WATER:
        return Refusal(
            reason=("Chaperon Eq. 9-17 carries a single density difference and is stated "
                    "for one contact at a time; the corpus prints no simultaneous form. "
                    "Call it twice, as oil_water and as gas_oil, and take the smaller."),
            needed=("a simultaneous gas-and-water Chaperon form",),
            source=CHANEY_CHAPERON_SCHOLS)

    need = _missing(k_h_md=k_h_md, k_v_md=k_v_md, mu_o_cp=mu_o_cp,
                    b_o_bbl_stb=b_o_bbl_stb, r_e_ft=r_e_ft, h_p_ft=h_p_ft)
    need += _missing(rho_o_lb_ft3=rho_o_lb_ft3)
    need += _missing(rho_w_lb_ft3=rho_w_lb_ft3) if system == OIL_WATER \
        else _missing(rho_g_lb_ft3=rho_g_lb_ft3)
    if need:
        return Refusal(reason=f"Chaperon needs {', '.join(need)}", needed=need,
                       source=CHANEY_CHAPERON_SCHOLS)

    alpha_dd = (r_e_ft / h_ft) * math.sqrt(k_v_md / k_h_md)          # Eq. 9-19
    q_c_star = CHAPERON_QC_INTERCEPT + CHAPERON_QC_SLOPE / alpha_dd  # Eq. 9-18
    drho = (rho_w_lb_ft3 - rho_o_lb_ft3) if system == OIL_WATER \
        else (rho_o_lb_ft3 - rho_g_lb_ft3)
    q = (CHAPERON_COEFF_LB_FT3 * k_h_md * (h_ft - h_p_ft) ** 2
         / (mu_o_cp * b_o_bbl_stb)) * drho * q_c_star

    flags = ("Ahmed Eq. 9-18 uses 1.943 with alpha'' = (r_e/h)sqrt(k_v/k_h); the onepetro "
             "restatement uses 1.843 with r_rD built on h_c (perforations-to-contact). "
             "The two do not reconcile; Ahmed's form is implemented and reproduces his "
             "Example 9-9.",)
    if system == GAS_OIL:
        flags += ("gas-oil use of Chaperon follows onepetro #1 Eq. 4, which defines "
                  "delta-rho as 'rho_w - rho_o or rho_o - rho_g'; Ahmed prints only the "
                  "water form",)
    return Quantity(
        q, "STB/day", "Chaperon critical oil rate (Ahmed Eq. 9-17, q_c* from Eq. 9-18)",
        CHANEY_CHAPERON_SCHOLS,
        inputs={"system": system, "h_ft": h_ft, "h_p_ft": h_p_ft, "k_h_md": k_h_md,
                "k_v_md": k_v_md, "alpha_dd": alpha_dd, "q_c_star": q_c_star,
                "delta_rho": drho, "mu_o_cp": mu_o_cp, "b_o_bbl_stb": b_o_bbl_stb},
        assumptions={"coefficient": CHAPERON_COEFF_LB_FT3, "density_unit": "lb/ft3",
                     "anisotropy": "valid for k_v != k_h"},
        flags=flags)


def schols_critical_rate(
    system: str,
    h_ft: float,
    h_p_ft: float | None = None,
    *,
    k_o_md: float | None = None,
    k_h_md: float | None = None,
    k_v_md: float | None = None,
    mu_o_cp: float | None = None,
    b_o_bbl_stb: float | None = None,
    r_e_ft: float | None = None,
    r_w_ft: float | None = None,
    rho_o_lb_ft3: float | None = None,
    rho_w_lb_ft3: float | None = None,
    rho_g_lb_ft3: float | None = None,
    **_ignored: Any,
) -> Quantity | Refusal:
    """Schols (1972). Ahmed Eq. 9-20.

    Isotropic only, stated outright by Ahmed, and explicitly not for simultaneous
    gas and water coning, stated by onepetro. Both are refusals.
    """
    if system == GAS_WATER:
        return Refusal(reason=f"Schols: {_NO_GAS_WATER}",
                       needed=("Chaney Eq. 9-15 with a Q_curve reading",),
                       source=CHANEY_CHAPERON_SCHOLS)
    if system == GAS_AND_WATER:
        return Refusal(
            reason=("onepetro #3: Schols' correlation \"does not directly apply to cases "
                    "in which water and gas coning act simultaneously\". Use Meyer-Garder "
                    "Eq. 9-3 (Pirson) for that case."),
            needed=("a simultaneous-coning correlation",), source=ONEPETRO_CORRELATIONS)

    iso = _isotropy_refusal(
        "Schols", "Ahmed, #122 p. 605: \"Schols' equation is only valid for isotropic "
        "formation, i.e., k_h = k_v.\"", CHANEY_CHAPERON_SCHOLS, k_h_md, k_v_md)
    if iso is not None:
        return iso

    need = _missing(k_o_md=k_o_md, mu_o_cp=mu_o_cp, b_o_bbl_stb=b_o_bbl_stb,
                    r_e_ft=r_e_ft, r_w_ft=r_w_ft, h_p_ft=h_p_ft,
                    rho_o_lb_ft3=rho_o_lb_ft3)
    need += _missing(rho_w_lb_ft3=rho_w_lb_ft3) if system == OIL_WATER \
        else _missing(rho_g_lb_ft3=rho_g_lb_ft3)
    if need:
        return Refusal(reason=f"Schols needs {', '.join(need)}", needed=need,
                       source=CHANEY_CHAPERON_SCHOLS)

    drho = (rho_w_lb_ft3 - rho_o_lb_ft3) if system == OIL_WATER \
        else (rho_o_lb_ft3 - rho_g_lb_ft3)
    bracket = SCHOLS_A + SCHOLS_B / math.log(r_e_ft / r_w_ft)
    shape = (h_ft / r_e_ft) ** SCHOLS_EXPONENT
    q = (SCHOLS_COEFF_LB_FT3 * (drho * k_o_md * (h_ft ** 2 - h_p_ft ** 2)
                                / (mu_o_cp * b_o_bbl_stb)) * bracket * shape)

    flags = _isotropy_flag(k_v_md)
    if system == GAS_OIL:
        flags += ("gas-oil use of Schols follows onepetro #3: \"Both works apply to both "
                  "water and gas coning\"; Ahmed prints only the water form",)
    return Quantity(
        q, "STB/day", "Schols critical oil rate (Ahmed Eq. 9-20)", CHANEY_CHAPERON_SCHOLS,
        inputs={"system": system, "h_ft": h_ft, "h_p_ft": h_p_ft, "k_o_md": k_o_md,
                "delta_rho": drho, "bracket": bracket, "shape_factor": shape,
                "mu_o_cp": mu_o_cp, "b_o_bbl_stb": b_o_bbl_stb, "r_e_ft": r_e_ft,
                "r_w_ft": r_w_ft},
        assumptions={"coefficient": SCHOLS_COEFF_LB_FT3, "density_unit": "lb/ft3",
                     "k_h_equals_k_v": True},
        flags=flags)


def chaney_critical_rate(
    system: str,
    h_ft: float,
    h_p_ft: float | None = None,
    *,
    q_curve_bbl_d: float | None = None,
    k_o_md: float | None = None,
    k_g_md: float | None = None,
    mu_o_cp: float | None = None,
    mu_g_cp: float | None = None,
    b_o_bbl_stb: float | None = None,
    b_g_bbl_mscf: float | None = None,
    rho_o_lb_ft3: float | None = None,
    rho_w_lb_ft3: float | None = None,
    rho_g_lb_ft3: float | None = None,
    k_h_md: float | None = None,
    k_v_md: float | None = None,
    **_ignored: Any,
) -> Quantity | Refusal:
    """Chaney et al. (1956). Ahmed Eqs. 9-14 (oil-water), 9-15 (gas-water), 9-16 (gas-oil).

    The only correlation in the corpus with a printed **gas-water** form, so it is
    the only route for bottom water in a gas well - and it needs Q_curve read off
    Figures 9-19..9-23, which are images here.
    """
    if system == GAS_AND_WATER:
        return Refusal(reason=("Chaney prints correction equations for oil-water, gas-water "
                               "and gas-oil separately (Eqs. 9-14..9-16); no simultaneous "
                               "form is given. Ahmed's note on p. 604 offers only a "
                               "trial-and-error use of the same curves."),
                       needed=("a simultaneous-coning Chaney form",),
                       source=CHANEY_CHAPERON_SCHOLS)

    iso = _isotropy_refusal(
        "Chaney", "Ahmed, #122 p. 604: \"Chaney's method was developed for a homogeneous, "
        "isotropic reservoir with k_v = k_h.\"", CHANEY_CHAPERON_SCHOLS, k_h_md, k_v_md)
    if iso is not None:
        return iso

    if q_curve_bbl_d is None:
        nearest = min(CHANEY_CHART_THICKNESSES, key=lambda t: abs(t - h_ft))
        return Refusal(
            reason=("Chaney's Q_curve has no closed form; it is read off Figures "
                    "9-19..9-23, drawn for sand thicknesses "
                    f"{CHANEY_CHART_THICKNESSES} ft (nearest to h = {h_ft} ft is "
                    f"{nearest} ft), r_e = 1000 ft, r_w = 3 in, k = 1000 md, mu_o = 1 cp. "
                    "Those figures are images in this corpus."),
            needed=("q_curve_bbl_d, read off the figure for this sand thickness at the "
                    "distance from the top of the perforations to the top of the sand",),
            source=CHANEY_CHAPERON_SCHOLS)

    if system == GAS_WATER:
        need = _missing(k_g_md=k_g_md, mu_g_cp=mu_g_cp, b_g_bbl_mscf=b_g_bbl_mscf,
                        rho_w_lb_ft3=rho_w_lb_ft3, rho_g_lb_ft3=rho_g_lb_ft3)
        if need:
            return Refusal(reason=f"Chaney gas-water (Eq. 9-15) needs {', '.join(need)}",
                           needed=need, source=CHANEY_CHAPERON_SCHOLS)
        drho = rho_w_lb_ft3 - rho_g_lb_ft3
        q = CHANEY_COEFF_GAS_WATER * (k_g_md * drho / (mu_g_cp * b_g_bbl_mscf)) * q_curve_bbl_d
        unit, eq = "Mscf/day", "9-15 (gas-water)"
        detail = {"k_g_md": k_g_md, "mu_g_cp": mu_g_cp, "b_g_bbl_mscf": b_g_bbl_mscf}
    else:
        need = _missing(k_o_md=k_o_md, mu_o_cp=mu_o_cp, b_o_bbl_stb=b_o_bbl_stb,
                        rho_o_lb_ft3=rho_o_lb_ft3)
        need += _missing(rho_w_lb_ft3=rho_w_lb_ft3) if system == OIL_WATER \
            else _missing(rho_g_lb_ft3=rho_g_lb_ft3)
        if need:
            return Refusal(reason=f"Chaney needs {', '.join(need)}", needed=need,
                           source=CHANEY_CHAPERON_SCHOLS)
        if system == OIL_WATER:
            coeff, drho, eq = (CHANEY_COEFF_OIL_WATER,
                               rho_w_lb_ft3 - rho_o_lb_ft3, "9-14 (oil-water)")
        else:
            coeff, drho, eq = (CHANEY_COEFF_GAS_OIL,
                               rho_o_lb_ft3 - rho_g_lb_ft3, "9-16 (gas-oil)")
        q = coeff * (k_o_md * drho / (mu_o_cp * b_o_bbl_stb)) * q_curve_bbl_d
        unit = "STB/day"
        detail = {"k_o_md": k_o_md, "mu_o_cp": mu_o_cp, "b_o_bbl_stb": b_o_bbl_stb}

    return Quantity(
        q, unit, f"Chaney et al. critical rate (Ahmed Eq. {eq})", CHANEY_CHAPERON_SCHOLS,
        inputs={"system": system, "h_ft": h_ft, "h_p_ft": h_p_ft,
                "q_curve_bbl_d": q_curve_bbl_d, "delta_rho": drho, **detail},
        assumptions={"density_unit": "lb/ft3",
                     "chart_basis": "Figures 9-19..9-23: r_e = 1000 ft, r_w = 3 in, "
                                    "k = 1000 md, mu_o = 1 cp, h in "
                                    f"{CHANEY_CHART_THICKNESSES} ft",
                     "k_h_equals_k_v": True},
        flags=("Q_curve is a caller-supplied chart reading, not computed",
               "Eqs. 9-14..9-16 correct for k, delta-rho, mu and B but not for r_e, r_w "
               "or h; the chart basis above is not rescaled"))


_CORRELATIONS = {
    "meyer_garder": meyer_garder_critical_rate,
    "schols": schols_critical_rate,
    "chierici": chierici_critical_rate,
    "chaperon": chaperon_critical_rate,
    "chaney": chaney_critical_rate,
}


def coning_critical_rate(
    system: str,
    h_ft: float,
    h_p_ft: float | None = None,
    *,
    density_unit: str = DENSITY_UNIT_LB_FT3,
    **kwargs: Any,
) -> Range | Refusal:
    """#47. The spread of published critical rates, not a single number.

    Runs Meyer-Garder, Schols, Chierici, Chaperon and Chaney over the same inputs
    and returns a Range across the ones that could answer. Each correlation's
    own Quantity (with its inputs, assumptions and flags) is available from the
    per-correlation function of the same name.

    Densities are lb/ft3 throughout - Ahmed's convention, per the catalog's
    reconcile decision on #47. A caller holding gm/cc (the basis of the JAS
    restatement, 0.001535) declares `density_unit="g/cm3"` and the values are
    converted here, once, at LB_FT3_PER_G_CC; any other unit raises. Output is
    STB/day, except gas_water (bottom water in a gas well) which is Mscf/day via
    Chaney Eq. 9-15.
    """
    if system not in SYSTEMS:
        raise ValueError(f"system must be one of {SYSTEMS}, got {system!r}")
    if density_unit not in DENSITY_UNITS:
        raise ValueError(
            f"density_unit must be one of {DENSITY_UNITS}, got {density_unit!r}. "
            "#47 is implemented on Ahmed's lb/ft3 form (catalog reconcile, RESOLVED); "
            "a density in another unit is converted explicitly or not accepted at all.")
    converted_from = None
    if density_unit in DENSITY_UNITS_G_CC:
        converted_from = density_unit
        kwargs = dict(kwargs)
        for _rho in _DENSITY_ARGS:
            if kwargs.get(_rho) is not None:
                kwargs[_rho] = kwargs[_rho] * LB_FT3_PER_G_CC
    _positive(h_ft=h_ft, mu_o_cp=kwargs.get("mu_o_cp"),
              b_o_bbl_stb=kwargs.get("b_o_bbl_stb"), k_o_md=kwargs.get("k_o_md"),
              k_h_md=kwargs.get("k_h_md"), k_v_md=kwargs.get("k_v_md"),
              r_e_ft=kwargs.get("r_e_ft"), r_w_ft=kwargs.get("r_w_ft"),
              mu_g_cp=kwargs.get("mu_g_cp"), b_g_bbl_mscf=kwargs.get("b_g_bbl_mscf"),
              k_g_md=kwargs.get("k_g_md"))
    r_e, r_w = kwargs.get("r_e_ft"), kwargs.get("r_w_ft")
    if r_e is not None and r_w is not None and r_e <= r_w:
        raise ValueError(f"r_e_ft ({r_e}) must exceed r_w_ft ({r_w})")
    if h_p_ft is not None and h_p_ft < 0:
        raise ValueError(f"h_p_ft must not be negative, got {h_p_ft}")

    rho_o, rho_w, rho_g = (kwargs.get("rho_o_lb_ft3"), kwargs.get("rho_w_lb_ft3"),
                           kwargs.get("rho_g_lb_ft3"))
    for name, drho in (("rho_w - rho_o", None if (rho_w is None or rho_o is None)
                        else rho_w - rho_o),
                       ("rho_o - rho_g", None if (rho_o is None or rho_g is None)
                        else rho_o - rho_g),
                       ("rho_w - rho_g", None if (rho_w is None or rho_g is None)
                        else rho_w - rho_g)):
        if drho is not None and drho <= 0:
            return Refusal(
                reason=(f"{name} = {drho:g} lb/ft3 is not positive: the contact is not "
                        "gravitationally stable and no coning correlation applies"),
                needed=("densities ordered gas < oil < water at reservoir conditions",),
                source=MEYER_GARDER)

    d_t = kwargs.get("d_t_ft")
    if h_p_ft is not None and h_p_ft > h_ft:
        return Refusal(reason=f"perforated interval h_p = {h_p_ft} ft exceeds the column "
                              f"thickness h = {h_ft} ft",
                       needed=("a perforated interval inside the column",), source=MEYER_GARDER)
    if d_t is not None and h_p_ft is not None and d_t + h_p_ft > h_ft:
        return Refusal(reason=f"D_t + h_p = {d_t + h_p_ft} ft exceeds h = {h_ft} ft; the "
                              "perforations do not fit in the column",
                       needed=("consistent D_t, h_p and h",), source=MEYER_GARDER)

    members: dict[str, float] = {}
    quantities: dict[str, Quantity] = {}
    reasons: list[str] = []
    needed: list[str] = []
    refused_sources: list[str] = []
    for name, fn in _CORRELATIONS.items():
        result = fn(system, h_ft, h_p_ft, **kwargs)
        if isinstance(result, Refusal):
            reasons.append(f"{name}: {result.reason}")
            needed.extend(result.needed)
            if result.source:
                refused_sources.append(result.source)
        else:
            members[name] = result.value
            quantities[name] = result

    unit = "Mscf/day" if system == GAS_WATER else "STB/day"
    if not members:
        return Refusal(reason=" | ".join(reasons),
                       needed=tuple(dict.fromkeys(needed)),
                       source="; ".join(dict.fromkeys(refused_sources)) or MEYER_GARDER)

    excluded = [r.split(":", 1)[0] for r in reasons]
    method = (f"spread of published critical-rate correlations ({', '.join(members)})"
              f" for a {system} system")
    if excluded:
        method += f"; excluded: {', '.join(excluded)} - see the per-correlation refusals"
    if len(members) == 1:
        method += " - single correlation, so the spread is degenerate"
    if converted_from is not None:
        method += (f"; densities converted from {converted_from} at "
                   f"{LB_FT3_PER_G_CC} lb/ft3 per g/cm3")
    # One anchor per answering member, never the first correlation's standing in
    # for the rest: Meyer-Garder is #118, Chierici #120, Chaperon/Schols/Chaney
    # #122, and a gas-water rate attributed to #118 would cite a segment that has
    # no gas-water form.
    source = "; ".join(dict.fromkeys(q.source for q in quantities.values()))
    # `Range` gained inputs/assumptions/flags to mirror `Quantity`; a spread that
    # leaves them empty is provenanced at the band but not at the reservoir it
    # came from, and `confidence_score` (#71) reads that as an assumed number
    # however well sourced each member is. The members already carry their own
    # inputs, so this reports what they agree on plus what varies between them.
    shared: dict[str, Any] = {}
    varying: list[str] = []
    for q in quantities.values():
        for key, value in q.inputs.items():
            if key not in shared:
                shared[key] = value
            elif shared[key] != value and key not in varying:
                varying.append(key)
    inputs = {k: v for k, v in shared.items() if k not in varying}
    if varying:
        inputs["varies_between_correlations"] = sorted(varying)
    # Member flags are deliberately NOT lifted onto the spread. They say nothing
    # `method` and `assumptions` do not already say here — which correlations
    # answered, which were excluded and why — and `confidence_score` (#71) caps
    # at QUALIFIED on the presence of any flag, so republishing them would drop a
    # fully-sourced two-correlation spread a level for no new information. That
    # D4 rule is blunt (its own tests record it), and this is not the place to
    # work around it.
    return Range(min(members.values()), max(members.values()), unit, method,
                 source, members=members, inputs=inputs,
                 assumptions={"system": system,
                              "correlations": sorted(members),
                              "excluded": tuple(excluded),
                              "density_unit": density_unit,
                              "density_converted_from": converted_from})


# --------------------------------------------------------------------------
# #48 - breakthrough time
# --------------------------------------------------------------------------

def mobility_exponent(m_water_oil: float) -> float | None:
    """alpha in Eq. 9-23, from Ahmed Eq. 9-24. None where the source stops.

    A step function, printed as one: 0.5 for M <= 1, 0.6 for 1 < M <= 10. Nothing
    is published above M = 10, so this returns None there rather than guessing.
    """
    if m_water_oil <= 0:
        raise ValueError(f"mobility ratio must be positive, got {m_water_oil}")
    for upper, alpha in MOBILITY_ALPHA_TABLE:
        if m_water_oil <= upper:
            return alpha
    return None


def _sobocinski_z(rho_w: float, rho_o: float, k_h_md: float, h_ft: float,
                  h_p_ft: float, mu_o_cp: float, b_o_bbl_stb: float,
                  q_stb_d: float) -> float:
    """Dimensionless cone height, Ahmed Eq. 9-21."""
    return (SOBOCINSKI_Z_COEFF * (rho_w - rho_o) * k_h_md * h_ft * (h_ft - h_p_ft)
            / (mu_o_cp * b_o_bbl_stb * q_stb_d))


def _z_limit_rate(rho_w: float, rho_o: float, k_h_md: float, h_ft: float,
                  h_p_ft: float, mu_o_cp: float, b_o_bbl_stb: float,
                  z_max: float) -> float:
    """Q_oc implied by imposing Z = Z_max on Eq. 9-21 (Ahmed Eqs. 9-25 / 9-27).

    Derived from Eq. 9-21 rather than using the printed 0.141e-4 / 0.1148e-4:
    0.492e-4/3.5 = 0.140571e-4 is what reproduces Ahmed's own Example 9-12 answer
    of 46.3 STB/day (the printed rounding gives 46.47).
    """
    return ((SOBOCINSKI_Z_COEFF / z_max) * (rho_w - rho_o) * k_h_md * h_ft
            * (h_ft - h_p_ft) / (mu_o_cp * b_o_bbl_stb))


def _breakthrough_one(
    method: str, q_stb_d: float, h_ft: float, h_p_ft: float, rho_w: float,
    rho_o: float, k_h_md: float, k_v_md: float, mu_o_cp: float,
    b_o_bbl_stb: float, phi: float, m: float, m_source: str,
) -> Quantity | Refusal:
    z = _sobocinski_z(rho_w, rho_o, k_h_md, h_ft, h_p_ft, mu_o_cp, b_o_bbl_stb, q_stb_d)

    if method == "sobocinski_cornelius":
        # 7 - 2Z vanishes at exactly 3.5, so the printed ceiling is the singularity.
        z_max, z_max_printed = SOBOCINSKI_Z_MAX, SOBOCINSKI_Z_MAX
        source, eq = SOBOCINSKI, "9-22"
        label, qoc_eq = "Sobocinski-Cornelius", "9-25"
    else:
        # 3 - 0.7Z vanishes at 30/7; Joshi's printed 4.286 rounds it up, which would
        # let Z in [30/7, 4.286) through with a negative (t_D)_BT.  See the constants.
        z_max, z_max_printed = BOURNAZEL_Z_SINGULAR, BOURNAZEL_Z_MAX
        source, eq = BOURNAZEL, "9-26"
        label, qoc_eq = "Bournazel-Jeanson", "9-27"

    if z >= z_max:
        q_oc = _z_limit_rate(rho_w, rho_o, k_h_md, h_ft, h_p_ft, mu_o_cp,
                             b_o_bbl_stb, z_max)
        return Refusal(
            reason=(f"{label}: Z = {z:.4f} >= {z_max_printed}, at which Joshi (1991) states there "
                    f"is no water breakthrough (Eq. {eq} also becomes singular there). "
                    f"The implied critical rate from Eq. {qoc_eq} is {q_oc:.2f} STB/day; "
                    f"the well is producing {q_stb_d:g} STB/day, at or below it."),
            needed=(f"a rate above {q_oc:.2f} STB/day for a finite breakthrough time",),
            source=source)

    alpha = mobility_exponent(m)
    if alpha is None:
        return Refusal(
            reason=(f"mobility ratio M = {m:g} exceeds {MOBILITY_M_MAX:g}; Ahmed Eq. 9-24 "
                    "publishes alpha only for M <= 1 (0.5) and 1 < M <= 10 (0.6). "
                    "Extrapolating alpha would be an invented correlation."),
            needed=("alpha for M > 10 - Sobocinski and Cornelius, JPT May 1965, SPE-894-PA, "
                    "which is not in this corpus",),
            source=SOBOCINSKI)

    if method == "sobocinski_cornelius":
        t_d = (4.0 * z + 1.75 * z ** 2 - 0.75 * z ** 3) / (7.0 - 2.0 * z)
    else:
        t_d = z / (3.0 - 0.7 * z)

    t_bt = (SOBOCINSKI_TIME_COEFF * mu_o_cp * h_ft * phi * t_d
            / ((rho_w - rho_o) * k_v_md * (1.0 + m ** alpha)))

    return Quantity(
        t_bt, "days", f"{label} time to water breakthrough (Ahmed Eqs. {eq} and 9-23)",
        source,
        inputs={"q_stb_d": q_stb_d, "Z": z, "t_D_BT": t_d, "M": m, "alpha": alpha,
                "M_to_alpha": m ** alpha, "h_ft": h_ft, "h_p_ft": h_p_ft,
                "k_h_md": k_h_md, "k_v_md": k_v_md, "phi": phi,
                "delta_rho": rho_w - rho_o, "mu_o_cp": mu_o_cp,
                "b_o_bbl_stb": b_o_bbl_stb},
        assumptions={"z_coefficient": SOBOCINSKI_Z_COEFF,
                     "time_coefficient": SOBOCINSKI_TIME_COEFF,
                     "alpha_branch": "M <= 1 -> 0.5; 1 < M <= 10 -> 0.6 (Eq. 9-24, a step)",
                     "M_source": m_source,
                     "system": "water coning into a vertical oil well",
                     "density_unit": "lb/ft3"})


def coning_breakthrough_time(
    q_stb_d: float,
    h_ft: float,
    h_p_ft: float,
    *,
    rho_w_lb_ft3: float,
    rho_o_lb_ft3: float,
    k_h_md: float,
    k_v_md: float,
    mu_o_cp: float,
    b_o_bbl_stb: float,
    phi: float,
    m_water_oil: float | None = None,
    k_rw_sor: float | None = None,
    k_ro_swc: float | None = None,
    mu_w_cp: float | None = None,
    method: str = "both",
    system: str = OIL_WATER,
) -> Quantity | Range | Refusal:
    """#48. Time to water breakthrough above the critical rate.

    Sobocinski-Cornelius (Eqs. 9-21..9-23) and Bournazel-Jeanson (Eq. 9-26) share
    Z and Eq. 9-23 and differ only in the dimensionless-time correlation - by a
    factor of 2.15 on Ahmed's own example (123 vs 57.2 days). `method="both"`
    (the default) therefore returns the spread; name one method for a Quantity.

    Water coning into a vertical oil well only: every symbol in both correlations
    is oil-side or water-side, and the corpus prints no gas analogue.
    """
    if method not in ("both", "sobocinski_cornelius", "bournazel_jeanson"):
        raise ValueError("method must be 'both', 'sobocinski_cornelius' or "
                         f"'bournazel_jeanson', got {method!r}")
    # k_rw_sor / k_ro_swc are guarded here too: k_ro_swc = 0 otherwise raises a bare
    # ZeroDivisionError out of Eq. 9-24, and two negatives cancel into a positive M
    # that would be accepted silently.
    _positive(q_stb_d=q_stb_d, h_ft=h_ft, k_h_md=k_h_md, k_v_md=k_v_md,
              mu_o_cp=mu_o_cp, b_o_bbl_stb=b_o_bbl_stb, mu_w_cp=mu_w_cp,
              k_rw_sor=k_rw_sor, k_ro_swc=k_ro_swc)
    if h_p_ft < 0:
        raise ValueError(f"h_p_ft must not be negative, got {h_p_ft}")
    if not 0.0 < phi <= 1.0:
        raise ValueError(f"phi must be a fraction in (0, 1], got {phi!r} "
                         "(Ahmed's Example 9-11 prints 13% and substitutes 0.13)")

    explicit = m_water_oil is not None
    derived = None not in (k_rw_sor, k_ro_swc, mu_w_cp)
    if explicit and derived:
        raise ValueError("supply either m_water_oil or (k_rw_sor, k_ro_swc, mu_w_cp), "
                         "not both")
    if explicit:
        m, m_source = m_water_oil, "supplied directly"
    elif derived:
        m = (k_rw_sor / k_ro_swc) * (mu_o_cp / mu_w_cp)
        m_source = "computed from Ahmed Eq. 9-24"
    else:
        return Refusal(
            reason="the water-oil mobility ratio M is required by Eq. 9-23",
            needed=("m_water_oil, or all of k_rw_sor, k_ro_swc and mu_w_cp for Eq. 9-24",),
            source=SOBOCINSKI)
    if m <= 0:
        raise ValueError(f"mobility ratio must be positive, got {m}")

    if system != OIL_WATER:
        if system == GAS_WATER:
            reason = ("Sobocinski-Cornelius and Bournazel-Jeanson are water-into-oil "
                      "correlations: Eq. 9-21 carries (rho_w - rho_o), mu_o and B_o, "
                      "Q_o is in STB/day, and Eq. 9-24 defines M as the water-oil "
                      "mobility ratio. " + _NO_GAS_WATER + " Eq. 9-23's coefficient 20,325 "
                      "has no published gas-phase counterpart.")
        elif system == GAS_OIL:
            reason = ("Sobocinski-Cornelius and Bournazel-Jeanson predict *water* "
                      "breakthrough (Ahmed #122 p. 606, \"BREAKTHROUGH TIME IN VERTICAL "
                      "WELLS\", is water throughout). The corpus prints no gas-coning "
                      "breakthrough-time analogue of Eqs. 9-22/9-23/9-26.")
        else:
            reason = (f"no breakthrough-time correlation is published for a {system} "
                      "system; Eqs. 9-21..9-26 are water-into-oil only")
        return Refusal(reason=reason,
                       needed=("a breakthrough-time correlation for this system",),
                       source=SOBOCINSKI)

    if rho_w_lb_ft3 <= rho_o_lb_ft3:
        return Refusal(reason=(f"rho_w - rho_o = {rho_w_lb_ft3 - rho_o_lb_ft3:g} lb/ft3 is "
                               "not positive; the contact is not gravitationally stable"),
                       needed=("densities ordered oil < water",), source=SOBOCINSKI)
    if h_p_ft >= h_ft:
        return Refusal(reason=(f"h - h_p = {h_ft - h_p_ft:g} ft: the perforations span the "
                               "whole column, so Eq. 9-21 gives Z <= 0 and the cone height "
                               "is undefined"),
                       needed=("a perforated interval shorter than the oil column",),
                       source=SOBOCINSKI)

    common = dict(q_stb_d=q_stb_d, h_ft=h_ft, h_p_ft=h_p_ft, rho_w=rho_w_lb_ft3,
                  rho_o=rho_o_lb_ft3, k_h_md=k_h_md, k_v_md=k_v_md, mu_o_cp=mu_o_cp,
                  b_o_bbl_stb=b_o_bbl_stb, phi=phi, m=m, m_source=m_source)

    if method != "both":
        return _breakthrough_one(method, **common)

    members: dict[str, float] = {}
    reasons: list[str] = []
    needed: list[str] = []
    for name in ("sobocinski_cornelius", "bournazel_jeanson"):
        result = _breakthrough_one(name, **common)
        if isinstance(result, Refusal):
            reasons.append(result.reason)  # already prefixed with the method's name
            needed.extend(result.needed)
        else:
            members[name] = result.value
    if not members:
        return Refusal(reason=" | ".join(reasons),
                       needed=tuple(dict.fromkeys(needed)), source=SOBOCINSKI)

    text = "time to water breakthrough, spread of " + " and ".join(members)
    if reasons:
        text += "; excluded: " + " | ".join(reasons)
    return Range(min(members.values()), max(members.values()), "days", text,
                 SOBOCINSKI, members=members)


# --------------------------------------------------------------------------
# #49 - critical rate as the contact advances
# --------------------------------------------------------------------------

_SCHEDULABLE = ("meyer_garder", "schols", "chaperon")
_CHART_BOUND = {
    "chierici": ("Figures 9-8..9-14", "Psi must be re-read at every new epsilon, delta "
                 "and r_De as the column shortens"),
    "chaney": ("Figures 9-19..9-23", "Q_curve must be re-read, and those figures exist "
               f"only for sand thicknesses {CHANEY_CHART_THICKNESSES} ft, so a rising "
               "contact walks off the chart family"),
}


def coning_rate_schedule(
    correlation: str,
    system: str,
    h_ft: float,
    h_p_ft: float,
    *,
    contact_rise_ft: Sequence[float] | None = None,
    times_days: Sequence[float] | None = None,
    contact_rise_ft_per_day: float | None = None,
    d_t_ft: float | None = None,
    **kwargs: Any,
) -> Range | Refusal:
    """#49. Critical rate re-evaluated as the contact advances on the perforations.

    There is no closed form. onepetro #1 states the direction only - "with time,
    that distance usually decreases ... Thus, the critical rate will tend to
    decrease with time" - so this is a driver, not an equation: it re-runs one #47
    correlation at each contact position the caller names.

    Geometry rule, from Ahmed's own definition of h_p (Example 9-2: measured from
    the top of the formation): **the column shortens by the advance, the
    perforated interval does not.** For a gas cap, D_t shortens with it.

    Contact *position* is the independent variable. The corpus gives no
    contact-rise velocity, so `times_days` is only usable together with a
    caller-supplied `contact_rise_ft_per_day`, which is flagged as the caller's
    number.
    """
    if correlation in _CHART_BOUND:
        figures, why = _CHART_BOUND[correlation]
        return Refusal(
            reason=(f"{correlation} cannot be scheduled: {why} ({figures} are images in "
                    "this corpus). Call coning_critical_rate once per contact position "
                    "with your own chart readings instead."),
            needed=(f"digitised {figures}",), source=CHIERICI)
    if correlation not in _SCHEDULABLE:
        raise ValueError(f"correlation must be one of {_SCHEDULABLE} (or one of "
                         f"{tuple(_CHART_BOUND)}, which refuse), got {correlation!r}")
    if system not in SYSTEMS:
        raise ValueError(f"system must be one of {SYSTEMS}, got {system!r}")
    if (contact_rise_ft is None) == (times_days is None):
        raise ValueError("supply exactly one of contact_rise_ft or times_days")

    if times_days is not None:
        if contact_rise_ft_per_day is None:
            return Refusal(
                reason=("a time axis needs a contact-rise velocity, and the corpus has "
                        "none: onepetro #1 says only that the distance to the contact "
                        "\"usually decreases\" with time. No aquifer influx or material "
                        "balance in 04-coning ties position to time."),
                needed=("contact_rise_ft_per_day from repeat logging, a material balance "
                        "or a simulator - the caller's number, not the corpus's",),
                source=ONEPETRO)
        if contact_rise_ft_per_day <= 0:
            raise ValueError("contact_rise_ft_per_day must be positive")
        if any(t < 0 for t in times_days):
            raise ValueError("times_days must not be negative")
        if list(times_days) != sorted(times_days) or len(set(times_days)) != len(times_days):
            raise ValueError("times_days must be strictly ascending")
        rises = [t * contact_rise_ft_per_day for t in times_days]
        labels = [f"day_{t:g}" for t in times_days]
    else:
        if not contact_rise_ft:
            raise ValueError("contact_rise_ft must not be empty")
        if any(d < 0 for d in contact_rise_ft):
            raise ValueError("contact_rise_ft must not be negative")
        if (list(contact_rise_ft) != sorted(contact_rise_ft)
                or len(set(contact_rise_ft)) != len(contact_rise_ft)):
            raise ValueError("contact_rise_ft must be strictly ascending")
        rises = list(contact_rise_ft)
        labels = [f"rise_{d:g}_ft" for d in contact_rise_ft]

    if system == GAS_OIL:
        if d_t_ft is None:
            return Refusal(reason="a gas-cap schedule needs d_t_ft (GOC to the top of the "
                                  "perforations); the GOC descends by the advance",
                           needed=("d_t_ft",), source=ONEPETRO)
        max_advance = d_t_ft
        limit = "D_t (the GOC would reach the top of the perforations)"
    else:
        max_advance = h_ft - h_p_ft
        limit = "h - h_p (the contact would reach the perforations)"
    if max_advance <= 0:
        return Refusal(reason=f"the contact is already at the perforations: {limit} = "
                              f"{max_advance:g} ft",
                       needed=("perforations standing off the contact",), source=ONEPETRO)
    over = [d for d in rises if d >= max_advance]
    if over:
        return Refusal(
            reason=(f"contact advance{'s' if len(over) > 1 else ''} "
                    f"{', '.join(format(d, 'g') for d in over)} ft reach or pass the "
                    f"perforations; the maximum admissible advance is {max_advance:g} ft "
                    f"({limit}, exclusive). Past it the correlations' thickness term is "
                    "zero or negative and the well is already coning."),
            needed=(f"contact advances strictly below {max_advance:g} ft",),
            source=ONEPETRO)

    # #49 is a driver over #47, so its validity limits are the *union* of the
    # driver's and the correlation's - not just the correlation's.  #47's own gate
    # (gravitationally stable density ordering, h_p / D_t against h, the positivity
    # checks) lives on coning_critical_rate, and a schedule must not answer where a
    # single point refuses: with rho_w < rho_o, Eq. 9-2 returns a *negative* rate
    # that *rises* as the column shortens, contradicting the only thing onepetro #1
    # states.  Checked once at the starting geometry - nothing it guards changes as
    # the column shortens, since advances at or past the perforations are already out.
    gate = coning_critical_rate(system, h_ft, h_p_ft, d_t_ft=d_t_ft, **kwargs)
    if isinstance(gate, Refusal):
        return Refusal(reason=f"{correlation} cannot be scheduled: {gate.reason}",
                       needed=gate.needed, source=gate.source)

    fn = _CORRELATIONS[correlation]
    members: dict[str, float] = {}
    correlation_source = ""
    for label, advance in zip(labels, rises):
        h = h_ft - advance
        step_kwargs = dict(kwargs)
        if system == GAS_OIL:
            step_kwargs["d_t_ft"] = d_t_ft - advance
        result = fn(system, h, h_p_ft, **step_kwargs)
        if isinstance(result, Refusal):
            return Refusal(
                reason=(f"{correlation} refused at {label} (h = {h:g} ft): {result.reason}"),
                needed=result.needed, source=result.source)
        members[label] = result.value
        correlation_source = result.source

    values = list(members.values())
    monotone = all(b < a for a, b in zip(values, values[1:]))
    trend = ("strictly decreasing" if monotone
             else "NOT monotonically decreasing - check the geometry inputs")
    method = (f"{correlation} critical rate re-evaluated at {len(members)} contact "
              f"positions (column shortens by the advance, h_p held fixed); {trend}")
    if times_days is not None:
        method += (f"; time axis from a caller-supplied contact rise of "
                   f"{contact_rise_ft_per_day:g} ft/day, which is not from the corpus")
    unit = "Mscf/day" if system == GAS_WATER else "STB/day"
    # Provenance is both halves: the onepetro prose rule that the rate falls as the
    # contact rises, and the Ahmed anchor of the correlation every member was
    # actually computed from.  Naming only the first would hide the equation.
    source = f"{ONEPETRO} + {correlation_source}"
    return Range(min(values), max(values), unit, method, source, members=members)
