"""`departure_correction` (#97) — bed-thickness distortion of vintage ES curves.

The catalog calls this an `equation`. It is not one, and `tool-verification.md`
says so: "`md_to_tvd`, `cbl_bond_index`, `departure_correction`: `equation` ->
cannot be, until a source is acquired." Departure correction proper is a family
of *charts* — Schlumberger's departure curves, keyed by spacing, Rm, hole
diameter, bed thickness and invasion diameter — and this corpus holds them only
as images (`img-8.jpeg` inside the Fig. 7-9 transcription; "Figure 5" and
"Figure 10" in the EPA document are captions with no data behind them).

So the tool answers the question the prose *can* answer — **is this reading
usable, and how is the bed geometry distorting it** — and refuses the one it
cannot: *here is the corrected Rt*. Returning a corrected number off a chart the
corpus does not contain would be inventing the chart.

Three things here are real and citable:

* the **geometric rules** (R1-R5 in `specs/97-departure_correction.md`): a bed
  logs one AM spacing thinner on a normal when it is resistive and one AM
  thicker when it is conductive; below one AM the normal curve *reverses* and
  the resistive bed reads lower than the shale; a lateral is asymmetric, blind
  for an AO below the bed, and needs 50 ft for a plateau;
* the **Fig. 7-9 Part A table**, whose text (unlike Part B) survived OCR — it
  carries two non-unity numeric factors, `R_64 = 2/3 R_t` and `R_64 = 1/2 R_t`,
  on rows the figure prints at two thicknesses and nowhere between them;
* the **lateral thin-bed relation** `Rt ~= Rmax * Rs / Rmin`, which the prose
  states as the inequality `(Ramax/Ramin) <= (Rt/Rs)` — so the table's value is
  a *floor* on Rt, and this module returns it as one.

`usability_verdict()` is the machine-readable half, written for
`rt_from_long_normal` (#98): a per-curve verdict plus the expected direction of
error, from the rule tables below, with no interpretation of its own.

**A checkpoint for whoever digitizes the charts.** `epa#2` prints one worked
point off Figure 5: "If the apparent resistivity on a 40-cm (16-in) normal log
is 60 ohm-m and the R m is 0.5 ohm-m in a 23-cm (9-in) well, the ratio on the
X-axis is 195. The corrected log value is 97.5 ohm-m at formation temperature."
That is 60/0.5 = 120 in, 195 out, 195 * 0.5 = 97.5. The mapping 120 -> 195
exists nowhere but the chart, which is why `borehole_correction` refuses even
with all three of those numbers in hand. Keep the point: it is a free test case
the day a chart family arrives.

See `specs/97-departure_correction.md` for every quoted sentence.
"""
from __future__ import annotations

import math

from ..result import Quantity, Range, Refusal

TRIESTE_DEVICES = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#0"
TRIESTE_SHAPES = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#1"
TRIESTE_FIG79 = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#2"
EPA_ELECTRICAL = "12-vintage-logs/epa-environmental-geophysics-electrical-methods#2"

# --------------------------------------------------------------------------
# Spacings
# --------------------------------------------------------------------------
# trieste#0: "The distance AM is called the spacing (16-in. spacing for the
# short normal, 64-in. spacing for the long normal)" and "The spacing AO is
# 18 ft 8 in."  epa#2 adds that other normals exist ("10, 20, 40 and 81 cm
# (4, 8, 16, and 32 in)") and that a groundwater lateral uses AO = 1.8 m, which
# is why both spacings are overridable rather than hard-wired.
SPACING_IN: dict[str, float] = {"short_normal": 16.0, "long_normal": 64.0}
LATERAL_AO_FT = 18.0 + 8.0 / 12.0  # 18 ft 8 in = 18.666666... ft
NORMAL_CURVES = ("short_normal", "long_normal")
KNOWN_CURVES = NORMAL_CURVES + ("lateral",)
CONTRASTS = ("resistive", "conductive")

# --------------------------------------------------------------------------
# Normal-device verdicts, in AM multiples.  Source phrases in the values.
# --------------------------------------------------------------------------
# Ordered thickest-first; the first row whose `min_am` the bed clears wins.
# `usable` False means no correction recovers Rt from the reading.
NORMAL_VERDICTS: tuple[dict, ...] = (
    {
        "verdict": "reads_rt",
        "min_am": 10.0,
        "usable": True,
        "error_direction": "low",
        "quote": "in a thick bed (h = 10 AM) ... the reading is almost equal to Rt",
        "source": TRIESTE_SHAPES,
    },
    {
        "verdict": "approaches_rt",
        "min_am": 6.0,
        "usable": True,
        "error_direction": "low",
        "quote": (
            "With a bed thickness six times AM, the recorded resistivity "
            "approaches, but does not reach, the true resistivity (Rt)"
        ),
        "source": EPA_ELECTRICAL,
    },
    {
        "verdict": "depressed",
        "min_am": 1.0,  # exclusive: h must be strictly greater than one AM
        "usable": True,
        "error_direction": "low",
        "quote": (
            "the apparent value of the 64-in. normal can be easily corrected to "
            "Rt, depending on the ratio R_64/R_s and the bed thickness "
            "(see Fig. 7-9)"
        ),
        "source": TRIESTE_SHAPES,
    },
    {
        "verdict": "reversed",
        "min_am": 0.0,
        "usable": False,
        "error_direction": "inverted",
        "quote": (
            "The log response when the bed thickness is equal to or less than "
            "the AM spacing ... The curve reverses, and the high-resistivity bed "
            "actually appears to have a lower value than the surrounding material."
        ),
        "source": EPA_ELECTRICAL,
    },
)

# trieste#1 says "a thickness less than the spacing"; epa#2 says "equal to or
# less than the AM spacing".  We take EPA's - the stricter reading, and EPA is
# the catalog's designated anchor for the bed-thickness rules - so h == AM
# reverses.  Flagged on every result rather than silently chosen.
REVERSAL_BOUNDARY_NOTE = (
    "reversal boundary taken as h <= AM (epa#2, 'equal to or less than'); "
    "trieste#1 says 'less than the spacing' - the two sources differ at h = AM"
)

# --------------------------------------------------------------------------
# Lateral verdicts, in feet.  trieste#1 + epa#2.
# --------------------------------------------------------------------------
LATERAL_PLATEAU_FT = 50.0
LATERAL_BEST_RESULTS_AO_MULTIPLE = 2.0

LATERAL_VERDICTS: tuple[dict, ...] = (
    {
        "verdict": "plateau",
        "usable": True,
        "error_direction": "reads_rt_below_upper_ao",
        "quote": (
            "a minimum bed thickness of about 50 ft is needed to obtain these "
            "plateau readings uninfluenced by surrounding formations"
        ),
        "source": TRIESTE_SHAPES,
    },
    {
        "verdict": "best_results_no_plateau",
        "usable": True,
        "error_direction": "asymmetric_low_over_upper_ao",
        "quote": "Best results are obtained when bed thickness is greater than twice AO",
        "source": EPA_ELECTRICAL,
    },
    {
        "verdict": "distorted",
        "usable": False,
        "error_direction": "asymmetric_unquantified",
        "quote": (
            "Anomalies are asymmetrical about a bed, and the amount of "
            "distortion is related to bed thickness and the effect of adjacent "
            "beds. For these reasons, the lateral log is not recommended"
        ),
        "source": EPA_ELECTRICAL,
    },
)

