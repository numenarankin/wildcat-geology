import { beforeEach, describe, expect, test, vi } from "vitest";

import type {
  G10Test,
  H15Test,
  LeaseMonth,
  LeaseW10,
  OperatorH15,
  W10Test,
  WellDossier,
} from "../../../scout/rrc-types";

/**
 * The wellbore tools, against hand-computed answers.
 *
 * The mirror is mocked, so what these check is arithmetic and refusal, not SQL.
 * Every expected number below was computed from the definition first and the
 * code second: an allocation share is a division done on paper, the AOF fixture
 * is three points laid on an exactly straight log-log line so C and n are known
 * before the fit runs, and the fluid-level fit is an ordinary least squares
 * worked out by hand over three uneven years.
 *
 * Four of them exist because the wrong answer is the plausible one:
 *   - oil and gas must take DIFFERENT shares of the same month
 *   - a month weighted by a real test must not look like one that fell back
 *   - one flow point cannot be fitted, and saying so is the answer
 *   - an absent open-flow potential is NOT zero
 */

const db = vi.hoisted(() => ({
  dossier: null as WellDossier | null,
  g10: [] as G10Test[],
  h15: [] as H15Test[],
  leaseW10: null as LeaseW10 | null,
  operatorH15: null as OperatorH15 | null,
  calls: [] as { sql: string; params: unknown[] }[],
  rankWells: [] as Record<string, unknown>[],
  rankTests: [] as Record<string, unknown>[],
  rankMonths: [] as Record<string, unknown>[],
  rankLeases: [] as Record<string, unknown>[],
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getWellDossier: async () => db.dossier,
  getWellG10: async () => db.g10,
  getWellH15: async () => db.h15,
  getLeaseW10: async () => db.leaseW10,
  getOperatorH15: async () => db.operatorH15,
}));

/**
 * The mirror, for the two ranking tools only.
 *
 * Routed on a fragment that appears in exactly one query and throwing on
 * anything unmatched, so a fixture cannot silently answer the wrong read. The
 * other tools in this file go through `rrc-queries` above and never reach here.
 */
vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string, params: unknown[] = []) => {
    db.calls.push({ sql, params });
    if (sql.includes("from rrc.wellbore w")) return db.rankWells;
    if (sql.includes("from rrc.w10_test t")) return db.rankTests;
    if (sql.includes("from rrc.lease_production p")) return db.rankMonths;
    if (sql.includes("count(distinct well_no)::int as ours")) return db.rankLeases;
    throw new Error(`unrouted query: ${sql.replace(/\s+/g, " ").slice(0, 100)}`);
  },
}));

const { TOOLS } = await import("./wells");

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function call(name: string, args: Record<string, unknown>): Promise<any> {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`no tool named ${name}`);
  // Through the tool's own schema, so the test exercises the defaults and
  // coercions the dispatcher applies rather than a hand-built argument object.
  return tool.run(tool.args.parse(args) as never);
}

// ------------------------------------------------------------------ fixtures

/** A lease-month carrying only the four volume columns these tools read. */
function month(
  cycle: string,
  v: { oil?: number; gas?: number; cond?: number; csgd?: number },
  reported = true
): LeaseMonth {
  return {
    cycle,
    oil_prod_vol: v.oil ?? 0,
    oil_allow: null,
    oil_ending_bal: null,
    gas_prod_vol: v.gas ?? 0,
    gas_allow: null,
    gas_lift_inj_vol: null,
    cond_prod_vol: v.cond ?? 0,
    cond_limit: null,
    cond_ending_bal: null,
    csgd_prod_vol: v.csgd ?? 0,
    csgd_limit: null,
    csgd_gas_lift: null,
    oil_tot_disp: null,
    gas_tot_disp: null,
    cond_tot_disp: null,
    csgd_tot_disp: null,
    prod_report_filed: "Y",
    reported,
  };
}

function w10(test_date: string, daily_oil: number | null, daily_gas: number | null): W10Test {
  return {
    test_date,
    daily_oil,
    daily_water: null,
    daily_gas,
    gas_oil_ratio: null,
    producing_method: "P",
    type_flag: "R",
    cycle: `${test_date.slice(0, 7)}-01`,
  };
}

function g10(t: Partial<G10Test> & { test_date: string }): G10Test {
  return {
    daily_gas: null,
    daily_cond: null,
    daily_water: null,
    potential: null,
    siwh_press: null,
    flow_press: null,
    bhp: null,
    gas_gravity: null,
    gas_liquid_ratio: null,
    shut_in_flag: null,
    shut_in_date: null,
    late_test: null,
    corrected: null,
    operator_no: "123456",
    ...t,
  };
}

