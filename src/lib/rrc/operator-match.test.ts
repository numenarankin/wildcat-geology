import { describe, expect, test } from "vitest";
import {
  basicNormalize,
  matchOperators,
  normalizeCompany,
  normalizePhone,
  parsePersonName,
  sameGivenName,
  samePerson,
  scoreOperator,
  type OperatorCandidate,
  type SignupIdentity,
} from "./operator-match";

/**
 * The oracle here is the intent, not the implementation: two people are the same
 * person when an operator would say so out loud. Every case below is written as
 * a claim about the world ("Jim Rankin IS James Rankin"), and the negative cases
 * matter more than the positive ones, because the cost of a false match is an
 * account filled with another company's wells.
 */

const OPERATOR = (over: Partial<OperatorCandidate> = {}): OperatorCandidate => ({
  operatorNumber: "123456",
  operatorName: "SKY RESOURCES OPERATING, LLC",
  phones: ["(940) 555-0142"],
  zips: ["76450"],
  city: "GRAHAM",
  state: "TX",
  officerNames: ["RANKIN, JAMES E"],
  wellCount: 48,
  ...over,
});

const IDENTITY = (over: Partial<SignupIdentity> = {}): SignupIdentity => ({
  companyName: "Sky Resources",
  personName: "Jim Rankin",
  phone: "940-555-0142",
  zip: "76450",
  city: "Graham",
  state: "TX",
  ...over,
});

describe("company names", () => {
  test("the entity suffix and the industry filler are noise", () => {
    // The case this whole module exists for: the operator types "Sky", the state
    // holds "SKY RESOURCES OPERATING, LLC", and they are the same company.
    expect(normalizeCompany("SKY RESOURCES OPERATING, LLC")).toBe("sky");
    expect(normalizeCompany("Sky Resources")).toBe("sky");
    expect(normalizeCompany("Sky Oil & Gas Inc.")).toBe("sky");
  });

  test("a name that is entirely filler keeps its words rather than emptying", () => {
    // `OIL & GAS PRODUCTION CO` is every filler word we strip. Reduced to "" it
    // would match every other all-filler operator in Texas, so the filler pass
    // is abandoned and the suffix-stripped form stands.
    expect(normalizeCompany("Oil & Gas Production Co")).toBe("oil gas production");
    expect(normalizeCompany("Oil & Gas Production Co")).not.toBe("");
  });

  test("a distinctive word survives its filler neighbours", () => {
    // "transfer" is what discriminates `Energy Transfer` from every other
    // operator with "energy" in the name, so it is the key, and the user typing
    // the full name reaches the same one.
    expect(normalizeCompany("Energy Transfer Partners LP")).toBe("transfer");
    expect(normalizeCompany("Energy Transfer")).toBe("transfer");
  });

  test("ampersands and punctuation do not change the key", () => {
    expect(normalizeCompany("Smith & Sons Oil Co.")).toBe(
      normalizeCompany("Smith and Sons Oil Company")
    );
  });

  test("containment is word-wise, so Sky does not match Skyline", () => {
    const sky = scoreOperator(
      { companyName: "Sky" },
      OPERATOR({ operatorName: "SKYLINE RESOURCES LLC", phones: [], zips: [], officerNames: [] })
    );
    expect(sky.signals).not.toContain("company_exact");
    expect(sky.signals).not.toContain("company_partial");
  });
});

describe("given names", () => {
  test("a diminutive is the same name in both directions", () => {
    expect(sameGivenName("Jim", "James")).toBe(true);
    expect(sameGivenName("James", "Jim")).toBe(true);
    expect(sameGivenName("Bob", "Robert")).toBe(true);
    expect(sameGivenName("Jack", "John")).toBe(true);
    expect(sameGivenName("Bill", "William")).toBe(true);
    expect(sameGivenName("Peggy", "Margaret")).toBe(true);
  });

  test("two diminutives of one formal name are the same name", () => {
    expect(sameGivenName("Jim", "Jimmy")).toBe(true);
    expect(sameGivenName("Bob", "Bobby")).toBe(true);
  });

  test("sharing a diminutive does NOT make two formal names equal", () => {
    // John and Jackson can both be called Jack. They are not the same name, and
    // the transitive closure of this relation says they are — which is why the
    // generated data is directed. Robert/William is the same failure two hops on.
    expect(sameGivenName("John", "Jackson")).toBe(false);
    expect(sameGivenName("Robert", "William")).toBe(false);
    expect(sameGivenName("Bob", "Bill")).toBe(false);
    expect(sameGivenName("John", "Robert")).toBe(false);
  });

  test("unrelated names do not match", () => {
    expect(sameGivenName("James", "Michael")).toBe(false);
    expect(sameGivenName("Sarah", "Susan")).toBe(false);
  });
});

describe("people", () => {
  test("the RRC's surname-first shouting parses", () => {
    expect(parsePersonName("RANKIN, JAMES E")).toEqual({ first: "james", last: "rankin" });
  });

  test("a name with no comma reads first-last", () => {
    expect(parsePersonName("Jim Rankin")).toEqual({ first: "jim", last: "rankin" });
  });

  test("a middle name is dropped rather than confusing the surname", () => {
    expect(parsePersonName("James Earl Rankin")).toEqual({ first: "james", last: "rankin" });
  });

  test("Jim Rankin is RANKIN, JAMES E", () => {
    expect(
      samePerson(parsePersonName("Jim Rankin")!, parsePersonName("RANKIN, JAMES E")!)
    ).toBe(true);
  });

  test("a bare initial matches, a different full name does not", () => {
    expect(samePerson(parsePersonName("J Rankin")!, parsePersonName("Jim Rankin")!)).toBe(true);
    expect(
      samePerson(parsePersonName("John Rankin")!, parsePersonName("RANKIN, JAMES E")!)
    ).toBe(false);
  });

  test("a shared surname alone is not a person match when both first names are known", () => {
    expect(
      samePerson(parsePersonName("Michael Rankin")!, parsePersonName("RANKIN, JAMES E")!)
    ).toBe(false);
  });
});

