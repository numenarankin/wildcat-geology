import { describe, expect, test, vi } from "vitest";

/**
 * The uphole-recompletion catalog, against a wellbore built by hand here so the
 * right answer is arithmetic done in this file rather than by the code.
 *
 * Four properties carry the weight, and each is a wrong answer with a rig
 * behind it:
 *
 *  1. A FORMATION THE BIT WENT THROUGH AND NOBODY SHOT is the whole product of
 *     this file. If the inventory misses one, the tool has no reason to exist.
 *  2. PERFORATIONS ARE NEVER MERGED ACROSS FILINGS. A set at 2,000 to 2,100 on
 *     a 1985 filing and one at 6,500 to 6,600 on a 2010 filing is not an open
 *     hole from 2,000 to 6,600, and anything at 4,000 is still behind pipe.
 *  3. `top_of_cement` IS FREE TEXT and refuses rather than parses. "2000 (E" is
 *     not a depth, and reading 2,000 out of it would report isolation on a well
 *     that has none.
 *  4. NO DOLLARS. The RRC record carries no cost, so no tool here may emit one.
 */

const db = vi.hoisted(() => ({
  /** Formation tops per api, as `rrc.completion_formation` rows. */
  formations: [] as {
    api_no: string;
    formation: string | null;
    depth: string | null;
    depth_tmd: string | null;
    user_isolated: string | null;
  }[],
  /** `rrc.wb_perf` rows, each already carrying the filing it belongs to. */
  perfs: [] as {
    api_number: string;
    file_date: string | null;
    top_ft: number | null;
    bottom_ft: number | null;
    open_hole_code: string | null;
  }[],
  completions: [] as Record<string, string | null>[],
  wellbores: [] as Record<string, string | null>[],
  leaseProduction: [] as Record<string, string | number | null>[],
  fields: [] as Record<string, string | null>[],
  locations: new Map<string, { lat: number; lon: number }>(),
  construction: new Map<string, unknown>(),
  dossiers: new Map<string, unknown>(),
  operators: new Map<string, unknown>(),
  pipelines: [] as unknown[],
  offsets: { wells: [] as unknown[], truncated: false },
  queries: [] as string[],
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string) => {
    db.queries.push(sql);
    if (sql.includes("completion_formation")) return db.formations;
    if (sql.includes("rrc.wb_perf")) return db.perfs;
    if (sql.includes("rrc.wellbore")) return db.wellbores;
    if (sql.includes("rrc.lease_production")) return db.leaseProduction;
    if (sql.includes("rrc.field")) return db.fields;
    if (sql.includes("from rrc.completion")) return db.completions;
    throw new Error(`unexpected query: ${sql.slice(0, 70)}`);
  },
  rrcQueryOne: async (sql: string, params: unknown[]) => {
    db.queries.push(sql);
    if (sql.includes("well_location")) return db.locations.get(String(params[0]).trim()) ?? null;
    if (sql.includes("rrc.field")) return db.fields.find((f) => f.field_no === params[0]) ?? null;
    throw new Error(`unexpected query: ${sql.slice(0, 70)}`);
  },
  rrcQuerySlow: async () => [],
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getWellConstruction: async (api: string) => db.construction.get(api.trim()) ?? null,
  getWellDossier: async (api: string) => db.dossiers.get(api.trim()) ?? null,
  getOperatorDossier: async (no: string) => db.operators.get(no.trim()) ?? null,
  getPipelines: async () => db.pipelines,
}));

vi.mock("../offsets", () => ({
  offsetWellbores: async () => db.offsets,
}));

const { TOOLS } = await import("./recompletion");

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Result = any;

const find = (name: string) => {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`No tool ${name}. Have: ${TOOLS.map((t) => t.name).join(", ")}`);
  return tool;
};

const call = async (name: string, args: Record<string, unknown>): Promise<Result> =>
  (await find(name).run(find(name).args.parse(args) as never)) as Result;

// --------------------------------------------------------------- fixtures

