"""Group D, tools #33 `rw_from_sp` and #34 `rw_pickett` - formation water
resistivity, the input `archie_sw` (#35) refuses to work without.

Specs: `specs/33-rw_from_sp.md`, `specs/34-rw_pickett.md`.

--- the decisions worth explaining ------------------------------------------

**Rwe is not Rw, and a*Rw is not Rw.** Both tools produce, as their natural
product, something one step short of Rw: the SP procedure yields an *equivalent*
resistivity Rwe (a proxy linearly related to chemical activity), and the Pickett
intercept yields the product a*Rw. Handing either onward as Rw is a silent error
that lands in a saturation, so neither is ever returned in an Rw slot. Every
resistivity `Quantity` here carries `assumptions["quantity_kind"]`, one of
`"Rwe"`, `"a*Rw"` or `"Rw"`, and `rw_provenance()` - the only supported way to
build the `rw_source` string `archie_sw` demands - raises `TypeError` on anything
that is not `"Rw"`. Confusing them is programmer error, so it is an exception
rather than a refusal. `tool-verification.md:63` records the mirror-image mistake
already made in this corpus, where Rwe was pinned as the source for a *salinity*.

**Rw is meaningless without its temperature.** Every resistivity returned carries
`assumptions["stated_at_degf"]`, and the only path between temperatures is
`petrophysics.resistivity_at_temperature` (Arps, X = 6.77 degF / 21.0 degC). That
function is called, never restated: Asquith Table 2.1's own row 2 prints exactly
it, `Rmf = Rmfsurf(Tsurf + 6.77)/(Tf + 6.77)`.

**Two of the three SP charts have closed forms; the third does not.** Asquith
Figures 2.3, 2.4 and 2.5 are images. Table 2.1 (`asquith#13`, p. 23) supplies the
algebra for 2.4 (which is Eq. 2.2 rearranged) and for 2.5 (Bateman-Konen), but
*not* for 2.3, the bed-thickness correction. So `rw_from_sp` computes the last
two steps and refuses the first one: below the sourced 20-ft full-development
thickness it demands a chart-read correction factor, and it names the bed
thickness and the Ri/Rm chart entry in the refusal so the caller can enter the
chart without going back to the log.

**Table 2.1's Rwe->Rw exponent is OCR-corrupted, and the source's own worked
examples settle it.** The recovered text prints `10^((1/log(BHT/19.9))^(-2))`
where the equation needs `10^(1/log10(T/19.9) - 2)` - a minus sign promoted to a
superscript. The corrupted form is out by a factor of six. See
`_CORRUPT_BATEMAN_KONEN_NUM_EXPONENT` below, which pins it so it cannot come
back.

**K is 61, not 60.** Asquith Eq. 2.3 prints `K = 0.133*Tf + 60`; Asquith's own
Table 2.1 and Chapter 10 example, and the AAPG page, all print 61. Three to one,
two of them inside the same book. 61 is the default, `k_form="60"` selects the
other, and both K values travel on every result.

**No R-squared, ever.** The Pickett 100% Sw line is a lower envelope placed by
judgment (`seg-wiki#0`: "the most 'southwest' edge of the data points"), not a
regression through the whole cloud - a regression through a mixed cloud includes
hydrocarbon-bearing points and biases Rw high. `rw_pickett` therefore requires
the caller to declare which points are wet, and reports the wet-point set it used
plus the per-point spread of a*Rw, which is an interpretable disagreement rather
than a fit statistic the literature never defines.
"""
from __future__ import annotations

import math

from dataclasses import dataclass
from typing import Any, Sequence

from .petrophysics import resistivity_at_temperature
from .result import Quantity, Range, Refusal

# --- corpus anchors -----------------------------------------------------------

ASQUITH_SP = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#14"
ASQUITH_TABLE_21 = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#13"
AAPG_RW_SP = "11-rw-and-crossplots/aapg-water-resistivity-determination#0"
KGS_PICKETT = "11-rw-and-crossplots/kgs-pickett-and-hingle-plots#1"
SEG_PICKETT = "11-rw-and-crossplots/seg-wiki-pickett-plot#0"
AAPG_PICKETT = "11-rw-and-crossplots/aapg-pickett-plot-construction#0"

# =============================================================================
# #33  rw_from_sp
# =============================================================================

# --- the SP coefficient K -----------------------------------------------------
#
# SSP = -K log(Rmf/Rwe). The corpus prints two intercepts for K and one slope.
# RECONCILE - RESOLVED in favour of 61 (specs/33-rw_from_sp.md, "Two defects"):
# Asquith Eq. 2.3 (asquith#14, p. 26) is the lone "60"; Asquith Table 2.1
# (asquith#13, p. 23), Asquith ch. 10 (K = 61 + 0.133*130 = 78.3) and the AAPG
# page (aapg#0, p. 4) all print 61. Both forms stay available and both K values
# are reported, because nothing in the corpus declares either a typo.

SP_K_FORMS: dict[str, dict[str, Any]] = {
    "61": {
        "intercept": 61.0,
        "slope": 0.133,
        "label": "K = 61 + 0.133*Tf (Asquith Table 2.1; AAPG)",
        "source": ASQUITH_TABLE_21,
    },
    "60": {
        "intercept": 60.0,
        "slope": 0.133,
        "label": "K = (0.133*Tf) + 60 (Asquith Eq. 2.3)",
        "source": ASQUITH_SP,
    },
}
SP_K_DEFAULT_FORM = "61"

# The degC form, 65 + 0.24*T(degC), is printed at aapg#0 p. 4. It is not offered:
# every other temperature in this module is degF (the Arps constant 6.77 is
# degF-bound, and Table 2.1 is captioned "for temperatures in degF"), and mixing
# unit systems inside one procedure is the exact failure the unit-bound argument
# names elsewhere in this package exist to prevent.

