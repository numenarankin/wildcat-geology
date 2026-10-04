/* eslint-disable @typescript-eslint/no-explicit-any */
import { beforeEach, describe, expect, test, vi } from "vitest";

/**
 * The acquisition screening catalog, against fixtures whose right answer is
 * known before the code runs.
 *
 * Every expected value below is derived from the record the fixture states, by
 * hand, and never read off a run. What these guard is not the SQL text but the
 * six ways these tools mislead while still returning a clean-looking object:
 *
 *  1. A DOLLAR FIGURE. The RRC publishes no price, cost or consideration, so a
 *     number in these results that reads as money is fabricated by definition.
 *     `no tool emits money` walks every number in a rich result from all
 *     thirteen tools and fails on a key that names one.
 *  2. AN UNFILTERED SCAN. `rrc.lease_production` is 78.6M rows behind a 5 s
 *     timeout, so a screen with no narrowing filter must refuse rather than
 *     attempt, and a refusal is a value, not a throw.
 *  3. A COMPOSITE THAT CANNOT BE REBUILT. The distress weights are asserted,
 *     not fitted, so the score is only defensible if the components are on the
 *     result and the arithmetic between them is the stated one.
 *  4. A TRANSFER THAT NEVER HAPPENED. The P-4 chg_operator flag is set on
 *     plenty of filings naming the same operator as the one before, and reading
 *     the flag rather than the operator turns paperwork into a deal.
 *  5. A RATE OVER THE WRONG DENOMINATOR. A twelve-cycle window is 365 or 366
 *     calendar days depending on where it sits, not twelve times thirty.
 *  6. DATE ARITHMETIC. An obligation calendar is nothing but date arithmetic,
 *     so it is computed here from a calendar counted by hand.
 */

// --------------------------------------------------------------- fixtures

/**
 * Days per calendar month, written out rather than computed, so the day counts
 * this test divides by are independent of the ones the code divides by.
 */
const DAYS: Record<string, number> = {
  "01": 31, "02": 28, "03": 31, "04": 30, "05": 31, "06": 30,
  "07": 31, "08": 31, "09": 30, "10": 31, "11": 30, "12": 31,
};
const days = (cycle: string) =>
  cycle.endsWith("-02") && Number(cycle.slice(0, 4)) % 4 === 0 ? 29 : DAYS[cycle.slice(5, 7)];

function cycles(start: string, n: number): string[] {
  const [y, m] = start.split("-").map(Number);
  return Array.from({ length: n }, (_, i) => {
    const t = y * 12 + (m - 1) + i;
    return `${Math.floor(t / 12)}-${String((t % 12) + 1).padStart(2, "0")}`;
  });
}

/** The published edge for every fixture here. */
const EDGE = "2025-06";

/**
 * The window `rrc_acquisition_screen` uses at months = 12 and edge 2025-06 is
 * 2024-07 through 2025-06. Counted by hand off the table above:
 *   Jul 31, Aug 31, Sep 30, Oct 31, Nov 30, Dec 31 = 184
 *   Jan 31, Feb 28, Mar 31, Apr 30, May 31, Jun 30 = 181
 */
const WINDOW_DAYS = 365;

/**
 * A lease on a clean exponential decline: 100 bbl/d falling 3% per month.
 * Volumes are the daily rate times the month's own length, so the code's
 * conversion back to a rate has to undo exactly this.
 */
function decliningLease(start: string, n: number) {
  return cycles(start, n).map((cycle, i) => {
    const rate = 100 * Math.pow(0.97, i);
    return {
      cycle,
      oil: Math.round(rate * days(cycle)),
      gas: Math.round(rate * 2 * days(cycle)),
      cond: 0,
      csgd: 0,
    };
  });
}

const db = vi.hoisted(() => ({
  calls: [] as { sql: string; params: unknown[] }[],
  leaseCandidates: [] as Record<string, unknown>[],
  scopeOperators: [] as Record<string, unknown>[],
  leaseWellCounts: [] as Record<string, unknown>[],
  leaseFlags: [] as Record<string, unknown>[],
  fleets: [] as Record<string, unknown>[],
  operators: [] as Record<string, unknown>[],
  operatorProduction: [] as Record<string, unknown>[],
  operatorLeaseKeys: [] as Record<string, unknown>[],
  leaseCounts: [] as Record<string, unknown>[],
  permitCounts: [] as Record<string, unknown>[],
  permitExpiry: [] as Record<string, unknown>[],
  statePlugs: [] as Record<string, unknown>[],
  h15Position: [] as Record<string, unknown>[],
  h15PositionPrior: [] as Record<string, unknown>[],
  h15Latest: [] as Record<string, unknown>[],
  h15Delinquent: [] as Record<string, unknown>[],
  idleWells: [] as Record<string, unknown>[],
  pluggedWells: [] as Record<string, unknown>[],
  plugSummary: [] as Record<string, unknown>[],
  perfs: [] as Record<string, unknown>[],
  formations: [] as Record<string, unknown>[],
  boltOn: [] as Record<string, unknown>[],
  officers: [] as Record<string, unknown>[],
  w10: [] as Record<string, unknown>[],
  uicPermits: [] as Record<string, unknown>[],
  liabilityReasons: [] as Record<string, unknown>[],
  liabilityIdle: [] as Record<string, unknown>[],
  sellerFlagged: [] as Record<string, unknown>[],
  sellerStatePlugs: [] as Record<string, unknown>[],
  unfiledMonths: [] as Record<string, unknown>[],
  uncoded: [] as Record<string, unknown>[],
  depth: [] as Record<string, unknown>[],
  obligationInactive: [] as Record<string, unknown>[],
  /** Lease series keyed "O/08/12345". */
  series: new Map<string, Record<string, unknown>[]>(),
}));

/**
 * The router matches on fragments that appear in exactly one query, and throws
 * on anything unmatched: a fixture silently answering the wrong read is the one
 * failure mode a mocked database has that a real one does not.
 */
vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string, params: unknown[] = []) => {
    db.calls.push({ sql, params });
    const s = sql;
    if (s.includes("prod_report_filed = 'N'")) return db.unfiledMonths;
    if (s.includes("count(distinct lease_no) filter")) return db.leaseCounts;
    if (s.includes("select distinct oil_gas_code, district_no, lease_no")) {
      return db.operatorLeaseKeys;
    }
    if (s.includes("from rrc.lease_production")) {
      return db.series.get(`${params[0]}/${params[1]}/${params[2]}`) ?? [];
    }
    if (s.includes("from rrc.operator_production")) return db.operatorProduction;
    if (s.includes("with mine as")) return db.boltOn;
    if (s.includes("from rrc.county_lease_cycle")) {
      return s.includes("select p.operator_no") ? db.scopeOperators : db.leaseCandidates;
    }
    if (s.includes("from rrc.regulatory_lease")) return db.leaseFlags;
    if (s.includes("from rrc.wb_plug_summary")) return db.plugSummary;
    if (s.includes("from rrc.wb_perf")) return db.perfs;
    if (s.includes("completion_formation")) return db.formations;
    if (s.includes("with latest as")) {
      // Two calls, the second anchored a year earlier. The date parameter is
      // the only thing separating them, which is the point of the pair.
      return String(params[1]).startsWith("2025") ? db.h15Position : db.h15PositionPrior;
    }
    if (s.includes("from rrc.wb_h15")) {
      return s.includes("status = 'D'") ? db.h15Delinquent : db.h15Latest;
    }
    if (s.includes("from rrc.operator_officers")) {
      // The name arm looks up by EQUALITY against what the resolver returned.
      // Applying that predicate here rather than ignoring it is what keeps the
      // fixture the single source of truth: a tool that quietly widened its
      // filter back to a wildcard would still pass against a mock that returns
      // every officer whatever it was asked for.
      if (s.includes("officer_name = any($1)")) {
        const wanted = new Set((params[0] as string[]) ?? []);
        return db.officers.filter((o) => wanted.has(String(o.officer_name)));
      }
      return db.officers;
    }
    if (s.includes("from rrc.operators")) return db.operators;
    if (s.includes("from rrc.permit")) {
      return s.includes("expires_date between") ? db.permitExpiry : db.permitCounts;
    }
    if (s.includes("from rrc.uic_live_permit")) return db.uicPermits;
    if (s.includes("from rrc.w10_test")) return db.w10;
    if (s.includes("state_funded_plug_no is not null")) {
      return s.includes("p.total_depth") ? db.sellerStatePlugs : db.statePlugs;
    }
    if (s.includes("from rrc.wellbore")) {
      if (s.includes("array_remove(array[")) return db.sellerFlagged;
      if (s.includes("as pollution")) return db.liabilityReasons;
      if (s.includes("left join rrc.well_location")) return db.uncoded;
      if (s.includes("sum(nullif(api_depth, '')::bigint)")) return db.depth;
      if (s.includes("as flagged,")) return db.fleets;
      if (s.includes("unnest")) return db.leaseWellCounts;
      if (s.includes("w.curr_inact_yrs")) return db.idleWells;
      if (s.includes("w.api_depth")) return db.pluggedWells;
      if (s.includes("::int, 0) * 12")) return db.obligationInactive;
      if (s.includes("curr_inact_yrs")) return db.liabilityIdle;
    }
    throw new Error(`unrouted query: ${s.replace(/\s+/g, " ").slice(0, 120)}`);
  },
  rrcQueryOne: async (sql: string) => {
    throw new Error(`unexpected rrcQueryOne: ${sql.slice(0, 60)}`);
  },
}));

