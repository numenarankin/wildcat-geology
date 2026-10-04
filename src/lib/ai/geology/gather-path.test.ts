import { describe, expect, it, vi } from "vitest";
import type { UIMessage } from "ai";

/**
 * Which path the geology RESEARCHER takes on a mixed turn.
 *
 * The bug this pins: `gatherGeology` ran the corpus-only question path
 * unconditionally, so "what plays are other operators making like my Repass 2"
 * answered about a well whose own log nobody opened — while the log sat in the
 * project folder the question was asked from. Nothing in the answer showed it,
 * and nothing failed.
 *
 * It is worth a test rather than a comment because the failure is invisible from
 * every direction. The researcher returns a brief either way, the brief is full
 * of real petrophysics either way (the corpus has plenty), and only someone who
 * knew the log existed would notice it was never read.
 *
 * The two collaborators are injected, so this asserts the DECISION without a
 * model call, a corpus on disk or a Python tool server.
 */

const gatherWell = vi.fn();
const gatherQuestion = vi.fn();

vi.mock("./run", () => ({
  gatherGeologyTurn: (...args: unknown[]) => gatherWell(...args),
  runGeologyTurn: vi.fn(),
}));
vi.mock("./question", () => ({
  gatherGeologyQuestion: (...args: unknown[]) => gatherQuestion(...args),
  runGeologyQuestion: vi.fn(),
}));
vi.mock("./corpus", () => ({
  openCorpus: () => ({}),
  corpusRoot: () => "/corpus",
  Corpus: class {},
}));
vi.mock("./tool-registry", () => ({ geologyRegistry: () => ({ size: 12 }) }));
vi.mock("./gatherer-model", () => ({
  sonnetGathererModel: () => ({}),
  newGathererUsage: () => ({ calls: 0, inputTokens: 0, outputTokens: 0, cacheReadTokens: 0 }),
}));

process.env.GEOLOGY_HARNESS = "1";
const { gatherGeology } = await import("./entry");

const WELL_CONTEXT = {
  brief: "# well brief",
  state: { well: { name: "REPASS 2" } },
  timing: { stage0: 1, stage1: 2, total: 3 },
  trace: { cacheHit: false },
};
const QUESTION_CONTEXT = { brief: "# corpus brief", trace: { chunks: 3 } };

const ask = (text: string): UIMessage[] => [
  { id: "u", role: "user", parts: [{ type: "text", text }] },
];

const LOG = [{ id: "file-repass-2", name: "Repass 2.las" }];

describe("the geology researcher on a mixed turn", () => {
  it("evaluates the log when one is in the project folder", async () => {
    // The reported failure, reproduced: a play-comparison question, asked with
    // the well's log sitting in the project. The corpus alone cannot say what
    // the rock is; only the log can.
    gatherWell.mockResolvedValue(WELL_CONTEXT);
    const out = await gatherGeology({
      messages: ask("what plays are other operators making similar to my repass 2 play?"),
      folderFiles: LOG,
    });

    expect(gatherWell).toHaveBeenCalled();
    expect(gatherQuestion).not.toHaveBeenCalled();
    expect(out?.brief).toBe("# well brief");
    // The log it picked has to be the log, not whatever file sorted first.
    expect(gatherWell.mock.calls[0][0].lasPath).toBe("file-repass-2");
  });

  it("finds the log named by the page the user is standing on", async () => {
    gatherWell.mockResolvedValue(WELL_CONTEXT);
    await gatherGeology({
      messages: ask("how does this compare to the offsets?"),
      // The real shape `buildPageContext` produces; `subject.ts` parses the
      // quoted filename and the `file id:` pair out of it.
      pageContext:
        'The user is viewing the file "Repass 2.las" (file id: file-repass-2) in a project.',
    });
    expect(gatherWell).toHaveBeenCalled();
  });

  it("reads the corpus alone when there is genuinely no log", async () => {
    // The other half of the contract. "Why does the neutron read high in gas"
    // has no well in it, and running Stage 0 over nothing would be a failure,
    // not a fallback.
    gatherQuestion.mockResolvedValue(QUESTION_CONTEXT);
    const out = await gatherGeology({
      messages: ask("why does the neutron read high in gas?"),
    });

    expect(gatherQuestion).toHaveBeenCalled();
    expect(gatherWell).not.toHaveBeenCalled();
    expect(out?.brief).toBe("# corpus brief");
  });

  it("falls back to the corpus when the log cannot be evaluated", async () => {
    // Stage 0 dies if the Python tool layer is unreachable. The corpus needs
    // none of what just failed, and answering from it beats handing Opus
    // nothing about the rock at all.
    gatherWell.mockRejectedValue(new Error("tool server unreachable"));
    gatherQuestion.mockResolvedValue(QUESTION_CONTEXT);
    const out = await gatherGeology({
      messages: ask("what is my repass 2 completed in?"),
      folderFiles: LOG,
    });

    expect(out?.brief).toBe("# corpus brief");
  });

  it("returns null rather than throwing when both paths fail", async () => {
    // The standing contract for every stage in the fan-out: a missing brief
    // costs quality, a thrown one costs the answer.
    gatherWell.mockRejectedValue(new Error("stage 0 died"));
    gatherQuestion.mockRejectedValue(new Error("corpus died"));
    const out = await gatherGeology({
      messages: ask("what is my repass 2 completed in?"),
      folderFiles: LOG,
    });

    expect(out).toBeNull();
  });
});
