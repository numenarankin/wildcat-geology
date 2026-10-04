import type { Traced } from "./trace"

/**
 * Dash gaps.
 *
 * A black and white log tells its curves apart by line style, so a dashed curve
 * is a continuous measurement drawn with the ink lifted every few rows. The
 * blanks carry no information, and leaving them NULL loses real readings. This
 * fills a gap that is bounded by a reading on each side, following a cubic that
 * leaves and enters at the slopes the curve is running at either side.
 *
 * Measured against known truth by cutting gaps into the solid curves, an
 * unconstrained cubic loses to a straight line because it overshoots, and a
 * least-squares parabola loses badly. Clamping each end slope to the chord's
 * direction and at most three times its magnitude is what makes the curve pay:
 * p90 error 6.86px to 6.53px, and 3.05px to 2.74px median where the curve is
 * turning hardest, which is where nearly all the error lives.
 *
 * The cleaned image's continuous redraw was also tried as the shape through the
 * gap, anchored to the scan at both ends. It changed no measured error, so it
 * is not used.
 */

/** Rows a dash gap may run to. Beyond this the curve has genuinely stopped. */
const MAX_GAP = 12
/** How far a curve may move across a gap before interpolation is a guess. */
const MAX_SPAN = 40
/** Samples either side used to read the slope the curve arrives and leaves at. */
const SLOPE_ROWS = 5
/** Most the end slopes may exceed the chord before the cubic starts to bulge. */
const OVERSHOOT = 3

export type DashFill = { curves: Traced["curves"]; filled: number; declined: number }

export function fillDashGaps(curves: Traced["curves"]): DashFill {
  let filled = 0
  let declined = 0

  const patched = curves.map((curve) => {
    const centroids = [...curve.centroids]

    for (let y = 1; y < centroids.length; y++) {
      if (centroids[y] !== null) continue
      let end = y
      while (end < centroids.length && centroids[end] === null) end++
      const length = end - y
      const before = centroids[y - 1]
      const after = end < centroids.length ? centroids[end] : null

      if (before === null || after === null) {
        y = end
        continue
      }
      if (length > MAX_GAP || Math.abs(after - before) > MAX_SPAN) {
        declined += length
        y = end
        continue
      }

      const span = length + 1
      const chord = (after - before) / span
      const entry = clamp(slopeAt(centroids, y - 1, -1), chord)
      const exit = clamp(slopeAt(centroids, end, 1), chord)

      for (let step = 0; step < length; step++) {
        const at = (step + 1) / span
        centroids[y + step] =
          (2 * at ** 3 - 3 * at ** 2 + 1) * before +
          (at ** 3 - 2 * at ** 2 + at) * span * entry +
          (-2 * at ** 3 + 3 * at ** 2) * after +
          (at ** 3 - at ** 2) * span * exit
      }
      filled += length
      y = end
    }

    return { ...curve, centroids }
  })

  return { curves: patched, filled, declined }
}

/** Least squares slope of the samples running away from `from` in `step`. */
function slopeAt(
  centroids: (number | null)[],
  from: number,
  step: number
): number {
  const xs: number[] = []
  const ys: number[] = []
  for (let i = 0; i < SLOPE_ROWS; i++) {
    const value = centroids[from + step * i]
    if (value === undefined || value === null) break
    xs.push(step * i)
    ys.push(value)
  }
  if (xs.length < 2) return 0
  const meanX = xs.reduce((sum, x) => sum + x, 0) / xs.length
  const meanY = ys.reduce((sum, y) => sum + y, 0) / ys.length
  let top = 0
  let bottom = 0
  for (let i = 0; i < xs.length; i++) {
    top += (xs[i] - meanX) * (ys[i] - meanY)
    bottom += (xs[i] - meanX) ** 2
  }
  return bottom === 0 ? 0 : top / bottom
}

/** A slope that disagrees with the chord, or dwarfs it, makes the cubic bulge. */
function clamp(slope: number, chord: number): number {
  if (chord === 0 || Math.sign(slope) !== Math.sign(chord)) return 0
  return Math.sign(slope) * Math.min(Math.abs(slope), OVERSHOOT * Math.abs(chord))
}
