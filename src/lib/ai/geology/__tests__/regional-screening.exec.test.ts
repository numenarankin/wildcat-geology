/**
 * The turn this whole expansion was built for, driven through the real harness.
 *
 * Everything else proves a part: the Python tests prove the tables are anchored
 * and the tools refuse correctly, `figure-image.test.ts` proves the bridge finds
 * and reads an image, `figure-vision.exec.test.ts` proves the model can read a
 * sheet. None of them proves the thing that actually has to happen — that Fable,
 * given a screening question and a catalog with four new names in it, reaches for
 * them.
 *
 * A tool can be written, registered, catalogued and still never called, and that
 * failure is invisible from every other test. So this asks a real Bend Arch
 * screening question and asserts the ledger shows the regional layer was used.
 *
 * Needs the Python tool host, like the other harness exec suite:
 *
 *     python3 scripts/geology-tools-dev.py
 *     GEOLOGY_TOOLS_URL=http://127.0.0.1:8781 RUN_LIVE=1 npx vitest run ...
 */
import { test, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";

vi.mock("@/lib/auth/early-access", () => ({
  assertEarlyAccess: async () => {},
  hasEarlyAccess: async () => true,
}));
vi.mock("@/lib/auth/session", () => ({
  assertSignedIn: async () => ({ id: "test" }),
  requireUser: async () => ({ id: "test" }),
  getSessionUser: async () => ({ id: "test" }),
  forbidUnlessSignedIn: async () => null,
}));

const ENV = path.resolve(__dirname, "../../../../../.env");
try {
  for (const line of readFileSync(ENV, "utf8").split("\n")) {
    const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2];
  }
} catch {
  /* .env is optional; the vars may already be in the environment */
}
process.env.GEOLOGY_HARNESS ??= "1";

const skip = !process.env.GEOLOGY_TOOLS_URL || !process.env.ANTHROPIC_API_KEY;

test.skipIf(skip)(
  "a Bend Arch screening question reaches the regional lookups",
  async () => {
    const { runGeology } = await import("../entry");

    const result = await runGeology({
      messages: [
        {
          id: "1",
          role: "user",
          parts: [
            {
              type: "text",
              text:
                "I just made a good well in Archer County completed in the CADOO. " +
                "What formation is that really, how deep does it sit in Archer County, " +
                "and which other fields around there produce the same rock? " +
                "Pull up a map of it if the library has one.",
            },
          ],
        },
      ] as unknown as Parameters<typeof runGeology>[0]["messages"],
    });

    expect(result, "runGeology declined; check GEOLOGY_HARNESS and the corpus").toBeTruthy();
    expect(result!.kind).toBe("question");
    if (result!.kind !== "question") return;

    let text = "";
    for await (const part of result!.stream.textStream) text += part;
    expect(text.length, "Fable produced no answer").toBeGreaterThan(120);

    // The ledger is the evidence. `toolCalls[]` is complete by construction —
    // every call goes through `callTool` — so a regional tool missing here means
    // Fable never reached for it, whatever the answer says.
    //
    // The deterministic layer arrives under one registry name: `petrophysics` is
    // a dispatcher, and the ledger records the name Fable called, not the tool it
    // dispatched to. Reading only `c.tool` therefore shows "petrophysics" for all
    // 153 of them and proves nothing — the dispatched name is in the arguments.
    const calls = result!.question.store.snapshot().toolCalls;
    const called = new Set<string>();
    for (const call of calls) {
      called.add(call.tool);
      const args = call.args as { tool?: unknown } | null;
      if (call.tool === "petrophysics" && args && typeof args.tool === "string") {
        called.add(args.tool);
      }
    }
    const regional = [
      "formation_alias_resolve",
      "reservoir_parameter_lookup",
      "figure_search",
      "figure_fetch",
    ].filter((name) => called.has(name));

    expect(
      regional.length,
      `no regional lookup was called. Tools used: ${[...called].join(", ") || "(none)"}`
    ).toBeGreaterThan(0);

    // The specific one the question turns on: CADOO is a misspelling, and the
    // answer is wrong unless something resolved it.
    expect(
      called.has("formation_alias_resolve"),
      `formation_alias_resolve was not called. Tools used: ${[...called].join(", ")}`
    ).toBe(true);
  },
  300_000
);
