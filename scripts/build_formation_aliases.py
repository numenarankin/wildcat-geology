#!/usr/bin/env python3
"""Cluster operator-typed RRC formation strings onto the canonical column.

The input is `tables/rrc-formation-strings.json` — every distinct string an
operator wrote in the formation-top section of a completion report for the six
Bend Arch counties, with its frequency and depth percentiles. The output is the
lookup `formation_alias_resolve` reads.

**The model only normalises names.** It is handed the raw string and the closed
list of canonical units, and it answers with one of those names or with one of
two refusals. It is never asked where a unit sits, how deep it is, or what it is
made of — those come from the column table and from the depth percentiles, both
of which are evidence rather than recall. Any answer naming a unit outside the
closed list is dropped by `verify()`, not argued with.

**Informal driller's names stay informal.** Roughly a third of these strings —
THOMAS SAND, VOGSTBERGER, BRYSON, KMA — are local lease names for a sand nobody
ever formally described. Forcing them onto a formal unit would be the worst
outcome available, so they are recorded as informal, and the interval they sit
in is computed from their own depth percentiles against the formal units' depth
windows in the same county. That bracket is arithmetic, not opinion.

Usage:
  python3 scripts/build_formation_aliases.py --estimate
  python3 scripts/build_formation_aliases.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import re
import sys

from anthropic import AsyncAnthropic

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "api" / "_geology"))
from build_toc import load_api_key  # noqa: E402
from tools.lookups import GEOLEX_UNITS  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent / "geology-corpus"
STRINGS = ROOT / "tables" / "rrc-formation-strings.json"
COLUMN_FILE = ROOT / "tables" / "strat-column-bend-arch.json"
OUT = ROOT / "tables" / "formation-aliases.json"

MODEL = "claude-sonnet-5"
EFFORT = "low"
BATCH = 30
MAX_CONCURRENCY = 6

# Suffixes the RRC record appends for regulatory reasons, not stratigraphic ones.
# " - DISPOSAL" says what the well does, not what the rock is; the H2S notes are
# a safety warning typed into the formation field. Stripping them here means the
# model never has to decide whether CADDO and CADDO - DISPOSAL are the same rock.
NOISE_SUFFIX = re.compile(
    r"\s*[-–]\s*(DISPOSAL|POSSIBLE H2S.*|INJECTION|SWD|SALT ?WATER DISPOSAL)\s*$", re.I)


def canonical_targets() -> dict[str, dict]:
    column = json.loads(COLUMN_FILE.read_text())["units"]
    targets = {u["name"]: {"name": u["name"], "rank": u["rank"], "system": u["system"],
                           "source": "strat-column-bend-arch"} for u in column}
    for name, rec in GEOLEX_UNITS.items():
        targets.setdefault(name, {"name": name, "rank": rec.get("rank") or "unit",
                                  "system": rec.get("system") or "Pennsylvanian",
                                  "source": "geolex_lookup"})
    return targets


SCHEMA = {
    "type": "object",
    "properties": {
        "assignments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "raw": {"type": "string", "description": "The input string, echoed exactly."},
                    "verdict": {
                        "type": "string",
                        "enum": ["formal", "informal", "not_a_formation"],
                        "description": "formal = it names a unit on the canonical list. informal = it is a real rock unit but a local driller's or lease name with no entry on the list. not_a_formation = it is not a rock unit at all (a regulatory placeholder, a well status, a field name used as a formation).",
                    },
                    "canonical": {
                        "type": "string",
                        "description": "When verdict is formal: the canonical name, copied EXACTLY from the supplied list. Empty string otherwise.",
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "low"],
                        "description": "low when the string is a plausible but uncertain spelling of the canonical unit.",
                    },
                    "note": {"type": "string", "description": "Short reason. Name the spelling variance if that is what this is."},
                },
                "required": ["raw", "verdict", "canonical", "confidence", "note"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["assignments"],
    "additionalProperties": False,
}

PROMPT = """You are normalising formation names typed by oil-and-gas operators onto \
a canonical stratigraphic column for the Bend Arch and Eastern Shelf of \
north-central Texas (Archer, Jack, Palo Pinto, Stephens, Wichita and Young Counties).

The canonical list — the ONLY names you may return in `canonical`:

{targets}

Here are the operator-typed strings to classify. Each shows how many completion \
filings used it and its median depth per county, which may help you tell a \
misspelling from a genuinely different unit.

{items}

For each string return one of:

- **formal** — it names a unit on the list above, including obvious misspellings \
  (MISSISIPIAN for the Mississippian, CADOO for the Caddo) and rank variants \
  (CADDO LIME, CADDO SAND and CADDO all name the Caddo). Copy `canonical` \
  EXACTLY from the list; anything not on the list is discarded.
- **informal** — a real producing interval, but a local driller's or lease name \
  that has no entry on the canonical list. North-central Texas is full of these \
  (operator sand names, names taken from a lease or a field). This is the right \
  answer for a great many of these strings. Do NOT stretch one onto a formal \
  unit because it is nearby in the section.
- **not_a_formation** — not a rock unit: a regulatory placeholder, a well \
  status, a permit category.

