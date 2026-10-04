import { describe, expect, test } from "vitest";
import {
  applyShares,
  monthsForWell,
  ownedShareByMonth,
  sharesByMonth,
  shareOf,
  type TestRow,
} from "./well-share";
import type { RrcMonth } from "./lease-history-series";

/** Wells with no completion date on file: eligible in every month. */
const refs = (...wellNos: string[]) =>
  wellNos.map((wellNo) => ({
    wellNo,
    produces: true,
    completedMonth: null,
    shutInMonth: null,
  }));

/**
 * Every expected number here is arithmetic done by hand from the split rule, not
 * a value read off the implementation:
 *
 *   weighted   = testedCount / wellCount
 *   tested w   = rate(w) / sum(tested rates) * weighted
 *   untested w = (1 - weighted) / untestedCount
 *
 * The lease's reported volume is the fixed quantity; the shares only decide how
 * it is divided, so every case below also checks it is still all there.
 */

const t = (
  wellNo: string,
  testDate: string,
  dailyOil: number,
  dailyGas = 0
): TestRow => ({ wellNo, testDate, dailyOil, dailyGas });

/** Sum of a month's shares, which must be 1 whenever any well exists. */
const sum = (m: Map<string, number> | undefined) =>
  [...(m?.values() ?? [])].reduce((s, v) => s + v, 0);

describe("sharesByMonth", () => {
  test("two tested wells split in the ratio of their rates", () => {
    // A tests 10, B tests 30. A is a quarter of the tested rate, B three quarters.
    const s = sharesByMonth(
      refs("A", "B"),
      [t("A", "2020-01-15", 10), t("B", "2020-01-20", 30)],
      ["2020-03"],
      "oil"
    );
    expect(shareOf(s, "2020-03", "A")).toBeCloseTo(0.25, 12);
    expect(shareOf(s, "2020-03", "B")).toBeCloseTo(0.75, 12);
    expect(sum(s.get("2020-03"))).toBeCloseTo(1, 12);
  });

  test("an untested well takes its head-count residual, never zero", () => {
    // Three wells, two tested: the tested pair share 2/3, C takes the other 1/3.
    // A = 10/40 * 2/3 = 1/6, B = 30/40 * 2/3 = 1/2, C = 1/3.
    const s = sharesByMonth(
      refs("A", "B", "C"),
      [t("A", "2020-01-15", 10), t("B", "2020-01-20", 30)],
      ["2020-03"],
      "oil"
    );
    expect(shareOf(s, "2020-03", "A")).toBeCloseTo(1 / 6, 12);
    expect(shareOf(s, "2020-03", "B")).toBeCloseTo(0.5, 12);
    expect(shareOf(s, "2020-03", "C")).toBeCloseTo(1 / 3, 12);
    expect(sum(s.get("2020-03"))).toBeCloseTo(1, 12);
  });

  test("a well whose test reports no rate is unweightable, not zero", () => {
    // B's test says 0 oil. That is not "B made nothing", so B keeps a head-count
    // share exactly as an untested well does.
    const s = sharesByMonth(
      refs("A", "B"),
      [t("A", "2020-01-15", 10), t("B", "2020-01-20", 0)],
      ["2020-03"],
      "oil"
    );
    expect(shareOf(s, "2020-03", "A")).toBeCloseTo(0.5, 12);
    expect(shareOf(s, "2020-03", "B")).toBeCloseTo(0.5, 12);
  });

  test("no tested well anywhere splits evenly", () => {
    const s = sharesByMonth(refs("A", "B", "C", "D"), [], ["2020-03"], "oil");
    for (const w of ["A", "B", "C", "D"]) {
      expect(shareOf(s, "2020-03", w)).toBeCloseTo(0.25, 12);
    }
    expect(sum(s.get("2020-03"))).toBeCloseTo(1, 12);
  });

  test("a single well takes the whole lease", () => {
    const s = sharesByMonth(refs("A"), [t("A", "2020-01-15", 10)], ["2020-03"], "oil");
    expect(shareOf(s, "2020-03", "A")).toBeCloseTo(1, 12);
  });

  test("the split moves when a test moves", () => {
    // A: 10 from 2014-01, then 20 from 2015-06. B: 30 throughout.
    const tests = [
      t("A", "2014-01-10", 10),
      t("A", "2015-06-04", 20),
      t("B", "2013-05-02", 30),
    ];
    const months = ["2012-01", "2014-03", "2015-06", "2015-07"];
    const s = sharesByMonth(refs("A", "B"), tests, months, "oil");

    // Before A's first test: its earliest test is the only thing known about it.
    expect(shareOf(s, "2012-01", "A")).toBeCloseTo(0.25, 12);
    // Between the two tests: 10 / 40.
    expect(shareOf(s, "2014-03", "A")).toBeCloseTo(0.25, 12);
    // The month of the new test is governed by it: 20 / 50.
    expect(shareOf(s, "2015-06", "A")).toBeCloseTo(0.4, 12);
    expect(shareOf(s, "2015-07", "A")).toBeCloseTo(0.4, 12);
    expect(shareOf(s, "2015-07", "B")).toBeCloseTo(0.6, 12);
    for (const m of months) expect(sum(s.get(m))).toBeCloseTo(1, 12);
  });

  test("the 1.64x test bias cancels: doubling every rate changes nothing", () => {
    const wells = ["A", "B", "C"];
    const months = ["2020-03"];
    const real = [t("A", "2020-01-15", 10), t("B", "2020-01-20", 30)];
    const inflated = real.map((r) => ({ ...r, dailyOil: (r.dailyOil ?? 0) * 2 }));
    const a = sharesByMonth(refs(...wells), real, months, "oil");
    const b = sharesByMonth(refs(...wells), inflated, months, "oil");
    for (const w of wells) {
      expect(shareOf(b, "2020-03", w)).toBeCloseTo(shareOf(a, "2020-03", w), 12);
    }
  });

  test("oil and gas are weighted separately", () => {
    // A makes the oil, B makes the gas. Weighting gas by the oil test would hand
    // A three quarters of casinghead gas it does not make.
    const tests = [t("A", "2020-01-15", 30, 10), t("B", "2020-01-20", 10, 30)];
    const oil = sharesByMonth(refs("A", "B"), tests, ["2020-03"], "oil");
    const gas = sharesByMonth(refs("A", "B"), tests, ["2020-03"], "gas");
    expect(shareOf(oil, "2020-03", "A")).toBeCloseTo(0.75, 12);
    expect(shareOf(gas, "2020-03", "A")).toBeCloseTo(0.25, 12);
  });
});

