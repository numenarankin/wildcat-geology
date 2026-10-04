import { beforeEach, describe, expect, test, vi } from "vitest";

/**
 * `rrc_person_search`, against the question that had no tool.
 *
 * "What is <person> doing in <county>" is three steps, and the catalog was
 * missing the first one: a person is not an operator, so operator search cannot
 * find one. People do not hold wellbores. Operating companies do, and a person
 * reaches them only through the P-5 officer file.
 *
 * Two properties carry the weight here, and both are about REFUSING to be
 * confidently wrong:
 *
 *  1. A person who is registered in Texas but holds nothing in the county asked
 *     about is an ANSWER, not a failure. It has to arrive as `ok: true` with the
 *     finding stated, because a refusal reads identically to "no such person"
 *     and those are different facts.
 *  2. A fuzzy name match must be reported as a fuzzy name match. The tool is
 *     answering about `SMITH, JOHN` when it was asked about "John Michael
 *     Smithe", and a caller that does not say so is putting words in the
 *     record's mouth.
 */

const db = vi.hoisted(() => ({
  queries: [] as { sql: string; params: unknown[] }[],
  /** Candidate pool for the resolver's one query. */
  names: [] as unknown[],
  affiliations: [] as unknown[],
  fleets: [] as unknown[],
  permits: [] as unknown[],
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string, params: unknown[]) => {
    db.queries.push({ sql, params });
    if (sql.includes("with hit as")) return db.names;
    if (sql.includes("string_agg(distinct nullif(btrim(oo.officer_title)")) return db.affiliations;
    if (sql.includes("rrc.wellbore")) return db.fleets;
    if (sql.includes("rrc.permit")) return db.permits;
    throw new Error(`unmocked query: ${sql.slice(0, 80)}`);
  },
}));

const { TOOLS } = await import("./people");
const personSearch = TOOLS.find((t) => t.name === "rrc_person_search")!;
const run = (args: unknown) => personSearch.run(args as never) as Promise<Record<string, unknown>>;

/** Andrews County is 003 in the RRC's own code handout. */
const ANDREWS = "003";

beforeEach(() => {
  db.queries = [];
  db.names = [{ officer_name: "SMITH, JOHN", operator_count: 2, sim: 0.5, surname_sim: 0.833 }];
  db.affiliations = [
    { operator_number: "100000", operator_name: "ALPHA OPERATING LLC", p5_status: "A", officer_title: "PRESIDENT" },
    { operator_number: "200000", operator_name: "BRAVO RESOURCES", p5_status: "A", officer_title: "DIRECTOR" },
  ];
  db.fleets = [
    { operator_number: "100000", wells: 40, wells_in_county: 12 },
    { operator_number: "200000", wells: 90, wells_in_county: 0 },
    // The rollup row, counted across both operators rather than added up.
    { operator_number: null, wells: 130, wells_in_county: 12 },
  ];
  db.permits = [{ operator_number: "100000", permits: 3, last_issued: "2026-04-02" }];
});

