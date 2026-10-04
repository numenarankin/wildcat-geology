/**
 * What happens when a step breaks.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/resilience.test.ts
 *
 * Every degradation in this subsystem is designed to be invisible to the
 * operator — a failed lookup is noted internally and the model works with what
 * it has — and that is exactly what makes a break hard to notice. Two things
 * therefore have to hold at once, and they pull in opposite directions:
 *
 *   1. No single failure ends the turn or costs more than itself.
 *   2. Every failure is recorded where someone looking can find it.
 *
 * The second is the one that rots quietly, so these assert the recording as
 * hard as the recovery.
 *
 * The corpus under `fixtures/corpus/` is real. Only the model's judgment is
 * scripted, and here it is scripted to fail.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { z } from "zod";
import { Corpus } from "@/lib/ai/geology/corpus";
import { gather, type GathererModel } from "@/lib/ai/geology/gatherer";
import { geologyTools } from "@/lib/ai/geology/ai-tools";
import { ToolRegistry } from "@/lib/ai/geology/registry";
import { createZoneEvaluation } from "@/lib/ai/geology/state";
import { scriptedModel } from "./fixtures/model";

const CORPUS_ROOT = path.join(import.meta.dirname, "fixtures", "corpus");

function corpus() {
  return new Corpus({
    knowledgeBase: path.join(CORPUS_ROOT, "knowledge-base"),
    toc: path.join(CORPUS_ROOT, "toc"),
  });
}

function store() {
  return createZoneEvaluation({
    api: "42-497-00001", name: "Repass 1", operator: null, county: "Wise", district: "09",
  });
}

function deps(model: GathererModel, registry = new ToolRegistry()) {
  return { corpus: corpus(), model, registry, ctx: { api: "42-497-00001" }, store: store() };
}

/** A scripted model with one hop replaced by a failure. */
function failing(hop: keyof GathererModel, only?: string): GathererModel {
  const base = scriptedModel();
  return {
    ...base,
    [hop]: async (arg: unknown, ...rest: unknown[]) => {
      if (only === undefined || arg === only) throw new Error(`${hop} timed out`);
      return (base[hop] as (...a: unknown[]) => unknown)(arg, ...rest);
    },
  } as GathererModel;
}

describe("a gatherer hop that fails", () => {
  test("splitting the question falls back to the question itself", async () => {
    // The alternative is no gather at all, over a step whose only job is to
    // decide whether one question is really two.
    const result = await gather("what is the porosity here", deps(failing("splitQuestion")));
    assert.deepEqual(result.subQuestions, ["what is the porosity here"]);
    assert.ok(result.chunks.length > 0, "the corpus was not read after a split failure");
    assert.match(result.errors.join(" "), /could not be split/);
  });

  test("costs its own sub-question and no others", async () => {
    /*
     * The failure this file exists for. `selectDocuments` runs once per
     * sub-question inside a `Promise.all`; unguarded, one 25-second Sonnet
     * timeout rejected the whole thing and threw away every passage gathered for
     * every sub-question — and the turn still produced a confident answer with
     * no library behind it.
     */
    const model = failing("selectDocuments", "second question");
    const scripted: GathererModel = {
      ...model,
      async splitQuestion() {
        return ["first question", "second question"];
      },
    };
    const result = await gather("two things", deps(scripted));

    assert.ok(result.chunks.length > 0, "the surviving sub-question lost its passages too");
    assert.equal(result.errors.length, 1);
    assert.match(result.errors[0], /second question/);
  });

  test("choosing sections is skipped, not fatal", async () => {
    const result = await gather("what is the porosity here", deps(failing("selectSegments")));
    assert.equal(result.chunks.length, 0);
    assert.match(result.errors.join(" "), /no sections chosen/);
    // Still a well-formed result: the caller must never have to guess whether
    // an empty gather was a decision or a crash.
    assert.deepEqual(result.dropped.unknownSegments, []);
    assert.ok(Array.isArray(result.sources));
  });

  test("choosing lookups is skipped, not fatal", async () => {
    const result = await gather("what is the porosity here", deps(failing("requestTools")));
    assert.ok(result.chunks.length > 0, "a failed tool choice cost the passages");
    assert.match(result.errors.join(" "), /no lookups chosen/);
  });

  test("an unreadable corpus still returns a result, and says so", async () => {
    const broken = new Corpus({ knowledgeBase: "/nonexistent", toc: "/nonexistent" });
    const result = await gather("anything", {
      ...deps(scriptedModel()),
      corpus: broken,
    });
    assert.deepEqual(result.chunks, []);
    assert.match(result.errors.join(" "), /reference index could not be opened/);
  });

  test("a healthy turn reports no errors at all", async () => {
    // The counterweight: if `errors` filled up on a clean run it would say
    // nothing when it mattered.
    const result = await gather("what is the porosity here", deps(scriptedModel()));
    assert.deepEqual(result.errors, []);
    assert.ok(result.chunks.length > 0);
  });
});

describe("a tool Fable calls that throws", () => {
  /** One tool, guaranteed to fail, registered the way a real one is. */
  function exploding(): ToolRegistry {
    const registry = new ToolRegistry();
    registry.register({
      name: "rrc_wells_near",
      description: "offsets",
      inputSchema: z.object({}),
      outputSchema: z.unknown(),
      readOnly: true,
      callableBy: ["fable"],
      async execute() {
        throw new Error("connection reset by peer");
      },
    });
    return registry;
  }

  test("comes back to the model as a fact, not as a thrown turn", async () => {
    /*
     * Thrown, this reaches the SDK and can end the run — the operator gets an
     * error where an answer should be, over one lookup that was never the whole
     * question. The rule the user set is that a tool failure is noted
     * INTERNALLY and Fable does its best with what it has.
     */
    const registry = exploding();
    const s = store();
    const tools = geologyTools(registry, { store: s, registry, ctx: { api: "x" } }, "fable");

    const out = (await tools.rrc_wells_near.execute?.({}, {} as never)) as {
      failed: boolean;
      reason: string;
      instruction: string;
    };
    assert.equal(out.failed, true);
    assert.match(out.reason, /connection reset/);
    // And the model is told what to do with it, because "do your best" is not
    // self-evident to something holding an error message.
    assert.match(out.instruction, /Do not mention it/);
    assert.match(out.instruction, /Continue with what you already have/);
  });

  test("is still recorded in the ledger, so the trace shows the attempt", async () => {
    // Swallowing the error for the model must not swallow it for us.
    const registry = exploding();
    const s = store();
    const tools = geologyTools(registry, { store: s, registry, ctx: { api: "x" } }, "fable");
    await tools.rrc_wells_near.execute?.({}, {} as never);

    const calls = s.snapshot().toolCalls;
    assert.equal(calls.length, 1);
    assert.equal(calls[0].tool, "rrc_wells_near");
    assert.equal(calls[0].ok, false);
    assert.equal(calls[0].requestedBy, "fable");
    assert.match(calls[0].error ?? "", /connection reset/);
  });
});
