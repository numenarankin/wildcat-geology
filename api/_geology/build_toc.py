#!/usr/bin/env python3
"""Build the knowledge-base table of contents.

One worker per corpus document, all running concurrently. Each worker segments
its document deterministically, describes every segment with a model call, and
writes that document's slice of the TOC as markdown. Once every document has
landed, the slices are unified into a single TOC.md.

Why segment inside the worker rather than handing a whole document to one call:
a model given 500 KB skims, and there is no way to detect what it skipped.
Here the traversal is code — segment offsets must partition the file exactly,
asserted before any model call — so coverage is arithmetic, not trust. The model
only ever describes a segment it was handed in full.

Usage:
  python3 scripts/build_toc.py                 # build (resumes from cache)
  python3 scripts/build_toc.py --estimate      # cost/time estimate, no API calls
  python3 scripts/build_toc.py --only asquith  # one document
  python3 scripts/build_toc.py --force         # ignore cache, re-describe all
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import hashlib
import re
import time

# The corpus, not the repo: knowledge-base/ and toc/ live under geology-corpus/.
REPO = pathlib.Path(__file__).resolve().parents[2]
ROOT = pathlib.Path(os.environ.get("GEOLOGY_CORPUS_ROOT") or REPO / "geology-corpus")
KB = ROOT / "knowledge-base"
TOC_DIR = ROOT / "toc"
CACHE = TOC_DIR / ".segments.jsonl"
CARDS = TOC_DIR / ".cards.jsonl"
HASHES = TOC_DIR / ".doc-hashes.json"

MODEL = "claude-opus-5"
# Segment description is scoped extraction against text the model was handed in
# full — `low` keeps 400+ calls fast without hurting the judgment involved.
# The document card is a synthesis over one document's entries, so it gets more.
SEGMENT_EFFORT = "low"
CARD_EFFORT = "medium"

# ~3k tokens per segment. Small enough that the model reads rather than skims,
# large enough that an entry keeps the context that makes it routable.
MAX_SEG_CHARS = 12_000
# Mistral's markdown is heading-dense, which fragmented segments to a ~1.9k-char
# median — too small to carry the context that makes an entry routable, and it
# doubled the call count. Merging runts forward to this floor restores a ~6k
# median (well under the cap) and halves the build cost.
MIN_SEG_CHARS = 2500
MAX_CONCURRENCY = 24
# Measured on this corpus: ~15s per segment call at concurrency 24 (Opus 5 thinks by default, and
# `effort: low` shapes depth rather than switching it off). Latency per call is
# what the estimate is built on, so re-measure if the model or effort changes.
SECONDS_PER_CALL = 15

SEGMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "heading": {"type": "string", "description": "Short label for this segment, in the operator's terms."},
        "question_forms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The questions this segment actually answers, phrased as a working geologist or operator would ask them. This is what retrieval matches against.",
        },
        "topics": {"type": "array", "items": {"type": "string"}},
        "entities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Named things that appear verbatim: formations, correlations, authors, curve mnemonics, tool names, basins.",
        },
        "equations_present": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Named equations or methods stated here (e.g. Archie, Turner, Larionov). Empty if none.",
        },
    },
    "required": ["heading", "question_forms", "topics", "entities", "equations_present"],
    "additionalProperties": False,
}

CARD_SCHEMA = {
    "type": "object",
    "properties": {
        "covers": {"type": "string", "description": "One sentence: what this document is."},
        "authoritative_for": {"type": "array", "items": {"type": "string"}},
        "not_good_for": {"type": "array", "items": {"type": "string"}},
        "scope": {"type": "string", "description": "Era, basin, or domain limits worth knowing before trusting it."},
    },
    "required": ["covers", "authoritative_for", "not_good_for", "scope"],
    "additionalProperties": False,
}

SEGMENT_SYSTEM = """\
You index a geology and petroleum-engineering corpus for a well-log analysis agent.

You are given ONE segment of one document. Describe only what is in front of you.
Never infer what neighbouring sections might contain, and never pad an entry to
look complete — an accurate thin entry beats an invented rich one.

