"""Export: LAS 2.0 writer (#75) and zone-evaluation sheet (#76).

Two tools that leave the building. Everything else in this layer computes; these
two hand something to the operator, which is why both are written to refuse more
readily than they emit.

**`export_las` is the only writer in the catalog.** Its rules come from
`02-las-format/kgs-las-2.0-field-table#1` and are pinned in
`specs/75-export_las.md` (R1-R9). Two of them are worth restating here because
they look like fussiness and are not:

*Fixed point or nothing.* The source: "All values in the ASCII log data section
must be floating point or integer (long) values. Other formats such as Text or
Exponential values are not supported." Python's default float formatting emits
`1e-05` and `1.7e+16`, so the temptation when a value will not fit a `%.4f`
field is to reach for `%g`. That produces a file most readers accept and some
mis-parse. A value that cannot be written in fixed point without lying — an
infinity, a magnitude past 1e12, a nonzero sample that would round to `0.0000` —
is refused instead.

*The whole file is validated before any of it is written.* A half-written LAS on
disk is a file the operator can still open, which is worse than no file. The
image is assembled and checked in memory, and only a clean image reaches the
filesystem.

`welly` and `lasio` are deliberately not imported: neither is installed here, and
a spec-conformance writer that delegates its formatting to a library cannot
enforce a rule the library does not have.

**`export_sheet` is a serialiser, not a report generator.** `well-log-agent.md`
deleted `sheet_render` because "a sheet rendered from the state object ahead of
the model is a second, independent account of the same well - and two
internally-correct accounts that disagree is exactly the failure this system
exists to prevent" (`well-log-agent.md:418-421`). What survives runs *after* the
prose, carries the prose verbatim as its first section, and generates no wording
of its own. `requested` therefore has no default: a caller that never considered
whether the operator asked for a sheet gets a `TypeError`, not a document.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .result import Quantity, Refusal

# --- sources -----------------------------------------------------------------
LAS_SOURCE = "02-las-format/kgs-las-2.0-field-table#1"
SHEET_SOURCE = "well-log-agent.md:414 (render waits on the model)"

# --- LAS constants -----------------------------------------------------------
# "Common Null Values are -999.25, -9999, etc." - the first one the source names.
DEFAULT_NULL = -999.25
LAS_VERSION = "2.0"
# Fixed point past this many digits is not a curve value, it is a unit error.
MAX_FIXED_MAGNITUDE = 1e12
# Relative slack on the uniform-step check: enough for float accumulation in a
# generated index, tight enough to catch a spliced log.
STEP_TOLERANCE = 1e-6

# ~V required fields, source R2.
VERSION_FIELDS = (
    ("VERS", "", LAS_VERSION, "CWLS log ASCII Standard -VERSION 2.0"),
    ("WRAP", "", "NO", "One line per depth step"),
)

# ~W required fields in the source's own order, with the source's descriptions.
# STRT/STOP/STEP/NULL are computed; the rest are caller-supplied descriptive
# fields that may be blank (spec R3).
INDEX_FIELDS = (
    ("STRT", "Start Depth"),
    ("STOP", "Stop Depth"),
    ("STEP", "Step Depth"),
)
NULL_DESCRIPTION = "Null Value; Common Null Values are -999.25, -9999, etc."
DESCRIPTIVE_FIELDS = (
    ("COMP", "Company Name"),
    ("WELL", "Well Name"),
    ("FLD", "Field Name"),
    ("LOC", "Well Location"),
    ("PROV", "Province; Canadian"),
    ("CTRY", "Country; Outside Canada"),
    ("STAT", "State"),
    ("CNTY", "County"),
    ("UWI", "Unique Well ID; Within Canada 16 character string"),
    ("API", "API-Number"),
    ("SRVC", "Logging Company"),
    ("LIC", "Regulatory Licence Number"),
    # The source prints "prefferred"; the typo is the KGS page's, not the
    # standard's, and is not worth exporting into every file we write.
    ("DATE", "Date logged, preferred date MM/DD/YYYY"),
)
# Any one of these present satisfies well-log-agent.md:269 - a LAS file is an
# array of depths, and depths with no well identity are the bare depths that
# rule forbids.
IDENTITY_FIELDS = ("WELL", "API", "UWI")


# --- input types -------------------------------------------------------------
@dataclass(frozen=True)
class LasCurve:
    """One column of a LAS file, with the provenance of how it was produced.

    `samples` accepts `Quantity` objects so a curve assembled from per-depth tool
    results carries its own method and source without the caller restating them.
    An absent sample is `None` or a float nan and becomes the file's NULL value.
    """

    mnemonic: str
    unit: str
    samples: Sequence[Any]
    method: str = ""
    source: str = ""
    description: str = ""
    decimals: int = 4
    inputs: Mapping[str, Any] = field(default_factory=dict)
    assumptions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.mnemonic, str) or not self.mnemonic.strip():
            raise ValueError("a LAS curve needs a non-empty string mnemonic")
        if not isinstance(self.decimals, int) or self.decimals < 0:
            raise ValueError(f"{self.mnemonic}: decimals must be a non-negative int")
        if isinstance(self.samples, (str, bytes)):
            raise ValueError(f"{self.mnemonic}: samples must be a sequence of numbers")


@dataclass(frozen=True)
class LasParameter:
    """One ~P line: a constant relevant to the wellbore."""

    mnemonic: str
    unit: str
    value: Any
    description: str = ""


# --- LAS helpers -------------------------------------------------------------
def _refuse_las(reason: str, *needed: str) -> Refusal:
    return Refusal(reason=reason, needed=tuple(needed), source=LAS_SOURCE)


def _delimiter_problem(label: str, text: str, *, allow_period: bool) -> str | None:
    """Spec R4. The corpus shows the four-field line layout but never says how a
    reader resolves a period or colon *inside* a field, so we forbid the
    ambiguity rather than bet on 'first period / last colon'."""
    if ":" in text:
        return f"{label} contains ':', the description delimiter: {text!r}"
    if not allow_period and "." in text:
        return f"{label} contains '.', the unit delimiter: {text!r}"
    if re.search(r"\s", text):
        return f"{label} contains whitespace, which separates the fields: {text!r}"
    return None


def _is_absent(value: Any) -> bool:
    if value is None:
        return True
    return isinstance(value, float) and math.isnan(value)


def _canonical(value: Any) -> str:
    """Order-independent text for one input value, for the agreement test below."""
    return json.dumps(value, sort_keys=True, default=str)


def _agreeing(dicts: list[Mapping[str, Any]]) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Split per-sample provenance dicts into what every sample agrees on and what
    varies along the curve.

    A curve is one column of many samples, so its inputs are not one dict: the
    bulk density behind a density porosity changes every half foot while the
    matrix density behind it does not. The constants are the assumption an
    operator argues with (Asquith's 2.644 against the AAPG table's 2.65 is about
    a porosity unit), so they are written; the varying ones are named rather than
    written, because writing one sample's value as if it held for the column
    would be a false statement about the curve.
    """
    if not dicts:
        return {}, ()
    shared = set(dicts[0])
    for d in dicts[1:]:
        shared &= set(d)
    constant: dict[str, Any] = {}
    varying: list[str] = []
    for key in sorted(shared, key=str):
        first = _canonical(dicts[0][key])
        if all(_canonical(d[key]) == first for d in dicts[1:]):
            constant[key] = dicts[0][key]
        else:
            varying.append(str(key))
    for key in {k for d in dicts for k in d} - shared:
        varying.append(str(key))
    return constant, tuple(sorted(varying))


