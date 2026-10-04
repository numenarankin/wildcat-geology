import { beforeEach, describe, expect, test, vi } from "vitest";

/**
 * The intelligence catalog, against fixtures whose right answer is computed
 * here by hand rather than by the code under test.
 *
 * Five properties carry the weight, and each is a wrong answer with a real cost
 * behind it:
 *
 *  1. A LINK IS SCORED BY WHAT IT SHOWS. A shared officer name AND a shared
 *     mailing address has to outrank a shared surname by a wide margin, or the
 *     graph tools launder a coincidence into a corporate family.
 *  2. THE GRAPH IS CYCLIC. Officer edges loop, so a path search that does not
 *     hold a visited set runs until the pool times out.
 *  3. THE FILING-PATTERN TOOLS MUST NOT ACCUSE. They return dates and filings.
 *     A single evaluative word in the payload is a conclusion the record
 *     cannot support, and the model will repeat it.
 *  4. INTENT COMES FROM THE PENDING QUEUE. Reading the issued-permit master
 *     instead answers a question that is weeks later and has no coordinates.
 *  5. AN UNFILTERED CALL IS REFUSED. rrc.permit alone is 950,665 rows behind a
 *     5 s statement timeout, so a statewide scan must fail fast and say so.
 */

const db = vi.hoisted(() => ({
  queries: [] as { sql: string; params: unknown[] }[],
  operators: [] as Record<string, unknown>[],
  officers: [] as { operator_number: string; officer_name: string; officer_title: string | null }[],
  completions: [] as Record<string, unknown>[],
  formations: [] as Record<string, unknown>[],
  wellbores: [] as Record<string, unknown>[],
  perfs: [] as Record<string, unknown>[],
  casing: [] as Record<string, unknown>[],
  plugs: [] as Record<string, unknown>[],
  h15: [] as Record<string, unknown>[],
  permits: [] as Record<string, unknown>[],
  pendingActivity: [] as Record<string, unknown>[],
  leases: [] as Record<string, unknown>[],
  leaseMonths: [] as Record<string, unknown>[],
  operatorProduction: [] as Record<string, unknown>[],
  p4Gatherer: [] as Record<string, unknown>[],
  p4Filing: [] as Record<string, unknown>[],
  uic: [] as Record<string, unknown>[],
  // Module-level helpers, mocked as themselves rather than as SQL.
  pendingQueue: [] as Record<string, unknown>[],
  approvedPermits: [] as Record<string, unknown>[],
  listPermits: [] as Record<string, unknown>[],
  wells: [] as Record<string, unknown>[],
  disposal: [] as Record<string, unknown>[],
  cycleEdge: "2026-03",
  /** Set to make any read of the approved-permit master a test failure. */
  banPermitReads: false,
}));

const norm = (v: unknown) => String(v ?? "").trim();
const key = (s: unknown) => String(s ?? "").replace(/[^A-Za-z0-9]/g, "").toUpperCase();
const digits = (s: unknown) => String(s ?? "").replace(/\D/g, "");

/**
 * The SQL router.
 *
 * Deliberately dumb: each branch returns the fixture rows a tool's own SQL
 * would have returned, with only the filtering the assertion depends on. It
 * does NOT reimplement Postgres, so no test below asserts a value that the
 * database would have computed.
 */
vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string, params: unknown[] = []) => {
    db.queries.push({ sql, params });
    if (db.banPermitReads && sql.includes("rrc.permit")) {
      throw new Error("this tool must not read the approved-permit master");
    }

    if (sql.includes("count(distinct operator_number)::int as n")) {
      const names = params[0] as string[];
      return names.map((officer_name) => ({
        officer_name,
        n: new Set(
          db.officers.filter((o) => o.officer_name === officer_name).map((o) => o.operator_number)
        ).size,
      }));
    }
    if (sql.includes("rrc.operator_officers")) {
      if (sql.includes("officer_name ilike any")) {
        const patterns = (params[0] as string[]).map((p) => p.replace("%", ""));
        return db.officers.filter(
          (o) =>
            norm(o.operator_number) !== norm(params[1]) &&
            patterns.some((p) => o.officer_name.startsWith(p))
        );
      }
      if (sql.includes("officer_name = any($1::text[])")) {
        const names = params[0] as string[];
        return db.officers.filter(
          (o) => names.includes(o.officer_name) && norm(o.operator_number) !== norm(params[1])
        );
      }
      return db.officers.filter((o) => norm(o.operator_number) === norm(params[0]));
    }
    // `from rrc.operators`, not `rrc.operators`: half the reads in this file
    // join the operator table for a name and must not be answered from it.
    if (sql.includes("from rrc.operators")) {
      if (sql.includes("org_date >= $1")) {
        return db.operators.filter((o) => String(o.org_date ?? "") >= String(params[0]));
      }
      if (sql.includes("= any($1::bpchar[])")) {
        const wanted = (params[0] as string[]).map(norm);
        return db.operators.filter((o) => wanted.includes(norm(o.operator_number)));
      }
      if (sql.includes("operator_number <> $1::bpchar")) {
        const [, addr, phone, zip] = params as string[];
        return db.operators.filter(
          (o) =>
            norm(o.operator_number) !== norm(params[0]) &&
            ((addr !== "" && key(o.addr1) === addr) ||
              (phone !== "" && digits(o.phone1) === phone) ||
              (zip !== "" && digits(o.zip1).slice(0, 5) === zip))
        );
      }
      return db.operators.filter((o) => norm(o.operator_number) === norm(params[0]));
    }
    if (sql.includes("rrc.completion_formation")) {
      const ids = params[0] as string[];
      return db.formations.filter((f) => ids.includes(String(f.tracking_no)));
    }
    if (sql.includes("rrc.completion")) {
      if (sql.includes("api_no = any($1::text[])")) {
        const apis = (params[0] as string[]).map(norm);
        return db.completions.filter((c) => apis.includes(norm(c.api_no)));
      }
      if (sql.includes("where field_no = $1")) {
        return db.completions.filter((c) => norm(c.field_no) === norm(params[0]));
      }
      if (sql.includes("where county = $1") || sql.includes("where c.county = $1")) {
        return db.completions.filter((c) => norm(c.county) === norm(params[0]));
      }
      return db.completions.filter((c) => norm(c.operator_no) === norm(params[0]));
    }
    if (sql.includes("rrc.wb_perf")) return db.perfs;
    if (sql.includes("rrc.wb_casing")) return db.casing;
    if (sql.includes("rrc.wb_plug_summary")) return db.plugs;
    if (sql.includes("rrc.wb_h15")) return db.h15;
    if (sql.includes("rrc.wellbore")) {
      if (sql.includes("ltrim(btrim(recent_permit), '0')")) {
        const strip = (v: unknown) => norm(v).replace(/^0+/, "");
        const wanted = (params[0] as string[]).map(strip);
        return db.wellbores
          .filter((w) => wanted.includes(strip(w.recent_permit)))
          .map((w) => ({ recent_permit: strip(w.recent_permit) }));
      }
      if (sql.includes("= any($1::bpchar[])")) {
        const wanted = (params[0] as string[]).map(norm);
        return db.wellbores.filter((w) => wanted.includes(norm(w.operator_number)));
      }
      return db.wellbores;
    }
    if (sql.includes("rrc.pending_activity")) return db.pendingActivity;
    if (sql.includes("rrc.permit")) return db.permits;
    if (sql.includes("rrc.lease_production")) return db.leaseMonths;
    if (sql.includes("rrc.lease")) return db.leases;
    if (sql.includes("rrc.operator_production")) return db.operatorProduction;
    if (sql.includes("rrc.p4_gatherer")) return db.p4Gatherer;
    if (sql.includes("rrc.p4_filing")) return db.p4Filing;
    if (sql.includes("rrc.uic_permit")) return db.uic;
    throw new Error(`unexpected query: ${sql.slice(0, 80)}`);
  },
  rrcQueryOne: async (sql: string, params: unknown[] = []) => {
    db.queries.push({ sql, params });
    if (sql.includes("from rrc.operators")) {
      return db.operators.find((o) => norm(o.operator_number) === norm(params[0])) ?? null;
    }
    if (sql.includes("rrc.operator_production")) {
      const cycles = db.operatorProduction
        .filter((p) => norm(p.operator_no) === norm(params[0]))
        .map((p) => String(p.cycle))
        .sort();
      return { first_cycle: cycles[0] ?? null, first: cycles[0] ?? null, last: cycles.at(-1) ?? null };
    }
    if (sql.includes("rrc.p4_filing")) {
      const rows = db.p4Filing.filter((f) => norm(f.operator_no) === norm(params[0]));
      const dates = rows.map((r) => String(r.effective_date)).sort();
      return { n: rows.length, first: dates[0] ?? null, last: dates.at(-1) ?? null };
    }
    if (sql.includes("rrc.wellbore")) {
      return { n: db.wellbores.filter((w) => norm(w.operator_number) === norm(params[0])).length };
    }
    if (sql.includes("rrc.wb_h15")) {
      const rows = db.h15.filter((h) => norm(h.operator_no) === norm(params[0]));
      const dates = rows.map((r) => String(r.status_date)).sort();
      return { n: rows.length, first: dates[0] ?? null, last: dates.at(-1) ?? null };
    }
    if (sql.includes("rrc.wb_plug_summary")) {
      const dates = db.plugs.map((p) => String(p.plug_date)).sort();
      return { n: db.plugs.length, first: dates[0] ?? null, last: dates.at(-1) ?? null };
    }
    throw new Error(`unexpected single-row query: ${sql.slice(0, 80)}`);
  },
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  resolveCounty: (ref: string) => {
    const table: Record<string, { county_no: string; county_name: string }> = {
      andrews: { county_no: "003", county_name: "ANDREWS" },
      "003": { county_no: "003", county_name: "ANDREWS" },
      crane: { county_no: "103", county_name: "CRANE" },
    };
    return table[ref.trim().toLowerCase()] ?? null;
  },
  getCycleEdge: async () => ({ reported: db.cycleEdge, loaded: db.cycleEdge }),
  getPendingQueue: async () => db.pendingQueue,
  getApprovedPermits: async () => db.approvedPermits,
  listPermits: async (f: unknown) => {
    if (db.banPermitReads) throw new Error("this tool must not read the approved-permit master");
    db.queries.push({ sql: "listPermits(rrc.permit)", params: [f] });
    return db.listPermits;
  },
  findWells: async () => db.wells,
  findDisposal: async () => db.disposal,
  getOperatorDisposal: async () => ({
    wells: db.disposal.length,
    commercialWells: db.disposal.filter((d) => d.is_commercial).length,
    permittedBblPerDay: null,
    injectedBbl12m: null,
    lastReported: null,
    reportedThrough: "2025-06",
  }),
  getOperatorDossier: async () => null,
  getCountyProfile: async () => null,
}));

