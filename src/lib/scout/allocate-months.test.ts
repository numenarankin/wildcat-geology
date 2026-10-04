import { describe, expect, test } from "vitest";
import {
  GAS_KEYS,
  mergeRecordMonths,
  monthlyRate,
  OIL_KEYS,
  scaleMonth,
} from "./allocate-months";
import type { LeaseMonth } from "./rrc-types";

/**
 * The oracle is the RRC's own filing convention, not the function's output:
 *
 *   oil record   liquid in `oil_prod_vol`,  gas in `csgd_prod_vol` (casinghead)
 *   gas record   gas in `gas_prod_vol`,     liquid in `cond_prod_vol` (condensate)
 *
 * No column is ever populated by both records, so a hole on one of each keeps
 * every barrel and every MCF exactly once.
 */

const month = (over: Partial<LeaseMonth> & { cycle: string }): LeaseMonth => ({
  oil_prod_vol: 0,
  oil_allow: null,
  oil_ending_bal: null,
  gas_prod_vol: 0,
  gas_allow: null,
  gas_lift_inj_vol: null,
  cond_prod_vol: 0,
  cond_limit: null,
  cond_ending_bal: null,
  csgd_prod_vol: 0,
  csgd_limit: null,
  csgd_gas_lift: null,
  oil_tot_disp: null,
  gas_tot_disp: null,
  cond_tot_disp: null,
  csgd_tot_disp: null,
  prod_report_filed: "Y",
  reported: true,
  ...over,
});

describe("scaleMonth", () => {
  test("liquids and gas take their own share", () => {
    // A well with three quarters of the lease's tested oil and a quarter of its
    // tested gas: 400 bbl -> 300, 800 MCF of casinghead -> 200.
    const out = scaleMonth(
      month({ cycle: "2024-03", oil_prod_vol: 400, csgd_prod_vol: 800 }),
      0.75,
      0.25
    );
    expect(out.oil_prod_vol).toBeCloseTo(300, 9);
    expect(out.csgd_prod_vol).toBeCloseTo(200, 9);
  });

  test("allowables move with the volume they cap", () => {
    // Left at lease scale, a half share of the oil would sit under the whole
    // lease's allowable and read as chronic underproduction.
    const out = scaleMonth(
      month({ cycle: "2024-03", oil_prod_vol: 400, oil_allow: 600 }),
      0.5,
      0.5
    );
    expect(out.oil_prod_vol).toBeCloseTo(200, 9);
    expect(out.oil_allow).toBeCloseTo(300, 9);
  });

  test("labels are not numbers and are left alone", () => {
    const out = scaleMonth(
      month({ cycle: "2024-03", oil_prod_vol: 400, prod_report_filed: "N" }),
      0.5,
      0.5
    );
    expect(out.cycle).toBe("2024-03");
    expect(out.prod_report_filed).toBe("N");
    expect(out.reported).toBe(true);
  });

  test("a null measure stays null rather than becoming zero", () => {
    // Null is "the state did not report this", which a share cannot turn into a
    // measurement of nothing.
    const out = scaleMonth(month({ cycle: "2024-03", oil_allow: null }), 0.5, 0.5);
    expect(out.oil_allow).toBeNull();
  });
});

describe("mergeRecordMonths", () => {
  test("an oil record and a gas record keep both streams, counted once", () => {
    const oilRecord = [
      month({ cycle: "2024-03", oil_prod_vol: 300, csgd_prod_vol: 120 }),
    ];
    const gasRecord = [
      month({ cycle: "2024-03", gas_prod_vol: 2000, cond_prod_vol: 15 }),
    ];
    const [m] = mergeRecordMonths([oilRecord, gasRecord]);
    expect(m.oil_prod_vol).toBe(300);
    expect(m.csgd_prod_vol).toBe(120);
    expect(m.gas_prod_vol).toBe(2000);
    expect(m.cond_prod_vol).toBe(15);
  });

  test("a month only one record covers is carried whole", () => {
    // The real case: a gas lease that stopped reporting in 2001 beside an oil
    // lease still filing casinghead in 2025.
    const gasRecord = [month({ cycle: "2001-08", gas_prod_vol: 2172 })];
    const oilRecord = [month({ cycle: "2025-10", csgd_prod_vol: 3 })];
    const out = mergeRecordMonths([gasRecord, oilRecord]);
    expect(out).toHaveLength(2);
    expect(out[0].cycle).toBe("2001-08");
    expect(out[0].gas_prod_vol).toBe(2172);
    expect(out[1].csgd_prod_vol).toBe(3);
  });

  test("filed on either record is filed", () => {
    // A hole whose gas lease has reported and whose oil lease has not is not an
    // unreported month; treating it as one draws the cliff to zero at the edge.
    const [m] = mergeRecordMonths([
      [month({ cycle: "2026-01", prod_report_filed: "N", reported: false })],
      [month({ cycle: "2026-01", prod_report_filed: "Y", reported: true })],
    ]);
    expect(m.prod_report_filed).toBe("Y");
    expect(m.reported).toBe(true);
  });

  test("output is oldest first regardless of input order", () => {
    const out = mergeRecordMonths([
      [month({ cycle: "2024-12" }), month({ cycle: "2024-01" })],
      [month({ cycle: "2024-06" })],
    ]);
    expect(out.map((m) => m.cycle)).toEqual(["2024-01", "2024-06", "2024-12"]);
  });

  test("one record merges to itself", () => {
    const only = [month({ cycle: "2024-03", oil_prod_vol: 300 })];
    expect(mergeRecordMonths([only])[0].oil_prod_vol).toBe(300);
  });

  test("no records is an empty series, not a row of zeros", () => {
    expect(mergeRecordMonths([])).toEqual([]);
    expect(mergeRecordMonths([[], []])).toEqual([]);
  });

  test("the merge does not mutate its input", () => {
    const a = [month({ cycle: "2024-03", oil_prod_vol: 300 })];
    const b = [month({ cycle: "2024-03", oil_prod_vol: 100 })];
    const merged = mergeRecordMonths([a, b]);
    expect(merged[0].oil_prod_vol).toBe(400);
    expect(a[0].oil_prod_vol).toBe(300);
  });
});

