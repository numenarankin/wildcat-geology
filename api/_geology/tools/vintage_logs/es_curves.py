"""#96 `es_curve_identify` — classify which vintage ES curves are present.

Staging fragment for `tools/petrophysics.py`. See `specs/96-es_curve_identify.md`.

The non-obvious decisions, in one place:

**Why this returns a structure and not a `Quantity`.** The question is "which of the four
ES measurements is in this file", which is a classification per curve. `curve_inventory`
(#3) set the precedent: a structured tool returns its own frozen dataclass whose numeric
member is a `Quantity` and whose failure mode is a `Refusal`. `completeness` is that
`Quantity`.

**Why `spacing_in` may be `None`.** Vintage curve naming is not standardised and this
corpus has no canonical mnemonic table (`tools/mnemonics.py` says so of its whole
dictionary). Identification is therefore a rule with confidence, not a lookup. A curve
labelled `NORM` with no spacing could be either normal, and `rt_from_long_normal` (#98)
will consume this answer: a 16-in. reading used as a 64-in. reading is a wrong Rt with no
outward sign. So the tool reports `ambiguous` with both candidates and leaves `spacing_in`
`None`. **There is no default spacing anywhere in this module.**

**Why Group A is duck-typed, not imported.** `curve_inventory` lives in `tools/las.py` and
`mnemonic_normalize` in `tools/mnemonics.py`. Both are taken as arguments so this module,
merging into `tools/petrophysics.py`, acquires no dependency on either. Nothing below
reads a field Group A does not already publish.
"""
from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range re-exported by module)


# --------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------
TRIESTE_ES = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#0"
TRIESTE_RT = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#1"
BEG_TIMELINE = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#34"
EPA_ELECTRICAL = "12-vintage-logs/epa-environmental-geophysics-electrical-methods#2"

ES_SOURCES = f"{TRIESTE_ES}; {BEG_TIMELINE}; {EPA_ELECTRICAL}"

# The sentence the whole tool hangs on.
SUITE_STATEMENT = (
    'trieste#0: "The conventional electrical survey (ES) usually consisted of an SP, '
    '16-in. normal, 64-in. normal, and 18-ft 8-in. lateral devices."'
)
SUITE_STATEMENT_2 = (
    'beg#34: ES logs "made four measurements: Spontaneous Potential (SP), 16-inch Short '
    'Normal (SN), 64-inch Long Normal (LN), and 18-ft, 8-inch Lateral Log (LAT)."'
)
NORMAL_SPACING_STATEMENT = (
    'trieste#0: "The distance AM is called the spacing (16-in. spacing for the short '
    'normal, 64-in. spacing for the long normal)".'
)
LATERAL_SPACING_STATEMENT = (
    'trieste#0: "The spacing AO is 18 ft 8 in." (lateral device, Fig. 7-2); '
    '"all electrodes are in the borehole, with N located 50 ft 10 in. above M."'
)
OTHER_SPACINGS_STATEMENT = (
    'epa#2: "The most common AM spacings are 40 and 162 cm (16 and 64 in); however, some '
    'loggers have other spacings available, such as 10, 20, 40 and 81 cm (4, 8, 16, and '
    '32 in)."'
)
IES_STATEMENT = (
    'beg#34: "The first induction tools that were used in Boonsville field were the '
    'Induction Electric Logs (IES logs), which provided three measurements: Spontaneous '
    'Potential (SP), 16-inch Short Normal (SN), and Deep Induction (ILD)."'
)
SUCCESSOR_STATEMENT = (
    'trieste#1: "The focusing electrode tools include the laterolog and SFL* spherically '
    'focused devices. These tools are much superior to the ES devices..."'
)
MICROLOG_STATEMENT = (
    'beg#34: "An additional log that was commonly run in Boonsville field was the '
    'microlog, which provided three measurements: Caliper, Micro Normal (2 inches), and '
    'Micro Inverse (1 inch x 1 inch)."'
)
APPARENT_R_CAVEAT = (
    'trieste#0: "the apparent resistivity, Ra, recorded by each device is affected by the '
    "resistivities and geometrical dimensions of all media around the device (borehole, "
    'invaded and uncontaminated zones, and adjacent beds)." No ES curve reads Rt directly.'
)

# Era window. beg#34 dates the ES to the 1940s-50s and the Short Normal's replacement to
# the late 1960s. `tools/mnemonics.py` already marks these windows advisory, because
# beg#34 calls its own figure "a rough time line" and it describes one field. Advisory
# here too: era never classifies a curve, it only ever raises a flag.
ERA_ES_FIRST = 1945
ERA_ES_LAST = 1969
ERA_STATEMENT = (
    'beg#34: "Wells were logged from the discovery of the field in 1945." / "In the late '
    "1960's, the Short Normal was replaced by focused shallow resistivity tools, such as "
    'the Spherically Focused Log (SFL)." Advisory only - beg#34 calls its own figure "a '
    'rough time line".'
)


# --------------------------------------------------------------------------
# The ES taxonomy
# --------------------------------------------------------------------------
ROLE_SP = "sp"
ROLE_SHORT_NORMAL = "short_normal_16in"
ROLE_LONG_NORMAL = "long_normal_64in"
ROLE_LATERAL = "lateral_18ft8in"

DEVICE_SP = "sp"
DEVICE_NORMAL = "normal"
DEVICE_LATERAL = "lateral"
DEVICE_MICRO = "micro"
DEVICE_POST_ES = "post_es"
DEVICE_UNKNOWN = "unknown"

STATUS_IDENTIFIED = "identified"
STATUS_AMBIGUOUS = "ambiguous"
STATUS_NONSTANDARD = "nonstandard_spacing"
STATUS_OUTSIDE = "outside_suite"
STATUS_UNIDENTIFIED = "unidentified"

CONF_EXPLICIT = "explicit_spacing"
CONF_CITED_MNEMONIC = "cited_mnemonic"
CONF_CITED_SUITE = "cited_suite"
CONF_MNEMONIC_DIGITS = "mnemonic_digits"

# 18 ft 8 in = 18 * 12 + 8 = 224 in.  trieste#0, "The spacing AO is 18 ft 8 in."
LATERAL_AO_IN = 18 * 12 + 8


@dataclass(frozen=True)
class EsDevice:
    """One measurement of the conventional ES, as the sources define it."""

    role: str
    device: str
    label: str
    spacing_in: float | None
    spacing_basis: str
    measures: str
    depth_of_investigation: str
    unit: str
    source: str


