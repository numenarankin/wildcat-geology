import type { Traced } from "./trace"

export type Scale = "linear" | "log"

export type CurveCalibration = {
  track: number
  /** Index of the palette cluster this curve came from. */
  curve: number
  color: string
  mnemonic: string
  unit: string
  min: number
  max: number
  scale: Scale
  /**
   * The pixel span the scale runs across, when it is not the traced track's:
   * a curve scaled over part of a track, or a track the scan cut off at the
   * page edge (wider than what is visible). Absent means the whole track.
   */
  band?: { x0: number; x1: number }
}

export type Calibration = {
  topDepth: number
  bottomDepth: number
  depthUnit: string
  curves: CurveCalibration[]
}

/**
 * Conventional triple-combo names so the curves land in the right track of a
 * LAS viewer. They are a starting point, not a reading of the image.
 */
type Preset = Omit<CurveCalibration, "track" | "curve" | "color">

const DEFAULTS: Record<number, Preset[]> = {
  0: [
    { mnemonic: "GR", unit: "GAPI", min: 0, max: 150, scale: "linear" },
    { mnemonic: "SP", unit: "MV", min: -160, max: 40, scale: "linear" },
    { mnemonic: "CALI", unit: "IN", min: 6, max: 16, scale: "linear" },
  ],
  1: [
    { mnemonic: "RESD", unit: "OHMM", min: 0.2, max: 2000, scale: "log" },
    { mnemonic: "RESM", unit: "OHMM", min: 0.2, max: 2000, scale: "log" },
    { mnemonic: "RESS", unit: "OHMM", min: 0.2, max: 2000, scale: "log" },
  ],
}

export function defaultCalibration(traced: Traced): Calibration {
  return {
    topDepth: 0,
    bottomDepth: 0,
    depthUnit: "F",
    curves: traced.curves.map(({ track, curve, color }, index) => {
      const withinTrack = traced.curves
        .filter((candidate) => candidate.track === track)
        .findIndex((candidate) => candidate.curve === curve)
      const preset = DEFAULTS[track]?.[withinTrack]
      return {
        track,
        curve,
        color,
        mnemonic: preset?.mnemonic ?? `CURVE${index + 1}`,
        unit: preset?.unit ?? "",
        min: preset?.min ?? 0,
        max: preset?.max ?? 100,
        scale: preset?.scale ?? "linear",
      }
    }),
  }
}

/** Pixel x within a track → curve value. The only place the axis is applied. */
export function valueAt(
  x: number,
  track: { x0: number; x1: number },
  curve: CurveCalibration
) {
  const span = track.x1 - 1 - track.x0
  const t = span <= 0 ? 0 : (x - track.x0) / span

  return curve.scale === "log"
    ? curve.min * Math.pow(curve.max / curve.min, t)
    : curve.min + (curve.max - curve.min) * t
}

/** The inverse, used to prove the written value maps back to the same pixel. */
export function pixelAt(
  value: number,
  track: { x0: number; x1: number },
  curve: CurveCalibration
) {
  const span = track.x1 - 1 - track.x0
  const t =
    curve.scale === "log"
      ? Math.log(value / curve.min) / Math.log(curve.max / curve.min)
      : (value - curve.min) / (curve.max - curve.min)

  return track.x0 + t * span
}
