import { beforeEach, describe, expect, test, vi } from "vitest";

/**
 * The allowable, ending-balance and disposition tools.
 *
 * The mirror is mocked and every expected number in this file was computed by
 * hand from the fixture above it, never by running the tool and copying what it
 * said. What these check is the four ways this file can be wrong while still
 * returning a well-shaped answer:
 *
 *   - A NULL ALLOWABLE silently becoming zero (invents a shut-in and a negative
 *     headroom) or infinity (invents room that is not there).
 *   - A TREND fitted through the wrong months, or with its sign inverted.
 *   - A DISPOSITION CODE total that does not add up to the fixture.
 *   - `rrc_infill_capacity` quietly answering from columns that do not exist.
 */

const db = vi.hoisted(() => ({
  calls: [] as { sql: string; params: unknown[] }[],
  positions: [] as Record<string, unknown>[],
  regulatory: [] as Record<string, unknown>[],
  leaseProduction: [] as Record<string, unknown>[],
}));

const q = vi.hoisted(() => ({
  edge: { reported: "2026-05", loaded: "2026-08" },
  lease: null as unknown,
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string, params: unknown[]) => {
    db.calls.push({ sql, params });
    if (sql.includes("produced_when_allowed")) return db.positions;
    if (sql.includes("rrc.regulatory_lease")) return db.regulatory;
    if (sql.includes("rrc.lease_production")) return db.leaseProduction;
    throw new Error(`unexpected query: ${sql.slice(0, 80)}`);
  },
  rrcQueryOne: async () => null,
  rrcQuerySlow: async () => [],
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getCycleEdge: async () => q.edge,
  getLeaseDossier: async () => q.lease,
  getOperatorDisposition: async () => ({ oil: [], gas: [], cond: [], csgd: [] }),
  getOperatorDossier: async () => null,
  getOperatorNetwork: async () => null,
  getPendingQueue: async () => [],
  listPermits: async () => [],
  // Reached only through `resolveSeries` for entities these tests do not use.
  getCountyProfile: async () => null,
  getFieldProfile: async () => null,
  getProductionTrend: async () => [],
  getWellDossier: async () => null,
}));

const { TOOLS } = await import("./production");

// The tools return `unknown` on purpose: a model reads them, not TypeScript.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Result = any;

/** Look up, validate, run: the same three steps `runRrcAnalysis` takes. */
async function call(name: string, args: Record<string, unknown>): Promise<Result> {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`no tool named ${name}. Have: ${TOOLS.map((t) => t.name).join(", ")}`);
  const parsed = tool.args.safeParse(args);
  if (!parsed.success) throw new Error(`bad args for ${name}: ${parsed.error.message}`);
  return (await tool.run(parsed.data as never)) as Result;
}

/** A lease-month with everything absent unless the fixture states it. */
function month(cycle: string, over: Record<string, unknown> = {}) {
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
    prod_report_filed: "Y" as const,
    reported: true,
    ...over,
  };
}

function dossier(over: Record<string, unknown> = {}) {
  return {
    oil_gas_code: "O",
    district_no: "08",
    lease_no: "12345",
    lease_name: "CHARGER 110",
    field_no: "12345678",
    field_name: "SPRABERRY (TREND AREA)",
    off_schedule: false,
    severance: false,
    monthly: [],
    disposition: { oil: [], gas: [], cond: [], csgd: [] },
    counties: [],
    wells: [],
    p4: { connections: [], filings: [] },
    ...over,
  };
}

/** One row as `leasePositions` selects it, before the key is attached. */
function position(over: Record<string, unknown> = {}) {
  return {
    oil_gas_code: "O",
    district_no: "08",
    lease_no: "00001",
    lease_name: null,
    field_no: null,
    field_name: null,
    months: 12,
    produced: 0,
    produced_when_allowed: 0,
    allowable: null,
    allowable_months: 0,
    disposed: 0,
    balance_first: null,
    balance_last: null,
    ...over,
  };
}