# The suite. Four measurements, in the order both sources print them.
ES_SUITE: tuple[EsDevice, ...] = (
    EsDevice(
        role=ROLE_SP,
        device=DEVICE_SP,
        label="spontaneous potential",
        spacing_in=None,  # not a spaced resistivity device; no AM/AO applies
        spacing_basis=(
            "the SP is not a spaced resistivity device; trieste#0 states no AM or AO for "
            "it, so no spacing is asserted"
        ),
        measures="spontaneous potential of the formation, in millivolts",
        depth_of_investigation=(
            "not defined - the SP is a potential measurement, not a resistivity device; "
            "the source states no depth of investigation for it"
        ),
        unit="MV",
        source=f"{TRIESTE_ES}; {BEG_TIMELINE}",
    ),
    EsDevice(
        role=ROLE_SHORT_NORMAL,
        device=DEVICE_NORMAL,
        label="16-in. short normal",
        spacing_in=16.0,
        spacing_basis=NORMAL_SPACING_STATEMENT,
        measures=(
            "apparent resistivity at AM = 16 in.; the invaded zone Ri - epa#2: short "
            "normal devices 'are considered to investigate only the invaded zone'"
        ),
        depth_of_investigation=(
            "shallowest of the ES resistivity logs (trieste#0: 'the 18-ft 8-in. lateral "
            "has the deepest investigation and the 16-in. normal the shallowest'); epa#2 "
            "puts the volume at a sphere of radius approximately twice AM, i.e. ~32 in."
        ),
        unit="OHM-M",
        source=f"{TRIESTE_ES}; {EPA_ELECTRICAL}",
    ),
    EsDevice(
        role=ROLE_LONG_NORMAL,
        device=DEVICE_NORMAL,
        label="64-in. long normal",
        spacing_in=64.0,
        spacing_basis=NORMAL_SPACING_STATEMENT,
        measures=(
            "apparent resistivity at AM = 64 in.; epa#2: long normal devices 'are "
            "considered to investigate both the invaded zone and the zone where native "
            "formation water is found'"
        ),
        depth_of_investigation=(
            "deeper than the 16-in. normal, shallower than the lateral (trieste#0); "
            "epa#2 volume ~ sphere of radius twice AM, i.e. ~128 in."
        ),
        unit="OHM-M",
        source=f"{TRIESTE_ES}; {EPA_ELECTRICAL}",
    ),
    EsDevice(
        role=ROLE_LATERAL,
        device=DEVICE_LATERAL,
        label="18-ft 8-in. lateral",
        spacing_in=float(LATERAL_AO_IN),
        spacing_basis=LATERAL_SPACING_STATEMENT,
        measures=(
            "apparent resistivity at AO = 18 ft 8 in. (224 in.); epa#2: 'Lateral logs are "
            "designed to measure resistivity beyond the invaded zone'. The curve is "
            "dissymmetrical about a bed (trieste#1)"
        ),
        depth_of_investigation=(
            "deepest of the ES resistivity logs (trieste#0). beg#34 limits it: it read "
            "close to true resistivity 'only in sandstones that were at least five times "
            "as thick as the measure length (18 ft, 8 inches) of the tool'"
        ),
        unit="OHM-M",
        source=f"{TRIESTE_ES}; {BEG_TIMELINE}; {EPA_ELECTRICAL}",
    ),
)

ES_ROLES: tuple[str, ...] = tuple(d.role for d in ES_SUITE)
_BY_ROLE: dict[str, EsDevice] = {d.role: d for d in ES_SUITE}
ES_RESISTIVITY_ROLES: tuple[str, ...] = (
    ROLE_SHORT_NORMAL,
    ROLE_LONG_NORMAL,
    ROLE_LATERAL,
)


# --------------------------------------------------------------------------
# Spacings the corpus names
# --------------------------------------------------------------------------
# The two ES normals, plus the other AM spacings epa#2 says loggers had available. A
# spacing in this table is *recognised*; only 16 and 64 are ES roles.
NORMAL_SPACINGS_IN: tuple[tuple[float, str, str], ...] = (
    (4.0, "10 cm (4 in) normal", OTHER_SPACINGS_STATEMENT),
    (8.0, "20 cm (8 in) normal", OTHER_SPACINGS_STATEMENT),
    (16.0, "16-in. short normal", NORMAL_SPACING_STATEMENT),
    (32.0, "81 cm (32 in) normal", OTHER_SPACINGS_STATEMENT),
    (64.0, "64-in. long normal", NORMAL_SPACING_STATEMENT),
)

# The ES lateral, plus the shorter lateral epa#2 names for groundwater tools.
# 1.8 m = 1.8 * 39.3700787 = 70.866 in.
LATERAL_SPACINGS_IN: tuple[tuple[float, str, str], ...] = (
    (70.866, "1.8 m groundwater lateral", OTHER_SPACINGS_STATEMENT),
    (float(LATERAL_AO_IN), "18-ft 8-in. lateral", LATERAL_SPACING_STATEMENT),
)

# OWNED, PROVISIONAL. Neither source states a matching tolerance; both state unit
# equivalences whose rounding is the only thing these have to absorb:
#   epa#2 prints 162 cm for the 64-in normal -> 162/2.54 = 63.7795 in, 0.22 in off.
#   epa#2 prints 5.7 m for the 18-ft 8-in lateral -> 224.409 in, 0.41 in off.
# +/-1.0 in cannot confuse the nearest neighbours in {4, 8, 16, 32, 64}.
NORMAL_SPACING_TOL_IN = 1.0
LATERAL_SPACING_TOL_IN = 4.0
SPACING_TOL_BASIS = (
    "OWNED/PROVISIONAL: the sources state unit equivalences (162 cm = 64 in, 5.7 m = "
    "18 ft 8 in) but no matching tolerance. +/-1.0 in on normals and +/-4.0 in on the "
    "lateral absorb exactly those printed roundings (63.7795 and 224.409 in)."
)

IN_PER_CM = 1.0 / 2.54
IN_PER_M = 100.0 / 2.54          # 39.3700787...
IN_PER_FT = 12.0


# --------------------------------------------------------------------------
# Mnemonic tables
# --------------------------------------------------------------------------
# Every ES row below is a rule over cited prose, not a lookup: this corpus has no
# canonical vintage mnemonic table (tools/mnemonics.py: the KGS curve-mnemonic table is
# not ingested, so absence means unadjudicated). beg#34 names SP, SN, LN and LAT; the
# spelling variants are this project's.
ES_MNEMONICS: dict[str, tuple[str, str]] = {
    # mnemonic -> (role, why)
    "SP": (ROLE_SP, SUITE_STATEMENT_2),
    "SPC": (ROLE_SP, "OWNED spelling variant of SP"),
    "SPON": (ROLE_SP, "OWNED spelling variant of SP"),
    "SN": (ROLE_SHORT_NORMAL, SUITE_STATEMENT_2),
    "SN16": (ROLE_SHORT_NORMAL, "OWNED spelling variant of SN carrying its spacing"),
    "SHN": (ROLE_SHORT_NORMAL, "OWNED spelling variant of SN"),
    "LN": (ROLE_LONG_NORMAL, SUITE_STATEMENT_2),
    "LN64": (ROLE_LONG_NORMAL, "OWNED spelling variant of LN carrying its spacing"),
    "LGN": (ROLE_LONG_NORMAL, "OWNED spelling variant of LN"),
    "LAT": (ROLE_LATERAL, SUITE_STATEMENT_2),
    "LAT18": (ROLE_LATERAL, "OWNED spelling variant of LAT carrying its spacing"),
    "LATL": (ROLE_LATERAL, "OWNED spelling variant of LAT"),
}

