"""Tool #84 `aof_compute`, plus the shared evaluator `deliverability_rate`.

MERGE NOTE for the coordinator: this fragment replaces `aof_compute`,
`backpressure_rate` and `lit_rate` in `tools/deliverability.py`. It does not
duplicate them — `backpressure_rate` and `lit_rate` survive as thin adapters onto
`deliverability_rate`, so that after the merge there is exactly one place in the
codebase where a deliverability fit is turned into a rate. `gas_ipr_curve` (#86)
imports `deliverability_rate`; it must not grow its own copy of Eq. 8-20.

Why AOF takes a fit object and not (C, n, p_r): AOF is a property of the fit, not
of the well. Ahmed's Example 8-2 yields four different AOFs from one set of test
points, spanning 8536 to 10827 Mscf/d. So the model and the form are not
decoration on the answer, they are part of it, and there is no code path here
that returns an unlabelled AOF.

Sources: Ahmed, Reservoir Engineering Handbook, Chapter 8 —
  #114 pp. 543-550  the four equations (8-20, 8-28, 8-33, 8-38) and their limits
  #115 pp. 552-557  Example 8-2, three methods evaluated at p_wf = 0
  #116 pp. 558-559  the fourth method and the four-method comparison table
and PetroWiki, Inflow and outflow performance #2, Eq. 1.2 — the pseudopressure
form of the back-pressure equation, which Ahmed does not give. Equations checked
present on that page before use; it is a petrowiki-* document, and
tool-verification.md records that several of those lost their math to image
conversion. This one did not.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from ..result import Quantity, Range, Refusal

AHMED_EQUATIONS = "00-reference/ahmed-reservoir-engineering-handbook#114"
AHMED_AOF = "00-reference/ahmed-reservoir-engineering-handbook#115"
AHMED_COMPARISON = "00-reference/ahmed-reservoir-engineering-handbook#116"
AHMED_AOF_BOTH = f"{AHMED_AOF} + {AHMED_COMPARISON}"
PETROWIKI_IOP = "09-gas-deliverability/petrowiki-peh-inflow-outflow-performance#2"

BACKPRESSURE = "Rawlins-Schellhardt"
LIT = "Houpeurt-LIT"

# --- the (model, form) pairs the corpus actually publishes -------------------
# Keyed (model, form) -> equation number, the source's own name for the method,
# and which potential drop its coefficients act on. A pair absent from this
# table is a pair no document states, and is refused rather than extrapolated.
# Ahmed writes Eq. 8-20 only in the pressure-squared form; PetroWiki #2 Eq. 1.2
# adds the pseudopressure version of the same empirical law (its equations
# survived conversion — verified present, unlike the other petrowiki-* pages).
# Nothing anywhere prints Q = C(p_r - p_wf)^n.
METHODS: dict[tuple[str, str], dict[str, str]] = {
    (BACKPRESSURE, "pressure-squared"): {
        "equation": "Eq. 8-20", "label": "back-pressure", "potential": "p2",
        "source": AHMED_EQUATIONS},
    (BACKPRESSURE, "pseudopressure"): {
        "equation": "PetroWiki Eq. 1.2", "label": "back-pressure-psi",
        "potential": "psi", "source": PETROWIKI_IOP},
    (LIT, "pressure-squared"): {
        "equation": "Eq. 8-28", "label": "p2-approach", "potential": "p2",
        "source": AHMED_EQUATIONS},
    (LIT, "pressure-approximation"): {
        "equation": "Eq. 8-33", "label": "p-approach", "potential": "p",
        "source": AHMED_EQUATIONS},
    (LIT, "pseudopressure"): {
        "equation": "Eq. 8-38", "label": "psi-approach", "potential": "psi",
        "source": AHMED_EQUATIONS},
}

MODELS = (BACKPRESSURE, LIT)
FORMS = ("pressure-squared", "pressure-approximation", "pseudopressure")

# --- validity limits, quoted from the source --------------------------------
# Ahmed #114 p. 546 (p-squared) and p. 548 (pressure), restated at #116 p. 559.
FORM_PRESSURE_LIMITS: dict[str, dict[str, Any]] = {
    "pressure-squared": {
        "bound": "max", "p_psia": 2000.0,
        "quote": "recommended for applications at pressures below 2000 psi",
        "source": AHMED_EQUATIONS},
    "pressure-approximation": {
        "bound": "min", "p_psia": 3000.0,
        "quote": "limited to applications for pressures greater than 3000 psi",
        "source": AHMED_COMPARISON},
    "pseudopressure": {
        "bound": None, "p_psia": None,
        "quote": "applicable to all ranges of pressure",
        "source": AHMED_EQUATIONS},
}

# Ahmed #114 p. 543: n runs 1.0 for completely laminar to 0.5 for fully
# turbulent. PetroWiki #2 states the same 0.5-1.0 band independently.
BACKPRESSURE_N_BAND = (0.5, 1.0)

# psi conventions under which psi(0) = 0 is a definition, not a guess. Ahmed #75
# integrates m(p) = INT 2p/(mu_g z) dp from p = 0, and #116's psi table prints
# the row (p = 0, psi = 0). A reference-normalised psi (the TAMU form the
# catalog's #81 reconcile warns against mixing) does NOT satisfy this.
ZERO_BASED_PSI_CONVENTIONS = (
    "ahmed-integral-from-zero", "ahmed", "integral-from-zero")

# --- Ahmed Example 8-2, the published AOFs ----------------------------------
# p_r = 1952 psia, psi_r = 316e6 psi^2/cp. Values from the comparison table at
# #116 p. 559. NOTE: #116's psi-method IPR table one page earlier prints 8342,
# which contradicts both this table and Ahmed's own Eq. 8-38 (which returns
# 8535.67 for a2 = 22.28e3, b2 = 1.727, dpsi = 316e6). The comparison table is
# the correct one; every row of it reproduces from the quadratic. 8342 is a
# corpus defect and is not used.
AHMED_EXAMPLE_8_2_AOF: dict[str, float] = {
    "back-pressure": 8980.0,   # C = 0.0169, n = 0.87            (#115)
    "p2-approach": 8763.0,     # a = 318, b = 0.01333            (#115)
    "p-approach": 10827.0,     # a1 = 0.06, b1 = 1.111e-5        (#115)
    "psi-approach": 8536.0,    # a2 = 22.28e3, b2 = 1.727        (#116)
}
# (10827 - 8763)/8763 = 23.5% across the three methods at #115 — the figure the
# catalog quotes. Adding the psi-approach at #116 widens it to
# (10827 - 8536)/8536 = 26.8%.
AOF_SPREAD_FLAG = (
    "AOF is method-dependent: on one test (Ahmed Example 8-2) the published "
    "methods give 8763-10827 Mscf/d, a 23.5% spread, widening to 26.8% against "
    "the pseudopressure AOF of 8536. Ahmed #116 calls the pseudopressure "
    "approach the more accurate and rigorous reference, and measures the others "
    "against it at 5.4% (p-squared), 6.0% (back-pressure) and 11% "
    "(pressure-approximation) average error. Report the method with the number.")


# --- reading a fit ----------------------------------------------------------

def _section(fit: Any, name: str) -> Mapping[str, Any]:
    """`fit` may be a Quantity or any mapping shaped like one."""
    if isinstance(fit, Mapping):
        section = fit.get(name, {})
    else:
        section = getattr(fit, name, {})
    return section if isinstance(section, Mapping) else {}


def _fit_value(fit: Any) -> Any:
    return fit.get("value") if isinstance(fit, Mapping) else getattr(fit, "value", None)


def _p_r(inputs: Mapping[str, Any]) -> Any:
    """`p_r_psia` is canonical; `p_r` is the pre-contract alias still in tools/."""
    return inputs.get("p_r_psia", inputs.get("p_r"))


def _psi_r(inputs: Mapping[str, Any]) -> Any:
    """`psi_r` is the group-I contract key, and the only one read.

    `backpressure_fit` (#82) was emitting `psi_r_psi2_cp` and this read both.
    Reconciled at integration in favour of one key: a reader that accepts two
    spellings hides the next drift instead of failing on it, and the fits and
    the evaluator have to agree on the contract for the dispatch to mean
    anything."""
    return inputs.get("psi_r")


def _method_of(fit: Any):
    """Resolve (model, form) to a METHODS row, or a Refusal."""
    assumptions = _section(fit, "assumptions")
    model, form = assumptions.get("model"), assumptions.get("form")
    if model not in MODELS:
        return Refusal(
            f"deliverability fit declares model {model!r}; this evaluator "
            f"implements only {' and '.join(MODELS)} (Ahmed Ch. 8)",
            needed=('assumptions["model"] in ' + repr(MODELS),), source=AHMED_EQUATIONS)
    if form not in FORMS:
        return Refusal(
            f"deliverability fit declares form {form!r}; coefficients are "
            f"form-specific and differ by orders of magnitude between forms, so "
            f"the form cannot be inferred",
            needed=('assumptions["form"] in ' + repr(FORMS),), source=AHMED_EQUATIONS)
    method = METHODS.get((model, form))
    if method is None:
        return Refusal(
            f"no document in this corpus states the {model} equation in the "
            f"{form} form. Ahmed gives it as Eq. 8-20 on (p_r^2 - p_wf^2) and "
            f"PetroWiki as Eq. 1.2 on (psi_r - psi_wf); there is no "
            f"Q = C(p_r - p_wf)^n anywhere, and Ahmed's Eq. 8-29 in that "
            f"pressure form is the LIT quadratic, a different model. "
            f"Substituting it would fabricate a method",
            needed=("a source stating this model in this form",),
            source=f"{AHMED_EQUATIONS} + {PETROWIKI_IOP}")
    return method


# --- the one evaluator ------------------------------------------------------

def deliverability_rate(fit: Any, p_wf_psia: float | None = None,
                        psi_wf: float | None = None):
    """Gas rate from a deliverability fit. The only fit-to-rate path in the tree.

    Dispatches on `fit.assumptions["model"]` and `["form"]`: the back-pressure
    power law (Eq. 8-20) solved directly, the LIT quadratic solved by its
    positive root (Eqs. 8-28 / 8-33 / 8-38), in whichever potential the fit
    declares.

    Supply `p_wf_psia` for the pressure and pressure-squared forms, `psi_wf` for
    the pseudopressure form. Supplying the wrong one refuses: a pseudopressure
    fit's coefficients act on psi, and converting p to psi needs the well's own
    m(p) integral, which this function does not have and will not guess.
    """
    if p_wf_psia is None and psi_wf is None:
        raise ValueError("give either p_wf_psia or psi_wf")

    method = _method_of(fit)
    if isinstance(method, Refusal):
        return method

    inputs = _section(fit, "inputs")
    assumptions = _section(fit, "assumptions")
    model = assumptions["model"]
    form = assumptions["form"]
    potential = method["potential"]

    # --- the potential drop the coefficients act on -------------------------
    if potential == "psi":
        if psi_wf is None:
            return Refusal(
                "a pseudopressure-form fit was handed a pressure and no "
                "pseudopressure. Its coefficients act on (psi_r - psi_wf); "
                "psi(p) is the well's own m(p) integral and cannot be inferred "
                "from p_wf",
                needed=("psi_wf, psi^2/cp, from the well's m(p) transform (tool "
                        "#81 pseudopressure)",),
                source=AHMED_EQUATIONS)
        psi_r = _psi_r(inputs)
        if psi_r is None:
            return Refusal(
                "pseudopressure fit carries no reservoir pseudopressure",
                needed=('inputs["psi_r"], psi^2/cp',), source=AHMED_EQUATIONS)
        delta = psi_r - psi_wf
        delta_desc, delta_unit = "psi_r - psi_wf", "psi^2/cp"
        drop_inputs = {"psi_r": psi_r, "psi_wf": psi_wf}
        p_r = _p_r(inputs)
    else:
        if p_wf_psia is None:
            return Refusal(
                f"a {form} fit was handed a pseudopressure and no pressure; the "
                f"two conventions differ by orders of magnitude and must not be "
                f"mixed",
                needed=("p_wf_psia, psia",), source=AHMED_EQUATIONS)
        p_r = _p_r(inputs)
        if p_r is None:
            return Refusal(
                "deliverability fit carries no reservoir pressure",
                needed=('inputs["p_r_psia"], psia',), source=AHMED_EQUATIONS)
        if potential == "p2":
            delta = p_r ** 2 - p_wf_psia ** 2
            delta_desc, delta_unit = "p_r^2 - p_wf^2", "psi^2"
        else:
            delta = p_r - p_wf_psia
            delta_desc, delta_unit = "p_r - p_wf", "psi"
        drop_inputs = {"p_r_psia": p_r, "p_wf_psia": p_wf_psia}

    if delta < 0:
        return Refusal(
            f"({delta_desc}) = {delta:.6g} {delta_unit} is negative: the flowing "
            f"pressure exceeds the reservoir pressure, so the well takes fluid "
            f"rather than delivering it",
            needed=("a flowing pressure below the reservoir pressure",),
            source=AHMED_EQUATIONS)

    # --- solve ---------------------------------------------------------------
    if model == BACKPRESSURE:
        c = _fit_value(fit)
        n = inputs.get("n")
        if c is None or n is None:
            return Refusal(
                "back-pressure fit is missing C or n",
                needed=("fit.value = C", 'inputs["n"]'), source=AHMED_EQUATIONS)
        if c <= 0 or n <= 0:
            return Refusal(
                f"back-pressure coefficients C = {c:.6g}, n = {n:.6g} are not "
                f"physical; Eq. 8-20 needs C > 0 and n in 0.5-1.0, and a "
                f"non-positive value means the fit failed, not that the well "
                f"cannot flow",
                needed=("a fit with C > 0 and n > 0",), source=AHMED_EQUATIONS)
        q = c * delta ** n
        coefficients = {"C": c, "n": n}
    else:
        a = _fit_value(fit)
        b = inputs.get("b")
        if a is None or b is None:
            return Refusal(
                "LIT fit is missing a or b",
                needed=("fit.value = a", 'inputs["b"]'), source=AHMED_EQUATIONS)
        if a <= 0:
            return Refusal(
                f"LIT laminar coefficient a = {a:.6g} is not positive; the "
                f"quadratic then has no physical positive root and the fit "
                f"itself is bad",
                needed=("a fit with a > 0",), source=AHMED_EQUATIONS)
        if b < 0:
            return Refusal(
                f"LIT inertial-turbulent coefficient b = {b:.6g} is negative; "
                f"turbulence cannot reduce the pressure drop, so the fit is bad",
                needed=("a fit with b >= 0",), source=AHMED_EQUATIONS)
        if b == 0:
            q = delta / a          # purely laminar; the quadratic degenerates
        else:
            discriminant = a ** 2 + 4 * b * delta
            if discriminant < 0:
                return Refusal(
                    f"the LIT quadratic has no real root: a^2 + 4b*({delta_desc})"
                    f" = {discriminant:.6g} < 0",
                    needed=("coefficients giving a real positive root",),
                    source=AHMED_EQUATIONS)
            q = (-a + math.sqrt(discriminant)) / (2 * b)
        coefficients = {"a": a, "b": b}

    if q < 0:                      # belt and braces; unreachable given the guards
        return Refusal(
            f"the fit returns a negative rate ({q:.6g} Mscf/d) at this pressure",
            needed=("a physically consistent fit",), source=AHMED_EQUATIONS)

    return Quantity(
        q, "Mscf/d",
        f"{method['label']} deliverability ({model}, {form} form, Ahmed "
        f"{method['equation']})",
        method["source"],
        inputs={**coefficients, **drop_inputs, "delta": delta},
        assumptions={"model": model, "form": form,
                     "equation": method["equation"],
                     "method_label": method["label"],
                     "potential": delta_desc},
        flags=_validity_flags(model, form, p_r, inputs))


def _validity_flags(model: str, form: str, p_r: float | None,
                    inputs: Mapping[str, Any]) -> tuple[str, ...]:
    """Ahmed's stated pressure limits per form, and the n band. Flags, not
    refusals: he applies the pressure-approximation method at 1952 psia in his
    own Example 8-2, in violation of its own 3000 psi limit, and that method is
    the 11%-error outlier. The caller has to see that, not be blocked by it."""
    flags: list[str] = []
    limit = FORM_PRESSURE_LIMITS[form]
    if p_r is not None and limit["bound"] == "max" and p_r > limit["p_psia"]:
        flags.append(
            f"p_r = {p_r:.6g} psia is above {limit['p_psia']:.0f} psi and the "
            f"{form} form is {limit['quote']} (Ahmed {limit['source']}); prefer "
            f"the pseudopressure form")
    if p_r is not None and limit["bound"] == "min" and p_r < limit["p_psia"]:
        flags.append(
            f"p_r = {p_r:.6g} psia is below {limit['p_psia']:.0f} psi and the "
            f"{form} form is {limit['quote']} (Ahmed {limit['source']}); this is "
            f"the method that carries 11% average error in Ahmed's own example, "
            f"which is run at 1952 psia")
    if model == BACKPRESSURE:
        n = inputs.get("n")
        lo, hi = BACKPRESSURE_N_BAND
        if n is not None and not lo <= n <= hi:
            flags.append(
                f"n = {n:.4g} is outside {lo}-{hi}; that band spans completely "
                f"laminar to fully turbulent flow (Ahmed {AHMED_EQUATIONS}), so "
                f"a value outside it means bad test data rather than a valid fit")
    return tuple(flags)


# --- AOF --------------------------------------------------------------------

def _psi_at_zero(fit: Any, psi_wf0: float | None):
    """psi(p = 0) for a pseudopressure AOF: given, defined, or refused."""
    if psi_wf0 is not None:
        return psi_wf0, ()
    convention = _section(fit, "assumptions").get("psi_convention")
    if convention in ZERO_BASED_PSI_CONVENTIONS:
        return 0.0, (
            f"psi(0) taken as 0 because the fit declares psi_convention="
            f"{convention!r}: Ahmed integrates m(p) from p = 0, so psi(0) = 0 by "
            f"definition, and #116's psi table prints that row. This does not "
            f"hold for a reference-normalised pseudopressure",)
    return Refusal(
        "AOF of a pseudopressure fit needs psi evaluated at p = 0. It is 0 only "
        "under Ahmed's convention of integrating m(p) from p = 0; under a "
        "reference-normalised pseudopressure it is not, and assuming the wrong "
        "one silently mis-scales the AOF",
        needed=("psi_wf0, psi^2/cp, at p = 0",
                'or assumptions["psi_convention"] on the fit'),
        source=AHMED_COMPARISON), ()


def aof_compute(fit: Any, psi_wf0: float | None = None):
    """Absolute open flow potential: the fit evaluated at p_wf = 0.

    Ahmed #115 labels the last row of each IPR table
    `0 | 8980 = AOF = (Q_g)_max`. Nothing more is computed here — the whole
    content of this tool is that the answer is only meaningful with the method
    attached, because the four methods disagree by 26.8% on one test
    (8536 to 10827 Mscf/d). 23.5% is the spread across three of them; the
    pseudopressure method is lower than all three.
    """
    method = _method_of(fit)
    if isinstance(method, Refusal):
        return method

    psi_flags: tuple[str, ...] = ()
    if method["potential"] == "psi":
        psi_zero, psi_flags = _psi_at_zero(fit, psi_wf0)
        if isinstance(psi_zero, Refusal):
            return psi_zero
        rate = deliverability_rate(fit, psi_wf=psi_zero)
    else:
        rate = deliverability_rate(fit, p_wf_psia=0.0)
    if isinstance(rate, Refusal):
        return rate

    return Quantity(
        rate.value, "Mscf/d",
        f"AOF = (Q_g)max at p_wf = 0, {method['label']} method (Ahmed "
        f"{method['equation']})",
        AHMED_AOF_BOTH,
        inputs=dict(rate.inputs),
        assumptions={**rate.assumptions,
                     "evaluated_at": "p_wf = 0 psia",
                     "zero_vs_atmospheric": (
                         "Ahmed's IPR tables evaluate AOF at p_wf = 0 exactly; "
                         "PetroWiki #2 describes AOF as flow against theoretical "
                         "atmospheric backpressure. Using 14.7 psia instead "
                         "moves Example 8-2 by 0.005% in the pressure-squared "
                         "forms and 0.45% in the pressure-approximation form "
                         "(10827.07 -> 10778.08). Call "
                         "deliverability_rate(fit, p_wf_psia=14.7) for that "
                         "convention"),
                     "published_example_8_2_aof": dict(AHMED_EXAMPLE_8_2_AOF)},
        flags=(AOF_SPREAD_FLAG,) + psi_flags + rate.flags)


def aof_compare(fits: list[Any], psi_wf0: float | None = None):
    """AOF by two or more methods on the same test, as a Range.

    Ahmed #116 part (c) is exactly this: one table, four methods, the same test
    points, with each method's error measured against the pseudopressure
    approach. So the source supports reporting the spread — and supports naming
    the psi-approach as the reference — but it never blends the methods into a
    single best estimate, and neither does this.
    """
    if len(fits) < 2:
        return Refusal(
            "a multi-method AOF comparison needs at least two fits; with one "
            "method there is no spread to report, and aof_compute is the tool",
            needed=("two or more deliverability fits of the same test",),
            source=AHMED_COMPARISON)

    members: dict[str, float] = {}
    for fit in fits:
        method = _method_of(fit)
        if isinstance(method, Refusal):
            return method
        label = method["label"]
        if label in members:
            return Refusal(
                f"two fits both declare the {label} method; a comparison needs "
                f"distinct method/form pairs or the spread is meaningless",
                needed=("one fit per method",), source=AHMED_COMPARISON)
        aof = aof_compute(fit, psi_wf0=psi_wf0)
        if isinstance(aof, Refusal):
            return Refusal(
                f"the {label} member of the comparison refused: {aof.reason}. "
                f"Dropping it would understate the spread, so the whole "
                f"comparison refuses",
                needed=aof.needed, source=aof.source or AHMED_COMPARISON)
        members[label] = aof.value

    low, high = min(members.values()), max(members.values())
    reference = ("psi-approach" if "psi-approach" in members else None)
    spread_pct = (high - low) / low * 100.0 if low > 0 else float("nan")
    return Range(
        low, high, "Mscf/d",
        f"AOF across {len(members)} deliverability methods on one test "
        f"(Ahmed Example 8-2 comparison, {AHMED_COMPARISON}); spread "
        f"{spread_pct:.1f}% of the low value; "
        + (f"reference method is the pseudopressure approach, which Ahmed calls "
           f"more accurate and rigorous than the other three"
           if reference else
           "no pseudopressure fit supplied, so the reference method Ahmed "
           "measures the others against is absent from this comparison")
        + ". Ahmed sets no threshold at which such a spread invalidates a test.",
        AHMED_AOF_BOTH,
        members=members)


# --- adapters kept so nothing else in the tree grows a second evaluator -----

def backpressure_rate(c: float, n: float, p_r: float, p_wf: float):
    """Q_g = C (p_r^2 - p_wf^2)^n. Eq. 8-20, via the shared evaluator.

    Behaviour change from the pre-#84 version: p_wf > p_r now returns a Refusal
    instead of raising. It is a statement about the caller's data, not a
    programmer error, and the operator should see it.
    """
    return deliverability_rate(
        {"value": c,
         "inputs": {"n": n, "p_r_psia": p_r},
         "assumptions": {"model": BACKPRESSURE, "form": "pressure-squared"}},
        p_wf_psia=p_wf)


def lit_rate(a: float, b: float, p_r: float, p_wf: float,
             form: str = "pressure-squared"):
    """LIT quadratic solved for its positive root, via the shared evaluator.

    Eq. 8-28 in the pressure-squared form, Eq. 8-33 in the pressure form. For
    the pseudopressure form call `deliverability_rate` directly with `psi_wf` —
    this signature takes pressures, and handing it a psi-form fit would mix the
    two conventions.
    """
    return deliverability_rate(
        {"value": a,
         "inputs": {"b": b, "p_r_psia": p_r},
         "assumptions": {"model": LIT, "form": form}},
        p_wf_psia=p_wf)
