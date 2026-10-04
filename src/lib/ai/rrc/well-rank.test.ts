import { describe, expect, test } from "vitest";

import type { TestRow, WellRef } from "../../rrc/well-share";
import { rankLeaseWells } from "./well-rank";

/**
 * Per-well estimates, against shares worked out on paper.
 *
 * Every expected number here was computed from the DEFINITION of the split
 * (`@/lib/rrc/well-share`) before the code ran, not read off what the code
 * returned. The definition, for the record:
 *
 *     weighted    = testedCount / wellCount
 *     tested w    = rate(w) / sum(rates) * weighted
 *     untested w  = (1 - weighted) / untestedCount
 *
 * The fixture is built so the plausible wrong answers are all visibly wrong:
 *
 *  - OIL AND GAS TAKE DIFFERENT SHARES. One well carries three quarters of the
 *    lease's tested oil and is the only well with a gas rate at all, and those
 *    two facts produce two different splits from one set of tests. Code that
 *    weighted casinghead by the oil test would hand it gas it does not make.
 *  - THE WELLS RE-SUM TO THE LEASE. That is the check a reader can run on any
 *    number quoted from this, so it is checked here to the cent.
 *  - AN UNTESTED WELL IS NOT ZERO. It takes a head-count share of the part of
 *    the lease the tested wells do not account for, and that is the weakest
 *    number in the output, so it has to be labelled.
 */

function well(wellNo: string, over: Partial<WellRef> = {}): WellRef {
  return { wellNo, produces: true, completedMonth: null, shutInMonth: null, ...over };
}

/** A, B and C. A is the good well, B is a poor one, C was never tested. */
const WELLS = [well("1"), well("2"), well("3")];

const TESTS: TestRow[] = [
  // A: 30 bbl/d oil, and the only well with a gas rate.
  { wellNo: "1", testDate: "2020-01-15", dailyOil: 30, dailyGas: 100 },
  // B: 10 bbl/d oil, no gas.
  { wellNo: "2", testDate: "2020-01-15", dailyOil: 10, dailyGas: 0 },
];

const MONTHS = [
  { month: "2026-04", oil: 1000, gas: 300 },
  { month: "2026-05", oil: 500, gas: 150 },
];

describe("splitting a lease among its wells", () => {
  const rows = rankLeaseWells(WELLS, TESTS, MONTHS);
  const by = (n: string) => rows.find((r) => r.well_no === n)!;

  test("weights oil by the tested oil rates", () => {
    // By hand: tested = {A: 30, B: 10}, sum 40, weighted = 2/3, one untested.
    //   A = 30/40 * 2/3 = 0.5
    //   B = 10/40 * 2/3 = 1/6
    //   C = (1 - 2/3) / 1 = 1/3
    // Over 1,000 then 500 barrels: A 500 + 250, B 166.67 + 83.33, C 333.33 + 166.67.
    expect(by("1").oil_bbl).toBeCloseTo(750, 9);
    expect(by("2").oil_bbl).toBeCloseTo(250, 9);
    expect(by("3").oil_bbl).toBeCloseTo(500, 9);
  });

  test("weights gas by the tested GAS rates, which is a different split", () => {
    // Only A has a gas rate, so tested = {A: 100}, weighted = 1/3, two untested
    // at (1 - 1/3)/2 = 1/3 each. Every well takes a third of the gas, even
    // though A takes half the oil.
    //   450 MCF over the window, 150 each.
    expect(by("1").gas_mcf).toBeCloseTo(150, 9);
    expect(by("2").gas_mcf).toBeCloseTo(150, 9);
    expect(by("3").gas_mcf).toBeCloseTo(150, 9);
    // The property that matters, stated directly: one set of tests, two splits.
    expect(by("1").oil_share_latest).not.toBeCloseTo(by("1").gas_share_latest!, 6);
  });

  test("the wells re-sum to the lease, which is the reader's check", () => {
    const oil = rows.reduce((a, r) => a + r.oil_bbl, 0);
    const gas = rows.reduce((a, r) => a + r.gas_mcf, 0);
    expect(oil).toBeCloseTo(1500, 9);
    expect(gas).toBeCloseTo(450, 9);
  });

  test("labels the untested well, whose number is the weakest one here", () => {
    expect(by("1").weighted_by).toBe("well-test");
    expect(by("2").weighted_by).toBe("well-test");
    expect(by("3").weighted_by).toBe("head-count");
  });

  test("returns a well that made nothing rather than omitting it", () => {
    // Absence and zero read the same in a ranked list, and they are different
    // facts: one well is on the lease and idle, the other is not on it.
    const shut = rankLeaseWells(
      [well("1"), well("2", { shutInMonth: "2025-01" })],
      TESTS,
      MONTHS
    );
    expect(shut.map((r) => r.well_no)).toEqual(["1", "2"]);
    expect(shut.find((r) => r.well_no === "2")!.oil_bbl).toBe(0);
    // And the running well takes the whole lease, not half of it.
    expect(shut.find((r) => r.well_no === "1")!.oil_bbl).toBeCloseTo(1500, 9);
  });

  test("gives a well no share of the months before it was drilled", () => {
    // B was completed inside the window. April is A's alone; May is split by
    // test, A 30 of 40 and B 10 of 40, both tested so `weighted` is 1.
    //   A = 1000 + 500 * 0.75 = 1375
    //   B =         500 * 0.25 =  125
    const late = rankLeaseWells(
      [well("1"), well("2", { completedMonth: "2026-05" })],
      TESTS,
      MONTHS
    );
    expect(late.find((r) => r.well_no === "1")!.oil_bbl).toBeCloseTo(1375, 9);
    expect(late.find((r) => r.well_no === "2")!.oil_bbl).toBeCloseTo(125, 9);
  });

  test("drops a service hole out of the denominator entirely", () => {
    // An injection well cannot make the lease's oil. Left in, it would take a
    // head-count third of a lease it physically cannot produce, off the wells
    // that did.
    const withInjector = rankLeaseWells(
      [well("1"), well("2"), well("9", { produces: false })],
      TESTS,
      MONTHS
    );
    expect(withInjector.find((r) => r.well_no === "9")!.oil_bbl).toBe(0);
    // A and B are the only producers and both are tested, so they split the
    // whole lease 30:10.
    expect(withInjector.find((r) => r.well_no === "1")!.oil_bbl).toBeCloseTo(1125, 9);
    expect(withInjector.find((r) => r.well_no === "2")!.oil_bbl).toBeCloseTo(375, 9);
  });

  test("splits evenly when no well on the lease was ever tested", () => {
    const untested = rankLeaseWells(WELLS, [], MONTHS);
    for (const r of untested) {
      expect(r.oil_bbl).toBeCloseTo(500, 9);
      expect(r.weighted_by).toBe("head-count");
    }
  });

  test("has nothing to say with no wells or no filed months", () => {
    expect(rankLeaseWells([], TESTS, MONTHS)).toEqual([]);
    expect(rankLeaseWells(WELLS, TESTS, [])).toEqual([]);
  });
});