# The microlog family: beg#34 calls it "An additional log that was commonly run" -
# adjacent to the ES, not one of its four measurements. Checked BEFORE any normal rule,
# because Micro Normal is 2 inches and would otherwise parse as a nonstandard ES normal.
MICRO_MNEMONICS: dict[str, str] = {
    "ML": "microlog",
    "MLOG": "microlog",
    "MN": "micro normal (2 in)",
    "MNOR": "micro normal (2 in)",
    "MI": "micro inverse (1 in x 1 in)",
    "MINV": "micro inverse (1 in x 1 in)",
    "CALI": "caliper (the microlog's third measurement)",
    "CAL": "caliper (the microlog's third measurement)",
}
MICRO_TOKENS: tuple[str, ...] = (
    "MICROLOG", "MICRO LOG", "MICRO NORMAL", "MICRO-NORMAL",
    "MICRO INVERSE", "MICRO-INVERSE", "MICRONORMAL", "MICROINVERSE",
)

# Post-ES devices. trieste#0 names the focusing-electrode family as the ES's successors;
# beg#34 names the induction, SFL, sonic, GR, CNL, FDC and PEF eras after it.
POST_ES_MNEMONICS: dict[str, str] = {
    "IL": (f"induction; {SUCCESSOR_STATEMENT}"),
    "ILD": ("deep induction (ILD); " + IES_STATEMENT),
    "ILM": ("medium induction; " + BEG_TIMELINE),
    "ILS": ("shallow induction; " + BEG_TIMELINE),
    "IND": ("induction; " + BEG_TIMELINE),
    "SFL": (
        'beg#34: "In the late 1960\'s, the Short Normal was replaced by focused shallow '
        'resistivity tools, such as the Spherically Focused Log (SFL)."'
    ),
    "SFLU": ("spherically focused log; " + BEG_TIMELINE),
    "LL": ("laterolog; " + SUCCESSOR_STATEMENT),
    "LL3": ("Laterolog 3; " + SUCCESSOR_STATEMENT),
    "LL7": ("Laterolog 7; " + SUCCESSOR_STATEMENT),
    "LL8": ("Laterolog 8; " + SUCCESSOR_STATEMENT),
    "LLD": ("deep laterolog of the DLL; " + SUCCESSOR_STATEMENT),
    "LLS": ("shallow laterolog of the DLL; " + SUCCESSOR_STATEMENT),
    "MLL": ('beg#34: MicroLaterlog, a later replacement for the microlog'),
    "MSFL": ('beg#34: MicroSFL, a later replacement for the microlog'),
    "PL": ('beg#34: Proximity log, a later replacement for the microlog'),
    "RXO": ("flushed-zone resistivity from a pad tool; post-ES"),
    "GR": (
        'beg#34: the gamma ray (GR) tool arrives with the late-1960s I/SFL suite, after '
        "the ES"
    ),
    "SGR": ("spectral gamma ray; post-ES"),
    "CGR": ("computed gamma ray; post-ES"),
    "RHOB": (
        'beg#34: "In the 1970\'s ... the Compensated Formation Density (FDC) devices '
        'became commonly used."'
    ),
    "DRHO": ("density correction; post-ES"),
    "FDC": ("Compensated Formation Density; " + BEG_TIMELINE),
    "NPHI": (
        'beg#34: "In the 1970\'s, two new tools, the Compensated Neutron (CNL) and the '
        'Compensated Formation Density (FDC) devices, became commonly used."'
    ),
    "CNL": ("Compensated Neutron; " + BEG_TIMELINE),
    "PHIN": ("neutron porosity; post-ES"),
    "DT": (
        'beg#34: the "borehole compensated sonic (BHS) tool" arrives with the late-1960s '
        "I/SFL suite"
    ),
    "AC": ("acoustic/sonic transit time; post-ES"),
    "PEF": (
        'beg#34: "In the 1980\'s, the density tool was enhanced to include a '
        'photoelectric effect measurement (PEF)."'
    ),
    "PE": ("photoelectric effect; " + BEG_TIMELINE),
    "EPT": ("microwave absorption tool; " + BEG_TIMELINE),
    "FMS": ("formation scanning tool; " + BEG_TIMELINE),
    "FMI": ("formation microimager; " + BEG_TIMELINE),
}

# Word tokens. LATEROLOG is scanned before LATERAL so "LATEROLOG 8" never reads as a
# lateral - the homonym trap tool-verification.md flags as failure mode 1.
POST_ES_TOKENS: tuple[str, ...] = (
    "LATEROLOG", "LATERO-LOG", "INDUCTION", "SPHERICALLY FOCUSED",
    "FOCUSED", "PROXIMITY", "GAMMA RAY", "NEUTRON", "DENSITY", "SONIC",
    "PHOTOELECTRIC",
)
INDUCTION_MNEMONICS: frozenset[str] = frozenset({"IL", "ILD", "ILM", "ILS", "IND"})
INDUCTION_TOKENS: tuple[str, ...] = ("INDUCTION",)

LATERAL_TOKENS: tuple[str, ...] = ("LATERAL",)
NORMAL_TOKENS: tuple[str, ...] = ("NORMAL", "NORM")
SP_TOKENS: tuple[str, ...] = (
    "SPONTANEOUS POTENTIAL", "SELF POTENTIAL", "SELF-POTENTIAL",
    "SPONTANEOUS-POTENTIAL", "SPONTANEOUS POT",
)
SHORT_TOKENS: tuple[str, ...] = ("SHORT", "SHRT")
LONG_TOKENS: tuple[str, ...] = ("LONG",)

# Unit spellings that mark a curve as a resistivity measurement. OWNED - the corpus gives
# the unit name ("ohm-meters", trieste#0) but no ASCII spelling list, same gap
# tools/mnemonics.py records for its own unit tokens.
RESISTIVITY_UNITS: frozenset[str] = frozenset(
    {"OHM-M", "OHMM", "OHM.M", "OHM_M", "OHMM2/M", "OHM-M2/M", "OHMS", "OHM",
     "OHM-METER", "OHM-METERS", "OHMMETER"}
)
POTENTIAL_UNITS: frozenset[str] = frozenset({"MV", "MILLIVOLT", "MILLIVOLTS", "M V"})

