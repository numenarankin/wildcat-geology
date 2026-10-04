"""Session plumbing: the weighted case set (#73) and the trajectory log (#74).

Neither owes a citation — `tool-catalog.md:549,553` marks both "plumbing, no
citation owed" — so the specs pin contracts instead of equations, at
`specs/73-case_set_build.md` and `specs/74-trajectory_log.md`. Three decisions
here are not obvious from the code.

**No weight is derived from evidence.** A case set exists to say which reading
is more likely and what would settle it. The tempting move is to score the
branches from their evidence and emit 0.7 / 0.3, but the evidence ordering the
architecture actually gives — `measured > documented > stated`
(`well-log-agent.md:263`) — is *ordinal*. It says which branch is better
supported, not by how much, and turning it into a split would manufacture
exactly the orphan number `tools/result.py` exists to prevent. So weights come
from the caller with a stated basis, or they are declared equal and flagged as
declared, and evidence contributes an `evidence_rank` beside the weight rather
than inside it.

**A case with no collapsing document is refused, not weakened.** `case_set_build`
will not emit a case that names no document capable of collapsing it. The whole
value of the object is "resolve by pulling the W-2" (`well-log-agent.md:215`);
an alternative the operator can do nothing about is a shrug with a weight on it.
The refusal is total for the call, because a case set silently missing the
conflict that mattered is worse than no case set.

**The trajectory log orders by sequence number, never by time.** `ts` is
diagnostic and is excluded from the entry hash, so replaying a recorded session
on a different day produces a byte-identical chain hash. Time cannot reorder a
replay, and two entries in the same millisecond cannot tie. Storage is an
in-memory list behind `TrajectoryStore` on purpose: `pipeline-implementation.md`
§5 says to fold this into the chat route's existing turn log rather than invent
a second store, so no database is invented here.
"""
from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
import math
import re
import threading
from typing import Any, Callable, Iterable, Protocol

from .result import Quantity, Refusal

# =============================================================================
# 73 - case_set_build
# =============================================================================

SPEC_73 = "specs/73-case_set_build.md"
SOURCE_73 = (
    "plumbing - contract pinned by specs/73-case_set_build.md; conflict records "
    "per well-log-agent.md:263 via conflict_detect [#65]"
)

# Evidence kinds, strongest first. From the state object's
# `evidence: [{claim, source_id, kind: measured|documented|stated}]`
# (well-log-agent.md:263) and the invariant at harness-implementation.md:112
# that `stated` can never be promoted to `measured`. Used for RANKING ONLY -
# see the module docstring.
EVIDENCE_KINDS: tuple[str, ...] = ("measured", "documented", "stated")

# Strings that name no document. A resolving_document of "more data" is the
# exact non-answer this field exists to outlaw, so it is rejected by name
# rather than by a heuristic about what a document looks like.
VAGUE_DOCUMENT_TOKENS: frozenset[str] = frozenset({
    "unknown", "n/a", "na", "none", "tbd", "?", "-", "--",
    "more data", "additional data", "further work", "see above",
})

# A conflict split this many ways was probably not decomposed.
WIDE_CONFLICT_BRANCHES = 4

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return _SLUG_RE.sub("-", text.casefold()).strip("-") or "case"


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _refuse_73(reason: str, needed: Iterable[str]) -> Refusal:
    return Refusal(reason=reason, needed=tuple(needed), source=SOURCE_73)