@dataclass(frozen=True)
class _Unwrapped:
    """One curve's samples as plain floats, with whatever provenance they carry."""

    values: list[float | None] = field(default_factory=list)
    method: str = ""
    source: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    varying_inputs: tuple[str, ...] = ()
    varying_assumptions: tuple[str, ...] = ()
    derived: bool = False
    error: str | None = None


def _unwrap_samples(curve: LasCurve) -> _Unwrapped:
    """Unwrap a curve's samples, and read the provenance off them.

    `Quantity` samples carry `method`, `source`, `inputs` and `assumptions`
    (`tools/result.py:22-29`). All four are taken from the samples when the curve
    does not declare them, so a curve assembled from per-depth tool results
    reaches the file with the equation, the anchor *and* the constants that
    produced it - `well-log-agent.md:270`, "Every value in `computed` carries its
    inputs and method. No orphan numbers."
    """
    values: list[float | None] = []
    methods: set[str] = set()
    sources: set[str] = set()
    sample_inputs: list[Mapping[str, Any]] = []
    sample_assumptions: list[Mapping[str, Any]] = []
    for i, raw in enumerate(curve.samples):
        if isinstance(raw, Quantity):
            if raw.unit != curve.unit:
                return _Unwrapped(error=(
                    f"{curve.mnemonic}: sample {i} is in {raw.unit!r} but the curve "
                    f"is declared {curve.unit!r}"
                ))
            methods.add(raw.method)
            sources.add(raw.source)
            sample_inputs.append(raw.inputs or {})
            sample_assumptions.append(raw.assumptions or {})
            values.append(None if _is_absent(raw.value) else float(raw.value))
            continue
        if _is_absent(raw):
            values.append(None)
            continue
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            return _Unwrapped(error=(
                f"{curve.mnemonic}: sample {i} is {type(raw).__name__}, not a number"
            ))
        values.append(float(raw))

    method = curve.method
    source = curve.source
    derived = False
    if not method and len(methods) == 1:
        method = next(iter(methods))
        derived = True
    if not source and len(sources) == 1:
        source = next(iter(sources))
        derived = True

    inputs = dict(curve.inputs)
    varying_inputs: tuple[str, ...] = ()
    if not inputs and sample_inputs:
        inputs, varying_inputs = _agreeing(sample_inputs)
        derived = derived or bool(inputs) or bool(varying_inputs)
    assumptions = dict(curve.assumptions)
    varying_assumptions: tuple[str, ...] = ()
    if not assumptions and sample_assumptions:
        assumptions, varying_assumptions = _agreeing(sample_assumptions)
        derived = derived or bool(assumptions) or bool(varying_assumptions)

    return _Unwrapped(values=values, method=method, source=source, inputs=inputs,
                      assumptions=assumptions, varying_inputs=varying_inputs,
                      varying_assumptions=varying_assumptions, derived=derived)


