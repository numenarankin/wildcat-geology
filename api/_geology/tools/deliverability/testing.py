"""Deliverability-test interpretation — tool #85, split in two on purpose.

The catalog entry for `deliverability_test_interpret` carries the correction
"Split this: the physics stabilisation check and the regulatory compliance check
are different tools." Both live here, and nothing is shared between them but the
input data:

  `deliverability_test_interpret` — PHYSICS. Structures a multi-point test into
  the (p_wf, Qg) pairs that `backpressure_fit` (#82) and `houpeurt_fit` (#83)
  consume, classifies it as flow-after-flow / isochronal / modified isochronal
  from the evidence, and judges stabilization from the flow-period pressures.
  Source: Cullender's isochronal procedure as given in PetroWiki PEH.

  `g10_compliance_check` — REGULATORY, Texas only. The 72-hour test, the 48-hour
  pre-flow and the 75% floor are Texas RRC Statewide Rule 28 / Form G-10, a
  jurisdiction rule with no physics content.

They are separate because the two verdicts are independent. A 1962 Oklahoma
isochronal test with one-hour flow periods is physically textbook and fails every
G-10 requirement; a 72-hour Texas test in a 0.01-md reservoir passes G-10 while
the pressure transient never reaches the drainage boundary. Reading either verdict
as the other is the failure this split prevents, so the physics function's
`method` string begins "PHYSICS", the regulatory one's begins "REGULATORY", their
`source` fields point at different documents, and no G-10 constant is reachable
from the physics path.

The corpus supplies no number for "stabilized". PetroWiki defines stabilization
time as "when the flowing pressure is no longer changing or is no longer changing
significantly" and stops there; the two equations that would let a tool predict it
are images in the markdown body. So the stabilization tolerance is CALLER, and a
test with no pressure evidence returns the verdict "unproven" rather than a guess.
"""
from __future__ import annotations

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused; kept for the shared import)

# --------------------------------------------------------------------------
# Anchors
# --------------------------------------------------------------------------
PEH_ISO = "09-gas-deliverability/petrowiki-peh-inflow-outflow-performance#4"
PEH_METHODS = "09-gas-deliverability/petrowiki-peh-inflow-outflow-performance#3"
PW_METHODS = "09-gas-deliverability/petrowiki-deliverability-testing-gas-wells#0"
PW_STABILIZATION = "09-gas-deliverability/petrowiki-deliverability-testing-gas-wells#2"
TAMU_SEQUENCE = "09-gas-deliverability/tamu-png613-lec07-deliverability-testing-gas-wells#0"

RRC_G10 = "09-gas-deliverability/rrc-g10-instructions#0"
RRC_SWR28_2017 = "09-gas-deliverability/rrc-notice-swr28-g10-revisions-2017#0"
RRC_W6 = "09-gas-deliverability/rrc-section-g-well-status-reports#10"

FLOW_AFTER_FLOW = "flow_after_flow"
ISOCHRONAL = "isochronal"
MODIFIED_ISOCHRONAL = "modified_isochronal"
TEST_TYPES = (FLOW_AFTER_FLOW, ISOCHRONAL, MODIFIED_ISOCHRONAL)

_EPS = 1e-9

# --------------------------------------------------------------------------
# Physics: what each test type requires, quoted from its source.
# Every entry is (value, quote, anchor). A `None` value means the source states
# the requirement but not a number — those are CALLER inputs, never defaults.
# --------------------------------------------------------------------------
TEST_METHOD_REQUIREMENTS: dict[str, dict[str, tuple]] = {
    FLOW_AFTER_FLOW: {
        "no_intermediate_shut_in": (
            None,
            "Each flow rate is established in succession without an intermediate "
            "shut-in period.",
            PW_METHODS,
        ),
        "all_points_stabilized": (
            None,
            "the analysis techniques for conventional flow-after-flow and "
            "single-point tests require data obtained under stabilized flowing "
            "conditions",
            PW_STABILIZATION,
        ),
        "customary_point_count": (
            4,
            "It involves conducting a series of flow rates, often referred to as a "
            "four-point test, as mandated by regulatory bodies.",
            PEH_METHODS,
        ),
    },
    ISOCHRONAL: {
        "min_transient_points": (
            3,
            "a minimum of three modified isochronal tests are performed, and each "
            "test includes a minimum of three different flow rates",
            PEH_ISO,
        ),
        "equal_flow_durations": (
            None,
            "producing the well at various flow rates, each with equal durations",
            PEH_ISO,
        ),
        "shut_in_returns_to_p_r": (
            None,
            "separating them with shut-in periods to allow the bottomhole pressure "
            "to stabilize at the average reservoir pressure",
            PEH_ISO,
        ),
        "extended_stabilized_point": (
            None,
            "the test requires obtaining an extended stabilized flow point",
            PEH_ISO,
        ),
    },
    MODIFIED_ISOCHRONAL: {
        "min_transient_points": (
            3,
            "a minimum of three modified isochronal tests are performed, and each "
            "test includes a minimum of three different flow rates",
            PEH_ISO,
        ),
        "equal_flow_durations": (
            None,
            "the modified isochronal test closely resembles the standard isochronal "
            "test, with the key difference being the duration of the shut-in periods",
            PEH_ISO,
        ),
        "shut_in_at_least_flow_duration": (
            None,
            "This modification requires equal or longer shut-in periods compared to "
            "the flow periods.",
            PEH_ISO,
        ),
        "extended_stabilized_point": (
            None,
            "the extended stabilized flow point and a stabilized shut-in bottomhole "
            "pressure are still required",
            PEH_ISO,
        ),
        "prior_shut_in_pressure_per_point": (
            None,
            "the measured bottomhole pressure just before the start of each flow "
            "period is used ... This replaces the use of the average reservoir "
            "pressure in these equations",
            PEH_ISO,
        ),
    },
}

