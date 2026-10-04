"""#94 salinity_from_rw — Rw -> NaCl concentration, for QC of a claimed Rw.

MERGE NOTE FOR THE COORDINATOR
------------------------------
Merge into `tools/petrophysics.py`, *below* `resistivity_at_temperature`, which
this module calls and must not duplicate. If it lands anywhere else, add
`from ..petrophysics import resistivity_at_temperature` at the top.

WHY THIS TOOL ONLY REFUSES
--------------------------
The concentration readout is chart-only. `11-rw-and-crossplots/aapg-water-
resistivity-determination#0` never states a concentration in any unit; its nine
recovered equations are the SP/SSP relation, the Archie reductions and the
resistivity-ratio set, and none carries a concentration term. The conversion is
performed on Schlumberger Chart **Gen-9** (Western Atlas 1-5; = Asquith Fig 1.11),
which is an un-OCR'd image in this corpus. `aapg-formation-water-density` states
the procedure explicitly and graphically: "At the intersection of formation
temperature (from Y-axis) and Rw (from X-axis), find the NaCl concentration (in
ppm) by reading diagonal line labels and interpolating." No closed-form
ppm(Rw, T) fit exists anywhere in the knowledge base (checked exhaustively). The
one salinity-bearing correlation in the reference handbook is Meehan's water
*viscosity*, Eq. 2-128 — a different dependent variable and the adjacent-equation
trap here. It is declined.

THE UNITS-AND-MEANING TRAP THIS TOOL IS BUILT AROUND
----------------------------------------------------
Three quantities live next to each other and two of them share a unit:

    Rw        formation-water resistivity            ohm-m
    Rwe       *equivalent* resistivity, a proxy for  ohm-m   <- not Rw
              chemical activity in the SP relation
    salinity  NaCl-equivalent concentration          ppm     <- not a resistivity

The catalog pin for this tool points at Asquith Table 2.1, where `Rwe` appears —
an implementer skimming it will read `Rwe` as a salinity, which is the single
failure this module exists to make impossible. Hence: units in every argument
name, and `rw_kind` is **required with no default**, so a caller cannot pass an
Rwe by omission. The reverse swap (a ppm number pasted into the resistivity slot)
is caught by magnitude.

WHAT IS ACTUALLY COMPUTED
-------------------------
The temperature normalisation, and only that. Gen-9's iso-salinity lines are the
Arps family — Mosul: "(Fig.2), which is based upon Arp's equation. This chart
relates between the resistivity, NaCl salinity, and temperature" — so every
(Rw, T) pair on one Arps trajectory reads the same salinity. Normalising Rw to
the temperature the operator will enter the chart at is therefore exact and
lossless, and the refusal carries the resulting entry pair so the computable half
of the work is not thrown away.
"""
from __future__ import annotations

from ..result import Quantity, Range, Refusal
# Arps temperature conversion. Imported rather than redefined: this module
# and `rw_tds` are the two halves of one chart-only transform and must not
# drift on the constant. See the package docstring on the duplicate in
# `petrophysics.py`.
from .rw_tds import resistivity_at_temperature

# --- provenance ------------------------------------------------------------

SALINITY_FROM_RW_SOURCE = (
    "11-rw-and-crossplots/aapg-water-resistivity-determination#0"
)
#: Where the Rwe -> Rw closed form lives, for the refusal that points at it.
ASQUITH_TABLE_2_1 = (
    "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#13 "
    "(Table 2.1, p. 23, after Western Atlas Logging Services 1985)"
)
#: Arps, Eq. 1.10 p. 9 — introduced there as the close approximation to Fig 1.11,
#: captioned "(Schlumberger, 1998, Figure Gen-9.)". Same chart as Chart 2 above.
ASQUITH_ARPS = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#9"

#: The chart that does the job the corpus will not do in closed form.
GEN9_CHART = (
    "Schlumberger Chart Gen-9 (Western Atlas 1-5; = Asquith Fig. 1.11)"
)

# --- bounds ----------------------------------------------------------------
# Both are PROVISIONAL house bounds: the corpus prints no axis limits for Gen-9
# anywhere. Stated as such in the refusal text so an operator can tell a sourced
# limit from ours. See specs/94-salinity_from_rw.md, Open questions 1.

#: Arps denominator singularity, degF. Asquith Eq. 1.10 / Mosul Eq. 9.
ARPS_X_DEGF = 6.77

