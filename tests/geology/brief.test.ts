/**
 * The tool ledger and the brief handed to Fable.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/brief.test.ts
 *
 * The requirement: Sonnet's output to Fable states exactly which tools were used
 * and what each returned, so Fable can show its work — and so a figure in the
 * answer that is not in the ledger is detectably not from a tool.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { Corpus } from "@/lib/ai/geology/corpus";
import { renderBrief } from "@/lib/ai/geology/brief";
import { fanOut } from "@/lib/ai/geology/stage1-fanout";
import { createZoneEvaluation } from "@/lib/ai/geology/state";
import type { HeaderFacts } from "@/lib/ai/geology/contracts";
import { CLEAN_API, fixtureRegistry } from "./fixtures/tools";
import { scriptedModel, type ScriptOptions } from "./fixtures/model";

const CORPUS_ROOT = path.join(import.meta.dirname, "fixtures", "corpus");

const HEADER: HeaderFacts = {
  api: CLEAN_API, name: "Repass 1", operator: "Test Operator", county: "Wise", district: "09",
  kbFt: 1204, glFt: 1190, epdFt: 1204, reference: "KB",
  latitude: 33.1234, longitude: -97.6543,
  startFt: 100, stopFt: 5000, stepFt: 0.5, nullValue: -999.25,
};

const PROMPT = "is there pay between 4,100 and 4,120, and will it cone?";

async function run(script: ScriptOptions = {}, toolOpts: Parameters<typeof fixtureRegistry>[0] = {}) {
  const store = createZoneEvaluation({
    api: CLEAN_API, name: "Repass 1", operator: "Test Operator", county: "Wise", district: "09",
  });
  store.setDatum({ stage: "stage0" }, {
    kbFt: 1204, glFt: 1190, reference: "KB", source: "LAS ~PARAMETER", resolved: true,
  });
  const result = await fanOut(store, { prompt: PROMPT, header: HEADER }, {
    registry: fixtureRegistry(toolOpts),
    corpus: new Corpus({
      knowledgeBase: path.join(CORPUS_ROOT, "knowledge-base"),
      toc: path.join(CORPUS_ROOT, "toc"),
    }),
    model: scriptedModel(script),
    ctx: { api: CLEAN_API, lasPath: "/fixtures/x.las" },
  });
  const brief = renderBrief({
    prompt: PROMPT,
    state: store.snapshot(),
    gathered: result.gathered,
    failedBranches: result.failed,
  });
  return { store, result, brief };
}

describe("every tool call is recorded", () => {
  test("the automatic branches all land in toolCalls with their output", async () => {
    const { store } = await run();
    const calls = store.snapshot().toolCalls;
    const names = calls.map((c) => c.tool);

    for (const expected of ["kb_lookup", "calculators", "offsets_within_radius", "continuity_check"]) {
      assert.ok(names.includes(expected), `${expected} was not recorded`);
    }
    for (const c of calls) {
      assert.ok(c.method.length > 0, `${c.tool} recorded no method`);
      assert.notEqual(c.output, undefined, `${c.tool} recorded no output`);
      assert.equal(c.requestedBy, "harness");
    }
  });

  test("a gatherer-requested call is recorded as the gatherer's, not the harness's", async () => {
    const { store } = await run({
      tools: [{ name: "rrc_completion_record", args: {} }],
    });
    const calls = store.snapshot().toolCalls;
    const mine = calls.filter((c) => c.requestedBy === "gatherer");
    assert.equal(mine.length, 1);
    assert.equal(mine[0].tool, "rrc_completion_record");
    // And its output is kept, not just the fact that it ran.
    assert.equal((mine[0].output as { api: string }).api, CLEAN_API);
  });

  test("a failed call is recorded as a failed call", async () => {
    // A tool that threw and left no trace looks exactly like a tool that was
    // never needed.
    const { store } = await run({}, { failing: ["continuity_check"] });
    const failed = store.snapshot().toolCalls.find((c) => c.tool === "continuity_check");
    assert.ok(failed);
    assert.equal(failed.ok, false);
    assert.match(failed.error ?? "", /unavailable/);
  });
});

describe("the brief tells Fable exactly what ran", () => {
  test("every tool appears with its arguments and its returned output", async () => {
    const { store, brief } = await run({ tools: [{ name: "rrc_completion_record", args: {} }] });

    for (const call of store.snapshot().toolCalls) {
      assert.ok(brief.includes(call.tool), `${call.tool} missing from the brief`);
    }
    // Output, not a description of output: the coning spread comes back as the
    // literal numbers the calculator returned.
    assert.match(brief, /"low": 38/);
    assert.match(brief, /"high": 94/);
    // Arguments too, so a reader can see the radius the offsets were pulled at.
    assert.match(brief, /"radiusFt":5280/);
  });

  test("the ledger separates automatic calls from the gatherer's own", async () => {
    const { brief } = await run({ tools: [{ name: "kb_lookup", args: { county: "Wise", district: "09" } }] });
    assert.match(brief, /Run automatically for every well/);
    assert.match(brief, /Requested by the context gatherer for this question/);
  });

  test("a failed tool is disclosed in the brief, not omitted", async () => {
    const { brief } = await run({}, { failing: ["offsets_within_radius"] });
    assert.match(brief, /FAILED/);
    assert.match(brief, /offsets_within_radius/);
    assert.match(brief, /the offsets branch failed/);
  });

  test("passages arrive verbatim, with the ID Fable cites", async () => {
    const { brief } = await run({ segments: ["01-curve-reading/gr-basics#1"] });
    assert.match(brief, /\[01-curve-reading\/gr-basics#1\]/);
    assert.match(brief, /IGR = \(GR_log - GR_clean\) \/ \(GR_shale - GR_clean\)/);
  });

  test("computed values carry their method and inputs", async () => {
    const { brief } = await run();
    assert.match(brief, /\*\*coning_critical_rate\*\* = 38–94 bbl\/d/);
    assert.match(brief, /Craft & Hawkins \/ Chaperon \/ Schols spread/);
    assert.match(brief, /standoffFt=12/);
  });

  test("assumptions are listed as assumptions, with their basis", async () => {
    const { brief } = await run();
    assert.match(brief, /## Assumptions in force/);
    assert.match(brief, /\*\*basin\*\* = Fort Worth/);
    assert.match(brief, /overridable/);
  });

  test("evidence keeps its kind, so `stated` cannot be read as measured", async () => {
    const { store } = await run();
    store.addEvidence({ stage: "stage1", branch: "user" }, {
      claim: "4110-18, not shot, SW on DST, scared them",
      sourceId: "operator-call",
      kind: "stated",
    });
    const brief = renderBrief({ prompt: PROMPT, state: store.snapshot(), gathered: null });
    assert.match(brief, /\[stated\] 4110-18, not shot/);
    assert.match(brief, /is evidence, not measurement/);
  });

  test("gaps are surfaced rather than papered over", async () => {
    const { brief } = await run({ documents: ["gr-basics", "no-such-doc"] });
    assert.match(brief, /## Gaps and open items/);
    assert.match(brief, /"no-such-doc", which is not in the corpus/);
  });

  test("an unresolved datum is stated in the header of the brief", async () => {
    const store = createZoneEvaluation({
      api: CLEAN_API, name: null, operator: null, county: null, district: null,
    });
    const brief = renderBrief({ prompt: PROMPT, state: store.snapshot(), gathered: null });
    assert.match(brief, /Datum: UNRESOLVED/);
  });

  test("a gate refusal reaches Fable with its remedy", async () => {
    const store = createZoneEvaluation({
      api: CLEAN_API, name: null, operator: null, county: null, district: null,
    });
    store.addRefusal({ stage: "stage1", branch: "standoff" }, {
      gate: "structural-datum",
      tool: "standoff",
      reason: "offset 42-497-30001 datum unresolved",
      remedy: "pull the W-2 for 42-497-30001",
    });
    const brief = renderBrief({ prompt: PROMPT, state: store.snapshot(), gathered: null });
    assert.match(brief, /## Gates that refused/);
    assert.match(brief, /pull the W-2/);
  });

  test("the brief instructs Fable that numbers must trace to a tool", async () => {
    // This is the sentence that makes "show your work" checkable rather than
    // aspirational.
    const { brief } = await run();
    assert.match(brief, /if a figure is not traceable to one of these, do not write it/);
    assert.match(brief, /Do not compute new ones/);
  });
});

describe("the ledger survives caching", () => {
  test("a restored state object keeps its tool calls", async () => {
    const { store } = await run();
    const snap = store.snapshot();
    const { ZoneEvaluationStore } = await import("@/lib/ai/geology/state");
    const restored = ZoneEvaluationStore.restore(snap);
    assert.deepEqual(restored.snapshot().toolCalls, snap.toolCalls);
    assert.ok(restored.snapshot().toolCalls.length > 0);
  });
});
