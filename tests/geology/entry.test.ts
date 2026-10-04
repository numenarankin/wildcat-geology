/**
 * The chat route's fork — when the harness takes a turn and when it declines.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/entry.test.ts
 *
 * The important behaviour is the declining. A geology turn with no log attached,
 * an unset flag, or no tools registered all belong on Orion's existing path, and
 * every one of them must resolve to "not mine" rather than to an error — a new
 * subsystem must not be able to turn a slow answer into no answer.
 */
import { test, describe, afterEach } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import type { UIMessage } from "ai";
import { runGeology, geologyHarnessEnabled } from "@/lib/ai/geology/entry";
import { setGeologyRegistry } from "@/lib/ai/geology/tool-registry";
import {
  resolveSubject,
  subjectFromFolder,
  subjectFromHistory,
  subjectFromPageContext,
  subjectIdentity,
  isFileIdentity,
} from "@/lib/ai/geology/subject";
import { fixtureRegistry, FILE_SUBJECT_ID_ALT } from "./fixtures/tools";
import { scriptedModel } from "./fixtures/model";
import { ToolRegistry } from "@/lib/ai/geology/registry";
import { registerRrcTools } from "@/lib/ai/geology/rrc-bridge";
import { z } from "zod";

/** Judgment substituted so the routing can be exercised without an API key. */
const MODELS = { gatherer: scriptedModel(), reasoning: { answer: () => ({}) as never } };

const CORPUS_ROOT = path.join(import.meta.dirname, "fixtures", "corpus");

function userTurn(text: string): UIMessage {
  return { id: "u1", role: "user", parts: [{ type: "text", text }] } as UIMessage;
}

function lasToolTurn(fileId: string): UIMessage {
  return {
    id: "a1",
    role: "assistant",
    parts: [{ type: "tool-read_las_full", input: { fileId } }],
  } as unknown as UIMessage;
}

const PAGE_LAS = 'The user is currently on a file (route /kb). They have the file "Sky Heighten.las" (LAS) open/selected — file id: file-abc.';
const PAGE_PDF = 'They have the file "Report.pdf" (PDF) open/selected — file id: file-pdf.';
/** A log under its own file id, so these turns cannot read another test's cached evaluation. */
const PAGE_ALT_LAS = `The user is currently on a file (route /kb). They have the file "Style Check.las" (LAS) open/selected — file id: ${FILE_SUBJECT_ID_ALT}.`;

describe("finding the log this turn is about", () => {
  test("the open file wins, when it is a log", () => {
    assert.deepEqual(subjectFromPageContext(PAGE_LAS), {
      fileId: "file-abc", via: "page", name: "Sky Heighten.las",
    });
  });

  test("a non-LAS selection is not a subject", () => {
    assert.equal(subjectFromPageContext(PAGE_PDF), null);
    assert.equal(subjectFromPageContext(undefined), null);
  });

  test("the most recent LAS read in the thread, when nothing is open", () => {
    const messages = [userTurn("first"), lasToolTurn("file-1"), userTurn("second"), lasToolTurn("file-2")];
    assert.deepEqual(subjectFromHistory(messages), { fileId: "file-2", via: "history" });
  });

  test("a thread with no log read has no subject", () => {
    assert.equal(subjectFromHistory([userTurn("what does high GR mean?")]), null);
  });

  test("exactly one log in the folder resolves; two is ambiguous", () => {
    assert.equal(subjectFromFolder([{ id: "a", name: "well.las" }])?.fileId, "a");
    assert.equal(subjectFromFolder([{ id: "a", name: "a.las" }, { id: "b", name: "b.LAS" }]), null);
    assert.equal(subjectFromFolder([{ id: "a", name: "notes.pdf" }]), null);
  });

  test("the page beats history beats the folder", async () => {
    const messages = [lasToolTurn("from-history")];
    const folderFiles = [{ id: "from-folder", name: "x.las" }];
    const pick = async (input: Parameters<typeof resolveSubject>[0]) =>
      (await resolveSubject(input)).subject;
    assert.equal((await pick({ pageContext: PAGE_LAS, messages, folderFiles }))?.fileId, "file-abc");
    assert.equal((await pick({ messages, folderFiles }))?.fileId, "from-history");
    assert.equal((await pick({ messages: [], folderFiles }))?.fileId, "from-folder");
    assert.equal(await pick({ messages: [] }), null);
  });

  test("a file-scoped identity is marked as one", () => {
    // The real API comes out of the header, which has not been read yet — so
    // Stage 0 must know not to treat this as a claim about the well.
    const id = subjectIdentity({ fileId: "file-abc", via: "page" });
    assert.equal(id, "file:file-abc");
    assert.equal(isFileIdentity(id), true);
    assert.equal(isFileIdentity("42-497-31234"), false);
  });
});