const q = vi.hoisted(() => ({
  p4: new Map<string, { connections: unknown[]; filings: unknown[] }>(),
  operatorH15: { wellsTested: 0, delinquent: 0, dueSoon: 0, lastTest: null as string | null },
  operatorDisposal: {
    wells: 0,
    commercialWells: 0,
    permittedBblPerDay: null as number | null,
    injectedBbl12m: null as number | null,
    lastReported: null as string | null,
    reportedThrough: "2024-08",
  },
  disposal: [] as Record<string, unknown>[],
  network: null as Record<string, unknown> | null,
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getCycleEdge: async () => ({ reported: EDGE, loaded: "2025-09" }),
  getLeaseP4: async (o: string, d: string, l: string) =>
    q.p4.get(`${o}/${d}/${l}`) ?? { connections: [], filings: [] },
  getOperatorH15: async () => q.operatorH15,
  getOperatorDisposal: async () => q.operatorDisposal,
  getOperatorNetwork: async () => q.network,
  findDisposal: async () => q.disposal,
  // The real resolver is a lookup table; only its two outcomes matter here.
  resolveCounty: (ref: string) =>
    /^(andrews|003)$/i.test(ref.trim()) ? { county_no: "003", county_name: "ANDREWS" } : null,
}));

/**
 * Name resolution is a stand-in here, not the real thing.
 *
 * `rrc_estate_map` used to match `officer_name ilike '%<the whole string>%'`,
 * which cannot find a name typed in reading order, with a middle name, or with
 * one wrong letter, against a table that stores `SMITH, JOHN B.`. It now calls
 * `resolveOfficerNames`, whose own tests are in `../people.test.ts` and whose
 * ranking needs live trigram scores to mean anything.
 *
 * What these tests are for is the AGGREGATION on top of it, so the stand-in
 * keeps the one property the aggregation depends on — a name in any order
 * reaches the file's spelling — using the real surname parser and nothing else.
 * The seam itself is asserted separately: estate_map must look names up by
 * equality against what the resolver returned, and never send a wildcard.
 */
vi.mock("../people", async () => {
  const { parsePersonName } = await import("../../../rrc/operator-match");
  return {
    resolveOfficerNames: async (raw: string) => {
      const want = parsePersonName(raw);
      return [...new Set(db.officers.map((o) => String(o.officer_name)))]
        .filter((n) => want?.last && parsePersonName(n)?.last === want.last)
        .map((officer_name) => ({
          officer_name,
          operator_count: 1,
          score: 1,
          matched: "surname" as const,
        }));
    },
    PERSON_NOTES: [],
  };
});

const { TOOLS } = await import("./screening");

type Result = any;

const call = async (name: string, args: Record<string, unknown>): Promise<Result> => {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`No tool ${name}. Have: ${TOOLS.map((t) => t.name).join(", ")}`);
  return (await tool.run(tool.args.parse(args) as never)) as Result;
};

beforeEach(() => {
  db.calls.length = 0;
  for (const key of Object.keys(db) as (keyof typeof db)[]) {
    const value = db[key];
    if (Array.isArray(value)) value.length = 0;
  }
  db.series.clear();
  q.p4.clear();
  q.operatorH15 = { wellsTested: 0, delinquent: 0, dueSoon: 0, lastTest: null };
  q.operatorDisposal = {
    wells: 0,
    commercialWells: 0,
    permittedBblPerDay: null,
    injectedBbl12m: null,
    lastReported: null,
    reportedThrough: "2024-08",
  };
  q.disposal.length = 0;
  q.network = null;
});

// ------------------------------------------------------------- the catalog

const EXPECTED_TOOLS = [
  "rrc_acquisition_screen",
  "rrc_distress_signal",
  "rrc_idle_with_reserves",
  "rrc_reentry_screen",
  "rrc_bolt_on",
  "rrc_transaction_history",
  "rrc_operator_exit",
  "rrc_estate_map",
  "rrc_package_value_drivers",
  "rrc_liability_check",
  "rrc_why_selling",
  "rrc_seller_asymmetry",
  "rrc_obligation_calendar",
];

test("the catalog is the thirteen screening tools, named once each", () => {
  expect(TOOLS.map((t) => t.name)).toEqual(EXPECTED_TOOLS);
  expect(new Set(TOOLS.map((t) => t.name)).size).toBe(13);
});

// --------------------------------------------------------------- refusals

describe("an unfiltered screen is refused rather than attempted", () => {
  test("rrc_acquisition_screen with no county, district or operator", async () => {
    const r = await call("rrc_acquisition_screen", {});
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/refused/i);
    expect(r.error).toMatch(/operator_no, county or district/);
    // A refusal is a value, and it costs nothing: no query was issued.
    expect(db.calls).toHaveLength(0);
  });

  test("rrc_idle_with_reserves, rrc_reentry_screen and rrc_operator_exit too", async () => {
    for (const name of ["rrc_idle_with_reserves", "rrc_reentry_screen", "rrc_operator_exit"]) {
      const r = await call(name, {});
      expect(r.ok, name).toBe(false);
      expect(r.error, name).toMatch(/refused/i);
    }
    expect(db.calls).toHaveLength(0);
  });

  test("a county the state does not have is refused by name", async () => {
    const r = await call("rrc_acquisition_screen", { county: "Nottingham" });
    expect(r.ok).toBe(false);
    expect(r.error).toBe('Not a Texas county: "Nottingham".');
  });

  test("a district that is not an RRC district is refused with the real list", async () => {
    const r = await call("rrc_acquisition_screen", { district: "12" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/Not an RRC district: "12"/);
    expect(r.error).toMatch(/7B/);
  });

  test("a tool with no target refuses instead of scanning", async () => {
    expect((await call("rrc_transaction_history", {})).ok).toBe(false);
    expect((await call("rrc_package_value_drivers", {})).ok).toBe(false);
    expect((await call("rrc_why_selling", {})).ok).toBe(false);
    expect((await call("rrc_seller_asymmetry", {})).ok).toBe(false);
    expect((await call("rrc_estate_map", {})).ok).toBe(false);
  });
});

// -------------------------------------------------------- 35 band and rate

describe("rrc_acquisition_screen", () => {
  beforeEach(() => {
    db.leaseCandidates = [
      {
        oil_gas_code: "O",
        district_no: "10",
        lease_no: "12345",
        lease_name: "SMITH A",
        operator_no: "111111",
        operator_name: "ALPHA OIL",
        county_name: "ANDREWS",
        field_name: "SPRABERRY",
        // 3,650 bbl over a 365-day window is 10.0 bopd exactly.
        oil: 3650,
        gas: 7300,
      },
    ];
    db.leaseWellCounts = [
      { oil_gas_code: "O", district: "08", lease_number: "12345", wells: 4 },
    ];
    db.leaseFlags = [
      {
        oil_gas_code: "O",
        district_no: "10",
        lease_no: "12345",
        off_schedule: "Y",
        severance: null,
      },
    ];
    db.fleets = [{ operator_number: "111111", wells: 40, flagged: 5, plugged: 3 }];
  });

  test("the window is the RRC's published edge, and its length is counted in calendar days", async () => {
    const r = await call("rrc_acquisition_screen", { county: "Andrews" });
    expect(r.ok).toBe(true);
    // 2024-07 through 2025-06. Feb 2025 is 28 days; no leap February is in it.
    expect(r.window).toEqual({ months: 12, through: EDGE, days: WINDOW_DAYS });
    expect(r.reported_through).toBe(EDGE);
  });

  test("a rate band is bound as a VOLUME over the window's own days, not over 30-day months", async () => {
    await call("rrc_acquisition_screen", { county: "Andrews", min_bopd: 5, max_mcfd: 40 });
    const screen = db.calls.find((c) => c.sql.includes("from rrc.county_lease_cycle"))!;
    // 5 bopd across 365 days is 1,825 bbl; 40 Mcf/d across 365 days is 14,600 Mcf.
    expect(screen.params).toContain(5 * WINDOW_DAYS);
    expect(screen.params).toContain(40 * WINDOW_DAYS);
    expect(screen.params).toContain(1825);
    expect(screen.params).toContain(14600);
  });

  test("bopd and mcfd divide the window volume by the same calendar days", async () => {
    const r = await call("rrc_acquisition_screen", { county: "Andrews" });
    const lease = r.leases[0];
    expect(lease.bopd).toBeCloseTo(3650 / 365, 12);
    expect(lease.bopd).toBeCloseTo(10, 12);
    expect(lease.mcfd).toBeCloseTo(7300 / 365, 12);
    expect(lease.mcfd).toBeCloseTo(20, 12);
  });

  test("the district is translated for the wellbore tape and shown as the label a person says", async () => {
    const r = await call("rrc_acquisition_screen", { county: "Andrews" });
    // PDQ 10 is District 08. Getting this backwards counts another quarter of
    // Texas's wells onto this lease.
    expect(r.leases[0].district_no).toBe("10");
    expect(r.leases[0].district).toBe("08");
    expect(r.leases[0].wells).toBe(4);
    const wellQuery = db.calls.find((c) => c.sql.includes("unnest"))!;
    expect(wellQuery.params[1]).toEqual(["08"]);
  });

  test("the lease flags and the operator's fleet size come through and filter", async () => {
    const r = await call("rrc_acquisition_screen", { county: "Andrews" });
    expect(r.leases[0].off_schedule).toBe(true);
    expect(r.leases[0].severance).toBe(false);
    expect(r.leases[0].operator_wells).toBe(40);

    expect((await call("rrc_acquisition_screen", { county: "Andrews", severance: true })).leases)
      .toHaveLength(0);
    expect((await call("rrc_acquisition_screen", { county: "Andrews", max_wells: 3 })).leases)
      .toHaveLength(0);
    expect(
      (await call("rrc_acquisition_screen", { county: "Andrews", max_operator_wells: 20 })).leases
    ).toHaveLength(0);
  });

  test("no curve is fitted unless the caller filters on decline, and it says so", async () => {
    const r = await call("rrc_acquisition_screen", { county: "Andrews" });
    expect(r.leases_fitted).toBe(0);
    expect(r.leases[0].decline).toBeNull();
    expect(db.calls.some((c) => c.sql.includes("from rrc.lease_production"))).toBe(false);
    expect(r.notes.join(" ")).toMatch(/No decline filter was given/);
  });

  test("with a decline filter the curve is fitted off the lease index and the filter bites", async () => {
    db.series.set("O/10/12345", decliningLease("2022-07", 36));
    const loose = await call("rrc_acquisition_screen", {
      county: "Andrews",
      max_decline_pct_per_yr: 99,
    });
    expect(loose.leases_fitted).toBe(1);
    expect(loose.leases[0].decline.fitted).toBe(true);
    // 3% per month compounded is 1 - 0.97^12 = 30.62% over a year. The fit is
    // hyperbolic and the terminal floor applies, so this is bounded rather than
    // asserted to the digit: what is being proved is that a 30%/yr lease passes
    // a 99% filter and fails a 5% one.
    expect(loose.leases[0].decline.declinePctPerYear).toBeGreaterThan(20);
    expect(loose.leases[0].decline.declinePctPerYear).toBeLessThan(45);

    const tight = await call("rrc_acquisition_screen", {
      county: "Andrews",
      max_decline_pct_per_yr: 5,
    });
    expect(tight.leases).toHaveLength(0);
  });
});

