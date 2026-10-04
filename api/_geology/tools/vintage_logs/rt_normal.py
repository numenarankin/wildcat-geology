"""Rt from a vintage ES suite - tool #98 `rt_from_long_normal` (group J).

Spec: `specs/98-rt_from_long_normal.md`.

Two decisions in here are not obvious from the code.

**Why this mostly refuses.** The source is a three-branch decision keyed to
`R_16"/R_m`, and two of the three branches terminate in Fig. 7-9 part B, whose
response column survived conversion only as `img-8.jpeg`. The high branch needs
Chart B-2 on top of that, which is not in the corpus at all. So the branch an
operator most wants an answer in - a tight, high-resistivity legacy pay zone -
is the branch that cannot be answered. Refusing there is the tool's purpose, not
a gap in it, and the refusal names what would unblock it rather than reaching for
the nearest relation.

**Why the branch is on every return value.** A caller computing Archie `Sw` off
this needs to know whether it is holding an `Rt` the source authorized or a
refusal wearing a number's shape. `Refusal` has no structured field for that, so
every refusal reason opens with a `[branch=...]` token and `es_rt_branch()` reads
it back off either return type.
"""
from __future__ import annotations

import math

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused; import kept uniform)

# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

TRIESTE_RT_RULES = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#1"
"""p. 7-4, "R_t From the ES Log" - the three-branch classification."""

TRIESTE_FIG_7_9 = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#2"
"""p. 7-6, Fig. 7-9 "R_t estimation from electrical logs" - parts A, B, C."""

EPA_NORMAL_RESISTIVITY = "12-vintage-logs/epa-environmental-geophysics-electrical-methods#2"
"""The R_16"/R_m departure-chart worked example: corrected values are stated
"at formation temperature", mud measured "at borehole temperature"."""

# --------------------------------------------------------------------------
# The branch key.  Trieste #1, p. 7-4, quoted in the spec:
#   1. Low    - R_16"/R_m < 10   (invasion up to 2d)
#   2. Medium - 10 < R_16"/R_m < 50
#   3. High   - R_16"/R_m > 50
# All six inequalities are strict in the source, so 10.0 and 50.0 belong to no
# branch.  The source does not say which way they fall; see spec Open question 1.
# --------------------------------------------------------------------------

BRANCH_BOUNDARY_LOW = 10.0
BRANCH_BOUNDARY_HIGH = 50.0

_BOUNDARY_EPS = 1e-9
"""Floating-point hygiene on the equality test at 10.0 and 50.0.  Not a source
threshold and not a physical tolerance - it exists so that a ratio formed as
30.0/3.0 lands on the boundary the same way 10.0/1.0 does."""

BRANCH_LOW = "low_resistivity"
BRANCH_MEDIUM = "medium_resistivity"
BRANCH_HIGH = "high_resistivity"
BRANCH_BOUNDARY_10 = "boundary_undefined_10"
BRANCH_BOUNDARY_50 = "boundary_undefined_50"

# --------------------------------------------------------------------------
# Fig. 7-9 part A, "In low resistivity, when R_16/R_m < 10 (invasion up to 2d)".
# Long Normal rows only - the Short Normal and Lateral rows are other devices
# and out of this tool's scope (see NON_LONG_NORMAL_ROWS below).
#
# "R_64 = R_t"     -> Rt = 1.0     * R_64
# "R_64 = 2/3 R_t" -> Rt = 1.5     * R_64
# "R_64 = 1/2 R_t" -> Rt = 2.0     * R_64
#
# TRANSCRIBED FROM THE ORIGINAL PDF (p. 7-6), 2026-08-05, replacing a reading
# taken from the markdown conversion.  Two things were wrong in that reading and
# both mattered:
#
#   1. The 2/3 response was lost.  Rows 2 and 5 read "R_64 = 2/3 R_t" in the
#      figure and had been transcribed as "1/2 R_t" - a 33% error in Rt on two
#      of five rows.
#   2. The R_64/R_s qualifications are printed as ">= 2.5", "<= 1.5" (15 ft) and
#      a bare "= 1.5" (10 ft), not as the approximations "=~ 2.5" / "=~ 1.5" the
#      conversion suggested.  So no snap tolerance belongs on this axis at all;
#      it is a threshold test.  The open interval 1.5 < R_64/R_s < 2.5 is
#      genuinely unaddressed by the figure and refuses.
#
# Two agents independently transcribed this table from the same OCR and agreed
# with each other.  They were both wrong.  Agreement between two readers of one
# corrupted artifact is not corroboration - only the original settles it.
#
# `thickness_ft = None` on the first row means "no nominal thickness, the row is
# a stated inequality (e > 20 ft)".  `r64_rs_qual` carries the row's R_64/R_s
# qualification exactly as printed - (">=", 2.5), ("<=", 1.5) or ("==", 1.5);
# `None` means the row carries none.  The 15 ft row prints "<= 1.5" and the
# 10 ft row prints a bare "= 1.5"; the two are NOT normalised to each other,
# because that difference is the figure's.
# --------------------------------------------------------------------------

