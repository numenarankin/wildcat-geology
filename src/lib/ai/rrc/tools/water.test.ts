import { beforeEach, describe, expect, test, vi } from "vitest";

import type {
  InjectionMonth,
  LeaseMonth,
  NearbyDisposal,
  UicPermit,
  WellInjection,
} from "../../../scout/rrc-types";
import { permittedPressurePsig } from "../../../scout/injection-series";

/**
 * The water catalog, against fixtures whose right answer is arithmetic done
 * here rather than by the code.
 *
 * Four properties carry the weight, and each one is a wrong answer with real
 * money behind it if it slips:
 *
 *  1. Utilisation is reported volume over PERMITTED volume, and the permit is a
 *     ceiling rather than an offer.
 *  2. Enhanced recovery (type 3) is not disposal. It goes back into a producing
 *     zone, so counting it as headroom invents somewhere for water to go.
 *  3. No reported volume is not zero volume. A well that has not filed is new,
 *     idle or late, and calling it empty is the most expensive wrong answer in
 *     this file.
 *  4. Every result carries the reporting edge, because H-10 filing runs about a
 *     YEAR behind and a thin recent tail is paperwork, not a well that stopped.
 */

const db = vi.hoisted(() => ({
  /** H-10 reporting edge. */
  edge: "2024-12",
  /** Production reporting edge, three months rather than a year behind. */
  cycleEdge: "2025-03",
  injection: new Map<string, unknown>(),
  disposal: [] as unknown[],
  wells: [] as unknown[],
  locations: new Map<string, { lat: number; lon: number }>(),
  h10Totals: [] as { uic_no: string; bbl: number; first_cycle: string }[],
  perfs: [] as { api_number: string; top_ft: number | null; bottom_ft: number | null }[],
  leases: new Map<string, { name: string; monthly: LeaseMonth[] }>(),
  queries: [] as { sql: string; params: unknown[] }[],
  disposalArgs: [] as unknown[],
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string, params: unknown[]) => {
    db.queries.push({ sql, params });
    if (sql.includes("rrc.uic_h10")) return db.h10Totals;
    if (sql.includes("wb_perf")) return db.perfs;
    throw new Error(`unexpected query: ${sql.slice(0, 60)}`);
  },
  rrcQueryOne: async (sql: string, params: unknown[]) => {
    db.queries.push({ sql, params });
    if (sql.includes("well_location")) return db.locations.get(String(params[0])) ?? null;
    throw new Error(`unexpected query: ${sql.slice(0, 60)}`);
  },
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getInjectionEdge: async () => ({ reported: db.edge, loaded: db.edge }),
  getWellInjection: async (api: string) => db.injection.get(api) ?? null,
  findDisposal: async (args: unknown) => {
    db.disposalArgs.push(args);
    return db.disposal;
  },
  findWells: async () => db.wells,
  getCycleEdge: async () => ({ reported: db.cycleEdge, loaded: db.cycleEdge }),
  getLeaseDossier: async (oilGasCode: string, districtNo: string, leaseNo: string) => {
    const row = db.leases.get(`${oilGasCode}/${districtNo}/${leaseNo}`);
    return row ? { lease_name: row.name, monthly: row.monthly } : null;
  },
  getWellDossier: async () => null,
  getOperatorDossier: async () => null,
  getFieldProfile: async () => null,
  getCountyProfile: async () => null,
  getProductionTrend: async () => [],
}));

const { TOOLS } = await import("./water");

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

/** Days per calendar month, written out so the divisor here is independent. */
const DAYS: Record<string, number> = {
  "01": 31, "02": 28, "03": 31, "04": 30, "05": 31, "06": 30,
  "07": 31, "08": 31, "09": 30, "10": 31, "11": 30, "12": 31,
};
const days = (cycle: string) => (cycle === "2024-02" ? 29 : DAYS[cycle.slice(5)]);
/** 2024 is a leap year, so a full calendar year of it is 366 days. */
const DAYS_2024 = 366;

