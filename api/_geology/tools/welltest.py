"""Group R: production and well test. Seven tools, five of which answer.

These sit beside `inflow.py` (linear-J drawdown), `tools/deliverability/` (the
gas fit-to-rate path) and `pressure.py` (the Horner extrapolation), and none of
them re-implements what those already do:

- `vogel_ipr` is the *curved* oil IPR below the bubble point, which is exactly
  the case `drawdown_estimate` refuses (Ahmed Eq. 7-7 holds above p_b only).
- `nodal_analysis` takes an inflow curve from `vogel_ipr` or `gas_ipr` and does
  not build one. It supplies the intersection with tubing that
  `turner_critical_rate` and `tubing_velocity` stop short of.
- `buildup_kh_skin` delegates the straight-line fit to
  `pressure.formation_pressure_estimate` and reads kh, skin and radius of
  investigation off the same slope. There is one Horner fit in this package.
- `material_balance` is Havlena-Odeh, and refuses without a pressure history,
  which the plan says will be the normal case for a stripper fleet.
- `wor_xplot` is the semilog WOR against cumulative oil line and the water and
  remaining-oil numbers Ahmed reads off it.

**Two tools always refuse, because the corpus does not carry their method.**
`chan_diagnostic` and `artificial_lift_screen` were both predicted blocked by
the expansion plan, and grepping the knowledge base confirms it: the only
occurrence of Chan anywhere is a "continue reading" hyperlink title in
`16-decline-curves/rfour-arps-dca-practical-guide#1`, with no slopes, no
derivative and no equation, and the corpus names rod pump, gas lift, ESP and PCP
only as a list of options (`05-liquid-loading/petrowiki-liquid-loading#3`) with
no selection criterion for any of them. They exist as refusing names so the gap
is visible on the tool surface and a caller gets redirected, the same reason
`underbalance_recommend` exists.

**Vogel is in psig.** Ahmed, #104 p. 483: "Notice that p_wf and p_r must be
expressed in psig." The parameter names say `_psig` rather than the `_psia` used
everywhere else in this package, because the ratio p_wf/p_r is what the
correlation is fitted on and the two bases give different answers.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from . import pressure
from .result import Quantity, Refusal

# --- corpus anchors -------------------------------------------------------
# Chapter 7, pp. 479-488: Eq. 7-8 (J is not constant below p_b), Vogel Eq. 7-9,
# the saturated procedure, and Case 1 Eqs. 7-10/7-11 for an undersaturated well.
VOGEL = "00-reference/ahmed-reservoir-engineering-handbook#104"
# pp. 488-489: Case 2, Eq. 7-12, J from a test point recorded below p_b.
VOGEL_CASE2 = "00-reference/ahmed-reservoir-engineering-handbook#105"
# PetroWiki/SPE PEH, "Systems Analysis": inflow and outflow curves, the
# intersection as the operating point, no intersection as no production, and the
# low-rate intersection of a hooked outflow curve as an unstable solution.
NODAL = "09-gas-deliverability/petrowiki-peh-inflow-outflow-performance#13"
# Chapter 6, pp. 457-465: Horner Eq. 6-177, k from the slope Eq. 6-178, skin
# Eq. 6-179, Example 6-25 worked end to end.
BUILDUP = "00-reference/ahmed-reservoir-engineering-handbook#100"
# Earlougher Eq. 8.7 (= Eq. 2.41), p. 93: r_d = 0.029 sqrt(kt/(phi mu c_t)).
RADIUS = "03-dst/earlougher-well-test-analysis-part2-1977#3"
# Chapter 14, pp. 1006-1009: WOR against cumulative oil on semilog paper as a
# line to be extrapolated (Figure 14-55), and cumulative water as the area under
# WOR versus N_p (Figure 14-56).
WOR = "00-reference/ahmed-reservoir-engineering-handbook#212"
# Chapter 11, pp. 753-755: Havlena-Odeh Eqs. 11-25 to 11-31, and F = N E_o as a
# straight line through the origin for a reservoir with no gas cap and no
# water influx.
MBE = "00-reference/ahmed-reservoir-engineering-handbook#156"

# Cited only by the two refusals, to say what the corpus does and does not hold.
LIFT_OPTIONS = "05-liquid-loading/petrowiki-liquid-loading#3"
PLUNGER = "05-liquid-loading/shaletec-introduction-to-plunger-lift#1"
CHAN_LINK_ONLY = "16-decline-curves/rfour-arps-dca-practical-guide#1"

# Ahmed Eq. 7-9 and Eq. 7-11 share this dimensionless group.
_VOGEL_A = 0.2
_VOGEL_B = 0.8
# Eq. 7-11 / Eq. 7-12: the 1.8 that makes the curve continuous with the straight
# line at p_b.
_VOGEL_DENOM = 1.8
# Eq. 6-178.
_KH_COEFF = 162.6
# Eq. 6-179. The equation prints 1.151 and Ahmed's own Example 6-25 evaluates it
# at 1.1513, which is ln(10)/2. The example's value is used so a caller can
# reproduce the published 8.6.
_SKIN_COEFF = 1.1513
_SKIN_OFFSET = 3.23
# Earlougher Eq. 8.7.
_RADIUS_COEFF = 0.029

PSIG = ("Ahmed #104, p. 483: \"Notice that p_wf and p_r must be expressed in "
        "psig.\" Vogel's dimensionless ratio is fitted on gauge pressure and "
        "psia would shift every point on the curve")
STABILIZED = ("every empirical IPR method in Ahmed Chapter 7 requires at least "
              "one STABILIZED flow test (#104, p. 481); this tool cannot verify "
              "stabilization and assumes it")


def _vogel(x: float) -> float:
    """Ahmed Eq. 7-9's dimensionless group, 1 - 0.2x - 0.8x^2."""
    return 1.0 - _VOGEL_A * x - _VOGEL_B * x * x


