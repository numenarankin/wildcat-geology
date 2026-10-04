#!/usr/bin/env python3
"""Render the corpus's maps and cross-sections, and index what each one shows.

The regional documents are map-heavy in a way the petrophysics half of the corpus
is not: isopach maps, structure-contour maps, net-sand trend maps, correlation
cross-sections. Those *are* the content — "how far does a Strawn channel extend
and in which direction" is a question a plate answers and a paragraph does not.

The decision this implements is that the **image** is the source of truth and the
transcription is only an index. A map described once at ingest and then never
looked at again is a game of telephone: whatever that one pass missed or garbled
is lost silently, forever, and every later answer inherits it. So each figure page
is rendered and kept, and `figure_fetch` hands the actual pixels to the model at
question time. What this script writes is the finding aid — enough to know a sheet
exists and whether it is worth opening.

## What gets rendered

Not every page. Candidates are pages whose text is sparse enough to be mostly
picture, or that carry a figure/plate caption. Each candidate is then shown to the
model, which says whether it is a figure worth keeping; body-text pages,
references and blank plates are dropped rather than indexed.

## Resolution

2576 px on the long edge, the high-resolution tier both Fable 5 and Sonnet 5
read. A contour label that survives at 2576 is unreadable at the 1568 default,
and an unreadable label is the whole reason the pixels are being kept.

Usage:
  python3 scripts/build_figures.py --survey
  python3 scripts/build_figures.py --only allen-1930-breckenridge-oil-field
  python3 scripts/build_figures.py
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
import pathlib
import re
import sys

import pymupdf
from anthropic import AsyncAnthropic

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "api" / "_geology"))
from build_toc import load_api_key  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent / "geology-corpus"
ORIGINALS = ROOT / "knowledge-base" / "originals"
FIGURES = ROOT / "figures"
OUT = ROOT / "tables" / "figures.json"

MODEL = "claude-sonnet-5"
EFFORT = "medium"
LONG_EDGE_PX = 2576
MAX_CONCURRENCY = 10

# The regional half of the corpus. The petrophysics textbooks have figures too,
# but their figures are teaching diagrams that the prose already carries; these
# documents' figures are the data.
SECTIONS = ("06-fort-worth-basin", "07-bend-arch")
# 853 pages of general-purpose mapping textbook, whose plates are worked examples
# from other basins. Not regional evidence.
SKIP = {"tearpock-bischke-applied-subsurface-geological-mapping"}

CAPTION = re.compile(r"^\s*(figure|fig\.|plate|pl\.)\s*\d+", re.I | re.M)
# Below this many characters a page is mostly ink, not prose.
SPARSE_TEXT_CHARS = 900


def candidates(doc: pymupdf.Document) -> list[int]:
    out = []
    for n in range(len(doc)):
        text = doc[n].get_text().strip()
        if len(text) < SPARSE_TEXT_CHARS or CAPTION.search(text):
            out.append(n)
    return out


# The API rejects an image source over 10 MB, and a 2576 px render of a scanned
# plate is routinely larger than that as PNG — the first run died on an 10.9 MB
# page. JPEG at this quality is a tenth the size with no loss a contour label
# cares about, and it keeps the shipped corpus out of gigabyte territory.
JPEG_QUALITY = 88
MAX_IMAGE_BYTES = 9_500_000


def render(page: pymupdf.Page, long_edge: int = LONG_EDGE_PX) -> bytes:
    """The page as a JPEG whose long edge is `long_edge`, under the size cap."""
    rect = page.rect
    edge = long_edge
    while True:
        scale = edge / max(rect.width, rect.height)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
        data = pix.tobytes("jpg", jpg_quality=JPEG_QUALITY)
        if len(data) <= MAX_IMAGE_BYTES or edge <= 1024:
            return data
        edge = int(edge * 0.8)


SCHEMA = {
    "type": "object",
    "properties": {
        "is_figure": {
            "type": "boolean",
            "description": "True only for a map, cross-section, chart, plate, correlation panel, or photograph that carries information. False for body text, a table of numbers, a title page, references, or a blank/near-blank page.",
        },
        "kind": {
            "type": "string",
            "enum": ["structure_map", "isopach_map", "facies_or_trend_map", "index_or_location_map",
                     "cross_section", "stratigraphic_column", "log_panel", "seismic",
                     "chart_or_graph", "photograph", "other"],
            "description": "What kind of figure. Use other only if none fit.",
        },
        "title": {"type": "string", "description": "The figure's own caption or title, transcribed as printed. Empty if it has none."},
        "shows": {"type": "string", "description": "One or two sentences: what a geologist would use this sheet for."},
        "counties": {"type": "array", "items": {"type": "string"}, "description": "Texas counties named or covered. Empty if none are legible."},
        "formations": {"type": "array", "items": {"type": "string"}, "description": "Stratigraphic units named on the sheet."},
        "fields": {"type": "array", "items": {"type": "string"}, "description": "Oil or gas fields named on the sheet."},
        "contour_interval": {"type": "string", "description": "As printed, with units, e.g. '50 ft'. Empty if not a contoured map or not stated."},
        "value_range": {"type": "string", "description": "The range the contours or axes span, as printed. Empty if not applicable."},
        "trend": {"type": "string", "description": "The dominant direction of the mapped feature, if the sheet shows one (e.g. 'thickens northwest'). Empty if none."},
        "cannot_answer": {"type": "string", "description": "One sentence on what this sheet does NOT show, so a reader knows when to stop trusting it."},
    },
    "required": ["is_figure", "kind", "title", "shows", "counties", "formations", "fields",
                 "contour_interval", "value_range", "trend", "cannot_answer"],
    "additionalProperties": False,
}

PROMPT = """This is one page of "{doc}", a geological report on north-central Texas.