# --------------------------------------------------------------------------
# Fig. 7-9 Part A (trieste#2).  The only numeric correction factors in either
# source.  Header: "A. In low resistivity, when R_{16}/R_{m} < 10 (invasion up
# to 2d)" - the whole table is gated on that ratio.
#
# `rt_over_ra` is the multiplier taking the apparent reading to Rt, so
# "R_64 = 1/2 R_t" is 2.0, "R_64 = 2/3 R_t" is 1.5, "R_64 = R_t" is 1.0.
# Values corrected against the original PDF on 2026-08-05; the markdown
# conversion had lost the 2/3 rows.  Enforced against rt_normal.py below.
#
# `e_ft` None means the row is a band, given by `e_low_ft`/`e_high_ft`.
# The table prints AM' = 5 ft (it calls 15 ft "3 AM'" and 10 ft "2 AM'"), a
# rounding of the true 64 in; the geometric rules above use the true spacing.
#
# `r64_over_rs_qual` is the row's R_64/R_s qualification AS PRINTED: (">=", 2.5),
# ("<=", 1.5) or ("==", 1.5).  The three are not normalised to one another - the
# figure prints "<= 1.5" on the 15 ft row and a bare "= 1.5" on the 10 ft row,
# and that difference is the figure's, so it is encoded and not smoothed away.
# `None` means the row carries no R_64/R_s qualification.
# --------------------------------------------------------------------------
FIG_79A_GATE_R16_OVER_RM = 10.0

#: The two thicknesses Fig. 7-9 Part A prints as points, in the figure's own
#: order of appearance.  Nothing else is a point row.
FIG_79A_PRINTED_POINT_ROWS_FT: tuple[float, ...] = (15.0, 10.0)

#: Float-representation tolerance on a point-row match, and nothing more.  It
#: exists so a thickness arrived at as 45.0/3.0 lands on the 15 ft row the same
#: way a literal 15.0 does.  It is NOT a physical window: the figure states no
#: tolerance on its "e =~ 15 ft" / "e =~ 10 ft" rows, so this tool does not
#: invent one.  See `assume_row_ft` for the caller's way through.
FIG_79A_POINT_ROW_REL_TOL = 1e-9

FIG_79A_ROWS: tuple[dict, ...] = (
    {
        "e_ft": None, "e_low_ft": 20.0, "e_high_ft": None, "e_low_exclusive": True,
        "device": "long_normal", "rt_over_ra": 1.0,
        "row": "e > 20 ft (> 4 AM') | Long Normal | R_64 = R_t",
        "needs_rm_approx_rs": False, "r64_over_rs_qual": None,
    },
    {
        "e_ft": 15.0, "device": "long_normal", "rt_over_ra": 1.5,
        "row": "e = 15 ft (3 AM') | R_m = R_s, R_64/R_s >= 2.5 | Long Normal | R_64 = 2/3 R_t",
        "needs_rm_approx_rs": True, "r64_over_rs_qual": (">=", 2.5),
    },
    {
        "e_ft": 15.0, "device": "long_normal", "rt_over_ra": 1.0,
        "row": "e = 15 ft (3 AM') | R_m = R_s, R_64/R_s <= 1.5 | Long Normal | R_64 = R_t",
        "needs_rm_approx_rs": True, "r64_over_rs_qual": ("<=", 1.5),
    },
    {
        "e_ft": 10.0, "device": "long_normal", "rt_over_ra": 2.0,
        "row": "e = 10 ft (2 AM') | R_m = R_s, R_64/R_s >= 2.5 | Long Normal | R_64 = 1/2 R_t",
        "needs_rm_approx_rs": True, "r64_over_rs_qual": (">=", 2.5),
    },
    {
        # The figure prints a bare "=" here, not the "<=" of the 15 ft row.
        "e_ft": 10.0, "device": "long_normal", "rt_over_ra": 1.5,
        "row": "e = 10 ft (2 AM') | R_m = R_s, R_64/R_s = 1.5 | Long Normal | R_64 = 2/3 R_t",
        "needs_rm_approx_rs": True, "r64_over_rs_qual": ("==", 1.5),
    },
    {
        "e_ft": None, "e_low_ft": 5.0, "e_high_ft": 10.0, "e_low_exclusive": True,
        "device": "short_normal", "rt_over_ra": 1.0,
        # OCR prints "R_{18}" here.  Confirmed against the original PDF
        # (knowledge-base/originals/.../trieste-...-ch7-resistivity.pdf p. 7-6,
        # read 2026-08-05): the figure prints R_16 = R_t.  The conversion bled
        # the lateral's symbol from the row below.
        "row": "5 ft < e < 10 ft | oil bearing, SP -50 to -80 mV | Short Normal | R_16 = R_t",
        "needs_rm_approx_rs": False, "r64_over_rs_qual": None,
        "needs_oil_and_sp": True, "e_high_exclusive": True,
    },
    {
        # Label as printed.  The figure prints "R_{19''} =~ R_t" on this row,
        # while section B of the SAME figure defines the lateral as
        # AO = 18 ft 8 in.  The two do not reconcile and this corpus offers
        # nothing that settles which is meant, so the label is transcribed as
        # printed rather than silently corrected to R_18'8".  UNRECONCILED -
        # label text only; every number and every rule here still uses
        # LATERAL_AO_FT = 18 ft 8 in., section B's spacing.
        "e_ft": None, "e_low_ft": None, "e_high_ft": None,
        "device": "lateral", "rt_over_ra": 1.0,
        "row": "Thin beds (in general) | surrounding beds homogeneous | "
               "Lateral in conductive bed | R_19'' =~ R_t",
        "needs_rm_approx_rs": False, "r64_over_rs_qual": None,
        "conductive_only": True,
    },
)

#: The thickness rows the figure actually prints, per device, for naming in a
#: refusal.  The point rows are quoted with the figure's own glyph so the caller
#: can see that the figure gives no tolerance on them.
FIG_79A_PRINTED_THICKNESS_ROWS: dict[str, str] = {
    "long_normal": "e > 20 ft (> 4 AM'), e =~ 15 ft (3 AM') and e =~ 10 ft (2 AM')",
    "short_normal": "5 ft < e < 10 ft",
    "lateral": (
        "5 ft < e < 10 ft (lateral in resistive bed) and 'Thin beds (in general)' "
        "(lateral in conductive bed)"
    ),
}

SHORT_NORMAL_SP_BAND_MV = (-80.0, -50.0)  # "SP is -50 to -80 mV"

