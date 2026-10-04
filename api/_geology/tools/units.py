"""Unit conversion for log values. Destination module: `tools/units.py`.

The non-obvious decisions, in the order they bite:

**The factors are ours.** There is no conversion table anywhere in the corpus —
`02-las-format/kgs-las-2.0-field-table#1` is a header-field table that shows a
unit is *declared* per field (`STRT .F`) and never says what any unit is worth.
That is survivable only because these particular numbers are not measurements:
1 ft = 0.3048 m is the definition of the international foot, percent means per
hundred, `kilo` means 1000. Every row of `SCALAR_UNITS` carries the definition it
comes from, and no factor appears inline in a formula. Converted values are
sourced `owned:` and never to an anchor this module does not have.

**Three things the number and its label do not carry**, each of which is a
refusal rather than a guess:

- *API is not a unit.* `beg#58`: "one of two different measures of radioactivity
  ... one unit is for the calibration of gamma-ray counters, the other for
  neutron detectors." Two standards, different physics, different pits, no factor
  between them. Enforced in `_api_gate`, not in a comment.
- *Neutron porosity carries a matrix reference.* `asquith#19`: the curves are
  displayed "in units referenced to a specific lithology (usually either
  limestone or sandstone...)", and `asquith#28` says a limestone-referenced curve
  shows a false crossover in a sandstone. So the matrix travels in
  `assumptions`, and a neutron conversion with no declared matrix **fails**. Note
  this is stricter than the catalog's "limestone unless the header says
  otherwise": the source does not support limestone as a silent default, so this
  module has none.
- *Temperature is affine.* degF -> degC is one arithmetic for a reading and a
  different one for a difference, and "degF" does not say which. `temperature_sense`
  has no default.

**An unknown unit token refuses, it does not raise.** Unit strings here come out
of files, not out of call sites: LAS declares a unit field but fixes no
vocabulary for it, so vendors write what they write. An unrecognised token is a
data condition the operator must see, like a bad mnemonic, and crashing a curve
loop on it is wrong. Exceptions stay for what can only be a call-site defect: a
non-numeric value, a non-string unit, an unknown `kind`, `matrix` or
`temperature_sense`.

Full reasoning, oracles and open questions: `specs/11-unit_convert.md`.
"""
from __future__ import annotations

import math
from typing import Any

from .result import Quantity, Range, Refusal

SPEC = "specs/11-unit_convert.md"

#: Every converted value is sourced here. A factor that is true by definition has
#: no corpus anchor and must not borrow one.
OWNED = f"owned: {SPEC} - exact by definition, not from the corpus"

#: The two rules this tool exists to enforce ARE sourced, at anchors the catalog
#: does not give. Refusals cite these.
BEG_API = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#58"
ASQUITH_NEUTRON = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#19"
LAS_UNIT_FIELD = "02-las-format/kgs-las-2.0-field-table#1"

# ---------------------------------------------------------------------------
# Definitional constants
# ---------------------------------------------------------------------------
# Named once, here, so that every derived row below is visibly derived from them
# rather than from a number someone typed.
FOOT_M = 0.3048                 # international foot, 1959 agreement: exact
US_SURVEY_FOOT_M = 1200 / 3937  # US survey foot: exact by definition
INCH_M = 0.0254                 # 1 in = 1/12 ft: exact
POUND_KG = 0.45359237           # international pound, 1959 agreement: exact

