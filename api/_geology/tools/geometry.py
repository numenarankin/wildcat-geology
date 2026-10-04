"""Wellbore geometry and the datum gate.

Everything structural in this layer stands on two things being right: the
minimum-curvature arithmetic, and knowing which elevation the depths are hung
on. Both have already gone wrong here, so both are pinned.

**The dogleg formula.** The one used is from
`17-directional-survey/drillingformulas-minimum-curvature-method`, validated
against that page's worked example. It is NOT the form printed in the thesis in
the same corpus section, whose Eq. 4.1 reads `(cos B2 - cos B1)` where it needs
`cos(B2 - B1)` and returns 31.79 degrees where the published answer is 12.95.
`tests/test_layer1.py` fails if the corrupt form is ever reintroduced. Beta is
in radians everywhere; the source says so, and converting at the boundary is
where published implementations go wrong.

**The datum.** `datum_resolve` is the gate, and its precedence policy is OURS,
not the corpus's — nothing published says what to do when a log heading, a LAS
`~W`/`~P` section and a state form disagree. So the policy is a module-level
table, every result carries which rule fired, and an unresolved datum stays
unresolved rather than defaulting. There are **four** references, not three:
`asquith#10` lists K.B., D.F., G.L. and T.K.B., and top of kelly bushing is a
distinct datum, never a spelling of KB.

`subsea_convert` therefore converts against the reference the depths are
actually hung on, not against whatever elevation it was handed. The real header
at `rrc-section-f#16` is why: its permanent datum is ground level at 2873 ft
while the log is measured from the kelly bushing at 2888 ft, so using the
permanent datum would put every subsea depth in that well out by 15 ft — an
error indistinguishable from real structure. The sign convention is negative
below sea level, fixed by Tearpock's own worked correction ("adjusted upward 10
ft... from -9748 ft to -9738 ft"), and it is asserted rather than assumed
because getting it backwards doubles the elevation difference instead of
cancelling it.

`structural_dip` returns **apparent** dip from two picks and refuses true dip
outright: three non-collinear picks do determine a plane, but the three-point
construction is not published anywhere in this corpus, and an invented equation
is the worst outcome available to this build.
"""
from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from dataclasses import dataclass, field as dc_field
from typing import Any
from typing import Any, Mapping
from typing import Any, Mapping, Sequence
import math
import re

from .result import Quantity, Range, Refusal
from .result import Quantity, Range, Refusal  # noqa: F401  (Range re-exported for the module)
from .result import Quantity, Range, Refusal  # noqa: F401  (Range: group contract)
from .result import Quantity, Range, Refusal  # noqa: F401  (house import contract)
# #16 converts a non-foot elevation through the real unit_convert (#11) rather
# than assuming feet; see `_elevation_16`.
from .units import unit_convert

# ---------------------------------------------------------------------------
# 15_datum_resolve
# The datum gate: which reference the log's depths are hung on, and its elevation.
# ---------------------------------------------------------------------------

ASQUITH_HEADING = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#10"
TEARPOCK_DATUM = "06-fort-worth-basin/tearpock-bischke-applied-subsurface-geological-mapping#24"
RRC_REAL_HEADER = "09-gas-deliverability/rrc-section-f-completions-electric-logs#16"

# Float hygiene, not a domain tolerance. The corpus states no allowance for how
# far two elevations may sit apart, so any real difference is surfaced; see
# `max_elevation_disagreement_ft` (R11, CALLER).
_EPS = 1e-9


# ---------------------------------------------------------------------------
# The four references (plus the two that appear on real headers unsourced)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Reference:
    """One depth reference, its printed name, and whether the corpus names it."""

    key: str
    name: str
    status: str          # SOURCED | UNSOURCED
    source: str
    note: str = ""


REFERENCES: dict[str, Reference] = {
    "KB": Reference("KB", "kelly bushing", "SOURCED", ASQUITH_HEADING,
                    "asquith#10 fig 1.2 item 5 'K.B. = kelly bushing elevation'; "
                    "tearpock#24 'KB Vertical distance from kelly bushing to sea level'"),
    "DF": Reference("DF", "drill floor", "SOURCED", ASQUITH_HEADING,
                    "asquith#10 fig 1.2 item 5 'D.F. = drill floor elevation'; "
                    "'derrick floor' on a scanned header normalises here too"),
    "GL": Reference("GL", "ground level", "SOURCED", ASQUITH_HEADING,
                    "asquith#10 fig 1.2 item 5 'G.L. = ground level elevation'"),
    "TKB": Reference("TKB", "top of kelly bushing", "SOURCED", ASQUITH_HEADING,
                     "asquith#10 fig 1.2 item 5 'T.K.B. = top of kelly bushing'. "
                     "A DISTINCT reference from KB, not a spelling of it"),
    "MSL": Reference("MSL", "mean sea level", "SOURCED", TEARPOCK_DATUM,
                     "tearpock#24: SSTVD is measured from sea level, the common datum"),
    "RT": Reference("RT", "rotary table", "UNSOURCED", "",
                    "seen on real headers, absent from the corpus; resolves only "
                    "from its own stated elevation (R10)"),
    "CH": Reference("CH", "casing head", "UNSOURCED", "",
                    "seen on real headers, absent from the corpus; resolves only "
                    "from its own stated elevation (R10)"),
}

# Longest / most specific FIRST. "top of kelly bushing" must not be eaten by
# "kelly bushing", and that ordering is the whole four-references guard.
_REFERENCE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("TKB", r"top\s+of\s+(?:the\s+)?kelly\s+bushing|top\s+of\s+kb|\btkb\b|\bt\s*k\s*b\b"),
    ("KB", r"kelly\s+bushing|kelly\s+bushing\s+elevation|\bkb\b|\bk\s*b\b"),
    ("DF", r"drill(?:ing)?\s+floor|derrick\s+floor|\bdf\b|\bd\s*f\b"),
    ("GL", r"ground\s+level|ground\s+elevation|ground\s+surface|\bgl\b|\bg\s*l\b"),
    ("MSL", r"mean\s+sea\s+level|\bsea\s+level\b|\bmsl\b"),
    ("RT", r"rotary\s+table|rotary\s+bushing|\brt\b|\br\s*t\b"),
    ("CH", r"casing\s+head|casing\s+flange|\bch\b"),
)

# Elevation field names as the two upstream tools spell them.
_ELEVATION_KEYS: tuple[tuple[str, str], ...] = (
    ("TKB", r"^(?:tkb|t\.?k\.?b\.?|top\s*of\s*kelly\s*bushing|tkb_elevation_ft|etkb)$"),
    ("KB", r"^(?:kb|k\.?b\.?|kelly\s*bushing|kb_elevation_ft|ekb|elkb)$"),
    ("DF", r"^(?:df|d\.?f\.?|drill(?:ing)?\s*floor|derrick\s*floor|df_elevation_ft|edf|eldf)$"),
    ("GL", r"^(?:gl|g\.?l\.?|ground\s*level|ground_elevation_ft|gl_elevation_ft|egl|elgl|elev)$"),
    ("PD", r"^(?:pd|permanent\s*datum|permanent_datum_elevation_ft|epd|pdate)$"),
    ("RT", r"^(?:rt|r\.?t\.?|rotary\s*table|rt_elevation_ft)$"),
    ("CH", r"^(?:ch|casing\s*head|casing\s*flange|ch_elevation_ft)$"),
    ("MSL", r"^(?:msl|sea\s*level|mean\s*sea\s*level)$"),
)

_ACCEPTED_ELEVATION_UNITS = ("FT", "F", "FEET", "'", "(UNSTATED)", "")


# ---------------------------------------------------------------------------
# The precedence policy. OWNED, not sourced. Tables, not code order.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceRank:
    rank: int
    key: str
    label: str
    status: str
    rationale: str
    can_resolve_alone: bool = True


PRECEDENCE: dict[str, SourceRank] = {
    "log_heading": SourceRank(
        1, "log_heading", "the log heading's own 'Log Measured From' box", "OWNED",
        "asquith#10 fig 1.2 item 5 states this block is 'information about "
        "location and elevation from which the well depths are measured', so it "
        "is the contractor's statement about the log in hand. The ordering above "
        "the LAS is ours."),
    "las_header": SourceRank(
        2, "las_header", "the LAS ~W/~P header", "OWNED",
        "a transcription of the heading, made later and by a different party; "
        "transcription is where the reference gets dropped."),
    "state_form": SourceRank(
        3, "state_form", "a state completion form (RRC W-2 / G-1 / W-15)", "OWNED",
        "describes the well and is filed against the permanent datum, which is "
        "precisely the quantity that is not the answer to this question."),
    "free_text": SourceRank(
        4, "free_text", "a note printed on the log face", "OWNED",
        "evidence that a stated value is right, never evidence of what it is.",
        can_resolve_alone=False),
}

DEFAULT_PRECEDENCE: tuple[str, ...] = ("log_heading", "las_header", "state_form",
                                       "free_text")


@dataclass(frozen=True)
class Rule:
    id: str
    status: str          # OWNED | CALLER | SOURCED
    text: str


RULES: dict[str, Rule] = {
    "R1-agreement": Rule(
        "R1-agreement", "OWNED",
        "every source that states a depth reference names the same one; resolved, "
        "with the corroborating sources listed"),
    "R2-precedence": Rule(
        "R2-precedence", "OWNED",
        "sources disagree; the highest-ranked source wins, the losers are named "
        "with the elevation the choice is worth, and this is house policy"),
    "R3-tie-unresolved": Rule(
        "R3-tie-unresolved", "OWNED",
        "two sources at the same rank disagree; precedence has nothing left to "
        "say and a coin flip is a guess, so unresolved"),
    "R4-strict-unresolved": Rule(
        "R4-strict-unresolved", "CALLER",
        "strict=True: any cross-source disagreement is unresolved and the "
        "precedence is not applied"),
    "R5-permanent-datum-is-not-the-answer": Rule(
        "R5-permanent-datum-is-not-the-answer", "OWNED",
        "a permanent datum stated with no 'log measured from' is unresolved; the "
        "permanent datum is what elevations are quoted against, not what depths "
        "are hung on, and it is never substituted"),
    "R6-log-over-driller": Rule(
        "R6-log-over-driller", "OWNED",
        "log-measured-from and drilling-measured-from differ; the log's statement "
        "wins for log depths, and the difference is flagged"),
    "R7-stated-over-derived": Rule(
        "R7-stated-over-derived", "OWNED",
        "a stated elevation beats one derived from another reference plus a "
        "height; derivation is used only where nothing is stated, and is flagged"),
    "R8-no-derivation-through-a-disagreement": Rule(
        "R8-no-derivation-through-a-disagreement", "OWNED",
        "the only route to the elevation runs through a quantity two sources "
        "disagree about; unresolved, never averaged"),
    "R9-tkb-is-not-kb": Rule(
        "R9-tkb-is-not-kb", "OWNED",
        "KB and TKB elevations are both present and differ while the reference is "
        "stated as unqualified 'kelly bushing'; unresolved, naming both"),
    "R10-unsourced-reference-needs-its-own-elevation": Rule(
        "R10-unsourced-reference-needs-its-own-elevation", "OWNED",
        "rotary table, casing head or any reference the corpus does not name "
        "resolves only from an explicitly stated elevation of its own"),
    "R11-elevation-disagreement-tolerance": Rule(
        "R11-elevation-disagreement-tolerance", "CALLER",
        "two sources give different elevations for the same reference; precedence "
        "picks and the difference is flagged. The corpus states no tolerance, so "
        "there is no default: the caller supplies max_elevation_disagreement_ft "
        "or every disagreement is surfaced"),
    "R0-no-evidence": Rule(
        "R0-no-evidence", "OWNED",
        "no evidence source was supplied at all"),
}


def policy_statement(precedence: Sequence[str] = DEFAULT_PRECEDENCE) -> str:
    """The precedence rendered for display. Travels on every result.

    The catalog requires the policy be visible wherever the answer is rendered,
    so it is a returned string and not a docstring.
    """
    ranked = ", then ".join(
        f"{PRECEDENCE[k].label}" for k in precedence if k in PRECEDENCE)
    return ("HOUSE POLICY, NOT SOURCED - no source in the corpus states what to "
            "do when a log heading, a LAS ~W/~P section and a state form "
            f"disagree about the depth reference. This answer used: {ranked}. "
            "A permanent datum is never substituted for a depth reference.")


# ---------------------------------------------------------------------------
# Value types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DatumStatement:
    """One source's claim about what the depths are measured from."""

    source_key: str
    rank: int
    role: str                        # log measured from | drilling measured from | permanent datum
    raw: str                         # as printed
    reference: str | None            # normalised key, None when unrecognised
    upstream_status: str = ""        # e.g. header_extract's DatumReport.status
    provenance: str = ""


@dataclass(frozen=True)
class Disagreement:
    kind: str
    detail: str
    values: dict[str, Any] = dc_field(default_factory=dict)
    offset_ft: float | None = None
    blocking: bool = False


@dataclass(frozen=True)
class DatumResolution:
    """Resolved or unresolved. `resolved` is the gate `subsea_convert` takes."""

    resolved: bool
    rule: str
    rule_status: str
    policy: str
    precedence_used: tuple[str, ...]
    reference: str | None = None
    reference_name: str | None = None
    elevation: Quantity | None = None
    winning_source: str | None = None
    permanent_datum: str | None = None
    permanent_datum_offset: Quantity | None = None
    references: dict[str, Quantity] = dc_field(default_factory=dict)
    kb_height: Quantity | Range | None = None
    statements: tuple[DatumStatement, ...] = ()
    disagreements: tuple[Disagreement, ...] = ()
    refusal: Refusal | None = None
    flags: tuple[str, ...] = ()
    source: str = ASQUITH_HEADING

    def __post_init__(self) -> None:
        if self.resolved and self.elevation is None:
            raise ValueError("a resolved datum must carry an elevation")
        if not self.resolved and self.refusal is None:
            raise ValueError("an unresolved datum must carry its Refusal")

    def __repr__(self) -> str:
        if not self.resolved:
            return f"DatumResolution(unresolved, {self.rule})"
        return (f"DatumResolution({self.reference} @ {self.elevation.value:g} ft, "
                f"{self.rule})")


def subsea_datum_inputs(result: DatumResolution | Refusal
                        ) -> tuple[float | None, bool, str]:
    """(elevation_ft, resolved, reference) -- exactly subsea_convert's arguments.

    Wiring these three by hand is how a caller ends up passing
    `datum_resolved=True` alongside a `None` elevation; they travel together.
    """
    if isinstance(result, Refusal) or not result.resolved or result.elevation is None:
        return (None, False, "")
    return (float(result.elevation.value), True, result.reference or "")


def require_datum(result: DatumResolution | Refusal) -> Quantity | Refusal:
    """The downstream gate, mirroring `raster.require_item`.

    Returns the elevation when resolved, the Refusal when not, so an unresolved
    datum propagates as a refusal-grade value instead of a None.
    """
    if isinstance(result, Refusal):
        return result
    if result.resolved and result.elevation is not None:
        return result.elevation
    return result.refusal or Refusal(
        reason="datum unresolved", needed=("a resolved depth reference",),
        source=ASQUITH_HEADING)


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalize_reference(text: Any) -> str | None:
    """Printed reference name -> reference key, or None if unrecognised.

    Ordered most-specific-first so "top of kelly bushing" cannot be read as
    "kelly bushing". Returns None rather than a best guess: an unrecognised
    reference is a refusal condition (R10), not a KB.
    """
    if text is None:
        return None
    probe = str(text).strip().lower()
    if not probe:
        return None
    probe = probe.replace(".", " ").replace("-", " ").replace("_", " ")
    probe = re.sub(r"\s+", " ", probe).strip()
    if probe in REFERENCES:                    # already a key
        return probe.upper()
    if probe.upper() in REFERENCES:
        return probe.upper()
    for key, pattern in _REFERENCE_PATTERNS:
        if re.search(pattern, probe):
            return key
    return None


def _elevation_key(name: Any) -> str | None:
    probe = str(name).strip().lower()
    probe = re.sub(r"\s+", " ", probe)
    for key, pattern in _ELEVATION_KEYS:
        if re.match(pattern, probe):
            return key
    return None


def _as_float(value: Any) -> float | None:
    """A number out of a Quantity, a float, or a header string like "2888'"."""
    if value is None:
        return None
    if isinstance(value, Quantity):
        return float(value.value)
    if isinstance(value, Range):
        return None                      # a band is not a number; R8 handles it
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    text = text.replace('"', " ").replace("'", " ").replace("’", " ").strip()
    text = re.sub(r"\s*(ft|feet|f)\s*$", "", text, flags=re.I).strip()
    try:
        return float(text)
    except ValueError:
        return None


def _unit_of(value: Any) -> str:
    if isinstance(value, (Quantity, Range)):
        return str(value.unit or "")
    return ""


def _unit_is_feet(value: Any) -> bool:
    unit = _unit_of(value).strip().upper().replace(".", "")
    return unit in _ACCEPTED_ELEVATION_UNITS


# ---------------------------------------------------------------------------
# Evidence gathering. Both upstream tools are written concurrently, so their
# shapes are read tolerantly: the documented attribute first, a mapping key
# second. A shape this cannot read is reported, never guessed at.
# ---------------------------------------------------------------------------

def _get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


@dataclass
class _Evidence:
    """Everything gathered from one source, before any policy is applied."""

    key: str
    rank: int
    statements: list[DatumStatement] = dc_field(default_factory=list)
    elevations: dict[str, tuple[float, str, Any]] = dc_field(default_factory=dict)
    kb_heights: list[tuple[float, str]] = dc_field(default_factory=list)
    kb_height_band: Range | None = None
    permanent_datum: str | None = None
    flags: list[str] = dc_field(default_factory=list)

    def reference(self) -> DatumStatement | None:
        for st in self.statements:
            if st.role == "log measured from":
                return st
        return None


def _record_elevation(ev: _Evidence, key: str | None, raw: Any, provenance: str,
                      flags: list[str]) -> None:
    if key is None or key == "MSL":
        return
    if isinstance(raw, Range):
        flags.append(f"{ev.key}: the elevation for {key} is a band, not a value; "
                     "it is not used to resolve an elevation (R8)")
        return
    number = _as_float(raw)
    if number is None:
        return
    if isinstance(raw, (Quantity,)) and not _unit_is_feet(raw):
        flags.append(f"{ev.key}: elevation for {key} is stated in "
                     f"{_unit_of(raw)!r}, not feet; unit_convert (#11) owns "
                     "conversion, so it is not used here")
        return
    # An elevation row that carries no unit at all is READ AS FEET, because the
    # corpus's headers are onshore Texas and both real LAS fixtures leave EPD and
    # APD unitless. That is a house reading, not a stated one, and this tool
    # refuses metres precisely because the unit decides the answer -- so the
    # assumption is surfaced rather than made silently. It changes no value.
    if isinstance(raw, Quantity) and not _unit_of(raw).strip().strip("()").upper() \
            in ("FT", "F", "FEET", "'"):
        flags.append(f"{ev.key}: the elevation for {key} carries no unit "
                     f"({_unit_of(raw)!r}); it is READ AS FEET, which is an "
                     "assumption of this tool and not a statement of the header")
    ev.elevations[key] = (number, provenance, raw)


