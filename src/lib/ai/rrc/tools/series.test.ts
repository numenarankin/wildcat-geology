import { beforeEach, describe, expect, test, vi } from "vitest";

import type { LeaseMonth } from "../../../scout/rrc-types";

/**
 * The time-series catalog, against hand-built leases whose right answer is
 * known before the code runs.
 *
 * Every fixture is generated from a stated law (a rate in barrels PER DAY, and
 * a month length written out below) and the expected answer is derived from
 * that law, never from a previous run. The three properties worth the most:
 *
 *  1. The unpublished tail is dropped before any arithmetic. The RRC runs about
 *     three cycles behind and those months sit in the mirror as zeros, so a fit
 *     or an average through them reports a collapse that is not happening.
 *  2. Volumes become daily rates first. A 28-day February against a 31-day
 *     January is a 10% artefact, and a decline tool that reads it as real is
 *     wrong in the direction operators act on.
 *  3. Nulls are "not reported", so they leave the arithmetic rather than
 *     entering it as zero.
 */

const db = vi.hoisted(() => ({
  /** Last cycle the RRC has published. Everything after it is unfiled. */
  edge: "2024-12",
  leases: new Map<string, { name: string; monthly: LeaseMonth[] }>(),
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getCycleEdge: async () => ({ reported: db.edge, loaded: db.edge }),
  getLeaseDossier: async (oilGasCode: string, districtNo: string, leaseNo: string) => {
    const row = db.leases.get(`${oilGasCode}/${districtNo}/${leaseNo}`);
    if (!row) return null;
    return {
      oil_gas_code: oilGasCode,
      district_no: districtNo,
      lease_no: leaseNo,
      lease_name: row.name,
      monthly: row.monthly,
    };
  },
  getWellDossier: async () => null,
  getOperatorDossier: async () => null,
  getFieldProfile: async () => null,
  getCountyProfile: async () => null,
  getProductionTrend: async () => [],
}));

const { TOOLS } = await import("./series");

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Result = any;

const call = async (name: string, args: Record<string, unknown>): Promise<Result> => {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`No tool ${name}. Have: ${TOOLS.map((t) => t.name).join(", ")}`);
  return (await tool.run(tool.args.parse(args) as never)) as Result;
};

// --------------------------------------------------------------- fixtures

/**
 * Days per calendar month, written out rather than computed, so the day count
 * this test divides by is independent of the one the code divides by. 2024 is a
 * leap year and 2023 is not, and both appear below on purpose.
 */
const DAYS: Record<string, number> = {
  "01": 31, "02": 28, "03": 31, "04": 30, "05": 31, "06": 30,
  "07": 31, "08": 31, "09": 30, "10": 31, "11": 30, "12": 31,
};
const days = (cycle: string) => (cycle === "2024-02" ? 29 : DAYS[cycle.slice(5)]);

function cycles(start: string, n: number): string[] {
  const [y, m] = start.split("-").map(Number);
  return Array.from({ length: n }, (_, i) => {
    const t = y * 12 + (m - 1) + i;
    return `${Math.floor(t / 12)}-${String((t % 12) + 1).padStart(2, "0")}`;
  });
}

function month(cycle: string, over: Partial<LeaseMonth> = {}): LeaseMonth {
  return {
    cycle,
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
  };
}

/** A month whose oil volume is exactly `rate` barrels per day times its length. */
const atRate = (cycle: string, rate: number, over: Partial<LeaseMonth> = {}) =>
  month(cycle, { oil_prod_vol: rate * days(cycle), ...over });

function lease(key: string, name: string, monthly: LeaseMonth[]) {
  db.leases.set(key, { name, monthly });
  const [oil_gas_code, district_no, lease_no] = key.split("/");
  return { entity: "lease" as const, oil_gas_code, district_no, lease_no };
}

/** A pure exponential decline: 100 bbl/d at t=0 falling at 50%/yr nominal. */
const QI = 100;
const DI = 0.5;
const declineRate = (k: number) => QI * Math.exp((-DI * k) / 12);

beforeEach(() => {
  db.edge = "2024-12";
  db.leases.clear();
});

// ------------------------------------------------------------ the tail rule