const { TOOLS } = await import("./intel");

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Result = any;

const find = (name: string) => {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`No tool ${name}. Have: ${TOOLS.map((t) => t.name).join(", ")}`);
  return tool;
};

const call = async (name: string, args: Record<string, unknown>): Promise<Result> =>
  (await find(name).run(find(name).args.parse(args) as never)) as Result;

/** Straight to the function, past the schema, for the guards it owns itself. */
const callRaw = async (name: string, args: Record<string, unknown>): Promise<Result> =>
  (await find(name).run(args as never)) as Result;

beforeEach(() => {
  db.queries = [];
  db.operators = [];
  db.officers = [];
  db.completions = [];
  db.formations = [];
  db.wellbores = [];
  db.perfs = [];
  db.casing = [];
  db.plugs = [];
  db.h15 = [];
  db.permits = [];
  db.pendingActivity = [];
  db.leases = [];
  db.leaseMonths = [];
  db.operatorProduction = [];
  db.p4Gatherer = [];
  db.p4Filing = [];
  db.uic = [];
  db.pendingQueue = [];
  db.approvedPermits = [];
  db.listPermits = [];
  db.wells = [];
  db.disposal = [];
  db.cycleEdge = "2026-03";
  db.banPermitReads = false;
});

// --------------------------------------------------------------- fixtures

function operator(
  no: string,
  extra: Record<string, unknown> = {}
): Record<string, unknown> {
  return {
    operator_number: no,
    operator_name: `OPERATOR ${no}`,
    p5_status: "A",
    org_date: "2000-01-01",
    last_p5_date: "2026-01-01",
    addr1: null,
    city1: null,
    state1: null,
    zip1: null,
    phone1: null,
    ...extra,
  };
}

// ----------------------------------------------------------- the catalog

describe("catalog", () => {
  test("every tool is uniquely named and summarised in one line", () => {
    const names = TOOLS.map((t) => t.name);
    expect(new Set(names).size).toBe(names.length);
    for (const tool of TOOLS) {
      expect(tool.name.startsWith("rrc_")).toBe(true);
      expect(tool.summary).not.toContain("\n");
      expect(tool.summary.length).toBeGreaterThan(20);
    }
  });
});

// ------------------------------------------------- 55 entity resolution

describe("rrc_entity_resolve", () => {
  /**
   * The subject shares BOTH an officer name and a mailing address with 200000,
   * and only a surname with 300000.
   *
   * Hand-computed from the asserted weights: officer 0.5 + address 0.3 = 0.80
   * against surname 0.10, an eight-to-one ordering that has to survive any
   * change to the scoring.
   */
  beforeEach(() => {
    db.operators = [
      operator("100000", { addr1: "123 Main St.", zip1: "797011234", phone1: "(432) 555-0100" }),
      operator("200000", { addr1: "123 MAIN ST", zip1: "797011234", phone1: null }),
      operator("300000", { addr1: "9 Elsewhere Blvd", zip1: "770020000", phone1: null }),
    ];
    db.officers = [
      { operator_number: "100000", officer_name: "ROE, JANE Q", officer_title: "PRESIDENT" },
      { operator_number: "200000", officer_name: "ROE, JANE Q", officer_title: "MEMBER" },
      { operator_number: "300000", officer_name: "ROE, ROBERT", officer_title: "PRESIDENT" },
    ];
  });

  test("an officer and an address outrank a shared surname", async () => {
    const r = await call("rrc_entity_resolve", { operator_no: "100000" });
    expect(r.ok).toBe(true);

    const strong = r.candidates.find((c: Result) => c.operator_number === "200000");
    const weak = r.candidates.find((c: Result) => c.operator_number === "300000");

    // 0.5 (officer name, filed on 2 operators) + 0.3 (same mailing address).
    expect(strong.confidence).toBeCloseTo(0.8, 10);
    expect(strong.signals.map((s: Result) => s.signal).sort()).toEqual([
      "mailing address",
      "officer name",
    ]);
    // Surname only, and nothing else.
    expect(weak.confidence).toBeCloseTo(0.1, 10);
    expect(weak.signals).toHaveLength(1);
    expect(weak.signals[0].signal).toBe("surname only");

    expect(strong.confidence).toBeGreaterThan(weak.confidence * 5);
    expect(r.candidates[0].operator_number).toBe("200000");
  });

  test("a name filed on many operators is discounted to the common weight", async () => {
    // Eleven operators carry the name in total, one past the threshold of ten.
    for (let i = 1; i <= 9; i += 1) {
      const no = `40000${i}`;
      db.operators.push(operator(no));
      db.officers.push({
        operator_number: no,
        officer_name: "ROE, JANE Q",
        officer_title: "AGENT",
      });
    }
    const r = await call("rrc_entity_resolve", { operator_no: "100000" });
    const strong = r.candidates.find((c: Result) => c.operator_number === "200000");
    // 0.15 (common name) + 0.3 (address), NOT 0.8.
    expect(strong.confidence).toBeCloseTo(0.45, 10);
    expect(strong.signals.some((s: Result) => s.signal === "officer name, common")).toBe(true);
    expect(r.officers[0].operators_with_this_name).toBe(11);
  });

  test("confidence never reaches certainty and the lead caveat is attached", async () => {
    const r = await call("rrc_entity_resolve", { operator_no: "100000" });
    for (const c of r.candidates) expect(c.confidence).toBeLessThanOrEqual(0.95);
    expect(r.notes.join(" ")).toMatch(/LEAD TO CHECK/);
  });

  test("an unknown operator is refused rather than answered empty", async () => {
    const r = await call("rrc_entity_resolve", { operator_no: "999999" });
    expect(r).toEqual({ ok: false, error: "No operator 999999." });
  });
});