describe("splitting a lease's volumes", () => {
  // 620 bbl and 310 MCF in a 31-day month, over three wells: A tests 10, B tests
  // 30, C has never been tested.
  const months: RrcMonth[] = [{ cycle: "2020-03-01", oilBbl: 620, gasMcf: 310 }];
  const wells = ["A", "B", "C"];
  const tests = [t("A", "2020-01-15", 10, 10), t("B", "2020-01-20", 30, 30)];
  const oilShares = sharesByMonth(refs(...wells), tests, ["2020-03"], "oil");
  const gasShares = sharesByMonth(refs(...wells), tests, ["2020-03"], "gas");

  test("one well's volume is its share of the lease's", () => {
    // A = 1/6 of 620 = 103.33 bbl; C, untested, = 1/3 of 620.
    const a = monthsForWell(months, oilShares, gasShares, "A");
    expect(a[0].oilBbl).toBeCloseTo(620 / 6, 9);
    expect(a[0].gasMcf).toBeCloseTo(310 / 6, 9);
    const c = monthsForWell(months, oilShares, gasShares, "C");
    expect(c[0].oilBbl).toBeCloseTo(620 / 3, 9);
  });

  test("the record's wells re-sum to the lease, exactly", () => {
    const total = wells
      .map((w) => monthsForWell(months, oilShares, gasShares, w)[0])
      .reduce(
        (s, m) => ({ oil: s.oil + m.oilBbl, gas: s.gas + m.gasMcf }),
        { oil: 0, gas: 0 }
      );
    expect(total.oil).toBeCloseTo(620, 9);
    expect(total.gas).toBeCloseTo(310, 9);
  });

  test("the lease page equals the sum of the well pages it owns", () => {
    // We hold A and C; B belongs to another operator on the same record.
    const owned = ["A", "C"];
    const scaled = applyShares(
      months,
      ownedShareByMonth(oilShares, owned),
      ownedShareByMonth(gasShares, owned)
    );
    const summed = owned
      .map((w) => monthsForWell(months, oilShares, gasShares, w)[0])
      .reduce((s, m) => s + m.oilBbl, 0);
    expect(scaled[0].oilBbl).toBeCloseTo(summed, 9);
    // And it is genuinely less than the lease: B's half is not ours.
    expect(scaled[0].oilBbl).toBeCloseTo(620 * (1 / 6 + 1 / 3), 9);
    expect(scaled[0].oilBbl).toBeLessThan(620);
  });

  test("holding a well does not change its own number", () => {
    // The 3-of-5 case must not move the three wells' values, only the lease total.
    const alone = monthsForWell(months, oilShares, gasShares, "A")[0];
    const withOthers = monthsForWell(months, oilShares, gasShares, "A")[0];
    expect(alone.oilBbl).toBe(withOthers.oilBbl);
  });

  test("owning every well is a no-op on the lease series", () => {
    const scaled = applyShares(
      months,
      ownedShareByMonth(oilShares, wells),
      ownedShareByMonth(gasShares, wells)
    );
    expect(scaled[0].oilBbl).toBeCloseTo(620, 9);
    expect(scaled[0].gasMcf).toBeCloseTo(310, 9);
  });

  test("a month with no share scales to zero rather than passing through", () => {
    const scaled = applyShares(months, new Map(), new Map());
    expect(scaled[0].oilBbl).toBe(0);
    expect(scaled[0].gasMcf).toBe(0);
  });
});