# --- Bateman-Konen, the closed form of Asquith Figure 2.5 ---------------------
#
# Asquith Table 2.1, asquith#13, p. 23, "Convert Rwe to Rw (this value is at
# formation temperature)". Constants named rather than inlined:
#
#   Rw = (Rwe + 0.131 * 10^(1/log10(T/19.9) - 2))
#        / (-0.5 * Rwe + 10^(0.0426/log10(T/50.8)))

BATEMAN_KONEN: dict[str, float] = {
    "num_coeff": 0.131,
    "num_temp_divisor": 19.9,
    "num_exp_offset": 2.0,
    "den_rwe_coeff": -0.5,
    "den_exp_coeff": 0.0426,
    "den_temp_divisor": 50.8,
}

# PINNED DEFECT. The OCR of Table 2.1 renders the numerator exponent as
#
#     10^( (1/log(BHT/19.9))^(-2) )
#
# i.e. the "- 2" became a superscript. Against the source's own worked examples
# (Rwe 0.096 at 130 degF -> Rw 0.10, asquith#14 p. 27; Rwe 0.103 at 140 degF ->
# Rw 0.103, aapg#0 p. 5) the corrupt form returns 0.572716 and 0.657009 - out by
# a factor of six - while the form implemented below returns 0.0964981 and
# 0.1025311. Kept here as a named string, pinnable by a test, in the same spirit
# as the corrupt dogleg equation in tests/test_layer1.py.
_CORRUPT_BATEMAN_KONEN_NUM_EXPONENT = "10**((1/log10(T/19.9))**-2)  # WRONG: 6x high"

# The conversion is singular where log10(T/50.8) = 0 and explodes just above it.
# 50.8 degF is arithmetic; the 60 degF floor is a PROVISIONAL guard, not a
# published limit - the corpus never states Figure 2.5's temperature range
# (specs/33-rw_from_sp.md, open question 2).
RWE_RW_SINGULAR_DEGF = 50.8
RWE_RW_MIN_TEMP_DEGF = 60.0

# --- bed thickness ------------------------------------------------------------
#
# SOURCED. aapg#0, p. 4: "If the bed was too thin for the SP to develop fully
# (beds thinner than 20 ft), the appropriate correction is applied from the
# charts." At or above this, SP is taken as SSP and the factor is 1.0 - flagged
# every time, because the AAPG example still read a 1.07 factor for a 24-ft bed.
SSP_FULL_DEVELOPMENT_FT = 20.0

# PROVISIONAL house rule, flag only, changes no value: below this the SP
# deflection is small enough that the baseline pick dominates the answer.
SP_NEAR_ZERO_MV = 5.0

# --- mud systems --------------------------------------------------------------
#
# asquith#14, p. 25: "the SP log can used only with conductive (i.e., saltwater
# base or freshwater base) drilling muds. This log does not work with oil-base
# muds or in air-filled holes." aapg#0, p. 5 repeats it for oil-based mud.

MUD_BASES: dict[str, dict[str, Any]] = {
    "water": {"conductive": True, "label": "water-base (fresh or saltwater) mud"},
    "oil": {"conductive": False, "label": "oil-base mud"},
    "air": {"conductive": False, "label": "air-filled / gas-filled hole"},
}

# Tokens that contradict a declared water base if they appear in the heading's
# raw mud description. Fail closed: a heading that says INVERT while the caller
# says water is a disagreement, not a default.
NONCONDUCTIVE_MUD_TOKENS: dict[str, str] = {
    "oil-base": "oil", "oil base": "oil", "oilbase": "oil", "obm": "oil",
    "invert": "oil", "diesel": "oil", "synthetic": "oil",
    "air": "air", "mist": "air", "nitrogen": "air",
}


@dataclass(frozen=True)
class SpWaterResistivity:
    """What the SP procedure yields. `rwe` and `rw` are deliberately separate."""

    sp_deflection_mv: Quantity
    ssp_mv: Quantity
    rm_at_tf: Quantity
    rmf_at_tf: Quantity
    ri_over_rm: Quantity
    k: Quantity
    rwe: Quantity
    rw: Quantity
    temperature_degf: float
    flags: tuple[str, ...] = ()

    def __repr__(self) -> str:  # keeps test failures readable
        return (f"SpWaterResistivity(Rwe={self.rwe.value:.6g}, Rw={self.rw.value:.6g}"
                f" ohm-m at {self.temperature_degf:g} degF)")


def _k_coefficient(formation_temp_degf: float,
                   k_form: str) -> tuple[float, dict[str, Any]]:
    try:
        spec = SP_K_FORMS[k_form]
    except KeyError:
        raise ValueError(
            f"unknown k_form {k_form!r}; known: {sorted(SP_K_FORMS)}") from None
    return spec["intercept"] + spec["slope"] * formation_temp_degf, spec


def _mud_conflict(mud_type_text: str, mud_base: str) -> tuple[str, str] | None:
    """Return (token, implied base) where the heading contradicts the declaration."""
    text = str(mud_type_text).lower()
    for token, implied in NONCONDUCTIVE_MUD_TOKENS.items():
        if token in text and implied != mud_base:
            return token, implied
    return None


