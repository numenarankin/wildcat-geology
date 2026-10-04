import { describe, expect, test } from "vitest";

import { TOOLS } from "./screen";

/**
 * The population screen, against the LIVE mirror.
 *
 * Fixtures were considered and rejected. Almost the entire tool is one SQL
 * statement: the predicates, the deduplication of a wellbore's several lease
 * rows, the three perforation states and the true match count all live in the
 * query. A mocked `rrcQuerySlow` would return whatever fixture the test author
 * wrote and assert that the tool passed it through, which tests the pass
 * through and nothing that can actually be wrong.
 *
 * So these run against the real record, and every expectation below is an
 * INVARIANT derived from what the screen means, never a number read off a run:
 *
 *   - the three perforation states must PARTITION the wells that reached the
 *     window, exactly, with nothing double counted and nothing lost;
 *   - a wider circle must return more wells than a narrower one, which is the
 *     specific defect this tool was built to remove (the anchored tools took
 *     the nearest sixty, so 15 miles and 40 miles returned the same wells);
 *   - a county cannot match more than the district that contains it, and no
 *     extent can match more than the state;
 *   - a returned page can never claim to be complete while the true match count
 *     exceeds it.
 *
 * Every one of those is computable from the definition of the screen without
 * running it, which is the whole point.
 */

const screen = TOOLS.find((t) => t.name === "rrc_well_screen");

type Ok = {
  ok: true;
  matched: number;
  returned: number;
  is_complete: boolean;
  population: {
    wells_in_extent: number;
    screenable: number;
    unscreenable: number;
    penetrated_the_window: number;
    perforated_in_window: number;
    behind_pipe: number;
    penetrated_with_no_perforation_record: number;
  };
  wells: {
    api_number: string;
    total_depth: number | null;
    operator_name: string | null;
    operator_number: string | null;
    shallowest_perf_ft: number | null;
    deepest_perf_ft: number | null;
    perf_intervals: number | null;
    perfs_below_filed_td: boolean | null;
  }[];
  by_operator: { key: string | null; wells: number }[];
  guidance: string[];
};
type Refusal = { ok: false; error: string };

async function run(args: Record<string, unknown>): Promise<Ok | Refusal> {
  return (await screen!.run(args as never)) as Ok | Refusal;
}

/**
 * The operator number behind a facet's name.
 *
 * `by_operator` is keyed by name because that is what a person reads, and the
 * screen filters on the number because that is the identity. Pulled off a
 * returned row rather than resolved separately, so the two cannot disagree.
 */
function operatorNoFor(r: Ok, name: string): string {
  const hit = r.wells.find((w) => w.operator_name === name);
  if (!hit?.operator_number) throw new Error(`no operator number on a row for ${name}`);
  return hit.operator_number;
}

function ok(r: Ok | Refusal): Ok {
  if (r.ok === false) throw new Error(`expected a result, got a refusal: ${r.error}`);
  return r;
}

/** Skips the whole file rather than failing it where the mirror is absent. */
const live = process.env.RRC_DATABASE_URL ? describe : describe.skip;

// ARCHER county sits inside district 09. The 4,050 to 4,120 ft window is the
// one from the conversation that prompted this tool.
const WINDOW = { depth_top_ft: 4050, depth_bottom_ft: 4120 };
const TIMEOUT = 120_000;
/** The tool's own ceiling on returned rows. */
const MAX = 300;

