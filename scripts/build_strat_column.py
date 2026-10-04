#!/usr/bin/env python3
"""Build the Bend Arch / Eastern Shelf subsurface stratigraphic column.

`geolex_lookup` (#61) resolves the Pennsylvanian **outcrop** belt of Eargle 1960:
Cisco, Canyon and Strawn plus their named members. Everything an operator
actually perforates on the Bend Arch below the Canyon — Caddo, Marble Falls,
Bend conglomerate, Barnett, Ellenburger — is subsurface and is not in that
report, so `GEOLEX_UNITS` cannot resolve it. This script builds the missing
half from documents the corpus already holds.

Two rules make the output trustworthy:

**The column is written here, not by the model.** `COLUMN` below is the ordered
list of units and their rank, and it is the only set of names that can appear in
the output. The model is asked one question per unit — *which passage in these
segments describes this unit, and what does it say* — and its answer is discarded
if the unit is not in `COLUMN`.

**Every record carries a verbatim quote and the anchor it came from**, and the
quote is checked back against the segment (`corpus_index.quote_resolves`) before
the record is written. A unit with no supporting passage is emitted with
`lithology: null` rather than a plausible sentence, because "the corpus does not
say" is the honest answer and the resolver has to be able to give it.

Usage:
  python3 scripts/build_strat_column.py --estimate
  python3 scripts/build_strat_column.py --only ellenburger
  python3 scripts/build_strat_column.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import sys

from anthropic import AsyncAnthropic

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "api" / "_geology"))
from build_toc import load_api_key  # noqa: E402
from corpus_index import anchor_text, quote_resolves, search  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent / "geology-corpus"
OUT = ROOT / "tables" / "strat-column-bend-arch.json"

MODEL = "claude-sonnet-5"
# Reading a named unit out of segments handed over in full is scoped extraction,
# not judgment: the unit list, the ordering and the acceptance test are all code.
EFFORT = "low"
MAX_CONCURRENCY = 8
SEGMENTS_PER_UNIT = 4
# Segments are handed over whole rather than as a window around the match. The
# first build passed a 1000-character excerpt and got back quotes that ended
# mid-word ("most of th") because the model was quoting the truncation, not the
# source. Whole segments cost more tokens and remove the failure entirely.
MAX_SEGMENT_CHARS = 9000
# A quote shorter than this is a fragment, not a description.
MIN_QUOTE_CHARS = 40

# Ordered youngest -> oldest. `search_terms` is what the corpus calls the unit,
# which is not always the canonical name (the Bend conglomerate is discussed as
# "Bend" as often as by its full name).
COLUMN: list[dict] = [
    {"name": "wichita group", "rank": "group", "system": "Permian",
     "search_terms": ["Wichita group", "Wichita Group"], "in_geolex": True},
    {"name": "cisco group", "rank": "group", "system": "Pennsylvanian",
     "search_terms": ["Cisco group", "Cisco Group"], "in_geolex": True},
    {"name": "canyon group", "rank": "group", "system": "Pennsylvanian",
     "search_terms": ["Canyon group", "Canyon Group"], "in_geolex": True},
    {"name": "palo pinto formation", "rank": "formation", "system": "Pennsylvanian",
     "search_terms": ["Palo Pinto limestone", "Palo Pinto formation"], "in_geolex": False},
    {"name": "strawn group", "rank": "group", "system": "Pennsylvanian",
     "search_terms": ["Strawn group", "Strawn Group"], "in_geolex": True},
    {"name": "caddo limestone", "rank": "formation", "system": "Pennsylvanian",
     "search_terms": ["Caddo limestone", "Caddo lime", "Caddo"], "in_geolex": False},
    {"name": "atoka group", "rank": "group", "system": "Pennsylvanian",
     "search_terms": ["Atoka"], "in_geolex": False},
    {"name": "bend conglomerate", "rank": "formation", "system": "Pennsylvanian",
     "search_terms": ["Bend conglomerate", "Bend Conglomerate"], "in_geolex": False},
    {"name": "smithwick shale", "rank": "formation", "system": "Pennsylvanian",
     "search_terms": ["Smithwick shale", "Smithwick"], "in_geolex": False},
    {"name": "marble falls limestone", "rank": "formation", "system": "Pennsylvanian",
     "search_terms": ["Marble Falls limestone", "Marble Falls"], "in_geolex": False},
    {"name": "barnett shale", "rank": "formation", "system": "Mississippian",
     "search_terms": ["Barnett shale", "Barnett Shale"], "in_geolex": False},
    {"name": "mississippian limestone", "rank": "informal", "system": "Mississippian",
     "search_terms": ["Mississippian limestone", "Chappel limestone", "Mississippian"],
     "in_geolex": False},
    {"name": "ellenburger group", "rank": "group", "system": "Ordovician",
     "search_terms": ["Ellenburger limestone", "Ellenburger group", "Ellenburger"],
     "in_geolex": False},
]

NAMES = {u["name"] for u in COLUMN}

SCHEMA = {
    "type": "object",
    "properties": {
        "supported": {
            "type": "boolean",
            "description": "True only if one of the supplied segments actually describes this unit's lithology or stratigraphic position. False if the unit is merely name-dropped.",
        },
        "lithology": {
            "type": "string",
            "description": "A VERBATIM span copied character-for-character out of one supplied segment, describing what the unit is made of or where it sits. 15-300 characters. Empty string if supported is false.",
        },
        "anchor": {
            "type": "string",
            "description": "The anchor of the segment the lithology span was copied from, exactly as labelled in the input. Empty string if supported is false.",
        },
        "bounds_note": {
            "type": "string",
            "description": "What the passage says about the unit's top or base contacts, in your own words. Empty if the passage says nothing about contacts.",
        },
        "reason": {
            "type": "string",
            "description": "If supported is false, one sentence naming what is missing.",
        },
    },
    "required": ["supported", "lithology", "anchor", "bounds_note", "reason"],
    "additionalProperties": False,
}

PROMPT = """You are reading segments of a petroleum-geology corpus to describe one \
stratigraphic unit of north-central Texas (the Bend Arch and the Eastern Shelf of \
the Midland Basin).

