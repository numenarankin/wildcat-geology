/**
 * Fable's output contract.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/fable-prompt.test.ts
 * Live: LIVE_AI_TESTS=1 node --env-file=.env --conditions=react-server --import tsx --test tests/geology/fable-prompt.test.ts
 *
 * Two requirements, from well-log-agent.md step 7 and the corpus rule:
 *
 *   SHOW THE WORK — premises leading to a conclusion, each premise grounded in
 *   the log, the user's data, the public record, a tool result, or established
 *   petrophysics. Not an assertion the operator has to take on trust.
 *
 *   NEVER CITE THE CORPUS — the reference library informs the reasoning and is
 *   invisible in the answer. Every OTHER source is named, because that is what
 *   makes a premise checkable.
 *
 * The offline tests pin the contract's structure. The live test is the one that
 * matters: it runs Fable on a real brief and reads what comes back.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { anthropic } from "@ai-sdk/anthropic";
import { generateText } from "ai";
import { FABLE_SYSTEM } from "@/lib/ai/geology/fable-prompt";
import { renderBrief } from "@/lib/ai/geology/brief";
import { Corpus } from "@/lib/ai/geology/corpus";
import { fanOut } from "@/lib/ai/geology/stage1-fanout";
import { createZoneEvaluation } from "@/lib/ai/geology/state";
import type { HeaderFacts } from "@/lib/ai/geology/contracts";
import { CLEAN_API, fixtureRegistry } from "./fixtures/tools";
import { scriptedModel } from "./fixtures/model";

const live = process.env.LIVE_AI_TESTS === "1";

describe("the prompt states the contract", () => {
  test("premises must be grounded in one of the five named kinds", () => {
    for (const kind of [
      "Something measured in the log",
      "Something in the user's own data",
      "Something in the Texas public record",
      "A calculation",
      "Established petrophysics",
    ]) {
      assert.ok(FABLE_SYSTEM.includes(kind), `the prompt does not name "${kind}" as a premise kind`);
    }
  });

  test("the corpus rule is absolute, not a preference", () => {
    assert.match(FABLE_SYSTEM, /Never name a document, author, textbook, section, equation number/);
    // The chain is required where the conclusion is contestable, NOT as a house
    // style on every answer — a retrieval question wrapped in six numbered
    // premises is a simple answer made hard to read, which is what shipped.
    // Prose is the default and the numbered chain is the exception. Shipped the
    // other way round, every answer — including "what is the porosity here" —
    // came back as a formal argument with a "The chain:" heading over it.
    assert.match(FABLE_SYSTEM, /\*\*Prose is the default\.\*\*/);
    assert.match(FABLE_SYSTEM, /Never announce the structure/);
    assert.match(FABLE_SYSTEM, /No "The chain:"/);
    assert.match(FABLE_SYSTEM, /not\s+as a way\s*\n?of showing your work/);
    assert.match(FABLE_SYSTEM, /anything that reveals a library exists/);
  });

  test("the RRC tools are named so they get reached for", () => {
    for (const tool of ["rrc_wells_near", "rrc_completion", "rrc_lease", "rrc_permits", "rrc_search", "rrc_data_vintage"]) {
      assert.ok(FABLE_SYSTEM.includes(tool), `${tool} is not mentioned`);
    }
    // The two traps carried over from Orion's own RRC guidance.
    assert.match(FABLE_SYSTEM, /internal 13 is\s+District 09/);
    assert.match(FABLE_SYSTEM, /rrc_data_vintage before treating recent months as complete/);
  });

  test("read-only and no-arithmetic are stated as rules, not hints", () => {
    assert.match(FABLE_SYSTEM, /You never write, save, or change anything/);
    assert.match(FABLE_SYSTEM, /You do not do arithmetic/);
  });

  test("the no-decisions rule is stated as a rule, banned phrasings, and a replacement", () => {
    assert.match(FABLE_SYSTEM, /You never recommend, advise, or tell the operator what to do/);
    assert.match(FABLE_SYSTEM, /I would perforate/);
    assert.match(FABLE_SYSTEM, /never hand the decision back either/i);
    assert.match(FABLE_SYSTEM, /Answer it — as OUTCOMES, not as instructions/);
  });

  test("the machinery is hidden from the answer but the method is not", () => {
    assert.match(FABLE_SYSTEM, /Never mention the machinery/);
    assert.match(FABLE_SYSTEM, /No tool names, no function calls/);
    assert.match(FABLE_SYSTEM, /Name the METHOD when it matters/);
  });

  test("tool output is framed as a claim, with flag-don't-fix", () => {
    assert.match(FABLE_SYSTEM, /Every number is a claim, not ground truth/);
    assert.match(FABLE_SYSTEM, /flag it, do not fix it/i);
    assert.match(FABLE_SYSTEM, /Do not recompute it/);
    // The failure mode this replaces: silently substituting a sensible-looking
    // number, which is the model doing arithmetic by another name.
    assert.match(FABLE_SYSTEM, /never "the tool returned an\s+invalid value"/);
  });

  test("the voice is a junior analyst, not an authority", () => {
    assert.match(FABLE_SYSTEM, /talented junior analyst/);
    assert.match(FABLE_SYSTEM, /No talking down|Talking down/);
    assert.match(FABLE_SYSTEM, /Certainty you have not earned/);
  });

});