// ---------------------------------------------------------- 56 the path

describe("rrc_path_between", () => {
  /**
   * A cyclic officer graph: A and B share X, A and C share X, B and C share Y,
   * C and D share Z. D is two hops from A and the A-B-C triangle loops.
   */
  beforeEach(() => {
    db.operators = ["A1", "B1", "C1", "D1", "E1"].map((no) => operator(no));
    db.officers = [
      { operator_number: "A1", officer_name: "X", officer_title: null },
      { operator_number: "B1", officer_name: "X", officer_title: null },
      { operator_number: "C1", officer_name: "X", officer_title: null },
      { operator_number: "B1", officer_name: "Y", officer_title: null },
      { operator_number: "C1", officer_name: "Y", officer_title: null },
      { operator_number: "C1", officer_name: "Z", officer_title: null },
      { operator_number: "D1", officer_name: "Z", officer_title: null },
      { operator_number: "E1", officer_name: "W", officer_title: null },
    ];
  });

  test("terminates on a cycle and finds the two-hop path", async () => {
    const r = await call("rrc_path_between", {
      from_operator_no: "A1",
      to_operator_no: "D1",
      max_depth: 4,
    });
    expect(r.ok).toBe(true);
    expect(r.found).toBe(true);
    // A1 -> C1 (officer X) -> D1 (officer Z). Two hops, no third.
    expect(r.hops).toBe(2);
    expect(r.path.map((p: Result) => p.operator_no)).toEqual(["A1", "C1", "D1"]);
    expect(r.path[2].via_officer).toBe("Z");
    // Five operators exist, so a search that revisited nodes would expand more.
    expect(r.nodes_expanded).toBeLessThanOrEqual(5);
  });

  test("respects the depth cap rather than searching on", async () => {
    const r = await call("rrc_path_between", {
      from_operator_no: "A1",
      to_operator_no: "D1",
      max_depth: 1,
    });
    expect(r.ok).toBe(true);
    expect(r.found).toBe(false);
    expect(r.max_depth).toBe(1);
  });

  test("an unreachable operator terminates instead of looping the cycle", async () => {
    const r = await call("rrc_path_between", {
      from_operator_no: "A1",
      to_operator_no: "E1",
      max_depth: 6,
    });
    expect(r.found).toBe(false);
    expect(r.nodes_expanded).toBeLessThanOrEqual(5);
  });

  test("path confidence falls off with length and never asserts a relationship", async () => {
    const r = await call("rrc_path_between", {
      from_operator_no: "A1",
      to_operator_no: "D1",
      max_depth: 4,
    });
    // Two hops on names filed on 3 and 2 operators: 0.5 * 0.5.
    expect(r.path_confidence).toBeCloseTo(0.25, 10);
    expect(r.notes.join(" ")).toMatch(/LEAD TO CHECK/);
  });

  test("the same operator on both ends is refused", async () => {
    const r = await call("rrc_path_between", {
      from_operator_no: "A1",
      to_operator_no: "A1",
    });
    expect(r.ok).toBe(false);
  });
});

// ------------------------------------------------------ 57 shell detect