def case_set_build(
    conflicts: list[dict[str, Any]],
    weight_bases: dict[str, str] | None = None,
) -> Quantity | Refusal:
    """Build the weighted case set from detected conflicts (#73).

    `conflicts` are records in the state object's shape
    `{id?, description, branches[], resolving_document?}`; each branch needs at
    minimum a `label` and a `completion_implication`, and either the branch or
    its conflict must name a `resolving_document`. Weights are caller-supplied
    with a basis in `weight_bases[conflict_id]`, or declared equal.

    Returns a `Quantity` whose `value` is the number of cases and whose
    `inputs["cases"]` holds the records, or a `Refusal` naming the conflict and
    branch that could not be turned into a case.
    """
    if not isinstance(conflicts, list):
        raise ValueError("conflicts must be a list of conflict records")
    if weight_bases is not None and not isinstance(weight_bases, dict):
        raise ValueError("weight_bases must be a dict of {conflict_id: basis}")
    for c in conflicts:
        if not isinstance(c, dict):
            raise ValueError("every conflict record must be a dict")

    bases = dict(weight_bases or {})

    if not conflicts:
        return _refuse_73(
            "no conflicts supplied - a case set is only built on the escalated path",
            ("at least one conflict record from conflict_detect [#65]",),
        )

    cases: list[dict[str, Any]] = []
    conflict_ids: list[str] = []
    basis_by_conflict: dict[str, str] = {}
    flags: list[str] = []
    seen_ids: set[str] = set()

    for index, conflict in enumerate(conflicts, start=1):
        cid = _text(conflict.get("id")) or f"conflict-{index}"
        if cid in seen_ids:
            return _refuse_73(
                f"conflict id {cid!r} appears twice - case ids would collide",
                ("a distinct id per conflict record",),
            )
        seen_ids.add(cid)

        description = _text(conflict.get("description"))
        if not description:
            return _refuse_73(
                f"conflict {cid!r} has no description - a case set names what is in conflict",
                ("description",),
            )

        branches = conflict.get("branches")
        if not isinstance(branches, list):
            raise ValueError(f"conflict {cid!r}: branches must be a list")
        for b in branches:
            if not isinstance(b, dict):
                raise ValueError(f"conflict {cid!r}: every branch must be a dict")

        if len(branches) < 2:
            return _refuse_73(
                f"conflict {cid!r} has {len(branches)} branch(es) - a case set requires "
                "at least two mutually exclusive readings",
                ("a second branch, or drop the conflict",),
            )

        conflict_doc = _text(conflict.get("resolving_document"))

        # --- per-branch validation ------------------------------------------
        prepared: list[dict[str, Any]] = []
        labels: list[str] = []
        for pos, branch in enumerate(branches, start=1):
            label = _text(branch.get("label"))
            if not label:
                return _refuse_73(
                    f"conflict {cid!r} branch {pos} has no label",
                    ("label",),
                )
            if label in labels:
                return _refuse_73(
                    f"conflict {cid!r} has duplicate branch labels: {label!r}",
                    ("distinct labels within a conflict",),
                )
            labels.append(label)

            implication = _text(branch.get("completion_implication"))
            if not implication:
                return _refuse_73(
                    f"conflict {cid!r} branch {label!r} has no completion_implication - "
                    "a case that implies nothing is not actionable",
                    ("completion_implication",),
                )

            branch_doc_raw = branch.get("resolving_document")
            branch_doc = _text(branch_doc_raw)
            if branch_doc:
                doc, doc_from, raw = branch_doc, "branch", branch_doc
            elif conflict_doc:
                doc, doc_from, raw = conflict_doc, "conflict", conflict_doc
            else:
                return _refuse_73(
                    f"conflict {cid!r} branch {label!r} names no document that would "
                    "collapse it (branch and conflict resolving_document both absent) - "
                    "a case with no resolving document is a shrug, not a case",
                    ("resolving_document on the branch or on the conflict",),
                )
            if raw.casefold() in VAGUE_DOCUMENT_TOKENS:
                return _refuse_73(
                    f"conflict {cid!r} branch {label!r} gives resolving_document {raw!r}, "
                    "which names no document",
                    ("a specific document, e.g. 'W-2 completion report, API 42-497-31234'",),
                )

            evidence = branch.get("evidence") or ()
            if not isinstance(evidence, (list, tuple)):
                raise ValueError(f"conflict {cid!r} branch {label!r}: evidence must be a list")
            ev_records: list[dict[str, Any]] = []
            for ev in evidence:
                if not isinstance(ev, dict):
                    raise ValueError(
                        f"conflict {cid!r} branch {label!r}: every evidence record must be a dict"
                    )
                kind = _text(ev.get("kind")).casefold()
                if kind not in EVIDENCE_KINDS:
                    return _refuse_73(
                        f"conflict {cid!r} branch {label!r} carries evidence of kind "
                        f"{ev.get('kind')!r}; the state object admits only "
                        f"{', '.join(EVIDENCE_KINDS)}",
                        (f"kind in {', '.join(EVIDENCE_KINDS)}",),
                    )
                ev_records.append(dict(ev))

            prepared.append({
                "label": label,
                "completion_implication": implication,
                "collapsing_document": doc,
                "collapsing_document_source": doc_from,
                "evidence": tuple(ev_records),
                "weight_in": branch.get("weight"),
            })

        # --- weights ---------------------------------------------------------
        supplied = [p for p in prepared if p["weight_in"] is not None]
        if supplied and len(supplied) != len(prepared):
            return _refuse_73(
                f"conflict {cid!r} supplies weight on {len(supplied)} of {len(prepared)} "
                "branches - a partial weighting has no basis",
                ("a weight on every branch, or none (weights are then declared equal)",),
            )

        if supplied:
            basis_text = _text(bases.get(cid))
            if not basis_text:
                return _refuse_73(
                    f"conflict {cid!r} supplies weights with no stated basis",
                    (f"weight_bases[{cid!r}] naming where the numbers came from",),
                )
            raws: list[float] = []
            for p in prepared:
                w = p["weight_in"]
                if isinstance(w, bool) or not isinstance(w, (int, float)):
                    raise ValueError(
                        f"conflict {cid!r} branch {p['label']!r}: weight must be a number"
                    )
                w = float(w)
                if not math.isfinite(w):
                    return _refuse_73(
                        f"conflict {cid!r} branch {p['label']!r} weight {w} is not finite",
                        ("a finite non-negative weight on every branch",),
                    )
                if w < 0:
                    return _refuse_73(
                        f"conflict {cid!r} branch {p['label']!r} weight {w} is negative",
                        ("a finite non-negative weight on every branch",),
                    )
                raws.append(w)
            total = math.fsum(raws)
            if total <= 0:
                return _refuse_73(
                    f"conflict {cid!r} weights sum to zero - no case would carry any weight",
                    ("at least one positive weight",),
                )
            basis = f"caller: {basis_text}"
        else:
            raws = [1.0] * len(prepared)
            total = float(len(prepared))
            basis = (
                "declared-equal: nothing supplied distinguishes the branches "
                f"(1/{len(prepared)})"
            )
            flags.append(
                f"conflict {cid!r}: weights declared equal - not derived from evidence"
            )
        basis_by_conflict[cid] = basis

        if supplied:
            normalised = [round(w / total, 6) for w in raws]
            # The largest case absorbs the rounding residue so the conflict's
            # weights sum to exactly 1.0. Ties break on label, so the choice is
            # stable across runs.
            top = min(
                range(len(prepared)),
                key=lambda i: (-normalised[i], prepared[i]["label"]),
            )
            normalised[top] = 1.0 - math.fsum(
                w for i, w in enumerate(normalised) if i != top
            )
        else:
            # Declared-equal means equal: every case gets exactly 1/n and no
            # case absorbs a residue, because a hair of extra weight on one
            # branch would contradict the basis string on all of them. The set
            # sums to 1.0 within float tolerance rather than exactly.
            normalised = [1.0 / len(prepared)] * len(prepared)

        # --- evidence ranking (ordinal, never a weight) -----------------------
        best: list[int] = []
        for p in prepared:
            kinds = [
                EVIDENCE_KINDS.index(_text(e.get("kind")).casefold())
                for e in p["evidence"]
            ]
            best.append(min(kinds) if kinds else len(EVIDENCE_KINDS))
        has_evidence = any(b < len(EVIDENCE_KINDS) for b in best)
        if has_evidence:
            tiers = sorted(set(best))
            ranks: list[int | None] = [tiers.index(b) + 1 for b in best]
            if len(tiers) > 1 and not supplied:
                flags.append(
                    f"conflict {cid!r}: branches differ in evidence strength; ranking "
                    "recorded per case, weights left equal - no numeric split is "
                    "derivable from an ordinal ranking"
                )
        else:
            ranks = [None] * len(prepared)

        if len(prepared) >= WIDE_CONFLICT_BRANCHES and not supplied:
            flags.append(
                f"conflict {cid!r} has {len(prepared)} branches - every case weight is "
                f"{1.0 / len(prepared):.6g}; consider whether it decomposes"
            )

        # case_id is "stable identity for tests, evals and the log", and the
        # duplicate-conflict-id refusal above exists because "case ids would
        # collide". Distinct labels can still collide through the slug -
        # "Sw = 0.32 (Rt uncorrected)" and "Sw = 0.32 [Rt uncorrected]" differ
        # only in punctuation - and an id that names two cases identifies
        # neither, so it is refused in the same shape rather than emitted.
        slugs: dict[str, str] = {}
        for p in prepared:
            slug = _slug(p["label"])
            if slug in slugs:
                return _refuse_73(
                    f"conflict {cid!r} branches {slugs[slug]!r} and {p['label']!r} both "
                    f"reduce to case_id {f'{cid}::{slug}'!r} - a case_id names one case "
                    "or it names none",
                    ("branch labels that differ in more than punctuation",),
                )
            slugs[slug] = p["label"]

        built: list[dict[str, Any]] = []
        for i, p in enumerate(prepared):
            case_flags: list[str] = []
            if p["collapsing_document_source"] == "conflict":
                case_flags.append(
                    "collapsing document inherited from the conflict, not specific to this case"
                )
            if ranks[i] is not None and best[i] == len(EVIDENCE_KINDS):
                case_flags.append(
                    "no evidence supplied for this branch while others carry some"
                )
            built.append({
                "case_id": f"{cid}::{_slug(p['label'])}",
                "conflict_id": cid,
                "conflict_description": description,
                "label": p["label"],
                "weight": normalised[i],
                "weight_raw": float(raws[i]),
                "weight_basis": basis,
                "completion_implication": p["completion_implication"],
                "collapsing_document": p["collapsing_document"],
                "collapsing_document_source": p["collapsing_document_source"],
                "evidence": p["evidence"],
                "evidence_rank": ranks[i],
                "flags": tuple(case_flags),
            })

        built.sort(key=lambda c: (-c["weight"], c["label"]))
        cases.extend(built)
        conflict_ids.append(cid)

    return Quantity(
        value=float(len(cases)),
        unit="cases",
        method="case_set_build v1",
        source=SOURCE_73,
        inputs={
            "cases": cases,
            "conflict_ids": conflict_ids,
            "conflict_count": len(conflict_ids),
        },
        assumptions={
            "weight_basis": basis_by_conflict,
            "weight_normalisation": (
                "raw weights divided by their sum within a conflict, 6 dp; the "
                "largest case absorbs the residue so each conflict sums to 1.0"
            ),
            "evidence_rank_order": (
                "measured > documented > stated (well-log-agent.md:263) - ordinal "
                "only, never converted to a weight"
            ),
            "case_order": (
                "conflicts in input order; within a conflict by descending weight "
                "then ascending label"
            ),
            "vague_document_tokens": sorted(VAGUE_DOCUMENT_TOKENS),
        },
        flags=tuple(flags),
    )


