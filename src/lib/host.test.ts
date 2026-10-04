import { afterEach, describe, expect, test } from "vitest";
import path from "node:path";
import { geologyHost, setGeologyHost } from "./host";
import { devHost } from "./host-dev";

const FIXTURES = path.resolve(__dirname, "../../tests/geology/fixtures");
const KEY = Symbol.for("geology.host");

afterEach(() => {
  delete (globalThis as { [KEY]?: unknown })[KEY];
});

describe("unwired host", () => {
  // A forgotten setGeologyHost must not serve the RRC mirror to anyone.
  test("refuses the auth gate", async () => {
    await expect(geologyHost().auth.assertSignedIn()).rejects.toThrow(/no host configured/);
  });

  test("has no files and no linked wells", async () => {
    expect(await geologyHost().files.listLas()).toEqual([]);
    expect(await geologyHost().wells.rrcApi("any")).toBeNull();
  });
});

describe("dev host", () => {
  test("lists the fixture logs and reads one", async () => {
    setGeologyHost(devHost(FIXTURES));
    const files = await geologyHost().files.listLas();
    expect(files.map((f) => f.name)).toEqual([
      "repass-2-stephens-tx-1983.las",
      "sky-heighten-1-stephens-tx-2013.las",
    ]);
    const las = await geologyHost().files.loadText("sky-heighten-1-stephens-tx-2013.las");
    expect(las?.text).toMatch(/SKY HEIGHTEN # 1/);
  });

  test("will not read outside its directory", async () => {
    setGeologyHost(devHost(FIXTURES));
    expect(await geologyHost().files.loadText("../fixtures/model.ts")).toBeNull();
  });
});
