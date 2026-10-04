import { beforeEach, describe, expect, test, vi } from "vitest";

/**
 * The offset feeder and the harness branch that reads it.
 *
 * The mirror is mocked, and deliberately: what these check is not the SQL text
 * but the three properties a wrong implementation still satisfies at a glance.
 *
 *  - The QUERY COUNT is fixed. A per-well loop returns the same answer and takes
 *    75 round trips to do it, inside a 5 s statement timeout shared with four
 *    other branches. It is the requirement most likely to regress, because
 *    nothing about the result shape changes when it does.
 *  - Every pick stays on its own well. Tops merged across APIs read as a clean
 *    result and put a neighbour's formation top in this well's answer.
 *  - Nothing is invented to fill the shape: no DST the mirror does not carry, no
 *    datum on a filing that named none.
 */

const db = vi.hoisted(() => ({
  configured: true,
  calls: [] as { sql: string; params: unknown[] }[],
  wells: [] as Record<string, unknown>[],
  picks: [] as Record<string, unknown>[],
  construction: [] as Record<string, unknown>[],
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => db.configured,
  rrcQuery: async (sql: string, params: unknown[]) => {
    db.calls.push({ sql, params });
    if (sql.includes("rrc.well_location")) return db.wells;
    if (sql.includes("completion_formation")) return db.picks;
    if (sql.includes("wb_root")) return db.construction;
    throw new Error(`unexpected query: ${sql.slice(0, 60)}`);
  },
}));

const { offsetWellbores } = await import("./offsets");
const { registerContractTools } = await import("../geology/contract-tools");
const { TOOL } = await import("../geology/contracts");
const { ToolRegistry } = await import("../geology/registry");
import type { ContractDeps } from "../geology/contract-tools";

/** The search point, and a well one hundredth of a degree due north of it. */
const LAT = 31.9686;
const LON = -102.0779;

const well = (api: string, over: Record<string, unknown> = {}) => ({
  api_number: api,
  operator_name: "PERMIAN DEEP ROCK OIL CO.  LLC",
  lease_name: "CHARGER 110",
  lat: LAT,
  lon: LON,
  bottom_lat: null,
  bottom_lon: null,
  ...over,
});

const built = (api: string, over: Record<string, unknown> = {}) => ({
  api_number: api,
  total_depth: 9550,
  elevation: 2780,
  elevation_code: "KB",
  plug_back_ft: 9516,
  casing: [],
  perfs: [],
  ...over,
});

beforeEach(() => {
  db.configured = true;
  db.calls = [];
  db.wells = [];
  db.picks = [];
  db.construction = [];
});

describe("offsetWellbores", () => {
  test("three queries for one well, and three for twenty-five", async () => {
    db.wells = [well("32942025")];
    db.construction = [built("32942025")];
    await offsetWellbores({ lat: LAT, lon: LON, radiusMi: 1 });
    expect(db.calls).toHaveLength(3);

    db.calls = [];
    db.wells = Array.from({ length: 25 }, (_, i) => well(`3294${String(2000 + i)}`));
    db.construction = db.wells.map((w) => built(w.api_number as string));
    db.picks = db.wells.flatMap((w) => [
      { api_no: w.api_number, formation: "SPRABERRY", depth: "7100", depth_tmd: "7100" },
      { api_no: w.api_number, formation: "WOLFCAMP", depth: "8400", depth_tmd: "8400" },
    ]);
    const { wells } = await offsetWellbores({ lat: LAT, lon: LON, radiusMi: 1, limit: 25 });
    expect(wells).toHaveLength(25);
    expect(db.calls).toHaveLength(3);
  });

  test("the children are fetched by API list, not one well at a time", async () => {
    db.wells = [well("32942025"), well("32945227")];
    db.construction = [built("32942025"), built("32945227")];
    await offsetWellbores({ lat: LAT, lon: LON, radiusMi: 1 });

    const picks = db.calls.find((c) => c.sql.includes("completion_formation"))!;
    expect(picks.params[0]).toEqual(["32942025", "32945227"]);
    // `rrc.wb_*` keys on blank-padded `character`. Cast the array to text and
    // the index is unusable: 41 ms becomes 24 s.
    const cons = db.calls.find((c) => c.sql.includes("wb_root"))!;
    expect(cons.sql).toContain("bpchar[]");
    expect(cons.params[0]).toEqual(["32942025", "32945227"]);
  });

  test("each well keeps its own tops", async () => {
    db.wells = [well("32942025"), well("32945227")];
    db.construction = [built("32942025"), built("32945227")];
    db.picks = [
      { api_no: "32942025", formation: "SPRABERRY", depth: "7100.0", depth_tmd: "7100.0" },
      { api_no: "32945227", formation: "WOLFCAMP", depth: "8,400'", depth_tmd: null },
      // The same tops come back once per completion report on the well.
      { api_no: "32945227", formation: "WOLFCAMP", depth: "8,400'", depth_tmd: null },
    ];
    const { wells } = await offsetWellbores({ lat: LAT, lon: LON, radiusMi: 1 });

    expect(wells[0].formationTops).toEqual([{ formation: "SPRABERRY", depthFt: 7100 }]);
    expect(wells[1].formationTops).toEqual([{ formation: "WOLFCAMP", depthFt: 8400 }]);
  });

  test("a well the wellbore database does not carry keeps its location and loses nothing else", async () => {
    db.wells = [well("32942025")];
    db.construction = [];
    const { wells } = await offsetWellbores({ lat: LAT, lon: LON, radiusMi: 1 });
    expect(wells[0]).toMatchObject({
      api_number: "32942025",
      kbElevationFt: null,
      elevationCode: null,
      totalDepthFt: null,
      plugBackFt: null,
      perforations: [],
      casing: [],
    });
  });

  test("one more well than asked for means truncated, and it is not returned", async () => {
    db.wells = [well("32942025"), well("32945227"), well("32944951")];
    db.construction = db.wells.map((w) => built(w.api_number as string));
    const { wells, truncated } = await offsetWellbores({ lat: LAT, lon: LON, radiusMi: 1, limit: 2 });
    expect(wells.map((w) => w.api_number)).toEqual(["32942025", "32945227"]);
    expect(truncated).toBe(true);
    // The limit the mirror sees is one higher, which is how truncation is
    // OBSERVED rather than assumed.
    expect(db.calls[0].params.at(-1)).toBe(3);
  });

  test("an unconfigured mirror answers empty and queries nothing", async () => {
    db.configured = false;
    await expect(offsetWellbores({ lat: LAT, lon: LON, radiusMi: 1 })).resolves.toEqual({
      wells: [],
      truncated: false,
    });
    expect(db.calls).toHaveLength(0);
  });
});