# The only numeric stabilization criterion the Texas RRC states in this corpus —
# and it belongs to Form W-6, the Communication or Packer Leakage Test, NOT to the
# G-10 deliverability test. Offered opt-in, with its scope attached, because
# borrowing it silently is `tool-verification.md` failure mode 1.
STABILIZATION_PRESETS: dict[str, dict] = {
    "rrc_w6_communication_test": {
        "window_hr": 0.25,
        "max_change_frac": 0.001,
        "reference": "shut_in_pressure",
        "quote": (
            "Under flowing conditions, the pressure may be considered stabilized "
            "when it does not vary more than 0.1% of the original shut-in well head "
            "pressure during a 15 minute interval."
        ),
        "source": RRC_W6,
        "scope": (
            "Texas RRC Form W-6 Communication or Packer Leakage Test. NOT a Form "
            "G-10 requirement and not a physics result; adopting it for a "
            "deliverability test is the caller's engineering judgment."
        ),
    },
}

# --------------------------------------------------------------------------
# Regulation: Texas RRC Form G-10 / Statewide Rule 28(c). Jurisdiction rules.
# --------------------------------------------------------------------------
G10_REQUIREMENTS: dict[str, tuple] = {
    "test_duration_hr_min": (
        72.0,
        "The test to determine the daily deliverability volume is to be of 72 hours "
        "minimum duration",
    ),
    "test_duration_hr_absolute_min": (
        24.0,
        "Under no circumstance is the deliverability test to be less than 24 hours "
        "with the hourly producing rate extrapolated to 24 hours to calculate a "
        "daily deliverability volume.",
    ),
    "pre_flow_duration_hr_min": (
        48.0,
        "pre-flow the well a minimum of 48 hours to stabilize it",
    ),
    "pre_flow_rate_fraction_min": (
        0.75,
        "pre-flow the well a minimum of 48 hours to stabilize it at a daily rate not "
        "less than 75% of the producing rate observed during the final 24 hours of "
        "the test",
    ),
    "base_pressure_psia": (
        14.65,
        "Report full-well stream deliverability volume in MCF ... measured at a base "
        "pressure of 14.65 pounds per square inch absolute (psia)",
    ),
    "base_temp_degf": (
        60.0,
        "and a standard base temperature of 60 degrees Fahrenheit",
    ),
    "condensate_gas_equivalent_mcf_per_bbl": (
        1.1,
        "If the actual gas equivalent of the condensate has not been determined by "
        "laboratory analysis, use a value of 1.1 MCF per barrel.",
    ),
    "exemption_mcfd_with_field_rules": (
        100.0,
        "If, however, deliverability and production remain at or less than 100 "
        "MCF/day ... the well is exempt from further G-10 testing",
    ),
    "exemption_mcfd_without_field_rules": (
        250.0,
        "or, in fields without special field rules, at or less than 250 MCF/day, the "
        "well is exempt from further G-10 testing",
    ),
}

# Statewide Rule 28 as amended effective 1 Jan 2017. These narrow *when a test is
# owed*, not what a test must contain, so they drive a flag and never a refusal —
# the G-10 instructions themselves allow a voluntary retest at any time.
SWR28_TEST_REQUIRED_SITUATIONS: tuple[str, ...] = (
    "initial_completion",
    "recompletion_into_different_field",
    "oil_well_reclassified_as_gas_well",
    "inactive_well_returned_to_production",
    "field_allocation_formula_uses_downhole_pressure",
    "reinstate_allowable",
    "required_by_commission_order_or_field_rule",
)

G10_JURISDICTION = "Texas (RRC Statewide Rule 28, Form G-10)"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _q(period: dict, key: str):
    v = period.get(key)
    return v


def _drift_in_window(series, window_hr: float):
    """Max pressure excursion over the last `window_hr` of a flow period.

    Returns (drift_psi, spanned) — `spanned` is False when the series is too
    short to cover the window, which is 'unproven', not 'not stabilized'.
    """
    if not series or len(series) < 2:
        return (None, False)
    times = [float(t) for t, _ in series]
    t_end, t_start = max(times), min(times)
    if (t_end - t_start) < window_hr - _EPS:
        return (None, False)
    window_pts = [float(p) for t, p in series if float(t) >= t_end - window_hr - _EPS]
    if len(window_pts) < 2:
        return (None, False)
    return (max(window_pts) - min(window_pts), True)


def _resolve_criterion(criterion):
    """A preset name or an explicit dict -> a normalised criterion dict."""
    if criterion is None:
        return None
    if isinstance(criterion, str):
        if criterion not in STABILIZATION_PRESETS:
            raise ValueError(
                f"unknown stabilization preset {criterion!r}; "
                f"known: {sorted(STABILIZATION_PRESETS)}"
            )
        return dict(STABILIZATION_PRESETS[criterion], preset=criterion)
    crit = dict(criterion)
    if "window_hr" not in crit:
        raise ValueError("a stabilization criterion needs 'window_hr'")
    if "max_change_psi" not in crit and "max_change_frac" not in crit:
        raise ValueError(
            "a stabilization criterion needs 'max_change_psi' or 'max_change_frac'"
        )
    crit.setdefault("source", "CALLER-supplied; the corpus states no numeric "
                             "stabilization tolerance")
    return crit