def _check_finite(**kwargs: float | None) -> None:
    for name, v in kwargs.items():
        if v is not None and not math.isfinite(v):
            raise ValueError(f"{name} must be finite, got {v!r}")


# =========================================================================
# vogel_ipr
# =========================================================================
def vogel_ipr(p_r_psig: float,
              p_b_psig: float,
              test_q_stb_d: float,
              test_p_wf_psig: float,
              steps: int = 10) -> Quantity | Refusal:
    """Solution-gas-drive oil IPR from one stabilized flow test. STB/day.

    Returns the absolute open flow (Q_o)max as the value, with the whole IPR
    curve as `Quantity` objects in `inputs["curve"]`, in the same shape
    `gas_ipr` returns so `nodal_analysis` can take either.

    Two regimes, both Ahmed's:

    - **saturated**, p_r <= p_b: Eq. 7-9 alone. (Q_o)max = Q_test / [1 - 0.2 x
      - 0.8 x^2] with x = p_wf/p_r, then the curve is that group times
      (Q_o)max (#104, p. 484).
    - **undersaturated**, p_r > p_b: straight line J (p_r - p_wf) above p_b and
      Eq. 7-11 below it, joined at Q_ob = J (p_r - p_b). J comes from Eq. 7-1
      when the test point is at or above p_b (Case 1) and from Eq. 7-12 when it
      is below (Case 2, #105 p. 488).

    All pressures are **psig**, not psia. A well with no bubble point is a
    straight line and belongs to `drawdown_estimate`; this tool refuses it.
    """
    _check_finite(p_r_psig=p_r_psig, p_b_psig=p_b_psig,
                  test_q_stb_d=test_q_stb_d, test_p_wf_psig=test_p_wf_psig)
    if p_r_psig <= 0:
        raise ValueError("p_r_psig must be positive")
    if test_q_stb_d <= 0:
        raise ValueError("test_q_stb_d must be positive; it is the rate J is measured from")
    if test_p_wf_psig < 0:
        raise ValueError("test_p_wf_psig must be >= 0")
    if steps < 1:
        raise ValueError("steps must be >= 1")

    if p_b_psig <= 0:
        return Refusal(
            reason=f"p_b = {p_b_psig:g} psig: with no bubble point inside the drawdown the "
                   "IPR never leaves the straight line, and Vogel's correlation describes "
                   "only the curvature that free gas causes (Ahmed #104, p. 479).",
            needed=("drawdown_estimate(form='oil-linear-j') for a constant-J oil well",
                    "a positive bubble-point pressure in psig if the well is saturated",),
            source=VOGEL)
    if test_p_wf_psig >= p_r_psig:
        return Refusal(
            reason=f"the test point has no drawdown: p_wf = {test_p_wf_psig:g} psig is at or "
                   f"above p_r = {p_r_psig:g} psig, so it fixes no point on the IPR.",
            needed=("a stabilized flow test with p_wf below the average reservoir pressure",),
            source=VOGEL)

    if p_r_psig <= p_b_psig:
        return _vogel_saturated(p_r_psig, p_b_psig, test_q_stb_d, test_p_wf_psig, steps)
    return _vogel_undersaturated(p_r_psig, p_b_psig, test_q_stb_d, test_p_wf_psig, steps)


def _grid(p_r: float, steps: int) -> list[float]:
    """Flowing pressures from p_r down to zero, Ahmed's own table order."""
    return [p_r * (steps - i) / steps for i in range(steps + 1)]


def _curve_point(rate: float, p_wf: float, index: int, n: int,
                 equation: str) -> Quantity:
    return Quantity(
        rate, "STB/day", f"Vogel IPR point ({equation})", VOGEL,
        inputs={"p_wf_psig": p_wf},
        assumptions={"curve_index": index, "curve_points": n,
                     "role": "AOF" if p_wf == 0.0 else "IPR point",
                     "pressure_basis": PSIG})


def _vogel_saturated(p_r: float, p_b: float, q_test: float, p_wf_test: float,
                     steps: int) -> Quantity | Refusal:
    group = _vogel(p_wf_test / p_r)
    if group <= 0:
        return Refusal(
            reason=f"the test point gives a dimensionless Vogel group of {group:.6g}; "
                   "Eq. 7-9 cannot be inverted for (Q_o)max there.",
            needed=("a stabilized test point with p_wf well below p_r",), source=VOGEL)
    q_max = q_test / group

    grid = _grid(p_r, steps)
    curve = [_curve_point(q_max * _vogel(p / p_r), p, i, len(grid), "Ahmed Eq. 7-9")
             for i, p in enumerate(grid)]
    return Quantity(
        q_max, "STB/day",
        "Vogel saturated IPR, (Q_o)max = Q_o / [1 - 0.2(p_wf/p_r) - 0.8(p_wf/p_r)^2] "
        "(Ahmed Eq. 7-9)", VOGEL,
        inputs={"regime": "saturated", "p_r_psig": p_r, "p_b_psig": p_b,
                "test_q_stb_d": q_test, "test_p_wf_psig": p_wf_test,
                "vogel_group_at_test": group, "curve": curve,
                "n_curve_points": len(curve)},
        assumptions={"pressure_basis": PSIG, "stabilized_test": STABILIZED,
                     "regime": "p_r <= p_b, so the whole IPR is below the bubble point and "
                               "Eq. 7-9 applies over its entire length (#104, p. 484)",
                     "water": "Vogel extends to a liquid rate Q_L = Q_o + Q_w at water cuts "
                              "to 97% (#104, p. 483); if the test rate was total liquid, so "
                              "is this curve, and this tool cannot tell the difference"},
        flags=("(Q_o)max is Eq. 7-9 at p_wf = 0, a definition rather than a rate the well "
               "can be produced at",))


