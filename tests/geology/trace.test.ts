/**
 * The verification side channel.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/trace.test.ts
 *
 * The answer is silent about its own machinery by design, so this is the only
 * thing that can say whether the tools and the corpus were used. Its job is to
 * be honest — in both directions. Overstating (calling a never-registered branch
 * a failure) and understating (missing Fable's own calls) are both ways of
 * making the console lie about a turn.
 */
import assert from "node:assert/strict";
import { describe, test } from "node:test";
import { geologyTrace, traceSummary } from "@/lib/ai/geology/trace";
import { createZoneEvaluation } from "@/lib/ai/geology/state";
import type { GeologyEntryResult } from "@/lib/ai/geology/entry";

function store() {
  return createZoneEvaluation({
    api: "42-429-36825", name: "SKY HEIGHTEN # 1", operator: null, county: null, district: null,
  });
}

function wellResult(s: ReturnType<typeof store>): GeologyEntryResult {
  return {
    kind: "well",
    subject: { fileId: "f", via: "page" },
    stream: null as never,
    // The trace reads the evaluation, never the meter; zeros keep it out of the way.
    gathererUsage: { inputTokens: 0, outputTokens: 0, cacheReadTokens: 0, calls: 0 },
    turn: {
      store: s,
      state: s.snapshot(),
      result: null as never,
      brief: "",
      timing: { stage0: 90, stage1: 1000, total: 1100 },
      trace: {
        cacheHit: false, missReason: "cold", failedBranches: [],
        subQuestions: ["what does the log say"], chunks: 2, gatherErrors: [],
        sources: ["01-curve-reading/asquith#3", "01-curve-reading/asquith#3", "04-coning/basics#1"],
        implausible: 0, missingRequirements: [], conflicts: 0, conflictNoteError: null,
      },
    },
  } as GeologyEntryResult;
}

describe("what the trace says happened", () => {
  test("a branch with no tool behind it is 'unavailable', not a failure", () => {
    // Six of these are recorded on every well turn — contract shapes whose
    // adapters are not written. Counted as failures the console reads as a
    // broken system on a turn that went exactly as designed.
    const s = store();
    s.addToolCall({ stage: "stage0" }, {
      tool: "curve_suite", args: {}, method: "(call failed)", ok: false, output: null,
      refused: null, requestedBy: "harness",
      error: 'no tool "curve_suite" available to harness',
    });
    s.addToolCall({ stage: "stage0" }, {
      tool: "las_header", args: {}, method: "LAS 2.0 section parse", ok: true,
      output: {}, refused: null, requestedBy: "harness", error: null,
    });
    s.addToolCall({ stage: "stage1" }, {
      tool: "rrc_wells_near", args: {}, method: "(call failed)", ok: false, output: null,
      refused: null, requestedBy: "gatherer", error: "connection reset",
    });

    const trace = geologyTrace(wellResult(s));
    assert.deepEqual(trace.tools.map((t) => t.status), ["unavailable", "ok", "failed"]);
    assert.equal(trace.by.unavailable, 1);
    assert.equal(trace.by.failed, 1);
    assert.equal(trace.by.ok, 1);
    // The summary counts what RAN, because that is the question being asked.
    assert.match(traceSummary(trace), /1 tools ran/);
    assert.match(traceSummary(trace), /1 failed/);
    assert.match(traceSummary(trace), /1 not built yet/);
  });

  test("corpus segments are deduped, and counted only when text was read", () => {
    const trace = geologyTrace(wellResult(store()));
    assert.deepEqual(trace.corpus, ["01-curve-reading/asquith#3", "04-coning/basics#1"]);
    assert.match(traceSummary(trace), /2 corpus segments read/);
  });

  test("reads the live ledger, so Fable's own calls are not missed", () => {
    // The snapshot is taken before the answer streams. A trace built from it
    // would report zero model tool calls on every turn — the exact claim the
    // side channel exists to check.
    const s = store();
    const result = wellResult(s);
    s.addToolCall({ stage: "stage3" }, {
      tool: "petrophysics", args: { tool: "archie_sw" }, method: "deterministic tool layer",
      ok: true, output: {}, refused: null, requestedBy: "fable", error: null,
    });
    const trace = geologyTrace(result);
    assert.equal(trace.by.fable, 1);
    assert.equal(trace.tools.at(-1)?.tool, "petrophysics");
  });

  test("a gate refusal is its own status, and carries the reason", () => {
    const s = store();
    s.addToolCall({ stage: "stage1" }, {
      tool: "archie_sw", args: {}, method: "Archie 1942", ok: true, output: {},
      refused: { gate: "archie_sw", reason: "Rw has no provenance", remedy: "pull the W-2" },
      requestedBy: "fable", error: null,
    });
    const trace = geologyTrace(wellResult(s));
    assert.equal(trace.tools[0].status, "refused");
    assert.equal(trace.tools[0].note, "Rw has no provenance");
    // A refusal is an answer, so it is not counted against the turn.
    assert.equal(trace.by.failed, 0);
  });
});