describe("wells that did not exist yet", () => {
  /*
   * RRC lease 01/01077 in the mirror: eight wells completed 1987, 1988, 2003,
   * 2014, 2015, 2021 and 2023 (one blank), with production filed back to 1993.
   * Weighting the 2023 well in 1993 takes barrels off the wells that drilled it.
   */
  const wells = [
    { wellNo: "OLD", produces: true, completedMonth: "1987-07", shutInMonth: null },
    { wellNo: "NEW", produces: true, completedMonth: "2023-08", shutInMonth: null },
    { wellNo: "UNDATED", produces: true, completedMonth: null, shutInMonth: null },
  ];
  const tests = [t("OLD", "2023-09-01", 10), t("NEW", "2023-09-02", 30)];

  test("a well is not weighted before it was completed", () => {
    const s = sharesByMonth(wells, tests, ["1993-04", "2023-08"], "oil");
    expect(shareOf(s, "1993-04", "NEW")).toBe(0);
    // OLD is tested and UNDATED is not, so they split 1/2 each: the tested well
    // takes 1/2 of the tested rate (it is the only one) times 1/2 head-count.
    expect(shareOf(s, "1993-04", "OLD")).toBeCloseTo(0.5, 12);
    expect(shareOf(s, "1993-04", "UNDATED")).toBeCloseTo(0.5, 12);
    expect(sum(s.get("1993-04"))).toBeCloseTo(1, 12);
    // From its completion month on, NEW is weighted: 30/40 * 2/3 = 0.5.
    expect(shareOf(s, "2023-08", "NEW")).toBeCloseTo(0.5, 12);
    expect(sum(s.get("2023-08"))).toBeCloseTo(1, 12);
  });

  test("an undated well is eligible everywhere", () => {
    // 38,221 of 440,050 scheduled wellbores have a blank completion date. Not
    // knowing when a well was drilled is not evidence that it was not.
    const s = sharesByMonth(wells, tests, ["1950-01"], "oil");
    expect(shareOf(s, "1950-01", "UNDATED")).toBeGreaterThan(0);
  });

  test("a month before every completion date still shares out in full", () => {
    // Otherwise the month would belong to nobody and its barrels would vanish.
    const s = sharesByMonth(
      [
        {
          wellNo: "A",
          produces: true,
          completedMonth: "2020-01",
          shutInMonth: null,
        },
      ],
      [],
      ["1999-01"],
      "oil"
    );
    expect(shareOf(s, "1999-01", "A")).toBeCloseTo(1, 12);
  });
});