# ---------------------------------------------------------------------------
# Scalar unit table: canonical token -> (family, factor to family base, note)
# ---------------------------------------------------------------------------
# The factor converts INTO the family base unit. Every note states the
# definition the number is, or the definitional constants it is built from.
# Nothing here is empirical and nothing here can drift.
SCALAR_UNITS: dict[str, tuple[str, float, str]] = {
    # length, base metre
    "M": ("length", 1.0, "base unit of the family"),
    "FT": ("length", FOOT_M, "1 ft = 0.3048 m exactly (international foot, 1959)"),
    "FT_US": ("length", US_SURVEY_FOOT_M,
              "1 US survey ft = 1200/3937 m exactly; 2 ppm longer than the international foot"),
    "IN": ("length", INCH_M, "1 in = 0.0254 m exactly (1/12 of the international foot)"),
    "CM": ("length", 0.01, "SI prefix centi- = 1e-2, by definition"),
    "MM": ("length", 0.001, "SI prefix milli- = 1e-3, by definition"),
    # density, base kg/m3
    "KG/M3": ("density", 1.0, "base unit of the family"),
    "G/CM3": ("density", 1000.0,
              "1 g/cm3 = 1e-3 kg / 1e-6 m3 = 1000 kg/m3, from the SI prefixes alone"),
    "MG/M3": ("density", 1000.0,
              "1 Mg/m3 = 1000 kg/m3; numerically identical to g/cm3, by the SI prefixes"),
    "LB/FT3": ("density", POUND_KG / FOOT_M ** 3,
               "derived: exact pound (0.45359237 kg) over the exact foot cubed"),
    # fraction, base v/v
    "V/V": ("fraction", 1.0, "base unit of the family"),
    "PCT": ("fraction", 0.01, "percent means per hundred, by definition"),
    # resistivity, base ohm-m. One token: this family normalises spelling only.
    "OHM-M": ("resistivity", 1.0, "base unit of the family; no alternate unit in use"),
    # interval transit time, base usec/m
    "USEC/M": ("transit_time", 1.0, "base unit of the family"),
    "USEC/FT": ("transit_time", 1 / FOOT_M,
                "derived: reciprocal of the exact foot; per foot is more per metre"),
    # potential, base volt
    "V": ("potential", 1.0, "base unit of the family"),
    "MV": ("potential", 0.001, "SI prefix milli- = 1e-3, by definition"),
    # photoelectric effect. Single token: identity only, kept so a PE curve
    # canonicalises instead of refusing.
    "B/E": ("pe", 1.0, "base unit of the family; no alternate unit in use"),
}

# ---------------------------------------------------------------------------
# Temperature: affine, so it cannot live in the scalar table
# ---------------------------------------------------------------------------
# T_kelvin = scale * T + offset. `delta` conversions use `scale` only: a
# temperature DIFFERENCE has no offset, which is the whole reason
# `temperature_sense` is required rather than defaulted.
TEMPERATURE_UNITS: dict[str, tuple[float, float, str]] = {
    "DEGK": (1.0, 0.0, "kelvin is the SI base unit"),
    "DEGC": (1.0, 273.15, "0 degC = 273.15 K exactly, by definition of the Celsius scale"),
    "DEGR": (5 / 9, 0.0, "Rankine is absolute with the Fahrenheit degree: 1 degR = 5/9 K exactly"),
    "DEGF": (5 / 9, 459.67 * 5 / 9,
             "T_K = (T_F + 459.67) * 5/9 exactly, by definition of the Fahrenheit scale"),
}
TEMPERATURE_FAMILY = "temperature"

# ---------------------------------------------------------------------------
# API calibration scales - deliberately NOT units
# ---------------------------------------------------------------------------
# beg#58: "API units - one of two different measures of radioactivity on well
# logs ... One unit is for the calibration of gamma-ray counters, the other for
# neutron detectors." asquith#19 on the neutron scale: "while other logs are
# calibrated in basic physical units, neutron logs are not". There is no factor
# between the two pits and none out of either, so these tokens are recognised
# only so that a request to convert them can be refused with a reason.
API_SCALES: dict[str, str] = {
    "GAPI": "API gamma-ray scale (gamma-ray calibration pit)",
    "NAPI": "API neutron scale (neutron calibration pit)",
    "API": "unqualified 'API' - the corpus names two API scales and this token picks neither",
}

