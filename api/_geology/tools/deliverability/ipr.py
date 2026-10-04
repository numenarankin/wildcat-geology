"""Tools #86 `gas_ipr_curve` and #57 `gas_ipr`. Ahmed Ch. 8, "Gas Well Performance".

Merges into `tools/deliverability.py`, replacing the `gas_ipr_curve` at line 117.

**#57 was missing from the tree entirely** when this file was tested — the same
accident `tools/inflow.py` records for `drawdown_estimate` (#56), which "was
written once inside `tools/deliverability.py` and lost when that module became a
package". `specs/57-gas_ipr.md` names this module as its destination and settles
the catalog's "§11's `gas_ipr_curve` replaces §6's `gas_ipr`" (tool-catalog.md:21)
as a statement about catalog *wording*: the two tools are the two halves of
Ahmed's Example 8-2. #57 takes the raw test points and fits (Steps 1-5); #86
takes an already-fitted relationship and tabulates it (Step 6). #57 is therefore
implemented here as an orchestrator with **no rate arithmetic and no fit
arithmetic of its own** — it validates, calls `backpressure_fit`/`houpeurt_fit`,
and reads its curve out of `gas_ipr_curve` and its headline AOF out of
`aof_compute`, so all four tools cannot drift apart on the same test.

Three decisions worth stating, because none of them is the obvious one:

**It returns a list of Quantity, one per curve point, not a single Quantity.**
The version being replaced returned `Quantity(curve[-1][1], ..., inputs={"curve":
curve})` — the last point as the headline value, the curve itself as bare tuples
inside `inputs`. That makes the reported number an accident of where the grid
happens to stop (it is the AOF only while the grid always ends at p_wf = 0), and
it routes every other point around the no-orphan-numbers contract that
`result.py` and the harness's `addComputed()` both enforce: a caller can quote
3,406 Mscf/d out of `inputs["curve"]` with no method attached to that number. An
IPR curve is a function, so `Range` (specified as a band) is not the answer
either. One Quantity per point is the contract read literally: every rate an
operator might act on carries its own method, source and inputs, the order is
preserved, and the AOF point is labelled rather than inferred from position.

**It does no rate arithmetic.** The catalog requires this tool to share one
evaluator with `aof_compute`, and it does: every point goes through
`deliverability_rate`. Ahmed's four forms already disagree by 23% on one test
(#116 p. 559); a second evaluator would let them drift further, and the AOF would
stop being the p_wf = 0 point of this curve by construction.

**`form` is required and cross-checked, not inherited.** tool-verification.md:111
names this tool: the same test gives a = 318 in the pressure-squared form and
a2 = 22.28e3 in the pseudopressure form, with b six orders of magnitude apart. A
caller who believes they hold a p-squared fit and actually holds a psi fit gets a
refusal here rather than a plausible wrong curve.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from ..result import Quantity, Range, Refusal
from .rate import deliverability_rate, aof_compute  # the one shared evaluator
from .backpressure import backpressure_fit          # #82, the only C/n fit
from .houpeurt import houpeurt_fit                  # #83, the only a/b fit

AHMED_CH8 = "00-reference/ahmed-reservoir-engineering-handbook#114"
AHMED_EX82 = "00-reference/ahmed-reservoir-engineering-handbook#115"
AHMED_EX82_PSI = "00-reference/ahmed-reservoir-engineering-handbook#116"

#: The three coefficient forms of Chapter 8, and the rate equation each one is
#: inverted through. Keyed exactly as the group-I fit contract writes
#: `assumptions["form"]`.
DELIVERABILITY_FORMS: dict[str, dict[str, str]] = {
    "pressure-squared": {
        "driving_force": "p_r^2 - p_wf^2, psi^2",
        "equations": "Ahmed Eq. 8-20 (Rawlins-Schellhardt) / Eq. 8-28 (LIT)",
        "page": "543, 546",
    },
    "pressure-approximation": {
        "driving_force": "p_r - p_wf, psi",
        "equations": "Ahmed Eq. 8-33",
        "page": "548",
    },
    "pseudopressure": {
        "driving_force": "psi_r - psi_wf, psi^2/cp",
        "equations": "Ahmed Eq. 8-38",
        "page": "549",
    },
}

#: The models the group-I fit contract can produce, and which coefficient key
#: each one puts on the fit alongside `.value`.
DELIVERABILITY_MODELS: dict[str, str] = {
    "Rawlins-Schellhardt": "n",   # .value = C, .inputs["n"] = n
    "Houpeurt-LIT": "b",          # .value = a, .inputs["b"] = b
}

#: Stated pressure ranges, Ahmed Chapter 8. These are the source's own words and
#: are flags, not refusals: Ahmed's Example 8-2 runs the pressure-approximation
#: form at p_r = 1952 psia, well below its own stated floor, and reports it as the
#: worst of four at 11% error. Refusing would make the published example
#: unreproducible while the source itself demonstrates the calculation.
FORM_PRESSURE_RANGE_PSIA: dict[str, dict[str, Any]] = {
    "pressure-squared": {
        "max_p_r": 2000.0,
        "quote": "This method is recommended for applications at pressures "
                 "below 2000 psi.",
        "page": 546,
    },
    "pressure-approximation": {
        "min_p_r": 3000.0,
        "quote": "the pressure method is applicable at pressures higher than "
                 "3000 psi",
        "page": 548,
    },
    # Pseudopressure has no range limit: "the pseudopressure approach is more
    # rigorous ... and is applicable to all ranges of pressure" (#114, p. 549).
    "pseudopressure": {},
}

#: Ahmed Eq. 8-20's stated bounds on the back-pressure exponent, #114 p. 543:
#: "n may vary from 1.0 for completely laminar flow to 0.5 for fully turbulent
#: flow." Physical bounds, flagged rather than refused — the source never says a
#: fit outside the band is invalid.
BACKPRESSURE_N_BAND = (0.5, 1.0)

#: The LIT derivation's four stated assumptions, #114 p. 546. Carried on every
#: LIT point so a caller cannot lose them.
LIT_ASSUMPTIONS = (
    "single phase flow in the reservoir",
    "homogeneous and isotropic reservoir system",
    "permeability independent of pressure",
    "(mu_g * z) constant",
)

#: #116 p. 559: back-pressure 8980, p-squared 8763, p-approximation 10827,
#: pseudopressure 8536 Mscf/d on one three-point test.
METHOD_SPREAD_NOTE = (
    "form-dependent: Ahmed's four forms span 8536-10827 Mscf/d (23%) on the same "
    "test data (#116, p. 559) - quote the form with the rate"
)

DEFAULT_N_POINTS = 11


def gas_ipr_curve(
    fit: Quantity,
    form: str,
    p_wf_grid: Sequence[float] | None = None,
    n_points: int | None = None,
    psi_of_p: Callable[[float], float] | None = None,
    psi_wf_grid: Sequence[float] | None = None,
) -> list[Quantity] | Refusal:
    """Tabulate the gas IPR from a fitted deliverability relationship.

    Ahmed's own procedure, stated once per form in #114 and executed four times in
    Example 8-2: "by assuming various values of p_wf and calculating the
    corresponding Q_g from Equation 8-28, the current IPR of the gas well at the
    current reservoir pressure p_r can be generated" (#114, p. 546).

    `fit` comes from `backpressure_fit` or `houpeurt_fit` and supplies p_r; there
    is deliberately no `p_r_psia` argument. Redrawing the curve at a different
    reservoir pressure is Ahmed's *future* IPR (Eqs. 8-40 to 8-44, #116 p. 560),
    which needs mu_g*z or mu_g*Bg at both pressures. Accepting a p_r here would
    silently produce that answer without its correction.

    Returns one `Quantity` per grid point in descending p_wf (Ahmed's table
    order), or a `Refusal`.
    """
    # ---- the fit must be a deliverability fit this source supports -----------
    if not isinstance(fit, Quantity):
        return Refusal(
            reason="gas_ipr_curve needs a fitted deliverability relationship, not "
                   f"a {type(fit).__name__}",
            needed=("a Quantity from backpressure_fit or houpeurt_fit",),
            source=AHMED_CH8,
        )
    model = fit.assumptions.get("model")
    if model not in DELIVERABILITY_MODELS:
        return Refusal(
            reason=f"fit carries model {model!r}; Ahmed Chapter 8 supports only "
                   "Rawlins-Schellhardt (Eq. 8-20) and Houpeurt-LIT "
                   "(Eqs. 8-28/8-33/8-38)",
            needed=("fit.assumptions['model'] in "
                    f"{sorted(DELIVERABILITY_MODELS)}",),
            source=AHMED_CH8,
        )
    second_key = DELIVERABILITY_MODELS[model]
    second = fit.inputs.get(second_key)
    if fit.value is None or second is None:
        return Refusal(
            reason=f"{model} fit is missing a coefficient: needs .value and "
                   f".inputs[{second_key!r}]",
            needed=(f"fit.inputs['{second_key}']",),
            source=AHMED_CH8,
        )

    # ---- the requested form must be the form the fit was taken in -----------
    if form not in DELIVERABILITY_FORMS:
        raise ValueError(
            f"form must be one of {sorted(DELIVERABILITY_FORMS)}, got {form!r}")
    fit_form = fit.assumptions.get("form")
    if fit_form != form:
        return Refusal(
            reason=f"fit is in the {fit_form!r} form and cannot serve a {form!r} "
                   "curve; the coefficients are in different units (a = 318 in "
                   "the pressure-squared form vs a2 = 22.28e3 in the "
                   "pseudopressure form on Ahmed's own test data)",
            needed=(f"a fit whose assumptions['form'] is {form!r}",),
            source=AHMED_CH8,
        )

    p_r = fit.inputs.get("p_r_psia")
    if p_r is None or p_r <= 0:
        return Refusal(
            reason="fit carries no positive average reservoir pressure; every "
                   "form of the rate equation is driven by a difference from p_r",
            needed=("fit.inputs['p_r_psia']",),
            source=AHMED_CH8,
        )

    # ---- the grid ------------------------------------------------------------
    if p_wf_grid is not None and n_points is not None:
        raise ValueError("pass p_wf_grid or n_points, not both")
    if p_wf_grid is not None:
        grid = [float(p) for p in p_wf_grid]
        grid_note = "caller-supplied p_wf grid"
    else:
        count = DEFAULT_N_POINTS if n_points is None else int(n_points)
        if count < 2:
            return Refusal(
                reason=f"a curve needs at least two points; {count} requested",
                needed=("n_points >= 2",),
                source=AHMED_CH8,
            )
        grid = [p_r * (1.0 - i / (count - 1)) for i in range(count)]
        grid_note = (f"uniform {count}-point grid from p_r to 0; Ahmed's own "
                     "sweep is irregular and unexplained, so this is the tool's "
                     "choice, not the source's")
    if len(grid) < 2:
        return Refusal(
            reason=f"a curve needs at least two points; {len(grid)} supplied",
            needed=("at least two p_wf values",),
            source=AHMED_CH8,
        )

    above = [p for p in grid if p > p_r]
    if above:
        return Refusal(
            reason=f"p_wf grid reaches {max(above):.6g} psia, above the "
                   f"reservoir pressure {p_r:.6g} psia; p_r^2 - p_wf^2 is then "
                   "negative and Ahmed Eq. 8-20 has no real rate - that is "
                   "injection, not inflow",
            needed=("every p_wf <= p_r",),
            source=AHMED_CH8,
        )
    below = [p for p in grid if p < 0]
    if below:
        return Refusal(
            reason=f"p_wf grid contains {min(below):.6g} psia, which is not a "
                   "pressure",
            needed=("every p_wf >= 0",),
            source=AHMED_CH8,
        )

    # ---- pseudopressure needs psi_wf per point -------------------------------
    psi_r = fit.inputs.get("psi_r")
    psi_values: list[float | None] = [None] * len(grid)
    if form == "pseudopressure":
        if psi_r is None:
            return Refusal(
                reason="pseudopressure form: the fit carries no psi_r, and Eq. "
                       "8-38 is driven by (psi_r - psi_wf); psi_r is not "
                       "recoverable from p_r alone",
                needed=("fit.inputs['psi_r']",),
                source=AHMED_CH8,
            )
        if psi_wf_grid is not None:
            if len(psi_wf_grid) != len(grid):
                raise ValueError(
                    f"psi_wf_grid has {len(psi_wf_grid)} values for "
                    f"{len(grid)} p_wf points")
            psi_values = [float(v) for v in psi_wf_grid]
        elif psi_of_p is not None:
            psi_values = [float(psi_of_p(p)) for p in grid]
        else:
            return Refusal(
                reason="pseudopressure form needs psi_wf at every p_wf and no p "
                       "-> psi conversion was supplied; Ahmed reads psi off "
                       "Figure 8-8, an image, and the corpus gives no "
                       "interpolation rule",
                needed=("psi_of_p (e.g. the pseudopressure tool bound to the "
                        "fluid properties) or psi_wf_grid",),
                source=AHMED_CH8,
            )

    # ---- flags that ride on every point --------------------------------------
    curve_flags: list[str] = [METHOD_SPREAD_NOTE]
    rng = FORM_PRESSURE_RANGE_PSIA[form]
    if "max_p_r" in rng and p_r > rng["max_p_r"]:
        curve_flags.append(
            f"p_r = {p_r:.6g} psia is above the {form} form's stated range "
            f"(Ahmed #114 p. {rng['page']}: \"{rng['quote']}\")")
    if "min_p_r" in rng and p_r < rng["min_p_r"]:
        curve_flags.append(
            f"p_r = {p_r:.6g} psia is below the {form} form's stated range "
            f"(Ahmed #114 p. {rng['page']}: \"{rng['quote']}\")")
    if model == "Rawlins-Schellhardt":
        n_exp = float(second)
        lo, hi = BACKPRESSURE_N_BAND
        if not lo <= n_exp <= hi:
            curve_flags.append(
                f"back-pressure exponent n = {n_exp:.4g} is outside {lo}-{hi}, "
                "the laminar-to-fully-turbulent band of Ahmed #114 p. 543")
    else:
        curve_flags.append("LIT derivation assumes " + "; ".join(LIT_ASSUMPTIONS))
    curve_flags.extend(f"from fit: {f}" for f in fit.flags)

    order = sorted(range(len(grid)), key=lambda i: -grid[i])
    n_pts = len(grid)
    curve: list[Quantity] = []

    for position, i in enumerate(order):
        p_wf = grid[i]
        psi_wf = psi_values[i]
        # The one evaluator, shared with aof_compute. No rate arithmetic here.
        rate = deliverability_rate(fit, p_wf_psia=p_wf, psi_wf=psi_wf)
        if isinstance(rate, Refusal):
            return Refusal(
                reason=f"at p_wf = {p_wf:.6g} psia: {rate.reason}",
                needed=rate.needed,
                source=rate.source or AHMED_CH8,
            )

        is_aof = p_wf == 0.0
        point_inputs: dict[str, Any] = {
            "p_wf_psia": p_wf,
            "p_r_psia": p_r,
            DELIVERABILITY_MODELS[model]: second,
            "coefficient": fit.value,
        }
        if psi_wf is not None:
            point_inputs["psi_wf"] = psi_wf
            point_inputs["psi_r"] = psi_r

        point_flags = list(curve_flags)
        if is_aof:
            point_flags.append(
                "aof-point: p_wf = 0, so this is the absolute open flow for this "
                "form - identical to aof_compute on the same fit")

        curve.append(Quantity(
            rate.value,
            "Mscf/d",
            f"gas IPR point, {model} {form} form "
            f"({DELIVERABILITY_FORMS[form]['equations']})",
            AHMED_EX82_PSI if form == "pseudopressure" else AHMED_EX82,
            inputs=point_inputs,
            assumptions={
                "form": form,
                "model": model,
                "driving_force": DELIVERABILITY_FORMS[form]["driving_force"],
                "grid": grid_note,
                "curve_index": position,
                "curve_points": n_pts,
                "role": "AOF" if is_aof else "IPR point",
                "procedure": "Ahmed #114 p. 546: assume values of p_wf, solve the "
                             "deliverability equation for Q_g",
            },
            flags=tuple(point_flags),
        ))

    return curve


# ===========================================================================
# #57 — gas_ipr. A test in, an AOF and its IPR out.
# ===========================================================================
#
# specs/57-gas_ipr.md. The distinction from #86 above: this one is handed the
# *test* — (p_wf, Q_g) pairs and p_r — and is the only tool in the chain that
# ever sees the data points, so it is the only one that can refuse on their
# quality. It fits nothing itself; #82/#83 own the fits and `deliverability_rate`
# owns the rates.

#: The methods of Ahmed Example 8-2 this tool will run, and the fit each maps to.
#: Both are pressure-squared: Q_g = C(p_r^2 - p_wf^2)^n (Eq. 8-20) and
#: p_r^2 - p_wf^2 = a Q_g + b Q_g^2 (Eq. 8-24, inverted as Eq. 8-28). A gas IPR
#: is written on p^2 or on psi, never on p, and never as Vogel's oil equation —
#: tool-verification.md:27 records the citation matcher landing this family in
#: Ahmed's *oil* chapter on the bare word "IPR".
GAS_IPR_METHODS: dict[str, dict[str, str]] = {
    "backpressure": {
        "model": "Rawlins-Schellhardt",
        "form": "pressure-squared",
        "equations": "Ahmed Eqs. 8-20/8-22/8-23",
        "driving_force": "p_r^2 - p_wf^2, psi^2",
        "coefficients": ("C", "n"),
    },
    "lit-pressure-squared": {
        "model": "Houpeurt-LIT",
        "form": "pressure-squared",
        "equations": "Ahmed Eqs. 8-24/8-27/8-28",
        "driving_force": "p_r^2 - p_wf^2, psi^2",
        "coefficients": ("a", "b"),
    },
}

#: The two forms Ahmed publishes that this tool refuses rather than approximates,
#: with the reason quoted from the source. Refusing is the point: substituting a
#: neighbouring form silently would move Example 8-2's answer by up to 23%.
GAS_IPR_REFUSED_METHODS: dict[str, dict[str, Any]] = {
    "lit-pressure": {
        "reason": (
            "the pressure-approximation form (Ahmed Eqs. 8-29 to 8-33) is "
            "applicable only above 3000 psi - \"It should be noted that the "
            "pressure-approximation method is limited to applications for "
            "pressures greater than 3000 psi\" (#116, p. 559) - and Ahmed's own "
            "Example 8-2 runs it at 1952 psia and reports it as the worst of "
            "four methods, 11% average error, AOF 10827 against the rigorous "
            "8536 Mscf/d. This tool returns a single bookable AOF and will not "
            "return that one"),
        "needed": ("method='backpressure' or 'lit-pressure-squared'",
                   "or houpeurt_fit (#83), which owns the form selector and "
                   "will fit a1/b1 with the range flag attached"),
    },
    "pseudopressure": {
        "reason": (
            "the pseudopressure form (Ahmed Eqs. 8-34 to 8-38) is driven by "
            "(psi_r - psi_wf), not by pressure: its coefficients came out "
            "a2 = 22.28e3 against a = 318 in the pressure-squared form on the "
            "same test, six orders of magnitude apart on b. psi_wf cannot be "
            "inferred from p_wf - it is the well's own m(p) integral, and Ahmed "
            "reads it off Figure 8-8, an image"),
        "needed": ("psi_wf at every test point and psi_r, from pseudopressure "
                   "(#81) on Ahmed's convention (m(p) integrated from p = 0)",
                   "then houpeurt_fit (#83, form='pseudopressure') and "
                   "gas_ipr_curve (#86)"),
    },
}

#: Ahmed #114 p. 543, on Eq. 8-20's exponent: "the exponent n may vary from 1.0
#: for completely laminar flow to 0.5 for fully turbulent flow." #82 *flags* a
#: fit outside this band; #57 *refuses* (spec R7). Deliberate and recorded: #82
#: hands an analyst a coefficient to inspect, #57 hands an operator a single AOF
#: to book capacity against, and an AOF from an n of 1.4 is not interpretable.
GAS_IPR_N_BAND = (0.5, 1.0)

#: Ahmed #114 p. 545: the back-pressure test is a "three-point or four-point flow
#: test". Two points fit Eq. 8-21 exactly with no residual, so the fit cannot be
#: falsified by the data - answered, but flagged.
GAS_IPR_MIN_POINTS = 2
GAS_IPR_RECOMMENDED_POINTS = 3

#: Default grid resolution: `steps` intervals from p_r down to 0 inclusive, so
#: `steps + 1` points and p_wf = 0 always on the curve. 10 matches #86's
#: DEFAULT_N_POINTS of 11 points. Ahmed's own sweep (1952, 1800, 1600, 1000,
#: 500, 0) is irregular and unexplained, so the uniform grid is this tool's
#: choice and says so in `assumptions`.
GAS_IPR_DEFAULT_STEPS = 10

#: #114 p. 545: "It is required that each rate be maintained sufficiently long
#: for the well to stabilize." Eq. 8-39 estimates how long from phi, S_g, mu_g,
#: r_e, k and p_r - none of which this tool receives.
GAS_IPR_STABILIZATION_NOTE = (
    "assumed, not checked: Ahmed #114 p. 545 requires every rate to be "
    "stabilized (pseudosteady state) and estimates the time from Eq. 8-39 out of "
    "phi, S_g, mu_g, r_e, k, p_r, none of which this tool is given - see "
    "deliverability_test_interpret (#85)")


def gas_ipr(points: Sequence[Sequence[float]],
            p_r_psia: float,
            method: str = "backpressure",
            p_wf_psia: Sequence[float] | None = None,
            steps: int = GAS_IPR_DEFAULT_STEPS) -> Quantity | Refusal:
    """Absolute open flow and the IPR behind it, from a multi-point gas test.

    Ahmed Example 8-2 end to end (#115 pp. 552-557): fit the deliverability
    relationship to the test points, then evaluate it down to p_wf = 0.

        "Equation 8-20 is commonly called the deliverability or back-pressure
        equation. If the coefficients of the equation (i.e., n and C) can be
        determined, the gas flow rate Q_g at any bottom-hole flow pressure p_wf
        can be calculated and the IPR curve constructed." - #114, p. 543

    points      [(p_wf_psia, qg_mscf_d), ...] stabilized test points. The
                shut-in row (p_r, 0) is not a flow point; drop it.
    p_r_psia    shut-in volumetric average reservoir pressure, psia (not psig).
    method      "backpressure" (default) | "lit-pressure-squared" |
                "lit-pressure" (refused) | "pseudopressure" (refused).
    p_wf_psia   explicit flowing pressures to tabulate; default is a uniform
                grid from p_r down to 0.
    steps       grid intervals when `p_wf_psia` is not given; steps + 1 points.

    Returns a `Quantity` whose `.value` is the AOF in Mscf/d - `aof_compute` on
    the fit, i.e. the fit at p_wf = 0, never a curve endpoint that happens to be
    last - with the fitted coefficients, the form, and the whole IPR curve as
    `Quantity` objects in `inputs["curve"]`. Or a `Refusal`.
    """
    # ---- R1/R2/R3: the method, before anything is computed -------------------
    if method in GAS_IPR_REFUSED_METHODS:
        refused = GAS_IPR_REFUSED_METHODS[method]
        return Refusal(
            reason=f"gas_ipr does not run the {method!r} method: "
                   + refused["reason"],
            needed=refused["needed"],
            source=AHMED_CH8,
        )
    if method not in GAS_IPR_METHODS:
        return Refusal(
            reason=f"unknown method {method!r}; Ahmed Chapter 8 publishes four "
                   "deliverability methods and this tool runs two of them: "
                   "'backpressure' (Eq. 8-20), 'lit-pressure-squared' "
                   "(Eq. 8-28), 'lit-pressure' (Eq. 8-33, refused - above "
                   "3000 psi only) and 'pseudopressure' (Eq. 8-38, refused - "
                   "needs psi_wf)",
            needed=(f"method in {sorted(GAS_IPR_METHODS)} "
                    f"(refused: {sorted(GAS_IPR_REFUSED_METHODS)})",),
            source=AHMED_CH8,
        )
    spec = GAS_IPR_METHODS[method]

    if p_r_psia is None or p_r_psia <= 0:
        return Refusal(
            reason=f"average reservoir pressure {p_r_psia!r} is not a positive "
                   "psia; every form of the deliverability equation is driven "
                   "by a difference from p_r",
            needed=("p_r_psia, psia (absolute, not gauge)",),
            source=AHMED_CH8,
        )

    # ---- R4/R5/R6: the test data --------------------------------------------
    pts = [tuple(p) for p in points] if points else []
    if len(pts) < GAS_IPR_MIN_POINTS:
        return Refusal(
            reason=f"a deliverability fit needs at least {GAS_IPR_MIN_POINTS} "
                   f"flow points and {len(pts)} were given; Eq. 8-22 reads the "
                   "exponent n off two points of the deliverability line, and "
                   "Ahmed's procedure is a three-point or four-point flow test "
                   "(#114, p. 545)",
            needed=(f"at least {GAS_IPR_MIN_POINTS} (p_wf_psia, qg_mscf_d) "
                    "stabilized test points",),
            source=AHMED_CH8,
        )
    for i, point in enumerate(pts):
        if len(point) != 2:
            return Refusal(
                reason=f"test point {i + 1} is {point!r}; each point is "
                       "(p_wf_psia, qg_mscf_d)",
                needed=("two-element test points, pressure first",),
                source=AHMED_CH8,
            )
        p_wf, qg = float(point[0]), float(point[1])
        if p_wf >= p_r_psia:
            return Refusal(
                reason=f"test point {i + 1} has p_wf = {p_wf:.6g} psia at or "
                       f"above the reservoir pressure {p_r_psia:.6g} psia, so "
                       "p_r^2 - p_wf^2 <= 0 and Eq. 8-21 has no logarithm. The "
                       "shut-in row of a deliverability table is not a flow "
                       "point - drop it before fitting",
                needed=("every test point with p_wf strictly below p_r",),
                source=AHMED_CH8,
            )
        if qg <= 0:
            return Refusal(
                reason=f"test point {i + 1} has Q_g = {qg:.6g} Mscf/d at "
                       f"p_wf = {p_wf:.6g} psia; a non-positive rate is not a "
                       "flow point and Eq. 8-21 needs log(Q_g)",
                needed=("a positive stabilized gas rate at every test point",),
                source=AHMED_CH8,
            )
    distinct = {float(p[0]) for p in pts}
    if len(distinct) < 2:
        return Refusal(
            reason=f"the {len(pts)} test points share the flowing pressure "
                   f"{distinct.pop():.6g} psia, so every point has the same "
                   "driving force, the deliverability line is vertical and its "
                   "slope is undefined",
            needed=("test points at genuinely different drawdowns",),
            source=AHMED_CH8,
        )

    # ---- the fit: #82 or #83, never arithmetic here --------------------------
    if spec["model"] == "Rawlins-Schellhardt":
        fit = backpressure_fit(pts, p_r_psia, form="pressure-squared",
                               method="least-squares")
    else:
        fit = houpeurt_fit(pts, p_r_psia, form="pressure-squared")
    if isinstance(fit, Refusal):
        return fit

    # ---- R7: the turbulence exponent must mean something ---------------------
    lo, hi = GAS_IPR_N_BAND
    if spec["model"] == "Rawlins-Schellhardt":
        n_fitted = float(fit.inputs["n"])
        if not lo <= n_fitted <= hi:
            return Refusal(
                reason=f"the fitted back-pressure exponent n = {n_fitted:.4f} "
                       f"is outside {lo}-{hi}: Ahmed #114 p. 543 gives n = 1.0 "
                       "for completely laminar flow and n = 0.5 for fully "
                       "turbulent flow, so a fit outside that band means the "
                       "test data (or the reported average reservoir pressure) "
                       "is wrong, and an AOF computed from it is not "
                       "interpretable. backpressure_fit (#82) will return the "
                       "coefficient with a flag if you want to inspect it",
                needed=("test points whose log-log deliverability slope falls "
                        f"in {lo}-{hi}",
                        "a verified stabilized average reservoir pressure"),
                source=AHMED_CH8,
            )

    # ---- the curve and the AOF: #86 and #84, one shared evaluator ------------
    if p_wf_psia is not None:
        grid = [float(p) for p in p_wf_psia]
        grid_note = "caller-supplied p_wf grid"
    else:
        n_steps = int(steps)
        if n_steps < 1:
            return Refusal(
                reason=f"steps = {n_steps} gives fewer than two grid points; a "
                       "curve needs at least two",
                needed=("steps >= 1, or an explicit p_wf_psia grid",),
                source=AHMED_CH8,
            )
        grid = [p_r_psia * (1.0 - i / n_steps) for i in range(n_steps + 1)]
        grid[-1] = 0.0          # the AOF row of Ahmed's table, exactly zero
        grid_note = (f"uniform {n_steps + 1}-point grid from p_r to 0; Ahmed's "
                     "own sweep is irregular and unexplained, so this is the "
                     "tool's choice, not the source's")

    curve = gas_ipr_curve(fit, spec["form"], p_wf_grid=grid)
    if isinstance(curve, Refusal):
        return curve

    aof = aof_compute(fit)      # the fit at p_wf = 0, by definition, not by grid
    if isinstance(aof, Refusal):
        return aof

    # ---- flags: caveats that do not invalidate the answer --------------------
    flags: list[str] = []
    if len(pts) < GAS_IPR_RECOMMENDED_POINTS:
        flags.append(
            f"two-point-fit-has-no-residual: {len(pts)} points fit the "
            "deliverability line exactly, so the fit cannot be checked against "
            "the data; Ahmed's test is a three-point or four-point flow test "
            "(#114, p. 545)")
    if p_r_psia > 2000.0:
        if method == "lit-pressure-squared":
            flags.append(
                f"p_r = {p_r_psia:.6g} psia is above the pressure-squared "
                "form's stated range: \"This method is recommended for "
                "applications at pressures below 2000 psi\" (#114, p. 546)")
        else:
            flags.append(
                f"p_r = {p_r_psia:.6g} psia: Ahmed sets no explicit pressure "
                "limit on Eq. 8-20 itself, but measures the back-pressure "
                "equation at 6.0% average error against the pseudopressure "
                "answer (#116, p. 559)")
    flags.append(METHOD_SPREAD_NOTE)
    flags.extend(f"from fit: {f}" for f in fit.flags)

    coef_names = spec["coefficients"]
    coefficients = {coef_names[0]: fit.value,
                    coef_names[1]: fit.inputs[coef_names[1]]}

    assumptions: dict[str, Any] = {
        "form": spec["form"],
        "model": spec["model"],
        "method": method,
        "equations": spec["equations"],
        "driving_force": spec["driving_force"],
        "coefficient_units": {coef_names[0]: fit.unit,
                              coef_names[1]: fit.assumptions.get(
                                  "b_unit", "dimensionless")},
        "fit": fit.assumptions.get("fit", ""),
        "validity": fit.assumptions.get("validity", ""),
        "grid": grid_note,
        "stabilization": GAS_IPR_STABILIZATION_NOTE,
        "aof_definition": (
            "AOF is Eq. 8-20 (or 8-28) at p_wf = 0, the last row of Ahmed's IPR "
            "table, '0 | 8980 = AOF = (Q_g)max' (#115, p. 554). It is a "
            "definition, not an achievable flowing condition"),
    }
    if spec["model"] == "Rawlins-Schellhardt":
        assumptions["n_band"] = (
            f"{lo}-{hi}: n = 1.0 completely laminar to n = 0.5 fully turbulent "
            "(#114, p. 543); the n exponent is Eq. 8-20's entire account of "
            "non-Darcy flow, and n = 1 would make the well Darcy")
    else:
        assumptions["b_meaning"] = (
            "b = (1422 T mu_g z / kh) D (Eq. 8-26), D the non-Darcy "
            "coefficient: b Q_g^2 is the inertial-turbulent term, and b = 0 "
            "would make the well Darcy and over-predict the rate")
        assumptions["model_assumptions"] = fit.assumptions.get(
            "model_assumptions", "")

    return Quantity(
        aof.value, "Mscf/d",
        f"AOF from a {len(pts)}-point deliverability test "
        f"({spec['model']}, {spec['form']} form, {spec['equations']})",
        f"{AHMED_CH8} + {AHMED_EX82}",
        inputs={
            **coefficients,
            "points": pts,
            "p_r_psia": p_r_psia,
            "curve": curve,
            "n_curve_points": len(curve),
        },
        assumptions=assumptions,
        flags=tuple(flags),
    )