#: The conductive-lateral row is headed only "Thin beds (in general)" - the
#: table never quantifies "thin" for it. Bounded here by EPA's own lateral
#: limit, "Best results are obtained when bed thickness is greater than twice
#: AO", so anything at or above 2 AO is not a thin bed. PROVISIONAL: the
#: boundary is EPA's, but its application to this row is ours.
LATERAL_THIN_BED_MAX_FT = LATERAL_BEST_RESULTS_AO_MULTIPLE * LATERAL_AO_FT

# --------------------------------------------------------------------------
# What the figure does and does not quantify.
#
# It printed "e =~ 15 ft" and "e =~ 10 ft" and never defined "=~".  This module
# and `rt_normal` each used to invent a window for it - +/-2.5 ft here, +/-15%
# there - so one published row produced two different answers at 12.6 ft.  Both
# windows are gone.  A bed is on a point row when its thickness IS the printed
# value; otherwise the tool refuses and names `assume_row_ft`, through which the
# caller may declare the row and own the judgement.  No shared replacement
# constant is defined, because no such number exists in the source.
#
# The long-normal rows carry a SECOND undefined "=~", on a different axis: they
# are qualified "R_m =~ R_s" and the figure states no tolerance on that one
# either.  This module used to read it as 0.8 <= Rm/Rs <= 1.25 and `rt_normal`
# as +/-15%; both were invented and both are gone, with no shared replacement.
#
# Unlike a bed thickness, this qualification prints NO NUMBER AT ALL - there is
# not even a printed value to match, so choosing zero tolerance would be as much
# this tool's decision as choosing 0.25.  So the tool never judges it: a row
# qualified "R_m =~ R_s" refuses until the caller declares `rm_approx_rs`, and a
# declared result is stamped as the caller's judgement.
# --------------------------------------------------------------------------
RM_APPROX_RS_QUALIFICATION = "R_m =~ R_s"

def rm_approx_rs_declaration_note(rm_over_rs: float) -> str:
    """The stamp put on `flags` and `assumptions` when the caller declares the
    qualification satisfied.  Mirrors the `assume_row_ft` stamp: it names the
    real ratio and says whose judgement the equivalence is.  `rt_normal` builds
    the identical text out of `R_m / R_s`, so one figure gives one stamp."""
    return (
        f"'{RM_APPROX_RS_QUALIFICATION}' declared satisfied by the caller "
        f"(rm_approx_rs=True) at Rm/Rs = {rm_over_rs:g}; Fig. 7-9 prints the "
        "qualification and states no tolerance on its '=~', so this "
        "equivalence is the caller's judgement and not the figure's"
    )


PROVISIONAL_NOTES = {
    "invasion_unchecked": (
        "Fig. 7-9 Part A is qualified '(invasion up to 2d)'; no invasion "
        "diameter is available to this tool, so the qualification is unchecked"
    ),
    "no_thickness_tolerance": (
        "Fig. 7-9 Part A states no tolerance on its '=~ 15 ft' / '=~ 10 ft' "
        "rows, so a point row is matched at the printed thickness only; no "
        "window is assumed"
    ),
}

#: What would turn every chart refusal in this module into an answer.
CHART_UNBLOCK = (
    "a digitized departure-curve family, keyed by electrode spacing, Rm, "
    "hole diameter, bed thickness and invasion diameter",
)


# ==========================================================================
# Helpers (not tools - plain rule-table lookups, so they return plain data)
# ==========================================================================
def _spacing_ft(curve: str, spacing_in: float | None, ao_ft: float | None) -> float:
    """AM for a normal, AO for a lateral, in feet."""
    if curve == "lateral":
        return LATERAL_AO_FT if ao_ft is None else float(ao_ft)
    if spacing_in is not None:
        return float(spacing_in) / 12.0
    return SPACING_IN[curve] / 12.0


def _on_printed_value(value: float, printed: float) -> bool:
    """Is `value` the printed number, allowing only for float representation?"""
    return math.isclose(value, printed, rel_tol=FIG_79A_POINT_ROW_REL_TOL, abs_tol=0.0)


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


def _printed_ratio_quals(rows: list[dict]) -> str:
    """The R_64/R_s qualifications of some rows, worded as the figure prints
    them - '>= 2.5' on one row and a bare '= 1.5' on another are not the same
    statement and are not merged into one."""
    seen: list[str] = []
    for row in rows:
        qual = row.get("r64_over_rs_qual")
        if qual is None:
            continue
        # printed as the figure prints it: "==" is the figure's bare "=".
        op = "=" if qual[0] == "==" else qual[0]
        text = f"'R_64/R_s {op} {qual[1]:g}'"
        if text not in seen:
            seen.append(text)
    return " and ".join(seen) if seen else "with no R_64/R_s qualification"


def _row_matches_thickness(row: dict, h_ft: float) -> bool:
    """Does a Fig. 7-9 Part A row cover this bed thickness?

    The figure prints two kinds of thickness row and they are treated
    differently, because the figure treats them differently:

    * **Bands it states** - 'e > 20 ft', '5 ft < e < 10 ft', 'Thin beds (in
      general)' - cover their whole range, because the range is the source's.
    * **Points it prints** - 'e =~ 15 ft', 'e =~ 10 ft' - match the printed
      value and nothing else. The figure never defines its '=~', so any window
      around 15 ft would be this tool's invention, not the figure's. A caller
      who judges a nearby bed to be on a row says so with `assume_row_ft`, and
      the result is stamped as their judgement.
    """
    if row.get("conductive_only"):
        return h_ft < LATERAL_THIN_BED_MAX_FT
    if row["e_ft"] is not None:
        return _on_printed_value(h_ft, row["e_ft"])
    low, high = row.get("e_low_ft"), row.get("e_high_ft")
    if low is not None:
        if row.get("e_low_exclusive") and h_ft <= low:
            return False
        if not row.get("e_low_exclusive") and h_ft < low:
            return False
    if high is not None:
        if row.get("e_high_exclusive") and h_ft >= high:
            return False
        if not row.get("e_high_exclusive") and h_ft > high:
            return False
    return True


