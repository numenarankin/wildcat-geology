/**
 * Stage 1 — fan-out, and the always-on gatherer. Phase 3 of
 * geology-agent/harness-implementation.md.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/stage1.test.ts
 *
 * What the plan says to prove:
 *   - the fan-out actually runs in parallel (assert concurrency, not just the
 *     merged result)
 *   - the gatherer runs on EVERY turn, including ones where every key resolves
 *   - its own tool calls land in the state object
 *   - no branch clobbers another's writes
 *   - chunks arrive verbatim, checked byte-for-byte against the corpus file
 *
 * The corpus under `fixtures/corpus/` is real: real markdown, a real two-level
 * TOC with real character offsets, and a real `.doc-hashes.json`. Only the
 * model's judgment is scripted.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { Corpus } from "@/lib/ai/geology/corpus";
import { gather } from "@/lib/ai/geology/gatherer";
import { fanOut } from "@/lib/ai/geology/stage1-fanout";
import { createZoneEvaluation } from "@/lib/ai/geology/state";
import type { HeaderFacts } from "@/lib/ai/geology/contracts";
import { CallCounter, CLEAN_API, fixtureRegistry } from "./fixtures/tools";
import { scriptedModel, type ScriptOptions } from "./fixtures/model";

const CORPUS_ROOT = path.join(import.meta.dirname, "fixtures", "corpus");
const KB = path.join(CORPUS_ROOT, "knowledge-base");

function corpus() {
  return new Corpus({ knowledgeBase: KB, toc: path.join(CORPUS_ROOT, "toc") });
}

const HEADER: HeaderFacts = {
  api: CLEAN_API, name: "Repass 1", operator: "Test Operator", county: "Wise", district: "09",
  kbFt: 1204, glFt: 1190, epdFt: 1204, reference: "KB",
  latitude: 33.1234, longitude: -97.6543,
  startFt: 100, stopFt: 5000, stepFt: 0.5, nullValue: -999.25,
};

function store() {
  return createZoneEvaluation({
    api: CLEAN_API, name: "Repass 1", operator: "Test Operator", county: "Wise", district: "09",
  });
}

function deps(script: ScriptOptions = {}, toolOpts: Parameters<typeof fixtureRegistry>[0] = {}) {
  return {
    registry: fixtureRegistry(toolOpts),
    corpus: corpus(),
    model: scriptedModel(script),
    ctx: { api: CLEAN_API, lasPath: "/fixtures/x.las" },
  };
}

/** `gather` needs a store to record its own tool calls into. */
function gatherDeps(script: ScriptOptions = {}, toolOpts: Parameters<typeof fixtureRegistry>[0] = {}) {
  return { ...deps(script, toolOpts), store: store() };
}

describe("the gatherer returns verbatim source text", () => {
  test("every chunk is a byte-exact slice of the corpus file", async () => {
    const result = await gather("is there pay here?", gatherDeps());
    assert.ok(result.chunks.length > 0);

    for (const chunk of result.chunks) {
      const file = await readFile(path.join(KB, chunk.section, `${chunk.slug}.md`), "utf8");
      assert.equal(
        chunk.text,
        file.slice(chunk.start, chunk.end),
        `${chunk.id} is not a verbatim slice`
      );
    }
  });

  test("the segments tile the document with no gap or overlap", async () => {
    // The coverage guarantee build_toc.py asserts, re-checked on the read side:
    // if the offsets did not tile, some of the document is unreachable and the
    // index would never say so.
    const entries = await corpus().detail("01-curve-reading", "gr-basics");
    const file = await readFile(path.join(KB, "01-curve-reading", "gr-basics.md"), "utf8");
    assert.equal(entries[0].start, 0);
    assert.equal(entries[entries.length - 1].end, file.length);
    for (let i = 1; i < entries.length; i++) {
      assert.equal(entries[i].start, entries[i - 1].end, "gap or overlap between segments");
    }
  });

  test("nothing summarizes: the text is never rewritten on the way out", async () => {
    const result = await gather("how do I pick Vsh?", gatherDeps({ segments: ["01-curve-reading/gr-basics#1"] }));
    assert.equal(result.chunks.length, 1);
    assert.match(result.chunks[0].text, /IGR = \(GR_log - GR_clean\) \/ \(GR_shale - GR_clean\)/);
  });
});