def _vogel_undersaturated(p_r: float, p_b: float, q_test: float, p_wf_test: float,
                          steps: int) -> Quantity | Refusal:
    if p_wf_test >= p_b:
        # Case 1, Eq. 7-1: the test point is on the straight-line part.
        j = q_test / (p_r - p_wf_test)
        case, case_source = "case-1 (test point at or above p_b, Eq. 7-1)", VOGEL
    else:
        # Case 2, Eq. 7-12: the test point is on the curved part, so J is backed
        # out through Eq. 7-11 rather than read off a straight line.
        denom = (p_r - p_b) + (p_b / _VOGEL_DENOM) * _vogel(p_wf_test / p_b)
        if denom <= 0:
            return Refusal(
                reason=f"Eq. 7-12's denominator is {denom:.6g}; no positive productivity "
                       "index solves this test point.",
                needed=("a stabilized test point consistent with p_r and p_b",),
                source=VOGEL_CASE2)
        j = q_test / denom
        case, case_source = "case-2 (test point below p_b, Eq. 7-12)", VOGEL_CASE2

    q_ob = j * (p_r - p_b)                       # Eq. 7-10
    q_max = q_ob + j * p_b / _VOGEL_DENOM        # Eq. 7-11 at p_wf = 0

    # p_b is forced onto the grid: it is the kink between the two equations, and
    # Ahmed's own IPR tables carry that row (#104, p. 488). Without it a coarse
    # grid interpolates straight across the corner.
    grid = sorted(set(_grid(p_r, steps)) | {p_b}, reverse=True)
    curve = []
    for i, p in enumerate(grid):
        if p >= p_b:
            rate, equation = j * (p_r - p), "Ahmed Eq. 7-6, straight line above p_b"
        else:
            rate = q_ob + (j * p_b / _VOGEL_DENOM) * _vogel(p / p_b)
            equation = "Ahmed Eq. 7-11, Vogel curve below p_b"
        curve.append(_curve_point(rate, p, i, len(grid), equation))

    return Quantity(
        q_max, "STB/day",
        "Vogel undersaturated IPR, straight line to p_b then Eq. 7-11 below it; "
        f"J from {case}", f"{VOGEL} + {VOGEL_CASE2}",
        inputs={"regime": "undersaturated", "p_r_psig": p_r, "p_b_psig": p_b,
                "test_q_stb_d": q_test, "test_p_wf_psig": p_wf_test,
                "j_stb_d_psi": j, "q_ob_stb_d": q_ob, "curve": curve,
                "n_curve_points": len(curve)},
        assumptions={"pressure_basis": PSIG, "stabilized_test": STABILIZED,
                     "case": case,
                     "j_meaning": "J is constant only from p_r down to p_b; below p_b "
                                  "(k_ro/mu_o B_o) falls and Eq. 7-11 carries the curvature",
                     "continuity": "Q_ob = J (p_r - p_b) joins the two pieces at p_b "
                                   "(Eq. 7-10)"},
        flags=("(Q_o)max = Q_ob + J p_b/1.8 is Eq. 7-11 at p_wf = 0, a definition rather "
               "than a rate the well can be produced at",))


# =========================================================================
# nodal_analysis
# =========================================================================
def nodal_analysis(inflow: Any,
                   tubing: Sequence[Sequence[float]]) -> Quantity | Refusal:
    """Where the inflow curve crosses the tubing curve: the operating point.

    `inflow` is a result from `vogel_ipr` or `gas_ipr` (either carries its curve
    in `inputs["curve"]`), or a bare `[[rate, p_node], ...]` list. `tubing` is
    the outflow curve, `[[rate, p_node], ...]`, one node pressure per rate. No
    tubing correlation is computed here: a multiphase pressure traverse is not in
    this corpus, so the curve is an input.

    PetroWiki #13: "The point of intersection between these two curves signifies
    the point of continuity ... This intersection indicates the expected
    production rate and pressure." Where they do not cross, "it indicates a lack
    of continuity within the system, implying that the well is not expected to
    produce" and this tool refuses rather than returning the closest approach.
    Where they cross twice, the source says "the intersection at the lower flow
    rate is not a stable solution and holds no meaningful significance", so the
    highest-rate crossing is returned and the others are reported as unstable.

    Both curves must be on ONE pressure basis and ONE rate unit. A `vogel_ipr`
    inflow is in psig (Ahmed's requirement) and STB/day; a `gas_ipr` inflow is in
    psia and Mscf/d. This tool cannot detect a mismatch and says so on the result.
    """
    inflow_pts, rate_unit, inflow_kind = _as_curve(inflow)
    if isinstance(inflow_pts, Refusal):
        return inflow_pts
    tubing_pts, _, _ = _as_curve(tubing, unit=rate_unit)
    if isinstance(tubing_pts, Refusal):
        return Refusal(reason="tubing curve: " + tubing_pts.reason,
                       needed=tubing_pts.needed, source=NODAL)

    lo = max(inflow_pts[0][0], tubing_pts[0][0])
    hi = min(inflow_pts[-1][0], tubing_pts[-1][0])
    if hi <= lo:
        return Refusal(
            reason=f"the two curves do not share a rate range: inflow spans "
                   f"[{inflow_pts[0][0]:g}, {inflow_pts[-1][0]:g}] and tubing spans "
                   f"[{tubing_pts[0][0]:g}, {tubing_pts[-1][0]:g}] {rate_unit}. There is "
                   "no rate at which continuity could be tested.",
            needed=("both curves tabulated over one overlapping range of rates",),
            source=NODAL)

    rates = sorted({q for q, _ in inflow_pts if lo <= q <= hi}
                   | {q for q, _ in tubing_pts if lo <= q <= hi} | {lo, hi})
    diff = [_interp(inflow_pts, q) - _interp(tubing_pts, q) for q in rates]

    crossings: list[float] = []
    for i in range(len(rates) - 1):
        a, b = diff[i], diff[i + 1]
        if a == 0.0:
            crossings.append(rates[i])
        elif a * b < 0.0:
            crossings.append(rates[i] + (rates[i + 1] - rates[i]) * a / (a - b))
    if diff[-1] == 0.0:
        crossings.append(rates[-1])

    if not crossings:
        return Refusal(
            reason="the inflow and outflow curves do not intersect over "
                   f"[{lo:g}, {hi:g}] {rate_unit}. PetroWiki #13: \"Because there is no "
                   "intersection it indicates a lack of continuity within the system, "
                   "implying that the well is not expected to produce under System A.\" "
                   f"The tubing curve sits {'above' if diff[0] < 0 else 'below'} the "
                   "inflow curve throughout.",
            needed=("a smaller tubing size, a lower wellhead pressure, or artificial lift, "
                    "then a new outflow curve",
                    "or an inflow curve at a higher reservoir pressure",),
            source=NODAL)

    q_op = max(crossings)
    p_op = _interp(inflow_pts, q_op)
    flags = []
    if len(crossings) > 1:
        flags.append(
            f"{len(crossings)} intersections at {', '.join(f'{q:.6g}' for q in crossings)} "
            f"{rate_unit}; the highest-rate one is returned because PetroWiki #13 states "
            "\"the intersection at the lower flow rate is not a stable solution and holds "
            "no meaningful significance\"")
    if q_op in (lo, hi):
        flags.append(f"the intersection is at the {'low' if q_op == lo else 'high'} end of "
                     "the tabulated overlap, so it may be an artefact of where the curves "
                     "were cut off rather than a real crossing")
    flags.append("inflow curve taken from " + inflow_kind)

    return Quantity(
        q_op, rate_unit,
        "systems (nodal) analysis: the rate at which inflow node pressure equals outflow "
        "node pressure, by linear interpolation between tabulated points (PetroWiki #13, "
        "Eqs. 1.74/1.75)", NODAL,
        inputs={"p_node": p_op, "n_intersections": len(crossings),
                "intersections": crossings, "overlap_rate_range": (lo, hi),
                "n_inflow_points": len(inflow_pts), "n_tubing_points": len(tubing_pts)},
        assumptions={"continuity": "inflow rate equals outflow rate and the node pressure is "
                                   "the same on both sides (PetroWiki #13)",
                     "interpolation": "straight segments between the supplied points; the "
                                      "answer is only as fine as the curves handed over",
                     "units": f"both curves are assumed to be in {rate_unit} and on one "
                              "pressure basis. A vogel_ipr inflow is psig and STB/day, a "
                              "gas_ipr inflow is psia and Mscf/d; this tool cannot detect a "
                              "mismatch",
                     "outflow_source": "the tubing curve is supplied, not computed: no "
                                       "multiphase pressure-traverse correlation is in this "
                                       "corpus"},
        flags=tuple(flags))


