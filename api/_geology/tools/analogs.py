"""Case-based reference over previously analysed zones (#63).

Plumbing: no equation is owed, so `specs/63-analog_retrieve.md` pins the contract
instead. Three decisions here are not obvious from the code.

**The store does not exist, and this module does not invent one.** Nothing in
`well-log-agent.md`, `harness-implementation.md`, `pipeline-implementation.md` or
this repository defines a library of analysed zones with known outcomes.
`ZoneEvaluation` (well-log-agent.md:254) is one analysis in flight and has no
outcome field at all; Stage 0's cache (harness-implementation.md:130) is a
per-well scratch copy invalidated on new data; `offsets[]` holds neighbouring RRC
wells, not analysed zones; the RRC outcome set (pipeline-implementation.md:183)
would carry outcomes but is eval substrate, is not indexed by curve signature,
and is not built. So this module defines the record schema, reads the declared
store path if a store is ever written there, and refuses by name when it is not.
Shipping sample cases would be an invented equation one layer up: indistinguishable
later from real wells with real outcomes, and someone would drill on it.

**Similarity is a stated arithmetic rule, not a model.** Scaled mean absolute
difference over a closed registry of numeric curve features, each with a declared
scale, so any ranking the tool produces can be re-derived by hand from the
`per_feature` block in the result. No embeddings and no LLM call: a tool that
calls a model is not a deterministic tool. The scales and the similarity
threshold are this tool's own definition of "similar", are not from the corpus,
and have not been swept against a validation set as well-log-agent.md:624
requires. Every result says so in `flags` rather than letting the number pass as
calibrated.

**An analog is evidence, not an answer.** Every match carries its own outcome
provenance (`evidence_kind`, `source_id`, who recorded it and when), `stated` is
never promoted to `measured`, and `value` is a count of cases rather than any
petrophysical quantity, because nothing computed for a case transfers to the zone
being analysed.
"""
from __future__ import annotations

import json
import math
import pathlib
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .result import Quantity, Refusal

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Declared, not created. Nothing in this repo writes it; see the module docstring
# and specs/63-analog_retrieve.md "the store does not exist".
DEFAULT_STORE_PATH = ROOT / "case-store" / "analog-cases.jsonl"

CASE_SCHEMA_VERSION = "analog-case-v1"
METHOD = "analog_retrieve scaled-L1 v1"
SPEC = "specs/63-analog_retrieve.md"

# On every returned Quantity. The catalog says "case-based reference" on purpose.
EVIDENCE_FLAG = (
    "analog: case-based reference only. similarity does not transfer this "
    "case's outcome or any of its values to the query zone"
)
UNCALIBRATED_FLAG = (
    "feature scales and the similarity threshold are provisional, not corpus-sourced, "
    "and not swept against a validation set (well-log-agent.md:624)"
)

# --- defaults ----------------------------------------------------------------
# PROVISIONAL, uncalibrated. Exposed as arguments so a caller sets its own.
DEFAULT_MIN_SIMILARITY = 0.70
DEFAULT_MIN_SHARED_FEATURES = 3
DEFAULT_TOP_K = 5

SIM_DECIMALS = 6  # scores are compared and reported at this precision

VALID_DEPTH_REFERENCES = ("KB", "GL", "DF")
VALID_EVIDENCE_KINDS = ("measured", "documented", "stated")
# Closed set. Adding a kind is a spec edit, not a data decision.
VALID_OUTCOME_KINDS = (
    "oil",
    "gas",
    "oil_and_gas",
    "wet",
    "tight",
    "noncommercial",
    "untested",
)


@dataclass(frozen=True)
class Feature:
    """One registered curve-signature feature and the size of one unit of
    difference on it. `scale` is what makes the metric dimensionless."""

    name: str
    unit: str
    scale: float
    rationale: str


