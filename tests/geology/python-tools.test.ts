/**
 * The Python tool layer, from the harness's side of the boundary.
 *
 * Two things are worth proving and they are different. The first is that the
 * catalog Fable reads describes the functions that actually exist — a generated
 * artefact can go stale in the repository without anything failing. The second
 * is that a LAS posted from TypeScript comes back with the values that are
 * written in the file, which is the only check that covers the whole seam:
 * `python-tools.ts`, the HTTP hop, `api/geology.py`, and the parser under it.
 *
 * The oracle for the second is the fixture's own header lines, read by eye:
 *
 *     WELL.  SKY HEIGHTEN # 1     EKB .F  1139.5
 *     COMP.  SKY RESOURCES, INC   EGL .F  1129.0
 *     CNTY.  STEPHENS             STRT.F  212.00000
 *     API .  42429368250000       STOP.F  3674.00000
 *
 * Not what the parser returns — what the file says. A test that asks the parser
 * what the parser thinks proves nothing about either.
 */
import assert from "node:assert/strict";
import { spawn, type ChildProcess } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { after, before, describe, test } from "node:test";
import { CATALOG_ENTRIES, PETROPHYSICS_CATALOG, findTool } from "@/lib/ai/geology/tool-catalog";
import { registerPythonTools, resolveDispatch, toolServiceUrl } from "@/lib/ai/geology/python-tools";
import { ToolRegistry } from "@/lib/ai/geology/registry";

const REPO = path.resolve(import.meta.dirname, "../..");
const FIXTURE = path.join(REPO, "tests/geology/fixtures/sky-heighten-1-stephens-tx-2013.las");
const PORT = 8787;

describe("the generated catalog", () => {
  test("describes 100+ tools, each with a name, a summary and a signature", () => {
    assert.ok(CATALOG_ENTRIES.length > 100, `only ${CATALOG_ENTRIES.length} tools in the catalog`);
    for (const tool of CATALOG_ENTRIES) {
      assert.match(tool.name, /^[a-z][a-z0-9_]*$/, `${tool.name} is not a tool name`);
      assert.ok(tool.summary.length > 10, `${tool.name} has no usable summary`);
      assert.ok(tool.signature.startsWith("("), `${tool.name} has no signature`);
      assert.ok(tool.module.startsWith("tools."), `${tool.name} names no module`);
    }
  });

  test("omits the tools the dispatcher will not run", () => {
    // Listed, the model would try them; each attempt costs a round trip to learn
    // what leaving them out says for free. `dispatch.py` holds the same list.
    for (const name of ["las_parse", "export_las", "export_sheet", "sensitivity_sweep"]) {
      assert.equal(findTool(name), undefined, `${name} should not be in the catalog`);
    }
  });

  test("names every argument, required and optional, with its type", () => {
    /*
     * The first catalog listed required NAMES only. That cost a wasted model
     * step every time a tool took an optional argument — `datum_resolve` takes
     * `header` and the model sent `las_header`, `subsea_convert` takes `kb` and
     * it sent `reference_elevation_ft`. Neither was on the list, so neither was
     * guessable, and four such calls failed in one measured turn.
     */
    const datum = findTool("datum_resolve");
    assert.ok(datum);
    assert.ok(datum.optional.some((p) => p.startsWith("header:")), "header is not advertised");

    const subsea = findTool("subsea_convert");
    assert.ok(subsea);
    assert.deepEqual(subsea.required, ["tvd: num"]);
    assert.ok(subsea.optional.some((p) => p.startsWith("kb:")), "kb is not advertised");

    // Every entry carries a type, or the model is guessing again.
    for (const tool of CATALOG_ENTRIES) {
      for (const p of [...tool.required, ...tool.optional]) {
        assert.match(p, /^[a-z_][\w]*: (num|int|str|bool|obj|any)(\[\])*(\[\])?\??$/, `${tool.name}: "${p}" is not a typed parameter`);
      }
    }
  });

  test("advertises the parsed-log signature for the path-taking tools", () => {
    // `las_validate` is specified against a file path. The function reaches it
    // through `validate_parsed`, hydrating the LAS from the posted text, so the
    // catalog must not tell the model to pass a path it does not have.
    const validate = findTool("las_validate");
    assert.ok(validate);
    assert.equal(validate.required.some((p) => p.startsWith("path:")), false, "still advertising a file path");
    assert.equal(validate.required.length, 0, "the log itself is not an argument the model passes");
  });

  test("the catalog still names every calculation", () => {
    // The listing no longer goes in Fable's prompt — the calculations are
    // registered tools with generated schemas now — but it is still what the
    // generator produces and what the schemas are built from, so a tool missing
    // from it is a tool nobody can call.
    assert.ok(PETROPHYSICS_CATALOG.includes("archie_sw"), "the saturation tool is not listed");
  });
});