live("rrc_well_screen", () => {
  test(
    "the three perforation states partition the wells that reached the window",
    async () => {
      // The reconciliation. `penetrated` is every hole deep enough; of those,
      // each one either has a perforation in the window, or has perforations
      // elsewhere and none in it, or has no perforation depths on file at all.
      // Those three are mutually exclusive and jointly exhaustive BY
      // CONSTRUCTION, so if the SQL disagrees the predicates are wrong.
      const [penetrated, behind] = await Promise.all([
        run({ ...WINDOW, county: "Archer", perforation_state: "penetrated", limit: 1 }),
        run({ ...WINDOW, county: "Archer", perforation_state: "behind_pipe", limit: 1 }),
      ]);
      const p = ok(penetrated).population;

      expect(p.perforated_in_window + p.behind_pipe + p.penetrated_with_no_perforation_record).toBe(
        p.penetrated_the_window
      );
      expect(ok(penetrated).matched).toBe(p.penetrated_the_window);
      // And the same number reached two ways: the bucket counted inside the
      // penetrated screen has to equal what the behind-pipe screen matches on
      // its own. Two internally consistent answers that disagree is the bug.
      expect(ok(behind).matched).toBe(p.behind_pipe);
      // The partition has to be non-trivial, or the assertions above would pass
      // on a county where nothing matched anything.
      expect(p.perforated_in_window).toBeGreaterThan(0);
      expect(p.behind_pipe).toBeGreaterThan(0);
    },
    TIMEOUT
  );

  test(
    "a wider circle matches strictly more wells than a narrower one",
    async () => {
      // The defect this tool exists to remove. `AREA_SHAPE` takes the nearest N
      // from an anchor, so `radius_mi` stopped doing anything past the sixtieth
      // well: measured live, a fit at 15 miles and at 40 miles ran on the same
      // sixty wells. Here the radius is a FILTER, so growing it must grow the
      // population.
      const anchor = { lat: 33.35, lon: -98.6, ...WINDOW, limit: 1 };
      const [near, far] = await Promise.all([
        run({ ...anchor, radius_mi: 15 }),
        run({ ...anchor, radius_mi: 40 }),
      ]);
      expect(ok(far).matched).toBeGreaterThan(ok(near).matched);
      expect(ok(near).matched).toBeGreaterThan(0);
    },
    TIMEOUT
  );

  test(
    "an extent never matches more than the extent that contains it",
    async () => {
      // Archer is inside district 09, and district 09 is inside Texas. A screen
      // that reported otherwise would mean the extent filter and the match
      // predicate are being applied in the wrong order, which is the exact bug
      // class this plan calls "caps applied before the filter".
      const [county, district, state] = await Promise.all([
        run({ ...WINDOW, county: "Archer", limit: 1 }),
        run({ ...WINDOW, district: "09", limit: 1 }),
        run({ ...WINDOW, limit: 1 }),
      ]);
      expect(ok(county).matched).toBeLessThanOrEqual(ok(district).matched);
      expect(ok(district).matched).toBeLessThanOrEqual(ok(state).matched);
      expect(ok(state).matched).toBeGreaterThan(0);
    },
    TIMEOUT
  );

  test(
    "a page smaller than the match count is never reported as complete",
    async () => {
      // The failure mode is a caption, not a calculation: the previous
      // generation carried a `truncated` boolean that was skimmed past twice in
      // one conversation. So the flag has to be right AND the note has to say
      // the word.
      const r = ok(await run({ ...WINDOW, district: "09", limit: 5 }));
      expect(r.matched).toBeGreaterThan(5);
      expect(r.returned).toBe(5);
      expect(r.is_complete).toBe(false);
      expect(r.guidance.join(" ")).toContain("sample:");
      // The breakdowns are computed over every match, not over the page, which
      // is what makes them safe to quote when the list is not.
      const facetTotal = r.by_operator.reduce((sum, f) => sum + f.wells, 0);
      expect(facetTotal).toBeGreaterThan(r.returned);
      expect(facetTotal).toBeLessThanOrEqual(r.matched);
    },
    TIMEOUT
  );

  test(
    "every returned well actually meets the screen it was returned for",
    async () => {
      // Reading the rows back against the definition, rather than trusting that
      // the WHERE clause said what it meant. A behind-pipe candidate reached the
      // bottom of the window by the deepest evidence the record carries, which
      // is total depth OR a perforation below that point, and it carries
      // perforations somewhere. Asserting on total depth alone would be
      // asserting something stricter than the screen claims.
      const r = ok(await run({ ...WINDOW, county: "Archer", limit: 25 }));
      expect(r.wells.length).toBeGreaterThan(0);
      for (const w of r.wells) {
        const reached = Math.max(w.total_depth ?? 0, w.deepest_perf_ft ?? 0);
        expect(reached).toBeGreaterThanOrEqual(WINDOW.depth_bottom_ft);
        expect(w.shallowest_perf_ft).not.toBeNull();
        // No perforation may fall inside the window: that is the whole claim.
        expect(w.perf_intervals).toBe(0);
      }
      // One hole, one row. A wellbore carries a row per lease and field it has
      // ever been assigned to, and without the dedup a single API comes back
      // several times and is counted several times.
      const apis = r.wells.map((w) => w.api_number);
      expect(new Set(apis).size).toBe(apis.length);
    },
    TIMEOUT
  );


  test(
    "a complete page says so, and a sample names the narrowing that would fit",
    async () => {
      // The failure this closes was a NON-ANSWER. Told only that a capped list
      // is never a population, the model stopped naming wells at all and
      // replied to "which wells could I buy" with county totals, twice. So the
      // result has to carry the other half: when the page holds every match,
      // say the list is the answer; when it does not, say which narrowing would
      // come back complete rather than "narrow it" in the abstract.
      const sample = ok(await run({ ...WINDOW, district: "09", limit: 5 }));
      expect(sample.is_complete).toBe(false);
      const note = sample.guidance.join(" ");
      expect(note).toContain("sample:");
      // Actionable, not abstract: it must name a narrowing and tell the model
      // to call again rather than to stop at the count.
      expect(note).toMatch(/call again/i);
      expect(note).toMatch(/county|field_name|operator_no/);

      // Now WALK the loop the note is telling the model to walk, on the
      // narrowing the result itself named. This is the assertion that matters:
      // the advice has to actually terminate in a complete list, or it is the
      // same non-answer with more steps.
      // County first, then the largest operator inside it. District 09's top
      // twelve holders each carry more than a page on their own, which is the
      // real shape of this data and the reason the note names the narrowing
      // that fits rather than telling the model to narrow once and hope.
      const wide = ok(await run({ ...WINDOW, county: "Archer", limit: MAX }));
      const fits = wide.by_operator.find((f) => f.key && f.wells > 0 && f.wells <= MAX);
      expect(fits).toBeDefined();
      const narrowed = ok(
        await run({ ...WINDOW, county: "Archer", operator_no: operatorNoFor(wide, fits!.key!), limit: MAX })
      );
      expect(narrowed.is_complete).toBe(true);
      expect(narrowed.wells.length).toBe(narrowed.matched);
      expect(narrowed.matched).toBeGreaterThan(0);
      expect(narrowed.guidance.join(" ")).toContain("complete:");
      // And the pointer to the tool that answers an acquisition question,
      // because reaching for the plain screen and hand-assembling the rest is
      // exactly what it did.
      expect(narrowed.guidance.join(" ")).toContain("rrc_analog_screen");
    },
    TIMEOUT
  );


  test(
    "a perforation below the filed total depth is flagged, not silently ranked",
    async () => {
      // The live failure: a Barnett horizontal came back in a list of vertical
      // Marble Falls candidates showing TD 4,682 and a shallowest perforation of
      // 4,920. Measured depth on a lateral is not comparable with a vertical's,
      // and nothing on the row said so. The screen still ADMITS these, because a
      // filed perforation is proof the hole reached that depth, but it has to
      // say which wells it is admitting on that basis.
      const r = ok(await run({ ...WINDOW, district: "09", limit: MAX }));
      for (const w of r.wells) {
        const impossible =
          w.total_depth != null && w.deepest_perf_ft != null && w.deepest_perf_ft > w.total_depth;
        expect(w.perfs_below_filed_td).toBe(impossible);
      }
      // And the guidance tells the model what to do with the flag rather than
      // leaving it as an unexplained boolean.
      expect(r.guidance.join(" ")).toContain("perfs_below_filed_td");
    },
    TIMEOUT
  );

  test("the guidance carries no sentence worth reciting", async () => {
    // Two answers in a row opened with a paragraph of meta lifted straight from
    // this block: what kind of screen it was, which arguments were chosen, what
    // it could not do. Prose invites relaying, so the block is fragments and
    // imperatives. The first line says what it is; nothing else reads as copy.
    const r = ok(await run({ ...WINDOW, county: "Archer", limit: 5 }));
    expect(r.guidance[0]).toContain("INTERNAL");
    for (const line of r.guidance.slice(1)) {
      // Nothing long enough to be a paragraph, and nothing addressed to a
      // reader rather than to the model. The bound is generous because one
      // entry carries a generated list of narrowings; what it rules out is a
      // paragraph of explanation, which is what was being recited.
      expect(line.length).toBeLessThan(400);
      expect(line).not.toMatch(/\bthe user\b/i);
    }
  });


  test(
    "takes a well as the centre of a circle, the way the question is asked",
    async () => {
      // Measured live: the model passed api with radius_mi twice, was refused
      // both times for missing lat/lon, and spent two of the turn's steps
      // looking up coordinates it should never have had to hold. Nobody asks
      // for wells within ten miles of 32.914, -98.676.
      const REPASS_2 = "42933846";
      const byApi = ok(await run({ ...WINDOW, api: REPASS_2, radius_mi: 10, limit: 3 }));
      const byPoint = ok(
        await run({ ...WINDOW, lat: 32.91431483, lon: -98.67620194, radius_mi: 10, limit: 3 })
      );
      // Same circle, so the same population. If the anchor resolved to a
      // different well the counts would drift and nothing would say so.
      expect(byApi.matched).toBe(byPoint.matched);
      expect(byApi.matched).toBeGreaterThan(0);

      // A well with no location on file refuses and says what to do instead,
      // rather than silently screening the whole state.
      const nowhere = await run({ ...WINDOW, api: "00000000", radius_mi: 10 });
      expect(nowhere.ok).toBe(false);
      expect((nowhere as Refusal).error).toMatch(/county, district or bbox/);
    },
    TIMEOUT
  );

  test("accepts the depth window under the names the model actually writes", async () => {
    // `depth_from_ft` / `depth_to_ft` cost a live turn two refusals: the
    // from/to vocabulary is right everywhere else in this catalog, so a wrong
    // guess here came from a right habit. Normalised rather than refused.
    const { runRrcAnalysis } = await import("../dispatch");
    void runRrcAnalysis;
    const { normalizeToolArgs, declaredArgs } = await import("../../tool-args");
    const declared = declaredArgs(screen!.args);
    const fixed = normalizeToolArgs(
      { county: "Archer", depth_from_ft: 4050, depth_to_ft: 4120 },
      declared
    );
    expect(fixed.depth_top_ft).toBe(4050);
    expect(fixed.depth_bottom_ft).toBe(4120);
    expect(fixed.depth_from_ft).toBeUndefined();
  });

  test("refuses what it cannot honestly screen", async () => {
    const county = await run({ ...WINDOW, county: "Nowhere" });
    expect(county.ok).toBe(false);
    expect((county as Refusal).error).toContain("Texas county");

    const window = await run({ depth_top_ft: 4120, depth_bottom_ft: 4120, county: "Archer" });
    expect(window.ok).toBe(false);

    const halfCircle = await run({ ...WINDOW, lat: 33.35 });
    expect(halfCircle.ok).toBe(false);
    expect((halfCircle as Refusal).error).toContain("lon");

    const district = await run({ ...WINDOW, district: "99" });
    expect(district.ok).toBe(false);
    expect((district as Refusal).error).toContain("district");
  });
});

