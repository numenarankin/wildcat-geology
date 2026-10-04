#!/usr/bin/env python3
"""Pull the operator-typed formation strings, and their depths, from the RRC mirror.

`rrc.completion_formation` is the formation-top section of the W-2/G-1 completion
report: ~2.4M rows statewide, one per formation an operator wrote down on a
filing, with the depth they encountered it. The `formation` column is free text.
It is what a pumper or a landman typed, so the same rock arrives as CADDO, CADDO
LIME, CADOO and CADDO - DISPOSAL.

This script is the front half of `formation_alias_resolve`: it collects the
distinct strings for the target counties with their frequency and their depth
distribution, so the clustering step has evidence rather than vocabulary. Depth
percentiles come from here and nowhere else — no publication states a per-county
depth window for the Bend Arch, but 60,000 filings do.

Depths are filtered to a plausible band before percentiles are taken. The raw
column carries typos and sentinel values (0, 1, 99999) that would otherwise drag
a p10 to zero.

Usage:
  RRC_DATABASE_URL=postgres://... python3 scripts/pull_rrc_formations.py
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import psycopg

ROOT = pathlib.Path(__file__).resolve().parent.parent / "geology-corpus"
OUT = ROOT / "tables" / "rrc-formation-strings.json"

# FIPS county codes, which is what `rrc.completion.county` holds.
COUNTIES = {
    "009": "ARCHER", "237": "JACK", "363": "PALO PINTO",
    "429": "STEPHENS", "485": "WICHITA", "503": "YOUNG",
}

# A formation top shallower than this is a surface-casing note or a typo; deeper
# than this is below basement everywhere in these six counties.
MIN_DEPTH_FT = 100
MAX_DEPTH_FT = 12000

QUERY = """
with tops as (
  -- DISTINCT because a completion packet repeats its formation section across
  -- parent and child rows; counting those twice would double every frequency
  -- and weight the percentiles toward whichever filings happen to be duplicated.
  select distinct
    cf.tracking_no,
    upper(btrim(cf.formation))                as raw,
    c.county                                  as county_code,
    -- The column is text and holds '4595.0'. Stripping every non-digit turns
    -- that into 45950, which then fails the depth band and silently zeroes the
    -- sample count, so match the number instead of scrubbing it.
    case when btrim(cf.depth) ~ '^[0-9]+(\.[0-9]+)?$'
         then btrim(cf.depth)::numeric end    as depth_ft
  from rrc.completion_formation cf
  join rrc.completion c on c.tracking_no = cf.tracking_no
  where c.county = any(%(codes)s)
    and cf.formation is not null
    and btrim(cf.formation) <> ''
)
select
  raw,
  county_code,
  count(*)                                                    as filings,
  count(depth_ft) filter (where depth_ft between %(lo)s and %(hi)s) as depth_n,
  percentile_disc(0.10) within group (order by depth_ft)
    filter (where depth_ft between %(lo)s and %(hi)s)         as p10,
  percentile_disc(0.50) within group (order by depth_ft)
    filter (where depth_ft between %(lo)s and %(hi)s)         as p50,
  percentile_disc(0.90) within group (order by depth_ft)
    filter (where depth_ft between %(lo)s and %(hi)s)         as p90
from tops
group by raw, county_code
order by filings desc
"""


def database_url() -> str:
    url = os.environ.get("RRC_DATABASE_URL")
    if url:
        return url
    raise SystemExit("set RRC_DATABASE_URL")


def main() -> None:
    with psycopg.connect(database_url(), connect_timeout=60) as conn, conn.cursor() as cur:
        cur.execute(QUERY, {"codes": list(COUNTIES), "lo": MIN_DEPTH_FT, "hi": MAX_DEPTH_FT})
        rows = cur.fetchall()

    strings: dict[str, dict] = {}
    for raw, code, filings, depth_n, p10, p50, p90 in rows:
        rec = strings.setdefault(raw, {"raw": raw, "filings": 0, "counties": {}})
        rec["filings"] += filings
        rec["counties"][COUNTIES[code]] = {
            "filings": filings,
            "depth_samples": depth_n,
            "depth_p10_ft": float(p10) if p10 is not None else None,
            "depth_p50_ft": float(p50) if p50 is not None else None,
            "depth_p90_ft": float(p90) if p90 is not None else None,
        }

    ordered = sorted(strings.values(), key=lambda r: -r["filings"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "rrc.completion_formation joined to rrc.completion, "
                  "Tiger Cloud mirror of the Texas RRC public record",
        "counties": sorted(COUNTIES.values()),
        "depth_filter_ft": [MIN_DEPTH_FT, MAX_DEPTH_FT],
        "distinct_strings": len(ordered),
        "total_filings": sum(r["filings"] for r in ordered),
        "strings": ordered,
    }, indent=2) + "\n")

    print(f"{len(ordered)} distinct strings, "
          f"{sum(r['filings'] for r in ordered)} filings -> {OUT}")
    for r in ordered[:15]:
        print(f"  {r['filings']:6d}  {r['raw']}")


if __name__ == "__main__":
    sys.exit(main())
