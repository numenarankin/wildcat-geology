/**
 * The corpus reader and the two-level TOC.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/corpus.test.ts
 *
 * The property that matters is DRIFT DETECTION. Every offset in the TOC was
 * computed against one version of a document. Rebuild the corpus without
 * rebuilding the index and those offsets still parse, still fall inside the
 * file, and quietly return the wrong passage — a plausible chunk attributed to a
 * real source, which is worse than a gap. `build_toc.py` writes a content hash
 * per document, so the check is exact; these tests prove it fires.
 *
 * Set GEOLOGY_CORPUS_ROOT to the real geology-agent directory to additionally
 * parse the shipped 63-document index.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import {
  Corpus,
  CorpusDriftError,
  CorpusError,
  docHash,
  parseDetail,
  parseRef,
} from "@/lib/ai/geology/corpus";

const CORPUS_ROOT = path.join(import.meta.dirname, "fixtures", "corpus");

function corpus() {
  return new Corpus({
    knowledgeBase: path.join(CORPUS_ROOT, "knowledge-base"),
    toc: path.join(CORPUS_ROOT, "toc"),
  });
}

describe("level 1: the resident index", () => {
  test("every card parses with its four fields and a segment count", async () => {
    const cards = await corpus().documentCards();
    assert.equal(cards.length, 2);

    const gr = cards.find((c) => c.slug === "gr-basics");
    assert.ok(gr);
    assert.equal(gr.section, "01-curve-reading");
    assert.match(gr.covers, /gamma ray/);
    assert.ok(gr.authoritativeFor.length >= 3);
    assert.ok(gr.notGoodFor.length >= 3);
    assert.match(gr.scope, /Introductory/);
    assert.equal(gr.segments, 2);
  });

  test("`not good for` is what stops the wrong document being opened", async () => {
    // The field exists to keep a GR primer from being cited for saturation
    // math. Assert it carries that, since an empty one silently reads as
    // "good for everything".
    const gr = await corpus().card("gr-basics");
    assert.ok(gr?.notGoodFor.some((s) => s.includes("saturation")));
  });
});

describe("level 2: segment entries", () => {
  test("entries carry offsets, question forms, and entities", async () => {
    const entries = await corpus().detail("01-curve-reading", "gr-basics");
    assert.equal(entries.length, 2);
    assert.equal(entries[0].id, "01-curve-reading/gr-basics#0");
    assert.equal(entries[0].start, 0);
    assert.ok(entries[0].answers.some((a) => a.includes("gamma ray curve actually measure")));
    assert.ok(entries[1].entities.includes("Larionov"));
    assert.deepEqual(entries[1].equations, ["linear gamma ray index"]);
  });

  test("a segment with a non-positive span is a hard error", () => {
    const bad = "### Broken  `s/d#0` (chars 500-500)\nAnswers: x\n";
    assert.throws(() => parseDetail(bad, "s", "d"), CorpusError);
  });

  test("a malformed ref is refused rather than half-parsed", () => {
    assert.throws(() => parseRef("gr-basics"), CorpusError);
    assert.throws(() => parseRef("01-curve-reading/gr-basics"), CorpusError);
    assert.deepEqual(parseRef("01-curve-reading/gr-basics#3"), {
      section: "01-curve-reading",
      slug: "gr-basics",
      index: 3,
    });
  });
});

describe("level 3: reading the document", () => {
  test("a read is a verbatim slice at the indexed offsets", async () => {
    const c = corpus();
    const chunk = await c.read("04-coning/coning-basics#0");
    const file = await readFile(
      path.join(CORPUS_ROOT, "knowledge-base", "04-coning", "coning-basics.md"),
      "utf8"
    );
    assert.equal(chunk.text, file.slice(chunk.start, chunk.end));
    assert.match(chunk.text, /Coning is the upward movement of water/);
  });

  test("a segment the TOC does not list cannot be read", async () => {
    await assert.rejects(corpus().read("04-coning/coning-basics#42"), CorpusError);
  });

  test("a document the corpus does not have is a clear error", async () => {
    await assert.rejects(corpus().document("04-coning", "not-here"), /no corpus document/);
  });
});

describe("drift between the index and the corpus", () => {
  test("a document edited after the TOC was built is refused, not silently misread", async () => {
    const root = await mkdtemp(path.join(tmpdir(), "geology-corpus-"));
    const kb = path.join(root, "knowledge-base", "s");
    const toc = path.join(root, "toc", "s");
    await mkdir(kb, { recursive: true });
    await mkdir(toc, { recursive: true });

    const original = "# Doc\n\nThe original text, indexed at these offsets.\n";
    await writeFile(path.join(root, "toc", "TOC.md"), [
      "# Knowledge base — table of contents", "", "## s", "",
      "### d",
      "- **Covers:** a test document",
      "- **Authoritative for:** nothing",
      "- **Not good for:** everything",
      "- **Scope:** a test",
      "- Detail: [`toc/s/d.md`](s/d.md) · 1 segments", "",
    ].join("\n"));
    await writeFile(path.join(toc, "d.md"), [
      "# d", "", "**Covers:** a test document", "",
      "**Authoritative for:** nothing", "", "**Not good for:** everything", "",
      "**Scope:** a test", "", "_1 segments._", "", "---", "",
      `### Whole document  \`s/d#0\` (chars 0-${original.length})`,
      "Answers: what does this say",
      "",
    ].join("\n"));
    await writeFile(
      path.join(root, "toc", ".doc-hashes.json"),
      JSON.stringify({ d: docHash(original) })
    );

    // Index built against `original`; the file now says something else, and is
    // long enough that the offsets remain valid. This is precisely the case
    // that would otherwise return a wrong-but-plausible passage.
    await writeFile(path.join(kb, "d.md"), "# Doc\n\nCompletely different text at the same offsets.\n");

    const drifted = new Corpus({
      knowledgeBase: path.join(root, "knowledge-base"),
      toc: path.join(root, "toc"),
    });
    await assert.rejects(drifted.read("s/d#0"), CorpusDriftError);
    await assert.rejects(drifted.read("s/d#0"), /Re-run build_toc\.py/);
  });

  test("the fixture corpus itself is in step with its index", async () => {
    // If this fails, the fixtures were edited without regenerating the TOC —
    // which is the same mistake the check above exists to catch, made here.
    const c = corpus();
    for (const card of await c.documentCards()) {
      await c.document(card.section, card.slug);
    }
  });

  test("docHash matches build_toc.py's definition", () => {
    // sha256 of the UTF-8 text, first 12 hex characters. Pinned because the
    // ledger this compares against is written by the Python side.
    assert.equal(docHash("hello"), "2cf24dba5fb0");
    assert.equal(docHash("hello").length, 12);
  });
});

describe("the shipped corpus", () => {
  const root = process.env.GEOLOGY_CORPUS_ROOT;
  const available = root !== undefined && existsSync(path.join(root, "toc", "TOC.md"));

  test("the real 63-document index parses", { skip: !available }, async () => {
    const real = new Corpus({
      knowledgeBase: path.join(root!, "knowledge-base"),
      toc: path.join(root!, "toc"),
    });
    const cards = await real.documentCards();
    assert.ok(cards.length >= 60, `only ${cards.length} cards parsed`);

    for (const card of cards) {
      assert.ok(card.covers.length > 0, `${card.slug} has no covers`);
      assert.ok(card.authoritativeFor.length > 0, `${card.slug} has no authoritative_for`);
      assert.ok(card.segments > 0, `${card.slug} claims no segments`);
    }
  });

  /**
   * Ordered and non-overlapping, but NOT gapless.
   *
   * `build_toc.py` tiles the file exactly and asserts it, then omits from the
   * written detail file any segment that produced no question forms and no
   * topics — front matter, reference lists, figure-caption blocks, index pages.
   * Those gaps are deliberate: the model declined to invent questions for text
   * that answers none, which is the behaviour we want. What must hold on the
   * read side is weaker and still worth pinning: entries advance monotonically,
   * never overlap, and never point past the end of the file.
   */
  test("every real document's segments are ordered and in bounds", { skip: !available }, async () => {
    const real = new Corpus({
      knowledgeBase: path.join(root!, "knowledge-base"),
      toc: path.join(root!, "toc"),
    });
    for (const card of await real.documentCards()) {
      const entries = await real.detail(card.section, card.slug).catch(() => null);
      if (!entries) continue; // reported by the orphan test below
      assert.ok(entries.length > 0, `${card.slug}: no segment entries`);
      const text = await real.document(card.section, card.slug);

      for (let i = 0; i < entries.length; i++) {
        const e = entries[i];
        assert.ok(e.end <= text.length, `${card.slug}#${e.index}: ends past the file`);
        if (i > 0) {
          assert.ok(
            e.start >= entries[i - 1].end,
            `${card.slug}: segment ${entries[i - 1].index} overlaps ${e.index}`
          );
        }
      }
      // Reading also verifies the document hash against the TOC's ledger.
      const chunk = await real.read(entries[entries.length - 1].id);
      assert.ok(chunk.text.length > 0, `${card.slug}: last segment is empty`);
    }
  });

  test("every card in the index has a detail file behind it", { skip: !available }, async () => {
    // A card with no level 2 is worse than a missing card: the gatherer reads
    // the card, decides the document is relevant, opens it, and gets nothing —
    // so the corpus looks like it has no answer when it does.
    const real = new Corpus({
      knowledgeBase: path.join(root!, "knowledge-base"),
      toc: path.join(root!, "toc"),
    });
    const orphans: string[] = [];
    for (const card of await real.documentCards()) {
      await real.detail(card.section, card.slug).catch(() => orphans.push(card.slug));
    }
    assert.deepEqual(orphans, [], `cards with no detail file: ${orphans.join(", ")}`);
  });

  test("the indexed fraction of each real document is disclosed, not assumed", { skip: !available }, async () => {
    // The gaps above mean the gatherer cannot reach part of the corpus. That is
    // fine when the gap is front matter and a problem if it is a chapter, so
    // the number is worth knowing rather than trusting. No document should be
    // mostly unreachable.
    const real = new Corpus({
      knowledgeBase: path.join(root!, "knowledge-base"),
      toc: path.join(root!, "toc"),
    });
    const thin: string[] = [];
    for (const card of await real.documentCards()) {
      const entries = await real.detail(card.section, card.slug).catch(() => null);
      if (!entries) continue; // reported by the orphan test above
      const text = await real.document(card.section, card.slug);
      const indexed = entries.reduce((sum, e) => sum + (e.end - e.start), 0);
      const fraction = indexed / text.length;
      if (fraction < 0.5) thin.push(`${card.slug} ${(fraction * 100).toFixed(0)}%`);
    }
    assert.deepEqual(thin, [], `documents less than half indexed: ${thin.join(", ")}`);
  });
});
