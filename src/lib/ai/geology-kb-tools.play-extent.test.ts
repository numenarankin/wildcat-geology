import { describe, expect, test } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";

import { geologyPlayExtentTool } from "./geology-kb-tools";
import { COUNTY_NAMES } from "../scout/counties";

/**
 * `geology_play_extent`, executed against the corpus that ships.
 *
 * The oracle is never the extractor. Every claim below is first read out of the
 * corpus files with `fs`, the sentence verbatim at a path this test names,
 * and only then compared with what the tool returned. A test that asserted
 * "Bend Arch returns Brown County" without proving Brown County is in the text
 * would pass just as happily against an extractor that had learned to say
 * "Brown", and would keep passing after the corpus changed underneath it.
 *
 * Each oracle sentence is asserted to still be on disk before it is used. A
 * corpus that no longer contains the trap or the figure fails HERE, loudly,
 * rather than quietly turning the assertion below it into a tautology.
 */

const ROOT = path.resolve(__dirname, "../../../geology-corpus");
const ctx = { toolCallId: "test", messages: [] } as never;

type ToolName = keyof ReturnType<typeof geologyPlayExtentTool>;

const extent = async (play: unknown): Promise<Record<string, unknown>> => {
  const t = geologyPlayExtentTool()["geology_play_extent" as ToolName] as unknown as {
    execute: (a: unknown, c: unknown) => Promise<unknown>;
  };
  return (await t.execute({ play }, ctx)) as Record<string, unknown>;
};

/** Read a corpus document the way a reader would, by its path. */
function source(doc: string): string {
  return readFileSync(path.join(ROOT, "knowledge-base", `${doc}.md`), "utf8");
}

/** A document by slug alone, wherever the corpus files it. */
function findDocument(slug: string): string | null {
  const base = path.join(ROOT, "knowledge-base");
  for (const entry of readdirSync(base, { withFileTypes: true })) {
    const file = entry.isDirectory()
      ? path.join(base, entry.name, `${slug}.md`)
      : path.join(base, `${slug}.md`);
    try {
      return readFileSync(file, "utf8");
    } catch {
      continue;
    }
  }
  return null;
}

/** Assert the oracle sentence is really there, then hand it back. */
function verbatim(doc: string, sentence: string): string {
  expect(
    source(doc).includes(sentence),
    `the oracle "${sentence}" is no longer in ${doc}; this test's premise changed`
  ).toBe(true);
  return sentence;
}

interface CountyRow {
  county: string;
  county_no: string | null;
  passages: number;
  with_play: number;
}

const countiesOf = (r: Record<string, unknown>): CountyRow[] => r.counties as CountyRow[];
const named = (r: Record<string, unknown>): string[] => countiesOf(r).map((c) => c.county);

interface Depths {
  count: number;
  min?: number;
  median?: number;
  max?: number;
  filter: string;
  quotes?: string[];
}

const depthsOf = (r: Record<string, unknown>): Depths => r.depths_ft as Depths;

describe("registration", () => {
  // Orion's catalog entry for it is Wildcat's to test.
  test("the description says to run it BEFORE choosing a radius", () => {
    const t = geologyPlayExtentTool().geology_play_extent as unknown as { description?: string };
    // If it does not say so, the tool exists and never gets called at the only
    // moment it is useful.
    expect(t.description).toMatch(/before/i);
  });
});