FIG_7_9_PART_A_LONG_NORMAL = (
    {
        "row": "e > 20 ft (> 4 AM')",
        "thickness_ft": None,
        "thickness_min_ft": 20.0,
        "r64_rs_qual": None,
        "requires_rm_approx_rs": False,
        "response": "R_64 = R_t",
        "rt_multiplier": 1.0,
    },
    {
        "row": "e = 15 ft (3 AM'), R_m = R_s, R_64/R_s >= 2.5",
        "thickness_ft": 15.0,
        "thickness_min_ft": None,
        "r64_rs_qual": (">=", 2.5),
        "requires_rm_approx_rs": True,
        "response": "R_64 = 2/3 R_t",
        "rt_multiplier": 1.5,
    },
    {
        "row": "e = 15 ft (3 AM'), R_m = R_s, R_64/R_s <= 1.5",
        "thickness_ft": 15.0,
        "thickness_min_ft": None,
        "r64_rs_qual": ("<=", 1.5),
        "requires_rm_approx_rs": True,
        "response": "R_64 = R_t",
        "rt_multiplier": 1.0,
    },
    {
        "row": "e = 10 ft (2 AM'), R_m = R_s, R_64/R_s >= 2.5",
        "thickness_ft": 10.0,
        "thickness_min_ft": None,
        "r64_rs_qual": (">=", 2.5),
        "requires_rm_approx_rs": True,
        "response": "R_64 = 1/2 R_t",
        "rt_multiplier": 2.0,
    },
    {
        "row": "e = 10 ft (2 AM'), R_m = R_s, R_64/R_s = 1.5",
        "thickness_ft": 10.0,
        "thickness_min_ft": None,
        "r64_rs_qual": ("==", 1.5),
        "requires_rm_approx_rs": True,
        "response": "R_64 = 2/3 R_t",
        "rt_multiplier": 1.5,
    },
)

NON_LONG_NORMAL_ROWS = (
    "5 ft < e < 10 ft, oil bearing and SP -50 to -80 mV: Short Normal, R_16 = R_t",
    "5 ft < e < 10 ft, surrounding beds homogeneous: Lateral in resistive bed, "
    "R_t = R_max x R_s / R_min",
    "thin beds in general, surrounding beds homogeneous: Lateral in conductive bed",
)
"""Fig. 7-9 part A's remaining rows.  Named in the refusal for thin beds so the
caller learns which device the source sends them to - this tool reads the long
normal only.

The Short Normal row's response is `R_16 = R_t`, confirmed against the original
PDF (p. 7-6) on 2026-08-05.  The markdown conversion rendered it `R_18`, which is
the lateral's symbol and is the correct reading only on the *conductive-bed
lateral* row beneath it - the conversion had bled one row's symbol into another.
Spec open question 4 is closed."""

FIG_7_9_PRINTED_POINT_ROWS_FT = (15.0, 10.0)
"""The two bed thicknesses Fig. 7-9 part A prints as points for the long normal.

There is no third one and there is no band around either.  This module used to
carry a `FIG_7_9_APPROX_TOLERANCE_FRAC = 0.15` window on them and `departure.py`
carried a +/-2.5 ft window, so one published row gave two different answers at
12.6 ft.  Both are gone: **the figure never defines the "=~" it prints, so no
tolerance exists to encode**, and inventing one is what produced the divergence.
A bed is on a point row when its thickness IS the printed value; otherwise the
tool refuses and names `assume_row_ft`, through which a caller may declare the
row and own the judgement."""

FIG_7_9_POINT_ROW_REL_TOL = 1e-9
"""Float-representation tolerance on a point-row match, nothing more: a
thickness formed as 45.0/3.0 must land on the 15 ft row the way a literal 15.0
does.  Not a physical window and not a sourced threshold."""