def _from_header(header: Any, flags: list[str]) -> _Evidence:
    """`header_extract` (#4): a HeaderExtract, or its DatumReport directly."""
    ev = _Evidence("las_header", PRECEDENCE["las_header"].rank)
    report = _get(header, "datum", None)
    if report is None and _get(header, "log_measured_from", "__missing__") != "__missing__":
        report = header                      # a bare DatumReport was passed
    fields = _get(header, "fields", None) or {}

    status = str(_get(report, "status", "") or "")
    lmf = _get(report, "log_measured_from", None)
    dmf = _get(report, "drilling_measured_from", None)
    pdat = _get(report, "permanent_datum", None)

    for role, raw in (("log measured from", lmf),
                      ("drilling measured from", dmf),
                      ("permanent datum", pdat)):
        if raw is None or not str(raw).strip():
            continue
        key = normalize_reference(raw)
        ev.statements.append(DatumStatement(
            source_key=ev.key, rank=ev.rank, role=role, raw=str(raw).strip(),
            reference=key, upstream_status=status,
            provenance="header_extract (#4) DatumReport"))
        if key is None:
            flags.append(f"las_header: {role} reads {str(raw).strip()!r}, which is "
                         "not one of the references the corpus names (R10)")
    ev.permanent_datum = normalize_reference(pdat)

    elevations = _get(report, "elevations", None) or {}
    if isinstance(elevations, Mapping):
        for name, raw in elevations.items():
            _record_elevation(ev, _elevation_key(name), raw,
                              "header_extract DatumReport.elevations", flags)
    if isinstance(fields, Mapping):
        for name, raw in fields.items():
            key = _elevation_key(name)
            if key and key not in ev.elevations:
                _record_elevation(ev, key, raw, f"header_extract fields[{name!r}]",
                                  flags)
        height = fields.get("kb_height_ft")
        if isinstance(height, Range):
            ev.kb_height_band = height
        else:
            number = _as_float(height)
            if number is not None:
                ev.kb_heights.append(
                    (number, "header_extract fields['kb_height_ft'] (APD)"))

    if status:
        ev.flags.append(f"header_extract reports item M as {status!r}; read here as "
                        "evidence, not as an answer")
    return ev


def _from_raster(raster: Any, flags: list[str]) -> _Evidence:
    """`raster_header_ocr` (#6): a RasterHeader."""
    ev = _Evidence("log_heading", PRECEDENCE["log_heading"].rank)
    items = _get(raster, "items", None) or {}
    if not isinstance(items, Mapping):
        return ev

    m_field = items.get("M")
    m_value = _get(m_field, "value", None)
    if isinstance(m_value, Mapping):
        for role_raw, raw in m_value.items():
            role = str(role_raw).strip().lower()
            if role == "measured from":
                role = "log measured from"
            if role not in ("log measured from", "drilling measured from",
                            "permanent datum"):
                flags.append(f"log_heading: item M carries {role_raw!r}, which is not "
                             "a datum role this tool reads")
                continue
            key = normalize_reference(raw)
            ev.statements.append(DatumStatement(
                source_key=ev.key, rank=ev.rank, role=role, raw=str(raw).strip(),
                reference=key, provenance="raster_header_ocr (#6) item M"))
            if key is None:
                flags.append(f"log_heading: {role} reads {str(raw).strip()!r}, which "
                             "is not one of the references the corpus names (R10)")
            if role == "permanent datum":
                ev.permanent_datum = key
    elif m_value is not None:
        flags.append("log_heading: item M is not a role->reference mapping; "
                     "raster_header_ocr reports it unpaired, so it states nothing "
                     "this tool can use")

    k_value = _get(items.get("K"), "value", None)
    if isinstance(k_value, Mapping):
        for name, raw in k_value.items():
            _record_elevation(ev, _elevation_key(name), raw,
                              f"raster_header_ocr item K[{name!r}]", flags)

    l_value = _get(items.get("L"), "value", None)
    if isinstance(l_value, Range):
        ev.kb_height_band = l_value
    else:
        number = _as_float(l_value)
        if number is not None:
            ev.kb_heights.append((number, "raster_header_ocr item L (APD)"))

    for conflict in (_get(raster, "conflicts", None) or ()):
        kind = str(_get(conflict, "kind", ""))
        if kind:
            ev.flags.append(f"raster_header_ocr reported {kind!r}: "
                            f"{_get(conflict, 'detail', '')}")
    return ev


def _from_state_form(form: Any, flags: list[str]) -> _Evidence:
    if not isinstance(form, Mapping):
        raise TypeError("state_form must be a mapping; got "
                        f"{type(form).__name__}")
    ev = _Evidence("state_form", PRECEDENCE["state_form"].rank)
    label = str(form.get("form") or "state form")
    raw = form.get("reference") or form.get("log_measured_from")
    if raw:
        key = normalize_reference(raw)
        ev.statements.append(DatumStatement(
            source_key=ev.key, rank=ev.rank, role="log measured from",
            raw=str(raw).strip(), reference=key, provenance=label))
        if key is None:
            flags.append(f"state_form: reference reads {str(raw).strip()!r}, which is "
                         "not one of the references the corpus names (R10)")
    pdat = form.get("permanent_datum")
    if pdat:
        ev.permanent_datum = normalize_reference(pdat)
        ev.statements.append(DatumStatement(
            source_key=ev.key, rank=ev.rank, role="permanent datum",
            raw=str(pdat).strip(), reference=ev.permanent_datum, provenance=label))
    for name, value in (form.get("elevations") or {}).items():
        _record_elevation(ev, _elevation_key(name), value, label, flags)
    height = _as_float(form.get("kb_height_ft"))
    if height is not None:
        ev.kb_heights.append((height, f"{label} kb_height_ft"))
    return ev


_FREE_TEXT_KB = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:'|’|ft\b|feet\b)?\s*(kb|kelly\s+bushing)\b", re.I)
_FREE_TEXT_MEASURED = re.compile(
    r"(?:log(?:ged)?|depths?|measured)\s+(?:\w+\s+){0,3}?from\s+(?:the\s+)?"
    r"(top\s+of\s+(?:the\s+)?kelly\s+bushing|kelly\s+bushing|drill(?:ing)?\s+floor|"
    r"derrick\s+floor|ground\s+level|rotary\s+table|kb|df|gl|rt|tkb)\b", re.I)


def _from_free_text(text: str) -> _Evidence:
    """Rank 4. Corroboration only -- `can_resolve_alone=False`."""
    ev = _Evidence("free_text", PRECEDENCE["free_text"].rank)
    match = _FREE_TEXT_MEASURED.search(text)
    if match:
        key = normalize_reference(match.group(1))
        ev.statements.append(DatumStatement(
            source_key=ev.key, rank=ev.rank, role="log measured from",
            raw=match.group(0).strip(), reference=key,
            provenance="a note printed on the log face"))
    for m in _FREE_TEXT_KB.finditer(text):
        ev.kb_heights.append((float(m.group(1)),
                              f"free text {m.group(0).strip()!r}"))
    return ev


# ---------------------------------------------------------------------------
# The resolution
# ---------------------------------------------------------------------------

def _unresolved(rule: str, reason: str, needed: tuple[str, ...],
                precedence: tuple[str, ...], **carry: Any) -> DatumResolution:
    return DatumResolution(
        resolved=False,
        rule=rule,
        rule_status=RULES[rule].status,
        policy=policy_statement(precedence),
        precedence_used=precedence,
        refusal=Refusal(reason=reason, needed=needed, source=ASQUITH_HEADING),
        **carry)


def _merge_elevations(evidence: list[_Evidence], precedence: tuple[str, ...],
                      max_disagreement: float | None,
                      disagreements: list[Disagreement],
                      ) -> tuple[dict[str, Quantity], bool]:
    """Reference key -> elevation, precedence-picked, every disagreement named.

    Returns (elevations, blocked). `blocked` is True only when the caller set
    `max_elevation_disagreement_ft` and a disagreement exceeded it (R11).
    """
    ordered = sorted(evidence, key=lambda e: precedence.index(e.key)
                     if e.key in precedence else 99)
    out: dict[str, Quantity] = {}
    chosen: dict[str, tuple[float, str, str]] = {}
    blocked = False
    for ev in ordered:
        for key, (number, provenance, _raw) in ev.elevations.items():
            if key not in chosen:
                chosen[key] = (number, ev.key, provenance)
                continue
            kept, kept_source, kept_prov = chosen[key]
            if abs(kept - number) <= _EPS:
                continue
            delta = number - kept
            over = (max_disagreement is not None
                    and abs(delta) > max_disagreement + _EPS)
            disagreements.append(Disagreement(
                kind="elevation_disagreement",
                detail=(f"{key} elevation is {kept:g} ft per {kept_source} and "
                        f"{number:g} ft per {ev.key}; {kept_source} is kept by "
                        "precedence (R2/R11) and neither value is averaged"
                        + (f", but the difference exceeds the caller's "
                           f"{max_disagreement:g} ft allowance" if over else "")),
                values={"reference": key, kept_source: kept, ev.key: number,
                        "kept_provenance": kept_prov, "other_provenance": provenance},
                offset_ft=delta, blocking=over))
            if over:
                blocked = True
    for key, (number, source_key, provenance) in chosen.items():
        ref = REFERENCES.get(key)
        out[key] = Quantity(
            number, "ft",
            f"elevation above sea level of the {ref.name if ref else key}, as "
            f"stated by {PRECEDENCE[source_key].label if source_key in PRECEDENCE else source_key}",
            ref.source if ref and ref.source else ASQUITH_HEADING,
            inputs={"source_key": source_key, "provenance": provenance,
                    "reference": key},
            assumptions={"sign": "positive above sea level (tearpock#24)"},
            flags=() if not ref or ref.status == "SOURCED" else
            (f"{key} is not a reference the corpus names; it resolves only from "
             "its own stated elevation (R10)",))
    return out, blocked


def _kb_height(evidence: list[_Evidence], elevations: dict[str, Quantity],
               precedence: tuple[str, ...], flags: list[str],
               disagreements: list[Disagreement]) -> Quantity | Range | None:
    """Stated KB height(s) plus the one the elevations imply. Never averaged."""
    members: dict[str, float] = {}
    band: Range | None = None
    for ev in sorted(evidence, key=lambda e: precedence.index(e.key)
                     if e.key in precedence else 99):
        if ev.kb_height_band is not None and band is None:
            band = ev.kb_height_band
        for number, provenance in ev.kb_heights:
            members.setdefault(f"stated: {provenance}", number)
    if "KB" in elevations and "GL" in elevations:
        members["derived: KB elevation - GL elevation"] = (
            elevations["KB"].value - elevations["GL"].value)
    if band is not None:
        for name, value in (band.members or {}).items():
            members.setdefault(f"upstream: {name}", float(value))
    if not members:
        return None
    values = sorted(set(round(v, 9) for v in members.values()))
    if len(values) == 1:
        return Quantity(
            values[0], "ft", "Kelly bushing height above the permanent datum "
            "(APD), all sources agreeing", ASQUITH_HEADING,
            inputs={"members": members})
    disagreements.append(Disagreement(
        kind="kb_height_disagreement",
        detail=("the Kelly bushing height is stated and derived at different "
                "values; both are reported as a band and neither is averaged. "
                "This does not by itself block the datum -- it blocks only an "
                "elevation that has to be derived through it (R8)"),
        values=dict(members), offset_ft=values[-1] - values[0]))
    flags.append(f"Kelly bushing height disagrees across sources: "
                 f"{', '.join(f'{k} = {v:g} ft' for k, v in members.items())}; "
                 "reported as a band, not averaged")
    return Range(min(values), max(values), "ft",
                 "Kelly bushing height: stated and derived values disagree, "
                 "reported as a band rather than a point",
                 ASQUITH_HEADING, members=members)


def datum_resolve(*,
                  header: Any = None,
                  raster: Any = None,
                  state_form: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
                  free_text: str | None = None,
                  precedence: Sequence[str] = DEFAULT_PRECEDENCE,
                  strict: bool = False,
                  max_elevation_disagreement_ft: float | None = None,
                  ) -> DatumResolution | Refusal:
    """Which reference the log's depths are hung on, and its elevation above MSL.

    Consumes `header_extract` (#4) and/or `raster_header_ocr` (#6) output, a
    transcribed state form, and free text from the log face. Returns a
    `DatumResolution` whose `resolved` flag is the gate `subsea_convert` (#18)
    takes -- or a bare `Refusal` when no evidence was supplied at all.

    Nothing is defaulted: a permanent datum is never substituted for a depth
    reference, an elevation is never invented, and two disagreeing values are
    never averaged.
    """
    order = tuple(precedence)
    for key in order:
        if key not in PRECEDENCE:
            raise ValueError(
                f"unknown precedence source {key!r}; the declared sources are "
                f"{tuple(PRECEDENCE)}")

    flags: list[str] = []
    disagreements: list[Disagreement] = []
    evidence: list[_Evidence] = []

    if raster is not None:
        evidence.append(_from_raster(raster, flags))
    if header is not None:
        evidence.append(_from_header(header, flags))
    if state_form is not None:
        # One well can have several forms on file (a W-2 and a G-1). They are
        # separate sources at the SAME rank, which is how R3 becomes reachable:
        # precedence cannot break a tie inside its own rank.
        forms = ([state_form] if isinstance(state_form, Mapping)
                 else list(state_form))
        for form in forms:
            evidence.append(_from_state_form(form, flags))
    if free_text:
        evidence.append(_from_free_text(free_text))

    if not evidence:
        return Refusal(
            reason="no datum evidence supplied: this tool reads a log heading, a "
                   "LAS header, a state form or a note from the log face, and was "
                   "given none of them",
            needed=("header_extract (#4) output",
                    "raster_header_ocr (#6) output",
                    "a transcribed state completion form",),
            source=ASQUITH_HEADING)

    for ev in evidence:
        if ev.key not in order:
            flags.append(f"{ev.key} evidence was supplied but {ev.key} is not in the "
                         "precedence the caller passed, so it was not consulted at all")
    evidence = [ev for ev in evidence if ev.key in order]
    for ev in evidence:
        flags.extend(ev.flags)

    elevations, blocked_by_tolerance = _merge_elevations(
        evidence, order, max_elevation_disagreement_ft, disagreements)

    statements: tuple[DatumStatement, ...] = tuple(
        st for ev in sorted(evidence, key=lambda e: order.index(e.key))
        for st in ev.statements)

    permanent_datum = next(
        (ev.permanent_datum for ev in sorted(evidence, key=lambda e: order.index(e.key))
         if ev.permanent_datum), None)

    # A header may print "Elevation of Permanent Datum" without repeating it under
    # the datum's own name. That is the same number, so it is aliased across --
    # not derived, not assumed, just the one value under both labels.
    if permanent_datum and "PD" in elevations and permanent_datum not in elevations:
        pd_q = elevations["PD"]
        elevations[permanent_datum] = Quantity(
            pd_q.value, "ft",
            f"elevation above sea level of the "
            f"{REFERENCES[permanent_datum].name}, read from the stated permanent-"
            f"datum elevation (the header names the permanent datum as that "
            f"reference)", pd_q.source, inputs=dict(pd_q.inputs),
            assumptions=dict(pd_q.assumptions),
            flags=pd_q.flags + ("taken from the permanent-datum elevation row",))

    kb_height = _kb_height(evidence, elevations, order, flags, disagreements)

    carry: dict[str, Any] = dict(
        references=elevations, kb_height=kb_height, statements=statements,
        permanent_datum=permanent_datum, flags=tuple(flags))

    def out(**extra: Any) -> dict[str, Any]:
        merged = dict(carry)
        merged.update(extra)
        merged["disagreements"] = tuple(disagreements)
        merged["flags"] = tuple(flags)
        return merged

    # --- R6: the log's statement wins over the driller's, and is flagged -----
    for ev in evidence:
        log_st = next((s for s in ev.statements if s.role == "log measured from"), None)
        drill_st = next((s for s in ev.statements
                         if s.role == "drilling measured from"), None)
        if log_st and drill_st and log_st.reference != drill_st.reference:
            disagreements.append(Disagreement(
                kind="log_vs_driller",
                detail=(f"{ev.key}: the log is measured from {log_st.raw!r} and the "
                        f"driller measured from {drill_st.raw!r}; these are log "
                        "depths, so the log's statement is used (R6)"),
                values={"log_measured_from": log_st.raw,
                        "drilling_measured_from": drill_st.raw}))
            flags.append(f"{ev.key}: log and driller measured depth from different "
                         "references; driller's depths are not interchangeable with "
                         "these")

    # --- who states a depth reference at all --------------------------------
    claims: list[DatumStatement] = [
        st for st in statements if st.role == "log measured from"]
    resolving = [st for st in claims
                 if PRECEDENCE[st.source_key].can_resolve_alone]

    if not resolving:
        corroborating = [st for st in claims if st not in resolving]
        pd_named = permanent_datum is not None
        reason = ("no source states what the log's depths are measured from"
                  + (f"; a permanent datum ({permanent_datum}) is stated, but the "
                     "permanent datum is the reference the elevations are quoted "
                     "against, not what the depths are hung on, and it is never "
                     "substituted (R5)" if pd_named else ""))
        if corroborating:
            reason += ("; a note on the log face names a reference, but free text "
                       "corroborates a stated value and never establishes one")
        return _unresolved(
            "R5-permanent-datum-is-not-the-answer",
            reason,
            ("the 'Log Measured From' box of the log heading (asquith#10 fig 1.2 "
             "item 5), or the LAS ~W/~P statement of it",),
            order, **out())

    # --- R1 / R2 / R3 / R4 ---------------------------------------------------
    by_rank: dict[int, list[DatumStatement]] = {}
    for st in resolving:
        by_rank.setdefault(st.rank, []).append(st)
    best_rank = min(by_rank)
    winners = by_rank[best_rank]

    distinct_all = {st.reference for st in resolving}
    if len(distinct_all) > 1:
        for st in resolving:
            if st.reference != winners[0].reference:
                a = elevations.get(winners[0].reference or "")
                b = elevations.get(st.reference or "")
                delta = (a.value - b.value) if (a and b) else None
                disagreements.append(Disagreement(
                    kind="reference_disagreement",
                    detail=(f"{st.source_key} states {st.raw!r} where "
                            f"{winners[0].source_key} states {winners[0].raw!r}"
                            + (f"; the choice is worth {delta:+.2f} ft on every "
                               "depth in the well" if delta is not None else
                               "; the elevation difference is not computable from "
                               "the evidence supplied")),
                    values={st.source_key: st.raw,
                            winners[0].source_key: winners[0].raw},
                    offset_ft=delta, blocking=strict))

    distinct_winners = {st.reference for st in winners}
    if len(distinct_winners) > 1:
        return _unresolved(
            "R3-tie-unresolved",
            "two sources of equal rank ("
            + PRECEDENCE[winners[0].source_key].label
            + ") name different depth references: "
            + ", ".join(sorted(f"{st.raw!r}" for st in winners))
            + "; the precedence policy cannot break a tie at its own rank and a "
              "coin flip is a guess",
            ("agreement between the equal-ranked sources, or a higher-ranked "
             "statement of the depth reference",),
            order, **out())

    if strict and len(distinct_all) > 1:
        return _unresolved(
            "R4-strict-unresolved",
            "strict=True and the sources disagree about the depth reference: "
            + "; ".join(f"{st.source_key} says {st.raw!r}" for st in resolving)
            + ". The house precedence would have chosen "
            + f"{winners[0].raw!r}, but strict mode declines to apply it",
            ("agreement between the sources, or strict=False to accept the "
             "declared house precedence",),
            order, **out())

    winner = winners[0]

    # A rank-4 claim cannot resolve, but it can still contradict, and dropping a
    # contradiction on the floor is how a header consumer stays confident and
    # wrong. It is recorded, non-blocking, and named as corroboration-grade.
    for st in claims:
        if st in resolving or st.reference == winner.reference:
            continue
        disagreements.append(Disagreement(
            kind="free_text_disagreement",
            detail=(f"a note on the log face reads {st.raw!r}, naming a different "
                    f"reference than the {PRECEDENCE[winner.source_key].label} "
                    f"({winner.raw!r}). Free text corroborates a stated value and "
                    "never establishes one, so it did not change the answer -- but "
                    "the header and its own notes do not agree"),
            values={"free_text": st.raw, winner.source_key: winner.raw}))
        flags.append("a note on the log face names a different depth reference "
                     "than the header does; the header was used")

    rule = "R1-agreement" if len(distinct_all) == 1 else "R2-precedence"
    if rule == "R2-precedence":
        flags.append(
            "the depth reference was chosen by HOUSE PRECEDENCE, not by the "
            "sources agreeing: " + policy_statement(order))

    reference = winner.reference
    if reference is None:
        return _unresolved(
            "R10-unsourced-reference-needs-its-own-elevation",
            f"the depth reference is stated as {winner.raw!r}, which is not one of "
            "the references the corpus names (kelly bushing, drill floor, ground "
            "level, top of kelly bushing) and is not one of the unsourced "
            "references this tool carries",
            ("a depth reference this tool recognises, or an explicit elevation "
             "above sea level for the reference named",),
            order, **out())

    # --- R9: TKB is a distinct reference, not a spelling of KB ---------------
    if reference == "KB" and "TKB" in elevations and "KB" in elevations:
        if abs(elevations["TKB"].value - elevations["KB"].value) > _EPS:
            unqualified = not re.search(r"top", winner.raw, re.I)
            if unqualified:
                return _unresolved(
                    "R9-tkb-is-not-kb",
                    f"the header states the depths are measured from {winner.raw!r} "
                    f"and prints both a kelly bushing elevation "
                    f"({elevations['KB'].value:g} ft) and a top-of-kelly-bushing "
                    f"elevation ({elevations['TKB'].value:g} ft), "
                    f"{abs(elevations['TKB'].value - elevations['KB'].value):g} ft "
                    "apart. asquith#10 lists K.B. and T.K.B. as separate elevations, "
                    "so an unqualified 'kelly bushing' does not say which, and "
                    "guessing puts that difference into every depth in the well",
                    ("a depth reference qualified as 'K.B.' or 'T.K.B.'",),
                    order, **out())

    ref_meta = REFERENCES[reference]

    # --- the elevation: R7 stated over derived, R8 no derivation through a
    #     disagreement, R10 unsourced references never derive ----------------
    elevation = elevations.get(reference)
    derived_flag: str | None = None
    if elevation is None:
        if ref_meta.status == "UNSOURCED":
            return _unresolved(
                "R10-unsourced-reference-needs-its-own-elevation",
                f"the depths are measured from the {ref_meta.name}, which the corpus "
                "does not name, and no elevation above sea level is stated for it. "
                "No offset from a reference the corpus does name is published, so "
                "it cannot be derived",
                (f"an explicit elevation above sea level for the {ref_meta.name}",),
                order, **out())
        base = elevations.get(permanent_datum or "") or elevations.get("GL")
        base_key = permanent_datum if elevations.get(permanent_datum or "") else "GL"
        if reference in ("KB", "TKB", "DF") and base is not None and kb_height is not None:
            if isinstance(kb_height, Range):
                return _unresolved(
                    "R8-no-derivation-through-a-disagreement",
                    f"no elevation is stated for the {ref_meta.name}, and the only "
                    f"route to one runs through the height above the permanent "
                    f"datum, which the evidence states at {kb_height.low:g} ft and "
                    f"{kb_height.high:g} ft. Those are not averaged and neither is "
                    "chosen, so the elevation is unresolved -- "
                    f"{kb_height.spread:g} ft of error on every depth in the well",
                    (f"an explicit {reference} elevation above sea level, or "
                     "agreement between the stated and derived heights",),
                    order, **out())
            value = base.value + kb_height.value
            derived_flag = (
                f"{reference} elevation was DERIVED as {base_key} elevation "
                f"{base.value:g} ft + height {kb_height.value:g} ft = {value:g} ft; "
                "no elevation was stated for it (R7)")
            flags.append(derived_flag)
            elevation = Quantity(
                value, "ft",
                f"elevation above sea level of the {ref_meta.name}, DERIVED as "
                f"{base_key} elevation + stated height above the permanent datum",
                ref_meta.source or ASQUITH_HEADING,
                inputs={f"{base_key}_elevation_ft": base.value,
                        "height_ft": kb_height.value, "reference": reference},
                assumptions={"sign": "positive above sea level (tearpock#24)",
                             "derivation": "R7-stated-over-derived: used only "
                                           "because nothing was stated"},
                flags=("derived, not stated",))
            elevations = dict(elevations)
            elevations[reference] = elevation
            carry["references"] = elevations
        else:
            return _unresolved(
                "R7-stated-over-derived",
                f"the depths are measured from the {ref_meta.name}, but no elevation "
                "above sea level is stated for it and none can be derived from what "
                "is. subsea_convert needs the number, not the name",
                (f"an elevation above sea level for the {ref_meta.name}",
                 "or a permanent-datum elevation plus the height above it",),
                order, **out())

    if blocked_by_tolerance:
        return _unresolved(
            "R11-elevation-disagreement-tolerance",
            "two sources state elevations for the same reference that differ by "
            f"more than the caller's {max_elevation_disagreement_ft:g} ft "
            "allowance: "
            + "; ".join(d.detail for d in disagreements
                        if d.kind == "elevation_disagreement" and d.blocking),
            ("agreement between the sources on the elevation, or a wider "
             "max_elevation_disagreement_ft, set knowingly",),
            order, **out())

    # --- the permanent-datum offset: the 15 ft on rrc#16 ---------------------
    # It is computed whenever both elevations are in hand, INCLUDING when the
    # permanent datum and the depth reference are the same point -- that case is
    # a stated offset of 0.0 ft, not an unknown one. Leaving it None there would
    # make None mean two different things ("they coincide" and "the offset is not
    # computable"), and a consumer cannot tell those apart. None now means
    # exactly one thing: no offset could be computed.
    pd_offset: Quantity | None = None
    if permanent_datum and permanent_datum in elevations:
        delta = elevation.value - elevations[permanent_datum].value
        pd_offset = Quantity(
            delta, "ft",
            f"offset of the depth reference ({reference}) above the permanent "
            f"datum ({permanent_datum}): {reference} elevation - "
            f"{permanent_datum} elevation",
            ASQUITH_HEADING,
            inputs={f"{reference}_elevation_ft": elevation.value,
                    f"{permanent_datum}_elevation_ft":
                        elevations[permanent_datum].value},
            assumptions={"sign": "positive when the depth reference is above the "
                                 "permanent datum"})
        if permanent_datum != reference:
            flags.append(
                f"the permanent datum is the {REFERENCES[permanent_datum].name} but "
                f"the depths are hung on the {ref_meta.name}, {delta:+.2f} ft away; "
                "any quantity quoted against the permanent datum must be corrected "
                "by that before it is compared with these depths")

    return DatumResolution(
        resolved=True,
        rule=rule,
        rule_status=RULES[rule].status,
        policy=policy_statement(order),
        precedence_used=order,
        reference=reference,
        reference_name=ref_meta.name,
        elevation=elevation,
        winning_source=winner.source_key,
        permanent_datum_offset=pd_offset,
        source=ref_meta.source or ASQUITH_HEADING,
        **out(references=elevations))

