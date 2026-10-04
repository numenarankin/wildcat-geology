"""Knowledge-base retrieval: keyed lookup (#59) and corpus search (#60).

Both are plumbing — no equation is owed, so `specs/59-kb_lookup.md` and
`specs/60-kb_search.md` pin the contract instead. Two decisions here are not
obvious from the code.

**"Semantic" retrieval with no model.** The catalog calls `kb_search` semantic.
It is BM25. The meaning comes from the TOC: `build_toc.py` already had a model
write, per segment, "the questions this passage actually answers, in the words an
operator would use", because "'Chapter 7: Saturation Determination' routes
nothing". Matching a question lexically against that cached routing text is
exact, instant and reproducible; re-deriving it per query with a model would be
none of those, and a tool that calls a model is not a deterministic tool.

**Why a document-card index exists at all.** `tool-verification.md:57` records
the defect: "Short documents lose to long ones under both BM25 and card-count
ranking." A 248-segment textbook gets 248 chances to appear; the two one-segment
NETL documents in `15-recompletion-screening/` get two, and in the real build
*zero* tools cited that section even though it holds the published method for
two of them. So a second index carries one record per document, scored on what
the document is *about*, and a per-document cap stops one source filling the
result. Ranking is deliberately not a function of segment size.

Verbatimness is structural rather than promised: the index stores `(file, start,
end)` and the text is sliced out of the file at return time, with the same read
and the same offsets `scripts/show_segment.py` uses. There is no second copy of
the corpus that could drift from it.
"""
from __future__ import annotations

import collections
import hashlib
import json
import math
import os
import pathlib
import re
import sys
from typing import Any, Callable, Iterable

from . import petrophysics
from .result import Quantity, Refusal

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Vendored into the wildcat app, the corpus ships at the repo root rather than
# beside this package, so its location is named rather than assumed.
# `GEOLOGY_CORPUS_ROOT` is the same variable the TypeScript side reads, which is
# what keeps the two halves reading one corpus. The sibling layout stays the
# fallback so the original repo still runs unchanged.
CORPUS = pathlib.Path(os.environ.get("GEOLOGY_CORPUS_ROOT") or ROOT)
KB = CORPUS / "knowledge-base"
TOC = CORPUS / "toc"
SEGMENT_META = TOC / ".segments.jsonl"
CARD_META = TOC / ".cards.jsonl"
INDEX_CACHE = TOC / ".kb-index.json"

# Bumped whenever anything below changes the index contents. The value is folded
# into the cache fingerprint, so an old artefact is rebuilt rather than served.
INDEX_VERSION = "kb-index-v1"

# --- ranking constants -------------------------------------------------------
# BM25 Okapi. b=0.75 is the length normalisation that keeps a long segment from
# winning on volume.
BM25_K1 = 1.5
BM25_B = 0.75
# A term in more than half the segments carries no signal; dropping it beats
# down-weighting it (inherited from scripts/tool_provenance.py).
COMMON_TERM_FRACTION = 0.5
# question_forms is the field written to be matched against, and it is ~100
# tokens against ~900 tokens of prose. Unweighted it is swamped by the text it
# was written to index.
META_WEIGHT = 3
# Document-card score, relative to the segment score. Both are BM25 so the
# magnitudes are comparable.
W_DOC = 0.5
# Per distinct query term naming an equation the segment's TOC entry names.
W_EQ = 2.0
# Refusal gate. Tuned against a probe set: off-domain queries reach coverage
# 0.25, in-domain probes from one word to a nineteen-word sentence reach 0.5-1.0.
MIN_COVERAGE = 0.5
MIN_SCORE = 8.0
# Advisory only — flags a thin result, never suppresses it.
WEAK_SCORE = 20.0

SOURCE_TOC = "toc/TOC.md"
# Asquith Tables 4.1/4.2, the reconcile decision recorded in petrophysics.py.
# BOTH anchors, because the two tables are not in the same segment: Table 4.2
# (rho_ma, rho_fl) segments as #18, Table 4.1 (Dt_ma Wyllie/RHG, Dt_fl) as #17.
# A lithology record carries dt_ma_wyllie and dt_ma_rhg as well as rho_ma, so
# citing #18 alone would point at a real but *different* table for two of its
# three fields — the MISCITED failure `tool-verification.md` was written about.
# Joined with "; " the way kb_search joins its own anchor list.
SOURCE_MATRIX = f"{petrophysics.ASQUITH_T41}; {petrophysics.ASQUITH_T42}"

