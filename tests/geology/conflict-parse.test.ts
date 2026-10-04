/**
 * The conflict-detector reply parser — line format, no JSON.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/conflict-parse.test.ts
 *
 * JSON was tried twice and failed twice (see conflict-model.ts). The line format
 * has no bracket to balance, no quote to escape, no comma to misplace, so a
 * mangled reply loses at most the block it mangled. These tests are the cases
 * that would have broken JSON.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { conflictView, parseConflicts, describe as renderView } from "@/lib/ai/geology/conflict-notes";
import { CONFLICTED, CLEAN } from "./fixtures/conflicted-states";

const ONE = `CONFLICT
what: the LAS and the W-2 disagree on kelly bushing
side: LAS header says KB 1204 ft
side: RRC W-2 says KB 1218 ft
resolves: the W-2 for this well`;

describe("the line format parses", () => {
  test("a single block", () => {
    const [c] = parseConflicts(ONE);
    assert.equal(c.description, "the LAS and the W-2 disagree on kelly bushing");
    assert.deepEqual(c.branches, ["LAS header says KB 1204 ft", "RRC W-2 says KB 1218 ft"]);
    assert.equal(c.resolvingDocument, "the W-2 for this well");
  });

  test("several blocks", () => {
    assert.equal(parseConflicts(`${ONE}\n\n${ONE}`).length, 2);
  });

  test("NONE, and anything with no blocks", () => {
    for (const empty of ["NONE", "", "No conflicts found.", "   \n\n  "]) {
      assert.deepEqual(parseConflicts(empty), []);
    }
  });

  test("more than two sides", () => {
    assert.equal(parseConflicts(`${ONE}\nside: the driller's tour sheet says 1210 ft`)[0].branches.length, 3);
  });

  test("unknown / none / n/a become null rather than a fake citation", () => {
    for (const value of ["unknown", "NONE", "n/a"]) {
      const text = ONE.replace("the W-2 for this well", value);
      assert.equal(parseConflicts(text)[0].resolvingDocument, null);
    }
  });
});

describe("what JSON would have choked on", () => {
  test("quotes, commas and brackets inside a value", () => {
    const [c] = parseConflicts(`CONFLICT
what: the "Caddo" pick, at 4,090 ft [KB], conflicts with the log
side: pick says 4,090 ft — operator's "usual" datum
side: log character says 4,118 ft
resolves: unknown`);
    assert.match(c.description, /"Caddo"/);
    assert.match(c.branches[0], /4,090 ft/);
  });

  test("a truncated reply keeps the complete blocks", () => {
    const text = `${ONE}\n\nCONFLICT\nwhat: second one that never finish`;
    assert.equal(parseConflicts(text).length, 1);
  });

  test("markdown the model added despite being told not to", () => {
    const text = ["## CONFLICT", "- what: datums disagree here", "- side: one reading", "- side: another reading"].join("\n");
    assert.equal(parseConflicts(text).length, 1);
  });

  test("prose before and after the block", () => {
    assert.equal(parseConflicts(`Let me look at this.\n\n${ONE}\n\nThat is all I found.`).length, 1);
  });

  test("two blocks run together with no CONFLICT header on the second", () => {
    const text = `${ONE}\nwhat: a second contradiction entirely\nside: reading one\nside: reading two`;
    assert.equal(parseConflicts(text).length, 2);
  });

  test("a one-sided block is dropped, not padded", () => {
    assert.deepEqual(parseConflicts("CONFLICT\nwhat: porosity looks high\nside: it looks high"), []);
  });

  test("a block with no `what` is dropped", () => {
    assert.deepEqual(parseConflicts("CONFLICT\nside: one\nside: two"), []);
  });
});

describe("the view renders as lines too", () => {
  test("every depth carries its well and reference", () => {
    const text = renderView(conflictView(CONFLICTED[2].build().snapshot()));
    for (const line of text.split("\n").filter((l: string) => l.includes("PICK"))) {
      assert.match(line, /42-497-30001/, "a pick line must name its own well");
      assert.match(line, /\b(KB|GL|DF)\b/, "a pick line must name its reference");
    }
  });

  test("an input with no provenance is called out, not left blank", () => {
    const text = renderView(conflictView(CONFLICTED[1].build().snapshot()));
    assert.match(text, /rw=0\.05\(NO SOURCE\)/);
  });

  test("evidence keeps its kind and the unresolved datum is shouted", () => {
    const text = renderView(conflictView(CONFLICTED[3].build().snapshot()));
    assert.match(text, /EVIDENCE \[stated\]/);
    assert.match(text, /EVIDENCE \[documented\]/);
    assert.match(renderView(conflictView(CONFLICTED[2].build().snapshot())), /DATUM UNRESOLVED/);
  });

  test("a clean well still renders its facts", () => {
    const text = renderView(conflictView(CLEAN[0].build().snapshot()));
    assert.match(text, /DATUM resolved/);
    assert.match(text, /COMPUTED sw=0\.41/);
    assert.match(text, /from Pickett plot, this well/);
  });

  test("no JSON punctuation is required of the model", () => {
    const text = renderView(conflictView(CLEAN[0].build().snapshot()));
    assert.ok(!text.includes("{"), "the view should not hand the model nested JSON");
  });
});