# ---------------------------------------------------------------------------
# 17_md_to_tvd
# Tool #17 `md_to_tvd` — measured depth to true vertical depth, minimum curvature.
# ---------------------------------------------------------------------------

MINCURV = "17-directional-survey/drillingformulas-minimum-curvature-method"

#: Attitude bounds. Not thresholds chosen by this build — the definitional range
#: of the quantities. Inclination is measured from vertical (0 = up-hole
#: vertical, 90 = horizontal, >90 = climbing); azimuth is a compass bearing.
INCLINATION_RANGE_DEG = (0.0, 180.0)
AZIMUTH_RANGE_DEG = (0.0, 360.0)


# --------------------------------------------------------------------------- #
# The published equations
# --------------------------------------------------------------------------- #

def dogleg_angle(inc1: float, inc2: float, azi1: float, azi2: float) -> float:
    """beta = acos[cos(I2-I1) - sin(I1)sin(I2)(1 - cos(A2-A1))], returned in RADIANS.

    The source states "ss must be in radians" for the ratio factor, so this
    returns radians and never degrees; converting at the boundary is where the
    published implementations go wrong.

    NOT the thesis form `cos I1 cos I2 + sin I1 sin I2 (cos A2 - cos A1)`, which
    returns 31.79 deg where this returns the published 12.95 deg.
    """
    i1, i2 = math.radians(inc1), math.radians(inc2)
    a1, a2 = math.radians(azi1), math.radians(azi2)
    cos_beta = math.cos(i2 - i1) - math.sin(i1) * math.sin(i2) * (1 - math.cos(a2 - a1))
    return math.acos(max(-1.0, min(1.0, cos_beta)))


def ratio_factor(beta_rad: float) -> float:
    """RF = (2/beta) tan(beta/2), beta in radians. Limit RF -> 1 as beta -> 0.

    Undefined at beta = pi (tan(pi/2)); callers reach that only through an
    attitude reversal between stations, which `md_to_tvd` refuses before getting
    here.
    """
    if beta_rad < 0:
        raise ValueError("beta must be non-negative; it is an acos result in [0, pi]")
    if beta_rad == 0:
        return 1.0
    if beta_rad >= math.pi:
        raise ValueError("ratio factor is singular at beta = pi (attitude reversal)")
    return (2.0 / beta_rad) * math.tan(beta_rad / 2.0)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def _attitude_refusal(inc: float, azi: float, where: str) -> Refusal | None:
    """Refuse anything that is not an inclination / azimuth. None if clean."""
    lo, hi = INCLINATION_RANGE_DEG
    if not (lo <= inc <= hi) or math.isnan(inc):
        return Refusal(
            reason=(f"inclination {inc} deg at {where} is outside {lo:g}-{hi:g} deg; "
                    "that is not an inclination and minimum curvature cannot be applied to it"),
            needed=("an inclination measured from vertical, 0-180 deg",),
            source=MINCURV,
        )
    lo, hi = AZIMUTH_RANGE_DEG
    if not (lo <= azi <= hi) or math.isnan(azi):
        return Refusal(
            reason=(f"azimuth {azi} deg at {where} is outside {lo:g}-{hi:g} deg; "
                    "a survey written on a -180/+180 convention must be normalised by the "
                    "caller, visibly, not silently here"),
            needed=("an azimuth as a compass bearing, 0-360 deg",),
            source=MINCURV,
        )
    return None


def validate_survey(stations: list[dict], *,
                    require_surface_start: bool = True) -> Refusal | None:
    """Refuse a station list that cannot support minimum curvature. None if clean.

    Checks, in the order a corrupt survey file usually fails them: enough
    stations, starts at surface, monotonic increasing MD (no duplicates), and
    every attitude inside its definitional range.

    `require_surface_start` is switched off by the callers that have a stated
    tie-back TVD at the first station, which resolves the unsurveyed lead-in as
    well as a surface start does.
    """
    if not isinstance(stations, list):
        raise TypeError("stations must be a list of {'md','inc','azi'} dicts")
    if len(stations) < 2:
        return Refusal(
            reason=(f"survey has {len(stations)} station(s); minimum curvature integrates "
                    "over intervals and one station defines no interval"),
            needed=("at least two survey stations, each with md, inc and azi",),
            source=MINCURV,
        )
    for n, s in enumerate(stations):
        missing = [k for k in ("md", "inc", "azi") if k not in s]
        if missing:
            return Refusal(
                reason=f"station {n} is missing {', '.join(missing)}",
                needed=("md, inc and azi on every station",),
                source=MINCURV,
            )
    if require_surface_start and stations[0]["md"] > 0:
        return Refusal(
            reason=(f"survey starts at {stations[0]['md']:g} ft MD, not at surface, and no TVD "
                    "was given for that first station; the unsurveyed lead-in has unknown "
                    "geometry, so TVD from surface is not determined by this survey"),
            needed=("a survey station at 0 ft MD",
                    "or surface_tvd = the known TVD of the first station",
                    "or assume_vertical_to_first_station=True to declare the lead-in vertical"),
            source=MINCURV,
        )
    for n, s in enumerate(stations):
        if not math.isfinite(float(s["md"])):
            return Refusal(
                reason=(f"station {n} has measured depth {s['md']}, which is not a depth; "
                        "a non-finite MD propagates silently into TVD and every structural "
                        "tool gated on it"),
                needed=("a finite measured depth on every station",),
                source=MINCURV,
            )
    for n, (s1, s2) in enumerate(zip(stations, stations[1:])):
        if s2["md"] == s1["md"]:
            return Refusal(
                reason=(f"stations {n} and {n + 1} share MD {s1['md']:g} ft; a zero-length "
                        "interval has no defined attitude change and usually means the "
                        "survey was merged or duplicated"),
                needed=("a survey with strictly increasing measured depth",),
                source=MINCURV,
            )
        if s2["md"] < s1["md"]:
            return Refusal(
                reason=(f"stations are out of depth order: {s1['md']:g} ft then "
                        f"{s2['md']:g} ft at index {n + 1}; minimum curvature integrates "
                        "downward and reordering silently would hide a corrupt survey"),
                needed=("a survey sorted by increasing measured depth",),
                source=MINCURV,
            )
    for n, s in enumerate(stations):
        bad = _attitude_refusal(s["inc"], s["azi"], f"station {n} ({s['md']:g} ft MD)")
        if bad is not None:
            return bad
    return None


# --------------------------------------------------------------------------- #
# One interval
# --------------------------------------------------------------------------- #

def md_to_tvd(md1: float, md2: float, inc1: float, inc2: float,
              azi1: float, azi2: float) -> Quantity | Refusal:
    """TVD increment over one survey interval by minimum curvature.

    dTVD = (dMD/2)(cos I1 + cos I2) x RF

    Published oracle: 3500 -> 3600 ft, 15 -> 25 deg, 20 -> 45 deg gives
    beta = 0.226049 rad (12.95 deg), RF = 1.004280, dTVD = 94.012343 ft.

    Raises ValueError if md2 <= md1 (programmer error: the caller built this
    interval). Refuses on attitudes that are not attitudes, and on a dogleg of
    pi where the ratio factor is singular.
    """
    if not (math.isfinite(md1) and math.isfinite(md2)):
        raise ValueError("md1 and md2 must be finite depths")
    if md2 <= md1:
        raise ValueError("md2 must be deeper than md1")
    bad = _attitude_refusal(inc1, azi1, f"upper station ({md1:g} ft MD)")
    if bad is None:
        bad = _attitude_refusal(inc2, azi2, f"lower station ({md2:g} ft MD)")
    if bad is not None:
        return bad

    dmd = md2 - md1
    beta = dogleg_angle(inc1, inc2, azi1, azi2)
    if beta >= math.pi:
        return Refusal(
            reason=(f"dogleg angle over {md1:g}-{md2:g} ft MD is {math.degrees(beta):.2f} deg, "
                    "a complete attitude reversal; RF = (2/beta)tan(beta/2) is singular there "
                    "and no well path turns back on itself between two stations"),
            needed=("a survey whose consecutive stations describe a continuous path",),
            source=MINCURV,
        )
    rf = ratio_factor(beta)
    dtvd = (dmd / 2.0) * (math.cos(math.radians(inc1)) + math.cos(math.radians(inc2))) * rf

    flags: tuple[str, ...] = ()
    if dtvd > dmd + 1e-9:
        flags += ("tvd_exceeds_md",)
    if beta == 0.0:
        flags += ("straight_interval",)

    return Quantity(dtvd, "ft", "minimum curvature", MINCURV,
                    inputs={"dMD": dmd, "md1": md1, "md2": md2,
                            "I1": inc1, "I2": inc2, "A1": azi1, "A2": azi2,
                            "beta_rad": beta, "beta_deg": math.degrees(beta),
                            "RF": rf},
                    assumptions={"beta_units": "radians",
                                 "path_model": "circular arc between stations"},
                    flags=flags)


# --------------------------------------------------------------------------- #
# Interpolation inside an interval
# --------------------------------------------------------------------------- #

def _tangent(inc_deg: float, azi_deg: float) -> tuple[float, float, float]:
    """Unit tangent of the well path: (north, east, down)."""
    i, a = math.radians(inc_deg), math.radians(azi_deg)
    return (math.sin(i) * math.cos(a), math.sin(i) * math.sin(a), math.cos(i))


def _slerp_attitude(inc1: float, inc2: float, azi1: float, azi2: float,
                    beta_rad: float, fraction: float) -> tuple[float, float]:
    """Attitude a fraction of the way along the circular arc between two stations.

    DERIVED from the source's stated circular-arc model, not printed on the
    page: the unit tangent rotates uniformly along the great circle joining the
    two station tangents, so

        t(f) = [sin((1-f)beta) t1 + sin(f beta) t2] / sin(beta)

    Returns (inclination_deg, azimuth_deg). Validated by additivity: splitting
    the published example at f = 0.5 reproduces its 94.012343 ft to 1e-14.
    """
    if beta_rad == 0.0 or math.sin(beta_rad) == 0.0:
        return inc1, azi1
    t1 = _tangent(inc1, azi1)
    t2 = _tangent(inc2, azi2)
    s = math.sin(beta_rad)
    w1 = math.sin((1.0 - fraction) * beta_rad) / s
    w2 = math.sin(fraction * beta_rad) / s
    v = tuple(w1 * x + w2 * y for x, y in zip(t1, t2))
    inc = math.degrees(math.acos(max(-1.0, min(1.0, v[2]))))
    if abs(v[0]) < 1e-15 and abs(v[1]) < 1e-15:      # vertical: azimuth undefined
        azi = azi1
    else:
        azi = math.degrees(math.atan2(v[1], v[0])) % 360.0
    return inc, azi


def station_at_md(md: float, stations: list[dict]) -> dict | Refusal:
    """The survey attitude at an arbitrary MD, by arc interpolation.

    Returns `{"md", "inc", "azi", "interpolated": bool, "interval": (md1, md2)}`.
    Refuses rather than extrapolating past either end of the survey.
    """
    bad = validate_survey(stations, require_surface_start=False)
    if bad is not None:
        return bad
    if md < stations[0]["md"]:
        return Refusal(
            reason=(f"{md:g} ft MD is above the shallowest survey station "
                    f"({stations[0]['md']:g} ft MD)"),
            needed=("a survey station at or above the requested depth",),
            source=MINCURV,
        )
    if md > stations[-1]["md"]:
        return Refusal(
            reason=(f"{md:g} ft MD is below the deepest survey station "
                    f"({stations[-1]['md']:g} ft MD); extrapolating past the last station "
                    "invents geometry"),
            needed=(f"survey coverage to at least {md:g} ft MD",),
            source=MINCURV,
        )
    for s1, s2 in zip(stations, stations[1:]):
        if s1["md"] <= md <= s2["md"]:
            if md == s1["md"]:
                return {"md": md, "inc": s1["inc"], "azi": s1["azi"],
                        "interpolated": False, "interval": (s1["md"], s2["md"])}
            if md == s2["md"]:
                return {"md": md, "inc": s2["inc"], "azi": s2["azi"],
                        "interpolated": False, "interval": (s1["md"], s2["md"])}
            beta = dogleg_angle(s1["inc"], s2["inc"], s1["azi"], s2["azi"])
            f = (md - s1["md"]) / (s2["md"] - s1["md"])
            inc, azi = _slerp_attitude(s1["inc"], s2["inc"], s1["azi"], s2["azi"], beta, f)
            return {"md": md, "inc": inc, "azi": azi,
                    "interpolated": True, "interval": (s1["md"], s2["md"])}
    # unreachable given the bracket checks above
    raise ValueError(f"{md} ft MD could not be bracketed in the survey")