Index it for a lookup that helps an operator find maps worth opening. You are \
writing a finding aid, not a replacement — the actual image is kept and will be \
shown to whoever asks, so you do not need to transcribe every contour. What you \
do need to get right is whether this page is a figure at all, what kind, and what \
it covers, because that is what decides whether anyone ever opens it.

Read the legend, the scale bar and the caption before deciding. If a value or a \
county is not legible, leave that field empty rather than guessing — an empty \
field costs a reader nothing and a wrong county sends them to the wrong sheet."""


async def classify(client: AsyncAnthropic, png: bytes, doc_title: str,
                   sem: asyncio.Semaphore) -> dict:
    b64 = base64.standard_b64encode(png).decode()
    async with sem:
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=4000,
            output_config={"effort": EFFORT,
                           "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": PROMPT.format(doc=doc_title)},
            ]}],
        )
    return json.loads(next(b.text for b in resp.content if b.type == "text"))


async def process(client: AsyncAnthropic, pdf: pathlib.Path,
                  sem: asyncio.Semaphore) -> list[dict]:
    slug = f"{pdf.parent.name}/{pdf.stem}"
    doc = pymupdf.open(pdf)
    pages = candidates(doc)
    rendered = {n: render(doc[n]) for n in pages}
    doc.close()

    verdicts = await asyncio.gather(
        *(classify(client, rendered[n], pdf.stem, sem) for n in pages))

    out_dir = FIGURES / pdf.parent.name / pdf.stem
    records: list[dict] = []
    for n, got in zip(pages, verdicts):
        if not got["is_figure"]:
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        rel = f"figures/{pdf.parent.name}/{pdf.stem}/p{n + 1:04d}.jpg"
        (ROOT / rel).write_bytes(rendered[n])
        records.append({
            "figure_id": f"{pdf.stem}#p{n + 1}",
            "doc_slug": slug,
            "page": n + 1,
            "image_path": rel,
            "image_bytes": len(rendered[n]),
            "kind": got["kind"],
            "title": got["title"].strip(),
            "shows": got["shows"].strip(),
            "counties": [c.strip().upper() for c in got["counties"] if c.strip()],
            "formations": [f.strip() for f in got["formations"] if f.strip()],
            "fields": [f.strip() for f in got["fields"] if f.strip()],
            "contour_interval": got["contour_interval"].strip(),
            "value_range": got["value_range"].strip(),
            "trend": got["trend"].strip(),
            "cannot_answer": got["cannot_answer"].strip(),
        })
    print(f"  {slug}: {len(records)} figures kept of {len(pages)} candidates "
          f"({len(rendered)} rendered)")
    return records


def pdfs(only: str | None) -> list[pathlib.Path]:
    out = []
    for section in SECTIONS:
        for pdf in sorted((ORIGINALS / section).glob("*.pdf")):
            if pdf.stem in SKIP or (only and only != pdf.stem):
                continue
            out.append(pdf)
    return out


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--survey", action="store_true")
    args = ap.parse_args()

    targets = pdfs(args.only)
    if args.survey:
        total = 0
        for pdf in targets:
            doc = pymupdf.open(pdf)
            n = len(candidates(doc))
            total += n
            print(f"{pdf.parent.name}/{pdf.stem:<58} {len(doc):>4} pages, {n:>4} candidates")
            doc.close()
        print(f"\n{total} candidate pages, one vision call each on {MODEL}")
        return

    client = AsyncAnthropic(api_key=load_api_key())
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    batches = await asyncio.gather(*(process(client, p, sem) for p in targets))
    records = [r for b in batches for r in b]

    existing = {}
    if args.only and OUT.exists():
        existing = {r["figure_id"]: r for r in json.loads(OUT.read_text())["figures"]}
    existing.update({r["figure_id"]: r for r in records})
    merged = sorted(existing.values(), key=lambda r: (r["doc_slug"], r["page"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "scripts/build_figures.py; pages rendered at "
                  f"{LONG_EDGE_PX}px long edge from knowledge-base/originals",
        "note": "the image is the source of truth; these fields are a finding aid",
        "long_edge_px": LONG_EDGE_PX,
        "figures": merged,
    }, indent=2) + "\n")
    kinds: dict[str, int] = {}
    for r in merged:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"\n{len(merged)} figures -> {OUT}")
    print(f"kinds: {kinds}")


if __name__ == "__main__":
    asyncio.run(main())