/* ------------------------------------------------------------------ *
 * The live check: what Fable actually writes.
 * ------------------------------------------------------------------ */

const HEADER: HeaderFacts = {
  api: CLEAN_API, name: "Repass 1", operator: "Test Operator", county: "Wise", district: "09",
  kbFt: 1204, glFt: 1190, epdFt: 1204, reference: "KB",
  latitude: 33.1234, longitude: -97.6543,
  startFt: 100, stopFt: 5000, stepFt: 0.5, nullValue: -999.25,
};

const QUESTION = "Is there pay between 4,100 and 4,120 here, and would you perforate it?";

async function buildBrief(): Promise<string> {
  const store = createZoneEvaluation({
    api: CLEAN_API, name: "Repass 1", operator: "Test Operator", county: "Wise", district: "09",
  });
  store.setDatum({ stage: "stage0" }, {
    kbFt: 1204, glFt: 1190, reference: "KB", source: "LAS ~PARAMETER", resolved: true,
  });
  store.addComputed({ stage: "stage0", branch: "curve-suite" }, {
    field: "phiD", value: 0.152, unit: "v/v",
    inputs: [
      { name: "rhob", value: 2.45, source: "RHOB" },
      { name: "rhoMatrix", value: 2.71, source: "assumption:matrix_density" },
    ],
    method: "density porosity", confidence: 0.8,
  });
  const result = await fanOut(store, { prompt: QUESTION, header: HEADER }, {
    registry: fixtureRegistry(),
    corpus: new Corpus({
      knowledgeBase: path.join(import.meta.dirname, "fixtures", "corpus", "knowledge-base"),
      toc: path.join(import.meta.dirname, "fixtures", "corpus", "toc"),
    }),
    model: scriptedModel(),
    ctx: { api: CLEAN_API, lasPath: "/fixtures/x.las" },
  });
  return renderBrief({
    prompt: QUESTION,
    state: store.snapshot(),
    gathered: result.gathered,
    failedBranches: result.failed,
  });
}