# --------------------------------------------------------------------------- #
# Whole survey
# --------------------------------------------------------------------------- #

def _walk(stations: list[dict], surface_tvd: float) -> tuple[float, dict] | Refusal:
    """Cumulative TVD over every interval, plus the survey's provenance summary."""
    tvd = surface_tvd
    max_beta = 0.0
    max_dls = 0.0
    for s1, s2 in zip(stations, stations[1:]):
        step = md_to_tvd(s1["md"], s2["md"], s1["inc"], s2["inc"], s1["azi"], s2["azi"])
        if isinstance(step, Refusal):
            return step
        tvd += step.value
        beta_deg = step.inputs["beta_deg"]
        max_beta = max(max_beta, beta_deg)
        max_dls = max(max_dls, beta_deg * 100.0 / step.inputs["dMD"])
    summary = {
        "stations": len(stations),
        "survey_top_md": stations[0]["md"],
        "survey_td_md": stations[-1]["md"],
        "intervals_used": len(stations) - 1,
        "max_dogleg_deg": max_beta,
        "max_dogleg_deg_per_100ft": max_dls,
    }
    return tvd, summary


def _vertical_lead_in(stations: list[dict]) -> list[dict]:
    """Prepend a surface station straight above the first, declaring it vertical."""
    first = stations[0]
    return [{"md": 0.0, "inc": 0.0, "azi": first["azi"]}] + list(stations)


def md_to_tvd_survey(stations: list[dict], surface_tvd: float | None = None, *,
                     depth_reference: str | None = None,
                     assume_vertical_to_first_station: bool = False
                     ) -> Quantity | Refusal:
    """Cumulative TVD at the deepest station of a survey. Stations: md, inc, azi.

    `surface_tvd` is the known TVD of the FIRST station — the tie-back. A survey
    that starts at 0 ft MD needs none (it defaults to 0). A survey that starts
    below surface needs one, because the unsurveyed lead-in is otherwise unknown
    geometry; supplying it is one of the two ways past that refusal, the other
    being `assume_vertical_to_first_station=True`.

    `depth_reference` names what MD is hung on ("KB", "GL", "DF") and is
    recorded, not resolved — that is `datum_resolve` / `datum_reconcile`.
    """
    flags: tuple[str, ...] = ()
    tie_back_stated = surface_tvd is not None
    bad = validate_survey(
        stations,
        require_surface_start=not (tie_back_stated or assume_vertical_to_first_station))
    if bad is not None:
        return bad

    used = list(stations)
    if not tie_back_stated and assume_vertical_to_first_station and used[0]["md"] > 0:
        used = _vertical_lead_in(used)
        flags += ("assumed_vertical_to_first_station",)
        bad = validate_survey(used)
        if bad is not None:
            return bad
    surface_tvd = 0.0 if surface_tvd is None else float(surface_tvd)
    if tie_back_stated and used[0]["md"] > 0:
        flags += ("tied_back_to_stated_tvd",)

    walked = _walk(used, surface_tvd)
    if isinstance(walked, Refusal):
        return walked
    tvd, summary = walked

    if all(s["inc"] == 0.0 for s in used):
        flags += ("survey_vertical_throughout",)
    if depth_reference is None:
        flags += ("depth_reference_unstated",)
    if (tvd - surface_tvd) > (used[-1]["md"] - used[0]["md"]) + 1e-9:
        flags += ("tvd_exceeds_md",)

    return Quantity(tvd, "ft", "minimum curvature, cumulative", MINCURV,
                    inputs={**summary, "td_md": used[-1]["md"]},
                    assumptions={"surface_tvd": surface_tvd,
                                 "beta_units": "radians",
                                 "depth_reference": depth_reference,
                                 "path_model": "circular arc between stations"},
                    flags=flags)


# --------------------------------------------------------------------------- #
# The vertical fallback and the caller-facing entry point
# --------------------------------------------------------------------------- #

def md_to_tvd_vertical(md: float, surface_tvd: float | None = 0.0, *,
                       depth_reference: str | None = None,
                       reason: str = "no directional survey supplied") -> Quantity:
    """TVD = MD for an unsurveyed hole, flagged as an assumption rather than a survey.

    The catalog specifies this fallback ("falls back to identity for vertical
    holes with an explicit flag") because most holes in this basin are vertical
    with no survey on file. It is never silent: `assumed_vertical` rides on every
    result so a downstream structural tool can say so in its own answer.
    """
    if not math.isfinite(md):
        raise ValueError("md must be a finite depth")
    if md < 0:
        raise ValueError("md must be non-negative")
    surface_tvd = 0.0 if surface_tvd is None else float(surface_tvd)
    return Quantity(surface_tvd + md, "ft", "vertical-hole identity (TVD = MD), assumed", MINCURV,
                    inputs={"md": md, "stations": 0},
                    assumptions={"hole": "vertical",
                                 "why": reason,
                                 "surface_tvd": surface_tvd,
                                 "depth_reference": depth_reference},
                    flags=("assumed_vertical",)
                          + (("depth_reference_unstated",) if depth_reference is None else ()))


def tvd_at_md(md: float, stations: list[dict] | None = None, surface_tvd: float | None = None, *,
              assume_vertical: bool = False,
              depth_reference: str | None = None,
              assume_vertical_to_first_station: bool = False) -> Quantity | Refusal:
    """TVD at one arbitrary measured depth — the question a caller actually asks.

    With a survey: walks every complete interval above `md`, then applies
    minimum curvature over the partial interval using the arc-interpolated
    attitude at `md` (see `_slerp_attitude`). Never linear-in-MD, never
    extrapolated past the deepest station.

    Without a survey: refuses, unless the caller declares the hole vertical with
    `assume_vertical=True`, which returns the flagged identity.

    `surface_tvd` is the tie-back TVD at the first station, as in
    `md_to_tvd_survey`.
    """
    if not math.isfinite(md):
        raise ValueError("md must be a finite depth")
    if md < 0:
        raise ValueError("md must be non-negative")

    if not stations:
        if assume_vertical:
            return md_to_tvd_vertical(md, surface_tvd, depth_reference=depth_reference,
                                      reason="no directional survey supplied; caller declared "
                                             "the hole vertical")
        return Refusal(
            reason=(f"no directional survey supplied, so TVD at {md:g} ft MD is not determined; "
                    "TVD = MD holds only for a vertical hole and that is an assumption the "
                    "caller has to own"),
            needed=("a directional survey (md, inc, azi per station)",
                    "or assume_vertical=True to accept the vertical-hole identity"),
            source=MINCURV,
        )

    tie_back_stated = surface_tvd is not None
    bad = validate_survey(
        stations,
        require_surface_start=not (tie_back_stated or assume_vertical_to_first_station))
    if bad is not None:
        return bad

    flags: tuple[str, ...] = ()
    used = list(stations)
    if not tie_back_stated and assume_vertical_to_first_station and used[0]["md"] > 0:
        used = _vertical_lead_in(used)
        flags += ("assumed_vertical_to_first_station",)
        bad = validate_survey(used)
        if bad is not None:
            return bad
    surface_tvd = 0.0 if surface_tvd is None else float(surface_tvd)
    if tie_back_stated and used[0]["md"] > 0:
        flags += ("tied_back_to_stated_tvd",)

    at = station_at_md(md, used)
    if isinstance(at, Refusal):
        return at

    # Every complete interval above md, then the partial one.
    complete = [s for s in used if s["md"] <= md]
    if len(complete) >= 2:
        walked = _walk(complete, surface_tvd)
        if isinstance(walked, Refusal):
            return walked
        tvd, summary = walked
    else:
        tvd, summary = surface_tvd, {
            "stations": len(used), "survey_top_md": used[0]["md"],
            "survey_td_md": used[-1]["md"], "intervals_used": 0,
            "max_dogleg_deg": 0.0, "max_dogleg_deg_per_100ft": 0.0,
        }

    partial: dict[str, float] | None = None
    if at["interpolated"]:
        top = complete[-1]
        step = md_to_tvd(top["md"], md, top["inc"], at["inc"], top["azi"], at["azi"])
        if isinstance(step, Refusal):
            return step
        tvd += step.value
        flags += ("interpolated_within_interval",)
        partial = {"from_md": top["md"], "to_md": md,
                   "interval": list(at["interval"]),
                   "interpolated_inc_deg": at["inc"],
                   "interpolated_azi_deg": at["azi"],
                   "dTVD": step.value}
        summary = dict(summary)
        summary["intervals_used"] = summary["intervals_used"] + 1
        summary["max_dogleg_deg"] = max(summary["max_dogleg_deg"], step.inputs["beta_deg"])
        summary["max_dogleg_deg_per_100ft"] = max(
            summary["max_dogleg_deg_per_100ft"],
            step.inputs["beta_deg"] * 100.0 / step.inputs["dMD"])

    if all(s["inc"] == 0.0 for s in used):
        flags += ("survey_vertical_throughout",)
    if depth_reference is None:
        flags += ("depth_reference_unstated",)
    if (tvd - surface_tvd) > (md - used[0]["md"]) + 1e-9:
        flags += ("tvd_exceeds_md",)

    assumptions: dict = {"surface_tvd": surface_tvd,
                         "beta_units": "radians",
                         "depth_reference": depth_reference,
                         "path_model": "circular arc between stations"}
    if partial is not None:
        assumptions["interpolation"] = (
            "minimum curvature over the partial interval, attitude by spherical linear "
            "interpolation of the station tangents (DERIVED from the source's circular-arc "
            "model; not printed on the page). NOT linear-in-MD interpolation of TVD.")

    return Quantity(tvd, "ft", "minimum curvature to requested MD", MINCURV,
                    inputs={**summary, "md": md,
                            **({"partial_interval": partial} if partial else {})},
                    assumptions=assumptions,
                    flags=flags)

# ---------------------------------------------------------------------------
# 18_subsea_convert
# subsea_convert (#18) — TVD to subsea elevation, the structural gate.
# ---------------------------------------------------------------------------

ASQUITH_LOG_HEADING = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#10"

#: The four depth references a log heading may declare.
#: `asquith#10`, Fig. 1.2 item 5: "K.B. = kelly bushing elevation, D.F. = drill
#: floor elevation, G.L. = ground level elevation, T.K.B. = top of kelly
#: bushing". Four, not three. TKB is deliberately NOT an alias of KB.

# The four references `asquith#10` Fig. 1.2 item 5 names. Derived from #15's
# sourced table rather than restated, so the two cannot drift apart; RT and CH
# are deliberately absent - they are on real headers and in no corpus source,
# and this tool must refuse them rather than alias RT to DF.
KNOWN_REFERENCES: tuple[str, ...] = ("KB", "GL", "DF", "TKB")

#: Keys searched, in order, for "which reference are the depths hung on".
#: Open question 1 in the spec: `datum_resolve` (#15) was still being written, so
#: this is a tolerant search rather than one documented field name. Narrow it
#: once #15 lands.
_REFERENCE_KEYS: tuple[str, ...] = (
    "depth_reference", "measured_from", "log_measured_from",
    "depths_measured_from", "reference",
)

#: Keys searched, in order, for a per-reference elevation table.
_TABLE_KEYS: tuple[str, ...] = ("elevations", "elevations_ft", "references", "datums")

#: Keys searched, in order, for a single scalar elevation on a mapping.
_SCALAR_ELEVATION_KEYS: tuple[str, ...] = ("elevation_ft", "elevation", "value")

_SIGN_CONVENTION = "negative below sea level"
_EQUATION = "SSTVD = TVD - KB"
_METHOD = ("SSTVD = TVD - E(reference), reported negative below sea level "
           "(Tearpock p. 61)")

#: The route out of the deviated-well refusal. Named here rather than inline so
#: it reads identically wherever it is rendered.
_DEVIATED_ROUTE: tuple[str, ...] = (
    "a directional survey (MD, inclination, azimuth) for this well",
    "md_to_tvd (#17) by minimum curvature to get TVD at the pick",
    "then subsea_convert again with that TVD and deviated=False",
)




def _search(containers: tuple[Any, ...], keys: tuple[str, ...]) -> Any:
    """First present, non-None value for any of `keys` across `containers`."""
    for key in keys:
        for container in containers:
            if isinstance(container, Mapping) and container.get(key) is not None:
                return container[key]
    return None