function cycles(start: string, n: number): string[] {
  const [y, m] = start.split("-").map(Number);
  return Array.from({ length: n }, (_, i) => {
    const t = y * 12 + (m - 1) + i;
    return `${Math.floor(t / 12)}-${String((t % 12) + 1).padStart(2, "0")}`;
  });
}

function permit(over: Partial<UicPermit> = {}): UicPermit {
  return {
    uic_no: "100001",
    api_number: "31711111",
    operator_no: "123456",
    operator_name: "TEST DISPOSAL LLC",
    lease_name: "SWD 1",
    uic_class: "2",
    inj_type: "1",
    approved_date: "2010-01-01",
    cancel_date: null,
    w3_date: null,
    max_bbl_per_day: 100,
    max_mcf_per_day: null,
    max_inj_pressure: 2000,
    max_inj_pressure_note: null,
    top_inj_zone: 6000,
    bot_inj_zone: 7000,
    inj_mode: "T",
    is_commercial: true,
    fluid_comment: null,
    location: null,
    fluids: ["Salt water"],
    live: true,
    ...over,
  };
}

const injMonth = (cycle: string, bbl: number, over: Partial<InjectionMonth> = {}): InjectionMonth => ({
  cycle,
  bbl,
  mcf: 0,
  avg_pressure: 500,
  max_pressure: 900,
  reported: cycle <= db.edge,
  ...over,
});

function injection(api: string, w: Partial<WellInjection> & { monthly: InjectionMonth[] }) {
  const permits = [permit()];
  const full: WellInjection = {
    permits,
    reportedThrough: db.edge,
    permittedBblPerDay: 100,
    permittedPressurePsig: permittedPressurePsig(permits),
    recentBblPerDay: null,
    ...w,
  };
  db.injection.set(api, full);
  return full;
}

function disposalRow(over: Partial<NearbyDisposal> = {}): NearbyDisposal {
  const max = over.max_bbl_per_day ?? null;
  const recent = over.recentBblPerDay ?? null;
  return {
    uic_no: "200001",
    api_number: "31700001",
    operator_no: "123456",
    operator_name: "TEST DISPOSAL LLC",
    lease_name: "SWD 1",
    well_no: "1",
    county_name: "MIDLAND",
    inj_type: "1",
    is_commercial: true,
    max_bbl_per_day: null,
    top_inj_zone: null,
    bot_inj_zone: null,
    lat: 31.9,
    lon: -102.1,
    distance_mi: 1,
    recentBblPerDay: null,
    utilisation: max && recent != null ? recent / max : null,
    ...over,
  };
}

const CENTER = { lat: 31.9686, lon: -102.0779 };

beforeEach(() => {
  db.edge = "2024-12";
  db.cycleEdge = "2025-03";
  db.injection.clear();
  db.leases.clear();
  db.locations.clear();
  db.disposal = [];
  db.wells = [];
  db.h10Totals = [];
  db.perfs = [];
  db.queries = [];
  db.disposalArgs = [];
});

// ------------------------------------------------------------- utilisation

