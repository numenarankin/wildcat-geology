import { beforeEach, describe, expect, test, vi } from "vitest";

import type { LeaseMonth, OperatorWellListRow } from "../../../scout/rrc-types";

/**
 * The operator catalog, against fixtures whose right answer is computed here by
 * hand rather than by running the code and writing down what it said.
 *
 * Four properties carry the weight:
 *
 *  1. `rrc_aggregate` NEVER BUILDS SQL FROM CALLER TEXT and never scans the
 *     state unfiltered. Both are checked against the query string and the
 *     parameter array the mirror actually received, not against the result.
 *  2. `rrc_operator_health` is a WEIGHTED SUM OF PUBLISHED COMPONENTS. The test
 *     applies the weights itself; if the composite and the components ever stop
 *     agreeing, the number cannot be argued with and the tool is worthless.
 *  3. `rrc_plugging_liability` PRODUCES NO MONEY. The RRC carries no cost data
 *     and a dollar figure here would be invention wearing a citation.
 *  4. `rrc_permit_cycle` tiles two twelve-month windows against the PERMIT tape's
 *     own edge. A month double-counted or dropped at the seam moves the headline
 *     change by several points and looks like activity.
 */

const db = vi.hoisted(() => ({
  /** Production reporting edge. Three months behind the calendar, as ever. */
  cycleEdge: "2026-05",
  queries: [] as { sql: string; params: unknown[] }[],
  dossiers: new Map<string, unknown>(),
  plugCount: { state_funded: 0, plugged: 0 } as { state_funded: number; plugged: number } | null,
  plugComparables: [] as unknown[],
  aggregateRows: [] as unknown[],
  permitEdge: "2026-08" as string | null,
  permitMonthly: [] as { cycle: string; permits: number }[],
  lagRows: [] as unknown[],
  spudRow: null as unknown,
  p4Rows: [] as unknown[],
  firstProduction: [] as unknown[],
  activityPlugs: [] as unknown[],
  permits: [] as unknown[],
  permitArgs: [] as unknown[],
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string, params: unknown[]) => {
    db.queries.push({ sql, params });
    if (sql.includes("lpad(w.recent_permit")) return db.lagRows;
    if (sql.includes("date_trunc('month', p.issued_date)")) return db.permitMonthly;
    if (sql.includes("order by plugs)")) return db.plugComparables;
    if (sql.includes("candidate as")) return db.firstProduction;
    if (sql.includes("rrc.county_lease_cycle")) return db.aggregateRows;
    if (sql.includes("rrc.p4_filing")) return db.p4Rows;
    if (sql.includes("rrc.wb_plug_summary s")) return db.activityPlugs;
    // The inactive-well read. `rrc_plugging_liability` asks the database rather
    // than filtering the dossier's well list, because that list is capped and
    // filtering it would undercount a liability silently. The mock applies the
    // same predicate the SQL does, over the same fixture, so the fixture stays
    // the one source of truth and the threshold test still bites.
    if (sql.includes("coalesce(nullif(curr_inact_yrs")) {
      const [op, threshold] = params as [string, number];
      const dossier = db.dossiers.get(op) as { wellRows?: unknown[] } | undefined;
      const rows = (dossier?.wellRows ?? []) as {
        api_depth: number | null;
        curr_inact_yrs: number | null;
        plug_date: string | null;
      }[];
      return rows
        .filter((w) => !w.plug_date && (w.curr_inact_yrs ?? 0) >= threshold)
        .map((w) => ({ api_depth: w.api_depth }));
    }
    throw new Error(`unexpected query: ${sql.slice(0, 80)}`);
  },
  rrcQueryOne: async (sql: string, params: unknown[]) => {
    db.queries.push({ sql, params });
    if (sql.includes("max(issued_date)")) return { permit_edge: db.permitEdge };
    if (sql.includes("s.state_funded)")) return db.plugCount;
    if (sql.includes("cmpl_or_recmpl_date")) return db.spudRow;
    throw new Error(`unexpected queryOne: ${sql.slice(0, 80)}`);
  },
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getCycleEdge: async () => ({ reported: db.cycleEdge, loaded: "2026-08" }),
  getOperatorDossier: async (op: string) => db.dossiers.get(op) ?? null,
  listPermits: async (args: unknown) => {
    db.permitArgs.push(args);
    return db.permits;
  },
  /** The real table trimmed to what these tests use. */
  resolveCounty: (ref: string) =>
    ref.trim().toUpperCase() === "REEVES"
      ? { county_no: "389", county_name: "REEVES" }
      : null,
}));

