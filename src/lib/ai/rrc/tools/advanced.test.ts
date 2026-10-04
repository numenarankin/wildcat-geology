import { readFileSync } from "node:fs";
import path from "node:path";

import { beforeEach, describe, expect, test, vi } from "vitest";

import type { LeaseMonth } from "../../../scout/rrc-types";

/**
 * The advanced catalog, against fixtures whose right answer was worked out
 * before the code ran.
 *
 * Every expected number below is derived from the stated method by hand: a
 * Kaplan-Meier curve multiplied out step by step, an HHI summed from shares, a
 * kriging estimate that must land exactly on its own control point. None of it
 * is a previous run's output, because a test that asserts what the code emits
 * proves only that the code is repeatable.
 *
 * The property with the most riding on it is the first one: an estimate must
 * never be able to pass as a filing, so the roll-ups below check that the two
 * come back apart and that nothing anywhere reports their sum.
 */

const db = vi.hoisted(() => ({
  edge: { reported: "2024-12", loaded: "2025-03" },
  leases: new Map<string, { name: string; monthly: LeaseMonth[]; wells?: unknown[]; operator_no?: string | null }>(),
  filingRows: [] as unknown[],
  survivalRows: [] as unknown[],
  wellKeyRows: [] as unknown[],
  testRows: [] as unknown[],
  operatorWellRows: [] as unknown[],
  fleetRows: [] as unknown[],
  operatorRows: [] as unknown[],
  countyLeaseRows: [] as unknown[],
  perfRows: [] as unknown[],
  completionRows: [] as unknown[],
  location: null as { lat: number; lon: number } | null,
  offsets: { wells: [] as unknown[], truncated: false },
  trend: new Map<string, unknown[]>(),
  county: null as unknown,
  queries: [] as string[],
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string) => {
    db.queries.push(sql);
    if (sql.includes("rrc.lease_production")) return db.filingRows;
    if (sql.includes("rrc.county_lease_cycle")) return db.countyLeaseRows;
    if (sql.includes("rrc.w10_test")) return db.testRows;
    if (sql.includes("rrc.well_location")) return db.location ? [db.location] : [];
    if (sql.includes("rrc.wb_perf")) return db.perfRows;
    if (sql.includes("rrc.completion")) return db.completionRows;
    if (sql.includes("rrc.operators")) return db.operatorRows;
    // Two wellbore group-bys: the county operator table names its alias `w`.
    if (sql.includes("count(distinct w.api_number)")) return db.operatorWellRows;
    if (sql.includes("count(distinct api_number)")) return db.fleetRows;
    if (sql.includes("api_depth")) return db.survivalRows;
    if (sql.includes("rrc.wellbore")) return db.wellKeyRows;
    throw new Error(`unexpected query: ${sql.slice(0, 70)}`);
  },
  rrcQueryOne: async () => null,
  rrcQuerySlow: async () => [],
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getCycleEdge: async () => db.edge,
  getInjectionEdge: async () => ({ reported: "2024-01", loaded: "2025-03" }),
  getLeaseDossier: async (ogc: string, dist: string, lease: string) => {
    const row = db.leases.get(`${ogc}/${dist}/${lease}`);
    if (!row) return null;
    return {
      oil_gas_code: ogc,
      district_no: dist,
      lease_no: lease,
      lease_name: row.name,
      field_no: "0001",
      operator_no: row.operator_no ?? null,
      monthly: row.monthly,
      wells: row.wells ?? [],
      counties: [],
      p4: { connections: [], filings: [] },
    };
  },
  getWellDossier: async () => null,
  getOperatorDossier: async () => null,
  getOperatorNetwork: async () => null,
  getFieldProfile: async () => null,
  getCountyProfile: async () => db.county,
  getProductionTrend: async (scope: string) => db.trend.get(scope) ?? [],
  findDisposal: async () => [],
  listPermits: async () => [],
  resolveCounty: (ref: string) => (ref ? { county_no: "003", county_name: "ANDREWS" } : null),
}));

vi.mock("../offsets", () => ({
  offsetWellbores: async () => db.offsets,
}));

const { TOOLS, kaplanMeier } = await import("./advanced");

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Result = any;