# The closed feature registry. A signature is compared only over these.
FEATURES: dict[str, Feature] = {
    f.name: f
    for f in (
        Feature("gr_api", "API", 100.0, "clean sand to shale is roughly this gap"),
        Feature("rhob_g_cc", "g/cc", 0.25, "quartz matrix to a porous sand"),
        Feature("nphi_frac", "v/v", 0.15, "tight to good neutron porosity"),
        Feature("phi_frac", "v/v", 0.10, "10 porosity units separates tight from good"),
        Feature("log10_rt_ohmm", "log10 ohm-m", 1.0,
                "resistivity reads per decade; one decade is wet versus pay"),
        Feature("dt_us_ft", "us/ft", 30.0, "tight (~55) to porous sand (~85)"),
        Feature("pef", "b/e", 3.0, "sandstone to limestone"),
        Feature("thickness_ft", "ft", 25.0, "a thin stringer versus a thick zone"),
        Feature("vsh_frac", "v/v", 0.25, "a quarter of the shale range"),
        Feature("sw_frac", "v/v", 0.25, "a quarter of the saturation range"),
    )
}


# ---------------------------------------------------------------------------
# the store
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CaseStore:
    """A named, ordered collection of case records. Order never reaches the
    output: ranking is total and ends in ascending case_id."""

    name: str
    records: tuple[Mapping[str, Any], ...]

    @staticmethod
    def from_records(records: Iterable[Mapping[str, Any]], name: str = "in-memory") -> "CaseStore":
        return CaseStore(name=name, records=tuple(records))


def load_default_store(path: pathlib.Path | None = None) -> CaseStore | None:
    """Read the declared JSON Lines store. `None` when it does not exist, which
    is the state of this repository and the reason this tool mostly refuses.

    Raises `ValueError` only for a file that exists and is not readable as JSON
    Lines: that is a broken store, and the caller turns it into a refusal.
    """
    p = pathlib.Path(path) if path is not None else DEFAULT_STORE_PATH
    if not p.exists():
        return None
    records: list[Mapping[str, Any]] = []
    with p.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{p}: line {lineno} is not valid JSON ({exc.msg})") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"{p}: line {lineno} is not a JSON object")
            records.append(obj)
    return CaseStore(name=str(p), records=tuple(records))


# ---------------------------------------------------------------------------
# record validation
# ---------------------------------------------------------------------------


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def _nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def validate_case(record: Any) -> tuple[str, ...]:
    """Every reason `record` is not a usable case, in a stable order.

    A record is data, so problems are reported rather than raised, and a bad
    record is excluded rather than repaired.
    """
    problems: list[str] = []
    if not isinstance(record, Mapping):
        return ("record is not a mapping",)

    if not _nonempty_str(record.get("case_id")):
        problems.append("case_id missing or not a non-empty string")
    if not _nonempty_str(record.get("well_api")):
        problems.append("well_api missing or not a non-empty string")

    schema = record.get("schema")
    if schema is not None and schema != CASE_SCHEMA_VERSION:
        problems.append(f"schema {schema!r} is not {CASE_SCHEMA_VERSION!r}")

    interval = record.get("interval")
    if not isinstance(interval, Mapping):
        problems.append("interval missing or not a mapping")
    else:
        top, base = interval.get("top_md_ft"), interval.get("base_md_ft")
        if not _is_number(top) or not _is_number(base):
            problems.append("interval.top_md_ft / base_md_ft must be finite numbers")
        elif float(base) <= float(top):
            problems.append("interval.base_md_ft must be below top_md_ft")
        if interval.get("depth_reference") not in VALID_DEPTH_REFERENCES:
            problems.append(
                "interval.depth_reference must be one of " + "/".join(VALID_DEPTH_REFERENCES)
            )
        if not isinstance(interval.get("datum_resolved"), bool):
            problems.append("interval.datum_resolved must be a bool")

    signature = record.get("signature")
    if not isinstance(signature, Mapping) or not signature:
        problems.append("signature missing or not a non-empty mapping")
    else:
        bad = sorted(str(k) for k, v in signature.items() if not _is_number(v))
        if bad:
            problems.append("signature values must be finite numbers: " + ", ".join(bad))
        if not any(k in FEATURES for k in signature):
            problems.append("signature carries no registered feature")

    analysis = record.get("analysis")
    if not isinstance(analysis, Mapping) or not _nonempty_str(analysis.get("method")):
        problems.append("analysis.method missing or not a non-empty string")

    outcome = record.get("outcome")
    if not isinstance(outcome, Mapping):
        problems.append("outcome missing or not a mapping")
    else:
        if outcome.get("kind") not in VALID_OUTCOME_KINDS:
            problems.append("outcome.kind must be one of " + "/".join(VALID_OUTCOME_KINDS))
        if not _nonempty_str(outcome.get("statement")):
            problems.append("outcome.statement missing or not a non-empty string")
        if outcome.get("evidence_kind") not in VALID_EVIDENCE_KINDS:
            problems.append(
                "outcome.evidence_kind must be one of " + "/".join(VALID_EVIDENCE_KINDS)
            )
        if not _nonempty_str(outcome.get("source_id")):
            problems.append("outcome.source_id missing: an outcome without provenance is a rumour")

    prov = record.get("provenance")
    if not isinstance(prov, Mapping):
        problems.append("provenance missing or not a mapping")
    else:
        if not _nonempty_str(prov.get("recorded_by")):
            problems.append("provenance.recorded_by missing or not a non-empty string")
        if not _nonempty_str(prov.get("recorded_at")):
            problems.append("provenance.recorded_at missing or not a non-empty string")

    return tuple(problems)


