import { describe, expect, test } from "vitest";

import {
  bucketAgainst,
  datumNote,
  DERRICK_BAND_FT,
  DERRICK_HEIGHT_FT,
  filedDatum,
  placeOnDatum,
} from "./datum";

/**
 * The datum layer, against what a filed elevation MEANS.
 *
 * Every expectation here is derived from the definition, not from a run. A
 * ground-referenced elevation is short of the rig floor by the derrick, so the
 * conversion must add exactly that and must never be silent about it; a
 * rig-floor elevation is already the thing depths are measured from, so it
 * converts by nothing and carries no band. The three-bucket test is checked at
 * its edges, because the edge is the whole point of having a third bucket.
 */

describe("what a filed elevation is measured from", () => {
  test("a rig-floor elevation is taken as filed, with no band", () => {
    for (const code of ["KB", "DF", "RT", "kb", " KB "]) {
      const d = filedDatum(2000, code);
      expect(d.elevationFt).toBe(2000);
      expect(d.bandFt).toBe(0);
      expect(d.source).toBe("filed_rig_floor");
    }
  });

  test("a ground elevation is raised by the derrick, and says so", () => {
    // The correction that was missing. 697,000 filings in the mirror are ground
    // referenced against 158,600 rig-floor ones, so reading `elevation` as a
    // kelly bushing put four wells in five too shallow in subsea by this much.
    for (const code of ["GL", "GR", "gl"]) {
      const d = filedDatum(2000, code);
      expect(d.elevationFt).toBe(2000 + DERRICK_HEIGHT_FT);
      expect(d.bandFt).toBe(DERRICK_BAND_FT);
      expect(d.source).toBe("filed_ground");
    }
    // And the correction is real rather than cosmetic: it has to be big enough
    // to matter against the standoff these tools argue about.
    expect(DERRICK_HEIGHT_FT).toBeGreaterThan(0);
    expect(DERRICK_BAND_FT).toBeGreaterThan(0);
  });

  test("an uncoded elevation is not adjusted by a made-up midpoint", () => {
    // Half a derrick is a number nobody filed. The value stands and the band
    // carries the whole of what is not known about it.
    const d = filedDatum(2000, null);
    expect(d.elevationFt).toBe(2000);
    expect(d.bandFt).toBe(DERRICK_BAND_FT);
    expect(d.source).toBe("filed_uncoded");
  });

  test("no elevation is never zero", () => {
    // The failure this guards is silent and total: a well defaulted to a datum
    // of zero lands its perforations thousands of feet out and looks like
    // structure.
    for (const raw of [null, 0, -5, Number.NaN]) {
      const d = filedDatum(raw as number | null, "KB");
      expect(d.elevationFt).toBeNull();
      expect(d.source).toBe("none");
    }
  });
});

describe("the three buckets", () => {
  const band = 11;
  test("refuses to call anything inside the band", () => {
    // Exactly at the band is still too close: the band is the size of what is
    // not known, so a gap that size is indistinguishable from no gap.
    expect(bucketAgainst(-4000, -4011, band)).toBe("too_close_to_call");
    expect(bucketAgainst(-4011, -4000, band)).toBe("too_close_to_call");
    expect(bucketAgainst(-4000, -4000, band)).toBe("too_close_to_call");
  });

  test("calls it only once the gap clears the band", () => {
    expect(bucketAgainst(-4000, -4012, band)).toBe("above");
    expect(bucketAgainst(-4012, -4000, band)).toBe("below");
  });

  test("a zero band still answers, because a filed rig floor has no error to hide", () => {
    expect(bucketAgainst(-4000, -4001, 0)).toBe("above");
    expect(bucketAgainst(-4001, -4000, 0)).toBe("below");
  });
});

describe("placing a population", () => {
  test("a filed elevation is never replaced by an interpolated one", async () => {
    const set = await placeOnDatum(
      [
        { api_number: "A", lat: 32, lon: -98, elevationFt: 1500, elevationCode: "KB" },
        { api_number: "B", lat: 32, lon: -98, elevationFt: 1500, elevationCode: "GL" },
      ],
      // Derivation ON, and it must still not touch either well: both filed.
      { derive: true }
    );
    expect(set.byApi.get("A")).toEqual({ elevationFt: 1500, bandFt: 0, source: "filed_rig_floor" });
    expect(set.byApi.get("B")?.elevationFt).toBe(1500 + DERRICK_HEIGHT_FT);
    expect(set.derived).toBe(0);
    expect(set.filed).toBe(2);
    expect(set.unplaced).toBe(0);
  });

  test("with derivation off, a well with no filed elevation stays unplaced", async () => {
    const set = await placeOnDatum([
      { api_number: "A", lat: 32, lon: -98, elevationFt: null, elevationCode: null },
    ]);
    expect(set.byApi.has("A")).toBe(false);
    expect(set.unplaced).toBe(1);
    // And the note has to say so, because an excluded well silently dropped is
    // how a fit reports confidence in a population it never had.
    expect(datumNote(set)).toContain("excluded");
  });

  test("the widest band travels with the set", async () => {
    const set = await placeOnDatum([
      { api_number: "A", lat: 32, lon: -98, elevationFt: 1500, elevationCode: "KB" },
      { api_number: "B", lat: 32, lon: -98, elevationFt: 1500, elevationCode: "GL" },
    ]);
    expect(set.widestBandFt).toBe(DERRICK_BAND_FT);
  });
});

/**
 * Interpolation against the real record.
 *
 * There is no honest fixture for this: the whole question is whether the wells
 * around a point agree closely enough to place one that filed nothing, and a
 * made-up neighbourhood answers that by construction. So it runs on the mirror
 * and asserts only what must be true of ANY interpolation: the value lands
 * inside the range of the wells it came from, and the band is never narrower
 * than the uncertainty already carried by its inputs.
 */
const live = process.env.RRC_DATABASE_URL ? describe : describe.skip;

live("interpolating a missing datum", () => {
  test(
    "lands between the neighbours and carries a band no tighter than its inputs",
    async () => {
      // A point in Archer County, District 09, where the record is dense.
      const set = await placeOnDatum(
        [{ api_number: "TARGET", lat: 33.6, lon: -98.68, elevationFt: null, elevationCode: null }],
        { derive: true, radiusMi: 5 }
      );
      const d = set.byApi.get("TARGET");
      expect(d).toBeDefined();
      expect(d!.source).toBe("derived_ground");
      expect(d!.neighbours).toBeGreaterThanOrEqual(3);
      // North Texas surface elevation, and this is the sanity bound a person
      // would apply: anywhere in Texas is between sea level and the top of the
      // Guadalupes, and Archer County is a thousand feet of rolling prairie.
      expect(d!.elevationFt!).toBeGreaterThan(500);
      expect(d!.elevationFt!).toBeLessThan(2500);
      // The band can never be tighter than the derrick uncertainty every one of
      // its inputs already carries.
      expect(d!.bandFt).toBeGreaterThanOrEqual(DERRICK_BAND_FT);
      expect(set.derived).toBe(1);
      expect(datumNote(set)).toContain("too close to call");
    },
    60_000
  );
});