describe("the gatherer verifies what the model claims", () => {
  test("a cited document that is not in the corpus is dropped and counted", async () => {
    const result = await gather("what about coning?", gatherDeps({ documents: ["coning-basics", "not-a-real-document"] }));
    assert.deepEqual(result.dropped.unknownDocuments, ["not-a-real-document"]);
    assert.ok(result.chunks.every((c) => c.slug === "coning-basics"));
  });

  test("a segment ID that does not exist is dropped and counted", async () => {
    const result = await gather("what about coning?", gatherDeps({
      documents: ["coning-basics"],
      segments: ["04-coning/coning-basics#0", "04-coning/coning-basics#99"],
    }));
    assert.deepEqual(result.dropped.unknownSegments, ["04-coning/coning-basics#99"]);
    assert.equal(result.chunks.length, 1);
  });

  test("an empty split still gathers, using the original question", async () => {
    const result = await gather("anything?", gatherDeps({ subQuestions: [] }));
    assert.deepEqual(result.subQuestions, ["anything?"]);
    assert.ok(result.chunks.length > 0);
  });
});

describe("sub-questions fan out and merge deterministically", () => {
  test("the split is capped and each sub-question searches independently", async () => {
    const observed = { cards: [], entries: [], subQuestions: [] } as NonNullable<ScriptOptions["observed"]>;
    const result = await gather("two questions in one", {
      ...gatherDeps({ subQuestions: ["a", "b", "c", "d"], observed }),
      maxSubQuestions: 3,
    });
    assert.deepEqual(result.subQuestions, ["a", "b", "c"]);
    assert.equal(observed.cards.length, 3, "level 1 is consulted once per sub-question");
  });

  test("the same segment retrieved by two sub-questions appears once", async () => {
    const result = await gather("q", gatherDeps({
      subQuestions: ["first", "second"],
      documents: ["gr-basics"],
      segments: ["01-curve-reading/gr-basics#0"],
    }));
    assert.equal(result.chunks.length, 1);
    assert.deepEqual(result.sources, ["01-curve-reading/gr-basics#0"]);
  });

  test("level 2 is opened only for the documents level 1 selected", async () => {
    const observed = { cards: [], entries: [], subQuestions: [] } as NonNullable<ScriptOptions["observed"]>;
    await gather("coning only", gatherDeps({ documents: ["coning-basics"], observed }));
    assert.ok(observed.entries[0].every((e) => e.slug === "coning-basics"));
    assert.ok(observed.cards[0].length > 1, "level 1 still shows every card");
  });
});

describe("the fan-out runs in parallel", () => {
  test("branch intervals overlap; they are not sequenced", async () => {
    const s = store();
    const result = await fanOut(s, { prompt: "is there pay?", header: HEADER }, {
      ...deps({ delayMs: 25 }, { delayMs: 25 }),
    });

    assert.equal(result.failed.length, 0);
    assert.equal(result.timings.length, 5, "five branches");

    // Real concurrency: every branch starts before the first one finishes. A
    // sequential implementation passes a "merged result is complete" assertion
    // just as well, which is why that assertion is not the test.
    const firstEnd = Math.min(...result.timings.map((t) => t.endedAt));
    for (const t of result.timings) {
      assert.ok(t.startedAt <= firstEnd, `${t.branch} started after another branch had finished`);
    }

    // And the wall clock reflects it: the gatherer alone is 4 model hops of
    // 25ms plus reads, so a sequenced fan-out would be far longer than the
    // slowest branch.
    const span = Math.max(...result.timings.map((t) => t.endedAt)) - Math.min(...result.timings.map((t) => t.startedAt));
    const slowest = Math.max(...result.timings.map((t) => t.endedAt - t.startedAt));
    assert.ok(span < slowest * 1.5, `fan-out took ${span}ms against a slowest branch of ${slowest}ms`);
  });

  test("no branch clobbers another's writes", async () => {
    const s = store();
    await fanOut(s, { prompt: "is there pay?", header: HEADER }, deps({ delayMs: 5 }, { delayMs: 5 }));
    const snap = s.snapshot();

    assert.ok(snap.offsets.length > 0, "offsets branch");
    assert.ok(snap.computed.some((c) => c.field === "coning_critical_rate"), "calculators branch");
    assert.ok(snap.assumptions.some((a) => a.field === "basin"), "kb-lookup branch");
    assert.ok(snap.evidence.some((e) => e.sourceId.startsWith("continuity:")), "continuity branch");
    assert.ok(snap.evidence.some((e) => e.sourceId.includes("#")), "gatherer branch");
    assert.deepEqual(s.inconsistencies(), []);
  });
});

