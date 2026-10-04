import { describe, expect, test } from "vitest";
import { z } from "zod";
import { CATALOG_ENTRIES, findTool } from "./tool-catalog";
import { petrophysicsSchemas, schemaFor } from "./catalog-schema";

/**
 * The two calls that failed in production, asserted as IMPOSSIBLE.
 *
 * Fable called `matrix_density_sensitivity` with `matrices` instead of
 * `matrix_candidates`, and `density_porosity` with no `lithology`. Both came
 * back 422 from Python, and rather than reading the returned signature and
 * calling again — which the dispatcher's design assumed it would — it gave up
 * and wrote a caveat about the matrix question, which is the number those two
 * tools compute.
 *
 * Everything before this was a patch on a guess: render the args, render them
 * differently, normalise synonyms, retry on the error. A schema is different in
 * kind, because the provider constrains decoding against it and the wrong call
 * stops being expressible.
 *
 * So these assert the schema REFUSES those exact shapes, by name.
 */

describe("the calls that failed in production", () => {
  test("`matrices` for `matrix_candidates` is refused", () => {
    const entry = findTool("matrix_density_sensitivity");
    expect(entry).toBeDefined();
    const schema = schemaFor(entry!);

    // The call Fable actually made.
    expect(schema.safeParse({ rho_b: 2.41, matrices: ["sandstone"] }).success).toBe(false);

    // The call it meant to make.
    expect(
      schema.safeParse({ rho_b: 2.41, matrix_candidates: ["sandstone"] }).success
    ).toBe(true);
  });

  test("`density_porosity` without `lithology` is refused", () => {
    const entry = findTool("density_porosity");
    expect(entry).toBeDefined();
    const schema = schemaFor(entry!);

    expect(schema.safeParse({ rho_b: 2.41 }).success).toBe(false);
    expect(schema.safeParse({ rho_b: 2.41, lithology: "sandstone" }).success).toBe(true);
  });
});

describe("the generated schemas", () => {
  test("every catalog entry produces one, and every required arg is required", () => {
    const schemas = petrophysicsSchemas();
    expect(schemas).toHaveLength(CATALOG_ENTRIES.length);

    for (const entry of CATALOG_ENTRIES) {
      const schema = schemaFor(entry);
      const shape = schema.shape as Record<string, z.ZodTypeAny>;
      for (const spec of entry.required) {
        const name = spec.slice(0, spec.indexOf(":")).trim();
        expect(shape[name], `${entry.name}.${name} missing`).toBeDefined();
        expect(
          shape[name].isOptional(),
          `${entry.name}.${name} is required in the catalog but optional in the schema`
        ).toBe(false);
      }
      for (const spec of entry.optional) {
        const name = spec.slice(0, spec.indexOf(":")).trim();
        expect(shape[name], `${entry.name}.${name} missing`).toBeDefined();
        expect(
          shape[name].isOptional(),
          `${entry.name}.${name} is optional in the catalog but required in the schema`
        ).toBe(true);
      }
    }
  });

  test("an unknown key is rejected rather than dropped", () => {
    // `.strict()` is the whole point. Stripping the key silently would send a
    // call missing the argument the model believed it was passing, which is a
    // worse failure than the one this replaces: the tool would answer, from the
    // wrong inputs, with full provenance.
    const schema = schemaFor(findTool("density_porosity")!);
    const parsed = schema.safeParse({
      rho_b: 2.41,
      lithology: "sandstone",
      nonsense_argument: 1,
    });
    expect(parsed.success).toBe(false);
  });

  test("types are enforced, so a string depth cannot reach a float argument", () => {
    const schema = schemaFor(findTool("density_porosity")!);
    expect(schema.safeParse({ rho_b: "2.41", lithology: "sandstone" }).success).toBe(false);
  });

  test("the whole set stays inside the budget that justified registering it", () => {
    /*
     * Measured at 72.6k characters when this landed, against ~13.2k for the
     * name-only catalog it replaced. That was the trade: ~15k extra tokens, in a
     * prompt Stage 3 marks `cacheControl: ephemeral`, against a turn measured at
     * 365k input tokens.
     *
     * If the catalog grows enough to break this, the trade needs re-deciding
     * rather than the ceiling raising — subsetting per turn is the next move,
     * and `ai@6` supports it through `activeTools`/`prepareStep`.
     */
    const bytes = petrophysicsSchemas().reduce(
      (n, s) => n + JSON.stringify(z.toJSONSchema(s.inputSchema)).length + s.description.length,
      0
    );
    expect(bytes).toBeLessThan(140_000);
  });
});