const { TOOLS } = await import("./operator");

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Result = any;

const find = (name: string) => {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`No tool ${name}. Have: ${TOOLS.map((t) => t.name).join(", ")}`);
  return tool;
};

const call = async (name: string, args: Record<string, unknown>): Promise<Result> =>
  (await find(name).run(find(name).args.parse(args) as never)) as Result;

/** Straight to the function, past the schema, for its own guards. */
const callRaw = async (name: string, args: Record<string, unknown>): Promise<Result> =>
  (await find(name).run(args as never)) as Result;

// --------------------------------------------------------------- fixtures

function cycles(start: string, n: number): string[] {
  const [y, m] = start.split("-").map(Number);
  return Array.from({ length: n }, (_, i) => {
    const t = y * 12 + (m - 1) + i;
    return `${Math.floor(t / 12)}-${String((t % 12) + 1).padStart(2, "0")}`;
  });
}

/** Oil only, so barrels of oil equivalent is the barrel count and nothing else. */
function month(cycle: string, oil: number, reported = true): LeaseMonth {
  return {
    cycle,
    oil_prod_vol: oil,
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
    prod_report_filed: null,
    reported,
  };
}

function well(over: Partial<OperatorWellListRow> = {}): OperatorWellListRow {
  return {
    api_number: "31700001",
    well_no: "1",
    lease_name: "TEST",
    lease_no: "12345",
    county_name: "REEVES",
    well_type_name: null,
    api_depth: null,
    curr_inact_yrs: null,
    plug_date: null,
    flagged14b2: false,
    ...over,
  };
}

/**
 * The health fixture, chosen so every component lands on a round score.
 *
 * 100 wells on schedule, 10 flagged, 12 plugged; 80 H-15 tested with 4
 * delinquent; one state-funded plug; P-5 active; and 24 reported months that
 * step from 100 bbl to 75 bbl at the halfway mark.
 */
function healthDossier() {
  const series = cycles("2024-06", 24);
  return {
    record: { operator_number: "111111", operator_name: "ORACLE OIL", p5_status: "A" },
    wells: { total: 100, byType: [], plugged: 12, flagged14b2: 10, reasons: [], surfaceViolations: 0, w3xViolations: 0 },
    wellRows: [],
    h15: { wellsTested: 80, delinquent: 4, dueSoon: 0, lastTest: null },
    monthly: series.map((c, i) => month(c, i < 12 ? 100 : 75)),
  };
}

beforeEach(() => {
  db.queries.length = 0;
  db.dossiers.clear();
  db.plugCount = { state_funded: 0, plugged: 0 };
  db.plugComparables = [];
  db.aggregateRows = [];
  db.permitEdge = "2026-08";
  db.permitMonthly = [];
  db.lagRows = [];
  db.spudRow = null;
  db.p4Rows = [];
  db.firstProduction = [];
  db.activityPlugs = [];
  db.permits = [];
  db.permitArgs.length = 0;
  db.cycleEdge = "2026-05";
});

// --------------------------------------------------------------------- 30