describe("the unpublished tail", () => {
  /** 24 filed months of decline, then three cycles the RRC has not published. */
  const withTail = () =>
    lease("O/08/11111", "TAILED", [
      ...cycles("2023-01", 24).map((c, k) => atRate(c, declineRate(k))),
      ...cycles("2025-01", 3).map((c) => month(c, { oil_prod_vol: 0, reported: false })),
    ]);
  /** The same lease, minus the three unpublished cycles. */
  const noTail = () =>
    lease(
      "O/08/11112",
      "CLEAN",
      cycles("2023-01", 24).map((c, k) => atRate(c, declineRate(k)))
    );

  test("rrc_series lists the unfiled cycles apart from the record", async () => {
    const r = await call("rrc_series", { ...withTail(), stream: "oil" });
    expect(r.ok).toBe(true);
    expect(r.reportedMonths).toBe(24);
    expect(r.points).toHaveLength(24);
    expect(r.points[23].cycle).toBe("2024-12");
    expect(r.unpublishedTail).toEqual(["2025-01", "2025-02", "2025-03"]);
    expect(r.reportedThrough).toBe("2024-12");
  });

  test("the decline is fitted to the filed months and is identical without the tail", async () => {
    const tailed = await call("rrc_decline", { ...withTail(), stream: "oil" });
    const clean = await call("rrc_decline", { ...noTail(), stream: "oil" });

    // Same lease, one with three unfiled zeros appended: the same fit or the
    // tail got into the arithmetic.
    expect(tailed.fit).toEqual(clean.fit);

    // The fixture IS q(t) = 100·exp(-0.5t), t in years from 2023-01, so the
    // fit must recover it: b = 0 (exponential), Di = 0.5/yr, qi = 100 bbl/d.
    expect(tailed.fit.b).toBe(0);
    expect(tailed.fit.Di).toBeCloseTo(DI, 9);
    expect(tailed.fit.qi).toBeCloseTo(QI, 6);
    expect(tailed.fit.startMonth).toBe("2023-01");
    expect(tailed.fit.monthsFitted).toBe(24);
    expect(tailed.fit.spanYears).toBeCloseTo(23 / 12, 12);
    expect(tailed.fit.r2Log).toBeCloseTo(1, 9);

    // The rate at the end of the window is 100·exp(-0.5·23/12) = 38.35 bbl/d.
    // Read through the zeros it would be a well on its way to nothing.
    expect(tailed.fit.currentRate).toBeCloseTo(QI * Math.exp((-DI * 23) / 12), 6);
    expect(tailed.fit.currentRate).toBeGreaterThan(35);
    // Exponential, so the next 12 months lose 1 - exp(-0.5) = 39.35%.
    expect(tailed.fit.forward12moDecline).toBeCloseTo(1 - Math.exp(-DI), 9);
    expect(tailed.reportedThrough).toBe("2024-12");
  });

  test("remaining reserves integrate forward from the window end, not from t=0", async () => {
    const r = await call("rrc_decline", { ...withTail(), stream: "oil" });
    // Closed form of the same integral: q at the window end, times the
    // geometric sum of exp(-Di·k/12) for k = 1..600, times days per month.
    const qEnd = QI * Math.exp((-DI * 23) / 12);
    const x = Math.exp(-DI / 12);
    const expected = qEnd * ((x * (1 - x ** 600)) / (1 - x)) * (365.25 / 12);
    expect(r.fit.remainingEur).toBeCloseTo(expected, 3);
    expect(r.fit.horizonYears).toBe(50);
    expect(r.fit.yearsToLimit).toBeNull();
  });

  test("an economic limit stops the integral, and 600 months is the horizon", async () => {
    // q falls below 10 bbl/d when 38.3533·exp(-0.5k/12) < 10, i.e.
    // k > 12·ln(3.83533)/0.5 = 32.24 months, so the 33rd forward month is the
    // first below it and 32 whole months are booked.
    const r = await call("rrc_decline", { ...withTail(), stream: "oil", economic_limit: 10 });
    expect(r.economicLimit).toBe(10);
    expect(r.fit.yearsToLimit).toBeCloseTo(32 / 12, 12);
  });

  test("trailing averages skip the unfiled zeros", async () => {
    const r = await call("rrc_series_stats", { ...withTail(), stream: "oil" });
    expect(r.reportedMonths).toBe(24);
    expect(r.firstCycle).toBe("2023-01");
    expect(r.lastCycle).toBe("2024-12");

    // Mean of the last three FILED daily rates. Counting the three unfiled
    // zeros instead would put this at 19.2, and last1 at 0.
    const last3 = (declineRate(21) + declineRate(22) + declineRate(23)) / 3;
    expect(r.dailyRate.last3).toBeCloseTo(last3, 9);
    expect(r.dailyRate.last1).toBeCloseTo(declineRate(23), 9);

    // One month of a 50%/yr exponential is exp(-0.5/12) - 1 = -4.08%.
    // Against an unfiled zero it would read -100%.
    expect(r.momPct).toBeCloseTo((Math.exp(-DI / 12) - 1) * 100, 9);
  });
});