RM_APPROX_RS_QUALIFICATION = "R_m =~ R_s"
"""Fig. 7-9 part A's other undefined "=~", printed as a qualification on the
15 ft and 10 ft rows.  The figure never defines it, and unlike the bed thickness
it prints no number at all - so there is not even a printed value to match, and
choosing zero tolerance would be as much this tool's decision as choosing 15%.

This module used to evaluate it at a provisional `+/-15%`
(`RM_APPROX_RS_TOLERANCE_FRAC`) while `departure.py` used `0.8 <= Rm/Rs <= 1.25`;
both were invented and both are deleted, with no shared replacement.  A row
carrying the qualification now refuses until the caller declares `rm_approx_rs`,
and a declared result is stamped as the caller's judgement.  Spec Open
question 3, SETTLED."""


def rm_approx_rs_declaration_note(rm_over_rs: float) -> str:
    """The stamp put on `flags` and `assumptions` when the caller declares the
    qualification satisfied.  Word-for-word `departure.py`'s stamp - one figure,
    one statement - built there from `rm_over_rs` and here from `R_m / R_s`."""
    return (
        f"'{RM_APPROX_RS_QUALIFICATION}' declared satisfied by the caller "
        f"(rm_approx_rs=True) at Rm/Rs = {rm_over_rs:g}; Fig. 7-9 prints the "
        "qualification and states no tolerance on its '=~', so this "
        "equivalence is the caller's judgement and not the figure's"
    )

AM_LONG_NORMAL_FT = 64.0 / 12.0
"""Long-normal AM spacing, 64 in.  Fig. 7-9 states its thickness rows in both ft
and multiples of AM'; recorded so the rounding in the table is auditable."""

# --------------------------------------------------------------------------
# What is missing, quoted where possible.  Named in the refusals.
# --------------------------------------------------------------------------

MISSING_FIG_7_9_PART_B = (
    "Fig. 7-9 part B 'Rules for using lateral (AO = 18 ft 8 in.)' - only the "
    "bed-thickness column survived conversion (e > 40 ft, e = 28 ft, e = 24 ft, "
    "5 ft < e < 10 ft); the entire response column is the image img-8.jpeg"
)

MISSING_CHART_B2 = (
    "Schlumberger Chart B-2 - Fig. 7-9: 'When R_16/R_m > 50, these values must be "
    "corrected for the borehole: Chart B-2.'  Not in the corpus in any form"
)


# --------------------------------------------------------------------------
# Helpers (not tools - they return plain values by design)
# --------------------------------------------------------------------------


def _classify_branch(ratio: float) -> str:
    """The three-branch key of Trieste #1 p. 7-4, boundaries left undecided."""
    if abs(ratio - BRANCH_BOUNDARY_LOW) <= _BOUNDARY_EPS:
        return BRANCH_BOUNDARY_10
    if abs(ratio - BRANCH_BOUNDARY_HIGH) <= _BOUNDARY_EPS:
        return BRANCH_BOUNDARY_50
    if ratio < BRANCH_BOUNDARY_LOW:
        return BRANCH_LOW
    if ratio < BRANCH_BOUNDARY_HIGH:
        return BRANCH_MEDIUM
    return BRANCH_HIGH


def _refuse(branch: str, reason: str, needed: tuple[str, ...], source: str) -> Refusal:
    """Every refusal opens with the branch, because `Refusal` has no field for it."""
    return Refusal(reason=f"[branch={branch}] {reason}", needed=needed, source=source)


def es_rt_branch(result) -> str | None:
    """Read the ES resistivity branch back off any `rt_from_long_normal` return.

    A downstream Archie caller needs one accessor whether it got a `Quantity` or
    a `Refusal`: the branch is what tells it whether it holds a real Rt.
    """
    assumptions = getattr(result, "assumptions", None)
    if isinstance(assumptions, dict) and "branch" in assumptions:
        return str(assumptions["branch"])
    reason = getattr(result, "reason", "")
    if reason.startswith("[branch="):
        return reason[len("[branch="):reason.index("]")].replace(" (provisional)", "")
    return None


def _on_printed_value(value: float, printed: float) -> bool:
    """Is `value` the number the figure prints, allowing only for float
    representation?  This is not a tolerance on the figure's `=~`."""
    return math.isclose(value, printed, rel_tol=FIG_7_9_POINT_ROW_REL_TOL, abs_tol=0.0)