describe("rrc_operator_health", () => {
  test("composite is the published components under the published weights", async () => {
    db.dossiers.set("111111", healthDossier());
    db.plugCount = { state_funded: 1, plugged: 3 };

    const r = await call("rrc_operator_health", { operator_no: "111111" });
    expect(r.ok).toBe(true);

    // Hand-computed, floor by floor.
    //   flag rate      10/100 = 0.10 over a 0.25 floor -> 1 - 0.40 = 0.60
    //   H-15 delinq     4/80  = 0.05 over a 0.25 floor -> 1 - 0.20 = 0.80
    //   plugged share  12/100 = 0.12 over a 0.60 floor -> 1 - 0.20 = 0.80
    //   state funded    1 well over a 3-well floor     -> 1 - 1/3  = 0.6667
    //   P-5 'A'                                        -> 1
    //   trend        900/1200 - 1 = -0.25, floor -0.50 -> 1 - 0.50 = 0.50
    const score = (name: string) =>
      r.components.find((c: Result) => c.component === name).score;
    expect(score("flag_14b2")).toBeCloseTo(0.6, 10);
    expect(score("h15_delinquency")).toBeCloseTo(0.8, 10);
    expect(score("plugged_share")).toBeCloseTo(0.8, 10);
    expect(score("state_funded_plugs")).toBeCloseTo(2 / 3, 10);
    expect(score("p5_status")).toBe(1);
    expect(score("production_trend")).toBeCloseTo(0.5, 10);

    // 0.25(0.60) + 0.20(0.80) + 0.15(0.80) + 0.20(2/3) + 0.10(1) + 0.10(0.50)
    // = 0.150 + 0.160 + 0.120 + 0.133333 + 0.100 + 0.050 = 0.7133333
    expect(r.weight_used).toBeCloseTo(1, 10);
    expect(r.composite_score).toBeCloseTo(71.333333, 5);

    // Every weight is on the result, so a reader can rescore by hand.
    expect(r.weights).toEqual({
      flag_14b2: 0.25,
      h15_delinquency: 0.2,
      plugged_share: 0.15,
      state_funded_plugs: 0.2,
      p5_status: 0.1,
      production_trend: 0.1,
    });
    const stated = Object.values(r.weights as Record<string, number>).reduce((a, b) => a + b, 0);
    expect(stated).toBeCloseTo(1, 10);
    expect(r.notes.join(" ")).toMatch(/ASSERTED, not fitted/);
  });

  test("the trailing windows stop at the reported edge, so unfiled zeros never score", async () => {
    const d = healthDossier();
    // Three unfiled cycles on the end, exactly as the mirror carries them.
    d.monthly = [...d.monthly, ...cycles("2026-06", 3).map((c) => month(c, 0, false))];
    db.dossiers.set("111111", d);

    const r = await call("rrc_operator_health", { operator_no: "111111" });
    expect(r.reported_through).toBe("2026-05");
    // Unchanged from the fixture above: the zeros were dropped, not averaged in.
    expect(r.inputs.boe_last_12).toBe(900);
    expect(r.inputs.boe_prior_12).toBe(1200);
    expect(r.inputs.production_change).toBeCloseTo(-0.25, 10);
  });

  test("an unscorable component is dropped and the rest renormalised", async () => {
    db.dossiers.set("222222", {
      record: { operator_number: "222222", operator_name: "NO FLEET LLC", p5_status: "D" },
      wells: { total: 0, byType: [], plugged: 0, flagged14b2: 0, reasons: [], surfaceViolations: 0, w3xViolations: 0 },
      wellRows: [],
      h15: { wellsTested: 0, delinquent: 0, dueSoon: 0, lastTest: null },
      monthly: [],
    });

    const r = await call("rrc_operator_health", { operator_no: "222222" });
    // Only state-funded plugs (0.20), P-5 (0.10) and trend survive, and trend
    // has no history: 0.20 + 0.10 = 0.30 of weight is usable.
    expect(r.weight_used).toBeCloseTo(0.3, 10);
    // 0.20(1) + 0.10(0) over 0.30 = 0.6667
    expect(r.composite_score).toBeCloseTo(66.666666, 5);
  });

  test("well counts are named as schedule counts", async () => {
    db.dossiers.set("111111", healthDossier());
    const r = await call("rrc_operator_health", { operator_no: "111111" });
    expect(r.wells_on_schedule).toBe(100);
    expect(r.notes.join(" ")).toMatch(/on_schedule = 'Y'/);
    expect(r.notes.join(" ")).toMatch(/per WELL by its most recent filing/);
  });

  test("an unknown operator is a refusal, not a throw", async () => {
    await expect(call("rrc_operator_health", { operator_no: "999999" })).resolves.toMatchObject({
      ok: false,
    });
  });
});