# ---------------------------------------------------------------------------
# argument checking (programmer error, so these raise)
# ---------------------------------------------------------------------------


def _check_signature(signature: Any) -> dict[str, float]:
    if not isinstance(signature, Mapping) or not signature:
        raise ValueError("signature must be a non-empty mapping of feature name to number")
    out: dict[str, float] = {}
    for key, value in signature.items():
        if not isinstance(key, str):
            raise ValueError(f"signature key {key!r} is not a string")
        if key not in FEATURES:
            raise ValueError(
                f"{key!r} is not a registered curve-signature feature; "
                f"registered: {', '.join(sorted(FEATURES))}"
            )
        if not _is_number(value):
            raise ValueError(f"signature[{key!r}] must be a finite number, got {value!r}")
        out[key] = float(value)
    return out


def _resolve_scales(scales: Mapping[str, float] | None) -> dict[str, float]:
    resolved = {name: f.scale for name, f in FEATURES.items()}
    if scales is None:
        return resolved
    if not isinstance(scales, Mapping):
        raise ValueError("scales must be a mapping of feature name to positive number")
    for key, value in scales.items():
        if key not in FEATURES:
            raise ValueError(f"scale override {key!r} is not a registered feature")
        if not _is_number(value) or float(value) <= 0:
            raise ValueError(f"scale for {key!r} must be a positive finite number, got {value!r}")
        resolved[key] = float(value)
    return resolved


# ---------------------------------------------------------------------------
# #63 analog_retrieve
# ---------------------------------------------------------------------------