describe("rrc_injection_trend", () => {
  /**
   * A well that took 1,000 bbl in each month of 2024 against a 100 bbl/d
   * permit, plus two months past the edge that the mirror has but nobody has
   * filed for.
   */
  const steady = () => {
    const monthly = [
      ...cycles("2024-01", 12).map((c) => injMonth(c, 1000)),
      ...cycles("2025-01", 2).map((c) => injMonth(c, 5000, { reported: false })),
    ];
    return injection("31711111", {
      monthly,
      permittedBblPerDay: 100,
      // The same twelve months ending at the edge, over the days actually
      // filed: the definition the well modal quotes.
      recentBblPerDay: 12000 / DAYS_2024,
    });
  };

  test("utilisation is reported barrels a day over the permitted ceiling", async () => {
    const inj = steady();
    const r = await call("rrc_injection_trend", { api: "31711111" });

    // 12,000 bbl across the 366 days of 2024 is 32.787 bbl/d.
    expect(r.recent_bbl_per_day).toBeCloseTo(12000 / DAYS_2024, 12);
    expect(r.recent_window_months).toBe(12);
    expect(r.permitted_bbl_per_day).toBe(100);
    // 32.787 / 100. Counting the two unfiled months would read 51.8%.
    expect(r.utilisation).toBeCloseTo(12000 / DAYS_2024 / 100, 12);

    // One well, one rate: the tool and the well modal cannot quote different
    // numbers for the same twelve months.
    expect(r.recent_bbl_per_day).toBe(inj.recentBblPerDay);
  });

  test("the series is the filed months, at their own calendar length", async () => {
    steady();
    const r = await call("rrc_injection_trend", { api: "31711111" });
    expect(r.series).toHaveLength(12);
    expect(r.series[0]).toEqual({
      cycle: "2024-01",
      bbl: 1000,
      bbl_per_day: 1000 / 31,
      avg_pressure: 500,
    });
    // February 2024 is 29 days, so the same volume is a higher rate.
    expect(r.series[1].bbl_per_day).toBeCloseTo(1000 / days("2024-02"), 12);
    expect(r.truncated).toBe(false);
    expect(r.reported_through).toBe("2024-12");
  });

  test("a well that stopped filing years ago has no recent rate, and is not called empty", async () => {
    // Last H-10 on file is December 2021, three years before the edge. The
    // barrels are real; they are just not recent, and quoting them as a current
    // rate would say this well is running when the record says only that it
    // once did.
    injection("31722222", {
      monthly: cycles("2021-01", 12).map((c) => injMonth(c, 30000)),
      permittedBblPerDay: 1000,
      recentBblPerDay: null,
    });
    const r = await call("rrc_injection_trend", { api: "31722222" });

    expect(r.recent_bbl_per_day).toBeNull();
    // Not 0, which would read as "this well is empty, send it your water".
    expect(r.utilisation).toBeNull();
    expect(r.months_to_full).toBeNull();
    // The record itself is still shown, and the edge says how old it is.
    expect(r.series).toHaveLength(12);
    expect(r.reported_through).toBe("2024-12");
    expect(r.notes.join(" ")).toContain("2024-12");
  });

  test("an intermittent filer is averaged over the months it filed, inside the window", async () => {
    // Three filings inside the twelve months ending at the edge, and a busy
    // 2020 that is nothing to do with the question.
    injection("31788888", {
      monthly: [
        ...cycles("2020-01", 12).map((c) => injMonth(c, 90000)),
        ...["2024-10", "2024-11", "2024-12"].map((c) => injMonth(c, 1000)),
      ],
      permittedBblPerDay: 100,
      recentBblPerDay: 3000 / 92,
    });
    const r = await call("rrc_injection_trend", { api: "31788888" });
    // 3,000 bbl over the 92 days of October, November and December. Over the
    // whole 365-day window it would read 8.2, which is how hard it runs only if
    // the nine unfiled months were idle rather than unfiled.
    expect(r.recent_bbl_per_day).toBeCloseTo(3000 / 92, 12);
    expect(r.utilisation).toBeCloseTo(3000 / 92 / 100, 12);
  });

  test("a well with nothing filed at all is null throughout", async () => {
    injection("31733333", {
      monthly: cycles("2025-01", 3).map((c) => injMonth(c, 500, { reported: false })),
      recentBblPerDay: null,
    });
    const r = await call("rrc_injection_trend", { api: "31733333" });
    expect(r.recent_bbl_per_day).toBeNull();
    expect(r.utilisation).toBeNull();
    expect(r.series).toEqual([]);
  });

  test("enhanced recovery is permitted and metered, and still says it is not disposal", async () => {
    injection("31744444", {
      permits: [permit({ inj_type: "3", max_bbl_per_day: 500 })],
      monthly: cycles("2024-01", 12).map((c) => injMonth(c, 1000)),
      permittedBblPerDay: 500,
      recentBblPerDay: 12000 / DAYS_2024,
    });
    const r = await call("rrc_injection_trend", { api: "31744444" });
    expect(r.is_disposal).toBe(false);
    expect(r.inj_types).toEqual(["3"]);
    // It still has a ceiling and a utilisation; what it does not have is room
    // for somebody else's water.
    expect(r.utilisation).toBeCloseTo(12000 / DAYS_2024 / 500, 12);
  });

  test("a ramping well projects months to full from the fitted slope", async () => {
    // 2024 at a flat 30 bbl/d, then nothing else: no ramp, no projection.
    injection("31755555", {
      monthly: cycles("2024-01", 12).map((c) => injMonth(c, 30 * days(c))),
      permittedBblPerDay: 100,
      recentBblPerDay: (30 * DAYS_2024) / DAYS_2024,
    });
    const r = await call("rrc_injection_trend", { api: "31755555" });
    expect(r.recent_bbl_per_day).toBeCloseTo(30, 12);
    expect(r.ramp_bbl_per_day_per_month).toBeCloseTo(0, 12);
    expect(r.months_to_full).toBeNull();
    expect(r.months_to_full_note).toContain("Not ramping");
  });

  test("no permit is an error, not an empty answer", async () => {
    const r = await call("rrc_injection_trend", { api: "99999999" });
    expect(r).toEqual({ ok: false, error: "No UIC permit for 99999999." });
  });
});

