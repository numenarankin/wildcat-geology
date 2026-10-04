import { describe, expect, test } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";

import { geologyKbTools } from "../geology-kb-tools";

/**
 * Orion's reference-library tools, executed against the corpus that ships.
 *
 * The oracle for a read is NOT the Corpus class that performed it. The TOC
 * detail file prints, per segment, the exact character range it occupies in the
 * source document; this test parses that line itself, slices the source file
 * with `fs`, and compares byte for byte. So a read is checked against the
 * published offsets rather than against the code that consumed them — which is
 * the failure that matters here. Offsets that are merely self-consistent still
 * return a passage, just the wrong one, and a plausible wrong passage is worse
 * than an error.
 */

const ROOT = path.resolve(__dirname, "../../../../geology-corpus");
const ctx = { toolCallId: "test", messages: [] } as never;

type ToolName = keyof ReturnType<typeof geologyKbTools>;

const call = async (name: string, args: unknown): Promise<Record<string, unknown>> => {
  const t = geologyKbTools()[name as ToolName] as unknown as {
    execute: (a: unknown, c: unknown) => Promise<unknown>;
  };
  return (await t.execute(args, ctx)) as Record<string, unknown>;
};

/** A small, stable document: two segments, and it is not going to be re-cut. */
const DOC = "01-curve-reading/aapg-density-neutron-log-porosity";

/** Parse the TOC detail the way a reader would, not the way `Corpus` does. */
function publishedSegments(doc: string) {
  const text = readFileSync(path.join(ROOT, "toc", `${doc}.md`), "utf8");
  const re = /^### (.+?)\s+`([^`]+)`\s+\(chars (\d+)-(\d+)\)$/gm;
  const out: { heading: string; ref: string; start: number; end: number }[] = [];
  for (const m of text.matchAll(re)) {
    out.push({ heading: m[1].trim(), ref: m[2], start: Number(m[3]), end: Number(m[4]) });
  }
  // A regex that stopped matching would make every comparison below vacuously
  // true — an empty oracle agrees with anything.
  if (out.length === 0) throw new Error(`the oracle parsed no segments out of ${doc}`);
  return out;
}

// Orion's registration of these tools (its catalog, its system prompt) is
// Wildcat's to test; this suite owns what the tools do.
describe("registry", () => {
  test("exactly the three library tools", () => {
    expect(Object.keys(geologyKbTools()).sort()).toEqual([
      "geology_kb_index",
      "geology_kb_read",
      "geology_kb_segments",
    ]);
  });
});

describe("navigating the index", () => {
  /*
   * These two used to assert the OPPOSITE: that an argument-less call returned
   * one card per document in the shipped corpus, and that a filter left the
   * full section list intact. That was the leak. The curated collection is the
   * asset here, and either result put its whole shape into the model's context
   * in a single call, from which a user persistent enough gets it back out.
   *
   * The library is a lookup now, not a catalogue. See `LIBRARY_PRIVACY`.
   */
  test("refuses to be browsed, because the inventory is the asset", async () => {
    const r = await call("geology_kb_index", {});
    expect(r.ok).toBe(false);
    expect(r.documents).toBeUndefined();
    expect(String(r.error)).toMatch(/not browsable/i);
    // And it has to say what to do instead, or the model treats a refusal as a
    // missing library and answers the subsurface question from memory.
    expect(String(r.error)).toMatch(/matching/);
  });

  test("never returns the section list, which is the collection's skeleton", async () => {
    // The sections ARE the curation: knowing the library is filed under
    // curve-reading / saturation / decline-curves is most of what someone
    // rebuilding it needs, and it costs one call to learn.
    for (const args of [
      { matching: "waxman-smits" },
      { section: "01-curve-reading" },
      { matching: "e" },
    ]) {
      const r = await call("geology_kb_index", args);
      expect(r.sections, `sections leaked for ${JSON.stringify(args)}`).toBeUndefined();
    }
  });

  test("caps results, so a match-everything filter is not an inventory", async () => {
    // Oracle: the level-1 TOC prints one `### ` card per document, and there are
    // far more of them than the cap. Counted from the file, not from the parser
    // under test.
    const toc = readFileSync(path.join(ROOT, "toc", "TOC.md"), "utf8");
    const cards = toc.split("\n").filter((l) => l.startsWith("### ")).length;
    expect(cards).toBeGreaterThan(12);

    // A single letter matches nearly every card. Without the cap this is the
    // unfiltered listing with one extra character typed.
    const r = await call("geology_kb_index", { matching: "e" });
    expect(r.ok).toBe(true);
    const docs = r.documents as unknown[];
    expect(docs.length).toBeLessThanOrEqual(12);
    expect(docs.length).toBeLessThan(cards);
    // And it must not report the total it withheld: "12 of 90" hands over the
    // size of the collection, which is the second thing an enumerator wants.
    expect(JSON.stringify(r)).not.toContain(String(cards));
  });

  test("still tells the model this is internal, next to the thing it governs", async () => {
    // A rule two thousand tokens away in the system prompt is one the model
    // applies unevenly. This rides on the result itself.
    const r = await call("geology_kb_index", { matching: "waxman-smits" });
    expect(String(r.private)).toMatch(/INTERNAL/);
  });

  test("a section filter returns the full card, because that is what picking needs", async () => {
    const r = await call("geology_kb_index", { section: "01-curve-reading" });
    const docs = r.documents as Record<string, unknown>[];
    expect(docs.length).toBeGreaterThan(0);
    for (const d of docs) {
      expect(String(d.document).startsWith("01-curve-reading/")).toBe(true);
      // The whole point of the card: what it is FOR and what it is NOT for.
      expect(Array.isArray(d.authoritativeFor)).toBe(true);
      expect(Array.isArray(d.notGoodFor)).toBe(true);
      expect(typeof d.scope).toBe("string");
    }
  });

  test("`matching` still finds the document a real question needs", async () => {
    // The narrowing must not have cost the capability. A model working on
    // shaly-sand saturation has to reach the document that is authoritative for
    // it, or the whole library may as well not be there.
    const r = await call("geology_kb_index", { matching: "waxman-smits" });
    expect(r.ok).toBe(true);
    const docs = r.documents as Record<string, unknown>[];
    expect(docs.length).toBeGreaterThan(0);
    expect(docs.length).toBeLessThanOrEqual(12);
  });
});