// --------------------------------------------------- volumes to daily rates

describe("month length", () => {
  /** A well that never changes: 100 bbl/d for all twelve months of 2024. */
  const flat = () =>
    lease(
      "O/08/22222",
      "STEADY",
      cycles("2024-01", 12).map((c) => atRate(c, 100))
    );

  test("a 29-day February is not a drop", async () => {
    const r = await call("rrc_series", { ...flat(), stream: "oil" });
    // The volumes really do fall 6.5% from January to February.
    expect(r.points[0].volume).toBe(3100);
    expect(r.points[1].volume).toBe(2900);
    // The rate does not move at all, and that is what the analysis reads.
    expect(r.points.every((p: Result) => p.dailyRate === 100)).toBe(true);
  });

  test("month-over-month is zero on a steady well", async () => {
    const r = await call("rrc_series_stats", { ...flat(), stream: "oil" });
    // Volume-over-volume from November (30 d) to December (31 d) would read
    // +3.33%; the rate reads 0.
    expect(r.momPct).toBe(0);
    expect(r.dailyRate.last3).toBe(100);
    expect(r.dailyRate.last12).toBe(100);
    expect(r.peak).toEqual({ cycle: "2024-01", dailyRate: 100 });
    expect(r.monthsSincePeak).toBe(11);
    expect(r.producingMonths).toBe(12);
    expect(r.idleMonths).toBe(0);
    expect(r.intermittency).toBe(0);
  });

  test("a steady well is projected steady", async () => {
    const r = await call("rrc_decline", { ...flat(), stream: "oil" });
    // 100 bbl/d in, 100 bbl/d out, and nothing lost over the next year.
    expect(r.fit.currentRate).toBeCloseTo(100, 9);
    expect(r.fit.forward12moDecline).toBeCloseTo(0, 12);
    // With no economic limit the reserve is just the 50-year horizon integral:
    // 100 bbl/d over 600 months of 365.25/12 days. The limit is what makes this
    // number mean anything, which is why the horizon is reported beside it.
    expect(r.fit.remainingEur).toBeCloseTo(100 * 600 * (365.25 / 12), 6);
    expect(r.fit.horizonYears).toBe(50);
  });

  test("a rising well has no decline to fit, and is told so", async () => {
    const rising = lease(
      "O/08/22224",
      "RISING",
      cycles("2024-01", 8).map((c, i) => atRate(c, 100 + 10 * i))
    );
    const r = await call("rrc_decline", { ...rising, stream: "oil" });
    expect(r.fit).toBeNull();
    expect(r.reason).toBe(
      "No sustained post-peak decline in the reported window (flat or rising)."
    );
  });

  test("fewer than six producing months names the shortfall", async () => {
    const short = lease(
      "O/08/22223",
      "YOUNG",
      cycles("2024-09", 4).map((c) => atRate(c, 100))
    );
    const r = await call("rrc_decline", { ...short, stream: "oil" });
    expect(r.fit).toBeNull();
    expect(r.reason).toBe("Only 4 reported producing months; a fit needs 6.");
  });

  test("IP is volume over calendar days, from the first producing month", async () => {
    // Idle January, then Feb-Apr at 100 bbl/d and May-Jul at 120 bbl/d, 2024.
    const rates = [0, 100, 100, 100, 120, 120, 120];
    const ip = lease(
      "O/08/55555",
      "NEW HOLE",
      cycles("2024-01", 7).map((c, i) => atRate(c, rates[i]))
    );
    const r = await call("rrc_ip", { ...ip, stream: "oil" });

    expect(r.firstProduction).toBe("2024-02");
    expect(r.monthsOfHistory).toBe(6);
    // February is 29 days in 2024. Dividing by 30 would say 96.7.
    expect(r.ip30).toBeCloseTo(100, 12);
    expect(r.ip90).toBeCloseTo(100, 12);
    // (100·(29+31+30) + 120·(31+30+31)) / 182 = 20040/182.
    expect(r.ip180).toBeCloseTo(20040 / 182, 12);
    expect(r.peak).toEqual({ cycle: "2024-05", dailyRate: 120 });
    expect(r.monthsToPeak).toBe(3);
  });
});