def analog_retrieve(
    signature: Mapping[str, float],
    *,
    store: CaseStore | Sequence[Mapping[str, Any]] | None = None,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
    top_k: int = DEFAULT_TOP_K,
    min_shared_features: int = DEFAULT_MIN_SHARED_FEATURES,
    exclude_api: str | None = None,
    outcome_kinds: Sequence[str] | None = None,
    scales: Mapping[str, float] | None = None,
    store_path: pathlib.Path | None = None,
) -> Quantity | Refusal:
    """Previously analysed zones whose curve signatures are close to `signature`.

    Returns a `Quantity` counting the matched cases, each carried in
    `inputs["matches"]` with its own outcome and outcome provenance, or a
    `Refusal` naming what is missing. Never returns the closest available case as
    a stand-in for a match.
    """
    query = _check_signature(signature)
    resolved_scales = _resolve_scales(scales)

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be an int >= 1")
    if (not isinstance(min_shared_features, int) or isinstance(min_shared_features, bool)
            or min_shared_features < 1):
        raise ValueError("min_shared_features must be an int >= 1")
    if not _is_number(min_similarity) or not 0.0 <= float(min_similarity) <= 1.0:
        raise ValueError("min_similarity must be a number in [0, 1]")
    min_similarity = float(min_similarity)
    if exclude_api is not None and not _nonempty_str(exclude_api):
        raise ValueError("exclude_api must be None or a non-empty string")
    if outcome_kinds is not None:
        if isinstance(outcome_kinds, str) or not isinstance(outcome_kinds, Sequence):
            raise ValueError("outcome_kinds must be None or a sequence of outcome kind strings")
        unknown = [k for k in outcome_kinds if k not in VALID_OUTCOME_KINDS]
        if unknown:
            raise ValueError(
                f"unknown outcome kind(s) {unknown}; valid: {', '.join(VALID_OUTCOME_KINDS)}"
            )
        outcome_kinds = tuple(outcome_kinds)

    # --- resolve the store ---------------------------------------------------
    store_source = str(store_path) if store_path is not None else str(DEFAULT_STORE_PATH)
    if store is None:
        try:
            store = load_default_store(store_path)
        except ValueError as exc:
            return Refusal(
                reason=f"the case store is unreadable: {exc}",
                needed=("a store whose every line is a JSON object matching "
                        f"{CASE_SCHEMA_VERSION} (see {SPEC})",),
                source=store_source,
            )
        if store is None:
            return Refusal(
                reason=(
                    "no store of previously analysed zones exists. Nothing in "
                    "well-log-agent.md, harness-implementation.md or "
                    "pipeline-implementation.md defines one: ZoneEvaluation has no "
                    "outcome field, Stage 0's cache is a per-well scratch copy, and "
                    "offsets[] holds neighbouring RRC wells rather than analysed "
                    f"zones. The declared path {store_source} does not exist. No "
                    "analog can be returned, and none will be fabricated."
                ),
                needed=(
                    f"a populated case store at {store_source} (JSON Lines, "
                    f"{CASE_SCHEMA_VERSION} records)",
                    "a writer that records each analysed zone with its curve signature, "
                    "its outcome, and the provenance of that outcome",
                    "a decision on where the store lives (pipeline-implementation.md:215)",
                ),
                source=store_source,
            )
    elif not isinstance(store, CaseStore):
        if isinstance(store, (str, bytes)) or not isinstance(store, Sequence):
            raise ValueError("store must be a CaseStore, a sequence of records, or None")
        store = CaseStore.from_records(store)

    store_source = store.name

    if not store.records:
        return Refusal(
            reason=(f"the case store {store.name!r} exists but holds no records. "
                    "An empty store is not an absent store: nobody has written an "
                    "analysed zone into it yet."),
            needed=("at least one recorded case with a curve signature and a known outcome",),
            source=store_source,
        )

    # --- validate, filter, score --------------------------------------------
    excluded: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    scored: list[dict[str, Any]] = []
    best_overlap = 0
    best_sim = -1.0
    best_sim_case = ""
    # Counted by case_id, so a flag can describe the cases actually returned
    # rather than the cases that merely cleared the threshold: top_k truncates
    # after this loop.
    stated_ids: set[str] = set()
    unresolved_datum_ids: set[str] = set()
    schemaless_ids: set[str] = set()
    # Cases removed by a caller filter never reach the overlap count, so a
    # refusal must not report their overlap as zero.
    dropped_by_exclude_api = 0
    dropped_by_outcome_kinds = 0
    compared = 0

    for index, record in enumerate(store.records):
        problems = validate_case(record)
        if problems:
            ident = record.get("case_id") if isinstance(record, Mapping) else None
            excluded.append({
                "case_id": ident if _nonempty_str(ident) else f"<record {index}>",
                "reason": "; ".join(problems),
            })
            continue

        case_id = str(record["case_id"])
        if case_id in seen_ids:
            excluded.append({"case_id": case_id, "reason": "duplicate case_id"})
            continue
        seen_ids.add(case_id)

        if exclude_api is not None and str(record["well_api"]) == exclude_api:
            dropped_by_exclude_api += 1
            excluded.append({"case_id": case_id, "reason": f"well_api == exclude_api {exclude_api}"})
            continue

        outcome = dict(record["outcome"])
        if outcome_kinds is not None and outcome["kind"] not in outcome_kinds:
            dropped_by_outcome_kinds += 1
            excluded.append({
                "case_id": case_id,
                "reason": f"outcome kind {outcome['kind']!r} not in requested kinds",
            })
            continue

        compared += 1
        case_sig = dict(record["signature"])
        shared = sorted(k for k in case_sig if k in query and k in FEATURES)
        unscored = sorted(k for k in case_sig if k not in FEATURES)
        best_overlap = max(best_overlap, len(shared))
        if len(shared) < min_shared_features:
            excluded.append({
                "case_id": case_id,
                "reason": (f"shares {len(shared)} registered feature(s) with the query, "
                           f"below min_shared_features {min_shared_features}"),
            })
            continue

        per_feature: dict[str, dict[str, float]] = {}
        total = 0.0
        for name in shared:
            q_val = query[name]
            c_val = float(case_sig[name])
            scaled = abs(q_val - c_val) / resolved_scales[name]
            total += scaled
            per_feature[name] = {
                "query": q_val,
                "case": c_val,
                "scale": resolved_scales[name],
                "scaled_diff": round(scaled, SIM_DECIMALS),
            }
        distance = total / len(shared)
        similarity = round(max(0.0, 1.0 - distance), SIM_DECIMALS)

        if similarity > best_sim or (similarity == best_sim and case_id < best_sim_case):
            best_sim, best_sim_case = similarity, case_id

        if similarity < min_similarity:
            excluded.append({
                "case_id": case_id,
                "reason": f"similarity {similarity} below min_similarity {min_similarity}",
            })
            continue

        interval = dict(record["interval"])
        prov = dict(record["provenance"])
        if not interval.get("datum_resolved", False):
            unresolved_datum_ids.add(case_id)
        if outcome["evidence_kind"] == "stated":
            stated_ids.add(case_id)
        if "schema" not in record:
            schemaless_ids.add(case_id)

        scored.append({
            "case_id": case_id,
            "well_api": str(record["well_api"]),
            "formation": record.get("formation"),
            "interval": interval,
            "similarity": similarity,
            "distance": round(distance, SIM_DECIMALS),
            "shared_features": shared,
            "per_feature": per_feature,
            "unscored_features": unscored,
            "analysis": dict(record["analysis"]),
            "outcome": outcome,
            "outcome_evidence_kind": outcome["evidence_kind"],
            "outcome_source_id": outcome["source_id"],
            "recorded_by": prov["recorded_by"],
            "recorded_at": prov["recorded_at"],
        })

    valid_count = len(seen_ids)
    if valid_count == 0:
        return Refusal(
            reason=(f"every one of the {len(store.records)} record(s) in {store.name!r} failed "
                    f"schema validation, so the store holds no usable case. Reasons: "
                    + " | ".join(f"{e['case_id']}: {e['reason']}" for e in excluded)),
            needed=(f"case records matching {CASE_SCHEMA_VERSION} (see {SPEC})",),
            source=store_source,
        )

    if not scored:
        if compared == 0 and (dropped_by_exclude_api or dropped_by_outcome_kinds):
            # No case was ever compared, so nothing is known about their overlap
            # or their similarity. Reporting "best overlap 0" here would state
            # something false about the store and send the caller to the wrong
            # dial.
            by_filter = []
            if dropped_by_exclude_api:
                by_filter.append(
                    f"{dropped_by_exclude_api} because well_api == exclude_api {exclude_api!r} "
                    "(a well is not its own analog)"
                )
            if dropped_by_outcome_kinds:
                by_filter.append(
                    f"{dropped_by_outcome_kinds} because outcome kind not in the requested "
                    f"outcome_kinds {list(outcome_kinds or ())}"
                )
            return Refusal(
                reason=(f"no case in {store.name!r} was compared against the query: all "
                        f"{valid_count} valid record(s) were removed by a caller filter — "
                        + "; ".join(by_filter)
                        + ". Their similarity is therefore unknown, and no filtered-out case "
                          "is substituted for a match."),
                needed=("a valid case that passes the requested filters: one from a different "
                        "well, or one whose outcome kind was asked for",),
                source=store_source,
            )
        if best_overlap < min_shared_features:
            return Refusal(
                reason=(f"no case in {store.name!r} shares {min_shared_features} registered "
                        f"signature feature(s) with the query; the best overlap was "
                        f"{best_overlap}. Two features in common is not a signature."),
                needed=("cases whose signatures carry the same features as the query, "
                        "or a lower min_shared_features",),
                source=store_source,
            )
        return Refusal(
            reason=(f"no case reached min_similarity {min_similarity}; the best was "
                    f"{best_sim} ({best_sim_case}). The least-bad case is not returned as "
                    "though it were a match."),
            needed=("a closer case, or an explicit lower min_similarity",),
            source=store_source,
        )

    # deterministic total order: similarity desc, shared count desc, case_id asc
    scored.sort(key=lambda m: (-m["similarity"], -len(m["shared_features"]), m["case_id"]))
    matches = scored[:top_k]
    excluded.sort(key=lambda e: str(e["case_id"]))

    # Counted over what top_k actually returns: a flag that says "returned" and
    # counts cases the caller never sees is a number disagreeing with its label.
    returned_ids = {m["case_id"] for m in matches}
    stated_outcomes = len(stated_ids & returned_ids)
    unresolved_datums = len(unresolved_datum_ids & returned_ids)
    schemaless = len(schemaless_ids & returned_ids)

    flags = [EVIDENCE_FLAG, UNCALIBRATED_FLAG]
    if stated_outcomes:
        flags.append(
            f"{stated_outcomes} returned case(s) carry a stated outcome, not a measured one; "
            "stated is never promoted"
        )
    if unresolved_datums:
        flags.append(
            f"{unresolved_datums} returned case(s) have an unresolved datum; their interval "
            "depths are not comparable to a resolved one"
        )
    if schemaless:
        flags.append(f"{schemaless} returned case(s) carry no schema version")
    if excluded:
        flags.append(f"{len(excluded)} record(s) in the store were excluded; see assumptions")
    if len(scored) > top_k:
        flags.append(f"{len(scored) - top_k} further case(s) cleared the threshold beyond top_k")

    return Quantity(
        value=float(len(matches)),
        unit="cases",
        method=METHOD,
        # Each case's own identifier is its provenance.
        source=f"{store.name}: " + "; ".join(m["case_id"] for m in matches),
        inputs={
            "query_signature": query,
            "matches": matches,
            "store": {
                "name": store.name,
                "records": len(store.records),
                "valid": valid_count,
                "excluded": len(excluded),
            },
        },
        assumptions={
            "metric": ("similarity = max(0, 1 - mean_i(|q_i - c_i| / scale_i)) over the "
                       "registered features shared by query and case"),
            "scales": {name: resolved_scales[name] for name in sorted(resolved_scales)},
            "scales_status": "PROVISIONAL, not corpus-sourced, not calibrated",
            "min_similarity": min_similarity,
            "min_shared_features": min_shared_features,
            "top_k": top_k,
            "exclude_api": exclude_api,
            "outcome_kinds": list(outcome_kinds) if outcome_kinds is not None else None,
            "tie_break": "similarity desc, then shared-feature count desc, then case_id asc",
            "rounding": f"similarity compared and reported at {SIM_DECIMALS} decimals",
            "schema_version": CASE_SCHEMA_VERSION,
            "evidence_status": ("analog cases are reference, not evidence about this zone; "
                                "each case's outcome provenance travels with it"),
            "excluded": excluded,
        },
        flags=tuple(flags),
    )