def _qualification_holds(qual: tuple[str, float] | None, value: float) -> bool:
    """Evaluate a row's R_64/R_s qualification exactly as the figure prints it."""
    if qual is None:
        return True
    op, threshold = qual
    if op == ">=":
        return value >= threshold
    if op == "<=":
        return value <= threshold
    if op == "==":
        return _on_printed_value(value, threshold)
    raise ValueError(f"unknown qualification operator {op!r}")


def _printed_ratio_quals(rows) -> str:
    """The R_64/R_s qualifications of some rows, worded as the figure prints
    them.  `>= 2.5` on one row and a bare `= 1.5` on another are different
    statements and are not merged."""
    seen: list[str] = []
    for row in rows:
        qual = row.get("r64_rs_qual")
        if qual is None:
            continue
        # printed as the figure prints it: "==" is the figure's bare "=".
        op = "=" if qual[0] == "==" else qual[0]
        text = f"'R_64/R_s {op} {qual[1]:g}'"
        if text not in seen:
            seen.append(text)
    return " and ".join(seen) if seen else "with no R_64/R_s qualification"


# --------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------


def rt_from_long_normal(
    r_16_ohmm: float,
    r_m_ohmm: float,
    r_64_ohmm: float | None = None,
    bed_thickness_ft: float | None = None,
    r_s_ohmm: float | None = None,
    *,
    r_m_at_formation_temp: bool = False,
    curves_identified: bool = False,
    thin_bed_distorted: bool = False,
    readings_departure_corrected: bool = False,
    rm_approx_rs: bool | None = None,
    assume_row_ft: float | None = None,
):
    """True formation resistivity Rt from a conventional ES suite.

    Trieste ch. 7 p. 7-4 subdivides formations into three classes on the ratio
    `R_16"/R_m` and prescribes a different device for each.  Only the low class
    terminates in content that survived conversion (Fig. 7-9 part A); the medium
    and high classes terminate in Fig. 7-9 part B, an image, and the high class
    additionally requires Chart B-2.  Those two refuse.

    `r_16_ohmm` and `r_m_ohmm` are required and have no defaults: their ratio is
    the branch key, and without it the tool cannot say which of the source's
    three classes the reading is even in.

    `assume_row_ft` is the caller's override of the bed-thickness row match, and
    only that: it declares "treat my bed as the figure's named row". It accepts a
    printed point row and nothing else (15.0 or 10.0 - `ValueError` otherwise,
    because asking for a row the figure does not print is a bug, not a question
    the source declines). The returned `Quantity` names the real thickness, the
    row applied, and that the equivalence is the caller's judgement and not the
    figure's, on both `flags` and `assumptions`.

    `rm_approx_rs` is the caller's declaration on the rows' other qualification,
    `R_m =~ R_s`. It has NO default: the figure prints the qualification and
    never says how close is close enough, so the tool cannot evaluate it and
    will not pretend to. `None` (undeclared) refuses on any row carrying the
    qualification, naming the argument and reporting the actual `R_m/R_s`;
    `False` refuses because the caller has ruled the row out; `True` answers,
    stamped on `flags` and `assumptions` as the caller's judgement. The
    `R_64/R_s` rows are untouched by it - the figure states those as thresholds.
    """
    # --- programmer error, not source limits -------------------------------
    if assume_row_ft is not None and not any(
        _on_printed_value(assume_row_ft, p) for p in FIG_7_9_PRINTED_POINT_ROWS_FT
    ):
        raise ValueError(
            f"assume_row_ft={assume_row_ft!r} is not a printed Fig. 7-9 part A "
            "point row; the figure prints long-normal point rows at "
            + " and ".join(f"{p:g} ft" for p in FIG_7_9_PRINTED_POINT_ROWS_FT)
            + " only. The override names a row that exists; it does not create one"
        )
    for name, value in (
        ("r_16_ohmm", r_16_ohmm),
        ("r_m_ohmm", r_m_ohmm),
        ("r_64_ohmm", r_64_ohmm),
        ("r_s_ohmm", r_s_ohmm),
    ):
        if value is not None and value <= 0:
            raise ValueError(f"{name} must be a positive resistivity in ohm-m, got {value}")
    if bed_thickness_ft is not None and bed_thickness_ft <= 0:
        raise ValueError(f"bed_thickness_ft must be positive, got {bed_thickness_ft}")

    ratio = r_16_ohmm / r_m_ohmm
    branch = _classify_branch(ratio)
    key = {"R_16in": r_16_ohmm, "R_m": r_m_ohmm, "R_16/R_m": ratio}

    # --- upstream gates ----------------------------------------------------
    # These come first: if the curves were never identified, the ratio itself is
    # not the branch key, so the branch reported alongside is provisional.
    if not curves_identified:
        return _refuse(
            f"{branch} (provisional)",
            "the 16-in. and 64-in. normal curves have not been identified; on a "
            "vintage ES both are traces in one track and are sometimes plotted in "
            "the opposite order, so R_16/R_m computed off the wrong trace "
            "classifies into the wrong branch silently. Ratio "
            f"{ratio:.4g} is not usable as the branch key until the curves are named.",
            ("es_curve_identify (#96) confirming which trace is the 16-in. short "
             "normal and which the 64-in. long normal",),
            TRIESTE_RT_RULES,
        )
    if thin_bed_distorted:
        return _refuse(
            branch,
            "the reading is declared thin-bed distorted; the normal device does "
            "not read a formation resistivity in a bed thinner than its spacing "
            "(Trieste Fig. 7-3: the curve reverses and reads a minimum opposite a "
            "resistive bed), so there is no Rt in this number to correct.",
            ("departure_correction (#97) clearing the reading, or a bed thick "
             "enough for the device",),
            TRIESTE_RT_RULES,
        )

    # --- branch 3: the expensive one ---------------------------------------
    if branch == BRANCH_HIGH:
        return _refuse(
            BRANCH_HIGH,
            f"R_16/R_m = {ratio:.4g} > {BRANCH_BOUNDARY_HIGH:g}: high-resistivity "
            "class. The source withdraws the 64-in. normal here - it 'is greatly "
            "affected by invasion so the 18-ft 8-in. lateral is the best choice "
            "for estimating Rt' (Trieste p. 7-4) - and the lateral's rules are "
            "Fig. 7-9 part B, whose response column did not survive conversion, "
            "on top of which the figure requires a borehole correction from Chart "
            "B-2. This is the commercially painful case and it is not an accident: "
            "a tight, high-resistivity legacy pay zone is exactly where R_16/R_m "
            "is large (high Rt, low R_m in the fresh muds these wells were "
            "drilled with), so the zone a legacy operator most wants a saturation "
            "on is precisely the zone where the vintage ES suite cannot yield a "
            "defensible Rt. No Rt is returned and none should be inferred from "
            "the 64-in. normal reading.",
            (MISSING_FIG_7_9_PART_B,
             MISSING_CHART_B2,
             "18-ft 8-in. lateral Ra_max / Ra_min picks off the log",
             "a modern deep-reading log over the zone (laterolog or induction) - "
             "the focusing-electrode tools are 'much superior to the ES devices "
             "for large Rt/Rm values' (Trieste p. 7-5), and this is the only "
             "unblock an operator can act on today"),
            TRIESTE_RT_RULES,
        )

    if branch == BRANCH_BOUNDARY_50:
        return _refuse(
            BRANCH_BOUNDARY_50,
            f"R_16/R_m = {ratio:.4g} sits exactly on the 50 boundary. The source "
            "writes '10 < R_16/R_m < 50' and 'R_16/R_m > 50', both strict, so 50 "
            "belongs to no class and the source does not say which way it falls. "
            "The ambiguity is harmless here: the medium and high classes both "
            "terminate in Fig. 7-9 part B, so this refuses under either reading.",
            (MISSING_FIG_7_9_PART_B,
             MISSING_CHART_B2,
             "a source stating whether the class boundaries are inclusive",),
            TRIESTE_RT_RULES,
        )

    # --- branch 2: chart-dependent -----------------------------------------
    if branch == BRANCH_MEDIUM:
        lateral_note = (
            " Above R_16/R_m > 20 the source makes the lateral primary rather than "
            "confirmatory, so this reading depends on it entirely."
            if ratio > 20.0
            else " Below R_16/R_m = 20 the source calls the 64-in. normal 'very "
            "useful', but states no response for it: Fig. 7-9 part A is scoped "
            "'when R_16/R_m < 10' and does not extend here."
        )
        return _refuse(
            BRANCH_MEDIUM,
            f"R_16/R_m = {ratio:.4g} is the medium-resistivity class. The source "
            "ends this branch in a chart: 'The lateral has an unsymmetrical curve, "
            "and Rt must be picked as shown in Fig. 7-9' (Trieste p. 7-4). Fig. 7-9 "
            "part B's response column is the image img-8.jpeg - only its "
            "bed-thickness column survived conversion - so there is no relation to "
            "apply." + lateral_note + " Nothing is interpolated and no adjacent "
            "relation is substituted.",
            (MISSING_FIG_7_9_PART_B,
             "18-ft 8-in. lateral readings picked per part B",),
            TRIESTE_RT_RULES,
        )

    if branch == BRANCH_BOUNDARY_10:
        return _refuse(
            BRANCH_BOUNDARY_10,
            f"R_16/R_m = {ratio:.4g} sits exactly on the 10 boundary. The source "
            "writes 'R_16/R_m < 10' and '10 < R_16/R_m < 50', both strict, so 10 "
            "belongs to no class and the source does not say which way it falls. "
            "Unlike the 50 boundary this one changes the answer - read low it "
            "would return a number from Fig. 7-9 part A, read medium it refuses - "
            "so the conservative reading is taken and no number is returned.",
            ("a source stating whether the class boundaries are inclusive",
             "a reading whose ratio is unambiguously below 10",),
            TRIESTE_RT_RULES,
        )

    # --- branch 1: the only determinate branch -----------------------------
    # R_m biases the branch key, and it biases it downwards: mud resistivity
    # falls as temperature rises, so a surface R_m is too high, the ratio too
    # low, and a >50 bed can present as a low-resistivity bed and collect a
    # number the source never authorized.  Refuse rather than flag.
    if not r_m_at_formation_temp:
        return _refuse(
            BRANCH_LOW,
            "R_m is not declared to be at formation temperature. Mud resistivity "
            "falls as temperature rises, so a flowline or surface R_m is too high, "
            f"which makes R_16/R_m = {ratio:.4g} too low and biases the class "
            "downwards - the direction that wrongly authorizes an answer, since "
            "only the low-resistivity class returns one.",
            ("R_m at formation temperature - correct a measured R_m with "
             "resistivity_at_temperature (Arps) using formation_temperature at "
             "the zone depth",),
            EPA_NORMAL_RESISTIVITY,
        )
    if r_64_ohmm is None or bed_thickness_ft is None:
        return _refuse(
            BRANCH_LOW,
            f"R_16/R_m = {ratio:.4g} is the low-resistivity class, where the source "
            "corrects the 64-in. normal to Rt 'depending on the ratio R_64/R_s and "
            "the bed thickness' (Trieste p. 7-4). Both are missing.",
            tuple(n for n, v in (("R_64 - the 64-in. long-normal reading at the zone", r_64_ohmm),
                                 ("bed_thickness_ft - e in Fig. 7-9", bed_thickness_ft))
                  if v is None),
            TRIESTE_FIG_7_9,
        )

    override_note = None
    if assume_row_ft is not None:
        override_note = (
            f"{assume_row_ft:g} ft row applied to a {bed_thickness_ft:g} ft bed "
            f"on the caller's declaration (assume_row_ft={assume_row_ft:g}); "
            f"Fig. 7-9 states no tolerance on its '=~ {assume_row_ft:g} ft' row, "
            "so this equivalence is the caller's judgement and not the figure's"
        )

    row = _match_fig_7_9_part_a_row(
        bed_thickness_ft if assume_row_ft is None else float(assume_row_ft),
        r_64_ohmm, r_s_ohmm, r_m_ohmm, rm_approx_rs,
    )
    if isinstance(row, Refusal):
        return row

    rt = row["rt_multiplier"] * r_64_ohmm
    flags = [
        "Rt read from a discrete row of Fig. 7-9 part A, a chart; rows are not "
        "interpolated and no value between them is supported",
        "branch heading scopes this class to 'invasion up to 2d'; the ES suite "
        "gives no invasion depth, so the scope is assumed and not verified",
    ]
    if row["thickness_ft"] is not None:
        flags.append(
            f"bed thickness is on the figure's printed '{row['row']}' row; the "
            "figure states no tolerance on that thickness and none is assumed"
            if override_note is None
            else "caller_declared_row: " + override_note
        )
    if not readings_departure_corrected:
        flags.append(
            "readings are not declared departure/borehole corrected; the branch "
            "rules are 'derived from a study of resistivity departure curves'"
        )
    rm_note = None
    if row["requires_rm_approx_rs"]:
        rm_note = rm_approx_rs_declaration_note(r_m_ohmm / r_s_ohmm)
        flags.append("caller_declared_rm_approx_rs: " + rm_note)

    assumptions = {
        "branch": BRANCH_LOW,
        "fig_7_9_row": row["row"],
        "fig_7_9_response": row["response"],
        "rt_multiplier": row["rt_multiplier"],
        "thickness_row_match": (
            "the figure states no tolerance on its '=~ 15 ft' / '=~ 10 ft' rows, "
            "so the bed thickness had to be the printed value; no window assumed"
        ),
        "invasion_scope": "up to 2d (branch heading, unverified)",
    }
    if rm_note is not None:
        assumptions["rm_approx_rs"] = rm_note
    if override_note is not None:
        assumptions["assume_row_ft"] = override_note
        assumptions["thickness_row_match"] = (
            "matched on the caller's assume_row_ft, not on the bed's own "
            "thickness: " + override_note
        )

    return Quantity(
        rt,
        "ohm-m",
        f"ES Rt, low-resistivity class, Fig. 7-9 part A: {row['response']}",
        TRIESTE_FIG_7_9,
        inputs={**key, "R_64": r_64_ohmm, "R_s": r_s_ohmm,
                "bed_thickness_ft": bed_thickness_ft,
                "assume_row_ft": assume_row_ft,
                "rm_approx_rs": rm_approx_rs},
        assumptions=assumptions,
        flags=tuple(flags),
    )


