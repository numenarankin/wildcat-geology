"""Tool #93 `produced_water_query` — regional formation-water chemistry lookup.

Group J, section 13. Spec: `specs/93-produced_water_query.md`.

This tool is a lookup, not an equation, and **the database it looks things up in
is not in this repository**. The corpus anchor
`11-rw-and-crossplots/usgs-produced-waters-geochemical-database-v3` is the USGS
data-release *landing page* — a DOI, a citation block and a staff directory. It
carries no field names, no units, no QC flags and no method. `toc/TOC.md` says so
in as many words: "the actual data values - no tables, analyses, or per-formation
salinity numbers are reproduced here … treat it as a gateway to the USGS data
release rather than a source of values or methods."

Three consequences are designed in rather than commented on:

* **There is no default `column_map` and no assumed unit.** The corpus does not
  state what the release calls its columns or whether TDS is mg/L or ppm, so the
  caller declares both. A guessed header that silently matched the wrong column
  would produce a number with the wrong meaning, which is worse than refusing.
* **The version pin is a checked value.** `PINNED_VERSION`/`PINNED_RELEASE_DATE`
  are compared against the handle before the file is opened, so a v2.3 file
  cannot be summarised as though it were v3.0.
* **Every returned Quantity is flagged as a regional analogue.** Its output feeds
  `nacl_equivalent` (#91) and `rw_from_tds` (#92) and thence `archie_sw`, which
  refuses without Rw provenance. A county median must never reach that chain
  looking like a sample from the operator's own well.

Median rather than mean: the compilation "mixes decades of analyses of uneven
reliability" (`toc/TOC.md`), i.e. it has outliers and no documented QC. That
choice is ours and is recorded in `assumptions["statistic"]`; p10 and p90 come
back alongside so the caller sees the spread rather than trusting the point.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from ..result import Quantity, Range, Refusal

# --------------------------------------------------------------------------
# The pin. Corpus: 11-rw-and-crossplots/usgs-produced-waters-geochemical-database-v3
# lines 4, 18-24 (title, DOI, authors, rights, superseded version).
# --------------------------------------------------------------------------
ANCHOR = "11-rw-and-crossplots/usgs-produced-waters-geochemical-database-v3#0"

PINNED_VERSION = "3.0"
PINNED_RELEASE_DATE = "December 2023"
PINNED_DOI = "10.5066/P9DSRCZJ"
PINNED_TITLE = (
    "U.S. Geological Survey National Produced Waters Geochemical Database "
    "(ver. 3.0, December 2023)"
)
PINNED_URL = "https://doi.org/10.5066/P9DSRCZJ"
# Accepted spellings of the release date. The landing page prints "December 2023"
# in the title and "January 9, 2024" as the page date; the publication year in the
# citation block is 2024. Only the release month/year is pinned.
_RELEASE_DATE_ALIASES = ("december 2023", "dec 2023", "2023-12", "12/2023")
# v2.3 (Blondes and others, 2019) is named on the landing page as the superseded
# version, so it is recognised by name in order to be refused by name.
SUPERSEDED_VERSIONS = {"2.3": "Blondes and others, 2019 (superseded by ver. 3.0)"}

# Roles the summary cannot be computed without. There is deliberately no mapping
# from these to real USGS headers: the corpus does not state them.
REQUIRED_ROLES = ("state", "county", "formation", "depth_ft", "tds")
# Ion roles, used when the caller maps them and the rows carry values.
ION_ROLES = ("na", "k", "ca", "mg", "cl", "so4", "hco3", "co3", "br")
OPTIONAL_ROLES = ION_ROLES + (
    "sample_date", "latitude", "longitude", "well_id", "basin", "ph",
)
ACCEPTED_TDS_UNITS = ("mg/L", "ppm")

# --------------------------------------------------------------------------
# Refusal literals. These are the oracle while the dataset is absent, so they are
# module constants a test can import rather than strings buried in a branch.
# --------------------------------------------------------------------------
DATASET_ABSENT_REASON = (
    "the USGS National Produced Waters Geochemical Database is not present in "
    "this repository; no produced-water analyses can be queried"
)
DATASET_ABSENT_NEEDED = (
    f"the release file for {PINNED_TITLE}, DOI {PINNED_DOI}, from {PINNED_URL}",
    "a ProducedWaterDataset handle: path to the release table, "
    f"version='{PINNED_VERSION}', release_date='{PINNED_RELEASE_DATE}'",
    "a column_map declaring which columns of that file hold: "
    + ", ".join(REQUIRED_ROLES),
    "the unit of the TDS column, declared as tds_unit='mg/L' or 'ppm' — the "
    "corpus record states no units",
    "the release data dictionary (and Blondes and others, 2019, for the v2.3 "
    "lineage) for field definitions, QC flags and analysis completeness — the "
    "corpus holds only the landing page",
)

# --------------------------------------------------------------------------
# Caveats carried on every result. Only the first is ours; the rest are sourced,
# and the source is named in the flag registry below so a caller can check it.
# --------------------------------------------------------------------------
FLAG_ANALOGUE = "regional-analogue-not-a-sample-from-this-well"
FLAG_NON_HC = "usgs-scope-includes-non-hydrocarbon-deep-formation-water"
FLAG_NOT_PETRO = "usgs-stated-uses-do-not-include-petrophysics"
FLAG_UNEVEN = "compilation-mixes-analyses-of-uneven-reliability-qc-flags-not-documented-in-corpus"
FLAG_VINTAGE = "sample-vintage-spans-20th-century-to-2010s"
FLAG_MG_PER_L = "tds-unit-mg-per-L-not-converted-to-ppm"
FLAG_NO_MIN_N = "no-minimum-sample-count-set-by-caller"
FLAG_NO_SPREAD = "no-dispersion-threshold-set-by-caller"
FLAG_INCOMPLETE = "incomplete-analyses-dropped"
FLAG_NO_DEPTH = "depth-window-excluded-rows-without-depth"

FLAG_BASIS: dict[str, str] = {
    FLAG_ANALOGUE: "structural: describes this tool's own operation",
    FLAG_NON_HC: f"{ANCHOR}: 'contains ... produced water and other deep "
                 "formation water samples'; geothermal deep formation waters "
                 "are in scope",
    FLAG_NOT_PETRO: f"{ANCHOR}: stated uses are regional hydrogeology, water "
                    "source, treatment/disposal, mineral commodities, "
                    "drinking/agricultural safety — not Rw or saturation",
    FLAG_UNEVEN: "toc/TOC.md: 'the database mixes decades of analyses of uneven "
                 "reliability and this card does not document QC flags'",
    FLAG_VINTAGE: "toc/TOC.md: 'spanning most of the 20th century into the 2010s'",
    FLAG_MG_PER_L: "11-rw-and-crossplots/aapg-formation-water-density: mg/L->ppm "
                   "needs the brine density, which this tool does not have",
}
# The caveats every successful lookup carries, whatever the query.
_ALWAYS_FLAGS = (FLAG_ANALOGUE, FLAG_NON_HC, FLAG_NOT_PETRO, FLAG_UNEVEN, FLAG_VINTAGE)


@dataclass(frozen=True)
class ProducedWaterDataset:
    """A caller-supplied handle on the USGS release file.

    Nothing here is defaulted from memory. `column_map` maps a role name
    (REQUIRED_ROLES + OPTIONAL_ROLES) to the header as it appears in *this* file;
    `tds_unit` is the unit the file's TDS column is in. Both are refused rather
    than assumed, because the corpus states neither.
    """

    path: str
    version: str
    release_date: str
    tds_unit: str
    column_map: Mapping[str, str] = field(default_factory=dict)
    doi: str = PINNED_DOI
    note: str = ""


def _norm(s: Any) -> str:
    return " ".join(str(s).strip().lower().split())


def _to_float(raw: Any) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "")
    if text == "" or _norm(text) in {"na", "n/a", "nd", "null", "none", "-", "--"}:
        return None
    try:
        v = float(text)
    except ValueError:
        return None
    # Sentinels seen across legacy compilations. Negative concentration/depth is
    # not physical, so the negative test also catches -999 style nulls.
    if v < 0:
        return None
    return v


def _percentile(sorted_vals: Sequence[float], p: float) -> float:
    """Linear-interpolation percentile, p in [0, 1]. Median is p=0.5."""
    if not sorted_vals:
        raise ValueError("percentile of an empty sequence")
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = p * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


def _version_refusal(ds: ProducedWaterDataset) -> Refusal | None:
    """R2: the pin, checked before the file is ever opened."""
    declared = (ds.version or "").strip().lstrip("vV").strip()
    declared_date = _norm(ds.release_date or "")
    if not declared or not declared_date:
        return Refusal(
            reason=(
                "the dataset handle does not declare both a version and a release "
                f"date; this tool is pinned to {PINNED_TITLE}, DOI {PINNED_DOI}, "
                "and will not summarise a file it cannot identify"
            ),
            needed=(
                f"version='{PINNED_VERSION}' and release_date='{PINNED_RELEASE_DATE}' "
                "on the ProducedWaterDataset handle",
                f"the release itself, from {PINNED_URL}",
            ),
            source=ANCHOR,
        )
    if declared != PINNED_VERSION or declared_date not in _RELEASE_DATE_ALIASES:
        extra = SUPERSEDED_VERSIONS.get(declared, "")
        return Refusal(
            reason=(
                f"dataset declares version {declared!r} released {ds.release_date!r}"
                + (f" — {extra}" if extra else "")
                + f"; this tool is pinned to version {PINNED_VERSION} "
                f"({PINNED_RELEASE_DATE}), DOI {PINNED_DOI}. Results are not "
                "reproducible across versions and are not reported from an "
                "unconfirmed one"
            ),
            needed=(
                f"{PINNED_TITLE}, DOI {PINNED_DOI}, from {PINNED_URL}",
                f"or an explicit re-pin of PINNED_VERSION away from {PINNED_VERSION}, "
                "with the catalog note updated",
            ),
            source=ANCHOR,
        )
    return None


def _schema_refusal(ds: ProducedWaterDataset, headers: Sequence[str] | None) -> Refusal | None:
    """R3/R4: the declared schema and unit."""
    missing = [r for r in REQUIRED_ROLES if not ds.column_map.get(r)]
    if missing:
        return Refusal(
            reason=(
                "the dataset handle does not map the columns this query needs: "
                + ", ".join(missing)
                + ". The corpus record for this database is a landing page and "
                "states no field names, so no default column map exists and none "
                "is guessed"
            ),
            needed=(
                "column_map entries for: " + ", ".join(missing),
                "the release data dictionary, which names the columns",
            ),
            source=ANCHOR,
        )
    unit = (ds.tds_unit or "").strip()
    if unit not in ACCEPTED_TDS_UNITS:
        return Refusal(
            reason=(
                f"the TDS unit is declared as {ds.tds_unit!r}; this tool accepts "
                + " or ".join(ACCEPTED_TDS_UNITS)
                + " and does not infer a unit, because mg/L and ppm differ by the "
                "brine density (~12% at 200,000 mg/L) and the corpus record states "
                "no units"
            ),
            needed=(
                "tds_unit='mg/L' or tds_unit='ppm', read from the release "
                "data dictionary",
            ),
            source=ANCHOR,
        )
    if headers is not None:
        unknown = {
            role: col for role, col in ds.column_map.items()
            if col and col not in headers
        }
        if unknown:
            return Refusal(
                reason=(
                    "column_map names headers that are not in the file: "
                    + ", ".join(f"{r}->{c!r}" for r, c in sorted(unknown.items()))
                    + ". Headers present: " + ", ".join(headers)
                ),
                needed=("a column_map matching this file's headers",),
                source=ANCHOR,
            )
    return None


def produced_water_query(
    county: str | None = None,
    state: str | None = None,
    formation: str | None = None,
    depth_ft: tuple[float | None, float | None] | None = None,
    dataset: ProducedWaterDataset | None = None,
    min_samples: int | None = None,
    max_tds_ratio: float | None = None,
    include_samples: bool = False,
) -> Quantity | Refusal:
    """Regional formation-water TDS (and major-ion suite) for a place.

    Returns the median TDS of the matching USGS analyses as a `Quantity` in the
    dataset's declared unit, with the full distribution, the per-ion medians and
    the sample count in `assumptions`, and the analogue/provenance caveats in
    `flags`. Refuses per `specs/93-produced_water_query.md` §5 (R1-R8).

    `min_samples` and `max_tds_ratio` are CALLER thresholds with no defaults: the
    corpus states no minimum sample count and no dispersion limit for a regional
    prior. Left unset, the tool answers and flags that nobody set a policy; the
    count and the p90/p10 ratio are always returned either way.
    """
    query: dict[str, Any] = {
        "state": state, "county": county, "formation": formation,
        "depth_ft": tuple(depth_ft) if depth_ft else None,
    }

    # R1 — the operative refusal today. Checked first: the caller cannot fix the
    # query without the data.
    if dataset is None:
        return Refusal(
            reason=DATASET_ABSENT_REASON,
            needed=DATASET_ABSENT_NEEDED,
            source=ANCHOR,
        )

    # R2 — the pin, before the file is opened.
    bad_version = _version_refusal(dataset)
    if bad_version is not None:
        return bad_version

    # R3/R4 — schema and unit, also before the file is opened.
    bad_schema = _schema_refusal(dataset, None)
    if bad_schema is not None:
        return bad_schema

    # R5 — a query with no predicate is not a regional prior.
    if state is None and county is None and formation is None and depth_ft is None:
        return Refusal(
            reason=(
                "no query predicate was given; a summary over the whole national "
                "database is not a regional water-chemistry prior for any well"
            ),
            needed=("at least one of: state, county, formation, depth_ft",),
            source=ANCHOR,
        )

    if not os.path.exists(dataset.path):
        return Refusal(
            reason=(
                f"the dataset file {dataset.path!r} does not exist. "
                + DATASET_ABSENT_REASON
            ),
            needed=DATASET_ABSENT_NEEDED,
            source=ANCHOR,
        )

    cm = dataset.column_map
    with open(dataset.path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.DictReader(fh)
        headers = list(reader.fieldnames or [])
        bad_headers = _schema_refusal(dataset, headers)
        if bad_headers is not None:
            return bad_headers
        rows = list(reader)

    d_lo = d_hi = None
    if depth_ft:
        d_lo, d_hi = depth_ft

    want_state, want_county, want_fm = _norm(state) if state else None, \
        _norm(county) if county else None, _norm(formation) if formation else None

    state_seen = False
    county_seen = False
    matched: list[dict[str, str]] = []
    n_dropped_no_depth = 0
    for row in rows:
        if want_state is not None:
            if _norm(row.get(cm["state"], "")) != want_state:
                continue
            state_seen = True
        if want_county is not None:
            if _norm(row.get(cm["county"], "")) != want_county:
                continue
            county_seen = True
        if want_fm is not None and _norm(row.get(cm["formation"], "")) != want_fm:
            continue
        if depth_ft:
            d = _to_float(row.get(cm["depth_ft"]))
            if d is None:
                n_dropped_no_depth += 1
                continue
            if d_lo is not None and d < d_lo:
                continue
            if d_hi is not None and d > d_hi:
                continue
        matched.append(row)

    # R6 — nothing matched. Say which predicate emptied the set: "this state is
    # not in the database" and "this formation is not in this state" are
    # different problems for the operator.
    if not matched:
        if want_state is not None and not state_seen:
            miss, what = state, "state"
        elif want_county is not None and not county_seen:
            miss, what = county, "county"
        elif want_fm is not None:
            miss, what = formation, "formation"
        else:
            miss, what = str(depth_ft), "depth window"
        return Refusal(
            reason=(
                f"the database holds no analyses for {what} {miss!r} under this "
                f"query {query}; the compilation covers the United States only and "
                "sampling is uneven, so an uncovered area or formation is expected "
                "rather than an error"
            ),
            needed=(
                "a covered area or formation, a wider depth window, "
                "or a measured water sample from the well itself",
                "coverage cannot be widened by this tool: it does not "
                "substitute a neighbouring formation for the one asked for",
            ),
            source=ANCHOR,
        )

    tds_vals: list[float] = []
    kept: list[dict[str, str]] = []
    for row in matched:
        v = _to_float(row.get(cm["tds"]))
        if v is None:
            continue
        tds_vals.append(v)
        kept.append(row)
    n_dropped_no_tds = len(matched) - len(kept)

    if not tds_vals:
        return Refusal(
            reason=(
                f"{len(matched)} analyses match the query but none carries a "
                "usable TDS value; an incomplete ion suite is common in a "
                "compilation spanning most of the 20th century"
            ),
            needed=(
                "analyses with a TDS value, or a caller decision to compute TDS "
                "from the ion sum — which this tool does not do, because the "
                "corpus does not state whether the release's own TDS is measured "
                "or summed",
            ),
            source=ANCHOR,
        )

    n = len(tds_vals)
    # R7 — CALLER threshold. No default: the corpus states no minimum sample count.
    if min_samples is not None and n < min_samples:
        return Refusal(
            reason=(
                f"only {n} usable analyses match this query; the caller requires "
                f"at least {min_samples} to characterise a regional prior"
            ),
            needed=(
                f"at least {min_samples} analyses: widen the depth window, the "
                "county or the formation, or lower min_samples deliberately",
                "note that no source in this corpus states a minimum sample "
                "count — this threshold is the caller's",
            ),
            source=ANCHOR,
        )

    ordered = sorted(tds_vals)
    p10, p50, p90 = (_percentile(ordered, q) for q in (0.10, 0.50, 0.90))
    ratio = (p90 / p10) if p10 > 0 else float("inf")

    # R8 — CALLER threshold, same standing as R7.
    if max_tds_ratio is not None and ratio > max_tds_ratio:
        return Refusal(
            reason=(
                f"the matching analyses are too scattered to characterise: "
                f"p90/p10 = {ratio:.2f} over {n} samples, above the caller's "
                f"limit of {max_tds_ratio}. TDS spans {ordered[0]:g} to "
                f"{ordered[-1]:g} {dataset.tds_unit}"
            ),
            needed=(
                "a tighter query (single formation, narrower depth window), or a "
                "caller decision to accept the spread and use the range rather "
                "than the median",
                "no source in this corpus states a dispersion limit — this "
                "threshold is the caller's",
            ),
            source=ANCHOR,
        )

    ion_medians: dict[str, dict[str, float]] = {}
    for ion in ION_ROLES:
        col = cm.get(ion)
        if not col:
            continue
        vals = sorted(v for v in (_to_float(r.get(col)) for r in kept) if v is not None)
        if vals:
            ion_medians[ion] = {"median": _percentile(vals, 0.5), "n": len(vals)}

    depths = sorted(
        v for v in (_to_float(r.get(cm["depth_ft"])) for r in kept) if v is not None
    )
    formations = sorted({
        str(r.get(cm["formation"], "")).strip()
        for r in kept if str(r.get(cm["formation"], "")).strip()
    })
    dates = sorted({
        str(r.get(cm["sample_date"], "")).strip()
        for r in kept if cm.get("sample_date") and str(r.get(cm["sample_date"], "")).strip()
    }) if cm.get("sample_date") else []

    flags = list(_ALWAYS_FLAGS)
    if dataset.tds_unit == "mg/L":
        flags.append(FLAG_MG_PER_L)
    if min_samples is None:
        flags.append(FLAG_NO_MIN_N)
    if max_tds_ratio is None:
        flags.append(FLAG_NO_SPREAD)
    if n_dropped_no_tds:
        flags.append(FLAG_INCOMPLETE)
    if n_dropped_no_depth:
        flags.append(FLAG_NO_DEPTH)

    assumptions: dict[str, Any] = {
        "dataset_title": PINNED_TITLE,
        "dataset_version": PINNED_VERSION,
        "dataset_release_date": PINNED_RELEASE_DATE,
        "dataset_doi": dataset.doi or PINNED_DOI,
        "dataset_path": dataset.path,
        "statistic": "median (p50) — chosen over the mean because the "
                     "compilation's QC is undocumented and outliers are expected",
        "n_matched": len(matched),
        "n_samples": n,
        "n_dropped_no_tds": n_dropped_no_tds,
        "n_dropped_no_depth": n_dropped_no_depth,
        "tds_p10": p10,
        "tds_p50": p50,
        "tds_p90": p90,
        "tds_min": ordered[0],
        "tds_max": ordered[-1],
        "tds_p90_over_p10": ratio,
        "tds_unit": dataset.tds_unit,
        "ion_medians": ion_medians,
        "ions_absent_from_column_map": [i for i in ION_ROLES if not cm.get(i)],
        "depth_ft_range": (depths[0], depths[-1]) if depths else None,
        "formations_matched": formations,
        "sample_date_range": (dates[0], dates[-1]) if dates else None,
        "min_samples_threshold": min_samples,
        "max_tds_ratio_threshold": max_tds_ratio,
        "flag_basis": {f: FLAG_BASIS[f] for f in flags if f in FLAG_BASIS},
    }
    if include_samples:
        assumptions["samples"] = kept

    return Quantity(
        value=p50,
        unit=dataset.tds_unit,
        method="usgs-produced-waters-v3-regional-summary",
        source=ANCHOR,
        inputs=query,
        assumptions=assumptions,
        flags=tuple(flags),
    )


def produced_water_spread(
    *args: Any, **kwargs: Any
) -> Range | Refusal:
    """The same query reported as a p10-p90 band rather than a point.

    For a caller that wants the prior propagated as a range into `rw_from_tds`
    (#92) and `uncertainty_propagate` (#70). Refuses identically; `members`
    carries the sample count, the median and the p90/p10 ratio so the band is not
    mistaken for a measurement interval.
    """
    q = produced_water_query(*args, **kwargs)
    if isinstance(q, Refusal):
        return q
    a = q.assumptions
    return Range(
        low=a["tds_p10"],
        high=a["tds_p90"],
        unit=q.unit,
        method="usgs-produced-waters-v3-regional-p10-p90",
        source=ANCHOR,
        members={
            "median": a["tds_p50"],
            "min": a["tds_min"],
            "max": a["tds_max"],
            "n_samples": float(a["n_samples"]),
            "p90_over_p10": a["tds_p90_over_p10"],
        },
    )
