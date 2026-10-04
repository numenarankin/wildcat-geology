import type { LocalFrame } from "./geo";

/**
 * A gridded surface as Wildcat's structure-map code reads it. Gridding itself
 * happens offline in `scripts/subsurface/build_maps.py` (verde, xtgeo); this
 * is the shape the copied `contours.ts` and `png.ts` take, and `sampleGrid` is
 * copied verbatim from wildcat src/lib/structure-maps/grid.ts.
 */
export interface DepthGrid {
  frame: LocalFrame;
  nx: number;
  ny: number;
  cellFt: number;
  /** Local coordinates of the centre of cell (0, 0), the south-west cell. */
  originX: number;
  originY: number;
  /** Row-major, `values[j * nx + i]`, j increasing northward. Every cell holds
   * a finite estimate; `mask` says which ones are within reach of a well. */
  values: Float32Array;
  /** 1 where the cell is within `maxDistanceFt` of a well, else 0. */
  mask: Uint8Array;
  /** Extent of the masked values. */
  min: number;
  max: number;
  maxDistanceFt: number;
}

/** Bilinear read of the grid at a local coordinate, for well-post residuals
 * and hover readouts. Returns null outside the grid or the mask. */
export function sampleGrid(g: DepthGrid, x: number, y: number): number | null {
  const gx = (x - g.originX) / g.cellFt;
  const gy = (y - g.originY) / g.cellFt;
  if (gx < 0 || gy < 0 || gx > g.nx - 1 || gy > g.ny - 1) return null;
  const i0 = Math.min(Math.floor(gx), g.nx - 2);
  const j0 = Math.min(Math.floor(gy), g.ny - 2);
  const fx = gx - i0;
  const fy = gy - j0;
  const k = j0 * g.nx + i0;
  if (!g.mask[k] && !g.mask[k + 1] && !g.mask[k + g.nx] && !g.mask[k + g.nx + 1]) return null;
  const v00 = g.values[k];
  const v10 = g.values[k + 1];
  const v01 = g.values[k + g.nx];
  const v11 = g.values[k + g.nx + 1];
  return (1 - fy) * ((1 - fx) * v00 + fx * v10) + fy * ((1 - fx) * v01 + fx * v11);
}