/**
 * WELL A, 31700001, built by hand.
 *
 * Two filings, and they are the point:
 *
 *   1985-03-01  perforated 2,000 to 2,100, and re-reports 7,000 to 7,100
 *   2010-05-01  perforated 6,500 to 6,600 and 7,000 to 7,100
 *               5 1/2" casing set at 8,200, cement top filed as "4000"
 *               8 5/8" casing set at 2,000, cement top filed as "SURF"
 *               plugged back to 8,000
 *   total depth 9,000
 *
 * Formation tops from the W-2 record:
 *
 *   YATES          1,500  never shot, and ABOVE every perforation
 *   SAN ANDRES     3,000  never shot
 *   MERGE PROBE    4,000  never shot, and sits between the two filings' perfs
 *   WOLFCAMP       7,050  inside the 7,000 to 7,100 set, so NOT behind pipe
 *   NO DEPTH ZONE  "N/A"  depth unrecorded, which is not zero
 */
const A = "31700001";
/** WELL B, whose cement top is free text that is not a depth. */
const B = "31700002";

function perf(
  api: string,
  file_date: string | null,
  top: number | null,
  bottom: number | null,
  oh: string | null = null
) {
  return { api_number: api, file_date, top_ft: top, bottom_ft: bottom, open_hole_code: oh };
}

function top(api: string, formation: string, depth: string | null) {
  return { api_no: api, formation, depth, depth_tmd: null, user_isolated: null };
}

function casing(size: number, set: number, toc: string | null) {
  return {
    seq: null,
    size_in: size,
    weight_lb_ft: 17,
    depth_set: set,
    hole_size_in: null,
    cement_amount: 400,
    cement_measure: "S",
    top_of_cement: toc,
  };
}