def _as_curve(obj: Any, unit: str = "") -> tuple[Any, str, str]:
    """Normalise an inflow or outflow curve to [(rate, pressure), ...] ascending.

    Accepts a `Quantity` carrying `inputs["curve"]` (what `vogel_ipr` and
    `gas_ipr` return), a list of curve-point `Quantity` objects, or a bare list
    of [rate, pressure] pairs.
    """
    kind = "supplied [rate, pressure] pairs"
    if isinstance(obj, Refusal):
        return Refusal(reason="the inflow result is itself a refusal: " + obj.reason,
                       needed=obj.needed or ("an inflow curve that resolved",),
                       source=NODAL), unit, kind
    if isinstance(obj, Quantity):
        kind = f"a {obj.unit} result: {obj.method}"
        unit = unit or obj.unit
        obj = obj.inputs.get("curve")
    points: list[tuple[float, float]] = []
    if isinstance(obj, (list, tuple)):
        for row in obj:
            if isinstance(row, Quantity):
                p = row.inputs.get("p_wf_psig", row.inputs.get("p_wf_psia"))
                if p is None:
                    return Refusal(
                        reason="a curve point carries no p_wf_psig or p_wf_psia",
                        needed=("curve points from vogel_ipr or gas_ipr",),
                        source=NODAL), unit, kind
                points.append((float(row.value), float(p)))
                unit = unit or row.unit
            elif isinstance(row, (list, tuple)) and len(row) == 2:
                points.append((float(row[0]), float(row[1])))
            else:
                return Refusal(reason=f"cannot read a [rate, pressure] pair out of {row!r}",
                               needed=("[[rate, node pressure], ...]",),
                               source=NODAL), unit, kind
    if len(points) < 2:
        return Refusal(reason=f"a curve needs at least two points, got {len(points)}",
                       needed=("a result from vogel_ipr or gas_ipr, or "
                               "[[rate, node pressure], ...]",),
                       source=NODAL), unit, kind
    points.sort()
    if points[0][0] == points[-1][0]:
        return Refusal(reason="every point on the curve is at one rate; there is no curve",
                       needed=("points at different rates",), source=NODAL), unit, kind
    for a, b in zip(points, points[1:]):
        if a[0] == b[0] and a[1] != b[1]:
            return Refusal(reason=f"two different node pressures are given at rate {a[0]:g}; "
                                  "the curve is not a function of rate",
                           needed=("one node pressure per rate",),
                           source=NODAL), unit, kind
    return points, unit or "rate", kind


def _interp(points: Sequence[tuple[float, float]], q: float) -> float:
    """Node pressure at rate `q`, linear between the bracketing points."""
    for (q0, p0), (q1, p1) in zip(points, points[1:]):
        if q0 <= q <= q1:
            return p0 if q1 == q0 else p0 + (p1 - p0) * (q - q0) / (q1 - q0)
    return points[0][1] if q < points[0][0] else points[-1][1]