// ------------------------------------------------------------ portfolio roll

describe("rrc_portfolio_roll", () => {
  /**
   * Lease A files all three months. Lease B files January only: February is
   * absent from the mirror and March is present but carries
   * `prod_report_filed = 'N'`, which is unfiled, not idle.
   */
  const setUp = () => {
    lease("O/08/31001", "ALPHA", [
      month("2024-01", { oil_prod_vol: 1000 }),
      month("2024-02", { oil_prod_vol: 2000 }),
      month("2024-03", { oil_prod_vol: 3000 }),
    ]);
    lease("O/08/31002", "BETA", [
      month("2024-01", { oil_prod_vol: 500 }),
      month("2024-03", { oil_prod_vol: 0, prod_report_filed: "N" }),
    ]);
    return ["O/08/31001", "O/08/31002"];
  };

  test("skip drops the incomplete months and counts them", async () => {
    const r = await call("rrc_portfolio_roll", {
      leases: setUp(),
      stream: "oil",
      missing: "skip",
    });
    expect(r.leaseCount).toBe(2);
    expect(r.cyclesInUniverse).toBe(3);
    // Only January has both leases.
    expect(r.series).toEqual([
      { cycle: "2024-01", total: 1500, reporting: 2, missing: 0 },
    ]);
    expect(r.affectedMonths).toBe(2);
    expect(r.missingLeaseMonths).toBe(2);
    expect(r.skippedMonths).toBe(2);
    expect(r.leases).toEqual([
      { key: "O/08/31001", label: "ALPHA", filedMonths: 3, unfiledMonths: 0 },
      { key: "O/08/31002", label: "BETA", filedMonths: 1, unfiledMonths: 1 },
    ]);
  });

  test("zero keeps the months and lets the absent lease count as nothing", async () => {
    const r = await call("rrc_portfolio_roll", {
      leases: setUp(),
      stream: "oil",
      missing: "zero",
    });
    expect(r.series).toEqual([
      { cycle: "2024-01", total: 1500, reporting: 2, missing: 0 },
      { cycle: "2024-02", total: 2000, reporting: 1, missing: 1 },
      { cycle: "2024-03", total: 3000, reporting: 1, missing: 1 },
    ]);
    // The same two months are called out; none of them is dropped.
    expect(r.affectedMonths).toBe(2);
    expect(r.missingLeaseMonths).toBe(2);
    expect(r.skippedMonths).toBe(0);
  });

  test("the two policies disagree, which is the whole point of asking", async () => {
    const leases = setUp();
    const skip = await call("rrc_portfolio_roll", { leases, stream: "oil", missing: "skip" });
    const zero = await call("rrc_portfolio_roll", { leases, stream: "oil", missing: "zero" });
    expect(skip.series).not.toEqual(zero.series);
    const total = (r: Result) => r.series.reduce((a: number, s: Result) => a + s.total, 0);
    expect(total(skip)).toBe(1500);
    expect(total(zero)).toBe(6500);
  });

  test("a portfolio larger than the cohort cap says it was cut", async () => {
    // 51 leases, one over MAX_COHORT. A total quietly missing a lease is worse
    // than a total that says it is partial.
    const keys = Array.from({ length: 51 }, (_, i) => {
      const key = `O/08/9${String(i).padStart(4, "0")}`;
      lease(key, `L${i}`, [month("2024-01", { oil_prod_vol: 10 })]);
      return key;
    });
    const r = await call("rrc_portfolio_roll", { leases: keys, stream: "oil", missing: "zero" });
    expect(r.leaseCount).toBe(50);
    expect(r.truncated).toBe(true);
  });
});

// ------------------------------------------------------------- type curve

