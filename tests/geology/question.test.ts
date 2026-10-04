/**
 * The no-log geology path.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/question.test.ts
 *
 * A 66-document petrophysics corpus mostly answers questions that are not about
 * one well. This path is what stops those falling through to a general
 * assistant with no corpus — and what stops the answer inventing a well to hang
 * numbers on.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { Corpus } from "@/lib/ai/geology/corpus";
import { runGeologyQuestion } from "@/lib/ai/geology/question";
import { FABLE_QUESTION_SYSTEM, FABLE_SYSTEM } from "@/lib/ai/geology/fable-prompt";
import type { ReasoningModel } from "@/lib/ai/geology/stage3-reason";
import { fixtureRegistry } from "./fixtures/tools";
import { scriptedModel, type ScriptOptions } from "./fixtures/model";

const CORPUS_ROOT = path.join(import.meta.dirname, "fixtures", "corpus");
const QUESTION = "How do I pick the clean and shale lines for Vsh?";

function seen() {
  return { systems: [] as string[], briefs: [] as string[] };
}

function reasoning(rec: ReturnType<typeof seen>): ReasoningModel {
  return {
    answer(system, messages) {
      rec.systems.push(system);
      rec.briefs.push(String((messages.at(-1) as { content: string }).content));
      return {} as never;
    },
  };
}

function deps(script: ScriptOptions = {}, rec = seen()) {
  return {
    corpus: new Corpus({
      knowledgeBase: path.join(CORPUS_ROOT, "knowledge-base"),
      toc: path.join(CORPUS_ROOT, "toc"),
    }),
    gatherer: scriptedModel(script),
    registry: fixtureRegistry(),
    reasoning: reasoning(rec),
  };
}

describe("it answers from the corpus", () => {
  test("verbatim passages reach the brief with their citable IDs", async () => {
    const rec = seen();
    const q = await runGeologyQuestion({ prompt: QUESTION }, deps({
      documents: ["gr-basics"],
      segments: ["01-curve-reading/gr-basics#1"],
    }, rec));

    assert.equal(q.trace.chunks, 1);
    assert.deepEqual(q.trace.sources, ["01-curve-reading/gr-basics#1"]);
    assert.match(rec.briefs[0], /\[01-curve-reading\/gr-basics#1\]/);
    assert.match(rec.briefs[0], /IGR = \(GR_log - GR_clean\)/);
  });

  test("the brief says there is no well rather than showing an empty one", async () => {
    const rec = seen();
    await runGeologyQuestion({ prompt: QUESTION }, deps({}, rec));
    assert.match(rec.briefs[0], /# Context for this question/);
    assert.match(rec.briefs[0], /No well log is in scope/);
    assert.ok(!rec.briefs[0].includes("## Well"), "an empty well block reads as a gap");
    assert.ok(!rec.briefs[0].includes("Datum:"));
  });

  test("Fable gets the no-log contract, and it is otherwise the same one", async () => {
    const rec = seen();
    await runGeologyQuestion({ prompt: QUESTION }, deps({}, rec));
    assert.equal(rec.systems[0], FABLE_QUESTION_SYSTEM);
    assert.match(rec.systems[0], /NO well log in scope/);
    assert.match(rec.systems[0], /Never invent a well, a depth, a curve reading/);
    // Same premise rules, same corpus invisibility, same no-decisions rule.
    for (const rule of [
      "Something measured in the log",
      "Never name a document, author, textbook, section, equation number",
      "You never recommend, advise, or tell the operator what to do",
      "talented junior analyst",
    ]) {
      assert.ok(rec.systems[0].includes(rule), `the question variant dropped: ${rule}`);
    }
    assert.notEqual(rec.systems[0], FABLE_SYSTEM);
  });
});

describe("the gatherer decides what to look up", () => {
  test("nothing fires automatically", async () => {
    // The well path has a floor of five branches. A question has none: "what is
    // the Archie exponent for a vuggy carbonate" needs no offset query.
    const q = await runGeologyQuestion({ prompt: QUESTION }, deps());
    assert.equal(q.trace.toolCalls, 0);
  });

  test("a lookup the gatherer asks for runs and is recorded", async () => {
    const q = await runGeologyQuestion({ prompt: "who else is drilling near 33.1, -97.6?" }, deps({
      tools: [{ name: "offsets_within_radius", args: { latitude: 33.1, longitude: -97.6, radiusFt: 5280, limit: 5 } }],
    }));
    assert.equal(q.trace.toolCalls, 1);
  });
});

describe("gaps are still disclosed", () => {
  test("a hallucinated citation is dropped and surfaced", async () => {
    const rec = seen();
    const q = await runGeologyQuestion({ prompt: QUESTION }, deps({
      documents: ["gr-basics", "no-such-doc"],
    }, rec));
    assert.equal(q.trace.droppedCitations, 1);
    assert.match(rec.briefs[0], /"no-such-doc", which is not in the corpus/);
  });

  test("a question the corpus cannot answer still produces a turn", async () => {
    const q = await runGeologyQuestion({ prompt: "what is the weather" }, deps({ documents: [] }));
    assert.equal(q.trace.chunks, 0);
    assert.ok(q.result.stream, "an empty corpus result must not cancel the answer");
  });
});