def _format_fixed(value: float, decimals: int) -> tuple[str, str | None]:
    """Spec R6.4. Fixed point, or a stated reason why it cannot be."""
    if math.isinf(value):
        return "", "is infinite, which fixed-point notation cannot express"
    magnitude = abs(value)
    if magnitude >= MAX_FIXED_MAGNITUDE:
        return "", (
            f"is {value!r}: at or past 1e12 it can only be written in exponential "
            "notation, which the LAS 2.0 data section forbids"
        )
    if magnitude > 0 and magnitude < 0.5 * 10.0 ** (-decimals):
        return "", (
            f"is {value!r}: at {decimals} decimals it would be written 0."
            + "0" * decimals
            + ", turning a real sample into zero"
        )
    text = f"{value:.{decimals}f}"
    if "e" in text or "E" in text:  # belt and braces; %f should never do this
        return "", f"formatted as {text!r}, which is exponential notation"
    return text, None


def _header_line(mnemonic: str, unit: str, value: str, description: str) -> str:
    """`MNEM.UNIT   VALUE : DESCRIPTION` - spec R4.

    The period sits immediately after the mnemonic, never after padding: a reader
    taking "everything left of the first period" as the mnemonic must not have to
    strip trailing spaces to get `VERS`.
    """
    head = f"{mnemonic}.{unit}".ljust(20)
    return f"{head} {value:<28} : {description}".rstrip()


def _stringify(value: Any) -> str:
    if isinstance(value, float):
        return repr(value)
    return str(value)