describe("rrc_type_curve", () => {
  /**
   * Five leases at 10, 20, 30, 40 and 50 bbl/d in their first producing month,
   * each halving monthly. Two start on different calendar dates and one has a
   * leading idle month, so month 0 can only be right if the tool normalises to
   * FIRST PRODUCTION rather than to a shared calendar month.
   */
  const cohort = () => {
    const curve = (base: number) => [base, base / 2, base / 4];
    lease("O/08/71001", "C1", cycles("2024-01", 3).map((c, i) => atRate(c, curve(10)[i])));
    lease(
      "O/08/71002",
      "C2",
      cycles("2024-01", 4).map((c, i) => atRate(c, i === 0 ? 0 : curve(20)[i - 1]))
    );
    lease("O/08/71003", "C3", cycles("2023-06", 3).map((c, i) => atRate(c, curve(30)[i])));
    lease("O/08/71004", "C4", cycles("2024-01", 3).map((c, i) => atRate(c, curve(40)[i])));
    // Only two months, so the band thins at t = 2.
    lease("O/08/71005", "C5", cycles("2024-01", 2).map((c, i) => atRate(c, curve(50)[i])));
    return ["O/08/71001", "O/08/71002", "O/08/71003", "O/08/71004", "O/08/71005"];
  };

  test("percentiles match the ones computed by hand", async () => {
    const r = await call("rrc_type_curve", { leases: cohort(), stream: "oil" });
    expect(r.curve).toHaveLength(3);

    // Month 0: sorted [10, 20, 30, 40, 50]. Linear interpolation at rank
    // 4·0.9 = 3.6 gives 40 + 0.6·10 = 46 for p10; the median is 30; rank
    // 4·0.1 = 0.4 gives 10 + 0.4·10 = 14 for p90.
    expect(r.curve[0]).toEqual({ month: 0, n: 5, p10: 46, p50: 30, p90: 14, mean: 30 });
    // Month 1: every rate halved, so every statistic halves.
    expect(r.curve[1]).toEqual({ month: 1, n: 5, p10: 23, p50: 15, p90: 7, mean: 15 });
    // Month 2: C5 has aged out. Sorted [2.5, 5, 7.5, 10]; rank 3·0.9 = 2.7
    // gives 7.5 + 0.7·2.5 = 9.25, rank 1.5 gives 6.25, rank 0.3 gives 3.25.
    expect(r.curve[2].n).toBe(4);
    expect(r.curve[2].p10).toBeCloseTo(9.25, 12);
    expect(r.curve[2].p50).toBeCloseTo(6.25, 12);
    expect(r.curve[2].p90).toBeCloseTo(3.25, 12);
    expect(r.curve[2].mean).toBeCloseTo(6.25, 12);

    // p10 is the HIGH case, which is the reserves convention and the opposite
    // of the statistical one.
    expect(r.curve[0].p10).toBeGreaterThan(r.curve[0].p50);
    expect(r.curve[0].p50).toBeGreaterThan(r.curve[0].p90);
  });

  test("month zero is each lease's own first production", async () => {
    const r = await call("rrc_type_curve", { leases: cohort(), stream: "oil" });
    expect(r.leases).toEqual([
      { key: "O/08/71001", label: "C1", firstProduction: "2024-01", months: 3 },
      // The idle January is not month 0.
      { key: "O/08/71002", label: "C2", firstProduction: "2024-02", months: 3 },
      // A different year entirely, still month 0.
      { key: "O/08/71003", label: "C3", firstProduction: "2023-06", months: 3 },
      { key: "O/08/71004", label: "C4", firstProduction: "2024-01", months: 3 },
      { key: "O/08/71005", label: "C5", firstProduction: "2024-01", months: 2 },
    ]);
    expect(r.truncated).toBe(false);
  });

  test("one resolvable lease is not a cohort", async () => {
    cohort();
    const r = await call("rrc_type_curve", { leases: ["O/08/71001", "O/08/NOPE"], stream: "oil" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("at least 2 leases");
  });
});

// ------------------------------------------------------------- uncertainty

describe("rrc_decline_ci", () => {
  /** A real decline with a deterministic wiggle, so residuals are not zero. */
  const noisy = () =>
    lease(
      "O/08/44444",
      "NOISY",
      cycles("2022-07", 30).map((c, k) =>
        atRate(c, declineRate(k) * (1 + 0.08 * Math.sin(k * 1.7)))
      )
    );

  test("the same seed reproduces exactly, a different seed does not, and Math.random is never touched", async () => {
    const args = { ...noisy(), stream: "oil", iterations: 40 };
    const random = vi.spyOn(Math, "random");

    const first = await call("rrc_decline_ci", { ...args, seed: 7 });
    const again = await call("rrc_decline_ci", { ...args, seed: 7 });
    const other = await call("rrc_decline_ci", { ...args, seed: 8 });

    expect(again).toEqual(first);
    expect(other.ci).not.toEqual(first.ci);
    // The one part of this catalog carrying error bars is the one part nobody
    // could check if it drew from an unseeded generator.
    expect(random).not.toHaveBeenCalled();
    random.mockRestore();

    expect(first.seed).toBe(7);
    expect(first.iterations).toBe(40);
    expect(first.converged).toBeGreaterThan(0);
    expect(first.converged).toBeLessThanOrEqual(40);
    expect(first.reportedThrough).toBe("2024-12");
  });

  test("the band brackets its own median and the point fit sits inside it", async () => {
    const r = await call("rrc_decline_ci", { ...noisy(), stream: "oil", seed: 3, iterations: 60 });
    for (const key of ["qi", "Di", "b", "remainingEur"] as const) {
      expect(r.ci[key].lo).toBeLessThanOrEqual(r.ci[key].median);
      expect(r.ci[key].median).toBeLessThanOrEqual(r.ci[key].hi);
    }
    expect(r.fit.qi).toBeGreaterThanOrEqual(r.ci.qi.lo);
    expect(r.fit.qi).toBeLessThanOrEqual(r.ci.qi.hi);
  });

  test("a series with no decline says so and still says where the record stops", async () => {
    const rising = lease(
      "O/08/44445",
      "RISING",
      cycles("2024-01", 8).map((c, i) => atRate(c, 100 + 10 * i))
    );
    const r = await call("rrc_decline_ci", { ...rising, stream: "oil", seed: 1 });
    expect(r.fit).toBeNull();
    expect(r.reason).toContain("flat or rising");
    // Every result carries the edge, including this one: without it the reader
    // cannot tell a flat well from a lease that stopped filing.
    expect(r.reportedThrough).toBe("2024-12");
  });
});

// ------------------------------------------------------- nulls are not zero

describe("rrc_ratios", () => {
  /**
   * An oil lease carrying its gas as casinghead. February produces gas and no
   * liquid, so its GOR is undefined: not zero, and not a data point.
   */
  const ratios = () =>
    lease("O/08/81001", "GASSY", [
      month("2024-01", { oil_prod_vol: 1000, csgd_prod_vol: 500 }),
      month("2024-02", { oil_prod_vol: 0, csgd_prod_vol: 600 }),
      month("2024-03", { oil_prod_vol: 1000, csgd_prod_vol: 700 }),
      month("2024-04", { oil_prod_vol: 1000, csgd_prod_vol: 900 }),
    ]);

  test("an undefined ratio is null, and the trend is fitted without it", async () => {
    const r = await call("rrc_ratios", { ...ratios() });
    // 500 mcf against 1000 bbl is 500 scf/bbl.
    expect(r.monthly.map((m: Result) => m.gorScfPerBbl)).toEqual([500, null, 700, 900]);
    // All the gas is casinghead, so the share is 1 and there is no condensate.
    expect(r.monthly.every((m: Result) => m.casingheadShare === 1)).toBe(true);
    expect(r.monthly.every((m: Result) => m.condYieldBblPerMMcf === 0)).toBe(true);

    // Ordinary least squares on the three defined points (0, 500), (2, 700),
    // (3, 900): x̄ = 5/3, ȳ = 700, Sxy = 600, Sxx = 14/3, so the slope is
    // 600/(14/3) = 128.571 and r² = 600²/((14/3)·80000) = 0.96429.
    expect(r.trend.gor.n).toBe(3);
    expect(r.trend.gor.slopePerMonth).toBeCloseTo(600 / (14 / 3), 9);
    expect(r.trend.gor.r2).toBeCloseTo(600 ** 2 / ((14 / 3) * 80000), 9);
    // Folding the null in as a zero would drag the slope to 90.
    expect(r.trend.gor.slopePerMonth).not.toBeCloseTo(90, 1);
  });

  test("the unpublished tail never reaches a ratio", async () => {
    // Ratios read the point series directly rather than through a stream, so
    // this is the one place the tail rule has no second line of defence: an
    // unfiled month would enter as a real month of zero oil and zero gas.
    const tailed = lease("O/08/81005", "TAILED", [
      month("2024-11", { oil_prod_vol: 1000, csgd_prod_vol: 500 }),
      month("2024-12", { oil_prod_vol: 1000, csgd_prod_vol: 700 }),
      month("2025-01", { oil_prod_vol: 0, csgd_prod_vol: 0, reported: false }),
    ]);
    const r = await call("rrc_ratios", { ...tailed });
    expect(r.monthly.map((m: Result) => m.cycle)).toEqual(["2024-11", "2024-12"]);
    expect(r.trend.gor.n).toBe(2);
    // Two months, 500 then 700 scf/bbl: the trend is +200 a month. A third
    // month of unfiled zeros would drag it to -175.
    expect(r.trend.gor.slopePerMonth).toBeCloseTo(200, 9);
  });

  test("produced water is refused rather than inferred", async () => {
    const r = await call("rrc_ratios", { ...ratios() });
    expect(r.waterCut).toBeNull();
    expect(r.waterCutNote).toContain("W-10/G-10");
  });
});

describe("statistics decline to answer without the data", () => {
  test("a trailing average shorter than its window is null, not a partial average", async () => {
    const six = lease(
      "O/08/81002",
      "SIX",
      cycles("2024-07", 6).map((c) => atRate(c, 100))
    );
    const r = await call("rrc_series_stats", { ...six, stream: "oil" });
    expect(r.dailyRate.last6).toBe(100);
    // Six months of history cannot answer a twelve-month question with the
    // six-month number.
    expect(r.dailyRate.last12).toBeNull();
    expect(r.yoyPct).toBeNull();
    expect(r.cagrPct).toBeNull();
  });

  test("year on year and CAGR agree when the history is exactly two years", async () => {
    const two = lease(
      "O/08/81003",
      "TWO YEARS",
      cycles("2023-01", 24).map((c, k) => atRate(c, declineRate(k)))
    );
    const monthly = db.leases.get("O/08/81003")!.monthly;
    const first12 = monthly.slice(0, 12).reduce((a, m) => a + m.oil_prod_vol, 0);
    const last12 = monthly.slice(12).reduce((a, m) => a + m.oil_prod_vol, 0);

    const r = await call("rrc_series_stats", { ...two, stream: "oil" });
    expect(r.yoyPct).toBeCloseTo((last12 / first12 - 1) * 100, 9);
    // Over exactly one year of separation the compounded rate IS the year on
    // year change. Two derivations of one quantity that must not disagree.
    expect(r.cagrPct).toBeCloseTo(r.yoyPct, 9);
  });

  test("idle months between production are intermittency; the lead-in is not", async () => {
    // Two idle months before first production, then one shut month inside it.
    const rates = [0, 0, 100, 100, 0, 100, 100];
    const patchy = lease(
      "O/08/81004",
      "PATCHY",
      cycles("2024-01", 7).map((c, i) => atRate(c, rates[i]))
    );
    const r = await call("rrc_series_stats", { ...patchy, stream: "oil" });
    expect(r.producingMonths).toBe(4);
    // Span is 2024-03 to 2024-07, five months, one of them idle.
    expect(r.idleMonths).toBe(1);
    expect(r.intermittency).toBeCloseTo(1 / 5, 12);
  });
});

// ---------------------------------------------------------------- the rest

describe("rrc_changepoint", () => {
  test("a sustained halving is one step, not a run of them", async () => {
    const step = lease(
      "O/08/66601",
      "STEPPED",
      cycles("2023-01", 12).map((c, i) => atRate(c, i < 6 ? 100 : 50))
    );
    const r = await call("rrc_changepoint", { ...step, stream: "oil" });
    // The three months either side of 2023-07 average 100 and 50.
    expect(r.events).toEqual([
      { cycle: "2023-07", type: "step_down", before: 100, after: 50, changePct: -50 },
    ]);
  });

  test("a shut-in and its restart are dated to the month each happened", async () => {
    const rates = [100, 100, 100, 100, 0, 100, 100, 100, 100];
    const shut = lease(
      "O/08/66602",
      "SHUT IN",
      cycles("2023-01", 9).map((c, i) => atRate(c, rates[i]))
    );
    const r = await call("rrc_changepoint", { ...shut, stream: "oil" });
    const stops = r.events.filter((e: Result) => e.type === "shutin" || e.type === "restart");
    expect(stops).toEqual([
      { cycle: "2023-05", type: "shutin", before: 100, after: 0, changePct: -100 },
      { cycle: "2023-06", type: "restart", before: 0, after: 100, changePct: null },
    ]);
  });
});

describe("rrc_peer_rank", () => {
  test("rank counts the peers the subject beats", async () => {
    const subject = lease(
      "O/08/91000",
      "SUBJECT",
      cycles("2024-01", 3).map((c) => atRate(c, 100))
    );
    const peers = [50, 150, 200].map((rate, i) => {
      const key = `O/08/9100${i + 1}`;
      lease(key, `PEER ${rate}`, cycles("2024-01", 3).map((c) => atRate(c, rate)));
      return key;
    });

    const r = await call("rrc_peer_rank", {
      ...subject,
      peers: [...peers, "not-a-key"],
      stream: "oil",
      metric: "peak_rate",
    });
    expect(r.value).toBe(100);
    expect(r.peerCount).toBe(3);
    // One of three peers is below 100.
    expect(r.betterThan).toBe(1);
    expect(r.percentileRank).toBeCloseTo(100 / 3, 12);
    expect(r.peerMedian).toBe(150);
    expect(r.peers.map((p: Result) => p.value)).toEqual([200, 150, 50]);
    expect(r.unresolved).toEqual([
      { key: "not-a-key", error: 'Not a lease key: "not-a-key". Use "O/08/12345".' },
    ]);
  });
});

describe("rrc_cohort_series", () => {
  test("each lease keeps its own rates and a bad key is reported, not dropped", async () => {
    const a = "O/08/95001";
    const b = "O/08/95002";
    lease(a, "ONE", cycles("2024-11", 2).map((c) => atRate(c, 10)));
    lease(b, "TWO", cycles("2024-11", 2).map((c) => atRate(c, 20)));

    const r = await call("rrc_cohort_series", { leases: [a, b, "junk"], stream: "oil" });
    expect(r.leases).toEqual([
      {
        key: a,
        label: "ONE",
        reportedThrough: "2024-12",
        points: [
          { cycle: "2024-11", dailyRate: 10 },
          { cycle: "2024-12", dailyRate: 10 },
        ],
      },
      {
        key: b,
        label: "TWO",
        reportedThrough: "2024-12",
        points: [
          { cycle: "2024-11", dailyRate: 20 },
          { cycle: "2024-12", dailyRate: 20 },
        ],
      },
    ]);
    expect(r.unresolved).toHaveLength(1);
    expect(r.truncated).toBe(false);
  });
});

describe("rrc_flow_regime", () => {
  test("an exponential decline is boundary-dominated, and the slope is -Di per day", async () => {
    const dec = lease(
      "O/08/96001",
      "DEPLETING",
      cycles("2023-01", 24).map((c, k) => atRate(c, declineRate(k)))
    );
    const r = await call("rrc_flow_regime", { ...dec, stream: "oil" });
    expect(r.regime).toBe("boundary_dominated");
    expect(r.producingMonths).toBe(24);
    expect(r.bdfStart).toBe("2023-01");
    // Under exponential decline q = qi - D·Np with D the DAILY nominal decline,
    // so the fitted slope is -0.5/365.25 = -0.001369 bbl/d per barrel.
    expect(r.rateVsCumSlope).toBeLessThan(0);
    expect(Math.abs(r.rateVsCumSlope / (-DI / 365.25) - 1)).toBeLessThan(0.05);
    expect(r.rateVsCumR2).toBeGreaterThan(0.99);
  });

  test("a steady well is flat, not declining", async () => {
    const flat = lease(
      "O/08/96002",
      "STEADY",
      cycles("2024-01", 12).map((c) => atRate(c, 100))
    );
    const r = await call("rrc_flow_regime", { ...flat, stream: "oil" });
    expect(r.regime).toBe("flat_or_rising");
    expect(r.logLogSlope).toBeCloseTo(0, 12);
    expect(r.bdfStart).toBeNull();
  });

  test("fewer than six producing months is refused rather than classified", async () => {
    const tiny = lease(
      "O/08/96003",
      "TINY",
      cycles("2024-09", 4).map((c) => atRate(c, 100))
    );
    const r = await call("rrc_flow_regime", { ...tiny, stream: "oil" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("a regime read needs 6");
  });
});

describe("the catalog", () => {
  test("every tool has a unique name and refuses an entity it cannot key", async () => {
    const names = TOOLS.map((t) => t.name);
    expect(new Set(names).size).toBe(names.length);
    const r = await call("rrc_series", { entity: "lease", stream: "oil" });
    expect(r).toEqual({
      ok: false,
      error: "entity 'lease' needs oil_gas_code, district_no and lease_no.",
    });
  });

  test("a long history is cut from the front and says so", async () => {
    const long = lease(
      "O/08/97001",
      "LONG",
      cycles("2023-01", 24).map((c, k) => atRate(c, declineRate(k)))
    );
    const r = await call("rrc_series", { ...long, stream: "oil", months: 5 });
    expect(r.points).toHaveLength(5);
    expect(r.points[0].cycle).toBe("2024-08");
    expect(r.points[4].cycle).toBe("2024-12");
    expect(r.truncated).toBe(true);
    // The count of what exists is not the count of what was returned.
    expect(r.reportedMonths).toBe(24);
  });
});