# ---------------------------------------------------------------------------
# Spellings seen in the wild -> canonical token
# ---------------------------------------------------------------------------
# OWNED, and certainly incomplete: LAS declares a unit field but fixes no
# vocabulary for it (LAS_UNIT_FIELD), so this is a vendor-spelling table, not a
# standard. Incompleteness is safe because an unrecognised spelling refuses; it
# can never land in the wrong family. Spellings are aligned with the table
# already in tools/mnemonics.py (see spec open question 5).
UNIT_SYNONYMS: dict[str, str] = {
    # length / depth / caliper
    "M": "M", "METER": "M", "METERS": "M", "METRE": "M", "METRES": "M",
    "F": "FT", "FT": "FT", "FEET": "FT", "FOOT": "FT", "'": "FT",
    "FTUS": "FT_US", "FT_US": "FT_US", "FT-US": "FT_US", "USFT": "FT_US",
    "SURVEYFT": "FT_US",
    "IN": "IN", "INCH": "IN", "INCHES": "IN", "INS": "IN", '"': "IN",
    "CM": "CM", "MM": "MM",
    # density
    "G/CM3": "G/CM3", "G/CM^3": "G/CM3", "G/CM**3": "G/CM3", "G/C3": "G/CM3",
    "G/CC": "G/CM3", "GM/CC": "G/CM3", "GM/CM3": "G/CM3", "GCC": "G/CM3",
    "KG/M3": "KG/M3", "KG/M^3": "KG/M3", "K/M3": "KG/M3", "KGM3": "KG/M3",
    "MG/M3": "MG/M3", "MG/M^3": "MG/M3",
    "LB/FT3": "LB/FT3", "LBM/FT3": "LB/FT3", "PPCF": "LB/FT3",
    # fraction vs percent
    "V/V": "V/V", "VV": "V/V", "DEC": "V/V", "DECIMAL": "V/V", "FRAC": "V/V",
    "FRACTION": "V/V", "VDEC": "V/V", "V/V_DEC": "V/V",
    "%": "PCT", "PCT": "PCT", "PERCENT": "PCT", "PU": "PCT", "P.U": "PCT",
    "PUC": "PCT", "%POR": "PCT", "PERC": "PCT",
    # resistivity
    "OHMM": "OHM-M", "OHM-M": "OHM-M", "OHM.M": "OHM-M", "OHM*M": "OHM-M",
    "OHM_M": "OHM-M", "OHM M": "OHM-M", "OHMSM": "OHM-M", "OHMS-M": "OHM-M",
    "OHMM2/M": "OHM-M", "OHM-METER": "OHM-M", "OHM-METRE": "OHM-M",
    "OHMMETER": "OHM-M",
    # transit time
    "US/F": "USEC/FT", "US/FT": "USEC/FT", "USEC/FT": "USEC/FT",
    "USEC/F": "USEC/FT", "USFT-1": "USEC/FT", "USECPF": "USEC/FT",
    "US/M": "USEC/M", "USEC/M": "USEC/M",
    # potential
    "V": "V", "VOLT": "V", "VOLTS": "V",
    "MV": "MV", "MVOLT": "MV", "MVOLTS": "MV", "MILLIVOLT": "MV",
    "MILLIVOLTS": "MV",
    # photoelectric effect
    "B/E": "B/E", "BARNS/E": "B/E", "B/ELEC": "B/E", "BE": "B/E",
    # temperature. NOTE: bare "F" is deliberately absent - see AMBIGUOUS_SPELLINGS.
    "DEGF": "DEGF", "DEG F": "DEGF", "FAHRENHEIT": "DEGF",
    "DEGC": "DEGC", "DEG C": "DEGC", "C": "DEGC", "CELSIUS": "DEGC",
    "DEGK": "DEGK", "K": "DEGK", "KELVIN": "DEGK",
    "DEGR": "DEGR", "R": "DEGR", "RANKINE": "DEGR",
    # calibration standards - recognised so they can be refused with a reason
    "GAPI": "GAPI", "APIGR": "GAPI", "GRAPI": "GAPI",
    "NAPI": "NAPI", "APINEU": "NAPI", "APIN": "NAPI",
    "API": "API", "APIU": "API", "API UNITS": "API",
}

# `F` is the LAS depth-unit spelling in the very field table this tool is
# anchored to ("STRT .F | nnnn.nn | : Start Depth", LAS_UNIT_FIELD) and it is
# also the obvious spelling of Fahrenheit. Feet and degrees Fahrenheit are not
# the same quantity, so the token is resolved from whatever is on the other side
# of the conversion, and refused outright when that does not settle it. No other
# spelling in the table has this problem: nothing in the corpus writes `.C` for
# centimetres.
AMBIGUOUS_SPELLINGS: dict[str, tuple[str, str]] = {
    # token: (reading if the other side is a length, reading if it is a temperature)
    "F": ("FT", "DEGF"),
}

