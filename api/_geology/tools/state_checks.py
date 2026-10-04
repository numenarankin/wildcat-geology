"""State-object rule engines: conflict_detect (#65), gate_check (#66),
provenance_audit (#67).

All three read the `ZoneEvaluation` of `well-log-agent.md:254` - quoted in each
spec - and none of them calls a model. `well-log-agent.md:331` makes Stage 2's
*semantic* conflict pass a Sonnet agent because a fixed predicate list only
catches the shapes already thought of; these are the predicates that can be
decided without judgement, so that a model miss cannot silently pass a state
object that contradicts itself on its face. Where a listed conflict shape does
need judgement (offset projection versus log character), the tool says so in
`assumptions["rules_not_evaluated"]` rather than approximating it.

Four decisions here are not obvious from the code.

**Reading is liberal, judging is strict.** The state object arrives serialized
from a TypeScript harness, is assembled by concurrent branches, and its optional
sections are genuinely optional. So a missing section is never an error - but it
is never a pass either: every section that was not audited is named on the
result, because a clean result that means "there was nothing there" is worse than
a refusal.

**No threshold is defaulted.** `gate_check` has no washout cutoff. The catalog
does carry a PROVISIONAL one (DiffCal > 1.0 in, `tool-catalog.md:88`), and
`hole_quality` (#25) is the tool licensed to apply it and label it as a house
rule. A gate that decides whether a number reaches an operator is the last place
a house rule should be applied silently, so the cutoff is a caller argument and
its absence blocks. The one washout threshold that *is* sourced - DRHO > 0.20
g/cm3, `asquith#18` - is imported from `petrophysics.DRHO_SUSPECT` rather than
restated, so there is one copy of it in the repo.

**#25's verdict is consumed as #25 ships it.** `gate_check`'s hole-quality gate
reads `QualityInterval(top_ft, base_ft, verdict, gates, statuses)` - the shape
`hole_quality` (#25) actually returns - and carries its gate names and
SOURCED/PROVISIONAL statuses through to the refusal verbatim. It once assumed a
`{top_md, base_md, flag, gate}` shape nothing produces, and so reported "nothing
in the state object says whether this was logged through good hole" over a real
DRHO washout it had been handed. `tool-catalog.md:112` is the reason that matters:
the operator can argue with a house rule and not with a sourced one, but only if
the gate says which fired. A verdict of `good` is a pass; `unknown` never is.

**Anchors are resolved, not pattern-matched.** `provenance_audit` opens the
document and counts its segments with the same function `scripts/show_segment.py`
uses (`build_toc.segment`, via `tools.kb`). A citation that looks like an anchor
but does not open is indistinguishable from an invented one, and the whole
provenance contract rests on being able to tell those apart.

**Resolving is not the same as being about the claim.** Rule 11 exists because
three defects in three unrelated tool groups passed rules 1-10 clean while citing
the wrong passage (`agent1-findings.md:57-65`). It closes only the part of that
gap that is a substring test - the result quotes a sentence, and the cited
passage either contains it or does not - and no model is called. An *unquoted*
claim against its anchor is still judgement and is still uncovered; `specs/67`
says so under "What rule 11 still cannot catch", because a clean audit that is
read as "the citations are about the claims" is the failure this whole tool is
meant to prevent.
"""
from __future__ import annotations

import math
import os
import pathlib
import re
from typing import Any, Iterable, Mapping, Sequence

from . import petrophysics
from .result import Quantity, Range, Refusal

ROOT = pathlib.Path(__file__).resolve().parent.parent
# See tools/kb.py: the corpus is named, not assumed to sit beside the package.
KB = pathlib.Path(os.environ.get("GEOLOGY_CORPUS_ROOT") or ROOT) / "knowledge-base"

# --- provenance of the rules themselves ---------------------------------------
# These are plumbing tools; the catalog says no citation is owed. What is owed is
# a pointer to where each rule was written down, so a caller can argue with it.
SOURCE_STATE = "well-log-agent.md#core-object-the-zone-evaluation-state"
SOURCE_STAGE2 = "well-log-agent.md#stage-2-conflict-detection"
SOURCE_GATES = "well-log-agent.md#gates-enforced-in-code"
# The two corpus anchors gate_check's washout gate rests on. drillopedia is the
# catalog's cited source and is qualitative ("if the caliper indicates a
# significant washout"); asquith#18 is the only numeric log-quality threshold in
# the corpus.
DRILLOPEDIA_CALIPER = "01-curve-reading/drillopedia-log-interpretation#1"
ASQUITH_DRHO = petrophysics.ASQUITH_T42  # asquith#18, the DRHO > 0.20 statement

DATUM_REFERENCES = ("KB", "GL", "DF")
EVIDENCE_KINDS = ("measured", "documented", "stated")
ASSUMPTION_SOURCES = ("default", "user", "derived")

# A provenance string that is present but says nothing. Treated as absent
# everywhere, so "Rw_source": "assumed" cannot satisfy the Rw gate.
PLACEHOLDERS = ("", "-", "n/a", "na", "none", "null", "unknown", "assumed",
                "assumption", "default", "guess", "guessed", "tbd", "?")

RW_KEYS = ("rw_source", "rw_provenance", "rw_from", "rwsource")

SATURATION_FIELD_TOKENS = frozenset({"sw", "swe", "swt", "swa", "sxo", "saturation"})
SATURATION_METHOD_TOKENS = ("archie", "saturation", "waxman", "simandoux", "indonesia")
POROSITY_FIELD_TOKENS = frozenset({"phi", "phid", "phin", "phis", "phie", "phix",
                                   "phixp", "porosity", "dphi", "nphi"})
POROSITY_METHOD_TOKENS = ("porosity", "wyllie", "raymer", "crossplot")
VSH_FIELD_TOKENS = frozenset({"vsh", "vshale", "vcl", "vclay", "igr", "gri"})
BVW_FIELD_TOKENS = frozenset({"bvw"})
RESISTIVITY_FIELD_TOKENS = frozenset({"rw", "rt", "rmf", "rm", "rxo", "ri", "ro",
                                      "resistivity", "res"})

# Unit spellings, normalised. A value whose unit is not here is not range-checked
# and is reported in assumptions["unchecked_field_classes"], because silence must
# not read as a pass.
FRACTION_UNITS = frozenset({"v/v", "vv", "frac", "fraction", "dec", "decimal", "-"})
PERCENT_UNITS = frozenset({"%", "pct", "percent", "pu", "p.u.", "puc"})
OHM_UNITS = frozenset({"ohmm", "ohm-m", "ohm.m", "ohm*m", "ohm m", "ohmmeter",
                       "ohmsm", "ohm-metre", "ohm-meter"})

# Physical bounds. Only bounds that ARE the definition of the quantity are here;
# plausibility windows are the caller's (pass ranges=...). See
# specs/65-conflict_detect.md, "Rule 8's bounds, and their marking".
DEFINITIONAL_RANGES: dict[str, tuple[float, float, str]] = {
    # SOURCED - definitional. Porosity is pore volume over bulk volume
    # (asquith#18 Eq. 4.7); saturation is a fraction of pore volume
    # (asquith#42 Eq. 7.1); Vsh and BVW are likewise fractions.
    "porosity": (0.0, 1.0, "fraction"),
    "saturation": (0.0, 1.0, "fraction"),
    "vsh": (0.0, 1.0, "fraction"),
    "bvw": (0.0, 1.0, "fraction"),
    # SOURCED - definitional. Archie divides by Rt (asquith#42); a resistivity
    # is a positive quantity. Upper bound is deliberately absent.
    "resistivity": (0.0, math.inf, "ohmm"),
}
RANGE_BASIS = {
    "porosity": "SOURCED - definitional (asquith#18 Eq. 4.7)",
    "saturation": "SOURCED - definitional (asquith#42 Eq. 7.1)",
    "vsh": "SOURCED - definitional (fraction of bulk volume)",
    "bvw": "SOURCED - definitional (fraction of bulk volume)",
    "resistivity": "SOURCED - definitional (strictly positive; asquith#42)",
}

# Gate 4's required engineering numbers, by the tool that produces each.
CONING_TOOLS = ("coning_critical_rate", "coning_breakthrough_time",
                "coning_rate_schedule", "critical_rate_coning")
LIQUID_LOADING_TOOLS = ("turner_critical_rate", "coleman_critical_rate",
                        "critical_velocity", "turner_coleman_spread",
                        "tubing_velocity", "is_loading",
                        "short_form_critical_velocity")

GATE_ALIASES: dict[str, str] = {
    "structural": "structural",
    "structural_conclusion": "structural",
    "standoff": "structural",
    "correlation": "structural",
    "contact": "structural",
    "contact_projection": "structural",
    "subsea": "structural",
    "point_sw": "point_sw",
    "sw": "point_sw",
    "saturation": "point_sw",
    "point_saturation": "point_sw",
    "archie": "point_sw",
    "porosity": "porosity",
    "phi": "porosity",
    "phid": "porosity",
    "phin": "porosity",
    "crossplot_porosity": "porosity",
    "completion_recommendation": "completion_recommendation",
    "completion": "completion_recommendation",
    "perforation_recommendation": "completion_recommendation",
    "rate_recommendation": "completion_recommendation",
}
GATE_ORDER = ("structural", "point_sw", "porosity", "completion_recommendation")
GATE_NUMBER = {name: i + 1 for i, name in enumerate(GATE_ORDER)}


