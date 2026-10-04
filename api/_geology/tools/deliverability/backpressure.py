"""Tool #82 — backpressure_fit. Rawlins-Schellhardt C and n. Spec: specs/82-backpressure_fit.md

Merges into `tools/deliverability.py`, replacing the existing `backpressure_fit`.

Two things the previous version left implicit and this one makes explicit, because
both change C by more than the measurement is worth:

*Form.* Eq. 8-20's C has units Mscf/d/psia^2n; the pseudopressure form's C has
units Mscf/d/(psia^2/cp)^n and, on PetroWiki's own example well, a value an order
of magnitude away (0.2874 vs 0.0269). `form` is therefore a first-class argument
and travels on the result. The pressure-approximation form of Rawlins-Schellhardt
is NOT in this corpus — Ahmed's Eq. 8-29 is the LIT quadratic, a different tool —
so asking for it gets a Refusal rather than an invented equation.

*Fitting method.* Ahmed reads n off two points on a hand-drawn line and C off a
third; the points he uses (600000, 1800) and (1500000, 4000) are not test points
at all. Least squares over the real points is reproducible but is a different
estimator and gives a different C (0.01700 vs the published 0.0169, AOF 9034 vs
8980). Both are offered, the difference is flagged, and neither is passed off as
the other.
"""
from __future__ import annotations

import math

from ..result import Quantity, Range, Refusal

AHMED_BP = "00-reference/ahmed-reservoir-engineering-handbook#114"
AHMED_AOF = "00-reference/ahmed-reservoir-engineering-handbook#115"
PETROWIKI_IOP = "09-gas-deliverability/petrowiki-peh-inflow-outflow-performance#2"

# --- Forms of the back-pressure equation ------------------------------------
# Each entry: the driving force Q is raised over, C's units, the anchor that
# prints that form, and its stated pressure applicability.
#
# Ahmed #114 labels C "Mscf/day/psi^2" and Example 8-2 Step 4 repeats it as
# "Mscf/psi^2"; both drop the exponent n and are dimensionally wrong. PetroWiki
# #3 labels the same coefficient "Mscf/D/psia^2n" and the pseudopressure one
# "Mscf/D/(psia^2/cp)^n". Reconcile: PetroWiki's units, Ahmed's equation.
FORMS = {
    "pressure-squared": {
        "driving_force": "p_r^2 - p_wf^2, psi^2",
        "c_unit": "Mscf/d/psia^2n",
        "equation": "Q_g = C (p_r^2 - p_wf^2)^n  (Ahmed Eq. 8-20)",
        "source": AHMED_BP,
        # Ahmed #114 (printed p. 546) states "below 2000 psi" for the
        # pressure-squared development; PetroWiki #2 states the same limitation
        # for Rawlins-Schellhardt itself but gives no number. Carried across as
        # a flag, never a refusal. See spec open question 3.
        "p_max_psia": 2000.0,
        "validity": ("pressure-squared is recommended below ~2000 psia "
                     "(Ahmed #114, printed p. 546; PetroWiki #2 says 'low pressures' "
                     "for Rawlins-Schellhardt without a number)"),
    },
    "pseudopressure": {
        "driving_force": "psi_r - psi_wf, psi^2/cp",
        "c_unit": "Mscf/d/(psia^2/cp)^n",
        "equation": "Q_g = C [psi(p_r) - psi(p_wf)]^n  (PetroWiki Eq. 1.2)",
        "source": PETROWIKI_IOP,
        "p_max_psia": None,  # applicable at all pressures
        "validity": "pseudopressure form is applicable across all pressure ranges",
    },
}

# Asked for but not in the corpus. Ahmed's pressure-approximation (Eq. 8-29) is
# the LIT quadratic p_r - p_wf = a1 Q + b1 Q^2, which belongs to houpeurt_fit;
# no document here prints Q = C (p_r - p_wf)^n.
UNSOURCED_FORMS = {
    "pressure": ("no document in the corpus prints a Rawlins-Schellhardt back-pressure "
                 "equation in the pressure-approximation form Q = C(p_r - p_wf)^n; "
                 "Ahmed's pressure-approximation Eq. 8-29 is the LIT quadratic "
                 "p_r - p_wf = a1*Qg + b1*Qg^2, which is houpeurt_fit's equation, "
                 "not a C-and-n fit"),
}

METHODS = ("least-squares", "two-point", "given-n")

# Ahmed #114: "the exponent n may vary from 1.0 for completely laminar flow to
# 0.5 for fully turbulent flow." PetroWiki #2: "typically falls within the range
# of 0.5 to 1.0." Stated as the physical meaning of n, not as a validity limit on
# the fit, and neither source prescribes an action outside it -> flag, not refuse.
N_LAMINAR = 1.0
N_FULLY_TURBULENT = 0.5