# =========================================================================
# buildup_kh_skin
# =========================================================================
def buildup_kh_skin(points: Sequence[Sequence[float]],
                    t_p_hr: float,
                    q_stb_d: float,
                    b_o_rb_stb: float,
                    mu_cp: float,
                    h_ft: float,
                    phi: float,
                    ct_psi: float,
                    rw_ft: float,
                    p_wf_psi: float | None = None,
                    delta_t_min_hr: float | None = None,
                    delta_t_max_hr: float | None = None,
                    storage: dict[str, float] | None = None,
                    test_type: str = "buildup") -> dict[str, Quantity | Refusal] | Refusal:
    """kh, k, skin and radius of investigation off one Horner straight line.

    The line is not fitted here. `pressure.formation_pressure_estimate` already
    fits it, screens wellbore storage and refuses a bad window, so this tool
    calls it and reads its slope m and p_1hr. There is one Horner fit in this
    package and this is not it.

    - kh = 162.6 Q_o B_o mu_o / m and k = that over h (Ahmed Eq. 6-178)
    - s = 1.1513 [ (p_1hr - p_wf)/m - log(k / (phi mu c_t r_w^2)) + 3.23 ]
      (Eq. 6-179). p_wf is the flowing pressure immediately before shut-in: it
      is taken from the dt = 0 row of `points` if there is one, otherwise from
      `p_wf_psi`, and without either the skin cannot be measured.
    - r_inv = 0.029 sqrt(k t / (phi mu c_t)) at the longest shut-in time in the
      fitted window (Earlougher Eq. 8.7 / 2.41).

    Returns a dict of `Quantity` keyed `kh_md_ft`, `k_md`, `skin` and
    `radius_of_investigation_ft`, or a `Refusal`.
    """
    _check_finite(q_stb_d=q_stb_d, b_o_rb_stb=b_o_rb_stb, mu_cp=mu_cp, h_ft=h_ft,
                  phi=phi, ct_psi=ct_psi, rw_ft=rw_ft, p_wf_psi=p_wf_psi)
    for name, value in (("q_stb_d", q_stb_d), ("b_o_rb_stb", b_o_rb_stb), ("mu_cp", mu_cp),
                        ("h_ft", h_ft), ("phi", phi), ("ct_psi", ct_psi), ("rw_ft", rw_ft)):
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value!r}")
    if phi >= 1.0:
        raise ValueError("phi is a fraction, not a percentage")

    fit = pressure.formation_pressure_estimate(
        points, t_p_hr, delta_t_min_hr=delta_t_min_hr, delta_t_max_hr=delta_t_max_hr,
        storage=storage, test_type=test_type)
    if isinstance(fit, Refusal):
        return fit

    m = float(fit.inputs["slope_m_psi_per_cycle"])
    p_1hr = float(fit.inputs["p_1hr_psi"])
    lo, hi = fit.inputs["delta_t_window_hr"]
    p_wf = fit.inputs.get("p_wf_psi") if p_wf_psi is None else p_wf_psi

    # Eq. 6-178.
    kh = _KH_COEFF * q_stb_d * b_o_rb_stb * mu_cp / m
    k = kh / h_ft
    shared = {"slope_m_psi_per_cycle": m, "p_star_psi": fit.value, "p_1hr_psi": p_1hr,
              "q_stb_d": q_stb_d, "b_o_rb_stb": b_o_rb_stb, "mu_cp": mu_cp, "h_ft": h_ft,
              "t_p_hr": t_p_hr, "n_points_used": fit.inputs["n_points_used"]}
    horner = ("the Horner slope is unaffected by skin (#100, p. 459), which is why kh comes "
              "off the line and skin needs the flowing pressure as well")
    out: dict[str, Quantity | Refusal] = {
        "kh_md_ft": Quantity(
            kh, "md.ft", "kh = 162.6 Q_o B_o mu_o / m (Ahmed Eq. 6-178)", BUILDUP,
            inputs=dict(shared), assumptions={"horner": horner},
            flags=tuple(fit.flags)),
        "k_md": Quantity(
            k, "md", "k = 162.6 Q_o B_o mu_o / (m h) (Ahmed Eq. 6-178)", BUILDUP,
            inputs=dict(shared),
            assumptions={"h_meaning": "h is the net thickness the flow comes from; kh is the "
                                      "measured quantity and k is kh divided by an h this "
                                      "test did not see"},
            flags=tuple(fit.flags)),
    }

    # Eq. 6-179. Skin is measured, not modelled: without the flowing pressure
    # immediately before shut-in there is nothing to measure it against. kh is
    # still returned, because the Horner slope does not need it.
    if p_wf is None:
        out["skin"] = Refusal(
            reason="skin needs p_wf immediately before shut-in (Ahmed Eq. 6-179) and neither "
                   "a dt = 0 row nor p_wf_psi was supplied. kh and k are unaffected: the "
                   "Horner slope does not see skin at all.",
            needed=("a (0.0, p_wf) row in points, or p_wf_psi",), source=BUILDUP)
    else:
        log_term = math.log10(k / (phi * mu_cp * ct_psi * rw_ft ** 2))
        s = _SKIN_COEFF * ((p_1hr - float(p_wf)) / m - log_term + _SKIN_OFFSET)
        out["skin"] = Quantity(
            s, "dimensionless",
            "s = 1.1513[(p_1hr - p_wf)/m - log(k/(phi mu c_t r_w^2)) + 3.23] "
            "(Ahmed Eq. 6-179)", BUILDUP,
            inputs={**shared, "p_wf_psi": float(p_wf), "phi": phi, "ct_psi": ct_psi,
                    "rw_ft": rw_ft, "k_md": k, "log_term": log_term},
            assumptions={"p_1hr": "read off the extrapolated straight line, not off the data "
                                  "at 1 hour (#100, p. 461)",
                         "coefficient": "1.1513 as Ahmed's Example 6-25 evaluates it; "
                                        "Eq. 6-179 itself prints the rounded 1.151",
                         "sign": "positive is damage, negative is stimulation; this is a "
                                 "MEASURED total skin and includes completion geometry, "
                                 "unlike perforation_skin which computes geometry alone"},
            flags=tuple(fit.flags))

    # Earlougher Eq. 8.7. t is the longest shut-in time actually fitted.
    t_max = max((dt for dt, _ in ((float(a), float(b)) for a, b in points)
                 if lo <= dt <= hi), default=0.0)
    if t_max > 0:
        r_inv = _RADIUS_COEFF * math.sqrt(k * t_max / (phi * mu_cp * ct_psi))
        out["radius_of_investigation_ft"] = Quantity(
            r_inv, "ft", "r = 0.029 sqrt(k t / (phi mu c_t)) (Earlougher Eq. 8.7 = Eq. 2.41)",
            RADIUS,
            inputs={"k_md": k, "t_hr": t_max, "phi": phi, "mu_cp": mu_cp, "ct_psi": ct_psi},
            assumptions={"t_meaning": "the longest shut-in time inside the fitted straight "
                                      "line, so this is how far the line saw",
                         "coefficient": "0.029 is Earlougher's radius of drainage, which he "
                                        "equates to the radius of investigation for a DST "
                                        "(#3, p. 93). The corpus also carries an AAPG DST "
                                        "form with a different constant, so this number is "
                                        "convention-dependent to within a factor of about two"},
            flags=("Earlougher #3: the radius of investigation from a short test \"should not "
                   "be used to identify faults or boundaries\"",))

    return out


