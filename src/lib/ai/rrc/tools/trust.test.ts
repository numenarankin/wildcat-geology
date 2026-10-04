import { beforeEach, describe, expect, test, vi } from "vitest";

import type { LeaseMonth } from "../../../scout/rrc-types";

/**
 * Provenance and coverage, against fixtures with a known hole in them.
 *
 * The point of these four tools is to say what the record does NOT show, so
 * every test here plants an absence and checks that it is counted: unfiled
 * lease-months, wells with no coordinate, a target key that resolves to
 * nothing. A coverage tool that quietly reports full coverage is worse than no
 * coverage tool, because it is believed.
 */

const db = vi.hoisted(() => ({
  edge: { reported: "2024-12", loaded: "2025-03" },
  injectionEdge: { reported: "2024-01", loaded: "2025-03" },
  leases: new Map<string, unknown>(),
  operators: new Map<string, unknown>(),
  wells: new Map<string, unknown>(),
  countyRows: [] as unknown[],
  operatorFilingRows: [] as unknown[],
  queries: [] as string[],
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string) => {
    db.queries.push(sql);
    if (sql.includes("rrc.lease_production")) return db.operatorFilingRows;
    if (sql.includes("rrc.wellbore")) return db.countyRows;
    return [];
  },
  rrcQueryOne: async () => null,
  rrcQuerySlow: async () => [],
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getCycleEdge: async () => db.edge,
  getInjectionEdge: async () => db.injectionEdge,
  getLeaseDossier: async (ogc: string, dist: string, lease: string) =>
    db.leases.get(`${ogc}/${dist}/${lease}`) ?? null,
  getOperatorDossier: async (op: string) => db.operators.get(op) ?? null,
  getWellDossier: async (api: string) => db.wells.get(api) ?? null,
  getOperatorNetwork: async () => null,
  getFieldProfile: async () => null,
  getCountyProfile: async () => null,
  getProductionTrend: async () => [],
  findDisposal: async () => [],
  findWells: async () => [],
  getWellInjection: async () => null,
  listPermits: async () => [],
  resolveCounty: (ref: string) => (ref ? { county_no: "003", county_name: "ANDREWS" } : null),
}));

const { TOOLS } = await import("./trust");

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Result = any;

const call = async (name: string, args: Record<string, unknown>): Promise<Result> => {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`No tool ${name}. Have: ${TOOLS.map((t) => t.name).join(", ")}`);
  return (await tool.run(tool.args.parse(args) as never)) as Result;
};

// ------------------------------------------------------------------ fixtures

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

/** A lease at a flat daily rate, with three months nobody filed. */
function plantedLease(key: string, missing: string[], rate = 100) {
  const [ogc, dist, no] = key.split("/");
  const monthly = cycles("2024-01", 12).map((c) =>
    missing.includes(c)
      ? month(c, { oil_prod_vol: 0, prod_report_filed: "N" })
      : month(c, { oil_prod_vol: rate * days(c) })
  );
  db.leases.set(key, {
    oil_gas_code: ogc,
    district_no: dist,
    lease_no: no,
    lease_name: "PLANTED LEASE",
    field_no: "0001",
    field_name: "SPRABERRY",
    operator_no: "123456",
    operator_name: "TEST OPERATOR",
    off_schedule: false,
    severance: false,
    monthly,
    counties: [{ county_no: "003", county_name: "ANDREWS" }],
    wells: [
      { api_number: "42003000010000", well_no: "1", lat: 32, lon: -102 },
      { api_number: "42003000020000", well_no: "2", lat: 32.01, lon: -102 },
      { api_number: "42003000030000", well_no: "3", lat: null, lon: null },
      { api_number: "42003000040000", well_no: "4", lat: null, lon: null },
      { api_number: "42003000050000", well_no: "5", lat: 32.02, lon: -102 },
    ],
    p4: { connections: [], filings: [] },
  });
  return { oil_gas_code: ogc, district_no: dist, lease_no: no };
}

beforeEach(() => {
  db.edge = { reported: "2024-12", loaded: "2025-03" };
  db.injectionEdge = { reported: "2024-01", loaded: "2025-03" };
  db.leases.clear();
  db.operators.clear();
  db.wells.clear();
  db.countyRows = [];
  db.operatorFilingRows = [];
  db.queries = [];
});

// ------------------------------------------------------------------ 70

