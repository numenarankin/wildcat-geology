#!/usr/bin/env python3
"""Extract regional priors for the Bend Arch counties from the corpus.

`basin_prior_lookup` (#62) has covered exactly one area since it was written —
the Boonsville project area — and refused everywhere else. That refusal was
honest, because a prior invented for a neighbouring county is worse than no
prior. This fills the gap the same way the rest of this corpus is built: by
quoting documents that are already in it, verbatim, with the anchor attached.

The four fields are the ones the tool already defines, and they are exactly the
qualitative screening content an operator needs:

  trap_style          what holds hydrocarbons here
  contact_behaviour   how the water behaves - coning, drive, contacts
  tool_suites         what was logged, and what those logs can and cannot answer
  pitfalls            the ways a screen goes wrong in this area

Same two gates as `build_strat_column.py`: the quote must appear verbatim in the
segment it cites, and a second call has to agree the quote is actually about the
location asked for. A field with no supporting passage is written as null. There
are eight locations and four fields, so most of the grid is expected to be empty
- that is what the corpus supports, and the tool reports it as such.

Usage:
  python3 scripts/build_basin_priors.py --estimate
  python3 scripts/build_basin_priors.py --only "archer county"
  python3 scripts/build_basin_priors.py
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
OUT = ROOT / "tables" / "basin-priors-bend-arch.json"

MODEL = "claude-sonnet-5"
EFFORT = "medium"
MAX_CONCURRENCY = 6
SEGMENTS_PER_LOCATION = 10
MAX_SEGMENT_CHARS = 9000
MIN_QUOTE_CHARS = 60

FIELDS = ("trap_style", "contact_behaviour", "tool_suites", "pitfalls")

LOCATIONS: list[dict] = [
    {"key": "bend arch", "label": "the Bend Arch",
     "aliases": ["bend arch", "bend arch, texas", "bend arch province"],
     "terms": ["Bend Arch", "Bend arch"]},
    {"key": "eastern shelf", "label": "the Eastern Shelf of the Midland Basin",
     "aliases": ["eastern shelf", "eastern shelf of the midland basin"],
     "terms": ["Eastern Shelf", "eastern shelf"]},
    {"key": "archer county", "label": "Archer County, Texas",
     "aliases": ["archer county", "archer county, texas", "archer"],
     "terms": ["Archer County", "Archer Co", "Archer"]},
    {"key": "young county", "label": "Young County, Texas",
     "aliases": ["young county", "young county, texas", "young"],
     "terms": ["Young County", "Young Co"]},
    {"key": "wichita county", "label": "Wichita County, Texas",
     "aliases": ["wichita county", "wichita county, texas"],
     "terms": ["Wichita County", "Wichita Co"]},
    {"key": "stephens county", "label": "Stephens County, Texas",
     "aliases": ["stephens county", "stephens county, texas", "breckenridge"],
     "terms": ["Stephens County", "Breckenridge field", "Breckenridge oil field"]},
    {"key": "palo pinto county", "label": "Palo Pinto County, Texas",
     "aliases": ["palo pinto county", "palo pinto county, texas"],
     "terms": ["Palo Pinto County", "Palo Pinto Co"]},
    {"key": "jack county", "label": "Jack County, Texas",
     "aliases": ["jack county, texas (bend arch)"],
     "terms": ["Jack County", "Jack Co"]},
]

FIELD_BRIEF = {
    "trap_style": "what traps hydrocarbons here - structure, stratigraphy, "
                  "pinch-outs, buildups, faulting, unconformities",
    "contact_behaviour": "how water and hydrocarbons sit and move - oil/water "
                         "contacts, water drive, coning, encroachment, water cut",
    "tool_suites": "what logging or measurement was run in this area and what "
                   "those measurements can and cannot resolve",
    "pitfalls": "the ways an interpretation goes wrong here - correlation "
                "traps, facies changes, thin beds, misleading log responses, "
                "depleted or watered-out intervals",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "priors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "enum": list(FIELDS)},
                    "supported": {"type": "boolean",
                                  "description": "False if no supplied segment says anything about this field FOR THIS LOCATION."},
                    "statement": {"type": "string",
                                  "description": "A VERBATIM span copied character-for-character from one supplied segment, 60-600 characters. Empty if unsupported."},
                    "anchor": {"type": "string",
                               "description": "The anchor of the segment the span came from, exactly as labelled. Empty if unsupported."},
                    "reason": {"type": "string", "description": "If unsupported, one sentence naming what is missing."},
                },
                "required": ["field", "supported", "statement", "anchor", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["priors"],
    "additionalProperties": False,
}

PROMPT = """You are building a regional screening prior for **{label}** from a \
petroleum-geology corpus.

Below are corpus segments that mention this location, each labelled with its anchor.

{segments}

Return one entry for each of these four fields:

{brief}

Two hard rules for every entry you mark supported:

1. `statement` must be copied VERBATIM from one segment above — character for \
character. It is checked against the segment text and thrown away if it does not match.
2. `anchor` must be the anchor of the segment you copied from, exactly as labelled.

Mark a field unsupported whenever the segments do not actually speak to it for \
**this location**. Most of this grid is expected to come back unsupported, and \
that is the correct answer — a prior invented for a county is worse than no prior, \
because a screen will act on it."""

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "about_this_location": {"type": "boolean",
                                "description": "True only if the passage's claim genuinely applies to the named location, and to the named topic."},
        "reason": {"type": "string"},
    },
    "required": ["about_this_location", "reason"],
    "additionalProperties": False,
}

VERIFY_PROMPT = """A regional screening table is about to record this passage as \
its **{field}** prior for **{label}**:

"{quote}"

{brief}

Refuse it if the passage is really about a different area (another basin, another \
county, a general statement about Texas or about geology anywhere), or if it does \
not actually speak to the topic named above. Answer true only if an operator \
screening acreage in {label} would be correctly informed by it. Default to false \
when uncertain."""


async def verify(client: AsyncAnthropic, location: dict, field: str, quote: str,
                 sem: asyncio.Semaphore) -> tuple[bool, str]:
    async with sem:
        resp = await client.messages.create(
            model=MODEL, max_tokens=1000,
            output_config={"effort": "low",
                           "format": {"type": "json_schema", "schema": VERIFY_SCHEMA}},
            messages=[{"role": "user", "content": VERIFY_PROMPT.format(
                field=field, label=location["label"], quote=quote,
                brief=FIELD_BRIEF[field])}],
        )
    got = json.loads(next(b.text for b in resp.content if b.type == "text"))
    return bool(got["about_this_location"]), (got.get("reason") or "").strip()


async def extract(client: AsyncAnthropic, location: dict,
                  sem: asyncio.Semaphore) -> dict:
    hits: list[tuple[str, str]] = []
    seen: set[str] = set()
    for term in location["terms"]:
        for anchor, _, _ in search(term, limit=SEGMENTS_PER_LOCATION):
            if anchor not in seen:
                seen.add(anchor)
                hits.append((anchor, (anchor_text(anchor) or "")[:MAX_SEGMENT_CHARS]))
        if len(hits) >= SEGMENTS_PER_LOCATION:
            break
    hits = hits[:SEGMENTS_PER_LOCATION]

    record = {"key": location["key"], "label": location["label"],
              "aliases": location["aliases"], "priors": {}}
    if not hits:
        for field in FIELDS:
            record["priors"][field] = {"statement": None, "anchor": None,
                                       "evidence": "no corpus segment mentions this location"}
        return record

    blocks = "\n\n".join(f"--- anchor: {a} ---\n{t}" for a, t in hits)
    brief = "\n".join(f"- **{f}**: {FIELD_BRIEF[f]}" for f in FIELDS)
    async with sem:
        resp = await client.messages.create(
            model=MODEL, max_tokens=8000,
            output_config={"effort": EFFORT,
                           "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": PROMPT.format(
                label=location["label"], segments=blocks, brief=brief)}],
        )
    got = json.loads(next(b.text for b in resp.content if b.type == "text"))
    by_field = {p["field"]: p for p in got["priors"]}

    for field in FIELDS:
        p = by_field.get(field)
        if not p or not p["supported"]:
            record["priors"][field] = {
                "statement": None, "anchor": None,
                "evidence": (p or {}).get("reason") or "no supporting passage"}
            continue
        anchor, quote = p["anchor"].strip(), p["statement"].strip()
        if anchor not in seen:
            record["priors"][field] = {"statement": None, "anchor": None,
                                       "evidence": f"cited {anchor!r}, which was not supplied"}
            continue
        if len(quote) < MIN_QUOTE_CHARS:
            record["priors"][field] = {"statement": None, "anchor": None,
                                       "evidence": f"quote was {len(quote)} chars, under the floor"}
            continue
        if not quote_resolves(anchor, quote):
            record["priors"][field] = {"statement": None, "anchor": None,
                                       "evidence": f"quote not verbatim in {anchor}"}
            continue
        about, why = await verify(client, location, field, quote, sem)
        if not about:
            record["priors"][field] = {"statement": None, "anchor": None,
                                       "evidence": f"rejected as off-location/off-topic: {why}"}
            continue
        record["priors"][field] = {"statement": quote, "anchor": anchor,
                                   "evidence": "verbatim and verified as about this location"}
    return record


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--estimate", action="store_true")
    args = ap.parse_args()

    targets = [l for l in LOCATIONS if not args.only or l["key"] == args.only]
    if args.estimate:
        print(f"{len(targets)} locations x (1 extract + up to 4 verify) on {MODEL}")
        return

    client = AsyncAnthropic(api_key=load_api_key())
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    records = await asyncio.gather(*(extract(client, l, sem) for l in targets))

    for r in records:
        got = [f for f in FIELDS if r["priors"][f]["statement"]]
        print(f"{r['key']:<20} {len(got)}/4  {', '.join(got) or '-'}")

    by_key = {}
    if args.only and OUT.exists():
        by_key = {r["key"]: r for r in json.loads(OUT.read_text())["locations"]}
    by_key.update({r["key"]: r for r in records})
    ordered = [by_key[l["key"]] for l in LOCATIONS if l["key"] in by_key]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "scripts/build_basin_priors.py; every statement is verbatim from "
                  "the anchor it cites and was checked as being about its location",
        "fields": list(FIELDS),
        "locations": ordered,
    }, indent=2) + "\n")
    filled = sum(1 for r in ordered for f in FIELDS if r["priors"][f]["statement"])
    print(f"\nwrote {OUT} ({filled}/{len(ordered) * len(FIELDS)} cells filled)")


if __name__ == "__main__":
    asyncio.run(main())