# Ahmed #114, back-pressure test Step 3: "If three or four rates are used, the
# test may be referred to as a three-point or four-point flow test."
MIN_POINTS_FOR_LINE = 2
RECOMMENDED_POINTS = 3


def backpressure_fit(
    points=None,
    p_r_psia: float = None,
    *,
    form: str = "pressure-squared",
    method: str = "least-squares",
    psi_r_psi2_cp: float = None,
    psi_wf_psi2_cp=None,
    line_points=None,
    c_point=None,
    n_given: float = None,
):
    """Rawlins-Schellhardt C and n from a multi-point deliverability test.

    Ahmed Eqs. 8-20 to 8-23 (`AHMED_BP`, catalog p. 566, printed pp. 543-544);
    pseudopressure form PetroWiki Eq. 1.2 (`PETROWIKI_IOP`).

    points          [(p_wf_psia, qg_mscfd), ...] stabilized test points.
    p_r_psia        average reservoir pressure, psia. Required for every form.
    form            "pressure-squared" (default) | "pseudopressure".
                    "pressure" is refused - see UNSOURCED_FORMS.
    method          "least-squares" (default) regresses log10(Qg) on log10(dp)
                        over all points, Eq. 8-21 fitted to the data;
                    "two-point"     n from Eq. 8-22 on `line_points`, C from
                        Eq. 8-23 on `c_point` - this is Ahmed's published
                        procedure, and his points are read off a drawn line,
                        not taken from the test;
                    "given-n"       n supplied, C from Eq. 8-23 alone.
    psi_r_psi2_cp,
    psi_wf_psi2_cp  pseudopressures, required with form="pseudopressure" when
                    `points` is used. psi_wf runs parallel to `points`.
    line_points     [(dp, Qg), (dp, Qg)] for method="two-point". dp is in the
                    FORM's driving-force units (psi^2 or psi^2/cp), NOT a pressure.
    c_point         (dp, Qg) that Eq. 8-23 is evaluated at. Same dp units.
                    Defaults to line_points[0] under "two-point".
    n_given         the exponent, for method="given-n".

    Returns Quantity with .value = C, .inputs["n"] = n, or Refusal.
    """
    spec = FORMS.get(form)
    if spec is None:
        why = UNSOURCED_FORMS.get(form)
        if why:
            return Refusal(
                reason=f"the {form!r} form of the Rawlins-Schellhardt equation is not "
                       f"sourced: {why}",
                needed=("a corpus source printing Q_g = C(p_r - p_wf)^n as a "
                        "Rawlins-Schellhardt back-pressure equation",),
                source=AHMED_BP,
            )
        raise ValueError(f"form must be one of {sorted(FORMS)}, got {form!r}")
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    if p_r_psia is None:
        raise ValueError("p_r_psia is required: it carries the form's pressure "
                         "validity check and the group-I result contract")

    flags: list[str] = []

    # Reduce the test points to (driving force, rate), refusing on any point the
    # method cannot take a logarithm of.
    pairs = []
    if points:
        pts = list(points)
        if form == "pseudopressure":
            if psi_r_psi2_cp is None or psi_wf_psi2_cp is None:
                return Refusal(
                    reason="the pseudopressure form needs psi(p_r) and psi(p_wf) for "
                           "every test point; pressures alone do not determine the "
                           "driving force psi_r - psi_wf",
                    needed=("psi_r_psi2_cp", "psi_wf_psi2_cp (parallel to points)"),
                    source=PETROWIKI_IOP,
                )
            psis = list(psi_wf_psi2_cp)
            if len(psis) != len(pts):
                raise ValueError("psi_wf_psi2_cp must run parallel to points")
        for i, (p_wf, qg) in enumerate(pts):
            # Ahmed's own Table 8-2 opens with the shut-in row (p_r, 0) and prints
            # "--" in its ratio column: he tabulates it as *not a data point*, not
            # as an error. `houpeurt_fit` (#83) drops it with a flag; this refused,
            # so pasting the published table into one sibling fitted and into the
            # other refused. Reconciled on #83's reading - the source's own
            # treatment - so the table can be used as printed.
            if qg == 0 and p_wf >= p_r_psia:
                flags.append(
                    f"test point {i + 1} is the shut-in row (Q_g = 0 at "
                    f"p_wf = {p_wf:g} >= p_r) and was dropped; Ahmed tabulates it "
                    "as '--' in Table 8-2 (#115), i.e. not a flow point")
                continue
            if form == "pseudopressure":
                dp = psi_r_psi2_cp - psis[i]
                if dp <= 0:
                    return Refusal(
                        reason=f"test point {i + 1} has psi_wf = {psis[i]:g} >= "
                               f"psi_r = {psi_r_psi2_cp:g} psi^2/cp: the driving force is "
                               "not positive, so the well is not flowing at that point "
                               "and log(0) is undefined",
                        needed=("a flowing point with psi_wf < psi_r",),
                        source=PETROWIKI_IOP,
                    )
            else:
                dp = p_r_psia ** 2 - p_wf ** 2
                if dp <= 0:
                    return Refusal(
                        reason=f"test point {i + 1} has p_wf = {p_wf:g} >= "
                               f"p_r = {p_r_psia:g} psia, so p_r^2 - p_wf^2 <= 0 and "
                               "Eq. 8-21 has no logarithm; the shut-in row of a "
                               "deliverability table is not a flow point - drop it "
                               "before fitting",
                        needed=("test points with p_wf strictly below p_r",),
                        source=AHMED_BP,
                    )
            if qg <= 0:
                return Refusal(
                    reason=f"test point {i + 1} has Q_g = {qg:g} Mscf/d; Eq. 8-21 needs "
                           "log(Q_g), and a non-positive rate is not a flow point",
                    needed=("a positive stabilized gas rate at every point",),
                    source=AHMED_BP,
                )
            pairs.append((dp, qg))

    # --- fit n and C ---------------------------------------------------------
    if method == "least-squares":
        if len(pairs) < MIN_POINTS_FOR_LINE:
            return Refusal(
                reason=f"a least-squares fit of Eq. 8-21 needs at least "
                       f"{MIN_POINTS_FOR_LINE} flow points; got {len(pairs)}",
                needed=("a multi-rate test: Ahmed's procedure uses three or four "
                        "stabilized rates",),
                source=AHMED_BP,
            )
        if len(pairs) < RECOMMENDED_POINTS:
            flags.append(
                f"{len(pairs)} points give an exact fit with no redundancy, so n cannot "
                "be checked against the data; Ahmed's back-pressure test uses three or "
                "four rates")
        xs = [math.log10(dp) for dp, _ in pairs]
        ys = [math.log10(qg) for _, qg in pairs]
        k = len(xs)
        mean_x, mean_y = sum(xs) / k, sum(ys) / k
        sxx = sum((x - mean_x) ** 2 for x in xs)
        if sxx == 0:
            return Refusal(
                reason="every test point has the same driving force, so the log-log "
                       "deliverability line is vertical and the slope n is undetermined",
                needed=("test points at genuinely different drawdowns",),
                source=AHMED_BP,
            )
        sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        n = sxy / sxx
        c = 10 ** (mean_y - n * mean_x)
        flags.append(
            "C came from least squares over the test points, not from the published "
            "procedure (a best-fit line drawn by eye, two points read off it, Eq. 8-22); "
            "the two give different C from the same test - on Ahmed's Example 8-2, "
            "0.01700 here against the published 0.0169")
        fit_note = ("ordinary least squares of log10(Qg) on log10(driving force) over "
                    "all test points (Eq. 8-21 orientation). The published procedure "
                    "instead draws a best-fit line by eye and reads two points off it "
                    "(Eq. 8-22), which gives a different C on the same data")
        method_label = "Rawlins-Schellhardt C, least squares on Ahmed Eq. 8-21"

    elif method == "two-point":
        lp = list(line_points) if line_points else pairs
        if len(lp) != 2:
            if len(lp) < 2:
                return Refusal(
                    reason=f"Eq. 8-22 computes n from exactly two points on the "
                           f"deliverability line; got {len(lp)}",
                    needed=("two (driving force, Q_g) points on the straight line - "
                            "Ahmed reads them off the drawn line, not off the test data",),
                    source=AHMED_BP,
                )
            raise ValueError("two-point needs exactly two line_points; pass the two you "
                             "read off the line, or use method='least-squares'")
        (dp1, q1), (dp2, q2) = lp
        if min(dp1, dp2, q1, q2) <= 0:
            return Refusal(
                reason="Eq. 8-22 takes logarithms of both the driving forces and the "
                       "rates, so all four coordinates must be strictly positive",
                needed=("two positive (driving force, Q_g) points",),
                source=AHMED_BP,
            )
        if dp1 == dp2 or q1 == q2:
            return Refusal(
                reason="the two points supplied for Eq. 8-22 share a driving force or a "
                       "rate, so the slope n is zero or undefined",
                needed=("two distinct points on the deliverability line",),
                source=AHMED_BP,
            )
        # Eq. 8-22: n = [log(Qg1) - log(Qg2)] / [log(dp1) - log(dp2)]
        n = (math.log10(q1) - math.log10(q2)) / (math.log10(dp1) - math.log10(dp2))
        cp = c_point if c_point is not None else lp[0]
        c = _c_from_point(cp, n)
        if isinstance(c, Refusal):
            return c
        fit_note = ("n from Eq. 8-22 on two points of the deliverability line, C from "
                    "Eq. 8-23 at one point - Ahmed's published procedure. If the points "
                    "were read off a hand-drawn line they are not test data and the fit "
                    "is only as good as the line")
        method_label = "Rawlins-Schellhardt C, two-point line read (Ahmed Eqs. 8-22/8-23)"

    else:  # given-n
        if n_given is None:
            raise ValueError("method='given-n' needs n_given")
        cp = c_point if c_point is not None else (pairs[0] if pairs else None)
        if cp is None:
            return Refusal(
                reason="Eq. 8-23 needs one (driving force, Q_g) point to evaluate C at; "
                       "none was supplied",
                needed=("c_point, or at least one test point",),
                source=AHMED_BP,
            )
        n = float(n_given)
        c = _c_from_point(cp, n)
        if isinstance(c, Refusal):
            return c
        fit_note = ("n supplied by the caller (read off a deliverability plot or taken "
                    "from a test report); C from Eq. 8-23 at a single point. Nothing "
                    "here checks n against the data")
        method_label = "Rawlins-Schellhardt C at a given n (Ahmed Eq. 8-23)"

    # --- physicality and validity -------------------------------------------
    if n <= 0:
        # Not stated by either source; see spec refusal 6. Eq. 8-20 is monotone
        # increasing in drawdown by construction, so n <= 0 would make the AOF
        # the well's minimum rate and every downstream IPR nonsense.
        return Refusal(
            reason=f"the fit gives n = {n:.4f}: Eq. 8-20 would then predict rate falling "
                   "as drawdown rises, and the AOF at p_wf = 0 would be the well's "
                   "minimum rather than its maximum. That is not a deliverability curve, "
                   "so the data or the reported average reservoir pressure is wrong",
            needed=("test points whose rate rises with drawdown",
                    "a verified stabilized average reservoir pressure"),
            source=AHMED_BP,
        )
    if not N_FULLY_TURBULENT <= n <= N_LAMINAR:
        side = ("above the laminar limit of 1.0 - suspect a wrong average reservoir "
                "pressure or an unstabilized point" if n > N_LAMINAR else
                "below the fully-turbulent limit of 0.5 - suspect liquid loading or a "
                "changing skin during the test")
        flags.append(
            f"n = {n:.4f} falls outside the 0.5-1.0 band Ahmed gives for "
            f"laminar-to-fully-turbulent flow ({side}). The value is reported because "
            "both sources state that band as the physical meaning of n, not as a "
            "validity limit on the fit")

    p_max = spec["p_max_psia"]
    # `>=`, not `>`: Ahmed says the form is recommended *below* 2000 psi, so
    # 2000 itself is outside it. `houpeurt.py` already read it that way and
    # the two siblings disagreed on the boundary sample.
    if p_max is not None and p_r_psia >= p_max:
        flags.append(
            f"average reservoir pressure {p_r_psia:g} psia exceeds ~{p_max:g} psia, "
            "above which the pressure-squared form loses accuracy; use "
            "form='pseudopressure', which is applicable at all pressures. The 2000 psia "
            "figure is Ahmed's, stated for the pressure-squared development at #114 "
            "printed p. 546; PetroWiki #2 states the limitation for Rawlins-Schellhardt "
            "itself but gives no number")

    flags.append(
        "Rawlins-Schellhardt is empirical and assumes every point is stabilized "
        "(pseudosteady state); this tool is not given flow-period durations and cannot "
        "check that - see deliverability_test_interpret")

    return Quantity(
        c, spec["c_unit"], method_label, spec["source"],
        inputs={
            "n": n,
            "p_r_psia": p_r_psia,
            "points": list(points) if points else [],
            "driving_force": [dp for dp, _ in pairs],
            "line_points": list(line_points) if line_points else None,
            "c_point": tuple(c_point) if c_point is not None else None,
            # Key is `psi_r`, not the argument's `psi_r_psi2_cp`: the group-I
            # fit contract that `deliverability_rate` dispatches on names it
            # `psi_r`, and one key beats a tolerant reader on both sides.
            "psi_r": psi_r_psi2_cp,
        },
        assumptions={
            "model": "Rawlins-Schellhardt",
            "form": form,
            "equation": spec["equation"],
            "driving_force": spec["driving_force"],
            "fit": f"{method}: {fit_note}",
            "validity": spec["validity"],
        },
        flags=tuple(flags),
    )


def _c_from_point(point, n: float):
    """Eq. 8-23: C = Q_g / (driving force)^n, at one point. Refusal if unusable."""
    dp, qg = point
    if dp <= 0 or qg <= 0:
        return Refusal(
            reason=f"Eq. 8-23 needs a positive driving force and rate to evaluate C at; "
                   f"got ({dp:g}, {qg:g})",
            needed=("a flowing point on the deliverability line",),
            source=AHMED_BP,
        )
    return qg / dp ** n