#: Brackets the corpus's published worked examples (70-250 degF) with margin.
TEMPERATURE_MIN_DEGF = 32.0
TEMPERATURE_MAX_DEGF = 400.0

#: Three orders of magnitude above every Rw printed in the corpus (0.018, 0.04,
#: 0.096, 0.103, 0.26, 0.284 ohm-m). A value at or above this is characteristic
#: of a concentration in ppm pasted into the resistivity argument.
IMPLAUSIBLE_RW_OHM_M = 1000.0

RW_KINDS = ("rw", "rwe")

# --- refusal texts, as constants so tests assert strings and not paraphrase ---

REASON_RWE_IS_NOT_RW = (
    "Rwe is an equivalent resistivity (ohm-m), a proxy for chemical activity in "
    "the SP relation SSP = -K log(Rmfe/Rwe). It is not a formation-water "
    "resistivity and it is not a concentration. Gen-9 is entered with Rw. "
    "Convert Rwe to Rw first, then call again with rw_kind='rw'."
)
NEEDED_RWE_IS_NOT_RW = (
    "Rw at formation temperature (ohm-m), converted from Rwe",
    "the Rwe->Rw step is chart-only in the cited source (Schlumberger SP-2 / "
    "Western Atlas 2-3); a closed form for it is printed at " + ASQUITH_TABLE_2_1,
)

REASON_LOOKS_LIKE_CONCENTRATION = (
    "is not a plausible formation-water resistivity in ohm-m: it is at or above "
    "1000 ohm-m, three orders of magnitude above every Rw printed in the corpus "
    "(0.018 to 0.284 ohm-m), and is characteristic of a concentration in ppm "
    "passed into the resistivity argument. If you hold a concentration and want "
    "a resistivity, the tool is rw_from_tds, not salinity_from_rw. PROVISIONAL: "
    "the corpus states no formation-water resistivity range, so this bound is "
    "ours, not the source's."
)
NEEDED_LOOKS_LIKE_CONCENTRATION = (
    "a formation-water resistivity in ohm-m, not a concentration in ppm",
    "if the input really is a concentration, call rw_from_tds (#92) instead",
)

REASON_TEMPERATURE_OUT_OF_RANGE = (
    "outside 32-400 degF, the band this tool will attempt. PROVISIONAL: the "
    "corpus does not print Gen-9's axis limits; this band brackets the published "
    "worked examples (70-250 degF) with margin. Widen it only against a "
    "digitised chart that states its own limits."
)
NEEDED_TEMPERATURE_OUT_OF_RANGE = (
    "a formation temperature within the chart's stated range",
    "or a digitised Gen-9 that states its own axis limits",
)

REASON_CHART_ONLY = (
    "Rw -> NaCl concentration is chart-only. The cited source performs it on "
    + GEN9_CHART
    + ", which is an un-digitised image in this corpus, and states the procedure "
    "graphically: read the concentration off the interpolated diagonal labels at "
    "the intersection of temperature and Rw. There is no closed form for "
    "concentration from Rw at temperature anywhere in the knowledge base, and "
    "none will be substituted from an adjacent equation."
)
NEEDED_CHART_ONLY = (
    "a digitised Gen-9 grid (Rw / temperature / NaCl concentration), or a "
    "published closed-form ppm(Rw, T) fit added to the corpus",
    "until then, read the concentration off Gen-9 by hand at the Rw and "
    "temperature stated in this reason",
    "note that Gen-9 reports NaCl-EQUIVALENT concentration: a sulfate- or "
    "bicarbonate-heavy water must pass through nacl_equivalent (#91) first, per "
    "the source's own assumption that 'all salts in solution in the fluids are "
    "NaCl or equivalent'",
)