#: Mnemonics that mean a neutron porosity. Used only to ADD the matrix
#: requirement, never to remove one, so a gap here cannot produce a silent
#: success - it can only fail to catch a caller who also forgot to say `kind`.
NEUTRON_MNEMONICS = frozenset({
    "NPHI", "PHIN", "NPOR", "TNPH", "CNL", "CNC", "NEUT", "NEU", "NPRL",
    "NPSS", "NPLS", "NPDL", "NPHI_LS", "NPHI_SS", "DSN", "SNP",
})
NEUTRON_KIND = "neutron_porosity"

#: The lithologies a neutron curve can be referenced to (asquith#19: "apparent
#: limestone, sandstone, or dolomite porosity units").
NEUTRON_MATRICES = frozenset({"limestone", "sandstone", "dolomite"})

KNOWN_KINDS = frozenset({
    NEUTRON_KIND, "depth", "density", "porosity", "saturation", "resistivity",
    "transit_time", "caliper", "temperature", "gamma_ray", "sp", "pe",
    "volume_fraction",
})

# ---------------------------------------------------------------------------
# Fraction ambiguity band - OWNED, PROVISIONAL
# ---------------------------------------------------------------------------
# No source states a cutoff. A porosity of 15 is 15% or 0.15 depending on
# convention and guessing wrong is 100x, so where the declared label and the
# magnitude disagree the tool refuses instead of trusting either. The bounds are
# the only two things that are certain: a fraction cannot exceed 1 and still be a
# fraction, and a percent below 1 is a tenth of a porosity unit.
FRACTION_MAX = 1.0    # |v| above this is not a fraction
PERCENT_MIN = 1.0     # |v| below this, declared as percent, reads as a fraction
PERCENT_MAX = 100.0   # |v| above this is neither convention
AMBIGUITY_BASIS = "OWNED, PROVISIONAL - no corpus source states a cutoff; see spec open question 2"


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------
def _clean(token: str) -> str:
    """Normalise a raw unit spelling for lookup. Casing and padding only.

    A trailing period is dropped because LAS writes the unit in a dot-delimited
    field ("STRT .F"), so parsers hand over `F.` as readily as `F`. Interior
    periods are kept: `OHM.M` and `P.U.` differ from each other by them.
    """
    return token.strip().strip("()").strip().rstrip(".").upper()


def canonical_unit(unit: str, other: str | None = None) -> str | None:
    """Canonical token for a raw unit spelling, or None if unrecognised.

    A lookup, not a measurement, so it returns a token rather than a Quantity -
    same shape as `matrix_constant_lookup` in tools/petrophysics.py. `other` is
    the unit on the far side of the conversion and is used only to settle the
    handful of spellings that mean two things (`F` is both the LAS depth unit and
    Fahrenheit).
    """
    if not isinstance(unit, str):
        raise TypeError(f"unit must be a string, got {type(unit).__name__}")
    return _canonical(_clean(unit), _clean(other) if isinstance(other, str) else None)


def _canonical(token: str, other: str | None = None) -> str | None:
    """Canonical token, or None for both 'not known' and 'known but ambiguous'.

    The two are distinguished by the caller (`token in AMBIGUOUS_SPELLINGS`) so
    the refusals can say different things.
    """
    if token in AMBIGUOUS_SPELLINGS:
        length_sense, temp_sense = AMBIGUOUS_SPELLINGS[token]
        if other is None or other in AMBIGUOUS_SPELLINGS:
            return None
        resolved_other = UNIT_SYNONYMS.get(other)
        if resolved_other is None:
            return None
        return temp_sense if resolved_other in TEMPERATURE_UNITS else length_sense
    return UNIT_SYNONYMS.get(token)


def _family(token: str) -> str | None:
    if token in TEMPERATURE_UNITS:
        return TEMPERATURE_FAMILY
    if token in API_SCALES:
        return "api"
    row = SCALAR_UNITS.get(token)
    return row[0] if row else None


def _vocabulary(family: str) -> tuple[str, ...]:
    if family == TEMPERATURE_FAMILY:
        return tuple(sorted(TEMPERATURE_UNITS))
    return tuple(sorted(t for t, r in SCALAR_UNITS.items() if r[0] == family))


def _known_tokens() -> tuple[str, ...]:
    return tuple(sorted(set(SCALAR_UNITS) | set(TEMPERATURE_UNITS) | set(API_SCALES)))


