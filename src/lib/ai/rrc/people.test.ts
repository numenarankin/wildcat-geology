import { beforeEach, describe, expect, test, vi } from "vitest";

/**
 * Finding a person by name, against the three ways a human types one wrong.
 *
 * This exists because of a real miss. A user asked what a named person was
 * doing in a county, supplying a middle name and a misspelled surname. The agent
 * searched operators, found nothing, and said so. Every layer of that was
 * broken, and the two that live here are:
 *
 *   1. The mirror stores `SMITH, JOHN B.`. The old match was
 *      `officer_name ilike '%<the whole string>%'`, which matches ZERO rows for
 *      a name typed in reading order, zero for a name with a middle name, and
 *      zero for a name with one wrong letter. All three came back as "no P-5
 *      officer matched", which reads like "this person operates nothing". Those
 *      are opposite answers and nothing distinguished them.
 *   2. Trigram similarity alone does not fix it, because it scores the WHOLE
 *      string and a correctly-spelled middle name outvotes a correctly-spelled
 *      given name. That is not hypothetical: measured on the live mirror,
 *      "John Michael Smithe" ranks `SMITH, MICHAEL` at 0.619 ABOVE every
 *      `SMITH, JOHN`. Ranking by score alone returns the wrong person with
 *      confidence, which is worse than returning none.
 *
 * So the expected order below is computed from the INTENT (a matching surname
 * and given name is a better answer than a matching surname alone, whatever the
 * string score says), never from what the code currently returns. The scores in
 * the fixture are the ones the real mirror produced.
 */

const db = vi.hoisted(() => ({
  queries: [] as { sql: string; params: unknown[] }[],
  rows: [] as unknown[],
}));

vi.mock("@/lib/scout/rrc-db", () => ({
  hasRrcDb: () => true,
  rrcQuery: async (sql: string, params: unknown[]) => {
    db.queries.push({ sql, params });
    return db.rows;
  },
}));

const { resolveOfficerNames } = await import("./people");

/** What the candidate pool looks like for "John Michael Smithe". */
function smithPool() {
  return [
    // Higher whole-string score than the right answer, because "Michael" is
    // spelled correctly and is in both strings. This row is the trap.
    { officer_name: "SMITH, MICHAEL", operator_count: 4, sim: 0.619, surname_sim: 0.833 },
    { officer_name: "SMITH, JOHN", operator_count: 2, sim: 0.5, surname_sim: 0.833 },
    // A different surname that happens to share trigrams. Must not outrank
    // either Smith, whatever its given name.
    { officer_name: "SELF, JOHN MICHAEL", operator_count: 9, sim: 0.583, surname_sim: 0.0 },
  ];
}

beforeEach(() => {
  db.queries = [];
  db.rows = [];
});

describe("resolving a person's name to the file's spelling", () => {
  test("a matching given name beats a higher string score", async () => {
    db.rows = smithPool();
    const out = await resolveOfficerNames("John Michael Smithe");

    // Oracle, by hand from intent:
    //   SMITH, JOHN   surname close (0.833 >= 0.4) + given name john = john  -> best
    //   SMITH, MICHAEL surname close, given name michael != john            -> next
    //   SELF, JOHN MICHAEL surname 0.0, not close                           -> last
    // Note this is the OPPOSITE of ordering by `sim`, which would put
    // SMITH, MICHAEL first and SELF second.
    expect(out.map((m) => m.officer_name)).toEqual([
      "SMITH, JOHN",
      "SMITH, MICHAEL",
      "SELF, JOHN MICHAEL",
    ]);
    expect(out[0].matched).toBe("surname and given name");
    expect(out[1].matched).toBe("surname");
    expect(out[2].matched).toBe("fuzzy");
  });

  test("probes the file's own surname-first spelling, not just what was typed", async () => {
    db.rows = smithPool();
    await resolveOfficerNames("John Michael Smithe");

    const { params } = db.queries[0];
    // The whole point: the string as typed can never match `SMITH, JOHN`, so a
    // canonical `Smithe, John` has to be sent alongside it. The middle name is
    // dropped, because it is the part least likely to be in the record in the
    // same form.
    // Lower case because `parsePersonName` normalizes, which costs nothing:
    // trigram similarity and `ilike` are both case-insensitive, and the mirror
    // stores every officer name shouty.
    expect(params).toContain("John Michael Smithe");
    expect(params).toContain("smithe, john");
    expect(params).toContain("smithe%");
    expect(params).toContain("smithe");
  });

  test("builds no SQL from the caller's text", async () => {
    db.rows = [];
    await resolveOfficerNames("O'Brien, Seán; drop table rrc.operators --");

    const { sql, params } = db.queries[0];
    expect(sql).not.toContain("drop table");
    expect(params.some((p) => String(p).includes("drop table"))).toBe(true);
  });

  test("a surname on its own still reaches a full name", async () => {
    db.rows = [{ officer_name: "RANKIN, POAGE H.", operator_count: 3, sim: 0.31, surname_sim: 1 }];
    const out = await resolveOfficerNames("Rankin");

    // A one-word probe scores badly against a full name under whole-string
    // similarity, so admission has to come from the prefix arm.
    expect(db.queries[0].params).toContain("rankin%");
    // No given name was supplied, so `surname` is the strongest claim that can
    // honestly be made.
    expect(out[0]).toMatchObject({ officer_name: "RANKIN, POAGE H.", matched: "surname" });
  });

  test("an exact hit says so, so a caller need not hedge", async () => {
    db.rows = [{ officer_name: "SMITH, JOHN", operator_count: 2, sim: 1, surname_sim: 1 }];
    const out = await resolveOfficerNames("Smith, John");
    expect(out[0].matched).toBe("exact");
  });

  test("knows Jim is James and does not think Bob is Bill", async () => {
    db.rows = [
      { officer_name: "RANKIN, JAMES E", operator_count: 1, sim: 0.3, surname_sim: 1 },
      { officer_name: "RANKIN, WILLIAM", operator_count: 8, sim: 0.45, surname_sim: 1 },
    ];
    const out = await resolveOfficerNames("Jim Rankin");

    // James outranks William on the NICKNAME EDGE ALONE. Every other signal
    // points the other way: William scores higher on the string and is filed on
    // eight times as many operators. Only `sameGivenName` knows that a Jim is a
    // James, and that a Bob is not a Bill.
    expect(out[0].officer_name).toBe("RANKIN, JAMES E");
    expect(out[0].matched).toBe("surname and given name");
    expect(out[1].matched).toBe("surname");
  });

  test("returns nothing for a name that is not a name", async () => {
    expect(await resolveOfficerNames("x")).toEqual([]);
    expect(db.queries).toHaveLength(0);
  });
});