describe("rrc_shell_detect", () => {
  beforeEach(() => {
    db.operators = [
      operator("500000", {
        operator_name: "NEWCO ENERGY LLC",
        org_date: "2025-01-15",
        addr1: "1 Office Park",
        city1: "MIDLAND",
        state1: "TX",
        zip1: "79701",
      }),
    ];
    db.officers = [
      { operator_number: "500000", officer_name: "DOE, SAM", officer_title: "MEMBER" },
    ];
    db.wellbores = [
      {
        operator_number: "500000",
        wells: 12,
        counties: ["ANDREWS"],
        oldest_completion: "19580401",
      },
    ];
    db.p4Filing = [
      { operator_no: "500000", transfers: 3, first_transfer: "2025-03-01", last_transfer: "2025-09-01" },
    ];
  });

  test("returns dated filings, with the interval computed from them", async () => {
    const r = await call("rrc_shell_detect", { since: "2025-01-01" });
    expect(r.ok).toBe(true);
    const row = r.operators[0];
    expect(row.operator_no).toBe("500000");
    expect(row.org_date).toBe("2025-01-15");
    expect(row.officer_count).toBe(1);
    expect(row.wells_on_schedule).toBe(12);
    expect(row.first_operator_change).toBe("2025-03-01");
    // 2025-01-15 to 2025-03-01: 16 days of January, 28 of February, 1 of March.
    expect(row.days_from_registration_to_first_change).toBe(45);
    // The wells are from 1958; the company is from 2025. Both facts, separately.
    expect(row.oldest_completion_on_those_wells).toBe("1958-04-01");
  });

  test("says nothing about intent or wrongdoing anywhere in the payload", async () => {
    const r = await call("rrc_shell_detect", { since: "2025-01-01" });
    const serialized = JSON.stringify(r);
    for (const word of [
      "shell",
      "fraud",
      "fraudulent",
      "scheme",
      "suspicious",
      "suspect",
      "evade",
      "evasion",
      "dodge",
      "illegal",
      "unlawful",
      "wrongdoing",
      "bad actor",
      "sham",
      "straw",
      "abuse",
      "launder",
      "orphan",
    ]) {
      expect(serialized.toLowerCase()).not.toContain(word);
    }
    expect(r.notes.join(" ")).toMatch(/nothing here is a finding about intent or conduct/i);
  });

  test("an operator with a board of officers is not in the result", async () => {
    db.officers.push({
      operator_number: "500000",
      officer_name: "POE, ALEX",
      officer_title: "VICE PRESIDENT",
    });
    const r = await call("rrc_shell_detect", { since: "2025-01-01" });
    expect(r.operators).toHaveLength(0);
  });

  test("a malformed since is refused", async () => {
    const r = await call("rrc_shell_detect", { since: "last year" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/YYYY-MM-DD/);
  });
});

// ------------------------------------------------------- 82 intent feed

describe("rrc_intent_feed", () => {
  beforeEach(() => {
    db.banPermitReads = true;
    db.pendingQueue = [
      {
        universal_doc_no: "D1",
        status_number: "917198",
        operator_number: "073056",
        operator_name: "BIG CO",
        lease_name: "SMITH A",
        well_number: "1H",
        county_name: "ANDREWS",
        district_name: "08",
        total_depth: 11000,
        filing_purpose: "New drill",
        current_state_code: "MAP",
        submit_date: "2026-08-01",
        days_pending: 9,
        horizontal: true,
        api_sequence_number: null,
        surface_lat: 32.0,
        surface_lon: -102.0,
        location_source: "gis",
      },
      {
        universal_doc_no: "D2",
        status_number: "917200",
        operator_number: "999999",
        operator_name: "OTHER CO",
        lease_name: "JONES B",
        well_number: "2",
        county_name: "CRANE",
        district_name: "08",
        total_depth: 9000,
        filing_purpose: "Recompletion",
        current_state_code: "API",
        submit_date: "2026-07-01",
        days_pending: 40,
        horizontal: false,
        api_sequence_number: "10312345",
        surface_lat: 33.0,
        surface_lon: -102.0,
        location_source: "dms",
      },
    ];
  });

  test("reads the pending queue and never the issued-permit table", async () => {
    const r = await call("rrc_intent_feed", { county: "Andrews" });
    expect(r.ok).toBe(true);
    expect(r.applications).toHaveLength(1);
    expect(r.applications[0].universal_doc_no).toBe("D1");
    expect(r.queue_size).toBe(2);
    // Nothing in this call may touch the approved master, which is a later,
    // coordinate-free feed answering a different question.
    expect(db.queries.some((q) => q.sql.includes("rrc.permit"))).toBe(false);
    expect(r.notes.join(" ")).toMatch(/APPLICATIONS, NOT PERMITS/);
  });

  test("a radius keeps what is inside it and drops what is not", async () => {
    // One degree of latitude is 69.1 miles, so D2 at 33.0 is far outside 25 mi
    // of 32.0 and D1 is at the centre.
    const r = await call("rrc_intent_feed", { lat: 32.0, lon: -102.0, radius_mi: 25 });
    expect(r.applications.map((a: Result) => a.universal_doc_no)).toEqual(["D1"]);
    expect(r.applications[0].distance_mi).toBe(0);
  });

  test("an operator filter and a purpose filter compose", async () => {
    const r = await call("rrc_intent_feed", { operator_no: "999999", purpose: "recompletion" });
    expect(r.applications.map((a: Result) => a.universal_doc_no)).toEqual(["D2"]);
    expect(r.by_operator).toEqual([
      { operator_no: "999999", operator_name: "OTHER CO", applications: 1 },
    ]);
  });
});

// --------------------------------------------- refusing an unbounded scan

describe("an unfiltered call is refused", () => {
  test.each([
    ["rrc_intent_feed", {}],
    ["rrc_recompletion_watch", {}],
    ["rrc_zone_migration", {}],
    ["rrc_new_entrant", {}],
    ["rrc_permit_purpose", {}],
    ["rrc_permit_abandoned", {}],
  ])("%s", async (name, args) => {
    const r = await callRaw(name, args);
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/required|refused/i);
    // A refusal is a value, not a throw, and it costs no query.
    expect(db.queries).toHaveLength(0);
  });

  test("rrc_backtest refuses an empty operator list", async () => {
    const r = await call("rrc_backtest", {
      signal: "h15_delinquent",
      outcome: "state_funded_plug",
      operator_nos: [],
    });
    expect(r.ok).toBe(false);
    expect(db.queries).toHaveLength(0);
  });

  test("a county that does not exist is named rather than scanned", async () => {
    const r = await call("rrc_area_watch", { county: "Nowhere", since: "2026-01-01" });
    expect(r).toEqual({ ok: false, error: "Not a Texas county: Nowhere." });
    expect(db.queries).toHaveLength(0);
  });
});