# Unit spellings stripped from the text before spacing parsing, so that the M of OHM-M
# is never read as a metre and the MV of an SP is never read as anything.
_UNIT_NOISE = (
    "OHM-METERS", "OHM-METER", "OHMMETER", "OHM-M2/M", "OHMM2/M",
    "OHM-M", "OHM_M", "OHM.M", "OHMM", "OHMS", "MMHO/M", "MILLIVOLTS",
    "MILLIVOLT", "MV",
)


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class EsCurveClass:
    """One curve, classified into the ES taxonomy, with the evidence that got it there.

    `spacing_in` is None unless evidence set it. There is no default and no inference
    from position, order or count - `rt_from_long_normal` (#98) depends on that.
    """

    mnemonic: str
    unit: str
    description: str
    device: str
    es_role: str | None
    status: str
    spacing_in: float | None
    spacing_basis: str
    candidates: tuple[str, ...]
    confidence: str | None
    evidence: tuple[str, ...]
    measures: str
    depth_of_investigation: str
    source: str
    flags: tuple[str, ...] = ()

    def __repr__(self) -> str:  # keeps test failures readable
        space = "-" if self.spacing_in is None else f"{self.spacing_in:g}in"
        return (
            f"EsCurveClass({self.mnemonic!r} -> {self.es_role or self.status}, "
            f"{space}, {self.confidence or 'no-confidence'})"
        )


@dataclass(frozen=True)
class EsSuiteIdentification:
    """What of the conventional ES this file holds, and what it does not."""

    curves: tuple[EsCurveClass, ...]
    present: dict[str, tuple[str, ...]]
    missing: tuple[str, ...]
    ambiguous: tuple[EsCurveClass, ...]
    unidentified: tuple[EsCurveClass, ...]
    nonstandard: tuple[EsCurveClass, ...]
    outside_suite: tuple[EsCurveClass, ...]
    completeness: Quantity
    suite: str
    source: str = ES_SOURCES
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)

    def role(self, role: str) -> tuple[EsCurveClass, ...]:
        """Every curve classified into this ES role - plural, because files repeat them."""
        if role not in ES_ROLES:
            raise ValueError(f"{role!r} is not an ES role; expected one of {ES_ROLES}")
        return tuple(c for c in self.curves if c.es_role == role)

    def has(self, role: str) -> bool:
        return bool(self.role(role))


# --------------------------------------------------------------------------
# Field access: mapping or object, matching curve_inventory's own accessor
# --------------------------------------------------------------------------
_MISSING = object()


def _field(record: Any, name: str, default: Any = _MISSING) -> Any:
    if isinstance(record, Mapping):
        value = record.get(name, _MISSING)
    else:
        value = getattr(record, name, _MISSING)
    if value is _MISSING:
        if default is _MISSING:
            raise TypeError(
                f"curve record is missing required field {name!r}: {record!r}. "
                "es_curve_identify takes CurveInventory, CurveRecords, or mappings with "
                "mnemonic/unit/description."
            )
        return default
    return value


def _records(inventory: Any) -> list[Any]:
    """Accept a CurveInventory, or any iterable of curve records."""
    curves = getattr(inventory, "curves", None)
    if curves is not None:
        return list(curves)
    if isinstance(inventory, Mapping):
        raise TypeError(
            "es_curve_identify takes a CurveInventory or an iterable of curve records, "
            "not a single mapping; wrap it in a list if it is one curve"
        )
    if not isinstance(inventory, Iterable):
        raise TypeError(
            f"inventory must be a CurveInventory or an iterable of curve records, got "
            f"{type(inventory).__name__}"
        )
    return list(inventory)


# --------------------------------------------------------------------------
# Text handling
# --------------------------------------------------------------------------
def _norm_key(raw: str) -> str:
    """Mnemonic lookup key: uppercase, strip the LAS API-code suffix and separators."""
    key = str(raw).strip().upper()
    key = key.split(":", 1)[0]          # LAS mnemonics may carry a :description suffix
    key = re.sub(r"[^A-Z0-9]", "", key)
    return key


def _norm_text(*parts: str) -> str:
    """One uppercase search string, with quote marks expanded to their unit words.

    18'8" -> 18 FT 8 IN, so the feet-and-inches regex sees a single spelling. Unit
    spellings are stripped first: the M of OHM-M must never read as a metre.
    """
    text = " ".join(str(p or "") for p in parts).upper()
    text = text.replace("’", "'").replace("”", '"').replace("″", '"')
    text = text.replace("′", "'")
    for noise in _UNIT_NOISE:
        text = text.replace(noise, " ")
    text = re.sub(r'(\d)\s*"', r"\1 IN ", text)
    text = re.sub(r"(\d)\s*'", r"\1 FT ", text)
    text = re.sub(r"[^A-Z0-9./]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_RE_FT_IN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:FT|FEET|FOOT)\s*(\d+(?:\.\d+)?)\s*(?:IN|INCH|INCHES)\b"
)
_RE_IN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:IN|INCH|INCHES)\b")
_RE_FT = re.compile(r"(\d+(?:\.\d+)?)\s*(?:FT|FEET|FOOT)\b")
_RE_CM = re.compile(r"(\d+(?:\.\d+)?)\s*(?:CM|CENTIMETER|CENTIMETERS|CENTIMETRES)\b")
_RE_M = re.compile(r"(\d+(?:\.\d+)?)\s*(?:M|METER|METERS|METRE|METRES)\b")


def _parse_spacing_in(text: str) -> tuple[float, str] | None:
    """-> (inches, how it was read), or None. Only ever reads a stated unit."""
    m = _RE_FT_IN.search(text)
    if m:
        inches = float(m.group(1)) * IN_PER_FT + float(m.group(2))
        return inches, f"stated as {m.group(0)!r} = {inches:g} in"
    m = _RE_IN.search(text)
    if m:
        return float(m.group(1)), f"stated as {m.group(0)!r}"
    m = _RE_CM.search(text)
    if m:
        inches = float(m.group(1)) * IN_PER_CM
        return inches, f"stated as {m.group(0)!r} = {inches:.4f} in ({OTHER_SPACINGS_STATEMENT})"
    m = _RE_M.search(text)
    if m:
        inches = float(m.group(1)) * IN_PER_M
        return inches, f"stated as {m.group(0)!r} = {inches:.4f} in"
    m = _RE_FT.search(text)
    if m:
        inches = float(m.group(1)) * IN_PER_FT
        return inches, f"stated as {m.group(0)!r} = {inches:g} in"
    return None


def _match_spacing(
    inches: float, table: tuple[tuple[float, str, str], ...], tol: float
) -> tuple[float, str, str] | None:
    best = None
    for nominal, label, basis in table:
        delta = abs(inches - nominal)
        if delta <= tol and (best is None or delta < best[0]):
            best = (delta, nominal, label, basis)
    if best is None:
        return None
    return best[1], best[2], best[3]


def _has_token(text: str, tokens: Iterable[str]) -> str | None:
    for token in tokens:
        if re.search(rf"(?<![A-Z0-9]){re.escape(token)}(?![A-Z0-9])", text):
            return token
    return None


_RE_DIGITS = re.compile(r"(?<![0-9.])(\d{1,3})(?![0-9.])")


def _mnemonic_digits(key: str, text: str) -> list[float]:
    """Bare numbers in the mnemonic, as candidate inch spacings.

    OWNED and unsourced: reading `R64` as a 64-in normal is a raster-digitization
    convention, not something any source sanctions. Always the weakest confidence and
    always flagged.
    """
    return [float(d) for d in _RE_DIGITS.findall(key)] + [
        float(d) for d in _RE_DIGITS.findall(text)
    ]