describe("choosing a segment", () => {
  test("returns the published refs for a document", async () => {
    const published = publishedSegments(DOC);
    const r = await call("geology_kb_segments", { document: DOC });

    expect(r.ok).toBe(true);
    expect(r.total).toBe(published.length);
    const refs = (r.segments as Record<string, unknown>[]).map((s) => s.ref);
    expect(refs).toEqual(published.map((p) => p.ref));
  });

  test("every segment carries the questions it answers — the field selection runs on", async () => {
    const r = await call("geology_kb_segments", { document: DOC });
    for (const s of r.segments as Record<string, unknown>[]) {
      expect(Array.isArray(s.answers)).toBe(true);
      expect((s.answers as string[]).length).toBeGreaterThan(0);
    }
  });

  test("`matching` filters on the answers, not just the heading", async () => {
    // "crossover" is in segment 1's heading AND in segment 0's answered
    // questions, so a heading-only filter would return one and this returns two.
    const r = await call("geology_kb_segments", { document: DOC, matching: "crossover" });
    expect(r.matched).toBe(2);
  });

  test("a long document is capped, and says so with the real count", async () => {
    const doc = "00-reference/ahmed-reservoir-engineering-handbook";
    const r = await call("geology_kb_segments", { document: doc });
    expect(r.truncated).toBe(true);
    expect((r.segments as unknown[]).length).toBe(40);
    // The count is the honest part: a silent cut reads as "that is all there is".
    expect(r.total).toBe(publishedSegments(doc).length);
    expect(String(r.note)).toContain(String(r.total));
  });

  test("a malformed document id is an answer, not a throw", async () => {
    const r = await call("geology_kb_segments", { document: "not-a-document" });
    expect(r.ok).toBe(false);
    expect(String(r.error)).toContain("section/slug");
  });
});

describe("reading a segment", () => {
  test("the text is the published byte range of the source document, exactly", async () => {
    const [first] = publishedSegments(DOC);
    const source = readFileSync(path.join(ROOT, "knowledge-base", `${DOC}.md`), "utf8");
    const expected = source.slice(first.start, first.end);

    const r = await call("geology_kb_read", { ref: first.ref });

    expect(r.ok).toBe(true);
    expect(r.heading).toBe(first.heading);
    expect(r.text).toBe(expected);
    // Verbatim means verbatim: no trimming, no reflow, no summary.
    expect((r.text as string).length).toBe(first.end - first.start);
  });

  test("the document's scope travels with the passage", async () => {
    // Without it a 1983 chartbook and a 2004 textbook read as equally current,
    // and the model has no way to tell which one it is holding.
    const [first] = publishedSegments(DOC);
    const r = await call("geology_kb_read", { ref: first.ref });
    expect(typeof r.scope).toBe("string");
    expect((r.scope as string).length).toBeGreaterThan(0);
    expect(Array.isArray(r.notGoodFor)).toBe(true);
  });

  test("a ref that does not exist refuses instead of returning the wrong passage", async () => {
    const r = await call("geology_kb_read", { ref: `${DOC}#999` });
    expect(r.ok).toBe(false);
    expect(String(r.error)).toContain("999");
  });

  test("a malformed ref refuses too", async () => {
    const r = await call("geology_kb_read", { ref: "garbage" });
    expect(r.ok).toBe(false);
  });
});

describe("no library on disk", () => {
  test("every tool refuses in words the model can pass on, and none throws", async () => {
    const real = process.env.GEOLOGY_CORPUS_ROOT;
    process.env.GEOLOGY_CORPUS_ROOT = path.join(ROOT, "..", "no-such-corpus");
    try {
      for (const [name, args] of [
        ["geology_kb_index", {}],
        ["geology_kb_segments", { document: DOC }],
        ["geology_kb_read", { ref: `${DOC}#0` }],
      ] as const) {
        const r = await call(name, args);
        expect(r.ok, name).toBe(false);
        expect(String(r.error)).toContain("not present in this environment");
      }
    } finally {
      if (real === undefined) delete process.env.GEOLOGY_CORPUS_ROOT;
      else process.env.GEOLOGY_CORPUS_ROOT = real;
    }
  });
});