# --- #75 export_las ----------------------------------------------------------
def export_las(
    path: str | pathlib.Path,
    index: LasCurve,
    curves: Sequence[LasCurve],
    well: Mapping[str, Any],
    *,
    null_value: float = DEFAULT_NULL,
    parameters: Sequence[LasParameter] = (),
    datum: Mapping[str, Any] | None = None,
    other: str = "",
    wrap: bool = False,
) -> Quantity | Refusal:
    """Write computed curves out as a LAS 2.0 file. See `specs/75-export_las.md`.

    Returns a `Quantity` counting the data rows written, or a `Refusal` - in
    which case nothing has been written and any pre-existing file at `path` is
    untouched.
    """
    target = pathlib.Path(path)
    if not target.parent.exists():
        raise ValueError(f"parent directory does not exist: {target.parent}")
    if not isinstance(index, LasCurve):
        raise ValueError("index must be a LasCurve")
    curves = list(curves)
    if not curves:
        raise ValueError("export_las needs at least one curve besides the index")
    for curve in curves:
        if not isinstance(curve, LasCurve):
            raise ValueError("every entry in curves must be a LasCurve")
        if len(curve.samples) != len(index.samples):
            raise ValueError(
                f"{curve.mnemonic} has {len(curve.samples)} samples but the index "
                f"has {len(index.samples)}"
            )
    if not isinstance(well, Mapping):
        raise ValueError("well must be a mapping of ~W mnemonic to value")

    flags: list[str] = []

    # R2 - the corpus states the semantics of WRAP NO only.
    if wrap:
        return _refuse_las(
            "wrapped output refused: the corpus states the meaning of WRAP=NO "
            '("One line per depth step") and gives NO as the required ~V value; '
            "it does not carry the rules for writing a wrapped file",
            "call again with wrap=False",
            "acquire the CWLS LAS 2.0 specification to support WRAP=YES",
        )

    # R7 - the NULL value itself must be writable, and written identically in
    # every column. One text for all columns, at whatever precision represents it
    # exactly: a curve at decimals=0 must not write its nulls as "-999".
    if not isinstance(null_value, (int, float)) or not math.isfinite(null_value):
        return _refuse_las(f"null_value {null_value!r} is not a finite number")
    null_value = float(null_value)
    null_text = ""
    for places in range(0, 11):
        candidate, null_error = _format_fixed(null_value, places)
        if null_error:
            return _refuse_las(f"null_value {null_error}")
        if float(candidate) == null_value:
            null_text = candidate
            break
    if not null_text:
        return _refuse_las(
            f"null_value {null_value!r} cannot be written exactly in fixed point at "
            "ten or fewer decimals",
            "a null value such as -999.25",
        )

    # --- index integrity, R9 ---
    unwrapped_index = _unwrap_samples(index)
    if unwrapped_index.error:
        return _refuse_las(unwrapped_index.error)
    index_values = unwrapped_index.values
    if len(index_values) < 2:
        return _refuse_las(
            f"the index has {len(index_values)} sample(s); STEP is undefined below two",
            "an index of at least two samples",
        )
    if any(v is None for v in index_values):
        first = next(i for i, v in enumerate(index_values) if v is None)
        return _refuse_las(
            f"index sample {first} is absent; the index defines the rows and "
            "cannot be NULL-substituted",
            "an index with no absent samples",
        )
    step = index_values[1] - index_values[0]
    if step == 0:
        return _refuse_las("the index does not advance: STEP would be zero")
    tolerance = abs(step) * STEP_TOLERANCE
    for i in range(1, len(index_values)):
        this_step = index_values[i] - index_values[i - 1]
        if this_step * step <= 0:
            return _refuse_las(
                f"the index is not monotonic at sample {i} "
                f"({index_values[i - 1]!r} -> {index_values[i]!r})",
                "a strictly monotonic index",
            )
        if abs(this_step - step) > tolerance:
            return _refuse_las(
                f"the index is not uniformly stepped: step {step!r} at sample 1 but "
                f"{this_step!r} at sample {i}. LAS 2.0 carries one STEP field and the "
                "corpus does not state how to write an irregular index",
                "a uniformly stepped index",
                "or resample before export",
            )

    # --- mnemonic uniqueness, R5 ---
    seen: dict[str, str] = {}
    for curve in (index, *curves):
        key = curve.mnemonic.strip().casefold()
        if key in seen:
            return _refuse_las(
                f"duplicate curve mnemonic {curve.mnemonic!r} (also {seen[key]!r}): a "
                "reader keying curves by mnemonic would silently drop one",
                "distinct mnemonics for every column",
            )
        seen[key] = curve.mnemonic

    # --- per-curve provenance and delimiters, R4 + R7 ---
    columns: list[tuple[LasCurve, _Unwrapped]] = []
    for curve in (index, *curves):
        unwrapped = _unwrap_samples(curve)
        if unwrapped.error:
            return _refuse_las(unwrapped.error)
        values, method, source = unwrapped.values, unwrapped.method, unwrapped.source
        if not method or not source:
            return _refuse_las(
                f"{curve.mnemonic} carries no {'method' if not method else 'source'}: "
                "an exported curve with no stated method is an orphan number in a file "
                "the operator will trust",
                f"{curve.mnemonic}.method and {curve.mnemonic}.source",
                "or samples that are Quantity objects carrying both",
            )
        if unwrapped.derived and "provenance-derived-from-samples" not in flags:
            flags.append("provenance-derived-from-samples")
        for label, text, allow_period in (
            ("mnemonic", curve.mnemonic.strip(), False),
            ("unit", curve.unit, False),
            ("description", curve.description, True),
            ("method", method, True),
        ):
            problem = _delimiter_problem(
                f"{curve.mnemonic} {label}",
                text,
                allow_period=allow_period,
            )
            # A description or a method is prose; whitespace in it is fine, only
            # the ':' delimiter is not.
            if problem and label in ("description", "method") and "whitespace" in problem:
                problem = None
            if problem:
                return _refuse_las(problem, "remove the delimiter character")
        columns.append((curve, unwrapped))

    # --- ~W descriptive fields, R3 + R8 ---
    well_values: dict[str, str] = {}
    blank: list[str] = []
    for mnemonic, description in DESCRIPTIVE_FIELDS:
        raw = well.get(mnemonic, well.get(mnemonic.lower(), ""))
        text = "" if raw is None else _stringify(raw).strip()
        if text:
            problem = _delimiter_problem(f"~W {mnemonic}", text, allow_period=True)
            if problem and "whitespace" in problem:
                problem = None  # a well name may contain spaces
            if problem:
                return _refuse_las(problem, f"a ~W {mnemonic} value without ':'")
        else:
            blank.append(mnemonic)
        well_values[mnemonic] = text
    if not any(well_values[m] for m in IDENTITY_FIELDS):
        return _refuse_las(
            "the file would carry depths with no well identity: WELL, API and UWI are "
            "all blank (well-log-agent.md:269 - every depth carries well.api)",
            "one of WELL, API or UWI",
        )
    if blank:
        flags.append("blank-required-fields: " + ", ".join(blank))

    # --- data section, R6 ---
    formatted: list[list[str]] = []
    nulls: dict[str, int] = {}
    for curve, unwrapped in columns:
        values = unwrapped.values
        column: list[str] = []
        null_count = 0
        for row, value in enumerate(values):
            if value is None:
                column.append(null_text)
                null_count += 1
                continue
            text, error = _format_fixed(value, curve.decimals)
            if error:
                return _refuse_las(
                    f"{curve.mnemonic} sample {row} (index {index_values[row]!r}) {error}",
                    "a larger `decimals` on the curve, or corrected units",
                )
            if float(text) == null_value:
                return _refuse_las(
                    f"{curve.mnemonic} sample {row} writes as {text!r}, which a reader "
                    "cannot tell from the file's NULL value: a real sample would be "
                    "read as absent",
                    "a different null_value",
                )
            column.append(text)
        nulls[curve.mnemonic] = null_count
        if null_count == len(values):
            flags.append(f"all-null-curve: {curve.mnemonic}")
        formatted.append(column)

    # --- assemble the file image (nothing is written until it is complete) ---
    lines: list[str] = []

    # ~V, first section (R1).
    lines.append("~Version Information")
    for mnemonic, unit, value, description in VERSION_FIELDS:
        lines.append(_header_line(mnemonic, unit, value, description))

    # ~W, second section (R1), all seventeen required mnemonics (R3).
    lines.append("~Well Information")
    strt_text, _ = _format_fixed(index_values[0], index.decimals)
    stop_text, _ = _format_fixed(index_values[-1], index.decimals)
    step_text, step_error = _format_fixed(step, index.decimals)
    if step_error:
        return _refuse_las(f"the index STEP {step_error}", "a coarser index")
    for (mnemonic, description), value in zip(
        INDEX_FIELDS, (strt_text, stop_text, step_text)
    ):
        lines.append(_header_line(mnemonic, index.unit, value, description))
    lines.append(_header_line("NULL", "", null_text, NULL_DESCRIPTION))
    for mnemonic, description in DESCRIPTIVE_FIELDS:
        lines.append(_header_line(mnemonic, "", well_values[mnemonic], description))

    # ~C, in data-section order (R5).
    lines.append("~Curve Information")
    for curve, unwrapped in columns:
        method = unwrapped.method
        description = curve.description or curve.mnemonic.strip()
        lines.append(
            _header_line(curve.mnemonic.strip(), curve.unit, "", f"{description} [{method}]")
        )

    # ~P, optional (R1). Datum first, since it is what a depth is measured from.
    parameter_lines: list[str] = []
    if datum:
        for mnemonic in ("EKB", "EGL", "EPD"):
            if mnemonic in datum and datum[mnemonic] is not None:
                text, error = _format_fixed(float(datum[mnemonic]), 2)
                if error:
                    return _refuse_las(f"datum {mnemonic} {error}")
                parameter_lines.append(
                    _header_line(mnemonic, index.unit, text, f"{mnemonic} elevation")
                )
    for parameter in parameters:
        if not isinstance(parameter, LasParameter):
            raise ValueError("every entry in parameters must be a LasParameter")
        value_text = _stringify(parameter.value)
        for label, text, allow_period in (
            ("mnemonic", parameter.mnemonic, False),
            ("unit", parameter.unit, False),
            ("value", value_text, True),
            ("description", parameter.description, True),
        ):
            problem = _delimiter_problem(f"~P {parameter.mnemonic} {label}", text, allow_period=allow_period)
            if problem and label in ("value", "description") and "whitespace" in problem:
                problem = None
            if problem:
                return _refuse_las(problem, "remove the delimiter character")
        parameter_lines.append(
            _header_line(parameter.mnemonic, parameter.unit, value_text, parameter.description)
        )
    if parameter_lines:
        lines.append("~Parameter Information")
        lines.extend(parameter_lines)

    # ~O, free-form: the provenance block (R7). This is the one section with "no
    # formatting requirements", so a corpus anchor can be written verbatim.
    lines.append("~Other")
    lines.append("Curve provenance - how each column was produced and from what source.")
    for curve, unwrapped in columns:
        role = "index" if curve is index else "curve"
        lines.append(f"  {curve.mnemonic.strip()} ({role}) unit={curve.unit or '-'}")
        lines.append(f"    method: {unwrapped.method}")
        lines.append(f"    source: {unwrapped.source}")
        if unwrapped.inputs:
            lines.append(
                f"    inputs: {json.dumps(unwrapped.inputs, sort_keys=True, default=str)}")
        if unwrapped.varying_inputs:
            # Named, not written: one sample's rho_b does not hold for the column.
            lines.append(
                "    inputs varying per sample: " + ", ".join(unwrapped.varying_inputs))
        if unwrapped.assumptions:
            lines.append(
                f"    assumptions: {json.dumps(unwrapped.assumptions, sort_keys=True, default=str)}"
            )
        if unwrapped.varying_assumptions:
            lines.append(
                "    assumptions varying per sample: "
                + ", ".join(unwrapped.varying_assumptions))
        lines.append(f"    absent samples written as NULL: {nulls[curve.mnemonic]}")
    if datum:
        reference = datum.get("reference")
        lines.append(
            "  depth reference: "
            + (str(reference) if reference else "not stated by the caller")
        )
    else:
        flags.append("datum-not-recorded")
        lines.append("  depth reference: not supplied; depths are as recorded in the source log")
    if other:
        for line in str(other).splitlines():
            lines.append(f"  {line}")

    # ~A, last section (R1). Index first, at least one space between columns (R6).
    lines.append("~ASCII")
    widths = [
        max(len(curve.mnemonic.strip()), max(len(text) for text in column))
        for (curve, _unwrapped), column in zip(columns, formatted)
    ]
    for row in range(len(index_values)):
        lines.append(
            " ".join(
                formatted[col][row].rjust(widths[col]) for col in range(len(columns))
            ).rstrip()
        )

    image = "\n".join(lines) + "\n"
    # The encoding is part of the image check, not part of the write. Encoding at
    # the filesystem, as `write_text` does, opens and truncates the target first:
    # a well name carrying a degree sign would then destroy the operator's
    # existing file and raise, which is the half-written outcome this tool is
    # built to avoid.
    try:
        encoded = image.encode("ascii")
    except UnicodeEncodeError as exc:
        offender = image[exc.start:exc.end]
        return _refuse_las(
            f"the file image carries the non-ASCII character {offender!r}, which the "
            "Log ASCII Standard cannot represent; it came from a caller-supplied "
            "field (a ~W value, a curve description or ~O text)",
            "ASCII-only text in the well header, curve descriptions and ~O block",
        )
    target.write_bytes(encoded)

    return Quantity(
        value=float(len(index_values)),
        unit="rows",
        method="export_las LAS 2.0 writer v1 (WRAP=NO, fixed-point)",
        source=LAS_SOURCE,
        inputs={
            "path": str(target),
            "index": index.mnemonic.strip(),
            "curves": [curve.mnemonic.strip() for curve, _unwrapped in columns[1:]],
            "null_value": float(null_value),
            "nulls_written": nulls,
            "strt": index_values[0],
            "stop": index_values[-1],
            "step": step,
            "bytes": len(encoded),
        },
        assumptions={
            "wrap": "NO",
            "vers": LAS_VERSION,
            "number_format": "fixed-point, %.Nf per curve; exponential notation refused",
            "absent_samples": "written as NULL, never interpolated, extrapolated or dropped",
            "section_order": "~V, ~W, ~C, ~P, ~O, ~A",
        },
        flags=tuple(flags),
    )