def rwe_to_rw(rwe_ohmm: float, temperature_degf: float):
    """Rwe -> Rw at formation temperature. Asquith Table 2.1, `asquith#13` p. 23.

    The closed form of Figure 2.5, which corrects "for average deviation from
    sodium chloride solutions, and for the influence of formation temperature"
    (asquith#13, p. 23). Public because it is the step most easily skipped, and
    because pinning it alone against the two published worked examples is the
    cleanest test of the OCR correction described in the module docstring.
    """
    if rwe_ohmm <= 0:
        raise ValueError("Rwe must be positive")
    if temperature_degf <= RWE_RW_MIN_TEMP_DEGF:
        return Refusal(
            reason=(f"the Table 2.1 Rwe-to-Rw conversion is singular at "
                    f"T = {RWE_RW_SINGULAR_DEGF} degF and is not usable at "
                    f"{temperature_degf:g} degF; the corpus never publishes the "
                    f"valid range of Figure 2.5, so {RWE_RW_MIN_TEMP_DEGF:g} degF is "
                    f"a provisional floor. If this temperature is in Celsius, "
                    f"convert it: every temperature in this module is degF"),
            needed=("formation temperature in degF, above the conversion's floor",),
            source=ASQUITH_TABLE_21,
        )
    bk = BATEMAN_KONEN
    num_exp = (1.0 / math.log10(temperature_degf / bk["num_temp_divisor"])
               - bk["num_exp_offset"])
    den_exp = bk["den_exp_coeff"] / math.log10(temperature_degf / bk["den_temp_divisor"])
    numerator = rwe_ohmm + bk["num_coeff"] * 10.0 ** num_exp
    denominator = bk["den_rwe_coeff"] * rwe_ohmm + 10.0 ** den_exp
    if denominator <= 0:
        return Refusal(
            reason=(f"the Rwe-to-Rw conversion is undefined for Rwe = {rwe_ohmm:g} "
                    f"ohm-m at {temperature_degf:g} degF: its denominator is "
                    f"{denominator:g}. This happens only for very fresh waters, "
                    f"beyond the range Figure 2.5 covers"),
            needed=("an Rwe inside the range of Asquith Figure 2.5",),
            source=ASQUITH_TABLE_21,
        )
    return Quantity(
        numerator / denominator, "ohm-m",
        "Rwe to Rw, Bateman-Konen closed form of Asquith Fig. 2.5 (Table 2.1)",
        ASQUITH_TABLE_21,
        inputs={"Rwe": rwe_ohmm, "Tf_degF": temperature_degf},
        assumptions={"quantity_kind": "Rw", "stated_at_degf": temperature_degf,
                     "constants": dict(bk),
                     "reconcile": ("numerator exponent is 1/log10(T/19.9) - 2; the "
                                   "OCR of Table 2.1 prints it as a ^-2 superscript, "
                                   "6x high against both published examples")},
    )