# --------------------------------------------------------------------------
# Per-curve classification
# --------------------------------------------------------------------------
def _outside(
    mnem: str, unit: str, desc: str, device: str, why: str, extra_flags: tuple[str, ...] = ()
) -> EsCurveClass:
    return EsCurveClass(
        mnemonic=mnem, unit=unit, description=desc,
        device=device, es_role=None, status=STATUS_OUTSIDE,
        spacing_in=None,
        spacing_basis="not an ES device; no ES spacing applies",
        candidates=(), confidence=None, evidence=(why,),
        measures="", depth_of_investigation="",
        source=f"{TRIESTE_ES}; {BEG_TIMELINE}",
        flags=extra_flags,
    )


def _as_role(
    mnem: str, unit: str, desc: str, role: str, confidence: str,
    evidence: tuple[str, ...], spacing_in: float | None, spacing_basis: str,
    flags: tuple[str, ...],
) -> EsCurveClass:
    dev = _BY_ROLE[role]
    out_flags = list(flags)
    if role != ROLE_SP:
        out_flags.append(f"apparent resistivity: {APPARENT_R_CAVEAT}")
    # Unit contradictions are reported, never used to overturn a stated spacing.
    ukey = _norm_key(unit)
    if role == ROLE_SP and ukey and ukey in {_norm_key(u) for u in RESISTIVITY_UNITS}:
        out_flags.append(
            f"unit contradiction: classified as the SP but the unit is {unit!r}, a "
            "resistivity unit"
        )
    if role != ROLE_SP and ukey and ukey in {_norm_key(u) for u in POTENTIAL_UNITS}:
        out_flags.append(
            f"unit contradiction: classified as {dev.label} but the unit is {unit!r}, a "
            "potential unit"
        )
    return EsCurveClass(
        mnemonic=mnem, unit=unit, description=desc,
        device=dev.device, es_role=role, status=STATUS_IDENTIFIED,
        spacing_in=spacing_in, spacing_basis=spacing_basis,
        candidates=(), confidence=confidence, evidence=evidence,
        measures=dev.measures, depth_of_investigation=dev.depth_of_investigation,
        source=dev.source, flags=tuple(out_flags),
    )


