import sharp from "sharp"

import { askGeminiJson, type GeminiUsage } from "./gemini"

export type DepthLabel = { y: number; value: number }

export type DepthFit = {
  labels: DepthLabel[]
  usage: GeminiUsage
  topDepth: number
  bottomDepth: number
  feetPerPixel: number
  /** Worst distance in feet between a label and the fitted line. */
  residual: number
}

/** Text is near-black; curves and grid are not. */
const MAX_INK = 110
const MAX_SPREAD = 45
const MIN_GLYPH_HEIGHT = 6
const MAX_GLYPH_HEIGHT = 44
const MAX_GLYPH_WIDTH = 60
/** Glyphs closer than this horizontally belong to the same number. */
const GLYPH_GAP = 14
const MIN_LABEL_WIDTH = 14
const MAX_LABELS = 12
const PAD = 4

type Box = { x0: number; y0: number; x1: number; y1: number }

/**
 * Reads the printed depth labels: the geometry is measured here (so each
 * label's y is exact) and only the digits go to the model.
 */
/**
 * Every depth label on the image: positions measured here, digits read by the
 * model. One label is enough for a caller that already knows the depth scale
 * (the multi-page path); `readDepths` below needs two to fit one.
 */
export async function readLabels(
  image: Buffer,
  /**
   * The scan the redraw was made from. When given, the digits are read off
   * the SCAN at each label's position, not off the redraw: where the redraw
   * could not make a label out, it has been seen to print the clean-up
   * prompt's example depths (4700, 4750, ...) instead.
   */
  source?: Buffer
): Promise<{ labels: DepthLabel[]; usage: GeminiUsage; height: number }> {
  const { data, info } = await sharp(image)
    .removeAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true })

  const { width, height } = info
  const boxes = labelBoxes(data, width, height)
  if (boxes.length < 1) {
    throw new Error("Found no depth labels")
  }

  const scan = source ? await sharp(source).metadata() : null
  const sx = scan?.width ? scan.width / width : 1
  const sy = scan?.height ? scan.height / height : 1
  // On the scan, the label may sit a little off where the redraw put it, so
  // the crop gets more room around it there.
  const pad = source ? PAD * 3 : PAD
  const crops = await Promise.all(
    boxes.map((box) => {
      const W = scan?.width ?? width
      const H = scan?.height ?? height
      const left = Math.max(0, Math.floor((box.x0 - pad) * sx))
      const top = Math.max(0, Math.floor((box.y0 - pad) * sy))
      const right = Math.min(W, Math.ceil((box.x1 + pad) * sx))
      const bottom = Math.min(H, Math.ceil((box.y1 + pad) * sy))
      return sharp(source ?? image)
        .extract({ left, top, width: right - left, height: bottom - top })
        .resize({ width: Math.max(60, Math.round(((box.x1 - box.x0 + pad * 2) * 3))) })
        .png()
        .toBuffer()
    })
  )

  const { values, usage } = await readNumbers(crops)
  const labels: DepthLabel[] = []

  boxes.forEach((box, index) => {
    const value = values[index]
    if (value === null) return
    labels.push({ y: (box.y0 + box.y1) / 2, value })
  })

  if (labels.length < 1) {
    throw new Error("Could not read any depth label")
  }

  return { labels, usage, height }
}

export async function readDepths(image: Buffer): Promise<DepthFit> {
  const { labels, usage, height } = await readLabels(image)
  if (labels.length < 2) {
    throw new Error(`Found ${labels.length} depth labels; need at least 2`)
  }
  return { ...fit(labels, height), usage }
}

/** Least squares through the labels: depth = feetPerPixel * y + top. */
function fit(labels: DepthLabel[], height: number): Omit<DepthFit, "usage"> {
  const n = labels.length
  const sumY = labels.reduce((sum, label) => sum + label.y, 0)
  const sumD = labels.reduce((sum, label) => sum + label.value, 0)
  const sumYY = labels.reduce((sum, label) => sum + label.y * label.y, 0)
  const sumYD = labels.reduce((sum, label) => sum + label.y * label.value, 0)

  const denominator = n * sumYY - sumY * sumY
  if (denominator === 0) throw new Error("Depth labels share one row")

  const feetPerPixel = (n * sumYD - sumY * sumD) / denominator
  const intercept = (sumD - feetPerPixel * sumY) / n

  const residual = labels.reduce(
    (worst, label) =>
      Math.max(worst, Math.abs(label.value - (feetPerPixel * label.y + intercept))),
    0
  )

  return {
    labels: labels.sort((a, b) => a.y - b.y),
    topDepth: round(intercept),
    bottomDepth: round(feetPerPixel * (height - 1) + intercept),
    feetPerPixel,
    residual,
  }
}

