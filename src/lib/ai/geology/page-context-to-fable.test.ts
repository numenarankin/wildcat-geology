import { describe, expect, it, vi } from "vitest";
import type { UIMessage } from "ai";

/**
 * Where the user is reaches Fable when the log evaluation falls through.
 *
 * The bug this pins: the page said which file was open, the resolver used it to
 * pin the log, the well path then failed (no tool server), and the fall-back
 * prompt told Fable "no log was pinned" and listed the library. Fable asked
 * which log. The knowledge existed on the server and was dropped before the
 * model. Everything but the two paths is injected, so this asserts what the
 * question path is HANDED, with no model call, corpus or tool server.
 */

const runWell = vi.fn();
const runQuestion = vi.fn();

vi.mock("./run", () => ({
  runGeologyTurn: (...args: unknown[]) => runWell(...args),
  gatherGeologyTurn: vi.fn(),
}));
vi.mock("./question", () => ({
  runGeologyQuestion: (...args: unknown[]) => runQuestion(...args),
  gatherGeologyQuestion: vi.fn(),
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
const { runGeology } = await import("./entry");

const PAGE =
  `The user is currently on the Files page (route /files/docs/tiff-1).\n\n` +
  `### They have the file "image (3).las" (LAS) open\nfile id: las-1\n` +
  `Read it with read_file, or read_las_full when the name ends in .las.`;

const ask = (text: string): UIMessage[] => [
  { id: "u", role: "user", parts: [{ type: "text", text }] },
];

describe("the question path is told where the user is", () => {
  it("hands Fable the page block and the open log when the evaluation fails", async () => {
    runWell.mockRejectedValue(new Error("las_header failed (fetch failed)"));
    runQuestion.mockResolvedValue({ result: { stream: null }, timing: {}, trace: {} });

    const out = await runGeology({
      messages: ask("analyze this log"),
      pageContext: PAGE,
      lasFiles: async () => [
        { id: "las-1", name: "image (3).las" },
        { id: "las-2", name: "Repass 2.las" },
      ],
    });

    expect(out?.kind).toBe("question");
    const handed = runQuestion.mock.calls[0][0];
    expect(handed.lasPath).toBe("las-1");
    expect(handed.pageContext).toContain('the file "image (3).las"');
    expect(handed.pageContext).toContain("file id: las-1");
  });
});
