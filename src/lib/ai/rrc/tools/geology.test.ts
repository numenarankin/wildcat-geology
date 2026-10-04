import { beforeEach, describe, expect, test, vi } from "vitest";

/**
 * The geology tools, against fixtures whose answers were worked out by hand.
 *
 * Every expected number below is derived from the fixture geometry, not from
 * running the code, because these tools exist to replace a model reading rows
 * out loud and a test that asserts whatever the implementation emits would
 * replace it with something equally unchecked.
 *
 * THE FIXTURE, and where its numbers come from:
 *
 *   Origin is 32.0 N, 102.0 W. A degree of latitude is 69 statute miles, so
 *   0.01 deg of longitude at 32 N is
 *
 *       0.01 x 69 x 5280 x cos(32 deg) = 0.01 x 364,320 x 0.848048096
 *                                      = 3,089.609 ft
 *
 *   Four wells sit on the corners of that box, all with a KB of 3,000 ft. Their
 *   WOLFCAMP picks are 8,000 ft on the west pair and 8,100 ft on the east pair,
 *   so in subsea (KB minus depth) the surface is -5,000 ft west and -5,100 ft
 *   east and does not vary north to south. That is a plane dipping due EAST at
 *
 *       tan(dip) = 100 / 3,089.609 = 0.0323666
 *       dip      = atan(0.0323666) = 1.8538 deg
 *       gradient = 0.0323666 x 5,280 = 170.90 ft per mile
 *
 *   and the surface passes through -5,000 ft at the origin exactly.
 */

const db = vi.hoisted(() => ({
  oil: [] as Record<string, unknown>[],
  gas: [] as Record<string, unknown>[],
  keys: [] as Record<string, unknown>[],
  perfFilings: [] as Record<string, unknown>[],
  production: [] as Record<string, unknown>[],
  elevations: [] as Record<string, unknown>[],
  point: null as { lat: number; lon: number } | null,
}));

const feeder = vi.hoisted(() => ({ wells: [] as unknown[], truncated: false }));
const mirror = vi.hoisted(() => ({ construction: null as unknown }));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQueryOne: async () => db.point,
  rrcQuery: async (sql: string) => {
    // Order matters: the test-table reads join rrc.wellbore too.
    if (sql.includes("w10_test")) return db.oil;
    if (sql.includes("g10_test")) return db.gas;
    if (sql.includes("wb_perf")) return db.perfFilings;
    if (sql.includes("lease_production")) return db.production;
    // Neighbour elevations, for the interpolated datum. Empty by default, and
    // the emptiness is load-bearing: with no neighbours a well that filed no
    // elevation stays UNPLACEABLE, which is what the exclusion tests below
    // assert. A fixture that quietly supplied neighbours would place every well
    // and the exclusion path would never run.
    if (sql.includes("f.elevation_code")) return db.elevations;
    if (sql.includes("rrc.wellbore")) return db.keys;
    throw new Error(`unexpected query: ${sql.slice(0, 60)}`);
  },
}));

vi.mock("@/lib/ai/rrc/offsets", () => ({
  offsetWellbores: async () => ({ wells: feeder.wells, truncated: feeder.truncated }),
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getCycleEdge: async () => ({ reported: "2026-05", loaded: "2026-08" }),
  getWellConstruction: async () => mirror.construction,
}));

const { TOOLS } = await import("./geology");
const { catalogLine, signature } = await import("../tool");

const LAT0 = 32.0;
const LON0 = -102.0;

/* eslint-disable @typescript-eslint/no-explicit-any */
async function run(name: string, args: unknown): Promise<any> {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`no tool ${name}`);
  return (await tool.run(args as never)) as any;
}

function well(api: string, over: Record<string, unknown> = {}) {
  return {
    api_number: api,
    operator_name: "TEST OPERATOR",
    lease_name: `LEASE ${api}`,
    distanceMi: 0.25,
    lat: LAT0,
    lon: LON0,
    bottomLat: null,
    bottomLon: null,
    kbElevationFt: 3000,
    elevationCode: "KB",
    totalDepthFt: 9000,
    plugBackFt: null,
    perforations: [] as unknown[],
    casing: [] as unknown[],
    formationTops: [] as unknown[],
    ...over,
  };
}

const top = (formation: string, depthFt: number) => ({ formation, depthFt });
const perf = (topFt: number, bottomFt: number) => ({ topFt, bottomFt, openHole: false });

