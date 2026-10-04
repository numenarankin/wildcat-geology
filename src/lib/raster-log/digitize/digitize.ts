import "server-only";

import { createHash } from "node:crypto";
import sharp from "sharp";

import { defaultCalibration, type CurveCalibration } from "./calibration";
import { fillDashGaps } from "./dash";
import { readDepths, readLabels, type DepthLabel } from "./depths";
import { cleanLogImage, type CleanedLog, type GeminiUsage } from "./gemini";
import { traceCleaned, type Traced } from "./trace";
import { buildLas, sampleTrace, type Check, type Sampled } from "./write";

/**
 * A scanned raster log to LAS, the way the log sandbox does it: Gemini redraws
 * the scan as a figure a program can trace (colour per curve, grey grid), the
 * curves are traced off that redraw one sample per pixel row, the depth labels
 * are read off the same redraw, and the LAS is written from those bytes.
 */

export interface Digitized {
  text: string;
  rows: number;
  checks: Check[];
  /** Depth labels read off the redraw, in redraw pixel rows. */
  labels: DepthLabel[];
  topDepth: number;
  bottomDepth: number;
  /** The redraw's size, so its rows can be mapped onto the scan's. */
  cleaned: { width: number; height: number };
  scan: { width: number; height: number };
  usage: GeminiUsage[];
  costUsd: number;
}

/** The first page of a TIFF (or any raster) as PNG, with its size. */
export async function firstPagePng(
  bytes: Buffer
): Promise<{ png: Buffer; width: number; height: number }> {
  const image = sharp(bytes, { page: 0 });
  const { width, height } = await image.metadata();
  if (!width || !height) throw new Error("Could not read the scan's size");
  return { png: await image.png().toBuffer(), width, height };
}

export async function digitizeScan(bytes: Buffer, source: string): Promise<Digitized> {
  const scan = await firstPagePng(bytes);
  const cleaned = await cleanLogImage(scan.png);
  const trace = await traceCleaned(cleaned.image);
  const depths = await readDepths(cleaned.image);
  const built = buildLas(
    { ...trace, curves: fillDashGaps(trace.curves).curves },
    {
      ...defaultCalibration(trace),
      topDepth: depths.topDepth,
      bottomDepth: depths.bottomDepth,
    },
    { source, imageHash: createHash("sha256").update(cleaned.image).digest("hex") }
  );

  const usage = [cleaned.usage, depths.usage];
  return {
    text: built.text,
    rows: built.rows,
    checks: built.checks,
    labels: depths.labels,
    topDepth: depths.topDepth,
    bottomDepth: depths.bottomDepth,
    cleaned: { width: trace.width, height: trace.height },
    scan: { width: scan.width, height: scan.height },
    usage,
    costUsd: usage.reduce((sum, u) => sum + u.costUsd, 0),
  };
}

export type DigitizedPage = {
  /** Depth rows, before any stitching. */
  sampled: Sampled;
  checks: Check[];
  labels: DepthLabel[];
  topDepth: number;
  bottomDepth: number;
  /** Feet per pixel of the page image sent in, so other pages can borrow the scale. */
  feetPerSourcePixel: number;
  /** Traced (track, colour) pairs `calibrate` could not name; they keep the default guess. */
  uncalibrated: { track: number; color: string }[];
  /** Tracks the trace found, left to right. */
  trackCount: number;
  usage: GeminiUsage[];
  costUsd: number;
};

/** A page redrawn and traced: the expensive half, done once. */
export type RedrawnPage = {
  /** The page image that was redrawn, kept to read the depth digits off. */
  png: Buffer;
  cleaned: CleanedLog;
  trace: Traced;
  sourceHeight: number;
  source: string;
};

/** Step one of a page: Gemini's redraw, then the trace (curves by colour, tracks by gutter). */
export async function redrawPage(png: Buffer, source: string): Promise<RedrawnPage> {
  const { height = 0 } = await sharp(png).metadata();
  const cleaned = await cleanLogImage(png);
  const trace = await traceCleaned(cleaned.image);
  return { png, cleaned, trace: { ...trace, curves: fillDashGaps(trace.curves).curves }, sourceHeight: height, source };
}

/** The depth labels on a redrawn page, positions in SOURCE pixels so pages compare. */
export async function pageLabels(
  page: RedrawnPage
): Promise<{ labels: DepthLabel[]; usage: GeminiUsage }> {
  // Digits off the scan first. If none can be made out there (the redraw put
  // the label somewhere the crop misses), fall back to the redraw's own
  // digits; the multi-page placement rejects a page whose labels disagree.
  const read = await readLabels(page.cleaned.image, page.png).catch(() => null);
  const { labels, usage } =
    read && read.labels.length > 0 ? read : await readLabels(page.cleaned.image);
  const toSource = page.sourceHeight > 0 ? page.sourceHeight / page.trace.height : 1;
  return { labels: labels.map((l) => ({ y: l.y * toSource, value: l.value })), usage };
}

/**
 * Step two: name the curves and write depth rows, given the page's depth at
 * its first and last SOURCE pixel row. `calibrate` receives the trace and
 * returns the curves it can identify; a traced curve it does not name keeps
 * `defaultCalibration`'s guess and is reported in `uncalibrated` rather than
 * dropped.
 */
export function calibratePage(
  page: RedrawnPage,
  calibrate: (traced: Traced) => CurveCalibration[] | null,
  depth: { topDepth: number; bottomDepth: number; labels: DepthLabel[] },
  usage: GeminiUsage[],
  /** Leave unnamed curves out instead of writing the default guess (set when a legend exists). */
  dropUnnamed = false
): DigitizedPage {
  const { cleaned, trace } = page;
  const guessed = defaultCalibration(trace);
  const named = calibrate(trace) ?? [];
  const uncalibrated: { track: number; color: string }[] = [];
  const curves = guessed.curves.flatMap((guess) => {
    const found = named.find((c) => c.track === guess.track && c.curve === guess.curve);
    if (!found) uncalibrated.push({ track: guess.track, color: guess.color });
    return found ? [found] : dropUnnamed ? [] : [guess];
  });
  const calibration = { ...guessed, curves, topDepth: depth.topDepth, bottomDepth: depth.bottomDepth };

  const built = buildLas(trace, calibration, {
    source: page.source,
    imageHash: createHash("sha256").update(cleaned.image).digest("hex"),
  });
  const all = [cleaned.usage, ...usage];
  return {
    sampled: sampleTrace(trace, calibration),
    checks: built.checks,
    labels: depth.labels,
    topDepth: depth.topDepth,
    bottomDepth: depth.bottomDepth,
    feetPerSourcePixel:
      page.sourceHeight > 1 ? (depth.bottomDepth - depth.topDepth) / (page.sourceHeight - 1) : 0,
    uncalibrated,
    trackCount: trace.tracks.length,
    usage: all,
    costUsd: all.reduce((sum, u) => sum + u.costUsd, 0),
  };
}