The unit is: **{name}** ({rank}, {system}).

Below are corpus segments that mention it, each labelled with its anchor.

{segments}

Return the single best passage describing what this unit IS: its lithology, its \
character, or its stratigraphic position. Two hard rules:

1. `lithology` must be copied VERBATIM from one segment above — character for \
character, no paraphrase, no ellipsis, no re-punctuation. It is checked against \
the segment text and the record is thrown away if it does not match.
2. `anchor` must be the anchor of the segment you copied from, exactly as labelled.

If none of these segments actually describes the unit — if it is only listed in a \
table of names, cited in a reference, or mentioned in passing — set supported to \
false and say so. A false is a useful answer here; an invented sentence is not.

The passage must be about **{name} itself**. A sentence that describes a \
neighbouring unit and merely names {name} in passing ("it is overlain by the \
{name}") is not a description of {name} — reject it and look for another, or \
return supported false."""

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "describes_the_unit": {
            "type": "boolean",
            "description": "True only if the quoted passage states something about THIS unit's own lithology, character, age, or position. False if it is really about a different unit, or is too generic to identify any unit.",
        },
        "reason": {"type": "string", "description": "One sentence."},
    },
    "required": ["describes_the_unit", "reason"],
    "additionalProperties": False,
}

VERIFY_PROMPT = """A lookup table for north-central Texas stratigraphy is about to \
record this quoted passage as its description of **{name}**:

"{quote}"

Your job is to refuse it if it does not belong. Answer false if the passage is \
really describing a different stratigraphic unit and only mentions {name} in \
passing (for example "it is overlain conformably by the {name}" describes the \
unit underneath, not {name}), or if it is so generic that it could describe \
almost any bed.

