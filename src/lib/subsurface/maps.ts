import "server-only";

import { readFile } from "node:fs/promises";
import path from "node:path";
import { toLngLat, toLocal } from "./geo";
import { sampleGrid, type DepthGrid } from "./grid";
import { contourLevels, contourLines, type ContourFeatureProps } from "./contours";
import { gridToPng } from "./png";

/**
 * Subsurface maps, read straight from the files `npm run build:subsurface`
 * writes (no database yet). The build grids the tops; this module turns a
 * grid into what the page draws, with Wildcat's structure-map code: a 16-bit
 * raster Mapbox colours on the GPU (encoded over the colour span, values
 * beyond it clamp to the end colours), contour lines cut at the well-distance
 * mask, and a post per well with the surface's residual there.
 */

const MAPS_DIR = path.join(process.cwd(), "data", "subsurface", "maps");

export type MapKind = "structure" | "isopach";

export interface SubsurfaceMapMeta {
  id: string;
  name: string;
  kind: MapKind;
  /** Wells with this top (structure) or both tops (isopach). */
  wells: number;
  /** Distinct locations after wells closer than a cell were merged. */
  control: number;
  /** Extent of the masked grid, feet. Contours run over this. */
  min: number;
  max: number;
  /** 2nd to 98th percentile of the masked grid: the colour ramp's span, so one
   * bad pick's bullseye does not flatten the rest of the map. */
  colorMin: number;
  colorMax: number;
  contourIntervalFt: number;
  /** Spline damping chosen by cross-validation; null for an isopach. */
  damping: number | null;
  /** Cross-validated R² of the spline on the detrended tops. */
  cvScore: number | null;
}

export interface SubsurfaceSummary {
  source: string;
  wellsInFile: number;
  withApi: number;
  placed: number;
  cellFt: number;
  maps: SubsurfaceMapMeta[];
}

export interface WellPostProps {
  wellId: string;
  name: string;
  /** Subsea top (structure) or interval thickness (isopach), feet. */
  value: number;
  /** Grid minus value at the well, feet. */
  residual: number | null;
}

interface MapFile extends SubsurfaceMapMeta {
  frame: DepthGrid["frame"];
  nx: number;
  ny: number;
  cellFt: number;
  originX: number;
  originY: number;
  maxDistanceFt: number;
  values: string;
  mask: string;
  posts: { id: string; name: string; lng: number; lat: number; value: number }[];
}

interface Loaded {
  meta: SubsurfaceMapMeta;
  grid: DepthGrid;
  posts: MapFile["posts"];
  png?: Buffer;
}

let summaryCache: SubsurfaceSummary | null = null;
const loaded = new Map<string, Loaded>();

export async function getSubsurfaceSummary(): Promise<SubsurfaceSummary | null> {
  if (summaryCache) return summaryCache;
  try {
    summaryCache = JSON.parse(await readFile(path.join(MAPS_DIR, "index.json"), "utf8")) as SubsurfaceSummary;
    return summaryCache;
  } catch {
    return null;
  }
}

async function load(id: string): Promise<Loaded | null> {
  const hit = loaded.get(id);
  if (hit) return hit;
  // Only ids the index lists, so a request can never name another file.
  const summary = await getSubsurfaceSummary();
  const meta = summary?.maps.find((m) => m.id === id);
  if (!meta) return null;
  const f = JSON.parse(await readFile(path.join(MAPS_DIR, `${id}.json`), "utf8")) as MapFile;
  const vb = Buffer.from(f.values, "base64");
  const values = new Float32Array(vb.buffer.slice(vb.byteOffset, vb.byteOffset + vb.byteLength));
  const mask = new Uint8Array(Buffer.from(f.mask, "base64"));
  const grid: DepthGrid = {
    frame: f.frame,
    nx: f.nx,
    ny: f.ny,
    cellFt: f.cellFt,
    originX: f.originX,
    originY: f.originY,
    values,
    mask,
    min: f.min,
    max: f.max,
    maxDistanceFt: f.maxDistanceFt,
  };
  const out = { meta, grid, posts: f.posts };
  loaded.set(id, out);
  return out;
}

