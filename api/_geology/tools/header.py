"""Log-header extraction against the Texas RRC's mandatory item list A-P.

Destination module: `tools/header.py`. `raster_header_ocr` (#6) imports the field
contract `RRC_HEADER_ITEMS` from here, so the contract is the public artefact and
the extractor is built on top of it rather than the other way round.

Four decisions that are not obvious from the code:

**This tool reports; it does not resolve.** Its most valuable output is a
statement that item M - "depth that log measurements are relative to" - is
ambiguous. The real header at `rrc-section-f#16` gives Permanent Datum = Ground
Level while the log is measured from the Kelly bushing 15 ft above it. Picking
either one silently puts a 15 ft error into every structural computation
downstream, so `DatumReport.status` carries `conflict`/`unresolved` out to
`datum_resolve` (#15), which is the gate, and no depth reference is chosen here.

**Tmax is not BHT.** RRC item N is "Max temperature recorded", an instrument
reading. Bottom-hole temperature is an inference from it. A vendor `BHT` mnemonic
in ~P is recorded under `bht_reported`, flagged, and explicitly does not satisfy
item N - the inference belongs to a different tool.

**~P is optional in LAS 2.0** (`kgs-las-2.0-field-table#1`), and eleven of the
sixteen RRC items can only come from it. Every ~P-sourced field therefore has one
uniform, defined absent-path: reported in `missing_fields`, its item reported in
`missing_items`, no value substituted, ever.

**A resistivity without its measurement temperature is unusable, not fine.** Item
J reads "Rm, Rmf, and Rmc values at stated measured temperature" - one
requirement. An Rm with no temperature is returned flagged and listed in
`unusable` so temperature correction refuses instead of guessing; a bare mud
sample temperature (MST) is recorded on its own and never assigned to a specific
resistivity.

Sources:
  `09-gas-deliverability/rrc-section-f-completions-electric-logs#15` - items A-P
  `09-gas-deliverability/rrc-section-f-completions-electric-logs#16` - real header
  `02-las-format/kgs-las-2.0-field-table#1` - LAS 2.0 sections and ~W mnemonics
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field as dc_field
from typing import Any

from .result import Quantity, Range, Refusal  # noqa: F401  (Range re-exported for the group)

RRC_HEADER_LIST = "09-gas-deliverability/rrc-section-f-completions-electric-logs#15"
RRC_REAL_HEADER = "09-gas-deliverability/rrc-section-f-completions-electric-logs#16"
LAS_SECTIONS = "02-las-format/kgs-las-2.0-field-table#1"


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HeaderField:
    """One extractable field of one RRC item.

    `sections` are LAS section keys (`~W` required, `~P` optional per
    `kgs-las-2.0-field-table#1`; `~C` where the item is answered by the curve
    list). `mnemonics` are searched in order, first match wins.

    PROVISIONAL: the corpus publishes no ~P mnemonic dictionary - `kgs#1` lists
    only the required ~W mnemonics and describes ~P in prose. Every ~P alias
    below is field practice, not a citation, which is why an unmatched mnemonic
    is reported missing rather than guessed at. `mnemonic_normalize` (#9) owns
    the alias dictionary; reconcile there on merge.
    """

    name: str
    unit: str | None                 # expected unit, None for text fields
    required: bool                   # required to satisfy its RRC item
    sections: tuple[str, ...]
    mnemonics: tuple[str, ...] = ()
    accepted_units: tuple[str, ...] = ()
    raster_labels: tuple[str, ...] = ()   # as printed on a paper header, for #6
    note: str = ""

    @property
    def numeric(self) -> bool:
        return self.unit is not None


@dataclass(frozen=True)
class HeaderItem:
    """One lettered item of the RRC's mandatory log-header list.

    `rrc_text` is verbatim from `rrc-section-f#15` so the contract can be audited
    against the regulation. All sixteen items are required - the list's own title
    is "Items Required on a Log Header".

    `satisfy` is how the item's required fields combine: "all" (every required
    field must be present) or "any" (one suffices, used where the source names a
    quantity that several fields can express).
    """

    letter: str
    rrc_text: str
    fields: tuple[HeaderField, ...]
    satisfy: str = "all"
    required: bool = True

    def required_fields(self) -> tuple[HeaderField, ...]:
        return tuple(f for f in self.fields if f.required)


_DEPTH_UNITS = ("F", "FT", "FEET", "M", "METRE", "METRES", "METER", "METERS")
_SIZE_UNITS = ("IN", "INCH", "INCHES", "MM", "CM")
_TEMP_UNITS = ("DEGF", "DEG F", "F", "DEGC", "DEG C", "C")
_RES_UNITS = ("OHMM", "OHM-M", "OHM.M", "OHMM2/M", "OHM", "OHMS")
_MUD_DENSITY_UNITS = ("LB/GAL", "PPG", "LBS/GAL", "G/CM3", "G/C3", "KG/M3", "LB/FT3")
_VISCOSITY_UNITS = ("S", "SEC", "S/QT", "SEC/QT", "CP", "MPA.S")


RRC_HEADER_ITEMS: dict[str, HeaderItem] = {
    "A": HeaderItem(
        letter="A",
        rrc_text="Well identification and location information",
        fields=(
            HeaderField("well_name", None, True, ("~W",), ("WELL",),
                        raster_labels=("well", "well name")),
            HeaderField("location", None, True, ("~W",), ("LOC", "LOCATION"),
                        raster_labels=("location",)),
            HeaderField("api_number", None, False, ("~W",), ("API", "APIN"),
                        raster_labels=("api", "api #", "api number"),
                        note="the RRC identifies wells by API; absence is flagged"),
            HeaderField("uwi", None, False, ("~W",), ("UWI",)),
            HeaderField("operator", None, False, ("~W",), ("COMP", "COMPANY", "OPER"),
                        raster_labels=("company", "operator")),
            HeaderField("field_name", None, False, ("~W",), ("FLD", "FIELD"),
                        raster_labels=("field",)),
            HeaderField("county", None, False, ("~W",), ("CNTY", "COUNTY"),
                        raster_labels=("county",)),
            HeaderField("state", None, False, ("~W",), ("STAT", "STATE"),
                        raster_labels=("state",)),
            HeaderField("country", None, False, ("~W",), ("CTRY", "PROV"),
                        raster_labels=("country",)),
        ),
    ),
    "B": HeaderItem(
        letter="B",
        rrc_text="Types of log measurements taken",
        satisfy="any",
        fields=(
            HeaderField("log_types", None, True, ("~P", "~C"),
                        ("LOGS", "LOGTYPE", "SERVICE", "RUNS"),
                        raster_labels=("other services", "log type", "type log"),
                        note="satisfied from the ~C curve list when no field states it"),
        ),
    ),
    "C": HeaderItem(
        letter="C",
        rrc_text="Depths logged",
        fields=(
            HeaderField("top_logged_ft", "ft", True, ("~W",), ("STRT",), _DEPTH_UNITS,
                        raster_labels=("top log interval", "top logged interval")),
            HeaderField("bottom_logged_ft", "ft", True, ("~W",), ("STOP",), _DEPTH_UNITS,
                        raster_labels=("bottom logged interval", "bottom log interval")),
            HeaderField("driller_td_ft", "ft", False, ("~P",), ("TDD", "TD", "DEPTHD"),
                        _DEPTH_UNITS, raster_labels=("depth driller", "depth onset")),
            HeaderField("logger_td_ft", "ft", False, ("~P",), ("TDL", "DEPTHL"),
                        _DEPTH_UNITS, raster_labels=("depth logger",)),
        ),
    ),
    "D": HeaderItem(
        letter="D",
        rrc_text="Bit sizes",
        fields=(
            HeaderField("bit_size_in", "in", True, ("~P",), ("BS", "BIT", "BITSIZE", "HSIZ"),
                        _SIZE_UNITS, raster_labels=("bit", "bit size", "open hole size"),
                        note="LAS ~P carries one bit size; a paper header carries a per-run table"),
        ),
    ),
    "E": HeaderItem(
        letter="E",
        rrc_text="Casing sizes",
        fields=(
            HeaderField("casing_size_in", "in", True, ("~P",), ("CS", "CSG", "CSGS", "CASING"),
                        _SIZE_UNITS, raster_labels=("casing", "casing size", "casing record")),
            HeaderField("casing_depth_ft", "ft", False, ("~P",), ("CSGD", "CSGL", "CASINGD"),
                        _DEPTH_UNITS, raster_labels=("casing bottom", "casing shoe")),
        ),
    ),
    "F": HeaderItem(
        letter="F",
        rrc_text="Date and time logging started and finished",
        fields=(
            HeaderField("date_logged", None, True, ("~W",), ("DATE",),
                        raster_labels=("date",)),
            HeaderField("time_logging_started", None, False, ("~P",),
                        ("TIMS", "STIM", "TSTART"),
                        raster_labels=("time well ready", "time logging started")),
            HeaderField("time_logging_finished", None, False, ("~P",),
                        ("TIMF", "FTIM", "TSTOP"),
                        raster_labels=("time logger on bottom", "time logging finished")),
        ),
    ),
    "G": HeaderItem(
        letter="G",
        rrc_text="Type of mud",
        fields=(
            HeaderField("mud_type", None, True, ("~P",), ("MUD", "MUDTYPE", "TYPFL", "FL", "DFT"),
                        raster_labels=("type fluid", "type of mud", "mud type", "fluid type")),
        ),
    ),
    "H": HeaderItem(
        letter="H",
        rrc_text="Mud density",
        fields=(
            HeaderField("mud_density", "lb/gal", True, ("~P",),
                        ("MDEN", "DFD", "MW", "MUDD", "MUDDEN"), _MUD_DENSITY_UNITS,
                        raster_labels=("density", "mud density", "mud weight"),
                        note="stated unit travels with the value; unit_convert (#11) converts"),
        ),
    ),
    "I": HeaderItem(
        letter="I",
        rrc_text="Mud viscosity",
        fields=(
            HeaderField("mud_viscosity", "s", True, ("~P",),
                        ("MVIS", "DFV", "VIS", "MUDV", "FUNNEL"), _VISCOSITY_UNITS,
                        raster_labels=("viscosity", "mud viscosity")),
        ),
    ),
    "J": HeaderItem(
        letter="J",
        rrc_text="Mud resistivity (Rm, Rmf, and Rmc values at stated measured temperature)",
        fields=(
            HeaderField("rm", "ohm-m", True, ("~P",), ("RM", "RMUD", "RMB"), _RES_UNITS,
                        raster_labels=("rm", "rm at meas. temp")),
            HeaderField("rm_temperature", "degF", True, ("~P",), ("RMT", "RMTEMP", "TRM"),
                        _TEMP_UNITS, raster_labels=("rm temp", "temp. of rm")),
            HeaderField("rmf", "ohm-m", True, ("~P",), ("RMF", "RMFS"), _RES_UNITS,
                        raster_labels=("rmf", "rmf at meas. temp")),
            HeaderField("rmf_temperature", "degF", True, ("~P",), ("RMFT", "MFST", "TRMF"),
                        _TEMP_UNITS, raster_labels=("rmf temp", "temp. of rmf")),
            HeaderField("rmc", "ohm-m", True, ("~P",), ("RMC", "RMCS"), _RES_UNITS,
                        raster_labels=("rmc", "rmc at meas. temp")),
            HeaderField("rmc_temperature", "degF", True, ("~P",), ("RMCT", "MCST", "TRMC"),
                        _TEMP_UNITS, raster_labels=("rmc temp", "temp. of rmc")),
            HeaderField("mud_sample_temperature", "degF", False, ("~P",), ("MST", "MSTEMP"),
                        _TEMP_UNITS, raster_labels=("mud sample temp",),
                        note="never assigned to a specific resistivity - that is an inference"),
        ),
    ),
    "K": HeaderItem(
        letter="K",
        rrc_text="Elevation above sea level",
        satisfy="any",
        fields=(
            HeaderField("kb_elevation_ft", "ft", True, ("~W", "~P"), ("EKB", "KB", "ELKB"),
                        _DEPTH_UNITS, raster_labels=("elevation k.b.", "kb elevation", "k.b.")),
            HeaderField("df_elevation_ft", "ft", True, ("~W", "~P"), ("EDF", "DF", "ELDF"),
                        _DEPTH_UNITS, raster_labels=("d.f.", "df elevation")),
            HeaderField("ground_elevation_ft", "ft", True, ("~W", "~P"), ("EGL", "GL", "ELEV", "ELGL"),
                        _DEPTH_UNITS, raster_labels=("g.l.", "ground level", "ground elevation")),
            HeaderField("permanent_datum_elevation_ft", "ft", False, ("~W", "~P"), ("EPD", "PDATE"),
                        _DEPTH_UNITS, raster_labels=("elevation of permanent datum",)),
        ),
    ),
    "L": HeaderItem(
        letter="L",
        rrc_text="Kelly bushing height",
        fields=(
            HeaderField("kb_height_ft", "ft", True, ("~W", "~P"), ("APD", "KBH", "EKBH"),
                        _DEPTH_UNITS,
                        raster_labels=("apd", "elevation apd", "kelly bushing height"),
                        note="APD is height above permanent datum; equals KB height only "
                             "when the log is measured from the KB"),
        ),
    ),
    "M": HeaderItem(
        letter="M",
        rrc_text="Depth that log measurements are relative to",
        fields=(
            HeaderField("log_measured_from", None, True, ("~W", "~P"), ("LMF", "LOGMEAS", "MEASFROM"),
                        raster_labels=("log measured from",)),
            HeaderField("permanent_datum", None, False, ("~W", "~P"), ("PDAT", "PD", "PERMDAT"),
                        raster_labels=("permanent datum",)),
            HeaderField("drilling_measured_from", None, False, ("~W", "~P"), ("DMF", "DRLMEAS"),
                        raster_labels=("drilling measured from",)),
        ),
    ),
    "N": HeaderItem(
        letter="N",
        rrc_text="Max temperature recorded",
        fields=(
            HeaderField("max_recorded_temp", "degF", True, ("~P",),
                        ("MRT", "TMAX", "MAXT", "MAXTEMP"), _TEMP_UNITS,
                        raster_labels=("max. recorded temp.", "maximum recorded temperature")),
            HeaderField("bht_reported", "degF", False, ("~P",), ("BHT", "BHTEMP"), _TEMP_UNITS,
                        raster_labels=("bht", "bottom hole temperature"),
                        note="does NOT satisfy item N - BHT is an inference from Tmax, "
                             "and making that inference is a different tool"),
        ),
    ),
    "O": HeaderItem(
        letter="O",
        rrc_text="Name of service company",
        fields=(
            HeaderField("service_company", None, True, ("~W", "~P"), ("SRVC", "SVCO", "SERVCO"),
                        raster_labels=("service company", "logging company")),
        ),
    ),
    "P": HeaderItem(
        letter="P",
        rrc_text="Name of service company employee",
        fields=(
            HeaderField("service_company_employee", None, True, ("~P",),
                        ("ENG", "ENGI", "ENGINEER", "RECBY", "LOGR", "WITN"),
                        raster_labels=("recorded by", "engineer", "logged by")),
        ),
    ),
}

# Fields, flat, in item order. Built once so #6 and the extractor agree by
# construction rather than by two lists being kept in step by hand.
FIELDS_BY_NAME: dict[str, HeaderField] = {
    f.name: f for item in RRC_HEADER_ITEMS.values() for f in item.fields
}
ITEM_OF_FIELD: dict[str, str] = {
    f.name: letter for letter, item in RRC_HEADER_ITEMS.items() for f in item.fields
}

# Printed-label -> field name, for raster_header_ocr (#6). Same contract, one
# table, so an OCR'd "Permanent Datum" and a LAS `PDAT` land on the same field.
RASTER_LABEL_INDEX: dict[str, str] = {
    label: f.name for f in FIELDS_BY_NAME.values() for label in f.raster_labels
}

# Item J binds each resistivity to its own stated temperature.
RESISTIVITY_TEMPERATURE_PAIRS: dict[str, str] = {
    "rm": "rm_temperature",
    "rmf": "rmf_temperature",
    "rmc": "rmc_temperature",
}

# No source states a tolerance for header self-agreement. This is float
# hygiene, not a domain tolerance: any real disagreement is surfaced.
_EPS = 1e-9


# ---------------------------------------------------------------------------
# Value types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TextField:
    """A header string. `Quantity.value` is a float; a well name is not.

    Carries the same provenance contract as `Quantity` and refuses to construct
    without a method and a source.
    """

    value: str
    method: str
    source: str
    inputs: dict[str, Any] = dc_field(default_factory=dict)
    flags: tuple[str, ...] = ()
    unit: None = None

    def __post_init__(self) -> None:
        if not self.method or not self.source:
            raise ValueError("a TextField must carry both a method and a source")

    def __repr__(self) -> str:
        return f"TextField({self.value!r}, {self.method})"


@dataclass(frozen=True)
class Conflict:
    """The header contradicting itself. Reported, never resolved here."""

    kind: str
    detail: str
    values: dict[str, Any] = dc_field(default_factory=dict)
    source: str = RRC_HEADER_LIST


@dataclass(frozen=True)
class DatumReport:
    """RRC item M. `status != "resolved"` is what `datum_resolve` (#15) gates on.

    status:
      resolved   - the log states what its depths are measured from
      conflict   - permanent datum and log-measured-from name different references
      unresolved - a permanent datum is stated but not what the log is measured from
      absent     - neither is stated
    """

    status: str
    detail: str
    permanent_datum: str | None = None
    log_measured_from: str | None = None
    drilling_measured_from: str | None = None
    offset_ft: float | None = None      # LMF elevation - permanent datum elevation
    elevations: dict[str, float] = dc_field(default_factory=dict)
    source: str = RRC_HEADER_LIST


@dataclass(frozen=True)
class HeaderExtract:
    fields: dict[str, Quantity | TextField]
    items_satisfied: tuple[str, ...]
    missing_items: tuple[str, ...]
    missing_fields: tuple[str, ...]
    unusable: tuple[str, ...]
    conflicts: tuple[Conflict, ...]
    datum: DatumReport
    # Fields the header *has* but left empty, as distinct from fields it does
    # not have. Both fail their RRC item and both appear in `missing_fields` -
    # a blank cell satisfies nothing - but they are different findings about
    # the header and a reporter that conflates them loses information the
    # operator needs. `rrc-section-f#16` contains both: it prints "Density /
    # Viscosity" and "Max. Recorded Temp." with the cells blank, and carries no
    # mud-resistivity row at all.
    blank_fields: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()
    source: str = RRC_HEADER_LIST
    source_file: str | None = None

    def get(self, name: str) -> Quantity | TextField | None:
        return self.fields.get(name)

    def value(self, name: str) -> Any:
        found = self.fields.get(name)
        return None if found is None else found.value

    def item_report(self) -> dict[str, str]:
        """Letter -> satisfied / missing, for rendering to an operator."""
        return {
            letter: ("satisfied" if letter in self.items_satisfied else "missing")
            for letter in RRC_HEADER_ITEMS
        }


# ---------------------------------------------------------------------------
# las_parse adaptation
# ---------------------------------------------------------------------------
# ASSUMED INTERFACE (reconcile on merge, las_parse #1 written concurrently):
# a mapping section-key -> sequence of entries, each entry carrying mnemonic,
# unit, value, description and the raw line. Both dict-shaped and
# attribute-shaped entries are accepted, as are several spellings of each key,
# so a small divergence in las_parse's shape does not break this tool.

_ALIASES = {
    "mnemonic": ("mnemonic", "mnem", "name", "key"),
    "unit": ("unit", "units"),
    "value": ("value", "val", "data"),
    "description": ("description", "descr", "desc", "comment"),
    "raw_line": ("raw_line", "raw", "line", "source_line"),
}


def _pluck(entry: Any, field_name: str) -> str:
    for alias in _ALIASES[field_name]:
        if isinstance(entry, Mapping):
            if alias in entry and entry[alias] is not None:
                return str(entry[alias])
        else:
            got = getattr(entry, alias, None)
            if got is not None:
                return str(got)
    return ""


def _section_letter(key: Any) -> str:
    text = str(key).strip().lstrip("~").strip().upper()
    return text[0] if text else ""


# las_parse (#1) as shipped returns a `LasFile`, which is neither a mapping nor
# an object with `.sections`: it exposes one attribute per LAS section. Matched
# structurally rather than by import so this module stays free of group-A
# cross-imports; `well` is the discriminator because ~W is the required section.
_LASFILE_SECTIONS = (("~V", "version_info"), ("~W", "well"),
                     ("~C", "curves"), ("~P", "parameters"))


def _unwrap(sections: Any) -> Mapping[Any, Any]:
    """Accept the parse result or its `sections` mapping."""
    if isinstance(sections, Mapping) and "sections" in sections:
        sections = sections["sections"]
    elif not isinstance(sections, Mapping) and hasattr(sections, "sections"):
        sections = sections.sections
    elif not isinstance(sections, Mapping) and hasattr(sections, "well"):
        sections = {key: getattr(sections, attr) or ()
                    for key, attr in _LASFILE_SECTIONS
                    if hasattr(sections, attr)}
    if not isinstance(sections, Mapping):
        raise TypeError(
            "header_extract expects a mapping of LAS section key -> entries "
            f"(las_parse output); got {type(sections).__name__}"
        )
    return sections


def _index(sections: Mapping[Any, Any]) -> dict[str, list[dict[str, str]]]:
    """Section letter -> normalized entries, order preserved."""
    out: dict[str, list[dict[str, str]]] = {}
    for key, entries in sections.items():
        letter = _section_letter(key)
        if not letter or letter == "A":       # the data section is never read
            continue
        if entries is None:
            entries = ()
        if isinstance(entries, (str, bytes)) or not isinstance(entries, Iterable):
            raise TypeError(f"section {key!r} does not hold a sequence of entries")
        bucket = out.setdefault(letter, [])
        for entry in entries:
            if not isinstance(entry, (Mapping,)) and not hasattr(entry, "__dict__") \
                    and not hasattr(entry, "mnemonic"):
                raise TypeError(
                    f"entry in section {key!r} is neither a mapping nor an object "
                    f"with mnemonic/unit/value: {entry!r}"
                )
            mnemonic = _pluck(entry, "mnemonic").strip().strip(".:").upper()
            if not mnemonic:
                continue
            raw = _pluck(entry, "raw_line").strip()
            unit = _pluck(entry, "unit").strip()
            value = _pluck(entry, "value").strip()
            descr = _pluck(entry, "description").strip()
            bucket.append({
                "mnemonic": mnemonic,
                "unit": unit,
                "value": value,
                "description": descr,
                "raw_line": raw or f"{mnemonic:<6}.{unit:<6} {value:<24}: {descr}",
                "raw_supplied": "yes" if raw else "no",
            })
    return out


# ---------------------------------------------------------------------------
# Value coercion
# ---------------------------------------------------------------------------

_MIXED_FRACTION = re.compile(r"^(?:(\d+)\s+)?(\d+)\s*/\s*(\d+)$")


def _to_float(text: str) -> float | None:
    """Deterministic numeric read. Returns None when the text is not a number.

    Handles the marks real headers carry: 10925', 7 7/8", 2,888. Mixed fractions
    matter because bit and casing sizes are written that way. Anything else is
    left as text and flagged rather than coerced.
    """
    s = str(text).strip().replace(",", "")
    s = s.replace('"', " ").replace("'", " ").replace("’", " ").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    match = _MIXED_FRACTION.match(s)
    if match:
        whole, num, den = match.groups()
        denom = float(den)
        if denom == 0:
            return None
        return (float(whole) if whole else 0.0) + float(num) / denom
    return None


def _unit_ok(stated: str, accepted: Sequence[str]) -> bool:
    if not stated or not accepted:
        return True
    probe = stated.strip().upper().replace(" ", "")
    return any(probe == ok.upper().replace(" ", "") for ok in accepted)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def _find(indexed: dict[str, list[dict[str, str]]],
          spec: HeaderField) -> tuple[str, dict[str, str]] | None:
    """First match, walking declared sections then candidate mnemonics."""
    for section in spec.sections:
        letter = _section_letter(section)
        for mnemonic in spec.mnemonics:
            for entry in indexed.get(letter, ()):
                if entry["mnemonic"] == mnemonic.upper():
                    return section, entry
    return None


def _build(spec: HeaderField, section: str, entry: dict[str, str],
           source_file: str | None) -> Quantity | TextField:
    flags: list[str] = []
    stated_unit = entry["unit"]
    method = (f"RRC log-header item {ITEM_OF_FIELD[spec.name]} "
              f"({spec.name}) from LAS {section} mnemonic {entry['mnemonic']}")
    inputs = {
        "section": section,
        "mnemonic": entry["mnemonic"],
        "raw_line": entry["raw_line"],
        "unit_as_stated": stated_unit or None,
        "description": entry["description"] or None,
        "source_file": source_file,
    }
    if entry["raw_supplied"] == "no":
        flags.append("raw line not supplied by las_parse; reconstructed from the entry")
    if spec.name == "max_recorded_temp" and entry["mnemonic"] == "TMAX":
        flags.append("matched via TMAX, which is also the Rock-Eval pyrolysis Tmax "
                     "mnemonic; confirm this is the maximum recorded borehole temperature")
    if spec.name == "bht_reported":
        flags.append("a reported bottom-hole temperature; it does NOT satisfy RRC item N "
                     "(max temperature recorded) and no Tmax is inferred from it")
    if spec.name == "kb_height_ft" and entry["mnemonic"] == "APD":
        flags.append("matched via APD (height above permanent datum); this equals the "
                     "Kelly bushing height only when the log is measured from the KB")
    if spec.name == "mud_sample_temperature":
        flags.append("a mud sample temperature; assigning it to a specific resistivity "
                     "is an inference this tool does not make")

    if not spec.numeric:
        return TextField(value=entry["value"], method=method, source=RRC_HEADER_LIST,
                         inputs=inputs, flags=tuple(flags))

    number = _to_float(entry["value"])
    if number is None:
        flags.append(f"value {entry['value']!r} is not numeric; returned as text and not "
                     "usable as a quantity")
        return TextField(value=entry["value"], method=method, source=RRC_HEADER_LIST,
                         inputs=inputs, flags=tuple(flags))
    if not stated_unit:
        unit = "(unstated)"
        flags.append(f"no unit stated in the header; the contract expects {spec.unit} "
                     "but none is assumed here")
    else:
        unit = stated_unit
        if not _unit_ok(stated_unit, spec.accepted_units):
            flags.append(f"stated unit {stated_unit!r} is outside the accepted set for "
                         f"{spec.name} ({', '.join(spec.accepted_units)}); value returned "
                         "unconverted")
    return Quantity(value=number, unit=unit, method=method, source=RRC_HEADER_LIST,
                    inputs=inputs, assumptions={"expected_unit": spec.unit},
                    flags=tuple(flags))


def _log_types_from_curves(indexed: dict[str, list[dict[str, str]]],
                           source_file: str | None) -> TextField | None:
    """Item B from the ~C curve list when no field states the log types.

    Deterministic and honest: the curves present are the measurements taken. The
    flag says where it came from so nobody mistakes it for a stated field.
    """
    curves = [e["mnemonic"] for e in indexed.get("C", ())]
    if not curves:
        return None
    return TextField(
        value=", ".join(curves),
        method="RRC log-header item B (log_types) from the LAS ~C curve mnemonics",
        source=LAS_SECTIONS,
        inputs={"section": "~C", "mnemonic": "*",
                "raw_line": "; ".join(e["raw_line"] for e in indexed["C"]),
                "unit_as_stated": None, "description": "curve information section",
                "source_file": source_file},
        flags=("derived from the ~C curve list, not from a stated log-type field; "
               "mnemonic meanings are mnemonic_normalize's (#9) concern",),
    )


def _add_conflict(conflicts: list[Conflict], kind: str, detail: str,
                  values: dict[str, Any]) -> None:
    conflicts.append(Conflict(kind=kind, detail=detail, values=values,
                              source=RRC_REAL_HEADER))


def _datum_report(found: dict[str, Quantity | TextField],
                  conflicts: list[Conflict]) -> DatumReport:
    """RRC item M, plus the elevation reconcile the real header at #16 fails.

    #16 prints Permanent Datum = Ground Level, Log Measured From = Kelly Bushing,
    K.B. 2888', G.L. 2873': every depth on that log sits 15 ft from the datum the
    well is nominally referenced to. Nothing here picks a winner.
    """
    pdat = found.get("permanent_datum")
    lmf = found.get("log_measured_from")
    dmf = found.get("drilling_measured_from")
    pdat_name = str(pdat.value).strip() if pdat is not None else None
    lmf_name = str(lmf.value).strip() if lmf is not None else None
    dmf_name = str(dmf.value).strip() if dmf is not None else None

    elevations = {
        name: float(found[name].value)
        for name in ("kb_elevation_ft", "df_elevation_ft", "ground_elevation_ft",
                     "permanent_datum_elevation_ft")
        if isinstance(found.get(name), Quantity)
    }

    def elevation_of(reference: str | None) -> float | None:
        if not reference:
            return None
        probe = reference.lower().replace(".", "").replace("-", " ")
        # Top of kelly bushing is a DISTINCT datum on a log heading, not a
        # spelling of KB — `asquith#10` Fig. 1.2 lists K.B., D.F., G.L. and
        # T.K.B. as four references. "top of kelly bushing" contains "kelly", so
        # without this branch it would silently take the KB elevation and the
        # difference between them would vanish. This header carries no TKB
        # elevation field, so the honest answer is "unknown": returning None
        # leaves `datum_resolve` free to refuse rather than to be wrong.
        if "tkb" in probe.replace(" ", "") or "top of kelly" in probe:
            return None
        # `rkb` = rotary kelly bushing, the same point as KB and the spelling
        # both real fixtures use (`repass-2` prints `LMF . R.K.B.`). Without it
        # the offset came back None on a log that fully declares its datum.
        # Checked after the TKB branch above, which is a different point.
        if "kelly" in probe or probe.strip() in {"kb", "k b", "rkb", "r k b"}:
            return elevations.get("kb_elevation_ft")
        if "derrick" in probe or "drill floor" in probe or probe.strip() in {"df", "d f"}:
            return elevations.get("df_elevation_ft")
        if "ground" in probe or probe.strip() in {"gl", "g l"}:
            return elevations.get("ground_elevation_ft")
        if "sea" in probe or "msl" in probe:
            return 0.0
        return None

    def same(a: str | None, b: str | None) -> bool:
        if a is None or b is None:
            return False
        norm_a = a.lower().replace(".", "").replace("-", " ").split()
        norm_b = b.lower().replace(".", "").replace("-", " ").split()
        return norm_a == norm_b

    # KB height stated vs derived. #16 states 16' APD; 2888 - 2873 = 15.
    stated_kb = found.get("kb_height_ft")
    if isinstance(stated_kb, Quantity) and \
            "kb_elevation_ft" in elevations and "ground_elevation_ft" in elevations:
        derived = elevations["kb_elevation_ft"] - elevations["ground_elevation_ft"]
        if abs(derived - float(stated_kb.value)) > _EPS:
            _add_conflict(
                conflicts, "kb_height_disagreement",
                "the stated Kelly bushing height and the one implied by the KB and "
                "ground elevations disagree; no source states a tolerance, so both are "
                "reported and neither is chosen",
                {"stated": float(stated_kb.value), "derived": derived,
                 "kb_elevation_ft": elevations["kb_elevation_ft"],
                 "ground_elevation_ft": elevations["ground_elevation_ft"]},
            )

    if dmf_name and lmf_name and not same(dmf_name, lmf_name):
        _add_conflict(
            conflicts, "measured_from_disagreement",
            "the log and the driller measured depth from different references; "
            "driller's depths and log depths are not interchangeable",
            {"log_measured_from": lmf_name, "drilling_measured_from": dmf_name},
        )

    offset = None
    lmf_elevation = elevation_of(lmf_name)
    pdat_elevation = elevations.get("permanent_datum_elevation_ft")
    if pdat_elevation is None:
        pdat_elevation = elevation_of(pdat_name)
    if lmf_elevation is not None and pdat_elevation is not None:
        offset = lmf_elevation - pdat_elevation

    common = dict(permanent_datum=pdat_name, log_measured_from=lmf_name,
                  drilling_measured_from=dmf_name, offset_ft=offset,
                  elevations=elevations)

    if lmf_name and pdat_name and not same(lmf_name, pdat_name):
        _add_conflict(
            conflicts, "datum_mismatch",
            f"the permanent datum is {pdat_name!r} but the log is measured from "
            f"{lmf_name!r}"
            + (f", {offset:+.2f} ft away" if offset is not None else
               " and the offset between them is not computable from this header"),
            {"permanent_datum": pdat_name, "log_measured_from": lmf_name,
             "offset_ft": offset},
        )
        return DatumReport(
            status="conflict",
            detail="permanent datum and log-measured-from name different references; "
                   "datum_resolve (#15) must settle this before any depth is used "
                   "structurally",
            **common)
    if lmf_name:
        return DatumReport(
            status="resolved",
            detail=f"log depths are measured from {lmf_name!r}"
                   + ("" if pdat_name else "; no permanent datum is stated"),
            **common)
    if pdat_name:
        return DatumReport(
            status="unresolved",
            detail=f"a permanent datum ({pdat_name!r}) is stated but the header does not "
                   "say what the log is measured from; RRC item M is unsatisfied and the "
                   "depths may not be assumed to be on the permanent datum",
            **common)
    return DatumReport(
        status="absent",
        detail="the header states neither a permanent datum nor what the log is "
               "measured from; RRC item M is unsatisfied",
        **common)


def header_extract(sections: Any, *, source_file: str | None = None,
                   strict_units: bool = False) -> HeaderExtract | Refusal:
    """Well identity and operational metadata, checked against RRC items A-P.

    Consumes `las_parse` output (see the assumed interface above). Returns a
    `HeaderExtract` reporting what was found, what is missing, what is present
    but unusable, and where the header contradicts itself - or a `Refusal` when
    there is no LAS 2.0 header to read at all.

    Nothing is defaulted and nothing is inferred: a missing mandatory item is
    reported missing, a datum conflict is reported as a conflict, and BHT is
    never derived from the maximum recorded temperature.
    """
    indexed = _index(_unwrap(sections))

    if "W" not in indexed or not indexed["W"]:
        return Refusal(
            reason="no ~W section: LAS 2.0 requires it, so this file has no readable "
                   "well header and nothing can be extracted",
            needed=("a ~W (Well Information) section",),
            source=LAS_SECTIONS,
        )

    header_flags: list[str] = []
    if "P" not in indexed or not indexed["P"]:
        header_flags.append(
            "no ~P section; ~P is optional in LAS 2.0, and every RRC item other than "
            "A, B, C, F and O is sourced from it, so those items are reported missing "
            "rather than assumed")

    found: dict[str, Quantity | TextField] = {}
    missing_fields: list[str] = []
    blank_fields: list[str] = []
    for letter, item in RRC_HEADER_ITEMS.items():
        for spec in item.fields:
            hit = _find(indexed, spec)
            if hit is None:
                if spec.required:
                    missing_fields.append(spec.name)
                continue
            section, entry = hit
            if not entry["value"]:
                # A blank cell satisfies nothing, so the field counts as
                # missing and no value is substituted. But "the logger had this
                # field and left it empty" is not the same fact as "this header
                # has no such field", so the blank is recorded separately. #16
                # prints Density / Viscosity and Max. Recorded Temp. blank, and
                # carries no mud-resistivity row at all.
                blank_fields.append(spec.name)
                if spec.required:
                    missing_fields.append(spec.name)
                continue
            found[spec.name] = _build(spec, section, entry, source_file)

    if "log_types" not in found:
        derived = _log_types_from_curves(indexed, source_file)
        if derived is not None:
            found["log_types"] = derived
            if "log_types" in missing_fields:
                missing_fields.remove("log_types")

    if not found:
        return Refusal(
            reason="a ~W section is present but not one field of the RRC log-header "
                   "list could be read from it; this is not a header this tool can "
                   "report on",
            needed=("LAS header entries whose mnemonics match the contract; see "
                    "mnemonic_normalize (#9) for unrecognized mnemonics",),
            source=RRC_HEADER_LIST,
        )

    conflicts: list[Conflict] = []
    datum = _datum_report(found, conflicts)

    # Item J: a resistivity without its own stated temperature is unusable.
    unusable: list[str] = []
    for res_name, temp_name in RESISTIVITY_TEMPERATURE_PAIRS.items():
        if res_name in found and temp_name not in found:
            unusable.append(res_name)
            existing = found[res_name]
            extra = (f"no stated measurement temperature ({temp_name}); RRC item J "
                     "requires the value at its measured temperature, so this "
                     "resistivity is unusable for temperature correction",)
            if "mud_sample_temperature" in found:
                extra += ("a mud sample temperature is present, but assigning it to this "
                          "resistivity is an inference this tool does not make",)
            found[res_name] = _with_flags(existing, extra)

    if strict_units:
        for name, value in found.items():
            if any("outside the accepted set" in flag for flag in value.flags):
                unusable.append(name)

    satisfied: list[str] = []
    missing_items: list[str] = []
    for letter, item in RRC_HEADER_ITEMS.items():
        required = item.required_fields()
        present = [f.name for f in required if f.name in found]
        if item.satisfy == "any":
            ok = bool(present)
        else:
            ok = len(present) == len(required)
        if ok and letter == "J":
            ok = not any(name in unusable for name in RESISTIVITY_TEMPERATURE_PAIRS)
        (satisfied if ok else missing_items).append(letter)

    if blank_fields:
        header_flags.append(
            "the header carries these fields but leaves them blank: "
            + ", ".join(sorted(set(blank_fields)))
            + "; a blank cell satisfies no RRC item, and it is reported as blank "
              "rather than as absent because the two are different findings")
    if "api_number" not in found:
        header_flags.append("no API number in the header; the RRC identifies wells by "
                            "API, so this header cannot be tied to an RRC record")
    if datum.status != "resolved":
        header_flags.append(f"depth reference (RRC item M) is {datum.status}: "
                            f"{datum.detail}")
    if "max_recorded_temp" not in found and "bht_reported" in found:
        header_flags.append("the header reports a bottom-hole temperature but no maximum "
                            "recorded temperature; item N is unsatisfied and Tmax is not "
                            "inferred from BHT")

    return HeaderExtract(
        fields=found,
        items_satisfied=tuple(satisfied),
        missing_items=tuple(missing_items),
        missing_fields=tuple(sorted(set(missing_fields))),
        unusable=tuple(sorted(set(unusable))),
        conflicts=tuple(conflicts),
        datum=datum,
        blank_fields=tuple(sorted(set(blank_fields))),
        flags=tuple(header_flags),
        source=RRC_HEADER_LIST,
        source_file=source_file,
    )


def _with_flags(value: Quantity | TextField,
                extra: tuple[str, ...]) -> Quantity | TextField:
    """Frozen dataclasses; rebuild rather than mutate."""
    if isinstance(value, Quantity):
        return Quantity(value=value.value, unit=value.unit, method=value.method,
                        source=value.source, inputs=value.inputs,
                        assumptions=value.assumptions, flags=value.flags + extra)
    return TextField(value=value.value, method=value.method, source=value.source,
                     inputs=value.inputs, flags=value.flags + extra)