def usability_verdict(
    curve: str,
    bed_thickness_ft: float,
    bed_contrast: str = "resistive",
    spacing_in: float | None = None,
    ao_ft: float | None = None,
) -> dict:
    """Per-curve usability verdict and expected direction of error.

    Not a tool: a lookup over `NORMAL_VERDICTS` / `LATERAL_VERDICTS` with no
    arithmetic of its own beyond the AM multiple. Written for #98
    (`rt_from_long_normal`), which needs the verdict without the `Quantity`
    wrapper. Raises on a curve it does not know rather than guessing, because
    guessing a spacing is the failure mode this tool exists to prevent.
    """
    if curve not in KNOWN_CURVES:
        raise ValueError(f"unknown curve {curve!r}; known: {KNOWN_CURVES}")
    if bed_contrast not in CONTRASTS:
        raise ValueError(f"bed_contrast must be one of {CONTRASTS}")
    spacing = _spacing_ft(curve, spacing_in, ao_ft)

    if curve == "lateral":
        if bed_thickness_ft >= LATERAL_PLATEAU_FT:
            row = LATERAL_VERDICTS[0]
        elif bed_thickness_ft >= LATERAL_BEST_RESULTS_AO_MULTIPLE * spacing:
            row = LATERAL_VERDICTS[1]
        else:
            row = LATERAL_VERDICTS[2]
        out = dict(row)
        out["ao_ft"] = spacing
        out["blind_zone_below_bed_ft"] = spacing
        out["upper_low_reading_zone_ft"] = spacing
        return out

    # Normal.  A conductive bed does not reverse: trieste#1's reversal case is
    # explicitly "bed more resistive than adjacent formations", and the
    # conductive figure (7-4) reports only a thickened, still-symmetrical
    # anomaly - "The curves are symmetrical and the apparent bed thickness is
    # greater than actual bed thickness by an amount equal to the AM spacing."
    am_multiple = bed_thickness_ft / spacing
    if bed_contrast == "conductive":
        row = next(r for r in NORMAL_VERDICTS if r["verdict"] == "depressed")
        out = dict(row)
        out.update(
            verdict="symmetrical_thickened",
            usable=True,
            error_direction="high",
            quote=(
                "The curves are symmetrical and the apparent bed thickness is "
                "greater than actual bed thickness by an amount equal to the "
                "AM spacing."
            ),
            source=TRIESTE_SHAPES,
        )
    elif am_multiple <= 1.0:  # h <= AM - see REVERSAL_BOUNDARY_NOTE
        out = dict(NORMAL_VERDICTS[-1])
    else:
        out = dict(next(r for r in NORMAL_VERDICTS if am_multiple >= r["min_am"]))
    out["am_ft"] = spacing
    out["am_multiple"] = am_multiple
    out["reversal_boundary_note"] = REVERSAL_BOUNDARY_NOTE
    return out


# ==========================================================================
# Tools
# ==========================================================================
def bed_geometry(
    curve: str,
    bed_thickness_ft: float | None,
    bed_contrast: str,
    spacing_in: float | None = None,
    ao_ft: float | None = None,
) -> Quantity | Refusal:
    """Apparent bed thickness the curve will draw, with the usability verdict.

    The always-answering half of #97. Returns feet, never a resistivity:
    * resistive bed on a normal -> `h - AM` ("the bed is logged as being one AM
      spacing thinner than it actually is", epa#2);
    * conductive bed on a normal -> `h + AM` ("the apparent bed thickness is
      greater than actual bed thickness by an amount equal to the AM spacing",
      trieste#1);
    * a lateral has no symmetric apparent thickness - its anomaly "extends
      below the bed for a distance slightly greater than the AO spacing" - so
      the tool returns the bed thickness unchanged and puts the asymmetry on
      the flags rather than faking a number.

    A reversed normal still returns a `Quantity`, flagged unusable, because the
    spurious-peak separation `h + AM` is the diagnostic that identifies the
    reversal on the log. `departure_correction` is what refuses.
    """
    guard = _guard_curve_and_thickness(curve, bed_thickness_ft)
    if guard is not None:
        return guard
    if bed_contrast not in CONTRASTS:
        raise ValueError(f"bed_contrast must be one of {CONTRASTS}")

    v = usability_verdict(curve, bed_thickness_ft, bed_contrast, spacing_in, ao_ft)
    flags: list[str] = [f"verdict={v['verdict']}", f"error_direction={v['error_direction']}"]
    if not v["usable"]:
        flags.append("reading is NOT usable for Rt: " + v["quote"])

    if curve == "lateral":
        flags.append(
            "lateral anomalies are asymmetric; the upper "
            f"{v['ao_ft']:.3f} ft (one AO) of a resistive bed reads low and the "
            f"anomaly extends slightly more than {v['ao_ft']:.3f} ft below the bed"
        )
        if v["verdict"] == "distorted":
            flags.append(
                "thin resistive bed: a spurious 'reflection' peak appears one AO "
                "below the bed, separated by a blind zone"
            )
        return Quantity(
            value=float(bed_thickness_ft),
            unit="ft",
            method="lateral bed geometry (no symmetric apparent thickness; trieste#1 Figs. 7-5/7-6)",
            source=TRIESTE_SHAPES,
            inputs={"curve": curve, "bed_thickness_ft": bed_thickness_ft,
                    "bed_contrast": bed_contrast, "ao_ft": v["ao_ft"]},
            assumptions={"rule": v["quote"], "ao_source": TRIESTE_DEVICES},
            flags=tuple(flags),
        )

    am = v["am_ft"]
    if bed_contrast == "resistive":
        apparent = bed_thickness_ft - am
        method = "apparent bed thickness = h - AM (resistive bed, normal device)"
        source = EPA_ELECTRICAL
    else:
        apparent = bed_thickness_ft + am
        method = "apparent bed thickness = h + AM (conductive bed, normal device)"
        source = TRIESTE_SHAPES

    if not v["usable"]:
        flags.append(
            "spurious peaks appear above and below the bed, separated by "
            f"h + AM = {bed_thickness_ft + am:.6f} ft "
            "('the distance between the two peaks is equal to bed thickness "
            "plus the spacing of the normal', trieste#1)"
        )
        flags.append(
            f"apparent thickness {apparent:.6f} ft is not meaningful under "
            "reversal: 'The log does not indicate the correct bed thickness' (epa#2)"
        )
    return Quantity(
        value=apparent,
        unit="ft",
        method=method,
        source=source,
        inputs={"curve": curve, "bed_thickness_ft": bed_thickness_ft,
                "bed_contrast": bed_contrast, "am_ft": am},
        assumptions={"rule": v["quote"], "spacing_source": TRIESTE_DEVICES,
                     "reversal_boundary": REVERSAL_BOUNDARY_NOTE},
        flags=tuple(flags),
    )


