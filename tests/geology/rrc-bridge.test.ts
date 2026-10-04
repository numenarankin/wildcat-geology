/**
 * Orion's RRC tools, reachable from the geology harness.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/rrc-bridge.test.ts
 *
 * Surrounding production is usually what turns a log reading into a conclusion,
 * and on the no-log path the public record is often the whole answer. These
 * assert the bridge admits every tool, keeps them read-only, and lets both the
 * gatherer and Fable reach them.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { registerRrcTools } from "@/lib/ai/geology/rrc-bridge";
import { ToolRegistry } from "@/lib/ai/geology/registry";
import { geologyRegistry, setGeologyRegistry } from "@/lib/ai/geology/tool-registry";

/** Every tool the scout page's data layer exposes. */
const EXPECTED = [
  "rrc_search", "rrc_data_vintage", "rrc_well", "rrc_lease", "rrc_operator",
  "rrc_operator_network", "rrc_disposition", "rrc_field", "rrc_county",
  "rrc_wells_near", "rrc_survey", "rrc_market", "rrc_leaderboard",
  "rrc_permits", "rrc_completion", "rrc_disposal",
];

describe("the bridge", () => {
  test("registers every RRC tool", () => {
    const registry = new ToolRegistry();
    const added = registerRrcTools(registry);
    assert.equal(added, EXPECTED.length);
    for (const name of EXPECTED) assert.ok(registry.has(name), `${name} was not bridged`);
  });

  test("both agents can reach them", () => {
    // The gatherer pulls the public record while assembling; Fable follows up
    // on what it finds. Neither is much use without it.
    const registry = new ToolRegistry();
    registerRrcTools(registry);
    for (const role of ["gatherer", "fable"] as const) {
      const names = registry.listFor(role).map((t) => t.name);
      for (const want of ["rrc_wells_near", "rrc_completion", "rrc_lease", "rrc_data_vintage"]) {
        assert.ok(names.includes(want), `${want} not callable by ${role}`);
      }
    }
  });

  test("they carry the description Orion wrote, so the model sees the same guidance", () => {
    const registry = new ToolRegistry();
    registerRrcTools(registry);
    const near = registry.listFor("gatherer").find((t) => t.name === "rrc_wells_near");
    assert.match(near?.description ?? "", /offset-well tool/i);
    const vintage = registry.listFor("gatherer").find((t) => t.name === "rrc_data_vintage");
    // The trap that matters: unfiled recent months read as a production collapse.
    assert.match(vintage?.description ?? "", /three months behind/i);
  });

  test("every bridged tool is read-only", () => {
    // The registry refuses anything else, so reaching this point proves it —
    // but assert the declaration too, since that is what the rule rests on.
    const registry = new ToolRegistry();
    registerRrcTools(registry);
    for (const tool of registry.listFor("fable")) assert.equal(tool.readOnly, true);
  });

  test("registering twice does not throw on the duplicate", () => {
    const registry = new ToolRegistry();
    assert.equal(registerRrcTools(registry), EXPECTED.length);
    assert.equal(registerRrcTools(registry), 0);
  });
});

describe("the live registry", () => {
  test("carries the RRC tools, the petrophysics layer, and Orion's read-only ones", () => {
    setGeologyRegistry(null);
    const registry = geologyRegistry();
    for (const name of EXPECTED) assert.ok(registry.has(name), `${name} missing`);
    // The gatherer gets the public record and the header read — enough to
    // assemble context. Orion's 100-odd record tools and the petrophysics
    // dispatcher are Fable's alone: the first would widen the gatherer's search
    // space without improving the hand-off, and the second needs the catalog
    // Fable has and the gatherer does not.
    assert.deepEqual(
      registry.listFor("gatherer").map((t) => t.name).filter((n) => !n.startsWith("rrc_")).sort(),
      ["las_header"]
    );
    assert.ok(registry.listFor("fable").length > EXPECTED.length, "Fable got no Orion tools");
    setGeologyRegistry(null);
  });

  test("admits no tool that mutates", () => {
    // Orion marks writes with `needsApproval`; the bridge filters on that and
    // the registry refuses anything not declared read-only. Two checks, and a
    // write tool would have to defeat both.
    setGeologyRegistry(null);
    const registry = geologyRegistry();
    for (const tool of registry.listFor("fable")) {
      assert.equal(tool.readOnly, true);
      assert.ok(
        !/^(create|update|set|add|delete|assign|grant|publish|save|edit|import|record)_/.test(tool.name),
        `${tool.name} looks like a write tool`
      );
    }
    setGeologyRegistry(null);
  });

  test("carries the parse Stage 0 needs, and not the aggregates nobody wrote", () => {
    setGeologyRegistry(null);
    const registry = geologyRegistry();
    // The Stage 0 contract, backed by api/geology.py.
    for (const name of ["las_header", "las_curves", "mnemonic_normalize", "petrophysics"]) {
      assert.ok(registry.has(name), `${name} missing`);
    }
    // The six aggregate branches Stage 0 and Stage 1 call on every well turn.
    // Each failed on every turn until `contract-tools.ts` composed them out of
    // the individual Python tools; nothing here may be "unavailable" again.
    for (const name of [
      "curve_suite", "hole_quality", "kb_lookup",
      "calculators", "continuity_check", "rrc_completion_record",
    ]) {
      assert.ok(registry.has(name), `${name} has no adapter — the harness will call it and fail`);
    }
    setGeologyRegistry(null);
  });
});
