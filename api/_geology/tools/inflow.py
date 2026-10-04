"""Inflow drawdown: what a proposed rate costs in sandface pressure.

One tool, `drawdown_estimate` (#56). It answers the inverse of an IPR
evaluation — rate in, pressure drop out — wherever a *linear* productivity
index is defined, and refuses everywhere else.

**Why this is not in `tools/deliverability/`.** That package is the gas-well
fit-to-rate path (#82-#86): it takes a multipoint test, fits a deliverability
exponent or a LIT quadratic, and evaluates rate from pressure. There is exactly
one fit-to-rate evaluator there and everything else is that evaluator at a
different point. This tool fits nothing and inverts nothing empirical. J is an
**input**, the oil form is Ahmed Chapter 7 rather than Chapter 8, and the
question asked runs the other way — pressure out, not rate out. Putting it in
that package would have meant a sixth `FORMS` table with a different meaning
sharing a namespace with five that already collide, and an oil-phase tool inside
a gas package. (This module was written once inside `tools/deliverability.py`
and lost when that module became a package; it is restored here, where the
package boundary cannot swallow it again.)

**The narrowness IS the tool.** Ahmed defines a linear J in exactly three
places, each with its own pressure window, and states in as many words that a
fourth does not exist:

- oil, Eq. 7-7, **above the bubble point only**. Below p_b, k_ro and
  (k_ro/mu_o B_o) both fall sharply, J is not constant, and Eq. 7-7 is the wrong
  equation — not an imprecise one. That is a refusal naming Vogel / Wiggins /
  Standing / Fetkovich / Klins-Clark.
- gas, Eq. 8-12, pressure-squared, **p_r and p_wf both below 2000 psi**.
- gas, Eqs. 8-3/8-5, pseudopressure, all pressures — but the answer is a
  *pseudopressure* drop in psi^2/cp, not a pressure drop in psi. It carries a
  flag saying so, because a Δψ of 2.7e8 rendered as "psi" is a catastrophic
  misread.
- gas above 3000 psi: "the concept of the productivity index J cannot be
  introduced into Equation 8-9" (#112, p. 537). There is no linear-J drawdown
  there. The tool refuses and names the pseudopressure form. **No approximation
  is ever substituted for a refused form.**

`p_b_psia` is required with no default on the oil form. A tool that defaults the
bubble point to zero can never refuse below it, which would delete the tool's
main content; omitting it is a refusal (R2), not a silent zero.

The output is always the **drawdown**, never the flowing pressure — one meaning
per tool. p_wf (or ψ_wf) rides along in `inputs` so the caller never re-subtracts.

Converting Δψ back to Δp needs the m(p) integral inverted and is out of scope;
that is `pseudopressure` (#81) territory. ψ̄_r is taken as an argument here rather
than computed, so this module has no dependency on the gas-PVT path.
"""
from __future__ import annotations

import math
from typing import Any

from .result import Quantity, Refusal

# --- corpus anchors -------------------------------------------------------
# Chapter 7, Oil Well Performance, pp. 473-478: Eqs. 7-1 ... 7-7, AOF = J p_r.
OIL = "00-reference/ahmed-reservoir-engineering-handbook#103"
# pp. 478-484: Example 7-1 solution, the below-bubble-point breakdown, Vogel Eq. 7-9.
OIL_BELOW_PB = "00-reference/ahmed-reservoir-engineering-handbook#104"
# Chapter 8, Vertical Gas Well Performance, pp. 533-538: Eqs. 8-1 ... 8-14 and
# the three pressure regions. Sole source for every gas form below; no gas form
# here is an adaptation of Eq. 7-7.
GAS = "00-reference/ahmed-reservoir-engineering-handbook#112"

# Not an anchor, and shaped so it cannot be mistaken for one.
HOUSE_RULE = "house-rule (not Ahmed): bubble-point proximity band"

# --- forms ----------------------------------------------------------------
# Each form is its own equation with its own units and its own pressure window.
# `form` is required and has no default: silently picking one would mix STB/day
# with Mscf/day and psi with psi^2/cp, which is the unit bug this module exists
# to prevent.
FORMS: dict[str, str] = {
    "oil-linear-j": "Eq. 7-7, p_wf = p_r - (1/J) Q_o; oil, above the bubble point only",
    "gas-pressure-squared": "Eq. 8-12, Q_g = J (p_r^2 - p_wf^2); gas, both pressures < 2000 psi",
    "gas-pseudopressure": "Eqs. 8-3/8-5, psi_wf = psi_r - (1/J) Q_g; gas, all pressures",
    "gas-pressure-approximation": "Eq. 8-9; NO productivity index exists for this form",
}