def departure_correction(
    curve: str,
    bed_thickness_ft: float | None,
    bed_contrast: str = "resistive",
    want: str = "verdict",
    spacing_in: float | None = None,
    ao_ft: float | None = None,
    r16_over_rm: float | None = None,
    rm_over_rs: float | None = None,
    r64_over_rs: float | None = None,
    ra_ohmm: float | None = None,
    sp_mv: float | None = None,
    oil_bearing: bool | None = None,
    ra_max_ohmm: float | None = None,
    ra_min_ohmm: float | None = None,
    rs_ohmm: float | None = None,
    rm_ohmm: float | None = None,
    hole_diameter_in: float | None = None,
    assume_row_ft: float | None = None,
    rm_approx_rs: bool | None = None,
) -> Quantity | Range | Refusal:
    """Bed-thickness and borehole correction for a vintage normal or lateral.

    `want`:
      * `"verdict"` (default) - apparent bed thickness plus the usability
        verdict, or a refusal when the curve is unusable in this bed;
      * `"rt_factor"` - the Fig. 7-9 Part A multiplier `Rt / R_apparent`, or
        `Rt` itself if `ra_ohmm` is given. Refuses off the printed rows;
      * `"borehole"` - always refuses. Chart B-2 / EPA Figure 5.

    `assume_row_ft` is the caller's override of the thickness match, and only
    that: it declares "treat my bed as the figure's named row". It accepts a
    printed point row and nothing else (15.0 or 10.0 - `ValueError` otherwise,
    because asking for a row the figure does not print is a bug, not a question
    the source declines). The resulting `Quantity` names the real thickness, the
    row applied, and that the equivalence is the caller's judgement and not the
    figure's, on both `flags` and `assumptions`.

    `rm_approx_rs` is the caller's declaration on the long-normal rows' other
    qualification, `R_m =~ R_s`. It has NO default: the figure prints the
    qualification and never says how close is close enough, so the tool cannot
    evaluate it and will not pretend to. `None` (undeclared) refuses on any row
    carrying the qualification, naming the argument and reporting the actual
    Rm/Rs ratio; `False` refuses because the caller has ruled the row out;
    `True` answers, stamped on `flags` and `assumptions` as the caller's
    judgement. `rm_over_rs` is still required alongside it - the ratio is what
    the refusal and the stamp report, not what the tool decides on.
    """
    if want not in ("verdict", "rt_factor", "borehole"):
        raise ValueError(f"want must be verdict, rt_factor or borehole; got {want!r}")
    if assume_row_ft is not None and not any(
        _on_printed_value(assume_row_ft, p) for p in FIG_79A_PRINTED_POINT_ROWS_FT
    ):
        raise ValueError(
            f"assume_row_ft={assume_row_ft!r} is not a printed Fig. 7-9 Part A "
            "point row; the figure prints point rows at "
            + " and ".join(f"{p:g} ft" for p in FIG_79A_PRINTED_POINT_ROWS_FT)
            + " only. The override names a row that exists; it does not create one"
        )

    if want == "borehole":
        return _refuse_borehole(rm_ohmm, hole_diameter_in, ra_ohmm, curve)

    guard = _guard_curve_and_thickness(curve, bed_thickness_ft)
    if guard is not None:
        return guard
    if bed_contrast not in CONTRASTS:
        raise ValueError(f"bed_contrast must be one of {CONTRASTS}")

    v = usability_verdict(curve, bed_thickness_ft, bed_contrast, spacing_in, ao_ft)

    if want == "verdict":
        if not v["usable"]:
            if curve in NORMAL_CURVES:
                return Refusal(
                    reason=(
                        f"{curve} in a {bed_thickness_ft:g} ft resistive bed at or "
                        f"below its {v['am_ft']:.4f} ft AM spacing: the curve is "
                        "REVERSED - '"
                        + v["quote"]
                        + "' No correction recovers Rt from a reading whose "
                        "contrast has the wrong sign. Spurious peaks lie "
                        f"{bed_thickness_ft + v['am_ft']:.4f} ft apart (h + AM). "
                        + REVERSAL_BOUNDARY_NOTE
                    ),
                    needed=(
                        "a shorter-spacing curve (h must exceed AM), or a "
                        "focusing-electrode log - 'These tools are much superior "
                        "to the ES devices ... for resolution of thin to "
                        "moderately thick beds' (trieste#1)",
                    ),
                    source=EPA_ELECTRICAL,
                )
            return Refusal(
                reason=(
                    f"lateral in a {bed_thickness_ft:g} ft bed, below twice AO "
                    f"({LATERAL_BEST_RESULTS_AO_MULTIPLE * v['ao_ft']:.4f} ft): '"
                    + v["quote"]
                    + "' Rt cannot be read off the curve - 'accuracy of bed Rt "
                    "cannot be expected' (trieste#1)."
                ),
                needed=(
                    "Fig. 7-9 Part B, whose Response column is an image "
                    "(img-8.jpeg) in this corpus",
                )
                + CHART_UNBLOCK
                + (
                    "or, for a thin resistive bed with homogeneous surroundings, "
                    "ra_max_ohmm / ra_min_ohmm / rs_ohmm with want='rt_factor'",
                ),
                source=TRIESTE_FIG79,
            )
        return bed_geometry(curve, bed_thickness_ft, bed_contrast, spacing_in, ao_ft)

    # want == "rt_factor"
    return _fig_79a(
        curve=curve,
        bed_thickness_ft=float(bed_thickness_ft),
        bed_contrast=bed_contrast,
        verdict=v,
        r16_over_rm=r16_over_rm,
        rm_over_rs=rm_over_rs,
        r64_over_rs=r64_over_rs,
        ra_ohmm=ra_ohmm,
        sp_mv=sp_mv,
        oil_bearing=oil_bearing,
        ra_max_ohmm=ra_max_ohmm,
        ra_min_ohmm=ra_min_ohmm,
        rs_ohmm=rs_ohmm,
        assume_row_ft=assume_row_ft,
        rm_approx_rs=rm_approx_rs,
    )


