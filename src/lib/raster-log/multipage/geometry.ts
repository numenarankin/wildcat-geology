import type { Band, Traced } from "../digitize/trace";
import type { LegendCurve } from "./read";

/**
 * A track's true width when the scan cut it off.
 *
 * A paper log is often wider than the scanner bed: the outer edge of the left
 * or right track runs off the page, and the visible band is narrower than the
 * one the scale is printed across. Mapping the scale onto the visible band
 * squeezes every value: on the Todd induction log the resistivity track lost
 * about a tenth of its width and every reading came out ~1.5x too high.
 *
 * The grid says how wide the track really is, because its spacing is fixed by
 * the scale:
 *  - log: lines at every 1..9 x 10^n between the scale's ends, so one decade's
 *    width is fitted from where the lines fall, measured from the edge that
 *    is still on the page;
 *  - linear: the API standard ten divisions per track.
 * A log track is fitted from both ends whether or not it touches the image
 * edge; a linear one only when it does.
 */

/** A track within this share of the image edge is treated as running off it. */
const EDGE_SHARE = 0.02;
/** How close (px) a grid line must fall to a predicted one to count. */
const MATCH_PX = 1.5;
const LINEAR_DIVISIONS = 10;
/** A grid line this close (px) to a track's end is that end's boundary line. */
const EDGE_LINE_PX = 3;

/** Grid columns inside a band, merged into line centres. */
function gridLines(traced: Traced, band: Band): number[] {
  const columns = traced.gridColumns.filter((x) => x >= band.x0 && x < band.x1);
  const centres: number[] = [];
  let run: number[] = [];
  for (const x of columns) {
    if (run.length === 0 || x - run[run.length - 1] <= 2) run.push(x);
    else {
      centres.push((run[0] + run[run.length - 1]) / 2);
      run = [x];
    }
  }
  if (run.length) centres.push((run[0] + run[run.length - 1]) / 2);
  return centres;
}

/** Positions of a log grid's lines, as decades from the scale's low end. */
function logGridOffsets(low: number, high: number): number[] {
  const offsets: number[] = [];
  for (let n = Math.floor(Math.log10(low)); 10 ** n <= high; n++) {
    for (let k = 1; k <= 9; k++) {
      const v = k * 10 ** n;
      if (v > low * 1.0001 && v < high * 0.9999) offsets.push(Math.log10(v / low));
    }
  }
  return offsets;
}

/**
 * Fit the width of one decade: the w for which predicted lines and observed
 * lines best explain each other (precision x recall, so a w that predicts a
 * line everywhere does not win by matching everything).
 */
function fitDecade(lines: number[], offsets: number[], anchor: number, direction: 1 | -1, visible: number, decades: number) {
  if (lines.length < 4) return null;
  let best: { w: number; score: number } | null = null;
  const minW = visible / decades;
  const maxW = (visible / decades) * 2;
  for (let w = minW; w <= maxW; w += 0.25) {
    const predicted = offsets
      .map((o) => anchor + direction * o * w)
      .filter((x) => Math.abs(x - anchor) <= visible);
    if (predicted.length < 3) continue;
    const hitObserved = lines.filter((x) => predicted.some((p) => Math.abs(p - x) <= MATCH_PX)).length;
    const hitPredicted = predicted.filter((p) => lines.some((x) => Math.abs(p - x) <= MATCH_PX)).length;
    const score = (hitObserved / lines.length) * (hitPredicted / predicted.length);
    if (!best || score > best.score) best = { w, score };
  }
  return best && best.score >= 0.5 ? best : null;
}

function linearDivision(lines: number[]): number | null {
  if (lines.length < 4) return null;
  const gaps = lines.slice(1).map((x, i) => x - lines[i]).sort((a, b) => a - b);
  return gaps[gaps.length >> 1];
}

/** The track's full band for this scale, reaching past the visible track where the scan cut it. */
export function fullTrackBand(traced: Traced, track: Band, curve: LegendCurve): Band {
  const visible = track.x1 - track.x0;
  const lines = gridLines(traced, track);

  if (curve.scale === "log") {
    // No image-edge test: the classification crop and the redraw can both
    // leave a margin beyond a cut-off track, so a track that ran off the scan
    // need not touch the image edge. What tells the ends apart is that a real
    // track edge is drawn (a boundary line) and a cut one is not. The decade
    // pattern is fitted from the drawn end only; with both ends drawn the
    // track is whole.
    const drawnLeft = lines.some((x) => Math.abs(x - track.x0) <= EDGE_LINE_PX);
    const drawnRight = lines.some((x) => Math.abs(x - (track.x1 - 1)) <= EDGE_LINE_PX);
    if (drawnLeft === drawnRight) return track;
    const low = Math.min(curve.left, curve.right);
    const high = Math.max(curve.left, curve.right);
    const decades = Math.log10(high / low);
    const lowOnLeft = curve.left < curve.right;
    const base = logGridOffsets(low, high);
    const fit = drawnLeft
      ? fitDecade(lines, base.map((o) => (lowOnLeft ? o : decades - o)), track.x0, 1, visible, decades)
      : fitDecade(lines, base.map((o) => (lowOnLeft ? decades - o : o)), track.x1 - 1, -1, visible, decades);
    const best = fit ? { side: drawnLeft ? ("left" as const) : ("right" as const), w: fit.w } : null;
    if (!best) return track;
    const full = best.w * decades;
    // Only ever widen: a fit narrower than what is visible is a bad fit.
    if (full <= visible * 1.01) return track;
    return best.side === "left" ? { x0: track.x0, x1: track.x0 + full } : { x0: track.x1 - full, x1: track.x1 };
  }

  // Linear grids are uniform, so they cannot say which side is missing; only a
  // track running into the image edge is widened, away from that edge.
  const edge = traced.width * EDGE_SHARE;
  const cutLeft = track.x0 <= edge;
  const cutRight = track.x1 >= traced.width - edge;
  if (cutLeft === cutRight) return track;
  const d = linearDivision(lines);
  if (d === null) return track;
  const full = d * LINEAR_DIVISIONS;
  if (full <= visible * 1.01) return track;
  return cutRight ? { x0: track.x0, x1: track.x0 + full } : { x0: track.x1 - full, x1: track.x1 };
}

/** The pixels a curve's scale runs across: its span of the (full) track. */
export function curveBand(traced: Traced, track: Band, curve: LegendCurve): Band {
  const full = fullTrackBand(traced, track, curve);
  const width = full.x1 - full.x0;
  const [from, to] = curve.span;
  if (from === 0 && to === 1) return full;
  return { x0: full.x0 + from * width, x1: full.x0 + to * width };
}