/**
 * The analog engine.
 *
 * The one thing it must never do is quote a base rate and a candidate list that
 * were counted over different populations, because both numbers would look
 * right and the ratio between them, which is the entire product, would be
 * wrong. So the assertions here are reconciliations against `rrc_well_screen`
 * run on the same extent: the denominator has to be that screen's
 * `perforated_in_window`, and the candidate count has to be its `behind_pipe`.
 */
type Analog = {
  ok: true;
  available: number;
  returned: number;
  is_complete: boolean;
  base_rate: {
    wells: number;
    dated: number;
    still_on_schedule: number;
    plugged_after_shooting_it: number;
    plugged_within_5_years: number;
    median_years_from_shooting_it_to_plugging: number | null;
    failure_rate: string | null;
  };
  candidates: { api_number: string }[];
  guidance: string[];
};

const analog = TOOLS.find((t) => t.name === "rrc_analog_screen");

live("rrc_analog_screen", () => {
  test(
    "counts its base rate and its candidates over the same population as the screen",
    async () => {
      const [a, s] = await Promise.all([
        analog!.run({ ...WINDOW, county: "Archer", limit: 5 } as never) as Promise<Analog>,
        run({ ...WINDOW, county: "Archer", perforation_state: "penetrated", limit: 1 }),
      ]);
      const p = ok(s).population;
      // `tried` is every well with a perforation in the window, which is the
      // screen's perforated bucket plus any well shot in the window that never
      // reached its base. The screen's bucket is the subset that penetrated, so
      // the analog denominator can only be equal or larger, never smaller.
      expect(a.base_rate.wells).toBeGreaterThanOrEqual(p.perforated_in_window);
      expect(a.available).toBe(p.behind_pipe);
    },
    TIMEOUT
  );

  test(
    "the outcome is conditional on the attempt, not on the well",
    async () => {
      const a = (await analog!.run({ ...WINDOW, county: "Archer", limit: 5 } as never)) as Analog;
      // A well plugged BEFORE anybody shot this window is not evidence against
      // the window. So the failures can never exceed the attempts that carry a
      // date, and the fast failures are a subset of the failures.
      expect(a.base_rate.dated).toBeLessThanOrEqual(a.base_rate.wells);
      expect(a.base_rate.plugged_after_shooting_it).toBeLessThanOrEqual(a.base_rate.dated);
      expect(a.base_rate.plugged_within_5_years).toBeLessThanOrEqual(
        a.base_rate.plugged_after_shooting_it
      );
      // The base rate leads the guidance, so a reader reaches it before the list.
      expect(a.guidance.join(" ")).toMatch(/base rate:/);
    },
    TIMEOUT
  );

  test(
    "says so plainly when nobody has ever tried the zone",
    async () => {
      // A window nobody in Archer County has perforated, because nobody has
      // drilled to it: the county's deepest holes are Pennsylvanian at a few
      // thousand feet. A tool that reported a 0% failure rate here would be
      // reporting "it has never failed" for a move nobody has ever made, which
      // is the most dangerous sentence this system could produce.
      //
      // Deep rather than shallow on purpose. The obvious empty window is a few
      // feet below surface, and it is not empty: 102 perforation records
      // statewide overlap 30 to 60 ft, which are junk rows, not completions.
      const a = (await analog!.run({
        depth_top_ft: 30_000,
        depth_bottom_ft: 31_000,
        county: "Archer",
        limit: 3,
      } as never)) as Analog;
      expect(a.base_rate.wells).toBe(0);
      expect(a.base_rate.failure_rate).toBeNull();
      expect(a.guidance.join(" ")).toContain("NO PRECEDENT");
    },
    TIMEOUT
  );
});