function seed() {
  db.formations = [
    top(A, "YATES", "1500"),
    top(A, "SAN ANDRES", "3000"),
    top(A, "MERGE PROBE", "4000"),
    top(A, "WOLFCAMP", "7050"),
    top(A, "NO DEPTH ZONE", "N/A"),
  ];
  db.perfs = [
    perf(A, "2010-05-01", 6500, 6600),
    perf(A, "2010-05-01", 7000, 7100),
    perf(A, "1985-03-01", 2000, 2100),
    // The SAME interval re-reported on an older filing. Counted once.
    perf(A, "1985-03-01", 7000, 7100),
  ];
  db.construction.set(A, {
    filings: [
      {
        file_date: "2010-05-01",
        completion_date: "2010-04-01",
        plug_back_ft: 8000,
        elevation: 2500,
        elevation_code: "GL",
        casing: [casing(5.5, 8200, "4000"), casing(8.625, 2000, "SURF")],
        perforations: [
          { seq: 1, top_ft: 6500, bottom_ft: 6600, open_hole: false },
          { seq: 2, top_ft: 7000, bottom_ft: 7100, open_hole: false },
        ],
      },
      {
        file_date: "1985-03-01",
        completion_date: "1985-02-01",
        plug_back_ft: null,
        elevation: 2500,
        elevation_code: "GL",
        casing: [],
        perforations: [
          { seq: 1, top_ft: 2000, bottom_ft: 2100, open_hole: false },
          { seq: 2, top_ft: 7000, bottom_ft: 7100, open_hole: false },
        ],
      },
    ],
    total_depth: 9000,
    shallowest_perf: 2000,
    deepest_perf: 7100,
    has_open_hole: false,
  });
  db.construction.set(B, {
    filings: [
      {
        file_date: "2000-01-01",
        completion_date: null,
        plug_back_ft: null,
        elevation: null,
        elevation_code: null,
        casing: [casing(5.5, 8000, "2000 (E")],
        perforations: [{ seq: 1, top_ft: 6000, bottom_ft: 6100, open_hole: false }],
      },
    ],
    total_depth: 8500,
    shallowest_perf: 6000,
    deepest_perf: 6100,
    has_open_hole: false,
  });

  db.locations.set(A, { lat: 32.0, lon: -102.0 });
  db.offsets = {
    truncated: false,
    wells: [
      {
        api_number: "31799999",
        distanceMi: 0.4,
        formationTops: [{ formation: "SAN ANDRES", depthFt: 3100 }],
        // Judged entirely inside this offset's own record: its own top against
        // its own perforations. No depth crosses between wells.
        perforations: [{ topFt: 3050, bottomFt: 3200, openHole: false }],
      },
      {
        api_number: "31799998",
        distanceMi: 1.1,
        formationTops: [{ formation: "SAN ANDRES", depthFt: 2950 }],
        perforations: [{ topFt: 7000, bottomFt: 7100, openHole: false }],
      },
    ],
  };

  db.dossiers.set(A, {
    header: { lease_name: "HAND BUILT", field_name: "DEEP (100)", field_number: "200", oil_gas_code: "O" },
    status: {
      well_type_name: "Oil Well",
      curr_inact_yrs: 4,
      wl_shut_in_date: "2022-01-01",
      wb_shut_in_date: null,
      multi_comp_flag: "N",
    },
    location: { lat: 32.0, lon: -102.0 },
    production: [
      { cycle: "2024-01", oil_prod_vol: 100, gas_prod_vol: 500, csgd_prod_vol: 0, gas_tot_disp: 100, csgd_tot_disp: 0, reported: true },
      { cycle: "2024-02", oil_prod_vol: 90, gas_prod_vol: 500, csgd_prod_vol: 0, gas_tot_disp: 100, csgd_tot_disp: 0, reported: true },
    ],
    // Water cut climbing hard: 20% then 60%, which is the reservoir case.
    w10: [
      { test_date: "2023-06-01", daily_oil: 4, daily_water: 6, daily_gas: 20, gas_oil_ratio: 5 },
      { test_date: "2021-06-01", daily_oil: 8, daily_water: 2, daily_gas: 16, gas_oil_ratio: 2 },
    ],
    h15: [],
    plugging: [],
    construction: db.construction.get(A),
  });

  db.operators.set("999999", {
    record: { operator_name: "HAND BUILT OPERATING" },
    // `total` is the AGGREGATE fleet count, which is what the cap is judged
    // against. It is deliberately separate from `wellRows.length`.
    wells: { total: 1, flagged14b2: 1 },
    wellRows: [
      {
        api_number: A,
        well_no: "1",
        lease_name: "HAND BUILT",
        county_name: "MIDLAND",
        well_type_name: "Oil Well",
        curr_inact_yrs: 6,
        plug_date: null,
        flagged14b2: true,
      },
    ],
  });

  // An 888-well operator, larger than the 500-well default cap and smaller than
  // the 2,000-well ceiling. Only the first hole carries formation tops, so the
  // fleet is 888 wells of which exactly one has anything behind pipe: what is
  // under test is the population arithmetic, not the geology.
  db.operators.set("888888", {
    record: { operator_name: "BIG FLEET OPERATING" },
    wells: { total: 888, flagged14b2: 0 },
    wellRows: Array.from({ length: 888 }, (_, i) => ({
      api_number: i === 0 ? A : `3172${String(i).padStart(4, "0")}`,
      well_no: String(i + 1),
      lease_name: "BIG FLEET",
      county_name: "MIDLAND",
      well_type_name: "Oil Well",
      curr_inact_yrs: 6,
      plug_date: null,
      flagged14b2: false,
    })),
  });

  db.pipelines = [
    {
      objectid: 1,
      system_name: "BIG GAS SYSTEM",
      operator_name: "SOME MIDSTREAM",
      commodity: "NATURAL GAS",
      commodity_desc: "NATURAL GAS",
      diameter: 12,
      status: "ACTIVE",
      geojson: JSON.stringify({ type: "LineString", coordinates: [[-102.01, 32.01], [-102.02, 32.02]] }),
    },
  ];

  // The analog pair: this hole completed in field 200 in 2015 and came uphole
  // into field 100 in 2018.
  db.completions = [
    { api_no: A, field_no: "200", field_name: "DEEP", operator_no: "999999", cmpl_or_recmpl_date: "01/15/2015", lease_name: "HAND BUILT", well_no: "1" },
    { api_no: A, field_no: "100", field_name: "SHALLOW", operator_no: "999999", cmpl_or_recmpl_date: "06/10/2018", lease_name: "HAND BUILT", well_no: "1" },
  ];
  db.wellbores = [
    { api_number: A, oil_gas_code: "O", district: "08", lease_number: "11111", field_number: "200" },
    { api_number: A, oil_gas_code: "O", district: "08", lease_number: "22222", field_number: "100" },
  ];
  // EWA district "08" is PDQ "10". The keys here are PDQ, so a tool that failed
  // to translate would find no production at all.
  db.leaseProduction = [
    { oil_gas_code: "O", district_no: "10", lease_no: "11111", cycle: "2017-06", oil_prod_vol: 100, gas_prod_vol: 0 },
    { oil_gas_code: "O", district_no: "10", lease_no: "11111", cycle: "2017-07", oil_prod_vol: 100, gas_prod_vol: 0 },
    { oil_gas_code: "O", district_no: "10", lease_no: "22222", cycle: "2018-07", oil_prod_vol: 400, gas_prod_vol: 0 },
    { oil_gas_code: "O", district_no: "10", lease_no: "22222", cycle: "2018-08", oil_prod_vol: 400, gas_prod_vol: 0 },
  ];
  db.fields = [
    {
      field_no: "100",
      field_name: "SHALLOW (100)",
      field_class: "B",
      field_h2s_flag: "N",
      wildcat_flag: "N",
      o_derived_rule_type_code: "",
      g_derived_rule_type_code: "SP",
      o_discovery_dt: "",
      g_discovery_dt: "",
    },
    {
      field_no: "200",
      field_name: "DEEP (200)",
      field_class: "B",
      field_h2s_flag: "N",
      wildcat_flag: "N",
      o_derived_rule_type_code: "SW",
      g_derived_rule_type_code: "",
      o_discovery_dt: "",
      g_discovery_dt: "",
    },
  ];
  db.queries = [];
}

