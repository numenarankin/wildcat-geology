#!/usr/bin/env python3
"""Build the field/reservoir parameter table for the Bend Arch counties.

The plan for this table named the BEG *Atlas of Major Texas Oil Reservoirs* as
its source. The Atlas is a 1983 snapshot of the state's biggest reservoirs; the
RRC mirror is the whole public record, current, and it already sits behind the
scout page. For the question this table exists to answer — *what is this
reservoir, how big did it get, and is anyone still producing it* — the record
beats the snapshot, and every number in it can be recomputed rather than trusted.

An RRC field name carries its reservoir in parentheses: `A & D (MARBLE FALLS
CONGL. 4900)` is the A & D field producing the Marble Falls. That parenthetical
is parsed out here and left as text; `reservoir_parameter_lookup` hands it to
`formation_alias_resolve`, so the reservoir a field produces resolves to the same
canonical column as a formation top on a completion report. The two tables meet.

What is *not* here, and would have come from the Atlas: porosity, net pay,
saturation, drive mechanism, recovery factor. Those are reservoir-engineering
measurements and the public record does not carry them. The lookup says so rather
than estimating them.

Usage:
  RRC_DATABASE_URL=postgres://... python3 scripts/pull_rrc_reservoirs.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import psycopg

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "api" / "_geology"))
from pull_rrc_formations import COUNTIES, database_url  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent / "geology-corpus"
OUT = ROOT / "tables" / "reservoir-parameters.json"

# `FIELD (RESERVOIR)` is the RRC naming convention. The trailing number in
# "(MARBLE FALLS CONGL. 4900)" is the reservoir's approximate depth, which the
# RRC uses to separate two reservoirs of the same name in one field.
RESERVOIR = re.compile(r"^(?P<field>.*?)\s*\((?P<reservoir>[^)]*)\)\s*$")
DEPTH_IN_NAME = re.compile(r"\b(\d{3,5})\b\s*$")

FIELDS_QUERY = """
select
  f.field_no,
  f.field_name,
  coalesce(nullif(f.o_county_no, ''), nullif(f.g_county_no, '')) as county_code,
  f.field_class,
  f.o_discovery_dt,
  f.g_discovery_dt,
  f.wildcat_flag
from rrc.field f
where f.o_county_no = any(%(codes)s) or f.g_county_no = any(%(codes)s)
"""

PRODUCTION_QUERY = """
select
  lp.field_no,
  sum(lp.oil_prod_vol)::numeric              as cum_oil_bbl,
  sum(lp.gas_prod_vol)::numeric              as cum_gas_mcf,
  sum(lp.csgd_prod_vol)::numeric             as cum_casinghead_mcf,
  count(distinct lp.lease_no)                as leases,
  min(lp.cycle)                              as first_cycle,
  max(lp.cycle)                              as last_cycle,
  count(distinct lp.cycle)                   as reported_cycles,
  count(distinct lp.operator_no)             as operators
from rrc.lease_production lp
where lp.field_no = any(%(fields)s)
group by lp.field_no
"""

# Depth and formation come from the completion reports filed in the field, not
# from the field name — the name's trailing number is the RRC's label, the tops
# are what the operators measured.
TOPS_QUERY = """
with tops as (
  select distinct c.field_no, c.tracking_no,
         upper(btrim(cf.formation)) as formation,
         case when btrim(cf.depth) ~ '^[0-9]+(\.[0-9]+)?$'
              then btrim(cf.depth)::numeric end as depth_ft
  from rrc.completion c
  join rrc.completion_formation cf on cf.tracking_no = c.tracking_no
  where c.county = any(%(codes)s) and c.field_no = any(%(fields)s)
)
select field_no, formation, count(*) as n,
       percentile_disc(0.5) within group (order by depth_ft)
         filter (where depth_ft between 100 and 12000) as median_depth_ft