# --- #76 export_sheet --------------------------------------------------------
_SHEET_SECTIONS = (
    "well",
    "datum",
    "interval",
    "curves",
    "computed",
    "assumptions",
    "offsets",
    "evidence",
    "conflicts",
    "open",
)
_SECTION_TITLES = {
    "well": "Well",
    "datum": "Datum",
    "interval": "Interval",
    "curves": "Curves",
    "computed": "Computed",
    "assumptions": "Assumptions",
    "offsets": "Offsets",
    "evidence": "Evidence",
    "conflicts": "Conflicts",
    "open": "Open",
}
_NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _refuse_sheet(reason: str, *needed: str) -> Refusal:
    return Refusal(reason=reason, needed=tuple(needed), source=SHEET_SOURCE)


def _fields_of(value: Any) -> dict[str, Any] | None:
    """A result object's own fields, or None if it is not one.

    `computed` entries reach this tool as `Quantity`, `Range` and `Refusal`
    objects as often as they reach it as mappings - that is what the rest of the
    layer reads (`tools/state_checks.py:183`: "Read a field from a mapping, a
    Quantity/Range/Refusal, or a mapping that wraps one"), and it is what the
    harness's tool ledger holds, "its output as returned"
    (`harness-implementation.md:178`). Their field order is fixed by the class,
    so the coercion is deterministic and C7 still holds.
    """
    if isinstance(value, type) or not dataclasses.is_dataclass(value):
        return None
    return {f.name: getattr(value, f.name) for f in dataclasses.fields(value)}