seed();

// ------------------------------------------------------------------ 109

describe("rrc_uphole_inventory", () => {
  test("finds the formations this hole penetrated and nobody ever perforated", async () => {
    const r = await call("rrc_uphole_inventory", { api: A });
    expect(r.ok).toBe(true);
    const well = r.wells[0];

    // Hand-computed: YATES 1500, SAN ANDRES 3000 and MERGE PROBE 4000 are behind
    // pipe. WOLFCAMP 7050 sits inside 7,000 to 7,100 and is not.
    expect(well.zones.map((z: Result) => z.formation)).toEqual([
      "YATES",
      "SAN ANDRES",
      "MERGE PROBE",
    ]);
    expect(well.behind_pipe_count).toBe(3);

    // The shallowest perforation on record is 2,000, so only YATES is uphole of
    // everything this well has ever produced from.
    expect(well.shallowest_perf_top_ft).toBe(2000);
    expect(well.uphole_count).toBe(1);
    expect(well.zones.find((z: Result) => z.formation === "YATES").above_shallowest_perf).toBe(true);
    expect(well.zones.find((z: Result) => z.formation === "SAN ANDRES").above_shallowest_perf).toBe(false);

    // A top with no readable depth is reported as unrecorded, never as zero and
    // never silently dropped into the behind-pipe list.
    expect(well.unrecorded_depth_zones).toEqual(["NO DEPTH ZONE"]);
    expect(well.zones.some((z: Result) => z.depth_ft == null)).toBe(false);
  });

  test("cross-references offsets inside each offset's own record", async () => {
    const r = await call("rrc_uphole_inventory", { api: A, radius_mi: 2 });
    const sanAndres = r.offset_cross_reference.by_formation.find(
      (f: Result) => f.formation === "SAN ANDRES"
    );
    // 31799999 has San Andres at 3,100 and is perforated 3,050 to 3,200: a hit.
    // 31799998 has it at 2,950 but is perforated 7,000 to 7,100: not a hit.
    expect(sanAndres.offsets_completed_in_zone).toBe(1);
    expect(sanAndres.apis).toEqual(["31799999"]);
    expect(sanAndres.nearest_mi).toBe(0.4);
  });

  test("ranks a fleet and reports the operator's wells", async () => {
    const r = await call("rrc_uphole_inventory", { operator_no: "999999" });
    expect(r.ok).toBe(true);
    expect(r.mode).toBe("operator");
    expect(r.wells[0].api_number).toBe(A);
    expect(r.wells[0].behind_pipe_count).toBe(3);
    expect(r.wells[0].lease_name).toBe("HAND BUILT");
    // One well in the fleet, one well screened, and the answer says so in terms
    // that cannot be read as anything else.
    expect(r.fleet_total).toBe(1);
    expect(r.examined).toBe(1);
    expect(r.is_complete).toBe(true);
  });

  test("refuses without an api, an api list or an operator", async () => {
    const r = await call("rrc_uphole_inventory", {});
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/api|apis|operator_no/);
  });

  test("a fleet larger than the cap is REFUSED, never sampled", async () => {
    const r = await call("rrc_uphole_inventory", { operator_no: "888888" });
    // 888 wells against the 500-well default. The old behaviour ranked the first
    // 25 and set `truncated: true`; a ranked list of an arbitrary subset is the
    // defect, so there must be no list at all.
    expect(r.ok).toBe(false);
    expect(r.fleet_total).toBe(888);
    expect(r.examined).toBe(0);
    expect(r.is_complete).toBe(false);
    expect(r.wells).toBeUndefined();
    // The refusal has to be actionable: the true size, and the two ways out.
    expect(r.error).toMatch(/888/);
    expect(r.error).toMatch(/rrc_well_screen/);
    expect(r.error).toMatch(/limit: 888/);
  });

  test("a raised limit screens the whole fleet, and the listing is capped after the screen", async () => {
    const r = await call("rrc_uphole_inventory", { operator_no: "888888", limit: 888 });
    expect(r.ok).toBe(true);
    expect(r.fleet_total).toBe(888);
    expect(r.examined).toBe(888);
    expect(r.is_complete).toBe(true);
    // Only the hand-built hole carries formation tops, and the count is over all
    // 888 rather than over the 100 rows listed.
    expect(r.wells_with_behind_pipe).toBe(1);
    expect(r.wells_with_uphole_zone).toBe(1);
    expect(r.wells_listed).toBe(100);
    expect(r.wells.length).toBe(100);
    expect(r.wells[0].api_number).toBe(A);
    expect(r.notes.join(" ")).toMatch(/All 888 wells were screened/);
  });

  test("an explicit api list is the population and is examined in full", async () => {
    const r = await call("rrc_uphole_inventory", { apis: [A, "31700009", "31700009", " "] });
    expect(r.ok).toBe(true);
    expect(r.mode).toBe("supplied");
    // Blank and duplicate entries collapse: two distinct holes were asked for.
    expect(r.fleet_total).toBe(2);
    expect(r.examined).toBe(2);
    expect(r.is_complete).toBe(true);
    expect(r.wells.map((w: Result) => w.api_number)).toEqual([A, "31700009"]);
    expect(r.population_source).toMatch(/supplied/);
  });

  test("an api list past the hard ceiling is refused rather than trimmed", async () => {
    const r = await call("rrc_uphole_inventory", {
      apis: Array.from({ length: 2001 }, (_, i) => `3173${String(i).padStart(4, "0")}`),
    });
    expect(r.ok).toBe(false);
    expect(r.fleet_total).toBe(2001);
    expect(r.examined).toBe(0);
    expect(r.error).toMatch(/2,000/);
  });
});

