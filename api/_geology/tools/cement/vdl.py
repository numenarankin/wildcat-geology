"""#106 `vdl_classify` — the four-case CBL/VDL waveform classification.

Merge target: `tools/cement.py` (alongside `attenuation`, `cbl_bond_index`,
`isolation_length_check`). Spec: `specs/106-vdl_classify.md`.

Two decisions carry the tool, and both are the source's, not ours.

**There are four classes, and the third one is the reason this file exists.**
`petrowiki-cement-bond-logs#2` enumerates free pipe, good bond, bond to casing
only, and partial bond. *Good bond* and *bond to casing only* produce the SAME
amplitude - both are drastically attenuated casing arrivals - and differ only in
whether later formation energy exists. So the full waveform is a required input,
not a corroboration: an amplitude curve alone cannot tell a well that is sealed
to the rock from one that is not, and the failure direction is the dangerous one.
A previous version of this tool dropped case 3; `tool-verification.md:114` records
it.

**Channelling is not observable here, so it is never returned.**
`spe-back-to-basics-bond-log-theory#0`: "Single CBL 3' amplitude can not identify
channeling / VDL is also inconclusive." Channelling and microannulus are sub-cases
of partial bond and are separated by a second log run under pressure, which is
`microannulus_discriminate` (#105). Every partial-bond result carries the pointer.

The two amplitude bands are OURS. The source describes amplitude qualitatively
("high-amplitude", "attenuated drastically") and never puts a number on it, and
the catalog's *Thresholds the corpus does not supply* table does not cover this
tool. They are overridable, reported on every result, and arranged so that moving
them shifts inputs into and out of the R15 refusal rather than silently between
two answers.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ..result import Quantity, Refusal

# --------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------

PETROWIKI_CBL = "13-cement-integrity/petrowiki-cement-bond-logs#2"
PETROWIKI_CBL_1 = "13-cement-integrity/petrowiki-cement-bond-logs#1"
PETROWIKI_CBL_3 = "13-cement-integrity/petrowiki-cement-bond-logs#3"
SPE_BOND_LOG = "13-cement-integrity/spe-back-to-basics-bond-log-theory#0"
DRILLINGMANUAL_CBL = "13-cement-integrity/drillingmanual-cement-bond-log"

MICROANNULUS_DISCRIMINATE = "microannulus_discriminate (#105)"
CBL_CALIBRATION = "cbl_calibration (#102)"

# --------------------------------------------------------------------------
# Constant tables. Status is part of the constant, not a comment.
# --------------------------------------------------------------------------

#: Casing transit time. Below this the formation arrival lands inside the
#: amplitude gate. SOURCED, PETROWIKI_CBL: "Formations with transit times less
#: than casing (57 usec/ft) can cause problems when interpreting the amplitude
#: curves because the formation signal can arrive in the amplitude gate."
FAST_FORMATION_TRANSIT_US_PER_FT = 57.0

#: Green-cement wait. SOURCED but NOT at the tool's own anchor - the PetroWiki
#: page gives only the direction ("cement-bond logs may vary over time as the
#: cement cures and its properties change", PETROWIKI_CBL_1). The number is
#: SPE_BOND_LOG: "Rule of thumb is to not run bond logs up to 48 hours after
#: cementing (cement types such as thermal cements may vary)."
GREEN_CEMENT_HOURS = 48.0

#: SOURCED, PETROWIKI_CBL: "A longer spacing, commonly >= 5 ft, is used for the
#: full-waveform recording because longer TR spacing provides greater separation
#: of the casing and formation-signal arrival times." Flag only, never a refusal.
VDL_MIN_TR_SPACING_FT = 5.0

#: SOURCED, PETROWIKI_CBL: "TR spacing typically ranges from 3 to 5 ft."
#: Flag only - a tool run outside it is unusual, not invalid.
TR_SPACING_RANGE_FT = (3.0, 5.0)

#: PROVISIONAL - OURS, NOT THE SOURCE'S. See the module docstring and
#: specs/106-vdl_classify.md "The two provisional bands, stated plainly".
FREE_PIPE_BAND = 0.80
BONDED_BAND = 0.20
BANDS_STATUS = "PROVISIONAL - ours, not the source's; no corpus document puts a number on casing amplitude"

#: The source's own case numbering, from PETROWIKI_CBL ("1. In the first
#: scenario, free pipe ... 4. In the last scenario, partial bond"). The ordinal
#: returned as Quantity.value IS the source's case number.
VDL_CLASS_BY_ORDINAL = {
    1: "free_pipe",
    2: "good_bond",
    3: "bond_to_casing_only",
    4: "partial_bond",
}
VDL_CLASS_ORDINAL = {name: n for n, name in VDL_CLASS_BY_ORDINAL.items()}
VDL_CLASS_UNIT = "vdl_class"

#: Cement systems. `False` means the acoustic interpretation this tool performs
#: is not valid for that system, per the source in the third column.
CEMENT_TYPES: dict[str, tuple[bool, str, str]] = {
    # key: (interpretable, source anchor, why)
    "neat": (True, PETROWIKI_CBL, "conventional portland system"),
    "portland": (True, PETROWIKI_CBL, "conventional portland system"),
    "conventional": (True, PETROWIKI_CBL, "conventional portland system"),
    "standard": (True, PETROWIKI_CBL, "conventional portland system"),
    "class_a": (True, PETROWIKI_CBL, "conventional portland system"),
    "class_c": (True, PETROWIKI_CBL, "conventional portland system"),
    "class_g": (True, PETROWIKI_CBL, "conventional portland system"),
    "class_h": (True, PETROWIKI_CBL, "conventional portland system"),
    "thermal": (True, SPE_BOND_LOG,
                "conventional for classification, but the 48 h wait 'may vary'"),
    "thermal_g": (True, SPE_BOND_LOG,
                  "conventional for classification, but the 48 h wait 'may vary'"),
    "foam": (False, PETROWIKI_CBL,
             "foam cements, which intentionally create void spaces in the cured cement, "
             "can be misinterpreted as partial bond if normal cement is assumed"),
    "foamed": (False, PETROWIKI_CBL,
               "foam cements, which intentionally create void spaces in the cured cement, "
               "can be misinterpreted as partial bond if normal cement is assumed"),
    "foam_cement": (False, PETROWIKI_CBL,
                    "foam cements, which intentionally create void spaces in the cured cement, "
                    "can be misinterpreted as partial bond if normal cement is assumed"),
    "lightweight": (False, SPE_BOND_LOG,
                    "light weight cement: pipe is allowed to carry some pipe arrivals even "
                    "under perfect bonded conditions, and formation arrivals, if present, "
                    "may have a faded appearance"),
    "light_weight": (False, SPE_BOND_LOG,
                     "light weight cement: pipe is allowed to carry some pipe arrivals even "
                     "under perfect bonded conditions, and formation arrivals, if present, "
                     "may have a faded appearance"),
    "low_density": (False, DRILLINGMANUAL_CBL,
                    "low-density, low compressive strength cement: the acoustic impedance is "
                    "only slightly more than that of the drilling mud"),
    "extended": (False, DRILLINGMANUAL_CBL,
                 "extended (low-density) cement: the acoustic impedance is only slightly "
                 "more than that of the drilling mud"),
    "microsphere": (False, DRILLINGMANUAL_CBL,
                    "cement with sponge-like microspheres: acoustic devices 'have to be "
                    "carefully used' for this system"),
}

#: `cbl_calibration` (#102) is written by another agent. These are the field
#: names this tool looks for, attribute first, then mapping key, then the
#: `.inputs` / `.assumptions` dicts of a returned Quantity.
_CAL_FIELDS: dict[str, tuple[str, ...]] = {
    "free_pipe_amplitude_mv": (
        "free_pipe_amplitude_mv", "free_pipe_amplitude", "free_pipe_mv",
        "amplitude_free_pipe", "a_free_pipe",
    ),
    "fully_bonded_amplitude_mv": (
        "bonded_amplitude", "fully_bonded_amplitude_mv", "fully_bonded_amplitude",
        "bonded_amplitude_mv", "hundred_percent_amplitude", "amplitude_100pct", "a_bonded",
    ),
    "tr_spacing_ft": (
        "tr_spacing_ft", "tr_spacing", "transmitter_receiver_spacing_ft", "d_ft",
    ),
    "casing_od_in": (
        "casing_od_in", "casing_size_in", "casing_od", "casing_diameter_in",
    ),
    "cement_type": ("cement_type", "cement", "cement_class"),
    "amplitude_unit": ("amplitude_unit",),
}

#: This tool's amplitudes are mV, the unit the source presents them in
#: ("Amplitude (mV)", PETROWIKI_CBL_1). #102 labels its anchors with
#: `amplitude_unit` and states downstream measurements must match, so a
#: disagreement is a refusal, not a conversion.
AMPLITUDE_UNIT = "mV"

_GAS_CAVEAT = (
    "bond to casing only: a similar response can be caused by the presence of "
    "formation gas in shallow, high-porosity zones - this tool cannot separate the two"
)
_CHANNEL_CAVEAT = (
    "partial bond covers both microannulus and channelling and this measurement "
    "cannot separate them: 'Single CBL 3\\' amplitude can not identify channeling / "
    "VDL is also inconclusive' (" + SPE_BOND_LOG + "). Separating them needs a second "
    "bond log under pressure - 'if only channeling exists, pressuring the casing will "
    "not significantly change the log' (" + PETROWIKI_CBL + "). Run " +
    MICROANNULUS_DISCRIMINATE + "."
)


def vdl_class_name(result: Any) -> str | None:
    """The class label off a `vdl_classify` result. `None` for a `Refusal`."""
    if isinstance(result, Refusal):
        return None
    return VDL_CLASS_BY_ORDINAL.get(int(round(result.value)))


# --------------------------------------------------------------------------
# Calibration reading
# --------------------------------------------------------------------------

def _read_field(obj: Any, names: Sequence[str]) -> Any:
    """Attribute, then mapping key, then a Quantity's inputs/assumptions."""
    for name in names:
        value = getattr(obj, name, None)
        if value is not None:
            return value
    if isinstance(obj, Mapping):
        for name in names:
            if obj.get(name) is not None:
                return obj[name]
    for holder in ("inputs", "assumptions"):
        nested = getattr(obj, holder, None)
        if isinstance(nested, Mapping):
            for name in names:
                if nested.get(name) is not None:
                    return nested[name]
    return None