// ---------------------------------------------------------------- headroom

describe("rrc_disposal_headroom", () => {
  /**
   * One disposal well with both numbers known, one enhanced-recovery well that
   * has no business in a headroom figure, and one disposal well that has never
   * filed.
   */
  const area = () => {
    db.disposal = [
      disposalRow({ uic_no: "D1", inj_type: "1", max_bbl_per_day: 5000, recentBblPerDay: 2000 }),
      disposalRow({ uic_no: "E1", inj_type: "3", max_bbl_per_day: 10000, recentBblPerDay: 100 }),
      disposalRow({ uic_no: "D2", inj_type: "2", max_bbl_per_day: 3000, recentBblPerDay: null }),
    ];
  };

  test("enhanced recovery is excluded from headroom", async () => {
    area();
    const r = await call("rrc_disposal_headroom", { ...CENTER });

    // Two disposal wells in the radius; the waterflood is not one of them.
    expect(r.wells).toBe(2);
    expect(r.wells_detail.map((w: Result) => w.uic_no)).toEqual(["D1"]);
    expect(r.unmeasured.map((w: Result) => w.uic_no)).toEqual(["D2"]);
    // 5,000 permitted less 2,000 reported. Counting the type 3 well would say
    // 15,000 permitted and 12,900 of headroom that does not exist.
    expect(r.permitted_bbl_per_day).toBe(5000);
    expect(r.reported_bbl_per_day).toBe(2000);
    expect(r.headroom_bbl_per_day).toBe(3000);
    expect(r.notes.join(" ")).toContain("Enhanced-recovery injection (type 3) is excluded");
  });

  test("a well that has not filed is held out rather than folded in at zero", async () => {
    area();
    const r = await call("rrc_disposal_headroom", { ...CENTER });
    expect(r.wells_measured).toBe(1);
    // Its ceiling is real and is reported; its spare capacity is unknown.
    // Folding it in would add 3,000 bbl/d of headroom nobody can verify.
    expect(r.unmeasured_permitted_bbl_per_day).toBe(3000);
    expect(r.unmeasured[0].recent_bbl_per_day).toBeNull();
    expect(r.headroom_bbl_per_day).toBe(3000);
  });

  test("per-well utilisation and headroom agree with the area totals", async () => {
    area();
    const r = await call("rrc_disposal_headroom", { ...CENTER });
    const w = r.wells_detail[0];
    expect(w.utilisation).toBeCloseTo(2000 / 5000, 12);
    expect(w.headroom_bbl_per_day).toBe(3000);
    // One measured well, so the row and the total are two derivations of one
    // number and must not disagree.
    expect(w.headroom_bbl_per_day).toBe(r.headroom_bbl_per_day);
    expect(r.reported_through).toBe("2024-12");
    expect(r.commercial_only).toBe(false);
    expect(r.radius_mi).toBe(25);
  });

  test("the commercial filter and the radius are passed to the search, not applied after", async () => {
    area();
    await call("rrc_disposal_headroom", { ...CENTER, radius_mi: 5, commercial_only: true, limit: 10 });
    expect(db.disposalArgs[0]).toEqual({
      lat: CENTER.lat,
      lon: CENTER.lon,
      radiusMi: 5,
      commercialOnly: true,
      limit: 10,
    });
  });

  test("a point that is not a point is refused before anything is queried", async () => {
    // The schema rejects NaN, so this is the guard behind it: the dispatcher is
    // one caller of `run`, and a search centred on NaN would scan.
    const r = await callRaw("rrc_disposal_headroom", { lat: Number.NaN, lon: -102 });
    expect(r).toEqual({ ok: false, error: "lat and lon are required." });
    expect(db.disposalArgs).toHaveLength(0);
  });
});