// ---------------------------------------------------------- 36 the weights

describe("rrc_distress_signal", () => {
  beforeEach(() => {
    db.operatorProduction = [
      // A quarter of the barrels gone: 1 - 9000/12000 = 0.25.
      { operator_no: "111111", last12: 9000, prior12: 12000 },
    ];
    db.operators = [
      {
        operator_number: "111111",
        operator_name: "ALPHA OIL",
        p5_status: "A",
        last_p5_date: "2024-12-01",
      },
    ];
    db.fleets = [{ operator_number: "111111", wells: 40, flagged: 5, plugged: 3 }];
    db.h15Position = [{ operator_no: "111111", wells: 20, delinquent: 1 }];
    db.h15PositionPrior = [{ operator_no: "111111", wells: 20, delinquent: 3 }];
    db.statePlugs = [{ operator_number: "111111", state_plugs: 2 }];
  });

  test("the composite is exactly the asserted weights applied to the components", async () => {
    const r = await call("rrc_distress_signal", { operators: ["111111"] });
    expect(r.ok).toBe(true);
    const op = r.operators[0];

    /*
     * Worked by hand from the fixture and the constants the tool publishes.
     *
     *   production_rollover  1 - 9000/12000 = 0.25 ; floor 0.5  -> 0.5
     *   h15_delinquency      1/20           = 0.05 ; floor 0.25 -> 0.2
     *   flags_14b2           5/40           = 0.125; floor 0.25 -> 0.5
     *   p5_expiry            days 2024-12-01 -> 2025-06-01, over 30.4375,
     *                        over a 12-month floor
     *   state_funded_plugs   2                     ; floor 5    -> 0.4
     */
    const p5Days = 31 + 31 + 28 + 31 + 30 + 31; // Dec, Jan, Feb, Mar, Apr, May
    expect(p5Days).toBe(182);
    const p5Score = p5Days / 30.4375 / 12;

    const expected =
      0.5 * 0.3 + 0.2 * 0.2 + 0.5 * 0.2 + p5Score * 0.15 + 0.4 * 0.15;
    expect(expected).toBeCloseTo(0.4247433, 6);
    expect(op.score).toBeCloseTo(expected, 12);
  });

  test("every component is returned with its value, weight and contribution", async () => {
    const r = await call("rrc_distress_signal", { operators: ["111111"] });
    const by = Object.fromEntries(
      r.operators[0].components.map((c: any) => [c.component, c])
    );
    expect(Object.keys(by).sort()).toEqual([
      "flags_14b2",
      "h15_delinquency",
      "p5_expiry",
      "production_rollover",
      "state_funded_plugs",
    ]);
    expect(by.production_rollover.value).toBeCloseTo(0.25, 12);
    expect(by.production_rollover.score).toBeCloseTo(0.5, 12);
    expect(by.production_rollover.weight).toBe(0.3);
    expect(by.production_rollover.contribution).toBeCloseTo(0.15, 12);

    expect(by.flags_14b2.value).toBeCloseTo(0.125, 12);
    expect(by.flags_14b2.contribution).toBeCloseTo(0.1, 12);
    expect(by.state_funded_plugs.value).toBe(2);
    expect(by.state_funded_plugs.contribution).toBeCloseTo(0.06, 12);

    // The contributions must be the score, or the parts do not explain the whole.
    const sum = r.operators[0].components.reduce(
      (a: number, c: any) => a + c.contribution,
      0
    );
    expect(sum).toBeCloseTo(r.operators[0].score, 12);
    // And the weights themselves have to be a partition, or "score" has no scale.
    expect(Object.values(r.weights).reduce((a: any, b: any) => a + b, 0)).toBeCloseTo(1, 12);
  });

  test("a component score is capped at one, so a collapse cannot outrank the scale", async () => {
    db.operatorProduction = [{ operator_no: "111111", last12: 0, prior12: 12000 }];
    db.statePlugs = [{ operator_number: "111111", state_plugs: 50 }];
    const r = await call("rrc_distress_signal", { operators: ["111111"] });
    const by = Object.fromEntries(
      r.operators[0].components.map((c: any) => [c.component, c])
    );
    // 1 - 0/12000 = 1.0 against a 0.5 floor is 2.0 before the cap.
    expect(by.production_rollover.value).toBe(1);
    expect(by.production_rollover.score).toBe(1);
    expect(by.state_funded_plugs.score).toBe(1);
    expect(r.operators[0].score).toBeLessThanOrEqual(1);
  });

  test("the delinquency TREND is reported beside the level, not folded into the score", async () => {
    const r = await call("rrc_distress_signal", { operators: ["111111"] });
    const ev = r.operators[0].evidence;
    // 1/20 now against 3/20 a year ago: falling, which does not lower the score.
    expect(ev.h15_delinquent_share).toBeCloseTo(0.05, 12);
    expect(ev.h15_delinquent_share_a_year_ago).toBeCloseTo(0.15, 12);
    expect(ev.h15_delinquent_share_change).toBeCloseTo(-0.1, 12);
    const h15 = r.operators[0].components.find((c: any) => c.component === "h15_delinquency");
    expect(h15.value).toBeCloseTo(0.05, 12);
  });

  test("an unmeasured component scores zero and says it was unmeasured", async () => {
    db.operatorProduction = [];
    db.h15Position = [];
    const r = await call("rrc_distress_signal", { operators: ["111111"] });
    const by = Object.fromEntries(
      r.operators[0].components.map((c: any) => [c.component, c])
    );
    expect(by.production_rollover.measured).toBe(false);
    expect(by.production_rollover.value).toBeNull();
    expect(by.production_rollover.contribution).toBe(0);
    expect(by.flags_14b2.measured).toBe(true);
  });

  test("the result says the weights are asserted rather than fitted", async () => {
    const r = await call("rrc_distress_signal", { operators: ["111111"] });
    expect(r.notes.join(" ")).toMatch(/ASSERTED, not fitted/);
    expect(r.floors).toBeDefined();
  });
});

// -------------------------------------------------------- 40 the P-4 story

