/**
 * Conflict notes — the gatherer flagging what does not add up as it hands off.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/conflict-notes.test.ts
 *
 * This replaced a dedicated Sonnet stage that routed contradictory wells to a
 * three-persona escalation. What had to survive the cut, and is asserted here:
 *
 *   - the deterministic findings still stand and cannot be un-found
 *   - the note-taker sees the facts and no conversation
 *   - a malformed claim is dropped, never repaired into a conflict
 *   - failing is not fatal — the turn answers with what was proved in code
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import {
  conflictView,
  describe as describeState,
  noteConflicts,
  parseConflicts,
  type ConflictView,
} from "@/lib/ai/geology/conflict-notes";
import { CASES, CLEAN, CONFLICTED } from "./fixtures/conflicted-states";

const BLOCK = `CONFLICT
what: Two readings of the perforated interval
side: 4110-4118 per the completion report
side: 4102-4110 per the scout card
resolves: the W-2 for this well`;

/** Returns a fixed reply and records exactly what it was shown. */
function noter(reply = "NONE", seen: string[] = []) {
  return async (view: ConflictView) => {
    seen.push(describeState(view));
    return reply;
  };
}

describe("the note-taker sees the facts and nothing else", () => {
  test("the view carries no prompt and no conversation", async () => {
    const seen: string[] = [];
    await noteConflicts(CONFLICTED[0].build(), noter("NONE", seen));
    const view = conflictView(CONFLICTED[0].build().snapshot());
    for (const forbidden of ["prompt", "question", "messages", "history", "conversation", "chunks"]) {
      assert.ok(!Object.keys(view).includes(forbidden), `the view exposes "${forbidden}"`);
    }
    assert.match(seen[0], /^WELL /);
  });

  test("each labelled conflict's signal is present in the view", () => {
    // The note-taker cannot find what it is not shown. This is the harness's
    // half of recall, independent of the model.
    for (const c of CONFLICTED) {
      const view = conflictView(c.build().snapshot());
      switch (c.name) {
        case "datum disagreement between the LAS and the RRC record":
          assert.equal(view.datum.resolved, false);
          assert.ok(view.alreadyFound.length > 0, "the proved disagreement must reach it");
          break;
        case "Sw reported as a point value with no Rw provenance": {
          const sw = view.computed.find((x) => x.field === "sw");
          assert.ok(sw?.inputs.some((i) => i.name === "rw" && i.source === null));
          break;
        }
        case "an offset pick projected onto a well whose datum is unresolved":
          assert.equal(view.datum.resolved, false);
          assert.ok(view.offsets.some((o) => !o.datumResolved));
          break;
        case "a stated recollection contradicting a documented DST result":
          assert.ok(view.evidence.some((e) => e.kind === "stated"));
          assert.ok(view.evidence.some((e) => e.kind === "documented"));
          break;
        case "a porosity above the physical limit for the stated matrix":
          assert.ok(view.computed.some((x) => x.field === "phiD" && x.value === 0.46));
          break;
        default:
          assert.fail(`unlabelled conflicted case: ${c.name}`);
      }
    }
  });

  test("the rendered state names the well and reference on every depth", () => {
    const text = describeState(conflictView(CONFLICTED[2].build().snapshot()));
    for (const line of text.split("\n").filter((l) => l.includes("PICK"))) {
      assert.match(line, /42-497-30001/);
      assert.match(line, /\b(KB|GL|DF)\b/);
    }
    assert.ok(!text.includes("{"), "the note-taker should not be handed nested JSON");
  });
});

describe("what it returns is verified before anything is recorded", () => {
  test("a noted conflict lands with the gatherer as its origin", async () => {
    const s = CLEAN[0].build();
    const r = await noteConflicts(s, noter(BLOCK));
    assert.equal(r.noted.length, 1);
    const written = s.snapshot().conflicts.at(-1);
    assert.equal(written?.origin.stage, "stage1");
    assert.equal(written?.origin.branch, "gatherer");
    assert.equal(written?.branches.length, 2);
  });

  test("a one-sided claim is dropped, not padded out to two", async () => {
    const s = CLEAN[0].build();
    const r = await noteConflicts(s, noter("CONFLICT\nwhat: porosity seems high\nside: it seems high"));
    assert.equal(r.noted.length, 0);
    assert.equal(s.snapshot().conflicts.length, 0);
  });

  test("a conflict already proved in code is not duplicated", async () => {
    const s = CONFLICTED[0].build();
    const already = s.snapshot().conflicts[0];
    const r = await noteConflicts(
      s,
      noter(`CONFLICT\nwhat:   ${already.description.toUpperCase()} \nside: a\nside: b`)
    );
    assert.equal(r.noted.length, 0);
    assert.equal(s.snapshot().conflicts.length, 1);
  });
});

describe("deterministic findings survive", () => {
  test("a note-taker that finds nothing cannot un-find a proved disagreement", async () => {
    const s = CONFLICTED[0].build();
    assert.equal(s.snapshot().conflicts.length, 1, "Stage 0/1 proved it arithmetically");
    const r = await noteConflicts(s, noter("NONE"));
    assert.equal(r.noted.length, 0);
    assert.equal(r.conflicts.length, 1);
  });

  test("it is shown what was already found, so it need not re-derive it", async () => {
    const seen: string[] = [];
    await noteConflicts(CONFLICTED[0].build(), noter("NONE", seen));
    assert.match(seen[0], /ALREADY-FOUND/);
  });
});

describe("failing is not fatal", () => {
  test("an error leaves the proved findings and records why", async () => {
    // No escalation to fall back on any more: the answer leans on what code
    // proved, and the turn carries on.
    const s = CONFLICTED[0].build();
    const r = await noteConflicts(s, async () => {
      throw new Error("sonnet timed out");
    });
    assert.match(r.error ?? "", /timed out/);
    assert.equal(r.conflicts.length, 1, "the proved conflict is untouched");
    assert.ok(s.snapshot().open.some((o) => o.question.includes("Conflict noting did not complete")));
    assert.ok(s.snapshot().open.every((o) => !o.blocking));
  });

  test("an unparseable reply is an error, not an invented conflict", async () => {
    const s = CLEAN[0].build();
    const r = await noteConflicts(s, noter("I could not determine any conflicts."));
    assert.equal(s.snapshot().conflicts.length, 0);
    assert.equal(r.noted.length, 0);
  });

  test("NONE is a clean, successful answer", async () => {
    const s = CLEAN[0].build();
    const r = await noteConflicts(s, noter("NONE"));
    assert.equal(r.error, null);
    assert.equal(r.noted.length, 0);
  });
});

describe("the labelled set", () => {
  test("is balanced enough to measure against", () => {
    assert.ok(CONFLICTED.length >= 5);
    assert.ok(CLEAN.length >= 3, "without clean cases, always-flag scores perfectly");
    assert.equal(new Set(CASES.map((c) => c.name)).size, CASES.length);
  });

  test("every case builds a valid state object", () => {
    for (const c of CASES) {
      assert.deepEqual(c.build().inconsistencies(), [], `${c.name} builds an inconsistent object`);
    }
  });

  test("a clean well renders without the shouty markers", () => {
    const text = describeState(conflictView(CLEAN[0].build().snapshot()));
    assert.match(text, /DATUM resolved/);
    assert.ok(!text.includes("UNRESOLVED"));
    assert.deepEqual(parseConflicts("NONE"), []);
  });
});