# Required arguments per form. Missing any of these is R2, a refusal, because a
# caller who forgot the bubble point is asking an unanswerable question, not
# passing an impossible one.
REQUIRED: dict[str, tuple[str, ...]] = {
    "oil-linear-j": ("p_r_psia", "q_stb_d", "j_stb_d_psi", "p_b_psia"),
    "gas-pressure-squared": ("p_r_psia", "q_mscf_d", "j_mscf_d_psi2"),
    "gas-pseudopressure": ("q_mscf_d", "j_mscf_d_psi2_cp"),
    "gas-pressure-approximation": (),
}

# --- pressure regions, Ahmed #112 pp. 536-537 -----------------------------
# Region III, "usually less than 2000 psi": (mu_g z) essentially constant
# (Golan and Whitson 1986), so Eq. 8-11 collapses to the linear-J Eq. 8-12.
REGION_III_MAX_PSIA = 2000.0
# Region II, 2000-3000 psi: "distinct curvature"; pseudopressure only.
REGION_I_MIN_PSIA = 3000.0
# Presentation only: how close to the Region II boundary is worth warning about.
_REGION_III_PROXIMITY_PSIA = 1800.0

# HOUSE RULE, not Ahmed. Figure 7-6 shows (k_ro/mu_o B_o) already moving as p
# approaches p_b from above, but Ahmed states no band. A flag, never a refusal.
BUBBLE_POINT_PROXIMITY_FRACTION = 0.10

# #104, p. 481: the empirical IPR methods Ahmed names for below the bubble point.
BELOW_PB_METHODS = ("Vogel", "Wiggins", "Standing", "Fetkovich", "Klins-Clark")

# #103, p. 474. A property of the test J was measured from, which this tool
# cannot see. Carried on every result rather than checked.
PSEUDOSTEADY_STATE = (
    "J is a valid measure of well productivity only if the well was flowing at "
    "pseudosteady state when it was measured (Ahmed #103, p. 474); this tool "
    "cannot verify that and assumes it"
)

_PSEUDOPRESSURE_FLAG = "pseudopressure-drawdown-not-psi"


def _check_finite(**kwargs: float | None) -> None:
    for name, v in kwargs.items():
        if v is not None and not math.isfinite(v):
            raise ValueError(f"{name} must be finite, got {v!r}")