const call = async (name: string, args: Record<string, unknown>): Promise<Result> => {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`No tool ${name}. Have: ${TOOLS.map((t) => t.name).join(", ")}`);
  return (await tool.run(tool.args.parse(args) as never)) as Result;
};

// ------------------------------------------------------------------ fixtures

/** Days per calendar month, written out so the divisor is independent of the code's. */
const DAYS: Record<string, number> = {
  "01": 31, "02": 28, "03": 31, "04": 30, "05": 31, "06": 30,
  "07": 31, "08": 31, "09": 30, "10": 31, "11": 30, "12": 31,
};
const days = (cycle: string) => (cycle === "2024-02" ? 29 : DAYS[cycle.slice(5)]);

function cycles(start: string, n: number): string[] {
  const [y, m] = start.split("-").map(Number);
  return Array.from({ length: n }, (_v, i) => {
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

const atRate = (cycle: string, rate: number, over: Partial<LeaseMonth> = {}) =>
  month(cycle, { oil_prod_vol: rate * days(cycle), ...over });

function lease(key: string, name: string, monthly: LeaseMonth[], extra: { wells?: unknown[]; operator_no?: string | null } = {}) {
  db.leases.set(key, { name, monthly, ...extra });
  const [oil_gas_code, district_no, lease_no] = key.split("/");
  return { oil_gas_code, district_no, lease_no };
}

function offsetWell(api: string, lat: number, lon: number, depth: number | null) {
  return {
    api_number: api,
    operator_name: "TEST OPERATOR",
    lease_name: "TEST LEASE",
    distanceMi: 0,
    lat,
    lon,
    bottomLat: null,
    bottomLon: null,
    kbElevationFt: null,
    elevationCode: null,
    totalDepthFt: depth,
    plugBackFt: null,
    perforations: [],
    casing: [],
    formationTops: [],
  };
}

beforeEach(() => {
  db.edge = { reported: "2024-12", loaded: "2025-03" };
  db.leases.clear();
  db.filingRows = [];
  db.survivalRows = [];
  db.wellKeyRows = [];
  db.testRows = [];
  db.operatorWellRows = [];
  db.fleetRows = [];
  db.operatorRows = [];
  db.countyLeaseRows = [];
  db.perfRows = [];
  db.completionRows = [];
  db.location = null;
  db.offsets = { wells: [], truncated: false };
  db.trend = new Map();
  db.county = null;
  db.queries = [];
});

// ------------------------------------------- an estimate is never a filing

describe("estimated volumes never enter a filed total", () => {
  /**
   * 27 cycles for one operator against a mirror loaded through 2025-03.
   *
   * Everything at least 12 months old files all ten of its leases, so the
   * settled baseline is 10. Three recent cycles are short: 5 of 10 filed with
   * 500 bbl, 2 of 10 with 200 bbl, and 0 of 10 with nothing.
   */
  const filingFixture = () => {
    db.filingRows = cycles("2023-01", 27).map((cycle) => {
      if (cycle === "2025-01") return { cycle, leases: 10, filed: 5, oil: 500, gas: 0 };
      if (cycle === "2025-02") return { cycle, leases: 10, filed: 2, oil: 200, gas: 0 };
      if (cycle === "2025-03") return { cycle, leases: 10, filed: 0, oil: 0, gas: 0 };
      return { cycle, leases: 10, filed: 10, oil: 1000, gas: 0 };
    });
  };

  test("rrc_nowcast divides the filed volume by measured completeness", async () => {
    filingFixture();
    const r = await call("rrc_nowcast", { operator_no: "123456" });
    expect(r.ok).toBe(true);
    expect(r.settled_lease_count).toBe(10);

    // Completeness is filed over the settled baseline: 5/10 and 2/10.
    const jan = r.tail.find((t: Result) => t.cycle === "2025-01");
    expect(jan.completeness).toBeCloseTo(0.5, 10);
    expect(jan.filed_volume).toBe(500);
    expect(jan.estimated_volume).toBeCloseTo(1000, 10); // 500 / 0.5
    expect(jan.estimated_uplift).toBeCloseTo(500, 10);
    expect(jan.filed_basis).toBe("filed");
    expect(jan.estimated_basis).toBe("estimated");

    const feb = r.tail.find((t: Result) => t.cycle === "2025-02");
    expect(feb.estimated_volume).toBeCloseTo(1000, 10); // 200 / 0.2
    expect(feb.estimated_uplift).toBeCloseTo(800, 10);

    // A cycle nobody has filed cannot be nowcast: 0/10 is not a ratio.
    const mar = r.tail.find((t: Result) => t.cycle === "2025-03");
    expect(mar.too_early).toBe(true);
    expect(mar.estimated_volume).toBeNull();

    // Only the three short cycles are the tail; a complete month is not.
    expect(r.tail.map((t: Result) => t.cycle)).toEqual(["2025-01", "2025-02", "2025-03"]);
  });

  test("the nowcast roll-up reports filed and estimated apart, with no sum anywhere", async () => {
    filingFixture();
    const r = await call("rrc_nowcast", { operator_no: "123456" });

    // By hand: filed across the tail is 500 + 200 + 0 = 700.
    // Estimated uplift is (1000-500) + (1000-200) = 1300.
    expect(r.tail_total.filed).toBe(700);
    expect(r.tail_total.estimated).toBeCloseTo(1300, 10);
    expect(r.tail_total.combined).toBeNull();
    expect(r.tail_total.filed_basis).toBe("filed");
    expect(r.tail_total.estimated_basis).toBe("estimated");

    // 2000 is the number this file must never produce.
    expect(JSON.stringify(r)).not.toContain("2000");
  });

  test("rrc_impute_gaps interpolates the unfiled month and keeps it out of the filed total", async () => {
    // 2024 at a flat 100 bbl/d, except June, which nobody filed.
    const key = lease(
      "O/08/12345",
      "GAP LEASE",
      cycles("2024-01", 12).map((c) =>
        c === "2024-06"
          ? month(c, { oil_prod_vol: 0, prod_report_filed: "N" })
          : atRate(c, 100)
      )
    );
    const r = await call("rrc_impute_gaps", key);
    expect(r.ok).toBe(true);
    expect(r.gap_months).toBe(1);
    expect(r.filed_months).toBe(11);
    expect(r.missing_share).toBeCloseTo(1 / 12, 10);

    // Bracketed by May and July, both at 100 bbl/d, so June is 100 bbl/d
    // across its 30 days: 3,000 bbl.
    const june = r.gaps[0];
    expect(june.cycle).toBe("2024-06");
    expect(june.method).toBe("bracket");
    expect(june.estimated_daily_rate).toBeCloseTo(100, 10);
    expect(june.estimated_volume).toBeCloseTo(3000, 10);
    expect(june.basis).toBe("estimated");

    // 2024 is a leap year: 366 days less June's 30 is 336 filed days at
    // 100 bbl/d, so the filed total is 33,600 and the imputed 3,000 stays out.
    expect(r.window_total.filed).toBeCloseTo(33600, 10);
    expect(r.window_total.estimated).toBeCloseTo(3000, 10);
    expect(r.window_total.combined).toBeNull();
    expect(JSON.stringify(r)).not.toContain("36600");
  });
});

// ------------------------------------------------------------ reconciliation

describe("reconciliation", () => {
  test("rrc_mass_balance finds the month that does not close", async () => {
    const key = lease("O/08/22222", "BALANCE LEASE", [
      month("2024-01", { oil_prod_vol: 500, oil_tot_disp: 400, oil_ending_bal: 100 }),
      // 100 + 500 - 450 - 150 = 0
      month("2024-02", { oil_prod_vol: 500, oil_tot_disp: 450, oil_ending_bal: 150 }),
      // 150 + 600 - 500 - 200 = 50, against a tolerance of 600 * 2% = 12
      month("2024-03", { oil_prod_vol: 600, oil_tot_disp: 500, oil_ending_bal: 200 }),
    ]);
    const r = await call("rrc_mass_balance", { entity: "lease", ...key });
    expect(r.ok).toBe(true);
    expect(r.months_checked).toBe(2); // The first month has no prior balance.
    expect(r.months_out_of_balance).toBe(1);
    expect(r.worst[0].cycle).toBe("2024-03");
    expect(r.worst[0].residual).toBeCloseTo(50, 10);
    expect(r.worst[0].tolerance).toBeCloseTo(12, 10);
    expect(r.total_absolute_residual).toBeCloseTo(50, 10);
  });

  test("rrc_mass_balance skips a month with no filed disposition rather than reading null as zero", async () => {
    const key = lease("O/08/22223", "PARTIAL LEASE", [
      month("2024-01", { oil_prod_vol: 500, oil_tot_disp: 400, oil_ending_bal: 100 }),
      // No disposition filed: reading that null as zero would invent a 500 bbl
      // residual out of a missing column.
      month("2024-02", { oil_prod_vol: 500, oil_tot_disp: null, oil_ending_bal: 150 }),
      // 150 + 600 - 550 - 200 = 0
      month("2024-03", { oil_prod_vol: 600, oil_tot_disp: 550, oil_ending_bal: 200 }),
      // 200 + 400 - 400 - 200 = 0
      month("2024-04", { oil_prod_vol: 400, oil_tot_disp: 400, oil_ending_bal: 200 }),
    ]);
    const r = await call("rrc_mass_balance", { entity: "lease", ...key });
    expect(r.ok).toBe(true);
    expect(r.months_checked).toBe(2);
    expect(r.months_skipped).toBe(1);
    expect(r.months_out_of_balance).toBe(0);
  });

  test("rrc_rollup_reconcile puts statewide against the districts summed", async () => {
    const point = (cycle: string, oil: number) => ({ cycle, oil, gas: 0, cond: 0, csgd: 0, reported: true });
    db.trend.set("statewide", [
      { key: "TX", label: "Texas", points: [point("2024-11", 1000), point("2024-12", 1000)] },
    ]);
    db.trend.set("districts", [
      { key: "08", label: "08", points: [point("2024-11", 600), point("2024-12", 600)] },
      { key: "7C", label: "7C", points: [point("2024-11", 300), point("2024-12", 300)] },
    ]);
    const r = await call("rrc_rollup_reconcile", { scope: "statewide" });
    expect(r.ok).toBe(true);
    expect(r.by_cycle).toHaveLength(2);
    // 1000 published statewide against 600 + 300 at district grain.
    expect(r.by_cycle[0].oil_difference).toBe(100);
    expect(r.total_oil_difference).toBe(200);
  });
});

// -------------------------------------------------------- survival analysis

describe("Kaplan-Meier", () => {
  /**
   * Six wells, one censored, worked out by hand:
   *
   *   t=1  at risk 6, 1 event -> S = 5/6           = 0.833333
   *   t=2  at risk 5, 1 event -> S = 5/6 * 4/5     = 0.666667
   *   (the well censored at t=3 leaves the risk set without an event)
   *   t=4  at risk 3, 1 event -> S = 2/3 * 2/3     = 0.444444
   *   t=5  at risk 2, 1 event -> S = 0.444444 * 1/2 = 0.222222
   *   t=6  at risk 1, 1 event -> S = 0
   */
  const six = [
    { t: 1, event: true },
    { t: 2, event: true },
    { t: 3, event: false },
    { t: 4, event: true },
    { t: 5, event: true },
    { t: 6, event: true },
  ];

  test("the curve steps down only at events, and censoring leaves the risk set", () => {
    const curve = kaplanMeier(six);
    expect(curve.map((c) => c.t)).toEqual([1, 2, 4, 5, 6]);
    expect(curve[0].survival).toBeCloseTo(5 / 6, 10);
    expect(curve[1].survival).toBeCloseTo(4 / 6, 10);
    expect(curve[2].at_risk).toBe(3); // The censored well is gone by t=4.
    expect(curve[2].survival).toBeCloseTo(4 / 9, 10);
    expect(curve[3].survival).toBeCloseTo(2 / 9, 10);
    expect(curve[4].survival).toBeCloseTo(0, 10);
  });

  test("rrc_well_survival matches the hand curve on a 20-well county", async () => {
    // All completed 2020-01. Two plugged after 12 months, three after 24, and
    // fifteen are still open at the mirror's edge.
    db.survivalRows = [
      ...Array.from({ length: 2 }, (_v, i) => ({
        api: `A${i}`, field_name: "F", well_type_name: "PRODUCING",
        completion_date: "20200115", orig_completion_dt: "20200115",
        plug_date: "20210115", wb_shut_in_date: null, api_depth: "5000",
      })),
      ...Array.from({ length: 3 }, (_v, i) => ({
        api: `B${i}`, field_name: "F", well_type_name: "PRODUCING",
        completion_date: "20200115", orig_completion_dt: "20200115",
        plug_date: "20220115", wb_shut_in_date: null, api_depth: "5000",
      })),
      ...Array.from({ length: 15 }, (_v, i) => ({
        api: `C${i}`, field_name: "F", well_type_name: "PRODUCING",
        completion_date: "20200115", orig_completion_dt: "20200115",
        plug_date: null, wb_shut_in_date: null, api_depth: "5000",
      })),
    ];
    const r = await call("rrc_well_survival", { county: "ANDREWS" });
    expect(r.ok).toBe(true);
    expect(r.n).toBe(20);
    expect(r.events).toBe(5);
    expect(r.censored).toBe(15);
    // t=1: 18/20 = 0.9. t=2: 0.9 * 15/18 = 0.75.
    expect(r.curve[0].survival).toBeCloseTo(0.9, 10);
    expect(r.curve[1].survival).toBeCloseTo(0.75, 10);
    expect(r.survival.find((s: Result) => s.years === 1).surviving).toBeCloseTo(0.9, 10);
    expect(r.survival.find((s: Result) => s.years === 5).surviving).toBeCloseTo(0.75, 10);
    // The curve never reaches a half, so there is no median to report.
    expect(r.median_life_years).toBeNull();
  });

  test("rrc_well_survival refuses a population too small to fit", async () => {
    db.survivalRows = Array.from({ length: 19 }, (_v, i) => ({
      api: `A${i}`, field_name: "F", well_type_name: "PRODUCING",
      completion_date: "20200115", orig_completion_dt: "20200115",
      plug_date: null, wb_shut_in_date: null, api_depth: "5000",
    }));
    const r = await call("rrc_well_survival", { county: "ANDREWS" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("19");
    expect(r.error).toContain("20");
  });
});

// -------------------------------------------------------- market structure

describe("concentration", () => {
  test("rrc_concentration returns the HHI computed by hand", async () => {
    // Shares of 50%, 30% and 20% of 100 wells: 2500 + 900 + 400 = 3800.
    db.operatorWellRows = [
      { operator_number: "111111", operator_name: "BIG", wells: 50 },
      { operator_number: "222222", operator_name: "MID", wells: 30 },
      { operator_number: "333333", operator_name: "SMALL", wells: 20 },
    ];
    const r = await call("rrc_concentration", { scope: "county", county: "ANDREWS" });
    expect(r.ok).toBe(true);
    expect(r.wells).toBe(100);
    expect(r.hhi).toBeCloseTo(3800, 6);
    expect(r.top[0].share).toBeCloseTo(0.5, 10);
    expect(r.basis).toBe("well count");
  });
});

// ------------------------------------------------------------ geostatistics

describe("kriging", () => {
  /** A 4x4 grid of wells whose depth rises 100 ft north and 50 ft east. */
  const grid = () => {
    const wells = [];
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) {
        wells.push(offsetWell(`G${i}${j}`, 32 + i * 0.01, -102 + j * 0.01, 8000 + i * 100 + j * 50));
      }
    }
    db.offsets = { wells, truncated: false };
  };

  test("rrc_krige reproduces a control point exactly", async () => {
    grid();
    // The well at i=1, j=2 sits at 8000 + 100 + 100 = 8200 ft.
    const r = await call("rrc_krige", {
      lat: 32.015,
      lon: -101.985,
      attribute: "total_depth_ft",
      radius_mi: 5,
      nugget: 0,
      targets: [{ lat: 32.01, lon: -101.98 }],
    });
    expect(r.ok).toBe(true);
    expect(r.control_points).toBe(16);
    expect(r.estimates[0].method).toBe("ordinary_kriging");
    expect(r.estimates[0].estimate).toBeCloseTo(8200, 6);
    // Standing on a control point, the kriging error is nil.
    expect(r.estimates[0].stdev).toBeCloseTo(0, 6);
    expect(r.estimates[0].basis).toBe("estimated");
  });

  test("rrc_variogram refuses a population too small to structure", async () => {
    db.offsets = {
      wells: Array.from({ length: 5 }, (_v, i) => offsetWell(`S${i}`, 32 + i * 0.01, -102, 8000 + i * 10)),
      truncated: false,
    };
    const r = await call("rrc_variogram", { lat: 32, lon: -102, attribute: "total_depth_ft" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("5");
    expect(r.error).toContain("12");
  });

  test("rrc_matched_pairs refuses when the matched cohort is too small", async () => {
    db.location = { lat: 32, lon: -102 };
    db.offsets = {
      wells: [
        offsetWell("42000000000000", 32, -102, 8000),
        offsetWell("42000000000001", 32.001, -102, 8000),
        offsetWell("42000000000002", 32.002, -102, 8000),
      ],
      truncated: false,
    };
    db.wellKeyRows = ["42000000000000", "42000000000001", "42000000000002"].map((api) => ({
      api, district: "08", oil_gas_code: "O", lease_number: "12345", well_no: "1",
      field_name: "SPRABERRY", well_type_name: "PRODUCING",
      completion_date: "20200101", orig_completion_dt: "20200101", plug_date: null, wb_shut_in_date: null,
    }));
    db.testRows = [
      { api: "42000000000000", test_date: "2024-06-01", daily_oil: 50, daily_water: 10, daily_gas: 100, gas_oil_ratio: 2000 },
      { api: "42000000000001", test_date: "2024-06-01", daily_oil: 40, daily_water: 10, daily_gas: 100, gas_oil_ratio: 2500 },
      { api: "42000000000002", test_date: "2024-06-01", daily_oil: 60, daily_water: 10, daily_gas: 100, gas_oil_ratio: 1600 },
    ];
    const r = await call("rrc_matched_pairs", { api: "42000000000000" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("2 matched offset");
  });
});

// ------------------------------------------------------------------ rigour

describe("uncertainty", () => {
  /** Twelve months rising 10 bbl/d a month: 10, 20 ... 120. Mean is 65. */
  const ramp = () =>
    lease(
      "O/08/33333",
      "RAMP LEASE",
      cycles("2024-01", 12).map((c, i) => atRate(c, 10 * (i + 1)))
    );

  test("rrc_uncertainty_ci reports the observed estimate and its seed", async () => {
    const key = ramp();
    const r = await call("rrc_uncertainty_ci", {
      entity: "lease",
      ...key,
      quantity: "mean_daily_rate",
      seed: 7,
    });
    expect(r.ok).toBe(true);
    expect(r.n_months).toBe(12);
    // (10 + 20 + ... + 120) / 12 = 780 / 12 = 65 bbl/d.
    expect(r.estimate).toBeCloseTo(65, 10);
    expect(r.seed).toBe(7);
    expect(r.converged_draws).toBeGreaterThan(0);
    expect(r.p05).toBeLessThanOrEqual(r.p95 as number);
  });

  test("one seed reproduces exactly, another does not", async () => {
    const key = ramp();
    const args = { entity: "lease", ...key, quantity: "mean_daily_rate" as const };
    const a = await call("rrc_uncertainty_ci", { ...args, seed: 7 });
    const b = await call("rrc_uncertainty_ci", { ...args, seed: 7 });
    const c = await call("rrc_uncertainty_ci", { ...args, seed: 8 });
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
    expect(JSON.stringify(c)).not.toBe(JSON.stringify(a));
    // The point estimate is the observed series and does not move with the seed.
    expect(c.estimate).toBeCloseTo(65, 10);
  });

  test("rrc_uncertainty_ci refuses a series too short for an interval", async () => {
    const key = lease("O/08/33334", "SHORT LEASE", cycles("2024-01", 8).map((c) => atRate(c, 100)));
    const r = await call("rrc_uncertainty_ci", {
      entity: "lease",
      ...key,
      quantity: "mean_daily_rate",
      seed: 7,
    });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("8");
  });

  test("Math.random appears nowhere in the file", () => {
    const source = readFileSync(path.join(__dirname, "advanced.ts"), "utf8");
    expect(source).not.toMatch(/Math\.random/);
    // Everything that samples goes through the shared seeded generator.
    expect(source).toMatch(/seeded\(/);
  });
});
