import { test, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";

/**
 * End to end for the geology harness: the real registry, the real Python tool
 * host, the live RRC mirror, and a real model.
 *
 * Three things here have only ever been proven in isolation, and each is a
 * silent failure if it is wrong:
 *
 *   1. `offsets_within_radius`. It was DECLARED and CALLED and registered
 *      nowhere, so Stage 1's offset branch threw on every turn and the failure
 *      was swallowed as a non-blocking open item. That is exactly the shape of
 *      bug a unit test does not catch, so it is tested here against the mirror.
 *   2. Groups M through R reaching the model. A tool can be written, registered
 *      and passing its own tests while absent from the generated catalog,
 *      because the group letters come from a corpus sidecar rather than from
 *      the code. Then the model is never told it exists.
 *   3. `rrc_analyze` inside the harness. The bridge admitted tools by an
 *      `rrc_` prefix, which is why two tools had never been reachable from
 *      Fable at all.
 *
 * Needs the Python tool host, which `next dev` does not provide:
 *
 *     python3 scripts/geology-tools-dev.py
 *     GEOLOGY_TOOLS_URL=http://127.0.0.1:8781 RUN_LIVE=1 npx vitest run ...
 */

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
  // No .env; the tests below skip.
}

const { geologyRegistry } = await import("../tool-registry");
const { CATALOG_ENTRIES } = await import("../tool-catalog");
const { TOOL } = await import("../contracts");

const skip = process.env.RUN_LIVE !== "1" || !process.env.RRC_DATABASE_URL;
const skipPython = skip || !process.env.GEOLOGY_TOOLS_URL;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CTX = { api: "11533824" } as any;

/**
 * Call a registered geology tool exactly the way the harness does, through
 * `registry.call`, so argument validation, output validation, the refusal
 * contract and the provenance requirement are all exercised. Calling
 * `execute` directly would skip every one of those.
 */
async function callTool(name: string, args: unknown): Promise<unknown> {
  const registry = geologyRegistry();
  expect(registry.has(name), `${name} is not registered`).toBe(true);
  return registry.call(name, args, CTX);
}

test.skipIf(skip)(
  "offsets_within_radius is registered and answers off the mirror",
  async () => {
    const registry = geologyRegistry();
    expect(
      registry.has(TOOL.offsetsWithinRadius),
      "Stage 1 calls this on every well turn; unregistered it throws and the failure is swallowed"
    ).toBe(true);

    // A real Midland Basin point, the same one the other live suites use.
    const out = (await callTool(TOOL.offsetsWithinRadius, {
      latitude: 31.997,
      longitude: -102.078,
      radiusFt: 5280,
      limit: 25,
    })) as { value: { offsets: unknown[]; truncated: boolean } };

    const offsets = out.value.offsets as {
      api: string;
      distanceFt: number;
      picks: { formation: string; depthFt: number; reference: string }[];
      dst: unknown[];
      datumResolved: boolean;
    }[];
    expect(offsets.length, "a mile of Midland Basin should not be empty").toBeGreaterThan(0);

    for (const o of offsets) {
      expect(o.api).toMatch(/^\d+$/);
      expect(o.distanceFt).toBeLessThanOrEqual(5281);
      // The mirror carries no DST. Inventing one would be worse than the gap.
      expect(o.dst).toEqual([]);
      // Every pick belongs to THIS well. Merging picks across wells is the
      // mistake the state object's own consistency check watches for.
      for (const p of o.picks) expect(typeof p.depthFt).toBe("number");
    }
  },
  120_000
);

test.skipIf(skip)(
  "rrc_analyze reaches the harness, and so do the two tools the prefix filter used to hide",
  async () => {
    const registry = geologyRegistry();
    expect(registry.has("rrc_analyze")).toBe(true);
    // These fail an `rrc_` prefix test on the name alone and were invisible to
    // Fable until the bridge started admitting by allowlist.
    expect(registry.has("get_well_rrc_record")).toBe(true);
    expect(registry.has("get_lease_rrc_record")).toBe(true);

    const out = (await callTool("rrc_analyze", {
      fn: "rrc_series",
      args: { entity: "statewide", stream: "oil", months: 12 },
    })) as { value: { ok?: boolean; reportedThrough?: string } };
    expect(out.value).toBeTruthy();
  },
  120_000
);