describe("rrc_person_search", () => {
  test("answers a misspelled name with the name it actually read", async () => {
    const out = await run({ name: "John Michael Smithe", county: "Andrews" });

    expect(out.ok).toBe(true);
    expect(out.resolved).toMatchObject({ officer_name: "SMITH, JOHN", matched: "surname and given name" });
    // The caller has to be told this was not an exact hit, or it will report
    // the name it was given as if the record had confirmed it.
    expect(JSON.stringify(out.notes)).toContain("not exactly");
  });

  test("narrows to the county and hands back the key every other tool takes", async () => {
    const out = await run({ name: "Smith, John", county: "Andrews" });

    // Hand-computed from the fixture: only ALPHA has anything in Andrews
    // (12 wells, 3 permits). BRAVO is bigger statewide and belongs to the same
    // person, and is correctly absent from the county answer.
    expect(out.county_summary).toMatchObject({
      county_no: ANDREWS,
      county_name: "Andrews",
      operators_active: 1,
      wells_on_schedule: 12,
      permits_last_24mo: 3,
    });
    const ops = out.operators as { operator_no: string; wells_in_county: number }[];
    expect(ops.map((o) => o.operator_no)).toEqual(["100000"]);
    expect(ops[0].wells_in_county).toBe(12);

    // Both county-scoped reads were bound to the resolved code, never to the
    // word the user typed.
    const scoped = db.queries.filter((q) => q.params.includes(ANDREWS));
    expect(scoped).toHaveLength(2);
  });

  test("counts the county total rather than adding the operators up", async () => {
    // Both operators hold the same 12 wellbores in the county, which happens
    // when one hole is on schedule to two of a person's companies across leases.
    // Added up that is 24 wells. Counted, it is 12, and 12 is the number of
    // wells there are.
    db.fleets = [
      { operator_number: "100000", wells: 40, wells_in_county: 12 },
      { operator_number: "200000", wells: 90, wells_in_county: 12 },
      { operator_number: null, wells: 118, wells_in_county: 12 },
    ];

    const out = await run({ name: "Smith, John", county: "Andrews" });
    const summary = out.county_summary as { wells_on_schedule: number };
    const ops = out.operators as { wells_in_county: number }[];

    expect(summary.wells_on_schedule).toBe(12);
    // The per-operator rows are honest on their own terms and still add to 24.
    // The headline must not be that sum.
    expect(ops.reduce((a, o) => a + o.wells_in_county, 0)).toBe(24);
  });

  test("a person with nothing in the county is an answer, not a refusal", async () => {
    db.fleets = [
      { operator_number: "100000", wells: 40, wells_in_county: 0 },
      { operator_number: "200000", wells: 90, wells_in_county: 0 },
      { operator_number: null, wells: 130, wells_in_county: 0 },
    ];
    db.permits = [];

    const out = await run({ name: "Smith, John", county: "Andrews" });

    expect(out.ok).toBe(true);
    expect(out.county_summary).toMatchObject({ operators_active: 0, wells_on_schedule: 0 });
    // The two operators still exist and the answer says so, because "registered
    // and active elsewhere" is the finding.
    expect(out.operators_total).toBe(2);
    expect(JSON.stringify(out.notes)).toContain("Andrews County in the last 24 months");
  });

  test("without a county it reports the whole footprint and no county field", async () => {
    const out = await run({ name: "Smith, John" });

    expect(out.county_summary).toBe(null);
    const ops = out.operators as { operator_no: string; wells_in_county: number | null }[];
    expect(ops.map((o) => o.operator_no)).toEqual(["200000", "100000"]);
    // Not zero and not a repeat of the statewide count. No county was asked
    // about, so there is no county number to report.
    expect(ops.every((o) => o.wells_in_county === null)).toBe(true);
  });

  test("names the other people the string could mean", async () => {
    db.names = [
      { officer_name: "SMITH, JOHN", operator_count: 2, sim: 0.5, surname_sim: 0.833 },
      { officer_name: "SMITH, JOHN B.", operator_count: 7, sim: 0.48, surname_sim: 0.833 },
    ];
    const out = await run({ name: "John Smithe" });

    // Same-name people never merge, so a second candidate is a second person to
    // ask about. It is listed rather than folded in.
    expect(out.other_matches).toEqual([
      { officer_name: "SMITH, JOHN B.", matched: "surname and given name", score: 0.48, operator_count: 7 },
    ]);
  });

  test("distinguishes absent from the file from operating nothing", async () => {
    db.names = [];
    const out = await run({ name: "Nobody Whatsoever" });

    expect(out.ok).toBe(false);
    const error = String(out.error);
    expect(error).toContain("That is an answer, not an error");
    // The limit of the claim, stated in the refusal: the RRC publishes
    // operators, not owners.
    expect(error).toContain("working interest");
  });

  test("refuses a county that is not a Texas county", async () => {
    const out = await run({ name: "Smith, John", county: "Lea" });
    expect(out).toMatchObject({ ok: false });
    expect(String(out.error)).toContain("Lea");
    expect(db.queries).toHaveLength(0);
  });
});
