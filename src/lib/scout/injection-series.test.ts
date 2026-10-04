/**
 * The injection series, checked against what the Injection tab CLAIMS rather
 * than against what the builder happens to return.
 *
 * Every expected number below is worked out by hand from the intent stated in
 * `injection-series.ts`: a monthly total against a daily allowance times that
 * month's own days, a PSIG ceiling that does not scale with anything, and an
 * absent figure that stays absent instead of collapsing to zero. The last one
 * is the reason this file exists — a zero and a null render as very different
 * claims (a permit of nothing, versus no permit on file) and only one of them
 * is true.
 */
import { describe, expect, it } from "vitest";
import type { InjectionMonth, UicPermit } from "./rrc-types";
import {
  buildInjectionSeries,
  daysIn,
  permittedPressurePsig,
  type InjectionSeriesInput,
} from "./injection-series";

function month(
  cycle: string,
  bbl: number,
  avg: number | null,
  max: number | null,
  reported = true
): InjectionMonth {
  return { cycle, bbl, mcf: 0, avg_pressure: avg, max_pressure: max, reported };
}

/** A live salt-water disposal permit; override only what a case is about. */
function permit(over: Partial<UicPermit> = {}): UicPermit {
  return {
    uic_no: "000121032",
    api_number: "50331203",
    operator_no: "786408",
    operator_name: "SKY RESOURCES, INC.",
    lease_name: "ROACH SWD",
    uic_class: "2",
    inj_type: "1",
    approved_date: "2014-06-01",
    cancel_date: null,
    w3_date: null,
    max_bbl_per_day: 25_000,
    max_mcf_per_day: null,
    max_inj_pressure: 1_200,
    max_inj_pressure_note: null,
    top_inj_zone: 4_900,
    bot_inj_zone: 6_100,
    inj_mode: "T",
    is_commercial: true,
    fluid_comment: "PRODUCED SALT WATER",
    location: null,
    fluids: ["Salt water"],
    live: true,
    ...over,
  };
}

const BASE: InjectionSeriesInput = {
  monthly: [],
  window: "All",
  permittedBblPerDay: 25_000,
  permittedPressurePsig: 1_200,
  showVolumeCeiling: true,
  showPressure: true,
};

describe("daysIn", () => {
  it("counts the days of the month the cycle names", () => {
    expect(daysIn("2025-01")).toBe(31);
    expect(daysIn("2025-04")).toBe(30);
    expect(daysIn("2023-02")).toBe(28);
    // The whole reason the ceiling is redrawn per month rather than held flat.
    expect(daysIn("2024-02")).toBe(29);
  });
});

describe("permittedPressurePsig", () => {
  it("is the HIGHEST live permit's PSIG, not their sum", () => {
    // One wellhead and one gauge: 1,200 + 900 is not a pressure anything can
    // reach. 1,200 is.
    expect(
      permittedPressurePsig([
        permit({ uic_no: "A", max_inj_pressure: 1_200 }),
        permit({ uic_no: "B", max_inj_pressure: 900 }),
      ])
    ).toBe(1_200);
  });

  it("ignores permits that are no longer live", () => {
    // A 1988 permit for 3,000 PSIG says nothing about what this hole may do
    // today; the live one caps it at 1,200.
    expect(
      permittedPressurePsig([
        permit({ uic_no: "OLD", max_inj_pressure: 3_000, live: false }),
        permit({ uic_no: "NOW", max_inj_pressure: 1_200 }),
      ])
    ).toBe(1_200);
  });

  it("is null when every permit on the hole is dead", () => {
    expect(
      permittedPressurePsig([permit({ max_inj_pressure: 3_000, live: false })])
    ).toBeNull();
  });

  it("is null when the RRC stated the limit in prose instead of a number", () => {
    expect(
      permittedPressurePsig([
        permit({
          max_inj_pressure: null,
          max_inj_pressure_note: "0.5 PSI PER FOOT OF DEPTH",
        }),
      ])
    ).toBeNull();
  });

  it("treats a zero in the column as no limit stated, not a limit of zero", () => {
    expect(permittedPressurePsig([permit({ max_inj_pressure: 0 })])).toBeNull();
  });

  it("is null for a well with no permits at all", () => {
    expect(permittedPressurePsig([])).toBeNull();
  });
});

describe("the volume ceiling", () => {
  const monthly = [
    month("2024-01", 700_000, 900, 1_100),
    month("2024-02", 690_000, 910, 1_120),
    month("2024-04", 705_000, 905, 1_110),
  ];

  it("is the daily allowance times THAT month's days", () => {
    const s = buildInjectionSeries({ ...BASE, monthly });
    // 25,000 x 31 = 775,000. 25,000 x 29 (2024 is a leap year) = 725,000.
    // 25,000 x 30 = 750,000.
    expect(s.rows.map((r) => r.permitted)).toEqual([775_000, 725_000, 750_000]);
    expect(s.showVolumeCeiling).toBe(true);
  });

  it("draws nothing when the toggle is off", () => {
    const s = buildInjectionSeries({ ...BASE, monthly, showVolumeCeiling: false });
    expect(s.rows.every((r) => r.permitted === null)).toBe(true);
    expect(s.showVolumeCeiling).toBe(false);
  });

  it("draws nothing — not a zero line — when no rate is on file", () => {
    for (const rate of [null, 0]) {
      const s = buildInjectionSeries({ ...BASE, monthly, permittedBblPerDay: rate });
      expect(s.showVolumeCeiling).toBe(false);
      expect(s.rows.map((r) => r.permitted)).toEqual([null, null, null]);
    }
  });

  it("carries the injected volume through untouched", () => {
    const s = buildInjectionSeries({ ...BASE, monthly });
    expect(s.rows.map((r) => r.volume)).toEqual([700_000, 690_000, 705_000]);
  });
});