describe("rrc_transaction_history", () => {
  /**
   * Three filings on one lease, newest first as the P-4 read returns them.
   *
   * The middle one carries the "Operator" change flag and names the SAME
   * operator as the filing before it. That is routine paperwork, and the whole
   * point of this fixture is that it must not become a deal.
   */
  const FILINGS = [
    {
      effective_date: "2023-02-01",
      approval_date: "2023-03-10",
      record_type: "R",
      operator_no: "222222",
      operator_name: "BETA RESOURCES",
      field_no: "1234",
      changes: ["Operator", "Purchaser"],
    },
    {
      effective_date: "2021-07-15",
      approval_date: "2021-08-01",
      record_type: "R",
      operator_no: "111111",
      operator_name: "ALPHA OIL",
      field_no: "1234",
      changes: ["Operator"],
    },
    {
      effective_date: "2019-03-01",
      approval_date: "2019-04-02",
      record_type: "O",
      operator_no: "111111",
      operator_name: "ALPHA OIL",
      field_no: "1234",
      changes: ["Lease name"],
    },
  ];

  beforeEach(() => {
    q.p4.set("O/10/12345", {
      connections: [
        {
          product_code: "O",
          type_code: "H",
          gpn_no: "333333",
          operator_name: "GAMMA CRUDE",
          actual_percent: 1,
          effective_date: "2023-02-01",
          interstate: false,
          intrastate: true,
        },
      ],
      filings: FILINGS,
    });
  });

  const args = { oil_gas_code: "O", district_no: "10", lease_no: "12345" };

  test("one transfer is reconstructed, at the filing where the operator actually changed", async () => {
    const r = await call("rrc_transaction_history", args);
    expect(r.ok).toBe(true);
    const lease = r.leases[0];
    expect(lease.filings).toBe(3);
    expect(lease.transfer_count).toBe(1);
    expect(lease.transfers).toEqual([
      {
        effective_date: "2023-02-01",
        approval_date: "2023-03-10",
        from_operator_no: "111111",
        from_operator_name: "ALPHA OIL",
        to_operator_no: "222222",
        to_operator_name: "BETA RESOURCES",
        changes: ["Operator", "Purchaser"],
        record_type: "R",
      },
    ]);
  });

  test("a filing flagged 'Operator' that names the same operator is NOT a transfer", async () => {
    const r = await call("rrc_transaction_history", args);
    const dates = r.leases[0].transfers.map((t: any) => t.effective_date);
    expect(dates).not.toContain("2021-07-15");
    expect(dates).toEqual(["2023-02-01"]);
  });

  test("with only unchanged operators there is no transfer at all", async () => {
    q.p4.set("O/10/12345", {
      connections: [],
      filings: [
        { ...FILINGS[1], effective_date: "2021-07-15" },
        { ...FILINGS[2], effective_date: "2019-03-01" },
      ],
    });
    const r = await call("rrc_transaction_history", args);
    expect(r.leases[0].transfers).toEqual([]);
    expect(r.transfers_total).toBe(0);
  });

  test("counterparty changes are reported separately from transfers", async () => {
    const r = await call("rrc_transaction_history", args);
    expect(r.leases[0].counterparty_changes).toEqual([
      {
        effective_date: "2023-02-01",
        approval_date: "2023-03-10",
        operator_no: "222222",
        operator_name: "BETA RESOURCES",
        changes: ["Operator", "Purchaser"],
      },
    ]);
    expect(r.leases[0].current_connections[0].counterparty_no).toBe("333333");
  });

  test("the result says outright that this is not a money comp", async () => {
    const r = await call("rrc_transaction_history", args);
    expect(r.notes.join(" ")).toMatch(/NOT A COMPS DATABASE IN THE MONEY SENSE/);
  });
});

// ------------------------------------------------------ 69 date arithmetic

describe("rrc_obligation_calendar", () => {
  /** Everything below is counted against this one calendar date. */
  const AS_OF = "2026-03-15";

  beforeEach(() => {
    db.h15Latest = [
      // Due 2026-06-01, which is in the window.
      {
        api_number: "00312345",
        next_test_year: "2026",
        next_test_month: "06",
        status: "C",
        test_date: "2024-06-04",
      },
      // Due 2025-11-01, already past.
      {
        api_number: "00399999",
        next_test_year: "2025",
        next_test_month: "11",
        status: "D",
        test_date: "2023-11-02",
      },
      // No parsable due date on the tape: dropped rather than guessed.
      {
        api_number: "00300001",
        next_test_year: "0000",
        next_test_month: "",
        status: "C",
        test_date: "2024-01-01",
      },
    ];
    db.permitExpiry = [
      { permit_number: "0912345", lease_name: "SMITH A", expires_date: "2026-09-30" },
    ];
    db.operators = [
      { operator_name: "ALPHA OIL", p5_status: "A", last_p5_date: "2025-08-04" },
    ];
    db.obligationInactive = [
      {
        api_number: "00355555",
        lease_name: "JONES B",
        inact_yrs: 3,
        inact_mos: 2,
        flagged: true,
      },
    ];
  });

  test("the horizon end is as_of plus the horizon in whole months", async () => {
    const r = await call("rrc_obligation_calendar", {
      operator_no: "111111",
      as_of: AS_OF,
      horizon_months: 12,
    });
    expect(r.ok).toBe(true);
    expect(r.as_of).toBe(AS_OF);
    expect(r.through).toBe("2027-03-15");
  });

  test("days_until is whole calendar days counted from as_of", async () => {
    const r = await call("rrc_obligation_calendar", {
      operator_no: "111111",
      as_of: AS_OF,
      horizon_months: 12,
    });
    const by = Object.fromEntries(r.obligations.map((o: any) => [o.subject, o]));

    /*
     * H-15 on 00312345, due the first of 2026-06. Counted by hand from
     * 2026-03-15: 16 days left in March, 30 in April, 31 in May, then the 1st.
     */
    expect(16 + 30 + 31 + 1).toBe(78);
    expect(by["00312345"].due_date).toBe("2026-06-01");
    expect(by["00312345"].days_until).toBe(78);
    expect(by["00312345"].overdue).toBe(false);

    /*
     * H-15 on 00399999, due 2025-11-01, which is BEHIND as_of. Counted back:
     * 30 in November, 31 December, 31 January, 28 February (2026 is not a leap
     * year), 14 into March.
     */
    expect(30 + 31 + 31 + 28 + 14).toBe(134);
    expect(by["00399999"].days_until).toBe(-134);
    expect(by["00399999"].overdue).toBe(true);

    /*
     * P-5 last filed 2025-08-04, renewed on a twelve-month term, so due
     * 2026-08-04. From 2026-03-15: 16 + 30 + 31 + 30 + 31 + 4.
     */
    expect(16 + 30 + 31 + 30 + 31 + 4).toBe(142);
    expect(by["111111"].due_date).toBe("2026-08-04");
    expect(by["111111"].days_until).toBe(142);

    /*
     * The permit expires 2026-09-30. From 2026-03-15: 16 + 30 + 31 + 30 + 31 +
     * 31 + 30 in the months to 2026-09-15... counted straight instead:
     * March 16, April 30, May 31, June 30, July 31, August 31, September 30.
     */
    expect(16 + 30 + 31 + 30 + 31 + 31 + 30).toBe(199);
    expect(by["0912345"].days_until).toBe(199);
  });

  test("an H-15 with no parsable due month is dropped, never given a date", async () => {
    const r = await call("rrc_obligation_calendar", {
      operator_no: "111111",
      as_of: AS_OF,
      horizon_months: 12,
    });
    expect(r.obligations.map((o: any) => o.subject)).not.toContain("00300001");
    expect(r.counts.h15).toBe(2);
  });

  test("a well past the 14(b)(2) clock is listed as overdue with no invented due date", async () => {
    const r = await call("rrc_obligation_calendar", {
      operator_no: "111111",
      as_of: AS_OF,
      horizon_months: 12,
    });
    const clock = r.obligations.find((o: any) => o.subject === "00355555");
    // 3 years and 2 months is 38 months, which is 26 past the 12-month clock.
    expect(clock.detail.months_inactive).toBe(38);
    expect(clock.detail.months_past_clock).toBe(26);
    expect(clock.due_date).toBeNull();
    expect(clock.days_until).toBeNull();
    expect(clock.overdue).toBe(true);
    expect(r.notes.join(" ")).toMatch(/NOT the expiry of any extension/);
  });

  test("obligations are ordered soonest first, with the undated ones last", async () => {
    const r = await call("rrc_obligation_calendar", {
      operator_no: "111111",
      as_of: AS_OF,
      horizon_months: 12,
    });
    expect(r.obligations.map((o: any) => o.days_until)).toEqual([-134, 78, 142, 199, null]);
    expect(r.counts.overdue).toBe(2);
  });

  test("a P-5 renewal past the horizon is left out rather than shown as due", async () => {
    // Filed 2025-11-20, so due 2026-11-20, past a 6-month horizon to 2026-09-15.
    db.operators = [
      { operator_name: "ALPHA OIL", p5_status: "A", last_p5_date: "2025-11-20" },
    ];
    const r = await call("rrc_obligation_calendar", {
      operator_no: "111111",
      as_of: AS_OF,
      horizon_months: 6,
    });
    expect(r.through).toBe("2026-09-15");
    expect(r.obligations.map((o: any) => o.form)).not.toContain("Form P-5");
  });

  test("a malformed as_of is refused rather than read as today", async () => {
    const r = await call("rrc_obligation_calendar", { operator_no: "111111", as_of: "March 2026" });
    expect(r.ok).toBe(false);
    expect(r.error).toBe("as_of must be YYYY-MM-DD.");
  });
});

// ------------------------------------------------------------- 38 re-entry