function h15(t: Partial<H15Test>): H15Test {
  return {
    test_date: null,
    status: "A",
    status_date: null,
    operator_no: "123456",
    test_type: "F",
    fluid_method: "S",
    mech_method: null,
    top_of_fluid: null,
    next_test_due: null,
    ...t,
  };
}

function dossier(
  over: Partial<Omit<WellDossier, "header">> & { header?: Partial<WellDossier["header"]> }
): WellDossier {
  return {
    api_number: "42123456",
    current: true,
    ...over,
    header: {
      api_number: "42123456",
      district: "08",
      county_code: null,
      county_name: null,
      oil_gas_code: "O",
      lease_name: "SMITH",
      lease_number: "12345",
      field_number: null,
      field_name: null,
      well_no: "3",
      well_no_display: "3",
      oil_unit_number: null,
      operator_name: "ACME OIL",
      operator_number: "123456",
      on_schedule: "Y",
      ...over.header,
    },
    status: null,
    compliance: null,
    filings: null,
    location: {
      lat: null,
      lon: null,
      bottom_lat: null,
      bottom_lon: null,
      symbol_num: null,
      reliability: null,
      api10: null,
      stcode: null,
      abstract_label: null,
      survey_name: null,
      block_number: null,
    },
    completions: [],
    production: over.production ?? [],
    allocationShare: over.allocationShare ?? null,
    productionByTest: over.productionByTest ?? [],
    injection: null,
    construction: null,
    h15: [],
    w10: over.w10 ?? [],
    g10: over.g10 ?? [],
    plugging: [],
    completionReports: [],
    w10Share: over.w10Share ?? null,
  };
}

beforeEach(() => {
  db.dossier = null;
  db.g10 = [];
  db.h15 = [];
  db.leaseW10 = null;
  db.operatorH15 = null;
});

// ------------------------------------------------------------------- 13