def _jsonable(value: Any) -> Any:
    """`json.dumps` hook. Coerces the layer's own result objects and refuses the
    rest, so refusal 5 still fires on a state no deterministic digest can cover."""
    fields = _fields_of(value)
    if fields is None:
        raise TypeError(f"{type(value).__name__} is not canonically serialisable")
    return fields


def _canonical_json(state: Mapping[str, Any]) -> str:
    return json.dumps(state, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), default=_jsonable)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _render_default(value: Any) -> Any:
    fields = _fields_of(value)
    return str(value) if fields is None else fields


def _cell(value: Any) -> str:
    """A markdown-table-safe rendering of a state value. Verbatim: no rounding,
    no unit conversion, no rewording (spec C2)."""
    if isinstance(value, str):
        text = value
    elif isinstance(value, bool) or value is None:
        text = json.dumps(value)
    elif isinstance(value, float):
        text = repr(value)
    elif isinstance(value, (int,)):
        text = str(value)
    else:
        text = json.dumps(value, sort_keys=True, ensure_ascii=False,
                          default=_render_default)
    return text.replace("|", r"\|").replace("\n", " ")


def _walk_numbers(node: Any, path: str) -> Iterable[tuple[str, float]]:
    """Every number in the state, including numbers written inside its strings."""
    if isinstance(node, bool):
        return
    if isinstance(node, (int, float)):
        if isinstance(node, float) and not math.isfinite(node):
            return
        yield path, float(node)
        return
    if isinstance(node, str):
        for match in _NUMBER.finditer(node):
            try:
                yield path, float(match.group().replace(",", ""))
            except ValueError:  # pragma: no cover - regex cannot produce this
                continue
        return
    if isinstance(node, Mapping):
        for key in sorted(node, key=str):
            yield from _walk_numbers(node[key], f"{path}.{key}")
        return
    if isinstance(node, (list, tuple)):
        for i, item in enumerate(node):
            yield from _walk_numbers(item, f"{path}[{i}]")
        return
    fields = _fields_of(node)
    if fields is not None:
        # A `Quantity` in `computed` is where the layer's numbers actually live;
        # a prose figure quoting one has to trace to it (C6 step 2 walks "the
        # whole state object: every int and float at any depth").
        yield from _walk_numbers(fields, path)