STOP = set("""a an the and or of for to in on at by with from as is are be been it its this that
these those which what when where how why not no than then there here into over under between
each per any all both some other same such only own more most less least very can may might will
would should could must rather never always every use used using uses do does did have has had
i we you they he she""".split())

_TOKEN = re.compile(r"[a-z][a-z0-9_\-']{1,}")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens of two or more characters, stop words removed.

    No stemming: a stemmer is a transform between what the caller asked and what
    was matched, and it is not obvious from the result which one happened.
    """
    return [w for w in _TOKEN.findall(text.lower()) if w not in STOP]


def canonical(key: str) -> str:
    """Whitespace and case are presentation, not identity. Nothing else moves."""
    return re.sub(r"\s+", " ", key.strip()).casefold()


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------


def _corpus_docs() -> list[pathlib.Path]:
    """The corpus files, in a fixed order. Mirrors build_toc.corpus_docs()."""
    return sorted(
        p for p in KB.glob("*/*.md")
        if not p.is_relative_to(KB / "originals")
        and not p.stem.endswith((".equations", ".visual"))
    )


def _segment_spans(text: str) -> list[tuple[int, int]]:
    """Segment offsets, imported from build_toc rather than reimplemented.

    A second copy of the segmentation rule would let anchors drift from what
    show_segment.py resolves, which would make every citation in a result wrong
    while everything still looked healthy. The import is lazy because build_toc
    pulls in the Anthropic SDK at module scope, and the cached path must never
    touch it.
    """
    # Two layouts hold it: `scripts/build_toc.py` in the corpus repo, and
    # `build_toc.py` beside this package once vendored into the app. Both are
    # offered, so neither checkout needs a different kb.py.
    for candidate in (ROOT / "scripts", ROOT):
        entry = str(candidate)
        if (candidate / "build_toc.py").is_file() and entry not in sys.path:
            sys.path.insert(0, entry)
    try:
        from build_toc import segment  # type: ignore
    except Exception as exc:  # pragma: no cover - environment problem, not logic
        raise RuntimeError(
            f"cannot import segmentation from scripts/build_toc.py: {exc}. "
            "kb_search anchors must match show_segment.py exactly, so it will "
            "not fall back to a local copy of the rule."
        ) from exc
    return segment(text)


def _fingerprint() -> str:
    """Content hash of everything the index is derived from, plus the tuning."""
    h = hashlib.sha256()
    h.update(INDEX_VERSION.encode())
    h.update(f"|{META_WEIGHT}|{sorted(STOP)}|{_TOKEN.pattern}".encode())
    for p in _corpus_docs():
        h.update(str(p.relative_to(KB)).encode())
        h.update(hashlib.sha256(p.read_bytes()).hexdigest().encode())
    for p in (SEGMENT_META, CARD_META):
        h.update(hashlib.sha256(p.read_bytes()).hexdigest().encode() if p.exists() else b"-")
    return h.hexdigest()


def _load_jsonl(path: pathlib.Path, key: str, value: str) -> dict[str, Any]:
    if not path.exists():
        return {}
    out: dict[str, Any] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec[key]] = rec[value]
    return out


def _build_index() -> dict[str, Any]:
    seg_meta = _load_jsonl(SEGMENT_META, "key", "entry")
    card_meta = _load_jsonl(CARD_META, "slug", "card")

    segments: list[dict[str, Any]] = []
    doc_sections: dict[str, str] = {}
    doc_counts: collections.Counter[str] = collections.Counter()

    for path in _corpus_docs():
        slug, section = path.stem, path.parent.name
        doc_sections[slug] = section
        text = path.read_text(errors="ignore")
        for i, (a, b) in enumerate(_segment_spans(text)):
            anchor = f"{section}/{slug}#{i}"
            meta = seg_meta.get(anchor, {})
            routing = " ".join(
                [meta.get("heading", "")]
                + list(meta.get("question_forms", []))
                + list(meta.get("topics", []))
                + list(meta.get("entities", []))
                + list(meta.get("equations_present", []))
            )
            tokens = tokenize(text[a:b]) + tokenize(routing) * META_WEIGHT
            doc_counts[slug] += 1
            segments.append({
                "anchor": anchor,
                "section": section,
                "slug": slug,
                "i": i,
                "a": a,
                "b": b,
                "heading": meta.get("heading", ""),
                "eqs": list(meta.get("equations_present", [])),
                "tf": dict(collections.Counter(tokens)),
            })

    cards: dict[str, dict[str, Any]] = {}
    for slug, card in card_meta.items():
        # not_good_for is excluded on purpose: indexing it would boost exactly
        # the documents that disclaim the topic.
        field = " ".join(
            [card.get("covers", "")]
            + list(card.get("authoritative_for", []))
            + [card.get("scope", "")]
        )
        cards[slug] = {"tf": dict(collections.Counter(tokenize(field)))}

    return {
        "version": INDEX_VERSION,
        "fingerprint": _fingerprint(),
        "segments": segments,
        "cards": cards,
        "doc_sections": doc_sections,
        "doc_counts": dict(doc_counts),
    }


def _postings(records: Iterable[tuple[Any, dict[str, int]]]) -> tuple[dict[str, list], float]:
    """term -> keys, in insertion order, plus the mean field length."""
    post: dict[str, list] = collections.defaultdict(list)
    total = 0
    n = 0
    for key, tf in records:
        n += 1
        total += sum(tf.values())
        for term in tf:
            post[term].append(key)
    return dict(post), (total / n if n else 1.0)


_INDEX: dict[str, Any] | None = None


def _index() -> dict[str, Any]:
    """Load, validate or rebuild the index; memoised for the process.

    Validity is a content fingerprint rather than a timestamp, so a stale
    artefact can never be served.
    """
    global _INDEX
    if _INDEX is not None and _INDEX["fingerprint"] == _fingerprint():
        return _INDEX

    fp = _fingerprint()
    idx: dict[str, Any] | None = None
    if INDEX_CACHE.exists():
        try:
            cached = json.loads(INDEX_CACHE.read_text())
            if cached.get("fingerprint") == fp and cached.get("version") == INDEX_VERSION:
                idx = cached
        except (json.JSONDecodeError, OSError):
            idx = None

    cache_note = ""
    if idx is None:
        idx = _build_index()
        try:
            tmp = INDEX_CACHE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(idx, sort_keys=True))
            os.replace(tmp, INDEX_CACHE)
        except OSError as exc:
            cache_note = f"index cache not written ({exc.__class__.__name__}); rebuilt in memory"

    seg_post, seg_avg = _postings((i, s["tf"]) for i, s in enumerate(idx["segments"]))
    card_post, card_avg = _postings((slug, c["tf"]) for slug, c in sorted(idx["cards"].items()))
    idx["seg_postings"] = seg_post
    idx["seg_avglen"] = seg_avg
    idx["card_postings"] = card_post
    idx["card_avglen"] = card_avg
    idx["cache_note"] = cache_note
    _INDEX = idx
    return idx


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _bm25(
    qcount: dict[str, int],
    tf_of: Callable[[Any], dict[str, int]],
    postings: dict[str, list],
    avglen: float,
    n_records: int,
) -> tuple[dict[Any, float], dict[Any, set], set[str]]:
    """Okapi BM25. Returns scores, matched query terms per record, and the terms
    that were dropped as too common to carry signal.

    Query terms are walked in sorted order over postings lists held in index
    order, so the floating-point sums are reproducible run to run.
    """
    scores: dict[Any, float] = collections.defaultdict(float)
    matched: dict[Any, set] = collections.defaultdict(set)
    dropped: set[str] = set()
    for term in sorted(qcount):
        plist = postings.get(term)
        if not plist:
            continue
        if len(plist) > n_records * COMMON_TERM_FRACTION:
            dropped.add(term)
            continue
        idf = math.log(1 + (n_records - len(plist) + 0.5) / (len(plist) + 0.5))
        for key in plist:
            tf = tf_of(key)
            freq = tf[term]
            dl = sum(tf.values())
            scores[key] += (
                qcount[term] * idf * freq * (BM25_K1 + 1)
                / (freq + BM25_K1 * (1 - BM25_B + BM25_B * dl / avglen))
            )
            matched[key].add(term)
    return scores, matched, dropped


# ---------------------------------------------------------------------------
# #60 kb_search
# ---------------------------------------------------------------------------


def kb_search(
    query: str,
    top_k: int = 5,
    section: str | None = None,
    document: str | None = None,
    require_equations: bool = False,
    per_doc: int = 2,
    min_coverage: float = MIN_COVERAGE,
    min_score: float = MIN_SCORE,
    max_chars: int | None = None,
) -> Quantity | Refusal:
    """Retrieve verbatim corpus chunks for a question, with their anchors.

    Returns text, never a summary or a conclusion. Refuses rather than returning
    the least-bad chunk. See `specs/60-kb_search.md` for the full contract.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("kb_search needs a non-empty query")
    if top_k < 1 or per_doc < 1:
        raise ValueError("top_k and per_doc must be at least 1")
    if max_chars is not None and max_chars < 1:
        raise ValueError("max_chars must be positive or None")

    idx = _index()
    segments = idx["segments"]

    if section is not None and section not in set(idx["doc_sections"].values()):
        raise ValueError(
            f"unknown section {section!r}; known: {sorted(set(idx['doc_sections'].values()))}"
        )
    if document is not None and document not in idx["doc_sections"]:
        raise ValueError(f"unknown document slug {document!r}")

    tokens = tokenize(query)
    qcount = dict(collections.Counter(tokens))
    if not qcount:
        return Refusal(
            reason=f"query {query!r} has no searchable terms once stop words are removed",
            needed=("a query containing at least one content word",),
            source=SOURCE_TOC,
        )

    seg_scores, seg_matched, seg_dropped = _bm25(
        qcount, lambda i: segments[i]["tf"], idx["seg_postings"], idx["seg_avglen"], len(segments)
    )
    card_scores, _, _ = _bm25(
        qcount, lambda s: idx["cards"][s]["tf"], idx["card_postings"],
        idx["card_avglen"], len(idx["cards"]),
    )

    # Coverage denominator. Terms the corpus does not contain at all stay IN the
    # denominator: "we have no such word" is evidence the corpus does not cover
    # the query, and excluding them would let an off-domain question that
    # happens to share one word through the gate at coverage 1.0. Only terms
    # dropped as too common to carry signal leave the denominator.
    unknown = sorted(t for t in qcount if t not in idx["seg_postings"])
    scorable = sorted(t for t in qcount if t not in seg_dropped)
    if not scorable or len(unknown) == len(qcount):
        return Refusal(
            reason=(f"no term in {query!r} occurs in the corpus as a distinguishing term "
                    f"(unknown: {unknown or 'none'}; too common: {sorted(seg_dropped) or 'none'})"),
            needed=tuple(unknown) or ("a more specific query",),
            source=SOURCE_TOC,
        )

    ranked: list[tuple[float, str, int]] = []
    for i, base in seg_scores.items():
        seg = segments[i]
        if section is not None and seg["section"] != section:
            continue
        if document is not None and seg["slug"] != document:
            continue
        if require_equations and not seg["eqs"]:
            continue
        eq_terms = set(tokenize(" ".join(seg["eqs"])))
        n_eq = len(eq_terms & set(tokens))
        total = base + W_DOC * card_scores.get(seg["slug"], 0.0) + W_EQ * n_eq
        ranked.append((total, seg["anchor"], i))
    # Descending score, then anchor ascending: a total order over the corpus, so
    # equal scores resolve identically every run.
    ranked.sort(key=lambda r: (-r[0], r[1]))

    if not ranked:
        where = (f" in section {section!r}" if section else "") + \
                (f" in document {document!r}" if document else "")
        if require_equations:
            return Refusal(
                reason=f"no segment matching {query!r}{where} names an equation in its TOC entry",
                needed=("retry with require_equations=False",),
                source=SOURCE_TOC,
            )
        return Refusal(
            reason=f"no segment{where} matches {query!r}",
            needed=("a broader query, or drop the section/document filter",),
            source=SOURCE_TOC,
        )

    best_total, _, best_i = ranked[0]
    best_cov = len(seg_matched[best_i]) / len(scorable)

    hits: list[dict[str, Any]] = []
    seen: collections.Counter[str] = collections.Counter()
    truncated_any = False
    for total, anchor, i in ranked:
        if len(hits) >= top_k:
            break
        seg = segments[i]
        coverage = len(seg_matched[i]) / len(scorable)
        if coverage < min_coverage or total < min_score:
            continue
        if seen[seg["slug"]] >= per_doc:
            continue
        seen[seg["slug"]] += 1
        path = KB / seg["section"] / f"{seg['slug']}.md"
        # Sliced from the file at return time, with the same read and the same
        # offsets show_segment.py uses. Never joined, stripped or rewrapped.
        text = path.read_text(errors="ignore")[seg["a"]:seg["b"]]
        cut = max_chars is not None and len(text) > max_chars
        if cut:
            text = text[:max_chars]
            truncated_any = True
        hits.append({
            "anchor": anchor,
            "section": seg["section"],
            "document": seg["slug"],
            "segment": seg["i"],
            "chars": [seg["a"], seg["b"]],
            "heading": seg["heading"],
            "text": text,
            "score": round(total, 6),
            "coverage": round(coverage, 4),
            "matched_terms": sorted(seg_matched[i]),
            "equations_present": seg["eqs"],
            "truncated": bool(cut),
        })

    if not hits:
        return Refusal(
            reason=(f"best match for {query!r} scored {best_total:.1f} with coverage "
                    f"{best_cov:.2f}; below min_score {min_score} / min_coverage "
                    f"{min_coverage}. Returning the least-bad chunk is not an option."),
            needed=("a query sharing more terms with the corpus, "
                    "or an explicit lower min_coverage/min_score",),
            source=SOURCE_TOC,
        )

    flags: list[str] = []
    if hits[0]["score"] < WEAK_SCORE:
        flags.append("weak lexical match - verify relevance before citing")
    if truncated_any:
        flags.append("one or more chunks truncated at max_chars - not the full segment")
    if idx.get("cache_note"):
        flags.append(idx["cache_note"])

    return Quantity(
        value=float(len(hits)),
        unit="records",
        method="kb_search bm25+toc v1",
        source="; ".join(h["anchor"] for h in hits),
        inputs={
            "query": query,
            "hits": hits,
            "scorable_terms": scorable,
            "unknown_terms": unknown,
            "common_terms_dropped": sorted(seg_dropped),
        },
        assumptions={
            "ranking": (f"bm25(k1={BM25_K1},b={BM25_B}) over text + {META_WEIGHT}x TOC routing "
                        f"metadata, + {W_DOC}*document-card bm25, + {W_EQ}*equation-name match"),
            "meta_weight": META_WEIGHT,
            "per_doc": per_doc,
            "top_k": top_k,
            "min_coverage": min_coverage,
            "min_score": min_score,
            "section": section,
            "document": document,
            "require_equations": require_equations,
            "tie_break": "descending score, then anchor ascending",
            "verbatim": "chunk text is the exact file slice; no summarisation",
            "corpus": f"{len(idx['doc_sections'])} documents, {len(segments)} segments",
        },
        flags=tuple(flags),
    )


