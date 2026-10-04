/**
 * The whole turn: Stage 0 -> 1 -> 2 -> 3.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/run.test.ts
 * Live: LIVE_AI_TESTS=1 node --env-file=.env --conditions=react-server --import tsx --test tests/geology/run.test.ts
 *
 * The offline pass asserts the harness: ordering, routing, what lands in the
 * state object, and that nothing short of a failed parse can end the turn. The
 * models are scripted; the harness is real.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { Corpus } from "@/lib/ai/geology/corpus";
import { MemoryEvaluationCache } from "@/lib/ai/geology/cache";
import { runGeologyTurn } from "@/lib/ai/geology/run";
import type { ReasoningModel } from "@/lib/ai/geology/stage3-reason";
import { CLEAN_API, DATUM_FIGHT_API, fixtureRegistry } from "./fixtures/tools";
import { scriptedModel, type ScriptOptions } from "./fixtures/model";

const CORPUS_ROOT = path.join(import.meta.dirname, "fixtures", "corpus");
const STAMPS = { las: "hash-1", rrc: "rrc-1", facts: "facts-1" };
const QUESTION = "Is there pay between 4,100 and 4,120, and what rate would it make?";

/**
 * Scripted reasoning. Records what Fable was shown.
 *
 * `streamText` is lazy, so a test that only inspected the returned stream would
 * pass without the model ever being called — this seam is what makes the
 * hand-off assertable.
 */
function scriptedReasoning(seen: { answers: string[]; systems: string[] }) {
  const model: ReasoningModel = {
    answer(system, messages) {
      seen.systems.push(system);
      seen.answers.push(String((messages.at(-1) as { content: string }).content));
      // Never consumed by these tests; the harness only passes it through.
      return { system } as never;
    },
  };
  return model;
}

function deps(opts: {
  script?: ScriptOptions;
  tools?: Parameters<typeof fixtureRegistry>[0];
  reasoning?: ReasoningModel;
} = {}) {
  return {
    registry: fixtureRegistry(opts.tools ?? {}),
    cache: new MemoryEvaluationCache(),
    corpus: new Corpus({
      knowledgeBase: path.join(CORPUS_ROOT, "knowledge-base"),
      toc: path.join(CORPUS_ROOT, "toc"),
    }),
    gatherer: scriptedModel(opts.script ?? {}),
    reasoning: opts.reasoning ?? scriptedReasoning({ answers: [], systems: [] }),
  };
}

const input = (api = CLEAN_API, prompt = QUESTION) => ({
  prompt, api, lasPath: `/fixtures/${api}.las`, stamps: STAMPS,
});