def _match_fig_7_9_part_a_row(
    bed_thickness_ft: float,
    r_64_ohmm: float,
    r_s_ohmm: float | None,
    r_m_ohmm: float,
    rm_approx_rs: bool | None,
):
    """Exact row match against Fig. 7-9 part A, or a `Refusal` saying why not.

    Returns the row dict on a match.  Never interpolates and never widens: the
    `e > 20 ft` row is a band the figure states and covers its whole range, while
    `e =~ 15 ft` and `e =~ 10 ft` are points the figure prints without ever
    defining its `=~`, so they match the printed thickness and nothing else.  A
    bed off a row refuses and names `assume_row_ft`; a bed between rows refuses
    because the figure states no relation between them.

    The same holds on the other axis: the point rows are qualified `R_m =~ R_s`,
    the figure defines that `=~` no better, and it prints no number there at
    all - so the qualification is never evaluated here.  It refuses until the
    caller declares `rm_approx_rs`, reporting the real `R_m/R_s` so they can.
    """
    # Row 1: the stated inequality, no qualifications.
    inequality_row = FIG_7_9_PART_A_LONG_NORMAL[0]
    if bed_thickness_ft > inequality_row["thickness_min_ft"]:
        return inequality_row

    candidates = [r for r in FIG_7_9_PART_A_LONG_NORMAL[1:]
                  if _on_printed_value(bed_thickness_ft, r["thickness_ft"])]
    if not candidates:
        no_tolerance = (
            "Fig. 7-9 part A prints its long-normal point rows at e =~ 15 ft "
            "(3 AM') and e =~ 10 ft (2 AM') and NEVER DEFINES that '=~', so "
            "there is no window inside which a nearby bed can be said to be on "
            "a row - any such window would be this tool's invention, not the "
            "figure's statement. If you judge this bed to be one of those cases, "
            "declare it with assume_row_ft=15.0 or assume_row_ft=10.0 and the "
            "answer comes back stamped as your judgement, not the figure's."
        )
        settle_it = (
            "a source that states the tolerance on Fig. 7-9 part A's '=~ 15 ft' "
            "/ '=~ 10 ft' rows, which would settle this",
            "or assume_row_ft=15.0 / assume_row_ft=10.0 to apply a named row on "
            "your own judgement",
        )
        if bed_thickness_ft > FIG_7_9_PART_A_LONG_NORMAL[1]["thickness_ft"]:
            return _refuse(
                BRANCH_LOW,
                f"bed thickness {bed_thickness_ft:g} ft is on no row of Fig. 7-9 "
                "part A: it lies between the printed e =~ 15 ft row and the "
                "stated e > 20 ft band. The rows are discrete readings off a "
                "chart; the figure states no relation between them and "
                "interpolating one would be inventing it. " + no_tolerance,
                ("a bed thickness on a printed row - above 20 ft, or exactly "
                 "15 ft or 10 ft",)
                + settle_it
                + ("Fig. 7-9 part A at full resolution, if the original figure is "
                   "continuous rather than tabular",),
                TRIESTE_FIG_7_9,
            )
        return _refuse(
            BRANCH_LOW,
            f"bed thickness {bed_thickness_ft:g} ft has no Long Normal row in "
            "Fig. 7-9 part A. " + no_tolerance
            + " Below about 10 ft (2 AM') the figure hands the bed to another "
            "device entirely: "
            + "; ".join(NON_LONG_NORMAL_ROWS)
            + ". This tool reads the long normal, so it declines rather than "
            "extrapolating a long-normal response into thicknesses the figure "
            "does not give it.",
            ("a bed thickness on a printed Long Normal row - above 20 ft, or "
             "exactly 15 ft or 10 ft",)
            + settle_it
            + ("the short normal or 18-ft 8-in. lateral reading, per the rows "
               "above",),
            TRIESTE_FIG_7_9,
        )

    # Rows 2-5 all carry qualifications keyed on R_s.
    if r_s_ohmm is None:
        return _refuse(
            BRANCH_LOW,
            f"bed thickness {bed_thickness_ft:g} ft matches a Fig. 7-9 part A row "
            "whose qualifications are 'R_m = R_s' and "
            + _printed_ratio_quals(candidates)
            + ". Neither can be checked without the surrounding-bed resistivity.",
            ("R_s - resistivity of the surrounding (shoulder) beds, read off the "
             "same log above and below the zone",),
            TRIESTE_FIG_7_9,
        )

    rm_over_rs = r_m_ohmm / r_s_ohmm
    if rm_approx_rs is None:
        return _refuse(
            BRANCH_LOW,
            f"every Fig. 7-9 part A row at e = {candidates[0]['thickness_ft']:g} "
            f"ft is qualified '{RM_APPROX_RS_QUALIFICATION}' and the figure "
            "states NO TOLERANCE on that '=~': it prints the qualification and "
            f"never says how close is close enough. Here R_m = {r_m_ohmm:g} "
            f"ohm-m against R_s = {r_s_ohmm:g} ohm-m, R_m/R_s = "
            f"{rm_over_rs:.4g}. Whether that counts as R_m =~ R_s is a judgement "
            "about this well's mud and its shoulder beds, which the caller is in "
            "a position to make and this tool is not - any tolerance it applied "
            "would be its own invention rather than the figure's statement. "
            "Declare it with rm_approx_rs=True and the row's published multiplier "
            "comes back stamped as your judgement, not the figure's; "
            "rm_approx_rs=False rules the row out.",
            ("rm_approx_rs declared by the caller for the R_m/R_s ratio above - "
             "True to apply the row, False to rule it out",
             "or a source that states the tolerance on Fig. 7-9 part A's "
             "'R_m =~ R_s' qualification, which would settle it",),
            TRIESTE_FIG_7_9,
        )
    if rm_approx_rs is False:
        return _refuse(
            BRANCH_LOW,
            "the caller declares R_m is not approximately R_s "
            f"(rm_approx_rs=False, at R_m/R_s = {rm_over_rs:.4g}), which every "
            f"Fig. 7-9 part A row at e = {candidates[0]['thickness_ft']:g} ft "
            "requires. The source offers no long-normal response for this "
            "thickness without that qualification.",
            ("a zone where R_m = R_s", "Fig. 7-9 part B for the lateral route",),
            TRIESTE_FIG_7_9,
        )

    # The figure qualifies these rows as printed thresholds - ">= 2.5" on both
    # high rows, "<= 1.5" at 15 ft and a bare "= 1.5" at 10 ft - so this is a
    # threshold test and no tolerance applies. The open interval between them is
    # unaddressed by the source, not merely un-snapped.
    r64_rs = r_64_ohmm / r_s_ohmm
    for row in candidates:
        if _qualification_holds(row["r64_rs_qual"], r64_rs):
            return row

    return _refuse(
        BRANCH_LOW,
        f"R_64/R_s = {r64_rs:.4g} is on no row of Fig. 7-9 part A at "
        f"e = {candidates[0]['thickness_ft']:g} ft. The figure qualifies the rows "
        "there " + _printed_ratio_quals(candidates) + " and prints nothing "
        "between those thresholds, so 1.5 < R_64/R_s < 2.5 is a gap in the "
        "published figure, not a near-miss on a tabulated value - there is no "
        "branch split between them to invent.",
        ("R_64/R_s satisfying a printed qualification at this thickness: "
         + _printed_ratio_quals(candidates),
         "a source that addresses 1.5 < R_64/R_s < 2.5 at this bed thickness, "
         "which would settle it",),
        TRIESTE_FIG_7_9,
    )
