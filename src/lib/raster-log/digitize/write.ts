import {
  pixelAt,
  valueAt,
  type Calibration,
  type CurveCalibration,
} from "./calibration"
import type { Traced } from "./trace"

export const NULL_VALUE = -999.25
const VALUE_DECIMALS = 4
const DEPTH_DECIMALS = 6
/** Depth intervals a real log grid is drawn at. */
const ROUND_DIVISIONS = [0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100]

export type Check = { name: string; ok: boolean; detail: string }

export type BuiltLas = {
  text: string
  checks: Check[]
  rows: number
  step: number
}

export type LasMeta = { source: string; imageHash: string }

/**
 * One LAS row per pixel row of the traced image. Nothing here resamples,
 * interpolates or smooths: depth is linear in y, value is the row's centroid
 * put through the axis map, and a row with no ink is NULL.
 */
export type Sampled = {
  curves: CurveCalibration[]
  depths: number[]
  /** One array per curve, one entry per depth; null where the row held no ink. */
  values: (number | null)[][]
  step: number
}

/**
 * The traced image as depth rows: depth linear in y, value through each
 * curve's axis map. `buildLas` writes one page from this; the multi-page
 * stitcher combines several.
 */
export function sampleTrace(traced: Traced, calibration: Calibration): Sampled {
  const { columns, depths, values, step } = sampleColumns(traced, calibration)
  return { curves: columns.map((c) => c.curve), depths, values, step }
}

export function buildLas(
  traced: Traced,
  calibration: Calibration,
  meta: LasMeta
): BuiltLas {
  const { columns, depths, values, step } = sampleColumns(traced, calibration)
  const { height } = traced
  const text = render(traced, calibration, meta, columns.map((c) => c.curve), depths, values, step)
  const checks = verify(traced, calibration, columns, depths, values, step)

  return { text, checks, rows: height, step }
}

function sampleColumns(traced: Traced, calibration: Calibration) {
  const { height } = traced
  const rawStep =
    height > 1
      ? (calibration.bottomDepth - calibration.topDepth) / (height - 1)
      : 0
  const step = round(rawStep, DEPTH_DECIMALS)

  const columns = calibration.curves
    .map((curve) => ({
      curve,
      traced: traced.curves.find(
        (candidate) =>
          candidate.track === curve.track && candidate.curve === curve.curve
      ),
    }))
    .filter((column) => column.traced !== undefined)

  const depths: number[] = []
  const values: (number | null)[][] = columns.map(() => [])

  for (let y = 0; y < height; y++) {
    depths.push(round(calibration.topDepth + y * step, DEPTH_DECIMALS))

    columns.forEach((column, index) => {
      const centroid = column.traced!.centroids[y]
      if (centroid === null) {
        values[index].push(null)
        return
      }
      const track = column.curve.band ?? traced.tracks[column.curve.track]
      values[index].push(
        round(valueAt(centroid, track, column.curve), VALUE_DECIMALS)
      )
    })
  }

  return { columns, depths, values, step }
}

function render(
  traced: Traced,
  calibration: Calibration,
  meta: LasMeta,
  curves: CurveCalibration[],
  depths: number[],
  values: (number | null)[][],
  step: number
) {
  const unit = calibration.depthUnit
  const lines: string[] = [
    "~VERSION INFORMATION",
    info("VERS", "", "2.0", "CWLS LOG ASCII STANDARD - VERSION 2.0"),
    info("WRAP", "", "NO", "ONE LINE PER DEPTH STEP"),
    "~WELL INFORMATION",
    info("STRT", unit, fixed(depths[0] ?? 0, DEPTH_DECIMALS), "START DEPTH"),
    info("STOP", unit, fixed(depths[depths.length - 1] ?? 0, DEPTH_DECIMALS), "STOP DEPTH"),
    info("STEP", unit, fixed(step, DEPTH_DECIMALS), "STEP"),
    info("NULL", "", String(NULL_VALUE), "NULL VALUE"),
    info("WELL", "", meta.source, "SOURCE IMAGE"),
    "~CURVE INFORMATION",
    info("DEPT", unit, "", "DEPTH"),
    ...curves.map((curve) =>
      info(
        curve.mnemonic,
        curve.unit,
        "",
        `TRACK ${curve.track + 1} COLOUR ${curve.color}`
      )
    ),
    "~PARAMETER INFORMATION",
    info("IMGH", "", meta.imageHash, "CLEANED IMAGE SHA-256"),
    info("IMGW", "PX", String(traced.width), "IMAGE WIDTH"),
    info("IMGH_PX", "PX", String(traced.height), "IMAGE HEIGHT"),
    ...curves.map((curve) =>
      info(
        `${curve.mnemonic}_AX`,
        "",
        `${curve.min} ${curve.max} ${curve.scale} ${(curve.band ?? traced.tracks[curve.track]).x0}-${(curve.band ?? traced.tracks[curve.track]).x1}`,
        "MIN MAX SCALE TRACK-PX"
      )
    ),
    "~ASCII",
  ]

  for (let row = 0; row < depths.length; row++) {
    const cells = [fixed(depths[row], DEPTH_DECIMALS)]
    for (const column of values) {
      const value = column[row]
      cells.push(
        value === null ? String(NULL_VALUE) : fixed(value, VALUE_DECIMALS)
      )
    }
    lines.push(cells.join(" "))
  }

  return `${lines.join("\n")}\n`
}