def _allowance(crit: dict, period: dict, p_r_psia: float):
    if "max_change_psi" in crit:
        return float(crit["max_change_psi"]), "absolute"
    ref_name = crit.get("reference", "p_r")
    if ref_name == "shut_in_pressure":
        ref = period.get("p_shut_in_psia")
        if ref is None:
            ref, ref_name = p_r_psia, "p_r (no p_shut_in_psia on this period)"
    else:
        ref = p_r_psia
    return float(crit["max_change_frac"]) * float(ref), f"fraction of {ref_name}"


def _sequence(rates: list[float]) -> str:
    if len(rates) < 2:
        return "single-point"
    if all(b > a for a, b in zip(rates, rates[1:])):
        return "increasing"
    if all(b < a for a, b in zip(rates, rates[1:])):
        return "decreasing"
    return "non-monotonic"


# --------------------------------------------------------------------------
# PHYSICS
# --------------------------------------------------------------------------
def deliverability_test_interpret(
    flow_periods: list[dict],
    p_r_psia: float,
    declared_test_type: str | None = None,
    equal_duration_tol_frac: float | None = None,
    p_r_return_tol_frac: float | None = None,
    stabilization_criterion=None,
    required_rate_sequence: str | None = None,
):
    """Structure a multi-point or isochronal gas-well test and judge stabilization.

    PHYSICS ONLY. No Texas RRC requirement is evaluated here — call
    `g10_compliance_check` for that, and read the two verdicts separately.

    flow_periods: ordered list of dicts with
        q_g_mscfd        (required, > 0)
        p_wf_psia        (required, flowing BHP at the end of the period)
        duration_hr      (required, > 0)
        shut_in_before_hr  (optional) hours shut in immediately before this period
        p_shut_in_psia     (optional) BHP measured just before this period starts
        extended           (optional bool) marks the extended stabilized flow point
        p_wf_series        (optional) [(t_hr, p_psia), ...] within the period

    Returns a Quantity whose value is the number of slope-determining analysis
    points, carrying `inputs["points"] = [(p_wf, q_g), ...]` and
    `inputs["p_r"]` in exactly the shape `backpressure_fit` and `houpeurt_fit`
    consume — or a Refusal naming every requirement that failed and by how much.
    """
    if declared_test_type is not None and declared_test_type not in TEST_TYPES:
        raise ValueError(f"declared_test_type must be one of {TEST_TYPES}")
    if required_rate_sequence not in (None, "increasing", "decreasing"):
        raise ValueError("required_rate_sequence must be 'increasing', 'decreasing' or None")
    if p_r_psia is None or float(p_r_psia) <= 0:
        raise ValueError("p_r_psia must be a positive absolute pressure")
    crit = _resolve_criterion(stabilization_criterion)

    problems: list[str] = []
    needed: list[str] = []
    flags: list[str] = []

    # ---- P1: enough periods to be a multi-point test at all -----------------
    if len(flow_periods) < 2:
        return Refusal(
            reason=(
                f"a deliverability test needs at least two flow periods; "
                f"{len(flow_periods)} given. A straight line cannot be fitted through "
                "one point — this is arithmetic, not a source requirement."
            ),
            needed=("at least two flow periods",),
            source=PEH_METHODS,
        )

    # ---- required measurements present and physical (P8) --------------------
    for i, per in enumerate(flow_periods):
        for key in ("q_g_mscfd", "p_wf_psia", "duration_hr"):
            if _q(per, key) is None:
                problems.append(f"flow period {i}: {key} is missing")
                needed.append(f"flow_periods[{i}]['{key}']")
        q, pwf, dur = _q(per, "q_g_mscfd"), _q(per, "p_wf_psia"), _q(per, "duration_hr")
        if q is not None and float(q) <= 0:
            problems.append(f"flow period {i}: q_g_mscfd = {float(q):.4g} is not positive")
        if dur is not None and float(dur) <= 0:
            raise ValueError(f"flow period {i}: duration_hr must be positive")
        if pwf is not None and float(pwf) >= float(p_r_psia) - _EPS:
            problems.append(
                f"flow period {i}: p_wf = {float(pwf):.2f} psia is not below "
                f"p_r = {float(p_r_psia):.2f} psia, so p_r^2 - p_wf^2 = "
                f"{float(p_r_psia) ** 2 - float(pwf) ** 2:.6g} psia^2 is not positive "
                "and neither backpressure_fit nor houpeurt_fit can use the point"
            )
    if problems:
        return Refusal(reason="; ".join(problems), needed=tuple(needed), source=PEH_ISO)

    # ---- classify (evidence first, declaration second) ----------------------
    later = flow_periods[1:]
    shut_in_hours_present = any(_q(p, "shut_in_before_hr") for p in later)
    shut_in_pressures = [_q(p, "p_shut_in_psia") for p in later]
    shut_in_pressures_present = all(v is not None for v in shut_in_pressures)
    observed_shut_in = shut_in_hours_present or any(v is not None for v in shut_in_pressures)

    observed_type = None
    basis = None
    max_p_r_deficit = None
    # A flow-after-flow test is *defined* by the absence of intermediate shut-ins,
    # so this contradiction is settled by evidence alone and needs no tolerance.
    if declared_test_type == FLOW_AFTER_FLOW and observed_shut_in:
        return Refusal(
            reason=(
                "declared test type 'flow_after_flow' contradicts the evidence: "
                "shut-in periods are present between flow periods, and "
                f'{PW_METHODS} defines the flow-after-flow test as one where "Each '
                'flow rate is established in succession without an intermediate '
                'shut-in period." The data reads as an isochronal or modified '
                "isochronal test"
            ),
            needed=("a corrected declared_test_type, or corrected test data",),
            source=PW_METHODS,
        )
    if not observed_shut_in:
        observed_type = FLOW_AFTER_FLOW
        basis = (
            f"no shut-in period between flow periods -> {PW_METHODS}: "
            f'"{TEST_METHOD_REQUIREMENTS[FLOW_AFTER_FLOW]["no_intermediate_shut_in"][1]}"'
        )
    elif shut_in_pressures_present and p_r_return_tol_frac is not None:
        max_p_r_deficit = max(
            abs(float(p_r_psia) - float(v)) / float(p_r_psia) for v in shut_in_pressures
        )
        if max_p_r_deficit <= float(p_r_return_tol_frac) + _EPS:
            observed_type = ISOCHRONAL
        else:
            observed_type = MODIFIED_ISOCHRONAL
        basis = (
            f"shut-in periods present; largest departure of a shut-in pressure from "
            f"p_r is {max_p_r_deficit:.4f} against the caller's "
            f"p_r_return_tol_frac = {float(p_r_return_tol_frac):.4f}"
        )
    elif declared_test_type is not None:
        observed_type = declared_test_type
        basis = (
            "caller declaration; the corpus gives no numeric tolerance for "
            '"stabilize at the average reservoir pressure", so the isochronal / '
            "modified-isochronal split could not be settled from the evidence"
        )
        if shut_in_pressures_present:
            max_p_r_deficit = max(
                abs(float(p_r_psia) - float(v)) / float(p_r_psia) for v in shut_in_pressures
            )
            flags.append(
                f"classification taken from the caller's declaration; measured "
                f"largest shut-in-pressure departure from p_r is {max_p_r_deficit:.4f} "
                "(supply p_r_return_tol_frac to have it judged)"
            )
        else:
            flags.append(
                "classification taken from the caller's declaration; no "
                "p_shut_in_psia supplied, so it could not be checked against the "
                "evidence"
            )
    else:
        return Refusal(
            reason=(
                "shut-in periods are present between flow periods, so the test is "
                "isochronal or modified isochronal, but which one cannot be "
                "determined: PEH #4 separates them by whether the shut-in pressure "
                'returns "to the average reservoir pressure", and the corpus states '
                "no tolerance for that. Supply p_shut_in_psia on every flow period "
                "together with p_r_return_tol_frac, or declare the test type."
            ),
            needed=(
                "flow_periods[i]['p_shut_in_psia'] on every period after the first",
                "p_r_return_tol_frac (CALLER — no corpus value)",
                "or declared_test_type",
            ),
            source=PEH_ISO,
        )

    # ---- P10: declaration versus evidence -----------------------------------
    if declared_test_type is not None and basis is not None and "declaration" not in basis:
        if declared_test_type != observed_type:
            return Refusal(
                reason=(
                    f"declared test type {declared_test_type!r} contradicts the "
                    f"evidence, which reads as {observed_type!r}: {basis}. Analysing "
                    "a mislabelled test by the wrong route gives a wrong flow "
                    "coefficient, so this is not resolved silently."
                ),
                needed=("a corrected declared_test_type, or corrected test data",),
                source=PEH_ISO,
            )

    test_type = observed_type
    reqs = TEST_METHOD_REQUIREMENTS[test_type]

    # ---- split transient points from the extended stabilized point ----------
    extended_idx = [i for i, p in enumerate(flow_periods) if p.get("extended")]
    if len(extended_idx) > 1:
        raise ValueError("at most one flow period may be marked extended")

    if test_type == FLOW_AFTER_FLOW:
        analysis_idx = list(range(len(flow_periods)))
        stabilized_point = None
        if extended_idx:
            flags.append(
                "a flow-after-flow test has no separate extended point — every rate "
                "is stabilized — so the 'extended' mark was carried through but not "
                "used to split the data"
            )
    else:
        if not extended_idx:
            problems.append(
                f"{test_type} test has no flow period marked extended, but "
                f'{PEH_ISO}: "{reqs["extended_stabilized_point"][1]}". Without it the '
                "flow coefficient C (or the Houpeurt intercept a) cannot be anchored"
            )
            needed.append("one flow period marked extended=True")
            analysis_idx = list(range(len(flow_periods)))
            stabilized_point = None
        else:
            analysis_idx = [i for i in range(len(flow_periods)) if i not in extended_idx]
            e = flow_periods[extended_idx[0]]
            stabilized_point = (float(e["p_wf_psia"]), float(e["q_g_mscfd"]))

    # ---- P2 / P3: point counts ----------------------------------------------
    if test_type == FLOW_AFTER_FLOW:
        customary = reqs["customary_point_count"]
        if len(analysis_idx) < customary[0]:
            flags.append(
                f"{len(analysis_idx)} flow points; {PEH_METHODS}: "
                f'"{customary[1]}" — "often", and the regulatory body is unnamed, so '
                "this is reported and not enforced"
            )
    else:
        minimum = reqs["min_transient_points"]
        if len(analysis_idx) < minimum[0]:
            problems.append(
                f"{test_type} test has {len(analysis_idx)} transient flow points, "
                f'below the {minimum[0]} of {PEH_ISO}: "{minimum[1]}" (scope caveat: '
                "that sentence sits in the multiple-modified-isochronal paragraph; it "
                "is the only stated minimum in the corpus and Example 1.2 uses three)"
            )
            needed.append(f"at least {minimum[0]} transient flow periods")

    # ---- P7 / P7': equal flow durations (isochronal families) ---------------
    duration_spread = None
    if test_type != FLOW_AFTER_FLOW and len(analysis_idx) >= 2:
        durs = [float(flow_periods[i]["duration_hr"]) for i in analysis_idx]
        duration_spread = (max(durs) - min(durs)) / min(durs)
        quote = reqs["equal_flow_durations"][1]
        if equal_duration_tol_frac is None:
            if duration_spread > _EPS:
                flags.append(
                    f"transient flow-period durations differ by a fraction of "
                    f"{duration_spread:.4f} (min {min(durs):.4g} h, max {max(durs):.4g} h); "
                    f'{PEH_ISO}: "{quote}" states equality but no tolerance, so this '
                    "is reported and not judged — supply equal_duration_tol_frac "
                    "(CALLER) to have it enforced"
                )
        elif duration_spread > float(equal_duration_tol_frac) + _EPS:
            problems.append(
                f"transient flow-period durations differ by a fraction of "
                f"{duration_spread:.4f}, above the caller's tolerance of "
                f"{float(equal_duration_tol_frac):.4f} (min {min(durs):.4g} h, max "
                f'{max(durs):.4g} h); {PEH_ISO}: "{quote}". Unequal flow periods '
                "investigate different drainage radii, which is the one assumption "
                "the isochronal method rests on"
            )
            needed.append("flow periods of equal duration, or a wider equal_duration_tol_frac")

    # ---- P5 / P11: modified-isochronal shut-in duration rule ----------------
    if test_type == MODIFIED_ISOCHRONAL:
        quote = reqs["shut_in_at_least_flow_duration"][1]
        for i in analysis_idx:
            if i == 0:
                continue
            si = _q(flow_periods[i], "shut_in_before_hr")
            dur = float(flow_periods[i]["duration_hr"])
            if si is None:
                flags.append(
                    f"flow period {i}: shut_in_before_hr is missing, so the "
                    f'"equal or longer shut-in periods" rule of {PEH_ISO} could not '
                    "be checked for it"
                )
                needed.append(f"flow_periods[{i}]['shut_in_before_hr']")
                continue
            if float(si) < dur - _EPS:
                problems.append(
                    f"flow period {i}: shut-in of {float(si):.2f} h is "
                    f"{dur - float(si):.2f} h shorter than its {dur:.2f} h flow "
                    f'period; {PEH_ISO}: "{quote}"'
                )
        # P6: the analysis pressure of a modified isochronal test
        missing_prior = [i for i in analysis_idx if _q(flow_periods[i], "p_shut_in_psia") is None]
        if missing_prior:
            problems.append(
                f"modified isochronal test is missing p_shut_in_psia on flow "
                f'period(s) {missing_prior}; {PEH_ISO}: '
                f'"{reqs["prior_shut_in_pressure_per_point"][1]}"'
            )
            needed.extend(f"flow_periods[{i}]['p_shut_in_psia']" for i in missing_prior)

    # ---- P14: rate sequence --------------------------------------------------
    rates = [float(flow_periods[i]["q_g_mscfd"]) for i in analysis_idx]
    sequence = _sequence(rates)
    if required_rate_sequence is not None and sequence != required_rate_sequence:
        problems.append(
            f"rates run {sequence} ({', '.join(f'{r:.4g}' for r in rates)}) but the "
            f"caller required {required_rate_sequence}. Note this is a CALLER rule: "
            "no source in the corpus requires a rate ordering"
        )
    elif sequence == "non-monotonic":
        flags.append(
            f"rate sequence is non-monotonic ({', '.join(f'{r:.4g}' for r in rates)}). "
            "No corpus source requires an ordering, but sequence changes the answer: "
            f"{TAMU_SEQUENCE} shows one well giving slope 1.097 in reverse sequence "
            "against 0.701 and 0.776 in normal sequence"
        )

    # ---- P12 / P13: stabilization -------------------------------------------
    if test_type == FLOW_AFTER_FLOW:
        must_be_stable = list(analysis_idx)
        transient_note = None
    else:
        must_be_stable = list(extended_idx)
        transient_note = (
            "not_required — the transient points of an isochronal test are "
            f'deliberately unstabilized; {PEH_ISO}: "eliminating the need for a '
            'series of stabilized flow rates as required in the flow-after-flow test"'
        )

    per_period_stability: dict[int, str] = {}
    if crit is None:
        verdict = "unproven"
        for i in must_be_stable:
            per_period_stability[i] = "unproven"
        flags.append(
            "stabilization not judged: no stabilization_criterion supplied. "
            f'{PW_STABILIZATION} defines stabilization as "when the flowing pressure '
            'is no longer changing or is no longer changing significantly" and gives '
            "no number, so the tolerance is CALLER and this tool will not invent one"
        )
    else:
        if "preset" in crit:
            flags.append(
                f"stabilization criterion is the preset {crit['preset']!r}: "
                f"{crit['scope']} (source {crit['source']})"
            )
        unproven, unstable = [], []
        for i in must_be_stable:
            drift, spanned = _drift_in_window(flow_periods[i].get("p_wf_series"),
                                              float(crit["window_hr"]))
            allow, allow_basis = _allowance(crit, flow_periods[i], float(p_r_psia))
            if not spanned:
                per_period_stability[i] = "unproven"
                unproven.append(i)
                continue
            if drift <= allow + _EPS:
                per_period_stability[i] = "stabilized"
            else:
                per_period_stability[i] = "not_stabilized"
                unstable.append(
                    f"flow period {i} drifted {drift:.2f} psi over the last "
                    f"{float(crit['window_hr']):.4g} h, above the allowance of "
                    f"{allow:.2f} psi ({allow_basis})"
                )
        if unstable:
            problems.append(
                "; ".join(unstable)
                + f'. {PW_STABILIZATION}: "the analysis techniques for conventional '
                'flow-after-flow and single-point tests require data obtained under '
                'stabilized flowing conditions"'
            )
        if unproven:
            flags.append(
                f"stabilization unproven on flow period(s) {unproven}: no p_wf_series, "
                "or the series does not span the criterion's window. Absence of "
                "evidence is not evidence of drift"
            )
        if unstable:
            verdict = "not_stabilized"
        elif unproven:
            verdict = "unproven"
        else:
            verdict = "stabilized"

    if problems:
        return Refusal(
            reason="; ".join(problems),
            needed=tuple(dict.fromkeys(needed)) or ("corrected test data",),
            source=PEH_ISO,
        )

    # ---- emit ----------------------------------------------------------------
    points = [(float(flow_periods[i]["p_wf_psia"]), float(flow_periods[i]["q_g_mscfd"]))
              for i in analysis_idx]
    p_prior = [_q(flow_periods[i], "p_shut_in_psia") for i in analysis_idx]

    if test_type != FLOW_AFTER_FLOW:
        flags.append(
            'inputs["points"] holds the TRANSIENT points only, because '
            f'{PEH_ISO} uses them to "determine the slope of the deliverability '
            'curve" while "the stabilized flow point is then utilized to estimate '
            'the flow coefficient, C". backpressure_fit on these points returns a '
            "correct n and a TRANSIENT C — re-anchor C on "
            'inputs["stabilized_point"] (PEH Eq. 1.29)'
        )
    if test_type == MODIFIED_ISOCHRONAL:
        flags.append(
            "modified isochronal: a scalar p_r is not this test's analysis pressure. "
            f'{PEH_ISO}: "the measured bottomhole pressure just before the start of '
            'each flow period is used ... This replaces the use of the average '
            'reservoir pressure". Use inputs["p_prior_psia"] per point; passing p_r '
            "to backpressure_fit or houpeurt_fit analyses this test as if it were a "
            "standard isochronal test"
        )
        flags.append(
            f'{PEH_ISO}: "the modified isochronal test is less accurate than the '
            'standard isochronal method"'
        )

    return Quantity(
        float(len(points)),
        "points",
        "PHYSICS: deliverability-test structuring, type classification and "
        "stabilization check (Cullender isochronal / Rawlins-Schellhardt "
        "flow-after-flow procedure). Carries no regulatory verdict",
        PEH_ISO,
        inputs={
            "points": points,
            "p_r": float(p_r_psia),
            "stabilized_point": stabilized_point,
            "p_prior_psia": p_prior,
            "flow_periods": flow_periods,
        },
        assumptions={
            "test_type": test_type,
            "classification_basis": basis,
            "declared_test_type": declared_test_type,
            "stabilization_verdict": verdict,
            "per_period_stabilization": per_period_stability,
            "transient_points_stabilization": transient_note,
            "stabilization_criterion": crit,
            "rate_sequence": sequence,
            "duration_spread_frac": duration_spread,
            "shut_in_departure_from_p_r_frac": max_p_r_deficit,
            "scope": "physics only — no jurisdiction rule is evaluated here",
        },
        flags=tuple(flags),
    )