function round(value: number) {
  return Math.round(value * 100) / 100
}

/** Dark glyphs, grouped into the numbers they spell. */
function labelBoxes(data: Buffer, width: number, height: number): Box[] {
  const ink = new Uint8Array(width * height)
  for (let index = 0; index < width * height; index++) {
    const offset = index * 3
    const r = data[offset]
    const g = data[offset + 1]
    const b = data[offset + 2]
    const max = Math.max(r, g, b)
    const min = Math.min(r, g, b)
    if (max <= MAX_INK && max - min <= MAX_SPREAD) ink[index] = 1
  }

  const glyphs: Box[] = []
  const seen = new Uint8Array(width * height)
  const stack: number[] = []

  for (let start = 0; start < width * height; start++) {
    if (!ink[start] || seen[start]) continue

    let box: Box = {
      x0: start % width,
      y0: Math.floor(start / width),
      x1: start % width,
      y1: Math.floor(start / width),
    }
    stack.push(start)
    seen[start] = 1

    while (stack.length) {
      const at = stack.pop()!
      const x = at % width
      const y = Math.floor(at / width)
      box = {
        x0: Math.min(box.x0, x),
        y0: Math.min(box.y0, y),
        x1: Math.max(box.x1, x),
        y1: Math.max(box.y1, y),
      }

      for (const [dx, dy] of [
        [1, 0],
        [-1, 0],
        [0, 1],
        [0, -1],
      ]) {
        const nx = x + dx
        const ny = y + dy
        if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue
        const next = ny * width + nx
        if (ink[next] && !seen[next]) {
          seen[next] = 1
          stack.push(next)
        }
      }
    }

    const glyphHeight = box.y1 - box.y0 + 1
    const glyphWidth = box.x1 - box.x0 + 1
    if (
      glyphHeight >= MIN_GLYPH_HEIGHT &&
      glyphHeight <= MAX_GLYPH_HEIGHT &&
      glyphWidth <= MAX_GLYPH_WIDTH
    ) {
      glyphs.push(box)
    }
  }

  // Glyphs on the same line and close together spell one number.
  const byLine = new Map<number, Box[]>()
  for (const glyph of glyphs) {
    const key = Math.round((glyph.y0 + glyph.y1) / 2 / 6)
    const line = byLine.get(key)
    if (line) line.push(glyph)
    else byLine.set(key, [glyph])
  }

  const labels: Box[] = []
  for (const line of byLine.values()) {
    line.sort((a, b) => a.x0 - b.x0)
    let group: Box | null = null

    for (const glyph of line) {
      if (group && glyph.x0 - group.x1 <= GLYPH_GAP) {
        group = {
          x0: Math.min(group.x0, glyph.x0),
          y0: Math.min(group.y0, glyph.y0),
          x1: Math.max(group.x1, glyph.x1),
          y1: Math.max(group.y1, glyph.y1),
        }
      } else {
        if (group && group.x1 - group.x0 >= MIN_LABEL_WIDTH) labels.push(group)
        group = glyph
      }
    }
    if (group && group.x1 - group.x0 >= MIN_LABEL_WIDTH) labels.push(group)
  }

  return labels.sort((a, b) => a.y0 - b.y0).slice(0, MAX_LABELS)
}

/** The only part a model does: turning each crop into its digits. */
async function readNumbers(
  crops: Buffer[]
): Promise<{ values: (number | null)[]; usage: GeminiUsage }> {
  const { value, usage } = await askGeminiJson<(number | string | null)[]>(
    crops,
    `Each image is a depth label printed on a well log. Read the number in each one.

Reply with only a JSON array of ${crops.length} entries, in the same order as the images. Use the number itself, or null if the image holds no readable number.`
  )
  const parsed = value ?? []
  if (!Array.isArray(parsed)) throw new Error("Unexpected reply reading depths")
  const values = crops.map((_, index) => {
    const value = parsed[index]
    // The model returns numbers as strings as often as not.
    const number =
      typeof value === "number"
        ? value
        : typeof value === "string" && value.trim() !== ""
          ? Number(value.replace(/,/g, ""))
          : NaN
    return Number.isFinite(number) ? number : null
  })
  return { values, usage }
}