def _classify_one(record: Any, normalized: Mapping[str, Any] | None) -> EsCurveClass:
    mnem = str(_field(record, "mnemonic"))
    unit = str(_field(record, "unit", "") or "")
    desc = str(_field(record, "description", "") or "")
    key = _norm_key(mnem)
    text = _norm_text(mnem, desc)
    evidence: list[str] = []
    flags: list[str] = []

    # Corroboration from mnemonic_normalize (#9), when the caller ran it. Evidence only:
    # it never overrides a spacing stated in the curve's own text.
    norm = None if not normalized else normalized.get(mnem, normalized.get(key))
    norm_family = ""
    if norm is not None and not isinstance(norm, Refusal):
        norm_family = str(getattr(norm, "family", "") or "")
        canonical = getattr(norm, "canonical", None)
        if canonical:
            evidence.append(
                f"mnemonic_normalize: {mnem!r} -> {canonical!r} "
                f"(family {norm_family!r}, {getattr(norm, 'match', '?')})"
            )
    elif isinstance(norm, Refusal):
        flags.append(f"mnemonic_normalize refused {mnem!r}: {norm.reason}")

    if bool(_field(record, "all_null", False)):
        flags.append(
            "curve is entirely null: the role is nominally present and carries no data"
        )

    # --- 1. the microlog family, before any normal rule -------------------
    micro = MICRO_MNEMONICS.get(key)
    micro_token = _has_token(text, MICRO_TOKENS)
    if micro or micro_token:
        why = micro or f"description names {micro_token!r}"
        return EsCurveClass(
            mnemonic=mnem, unit=unit, description=desc,
            device=DEVICE_MICRO, es_role=None, status=STATUS_OUTSIDE,
            spacing_in=None,
            spacing_basis=(
                "microlog spacings (Micro Normal 2 in, Micro Inverse 1 in x 1 in) are "
                "not ES spacings"
            ),
            candidates=(), confidence=None,
            evidence=tuple(evidence + [f"{why}; {MICROLOG_STATEMENT}"]),
            measures="microlog measurement; used qualitatively to find permeable zones",
            depth_of_investigation="pad device, flushed zone",
            source=BEG_TIMELINE,
            flags=tuple(flags + [
                "adjacent to the ES suite, not one of its four measurements"
            ]),
        )

    # --- 2. post-ES devices ----------------------------------------------
    post = POST_ES_MNEMONICS.get(key)
    post_token = _has_token(text, POST_ES_TOKENS)
    if post or post_token:
        why = post or f"description names {post_token!r}; {SUCCESSOR_STATEMENT}"
        return _outside(mnem, unit, desc, DEVICE_POST_ES, why)

    # --- 3. exact ES mnemonic --------------------------------------------
    if key in ES_MNEMONICS:
        role, why = ES_MNEMONICS[key]
        dev = _BY_ROLE[role]
        evidence.append(f"mnemonic {key!r} is a cited ES mnemonic: {why}")
        role_flags = list(flags)
        if role in (ROLE_SHORT_NORMAL, ROLE_LONG_NORMAL):
            role_flags.append(
                f"spacing inherited from the suite definition, not from this curve's "
                f"text: {OTHER_SPACINGS_STATEMENT}"
            )
        if role == ROLE_LATERAL:
            role_flags.append(
                "spacing inherited from the suite definition; epa#2 also names a 1.8 m "
                "(70.9 in) lateral 'in tools used in groundwater'"
            )
        # A stated spacing in the same curve's text outranks the inherited one.
        parsed = _parse_spacing_in(text)
        if parsed is not None and dev.spacing_in is not None:
            inches, how = parsed
            tol = (
                LATERAL_SPACING_TOL_IN if role == ROLE_LATERAL else NORMAL_SPACING_TOL_IN
            )
            if abs(inches - dev.spacing_in) <= tol:
                return _as_role(
                    mnem, unit, desc, role, CONF_EXPLICIT,
                    tuple(evidence + [f"spacing {how}, matching {dev.label}"]),
                    dev.spacing_in, dev.spacing_basis, tuple(flags),
                )
            role_flags.append(
                f"spacing {how} does not match {dev.label} ({dev.spacing_in:g} in) "
                f"within {tol:g} in; the mnemonic and the stated spacing disagree"
            )
        return _as_role(
            mnem, unit, desc, role, CONF_CITED_MNEMONIC, tuple(evidence),
            dev.spacing_in, dev.spacing_basis, tuple(role_flags),
        )

    # --- 4. device family from words -------------------------------------
    sp_token = _has_token(text, SP_TOKENS)
    lateral_token = _has_token(text, LATERAL_TOKENS)
    normal_token = _has_token(text, NORMAL_TOKENS)

    if sp_token and not lateral_token and not normal_token:
        evidence.append(f"description names {sp_token!r}; {SUITE_STATEMENT}")
        return _as_role(
            mnem, unit, desc, ROLE_SP, CONF_CITED_SUITE, tuple(evidence),
            None, _BY_ROLE[ROLE_SP].spacing_basis, tuple(flags),
        )

    device = (
        DEVICE_LATERAL if lateral_token
        else DEVICE_NORMAL if normal_token
        else DEVICE_UNKNOWN
    )

    # --- 5. a spacing stated in this curve's own text ---------------------
    parsed = _parse_spacing_in(text)
    if device in (DEVICE_NORMAL, DEVICE_LATERAL) and parsed is not None:
        inches, how = parsed
        table = LATERAL_SPACINGS_IN if device == DEVICE_LATERAL else NORMAL_SPACINGS_IN
        tol = (
            LATERAL_SPACING_TOL_IN if device == DEVICE_LATERAL
            else NORMAL_SPACING_TOL_IN
        )
        hit = _match_spacing(inches, table, tol)
        if hit is not None:
            nominal, label, basis = hit
            role = _role_for_spacing(device, nominal)
            if role is not None:
                evidence.append(
                    f"device {device!r} from {lateral_token or normal_token!r}; "
                    f"spacing {how}, matching the {label} ({basis})"
                )
                return _as_role(
                    mnem, unit, desc, role, CONF_EXPLICIT, tuple(evidence),
                    nominal, basis, tuple(flags),
                )
            # A real spacing the literature names, but not one of the ES suite's.
            return _nonstandard(
                mnem, unit, desc, device, nominal, label, basis,
                tuple(evidence + [f"spacing {how}, matching the {label}"]), tuple(flags),
            )
        return _nonstandard(
            mnem, unit, desc, device, inches,
            "a spacing no source in this corpus names", SPACING_TOL_BASIS,
            tuple(evidence + [f"spacing {how}; no corpus-named spacing within tolerance"]),
            tuple(flags),
        )

    # --- 6. short/long qualifier with no spacing --------------------------
    if device == DEVICE_NORMAL:
        short = _has_token(text, SHORT_TOKENS)
        long_ = _has_token(text, LONG_TOKENS)
        if short and not long_:
            evidence.append(
                f"description names a short normal ({short!r}) with no spacing; "
                f"{NORMAL_SPACING_STATEMENT}"
            )
            return _as_role(
                mnem, unit, desc, ROLE_SHORT_NORMAL, CONF_CITED_SUITE, tuple(evidence),
                16.0, NORMAL_SPACING_STATEMENT,
                tuple(flags + [
                    f"spacing not stated by this curve; taken from the ES suite "
                    f"definition. {OTHER_SPACINGS_STATEMENT}"
                ]),
            )
        if long_ and not short:
            evidence.append(
                f"description names a long normal ({long_!r}) with no spacing; "
                f"{NORMAL_SPACING_STATEMENT}"
            )
            return _as_role(
                mnem, unit, desc, ROLE_LONG_NORMAL, CONF_CITED_SUITE, tuple(evidence),
                64.0, NORMAL_SPACING_STATEMENT,
                tuple(flags + [
                    f"spacing not stated by this curve; taken from the ES suite "
                    f"definition. {OTHER_SPACINGS_STATEMENT}"
                ]),
            )

    if device == DEVICE_LATERAL:
        evidence.append(
            f"description names a lateral with no spacing; {LATERAL_SPACING_STATEMENT} "
            "and the ES has exactly one lateral"
        )
        return _as_role(
            mnem, unit, desc, ROLE_LATERAL, CONF_CITED_SUITE, tuple(evidence),
            float(LATERAL_AO_IN), LATERAL_SPACING_STATEMENT,
            tuple(flags + [
                "spacing not stated by this curve; taken from the ES suite definition. "
                "epa#2 also names a 1.8 m (70.9 in) lateral 'in tools used in "
                "groundwater', which this rule cannot distinguish by name alone"
            ]),
        )

    # --- 7. bare digits next to a resistivity marker ----------------------
    is_resistivity = _norm_key(unit) in {_norm_key(u) for u in RESISTIVITY_UNITS} or (
        norm_family == "resistivity"
    )
    if device == DEVICE_NORMAL or (device == DEVICE_UNKNOWN and is_resistivity):
        for digits in _mnemonic_digits(key, text):
            hit = _match_spacing(digits, NORMAL_SPACINGS_IN, 0.0)
            if hit is None:
                continue
            nominal, label, basis = hit
            role = _role_for_spacing(DEVICE_NORMAL, nominal)
            if role is None:
                continue
            evidence.append(
                f"bare digits {digits:g} in {mnem!r} read as an AM spacing in inches, "
                f"matching the {label} ({basis})"
            )
            return _as_role(
                mnem, unit, desc, role, CONF_MNEMONIC_DIGITS, tuple(evidence),
                nominal, basis,
                tuple(flags + [
                    "OWNED, unsourced: the spacing was read from bare digits in the "
                    "mnemonic with no unit stated. No source sanctions this reading; it "
                    "is a raster-digitization convention. Treat as the weakest evidence."
                ]),
            )

    # --- 8. a normal device whose spacing is not recoverable --------------
    if device == DEVICE_NORMAL:
        return EsCurveClass(
            mnemonic=mnem, unit=unit, description=desc,
            device=DEVICE_NORMAL, es_role=None, status=STATUS_AMBIGUOUS,
            spacing_in=None,
            spacing_basis=(
                "no spacing is stated and no cited mnemonic fixes one; the source "
                "cannot tell the 16-in. short normal from the 64-in. long normal here"
            ),
            candidates=(ROLE_SHORT_NORMAL, ROLE_LONG_NORMAL),
            confidence=None,
            evidence=tuple(evidence + [
                f"description names a normal device ({normal_token!r}) with no spacing "
                f"and no short/long qualifier. {NORMAL_SPACING_STATEMENT} "
                f"{OTHER_SPACINGS_STATEMENT}"
            ]),
            measures=(
                "apparent resistivity from a normal device of unknown AM spacing; which "
                "zone it sees is undetermined until the spacing is known"
            ),
            depth_of_investigation=(
                "undetermined: trieste#0 - 'the longer the spacing, the deeper the "
                "device investigates' - so without the spacing there is no answer"
            ),
            source=f"{TRIESTE_ES}; {EPA_ELECTRICAL}",
            flags=tuple(flags + [
                "AMBIGUOUS: no spacing was guessed. rt_from_long_normal (#98) must not "
                "consume this curve as either normal - a 16-in. reading used as a 64-in. "
                "reading is a wrong Rt."
            ]),
        )

    # --- 9. nothing reached it -------------------------------------------
    return EsCurveClass(
        mnemonic=mnem, unit=unit, description=desc,
        device=DEVICE_UNKNOWN, es_role=None, status=STATUS_UNIDENTIFIED,
        spacing_in=None,
        spacing_basis="no spacing evidence of any kind",
        candidates=(), confidence=None,
        evidence=tuple(evidence + [
            "no ES device rule reached this curve: no cited mnemonic, no device word, "
            "no stated spacing"
        ]),
        measures="resistivity, device unknown" if is_resistivity else "",
        depth_of_investigation="",
        source=ES_SOURCES,
        flags=tuple(flags + (
            ["carries a resistivity unit, so it is a resistivity curve of unknown device"]
            if is_resistivity else []
        )),
    )