describe("rrc_allocate_well", () => {
  /**
   * The lease filed 1,000 bbl and 500 mcf in January and 800 / 400 in February.
   * This hole was allocated 400 / 150 then 200 / 160.
   *
   * By hand: oil 400/1000 = 0.4 and gas 150/500 = 0.3 in January; oil 200/800 =
   * 0.25 and gas 160/400 = 0.4 in February. The two streams disagree in both
   * months and reverse between them, which is the whole point of weighting them
   * apart, and a collapsed single share could not produce either pair.
   */
  beforeEach(() => {
    db.dossier = dossier({
      production: [
        month("2024-01", { oil: 1000, csgd: 500 }),
        month("2024-02", { oil: 800, csgd: 400 }),
      ],
      productionByTest: [
        month("2024-01", { oil: 400, csgd: 150 }),
        month("2024-02", { oil: 200, csgd: 160 }),
      ],
      allocationShare: 0.25,
      w10: [w10("2024-02-10", 40, 100)],
    });
  });

  test("oil and gas take separate shares, month by month", async () => {
    const r = await call("rrc_allocate_well", { api: "42123456" });

    expect(r.ok).toBe(true);
    expect(r.grain).toBe("well");
    expect(r.allocation.method).toBe("well-test");

    expect(r.months[0].oil_share).toBeCloseTo(0.4, 10);
    expect(r.months[0].gas_share).toBeCloseTo(0.3, 10);
    expect(r.months[1].oil_share).toBeCloseTo(0.25, 10);
    expect(r.months[1].gas_share).toBeCloseTo(0.4, 10);
    expect(r.months[0].oil_share).not.toBeCloseTo(r.months[0].gas_share, 6);

    // The volumes the shares came from, not the lease's.
    expect(r.months[0].oil_bbl).toBe(400);
    expect(r.months[0].lease_oil_bbl).toBe(1000);
    expect(r.months[1].gas_mcf).toBe(160);
  });

  test("the quoted share is the newest reported month's, and it reconciles", async () => {
    const r = await call("rrc_allocate_well", { api: "42123456" });

    expect(r.allocation.asOfCycle).toBe("2024-02");
    expect(r.allocation.oilShare).toBeCloseTo(0.25, 10);
    expect(r.allocation.gasShare).toBeCloseTo(0.4, 10);
    // The even split is offered, never substituted: 1/4 is not 1/5 of the oil.
    expect(r.allocation.evenSplitShare).toBe(0.25);
    expect(r.lifetime.oil_bbl).toBe(600);
    expect(r.lifetime.gas_mcf).toBe(310);
    expect(r.lifetime.lease_oil_bbl).toBe(1800);
    expect(r.notes.join(" ")).toContain("ESTIMATE");
  });

  test("an unweightable hole returns LEASE months, and says so", async () => {
    db.dossier = dossier({
      production: [month("2024-01", { oil: 1000, csgd: 500 })],
      productionByTest: [],
      allocationShare: 0.2,
    });
    const r = await call("rrc_allocate_well", { api: "42123456" });

    expect(r.grain).toBe("lease");
    expect(r.allocation.method).toBe("even-split");
    // Never the lease figure under a per-well name.
    expect(r.months[0].oil_bbl).toBeNull();
    expect(r.months[0].lease_oil_bbl).toBe(1000);
    expect(r.months[0].oil_share).toBeNull();
    expect(r.allocation.evenSplitShare).toBe(0.2);
  });

  test("a missing wellbore is a value, not a throw", async () => {
    db.dossier = null;
    const r = await call("rrc_allocate_well", { api: "00000000" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("00000000");
  });
});

// ------------------------------------------------------------------- 14

describe("rrc_allocation_basis", () => {
  /**
   * Two tests on this hole: January reports no oil rate (a test can be filed
   * with a gas rate and no oil), June reports 40 bbl/d. Four wells on schedule,
   * so the head-count share is 1/4.
   *
   * By hand: May is governed by the January test, which cannot weight oil, so
   * May's oil is the head-count residual and lands exactly on 0.25. June is
   * governed by its own test and lands on 400/1000 = 0.4, which is not 0.25.
   * Gas is test-backed in BOTH months, because the January test does carry a gas
   * rate: one test, two different answers, which is why the two are labelled
   * separately.
   */
  beforeEach(() => {
    db.dossier = dossier({
      production: [
        month("2024-05", { oil: 1000, csgd: 500 }),
        month("2024-06", { oil: 1000, csgd: 500 }),
      ],
      productionByTest: [
        month("2024-05", { oil: 250, csgd: 200 }),
        month("2024-06", { oil: 400, csgd: 200 }),
      ],
      allocationShare: 0.25,
      // Newest first, as the query returns them.
      w10: [w10("2024-06-10", 40, 100), w10("2024-01-15", null, 100)],
      w10Share: 0.4,
    });
    db.leaseW10 = {
      wells: [
        { well_no: "3", api_number: "42123456", test_date: "2024-06-10", daily_oil: 40, producing_method: "P", share: 0.4 },
        { well_no: "4", api_number: "42123457", test_date: "2024-06-10", daily_oil: 60, producing_method: "P", share: 0.6 },
      ],
      testedBopd: 100,
      untested: 2,
    };
  });

  test("a test-backed month is marked differently from a head-count month", async () => {
    const r = await call("rrc_allocation_basis", { api: "42123456" });

    const may = r.months[0];
    const june = r.months[1];

    expect(may.cycle).toBe("2024-05");
    expect(may.oil_basis).toBe("head-count");
    expect(may.governing_test_date).toBe("2024-01-15");
    expect(may.oil_share).toBeCloseTo(0.25, 10);
    expect(may.oil_share_matches_even_split).toBe(true);

    expect(june.oil_basis).toBe("well-test");
    expect(june.governing_test_date).toBe("2024-06-10");
    expect(june.oil_share).toBeCloseTo(0.4, 10);
    expect(june.oil_share_matches_even_split).toBe(false);

    // The two labels are genuinely different, which is the property that fails
    // when a tool asserts "weighted by test" for every month it emits.
    expect(may.oil_basis).not.toBe(june.oil_basis);
  });

  test("one test can weight the gas and fail to weight the oil", async () => {
    const r = await call("rrc_allocation_basis", { api: "42123456" });
    expect(r.months[0].oil_basis).toBe("head-count");
    expect(r.months[0].gas_basis).toBe("well-test");
    expect(r.months[0].governing_test_gas_mcf_per_day).toBe(100);
    expect(r.months[0].governing_test_oil_bbl_per_day).toBeNull();
  });

  test("the tests behind the split are shown, not just the answer", async () => {
    const r = await call("rrc_allocation_basis", { api: "42123456" });
    expect(r.wells_on_schedule).toBe(4);
    expect(r.even_split_share).toBe(0.25);
    expect(r.this_well_tests).toHaveLength(2);
    expect(r.this_well_tests[0].test_date).toBe("2024-06-10");
    expect(r.lease_tests.tested_bopd).toBe(100);
    expect(r.lease_tests.wells).toHaveLength(2);
    expect(r.lease_tests.untested_wells).toBe(2);
  });

  test("an unweighted hole is refused rather than explained", async () => {
    db.dossier = dossier({ production: [month("2024-05", { oil: 10 })], productionByTest: [] });
    const r = await call("rrc_allocation_basis", { api: "42123456" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("no current schedule");
  });
});

// ------------------------------------------------------------------- 15

describe("rrc_deliverability_trend", () => {
  /**
   * Two flowing tests exactly 730 days apart, 1,000 then 500 mcf/d, and a third
   * filed while the well was shut in.
   *
   * By hand: 730 / 365.25 = 1.998631075 years, so the log-rate slope is
   * ln(0.5) / 1.998631075 = -0.34681097 per year, an effective annual decline of
   * (1 - e^-0.34681097) x 100 = 29.306%. The shut-in test is NOT in that fit; a
   * closed well tests at no rate for a reason that is not decline.
   *
   * Shut-in wellhead pressure falls 2,000 to 1,600 over the same span, so
   * -400 / 1.998631075 = -200.137 psi/yr.
   */
  beforeEach(() => {
    db.g10 = [
      g10({ test_date: "2024-01-01", daily_gas: 500, siwh_press: 1600, flow_press: 800 }),
      g10({ test_date: "2022-01-01", daily_gas: 1000, siwh_press: 2000, flow_press: 900 }),
      g10({ test_date: "2025-01-01", daily_gas: 0, shut_in_flag: "Y" }),
    ];
  });

  test("decline is fitted over flowing tests only", async () => {
    const r = await call("rrc_deliverability_trend", { district: "08", gas_id: "123456" });

    expect(r.ok).toBe(true);
    expect(r.tests).toBe(3);
    expect(r.shut_in_tests).toBe(1);
    expect(r.decline.n).toBe(2);
    expect(r.decline.nominal_per_year).toBeCloseTo(0.34681, 4);
    expect(r.decline.effective_pct_per_year).toBeCloseTo(29.306, 2);
    expect(r.decline.first_mcf_per_day).toBe(1000);
    expect(r.decline.last_mcf_per_day).toBe(500);
  });

  test("shut-in pressure carries its own trend", async () => {
    const r = await call("rrc_deliverability_trend", { district: "08", gas_id: "123456" });
    expect(r.shut_in_pressure.psi_per_year).toBeCloseTo(-200.137, 2);
    expect(r.shut_in_pressure.n).toBe(2);
    expect(r.shut_in_pressure.first).toBe(2000);
  });

  test("a missing potential is never reported as zero", async () => {
    // One filing leaves it null, the other zero-fills it. Both mean the field
    // rules did not require the test.
    db.g10 = [
      g10({ test_date: "2024-01-01", daily_gas: 500, potential: 0 }),
      g10({ test_date: "2022-01-01", daily_gas: 1000, potential: null }),
    ];
    const r = await call("rrc_deliverability_trend", { district: "08", gas_id: "123456" });

    expect(r.series[0].potential_mcf_per_day).toBeNull();
    expect(r.series[1].potential_mcf_per_day).toBeNull();
    expect(r.series.map((s: { potential_mcf_per_day: number | null }) => s.potential_mcf_per_day)).not.toContain(0);
    expect(r.notes.join(" ")).toContain("NOT REQUIRED");
  });

  test("a same-day multi-point test collapses to one point on the curve", async () => {
    db.g10 = [
      g10({ test_date: "2024-01-01", daily_gas: 190, flow_press: 900 }),
      g10({ test_date: "2024-01-01", daily_gas: 640, flow_press: 600 }),
      g10({ test_date: "2022-01-01", daily_gas: 1000 }),
    ];
    const r = await call("rrc_deliverability_trend", { district: "08", gas_id: "123456" });
    expect(r.tests).toBe(2);
    // The deliverability of the day is its largest rate, not the choked point.
    expect(r.series[1].daily_gas_mcf).toBe(640);
  });

  test("an oil completion is told which form it files", async () => {
    db.dossier = dossier({ header: { oil_gas_code: "O" }, g10: [] });
    const r = await call("rrc_deliverability_trend", { api: "42123456" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("W-10");
  });
});

// ------------------------------------------------------------------- 16

describe("rrc_aof", () => {
  /**
   * Three points of one back-pressure test at a 1,000 psi shut-in pressure:
   *
   *   Pwf 900 -> Pr^2 - Pwf^2 = 190,000, q = 190
   *   Pwf 800 ->                360,000, q = 360
   *   Pwf 600 ->                640,000, q = 640
   *
   * q is exactly (Pr^2 - Pwf^2) / 1000 at every point, so the log-log line is
   * exactly straight: n = 1 and C = 0.001 by construction, before any fit runs.
   * AOF is that curve at Pwf = 0, which is 0.001 x 1,000^2 = 1,000 mcf/d.
   */
  const threePoint = [
    g10({ test_date: "2024-03-01", daily_gas: 190, siwh_press: 1000, flow_press: 900 }),
    g10({ test_date: "2024-03-01", daily_gas: 360, siwh_press: 1000, flow_press: 800 }),
    g10({ test_date: "2024-03-01", daily_gas: 640, siwh_press: 1000, flow_press: 600 }),
  ];

  test("fits Rawlins-Schellhardt and evaluates at zero flowing pressure", async () => {
    db.g10 = threePoint;
    const r = await call("rrc_aof", { district: "08", gas_id: "123456" });

    expect(r.ok).toBe(true);
    expect(r.refusal).toBeNull();
    expect(r.points).toBe(3);
    expect(r.test_date).toBe("2024-03-01");
    expect(r.fit.n).toBeCloseTo(1, 10);
    expect(r.fit.c).toBeCloseTo(0.001, 10);
    expect(r.fit.r2).toBeCloseTo(1, 10);
    expect(r.aof_mcf_per_day).toBeCloseTo(1000, 6);
  });

  test("refuses a single-point test rather than fitting one point", async () => {
    db.g10 = [threePoint[0]];
    const r = await call("rrc_aof", { district: "08", gas_id: "123456" });

    expect(r.ok).toBe(true);
    expect(r.aof_mcf_per_day).toBeNull();
    expect(r.fit).toBeNull();
    expect(r.refusal).toContain("3 flow points");
    expect(r.refusal).toContain("one flow point per filing");
  });

  test("will not pool points from different years into one curve", async () => {
    db.g10 = [
      g10({ test_date: "2022-03-01", daily_gas: 190, siwh_press: 1000, flow_press: 900 }),
      g10({ test_date: "2023-03-01", daily_gas: 360, siwh_press: 1000, flow_press: 800 }),
      g10({ test_date: "2024-03-01", daily_gas: 640, siwh_press: 1000, flow_press: 600 }),
    ];
    const r = await call("rrc_aof", { district: "08", gas_id: "123456" });
    expect(r.aof_mcf_per_day).toBeNull();
    expect(r.refusal).toContain("different YEARS");
  });

  test("an absent filed potential is null and explained, not zero", async () => {
    db.g10 = [g10({ test_date: "2024-03-01", daily_gas: 190, siwh_press: 1000, flow_press: 900, potential: 0 })];
    const r = await call("rrc_aof", { district: "08", gas_id: "123456" });

    expect(r.filed_potential).toBeNull();
    expect(r.filed_potential_note).toContain("NOT REQUIRED");
  });

  test("a filed potential is passed through when the field rules required one", async () => {
    db.g10 = [
      g10({ test_date: "2024-03-01", daily_gas: 190, siwh_press: 1000, flow_press: 900, potential: 2500 }),
    ];
    const r = await call("rrc_aof", { district: "08", gas_id: "123456" });
    expect(r.filed_potential.potential_mcf_per_day).toBe(2500);
  });
});

// ------------------------------------------------------------------- 17

describe("rrc_drawdown", () => {
  test("drawdown and gas-liquid ratio off the latest test", async () => {
    // 1,200 shut in against 900 flowing is 300 psi, a quarter of the shut-in
    // pressure. 5,000 mcf against 100 bbl is 50,000 cf/bbl, which is what the
    // filing says, and half the statutory gas-well line.
    db.g10 = [
      g10({
        test_date: "2024-05-01",
        daily_gas: 5000,
        daily_cond: 100,
        siwh_press: 1200,
        flow_press: 900,
        gas_liquid_ratio: 50000,
      }),
    ];
    const r = await call("rrc_drawdown", { district: "08", gas_id: "123456" });

    expect(r.latest.drawdown_psi).toBe(300);
    expect(r.latest.drawdown_fraction).toBeCloseTo(0.25, 10);
    expect(r.latest.gas_liquid_ratio_computed).toBeCloseTo(50000, 6);
    expect(r.latest.gas_liquid_ratio_agrees).toBe(true);
    expect(r.latest.classifies_as_gas_well).toBe(false);
  });

  test("a zero-filled pressure is not recorded, not a measurement", async () => {
    db.g10 = [
      g10({ test_date: "2022-05-01", daily_gas: 4000, siwh_press: 1200, flow_press: 900 }),
      g10({ test_date: "2024-05-01", daily_gas: 5000, siwh_press: 0, flow_press: 0 }),
    ];
    const r = await call("rrc_drawdown", { district: "08", gas_id: "123456" });

    expect(r.latest.test_date).toBe("2024-05-01");
    expect(r.latest.shut_in_wellhead_psi).toBeNull();
    expect(r.latest.drawdown_psi).toBeNull();
    expect(r.latest.drawdown_reason).toContain("not zero");
    // The older filing that does carry pressures is offered, never substituted.
    expect(r.latest_with_pressures.test_date).toBe("2022-05-01");
    expect(r.latest_with_pressures.drawdown_psi).toBe(300);
  });
});

// ------------------------------------------------------------------- 18

describe("rrc_fluid_level_trend", () => {
  /**
   * Top of fluid 2,000 ft on 2020-01-01, 1,600 on 2022-01-01, 1,200 on
   * 2024-01-01: the column is rising 400 ft every two years.
   *
   * By hand, with x in 365.25-day years from the first test: x = 0,
   * 731/365.25 = 2.001368925, 1461/365.25 = 4. mx = 2.000456308, my = 1600.
   * Sxy = -1600 exactly and Sxx = 8.000001249, so the slope is -199.9999688
   * ft/yr and the intercept 2000.0911992 ft. The line reaches surface at
   * x = 2000.0911992 / 199.9999688 = 10.0004576 years, which is 6.0004576 years
   * after the last test.
   */
  beforeEach(() => {
    db.h15 = [
      h15({ test_date: "2024-01-01", top_of_fluid: 1200 }),
      h15({ test_date: "2022-01-01", top_of_fluid: 1600 }),
      h15({ test_date: "2020-01-01", top_of_fluid: 2000 }),
    ];
  });

  test("rise rate and time to surface", async () => {
    const r = await call("rrc_fluid_level_trend", { api: "42123456" });

    expect(r.ok).toBe(true);
    expect(r.tests).toBe(3);
    expect(r.fit.slope_ft_per_year).toBeCloseTo(-200, 3);
    expect(r.rise_ft_per_year).toBeCloseTo(200, 3);
    expect(r.years_to_surface).toBeCloseTo(6.0005, 3);
    expect(r.latest_top_of_fluid_ft).toBe(1200);
    expect(r.notes.join(" ")).toContain("year behind");
  });

  test("a falling column does not project to surface", async () => {
    db.h15 = [
      h15({ test_date: "2024-01-01", top_of_fluid: 2000 }),
      h15({ test_date: "2020-01-01", top_of_fluid: 1200 }),
    ];
    const r = await call("rrc_fluid_level_trend", { api: "42123456" });

    expect(r.rise_ft_per_year).toBeLessThan(0);
    expect(r.years_to_surface).toBeNull();
    expect(r.years_to_surface_reason).toContain("falling or flat");
  });

  test("one test is a refusal, and late filing is the reason offered", async () => {
    db.h15 = [h15({ test_date: "2024-01-01", top_of_fluid: 1200 })];
    const r = await call("rrc_fluid_level_trend", { api: "42123456" });

    expect(r.ok).toBe(true);
    expect(r.rise_ft_per_year).toBeNull();
    expect(r.refusal).toContain("needs two");
    expect(r.refusal).toContain("year behind");
  });

  test("a zero-filled fluid depth is dropped, not read as surface", async () => {
    db.h15 = [
      h15({ test_date: "2024-01-01", top_of_fluid: 0 }),
      h15({ test_date: "2022-01-01", top_of_fluid: 1600 }),
      h15({ test_date: "2020-01-01", top_of_fluid: 2000 }),
    ];
    const r = await call("rrc_fluid_level_trend", { api: "42123456" });
    // Two usable tests, and the fit is only what they support: 400 ft over the
    // 731 days from 2020-01-01 to 2022-01-01 is 400 / 2.001368925 = 199.8632
    // ft/yr. The dropped row does not pull the line down to surface.
    expect(r.tests).toBe(2);
    expect(r.rise_ft_per_year).toBeCloseTo(199.8632, 3);
  });
});

// ------------------------------------------------------------------- 19

describe("rrc_h15_clock", () => {
  test("days remaining, counted to the first of the due month", async () => {
    // Due 2026-09-01, asked on 2026-08-10: 22 days.
    db.h15 = [h15({ test_date: "2025-09-04", next_test_due: "2026-09", status: "A" })];
    db.operatorH15 = { wellsTested: 40, delinquent: 3, dueSoon: 5, lastTest: "2026-07-01" };

    const r = await call("rrc_h15_clock", { api: "42123456", as_of: "2026-08-10" });

    expect(r.well.days_to_due).toBe(22);
    expect(r.well.past_due).toBe(false);
    expect(r.well.delinquent).toBe(false);
    // The filing names the operator, so an API alone reaches the fleet rollup.
    expect(r.operator.operator_no).toBe("123456");
    expect(r.operator.delinquent).toBe(3);
    expect(r.operator.due_within_90_days).toBe(5);
  });

  test("past due counts negative", async () => {
    // Due 2026-06-01, asked on 2026-08-10: 30 + 31 + 9 = 70 days past.
    db.h15 = [h15({ test_date: "2025-05-04", next_test_due: "2026-06", status: "D" })];
    const r = await call("rrc_h15_clock", { api: "42123456", as_of: "2026-08-10" });

    expect(r.well.days_to_due).toBe(-70);
    expect(r.well.past_due).toBe(true);
    expect(r.well.delinquent).toBe(true);
  });

  test("no filing is a stated reason, not a zero clock", async () => {
    db.h15 = [];
    const r = await call("rrc_h15_clock", { api: "42123456", as_of: "2026-08-10" });

    expect(r.well.days_to_due).toBeNull();
    expect(r.well.next_test_due).toBeNull();
    expect(r.well.reason).toContain("inactive-well test");
    expect(r.operator).toBeNull();
  });

  test("the operator's own clock is flagged as the database's, not as_of", async () => {
    db.operatorH15 = { wellsTested: 40, delinquent: 3, dueSoon: 5, lastTest: "2026-07-01" };
    const r = await call("rrc_h15_clock", { operator_no: "123456", as_of: "2026-08-10" });

    expect(r.well).toBeNull();
    expect(r.operator.wells_tested).toBe(40);
    expect(r.notes.join(" ")).toContain("not against as_of");
  });

  test("neither key is a refusal", async () => {
    const r = await call("rrc_h15_clock", {});
    expect(r.ok).toBe(false);
    expect(r.error).toContain("operator_no");
  });
});

// ------------------------------------------------------- 20/21 well ranking

/**
 * Ranking wells, which is the question the lease grain cannot answer.
 *
 * The split's own arithmetic is proved against a hand oracle in
 * `../well-rank.test.ts`. What these check is the part only the tool can get
 * wrong: the DISTRICT, which is coded two different ways in two tables, and
 * whether the estimate still reconciles to the filing after the tool has moved
 * it around.
 *
 * The district is the one to fear. `wellbore` and `w10_test` are keyed on the
 * real label ("09"), `lease_production` on PDQ's internal code ("13"), and they
 * are not interchangeable. Swapping them lands on a different district's lease
 * and reports another operator's production as this one's, with no error
 * anywhere.
 */
describe("rrc_lease_well_ranking", () => {
  beforeEach(() => {
    db.calls = [];
    // Two wells. Well 1 tests at 30 bbl/d, well 2 at 10.
    db.rankWells = [
      {
        oil_gas_code: "O",
        district: "09",
        lease_number: "33913",
        well_no: "1",
        api_number: "50342430",
        completion_date: null,
        well_type_name: "OIL",
        shut_in_date: null,
      },
      {
        oil_gas_code: "O",
        district: "09",
        lease_number: "33913",
        well_no: "2",
        api_number: "50342444",
        completion_date: null,
        well_type_name: "OIL",
        shut_in_date: null,
      },
    ];
    db.rankTests = [
      { district: "09", lease_no: "33913", well_no: "1", test_date: "2025-01-10", daily_oil: 30, daily_gas: 0 },
      { district: "09", lease_no: "33913", well_no: "2", test_date: "2025-01-10", daily_oil: 10, daily_gas: 0 },
    ];
    db.rankMonths = [
      { oil_gas_code: "O", district_no: "13", lease_no: "33913", month: "2026-04", oil: 1000, gas: 0 },
      { oil_gas_code: "O", district_no: "13", lease_no: "33913", month: "2026-05", oil: 800, gas: 0 },
    ];
  });

  test("reads wells and tests on the real district, production on the internal one", async () => {
    const r = await call("rrc_lease_well_ranking", {
      oil_gas_code: "O",
      district_no: "13",
      lease_no: "33913",
    });
    expect(r.ok).toBe(true);

    // District 13 is PDQ's internal code for District 09. Everything below is
    // asserted on the PARAMETERS the mirror actually received.
    const wells = db.calls.find((c) => c.sql.includes("from rrc.wellbore w"))!;
    expect(wells.params[1]).toEqual(["09"]);
    const tests = db.calls.find((c) => c.sql.includes("from rrc.w10_test t"))!;
    expect(tests.params[0]).toEqual(["09"]);
    const prod = db.calls.find((c) => c.sql.includes("from rrc.lease_production p"))!;
    expect(prod.params[1]).toEqual(["13"]);
  });

  test("splits the lease 30:10 and hands back each well's API", async () => {
    const r = await call("rrc_lease_well_ranking", {
      oil_gas_code: "O",
      district_no: "13",
      lease_no: "33913",
    });
    // By hand: both wells tested, so the split is the rate ratio, 0.75 and 0.25
    // of 1,800 barrels.
    expect(r.lease_totals.oil_bbl).toBe(1800);
    expect(r.wells.map((w: { well_no: string }) => w.well_no)).toEqual(["1", "2"]);
    expect(r.wells[0].oil_bbl).toBeCloseTo(1350, 9);
    expect(r.wells[1].oil_bbl).toBeCloseTo(450, 9);
    // Chainable, or the answer is a dead end: nothing else here takes a well_no.
    expect(r.wells[0].api).toBe("50342430");
    // The reader's check.
    expect(r.wells.reduce((a: number, w: { oil_bbl: number }) => a + w.oil_bbl, 0)).toBeCloseTo(
      r.lease_totals.oil_bbl,
      9
    );
  });

  test("says so when the lease filed nothing, rather than returning zeros", async () => {
    db.rankMonths = [];
    const r = await call("rrc_lease_well_ranking", {
      oil_gas_code: "O",
      district_no: "13",
      lease_no: "33913",
    });
    expect(r.ok).toBe(false);
    // The likeliest cause is the district coding, so the refusal names it.
    expect(r.error).toMatch(/INTERNAL code/);
  });
});

describe("rrc_operator_well_ranking", () => {
  beforeEach(() => {
    db.calls = [];
    db.rankLeases = [
      { oil_gas_code: "O", district: "09", lease_number: "33913", lease_name: "ROACH", field_name: "YOUNG", ours: 2 },
      { oil_gas_code: "O", district: "7B", lease_number: "16666", lease_name: "CORBETT", field_name: "CORBETT", ours: 1 },
    ];
    db.rankWells = [
      { oil_gas_code: "O", district: "09", lease_number: "33913", well_no: "1", api_number: "A1", completion_date: null, well_type_name: "OIL", shut_in_date: null },
      { oil_gas_code: "O", district: "09", lease_number: "33913", well_no: "2", api_number: "A2", completion_date: null, well_type_name: "OIL", shut_in_date: null },
      { oil_gas_code: "O", district: "7B", lease_number: "16666", well_no: "1", api_number: "B1", completion_date: null, well_type_name: "OIL", shut_in_date: null },
    ];
    db.rankTests = [
      { district: "09", lease_no: "33913", well_no: "1", test_date: "2025-01-10", daily_oil: 30, daily_gas: 0 },
      { district: "09", lease_no: "33913", well_no: "2", test_date: "2025-01-10", daily_oil: 10, daily_gas: 0 },
    ];
    db.rankMonths = [
      // PDQ's internal codes, which is how `lease_production` is keyed: real
      // district 09 is internal 13, and real 7B is internal 08. A fixture that
      // repeated the real label here would be testing nothing.
      { oil_gas_code: "O", district_no: "13", lease_no: "33913", month: "2026-05", oil: 1000, gas: 0 },
      { oil_gas_code: "O", district_no: "08", lease_no: "16666", month: "2026-05", oil: 600, gas: 0 },
    ];
  });

  test("ranks wells across leases, not leases", async () => {
    const r = await call("rrc_operator_well_ranking", { operator_no: "786408" });
    expect(r.ok).toBe(true);

    // By hand: ROACH splits 1,000 as 750/250; CORBETT's single well takes all
    // 600. So the order is 750, 600, 250 — and the middle well beats the third
    // ONLY because the split happened. Ranking by lease would put both ROACH
    // wells above CORBETT and be wrong.
    expect(
      r.wells.map((w: { lease_no: string; well_no: string; oil_bbl: number }) => [
        w.lease_no,
        w.well_no,
        Math.round(w.oil_bbl),
      ])
    ).toEqual([
      ["33913", "1", 750],
      ["16666", "1", 600],
      ["33913", "2", 250],
    ]);
  });

  test("reads the whole fleet in a fixed number of queries", async () => {
    await call("rrc_operator_well_ranking", { operator_no: "786408" });
    // One lease list, then one read each for wells, tests and months. A
    // per-lease loop here is what makes a 200-lease operator time out.
    expect(db.calls).toHaveLength(4);
  });

  test("refuses an operator with nothing on a current schedule", async () => {
    db.rankLeases = [];
    const r = await call("rrc_operator_well_ranking", { operator_no: "000000" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/no wells on a current P-5 schedule/);
  });
});

// ---------------------------------------------------------------- catalog

test("every tool is named, summarised and reachable", () => {
  expect(TOOLS.map((t) => t.name)).toEqual([
    "rrc_allocate_well",
    "rrc_allocation_basis",
    "rrc_lease_well_ranking",
    "rrc_operator_well_ranking",
    "rrc_deliverability_trend",
    "rrc_aof",
    "rrc_drawdown",
    "rrc_fluid_level_trend",
    "rrc_h15_clock",
  ]);
  for (const t of TOOLS) {
    expect(t.summary.length).toBeGreaterThan(20);
    expect(t.summary).not.toContain("\n");
  }
});