# =============================================================================
# 74 - trajectory_log
# =============================================================================

SPEC_74 = "specs/74-trajectory_log.md"
SOURCE_74 = "plumbing - contract pinned by specs/74-trajectory_log.md"

# Closed vocabulary. An eval harness that must handle arbitrary kinds cannot
# assert anything, so an unknown kind refuses rather than being admitted.
KINDS: tuple[str, ...] = (
    "confidence_change",
    "model_answer",
    "note",
    "refusal",
    "state_transition",
    "tool_call",
    "tool_result",
)

# Stage attribution is what makes the log a read of the state object rather than
# a parallel structure (pipeline-implementation.md:161).
STAGES: tuple[str, ...] = (
    "harness",
    "stage0_resolve",
    "stage1_fanout",
    "stage2_conflicts",
    "stage3_reason",
    "stage4_render",
)

TOOL_OUTCOMES: tuple[str, ...] = ("error", "quantity", "range", "refusal")
ANSWER_PATHS: tuple[str, ...] = ("escalated", "standard")

# Required payload keys per kind. Conditional requirements (provenance on a
# numeric tool result, a cause on a confidence change) are enforced below.
REQUIRED_PAYLOAD: dict[str, tuple[str, ...]] = {
    "confidence_change": ("field", "to", "from", "cause"),
    "model_answer": ("requested_model", "path"),
    "note": ("text",),
    "refusal": ("reason",),
    "state_transition": ("field", "to"),
    "tool_call": ("tool", "args"),
    "tool_result": ("tool", "call_id", "outcome"),
}