/**
 * The oracle here is arithmetic done by hand against the RRC's filing rules,
 * never the function's own output. Two rules decide every case:
 *
 *   - a stream is the SUM of its pair of columns (OIL_KEYS / GAS_KEYS), and
 *   - an UNREPORTED month is one the RRC has not published — unknown, not zero
 *     — so it is not in the numerator and must not be in the denominator.
 *
 * A month the RRC published with no report filed is a real zero and stays in
 * both.
 */
describe("monthlyRate", () => {
  test("a full year averages the year", () => {
    // 12 months at 300 bbl of oil-record liquid = 3,600 / 12 = 300.
    const year = Array.from({ length: 12 }, (_, i) =>
      month({ cycle: `2024-${String(i + 1).padStart(2, "0")}`, oil_prod_vol: 300 })
    );
    expect(monthlyRate(year, OIL_KEYS)).toBeCloseTo(300, 9);
  });

  test("both columns of a stream count", () => {
    // One month, 100 bbl on the oil record and 40 bbl of condensate off the gas
    // record: the well made 140 bbl that month, so its rate is 140/mo.
    const one = [
      month({ cycle: "2024-03", oil_prod_vol: 100, cond_prod_vol: 40 }),
    ];
    expect(monthlyRate(one, OIL_KEYS)).toBeCloseTo(140, 9);
    // Same month's gas pair: 900 MCF sales gas + 100 MCF casinghead.
    const gas = [
      month({ cycle: "2024-03", gas_prod_vol: 900, csgd_prod_vol: 100 }),
    ];
    expect(monthlyRate(gas, GAS_KEYS)).toBeCloseTo(1000, 9);
  });

  test("a new well is divided by the months it actually filed", () => {
    // Three filed months at 600 bbl beside nine the RRC has not published. The
    // well is making 600 a month; dividing by twelve would report 150 and read
    // as a fourth of a real well.
    const series = [
      ...Array.from({ length: 9 }, (_, i) =>
        month({
          cycle: `2024-${String(i + 1).padStart(2, "0")}`,
          reported: false,
        })
      ),
      month({ cycle: "2024-10", oil_prod_vol: 600 }),
      month({ cycle: "2024-11", oil_prod_vol: 600 }),
      month({ cycle: "2024-12", oil_prod_vol: 600 }),
    ];
    expect(monthlyRate(series, OIL_KEYS)).toBeCloseTo(600, 9);
  });

  test("a published month with no report filed is a zero that counts", () => {
    // Six months at 600 and six filed empty: 3,600 over twelve = 300. A shut-in
    // half-year IS half the rate, and hiding it would flatter the well.
    const series = [
      ...Array.from({ length: 6 }, (_, i) =>
        month({ cycle: `2024-0${i + 1}`, oil_prod_vol: 600 })
      ),
      ...Array.from({ length: 6 }, (_, i) =>
        month({
          cycle: `2024-${String(i + 7).padStart(2, "0")}`,
          prod_report_filed: "N",
        })
      ),
    ];
    expect(monthlyRate(series, OIL_KEYS)).toBeCloseTo(300, 9);
  });

  test("only the trailing window counts", () => {
    // Fourteen months: two old ones at 6,000 then a year at 300. The window is
    // the last twelve, so the spike is out and the answer is 300, not 1,114.
    const series = [
      month({ cycle: "2023-11", oil_prod_vol: 6000 }),
      month({ cycle: "2023-12", oil_prod_vol: 6000 }),
      ...Array.from({ length: 12 }, (_, i) =>
        month({ cycle: `2024-${String(i + 1).padStart(2, "0")}`, oil_prod_vol: 300 })
      ),
    ];
    expect(monthlyRate(series, OIL_KEYS)).toBeCloseTo(300, 9);
  });

  test("nothing reported is zero, not a division by zero", () => {
    expect(monthlyRate([], OIL_KEYS)).toBe(0);
    expect(
      monthlyRate([month({ cycle: "2024-03", reported: false })], OIL_KEYS)
    ).toBe(0);
  });
});