// --------------------------------------------------------------- fragility

describe("rrc_disposal_fragility", () => {
  /**
   * Four disposal wells with a rate on file, one that has never filed, and a
   * waterflood that is not disposal at all. D is over-permitted: it takes 900
   * bbl/d against a 100 bbl/d ceiling, so it lends no capacity back.
   */
  const area = () => {
    db.disposal = [
      disposalRow({ uic_no: "A", max_bbl_per_day: 3200, recentBblPerDay: 3000 }),
      disposalRow({ uic_no: "B", max_bbl_per_day: 1200, recentBblPerDay: 1000 }),
      disposalRow({ uic_no: "C", max_bbl_per_day: 600, recentBblPerDay: 500 }),
      disposalRow({ uic_no: "D", max_bbl_per_day: 100, recentBblPerDay: 900 }),
      disposalRow({ uic_no: "E", max_bbl_per_day: 1000, recentBblPerDay: null }),
      disposalRow({ uic_no: "F", inj_type: "3", max_bbl_per_day: 9000, recentBblPerDay: 5000 }),
    ];
  };

  test("wells rank by the barrels that would need another home", async () => {
    area();
    const r = await call("rrc_disposal_fragility", { ...CENTER });

    expect(r.wells).toBe(5);
    expect(r.wells_scored).toBe(4);
    // 3000 + 1000 + 500 + 900. The waterflood's 5,000 is not area disposal.
    expect(r.area_bbl_per_day).toBe(5400);
    expect(r.ranked.map((w: Result) => w.uic_no)).toEqual(["A", "B", "D", "C"]);
    expect(r.ranked.map((w: Result) => w.displaced_bbl_per_day)).toEqual([3000, 1000, 900, 500]);
    expect(r.ranked[0].share_of_area).toBeCloseTo(3000 / 5400, 12);
  });

  test("headroom elsewhere counts only the wells that could take the water", async () => {
    area();
    const r = await call("rrc_disposal_fragility", { ...CENTER });
    const by = Object.fromEntries(r.ranked.map((w: Result) => [w.uic_no, w]));

    // Losing A displaces 3,000 into B's 200 and C's 100. D is 800 over its own
    // ceiling and lends nothing back; E has never filed and is not counted.
    expect(by.A.remaining_headroom_bbl_per_day).toBe(300);
    expect(by.A.shortfall_bbl_per_day).toBe(2700);
    // Losing B: A's 200 plus C's 100.
    expect(by.B.remaining_headroom_bbl_per_day).toBe(300);
    expect(by.B.shortfall_bbl_per_day).toBe(700);
    // Losing D: A 200, B 200, C 100.
    expect(by.D.remaining_headroom_bbl_per_day).toBe(500);
    expect(by.D.shortfall_bbl_per_day).toBe(400);
    // Losing C: A 200, B 200, D nothing.
    expect(by.C.remaining_headroom_bbl_per_day).toBe(400);
    expect(by.C.shortfall_bbl_per_day).toBe(100);
  });

  test("a well that never filed is listed, not ranked at zero", async () => {
    area();
    const r = await call("rrc_disposal_fragility", { ...CENTER });
    // Zero would sort it to the bottom of a risk list, which is exactly where a
    // well nobody has measured does not belong.
    expect(r.ranked.map((w: Result) => w.uic_no)).not.toContain("E");
    expect(r.unscored).toEqual([
      {
        uic_no: "E",
        api_number: "31700001",
        operator_name: "TEST DISPOSAL LLC",
        max_bbl_per_day: 1000,
      },
    ]);
    expect(r.reported_through).toBe("2024-12");
  });
});