describe("the privacy contract", () => {
  /*
   * Same contract the three navigation tools carry: the curated collection is
   * the asset, so no call may return the library's shape. This tool reads the
   * whole corpus on every call, which makes it the most attractive route to an
   * inventory in the file, hence the sweep below rather than a spot check.
   */
  test("a subjectless call refuses, and refuses with something to do instead", async () => {
    for (const play of ["", "   ", "a", "of"]) {
      const r = await extent(play);
      expect(r.ok, `"${play}" was answered`).toBe(false);
      expect(r.counties).toBeUndefined();
      expect(r.passages).toBeUndefined();
      expect(String(r.error)).toMatch(/name the play/i);
      // A bare refusal reads as a missing library, and the model then answers
      // the subsurface question out of its own head.
      expect(String(r.error)).toMatch(/Bend Arch/);
    }
  });

  test("no result names a document, a section or a file path", async () => {
    // Oracle: the level-1 TOC prints every section as `## ` and every document
    // as `### `. Parsed here from the file, so the check covers the real
    // collection rather than a list this test remembers.
    const toc = readFileSync(path.join(ROOT, "toc", "TOC.md"), "utf8").split("\n");
    const sections = toc.filter((l) => l.startsWith("## ")).map((l) => l.slice(3).trim());
    const slugs = toc.filter((l) => l.startsWith("### ")).map((l) => l.slice(4).trim());
    expect(sections.length).toBeGreaterThan(10);
    expect(slugs.length).toBeGreaterThan(50);

    for (const play of ["Bend Arch", "Caddo", "Strawn", "Marble Falls"]) {
      const wire = JSON.stringify(await extent(play));
      for (const id of [...sections, ...slugs]) {
        expect(wire.includes(id), `${play} leaked the document id "${id}"`).toBe(false);
      }
      for (const trace of ["geology-corpus", "knowledge-base", ".md", "/toc/"]) {
        expect(wire.includes(trace), `${play} leaked "${trace}"`).toBe(false);
      }
      // Nor the browsable shape the other tools refuse to hand over.
      const r = await extent(play);
      expect(r.documents).toBeUndefined();
      expect(r.sections).toBeUndefined();
      expect(r.segments).toBeUndefined();
      // And it says what it is, next to the thing it governs.
      expect(String(r.private)).toMatch(/INTERNAL/);
    }
  });

  test("a document it could not read is reported, never silently dropped", async () => {
    // Oracle: `build_toc.py` records sha256[:12] of each document's UTF-8 text
    // in `.doc-hashes.json`. Re-hashed here, independently of `Corpus`, a
    // mismatch means that document cannot be read and its evidence is missing
    // from the answer. Whether the shipped corpus drifts is not this test's
    // business; that the tool tells the truth about it either way IS.
    const hashes = JSON.parse(
      readFileSync(path.join(ROOT, "toc", ".doc-hashes.json"), "utf8")
    ) as Record<string, string>;
    const drifted = Object.entries(hashes).filter(([slug, expected]) => {
      const file = findDocument(slug);
      return file !== null && createHash("sha256").update(file, "utf8").digest("hex").slice(0, 12) !== expected;
    });

    const r = await extent("Bend Arch");
    if (drifted.length > 0) {
      expect(
        String(r.warning),
        `${drifted.length} document(s) drifted but the answer claims to be complete`
      ).toMatch(/could not be read/i);
      // The shortfall must not name what was lost, or the warning becomes the
      // inventory the refusal above exists to prevent.
      for (const [slug] of drifted) expect(String(r.warning)).not.toContain(slug);
    } else {
      expect(r.warning).toBeUndefined();
    }
  });

  test("the library not being on disk is an answer, not a throw", async () => {
    const real = process.env.GEOLOGY_CORPUS_ROOT;
    process.env.GEOLOGY_CORPUS_ROOT = path.join(ROOT, "..", "no-such-corpus");
    try {
      const r = await extent("Bend Arch");
      expect(r.ok).toBe(false);
      expect(String(r.error)).toContain("not present in this environment");
    } finally {
      if (real === undefined) delete process.env.GEOLOGY_CORPUS_ROOT;
      else process.env.GEOLOGY_CORPUS_ROOT = real;
    }
  });
});