# =========================================================================
# 56 - drawdown_estimate
# =========================================================================
def drawdown_estimate(form: str,
                      p_r_psia: float | None = None,
                      q_stb_d: float | None = None,
                      j_stb_d_psi: float | None = None,
                      p_b_psia: float | None = None,
                      q_mscf_d: float | None = None,
                      j_mscf_d_psi2: float | None = None,
                      j_mscf_d_psi2_cp: float | None = None,
                      psi_r_psi2_cp: float | None = None) -> Quantity | Refusal:
    """Sandface drawdown at a proposed rate, from a linear productivity index.

    Returns the **drawdown**: Δp = p̄_r − p_wf in psi for the two pressure forms,
    Δψ = ψ̄_r − ψ_wf in psi^2/cp for the pseudopressure form. The flowing
    pressure is in `inputs` as `p_wf_psia` / `psi_wf_psi2_cp`.

    `form` is required, and for `"oil-linear-j"` so is `p_b_psia` — pass `0.0`
    to assert explicitly that free gas cannot appear. Refusals are returned, not
    raised. Impossible arguments (negative pressure, J <= 0, negative rate) raise
    `ValueError`; they are programmer error, not an unanswerable question.
    """
    # R1 - unknown form.
    if form not in FORMS:
        return Refusal(
            reason=f"unknown form {form!r}; a drawdown is only defined where a linear "
                   "productivity index is, and Ahmed defines one in three places",
            needed=tuple(f"form={name!r}: {desc}" for name, desc in FORMS.items()),
            source=GAS)

    # R6 - refused on the source's own words, whatever else was passed. Checked
    # before the missing-argument sweep because no set of arguments makes this
    # form answerable, and reporting "you forgot p_r_psia" would imply otherwise.
    if form == "gas-pressure-approximation":
        return Refusal(
            reason="Ahmed, #112 pp. 536-537: \"It should be pointed out the concept of the "
                   "productivity index J cannot be introduced into Equation 8-9 since "
                   "Equation 8-9 is only valid for applications when both p_wf and p_r are "
                   "above 3000 psi.\" There is no linear-J drawdown form for a gas well in "
                   "the high-pressure region, and this tool will not substitute an "
                   "approximation for one.",
            needed=("form='gas-pseudopressure' — Eq. 8-3 is applicable at all pressures, "
                    "but returns a pseudopressure drop in psi^2/cp, not psi",
                    "psi_r_psi2_cp and psi_wf from pseudopressure (#81) if a pressure drop "
                    "in psi is what you need; inverting m(p) is out of scope here"),
            source=GAS)

    # R2 - missing required arguments for the chosen form.
    supplied: dict[str, float | None] = {
        "p_r_psia": p_r_psia, "q_stb_d": q_stb_d, "j_stb_d_psi": j_stb_d_psi,
        "p_b_psia": p_b_psia, "q_mscf_d": q_mscf_d, "j_mscf_d_psi2": j_mscf_d_psi2,
        "j_mscf_d_psi2_cp": j_mscf_d_psi2_cp, "psi_r_psi2_cp": psi_r_psi2_cp,
    }
    missing = tuple(name for name in REQUIRED[form] if supplied[name] is None)
    if missing:
        extra = ()
        if "p_b_psia" in missing:
            extra = ("p_b_psia has no default on purpose: this tool's job is to refuse below "
                     "the bubble point, and a tool that defaults it to zero can never do that. "
                     "Pass 0.0 to assert explicitly that free gas cannot appear.",)
        return Refusal(
            reason=f"form={form!r} needs {', '.join(missing)}",
            needed=missing + extra,
            source=OIL if form == "oil-linear-j" else GAS)

    _check_finite(p_r_psia=p_r_psia, q_stb_d=q_stb_d, j_stb_d_psi=j_stb_d_psi,
                  p_b_psia=p_b_psia, q_mscf_d=q_mscf_d, j_mscf_d_psi2=j_mscf_d_psi2,
                  j_mscf_d_psi2_cp=j_mscf_d_psi2_cp, psi_r_psi2_cp=psi_r_psi2_cp)

    if form == "oil-linear-j":
        return _oil_linear_j(float(p_r_psia), float(q_stb_d),      # type: ignore[arg-type]
                             float(j_stb_d_psi), float(p_b_psia))  # type: ignore[arg-type]
    if form == "gas-pressure-squared":
        return _gas_pressure_squared(float(p_r_psia), float(q_mscf_d),   # type: ignore[arg-type]
                                     float(j_mscf_d_psi2))               # type: ignore[arg-type]
    return _gas_pseudopressure(float(q_mscf_d), float(j_mscf_d_psi2_cp),  # type: ignore[arg-type]
                               psi_r_psi2_cp)