/**
 * The delivery contract, which is a different thing from the reasoning contract.
 *
 * Voice reaches the harness through the same door as the drawer, but its answer
 * is read aloud. Stage 3 builds its own `streamText`, so nothing the voice route
 * layers onto its own call — VOICE_STYLE at position 0, the brevity reminder at
 * the end — can reach Fable. The suffix is the only channel, and if it silently
 * stopped arriving the failure would be a spoken answer with its headings and
 * depth markers read out, which no unit test would otherwise catch.
 *
 * Oracle: the string the caller passed, verbatim, at the END of the system
 * prompt Fable was given. Not "the prompt is longer" — the exact text, in the
 * position that makes it the last instruction.
 */
describe("the caller's style suffix reaches Fable", () => {
  const env = { ...process.env };
  const SUFFIX = "\n\nSPOKEN: plain prose, no markdown.";

  /** Captures the system prompt instead of calling the API. */
  function capturing(): { model: { answer: (s: string) => never }; system: () => string } {
    let seen = "";
    return {
      model: { answer: (s: string) => { seen = s; return {} as never; } },
      system: () => seen,
    };
  }

  afterEach(() => {
    process.env.GEOLOGY_HARNESS = env.GEOLOGY_HARNESS;
    process.env.GEOLOGY_CORPUS_ROOT = env.GEOLOGY_CORPUS_ROOT;
    setGeologyRegistry(null);
  });

  function enable() {
    process.env.GEOLOGY_HARNESS = "1";
    process.env.GEOLOGY_CORPUS_ROOT = CORPUS_ROOT;
    setGeologyRegistry(fixtureRegistry());
  }

  test("on the well path", async () => {
    enable();
    const cap = capturing();
    const r = await runGeology({
      messages: [userTurn("is there pay?")],
      pageContext: PAGE_ALT_LAS,
      styleSuffix: SUFFIX,
      models: { gatherer: scriptedModel(), reasoning: cap.model as never },
    });
    assert.equal(r?.kind, "well");
    assert.ok(cap.system().endsWith(SUFFIX), "the suffix is not the last instruction Fable read");
  });

  test("on the corpus question path", async () => {
    enable();
    const cap = capturing();
    const r = await runGeology({
      messages: [userTurn("how do I pick the clean and shale lines for Vsh?")],
      styleSuffix: SUFFIX,
      models: { gatherer: scriptedModel(), reasoning: cap.model as never },
    });
    assert.equal(r?.kind, "question");
    assert.ok(cap.system().endsWith(SUFFIX), "the suffix is not the last instruction Fable read");
  });

  test("the typed path passes none, and Fable's own contract is unchanged", async () => {
    enable();
    const cap = capturing();
    await runGeology({
      messages: [userTurn("is there pay?")],
      pageContext: PAGE_ALT_LAS,
      models: { gatherer: scriptedModel(), reasoning: cap.model as never },
    });
    assert.ok(cap.system().length > 0);
    assert.ok(!cap.system().includes("SPOKEN:"), "a delivery rule leaked into the typed path");
  });
});

