import { describe, expect, test } from "vitest";
import {
  earliestMeasuredDate,
  expandMonthlyToDaily,
  type RrcMonth,
} from "./lease-history-series";

/**
 * The oracle here is arithmetic done by hand, not the function's own output:
 * a month's volume divided by that month's real day count, laid on every day of
 * the month, cut strictly before the operator's first record.
 */

const month = (over: Partial<RrcMonth> & { cycle: string }): RrcMonth => ({
  oilBbl: 0,
  gasMcf: 0,
  ...over,
});

describe("expandMonthlyToDaily", () => {
  test("spreads a month's volume evenly across its days", () => {
    // 310 bbl over a 31-day month is 10 bbl/d.
    const { oil } = expandMonthlyToDaily(
      [month({ cycle: "2024-01-01", oilBbl: 310 })],
      null
    );
    expect(oil).toHaveLength(31);
    expect(oil[0]).toEqual({ date: "2024-01-01", value: 10 });
    expect(oil[30]).toEqual({ date: "2024-01-31", value: 10 });
  });

  test("uses each month's real length, including February in a leap year", () => {
    // 290 bbl / 29 days = 10 bbl/d. A hardcoded 30 or 31 would give 9.67 or 9.35.
    const { oil } = expandMonthlyToDaily(
      [month({ cycle: "2024-02-01", oilBbl: 290 })],
      null
    );
    expect(oil).toHaveLength(29);
    expect(oil[28]).toEqual({ date: "2024-02-29", value: 10 });
  });

  test("a non-leap February is 28 days", () => {
    const { oil } = expandMonthlyToDaily(
      [month({ cycle: "2023-02-01", oilBbl: 280 })],
      null
    );
    expect(oil).toHaveLength(28);
    expect(oil[27]).toEqual({ date: "2023-02-28", value: 10 });
  });

  test("the daily rates re-integrate to the reported monthly volume", () => {
    // The whole point of a rate series: no barrels invented, none lost.
    const months = [
      month({ cycle: "2024-01-01", oilBbl: 457, gasMcf: 1234 }),
      month({ cycle: "2024-02-01", oilBbl: 301, gasMcf: 999 }),
    ];
    const { oil, gas } = expandMonthlyToDaily(months, null);
    expect(oil.reduce((s, p) => s + p.value, 0)).toBeCloseTo(457 + 301, 6);
    expect(gas.reduce((s, p) => s + p.value, 0)).toBeCloseTo(1234 + 999, 6);
  });

  test("stops strictly before the operator's first record", () => {
    // The boundary day belongs to the operator, so the state's series must not
    // reach it — an overlap would double-count that day on the chart.
    const { oil } = expandMonthlyToDaily(
      [month({ cycle: "2024-03-01", oilBbl: 310 })],
      "2024-03-10"
    );
    expect(oil).toHaveLength(9);
    expect(oil[oil.length - 1].date).toBe("2024-03-09");
    expect(oil.some((p) => p.date === "2024-03-10")).toBe(false);
  });

  test("a boundary before all history yields nothing", () => {
    const { oil } = expandMonthlyToDaily(
      [month({ cycle: "2024-03-01", oilBbl: 310 })],
      "2024-01-01"
    );
    expect(oil).toEqual([]);
  });

  test("a stream the lease never reported stays empty, not a line of zeros", () => {
    // An oil lease that never made gas must not draw a gas history implying it
    // was measured and found to be nothing.
    const { oil, gas } = expandMonthlyToDaily(
      [month({ cycle: "2024-01-01", oilBbl: 310 })],
      null
    );
    expect(oil).toHaveLength(31);
    expect(gas).toEqual([]);
  });

  test("a zero month BETWEEN reported months is kept", () => {
    // Shut in for a month is information; dropping it would close the gap and
    // imply continuous production.
    const { oil } = expandMonthlyToDaily(
      [
        month({ cycle: "2024-01-01", oilBbl: 310 }),
        month({ cycle: "2024-02-01", oilBbl: 0 }),
        month({ cycle: "2024-03-01", oilBbl: 310 }),
      ],
      null
    );
    expect(oil).toHaveLength(31 + 29 + 31);
    expect(oil.find((p) => p.date === "2024-02-15")?.value).toBe(0);
  });

  test("trailing zero months are dropped, not drawn as a cliff", () => {
    /*
     * Texas runs two to three months behind and files the months it has not
     * collected as zero, which `prod_report_filed = 'Y'` does not exclude. Real
     * case, gas record 7B/126318: 130 MCF in Nov 2025, 125 in Dec, then 0.0 for
     * Jan through May 2026. Drawn as-is the chart falls off a cliff to nothing
     * at its right-hand edge, and the well reads as dead.
     */
    const { gas } = expandMonthlyToDaily(
      [
        month({ cycle: "2025-11-01", gasMcf: 130 }),
        month({ cycle: "2025-12-01", gasMcf: 125 }),
        month({ cycle: "2026-01-01", gasMcf: 0 }),
        month({ cycle: "2026-02-01", gasMcf: 0 }),
      ],
      null
    );
    expect(gas).toHaveLength(30 + 31);
    expect(gas.at(-1)?.date).toBe("2025-12-31");
  });

  test("a stream that never reported draws nothing, even beside one that did", () => {
    /*
     * A gas well's oil column is zero for its whole life. Drawing it produces a
     * flat zero line across the chart and an axis in denormals (2e-323), which
     * is what an all-zero series does to a chart's domain.
     */
    const { oil, gas } = expandMonthlyToDaily(
      [
        month({ cycle: "2024-01-01", gasMcf: 310 }),
        month({ cycle: "2024-02-01", gasMcf: 290 }),
      ],
      null
    );
    expect(oil).toEqual([]);
    expect(gas).toHaveLength(31 + 29);
  });

  test("leading zero months are dropped too", () => {
    // A lease filed before it produced anything should start where it started.
    const { oil } = expandMonthlyToDaily(
      [
        month({ cycle: "2024-01-01", oilBbl: 0 }),
        month({ cycle: "2024-02-01", oilBbl: 290 }),
      ],
      null
    );
    expect(oil).toHaveLength(29);
    expect(oil[0].date).toBe("2024-02-01");
  });

  test("output is sorted by date regardless of input order", () => {
    const { oil } = expandMonthlyToDaily(
      [
        month({ cycle: "2024-03-01", oilBbl: 31 }),
        month({ cycle: "2024-01-01", oilBbl: 31 }),
      ],
      null
    );
    const dates = oil.map((p) => p.date);
    expect([...dates].sort()).toEqual(dates);
    expect(dates[0]).toBe("2024-01-01");
  });

  test("empty input and unparseable cycles are dropped, not thrown on", () => {
    expect(expandMonthlyToDaily([], null)).toEqual({ oil: [], gas: [] });
    expect(
      expandMonthlyToDaily([month({ cycle: "garbage", oilBbl: 10 })], null).oil
    ).toEqual([]);
    expect(
      expandMonthlyToDaily([month({ cycle: "2024-13-01", oilBbl: 10 })], null).oil
    ).toEqual([]);
  });

  test("a full ISO timestamp cycle is read as its month", () => {
    const { oil } = expandMonthlyToDaily(
      [month({ cycle: "2024-04-01T00:00:00.000Z", oilBbl: 300 })],
      null
    );
    expect(oil).toHaveLength(30);
    expect(oil[0].date).toBe("2024-04-01");
  });
});

describe("earliestMeasuredDate", () => {
  test("is the earliest date across every stream the operator records", () => {
    expect(
      earliestMeasuredDate(
        [{ date: "2025-03-04" }, { date: "2025-03-09" }],
        [{ date: "2025-01-22" }],
        [{ date: "2025-06-01" }]
      )
    ).toBe("2025-01-22");
  });

  test("null when the operator has recorded nothing", () => {
    expect(earliestMeasuredDate([], [], [])).toBe(null);
  });

  test("ignores empty streams beside populated ones", () => {
    expect(earliestMeasuredDate([], [{ date: "2025-02-02" }])).toBe("2025-02-02");
  });
});