// --------------------------------------------------------------------- 31

describe("rrc_plugging_liability", () => {
  beforeEach(() => {
    db.dossiers.set("111111", {
      record: { operator_number: "111111", operator_name: "ORACLE OIL", p5_status: "A" },
      wells: { total: 6, byType: [], plugged: 1, flagged14b2: 0, reasons: [], surfaceViolations: 0, w3xViolations: 0 },
      wellRows: [
        well({ api_number: "A", api_depth: 3000, curr_inact_yrs: 2 }),
        well({ api_number: "B", api_depth: 3500, curr_inact_yrs: 5 }),
        well({ api_number: "C", api_depth: 9000, curr_inact_yrs: 3 }),
        // Active: below the inactivity threshold.
        well({ api_number: "D", api_depth: 9000, curr_inact_yrs: 0 }),
        // Already plugged: no burden left.
        well({ api_number: "E", api_depth: 4000, curr_inact_yrs: 4, plug_date: "20200101" }),
        // No depth on file: counted, never guessed at.
        well({ api_number: "F", api_depth: null, curr_inact_yrs: 6 }),
      ],
      h15: { wellsTested: 0, delinquent: 0, dueSoon: 0, lastTest: null },
      monthly: [],
    });
    db.plugComparables = [
      { band: "2500-5000", jobs: 100, median_plugs: 4, median_sacks: 170, median_depth: 3700 },
      { band: "7500-10000", jobs: 50, median_plugs: 6, median_sacks: 289, median_depth: 8600 },
    ];
  });

  test("quantities are the band medians times the well count", async () => {
    const r = await call("rrc_plugging_liability", { operator_no: "111111" });
    expect(r.ok).toBe(true);

    expect(r.inactive_unplugged_wells).toBe(4); // A, B, C, F
    expect(r.wells_scored).toBe(3);
    expect(r.wells_without_depth).toBe(1);

    const band = (name: string) => r.by_band.find((b: Result) => b.band === name);
    // A and B, median depth (3000 + 3500) / 2 = 3250.
    expect(band("2500-5000").wells).toBe(2);
    expect(band("2500-5000").median_well_depth_ft).toBe(3250);
    expect(band("2500-5000").estimated_plugs).toBe(8); // 4 x 2
    expect(band("2500-5000").estimated_cement_sacks).toBe(340); // 170 x 2
    expect(band("7500-10000").wells).toBe(1);
    expect(band("7500-10000").estimated_plugs).toBe(6);
    expect(band("7500-10000").estimated_cement_sacks).toBe(289);
    // The 5000-7500 band holds nobody and is not sent as an empty row.
    expect(r.by_band.map((b: Result) => b.band)).toEqual(["2500-5000", "7500-10000"]);

    expect(r.totals.estimated_plugs).toBe(14); // 8 + 6
    expect(r.totals.estimated_cement_sacks).toBe(629); // 340 + 289
    expect(r.totals.total_footage_ft).toBe(15500); // 3000 + 3500 + 9000 + 0
  });

  test("never returns a dollar figure", async () => {
    const r = await call("rrc_plugging_liability", { operator_no: "111111" });

    expect(r.dollars).toBeNull();
    expect(r.cost_estimate_refused).toMatch(/no plugging cost data/i);

    // Nothing anywhere in the payload is a number under a money name, and no
    // string carries a currency amount. A refusal in the notes that a number
    // elsewhere quietly contradicts would be worse than no refusal at all.
    const MONEY_KEY = /cost|price|usd|dollar|\bfee\b|amount|value|\$/i;
    const walk = (node: unknown, path: string) => {
      if (typeof node === "number") {
        expect(MONEY_KEY.test(path), `${path} is a number under a money name`).toBe(false);
      } else if (typeof node === "string") {
        expect(node, `${path} carries a currency amount`).not.toMatch(/\$\s?[\d,]/);
      } else if (Array.isArray(node)) {
        node.forEach((v, i) => walk(v, `${path}[${i}]`));
      } else if (node && typeof node === "object") {
        for (const [k, v] of Object.entries(node)) walk(v, `${path}.${k}`);
      }
    };
    walk(r, "result");
  });

  test("the inactivity threshold moves the population", async () => {
    const r = await call("rrc_plugging_liability", { operator_no: "111111", inactive_years: 4 });
    // Only B (5) and F (6) clear four years.
    expect(r.inactive_unplugged_wells).toBe(2);
    expect(r.wells_scored).toBe(1);
    expect(r.totals.estimated_plugs).toBe(4);
  });
});