describe("the fork declines cleanly", () => {
  const env = { ...process.env };
  afterEach(() => {
    process.env.GEOLOGY_HARNESS = env.GEOLOGY_HARNESS;
    process.env.GEOLOGY_CORPUS_ROOT = env.GEOLOGY_CORPUS_ROOT;
    setGeologyRegistry(null);
  });

  test("off by default", async () => {
    delete process.env.GEOLOGY_HARNESS;
    assert.equal(geologyHarnessEnabled(), false);
    assert.equal(await runGeology({ messages: [userTurn("is there pay?")], pageContext: PAGE_LAS, models: MODELS }), null);
  });

  test("a geology question with no log takes the question path, not null", async () => {
    // Without this the entire petrophysics corpus goes unused on every question
    // that is not about an attached log.
    process.env.GEOLOGY_HARNESS = "1";
    process.env.GEOLOGY_CORPUS_ROOT = CORPUS_ROOT;
    setGeologyRegistry(fixtureRegistry());
    const r = await runGeology({
      messages: [userTurn("how do I pick the clean and shale lines for Vsh?")],
      models: MODELS,
    });
    assert.ok(r);
    assert.equal(r.kind, "question");
  });

  test("no corpus configured", async () => {
    process.env.GEOLOGY_HARNESS = "1";
    // A path with no TOC. Deleting the variable is not the same test: it falls
    // back to the corpus that ships in the repo, which exists.
    process.env.GEOLOGY_CORPUS_ROOT = path.join(import.meta.dirname, "fixtures", "no-such-corpus");
    setGeologyRegistry(fixtureRegistry());
    assert.equal(await runGeology({ messages: [userTurn("is there pay?")], pageContext: PAGE_LAS, models: MODELS }), null);
  });

  test("no tools registered — the state until the catalog lands", async () => {
    process.env.GEOLOGY_HARNESS = "1";
    process.env.GEOLOGY_CORPUS_ROOT = CORPUS_ROOT;
    // Empty by construction. `null` would build the REAL registry, which is no
    // longer empty — the contract tools register whether or not anything is
    // reachable behind them.
    setGeologyRegistry(new ToolRegistry());
    assert.equal(await runGeology({ messages: [userTurn("is there pay?")], pageContext: PAGE_LAS, models: MODELS }), null);
  });

  test("a turn that throws inside the harness degrades to the corpus, not to Orion", async () => {
    process.env.GEOLOGY_HARNESS = "1";
    process.env.GEOLOGY_CORPUS_ROOT = CORPUS_ROOT;
    // The header read fails, which is Stage 0's one hard failure. Measured in
    // production as `fetch failed` when the tool layer was unreachable — and
    // that used to hand a subsurface question to Orion, which has no
    // petrophysics library at all. The corpus path needs none of what broke.
    setGeologyRegistry(fixtureRegistry({ failHeader: true }));
    const result = await runGeology({ messages: [userTurn("is there pay?")], pageContext: PAGE_LAS, models: MODELS });
    assert.equal(result?.kind, "question", "a dead tool layer still cost the whole library");
  });
});

/**
 * Resolution against the rows that actually exist.
 *
 * Both rules here were first written against what the schema said rather than
 * what the database holds, and both failed on the first real question asked of
 * the deployed harness — silently, into the no-log path, producing a confident
 * answer about a well whose log was in the project the whole time.
 *
 * So these fixtures are copied from production, duplicate uploads and wrong
 * `type` and all. Do not tidy them.
 */