Answer true only if a geologist reading this passage alone would learn something \
about {name} itself. Default to false when uncertain."""


async def aboutness(client: AsyncAnthropic, unit: dict, quote: str,
                    sem: asyncio.Semaphore) -> tuple[bool, str]:
    """Second gate: the quote resolves, but is it *about* this unit?

    `test_provenance_quotes.py` records the defect this exists for — "a citation
    that resolves is not a citation that is about the claim". The verbatim check
    proves provenance and nothing else, and the first build of this table proved
    the point by recording "it is overlain conformably by the Marble Falls
    limestone" as the description of the Marble Falls.
    """
    async with sem:
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=1000,
            output_config={"effort": EFFORT,
                           "format": {"type": "json_schema", "schema": VERIFY_SCHEMA}},
            messages=[{"role": "user", "content": VERIFY_PROMPT.format(
                name=unit["name"], quote=quote)}],
        )
    got = json.loads(next(b.text for b in resp.content if b.type == "text"))
    return bool(got["describes_the_unit"]), (got.get("reason") or "").strip()


async def extract(client: AsyncAnthropic, unit: dict, sem: asyncio.Semaphore) -> dict:
    hits: list[tuple[str, int, str]] = []
    seen: set[str] = set()
    for term in unit["search_terms"]:
        for anchor, n, _ in search(term, limit=SEGMENTS_PER_UNIT):
            if anchor not in seen:
                seen.add(anchor)
                body = anchor_text(anchor) or ""
                hits.append((anchor, n, body[:MAX_SEGMENT_CHARS]))
        if len(hits) >= SEGMENTS_PER_UNIT:
            break
    hits = hits[:SEGMENTS_PER_UNIT]
    if not hits:
        return {**unit, "lithology": None, "anchor": None, "bounds_note": None,
                "evidence": "no corpus segment mentions this unit"}

    blocks = "\n\n".join(f"--- anchor: {a} ---\n{x}" for a, _, x in hits)
    prompt = PROMPT.format(name=unit["name"], rank=unit["rank"],
                           system=unit["system"], segments=blocks)

    # The failure this retries is a labelling slip, not a knowledge gap: with six
    # blocks in front of it the model occasionally pairs a real quote from one
    # block with the anchor of another. The check below catches it either way;
    # retrying just stops one slip from costing a unit its evidence.
    last = "no attempt made"
    for attempt in range(6):
        async with sem:
            resp = await client.messages.create(
                model=MODEL,
                max_tokens=4000,
                output_config={"effort": EFFORT,
                               "format": {"type": "json_schema", "schema": SCHEMA}},
                messages=[{"role": "user", "content": prompt}],
            )
        got = json.loads(next(b.text for b in resp.content if b.type == "text"))

        if not got["supported"]:
            last = got.get("reason") or "no supporting passage"
            break

        anchor, quote = got["anchor"].strip(), got["lithology"].strip()
        if anchor not in seen:
            last = f"model cited {anchor!r}, which was not supplied"
            continue
        if len(quote) < MIN_QUOTE_CHARS:
            last = f"quote was {len(quote)} chars, under the {MIN_QUOTE_CHARS}-char floor"
            continue
        if not quote_resolves(anchor, quote):
            last = f"quote did not appear verbatim in {anchor}"
            continue
        about, why = await aboutness(client, unit, quote, sem)
        if not about:
            last = f"quote resolves but is not about the unit: {why}"
            continue

        return {**unit, "lithology": quote, "anchor": anchor,
                "bounds_note": (got.get("bounds_note") or "").strip() or None,
                "evidence": "verbatim quote verified against the cited segment"}

    return {**unit, "lithology": None, "anchor": None, "bounds_note": None,
            "evidence": last}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="one unit name")
    ap.add_argument("--estimate", action="store_true")
    args = ap.parse_args()

    units = [u for u in COLUMN if not args.only or u["name"] == args.only]
    if args.estimate:
        print(f"{len(units)} units x 1 call on {MODEL} (effort={EFFORT})")
        return

    client = AsyncAnthropic(api_key=load_api_key())
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    records = await asyncio.gather(*(extract(client, u, sem) for u in units))

    for r in records:
        mark = "ok " if r["lithology"] else "-- "
        print(f"{mark}{r['name']:<26} {r['anchor'] or r['evidence']}")

    fresh = [{k: v for k, v in r.items() if k != "search_terms"} for r in records]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    by_name = {}
    if args.only and OUT.exists():
        by_name = {u["name"]: u for u in json.loads(OUT.read_text())["units"]}
    by_name.update({r["name"]: r for r in fresh})

    # Position is assigned from COLUMN after the merge, never from the slice that
    # happened to be rebuilt — a `--only` run rebuilding one unit must not renumber
    # it to 0 just because it was alone in its batch.
    ordered = [by_name[u["name"]] for u in COLUMN if u["name"] in by_name]
    for i, r in enumerate(ordered):
        r["position"] = i          # 0 = youngest
        r["above"] = ordered[i - 1]["name"] if i else None
        r["below"] = ordered[i + 1]["name"] if i + 1 < len(ordered) else None
    OUT.write_text(json.dumps({
        "source": "extracted from the corpus by scripts/build_strat_column.py; "
                  "ordering and unit list are declared in that script, lithology "
                  "quotes are verbatim and verified against their anchors",
        "units": ordered,
    }, indent=2) + "\n")
    print(f"\nwrote {OUT} ({sum(1 for r in ordered if r['lithology'])}/{len(ordered)} with evidence)")


if __name__ == "__main__":
    asyncio.run(main())