def _numeric(value: Any) -> float | None:
    """Accept a float or a `Quantity`-like carrier of one."""
    if value is None:
        return None
    inner = getattr(value, "value", value)
    try:
        return float(inner)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------

def vdl_classify(
    amplitude_mv: float | Sequence[float],
    *,
    waveform: Any = None,
    calibration: Any = None,
    tr_spacing_ft: float | None = None,
    casing_od_in: float | None = None,
    cement_type: str | None = None,
    formation_transit_time_us_per_ft: float | None = None,
    hours_since_cementing: float | None = None,
    vdl_tr_spacing_ft: float | None = None,
    free_pipe_band: float = FREE_PIPE_BAND,
    bonded_band: float = BONDED_BAND,
) -> Quantity | Refusal:
    """Classify a CBL/VDL waveform into the source's four cases.

    Returns a `Quantity` whose `value` is the source's own case number
    (1 free pipe, 2 good bond, 3 bond to casing only, 4 partial bond) and whose
    unit is `"vdl_class"` - a nominal code, not a magnitude. Decode with
    `VDL_CLASS_BY_ORDINAL` or `vdl_class_name`.

    `calibration` is a `cbl_calibration` (#102) result and is never recomputed
    here; the catalog requires #103 and #106 to read the same object. `waveform`
    carries the full-waveform observation and must declare
    `formation_arrival_present` - that field alone separates good bond from bond
    to casing only.

    Never returns a channelling or microannulus verdict. Both are sub-cases of
    partial bond, and the source says this measurement cannot separate them.
    """
    # -- programmer error --------------------------------------------------
    if not (0.0 <= bonded_band < free_pipe_band <= 1.0):
        raise ValueError("bands must satisfy 0 <= bonded_band < free_pipe_band <= 1")
    for name, value in (("tr_spacing_ft", tr_spacing_ft),
                        ("casing_od_in", casing_od_in),
                        ("vdl_tr_spacing_ft", vdl_tr_spacing_ft),
                        ("formation_transit_time_us_per_ft",
                         formation_transit_time_us_per_ft)):
        if value is not None and float(value) <= 0:
            raise ValueError(f"{name} must be positive, got {value!r}")
    if hours_since_cementing is not None and float(hours_since_cementing) < 0:
        raise ValueError("hours_since_cementing cannot be negative")

    amplitudes = _amplitude_series(amplitude_mv)
    amplitude = _median(amplitudes)

    flags: list[str] = []
    checks_not_run: list[str] = []

    # -- R6/R7/R8/R9: the catalog's required inputs ------------------------
    if tr_spacing_ft is None:
        return Refusal(
            reason="TR spacing is a required input and was not supplied; a 3 ft and a 5 ft "
                   "tool do not give the same amplitude from the same cement",
            needed=("tr_spacing_ft, in ft, of the amplitude measurement",),
            source=PETROWIKI_CBL,
        )
    if casing_od_in is None:
        return Refusal(
            reason="casing size is a required input and was not supplied; 'opening time for "
                   "the gate is a function of the casing size and the borehole-fluid velocity'",
            needed=("casing_od_in, in inches",),
            source=PETROWIKI_CBL,
        )
    if cement_type is None:
        return Refusal(
            reason="cement type is a required input and was not supplied: 'When conducting a "
                   "cement evaluation, information on the type of cement used is essential'",
            needed=("cement_type, one of " + ", ".join(sorted(CEMENT_TYPES)),),
            source=PETROWIKI_CBL,
        )
    cement_key = str(cement_type).strip().lower().replace(" ", "_").replace("-", "_")
    if cement_key not in CEMENT_TYPES:
        return Refusal(
            reason=f"cement type {cement_type!r} is not recognised; 'information on the type "
                   "of cement used is essential' and an unrecognised system is not assumed "
                   "to be a conventional one",
            needed=("cement_type, one of " + ", ".join(sorted(CEMENT_TYPES)),),
            source=PETROWIKI_CBL,
        )

    # -- R10/R11: SOURCED refusal, foam and lightweight cement -------------
    interpretable, cement_source, cement_note = CEMENT_TYPES[cement_key]
    if not interpretable:
        return Refusal(
            reason=f"cement type {cement_key!r} is outside conventional acoustic "
                   f"interpretation: {cement_note}",
            needed=("a conventional cement system, or a service-company calibration for this "
                    "system - 'users are advised to consult with the logging service company "
                    "regarding the appropriate calibrations'",
                    "or an ultrasonic/attenuation combination method for foam and lightweight "
                    "systems"),
            source=cement_source,
        )
    if cement_key.startswith("thermal"):
        flags.append("thermal cement: the 48 h green-cement rule of thumb 'may vary' for this "
                     "system (" + SPE_BOND_LOG + ")")

    # -- R12: SOURCED refusal, green cement --------------------------------
    if hours_since_cementing is None:
        checks_not_run.append("green_cement_48h")
        flags.append("green-cement check not run: hours_since_cementing was not supplied, so "
                     f"the {GREEN_CEMENT_HOURS:.0f} h rule of thumb could not be applied")
    elif float(hours_since_cementing) < GREEN_CEMENT_HOURS:
        return Refusal(
            reason=f"cement is green: {float(hours_since_cementing):.1f} h since cementing, "
                   f"inside the {GREEN_CEMENT_HOURS:.0f} h rule of thumb - 'Rule of thumb is "
                   f"to not run bond logs up to 48 hours after cementing'. Low compressive "
                   "strength gives higher than normal amplitudes, so every class would read "
                   "worse-bonded than it is",
            needed=(f"a log run at least {GREEN_CEMENT_HOURS:.0f} h after cementing",
                    "or a compressive-strength-vs-time correction from the service company"),
            source=SPE_BOND_LOG,
        )

    # -- R13: SOURCED refusal, fast formation ------------------------------
    if formation_transit_time_us_per_ft is None:
        checks_not_run.append("fast_formation_57us")
        flags.append("fast-formation check not run: formation_transit_time_us_per_ft was not "
                     f"supplied, so the {FAST_FORMATION_TRANSIT_US_PER_FT:.0f} usec/ft casing "
                     "transit time could not be compared")
    elif float(formation_transit_time_us_per_ft) < FAST_FORMATION_TRANSIT_US_PER_FT:
        return Refusal(
            reason=f"fast formation: transit time {float(formation_transit_time_us_per_ft):.1f} "
                   f"usec/ft is less than casing ({FAST_FORMATION_TRANSIT_US_PER_FT:.0f} "
                   "usec/ft), so 'the formation signal can arrive in the amplitude gate' and "
                   "the amplitude curve no longer measures the casing arrival alone",
            needed=("VDL confirmation that the formation arrival is not impacting the "
                    "amplitude curve - 'The VDL should be examined to ensure that the "
                    "formation arrival is impacting the amplitude curve'",
                    "or a pad-type radial measurement, which is 'unaffected by ... fast "
                    "formations' (" + PETROWIKI_CBL_3 + ")"),
            source=PETROWIKI_CBL,
        )

    # -- R1/R2/R3: the calibration -----------------------------------------
    if calibration is None:
        return Refusal(
            reason="no calibration: the free-pipe (BI = 0) and 100%-bonded (BI = 1) amplitudes "
                   "are not constants - they vary with drilling mud, cement acoustic "
                   "properties, casing size and thickness - and this tool must read the same "
                   "calibration object as cbl_bond_index (#103) rather than deriving its own",
            needed=(f"a {CBL_CALIBRATION} result for this casing size, cement type and TR "
                    "spacing",),
            source=DRILLINGMANUAL_CBL,
        )

    a_free = _numeric(_read_field(calibration, _CAL_FIELDS["free_pipe_amplitude_mv"]))
    a_bond = _numeric(_read_field(calibration, _CAL_FIELDS["fully_bonded_amplitude_mv"]))
    missing = [n for n, v in (("free-pipe amplitude", a_free),
                              ("100%-bonded amplitude", a_bond)) if v is None]
    if missing:
        return Refusal(
            reason=f"the calibration does not carry the {' and the '.join(missing)}; "
                   "interpretation 'requires correct knowledge of the amplitude of 100% "
                   "cemented sheath and of free pipe'",
            needed=tuple(
                f"{CBL_CALIBRATION} field, one of: " + ", ".join(_CAL_FIELDS[key])
                for key, label in (("free_pipe_amplitude_mv", "free-pipe amplitude"),
                                   ("fully_bonded_amplitude_mv", "100%-bonded amplitude"))
                if label in missing
            ) + (
                "an attenuation-only calibration (free_pipe_attenuation_db_ft / "
                "bonded_attenuation_db_ft) is not accepted here: converting it would change "
                "what the amplitude fraction means. That chain is cbl_bond_index (#103)",
            ),
            source=DRILLINGMANUAL_CBL,
        )
    if a_free <= 0 or a_bond <= 0 or a_free <= a_bond:
        return Refusal(
            reason=f"the calibration is not a scale: free-pipe amplitude {a_free:g} mV must be "
                   f"positive and greater than the 100%-bonded amplitude {a_bond:g} mV; free "
                   "pipe is the high-amplitude end by the source's own definition of case 1",
            needed=(f"a {CBL_CALIBRATION} whose free-pipe amplitude exceeds its 100%-bonded "
                    "amplitude",),
            source=DRILLINGMANUAL_CBL,
        )

    # -- R14: the calibration must describe THIS log -----------------------
    mismatch = _calibration_mismatch(calibration, tr_spacing_ft, casing_od_in, cement_key)
    if mismatch is not None:
        return Refusal(
            reason=f"the calibration does not describe this log: {mismatch}. 'Must read the "
                   "same calibration object' has no content if that object was established "
                   "for a different tool, casing or cement",
            needed=(f"a {CBL_CALIBRATION} established at {tr_spacing_ft:g} ft TR spacing on "
                    f"{casing_od_in:g} in. casing with {cement_key} cement",),
            source=DRILLINGMANUAL_CBL,
        )

    # -- R4/R5: the full waveform ------------------------------------------
    if waveform is None:
        return Refusal(
            reason="no full waveform: an amplitude curve alone cannot separate good bond from "
                   "bond to casing only, because both are drastically attenuated casing "
                   "arrivals and they differ only in whether later formation energy exists. "
                   "'pipe amplitude ... provides no indication of the quality of the bond "
                   "between the cement and the formation'",
            needed=("a full-waveform (VDL) observation declaring formation_arrival_present",),
            source=PETROWIKI_CBL,
        )
    formation_arrival = _read_field(waveform, ("formation_arrival_present",
                                               "formation_arrival",
                                               "later_formation_energy_present"))
    if formation_arrival is None:
        return Refusal(
            reason="the waveform observation does not declare formation_arrival_present, "
                   "which is the only thing separating good bond from bond to casing only: "
                   "case 3 'is indicated by the lack of later-arriving formation energy'",
            needed=("waveform.formation_arrival_present, a bool read off the VDL",),
            source=PETROWIKI_CBL,
        )
    formation_arrival = bool(formation_arrival)

    # -- the discriminant ---------------------------------------------------
    span = a_free - a_bond
    fraction = (amplitude - a_bond) / span

    # -- classify: the source's four cases ---------------------------------
    if formation_arrival:
        if fraction <= bonded_band:
            # Case 2: "little (weak) to no casing signals and little amplitude
            # until the arrival of the strong formation signal."
            ordinal = 2
        else:
            # Case 4: "the resulting waveform is comprised of a casing signal
            # and a formation signal; the casing signal arrives first, followed
            # by the formation signal."
            ordinal = 4
    else:
        if fraction >= free_pipe_band:
            # Case 1: "long-lived, high-amplitude, of uniform frequency."
            ordinal = 1
        elif fraction <= bonded_band:
            # Case 3: "attenuated drastically ... indicated by the lack of
            # later-arriving formation energy."
            ordinal = 3
        else:
            # R15: matches none of the four. Partial bond needs a formation
            # signal, bond-to-casing-only needs drastic attenuation, free pipe
            # needs high amplitude.
            return Refusal(
                reason=f"ambiguous: the casing amplitude sits at {fraction:.3f} of the "
                       f"free-pipe/100%-bonded span with no formation arrival. That matches "
                       "none of the source's four cases - partial bond requires a formation "
                       "signal, bond to casing only requires drastic attenuation, free pipe "
                       "requires high amplitude",
                needed=("a formation-arrival observation from a longer-spaced VDL (>= 5 ft), "
                        "which gives 'greater separation of the casing and formation-signal "
                        "arrival times'",
                        "or a radial cement-evaluation measurement",
                        f"the bands used were bonded_band={bonded_band:g}, "
                        f"free_pipe_band={free_pipe_band:g}, which are ours, not the source's"),
                source=PETROWIKI_CBL,
            )

    label = VDL_CLASS_BY_ORDINAL[ordinal]

    # -- flags --------------------------------------------------------------
    flags.extend(_amplitude_flags(amplitudes, span, fraction))
    flags.extend(_spacing_flags(tr_spacing_ft, vdl_tr_spacing_ft))
    flags.extend(_corroboration_flags(waveform, label, fraction, free_pipe_band))
    if label == "bond_to_casing_only":
        flags.append(_GAS_CAVEAT)
    if label == "partial_bond":
        flags.append(_CHANNEL_CAVEAT)

    assumptions: dict[str, Any] = {
        "vdl_class": label,
        "source_case_number": ordinal,
        "casing_amplitude_fraction_of_free_pipe_span": fraction,
        "fraction_is_not_a_bond_index": "linear position between the two calibration anchors; "
                                        "bond index is a ratio of attenuations and is "
                                        "cbl_bond_index (#103)",
        "bands": {"bonded_band": bonded_band, "free_pipe_band": free_pipe_band},
        "bands_status": BANDS_STATUS,
        "calibration_source": getattr(calibration, "source", None) or CBL_CALIBRATION,
        "checks_not_run": tuple(checks_not_run),
        "class_table": dict(VDL_CLASS_BY_ORDINAL),
    }
    if label == "partial_bond":
        assumptions["next_tool"] = MICROANNULUS_DISCRIMINATE
        assumptions["channelling_verdict"] = (
            "not returned: channelling and microannulus are sub-cases of partial bond and "
            "this measurement cannot separate them"
        )

    return Quantity(
        float(ordinal), VDL_CLASS_UNIT,
        f"VDL/CBL four-case waveform classification: {label}", PETROWIKI_CBL,
        inputs={
            "amplitude_mv": amplitude,
            "amplitude_samples_mv": tuple(amplitudes) if len(amplitudes) > 1 else None,
            "formation_arrival_present": formation_arrival,
            "free_pipe_amplitude_mv": a_free,
            "fully_bonded_amplitude_mv": a_bond,
            "tr_spacing_ft": tr_spacing_ft,
            "casing_od_in": casing_od_in,
            "cement_type": cement_key,
            "formation_transit_time_us_per_ft": formation_transit_time_us_per_ft,
            "hours_since_cementing": hours_since_cementing,
        },
        assumptions=assumptions,
        flags=tuple(flags),
    )


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _amplitude_series(amplitude_mv: Any) -> list[float]:
    if isinstance(amplitude_mv, (str, bytes)):
        raise ValueError("amplitude_mv must be a number or a sequence of numbers")
    if isinstance(amplitude_mv, Sequence):
        values = [float(v) for v in amplitude_mv]
        if not values:
            raise ValueError("amplitude_mv series is empty")
    else:
        values = [float(getattr(amplitude_mv, "value", amplitude_mv))]
    if any(v <= 0 for v in values):
        raise ValueError("amplitudes must be positive, in mV")
    return values


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0


