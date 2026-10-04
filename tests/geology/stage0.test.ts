/**
 * Stage 0 — Resolve. Phase 2 of geology-agent/harness-implementation.md.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/stage0.test.ts
 *
 * What the plan says to prove, and what each block below asserts:
 *   - a cold well materializes a complete state object
 *   - a second call hits cache
 *   - each of the three invalidation triggers actually invalidates
 *   - a header with no EKB comes back unresolved rather than guessing
 *   - the header is published BEFORE the full parse finishes (the one ordering
 *     constraint in the architecture, and the reason Stage 0 returns two promises)
 *
 * Tools are fixtures — real tool objects with real schemas over fixed data. The
 * harness code is the code under test.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { z } from "zod";
import { MemoryEvaluationCache, STATE_VERSION, type CacheStamps } from "@/lib/ai/geology/cache";
import { resolveStage0 } from "@/lib/ai/geology/stage0-resolve";
import { ToolContractError, ToolNotFoundError, ToolRegistry } from "@/lib/ai/geology/registry";
import {
  CLEAN_API,
  CallCounter,
  DATUM_FIGHT_API,
  NO_EKB_API,
  fixtureRegistry,
} from "./fixtures/tools";

const STAMPS: CacheStamps = { las: "hash-las-1", rrc: "rrc-v1", facts: "facts-v1" };

function deps(opts: Parameters<typeof fixtureRegistry>[0] = {}) {
  return {
    registry: fixtureRegistry(opts),
    cache: new MemoryEvaluationCache(),
    now: () => 1_700_000_000_000,
  };
}

async function resolve(api: string, d: ReturnType<typeof deps>, stamps: CacheStamps = STAMPS) {
  return resolveStage0({ api, lasPath: `/fixtures/${api}.las`, stamps }, d).done;
}

describe("a cold well materializes a complete state object", () => {
  test("well, datum, curves, computed values and assumptions all land", async () => {
    const r = await resolve(CLEAN_API, deps());
    const s = r.store.snapshot();

    assert.equal(r.cacheHit, false);
    assert.equal(r.missReason, "cold");

    assert.equal(s.well.api, CLEAN_API);
    assert.equal(s.well.name, "Repass 1");
    assert.equal(s.well.county, "Wise");

    assert.equal(s.datum.resolved, true);
    assert.equal(s.datum.kbFt, 1204);

    assert.equal(s.curves.length, 7);
    assert.equal(s.computed.some((c) => c.field === "phiD"), true);
    assert.equal(s.computed.some((c) => c.field === "vsh"), true);
    assert.equal(s.assumptions.some((a) => a.field === "matrix_density"), true);
  });

  test("every computed value carries its inputs and method", async () => {
    const r = await resolve(CLEAN_API, deps());
    for (const c of r.store.snapshot().computed) {
      assert.ok(c.inputs.length > 0, `${c.field} has no inputs`);
      assert.ok(c.method.length > 0, `${c.field} has no method`);
    }
    assert.deepEqual(r.store.inconsistencies(), []);
  });

  test("the assumption the porosity rests on is recorded, not implied", async () => {
    // The failure both sample analyses shared: a porosity whose matrix constant
    // nobody stated. Assert the constant is in `assumptions[]` AND named as an
    // input of the value that used it.
    const r = await resolve(CLEAN_API, deps());
    const s = r.store.snapshot();
    const matrix = s.assumptions.find((a) => a.field === "matrix_density");
    assert.ok(matrix, "matrix density must be recorded as an assumption");
    assert.equal(matrix.value, 2.71);
    assert.equal(matrix.overridable, true);

    const phiD = r.store.latest("phiD");
    assert.ok(phiD?.inputs.some((i) => i.source === "assumption:matrix_density"));
  });

  test("an unknown mnemonic is kept and flagged, never guessed", async () => {
    const r = await resolve(CLEAN_API, deps());
    const xz = r.store.snapshot().curves.find((c) => c.mnemonicRaw === "XZ99");
    assert.ok(xz);
    assert.equal(xz.mnemonicCanonical, null);
    assert.equal(xz.flagged, true);
    // And the known ones are not flagged.
    assert.equal(r.store.snapshot().curves.find((c) => c.mnemonicRaw === "GR")?.flagged, false);
  });

  test("washouts are recorded as measured evidence with a suppression note", async () => {
    const r = await resolve(CLEAN_API, deps());
    const s = r.store.snapshot();
    assert.equal(r.store.latest("washout_intervals")?.value, 1);
    const ev = s.evidence.find((e) => e.claim.includes("washed out"));
    assert.ok(ev);
    assert.equal(ev.kind, "measured");
    assert.ok(s.open.some((o) => o.question.includes("Density porosity is suppressed")));
  });
});

describe("the datum cross-check", () => {
  test("agreement within reporting precision is not a conflict", async () => {
    // Header 1204, RRC 1204.5. Half a foot is how the two forms round.
    const r = await resolve(CLEAN_API, deps());
    const s = r.store.snapshot();
    assert.equal(s.conflicts.length, 0);
    assert.equal(s.datum.resolved, true);
    assert.ok(s.evidence.some((e) => e.claim.includes("agrees with the LAS header")));
  });

  test("a header with no EKB is resolved BY the RRC record, not guessed", async () => {
    const r = await resolve(NO_EKB_API, deps());
    const s = r.store.snapshot();
    assert.equal(s.datum.kbFt, 1212, "the RRC value fills the gap");
    assert.equal(s.datum.source, "RRC W-2");
    assert.equal(s.datum.resolved, true);
    assert.equal(s.conflicts.length, 0, "absence is not a competing opinion");
  });

  test("a real disagreement leaves the datum unresolved and records the conflict", async () => {
    // Header 1204 vs RRC 1218. Fourteen feet moves a pick out of the zone.
    const r = await resolve(DATUM_FIGHT_API, deps());
    const s = r.store.snapshot();
    assert.equal(s.datum.resolved, false);
    assert.equal(s.conflicts.length, 1);
    assert.match(s.conflicts[0].description, /Datum disagreement/);
    assert.match(s.conflicts[0].resolvingDocument ?? "", /W-2/);
    assert.ok(s.open.some((o) => o.question.includes("unresolved")));
  });

  test("an unresolved datum is not by itself blocking", async () => {
    // Plenty of questions need no datum at all. The structural gate blocks, in
    // the tool that would produce the number — not here.
    const r = await resolve(DATUM_FIGHT_API, deps());
    const item = r.store.snapshot().open.find((o) => o.question.includes("unresolved"));
    assert.equal(item?.blocking, false);
  });
});

describe("the header is published before the parse completes", () => {
  test("`header` settles while `done` is still running", async () => {
    const order: string[] = [];
    const handle = resolveStage0(
      { api: CLEAN_API, lasPath: "/fixtures/x.las", stamps: STAMPS },
      deps({ delayMs: 20 })
    );
    const h = handle.header.then(() => order.push("header"));
    const d = handle.done.then(() => order.push("done"));
    await Promise.all([h, d]);
    assert.deepEqual(order, ["header", "done"]);
  });

  test("the header carries what Stage 1's RRC branches need", async () => {
    const handle = resolveStage0(
      { api: CLEAN_API, lasPath: "/fixtures/x.las", stamps: STAMPS },
      deps({ delayMs: 5 })
    );
    const header = await handle.header;
    assert.equal(header.latitude, 33.1234);
    assert.equal(header.longitude, -97.6543);
    assert.equal(header.kbFt, 1204);
    await handle.done;
  });

  test("a header that cannot be read fails both promises", async () => {
    const handle = resolveStage0(
      { api: CLEAN_API, lasPath: "/fixtures/x.las", stamps: STAMPS },
      deps({ failHeader: true })
    );
    await assert.rejects(handle.header, /LAS header unreadable/);
    await assert.rejects(handle.done, /LAS header unreadable/);
  });
});

describe("cache", () => {
  test("a second call hits cache and calls no tools at all", async () => {
    const counter = new CallCounter();
    const d = deps({ counter });

    const first = await resolve(CLEAN_API, d);
    assert.equal(first.cacheHit, false);
    const afterFirst = counter.total;
    assert.ok(afterFirst > 0);

    const second = await resolve(CLEAN_API, d);
    assert.equal(second.cacheHit, true);
    assert.equal(second.missReason, null);
    assert.equal(counter.total, afterFirst, "a cache hit must do no work");
  });

  test("a cache hit restores the whole state object", async () => {
    const d = deps();
    const first = await resolve(CLEAN_API, d);
    const second = await resolve(CLEAN_API, d);
    assert.deepEqual(second.store.snapshot(), first.store.snapshot());
    assert.equal(second.header.kbFt, 1204, "the header comes back too, for Stage 1");
  });

  test("a restored store starts a fresh journal but keeps writing past the old seq", async () => {
    const d = deps();
    await resolve(CLEAN_API, d);
    const second = await resolve(CLEAN_API, d);

    // The cached turn did not do Stage 0's work, so its trajectory must not
    // claim it did.
    assert.equal(second.store.journal().length, 0);

    const highest = Math.max(...second.store.snapshot().computed.map((c) => c.seq));
    const added = second.store.addOpen({ stage: "stage3" }, { question: "later", blocking: false });
    assert.ok(added.seq > highest, "new writes must not collide with restored ones");
  });

  test("a new LAS invalidates: different hash, different key", async () => {
    const counter = new CallCounter();
    const d = deps({ counter });
    await resolve(CLEAN_API, d);
    counter.reset();

    const again = await resolve(CLEAN_API, d, { ...STAMPS, las: "hash-las-2" });
    assert.equal(again.cacheHit, false);
    assert.equal(again.missReason, "cold", "a new file is a new key, not a stale entry");
    assert.ok(counter.total > 0, "the work must actually re-run");
  });

  test("a new RRC record invalidates and says so", async () => {
    const counter = new CallCounter();
    const d = deps({ counter });
    await resolve(CLEAN_API, d);
    counter.reset();

    const again = await resolve(CLEAN_API, d, { ...STAMPS, rrc: "rrc-v2" });
    assert.equal(again.cacheHit, false);
    assert.equal(again.missReason, "rrc record changed");
    assert.ok(counter.total > 0);
  });

  test("a new user fact invalidates and says so", async () => {
    const d = deps();
    await resolve(CLEAN_API, d);
    const again = await resolve(CLEAN_API, d, { ...STAMPS, facts: "facts-v2" });
    assert.equal(again.cacheHit, false);
    assert.equal(again.missReason, "user facts changed");
  });

  test("a state-version bump invalidates every entry", async () => {
    const d = deps();
    await resolve(CLEAN_API, d);
    const entry = await d.cache.get(`${CLEAN_API}:${STAMPS.las}`);
    assert.ok(entry);
    await d.cache.set(`${CLEAN_API}:${STAMPS.las}`, { ...entry, version: STATE_VERSION - 1 });

    const again = await resolve(CLEAN_API, d);
    assert.equal(again.cacheHit, false);
    assert.match(again.missReason ?? "", /state version/);
  });

  test("two wells do not share a cache entry", async () => {
    const d = deps();
    await resolve(CLEAN_API, d);
    const other = await resolve(NO_EKB_API, d);
    assert.equal(other.cacheHit, false);
    assert.equal(other.store.snapshot().well.api, NO_EKB_API);
    assert.equal(d.cache.size, 2);
  });
});

describe("the tool boundary", () => {
  test("the registry refuses a tool that is not declared read-only", () => {
    const registry = new ToolRegistry();
    assert.throws(
      () =>
        registry.register({
          name: "save_pick",
          description: "writes a formation pick",
          inputSchema: z.object({ depth: z.number() }),
          outputSchema: z.object({ id: z.string() }),
          // The type says `true`; a write tool can only get here by lying, and
          // the registry checks at runtime as well.
          readOnly: false as true,
          callableBy: ["fable"],
          execute: async () => ({
            value: { id: "pick-1" },
            provenance: { tool: "save_pick", inputs: {}, method: "insert" },
          }),
        }),
      ToolContractError
    );
    assert.equal(registry.has("save_pick"), false);
  });

  test("a tool callable by nobody is refused", () => {
    assert.throws(
      () =>
        new ToolRegistry().register({
          name: "orphan",
          description: "unreachable",
          inputSchema: z.object({}),
          outputSchema: z.object({}),
          readOnly: true,
          callableBy: [],
          execute: async () => ({ value: {}, provenance: { tool: "orphan", inputs: {}, method: "x" } }),
        }),
      ToolContractError
    );
  });

  test("a role that may not call a tool cannot reach it", async () => {
    const registry = fixtureRegistry();
    // curve_suite is harness-only; the gatherer must not be able to run it.
    await assert.rejects(
      registry.call("curve_suite", { curves: [] }, { api: CLEAN_API }, "gatherer"),
      ToolNotFoundError
    );
    // …and the harness can.
    const ok = await registry.call("curve_suite", { curves: [] }, { api: CLEAN_API }, "harness");
    assert.ok(ok.provenance.method);
  });

  test("bad arguments are rejected at the boundary, naming the tool", async () => {
    const registry = fixtureRegistry();
    await assert.rejects(
      registry.call("mnemonic_normalize", { raw: 42 }, { api: CLEAN_API }),
      (err: unknown) => {
        assert.ok(err instanceof ToolContractError);
        assert.match(err.message, /mnemonic_normalize/);
        return true;
      }
    );
  });

  test("a tool returning the wrong shape is caught before it becomes a number", async () => {
    const registry = fixtureRegistry();
    registry.register({
      name: "broken",
      description: "returns nonsense",
      inputSchema: z.object({}),
      outputSchema: z.object({ n: z.number() }),
      readOnly: true,
      callableBy: ["harness"],
      execute: async () => ({
        value: { n: "not a number" } as never,
        provenance: { tool: "broken", inputs: {}, method: "x" },
      }),
    });
    await assert.rejects(registry.call("broken", {}, { api: CLEAN_API }), ToolContractError);
  });

  test("a gate refusing without a remedy is a contract error", async () => {
    const registry = fixtureRegistry();
    registry.register({
      name: "refuses_badly",
      description: "refuses with no way forward",
      inputSchema: z.object({}),
      outputSchema: z.object({}),
      readOnly: true,
      callableBy: ["harness"],
      execute: async () => ({
        value: {},
        provenance: { tool: "refuses_badly", inputs: {}, method: "x" },
        refused: { gate: "sw-rw-provenance" as const, reason: "no Rw", remedy: "" },
      }),
    });
    await assert.rejects(registry.call("refuses_badly", {}, { api: CLEAN_API }), /remedy/);
  });
});