def _as_float_18(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _elevation_number(value: Any) -> tuple[float | None, str | None]:
    """(elevation_ft, offending_unit).

    An elevation may arrive as a bare float or as a `Quantity` — `datum_resolve`
    (#15) emits `references: dict[str, Quantity]`, so the Quantity case is the
    normal one, not an exotic one. A Quantity that declares a unit which is not
    feet is NOT converted here: `unit_convert` (#11) owns conversion and #15
    already declines a non-foot elevation for the same reason
    (`_record_elevation`). It is returned as an offending unit so the caller can
    refuse and say which unit it was.
    """
    if isinstance(value, Quantity):
        if not _unit_is_feet(value):
            return None, _unit_of(value) or "(unstated)"
        return _as_float_18(value.value), None
    if isinstance(value, Range):
        return None, None            # a band is not an elevation; #15 owns R8
    return _as_float_18(value), None


def _elevation_table(containers: tuple[Any, ...]
                     ) -> tuple[dict[str, float], dict[str, str]]:
    """Pull a {reference: elevation_ft} table out of whatever #15 handed us.

    Reads an explicit table under one of `_TABLE_KEYS`, and also picks up bare
    per-reference keys (`{"KB": 2888.0, "GL": 2873.0}`) on a mapping, which is
    the shape a caller transcribing a log heading naturally writes.

    Returns the usable table and, separately, {reference: unit} for elevations
    that were present but stated in something other than feet — dropping those
    silently would turn a unit error into "no elevation available".
    """
    table: dict[str, float] = {}
    wrong_unit: dict[str, str] = {}
    raw = _search(containers, _TABLE_KEYS)
    if isinstance(raw, Mapping):
        for name, elev in raw.items():
            ref = normalize_reference(name)
            val, bad_unit = _elevation_number(elev)
            if ref and val is not None:
                table.setdefault(ref, val)
            elif ref and bad_unit:
                wrong_unit.setdefault(ref, bad_unit)
    for container in containers:
        if not isinstance(container, Mapping):
            continue
        for name, elev in container.items():
            if not isinstance(name, str) or name.strip().upper() not in KNOWN_REFERENCES:
                continue
            val, bad_unit = _elevation_number(elev)
            if val is not None:
                table.setdefault(name.strip().upper(), val)
            elif bad_unit:
                wrong_unit.setdefault(name.strip().upper(), bad_unit)
    return table, wrong_unit


def _refuse_wrong_unit(reference: str, unit: str) -> Refusal:
    """Feet in, feet out. The one place a unit slip is caught."""
    return Refusal(
        reason=(f"the {reference} elevation is stated in {unit!r}, not feet, and this "
                "tool subtracts it from a depth in feet; converting it here would be "
                "arithmetic on a unit the caller never declared"),
        needed=(f"the {reference} elevation in ft above sea level",
                "unit_convert (#11) on the elevation before datum_resolve (#15)"),
        source=ASQUITH_LOG_HEADING)


def _datum_from_resolution(res: Any) -> Any:
    """`datum_resolve`'s (#15) own return type, read as the documented shape.

    Spec open question 1: #18 was written before #15 landed, so `datum=` was
    specified as Quantity / Refusal / Mapping. #15 ships a `DatumResolution`,
    and `subsea_convert(datum=datum_resolve(...))` — the one call this tool
    exists for — raised TypeError. Unresolved propagates as #15's own Refusal;
    resolved is flattened into the mapping shape this tool already reads, so the
    reference gate, the per-reference table and the permanent-datum flag all
    keep working off #15's evidence rather than a re-derivation.
    """
    if not getattr(res, "resolved", False):
        return getattr(res, "refusal", None) or Refusal(
            reason="datum_resolve reported the datum unresolved",
            needed=("a resolved depth reference and its elevation above sea level",),
            source=getattr(res, "source", ASQUITH_LOG_HEADING))
    out: dict[str, Any] = {"depth_reference": res.reference,
                           "elevations": dict(res.references or {}),
                           "permanent_datum": res.permanent_datum}
    if res.elevation is not None and res.reference:
        out["elevations"].setdefault(res.reference, res.elevation)
    return out


def _refuse(reason: str, needed: tuple[str, ...], source: str = TEARPOCK_DATUM) -> Refusal:
    return Refusal(reason=reason, needed=needed, source=source)


def subsea_convert(tvd: float,
                   kb: float | None = None,
                   datum_resolved: bool | None = None,
                   reference: str = "KB",
                   deviated: bool = False,
                   *,
                   datum: Any = None,
                   depth_reference: str | None = None,
                   deviation_deg: float | None = None):
    """SSTVD from TVD, against the reference the depths are actually hung on.

    `SSTVD = E(R) - TVD`, i.e. Tearpock's `SSTVD = TVD - KB` (p. 61,
    `tearpock#24`, vertical wells only) generalised from KB to any of the four
    references a log heading may declare, and reported in the map convention:
    **negative below sea level**, positive above it. See the module docstring.

    Preferred call passes `datum=` — the `datum_resolve` (#15) result — from
    which the reference and that reference's elevation are read together. The
    legacy `(tvd, kb, datum_resolved, reference)` form still works and is
    flagged.

    Returns a Quantity, or a Refusal when the datum is unresolved, when the
    reference the depths are hung on is unknown, when the elevation held belongs
    to a different reference than the depths are hung on, or when the hole is
    deviated. Raises TypeError/ValueError only for programmer error.
    """
    # --- programmer error, not refusals ------------------------------------
    if datum is not None and datum_resolved is not None:
        raise ValueError(
            "pass datum= (the datum_resolve result) or the legacy datum_resolved= "
            "flag, not both")
    if isinstance(datum, DatumResolution):
        datum = _datum_from_resolution(datum)
    if datum is not None and not isinstance(datum, (Refusal, Quantity, Mapping)):
        raise TypeError(
            "datum must be the datum_resolve (#15) result — a Quantity or a "
            f"Refusal — or a mapping of heading fields; got {type(datum).__name__}")

    tvd_val = _as_float_18(tvd)
    if tvd_val is None:
        return _refuse(
            reason=f"tvd is not a finite depth ({tvd!r}); no subsea elevation can be produced",
            needed=("a finite true vertical depth in ft below the depth reference",),
        )

    # --- gate 1: is the datum resolved at all? -----------------------------
    if isinstance(datum, Refusal):
        return _refuse(
            reason=("datum unresolved upstream, so structural depth cannot be produced; "
                    f"datum_resolve refused: {datum.reason}"),
            needed=tuple(datum.needed) or (
                "an elevation for the reference the depths are hung on",
                "which reference the depths are hung on (the heading's 'Log Measured From')",
            ),
            source=datum.source or TEARPOCK_DATUM,
        )
    if datum is None and not datum_resolved:
        return _refuse(
            reason=("datum unresolved; subsea conversion is the gate everything "
                    "structural depends on"),
            needed=("KB, GL, DF or TKB elevation and which reference the depths are hung on",),
        )

    # --- resolve which reference the depths are hung on ---------------------
    containers: tuple[Any, ...] = ()
    if isinstance(datum, Quantity):
        containers = (datum.inputs, datum.assumptions)
    elif isinstance(datum, Mapping):
        containers = (datum,)

    asserted_ref = normalize_reference(depth_reference)
    if depth_reference is not None and asserted_ref is None:
        return _refuse(
            reason=(f"depth_reference {depth_reference!r} is not one of the four "
                    "references a log heading declares (KB, GL, DF, TKB); it will not "
                    "be guessed"),
            needed=("a depth reference of KB, GL, DF or TKB",),
            source=ASQUITH_LOG_HEADING,
        )

    legacy = datum is None
    if legacy:
        resolved_ref = asserted_ref or normalize_reference(reference)
        if resolved_ref is None:
            return _refuse(
                reason=(f"reference {reference!r} is not one of KB, GL, DF or TKB; the "
                        "reference the depths are hung on will not be guessed"),
                needed=("a depth reference of KB, GL, DF or TKB",),
                source=ASQUITH_LOG_HEADING,
            )
    else:
        datum_ref = normalize_reference(_search(containers, _REFERENCE_KEYS))
        if asserted_ref and datum_ref and asserted_ref != datum_ref:
            return _refuse(
                reason=("caller and datum_resolve disagree on which reference the depths "
                        f"are hung on: caller says {asserted_ref}, datum_resolve says "
                        f"{datum_ref}; converting against either would be a guess"),
                needed=("datum_reconcile (#16) over the two readings of the heading",
                        "or a corrected 'Log Measured From' for this well"),
            )
        resolved_ref = asserted_ref or datum_ref
        if resolved_ref is None:
            return _refuse(
                reason=("the reference the depths are hung on was not resolved; it will "
                        "not be defaulted to KB, because a log measured from KB against "
                        "a GL permanent datum is out by the whole rig-floor height "
                        "(rrc-section-f#16: KB 2888', GL 2873', 15 ft apart)"),
                needed=("datum_resolve (#15) on the heading's 'Log Measured From' line "
                        "or the LAS ~W section",
                        "or an explicit depth_reference of KB, GL, DF or TKB"),
                source=ASQUITH_LOG_HEADING,
            )

    # --- resolve the elevation OF THAT REFERENCE ---------------------------
    flags: list[str] = []
    if legacy:
        elevation = _as_float_18(kb)
        if elevation is None:
            return _refuse(
                reason=(f"no finite elevation supplied for {resolved_ref}; an elevation is "
                        "never defaulted"),
                needed=(f"the {resolved_ref} elevation in ft above sea level",),
            )
        elevation_source = f"caller-supplied {resolved_ref} elevation"
        flags.append("legacy-call:reference-and-elevation-asserted-by-caller")
    else:
        table, wrong_unit = _elevation_table(containers)
        if isinstance(datum, Mapping):
            scalar, scalar_bad_unit = _elevation_number(
                _search((datum,), _SCALAR_ELEVATION_KEYS))
        elif not _unit_is_feet(datum):
            # A resolved elevation that declares metres is not a foot elevation
            # and is never silently subtracted from a depth in feet.
            scalar, scalar_bad_unit = None, _unit_of(datum) or "(unstated)"
        else:
            scalar, scalar_bad_unit = _as_float_18(datum.value), None
        # The scalar elevation is only usable when it is the elevation OF the
        # reference the depths are hung on. This is the rrc#16 gate: a resolved
        # "datum elevation" that belongs to the permanent datum (GL) is not the
        # subtrahend for depths measured from KB. The scalar's own reference is
        # whatever datum_resolve labelled it, falling back to the reference it
        # named as the depth reference.
        scalar_ref = normalize_reference(
            _search(containers, ("elevation_reference", "elevation_of", "datum_reference"))
        ) or normalize_reference(_search(containers, _REFERENCE_KEYS))

        if resolved_ref in table:
            elevation = table[resolved_ref]
            elevation_source = f"datum_resolve elevation table[{resolved_ref}]"
        elif scalar is not None and scalar_ref == resolved_ref:
            elevation = scalar
            elevation_source = f"datum_resolve resolved {resolved_ref} elevation"
        elif resolved_ref in wrong_unit:
            return _refuse_wrong_unit(resolved_ref, wrong_unit[resolved_ref])
        elif scalar_bad_unit and (scalar_ref is None or scalar_ref == resolved_ref):
            return _refuse_wrong_unit(resolved_ref, scalar_bad_unit)
        else:
            held = ", ".join(f"{r} {table[r]:g} ft" for r in KNOWN_REFERENCES if r in table)
            return _refuse(
                reason=(f"depths are hung on {resolved_ref} but no {resolved_ref} elevation "
                        f"is available; held instead: {held or 'none'}. One reference's "
                        "elevation is never substituted for another's — rrc-section-f#16 "
                        "is a real heading whose permanent datum is GL while the log is "
                        "measured from KB, 15 ft apart"),
                needed=(f"the {resolved_ref} elevation in ft above sea level",
                        f"or the offset from a known reference to {resolved_ref} "
                        "(datum_resolve #15 / datum_reconcile #16)"),
                source=ASQUITH_LOG_HEADING,
            )

        permanent = normalize_reference(
            _search(containers, ("permanent_datum", "permanent_datum_reference"))
        )
        if permanent and permanent != resolved_ref:
            flags.append("reference-datum-differs-from-permanent-datum")

    # `elevation` is finite by construction: every path above it runs through
    # `_as_float_18`, which rejects non-finite values, and refuses on None.

    # --- gate 2: vertical wells only ---------------------------------------
    dev_angle = _as_float_18(deviation_deg)
    # deviation_deg is additive only: it can declare a hole deviated, never clear
    # a deviated=True the caller passed.
    if deviated or (dev_angle is not None and dev_angle > 0.0):
        stated = (f"; recorded hole angle {dev_angle:g} deg (Tearpock defines a vertical "
                  "wellbore as drilled 90 deg to horizontal, and states no tolerance)"
                  ) if dev_angle is not None and dev_angle > 0.0 else ""
        return _refuse(
            reason=("SSTVD = TVD - KB is stated for vertical wells only (Tearpock p. 61: "
                    "'For vertical wells the SSTVD = TVD - KB'); a deviated well must be "
                    "converted MD -> TVD by directional survey first" + stated),
            needed=_DEVIATED_ROUTE,
        )

    # --- the conversion ----------------------------------------------------
    # Tearpock's equation gives the magnitude below sea level; his maps and
    # worked examples print it negative (-1340 ft at #68, -9738 ft at #23, where
    # "adjusted upward 10 ft" moves -9748 to -9738 and so fixes the direction of
    # the number line, not just the glyph). Deeper is more negative.
    sstvd = elevation - tvd_val

    if sstvd > 0.0:
        flags.append("above-sea-level")

    return Quantity(
        sstvd, "ft SS", _METHOD, TEARPOCK_DATUM,
        inputs={"TVD": tvd_val,
                "elevation_ft": elevation,
                "reference": resolved_ref,
                "elevation_source": elevation_source},
        assumptions={"sign": _SIGN_CONVENTION,
                     "hole": "vertical",
                     "equation": _EQUATION,
                     "reference_generalised_from": "KB",
                     "reference_definitions": ASQUITH_LOG_HEADING},
        flags=tuple(flags),
    )

# ---------------------------------------------------------------------------
# 16_datum_reconcile
# Tool #16 `datum_reconcile` — staging file for merge into `tools/geometry.py`.
# ---------------------------------------------------------------------------

# MERGE NOTE: already present in geometry.py — drop this duplicate.

# The reference names a well's depths may be hung on. Four, not three: Asquith &
# Krygowski 2004 #10, log-heading item 5, "K.B. = kelly bushing elevation,
# D.F. = drill floor elevation, G.L. = ground level elevation, T.K.B. = top of
# kelly bushing". MSL is added for offshore/sea-level-referenced depths, which
# Tearpock #24 defines as the common datum itself.
ASQUITH_REFERENCES = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#10"


# Where an `elevations` mapping in the shape `tools.header.DatumReport` produces
# keeps each reference's elevation. `MSL` is sea level by definition, so 0.0.
_ELEVATION_KEYS_16: dict[str, str] = {
    "KB": "kb_elevation_ft",
    "DF": "df_elevation_ft",
    "GL": "ground_elevation_ft",
}


@dataclass(frozen=True)
class WellDatum:
    """One well's resolved elevation reference — the three fields #16 consumes.

    `elevation_ft` is the elevation of `reference` ABOVE MEAN SEA LEVEL, in feet,
    which is Tearpock's KB: "Vertical distance from kelly bushing to sea level".
    It is NOT a kelly bushing height above ground.
    """

    well: str = ""
    reference: str | None = None
    elevation_ft: float | None = None
    resolved: bool = False
    source: str = ""
    detail: str = ""
    deviated: bool = False
    # Set when an elevation WAS supplied but in a unit that cannot be brought to
    # feet. Distinct from "no elevation": the operator gave one and it was
    # unusable, and the refusal has to say which.
    elevation_problem: str | None = None
    extra: dict[str, Any] = dc_field(default_factory=dict)




def _get_16(obj: Any, key: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)


def _finite_16(value: Any) -> float | None:
    """A finite float out of a float, a numeric string, or a `Quantity`.

    The declared unit is NOT inspected here; see `_elevation_16`, which is what
    every elevation goes through.
    """
    if isinstance(value, Quantity):
        value = value.value
    elif isinstance(value, Refusal):
        return None
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return None
    return as_float if math.isfinite(as_float) else None


def _elevation_16(value: Any, notes: list[str], problems: list[str]) -> float | None:
    """An elevation in FEET, honouring whatever unit the value declares.

    A `Quantity` carries its own unit and this tool's arithmetic is in feet
    throughout, so the unit is read rather than assumed. An elevation stated in
    metres and taken as feet is a 3.28x datum error — the largest possible
    version of the "elevation error that looks like structure" this tool exists
    to prevent — so a non-foot unit is converted through the real `unit_convert`
    (#11) and a unit that #11 cannot convert becomes a refusal, never a number.
    `_ACCEPTED_ELEVATION_UNITS` is the same foot-spelling table `datum_resolve`
    (#15) accepts, and it includes the LAS spelling `F`, which `unit_convert`
    would read as Fahrenheit.
    """
    unit = ""
    if isinstance(value, Quantity):
        unit = str(value.unit or "").strip()
    as_float = _finite_16(value)
    if as_float is None:
        return None
    if not unit or unit.upper() in _ACCEPTED_ELEVATION_UNITS:
        return as_float
    converted = unit_convert(as_float, unit, "ft")
    if isinstance(converted, Refusal):
        problems.append(
            f"the elevation is declared in {unit!r}; this tool's arithmetic is in "
            f"feet and unit_convert (#11) will not convert that unit — "
            f"{converted.reason}")
        return None
    notes.append(f"elevation-unit-converted: {as_float:g} {unit} -> "
                 f"{converted.value:g} ft by unit_convert (#11)")
    return float(converted.value)


def _coerce_datum(supplied: Any,
                  label: str) -> tuple[WellDatum, str | None, tuple[str, ...]]:
    """Adapt a `datum_resolve` result to `WellDatum`.

    Returns `(datum, blocker, needed)`. `blocker` is a human-readable reason the
    datum is unusable, or None; `needed` names what would unblock it and is never
    empty when `blocker` is set. Every field defaults to absent: an unreadable
    shape yields a blocker, never an assumed agreement. Accepts `WellDatum`,
    `tools.header.DatumReport`, a plain mapping, or a `Refusal` from #15.
    """
    if supplied is None or isinstance(supplied, (int, float, str, bool)):
        raise TypeError(
            f"{label}: expected a datum_resolve result (WellDatum, DatumReport, "
            f"mapping or Refusal), got {type(supplied).__name__}")

    if isinstance(supplied, Refusal):
        return (WellDatum(well=label, detail=supplied.reason),
                f"{label}: datum_resolve refused — {supplied.reason}",
                supplied.needed or (
                    f"{label}: a resolved elevation reference and its elevation "
                    f"above mean sea level, in ft",))

    if isinstance(supplied, (WellDatum, Mapping)) or hasattr(supplied, "__dict__") or \
            hasattr(supplied, "__dataclass_fields__"):
        # A WellDatum goes through the same reader as everything else, so that
        # reference-name normalisation and the MSL default can never depend on
        # which shape the caller happened to hand in.
        datum = _from_fields(supplied, label)
    else:
        raise TypeError(
            f"{label}: expected a datum_resolve result, got {type(supplied).__name__}")

    name = datum.well or label
    status = str(_get_16(supplied, "status") or "").strip().lower()
    want_reference = (f"{name}: which reference its depths are hung on "
                      f"(KB, DF, GL, TKB or MSL)")
    want_elevation = (f"{name}: the elevation of that reference above mean sea "
                      f"level, in ft")

    if not datum.resolved:
        if status == "conflict":
            return datum, (
                f"{name}: datum_resolve reports a CONFLICT — the heading names one "
                f"permanent datum and a different log-measured-from, so the well "
                f"itself does not say which reference its depths belong to"
                + (f" ({datum.detail})" if datum.detail else "")
            ), (f"{name}: which of the references named in the heading the depths "
                f"are actually hung on",)
        needed = (want_reference,) if datum.reference is None else ()
        if datum.elevation_ft is None:
            needed += (want_elevation,)
        return datum, (
            f"{name}: datum unresolved"
            + (f" ({status})" if status else "")
            + (f" — {datum.detail}" if datum.detail else "")
            + "; two wells with unknown datums are not assumed to share one"
        ), (needed or (want_reference, want_elevation))

    if datum.reference is None:
        return datum, (
            f"{name}: resolved, but the reference the depths are hung on is not named"
        ), (want_reference,)

    if datum.elevation_ft is None and datum.elevation_problem:
        return datum, (
            f"{name}: hung on {datum.reference}, and an elevation was supplied, but "
            f"{datum.elevation_problem}"
        ), (f"{name}: the elevation of {datum.reference} above mean sea level, in ft "
            f"or in a length unit unit_convert (#11) recognises",)

    if datum.elevation_ft is None:
        return datum, (
            f"{name}: hung on {datum.reference}, but no elevation is available for "
            f"that reference — a named reference without an elevation cannot be put "
            f"on subsea, and two wells both reporting '{datum.reference}' are not "
            f"reconciled by that fact"
        ), (f"{name}: the elevation of {datum.reference} above mean sea level, in ft",)

    if not math.isfinite(datum.elevation_ft):
        return (datum,
                f"{name}: {datum.reference} elevation is not a finite number",
                (want_elevation,))

    return datum, None, ()


def _from_fields(supplied: Any, label: str) -> WellDatum:
    """Read the three consumed fields out of a DatumReport / mapping / object."""
    status = str(_get_16(supplied, "status") or "").strip().lower()
    resolved_flag = _get_16(supplied, "resolved")
    if isinstance(resolved_flag, bool):
        resolved = resolved_flag
    elif status:
        resolved = status == "resolved"      # conflict / unresolved / absent all fail
    else:
        resolved = False                     # fail-safe: absent means unresolved

    raw_reference = _get_16(supplied, "reference")
    if raw_reference is None:
        raw_reference = _get_16(supplied, "log_measured_from")
    if raw_reference is None:
        raw_reference = _get_16(supplied, "datum_reference")
    reference = normalize_reference(raw_reference)

    # `elevation` is #15's DatumResolution field and is a Quantity; `elevation_ft`
    # is the plain-float spelling. Both mean the same thing: the elevation of the
    # winning reference above mean sea level.
    notes: list[str] = []
    problems: list[str] = []
    elevation = _elevation_16(_get_16(supplied, "elevation_ft"), notes, problems)
    if elevation is None:
        elevation = _elevation_16(_get_16(supplied, "elevation"), notes, problems)
    if elevation is None:
        elevation = _elevation_16(_get_16(supplied, "datum_elevation_ft"), notes, problems)
    if elevation is None and reference == "MSL":
        elevation = 0.0                      # sea level is the datum, by definition
    if elevation is None and reference is not None:
        # #15's `references` is keyed by canonical name (KB/TKB/DF/GL) and holds
        # Quantities; header.py's `elevations` is keyed by field name and holds
        # floats. Both are read, neither is required.
        by_reference = _get_16(supplied, "references")
        if isinstance(by_reference, Mapping):
            elevation = _elevation_16(by_reference.get(reference), notes, problems)
        if elevation is None:
            elevations = _get_16(supplied, "elevations")
            if isinstance(elevations, Mapping):
                key = _ELEVATION_KEYS_16.get(reference)
                if key is not None:
                    elevation = _elevation_16(elevations.get(key), notes, problems)
        # TKB deliberately has no fallback to the KB elevation: no source in the
        # corpus gives the KB-to-TKB separation, so they are not interchangeable.

    deviated = bool(_get_16(supplied, "deviated") or False)
    detail = str(_get_16(supplied, "detail") or "")
    if not detail:
        # #15 attaches its own Refusal to an unresolved DatumResolution; quote it
        # rather than telling the operator only that the datum is unresolved.
        attached = _get_16(supplied, "refusal")
        if isinstance(attached, Refusal):
            detail = attached.reason
    source = str(_get_16(supplied, "source") or "")
    well = str(_get_16(supplied, "well") or _get_16(supplied, "well_name") or label)
    extra = _get_16(supplied, "extra")
    carried = dict(extra) if isinstance(extra, Mapping) else {}
    if notes and elevation is not None:
        carried["elevation_unit_conversion"] = notes[0]

    return WellDatum(well=well, reference=reference, elevation_ft=elevation,
                     resolved=resolved, source=source, detail=detail,
                     deviated=deviated, elevation_problem=problems[0] if problems else None,
                     extra=carried)


def datum_reconcile(well_a: Any, well_b: Any, *,
                    marker_tvd_a_ft: float | None = None,
                    marker_tvd_b_ft: float | None = None,
                    tolerance_ft: float = 0.0) -> Quantity | Refusal:
    """Reconcile two wells' elevation references. Tearpock p. 61 (`#24`).

    Three outcomes, and the third is why the tool exists:

    - both references at the same elevation -> `Quantity(0.0, "ft")`,
      flag `datums-agree`;
    - different elevations -> `Quantity(E_A - E_B, "ft")`,
      flag `correction-required`;
    - it cannot be determined -> `Refusal`, whose `.value` is None.

    The correction is `E_A - E_B`: ADD IT TO A WELL-B DEPTH to express that depth
    in well A's reference frame. Positive means well A's reference sits higher, so
    a horizon at a given subsea elevation reads deeper on well A's log. It does
    NOT mean well A is structurally high.

    `marker_tvd_a_ft` / `marker_tvd_b_ft` are the TVD of the SAME marker in each
    well; supply both or neither. Given them, the tool splits the apparent depth
    difference into the part that is datum artifact and the part that is geology.
    """
    datum_a, blocker_a, needed_a = _coerce_datum(well_a, "well_a")
    datum_b, blocker_b, needed_b = _coerce_datum(well_b, "well_b")

    if blocker_a or blocker_b:
        reasons = [r for r in (blocker_a, blocker_b) if r]
        needed = list(needed_a) + list(needed_b)
        return Refusal(
            reason="datum cannot be reconciled: " + "; ".join(reasons)
                   + ". Returning no correction would be indistinguishable from "
                     "returning a zero correction, and correlating on an unknown "
                     "datum produces an elevation error that looks like structure.",
            needed=tuple(dict.fromkeys(needed)),
            source=TEARPOCK_DATUM,
        )

    if (marker_tvd_a_ft is None) != (marker_tvd_b_ft is None):
        return Refusal(
            reason="the structural split needs the same marker's TVD in BOTH wells; "
                   "exactly one was supplied and this tool will not guess which well "
                   "the caller meant",
            needed=("marker_tvd_a_ft and marker_tvd_b_ft, or neither",),
            source=TEARPOCK_DATUM,
        )

    if not math.isfinite(tolerance_ft) or tolerance_ft < 0:
        raise ValueError("tolerance_ft must be a finite, non-negative number of feet")

    elevation_a = float(datum_a.elevation_ft)  # type: ignore[arg-type]
    elevation_b = float(datum_b.elevation_ft)  # type: ignore[arg-type]
    correction = elevation_a - elevation_b

    inputs: dict[str, Any] = {
        "well_a": datum_a.well,
        "well_b": datum_b.well,
        "reference_a": datum_a.reference,
        "reference_b": datum_b.reference,
        "elevation_a_ft": elevation_a,
        "elevation_b_ft": elevation_b,
    }
    if datum_a.source:
        inputs["datum_resolve_source_a"] = datum_a.source
    if datum_b.source:
        inputs["datum_resolve_source_b"] = datum_b.source

    flags: list[str] = []
    agree = abs(correction) <= tolerance_ft
    flags.append("datums-agree" if agree else "correction-required")

    # A converted elevation is still a converted elevation: the operator is told,
    # on the result, that the number they handed in was not in feet.
    for side, datum in (("well_a", datum_a), ("well_b", datum_b)):
        note = datum.extra.get("elevation_unit_conversion")
        if note:
            flags.append(f"{side}: {note}")

    if datum_a.reference != datum_b.reference:
        flags.append(f"reference-mismatch: {datum_a.reference} vs {datum_b.reference}")
        if agree:
            flags.append("coincident-elevations-different-references")

    deviated = datum_a.deviated or datum_b.deviated
    if deviated:
        flags.append("deviated: correction is an elevation offset applied to TVD, "
                     "not to MD; a reconciled datum does not make two MD logs "
                     "comparable")

    if marker_tvd_a_ft is not None and marker_tvd_b_ft is not None:
        # Sign lives in subsea_convert and nowhere else. SSTVD = -(TVD - E),
        # negative below sea level (Tearpock writes -1340 ft).
        sstvd_a = subsea_convert(float(marker_tvd_a_ft), elevation_a, True,
                                 reference=datum_a.reference or "KB",
                                 deviated=datum_a.deviated)
        sstvd_b = subsea_convert(float(marker_tvd_b_ft), elevation_b, True,
                                 reference=datum_b.reference or "KB",
                                 deviated=datum_b.deviated)
        for side, result in (("well_a", sstvd_a), ("well_b", sstvd_b)):
            if isinstance(result, Refusal):
                return Refusal(
                    reason=f"subsea conversion of the {side} marker refused: "
                           f"{result.reason}",
                    needed=result.needed,
                    source=result.source or TEARPOCK_DATUM,
                )
        raw_diff = float(marker_tvd_a_ft) - float(marker_tvd_b_ft)
        inputs["marker_tvd_a_ft"] = float(marker_tvd_a_ft)
        inputs["marker_tvd_b_ft"] = float(marker_tvd_b_ft)
        inputs["sstvd_a_ft"] = sstvd_a.value
        inputs["sstvd_b_ft"] = sstvd_b.value
        inputs["raw_diff_ft"] = raw_diff
        inputs["datum_artifact_ft"] = correction
        # structural = raw - correction = (TVD_A - E_A) - (TVD_B - E_B)
        #            = -(SSTVD_A - SSTVD_B); positive means A truly deeper subsea.
        inputs["structural_ft"] = raw_diff - correction
        flags.append("marker-supplied: raw depth difference split into datum and "
                     "structural parts")

    return Quantity(
        correction, "ft",
        "datum reconcile via SSTVD = -(TVD - E) (Tearpock p. 61)",
        TEARPOCK_DATUM,
        inputs=inputs,
        assumptions={
            "correction_ft": "E_a - E_b",
            "correction_applies_to": "well_b depths, to put them in well_a's frame",
            "sign": "positive means well_a's reference is higher, so a horizon at a "
                    "given subsea elevation reads deeper on well_a",
            "subsea_sign": "negative below sea level, from subsea_convert",
            "tolerance_ft": tolerance_ft,
            "tolerance_provenance": "CALLER — no source states an elevation "
                                    "tolerance; default 0.0 swallows nothing",
            "reference_names": ASQUITH_REFERENCES,
            "hole": "deviated" if deviated else "vertical",
        },
        flags=tuple(flags),
    )

# ---------------------------------------------------------------------------
# 19_offset_geometry
# Offset-well geometry: distance and bearing between two wells (#19).
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Provenance strings
# ---------------------------------------------------------------------------

# `tool-catalog.md:254` reads "Source: none - no source in corpus. no
# distance/bearing formula in corpus; arguably plumbing". See the module
# docstring and the spec's "Kind" section for why that verdict is accepted for
# the arithmetic and rejected for the gate.
NO_CITATION = (
    "not applicable - plumbing arithmetic, no citation owed "
    "(tool-catalog.md:254 'no distance/bearing formula in corpus; arguably plumbing')"
)

# Neither anchor below sources a formula. They are the evidence that a
# coordinate without a declared frame is not a coordinate, which is what the
# refusals in this module encode. Quoted in `assumptions`, never in `source`.
RRC_LATLON_TYPE = "09-gas-deliverability/rrc-section-f-completions-electric-logs#2"
RRC_LATLON_TYPE_QUOTE = (
    'RRC Form W-2/G-1 field 6: "Well Latitude/Longitude (minimum five decimal places '
    'required):" with a separate field "Latitude/Longitude type:" beside it - the '
    "regulator requires the frame to be declared, not inferred"
)
SPC_ZONE_DATUM = "06-fort-worth-basin/alhakeem-2013-boonsville-3d-seismic-thesis#5"
SPC_ZONE_DATUM_QUOTE = (
    'alhakeem#5: Boonsville corner coordinates are "X and Y values for the North Central '
    'Texas Zone (4202) of the U. S. State Plane Coordinate System and the 1927 North '
    'American Datum" - zone and datum travel with the numbers'
)

# ---------------------------------------------------------------------------
# Constants. Each says what it is and where it came from.
# ---------------------------------------------------------------------------

# WGS84 DEFINING constants. These two are the definition of the ellipsoid (the
# semi-major axis is exact by definition, the flattening is the defining
# inverse); everything geodetic below is derived from them in code rather than
# quoted, so the arithmetic is checkable and only two numbers are asserted.
# Not from this corpus - no corpus document defines an ellipsoid. They are not
# in dispute and no formula in this module depends on believing a source about
# them; they set the SIZE of a declared approximation, and that approximation's
# error is computed and reported.
WGS84_A_M = 6378137.0                      # semi-major axis, metres (exact, defining)
WGS84_INV_F = 298.257223563                # inverse flattening (defining)

WGS84_F = 1.0 / WGS84_INV_F                # 3.352810664747...e-3
WGS84_B_M = WGS84_A_M * (1.0 - WGS84_F)    # semi-minor axis  = 6356752.314245 m
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)       # first eccentricity squared = 6.694380e-3