# --- oil, Eq. 7-7 ---------------------------------------------------------
def _oil_linear_j(p_r_psia: float, q_stb_d: float, j_stb_d_psi: float,
                  p_b_psia: float) -> Quantity | Refusal:
    if p_r_psia <= 0:
        raise ValueError("p_r_psia must be positive")
    if p_b_psia < 0:
        raise ValueError("p_b_psia must be >= 0 (pass 0.0 to assert an undersaturated system)")
    if j_stb_d_psi <= 0:
        raise ValueError("j_stb_d_psi must be positive; Eq. 7-1 divides by it")
    if q_stb_d < 0:
        raise ValueError("q_stb_d must be >= 0")

    # R3 - saturated at static conditions: the IPR is curved over the whole
    # interval, so there is no straight line to invert at any rate.
    if p_r_psia <= p_b_psia:
        return Refusal(
            reason=f"the reservoir is saturated: p_r = {p_r_psia:g} psia is at or below the "
                   f"bubble point p_b = {p_b_psia:g} psia. Ahmed #104, p. 479: \"when the "
                   "pressure drops below the bubble-point pressure, the IPR deviates from "
                   "that of the simple straight-line relationship.\" Below p_b gas comes out "
                   "of solution and both k_ro and (k_ro/mu_o B_o) fall sharply, so J of "
                   "Eq. 7-8 is not constant and Eq. 7-7 does not hold anywhere on this IPR.",
            needed=tuple(f"{m}'s method" for m in BELOW_PB_METHODS)
                   + ("Vogel Eq. 7-9 is given in full at #104, p. 483; all of these need at "
                      "least one stabilized flow test",),
            source=OIL_BELOW_PB)

    # Eq. 7-1 / 7-7: Dp = Q_o / J, p_wf = p_r - Dp.
    drawdown_psi = q_stb_d / j_stb_d_psi
    p_wf_psia = p_r_psia - drawdown_psi
    # AOF = J p_r (#103, p. 478). Ahmed's Example 7-1(b) prints 375.5 for
    # 0.275 x 1300; the arithmetic is 357.5 and the digits are transposed in
    # print. The equation, not the misprint, is what is implemented.
    aof_stb_d = j_stb_d_psi * p_r_psia

    # R5 - the rate exceeds absolute open flow. Checked before R4 because with
    # p_b = 0 the two conditions coincide and "you asked for more than the well
    # can ever make" is the more useful reading of p_wf < 0.
    if p_wf_psia < 0:
        return Refusal(
            reason=f"q = {q_stb_d:g} STB/day exceeds the absolute open flow potential "
                   f"AOF = J p_r = {aof_stb_d:g} STB/day (#103, p. 478); it would require a "
                   f"flowing pressure of {p_wf_psia:g} psia. No drawdown exists for this rate.",
            needed=(f"a rate at or below AOF = {aof_stb_d:g} STB/day",
                    "AOF is itself the straight-line extrapolation to p_wf = 0 and is not a "
                    "rate the well can generally produce"),
            source=OIL)

    # R4 - the drawdown crosses the bubble point partway down. The straight line
    # is valid from p_r to p_b and curved below it, so this rate cannot be
    # evaluated with a single constant J.
    if p_wf_psia < p_b_psia:
        q_max_stb_d = j_stb_d_psi * (p_r_psia - p_b_psia)
        return Refusal(
            reason=f"this rate pulls the sandface to p_wf = {p_wf_psia:.6g} psia, below the "
                   f"bubble point p_b = {p_b_psia:g} psia. The IPR is a straight line only "
                   f"from p_r down to p_b; below p_b (Ahmed #104, p. 479) it deviates from "
                   "the straight-line relationship, so a single constant J cannot describe "
                   "the drawdown over this interval.",
            needed=(f"a rate at or below J (p_r - p_b) = {q_max_stb_d:g} STB/day, which is the "
                    "largest rate that keeps the sandface above the bubble point",)
                   + tuple(f"{m}'s method for the curved part" for m in BELOW_PB_METHODS)
                   + ("Vogel Eq. 7-9, #104 p. 483, for a saturated IPR",),
            source=OIL_BELOW_PB)

    flags: list[str] = []
    if p_b_psia > 0 and p_wf_psia < p_b_psia * (1.0 + BUBBLE_POINT_PROXIMITY_FRACTION):
        flags.append(
            f"p_wf is within {BUBBLE_POINT_PROXIMITY_FRACTION:.0%} of the bubble point; "
            "Ahmed's Figure 7-6 shows (k_ro/mu_o B_o) already moving as p approaches p_b "
            "from above, so J is starting to drift. This band is a house rule, not Ahmed's.")
    if p_b_psia == 0.0:
        flags.append("p_b_psia = 0.0 was asserted by the caller: the reservoir is taken to be "
                     "undersaturated everywhere, so no bubble-point check can bind")

    return Quantity(
        drawdown_psi, "psi",
        "linear productivity index, Dp = Q_o/J (Ahmed Eq. 7-1/7-7, oil, above the bubble point)",
        OIL,
        inputs={"form": "oil-linear-j", "p_r_psia": p_r_psia, "q_stb_d": q_stb_d,
                "j_stb_d_psi": j_stb_d_psi, "p_b_psia": p_b_psia,
                "p_wf_psia": p_wf_psia, "aof_stb_d": aof_stb_d},
        assumptions={"form": FORMS["oil-linear-j"],
                     "pseudosteady_state": PSEUDOSTEADY_STATE,
                     "validity_window": "p_r > p_b and p_wf >= p_b; J constant over the "
                                        "whole drawdown (#104, p. 481)",
                     "rate_basis": "q_stb_d must be measured on the same basis as J. Eq. 7-1 "
                                   "is defined for water-free oil production; if J came from a "
                                   "total-liquid test, the result is a total-liquid drawdown "
                                   "and this tool cannot tell the difference",
                     "bubble_point_proximity_band": HOUSE_RULE},
        flags=tuple(flags))