def rw_from_sp(
    sp_mv: float,
    shale_baseline_mv: float,
    *,
    bed_thickness_ft: float,
    ri_ohmm: float,
    rm_ohmm: float,
    rm_temp_degf: float,
    rmf_ohmm: float,
    rmf_temp_degf: float,
    formation_temp_degf: float,
    mud_base: str,
    mud_type_text: str = "",
    sp_correction_factor: float | None = None,
    ri_curve: str = "",
    hydrocarbon_bearing: bool = False,
    shaly: bool = False,
    k_form: str = SP_K_DEFAULT_FORM,
    report_at_degf: float | None = None,
) -> SpWaterResistivity | Refusal:
    """Formation water resistivity from an SP deflection. Asquith ch. 2.

    The published four-step procedure (`asquith#13`, p. 23): correct Rm and Rmf
    to formation temperature; correct SP to SSP for bed thickness; read Rwe from
    SSP; convert Rwe to Rw. Steps 1, 3 and 4 have closed forms in Table 2.1 and
    are computed here. Step 2's chart (Figure 2.3) is an image with no formula
    anywhere in the corpus, so its factor is either supplied by the caller or
    justified by the sourced 20-ft full-development thickness - otherwise this
    refuses.

    Returns `Rwe` and `Rw` as separate fields. `Rwe` is an equivalent
    resistivity: not a water resistivity, and not a salinity.
    """
    # --- programmer error: impossible arguments -------------------------------
    for name, value in (("ri_ohmm", ri_ohmm), ("rm_ohmm", rm_ohmm),
                        ("rmf_ohmm", rmf_ohmm)):
        if value <= 0:
            raise ValueError(f"{name} must be positive; got {value!r}")
    if bed_thickness_ft <= 0:
        raise ValueError(
            f"bed_thickness_ft must be positive; got {bed_thickness_ft!r}")
    for name, value in (("rm_temp_degf", rm_temp_degf),
                        ("rmf_temp_degf", rmf_temp_degf),
                        ("formation_temp_degf", formation_temp_degf)):
        if value <= 0:
            raise ValueError(
                f"{name} must be a positive Fahrenheit temperature; got {value!r}")
    if sp_correction_factor is not None and sp_correction_factor < 1.0:
        raise ValueError(
            "an SP bed-thickness correction magnifies SP toward SSP, so the factor "
            f"is >= 1.0; got {sp_correction_factor!r} (a misread of Figure 2.3)")

    # --- refusal: the SP does not work here at all ----------------------------
    base = str(mud_base).strip().lower()
    if base not in MUD_BASES:
        return Refusal(
            reason=(f"mud base {mud_base!r} is not recognised, and the SP is valid "
                    f"only in a conductive borehole fluid, so this fails closed "
                    f"rather than assuming water-base mud"),
            needed=(f"mud_base, one of {sorted(MUD_BASES)}",),
            source=ASQUITH_SP,
        )
    if not MUD_BASES[base]["conductive"]:
        return Refusal(
            reason=(f"the SP does not work in {MUD_BASES[base]['label']}: \"This log "
                    f"does not work with oil-base muds or in air-filled holes\" "
                    f"(Asquith p. 25). There is no SP measurement to interpret, "
                    f"whatever the curve contains"),
            needed=("an Rw from a water analysis, a Pickett plot (rw_pickett), or a "
                    "catalogued produced-water record",),
            source=ASQUITH_SP,
        )
    if mud_type_text:
        conflict = _mud_conflict(mud_type_text, base)
        if conflict is not None:
            token, implied = conflict
            return Refusal(
                reason=(f"the log heading mud description {mud_type_text!r} contains "
                        f"{token!r}, which indicates a {MUD_BASES[implied]['label']}, "
                        f"but mud_base was declared {base!r}. Failing closed: the SP "
                        f"is invalid if the heading is right"),
                needed=("agreement between the declared mud base and the heading, or "
                        "a corrected heading",),
                source=ASQUITH_SP,
            )

    # --- refusal: outside the Rwe->Rw conversion's range ----------------------
    if formation_temp_degf <= RWE_RW_MIN_TEMP_DEGF:
        probe = rwe_to_rw(1.0, formation_temp_degf)
        if isinstance(probe, Refusal):
            return probe

    flags: list[str] = []

    # --- step 1: Rm and Rmf to formation temperature (Arps) -------------------
    rm_at_tf = resistivity_at_temperature(rm_ohmm, rm_temp_degf,
                                          formation_temp_degf, units="degF")
    rmf_at_tf = resistivity_at_temperature(rmf_ohmm, rmf_temp_degf,
                                           formation_temp_degf, units="degF")

    # --- step 0: the baseline subtraction ------------------------------------
    deflection = sp_mv - shale_baseline_mv
    if deflection > 0:
        flags.append(
            "positive (reversed) SP deflection: Rmf < Rw, i.e. the mud filtrate is "
            "fresher than the formation water (Asquith p. 25)")
    if abs(deflection) < SP_NEAR_ZERO_MV:
        flags.append(
            f"|SP deflection| = {abs(deflection):g} mV, below the "
            f"{SP_NEAR_ZERO_MV:g} mV provisional house floor: Rmf is close to Rw and "
            f"the answer is dominated by the shale-baseline pick")

    # --- step 2: SP -> SSP, the chart this tool cannot compute ----------------
    ri_over_rm_value = ri_ohmm / rm_at_tf.value
    if sp_correction_factor is None:
        if bed_thickness_ft < SSP_FULL_DEVELOPMENT_FT:
            return Refusal(
                reason=(f"the bed is {bed_thickness_ft:g} ft thick, below the "
                        f"{SSP_FULL_DEVELOPMENT_FT:g} ft at which the SP develops "
                        f"fully (AAPG: \"beds thinner than 20 ft\" need the chart "
                        f"correction), so SP is not SSP. The correction is Asquith "
                        f"Figure 2.3 / Western Atlas Chart 3, a chart image with no "
                        f"published formula in this corpus. Chart entry: bed "
                        f"thickness {bed_thickness_ft:g} ft, Ri/Rm = "
                        f"{ri_over_rm_value:.4g} (Ri {ri_ohmm:g}, Rm "
                        f"{rm_at_tf.value:.4g} ohm-m at {formation_temp_degf:g} degF)"),
                needed=(f"sp_correction_factor read from Asquith Fig. 2.3 at bed "
                        f"thickness {bed_thickness_ft:g} ft and Ri/Rm = "
                        f"{ri_over_rm_value:.4g}",),
                source=AAPG_RW_SP,
            )
        factor = 1.0
        flags.append(
            f"SP taken as SSP with no bed-thickness correction: the bed is "
            f"{bed_thickness_ft:g} ft, at or above the "
            f"{SSP_FULL_DEVELOPMENT_FT:g} ft full-development thickness (aapg#0). "
            f"The AAPG worked example still read a 1.07 factor for a 24-ft bed, so "
            f"this is a floor, not an identity")
    else:
        factor = float(sp_correction_factor)
    ssp = deflection * factor

    # --- steps 3 and 4: Rwe, then Rw -----------------------------------------
    k_value, k_spec = _k_coefficient(formation_temp_degf, k_form)
    other_form = "60" if k_form == "61" else "61"
    k_other, k_other_spec = _k_coefficient(formation_temp_degf, other_form)

    rwe_value = rmf_at_tf.value * 10.0 ** (ssp / k_value)
    rwe_other = rmf_at_tf.value * 10.0 ** (ssp / k_other)
    flags.append(
        f"K form {k_form!r} ({k_spec['label']}) gives K = {k_value:.4g}; the "
        f"corpus's other form ({k_other_spec['label']}) gives K = {k_other:.4g} and "
        f"Rwe = {rwe_other:.6g} ohm-m")

    rw_step = rwe_to_rw(rwe_value, formation_temp_degf)
    if isinstance(rw_step, Refusal):
        return rw_step

    if hydrocarbon_bearing:
        flags.append(
            "bed declared hydrocarbon-bearing: the SP is suppressed there, so Rw "
            "reads too high, Archie Sw reads too high, and this creates \"the chance "
            "for missed production\" (asquith#13, p. 23). AAPG p. 5 is blunter - the "
            "method \"does not give correct estimations of Rw in hydrocarbon-bearing "
            "zones\". Use a zone known to contain only water")
    if shaly:
        flags.append(
            "bed declared shaly: shaliness suppresses the SP (asquith#14, p. 25), in "
            "the same direction - Rw and Sw read high")
    if bed_thickness_ft < SSP_FULL_DEVELOPMENT_FT:
        flags.append(
            f"thin bed ({bed_thickness_ft:g} ft): SP suppression corrected by the "
            f"supplied factor {factor:g}, which is a chart read and carries its own "
            f"error")

    common_inputs = {
        "SP_read_mV": sp_mv, "shale_baseline_mV": shale_baseline_mv,
        "bed_thickness_ft": bed_thickness_ft, "Ri_ohmm": ri_ohmm,
        "Rm_ohmm": rm_ohmm, "Rm_temp_degF": rm_temp_degf,
        "Rmf_ohmm": rmf_ohmm, "Rmf_temp_degF": rmf_temp_degf,
        "Tf_degF": formation_temp_degf,
    }
    assumptions_common = {
        "mud_base": base, "mud_type_text": mud_type_text,
        "sp_correction_factor": factor,
        "sp_correction_source": (
            "caller, read from Asquith Fig. 2.3" if sp_correction_factor is not None
            else f"assumed 1.0, bed >= {SSP_FULL_DEVELOPMENT_FT:g} ft"),
        "k_form": k_form, "K": k_value, "K_other_form": k_other,
        "Ri_curve": ri_curve or "unnamed shallow-reading resistivity curve",
        "stated_at_degf": formation_temp_degf,
    }

    rwe = Quantity(
        rwe_value, "ohm-m",
        "Rwe from SSP, Asquith Eq. 2.2 rearranged (Table 2.1: Rwe = Rmf*10^(SSP/K))",
        ASQUITH_TABLE_21,
        inputs={**common_inputs, "SSP_mV": ssp, "Rmf_at_Tf": rmf_at_tf.value},
        assumptions={**assumptions_common, "quantity_kind": "Rwe"},
        flags=tuple(flags) + (
            "this is Rwe, an EQUIVALENT resistivity linearly related to chemical "
            "activity. It is not Rw: do not pass it to archie_sw and do not read it "
            "as a salinity (tool-verification.md:63)",),
    )
    rw = Quantity(
        rw_step.value, "ohm-m",
        "Rw from SP: Asquith ch. 2 procedure (Eq. 2.2 for Rwe, Table 2.1 "
        "Bateman-Konen for Rwe->Rw)",
        ASQUITH_TABLE_21,
        inputs={**common_inputs, "SSP_mV": ssp, "Rmf_at_Tf": rmf_at_tf.value,
                "Rwe": rwe_value},
        assumptions={**assumptions_common, "quantity_kind": "Rw",
                     "procedure": "asquith#13 p. 23, steps 1-4",
                     "rwe_to_rw": rw_step.method},
        flags=tuple(flags),
    )

    result = SpWaterResistivity(
        sp_deflection_mv=Quantity(
            deflection, "mV", "SP minus shale baseline (Asquith p. 27)", ASQUITH_SP,
            inputs={"SP_read_mV": sp_mv, "shale_baseline_mV": shale_baseline_mv}),
        ssp_mv=Quantity(
            ssp, "mV",
            "SSP = SP x bed-thickness correction factor (Asquith Fig. 2.3)",
            ASQUITH_SP,
            inputs={"SP_mV": deflection, "correction_factor": factor},
            assumptions={"factor_source": assumptions_common["sp_correction_source"]}),
        rm_at_tf=rm_at_tf,
        rmf_at_tf=rmf_at_tf,
        ri_over_rm=Quantity(
            ri_over_rm_value, "ratio", "Ri/Rm at Tf, the Figure 2.3 chart entry",
            ASQUITH_SP,
            inputs={"Ri_ohmm": ri_ohmm, "Rm_at_Tf": rm_at_tf.value},
            assumptions={"Ri_curve": assumptions_common["Ri_curve"]}),
        k=Quantity(k_value, "mV", k_spec["label"], k_spec["source"],
                   inputs={"Tf_degF": formation_temp_degf},
                   assumptions={"k_form": k_form, "other_form_K": k_other}),
        rwe=rwe,
        rw=rw,
        temperature_degf=formation_temp_degf,
        flags=tuple(flags),
    )
    if report_at_degf is None:
        return result
    return _restate_sp_result(result, report_at_degf)