describe("the gatherer is unconditional", () => {
  test("it runs even when every dictionary key resolves", async () => {
    // The revision this replaced ran the gatherer ONLY on a key miss. A
    // dictionary hit means a name resolved; it says nothing about whether the
    // corpus holds the passage answering the question.
    const counter = new CallCounter();
    const s = store();
    const result = await fanOut(s, { prompt: "anything", header: HEADER }, deps({}, { counter }));

    assert.ok(counter.get("kb_lookup") > 0, "the keyed lookup resolved");
    assert.ok(result.gathered, "and the gatherer still ran");
    assert.ok(result.gathered.chunks.length > 0);
  });

  test("its own tool calls land in the state object", async () => {
    const counter = new CallCounter();
    const s = store();
    const result = await fanOut(
      s,
      { prompt: "what do offsets say?", header: HEADER },
      deps(
        { tools: [{ name: "offsets_within_radius", args: { latitude: 33.1, longitude: -97.6, radiusFt: 5280, limit: 5 } }] },
        { counter }
      )
    );

    assert.ok(result.gathered);
    assert.equal(result.gathered.toolResults.length, 1);
    assert.equal(result.gathered.toolResults[0].name, "offsets_within_radius");
    // Called twice: once by the gatherer's own judgment, once by the offsets
    // branch. Both are legitimate and neither blocks the other.
    assert.equal(counter.get("offsets_within_radius"), 2);
  });

  test("a tool the gatherer may not call is dropped, not thrown", async () => {
    const s = store();
    const result = await fanOut(
      s,
      { prompt: "compute something", header: HEADER },
      // curve_suite is harness-only.
      deps({ tools: [{ name: "curve_suite", args: { curves: [] } }] })
    );
    assert.equal(result.failed.length, 0);
    assert.equal(result.gathered?.toolResults.length, 0);
  });
});

describe("a failing branch does not sink the turn", () => {
  test("the fan-out completes and names what was lost", async () => {
    const s = store();
    const result = await fanOut(
      s,
      { prompt: "is there pay?", header: HEADER },
      deps({}, { failing: ["offsets_within_radius"] })
    );

    assert.deepEqual(result.failed, ["offsets"]);
    assert.ok(result.gathered, "the gatherer still ran");
    assert.ok(s.snapshot().computed.some((c) => c.field === "coning_critical_rate"), "so did the calculators");

    const item = s.snapshot().open.find((o) => o.question.includes('"offsets" failed'));
    assert.ok(item, "the loss must be surfaced, not swallowed");
    assert.equal(item.blocking, false);
  });

  test("a well with no surface location says so instead of failing", async () => {
    const s = store();
    const result = await fanOut(
      s,
      { prompt: "offsets?", header: { ...HEADER, latitude: null, longitude: null } },
      deps()
    );
    assert.deepEqual(result.failed, []);
    assert.equal(s.snapshot().offsets.length, 0);
    assert.ok(s.snapshot().open.some((o) => o.question.includes("No surface location")));
  });

  test("a truncated offset search is disclosed", async () => {
    const s = store();
    await fanOut(s, { prompt: "offsets?", header: HEADER }, deps({}, { offsetsTruncated: true }));
    assert.ok(s.snapshot().open.some((o) => o.question.includes("limit")));
  });
});

describe("offset picks are stamped with the offset's own well", () => {
  test("an offset pick never lands under the subject well", async () => {
    const s = store();
    await fanOut(s, { prompt: "offsets?", header: HEADER }, deps());
    const offset = s.snapshot().offsets[0];
    assert.equal(offset.api, "42-497-30001");
    assert.equal(offset.picks[0].depth.api, "42-497-30001");
    assert.notEqual(offset.picks[0].depth.api, CLEAN_API);
    assert.deepEqual(s.inconsistencies(), []);
  });
});