// ------------------------------------------------------------ seismic bands

describe("rrc_seismic_exposure", () => {
  const area = () => {
    db.disposal = [
      disposalRow({ uic_no: "S1", bot_inj_zone: 4000, max_bbl_per_day: 1000 }),
      disposalRow({ uic_no: "S2", bot_inj_zone: 9000, max_bbl_per_day: 2000 }),
      disposalRow({ uic_no: "S3", bot_inj_zone: null, max_bbl_per_day: 500 }),
      disposalRow({ uic_no: "X1", inj_type: "3", bot_inj_zone: 12000, max_bbl_per_day: 8000 }),
    ];
    db.h10Totals = [
      { uic_no: "S1", bbl: 5000, first_cycle: "2015-01" },
      { uic_no: "S2", bbl: 20000, first_cycle: "2018-06" },
      { uic_no: "S3", bbl: 1000, first_cycle: "2020-02" },
    ];
  };

  test("cumulative barrels land in the band of their permitted bottom", async () => {
    area();
    const r = await call("rrc_seismic_exposure", { ...CENTER });

    expect(r.wells).toBe(3);
    expect(r.by_band).toEqual([
      { band: "shallow", depth_ft: { from: 0, to: 5000 }, wells: 1, cumulative_bbl: 5000, permitted_bbl_per_day: 1000 },
      { band: "deep", depth_ft: { from: 8000, to: 10000 }, wells: 1, cumulative_bbl: 20000, permitted_bbl_per_day: 2000 },
      { band: "unknown", depth_ft: null, wells: 1, cumulative_bbl: 1000, permitted_bbl_per_day: 500 },
    ]);
    // 5,000 + 20,000 + 1,000, and 20,000 of it at or below 8,000 ft.
    expect(r.cumulative_bbl).toBe(26000);
    expect(r.deep_wells).toBe(1);
    expect(r.deep_cumulative_bbl).toBe(20000);
    expect(r.deep_share).toBeCloseTo(20000 / 26000, 12);
    expect(r.deep_threshold_ft).toBe(8000);
  });

  test("the H-10 total is asked only for the disposal wells, and only to the edge", async () => {
    area();
    await call("rrc_seismic_exposure", { ...CENTER });
    const q = db.queries.find((c) => c.sql.includes("rrc.uic_h10"))!;
    // One round trip, keyed by the permits this radius already returned.
    expect(db.queries.filter((c) => c.sql.includes("rrc.uic_h10"))).toHaveLength(1);
    expect(q.params[0]).toEqual(["S1", "S2", "S3"]);
    expect(q.params[1]).toBe("2024-12");
  });

  test("a well with no H-10 total is null, not zero barrels", async () => {
    db.disposal = [disposalRow({ uic_no: "S9", bot_inj_zone: 6000 })];
    db.h10Totals = [];
    const r = await call("rrc_seismic_exposure", { ...CENTER });
    expect(r.wells_detail[0].cumulative_bbl).toBeNull();
    expect(r.wells_detail[0].first_reported).toBeNull();
    expect(r.wells_detail[0].band).toBe("intermediate");
    expect(r.deep_share).toBeNull();
  });

  test("an empty radius answers empty without querying the H-10 table", async () => {
    const r = await call("rrc_seismic_exposure", { ...CENTER });
    expect(r.wells).toBe(0);
    expect(r.by_band).toEqual([]);
    expect(r.reported_through).toBe("2024-12");
    expect(db.queries).toHaveLength(0);
  });
});

// ------------------------------------------------------ pressure and offsets