/* ------------------------------------------------------------------ *
 * The harness branch
 * ------------------------------------------------------------------ */

/** The Python side of the contract deps. No offset branch touches it. */
const deps: ContractDeps = {
  run: async () => ({ kind: "Refusal" }),
  columns: async () => null,
  header: async () => null,
};

function registry() {
  const r = new ToolRegistry();
  registerContractTools(r, deps);
  return r;
}

const ctx = { api: "42-329-42999" };

const call = async (args: Record<string, unknown> = {}) => {
  const result = await registry().call(TOOL.offsetsWithinRadius, {
    latitude: LAT,
    longitude: LON,
    radiusFt: 5280,
    limit: 25,
    ...args,
  }, ctx);
  return result.value as {
    offsets: {
      api: string;
      distanceFt: number;
      picks: { formation: string; depthFt: number; reference: string }[];
      dst: unknown[];
      datumResolved: boolean;
    }[];
    truncated: boolean;
  };
};

describe("offsets_within_radius", () => {
  test("is registered", () => {
    expect(registry().has(TOOL.offsetsWithinRadius)).toBe(true);
  });

  test("distance is reported in feet from the search point", async () => {
    db.wells = [well("32942025"), well("32945227", { lat: LAT + 0.01 })];
    db.construction = [built("32942025"), built("32945227")];
    const { offsets } = await call();

    expect(offsets[0].distanceFt).toBeCloseTo(0, 6);
    // Due north, so the great circle is the arc itself: 3958.7613 mi * 0.01 deg
    // in radians * 5280 = 3648.13 ft.
    expect(offsets[1].distanceFt).toBeCloseTo(3648.13, 1);
  });

  test("a filed elevation and a code resolve the datum; a missing one does not", async () => {
    db.wells = [well("32942025"), well("32945227"), well("32944951")];
    db.construction = [
      built("32942025", { elevation_code: "GR" }),
      built("32945227", { elevation: null, elevation_code: null }),
      built("32944951", { elevation: 2780, elevation_code: "XX" }),
    ];
    db.picks = db.wells.map((w) => ({
      api_no: w.api_number,
      formation: "WOLFCAMP",
      depth: "8400",
      depth_tmd: "8400",
    }));
    const { offsets } = await call();

    expect(offsets[0].datumResolved).toBe(true);
    expect(offsets[0].picks[0].reference).toBe("GL");
    // No elevation, and no code: the pick still has to name a datum, and says
    // so by refusing to claim the datum is resolved.
    expect(offsets[1].datumResolved).toBe(false);
    expect(offsets[1].picks[0].reference).toBe("KB");
    // An elevation on a code we cannot map is still unresolved.
    expect(offsets[2].datumResolved).toBe(false);
  });

  test("a pick with no readable depth is dropped, not zeroed", async () => {
    db.wells = [well("32942025")];
    db.construction = [built("32942025")];
    db.picks = [
      { api_no: "32942025", formation: "SPRABERRY", depth: "7100", depth_tmd: null },
      { api_no: "32942025", formation: "WOLFCAMP", depth: "", depth_tmd: null },
    ];
    const { offsets } = await call();
    expect(offsets[0].picks).toEqual([
      { formation: "SPRABERRY", depthFt: 7100, reference: "KB" },
    ]);
  });

  test("dst is always empty, because the mirror has none", async () => {
    db.wells = [well("32942025"), well("32945227")];
    db.construction = [built("32942025"), built("32945227")];
    const { offsets } = await call();
    expect(offsets.every((o) => o.dst.length === 0)).toBe(true);
  });

  test("the subject well is not returned as its own offset", async () => {
    // The store rejects an offset that IS the subject well, which would cost
    // the whole branch. The header carries the state code; the mirror does not.
    db.wells = [well("32942999"), well("32942025")];
    db.construction = [built("32942999"), built("32942025")];
    const { offsets } = await call();
    expect(offsets.map((o) => o.api)).toEqual(["32942025"]);
  });

  test("an unconfigured mirror leaves the branch empty rather than failing", async () => {
    db.configured = false;
    await expect(call()).resolves.toEqual({ offsets: [], truncated: false });
  });
});