/**
 * Asking for the rock by name.
 *
 * The screen takes depths because depth is what almost every well carries, and
 * the cost of that decision was that somebody had to supply the numbers. The
 * geology side's alias table supplies them now, and the risk it introduces is
 * the one worth testing: a name that quietly resolves to the WRONG unit returns
 * wells that look exactly like the right answer. So these assert the refusals
 * as hard as the resolution.
 */
live("screening by formation name", () => {
  test(
    "resolves a rock and a county to the window the filings actually show",
    async () => {
      // Oracle from the table, not from the tool: the Caddo Limestone in Jack
      // County is filed p10 4275 ft, p50 4723, p90 5184 over 225 completion
      // reports. The screen must use that band and say where it came from.
      const r = ok(await run({ formation: "Caddo", county: "Jack", limit: 3 }));
      const from = (r as unknown as { screen: { formation?: { canonical: string; county: string; depth_samples: number }; depth_window_ft: number[] } }).screen;
      expect(from.formation?.canonical).toBe("caddo limestone");
      expect(from.formation?.county).toBe("JACK");
      expect(from.depth_window_ft[0]).toBe(4275);
      expect(from.depth_window_ft[1]).toBe(5184);
      expect(from.formation?.depth_samples).toBe(225);
      expect(r.matched).toBeGreaterThan(0);
    },
    TIMEOUT
  );

  test("refuses rather than guessing at the edges", async () => {
    // A county the table does not cover. Extrapolating a north-central Texas
    // window into the Permian Basin would be a confident wrong screen.
    const far = await run({ formation: "Caddo", county: "Midland" });
    expect(far.ok).toBe(false);
    expect((far as Refusal).error).toMatch(/counties|covered/i);

    // A rock nobody filed. No nearest match, ever.
    const unknown = await run({ formation: "Wolfcamp", county: "Jack" });
    expect(unknown.ok).toBe(false);

    // A formation with no county is not a depth.
    const noCounty = await run({ formation: "Caddo" });
    expect(noCounty.ok).toBe(false);
    expect((noCounty as Refusal).error).toContain("county");

    // Neither depths nor a rock.
    const nothing = await run({ county: "Jack" });
    expect(nothing.ok).toBe(false);
  });

  test(
    "explicit depths win over a name, because a caller who typed numbers meant them",
    async () => {
      const r = ok(
        await run({ ...WINDOW, formation: "Caddo", county: "Archer", limit: 1 })
      );
      const screen = (r as unknown as { screen: { depth_window_ft: number[] } }).screen;
      expect(screen.depth_window_ft).toEqual([WINDOW.depth_top_ft, WINDOW.depth_bottom_ft]);
    },
    TIMEOUT
  );
});