describe("scoring one candidate", () => {
  test("phone and officer together read as confident, and the reason says why", () => {
    const s = scoreOperator(IDENTITY(), OPERATOR());
    expect(s.signals).toContain("phone");
    expect(s.signals).toContain("officer");
    expect(s.confidence).toBe("confident");
    expect(s.reason).toContain("Same phone number");
    expect(s.reason).toContain("Jim Rankin");
  });

  test("the phone alone is enough to be confident", () => {
    // Nothing else agrees: different company, no officer given, no ZIP, and a
    // city the identity does not claim. The phone carries it on its own.
    const s = scoreOperator(
      {
        companyName: "Something Else Entirely",
        phone: "940-555-0142",
      },
      OPERATOR({ officerNames: [] })
    );
    expect(s.signals).toEqual(["phone"]);
    expect(s.confidence).toBe("confident");
  });

  test("a company name alone is NOT confident", () => {
    // Normalization is aggressive on purpose, so `sky` is a plausible key for
    // more than one Texas operator. Promoting this to "Is this you?" would put
    // somebody else's fleet behind a single click.
    const s = scoreOperator(
      { companyName: "Sky Resources" },
      OPERATOR({ phones: [], zips: [], officerNames: [], city: null, state: null })
    );
    expect(s.signals).toEqual(["company_exact"]);
    expect(s.confidence).toBe("possible");
  });

  test("company name plus ZIP is confident", () => {
    const s = scoreOperator(
      { companyName: "Sky Resources", zip: "76450" },
      OPERATOR({ phones: [], officerNames: [] })
    );
    expect(s.confidence).toBe("confident");
  });

  test("an alias catches what normalization cannot", () => {
    const s = scoreOperator(
      { companyName: "Rankin Family Partnership", aliases: ["Sky"] },
      OPERATOR({ phones: [], officerNames: [], zips: [] })
    );
    expect(s.signals).toContain("company_exact");
  });

  test("a phone with a country code still matches", () => {
    expect(normalizePhone("+1 (940) 555-0142")).toBe(normalizePhone("940-555-0142"));
  });

  test("the mirror's all-zero placeholders are not values", () => {
    // 7,926 operators in the mirror carry `0000000000` for a missing phone or
    // `000000000` for a missing ZIP (counted against rrc.operators). Read as
    // data, every one of them shares a phone number with every other.
    expect(normalizePhone("0000000000")).toBe("");
    const s = scoreOperator(
      { companyName: "Nothing Alike", phone: "0000000000", zip: "00000" },
      OPERATOR({
        operatorName: "SOME OTHER OPERATOR",
        phones: ["0000000000"],
        zips: ["000000000"],
        officerNames: [],
        city: null,
        state: null,
      })
    );
    expect(s.signals).toEqual([]);
    expect(s.confidence).toBe("weak");
  });

  test("a ZIP+4 matches its five-digit form", () => {
    const s = scoreOperator(
      { companyName: "Sky", zip: "76450-1234" },
      OPERATOR({ phones: [], officerNames: [] })
    );
    expect(s.signals).toContain("zip");
  });
});

describe("ranking a field of candidates", () => {
  test("the strongest match leads and the rest are alternates", () => {
    const right = OPERATOR();
    const namesake = OPERATOR({
      operatorNumber: "999999",
      operatorName: "SKY OPERATING CO",
      phones: ["(432) 555-0000"],
      zips: ["79701"],
      city: "MIDLAND",
      officerNames: ["SMITH, DAVID"],
      wellCount: 12,
    });

    const { best, alternates } = matchOperators(IDENTITY(), [namesake, right]);

    expect(best?.candidate.operatorNumber).toBe("123456");
    expect(best?.confidence).toBe("confident");
    // The namesake is still offered: the point of the alternates list is that a
    // confident match can still be wrong, and only the user can tell.
    expect(alternates.map((a) => a.candidate.operatorNumber)).toEqual(["999999"]);
  });

  test("a city-only coincidence is dropped, not listed", () => {
    const { best, alternates } = matchOperators(
      { companyName: "Rankin Petroleum", city: "Graham", state: "TX" },
      [OPERATOR({ phones: [], officerNames: [], zips: [] })]
    );
    expect(best).toBeNull();
    expect(alternates).toEqual([]);
  });

  test("nothing in, nothing out", () => {
    expect(matchOperators(IDENTITY(), [])).toEqual({ best: null, alternates: [] });
  });

  test("alternates are capped", () => {
    const many = Array.from({ length: 9 }, (_, i) =>
      OPERATOR({ operatorNumber: `90000${i}`, phones: [], officerNames: [], wellCount: i })
    );
    const { alternates } = matchOperators(IDENTITY(), many);
    expect(alternates.length).toBe(4);
  });
});

describe("normalization basics", () => {
  test("accents and case do not change a key", () => {
    expect(basicNormalize("Peña Oil")).toBe("pena oil");
    expect(basicNormalize("  MULTIPLE   SPACES ")).toBe("multiple spaces");
  });
});
