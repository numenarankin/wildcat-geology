import { describe, expect, it } from "vitest";
import {
  CAD_COUNTIES,
  cadCoverage,
  cadCoverageSentence,
  fmtInterest,
  fmtInterestPct,
  fmtValue,
  interestTotals,
  interestTypeLabel,
  ownerTypeLabel,
} from "./cad";

/**
 * The pure half of mineral ownership, checked against numbers written out by
 * hand from the Archer roll (docs/plans/scout-minerals.md §8).
 */
describe("coverage", () => {
  it("is Archer 2025 and nothing else", () => {
    expect(Object.keys(CAD_COUNTIES)).toEqual(["009"]);
    expect(cadCoverage("009")).toEqual({ countyNo: "009", name: "Archer", taxYear: 2025 });
  });

  it("accepts the code however a caller spells it", () => {
    expect(cadCoverage("9")?.countyNo).toBe("009");
    expect(cadCoverage(" 009 ")?.countyNo).toBe("009");
  });

  it("is null for a county with no roll, and for no county", () => {
    expect(cadCoverage("003")).toBeNull();
    expect(cadCoverage(null)).toBeNull();
    expect(cadCoverage("")).toBeNull();
  });

  it("names the county and the roll year in the one sentence", () => {
    expect(cadCoverageSentence()).toBe(
      "Mineral ownership is loaded for Archer County (2025 roll)."
    );
  });
});

describe("interest totals", () => {
  // ANDREWS "A" (O/13/19365), by hand from the roll: five royalty rows summing
  // 0.124999, one working at 0.820313, three overriding summing 0.054688.
  const andrews = [
    { interest_type: "W", interest: 0.820313 },
    { interest_type: "O", interest: 0.053173 },
    { interest_type: "R", interest: 0.030384 },
    { interest_type: "R", interest: 0.03125 },
    { interest_type: "R", interest: 0.03125 },
    { interest_type: "R", interest: 0.016865 },
    { interest_type: "R", interest: 0.01525 },
    { interest_type: "O", interest: 0.001015 },
    { interest_type: "O", interest: 0.0005 },
  ];

  it("sums per type and never normalises to one", () => {
    const t = interestTotals(andrews);
    expect(t.map((x) => x.type)).toEqual(["R", "W", "O"]);
    expect(t[0]).toEqual({ type: "R", label: "Royalty", count: 5, sum: 0.124999 });
    expect(t[1]).toEqual({ type: "W", label: "Working", count: 1, sum: 0.820313 });
    expect(t[2]).toEqual({ type: "O", label: "Overriding", count: 3, sum: 0.054688 });
    // The three together are exactly what the county taxes, which is not 1.
    expect(t.reduce((s, x) => s + x.sum, 0)).toBeCloseTo(1.0, 6);
  });

  it("reports a type with no rows as zero rather than dropping it", () => {
    const t = interestTotals([{ interest_type: "r", interest: 0.125 }]);
    expect(t[0]).toEqual({ type: "R", label: "Royalty", count: 1, sum: 0.125 });
    expect(t[1].count).toBe(0);
    expect(t[2].sum).toBe(0);
  });

  it("does not leak floating error into the sum", () => {
    // 0.1 + 0.2 is the textbook case; the roll's precision is eight places.
    expect(interestTotals([
      { interest_type: "R", interest: 0.1 },
      { interest_type: "R", interest: 0.2 },
    ])[0].sum).toBe(0.3);
  });
});

describe("labels and formats", () => {
  it("spells out the codes the roll uses", () => {
    expect(ownerTypeLabel("I")).toBe("Individual");
    expect(ownerTypeLabel("T")).toBe("Trust");
    expect(ownerTypeLabel("Z")).toBe("Z");
    expect(ownerTypeLabel(null)).toBeNull();
    expect(interestTypeLabel("W")).toBe("Working");
    expect(interestTypeLabel("o")).toBe("Overriding");
  });

  it("prints an interest at the roll's six places and as a percent", () => {
    expect(fmtInterest(0.125)).toBe("0.125000");
    expect(fmtInterest(0.0016)).toBe("0.001600");
    expect(fmtInterest(null)).toBe("—");
    expect(fmtInterestPct(0.820313)).toBe("82.03%");
    expect(fmtInterestPct(0.0016)).toBe("0.1600%");
    expect(fmtInterestPct(0.03125)).toBe("3.125%");
  });

  it("prints appraised value as whole dollars", () => {
    expect(fmtValue(1297330)).toBe("$1,297,330");
    expect(fmtValue(600)).toBe("$600");
    expect(fmtValue(null)).toBe("—");
  });
});