def _calibration_mismatch(calibration: Any, tr_spacing_ft: float,
                          casing_od_in: float, cement_key: str) -> str | None:
    """Reconcile the call arguments against whatever the calibration declares."""
    cal_unit = _read_field(calibration, _CAL_FIELDS["amplitude_unit"])
    if isinstance(cal_unit, str) and cal_unit.strip() and cal_unit.strip() != AMPLITUDE_UNIT:
        return (f"its anchors are in {cal_unit.strip()}, this tool's amplitude_mv is in "
                f"{AMPLITUDE_UNIT}; the fraction between the anchors is meaningless across "
                "two units and no conversion is applied")
    cal_tr = _numeric(_read_field(calibration, _CAL_FIELDS["tr_spacing_ft"]))
    if cal_tr is not None and abs(cal_tr - float(tr_spacing_ft)) > 1e-9:
        return (f"it was established at {cal_tr:g} ft TR spacing, this log was run at "
                f"{float(tr_spacing_ft):g} ft")
    cal_od = _numeric(_read_field(calibration, _CAL_FIELDS["casing_od_in"]))
    if cal_od is not None and abs(cal_od - float(casing_od_in)) > 1e-9:
        return (f"it was established on {cal_od:g} in. casing, this log was run on "
                f"{float(casing_od_in):g} in. casing")
    cal_cement = _read_field(calibration, _CAL_FIELDS["cement_type"])
    if isinstance(cal_cement, str):
        cal_key = cal_cement.strip().lower().replace(" ", "_").replace("-", "_")
        if cal_key and cal_key != cement_key:
            return f"it was established for {cal_key!r} cement, this well used {cement_key!r}"
    return None


