import { describe, it, expect } from "vitest";
import { RRC_TOOLS, RRC_CATALOG, findRrcTool } from "./registry";
import { catalogLine, signature } from "./tool";
import { coerceEnumValue, enumOptions } from "../tool-args";

/**
 * Invariants over the catalog as a whole, which no single tool's tests can see.
 *
 * The catalog IS the documentation: the model gets one line per tool and nothing
 * else, so a duplicate name, a missing summary or a signature that does not
 * match the function behind it is a tool called wrong on every turn with no way
 * for anyone to notice.
 */

describe("the RRC analysis catalog", () => {
  it("has no duplicate names", () => {
    // Two tools answering to one name means the registry's Map silently keeps
    // whichever was registered last, so the other is unreachable and nothing
    // reports it.
    const names = RRC_TOOLS.map((t) => t.name);
    const dupes = [...new Set(names.filter((n, i) => names.indexOf(n) !== i))];
    expect(dupes).toEqual([]);
  });

  it("names every tool so the geology bridge can admit it", () => {
    // `rrc-bridge.ts` admits by an `rrc_` prefix. A tool named otherwise is
    // invisible to Fable, silently, which is exactly how `offsets_within_radius`
    // went missing for so long.
    const wrong = RRC_TOOLS.filter((t) => !t.name.startsWith("rrc_")).map((t) => t.name);
    expect(wrong).toEqual([]);
  });

  it("gives every tool a summary that says what it answers", () => {
    const thin = RRC_TOOLS.filter((t) => (t.summary ?? "").trim().length < 30).map((t) => t.name);
    expect(thin).toEqual([]);
  });

  it("derives each signature from the live zod shape", () => {
    // The signature is generated rather than written precisely so it cannot
    // drift from the function. This asserts the generation still works over
    // every shape in use, including enums, arrays and defaults.
    for (const tool of RRC_TOOLS) {
      const sig = signature(tool);
      expect(sig.startsWith(`${tool.name}(`)).toBe(true);
      expect(sig.endsWith(")")).toBe(true);
      expect(catalogLine(tool)).toContain(tool.summary);
    }
  });

  it("uses no em dashes in anything the model reads", () => {
    expect(RRC_CATALOG).not.toContain("—");
  });

  it("resolves every registered name through the dispatcher's lookup", () => {
    for (const tool of RRC_TOOLS) {
      expect(findRrcTool(tool.name)).toBe(tool);
    }
  });
});

describe("enum coercion cannot silently pick the wrong option", () => {
  it("has no enum whose options let a near-miss snap onto the wrong one", () => {
    // `coerceEnumValue` snaps a descriptive value onto an option when exactly
    // one option is a prefix of it followed by a separator. That is safe only
    // while no option is itself a prefix of another: with `oil` and `oil_gas`
    // both legal, "oil_gas_code" would be a genuine ambiguity. The helper
    // refuses to guess when two match, so this asserts the shape it relies on
    // and documents WHY the ambiguity guard has to stay.
    const collisions: string[] = [];
    for (const tool of RRC_TOOLS) {
      for (const [key, schema] of Object.entries(tool.args.shape)) {
        const options = enumOptions(schema);
        for (const a of options) {
          for (const b of options) {
            if (a !== b && b.toLowerCase().startsWith(a.toLowerCase())) {
              collisions.push(`${tool.name}.${key}: "${a}" is a prefix of "${b}"`);
            }
          }
        }
      }
    }
    // Any entry here is not a bug on its own, it is a place where the guard is
    // doing real work and a change to the helper would start mis-snapping.
    expect(collisions, collisions.join("\n")).toEqual([]);
  });

  it("leaves an unmatchable value alone so the refusal still names the signature", () => {
    // The failure mode that matters: a value nothing matches must NOT be
    // silently replaced, or the model gets an answer to a question it did not
    // ask.
    expect(coerceEnumValue("water", ["oil", "gas", "cond", "csgd"])).toBe(null);
    expect(coerceEnumValue("oilfield", ["oil", "gas"])).toBe(null);
    expect(coerceEnumValue("oil_production", ["oil", "gas"])).toBe("oil");
  });
});
