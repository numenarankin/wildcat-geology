"""Where to perforate: the optimum interval, the deliverability curve, the check.

Two curves decide where to perforate: the coning limit, which falls as the
perforations lengthen toward the contacts, and the well's deliverability, which
rises. The optimum is where they cross.

`perf_length_optimize` (#50) computes **neither** curve, and that is the design
decision worth explaining. The coning side needs Chierici's dimensionless
function Psi, which exists only as Figures 9-8 through 9-14 — images in the
corpus, with no closed form and no digitised table anywhere in the knowledge
base. Fitting a curve to them would be inventing an equation, so the chart
readings are a required input and their absence is a refusal that tells the
caller which figure to read and what to enter it with. The deliverability side is
injected too, as a callable or a table of points, so that the equation behind it
lives in exactly one place.

That place is now `partial_penetration_rate` (#51, Kozeny), also in this module.
It is the intended supplier of #50's `producing_rate` argument, and
`curve_points` adapts its `Range` into the `(b/h, q)` pairs #50 already consumes.
**#50's signature is unchanged by that** — nothing here calls into it, and the
injection stays injection, because the two tools cite different sources with
different reservoirs and coupling them would hide that.

Kozeny carries a defect the caller must be told about. The SPE page prints Eq. 14
and a substitution that agree with each other and evaluate to 417.52 STB/D, then
prints the answer as 430 and a whole table 2.93% high; only an unprinted `-0.5`
in the denominator closes the gap. The equation as printed wins, because the
alternative is shipping an equation no source states, and every result carries a
flag saying so. See `specs/51-partial_penetration_rate.md`.

`perf_standoff_check` (#58) is the reverse question — not "what is optimum" but
"is this proposal defensible". Its three halves have three evidentiary statuses,
which is its whole shape: Chierici's contact geometry is sourced with published
bounds, while the washout and net-pay cutoffs exist in no source, so they are
required arguments with no default and the tool refuses rather than picking one.

What this module does own is the arithmetic Ahmed leaves implicit: the selection
rule in #50. His Step 8 only says "compare"; the rule that reproduces his
published answer is that a well delivers min(critical, producing) at each
penetration, and the optimum maximises that minimum.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from .result import Quantity, Range, Refusal

# Ahmed, Reservoir Engineering Handbook, Ch. 9 "Gas and Water Coning".
# Chierici-Ciucci procedure and Example 9-6 (pp. 611-613).
CHIERICI_OPT = "00-reference/ahmed-reservoir-engineering-handbook#121"
# Dimensionless parameter definitions, Eqs. 9-5..9-10 and their validity ranges
# (pp. 581-584). Kept separate so a refusal cites the segment that states the limit.
CHIERICI_DEFS = "00-reference/ahmed-reservoir-engineering-handbook#120"

# Coefficient of Eqs. 9-9 and 9-10, for Q in STB/day with h in ft, rho in lb/ft3,
# k in md, B_o in bbl/STB, mu_o in cp.
CRITICAL_RATE_COEFF = 0.492e-4

# Validity ranges stated by the authors, Ahmed pp. 582-583 (Eqs. 9-5 to 9-8).
R_DE_RANGE = (5.0, 80.0)          # "5 <= r_De <= 80", after Meyer and Garder
EPSILON_MAX = 0.75                # "0 <= epsilon <= 0.75"
DELTA_G_RANGE = (0.070, 0.9)      # gas cone ratio, Eq. 9-7
DELTA_W_RANGE = (0.070, 0.9)      # water cone ratio, Eq. 9-8

# One working chart per r_De. Figures 9-8 through 9-14, Ahmed pp. 584-587.
CHART_FAMILIES = {
    5.0: "Figure 9-8",
    10.0: "Figure 9-9",
    20.0: "Figure 9-10",
    30.0: "Figure 9-11",
    40.0: "Figure 9-12",
    60.0: "Figure 9-13",
    80.0: "Figure 9-14",
}

HOMOGENEOUS_ONLY = (
    "Chierici's charts apply to homogeneous formations only "
    "(Ahmed p. 584); this cannot be checked from the inputs"
)
# Chierici's potentiometric model is for *vertical* oil wells (Ahmed p. 581), so
# h, h_p, D_t and D_b are all true vertical lengths. Handing this tool measured
# depths off a deviated well makes every step wrong and nothing downstream shows
# it, so the convention is stated on every result.
TRUE_VERTICAL_ONLY = (
    "all lengths are true vertical (TVD): h, h_p, D_t and D_b are vertical "
    "distances, because Chierici's model is for vertical oil wells (Ahmed "
    "p. 581); measured-depth lengths from a deviated well are not valid input"
)
# Ahmed's Step 6 prose cites Eq. 9-9 (which carries rho_w - rho_o) but his
# Example 9-6 arithmetic substitutes 40.12 lb/ft3 = rho_o - rho_g, i.e. Eq. 9-10.
# The arithmetic is what reproduces the published 740 STB/day, so it wins, and
# every result says so. See specs/50-perf_length_optimize.md, Open question 1.
EQ_DISCREPANCY = (
    "source discrepancy: Ahmed's Step 6 names Eq. 9-9 (Q_ow, uses rho_w - rho_o) "
    "but Example 9-6 substitutes rho_o - rho_g, i.e. Eq. 9-10; the worked "
    "arithmetic is followed here because it reproduces the published answer"
)


def _effective_dimensionless_radius(r_e_ft: float, h_ft: float,
                                    k_h_md: float, k_v_md: float) -> float:
    """r_De = (r_e/h) sqrt(k_h/k_v).  Ahmed Eq. 9-5, p. 581.

    Private: the exported Chierici parameter tools live with the coning module.
    Note the direction of the permeability ratio — Hoyland's Eq. 9-12 defines a
    different r_D with k_v/k_h, and the two are not interchangeable.
    """
    return (r_e_ft / h_ft) * (k_h_md / k_v_md) ** 0.5


def _bracketing_charts(r_de: float) -> str:
    families = sorted(CHART_FAMILIES)
    below = [f for f in families if f <= r_de]
    above = [f for f in families if f >= r_de]
    lo = CHART_FAMILIES[below[-1]] if below else CHART_FAMILIES[families[0]]
    hi = CHART_FAMILIES[above[0]] if above else CHART_FAMILIES[families[-1]]
    return lo if lo == hi else f"{lo} and {hi} (interpolate)"


def _critical_rate_stb_d(h_ft: float, delta_rho_lb_ft3: float, b_o_rb_stb: float,
                         mu_o_cp: float, k_ro: float, k_h_md: float, psi: float) -> float:
    """Chierici critical oil rate, Ahmed Eq. 9-10 (Eq. 9-9 differs only in Δρ)."""
    return (CRITICAL_RATE_COEFF * h_ft ** 2 * delta_rho_lb_ft3
            * k_ro * k_h_md * psi) / (b_o_rb_stb * mu_o_cp)


def _producing_rate_at(producing_rate: Any, eps: float) -> tuple[float | None, bool]:
    """Evaluate the injected deliverability curve at b/h = eps.

    Returns (rate, interpolated). A None rate means the point is outside the
    supplied table; this function never extrapolates.
    """
    if callable(producing_rate):
        return float(producing_rate(eps)), False
    points = sorted((float(x), float(q)) for x, q in producing_rate)
    for x, q in points:
        if abs(x - eps) < 1e-9:
            return q, False
    if eps < points[0][0] or eps > points[-1][0]:
        return None, False
    for (x0, q0), (x1, q1) in zip(points, points[1:]):
        if x0 <= eps <= x1:
            return q0 + (q1 - q0) * (eps - x0) / (x1 - x0), True
    return None, False


def perf_length_optimize(
    h_ft: float,
    r_e_ft: float,
    k_h_md: float,
    k_v_md: float,
    k_ro: float,
    b_o_rb_stb: float,
    mu_o_cp: float,
    rho_o_lb_ft3: float,
    rho_w_lb_ft3: float,
    rho_g_lb_ft3: float,
    chart_readings: Sequence[Sequence[float]] | None = None,
    producing_rate: Callable[[float], float] | Sequence[Sequence[float]] | None = None,
):
    """Optimum perforated length and position. Chierici-Ciucci, Ahmed pp. 611-613.

    `chart_readings` is a sequence of `(h_p_ft, psi_opt, delta_g_opt)` read off the
    working chart for this r_De at the Δρ_og/Δρ_ow entry ratio (Ahmed's Step 3).
    `producing_rate` is the theoretical deliverability curve versus fractional
    penetration b/h — tool #51 `partial_penetration_rate` — as a callable or as
    `(b_over_h, q_stb_d)` points.

    Returns the best rate the well can hold without coning, STB/day, with the
    winning h_p, the distance below the GOC (D_t) and above the WOC (D_b) on
    `inputs`. Refuses when either curve is missing or the source's validity
    ranges are violated.
    """
    if h_ft <= 0 or r_e_ft <= 0:
        raise ValueError("h_ft and r_e_ft must be positive")
    if k_h_md <= 0 or k_v_md <= 0:
        raise ValueError("k_h_md and k_v_md must be positive")
    if b_o_rb_stb <= 0 or mu_o_cp <= 0:
        raise ValueError("b_o_rb_stb and mu_o_cp must be positive")
    if k_ro <= 0:
        raise ValueError("k_ro must be positive")

    delta_rho_ow = rho_w_lb_ft3 - rho_o_lb_ft3
    delta_rho_og = rho_o_lb_ft3 - rho_g_lb_ft3
    r_de = _effective_dimensionless_radius(r_e_ft, h_ft, k_h_md, k_v_md)

    if delta_rho_ow <= 0 or delta_rho_og <= 0:
        return Refusal(
            reason=("fluid densities are not ordered gas < oil < water "
                    f"(rho_g={rho_g_lb_ft3}, rho_o={rho_o_lb_ft3}, rho_w={rho_w_lb_ft3} lb/ft3); "
                    "the chart entry ratio Δρ_og/Δρ_ow is undefined"),
            needed=("densities such that rho_g < rho_o < rho_w",),
            source=CHIERICI_DEFS)

    if not R_DE_RANGE[0] <= r_de <= R_DE_RANGE[1]:
        return Refusal(
            reason=(f"effective dimensionless radius r_De = {r_de:.2f} is outside the "
                    f"{R_DE_RANGE[0]:.0f}-{R_DE_RANGE[1]:.0f} range the Chierici "
                    "correlation is stated to be valid over (Ahmed p. 582)"),
            needed=("a coning method valid outside 5 <= r_De <= 80",),
            source=CHIERICI_DEFS)

    ratio = delta_rho_og / delta_rho_ow
    if producing_rate is None:
        return Refusal(
            reason=("the theoretical producing-rate curve versus fractional penetration "
                    "b/h is missing; Ahmed's Step 8 compares the coning limit against "
                    "rates from a flow equation at maximum drawdown, and this tool does "
                    "not compute that half"),
            needed=("partial_penetration_rate (#51, Kozeny) evaluated across b/h, "
                    "or caller-supplied (b_over_h, q_stb_d) points",),
            source=CHIERICI_OPT)
    if not chart_readings:
        return Refusal(
            reason=("Chierici's dimensionless function Psi has no closed form; it must be "
                    f"read from {_bracketing_charts(r_de)} for r_De = {r_de:.2f}, entering "
                    f"at Δρ_og/Δρ_ow = {ratio:.2f}"),
            needed=(f"(h_p_ft, psi_opt, delta_g_opt) triples from {_bracketing_charts(r_de)}",),
            source=CHIERICI_DEFS)

    table: list[dict[str, float]] = []
    dropped: list[str] = []
    interpolated = False

    for reading in chart_readings:
        h_p_ft, psi_opt, delta_g_opt = (float(v) for v in reading)
        eps = h_p_ft / h_ft                                   # Eq. 9-6
        if not 0 < eps <= EPSILON_MAX:
            dropped.append(f"h_p={h_p_ft:g} ft: epsilon={eps:.3f} outside 0 < e <= {EPSILON_MAX}")
            continue
        if not DELTA_G_RANGE[0] <= delta_g_opt <= DELTA_G_RANGE[1]:
            dropped.append(f"h_p={h_p_ft:g} ft: delta_g={delta_g_opt:.3f} outside "
                           f"{DELTA_G_RANGE[0]}-{DELTA_G_RANGE[1]}")
            continue
        d_t_ft = h_ft * delta_g_opt                           # Step 4, Eq. 9-7
        d_b_ft = h_ft - d_t_ft - h_p_ft                       # Step 5, Eq. 9-8
        if d_b_ft < 0:
            dropped.append(f"h_p={h_p_ft:g} ft: perforations do not fit "
                           f"(D_t={d_t_ft:.1f} + h_p > h)")
            continue
        delta_w = d_b_ft / h_ft
        if not DELTA_W_RANGE[0] <= delta_w <= DELTA_W_RANGE[1]:
            dropped.append(f"h_p={h_p_ft:g} ft: delta_w={delta_w:.3f} outside "
                           f"{DELTA_W_RANGE[0]}-{DELTA_W_RANGE[1]}")
            continue
        q_prod, was_interp = _producing_rate_at(producing_rate, eps)
        if q_prod is None:
            dropped.append(f"h_p={h_p_ft:g} ft: b/h={eps:.3f} outside the supplied "
                           "producing-rate table (no extrapolation)")
            continue
        interpolated = interpolated or was_interp
        q_crit = _critical_rate_stb_d(h_ft, delta_rho_og, b_o_rb_stb, mu_o_cp,
                                      k_ro, k_h_md, psi_opt)   # Step 6, Eq. 9-10
        table.append({
            "h_p_ft": h_p_ft, "epsilon": eps, "psi_opt": psi_opt,
            "delta_g_opt": delta_g_opt, "D_t_ft": d_t_ft, "D_b_ft": d_b_ft,
            "delta_w": delta_w, "Q_crit_stb_d": q_crit,
            "Q_producing_stb_d": q_prod, "Q_achievable_stb_d": min(q_crit, q_prod),
        })

    if not table:
        return Refusal(
            reason=("no candidate perforated length survived the Chierici validity "
                    "limits or the supplied producing-rate span: " + "; ".join(dropped)),
            needed=("chart readings within 0 < epsilon <= 0.75, "
                    "0.07 <= delta <= 0.9, covered by the producing-rate curve",),
            source=CHIERICI_DEFS)

    # Ahmed's Step 8: the well delivers min(coning limit, deliverability) at each
    # penetration; the optimum is the sampled point maximising that.
    best_i = max(range(len(table)), key=lambda i: table[i]["Q_achievable_stb_d"])
    best = table[best_i]

    flags = [EQ_DISCREPANCY]
    if dropped:
        flags.append("candidates dropped: " + "; ".join(dropped))
    if interpolated:
        flags.append("producing rate linearly interpolated between supplied b/h points")
    if r_de not in CHART_FAMILIES:
        flags.append(f"r_De = {r_de:.2f} is not a chart family; readings were expected "
                     f"from {_bracketing_charts(r_de)}")
    # "Edge of the grid" is the smallest or largest h_p supplied, not the first
    # or last reading handed in: chart_readings need not arrive sorted, and
    # keying this off list position silently loses the flag when they do not.
    grid = [row["h_p_ft"] for row in table]
    if len(table) > 1 and best["h_p_ft"] in (min(grid), max(grid)):
        flags.append("the optimum sits at the edge of the supplied h_p grid; the true "
                     "crossing may lie outside it — extend the grid and re-run")
    if best["Q_crit_stb_d"] <= best["Q_producing_stb_d"]:
        flags.append("coning-limited at the optimum: the well could flow "
                     f"{best['Q_producing_stb_d']:.0f} STB/day but would cone")
    else:
        flags.append("deliverability-limited at the optimum: the coning limit is "
                     f"{best['Q_crit_stb_d']:.0f} STB/day, above what the well can flow")

    return Quantity(
        best["Q_achievable_stb_d"], "STB/day",
        "Chierici-Ciucci optimum completion interval (Ahmed Ch. 9, Eqs. 9-5 to 9-10)",
        CHIERICI_OPT,
        inputs={
            "h_ft": h_ft, "r_e_ft": r_e_ft, "k_h_md": k_h_md, "k_v_md": k_v_md,
            "k_ro": k_ro, "B_o_rb_stb": b_o_rb_stb, "mu_o_cp": mu_o_cp,
            "rho_o_lb_ft3": rho_o_lb_ft3, "rho_w_lb_ft3": rho_w_lb_ft3,
            "rho_g_lb_ft3": rho_g_lb_ft3,
            "r_De": r_de, "delta_rho_ow": delta_rho_ow, "delta_rho_og": delta_rho_og,
            "delta_rho_ratio": ratio,
            "h_p_ft": best["h_p_ft"], "epsilon": best["epsilon"],
            "psi_opt": best["psi_opt"], "delta_g_opt": best["delta_g_opt"],
            "D_t_ft": best["D_t_ft"], "D_b_ft": best["D_b_ft"],
            "delta_w": best["delta_w"],
            "Q_crit_stb_d": best["Q_crit_stb_d"],
            "Q_producing_stb_d": best["Q_producing_stb_d"],
            "table": table,
        },
        assumptions={
            "coefficient": CRITICAL_RATE_COEFF,
            "critical_rate_equation": "Eq. 9-10 (rho_o - rho_g), per Example 9-6 arithmetic",
            "selection_rule": "max over sampled h_p of min(critical rate, producing rate)",
            "producing_rate_source": "injected; intended supplier is "
                                     "partial_penetration_rate (#51, Kozeny)",
            "psi_source": f"read from {_bracketing_charts(r_de)} (chart, no closed form)",
            "formation": HOMOGENEOUS_ONLY,
            "depth_convention": TRUE_VERTICAL_ONLY,
        },
        flags=tuple(flags))


# ---------------------------------------------------------------------------
# #51  partial_penetration_rate — Kozeny
# ---------------------------------------------------------------------------

# SPE, "Water and gas coning", print-to-PDF capture. Eq. 14 and the nomenclature
# under it are at #4 (p. 14 of 21); Example 2, Table 9.28 and the b = 60 ft
# substitution are at #5 (p. 17). The HTML capture of the same page
# (04-coning/onepetro-water-and-gas-coning) lost Eq. 14 to image conversion — it
# renders as an RTENOTITLE placeholder, one of 29 in that file — and the
# pge-blog mirror lost it entirely. The print capture is the only copy in the
# corpus that carries the math, and its OCR was checked against the rendered
# page image at 200 dpi before anything here was written.
KOZENY_EQ = "04-coning/onepetro-water-and-gas-coning-print#4"
KOZENY_EXAMPLE = "04-coning/onepetro-water-and-gas-coning-print#5"

# Coefficient of Eq. 14, for q in STB/D with k in md, b and h in ft, p in psi,
# mu in cp, B_o in RB/STB. Same constant as the steady-state radial Darcy
# equation it degenerates to at b = h (Ahmed Eq. 6-27).
DARCY_COEFF = 0.00708
# Coefficient of the partial-penetration correction, Eq. 14's bracket.
KOZENY_BRACKET_COEFF = 7.0

# Eq. 14 as printed does not reproduce the source's own Table 9.28. Both printed
# renderings of the equation agree with each other (the display equation at #4
# and the worked substitution "(1.11 cp)(1.25 RB/STB)(ln 933/0.5 + 10)" at #5),
# and both were confirmed on the page image rather than trusted from OCR. Only
# the numbers dissent, and they dissent by a constant factor on all ten rows:
# ln(r_e/r_w) - 0.5 + s reproduces the table to four significant figures
# throughout. That -0.5 appears in no document in this corpus, so it is not
# implemented; shipping an equation no source states is the one outcome this
# build forbids outright. See specs/51-partial_penetration_rate.md.
SOURCE_TABLE_DISCREPANCY = (
    "source discrepancy: Eq. 14 as printed gives 417.52 STB/D for the source's own "
    "Example 2 (b = 60 ft), where the source prints 430 STB/D; every row of Table "
    "9.28 is high by the same 2.93%, reproducible only with an unprinted -0.5 in "
    "the denominator. The equation as printed is implemented; rates from this tool "
    "run ~2.9% below the source's tabulated column"
)

KOZENY_ASSUMPTIONS = {
    "flow_regime": "steady-state flow in a circular drainage area (source, #4)",
    "units": "md, ft, psi, cp, STB/D (stated by the source; do not mix)",
    "cosine_argument": "radians (stated by the source)",
    "darcy_coefficient": DARCY_COEFF,
    "bracket_coefficient": KOZENY_BRACKET_COEFF,
    "method_spread": "the source notes several authors offer expressions for this rate "
                     "and that 'most efforts yield estimates within a few percent of "
                     "one another'; only Kozeny is printed, so there is nothing here "
                     "to reconcile against",
}


def _kozeny_terms(b_ft: float, h_ft: float, k_h_md: float, k_v_md: float,
                  r_e_ft: float, r_w_ft: float, p_e_psi: float, p_w_psi: float,
                  mu_o_cp: float, b_o_rb_stb: float, skin: float,
                  ) -> tuple[float, float, float]:
    """Return (Darcy prefactor STB/D, partial-penetration bracket, ln(r_e/r_w)).

    Eq. 14 split at its own multiplication sign so both halves can be reported.
    Note the *nested* radical: the whole of (r_w/2b)·sqrt(k_v/k_H) sits under the
    outer square root. Reading it as sqrt(r_w/2b)·sqrt(k_v/k_H) is a plausible
    slip and gives 407.0 rather than 417.5 STB/D on the source's own example.
    """
    ln_re_rw = math.log(r_e_ft / r_w_ft)
    prefactor = (DARCY_COEFF * k_h_md * b_ft * (p_e_psi - p_w_psi)
                 / (mu_o_cp * b_o_rb_stb * (ln_re_rw + skin)))
    bracket = 1.0 + KOZENY_BRACKET_COEFF * math.sqrt(
        (r_w_ft / (2.0 * b_ft)) * math.sqrt(k_v_md / k_h_md)
    ) * math.cos(math.pi * b_ft / (2.0 * h_ft))
    return prefactor, bracket, ln_re_rw


def partial_penetration_rate(
    b_ft: float,
    h_ft: float,
    k_h_md: float,
    k_v_md: float,
    r_e_ft: float,
    r_w_ft: float,
    p_e_psi: float,
    p_w_psi: float,
    mu_o_cp: float,
    b_o_rb_stb: float,
    skin: float,
):
    """Theoretical producing rate of a partially perforated well. Kozeny, Eq. 14.

        q = 0.00708 k_H b (p_e - p_w) / (mu_o B_o [ln(r_e/r_w) + s])
            · [1 + 7 sqrt((r_w/2b) sqrt(k_v/k_H)) cos(pi b / 2h)]

    `b_ft` is the perforated (open) interval, `h_ft` the net formation thickness.
    `skin` has no default: a silent s = 0 would be an invented input.

    Returns STB/day. This is the deliverability half of the perforation
    optimisation — the curve `perf_length_optimize` (#50) takes as
    `producing_rate` — and every result carries the flag naming the source's own
    2.93% table discrepancy. Refuses where the arithmetic has no meaning: b > h,
    no drawdown, or a skin more negative than ln(r_e/r_w).
    """
    if h_ft <= 0:
        raise ValueError("h_ft must be positive")
    if b_ft < 0:
        raise ValueError("b_ft must not be negative")
    if k_h_md <= 0 or k_v_md <= 0:
        raise ValueError("k_h_md and k_v_md must be positive")
    if r_e_ft <= 0 or r_w_ft <= 0:
        raise ValueError("r_e_ft and r_w_ft must be positive")
    if r_e_ft <= r_w_ft:
        raise ValueError("r_e_ft must exceed r_w_ft")
    if mu_o_cp <= 0 or b_o_rb_stb <= 0:
        raise ValueError("mu_o_cp and b_o_rb_stb must be positive")

    common = {
        "b_ft": b_ft, "h_ft": h_ft, "k_h_md": k_h_md, "k_v_md": k_v_md,
        "r_e_ft": r_e_ft, "r_w_ft": r_w_ft, "p_e_psi": p_e_psi,
        "p_w_psi": p_w_psi, "mu_o_cp": mu_o_cp, "B_o_rb_stb": b_o_rb_stb,
        "skin": skin, "b_over_h": b_ft / h_ft,
    }

    if b_ft > h_ft:
        return Refusal(
            reason=(f"perforated interval b = {b_ft:g} ft exceeds the formation "
                    f"thickness h = {h_ft:g} ft; past b = h the cosine turns negative "
                    "and Eq. 14's correction starts subtracting, which has no physical "
                    "reading, and the source's own tables stop at b/h = 1"),
            needed=("b_ft <= h_ft",),
            source=KOZENY_EQ)

    drawdown = p_e_psi - p_w_psi
    if drawdown <= 0:
        return Refusal(
            reason=(f"p_e = {p_e_psi:g} psi is not above p_w = {p_w_psi:g} "
                    "psi, so the steady-state productivity relation Eq. 14 describes "
                    "does not apply"),
            needed=("p_e_psi > p_w_psi",),
            source=KOZENY_EQ)

    ln_re_rw = math.log(r_e_ft / r_w_ft)
    if ln_re_rw + skin <= 0:
        return Refusal(
            reason=(f"the denominator of Eq. 14 is not positive: ln(r_e/r_w) = "
                    f"{ln_re_rw:.4f} with skin = {skin:g} gives {ln_re_rw + skin:.4f}; "
                    "a skin more negative than the geometric term makes the rate "
                    "infinite or negative"),
            needed=("ln(r_e/r_w) + skin > 0",),
            source=KOZENY_EQ)

    if b_ft == 0:
        # Eq. 14 is 0/0 here — the prefactor falls linearly in b, the bracket
        # grows as b^-1/2, and the product tends to zero. Table 9.28 prints 0.0
        # for its b/h = 0 row, so the value is the source's, not an assumption.
        return Quantity(
            0.0, "STB/day",
            "Kozeny partial-penetration rate (SPE Eq. 14), degenerate b = 0",
            KOZENY_EQ,
            inputs={**common, "ln_re_rw": ln_re_rw,
                    "denominator": mu_o_cp * b_o_rb_stb * (ln_re_rw + skin),
                    "darcy_term_stb_d": 0.0, "partial_penetration_factor": None},
            assumptions=dict(KOZENY_ASSUMPTIONS),
            flags=(SOURCE_TABLE_DISCREPANCY,
                   "b = 0: no perforated interval, so no rate. Eq. 14 is 0/0 at this "
                   "point and the value is the limit, which is what Table 9.28 prints "
                   "for its b/h = 0 row"))

    prefactor, bracket, ln_re_rw = _kozeny_terms(
        b_ft, h_ft, k_h_md, k_v_md, r_e_ft, r_w_ft,
        p_e_psi, p_w_psi, mu_o_cp, b_o_rb_stb, skin)
    value = prefactor * bracket
    # The same well fully perforated: Eq. 14 at b = h, where cos(pi/2) = 0 and
    # the bracket is 1. Opening less of the pay cannot produce more oil, so this
    # is a ceiling the correlation must respect and sometimes does not.
    full_penetration_stb_d = (DARCY_COEFF * k_h_md * h_ft * drawdown
                              / (mu_o_cp * b_o_rb_stb * (ln_re_rw + skin)))

    flags = [SOURCE_TABLE_DISCREPANCY]
    if value > full_penetration_stb_d:
        # Kozeny's bracket grows as b^-1/2 while the prefactor falls only as b,
        # so for a large enough r_w/h the correction outruns the pay it is
        # correcting: a 0.5 ft wellbore in 20 ft of pay peaks near b/h = 0.8 at
        # a rate above the fully perforated one. The source prints no range over
        # which the correction is stated to hold and none is invented here, so
        # this is reported rather than refused — but a caller feeding this into
        # perf_length_optimize (#50) would get an optimum off a curve that is
        # not physical. See specs/51-partial_penetration_rate.md, open question 2.
        flags.append(
            f"non-physical regime: Eq. 14 gives {value:.2f} STB/day at b = "
            f"{b_ft:g} ft, above the {full_penetration_stb_d:.2f} STB/day the "
            f"same well gives fully perforated (b = h = {h_ft:g} ft); opening "
            "less pay cannot produce more oil. Kozeny's correction is a "
            "pseudo-skin approximation and this well (r_w/h = "
            f"{r_w_ft / h_ft:.4g}, b/h = {b_ft / h_ft:.4g}) is outside where it "
            "behaves; the source states no validity range, so this is flagged "
            "and not refused")
    if b_ft == h_ft:
        flags.append("b = h: fully penetrating, cos(pi/2) = 0 and Eq. 14 degenerates "
                     "to the steady-state radial Darcy equation")
    if k_v_md > k_h_md:
        flags.append(f"k_v = {k_v_md:g} md exceeds k_h = {k_h_md:g} md, which is "
                     "unusual; the source states no limit on the ratio, so this is "
                     "reported rather than refused")

    return Quantity(
        value, "STB/day",
        "Kozeny partial-penetration producing rate (SPE 'Water and gas coning', Eq. 14)",
        KOZENY_EQ,
        inputs={**common, "drawdown_psi": drawdown, "ln_re_rw": ln_re_rw,
                "denominator": mu_o_cp * b_o_rb_stb * (ln_re_rw + skin),
                "darcy_term_stb_d": prefactor,
                "partial_penetration_factor": bracket,
                "full_penetration_stb_d": full_penetration_stb_d},
        assumptions=dict(KOZENY_ASSUMPTIONS),
        flags=tuple(flags))


def partial_penetration_rate_curve(
    b_over_h_values: Sequence[float],
    h_ft: float,
    k_h_md: float,
    k_v_md: float,
    r_e_ft: float,
    r_w_ft: float,
    p_e_psi: float,
    p_w_psi: float,
    mu_o_cp: float,
    b_o_rb_stb: float,
    skin: float,
):
    """Kozeny rate across a range of fractional penetrations b/h.

    The curve `perf_length_optimize` (#50) consumes as `producing_rate`. Returns
    a `Range` spanning the rates, with one `members` entry per requested b/h
    keyed by the fraction as a numeric string; `curve_points` turns that into the
    `(b_over_h, q_stb_d)` pairs #50 accepts. Refuses for the whole curve if any
    single point would refuse — a curve with a hole in it would be read as a
    complete one.
    """
    values = [float(v) for v in b_over_h_values]
    if not values:
        return Refusal(
            reason="no b/h values supplied, so there is no curve to evaluate",
            needed=("a non-empty sequence of fractional penetrations b/h",),
            source=KOZENY_EQ)
    for v in values:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"b_over_h must lie in [0, 1]; got {v}")

    members: dict[str, float] = {}
    for v in sorted(set(values)):
        one = partial_penetration_rate(
            v * h_ft, h_ft, k_h_md, k_v_md, r_e_ft, r_w_ft,
            p_e_psi, p_w_psi, mu_o_cp, b_o_rb_stb, skin)
        if isinstance(one, Refusal):
            return Refusal(
                reason=f"the curve cannot be evaluated at b/h = {v:g}: {one.reason}",
                needed=one.needed,
                source=one.source)
        members[f"{v:g}"] = one.value

    rates = list(members.values())
    return Range(
        min(rates), max(rates), "STB/day",
        "Kozeny partial-penetration producing rate across b/h "
        "(SPE 'Water and gas coning', Eq. 14)",
        KOZENY_EQ,
        members=members)


def curve_points(curve: Range) -> list[tuple[float, float]]:
    """Adapt a `partial_penetration_rate_curve` Range into #50's point form.

    Not a tool — an adapter, and the only reason it exists is that
    `perf_length_optimize` documents `producing_rate` as "a sequence of
    (b_over_h, q_stb_d) points" and `Range.members` is keyed by string. Returning
    a list of pairs rather than a `Quantity` is deliberate: it is a shape
    conversion, and every number in it already came from a `Quantity`.
    """
    return sorted((float(k), v) for k, v in curve.members.items())


# ---------------------------------------------------------------------------
# #58  perf_standoff_check
# ---------------------------------------------------------------------------

# Depth-registry allowance on net-pay membership. tool-catalog.md, section
# "Thresholds the corpus does not supply", marks this PROVISIONAL *with a basis*:
# asquith#64 states a log suite generally needs more than one logging run and
# "some logs differ slightly in depth-registry of beds", so the tolerance is set
# by log mechanics rather than by taste. It is a default, not a constant, and
# every result says it is provisional.
PERF_IN_ZONE_TOLERANCE_FT = 2.0
CATALOG_THRESHOLDS = ('tool-catalog.md, "Thresholds the corpus does not supply"')

PROVISIONAL_TOLERANCE = (
    f"net-pay membership allows a depth-registry tolerance of "
    f"{PERF_IN_ZONE_TOLERANCE_FT:g} ft, which is PROVISIONAL per {CATALOG_THRESHOLDS} "
    "(basis: asquith#64, logs from different runs differ in depth registry). It is "
    "overridable and it is not applied to the washout intervals"
)
# Neither of these appears in the corpus or in the catalog's threshold table, so
# per that table's own definition — "CALLER means the tool refuses to run without
# being told" — they are arguments with no default.
NO_WASHOUT_CUTOFF = (
    "no source in the corpus states how much washed-out hole disqualifies a "
    "perforated interval, and the catalog's threshold table does not list one"
)
NO_NET_PAY_CUTOFF = (
    "no source in the corpus states what fraction of a perforated interval must be "
    "net pay, and the catalog's threshold table does not list one"
)

# Ahmed's bands police *his correlation*, not perforating in general. Failing one
# does not predict coning; it says Chierici's charts cannot speak to this well.
BANDS_ARE_CORRELATION_LIMITS = (
    "the epsilon/delta bounds are the validity limits of the Chierici-Ciucci "
    "graphical correlation (Ahmed pp. 582-583), not a prediction that the well will "
    "cone; a FAIL means the charts cannot answer for this geometry"
)

# A contact from `contact_project` (#21) is a projection from another wellbore,
# not a measurement at this one, and `tool-catalog.md` specifies the standoff it
# feeds (#22 `standoff_compute`) as "carried with its uncertainty range". So the
# uncertainty is an input here, not a constant: no number is invented, and when
# the caller states one the bands are evaluated over the whole interval it
# implies rather than at the projected depth alone. A verdict that could flip
# inside the caller's own uncertainty is reported as INDETERMINATE, never as a
# crisp PASS.
CONTACT_UNCERTAINTY_ABSENT = (
    "contacts treated as exact: no contact_uncertainty_ft was supplied, so every "
    "band was evaluated at the projected contact depth alone. A contact from "
    "contact_project (#21) is a projection, not a measurement — pass its "
    "uncertainty to get a verdict that survives it"
)
VERDICT_PASS = "verdict: PASS"
VERDICT_FAIL = "verdict: FAIL"
VERDICT_INDETERMINATE = "verdict: INDETERMINATE"


def _ratio_interval(num: tuple[float, float],
                    den: tuple[float, float]) -> tuple[float, float]:
    """Interval of num/den over both intervals. `den` must not straddle zero.

    Corner evaluation rather than a sign analysis: the numerator may be negative
    (perforations past a contact) and the quotient is monotone in each argument,
    so the extremes are at the corners.
    """
    corners = [n / d for n in num for d in den]
    return min(corners), max(corners)


def _band_status(interval: tuple[float, float],
                 band: tuple[float, float]) -> str:
    """"pass" / "fail" / "indeterminate" for an interval against a closed band.

    Decided only when the whole interval falls on one side. With a zero-width
    interval — the no-uncertainty case — this is the plain membership test.
    """
    lo, hi = interval
    if band[0] <= lo and hi <= band[1]:
        return "pass"
    if hi < band[0] or lo > band[1]:
        return "fail"
    return "indeterminate"


def _merge_intervals(intervals: Iterable[Sequence[float]]) -> list[tuple[float, float]]:
    """Merge overlapping (top, base) depth pairs so footage is never double-counted."""
    pairs: list[tuple[float, float]] = []
    for iv in intervals:
        top, base = (float(v) for v in iv)
        if top > base:
            raise ValueError(f"interval ({top}, {base}) has its top below its base")
        pairs.append((top, base))
    pairs.sort()
    merged: list[tuple[float, float]] = []
    for top, base in pairs:
        if merged and top <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], base))
        else:
            merged.append((top, base))
    return merged


def _overlap_ft(a: tuple[float, float], intervals: Sequence[tuple[float, float]]) -> float:
    return sum(max(0.0, min(a[1], base) - max(a[0], top)) for top, base in intervals)


def perf_standoff_check(
    perf_top_ft: float,
    perf_base_ft: float,
    k_h_md: float,
    k_v_md: float,
    r_e_ft: float,
    goc_ft: float | None = None,
    woc_ft: float | None = None,
    h_ft: float | None = None,
    washout_intervals_ft: Sequence[Sequence[float]] | None = None,
    net_pay_intervals_ft: Sequence[Sequence[float]] | None = None,
    max_washout_overlap_frac: float | None = None,
    min_net_pay_frac: float | None = None,
    depth_registry_tolerance_ft: float = PERF_IN_ZONE_TOLERANCE_FT,
    contact_uncertainty_ft: float | None = None,
):
    """Validate a proposed perforated interval. Chierici geometry, Ahmed pp. 581-584.

    Three questions with three evidentiary statuses. The contact geometry is
    sourced: Ahmed prints 5 <= r_De <= 80, 0 <= epsilon <= 0.75 and
    0.07 <= delta <= 0.9, and those bands are checked and cited. The washout and
    net-pay halves are not sourced anywhere, so `max_washout_overlap_frac` and
    `min_net_pay_frac` have no defaults and the tool refuses without them; the
    overlap and coverage are still measured and reported, because those are facts.

    Depths increase downward in one consistent reference — Chierici's geometry is
    vertical distance, so TVD or TVDSS, not MD in a deviated well.
    `washout_intervals_ft` comes from `hole_quality` (#25) and
    `net_pay_intervals_ft` from `net_pay_cutoffs` (#39); an empty sequence means
    "none found" and is accepted, `None` means "not evaluated" and is refused.

    `contact_uncertainty_ft` is the +/- uncertainty on the projected contacts,
    caller-supplied with no default because no source states one. Given it, the
    bands are evaluated over the whole interval it implies and a verdict that
    could flip inside it comes back `verdict: INDETERMINATE` rather than PASS.

    Returns the governing standoff in ft — min(D_t, D_b), negative if the
    perforations are past a contact — with `verdict: PASS`, `verdict: FAIL` or
    `verdict: INDETERMINATE` first on `flags` and one flag per failed or
    undecidable check.
    """
    if perf_top_ft >= perf_base_ft:
        raise ValueError("perf_top_ft must be above perf_base_ft (depth increases down)")
    if k_h_md <= 0 or k_v_md <= 0:
        raise ValueError("k_h_md and k_v_md must be positive")
    if r_e_ft <= 0:
        raise ValueError("r_e_ft must be positive")
    if depth_registry_tolerance_ft < 0:
        raise ValueError("depth_registry_tolerance_ft must not be negative")
    for name, frac in (("max_washout_overlap_frac", max_washout_overlap_frac),
                       ("min_net_pay_frac", min_net_pay_frac)):
        if frac is not None and not 0.0 <= float(frac) <= 1.0:
            raise ValueError(f"{name} must lie in [0, 1]; got {frac}")
    if h_ft is not None and h_ft <= 0:
        raise ValueError("h_ft must be positive")
    if contact_uncertainty_ft is not None and float(contact_uncertainty_ft) < 0:
        raise ValueError("contact_uncertainty_ft must not be negative")

    h_p_ft = perf_base_ft - perf_top_ft

    if goc_ft is None and woc_ft is None:
        return Refusal(
            reason=("no fluid contact supplied, so there is nothing to stand off from; "
                    "this tool checks a perforated interval against the projected "
                    "gas-oil and/or water-oil contact"),
            needed=("goc_ft and/or woc_ft, from contact_project (#21)",),
            source=CHIERICI_DEFS)

    if goc_ft is not None and woc_ft is not None:
        if goc_ft >= woc_ft:
            return Refusal(
                reason=(f"the contacts are not ordered gas above water "
                        f"(GOC = {goc_ft:g} ft, WOC = {woc_ft:g} ft); the oil column "
                        "and Chierici's geometry are undefined"),
                needed=("goc_ft < woc_ft in a depth-increases-downward reference",),
                source=CHIERICI_DEFS)
        derived_h = woc_ft - goc_ft
        if h_ft is not None and abs(h_ft - derived_h) > depth_registry_tolerance_ft:
            return Refusal(
                reason=(f"h_ft = {h_ft:g} ft disagrees with the contacts, which give "
                        f"WOC - GOC = {derived_h:g} ft, by more than the "
                        f"{depth_registry_tolerance_ft:g} ft registry tolerance; two "
                        "sources of truth for the oil column that disagree is the "
                        "finding, not something to average"),
                needed=("a reconciled oil column: either the contacts or h_ft is wrong",),
                source=CHIERICI_DEFS)
        column_h = derived_h
        h_source = "derived from the contacts (WOC - GOC), per Ahmed Example 9-5 Step 2"
    else:
        if h_ft is None:
            missing = "GOC" if goc_ft is None else "WOC"
            return Refusal(
                reason=(f"only one contact was supplied (the {missing} is missing) and "
                        "h_ft was not given, so the oil column thickness Chierici's "
                        "dimensionless groups divide by cannot be derived"),
                needed=("h_ft, or the missing contact from contact_project (#21), "
                        "or column_height (#23)",),
                source=CHIERICI_DEFS)
        column_h = float(h_ft)
        h_source = "supplied by the caller; only one contact is known"

    if washout_intervals_ft is None:
        return Refusal(
            reason=("washout intervals were not supplied; this tool will not report a "
                    "verdict that silently skipped the hole-quality half. Pass an empty "
                    "sequence to state that none were found"),
            needed=("washout_intervals_ft from hole_quality (#25), "
                    "or [] to state that there are none",),
            source=CHIERICI_DEFS)
    if net_pay_intervals_ft is None:
        return Refusal(
            reason=("net-pay intervals were not supplied; this tool will not report a "
                    "verdict that silently skipped the net-pay half. Pass an empty "
                    "sequence to state that none were found"),
            needed=("net_pay_intervals_ft from net_pay_cutoffs (#39), "
                    "or [] to state that there are none",),
            source=CHIERICI_DEFS)
    if max_washout_overlap_frac is None:
        return Refusal(
            reason=(NO_WASHOUT_CUTOFF + ", so it is CALLER and this tool will not "
                    "default one. State the fraction of the proposed interval that may "
                    "sit in washed-out hole"),
            needed=("max_washout_overlap_frac (0-1), stated by the caller",),
            source=CATALOG_THRESHOLDS)
    if min_net_pay_frac is None:
        return Refusal(
            reason=(NO_NET_PAY_CUTOFF + ", so it is CALLER and this tool will not "
                    "default one. State the fraction of the proposed interval that must "
                    "be net pay"),
            needed=("min_net_pay_frac (0-1), stated by the caller",),
            source=CATALOG_THRESHOLDS)

    # Contact uncertainty. Zero when the caller states none, which collapses every
    # interval below to a point and leaves the arithmetic exactly as it was.
    u_ft = 0.0 if contact_uncertainty_ft is None else float(contact_uncertainty_ft)
    # Each contact moves independently, so an h derived from both moves by 2u. An
    # h the caller stated is theirs, not derived, and is not perturbed here.
    if goc_ft is not None and woc_ft is not None:
        h_interval = (column_h - 2.0 * u_ft, column_h + 2.0 * u_ft)
    else:
        h_interval = (column_h, column_h)
    if h_interval[0] <= 0:
        return Refusal(
            reason=(f"a contact uncertainty of +/-{u_ft:g} ft spans the whole "
                    f"{column_h:g} ft oil column, so h could be zero or inverted and "
                    "none of Chierici's dimensionless groups can be formed"),
            needed=("a contact uncertainty smaller than half the oil column, "
                    "or better-constrained contacts from contact_project (#21)",),
            source=CHIERICI_DEFS)

    r_de = _effective_dimensionless_radius(r_e_ft, column_h, k_h_md, k_v_md)  # Eq. 9-5
    if not R_DE_RANGE[0] <= r_de <= R_DE_RANGE[1]:
        return Refusal(
            reason=(f"effective dimensionless radius r_De = {r_de:.2f} is outside the "
                    f"{R_DE_RANGE[0]:.0f}-{R_DE_RANGE[1]:.0f} range the Chierici "
                    "correlation is stated to be valid over (Ahmed p. 582), so its "
                    "bounds cannot be applied to this completion at all"),
            needed=("a coning method valid outside 5 <= r_De <= 80",),
            source=CHIERICI_DEFS)

    epsilon = h_p_ft / column_h                                  # Eq. 9-6
    d_t_ft = None if goc_ft is None else perf_top_ft - goc_ft
    d_b_ft = None if woc_ft is None else woc_ft - perf_base_ft
    delta_g = None if d_t_ft is None else d_t_ft / column_h      # Eq. 9-7
    delta_w = None if d_b_ft is None else d_b_ft / column_h      # Eq. 9-8

    # r_De falls as h rises, so the interval runs the other way from h's.
    k_ratio = (k_h_md / k_v_md) ** 0.5
    r_de_interval = (r_e_ft / h_interval[1] * k_ratio, r_e_ft / h_interval[0] * k_ratio)
    epsilon_interval = _ratio_interval((h_p_ft, h_p_ft), h_interval)
    delta_g_interval = (None if d_t_ft is None else
                        _ratio_interval((d_t_ft - u_ft, d_t_ft + u_ft), h_interval))
    delta_w_interval = (None if d_b_ft is None else
                        _ratio_interval((d_b_ft - u_ft, d_b_ft + u_ft), h_interval))

    failures: list[str] = []
    undecided: list[str] = []
    skipped: list[str] = []

    def _spread(label: str, interval: tuple[float, float]) -> str:
        return (f"{label} could be anywhere in {interval[0]:.4f}-{interval[1]:.4f} "
                f"under the caller's +/-{u_ft:g} ft contact uncertainty")

    if _band_status(r_de_interval, R_DE_RANGE) == "indeterminate" and u_ft > 0:
        undecided.append(_spread(f"r_De = {r_de:.4f}", r_de_interval)
                         + f", which crosses the {R_DE_RANGE[0]:.0f}-"
                           f"{R_DE_RANGE[1]:.0f} validity range (Ahmed Eq. 9-5, p. 582)")

    eps_status = _band_status(epsilon_interval, (0.0, EPSILON_MAX))
    if epsilon <= 0 or eps_status == "fail":
        failures.append(f"epsilon = h_p/h = {epsilon:.4f} is outside 0 < e <= "
                        f"{EPSILON_MAX} (Ahmed Eq. 9-6, p. 582)")
    elif eps_status == "indeterminate":
        undecided.append(_spread(f"epsilon = h_p/h = {epsilon:.4f}", epsilon_interval)
                         + f", which crosses the 0-{EPSILON_MAX} band "
                           "(Ahmed Eq. 9-6, p. 582)")

    if delta_g is None:
        skipped.append("gas-side check skipped: no GOC supplied")
    else:
        status = _band_status(delta_g_interval, DELTA_G_RANGE)
        extra = (" — the perforations lie above the GOC, i.e. in the gas cap"
                 if d_t_ft < 0 else "")
        if status == "fail":
            failures.append(f"delta_g = D_t/h = {delta_g:.4f} (D_t = {d_t_ft:g} ft) is "
                            f"outside {DELTA_G_RANGE[0]}-{DELTA_G_RANGE[1]} "
                            f"(Ahmed Eq. 9-7, p. 583){extra}")
        elif status == "indeterminate":
            undecided.append(
                _spread(f"delta_g = D_t/h = {delta_g:.4f} (D_t = {d_t_ft:g} ft)",
                        delta_g_interval)
                + f", which crosses the {DELTA_G_RANGE[0]}-{DELTA_G_RANGE[1]} band "
                  f"(Ahmed Eq. 9-7, p. 583){extra}")
    if delta_w is None:
        skipped.append("water-side check skipped: no WOC supplied")
    else:
        status = _band_status(delta_w_interval, DELTA_W_RANGE)
        extra = (" — the perforations lie below the WOC, i.e. in the aquifer"
                 if d_b_ft < 0 else "")
        if status == "fail":
            failures.append(f"delta_w = D_b/h = {delta_w:.4f} (D_b = {d_b_ft:g} ft) is "
                            f"outside {DELTA_W_RANGE[0]}-{DELTA_W_RANGE[1]} "
                            f"(Ahmed Eq. 9-8, p. 583){extra}")
        elif status == "indeterminate":
            undecided.append(
                _spread(f"delta_w = D_b/h = {delta_w:.4f} (D_b = {d_b_ft:g} ft)",
                        delta_w_interval)
                + f", which crosses the {DELTA_W_RANGE[0]}-{DELTA_W_RANGE[1]} band "
                  f"(Ahmed Eq. 9-8, p. 583){extra}")

    perf = (perf_top_ft, perf_base_ft)
    washouts = _merge_intervals(washout_intervals_ft)
    washout_overlap_ft = _overlap_ft(perf, washouts)
    washout_frac = washout_overlap_ft / h_p_ft
    if washout_frac > float(max_washout_overlap_frac):
        failures.append(f"{washout_overlap_ft:g} ft of the {h_p_ft:g} ft interval "
                        f"({washout_frac:.3f}) sits in washed-out hole, above the "
                        f"caller's limit of {float(max_washout_overlap_frac):.3f} "
                        f"({NO_WASHOUT_CUTOFF})")

    tol = float(depth_registry_tolerance_ft)
    widened = _merge_intervals(
        (float(top) - tol, float(base) + tol) for top, base in net_pay_intervals_ft)
    net_pay_covered_ft = _overlap_ft(perf, widened)
    net_pay_frac = net_pay_covered_ft / h_p_ft
    if net_pay_frac < float(min_net_pay_frac):
        failures.append(f"{net_pay_covered_ft:g} ft of the {h_p_ft:g} ft interval "
                        f"({net_pay_frac:.3f}) is net pay, below the caller's minimum "
                        f"of {float(min_net_pay_frac):.3f} ({NO_NET_PAY_CUTOFF})")

    standoffs = [d for d in (d_t_ft, d_b_ft) if d is not None]
    governing = min(standoffs)

    if failures:
        verdict = VERDICT_FAIL
    elif undecided:
        verdict = VERDICT_INDETERMINATE
    else:
        verdict = VERDICT_PASS
    flags = [verdict]
    flags.extend(failures)
    flags.extend(undecided)
    flags.extend(skipped)
    if contact_uncertainty_ft is None:
        flags.append(CONTACT_UNCERTAINTY_ABSENT)
    flags.append(PROVISIONAL_TOLERANCE)
    flags.append(BANDS_ARE_CORRELATION_LIMITS)
    flags.append(HOMOGENEOUS_ONLY)

    return Quantity(
        governing, "ft",
        "Chierici-Ciucci perforation geometry check (Ahmed Ch. 9, Eqs. 9-5 to 9-8)",
        CHIERICI_DEFS,
        inputs={
            "perf_top_ft": perf_top_ft, "perf_base_ft": perf_base_ft,
            "h_p_ft": h_p_ft, "goc_ft": goc_ft, "woc_ft": woc_ft,
            "h_ft": column_h, "k_h_md": k_h_md, "k_v_md": k_v_md, "r_e_ft": r_e_ft,
            "D_t_ft": d_t_ft, "D_b_ft": d_b_ft,
            "r_De": r_de, "epsilon": epsilon,
            "delta_g": delta_g, "delta_w": delta_w,
            "contact_uncertainty_ft": contact_uncertainty_ft,
            "governing_standoff_range_ft": (governing - u_ft, governing + u_ft),
            "h_range_ft": h_interval,
            "r_De_range": r_de_interval,
            "epsilon_range": epsilon_interval,
            "delta_g_range_computed": delta_g_interval,
            "delta_w_range_computed": delta_w_interval,
            "washout_overlap_ft": washout_overlap_ft,
            "washout_overlap_frac": washout_frac,
            "net_pay_covered_ft": net_pay_covered_ft,
            "net_pay_frac": net_pay_frac,
            "washout_intervals_ft": washouts,
            "net_pay_intervals_ft": _merge_intervals(net_pay_intervals_ft),
        },
        assumptions={
            "r_De_range": R_DE_RANGE,
            "epsilon_max": EPSILON_MAX,
            "delta_g_range": DELTA_G_RANGE,
            "delta_w_range": DELTA_W_RANGE,
            "bounds_source": f"{CHIERICI_DEFS} (Ahmed pp. 582-583)",
            "h_ft_origin": h_source,
            "depth_registry_tolerance_ft": tol,
            "depth_registry_tolerance_status": f"PROVISIONAL per {CATALOG_THRESHOLDS}",
            "max_washout_overlap_frac": float(max_washout_overlap_frac),
            "min_net_pay_frac": float(min_net_pay_frac),
            "unsourced_cutoffs": "both fractions are caller-supplied; "
                                 f"{NO_WASHOUT_CUTOFF}; {NO_NET_PAY_CUTOFF}",
            "contact_uncertainty_ft": (
                contact_uncertainty_ft if contact_uncertainty_ft is not None
                else "not supplied; no source states one, so none is assumed and "
                     "the contacts were treated as exact"),
            "depth_reference": "one consistent reference increasing downward; vertical "
                               "distance is what Chierici's geometry means, so TVD or "
                               "TVDSS rather than MD in a deviated well",
            "formation": HOMOGENEOUS_ONLY,
        },
        flags=tuple(flags))
