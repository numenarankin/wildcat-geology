import { describe, expect, it } from "vitest";
import { z } from "zod";
import {
  ARG_SYNONYMS,
  coerceEnumArgs,
  coerceEnumValue,
  declaredArgs,
  enumOptions,
  normalizeToolArgs,
} from "./tool-args";

/**
 * The safety of the rewrite is the whole point. A refused call costs a round
 * trip; a call silently rewritten onto the wrong argument returns a confident
 * wrong answer, which is far worse. So most of these are about what it must NOT
 * touch.
 */

const declared = (...names: string[]) => new Set(names);

describe("normalizeToolArgs", () => {
  it("rewrites the synonym the model actually used in production", () => {
    // rank({kind: "wells"}), where the argument is `cohort`.
    expect(
      normalizeToolArgs({ kind: "wells", metric: "oil" }, declared("cohort", "metric"))
    ).toEqual({ cohort: "wells", metric: "oil" });
  });

  it("rewrites window and paging synonyms", () => {
    expect(
      normalizeToolArgs({ since: "2026-01-01", until: "2026-03-01", top: 5 }, declared("from", "to", "limit"))
    ).toEqual({ from: "2026-01-01", to: "2026-03-01", limit: 5 });
  });

  it("leaves a tool alone when it declares the synonym itself", () => {
    // `rrc_permits` really has `since` and `until`. Rewriting them onto from/to
    // would drop the arguments the tool actually reads.
    const args = { since: "2026-01-01", until: "2026-03-01" };
    expect(normalizeToolArgs(args, declared("since", "until"))).toEqual(args);
  });

  it("never overwrites a blessed name the caller already set", () => {
    // Both present means the caller meant both. Guessing which wins is how a
    // correct call becomes a wrong one.
    const args = { from: "2026-01-01", since: "2020-01-01" };
    expect(normalizeToolArgs(args, declared("from"))).toEqual(args);
  });

  it("does not invent an argument the tool does not take", () => {
    const args = { kind: "wells" };
    expect(normalizeToolArgs(args, declared("metric"))).toEqual(args);
  });

  it("does nothing when the schema is unknown", () => {
    // Guessing without a schema would apply a rename to a tool that never wanted
    // it, turning a clear refusal into a silently wrong call.
    const args = { kind: "wells" };
    expect(normalizeToolArgs(args, null)).toEqual(args);
    expect(normalizeToolArgs(args, declared())).toEqual(args);
  });

  it("returns the same object when there is nothing to do", () => {
    const args = { cohort: "wells" };
    expect(normalizeToolArgs(args, declared("cohort"))).toBe(args);
  });

  it("does not mutate the caller's object", () => {
    const args = { kind: "wells" };
    normalizeToolArgs(args, declared("cohort"));
    expect(args).toEqual({ kind: "wells" });
  });

  it("rewrites several arguments in one call", () => {
    expect(
      normalizeToolArgs(
        { well_id: "smith-3", since: "2026-01-01", top: 3 },
        declared("wellId", "from", "limit")
      )
    ).toEqual({ wellId: "smith-3", from: "2026-01-01", limit: 3 });
  });

  it("takes the first synonym present and stops", () => {
    // Two synonyms for one blessed name is ambiguous. Taking one and leaving the
    // other visible is better than merging them silently.
    const out = normalizeToolArgs({ top: 3, max: 9 }, declared("limit"));
    expect(out.limit).toBe(3);
    expect(out.max).toBe(9);
  });
});

describe("declaredArgs", () => {
  it("reads a Zod object's keys", () => {
    expect([...declaredArgs(z.object({ a: z.string(), b: z.number() }))].sort()).toEqual([
      "a",
      "b",
    ]);
  });

  it("is empty for anything that is not an object schema", () => {
    expect(declaredArgs(z.string()).size).toBe(0);
    expect(declaredArgs(undefined).size).toBe(0);
  });
});

describe("the synonym table itself", () => {
  it("never lists a name as its own synonym", () => {
    for (const [blessed, synonyms] of Object.entries(ARG_SYNONYMS)) {
      expect(synonyms, `${blessed} lists itself`).not.toContain(blessed);
    }
  });

  it("maps kind and cohort to each other, which is the live failure", () => {
    // Either spelling has to survive whichever tool the model came from.
    expect(ARG_SYNONYMS.cohort).toContain("kind");
    expect(ARG_SYNONYMS.kind).toContain("cohort");
  });
});

describe("coerceEnumValue", () => {
  const metrics = ["oil", "gas", "water"];

  it("snaps the value a model actually produced", () => {
    // rank({metric: "oil_production"}) on the first question ever asked of it.
    expect(coerceEnumValue("oil_production", metrics)).toBe("oil");
  });

  it("is case and punctuation insensitive on an exact match", () => {
    expect(coerceEnumValue("Oil", metrics)).toBe("oil");
    expect(coerceEnumValue("WATER", metrics)).toBe("water");
  });

  it("does not match a longer word that merely starts the same", () => {
    // "oilfield" is not oil. Snapping it would answer a question nobody asked.
    expect(coerceEnumValue("oilfield", metrics)).toBeNull();
  });

  it("refuses an ambiguous value rather than picking", () => {
    expect(coerceEnumValue("g", ["gas", "gor"])).toBeNull();
  });

  it("returns null for something unrelated", () => {
    expect(coerceEnumValue("revenue", metrics)).toBeNull();
    expect(coerceEnumValue(7, metrics)).toBeNull();
  });
});

describe("enumOptions and coerceEnumArgs", () => {
  const schema = z.object({
    metric: z.enum(["oil", "gas", "water"]),
    cohort: z.enum(["wells", "leases"]).optional(),
    from: z.string().optional(),
  });

  it("reads options through optional wrappers", () => {
    expect(enumOptions(schema.shape.metric)).toEqual(["oil", "gas", "water"]);
    expect(enumOptions(schema.shape.cohort)).toEqual(["wells", "leases"]);
    expect(enumOptions(schema.shape.from)).toEqual([]);
  });

  it("fixes the enum and leaves the free-form argument alone", () => {
    const out = coerceEnumArgs(schema, {
      metric: "oil_production",
      from: "last_6_months",
    });
    expect(out).toEqual({ metric: "oil", from: "last_6_months" });
  });

  it("makes the refused live call valid", () => {
    const out = coerceEnumArgs(schema, { metric: "oil_production", cohort: "wells" });
    expect(schema.safeParse(out).success).toBe(true);
  });

  it("leaves an unmatchable value in place so the refusal still explains itself", () => {
    const out = coerceEnumArgs(schema, { metric: "revenue" });
    expect(out.metric).toBe("revenue");
    expect(schema.safeParse(out).success).toBe(false);
  });

  it("returns the same object when nothing needed fixing", () => {
    const args = { metric: "oil" };
    expect(coerceEnumArgs(schema, args)).toBe(args);
  });
});