Precision matters more than coverage. An unmapped string costs the user one \
lookup that refuses; a wrongly mapped one silently corrupts every screen that \
uses it."""


async def classify(client: AsyncAnthropic, batch: list[dict], targets: dict,
                   sem: asyncio.Semaphore) -> list[dict]:
    listing = "\n".join(
        f"- {t['name']}  ({t['rank']}, {t['system']})" for t in targets.values())
    items = []
    for r in batch:
        depths = ", ".join(
            f"{c} {v['depth_p50_ft']:.0f}ft" for c, v in sorted(r["counties"].items())
            if v["depth_p50_ft"] is not None) or "no depth samples"
        items.append(f'- "{r["clean"]}"  ({r["filings"]} filings; {depths})')

    async with sem:
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": EFFORT,
                           "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": PROMPT.format(
                targets=listing, items="\n".join(items))}],
        )
    got = json.loads(next(b.text for b in resp.content if b.type == "text"))
    return got["assignments"]


def verify(assignments: list[dict], batch: list[dict], targets: dict) -> list[dict]:
    """Drop anything that names a unit off the list, or a string we did not send."""
    by_clean = {r["clean"]: r for r in batch}
    out = []
    for a in assignments:
        raw = a.get("raw", "").strip()
        if raw not in by_clean:
            continue
        verdict = a["verdict"]
        canonical = (a.get("canonical") or "").strip().lower()
        if verdict == "formal":
            if canonical not in targets:
                # The one invention this pipeline is exposed to, and the reason
                # the closed list exists: a target that is not on it is dropped
                # rather than added.
                out.append({**by_clean[raw], "verdict": "unmapped", "canonical": None,
                            "confidence": "low",
                            "note": f"model returned off-list target {canonical!r}"})
                continue
            out.append({**by_clean[raw], "verdict": "formal", "canonical": canonical,
                        "confidence": a.get("confidence", "low"),
                        "note": a.get("note", "")})
        else:
            out.append({**by_clean[raw], "verdict": verdict, "canonical": None,
                        "confidence": a.get("confidence", "low"),
                        "note": a.get("note", "")})
    return out


def depth_windows(records: list[dict]) -> dict[str, dict]:
    """Per canonical unit per county: the depth band its member strings report.

    Aggregated from the strings that mapped to the unit, weighted by how many
    depth samples each contributed. No publication states these; 60,000 filings do.
    """
    acc: dict[str, dict[str, dict]] = {}
    for r in records:
        if r["verdict"] != "formal":
            continue
        unit = acc.setdefault(r["canonical"], {})
        for county, v in r["counties"].items():
            if not v["depth_samples"]:
                continue
            c = unit.setdefault(county, {"samples": 0, "p10": [], "p50": [], "p90": []})
            c["samples"] += v["depth_samples"]
            c["p10"].append((v["depth_p10_ft"], v["depth_samples"]))
            c["p50"].append((v["depth_p50_ft"], v["depth_samples"]))
            c["p90"].append((v["depth_p90_ft"], v["depth_samples"]))

    def weighted(pairs: list[tuple[float, int]]) -> float:
        total = sum(w for _, w in pairs)
        return round(sum(v * w for v, w in pairs) / total, 1) if total else None

    return {unit: {county: {"depth_samples": c["samples"],
                            "depth_p10_ft": weighted(c["p10"]),
                            "depth_p50_ft": weighted(c["p50"]),
                            "depth_p90_ft": weighted(c["p90"])}
                   for county, c in counties.items()}
            for unit, counties in acc.items()}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--estimate", action="store_true")
    args = ap.parse_args()

    data = json.loads(STRINGS.read_text())
    targets = canonical_targets()

    rows = []
    for r in data["strings"]:
        clean = NOISE_SUFFIX.sub("", r["raw"]).strip()
        rows.append({**r, "clean": clean})

    # Distinct cleaned strings, keeping every raw spelling that folds into it.
    merged: dict[str, dict] = {}
    for r in rows:
        m = merged.setdefault(r["clean"], {"clean": r["clean"], "raw_forms": [],
                                           "filings": 0, "counties": {}})
        m["raw_forms"].append(r["raw"])
        m["filings"] += r["filings"]
        for county, v in r["counties"].items():
            c = m["counties"].setdefault(county, {"filings": 0, "depth_samples": 0,
                                                  "depth_p10_ft": None,
                                                  "depth_p50_ft": None,
                                                  "depth_p90_ft": None})
            c["filings"] += v["filings"]
            if v["depth_samples"] and v["depth_samples"] > c["depth_samples"]:
                c.update({k: v[k] for k in
                          ("depth_samples", "depth_p10_ft", "depth_p50_ft", "depth_p90_ft")})

    batch_list = sorted(merged.values(), key=lambda r: -r["filings"])
    batches = [batch_list[i:i + BATCH] for i in range(0, len(batch_list), BATCH)]

    if args.estimate:
        print(f"{len(batch_list)} cleaned strings ({data['distinct_strings']} raw) "
              f"in {len(batches)} calls on {MODEL}")
        return

    client = AsyncAnthropic(api_key=load_api_key())
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    results = await asyncio.gather(
        *(classify(client, b, targets, sem) for b in batches))
    records = [r for assignments, b in zip(results, batches)
               for r in verify(assignments, b, targets)]

    counts: dict[str, int] = {}
    for r in records:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    covered = sum(r["filings"] for r in records if r["verdict"] == "formal")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "scripts/build_formation_aliases.py over "
                  "tables/rrc-formation-strings.json; canonical targets are the "
                  "closed union of strat-column-bend-arch and GEOLEX_UNITS",
        "counties": data["counties"],
        "verdict_counts": counts,
        "filings_mapped_to_formal_units": covered,
        "total_filings": data["total_filings"],
        "depth_windows": depth_windows(records),
        "aliases": sorted(records, key=lambda r: -r["filings"]),
    }, indent=2) + "\n")

    print(f"{counts} over {len(records)} strings")
    print(f"formal units carry {covered}/{data['total_filings']} filings "
          f"({covered / data['total_filings'] * 100:.1f}%)")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