def salinity_from_rw(
    rw_ohm_m: float,
    t_degf: float,
    rw_kind: str,
    t_chart_entry_degf: float | None = None,
) -> Refusal:
    """NaCl-equivalent concentration implied by a formation-water resistivity.

    Always returns a `Refusal`: the transform is chart-only (Gen-9). The refusal
    carries the Arps-normalised (Rw, T) pair to enter the chart with, which is
    the part of the job the corpus does support.

    `rw_kind` has no default on purpose. Rwe and Rw are both in ohm-m and only
    one of them can be used here, so the caller declares which it holds rather
    than finding out downstream.

    Args:
        rw_ohm_m: formation-water resistivity at `t_degf`, ohm-m.
        t_degf: temperature at which `rw_ohm_m` was measured or reported, degF.
        rw_kind: "rw" or "rwe". Required.
        t_chart_entry_degf: optional temperature to normalise Rw to before
            entering Gen-9, degF (typically formation temperature). Defaults to
            `t_degf`, i.e. no normalisation.

    Raises:
        ValueError: on impossible arguments — a non-positive resistivity, a
            temperature at or below the Arps singularity, or an undeclared
            `rw_kind`. These are programmer errors, not refusals.
    """
    # 1-3: impossible arguments. Exceptions, never refusals.
    if rw_ohm_m <= 0:
        raise ValueError(
            f"resistivity must be positive; got rw_ohm_m={rw_ohm_m!r} ohm-m"
        )
    if rw_kind not in RW_KINDS:
        raise ValueError(
            f"rw_kind must be one of {RW_KINDS}; got {rw_kind!r}. It is required "
            "because Rw and Rwe share the unit ohm-m and only Rw is usable here."
        )
    t_entry = t_degf if t_chart_entry_degf is None else t_chart_entry_degf
    for name, t in (("t_degf", t_degf), ("t_chart_entry_degf", t_entry)):
        if t <= -ARPS_X_DEGF:
            raise ValueError(
                f"{name}={t!r} degF is at or below the Arps singularity "
                f"(-{ARPS_X_DEGF} degF); the temperature correction is undefined "
                "there"
            )

    # 4: the refusal this tool exists for. An Rwe is not an Rw and is not a
    #    salinity, and the discredited catalog pin invites exactly that swap.
    if rw_kind == "rwe":
        return Refusal(
            reason=f"{REASON_RWE_IS_NOT_RW} (given Rwe = {rw_ohm_m:.6g} ohm-m at "
            f"{t_degf:.6g} degF)",
            needed=NEEDED_RWE_IS_NOT_RW,
            source=SALINITY_FROM_RW_SOURCE,
        )

    # 5: the same swap in the other direction — a ppm number in the ohm-m slot.
    if rw_ohm_m >= IMPLAUSIBLE_RW_OHM_M:
        return Refusal(
            reason=f"rw_ohm_m = {rw_ohm_m:.6g} {REASON_LOOKS_LIKE_CONCENTRATION}",
            needed=NEEDED_LOOKS_LIKE_CONCENTRATION,
            source=SALINITY_FROM_RW_SOURCE,
        )

    # 6: outside the band we will attempt. Marked PROVISIONAL in the text
    #    because the corpus prints no axis limits for Gen-9.
    for name, t in (("t_degf", t_degf), ("t_chart_entry_degf", t_entry)):
        if not (TEMPERATURE_MIN_DEGF <= t <= TEMPERATURE_MAX_DEGF):
            return Refusal(
                reason=f"{name} = {t:.6g} degF is "
                f"{REASON_TEMPERATURE_OUT_OF_RANGE}",
                needed=NEEDED_TEMPERATURE_OUT_OF_RANGE,
                source=SALINITY_FROM_RW_SOURCE,
            )

    # 7: terminal. Normalise to the chart-entry temperature (Arps, exact along
    #    Gen-9's iso-salinity lines) and hand the operator the entry pair.
    #    `resistivity_at_temperature` is the existing group-D implementation of
    #    Asquith Eq. 1.10; it is called, not reimplemented.
    rw_entry = (
        rw_ohm_m
        if t_entry == t_degf
        else resistivity_at_temperature(  # noqa: F821  (same module after merge)
            rw_ohm_m, t_degf, t_entry, units="degF"
        ).value
    )
    normalised = ""
    if t_entry != t_degf:
        normalised = (
            f" Rw was normalised from {rw_ohm_m:.6g} ohm-m at {t_degf:.6g} degF "
            f"by Arps R2 = R1(T1+{ARPS_X_DEGF})/(T2+{ARPS_X_DEGF}) [{ASQUITH_ARPS}], "
            "which is exact along Gen-9's iso-salinity lines."
        )
    return Refusal(
        reason=f"{REASON_CHART_ONLY}{normalised} "
        f"Enter Gen-9 at Rw = {rw_entry:.6g} ohm-m, T = {t_entry:.6g} degF.",
        needed=NEEDED_CHART_ONLY,
        source=SALINITY_FROM_RW_SOURCE,
    )