def _role_for_spacing(device: str, nominal: float) -> str | None:
    """The ES role a matched nominal spacing belongs to, or None if it is not an ES one."""
    for dev in ES_SUITE:
        if dev.device == device and dev.spacing_in is not None:
            if math.isclose(dev.spacing_in, nominal, rel_tol=0.0, abs_tol=1e-9):
                return dev.role
    return None


def _nonstandard(
    mnem: str, unit: str, desc: str, device: str, inches: float, label: str,
    basis: str, evidence: tuple[str, ...], flags: tuple[str, ...],
) -> EsCurveClass:
    return EsCurveClass(
        mnemonic=mnem, unit=unit, description=desc,
        device=device, es_role=None, status=STATUS_NONSTANDARD,
        spacing_in=inches, spacing_basis=basis,
        candidates=(), confidence=CONF_EXPLICIT, evidence=evidence,
        measures=(
            f"apparent resistivity from a {device} device at {inches:g} in spacing "
            f"({label}); not one of the ES suite's devices"
        ),
        depth_of_investigation=(
            "trieste#0: 'the longer the spacing, the deeper the device investigates into "
            "the formation'"
        ),
        source=f"{TRIESTE_ES}; {EPA_ELECTRICAL}",
        flags=tuple(list(flags) + [
            f"spacing {inches:g} in is not one of the ES suite's ({SUITE_STATEMENT}). "
            "It must not be substituted for the 16-in. or 64-in. normal or the "
            "18-ft 8-in. lateral downstream."
        ]),
    )