// --------------------------------------------- perforations are not merged

describe("perforations are never merged across filings", () => {
  test("a zone between two filings' perforations is still behind pipe", async () => {
    const r = await call("rrc_uphole_inventory", { api: A });
    const zones = r.wells[0].zones.map((z: Result) => z.formation);
    // The 1985 filing was shot 2,000 to 2,100 and the 2010 filing 6,500 to
    // 6,600. Merging them would read as open from 2,000 to 7,100 and swallow
    // MERGE PROBE at 4,000 along with SAN ANDRES at 3,000.
    expect(zones).toContain("MERGE PROBE");
    expect(zones).toContain("SAN ANDRES");
  });

  test("the current completion is the newest filing's, not a cross-filing envelope", async () => {
    const r = await call("rrc_plugback_feasibility", { api: A, target_top_ft: 3000, target_bottom_ft: 3100 });
    expect(r.ok).toBe(true);
    // The 2010 filing's own shallowest perforation is 6,500. The 1985 filing's
    // 2,000 belongs to a different filing and must not be borrowed.
    expect(r.current_completion.file_date).toBe("2010-05-01");
    expect(r.current_completion.top_ft).toBe(6500);
    expect(r.current_completion.bottom_ft).toBe(7100);
    // 6,500 minus 3,100 = 3,400 ft of room for a plug.
    expect(r.room_ft).toBe(3400);
    expect(r.feasible).toBe(true);
  });

  test("casing comes from the newest filing alone", async () => {
    const r = await call("rrc_casing_at_depth", { api: A, top_ft: 3000, bottom_ft: 3100 });
    expect(r.ok).toBe(true);
    expect(r.filing_date).toBe("2010-05-01");
    expect(r.cased).toBe(true);
    // Two strings reach 3,100? Only the 5 1/2" at 8,200 does; the 8 5/8" stops
    // at 2,000.
    expect(r.innermost_string.size_in).toBe(5.5);
    expect(r.innermost_string.set_ft).toBe(8200);
    expect(r.strings.filter((s: Result) => s.covers_target).length).toBe(1);
    expect(r.deepest_set_ft).toBe(8200);
  });

  test("a target below the deepest string is not called cased", async () => {
    const r = await call("rrc_casing_at_depth", { api: A, top_ft: 8500 });
    expect(r.cased).toBe(false);
    expect(r.innermost_string).toBeNull();
  });
});