# =========================================================================
# chan_diagnostic - always refuses, the corpus has no method
# =========================================================================
def chan_diagnostic(points: Sequence[Sequence[float]] | None = None,
                    oil_rate_stb_d: float | None = None,
                    water_rate_stb_d: float | None = None) -> Refusal:
    """Always refuses. The WOR-derivative diagnostic is not in this corpus.

    Arguments are accepted and ignored so a caller's call site does not have to
    change to get the honest answer, the same shape as `underbalance_recommend`.
    """
    return Refusal(
        reason="Chan's log-log WOR and WOR' against time diagnostic is not in this corpus. "
               "The only occurrence of the name anywhere in the knowledge base is a "
               "\"continue reading\" hyperlink title, \"Chan diagnostic - reading water "
               f"production mechanisms\" ({CHAN_LINK_ONLY}), which carries no plot, no slope "
               "and no equation. The corpus does hold WOR as a produced ratio (Ahmed #76) "
               "and the waterflood WOR relationships of Chapter 14, but neither states the "
               "derivative slopes that separate channelling from coning from normal "
               "displacement, and inventing those thresholds would make this tool return a "
               "recompletion decision nobody could defend to an operator.",
        needed=("SPE 30775, Chan, K.S., \"Water Control Diagnostic Plots\" (1995), the "
                "source of the WOR/WOR' slope signatures",
                "until then: coning_critical_rate and coning_breakthrough_time for the "
                "coning side, plugback_vs_squeeze for the recompletion decision, and "
                "wor_xplot for the deterministic water forecast"),
        source=CHAN_LINK_ONLY)


# =========================================================================
# wor_xplot
# =========================================================================
def wor_xplot(points: Sequence[Sequence[float]],
              wor_limit: float | None = None) -> dict[str, Quantity] | Refusal:
    """WOR against cumulative oil: the water forecast and the remaining oil.

    Ahmed #212, p. 1008, step 4: "If the water-oil ratio is plotted against the
    oil recovery on semi-log paper and a Cartesian scale, the oil recovery at
    breakthrough can be found by extrapolating the line." Step 6: "The
    cumulative water produced at any given value of WOR is obtained by finding
    the area under the curve of WOR versus N_P."

    `points` is `[[np_stb, wor_bbl_stb], ...]`. Returns a dict of `Quantity`:
    `np_at_limit_stb` and `remaining_oil_stb` when `wor_limit` is given, and
    `cumulative_water_bbl` over the supplied history always.

    This is NOT Ershaghi's X-plot, which is not in this corpus. It is the
    semilog line Ahmed states, used forward to an economic WOR instead of
    backward to breakthrough.
    """
    rows = [(float(np_), float(wor)) for np_, wor in points]
    for np_, wor in rows:
        _check_finite(np_stb=np_, wor=wor)
    if len(rows) < 2:
        return Refusal(reason=f"a line needs two points, got {len(rows)}",
                       needed=("[[cumulative oil STB, WOR bbl/STB], ...]",), source=WOR)
    if any(wor <= 0 for _, wor in rows):
        return Refusal(
            reason="a WOR of zero or less has no logarithm, and the plot Ahmed describes is "
                   "semilog in WOR. Pre-breakthrough rows belong outside the fit.",
            needed=("only rows after water breakthrough, all with WOR > 0",), source=WOR)
    rows.sort()
    if rows[0][0] == rows[-1][0]:
        return Refusal(reason="every row is at one cumulative oil; there is no line to fit",
                       needed=("production history at increasing cumulative oil",), source=WOR)

    xs = [np_ for np_, _ in rows]
    ys = [math.log10(wor) for _, wor in rows]
    # The same least squares pressure.py fits its Horner line with; one
    # implementation of a straight line in this package.
    slope, intercept, r2, max_resid = pressure._fit_line(xs, ys)

    # Cumulative water is the area under WOR against N_p (step 6), by trapezoid
    # over the rows given. It is history, not forecast.
    wp = sum((b[1] + a[1]) / 2.0 * (b[0] - a[0]) for a, b in zip(rows, rows[1:]))

    shared = {"n_points": len(rows), "slope_log10_wor_per_stb": slope,
              "intercept_log10_wor": intercept, "r_squared": r2,
              "max_residual_log10_wor": max_resid,
              "np_last_stb": rows[-1][0], "wor_last": rows[-1][1]}
    flags = []
    if slope <= 0:
        flags.append("the fitted WOR is flat or falling with cumulative oil, so nothing can "
                     "be forecast forward from it")
    if max_resid > 0.1:
        flags.append(f"residuals reach {max_resid:.3g} log cycles, so these points are not on "
                     "one straight line (house presentation rule; Ahmed states no "
                     "goodness-of-fit criterion)")

    out: dict[str, Quantity] = {
        "cumulative_water_bbl": Quantity(
            wp, "bbl",
            "area under WOR against N_p by trapezoid over the supplied history "
            "(Ahmed #212 p. 1008, step 6 / Figure 14-56)", WOR,
            inputs=dict(shared),
            assumptions={"scope": "the supplied history only; this is not a forecast",
                         "units": "WOR in bbl/STB against N_p in STB gives bbl of water"},
            flags=tuple(flags)),
    }

    if wor_limit is None:
        return out
    _check_finite(wor_limit=wor_limit)
    if wor_limit <= 0:
        raise ValueError("wor_limit must be positive")
    if slope <= 0:
        return Refusal(
            reason=f"the semilog fit has slope {slope:.6g} log cycles per STB: WOR is not "
                   "rising with cumulative oil, so extrapolating to a limiting WOR would "
                   "run the line backwards and return a cumulative oil below what the well "
                   "has already made.",
            needed=("a history over which the water cut is climbing",
                    "or a longer history, if the flat stretch is a rate change rather than "
                    "the reservoir",), source=WOR)

    np_limit = (math.log10(wor_limit) - intercept) / slope
    remaining = np_limit - rows[-1][0]
    limit_flags = list(flags)
    if wor_limit <= rows[-1][1]:
        limit_flags.append(f"wor_limit {wor_limit:g} is at or below the last observed WOR "
                           f"{rows[-1][1]:g}; the well is already past it and the remaining "
                           "oil comes out negative")
    if np_limit > 2.0 * rows[-1][0]:
        limit_flags.append("the limiting WOR is more than one doubling of cumulative oil "
                           "beyond the last point; Ahmed extrapolates this line backwards to "
                           "breakthrough, and states no forward range for it")

    method = ("log10(WOR) = a + b N_p fitted by least squares and solved at the limiting "
              "WOR (Ahmed #212 p. 1008, step 4 / Figure 14-55)")
    assumptions = {"line": "Ahmed states the semilog WOR against oil recovery relationship "
                           "is a straight line and extrapolates it; this tool extrapolates "
                           "the same line forward to an economic WOR",
                   "not_ershaghi": "Ershaghi's X-plot is a different construction and is not "
                                   "in this corpus",
                   "drive": "the line is stated for a waterflood; a well watering out from "
                            "an aquifer or a channel behind pipe need not follow it"}
    out["np_at_limit_stb"] = Quantity(
        np_limit, "STB", method, WOR,
        inputs={**shared, "wor_limit": wor_limit}, assumptions=assumptions,
        flags=tuple(limit_flags))
    out["remaining_oil_stb"] = Quantity(
        remaining, "STB", method + ", less the cumulative oil already produced", WOR,
        inputs={**shared, "wor_limit": wor_limit, "np_at_limit_stb": np_limit},
        assumptions=assumptions, flags=tuple(limit_flags))
    return out