function verify(
  traced: Traced,
  calibration: Calibration,
  columns: { curve: CurveCalibration; traced?: Traced["curves"][number] }[],
  depths: number[],
  values: (number | null)[][],
  step: number
): Check[] {
  const checks: Check[] = []

  checks.push({
    name: "One row per pixel row",
    ok: depths.length === traced.height,
    detail: `${depths.length} rows, ${traced.height} pixel rows`,
  })

  let worstStep = 0
  for (let row = 1; row < depths.length; row++) {
    worstStep = Math.max(worstStep, Math.abs(depths[row] - depths[row - 1] - step))
  }
  checks.push({
    name: "Depth step constant",
    ok: worstStep <= 2e-6,
    detail: `step ${step}, worst deviation ${worstStep.toExponential(1)}`,
  })

  let outside = 0
  columns.forEach((column, index) => {
    const low = Math.min(column.curve.min, column.curve.max)
    const high = Math.max(column.curve.min, column.curve.max)
    for (const value of values[index]) {
      if (value === null) continue
      if (value < low - 1e-6 || value > high + 1e-6) outside++
    }
  })
  checks.push({
    name: "Values inside track domain",
    ok: outside === 0,
    detail: outside === 0 ? "all inside" : `${outside} outside`,
  })

  let nullMismatch = 0
  columns.forEach((column, index) => {
    const blanks = column.traced!.centroids.filter((c) => c === null).length
    const written = values[index].filter((v) => v === null).length
    if (blanks !== written) nullMismatch++
  })
  checks.push({
    name: "NULLs match blank rows",
    ok: nullMismatch === 0,
    detail: nullMismatch === 0 ? "counted independently, equal" : `${nullMismatch} curves differ`,
  })

  let worstPixel = 0
  columns.forEach((column, index) => {
    const track = column.curve.band ?? traced.tracks[column.curve.track]
    column.traced!.centroids.forEach((centroid, row) => {
      const value = values[index][row]
      if (centroid === null || value === null) return
      worstPixel = Math.max(
        worstPixel,
        Math.abs(pixelAt(value, track, column.curve) - centroid)
      )
    })
  })
  checks.push({
    name: "Value inverts to the same pixel",
    ok: worstPixel < 0.01,
    detail: `worst ${worstPixel.toExponential(2)} px`,
  })

  const spacing = medianSpacing(traced.gridRows)
  if (spacing === null) {
    checks.push({
      name: "Grid spacing implies a round interval",
      ok: true,
      detail: "too few grid lines to check",
    })
  } else {
    const implied = Math.abs(step) * spacing
    const nearest = ROUND_DIVISIONS.reduce((best, candidate) =>
      Math.abs(candidate - implied) < Math.abs(best - implied) ? candidate : best
    )
    const off = Math.abs(implied - nearest) / nearest
    // A grid measured in whole pixels can only be so exact: half a pixel of
    // spacing error is the floor, whatever the percentage works out to.
    const tolerance = Math.max(0.02, (0.5 * Math.abs(step)) / implied)
    checks.push({
      name: "Grid spacing implies a round interval",
      ok: off <= tolerance,
      detail: `${spacing}px grid = ${implied.toFixed(2)} ${calibration.depthUnit}, nearest round ${nearest}`,
    })
  }

  return checks
}

function medianSpacing(positions: number[]) {
  const centers: number[] = []
  let run: number[] = []
  for (const position of positions) {
    if (run.length === 0 || position - run[run.length - 1] <= 2) {
      run.push(position)
    } else {
      centers.push((run[0] + run[run.length - 1]) / 2)
      run = [position]
    }
  }
  if (run.length) centers.push((run[0] + run[run.length - 1]) / 2)
  if (centers.length < 3) return null

  const gaps = centers.slice(1).map((center, index) => center - centers[index])
  gaps.sort((a, b) => a - b)
  return gaps[gaps.length >> 1]
}

function info(mnemonic: string, unit: string, value: string, description: string) {
  return ` ${mnemonic}.${unit} ${value} : ${description}`
}

function fixed(value: number, decimals: number) {
  return value.toFixed(decimals)
}

function round(value: number, decimals: number) {
  const factor = 10 ** decimals
  return Math.round(value * factor) / factor
}