describe("rrc_provenance", () => {
  test("traces the latest reported number to its filing and cycle", async () => {
    const key = plantedLease("O/08/12345", []);
    const r = await call("rrc_provenance", key);
    expect(r.ok).toBe(true);
    expect(r.cycle).toBe("2024-12");
    // 100 bbl/d across December's 31 days.
    expect(r.value).toBe(3100);
    expect(r.daily_rate).toBeCloseTo(100, 10);
    expect(r.basis).toBe("filed");
    expect(r.source.table).toBe("rrc.lease_production");
    expect(r.source.form).toContain("Form PR");
    expect(r.source.key).toEqual({ oil_gas_code: "O", district_no: "08", lease_no: "12345", cycle: "2024-12" });
    // The mirror is loaded three cycles past what the RRC has published.
    expect(r.reporting_edge.production_reported_through).toBe("2024-12");
    expect(r.reporting_edge.cycles_behind).toBe(3);
  });

  test("an unfiled cycle is labelled not filed, never as a zero measurement", async () => {
    const key = plantedLease("O/08/12346", ["2024-06"]);
    const r = await call("rrc_provenance", { ...key, cycle: "2024-06" });
    expect(r.ok).toBe(true);
    expect(r.value).toBe(0);
    expect(r.basis).toBe("not filed");
    expect(r.caveats.join(" ")).toContain("absence of paperwork");
  });

  test("a cycle outside the record refuses and says what the record holds", async () => {
    const key = plantedLease("O/08/12347", []);
    const r = await call("rrc_provenance", { ...key, cycle: "1999-01" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("2024-01");
    expect(r.error).toContain("2024-12");
  });
});

// ------------------------------------------------------------------ 71

describe("rrc_coverage", () => {
  test("reports the missing lease-months planted in the fixture", async () => {
    // Three of twelve published months were never filed.
    const key = plantedLease("O/08/55555", ["2024-03", "2024-07", "2024-11"]);
    const r = await call("rrc_coverage", { scope: "lease", ...key });
    expect(r.ok).toBe(true);
    expect(r.production.reported_months).toBe(12);
    expect(r.production.missing_months).toBe(3);
    expect(r.production.missing_share).toBeCloseTo(0.25, 10);
    expect(r.production.missing_cycles).toEqual(["2024-03", "2024-07", "2024-11"]);
    expect(r.caveats[0]).toContain("3 of 12");
  });

  test("counts the wells that can never appear in a radius search", async () => {
    const key = plantedLease("O/08/55556", []);
    const r = await call("rrc_coverage", { scope: "lease", ...key });
    expect(r.wells).toBe(5);
    expect(r.wells_without_coordinates).toBe(2);
    expect(r.wells_without_coordinates_share).toBeCloseTo(0.4, 10);
    expect(r.wells_missing_coordinates.map((w: Result) => w.well_no)).toEqual(["3", "4"]);
    // Both reporting lags travel with every coverage answer.
    expect(r.lags.production_lag_months).toBe(3);
    expect(r.lags.h10_lag_months).toBe(14);
  });

  test("a clean lease says so rather than staying silent", async () => {
    const key = plantedLease("O/08/55557", []);
    const r = await call("rrc_coverage", { scope: "lease", ...key });
    expect(r.production.missing_months).toBe(0);
    expect(r.caveats[0]).toContain("Every published cycle");
  });

  test("county scope counts wells with no coordinate and no completion date", async () => {
    db.countyRows = [{ wells: 200, no_coords: 25, no_completion: 40 }];
    const r = await call("rrc_coverage", { scope: "county", county: "ANDREWS" });
    expect(r.ok).toBe(true);
    expect(r.wells_without_coordinates).toBe(25);
    expect(r.wells_without_coordinates_share).toBeCloseTo(0.125, 10);
    expect(r.wells_without_completion_date).toBe(40);
    expect(r.caveats.join(" ")).toContain("25 of 200");
    // The survey table has no county column at all: a standing blind spot.
    expect(r.caveats.join(" ")).toContain("NO county column");
  });

  test("lease scope refuses without the keys a lease needs", async () => {
    const r = await call("rrc_coverage", { scope: "lease", district_no: "08" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("oil_gas_code");
  });
});

// ------------------------------------------------------------------ 72

describe("rrc_target_list", () => {
  test("ranks by score, classifies each key, and carries the arguments to reopen it", async () => {
    const r = await call("rrc_target_list", {
      title: "Screen",
      items: [
        { key: "O/08/12345", label: "ALPHA", score: 10, metrics: { bopd: 100 } },
        { key: "42003000010000", label: "BRAVO", score: 30, metrics: { bopd: 300 } },
        { key: "123456", label: "CHARLIE", score: 20, metrics: { bopd: 200 } },
      ],
    });
    expect(r.ok).toBe(true);
    expect(r.rows.map((x: Result) => x.label)).toEqual(["BRAVO", "CHARLIE", "ALPHA"]);
    expect(r.rows.map((x: Result) => x.rank)).toEqual([1, 2, 3]);
    expect(r.rows.map((x: Result) => x.kind)).toEqual(["well", "operator", "lease"]);
    expect(r.rows[2].reopen).toEqual({
      entity: "lease",
      oil_gas_code: "O",
      district_no: "08",
      lease_no: "12345",
    });
    expect(r.rows[0].reopen).toEqual({ entity: "well", api: "42003000010000" });
    expect(r.csv.split("\n")[0]).toBe("rank,key,kind,label,score,bopd");
    expect(r.csv.split("\n")).toHaveLength(4);
  });

  test("a row missing the sort key ranks last rather than as a zero", async () => {
    const r = await call("rrc_target_list", {
      items: [
        { key: "O/08/1", label: "NO SCORE" },
        { key: "O/08/2", label: "LOW", score: -5 },
        { key: "O/08/3", label: "HIGH", score: 5 },
      ],
    });
    expect(r.rows.map((x: Result) => x.label)).toEqual(["HIGH", "LOW", "NO SCORE"]);
  });

  test("an unrecognised key is passed through, named, and given no reopen arguments", async () => {
    const r = await call("rrc_target_list", { items: [{ key: "not a key", score: 1 }] });
    expect(r.rows[0].kind).toBe("unknown");
    expect(r.rows[0].reopen).toBeNull();
    expect(r.unrecognised_keys).toEqual(["not a key"]);
  });

  test("a cut list is marked truncated", async () => {
    const r = await call("rrc_target_list", {
      items: Array.from({ length: 5 }, (_v, i) => ({ key: `O/08/${i}`, score: i })),
      limit: 2,
    });
    expect(r.rows).toHaveLength(2);
    expect(r.total_items).toBe(5);
    expect(r.truncated).toBe(true);
  });
});

// ------------------------------------------------------------------ 73

describe("rrc_case_file", () => {
  test("re-reads each target and measures the change since a stated cycle", async () => {
    // 100 bbl/d through June, then half that.
    const monthly = cycles("2024-01", 12).map((c) =>
      month(c, { oil_prod_vol: (c <= "2024-06" ? 100 : 50) * days(c) })
    );
    db.leases.set("O/08/77777", {
      lease_name: "CASE LEASE",
      operator_name: "TEST OPERATOR",
      field_name: "SPRABERRY",
      off_schedule: false,
      severance: true,
      monthly,
      wells: [{ api_number: "42003000010000" }],
      counties: [],
      p4: { connections: [], filings: [] },
    });

    const r = await call("rrc_case_file", {
      title: "Andrews review",
      targets: [{ key: "O/08/77777", note: "watch the severance flag" }, { key: "O/08/99999" }],
      checked: ["rrc_decline", "rrc_not_a_tool"],
      since: "2024-01",
    });

    expect(r.ok).toBe(true);
    const target = r.targets[0];
    expect(target.found).toBe(true);
    expect(target.note).toBe("watch the severance flag");
    expect(target.severance).toBe(true);
    expect(target.latest_cycle).toBe("2024-12");
    expect(target.latest_oil_bbl_per_day).toBeCloseTo(50, 10);
    expect(target.since_oil_bbl_per_day).toBeCloseTo(100, 10);
    // 50 against 100 is a halving.
    expect(target.change).toBeCloseTo(-0.5, 10);
    expect(r.movers[0].key).toBe("O/08/77777");

    // A target that resolves to nothing is named, not dropped.
    expect(r.missing).toEqual(["O/08/99999"]);
    expect(r.found).toBe(1);

    // Checked tools are validated against the live catalog.
    expect(r.checked).toEqual([
      { name: "rrc_decline", is_catalog_tool: true },
      { name: "rrc_not_a_tool", is_catalog_tool: false },
    ]);
  });

  test("refuses a malformed since cycle", async () => {
    const r = await call("rrc_case_file", { title: "x", targets: [{ key: "O/08/1" }], since: "last June" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("since");
  });

  test("stores nothing: the same call twice returns the same case file", async () => {
    plantedLease("O/08/88888", []);
    const args = { title: "Repeat", targets: [{ key: "O/08/88888" }] };
    const a = await call("rrc_case_file", args);
    const b = await call("rrc_case_file", args);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
    expect(a.notes[0]).toContain("STATELESS");
  });
});