# IUGG mean radius R1 = (2a + b)/3 = 6371008.771415 m. The sphere the haversine
# in `_geographic_pair` runs on. Declared, not assumed: see SPHERE_ERROR_BOUND.
EARTH_MEAN_RADIUS_M = (2.0 * WGS84_A_M + WGS84_B_M) / 3.0

# How far a sphere of R1 can be from the ellipsoid, computed from the same two
# defining constants. The meridional radius of curvature
# M = a(1-e^2)/(1 - e^2 sin^2 phi)^(3/2) runs from a(1-e^2) at the equator to
# a/sqrt(1-e^2) at the pole; the bound is the larger relative departure from R1.
# 0.005583 -> +/-0.558%. Attached to every geographic result.
_M_EQUATOR_M = WGS84_A_M * (1.0 - WGS84_E2)                 # 6335439.327 m
_M_POLE_M = WGS84_A_M / math.sqrt(1.0 - WGS84_E2)           # 6399593.626 m
SPHERE_ERROR_BOUND = max(
    abs(_M_EQUATOR_M / EARTH_MEAN_RADIUS_M - 1.0),
    abs(_M_POLE_M / EARTH_MEAN_RADIUS_M - 1.0),
)

# Length units, metres per unit. Every factor is exact by definition, so a
# round trip through metres is lossless.
#   us survey foot : 1200/3937 m exactly (US Metric Act of 1866 / the survey
#                    foot; the definition SPCS27 and SPCS83 feet are stated in)
#   international foot : 0.3048 m exactly (1959 international yard and pound
#                    agreement)
#   statute mile   : 5280 international feet = 1609.344 m exactly
# usft and ift differ by 2 ppm - 0.02 ft per 10000 ft. Below every other term
# in this module, and still stated rather than assumed silently.
METRES_PER_UNIT: dict[str, float] = {
    "m": 1.0,
    "km": 1000.0,
    "usft": 1200.0 / 3937.0,
    "ift": 0.3048,
    "mi": 1609.344,
}

# A bare "ft" is ambiguous. It is taken as the US survey foot, because that is
# the foot the State Plane Coordinate System and Texas survey practice are
# defined in, and the assumption is flagged on the result rather than buried.
AMBIGUOUS_FOOT = "ft"
AMBIGUOUS_FOOT_MEANS = "usft"

_UNIT_SPELLINGS: dict[str, str] = {
    "m": "m", "metre": "m", "meter": "m", "metres": "m", "meters": "m",
    "km": "km", "kilometre": "km", "kilometer": "km",
    "ft": AMBIGUOUS_FOOT, "foot": AMBIGUOUS_FOOT, "feet": AMBIGUOUS_FOOT,
    "usft": "usft", "usfeet": "usft", "ussurveyfoot": "usft",
    "ussurveyfeet": "usft", "surveyfoot": "usft", "usft2": "usft",
    "ift": "ift", "internationalfoot": "ift", "internationalfeet": "ift",
    "intlfoot": "ift",
    "mi": "mi", "mile": "mi", "miles": "mi", "statutemile": "mi",
}

# Datum spelling normalization ONLY. This is not a geodetic registry and does
# not assert that any two datums are equivalent: it folds spellings of the SAME
# name. An unrecognized spelling is compared verbatim, so two identical unknown
# spellings still pass and two different spellings of one datum refuse - the
# conservative direction. NAD83 and WGS84 are deliberately NOT folded together;
# they differ at the metre level.
_DATUM_SPELLINGS: dict[str, str] = {
    "NAD27": "NAD27", "NAD1927": "NAD27", "NORTHAMERICANDATUM1927": "NAD27",
    "NORTHAMERICANDATUMOF1927": "NAD27",
    "NAD83": "NAD83", "NAD1983": "NAD83", "NORTHAMERICANDATUM1983": "NAD83",
    "NORTHAMERICANDATUMOF1983": "NAD83",
    "WGS84": "WGS84", "WGS1984": "WGS84", "WORLDGEODETICSYSTEM1984": "WGS84",
}

# Tokens that mean "nobody said". Treated as absent, never as a datum name.
_ABSENT_TOKENS = {"", "?", "NA", "N/A", "NONE", "NULL", "UNKNOWN", "UNK", "TBD", "ASSUMED"}

# OWNED, UNCITED. No corpus document states a datum shift magnitude. Used only
# to explain WHY the tool refuses on mixed datums - never in a computation.
NAD_SHIFT_NOTE = (
    "the NAD27/NAD83 horizontal shift in Texas is of order 100 ft, larger than the "
    "well spacings this tool is asked about (owned assertion, not sourced in this corpus)"
)

# The RRC requires latitude/longitude to a MINIMUM of five decimal places
# (`rrc-section-f-completions-electric-logs#2`). One unit in the fifth decimal
# of latitude is this many feet, so a smaller separation may not be resolvable
# at the precision the regulator guarantees. A floor derived from a stated
# rule, not an invented threshold.
RRC_LATLON_MIN_DECIMALS = 5
LATLON_RESOLUTION_M = math.radians(10.0 ** -RRC_LATLON_MIN_DECIMALS) * EARTH_MEAN_RADIUS_M

KIND_GEOGRAPHIC = "geographic"
KIND_PROJECTED = "projected"
_KINDS = (KIND_GEOGRAPHIC, KIND_PROJECTED)

# Location descriptions that are survey calls, not coordinates. RRC form field
# 5a is "Location (section, block and survey)" - a real way a Texas location
# arrives and one this tool cannot difference (refusal R7).
#
# The spelled-out words are not enough: on real Texas logs the call arrives
# abbreviated. Both LAS fixtures in `tests/fixtures/` carry exactly this shape
# and no coordinate at all -
#   "383' FNL & 1262' FEL. SEC. 1099 T.E. & L. SURV. 4 MI. NE IVAN"
#   "2509' FSL X 1072' FEL, SEC 4 BLK 1 SP RR CO A-1772"
# - so `SEC.`/`SURV.`/`BLK`, the abstract number `A-1772`, and the footage-call
# tokens FNL/FSL/FEL/FWL all have to be recognized or R7 never fires on the data
# this tool actually meets. Matched on word boundaries so `sec` does not fire on
# "secondary". False positives here cost a refusal, never a wrong answer, and R7
# is only consulted when no CRS was declared.
_SURVEY_CALL_WORDS = ("section", "block", "survey", "abstract", "league", "labor", "footage")
_SURVEY_CALL_RE = re.compile(
    r"\b(?:sections?|blocks?|surveys?|abstracts?|leagues?|labors?|footages?"
    r"|secs?|blks?|surv|svy|abst|f[nsew]l)\b"
    r"|\ba-\s?\d+\b",
    re.IGNORECASE,
)

METHOD_PLANAR = "planar separation in one projected CRS"
METHOD_HAVERSINE = "great-circle (haversine) on a sphere of declared radius"
METHOD_BEARING_GRID = "grid bearing, atan2(dE, dN)"
METHOD_BEARING_TRUE = "true initial great-circle bearing, atan2(sin dlon cos lat2, cos lat1 sin lat2 - sin lat1 cos lat2 cos dlon)"


# ---------------------------------------------------------------------------
# Input records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Crs:
    """A declared coordinate reference system. Every field is the caller's
    assertion; nothing here is inferred from any coordinate value.

    `kind` is validated at construction because a third kind is a programmer
    error. `datum`, `zone` and `units` are NOT validated here: a missing
    declaration is a domain refusal the caller must be able to render, so it is
    caught by the gate and returned as a `Refusal`.
    """

    kind: str
    datum: str | None = None
    name: str = ""
    zone: str | None = None
    units: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ValueError(f"crs kind must be one of {_KINDS}, got {self.kind!r}")

    def label(self) -> str:
        bits = [self.name] if self.name else []
        bits.append(self.kind)
        if self.datum:
            bits.append(str(self.datum))
        if self.zone:
            bits.append(f"zone {self.zone}")
        if self.units:
            bits.append(str(self.units))
        return " / ".join(bits)


@dataclass(frozen=True)
class WellLocation:
    """One well's location, in one declared CRS, for one declared point.

    `point` says WHICH point on the well the coordinate is - surface,
    bottomhole, mid-perf. It has no default and its absence refuses: a
    horizontal well's surface and bottomhole locations can be a mile apart, so
    "the distance between two wells" is undefined until the caller says which
    end of each well it means.
    """

    name: str
    crs: Crs | None = None
    lat_deg: float | None = None
    lon_deg: float | None = None
    easting: float | None = None
    northing: float | None = None
    point: str | None = None
    location_description: str | None = None   # e.g. a section/block/survey call


# ---------------------------------------------------------------------------
# Coercion and normalization helpers
# ---------------------------------------------------------------------------


def _norm_token(s: Any) -> str:
    """Uppercase, strip everything that is not alphanumeric. Spelling only."""
    return "".join(ch for ch in str(s).upper() if ch.isalnum())


def _absent(s: Any) -> bool:
    return s is None or _norm_token(s) in _ABSENT_TOKENS


def _norm_datum(datum: Any) -> str:
    tok = _norm_token(datum)
    return _DATUM_SPELLINGS.get(tok, tok)


def _norm_zone(zone: Any) -> str:
    return _norm_token(zone)


def _norm_unit(unit: Any) -> str | None:
    """Map a unit spelling to a key of METRES_PER_UNIT, or AMBIGUOUS_FOOT."""
    tok = "".join(ch for ch in str(unit).lower() if ch.isalnum())
    return _UNIT_SPELLINGS.get(tok)


def _metres_per(unit_key: str) -> float:
    if unit_key == AMBIGUOUS_FOOT:
        return METRES_PER_UNIT[AMBIGUOUS_FOOT_MEANS]
    return METRES_PER_UNIT[unit_key]


def _as_crs(crs: Any) -> Crs | None:
    if crs is None or isinstance(crs, Crs):
        return crs
    if isinstance(crs, Mapping):
        kind = crs.get("kind")
        if kind not in _KINDS:
            raise ValueError(f"crs kind must be one of {_KINDS}, got {kind!r}")
        return Crs(kind=kind, datum=crs.get("datum"), name=crs.get("name", "") or "",
                   zone=crs.get("zone"), units=crs.get("units"))
    raise TypeError(f"crs must be a Crs, a mapping or None, got {type(crs).__name__}")


def _as_location(loc: Any, label: str) -> WellLocation:
    if isinstance(loc, WellLocation):
        return loc
    if isinstance(loc, Mapping):
        return WellLocation(
            name=str(loc.get("name", label)),
            crs=_as_crs(loc.get("crs")),
            lat_deg=loc.get("lat_deg"),
            lon_deg=loc.get("lon_deg"),
            easting=loc.get("easting"),
            northing=loc.get("northing"),
            point=loc.get("point"),
            location_description=loc.get("location_description"),
        )
    raise TypeError(f"{label} must be a WellLocation or a mapping, got {type(loc).__name__}")


def _finite(v: Any) -> bool:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    return math.isfinite(f)


def _looks_like_survey_call(loc: WellLocation) -> bool:
    text = loc.location_description or ""
    return bool(_SURVEY_CALL_RE.search(text))


# ---------------------------------------------------------------------------
# The gate. Everything that can refuse, in one place and in a fixed order.
# ---------------------------------------------------------------------------