def _restate_sp_result(result: SpWaterResistivity,
                       report_at_degf: float) -> SpWaterResistivity:
    """Move Rwe and Rw to another temperature through Arps, carrying both."""
    if report_at_degf <= 0:
        raise ValueError("report_at_degf must be a positive Fahrenheit temperature")
    moved = []
    for q in (result.rwe, result.rw):
        arps = resistivity_at_temperature(q.value, result.temperature_degf,
                                          report_at_degf, units="degF")
        moved.append(Quantity(
            arps.value, "ohm-m",
            f"{q.method}, restated at {report_at_degf:g} degF via the Arps "
            f"correction", q.source,
            inputs={**q.inputs, f"value_at_{result.temperature_degf:g}degF": q.value},
            assumptions={**q.assumptions, "stated_at_degf": report_at_degf,
                         "converted_from_degf": result.temperature_degf,
                         "conversion": arps.method},
            flags=q.flags))
    return SpWaterResistivity(
        sp_deflection_mv=result.sp_deflection_mv, ssp_mv=result.ssp_mv,
        rm_at_tf=result.rm_at_tf, rmf_at_tf=result.rmf_at_tf,
        ri_over_rm=result.ri_over_rm, k=result.k,
        rwe=moved[0], rw=moved[1], temperature_degf=report_at_degf,
        flags=result.flags + (
            f"Rwe and Rw restated from {result.temperature_degf:g} degF to "
            f"{report_at_degf:g} degF (Arps)",))


# =============================================================================
# #34  rw_pickett
# =============================================================================

# Published parameter ranges, seg-wiki-pickett-plot#0, p. 2: "a = proportionality
# constant varying from 0.6 to 1.5; m = cementation factor that varies between
# 1.3 and 3". Used only to flag a value outside published experience.
ARCHIE_A_RANGE = (0.6, 1.5)
ARCHIE_M_RANGE = (1.3, 3.0)

# PROVISIONAL house rule, reporting only, changes no value: how far a supplied m
# may sit from the free-fit m before the disagreement is flagged.
M_DISAGREEMENT_FRAC = 0.10

# The source states the sample-size requirement and never quantifies it, so
# neither does this module (specs/34-rw_pickett.md, open question 3).
SEG_SAMPLE_SIZE_CAUTION = (
    "seg-wiki#0: \"there must be a statistically significant number of zones "
    "plotted in order to provide accurate calculations\" - the source sets no "
    "number, so neither does this tool")

