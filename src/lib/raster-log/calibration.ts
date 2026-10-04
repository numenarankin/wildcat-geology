/**
 * Raster well logs: turning feet into pixel rows, and a depth range into crops
 * the model can see without being shrunk. Pure; the I/O is in `raster-log.ts`.
 * Plan: docs/plans/raster-log-crops.md.
 *
 * Pages are 1-based everywhere a person or the model sees them (the tools, the
 * stored calibration, the approval card). Only the `sharp` call is 0-based.
 */

/** One depth label read off the log: this pixel row is this depth. */
export interface DepthAnchor {
  row: number;
  depthFt: number;
}

/** A stretch of one page that carries a single depth scale. */
export interface RasterLogSegment {
  page: number;
  rowStart: number;
  rowEnd: number;
  anchors: DepthAnchor[];
}

export interface RasterLogPage {
  page: number;
  width: number;
  height: number;
}

/** `files.raster_log`. */
export interface RasterLogCalibration {
  pages: RasterLogPage[];
  segments: RasterLogSegment[];
}

/** An anchor as the model proposes it: flat, so the approval card is a table. */
export interface AnchorInput {
  section: number;
  page: number;
  row: number;
  depthFt: number;
}

/*
 * What an image may be before the model shrinks it. Opus 5 (and the rest of the
 * high-resolution tier) takes 2,576 px on the long edge and up to 4,784 visual
 * tokens; at ~750 px per token that is ~3.59 MP. A crop inside both is seen
 * pixel for pixel. A 1,700 px wide log therefore gets 2,110 rows a crop, not
 * 2,576: the pixel budget binds before the edge does.
 */
export const MAX_EDGE_PX = 2576;
export const MAX_IMAGE_PIXELS = 4784 * 750;
/** Crops overlap so a kick sitting on a crop edge is whole in one of them. */
export const OVERLAP_PX = 64;
/** ~19k tokens a call. A longer range says where it stopped. */
export const MAX_CROPS_PER_CALL = 4;

export interface DepthFit {
  interceptFt: number;
  ftPerRow: number;
  /** Anchor depth minus fitted depth, in the order the anchors were given. */
  residualsFt: number[];
  /** How far an anchor may sit off the line before the scale is refused. */
  limitFt: number;
}

/**
 * Least-squares depth = intercept + ftPerRow x row.
 *
 * The limit is 2 ft or 1% of the depth the anchors span, whichever is larger: a
 * label misread by a digit ("4,300" for "4,200") lands 100 ft off and is caught;
 * the few pixels of slop in placing a label is not.
 */
export function fitDepthMap(anchors: DepthAnchor[]): DepthFit {
  const n = anchors.length;
  const meanRow = anchors.reduce((s, a) => s + a.row, 0) / n;
  const meanFt = anchors.reduce((s, a) => s + a.depthFt, 0) / n;
  let cov = 0;
  let varRow = 0;
  for (const a of anchors) {
    cov += (a.row - meanRow) * (a.depthFt - meanFt);
    varRow += (a.row - meanRow) ** 2;
  }
  const ftPerRow = varRow === 0 ? 0 : cov / varRow;
  const interceptFt = meanFt - ftPerRow * meanRow;
  const depths = anchors.map((a) => a.depthFt);
  const span = Math.max(...depths) - Math.min(...depths);
  return {
    interceptFt,
    ftPerRow,
    residualsFt: anchors.map((a) => a.depthFt - (interceptFt + ftPerRow * a.row)),
    limitFt: Math.max(2, 0.01 * span),
  };
}

const ft = (n: number) => `${Math.round(n * 10) / 10}`;

