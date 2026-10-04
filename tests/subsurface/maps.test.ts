/**
 * The subsurface maps the /map page draws, checked against values worked out
 * by hand from the tops file rather than from the build.
 *
 * Run: node --conditions=react-server --import tsx --test tests/subsurface/maps.test.ts
 * Needs `npm run build:subsurface` to have written data/subsurface/maps.
 *
 * Oracle rows, read off `WildcatIQ-tops (1).TXT` (Marble Falls is the column
 * ending at character 116, Barnett at 128):
 * - 42-363-32156 CRUMPTON-WILLIAMS #24: datum 1239, Marble Falls 4312 MD
 *   -> subsea 1239 - 4312 = -3073.
 * - 42-363-34102 GRAGG #1: datum 1130, Marble Falls 4200, Barnett 4569.31
 *   -> Marble Falls to Barnett thickness 369.31.
 */
import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { getMapContours, getMapMesh, getMapPosts, getMapRaster, getSubsurfaceSummary } from "@/lib/subsurface/maps";

function post(fc: Awaited<ReturnType<typeof getMapPosts>>, id: string) {
  const f = fc?.features.find((x) => x.properties.wellId === id);
  assert.ok(f, `post for ${id}`);
  return f.properties;
}

describe("subsurface maps", () => {
  test("index lists four structures and three isopachs, shallow to deep", async () => {
    const s = await getSubsurfaceSummary();
    assert.ok(s);
    assert.deepEqual(
      s.maps.map((m) => m.id),
      ["caddo", "marble-falls", "barnett", "miss-lime", "caddo-to-marble-falls", "marble-falls-to-barnett", "barnett-to-miss-lime"]
    );
    assert.equal(s.wellsInFile, 2375);
  });

  test("structure post is datum minus measured depth", async () => {
    const p = post(await getMapPosts("marble-falls"), "42-363-32156");
    assert.equal(p.value, -3073);
    assert.equal(p.name, "CRUMPTON-WILLIAMS #24");
  });

  test("isopach post is the interval between the two tops", async () => {
    const p = post(await getMapPosts("marble-falls-to-barnett"), "42-363-34102");
    assert.ok(Math.abs(p.value - 369.31) < 1e-6, String(p.value));
  });

  test("the surface misses wells by no more than neighbouring picks disagree", async () => {
    // The picks are noisy: wells under 1000 ft apart disagree by a median of
    // 12 ft (Caddo), 21 (Marble Falls), 28 (Barnett) and 30 (Miss Lime),
    // measured on the raw file. No surface can honour both of two such wells,
    // so the bar is that scatter, not zero.
    for (const id of ["caddo", "marble-falls", "barnett", "miss-lime"]) {
      const fc = await getMapPosts(id);
      const r = fc!.features
        .map((f) => f.properties.residual)
        .filter((v): v is number => v != null)
        .map(Math.abs)
        .sort((a, b) => a - b);
      const median = r[Math.floor(r.length / 2)];
      assert.ok(median <= 30, `${id} median miss ${median} ft`);
    }
  });

  test("contours sit on the requested interval", async () => {
    const fc = await getMapContours("marble-falls", 50);
    assert.ok(fc && fc.features.length > 0);
    for (const f of fc.features) assert.equal(Math.abs(f.properties.value % 50), 0);
    assert.ok(fc.features.some((f) => f.properties.index));
  });

  test("raster is a PNG the size of the grid", async () => {
    const png = await getMapRaster("caddo");
    assert.ok(png);
    assert.equal(png.subarray(1, 4).toString("ascii"), "PNG");
    const f = JSON.parse(await readFile(path.join(process.cwd(), "data/subsurface/maps/caddo.json"), "utf8"));
    assert.equal(png.readUInt32BE(16), f.nx);
    assert.equal(png.readUInt32BE(20), f.ny);
  });

  test("3D mesh is depth positive down, north row first, holes outside the mask", async () => {
    const buf = await getMapMesh("marble-falls");
    assert.ok(buf);
    const mesh = new Float32Array(buf.buffer, buf.byteOffset, buf.byteLength / 4);
    const f = JSON.parse(await readFile(path.join(process.cwd(), "data/subsurface/maps/marble-falls.json"), "utf8"));
    const vb = Buffer.from(f.values, "base64");
    const values = new Float32Array(vb.buffer, vb.byteOffset, vb.byteLength / 4);
    const mask = Buffer.from(f.mask, "base64");
    assert.equal(mesh.length, f.nx * f.ny);
    // Mesh row 0 is the grid's northernmost row (j = ny - 1).
    for (let i = 0; i < f.nx; i++) {
      const k = (f.ny - 1) * f.nx + i;
      if (mask[k]) assert.equal(mesh[i], -values[k]);
      else assert.ok(Number.isNaN(mesh[i]));
    }
    const finite = Array.from(mesh).filter(Number.isFinite);
    assert.ok(Math.min(...finite) >= -f.max - 0.01 && Math.max(...finite) <= -f.min + 0.01);
    assert.equal(await getMapMesh("marble-falls-to-barnett"), null);
  });

  test("unknown ids read nothing", async () => {
    assert.equal(await getMapPosts("../index"), null);
  });
});
