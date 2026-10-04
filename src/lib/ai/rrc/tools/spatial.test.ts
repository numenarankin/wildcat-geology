/* eslint-disable @typescript-eslint/no-explicit-any */
import { beforeEach, describe, expect, test, vi } from "vitest";

/**
 * The spatial tools, against hand-placed wells and hand-computed answers.
 *
 * Every expected value below is worked out from the geometry, never read off a
 * run. The four wells sit on ONE meridian and are spaced in whole hundredths of
 * a degree, which makes the great circle exact arithmetic: a due-north hop has
 * no longitude term, so the distance is R * dTheta and nothing else. With
 * R = 3958.7613 mi, 0.01 deg = 0.6909342 mi, and every distance here is a
 * multiple of that.
 *
 * What these are guarding is not the SQL text but the four ways these tools
 * mislead while still returning a clean-looking object:
 *
 *  - A distance that is quietly wrong. Nothing about the shape changes.
 *  - A well with no coordinate dropped instead of counted, so a lease the RRC
 *    half-geocoded reports the spacing of the half it could see.
 *  - Density arithmetic off by a section.
 *  - An unfiltered call answered instead of refused.
 */

const db = vi.hoisted(() => ({
  calls: [] as { sql: string; params: unknown[] }[],
  setWells: [] as Record<string, unknown>[],
  tracts: [] as Record<string, unknown>[],
  offsetWells: [] as Record<string, unknown>[],
  vintages: [] as Record<string, unknown>[],
  one: null as Record<string, unknown> | null,
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string, params: unknown[]) => {
    db.calls.push({ sql, params });
    if (sql.includes("completion_formation")) return [];
    if (sql.includes("wb_filing")) return [];
    if (sql.includes("orig_completion")) return db.vintages;
    if (sql.includes("survey_polygon")) return db.tracts;
    if (sql.includes("on_schedule desc nulls last")) return db.offsetWells;
    if (sql.includes("rrc.wellbore")) return db.setWells;
    throw new Error(`unexpected query: ${sql.slice(0, 80)}`);
  },
  rrcQueryOne: async (sql: string, params: unknown[]) => {
    db.calls.push({ sql, params });
    return db.one;
  },
}));

const q = vi.hoisted(() => ({
  pipelines: [] as Record<string, unknown>[],
  disposal: [] as Record<string, unknown>[],
}));

vi.mock("@/lib/scout/rrc-queries", () => ({
  getPipelines: async () => q.pipelines,
  findDisposal: async () => q.disposal,
  getInjectionEdge: async () => ({ reported: "2025-06" }),
  // The real resolver is a lookup table; only its two outcomes matter here.
  resolveCounty: (ref: string) =>
    /^midland$/i.test(ref.trim()) ? { county_no: "329", county_name: "MIDLAND" } : null,
}));

const { TOOLS } = await import("./spatial");

async function call(name: string, args: Record<string, unknown> = {}): Promise<any> {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new Error(`no tool named ${name}`);
  const parsed = tool.args.safeParse(args);
  if (!parsed.success) throw new Error(`bad args for ${name}: ${parsed.error.message}`);
  return (await tool.run(parsed.data as never)) as any;
}

/** R * 0.01 deg in radians, the unit every hand-computed distance is built from. */
const HOP = 3958.7613 * 0.01 * (Math.PI / 180); // 0.69093420 mi

const LON = -102.0;

const well = (api: string, lat: number | null, over: Record<string, unknown> = {}) => ({
  api_number: api,
  operator_name: "PERMIAN DEEP ROCK OIL CO.  LLC",
  lease_name: "CHARGER 110",
  well_type_name: "PRODUCING",
  county_name: "MIDLAND",
  lat,
  lon: lat === null ? null : LON,
  bottom_lat: null,
  bottom_lon: null,
  distance_mi: null,
  ...over,
});

/**
 * Four wells on one meridian: 32.00, 32.01, 32.03, 32.10.
 *
 * Gaps of 0.01, 0.02 and 0.07 degrees, so the nearest-neighbour distances are
 * 1, 1, 2 and 7 hops. Nothing here is symmetric by accident: C's nearest is B
 * and not D, which is what makes the median land between two different values.
 */
const FOUR = [
  well("32900001", 32.0),
  well("32900002", 32.01),
  well("32900003", 32.03),
  well("32900004", 32.1),
];

