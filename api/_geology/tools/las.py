"""LAS file ingest: parse, validate, inventory.

Three tools that share one subject, so they share one module. The corpus
describes LAS **2.0** and nothing else (`02-las-format/kgs-las-2.0-field-table#1`,
`usgs-las-format`), and the CWLS specification itself is not held, which is the
fact that shapes all three:

- `las_parse` is deliberately tolerant. It parses 3.0 under the sourced rule that
  a 2.0 reader ignores 3.0 data items, parses 1.2 best-effort behind a flag, and
  records everything else as a deviation rather than raising. A file it cannot
  read at all is a `Refusal`, not an exception.
- `las_validate` is deliberately strict, and the divergence is intentional:
  parsing wants to recover what is there, validating wants to say what is wrong.
  Every check carries whether its rule came from the corpus or is a house rule,
  and the quality score is labelled owned because no source scores a file.
- `curve_inventory` will not guess whether its values have been scrubbed of
  undeclared null sentinels. `values_are_scrubbed` is keyword-only with no
  default, because either default silently produces a plausible wrong null
  fraction: -999.25 and -9999 are both "common" per the source, so the declared
  NULL alone never settles it.

`WRAP=YES` refuses the data section and keeps the header. No source in the corpus
defines the wrapped continuation layout, and guessing it assigns real numbers to
the wrong curves.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import dataclass, field, replace
from statistics import median
from typing import Any
from typing import Any, Iterable, Mapping, Sequence
import math
import os
import re

from .result import Quantity, Range, Refusal
from .result import Quantity, Range, Refusal  # noqa: F401  (Quantity re-exported for the module)
from .result import Quantity, Range, Refusal  # noqa: F401  (Range unused; imported per house convention)

# ---------------------------------------------------------------------------
# 01_las_parse
# LAS file reading. Destination module: tools/las.py.
# ---------------------------------------------------------------------------

KGS_LAS20 = "02-las-format/kgs-las-2.0-field-table#1"
USGS_LAS = "02-las-format/usgs-las-format#1"

# kgs#1 names the sections by their one-letter form and their long form
# ('"~V" (also known as "~VERSION INFORMATION SECTION")'), so the letter after the
# tilde identifies the section.
LAS20_SECTIONS: dict[str, str] = {
    "V": "version",
    "W": "well",
    "C": "curve",
    "P": "parameter",
    "O": "other",
    "A": "ascii",
}
# The long names kgs#1 gives for each. Matching on the whole first word rather
# than on the initial letter matters for LAS 3.0, whose extra sections include
# ~Core_Data and ~Perforations: on a first-letter rule those would be read as ~C
# curve definitions and ~P parameters and would silently corrupt both.
LAS20_SECTION_NAMES: dict[str, str] = {
    "V": "VERSION",
    "W": "WELL",
    "C": "CURVE",
    "P": "PARAMETER",
    "O": "OTHER",
    "A": "ASCII",
}
# kgs#1: ~V, ~W, ~C and ~A are "a required section"; ~P and ~O are "an optional
# section".
LAS20_REQUIRED_SECTIONS: tuple[str, ...] = ("V", "W", "C", "A")

# Abbreviations real writers use that are neither the letter nor a prefix/extension
# of the long name, so the two rules in `_section_letter` both miss them. `~Params`
# is the observed case: "PARAMETER".startswith("PARAMS") is False and so is the
# reverse, so the whole parameter block was landing in `unknown_sections` and
# RM/RMF/RMT/RMBH/BHT/BS/CSGS were unreachable through the typed API. Both LAS
# fixtures head their parameter block that way — a 1983 Dresser Atlas log and a
# 2013 Pioneer log, 30 years and two service companies apart, so it is the
# convention rather than one vendor's quirk.
#
# Kept as an explicit table rather than relaxing to a first-letter rule, which is
# what the docstring below warns against: a first-letter rule would swallow LAS
# 3.0's ~Perforations and ~Core_Data as parameter and curve blocks.
LAS20_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "P": ("PARAMS", "PARAM"),
}

# kgs#1, "required fields in the ~Version information section".
LAS20_REQUIRED_VERSION_MNEMONICS: tuple[str, ...] = ("VERS", "WRAP")

# kgs#1, "required fields in the ~Well Information Section". Exported for
# las_validate to score against; las_parse only reports the ones it needs to do
# its own job, because judging completeness is that tool's role, not this one's.
LAS20_REQUIRED_WELL_MNEMONICS: tuple[str, ...] = (
    "STRT", "STOP", "STEP", "NULL", "COMP", "WELL", "FLD", "LOC", "PROV",
    "CTRY", "STAT", "CNTY", "UWI", "API", "SRVC", "LIC", "DATE",
)

# kgs#1 lists these verbatim as the common null values. Recorded for provenance
# only - this tool never applies them; see null_scrub.
LAS20_COMMON_NULLS: tuple[float, ...] = (-999.25, -9999.0)

_VERSION_SUPPORT = {
    "2.0": "described",
    "3.0": "backward-compatible",
}


@dataclass(frozen=True)
class ParseDeviation:
    """Something in the file that departs from LAS 2.0, or from what we assumed.

    `source` is the corpus anchor for the rule that was broken. An **empty**
    `source` means this parser's own house rule, not a published requirement -
    a distinction las_validate needs before it scores anything.
    """

    code: str
    message: str
    line_no: int | None = None
    raw: str = ""
    count: int = 1
    source: str = ""


@dataclass(frozen=True)
class HeaderLine:
    """One parsed `MNEM .UNIT VALUE : DESCRIPTION` line, with its raw text."""

    mnemonic: str
    unit: str
    value: str
    description: str
    raw: str
    line_no: int
    section: str


@dataclass(frozen=True)
class CurveDef:
    """One ~C entry. `column_index` is its position in the data section.

    kgs#1: ~C "contains curve mnemonics and their definitions in the order that
    they appear in the data section", so position is meaning, not decoration.
    """

    mnemonic: str
    unit: str
    value: str
    description: str
    raw: str
    line_no: int
    column_index: int


@dataclass(frozen=True)
class LasFile:
    """A parsed LAS file: header, curve definitions, parameters and data, apart.

    Not a Quantity - this is a document, not a measurement. It carries its own
    provenance instead: where it came from, how it was decoded, what the file
    declared, and every deviation noticed on the way through.
    """

    path: str
    encoding: str
    source: str
    method: str
    vers: str | None
    wrap: str | None
    version_support: str
    null_value: float | None
    null_raw: str
    version_info: tuple[HeaderLine, ...] = ()
    well: tuple[HeaderLine, ...] = ()
    curves: tuple[CurveDef, ...] = ()
    parameters: tuple[HeaderLine, ...] = ()
    other: tuple[str, ...] = ()
    unknown_sections: dict[str, tuple[str, ...]] = field(default_factory=dict)
    columns: tuple[tuple[float, ...], ...] = ()
    section_order: tuple[str, ...] = ()
    deviations: tuple[ParseDeviation, ...] = ()
    flags: tuple[str, ...] = ()
    data_refusal: Refusal | None = None
    # The caller's depth unit, carried from las_parse(). Used by nothing except
    # declared_depth_range(), and there only when ~W carries no unit on
    # STRT/STOP - the tool never infers feet-versus-metres from the numbers.
    assume_depth_unit: str | None = None

    # -- accessors -------------------------------------------------------

    @property
    def mnemonics(self) -> tuple[str, ...]:
        return tuple(c.mnemonic for c in self.curves)

    @property
    def deviation_codes(self) -> tuple[str, ...]:
        return tuple(d.code for d in self.deviations)

    @property
    def n_rows(self) -> int:
        return len(self.columns[0]) if self.columns else 0

    @property
    def index_mnemonic(self) -> str | None:
        """kgs#1: "The index values always appear in the first column"."""
        return self.curves[0].mnemonic if self.curves else None

    @property
    def index_values(self) -> tuple[float, ...]:
        return self.columns[0] if self.columns else ()

    def column(self, mnemonic: str) -> tuple[float, ...]:
        """The data array for a curve. Exact match first, then case-insensitive.

        Case folding is not mnemonic normalization - GR and gr are the same
        mnemonic typed differently. Anything semantic is mnemonic_normalize's job.
        Duplicated mnemonics resolve to the first; go by column index for the rest.
        """
        for c in self.curves:
            if c.mnemonic == mnemonic and c.column_index < len(self.columns):
                return self.columns[c.column_index]
        want = mnemonic.strip().upper()
        for c in self.curves:
            if c.mnemonic.upper() == want and c.column_index < len(self.columns):
                return self.columns[c.column_index]
        raise KeyError(
            f"no column {mnemonic!r} in {self.path}; present: {list(self.mnemonics)}"
            + (" (data section refused - see data_refusal)" if self.data_refusal else "")
        )

    def header_value(self, mnemonic: str, section: str | None = None) -> str | None:
        """Raw string value of a header mnemonic, unconverted. None if absent.

        ~W and ~P can carry the same mnemonic, so `section` ("version" | "well" |
        "parameter") disambiguates. Search order without it is ~V, ~W, ~P.
        """
        want = mnemonic.strip().upper()
        blocks = {"version": self.version_info, "well": self.well,
                  "parameter": self.parameters}
        order = [section] if section else ["version", "well", "parameter"]
        for name in order:
            if name not in blocks:
                raise ValueError(f"unknown header section {name!r}; known: {sorted(blocks)}")
            for line in blocks[name]:
                if line.mnemonic.upper() == want:
                    return line.value
        return None

    def declared_depth_range(self, assume_unit: str | None = None):
        """STRT..STOP as declared in ~W. A Range, because it is a physical band.

        Declared, not measured: this reports what the header says, and says so in
        `method`. Comparing it against the data is las_validate's job. Refuses
        rather than assume feet when ~W carries no unit - metric LAS files exist
        and a silent factor of 3.28 in depth is not recoverable downstream.
        """
        strt = self._numeric_well("STRT")
        stop = self._numeric_well("STOP")
        if strt is None or stop is None:
            return Refusal(
                reason="~W does not declare a numeric STRT and STOP, so the file "
                       "states no depth range",
                needed=("STRT and STOP in the ~W section (kgs#1 lists both as required)",),
                source=KGS_LAS20,
            )
        unit = ""
        for line in self.well:
            if line.mnemonic.upper() == "STRT":
                unit = line.unit.strip()
        unit = unit or assume_unit or self.assume_depth_unit or ""
        if not unit:
            return Refusal(
                reason="STRT/STOP carry no unit; feet and metres are not "
                       "distinguishable from the numbers alone",
                needed=("a unit on STRT in ~W, or an explicit assume_unit from the caller",),
                source=KGS_LAS20,
            )
        members = {"STRT": strt, "STOP": stop}
        step = self._numeric_well("STEP")
        if step is not None:
            members["STEP"] = step
        return Range(
            low=min(strt, stop), high=max(strt, stop), unit=unit,
            method="depth range as declared in the ~W section (STRT/STOP); "
                   "declared, not measured from the data",
            source=KGS_LAS20, members=members,
        )

    def _numeric_well(self, mnemonic: str) -> float | None:
        raw = self.header_value(mnemonic, "well")
        if raw is None:
            return None
        try:
            return float(raw.strip())
        except ValueError:
            return None


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------


