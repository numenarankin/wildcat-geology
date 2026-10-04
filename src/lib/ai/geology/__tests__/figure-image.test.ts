/**
 * The one tool result that is not JSON.
 *
 * `figure_fetch` answers with a map, and a map only helps if the pixels reach
 * the model. Everything between the Python tool and the model turn is TypeScript
 * — the path finder, the corpus read, the per-run budget — and none of it is
 * exercised by the Python tests. This is that half.
 *
 * The assertions worth having are the ones that fail loudly rather than quietly:
 * a result that carries an image must not serialise to JSON-only, and a result
 * that does not must not be turned into an image call.
 */
import { describe, expect, it } from "vitest";
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import {
  claimImageBudget,
  findFigureImage,
  imagesUsed,
  MAX_IMAGES_PER_RUN,
  readFigureImage,
} from "../figure-image";

const CORPUS = path.join(process.cwd(), "geology-corpus");

/**
 * The rendered pages are not committed — 161 MB in the repo got swept into two
 * different function bundles and blew the 250 MB ceiling on both, so they live in
 * the `geology-figures` bucket and `scripts/build_figures.py` puts them on disk
 * locally. A fresh clone has the index and no pixels, so the tests that need
 * pixels skip there and stay strict everywhere they can actually run.
 */
const haveImages = existsSync(path.join(CORPUS, "figures"));

/** One real figure out of the shipped index, so the test moves with the corpus. */
async function anyIndexedFigure(): Promise<{ path: string; media_type: string }> {
  const raw = await readFile(path.join(CORPUS, "tables", "figures.json"), "utf8");
  const index = JSON.parse(raw) as {
    figures: Array<{ image_path: string; image_bytes: number }>;
  };
  expect(index.figures.length).toBeGreaterThan(0);
  return { path: index.figures[0].image_path, media_type: "image/jpeg" };
}

/** The shape `figure_fetch` comes back as, after the dispatcher flattens it. */
function figureResult(imagePath: string) {
  return {
    value: {
      value: 36,
      unit: "page",
      method: "figure_fetch v1",
      inputs: {
        figure_id: "some-document#p36",
        kind: "isopach_map",
        image: { path: imagePath, media_type: "image/jpeg", bytes: 475329 },
      },
    },
    method: "deterministic tool layer: figure_fetch",
  };
}

describe("findFigureImage", () => {
  it("finds the image a figure result points at, however deeply it is nested", async () => {
    const figure = await anyIndexedFigure();
    const found = findFigureImage(figureResult(figure.path));
    expect(found).toEqual({ path: figure.path, mediaType: "image/jpeg" });
  });

  it("ignores a result that carries no image", () => {
    // Every other tool in the layer. If this ever matched, every numeric answer
    // would try to become an image call.
    expect(
      findFigureImage({
        value: { value: 4575, unit: "ft", inputs: { canonical: "caddo limestone" } },
      })
    ).toBeNull();
  });

  it("ignores an image key that is not a figure payload", () => {
    expect(findFigureImage({ value: { image: "a string" } })).toBeNull();
    expect(findFigureImage({ value: { image: { path: 12 } } })).toBeNull();
    expect(findFigureImage({ value: { image: { path: "x.jpg" } } })).toBeNull();
  });

  it("does not recurse forever on a cyclic result", () => {
    const cyclic: Record<string, unknown> = { value: 1 };
    cyclic.self = cyclic;
    expect(findFigureImage(cyclic)).toBeNull();
  });
});

describe("readFigureImage", () => {
  it.skipIf(!haveImages)("reads a shipped figure as base64", async () => {
    const figure = await anyIndexedFigure();
    const data = await readFigureImage({ path: figure.path, mediaType: "image/jpeg" });
    expect(data).toBeTruthy();
    // JPEG magic bytes survive the base64 round trip: /9j/ is 0xFFD8FF.
    expect(data!.startsWith("/9j/")).toBe(true);
    expect(Buffer.from(data!, "base64").byteLength).toBeGreaterThan(10_000);
  });

  it("returns null rather than throwing when the file is missing", async () => {
    expect(
      await readFigureImage({ path: "figures/nope/missing.jpg", mediaType: "image/jpeg" })
    ).toBeNull();
  });

  it("refuses a path that escapes the corpus", async () => {
    // The path comes from a corpus table rather than the model, but it reaches a
    // readFile, so it is checked anyway.
    expect(
      await readFigureImage({ path: "../../etc/passwd", mediaType: "image/jpeg" })
    ).toBeNull();
  });
});

describe("the figures do not ship inside a function bundle", () => {
  it("keeps geology-corpus/figures out of the Python function's includeFiles", async () => {
    // The regression this exists for: `includeFiles: "{api/_geology,geology-corpus}/**"`
    // pulled 161 MB of rendered pages into the geology function and the deploy
    // failed at 249 MB against a 250 MB ceiling. The images are served from
    // object storage instead, and nothing about that is enforced by types.
    const raw = await readFile(path.join(process.cwd(), "vercel.json"), "utf8");
    const config = JSON.parse(raw) as {
      functions: Record<string, { includeFiles?: string }>;
    };
    const glob = config.functions["api/geology.py"]?.includeFiles ?? "";
    expect(glob).toBeTruthy();
    expect(
      glob.includes("geology-corpus/**") || glob.includes(",geology-corpus}"),
      `includeFiles would bundle every figure: ${glob}`
    ).toBe(false);
    expect(glob).toContain("geology-corpus/tables");
  });
});

describe("the per-run image budget", () => {
  it("allows the cap and then stops, per run", () => {
    const run = {};
    for (let i = 0; i < MAX_IMAGES_PER_RUN; i++) {
      expect(claimImageBudget(run)).toBe(true);
    }
    expect(claimImageBudget(run)).toBe(false);
    expect(imagesUsed(run)).toBe(MAX_IMAGES_PER_RUN);
  });

  it("counts each run separately", () => {
    const first = {};
    const second = {};
    expect(claimImageBudget(first)).toBe(true);
    expect(imagesUsed(second)).toBe(0);
    expect(claimImageBudget(second)).toBe(true);
  });
});