// ------------------------------------------------------------------ 112

describe("rrc_cement_top_check", () => {
  test("answers when the filed top of cement is plainly a depth", async () => {
    // The 5 1/2" is set at 8,200 with cement filed as "4000". A target at 5,000
    // is below the cement top, so it is behind cemented pipe.
    const covered = await call("rrc_cement_top_check", { api: A, top_ft: 5000, bottom_ft: 5100 });
    expect(covered.ok).toBe(true);
    expect(covered.refused).toBe(false);
    expect(covered.cemented).toBe(true);
    expect(covered.strings[0].top_of_cement_kind).toBe("depth");
    expect(covered.strings[0].top_of_cement_ft).toBe(4000);

    // A target at 3,000 is ABOVE the cement top of 4,000. No isolation there,
    // and the answer is a plain false rather than a refusal.
    const above = await call("rrc_cement_top_check", { api: A, top_ft: 3000, bottom_ft: 3100 });
    expect(above.refused).toBe(false);
    expect(above.cemented).toBe(false);
    expect(above.notes.join(" ")).toMatch(/squeeze, not a recompletion/);
  });

  test("reads the surface codes the tape actually uses", async () => {
    const r = await call("rrc_cement_top_check", { api: A, top_ft: 1500 });
    const shoe = r.strings.find((s: Result) => s.size_in === 8.625);
    expect(shoe.top_of_cement_kind).toBe("surface");
    expect(shoe.top_of_cement_ft).toBe(0);
  });

  test("refuses on a free-text top of cement that is not a depth", async () => {
    const r = await call("rrc_cement_top_check", { api: B, top_ft: 3000, bottom_ft: 3100 });
    expect(r.ok).toBe(true);
    // "2000 (E" starts with digits. Reading 2,000 out of it would report the
    // target isolated on a well nobody can show is isolated.
    expect(r.strings[0].top_of_cement_kind).toBe("unparsed");
    expect(r.strings[0].top_of_cement_ft).toBeNull();
    expect(r.refused).toBe(true);
    expect(r.cemented).toBeNull();
    expect(r.unparsed_values).toEqual(["2000 (E"]);
    expect(r.refusal_reason).toMatch(/do not assume isolation/i);
  });
});

// ------------------------------------------------------------------ 114

describe("rrc_squeeze_burden", () => {
  test("counts the intervals between the plug-back depth and the target", async () => {
    const r = await call("rrc_squeeze_burden", { api: A, target_top_ft: 3000, target_bottom_ft: 3100 });
    expect(r.ok).toBe(true);
    // Plug-back is 8,000 off the newest filing. Between 3,100 and 8,000 lie
    // 6,500 to 6,600 and 7,000 to 7,100. The 1985 set at 2,000 to 2,100 is
    // above the target and does not count.
    expect(r.plug_back_ft).toBe(8000);
    expect(r.plug_back_source).toBe("wb_filing");
    expect(r.intervals_to_isolate).toBe(2);
    expect(r.intervals.map((i: Result) => [i.top_ft, i.bottom_ft])).toEqual([
      [6500, 6600],
      [7000, 7100],
    ]);
    // 100 ft plus 100 ft.
    expect(r.feet_to_isolate).toBe(200);
    // 7,000 to 7,100 appears on both filings and is counted ONCE.
    expect(r.duplicate_rows_removed).toBe(1);
    expect(r.rows_by_filing).toEqual([
      { file_date: "2010-05-01", intervals: 2 },
      { file_date: "1985-03-01", intervals: 1 },
    ]);
  });

  test("a supplied plug-back depth overrides the filing", async () => {
    const r = await call("rrc_squeeze_burden", {
      api: A,
      target_top_ft: 3000,
      target_bottom_ft: 3100,
      plug_back_ft: 6700,
    });
    // Above 6,700 only the 6,500 to 6,600 set remains.
    expect(r.plug_back_source).toBe("supplied");
    expect(r.intervals_to_isolate).toBe(1);
    expect(r.feet_to_isolate).toBe(100);
  });

  test("refuses when the plug-back sits above the target", async () => {
    const r = await call("rrc_squeeze_burden", { api: A, target_top_ft: 8500, plug_back_ft: 8000 });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/at or above the base of the target/);
  });
});

// ------------------------------------------------------------------ 110