# ---------------------------------------------------------------------------
# The gates
# ---------------------------------------------------------------------------
def _is_neutron(kind: str | None, mnemonic: str | None) -> bool:
    if kind == NEUTRON_KIND:
        return True
    if mnemonic and _clean(mnemonic).replace("-", "_") in NEUTRON_MNEMONICS:
        return True
    return False


def _api_gate(src: str, dst: str, raw_from: str, raw_to: str) -> Refusal | None:
    """Rule 1. API is a calibration standard, not a unit (beg#58)."""
    if src not in API_SCALES and dst not in API_SCALES:
        return None
    if src == dst and src != "API":
        return None  # identity no-op; handled by the caller, flagged there
    named = ", ".join(f"{t}: {API_SCALES[t]}" for t in (src, dst) if t in API_SCALES)
    return Refusal(
        reason=(
            f"cannot convert {raw_from!r} to {raw_to!r}: API is a calibration standard, "
            "not a unit. The corpus names two unrelated API scales - one for the "
            "calibration of gamma-ray counters, the other for neutron detectors - and "
            f"there is no factor between them or out of either ({named})"
        ),
        needed=(
            "a measurement in a physical unit; an API reading converts to porosity or "
            "shale volume only through a tool-specific chart, which is neutron_porosity_correct "
            "(#27) territory and is not in the corpus",
        ),
        source=BEG_API,
    )


def _neutron_gate(matrix: str | None, to_matrix: str | None,
                  raw_from: str, raw_to: str) -> Refusal | None:
    """Rule 2. The matrix reference travels with the value, or nothing does."""
    if matrix is None:
        return Refusal(
            reason=(
                f"cannot convert a neutron porosity from {raw_from!r} to {raw_to!r} with no "
                "declared matrix reference. Neutron curves are recorded in units referenced "
                "to a lithology - apparent limestone, sandstone or dolomite porosity units - "
                "and a value stripped of that reference is corrupt, not converted "
                "(asquith#19; a limestone-referenced curve shows a false crossover in a "
                "sandstone, asquith#28). The corpus does not support defaulting the matrix: "
                "it says the reference is 'usually either limestone or sandstone, depending "
                "on the geologic environment'"
            ),
            needed=(
                "matrix= one of limestone / sandstone / dolomite, read from the log heading "
                "or the LAS ~P matrix parameter (header_extract, #4)",
            ),
            source=ASQUITH_NEUTRON,
        )
    if to_matrix is not None and to_matrix != matrix:
        return Refusal(
            reason=(
                f"a {matrix} neutron porosity cannot be re-referenced to {to_matrix} by unit "
                "conversion. Moving a neutron curve between matrix references is a "
                "tool-specific chart correction (asquith#19), not arithmetic on the unit"
            ),
            needed=("neutron_porosity_correct (#27), with the chart for the specific tool",),
            source=ASQUITH_NEUTRON,
        )
    return None


def _ambiguity_gate(value: float, src: str, dst: str, raw_from: str) -> Refusal | None:
    """Fraction vs percent. Owned and provisional; refuses rather than picks."""
    magnitude = abs(value)
    if src == "PCT" and dst == "V/V" and 0.0 < magnitude < PERCENT_MIN:
        return Refusal(
            reason=(
                f"{value:g} declared as {raw_from!r} is ambiguous: as a percent it is "
                f"{value / 100.0:g} v/v, but the magnitude already reads as a fraction "
                f"({value:g} v/v = {value * 100.0:g}%). Converting resolves it one way or the "
                "other and the wrong way is a factor of 100"
            ),
            needed=(
                "confirmation of whether the label or the magnitude is right - the curve's "
                "full range usually settles it - then trust_declared_unit=True to convert on "
                "the declared label",
            ),
            source=OWNED,
        )
    if src == "V/V" and dst == "PCT" and FRACTION_MAX < magnitude <= PERCENT_MAX:
        return Refusal(
            reason=(
                f"{value:g} declared as {raw_from!r} is ambiguous: a fraction cannot exceed "
                f"1.0, so this is most likely already a percent ({value:g}% = "
                f"{value / 100.0:g} v/v). Converting would multiply it by 100 again"
            ),
            needed=(
                "confirmation of whether the label or the magnitude is right, then "
                "trust_declared_unit=True to convert on the declared label",
            ),
            source=OWNED,
        )
    if src == "V/V" and dst == "PCT" and magnitude > PERCENT_MAX:
        return Refusal(
            reason=(
                f"{value:g} declared as {raw_from!r} fits neither convention: it is not a "
                f"fraction (>{FRACTION_MAX:g}) and not a percent (>{PERCENT_MAX:g}%)"
            ),
            needed=("the curve's real unit, or null_scrub (#12) if this is a sentinel value",),
            source=OWNED,
        )
    return None