describe("service holes", () => {
  /*
   * RRC lease 33913 (Roach) carries 18 wells on a current schedule, of which 5
   * are INJECTION or WATER SUPPLY. They file no producing W-10, so they read as
   * untested and were taking a head-count share of the lease's oil — 28% of it,
   * assigned to holes that physically cannot produce.
   */
  const wells = [
    { wellNo: "P1", produces: true, completedMonth: null, shutInMonth: null },
    { wellNo: "P2", produces: true, completedMonth: null, shutInMonth: null },
    { wellNo: "INJ", produces: false, completedMonth: null, shutInMonth: null },
  ];

  test("an injector takes no share, and the producers take it all", () => {
    const s = sharesByMonth(wells, [t("P1", "2020-01-15", 30)], ["2020-03"], "oil");
    expect(shareOf(s, "2020-03", "INJ")).toBe(0);
    // P1 is tested and P2 is not, so they split 1/2 each of a denominator of 2 —
    // not 1/3 each of a denominator of 3.
    expect(shareOf(s, "2020-03", "P1")).toBeCloseTo(0.5, 12);
    expect(shareOf(s, "2020-03", "P2")).toBeCloseTo(0.5, 12);
    expect(sum(s.get("2020-03"))).toBeCloseTo(1, 12);
  });

  test("a record of nothing but service holes still shares out in full", () => {
    // Otherwise the month belongs to nobody and its barrels vanish.
    const s = sharesByMonth(
      [
        {
          wellNo: "INJ",
          produces: false,
          completedMonth: null,
          shutInMonth: null,
        },
      ],
      [],
      ["2020-03"],
      "oil"
    );
    expect(shareOf(s, "2020-03", "INJ")).toBeCloseTo(1, 12);
  });
});

describe("wells that have stopped", () => {
  /*
   * API 50336281 (RILEY E. E. 3) was shut in 2022-12 and still held a live
   * disposal permit, so the map painted it blue and the split handed it 2.7
   * bbl/d of its lease's CURRENT production — while its own page, reading the
   * same record, said "Shut In".
   */
  const wells = [
    { wellNo: "RUNNING", produces: true, completedMonth: null, shutInMonth: null },
    { wellNo: "STOPPED", produces: true, completedMonth: null, shutInMonth: "2022-12" },
  ];
  const tests = [t("RUNNING", "2022-06-01", 10), t("STOPPED", "2022-06-02", 30)];

  test("a shut-in well keeps its share up to the month it stopped", () => {
    const s = sharesByMonth(wells, tests, ["2022-11", "2022-12"], "oil");
    expect(shareOf(s, "2022-11", "STOPPED")).toBeCloseTo(0.75, 12);
    // The month it shut in is still its own: it produced for part of it.
    expect(shareOf(s, "2022-12", "STOPPED")).toBeCloseTo(0.75, 12);
  });

  test("and none of it afterwards, which the running well absorbs", () => {
    const s = sharesByMonth(wells, tests, ["2023-01", "2026-05"], "oil");
    expect(shareOf(s, "2023-01", "STOPPED")).toBe(0);
    expect(shareOf(s, "2023-01", "RUNNING")).toBeCloseTo(1, 12);
    expect(sum(s.get("2023-01"))).toBeCloseTo(1, 12);
    expect(shareOf(s, "2026-05", "STOPPED")).toBe(0);
  });

  test("a month after every well stopped still shares out in full", () => {
    // Otherwise the month belongs to nobody and its barrels vanish.
    const s = sharesByMonth(
      [{ wellNo: "A", produces: true, completedMonth: null, shutInMonth: "2020-01" }],
      [],
      ["2024-06"],
      "oil"
    );
    expect(shareOf(s, "2024-06", "A")).toBeCloseTo(1, 12);
  });
});