# --------------------------------------------------------------------------
# REGULATION — Texas only
# --------------------------------------------------------------------------
def g10_compliance_check(
    test_duration_hr: float | None,
    pre_flow_duration_hr: float | None,
    final_24hr_gas_mcf: float | None = None,
    final_hourly_rate_mcfh: float | None = None,
    pre_flow_avg_rate_mcfd: float | None = None,
    pre_flow_24hr_rates_mcfd: list[float] | None = None,
    condensate_bbl_final_24hr: float = 0.0,
    gas_equivalent_mcf_per_bbl: float | None = None,
    district_approval_short_test: bool = False,
    base_pressure_psia: float = 14.65,
    base_temp_degf: float = 60.0,
    field_has_special_field_rules: bool | None = None,
    test_reason: str | None = None,
    pre_flow_rate_basis: str = "dry_gas",
):
    """Texas RRC Form G-10 / Statewide Rule 28(c) compliance. NOT a physics check.

    This is a jurisdiction rule. A test can be physically excellent and fail it
    (any out-of-state or historical test will), and a test can pass it while the
    pressure transient never reached the drainage boundary. For the physics, call
    `deliverability_test_interpret` and read that verdict separately.

    Returns a Quantity holding the full-well-stream deliverability volume that
    would be reported on the form, in MCF/d at 14.65 psia and 60 degF — or a
    Refusal listing every requirement that failed and by how much.
    """
    if pre_flow_rate_basis not in ("dry_gas", "full_well_stream"):
        raise ValueError("pre_flow_rate_basis must be 'dry_gas' or 'full_well_stream'")
    if condensate_bbl_final_24hr is None or float(condensate_bbl_final_24hr) < 0:
        raise ValueError("condensate_bbl_final_24hr must be zero or positive")

    problems: list[str] = []
    needed: list[str] = []
    flags: list[str] = []
    margins: dict[str, float] = {}

    # ---- base conditions (G8) ------------------------------------------------
    bp, bp_quote = G10_REQUIREMENTS["base_pressure_psia"]
    bt, bt_quote = G10_REQUIREMENTS["base_temp_degf"]
    if abs(float(base_pressure_psia) - bp) > 1e-6 or abs(float(base_temp_degf) - bt) > 1e-6:
        problems.append(
            f"volumes are stated at {float(base_pressure_psia):.4g} psia / "
            f"{float(base_temp_degf):.4g} degF, but {RRC_G10}: \"{bp_quote}\" and "
            f"\"{bt_quote}\". No conversion is applied: the corpus gives none for this "
            "tool, and inventing one is exactly the failure this layer exists to prevent"
        )
        needed.append("volumes referenced to 14.65 psia and 60 degF")

    # ---- the reported rate (G6) ---------------------------------------------
    dry_gas_mcfd = None
    if final_24hr_gas_mcf is not None:
        dry_gas_mcfd = float(final_24hr_gas_mcf)
    elif final_hourly_rate_mcfh is not None:
        dry_gas_mcfd = 24.0 * float(final_hourly_rate_mcfh)
        flags.append(
            f"daily volume extrapolated from an hourly rate of "
            f"{float(final_hourly_rate_mcfh):.4g} MCF/h x 24 h; {RRC_G10}: "
            f"\"{G10_REQUIREMENTS['test_duration_hr_absolute_min'][1]}\""
        )
    else:
        problems.append(
            "no final-24-hour production given; {0}: \"The reported test rate, that "
            "is, the daily deliverability volume you will be reporting on the Form "
            "G-10, is the actual production during the final 24 hours of the overall "
            "test period.\"".format(RRC_G10)
        )
        needed.append("final_24hr_gas_mcf (or final_hourly_rate_mcfh)")

    # ---- condensate gas equivalent (G10) ------------------------------------
    ge_default, ge_quote = G10_REQUIREMENTS["condensate_gas_equivalent_mcf_per_bbl"]
    cond = float(condensate_bbl_final_24hr)
    if gas_equivalent_mcf_per_bbl is None:
        ge = ge_default
        if cond > 0:
            flags.append(f"{RRC_G10}: \"{ge_quote}\" — 1.1 MCF/bbl used")
    else:
        ge = float(gas_equivalent_mcf_per_bbl)
    full_well_stream = None if dry_gas_mcfd is None else dry_gas_mcfd + cond * ge

    # ---- test duration (G1, G2, G9) -----------------------------------------
    d_min, d_quote = G10_REQUIREMENTS["test_duration_hr_min"]
    d_abs, d_abs_quote = G10_REQUIREMENTS["test_duration_hr_absolute_min"]
    if test_duration_hr is None:
        problems.append("test_duration_hr is missing, so the 72-hour requirement "
                        "cannot be evaluated")
        needed.append("test_duration_hr")
    else:
        td = float(test_duration_hr)
        if td <= 0:
            raise ValueError("test_duration_hr must be positive")
        margins["test_duration_hr"] = td
        margins["test_duration_margin_hr"] = td - d_min
        if td < d_abs - _EPS:
            problems.append(
                f"test duration {td:.2f} h is {d_abs - td:.2f} h below the absolute "
                f"floor of {d_abs:.0f} h; {RRC_G10}: \"{d_abs_quote}\". District "
                "approval cannot cure this"
            )
            needed.append(f"a test of at least {d_abs:.0f} hours")
        elif td < d_min - _EPS:
            if district_approval_short_test:
                flags.append(
                    f"short test: {td:.2f} h is {d_min - td:.2f} h below the "
                    f"{d_min:.0f} h minimum, permitted only because prior district "
                    f"office approval was declared; {RRC_G10}: \"Obtain prior approval "
                    "from the district office before conducting a test of less than "
                    "72-hours duration.\""
                )
            else:
                problems.append(
                    f"test duration {td:.2f} h is {d_min - td:.2f} h short of the "
                    f"{d_min:.0f} h minimum and no prior district-office approval was "
                    f"declared; {RRC_G10}: \"{d_quote}\"; \"Obtain prior approval from "
                    "the district office before conducting a test of less than "
                    "72-hours duration.\""
                )
                needed.append(f"a {d_min:.0f}-hour test, or district_approval_short_test=True")

    # ---- pre-flow duration (G3, G4) -----------------------------------------
    pf_min, pf_quote = G10_REQUIREMENTS["pre_flow_duration_hr_min"]
    if pre_flow_duration_hr is None:
        problems.append(
            f"pre-flow duration is missing, so the 48-hour stabilization requirement "
            f"cannot be evaluated; {RRC_G10}: \"{pf_quote}\""
        )
        needed.append("pre_flow_duration_hr")
    else:
        pf = float(pre_flow_duration_hr)
        if pf < 0:
            raise ValueError("pre_flow_duration_hr must be zero or positive")
        margins["pre_flow_duration_hr"] = pf
        margins["pre_flow_duration_margin_hr"] = pf - pf_min
        if pf < pf_min - _EPS:
            problems.append(
                f"pre-flow duration {pf:.2f} h is {pf_min - pf:.2f} h short of the "
                f"{pf_min:.0f} h minimum; {RRC_G10}: \"{pf_quote}\""
            )
            needed.append(f"a pre-flow of at least {pf_min:.0f} hours")

    # ---- pre-flow rate versus the 75% floor (G5, G7) -------------------------
    frac_min, frac_quote = G10_REQUIREMENTS["pre_flow_rate_fraction_min"]
    pre_avg = None
    if pre_flow_avg_rate_mcfd is not None:
        pre_avg = float(pre_flow_avg_rate_mcfd)
        if pre_flow_24hr_rates_mcfd:
            flags.append("both pre_flow_avg_rate_mcfd and pre_flow_24hr_rates_mcfd "
                         "given; the explicit average was used")
    elif pre_flow_24hr_rates_mcfd:
        comp = [float(r) for r in pre_flow_24hr_rates_mcfd]
        pre_avg = sum(comp) / len(comp)
        if len(comp) != 2:
            flags.append(
                f"{len(comp)} component 24-hour rates averaged; {RRC_G10} describes "
                "the case of two: \"The average producing rate during that initial "
                "minimum 48-hour stabilization period is the average of the producing "
                "rates during the two 24-hour component periods.\""
            )
    else:
        problems.append(
            f"no pre-flow rate given, so the 75% floor cannot be evaluated; "
            f"{RRC_G10}: \"{frac_quote}\""
        )
        needed.append("pre_flow_avg_rate_mcfd (or pre_flow_24hr_rates_mcfd)")

    if pre_avg is not None and dry_gas_mcfd is not None:
        reference = dry_gas_mcfd if pre_flow_rate_basis == "dry_gas" else full_well_stream
        floor = frac_min * reference
        margins["pre_flow_avg_rate_mcfd"] = pre_avg
        margins["pre_flow_rate_floor_mcfd"] = floor
        margins["pre_flow_rate_fraction"] = (pre_avg / reference) if reference else float("nan")
        if cond > 0:
            flags.append(
                f"the 75% floor was taken against the {pre_flow_rate_basis} final-24-h "
                f"rate ({reference:.4g} MCF/d). The G-10 instruction says \"the "
                "producing rate observed during the final 24 hours\" without saying "
                "whether that is dry gas or full-well stream, and the two differ for a "
                "condensate well — set pre_flow_rate_basis explicitly"
            )
        if pre_avg < floor - 1e-9:
            problems.append(
                f"pre-flow average rate {pre_avg:.4g} MCF/d is "
                f"{floor - pre_avg:.4g} MCF/d below the floor of {floor:.4g} MCF/d "
                f"({frac_min:.0%} of the final-24-hour rate {reference:.4g} MCF/d; "
                f"ratio {pre_avg / reference:.4f}); {RRC_G10}: \"{frac_quote}\""
            )
            needed.append("a pre-flow stabilized at 75% or more of the final-24-hour rate")

    # ---- SWR 28 trigger (G12) ------------------------------------------------
    if test_reason is not None and test_reason not in SWR28_TEST_REQUIRED_SITUATIONS:
        flags.append(
            f"test_reason {test_reason!r} is not one of the seven situations that "
            f"require a test under Statewide Rule 28 as amended effective 1 Jan 2017 "
            f"({RRC_SWR28_2017}): {', '.join(SWR28_TEST_REQUIRED_SITUATIONS)}. Not a "
            f"defect — {RRC_G10} allows the form to be filed \"at any time to report "
            "an initial test, a retest, or to correct information already filed\""
        )

    if problems:
        return Refusal(
            reason="TEXAS RRC FORM G-10 / STATEWIDE RULE 28 (regulatory, not physics): "
                   + "; ".join(problems),
            needed=tuple(dict.fromkeys(needed)),
            source=RRC_G10,
        )

    # ---- exemption note (G11) ------------------------------------------------
    ex_with, ex_with_quote = G10_REQUIREMENTS["exemption_mcfd_with_field_rules"]
    ex_without, ex_without_quote = G10_REQUIREMENTS["exemption_mcfd_without_field_rules"]
    if full_well_stream <= ex_with + _EPS:
        flags.append(f"{full_well_stream:.4g} MCF/d — {RRC_G10}: \"{ex_with_quote}\"")
    elif field_has_special_field_rules is False and full_well_stream <= ex_without + _EPS:
        flags.append(f"{full_well_stream:.4g} MCF/d — {RRC_G10}: \"{ex_without_quote}\"")

    return Quantity(
        full_well_stream,
        "MCF/d",
        "REGULATORY (Texas RRC Statewide Rule 28 / Form G-10): full-well-stream "
        "deliverability volume and compliance of the test procedure. This is a "
        "jurisdiction rule, not a physics stabilization result",
        RRC_G10,
        inputs={
            "dry_gas_final_24hr_mcf": dry_gas_mcfd,
            "condensate_bbl_final_24hr": cond,
            "gas_equivalent_mcf_per_bbl": ge,
            "test_duration_hr": test_duration_hr,
            "pre_flow_duration_hr": pre_flow_duration_hr,
            "pre_flow_avg_rate_mcfd": pre_avg,
            "margins": margins,
        },
        assumptions={
            "jurisdiction": G10_JURISDICTION,
            "compliance": "compliant",
            "scope": "regulatory only — carries no statement about physical "
                     "stabilization; call deliverability_test_interpret for that",
            "base_pressure_psia": float(base_pressure_psia),
            "base_temp_degf": float(base_temp_degf),
            "district_approval_short_test": bool(district_approval_short_test),
            "pre_flow_rate_basis": pre_flow_rate_basis,
        },
        flags=tuple(flags),
    )