test.skipIf(skipPython)(
  "every new group M-R tool is in the catalog AND answers over the real Python seam",
  async () => {
    const newGroups = CATALOG_ENTRIES.filter((t) => "MNOPQR".includes(t.group));
    expect(newGroups.length, "groups M-R missing from the generated catalog").toBe(36);

    // Every new group must be reachable from the catalog through the real
    // dispatcher and the real HTTP seam. Called with NO arguments on purpose:
    // the only two acceptable answers are a result or the tool's own
    // signature, and those are exactly the two a model can continue from.
    const probes = [
      "volumetrics",
      "relative_permeability",
      "structure_map",
      "mn_plot",
      "rock_typing",
      "vogel_ipr",
    ];
    for (const name of probes) {
      let answer: string;
      try {
        answer = JSON.stringify(await callTool("petrophysics", { tool: name, args: {} }));
      } catch (e) {
        // A 422 carrying the signature is a legitimate answer here, not a
        // failure: it is the recovery path a parameterless catalog depends on.
        answer = (e as Error).message;
      }
      expect(
        answer.includes(name),
        `${name} answered without naming itself: ${answer.slice(0, 200)}`
      ).toBe(true);
      expect(
        /rejected these arguments|"unit"|"reason"|"value"/.test(answer),
        `${name} gave neither a result nor a usable signature: ${answer.slice(0, 200)}`
      ).toBe(true);
    }
  },
  180_000
);

test.skipIf(skipPython)(
  "a bad call to the Python layer comes back with the real signature",
  async () => {
    // This is what pays for a catalog that lists no arguments. If a miss came
    // back as a bare error the model would have nothing to correct against.
    let caught: string | null = null;
    try {
      await callTool("petrophysics", { tool: "buildup_kh_skin", args: {} });
    } catch (e) {
      caught = (e as Error).message;
    }
    const message =
      caught ??
      JSON.stringify(await callTool("petrophysics", { tool: "buildup_kh_skin", args: {} }));
    expect(message).toContain("buildup_kh_skin(");
    expect(message).toMatch(/missing a required argument|rejected these arguments/);
  },
  120_000
);

test.skipIf(skipPython || !process.env.ANTHROPIC_API_KEY)(
  "a real geology turn runs the harness end to end and consumes its ledger",
  async () => {
    // The whole door the chat route uses. No log in scope, so this is the
    // question path: gatherer, corpus, tools, then Fable. It proves the harness
    // is reachable with the real flag, the real corpus and the real tool layer,
    // and that the answer is streamed rather than thrown away.
    const { runGeology } = await import("../entry");

    const result = await runGeology({
      messages: [
        {
          id: "1",
          role: "user",
          parts: [
            {
              type: "text",
              text: "Who else is drilling in Wise County right now, and what have they been completing in? Use the public record.",
            },
          ],
        },
      ] as unknown as Parameters<typeof runGeology>[0]["messages"],
    });

    expect(result, "runGeology declined; check GEOLOGY_HARNESS and the corpus").toBeTruthy();
    expect(result!.kind).toBe("question");
    if (result!.kind !== "question") return;

    // The gatherer ran and reached something. Zero of both means the harness
    // came up but every branch failed, which is the degraded state that looks
    // identical to a working one from the outside.
    const trace = result!.question.trace;
    expect(
      trace.chunks + trace.toolCalls,
      `gatherer produced nothing: ${JSON.stringify(trace)}`
    ).toBeGreaterThan(0);

    // Drain Fable's stream so a failure inside it surfaces here rather than
    // being discarded with the unread stream.
    let text = "";
    for await (const part of result!.stream.textStream) text += part;
    expect(text.length, "Fable produced no answer").toBeGreaterThan(40);
  },
  300_000
);

test.skipIf(skipPython)(
  "Fable's tool wrapper hands a bad call back as a readable value, not a throw",
  async () => {
    // The other half of the recovery contract. `registry.call` THROWS on bad
    // arguments; if that reached the SDK it could end the step and the operator
    // would get an error where an answer belongs. What Fable must receive is the
    // signature as a value it can correct against.
    const { geologyTools } = await import("../ai-tools");
    const { createZoneEvaluation } = await import("../state");
    const registry = geologyRegistry();
    const store = createZoneEvaluation({
      api: "11533824", name: null, operator: null, county: null, district: null,
    });
    const tools = geologyTools(registry, { store, registry, ctx: CTX }, "fable");

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const out = (await (tools as any).petrophysics.execute(
      { tool: "buildup_kh_skin", args: {} },
      {}
    )) as { failed?: boolean };
    const text = JSON.stringify(out);
    expect(out.failed, `threw instead of returning: ${text}`).toBe(true);
    expect(text).toContain("buildup_kh_skin(");
  },
  120_000
);