describe("rrc_reentry_screen", () => {
  beforeEach(() => {
    db.pluggedWells = [
      {
        api_number: "00312345",
        well_no: "1",
        lease_name: "SMITH A",
        county_name: "ANDREWS",
        field_name: "SPRABERRY",
        operator_number: "111111",
        operator_name: "ALPHA OIL",
        api_depth: 9000,
      },
    ];
    db.plugSummary = [
      {
        api_number: "00312345",
        plug_date: "2019-05-02",
        total_depth: 9000,
        shallowest_plug_top: 6000,
        plugs: 4,
        cement_sacks: 200,
        state_funded: false,
      },
    ];
    db.perfs = [
      // Entirely above the plug: all 200 ft count.
      { api_number: "00312345", top_ft: 5000, bottom_ft: 5200 },
      // Straddles the plug top at 6000: only the 100 ft above it count.
      { api_number: "00312345", top_ft: 5900, bottom_ft: 6300 },
      // Entirely below the plug: nothing counts.
      { api_number: "00312345", top_ft: 7000, bottom_ft: 7400 },
    ];
    db.formations = [
      // Covered by the 5000-5200 perforation, so it was shot.
      { api_no: "00312345", formation: "SPRABERRY", depth: 5100 },
      // Logged and never shot.
      { api_no: "00312345", formation: "WOLFCAMP", depth: 8200 },
      { api_no: "00312345", formation: "STRAWN", depth: 8800 },
    ];
  });

  test("perforated feet above the shallowest plug are summed, straddling intervals clipped", async () => {
    const r = await call("rrc_reentry_screen", { operator_no: "111111" });
    expect(r.ok).toBe(true);
    const well = r.wells[0];
    // (5200 - 5000) + (6000 - 5900) + nothing below = 300 ft, across 2 intervals.
    expect(well.perf_ft_above_plug).toBe(300);
    expect(well.perfs_above_plug).toBe(2);
    expect(well.perf_intervals).toBe(3);
    expect(well.shallowest_plug_top_ft).toBe(6000);
  });

  test("formations logged but never perforated are named with their depths", async () => {
    const r = await call("rrc_reentry_screen", { operator_no: "111111" });
    const well = r.wells[0];
    expect(well.formations_logged).toBe(3);
    expect(well.formations_never_perforated).toBe(2);
    expect(well.formations).toEqual([
      { formation: "WOLFCAMP", depth_ft: 8200 },
      { formation: "STRAWN", depth_ft: 8800 },
    ]);
  });

  test("cement is reported per plug from the W-3's own numbers", async () => {
    const r = await call("rrc_reentry_screen", { operator_no: "111111" });
    // 200 sacks over 4 plugs.
    expect(r.wells[0].cement_sacks_per_plug).toBe(50);
    expect(r.wells[0].plug_date).toBe("2019-05-02");
    expect(r.wells[0].state_funded_plug).toBe(false);
  });

  test("the minimum-feet filter cuts on the computed number", async () => {
    const r = await call("rrc_reentry_screen", { operator_no: "111111", min_perf_ft_above_plug: 301 });
    expect(r.wells).toHaveLength(0);
    expect(r.wells_examined).toBe(1);
  });
});

// ------------------------------------------------------- 37 idle and reserves

describe("rrc_idle_with_reserves", () => {
  beforeEach(() => {
    db.idleWells = [
      {
        api_number: "00312345",
        well_no: "1",
        lease_name: "SMITH A",
        lease_number: "12345",
        oil_gas_code: "O",
        district: "08",
        county_name: "ANDREWS",
        operator_number: "111111",
        operator_name: "ALPHA OIL",
        well_type_name: "SHUT IN",
        inact_yrs: 2,
        inact_mos: 3,
        flagged: false,
      },
      {
        api_number: "00312346",
        well_no: "2",
        lease_name: "SMITH A",
        lease_number: "12345",
        oil_gas_code: "O",
        district: "08",
        county_name: "ANDREWS",
        operator_number: "111111",
        operator_name: "ALPHA OIL",
        well_type_name: "TEMP ABANDONED",
        inact_yrs: 0,
        inact_mos: 8,
        flagged: true,
      },
    ];
    // The wellbore tape says District 08; the production tape keys it as 10.
    db.series.set("O/10/12345", decliningLease("2022-07", 36));
  });

  test("idle wells are grouped onto the lease, which is the only grain volumes exist at", async () => {
    const r = await call("rrc_idle_with_reserves", { operator_no: "111111" });
    expect(r.ok).toBe(true);
    expect(r.idle_wells).toBe(2);
    expect(r.leases).toHaveLength(1);
    expect(r.leases[0].key).toBe("O/10/12345");
    expect(r.leases[0].district).toBe("08");
    expect(r.leases[0].idle_wells).toBe(2);
    expect(r.notes.join(" ")).toMatch(/REMAINING RESERVES ARE THE LEASE'S, NOT THE IDLE WELL'S/);
  });

  test("the 14(b)(2) clock is read off the RRC's own inactivity counters", async () => {
    const r = await call("rrc_idle_with_reserves", { operator_no: "111111" });
    const wells = Object.fromEntries(r.leases[0].wells.map((w: any) => [w.api_number, w]));
    // 2 years 3 months is 27 months, past the 12-month clock.
    expect(wells["00312345"].past_14b2_clock).toBe(true);
    // 8 months is not.
    expect(wells["00312346"].past_14b2_clock).toBe(false);
  });

  test("a lease whose curve still has reserves survives the minimum, and a high one does not", async () => {
    const r = await call("rrc_idle_with_reserves", { operator_no: "111111" });
    expect(r.leases[0].remaining_bbl).toBeGreaterThan(0);
    const high = await call("rrc_idle_with_reserves", {
      operator_no: "111111",
      min_remaining_bbl: 1e12,
    });
    expect(high.leases).toHaveLength(0);
  });

  test("a lease with too little history is reported as unfitted rather than as empty", async () => {
    db.series.set("O/10/12345", decliningLease("2025-03", 4));
    const r = await call("rrc_idle_with_reserves", { operator_no: "111111" });
    expect(r.leases).toHaveLength(0);
    expect(r.unfitted).toEqual([
      { key: "O/10/12345", reason: "Only 4 reported producing months; a fit needs 6." },
    ]);
  });
});

// ------------------------------------------------------------ 39 the caveat

describe("rrc_bolt_on", () => {
  beforeEach(() => {
    db.boltOn = [
      {
        oil_gas_code: "O",
        district: "08",
        lease_number: "77777",
        lease_name: "NEIGHBOR C",
        operator_number: "222222",
        operator_name: "BETA RESOURCES",
        survey_name: "T & P RR CO",
        block_number: "A-34",
        abstract_label: "A-341",
        shared: true,
        wells: 3,
      },
    ];
    db.series.set("O/10/77777", decliningLease("2022-07", 36));
  });

  test("the acreage caveat rides on every result", async () => {
    const r = await call("rrc_bolt_on", { operator_no: "111111" });
    expect(r.ok).toBe(true);
    expect(r.notes.join(" ")).toMatch(/Survey tracts are land grants, not leases/);
    expect(r.notes.join(" ")).toMatch(/BOUNDING BOX, not its outline/);
  });

  test("a shared tract is labelled as such and the lease is measured over the window", async () => {
    const r = await call("rrc_bolt_on", { operator_no: "111111" });
    const lease = r.leases[0];
    expect(lease.relation).toBe("same_tract");
    expect(lease.key).toBe("O/10/77777");
    expect(lease.wells_in_tract).toBe(3);
    // The last twelve cycles of the fixture, summed by hand from the same law.
    const window = decliningLease("2022-07", 36).slice(-12);
    expect(lease.oil_bbl).toBe(window.reduce((a, r2) => a + r2.oil, 0));
    expect(lease.bopd).toBeCloseTo(lease.oil_bbl / WINDOW_DAYS, 12);
  });

  test("adjacency is opt-in and reaches the query as a bound parameter", async () => {
    await call("rrc_bolt_on", { operator_no: "111111", include_adjacent: true });
    const boltCall = db.calls.find((c) => c.sql.includes("with mine as"))!;
    expect(boltCall.params).toEqual(["111111", true, 300]);
  });

  test("a missing operator_no is refused", async () => {
    expect((await call("rrc_bolt_on", { operator_no: "  " })).ok).toBe(false);
  });
});

// --------------------------------------------------------------- 68 filings