describe("rrc_zone_abandonment_reason", () => {
  test("a rising water cut reads as a reservoir answer, and uphole is the case for it", async () => {
    const r = await call("rrc_zone_abandonment_reason", { api: A });
    expect(r.ok).toBe(true);
    // Oldest test 2/(8+2) = 0.2, newest 6/(4+6) = 0.6, over two tests: a slope
    // of +0.4 per test.
    expect(r.test_trend.water_cut_latest).toBeCloseTo(0.6, 10);
    expect(r.test_trend.water_cut_slope_per_test).toBeCloseTo(0.4, 10);
    expect(r.verdict).toBe("reservoir");
    expect(r.uphole_advised).toBe(true);
  });

  test("a standing fluid level makes it mechanical, and says uphole is the wrong answer", async () => {
    const flat = JSON.parse(JSON.stringify(db.dossiers.get(A))) as Result;
    // Same rates on both tests: no water-cut trend to blame.
    flat.w10 = [
      { test_date: "2023-06-01", daily_oil: 5, daily_water: 5, daily_gas: 10, gas_oil_ratio: 2 },
      { test_date: "2021-06-01", daily_oil: 5, daily_water: 5, daily_gas: 10, gas_oil_ratio: 2 },
    ];
    flat.h15 = [
      { test_date: "2024-01-01", status: "A", test_type: "F", fluid_method: "S", mech_method: null, top_of_fluid: 1200 },
    ];
    flat.construction = db.construction.get(A);
    db.dossiers.set("31700003", flat);

    const r = await call("rrc_zone_abandonment_reason", { api: "31700003" });
    expect(r.verdict).toBe("mechanical");
    expect(r.uphole_advised).toBe(false);
    expect(r.uphole_note).toMatch(/WRONG answer/);
  });
});

// ------------------------------------------------------------------ 115

describe("rrc_uphole_analogs", () => {
  test("keys on the pair and translates the district before reading production", async () => {
    const r = await call("rrc_uphole_analogs", { from_field_no: "200", to_field_no: "100" });
    expect(r.ok).toBe(true);
    expect(r.moves_found).toBe(1);
    const a = r.analogs[0];
    expect(a.api_number).toBe(A);
    expect(a.prior_completion_cycle).toBe("2015-01");
    expect(a.moved_cycle).toBe("2018-06");
    // 12 months before the move on the old lease: two reported cycles at 100.
    expect(a.before.oil_bbl_per_month).toBe(100);
    // 12 months after, on the new lease: two cycles at 400.
    expect(a.after.oil_bbl_per_month).toBe(400);
    expect(a.oil_delta_bbl_per_month).toBe(300);
    expect(a.failed).toBe(false);
    expect(r.failure_rate).toBe(0);
    expect(r.median_oil_delta_bbl_per_month).toBe(300);
  });

  test("refuses the degenerate pair", async () => {
    const r = await call("rrc_uphole_analogs", { from_field_no: "100", to_field_no: "100" });
    expect(r.ok).toBe(false);
  });
});

// ------------------------------------------------------------------ 117/118

describe("regulatory", () => {
  test("names the reclassification and the forms when the field changes", async () => {
    const r = await call("rrc_recompletion_regulatory", { api: A, target_field_no: "100" });
    expect(r.ok).toBe(true);
    expect(r.field_changes).toBe(true);
    // Field 100 carries only a gas rule type, so the hole reclassifies O to G.
    expect(r.target_field.oil_gas_code).toBe("G");
    expect(r.reclassification).toBe(true);
    expect(r.forms_implicated).toEqual(["G-1", "P-4", "G-10"]);
    expect(r.consequences.join(" ")).toMatch(/NEW FIELD NUMBER/);
    expect(r.not_in_this_mirror.join(" ")).toMatch(/spacing/);
  });

  test("rrc_target_allowable refuses, because rrc.field carries no allowable or spacing rule", async () => {
    const r = await call("rrc_target_allowable", { field_no: "100" });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/no allowable, no spacing rule and no density rule/);
    // Special field rules exist for this field and the mirror does not hold them.
    expect(r.field.rule_type_code).toBe("SP");
    expect(r.field.rule_type_meaning).toMatch(/SPECIAL FIELD RULES/);
    expect(r.missing.length).toBeGreaterThan(0);
  });
});

// ------------------------------------------------------------------ 116/119