# m by porosity type, aapg-pickett-plot-construction#0, Step 3. Quoted, not wired
# into a lookup: the porosity-type call is the interpreter's and #24 is the
# lookup tool. Kept here so a supplied m has a citable origin.
PICKETT_M_BY_POROSITY_TYPE: dict[str, tuple[float, float]] = {
    "sandstone with diagenetic or detrital clay in pores": (1.7, 1.8),
    "clean macro- to micro-sized pore throats (Archie rocks)": (2.0, 2.0),
    "vuggy (touching to non touching)": (2.2, 3.0),
}


@dataclass(frozen=True)
class PickettFit:
    """What a Pickett plot yields: m, a*Rw, and Rw only if `a` was supplied."""

    m: Quantity
    a_rw: Quantity
    rw: Quantity | Refusal
    a_rw_spread: Range
    slope: Quantity
    intercept: Quantity
    wet_points: tuple[tuple[int, float | None, float, float], ...]
    temperature_degf: float
    flags: tuple[str, ...] = ()

    def __repr__(self) -> str:  # keeps test failures readable
        rw = f"{self.rw.value:.6g}" if isinstance(self.rw, Quantity) else "refused"
        return (f"PickettFit(m={self.m.value:.6g}, a*Rw={self.a_rw.value:.6g}, "
                f"Rw={rw}, n_wet={len(self.wet_points)})")


def _wet_indices(wet: Sequence[Any], n: int) -> list[int]:
    """A boolean mask or a sequence of indices, both accepted, neither guessed."""
    items = list(wet)
    if items and all(isinstance(v, bool) for v in items):
        if len(items) != n:
            raise ValueError(f"wet mask has {len(items)} entries for {n} points")
        return [i for i, flag in enumerate(items) if flag]
    out: list[int] = []
    for v in items:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(
                "wet must be a boolean mask over all points or a sequence of "
                f"integer indices; got {v!r}")
        if not 0 <= v < n:
            raise ValueError(f"wet index {v} is outside 0..{n - 1}")
        out.append(v)
    return sorted(set(out))