# ---------------------------------------------------------------------------
# #59 kb_lookup
# ---------------------------------------------------------------------------


def _lithology_table() -> dict[str, dict[str, float]]:
    """A view onto petrophysics.MATRIX, not a copy of it.

    The corpus disagrees with itself on matrix density and the catalog resolves
    it once, in petrophysics.py. A second table here would be a second answer to
    the same question.
    """
    return {canonical(k): dict(v) for k, v in petrophysics.MATRIX.items()}


def _fluid_table() -> dict[str, dict[str, float]]:
    return {canonical(k): dict(v) for k, v in petrophysics.FLUID.items()}


def _document_table() -> dict[str, dict[str, Any]]:
    idx = _index()
    cards = _load_jsonl(CARD_META, "slug", "card")
    out: dict[str, dict[str, Any]] = {}
    for slug, section in sorted(idx["doc_sections"].items()):
        card = cards.get(slug, {})
        out[canonical(slug)] = {
            "slug": slug,
            "section": section,
            "covers": card.get("covers", ""),
            "authoritative_for": list(card.get("authoritative_for", [])),
            "not_good_for": list(card.get("not_good_for", [])),
            "scope": card.get("scope", ""),
            "segments": idx["doc_counts"].get(slug, 0),
        }
    return out


def _section_table() -> dict[str, dict[str, Any]]:
    idx = _index()
    by_section: dict[str, list[str]] = collections.defaultdict(list)
    for slug, section in sorted(idx["doc_sections"].items()):
        by_section[section].append(slug)
    return {
        canonical(sec): {
            "section": sec,
            "documents": docs,
            "segments": sum(idx["doc_counts"].get(d, 0) for d in docs),
        }
        for sec, docs in sorted(by_section.items())
    }