# ==========================================================================
# Fig. 7-9 Part A
# ==========================================================================
def _fig_79a(
    curve: str,
    bed_thickness_ft: float,
    bed_contrast: str,
    verdict: dict,
    r16_over_rm: float | None,
    rm_over_rs: float | None,
    r64_over_rs: float | None,
    ra_ohmm: float | None,
    sp_mv: float | None,
    oil_bearing: bool | None,
    ra_max_ohmm: float | None,
    ra_min_ohmm: float | None,
    rs_ohmm: float | None,
    assume_row_ft: float | None = None,
    rm_approx_rs: bool | None = None,
) -> Quantity | Refusal:
    """The only numeric correction factors either source supplies."""
    # The lateral thin-bed relation is the one Part A row that is not a
    # multiplier, so it is handled before the ratio gate below - the row is
    # printed under the same "R_16/R_m < 10" heading, so the gate still applies.
    if curve == "lateral" and bed_contrast == "resistive":
        return _lateral_thin_bed(
            bed_thickness_ft, r16_over_rm, ra_max_ohmm, ra_min_ohmm, rs_ohmm
        )

    if r16_over_rm is None:
        return Refusal(
            reason=(
                "Fig. 7-9 Part A applies only 'In low resistivity, when "
                "R_{16}/R_{m} < 10 (invasion up to 2d)' and that ratio was not "
                "supplied; the 16-in normal reading and the mud resistivity are "
                "what decide whether any tabulated factor applies at all"
            ),
            needed=("r16_over_rm (the 16-in normal reading divided by Rm at "
                    "formation temperature)",),
            source=TRIESTE_FIG79,
        )
    if r16_over_rm >= FIG_79A_GATE_R16_OVER_RM:
        return Refusal(
            reason=(
                f"R_16/R_m = {r16_over_rm:g} is not below "
                f"{FIG_79A_GATE_R16_OVER_RM:g}; Fig. 7-9 Part A is headed 'A. In "
                "low resistivity, when R_{16}/R_{m} < 10 (invasion up to 2d)'. "
                "The medium (10-50) and high (>50) branches end in charts, not "
                "in tabulated factors"
            ),
            needed=("Fig. 7-9 Parts B and C, which are images in this corpus",)
            + CHART_UNBLOCK,
            source=TRIESTE_FIG79,
        )

    # The thickness the row match is made on.  `assume_row_ft` moves this and
    # nothing else: every other use of the bed thickness stays the real one.
    match_thickness_ft = (
        bed_thickness_ft if assume_row_ft is None else float(assume_row_ft)
    )
    override_note = None
    if assume_row_ft is not None:
        override_note = (
            f"{assume_row_ft:g} ft row applied to a {bed_thickness_ft:g} ft bed "
            f"on the caller's declaration (assume_row_ft={assume_row_ft:g}); "
            f"Fig. 7-9 states no tolerance on its '=~ {assume_row_ft:g} ft' row, "
            "so this equivalence is the caller's judgement and not the figure's"
        )

    candidates = [
        r for r in FIG_79A_ROWS
        if r["device"] == curve and _row_matches_thickness(r, match_thickness_ft)
    ]
    if curve == "lateral":
        candidates = [r for r in candidates if bed_contrast == "conductive"]
    if not candidates:
        return Refusal(
            reason=(
                f"no Fig. 7-9 Part A row covers a {curve} in a "
                f"{bed_thickness_ft:g} ft bed. For this device the figure prints "
                f"{FIG_79A_PRINTED_THICKNESS_ROWS.get(curve, 'no thickness row')}"
                ", and it defines no tolerance on the '=~' of its point rows - "
                "so a bed that is not AT a printed thickness is on no row, and "
                "any window that put it on one would be this tool's invention "
                "rather than the figure's statement. Nothing is interpolated "
                "between rows either: the thicknesses between them are read off "
                "the departure curves. If you judge this bed to be the figure's "
                "10 ft or 15 ft case, say so with assume_row_ft=10.0 or "
                "assume_row_ft=15.0 and the answer will be returned stamped as "
                "your declaration, not the figure's"
            ),
            needed=(
                "a bed thickness on a printed row - exactly "
                + " or ".join(f"{p:g} ft" for p in FIG_79A_PRINTED_POINT_ROWS_FT)
                + ", or a band the figure states",
                "or a source that states the tolerance on Fig. 7-9 Part A's "
                "'=~ 15 ft' / '=~ 10 ft' rows, which would settle this",
                "or assume_row_ft=10.0 / assume_row_ft=15.0 to apply a named row "
                "on your own judgement",
                "Fig. 7-9's departure curves, an image in this corpus",
            )
            + CHART_UNBLOCK,
            source=TRIESTE_FIG79,
        )

    # Qualification filters, in the order the table prints them.
    row = None
    ratio_rejected: list[dict] = []
    for cand in candidates:
        if cand.get("needs_oil_and_sp"):
            if not oil_bearing:
                continue
            if sp_mv is None or not (
                SHORT_NORMAL_SP_BAND_MV[0] <= sp_mv <= SHORT_NORMAL_SP_BAND_MV[1]
            ):
                continue
        if cand["needs_rm_approx_rs"]:
            if rm_over_rs is None:
                return Refusal(
                    reason=(
                        f"the Fig. 7-9 Part A row '{cand['row']}' is qualified "
                        f"'{RM_APPROX_RS_QUALIFICATION}' and the mud-to-shoulder "
                        "resistivity ratio was not supplied. The ratio is not how "
                        "the tool decides the qualification - it cannot, the "
                        "figure states no tolerance on that '=~' - it is what the "
                        "tool reports so the caller can decide it with "
                        "rm_approx_rs"
                    ),
                    needed=("rm_over_rs (mud resistivity / surrounding-bed "
                            "resistivity, both at formation temperature)",
                            "and rm_approx_rs, the caller's declaration on the "
                            "row's 'R_m =~ R_s' qualification",),
                    source=TRIESTE_FIG79,
                )
            if rm_approx_rs is None:
                return Refusal(
                    reason=(
                        f"the Fig. 7-9 Part A row '{cand['row']}' is qualified "
                        f"'{RM_APPROX_RS_QUALIFICATION}' and the figure states NO "
                        "TOLERANCE on that '=~': it prints the qualification and "
                        "never says how close is close enough. Here Rm/Rs = "
                        f"{rm_over_rs:g}. Whether that counts as R_m =~ R_s is a "
                        "judgement about this well's mud and its shoulder beds, "
                        "which the caller is in a position to make and this tool "
                        "is not - any band it applied would be its own invention "
                        "rather than the figure's statement. Declare it with "
                        "rm_approx_rs=True and the row's published factor comes "
                        "back stamped as your judgement, not the figure's; "
                        "rm_approx_rs=False rules the row out"
                    ),
                    needed=(
                        "rm_approx_rs declared by the caller for the Rm/Rs ratio "
                        "above - True to apply the row, False to rule it out",
                        "or a source that states the tolerance on Fig. 7-9 Part "
                        "A's 'R_m =~ R_s' qualification, which would settle it",
                    )
                    + CHART_UNBLOCK,
                    source=TRIESTE_FIG79,
                )
            if rm_approx_rs is False:
                return Refusal(
                    reason=(
                        "the caller declares R_m is not approximately R_s "
                        f"(rm_approx_rs=False, at Rm/Rs = {rm_over_rs:g}) and the "
                        f"Fig. 7-9 Part A row '{cand['row']}' is qualified "
                        f"'{RM_APPROX_RS_QUALIFICATION}'. The figure states no "
                        "long-normal response for this bed without it"
                    ),
                    needed=("a bed where Rm =~ Rs, or Fig. 7-9's departure "
                            "curves for the general case",)
                    + CHART_UNBLOCK,
                    source=TRIESTE_FIG79,
                )
            if r64_over_rs is None:
                return Refusal(
                    reason=(
                        f"the Fig. 7-9 Part A rows at e = {cand['e_ft']:g} ft "
                        "branch on R_64/R_s and it was not supplied. The figure "
                        "qualifies them "
                        + _printed_ratio_quals(candidates)
                        + " and states no response outside those"
                    ),
                    needed=("r64_over_rs (the 64-in normal reading divided by "
                            "the surrounding-bed resistivity)",),
                    source=TRIESTE_FIG79,
                )
            if not _qualification_holds(cand["r64_over_rs_qual"], r64_over_rs):
                ratio_rejected.append(cand)
                continue
        row = cand
        break

    if row is None and ratio_rejected:
        return Refusal(
            reason=(
                f"R_64/R_s = {r64_over_rs:g} is on no Fig. 7-9 Part A row at "
                f"e = {ratio_rejected[0]['e_ft']:g} ft. The figure qualifies the "
                "rows there "
                + _printed_ratio_quals(ratio_rejected)
                + ", and prints nothing between those thresholds: "
                "1.5 < R_64/R_s < 2.5 is a gap in the published figure, not a "
                "near-miss on a tabulated value, so no row may be assigned to "
                "it and no branch split between them exists to invent"
            ),
            needed=(
                "R_64/R_s satisfying a printed qualification - at or above 2.5, "
                "or the row's stated 1.5 case",
                "a source that addresses 1.5 < R_64/R_s < 2.5 at this bed "
                "thickness, which would settle it",
            )
            + CHART_UNBLOCK,
            source=TRIESTE_FIG79,
        )

    if row is None:
        return Refusal(
            reason=(
                f"a Fig. 7-9 Part A row exists for a {curve} at "
                f"{bed_thickness_ft:g} ft but its qualifications are not met "
                "(oil bearing with SP between -50 and -80 mV for the short "
                f"normal; '{RM_APPROX_RS_QUALIFICATION}' for the long normal)"
            ),
            needed=("the row's stated qualifications, or Fig. 7-9's departure "
                    "curves for the general case",)
            + CHART_UNBLOCK,
            source=TRIESTE_FIG79,
        )

    factor = row["rt_over_ra"]
    assumptions = {
        "fig_7_9_row": row["row"],
        "gate": "A. In low resistivity, when R_{16}/R_{m} < 10 (invasion up to 2d)",
        "invasion": PROVISIONAL_NOTES["invasion_unchecked"],
        "thickness_row_match": PROVISIONAL_NOTES["no_thickness_tolerance"],
    }
    rm_note = None
    if row["needs_rm_approx_rs"]:
        rm_note = rm_approx_rs_declaration_note(rm_over_rs)
        assumptions["rm_approx_rs"] = rm_note
    if override_note is not None:
        assumptions["assume_row_ft"] = override_note
        assumptions["thickness_row_match"] = (
            "matched on the caller's assume_row_ft, not on the bed's own "
            "thickness: " + override_note
        )
    flags = [f"verdict={verdict['verdict']}", f"error_direction={verdict['error_direction']}"]
    if override_note is not None:
        flags.append("caller_declared_row: " + override_note)
    if rm_note is not None:
        flags.append("caller_declared_rm_approx_rs: " + rm_note)
    if row["device"] == "short_normal" and row.get("needs_oil_and_sp"):
        flags.append(
            "OCR reconcile: the table prints 'R_18' in the Short Normal row; "
            "read as R_16, the short normal being the 16-in device (trieste#0). "
            "Confirmed against the original PDF, knowledge-base/originals/"
            "12-vintage-logs/trieste-log-interpretation-ch7-resistivity.pdf "
            "p. 7-6, which prints R_16\" = R_t on this row"
        )
    if factor == 1.0:
        flags.append("the tabulated response is an identity - no correction is applied")

    inputs = {
        "curve": curve, "bed_thickness_ft": bed_thickness_ft,
        "bed_contrast": bed_contrast, "r16_over_rm": r16_over_rm,
        "rm_over_rs": rm_over_rs, "r64_over_rs": r64_over_rs,
        "sp_mv": sp_mv, "oil_bearing": oil_bearing,
        "assume_row_ft": assume_row_ft, "rm_approx_rs": rm_approx_rs,
    }
    if ra_ohmm is None:
        return Quantity(
            value=factor, unit="dimensionless",
            method="Fig. 7-9 Part A: Rt / R_apparent",
            source=TRIESTE_FIG79, inputs=inputs, assumptions=assumptions,
            flags=tuple(flags),
        )
    return Quantity(
        value=factor * ra_ohmm, unit="ohm-m",
        method=f"Fig. 7-9 Part A: Rt = {factor:g} x R_apparent",
        source=TRIESTE_FIG79,
        inputs={**inputs, "ra_ohmm": ra_ohmm},
        assumptions=assumptions, flags=tuple(flags),
    )


