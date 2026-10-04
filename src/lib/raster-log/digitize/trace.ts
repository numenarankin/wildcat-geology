import sharp from "sharp"

import { CURVES, classifyImage, type PixelClass } from "./palette"

export type Band = { x0: number; x1: number }

export type TracedCurve = {
  track: number
  /** Index into the palette's curve clusters. */
  curve: number
  color: string
  /** x centroid per pixel row, null where that row holds none of this colour. */
  centroids: (number | null)[]
}

export type Traced = {
  width: number
  height: number
  tracks: Band[]
  gridRows: number[]
  gridColumns: number[]
  curves: TracedCurve[]
}

/** A single run wider than this share of a track is a legend bar, not a trace. */
const MAX_RUN_SHARE = 0.25
/** How far from the last known x a weak-margin rescue may look. */
const RESCUE_WINDOW = 12
/** Rows of gap that linear interpolation may bridge; longer stays a real gap. */
const MAX_BRIDGE = 3
/** Rows after which a curve is treated as lost and continuity restarts. */
const CONTINUITY_ROWS = 30
const GRID_ROW_COVERAGE = 0.25
const GRID_COLUMN_COVERAGE = 0.5
const TRACK_INK = 0.02
const MIN_TRACK_WIDTH = 40
const MIN_GUTTER = 8

/** Traces the cleaned image: one sample per pixel row, no smoothing anywhere. */
export async function traceCleaned(image: Buffer): Promise<Traced> {
  const { data, info } = await sharp(image)
    .removeAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true })

  const { width, height } = info
  const { classes, weak } = classifyImage(data, width, height)
  const tracks = findTracks(classes, width, height)

  const gridRows: number[] = []
  for (let y = 0; y < height; y++) {
    let hits = 0
    for (let x = 0; x < width; x++) {
      if (classes[y * width + x] === "grid") hits++
    }
    if (hits / width > GRID_ROW_COVERAGE) gridRows.push(y)
  }

  const gridColumns: number[] = []
  for (let x = 0; x < width; x++) {
    let hits = 0
    for (let y = 0; y < height; y++) {
      if (classes[y * width + x] === "grid") hits++
    }
    if (hits / height > GRID_COLUMN_COVERAGE) gridColumns.push(x)
  }

  const curves: TracedCurve[] = []

  tracks.forEach((track, trackIndex) => {
    const trackWidth = track.x1 - track.x0

    CURVES.forEach((definition, curveIndex) => {
      const centroids = new Array<number | null>(height).fill(null)
      const maxRun = trackWidth * MAX_RUN_SHARE
      let lastX: number | null = null
      let lastY = -CONTINUITY_ROWS
      let seen = 0

      for (let y = 0; y < height; y++) {
        const row = y * width
        const anchor: number | null = y - lastY <= CONTINUITY_ROWS ? lastX : null

        // Runs of this colour in this row. A steep or doubled-back curve puts
        // several on one row, so pick the one continuing the trace rather than
        // dropping the row.
        let runs = findRuns(track, maxRun, (x) => {
          const pixel = classes[row + x]
          return typeof pixel !== "string" && pixel.curve === curveIndex
        })

        // Nothing at full margin: at a crossing or a thin, near-horizontal
        // stretch the blend misses it, so retry near where the curve was.
        if (runs.length === 0 && anchor !== null) {
          runs = findRuns(track, maxRun, (x) => {
            if (weak[row + x] !== curveIndex + 1) return false
            return Math.abs(x - anchor) <= RESCUE_WINDOW
          })
        }

        if (runs.length === 0) continue

        const chosen: Run =
          anchor === null
            ? runs.reduce((widest, run) => (run.count > widest.count ? run : widest))
            : runs.reduce((closest, run) =>
                Math.abs(run.centre - anchor) < Math.abs(closest.centre - anchor)
                  ? run
                  : closest
              )

        centroids[y] = chosen.centre
        lastX = chosen.centre
        lastY = y
        seen++
      }

      bridge(centroids)

      if (seen > height * 0.02) {
        curves.push({
          track: trackIndex,
          curve: curveIndex,
          color: definition.hex,
          centroids,
        })
      }
    })
  })

  return {
    width,
    height,
    tracks,
    gridRows,
    gridColumns,
    curves,
  }
}

/** Tracks are the inked column bands; the gutters between them are blank. */
function findTracks(classes: PixelClass[], width: number, height: number) {
  const inked = new Array<boolean>(width).fill(false)
  for (let x = 0; x < width; x++) {
    let hits = 0
    for (let y = 0; y < height; y++) {
      if (classes[y * width + x] !== "blank") hits++
    }
    inked[x] = hits / height > TRACK_INK
  }

  const tracks: Band[] = []
  let start: number | null = null

  for (let x = 0; x <= width; x++) {
    const solid = x < width && inked[x]
    if (solid && start === null) start = x
    if (!solid && start !== null) {
      const gutter = blankRun(inked, x)
      if (gutter >= MIN_GUTTER || x === width) {
        if (x - start >= MIN_TRACK_WIDTH) tracks.push({ x0: start, x1: x })
        start = null
      }
    }
  }

  return tracks.length > 0 ? tracks : [{ x0: 0, x1: width }]
}

type Run = { centre: number; count: number }

/** Contiguous x runs of a colour in one row, ignoring single-pixel breaks. */
function findRuns(
  track: Band,
  maxRun: number,
  hit: (x: number) => boolean
): Run[] {
  const runs: Run[] = []
  let start: number | null = null
  let last = -99
  let sum = 0
  let count = 0

  const close = () => {
    if (start === null) return
    if (last - start + 1 <= maxRun) runs.push({ centre: sum / count, count })
    start = null
    sum = 0
    count = 0
  }

  for (let x = track.x0; x <= track.x1; x++) {
    if (x < track.x1 && hit(x)) {
      if (start === null || x - last > 2) {
        if (start !== null) close()
        start = x
      }
      last = x
      sum += x
      count++
    }
  }
  close()

  return runs
}

/** Fill short gaps between two known samples; long ones are real dashes. */
function bridge(centroids: (number | null)[]) {
  let previous: number | null = null

  for (let y = 0; y < centroids.length; y++) {
    if (centroids[y] === null) continue
    if (previous !== null) {
      const gap = y - previous - 1
      if (gap > 0 && gap <= MAX_BRIDGE) {
        const from = centroids[previous]!
        const step = (centroids[y]! - from) / (gap + 1)
        for (let fill = 1; fill <= gap; fill++) {
          centroids[previous + fill] = from + step * fill
        }
      }
    }
    previous = y
  }
}

function blankRun(inked: boolean[], from: number) {
  let length = 0
  while (from + length < inked.length && !inked[from + length]) length++
  return length
}