from tops
where formation <> ''
group by field_no, formation
"""


def year_of(value) -> int | None:
    """The year in an RRC `DD-MON-YY` discovery date.

    Two-digit years are 1900s, without exception. The column's whole range is
    `01-APR-01` to `31-OCT-98`, so there is no 2000s date to disambiguate from —
    and the usual "pivot at 25" rule gets it catastrophically wrong here:
    Wichita County Regular is `31-DEC-10`, which is 1910, the year before the
    Electra discovery. Reading that as 2010 turns the oldest producing county on
    the Bend Arch into a new play.
    """
    if not value:
        return None
    text = str(value).strip()
    m = re.search(r"(\d{2,4})\s*$", text)
    if not m:
        return None
    digits = m.group(1)
    year = int(digits)
    if len(digits) <= 2:
        year += 1900
    return year if 1860 <= year <= 2100 else None


def main() -> None:
    codes = list(COUNTIES)
    with psycopg.connect(database_url(), connect_timeout=90) as conn, conn.cursor() as cur:
        cur.execute(FIELDS_QUERY, {"codes": codes})
        fields = cur.fetchall()
        print(f"{len(fields)} fields in {', '.join(COUNTIES.values())}")

        numbers = [f[0] for f in fields]
        cur.execute(PRODUCTION_QUERY, {"fields": numbers})
        production = {r[0]: r for r in cur.fetchall()}
        print(f"production for {len(production)} of them")

        cur.execute(TOPS_QUERY, {"codes": codes, "fields": numbers})
        tops: dict[str, list] = {}
        for field_no, formation, n, depth in cur.fetchall():
            tops.setdefault(field_no, []).append((formation, n, depth))
        print(f"completion tops for {len(tops)} of them")

    records = []
    for field_no, field_name, county_code, field_class, o_dt, g_dt, wildcat in fields:
        m = RESERVOIR.match(field_name or "")
        field_part = (m.group("field") if m else field_name or "").strip()
        reservoir = (m.group("reservoir") if m else "").strip()
        depth_label = DEPTH_IN_NAME.search(reservoir)

        p = production.get(field_no)
        field_tops = sorted(tops.get(field_no, []), key=lambda t: -t[1])

        records.append({
            "field_no": field_no,
            "field_name": (field_name or "").strip(),
            "field": field_part,
            "reservoir": reservoir,
            "reservoir_depth_label_ft": int(depth_label.group(1)) if depth_label else None,
            "county": COUNTIES.get(county_code or "", None),
            "field_class": field_class,
            "wildcat": (wildcat or "").strip().upper() == "Y",
            "discovery_year_oil": year_of(o_dt),
            "discovery_year_gas": year_of(g_dt),
            "cum_oil_bbl": float(p[1]) if p and p[1] is not None else None,
            "cum_gas_mcf": float(p[2]) if p and p[2] is not None else None,
            "cum_casinghead_mcf": float(p[3]) if p and p[3] is not None else None,
            "leases": int(p[4]) if p else 0,
            "first_production": str(p[5]) if p and p[5] else None,
            "last_production": str(p[6]) if p and p[6] else None,
            "reported_cycles": int(p[7]) if p else 0,
            "operators": int(p[8]) if p else 0,
            "completion_formations": [
                {"formation": f, "completions": n,
                 "median_depth_ft": float(d) if d is not None else None}
                for f, n, d in field_tops[:6]
            ],
        })

    records.sort(key=lambda r: -(r["cum_oil_bbl"] or 0))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "rrc.field, rrc.lease_production and rrc.completion_formation, "
                  "Texas RRC public record via the Tiger Cloud mirror",
        "counties": sorted(COUNTIES.values()),
        "not_included": ("porosity, net pay, water saturation, drive mechanism and "
                         "recovery factor are reservoir-engineering measurements the "
                         "public record does not carry; this table does not estimate them"),
        "fields": len(records),
        "reservoirs": records,
    }, indent=2) + "\n")

    with_oil = [r for r in records if r["cum_oil_bbl"]]
    print(f"wrote {OUT}: {len(records)} fields, {len(with_oil)} with reported oil")
    for r in records[:10]:
        print(f"  {(r['cum_oil_bbl'] or 0):>12,.0f} bbl  {r['county']:<11} {r['field_name']}")


if __name__ == "__main__":
    sys.exit(main())