def rw_pickett(
    rt_ohmm: Sequence[float],
    phi: Sequence[float],
    *,
    wet: Sequence[Any] | None,
    temperature_degf: float | None,
    a: float | None = None,
    m: float | None = None,
    depths_ft: Sequence[float] | None = None,
    rt_invasion_corrected: bool = False,
    report_at_degf: float | None = None,
) -> PickettFit | Refusal:
    """Rw (or a*Rw) and m from a Pickett plot over declared-wet points.

    `log(phi) = (-1/m) log(Rt) + log(a*Rw)/m - (n log(Sw))/m` (kgs#1;
    corroborated by seg-wiki#0 eq. 3). On the 100% Sw line the last term
    vanishes, so `m = -1/slope` and `a*Rw = 10^(m * intercept)`.

    Returns `a*Rw` always, and `Rw` only when `a` is supplied, because the
    intercept cannot separate them. Requires the caller to say which points are
    wet: the 100% Sw line is a judgment envelope along the low-resistivity edge
    of the cloud, and a regression through every point would include
    hydrocarbon-bearing points and bias Rw high.
    """
    rts = list(rt_ohmm)
    phis = list(phi)
    if len(rts) != len(phis):
        raise ValueError(
            f"rt_ohmm has {len(rts)} values and phi has {len(phis)}; they are "
            f"matched pairs")
    depths = list(depths_ft) if depths_ft is not None else None
    if depths is not None and len(depths) != len(rts):
        raise ValueError(f"depths_ft has {len(depths)} values for {len(rts)} points")
    for value in phis:
        if isinstance(value, (int, float)) and math.isfinite(value) and value > 1.0:
            raise ValueError(
                f"porosity must be a fraction (v/v); got {value!r}. phi**m is not "
                f"scale-invariant, so percent porosity moves a*Rw by 100**m")
    if a is not None and a <= 0:
        raise ValueError(f"a must be positive; got {a!r}")
    if m is not None and m <= 0:
        raise ValueError(f"m must be positive; got {m!r}")

    if temperature_degf is None:
        return Refusal(
            reason=("an Rw with no temperature is not usable: resistivity is a "
                    "strong function of temperature, and every downstream "
                    "comparison is at formation temperature"),
            needed=("temperature_degf: the formation temperature of the wet "
                    "interval, e.g. from temperature_gradient (#32)",),
            source=ASQUITH_TABLE_21,
        )
    if temperature_degf <= 0:
        raise ValueError(
            f"temperature_degf must be a positive Fahrenheit temperature; got "
            f"{temperature_degf!r}")

    if wet is None:
        return Refusal(
            reason=("the 100% Sw line is placed along the low-resistivity edge of "
                    "the point cloud by judgment - \"the most 'southwest' edge of "
                    "the data points\" (seg-wiki#0) - not fitted through every "
                    "point. A regression through a mixed cloud includes "
                    "hydrocarbon-bearing points, which sit at higher Rt, and biases "
                    "a*Rw and Rw high. This tool will not pick the wet points for "
                    "you"),
            needed=("wet: a boolean mask or index list naming the points from an "
                    "interval known or interpreted to be 100% water-bearing",),
            source=SEG_PICKETT,
        )

    flags: list[str] = [SEG_SAMPLE_SIZE_CAUTION]
    selected = _wet_indices(wet, len(rts))
    points: list[tuple[int, float | None, float, float]] = []
    dropped = 0
    for i in selected:
        r, p = rts[i], phis[i]
        ok = (isinstance(r, (int, float)) and isinstance(p, (int, float))
              and math.isfinite(r) and math.isfinite(p) and r > 0 and p > 0)
        if not ok:
            dropped += 1
            continue
        points.append(
            (i, depths[i] if depths is not None else None, float(r), float(p)))
    if dropped:
        flags.append(
            f"{dropped} declared-wet point(s) dropped as unusable (null, non-finite, "
            f"or non-positive Rt or porosity); {len(points)} used")

    need = 1 if m is not None else 2
    if len(points) < need:
        return Refusal(
            reason=(f"{len(points)} usable wet point(s); "
                    + ("a slope needs at least two distinct points" if m is None
                       else "at least one point is needed")),
            needed=(("more wet points, or a supplied m so only the intercept is "
                     "fitted") if m is None else
                    "at least one wet point with positive Rt and porosity",),
            source=KGS_PICKETT,
        )

    xs = [math.log10(p[2]) for p in points]   # log10 Rt, the x axis
    ys = [math.log10(p[3]) for p in points]   # log10 phi, the y axis
    n = len(points)
    x_bar = sum(xs) / n
    y_bar = sum(ys) / n
    sxx = sum((x - x_bar) ** 2 for x in xs)
    sxy = sum((x - x_bar) * (y - y_bar) for x, y in zip(xs, ys))

    free_slope: float | None = None
    free_m: float | None = None
    if sxx > 0:
        free_slope = sxy / sxx
        if free_slope < 0:
            free_m = -1.0 / free_slope

    if m is None:
        if sxx == 0:
            return Refusal(
                reason=("every wet point has the same Rt, so the Pickett line has no "
                        "slope and m cannot be fitted"),
                needed=("wet points spanning a range of Rt, or a supplied m",),
                source=KGS_PICKETT,
            )
        if free_slope >= 0:
            return Refusal(
                reason=(f"the wet points fit a slope of {free_slope:.4g}; the Pickett "
                        f"line's slope is -1/m and must be negative (porosity falls "
                        f"as Rt rises along the water line). These points do not "
                        f"describe a 100% Sw line"),
                needed=("wet points from a single water-bearing interval, or a "
                        "supplied m",),
                source=KGS_PICKETT,
            )
        slope = free_slope
        m_value = free_m
        m_method = ("m = -1/slope of the least-squares fit through the declared wet "
                    "points")
        m_assumptions: dict[str, Any] = {"fitted": True, "n_wet": n}
    else:
        m_value = float(m)
        slope = -1.0 / m_value
        m_method = "m supplied by the caller; only the intercept was fitted"
        m_assumptions = {"fitted": False, "n_wet": n,
                         "free_fit_m": free_m, "free_fit_slope": free_slope}
        if free_m is not None and abs(free_m - m_value) > M_DISAGREEMENT_FRAC * m_value:
            flags.append(
                f"supplied m = {m_value:g} but the free fit through the same wet "
                f"points gives m = {free_m:.4g}, more than {M_DISAGREEMENT_FRAC:.0%} "
                f"apart; both are reported and neither is preferred by the source")

    intercept = y_bar - slope * x_bar
    a_rw_value = 10.0 ** (m_value * intercept)

    per_point: dict[str, float] = {}
    for idx, depth, r, p in points:
        key = f"{depth:g} ft" if depth is not None else f"point {idx}"
        if key in per_point:
            # A spliced or resampled log repeats depths. Without this the second
            # reading overwrites the first, the spread silently loses a point,
            # and `len(members)` stops agreeing with `len(wet_points)`.
            key = f"{key} (point {idx})"
        per_point[key] = p ** m_value * r
    spread_values = list(per_point.values())

    if not ARCHIE_M_RANGE[0] <= m_value <= ARCHIE_M_RANGE[1]:
        flags.append(
            f"m = {m_value:.4g} is outside the published range "
            f"{ARCHIE_M_RANGE[0]}-{ARCHIE_M_RANGE[1]} (seg-wiki#0, p. 2)")
    if a is not None and not ARCHIE_A_RANGE[0] <= a <= ARCHIE_A_RANGE[1]:
        flags.append(
            f"a = {a:g} is outside the published range {ARCHIE_A_RANGE[0]}-"
            f"{ARCHIE_A_RANGE[1]} (seg-wiki#0, p. 2)")
    if n == 2:
        flags.append(
            "exactly two wet points: a line through two points has no redundancy, "
            "and the a*Rw spread is not evidence of agreement")
    if not rt_invasion_corrected:
        flags.append(
            "Rt not declared invasion-corrected; deep readings are not Rt, and an "
            "invaded wet zone reads toward Rmf")

    inputs = {
        "n_wet_points": n,
        "wet_points": tuple(points),
        "Tf_degF": temperature_degf,
    }
    assumptions = {
        "stated_at_degf": temperature_degf,
        "m": m_value, "a": a,
        "wet_point_selection": "declared by the caller; not fitted or inferred",
        "fit": ("least squares through the declared wet points only; the published "
                "constructions place the line by hand, so no fit statistic is "
                "reported (kgs#1, seg-wiki#0, aapg-pickett-plot-construction#0)"),
        **m_assumptions,
    }

    a_rw = Quantity(
        a_rw_value, "ohm-m",
        "a*Rw = 10^(m * intercept) of the Pickett wet line (kgs#1)",
        KGS_PICKETT,
        inputs=inputs,
        assumptions={**assumptions, "quantity_kind": "a*Rw"},
        flags=tuple(flags) + (
            "this is the PRODUCT a*Rw, which is what the intercept yields. It is not "
            "Rw: assuming a = 1 is worth up to 40% on Rw across the published range "
            "of a (0.6-1.5)",),
    )
    if a is None:
        rw: Quantity | Refusal = Refusal(
            reason=("the Pickett intercept yields the product a*Rw; nothing on the "
                    "plot separates the tortuosity factor from Rw, so Rw is not "
                    f"available. a*Rw = {a_rw_value:.6g} ohm-m at "
                    f"{temperature_degf:g} degF"),
            needed=("a, the Archie tortuosity factor (published range 0.6-1.5, "
                    "seg-wiki#0), from core or a declared convention",),
            source=KGS_PICKETT,
        )
    else:
        rw = Quantity(
            a_rw_value / a, "ohm-m",
            "Rw from a Pickett plot: a*Rw from the wet-line intercept, divided by "
            "the supplied a (kgs#1)",
            KGS_PICKETT,
            inputs={**inputs, "a_Rw": a_rw_value, "a": a},
            assumptions={**assumptions, "quantity_kind": "Rw"},
            flags=tuple(flags),
        )

    result = PickettFit(
        m=Quantity(m_value, "exponent", m_method, KGS_PICKETT,
                   inputs={"slope": slope, "n_wet_points": n},
                   assumptions=m_assumptions, flags=tuple(flags)),
        a_rw=a_rw,
        rw=rw,
        a_rw_spread=Range(
            min(spread_values), max(spread_values), "ohm-m",
            "per-point a*Rw = phi^m * Rt over the wet set - the spread the wet "
            "points actually disagree by, reported instead of a fit statistic the "
            "published construction does not define",
            KGS_PICKETT, members=per_point),
        slope=Quantity(slope, "dimensionless",
                       "slope of log10(phi) on log10(Rt); slope = -1/m (kgs#1)",
                       KGS_PICKETT, inputs={"n_wet_points": n},
                       assumptions={"axes": "x = log10(Rt), y = log10(phi)"}),
        intercept=Quantity(intercept, "log10(v/v)",
                           "intercept of log10(phi) at Rt = 1; equals log10(a*Rw)/m "
                           "on the 100% Sw line (kgs#1)",
                           KGS_PICKETT, inputs={"n_wet_points": n}),
        wet_points=tuple(points),
        temperature_degf=temperature_degf,
        flags=tuple(flags),
    )
    if report_at_degf is None:
        return result
    return _restate_pickett(result, report_at_degf)