// ------------------------------------------------------- 52 peer uptime

describe("rrc_peer_uptime", () => {
  test("uptime, closed gaps and the longest gap, over reported cycles only", async () => {
    db.leases = [{ operator_no: "100000", leases: 4 }];
    db.operators = [operator("100000")];
    db.cycleEdge = "2026-06";
    // Six reported cycles, three producing, one closed two-month gap, and a
    // trailing zero at the edge that is NOT a restart.
    db.leaseMonths = [
      { operator_no: "100000", cycle: "2026-01", oil: 10, gas: 0, oil_allow: null },
      { operator_no: "100000", cycle: "2026-02", oil: 0, gas: 0, oil_allow: null },
      { operator_no: "100000", cycle: "2026-03", oil: 0, gas: 0, oil_allow: null },
      { operator_no: "100000", cycle: "2026-04", oil: 5, gas: 0, oil_allow: null },
      { operator_no: "100000", cycle: "2026-05", oil: 7, gas: 0, oil_allow: null },
      { operator_no: "100000", cycle: "2026-06", oil: 0, gas: 0, oil_allow: null },
      // Beyond the reporting edge: unfiled, not zero, and excluded.
      { operator_no: "100000", cycle: "2026-07", oil: 0, gas: 0, oil_allow: null },
    ];

    const r = await call("rrc_peer_uptime", { operator_no: "100000", field_no: "16032300" });
    expect(r.ok).toBe(true);
    const s = r.subject;
    expect(s.months).toBe(6);
    expect(s.producing_months).toBe(3);
    expect(s.uptime).toBeCloseTo(0.5, 10);
    expect(s.stops).toBe(1);
    expect(s.longest_gap_months).toBe(2);
    expect(s.last_producing_cycle).toBe("2026-05");
    expect(s.oil_bbl).toBe(22);
    expect(r.reported_through).toBe("2026-06");
  });
});

// ----------------------------------------------------- 47 zone migration

describe("rrc_zone_migration", () => {
  test("buckets MM/DD/YYYY filing dates by real year, not by text order", async () => {
    // Sorted as text, 12/31/2025 outranks 01/04/2026. Sorted as dates it does
    // not, and these two land in different years.
    db.completions = [
      {
        operator_no: "100000",
        field_no: "F1",
        field_name: "SPRABERRY",
        completion_type: "1",
        cmpl_or_recmpl_date: "12/31/2025",
        approved_dt: "01/15/2026",
      },
      {
        operator_no: "100000",
        field_no: "F2",
        field_name: "WOLFCAMP",
        completion_type: "1",
        cmpl_or_recmpl_date: "01/04/2026",
        approved_dt: "02/01/2026",
      },
    ];
    db.permits = [
      { yr: "2025", depth: 9000 },
      { yr: "2026", depth: 11000 },
      { yr: "2026", depth: 13000 },
    ];

    const r = await call("rrc_zone_migration", {
      operator_no: "100000",
      since: "2025-01-01",
      until: "2026-12-31",
    });
    expect(r.ok).toBe(true);
    const years = Object.fromEntries(r.by_year.map((y: Result) => [y.year, y]));
    expect(years["2025"].completion_filings).toBe(1);
    expect(years["2025"].top_fields[0].field_name).toBe("SPRABERRY");
    expect(years["2026"].completion_filings).toBe(1);
    expect(years["2026"].top_fields[0].field_name).toBe("WOLFCAMP");
    // Median of one value is that value; of [11000, 13000] it is 12000.
    expect(years["2025"].median_permit_depth_ft).toBe(9000);
    expect(years["2026"].median_permit_depth_ft).toBe(12000);
    expect(r.depth_shift_ft).toBe(3000);
  });
});

// ------------------------------------------------ 48 completion benchmark