# Fewer changes than this on one field is not a trend, so monotonic increase is
# not reported for it (well-log-agent.md:464).
MONOTONIC_MIN_CHANGES = 3

_HASHED_FIELDS = ("seq", "session_id", "kind", "stage", "actor", "model", "payload")


def _canonical(obj: Any) -> str:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="microseconds")


def _refuse_74(reason: str, needed: Iterable[str]) -> Refusal:
    return Refusal(reason=reason, needed=tuple(needed), source=SOURCE_74)


class TrajectoryStore(Protocol):
    """Append-only sink. Deliberately has no update and no delete."""

    def append(self, entry: dict[str, Any]) -> None: ...

    def records(self) -> tuple[dict[str, Any], ...]: ...


class InMemoryTrajectoryStore:
    """The only implementation today.

    `pipeline-implementation.md` §5 says to extend the chat route's existing turn
    log rather than invent a second store, so this holds the session in memory
    and hands out deep copies on read. Persisting later means implementing
    `TrajectoryStore` elsewhere, not changing the schema or any caller.
    """

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def append(self, entry: dict[str, Any]) -> None:
        self._entries.append(entry)

    def records(self) -> tuple[dict[str, Any], ...]:
        return tuple(copy.deepcopy(e) for e in self._entries)

    def __len__(self) -> int:
        return len(self._entries)


