import { contourLevels } from "./contours";
import { PALETTES, type PaletteId } from "./palette";

/** Which end of the value range takes the ramp's first (warm) stop: "subsea"
 * puts it on the largest value, "tvd" on the smallest. */
export type MapDatum = "subsea" | "tvd";

export function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

/** The ramp read at t in [0, 1], 0 being the first (shallow) stop. */
export function rampAt(stops: string[], t: number): string {
  const x = Math.min(1, Math.max(0, t)) * (stops.length - 1);
  const i = Math.min(stops.length - 2, Math.floor(x));
  const f = x - i;
  const a = hexToRgb(stops[i]);
  const b = hexToRgb(stops[i + 1]);
  const c = a.map((v, k) => Math.round(v + (b[k] - v) * f));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

export interface Band {
  /** Lower and upper edge, feet; null where the band runs off the colour span. */
  from: number | null;
  to: number | null;
  color: string;
}

/**
 * The fill as solid bands, one per contour interval, so each colour sits
 * between two contour lines (the filled-contour look of a printed structure
 * map). Edges are the contour levels themselves (`contourLevels`, the same
 * call the lines are drawn from). Each band takes the ramp's colour at its
 * midpoint across the colour span; in subsea the shallow (first) stop goes to
 * the LARGEST value. Levels outside the span are dropped, so the outermost
 * bands absorb the outliers.
 */
export function colorBands(palette: PaletteId, datum: MapDatum, span: { min: number; max: number }, intervalFt: number): Band[] {
  const stops = PALETTES[palette].stops;
  const edges = contourLevels(span.min, span.max, intervalFt).levels.filter((v) => v > span.min && v < span.max);
  const bounds: (number | null)[] = [null, ...edges, null];
  const range = span.max - span.min || 1;
  const bands: Band[] = [];
  for (let k = 0; k + 1 < bounds.length; k++) {
    const lo = bounds[k] ?? span.min;
    const hi = bounds[k + 1] ?? span.max;
    const t = ((lo + hi) / 2 - span.min) / range;
    bands.push({ from: bounds[k], to: bounds[k + 1], color: rampAt(stops, datum === "subsea" ? 1 - t : t) });
  }
  return bands;
}

/** The colour of the band holding `v`, as [r, g, b] in 0..255. */
export function bandRgbAt(bands: Band[], v: number): [number, number, number] {
  const band = bands.find((b) => (b.from == null || v >= b.from) && (b.to == null || v < b.to)) ?? bands[bands.length - 1];
  const [r, g, b] = (band.color.match(/\d+/g) ?? ["0", "0", "0"]).map(Number);
  return [r, g, b];
}