def _amplitude_flags(amplitudes: Sequence[float], span: float,
                     fraction: float) -> list[str]:
    flags: list[str] = []
    if fraction > 1.0:
        flags.append(f"amplitude is above the free-pipe anchor (fraction {fraction:.3f} > 1); "
                     "the calibration may not describe this interval")
    elif fraction < 0.0:
        flags.append(f"amplitude is below the 100%-bonded anchor (fraction {fraction:.3f} < 0); "
                     "the calibration may not describe this interval")
    if len(amplitudes) > 1:
        lo, hi = min(amplitudes), max(amplitudes)
        flags.append(
            f"amplitude varies over the interval: {lo:g}-{hi:g} mV, a span of "
            f"{(hi - lo) / span:.3f} of the free-pipe/100%-bonded span. The source notes "
            "channelling 'is generally localized and nonuniform ... and can frequently be "
            "identified by variations in the amplitude response', but gives no cutoff, so "
            "none is applied here and no channelling verdict follows from this number"
        )
    return flags


def _spacing_flags(tr_spacing_ft: float, vdl_tr_spacing_ft: float | None) -> list[str]:
    flags: list[str] = []
    lo, hi = TR_SPACING_RANGE_FT
    if not (lo <= float(tr_spacing_ft) <= hi):
        flags.append(f"TR spacing {float(tr_spacing_ft):g} ft is outside the {lo:g}-{hi:g} ft "
                     "the source calls typical")
    if vdl_tr_spacing_ft is not None and float(vdl_tr_spacing_ft) < VDL_MIN_TR_SPACING_FT:
        flags.append(
            f"the full waveform was recorded at {float(vdl_tr_spacing_ft):g} ft TR spacing; "
            f"a spacing >= {VDL_MIN_TR_SPACING_FT:g} ft is used for full-waveform recording "
            "'because longer TR spacing provides greater separation of the casing and "
            "formation-signal arrival times', so the formation-arrival call is less secure"
        )
    return flags