/** Why one section's anchors cannot be a depth scale, or null if they can. */
export function checkAnchors(
  anchors: DepthAnchor[],
  page: RasterLogPage
): string | null {
  if (anchors.length < 3) {
    return `needs at least 3 depth marks, has ${anchors.length}`;
  }
  for (const a of anchors) {
    if (!(a.row >= 0 && a.row < page.height)) {
      return `row ${a.row} is off page ${page.page}, which has rows 0 to ${page.height - 1}`;
    }
  }
  const sorted = [...anchors].sort((a, b) => a.row - b.row);
  for (let i = 1; i < sorted.length; i++) {
    const [above, below] = [sorted[i - 1], sorted[i]];
    if (below.row === above.row) return `row ${below.row} is marked twice`;
    if (below.depthFt <= above.depthFt) {
      return (
        `depth must increase down the log: row ${below.row} reads ${ft(below.depthFt)} ft, ` +
        `below row ${above.row} at ${ft(above.depthFt)} ft`
      );
    }
  }
  const fit = fitDepthMap(anchors);
  const worst = Math.max(...fit.residualsFt.map(Math.abs));
  if (worst > fit.limitFt) {
    const each = anchors
      .map((a, i) => `${ft(a.depthFt)} ft at row ${a.row}: ${ft(fit.residualsFt[i])} ft off`)
      .join("; ");
    return (
      `the marks do not fall on one straight depth scale (allowed ${ft(fit.limitFt)} ft): ${each}. ` +
      `With 3 marks the fit cannot tell which one is wrong; re-read the labels`
    );
  }
  return null;
}