describe("rrc_seller_asymmetry", () => {
  beforeEach(() => {
    db.sellerFlagged = [
      {
        api_number: "00312345",
        lease_name: "SMITH A",
        modified_dt: "2024-11-02",
        reasons: ["H-15 delinquent", "Pollution"],
      },
    ];
    db.h15Delinquent = [
      { api_number: "00399999", status_date: "2025-01-09", test_date: "2023-11-02" },
    ];
    db.sellerStatePlugs = [
      { api_number: "00344444", plug_date: "2022-04-18", total_depth: 7400 },
    ];
    db.operators = [{ p5_status: "D", last_p5_date: "2024-02-01" }];
    db.uicPermits = [
      {
        uic_no: "UIC-1",
        approved_date: "2018-06-06",
        max_bbl_per_day: 10000,
        max_inj_pressure: 1200,
        is_commercial: true,
      },
    ];
    db.leaseFlags = [{ off_schedule: "Y", severance: "Y" }];
    db.unfiledMonths = [{ cycle: "2025-03" }, { cycle: "2024-12" }];
  });

  test("every item names its filing and carries its date, newest first", async () => {
    const r = await call("rrc_seller_asymmetry", {
      operator_no: "111111",
      oil_gas_code: "O",
      district_no: "10",
      lease_no: "12345",
    });
    expect(r.ok).toBe(true);
    for (const item of r.items) {
      expect(typeof item.filing).toBe("string");
      expect(item.filing.length).toBeGreaterThan(0);
      expect(item).toHaveProperty("date");
    }
    const dated = r.items.filter((i: any) => i.date).map((i: any) => i.date);
    expect(dated).toEqual([...dated].sort().reverse());
    expect(dated[0]).toBe("2025-03");
  });

  test("the items are the ones a seller understates, each tied to its form", async () => {
    const r = await call("rrc_seller_asymmetry", {
      operator_no: "111111",
      oil_gas_code: "O",
      district_no: "10",
      lease_no: "12345",
    });
    const by = Object.fromEntries(r.items.map((i: any) => [i.item, i]));
    expect(by["14(b)(2) flagged well"].date).toBe("2024-11-02");
    expect(by["14(b)(2) flagged well"].filing).toMatch(/record last modified/);
    expect(by["H-15 delinquent well"].date).toBe("2025-01-09");
    expect(by["State-funded plug on the record"].date).toBe("2022-04-18");
    expect(by["State-funded plug on the record"].filing).toMatch(/Form W-3/);
    expect(by["P-5 not in active status"].date).toBe("2024-02-01");
    expect(by["Live injection permit inherited"].date).toBe("2018-06-06");
    expect(by["Production months never filed"].detail.months).toBe(2);
  });

  test("an item the tape carries no date for says so rather than borrowing one", async () => {
    const r = await call("rrc_seller_asymmetry", {
      oil_gas_code: "O",
      district_no: "10",
      lease_no: "12345",
    });
    const severance = r.items.find((i: any) => i.item === "Lease under severance");
    expect(severance.date).toBeNull();
    expect(severance.filing).toMatch(/carries no date/);
    // Undated items sort last, never first, so the newest real filing leads.
    expect(r.items[r.items.length - 1].date).toBeNull();
  });
});

// ------------------------------------------------------------- 67 and 41-44

describe("the reason and sweep tools", () => {
  test("rrc_why_selling reports every reason with its evidence, indicated or not", async () => {
    db.series.set("O/10/12345", decliningLease("2022-07", 36));
    db.w10 = [
      { test_date: "2022-01-05", well_no: "1", daily_oil: 90, daily_water: 10 },
      { test_date: "2022-07-05", well_no: "1", daily_oil: 80, daily_water: 20 },
      { test_date: "2024-01-05", well_no: "1", daily_oil: 60, daily_water: 40 },
      { test_date: "2024-07-05", well_no: "1", daily_oil: 40, daily_water: 60 },
    ];
    q.p4.set("O/10/12345", {
      connections: [],
      filings: [
        {
          effective_date: "2024-09-01",
          approval_date: "2024-10-01",
          record_type: "R",
          operator_no: "111111",
          operator_name: "ALPHA OIL",
          field_no: null,
          changes: ["Purchaser"],
        },
      ],
    });
    q.operatorH15 = { wellsTested: 20, delinquent: 4, dueSoon: 2, lastTest: "2025-01-01" };
    q.operatorDisposal = {
      wells: 2,
      commercialWells: 1,
      permittedBblPerDay: 10,
      injectedBbl12m: 3650,
      lastReported: "2024-08",
      reportedThrough: "2024-08",
    };

    const r = await call("rrc_why_selling", {
      oil_gas_code: "O",
      district_no: "10",
      lease_no: "12345",
      operator_no: "111111",
    });
    expect(r.ok).toBe(true);
    expect(r.reasons.map((x: any) => x.reason)).toEqual([
      "water_cut_inflecting",
      "gor_blowing_out",
      "purchaser_departed",
      "h15_coming_due",
      "disposal_near_capacity",
      "decline_steepening",
    ]);

    const by = Object.fromEntries(r.reasons.map((x: any) => [x.reason, x]));
    // Water cut: the first two tests average (0.10 + 0.20) / 2 = 0.15, the last
    // two (0.40 + 0.60) / 2 = 0.50. A ratio of 3.33 clears the 1.25 threshold.
    expect(by.water_cut_inflecting.evidence.early_mean_water_cut).toBeCloseTo(0.15, 12);
    expect(by.water_cut_inflecting.evidence.recent_mean_water_cut).toBeCloseTo(0.5, 12);
    expect(by.water_cut_inflecting.indicated).toBe(true);

    // Disposal: 3,650 bbl over 365 days is 10 bbl/d against a 10 bbl/d ceiling.
    expect(by.disposal_near_capacity.evidence.utilisation).toBeCloseTo(1, 12);
    expect(by.disposal_near_capacity.indicated).toBe(true);

    // The GOR fixture is a flat 2 Mcf per barrel, so this one is NOT indicated,
    // and a tool that reports every reason has to say so rather than omit it.
    expect(by.gor_blowing_out.indicated).toBe(false);
    // The fixture is a flat 2 Mcf per barrel, which is 2,000 scf/bbl. Volumes
    // are whole barrels and whole Mcf, so the monthly rounding moves this by
    // well under one part in a thousand and never by more than a unit.
    expect(by.gor_blowing_out.evidence.recent_6mo_gor_scf_per_bbl).toBeGreaterThan(1999);
    expect(by.gor_blowing_out.evidence.recent_6mo_gor_scf_per_bbl).toBeLessThan(2001);

    expect(by.purchaser_departed.indicated).toBe(true);
    expect(by.h15_coming_due.indicated).toBe(true);
    expect(r.indicated).toContain("water_cut_inflecting");
    expect(r.indicated).not.toContain("gor_blowing_out");
  });

  test("rrc_operator_exit trips only when all three signals fall", async () => {
    db.operatorProduction = [{ operator_no: "111111", last12: 6000, prior12: 12000 }];
    db.leaseCounts = [{ operator_no: "111111", last12: 6, prior12: 10 }];
    db.permitCounts = [{ operator_number: "111111", last12: 0, prior12: 4 }];
    db.operators = [
      { operator_number: "111111", operator_name: "ALPHA OIL", p5_status: "A", last_p5_date: "2025-01-01" },
    ];
    db.fleets = [{ operator_number: "111111", wells: 40, flagged: 2, plugged: 6 }];

    const r = await call("rrc_operator_exit", { operators: ["111111"] });
    const op = r.operators[0];
    // 1 - 6000/12000 = 0.50 against a 0.25 threshold; 1 - 6/10 = 0.40 against
    // 0.20; zero permits against a 0 threshold.
    expect(op.production_drop).toBeCloseTo(0.5, 12);
    expect(op.lease_drop).toBeCloseTo(0.4, 12);
    expect(op.signals).toEqual({
      production_falling: true,
      leases_falling: true,
      permits_stopped: true,
    });
    expect(op.winding_down).toBe(true);

    db.permitCounts = [{ operator_number: "111111", last12: 7, prior12: 4 }];
    const still = await call("rrc_operator_exit", { operators: ["111111"] });
    expect(still.operators[0].winding_down).toBe(false);
    expect(still.operators[0].signals_tripped).toBe(2);
    expect(still.notes.join(" ")).toMatch(/FALLING WELL COUNT CANNOT BE MEASURED/);
  });

  test("rrc_liability_check counts the fleet, the flags and the gaps", async () => {
    db.fleets = [{ operator_number: "111111", wells: 40, flagged: 10, plugged: 6 }];
    db.liabilityReasons = [
      {
        flagged: 10,
        h15_delinquent: 4,
        pollution: 1,
        mechanical_integrity: 2,
        plugging_order: 0,
        district_state_plugging: 1,
        surface_violations: 3,
        w3x_violations: 0,
      },
    ];
    q.operatorH15 = { wellsTested: 20, delinquent: 4, dueSoon: 2, lastTest: "2025-01-01" };
    db.h15Delinquent = [{ api_number: "00399999", status_date: "2025-01-09", test_date: "2023-11-02" }];
    db.liabilityIdle = [
      {
        api_number: "00355555",
        well_no: "3",
        lease_name: "JONES B",
        well_type_name: "SHUT IN",
        inact_yrs: 7,
        inact_mos: 1,
        flagged: true,
      },
    ];
    db.uncoded = [{ wells: 8 }];
    db.statePlugs = [{ wells: 2 }];
    q.disposal = [
      {
        uic_no: "UIC-1",
        api_number: "00312345",
        lease_name: "SMITH A",
        inj_type: "2",
        is_commercial: true,
        max_bbl_per_day: 10000,
        utilisation: 0.4,
      },
    ];

    const r = await call("rrc_liability_check", { operator_no: "111111" });
    expect(r.ok).toBe(true);
    expect(r.fleet).toEqual({ wells_on_schedule: 40, wells_plugged: 6, wells_unplugged: 34 });
    // 10 of 40 wells flagged.
    expect(r.flagged_14b2.share).toBeCloseTo(0.25, 12);
    // 8 of 40 wells with no coordinate on file.
    expect(r.no_coordinates.share).toBeCloseTo(0.2, 12);
    expect(r.orphan_risk.inactive_years_threshold).toBe(5);
    expect(r.orphan_risk.state_funded_plugs_already).toBe(2);
    expect(r.injection_inherited.permitted_bbl_per_day).toBe(10000);
    expect(r.h15.delinquent).toBe(4);
  });

  test("rrc_estate_map keeps only principals holding at least min_operators", async () => {
    db.officers = [
      { officer_name: "EWING, J R", operator_number: "111111", officer_title: "PRESIDENT" },
      { officer_name: "EWING, J R", operator_number: "222222", officer_title: "DIRECTOR" },
      // Same surname, one P-5. Whether this person appears is the whole
      // question `min_operators` answers.
      { officer_name: "EWING, BOBBY", operator_number: "333333", officer_title: "PRESIDENT" },
    ];
    db.operators = [
      {
        operator_number: "111111",
        operator_name: "ALPHA OIL",
        p5_status: "A",
        org_date: "2001-01-01",
        last_p5_date: "2025-06-01",
      },
      {
        operator_number: "222222",
        operator_name: "BETA RESOURCES",
        p5_status: "D",
        org_date: "2015-06-01",
        last_p5_date: "2023-06-01",
      },
      {
        operator_number: "333333",
        operator_name: "GAMMA CRUDE",
        p5_status: "A",
        org_date: "2019-01-01",
        last_p5_date: "2025-01-01",
      },
    ];
    db.fleets = [
      { operator_number: "111111", wells: 40, flagged: 0, plugged: 0 },
      { operator_number: "222222", wells: 12, flagged: 0, plugged: 0 },
      { operator_number: "333333", wells: 5, flagged: 0, plugged: 0 },
    ];

    const spread = await call("rrc_estate_map", {
      officer_name: "EWING",
      as_of: "2026-01-01",
      min_operators: 2,
    });
    expect(spread.ok).toBe(true);
    expect(spread.principals).toHaveLength(1);
    expect(spread.principals[0].officer_name).toBe("EWING, J R");
    expect(spread.principals[0].operator_count).toBe(2);
    expect(spread.principals[0].wells_on_schedule).toBe(52);
    expect(spread.principals[0].oldest_registration).toBe("2001-01-01");
    expect(spread.principals[0].newest_p5_filing).toBe("2025-06-01");

    // Alpha filed 2025-06-01; as_of is 2026-01-01. Counted by hand:
    // June 30, July 31, August 31, September 30, October 31, November 30,
    // December 31.
    expect(30 + 31 + 31 + 30 + 31 + 30 + 31).toBe(214);
    const alpha = spread.principals[0].operators.find((o: any) => o.operator_no === "111111");
    expect(alpha.days_since_p5_filing).toBe(214);

    // Asked by NAME, the floor is one. The question is "what does this person
    // hold", and a floor of two answers "nothing" for anyone with a single P-5,
    // which is most people. That was the old default and it made the tool
    // useless for the question it now has to answer.
    const byName = await call("rrc_estate_map", { officer_name: "EWING", as_of: "2026-01-01" });
    expect(byName.principals.map((p: any) => p.officer_name)).toEqual([
      "EWING, J R",
      "EWING, BOBBY",
    ]);
    expect(byName.names_read.map((n: any) => n.officer_name)).toEqual([
      "EWING, J R",
      "EWING, BOBBY",
    ]);
  });

  test("rrc_estate_map looks a name up by equality, never by a wildcard", async () => {
    db.officers = [
      { officer_name: "EWING, J R", operator_number: "111111", officer_title: "PRESIDENT" },
    ];
    db.operators = [
      {
        operator_number: "111111",
        operator_name: "ALPHA OIL",
        p5_status: "A",
        org_date: "2001-01-01",
        last_p5_date: "2025-06-01",
      },
    ];
    db.fleets = [{ operator_number: "111111", wells: 40, flagged: 0, plugged: 0 }];

    const r = await call("rrc_estate_map", { officer_name: "J R Ewing", as_of: "2026-01-01" });
    expect(r.ok).toBe(true);

    // The old query was `officer_name ilike '%J R Ewing%'`, which finds nothing
    // in a table that stores the surname first. Nothing may send the caller's
    // string to the database as a pattern any more.
    const officerReads = db.calls.filter((c) => c.sql.includes("rrc.operator_officers"));
    expect(officerReads).toHaveLength(1);
    expect(officerReads[0].sql).toContain("officer_name = any($1)");
    expect(officerReads[0].sql).not.toContain("ilike");
    expect(officerReads[0].params[0]).toEqual(["EWING, J R"]);
  });

  test("rrc_package_value_drivers says outright that it does not value", async () => {
    db.series.set("O/10/12345", decliningLease("2022-07", 36));
    db.w10 = [{ test_date: "2024-07-05", well_no: "1", daily_oil: 40, daily_water: 60 }];
    const r = await call("rrc_package_value_drivers", {
      oil_gas_code: "O",
      district_no: "10",
      lease_no: "12345",
    });
    expect(r.ok).toBe(true);
    expect(r.does_not_value).toMatch(/SIZES a package\. It does not value one/);
    expect(r.decline.oil.fitted).toBe(true);
    expect(r.decline.oil.remaining).toBeGreaterThan(0);
    // Water cut on the one test: 60 / (40 + 60).
    expect(r.water_cut.latest.water_cut).toBeCloseTo(0.6, 12);
    // Disposal and plugging follow the P-5, so with a lease alone they refuse
    // rather than report a zero that reads as "none".
    expect(r.disposal_exposure.reason).toMatch(/Supply operator_no/);
    expect(r.plugging_burden.reason).toMatch(/Supply operator_no/);
  });
});

