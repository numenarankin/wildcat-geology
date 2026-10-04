import { describe, expect, it } from "vitest";
import {
  casingLabel,
  h15Method,
  injTypeLabel,
  isDisposal,
  isH15Problem,
} from "./rrc-uic";

/**
 * The RRC's code values, put back into words.
 *
 * Each of these fails silently if it is wrong: a mislabelled injection type
 * still renders a plausible sentence, and a casing size rounded the wrong way
 * still looks like pipe. So every expectation is derived from the manual's own
 * domain, not from what the function happens to return.
 */

describe("injTypeLabel", () => {
  it("reads code 3 as enhanced recovery in both eras", () => {
    // 1, 2 and 3 kept their meaning across the 1995-06-01 renumbering.
    expect(injTypeLabel("3", "1988-01-01")).toMatch(/recovery/i);
    expect(injTypeLabel("3", "2020-01-01")).toMatch(/recovery/i);
  });

  it("resolves the renumbered codes by the permit's own date", () => {
    // THE TRAP: code 5 meant "gas storage" before 1995-06-01 and "liquid
    // storage in a salt formation" after. A single label would be wrong for
    // half the file.
    expect(injTypeLabel("5", "1990-03-01")).toBe("Gas storage");
    expect(injTypeLabel("5", "2001-03-01")).toMatch(/salt formation/i);
    // The boundary itself belongs to the NEW scheme.
    expect(injTypeLabel("5", "1995-06-01")).toMatch(/salt formation/i);
  });

  it("falls back to the raw code rather than inventing a name", () => {
    // Type 8 is in the data and in no version of the manual.
    expect(injTypeLabel("8", null)).toBe("Type 8");
    expect(injTypeLabel(null, null)).toBeNull();
  });

  it("with no approval date, assumes the current scheme", () => {
    // 99% of permits have no approved_date at all, so the fallback is the one
    // that runs almost always — it must be the modern meaning.
    expect(injTypeLabel("5", null)).toMatch(/salt formation/i);
  });
});

describe("isDisposal", () => {
  it("is true only for the two disposal types", () => {
    expect(isDisposal("1")).toBe(true);
    expect(isDisposal("2")).toBe(true);
    // Type 3 is waterflood injection into a PRODUCING zone. Counting it as
    // disposal would offer someone's producing reservoir as a place to send
    // produced water.
    expect(isDisposal("3")).toBe(false);
    expect(isDisposal(null)).toBe(false);
  });
});

describe("casingLabel", () => {
  it("writes pipe the way an operator says it", () => {
    expect(casingLabel(5.5)).toBe('5 1/2"');
    expect(casingLabel(8.625)).toBe('8 5/8"');
    expect(casingLabel(13.375)).toBe('13 3/8"');
    expect(casingLabel(9.625)).toBe('9 5/8"');
    expect(casingLabel(2.375)).toBe('2 3/8"');
    expect(casingLabel(2.875)).toBe('2 7/8"');
  });

  it("drops the fraction when there is none", () => {
    expect(casingLabel(7)).toBe('7"');
    expect(casingLabel(20)).toBe('20"');
  });

  it("has nothing to say about an unrecorded size", () => {
    expect(casingLabel(null)).toBeNull();
  });
});

describe("h15Method", () => {
  it("reads the method column that matches the test type", () => {
    // Fluid-level and mechanical-integrity tests store their method in
    // DIFFERENT columns, and the unused one is blank. Reading the wrong one
    // silently returns nothing for every test of that kind.
    expect(h15Method("F", "S", null)).toBe("sonic");
    expect(h15Method("M", null, "H")).toBe("hydraulic pressure");
  });

  it("ignores a stray value in the column for the other kind of test", () => {
    expect(h15Method("F", null, "H")).toBeNull();
  });

  it("has nothing to say about an untyped test", () => {
    expect(h15Method(null, "S", "H")).toBeNull();
  });
});

describe("isH15Problem", () => {
  it("flags only the statuses that are actually a problem", () => {
    expect(isH15Problem("D")).toBe(true);
    expect(isH15Problem("N")).toBe(true);
    expect(isH15Problem("X")).toBe(true);
    // Approved, compliant, pending, extension and UIC are all fine — a well
    // under a W-3A extension is in good standing, not delinquent.
    for (const ok of ["A", "C", "P", "W", "U", "E", null]) {
      expect(isH15Problem(ok)).toBe(false);
    }
  });
});