def _render_mapping(title: str, node: Mapping[str, Any]) -> tuple[list[str], int]:
    lines = [f"## {title}", "", "| Field | Value |", "| --- | --- |"]
    count = 0
    for key in sorted(node, key=str):
        lines.append(f"| {_cell(key)} | {_cell(node[key])} |")
        count += 1
    lines.append("")
    return lines, count


def _render_list(title: str, node: Sequence[Any]) -> tuple[list[str], int]:
    lines = [f"## {title}", ""]
    for i, entry in enumerate(node):
        lines.append(f"### {title} [{i}]")
        lines.append("")
        fields = None if isinstance(entry, Mapping) else _fields_of(entry)
        if isinstance(entry, Mapping) or fields is not None:
            record = dict(entry) if fields is None else fields
            lines.append("| Field | Value |")
            lines.append("| --- | --- |")
            if fields is not None:
                # A refusal has to read as a refusal. Rendered as bare fields it
                # is a row of prose an operator can mistake for a value, and the
                # one thing this tool must never do is let a declined answer look
                # like an answered one.
                lines.append(f"| (record type) | {type(entry).__name__} |")
            for key in sorted(record, key=str):
                value = record[key]
                rendered = _cell(value) if value not in ("", None) else "(empty)"
                lines.append(f"| {_cell(key)} | {rendered} |")
        else:
            lines.append(f"`{_cell(entry)}`")
        lines.append("")
    return lines, len(node)


