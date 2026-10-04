/**
 * Deterministic plausibility checks — the defence against a broken tool.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/plausibility.test.ts
 *
 * The tool layer is under construction. A tool that returns a plausible-looking
 * wrong number defeats every provenance rule in the system: it has inputs, it
 * has a method, it looks exactly like a correct one. These checks catch it
 * arithmetically, so escalation does not depend on the model noticing.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { checkPlausibility } from "@/lib/ai/geology/plausibility";
import { createZoneEvaluation, type ComputedInit } from "@/lib/ai/geology/state";

function store(...values: ComputedInit[]) {
  const s = createZoneEvaluation({
    api: "42-497-31234", name: "Test 1", operator: "Op", county: "Wise", district: "09",
  });
  for (const v of values) s.addComputed({ stage: "stage1", branch: "calculators" }, v);
  return s;
}

const computed = (field: string, value: ComputedInit["value"], unit: string | null = "v/v"): ComputedInit => ({
  field, value, unit,
  inputs: [{ name: "rhob", value: 2.45, source: "RHOB" }],
  method: "test", confidence: null,
});

describe("physical bounds", () => {
  test("a porosity above 45% is not rock", () => {
    const s = store(computed("phiD", 0.62));
    const found = checkPlausibility(s);
    assert.equal(found.length, 1);
    assert.match(found[0].why, /45%/);
    assert.equal(s.snapshot().conflicts.length, 1, "it must escalate, not just report");
  });

  test("a saturation above 1 is not a saturation", () => {
    assert.equal(checkPlausibility(store(computed("sw", 1.4))).length, 1);
  });

  test("a negative resistivity, thickness, or standoff", () => {
    assert.equal(checkPlausibility(store(computed("rt", -5, "ohmm"))).length, 1);
    assert.equal(checkPlausibility(store(computed("net_pay_thickness", -12, "ft"))).length, 1);
    assert.equal(checkPlausibility(store(computed("standoff", -3, "ft"))).length, 1);
  });

  test("a bulk density that is not rock", () => {
    assert.equal(checkPlausibility(store(computed("rhob", 0.4, "g/cc"))).length, 1);
  });

  test("both ends of a range are checked, not just the low one", () => {
    assert.equal(checkPlausibility(store(computed("sw", { low: 0.3, high: 1.8 }))).length, 1);
  });

  test("ordinary values pass", () => {
    const s = store(
      computed("phiD", 0.152),
      computed("sw", 0.41),
      computed("vsh", 0.22),
      computed("rt", 22, "ohmm"),
      computed("rhob", 2.45, "g/cc"),
      computed("coning_critical_rate", { low: 38, high: 94 }, "bbl/d"),
    );
    assert.deepEqual(checkPlausibility(s), []);
    assert.equal(s.snapshot().conflicts.length, 0);
  });

  test("a field with no bound is left alone", () => {
    assert.deepEqual(checkPlausibility(store(computed("washout_intervals", 3, "intervals"))), []);
  });
});

describe("unit and magnitude", () => {
  test("a v/v value above 1 is a percentage that never got converted", () => {
    // The silent one: 15.2 reads as a perfectly reasonable porosity if you take
    // it as a percent, so nothing downstream would question it.
    const found = checkPlausibility(store(computed("phiE", 15.2)));
    assert.equal(found.length, 1);
    assert.match(found[0].why, /percentage/);
  });

  test("the same magnitude in percent units is fine", () => {
    assert.deepEqual(checkPlausibility(store(computed("phiE", 15.2, "%"))), []);
  });

  test("the range check fires before the unit check, and only once", () => {
    assert.equal(checkPlausibility(store(computed("sw", 42))).length, 1);
  });
});

describe("redundancy: crossplot porosity must lie between its inputs", () => {
  const pair = [computed("phiD", 0.152), computed("phiN", 0.24)];

  test("a crossplot value outside the pair is arithmetic, not geology", () => {
    const s = store(...pair, computed("phiXplot", 0.31));
    const found = checkPlausibility(s);
    assert.equal(found.length, 1);
    assert.match(found[0].why, /between its density and neutron/);
    assert.match(s.snapshot().conflicts[0].description, /0\.152.*0\.24|0\.24.*0\.152/);
  });

  test("a value between them passes", () => {
    assert.deepEqual(checkPlausibility(store(...pair, computed("phiXplot", 0.196))), []);
  });

  test("root-mean-square forms just outside the pair are tolerated", () => {
    assert.deepEqual(checkPlausibility(store(...pair, computed("phiXplot", 0.2005))), []);
  });

  test("no check without all three values", () => {
    assert.deepEqual(checkPlausibility(store(...pair)), []);
    assert.deepEqual(checkPlausibility(store(computed("phiD", 0.152), computed("phiXplot", 0.4))), []);
  });

  test("this catches a tool whose output is individually plausible", () => {
    // 31% porosity breaks no bound on its own. Only its relationship to the
    // values it was derived from shows it is wrong.
    assert.deepEqual(checkPlausibility(store(computed("phiXplot", 0.31))), []);
    assert.equal(checkPlausibility(store(...pair, computed("phiXplot", 0.31))).length, 1);
  });
});

describe("the finding reaches the operator in domain terms", () => {
  test("the conflict says what is impossible, not that a tool failed", () => {
    const s = store(computed("phiD", 0.62));
    checkPlausibility(s);
    const c = s.snapshot().conflicts[0];
    assert.match(c.description, /not physically possible/);
    assert.ok(!/tool|function|returned invalid/i.test(c.description), "the machinery must not leak into the finding");
    assert.equal(c.branches.length, 2);
  });
});