# --------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------
def es_curve_identify(
    inventory: Any,
    *,
    normalized: Mapping[str, Any] | None = None,
    era: int | None = None,
    strict: bool = False,
) -> EsSuiteIdentification | Refusal:
    """Classify a curve inventory into the conventional ES suite.

    `inventory` is Group A's `curve_inventory` output (#3), a bare iterable of its
    `CurveRecord`s, or any iterable of mappings carrying `mnemonic`/`unit`/`description`.
    `normalized` is optional `mnemonic_normalize` (#9) output keyed by raw mnemonic, used
    as corroborating evidence only.

    `era` is advisory and never classifies anything. `strict=True` says the caller wants a
    definite classification, so an ambiguous curve becomes a `Refusal` instead of a
    reported ambiguity.

    Refuses when: the inventory is empty; there is no resistivity curve at all; there is
    no normal or lateral device of any spacing (the suite is not an ES); the suite is an
    IES rather than an ES by beg#34's definition; or `strict` and something is ambiguous.
    """
    if era is not None and not isinstance(era, int):
        raise ValueError(f"era must be a four-digit year as int, got {era!r}")
    if not isinstance(strict, bool):
        raise TypeError("strict must be a bool")

    records = _records(inventory)
    index_mnemonic = getattr(inventory, "index_mnemonic", None)

    # ---- R1: nothing to classify ----------------------------------------
    if not records:
        return Refusal(
            reason="the curve inventory is empty; there is nothing to classify",
            needed=("a curve_inventory (#3) result with at least one curve",),
            source=ES_SOURCES,
        )

    classified: list[EsCurveClass] = []
    skipped_index: list[str] = []
    for record in records:
        mnem = str(_field(record, "mnemonic"))
        if bool(_field(record, "is_index", False)) or (
            index_mnemonic is not None and mnem == index_mnemonic
        ):
            skipped_index.append(mnem)
            continue
        classified.append(_classify_one(record, normalized))

    curves = tuple(classified)
    if not curves:
        return Refusal(
            reason=(
                "the inventory holds only the depth index "
                f"({', '.join(skipped_index)}); there are no curves to classify"
            ),
            needed=("an inventory with at least one non-index curve",),
            source=ES_SOURCES,
        )

    resistivity_units = {_norm_key(u) for u in RESISTIVITY_UNITS}
    has_resistivity = any(
        c.device in (DEVICE_NORMAL, DEVICE_LATERAL)
        or (c.device == DEVICE_POST_ES and _is_resistivity_post_es(c))
        or _norm_key(c.unit) in resistivity_units
        for c in curves
    )

    # ---- R2: no resistivity of any kind ---------------------------------
    if not has_resistivity:
        return Refusal(
            reason=(
                "no resistivity curve is present. The conventional ES is defined by its "
                f"resistivity devices - {SUITE_STATEMENT} - and an SP alone is not an "
                "ES. Curves seen: " + ", ".join(c.mnemonic for c in curves)
            ),
            needed=(
                "at least one resistivity curve (a normal, a lateral, or a curve in "
                "ohm-m)",
                "or curve descriptions/units that identify one",
            ),
            source=ES_SOURCES,
        )

    es_devices = [c for c in curves if c.device in (DEVICE_NORMAL, DEVICE_LATERAL)]
    induction = [
        c for c in curves
        if _norm_key(c.mnemonic) in INDUCTION_MNEMONICS
        or _has_token(_norm_text(c.mnemonic, c.description), INDUCTION_TOKENS)
    ]
    focused = [c for c in curves if c.device == DEVICE_POST_ES and _is_resistivity_post_es(c)]

    # ---- R3: resistivity, but no ES device at all -----------------------
    if not es_devices:
        if focused or induction:
            names = ", ".join(sorted({c.mnemonic for c in focused + induction}))
            return Refusal(
                reason=(
                    "this is not a conventional electrical survey: every resistivity "
                    f"curve present ({names}) is a focusing-electrode or induction "
                    f"device, which the source names as the ES's successors. "
                    f"{SUCCESSOR_STATEMENT}"
                ),
                needed=(
                    "a normal or lateral curve - the ES suite is "
                    "SP + 16-in. normal + 64-in. normal + 18-ft 8-in. lateral",
                ),
                source=f"{TRIESTE_ES}; {BEG_TIMELINE}",
            )
        names = ", ".join(c.mnemonic for c in curves)
        return Refusal(
            reason=(
                "resistivity curves are present but no ES device could be identified in "
                f"any of them ({names}). Vintage curve naming is not standardised and "
                "nothing here names a normal, a lateral, or a spacing, so no "
                "classification will be guessed."
            ),
            needed=(
                "curve descriptions naming the device ('short normal', 'lateral')",
                "or the AM/AO spacing (16 in., 64 in., 18 ft 8 in.)",
                "or a raster header giving the same",
            ),
            source=ES_SOURCES,
        )

    present: dict[str, tuple[str, ...]] = {}
    for c in curves:
        if c.es_role is not None:
            present[c.es_role] = present.get(c.es_role, ()) + (c.mnemonic,)
    missing = tuple(r for r in ES_ROLES if r not in present)
    ambiguous = tuple(c for c in curves if c.status == STATUS_AMBIGUOUS)
    unidentified = tuple(c for c in curves if c.status == STATUS_UNIDENTIFIED)
    nonstandard = tuple(c for c in curves if c.status == STATUS_NONSTANDARD)
    outside = tuple(c for c in curves if c.status == STATUS_OUTSIDE)

    # ---- R4: an IES, not an ES ------------------------------------------
    # beg#34 defines both suites explicitly, so this is a sourced discrimination and not
    # an inference: SP + 16-in short normal + a deep induction, with neither the long
    # normal nor the lateral, is the IES.
    if (
        induction
        and ROLE_SHORT_NORMAL in present
        and ROLE_LONG_NORMAL not in present
        and ROLE_LATERAL not in present
        and not ambiguous
    ):
        return Refusal(
            reason=(
                "this suite is an Induction Electric Log (IES), not a conventional "
                f"electrical survey (ES). {IES_STATEMENT} Present: "
                + ", ".join(f"{r}={'/'.join(m)}" for r, m in present.items())
                + f"; induction: {', '.join(sorted({c.mnemonic for c in induction}))}. "
                "The 64-in. long normal and the 18-ft 8-in. lateral are both absent."
            ),
            needed=(
                "a 64-in. long normal and an 18-ft 8-in. lateral, which the ES has and "
                "the IES does not",
                "or a caller that wants the IES suite rather than the ES",
            ),
            source=BEG_TIMELINE,
        )

    # ---- R5: strict, and the source cannot resolve something ------------
    if strict and ambiguous:
        names = ", ".join(c.mnemonic for c in ambiguous)
        return Refusal(
            reason=(
                f"a definite classification was requested (strict=True) but {names} "
                "cannot be resolved from the source: the curve names a normal device "
                "with no spacing and no short/long qualifier, and the 16-in. and 64-in. "
                "normals are indistinguishable by name alone. No spacing will be "
                "guessed - a 16-in. reading used as a 64-in. reading is a wrong Rt."
            ),
            needed=(
                f"a stated AM spacing for {names} (16 in./40 cm or 64 in./162 cm)",
                "or a description qualifying it as the short or the long normal",
                "or strict=False to accept the ambiguity as a reported classification",
            ),
            source=f"{TRIESTE_ES}; {EPA_ELECTRICAL}",
        )

    # ---- the report ------------------------------------------------------
    n_present = len(present)
    completeness = Quantity(
        value=n_present / len(ES_ROLES),
        unit="fraction",
        method=(
            f"es_curve_identify: {n_present} of the {len(ES_ROLES)} ES measurements "
            "identified in the inventory"
        ),
        source=f"{TRIESTE_ES}; {BEG_TIMELINE}",
        inputs={
            "mnemonics": tuple(c.mnemonic for c in curves),
            "present": {r: m for r, m in present.items()},
            "missing": missing,
        },
        assumptions={
            "suite": SUITE_STATEMENT,
            "suite_corroboration": SUITE_STATEMENT_2,
        },
        flags=tuple(
            [f"ambiguous: {c.mnemonic}" for c in ambiguous]
            + [f"unidentified: {c.mnemonic}" for c in unidentified]
        ),
    )

    flags: list[str] = []
    for role, mnems in present.items():
        if len(mnems) > 1:
            flags.append(
                f"duplicate role: {len(mnems)} curves classify as {role} ({', '.join(mnems)}); "
                "rt_from_long_normal (#98) must be told which one to read"
            )
    if missing:
        flags.append(
            "missing from the suite: " + ", ".join(missing)
            + f". The ES is four measurements - {SUITE_STATEMENT}"
        )
    if ambiguous:
        flags.append(
            "ambiguous, reported rather than guessed: "
            + ", ".join(f"{c.mnemonic} ({'|'.join(c.candidates)})" for c in ambiguous)
        )
    if unidentified:
        flags.append("unidentified: " + ", ".join(c.mnemonic for c in unidentified))
    if nonstandard:
        flags.append(
            "nonstandard spacings, not ES devices: "
            + ", ".join(f"{c.mnemonic} @ {c.spacing_in:g} in" for c in nonstandard)
        )
    if induction or focused:
        flags.append(
            "post-ES resistivity curves also present ("
            + ", ".join(sorted({c.mnemonic for c in induction + focused}))
            + "); this file mixes eras"
        )
    if skipped_index:
        flags.append("depth index not classified: " + ", ".join(skipped_index))
    if era is not None and not (ERA_ES_FIRST <= era <= ERA_ES_LAST):
        flags.append(
            f"era {era} is outside the ES window {ERA_ES_FIRST}-{ERA_ES_LAST}. "
            f"{ERA_STATEMENT} Advisory only: era classified nothing here."
        )

    suite = "ES" if not missing else "ES-partial"

    return EsSuiteIdentification(
        curves=curves,
        present=present,
        missing=missing,
        ambiguous=ambiguous,
        unidentified=unidentified,
        nonstandard=nonstandard,
        outside_suite=outside,
        completeness=completeness,
        suite=suite,
        source=ES_SOURCES,
        flags=tuple(flags),
        assumptions={
            "suite_definition": SUITE_STATEMENT,
            "suite_corroboration": SUITE_STATEMENT_2,
            "normal_spacings": NORMAL_SPACING_STATEMENT,
            "lateral_spacing": LATERAL_SPACING_STATEMENT,
            "other_spacings": OTHER_SPACINGS_STATEMENT,
            "spacing_tolerance_in": {
                "normal": NORMAL_SPACING_TOL_IN,
                "lateral": LATERAL_SPACING_TOL_IN,
                "basis": SPACING_TOL_BASIS,
            },
            "no_canonical_mnemonic_table": (
                "This corpus has no canonical vintage mnemonic table (tools/mnemonics.py: "
                "the KGS curve-mnemonic table is not ingested). Every mnemonic rule here "
                "is a rule over cited prose plus owned spelling variants, which is why "
                "each identification carries a confidence and its evidence."
            ),
            "era": None if era is None else {"year": era, "basis": ERA_STATEMENT},
        },
    )


def _is_resistivity_post_es(c: EsCurveClass) -> bool:
    """Post-ES curves that are resistivity measurements, for the not-an-ES refusal."""
    key = _norm_key(c.mnemonic)
    if key in INDUCTION_MNEMONICS:
        return True
    if key in {"SFL", "SFLU", "LL", "LL3", "LL7", "LL8", "LLD", "LLS", "MLL", "MSFL",
               "PL", "RXO"}:
        return True
    text = _norm_text(c.mnemonic, c.description)
    return _has_token(text, ("LATEROLOG", "INDUCTION", "SPHERICALLY FOCUSED")) is not None
