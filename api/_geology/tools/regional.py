"""Regional screening lookups for the Bend Arch and the Eastern Shelf.

Three tools that answer the question the petrophysics layer cannot: *does this
other lease look like the one that just worked*. They share a shape with the rest
of group G — exact keys, refusals rather than near matches, every value carrying
where it came from — and they read tables that ship with the corpus.

## Why these are separate from `geolex_lookup`

`geolex_lookup` (#61) resolves the Pennsylvanian outcrop belt of Eargle 1960 and
nothing else, because that is the one report behind it. It is exact and anchored
and should stay that way. The strings an operator actually types on a completion
report — CADOO, GUNSIGHT LIME, MISSISSIPPIAN - DISPOSAL — are not outcrop names,
are frequently misspelled, and half the time name a local driller's sand that was
never formally described. Bolting that onto an anchored lookup would turn a
citable tool into a guessing one.

So `formation_alias_resolve` is the messy front door and `geolex_lookup` stays
the clean one. The alias table's canonical targets are a closed list — the
subsurface column in `tables/strat-column-bend-arch.json` plus `GEOLEX_UNITS` —
and a string that does not land on it resolves to a refusal or to an honest
"informal, no formal equivalent", never to the nearest plausible unit.

## Where the numbers come from

Depth windows are computed from `rrc.completion_formation`, the formation-top
section of every W-2/G-1 filed in the six counties — about 16,000 filings. No
publication states a per-county depth window for these units; the filings do, and
every window carries the sample count behind it so a two-well county reads as
one. Lithology quotes come from corpus documents and carry the anchor they were
copied from, verified verbatim at build time.
"""
from __future__ import annotations

import functools
import json
import os
import pathlib
import re
from typing import Any

from .result import Quantity, Refusal

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Same variable the TypeScript side reads, so both halves see one corpus.
CORPUS = pathlib.Path(os.environ.get("GEOLOGY_CORPUS_ROOT") or ROOT)
TABLES = CORPUS / "tables"

ALIASES_FILE = TABLES / "formation-aliases.json"
COLUMN_FILE = TABLES / "strat-column-bend-arch.json"
RESERVOIRS_FILE = TABLES / "reservoir-parameters.json"
FIGURES_FILE = TABLES / "figures.json"

SOURCE_RRC = ("rrc.completion_formation joined to rrc.completion, Texas RRC "
              "public record via the Tiger Cloud mirror")
SOURCE_COLUMN = "tables/strat-column-bend-arch.json (quotes verified against their anchors)"

# A window built on fewer filings than this is reported, but flagged: three wells
# in a county is a fact about those three wells, not about the county.
THIN_SAMPLE = 8