/** The four corners of the box described at the head of this file. */
const STRUCTURE = [
  well("10000001", { lat: 32.0, lon: -102.0, formationTops: [top("WOLFCAMP", 8000)] }),
  well("10000002", { lat: 32.0, lon: -101.99, formationTops: [top("WOLFCAMP", 8100)] }),
  well("10000003", {
    lat: 32.01,
    lon: -102.0,
    // This well is the only one that filed a SPRABERRY pick.
    formationTops: [top("SPRABERRY", 7000), top("WOLFCAMP", 8000)],
  }),
  well("10000004", { lat: 32.01, lon: -101.99, formationTops: [top("WOLFCAMP", 8100)] }),
];

beforeEach(() => {
  db.oil = [];
  db.gas = [];
  db.keys = [];
  db.perfFilings = [];
  db.production = [];
  db.elevations = [];
  db.point = { lat: LAT0, lon: LON0 };
  feeder.wells = [];
  feeder.truncated = false;
  mirror.construction = null;
});

describe("the catalog", () => {
  test("registers all seventeen tools, uniquely named, with a renderable signature", () => {
    expect(TOOLS).toHaveLength(17);
    expect(new Set(TOOLS.map((t) => t.name)).size).toBe(17);
    for (const tool of TOOLS) {
      // The catalog line carries the NAME, what the tool answers, and the few
      // arguments that change WHAT IT CAN REACH rather than how the question is
      // phrased. Everything else still comes back from the dispatcher on a bad
      // call. `radius_mi`, `limit` and `datum` are rendered because a default
      // the model cannot see is a default it cannot decide to change: hiding
      // the radius is how a screen of Texas ran against the nearest sixty
      // wells with nobody able to tell it to look wider.
      expect(catalogLine(tool)).toContain(tool.summary);
      expect(catalogLine(tool).startsWith(tool.name)).toBe(true);
      for (const arg of ["radius_mi", "limit", "datum"]) {
        if (arg in tool.args.shape) expect(catalogLine(tool)).toContain(`${arg}:`);
      }
      // The zod shape must still RENDER, because that is what a mismatch
      // replies with, and a shape that does not render leaves a wrong call
      // unanswerable.
      expect(signature(tool)).toMatch(new RegExp(`^${tool.name}\\(`));
      expect(tool.summary.split("\n")).toHaveLength(1);
    }
  });
});