// --------------------------------------------------------------------- 32

describe("rrc_activity_diff", () => {
  test("refuses without a scope", async () => {
    const r = await call("rrc_activity_diff", { since: "2026-01-01" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/operator_no, county or district/);
    expect(db.queries).toHaveLength(0);
  });

  test("refuses a malformed date", async () => {
    const r = await call("rrc_activity_diff", { county: "Reeves", since: "January 2026" });
    expect(r.ok).toBe(false);
    expect(db.queries).toHaveLength(0);
  });

  test("a county-only scope says the P-4 tape cannot answer, rather than returning nothing", async () => {
    const r = await call("rrc_activity_diff", { county: "Reeves", since: "2026-01-01" });
    expect(r.ok).toBe(true);
    expect(r.operator_transfers.count).toBe(0);
    expect(r.notes.join(" ")).toMatch(/P-4 tape carries no county/);
    expect(db.queries.some((q) => q.sql.includes("rrc.p4_filing"))).toBe(false);
  });

  test("first production stops at the reported edge even when until is later", async () => {
    const r = await call("rrc_activity_diff", {
      operator_no: "111111",
      since: "2026-01-01",
      until: "2026-08-10",
    });
    expect(r.first_production.measured_through).toBe("2026-05-01");
    const q = db.queries.find((x) => x.sql.includes("candidate as"))!;
    expect(q.params).toContain("2026-05-01");
    expect(q.params).toContain("2026-01-01");
    expect(q.params).toContain("111111");
  });
});

// --------------------------------------------------------------------- 33

describe("rrc_permit_cycle", () => {
  /**
   * A hand-built permit tape against a 2026-08 edge.
   *
   *   trailing 12: 2025-09 .. 2026-08  ->  3 + 7 + 5   = 15
   *   prior 12:    2024-09 .. 2025-08  -> 10 + 6 + 4   = 20
   *   2024-08 sits one month outside the prior window and must not count.
   */
  const monthlyFixture = [
    { cycle: "2024-08", permits: 99 },
    { cycle: "2024-09", permits: 10 },
    { cycle: "2025-01", permits: 6 },
    { cycle: "2025-08", permits: 4 },
    { cycle: "2025-09", permits: 3 },
    { cycle: "2026-01", permits: 7 },
    { cycle: "2026-08", permits: 5 },
  ];

  test("trailing 12 against prior 12 tiles the seam exactly", async () => {
    db.permitMonthly = monthlyFixture;
    const r = await call("rrc_permit_cycle", { operator_no: "111111" });

    expect(r.ok).toBe(true);
    expect(r.permit_edge).toBe("2026-08");
    expect(r.permits.trailing_12).toBe(15);
    expect(r.permits.prior_12).toBe(20);
    expect(r.permits.change).toBeCloseTo(-0.25, 10); // 15/20 - 1
    // 2024-08 is outside both windows and is not sent back either.
    expect(r.permits.monthly.map((m: Result) => m.cycle)).not.toContain("2024-08");
    expect(r.permits.monthly).toHaveLength(6);
  });

  test("permits anchor on the permit tape's edge, production on the cycle edge", async () => {
    db.permitMonthly = monthlyFixture;
    const r = await call("rrc_permit_cycle", { operator_no: "111111" });
    expect(r.permit_edge).toBe("2026-08");
    expect(r.production_reported_through).toBe("2026-05");
    const q = db.queries.find((x) => x.sql.includes("date_trunc('month', p.issued_date)"))!;
    // The anchor is bound, never written into the statement.
    expect(q.params).toContain("2026-08");
    expect(q.sql).not.toContain("2026-08");
  });

  test("the lag excludes leases that were already producing, and censoring is reported", async () => {
    db.lagRows = [
      // A brand-new lease: permitted 2024-01, first barrels 2024-05 -> 4 months.
      { permit_number: "0000001", issued_cycle: "2024-01", first_cycle: "2024-05", had_prior_production: false },
      // 2024-03 to 2025-03 -> 12 months.
      { permit_number: "0000002", issued_cycle: "2024-03", first_cycle: "2025-03", had_prior_production: false },
      // Permitted, still nothing filed: censored, counted, kept out of the median.
      { permit_number: "0000003", issued_cycle: "2025-06", first_cycle: null, had_prior_production: false },
      // An infill on a lease that never stopped producing: "next month" is an
      // artefact of lease-grain reporting and must not enter the median.
      { permit_number: "0000004", issued_cycle: "2024-01", first_cycle: "2024-02", had_prior_production: true },
    ];
    const r = await call("rrc_permit_cycle", { operator_no: "111111" });

    expect(r.permit_to_first_production.permits_linked).toBe(4);
    expect(r.permit_to_first_production.on_new_leases).toBe(3);
    expect(r.permit_to_first_production.measured).toBe(2);
    expect(r.permit_to_first_production.awaiting_production).toBe(1);
    // Median of {4, 12}, not of {1, 4, 12}.
    expect(r.permit_to_first_production.median_months).toBe(8);
    // Interpolated percentiles over the same two points, not their min and max.
    expect(r.permit_to_first_production.p10_months).toBeCloseTo(4.8, 10);
    expect(r.permit_to_first_production.p90_months).toBeCloseTo(11.2, 10);
    expect(r.notes.join(" ")).toMatch(/RIGHT-CENSORED/);
  });

  test("spud to completion comes back as days with its own sample", async () => {
    db.spudRow = { jobs: 1371, p10: 42, median_days: 120, p90: 1054, first: "2012-02", last: "2026-06" };
    const r = await call("rrc_permit_cycle", { county: "Reeves" });
    expect(r.spud_to_completion.median_days).toBe(120);
    expect(r.spud_to_completion.jobs).toBe(1371);
    const q = db.queries.find((x) => x.sql.includes("cmpl_or_recmpl_date"))!;
    expect(q.params).toContain("389");
  });

  test("refuses without a scope, and refuses a district that is not one", async () => {
    const bare = await call("rrc_permit_cycle", {});
    expect(bare.ok).toBe(false);
    expect(db.queries).toHaveLength(0);

    const bad = await call("rrc_permit_cycle", { district: "42" });
    expect(bad.ok).toBe(false);
    expect(bad.error).toMatch(/Not an RRC district/);
    expect(db.queries).toHaveLength(0);
  });
});

// --------------------------------------------------------------------- 34

describe("rrc_aggregate", () => {
  const base = { group_by: "operator", metric: "oil_bbl" };

  test("refuses an unfiltered statewide scan", async () => {
    const r = await call("rrc_aggregate", base);
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/county, district, operator_no, field_no/);
    // The refusal is not a query that came back empty.
    expect(db.queries).toHaveLength(0);
  });

  test("an existence filter alone does not count as narrowing", async () => {
    const r = await call("rrc_aggregate", { ...base, has_commercial_disposal: true });
    expect(r.ok).toBe(false);
    expect(db.queries).toHaveLength(0);
  });

  test("rejects an off-allowlist group_by or metric without issuing a query", async () => {
    const dim = await callRaw("rrc_aggregate", {
      ...base,
      group_by: "operator; drop table rrc.permit",
      county: "Reeves",
    });
    expect(dim.ok).toBe(false);
    expect(dim.error).toMatch(/Allowed: operator, field, county, district, lease/);
    expect(db.queries).toHaveLength(0);

    const met = await callRaw("rrc_aggregate", {
      ...base,
      metric: "(select version())",
      county: "Reeves",
    });
    expect(met.ok).toBe(false);
    expect(met.error).toMatch(/Allowed: oil_bbl, gas_mcf/);
    expect(db.queries).toHaveLength(0);
  });

  test("the Zod enum refuses the same names before the function is reached", () => {
    const shape = find("rrc_aggregate").args;
    expect(shape.safeParse({ group_by: "operator; --", metric: "oil_bbl" }).success).toBe(false);
    expect(shape.safeParse({ group_by: "operator", metric: "1;--" }).success).toBe(false);
  });

  test("formation is refused with what the mirror actually has", async () => {
    const r = await call("rrc_aggregate", { ...base, group_by: "formation", county: "Reeves" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/no formation/);
    expect(r.error).toMatch(/field/);
    expect(db.queries).toHaveLength(0);
  });

  test("never interpolates caller text into SQL: every value is a bound parameter", async () => {
    const INJECTION = "100852'; drop table rrc.permit; --";
    db.aggregateRows = [{ key: "100852", label: "ORACLE OIL", value: 42 }];

    const r = await call("rrc_aggregate", {
      group_by: "operator",
      metric: "boe",
      operator_no: INJECTION,
      county: "Reeves",
      district: "8A",
      field_no: "12345678",
      oil_gas_code: "O",
      permit_since: "2024-01-01",
      has_commercial_disposal: true,
      min_value: 1000,
      months: 24,
      limit: 5,
    });
    expect(r.ok).toBe(true);

    const q = db.queries.find((x) => x.sql.includes("rrc.county_lease_cycle"))!;
    expect(q).toBeTruthy();

    // Not one caller-supplied character reached the statement.
    for (const value of [INJECTION, "drop table", "REEVES", "12345678", "2024-01-01"]) {
      expect(q.sql).not.toContain(value);
    }
    // They all reached the parameter array instead, resolved where resolution
    // was due: "Reeves" as the county code, "8A" as its PDQ district.
    expect(q.params).toContain(INJECTION);
    expect(q.params).toContain("389");
    expect(q.params).toContain("11");
    expect(q.params).toContain("12345678");
    expect(q.params).toContain("O");
    expect(q.params).toContain("2024-01-01");
    expect(q.params).toContain(1000);

    // Every placeholder in the statement has a parameter behind it, and there
    // are no orphans either way.
    const markers = new Set([...q.sql.matchAll(/\$(\d+)/g)].map((m) => Number(m[1])));
    expect([...markers].sort((a, b) => a - b)).toEqual(
      q.params.map((_, i) => i + 1)
    );

    // The fragments that did make it are the allowlisted ones, verbatim.
    expect(q.sql).toContain("p.operator_no = $");
    expect(q.sql).toContain("p.county_no = $");
    expect(q.sql).toContain("rrc.uic_live_permit");
    expect(q.sql).toContain("group by 1");
  });

  test("the window is anchored on the reported edge, not on today", async () => {
    db.aggregateRows = [];
    const r = await call("rrc_aggregate", {
      ...base,
      county: "Reeves",
      months: 12,
    });
    expect(r.window).toEqual({ from: "2025-06", through: "2026-05" });
    const q = db.queries.find((x) => x.sql.includes("rrc.county_lease_cycle"))!;
    expect(q.params).toContain("2026-05-01");
    expect(q.params).toContain(12);
    expect(q.sql).not.toContain("now()");
  });

  test("marks truncation rather than implying the list is everything", async () => {
    db.aggregateRows = Array.from({ length: 4 }, (_, i) => ({
      key: `k${i}`,
      label: `L${i}`,
      value: 10 - i,
    }));
    const r = await call("rrc_aggregate", { ...base, county: "Reeves", limit: 3 });
    expect(r.groups).toHaveLength(3);
    expect(r.truncated).toBe(true);

    // One more row than the limit is what the query asked for, which is how
    // truncation is known without a second count.
    const q = db.queries.find((x) => x.sql.includes("rrc.county_lease_cycle"))!;
    expect(q.params.at(-1)).toBe(4);
  });

  test("an unresolvable county is a refusal, not an empty result", async () => {
    const r = await call("rrc_aggregate", { ...base, county: "Nottingham" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/Not a Texas county/);
    expect(db.queries).toHaveLength(0);
  });
});