/**
 * Who holds the candidates, which is the half of "where else can I do this"
 * that a well count does not answer.
 *
 * The live failure this closes: asked what wells could be BOUGHT, the answer
 * came back with an inventory total and led the candidate list with wells the
 * asker already operates. So these assert that the exclusion actually removes a
 * population and that the owner block reconciles against the candidates it is
 * computed from.
 */
type Owner = {
  operator_number: string | null;
  operator_name: string | null;
  candidates: number;
  wells_in_extent: number;
  wells_on_the_14b2_clock: number;
  p5_org_status: string | null;
};

live("who holds the candidates", () => {
  test(
    "the owner block reconciles against the candidate count",
    async () => {
      const a = (await analog!.run({
        ...WINDOW,
        county: "Archer",
        limit: 5,
      } as never)) as Analog & { owners: Owner[] };
      expect(a.owners.length).toBeGreaterThan(0);
      // The block is capped at the facet limit, so it can only ever account for
      // part of the population. What it must never do is claim more.
      const listed = a.owners.reduce((n, o) => n + o.candidates, 0);
      expect(listed).toBeLessThanOrEqual(a.available);
      for (const o of a.owners) {
        // An operator cannot hold more candidates than they hold wells here.
        expect(o.candidates).toBeLessThanOrEqual(o.wells_in_extent);
        expect(o.wells_on_the_14b2_clock).toBeLessThanOrEqual(o.wells_in_extent);
      }
      // Ordered by candidates, so the biggest holder is the first thing read.
      expect(a.owners[0].candidates).toBeGreaterThanOrEqual(
        a.owners[a.owners.length - 1].candidates
      );
    },
    TIMEOUT
  );


  test(
    "the same screen returns the same owners every time",
    async () => {
      // Regression. The dedup that picks one row per wellbore ordered only on
      // on_schedule, which is not a total order: a hole with several rows
      // carrying the same flag was represented by whichever row the planner
      // happened to return, so the operator attached to it changed between
      // identical calls. Three consecutive runs gave the top operator 139, 135
      // and 138 candidates. The match COUNT was stable throughout, which is why
      // it stayed hidden until a question was asked about ownership.
      const args = { ...WINDOW, county: "Archer", limit: 1 };
      const runs = await Promise.all([
        analog!.run(args as never) as Promise<Analog & { owners: Owner[] }>,
        analog!.run(args as never) as Promise<Analog & { owners: Owner[] }>,
        analog!.run(args as never) as Promise<Analog & { owners: Owner[] }>,
      ]);
      const shape = (r: Analog & { owners: Owner[] }) =>
        JSON.stringify(r.owners.map((o) => [o.operator_number, o.candidates]));
      expect(shape(runs[1])).toBe(shape(runs[0]));
      expect(shape(runs[2])).toBe(shape(runs[0]));
    },
    TIMEOUT
  );

  test(
    "excluding an operator removes their wells from the whole population",
    async () => {
      const base = (await analog!.run({
        ...WINDOW,
        county: "Archer",
        limit: 1,
      } as never)) as Analog & { owners: Owner[] };
      const biggest = base.owners[0];
      expect(biggest.operator_number).toBeTruthy();

      const without = (await analog!.run({
        ...WINDOW,
        county: "Archer",
        exclude_operator_no: biggest.operator_number!,
        limit: 1,
      } as never)) as Analog & { owners: Owner[] };

      // Gone from the candidates, and gone from the OWNER block too: an
      // exclusion that only hid the rows would leave the counts unchanged and
      // the reader would still be looking at their own inventory.
      expect(without.available).toBe(base.available - biggest.candidates);
      expect(without.owners.map((o) => o.operator_number)).not.toContain(
        biggest.operator_number
      );
      // And out of the base rate as well, since it is the same population.
      expect(without.base_rate.wells).toBeLessThanOrEqual(base.base_rate.wells);
    },
    TIMEOUT
  );
});