def las_parse(path: str, *, assume_depth_unit: str | None = None):
    """Read a LAS file into header, curve definitions, parameters and data arrays.

    Returns a `LasFile`, or a `Refusal` when the bytes are not LAS at all. A path
    that does not exist raises FileNotFoundError: that is programmer error, not a
    condition the source declines to cover.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"no LAS file at {path!r}")
    with open(path, "rb") as fh:
        blob = fh.read()
    text, encoding, seed = _decode(blob)
    return parse_las_text(text, source_name=path, encoding=encoding,
                          seed_deviations=seed, assume_depth_unit=assume_depth_unit)


def parse_las_text(text: str, source_name: str = "<string>", *,
                   encoding: str = "utf-8",
                   seed_deviations: tuple[ParseDeviation, ...] = (),
                   assume_depth_unit: str | None = None):
    """Same parse, over content already in memory (an upload, a stream)."""
    dev: list[ParseDeviation] = list(seed_deviations)
    flags: list[str] = []

    lines = text.splitlines()
    if not any(ln.lstrip().startswith("~") for ln in lines):
        return Refusal(
            reason=f"{source_name}: no line begins with '~', so the file has no LAS "
                   "section structure and cannot be read as LAS",
            needed=("a file with LAS section headers ~V ~W ~C ~A (kgs#1)",),
            source=KGS_LAS20,
        )

    sections, order, preamble = _split_sections(lines)
    present = set(order)
    if not ({"V", "W", "C"} & present):
        return Refusal(
            reason=f"{source_name}: has section markers but none of the required LAS "
                   "2.0 sections ~V, ~W or ~C; its lines cannot be attributed to LAS "
                   "sections",
            needed=("a file containing ~V, ~W and ~C (kgs#1 lists all three as required)",),
            source=KGS_LAS20,
        )
    if preamble:
        dev.append(ParseDeviation(
            "CONTENT_BEFORE_FIRST_SECTION",
            f"{len(preamble)} non-blank line(s) precede the first ~ section",
            line_no=preamble[0][0], raw=preamble[0][1], count=len(preamble),
            source=KGS_LAS20,
        ))
    for letter in LAS20_REQUIRED_SECTIONS:
        if letter not in present:
            dev.append(ParseDeviation(
                "MISSING_SECTION",
                f"required section ~{letter} ({LAS20_SECTIONS[letter]}) is absent",
                source=KGS_LAS20,
            ))
    if order and order[0] != "V":
        dev.append(ParseDeviation(
            "VERSION_SECTION_NOT_FIRST",
            f"~V must be the first section; first section is ~{order[0]}",
            source=KGS_LAS20,
        ))
    if "A" in order and order[-1] != "A":
        after = [s for s in order[order.index("A") + 1:]]
        dev.append(ParseDeviation(
            "SECTION_AFTER_DATA",
            "~A must be the last section in the file; these follow it and were not "
            f"interpreted: {after}",
            source=KGS_LAS20,
        ))

    version_info = _parse_block(sections.get("V", []), "version", dev)
    well = _parse_block(sections.get("W", []), "well", dev)
    parameters = _parse_block(sections.get("P", []), "parameter", dev)
    curve_lines = _parse_block(sections.get("C", []), "curve", dev)
    curves = tuple(
        CurveDef(h.mnemonic, h.unit, h.value, h.description, h.raw, h.line_no, i)
        for i, h in enumerate(curve_lines)
    )
    _report_duplicates(curves, dev)
    other = tuple(raw for _, raw in sections.get("O", []))

    unknown: dict[str, tuple[str, ...]] = {}
    for name, rows in sections.get("_unknown", {}).items():  # type: ignore[union-attr]
        unknown[name] = tuple(raw for _, raw in rows)

    vers, wrap = _version_fields(version_info, dev)
    support = _VERSION_SUPPORT.get(vers or "", "undescribed")
    if support == "backward-compatible":
        flags.append(
            "VERS 3.0 read with LAS 2.0 rules; usgs-las-format#1 states a 2.0 reader "
            "should ignore 3.0 data items, so 3.0-only sections were retained raw and "
            "not interpreted"
        )
    elif vers != "2.0":
        shown = f"VERS {vers}" if vers else "no VERS"
        flags.append(
            f"{shown}: no corpus source describes this version; parsed with LAS 2.0 "
            "rules, and any version-specific syntax will be reported as a LAS 2.0 "
            "deviation rather than understood"
        )
        dev.append(ParseDeviation(
            "UNDESCRIBED_VERSION",
            f"{shown}; the corpus describes LAS 2.0 only",
            source=USGS_LAS,
        ))
    if unknown:
        dev.append(ParseDeviation(
            "UNKNOWN_SECTION",
            "section(s) outside the LAS 2.0 set ~V ~W ~C ~P ~O ~A retained raw and "
            f"not interpreted: {sorted(unknown)}",
            count=len(unknown), source=USGS_LAS,
        ))

    null_raw = ""
    null_value = None
    for line in well:
        if line.mnemonic.upper() == "NULL":
            null_raw = line.value
            try:
                null_value = float(line.value.strip())
            except ValueError:
                dev.append(ParseDeviation(
                    "UNPARSEABLE_NULL", f"NULL value {line.value!r} is not a number",
                    line_no=line.line_no, raw=line.raw, source=KGS_LAS20))
            break
    else:
        dev.append(ParseDeviation(
            "MISSING_REQUIRED_WELL_MNEMONIC",
            "~W does not declare NULL; downstream null handling has no declared "
            "sentinel to start from",
            source=KGS_LAS20))
    if null_value is not None:
        flags.append(
            f"declared NULL {null_value} is carried, not applied; undeclared sentinels "
            "are common, so run null_scrub before trusting any array"
        )

    data_rows = sections.get("A", [])
    columns, data_refusal = _parse_data(data_rows, curves, wrap, dev)
    if data_refusal is not None:
        flags.append("data section not decoded - see data_refusal")

    return LasFile(
        path=source_name,
        encoding=encoding,
        source=KGS_LAS20,
        method="LAS 2.0 section parse (kgs-las-2.0-field-table#1)",
        vers=vers,
        wrap=wrap,
        version_support=support,
        null_value=null_value,
        null_raw=null_raw,
        version_info=version_info,
        well=well,
        curves=curves,
        parameters=parameters,
        other=other,
        unknown_sections=unknown,
        columns=columns,
        section_order=tuple(order),
        deviations=tuple(dev),
        flags=tuple(flags),
        data_refusal=data_refusal,
        assume_depth_unit=assume_depth_unit,
    )


# ---------------------------------------------------------------------------
# internals
# ---------------------------------------------------------------------------


def _decode(blob: bytes) -> tuple[str, str, tuple[ParseDeviation, ...]]:
    """UTF-8, falling back to Latin-1. Vintage files are rarely UTF-8."""
    dev: list[ParseDeviation] = []
    if blob.startswith(b"\xef\xbb\xbf"):
        blob = blob[3:]
        dev.append(ParseDeviation(
            "BYTE_ORDER_MARK",
            "file begins with a UTF-8 BOM, which displaces the required '~V must be "
            "the first section'; stripped before parsing",
            source=KGS_LAS20))
    try:
        return blob.decode("utf-8"), "utf-8", tuple(dev)
    except UnicodeDecodeError:
        dev.append(ParseDeviation(
            "NOT_UTF8", "file is not valid UTF-8; decoded as latin-1"))
        return blob.decode("latin-1"), "latin-1", tuple(dev)


def _section_letter(body: str) -> str | None:
    """Which LAS 2.0 section a `~...` line opens, or None if it is not one.

    kgs#1 gives both forms ('"~V" (also known as "~VERSION INFORMATION SECTION")'),
    so the first word must be either the letter itself or the section's long name.
    A first-letter rule would swallow LAS 3.0's ~Core_Data and ~Perforations as
    curve and parameter blocks.
    """
    if not body:
        return None
    word = body.split()[0].split("|")[0].strip().upper()
    if not word:
        return None
    for letter, name in LAS20_SECTION_NAMES.items():
        if word == letter or name.startswith(word) or word.startswith(name):
            return letter
    for letter, aliases in LAS20_SECTION_ALIASES.items():
        if word in aliases:
            return letter
    return None


def _split_sections(lines: list[str]):
    """Bucket lines by section letter, preserving line numbers and raw text."""
    sections: dict[Any, Any] = {}
    unknown: dict[str, list[tuple[int, str]]] = {}
    order: list[str] = []
    preamble: list[tuple[int, str]] = []
    current: str | None = None
    current_unknown: str | None = None

    for i, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            # House rule: the corpus never mentions comments, but real files carry
            # them and treating a comment as a header line would invent a mnemonic.
            continue
        if stripped.startswith("~"):
            body = stripped[1:].strip()
            letter = _section_letter(body)
            if letter is not None:
                current, current_unknown = letter, None
                order.append(letter)
                sections.setdefault(letter, [])
            else:
                name = body or "~"
                current, current_unknown = None, name
                unknown.setdefault(name, [])
            continue
        if current is not None:
            sections[current].append((i, raw.rstrip()))
        elif current_unknown is not None:
            unknown[current_unknown].append((i, raw.rstrip()))
        else:
            preamble.append((i, raw.rstrip()))
    if unknown:
        sections["_unknown"] = unknown
    return sections, order, preamble


def _parse_block(rows: list[tuple[int, str]], section: str,
                 dev: list[ParseDeviation]) -> tuple[HeaderLine, ...]:
    out: list[HeaderLine] = []
    malformed: list[tuple[int, str]] = []
    for line_no, raw in rows:
        parsed = _parse_header_line(raw, line_no, section)
        if parsed is None:
            malformed.append((line_no, raw))
            continue
        out.append(parsed)
    if malformed:
        dev.append(ParseDeviation(
            "MALFORMED_HEADER_LINE",
            f"{len(malformed)} line(s) in the ~{section[0].upper()} section carry no "
            "'.' delimiter and could not be read as MNEM.UNIT VALUE : DESCRIPTION",
            line_no=malformed[0][0], raw=malformed[0][1], count=len(malformed),
            source=KGS_LAS20))
    return tuple(out)


def _parse_header_line(raw: str, line_no: int, section: str) -> HeaderLine | None:
    """Split `MNEM .UNIT VALUE : DESCRIPTION` per the kgs#1 four-column table.

    House rule, stated in the spec: the mnemonic ends at the *first* dot and the
    description begins at the *last* colon. The corpus prints the four-column
    layout but not the delimiter discipline, and the CWLS spec is not held. Last
    colon is what keeps `TIME. 08:30:00 : Time logged` intact.
    """
    body = raw.strip()
    dot = body.find(".")
    if dot < 0:
        return None
    mnemonic = body[:dot].strip()
    rest = body[dot + 1:]
    colon = rest.rfind(":")
    if colon < 0:
        middle, description = rest, ""
    else:
        middle, description = rest[:colon], rest[colon + 1:].strip()
    if middle and not middle[0].isspace():
        parts = middle.split(None, 1)
        unit = parts[0]
        value = parts[1].strip() if len(parts) > 1 else ""
    else:
        unit = ""
        value = middle.strip()
    return HeaderLine(mnemonic=mnemonic, unit=unit, value=value,
                      description=description, raw=raw.rstrip(), line_no=line_no,
                      section=section)


def _report_duplicates(curves: tuple[CurveDef, ...], dev: list[ParseDeviation]) -> None:
    seen: dict[str, int] = {}
    dupes: list[CurveDef] = []
    for c in curves:
        key = c.mnemonic.upper()
        if key in seen:
            dupes.append(c)
        seen[key] = c.column_index
    if dupes:
        dev.append(ParseDeviation(
            "DUPLICATE_MNEMONIC",
            "curve mnemonic(s) repeated in ~C: "
            f"{sorted({c.mnemonic for c in dupes})}; every column is kept, but "
            "column(mnemonic) resolves to the first",
            line_no=dupes[0].line_no, raw=dupes[0].raw, count=len(dupes)))


def _version_fields(version_info: tuple[HeaderLine, ...],
                    dev: list[ParseDeviation]) -> tuple[str | None, str | None]:
    found: dict[str, HeaderLine] = {}
    for line in version_info:
        found.setdefault(line.mnemonic.upper(), line)
    for mnem in LAS20_REQUIRED_VERSION_MNEMONICS:
        if mnem not in found:
            dev.append(ParseDeviation(
                "MISSING_REQUIRED_VERSION_MNEMONIC",
                f"~V does not declare {mnem}, which kgs#1 lists as required",
                source=KGS_LAS20))
    vers = found["VERS"].value.strip() if "VERS" in found else None
    # Reported verbatim, per the spec's output table ("Declared, verbatim").
    # Case folding happens where WRAP is *compared*, not where it is recorded.
    wrap = found["WRAP"].value.strip() if "WRAP" in found else None
    return (vers or None), (wrap or None)


def _parse_data(rows: list[tuple[int, str]], curves: tuple[CurveDef, ...],
                wrap: str | None, dev: list[ParseDeviation]):
    """~A into one array per column, or a Refusal for the data section alone.

    `wrap` arrives as the file declared it; the mode test is case-insensitive
    because kgs#1 tabulates the value ('WRAP . NO') without stating a case rule.
    """
    declared_wrap, wrap = wrap, (wrap.strip().upper() if wrap else wrap)
    if wrap == "YES":
        return (), Refusal(
            reason="the file declares WRAP=YES, and no corpus source defines the "
                   "wrapped-data layout; decoding it would mean guessing which "
                   "continuation line belongs to which curve. The header was parsed "
                   "and is returned.",
            needed=("the same log in un-wrapped form (WRAP=NO), or the CWLS LAS 2.0 "
                    "specification section on wrap mode added to the corpus",),
            source=KGS_LAS20,
        )
    if wrap is not None and wrap != "NO":
        dev.append(ParseDeviation(
            "WRAP_UNRECOGNIZED", f"WRAP is {declared_wrap!r}, neither YES nor NO",
            source=KGS_LAS20))
        return (), Refusal(
            reason=f"the file declares WRAP={declared_wrap!r}, which is neither the un-wrapped "
                   "mode the corpus defines nor a mode it describes; the data section "
                   "was not decoded",
            needed=("a file declaring WRAP=NO (kgs#1: 'WRAP . NO : One line per depth step')",),
            source=KGS_LAS20,
        )
    if wrap is None:
        dev.append(ParseDeviation(
            "WRAP_ASSUMED_NO",
            "~V declares no WRAP; the data section was read as un-wrapped, one line "
            "per depth step"))
    if not rows:
        return (), None

    expected = len(curves)
    if expected == 0:
        expected = len(rows[0][1].split())
        dev.append(ParseDeviation(
            "NO_CURVE_SECTION",
            f"no ~C section, so columns are unnamed; column count {expected} was taken "
            "from the first data line",
            line_no=rows[0][0], raw=rows[0][1], source=KGS_LAS20))
        if expected == 0:
            return (), None

    kept: list[list[float]] = []
    bad_width: list[tuple[int, str]] = []
    bad_cell: list[tuple[int, str]] = []
    exponent: list[tuple[int, str]] = []

    for line_no, raw in rows:
        tokens = raw.split()
        if len(tokens) != expected:
            bad_width.append((line_no, raw))
            continue
        values: list[float] = []
        for token in tokens:
            try:
                v = float(token)
            except ValueError:
                v = float("nan")
                bad_cell.append((line_no, raw))
            else:
                if "e" in token.lower():
                    exponent.append((line_no, raw))
            values.append(v)
        kept.append(values)

    if bad_width:
        dev.append(ParseDeviation(
            "ROW_WIDTH_MISMATCH",
            f"{len(bad_width)} data line(s) do not carry {expected} values and were "
            "dropped rather than padded, since a padded cell is indistinguishable "
            "from a reading",
            line_no=bad_width[0][0], raw=bad_width[0][1], count=len(bad_width),
            source=KGS_LAS20))
    if bad_cell:
        dev.append(ParseDeviation(
            "UNPARSEABLE_VALUE",
            f"{len(bad_cell)} data cell(s) are not floating point or integer values; "
            "stored as NaN. kgs#1: 'All values in the ASCII log data section must be "
            "floating point or integer (long) values'",
            line_no=bad_cell[0][0], raw=bad_cell[0][1], count=len(bad_cell),
            source=KGS_LAS20))
    if exponent:
        dev.append(ParseDeviation(
            "EXPONENTIAL_VALUE",
            f"{len(exponent)} data cell(s) use exponential notation, which kgs#1 says "
            "is 'not supported'; the values were read anyway",
            line_no=exponent[0][0], raw=exponent[0][1], count=len(exponent),
            source=KGS_LAS20))

    if not kept:
        return (), Refusal(
            reason=f"the ~A section has {len(rows)} data line(s) but not one carries "
                   f"{expected} values, so no row can be mapped onto the {expected} "
                   "curve(s) in ~C. If the file is wrapped, its ~V does not say so.",
            needed=("data lines with one value per ~C curve, or an un-wrapped file",),
            source=KGS_LAS20,
        )
    columns = tuple(tuple(row[i] for row in kept) for i in range(expected))
    return columns, None


__all__ = [
    "las_parse", "parse_las_text", "LasFile", "CurveDef", "HeaderLine", "ParseDeviation",
    "LAS20_SECTIONS", "LAS20_REQUIRED_SECTIONS", "LAS20_REQUIRED_VERSION_MNEMONICS",
    "LAS20_REQUIRED_WELL_MNEMONICS", "LAS20_COMMON_NULLS", "KGS_LAS20", "USGS_LAS",
]

# ---------------------------------------------------------------------------
# 02_las_validate
# LAS 2.0 deviation reporting — tool #2, `las_validate`.
# ---------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Anchors. KGS is the field table; USGS corroborates the required-section list
# and names LAS Certify as the authoritative checker (which this tool is not).
# --------------------------------------------------------------------------
OWNED = ""  # a rule of ours carries no anchor, and that is how it is detected

SPEC = "specs/02-las_validate.md"
SCORE_SOURCE = f"owned: {SPEC} Scoring - not from the corpus"

# The document the corpus references but does not contain. Named in every
# `not_checked` entry so the missing dependency is visible in tool output.
CWLS_SPEC = (
    "CWLS 'LAS Version 2.0: Update July 2009' specification "
    "(referenced in the REFERENCE block of "
    "02-las-format/kgs-las-2.0-field-table#1; not held in this corpus)"
)

PROV_CORPUS = "corpus"
PROV_PARTIAL = "corpus-partial"
PROV_HOUSE = "house"

# --------------------------------------------------------------------------
# Sourced tables. KGS #1, quoted in specs/02-las_validate.md.
# --------------------------------------------------------------------------

# "~V ... is a required section ... must be the first section"
# "~W ... is a required section; ... is preferably the second section"
# "~C ... is a required section"
# "~P ... is an optional section"   "~O ... is an optional section"
# "~A ... is a required section; ... is the last section in the file"
REQUIRED_SECTIONS: tuple[str, ...] = ("V", "W", "C", "A")
OPTIONAL_SECTIONS: tuple[str, ...] = ("P", "O")

# "The following are considered required fields in the ~Version information
# section for the LAS version 2.0 standard": VERS, WRAP.
REQUIRED_V_MNEMONICS: tuple[str, ...] = ("VERS", "WRAP")

# "The following are considered required fields int the ~Well Information
# Section for the LAS version 2.0 standard" - the full field table.
REQUIRED_W_MNEMONICS: tuple[str, ...] = (
    "STRT", "STOP", "STEP", "NULL", "COMP", "WELL", "FLD", "LOC", "PROV",
    "CTRY", "STAT", "CNTY", "UWI", "API", "SRVC", "LIC", "DATE",
)
# The four whose value format the table gives as `nnnn.nn` and which downstream
# numeric tools actually need. Our severity split keys off this set.
NUMERIC_W_MNEMONICS: tuple[str, ...] = ("STRT", "STOP", "STEP", "NULL")

# "Null Value; Common Null Values are -999.25, -9999, etc."  The list is
# sourced; scanning the data for an *undeclared* one is our rule.
COMMON_NULL_SENTINELS: tuple[float, ...] = (-999.25, -9999.0)

# The version this rule set covers. KGS #1 documents LAS 2.0 only, and
# toc/TOC.md:79 marks the document as not good for 1.2 or 3.0 differences.
SUPPORTED_VERSION = "2.0"

# --------------------------------------------------------------------------
# House tables. Ours; no anchor exists for any of these.
# --------------------------------------------------------------------------

# "The index of the data columns is either Depth or Time" (sourced) - but the
# corpus gives no mnemonic list, so this table is ours and the deviation it
# raises is only `info`.
INDEX_MNEMONICS: frozenset[str] = frozenset(
    {"DEPT", "DEPTH", "MD", "TVD", "TIME", "TIM", "ETIM"}
)

# Ours: the `MNEM.UNIT VALUE : DESCRIPTION` shape is implied by the field
# table's column headings, never specified. Applied only outside ~O, which
# "has no formatting requirements".
_HEADER_LINE_RE = re.compile(r"^\s*[^\s.:][^.:]*\.[^:]*:")

# Ours: severity weights and the score's functional form.
SEVERITY_WEIGHT: dict[str, float] = {"error": 1.0, "warning": 0.25, "info": 0.0}

_EXPONENT_RE = re.compile(r"[eEdD]")
_NUMERIC_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)$")


# --------------------------------------------------------------------------
# Result types
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Deviation:
    """One observed departure from one rule, with that rule's provenance.

    `source` is the corpus anchor, and is empty exactly when `provenance` is
    "house". Severity is ours in every case.
    """

    code: str
    message: str
    severity: str            # error | warning | info  (ours)
    provenance: str          # corpus | corpus-partial | house
    source: str = OWNED
    section: str | None = None
    mnemonic: str | None = None
    line_no: int | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.severity not in SEVERITY_WEIGHT:
            raise ValueError(f"unknown severity {self.severity!r}")
        if self.provenance not in (PROV_CORPUS, PROV_PARTIAL, PROV_HOUSE):
            raise ValueError(f"unknown provenance {self.provenance!r}")
        if (self.provenance == PROV_HOUSE) != (not self.source):
            raise ValueError(
                "a house rule must carry no source and a corpus rule must carry one; "
                f"got provenance={self.provenance!r} source={self.source!r}"
            )


@dataclass(frozen=True)
class UncheckedRule:
    """A rule this tool cannot run, and what would unblock it."""

    code: str
    reason: str
    needed: str = CWLS_SPEC


@dataclass(frozen=True)
class ValidationReport:
    """Every deviation, everything left unchecked, and one house score."""

    deviations: tuple[Deviation, ...]
    not_checked: tuple[UncheckedRule, ...]
    quality_score: Quantity
    counts: dict[str, int]
    las_version: str | None
    wrap: str | None
    sections_present: tuple[str, ...]
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()
    # las_parse reports its own deviations (specs/01-las_parse.md "Output").
    # They are carried through verbatim rather than folded in, so the score
    # cannot double-count a problem both tools noticed.
    parser_deviations: tuple[Any, ...] = ()

    @property
    def value(self) -> float:
        """The score, for callers that only want the number."""
        return self.quality_score.value

    def deviations_by_provenance(self) -> dict[str, tuple[Deviation, ...]]:
        return {
            p: tuple(d for d in self.deviations if d.provenance == p)
            for p in (PROV_CORPUS, PROV_PARTIAL, PROV_HOUSE)
        }

    def sourced_deviations(self) -> tuple[Deviation, ...]:
        """Only the deviations whose rule came from the corpus."""
        return tuple(d for d in self.deviations if d.provenance != PROV_HOUSE)


# --------------------------------------------------------------------------
# Adapter over las_parse output. Tolerant by design: a field this tool cannot
# find degrades to a `not_checked` entry, never to a passed check.
# --------------------------------------------------------------------------
_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    # The `vers`/`version_info`/`columns`/`section_order`/`data_refusal` names are
    # las_parse's own, per specs/01-las_parse.md "Output"; the rest are fallbacks
    # so a shape change on merge does not silently pass checks.
    "version": ("vers", "version", "las_version", "version_number"),
    "wrap": ("wrap", "wrapped", "wrap_mode"),
    "sections": ("section_order", "sections", "blocks"),
    "header": ("header", "headers", "sections_by_code"),
    "version_section": ("version_info", "version_section", "version_entries", "vers_section"),
    "well": ("well", "well_section", "well_entries"),
    "curves": ("curves", "curve_section", "curve_entries"),
    "parameters": ("parameters", "parameter_section", "parameter_entries", "params"),
    "other": ("other", "other_section"),
    "data": ("columns", "data", "data_arrays", "arrays", "curves_data"),
    "data_lines": ("data_lines", "ascii_lines", "raw_data_lines"),
    "null_value": ("null_value", "null", "null_val"),
    "data_refusal": ("data_refusal",),
    "parser_deviations": ("deviations",),
}
_ENTRY_ALIASES: dict[str, tuple[str, ...]] = {
    "mnemonic": ("mnemonic", "mnem", "name", "key"),
    "unit": ("unit", "units"),
    "value": ("value", "val", "data"),
    "description": ("description", "descr", "desc", "comment"),
    "raw": ("raw", "raw_line", "line", "text", "source_line"),
    "line_no": ("line_no", "lineno", "line_number", "index"),
}

_SECTION_CODES = {
    "V": "V", "VERSION": "V",
    "W": "W", "WELL": "W",
    "C": "C", "CURVE": "C",
    "P": "P", "PARAMETER": "P", "PARAM": "P",
    "O": "O", "OTHER": "O",
    "A": "A", "ASCII": "A", "DATA": "A",
}

_SECTION_LABEL = {
    "V": "~V (version)", "W": "~W (well)", "C": "~C (curve)",
    "P": "~P (parameter)", "O": "~O (other)", "A": "~A (ascii data)",
}

_MISSING = object()


def _pick(obj: Any, aliases: Iterable[str], default: Any = _MISSING) -> Any:
    """Attribute first, then mapping key, over a list of accepted names."""
    for name in aliases:
        if isinstance(obj, Mapping):
            if name in obj:
                return obj[name]
        else:
            got = getattr(obj, name, _MISSING)
            if got is not _MISSING:
                return got
    return default


def _field(parsed: Any, key: str, default: Any = _MISSING) -> Any:
    return _pick(parsed, _FIELD_ALIASES[key], default)


def _entry_field(entry: Any, key: str, default: Any = None) -> Any:
    if isinstance(entry, str):  # a bare mnemonic string
        return entry if key == "mnemonic" else default
    got = _pick(entry, _ENTRY_ALIASES[key], _MISSING)
    return default if got is _MISSING else got


def _section_code(raw: Any) -> str | None:
    """Normalize a section identifier to one of V W C P O A."""
    if raw is None:
        return None
    if not isinstance(raw, str):
        raw = _pick(raw, ("code", "name", "section", "title"), None)
        if raw is None or not isinstance(raw, str):
            return None
    token = raw.strip().lstrip("~").strip().upper()
    if not token:
        return None
    for key, code in _SECTION_CODES.items():
        if token == key or token.startswith(key):
            return code
    return token[0] if token[0] in "VWCPOA" else None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            out = float(text)
        except ValueError:
            return None
        return out if math.isfinite(out) else None
    return None


def _seq(value: Any) -> list[Any]:
    if value is None or value is _MISSING:
        return []
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, (str, bytes)):
        return []
    if isinstance(value, Sequence):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return []


def _entries_for(parsed: Any, code: str) -> list[Any] | None:
    """Header entries for one section, or None if the parser did not supply them."""
    header = _field(parsed, "header", None)
    if isinstance(header, Mapping):
        for key in (code, code.lower(), f"~{code}", _SECTION_LABEL[code]):
            if key in header:
                return _seq(header[key])
        for key, val in header.items():
            if _section_code(key) == code:
                return _seq(val)
    alias_key = {"V": "version_section", "W": "well", "C": "curves",
                 "P": "parameters", "O": "other"}.get(code)
    if alias_key:
        direct = _field(parsed, alias_key, None)
        if direct is not None:
            return _seq(direct)
    return None


# --------------------------------------------------------------------------
# Public entry points
# --------------------------------------------------------------------------
def las_validate(path: str, **kwargs: Any) -> ValidationReport | Refusal:
    """Parse a LAS file with `las_parse` (#1) and report its deviations.

    Holds no parsing logic: the import is deferred so this module loads even
    while `tools/las.py` is being written alongside it.
    """
    try:
        # After the merge this module *is* tools/las.py, and the import resolves
        # to the already-loaded module — harmless, and it keeps the pre-merge
        # staging file importable on its own.
        from .las import las_parse  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover - merge-time wiring
        return Refusal(
            reason=f"las_parse is unavailable ({exc.__class__.__name__}: {exc})",
            needed=("tools.las.las_parse",),
            source=KGS_LAS20,
        )
    try:
        parsed = las_parse(path)
    except Exception as exc:
        return Refusal(
            reason=f"{path!r} could not be parsed as LAS ({exc.__class__.__name__}: {exc})",
            needed=("a readable LAS file", "las_parse to return a parsed object"),
            source=KGS_LAS20,
        )
    if isinstance(parsed, Refusal):
        return parsed
    return validate_parsed(parsed, **kwargs)


def validate_parsed(
    parsed: Any,
    *,
    treat_as_las_20: bool = False,
    index_tolerance: float | None = None,
    check_undeclared_nulls: bool = True,
    extra_null_sentinels: Sequence[float] = (),
) -> ValidationReport | Refusal:
    """Report every deviation from the corpus-held LAS 2.0 rules.

    Pure over `las_parse` output; the file-reading half is `las_validate`.
    Returns a report in all but the four cases in
    `specs/02-las_validate.md` "Validity limits and refusal conditions".
    """
    if parsed is None or isinstance(parsed, (str, bytes, int, float)):
        return Refusal(
            reason="las_validate needs the parsed object from las_parse, not a raw file body",
            needed=("las_parse(path) output",),
            source=KGS_LAS20,
        )

    deviations: list[Deviation] = []
    not_checked: list[UncheckedRule] = list(_STANDING_UNCHECKED)
    assumptions: dict[str, Any] = dict(_STANDING_ASSUMPTIONS)
    flags: list[str] = ["not-a-CWLS-conformance-check"]

    order = _section_order(parsed)
    if not order:
        return Refusal(
            reason="no LAS sections found; this does not look like a LAS file",
            needed=("a LAS file with at least one '~' section",),
            source=KGS_LAS20,
        )

    v_entries = _entries_for(parsed, "V")
    declared_version = _declared_version(parsed, v_entries)
    version_flags: tuple[str, ...] = ()
    if (declared_version is not None
            and _norm_version(declared_version) != _norm_version(SUPPORTED_VERSION)):
        if not treat_as_las_20:
            return Refusal(
                reason=(
                    f"file declares VERS {declared_version}; the only LAS rules held in "
                    "this corpus are LAS 2.0 (kgs-las-2.0-field-table#1, which "
                    "toc/TOC.md marks as not good for LAS 1.2 or 3.0 syntax differences)"
                ),
                needed=(
                    "the CWLS LAS 1.2 / 3.0 specification",
                    "or treat_as_las_20=True to apply the 2.0 rules anyway",
                ),
                source=KGS_LAS20,
            )
        version_flags = ("rules-applied-outside-declared-version",)
        flags.append("rules-applied-outside-declared-version")
        assumptions["treat_as_las_20"] = True

    def add(dev: Deviation) -> None:
        deviations.append(
            dev if not version_flags else replace(dev, flags=dev.flags + version_flags)
        )

    # ---- Sections: presence and order (corpus) ---------------------------
    _check_sections(order, add)

    # ---- ~V required mnemonics + WRAP domain -----------------------------
    wrap_raw = _check_version_section(parsed, v_entries, declared_version, add, not_checked)

    # ---- ~W required mnemonics and numeric values ------------------------
    w_entries = _entries_for(parsed, "W")
    w_values = _check_well_section(w_entries, add, not_checked)

    # ---- header line grammar + duplicates (house) ------------------------
    _check_header_grammar(parsed, add, not_checked)

    # ---- ~C and the data section ----------------------------------------
    curves = _seq(_field(parsed, "curves", None)) or (_entries_for(parsed, "C") or [])
    _check_curves(curves, add, not_checked)

    wrapped = _is_wrapped(wrap_raw)
    data_refusal = _field(parsed, "data_refusal", None)
    if wrapped:
        flags.append("wrapped-file: data-section rules not held")
        not_checked.append(UncheckedRule(
            code="A_WRAPPED_LAYOUT",
            reason="WRAP=YES; the wrapped data-section layout is not stated in the corpus",
        ))
    elif isinstance(data_refusal, Refusal):
        # las_parse declined to decode the data section; validating arrays it
        # refused to produce would be validating nothing.
        flags.append("las_parse refused the data section; header-only report")
        not_checked.append(UncheckedRule(
            code="A_DATA_SECTION",
            reason=f"las_parse refused the data section: {data_refusal.reason}",
            needed="; ".join(data_refusal.needed) or "a decodable ~A section",
        ))
    else:
        columns, orientation = _data_columns(parsed, len(curves))
        assumptions["data_orientation"] = orientation
        _check_data(parsed, curves, columns, w_values, add, not_checked,
                    index_tolerance=index_tolerance,
                    check_undeclared_nulls=check_undeclared_nulls,
                    extra_null_sentinels=tuple(extra_null_sentinels),
                    assumptions=assumptions)

    counts = {sev: sum(1 for d in deviations if d.severity == sev) for sev in SEVERITY_WEIGHT}
    score = _score(tuple(deviations), counts)

    parser_deviations = tuple(_seq(_field(parsed, "parser_deviations", None)))
    if parser_deviations:
        assumptions["parser_deviations_excluded_from_score"] = (
            f"{len(parser_deviations)} deviations reported by las_parse are carried in "
            "`parser_deviations` and not scored here, to avoid double-counting"
        )

    return ValidationReport(
        deviations=tuple(deviations),
        not_checked=tuple(not_checked),
        quality_score=score,
        counts=counts,
        las_version=declared_version,
        wrap=str(wrap_raw) if wrap_raw is not None else None,
        sections_present=tuple(order),
        assumptions=assumptions,
        flags=tuple(flags),
        parser_deviations=parser_deviations,
    )


# --------------------------------------------------------------------------
# Standing disclosures. Present on every report, whatever the file looks like.
# --------------------------------------------------------------------------
_STANDING_UNCHECKED: tuple[UncheckedRule, ...] = (
    UncheckedRule("HEADER_FORMAT_RULES",
                  "the corpus says each section 'has formatting requirements' and never "
                  "states them; only a house-rule approximation of the line grammar runs"),
    UncheckedRule("LINE_LENGTH", "no maximum line length is stated in the corpus"),
    UncheckedRule("CHARACTER_SET",
                  "permitted characters in mnemonics, units and free-text fields are not stated"),
    UncheckedRule("COMMENT_LINES", "comment ('#') line rules are not stated in the corpus"),
    UncheckedRule("W_CONDITIONAL_FIELDS",
                  "the field table lists PROV, CTRY, STAT, CNTY, UWI and API all as required, "
                  "which cannot all bind at once; which are conditional is not stated"),
    UncheckedRule("UNIT_VOCABULARY", "no unit-string vocabulary is stated in the corpus"),
    UncheckedRule("DATE_FORMAT",
                  "the field table calls MM/DD/YYYY 'preferred' and states no rule"),
    UncheckedRule("CURVE_API_CODES", "~C API-code field semantics are not stated in the corpus"),
    UncheckedRule("LAS_12_AND_30_RULES",
                  "LAS 1.2 and LAS 3.0 rule sets are absent; toc/TOC.md marks the corpus "
                  "document as not good for their syntax differences",
                  needed="the CWLS LAS 1.2 and LAS 3.0 specifications"),
)

_STANDING_ASSUMPTIONS: dict[str, Any] = {
    "rule_set": "LAS 2.0, corpus-held subset only",
    "sourced_rules": (
        "required sections V/W/C/A and optional P/O; ~V first; ~A last; "
        "~V mnemonics VERS+WRAP; the 17 ~W mnemonics; STRT/STOP/STEP/NULL numeric; "
        "~A values float or long and not exponential; space-separated columns; "
        "curve count equals column count; index in the first column; "
        "declared STRT/STOP/STEP match the data"
    ),
    "sourced_from": (KGS_LAS20, USGS_LAS),
    "house_rules": (
        "header line grammar MNEM.UNIT VALUE : DESCRIPTION; no whitespace in a mnemonic; "
        "duplicate mnemonics; monotonic index; regular index step; "
        "the index-mnemonic table; the undeclared-null scan; STEP=0 means variable"
    ),
    "severity_is_ours": "no corpus source grades a deviation; error/warning/info are ours",
    "score_weights": dict(SEVERITY_WEIGHT),
    "score_formula": "1 / (1 + sum of severity weights) - invented here, see " + SPEC,
    "not_a_conformance_check": (
        "the CWLS spec is not held; per usgs-las-format#1 the authoritative checker "
        "is the CWLS 'LAS Certify' software"
    ),
}


# --------------------------------------------------------------------------
# Individual check groups
# --------------------------------------------------------------------------
def _section_order(parsed: Any) -> list[str]:
    raw = _field(parsed, "sections", None)
    codes: list[str] = []
    if isinstance(raw, Mapping):
        candidates = list(raw.keys())
    else:
        candidates = _seq(raw)
    for item in candidates:
        code = _section_code(item)
        if code:
            codes.append(code)
    if codes:
        return codes
    # Fall back to whichever per-section fields the parser did expose.
    for code in ("V", "W", "C", "P", "O", "A"):
        if code == "A":
            if _field(parsed, "data", None) not in (None, _MISSING):
                codes.append("A")
            continue
        if _entries_for(parsed, code):
            codes.append(code)
    return codes


def _declared_version(parsed: Any, v_entries: list[Any] | None) -> str | None:
    """The declared VERS, or None. A blank VERS reads as *absent*, not as a
    foreign version: a missing version is the deviation this tool reports, and
    turning it into a refusal would hide it."""
    direct = _field(parsed, "version", None)
    if direct not in (None, _MISSING) and str(direct).strip():
        return str(direct).strip()
    for entry in v_entries or []:
        if str(_entry_field(entry, "mnemonic", "")).strip().upper() == "VERS":
            value = _entry_field(entry, "value", None)
            text = "" if value is None else str(value).strip()
            return text or None
    return None


def _norm_version(text: str) -> str:
    got = _as_float(text)
    return f"{got:g}" if got is not None else text.strip()


def _mnemonics(entries: Iterable[Any]) -> list[str]:
    out = []
    for entry in entries:
        mnem = _entry_field(entry, "mnemonic", None)
        out.append("" if mnem is None else str(mnem).strip().upper())
    return out


def _check_sections(order: list[str], add) -> None:
    present = set(order)
    for code in REQUIRED_SECTIONS:
        if code not in present:
            add(Deviation(
                code=f"{code}_SECTION_MISSING",
                message=f"{_SECTION_LABEL[code]} is missing; the source calls it a required section",
                severity="error", provenance=PROV_CORPUS, source=KGS_LAS20, section=code,
            ))
    if "V" in present and order[0] != "V":
        add(Deviation(
            code="V_NOT_FIRST",
            message=f"~V is not the first section (first is {_SECTION_LABEL.get(order[0], order[0])}); "
                    "the source says it 'must be the first section'",
            severity="error", provenance=PROV_CORPUS, source=KGS_LAS20, section="V",
            detail={"section_order": tuple(order)},
        ))
    if "A" in present and order[-1] != "A":
        add(Deviation(
            code="A_NOT_LAST",
            message=f"~A is not the last section (last is {_SECTION_LABEL.get(order[-1], order[-1])}); "
                    "the source says it 'is the last section in the file'",
            severity="error", provenance=PROV_CORPUS, source=KGS_LAS20, section="A",
            detail={"section_order": tuple(order)},
        ))
    # "is preferably the second section" - a preference, so info, not error.
    if "W" in present and len(order) > 1 and order[1] != "W":
        add(Deviation(
            code="W_NOT_SECOND",
            message="~W is not the second section; the source says it 'is preferably the second section'",
            severity="info", provenance=PROV_CORPUS, source=KGS_LAS20, section="W",
            detail={"section_order": tuple(order)},
        ))


def _check_version_section(parsed: Any, v_entries: list[Any] | None,
                           declared_version: str | None, add,
                           not_checked: list[UncheckedRule]) -> Any:
    wrap_raw = _field(parsed, "wrap", None)
    if wrap_raw is _MISSING:
        wrap_raw = None
    if v_entries is None:
        not_checked.append(UncheckedRule(
            code="V_MNEM_PRESENCE",
            reason="las_parse exposed no ~V entries; VERS/WRAP presence could not be checked",
            needed="las_parse to expose the ~V section entries",
        ))
        return wrap_raw

    present = set(_mnemonics(v_entries))
    for mnem in REQUIRED_V_MNEMONICS:
        if mnem not in present:
            # A VERS we already read from parsed.version still counts as present.
            if mnem == "VERS" and declared_version:
                continue
            add(Deviation(
                code="V_MNEM_MISSING",
                message=f"~V is missing required mnemonic {mnem}",
                severity="error", provenance=PROV_CORPUS, source=KGS_LAS20,
                section="V", mnemonic=mnem,
            ))
    if wrap_raw is None:
        for entry in v_entries:
            if str(_entry_field(entry, "mnemonic", "")).strip().upper() == "WRAP":
                wrap_raw = _entry_field(entry, "value", None)
                break
    if wrap_raw is not None:
        token = _wrap_token(wrap_raw)
        if token not in ("YES", "NO"):
            add(Deviation(
                code="WRAP_VALUE_INVALID",
                message=f"WRAP value {wrap_raw!r} is neither YES nor NO; the source describes a "
                        "two-state 'wrapped' / 'un-wrapped' mode and tabulates 'NO'",
                severity="error", provenance=PROV_PARTIAL, source=KGS_LAS20,
                section="V", mnemonic="WRAP",
            ))
    return wrap_raw


def _wrap_token(wrap_raw: Any) -> str:
    if isinstance(wrap_raw, bool):
        return "YES" if wrap_raw else "NO"
    return str(wrap_raw).strip().upper()


def _is_wrapped(wrap_raw: Any) -> bool:
    return _wrap_token(wrap_raw) == "YES" if wrap_raw is not None else False


def _check_well_section(w_entries: list[Any] | None, add,
                        not_checked: list[UncheckedRule]) -> dict[str, float]:
    """Required ~W mnemonics and the numeric values of STRT/STOP/STEP/NULL."""
    values: dict[str, float] = {}
    if w_entries is None:
        not_checked.append(UncheckedRule(
            code="W_MNEM_PRESENCE",
            reason="las_parse exposed no ~W entries; the required-field check could not run",
            needed="las_parse to expose the ~W section entries",
        ))
        return values

    by_mnem: dict[str, Any] = {}
    for entry in w_entries:
        mnem = str(_entry_field(entry, "mnemonic", "")).strip().upper()
        by_mnem.setdefault(mnem, entry)

    for mnem in REQUIRED_W_MNEMONICS:
        if mnem not in by_mnem:
            numeric = mnem in NUMERIC_W_MNEMONICS
            add(Deviation(
                code="W_MNEM_MISSING",
                message=f"~W is missing required mnemonic {mnem}; the field table lists it as "
                        "a required field of the LAS 2.0 ~Well Information Section",
                # Requiredness is the source's; this grading is ours.
                severity="error" if numeric else "warning",
                provenance=PROV_CORPUS, source=KGS_LAS20, section="W", mnemonic=mnem,
                detail={"severity_is_house_assigned": True},
            ))
            continue
        if mnem in NUMERIC_W_MNEMONICS:
            raw_value = _entry_field(by_mnem[mnem], "value", None)
            got = _as_float(raw_value)
            if got is None:
                add(Deviation(
                    code="W_VALUE_NOT_NUMERIC",
                    message=f"~W {mnem} value {raw_value!r} is not numeric; the field table "
                            "gives its format as nnnn.nn",
                    severity="error", provenance=PROV_CORPUS, source=KGS_LAS20,
                    section="W", mnemonic=mnem,
                    line_no=_entry_field(by_mnem[mnem], "line_no", None),
                ))
            else:
                values[mnem] = got
    return values


def _check_header_grammar(parsed: Any, add, not_checked: list[UncheckedRule]) -> None:
    """House rules over header lines. ~O is exempt: 'has no formatting requirements'."""
    saw_any_raw = False
    for code in ("V", "W", "C", "P"):
        entries = _entries_for(parsed, code)
        if entries is None:
            continue
        seen: dict[str, int] = {}
        for entry in entries:
            mnem = str(_entry_field(entry, "mnemonic", "") or "").strip()
            line_no = _entry_field(entry, "line_no", None)
            upper = mnem.upper()
            if upper:
                seen[upper] = seen.get(upper, 0) + 1
                if seen[upper] == 2:
                    add(Deviation(
                        code="DUPLICATE_CURVE_MNEMONIC" if code == "C" else "DUPLICATE_MNEMONIC",
                        message=f"mnemonic {mnem} appears more than once in {_SECTION_LABEL[code]}",
                        severity="warning", provenance=PROV_HOUSE, section=code,
                        mnemonic=upper, line_no=line_no,
                    ))
            if mnem and re.search(r"\s", mnem):
                add(Deviation(
                    code="MNEMONIC_HAS_WHITESPACE",
                    message=f"mnemonic {mnem!r} in {_SECTION_LABEL[code]} contains whitespace",
                    severity="warning", provenance=PROV_HOUSE, section=code,
                    mnemonic=mnem, line_no=line_no,
                ))
            raw = _entry_field(entry, "raw", None)
            if raw is None:
                continue
            saw_any_raw = True
            text = str(raw)
            if text.strip() and not _HEADER_LINE_RE.match(text):
                add(Deviation(
                    code="HEADER_LINE_GRAMMAR",
                    message=f"header line in {_SECTION_LABEL[code]} does not read "
                            "'MNEM.UNIT VALUE : DESCRIPTION'",
                    severity="warning", provenance=PROV_HOUSE, section=code,
                    mnemonic=mnem or None, line_no=line_no,
                    detail={"raw": text.rstrip()},
                ))
    if not saw_any_raw:
        not_checked.append(UncheckedRule(
            code="HEADER_LINE_GRAMMAR",
            reason="las_parse exposed no raw header line text; even the house-rule grammar "
                   "approximation could not run",
            needed="las_parse to keep the raw text of each header entry",
        ))


def _check_curves(curves: list[Any], add, not_checked: list[UncheckedRule]) -> None:
    if not curves:
        not_checked.append(UncheckedRule(
            code="C_ENTRIES",
            reason="las_parse exposed no ~C entries; curve-versus-column checks could not run",
            needed="las_parse to expose the ~C section entries",
        ))
        return
    mnems = _mnemonics(curves)
    first = mnems[0]
    if first not in INDEX_MNEMONICS:
        # kgs#1: "The index values always appear in the first column". Reported
        # as its own deviation, not folded into INDEX_CURVE_UNRECOGNIZED below:
        # an unrecognized vendor mnemonic in column 1 is a naming question, a
        # recognized index sitting in column 3 mis-addresses every column.
        # Identifying *which* curve is the index still leans on the house
        # mnemonic table, and the severity is ours; both are recorded in detail.
        misplaced = [(i, m) for i, m in enumerate(mnems) if i and m in INDEX_MNEMONICS]
        if misplaced:
            at, mnem = misplaced[0]
            add(Deviation(
                code="INDEX_NOT_FIRST_COLUMN",
                message=f"curve {mnem} is a depth or time index but appears in data column "
                        f"{at + 1}, not the first; the source says 'The index values always "
                        f"appear in the first column' (first curve is {first!r})",
                severity="error", provenance=PROV_CORPUS, source=KGS_LAS20,
                section="C", mnemonic=mnem,
                detail={"column_index": at, "first_curve": first,
                        "index_identified_with_house_mnemonic_table": True,
                        "severity_is_house_assigned": True},
            ))
        add(Deviation(
            code="INDEX_CURVE_UNRECOGNIZED",
            message=f"first curve {first!r} is not a recognized depth or time index; the source "
                    "says 'the index of the data columns is either Depth or Time' but supplies "
                    "no mnemonic list, so the list used here is ours",
            severity="info", provenance=PROV_PARTIAL, source=KGS_LAS20,
            section="C", mnemonic=first or None,
            detail={"recognized": tuple(sorted(INDEX_MNEMONICS))},
        ))


def _data_columns(parsed: Any, n_curves: int) -> tuple[list[list[Any]], str]:
    """Normalize `data` to columns, reporting which orientation was inferred."""
    raw = _field(parsed, "data", None)
    rows_or_cols = _seq(raw)
    if not rows_or_cols:
        return [], "empty"
    inner = [_seq(item) for item in rows_or_cols]
    if not any(inner):
        return [], "empty"
    if n_curves and len(inner) == n_curves and (len(inner) != len(inner[0]) or n_curves == 1):
        return inner, "columns (matched curve count)"
    if n_curves and inner and len(inner[0]) == n_curves:
        transposed = [list(col) for col in zip(*inner)]
        return transposed, "rows (inner length matched curve count)"
    if len(inner) == n_curves:
        return inner, "columns (assumed; square data)"
    return inner, "columns (assumed; neither dimension matched the curve count)"


def _check_data(parsed: Any, curves: list[Any], columns: list[list[Any]],
                w_values: dict[str, float], add, not_checked: list[UncheckedRule],
                *, index_tolerance: float | None, check_undeclared_nulls: bool,
                extra_null_sentinels: tuple[float, ...],
                assumptions: dict[str, Any]) -> None:
    # --- raw-line checks: numeric format and the space delimiter (corpus) ---
    data_lines = _seq(_field(parsed, "data_lines", None))
    if data_lines:
        _check_data_lines(data_lines, len(curves), add)
    else:
        not_checked.append(UncheckedRule(
            code="A_TEXT_FORMAT",
            reason="las_parse exposed no raw ~A lines; the 'floating point or integer only', "
                   "'no exponential values' and 'separated by at least one space' checks "
                   "could not run on the file text",
            needed="las_parse to keep the raw lines of the ~A section",
        ))
        # Fall back to what can still be seen in the parsed values.
        for c_index, column in enumerate(columns):
            mnem = _mnemonics(curves)[c_index] if c_index < len(curves) else f"col{c_index}"
            for r_index, value in enumerate(column):
                if isinstance(value, str) and _EXPONENT_RE.search(value):
                    add(Deviation(
                        code="A_VALUE_EXPONENTIAL",
                        message=f"~A value {value!r} (curve {mnem}, row {r_index}) is exponential; "
                                "the source says exponential values 'are not supported'",
                        severity="error", provenance=PROV_CORPUS, source=KGS_LAS20,
                        section="A", mnemonic=mnem or None,
                    ))
                elif _as_float(value) is None:
                    add(Deviation(
                        code="A_VALUE_NOT_NUMERIC",
                        message=f"~A value {value!r} (curve {mnem}, row {r_index}) is not a float "
                                "or long; the source allows no other format",
                        severity="error", provenance=PROV_CORPUS, source=KGS_LAS20,
                        section="A", mnemonic=mnem or None,
                    ))

    if not columns:
        not_checked.append(UncheckedRule(
            code="A_DATA_ARRAYS",
            reason="las_parse exposed no data arrays; column-count and index checks could not run",
            needed="las_parse to expose the ~A data arrays",
        ))
        return

    # --- curve count versus column count (corpus) ---
    # Honesty note: when the orientation had to be *inferred* as rows, that
    # inference already used the curve count, so the check below cannot fire and
    # is reported as not run rather than as passed.
    if str(assumptions.get("data_orientation", "")).startswith("rows"):
        not_checked.append(UncheckedRule(
            code="A_COLUMN_COUNT",
            reason="the data orientation was inferred from the curve count, so curve-count "
                   "versus column-count could not be checked independently",
            needed="las_parse to state the orientation of `data` (columns, per the assumed "
                   "interface in specs/02-las_validate.md)",
        ))
    elif curves and len(columns) != len(curves):
        add(Deviation(
            code="A_COLUMN_COUNT",
            message=f"~A has {len(columns)} data columns but ~C defines {len(curves)} curves; "
                    "the source says ~C lists curves 'in the order that they appear in the "
                    "data section'",
            severity="error", provenance=PROV_CORPUS, source=KGS_LAS20, section="A",
            detail={"columns": len(columns), "curves": len(curves)},
        ))

    index = [_as_float(v) for v in columns[0]]
    index = [v for v in index if v is not None]
    if len(index) < 2:
        return

    # --- declared STRT/STOP/STEP versus the data (corpus rule, our tolerance) ---
    tol = index_tolerance
    if tol is None:
        scale = max(1.0, abs(index[0]), abs(index[-1]))
        tol = 1e-6 + 1e-6 * scale
    assumptions["index_tolerance"] = tol
    assumptions["index_tolerance_is_house"] = True
    for mnem, observed in (("STRT", index[0]), ("STOP", index[-1])):
        declared = w_values.get(mnem)
        if declared is not None and abs(declared - observed) > tol:
            add(Deviation(
                code="STRT_STOP_STEP_MISMATCH",
                message=f"~W {mnem} declares {declared:g} but the data index {'starts' if mnem == 'STRT' else 'ends'} "
                        f"at {observed:g}; ~W is specified to carry 'the start and stop values of "
                        "the data in this file'",
                severity="warning", provenance=PROV_CORPUS, source=KGS_LAS20,
                section="W", mnemonic=mnem,
                detail={"declared": declared, "observed": observed, "tolerance": tol,
                        "tolerance_is_house": True},
            ))

    steps = [b - a for a, b in zip(index, index[1:])]
    declared_step = w_values.get("STEP")
    if declared_step is not None and abs(declared_step) > tol:
        median_step = sorted(steps)[len(steps) // 2]
        if abs(declared_step - median_step) > max(tol, 1e-9):
            add(Deviation(
                code="STRT_STOP_STEP_MISMATCH",
                message=f"~W STEP declares {declared_step:g} but the data index steps by "
                        f"{median_step:g}",
                severity="warning", provenance=PROV_CORPUS, source=KGS_LAS20,
                section="W", mnemonic="STEP",
                detail={"declared": declared_step, "observed": median_step,
                        "tolerance_is_house": True},
            ))
    elif declared_step is not None:
        # STEP = 0 as "variable step" is a convention the corpus does not state.
        assumptions["step_zero_read_as_variable"] = "house rule; not stated in the corpus"

    # --- house rules on the index ---
    if any(s > 0 for s in steps) and any(s < 0 for s in steps):
        add(Deviation(
            code="INDEX_NOT_MONOTONIC",
            message="the index column changes direction; nothing in the corpus requires "
                    "monotonicity, so this is our rule",
            severity="info", provenance=PROV_HOUSE, section="A",
            detail={"n_reversals": sum(1 for a, b in zip(steps, steps[1:]) if a * b < 0)},
        ))
    elif declared_step is not None and abs(declared_step) > tol:
        irregular = sum(1 for s in steps if abs(s - declared_step) > max(tol, 1e-9))
        if irregular:
            add(Deviation(
                code="INDEX_STEP_IRREGULAR",
                message=f"{irregular} of {len(steps)} index intervals differ from the declared "
                        "STEP; irregular spacing under a non-zero STEP is our rule",
                severity="info", provenance=PROV_HOUSE, section="A",
                detail={"irregular_intervals": irregular, "intervals": len(steps)},
            ))

    # --- undeclared null sentinels (list sourced, scan ours) ---
    if check_undeclared_nulls:
        declared_null = w_values.get("NULL")
        if declared_null is None:
            declared_null = _as_float(_field(parsed, "null_value", None))
        candidates = tuple(COMMON_NULL_SENTINELS) + tuple(extra_null_sentinels)
        undeclared = [s for s in candidates
                      if declared_null is None or abs(s - declared_null) > 1e-9]
        for sentinel in undeclared:
            hits = sum(1 for col in columns for v in col
                       if (f := _as_float(v)) is not None and abs(f - sentinel) < 1e-9)
            if hits:
                add(Deviation(
                    code="UNDECLARED_NULL_SENTINEL",
                    message=f"{hits} data values equal {sentinel:g}, a common null value the "
                            "source lists ('-999.25, -9999, etc.') but this file does not "
                            f"declare (NULL = {declared_null})",
                    severity="warning", provenance=PROV_PARTIAL, source=KGS_LAS20,
                    section="A",
                    detail={"sentinel": sentinel, "count": hits, "declared_null": declared_null,
                            "scan_is_house_rule": True},
                ))


def _check_data_lines(data_lines: Sequence[Any], n_curves: int, add) -> None:
    for offset, raw in enumerate(data_lines):
        text = str(raw).rstrip("\n")
        if not text.strip():
            continue
        if text.lstrip().startswith("~"):
            continue
        if "\t" in text or "," in text:
            add(Deviation(
                code="A_DELIMITER_NOT_SPACE",
                message="~A line uses a tab or comma; the source requires each column to be "
                        "'separated by at least one space (ASCII 32)'",
                severity="warning", provenance=PROV_CORPUS, source=KGS_LAS20,
                section="A", line_no=offset,
                detail={"raw": text[:120]},
            ))
        tokens = text.split()
        for token in tokens:
            if _EXPONENT_RE.search(token):
                add(Deviation(
                    code="A_VALUE_EXPONENTIAL",
                    message=f"~A token {token!r} is exponential; the source says 'other formats "
                            "such as Text or Exponential values are not supported'",
                    severity="error", provenance=PROV_CORPUS, source=KGS_LAS20,
                    section="A", line_no=offset,
                ))
            elif not _NUMERIC_RE.match(token):
                add(Deviation(
                    code="A_VALUE_NOT_NUMERIC",
                    message=f"~A token {token!r} is not a floating point or integer value; "
                            "the source allows no other format",
                    severity="error", provenance=PROV_CORPUS, source=KGS_LAS20,
                    section="A", line_no=offset,
                ))
        if n_curves and tokens and len(tokens) != n_curves:
            add(Deviation(
                code="A_ROW_LENGTH",
                message=f"~A line has {len(tokens)} values but ~C defines {n_curves} curves; "
                        "the field table describes WRAP=NO as 'one line per depth step'",
                severity="error", provenance=PROV_PARTIAL, source=KGS_LAS20,
                section="A", line_no=offset,
                detail={"tokens": len(tokens), "curves": n_curves},
            ))


# --------------------------------------------------------------------------
# Scoring - ours end to end
# --------------------------------------------------------------------------
def _score(deviations: tuple[Deviation, ...], counts: dict[str, int]) -> Quantity:
    """score = 1 / (1 + sum of severity weights). Bounded (0, 1]; 1.0 when clean.

    The form and the three weights are invented in specs/02-las_validate.md.
    Nothing in the corpus grades a LAS deviation, so a caller with its own
    weighting should recompute from `report.deviations` and ignore this.
    """
    penalty = sum(SEVERITY_WEIGHT[d.severity] for d in deviations)
    value = 1.0 / (1.0 + penalty)
    flags = ["score weights and formula are a house heuristic, not from any source"]
    if any(d.provenance == PROV_HOUSE for d in deviations):
        flags.append("some deviations rest on house rules; see deviations_by_provenance()")
    return Quantity(
        value=value,
        unit="v/v",
        method="house data-quality heuristic (LAS 2.0 corpus-held subset)",
        source=SCORE_SOURCE,
        inputs={"counts": dict(counts), "penalty": penalty,
                "n_deviations": len(deviations)},
        assumptions={"formula": "1 / (1 + sum(w))", "weights": dict(SEVERITY_WEIGHT),
                     "sourced": False,
                     "rules_checked_against": (KGS_LAS20, USGS_LAS),
                     "not_a_CWLS_conformance_score": True},
        flags=tuple(flags),
    )

# ---------------------------------------------------------------------------
# 03_curve_inventory
# `curve_inventory` (#3, group A) — staged for merge into `tools/las.py`.
# ---------------------------------------------------------------------------

# `~V`/`~W`/`~C`/`~A` field vocabulary, the ~C-order-equals-column-order rule,
# the index-in-first-column rule, and the "common null values" warning.
LAS_KGS = "02-las-format/kgs-las-2.0-field-table#1"

# House rules. Neither is in the corpus, so both are arguments, both land in
# `assumptions`, and the gap rule announces itself in a flag.
DEFAULT_GAP_FACTOR = 1.5      # increment > factor * step counts as a gap
DEFAULT_STEP_TOL_FRAC = 0.01  # declared vs measured step agreement
NULL_MATCH_RTOL = 1e-9        # LAS nulls are written as text, so match loosely

# Named in the source as "common": both, which is the whole problem.
DOCUMENTED_COMMON_NULLS = (-999.25, -9999.0)



# --------------------------------------------------------------------------
# return shapes
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class CurveRecord:
    """One `~C` entry joined to its column of `~A`. Mnemonic and unit are raw."""

    mnemonic: str
    unit: str
    description: str
    column: int
    is_index: bool
    n_samples: int
    n_null: int
    null_fraction: Quantity
    depth_range: Range | None
    all_null: bool
    flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CurveInventory:
    curves: tuple[CurveRecord, ...]
    index_mnemonic: str
    index_unit: str
    n_samples: int
    logged_interval: Range
    step: Quantity | None
    gaps: tuple[tuple[float, float], ...]
    direction: str  # "increasing" | "decreasing" | "non-monotonic"
    source: str = LAS_KGS
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)

    def by_mnemonic(self, mnemonic: str) -> tuple[CurveRecord, ...]:
        """All records with this raw mnemonic — plural, because files repeat them."""
        return tuple(c for c in self.curves if c.mnemonic == mnemonic)


# --------------------------------------------------------------------------
# record access: mapping or object, whatever `las_parse` ends up returning
# --------------------------------------------------------------------------
def _curve_field(record: Any, name: str, default: Any = _MISSING) -> Any:
    if isinstance(record, Mapping):
        value = record.get(name, _MISSING)
    else:
        value = getattr(record, name, _MISSING)
    if value is _MISSING:
        if default is _MISSING:
            raise TypeError(
                f"curve record is missing required field {name!r}: {record!r}. "
                "curve_inventory takes mappings or objects with "
                "mnemonic/unit/description/values."
            )
        return default
    return value


def _is_null(value: Any, declared_null: float | None) -> tuple[bool, bool, bool]:
    """-> (is_null, is_non_finite, is_non_numeric).

    `None` and NaN are nulls on both paths: NaN is not a sentinel guess, it is
    not a number. `declared_null` is matched only on the unscrubbed path.
    """
    if value is None:
        return True, False, False
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return True, False, True  # source: ~A permits float or integer only
    v = float(value)
    if math.isnan(v):
        return True, False, False
    if math.isinf(v):
        return False, True, False
    if declared_null is not None and math.isclose(
        v, declared_null, rel_tol=NULL_MATCH_RTOL, abs_tol=NULL_MATCH_RTOL
    ):
        return True, False, False
    return False, False, False


def _clean_column(values: Sequence[Any], declared_null: float | None):
    """-> (list[float | None], n_null, saw_non_finite, saw_non_numeric)."""
    out: list[float | None] = []
    n_null = 0
    non_finite = False
    non_numeric = False
    for raw in values:
        is_null, is_inf, is_text = _is_null(raw, declared_null)
        non_finite = non_finite or is_inf
        non_numeric = non_numeric or is_text
        if is_null:
            out.append(None)
            n_null += 1
        else:
            out.append(float(raw))
    return out, n_null, non_finite, non_numeric


def _monotone_direction(diffs: Sequence[float]) -> str:
    if not diffs:
        return "increasing"  # a single sample has no direction to contradict
    if all(d > 0 for d in diffs):
        return "increasing"
    if all(d < 0 for d in diffs):
        return "decreasing"
    return "non-monotonic"


# --------------------------------------------------------------------------
# the tool
# --------------------------------------------------------------------------
def curve_inventory(
    curves: Iterable[Any],
    *,
    values_are_scrubbed: bool,
    declared_null: float | None = None,
    index_mnemonic: str | None = None,
    declared_start: float | None = None,
    declared_stop: float | None = None,
    declared_step: float | None = None,
    depth_unit: str | None = None,
    gap_factor: float = DEFAULT_GAP_FACTOR,
    step_tol_frac: float = DEFAULT_STEP_TOL_FRAC,
    null_basis: Any = None,
) -> CurveInventory | Refusal:
    """Enumerate the curves of one LAS file, their depth spans and null fractions.

    `values_are_scrubbed` is keyword-only and has no default on purpose: it says
    whether `None` already marks every null (`null_scrub` output) or whether only
    `declared_null` can be counted. See the module docstring.
    """
    if not isinstance(values_are_scrubbed, bool):
        raise TypeError("values_are_scrubbed must be a bool; it is not inferable")

    records = list(curves)
    if not records:
        return Refusal(
            reason="no curves declared; ~C is empty or absent",
            needed=("a ~C section listing curve mnemonics",),
            source=LAS_KGS,
        )

    # The null basis has to exist before anything is counted. Without one, even
    # the index column may still hold sentinels, so the depth frame would be
    # wrong too — not just the null fractions.
    if not values_are_scrubbed and declared_null is None:
        return Refusal(
            reason=(
                "values are unscrubbed and no NULL was declared; there is no basis "
                "for distinguishing a null from a reading"
            ),
            needed=(
                "null_scrub output (None marking nulls), or the ~W NULL value",
            ),
            source=LAS_KGS,
        )

    match_null = None if values_are_scrubbed else float(declared_null)  # type: ignore[arg-type]

    mnemonics = [str(_curve_field(r, "mnemonic")) for r in records]
    units = [str(_curve_field(r, "unit", "") or "") for r in records]
    descriptions = [str(_curve_field(r, "description", "") or "") for r in records]

    columns = []
    for record in records:
        raw = _curve_field(record, "values")
        columns.append(_clean_column(list(raw), match_null))

    lengths = {len(c[0]) for c in columns}
    if lengths == {0}:
        return Refusal(
            reason="~A holds no rows; there is nothing to inventory",
            needed=("a populated ~A data section",),
            source=LAS_KGS,
        )
    if len(lengths) > 1:
        return Refusal(
            reason=(
                "curve columns have unequal lengths "
                f"({sorted(lengths)}); ~A is not rectangular, so the ~C-order to "
                "column join is unsafe"
            ),
            needed=("a parse whose curve columns are all the same length",),
            source=LAS_KGS,
        )

    n_samples = lengths.pop()

    # ---- index curve -----------------------------------------------------
    file_flags: list[str] = []
    if index_mnemonic is None:
        index_col = 0  # source: "The index values always appear in the first column"
    else:
        if index_mnemonic not in mnemonics:
            return Refusal(
                reason=f"named index curve {index_mnemonic!r} is not in ~C",
                needed=(f"an index mnemonic present in {mnemonics!r}",),
                source=LAS_KGS,
            )
        index_col = mnemonics.index(index_mnemonic)
        if index_col != 0:
            file_flags.append(
                f"index {mnemonics[index_col]!r} is column {index_col}, not the "
                "first column; the source requires the index first"
            )

    index_values = columns[index_col][0]
    usable = [(row, v) for row, v in enumerate(index_values) if v is not None]
    if not usable:
        return Refusal(
            reason=(
                f"index curve {mnemonics[index_col]!r} is entirely null; the file "
                "has no depth frame, so no range, step or per-curve span is defined"
            ),
            needed=("an index column with at least one non-null sample",),
            source=LAS_KGS,
        )
    if len(usable) < n_samples:
        file_flags.append(
            f"{n_samples - len(usable)} of {n_samples} index samples are null; "
            "rows without an index are excluded from the frame and can look like gaps"
        )

    index_unit = depth_unit if depth_unit is not None else units[index_col]
    depths = [v for _, v in usable]

    logged_interval = Range(
        low=min(depths),
        high=max(depths),
        unit=index_unit,
        method="min and max of the non-null index column",
        source=LAS_KGS,
        members={
            "first_sample": depths[0],
            "last_sample": depths[-1],
            "n_index_samples": float(len(depths)),
        },
    )

    # ---- step, direction, gaps ------------------------------------------
    diffs = [b - a for a, b in zip(depths, depths[1:])]
    direction = _monotone_direction(diffs)
    if direction == "non-monotonic":
        file_flags.append(
            "index is not monotonic (a reversal or a repeated value); depth "
            "range is reported from min and max"
        )
    elif direction == "decreasing":
        file_flags.append("index decreases with row order (bottom-up file)")

    step: Quantity | None = None
    if diffs:
        magnitudes = [abs(d) for d in diffs]
        measured = median(magnitudes)
        step_flags: list[str] = []
        if declared_step is not None:
            if declared_step == 0:
                step_flags.append(
                    "declared STEP is 0; the corpus does not state what a zero "
                    "step means, so the step here is measured from the index column"
                )
            elif abs(abs(declared_step) - measured) > step_tol_frac * max(
                abs(declared_step), 1e-12
            ):
                step_flags.append(
                    f"declared STEP {declared_step} disagrees with the measured "
                    f"step {measured:g} by more than {step_tol_frac:.1%}"
                )
        if direction == "non-monotonic":
            step_flags.append("index is not monotonic; the measured step is indicative only")
        step = Quantity(
            value=measured,
            unit=index_unit,
            method="median absolute first difference of the index column",
            source=LAS_KGS,
            inputs={"n_increments": len(diffs), "declared_step": declared_step},
            assumptions={"direction": direction},
            flags=tuple(step_flags),
        )
    else:
        file_flags.append("only one usable index sample; no step could be measured")

    gaps: list[tuple[float, float]] = []
    if step is not None and step.value > 0:
        limit = gap_factor * step.value
        for (a, b) in zip(depths, depths[1:]):
            if abs(b - a) > limit:
                gaps.append((a, b))
    if gaps:
        file_flags.append(
            f"{len(gaps)} depth gap(s) wider than {gap_factor}x the step; the gap "
            "factor is a house rule, not from the corpus"
        )

    # ---- declared frame cross-check --------------------------------------
    # kgs#1 on ~W: it "contains information on the well name, location, and start
    # and stop values of the data in this file" - so STRT is the first index
    # sample and STOP the last, not merely a bound the data sits inside. A file
    # whose ~A starts below its declared STRT is the case worth catching, and
    # containment alone would miss it. Tolerance is one sample interval: a
    # difference smaller than the step is not resolvable from the data.
    for name, declared, measured, which in (
        ("STRT", declared_start, depths[0], "first"),
        ("STOP", declared_stop, depths[-1], "last"),
    ):
        if declared is None:
            continue
        tol = abs(step.value) if step is not None else 0.0
        if abs(declared - measured) > tol:
            file_flags.append(
                f"declared {name} {declared:g} disagrees with the {which} index "
                f"sample {measured:g} (difference {abs(declared - measured):g} "
                f"exceeds one step, {tol:g}); the declaration is reported, never "
                "substituted for the data"
            )

    # ---- per-curve records ------------------------------------------------
    if not values_are_scrubbed:
        file_flags.append(
            "values were not scrubbed: only the declared NULL "
            f"({declared_null}) was counted, so every null fraction is a LOWER "
            "BOUND and every depth range may be over-stated. The source names "
            f"{DOCUMENTED_COMMON_NULLS} as both common, so undeclared sentinels "
            "may remain. Run null_scrub (#12) for a true count."
        )

    seen: dict[str, int] = {}
    for m in mnemonics:
        seen[m] = seen.get(m, 0) + 1
    duplicates = sorted(m for m, n in seen.items() if n > 1)
    if duplicates:
        file_flags.append(
            f"duplicate mnemonics in ~C: {duplicates}; which is which is a "
            "normalization question, not a parse one"
        )

    null_method = (
        "null samples / total samples; nulls from null_scrub"
        if values_are_scrubbed
        else f"null samples / total samples; nulls = declared NULL {declared_null} only"
    )
    lower_bound_flag = (
        ()
        if values_are_scrubbed
        else ("lower bound: undeclared sentinels may remain (see file flags)",)
    )

    records_out: list[CurveRecord] = []
    for col, (values, n_null, non_finite, non_numeric) in enumerate(columns):
        curve_flags: list[str] = list(lower_bound_flag)
        if not units[col]:
            curve_flags.append("no unit declared in ~C; unit_convert cannot run on this curve")
        if non_finite:
            curve_flags.append("column holds a non-finite value (inf)")
        if non_numeric:
            curve_flags.append(
                "column holds a non-numeric value, counted as null; the source "
                "permits only floating point or integer values in ~A"
            )

        all_null = n_null == n_samples
        if all_null:
            curve_flags.append("curve is entirely null; present in ~C, absent in ~A")

        # Span: index at the first and last non-null sample of THIS curve, not
        # the file's STRT/STOP.
        depth_range = None
        if not all_null:
            live = [r for r, v in enumerate(values) if v is not None and index_values[r] is not None]
            if live:
                first_d = index_values[live[0]]
                last_d = index_values[live[-1]]
                assert first_d is not None and last_d is not None
                depth_range = Range(
                    low=min(first_d, last_d),
                    high=max(first_d, last_d),
                    unit=index_unit,
                    method="index at the first and last non-null sample of the curve",
                    source=LAS_KGS,
                    members={
                        "first_non_null_row": float(live[0]),
                        "last_non_null_row": float(live[-1]),
                        "at_first_non_null": first_d,
                        "at_last_non_null": last_d,
                    },
                )
            else:
                curve_flags.append(
                    "every non-null sample of this curve sits on a null index row; "
                    "no depth span can be assigned"
                )

        records_out.append(
            CurveRecord(
                mnemonic=mnemonics[col],
                unit=units[col],
                description=descriptions[col],
                column=col,
                is_index=(col == index_col),
                n_samples=n_samples,
                n_null=n_null,
                null_fraction=Quantity(
                    value=n_null / n_samples,
                    unit="v/v",
                    method=null_method,
                    source=LAS_KGS,
                    inputs={"n_null": n_null, "n_samples": n_samples},
                    assumptions={
                        "null_basis": "null_scrub" if values_are_scrubbed else "declared NULL only",
                        "declared_null": declared_null,
                        "null_scrub_detail": null_basis,
                    },
                    flags=tuple(lower_bound_flag),
                ),
                depth_range=depth_range,
                all_null=all_null,
                flags=tuple(curve_flags),
            )
        )

    # Evidence that the index may not be column 0 — reported, never acted on.
    if index_col == 0 and direction == "non-monotonic":
        for col, (values, _n, _f, _t) in enumerate(columns):
            if col == index_col:
                continue
            live = [v for v in values if v is not None]
            if len(live) > 1 and _monotone_direction(
                [b - a for a, b in zip(live, live[1:])]
            ) in ("increasing", "decreasing"):
                file_flags.append(
                    f"column 0 {mnemonics[0]!r} is not monotonic but column {col} "
                    f"{mnemonics[col]!r} is; the index may not be the first column. "
                    "Pass index_mnemonic to re-frame — this tool will not guess."
                )
                break

    return CurveInventory(
        curves=tuple(records_out),
        index_mnemonic=mnemonics[index_col],
        index_unit=index_unit,
        n_samples=n_samples,
        logged_interval=logged_interval,
        step=step,
        gaps=tuple(gaps),
        direction=direction,
        source=LAS_KGS,
        flags=tuple(file_flags),
        assumptions={
            "values_are_scrubbed": values_are_scrubbed,
            "declared_null": declared_null,
            "declared_start": declared_start,
            "declared_stop": declared_stop,
            "declared_step": declared_step,
            "gap_factor": gap_factor,
            "gap_factor_basis": "house rule; the corpus supplies no gap threshold",
            "step_tol_frac": step_tol_frac,
            "index_from": "caller" if index_mnemonic else "first column, per the source",
            "null_scrub_detail": null_basis,
        },
    )


# ---------------------------------------------------------------------------
# parse -> inventory
# The three tools above were specified separately and their shapes did not meet:
# las_parse returns curve definitions and columns side by side, curve_inventory
# wants one record per curve carrying its own values. The join is here rather
# than at every call site, and it is the only place that knows both shapes.
# ---------------------------------------------------------------------------
def curve_inventory_from_las(
    las_file: "LasFile",
    *,
    scrubbed_columns: "Sequence[Sequence[Any]] | None" = None,
    null_basis: Any = None,
    **kw: Any,
):
    """Inventory the curves of a parsed LAS file.

    `las_parse` does not resolve nulls - a declared-NULL cell arrives as the
    file's own number - so with raw columns this reports `values_are_scrubbed`
    False and every null fraction is a lower bound, exactly as the source's own
    "Common Null Values are -999.25, -9999, etc." warns. Pass `null_scrub`'s
    output as `scrubbed_columns` to get the real fractions; the flag then says
    so rather than the caller having to remember which it asked for.
    """
    if isinstance(las_file, Refusal):
        return las_file
    columns = tuple(scrubbed_columns) if scrubbed_columns is not None else las_file.columns
    if len(columns) != len(las_file.curves):
        return Refusal(
            reason=(
                f"{len(las_file.curves)} curves declared in ~C but {len(columns)} columns "
                "supplied; the ~C-order join would assign values to the wrong curve"
            ),
            needed=("one column per ~C entry, in ~C order",),
            source=KGS_LAS20,
        )
    records = [
        {
            "mnemonic": c.mnemonic,
            "unit": c.unit,
            "description": c.description,
            "values": list(values),
        }
        for c, values in zip(las_file.curves, columns)
    ]

    def _num(mnemonic: str) -> float | None:
        raw = las_file.header_value(mnemonic, section="well")
        try:
            return None if raw in (None, "") else float(str(raw).strip())
        except ValueError:
            return None

    defaults = {
        "declared_null": las_file.null_value,
        "declared_start": _num("STRT"),
        "declared_stop": _num("STOP"),
        "declared_step": _num("STEP"),
        # No depth_unit default: curve_inventory already falls back to the index
        # curve's own ~C unit, which is right whether or not the index is column
        # 0. Defaulting it from curves[0] would stamp column 0's unit onto a
        # named index elsewhere in the file - feet labelled as metres, silently.
    }
    for key, value in defaults.items():
        kw.setdefault(key, value)
    return curve_inventory(
        records,
        values_are_scrubbed=scrubbed_columns is not None,
        null_basis=null_basis,
        **kw,
    )