def export_sheet(
    state: Mapping[str, Any],
    *,
    requested: bool,
    answer: str,
    answer_state_digest: str | None = None,
    path: str | pathlib.Path | None = None,
) -> Quantity | Refusal:
    """Serialise a zone evaluation as a filable document. See
    `specs/76-export_sheet.md`.

    `requested` is keyword-only with no default on purpose: the sheet is produced
    on explicit operator request only, and a caller that has not considered the
    question gets a `TypeError` rather than a document.
    """
    if not isinstance(state, Mapping):
        raise ValueError("state must be a mapping (the ZoneEvaluation)")
    if not isinstance(answer, str):
        raise ValueError("answer must be the prose string already delivered")
    target = pathlib.Path(path) if path is not None else None
    if target is not None and not target.parent.exists():
        raise ValueError(f"parent directory does not exist: {target.parent}")

    # C3 - explicit request, and literally True.
    if requested is not True:
        return _refuse_sheet(
            "sheet not explicitly requested - export_sheet renders on explicit "
            f"operator request only (requested={requested!r})",
            "requested=True, set because the operator asked for a sheet",
        )
    # C4 - never ahead of the answer.
    if not answer.strip():
        return _refuse_sheet(
            "no answer has been delivered; the sheet may not precede the prose "
            "(well-log-agent.md:414 - render waits on the model)",
            "the answer text that was streamed to the operator",
        )

    # C5 - state identity.
    try:
        canonical = _canonical_json(state)
    except (TypeError, ValueError) as exc:
        return _refuse_sheet(
            f"state is not canonically serialisable, so no state identity can be "
            f"established: {exc}",
            "a JSON-serialisable state object",
        )
    state_digest = _digest(canonical)
    answer_digest = _digest(answer)

    well = state.get("well") if isinstance(state.get("well"), Mapping) else {}
    state_id = ""
    for candidate in (well.get("api"), well.get("name"), state.get("file_hash")):
        if candidate:
            state_id = str(candidate)
            break
    if not state_id:
        return _refuse_sheet(
            "state identity unresolvable - a sheet that cannot name its well cannot "
            "be filed (no well.api, no well.name, no file_hash)",
            "well.api",
            "or well.name",
            "or file_hash",
        )

    flags: list[str] = []
    revision = state.get("revision", state.get("version"))
    if revision is None:
        revision_text = "not carried by state"
        flags.append("state-revision-not-carried")
    else:
        revision_text = _cell(revision)

    if answer_state_digest is None:
        flags.append("answer-digest-unverified")
    elif answer_state_digest != state_digest:
        return _refuse_sheet(
            f"state changed after the answer: answer was derived from state "
            f"{answer_state_digest}, this sheet would be derived from state "
            f"{state_digest}. Two accounts of the same well from two different states "
            "is the divergence this tool exists to prevent",
            "the state the answer was derived from",
            "or a fresh answer derived from the current state",
        )

    # C6 - reconcile every figure in the prose against the state.
    state_numbers = list(_walk_numbers(state, "state"))
    reconciliation: list[dict[str, Any]] = []
    unreconciled = 0
    for match in _NUMBER.finditer(answer):
        token = match.group()
        try:
            figure = float(token.replace(",", ""))
        except ValueError:  # pragma: no cover
            continue
        decimals = len(token.split(".")[1]) if "." in token else 0
        matched_path = ""
        for candidate_path, candidate in state_numbers:
            if math.isclose(round(candidate, decimals), figure, rel_tol=1e-12, abs_tol=1e-12):
                matched_path = candidate_path
                break
        if matched_path:
            reconciliation.append({"figure": token, "status": "RECONCILED", "state_path": matched_path})
        else:
            reconciliation.append({"figure": token, "status": "UNRECONCILED", "state_path": ""})
            unreconciled += 1
    if unreconciled:
        flags.append(f"unreconciled-figures: {unreconciled}")

    # --- render (C1, C2) ---
    lines: list[str] = [
        "# Zone evaluation sheet",
        "",
        "Serialised from the state object the answer was derived from. Every value "
        "below is verbatim from that state; no wording in this document was generated.",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| State ID | {_cell(state_id)} |",
        f"| State digest | {state_digest} |",
        f"| State revision | {revision_text} |",
        f"| Answer digest | {answer_digest} |",
        f"| Answer state digest supplied | {_cell(answer_state_digest) if answer_state_digest else '(none)'} |",
        "",
        "## Answer as delivered",
        "",
    ]
    lines.extend(answer.rstrip("\n").split("\n"))
    lines.append("")

    records_by_section: dict[str, int] = {}
    total = 0
    for key in _SHEET_SECTIONS:
        title = _SECTION_TITLES[key]
        node = state.get(key)
        if node is None or (hasattr(node, "__len__") and len(node) == 0):
            lines.extend([f"## {title}", "", "(not present in state)", ""])
            records_by_section[key] = 0
            flags.append(f"empty-section: {key}")
            continue
        if isinstance(node, Mapping):
            block, count = _render_mapping(title, node)
        elif isinstance(node, (list, tuple)):
            block, count = _render_list(title, node)
        else:
            block, count = [f"## {title}", "", f"`{_cell(node)}`", ""], 1
        lines.extend(block)
        records_by_section[key] = count
        total += count

    extras = [key for key in sorted(state, key=str) if key not in _SHEET_SECTIONS]
    lines.extend(["## Unrecognised state fields", ""])
    if extras:
        lines.extend(["| Field | Value |", "| --- | --- |"])
        for key in extras:
            lines.append(f"| {_cell(key)} | {_cell(state[key])} |")
            total += 1
        records_by_section["unrecognised"] = len(extras)
    else:
        lines.append("(none)")
        records_by_section["unrecognised"] = 0
    lines.append("")

    lines.extend(
        [
            "## Reconciliation",
            "",
            "Every figure printed in the answer, traced to the state it came from. An "
            "UNRECONCILED figure appears in no part of this state.",
            "",
            "| Figure | Status | State path |",
            "| --- | --- | --- |",
        ]
    )
    if reconciliation:
        for row in reconciliation:
            lines.append(
                f"| {row['figure']} | {row['status']} | {row['state_path'] or '-'} |"
            )
    else:
        lines.append("| (no figures in the answer) | - | - |")
    lines.append("")

    sheet = "\n".join(lines)
    if target is not None:
        target.write_text(sheet, encoding="utf-8")

    return Quantity(
        value=float(total),
        unit="records",
        method="export_sheet state serialisation v1",
        source=SHEET_SOURCE,
        inputs={
            "state_digest": state_digest,
            "answer_digest": answer_digest,
            "state_id": state_id,
            "state_revision": revision_text,
            "path": str(target) if target is not None else None,
            "sheet": sheet,
            "records_by_section": records_by_section,
            "reconciliation": reconciliation,
        },
        assumptions={
            "requested": "explicit, True",
            "derivation": "serialised from the state the answer was derived from",
            "wording": "verbatim from state; no text generated",
            "reconciliation": "prose figure matches a state number rounded to the "
            "figure's own printed precision",
        },
        flags=tuple(flags),
    )