describe("where the tool layer is", () => {
  const saved = { url: process.env.GEOLOGY_TOOLS_URL, vercel: process.env.VERCEL_URL };
  after(() => {
    process.env.GEOLOGY_TOOLS_URL = saved.url;
    process.env.VERCEL_URL = saved.vercel;
  });

  test("deployed, it is this same app", () => {
    delete process.env.GEOLOGY_TOOLS_URL;
    process.env.VERCEL_URL = "wildcat-abc123.vercel.app";
    // The per-deployment host, not production's: a preview must reach its own
    // tools, or a tool change can never be tested before it ships.
    assert.equal(toolServiceUrl(), "https://wildcat-abc123.vercel.app/api/geology");
  });

  test("locally, it is the dev server", () => {
    delete process.env.GEOLOGY_TOOLS_URL;
    delete process.env.VERCEL_URL;
    assert.equal(toolServiceUrl(), "http://127.0.0.1:8781/api/geology");
  });

  test("an override may name the origin or the route", () => {
    process.env.GEOLOGY_TOOLS_URL = "http://127.0.0.1:9000";
    assert.equal(toolServiceUrl(), "http://127.0.0.1:9000/api/geology");
    process.env.GEOLOGY_TOOLS_URL = "http://127.0.0.1:9000/api/geology";
    assert.equal(toolServiceUrl(), "http://127.0.0.1:9000/api/geology");
  });
});

describe("what gets registered", () => {
  test("four tools, all read-only, and the dispatcher is the HARNESS's alone", () => {
    const registry = new ToolRegistry();
    assert.equal(registerPythonTools(registry), 4);
    for (const tool of registry.listFor("fable")) assert.equal(tool.readOnly, true);

    /*
     * The dispatcher is no longer Fable's.
     *
     * Its `args` is a free-form record, which is exactly the hole the generated
     * schemas close: Fable called `matrix_density_sensitivity` with `matrices`
     * and `density_porosity` with no `lithology`, and nothing could refuse
     * either until Python did. Leaving the dispatcher in Fable's reach would
     * have kept an unenforced way to make the same call.
     *
     * The harness keeps it because its branches call by name from code, where
     * there is no decoding to constrain.
     */
    assert.ok(registry.listFor("harness").some((t) => t.name === "petrophysics"));
    assert.equal(
      registry.listFor("fable").some((t) => t.name === "petrophysics"),
      false,
      "Fable can still reach the unenforced dispatcher"
    );
    // And the gatherer never could: it writes `name key=value` lines, which is
    // useless for a dispatcher whose first argument is another tool's name.
    assert.equal(
      registry.listFor("gatherer").some((t) => t.name === "petrophysics"),
      false,
      "the gatherer can reach a dispatcher it cannot address"
    );
  });

  test("registering twice does not throw on the duplicate", () => {
    const registry = new ToolRegistry();
    assert.equal(registerPythonTools(registry), 4);
    assert.equal(registerPythonTools(registry), 0);
  });
});

/**
 * The whole seam, against a real log.
 *
 * `next dev` runs no Python, so the dev server stands in for the deployed
 * function — the same handler, on a port. Skipped rather than failed where
 * python3 is absent: this suite has to run on a machine that only builds the
 * TypeScript.
 */