def _gate(a: WellLocation, b: WellLocation) -> Refusal | dict[str, Any]:
    """Validate the pair and return the resolved frame, or the reason it cannot.

    Refusal order is deliberate: frame problems are reported before coordinate
    problems, because a missing CRS makes the coordinates unreadable rather
    than merely absent.
    """
    # R7 - a survey call is not a coordinate. Checked first: it is the case
    # where the caller has a location but not one this tool can difference.
    for loc in (a, b):
        if loc.crs is None and _looks_like_survey_call(loc):
            return Refusal(
                reason=(
                    f"{loc.name}'s location is given as a survey call "
                    f"({loc.location_description!r}), which is not a coordinate. RRC form "
                    "field 5a records a location as section, block and survey with footages "
                    "from a survey line; converting that to a coordinate needs the survey "
                    "plat, which this tool has no access to"
                ),
                needed=("a coordinate in a declared CRS - latitude/longitude, or a state "
                        "plane easting/northing with its zone and datum",),
                source=NO_CITATION,
            )

    # R1 - the CRS is a required input and is never inferred from the numbers.
    for loc in (a, b):
        if loc.crs is None:
            return Refusal(
                reason=(
                    f"{loc.name} has no declared coordinate reference system. The CRS is a "
                    "required input and is never inferred from the magnitude of the "
                    "coordinates: 1864886 is not evidence of state plane and 33.17 is not "
                    "evidence of latitude"
                ),
                needed=(f"{loc.name}: crs.kind ('geographic' or 'projected') and crs.datum; "
                        "if projected, also crs.zone and crs.units",),
                source=NO_CITATION,
            )
        if _absent(loc.crs.datum):
            return Refusal(
                reason=(
                    f"{loc.name}'s CRS names no datum (got {loc.crs.datum!r}). Without it the "
                    "two wells cannot be shown to be in the same frame, and "
                    + NAD_SHIFT_NOTE
                ),
                needed=(f"{loc.name}: crs.datum, e.g. 'NAD27' or 'NAD83'",),
                source=NO_CITATION,
            )

    # R2 - mixed classes. That is a projection, and this tool does not project.
    if a.crs.kind != b.crs.kind:
        return Refusal(
            reason=(
                f"{a.name} is in a {a.crs.kind} CRS and {b.name} is in a {b.crs.kind} CRS. "
                "Differencing them requires a forward or inverse map projection, which is "
                "not implemented here and is not sourced anywhere in this corpus"
            ),
            needed=("both wells in the same CRS class, or a projection library with a "
                    "sourced definition of the projected CRS",),
            source=NO_CITATION,
        )

    # R4 - datum. Checked before zone because it applies to both classes, and
    # this is the refusal that would otherwise silently answer: the subtraction
    # works, the number looks like feet, and it is wrong by the datum shift.
    da, db = _norm_datum(a.crs.datum), _norm_datum(b.crs.datum)
    if da != db:
        return Refusal(
            reason=(
                f"{a.name} is on datum {a.crs.datum!r} and {b.name} is on datum "
                f"{b.crs.datum!r}. A datum transformation is required before these "
                "coordinates can be differenced; NAD27<->NAD83 needs a NADCON-grade grid "
                "shift, which is not implemented here and is not sourced in this corpus. "
                "The subtraction would succeed and be wrong: " + NAD_SHIFT_NOTE
            ),
            needed=("both wells on the same datum, or a sourced datum transformation",),
            source=NO_CITATION,
        )

    kind = a.crs.kind
    frame: dict[str, Any] = {"kind": kind, "datum": da}

    if kind == KIND_PROJECTED:
        # R3 - zone. No zone-name registry is asserted, so two spellings of one
        # zone also refuse; see spec open question 2.
        for loc in (a, b):
            if _absent(loc.crs.zone):
                return Refusal(
                    reason=(
                        f"{loc.name}'s projected CRS names no zone (got {loc.crs.zone!r}). "
                        "A state plane easting and northing mean nothing without the zone "
                        "they were computed in"
                    ),
                    needed=(f"{loc.name}: crs.zone, e.g. '4202' (Texas North Central)",),
                    source=NO_CITATION,
                )
        za, zb = _norm_zone(a.crs.zone), _norm_zone(b.crs.zone)
        if za != zb:
            return Refusal(
                reason=(
                    f"{a.name} is in zone {a.crs.zone!r} and {b.name} is in zone "
                    f"{b.crs.zone!r}. Coordinates in two projected zones are in two "
                    "different frames and cannot be differenced at all - the result would "
                    "not be inaccurate, it would be meaningless. Reprojection is not "
                    "implemented here. Note this tool asserts no zone-name registry, so two "
                    "spellings of the same zone also refuse: state them identically"
                ),
                needed=("both wells in the same zone, or a sourced reprojection",),
                source=NO_CITATION,
            )
        for loc in (a, b):
            if _absent(loc.crs.units):
                return Refusal(
                    reason=(f"{loc.name}'s projected CRS names no length unit (got "
                            f"{loc.crs.units!r}); a state plane easting can be in metres, "
                            "US survey feet or international feet"),
                    needed=(f"{loc.name}: crs.units - 'm', 'usft', 'ift' (or 'ft', taken as "
                            "the US survey foot and flagged)",),
                    source=NO_CITATION,
                )
        ua, ub = _norm_unit(a.crs.units), _norm_unit(b.crs.units)
        for loc, u in ((a, ua), (b, ub)):
            if u is None:
                return Refusal(
                    reason=(f"{loc.name}'s length unit {loc.crs.units!r} is not one this tool "
                            "recognizes; it is not guessed"),
                    needed=("crs.units in " + ", ".join(sorted(METRES_PER_UNIT)) + " or 'ft'",),
                    source=NO_CITATION,
                )
        frame.update({"zone": za, "zone_as_written": a.crs.zone, "units": (ua, ub)})

        # R5 - coordinates present and finite.
        for loc in (a, b):
            for field_name, v in (("easting", loc.easting), ("northing", loc.northing)):
                if not _finite(v):
                    return Refusal(
                        reason=(f"{loc.name} has no usable {field_name} (got {v!r}) in its "
                                "declared projected CRS"),
                        needed=(f"{loc.name}: a finite {field_name} in {loc.crs.units}",),
                        source=NO_CITATION,
                    )
    else:
        # R5 - geographic coordinates present, finite and in range.
        for loc in (a, b):
            for field_name, v, lim in (("lat_deg", loc.lat_deg, 90.0),
                                       ("lon_deg", loc.lon_deg, 180.0)):
                if not _finite(v):
                    return Refusal(
                        reason=(f"{loc.name} has no usable {field_name} (got {v!r}) in its "
                                "declared geographic CRS"),
                        needed=(f"{loc.name}: a finite {field_name} in decimal degrees",),
                        source=NO_CITATION,
                    )
                if abs(float(v)) > lim:
                    return Refusal(
                        reason=(f"{loc.name}'s {field_name} is {float(v)}, outside "
                                f"[-{lim:g}, {lim:g}]; it is not a decimal degree in this "
                                "CRS. Longitude is east-positive here - a Texas longitude is "
                                "negative"),
                        needed=(f"{loc.name}: {field_name} within [-{lim:g}, {lim:g}]",),
                        source=NO_CITATION,
                    )

    # R6 - which point on the well. Last, because it is the only refusal that is
    # about the question rather than the coordinates.
    for loc in (a, b):
        if _absent(loc.point):
            return Refusal(
                reason=(
                    f"{loc.name} does not say which point on the well its coordinate is "
                    f"(got {loc.point!r}). A horizontal well's surface and bottomhole "
                    "locations can be a mile apart, so the distance between two wells is "
                    "undefined until the caller states which end of each well it means"
                ),
                needed=(f"{loc.name}: point, e.g. 'surface', 'bottomhole', 'mid-perf'",),
                source=NO_CITATION,
            )

    return frame


# ---------------------------------------------------------------------------
# The two computations
# ---------------------------------------------------------------------------


def _projected_pair(a: WellLocation, b: WellLocation,
                    frame: dict[str, Any]) -> dict[str, Any]:
    """Planar separation and grid bearing, working in metres.

    `atan2(dE, dN)` and not `atan2(dN, dE)`: an azimuth is measured from +N
    toward +E, the transpose of the mathematical convention.
    """
    ua, ub = frame["units"]
    ka, kb = _metres_per(ua), _metres_per(ub)
    de_m = float(b.easting) * kb - float(a.easting) * ka
    dn_m = float(b.northing) * kb - float(a.northing) * ka
    d_m = math.hypot(de_m, dn_m)
    bearing = math.degrees(math.atan2(de_m, dn_m)) % 360.0 if d_m > 0.0 else None
    return {
        "distance_m": d_m,
        "bearing_deg": bearing,
        "de_m": de_m,
        "dn_m": dn_m,
        "units": (ua, ub),
    }


def _geographic_pair(a: WellLocation, b: WellLocation) -> dict[str, Any]:
    """Haversine arc and true initial bearing on a sphere of EARTH_MEAN_RADIUS_M.

    Haversine rather than the spherical law of cosines: the law of cosines
    loses precision at short separations, and short separations are the entire
    use case.
    """
    la1, la2 = math.radians(float(a.lat_deg)), math.radians(float(b.lat_deg))
    lo1, lo2 = math.radians(float(a.lon_deg)), math.radians(float(b.lon_deg))
    dla, dlo = la2 - la1, lo2 - lo1

    h = math.sin(dla / 2.0) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2.0) ** 2
    d_m = 2.0 * EARTH_MEAN_RADIUS_M * math.asin(math.sqrt(min(1.0, h)))

    y = math.sin(dlo) * math.cos(la2)
    x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlo)
    bearing = math.degrees(math.atan2(y, x)) % 360.0 if (y != 0.0 or x != 0.0) else None
    if d_m == 0.0:
        bearing = None
    return {"distance_m": d_m, "bearing_deg": bearing, "dlat_deg": float(b.lat_deg) - float(a.lat_deg),
            "dlon_deg": float(b.lon_deg) - float(a.lon_deg), "haversine_h": h}


# ---------------------------------------------------------------------------
# Flags shared by both public entry points
# ---------------------------------------------------------------------------


def _shared_flags(a: WellLocation, b: WellLocation, frame: dict[str, Any],
                  geom: dict[str, Any]) -> list[str]:
    flags: list[str] = []

    if _norm_token(a.point) != _norm_token(b.point):
        flags.append(
            f"point types differ: {a.name} is {a.point!r} and {b.name} is {b.point!r}; "
            "this is a legitimate question but the two coordinates are not the same kind "
            "of location"
        )

    if frame["kind"] == KIND_PROJECTED:
        ua, ub = frame["units"]
        if AMBIGUOUS_FOOT in (ua, ub):
            flags.append(
                "a bare 'ft' was declared and is taken as the US survey foot (1200/3937 m), "
                "the foot the State Plane Coordinate System is defined in; the international "
                "foot would differ by 2 ppm, 0.02 ft per 10000 ft"
            )
        for loc in (a, b):
            if abs(float(loc.easting)) <= 180.0 and abs(float(loc.northing)) <= 90.0:
                flags.append(
                    f"{loc.name}'s coordinates ({loc.easting}, {loc.northing}) fall inside the "
                    "range of decimal degrees while the CRS is declared projected; the "
                    "declaration governs and was used unchanged, but the two look "
                    "inconsistent"
                )
    return flags