describe("the pressure series", () => {
  it("plots the average and the max, and bands the spread between them", () => {
    const s = buildInjectionSeries({
      ...BASE,
      monthly: [month("2024-01", 700_000, 900, 1_100)],
    });
    expect(s.rows[0].pressure).toBe(900);
    expect(s.rows[0].pressureMax).toBe(1_100);
    expect(s.rows[0].pressureBand).toEqual([900, 1_100]);
  });

  it("leaves a GAP for a month with no max filed, never a zero", () => {
    const s = buildInjectionSeries({
      ...BASE,
      monthly: [
        month("2024-01", 700_000, 900, 1_100),
        month("2024-02", 690_000, 910, null),
        month("2024-03", 705_000, 905, 1_130),
      ],
    });
    expect(s.rows.map((r) => r.pressureMax)).toEqual([1_100, null, 1_130]);
    // The band needs two edges. With one it is not drawn at half height off a
    // zero, which would claim a reading nobody took.
    expect(s.rows.map((r) => r.pressureBand)).toEqual([
      [900, 1_100],
      null,
      [905, 1_130],
    ]);
    // The average is unaffected by its neighbour's missing max.
    expect(s.rows.map((r) => r.pressure)).toEqual([900, 910, 905]);
  });

  it("leaves a gap in the band when only the max was filed", () => {
    const s = buildInjectionSeries({
      ...BASE,
      monthly: [month("2024-01", 700_000, null, 1_100)],
    });
    expect(s.rows[0].pressure).toBeNull();
    expect(s.rows[0].pressureMax).toBe(1_100);
    expect(s.rows[0].pressureBand).toBeNull();
  });

  it("orders a transposed pair rather than drawing it inside out", () => {
    // avg 1,150 above max 900 is an entry error, not a reading; the band is
    // still the spread between the two numbers on file.
    const s = buildInjectionSeries({
      ...BASE,
      monthly: [month("2024-01", 700_000, 1_150, 900)],
    });
    expect(s.rows[0].pressureBand).toEqual([900, 1_150]);
  });

  it("empties the whole PSIG axis when the overlay is off", () => {
    const s = buildInjectionSeries({
      ...BASE,
      monthly: [month("2024-01", 700_000, 900, 1_100)],
      showPressure: false,
    });
    const [r] = s.rows;
    expect(r.pressure).toBeNull();
    expect(r.pressureMax).toBeNull();
    expect(r.pressureBand).toBeNull();
    // The ceiling belongs to that axis, so it goes with it — and the volume
    // ceiling is untouched by the pressure toggle.
    expect(r.permittedPressure).toBeNull();
    expect(s.showPressureCeiling).toBe(false);
    expect(r.permitted).toBe(775_000);
  });

  it("offers the overlay whenever EITHER pressure was filed", () => {
    const only = (avg: number | null, max: number | null) =>
      buildInjectionSeries({
        ...BASE,
        monthly: [month("2024-01", 700_000, avg, max)],
      }).hasPressure;
    expect(only(900, 1_100)).toBe(true);
    expect(only(null, 1_100)).toBe(true);
    expect(only(900, null)).toBe(true);
    expect(only(null, null)).toBe(false);
    // Zeroes are how the H-10 spells "no gauge on this well".
    expect(only(0, 0)).toBe(false);
  });
});