describe("what Fable actually writes", { skip: !live }, () => {
  test("shows its work and never reveals the reference library", async () => {
    const brief = await buildBrief();
    const { text } = await generateText({
      model: anthropic("claude-fable-5"),
      maxOutputTokens: 6_000,
      abortSignal: AbortSignal.timeout(180_000),
      providerOptions: { anthropic: { effort: "high" } },
      system: FABLE_SYSTEM,
      messages: [{ role: "user", content: brief }],
    });

    console.log("\n----- Fable -----\n" + text + "\n-----------------\n");

    // 1. The corpus is invisible. The brief handed it `gr-basics` and
    //    `coning-basics` with their segment IDs; none of that may surface.
    for (const leak of ["gr-basics", "coning-basics", "01-curve-reading", "04-coning", "#0", "#1"]) {
      assert.ok(!text.includes(leak), `the answer leaked corpus internals: "${leak}"`);
    }
    for (const phrase of [/reference material/i, /the literature/i, /knowledge base/i, /corpus/i, /passage/i]) {
      assert.ok(!phrase.test(text), `the answer revealed the library: ${phrase}`);
    }

    // 2. The work is shown as an auditable chain, not implied by prose. Testing
    //    for connective words ("because", "since") was too weak a proxy: it
    //    passed answers that merely read like reasoning. Numbered premises and
    //    a marked conclusion are the thing actually asked for.
    const numbered = (text.match(/^\s*(?:\d+[.)]|\*\*\d+[.)])/gm) ?? []).length;
    assert.ok(numbered >= 2, `only ${numbered} numbered premises — this is prose, not a chain`);
    assert.ok(
      /premise|therefore|follows|on 1|conclusion/i.test(text),
      "the conclusion does not say which premises carry it"
    );

    // 3. Premises are grounded in sources that ARE nameable. The brief carried
    //    a curve, a computed value with its method, an assumption, and an
    //    offset well; a shown chain should reach for them by name.
    const grounded = [
      /RHOB|GR\b|caliper|curve/i,          // the log
      /2\.71|matrix/i,                      // the assumption, named as one
      /42-497-30001|offset/i,               // the public record
      /0\.15|15\.2|porosity/i,              // the computed value
    ].filter((r) => r.test(text)).length;
    assert.ok(grounded >= 3, `only ${grounded}/4 premise sources were named in the answer`);

    // 4. Assumptions are flagged as assumptions, not smuggled in as fact.
    assert.ok(/assum/i.test(text), "the matrix density assumption was not surfaced as an assumption");

    // 5. It analyzes; it does not decide. The operator owns the call, and an
    //    analysis that ends in an instruction quietly moves a completion
    //    decision onto a log reader that has seen one well.
    const DECIDES: [string, RegExp][] = [
      ["I would (not) perforate", /\bI (would|wouldn't|would not|'d)\b[^.]{0,40}\b(perforate|complete|drill|frac|stay out|pass)/i],
      ["you should / need to", /\byou (should|need to|ought to|must)\b/i],
      ["my recommendation", /\b(my|the) recommendation\b|\bI recommend\b|\bI'd recommend\b/i],
      ["imperative verdict", /^\s*\**(do not|don't|avoid|skip|go ahead)\b[^.]{0,40}(perforate|complete|it)/im],
      ["what I'd do", /what I(?:'d| would) do\b/i],
      ["not worth it", /\bnot worth (it|the)\b/i],
      // Handing the decision back is its own failure: it implies the call was
      // briefly in question, and it substitutes for doing the outcome analysis.
      ["your call", /\b(your call|your decision|up to you|the decision is yours)\b/i],
      ["you know your acreage", /\byou know (this|your) (acreage|lease|area|wells)\b/i],
    ];
    for (const [name, re] of DECIDES) {
      assert.ok(!re.test(text), `the answer made the decision for the operator: ${name}`);
    }

    // 6. The machinery stays behind the curtain. Methods are petroleum
    //    engineering and belong in the answer; tool names are plumbing.
    for (const leak of [
      "curve_suite", "hole_quality", "kb_lookup", "calculators", "continuity_check",
      "offsets_within_radius", "rrc_wells_near", "rrc_completion", "las_header",
      "tool", "Tool result",
    ]) {
      assert.ok(!text.includes(leak), `the answer exposed the machinery: "${leak}"`);
    }
    assert.ok(!/\bI ran\b|\bthe system (returned|says)\b|\bqueried\b/i.test(text), "the answer narrated its own plumbing");

    // 7. Not cocky. These are the tells from the tone that was rejected.
    for (const re of [/\bclearly\b/i, /\bobviously\b/i, /\bsimply put\b/i, /\bas you (may |might )?know\b/i]) {
      assert.ok(!re.test(text), `overconfident or condescending phrasing: ${re}`);
    }
  });
});