beforeEach(() => {
  db.calls = [];
  db.setWells = [];
  db.tracts = [];
  db.offsetWells = [];
  db.vintages = [];
  db.one = null;
  q.pipelines = [];
  q.disposal = [];
});

// ------------------------------------------------------------------ 23

describe("rrc_spacing", () => {
  test("nearest-neighbour distances are the hops between the wells", async () => {
    db.setWells = [...FOUR];
    const r = await call("rrc_spacing", { operator_no: "217012" });

    expect(r.ok).toBe(true);
    expect(r.wells_located).toBe(4);
    // A and B are each other's nearest at one hop; C's nearest is B at two
    // hops, not D at seven; D's nearest is C at seven.
    expect(r.nearest_neighbour_mi.min).toBeCloseTo(HOP, 6);
    expect(r.nearest_neighbour_mi.min).toBeCloseTo(0.6909342, 6);
    expect(r.nearest_neighbour_mi.max).toBeCloseTo(7 * HOP, 6);
    expect(r.nearest_neighbour_mi.max).toBeCloseTo(4.8365394, 6);
    // Sorted [1, 1, 2, 7] hops: the median is the mean of the middle two.
    expect(r.nearest_neighbour_mi.median).toBeCloseTo(1.5 * HOP, 6);
    expect(r.nearest_neighbour_mi.median).toBeCloseTo(1.0364013, 6);
    expect(r.nearest_neighbour_mi.mean).toBeCloseTo((11 / 4) * HOP, 6);
    // Linear-interpolated p90 of [1, 1, 2, 7]: index 2.7, so 2 + 0.7 * (7 - 2).
    expect(r.nearest_neighbour_mi.p90).toBeCloseTo(5.5 * HOP, 6);
    expect(r.median_nearest_neighbour_ft).toBeCloseTo(1.5 * HOP * 5280, 3);
    expect(r.median_nearest_neighbour_ft).toBeCloseTo(5472.199, 2);
    expect(r.collocated_pairs).toBe(0);
  });

  test("drainage area is the section conversion of the median spacing", async () => {
    db.setWells = [...FOUR];
    const r = await call("rrc_spacing", { operator_no: "217012" });

    // 1.0364013 mi squared is 1.0741277 square miles, times 640 acres.
    expect(r.section_acres).toBe(640);
    expect(r.drainage_acres_from_spacing).toBeCloseTo((1.5 * HOP) ** 2 * 640, 6);
    expect(r.drainage_acres_from_spacing).toBeCloseTo(687.4417, 3);
    // Median wells per occupied section is 1, so the density route says a whole
    // section each. The two routes disagreeing by 47 acres IS the clustering.
    expect(r.drainage_acres_from_density).toBe(640);
  });

  test("wells per section counts one-mile cells, not the set", async () => {
    db.setWells = [...FOUR];
    const r = await call("rrc_spacing", { operator_no: "217012" });

    // Cells are laid from the south-west corner, 69 miles to the degree of
    // latitude: 0.00 and 0.01 deg are 0.00 and 0.69 mi north, both in cell 0;
    // 0.03 deg is 2.07 mi, cell 2; 0.10 deg is 6.90 mi, cell 6.
    expect(r.occupied_sections).toBe(3);
    expect(r.wells_per_section.max).toBe(2);
    expect(r.wells_per_section.median).toBe(1);
    expect(r.wells_per_section.mean).toBeCloseTo(4 / 3, 10);
  });

  test("wells with no coordinate are counted, not dropped", async () => {
    db.setWells = [...FOUR, well("32900005", null), well("32900006", null)];
    const r = await call("rrc_spacing", { operator_no: "217012" });

    expect(r.wells_in_set).toBe(6);
    expect(r.wells_located).toBe(4);
    expect(r.wells_without_coordinates).toBe(2);
    expect(r.coverage_known).toBe(true);
    // The two ungeocoded wells change the reported coverage and nothing else:
    // every distance is still the four-well answer.
    expect(r.nearest_neighbour_mi.median).toBeCloseTo(1.0364013, 6);
    expect(r.occupied_sections).toBe(3);
    expect(r.notes.some((n: string) => n.includes("2 of 6 wells"))).toBe(true);
  });

  test("a radius search says its missing count is not a coverage claim", async () => {
    db.setWells = [...FOUR];
    const r = await call("rrc_spacing", { lat: 32.0, lon: LON, radius_mi: 10 });

    expect(r.coverage_known).toBe(false);
    expect(r.wells_without_coordinates).toBe(0);
    expect(r.notes.some((n: string) => n.includes("not a coverage claim"))).toBe(true);
    expect(r.wells_per_section_over_search_disc).toBeCloseTo(4 / (Math.PI * 100), 10);
  });

  test("an unfiltered call is refused without touching the mirror", async () => {
    const r = await call("rrc_spacing", {});
    expect(r.ok).toBe(false);
    expect(r.error).toContain("county");
    expect(r.error).toContain("operator_no");
    expect(r.error).toContain("refused");
    expect(db.calls).toHaveLength(0);
  });

  test("a county that is not a county is refused, not scanned", async () => {
    const r = await call("rrc_spacing", { county: "Fremont" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("Not a Texas county");
    expect(db.calls).toHaveLength(0);
  });

  test("one more well than asked for means truncated, and it is not returned", async () => {
    db.setWells = [...FOUR, well("32900005", 32.2)];
    const r = await call("rrc_spacing", { county: "Midland", limit: 4 });

    expect(r.wells_in_set).toBe(4);
    expect(r.truncated).toBe(true);
    // The limit the mirror sees is one higher, which is how truncation is
    // OBSERVED rather than assumed.
    expect(db.calls[0].params.at(-1)).toBe(5);
  });

  test("a pad is flagged as a pad, not sold as a two-acre drainage area", async () => {
    // 0.0001 deg apart is 36.5 ft: one pad, two wellheads. Left unflagged the
    // spacing route reports a drainage area of hundredths of an acre, which is
    // arithmetically right and says nothing about the reservoir.
    db.setWells = [well("32900001", 32.0), well("32900002", 32.0001), well("32900003", 32.03)];
    const r = await call("rrc_spacing", { operator_no: "217012" });

    expect(r.collocated_pairs).toBe(2);
    expect(r.drainage_acres_from_spacing).toBeCloseTo((0.01 * HOP) ** 2 * 640, 10);
    expect(r.notes.some((n: string) => n.includes("PAD, not a spacing pattern"))).toBe(true);
  });

  test("bottomhole is measured on bottomhole wells only, never mixed with surface", async () => {
    db.setWells = [
      well("32900001", 32.0, { bottom_lat: 32.0, bottom_lon: LON }),
      well("32900002", 32.01, { bottom_lat: 32.02, bottom_lon: LON }),
      well("32900003", 32.03),
    ];
    const r = await call("rrc_spacing", { operator_no: "217012", datum: "bottomhole" });

    expect(r.wells_located).toBe(2);
    expect(r.wells_without_coordinates).toBe(1);
    // Bottomholes are 0.02 deg apart even though the wellheads are 0.01 apart.
    expect(r.nearest_neighbour_mi.median).toBeCloseTo(2 * HOP, 6);
  });
});

// ------------------------------------------------------------------ 24

/** A square tract, 0.02 deg on a side, centred on the well at 32.00 / -102.00. */
const SQUARE = JSON.stringify({
  type: "Polygon",
  coordinates: [
    [
      [-102.01, 31.99],
      [-101.99, 31.99],
      [-101.99, 32.01],
      [-102.01, 32.01],
      [-102.01, 31.99],
    ],
  ],
});

/**
 * A right triangle whose BOUNDING BOX holds the well and whose outline does
 * not: the hypotenuse runs from (-101.99, 32.02) to (-102.02, 31.99), so at
 * longitude -102.00 it sits at latitude 32.01, a hundredth north of the well.
 */
const TRIANGLE = JSON.stringify({
  type: "Polygon",
  coordinates: [
    [
      [-102.02, 32.02],
      [-101.99, 32.02],
      [-102.02, 31.99],
      [-102.02, 32.02],
    ],
  ],
});

describe("rrc_footprint", () => {
  test("a tract is credited only when the well is inside its outline", async () => {
    db.setWells = [well("32900001", 32.0)];
    db.tracts = [
      {
        objectid: 1,
        abstract_number: "00164",
        abstract_label: "A-64",
        survey_name: "T&P RR CO",
        block_number: "37",
        acres: 640,
        min_lon: -102.01,
        min_lat: 31.99,
        max_lon: -101.99,
        max_lat: 32.01,
        geojson: SQUARE,
      },
      {
        objectid: 2,
        abstract_number: "00181",
        abstract_label: "A-181",
        survey_name: "T&P RR CO",
        block_number: "37",
        acres: 653,
        min_lon: -102.02,
        min_lat: 31.99,
        max_lon: -101.99,
        max_lat: 32.02,
        geojson: TRIANGLE,
      },
    ];
    const r = await call("rrc_footprint", { operator_no: "217012" });

    // Both tracts' boxes hold the point; only the square holds the point. Take
    // the box and the acreage doubles to 1,293.
    expect(r.tract_count).toBe(1);
    expect(r.tracts[0].abstract).toBe("A-64");
    expect(r.tract_acres_total).toBe(640);
    expect(r.wells_in_no_tract).toBe(0);
  });

  test("one tract holding several wells is still one tract of acreage", async () => {
    db.setWells = [well("32900001", 32.0), well("32900002", 32.005), well("32900003", 32.9)];
    db.tracts = [
      {
        objectid: 1,
        abstract_number: "00164",
        abstract_label: "A-64",
        survey_name: "T&P RR CO",
        block_number: "37",
        acres: 640,
        min_lon: -102.01,
        min_lat: 31.99,
        max_lon: -101.99,
        max_lat: 32.01,
        geojson: SQUARE,
      },
    ];
    const r = await call("rrc_footprint", { operator_no: "217012" });

    expect(r.tracts[0].wells_inside).toBe(2);
    expect(r.tract_acres_total).toBe(640);
    // The third well is a mile north of the tract and the layer placed it in
    // nothing, which is a gap in the survey layer, not unowned land.
    expect(r.wells_in_no_tract).toBe(1);
  });

  test("every result carries the no-lease-lines caveat", async () => {
    db.setWells = [well("32900001", 32.0)];
    const r = await call("rrc_footprint", { operator_no: "217012" });
    expect(r.notes.some((n: string) => n.includes("NO lease boundaries"))).toBe(true);
    expect(r.notes.some((n: string) => n.includes("bigger than the lease"))).toBe(true);
  });

  test("a footprint with no operator and no lease is refused", async () => {
    const r = await call("rrc_footprint", { county: "Midland" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("operator_no");
    expect(db.calls).toHaveLength(0);
  });
});

// ------------------------------------------------------------------ 25

describe("rrc_offsets", () => {
  const offset = (api: string, lat: number) => ({
    api_number: api,
    operator_name: "PERMIAN DEEP ROCK OIL CO.  LLC",
    lease_name: "CHARGER 110",
    lat,
    lon: LON,
    bottom_lat: null,
    bottom_lon: null,
    distance_mi: null,
  });

  test("vintage keeps the wells inside the window and says why the rest went", async () => {
    db.offsetWells = [offset("32900002", 32.01), offset("32900003", 32.03)];
    db.vintages = [
      { api_number: "32900002", orig_completion: new Date("2019-06-30T00:00:00Z") },
      { api_number: "32900003", orig_completion: new Date("1978-04-01T00:00:00Z") },
    ];
    const r = await call("rrc_offsets", {
      lat: 32.0,
      lon: LON,
      radius_mi: 5,
      completed_after: "2015",
    });

    expect(r.apis).toEqual(["32900002"]);
    expect(r.completed_after).toBe("2015-01-01");
    expect(r.included[0].completed).toBe("2019-06-30");
    // One hop north of the search point, computed from the arc and not read
    // back off the tool.
    expect(r.included[0].distance_mi).toBeCloseTo(HOP, 6);
    expect(r.excluded).toEqual([
      { api_number: "32900003", distance_mi: expect.any(Number), why: "completed 1978-04-01, before 2015-01-01" },
    ]);
  });

  test("a well with no completion date is excluded and counted, never assumed in", async () => {
    db.offsetWells = [offset("32900002", 32.01)];
    db.vintages = [];
    const r = await call("rrc_offsets", { lat: 32.0, lon: LON, completed_after: "2015" });

    expect(r.apis).toEqual([]);
    expect(r.excluded[0].why).toContain("no completion date on file");
    expect(r.notes.some((n: string) => n.includes("1 well(s)"))).toBe(true);
  });

  test("the target well is not returned as its own offset", async () => {
    db.one = { lat: 32.0, lon: LON };
    db.offsetWells = [offset("32900001", 32.0), offset("32900002", 32.01)];
    const r = await call("rrc_offsets", { api: "32900001" });

    expect(r.apis).toEqual(["32900002"]);
    expect(r.excluded[0].why).toBe("is the target well");
  });

  test("a target the RRC never geocoded is refused rather than centred on nothing", async () => {
    db.one = { lat: null, lon: null };
    const r = await call("rrc_offsets", { api: "32900001" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("No surface location");
  });

  test("no api and no point is refused", async () => {
    const r = await call("rrc_offsets", {});
    expect(r.ok).toBe(false);
    expect(r.error).toContain("lat and lon");
  });
});

// ------------------------------------------------------------------ 79

/** A due-east line at latitude 32.01, one hop north of the test point. */
const EAST_WEST = (lat: number) =>
  JSON.stringify({
    type: "LineString",
    coordinates: [
      [-102.05, lat],
      [-101.95, lat],
    ],
  });

const segment = (over: Record<string, unknown>) => ({
  objectid: 1,
  p5_num: "836037",
  operator_name: "TARGA MIDSTREAM SERVICES LLC",
  system_name: "SANDHILLS",
  commodity: "NATURAL GAS",
  commodity_desc: "NATURAL GAS",
  diameter: 6.63,
  status: "In Service",
  interstate: "No",
  t4permit: "05123",
  length_mi: 6.0,
  geojson: EAST_WEST(32.01),
  ...over,
});

describe("rrc_takeaway", () => {
  test("distance is to the nearest point on the line, not to a vertex", async () => {
    // Vertices sit 2.9 miles east and west; the line itself passes one hop due
    // north. A nearest-vertex answer would report 2.98 mi instead of 0.69.
    q.pipelines = [segment({})];
    const r = await call("rrc_takeaway", { lat: 32.0, lon: LON, radius_mi: 5 });

    expect(r.nearest_in_service.distance_mi).toBeCloseTo(HOP, 6);
    expect(r.nearest_in_service.distance_mi).toBeCloseTo(0.6909342, 6);
  });

  test("abandoned pipe is reported apart and never offered as takeaway", async () => {
    q.pipelines = [
      segment({}),
      segment({
        objectid: 2,
        status: "Abandoned",
        system_name: "MIDWAY SOUTH FIELD",
        // Half a hop north: closer than the live line, and dead.
        geojson: EAST_WEST(32.005),
      }),
    ];
    const r = await call("rrc_takeaway", { lat: 32.0, lon: LON, radius_mi: 5 });

    expect(r.nearest_in_service.objectid).toBe(1);
    expect(r.nearest_out_of_service.objectid).toBe(2);
    expect(r.nearest_out_of_service.distance_mi).toBeCloseTo(0.5 * HOP, 6);
    expect(r.in_service_segments).toBe(1);
    expect(r.systems_within_radius).toBe(1);
  });

  test("a lease with no located well is refused rather than measured from nowhere", async () => {
    db.setWells = [well("32900001", null)];
    const r = await call("rrc_takeaway", { lease: "O/08/45552" });
    expect(r.ok).toBe(false);
    expect(r.error).toContain("has a surface coordinate on file");
  });

  test("no point and no entity is refused", async () => {
    const r = await call("rrc_takeaway", {});
    expect(r.ok).toBe(false);
    expect(r.error).toContain("refused");
  });
});

// ------------------------------------------------------------------ 80

describe("rrc_chokepoint", () => {
  test("wells go to the nearest in-service system and shares sum to one", async () => {
    db.setWells = [well("32900001", 32.0), well("32900002", 32.02)];
    q.pipelines = [
      // At 32.005: nearest to the well at 32.00.
      segment({ objectid: 1, system_name: "SANDHILLS", geojson: EAST_WEST(32.005), length_mi: 6 }),
      // At 32.03: nearest to the well at 32.02.
      segment({
        objectid: 2,
        p5_num: "617094",
        operator_name: "ONEOK WESTEX TRANSMISSION,L.L.C.",
        system_name: "WESTEX",
        geojson: EAST_WEST(32.03),
        length_mi: 2,
      }),
    ];
    q.disposal = [];
    const r = await call("rrc_chokepoint", { lat: 32.0, lon: LON, radius_mi: 5 });

    expect(r.wells_attributed).toBe(2);
    const sandhills = r.pipeline.ranked.find((s: any) => s.system_name === "SANDHILLS");
    const westex = r.pipeline.ranked.find((s: any) => s.system_name === "WESTEX");
    expect(sandhills.dependent_wells).toBe(1);
    expect(westex.dependent_wells).toBe(1);
    expect(sandhills.miles_in_area).toBe(6);
    // Two systems at half the wells each: HHI is 2 * 50^2 = 5,000.
    expect(r.pipeline.hhi_by_dependent_wells).toBeCloseTo(5000, 6);
    // And 6 miles against 2: 75^2 + 25^2 = 6,250.
    expect(r.pipeline.hhi_by_miles).toBeCloseTo(6250, 6);
    expect(r.pipeline.top_system_dependent_share).toBe(0.5);
  });

  test("disposal is ranked by barrels a day and unfiled wells are never zeroed", async () => {
    db.setWells = [];
    q.pipelines = [];
    q.disposal = [
      {
        uic_no: "0001",
        api_number: "32900007",
        operator_name: "A",
        lease_name: "L",
        distance_mi: 1,
        is_commercial: true,
        max_bbl_per_day: 30000,
        recentBblPerDay: 24000,
      },
      {
        uic_no: "0002",
        api_number: "32900008",
        operator_name: "B",
        lease_name: "M",
        distance_mi: 2,
        is_commercial: true,
        max_bbl_per_day: 20000,
        recentBblPerDay: 8000,
      },
      {
        uic_no: "0003",
        api_number: "32900009",
        operator_name: "C",
        lease_name: "N",
        distance_mi: 3,
        is_commercial: true,
        max_bbl_per_day: 25000,
        recentBblPerDay: null,
      },
    ];
    const r = await call("rrc_chokepoint", { lat: 32.0, lon: LON, radius_mi: 5 });

    expect(r.disposal.wells).toBe(3);
    expect(r.disposal.wells_scored).toBe(2);
    expect(r.disposal.area_bbl_per_day).toBe(32000);
    // 24,000 of 32,000 is 75%, so HHI is 75^2 + 25^2 = 6,250.
    expect(r.disposal.top_well_share).toBe(0.75);
    expect(r.disposal.hhi_by_bbl).toBeCloseTo(6250, 6);
    // The third well never filed. Ranked at zero it would look like the safest
    // thing in the area; it is listed unscored instead.
    expect(r.disposal.unscored.map((d: any) => d.uic_no)).toEqual(["0003"]);
    expect(r.disposal.reported_through).toBe("2025-06");
  });

  test("proximity is named as a proxy, not sold as a connection", async () => {
    db.setWells = [];
    const r = await call("rrc_chokepoint", { lat: 32.0, lon: LON });
    expect(r.notes.some((n: string) => n.includes("P-4"))).toBe(true);
    expect(r.notes.some((n: string) => n.includes("PROXIMITY"))).toBe(true);
  });
});

// ------------------------------------------------------------------ 81

describe("rrc_pipeline_activity", () => {
  test("refuses every call and names what the record is missing", async () => {
    const r = await call("rrc_pipeline_activity", { lat: 32.0, lon: LON, since_year: 2020 });

    expect(r.ok).toBe(false);
    expect(r.error).toContain("no date of any kind");
    expect(r.missing.length).toBeGreaterThan(0);
    expect(r.instead.some((s: string) => s.includes("rrc_takeaway"))).toBe(true);
    // A refusal that queried the mirror would be a refusal with a bill.
    expect(db.calls).toHaveLength(0);
  });

  test("the catalog line says so, so the model does not have to call to find out", () => {
    const tool = TOOLS.find((t) => t.name === "rrc_pipeline_activity")!;
    expect(tool.summary).toContain("REFUSED");
  });
});

describe("the catalog", () => {
  test("carries the six spatial tools", () => {
    expect(TOOLS.map((t) => t.name)).toEqual([
      "rrc_spacing",
      "rrc_footprint",
      "rrc_offsets",
      "rrc_takeaway",
      "rrc_chokepoint",
      "rrc_pipeline_activity",
    ]);
  });
});