class TrajectoryLog:
    """Append-only, sequence-ordered session log (#74).

    Ordering is by `seq`, assigned here and never by the caller. `ts` is
    diagnostic: it is excluded from `entry_hash`, so the same session replayed on
    a different day produces the same `chain_hash`.
    """

    def __init__(
        self,
        session_id: str,
        clock: Callable[[], str] | None = None,
        store: TrajectoryStore | None = None,
    ) -> None:
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("session_id must be a non-empty string")
        self.session_id = session_id.strip()
        self._clock = clock or _utc_now
        # `store is not None`, never `store or ...`: a store that reports its
        # own length - InMemoryTrajectoryStore does, and so would any row-counting
        # persistent one - is falsy while empty, so `or` threw away the caller's
        # store on the first call and wrote the session into a throwaway. That is
        # the swap specs/74 relies on ("implementing TrajectoryStore elsewhere,
        # not changing the schema or any caller") failing silently.
        self._store: TrajectoryStore = (
            store if store is not None else InMemoryTrajectoryStore()
        )
        self._seq = 0
        self._chain = ""
        self._open_calls: dict[str, int] = {}
        self._answered_calls: set[str] = set()
        self._entry_flags: list[str] = []
        # Stage 1 fans out and "branches all write at once"
        # (harness-implementation.md:118), so seq assignment cannot be a bare
        # read-modify-write: preempted between reading self._seq and storing it,
        # two branches take the same number and the chain forks off one
        # predecessor. Reentrant because append() calls snapshot() while held.
        self._lock = threading.RLock()

    # -- reads ---------------------------------------------------------------

    def records(self) -> tuple[dict[str, Any], ...]:
        """The projection, in ascending `seq`. There is no other order."""
        return self._store.records()

    @property
    def chain_hash(self) -> str:
        return self._chain

    def __len__(self) -> int:
        return self._seq

    # -- the append path -----------------------------------------------------

    def append(self, event: dict[str, Any]) -> Quantity | Refusal:
        """Validate and append one event. Returns the log's typed state or a Refusal."""
        if not isinstance(event, dict):
            raise ValueError("an event must be a dict")

        with self._lock:
            return self._append_locked(event)

    def _append_locked(self, event: dict[str, Any]) -> Quantity | Refusal:
        position = self._seq + 1
        refusal = self._validate(event, position)
        if refusal is not None:
            return refusal

        kind = event["kind"].strip()
        stage = event["stage"].strip()
        actor = event["actor"].strip()
        model = event.get("model")
        model = model.strip() if isinstance(model, str) else None
        payload = copy.deepcopy(event["payload"])

        seq = position
        self._seq = seq

        if kind == "tool_call":
            call_id = _text(payload.get("call_id")) or f"call-{seq}"
            payload["call_id"] = call_id
            self._open_calls[call_id] = seq
        elif kind == "tool_result":
            self._answered_calls.add(_text(payload.get("call_id")))
        elif kind == "confidence_change":
            prev = payload.get("from")
            payload["delta"] = (
                None if prev is None else round(float(payload["to"]) - float(prev), 12)
            )

        entry: dict[str, Any] = {
            "seq": seq,
            "session_id": self.session_id,
            "kind": kind,
            "stage": stage,
            "actor": actor,
            "model": model,
            "payload": payload,
        }
        entry_hash = hashlib.sha256(
            _canonical({k: entry[k] for k in _HASHED_FIELDS}).encode("utf-8")
        ).hexdigest()
        self._chain = hashlib.sha256((self._chain + entry_hash).encode("utf-8")).hexdigest()

        ts = event.get("ts")
        entry["ts"] = ts if isinstance(ts, str) and ts.strip() else self._clock()
        entry["entry_hash"] = entry_hash
        entry["chain_hash"] = self._chain

        entry_flags: list[str] = []
        if kind == "model_answer":
            requested = _text(payload.get("requested_model"))
            if requested and model and requested != model:
                flag = f"model redirect: {requested} -> {model}"
                entry_flags.append(flag)
                self._entry_flags.append(flag)
        entry["flags"] = tuple(entry_flags)

        self._store.append(entry)
        return self.snapshot()

    # -- validation ----------------------------------------------------------

    def _validate(self, event: dict[str, Any], position: int) -> Refusal | None:
        where = f"entry {position}"

        if "seq" in event:
            return _refuse_74(
                f"{where} supplies seq={event['seq']!r}; seq is assigned by the log, "
                "never by the caller",
                ("drop 'seq' from the event",),
            )

        kind = _text(event.get("kind"))
        if kind not in KINDS:
            return _refuse_74(
                f"{where}: unknown kind {event.get('kind')!r}; known kinds: "
                + ", ".join(KINDS),
                KINDS,
            )
        where = f"{where} (kind {kind!r})"

        stage = _text(event.get("stage"))
        if stage not in STAGES:
            return _refuse_74(
                f"{where}: unknown stage {event.get('stage')!r}; known stages: "
                + ", ".join(STAGES),
                STAGES,
            )

        if not _text(event.get("actor")):
            return _refuse_74(
                f"{where} has no actor - the log records who made every entry",
                ("actor",),
            )

        model = event.get("model")
        if model is not None and not isinstance(model, str):
            raise ValueError("model must be a string or None")

        payload = event.get("payload")
        if payload is None:
            return _refuse_74(
                f"{where} has no payload; kind {kind!r} requires "
                + ", ".join(REQUIRED_PAYLOAD[kind]),
                tuple(f"payload.{k}" for k in REQUIRED_PAYLOAD[kind]),
            )
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dict")
        try:
            _canonical(payload)
        except (TypeError, ValueError) as exc:
            return _refuse_74(
                f"{where} payload is not JSON-serialisable: {exc}",
                ("a payload of JSON scalars, lists and string-keyed dicts",),
            )

        for key in REQUIRED_PAYLOAD[kind]:
            if key not in payload:
                return _refuse_74(
                    f"{where} payload has no {key!r}",
                    (f"payload.{key}",),
                )

        if kind == "model_answer":
            if not _text(model):
                return _refuse_74(
                    f"{where} has no model - \"record which model actually answered\" "
                    "(well-log-agent.md:465)",
                    ("model, and payload.requested_model",),
                )
            if _text(payload.get("path")) not in ANSWER_PATHS:
                return _refuse_74(
                    f"{where}: unknown path {payload.get('path')!r}; known paths: "
                    + ", ".join(ANSWER_PATHS),
                    ANSWER_PATHS,
                )

        if kind == "confidence_change":
            if not _text(payload.get("cause")):
                return _refuse_74(
                    f"{where} payload has no 'cause' - a confidence change with no "
                    "cause cannot be debugged",
                    ("payload.cause",),
                )
            for key in ("from", "to"):
                v = payload.get(key)
                if key == "from" and v is None:
                    continue
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    raise ValueError(f"confidence {key!r} must be a number (or None for 'from')")
                if not math.isfinite(float(v)) or not 0.0 <= float(v) <= 1.0:
                    return _refuse_74(
                        f"{where}: confidence {key}={v} is outside [0, 1]",
                        ("a confidence in [0, 1]",),
                    )

        if kind == "tool_result":
            outcome = _text(payload.get("outcome"))
            if outcome not in TOOL_OUTCOMES:
                return _refuse_74(
                    f"{where}: unknown outcome {payload.get('outcome')!r}; known "
                    "outcomes: " + ", ".join(TOOL_OUTCOMES),
                    TOOL_OUTCOMES,
                )
            call_id = _text(payload.get("call_id"))
            if call_id not in self._open_calls:
                return _refuse_74(
                    f"{where} references call_id {payload.get('call_id')!r} which was "
                    "never opened in this session",
                    ("a tool_call entry with that call_id, appended first",),
                )
            if outcome in ("quantity", "range") and not (
                _text(payload.get("method")) and _text(payload.get("source"))
            ):
                return _refuse_74(
                    f"{where} outcome {outcome!r} has no method/source - a number in "
                    "the log without its provenance is an orphan number",
                    ("payload.method", "payload.source"),
                )
            if outcome in ("refusal", "error") and not _text(payload.get("reason")):
                return _refuse_74(
                    f"{where} outcome {outcome!r} has no reason",
                    ("payload.reason",),
                )

        if kind == "refusal" and not (
            _text(payload.get("tool")) or _text(payload.get("gate"))
        ):
            return _refuse_74(
                f"{where} names neither a tool nor a gate",
                ("payload.tool or payload.gate",),
            )

        corrects = payload.get("corrects")
        if corrects is not None:
            if isinstance(corrects, bool) or not isinstance(corrects, int):
                raise ValueError("payload.corrects must be an int seq")
            if not 1 <= corrects <= self._seq:
                return _refuse_74(
                    f"{where} corrects seq {corrects}, which is not in this log",
                    ("the seq of an entry already appended",),
                )

        return None

    # -- summary and flags ---------------------------------------------------

    def summary(self) -> dict[str, Any]:
        entries = self._store.records()
        by_kind: dict[str, int] = {}
        by_stage: dict[str, int] = {}
        models: set[str] = set()
        confidence: dict[str, list[float]] = {}
        refusals = 0
        for e in entries:
            by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
            by_stage[e["stage"]] = by_stage.get(e["stage"], 0) + 1
            if e["model"]:
                models.add(e["model"])
            if e["kind"] == "refusal" or (
                e["kind"] == "tool_result" and e["payload"].get("outcome") == "refusal"
            ):
                refusals += 1
            if e["kind"] == "confidence_change":
                confidence.setdefault(e["payload"]["field"], []).append(
                    float(e["payload"]["to"])
                )
        unanswered = sorted(set(self._open_calls) - self._answered_calls)
        return {
            "entries": len(entries),
            "by_kind": dict(sorted(by_kind.items())),
            "by_stage": dict(sorted(by_stage.items())),
            "tool_calls": by_kind.get("tool_call", 0),
            "tool_results": by_kind.get("tool_result", 0),
            "unanswered_tool_calls": len(unanswered),
            "unanswered_call_ids": tuple(unanswered),
            "refusals": refusals,
            "models": tuple(sorted(models)),
            "model_redirects": len(self._entry_flags),
            "confidence_fields": tuple(sorted(confidence)),
            "confidence_trend": {k: tuple(v) for k, v in sorted(confidence.items())},
        }

    def flags(self) -> tuple[str, ...]:
        summary = self.summary()
        out: list[str] = []
        if summary["unanswered_call_ids"]:
            out.append(
                f"{summary['unanswered_tool_calls']} tool call(s) with no recorded "
                "result: " + ", ".join(summary["unanswered_call_ids"])
            )
        out.extend(self._entry_flags)
        for field, trend in summary["confidence_trend"].items():
            if len(trend) >= MONOTONIC_MIN_CHANGES and all(
                b > a for a, b in zip(trend, trend[1:])
            ):
                out.append(
                    f"confidence for {field!r} increased monotonically across "
                    f"{len(trend)} changes - monotonic increase across a session is a "
                    "flag on its face (well-log-agent.md:464)"
                )
        if summary["refusals"]:
            out.append(f"{summary['refusals']} refusal(s) recorded")
        return tuple(out)

    # -- the typed return ----------------------------------------------------

    def snapshot(self) -> Quantity:
        entries = self._store.records()
        return Quantity(
            value=float(len(entries)),
            unit="entries",
            method="trajectory_log v1",
            source=SOURCE_74,
            inputs={
                "session_id": self.session_id,
                "entries": list(entries),
                "sequence": [e["seq"] for e in entries],
                "chain_hash": self._chain,
                "summary": self.summary(),
            },
            assumptions={
                "ordering": (
                    "ascending seq, gapless from 1; ts is diagnostic and never the sort key"
                ),
                "append_only": (
                    "corrections are new entries carrying payload.corrects; no update "
                    "or delete exists"
                ),
                "hash": (
                    "sha256 over canonical JSON of {seq, session_id, kind, stage, "
                    "actor, model, payload}, excluding ts; chained into chain_hash"
                ),
                "store": (
                    "in-memory behind TrajectoryStore; pipeline-implementation.md "
                    "sec.5 says extend the existing turn log rather than invent a "
                    "second store"
                ),
                "kinds": list(KINDS),
                "stages": list(STAGES),
            },
            flags=self.flags(),
        )