describe("the pressure ceiling", () => {
  const monthly = [
    month("2024-01", 700_000, 900, 1_100),
    month("2024-02", 690_000, 980, 1_450),
  ];

  it("shows an exceedance as a crossing, with no arithmetic left to the reader", () => {
    const s = buildInjectionSeries({ ...BASE, monthly });
    expect(s.rows.map((r) => r.permittedPressure)).toEqual([1_200, 1_200]);
    // February's 1,450 is plotted ABOVE the 1,200 line that is drawn beside it;
    // January's 1,100 sits under it. That difference is the whole feature.
    expect(s.rows[0].pressureMax!).toBeLessThan(s.rows[0].permittedPressure!);
    expect(s.rows[1].pressureMax!).toBeGreaterThan(s.rows[1].permittedPressure!);
  });

  it("is flat: PSIG does not scale with the length of the month", () => {
    // Unlike the volume ceiling one row above it, which is 775,000 then 725,000.
    const s = buildInjectionSeries({ ...BASE, monthly });
    expect(new Set(s.rows.map((r) => r.permittedPressure)).size).toBe(1);
  });

  it("draws nothing for a well with no permitted maximum on file", () => {
    const s = buildInjectionSeries({
      ...BASE,
      monthly,
      permittedPressurePsig: permittedPressurePsig([
        permit({ max_inj_pressure: null, max_inj_pressure_note: "SEE PERMIT" }),
      ]),
    });
    expect(s.showPressureCeiling).toBe(false);
    // Null everywhere, so the chart has no series to draw. A 0 here would be a
    // line along the axis that every filed month towers over.
    expect(s.rows.map((r) => r.permittedPressure)).toEqual([null, null]);
    // The pressure the well DID report is still plotted; only the ceiling goes.
    expect(s.rows.map((r) => r.pressureMax)).toEqual([1_100, 1_450]);
  });

  it("draws nothing when the stated maximum is zero", () => {
    const s = buildInjectionSeries({ ...BASE, monthly, permittedPressurePsig: 0 });
    expect(s.showPressureCeiling).toBe(false);
    expect(s.rows.map((r) => r.permittedPressure)).toEqual([null, null]);
  });
});

describe("the H-10 reporting edge", () => {
  const monthly = [
    month("2024-10", 700_000, 900, 1_100),
    month("2024-11", 690_000, 910, 1_120),
    month("2024-12", 180_000, 905, 1_110, false),
    month("2025-01", 40_000, null, null, false),
  ];

  it("marks the tail from the FIRST unfiled month to the last month drawn", () => {
    const s = buildInjectionSeries({ ...BASE, monthly });
    expect(s.unreportedFrom).toBe("2024-12");
    expect(s.lastCycle).toBe("2025-01");
  });

  it("keeps the thin tail's volumes rather than hiding them", () => {
    // Some operators do file on time, so the tail is a fraction of the real
    // volume, not zero. It is shaded, not dropped.
    const s = buildInjectionSeries({ ...BASE, monthly });
    expect(s.rows.map((r) => r.volume)).toEqual([700_000, 690_000, 180_000, 40_000]);
    expect(s.rows.map((r) => r.reported)).toEqual([true, true, false, false]);
  });

  it("still ceilings the unfiled months, on both axes", () => {
    // The permit did not lapse because the paperwork is late.
    const s = buildInjectionSeries({ ...BASE, monthly });
    expect(s.rows[3].permitted).toBe(775_000); // 25,000 x 31 days in January
    expect(s.rows[3].permittedPressure).toBe(1_200);
  });

  it("shades nothing when every month in the window is filed", () => {
    const s = buildInjectionSeries({ ...BASE, monthly: monthly.slice(0, 2) });
    expect(s.unreportedFrom).toBeNull();
    expect(s.lastCycle).toBe("2024-11");
  });

  it("has no cycles at all for a well that never filed", () => {
    const s = buildInjectionSeries({ ...BASE, monthly: [] });
    expect(s.rows).toEqual([]);
    expect(s.unreportedFrom).toBeNull();
    expect(s.lastCycle).toBeNull();
    expect(s.hasPressure).toBe(false);
  });
});

describe("the window buttons", () => {
  // 130 months, 2015-01 through 2025-10: index 129 is 2015 + 10 years and 9
  // months, so October 2025.
  const monthly = Array.from({ length: 130 }, (_, i) => {
    const y = 2015 + Math.floor(i / 12);
    const m = String((i % 12) + 1).padStart(2, "0");
    return month(`${y}-${m}`, 700_000, 900, 1_100);
  });

  it("5Y is the last 60 months", () => {
    const s = buildInjectionSeries({ ...BASE, monthly, window: "5Y" });
    expect(s.rows).toHaveLength(60);
    // 130 - 60 = index 70 = 2015-01 plus 5 years and 10 months.
    expect(s.rows[0].cycle).toBe("2020-11");
    expect(s.lastCycle).toBe("2025-10");
  });

  it("10Y is the last 120 months", () => {
    const s = buildInjectionSeries({ ...BASE, monthly, window: "10Y" });
    expect(s.rows).toHaveLength(120);
    expect(s.rows[0].cycle).toBe("2015-11");
    expect(s.lastCycle).toBe("2025-10");
  });

  it("All is every month on file", () => {
    const s = buildInjectionSeries({ ...BASE, monthly, window: "All" });
    expect(s.rows).toHaveLength(130);
    expect(s.rows[0].cycle).toBe("2015-01");
  });

  it("does not offer the pressure overlay for a window with no readings in it", () => {
    // Gauge fitted in 2024: the 5Y window has pressure, the 10Y window's older
    // half does not change that, but a window ending before it does.
    const gauged = monthly.map((m) =>
      m.cycle >= "2024-01" ? m : { ...m, avg_pressure: null, max_pressure: null }
    );
    expect(buildInjectionSeries({ ...BASE, monthly: gauged, window: "5Y" }).hasPressure).toBe(
      true
    );
    expect(
      buildInjectionSeries({
        ...BASE,
        monthly: gauged.slice(0, 60),
        window: "All",
      }).hasPressure
    ).toBe(false);
  });
});