// ------------------------------------------------------------ no money, ever

/**
 * A rich fixture every tool answers from, so the money sweep runs against real
 * output rather than against a pile of refusals.
 */
function loadRichFixture() {
  db.leaseCandidates = [
    {
      oil_gas_code: "O",
      district_no: "10",
      lease_no: "12345",
      lease_name: "SMITH A",
      operator_no: "111111",
      operator_name: "ALPHA OIL",
      county_name: "ANDREWS",
      field_name: "SPRABERRY",
      oil: 3650,
      gas: 7300,
    },
  ];
  db.scopeOperators = [{ operator_no: "111111", oil: 3650 }];
  db.leaseWellCounts = [{ oil_gas_code: "O", district: "08", lease_number: "12345", wells: 4 }];
  db.leaseFlags = [
    { oil_gas_code: "O", district_no: "10", lease_no: "12345", off_schedule: "Y", severance: "Y" },
  ];
  db.fleets = [{ operator_number: "111111", wells: 40, flagged: 10, plugged: 6 }];
  db.operators = [
    {
      operator_number: "111111",
      operator_name: "ALPHA OIL",
      p5_status: "D",
      org_date: "2001-01-01",
      last_p5_date: "2024-12-01",
    },
    {
      operator_number: "222222",
      operator_name: "BETA RESOURCES",
      p5_status: "A",
      org_date: "2015-06-01",
      last_p5_date: "2025-06-01",
    },
  ];
  db.operatorProduction = [{ operator_no: "111111", last12: 9000, prior12: 12000 }];
  db.operatorLeaseKeys = [{ oil_gas_code: "O", district_no: "10", lease_no: "12345" }];
  db.leaseCounts = [{ operator_no: "111111", last12: 6, prior12: 10 }];
  db.permitCounts = [{ operator_number: "111111", last12: 0, prior12: 4 }];
  db.permitExpiry = [
    { permit_number: "0912345", lease_name: "SMITH A", expires_date: "2026-09-30" },
  ];
  db.statePlugs = [{ operator_number: "111111", state_plugs: 2, wells: 2 }];
  db.sellerStatePlugs = [{ api_number: "00344444", plug_date: "2022-04-18", total_depth: 7400 }];
  db.h15Position = [{ operator_no: "111111", wells: 20, delinquent: 4 }];
  db.h15PositionPrior = [{ operator_no: "111111", wells: 20, delinquent: 2 }];
  db.h15Latest = [
    {
      api_number: "00312345",
      next_test_year: "2026",
      next_test_month: "06",
      status: "C",
      test_date: "2024-06-04",
    },
  ];
  db.h15Delinquent = [
    { api_number: "00399999", status_date: "2025-01-09", test_date: "2023-11-02" },
  ];
  db.idleWells = [
    {
      api_number: "00312345",
      well_no: "1",
      lease_name: "SMITH A",
      lease_number: "12345",
      oil_gas_code: "O",
      district: "08",
      county_name: "ANDREWS",
      operator_number: "111111",
      operator_name: "ALPHA OIL",
      well_type_name: "SHUT IN",
      inact_yrs: 2,
      inact_mos: 3,
      flagged: true,
    },
  ];
  db.pluggedWells = [
    {
      api_number: "00344444",
      well_no: "4",
      lease_name: "SMITH A",
      county_name: "ANDREWS",
      field_name: "SPRABERRY",
      operator_number: "111111",
      operator_name: "ALPHA OIL",
      api_depth: 9000,
    },
  ];
  db.plugSummary = [
    {
      api_number: "00344444",
      plug_date: "2022-04-18",
      total_depth: 9000,
      shallowest_plug_top: 6000,
      plugs: 4,
      cement_sacks: 200,
      state_funded: true,
    },
  ];
  db.perfs = [{ api_number: "00344444", top_ft: 5000, bottom_ft: 5200 }];
  db.formations = [{ api_no: "00344444", formation: "WOLFCAMP", depth: 8200 }];
  db.boltOn = [
    {
      oil_gas_code: "O",
      district: "08",
      lease_number: "77777",
      lease_name: "NEIGHBOR C",
      operator_number: "222222",
      operator_name: "BETA RESOURCES",
      survey_name: "T & P RR CO",
      block_number: "A-34",
      abstract_label: "A-341",
      shared: true,
      wells: 3,
    },
  ];
  db.officers = [
    { officer_name: "J R EWING", operator_number: "111111", officer_title: "PRESIDENT" },
    { officer_name: "J R EWING", operator_number: "222222", officer_title: "DIRECTOR" },
  ];
  db.w10 = [
    { test_date: "2022-01-05", well_no: "1", daily_oil: 90, daily_water: 10 },
    { test_date: "2022-07-05", well_no: "1", daily_oil: 80, daily_water: 20 },
    { test_date: "2024-01-05", well_no: "1", daily_oil: 60, daily_water: 40 },
    { test_date: "2024-07-05", well_no: "1", daily_oil: 40, daily_water: 60 },
  ];
  db.uicPermits = [
    {
      uic_no: "UIC-1",
      approved_date: "2018-06-06",
      max_bbl_per_day: 10000,
      max_inj_pressure: 1200,
      is_commercial: true,
    },
  ];
  db.liabilityReasons = [
    {
      flagged: 10,
      h15_delinquent: 4,
      pollution: 1,
      mechanical_integrity: 2,
      plugging_order: 0,
      district_state_plugging: 1,
      surface_violations: 3,
      w3x_violations: 0,
    },
  ];
  db.liabilityIdle = [
    {
      api_number: "00355555",
      well_no: "3",
      lease_name: "JONES B",
      well_type_name: "SHUT IN",
      inact_yrs: 7,
      inact_mos: 1,
      flagged: true,
    },
  ];
  db.sellerFlagged = [
    {
      api_number: "00312345",
      lease_name: "SMITH A",
      modified_dt: "2024-11-02",
      reasons: ["H-15 delinquent", "Pollution"],
    },
  ];
  db.unfiledMonths = [{ cycle: "2025-03" }, { cycle: "2024-12" }];
  db.uncoded = [{ wells: 8 }];
  db.depth = [{ wells: 34, total_ft: 300000, deepest: 11000 }];
  db.obligationInactive = [
    { api_number: "00355555", lease_name: "JONES B", inact_yrs: 3, inact_mos: 2, flagged: true },
  ];
  db.series.set("O/10/12345", decliningLease("2022-07", 36));
  db.series.set("O/10/77777", decliningLease("2022-07", 36));

  q.p4.set("O/10/12345", {
    connections: [
      {
        product_code: "O",
        type_code: "H",
        gpn_no: "333333",
        operator_name: "GAMMA CRUDE",
        actual_percent: 1,
        effective_date: "2024-09-01",
        interstate: false,
        intrastate: true,
      },
    ],
    filings: [
      {
        effective_date: "2024-09-01",
        approval_date: "2024-10-01",
        record_type: "R",
        operator_no: "222222",
        operator_name: "BETA RESOURCES",
        field_no: "1234",
        changes: ["Operator", "Purchaser"],
      },
      {
        effective_date: "2019-03-01",
        approval_date: "2019-04-02",
        record_type: "O",
        operator_no: "111111",
        operator_name: "ALPHA OIL",
        field_no: "1234",
        changes: ["Lease name"],
      },
    ],
  });
  q.operatorH15 = { wellsTested: 20, delinquent: 4, dueSoon: 2, lastTest: "2025-01-01" };
  q.operatorDisposal = {
    wells: 2,
    commercialWells: 1,
    permittedBblPerDay: 10000,
    injectedBbl12m: 1_000_000,
    lastReported: "2024-08",
    reportedThrough: "2024-08",
  };
  q.disposal = [
    {
      uic_no: "UIC-1",
      api_number: "00312345",
      lease_name: "SMITH A",
      inj_type: "2",
      is_commercial: true,
      max_bbl_per_day: 10000,
      utilisation: 0.4,
    },
  ];
  q.network = {
    operator_number: "111111",
    operator_name: "ALPHA OIL",
    p5_status: "D",
    officers: [{ officer_name: "J R EWING", officer_title: "PRESIDENT" }],
    related: [
      {
        officer_name: "J R EWING",
        operator_number: "222222",
        operator_name: "BETA RESOURCES",
        p5_status: "A",
      },
    ],
  };
}