describe("rrc_completion_benchmark", () => {
  test("our median against the field's own distribution, and no invented shot density", async () => {
    db.completions = [
      { api_no: "00100001", operator_no: "100000", field_no: "F1" },
      { api_no: "00100002", operator_no: "200000", field_no: "F1" },
      { api_no: "00100003", operator_no: "200000", field_no: "F1" },
      { api_no: "00100004", operator_no: "300000", field_no: "F1" },
    ];
    db.perfs = [
      { api_number: "00100001", perf_ft: 2000, intervals: 2 },
      { api_number: "00100002", perf_ft: 1000, intervals: 1 },
      { api_number: "00100003", perf_ft: 3000, intervals: 3 },
      { api_number: "00100004", perf_ft: 4000, intervals: 4 },
    ];

    const r = await call("rrc_completion_benchmark", {
      operator_no: "100000",
      field_no: "F1",
    });
    expect(r.ok).toBe(true);
    const perf = r.perforated_length_ft;
    expect(perf.ours_median).toBe(2000);
    expect(perf.ours_n).toBe(1);
    // [1000, 2000, 3000, 4000]: median 2500, p10 1300, p90 3700.
    expect(perf.field_median).toBe(2500);
    expect(perf.field_p10).toBeCloseTo(1300, 10);
    expect(perf.field_p90).toBeCloseTo(3700, 10);
    // Two of the four wells are at or below our 2000 ft.
    expect(perf.percentile_in_field).toBeCloseTo(0.5, 10);
    // The record carries intervals and no shot count. Null, and said out loud.
    expect(r.shot_density).toBeNull();
    expect(r.notes.join(" ")).toMatch(/SHOT DENSITY IS NOT IN THE RECORD/);
  });

  test("an operator with no filings in the field is told so", async () => {
    db.completions = [{ api_no: "00100002", operator_no: "200000", field_no: "F1" }];
    const r = await call("rrc_completion_benchmark", { operator_no: "100000", field_no: "F1" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/no completion filings in field F1/);
  });
});

// --------------------------------------------------- 84 permit abandoned

describe("rrc_permit_abandoned", () => {
  test("pairs the seven-digit permit against the wellbore's six, and keeps only the unbuilt", async () => {
    db.permits = [
      {
        permit_number: "0400270",
        permit_seq: "99",
        operator_number: "100000",
        operator_name: "OPERATOR 100000",
        lease_name: "BUILT LEASE",
        well_number: "1",
        county_code: "003",
        district: "08",
        total_depth: 9000,
        issued_date: "2023-01-10",
        expires_date: "2025-01-10",
      },
      {
        permit_number: "0400271",
        permit_seq: "99",
        operator_number: "100000",
        operator_name: "OPERATOR 100000",
        lease_name: "DEAD LEASE",
        well_number: "2",
        county_code: "003",
        district: "08",
        total_depth: 12000,
        issued_date: "2023-02-10",
        expires_date: "2025-02-10",
      },
    ];
    // rrc.wellbore carries six digits, sometimes WITH a leading zero of its
    // own. Stripping only the permit master's pad calls this permit unbuilt.
    db.wellbores = [{ recent_permit: "0400270" }];

    const r = await call("rrc_permit_abandoned", { county: "Andrews" });
    expect(r.ok).toBe(true);
    expect(r.expired).toBe(2);
    expect(r.unbuilt).toBe(1);
    expect(r.unbuilt_share).toBeCloseTo(0.5, 10);
    expect(r.abandoned[0].permit_number).toBe("0400271");
    expect(r.abandoned[0].lease_name).toBe("DEAD LEASE");
    expect(r.by_operator).toEqual([
      { operator_no: "100000", operator_name: "OPERATOR 100000", permits: 1 },
    ]);
    expect(r.notes.join(" ")).toMatch(/candidate list, not a count/);
  });
});

// ---------------------------------------------------- 54 permit forecast

describe("rrc_permit_forecast", () => {
  test("the median lag comes from paired filings, and an implausible pair is dropped", async () => {
    db.wellbores = [
      { api_number: "00300001", recent_permit: "100001", completion_date: "20240110" },
      { api_number: "00300002", recent_permit: "100002", completion_date: "20240419" },
      { api_number: "00300003", recent_permit: "100003", completion_date: "20241026" },
      // Permitted in 2015, completed in 2024: a re-entry, not a drilling cycle.
      { api_number: "00300004", recent_permit: "100004", completion_date: "20240101" },
    ];
    db.permits = [
      { permit_number: "0100001", issued_date: "2023-10-02" },
      { permit_number: "0100002", issued_date: "2023-10-02" },
      { permit_number: "0100003", issued_date: "2023-10-02" },
      { permit_number: "0100004", issued_date: "2015-01-01" },
    ];
    db.listPermits = [
      {
        permit_number: "0100009",
        operator_number: "100000",
        operator_name: "OPERATOR 100000",
        lease_name: "PENDING LEASE",
        issued_date: "2026-01-01",
        expires_date: "2028-01-01",
      },
    ];

    const r = await call("rrc_permit_forecast", { county: "Andrews" });
    expect(r.ok).toBe(true);
    // 2023-10-02 to 2024-01-10 is 100 days, to 2024-04-19 is 200, to 2024-10-26
    // is 390. The 2015 pair is 3288 days and is trimmed at five years.
    expect(r.lag_sample).toBe(3);
    expect(r.permit_to_completion_days.median).toBe(200);
    // 200 days is 6.58 months, rounded to 7, added to the issue date.
    expect(r.projected[0].projected_completion).toBe("2026-08-01");
    expect(r.projected[0].permit_number).toBe("0100009");
    expect(r.notes.join(" ")).toMatch(/PERMIT ISSUE TO COMPLETION DATE, not to first production/);
  });
});

// ----------------------------------------------------- 45 the timeline

describe("rrc_operator_timeline", () => {
  test("orders events by date and separates a second filing on a hole", async () => {
    db.listPermits = [
      {
        permit_number: "0400270",
        lease_name: "SMITH A",
        well_number: "1",
        total_depth: 9000,
        filed_date: "2019-12-20",
        issued_date: "2020-01-05",
      },
    ];
    db.completions = [
      {
        operator_no: "100000",
        api_no: "00300001",
        lease_name: "SMITH A",
        well_no: "1",
        field_no: "F1",
        field_name: "SPRABERRY",
        completion_type: "1",
        purpose_of_filing: "1",
        spud_dt: "02/01/2020",
        cmpl_or_recmpl_date: "04/01/2020",
        approved_dt: "05/01/2020",
      },
      {
        operator_no: "100000",
        api_no: "00300001",
        lease_name: "SMITH A",
        well_no: "1",
        field_no: "F2",
        field_name: "WOLFCAMP",
        completion_type: "7",
        purpose_of_filing: "1",
        spud_dt: null,
        cmpl_or_recmpl_date: "06/15/2023",
        approved_dt: "07/01/2023",
      },
    ];
    db.wellbores = [
      {
        operator_number: "100000",
        api_number: "00300001",
        lease_name: "SMITH A",
        well_no: "1",
        plug_date: "20250310",
      },
    ];
    db.operatorProduction = [{ operator_no: "100000", cycle: "2020-05" }];

    const r = await call("rrc_operator_timeline", { operator_no: "100000" });
    expect(r.ok).toBe(true);
    expect(r.events.map((e: Result) => [e.date, e.event])).toEqual([
      ["2019-12-20", "permit filed"],
      ["2020-01-05", "permit issued"],
      ["2020-02-01", "spud"],
      ["2020-04-01", "completion"],
      ["2020-05-01", "first reported production"],
      // Typed "Other", but this hole already had a filing in 2020, so it is
      // later work on an existing wellbore.
      ["2023-06-15", "recompletion"],
      ["2025-03-10", "plug"],
    ]);
    expect(r.counts.recompletion).toBe(1);
  });
});

// ---------------------------------------------------- 59 the pattern scan

describe("rrc_pattern_scan", () => {
  test("reports each step whether or not it happened, with no verdict", async () => {
    db.operators = [operator("500000", { org_date: "2025-01-15" })];
    db.p4Filing = [{ operator_no: "500000", effective_date: "2025-03-01" }];
    db.wellbores = [{ operator_number: "500000", api_number: "00300001" }];
    db.operatorProduction = [{ operator_no: "500000", cycle: "2025-06" }];

    const r = await call("rrc_pattern_scan", {
      pattern: "entity_then_transfers",
      operator_no: "500000",
    });
    expect(r.ok).toBe(true);
    expect(r.steps.map((s: Result) => [s.step, s.observed])).toEqual([
      ["operator registered", true],
      ["leases transferred in on a P-4", true],
      ["wells carried on schedule", true],
      ["production reported", true],
    ]);
    expect(r.dates_in_sequence_order).toBe(true);
    expect(r.steps[0].first_date).toBe("2025-01-15");
    expect(r.steps[1].first_date).toBe("2025-03-01");
    // Named patterns only, and nothing about what the pattern means.
    expect(JSON.stringify(r).toLowerCase()).not.toContain("shell");
    expect(JSON.stringify(r).toLowerCase()).not.toContain("fraud");
    expect(JSON.stringify(r)).not.toMatch(/\bscore\b/i);
  });

  test("a pattern name outside the fixed set never reaches the function", () => {
    const parsed = find("rrc_pattern_scan").args.safeParse({
      pattern: "whatever_the_caller_invented",
      operator_no: "500000",
    });
    expect(parsed.success).toBe(false);
  });
});

// ------------------------------------------------------- 83 the purpose

describe("rrc_permit_purpose", () => {
  test("labels the W-1 codes and floors the approval share", async () => {
    db.pendingActivity = [
      { filing_purpose_code: "01", month: "2026-06", n: 8, approved: 6 },
      { filing_purpose_code: "14", month: "2026-06", n: 2, approved: 0 },
    ];
    const r = await call("rrc_permit_purpose", { county: "Andrews" });
    expect(r.ok).toBe(true);
    expect(r.applications).toBe(10);
    const drill = r.by_purpose.find((p: Result) => p.purpose_code === "01");
    const recomp = r.by_purpose.find((p: Result) => p.purpose_code === "14");
    expect(drill.purpose).toBe("New drill");
    expect(drill.approved_share).toBeCloseTo(0.75, 10);
    expect(drill.share_of_all).toBeCloseTo(0.8, 10);
    expect(recomp.purpose).toBe("Recompletion");
    expect(recomp.approved_share).toBe(0);
    expect(r.notes.join(" ")).toMatch(/2025-07-07/);
  });
});
