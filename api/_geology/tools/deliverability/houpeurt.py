"""Tool #83 `houpeurt_fit` — LIT (laminar-inertial-turbulent) coefficients a and b.

Merge target: `tools/deliverability.py`. This REPLACES the existing `lit_fit`
(deliverability.py:81), which implemented only the pressure-squared form, could
not refuse, and hardcoded its form label. `lit_fit` is retained below as a
deprecated alias so `tests/test_gas_and_flow.py::test_lit_round_trip` keeps
working — see specs/83-houpeurt_fit.md, "Relationship to the existing code".

Why `form` is required and has no default: Ahmed gives three quadratic forms
(Eqs. 8-24, 8-29, 8-34) and on Example 8-2's single data set their laminar
coefficients are 318, 0.06 and 22.28e3 — six orders of magnitude apart, in three
different units. `tool-verification.md:108-111` records the undifferentiated
"a and b" as a defect. An (a, b) pair without its form is not interpretable, so
the form is an argument, the unit string encodes it, and it travels on the result.

The corpus's other deliverability document,
`09-gas-deliverability/petrowiki-deliverability-testing-gas-wells`, lost every
equation to image conversion (`tool-verification.md:37`) and is deliberately not
cited here.
"""
from __future__ import annotations

import math

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused here)

AHMED_LIT = "00-reference/ahmed-reservoir-engineering-handbook#114"
AHMED_LIT_EXAMPLE = "00-reference/ahmed-reservoir-engineering-handbook#115"

PRESSURE_SQUARED = "pressure-squared"
PRESSURE_APPROXIMATION = "pressure-approximation"
PSEUDOPRESSURE = "pseudopressure"

# Per-form definition, from Ahmed Ch. 8 (`ahmed#114`, pp. 545-550).
#   drop            the left-hand side of the quadratic
#   a_eq / b_eq     the equation numbers defining the coefficients
#   unit / b_unit   coefficient units; these differ per form and are load-bearing
FORMS: dict[str, dict[str, str]] = {
    PRESSURE_SQUARED: {
        "drop": "p_r^2 - p_wf^2",
        "quadratic_eq": "8-24",
        "linear_eq": "8-27",
        "a_eq": "8-25",
        "b_eq": "8-26",
        "rate_eq": "8-28",
        "unit": "psi^2/(Mscf/d)",
        "b_unit": "psi^2/(Mscf/d)^2",
    },
    PRESSURE_APPROXIMATION: {
        "drop": "p_r - p_wf",
        "quadratic_eq": "8-29",
        "linear_eq": "8-32",
        "a_eq": "8-30",
        "b_eq": "8-31",
        "rate_eq": "8-33",
        "unit": "psi/(Mscf/d)",
        "b_unit": "psi/(Mscf/d)^2",
    },
    PSEUDOPRESSURE: {
        "drop": "psi_r - psi_wf",
        "quadratic_eq": "8-34",
        "linear_eq": "8-37",
        "a_eq": "8-35",
        "b_eq": "8-36",
        "rate_eq": "8-38",
        "unit": "(psi^2/cp)/(Mscf/d)",
        "b_unit": "(psi^2/cp)/(Mscf/d)^2",
    },
}

# Stated pressure validity, quoted from the source. Tested against p_r (the
# average reservoir pressure) — see spec open question 1; Ahmed does not say
# which pressure he means, and p_r is the conservative choice.
#   (min_psia, max_psia, quote)  with None for unbounded.
FORM_PRESSURE_LIMITS: dict[str, tuple[float | None, float | None, str]] = {
    PRESSURE_SQUARED: (
        None, 2000.0,
        "This method is recommended for applications at pressures below 2000 psi "
        "(ahmed#114, p. 546)",
    ),
    PRESSURE_APPROXIMATION: (
        3000.0, None,
        "the pressure method is applicable at pressures higher than 3000 psi "
        "(ahmed#114, p. 548; restated ahmed#116, p. 559)",
    ),
    PSEUDOPRESSURE: (
        None, None,
        "the pseudopressure approach is more rigorous than either the "
        "pressure-squared or pressure-approximation method and is applicable to "
        "all ranges of pressure (ahmed#114, p. 549)",
    ),
}

# Ahmed's own assumption list for the LIT derivation (`ahmed#114`, p. 546).
# None of these is checkable from test data, which is why they ride on the result.
LIT_MODEL_ASSUMPTIONS = (
    "single phase flow in the reservoir",
    "homogeneous and isotropic reservoir system",
    "permeability is independent of pressure",
    "the product (mu_g * z) is constant",
)