describe("rrc_pressure_interference", () => {
  const setUp = () => {
    injection("31711111", {
      permits: [
        permit({ top_inj_zone: 6000, bot_inj_zone: 6800, max_inj_pressure: 2000 }),
        permit({ uic_no: "100002", top_inj_zone: 6500, bot_inj_zone: 7000, max_inj_pressure: 1800 }),
        // Cancelled, so it is not part of the interval this well can use.
        permit({ uic_no: "100003", top_inj_zone: 2000, bot_inj_zone: 3000, live: false }),
      ],
      monthly: cycles("2024-01", 12).map((c) => injMonth(c, 1000, { max_pressure: 1500 })),
      permittedBblPerDay: 100,
      recentBblPerDay: 12000 / DAYS_2024,
    });
    db.locations.set("31711111", { lat: 31.9, lon: -102.1 });
    db.wells = [
      { api_number: "31700010", lease_name: "OFFSET A", well_no: "1", operator_name: "OP", well_type_name: "OIL", distance_mi: 0.2 },
      { api_number: "31700020", lease_name: "OFFSET B", well_no: "2", operator_name: "OP", well_type_name: "OIL", distance_mi: 0.5 },
      { api_number: "31700030", lease_name: "OFFSET C", well_no: "3", operator_name: "OP", well_type_name: "OIL", distance_mi: 0.9 },
      // The injector itself, which is not its own offset.
      { api_number: "31711111", lease_name: "SWD 1", well_no: "1", operator_name: "OP", well_type_name: "SWD", distance_mi: 0 },
    ];
    db.perfs = [
      { api_number: "31700010", top_ft: 6500, bottom_ft: 7500 },
      { api_number: "31700020", top_ft: 4000, bottom_ft: 5000 },
    ];
  };

  test("the injection interval is the envelope of the live permits", async () => {
    setUp();
    const r = await call("rrc_pressure_interference", { api: "31711111" });
    // Shallowest live top to deepest live bottom. The cancelled permit's 2,000
    // ft top is not an interval this well can inject into.
    expect(r.injection_interval_ft).toEqual({ top: 6000, bottom: 7000 });
    expect(r.permitted_max_pressure_psig).toBe(2000);
    expect(r.observed_max_pressure_psig).toBe(1500);
    expect(r.recent_bbl_per_day).toBeCloseTo(12000 / DAYS_2024, 12);
    expect(r.reported_through).toBe("2024-12");
  });

  test("overlap is the shared feet of section, and an unperforated offset is unknown", async () => {
    setUp();
    const r = await call("rrc_pressure_interference", { api: "31711111" });
    expect(r.offsets.map((o: Result) => o.api_number)).toEqual([
      "31700010",
      "31700020",
      "31700030",
    ]);
    // 6,500 to 7,000 of the 6,000 to 7,000 interval.
    expect(r.offsets[0]).toMatchObject({ overlap_ft: 500, same_interval: true });
    // 4,000 to 5,000 is a thousand feet above it: no overlap, not unknown.
    expect(r.offsets[1]).toMatchObject({ overlap_ft: 0, same_interval: false });
    // No perforation on file. Not zero overlap, which would claim the wells are
    // separated when the filing simply does not say.
    expect(r.offsets[2]).toMatchObject({
      perf_top_ft: null,
      perf_bottom_ft: null,
      overlap_ft: null,
      same_interval: null,
    });
    expect(r.offsets_same_interval).toBe(1);
    expect(r.offsets_unknown_interval).toBe(1);
  });

  test("a permit with no interval says so rather than reporting a false overlap", async () => {
    setUp();
    injection("31766666", {
      permits: [permit({ top_inj_zone: null, bot_inj_zone: null })],
      monthly: cycles("2024-01", 12).map((c) => injMonth(c, 1000)),
    });
    db.locations.set("31766666", { lat: 31.9, lon: -102.1 });
    const r = await call("rrc_pressure_interference", { api: "31766666" });
    expect(r.injection_interval_ft).toEqual({ top: null, bottom: null });
    expect(r.offsets.every((o: Result) => o.overlap_ft === null)).toBe(true);
    expect(r.notes).toContain("The permit carries no injection interval, so no overlap could be computed.");
  });

  test("a well with no surface location is refused", async () => {
    injection("31777777", { monthly: [] });
    const r = await call("rrc_pressure_interference", { api: "31777777" });
    expect(r).toEqual({ ok: false, error: "No surface location on file for 31777777." });
  });
});

// -------------------------------------------------------------- response