def _lateral_thin_bed(
    bed_thickness_ft: float,
    r16_over_rm: float | None,
    ra_max_ohmm: float | None,
    ra_min_ohmm: float | None,
    rs_ohmm: float | None,
) -> Quantity | Refusal:
    """`Rt ~ Rmax * Rs / Rmin` - returned as a LOWER BOUND on Rt.

    Fig. 7-9 Part A prints it as an approximate equality; the prose at
    trieste#1 prints the same relation as an inequality, "(Ramax/Ramin) <=
    (Rt/Rs)", which rearranges to `Rt >= Rs * Ramax / Ramin`. The two
    statements are of one relation, and the inequality is the one that says
    which way the error runs. So the value is a floor, flagged as one.
    """
    if not (5.0 < bed_thickness_ft < 10.0):
        return Refusal(
            reason=(
                f"the lateral thin-resistive-bed relation is tabulated for "
                f"'5 ft < e < 10 ft'; this bed is {bed_thickness_ft:g} ft. "
                "Above that band Rt is picked off the asymmetric lateral curve "
                "per Fig. 7-9 Part B"
            ),
            needed=("Fig. 7-9 Part B, an image (img-8.jpeg) in this corpus",)
            + CHART_UNBLOCK,
            source=TRIESTE_FIG79,
        )
    if r16_over_rm is None or r16_over_rm >= FIG_79A_GATE_R16_OVER_RM:
        return Refusal(
            reason=(
                "the row sits under Fig. 7-9's heading 'A. In low resistivity, "
                "when R_{16}/R_{m} < 10 (invasion up to 2d)'; R_16/R_m is "
                + ("not supplied" if r16_over_rm is None else f"{r16_over_rm:g}")
            ),
            needed=("r16_over_rm below 10",),
            source=TRIESTE_FIG79,
        )
    missing = [n for n, x in (("ra_max_ohmm", ra_max_ohmm),
                              ("ra_min_ohmm", ra_min_ohmm),
                              ("rs_ohmm", rs_ohmm)) if x is None]
    if missing:
        return Refusal(
            reason=(
                "'R_t =~ R_max x R_s/R_min' needs the lateral's maximum and "
                "minimum apparent readings across the bed and the surrounding-bed "
                f"resistivity; missing {', '.join(missing)}"
            ),
            needed=tuple(missing),
            source=TRIESTE_FIG79,
        )
    if ra_min_ohmm <= 0:
        raise ValueError("ra_min_ohmm must be positive")
    rt = ra_max_ohmm * rs_ohmm / ra_min_ohmm
    return Quantity(
        value=rt, unit="ohm-m",
        method="Fig. 7-9 Part A, lateral in resistive bed: Rt >= Rmax x Rs / Rmin",
        source=TRIESTE_FIG79,
        inputs={"ra_max_ohmm": ra_max_ohmm, "ra_min_ohmm": ra_min_ohmm,
                "rs_ohmm": rs_ohmm, "bed_thickness_ft": bed_thickness_ft,
                "r16_over_rm": r16_over_rm},
        assumptions={
            "qualification": "Surrounding beds homogeneous",
            "inequality": "(Ramax/Ramin) <= (Rt/Rs), trieste#1",
            "gate": "A. In low resistivity, when R_{16}/R_{m} < 10",
        },
        flags=(
            "lower_bound_on_rt: trieste#1 states the relation as "
            "'(Ramax/Ramin) <= (Rt/Rs)', so the true Rt is at least this value",
            "error_direction=low",
            "trieste#1: 'accuracy of bed Rt cannot be expected'",
            "the lateral's peak is asymmetric; a 'blind zone' follows the bed "
            "and a spurious reflection peak sits one AO below it",
        ),
    )