def _canonical(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def _load(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


@functools.lru_cache(maxsize=1)
def _aliases() -> dict[str, Any] | None:
    return _load(ALIASES_FILE)


@functools.lru_cache(maxsize=1)
def _column() -> dict[str, Any] | None:
    return _load(COLUMN_FILE)


@functools.lru_cache(maxsize=1)
def _alias_index() -> dict[str, dict]:
    """Every spelling that resolves, keyed canonically.

    Both the cleaned string and each raw form it absorbed are keys, so
    "MISSISSIPPIAN - DISPOSAL" resolves as readily as "Mississippian" — the
    regulatory suffix was folded at build time and the caller should not have to
    know that.
    """
    data = _aliases()
    if not data:
        return {}
    index: dict[str, dict] = {}
    for record in data["aliases"]:
        for key in [record["clean"], *record.get("raw_forms", [])]:
            index.setdefault(_canonical(key), record)
    return index


@functools.lru_cache(maxsize=1)
def _column_index() -> dict[str, dict]:
    data = _column()
    return {u["name"]: u for u in data["units"]} if data else {}


def _window(unit: str, county: str | None) -> tuple[dict | None, str | None]:
    """The depth window for `unit`, in `county` if named, else the whole area."""
    data = _aliases()
    if not data:
        return None, None
    windows = data.get("depth_windows", {}).get(unit)
    if not windows:
        return None, None
    if county:
        key = county.strip().upper()
        return (windows.get(key), key) if key in windows else (None, key)
    # No county named: pool every county, weighted by sample count.
    total = sum(w["depth_samples"] for w in windows.values())
    if not total:
        return None, None
    pooled = {
        "depth_samples": total,
        "depth_p10_ft": round(sum(w["depth_p10_ft"] * w["depth_samples"]
                                  for w in windows.values()) / total, 1),
        "depth_p50_ft": round(sum(w["depth_p50_ft"] * w["depth_samples"]
                                  for w in windows.values()) / total, 1),
        "depth_p90_ft": round(sum(w["depth_p90_ft"] * w["depth_samples"]
                                  for w in windows.values()) / total, 1),
    }
    return pooled, None


def _bracket(record: dict, county: str | None) -> dict | None:
    """Which formal units an informal sand sits between, by its own depths.

    Arithmetic, not opinion: take the informal name's median depth in this county
    and find the formal units whose median depth falls either side of it. It is
    the only defensible thing to say about a name nobody ever formally described,
    and it is exactly what an operator wants — "the Vogstberger is a Strawn-level
    sand here" — without pretending the Vogstberger IS the Strawn.
    """
    counties = record.get("counties", {})
    if county:
        stats = counties.get(county.strip().upper())
    else:
        sampled = [c for c in counties.values() if c.get("depth_samples")]
        stats = max(sampled, key=lambda c: c["depth_samples"]) if sampled else None
    if not stats or stats.get("depth_p50_ft") is None:
        return None

    depth = stats["depth_p50_ft"]
    marks: list[tuple[float, str]] = []
    for unit in _column_index():
        window, _ = _window(unit, county)
        if window and window.get("depth_p50_ft") is not None:
            marks.append((window["depth_p50_ft"], unit))
    if not marks:
        return None
    marks.sort()

    above = [name for d, name in marks if d <= depth]
    below = [name for d, name in marks if d > depth]
    return {
        "median_depth_ft": depth,
        "depth_samples": stats["depth_samples"],
        "shallower_formal_unit": above[-1] if above else None,
        "deeper_formal_unit": below[0] if below else None,
        "basis": "median filed top depth against the same counties' formal-unit medians",
    }


def formation_alias_resolve(raw: str, county: str | None = None) -> Quantity | Refusal:
    """Resolve one operator-typed RRC formation string to the canonical column.

    Answers what rock "CADOO", "GUNSIGHT LIME" or "MISSISSIPPIAN - DISPOSAL"
    names, and how deep that unit is filed in the county asked about. Three
    outcomes, and only the first is a formal unit: a canonical name; an informal
    driller's sand bracketed by depth between the formal units around it; or a
    refusal. Never a near match.
    """
    if not isinstance(raw, str):
        raise TypeError("formation_alias_resolve takes a string")
    if county is not None and not isinstance(county, str):
        raise TypeError("county must be a string when supplied")
    if not raw.strip():
        raise ValueError("formation_alias_resolve needs a non-empty string")

    data = _aliases()
    if not data:
        return Refusal(
            reason=f"the alias table is not present at {ALIASES_FILE.name}",
            needed=("scripts/pull_rrc_formations.py then scripts/build_formation_aliases.py",),
            source="",
        )

    covered = {c.upper() for c in data["counties"]}
    asked = county.strip().upper() if county else None
    if asked and asked not in covered:
        return Refusal(
            reason=(f"county {county!r} is outside the area this table covers; "
                    "this tool will not extrapolate a depth window across the basin"),
            needed=tuple(sorted(covered)),
            source=SOURCE_RRC,
        )

    record = _alias_index().get(_canonical(raw))
    if record is None:
        return Refusal(
            reason=(f"no completion filing in these counties spells a formation "
                    f"{raw!r}; this tool matches recorded spellings and will not "
                    "guess the nearest one"),
            needed=(f"one of {len(_alias_index())} spellings recorded in "
                    f"{', '.join(sorted(covered))}",),
            source=SOURCE_RRC,
        )

    verdict = record["verdict"]
    flags: list[str] = []

    if verdict in ("not_a_formation", "unmapped"):
        return Refusal(
            reason=(f"{raw!r} is recorded on {record['filings']} filings but does not "
                    f"name a rock unit ({record.get('note') or verdict})"),
            needed=("a formation name; this string is a regulatory or descriptive entry",),
            source=SOURCE_RRC,
        )

    if verdict == "informal":
        bracket = _bracket(record, asked)
        if bracket is None:
            flags.append("no filed depths for this name in the county asked about, so "
                         "it could not be bracketed against the formal column")
        return Quantity(
            value=float(record["filings"]),
            unit="filings",
            method="formation_alias_resolve v1 - informal driller's name, bracketed by filed depth",
            source=SOURCE_RRC,
            inputs={
                "raw": raw, "cleaned": record["clean"],
                "raw_forms": tuple(record.get("raw_forms", ())),
                "county": asked, "rank": "informal", "canonical": None,
                "bracket": bracket,
                "note": record.get("note") or "",
            },
            assumptions={
                "resolution": "informal",
                "why": ("this name is used on completion reports but has no entry on the "
                        "canonical column; it is a local driller's or lease name"),
            },
            flags=tuple(flags),
        )

    unit = _column_index().get(record["canonical"])
    window, window_county = _window(record["canonical"], asked)
    if window and window["depth_samples"] < THIN_SAMPLE:
        flags.append(f"depth window rests on {window['depth_samples']} filed tops; "
                     "treat it as those wells, not as the county")
    if asked and window is None:
        flags.append(f"no filed tops for this unit in {asked}; "
                     "no depth window could be computed there")
    if record.get("confidence") == "low":
        flags.append("spelling matched with low confidence at build time")

    return Quantity(
        value=float(record["filings"]),
        unit="filings",
        method="formation_alias_resolve v1 - canonical unit from the closed column",
        source=SOURCE_RRC + ("; " + SOURCE_COLUMN if unit else ""),
        inputs={
            "raw": raw, "cleaned": record["clean"],
            "raw_forms": tuple(record.get("raw_forms", ())),
            "county": asked,
            "canonical": record["canonical"],
            "rank": (unit or {}).get("rank"),
            "system": (unit or {}).get("system"),
            "above": (unit or {}).get("above"),
            "below": (unit or {}).get("below"),
            "lithology": (unit or {}).get("lithology"),
            "lithology_anchor": (unit or {}).get("anchor"),
            "depth_window_ft": window,
            "depth_window_county": window_county,
        },
        assumptions={
            "resolution": "formal",
            "canonical_source": ("closed union of tables/strat-column-bend-arch.json "
                                 "and GEOLEX_UNITS; an off-list target is dropped at "
                                 "build time, never recorded"),
            "depth_basis": "percentiles of filed formation-top depths, 100-12000 ft band",
        },
        flags=tuple(flags),
    )


# --- reservoir parameters ----------------------------------------------------

SOURCE_FIELDS = ("rrc.field, rrc.lease_production and rrc.completion_formation, "
                 "Texas RRC public record via the Tiger Cloud mirror")

# What the public record cannot tell you, named explicitly so the answer says so
# rather than leaving the caller to assume the fields are merely missing.
NOT_IN_THE_RECORD = (
    "porosity", "net pay", "water saturation", "drive mechanism", "recovery factor",
    "original oil in place",
)


@functools.lru_cache(maxsize=1)
def _reservoirs() -> dict[str, Any] | None:
    return _load(RESERVOIRS_FILE)


@functools.lru_cache(maxsize=1)
def _reservoir_index() -> dict[str, list[dict]]:
    data = _reservoirs()
    if not data:
        return {}
    index: dict[str, list[dict]] = {}
    for record in data["reservoirs"]:
        keys = {record["field_name"], record["field"], record["field_no"]}
        if record["reservoir"]:
            keys.add(f"{record['field']} ({record['reservoir']})")
        for key in keys:
            if key:
                index.setdefault(_canonical(key), []).append(record)
    return index


def reservoir_parameter_lookup(reservoir: str,
                               county: str | None = None) -> Quantity | Refusal:
    """Discovery, cumulative production and completion depths for one RRC field.

    Keyed on the field name as the RRC writes it — "K-M-A", "CASH (STRAWN 3820)"
    — or on its field number. Returns what the public record actually carries and
    names what it does not: porosity, net pay, saturation, drive and recovery
    factor are reservoir-engineering measurements no filing reports, and this
    tool will not estimate them.
    """
    if not isinstance(reservoir, str):
        raise TypeError("reservoir_parameter_lookup takes a string")
    if county is not None and not isinstance(county, str):
        raise TypeError("county must be a string when supplied")
    if not reservoir.strip():
        raise ValueError("reservoir_parameter_lookup needs a non-empty name")

    data = _reservoirs()
    if not data:
        return Refusal(
            reason=f"the reservoir table is not present at {RESERVOIRS_FILE.name}",
            needed=("scripts/pull_rrc_reservoirs.py",),
            source="",
        )

    covered = {c.upper() for c in data["counties"]}
    asked = county.strip().upper() if county else None
    if asked and asked not in covered:
        return Refusal(
            reason=f"county {county!r} is outside the area this table covers",
            needed=tuple(sorted(covered)),
            source=SOURCE_FIELDS,
        )

    matches = _reservoir_index().get(_canonical(reservoir), [])
    if asked:
        matches = [m for m in matches if m["county"] == asked]
    if not matches:
        return Refusal(
            reason=(f"no RRC field named {reservoir!r}"
                    + (f" in {asked}" if asked else "")
                    + "; this tool matches the field name as the RRC records it "
                      "and will not guess a near neighbour"),
            needed=("an RRC field name, e.g. 'K-M-A' or 'CASH (STRAWN 3820)', "
                    "or an eight-digit field number",),
            source=SOURCE_FIELDS,
        )

    # More than one field can share a name across counties; the biggest producer
    # is returned and the rest are named so the caller can disambiguate.
    matches.sort(key=lambda m: -(m["cum_oil_bbl"] or 0))
    record, others = matches[0], matches[1:]

    flags: list[str] = []
    if others:
        flags.append(f"{len(others)} other field(s) share this name; "
                     "the largest producer is returned - pass county to pick one")
    if not record["reported_cycles"]:
        flags.append("no production has been reported for this field in the mirror")
    if record["wildcat"]:
        flags.append("flagged wildcat in the RRC field record")

    return Quantity(
        value=float(record["cum_oil_bbl"] or 0.0),
        unit="bbl",
        method="reservoir_parameter_lookup v1 - cumulative reported oil for the field",
        source=SOURCE_FIELDS,
        inputs={
            "field_no": record["field_no"],
            "field_name": record["field_name"],
            "field": record["field"],
            "reservoir": record["reservoir"] or None,
            "reservoir_depth_label_ft": record["reservoir_depth_label_ft"],
            "county": record["county"],
            "discovery_year_oil": record["discovery_year_oil"],
            "discovery_year_gas": record["discovery_year_gas"],
            "cum_oil_bbl": record["cum_oil_bbl"],
            "cum_gas_mcf": record["cum_gas_mcf"],
            "cum_casinghead_mcf": record["cum_casinghead_mcf"],
            "leases": record["leases"],
            "operators": record["operators"],
            "first_production": record["first_production"],
            "last_production": record["last_production"],
            "reported_cycles": record["reported_cycles"],
            "completion_formations": tuple(
                tuple(sorted(f.items())) for f in record["completion_formations"]),
            "other_fields_with_this_name": tuple(
                (m["field_no"], m["county"]) for m in others),
        },
        assumptions={
            "not_in_the_public_record": NOT_IN_THE_RECORD,
            "production_basis": ("summed lease_production cycles for this field number; "
                                 "leases that never filed are absent, so cumulative "
                                 "volumes are a floor"),
            "reservoir_name_basis": ("the parenthetical in the RRC field name; pass it "
                                     "to formation_alias_resolve to reach the column"),
        },
        flags=tuple(flags),
    )


# --- figures -----------------------------------------------------------------

SOURCE_FIGURES = "tables/figures.json; pages rendered from knowledge-base/originals"


@functools.lru_cache(maxsize=1)
def _figures() -> dict[str, Any] | None:
    return _load(FIGURES_FILE)


@functools.lru_cache(maxsize=1)
def _figure_index() -> dict[str, dict]:
    data = _figures()
    return {_canonical(f["figure_id"]): f for f in data["figures"]} if data else {}


def _figure_payload(record: dict) -> dict:
    """The record as the harness receives it, with the image located.

    `image` is the key `call-tool.ts` looks for: when a result carries one, the
    harness reads that file out of the corpus and attaches it to the next model
    turn as an image block. Everything else here is the finding aid — enough to
    decide whether the sheet is worth the tokens.
    """
    return {
        "figure_id": record["figure_id"],
        "doc_slug": record["doc_slug"],
        "page": record["page"],
        "kind": record["kind"],
        "title": record["title"],
        "shows": record["shows"],
        "counties": tuple(record["counties"]),
        "formations": tuple(record["formations"]),
        "fields": tuple(record["fields"]),
        "contour_interval": record["contour_interval"] or None,
        "value_range": record["value_range"] or None,
        "trend": record["trend"] or None,
        "cannot_answer": record["cannot_answer"] or None,
        "image": {
            "path": record["image_path"],
            "media_type": "image/jpeg",
            "bytes": record["image_bytes"],
        },
    }


def figure_search(query: str, county: str | None = None,
                  kind: str | None = None, limit: int = 8) -> Quantity | Refusal:
    """Find map and cross-section sheets by what they cover.

    The finding aid, not the sheet: this returns figure ids and what each one
    shows so a caller can pick, then `figure_fetch` hands over the image itself.
    Matching is over the indexed title, description, formations, fields and
    counties — deliberately lexical, so a hit is explainable.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("figure_search needs a non-empty query")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("limit must be a positive int")

    data = _figures()
    if not data:
        return Refusal(
            reason=f"the figure index is not present at {FIGURES_FILE.name}",
            needed=("scripts/build_figures.py",),
            source="",
        )

    terms = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
    if not terms:
        raise ValueError("figure_search needs a query with a word longer than two letters")

    wanted_county = county.strip().upper() if county else None
    scored: list[tuple[int, dict]] = []
    for record in data["figures"]:
        if wanted_county and wanted_county not in record["counties"]:
            continue
        if kind and record["kind"] != kind:
            continue
        haystack = " ".join([
            record["title"], record["shows"], record["kind"],
            " ".join(record["formations"]), " ".join(record["fields"]),
            " ".join(record["counties"]), record["doc_slug"],
        ]).lower()
        score = sum(haystack.count(t) for t in terms)
        if score:
            scored.append((score, record))

    if not scored:
        return Refusal(
            reason=(f"no indexed figure matches {query!r}"
                    + (f" in {wanted_county}" if wanted_county else "")
                    + (f" of kind {kind!r}" if kind else "")),
            needed=(f"{len(data['figures'])} figures are indexed; "
                    "try a formation, a county, or a field name",),
            source=SOURCE_FIGURES,
        )

    scored.sort(key=lambda s: (-s[0], s[1]["figure_id"]))
    hits = [_figure_payload(r) for _, r in scored[:limit]]
    return Quantity(
        value=float(len(scored)),
        unit="figures",
        method="figure_search v1 - lexical match over the figure index",
        source=SOURCE_FIGURES,
        inputs={"query": query, "county": wanted_county, "kind": kind,
                "returned": tuple(tuple(sorted(h.items(), key=lambda kv: kv[0]))
                                  for h in hits),
                "figure_ids": tuple(h["figure_id"] for h in hits)},
        assumptions={"matching": "lexical over title, description, formations, "
                                 "fields, counties and document slug"},
        flags=("more matches than the limit; raise limit to see them",) if len(scored) > limit else (),
    )


def figure_fetch(figure_id: str) -> Quantity | Refusal:
    """Hand over one map or cross-section — the image itself, not a description.

    The index says a sheet exists and roughly what it covers; this returns the
    rendered page so the model reads the contours, the legend and the well
    symbols directly. Transcribing a map once at ingest and answering from that
    prose forever is a game of telephone, and the thing it loses is exactly the
    detail a screen turns on.
    """
    if not isinstance(figure_id, str):
        raise TypeError("figure_fetch takes a string figure id")
    if not figure_id.strip():
        raise ValueError("figure_fetch needs a non-empty figure id")

    data = _figures()
    if not data:
        return Refusal(
            reason=f"the figure index is not present at {FIGURES_FILE.name}",
            needed=("scripts/build_figures.py",),
            source="",
        )

    record = _figure_index().get(_canonical(figure_id))
    if record is None:
        return Refusal(
            reason=(f"no figure with id {figure_id!r}; ids look like "
                    "'allen-1930-breckenridge-oil-field#p12'"),
            needed=("figure_search to find an id",),
            source=SOURCE_FIGURES,
        )

    payload = _figure_payload(record)
    flags: list[str] = []
    # Deliberately not a refusal when the file is absent here.
    #
    # The rendered pages are 161 MB and do not ship inside the deployed function
    # — they live in object storage, and the harness resolves the path against
    # disk first and the bucket second. So on the deployed function this check is
    # expected to miss, and refusing on it would turn every figure request in
    # production into a refusal while passing locally. The integrity check that
    # matters (every indexed figure has an image) runs at build time, in
    # `tests/test_regional.py`, against the repository where the files do exist.
    if not (CORPUS / record["image_path"]).exists():
        flags.append("the image is not on this host's disk; the harness resolves it "
                     "from object storage")
    return Quantity(
        value=float(record["page"]),
        unit="page",
        method="figure_fetch v1 - the rendered page, for the model to read directly",
        source=f"{record['doc_slug']} p.{record['page']}",
        inputs=payload,
        assumptions={
            "the_image_is_the_source": ("the indexed description is a finding aid; "
                                        "read the image for anything that matters"),
            "render": f"{data.get('long_edge_px')} px long edge, JPEG",
        },
        flags=tuple(flags),
    )