# =========================================================================
# material_balance
# =========================================================================
def material_balance(history: Sequence[Mapping[str, float]] | None = None,
                     b_oi_rb_stb: float | None = None,
                     r_si_scf_stb: float | None = None,
                     drive: str = "depletion") -> Quantity | Refusal:
    """Original oil in place from the Havlena-Odeh straight line. STB.

    Ahmed #156, pp. 753-755. For a reservoir with no initial gas cap (m = 0), no
    water influx (W_e = 0) and negligible formation and water compressibility,
    Eq. 11-25 reduces to F = N E_o, and "a plot of the parameter F as a function
    of the oil expansion parameter E_o would yield a straight line with a slope
    N and intercept equal to zero."

        F   = N_p [B_o + (R_p - R_s) B_g] + W_p B_w      (Eq. 11-26)
        E_o = (B_o - B_oi) + (R_si - R_s) B_g            (Eq. 11-28)

    `history` is one mapping per pressure survey with keys `p_psia`, `np_stb`,
    `bo_rb_stb`, `rs_scf_stb`, `rp_scf_stb`, `bg_rb_scf`, and optionally
    `wp_bbl` and `bw_rb_bbl`. **Without a pressure history this refuses**, which
    the expansion plan expects to be the normal case: every term above is a PVT
    property evaluated at a measured reservoir pressure, and there is no version
    of this calculation that runs on production alone.
    """
    if drive != "depletion":
        return Refusal(
            reason=f"drive={drive!r}: this tool runs only the depletion-drive reduction of "
                   "Eq. 11-25, F = N E_o. A gas cap needs m and E_g (Eq. 11-30) and an "
                   "aquifer needs a water-influx model for W_e, and each turns the same "
                   "plot into a different straight line with a different unknown.",
            needed=("drive='depletion'",
                    "for a gas cap: F against (E_o + m E_g) with m known, or the "
                    "F/E_o against E_g/E_o plot (Ahmed #157)",
                    "for water drive: a W_e model before the plot means anything",),
            source=MBE)
    if not history:
        return Refusal(
            reason="material balance needs a pressure history. Every term in Eqs. 11-26 and "
                   "11-28 is a PVT property evaluated at a measured average reservoir "
                   "pressure, so with no pressures there is no expansion to plot production "
                   "against and no straight line whose slope is N.",
            needed=("history=[{'p_psia', 'np_stb', 'bo_rb_stb', 'rs_scf_stb', "
                    "'rp_scf_stb', 'bg_rb_scf', optional 'wp_bbl', 'bw_rb_bbl'}, ...], "
                    "one row per pressure survey",
                    "b_oi_rb_stb and r_si_scf_stb at the initial pressure",
                    "volumetrics is the alternative when no pressure was ever measured, and "
                    "it answers a different question",),
            source=MBE)
    if b_oi_rb_stb is None or r_si_scf_stb is None:
        return Refusal(
            reason="E_o is measured from the initial state: (B_o - B_oi) + (R_si - R_s) B_g "
                   "(Eq. 11-28). Without B_oi and R_si there is no datum to expand from.",
            needed=tuple(n for n, v in (("b_oi_rb_stb", b_oi_rb_stb),
                                        ("r_si_scf_stb", r_si_scf_stb)) if v is None),
            source=MBE)

    required = ("p_psia", "np_stb", "bo_rb_stb", "rs_scf_stb", "rp_scf_stb", "bg_rb_scf")
    fs: list[float] = []
    eos: list[float] = []
    pressures: list[float] = []
    for i, row in enumerate(history):
        missing = tuple(k for k in required if row.get(k) is None)
        if missing:
            return Refusal(
                reason=f"history row {i} is missing {', '.join(missing)}",
                needed=required, source=MBE)
        p = float(row["p_psia"])
        bo, rs, rp = float(row["bo_rb_stb"]), float(row["rs_scf_stb"]), float(row["rp_scf_stb"])
        bg, np_ = float(row["bg_rb_scf"]), float(row["np_stb"])
        wp = float(row.get("wp_bbl") or 0.0)
        bw = float(row.get("bw_rb_bbl") or 1.0)
        _check_finite(p_psia=p, bo=bo, rs=rs, rp=rp, bg=bg, np_stb=np_, wp=wp, bw=bw)
        pressures.append(p)
        fs.append(np_ * (bo + (rp - rs) * bg) + wp * bw)          # Eq. 11-26
        eos.append((bo - b_oi_rb_stb) + (r_si_scf_stb - rs) * bg)  # Eq. 11-28

    usable = [(e, f) for e, f in zip(eos, fs) if e > 0.0]
    if len(usable) < 2:
        return Refusal(
            reason=f"only {len(usable)} row(s) have a positive oil expansion E_o. The "
                   "straight line is F against E_o, so a reservoir that has not measurably "
                   "depleted below its initial state gives nothing to fit.",
            needed=("at least two surveys at pressures below the initial pressure",
                    "B_oi and R_si that really are the initial values, not the first "
                    "survey's",), source=MBE)

    # Least squares through the origin: Ahmed states the intercept is zero, so
    # fitting one would be fitting a parameter the source says does not exist.
    n_stb = sum(e * f for e, f in usable) / sum(e * e for e, _ in usable)
    residuals = [f - n_stb * e for e, f in usable]
    worst = max(abs(r) for r in residuals)
    scale = max(f for _, f in usable)

    flags = []
    if len(usable) < 3:
        flags.append("two points define a line exactly; the straight-line method's whole "
                     "value is the SHAPE of the plot (#156, p. 755), and two points have "
                     "no shape")
    if worst > 0.1 * scale:
        flags.append(f"worst residual is {worst:.4g} rb against a largest withdrawal of "
                     f"{scale:.4g} rb; Ahmed #156, p. 755: \"if the plotted data deviates "
                     "from this straight line there is some reason for it\", most often a "
                     "gas cap or water influx that this depletion form assumes away")
    if len(usable) < len(eos):
        flags.append(f"{len(eos) - len(usable)} row(s) with E_o <= 0 were dropped")

    return Quantity(
        n_stb, "STB",
        "Havlena-Odeh straight line F = N E_o, least squares through the origin "
        "(Ahmed Eqs. 11-25/11-26/11-28)", MBE,
        inputs={"n_rows": len(eos), "n_rows_used": len(usable),
                "pressure_range_psia": (min(pressures), max(pressures)),
                "f_rb": fs, "e_o_rb_stb": eos, "b_oi_rb_stb": b_oi_rb_stb,
                "r_si_scf_stb": r_si_scf_stb, "max_residual_rb": worst},
        assumptions={"reduction": "m = 0 (no gas cap), W_e = 0 (no water influx), c_f and "
                                  "c_w negligible, no injection. Eq. 11-25 reduces to "
                                  "F = N E_o only under all four",
                     "intercept": "fixed at zero, as Ahmed states, rather than fitted",
                     "sequence": "the straight-line method \"attaches significance to the "
                                 "sequence of the plotted points, the direction in which "
                                 "they plot, and to the shape\" (#156, p. 755); a least "
                                 "squares slope sees none of that, so read the residuals",
                     "n_meaning": "N is original oil in place, not reserves"},
        flags=tuple(flags))