def _restate_pickett(result: PickettFit, report_at_degf: float) -> PickettFit:
    """Move a*Rw and Rw to another temperature through Arps, carrying both."""
    if report_at_degf <= 0:
        raise ValueError("report_at_degf must be a positive Fahrenheit temperature")

    def move(q: Quantity) -> Quantity:
        arps = resistivity_at_temperature(q.value, result.temperature_degf,
                                          report_at_degf, units="degF")
        return Quantity(
            arps.value, "ohm-m",
            f"{q.method}, restated at {report_at_degf:g} degF via the Arps "
            f"correction", q.source,
            inputs={**q.inputs, f"value_at_{result.temperature_degf:g}degF": q.value},
            assumptions={**q.assumptions, "stated_at_degf": report_at_degf,
                         "converted_from_degf": result.temperature_degf,
                         "conversion": arps.method},
            flags=q.flags)

    spread_members = {
        k: resistivity_at_temperature(v, result.temperature_degf, report_at_degf,
                                      units="degF").value
        for k, v in result.a_rw_spread.members.items()
    }
    return PickettFit(
        m=result.m,
        a_rw=move(result.a_rw),
        rw=move(result.rw) if isinstance(result.rw, Quantity) else result.rw,
        a_rw_spread=Range(min(spread_members.values()), max(spread_members.values()),
                          "ohm-m",
                          result.a_rw_spread.method + f", at {report_at_degf:g} degF",
                          result.a_rw_spread.source, members=spread_members),
        slope=result.slope, intercept=result.intercept,
        wet_points=result.wet_points, temperature_degf=report_at_degf,
        flags=result.flags + (
            f"a*Rw and Rw restated from {result.temperature_degf:g} degF to "
            f"{report_at_degf:g} degF (Arps)",))


# =============================================================================
# the provenance gate
# =============================================================================

def rw_provenance(quantity: Quantity) -> str:
    """The `rw_source` string `archie_sw` (#35) refuses to work without.

    The gate on Rwe and a*Rw. `archie_sw` takes `rw_source` as a free string, so
    nothing downstream can tell an Rw from an equivalent resistivity or from a
    product - this is where that is caught. Passing the wrong quantity is
    programmer error, not a condition the source declines to cover, so it raises
    rather than refusing.
    """
    if not isinstance(quantity, Quantity):
        raise TypeError(
            f"rw_provenance takes the Rw Quantity off a result record; got "
            f"{type(quantity).__name__}")
    kind = quantity.assumptions.get("quantity_kind")
    if kind != "Rw":
        raise TypeError(
            f"this Quantity is {kind!r}, not 'Rw'. "
            + ("Rwe is an equivalent resistivity, linearly related to chemical "
               "activity: convert it with rwe_to_rw() before using it as Rw, and "
               "never read it as a salinity."
               if kind == "Rwe" else
               "a*Rw is the product the Pickett intercept yields: supply the "
               "tortuosity factor a to rw_pickett to separate Rw from it."
               if kind == "a*Rw" else
               "only a Quantity carrying quantity_kind == 'Rw' may be used as Rw."))
    temp = quantity.assumptions.get("stated_at_degf")
    # specs/34 O5: the Pickett string carries the wet-point count, because
    # seg-wiki#0's "statistically significant number of zones" caution is
    # unusable downstream once the PickettFit record is gone. Absent on Rw from
    # any other route, which has no point count.
    n_wet = quantity.inputs.get("n_wet_points")
    over = f" over {n_wet} wet point{'' if n_wet == 1 else 's'}" if n_wet else ""
    return (f"{quantity.method}; Rw = {quantity.value:.6g} ohm-m at {temp:g} degF"
            f"{over} [{quantity.source}]")