/** Arguments that give every tool something real to answer. */
const RICH_CALLS: [string, Record<string, unknown>][] = [
  ["rrc_acquisition_screen", { county: "Andrews", max_decline_pct_per_yr: 99 }],
  ["rrc_distress_signal", { operators: ["111111"] }],
  ["rrc_idle_with_reserves", { operator_no: "111111" }],
  ["rrc_reentry_screen", { operator_no: "111111" }],
  ["rrc_bolt_on", { operator_no: "111111", include_adjacent: true }],
  ["rrc_transaction_history", { operator_no: "111111" }],
  ["rrc_operator_exit", { operators: ["111111"] }],
  ["rrc_estate_map", { operator_no: "111111", as_of: "2026-01-01" }],
  [
    "rrc_package_value_drivers",
    { oil_gas_code: "O", district_no: "10", lease_no: "12345", operator_no: "111111" },
  ],
  ["rrc_liability_check", { operator_no: "111111" }],
  [
    "rrc_why_selling",
    { oil_gas_code: "O", district_no: "10", lease_no: "12345", operator_no: "111111" },
  ],
  [
    "rrc_seller_asymmetry",
    { operator_no: "111111", oil_gas_code: "O", district_no: "10", lease_no: "12345" },
  ],
  ["rrc_obligation_calendar", { operator_no: "111111", as_of: "2026-03-15" }],
];

/**
 * A key that names money, on a NUMBER.
 *
 * Only numbers, because prose is allowed to say the record carries no prices,
 * and that sentence is the point rather than a violation.
 */
const MONEY_KEY =
  /(price|cost|usd|dollar|payout|npv|\birr\b|profit|revenue|margin|valuation|worth|_per_boe|per_barrel_[a-z]*(cost|price))/i;

function walkNumbers(value: unknown, path: string, seen: string[]): void {
  if (value === null || value === undefined) return;
  if (typeof value === "number") {
    if (MONEY_KEY.test(path.split(".").pop() ?? "")) seen.push(path);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((v, i) => walkNumbers(v, `${path}.${i}`, seen));
    return;
  }
  if (typeof value === "object") {
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      walkNumbers(v, `${path}.${k}`, seen);
    }
  }
}

describe("no tool emits money", () => {
  beforeEach(loadRichFixture);

  test("every tool answers the rich fixture, so this sweep is over real output", async () => {
    for (const [name, args] of RICH_CALLS) {
      const r = await call(name, args);
      expect(r.ok, `${name}: ${r.error ?? ""}`).toBe(true);
    }
    expect(RICH_CALLS.map(([n]) => n)).toEqual(EXPECTED_TOOLS);
  });

  test("no numeric field in any result is named as a price, cost or valuation", async () => {
    const offenders: string[] = [];
    for (const [name, args] of RICH_CALLS) {
      walkNumbers(await call(name, args), name, offenders);
    }
    expect(offenders).toEqual([]);
  });

  test("no serialized result contains a currency mark", async () => {
    for (const [name, args] of RICH_CALLS) {
      const json = JSON.stringify(await call(name, args));
      expect(json, name).not.toContain("$");
      expect(json, name).not.toMatch(/\bUSD\b/);
      expect(json, name).not.toMatch(/\d\s*(dollars|per barrel of oil)/i);
    }
  });

  test("the tools that size a package say in their own output that they do not value one", async () => {
    const sizing = await call("rrc_package_value_drivers", {
      oil_gas_code: "O",
      district_no: "10",
      lease_no: "12345",
      operator_no: "111111",
    });
    expect(sizing.does_not_value).toMatch(/does not value one/);
    expect(sizing.notes.join(" ")).toMatch(/It is NOT a cost/);

    // And the plugging burden is stated in FEET, which is the physical size of
    // the obligation and the only unit this record supports.
    expect(sizing.plugging_burden.total_unplugged_depth_ft).toBe(300000);
  });

  test("every tool carries the no-price and lag caveats where they apply", async () => {
    for (const [name, args] of RICH_CALLS) {
      const r = await call(name, args);
      const text = JSON.stringify(r.notes ?? []) + (r.does_not_value ?? "");
      expect(text, name).toMatch(/no prices|carries no price|does not value/i);
    }
  });
});