def trajectory_log(
    events: list[dict[str, Any]],
    session_id: str,
    clock: Callable[[], str] | None = None,
    log: TrajectoryLog | None = None,
) -> Quantity | Refusal:
    """Fold a session's events into an ordered, append-only trajectory (#74).

    Events are appended in the order given and receive gapless sequence numbers.
    Pass `log` to continue an existing session; pass `clock` (a callable
    returning an ISO-8601 string) for a deterministic `ts`.

    Returns a `Quantity` whose `value` is the entry count and whose
    `inputs["entries"]` is the ordered log, or the first `Refusal` raised by an
    invalid event. Entries appended before that point stay appended: the log is
    append-only, so an accepted entry is never retracted.
    """
    if not isinstance(events, list):
        raise ValueError("events must be a list of event dicts")

    # `log is not None`, never `log or ...`: TrajectoryLog defines __len__, so a
    # freshly constructed empty log is falsy and `or` silently routed the whole
    # batch into a throwaway log the caller never sees. That is the Stage-0 case
    # (harness-implementation.md:125) - the log is empty exactly when the first
    # events arrive.
    session = log if log is not None else TrajectoryLog(session_id, clock=clock)
    if log is not None and clock is not None:
        raise ValueError("clock applies to a new log; the existing log keeps its own")

    if not events and log is None:
        return _refuse_74(
            "no events supplied - an empty trajectory is not a log",
            ("at least one event: a state transition, tool call, confidence change, "
             "refusal or model answer",),
        )

    for event in events:
        result = session.append(event)
        if isinstance(result, Refusal):
            return result
    return session.snapshot()