describe("a real LAS through the whole path", () => {
  let server: ChildProcess | null = null;
  const savedUrl = process.env.GEOLOGY_TOOLS_URL;

  before(async () => {
    process.env.GEOLOGY_TOOLS_URL = `http://127.0.0.1:${PORT}`;
    server = spawn("python3", [path.join(REPO, "scripts/geology-tools-dev.py")], {
      env: { ...process.env, GEOLOGY_TOOLS_PORT: String(PORT) },
      stdio: "ignore",
    });
    server.on("error", () => {
      server = null;
    });
    // Import costs a beat; poll rather than sleep a guessed interval.
    for (let i = 0; i < 60 && server; i++) {
      try {
        const res = await fetch(`http://127.0.0.1:${PORT}/api/geology`);
        if (res.ok) return;
      } catch {
        await new Promise((r) => setTimeout(r, 250));
      }
    }
  });

  after(() => {
    server?.kill();
    process.env.GEOLOGY_TOOLS_URL = savedUrl;
  });

  async function reachable(): Promise<boolean> {
    try {
      return (await fetch(`http://127.0.0.1:${PORT}/api/geology`)).ok;
    } catch {
      return false;
    }
  }

  /** Stands in for the Supabase read. The parse is what is under test. */
  const readLas = async () => ({
    name: "sky-heighten-1-stephens-tx-2013.las",
    text: readFileSync(FIXTURE, "latin1"),
  });

  test("the header comes back with the values written in the file", async (t) => {
    if (!(await reachable())) return t.skip("no python3 tool layer on this machine");
    const registry = new ToolRegistry();
    registerPythonTools(registry, readLas);
    const { value } = await registry.call("las_header", {}, {
      api: "42-429-36825",
      lasPath: "file:fixture",
    });
    const header = value as Record<string, unknown>;

    assert.equal(header.name, "SKY HEIGHTEN # 1");
    assert.equal(header.operator, "SKY RESOURCES, INC");
    assert.equal(header.county, "STEPHENS");
    assert.equal(header.api, "42429368250000");
    assert.equal(header.kbFt, 1139.5);
    assert.equal(header.glFt, 1129);
    assert.equal(header.startFt, 212);
    assert.equal(header.stopFt, 3674);
    // The file declares an EKB, so KB is the reference it supports. Nothing else
    // in the file could establish one, and guessing is how a depth ends up hung
    // on the wrong datum.
    assert.equal(header.reference, "KB");
  });

  test("an unknown mnemonic is flagged, never guessed", async (t) => {
    if (!(await reachable())) return t.skip("no python3 tool layer on this machine");
    const registry = new ToolRegistry();
    registerPythonTools(registry, readLas);
    const ctx = { api: "42-429-36825" };

    // GRD is in this log and is not in the dictionary. A null canonical is the
    // answer: the curve is kept and usable, it is simply unidentified.
    const unknown = await registry.call("mnemonic_normalize", { raw: "GRD", unit: "API" }, ctx);
    assert.equal((unknown.value as { canonical: string | null }).canonical, null);

    const known = await registry.call("mnemonic_normalize", { raw: "GR", unit: "API" }, ctx);
    assert.equal((known.value as { canonical: string | null }).canonical, "GR");
  });

  test("a calculation runs by name and carries its method back", async (t) => {
    if (!(await reachable())) return t.skip("no python3 tool layer on this machine");
    const registry = new ToolRegistry();
    registerPythonTools(registry, readLas);
    // Density porosity of a 2.35 g/cc reading in a clean sandstone on fresh mud.
    // Asquith Eq. 4.7 is (rho_ma - rho_b) / (rho_ma - rho_fl), and the constants
    // are the corpus's, not round numbers: sandstone matrix 2.644 g/cc and fresh
    // water 1.0 g/cc, both from Asquith Table 4.1/4.2. By hand:
    //
    //     (2.644 - 2.35) / (2.644 - 1.0)  =  0.294 / 1.644  =  0.17883 v/v
    const { value, provenance } = await registry.call(
      "petrophysics",
      { tool: "density_porosity", args: { rho_b: 2.35, lithology: "sandstone" } },
      { api: "42-429-36825" }
    );
    const result = value as {
      value: number;
      unit: string;
      method: string;
      source: string;
      inputs: { rho_ma: number; rho_fl: number };
    };
    assert.ok(Math.abs(result.value - 0.17883) < 0.0001, `phiD came back ${result.value}`);
    assert.equal(result.unit, "v/v");
    // The constants are the point. A tool that quietly substituted 2.65 would
    // still return a plausible porosity, and the answer would be wrong by a
    // porosity unit with nothing to show for it.
    assert.equal(result.inputs.rho_ma, 2.644);
    assert.equal(result.inputs.rho_fl, 1.0);
    assert.match(result.method, /Asquith/);
    assert.ok(result.source.length > 0, "no reference on a computed number");
    assert.equal(provenance.tool, "density_porosity");
  });

  test("a call that does not fit comes back with the signature it wanted", async (t) => {
    if (!(await reachable())) return t.skip("no python3 tool layer on this machine");
    const registry = new ToolRegistry();
    registerPythonTools(registry, readLas);
    // `gr` is the obvious wrong guess for `gr_log`. The reply has to teach the
    // real signature, because that is what makes one dispatcher cheaper than
    // 113 registered schemas.
    await assert.rejects(
      registry.call(
        "petrophysics",
        { tool: "vshale", args: { gr: 75, gr_clean: 20, gr_shale: 120 } },
        { api: "42-429-36825" }
      ),
      /gr_log/
    );
  });

  test("a tool that would write is refused, and says why", async (t) => {
    if (!(await reachable())) return t.skip("no python3 tool layer on this machine");
    const registry = new ToolRegistry();
    registerPythonTools(registry, readLas);
    await assert.rejects(
      // "harness", because the dispatcher is no longer Fable's to call.
      registry.call("petrophysics", { tool: "export_las", args: {} }, { api: "42-429-36825" }, "harness"),
      // Refused twice over: it is not in the catalog the harness checks against
      // before the call goes out, and `dispatch.py` refuses it again by name.
      /export_las/
    );
  });
});