# name -> (loader, provenance, owing tool if unpopulated)
TABLES: dict[str, tuple[Callable[[], dict[str, Any]], str, str]] = {
    "lithology": (_lithology_table, SOURCE_MATRIX, ""),
    "fluid": (_fluid_table, SOURCE_MATRIX, ""),
    "document": (_document_table, SOURCE_TOC, ""),
    "section": (_section_table, SOURCE_TOC, ""),
    # Registered empty on purpose. "No such table" and "that table is not built
    # yet" are different facts, and inventing stratigraphy or a county-to-basin
    # map to fill them would be the worst outcome available here.
    "formation": (dict, "", "geolex_lookup [#61] owns formation-to-stratigraphic-position data"),
    "county_basin": (dict, "", "basin_prior_lookup [#62] owns county-to-basin priors"),
}


def known_tables() -> tuple[str, ...]:
    return tuple(sorted(TABLES))


def kb_lookup(table: str, key: str) -> Quantity | Refusal:
    """Exact-key retrieval from a registered reference table.

    Canonicalises whitespace and case and nothing else. A miss is a Refusal
    naming the key and the table; never a default and never a near match. See
    `specs/59-kb_lookup.md`.
    """
    if not isinstance(table, str) or not isinstance(key, str):
        raise TypeError("kb_lookup takes two strings")
    if not key.strip():
        raise ValueError("kb_lookup needs a non-empty key")

    tname = canonical(table)
    if tname not in TABLES:
        return Refusal(
            reason=f"unknown table {table!r}",
            needed=known_tables(),
            source=SOURCE_TOC,
        )

    loader, provenance, owed = TABLES[tname]
    rows = loader()
    ckey = canonical(key)

    if not rows:
        return Refusal(
            reason=f"table {tname!r} is registered but not populated, so {key!r} cannot be resolved",
            needed=(owed,) if owed else ("the table has no data source yet",),
            source=SOURCE_TOC,
        )

    if ckey not in rows:
        keys = sorted(rows)
        needed = tuple(keys) if len(keys) <= 40 else (f"one of {len(keys)} keys in table {tname!r}",)
        return Refusal(
            reason=(f"key {key!r} not found in table {tname!r}; "
                    "this tool matches exactly and will not guess a near neighbour"),
            needed=needed,
            source=provenance or SOURCE_TOC,
        )

    return Quantity(
        value=1.0,
        unit="records",
        method="kb_lookup exact-key v1",
        source=provenance or SOURCE_TOC,
        inputs={"table": tname, "key": key, "canonical_key": ckey, "record": rows[ckey]},
        assumptions={
            "canonicalisation": "strip; collapse internal whitespace; casefold",
            "matching": "exact only - no fuzzy, prefix or synonym match",
            "value_meaning": "count of records returned; the record is in inputs['record']",
        },
    )