# ==========================================================================
# Refusals
# ==========================================================================
def _guard_curve_and_thickness(
    curve: str, bed_thickness_ft: float | None
) -> Refusal | None:
    """An unidentified curve is never corrected as if it were a known one."""
    if curve not in KNOWN_CURVES:
        return Refusal(
            reason=(
                f"curve {curve!r} has no known electrode spacing, and every rule "
                "here is a function of the spacing - a bed logs one AM thinner, "
                "reverses below one AM, and a lateral is blind for one AO below "
                "the bed. Correcting an unidentified curve as if it were a known "
                "one would apply the wrong spacing silently"
            ),
            needed=(
                f"an identified curve from es_curve_identify, one of {KNOWN_CURVES}",
                "or an explicit spacing_in (normal) / ao_ft (lateral)",
            ),
            source=TRIESTE_DEVICES,
        )
    if bed_thickness_ft is None:
        return Refusal(
            reason=(
                "bed thickness was not supplied. Every departure rule in both "
                "sources is stated in bed thickness relative to the spacing "
                "('the bed is logged as being one AM spacing thinner'; 'the bed "
                "thickness is equal to or less than the AM spacing ... The curve "
                "reverses'), so without it there is no verdict to give"
            ),
            needed=("bed_thickness_ft, from bed boundaries picked on the log",),
            source=EPA_ELECTRICAL,
        )
    if bed_thickness_ft <= 0:
        raise ValueError("bed_thickness_ft must be positive")
    return None


def _refuse_borehole(
    rm_ohmm: float | None,
    hole_diameter_in: float | None,
    ra_ohmm: float | None,
    curve: str,
) -> Refusal:
    """Borehole correction is a chart in both sources. It always refuses.

    It refuses *with* the inputs present, not for want of them - that is the
    point. epa#2 prints a complete worked example off Figure 5 (Ra = 60 ohm-m,
    Rm = 0.5 ohm-m, 9-in hole -> corrected 97.5 ohm-m) and the tool still will
    not return 97.5, because the step that produced it, 60/0.5 = 120 on the
    x-axis mapping to 195, is a curve on a chart this corpus holds only as an
    image.
    """
    missing = [n for n, x in (("rm_ohmm", rm_ohmm),
                              ("hole_diameter_in", hole_diameter_in),
                              ("ra_ohmm", ra_ohmm)) if x is None]
    supplied = "; ".join(
        f"{n}={x:g}" for n, x in (("ra_ohmm", ra_ohmm), ("rm_ohmm", rm_ohmm),
                                  ("hole_diameter_in", hole_diameter_in))
        if x is not None
    ) or "none"
    return Refusal(
        reason=(
            "borehole correction is chart-only in this corpus and cannot be "
            "computed. trieste#2: 'When R_16/R_m > 50, these values must be "
            "corrected for the borehole: Chart B-2.' epa#2: 'Charts for making "
            "these corrections are available in old logging manuals. Figure 5 is "
            "an example of one of these charts that is used to correct 40-cm "
            "(16-in) normal curves for borehole diameter and mud resistivity.' "
            "Both figures are images here, with no data behind them. epa#2's own "
            "worked point - 60 ohm-m apparent, Rm 0.5, 9-in hole, corrected to "
            "97.5 - turns on reading 120 off the x-axis as 195, which no equation "
            "in either source supplies. "
            f"(curve={curve}; inputs supplied: {supplied}"
            + (f"; still missing: {', '.join(missing)}" if missing else "")
            + "). Returning a number here would be inventing the chart"
        ),
        needed=CHART_UNBLOCK
        + ("specifically Schlumberger Chart B-2 and the Fig. 7-9 departure "
           "curves, digitized",),
        source=TRIESTE_FIG79,
    )


# --------------------------------------------------------------------------
# One source of truth for Fig. 7-9 part A.
#
# This module and `rt_normal` each transcribed the same figure independently and
# agreed with each other while both being wrong -- they were reading one
# corrupted conversion, which is not corroboration. The values are now taken
# from the original PDF, and this check makes a future divergence an ImportError
# instead of a silent 33% error in Rt.
#
# The two tables keep different shapes on purpose (this one carries every device
# and thickness band; `rt_normal`'s carries the long-normal rows it evaluates),
# so they are reconciled on the three things that must agree, in table order:
# the thickness each row applies at, the R_64/R_s qualification as printed, and
# the multiplier taking the apparent long-normal reading to Rt.
#
# The thickness and the qualification are in the guard because leaving them out
# is what let the divergence happen: the multipliers agreed while one module
# matched a 12.6 ft bed to the 15 ft row (+/-2.5 ft) and the other refused it
# (+/-15%), so one figure gave two answers. Both windows are gone, and the guard
# now makes a future re-invention an ImportError.
# --------------------------------------------------------------------------
def _fig_79a_long_normal_signature() -> list[tuple]:
    """(thickness rule, R_64/R_s qualification, does the row carry
    'R_m =~ R_s'?, Rt multiplier) per long-normal row."""
    out = []
    for row in FIG_79A_ROWS:
        if row["device"] != "long_normal":
            continue
        if row["e_ft"] is not None:
            thickness = ("==", row["e_ft"])
        elif row.get("e_low_ft") is not None and row.get("e_high_ft") is None:
            thickness = (">" if row.get("e_low_exclusive") else ">=", row["e_low_ft"])
        else:  # pragma: no cover - no such long-normal row exists in the figure
            thickness = ("band", row.get("e_low_ft"), row.get("e_high_ft"))
        out.append((thickness, row["r64_over_rs_qual"],
                    bool(row["needs_rm_approx_rs"]), row["rt_over_ra"]))
    return out


def _reconcile_fig_79a_with_rt_normal() -> None:
    from .rt_normal import FIG_7_9_PART_A_LONG_NORMAL as _canonical

    here = _fig_79a_long_normal_signature()
    there = []
    for row in _canonical:
        if row["thickness_ft"] is not None:
            thickness = ("==", row["thickness_ft"])
        else:
            thickness = (">", row["thickness_min_ft"])
        there.append((thickness, row["r64_rs_qual"],
                      bool(row["requires_rm_approx_rs"]), row["rt_multiplier"]))
    if here != there:
        raise ImportError(
            "Fig. 7-9 part A disagrees between departure.py and rt_normal.py: "
            f"{here} vs {there}. Both describe one published table, so one of "
            "them has drifted -- in thickness, in the R_64/R_s qualification, in "
            "whether the row carries 'R_m =~ R_s', or in the multiplier, any of "
            "which makes one figure give two answers. "
            "Settle it against knowledge-base/originals/12-vintage-logs/"
            "trieste-log-interpretation-ch7-resistivity.pdf p. 7-6 -- not "
            "against the markdown conversion, which is what caused the last "
            "divergence. If the disagreement is a tolerance on either of the "
            "figure's undefined '=~' glyphs -- the bed thickness or "
            "'R_m =~ R_s' -- there is none: the figure states neither, and the "
            "fix is assume_row_ft and rm_approx_rs, not a new constant."
        )


_reconcile_fig_79a_with_rt_normal()