describe("where the Bend Arch is, per the corpus", () => {
  /*
   * The independently known truth: two documents in the collection state their
   * ground in their own titles. Neither title is something the extractor could
   * have invented, and neither county is guessable from the play's name.
   */
  test("returns the counties the corpus actually discusses", async () => {
    verbatim(
      "07-bend-arch/eargle-1960-usgs-pp-315d",
      "Stratigraphy of Pennsylvanian and Lower Permian Rocks in Brown and Coleman Counties, Texas"
    );
    verbatim(
      "07-bend-arch/usgs-ofr-2007-1313-young-county",
      "coaly shale samples, Young County, north-central Texas"
    );

    const r = await extent("Bend Arch");
    expect(r.ok).toBe(true);
    for (const county of ["Brown", "Coleman", "Young"]) {
      expect(named(r), `${county} County is in the corpus but not in the result`).toContain(
        county
      );
    }
  });

  test("each county carries the RRC number a screen is run on", async () => {
    const r = await extent("Bend Arch");
    const rows = countiesOf(r);
    // Oracle: the RRC oil-and-gas county codes. Brown is 049, Coleman 083,
    // Young 503, three-digit and zero-padded, as every rrc query binds them.
    const expected: Record<string, string> = {
      Brown: "049",
      Coleman: "083",
      Young: "503",
    };
    for (const [county, no] of Object.entries(expected)) {
      expect(rows.find((c) => c.county === county)?.county_no).toBe(no);
    }
  });

  test("every county returned is a real Texas county", async () => {
    const gazetteer = new Set(Object.values(COUNTY_NAMES));
    for (const play of ["Bend Arch", "Caddo", "Strawn", "Marble Falls"]) {
      for (const row of countiesOf(await extent(play))) {
        expect(gazetteer.has(row.county), `${row.county} is not a Texas county`).toBe(true);
        expect(row.county_no).toMatch(/^\d{3}$/);
        expect(row.passages).toBeGreaterThan(0);
        expect(row.with_play).toBeLessThanOrEqual(row.passages);
      }
    }
  });

  test("a county named in a neighbouring clause is NOT evidence", async () => {
    // The trap, verbatim in the corpus: a plate credit. Anything that walks
    // backwards through the comma reads it as evidence for Camp County, which
    // is in east Texas, 200 miles off the Bend Arch. A singular "County" is
    // preceded by exactly one county name and that is the whole defence.
    verbatim(
      "06-fort-worth-basin/allen-1930-breckenridge-oil-field",
      "Information from the Texas Company, Parks Camp, Stephens County."
    );
    const r = await extent("Bend Arch");
    expect(named(r)).toContain("Stephens");
    expect(named(r)).not.toContain("Camp");
  });

  test("counties are ranked by the evidence, strongest first", async () => {
    const rows = countiesOf(await extent("Caddo"));
    // A county named in the same passage as the play outranks one named only
    // in a document about it. Unranked, the list is alphabetical noise and the
    // model screens the first three it reads.
    const byPlay = rows.map((c) => c.with_play);
    expect([...byPlay].sort((a, b) => b - a)).toEqual(byPlay);
    expect(byPlay[0]).toBeGreaterThan(0);
  });
});

