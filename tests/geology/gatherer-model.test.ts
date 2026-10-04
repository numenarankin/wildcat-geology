/**
 * The live gatherer's parsing — the half that is not judgment.
 *
 * Run: node --conditions=react-server --import tsx --test tests/geology/gatherer-model.test.ts
 *
 * These pin the line-format handling. The bug that motivated them: a greedy
 * bullet-stripper ate the leading digits of every section-numbered ID, turning
 * "01-curve-reading/gr-basics#1" into "curve-reading/gr-basics#1", which the
 * verifier then dropped as a citation to a document that does not exist. Silent,
 * and it emptied every retrieval against a corpus whose sections are numbered.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { __test } from "@/lib/ai/geology/gatherer-model";

describe("list parsing", () => {
  test("a numbered section prefix survives", () => {
    assert.equal(__test.stripBullet("01-curve-reading/gr-basics#1"), "01-curve-reading/gr-basics#1");
    assert.equal(__test.stripBullet("`04-coning/coning-basics#0`"), "04-coning/coning-basics#0");
  });

  test("real list markers are still removed", () => {
    assert.equal(__test.stripBullet("- 01-curve-reading/gr-basics#1"), "01-curve-reading/gr-basics#1");
    assert.equal(__test.stripBullet("* gr-basics"), "gr-basics");
    assert.equal(__test.stripBullet("1. gr-basics"), "gr-basics");
    assert.equal(__test.stripBullet("2) 04-coning/coning-basics#0"), "04-coning/coning-basics#0");
  });

  test("empty and refusal lines are dropped", () => {
    assert.deepEqual(__test.lines("a\n\n  \nb"), ["a", "b"]);
    assert.deepEqual(__test.lines("none"), []);
    assert.deepEqual(__test.lines("N/A"), []);
  });

  test("tool arguments parse as key=value, numbers stay numbers", () => {
    assert.deepEqual(__test.parseArgs(["lat=32.5", "lon=-102.05", 'name="Smith 3"']), {
      lat: 32.5, lon: -102.05, name: "Smith 3",
    });
    assert.deepEqual(__test.parseArgs(["garbage", "=x", "k="]), {});
  });
});

/**
 * How a requested lookup is read off the reply.
 *
 * The gatherer made zero tool calls for weeks and looked like it had decided
 * the public record was not worth pulling. It had not: it was asking for
 * `rrc_well(api=42-429-33846)` every turn, and the parser — which expected
 * `name key=value` — dropped every parenthesised line silently. The catalog
 * above the instruction lists signatures WITH parentheses, so mirroring them is
 * the natural thing for a model to do.
 */
describe("reading a requested lookup", () => {
  const known = new Set(["rrc_well", "rrc_wells_near", "rrc_county", "rrc_completion"]);

  test("takes the parenthesised form the model actually writes", () => {
    assert.deepEqual(__test.parseRequest("rrc_well(api=42-429-33846)", known), {
      name: "rrc_well",
      args: { api: "42-429-33846" },
    });
  });

  test("takes several arguments inside the parentheses", () => {
    assert.deepEqual(__test.parseRequest("rrc_county(county=STEPHENS, district_no=7)", known), {
      name: "rrc_county",
      args: { county: "STEPHENS", district_no: 7 },
    });
  });

  test("takes the bare form the instruction asks for", () => {
    assert.deepEqual(__test.parseRequest("rrc_well api=42-429-33846", known), {
      name: "rrc_well",
      args: { api: "42-429-33846" },
    });
  });

  test("a no-argument call is a call, not a discard", () => {
    assert.deepEqual(__test.parseRequest("rrc_wells_near()", known), {
      name: "rrc_wells_near",
      args: {},
    });
  });

  test("a tool that is not on offer is dropped, in either form", () => {
    assert.equal(__test.parseRequest("delete_everything(now=true)", known), null);
    assert.equal(__test.parseRequest("some prose about the well", known), null);
  });
});
