// Copied verbatim from wildcat src/lib/structure-maps/contours.ts. Keep in sync.
import { contours as d3Contours } from "d3-contour";
import { toLngLat } from "./geo";
import type { DepthGrid } from "./grid";

/**
 * Contour lines from a depth grid, as GeoJSON in lng/lat.
 *
 * d3-contour walks the grid and hands back, per level, the polygon rings of
 * the region at or above that level; the rings ARE the contour lines. They are
 * cut wherever they leave the well-distance mask, so the map never draws a
 * line through country the tops say nothing about: the grid is evaluated on
 * the whole rectangle (the spline extrapolates smoothly, which keeps the
 * geometry clean at the mask edge), and the mask is applied per vertex here.
 */

export interface ContourLevels {
  /** Every contour level, ascending. */
  levels: number[];
  /** Levels that carry a label and a heavier stroke (every `indexEvery`th). */
  index: Set<number>;
}

/** Levels at `interval`, covering [min, max]; every fifth is an index contour. */
export function contourLevels(min: number, max: number, interval: number, indexEvery = 5): ContourLevels {
  if (!(interval > 0) || !Number.isFinite(min) || !Number.isFinite(max)) {
    return { levels: [], index: new Set() };
  }
  const levels: number[] = [];
  const first = Math.ceil(min / interval) * interval;
  // Cap the count so a tiny interval on a deep range cannot produce a hundred
  // thousand rings; the page tells the user the interval it actually drew.
  for (let v = first; v <= max && levels.length < 400; v += interval) levels.push(Math.round(v * 1e6) / 1e6);
  const index = new Set(levels.filter((v) => Math.round(v / interval) % indexEvery === 0));
  return { levels, index };
}

export interface ContourFeatureProps {
  /** Depth of the line in the map datum, feet. */
  value: number;
  /** True for an index (labelled, heavier) contour. */
  index: boolean;
}

/** Nearest cell's mask value for a grid-space vertex (d3 puts cell centres at
 * i + 0.5). A vertex beyond the outermost cell centres lies on the grid's own
 * edge: d3 closes every "at or above" region along that edge, and those
 * segments are the frame, not a contour, so they are treated as outside. */
function inMask(g: DepthGrid, gx: number, gy: number): boolean {
  if (gx < 0.5 || gy < 0.5 || gx > g.nx - 0.5 || gy > g.ny - 0.5) return false;
  const i = Math.min(g.nx - 1, Math.max(0, Math.floor(gx)));
  const j = Math.min(g.ny - 1, Math.max(0, Math.floor(gy)));
  return g.mask[j * g.nx + i] === 1;
}

function gridToLngLat(g: DepthGrid, gx: number, gy: number): [number, number] {
  const x = g.originX + (gx - 0.5) * g.cellFt;
  const y = g.originY + (gy - 0.5) * g.cellFt;
  const [lng, lat] = toLngLat(g.frame, x, y);
  return [Math.round(lng * 1e6) / 1e6, Math.round(lat * 1e6) / 1e6];
}

/** Split one ring into the runs of vertices that lie inside the mask. */
function maskedRuns(g: DepthGrid, ring: number[][]): [number, number][][] {
  const runs: [number, number][][] = [];
  let current: [number, number][] = [];
  for (const [gx, gy] of ring) {
    if (inMask(g, gx, gy)) {
      current.push(gridToLngLat(g, gx, gy));
    } else if (current.length > 0) {
      runs.push(current);
      current = [];
    }
  }
  if (current.length > 0) runs.push(current);
  // A ring is closed, so a run ending at the ring's end continues at its start.
  if (runs.length > 1 && inMask(g, ring[0][0], ring[0][1]) && inMask(g, ring[ring.length - 1][0], ring[ring.length - 1][1])) {
    const tail = runs.pop()!;
    runs[0] = [...tail, ...runs[0]];
  }
  return runs.filter((r) => r.length >= 2);
}

export function contourLines(g: DepthGrid, levels: ContourLevels): GeoJSON.FeatureCollection<GeoJSON.LineString, ContourFeatureProps> {
  const features: GeoJSON.Feature<GeoJSON.LineString, ContourFeatureProps>[] = [];
  if (levels.levels.length === 0) return { type: "FeatureCollection", features };
  const gen = d3Contours().size([g.nx, g.ny]).thresholds(levels.levels).smooth(true);
  const polys = gen(Array.from(g.values));
  for (const poly of polys) {
    const value = poly.value;
    const index = levels.index.has(value);
    for (const polygon of poly.coordinates) {
      for (const ring of polygon) {
        // d3 closes each ring by repeating the first vertex; drop it so the
        // wrap-around join above does not double a point.
        const open = ring.length > 1 && ring[0][0] === ring[ring.length - 1][0] && ring[0][1] === ring[ring.length - 1][1] ? ring.slice(0, -1) : ring;
        for (const run of maskedRuns(g, open)) {
          // Re-close a run that survived whole: the line is a closed loop.
          const coords = run.length === open.length ? [...run, run[0]] : run;
          features.push({
            type: "Feature",
            geometry: { type: "LineString", coordinates: coords },
            properties: { value, index },
          });
        }
      }
    }
  }
  return { type: "FeatureCollection", features };
}
