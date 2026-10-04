"""Drillstem testing. Earlougher, *Advances in Well Test Analysis*, Chapter 8.

Three tools, none of which is a formula in the usual sense, and each shaped by
something the source says that a bare reading of the catalog entry would miss.

`dst_structure` is a schema, not a calculation. Its one non-obvious decision:
the Fig. 8.1 caption as OCR'd prints `p_if1` and `p_if2` twice each, where the
second of each pair is the *final* flowing pressure. The running text at #3
names those `p_ff1` and `p_ff2`, and Eqs. 8.10/8.11 take `p_ff2`, so the schema
uses the text's names and records the caption defect at the table rather than
silently normalising it. Nothing is ever derived from anything else here — in
particular the tested interval `h` is not computed from a top/bottom pair,
because for a single-packer test with tail pipe the tested interval is
packer-to-bottom and the source defines neither.

`dst_validate` is the one that can do real damage by being eager. Sec. 8.4 names
fourteen chart signatures and **most of them are not failures**: surface flow,
drill-collar fillup, gas going into solution, wellbore storage below the CIP
valve, and heading are all normal behaviour. The source states a data verdict for
exactly two of the fourteen ("Such test data cannot be analyzed", Fig. 8.13; and
Fig. 8.11's "test data must be disregarded", which the source gates on a separate
confirmation — an abnormally large mud recovery). So severity is a five-level
field taken from the source's own wording, only `invalidating` clears the
analysable flag, and a `malfunction` is never promoted. The same caution drives
the hydrostatic-mud check: Example 8.1 accepts a 1.04% p_ihm-to-p_fhm difference
as "indicative of the accuracy of p_i", so that check reports and does not judge.
An observation the source does not name is refused, not classified.

`dst_recovery_volume` needs capacity *by string section*. Example 8.1's 315-ft oil
column occupies the top 173 ft of drill collar and then 142 ft of drillpipe at
2.34x the capacity; one multiplication over the whole column is off by 46% on the
rate, and the source's own example blows up on exactly this (Ammann reported no
drill collar where the data show 240 ft, and k/mu came out a factor of two apart).
So a missing string description is a refusal, never a single assumed capacity.
The catalog asks for a gas-cut correction; the source has none. It mentions
gas-cut mud once, and *discards* the reported gas-cut length in favour of one
derived from pressure and mud gradient. Requesting the correction therefore
refuses.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .result import Quantity, Refusal

# ---------------------------------------------------------------------------
# Corpus anchors
# ---------------------------------------------------------------------------
FIG_81 = "03-dst/earlougher-well-test-analysis-part2-1977#1"       # Sec. 8.1, Fig. 8.1
LIMITED_DATA = "03-dst/earlougher-well-test-analysis-part2-1977#3"  # wellsite subset, Table 8.1
TICKET = "03-dst/earlougher-well-test-analysis-part2-1977#4"        # Fig. 8.5 layout, mud check
EXAMPLE_81 = "03-dst/earlougher-well-test-analysis-part2-1977#5"    # Example 8.1 recovery volume
FLOW_DATA = "03-dst/earlougher-well-test-analysis-part2-1977#6"     # flow-period analysis
TROUBLE = "03-dst/earlougher-well-test-analysis-part2-1977#8"       # Sec. 8.4 signatures

# ---------------------------------------------------------------------------
# Fig. 8.1 field list  (source: FIG_81)
#
# The caption as OCR'd reads "p_if1 = initial flowing pressure in first flow
# period; p_if1 = final flowing pressure in first flow period" and repeats the
# defect for the second cycle. The final-flowing symbols are p_ff1 / p_ff2 per
# the running text at LIMITED_DATA ("the pressure at the end of each flow
# period, p_ff1 and p_ff2") and per Eqs. 8.10 and 8.11, which take p_ff2.
# ---------------------------------------------------------------------------
FIG_81_PRESSURES: dict[str, str] = {
    "p_ihm": "initial hydrostatic mud pressure",
    "p_if1": "initial flowing pressure in first flow period",
    "p_ff1": "final flowing pressure in first flow period",
    "p_isi": "initial shut-in pressure",
    "p_if2": "initial flowing pressure in second flow period",
    "p_ff2": "final flowing pressure in second flow period",
    "p_fsi": "final shut-in pressure",
    "p_fhm": "final hydrostatic mud pressure",
}

#: The six chart phases of Fig. 8.1, in order.
FIG_81_PERIODS: tuple[str, ...] = (
    "going into hole",
    "initial flow period",
    "initial shut-in period",
    "final flow period",
    "final shut-in period",
    "coming out of hole",
)

#: Read at the wellsite before the service company reads the full chart
#: (LIMITED_DATA). This subset is what Eqs. 8.8 through 8.11 consume.
WELLSITE_SUBSET: tuple[str, ...] = ("p_ihm", "p_isi", "p_ff1", "p_ff2", "p_fsi", "p_fhm")

#: Period durations, "usually also reported" at the wellsite (LIMITED_DATA).
DURATION_FIELDS: dict[str, str] = {
    "initial_flow_min": "initial flow period",
    "initial_shut_in_min": "initial shut-in period",
    "final_flow_min": "final flow period",
    "final_shut_in_min": "final shut-in period",
}

#: Ticket header and per-period bookkeeping, Fig. 8.5 (TICKET).
TICKET_HEADER_FIELDS: dict[str, str] = {
    "gauge_no": "Gauge No.",
    "gauge_depth_ft": "Depth (ft)",
    "clock_no": "Clock No.",
    "clock_hours": "clock duration (hours)",
    "ticket_no": "Ticket No.",
    "reading_interval_min": "Reading Interval (minutes)",
    "remarks": "REMARKS",
}

#: Fields the Example 8.1 text reads off the Fig. 8.6 data sheet (EXAMPLE_81).
#: Fig. 8.6 is an image in the corpus and is not transcribed; this is the set the
#: prose names, not the full service-company form.
DATA_SHEET_FIELDS: dict[str, str] = {
    "gauge_depth_ft": "depth to the gauge (ft)",
    "mud_density_lbm_per_gal": "mud density (lbm/gal)",
    "recovery_description": "description of the recovery",
    "recovery_len_ft": "length of recovery in the drillstring (ft)",
    "drill_collar_len_ft": "length of drill collar in the tool string (ft)",
    "drill_collar_id_in": "drill collar inside diameter (in.)",
    "drill_collar_capacity_bbl_per_ft": "drill collar capacity (bbl/ft)",
    "drillpipe_capacity_bbl_per_ft": "drillpipe capacity (bbl/ft)",
    "tested_interval_h_ft": "tested interval thickness h (ft)",
    "oil_gravity_api": "oil gravity (degrees API)",
    "situation_during_test": "Table 8.1 'Situation During Test' descriptor",
}

#: Table 8.1 "Situation During Test" values (LIMITED_DATA).
BLOW_DESCRIPTIONS: tuple[str, ...] = (
    "strong, continuing blow",
    "blow dies",
    "reservoir fluid produced at surface",
)

#: Table 8.1 minimum times, minutes (LIMITED_DATA). Recommendations for use "when
#: experience in the area is not available" — never validity criteria, so a
#: shortfall is a flag and never a refusal.
#:
#: Used when the ticket does not state a "Situation During Test". The initial
#: flow and initial shut-in rows are situation-independent ("All"); the two final
#: rows are not, and their entries here are the strong-continuing-blow values,
#: which is the stricter of the tabulated pair — a fallback, not a source claim.
TABLE_81_MINIMUM_MIN: dict[str, float] = {
    "initial_flow_min": 3.0,      # table reads "3 to 5"; 3 is its lower bound
    "initial_shut_in_min": 30.0,
    "final_flow_min": 60.0,
    "final_shut_in_min": 45.0,
}

#: Table 8.1's Minimum Time column is per-situation for the final flow and final
#: shut-in rows (LIMITED_DATA), and the tabulated minimums differ by situation:
#:
#:   Final flow      strong, continuing blow ............. 60
#:                   blow dies ........................... (blank: "Shut in when
#:                                                          blow dies")
#:                   reservoir fluid produced at surface .. 60
#:   Final shut-in   strong continuous blow .............. 45
#:                   blow dies ........................... two times flow time
#:                   reservoir fluid produced at surface .. 30
#:
#: `None` means the table gives no minimum for that combination, so no shortfall
#: can be reported against it. The blow-dies final shut-in is `None` here because
#: its minimum is a multiple of the flow time rather than a constant; it is
#: checked separately so the flag can carry the table's footnote ("there will be
#: no buildup, so no buildup analysis"), which is what actually blocks analysis.
TABLE_81_SITUATION_MINIMUM_MIN: dict[str, dict[str, float | None]] = {
    "strong, continuing blow": {"final_flow_min": 60.0, "final_shut_in_min": 45.0},
    "blow dies": {"final_flow_min": None, "final_shut_in_min": None},
    "reservoir fluid produced at surface": {"final_flow_min": 60.0,
                                            "final_shut_in_min": 30.0},
}

#: Named by the catalog entry but by no figure in the source. Carried through so a
#: ticket is not silently truncated, always flagged so it is not mistaken for a
#: sourced field. Surface flow appears in the source as a chart feature (Fig. 8.20,
#: "the flat portion in the second flow period indicates the well is flowing at the
#: surface"), never as a ticket field.
UNSOURCED_PASSTHROUGH: dict[str, str] = {
    "time_to_surface_min": "no figure in Chapter 8 names a time-to-surface field",
    "tested_interval_top_ft": "the source names the tested interval only as the thickness h",
    "tested_interval_bottom_ft": "the source names the tested interval only as the thickness h",
}

_NUMERIC_FIELDS = (
    set(FIG_81_PRESSURES)
    | set(DURATION_FIELDS)
    | {"gauge_depth_ft", "clock_hours", "reading_interval_min"}
    | {"mud_density_lbm_per_gal", "recovery_len_ft", "drill_collar_len_ft",
       "drill_collar_id_in", "drill_collar_capacity_bbl_per_ft",
       "drillpipe_capacity_bbl_per_ft", "tested_interval_h_ft", "oil_gravity_api"}
    | {"time_to_surface_min", "tested_interval_top_ft", "tested_interval_bottom_ft"}
)


def _as_float(name: str, value: Any) -> float:
    """Coerce a ticket field, raising on junk. Bad types are programmer error."""
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric, got {value!r}") from exc
    if out < 0:
        raise ValueError(f"{name} must not be negative, got {out}")
    return out


def dst_structure(ticket: Mapping[str, Any], pressure_unit: str = "psig"):
    """Structure a parsed DST ticket against the Fig. 8.1 / Fig. 8.5 field lists.

    Computes nothing. Reports how much of the Fig. 8.1 pressure set is present and
    therefore which analysis route the source allows: the full Horner route needs
    the chart, the limited-data route (Eqs. 8.8 to 8.11) needs the wellsite subset.
    Missing fields are named, never filled.

    Pressures are psig, temperature-corrected — the Fig. 8.5 column heading is
    "PSIG Temp. Corr." and Example 8.1 works in psig throughout. A psia ticket is
    a programmer error and raises.
    """
    if pressure_unit != "psig":
        raise ValueError(
            "DST chart pressures are psig, temperature-corrected (Fig. 8.5 column "
            f"heading); got pressure_unit={pressure_unit!r}")

    pressures: dict[str, float] = {}
    durations: dict[str, float] = {}
    header: dict[str, Any] = {}
    data_sheet: dict[str, Any] = {}
    passthrough: dict[str, Any] = {}
    unrecognized: dict[str, Any] = {}

    for key, raw in ticket.items():
        if raw is None:
            continue
        value = _as_float(key, raw) if key in _NUMERIC_FIELDS else raw
        if key in FIG_81_PRESSURES:
            pressures[key] = value
        elif key in DURATION_FIELDS:
            durations[key] = value
        elif key in TICKET_HEADER_FIELDS:
            header[key] = value
        elif key in DATA_SHEET_FIELDS:
            data_sheet[key] = value
        elif key in UNSOURCED_PASSTHROUGH:
            passthrough[key] = value
        else:
            unrecognized[key] = value

    if not pressures:
        return Refusal(
            reason="the ticket carries none of the eight Fig. 8.1 pressures; there is "
                   "nothing to structure and no analysis route in Sec. 8.3 can start",
            needed=(f"at least the initial shut-in pressure p_isi "
                    f"(Eq. 8.8 takes p_i ~= p_isi); the full Fig. 8.1 set is "
                    f"{', '.join(FIG_81_PRESSURES)}",),
            source=FIG_81)

    present = tuple(k for k in WELLSITE_SUBSET if k in pressures)
    missing = tuple(k for k in WELLSITE_SUBSET if k not in pressures)

    flags: list[str] = []
    if missing:
        named = ", ".join(f"{k} ({FIG_81_PRESSURES[k]})" for k in missing)
        flags.append(
            f"wellsite-reported subset incomplete, missing {named}; the limited-data "
            "route (Eqs. 8.9 to 8.11) is unavailable without it")
    # Table 8.1's Minimum Time column is per-situation on the two final rows;
    # fall back to the situation-independent table when no descriptor is given.
    minimums: dict[str, float | None] = dict(TABLE_81_MINIMUM_MIN)
    _situation = data_sheet.get("situation_during_test")
    if isinstance(_situation, str):
        minimums.update(TABLE_81_SITUATION_MINIMUM_MIN.get(_situation, {}))
    for key, label in DURATION_FIELDS.items():
        minimum = minimums[key]
        if key not in durations:
            flags.append(f"{label} duration not reported; the Horner plot needs t_p")
        elif minimum is not None and durations[key] < minimum:
            flags.append(
                f"{label} of {durations[key]:g} min is below the Table 8.1 minimum of "
                f"{minimum:g} min; Table 8.1 is a recommendation for "
                "when experience in the area is not available, not a validity criterion")
    if durations.get("final_shut_in_min") is not None and \
            data_sheet.get("situation_during_test") == "blow dies":
        flow = durations.get("final_flow_min")
        if flow is not None and durations["final_shut_in_min"] < 2 * flow:
            flags.append(
                "the blow died during the flow period; Table 8.1 asks for a minimum "
                f"shut-in of twice the flow time ({2 * flow:g} min) in that case, and "
                "notes there will be no buildup, so no buildup analysis")
    if data_sheet.get("situation_during_test") is not None and \
            data_sheet["situation_during_test"] not in BLOW_DESCRIPTIONS:
        flags.append(
            f"situation_during_test {data_sheet['situation_during_test']!r} is not one "
            f"of the Table 8.1 descriptors {BLOW_DESCRIPTIONS}")
    for key in passthrough:
        flags.append(f"{key} carried through unvalidated: {UNSOURCED_PASSTHROUGH[key]}")
    if {"tested_interval_top_ft", "tested_interval_bottom_ft"} <= set(passthrough) \
            and "tested_interval_h_ft" not in data_sheet:
        flags.append(
            "a top/bottom pair was given without the tested interval h; h is not "
            "derived from it — for a single-packer test with tail pipe the tested "
            "interval runs packer-to-bottom and the source defines neither")
    if unrecognized:
        flags.append(
            f"not named by Fig. 8.1, Fig. 8.5 or the Fig. 8.6 data sheet, held aside: "
            f"{', '.join(sorted(unrecognized))}")

    return Quantity(
        float(len(pressures)), "count",
        "DST ticket structuring (Fig. 8.1 field list)", FIG_81,
        inputs={"pressures_psig": pressures,
                "durations_min": durations,
                "header": header,
                "data_sheet": data_sheet,
                "unsourced_passthrough": passthrough,
                "unrecognized": unrecognized,
                "wellsite_subset_present": present,
                "wellsite_subset_missing": missing,
                "chart_periods": FIG_81_PERIODS},
        assumptions={"pressure_basis": "psig, temperature-corrected (Fig. 8.5 heading)",
                     "p_ff1/p_ff2": "Fig. 8.1 caption prints p_if1/p_if2 twice; the "
                                    "final-flowing symbols are named p_ff1 and p_ff2 in "
                                    "the text at " + LIMITED_DATA,
                     "field_sources": {"pressures": FIG_81, "durations": LIMITED_DATA,
                                       "header": TICKET, "data_sheet": EXAMPLE_81}},
        flags=tuple(flags))


# ---------------------------------------------------------------------------
# Sec. 8.4 named chart signatures  (source: TROUBLE, Figs. 8.10 to 8.23)
#
# severity levels, and why five rather than two:
#   invalidating   - the source itself says the data must be disregarded or
#                    cannot be analysed. Two entries only.
#   malfunction    - the source names a tool/gauge/packer/plugging malfunction
#                    but states no verdict on the data. Reported, never promoted.
#   data_limitation- part of the record is unusable and the source says which
#                    part remains usable.
#   hole_condition - a warning about what may happen, not a chart defect.
#   not_a_failure  - normal or expected behaviour. Seven of the fourteen:
#                    Figs. 8.12, 8.17, 8.18, 8.20, 8.21, 8.22, 8.23.
# ---------------------------------------------------------------------------
_NOT_A_FAILURE = "not_a_failure"
_MALFUNCTION = "malfunction"
_INVALIDATING = "invalidating"
_DATA_LIMITATION = "data_limitation"
_HOLE_CONDITION = "hole_condition"

DST_SIGNATURES: dict[str, dict[str, Any]] = {
    "tight_hole": {
        "figure": "8.10", "severity": _HOLE_CONDITION, "source": TROUBLE,
        "wording": "Tight hole condition. This may cause pressure surging or tool sticking.",
        "verdict": None},
    "hydrostatic_mud_decrease": {
        "figure": "8.11", "severity": _MALFUNCTION, "source": TROUBLE,
        "wording": "Leaking drillpipe or mud loss to some formation, or both, are "
                   "indicated by the hydrostatic mud-pressure decrease shown here. A "
                   "leaking drillpipe may be confirmed if an abnormally large amount of "
                   "mud is recovered with the produced fluids. In this case test data "
                   "must be disregarded.",
        "verdict": None,
        # Escalates to invalidating only on the source's own confirmation.
        "confirmed_severity": _INVALIDATING,
        "confirmed_verdict": "In this case test data must be disregarded.",
        "confirmed_by": "an abnormally large amount of mud recovered with the produced fluids"},
    "delay_going_in_no_mud_loss": {
        "figure": "8.12", "severity": _NOT_A_FAILURE, "source": TROUBLE,
        "wording": "Delay while going into the hole without mud loss.",
        "verdict": None},
    "stair_stepping_buildup": {
        "figure": "8.13", "severity": _INVALIDATING, "source": TROUBLE,
        "wording": "The stair-stepping pattern in the buildup curves indicates a "
                   "malfunctioning pressure gauge or recorder. Such test data cannot "
                   "be analyzed.",
        "verdict": "Such test data cannot be analyzed."},
    "clock_stopped": {
        "figure": "8.14", "severity": _MALFUNCTION, "source": TROUBLE,
        "wording": "Clock stopped.", "verdict": None},
    "clock_ran_away": {
        "figure": "8.15", "severity": _MALFUNCTION, "source": TROUBLE,
        "wording": "Clock ran away.", "verdict": None},
    "s_shape_flow_and_buildup": {
        "figure": "8.16", "severity": _MALFUNCTION, "source": TROUBLE,
        "wording": "The S shape of the latter part of the flow curve and the early part "
                   "of the buildup curve indicates fluid communication around the "
                   "packer. This may be caused by a fracture or a poorly seated packer.",
        "verdict": None},
    "s_shape_buildup_only": {
        "figure": "8.17", "severity": _NOT_A_FAILURE, "source": TROUBLE,
        "wording": "An S shape occurring only in the buildup portion of the curve "
                   "indicates gas is going into solution in the wellbore. This mechanism "
                   "is characterized by a sharp transition between the flow and buildup "
                   "curves.",
        "verdict": None},
    "s_shape_first_flow_only": {
        "figure": "8.18", "severity": _NOT_A_FAILURE, "source": TROUBLE,
        "wording": "An S-shaped curve occurs only in the first flow period when the "
                   "volume below the closed-in pressure valve is large compared with the "
                   "volume of the fluid flowed during the flow period. A wellbore storage "
                   "effect caused by the relatively large volume between the hydrospring "
                   "tester and CIP valves.",
        "verdict": None},
    "up_and_down_pressure": {
        "figure": "8.19", "severity": _MALFUNCTION, "source": TROUBLE,
        "wording": "This behavior indicates a plugged bottom-hole choke or perforated "
                   "anchor. The up-and-down nature of the pressure curve is caused by "
                   "momentary breakthrough and release of the pressure.",
        "verdict": None},
    "flat_second_flow": {
        "figure": "8.20", "severity": _NOT_A_FAILURE, "source": TROUBLE,
        "wording": "The flat portion in the second flow period indicates the well is "
                   "flowing at the surface.",
        "verdict": None},
    "slope_decrease_flow": {
        "figure": "8.21", "severity": _NOT_A_FAILURE, "source": TROUBLE,
        "wording": "A decrease in slope in either flow period indicates fillup of the "
                   "drill collar and transition to a drillpipe of a larger internal "
                   "diameter.",
        "verdict": None},
    "gas_surface_flow_water_cushion": {
        "figure": "8.22", "severity": _NOT_A_FAILURE, "source": TROUBLE,
        "wording": "This behavior typically occurs in gas reservoirs when flow occurs at "
                   "the surface. The pressure decrease at Point G is caused by the water "
                   "cushion flowing at the surface, which decreases average density of "
                   "the flowing column.",
        "verdict": None},
    "rippled_flow_curve": {
        "figure": "8.23", "severity": _NOT_A_FAILURE, "source": TROUBLE,
        "wording": "The rippled appearance in the flow curve indicates that gas has "
                   "broken through the liquid in the drillstring and the well is flowing "
                   "by heads.",
        "verdict": None},
    # Same chapter, different sections. Carried because each states an explicit
    # verdict on which part of the record survives.
    "linear_flowing_pressure_rise": {
        "figure": "Sec. 8.3", "severity": _DATA_LIMITATION, "source": LIMITED_DATA,
        "wording": "If the pressure in the flowstring recorder increases linearly with "
                   "time ... the controlling factor is critical flow through the "
                   "perforations in the anchor pipe.",
        "verdict": "the flowing pressure data from the flowstring recorder are useless, "
                   "although shut-in data are analyzable ... all data from the blanked-off "
                   "recorder can be analyzed in the normal fashion"},
    "well_kills_itself": {
        "figure": "Sec. 8.3", "severity": _DATA_LIMITATION, "source": FLOW_DATA,
        "wording": "the pressure exerted by the produced fluid column can reach the "
                   "reservoir pressure, causing production to stop during the flow "
                   "period - the well kills itself.",
        "verdict": "data from the shut-in period cannot be analyzed. However, flow-period "
                   "data can be analyzed by multiple-rate techniques or by type-curve "
                   "matching"},
}

#: Sec. 8.4: "A good DST chart has the following characteristics."
GOOD_CHART_CRITERIA: tuple[str, ...] = (
    "The pressure base line is straight and clear.",
    "Recorded initial and final hydrostatic mud pressures are the same and are "
    "consistent with depth and mud weight.",
    "Flow and buildup pressures are recorded as smooth curves.",
)

#: Example 8.1 (TICKET): "The difference of 1.04 percent between p_ihm and p_fhm
#: may be a result of mud loss. Such differences in the range of 0.5 to 1 percent
#: are indicative of the accuracy of p_i estimated from a DST." Reported, not
#: judged; the source gives no cutoff at which the pair alone condemns a test.
MUD_PRESSURE_ACCURACY_BAND_PCT: tuple[float, float] = (0.5, 1.0)

#: The largest difference the source is on record accepting, from the same
#: passage. Used as the comparison point rather than the band's 1.0, so that the
#: source's own worked example does not trip its own check.
MUD_PRESSURE_ACCEPTED_PCT = 1.04

#: LIMITED_DATA: extrapolated p_i "should be about the same for both the initial
#: and final shut-in periods ... a typical value might be 5 percent."
P_I_AGREEMENT_PCT = 5.0


def dst_validate(observations: Sequence[str] = (), *,
                 p_ihm_psig: float | None = None, p_fhm_psig: float | None = None,
                 mud_recovery_abnormal: bool | None = None,
                 baseline_straight_and_clear: bool | None = None,
                 curves_smooth: bool | None = None,
                 p_i_initial_psig: float | None = None,
                 p_i_final_psig: float | None = None):
    """Assess a DST chart against the Sec. 8.4 named signatures.

    Takes observations already read off the chart — this tool does not digitise a
    chart and does not infer a pattern from numbers. `value` is 1.0 while the
    chart is analysable and drops to 0.0 only on a signature the source itself
    declares unanalysable. An observation Sec. 8.4 does not name is refused,
    because there is no source verdict to report for it.
    """
    obs = tuple(observations or ())
    unknown = [o for o in obs if o not in DST_SIGNATURES]
    if unknown:
        return Refusal(
            reason=f"{', '.join(repr(u) for u in unknown)} is not among the chart "
                   "signatures Sec. 8.4 names; refusing to classify an unnamed pattern",
            needed=(f"one of: {', '.join(sorted(DST_SIGNATURES))}",),
            source=TROUBLE)

    stated = (p_ihm_psig is not None or p_fhm_psig is not None
              or baseline_straight_and_clear is not None or curves_smooth is not None
              or p_i_initial_psig is not None or p_i_final_psig is not None)
    if not obs and not stated:
        return Refusal(
            reason="no chart observations and no recorded pressures were supplied; "
                   "there is nothing to assess",
            needed=("chart signatures from Sec. 8.4, or the recorded hydrostatic mud "
                    "pressures p_ihm and p_fhm, or the good-chart criteria",),
            source=TROUBLE)

    findings: list[dict[str, Any]] = []
    flags: list[str] = []
    invalidating = False

    for key in obs:
        sig = DST_SIGNATURES[key]
        severity, verdict = sig["severity"], sig["verdict"]
        if key == "hydrostatic_mud_decrease":
            if mud_recovery_abnormal is True:
                severity = sig["confirmed_severity"]
                verdict = sig["confirmed_verdict"]
            else:
                flags.append(
                    "Fig. 8.11 pattern seen, but a leaking drillpipe is only confirmed by "
                    f"{sig['confirmed_by']}; without that confirmation the source states "
                    "no verdict on the data")
        if severity == _INVALIDATING:
            invalidating = True
        findings.append({"key": key, "figure": sig["figure"], "severity": severity,
                         "wording": sig["wording"], "verdict": verdict,
                         "source": sig["source"]})
        if severity != _NOT_A_FAILURE:
            flags.append(f"Fig. {sig['figure']} [{severity}]: {sig['wording']}"
                         + (f" VERDICT: {verdict}" if verdict else ""))

    if baseline_straight_and_clear is False:
        flags.append(f"good-chart criterion 1 not met: \"{GOOD_CHART_CRITERIA[0]}\" "
                     "(Sec. 8.4 states no data verdict for this on its own)")
    if curves_smooth is False:
        flags.append(f"good-chart criterion 3 not met: \"{GOOD_CHART_CRITERIA[2]}\" "
                     "(Sec. 8.4 states no data verdict for this on its own)")

    mud_pct = None
    if p_ihm_psig is not None and p_fhm_psig is not None:
        if p_ihm_psig <= 0:
            raise ValueError("p_ihm_psig must be positive")
        mud_pct = 100.0 * (p_ihm_psig - p_fhm_psig) / p_ihm_psig
        lo, hi = MUD_PRESSURE_ACCURACY_BAND_PCT
        if abs(mud_pct) <= MUD_PRESSURE_ACCEPTED_PCT:
            flags.append(
                f"p_fhm is {mud_pct:+.2f}% off p_ihm; the source calls differences in the "
                f"{lo} to {hi} percent range indicative of the accuracy of p_i estimated "
                "from a DST, and accepts 1.04% in Example 8.1 as possible mud loss - "
                "not a failure")
        elif mud_pct > MUD_PRESSURE_ACCEPTED_PCT:
            flags.append(
                f"hydrostatic mud pressure fell {mud_pct:.2f}% over the test, more than "
                f"the {MUD_PRESSURE_ACCEPTED_PCT}% Example 8.1 accepts as mud loss; the "
                "source states no cutoff. Fig. 8.11 associates a hydrostatic mud-pressure "
                "decrease with leaking drillpipe or mud loss, and disregarding the data "
                "needs the abnormal-mud-recovery confirmation, which was not supplied"
                if mud_recovery_abnormal is not True else
                f"hydrostatic mud pressure fell {mud_pct:.2f}% and an abnormally large mud "
                "recovery is reported (Fig. 8.11); note the source ties the disregard "
                "verdict to the Fig. 8.11 chart pattern, which was not among the "
                "observations given")
        else:
            flags.append(
                f"hydrostatic mud pressure rose {-mud_pct:.2f}% over the test; good-chart "
                f"criterion 2 asks that they be the same, and Sec. 8.4 names no signature "
                "for an increase")
    elif p_ihm_psig is not None or p_fhm_psig is not None:
        flags.append("good-chart criterion 2 skipped: it compares the recorded initial "
                     "and final hydrostatic mud pressures and only one was supplied")

    p_i_pct = None
    if p_i_initial_psig is not None and p_i_final_psig is not None:
        if p_i_initial_psig <= 0:
            raise ValueError("p_i_initial_psig must be positive")
        p_i_pct = 100.0 * abs(p_i_initial_psig - p_i_final_psig) / p_i_initial_psig
        if p_i_pct > P_I_AGREEMENT_PCT:
            flags.append(
                f"extrapolated p_i differs by {p_i_pct:.1f}% between the initial and final "
                f"shut-ins, past the {P_I_AGREEMENT_PCT:g} percent the source offers as a "
                "typical significance level; 'a very small reservoir or a bad test is "
                "indicated ... the test should be repeated with a longer final flow "
                "period, if possible'")

    return Quantity(
        0.0 if invalidating else 1.0, "bool",
        "DST chart trouble-shooting (Sec. 8.4 named signatures)", TROUBLE,
        inputs={"observations": obs, "findings": tuple(findings),
                "p_ihm_psig": p_ihm_psig, "p_fhm_psig": p_fhm_psig,
                "mud_pressure_change_pct": mud_pct,
                "mud_recovery_abnormal": mud_recovery_abnormal,
                "p_i_initial_psig": p_i_initial_psig, "p_i_final_psig": p_i_final_psig,
                "p_i_difference_pct": p_i_pct},
        assumptions={"analysable": "1.0 unless a signature the source itself calls "
                                   "unanalysable is present",
                     "severity_levels": (_INVALIDATING, _MALFUNCTION, _DATA_LIMITATION,
                                         _HOLE_CONDITION, _NOT_A_FAILURE),
                     "good_chart_criteria": GOOD_CHART_CRITERIA,
                     "not_implemented": "criterion 2's 'consistent with depth and mud "
                                        "weight' is reported, not judged: Example 8.1 "
                                        "accepts 5.66% and 4.57% deviations from the "
                                        "depth-and-mud-weight calculation as mud-density "
                                        "error, and no cutoff is stated"},
        flags=tuple(flags))


# ---------------------------------------------------------------------------
# Recovered-column volume  (source: EXAMPLE_81)
#
# Capacities are given data in the source, never computed there from an ID, so
# this module holds no ID-to-capacity formula. The two values below are the
# Example 8.1 string, kept for the oracle and for reference - they are that
# string's capacities, not a pipe table.
# ---------------------------------------------------------------------------
EXAMPLE_81_CAPACITY_BBL_PER_FT: dict[str, float] = {
    "2.5-in.-ID drill collar": 0.00607,
    "drillpipe (Example 8.1)": 0.01422,
}


def dst_recovery_volume(recovered_len_ft: float,
                        string_sections: Sequence[Mapping[str, Any]] | None, *,
                        prior_fill_len_ft: float = 0.0,
                        gas_cut: bool = False,
                        apply_gas_cut_correction: bool = False):
    """Recovered fluid column to barrels, section by section. Example 8.1.

    `string_sections` runs **bottom-first**, each entry
    `{"name", "len_ft", "capacity_bbl_per_ft"}`; only the topmost may give
    `len_ft = None`, meaning it runs to surface. `prior_fill_len_ft` is fluid
    already standing at the bottom of the string — the "67 ft mud" term — and the
    recovered column sits above it, as the source's arithmetic places it.

    Refuses without a string description: the collar-to-drillpipe transition is
    the whole point of the calculation, and assuming one capacity is the error the
    source's own worked example is a warning about.
    """
    if recovered_len_ft < 0 or prior_fill_len_ft < 0:
        raise ValueError("lengths must not be negative")

    if not string_sections:
        return Refusal(
            reason="no drillstring description was given; the recovered column normally "
                   "crosses the drill-collar/drillpipe transition (Example 8.1: 173 ft of "
                   "collar at 0.00607 bbl/ft then 142 ft of pipe at 0.01422 bbl/ft) and a "
                   "single assumed capacity is wrong by a factor of over two",
            needed=("string_sections ordered from the bottom, each with len_ft and "
                    "capacity_bbl_per_ft (the topmost may give len_ft=None for 'to "
                    "surface')",),
            source=EXAMPLE_81)

    if apply_gas_cut_correction:
        return Refusal(
            reason="the source states no gas-cut correction. Chapter 8 mentions gas-cut "
                   "recovery once - Fig. 8.6 'reports that 75 ft of oil- and gas-cut mud "
                   "were recovered' - and then sets that reported length aside in favour "
                   "of 67 ft derived from pressure and mud gradient. No shrinkage factor "
                   "or gas/liquid correction appears anywhere in the chapter",
            needed=("a published gas-cut or shrinkage correction for DST recoveries, or a "
                    "surface-gauged rate",),
            source=EXAMPLE_81)

    sections = list(string_sections)
    for i, sec in enumerate(sections):
        cap = sec.get("capacity_bbl_per_ft")
        name = sec.get("name", f"section {i + 1}")
        if cap is None:
            return Refusal(
                reason=f"{name} has no capacity_bbl_per_ft; the source prints pipe "
                       "capacities as given data and never derives them from an inside "
                       "diameter, so none can be computed here",
                needed=(f"capacity_bbl_per_ft for {name}, from the DST ticket or a pipe "
                        "data table",),
                source=EXAMPLE_81)
        if float(cap) <= 0:
            raise ValueError(f"{name}: capacity_bbl_per_ft must be positive")
        if sec.get("len_ft") is None and i != len(sections) - 1:
            return Refusal(
                reason=f"{name} is not the topmost section but has no len_ft; only the "
                       "section running to surface may be open-ended",
                needed=(f"len_ft for {name}",),
                source=EXAMPLE_81)
        if sec.get("len_ft") is not None and float(sec["len_ft"]) < 0:
            raise ValueError(f"{name}: len_ft must not be negative")

    open_topped = sections[-1].get("len_ft") is None
    described_len = sum(float(s["len_ft"]) for s in sections if s.get("len_ft") is not None)
    if not open_topped and prior_fill_len_ft > described_len:
        return Refusal(
            reason=f"the pre-existing fill of {prior_fill_len_ft:g} ft already exceeds the "
                   f"{described_len:g} ft of string described",
            needed=("a string description covering the full fluid column",),
            source=EXAMPLE_81)

    remaining = float(recovered_len_ft)
    cursor = float(prior_fill_len_ft)  # ft occupied, measured from the string bottom
    base = 0.0
    per_section: list[dict[str, Any]] = []
    total = 0.0
    for sec in sections:
        cap = float(sec["capacity_bbl_per_ft"])
        name = sec.get("name", "section")
        length = float(sec["len_ft"]) if sec.get("len_ft") is not None else float("inf")
        top = base + length
        free_from = max(cursor, base)
        free = max(0.0, top - free_from)
        take = min(remaining, free)
        if take > 0:
            bbl = take * cap
            total += bbl
            per_section.append({"name": name, "len_in_section_ft": take,
                                "capacity_bbl_per_ft": cap, "bbl": bbl})
            remaining -= take
        base = top
        if remaining <= 0:
            break

    if remaining > 1e-9:
        return Refusal(
            reason=f"the recovered column runs {remaining:g} ft above the top of the "
                   f"described string ({described_len:g} ft with {prior_fill_len_ft:g} ft "
                   "already filled); capacity above the description is unknown, and a "
                   "column that reached surface means the well flowed at the surface "
                   "(Fig. 8.20) and the rate should be gauged rather than inferred",
            needed=("string sections covering the full column, or a surface-gauged rate",),
            source=EXAMPLE_81)

    flags: list[str] = []
    if gas_cut:
        flags.append(
            "recovery reported as gas-cut; this is the in-pipe column volume with no "
            "correction, because the source states none. In Example 8.1 the reported "
            "75 ft of oil- and gas-cut mud was set aside for 67 ft derived from pressure "
            "and mud gradient")
    if not per_section:
        flags.append("recovered column length is zero; nothing was recovered")
    elif len(per_section) > 1:
        flags.append(
            "column crosses " + str(len(per_section) - 1) + " string transition(s); "
            "capacities differ by "
            f"{max(s['capacity_bbl_per_ft'] for s in per_section) / min(s['capacity_bbl_per_ft'] for s in per_section):.2f}x")
    else:
        flags.append("column lies within a single string section")
    flags.append(
        "accuracy is bounded by the reported pipe sizes: in Example 8.1 an inconsistent "
        "drill-collar report put k/mu a factor of two apart between the two flow periods")

    return Quantity(
        total, "bbl", "recovered column volume by string section (Example 8.1)",
        EXAMPLE_81,
        inputs={"recovered_len_ft": float(recovered_len_ft),
                "prior_fill_len_ft": float(prior_fill_len_ft),
                "per_section": tuple(per_section),
                "string_sections": tuple(
                    {"name": s.get("name"), "len_ft": s.get("len_ft"),
                     "capacity_bbl_per_ft": s.get("capacity_bbl_per_ft")}
                    for s in sections)},
        assumptions={"column_position": "the recovered column stands above any "
                                        "pre-existing fill ('assuming that the oil flows "
                                        "through the dense mud')",
                     "fluid": "one fluid type over the whole column, as the source "
                              "assumes; it names that assumption as a source of error",
                     "gas_cut_correction": "none exists in the source"},
        flags=tuple(flags))
