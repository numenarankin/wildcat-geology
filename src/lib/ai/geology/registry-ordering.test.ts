import { describe, expect, test } from "vitest";
import { geologyRegistry } from "./tool-registry";

/**
 * The generated petrophysics wrappers must never take a hand-written tool's name.
 *
 * Registered before the contract branches they claimed `kb_lookup` and
 * `hole_quality` as `callableBy: ["fable"]`, and Stage 0 lost both — the trace
 * reported them `unavailable` to the harness on a live turn.
 */
describe("registry ordering", () => {
  test("the harness keeps every tool it calls", () => {
    const r = geologyRegistry();
    for (const name of ["kb_lookup", "hole_quality", "curve_suite", "las_header"]) {
      const forHarness = r.listFor("harness").some((t) => t.name === name);
      expect(forHarness, `${name} is not callable by the harness`).toBe(true);
    }
  });
});