/** Image corners for Mapbox, [top-left, top-right, bottom-right, bottom-left].
 * Same as `imageCorners` in wildcat src/lib/structure-maps/build.ts. */
export type Corners = [[number, number], [number, number], [number, number], [number, number]];

function imageCorners(g: DepthGrid): Corners {
  const west = g.originX - 0.5 * g.cellFt;
  const east = g.originX + (g.nx - 0.5) * g.cellFt;
  const south = g.originY - 0.5 * g.cellFt;
  const north = g.originY + (g.ny - 0.5) * g.cellFt;
  return [toLngLat(g.frame, west, north), toLngLat(g.frame, east, north), toLngLat(g.frame, east, south), toLngLat(g.frame, west, south)];
}

export async function getMapCorners(id: string): Promise<Corners | null> {
  const m = await load(id);
  return m ? imageCorners(m.grid) : null;
}

export async function getMapRaster(id: string): Promise<Buffer | null> {
  const m = await load(id);
  if (!m) return null;
  m.png ??= gridToPng({ ...m.grid, min: m.meta.colorMin, max: m.meta.colorMax });
  return m.png;
}

export const MIN_INTERVAL_FT = 5;
export const MAX_INTERVAL_FT = 1000;

export async function getMapContours(
  id: string,
  intervalFt?: number
): Promise<GeoJSON.FeatureCollection<GeoJSON.LineString, ContourFeatureProps> | null> {
  const m = await load(id);
  if (!m) return null;
  const interval =
    intervalFt && Number.isFinite(intervalFt)
      ? Math.min(MAX_INTERVAL_FT, Math.max(MIN_INTERVAL_FT, intervalFt))
      : m.meta.contourIntervalFt;
  return contourLines(m.grid, contourLevels(m.grid.min, m.grid.max, interval));
}

export async function getMapPosts(id: string): Promise<GeoJSON.FeatureCollection<GeoJSON.Point, WellPostProps> | null> {
  const m = await load(id);
  if (!m) return null;
  return {
    type: "FeatureCollection",
    features: m.posts.map((p) => {
      const [x, y] = toLocal(m.grid.frame, p.lng, p.lat);
      const at = sampleGrid(m.grid, x, y);
      return {
        type: "Feature",
        geometry: { type: "Point", coordinates: [p.lng, p.lat] },
        properties: {
          wellId: p.id,
          name: p.name,
          value: p.value,
          residual: at == null ? null : Math.round((at - p.value) * 10) / 10,
        },
      };
    }),
  };
}

/** The grid every map shares, as the 3D viewer's MapLayer `frame` wants it:
 * origin is the south-west node, feet in the local frame. */
export interface GridFrame {
  origin: [number, number];
  increment: [number, number];
  count: [number, number];
}

export async function getGridFrame(): Promise<GridFrame | null> {
  const summary = await getSubsurfaceSummary();
  const first = summary?.maps[0];
  const m = first ? await load(first.id) : null;
  if (!m) return null;
  return { origin: [m.grid.originX, m.grid.originY], increment: [m.grid.cellFt, m.grid.cellFt], count: [m.grid.nx, m.grid.ny] };
}

/**
 * A structure map as the 3D viewer's mesh: float32, depth in feet positive
 * DOWN (the negated subsea value), NaN outside the mask so the surface has
 * holes where the wells say nothing, rows NORTH first (the viewer's
 * MapLayer reads the first row as max y; ours runs south first).
 */
export async function getMapMesh(id: string): Promise<Buffer | null> {
  const m = await load(id);
  if (!m || m.meta.kind !== "structure") return null;
  const { nx, ny, values, mask } = m.grid;
  const out = new Float32Array(nx * ny);
  for (let j = 0; j < ny; j++) {
    const row = ny - 1 - j;
    for (let i = 0; i < nx; i++) {
      const k = j * nx + i;
      out[row * nx + i] = mask[k] ? -values[k] : NaN;
    }
  }
  return Buffer.from(out.buffer);
}