# --- gas, Eq. 8-12 --------------------------------------------------------
def _gas_pressure_squared(p_r_psia: float, q_mscf_d: float,
                          j_mscf_d_psi2: float) -> Quantity | Refusal:
    if p_r_psia <= 0:
        raise ValueError("p_r_psia must be positive")
    if j_mscf_d_psi2 <= 0:
        raise ValueError("j_mscf_d_psi2 must be positive; Eq. 8-12 divides by it")
    if q_mscf_d < 0:
        raise ValueError("q_mscf_d must be >= 0")

    # R7 - out of Region III. Ahmed's own Example 8-1(b) applies the
    # pressure-squared method at p_r = 2000 exactly ("Because p_r and p_wf =
    # 2000, use the pressure-squared approximation"), so the boundary is
    # inclusive and this fires on > 2000, not >= 2000.
    if p_r_psia > REGION_III_MAX_PSIA:
        region = ("Region II (2000-3000 psi), where \"the pressure function shows distinct "
                  "curvature\"" if p_r_psia <= REGION_I_MIN_PSIA
                  else "Region I (above 3000 psi), where the pressure-approximation form "
                       "applies and no productivity index exists for it")
        return Refusal(
            reason=f"p_r = {p_r_psia:g} psia is above the {REGION_III_MAX_PSIA:g} psi ceiling "
                   f"on Eq. 8-12. Ahmed #112, p. 537: the (mu_g z) product is essentially "
                   "constant only below 2000 psi (Golan and Whitson 1986), which is what "
                   f"collapses Eq. 8-11 into a linear J. This is {region}.",
            needed=("form='gas-pseudopressure' — Eq. 8-1 is the form Ahmed directs to here, "
                    "and it returns a pseudopressure drop in psi^2/cp, not psi",
                    "psi_r_psi2_cp and a J in Mscf/day/(psi^2/cp) from Eq. 8-2"),
            source=GAS)

    # Eq. 8-12 inverted: p_wf = sqrt(p_r^2 - Q_g/J).
    aof_mscf_d = j_mscf_d_psi2 * p_r_psia ** 2        # Eq. 8-13
    radicand = p_r_psia ** 2 - q_mscf_d / j_mscf_d_psi2

    # R5 - beyond AOF; the radicand goes negative and there is no real p_wf.
    if radicand < 0:
        return Refusal(
            reason=f"q = {q_mscf_d:g} Mscf/day exceeds the absolute open flow potential "
                   f"AOF = J p_r^2 = {aof_mscf_d:g} Mscf/day (Eq. 8-13); p_r^2 - Q_g/J is "
                   "negative, so no real flowing pressure satisfies Eq. 8-12.",
            needed=(f"a rate at or below AOF = {aof_mscf_d:g} Mscf/day",),
            source=GAS)

    p_wf_psia = math.sqrt(radicand)
    drawdown_psi = p_r_psia - p_wf_psia

    flags: list[str] = []
    if _REGION_III_PROXIMITY_PSIA < p_r_psia <= REGION_III_MAX_PSIA:
        flags.append(f"p_r = {p_r_psia:g} psia is close to the {REGION_III_MAX_PSIA:g} psi "
                     "edge of Ahmed's Region III (\"usually less than 2000 psi\"); the "
                     "(mu_g z)-constant assumption behind Eq. 8-12 is at its limit")

    return Quantity(
        drawdown_psi, "psi",
        "pressure-squared productivity index, p_wf = sqrt(p_r^2 - Q_g/J) "
        "(Ahmed Eq. 8-12, gas, Region III)",
        GAS,
        inputs={"form": "gas-pressure-squared", "p_r_psia": p_r_psia, "q_mscf_d": q_mscf_d,
                "j_mscf_d_psi2": j_mscf_d_psi2, "p_wf_psia": p_wf_psia,
                "aof_mscf_d": aof_mscf_d},
        assumptions={"form": FORMS["gas-pressure-squared"],
                     "pseudosteady_state": PSEUDOSTEADY_STATE,
                     "validity_window": f"p_r and p_wf both below {REGION_III_MAX_PSIA:g} psi "
                                        "(#112, p. 538); (mu_g z) taken as constant over the "
                                        "drawdown",
                     "j_source": "Eq. 8-14, J = kh / [1422 T (mu_g z)_avg (ln(r_e/r_w) - 0.75 "
                                 "+ s)]; this tool takes J rather than deriving it"},
        flags=tuple(flags))