def _radius_assumptions() -> dict[str, Any]:
    return {
        "earth_model": "sphere",
        "earth_radius_m": EARTH_MEAN_RADIUS_M,
        "earth_radius_usft": EARTH_MEAN_RADIUS_M / METRES_PER_UNIT["usft"],
        "earth_radius_basis": "IUGG mean radius R1 = (2a + b)/3, from the WGS84 defining "
                              "a = 6378137 m and 1/f = 298.257223563",
        "sphere_error_bound_fraction": SPHERE_ERROR_BOUND,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def offset_distance(a: Any, b: Any, *, distance_unit: str = "ft") -> Quantity | Refusal:
    """Horizontal separation between two wells, in one declared CRS.

    Returns a `Quantity` in `distance_unit` (default: the US survey foot), or a
    `Refusal` naming what is missing. See the module docstring for the frame
    rules; the arithmetic is in `_projected_pair` / `_geographic_pair`.
    """
    a = _as_location(a, "a")
    b = _as_location(b, "b")

    out_unit = _norm_unit(distance_unit)
    if out_unit is None:
        raise ValueError(
            f"unknown distance_unit {distance_unit!r}; expected one of "
            + ", ".join(sorted(METRES_PER_UNIT)) + " or 'ft'"
        )

    frame = _gate(a, b)
    if isinstance(frame, Refusal):
        return frame

    if frame["kind"] == KIND_PROJECTED:
        geom = _projected_pair(a, b, frame)
        method = METHOD_PLANAR
        assumptions: dict[str, Any] = {
            "crs_class": KIND_PROJECTED,
            "datum": frame["datum"],
            "zone": frame["zone_as_written"],
            "distance_kind": "grid distance",
            "crs_declared_by_caller": True,
            "crs_evidence": SPC_ZONE_DATUM_QUOTE,
            "crs_evidence_anchor": SPC_ZONE_DATUM,
        }
        flags = _shared_flags(a, b, frame, geom)
        flags.append(
            "this is a GRID distance in the projected CRS, not a ground distance; they "
            "differ by the point scale factor of the projection (of order 1 part in 10^4 "
            "in a Texas Lambert zone), which is not applied here because applying it needs "
            "the projection definition this tool does not carry"
        )
        inputs = {
            "a": a.name, "b": b.name,
            "a_easting": a.easting, "a_northing": a.northing,
            "b_easting": b.easting, "b_northing": b.northing,
            "a_units": a.crs.units, "b_units": b.crs.units,
            "a_point": a.point, "b_point": b.point,
            "dE_m": geom["de_m"], "dN_m": geom["dn_m"],
        }
    else:
        geom = _geographic_pair(a, b)
        method = METHOD_HAVERSINE
        assumptions = {
            "crs_class": KIND_GEOGRAPHIC,
            "datum": frame["datum"],
            "distance_kind": "great-circle arc",
            "longitude_sign": "east positive",
            "crs_declared_by_caller": True,
            "crs_evidence": RRC_LATLON_TYPE_QUOTE,
            "crs_evidence_anchor": RRC_LATLON_TYPE,
            "coordinate_resolution_m": LATLON_RESOLUTION_M,
            "coordinate_resolution_basis": (
                f"RRC form field 6 requires latitude/longitude to a minimum of "
                f"{RRC_LATLON_MIN_DECIMALS} decimal places ({RRC_LATLON_TYPE}); one unit in "
                "that place is this arc on the declared sphere"
            ),
        }
        assumptions.update(_radius_assumptions())
        flags = _shared_flags(a, b, frame, geom)
        flags.append(
            f"spherical earth model: a sphere of R1 departs from the WGS84 ellipsoid by up "
            f"to {SPHERE_ERROR_BOUND * 100:.3f}%, i.e. "
            f"{geom['distance_m'] * SPHERE_ERROR_BOUND / _metres_per(out_unit):.3f} "
            f"{out_unit} on this separation. An ellipsoidal (Vincenty/Karney) distance is "
            "not offered because no such formula is in this corpus"
        )
        if geom["distance_m"] <= LATLON_RESOLUTION_M:
            flags.append(
                "the separation is at or below the arc of one unit in the fifth decimal "
                f"place of latitude ({LATLON_RESOLUTION_M / _metres_per(out_unit):.3f} "
                f"{out_unit}); at the minimum precision the RRC requires these two "
                "locations may not be distinguishable"
            )
        inputs = {
            "a": a.name, "b": b.name,
            "a_lat_deg": a.lat_deg, "a_lon_deg": a.lon_deg,
            "b_lat_deg": b.lat_deg, "b_lon_deg": b.lon_deg,
            "a_point": a.point, "b_point": b.point,
            "dlat_deg": geom["dlat_deg"], "dlon_deg": geom["dlon_deg"],
            "haversine_h": geom["haversine_h"],
        }

    value = geom["distance_m"] / _metres_per(out_unit)
    if out_unit == AMBIGUOUS_FOOT:
        assumptions["foot"] = "US survey foot (1200/3937 m exactly)"
    return Quantity(value, out_unit, method, NO_CITATION,
                    inputs=inputs, assumptions=assumptions, flags=tuple(flags))


def offset_bearing(a: Any, b: Any) -> Quantity | Refusal:
    """Bearing from well A to well B, degrees in [0, 360), clockwise from north.

    Projected input returns a GRID bearing, from the projection's +N axis;
    geographic input returns a TRUE initial great-circle bearing. They are not
    interchangeable - they differ by the grid convergence angle, which this tool
    flags and does not compute. Neither is magnetic.
    """
    a = _as_location(a, "a")
    b = _as_location(b, "b")

    frame = _gate(a, b)
    if isinstance(frame, Refusal):
        return frame

    if frame["kind"] == KIND_PROJECTED:
        geom = _projected_pair(a, b, frame)
        method = METHOD_BEARING_GRID
        reference = "grid north"
        assumptions = {
            "crs_class": KIND_PROJECTED,
            "datum": frame["datum"],
            "zone": frame["zone_as_written"],
            "crs_evidence": SPC_ZONE_DATUM_QUOTE,
            "crs_evidence_anchor": SPC_ZONE_DATUM,
        }
        extra_flag = (
            "GRID bearing, measured from the projection's grid north. Grid north is not "
            "true north: the two differ by the grid convergence angle, which is not "
            "computed here because it needs the projection definition this tool does not "
            "carry. On the Boonsville corners (alhakeem#5) the difference is 0.24 degrees, "
            "and it grows toward a zone edge"
        )
        inputs = {
            "a": a.name, "b": b.name,
            "a_easting": a.easting, "a_northing": a.northing,
            "b_easting": b.easting, "b_northing": b.northing,
            "a_point": a.point, "b_point": b.point,
            "dE_m": geom["de_m"], "dN_m": geom["dn_m"],
        }
    else:
        geom = _geographic_pair(a, b)
        method = METHOD_BEARING_TRUE
        reference = "true north"
        assumptions = {
            "crs_class": KIND_GEOGRAPHIC,
            "datum": frame["datum"],
            "longitude_sign": "east positive",
            "crs_evidence": RRC_LATLON_TYPE_QUOTE,
            "crs_evidence_anchor": RRC_LATLON_TYPE,
        }
        assumptions.update(_radius_assumptions())
        extra_flag = (
            "TRUE initial bearing at A. A great-circle azimuth changes along the path, so "
            "the bearing back from B is NOT this value plus 180 degrees, and this is not a "
            "constant-heading rhumb line. Not magnetic: no declination is applied"
        )
        inputs = {
            "a": a.name, "b": b.name,
            "a_lat_deg": a.lat_deg, "a_lon_deg": a.lon_deg,
            "b_lat_deg": b.lat_deg, "b_lon_deg": b.lon_deg,
            "a_point": a.point, "b_point": b.point,
            "dlat_deg": geom["dlat_deg"], "dlon_deg": geom["dlon_deg"],
        }

    # R8 - coincident points. The distance is a perfectly good zero; the
    # direction does not exist, so it is refused rather than reported as 0.
    if geom["bearing_deg"] is None:
        return Refusal(
            reason=(
                f"{a.name} and {b.name} are at the same location in the declared CRS, so "
                "the bearing between them does not exist. The distance is zero and is "
                "returned normally"
            ),
            needed=("two distinct locations",),
            source=NO_CITATION,
        )

    assumptions.update({
        "bearing_reference": reference,
        "bearing_sense": "clockwise",
        "bearing_origin": f"at {a.name}, directed toward {b.name}",
        "bearing_range": "[0, 360)",
        "bearing_zero": "north",
    })
    flags = _shared_flags(a, b, frame, geom)
    flags.append(extra_flag)
    return Quantity(geom["bearing_deg"], "deg", method, NO_CITATION,
                    inputs=inputs, assumptions=assumptions, flags=tuple(flags))


def offset_geometry(a: Any, b: Any, *,
                    distance_unit: str = "ft") -> dict[str, Quantity | Refusal] | Refusal:
    """Distance and bearing between two wells from coordinates (#19).

    Returns either a single `Refusal` - the pair failed the frame gate, so
    neither answer exists - or a dict of two typed results:

        {"distance": Quantity, "bearing": Quantity | Refusal}

    `bearing` is individually a `Refusal` in exactly one case: coincident
    locations, where the distance is a good zero and the direction is undefined.
    Every value in the dict is a `Quantity` or a `Refusal`; nothing here is a
    bare float.
    """
    distance = offset_distance(a, b, distance_unit=distance_unit)
    if isinstance(distance, Refusal):
        return distance
    return {"distance": distance, "bearing": offset_bearing(a, b)}

# ---------------------------------------------------------------------------
# 20_structural_dip
# Structural dip from correlated formation-top picks — apparent only.
# ---------------------------------------------------------------------------

# --------------------------------------------------------------------------- #
# Corpus anchors
# --------------------------------------------------------------------------- #

_TEARPOCK = "06-fort-worth-basin/tearpock-bischke-applied-subsurface-geological-mapping"

#: Chap. 2, pp. 17-21. Mechanical contouring: "the slope or angle of dip of the
#: surface being contoured is uniform between points of control". Equal-spaced:
#: "choose closely spaced data and determine the slope or angle of dip between
#: them". And the one validity limit: the data "are not on opposite sides of a
#: nose or on opposite flanks of a fold".
TEARPOCK_CONTOURING = f"{_TEARPOCK}#13"

#: Chap. 6, the RAM projection: "Choose a grid that is 90 deg to the dip of the
#: structure ... so that true length and slope measurements can be made" — the
#: corpus stating, without the word, why an off-dip slope is not the true one.
TEARPOCK_RAM = f"{_TEARPOCK}#75"

#: Chap. 8, p. 378: "we consider any structure with a dip greater than 5 deg as
#: steeply dipping". The only dip threshold the corpus supplies.
TEARPOCK_STEEP = f"{_TEARPOCK}#118"

#: Chap. 12: apparent -> true dip by stereographic projection, by hand, and only
#: with the strike known independently. Not a closed form, not a three-point
#: solution.
TEARPOCK_STEREONET = f"{_TEARPOCK}#202"

#: Chap. 13: the corpus's only utterance of "three-point problem" — named, an
#: answer printed, no procedure. This anchor exists to be cited in a refusal.
TEARPOCK_THREE_POINT = f"{_TEARPOCK}#219"

#: The datum gate, shared with `subsea_convert` (#18) and `datum_resolve` (#15).

# --------------------------------------------------------------------------- #
# Conventions — stated in a table, never inline, and echoed into every result.
# These are invisible downstream when wrong.
# --------------------------------------------------------------------------- #

CONVENTIONS: dict[str, str] = {
    "dip_angle": (
        "degrees from horizontal; 0 = flat, 90 = vertical. Never radians, never a "
        "percentage grade, never ft/mi — the rate is reported separately as "
        "dip_rate_ft_per_mile."
    ),
    "dip_azimuth": (
        "degrees clockwise from true north, 0 <= A < 360, pointing DOWN-dip "
        "(from the shallower pick toward the deeper one)."
    ),
    "strike": (
        "right-hand rule: strike = (dip_azimuth - 90) mod 360, so an observer "
        "facing along the strike azimuth has the dip on their right. Reserved "
        "for the true-dip path; nothing in this module returns a strike today."
    ),
    "depth_sign": (
        "subsea elevation, POSITIVE UPWARD, sea level = 0 — exactly what "
        "subsea_convert returns (-1340 ft for a pick 1340 ft below sea level, "
        "Tearpock p. 61). The shallower pick is the one with the GREATER value."
    ),
    "coordinates": (
        "x_ft east-positive, y_ft north-positive, one projected map system (state "
        "plane / UTM) in feet for every pick. Grid north is assumed equal to true "
        "north; no grid convergence is applied."
    ),
}

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

#: SOURCED. Tearpock Chap. 8 p. 378 (`TEARPOCK_STEEP`). Flag only, never a refusal.
STEEP_DIP_DEG = 5.0

#: HOUSE RULE, not sourced. Scale-free: perpendicular offset over base length.
#: Permitted here and only here because it selects between two REFUSALS and can
#: never influence a returned number — no value escapes the >=3-pick branch.
DEFAULT_COLLINEAR_TOLERANCE_RATIO = 0.01

FT_PER_MILE = 5280.0

#: The datum this tool computes on. Anything else refuses.
REQUIRED_DEPTH_BASIS = "SSTVD"

_REQUIRED_PICK_FIELDS = (
    "well",
    "x_ft",
    "y_ft",
    "sstvd_ft",
    "depth_basis",
    "datum_resolved",
    "depth_reference",
)

_FLAG_NOTES: dict[str, str] = {
    "apparent_dip": (
        "This is the component of dip along the line joining the two picks, not "
        "true dip. True dip is at least this steep and its direction is unknown."
    ),
    "true_dip_requires_three_noncollinear_picks": (
        "Three or more picks not on one line determine the plane, hence true dip "
        "and strike. Two picks never can, at any spacing."
    ),
    "same_flank_not_declared": (
        "Tearpock #13: data used to establish a rate of dip must not lie on "
        "opposite sides of a nose or on opposite flanks of a fold. The caller did "
        "not declare same_flank, so this dip may span a structural axis."
    ),
    "steeply_dipping_gt_5deg": (
        "Tearpock Chap. 8 p. 378: dip greater than 5 deg is steeply dipping for "
        "fault and structure map integration. This fired on an APPARENT dip, so "
        "the true structure is at least this steep."
    ),
    "horizontal_no_dip_direction": (
        "The two picks are at the same subsea elevation: dip is 0 and no down-dip "
        "direction exists. dip_azimuth_deg is None rather than an arbitrary bearing."
    ),
    "all_picks_above_sea_level": (
        "Every pick is above sea level on the positive-up convention. Confirm the "
        "sign: raw TVD passed as SSTVD leaves the dip magnitude intact and flips "
        "the reported down-dip azimuth by 180 degrees."
    ),
}

_METHOD_APPARENT = (
    "apparent dip between two control points — slope angle = arctan(rise/run) on "
    "subsea picks; the rule is Tearpock #13 (mechanical / equal-spaced contouring: "
    "dip determined between adjacent points of control), the arithmetic is the "
    "definition of a slope angle and is not a corpus correlation"
)


# --------------------------------------------------------------------------- #
# Input handling
# --------------------------------------------------------------------------- #


def _number(value: Any, field: str, well: Any) -> float:
    """Coerce a coordinate/elevation. Bad types are programmer error, not data."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"pick {well!r}: {field} must be a number in feet, got {type(value).__name__}"
        )
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"pick {well!r}: {field} is not finite ({value!r})")
    return out


def _normalise_picks(picks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]] | Refusal:
    """Validate and normalise the pick records, or refuse.

    Gate order is deliberate: shape, then datum basis, then datum resolution,
    then reference agreement, then identity. Each refusal names the tool that
    unblocks it.
    """
    if not isinstance(picks, Sequence) or isinstance(picks, (str, bytes)):
        raise ValueError("picks must be a sequence of pick mappings")

    out: list[dict[str, Any]] = []
    for i, pick in enumerate(picks):
        if not isinstance(pick, Mapping):
            raise ValueError(f"pick {i} is not a mapping; got {type(pick).__name__}")
        missing = [f for f in _REQUIRED_PICK_FIELDS if f not in pick]
        if missing:
            return Refusal(
                reason=(
                    f"pick {i} ({pick.get('well', 'unnamed')!r}) is missing "
                    f"{', '.join(missing)}; a dip cannot be computed from a partial pick"
                ),
                needed=tuple(missing),
                source=TEARPOCK_CONTOURING,
            )
        well = pick["well"]
        out.append(
            {
                "well": well,
                "x_ft": _number(pick["x_ft"], "x_ft", well),
                "y_ft": _number(pick["y_ft"], "y_ft", well),
                "sstvd_ft": _number(pick["sstvd_ft"], "sstvd_ft", well),
                "depth_basis": pick["depth_basis"],
                "datum_resolved": pick["datum_resolved"],
                "depth_reference": pick["depth_reference"],
            }
        )

    # --- datum basis: subsea only, never MD and never mixed -----------------
    # Compared case-insensitively. The basis is a label, not a value: "sstvd"
    # and "SSTVD" name the same thing, and refusing one of them is a false
    # refusal that tells the caller to convert a depth already in the right
    # frame. What must never be relaxed is which basis is required.
    wrong_basis = [p for p in out
                   if str(p["depth_basis"]).strip().upper() != REQUIRED_DEPTH_BASIS.upper()]
    if wrong_basis:
        bases = sorted({str(p["depth_basis"]) for p in wrong_basis})
        return Refusal(
            reason=(
                f"dip is computed from subsea true vertical depths; "
                f"{', '.join(repr(p['well']) for p in wrong_basis)} supplied "
                f"depth_basis {bases}. Measured depth carries hole deviation and "
                f"TVD carries each well's own elevation, so neither is comparable "
                f"between wells"
            ),
            needed=(
                "md_to_tvd (#17) to convert measured depth to TVD",
                "subsea_convert (#18) to hang TVD on sea level",
                f'depth_basis == "{REQUIRED_DEPTH_BASIS}" on every pick',
            ),
            source=TEARPOCK_DATUM,
        )

    # --- datum resolution: same gate as subsea_convert ----------------------
    unresolved = [p["well"] for p in out if not p["datum_resolved"]]
    if unresolved:
        return Refusal(
            reason=(
                "datum unresolved for "
                f"{', '.join(repr(w) for w in unresolved)}; subsea depth is the "
                "gate everything structural depends on, and an unresolved datum "
                "makes a dip between wells arithmetic on two different zeros"
            ),
            needed=(
                "datum_resolve (#15): KB, GL, DF or TKB elevation and which "
                "reference the depths are hung on",
            ),
            source=TEARPOCK_DATUM,
        )

    # --- one reference across the set ---------------------------------------
    references = sorted({str(p["depth_reference"]) for p in out})
    if len(references) > 1:
        return Refusal(
            reason=(
                f"picks are hung on different depth references {references}; a "
                "KB-versus-GL mix is a constant elevation offset between wells "
                "that reads as dip, and over short well spacing it can invert the "
                "structure"
            ),
            needed=(
                "datum_reconcile (#16) to confirm one reference and return the "
                "correction if there is not",
            ),
            source=TEARPOCK_DATUM,
        )

    # --- identity -------------------------------------------------------------
    seen_wells: dict[Any, int] = {}
    for p in out:
        if p["well"] in seen_wells:
            return Refusal(
                reason=(
                    f"well {p['well']!r} appears twice in the pick set; a well "
                    "cannot dip against itself, and a duplicate signals a merge "
                    "defect upstream"
                ),
                needed=("one pick per well",),
                source=TEARPOCK_CONTOURING,
            )
        seen_wells[p["well"]] = 1

    for i in range(len(out)):
        for j in range(i + 1, len(out)):
            if out[i]["x_ft"] == out[j]["x_ft"] and out[i]["y_ft"] == out[j]["y_ft"]:
                return Refusal(
                    reason=(
                        f"{out[i]['well']!r} and {out[j]['well']!r} sit at the same "
                        "map location; there is no horizontal run and therefore no "
                        "dip direction. A depth difference at one location is a "
                        "section thickness or a datum error, not a dip"
                    ),
                    needed=("distinct surveyed surface locations for the picks",),
                    source=TEARPOCK_CONTOURING,
                )

    return out


def _bearing_deg(dx_east: float, dy_north: float) -> float:
    """Compass bearing of a map vector: degrees clockwise from north, 0-360.

    Private on purpose. `offset_geometry` (#19) owns distance and bearing between
    wells; on merge into tools/geometry.py this collapses into that one
    implementation. Two independent distance calculations in one module is the
    "two internally-correct answers that disagree" failure.
    """
    return math.degrees(math.atan2(dx_east, dy_north)) % 360.0


def _run_ft(a: Mapping[str, Any], b: Mapping[str, Any]) -> float:
    return math.hypot(b["x_ft"] - a["x_ft"], b["y_ft"] - a["y_ft"])


# --------------------------------------------------------------------------- #
# Two picks -> apparent dip
# --------------------------------------------------------------------------- #


def apparent_dip_two_picks(
    pick_a: Mapping[str, Any],
    pick_b: Mapping[str, Any],
    *,
    same_flank: bool | None = None,
) -> Quantity | Refusal:
    """Apparent dip between two correlated subsea picks.

    The returned angle is the component of dip along the line joining the two
    wells and nothing more. It is flagged `apparent_dip`, and the flag notes name
    what would make it true.

    `same_flank` is tri-state per Tearpock #13: True (caller asserts both picks
    are on the same structural flank), False (refuse — the source forbids it),
    None (compute, and flag that the assumption is undeclared).
    """
    normalised = _normalise_picks([pick_a, pick_b])
    if isinstance(normalised, Refusal):
        return normalised
    a, b = normalised

    if same_flank is False:
        return Refusal(
            reason=(
                f"{a['well']!r} and {b['well']!r} are declared to be on opposite "
                "flanks. Tearpock #13: the data used to establish the slope or "
                "rate of dip must not be on opposite sides of a nose or on "
                "opposite flanks of a fold — a dip across a structural axis is an "
                "average of two dips that point in different directions"
            ),
            needed=(
                "two picks on the same structural flank",
                "or a third, non-collinear pick and a published three-point method",
            ),
            source=TEARPOCK_CONTOURING,
        )

    run = _run_ft(a, b)  # > 0: coincident locations already refused

    if a["sstvd_ft"] >= b["sstvd_ft"]:
        shallow, deep = a, b
    else:
        shallow, deep = b, a
    rise = shallow["sstvd_ft"] - deep["sstvd_ft"]  # >= 0 by construction

    dip_deg = math.degrees(math.atan2(rise, run))
    dip_rate = rise / run * FT_PER_MILE

    if rise == 0.0:
        azimuth: float | None = None
    else:
        azimuth = _bearing_deg(
            deep["x_ft"] - shallow["x_ft"], deep["y_ft"] - shallow["y_ft"]
        )

    flags = ["apparent_dip", "true_dip_requires_three_noncollinear_picks"]
    if same_flank is None:
        flags.append("same_flank_not_declared")
    if dip_deg > STEEP_DIP_DEG:
        flags.append("steeply_dipping_gt_5deg")
    if rise == 0.0:
        flags.append("horizontal_no_dip_direction")
    if a["sstvd_ft"] > 0.0 and b["sstvd_ft"] > 0.0:
        flags.append("all_picks_above_sea_level")

    return Quantity(
        dip_deg,
        "deg",
        _METHOD_APPARENT,
        TEARPOCK_CONTOURING,
        inputs={
            "wells": (a["well"], b["well"]),
            "shallow_well": shallow["well"],
            "deep_well": deep["well"],
            "sstvd_shallow_ft": shallow["sstvd_ft"],
            "sstvd_deep_ft": deep["sstvd_ft"],
            "run_ft": run,
            "rise_ft": rise,
            "dip_azimuth_deg": azimuth,
            "dip_rate_ft_per_mile": dip_rate,
        },
        assumptions={
            "dip_is_apparent": True,
            "apparent_dip_is_along_bearing_deg": azimuth,
            "depth_basis": REQUIRED_DEPTH_BASIS,
            "depth_reference": a["depth_reference"],
            "same_flank": same_flank,
            "steep_dip_threshold_deg": STEEP_DIP_DEG,
            "steep_dip_threshold_source": TEARPOCK_STEEP,
            "conventions": dict(CONVENTIONS),
            "flag_notes": {f: _FLAG_NOTES[f] for f in flags},
            "corroborating_source": TEARPOCK_RAM,
        },
        flags=tuple(flags),
    )


# --------------------------------------------------------------------------- #
# Three or more picks -> refusal (no published method; collinear cannot work)
# --------------------------------------------------------------------------- #


def _collinearity(
    picks: Sequence[Mapping[str, Any]],
) -> tuple[float, float, float, tuple[Any, Any], Any]:
    """(base_ft, max_offset_ft, ratio, base_wells, offset_well) in map view.

    Base is the widest-separated pair; offset is the largest perpendicular
    distance of any other pick from that line, h = 2 * |triangle area| / base.
    """
    base = 0.0
    base_pair: tuple[Mapping[str, Any], Mapping[str, Any]] = (picks[0], picks[1])
    for i in range(len(picks)):
        for j in range(i + 1, len(picks)):
            d = _run_ft(picks[i], picks[j])
            if d > base:
                base, base_pair = d, (picks[i], picks[j])

    p, q = base_pair
    ux, uy = q["x_ft"] - p["x_ft"], q["y_ft"] - p["y_ft"]
    max_offset, offset_well = 0.0, None
    for r in picks:
        if r is p or r is q:
            continue
        cross = abs(ux * (r["y_ft"] - p["y_ft"]) - uy * (r["x_ft"] - p["x_ft"]))
        h = cross / base
        if h > max_offset:
            max_offset, offset_well = h, r["well"]

    return base, max_offset, max_offset / base, (p["well"], q["well"]), offset_well


def true_dip_from_picks(
    picks: Sequence[Mapping[str, Any]],
    *,
    collinear_tolerance_ratio: float = DEFAULT_COLLINEAR_TOLERANCE_RATIO,
) -> Refusal:
    """True dip and strike from three or more picks — always a `Refusal`.

    The return type is `Refusal` and not `Quantity | Refusal` on purpose: the
    absence of a method should be visible at the call site, not buried in a
    comment. Two distinct refusals, because they have different remedies —
    collinear picks cannot be fixed by finding a source, and a source cannot be
    substituted for a well off the section line.
    """
    normalised = _normalise_picks(picks)
    if isinstance(normalised, Refusal):
        return normalised

    if len(normalised) < 3:
        return Refusal(
            reason=(
                f"{len(normalised)} pick(s) cannot determine a plane; true dip and "
                "strike need three picks that are not on one line"
            ),
            needed=("three or more non-collinear correlated picks",),
            source=TEARPOCK_CONTOURING,
        )

    base, offset, ratio, base_wells, offset_well = _collinearity(normalised)
    if ratio < collinear_tolerance_ratio:
        return Refusal(
            reason=(
                f"the {len(normalised)} picks are collinear in map view "
                f"(largest perpendicular offset {offset:.1f} ft over a "
                f"{base:.1f} ft base, ratio {ratio:.4f} < "
                f"{collinear_tolerance_ratio}); wells on one section line sample "
                "one direction only, so no number of them determines a plane. "
                "Fitting one here would return a large, precise and meaningless "
                "dip azimuth. Apparent dip along the section line is available "
                "from apparent_dip_two_picks"
            ),
            needed=(
                "a pick from a well off the line joining "
                f"{base_wells[0]!r} and {base_wells[1]!r}",
                "or accept apparent dip along the section line via "
                "apparent_dip_two_picks / structural_dip with two picks",
            ),
            source=TEARPOCK_CONTOURING,
        )

    return Refusal(
        reason=(
            "three non-collinear picks do determine true dip and strike — the "
            "three-point problem — but no corpus document publishes the method. "
            f"{TEARPOCK_THREE_POINT} names it and prints one answer ('results in "
            "an average bed dip of 42 deg') with no procedure and no inputs; "
            f"{TEARPOCK_STEREONET} converts apparent to true dip graphically on a "
            "stereonet and needs the strike known independently; every other dip "
            "expression in the corpus (TST = TVT cos phi, the 3D TVT correction, "
            "Eq. 6-2, throw = AB sin theta) takes dip as an input. Inventing the "
            "construction here would be an unsourced equation presented as a "
            "structural fact"
        ),
        needed=(
            "a corpus source publishing the three-point construction "
            "(plane through three points -> dip magnitude, dip azimuth, strike)",
            "or a measured dip: a dipmeter log, or a completed structure map "
            "(Tearpock: formation dip is 'obtained from a dip meter log or a "
            "completed structure map')",
            "meanwhile: apparent dip between any two of these picks, via "
            "apparent_dip_two_picks",
        ),
        source=TEARPOCK_THREE_POINT,
    )


# --------------------------------------------------------------------------- #
# Catalog entry point
# --------------------------------------------------------------------------- #


def structural_dip(
    picks: Sequence[Mapping[str, Any]],
    *,
    same_flank: bool | None = None,
    collinear_tolerance_ratio: float = DEFAULT_COLLINEAR_TOLERANCE_RATIO,
) -> Quantity | Refusal:
    """Dip of a correlated horizon from two or more subsea picks.

    Two picks -> **apparent** dip along the line joining them, flagged as such.
    Three or more -> the true-dip path, which refuses: collinear picks on
    collinearity, non-collinear picks because the three-point method is not in
    the corpus.

    Each pick is a mapping with `well`, `x_ft`, `y_ft`, `sstvd_ft`,
    `depth_basis` (`"SSTVD"`), `datum_resolved` and `depth_reference`.
    """
    if not isinstance(picks, Sequence) or isinstance(picks, (str, bytes)):
        raise ValueError("picks must be a sequence of pick mappings")

    if len(picks) < 2:
        return Refusal(
            reason=(
                f"{len(picks)} pick(s) supplied; a dip needs at least two points "
                "of control — one pick is a point and has no slope"
            ),
            needed=("at least two correlated picks on the same horizon",),
            source=TEARPOCK_CONTOURING,
        )

    if len(picks) == 2:
        return apparent_dip_two_picks(picks[0], picks[1], same_flank=same_flank)

    return true_dip_from_picks(
        picks, collinear_tolerance_ratio=collinear_tolerance_ratio
    )