def _least_squares(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Intercept a and slope b of y = a + b x. Ahmed draws this line by hand."""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0.0:
        raise ZeroDivisionError  # caller turns this into a refusal
    b = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / sxx
    return mean_y - b * mean_x, b


def houpeurt_fit(points, p_r_psia: float, form: str, psi_r: float | None = None):
    """Houpeurt LIT coefficients a and b from a multi-rate deliverability test.

    points: [(p_wf_psia, qg_mscf_d)] or [(p_wf_psia, qg_mscf_d, psi_wf)].
        Note the order — rate second, pseudopressure third. This is NOT the
        column order of Ahmed's table (#115 prints p_wf, psi_wf, Q_g); it keeps
        the signature of the `lit_fit` it replaces so existing callers cannot
        silently transpose two arguments.
    p_r_psia: average (stabilised shut-in) reservoir pressure, psia.
    form: one of the three module constants. Required; there is no safe default.
    psi_r: reservoir pseudopressure, psi^2/cp — required for, and only used by,
        the pseudopressure form. Must be on Ahmed's convention (m(p) integrated
        from p = 0, per the reconcile at tool-catalog.md:594-600); mixing it with
        a reference-normalised psi_wf gives a wrong drop and no error.

    Fitted by ordinary least squares of drop/Qg on Qg — Ahmed's Eq. 8-27/8-32/8-37
    plot, but regressed rather than drawn, which does not reproduce his published
    pair exactly. Returns a as .value and b as .inputs["b"].
    """
    if form not in FORMS:
        # Programmer error, not a corpus limit: raise rather than refuse.
        raise ValueError(
            f"unknown form {form!r}; expected one of {sorted(FORMS)}"
        )
    spec = FORMS[form]

    if p_r_psia <= 0:
        raise ValueError("p_r_psia must be positive")

    if form == PSEUDOPRESSURE and psi_r is None:
        return Refusal(
            reason="the pseudopressure form needs the reservoir pseudopressure "
                   "psi_r; Eq. 8-34 is written on (psi_r - psi_wf) and there is "
                   "no way to get it from pressures alone",
            needed=("psi_r (psi^2/cp, Ahmed convention — see tool #81 "
                    "`pseudopressure`)",),
            source=AHMED_LIT,
        )

    flags: list[str] = []
    xs: list[float] = []
    ys: list[float] = []
    used: list[tuple] = []

    for i, point in enumerate(points):
        if len(point) == 3:
            p_wf, qg, psi_wf = point
        elif len(point) == 2:
            p_wf, qg = point
            psi_wf = None
        else:
            raise ValueError(
                "each point must be (p_wf_psia, qg_mscf_d) or "
                "(p_wf_psia, qg_mscf_d, psi_wf)"
            )

        # Ahmed's own tables carry the shut-in row (p_r, 0) with "—" in the ratio
        # column (#115 step 1, #116 step 1). Drop it instead of refusing, so a
        # caller who transcribes the published table verbatim still gets a fit.
        if qg == 0 and p_wf >= p_r_psia:
            flags.append(
                f"point {i} is the shut-in row (Qg = 0 at p_wf = p_r) and was "
                "dropped; Ahmed tabulates it as '—' (ahmed#115)"
            )
            continue

        if qg <= 0:
            return Refusal(
                reason=f"point {i} has a non-positive rate ({qg} Mscf/d); "
                       f"Eq. {spec['linear_eq']} divides the drop by Qg",
                needed=("a positive stabilised gas rate at every test point",),
                source=AHMED_LIT,
            )

        if p_wf >= p_r_psia:
            return Refusal(
                reason=f"point {i} has p_wf = {p_wf} psia at or above p_r = "
                       f"{p_r_psia} psia; the deliverability test shuts in to "
                       "p_r and then produces, so every flowing pressure must be "
                       "below it (ahmed#114, p. 551, steps 1-2)",
                needed=("p_wf strictly below the average reservoir pressure",),
                source=AHMED_LIT,
            )

        if form == PRESSURE_SQUARED:
            drop = p_r_psia ** 2 - p_wf ** 2
        elif form == PRESSURE_APPROXIMATION:
            drop = p_r_psia - p_wf
        else:
            if psi_wf is None:
                return Refusal(
                    reason=f"point {i} carries no psi_wf, which Eq. 8-34 needs; "
                           "the pressure-squared drop is not a substitute (the "
                           "coefficients differ by ~1e5)",
                    needed=("psi_wf, psi^2/cp, as the third element of every point",),
                    source=AHMED_LIT,
                )
            drop = psi_r - psi_wf

        xs.append(qg)
        ys.append(drop / qg)
        used.append(tuple(point))

    if len(xs) < 2:
        return Refusal(
            reason=f"a straight line in (a, b) has two parameters and only "
                   f"{len(xs)} usable test point(s) were supplied; Ahmed's method "
                   "is a three- or four-point flow test (ahmed#114, p. 551)",
            needed=("at least two flowing points; three or four for a real test",),
            source=AHMED_LIT,
        )

    if len(xs) == 2:
        flags.append(
            "two points fit the line with zero residual, so nothing here tests "
            "whether the data actually lies on a straight line; Ahmed's procedure "
            "is a three- or four-point test (ahmed#114, p. 551)"
        )

    try:
        a, b = _least_squares(xs, ys)
    except ZeroDivisionError:
        return Refusal(
            reason="every test point is at the same rate, so the slope b of "
                   f"Eq. {spec['linear_eq']} is undetermined",
            needed=("test points at two or more distinct stabilised rates",),
            source=AHMED_LIT,
        )

    # b = (group) * D, with D the non-Darcy coefficient (Eqs. 8-26/8-31/8-36).
    # Turbulence can only add drawdown, so a negative b is not a physical fit —
    # it is unstabilised or mis-transcribed data. It would also break the
    # positive root of Eq. 8-28 once a^2 + 4b*drop goes negative. This rule is
    # ours, derived from the source's definition; Ahmed never states it.
    if b < 0:
        return Refusal(
            reason=f"the fit gives b = {b:.6g} {spec['b_unit']}; b is "
                   f"(group)*D with D the non-Darcy coefficient "
                   f"(Eq. {spec['b_eq']}), so a negative b is unphysical — "
                   "turbulence cannot reduce drawdown. The drop/Qg ratios fall "
                   "with rate, which means unstabilised rates, a mis-transcribed "
                   "point, or a drifting reverse-sequence test",
            needed=("test points whose (drop/Qg) rises with rate — i.e. a "
                    "stabilised test",),
            source=AHMED_LIT,
        )

    if b == 0:
        flags.append(
            "b = 0: the fit found no inertial-turbulent term (D = 0). Possible "
            "at low rate, but on a two-point test it usually means the data, not "
            "the reservoir"
        )

    lo, hi, quote = FORM_PRESSURE_LIMITS[form]
    in_range = True
    if lo is not None and p_r_psia <= lo:
        in_range = False
    if hi is not None and p_r_psia >= hi:
        in_range = False
    if not in_range:
        # A flag, not a refusal: Ahmed's own Example 8-2 runs all three forms at
        # p_r = 1952 psia — including the pressure-approximation form, which is
        # outside its stated range — and reports the 11% error rather than
        # declining (ahmed#116, p. 559). Refusing would contradict the source.
        flags.append(
            f"p_r = {p_r_psia:g} psia is outside the stated range of the "
            f"{form} form: \"{quote}\". Ahmed applies it anyway in Example 8-2 "
            "and measures the error, so this is a caveat, not a bar; the "
            "pseudopressure form is valid at all pressures"
        )
        if 2000.0 <= p_r_psia <= 3000.0 and form != PSEUDOPRESSURE:
            flags.append(
                "2000-3000 psia is a gap: the source states the pressure-squared "
                "form below 2000 psi and the pressure form above 3000 psi, and "
                "says nothing about the interval between. Use the pseudopressure "
                "form here"
            )

    inputs: dict = {
        "b": b,
        "p_r_psia": p_r_psia,
        "points": list(points),
        "fit_points": used,
        "n_points": len(xs),
    }
    if form == PSEUDOPRESSURE:
        inputs["psi_r"] = psi_r

    return Quantity(
        a,
        spec["unit"],
        f"Houpeurt LIT laminar coefficient a, {form} form "
        f"(Ahmed Eq. {spec['a_eq']}; fitted on Eq. {spec['linear_eq']})",
        AHMED_LIT,
        inputs=inputs,
        assumptions={
            "model": "Houpeurt-LIT",
            "form": form,
            "quadratic": f"{spec['drop']} = a*Qg + b*Qg^2 (Eq. {spec['quadratic_eq']})",
            "b_unit": spec["b_unit"],
            "rate_equation": f"invert with Eq. {spec['rate_eq']}",
            "fit": "ordinary least squares of (drop/Qg) on Qg; the source draws "
                   "the line by hand, so published coefficients differ (Example "
                   "8-2: a = 318 drawn vs 313.70 fitted)",
            "validity": quote,
            "model_assumptions": LIT_MODEL_ASSUMPTIONS,
            "worked_example": AHMED_LIT_EXAMPLE,
        },
        flags=tuple(flags),
    )


def lit_fit(points, p_r: float):
    """Deprecated alias for `houpeurt_fit(..., form="pressure-squared")`.

    Kept only because `tests/test_gas_and_flow.py::test_lit_round_trip` calls it
    and that round-trip is worth keeping. New callers must state a form: the
    three forms' coefficients differ by six orders of magnitude.
    """
    result = houpeurt_fit(points, p_r, PRESSURE_SQUARED)
    if isinstance(result, Refusal):
        return result
    return Quantity(
        result.value, result.unit, result.method, result.source,
        inputs=result.inputs, assumptions=result.assumptions,
        flags=result.flags + (
            "deprecated: call houpeurt_fit with an explicit form",
        ),
    )