describe("rrc_structure_surface", () => {
  test("returns the dip, azimuth and projection computed by hand from the fixture", async () => {
    feeder.wells = STRUCTURE;
    const r = await run("rrc_structure_surface", {
      lat: LAT0,
      lon: LON0,
      formation: "WOLFCAMP",
      target_kb_ft: 3200,
    });

    expect(r.ok).toBe(true);
    expect(r.fit.n).toBe(4);
    // A plane through four points that lie exactly on one.
    expect(r.fit.r2).toBeCloseTo(1, 10);
    expect(r.fit.rmse_ft).toBeCloseTo(0, 6);
    expect(r.fit.dip_deg).toBeCloseTo(1.8538, 3);
    // Subsea falls to the east, so downdip is due east.
    expect(r.fit.dip_azimuth_deg).toBeCloseTo(90, 6);
    expect(r.fit.dip_ft_per_mile).toBeCloseTo(170.9, 1);
    // The origin is the west pair's own position: -5,000 ft, not a fitted guess.
    expect(r.target.subsea_ft).toBeCloseTo(-5000, 6);
    // 3,200 ft of KB above a top at -5,000 ft subsea is 8,200 ft on that datum.
    expect(r.target.measured_depth_ft).toBeCloseTo(8200, 6);
  });

  test("a target a mile downdip sits one gradient lower", async () => {
    feeder.wells = STRUCTURE;
    // A mile east of the origin: 5,280 / 3,089.609 x 100 = 170.90 ft deeper.
    const eastMile = LON0 + 5280 / (69 * 5280 * Math.cos((LAT0 * Math.PI) / 180));
    const r = await run("rrc_structure_surface", {
      lat: LAT0,
      lon: LON0,
      formation: "WOLFCAMP",
      target_lat: LAT0,
      target_lon: eastMile,
    });
    expect(r.target.subsea_ft).toBeCloseTo(-5170.9, 1);
  });

  test("a well with no filed elevation is EXCLUDED from the fit and counted", async () => {
    // Its pick is 8,000 ft. Treated as a datum of zero it would land at -8,000 ft
    // subsea, 3,000 ft below a surface whose whole relief is 100 ft, and the fit
    // would still return a plane and an r-squared.
    feeder.wells = [
      ...STRUCTURE,
      well("10000005", {
        lat: 32.005,
        lon: -101.995,
        kbElevationFt: null,
        elevationCode: null,
        formationTops: [top("WOLFCAMP", 8000)],
      }),
    ];
    const r = await run("rrc_structure_surface", { lat: LAT0, lon: LON0, formation: "WOLFCAMP" });

    expect(r.ok).toBe(true);
    expect(r.population.wells_in_radius).toBe(5);
    expect(r.population.placed_in_subsea).toBe(4);
    expect(r.population.excluded_no_datum).toBe(1);
    expect(r.population.excluded_apis).toEqual(["10000005"]);
    // The fit is the same one the four-well fixture gives, untouched.
    expect(r.fit.n).toBe(4);
    expect(r.fit.r2).toBeCloseTo(1, 10);
    expect(r.fit.dip_deg).toBeCloseTo(1.8538, 3);
    expect(r.points.map((p: { api: string }) => p.api)).not.toContain("10000005");
  });

  test("picks are never merged across wells", async () => {
    feeder.wells = STRUCTURE;
    const wolf = await run("rrc_structure_surface", { lat: LAT0, lon: LON0, formation: "WOLFCAMP" });
    // Each well's point carries its OWN filed depth, and no well inherits another's.
    expect(
      Object.fromEntries(wolf.points.map((p: { api: string; filed_pick_ft: number }) => [p.api, p.filed_pick_ft]))
    ).toEqual({
      "10000001": 8000,
      "10000002": 8100,
      "10000003": 8000,
      "10000004": 8100,
    });

    // Only well 10000003 filed a SPRABERRY. If picks leaked between wells the
    // population would be four; it is one, and the tool refuses.
    const spraberry = await run("rrc_structure_surface", {
      lat: LAT0,
      lon: LON0,
      formation: "SPRABERRY",
    });
    expect(spraberry.ok).toBe(false);
    expect(spraberry.usable_apis).toEqual(["10000003"]);
    expect(spraberry.population.with_this_pick).toBe(1);
  });

  test("refuses to fit a plane through three points", async () => {
    feeder.wells = STRUCTURE.slice(0, 3);
    const r = await run("rrc_structure_surface", { lat: LAT0, lon: LON0, formation: "WOLFCAMP" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/needs 4/);
    expect(r.population.with_this_pick).toBe(3);
    expect(r.fit).toBeUndefined();
  });

  test("refuses a collinear population, which fixes no dip direction", async () => {
    feeder.wells = [8000, 8100, 8200, 8300].map((depth, i) =>
      well(`2000000${i}`, { lat: LAT0 + i * 0.01, lon: LON0, formationTops: [top("WOLFCAMP", depth)] })
    );
    const r = await run("rrc_structure_surface", { lat: LAT0, lon: LON0, formation: "WOLFCAMP" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/collinear/);
  });
});

describe("rrc_contact_from_offsets", () => {
  /**
   * Six wells, KB 3,000 ft. The crossover is placed between the deepest dry
   * perforation base (8,200 ft, so -5,200 subsea) and the shallowest wet
   * perforation top (8,300 ft, so -5,300 subsea), which brackets a contact at
   * their midpoint: -5,250 ft subsea.
   */
  const CONTACT_WELLS = [
    well("30000001", { perforations: [perf(8000, 8100)] }),
    well("30000002", { perforations: [perf(8100, 8200)] }),
    well("30000003", { perforations: [perf(8300, 8400)] }),
    well("30000004", { perforations: [perf(8400, 8500)] }),
    well("30000005", { perforations: [perf(8050, 8150)] }),
    well("30000006", { perforations: [perf(8350, 8450)] }),
  ];
  const CONTACT_TESTS = [
    { api: "30000001", test_date: "2025-03-01", daily_oil: 50, daily_water: 0, daily_gas: 40, gas_oil_ratio: 800, producing_method: "P" },
    { api: "30000002", test_date: "2025-03-01", daily_oil: 40, daily_water: 5, daily_gas: 30, gas_oil_ratio: 750, producing_method: "P" },
    { api: "30000003", test_date: "2025-03-01", daily_oil: 5, daily_water: 95, daily_gas: 4, gas_oil_ratio: 800, producing_method: "P" },
    { api: "30000004", test_date: "2025-03-01", daily_oil: 2, daily_water: 98, daily_gas: 2, gas_oil_ratio: 800, producing_method: "P" },
    { api: "30000005", test_date: "2025-03-01", daily_oil: 30, daily_water: 10, daily_gas: 20, gas_oil_ratio: 700, producing_method: "P" },
    { api: "30000006", test_date: "2025-03-01", daily_oil: 1, daily_water: 60, daily_gas: 1, gas_oil_ratio: 900, producing_method: "P" },
  ];

  test("finds the crossover the fixture was built around", async () => {
    feeder.wells = CONTACT_WELLS;
    db.oil = CONTACT_TESTS;
    const r = await run("rrc_contact_from_offsets", { lat: LAT0, lon: LON0 });

    expect(r.ok).toBe(true);
    expect(r.dry_wells).toBe(3);
    expect(r.wet_wells).toBe(3);
    expect(r.bracket.deepest_dry_perf_subsea_ft).toBe(-5200);
    expect(r.bracket.shallowest_wet_perf_subsea_ft).toBe(-5300);
    expect(r.bracket.clean_crossover).toBe(true);
    expect(r.bracket.overlap_ft).toBe(0);
    expect(r.contact_subsea_ft).toBe(-5250);
  });

  test("a well with no filed elevation cannot be placed and is counted, not assumed dry", async () => {
    feeder.wells = [
      ...CONTACT_WELLS,
      well("30000007", { kbElevationFt: null, elevationCode: null, perforations: [perf(8000, 8100)] }),
    ];
    db.oil = [
      ...CONTACT_TESTS,
      { api: "30000007", test_date: "2025-03-01", daily_oil: 0, daily_water: 500, daily_gas: 0, gas_oil_ratio: null, producing_method: "P" },
    ];
    const r = await run("rrc_contact_from_offsets", { lat: LAT0, lon: LON0 });

    expect(r.population.excluded_no_datum).toBe(1);
    expect(r.population.excluded_apis).toEqual(["30000007"]);
    expect(r.population.with_perfs_in_subsea).toBe(6);
    // The excluded well is wet at 8,000 to 8,100 ft. On somebody else's datum it
    // would drag the shallowest wet perforation up 300 ft and move the contact.
    expect(r.contact_subsea_ft).toBe(-5250);
    expect(r.wells_detail.map((w: { api: string }) => w.api)).not.toContain("30000007");
  });

  test("overlapping wet and dry perforations refuse a single contact", async () => {
    feeder.wells = CONTACT_WELLS;
    db.oil = CONTACT_TESTS.map((t) =>
      // The shallowest well now makes water, so a wet interval sits above a dry one.
      t.api === "30000001" ? { ...t, daily_oil: 1, daily_water: 99 } : t
    );
    const r = await run("rrc_contact_from_offsets", { lat: LAT0, lon: LON0 });

    expect(r.ok).toBe(true);
    expect(r.bracket.clean_crossover).toBe(false);
    expect(r.contact_subsea_ft).toBeNull();
    // Deepest dry base is now -5,200 (well 2); shallowest wet top is -5,000.
    expect(r.bracket.overlap_ft).toBe(200);
  });
});

describe("rrc_depth_reconcile", () => {
  test("flags a log deeper than the filed TD and an elevation with no datum code", async () => {
    mirror.construction = {
      filings: [
        {
          file_date: "2019-04-02",
          completion_date: null,
          plug_back_ft: null,
          elevation: 2780,
          elevation_code: null,
          casing: [],
          perforations: [],
        },
      ],
      total_depth: 9550,
      shallowest_perf: 9000,
      deepest_perf: 9400,
      has_open_hole: false,
    };
    const r = await run("rrc_depth_reconcile", {
      api: "32942025",
      log_td_ft: 9700,
      log_kb_ft: 2790,
    });

    expect(r.ok).toBe(true);
    expect(r.agrees).toBe(false);
    const fields = r.conflicts.map((c: { field: string }) => c.field);
    expect(fields).toContain("total_depth_ft");
    expect(fields).toContain("elevation_code");
    const td = r.conflicts.find((c: { field: string }) => c.field === "total_depth_ft");
    expect(td.difference_ft).toBe(150);
    expect(td.rrc_value).toBe(9550);
    // The elevation is reported as filed, never as zero for want of a code.
    expect(r.rrc.elevation_ft).toBe(2780);
    expect(r.rrc.elevation_code).toBeNull();
  });

  test("agrees when the log matches inside tolerance", async () => {
    mirror.construction = {
      filings: [
        {
          file_date: "2019-04-02",
          completion_date: null,
          plug_back_ft: null,
          elevation: 2780,
          elevation_code: "KB",
          casing: [],
          perforations: [],
        },
      ],
      total_depth: 9550,
      shallowest_perf: null,
      deepest_perf: null,
      has_open_hole: false,
    };
    const r = await run("rrc_depth_reconcile", {
      api: "32942025",
      log_td_ft: 9530,
      log_kb_ft: 2784,
    });
    expect(r.agrees).toBe(true);
    expect(r.conflicts).toEqual([]);
  });
});

describe("rrc_pick_reconcile", () => {
  test("refuses when the subject well has no datum of its own", async () => {
    feeder.wells = STRUCTURE;
    mirror.construction = { filings: [{ elevation: null, elevation_code: null }], total_depth: 9000 };
    const r = await run("rrc_pick_reconcile", {
      api: "40000001",
      formation: "WOLFCAMP",
      log_pick_ft: 8050,
    });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/subsea/);
  });

  test("measures the log pick against the offsets' fitted surface", async () => {
    feeder.wells = STRUCTURE;
    mirror.construction = {
      filings: [{ elevation: 3000, elevation_code: "KB" }],
      total_depth: 9000,
    };
    // Subject sits at the origin with KB 3,000, so a pick at 8,050 ft is -5,050
    // subsea against a fitted surface of -5,000: 50 ft LOW.
    const r = await run("rrc_pick_reconcile", {
      api: "40000001",
      formation: "WOLFCAMP",
      log_pick_ft: 8050,
    });
    expect(r.ok).toBe(true);
    expect(r.log.subsea_ft).toBe(-5050);
    expect(r.fit.n).toBe(4);
    expect(r.fit.projected_subsea_ft).toBeCloseTo(-5000, 6);
    expect(r.residual_ft).toBeCloseTo(-50, 6);
    expect(r.reads).toMatch(/LOW/);
  });
});

describe("rrc_productivity_index", () => {
  test("divides each well's own rate by its own net perforated feet, per formation", async () => {
    feeder.wells = [
      well("50000001", {
        formationTops: [top("SPRABERRY", 7000), top("WOLFCAMP", 8000)],
        // Two 20 ft benches: 40 net feet, not the 400 ft envelope.
        perforations: [perf(8100, 8120), perf(8480, 8500)],
      }),
      well("50000002", {
        formationTops: [top("WOLFCAMP", 8000)],
        perforations: [perf(8200, 8300)],
      }),
    ];
    db.oil = [
      { api: "50000001", test_date: "2025-01-01", daily_oil: 80, daily_water: 10, daily_gas: 60, gas_oil_ratio: 750, producing_method: "P" },
      { api: "50000002", test_date: "2025-01-01", daily_oil: 50, daily_water: 5, daily_gas: 40, gas_oil_ratio: 800, producing_method: "P" },
    ];
    const r = await run("rrc_productivity_index", { lat: LAT0, lon: LON0 });

    expect(r.ok).toBe(true);
    const detail = Object.fromEntries(
      r.wells_detail.map((w: { api: string }) => [w.api, w])
    );
    expect(detail["50000001"].net_perf_ft).toBe(40);
    expect(detail["50000001"].bopd_per_perf_ft).toBeCloseTo(2, 10); // 80 / 40
    expect(detail["50000002"].bopd_per_perf_ft).toBeCloseTo(0.5, 10); // 50 / 100
    // Both wells are perforated below their own WOLFCAMP pick, and the SPRABERRY
    // pick on the first well belongs to the first well only.
    expect(r.by_formation).toHaveLength(1);
    expect(r.by_formation[0].formation).toBe("WOLFCAMP");
    expect(r.by_formation[0].wells).toBe(2);
    expect(r.by_formation[0].oil.median).toBeCloseTo(1.25, 10); // (2 + 0.5) / 2
  });
});