# --- gas, Eqs. 8-3 / 8-5 --------------------------------------------------
def _gas_pseudopressure(q_mscf_d: float, j_mscf_d_psi2_cp: float,
                        psi_r_psi2_cp: float | None) -> Quantity | Refusal:
    if j_mscf_d_psi2_cp <= 0:
        raise ValueError("j_mscf_d_psi2_cp must be positive; Eq. 8-3 divides by it")
    if q_mscf_d < 0:
        raise ValueError("q_mscf_d must be >= 0")
    if psi_r_psi2_cp is not None and psi_r_psi2_cp < 0:
        raise ValueError("psi_r_psi2_cp must be >= 0")

    # Eq. 8-5 inverted: Dpsi = Q_g / J. The exact analogue of Eq. 7-7, and the
    # one Ahmed himself draws the analogy for.
    drawdown_psi2_cp = q_mscf_d / j_mscf_d_psi2_cp

    inputs: dict[str, Any] = {"form": "gas-pseudopressure", "q_mscf_d": q_mscf_d,
                              "j_mscf_d_psi2_cp": j_mscf_d_psi2_cp}
    if psi_r_psi2_cp is not None:
        aof_mscf_d = j_mscf_d_psi2_cp * psi_r_psi2_cp   # Eq. 8-4
        psi_wf = psi_r_psi2_cp - drawdown_psi2_cp
        # R8 - beyond AOF; psi_wf would be negative.
        if psi_wf < 0:
            return Refusal(
                reason=f"q = {q_mscf_d:g} Mscf/day exceeds the absolute open flow potential "
                       f"AOF = J psi_r = {aof_mscf_d:g} Mscf/day (Eq. 8-4); it implies a "
                       f"flowing pseudopressure of {psi_wf:g} psi^2/cp, which cannot be "
                       "negative.",
                needed=(f"a rate at or below AOF = {aof_mscf_d:g} Mscf/day",),
                source=GAS)
        inputs["psi_r_psi2_cp"] = psi_r_psi2_cp
        inputs["psi_wf_psi2_cp"] = psi_wf
        inputs["aof_mscf_d"] = aof_mscf_d

    flags = [
        _PSEUDOPRESSURE_FLAG + ": this value is a real-gas pseudopressure drop in psi^2/cp, "
        "NOT a pressure drop in psi. Converting it to psi requires inverting the m(p) "
        "integral against this gas's psi(p) table and is out of scope here (see "
        "pseudopressure, #81).",
    ]
    if psi_r_psi2_cp is None:
        flags.append("no psi_r_psi2_cp supplied, so the flowing pseudopressure psi_wf could "
                     "not be reported and the AOF check (Eq. 8-4) did not run")

    return Quantity(
        drawdown_psi2_cp, "psi^2/cp",
        "pseudopressure productivity index, Dpsi = Q_g/J (Ahmed Eqs. 8-3/8-5, gas, "
        "all pressure regions)",
        GAS,
        inputs=inputs,
        assumptions={"form": FORMS["gas-pseudopressure"],
                     "pseudosteady_state": PSEUDOSTEADY_STATE,
                     "validity_window": "none on pressure — Eq. 8-1, which Eq. 8-3 restates "
                                        "with J, is applicable to all ranges of pressure",
                     "j_source": "Eq. 8-2, J = kh / [1422 T (ln(r_e/r_w) - 0.75 + s)]; this "
                                 "tool takes J rather than deriving it",
                     "psi_basis": "psi_r_psi2_cp must be on the same psi(p) table as the psi "
                                  "that J was measured against"},
        flags=tuple(flags))