# --- reading the state object -------------------------------------------------

def _is_mapping(x: Any) -> bool:
    return isinstance(x, Mapping)


def _section(state: Mapping[str, Any], *names: str) -> Any:
    """First present of several spellings. The harness is TypeScript; both
    `toolCalls` and `tool_calls` reach here depending on the serializer."""
    for n in names:
        if n in state and state[n] is not None:
            return state[n]
    return None


def _listof(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _attr(entry: Any, *names: str, default: Any = None) -> Any:
    """Read a field from a mapping, a Quantity/Range/Refusal, or a mapping that
    wraps one. Never raises: an unreadable entry is judged, not crashed on."""
    for name in names:
        if _is_mapping(entry):
            if name in entry and entry[name] is not None:
                return entry[name]
        else:
            got = getattr(entry, name, None)
            if got is not None:
                return got
    inner = entry.get("quantity") if _is_mapping(entry) else None
    if inner is None and _is_mapping(entry):
        inner = entry.get("result")
    if inner is not None and not _is_mapping(inner):
        for name in names:
            got = getattr(inner, name, None)
            if got is not None:
                return got
    return default


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _meaningful(value: Any) -> bool:
    """A provenance string that actually says something."""
    return _text(value).lower() not in PLACEHOLDERS


def _tokens(text: Any) -> frozenset[str]:
    if not isinstance(text, str):
        return frozenset()
    return frozenset(t for t in re.split(r"[^a-z0-9]+", text.lower()) if t)


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if _is_mapping(value) else {}


class _Entry:
    """One `computed` record, however it was spelled."""

    __slots__ = ("raw", "index", "field", "value", "unit", "method", "source",
                 "inputs", "members", "assumptions", "depth_md", "well_api", "tool",
                 "is_range", "is_refusal", "flags", "quote")

    def __init__(self, raw: Any, index: int) -> None:
        self.raw = raw
        self.index = index
        self.field = _text(_attr(raw, "field", "name", default=""))
        self.value = _attr(raw, "value")
        self.unit = _text(_attr(raw, "unit", default=""))
        self.method = _text(_attr(raw, "method", default=""))
        self.source = _text(_attr(raw, "source", "anchor", "source_id", default=""))
        self.inputs = _dict(_attr(raw, "inputs"))
        # A `Range` has no `inputs` field at all: what it was assembled from is in
        # `members` (`tools/result.py:61` - for coning_critical_rate (#47), one
        # entry per published correlation). Read here so provenance_audit (#67)
        # audits a band on the field the type actually carries, instead of calling
        # every real Range an orphan.
        self.members = _dict(_attr(raw, "members"))
        self.assumptions = _dict(_attr(raw, "assumptions"))
        self.depth_md = _numeric(_attr(raw, "depth_md", "depth", "md"))
        self.well_api = _text(_attr(raw, "well_api", "api", default=""))
        self.tool = _text(_attr(raw, "tool", default=""))
        self.is_range = isinstance(raw, Range) or _text(_attr(raw, "kind")) == "range" or (
            _is_mapping(raw) and "low" in raw and "high" in raw)
        self.is_refusal = isinstance(raw, Refusal) or _text(_attr(raw, "kind")) == "refusal" or (
            _is_mapping(raw) and "reason" in raw and "value" not in raw)
        # Rule 11 reads the prose a result puts in front of the operator. `flags`
        # is where a tool quotes the sentence behind a caveat; `quote` is where a
        # handful of tools (tools/deliverability/rate.py:77,
        # tools/perforating/config.py:286) carry the sentence outright.
        self.flags = tuple(str(f) for f in _listof(_attr(raw, "flags")) if isinstance(f, str))
        self.quote = _text(_attr(raw, "quote", default=""))

    @property
    def path(self) -> str:
        return f"computed[{self.index}]"

    def display(self) -> str:
        """What to print in a finding. A `Range` has no `.value`, so printing that
        would report every band as "= None" and hide what was flagged."""
        if self.value is not None:
            return f"{self.value}"
        low, high = _numeric(_attr(self.raw, "low")), _numeric(_attr(self.raw, "high"))
        if low is not None and high is not None:
            return f"{low}-{high}"
        return "None"

    def provenance(self, *keys: str) -> str:
        """Look for a provenance key in inputs and assumptions alike.

        `archie_sw` records `Rw_source` in `assumptions`, not `inputs`
        (tools/petrophysics.py:167), so a gate that looked only at `inputs`
        would refuse every correctly-sourced saturation in the repo.
        """
        for bag in (self.inputs, self.assumptions):
            for k, v in bag.items():
                if k.lower().replace("-", "_") in keys and _meaningful(v):
                    return _text(v) or str(v)
        return ""

    def is_saturation(self) -> bool:
        if _tokens(self.field) & SATURATION_FIELD_TOKENS:
            return True
        low = self.method.lower()
        return any(t in low for t in SATURATION_METHOD_TOKENS)

    def is_porosity(self) -> bool:
        if _tokens(self.field) & POROSITY_FIELD_TOKENS:
            return True
        low = self.method.lower()
        return any(t in low for t in POROSITY_METHOD_TOKENS)

    def field_class(self) -> str | None:
        toks = _tokens(self.field)
        if toks & SATURATION_FIELD_TOKENS:
            return "saturation"
        if toks & POROSITY_FIELD_TOKENS:
            return "porosity"
        if toks & VSH_FIELD_TOKENS:
            return "vsh"
        if toks & BVW_FIELD_TOKENS:
            return "bvw"
        if toks & RESISTIVITY_FIELD_TOKENS:
            return "resistivity"
        if self.is_saturation():
            return "saturation"
        if self.is_porosity():
            return "porosity"
        return None


def _entries(state: Mapping[str, Any]) -> list[_Entry]:
    return [_Entry(raw, i) for i, raw in enumerate(_listof(_section(state, "computed")))]


def _tool_ledger(state: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    raw = _section(state, "toolCalls", "tool_calls", "ledger")
    if raw is None:
        return None
    return [_dict(c) if _is_mapping(c) else {"tool": _text(_attr(c, "tool"))}
            for c in _listof(raw)]


def _finding(rule: int, name: str, field: str, detail: str, remedy: str,
             **extra: Any) -> dict[str, Any]:
    out = {"rule": rule, "name": name, "field": field, "detail": detail,
           "remedy": remedy}
    out.update(extra)
    return out


def _ordered(found: list[tuple[int, int, dict[str, Any]]]) -> list[dict[str, Any]]:
    """Rule number, then position in the state object. A total order that does
    not depend on dict iteration."""
    return [f for _, _, f in sorted(found, key=lambda t: (t[0], t[1]))]


# --- #65 conflict_detect ------------------------------------------------------

def _same(a: Any, b: Any, rel_tol: float) -> bool:
    na, nb = _numeric(a), _numeric(b)
    if na is None or nb is None:
        return a == b
    if na == nb:
        return True
    scale = max(abs(na), abs(nb))
    return abs(na - nb) <= rel_tol * scale


def _normalised_value(entry: _Entry, klass: str) -> float | None:
    """Value in the unit the bound is stated in, or None if not comparable."""
    v = _numeric(entry.value)
    if v is None:
        return None
    unit = entry.unit.strip().lower()
    want = DEFINITIONAL_RANGES[klass][2]
    if want == "fraction":
        if unit in FRACTION_UNITS:
            return v
        if unit in PERCENT_UNITS:
            return v / 100.0
        return None
    if want == "ohmm":
        return v if unit.replace(" ", "") in {u.replace(" ", "") for u in OHM_UNITS} else None
    return None


def conflict_detect(state: Any, *, rel_tol: float = 0.0,
                    ranges: Mapping[str, tuple[float, float, str]] | None = None
                    ) -> Quantity | Refusal:
    """Rule-based contradiction scan over the state object. Determines routing.

    Nine rules, fired in order, spelled out in `specs/65-conflict_detect.md`.
    A clean scan is a `Quantity` with value 0, not a refusal; conflicts are this
    tool's output, not its failure mode.
    """
    if not _is_mapping(state):
        return Refusal(
            reason="conflict_detect needs the ZoneEvaluation state object as a mapping; "
                   f"got {type(state).__name__}",
            needed=("a serialized ZoneEvaluation (well-log-agent.md#core-object)",),
            source=SOURCE_STAGE2,
        )
    if not any(k in state for k in ("well", "datum", "computed")):
        return Refusal(
            reason="state object carries none of well/datum/computed; there is nothing to "
                   "scan and an empty result would read as 'clean'",
            needed=("a state object with at least one of well, datum, computed",),
            source=SOURCE_STAGE2,
        )
    if rel_tol < 0:
        return Refusal(
            reason=f"rel_tol {rel_tol} is negative; a tolerance cannot be below zero",
            needed=("rel_tol >= 0 (0.0 means any difference is a disagreement)",),
            source=SOURCE_STAGE2,
        )

    bounds = dict(DEFINITIONAL_RANGES)
    bounds.update({k: tuple(v) for k, v in (ranges or {}).items()})  # type: ignore[misc]
    found: list[tuple[int, int, dict[str, Any]]] = []
    not_evaluated: list[str] = []
    unchecked: set[str] = set()

    datum = _dict(_section(state, "datum"))
    offsets = [_dict(o) for o in _listof(_section(state, "offsets"))]
    entries = _entries(state)
    ledger = _tool_ledger(state)

    # Rule 1 - datum unresolved.
    if not datum:
        found.append((1, 0, _finding(
            1, "datum_unresolved", "datum",
            "no datum section: the well has no reference elevation",
            "resolve EKB/EGL from the LAS ~PARAMETER section and cross-check the W-2/G-1")))
    elif datum.get("resolved") is not True:
        found.append((1, 0, _finding(
            1, "datum_unresolved", "datum.resolved",
            f"datum.resolved is {datum.get('resolved')!r}; subsea depths and cross-well "
            "comparison are provisional",
            "resolve EKB against the W-2/G-1 record; Stage 0 sets resolved=true on a match")))

    # Rule 2 - datum reference unknown.
    if datum:
        ref = _text(datum.get("reference")).upper()
        if ref not in DATUM_REFERENCES:
            found.append((2, 0, _finding(
                2, "datum_reference_unknown", "datum.reference",
                f"reference {datum.get('reference')!r} is not one of {DATUM_REFERENCES}; "
                "a depth with no stated reference is a bare depth",
                "state the reference the elevations are measured from (KB, GL or DF)")))

    # Rule 3 - two datum readings disagree.
    candidates = [_dict(c) for c in _listof(datum.get("candidates"))]
    if not candidates:
        not_evaluated.append("3 datum_candidates_disagree (no datum.candidates in the object)")
    else:
        first = candidates[0]
        for j, cand in enumerate(candidates[1:], start=1):
            diffs = [k for k in ("kb_ft", "gl_ft", "reference")
                     if not _same(first.get(k), cand.get(k), rel_tol)]
            if diffs:
                found.append((3, j, _finding(
                    3, "datum_candidates_disagree", f"datum.candidates[0] vs [{j}]",
                    f"{', '.join(diffs)} disagree: {first.get('source')!r} gives "
                    f"{ {k: first.get(k) for k in diffs} }, {cand.get('source')!r} gives "
                    f"{ {k: cand.get(k) for k in diffs} }",
                    "pull the W-2/G-1 and set datum from the filed record; report a range "
                    "until it is resolved")))

    # Rules 4 and 5 - offset datums.
    subject_ref = _text(datum.get("reference")).upper()
    for i, off in enumerate(offsets):
        if off.get("datum_resolved") is not True:
            found.append((4, i, _finding(
                4, "offset_datum_unresolved", f"offsets[{i}].datum_resolved",
                f"offset {off.get('api')!r} has datum_resolved="
                f"{off.get('datum_resolved')!r}; it cannot carry a structural comparison",
                f"pull the W-2 for {off.get('api')!r} and resolve its reference elevation")))
        off_ref = _text(_dict(off.get("datum")).get("reference") or off.get("reference")).upper()
        if off_ref and subject_ref and off_ref != subject_ref:
            found.append((5, i, _finding(
                5, "datum_reference_mismatch", f"offsets[{i}].datum.reference",
                f"offset {off.get('api')!r} is on {off_ref}, subject well is on "
                f"{subject_ref}; comparing them is a tens-of-feet error",
                "convert both wells to a common reference before comparing depths")))

    # Rule 6 - two readings of one field.
    groups: dict[tuple[str, str, float | None], list[_Entry]] = {}
    order: list[tuple[str, str, float | None]] = []
    for e in entries:
        if not e.field:
            continue
        key = (e.field.strip().lower(), e.well_api, e.depth_md)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(e)
    for key in order:  # insertion order, not dict order
        members = groups[key]
        if len(members) < 2:
            continue
        first = members[0]
        if all(_same(first.value, m.value, rel_tol) for m in members[1:]):
            continue
        sources = {m.source for m in members if m.source}
        label = "same document" if len(sources) == 1 and len(
            [m for m in members if m.source]) == len(members) else "same field"
        found.append((6, min(m.index for m in members), _finding(
            6, "incompatible_readings",
            ", ".join(m.path for m in members),
            f"{label}: field {first.field!r} has values "
            f"{[m.value for m in members]}"
            + (f" all from {sorted(sources)[0]}" if label == "same document" else ""),
            "resolve which reading is right (the resolving document, or a third "
            "measurement); do not average them or take last-wins",
            label=label)))

    # Rule 7 - saturation without Rw provenance.
    for e in entries:
        if not e.is_saturation() or e.is_refusal:
            continue
        if not e.provenance(*RW_KEYS):
            found.append((7, e.index, _finding(
                7, "saturation_without_rw", f"{e.path}.assumptions.Rw_source",
                f"saturation {e.field or e.method!r} carries no Rw provenance in inputs or "
                "assumptions",
                "supply Rw from rw_pickett (#34), rw_from_sp, or a measured water analysis; "
                "otherwise emit a range or a Pickett-plot request")))

    # Rule 8 - outside a physical range.
    for e in entries:
        if e.is_refusal:
            continue
        klass = e.field_class()
        if klass is None or klass not in bounds:
            if _numeric(e.value) is not None and e.field:
                unchecked.add(e.field.strip().lower())
            continue
        v = _normalised_value(e, klass) if klass in DEFINITIONAL_RANGES else _numeric(e.value)
        if v is None:
            unchecked.add(f"{e.field.strip().lower()} (unit {e.unit!r} not recognised)")
            continue
        lo, hi, _unit = bounds[klass]
        if lo <= v <= hi and not (klass == "resistivity" and v <= 0):
            continue
        remedy = ("check the inputs and the assumed constants that produced it")
        if klass == "porosity" and v < 0:
            remedy = ("re-run with the correct matrix density: asquith#18 says a negative "
                      "density porosity means the assumed rho_ma was too high, and is often "
                      "anhydrite or another heavy mineral")
        elif klass == "saturation" and v > 1:
            remedy = "check Rw, m and n, or accept that the interval is wet (Sw cannot exceed 1)"
        found.append((8, e.index, _finding(
            8, "outside_physical_range", f"{e.path}.value",
            f"{e.field or e.method} = {e.value} {e.unit} is outside the {klass} bound "
            f"[{lo}, {hi}] ({RANGE_BASIS.get(klass, 'CALLER-supplied bound')})",
            remedy, basis=RANGE_BASIS.get(klass, "CALLER"))))

    # Rule 8, continued: interval ordering. Definitional, not a tuning knob -
    # the base of an interval is below its top.
    interval = _dict(_section(state, "interval"))
    top_md, base_md = _numeric(interval.get("top_md")), _numeric(interval.get("base_md"))
    if top_md is not None and base_md is not None and base_md <= top_md:
        found.append((8, 10_000, _finding(
            8, "outside_physical_range", "interval.base_md",
            f"base_md {base_md} is not below top_md {top_md}",
            "correct the interval; a base at or above its top is a transposition",
            basis="SOURCED - definitional (interval ordering)")))

    # Rule 9 - a refused or failed tool call.
    if ledger is None:
        not_evaluated.append("9 refused_tool_result (no toolCalls ledger in the object)")
    else:
        for i, call in enumerate(ledger):
            refused = call.get("refused")
            error = call.get("error")
            if refused:
                r = _dict(refused)
                found.append((9, i, _finding(
                    9, "refused_tool_result", f"toolCalls[{i}].refused",
                    f"{call.get('tool')!r} refused at gate {r.get('gate')!r}: {r.get('reason')}",
                    _text(r.get("remedy")) or "satisfy the gate the tool named")))
            elif error:
                found.append((9, i, _finding(
                    9, "refused_tool_result", f"toolCalls[{i}].error",
                    f"{call.get('tool')!r} failed: {error}",
                    "re-run the call with valid arguments, or record why the value is absent")))

    not_evaluated.append(
        "10 offset_projection_vs_log_character - needs a log-derived contact depth with its "
        "uncertainty in the state object; no corpus threshold converts curve character into "
        "agreement. Left to the Stage 2 agent (well-log-agent.md:339)")

    findings = _ordered(found)
    counts: dict[int, int] = {}
    for f in findings:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    evaluated = tuple(f"{n} {nm}" for n, nm in (
        (1, "datum_unresolved"), (2, "datum_reference_unknown"),
        (3, "datum_candidates_disagree"), (4, "offset_datum_unresolved"),
        (5, "datum_reference_mismatch"), (6, "incompatible_readings"),
        (7, "saturation_without_rw"), (8, "outside_physical_range"),
        (9, "refused_tool_result"))
        if not any(s.startswith(f"{n} ") for s in not_evaluated))

    return Quantity(
        value=float(len(findings)),
        unit="conflicts",
        method="conflict_detect rules v1",
        source=SOURCE_STAGE2,
        inputs={
            "findings": findings,
            "routing": "escalated" if findings else "standard",
            "counts_by_rule": counts,
            "scanned": {"computed": len(entries), "offsets": len(offsets),
                        "tool_calls": len(ledger) if ledger is not None else 0},
        },
        assumptions={
            "rel_tol": rel_tol,
            "rules_evaluated": evaluated,
            "rules_not_evaluated": tuple(not_evaluated),
            "unchecked_field_classes": tuple(sorted(unchecked)),
            "range_bounds": {k: (v[0], v[1], v[2], RANGE_BASIS.get(k, "CALLER"))
                             for k, v in sorted(bounds.items())},
            "value_meaning": "count of findings; the findings are in inputs['findings']",
        },
    )


# --- #66 gate_check -----------------------------------------------------------

def _hq_bound(iv: Any, *names: str) -> float | None:
    """One end of a hole-quality interval, in feet MD.

    `hole_quality` (#25) ships `QualityInterval.top_ft / .base_ft` as `Quantity`
    objects; a serialized state object may spell the same thing `top_md`. Both
    are read, and a `Quantity` bound is unwrapped, because the alternative is
    what this replaced: a gate that could not parse the verdict it was handed and
    reported "nothing is known about the hole" over a real washout.
    """
    for name in names:
        got = _attr(iv, name)
        if got is None:
            continue
        value = _numeric(got)
        if value is None:
            value = _numeric(_attr(got, "value"))
        if value is not None:
            return value
    return None


def _hq_basis(iv: Any) -> str:
    """#25's own gate names and statuses, carried through verbatim.

    `tool-catalog.md:112`: *"hole_quality must return which gate fired, because
    one is defensible in front of an operator and the other is a house rule."*
    That distinction is worth nothing if this tool drops it on the way to the
    operator, so the status/gate pairs are reproduced, not re-derived.
    """
    statuses = _dict(_attr(iv, "statuses"))
    gates = _listof(_attr(iv, "gates"))
    if statuses:
        ordered = [g for g in gates if g in statuses] or sorted(statuses)
        return ", ".join(f"{statuses[g]} ({g})" for g in ordered)
    stated = _text(_attr(iv, "gate")) or _text(_attr(iv, "basis"))
    if stated:
        return stated
    if gates:
        return "gates " + ", ".join(str(g) for g in gates)
    return "carried from hole_quality (#25); see tool-catalog.md:112"


def _hole_quality_intervals(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Normalise whatever the state object carries into one interval shape.

    Accepted: a `HoleQuality` (or anything carrying `.intervals`), a sequence of
    `QualityInterval` objects, or the mapping shape
    `{top_md, base_md, flag, gate, source}` a serializing harness would produce.
    """
    raw = _section(state, "hole_quality", "holeQuality")
    if raw is None:
        return []
    if not isinstance(raw, (list, tuple)):
        inner = _attr(raw, "intervals")
        if inner is not None:
            raw = inner
    out: list[dict[str, Any]] = []
    for iv in _listof(raw):
        out.append({
            "top": _hq_bound(iv, "top_md", "top_ft", "top", "top_depth_ft"),
            "base": _hq_bound(iv, "base_md", "base_ft", "base", "bottom_ft"),
            "verdict": _text(_attr(iv, "verdict", default="")).lower(),
            "flag": _text(_attr(iv, "flag") or _attr(iv, "status")
                          or _attr(iv, "quality") or ""),
            "gates": tuple(str(g) for g in _listof(_attr(iv, "gates"))),
            "basis": _hq_basis(iv),
            "washout": _attr(iv, "washout"),
            "bad_hole": _attr(iv, "bad_hole"),
        })
    return out


def _covering_interval(intervals: Iterable[Mapping[str, Any]], depth: float | None):
    if depth is None:
        return None
    for j, iv in enumerate(intervals):
        top, base = iv.get("top"), iv.get("base")
        if top is None or base is None:
            continue
        if min(top, base) <= depth <= max(top, base):
            return j, iv
    return None


def _flagged_bad(iv: Mapping[str, Any]) -> bool:
    if iv.get("verdict") == "bad":
        return True
    flag = _text(iv.get("flag")).lower()
    if iv.get("washout") is True or iv.get("bad_hole") is True:
        return True
    if any(t in " ".join(iv.get("gates", ())).lower()
           for t in ("washout", "rugos", "undergauge", "drho")) and \
            iv.get("verdict") not in ("good", "unknown"):
        return True
    return any(t in flag for t in ("washout", "bad", "rugose", "rugosity", "enlarge",
                                   "suspect", "undergauge"))


def _flagged_good(iv: Mapping[str, Any]) -> bool:
    """#25 says "good" only where every evaluable gate cleared; "unknown" is not
    a pass and never becomes one here (`specs/25`, and `specs/66` step 4)."""
    return iv.get("verdict") == "good" or _text(iv.get("flag")).lower() in (
        "good", "in gauge", "in-gauge")


def _gate_finding(gate: str, field: str, detail: str, remedy: str, basis: str,
                  order: int) -> tuple[int, int, dict[str, Any]]:
    return (GATE_NUMBER[gate], order, {
        "gate": GATE_NUMBER[gate], "name": gate, "field": field,
        "detail": detail, "remedy": remedy, "basis": basis,
    })


def gate_check(state: Any, renders: Sequence[str] | str | None = None, *,
               washout_cutoff_in: float | None = None) -> Quantity | Refusal:
    """The four render gates of `well-log-agent.md:223`, over the state object.

    `renders` names the claims the turn is about to make; nothing in the state
    object says what is about to be rendered, and a gate that guesses what it is
    guarding is not a gate. An unrecognised name refuses rather than being
    skipped, because a typo that skipped a gate is the bypass the design forbids.

    `washout_cutoff_in` has no default. The only sourced washout threshold is
    DRHO > 0.20 g/cm3 (asquith#18, imported as petrophysics.DRHO_SUSPECT); the
    caliper cutoff in tool-catalog.md:88 is marked PROVISIONAL and belongs to
    hole_quality (#25), which labels it as a house rule. This gate will block
    before it applies one silently.
    """
    if not _is_mapping(state):
        return Refusal(
            reason=f"gate_check cannot read the state object: got {type(state).__name__}",
            needed=("a serialized ZoneEvaluation (well-log-agent.md#core-object)",),
            source=SOURCE_GATES,
        )
    names = [renders] if isinstance(renders, str) else list(renders or [])
    if not names:
        return Refusal(
            reason="gate_check requires the list of claims to guard; it will not infer them "
                   "from the state object",
            needed=GATE_ORDER,
            source=SOURCE_GATES,
        )
    wanted: list[str] = []
    for n in names:
        key = _text(n).lower().replace("-", "_").replace(" ", "_")
        if key not in GATE_ALIASES:
            return Refusal(
                reason=f"unrecognised render name {n!r}; it is refused rather than skipped, "
                       "because a name that guards nothing is a bypassed gate",
                needed=GATE_ORDER,
                source=SOURCE_GATES,
            )
        gate = GATE_ALIASES[key]
        if gate not in wanted:
            wanted.append(gate)
    if washout_cutoff_in is not None and washout_cutoff_in <= 0:
        return Refusal(
            reason=f"washout_cutoff_in {washout_cutoff_in} is not positive; a cutoff at or "
                   "below zero flags every in-gauge hole",
            needed=("a positive DiffCal cutoff in inches (caliper - bit size)",),
            source=SOURCE_GATES,
        )

    datum = _dict(_section(state, "datum"))
    offsets = [_dict(o) for o in _listof(_section(state, "offsets"))]
    entries = _entries(state)
    ledger = _tool_ledger(state) or []
    intervals = _hole_quality_intervals(state)
    found: list[tuple[int, int, dict[str, Any]]] = []
    evidence: dict[str, Any] = {}

    # --- Gate 1: structural conclusion.
    if "structural" in wanted:
        subject_ref = _text(datum.get("reference")).upper()
        if datum.get("resolved") is not True:
            found.append(_gate_finding(
                "structural", "datum.resolved",
                f"subject datum resolved={datum.get('resolved')!r}",
                "resolve EKB against the W-2/G-1 record before drawing a structural "
                "conclusion", "architecture (well-log-agent.md:227)", 0))
        if subject_ref not in DATUM_REFERENCES:
            found.append(_gate_finding(
                "structural", "datum.reference",
                f"subject datum reference {datum.get('reference')!r} is not one of "
                f"{DATUM_REFERENCES}",
                "state the reference the elevations are measured from",
                "architecture (well-log-agent.md:227)", 1))
        if not offsets:
            found.append(_gate_finding(
                "structural", "offsets",
                "a structural conclusion compares two wells and this state object has no "
                "offset",
                "supply the offset well with its datum, or render this as a single-well "
                "observation rather than a structural conclusion",
                "architecture (well-log-agent.md:227)", 2))
        for i, off in enumerate(offsets):
            if off.get("datum_resolved") is not True:
                found.append(_gate_finding(
                    "structural", f"offsets[{i}].datum_resolved",
                    f"offset {off.get('api')!r} datum_resolved="
                    f"{off.get('datum_resolved')!r}",
                    f"pull the W-2 for {off.get('api')!r} and resolve its elevation",
                    "architecture (well-log-agent.md:227)", 3 + i))
            off_ref = _text(_dict(off.get("datum")).get("reference")
                            or off.get("reference")).upper()
            if not off_ref:
                found.append(_gate_finding(
                    "structural", f"offsets[{i}].datum.reference",
                    f"offset {off.get('api')!r} states no datum reference; unstated is not "
                    "'confirmed to be on the same reference'",
                    "state the offset's reference (KB, GL or DF)",
                    "architecture (well-log-agent.md:227)", 100 + i))
            elif subject_ref and off_ref != subject_ref:
                found.append(_gate_finding(
                    "structural", f"offsets[{i}].datum.reference",
                    f"offset {off.get('api')!r} is on {off_ref}, subject is on {subject_ref}",
                    "convert both wells to a common reference before comparing",
                    "architecture (well-log-agent.md:227)", 200 + i))
        evidence["structural"] = {"subject_reference": subject_ref, "offsets": len(offsets)}

    # --- Gate 2: Sw as a point number.
    if "point_sw" in wanted:
        sats = [e for e in entries if e.is_saturation() and not e.is_refusal]
        points = [e for e in sats if not e.is_range]
        if not sats:
            found.append(_gate_finding(
                "point_sw", "computed",
                "no saturation in computed[]; a saturation in the prose that is not in "
                "computed[] came from nowhere",
                "call archie_sw (#35) - or shaly_sand_sw - and record the result, or do not "
                "state a saturation", "architecture (well-log-agent.md:228)", 0))
        for e in points:
            rw = e.provenance(*RW_KEYS)
            if not rw:
                found.append(_gate_finding(
                    "point_sw", f"{e.path}.assumptions.Rw_source",
                    f"point saturation {e.field or e.method!r} = {e.value} has no Rw "
                    "provenance in inputs or assumptions",
                    "supply Rw from rw_pickett (#34), rw_from_sp, or a measured water "
                    "analysis; otherwise emit a range or a Pickett-plot request "
                    "(well-log-agent.md:228)",
                    "architecture (well-log-agent.md:228)", e.index))
        evidence["point_sw"] = {"saturations": len(sats), "point_values": len(points)}

    # --- Gate 3: porosity through a washout.
    if "porosity" in wanted:
        phis = [e for e in entries if e.is_porosity() and not e.is_refusal]
        if not phis:
            found.append(_gate_finding(
                "porosity", "computed",
                "no porosity in computed[]; a porosity in the prose that is not in "
                "computed[] came from nowhere",
                "call density_porosity / sonic_porosity / crossplot_porosity and record the "
                "result", "architecture (well-log-agent.md:229)", 0))
        for e in phis:
            drho = _numeric(e.inputs.get("drho") or e.assumptions.get("drho")
                            or _attr(e.raw, "drho"))
            hit = _covering_interval(intervals, e.depth_md)
            caliper = _numeric(e.inputs.get("caliper_in") or e.inputs.get("caliper")
                               or e.assumptions.get("caliper_in"))
            bit = _numeric(e.inputs.get("bit_size_in") or e.inputs.get("bit_size")
                           or e.assumptions.get("bit_size_in"))
            if drho is not None and drho > petrophysics.DRHO_SUSPECT:
                found.append(_gate_finding(
                    "porosity", f"{e.path}.inputs.drho",
                    f"DRHO {drho:.2f} g/cm3 exceeds {petrophysics.DRHO_SUSPECT} g/cm3, so the "
                    "bulk density behind this porosity is suspect and possibly invalid",
                    "take the porosity from an in-gauge interval, or use a porosity that does "
                    "not depend on the density curve",
                    f"SOURCED ({ASQUITH_DRHO})", e.index))
            elif hit is not None and _flagged_bad(hit[1]):
                j, iv = hit
                fired = ", ".join(iv.get("gates", ())) or iv.get("flag") or "bad hole"
                found.append(_gate_finding(
                    "porosity", f"hole_quality[{j}] over {e.path}.depth_md",
                    f"depth {e.depth_md} lies in hole_quality interval "
                    f"{iv.get('top')}-{iv.get('base')} ft, verdict "
                    f"{iv.get('verdict') or iv.get('flag')!r}, gate(s) fired: {fired}",
                    "report porosity only from in-gauge intervals, or state the hole "
                    "condition alongside the number",
                    iv.get("basis") or "carried from hole_quality (#25); see "
                    "tool-catalog.md:112", e.index))
            elif hit is not None and _flagged_good(hit[1]):
                continue  # #25 cleared this depth: that is evidence, not silence
            elif drho is not None:
                continue  # DRHO known and in spec: the sourced gate passes
            elif caliper is not None and bit is not None:
                diff = caliper - bit
                if washout_cutoff_in is None:
                    found.append(_gate_finding(
                        "porosity", f"{e.path}.inputs.caliper_in",
                        f"caliper {caliper} in against bit {bit} in (DiffCal {diff:+.2f} in) "
                        "and no numeric caliper cutoff exists in the corpus - the source is "
                        f"qualitative ({DRILLOPEDIA_CALIPER}: 'if the caliper indicates a "
                        "significant washout')",
                        "pass washout_cutoff_in explicitly (tool-catalog.md:88 carries a "
                        "PROVISIONAL 1.0 in), or run hole_quality (#25) and attach its flag, "
                        "or attach DRHO to the porosity",
                        "CALLER (no default, ever)", e.index))
                elif diff > washout_cutoff_in:
                    found.append(_gate_finding(
                        "porosity", f"{e.path}.inputs.caliper_in",
                        f"DiffCal {diff:+.2f} in exceeds the caller's cutoff "
                        f"{washout_cutoff_in} in",
                        "report porosity only from in-gauge intervals, or state the hole "
                        "condition alongside the number",
                        f"CALLER (washout_cutoff_in={washout_cutoff_in}; the corpus states no "
                        f"caliper cutoff - {DRILLOPEDIA_CALIPER} is qualitative)", e.index))
            else:
                found.append(_gate_finding(
                    "porosity", "hole_quality",
                    f"nothing in the state object says whether {e.field or e.method!r} at "
                    f"depth {e.depth_md} was logged through good hole",
                    "attach DRHO to the porosity, or run hole_quality (#25) over CAL and BS "
                    "and put its intervals in the state object",
                    "architecture (well-log-agent.md:229) - unevaluable, not a pass", e.index))
        evidence["porosity"] = {"porosities": len(phis),
                                "hole_quality_intervals": len(intervals),
                                "washout_cutoff_in": washout_cutoff_in}

    # --- Gate 4: completion recommendation.
    if "completion_recommendation" in wanted:
        def _hits(tools: Sequence[str]) -> tuple[list[str], list[str]]:
            ok: list[str] = []
            refused: list[str] = []
            for e in entries:
                blob = f"{e.tool} {e.method} {e.field}".lower()
                for t in tools:
                    if t in blob or t.replace("_", " ") in blob:
                        (refused if e.is_refusal else ok).append(f"{t} @ {e.path}")
            for i, call in enumerate(ledger):
                name = _text(call.get("tool")).lower()
                if name in tools:
                    if call.get("refused") or call.get("error"):
                        refused.append(f"{name} @ toolCalls[{i}]")
                    else:
                        ok.append(f"{name} @ toolCalls[{i}]")
            return ok, refused

        coning_ok, coning_refused = _hits(CONING_TOOLS)
        ll_ok, ll_refused = _hits(LIQUID_LOADING_TOOLS)
        if not coning_ok:
            found.append(_gate_finding(
                "completion_recommendation", "computed / toolCalls",
                "no coning number attached"
                + (f" (refused: {coning_refused})" if coning_refused else ""),
                "call coning_critical_rate (#47) - and coning_breakthrough_time (#48) where "
                "the contact is close - and attach the result",
                "architecture (well-log-agent.md:230, :236)", 0))
        if not ll_ok:
            found.append(_gate_finding(
                "completion_recommendation", "computed / toolCalls",
                "no liquid-loading number attached"
                + (f" (refused: {ll_refused})" if ll_refused else ""),
                "call turner_critical_rate (#52) and coleman_critical_rate (#53), or "
                "tubing_velocity (#54), and attach the result",
                "architecture (well-log-agent.md:230, :236)", 1))
        evidence["completion_recommendation"] = {
            "coning": coning_ok, "coning_refused": coning_refused,
            "liquid_loading": ll_ok, "liquid_loading_refused": ll_refused}

    findings = _ordered(found)
    if findings:
        lines = [f"{len(findings)} gate(s) block this render:"]
        needed: list[str] = []
        for f in findings:
            lines.append(f"GATE {f['gate']} {f['name']}: blocked by {f['field']} - "
                         f"{f['detail']} [{f['basis']}]")
            needed.append(f"{f['name']}: {f['remedy']}")
        source = SOURCE_GATES
        if any(f["name"] == "porosity" for f in findings):
            source = f"{SOURCE_GATES} + {ASQUITH_DRHO} + {DRILLOPEDIA_CALIPER}"
        return Refusal(reason="\n".join(lines), needed=tuple(needed), source=source)

    return Quantity(
        value=float(len(wanted)),
        unit="gates",
        method="gate_check v1",
        source=SOURCE_GATES,
        inputs={"gates_passed": tuple(wanted), "renders": tuple(names),
                "evidence": evidence},
        assumptions={
            "washout_cutoff_in": washout_cutoff_in,
            "washout_cutoff_basis": ("CALLER - the corpus states no numeric caliper cutoff; "
                                     f"{DRILLOPEDIA_CALIPER} is qualitative"),
            "drho_suspect": petrophysics.DRHO_SUSPECT,
            "drho_basis": f"SOURCED ({ASQUITH_DRHO})",
            "value_meaning": "count of gates evaluated and passed",
        },
    )


# --- #67 provenance_audit -----------------------------------------------------

_SEGMENT_COUNTS: dict[str, int] = {}
_SEGMENTATION_ERROR: list[str] = []

_ANCHOR_PART = re.compile(r"[;]|\s\+\s")
USER_SOURCE_PREFIXES = ("user:", "stated:", "conversation:", "operator:", "call:")


def _segment_count(path: pathlib.Path) -> int | None:
    """Number of segments in a corpus document, via the same function
    scripts/show_segment.py uses. None when segmentation is unavailable."""
    key = str(path)
    if key in _SEGMENT_COUNTS:
        return _SEGMENT_COUNTS[key]
    if _SEGMENTATION_ERROR:
        return None
    try:
        from . import kb
        spans = kb._segment_spans(path.read_text(errors="ignore"))
    except Exception as exc:  # segmentation unavailable: audit refuses, never guesses
        _SEGMENTATION_ERROR.append(str(exc))
        return None
    _SEGMENT_COUNTS[key] = len(spans)
    return len(spans)


def _token_resolves(token: str) -> tuple[bool, str]:
    """One whitespace-delimited token: corpus anchor, corpus document, or repo file."""
    token = token.strip().strip("(),;:'\"`\\").rstrip(".")
    if not token or token.lower() in PLACEHOLDERS:
        return False, "empty or placeholder source"
    key, _, idx = token.partition("#")
    key = key.strip()
    # A repo pointer may carry a line number: `well-log-agent.md:414`.
    key = re.sub(r":\d+(-\d+)?$", "", key)
    doc = KB / f"{key}.md"
    if doc.exists():
        if not idx:
            return True, "whole-document anchor"
        if not idx.isdigit():
            return False, f"segment index {idx!r} is not a number"
        n = int(idx)
        count = _segment_count(doc)
        if count is None:
            return False, "segmentation unavailable"
        if 0 <= n < count:
            return True, f"segment {n} of {count - 1}"
        return False, f"segment {n} is out of range (document has 0-{count - 1})"
    if (ROOT / key).is_file():
        return True, "repo file"
    if "/" in key or key.endswith(".md"):
        return False, f"no such document: knowledge-base/{key}.md"
    return False, "not a corpus anchor and not a repo file"


def _part_resolves(part: str) -> tuple[bool, str]:
    """A source part resolves when *something* in it opens.

    Sources in this repo carry page notes ("…#100, p. 458"), parentheticals, and
    plumbing tools cite a spec inside a sentence ("plumbing - contract pinned by
    specs/74-trajectory_log.md"). The substantive requirement is that the caller
    can get from the string to a document, so every token is tried and the part
    resolves if one of them does. A string with no openable pointer anywhere in
    it does not resolve, which is the case this rule exists to catch.
    """
    part = part.strip()
    if not part or part.lower() in PLACEHOLDERS:
        return False, "empty or placeholder source"
    tokens = [t for t in re.split(r"[\s,]+", part) if t.strip(" ,()'\"`.")]
    reasons: list[str] = []
    for tok in tokens:
        ok, why = _token_resolves(tok)
        if ok:
            return True, why if len(tokens) == 1 else f"{tok.strip(chr(44))}: {why}"
        reasons.append(why)
    return False, reasons[0] if len(tokens) == 1 else (
        "no token in this source opens: " + "; ".join(
            f"{t}: {r}" for t, r in zip(tokens, reasons)))


def _bears_pointer(part: str) -> bool:
    """Does this part even claim to cite something? A trailing note alongside a
    real anchor ("…#1; not held in this corpus") is a note, not a second
    citation, and holding it to the anchor standard would flag honest sources."""
    return any("/" in t or t.endswith(".md") or ".md#" in t or ".md:" in t
               for t in re.split(r"[\s,]+", part))


def _source_resolves(source: str) -> tuple[bool, str]:
    """Every citing part of a source must open, and there must be one.

    Split on `;` and ` + `, so a multi-anchor source (as `kb_search` builds at
    `tools/kb.py:485`) is checked anchor by anchor: a bogus anchor hiding in a
    list of good ones is exactly what this catches.
    """
    parts = [p for p in _ANCHOR_PART.split(source) if p.strip()]
    citing = [p for p in parts if _bears_pointer(p)]
    if not parts:
        return False, "empty source"
    if not citing:
        return False, f"no citation in {source.strip()!r}: it points at no document"
    details: list[str] = []
    ok = True
    for p in citing:
        good, why = _part_resolves(p)
        ok = ok and good
        details.append(f"{p.strip()}: {why}")
    return ok, "; ".join(details)


# --- rule 11: does the cited passage contain the sentence the result quotes? ---
#
# Rule 4 asks whether an anchor opens. Rule 11 asks whether it opens onto the
# passage the result says it does. Three defects of exactly this shape were found
# in three unrelated tool groups (agent1-findings.md:57-65): a gas-water rate
# tagged to the segment that says no gas-water correlation exists, Asquith Table
# 4.1 constants cited to Table 4.2, and a high-gravity flag citing `ahmed#12`
# while quoting Sutton's sentence from `#14`. All three *resolve*. The one part of
# "is this citation about the claim?" that can be decided without a model is the
# part where the result quotes the source verbatim: the sentence is either in the
# cited passage or it is not.
#
# The rule is deliberately lopsided. It will run over every result in the repo,
# and a rule that cries wolf gets switched off - so every ambiguity resolves
# towards silence.

MIN_QUOTE_CHARS = 25     # after normalisation; below this a quoted fragment is a
                         # label, not a citation of prose
MIN_QUOTE_WORDS = 4      # whitespace-delimited, in the raw span

# A quoted span is treated as a quotation of source prose only if it contains one
# of these. This is a positive test for English prose, not a blacklist of things
# to ignore: a quoted argument name, mnemonic, unit, enum value, anchor or
# equation carries no function word, and source prose essentially always does.
FUNCTION_WORDS = frozenset({
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "from", "by", "with",
    "and", "or", "but", "not", "no", "as", "is", "are", "was", "were", "be",
    "been", "it", "its", "this", "that", "these", "those", "than", "then",
    "when", "where", "which", "while", "if", "should", "must", "may", "can",
    "will", "would", "shall", "there", "their", "into", "over", "under", "such",
    "all", "any", "both", "each", "more", "most", "less", "least", "very",
})

# Openers/closers. Straight single quotes are only honoured at a word boundary,
# so an apostrophe ("Asquith's", "isn't") never opens or closes a span. A span
# whose interior holds an apostrophe simply is not extracted - a miss, which is
# the direction this rule errs in.
_QUOTE_SPANS = (
    re.compile(r'"([^"]+)"'),
    re.compile(r'“([^”]+)”'),
    re.compile(r'‘([^’]+)’'),
    re.compile(r"(?<![0-9A-Za-z])'([^'’]+)'(?![0-9A-Za-z])"),
)
_ELLIPSIS = ("...", "…")

_DOC_SPAN_CACHE: dict[str, list[tuple[int, int]]] = {}
_DOC_RAW_CACHE: dict[str, str] = {}
_NORM_CACHE: dict[str, str] = {}
_PARENTHETICAL = re.compile(r"\([^()]*\)")


def _normalise_prose(text: str) -> str:
    """Fold everything that is presentation, so a quote and its source compare.

    Real cases this exists for, all hit by testers: curly versus straight quotes
    (`“Block”` against `'Block'`), markdown emphasis (`_squeeze cementing_`),
    the corpus wrapping a sentence across lines, and stray punctuation drift
    (`ohm-m` / `ohm m`). Every non-alphanumeric character becomes a space on both
    sides and whitespace collapses, which folds all four at once and cannot
    introduce a difference that was not there.
    """
    return " ".join(re.sub(r"[^0-9a-z]+", " ", text.lower()).split())


def _doc_spans(path: pathlib.Path, text: str) -> list[tuple[int, int]] | None:
    key = str(path)
    if key in _DOC_SPAN_CACHE:
        return _DOC_SPAN_CACHE[key]
    if _SEGMENTATION_ERROR:
        return None
    try:
        from . import kb
        spans = kb._segment_spans(text)
    except Exception as exc:  # same contract as _segment_count: never guess
        _SEGMENTATION_ERROR.append(str(exc))
        return None
    _DOC_SPAN_CACHE[key] = spans
    return spans


def _token_text(token: str) -> str | None:
    """The normalised text a single source token points at, or None.

    A `#n` anchor gives that segment; a bare document or a repo file gives the
    whole file. A `#fragment` on a repo file is a heading, not a segment index
    (specs/67, source-resolution rule 4), so the whole file is searched.
    """
    token = token.strip().strip("(),;:'\"`\\").rstrip(".")
    if not token or token.lower() in PLACEHOLDERS:
        return None
    key, _, idx = token.partition("#")
    key = re.sub(r":\d+(-\d+)?$", "", key.strip())
    doc = KB / f"{key}.md"
    if doc.exists():
        text = _raw(doc)
        if idx.isdigit():
            spans = _doc_spans(doc, text)
            if spans is None:
                return None
            n = int(idx)
            if not 0 <= n < len(spans):
                return None
            a, b = spans[n]
            return _cached_norm(f"{doc}#{n}", text[a:b])
        if idx:
            return None
        return _cached_norm(str(doc), text)
    repo = ROOT / key
    if repo.is_file():
        return _cached_norm(str(repo), _raw(repo))
    return None


def _raw(path: pathlib.Path) -> str:
    key = str(path)
    if key not in _DOC_RAW_CACHE:
        _DOC_RAW_CACHE[key] = path.read_text(errors="ignore")
    return _DOC_RAW_CACHE[key]


def _cached_norm(key: str, text: str) -> str:
    if key not in _NORM_CACHE:
        _NORM_CACHE[key] = _normalise_prose(text)
    return _NORM_CACHE[key]


def _source_texts(source: str) -> list[tuple[str, str]]:
    """(pointer, normalised text) for every token in the source that opens.

    A multi-anchor source is searched in full: the quote need only be in one of
    the passages the result cites. Union, not intersection - a result that cites
    three segments and quotes one of them is citing correctly.
    """
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for part in _ANCHOR_PART.split(source):
        for tok in re.split(r"[\s,]+", part):
            tok = tok.strip(" ,()'\"`.")
            if not tok or tok in seen:
                continue
            seen.add(tok)
            text = _token_text(tok)
            if text is not None:
                out.append((tok, text))
    return out


def _quoted_spans(text: str) -> list[str]:
    """Quoted spans of `text`, in order of appearance, deduplicated."""
    hits: list[tuple[int, str]] = []
    for pattern in _QUOTE_SPANS:
        for m in pattern.finditer(text):
            hits.append((m.start(), m.group(1)))
    out: list[str] = []
    seen: set[str] = set()
    for _, span in sorted(hits, key=lambda h: h[0]):
        key = _normalise_prose(span)
        if key and key not in seen:
            seen.add(key)
            out.append(span)
    return out


def _is_citable_quotation(span: str) -> bool:
    """Is this quoted span a quotation of source prose, or something else?

    Five conservatism rules, each aimed at a class of quoted string that is not a
    quotation and would otherwise be flagged:

    1. A span containing `...` or `…` splices two sentences and will not appear
       verbatim anywhere. Skipped, not flagged.
    2. Under `MIN_QUOTE_CHARS` normalised characters it is a label or a word, not
       a citation.
    3. Under `MIN_QUOTE_WORDS` raw words it is a name, a unit or a value.
    4. With no English function word in it, it is not prose: quoted argument
       names, mnemonics (`DRHO`), units (`g/cm3`), enum values and equations all
       fail this and all pass a bare length test.
    5. A span that itself resolves as a citation is a pointer, not a quotation -
       a tool that names an anchor inside its method text is citing, not quoting.
    """
    if any(e in span for e in _ELLIPSIS):
        return False
    norm = _normalise_prose(span)
    if len(norm) < MIN_QUOTE_CHARS:
        return False
    if len(span.split()) < MIN_QUOTE_WORDS:
        return False
    if not (set(norm.split()) & FUNCTION_WORDS):
        return False
    if _source_resolves(span)[0]:
        return False
    return True


def _inline_texts(text: str) -> list[tuple[str, str]]:
    """Passages named *inside* the same text as the quotation.

    Rule 11's premise is that the result quotes a sentence **from its source**.
    Where a tool writes the anchor next to the quote - `asquith#32: "similar in
    depth of investigation to the short normal"` on a result whose own `source`
    is `#43` - the quotation is attributed to the anchor beside it, and holding
    it to the entry's `source` would flag a correct citation. Measured: this
    silences 7 findings in the shipped repo, every one of them a flag that names
    its own anchor.
    """
    out: list[tuple[str, str]] = []
    for tok in re.split(r"[\s;]+", text):
        tok = tok.strip(" ,()'\"`.")
        if not tok or ("/" not in tok and ".md" not in tok):
            continue
        got = _token_text(tok)
        if got is not None:
            out.append((tok, got))
    return out


def _quote_claims(entry: "_Entry") -> list[tuple[str, str, str]]:
    """(where, span, containing text) for every citable quotation the entry puts
    in front of a reader: its `method`, each of its `flags`, and a top-level
    `quote` field."""
    out: list[tuple[str, str, str]] = []
    fields: list[tuple[str, str]] = [("method", entry.method)]
    fields += [(f"flags[{i}]", f) for i, f in enumerate(entry.flags)]
    for where, text in fields:
        if not text:
            continue
        for span in _quoted_spans(text):
            if _is_citable_quotation(span):
                out.append((where, span, text))
    # A `quote` field is the quotation; the tools that carry one
    # (tools/deliverability/rate.py:77, tools/perforating/config.py:286) store
    # the bare sentence with no quote marks around it, so the whole value is the
    # span. Quote marks inside it are still honoured.
    if entry.quote:
        for span in [entry.quote] + _quoted_spans(entry.quote):
            if _is_citable_quotation(span):
                out.append(("quote", span, entry.quote))
                break
    return out


def _quote_is_present(span: str, passages: Sequence[tuple[str, str]]) -> bool:
    """Is this quotation in one of these passages?

    Two attempts, and only a miss on both is a finding. The second drops
    parentheticals: a tool that writes its page note inside the quote marks -
    `"…below 2000 psi (ahmed#114, p. 546)"` - is quoting faithfully and
    annotating, and the annotation is not the source's words.
    """
    norm = _normalise_prose(span)
    if any(norm in text for _, text in passages):
        return True
    bare = _normalise_prose(_PARENTHETICAL.sub(" ", span))
    if len(bare) >= MIN_QUOTE_CHARS and bare != norm:
        return any(bare in text for _, text in passages)
    return False


def _has_depth(entry: Any) -> float | None:
    for k in ("depth_md", "top_md", "base_md", "depth", "md", "tvd", "depth_ft"):
        v = _numeric(_attr(entry, k))
        if v is not None:
            return v
    return None


def provenance_audit(state: Any, *, require_anchor: bool = True) -> Quantity | Refusal:
    """Flag every value in the state object that does not carry its provenance.

    Strict by design: a value with a method but no anchor is an orphan, and a
    value whose anchor does not open is an orphan. Anchors are resolved by
    reading the corpus with the segmentation `scripts/show_segment.py` uses, so
    "clean" means show_segment.py could actually print the passage.

    Flagging, not blocking: blocking is gate_check (#66)'s job.
    """
    if not _is_mapping(state):
        return Refusal(
            reason=f"provenance_audit cannot read the state object: got {type(state).__name__}",
            needed=("a serialized ZoneEvaluation (well-log-agent.md#core-object)",),
            source=SOURCE_STATE,
        )

    well = _dict(_section(state, "well"))
    datum = _dict(_section(state, "datum"))
    entries = _entries(state)
    ledger = _tool_ledger(state)
    assumptions = [_dict(a) for a in _listof(_section(state, "assumptions"))]
    evidence = [_dict(e) for e in _listof(_section(state, "evidence"))]
    offsets = [_dict(o) for o in _listof(_section(state, "offsets"))]
    interval = _dict(_section(state, "interval"))

    found: list[tuple[int, int, dict[str, Any]]] = []
    not_audited: list[str] = []
    audited = 0
    quoted = 0          # citable quotations rule 11 was able to look up
    dirty: set[str] = set()

    def flag(rule: int, order: int, name: str, field: str, detail: str, remedy: str) -> None:
        found.append((rule, order, _finding(rule, name, field, detail, remedy)))
        dirty.add(field)

    # Rules 1-5 over computed[].
    if not entries:
        not_audited.append("computed[] (absent or empty)")
    for e in entries:
        audited += 1
        if not e.is_refusal:
            # A Range carries its constituents in `members`, not `inputs`: the
            # type has no `inputs` field (tools/result.py:52). Rule 1 asks whether
            # anything says what the value was made from, and `members` does, so a
            # band with populated members is not an orphan. specs/67 makes the
            # same carve-out for Refusal and rule 2; this is its Range half.
            if not e.inputs and not e.members:
                flag(1, e.index, "missing_inputs", f"{e.path}.inputs",
                     f"{e.field or e.method or 'value'} = {e.display()} carries no inputs "
                     "and no members, so it cannot be recomputed or checked",
                     "record the arguments the tool was called with (harness-implementation."
                     "md:109: addComputed() refuses a value without inputs and method)")
            if not e.method:
                flag(2, e.index, "missing_method", f"{e.path}.method",
                     f"{e.field or 'value'} = {e.display()} names no method",
                     "record the published equation or procedure that produced it")
            if e.method and not e.source:
                flag(3, e.index, "missing_source", f"{e.path}.source",
                     f"{e.field or e.method!r} has a method but no anchor: a method with no "
                     "source is a claim about a book nobody named",
                     "cite the corpus anchor the method came from "
                     "(<section>/<slug>#<n>), the same one show_segment.py resolves")
        if e.source and require_anchor:
            ok, why = _source_resolves(e.source)
            if not ok:
                flag(4, e.index, "unresolvable_source", f"{e.path}.source",
                     f"source {e.source!r} does not resolve - {why}",
                     "correct the anchor until `python3 scripts/show_segment.py "
                     "'<anchor>'` prints the passage")
            else:
                # Rule 11 - the anchor opens, but onto what? Only a quotation can
                # be checked without judgement, so only a quotation is checked.
                claims = _quote_claims(e)
                if claims:
                    quoted += len(claims)
                    cited = _source_texts(e.source)
                    opened = ", ".join(p for p, _ in cited) or "nothing that opens"
                    for k, (where, span, text) in enumerate(claims):
                        passages = cited + _inline_texts(text)
                        if _quote_is_present(span, passages):
                            continue
                        flag(11, e.index * 100 + k, "quote_not_in_source",
                             f"{e.path}.{where}",
                             f"quotes {span.strip()!r}, which does not appear in "
                             f"{e.source!r} (searched: {opened}). The anchor resolves; it "
                             "does not contain the sentence the result attributes to it",
                             "cite the segment the sentence is actually in - "
                             "`python3 scripts/kb_grep.py` or show_segment.py over the "
                             "neighbouring segments - or drop the quotation marks if the "
                             "words are the tool's own")

    if not require_anchor:
        not_audited.append("rule 4 unresolvable_source (require_anchor=False)")
        not_audited.append("rule 11 quote_not_in_source (require_anchor=False: the "
                           "passage cannot be opened, so the quote cannot be looked up)")
    elif not quoted:
        not_audited.append("rule 11 quote_not_in_source (no computed entry quotes its "
                           "source; nothing to check against)")
    if ledger is None:
        not_audited.append("rule 5 untraceable_to_tool (no toolCalls ledger in the object)")
    else:
        names = {_text(c.get("tool")).lower() for c in ledger if _text(c.get("tool"))}
        for e in entries:
            if e.is_refusal:
                continue
            if e.tool:
                if e.tool.lower() not in names:
                    flag(5, e.index, "untraceable_to_tool", f"{e.path}.tool",
                         f"tool {e.tool!r} appears in no toolCalls entry; a figure that is "
                         "not in the ledger did not come from a tool",
                         "route the call through call-tool.ts so the ledger records it")
                continue
            blob = _tokens(f"{e.method} {e.field}")
            if not any(_tokens(n) <= blob for n in names):
                flag(5, e.index, "untraceable_to_tool", f"{e.path}.method",
                     f"method {e.method!r} matches no tool in the ledger "
                     f"({sorted(names)})",
                     "carry the producing tool's name on the entry as `tool`, or route the "
                     "call through the ledger")

    # Rule 6 - bare depths.
    api = _text(well.get("api"))
    reference = _text(datum.get("reference")).upper()
    if interval and any(_numeric(interval.get(k)) is not None
                        for k in ("top_md", "base_md", "top_ss", "base_ss")):
        audited += 1
        missing = [n for n, v in (("well.api", api),
                                  ("datum.reference", reference)) if not v]
        if missing:
            flag(6, 0, "bare_depth", "interval",
                 f"interval carries depths but {', '.join(missing)} is absent",
                 "every depth carries well.api and the datum reference "
                 "(well-log-agent.md:266)")
    for e in entries:
        if _has_depth(e.raw) is None:
            continue
        missing = [n for n, v in (("well.api", e.well_api or api),
                                  ("datum.reference", reference)) if not v]
        if missing:
            flag(6, 1000 + e.index, "bare_depth", f"{e.path}.depth_md",
                 f"depth {_has_depth(e.raw)} with {', '.join(missing)} absent",
                 "set well.api and datum.reference, or carry well_api on the entry")
    for i, off in enumerate(offsets):
        for j, pick in enumerate(_listof(off.get("picks"))):
            if _has_depth(pick) is None:
                continue
            audited += 1
            if not _text(off.get("api")):
                flag(6, 2000 + i * 100 + j, "bare_depth", f"offsets[{i}].picks[{j}]",
                     f"pick at depth {_has_depth(pick)} on an offset with no api",
                     "identify the offset well by API, or drop the pick")

    # Rule 7 - silent assumptions.
    if not assumptions:
        not_audited.append("assumptions[] (absent or empty)")
    for i, a in enumerate(assumptions):
        audited += 1
        src = _text(a.get("source")).lower()
        if not _text(a.get("field")) or a.get("value") is None or src not in ASSUMPTION_SOURCES:
            flag(7, i, "silent_assumption", f"assumptions[{i}]",
                 f"field={a.get('field')!r} value={a.get('value')!r} source={a.get('source')!r};"
                 f" source must be one of {ASSUMPTION_SOURCES}",
                 "record what was assumed, its value, and whether it is a default, a user "
                 "override, or derived (nothing is assumed silently)")

    # Rules 8-9 - evidence.
    if not evidence:
        not_audited.append("evidence[] (absent or empty)")
    for i, ev in enumerate(evidence):
        audited += 1
        sid = _text(ev.get("source_id") or ev.get("source"))
        kind = _text(ev.get("kind")).lower()
        if not sid or kind not in EVIDENCE_KINDS:
            flag(8, i, "unattributed_evidence", f"evidence[{i}]",
                 f"source_id={ev.get('source_id')!r} kind={ev.get('kind')!r}; kind must be "
                 f"one of {EVIDENCE_KINDS}",
                 "attribute the claim and state whether it is measured, documented or stated")
        elif kind in ("measured", "documented"):
            user = (_text(ev.get("source_kind")).lower() == "user"
                    or sid.lower().startswith(USER_SOURCE_PREFIXES))
            if user:
                flag(9, i, "stated_promoted", f"evidence[{i}].kind",
                     f"{sid!r} is a user statement carried as {kind!r}; nothing the user said "
                     "becomes a measurement",
                     "set kind='stated'; promote it only when a measurement or a document "
                     "arrives with its own source_id")

    # Rule 10 - unsourced datum.
    if datum and any(_numeric(datum.get(k)) is not None for k in ("kb_ft", "gl_ft", "epd_ft")):
        audited += 1
        if not _meaningful(datum.get("source")):
            flag(10, 0, "datum_unsourced", "datum.source",
                 f"kb_ft={datum.get('kb_ft')!r} gl_ft={datum.get('gl_ft')!r} with no source",
                 "name where the elevation came from (LAS ~PARAMETER EKB, W-2, G-1)")
        # A datum source is a record reference (W-2, LAS ~PARAMETER), not a corpus
        # anchor, so rule 4 does not apply to it.

    if require_anchor and _SEGMENTATION_ERROR:
        return Refusal(
            reason="cannot resolve corpus anchors: "
                   f"{_SEGMENTATION_ERROR[0]}. The audit refuses rather than passing values "
                   "whose anchors it could not check - a wrong citation with a clean bill is "
                   "the one outcome this tool exists to prevent",
            needed=("run from the repo root so scripts/build_toc.py is importable",
                    "or pass require_anchor=False and accept an unverified result"),
            source=SOURCE_STATE,
        )

    findings = _ordered(found)
    counts: dict[int, int] = {}
    for f in findings:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1

    return Quantity(
        value=float(len(findings)),
        unit="orphans",
        method="provenance_audit rules v1",
        source=SOURCE_STATE,
        inputs={
            "findings": findings,
            "audited": audited,
            "clean": max(audited - len(dirty), 0),
            "quotations_checked": quoted,
            "counts_by_rule": counts,
        },
        assumptions={
            "require_anchor": require_anchor,
            "not_audited": tuple(not_audited),
            "rules_evaluated": ("1 missing_inputs", "2 missing_method", "3 missing_source",
                                "4 unresolvable_source", "5 untraceable_to_tool",
                                "6 bare_depth", "7 silent_assumption",
                                "8 unattributed_evidence", "9 stated_promoted",
                                "10 datum_unsourced", "11 quote_not_in_source"),
            "anchor_resolution": ("build_toc.segment via tools.kb - the same segmentation "
                                  "scripts/show_segment.py uses"),
            "quote_matching": (
                f"normalised substring (case, punctuation, markdown emphasis and line "
                f"wrapping folded); spans under {MIN_QUOTE_CHARS} normalised chars or "
                f"{MIN_QUOTE_WORDS} words, spliced spans ('...'), spans with no English "
                "function word, and spans that are themselves citations are not checked"),
            "value_meaning": "count of orphan findings; they are in inputs['findings']",
        },
    )