# ---------------------------------------------------------------------------
# The conversion
# ---------------------------------------------------------------------------
def _validate_call(value: Any, from_unit: Any, to_unit: Any, kind: str | None,
                   matrix: str | None, to_matrix: str | None,
                   temperature_sense: str | None) -> None:
    """Programmer error only. Everything a file can cause is a Refusal, not this."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"value must be a real number, got {type(value).__name__}")
    for name, unit in (("from_unit", from_unit), ("to_unit", to_unit)):
        if not isinstance(unit, str):
            raise TypeError(f"{name} must be a string, got {type(unit).__name__}")
    if kind is not None and kind not in KNOWN_KINDS:
        raise ValueError(f"unknown kind {kind!r}; known: {sorted(KNOWN_KINDS)}")
    for name, m in (("matrix", matrix), ("to_matrix", to_matrix)):
        if m is not None and m not in NEUTRON_MATRICES:
            raise ValueError(f"unknown {name} {m!r}; known: {sorted(NEUTRON_MATRICES)}")
    if temperature_sense is not None and temperature_sense not in ("absolute", "delta"):
        raise ValueError(
            f"unknown temperature_sense {temperature_sense!r}; use 'absolute' or 'delta'"
        )


def _resolve(value: float, from_unit: str, to_unit: str, kind: str | None,
             mnemonic: str | None, matrix: str | None, matrix_source: str | None,
             to_matrix: str | None, temperature_sense: str | None,
             trust_declared_unit: bool) -> Refusal | tuple[float, dict, dict, tuple]:
    """Everything both entry points share. Refusal, or (value, inputs, assumptions, flags)."""
    _validate_call(value, from_unit, to_unit, kind, matrix, to_matrix, temperature_sense)

    if not math.isfinite(value):
        return Refusal(
            reason=f"value {value!r} is not finite; a null sentinel or a failed read cannot "
                   "be converted",
            needed=("null_scrub (#12) before any arithmetic",),
            source=OWNED,
        )

    raw_from, raw_to = from_unit, to_unit
    tok_from, tok_to = _clean(from_unit), _clean(to_unit)
    if not tok_from or not tok_to:
        missing = "from_unit" if not tok_from else "to_unit"
        return Refusal(
            reason=f"no unit declared ({missing} is empty); a value with no declared unit "
                   "cannot be converted, and assuming one is how a 100x error gets in",
            needed=("the unit as declared in the LAS ~C or ~W field for this value",),
            source=LAS_UNIT_FIELD,
        )

    src = _canonical(tok_from, tok_to)
    dst = _canonical(tok_to, tok_from)

    # R2 before R2b (spec table order). A token that is in no table at all is
    # named even when the other side is the ambiguous `F`, because the unknown
    # token is also *why* `F` did not resolve: reporting only the ambiguity sends
    # the caller to fix the side that was fine.
    unknown = [raw for raw, tok in ((raw_from, tok_from), (raw_to, tok_to))
               if tok not in AMBIGUOUS_SPELLINGS and tok not in UNIT_SYNONYMS]
    if unknown:
        return Refusal(
            reason=f"unrecognised unit token(s) {', '.join(repr(u) for u in unknown)}. LAS "
                   "declares a unit per field but fixes no vocabulary for it, so this table "
                   "is a vendor-spelling table and is incomplete by construction",
            needed=(f"one of: {', '.join(_known_tokens())}",
                    "or an added spelling in UNIT_SYNONYMS, if this token is a real one"),
            source=LAS_UNIT_FIELD,
        )

    unresolved = [raw for raw, tok, canon in ((raw_from, tok_from, src), (raw_to, tok_to, dst))
                  if canon is None and tok in AMBIGUOUS_SPELLINGS]
    if unresolved:
        senses = ", ".join(
            f"{raw!r} is either {AMBIGUOUS_SPELLINGS[_clean(raw)][0]} or "
            f"{AMBIGUOUS_SPELLINGS[_clean(raw)][1]}" for raw in unresolved
        )
        return Refusal(
            reason=f"ambiguous unit spelling: {senses}. LAS writes '.F' for feet in its own "
                   "field table (STRT .F : Start Depth) and F is also Fahrenheit; the other "
                   "side of this conversion does not settle which is meant",
            needed=("the unit spelled unambiguously - FT or DEGF",),
            source=LAS_UNIT_FIELD,
        )

    # Both tokens are known and both ambiguities are settled by here.
    api_refusal = _api_gate(src, dst, raw_from, raw_to)
    if api_refusal is not None:
        return api_refusal

    fam_from, fam_to = _family(src), _family(dst)
    if fam_from != fam_to:
        return Refusal(
            reason=f"{raw_from!r} ({fam_from}) and {raw_to!r} ({fam_to}) are different physical "
                   "quantities; this is a mislabelled curve or a wrong target, not a conversion",
            needed=(f"a target in the {fam_from} family: {', '.join(_vocabulary(fam_from))}",),
            source=OWNED,
        )

    is_neutron = _is_neutron(kind, mnemonic)
    flags: list[str] = []
    assumptions: dict[str, Any] = {"basis": "definitional", "family": fam_from}
    if kind is not None:
        assumptions["kind"] = kind
    if mnemonic:
        assumptions["mnemonic"] = mnemonic

    if is_neutron:
        neutron_refusal = _neutron_gate(matrix, to_matrix, raw_from, raw_to)
        if neutron_refusal is not None:
            return neutron_refusal
        # The reference travels with the value. This is the point of the gate.
        assumptions["matrix"] = matrix
        assumptions["matrix_source"] = matrix_source or "caller-asserted"
        assumptions["matrix_rule"] = (
            "neutron porosity is referenced to a lithology (asquith#19); the reference is "
            "carried, never dropped and never defaulted"
        )
        if not matrix_source:
            flags.append(
                "matrix reference asserted by the caller with no header provenance; "
                "confirm against the log heading or the LAS ~P matrix parameter"
            )

    # Ambiguity gate, only where the two conventions are 100x apart.
    if fam_from == "fraction" and src != dst:
        ambiguity = _ambiguity_gate(value, src, dst, raw_from)
        if ambiguity is not None:
            if not trust_declared_unit:
                return ambiguity
            flags.append(
                f"ambiguity band overridden by the caller: {ambiguity.reason.split(':')[0]}"
                f" - converted on the declared unit {raw_from!r}"
            )
        assumptions["ambiguity_band"] = AMBIGUITY_BASIS
        assumptions["trust_declared_unit"] = trust_declared_unit

    inputs = {
        # The catalog's rule: every converted value retains its original.
        "value": value,
        "unit": raw_from,
        "canonical_from": src,
        "canonical_to": dst,
    }

    if fam_from == TEMPERATURE_FAMILY:
        if temperature_sense is None:
            return Refusal(
                reason=f"a {raw_from!r} to {raw_to!r} conversion is affine, not scalar: an "
                       "absolute temperature and a temperature difference convert differently "
                       "(18 degF is 10 degC as a difference and -7.78 degC as a reading), and "
                       "the unit does not say which this is",
                needed=("temperature_sense='absolute' for a reading (BHT, formation "
                        "temperature) or 'delta' for a difference or an interval",),
                source=OWNED,
            )
        s_from, o_from, note_from = TEMPERATURE_UNITS[src]
        s_to, o_to, note_to = TEMPERATURE_UNITS[dst]
        if src == dst:
            # Identity. Round-tripping the value through kelvin and back is the
            # same arithmetic in exact terms but not in floating point: 100 degF
            # came back as 99.99999999999997, so a value converted to its own
            # unit stopped comparing equal to itself. A conversion between a unit
            # and itself is exactly the value, by definition.
            out = float(value)
        elif temperature_sense == "delta":
            out = value * s_from / s_to
        else:
            out = (value * s_from + o_from - o_to) / s_to
        assumptions.update({
            "temperature_sense": temperature_sense,
            "scale_from": s_from, "offset_from_K": o_from,
            "scale_to": s_to, "offset_to_K": o_to,
            "definition_from": note_from, "definition_to": note_to,
        })
        if temperature_sense == "delta":
            flags.append("temperature difference: scale applied, scale offsets dropped")
        return out, inputs, assumptions, tuple(flags)

    if src in API_SCALES:  # identity no-op that survived the gate
        assumptions["api_scale"] = API_SCALES[src]
        flags.append(
            "API is a calibration standard, not a unit (beg#58): the value is unchanged and "
            "no conversion was applied"
        )
        return float(value), inputs, assumptions, tuple(flags)

    f_from, note_from = SCALAR_UNITS[src][1], SCALAR_UNITS[src][2]
    f_to, note_to = SCALAR_UNITS[dst][1], SCALAR_UNITS[dst][2]
    if src == dst:
        # Identity. `value * f / f` is not `value` in floating point when f is not a
        # power of two: 7.5 FT_US -> FT_US came back as 7.499999999999999, and the
        # recorded factor of 1.0 then did not reproduce the answer. A unit converted
        # to itself is the value, exactly - that is what "same unit" means.
        out = float(value)
    else:
        out = value * f_from / f_to
    assumptions.update({
        "factor": f_from / f_to,
        "definition_from": note_from,
        "definition_to": note_to,
    })
    if "FT_US" in (src, dst):
        flags.append(
            "US survey foot used (1200/3937 m, 2 ppm longer than the international foot: "
            "0.02 ft over 10,000 ft); confirm which foot the depths were surveyed in"
        )
    return out, inputs, assumptions, tuple(flags)


def unit_convert(value: float, from_unit: str, to_unit: str, *,
                 kind: str | None = None, mnemonic: str | None = None,
                 matrix: str | None = None, matrix_source: str | None = None,
                 to_matrix: str | None = None, temperature_sense: str | None = None,
                 trust_declared_unit: bool = False) -> Quantity | Refusal:
    """Convert one declared value, or refuse and say why.

    The result always carries the original value and the original unit spelling
    in `inputs`, per the catalog: a converted number that has lost what it was is
    not traceable.
    """
    resolved = _resolve(value, from_unit, to_unit, kind, mnemonic, matrix, matrix_source,
                        to_matrix, temperature_sense, trust_declared_unit)
    if isinstance(resolved, Refusal):
        return resolved
    out, inputs, assumptions, flags = resolved
    return Quantity(
        value=out,
        unit=inputs["canonical_to"],
        method=f"unit_convert {inputs['canonical_from']} -> {inputs['canonical_to']} "
               f"(definitional)",
        source=OWNED,
        inputs=inputs,
        assumptions=assumptions,
        flags=flags,
    )


def unit_convert_range(low: float, high: float, from_unit: str, to_unit: str,
                       **kwargs: Any) -> Range | Refusal:
    """The same conversion applied to a band. Originals ride in `members`."""
    lo = unit_convert(low, from_unit, to_unit, **kwargs)
    if isinstance(lo, Refusal):
        return lo
    hi = unit_convert(high, from_unit, to_unit, **kwargs)
    if isinstance(hi, Refusal):
        return hi
    lo_v, hi_v = lo.value, hi.value
    if lo_v > hi_v:  # every conversion here is monotonic; a swap means low > high came in
        lo_v, hi_v = hi_v, lo_v
    members = {"low_in": float(low), "high_in": float(high)}
    if "factor" in lo.assumptions:
        members["factor"] = float(lo.assumptions["factor"])
    return Range(low=lo_v, high=hi_v, unit=lo.unit, method=lo.method, source=OWNED,
                 members=members)


def convert_neutron_porosity(value: float, from_unit: str, to_unit: str, matrix: str, *,
                             matrix_source: str | None = None, to_matrix: str | None = None,
                             mnemonic: str | None = None,
                             trust_declared_unit: bool = False) -> Quantity | Refusal:
    """Neutron porosity conversion with the matrix reference required positionally.

    Same path as `unit_convert`; the signature is the point. A caller cannot drop
    the matrix by forgetting a keyword, which is the failure mode the rule
    exists to stop.
    """
    return unit_convert(
        value, from_unit, to_unit, kind=NEUTRON_KIND, mnemonic=mnemonic,
        matrix=matrix, matrix_source=matrix_source, to_matrix=to_matrix,
        trust_declared_unit=trust_declared_unit,
    )