# =========================================================================
# artificial_lift_screen - always refuses, the corpus has no criteria
# =========================================================================
def artificial_lift_screen(q_liquid_bbl_d: float | None = None,
                           depth_ft: float | None = None,
                           glr_scf_bbl: float | None = None,
                           deviation_deg: float | None = None) -> Refusal:
    """Always refuses. The corpus states no selection criteria to screen on.

    Arguments are accepted and ignored, the same shape as
    `underbalance_recommend`, so a caller does not have to change a call site to
    get the honest answer.
    """
    return Refusal(
        reason="Nothing in this corpus compares rod pump against gas lift against plunger. "
               f"The one passage that lists them ({LIFT_OPTIONS}) says only that \"various "
               "artificial lift methods can be used, such as plunger lift, gas lift, sucker "
               "rod pumps, electric submersible pumps (ESP) or progressive cavity pumps "
               "(PCP) depending on the field conditions\", and never says which field "
               "conditions. There is no rate window, no depth limit and no gas-liquid ratio "
               "threshold for rod pump or for gas lift anywhere in the knowledge base, so a "
               "three-way screen would be three thresholds invented to fill a table.",
        needed=("a published artificial-lift selection chart, for example Clegg, Bucaram and "
                "Hein, \"Recommendations and Comparisons for Selecting Artificial-Lift "
                "Methods\", JPT 1993",
                f"PLUNGER LIFT ALONE is screenable from {PLUNGER}: at least 400 scf/bbl per "
                "1000 ft of lift without a packer and 2000 with one, casing pressure at "
                "least 1.5 times line pressure, lift pressure at least twice the fluid load, "
                "typically under 100 bbl/day, deviation under 60 degrees and dogleg under 10 "
                "degrees per 100 ft. That screens one candidate in, and cannot rank it "
                "against the two this tool was asked to compare",
                "turner_critical_rate and coleman_critical_rate for whether the well is "
                "loading at all, which is the question that precedes this one"),
        source=LIFT_OPTIONS)