def _corroboration_flags(waveform: Any, label: str, fraction: float,
                         free_pipe_band: float) -> list[str]:
    """Optional waveform features. Corroboration only - never a discriminator."""
    flags: list[str] = []
    shear = _read_field(waveform, ("shear_wave_amplitudes_present", "shear_present"))
    if label == "good_bond" and shear is False:
        flags.append("good bond called, but no shear-wave amplitudes were observed on the "
                     "full waveform; 'the presence of shear-wave amplitudes on the "
                     "full-waveform display is an indication of good acoustic coupling to "
                     "the formation', so the corroboration is absent")
    if label == "partial_bond" and fraction >= free_pipe_band:
        flags.append(f"conflicting evidence: a formation arrival was observed while the casing "
                     f"amplitude sits at {fraction:.3f} of the span, i.e. free-pipe level, "
                     "where the source says there is 'no acoustic coupling with the "
                     "formation'. Classified as partial bond because both arrivals are "
                     "present, but the two observations disagree")
    collars = _read_field(waveform, ("collar_chevrons_present", "collar_signals_present"))
    if collars is True and label in ("good_bond",):
        flags.append("casing-collar 'w' patterns were observed; the source associates collar "
                     "signals with cases of poor bonding (" + PETROWIKI_CBL_1 + ")")
    return flags
