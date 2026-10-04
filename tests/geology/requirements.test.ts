/**
 * The must-compute rule.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/requirements.test.ts
 *
 * The largest penalty in the graded runs was closed-form arithmetic that never
 * happened — coning rate, Turner, drawdown and IPR were all computable and none
 * got computed. A model cannot notice a number it never thought to want, so the
 * harness decides what a question requires and says what is missing.
 *
 * The other half of the rule: a missing number never cancels the turn, and the
 * reason it is missing stays internal.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { checkRequirements, classifyIntents } from "@/lib/ai/geology/requirements";
import { renderBrief } from "@/lib/ai/geology/brief";
import { createZoneEvaluation, type ComputedInit, type ZoneEvaluationStore } from "@/lib/ai/geology/state";

const S1 = { stage: "stage1" as const, branch: "calculators" };

function store(...fields: string[]): ZoneEvaluationStore {
  const s = createZoneEvaluation({
    api: "42-497-31234", name: "Test 1", operator: "Op", county: "Wise", district: "09",
  });
  for (const field of fields) {
    const v: ComputedInit = {
      field, value: 1, unit: null,
      inputs: [{ name: "x", value: 1, source: "y" }],
      method: "test", confidence: null,
    };
    s.addComputed(S1, v);
  }
  return s;
}

describe("classifying what a question obliges", () => {
  test("a rate question wants the rate closed forms", () => {
    assert.ok(classifyIntents("what rate will this make?").includes("rate"));
  });

  test("a perforating question wants coning, unloading, standoff and net pay", () => {
    const r = checkRequirements(store(), "where should I perforate?");
    const labels = r.statuses.map((s) => s.label).join(" | ");
    for (const want of ["coning", "Turner/Coleman", "standoff", "net pay"]) {
      assert.ok(labels.includes(want), `${want} not required for a perforating question`);
    }
  });

  test("overlapping intents do not duplicate a requirement", () => {
    // "perforate and what will it make" matches rate + completion + water, all
    // of which want the coning rate.
    const r = checkRequirements(store(), "should I perforate this and what rate will it make in water?");
    const coning = r.statuses.filter((s) => s.label.includes("coning"));
    assert.equal(coning.length, 1);
    assert.ok(r.intents.length >= 2);
  });

  test("a question with no numeric duty requires nothing", () => {
    const r = checkRequirements(store(), "what curves are in this log?");
    assert.deepEqual(r.intents, []);
    assert.deepEqual(r.statuses, []);
  });
});

describe("what is present and what is missing", () => {
  test("a computed value satisfies its requirement", () => {
    const r = checkRequirements(store("coning_critical_rate"), "will it cone?");
    const coning = r.statuses.find((s) => s.label.includes("coning"));
    assert.equal(coning?.satisfied, true);
    assert.ok(!r.missing.some((m) => m.label.includes("coning")));
  });

  test("the gap is recorded as a non-blocking open item, never a conflict", () => {
    // A missing number is an absence, not a contradiction — it must not route
    // the turn to the escalated path.
    const s = store();
    const r = checkRequirements(s, "what rate will this make?");
    assert.ok(r.missing.length > 0);
    assert.equal(s.snapshot().conflicts.length, 0, "a gap must not escalate the turn");
    assert.ok(s.snapshot().open.every((o) => !o.blocking), "a lost prerequisite must not block");
  });

  test("attempted-and-failed is distinguished from never-produced", () => {
    const s = store();
    s.addToolCall(S1, {
      tool: "calculators", args: {}, method: "(call failed)", ok: false,
      output: null, refused: null, requestedBy: "harness", error: "timeout",
    });
    const r = checkRequirements(s, "what rate will this make?");
    assert.ok(r.missing.every((m) => m.reason === "attempted and failed"));

    const clean = checkRequirements(store(), "what rate will this make?");
    assert.ok(clean.missing.every((m) => m.reason === "not produced"));
  });

  test("a gate refusal counts as attempted", () => {
    const s = store();
    s.addRefusal(S1, {
      gate: "structural-datum", tool: "standoff",
      reason: "datum unresolved", remedy: "pull the W-2",
    });
    const r = checkRequirements(s, "how much standoff do I have?");
    assert.equal(r.missing.find((m) => m.label.includes("standoff"))?.reason, "attempted and failed");
  });
});

describe("what reaches Fable", () => {
  function brief(prompt: string, s: ZoneEvaluationStore) {
    return renderBrief({
      prompt, state: s.snapshot(), gathered: null,
      requirements: checkRequirements(s, prompt),
    });
  }

  test("available numbers are marked as mandatory to use", () => {
    const text = brief("will it cone?", store("coning_critical_rate"));
    assert.match(text, /## What this question requires/);
    assert.match(text, /available above\. Use it; do not answer around it/);
  });

  test("a missing number tells Fable to answer anyway, in domain terms", () => {
    const text = brief("what rate will this make?", store());
    assert.match(text, /NOT AVAILABLE/);
    assert.match(text, /answer the rest of the question in full/);
    assert.match(text, /Do not estimate it/);
    assert.match(text, /Do not shorten your answer because of it/);
    assert.match(text, /Do not use the words failed, error, or unavailable/);
  });

  test("the internal reason is present for Fable but framed as internal", () => {
    // Fable needs to know it was attempted; the operator must never hear it.
    const text = brief("what rate will this make?", store());
    assert.match(text, /\(not produced; internal, never repeat this to the operator\)/);
  });

  test("a question with no numeric duty adds no section", () => {
    assert.ok(!brief("what curves are in this log?", store()).includes("What this question requires"));
  });
});