describe("finding the log the way the app actually stores them", () => {
  const QUESTION = "What is the porosity in the 4109' to 4122' zone in the Repass 2 well?";
  // Test Project, verbatim: the same log uploaded twice.
  const PROJECT = [
    { id: "dup", name: "Repass 2 (1).las" },
    { id: "real", name: "Repass 2.las" },
  ];

  test("a project page with nothing selected still finds the well named in the question", async () => {
    // The reported failure. `subjectFromFolder` demanded exactly one log and
    // called two "ambiguous" — but they are the same log kept twice, and the
    // operator said which well in words.
    const { subject } = await resolveSubject({ messages: [], folderFiles: PROJECT, prompt: QUESTION });
    assert.equal(subject?.via, "folder");
    // The plain name over the "(1)" duplicate: either is right, none is wrong.
    assert.equal(subject?.name, "Repass 2.las");
  });

  test("a selected log resolves even though its stored type is `doc`", async () => {
    // `buildPageContext` prints the file's `type`, and an uploaded well log is
    // typed `doc`. The old rule required the marker "(LAS)", which therefore
    // never appeared — selecting the log did nothing at all.
    const { subject } = await resolveSubject({
      messages: [],
      pageContext: 'They have the file "Repass 2.las" (DOC) open/selected — file id: abc-123.',
      prompt: QUESTION,
    });
    assert.equal(subject?.fileId, "abc-123");
    assert.equal(subject?.via, "page");
  });

  test("a selected file that is not a log resolves to nothing", async () => {
    // The check the type marker was there to make. The filename makes it now.
    const { subject } = await resolveSubject({
      messages: [],
      pageContext: 'They have the file "scout report.pdf" (DOC) open/selected — file id: p1.',
      prompt: QUESTION,
    });
    assert.equal(subject, null);
  });

  test("several different wells and no clue is still ambiguous", async () => {
    // The case the strict rule was right about. Guessing between two unrelated
    // wells would put the wrong well's numbers in the answer.
    const { subject, candidates } = await resolveSubject({
      messages: [],
      folderFiles: [
        { id: "a", name: "Sky Heighten.las" },
        { id: "b", name: "Bell Ranch.las" },
      ],
      prompt: "what does high GR mean",
    });
    assert.equal(subject, null);
    // Ambiguous is not empty. Both come back so the no-log prompt can name them
    // instead of asserting there is no log.
    assert.equal(candidates.length, 2);
  });

  test("naming one of several wells picks that one", async () => {
    const { subject } = await resolveSubject({
      messages: [],
      folderFiles: [
        { id: "a", name: "Sky Heighten.las" },
        { id: "b", name: "Bell Ranch.las" },
      ],
      prompt: "how does the Bell Ranch log look through the Caddo?",
    });
    assert.equal(subject?.fileId, "b");
  });
});

/**
 * What happens when the log cannot be read.
 *
 * The reported failure: the Python tool server was down, Stage 0 threw `fetch
 * failed`, and a subsurface question went to Orion — which has no petrophysics
 * library at all. The corpus path needs none of what failed. Answering from the
 * library without the log is far closer to right than a general assistant
 * guessing, so that is the floor, and Orion is only reached if the floor also
 * gives way.
 */
describe("when the well path cannot run", () => {
  const FIXTURE_CORPUS = path.join(import.meta.dirname, "fixtures", "corpus");

  function env() {
    process.env.GEOLOGY_HARNESS = "1";
    process.env.GEOLOGY_CORPUS_ROOT = FIXTURE_CORPUS;
  }

  afterEach(() => {
    delete process.env.GEOLOGY_CORPUS_ROOT;
    setGeologyRegistry(null);
  });

  test("falls back to the corpus, not to Orion", async () => {
    env();
    // A registry whose LAS tools throw exactly as an unreachable tool server does.
    const registry = new ToolRegistry();
    registerRrcTools(registry);
    registry.register({
      name: "las_header",
      description: "the header",
      inputSchema: z.object({}),
      outputSchema: z.unknown(),
      readOnly: true,
      callableBy: ["harness", "gatherer", "fable"],
      async execute() {
        throw new TypeError("fetch failed");
      },
    });
    setGeologyRegistry(registry);

    const result = await runGeology({
      messages: [
        { id: "u1", role: "user", parts: [{ type: "text", text: "Does the subsea top change the picture?" }] },
      ] as UIMessage[],
      folderFiles: [{ id: "f1", name: "Repass 2.las" }],
      models: MODELS,
    });

    assert.ok(result, "the turn was handed to Orion, which has no corpus at all");
    assert.equal(result.kind, "question");
    // And the corpus was genuinely read, not just the path taken.
    assert.ok(result.kind === "question" && result.question.gathered.chunks.length > 0);
  });
});