function median(values: number[]): number {
  const s = [...values].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/**
 * The model's flat anchor list, grouped into checked segments.
 *
 * A section's rows run from its outermost labels plus one label interval each
 * way: a depth scale is trusted a label past the last label anyone read, and no
 * further. Where two sections on a page would then overlap, they meet halfway
 * across the gap between their labels.
 */
export function buildCalibration(
  input: AnchorInput[],
  pages: RasterLogPage[]
): { ok: true; calibration: RasterLogCalibration } | { ok: false; problems: string[] } {
  const problems: string[] = [];
  const bySection = new Map<number, AnchorInput[]>();
  for (const a of input) {
    bySection.set(a.section, [...(bySection.get(a.section) ?? []), a]);
  }

  const segments: (RasterLogSegment & { firstRow: number; lastRow: number })[] = [];
  for (const [section, anchors] of [...bySection].sort((a, b) => a[0] - b[0])) {
    const pageNos = new Set(anchors.map((a) => a.page));
    if (pageNos.size > 1) {
      problems.push(`section ${section}: marks on more than one page (${[...pageNos].join(", ")})`);
      continue;
    }
    const page = pages.find((p) => p.page === anchors[0].page);
    if (!page) {
      problems.push(`section ${section}: there is no page ${anchors[0].page}`);
      continue;
    }
    const marks = anchors.map(({ row, depthFt }) => ({ row, depthFt }));
    const problem = checkAnchors(marks, page);
    if (problem) {
      problems.push(`section ${section}: ${problem}`);
      continue;
    }
    const rows = marks.map((m) => m.row).sort((a, b) => a - b);
    const spacing = median(rows.slice(1).map((r, i) => r - rows[i]));
    const firstRow = rows[0];
    const lastRow = rows[rows.length - 1];
    segments.push({
      page: page.page,
      rowStart: Math.max(0, Math.floor(firstRow - spacing)),
      rowEnd: Math.min(page.height, Math.ceil(lastRow + spacing)),
      anchors: marks,
      firstRow,
      lastRow,
    });
  }

  const ordered = [...segments].sort((a, b) => a.page - b.page || a.firstRow - b.firstRow);
  for (let i = 1; i < ordered.length; i++) {
    const [upper, lower] = [ordered[i - 1], ordered[i]];
    if (upper.page !== lower.page) continue;
    if (lower.firstRow <= upper.lastRow) {
      problems.push(
        `sections overlap on page ${lower.page}: rows ${upper.firstRow}-${upper.lastRow} and ${lower.firstRow}-${lower.lastRow}`
      );
      continue;
    }
    if (upper.rowEnd > lower.rowStart) {
      const mid = Math.round((upper.lastRow + lower.firstRow) / 2);
      upper.rowEnd = mid;
      lower.rowStart = mid;
    }
  }

  if (problems.length > 0) return { ok: false, problems };
  return {
    ok: true,
    calibration: {
      pages,
      segments: ordered.map(({ page, rowStart, rowEnd, anchors }) => ({
        page,
        rowStart,
        rowEnd,
        anchors,
      })),
    },
  };
}

/** A segment's fitted scale and the depths its rows cover. */
export function segmentScale(segment: RasterLogSegment) {
  const fit = fitDepthMap(segment.anchors);
  const depthAt = (row: number) => fit.interceptFt + fit.ftPerRow * row;
  const rowAt = (depthFt: number) => (depthFt - fit.interceptFt) / fit.ftPerRow;
  return {
    fit,
    depthAt,
    rowAt,
    topFt: depthAt(segment.rowStart),
    bottomFt: depthAt(segment.rowEnd),
    pxPerFt: 1 / fit.ftPerRow,
  };
}

/**
 * The segment to read a depth range from.
 *
 * One that covers the whole range beats one that covers part of it; among
 * those, the most pixels per foot wins, so the 5" detail section is read ahead
 * of the 1" overview of the same interval. The range comes back clipped to what
 * the segment actually covers.
 */
export function pickSegment(
  calibration: RasterLogCalibration,
  topFt: number,
  bottomFt: number
): { segment: RasterLogSegment; topFt: number; bottomFt: number } | null {
  const ranked = calibration.segments
    .map((segment) => ({ segment, scale: segmentScale(segment) }))
    .filter(({ scale }) => scale.topFt < bottomFt && scale.bottomFt > topFt)
    .map((c) => ({
      ...c,
      covers: c.scale.topFt <= topFt && c.scale.bottomFt >= bottomFt,
    }))
    .sort(
      (a, b) =>
        Number(b.covers) - Number(a.covers) || b.scale.pxPerFt - a.scale.pxPerFt
    );
  const best = ranked[0];
  if (!best) return null;
  return {
    segment: best.segment,
    topFt: Math.max(topFt, best.scale.topFt),
    bottomFt: Math.min(bottomFt, best.scale.bottomFt),
  };
}

export interface CropPlan {
  page: number;
  /** Source rows [top, top + height), full page width. */
  top: number;
  height: number;
  /** What the image is sent at; equal to the source unless the page is too wide. */
  outWidth: number;
  outHeight: number;
}

/**
 * Cut rows [topRow, bottomRow) of a page into crops the model sees unshrunk.
 *
 * Full width always: a curve read without its track and scale header column
 * beside it is a squiggle. A page wider than the edge limit is scaled to fit,
 * which is the one case a crop is not pixel for pixel.
 */
export function planCrops(
  page: RasterLogPage,
  topRow: number,
  bottomRow: number,
  maxCrops = MAX_CROPS_PER_CALL
): { crops: CropPlan[]; nextRow: number | null } {
  const top = Math.max(0, Math.floor(topRow));
  const bottom = Math.min(page.height, Math.ceil(bottomRow));
  const outWidth = Math.min(page.width, MAX_EDGE_PX);
  const scale = outWidth / page.width;
  const maxOutHeight = Math.min(MAX_EDGE_PX, Math.floor(MAX_IMAGE_PIXELS / outWidth));
  const maxRows = Math.floor(maxOutHeight / scale);
  const overlapRows = Math.ceil(OVERLAP_PX / scale);

  const crops: CropPlan[] = [];
  let start = top;
  while (start < bottom) {
    if (crops.length === maxCrops) return { crops, nextRow: start };
    const height = Math.min(maxRows, bottom - start);
    crops.push({
      page: page.page,
      top: start,
      height,
      outWidth,
      outHeight: Math.round(height * scale),
    });
    if (start + height >= bottom) break;
    start = start + height - overlapRows;
  }
  return { crops, nextRow: null };
}

/** A whole page shrunk to fit one image, for finding the sections and labels. */
export function overviewSize(page: RasterLogPage): { width: number; height: number; scale: number } {
  const scale = Math.min(
    1,
    MAX_EDGE_PX / page.width,
    MAX_EDGE_PX / page.height,
    Math.sqrt(MAX_IMAGE_PIXELS / (page.width * page.height))
  );
  return {
    width: Math.max(1, Math.floor(page.width * scale)),
    height: Math.max(1, Math.floor(page.height * scale)),
    scale,
  };
}

/** Parse `files.raster_log`, or null for anything that is not a calibration. */
export function parseCalibration(raw: unknown): RasterLogCalibration | null {
  if (!raw || typeof raw !== "object") return null;
  const c = raw as Partial<RasterLogCalibration>;
  if (!Array.isArray(c.pages) || !Array.isArray(c.segments)) return null;
  return c as RasterLogCalibration;
}
