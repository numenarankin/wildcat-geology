#!/usr/bin/env python3
"""Resolve a corpus anchor to its text, and find the segments that mention a term.

`show_segment.py` already prints one segment given its anchor; this is the same
addressing used as a library, plus the reverse direction — which anchors mention
a term — because building an anchored lookup table means finding the evidence
before you can cite it.

Nothing here calls a model. Segmentation comes from `build_toc.segment`, so an
anchor resolved here is the same span the TOC named and the same span
`tools.state_checks._token_text` reads when it audits a citation.
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "api" / "_geology"))
from build_toc import segment  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent / "geology-corpus"
KB = ROOT / "knowledge-base"


def documents() -> list[pathlib.Path]:
    return sorted(p for p in KB.glob("*/*.md")
                  if not p.is_relative_to(KB / "originals")
                  and not p.stem.endswith((".equations", ".visual")))


def slug_of(path: pathlib.Path) -> str:
    return f"{path.parent.name}/{path.stem}"


def spans_of(path: pathlib.Path) -> tuple[str, list[tuple[int, int]]]:
    text = path.read_text(errors="ignore")
    return text, segment(text)


def anchor_text(anchor: str) -> str | None:
    """The raw text of `<section>/<slug>#<n>`, or None if it does not resolve."""
    key, _, idx = anchor.partition("#")
    path = KB / f"{key}.md"
    if not path.exists() or not idx.isdigit():
        return None
    text, spans = spans_of(path)
    n = int(idx)
    if not 0 <= n < len(spans):
        return None
    a, b = spans[n]
    return text[a:b]


def normalise(text: str) -> str:
    """Fold whitespace and case so a quote survives OCR line wrapping."""
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_resolves(anchor: str, quote: str) -> bool:
    """Is `quote` verbatim (modulo whitespace/case) inside `anchor`'s segment?"""
    body = anchor_text(anchor)
    if body is None:
        return False
    return normalise(quote) in normalise(body)


def search(term: str, limit: int = 12) -> list[tuple[str, int, str]]:
    """Anchors mentioning `term`, most mentions first: (anchor, hits, excerpt)."""
    pattern = re.compile(re.escape(term), re.I)
    out: list[tuple[str, int, str]] = []
    for path in documents():
        text, spans = spans_of(path)
        for n, (a, b) in enumerate(spans):
            body = text[a:b]
            hits = len(pattern.findall(body))
            if hits:
                m = pattern.search(body)
                lo = max(0, m.start() - 300)
                out.append((f"{slug_of(path)}#{n}", hits, body[lo:m.start() + 700]))
    out.sort(key=lambda r: -r[1])
    return out[:limit]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: corpus_index.py <term> | corpus_index.py --anchor <anchor>")
    if sys.argv[1] == "--anchor":
        body = anchor_text(sys.argv[2])
        print(body if body is not None else f"unresolved: {sys.argv[2]}")
    else:
        for anchor, hits, excerpt in search(sys.argv[1]):
            print(f"\n=== {anchor}  ({hits} hits)\n{excerpt[:900]}")