describe("takeaway and scoring", () => {
  test("finds the gas line and flags a lease that is not moving its gas", async () => {
    const r = await call("rrc_uphole_takeaway_check", { api: A });
    expect(r.ok).toBe(true);
    expect(r.gas_lines_within_radius).toBe(1);
    expect(r.nearest_gas_line.system_name).toBe("BIG GAS SYSTEM");
    // 1,000 mcf produced, 200 disposed: a fifth of it has anywhere to go.
    expect(r.lease_gas_mcf_last_24).toBe(1000);
    expect(r.lease_gas_disposed_last_24).toBe(200);
    expect(r.lease_gas_disposed_share).toBeCloseTo(0.2, 10);
    expect(r.takeaway).toBe("line_present_lease_not_moving_gas");
  });

  test("scores uplift and compliance relief together", async () => {
    const r = await call("rrc_reentry_value", { operator_no: "999999" });
    expect(r.ok).toBe(true);
    const w = r.scored[0];
    // One uphole zone of a possible three: 1/3. Flagged 14(b)(2) is 0.6, plus
    // six inactive years capped into 0.4 as 0.4. Relief caps at 1.
    expect(w.uphole_count).toBe(1);
    expect(w.uplift_score).toBeCloseTo(1 / 3, 10);
    expect(w.compliance_relief_score).toBeCloseTo(1, 10);
    expect(w.score).toBeCloseTo(1 / 3 + 1, 10);
    // Both levers pulled by one job, which is the point of scoring them together.
    expect(w.both).toBe(true);
    expect(r.both_count).toBe(1);
    expect(r.fleet_total).toBe(1);
    expect(r.examined).toBe(1);
    expect(r.is_complete).toBe(true);
  });

  test("rrc_reentry_value refuses a fleet larger than the cap too", async () => {
    const r = await call("rrc_reentry_value", { operator_no: "888888" });
    expect(r.ok).toBe(false);
    expect(r.fleet_total).toBe(888);
    expect(r.scored).toBeUndefined();
    expect(r.error).toMatch(/limit: 888/);
  });
});

// ------------------------------------------------------- no dollars, anywhere

describe("no tool emits a dollar figure", () => {
  /** Every tool, with arguments that reach a real answer. */
  const invocations: [string, Record<string, unknown>][] = [
    ["rrc_uphole_inventory", { api: A }],
    ["rrc_zone_abandonment_reason", { api: A }],
    ["rrc_casing_at_depth", { api: A, top_ft: 3000, bottom_ft: 3100 }],
    ["rrc_cement_top_check", { api: A, top_ft: 3000, bottom_ft: 3100 }],
    ["rrc_plugback_feasibility", { api: A, target_top_ft: 3000, target_bottom_ft: 3100 }],
    ["rrc_squeeze_burden", { api: A, target_top_ft: 3000, target_bottom_ft: 3100 }],
    ["rrc_uphole_analogs", { from_field_no: "200", to_field_no: "100" }],
    ["rrc_uphole_takeaway_check", { api: A }],
    ["rrc_recompletion_regulatory", { api: A, target_field_no: "100" }],
    ["rrc_target_allowable", { field_no: "100" }],
    ["rrc_reentry_value", { operator_no: "999999" }],
  ];

  test("all eleven tools are present", () => {
    expect(TOOLS.map((t) => t.name)).toEqual(invocations.map(([n]) => n));
    expect(TOOLS.length).toBe(11);
  });

  /**
   * A currency symbol against a number, or a numeric field named like money.
   *
   * Not a word search: several tools SAY "no cost, price or payout figure is
   * derivable", and that sentence is the refusal, not a violation.
   */
  const MONEY_KEY = /usd|dollar|cost|price|payout|revenue|npv|capex|\bafe\b/i;

  function scan(node: unknown, path: string, hits: string[]): void {
    if (typeof node === "string") {
      if (/\$\s*-?[\d.,]/.test(node)) hits.push(`${path}: ${node}`);
      return;
    }
    if (Array.isArray(node)) {
      node.forEach((v, i) => scan(v, `${path}[${i}]`, hits));
      return;
    }
    if (node && typeof node === "object") {
      for (const [k, v] of Object.entries(node)) {
        if (typeof v === "number" && MONEY_KEY.test(k)) hits.push(`${path}.${k}: ${v}`);
        scan(v, `${path}.${k}`, hits);
      }
    }
  }

  for (const [name, args] of invocations) {
    test(`${name} returns no money`, async () => {
      const hits: string[] = [];
      scan(await call(name, args), name, hits);
      expect(hits).toEqual([]);
    });
  }
});