The entry you write is used to ROUTE a question to this segment. So the most
important field is `question_forms`: the questions this passage actually answers,
in the words an operator or geologist would use. "Chapter 7: Saturation
Determination" routes nothing; "how do I pick Rw from the SP curve" routes.

`entities` must be strings that appear VERBATIM in the segment — they are checked
against the text. Do not normalise spellings, expand abbreviations, or add a
formation you merely inferred. If the segment is front matter, a reference list,
a figure caption block, or otherwise carries no retrievable content, say so in
`heading` and return empty arrays."""

CARD_SYSTEM = """\
You write the top-level card for one document in a geology corpus index.

You are given the document's title and the per-section entries already extracted
from it. Write the card that decides whether a retrieval agent opens this
document at all. Be honest about limits: `not_good_for` and `scope` are what stop
the agent citing a North Sea study for a Texas well, or a 1922 naming paper for a
modern petrophysical calculation."""


def load_api_key() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    env = REPO / ".env"
    for line in (env.read_text().splitlines() if env.exists() else []):
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("no ANTHROPIC_API_KEY in env or .env")


def corpus_docs() -> list[pathlib.Path]:
    return sorted(p for p in KB.glob("*/*.md")
                  if not p.is_relative_to(KB / "originals")
                  and not p.stem.endswith((".equations", ".visual")))


def segment(text: str) -> list[tuple[int, int]]:
    """Split into (start, end) offsets that exactly partition the text.

    Headings first (which covers the `## Page N` markers in OCR'd documents),
    then a hard character cap for any run of prose with no heading structure.
    """
    cuts = [0]
    for m in re.finditer(r"^#{1,4} .+$", text, re.M):
        if m.start() > cuts[-1]:
            cuts.append(m.start())
    cuts.append(len(text))

    spans: list[tuple[int, int]] = []
    for a, b in zip(cuts, cuts[1:]):
        while b - a > MAX_SEG_CHARS:
            # Prefer a paragraph boundary just under the cap.
            split = text.rfind("\n\n", a, a + MAX_SEG_CHARS)
            if split <= a:
                split = a + MAX_SEG_CHARS
            spans.append((a, split))
            a = split
        if b > a:
            spans.append((a, b))

    # Merge runt segments forward so a lone heading line isn't its own call.
    merged: list[tuple[int, int]] = []
    for s in spans:
        if merged and (s[1] - s[0]) < MIN_SEG_CHARS and (s[1] - merged[-1][0]) <= MAX_SEG_CHARS:
            merged[-1] = (merged[-1][0], s[1])
        else:
            merged.append(s)

    # The coverage guarantee: offsets must tile the file with no gap or overlap.
    assert merged[0][0] == 0, "segmentation does not start at 0"
    assert merged[-1][1] == len(text), "segmentation does not reach end of file"
    for (_, prev_end), (start, _) in zip(merged, merged[1:]):
        assert prev_end == start, f"segmentation gap/overlap at {prev_end}!={start}"
    return merged


def clean(v: str) -> str:
    """Normalise a model-produced field before it reaches the markdown.

    Three failures seen in practice: literal `\\u2014` escapes that survived
    JSON decoding, embedded newlines that break a markdown bullet in half, and
    runs of collapsed whitespace.
    """
    if not isinstance(v, str):
        return v
    if "\\u" in v:
        try:
            v = v.encode().decode("unicode_escape")
        except UnicodeDecodeError:
            pass
    return re.sub(r"\s+", " ", v).strip()


def degenerate(card: dict) -> str | None:
    """Reject a card that is empty or stuck in a repetition loop.

    Two failure shapes seen, and the second is why the tail check alone is not
    enough. `petrowiki-remedial-cementing` decayed into fragments at the end
    ("...yedia entry. y. edia. edia. ia.") — caught by looking at the tail.
    `rrc-g10-tape-user-manual` instead emitted an EMPTY `not_good_for` and spilled
    that content into `scope` as ~20 restatements of the same clause, each
    truncated a character further ("...deliverability... liverability...
    iverability..."). The prose stayed well-formed, so only the repetition shows
    it: a healthy field never repeats a 15-char shingle more than about 3 times.
    """
    covers, scope = card.get("covers", ""), card.get("scope", "")
    if len(covers) < 40:
        return "covers too short"
    if not card.get("authoritative_for"):
        return "no authoritative_for"
    if not card.get("not_good_for"):
        return "no not_good_for"
    for name, field in (("covers", covers), ("scope", scope)):
        tail = field[-120:]
        frags = [f.strip() for f in tail.split(".") if f.strip()]
        if len(frags) >= 4 and sum(1 for f in frags if len(f) <= 6) >= 3:
            return f"{name}: repetition loop (fragment tail)"
        if len(field) >= 200 and repetition(field) >= 5:
            return f"{name}: repetition loop ({repetition(field)}x shingle)"
    return None


def repetition(text: str, width: int = 15) -> int:
    """How many times the most-repeated `width`-char shingle occurs."""
    if len(text) < width * 2:
        return 0
    counts: dict[str, int] = {}
    for i in range(len(text) - width + 1):
        s = text[i:i + width]
        counts[s] = counts.get(s, 0) + 1
    return max(counts.values())


def doc_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def load_hashes() -> dict[str, str]:
    return json.loads(HASHES.read_text()) if HASHES.exists() else {}


def load_cards() -> dict[str, dict]:
    if not CARDS.exists():
        return {}
    return {r["slug"]: r["card"] for r in
            (json.loads(l) for l in CARDS.read_text().splitlines() if l.strip())}


def load_cache() -> dict[str, dict]:
    if not CACHE.exists():
        return {}
    out = {}
    for line in CACHE.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            out[row["key"]] = row["entry"]
    return out


async def describe_segment(client, sem, key, doc_title, body, cache, lock) -> dict:
    if key in cache:
        return cache[key]
    async with sem:
        # Streamed, not because we render tokens, but because the SDK refuses a
        # non-streaming request whose max_tokens could outlast the 10-minute
        # idle-connection window. A few entity-dense segments need the headroom.
        async with client.messages.stream(
            model=MODEL,
            max_tokens=24000,
            system=SEGMENT_SYSTEM,
            output_config={"effort": SEGMENT_EFFORT,
                           "format": {"type": "json_schema", "schema": SEGMENT_SCHEMA}},
            messages=[{"role": "user", "content": f"Document: {doc_title}\n\n---\n\n{body}"}],
        ) as stream:
            resp = await stream.get_final_message()
    if resp.stop_reason == "max_tokens":
        raise RuntimeError(f"segment {key}: response hit max_tokens, entry truncated")
    entry = json.loads(next(b.text for b in resp.content if b.type == "text"))
    async with lock:
        with CACHE.open("a") as fh:
            fh.write(json.dumps({"key": key, "entry": entry}) + "\n")
        cache[key] = entry
    return entry


def verify_entities(entry: dict, body: str) -> dict:
    """Drop entity claims that don't appear in the segment.

    Cheap mechanical check on the one field that is supposed to be verbatim —
    kills hallucinated formations and correlations in code rather than trusting
    the model's word for them.
    """
    low = body.lower()
    kept = [e for e in entry.get("entities", []) if e.lower() in low]
    entry["entities_dropped"] = len(entry.get("entities", [])) - len(kept)
    entry["entities"] = kept
    return entry


async def build_doc(client, sem, doc, cache, lock, hashes, cards) -> dict:
    text = doc.read_text(encoding="utf-8")
    section, slug = doc.parent.name, doc.stem
    spans = segment(text)
    h = doc_hash(text)

    # A document whose text is unchanged must cost nothing. If it DID change,
    # its cached segment entries describe spans that no longer exist, so they
    # are dropped here rather than silently reused against different text.
    if hashes.get(slug) not in (None, h):
        async with lock:
            for i in range(len(spans) + 200):
                cache.pop(f"{section}/{slug}#{i}", None)
            cards.pop(slug, None)

    entries = await asyncio.gather(*[
        describe_segment(client, sem, f"{section}/{slug}#{i}", slug, text[a:b], cache, lock)
        for i, (a, b) in enumerate(spans)
    ])
    entries = [verify_entities(dict(e), text[a:b]) for e, (a, b) in zip(entries, spans)]
    for e in entries:
        e["heading"] = clean(e["heading"])
        for f in ("question_forms", "topics", "entities", "equations_present"):
            e[f] = [clean(x) for x in e[f]]

    # Coverage ledger: one entry per segment or the build is wrong.
    assert len(entries) == len(spans), f"{slug}: {len(entries)} entries for {len(spans)} segments"

    digest = "\n".join(
        f"- {e['heading']}: {'; '.join(e['question_forms'][:4])}" for e in entries if e["question_forms"]
    )
    if not digest.strip():
        raise RuntimeError(
            f"{slug}: no question_forms in any of {len(spans)} segments — "
            "the source text is probably unusable, not the document thin")
    if slug in cards:
        card = cards[slug]
    else:
        card = await _card(client, sem, slug, section, digest, cards, lock)
    return _write_doc(doc, section, slug, spans, entries, card, h, hashes)


async def _card(client, sem, slug, section, digest, cards, lock) -> dict:
    async with sem:
        card_resp = await client.messages.create(
            model=MODEL,
            max_tokens=4000,
            system=CARD_SYSTEM,
            output_config={"effort": CARD_EFFORT,
                           "format": {"type": "json_schema", "schema": CARD_SCHEMA}},
            messages=[{"role": "user", "content": f"Document: {slug}\nSection: {section}\n\nSection entries:\n{digest[:20000]}"}],
        )
    card = json.loads(next(b.text for b in card_resp.content if b.type == "text"))
    card = {k: ([clean(x) for x in v] if isinstance(v, list) else clean(v))
            for k, v in card.items()}
    why = degenerate(card)
    if why:
        raise RuntimeError(f"card for {slug} rejected: {why}")
    async with lock:
        with CARDS.open("a") as fh:
            fh.write(json.dumps({"slug": slug, "card": card}) + "\n")
        cards[slug] = card
    return card


def _write_doc(doc, section, slug, spans, entries, card, h, hashes) -> dict:
    out = TOC_DIR / section / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {slug}", "", f"**Covers:** {card['covers']}", "",
        f"**Authoritative for:** {', '.join(card['authoritative_for']) or '—'}", "",
        f"**Not good for:** {', '.join(card['not_good_for']) or '—'}", "",
        f"**Scope:** {card['scope']}", "",
        f"_{len(spans)} segments._", "", "---", "",
    ]
    for i, (e, (a, b)) in enumerate(zip(entries, spans)):
        if not e["question_forms"] and not e["topics"]:
            continue
        lines.append(f"### {e['heading']}  `{section}/{slug}#{i}` (chars {a}-{b})")
        if e["question_forms"]:
            lines.append("Answers: " + " · ".join(e["question_forms"]))
        if e["entities"]:
            lines.append("Entities: " + ", ".join(e["entities"]))
        if e["equations_present"]:
            lines.append("Equations: " + ", ".join(e["equations_present"]))
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")

    hashes[slug] = h
    return {"section": section, "slug": slug, "card": card, "segments": len(spans),
            "dropped": sum(e["entities_dropped"] for e in entries)}


def compact() -> None:
    """Collapse the append-only caches to one line per key, last write wins.

    Both caches are appended to during a run so a crash keeps what was paid for.
    Left alone they grow on every rebuild — a re-described document leaves its
    old line behind — and any reader that takes the FIRST match for a key gets
    a stale card. Rewriting here makes last-wins a property of the file rather
    than of the reader.
    """
    for path, field in ((CARDS, "slug"), (CACHE, "key")):
        if not path.exists():
            continue
        rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        keep = {r[field]: r for r in rows}
        if len(keep) != len(rows):
            path.write_text("".join(json.dumps(r) + "\n" for r in keep.values()))
            print(f"  {path.name}: {len(rows)} -> {len(keep)} lines")


def write_index(results: list[dict]) -> None:
    """Level 1 of the TOC — the only part that stays resident in the gatherer."""
    by_section: dict[str, list[dict]] = {}
    for r in results:
        by_section.setdefault(r["section"], []).append(r)

    lines = [
        "# Knowledge base — table of contents", "",
        "Level 1. One card per document; this is what the context gatherer holds",
        "resident. Open the per-document file under `toc/<section>/` for its",
        "section-level entries before reading the source document itself.", "",
    ]
    for section in sorted(by_section):
        lines += [f"## {section}", ""]
        for r in sorted(by_section[section], key=lambda x: x["slug"]):
            c = r["card"]
            lines += [
                f"### {r['slug']}",
                f"- **Covers:** {c['covers']}",
                f"- **Authoritative for:** {', '.join(c['authoritative_for']) or '—'}",
                f"- **Not good for:** {', '.join(c['not_good_for']) or '—'}",
                f"- **Scope:** {c['scope']}",
                f"- Detail: [`toc/{r['section']}/{r['slug']}.md`]({r['section']}/{r['slug']}.md) · {r['segments']} segments",
                "",
            ]
    (TOC_DIR / "TOC.md").write_text("\n".join(lines), encoding="utf-8")


def estimate(docs: list[pathlib.Path]) -> None:
    total_chars = seg_count = 0
    rows = []
    for d in docs:
        text = d.read_text(encoding="utf-8")
        spans = segment(text)
        rows.append((d.parent.name + "/" + d.stem, len(text), len(spans)))
        total_chars += len(text)
        seg_count += len(spans)

    in_tok = total_chars / 4 + seg_count * 400 + len(docs) * 2000  # bodies + system + cards
    out_tok = seg_count * 260 + len(docs) * 200
    cost = in_tok / 1e6 * 5.00 + out_tok / 1e6 * 25.00

    for name, chars, segs in sorted(rows, key=lambda r: -r[2])[:8]:
        print(f"  {segs:4}  segments  {chars/1024:8,.0f} KB  {name}")
    print(f"\n  {len(docs)} documents, {seg_count} segments, ~{total_chars/1024:,.0f} KB")
    print(f"  ~{in_tok/1e6:.2f}M input + ~{out_tok/1000:.0f}K output tokens on {MODEL}")
    print(f"  cost ~${cost:.2f}  (Batch API would halve it to ~${cost/2:.2f})")
    waves = -(-(seg_count + len(docs)) // MAX_CONCURRENCY)
    mins = waves * SECONDS_PER_CALL / 60
    print(f"  time  ~{mins:.0f} min at concurrency {MAX_CONCURRENCY} "
          f"({SECONDS_PER_CALL}s/call measured, {waves} waves)")


async def main_async(args) -> int:
    docs = corpus_docs()
    if args.only:
        docs = [d for d in docs if args.only in d.stem]
    if not docs:
        print("no documents matched")
        return 1

    if args.estimate:
        estimate(docs)
        return 0

    TOC_DIR.mkdir(exist_ok=True)
    if args.force and CACHE.exists():
        CACHE.unlink()
    cache, hashes, cards = load_cache(), load_hashes(), load_cards()
    print(f"{len(docs)} documents, {len(cache)} segments / {len(cards)} cards cached")

    # Imported here rather than at module scope: `tools/kb.py` imports this file
    # for `segment()` alone, and inside the deployed app the Anthropic Python SDK
    # is not installed — the app's model calls are made from TypeScript. Building
    # the corpus still needs it, and still gets it, at the one call site.
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=load_api_key())
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    lock = asyncio.Lock()
    started = time.time()

    async def worker(doc):
        try:
            r = await build_doc(client, sem, doc, cache, lock, hashes, cards)
            note = f", {r['dropped']} unverifiable entities dropped" if r["dropped"] else ""
            print(f"  ok   {r['section']}/{r['slug']}: {r['segments']} segments{note}", flush=True)
            return r
        except Exception as exc:  # noqa: BLE001 - one bad doc must not sink the run
            print(f"  FAIL {doc.parent.name}/{doc.stem}: {type(exc).__name__}: {exc}", flush=True)
            return None

    results = [r for r in await asyncio.gather(*[worker(d) for d in docs]) if r]
    HASHES.write_text(json.dumps(hashes, indent=1, sort_keys=True))
    compact()
    if results:
        write_index(results)
    print(f"\n{len(results)}/{len(docs)} documents in {time.time() - started:.0f}s -> toc/TOC.md")
    return 0 if len(results) == len(docs) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--force", action="store_true")
    return asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