/**
 * How a dispatcher call is read.
 *
 * These are the shapes models actually produce. Every one of them used to be a
 * schema rejection that cost a round trip to say what the shape already made
 * obvious, and the first one — a flattened call — was the single most common
 * failure in the first live run.
 */
describe("reading a dispatcher call", () => {
  test("takes the arguments nested under args", () => {
    assert.deepEqual(resolveDispatch({ tool: "vshale", args: { gr_log: 75 } }), {
      tool: "vshale",
      args: { gr_log: 75 },
    });
  });

  test("takes them flattened alongside the name", () => {
    assert.deepEqual(resolveDispatch({ tool: "vshale", gr_log: 75, gr_clean: 20 }), {
      tool: "vshale",
      args: { gr_log: 75, gr_clean: 20 },
    });
  });

  test("accepts `name` for the tool, because models reach for it", () => {
    assert.deepEqual(resolveDispatch({ name: "archie_sw", args: { rt: 12 } }), {
      tool: "archie_sw",
      args: { rt: 12 },
    });
  });

  test("a tool with no arguments is a call, not an error", () => {
    assert.deepEqual(resolveDispatch({ tool: "las_validate" }), { tool: "las_validate", args: {} });
  });

  test("no name at all is refused with an example, never guessed", () => {
    // Picking a tool for the caller would be worse than saying what was needed.
    assert.throws(() => resolveDispatch({ rho_b: 2.35 }), /no tool named\. Call this as/);
  });

  test("an unknown name is refused before the call goes out, with the near misses", () => {
    // Checked against the catalog here rather than at the far end: a round trip
    // to learn a name is a typo is a round trip the prompt already paid for.
    assert.throws(() => resolveDispatch({ tool: "archie" }), /archie_sw/);
    assert.throws(() => resolveDispatch({ tool: "not_a_tool_at_all" }), /no tool named/);
  });
});