describe("how deep, per the corpus", () => {
  test("the depth band comes from figures the corpus really quotes", async () => {
    verbatim(
      "06-fort-worth-basin/hardage-3d-seismic-carbonate-karst-collapse",
      "The Upper Caddo was perforated from 4,886 to 4,902 ft"
    );
    verbatim(
      "06-fort-worth-basin/hardage-3d-seismic-carbonate-karst-collapse",
      "drilled through the basal Bend Conglomerate to a total depth of 5,830 ft"
    );

    const d = depthsOf(await extent("Caddo"));
    expect(d.count).toBeGreaterThan(1);
    // A perforated interval quoted as a range must contribute BOTH ends, or a
    // band fitted from these figures is narrower than the text supports.
    const quotes = (d.quotes ?? []).join("\n");
    expect(quotes).toContain("4,886");
    expect(quotes).toContain("4,902");
    // The band has to reach the deepest figure the corpus states.
    expect(d.max).toBeGreaterThanOrEqual(5830);
    expect(d.min).toBeGreaterThanOrEqual(300);
    expect(d.max).toBeLessThanOrEqual(25_000);
    expect(d.median).toBeGreaterThanOrEqual(d.min as number);
    expect(d.median).toBeLessThanOrEqual(d.max as number);
    // A distribution, not a number. One figure reported alone reads as the
    // answer; count is what says how much text is behind it.
    expect(d.filter).toMatch(/ft/);
    expect(d.quotes?.length).toBeGreaterThan(1);
    for (const q of d.quotes ?? []) expect(q).toMatch(/^[\d,]+ ft: /);
  });

  test("a thickness is not a depth", async () => {
    // The trap, verbatim: a figure in a Caddo passage, carrying a foot unit,
    // that is a formation THICKNESS. An extractor that took every number with
    // "ft" after it reports a Caddo at 1,200 ft, and 1,200 ft is where a
    // screen would then go looking.
    verbatim(
      "06-fort-worth-basin/alhakeem-2013-boonsville-3d-seismic-thesis",
      "the thickness of 1200 ft from the top of the Caddo"
    );
    // Hand-computed oracle: the shallowest DEPTH the corpus states for the
    // Caddo is a well drilling "in a gas sand at 1,400 feet". So a band whose
    // floor reaches 1,200 has swallowed the thickness above.
    verbatim(
      "06-fort-worth-basin/allen-1930-breckenridge-oil-field",
      "Caddo Sheppard No.3 is drilling in a gas sand at 1,400 feet"
    );

    const caddo = depthsOf(await extent("Caddo"));
    expect(caddo.min).toBe(1400);

    // And nothing quoted as a depth may be a sentence about thickness.
    for (const play of ["Caddo", "Bend Arch", "Strawn"]) {
      const quotes = (depthsOf(await extent(play)).quotes ?? []).join("\n");
      expect(quotes, `a thickness was quoted as a depth for ${play}`).not.toMatch(/thick/i);
    }
  });

  test("no depth figure is a stated absence, never an empty band", async () => {
    // "min 0, max 0" would be read as a depth. The play a paper discusses
    // structurally, without ever quoting a drilling depth, is the common case.
    const d = depthsOf(await extent("Zzzqx Formation"));
    expect(d.count).toBe(0);
    expect(d.min).toBeUndefined();
    expect(d.max).toBeUndefined();
    expect(String((d as unknown as { note: string }).note)).toMatch(/no depth figure/i);
  });
});

describe("the evidence is readable, and says what it is", () => {
  test("every excerpt contains the play term, so the model can check the extraction", async () => {
    for (const play of ["Bend Arch", "Caddo", "Marble Falls"]) {
      const r = await extent(play);
      const excerpts = r.passages as string[];
      expect(excerpts.length).toBeGreaterThan(0);
      expect(excerpts.length).toBeLessThanOrEqual(5);
      const term = new RegExp(play.replace(/\s+/g, "\\s+"), "i");
      for (const e of excerpts) {
        expect(e, `an excerpt for ${play} does not contain the play term`).toMatch(term);
        // Short enough to read, long enough to carry its own context.
        expect(e.length).toBeLessThan(600);
      }
    }
  });

  test("the note says this is the literature, not a well population", async () => {
    const r = await extent("Bend Arch");
    const note = String(r.note);
    expect(note).toMatch(/literature/i);
    expect(note).toMatch(/not a measured well population/i);
    // The instruction that stops it being screened on directly.
    expect(note).toMatch(/confirm|record/i);
  });

  test("a play the corpus does not discuss returns nothing, and says so plainly", async () => {
    const r = await extent("Zzzqx Formation");
    expect(r.ok).toBe(true);
    expect(countiesOf(r)).toEqual([]);
    expect(r.passages).toEqual([]);
    expect(r.matched_passages).toBe(0);
  });

  test("the same question twice gives the same answer", async () => {
    // Deterministic extraction: no model call, no sampling, no cache that can
    // hand back a different extent to the second caller in a conversation.
    const [a, b] = [await extent("Caddo"), await extent("Caddo")];
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });
});
