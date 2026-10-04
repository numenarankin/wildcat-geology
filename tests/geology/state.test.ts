/**
 * Zone Evaluation State — the invariants, not the plumbing.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/state.test.ts
 *
 * Phase 1 of geology-agent/harness-implementation.md. Every test below asserts a
 * write is REFUSED or is RECORDED AS A CONFLICT — those are the behaviours the
 * object exists for. A test that only proved values round-trip would be testing
 * a struct.
 *
 * The intent being tested (well-log-agent.md, "Core object"):
 *   - No bare depths anywhere; every depth carries well.api + reference.
 *   - Every value in `computed` carries its inputs and method.
 *   - `[stated]` vs `[derived]` preserved end to end; nothing the user said
 *     becomes a measurement.
 *   - Concurrent branch writes must not silently last-wins each other.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import {
  createZoneEvaluation,
  InvariantError,
  type Origin,
  type Well,
} from "@/lib/ai/geology/state";

const WELL: Well = {
  api: "42-497-31234",
  name: "Repass 1",
  operator: "Test Operator",
  county: "Wise",
  district: "09",
};

const S0: Origin = { stage: "stage0" };
const FANOUT = (branch: string): Origin => ({ stage: "stage1", branch });

function store() {
  return createZoneEvaluation(WELL);
}

describe("depths carry a well and a reference", () => {
  test("a depth with no datum reference is refused", () => {
    const s = store();
    assert.throws(() => s.depth(4110, null), InvariantError);
  });

  test("a depth defaults to the subject well and keeps its reference", () => {
    const d = store().depth(4110, "KB");
    assert.equal(d.api, WELL.api);
    assert.equal(d.reference, "KB");
    assert.equal(d.subsea, false);
  });

  test("an interval spanning two wells is refused", () => {
    const s = store();
    const top = s.depth(4110, "KB");
    const base = s.depth(4118, "KB", { api: "42-497-99999" });
    assert.throws(() => s.setInterval(S0, { topMd: top, baseMd: base, topSs: null, baseSs: null }), InvariantError);
  });

  test("an interval mixing KB and GL is refused", () => {
    const s = store();
    const top = s.depth(4110, "KB");
    const base = s.depth(4118, "GL");
    assert.throws(() => s.setInterval(S0, { topMd: top, baseMd: base, topSs: null, baseSs: null }), InvariantError);
  });

  test("an inverted interval is refused", () => {
    const s = store();
    assert.throws(
      () =>
        s.setInterval(S0, {
          topMd: s.depth(4118, "KB"),
          baseMd: s.depth(4110, "KB"),
          topSs: null,
          baseSs: null,
        }),
      InvariantError
    );
  });
});

describe("computed values carry inputs and a method", () => {
  test("a value with no inputs is refused", () => {
    const s = store();
    assert.throws(
      () => s.addComputed(S0, { field: "phiD", value: 0.12, unit: "v/v", inputs: [], method: "density porosity", confidence: null }),
      InvariantError
    );
  });

  test("a value with no method is refused", () => {
    const s = store();
    assert.throws(
      () =>
        s.addComputed(S0, {
          field: "phiD",
          value: 0.12,
          unit: "v/v",
          inputs: [{ name: "rhob", value: 2.45, source: "RHOB" }],
          method: "",
          confidence: null,
        }),
      InvariantError
    );
  });

  test("the refusal names the field and the reason", () => {
    const s = store();
    assert.throws(
      () => s.addComputed(S0, { field: "phiD", value: 0.12, unit: "v/v", inputs: [], method: "x", confidence: null }),
      (err: unknown) => {
        assert.ok(err instanceof InvariantError);
        assert.match(err.message, /phiD/);
        assert.match(err.message, /inputs/);
        return true;
      }
    );
  });

  test("a well-formed value is accepted and retrievable as the latest", () => {
    const s = store();
    // phiD = (2.71 - 2.45) / (2.71 - 1.0) = 0.26 / 1.71 = 0.15205...
    // Hand-computed from the density-porosity definition, not from any code.
    s.addComputed(S0, {
      field: "phiD",
      value: 0.152,
      unit: "v/v",
      inputs: [
        { name: "rhob", value: 2.45, source: "RHOB" },
        { name: "rhoMatrix", value: 2.71, source: "assumption:matrix_density" },
        { name: "rhoFluid", value: 1.0, source: "assumption:fluid_density" },
      ],
      method: "density porosity",
      confidence: 0.8,
    });
    assert.equal(s.latest("phiD")?.value, 0.152);
    assert.equal(s.latest("phiD")?.inputs.length, 3);
    assert.equal(s.latest("nothing"), undefined);
  });

  test("a range is a legal value, since gates return bands not numbers", () => {
    const s = store();
    s.addComputed(S0, {
      field: "sw",
      value: { low: 0.35, high: 0.72 },
      unit: "v/v",
      inputs: [{ name: "rw", value: "unmeasured", source: null }],
      method: "Archie across plausible Rw",
      confidence: null,
    });
    assert.deepEqual(s.latest("sw")?.value, { low: 0.35, high: 0.72 });
  });

  test("same field, same inputs, different answer is recorded as a conflict", () => {
    const s = store();
    const inputs = [{ name: "rhob", value: 2.45, source: "RHOB" }];
    s.addComputed(FANOUT("calculators"), {
      field: "phiD", value: 0.152, unit: "v/v", inputs, method: "density porosity", confidence: null,
    });
    s.addComputed(FANOUT("recheck"), {
      field: "phiD", value: 0.201, unit: "v/v", inputs, method: "density porosity", confidence: null,
    });
    const snap = s.snapshot();
    assert.equal(snap.conflicts.length, 1);
    assert.match(snap.conflicts[0].description, /phiD/);
    // Both are kept. Discarding one would be choosing, and we cannot tell which.
    assert.equal(snap.computed.filter((c) => c.field === "phiD").length, 2);
  });

  test("same field with different inputs is a recompute, not a conflict", () => {
    const s = store();
    s.addComputed(S0, {
      field: "sw", value: 0.45, unit: "v/v",
      inputs: [{ name: "rw", value: 0.05, source: "assumption" }],
      method: "Archie", confidence: null,
    });
    s.addComputed({ stage: "stage3" }, {
      field: "sw", value: 0.38, unit: "v/v",
      inputs: [{ name: "rw", value: 0.07, source: "Pickett" }],
      method: "Archie", confidence: null,
    });
    assert.equal(s.snapshot().conflicts.length, 0);
    assert.equal(s.latest("sw")?.value, 0.38);
  });
});

describe("evidence keeps stated separate from measured", () => {
  test("a stated claim cannot be re-recorded as measured", () => {
    const s = store();
    const claim = "4110-18, not shot, SW on DST, scared them";
    s.addEvidence(S0, { claim, sourceId: "operator-call-2026-03", kind: "stated" });
    assert.throws(
      () => s.addEvidence(FANOUT("kb"), { claim, sourceId: "operator-call-2026-03", kind: "measured" }),
      InvariantError
    );
  });

  test("the same claim from a different source may be measured", () => {
    const s = store();
    const claim = "DST recovered salt water 4110-18";
    s.addEvidence(S0, { claim, sourceId: "operator-call", kind: "stated" });
    s.addEvidence(S0, { claim, sourceId: "dst-ticket-1954", kind: "documented" });
    assert.equal(s.snapshot().evidence.length, 2);
  });
});

describe("curves: unknown mnemonics are flagged, never guessed", () => {
  test("an unrecognized mnemonic with no flag is refused", () => {
    const s = store();
    assert.throws(
      () => s.addCurve(S0, { mnemonicRaw: "XZ99", mnemonicCanonical: null, unit: "??", source: "las", flagged: false }),
      InvariantError
    );
  });

  test("an unrecognized mnemonic that IS flagged is accepted", () => {
    const s = store();
    s.addCurve(S0, { mnemonicRaw: "XZ99", mnemonicCanonical: null, unit: "??", source: "las", flagged: true });
    assert.equal(s.snapshot().curves[0].flagged, true);
  });
});

describe("datum: disagreement is a hard state, not a last-wins", () => {
  test("two sources disagreeing records a conflict and leaves it unresolved", () => {
    const s = store();
    s.setDatum(S0, { kbFt: 1204, glFt: 1190, reference: "KB", source: "~PARAMETER EKB", resolved: true });
    s.setDatum(FANOUT("rrc"), { kbFt: 1218, glFt: 1190, reference: "KB", source: "RRC W-2", resolved: true });

    const snap = s.snapshot();
    assert.equal(snap.datum.resolved, false, "a disputed datum must not read as resolved");
    assert.equal(snap.datum.kbFt, 1204, "the first reading is kept, not overwritten");
    assert.equal(snap.conflicts.length, 1);
    assert.match(snap.conflicts[0].description, /Datum disagreement/);
    assert.equal(snap.conflicts[0].branches.length, 2);
    assert.match(snap.conflicts[0].resolvingDocument ?? "", /W-2/);
  });

  test("re-asserting the same datum is not a conflict", () => {
    const s = store();
    const d = { kbFt: 1204, glFt: 1190, reference: "KB" as const, source: "~PARAMETER EKB", resolved: true };
    s.setDatum(S0, d);
    s.setDatum(FANOUT("rrc"), { ...d, source: "RRC W-2" });
    assert.equal(s.snapshot().conflicts.length, 0);
    assert.equal(s.snapshot().datum.resolved, true);
  });

  test("a fresh evaluation starts unresolved", () => {
    assert.equal(store().snapshot().datum.resolved, false);
  });
});

describe("concurrent fan-out branches", () => {
  test("branches writing different fields all land", async () => {
    const s = store();
    const tick = () => new Promise((r) => setImmediate(r));

    await Promise.all([
      (async () => {
        await tick();
        s.addComputed(FANOUT("calculators"), {
          field: "turnerRate", value: 412, unit: "mcf/d",
          inputs: [{ name: "tubingId", value: 1.995, source: "assumption" }],
          method: "Turner critical rate", confidence: null,
        });
      })(),
      (async () => {
        s.addOffset(FANOUT("offsets"), {
          api: "42-497-30001", distanceFt: 2640, picks: [], dst: [], datumResolved: true,
        });
        await tick();
        s.addEvidence(FANOUT("offsets"), {
          claim: "offset perforated 4108-4120", sourceId: "rrc-completion-1", kind: "documented",
        });
      })(),
      (async () => {
        await tick();
        s.addCurve(FANOUT("stage0"), {
          mnemonicRaw: "GR", mnemonicCanonical: "GR", unit: "GAPI", source: "las", flagged: false,
        });
      })(),
    ]);

    const snap = s.snapshot();
    assert.equal(snap.computed.length, 1);
    assert.equal(snap.offsets.length, 1);
    assert.equal(snap.evidence.length, 1);
    assert.equal(snap.curves.length, 1);
    assert.equal(snap.conflicts.length, 0);
  });

  test("two branches disagreeing on the datum produce a conflict, not a coin flip", async () => {
    const s = store();
    const tick = () => new Promise((r) => setImmediate(r));
    await Promise.all([
      (async () => {
        await tick();
        s.setDatum(FANOUT("las"), { kbFt: 1204, glFt: 1190, reference: "KB", source: "las", resolved: true });
      })(),
      (async () => {
        await tick();
        await tick();
        s.setDatum(FANOUT("rrc"), { kbFt: 1218, glFt: 1190, reference: "KB", source: "rrc", resolved: true });
      })(),
    ]);
    assert.equal(s.hasConflicts(), true);
    assert.equal(s.snapshot().datum.resolved, false);
  });
});

describe("the journal is complete by construction", () => {
  test("every write produces exactly one entry, in order, with its origin", () => {
    const s = store();
    s.setDatum(S0, { kbFt: 1204, glFt: 1190, reference: "KB", source: "las", resolved: true });
    s.addCurve(S0, { mnemonicRaw: "GR", mnemonicCanonical: "GR", unit: "GAPI", source: "las", flagged: false });
    s.addAssumption(FANOUT("kb"), {
      field: "matrix_density", value: 2.71, source: "default", basis: "limestone matrix", overridable: true,
    });
    s.addOpen({ stage: "stage3" }, { question: "Which KB is right?", blocking: true });

    const log = s.journal();
    assert.deepEqual(log.map((e) => e.action), ["setDatum", "addCurve", "addAssumption", "addOpen"]);
    assert.deepEqual(log.map((e) => e.seq), [1, 2, 3, 4]);
    assert.equal(log[2].origin.stage, "stage1");
    assert.equal(log[2].origin.branch, "kb");
    assert.equal(log[3].origin.stage, "stage3");
  });

  test("a refused write leaves no trace", () => {
    const s = store();
    assert.throws(
      () => s.addComputed(S0, { field: "phiD", value: 0.12, unit: null, inputs: [], method: "x", confidence: null }),
      InvariantError
    );
    assert.equal(s.journal().length, 0);
    assert.equal(s.snapshot().computed.length, 0);
  });

  test("a conflict recorded by a write is journalled too", () => {
    const s = store();
    s.setDatum(S0, { kbFt: 1204, glFt: 1190, reference: "KB", source: "las", resolved: true });
    s.setDatum(FANOUT("rrc"), { kbFt: 1218, glFt: 1190, reference: "KB", source: "rrc", resolved: true });
    assert.deepEqual(s.journal().map((e) => e.action), ["setDatum", "addConflict", "setDatum"]);
  });
});

describe("guards on the rest of the object", () => {
  test("the subject well cannot be recorded as its own offset", () => {
    const s = store();
    assert.throws(
      () => s.addOffset(S0, { api: WELL.api, distanceFt: 0, picks: [], dst: [], datumResolved: true }),
      InvariantError
    );
  });

  test("the well API cannot change mid-evaluation", () => {
    const s = store();
    assert.throws(() => s.setWell(S0, { api: "42-497-00000" }), InvariantError);
    s.setWell(S0, { operator: "New Operator" });
    assert.equal(s.snapshot().well.operator, "New Operator");
    assert.equal(s.snapshot().well.api, WELL.api);
  });

  test("a conflict needs at least two branches", () => {
    const s = store();
    assert.throws(() =>
      s.addConflict(S0, { description: "one-sided", branches: ["only"], resolvingDocument: null })
    );
  });

  test("the inconsistency metric is zero on a well-formed object", () => {
    const s = store();
    s.addComputed(S0, {
      field: "phiD", value: 0.152, unit: "v/v",
      inputs: [{ name: "rhob", value: 2.45, source: "RHOB" }],
      method: "density porosity", confidence: null,
    });
    s.addOffset(S0, {
      api: "42-497-30001", distanceFt: 2640,
      picks: [{ formation: "Caddo", depth: s.depth(4090, "KB", { api: "42-497-30001" }) }],
      dst: [], datumResolved: true,
    });
    assert.deepEqual(s.inconsistencies(), []);
  });

  test("the inconsistency metric catches an offset carrying another well's pick", () => {
    const s = store();
    s.addOffset(S0, {
      api: "42-497-30001", distanceFt: 2640,
      // The copy-paste this object exists to make visible: the subject well's
      // depth filed under the offset.
      picks: [{ formation: "Caddo", depth: s.depth(4090, "KB") }],
      dst: [], datumResolved: true,
    });
    const found = s.inconsistencies();
    assert.equal(found.length, 1);
    assert.match(found[0], /carries a pick on/);
  });

  test("a gate refusal is recorded with its remedy", () => {
    const s = store();
    s.addRefusal({ stage: "stage3", branch: "standoff" }, {
      gate: "structural-datum",
      tool: "standoff",
      reason: "offset 42-497-30001 datum unresolved",
      remedy: "pull the W-2 for 42-497-30001",
    });
    const r = s.snapshot().refusals[0];
    assert.equal(r.gate, "structural-datum");
    assert.match(r.remedy, /W-2/);
  });
});