describe("rrc_injection_response", () => {
  /**
   * A flood that answers three months later: every month's oil is exactly twice
   * the barrels injected three months before, and nothing else lines up.
   */
  const setUp = () => {
    const inj = [100, 200, 150, 300, 250, 400, 350, 500, 450, 600, 550, 700];
    const injCycles = cycles("2023-01", 12);
    injection("31711111", {
      monthly: injCycles.map((c, i) => injMonth(c, inj[i])),
      recentBblPerDay: null,
    });
    const prodCycles = cycles("2023-01", 15);
    db.leases.set("O/08/12345", {
      name: "OFFSET LEASE",
      monthly: prodCycles.map((c, i) => ({
        cycle: c,
        oil_prod_vol: i < 3 ? 90 : 2 * inj[i - 3],
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
      })),
    });
    return {
      injector_api: "31711111",
      entity: "lease" as const,
      oil_gas_code: "O",
      district_no: "08",
      lease_no: "12345",
    };
  };

  test("the lag that carries the response is found and named", async () => {
    const r = await call("rrc_injection_response", { ...setUp(), stream: "oil" });
    expect(r.best_lag_months).toBe(3);
    expect(r.best_r).toBeCloseTo(1, 12);

    const three = r.by_lag.find((l: Result) => l.lag_months === 3);
    // Twelve pairs, each production exactly twice the injection.
    expect(three.n).toBe(12);
    expect(three.slope_production_per_bbl_injected).toBeCloseTo(2, 12);
    expect(three.r2).toBeCloseTo(1, 12);
    expect(three.sufficient).toBe(true);
    // No other lag is a straight line.
    for (const l of r.by_lag.filter((l: Result) => l.lag_months !== 3)) {
      expect(l.r2).toBeLessThan(0.99);
    }
  });

  test("a thin lag is reported with its pair count rather than a correlation to believe", async () => {
    const args = setUp();
    const r = await call("rrc_injection_response", { ...args, lags: [3, 14] });
    const thin = r.by_lag.find((l: Result) => l.lag_months === 14);
    // Only 2023-01 and 2023-02 injection reach a month production still covers.
    expect(thin.n).toBe(1);
    expect(thin.sufficient).toBe(false);
    expect(r.best_lag_months).toBe(3);
  });

  test("both edges are reported, because they are a year apart", async () => {
    const r = await call("rrc_injection_response", { ...setUp() });
    expect(r.injection_reported_through).toBe("2024-12");
    expect(r.production_reported_through).toBe("2025-03");
    expect(r.overlap_months).toBe(12);
    expect(r.notes.join(" ")).toContain("Correlation, not causation");
  });

  test("an offset the caller could not key is an error naming the missing key", async () => {
    setUp();
    const r = await call("rrc_injection_response", {
      injector_api: "31711111",
      entity: "lease",
    });
    expect(r).toEqual({
      ok: false,
      error: "entity 'lease' needs oil_gas_code, district_no and lease_no.",
    });
  });
});

// ----------------------------------------------------------------- catalog

describe("the catalog", () => {
  test("every tool has a unique name", () => {
    const names = TOOLS.map((t) => t.name);
    expect(new Set(names).size).toBe(names.length);
  });

  test("every answer carries the reporting edge and the caveats behind it", async () => {
    db.disposal = [disposalRow({ uic_no: "D1", max_bbl_per_day: 100, recentBblPerDay: 10 })];
    injection("31711111", {
      monthly: cycles("2024-01", 12).map((c) => injMonth(c, 1000)),
      recentBblPerDay: 12000 / DAYS_2024,
    });
    db.locations.set("31711111", { lat: 31.9, lon: -102.1 });

    const results = [
      await call("rrc_injection_trend", { api: "31711111" }),
      await call("rrc_disposal_headroom", { ...CENTER }),
      await call("rrc_seismic_exposure", { ...CENTER }),
      await call("rrc_pressure_interference", { api: "31711111" }),
      await call("rrc_disposal_fragility", { ...CENTER }),
    ];
    for (const r of results) {
      expect(r.ok).toBe(true);
      expect(r.reported_through).toBe("2024-12");
      // The lag is the caveat that makes the number readable at all.
      expect(r.notes.join(" ")).toContain("H-10 filing runs about a year behind");
    }
  });
});