describe("a clean turn takes the standard path", () => {
  test("every stage runs and the answer streams", async () => {
    const turn = await runGeologyTurn(input(), deps());

    // Stage 0 landed.
    assert.equal(turn.state.well.api, CLEAN_API);
    assert.equal(turn.state.datum.resolved, true);
    assert.ok(turn.state.curves.length > 0);
    // Stage 1 landed.
    assert.ok(turn.trace.chunks > 0, "the gatherer returned nothing");
    assert.ok(turn.state.offsets.length > 0);
    // And the brief carries the lot.
    assert.match(turn.brief, /## What this question requires/);
    assert.match(turn.brief, /## Tools that ran/);
  });

  test("the gatherer runs on every turn, and its passages are in the brief", async () => {
    const turn = await runGeologyTurn(input(), deps());
    assert.ok(turn.trace.subQuestions.length > 0);
    assert.match(turn.brief, /## Knowledge base passages/);
  });

  test("a second turn on the same well hits the Stage 0 cache", async () => {
    const d = deps();
    await runGeologyTurn(input(), d);
    const second = await runGeologyTurn(input(), d);
    assert.equal(second.trace.cacheHit, true);
    assert.equal(second.trace.missReason, null);
  });
});

describe("conflicts are noted, not routed", () => {
  test("a conflict proved in code reaches Fable in the brief", async () => {
    // The datum-fight fixture disagrees between the LAS and the RRC record.
    // There is no escalated path any more: the contradiction is context.
    const turn = await runGeologyTurn(input(DATUM_FIGHT_API), deps());
    assert.ok(turn.trace.conflicts > 0);
    assert.match(turn.brief, /## Conflicts/);
    assert.match(turn.brief, /Datum disagreement/);
  });

  test("the gatherer's own notes land as conflicts", async () => {
    const turn = await runGeologyTurn(
      input(),
      deps({
        script: {
          conflictNotes: [
            "CONFLICT",
            "what: two readings of the perforated interval",
            "side: 4110-4118 per the completion report",
            "side: 4102-4110 per the scout card",
            "resolves: unknown",
          ].join("\n"),
        },
      })
    );
    assert.equal(turn.trace.conflicts, 1);
    assert.match(turn.brief, /two readings of the perforated interval/);
  });

  test("a note-taker that fails does not stop the turn", async () => {
    const turn = await runGeologyTurn(input(), deps({ script: { failConflictNotes: true } }));
    assert.match(turn.trace.conflictNoteError ?? "", /note-taker unavailable/);
    assert.ok(turn.result.stream, "the turn must still answer");
  });

  test("there is one Fable call and no personas", async () => {
    const seen = { answers: [] as string[], systems: [] as string[] };
    await runGeologyTurn(input(DATUM_FIGHT_API), deps({ reasoning: scriptedReasoning(seen) }));
    assert.equal(seen.answers.length, 1, "exactly one model answers the operator");
    assert.match(seen.answers[0], /## Conflicts/);
  });
});

describe("nothing short of a failed parse ends the turn", () => {
  test("a failed fan-out branch still produces an answer", async () => {
    const turn = await runGeologyTurn(input(), deps({ tools: { failing: ["offsets_within_radius"] } }));
    assert.deepEqual(turn.trace.failedBranches, ["offsets"]);
    assert.ok(turn.result.stream, "the turn must still answer");
    assert.match(turn.brief, /the offsets branch failed/);
  });

  test("a missing required number is reported, not fatal", async () => {
    const turn = await runGeologyTurn(input(), deps({ tools: { failing: ["calculators"] } }));
    assert.ok(turn.trace.missingRequirements.length > 0);
    assert.match(turn.brief, /NOT AVAILABLE/);
    assert.ok(turn.result.stream);
  });

  test("a failed LAS parse is the one hard failure", async () => {
    await assert.rejects(
      runGeologyTurn(input(), deps({ tools: { failHeader: true } })),
      /LAS header unreadable/
    );
  });
});

describe("ordering and observability", () => {
  test("Stage 1 starts on the header, not on the full parse", async () => {
    // With every tool slowed equally, a run that waited for Stage 0 to finish
    // before starting Stage 1 would take about twice as long as one that did
    // not. Assert the overlap directly instead of timing it.
    const turn = await runGeologyTurn(input(), deps({ tools: { delayMs: 20 } }));
    const stage0Calls = turn.state.toolCalls.filter((c) => c.origin.stage === "stage0");
    const stage1Calls = turn.state.toolCalls.filter((c) => c.origin.stage === "stage1");
    assert.ok(stage0Calls.length > 1 && stage1Calls.length > 0);
    // Stage 1 writes are interleaved with Stage 0's, not appended after them.
    const lastStage0 = Math.max(...stage0Calls.map((c) => c.seq));
    const firstStage1 = Math.min(...stage1Calls.map((c) => c.seq));
    assert.ok(firstStage1 < lastStage0, "Stage 1 did not start until Stage 0 had finished");
  });

  test("the trace carries what the latency budget needs", async () => {
    const turn = await runGeologyTurn(input(), deps());
    for (const k of ["stage0", "stage1", "total"] as const) {
      assert.equal(typeof turn.timing[k], "number");
    }
    assert.equal(typeof turn.trace.implausible, "number");
  });

  test("the tool ledger records who asked for each call", async () => {
    const turn = await runGeologyTurn(
      input(),
      deps({ script: { tools: [{ name: "rrc_completion_record", args: {} }] } })
    );
    const requesters = new Set(turn.state.toolCalls.map((c) => c.requestedBy));
    assert.ok(requesters.has("harness"));
    assert.ok(requesters.has("gatherer"));
  });
});