const LEASE = { entity: "lease", oil_gas_code: "O", district_no: "08", lease_no: "12345" };

beforeEach(() => {
  db.calls = [];
  db.positions = [];
  db.regulatory = [];
  db.leaseProduction = [];
  q.edge = { reported: "2026-05", loaded: "2026-08" };
  q.lease = null;
});

// -------------------------------------------------------------------- 74

describe("rrc_allowable_headroom", () => {
  /*
   * THE ORACLE, computed by hand from this fixture:
   *
   *   2026-01  produced 3000  allowable 4500  ->  headroom  1500, util 0.6666..
   *   2026-02  produced 2000  allowable null  ->  headroom  null, util null
   *   2026-03  produced 5000  allowable 5000  ->  headroom     0, util 1
   *   2026-07  produced    0                  ->  unreported, dropped
   *
   *   filed months in window        3
   *   months with a ceiling         2
   *   total allowable        4500 + 5000 = 9500
   *   produced when allowed  3000 + 5000 = 8000   (NOT 10000: the null month
   *                                                 has nothing to compare to)
   *   total headroom         9500 - 8000 = 1500
   *   utilisation            8000 / 9500 = 0.842105263157894...
   */
  const monthly = [
    month("2026-01", { oil_prod_vol: 3000, oil_allow: 4500 }),
    month("2026-02", { oil_prod_vol: 2000, oil_allow: null }),
    month("2026-03", { oil_prod_vol: 5000, oil_allow: 5000 }),
    month("2026-07", { reported: false }),
  ];

  test("headroom is allowable minus actual, per month and summed", async () => {
    q.lease = dossier({ monthly });
    const r = await call("rrc_allowable_headroom", LEASE);

    expect(r.ok).toBe(true);
    expect(r.filed_months).toBe(3);
    expect(r.months_with_ceiling).toBe(2);
    expect(r.total_allowable).toBe(9500);
    expect(r.total_produced_when_allowed).toBe(8000);
    expect(r.total_headroom).toBe(1500);
    expect(r.utilisation).toBeCloseTo(8000 / 9500, 12);

    expect(r.series[0]).toMatchObject({ cycle: "2026-01", produced: 3000, allowable: 4500, headroom: 1500 });
    expect(r.series[0].utilisation).toBeCloseTo(3000 / 4500, 12);
    // At the ceiling: zero headroom is a number, not a missing one.
    expect(r.series[2]).toMatchObject({ cycle: "2026-03", headroom: 0, utilisation: 1 });
    expect(r.latest.cycle).toBe("2026-03");
  });

  test("a null allowable is neither zero nor unlimited", async () => {
    q.lease = dossier({ monthly });
    const r = await call("rrc_allowable_headroom", LEASE);

    const nullMonth = r.series.find((s: Result) => s.cycle === "2026-02");
    expect(nullMonth.allowable).toBeNull();
    // Not zero: zero would make headroom -2000 and utilisation infinite.
    expect(nullMonth.headroom).toBeNull();
    expect(nullMonth.utilisation).toBeNull();
    // Its production is still reported, so the month is not simply discarded.
    expect(nullMonth.produced).toBe(2000);

    // Read as zero, the totals would be 9500 allowable against 10000 produced,
    // i.e. -500 of headroom and a lease apparently over its ceiling.
    expect(r.total_headroom).toBe(1500);
    expect(r.total_headroom).not.toBe(-500);
    expect(r.total_produced_when_allowed).not.toBe(10000);
    // Read as unlimited, nothing would be finite.
    expect(Number.isFinite(r.total_allowable)).toBe(true);
    expect(r.months_without_ceiling).toBe(1);
  });

  test("the unreported tail never reaches the arithmetic", async () => {
    q.lease = dossier({
      monthly: [...monthly, month("2026-06", { oil_allow: 5000, reported: false })],
    });
    const r = await call("rrc_allowable_headroom", LEASE);
    // 2026-06 states a 5000 ceiling against an unfiled zero. Counted, it would
    // add 5000 of phantom headroom.
    expect(r.total_headroom).toBe(1500);
    expect(r.series.some((s: Result) => s.cycle === "2026-06")).toBe(false);
  });

  test("a month the operator did not file is not zero production", async () => {
    q.lease = dossier({
      monthly: [
        ...monthly,
        month("2026-04", { oil_prod_vol: 0, oil_allow: 5000, prod_report_filed: "N" }),
      ],
    });
    const r = await call("rrc_allowable_headroom", LEASE);
    expect(r.filed_months).toBe(3);
    expect(r.total_headroom).toBe(1500);
  });

  test("geographic rollups are refused, not answered with nulls", async () => {
    const r = await call("rrc_allowable_headroom", { entity: "county", county: "MIDLAND" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("lease grain");
  });

  test("operator scope ranks leases by the room each has left", async () => {
    /*
     * ORACLE:
     *   ALPHA  allowable 5000, produced-when-allowed 1000 -> headroom 4000, util 0.2
     *   BRAVO  allowable 4000, produced-when-allowed 4000 -> headroom    0, util 1.0
     *   CHARLIE no ceiling stated                          -> held out entirely
     *
     *   total allowable 9000, total produced 5000, total headroom 4000
     */
    db.positions = [
      position({ lease_no: "1", lease_name: "ALPHA", produced: 1000, produced_when_allowed: 1000, allowable: 5000, allowable_months: 12 }),
      position({ lease_no: "2", lease_name: "BRAVO", produced: 4000, produced_when_allowed: 4000, allowable: 4000, allowable_months: 12 }),
      position({ lease_no: "3", lease_name: "CHARLIE", produced: 9000, allowable: null }),
    ];
    const r = await call("rrc_allowable_headroom", { entity: "operator", operator_no: "123456" });

    expect(r.leases).toBe(3);
    expect(r.leases_with_ceiling).toBe(2);
    expect(r.total_allowable).toBe(9000);
    expect(r.total_produced_when_allowed).toBe(5000);
    expect(r.total_headroom).toBe(4000);
    expect(r.ranked.map((x: Result) => x.lease_name)).toEqual(["ALPHA", "BRAVO"]);
    expect(r.ranked[0].headroom).toBe(4000);
    expect(r.ranked[0].utilisation).toBeCloseTo(0.2, 12);
    expect(r.at_ceiling).toBe(1);
    // CHARLIE's 9000 barrels are real and its room is unknown. Folding it in at
    // zero use would have added 9000 of headroom that nobody can verify.
    expect(r.leases_without_ceiling).toEqual([
      { key: "O/08/3", lease_name: "CHARLIE", produced: 9000 },
    ]);
  });

  test("the operator read is bounded to the reported edge and a row cap", async () => {
    db.positions = [];
    await call("rrc_allowable_headroom", { entity: "operator", operator_no: "123456", months: 12 });
    const sql = db.calls[0].sql;
    expect(sql).toContain("operator_no = $1");
    expect(sql).toContain("interval '12 months'");
    expect(sql).toContain("limit $3");
    expect(db.calls[0].params).toEqual(["123456", "2026-05", 50]);
  });
});

// -------------------------------------------------------------------- 75

describe("rrc_choke_detect", () => {
  /*
   * ORACLE, three leases at a 0.75 threshold:
   *
   *   ALPHA   1000 / 5000 = 0.20 under. Disposed 400 of 1000 produced, and the
   *           ending balance went 100 -> 700. Made it, did not sell it:
   *           stock_building, headroom 4000.
   *   BRAVO   2000 / 4000 = 0.50 under. Disposed 2000 of 2000. Sold everything
   *           and still short: constraint_upstream_of_the_tank, headroom 2000.
   *   CHARLIE 4000 / 4000 = 1.00. Not under the threshold at all.
   */
  beforeEach(() => {
    db.positions = [
      position({ lease_no: "1", lease_name: "ALPHA", produced: 1000, produced_when_allowed: 1000, allowable: 5000, allowable_months: 12, disposed: 400, balance_first: 100, balance_last: 700 }),
      position({ lease_no: "2", lease_name: "BRAVO", produced: 2000, produced_when_allowed: 2000, allowable: 4000, allowable_months: 12, disposed: 2000, balance_first: 50, balance_last: 50 }),
      position({ lease_no: "3", lease_name: "CHARLIE", produced: 4000, produced_when_allowed: 4000, allowable: 4000, allowable_months: 12, disposed: 4000 }),
    ];
  });

  test("separates product made and not sold from product sold in full", async () => {
    const r = await call("rrc_choke_detect", { operator_no: "123456" });

    expect(r.leases_with_ceiling).toBe(3);
    expect(r.leases_under_threshold).toBe(2);
    expect(r.stock_building).toBe(1);
    expect(r.constraint_upstream_of_the_tank).toBe(1);
    expect(r.indeterminate).toBe(0);

    const [first, second] = r.leases_detail;
    expect(first).toMatchObject({
      lease_name: "ALPHA",
      headroom: 4000,
      undisposed: 600,
      balance_change: 600,
      verdict: "stock_building",
    });
    expect(first.utilisation).toBeCloseTo(0.2, 12);
    expect(second).toMatchObject({
      lease_name: "BRAVO",
      headroom: 2000,
      undisposed: 0,
      verdict: "constraint_upstream_of_the_tank",
    });
    expect(r.leases_detail.some((l: Result) => l.lease_name === "CHARLIE")).toBe(false);
  });

  test("gas cannot reach a stock verdict, and says so", async () => {
    // The fixture still carries ALPHA's rising balance, which the real gas
    // query can never return. The verdict must come from the stream, not from
    // whatever numbers happen to arrive: gas is not stored on the lease.
    const r = await call("rrc_choke_detect", { operator_no: "123456", stream: "gas" });
    expect(r.stock_test_available).toBe(false);
    expect(r.stock_building).toBe(0);
    expect(r.notes.join(" ")).toContain("no ending balance");
  });

  test("an unfiltered scan is refused", async () => {
    const r = await call("rrc_choke_detect", {});
    expect(r.ok).toBe(false);
    expect(r.error).toContain("operator_no or district_no");
  });
});

// -------------------------------------------------------------------- 76

describe("rrc_inventory_signal", () => {
  /*
   * ORACLE on a straight rising series, balances 1000/2000/3000/4000 over four
   * months with 3000 bbl produced and 2000 disposed each month:
   *
   *   mean x 1.5, mean y 2500
   *   Sxy = (-1.5)(-1500) + (-0.5)(-500) + (0.5)(500) + (1.5)(1500) = 5000
   *   Sxx = 2.25 + 0.25 + 0.25 + 2.25                               = 5
   *   slope = 5000 / 5 = 1000 per month, r2 = 1 (the points are collinear)
   *   direction "rising", change 4000 - 1000 = 3000
   *   slope share 1000 / 2500 = 0.4
   *   days of production held = 4000 / (3000 / 30.4375) = 40.5833...
   *   undisposed over the window = 4 * 3000 - 4 * 2000 = 4000
   */
  const rising = ["2026-01", "2026-02", "2026-03", "2026-04"].map((c, i) =>
    month(c, { oil_prod_vol: 3000, oil_tot_disp: 2000, oil_ending_bal: 1000 * (i + 1) })
  );

  test("a rising ending balance reads as rising, with the right slope", async () => {
    q.lease = dossier({ monthly: rising });
    const r = await call("rrc_inventory_signal", LEASE);

    expect(r.months_with_balance).toBe(4);
    expect(r.direction).toBe("rising");
    expect(r.slope_per_month).toBeCloseTo(1000, 9);
    expect(r.r2).toBeCloseTo(1, 12);
    expect(r.first_balance).toBe(1000);
    expect(r.latest_balance).toBe(4000);
    expect(r.change).toBe(3000);
    expect(r.slope_share_per_month).toBeCloseTo(0.4, 12);
    expect(r.latest_days_of_production).toBeCloseTo((4000 * 30.4375) / 3000, 9);
    expect(r.undisposed_in_window).toBe(4000);
  });

  test("the same series reversed reads as falling", async () => {
    q.lease = dossier({
      monthly: ["2026-01", "2026-02", "2026-03", "2026-04"].map((c, i) =>
        month(c, { oil_prod_vol: 3000, oil_ending_bal: 4000 - 1000 * i })
      ),
    });
    const r = await call("rrc_inventory_signal", LEASE);
    expect(r.direction).toBe("falling");
    expect(r.slope_per_month).toBeCloseTo(-1000, 9);
    expect(r.change).toBe(-3000);
  });

  test("months with no stated balance are not fitted as zero", async () => {
    q.lease = dossier({
      monthly: [
        month("2026-01", { oil_prod_vol: 3000, oil_ending_bal: 1000 }),
        month("2026-02", { oil_prod_vol: 3000, oil_ending_bal: null }),
        month("2026-03", { oil_prod_vol: 3000, oil_ending_bal: 2000 }),
      ],
    });
    const r = await call("rrc_inventory_signal", LEASE);
    expect(r.months_in_window).toBe(3);
    expect(r.months_with_balance).toBe(2);
    // Two stated points one index apart: slope 1000. A null read as zero would
    // fit 1000/0/2000 and give slope 500 with the middle month dragging it.
    expect(r.slope_per_month).toBeCloseTo(1000, 9);
    expect(r.direction).toBe("rising");
  });

  test("one stated balance is no trend at all", async () => {
    q.lease = dossier({ monthly: [month("2026-01", { oil_ending_bal: 1000 })] });
    const r = await call("rrc_inventory_signal", LEASE);
    expect(r.direction).toBeNull();
    expect(r.slope_per_month).toBeNull();
  });

  test("gas has no ending balance, so it is refused", async () => {
    const r = await call("rrc_inventory_signal", { ...LEASE, entity: "operator", operator_no: "1" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("lease grain");
  });
});

// -------------------------------------------------------------------- 77

describe("rrc_flare_map", () => {
  /*
   * ORACLE, added up by hand from the two months below:
   *
   *   code 01: 100 + 150 =  250
   *   code 03: 400 + 350 =  750
   *   code 05:  25 +  75 =  100
   *   grand total        = 1100
   *   ranked by volume   : 03, 01, 05
   */
  const csgd = [
    { cycle: "2026-01", codes: { "01": 100, "03": 400, "05": 25 } },
    { cycle: "2026-02", codes: { "01": 150, "03": 350, "05": 75 } },
  ];

  test("per-code totals match the fixture", async () => {
    q.lease = dossier({ disposition: { oil: [], gas: [], cond: [], csgd } });
    const r = await call("rrc_flare_map", { oil_gas_code: "O", district_no: "08", lease_no: "12345" });

    expect(r.total_volume).toBe(1100);
    expect(r.by_code).toEqual([
      { code: "03", volume: 750, share: 750 / 1100 },
      { code: "01", volume: 250, share: 250 / 1100 },
      { code: "05", volume: 100, share: 100 / 1100 },
    ]);
  });

  test("nothing is classified until the caller names the codes", async () => {
    q.lease = dossier({ disposition: { oil: [], gas: [], cond: [], csgd } });
    const r = await call("rrc_flare_map", { oil_gas_code: "O", district_no: "08", lease_no: "12345" });

    // The documented default is the EMPTY set: the mirror carries no code
    // labels, so the tool refuses to guess which code means vented or flared.
    expect(r.selected_codes).toEqual([]);
    expect(r.selected_volume).toBeNull();
    expect(r.selected_share).toBeNull();
    expect(r.selected_series).toEqual([]);
    expect(r.notes.join(" ")).toContain("No vent/flare code set was supplied");
    // No code anywhere in the result is given a name.
    expect(JSON.stringify(r)).not.toMatch(/"vented"|"flared"/);
  });

  test("a caller-supplied code set is subtotalled and echoed back", async () => {
    q.lease = dossier({ disposition: { oil: [], gas: [], cond: [], csgd } });
    const r = await call("rrc_flare_map", {
      oil_gas_code: "O",
      district_no: "08",
      lease_no: "12345",
      vent_flare_codes: ["05", "77"],
    });

    expect(r.selected_codes).toEqual(["05", "77"]);
    // 25 + 75 = 100 for code 05; code 77 is absent and contributes nothing.
    expect(r.selected_volume).toBe(100);
    expect(r.selected_share).toBeCloseTo(100 / 1100, 12);
    expect(r.selected_codes_absent).toEqual(["77"]);
    expect(r.selected_series).toEqual([
      { cycle: "2026-01", volume: 25 },
      { cycle: "2026-02", volume: 75 },
    ]);
  });

  test("area-wide disposition is refused with the reason", async () => {
    const r = await call("rrc_flare_map", { district_no: "08" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("48.5M rows");
  });
});

// -------------------------------------------------------------------- 78

describe("rrc_gas_orphan", () => {
  test("casinghead made, none disposed, no P-4 taker", async () => {
    // 600 + 400 produced, 0 disposed. The whole 1000 has no reported route.
    q.lease = dossier({
      monthly: [
        month("2026-01", { csgd_prod_vol: 600, csgd_tot_disp: null }),
        month("2026-02", { csgd_prod_vol: 400, csgd_tot_disp: null }),
      ],
      p4: { connections: [{ product_code: "O", type_code: "H", operator_name: "BUYER" }], filings: [] },
    });
    const r = await call("rrc_gas_orphan", { oil_gas_code: "O", district_no: "08", lease_no: "12345" });

    expect(r.csgd_produced).toBe(1000);
    expect(r.csgd_disposed).toBe(0);
    expect(r.undisposed).toBe(1000);
    expect(r.undisposed_share).toBe(1);
    expect(r.p4_casinghead_takers).toEqual([]);
    expect(r.orphan).toBe(true);
  });

  test("a full-well-stream connection counts as a taker", async () => {
    q.lease = dossier({
      monthly: [month("2026-01", { csgd_prod_vol: 600, csgd_tot_disp: 600 })],
      p4: { connections: [{ product_code: "F", type_code: "G", operator_name: "GATHERER" }], filings: [] },
    });
    const r = await call("rrc_gas_orphan", { oil_gas_code: "O", district_no: "08", lease_no: "12345" });
    expect(r.p4_casinghead_takers).toHaveLength(1);
    expect(r.orphan).toBe(false);
    expect(r.undisposed).toBe(0);
  });

  test("operator scope ranks leases by the gas with no reported route", async () => {
    db.positions = [
      position({ lease_no: "1", lease_name: "ALPHA", produced: 1000, disposed: 0 }),
      position({ lease_no: "2", lease_name: "BRAVO", produced: 5000, disposed: 4500 }),
      position({ lease_no: "3", lease_name: "CHARLIE", produced: 800, disposed: 800 }),
    ];
    const r = await call("rrc_gas_orphan", { operator_no: "123456" });
    expect(r.leases_producing_casinghead).toBe(3);
    expect(r.leases_with_undisposed_casinghead).toBe(2);
    expect(r.total_undisposed).toBe(1500);
    expect(r.leases_detail.map((l: Result) => l.lease_name)).toEqual(["ALPHA", "BRAVO"]);
    expect(r.leases_detail[1].undisposed).toBe(500);
  });
});

// -------------------------------------------------------------------- 88

describe("rrc_infill_capacity", () => {
  test("refuses, and names exactly which columns do not exist", async () => {
    const r = await call("rrc_infill_capacity", { field_no: "12345678" });

    expect(r.ok).toBe(false);
    // The verified fact: rrc.field is field_no, field_name, district_no and
    // nothing else, so there is no spacing or density rule to read.
    expect(r.missing[0]).toContain("field_no, field_name, district_no");
    expect(r.missing.join(" ")).toContain("SWR 37");
    expect(r.missing.join(" ")).toContain("SWR 38");
    expect(r.would_need).toContain("field rules");
    // It must not have quietly answered from a permit applicant's assertion.
    expect(r.wells_remaining).toBeUndefined();
    expect(db.calls).toHaveLength(0);
  });
});

// -------------------------------------------------------------------- 89

describe("rrc_severance_watch", () => {
  test("severed leases carry the production and the barrels in the tank", async () => {
    db.regulatory = [
      { oil_gas_code: "O", district_no: "08", lease_no: "1", lease_name: "ALPHA", field_name: null, operator_no: "123456", operator_name: "OP", severance: true, off_schedule: false },
      { oil_gas_code: "O", district_no: "08", lease_no: "2", lease_name: "BRAVO", field_name: null, operator_no: "123456", operator_name: "OP", severance: true, off_schedule: true },
    ];
    db.leaseProduction = [
      { oil_gas_code: "O", district_no: "08", lease_no: "1", oil: 12000, gas: 400, oil_ending_bal: 900, last_cycle: "2026-05" },
      { oil_gas_code: "O", district_no: "08", lease_no: "2", oil: 3000, gas: 0, oil_ending_bal: 100, last_cycle: "2026-04" },
    ];
    const r = await call("rrc_severance_watch", { operator_no: "123456" });

    expect(r.leases).toBe(2);
    expect(r.severed).toBe(2);
    expect(r.severed_oil_last_window).toBe(15000);
    expect(r.severed_oil_in_tank).toBe(1000);
    // Ranked by the production now stranded.
    expect(r.leases_detail[0].lease_name).toBe("ALPHA");
    // Off schedule is opt-in: the default query asks for severance only.
    expect(db.calls[0].sql).toContain("lease_severance_flag = 'Y'");
    expect(db.calls[0].sql).not.toContain("lease_off_sched_flag = 'Y')");
  });

  test("off schedule is only included when asked for", async () => {
    db.regulatory = [];
    await call("rrc_severance_watch", { operator_no: "123456", include_off_schedule: true });
    expect(db.calls[0].sql).toContain("lease_off_sched_flag = 'Y'");
  });

  test("an unfiltered scan is refused", async () => {
    const r = await call("rrc_severance_watch", {});
    expect(r.ok).toBe(false);
    expect(db.calls).toHaveLength(0);
  });
});

// -------------------------------------------------------------------- 90 / 91

describe("the composed intel tools", () => {
  test("counter intel says so plainly when an operator has never filed", async () => {
    const r = await call("rrc_counter_intel", { operator_no: "123456" });
    expect(r.ok).toBe(true);
    expect(r.permits_in_window).toBe(0);
    expect(r.notes.join(" ")).toContain("No approved drilling permit");
  });

  test("order of battle refuses an operator number the mirror does not have", async () => {
    const r = await call("rrc_order_of_battle", { operator_no: "999999" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("999999");
  });
});

// ------------------------------------------------------------------ catalog

describe("the catalog", () => {
  test("all nine tools are registered under their spec names", () => {
    expect(TOOLS.map((t) => t.name)).toEqual([
      "rrc_allowable_headroom",
      "rrc_choke_detect",
      "rrc_inventory_signal",
      "rrc_flare_map",
      "rrc_gas_orphan",
      "rrc_infill_capacity",
      "rrc_severance_watch",
      "rrc_counter_intel",
      "rrc_order_of_battle",
    ]);
  });

  test("no summary names a disposition code", () => {
    for (const t of TOOLS) {
      expect(t.summary.toLowerCase()).not.toMatch(/\bcode 0\d\b/);
      expect(t.summary.length).toBeLessThan(220);
    }
  });
});
