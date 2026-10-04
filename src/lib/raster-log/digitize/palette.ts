/**
 * Classification against the palette the prompt dictates: each curve is a pure
 * primary, the grid is light grey, the page is white. The generator's output is
 * JPEG, so the exact shade is never what was asked for — but the dominant
 * channel survives compression, which is all this needs. Keeping the classifier
 * tied to the prompt means one source of truth for what the colours mean.
 */

export type CurveName = "red" | "green" | "blue"

export type PixelClass = "blank" | "grid" | { curve: number }

export const CURVES: { name: CurveName; hex: string }[] = [
  { name: "red", hex: "#e11d48" },
  { name: "green", hex: "#15803d" },
  { name: "blue", hex: "#1d4ed8" },
]

/** Ink darker than this is text, not a curve. */
const MIN_INK = 30
/** A channel must lead the next by this much to name the colour. */
const DOMINANCE = 25
/** Used only to rescue a row that would otherwise be empty: where two curves
 * cross, or a near-horizontal stretch thins out, the blend misses DOMINANCE. */
const WEAK_DOMINANCE = 8
/** Spread below this is a grey: page, grid or text. */
const GREY_SPREAD = 40
/** Greys between these bounds are the grid; brighter is the page. */
const GRID_MIN = 90
const GRID_MAX = 242

export function classifyPixel(r: number, g: number, b: number): PixelClass {
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)

  if (max - min < GREY_SPREAD) {
    return max >= GRID_MIN && max <= GRID_MAX ? "grid" : "blank"
  }

  if (max < MIN_INK) return "blank"

  const curve = leadingChannel(r, g, b, DOMINANCE)
  return curve === null ? "blank" : { curve }
}

function leadingChannel(r: number, g: number, b: number, margin: number) {
  const max = Math.max(r, g, b)
  const second =
    r === max ? Math.max(g, b) : g === max ? Math.max(r, b) : Math.max(r, g)
  if (max - second < margin) return null
  return r === max ? 0 : g === max ? 1 : 2
}

export type Classified = {
  classes: PixelClass[]
  /** Curve index + 1 under the looser margin, 0 for none. */
  weak: Uint8Array
}

export function classifyImage(
  data: Buffer,
  width: number,
  height: number
): Classified {
  const classes = new Array<PixelClass>(width * height)
  const weak = new Uint8Array(width * height)

  for (let index = 0; index < width * height; index++) {
    const offset = index * 3
    const r = data[offset]
    const g = data[offset + 1]
    const b = data[offset + 2]
    classes[index] = classifyPixel(r, g, b)

    const max = Math.max(r, g, b)
    if (max >= MIN_INK && max - Math.min(r, g, b) >= GREY_SPREAD) {
      const curve = leadingChannel(r, g, b, WEAK_DOMINANCE)
      if (curve !== null) weak[index] = curve + 1
    }
  }

  return { classes, weak }
}
