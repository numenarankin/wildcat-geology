import "server-only";

import sharp from "sharp";
import { calibratePage, pageLabels, redrawPage, type RedrawnPage } from "../digitize/digitize";
import type { DigitizedPage } from "../digitize/digitize";
import type { DepthLabel } from "../digitize/depths";
import { NULL_VALUE, type Check } from "../digitize/write";
import type { CurveCalibration } from "../digitize/calibration";
import type { Traced } from "../digitize/trace";
import { curveBand } from "./geometry";
import {
  boxToPixels,
  classifyPage,
  readHeading,
  readLegend,
  type HeaderItem,
  type Legend,
  type LineStyle,
  type PageRead,
} from "./read";

/**
 * A scanned log of any number of pages, to one LAS per log.
 *
 * A paper log is a heading, then the curves cut into page-sized sections, with
 * a scale legend at the top and/or bottom; one file often holds several logs
 * (an induction and a density run). No page is dropped: each is classified,
 * and each kind has a job.
 *
 *  - heading: read into the LAS header (~W well lines, ~P parameters). It also
 *    starts a new log: every page after it belongs to that log until the next.
 *  - legend (on a curve page): the curves' real names, units and scales. The
 *    redraw colours curves by line style (solid red, dashed green, dotted blue,
 *    `clean-up-log.md`), and the legend says which line style is which curve,
 *    so the two together name every traced colour.
 *  - curves: the curve grid alone (legends cropped off) through the existing
 *    single-page pipeline, then stitched with the log's other pages by depth.
 *  - other / repeat sections: reported, not stitched into the main pass.
 */

export type PageOutcome = {
  page: number;
  kind: PageRead["kind"];
  /** What happened to it, for the user: "Heading read", "Digitized 3,889-4,109 ft", ... */
  outcome: string;
  ok: boolean;
};

export type LogResult = {
  title: string;
  fileName: string;
  las: string;
  pages: number[];
  topDepth: number;
  bottomDepth: number;
  curves: string[];
  checks: Check[];
};

export type MultipageResult = {
  logs: LogResult[];
  pages: PageOutcome[];
  costUsd: number;
};

/** Pages digitized at once. Each is two Gemini calls; the redraw is the slow one. */
const CONCURRENCY = 4;

/** A label further than this from the log's scale line is reported. */
const LABEL_TOLERANCE_FT = 2;

/** Least-squares feet per pixel through a page's labels. */
function slopeOf(labels: DepthLabel[]): number {
  const n = labels.length;
  const my = labels.reduce((s, l) => s + l.y, 0) / n;
  const mv = labels.reduce((s, l) => s + l.value, 0) / n;
  const num = labels.reduce((s, l) => s + (l.y - my) * (l.value - mv), 0);
  const den = labels.reduce((s, l) => s + (l.y - my) ** 2, 0);
  return den === 0 ? NaN : num / den;
}

function mean(xs: number[]) {
  return xs.reduce((s, x) => s + x, 0) / xs.length;
}

/** Offsets within the label tolerance are one answer. */
function dedupe(xs: number[]) {
  return xs.filter((x, i) => xs.findIndex((y) => Math.abs(y - x) <= LABEL_TOLERANCE_FT) === i);
}

function round2(n: number) {
  return Math.round(n * 100) / 100;
}

const LINE_TO_PALETTE: Record<LineStyle, number> = { solid: 0, dashed: 1, dotted: 2 };

async function pool<T, R>(items: T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const out = new Array<R>(items.length);
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(limit, items.length) }, async () => {
      while (next < items.length) {
        const i = next++;
        out[i] = await fn(items[i]);
      }
    })
  );
  return out;
}

async function crop(png: Buffer, box: [number, number, number, number]): Promise<Buffer> {
  const { width = 0, height = 0 } = await sharp(png).metadata();
  return sharp(png).extract(boxToPixels(box, width, height)).png().toBuffer();
}

function feet(n: number): string {
  return Math.round(n).toLocaleString("en-US");
}

/**
 * The legend's tracks onto the trace's. Matched by order, left to right, and
 * only when the counts agree: a guess at which printed track a traced band is
 * would put a resistivity scale on a gamma ray.
 */
function calibrator(legend: Legend | null) {
  return (traced: Traced): CurveCalibration[] | null => {
    if (!legend || legend.tracks.length !== traced.tracks.length) return null;
    return traced.curves.flatMap((curve) => {
      const candidates = legend.tracks[curve.track]?.curves.filter(
        (c) => LINE_TO_PALETTE[c.line] === curve.curve
      ) ?? [];
      // Two curves drawn in the same line style in one track come out of the
      // redraw as one colour; which of them was traced is unknowable.
      if (candidates.length !== 1) return [];
      const match = candidates[0];
      return [
        {
          track: curve.track,
          curve: curve.curve,
          color: curve.color,
          mnemonic: match.mnemonic,
          unit: match.unit,
          min: match.left,
          max: match.right,
          scale: match.scale,
          band: curveBand(traced, traced.tracks[curve.track], match),
        },
      ];
    });
  };
}

/** What a legend says the redraw cannot separate, for the user. */
function legendLimits(legend: Legend | null): string[] {
  if (!legend) return [];
  return legend.tracks.flatMap((track, t) => {
    const byLine = new Map<LineStyle, string[]>();
    for (const c of track.curves) byLine.set(c.line, [...(byLine.get(c.line) ?? []), c.mnemonic]);
    return [...byLine.entries()]
      .filter(([, names]) => names.length > 1)
      .map(([line, names]) => `${names.join(" and ")} are both ${line} in track ${t + 1}, so they cannot be told apart and are left out`);
  });
}

type Group = {
  heading: number | null;
  title: string | null;
  pages: number[];
};

/** A heading starts a log; pages before the first heading form one of their own. */
function groupPages(reads: PageRead[]): Group[] {
  const groups: Group[] = [];
  reads.forEach((read, index) => {
    if (read.kind === "heading") {
      groups.push({ heading: index, title: read.title, pages: [] });
      return;
    }
    if (groups.length === 0) groups.push({ heading: null, title: null, pages: [] });
    groups[groups.length - 1].pages.push(index);
  });
  return groups;
}

export async function digitizePages(pngs: Buffer[], fileName: string): Promise<MultipageResult> {
  let costUsd = 0;
  const outcomes: PageOutcome[] = [];

  // 1. What every page is. All at once: they are independent and cheap.
  const reads = await Promise.all(
    pngs.map(async (png, index) => {
      try {
        const { read, usage } = await classifyPage(png);
        costUsd += usage.costUsd;
        return read;
      } catch (err) {
        outcomes[index] = {
          page: index + 1,
          kind: "other",
          outcome: `Could not tell what this page is: ${err instanceof Error ? err.message : err}`,
          ok: false,
        };
        return { kind: "other", title: null, curveArea: null, legendAreas: [], repeat: false, note: "" } as PageRead;
      }
    })
  );

  const groups = groupPages(reads);
  const base = fileName.replace(/\.[^.]+$/, "");
  const logs: LogResult[] = [];

  for (const [groupIndex, group] of groups.entries()) {
    // 2. The heading, and the legend from whichever pages print one.
    const headerItems: HeaderItem[] = [];
    if (group.heading !== null) {
      try {
        const { items, usage } = await readHeading(pngs[group.heading]);
        costUsd += usage.costUsd;
        headerItems.push(...items);
        outcomes[group.heading] = {
          page: group.heading + 1,
          kind: "heading",
          outcome: `Heading read: ${items.length} header fields`,
          ok: true,
        };
      } catch (err) {
        outcomes[group.heading] = {
          page: group.heading + 1,
          kind: "heading",
          outcome: `Heading could not be read: ${err instanceof Error ? err.message : err}`,
          ok: false,
        };
      }
    }

    const legendCrops = await Promise.all(
      group.pages.flatMap((p) => reads[p].legendAreas.map((box) => crop(pngs[p], box)))
    );
    let legend: Legend | null = null;
    if (legendCrops.length > 0) {
      try {
        const read = await readLegend(legendCrops);
        costUsd += read.usage.costUsd;
        legend = read.legend;
      } catch {
        legend = null;
      }
    }

    // 3. Every curve page through the single-page pipeline: redraw and trace
    // first (the slow, paid half), then depths and names.
    const curvePages = group.pages.filter((p) => reads[p].kind === "curves");
    const failed = (p: number, err: unknown) => {
      outcomes[p] = {
        page: p + 1,
        kind: "curves",
        outcome: `Could not digitize: ${err instanceof Error ? err.message : err}`,
        ok: false,
      };
    };
    const redrawn = await pool(curvePages, CONCURRENCY, async (p) => {
      try {
        const read = reads[p];
        const png = read.curveArea ? await crop(pngs[p], read.curveArea) : pngs[p];
        return { p, page: await redrawPage(png, `${fileName} page ${p + 1}`) };
      } catch (err) {
        failed(p, err);
        return null;
      }
    });
    const ready = redrawn.filter((r): r is { p: number; page: RedrawnPage } => r !== null);
    const calibrate = calibrator(legend);

    // Depth. Every page of one scan shares one depth scale, so it is measured
    // once per log (the median of what each page with two or more labels
    // implies) and each page fits only its offset, as the median over its
    // labels. A misread label then cannot tilt a page, and a page that shows a
    // single label (the short last section above a legend) still places.
    const labelled = await pool(ready, CONCURRENCY, async ({ p, page }) => {
      try {
        const { labels, usage } = await pageLabels(page);
        return { p, page, labels, usage };
      } catch (err) {
        failed(p, err);
        return null;
      }
    });
    const withLabels = labelled.filter((l): l is NonNullable<typeof l> => l !== null);
    const slopes = withLabels.flatMap(({ labels }) => (labels.length >= 2 ? [slopeOf(labels)] : []))
      .filter((m) => Number.isFinite(m) && m > 0)
      .sort((a, b) => a - b);
    const scale = slopes.length > 0 ? slopes[slopes.length >> 1] : null;

    // Each label implies an offset for its page; the offset most labels agree
    // on wins. A tie (two labels, two answers: one misread) is broken by page
    // order, since a page's depth must fall between its neighbours' in the file.
    const placed = withLabels.map(({ p, page, labels, usage }) => {
      if (scale === null) return { p, page, labels, usage, candidates: [] as number[] };
      const offsets = labels.map((l) => l.value - scale * l.y);
      const support = offsets.map((o) => offsets.filter((q) => Math.abs(q - o) <= LABEL_TOLERANCE_FT).length);
      const most = Math.max(...support);
      const candidates = dedupe(
        offsets
          .filter((_, i) => support[i] === most)
          .map((o) => mean(offsets.filter((q) => Math.abs(q - o) <= LABEL_TOLERANCE_FT)))
      );
      return { p, page, labels, usage, candidates };
    });
    const tops = new Map<number, number>();
    for (const x of placed) if (x.candidates.length === 1) tops.set(x.p, x.candidates[0]);
    for (const x of placed) {
      if (x.candidates.length < 2) continue;
      const before = [...tops.entries()].filter(([q]) => q < x.p).sort((a, b) => b[0] - a[0])[0]?.[1];
      const after = [...tops.entries()].filter(([q]) => q > x.p).sort((a, b) => a[0] - b[0])[0]?.[1];
      const fits = x.candidates.filter(
        (c) => (before === undefined || c > before) && (after === undefined || c < after)
      );
      if (fits.length === 1) tops.set(x.p, fits[0]);
    }

    const digitized = placed.flatMap(({ p, page, labels, usage, candidates }) => {
      const top = tops.get(p);
      if (scale === null || top === undefined) {
        failed(
          p,
          new Error(
            scale === null
              ? "No page of this log shows two depth labels, so its depth scale is unknown"
              : `Its depth labels disagree (${labels.map((l) => feet(l.value)).join(", ")}) and page order cannot settle which is right`
          )
        );
        return [];
      }
      const worst = Math.max(...labels.map((l) => Math.abs(l.value - (top + scale * l.y))));
      const done = calibratePage(
        page,
        calibrate,
        {
          topDepth: round2(top),
          bottomDepth: round2(top + scale * (page.sourceHeight - 1)),
          labels,
        },
        [usage],
        legend !== null
      );
      costUsd += done.costUsd;
      if (worst > LABEL_TOLERANCE_FT) {
        done.checks.push({
          name: "Depth labels agree with the log's scale",
          ok: false,
          detail: `${candidates.length > 1 ? "placed by page order; " : ""}a label is ${worst.toFixed(1)} ft off (misread, or not a depth)`,
        });
      }
      return [{ p, page: done }];
    });

    for (const p of group.pages) {
      if (outcomes[p]) continue;
      if (reads[p].kind !== "curves") {
        const legendOnly = reads[p].legendAreas.length > 0;
        outcomes[p] = {
          page: p + 1,
          kind: reads[p].kind,
          outcome: legendOnly ? "Scale legend read" : reads[p].note || "Not a curve page",
          ok: true,
        };
      }
    }

    const done = digitized.filter((d): d is { p: number; page: DigitizedPage } => d !== null);
    for (const { p, page } of done) {
      const extras = [
        reads[p].legendAreas.length > 0 ? "scale legend read" : null,
        reads[p].repeat ? "repeat section left out" : null,
        page.uncalibrated.length > 0 ? `${page.uncalibrated.length} curve(s) not matched to the legend` : null,
      ].filter(Boolean);
      outcomes[p] = {
        page: p + 1,
        kind: "curves",
        outcome: `Digitized ${feet(page.topDepth)}-${feet(page.bottomDepth)} ft${extras.length ? ` (${extras.join(", ")})` : ""}`,
        ok: page.uncalibrated.length === 0,
      };
    }
    if (done.length === 0) continue;

    // 4. One LAS for the log.
    const title = group.title ?? (groups.length > 1 ? `Log ${groupIndex + 1}` : base);
    const limits = legendLimits(legend);
    const noLegend = legend === null;
    const log = stitch({
        title,
        fileName: groups.length > 1 ? `${base} - ${title}.las` : `${base}.las`,
        source: fileName,
        header: headerItems,
        pages: done,
      });
    log.checks.push(
      ...limits.map((detail) => ({ name: "Curves the legend names but the digitizer cannot separate", ok: false, detail })),
      ...(noLegend
        ? [{ name: "Scale legend found", ok: false, detail: "no legend was found, so curve names and scales are standard guesses" }]
        : [])
    );
    logs.push(log);
  }

  pngs.forEach((_, i) => {
    outcomes[i] ??= { page: i + 1, kind: reads[i].kind, outcome: reads[i].note || "Not a curve page", ok: true };
  });

  return { logs, pages: outcomes, costUsd };
}

// ------------------------------------------------------------------ stitching

const DEPTH_DECIMALS = 4;
/** Two readings of one curve over the same depths should track each other closely. */
const MIN_OVERLAP_CORRELATION = 0.8;
/** Fewer common samples than this is too short an overlap to judge. */
const MIN_OVERLAP_SAMPLES = 40;

/** Value of a page's curve at a depth, by linear interpolation between its rows. */
function valueAtDepth(page: DigitizedPage, column: number, depth: number): number | null {
  const { depths, values } = page.sampled;
  if (depth < depths[0] || depth > depths[depths.length - 1]) return null;
  let lo = 0;
  let hi = depths.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (depths[mid] <= depth) lo = mid;
    else hi = mid;
  }
  const a = values[column][lo];
  const b = values[column][hi];
  if (a === null || b === null) return null;
  const t = depths[hi] === depths[lo] ? 0 : (depth - depths[lo]) / (depths[hi] - depths[lo]);
  return a + (b - a) * t;
}

/** Pearson correlation of one curve on two pages over their shared depths, or null if too short. */
function overlapCorrelation(a: DigitizedPage, b: DigitizedPage, mnemonic: string): number | null {
  const ca = a.sampled.curves.findIndex((c) => c.mnemonic === mnemonic);
  const cb = b.sampled.curves.findIndex((c) => c.mnemonic === mnemonic);
  if (ca === -1 || cb === -1) return null;
  const from = Math.max(a.sampled.depths[0], b.sampled.depths[0]);
  const to = Math.min(a.sampled.depths[a.sampled.depths.length - 1], b.sampled.depths[b.sampled.depths.length - 1]);
  const xs: number[] = [];
  const ys: number[] = [];
  for (const depth of b.sampled.depths) {
    if (depth < from || depth > to) continue;
    const x = valueAtDepth(a, ca, depth);
    const y = valueAtDepth(b, cb, depth);
    if (x === null || y === null) continue;
    xs.push(x);
    ys.push(y);
  }
  if (xs.length < MIN_OVERLAP_SAMPLES) return null;
  const mx = xs.reduce((s, x) => s + x, 0) / xs.length;
  const my = ys.reduce((s, y) => s + y, 0) / ys.length;
  let num = 0;
  let dx = 0;
  let dy = 0;
  for (let i = 0; i < xs.length; i++) {
    num += (xs[i] - mx) * (ys[i] - my);
    dx += (xs[i] - mx) ** 2;
    dy += (ys[i] - my) ** 2;
  }
  return dx === 0 || dy === 0 ? null : num / Math.sqrt(dx * dy);
}
const VALUE_DECIMALS = 4;

function lasLine(mnemonic: string, unit: string, value: string, description: string) {
  return ` ${mnemonic}.${unit} ${value} : ${description}`;
}

/**
 * Pages in depth order, each contributing the rows below where the previous
 * page ended (a scan of a continuous log overlaps at the page breaks; the
 * earlier page keeps the overlap). One row per traced pixel row, never
 * resampled, so the step is not constant across page breaks: STEP is 0, which
 * LAS 2.0 defines as "variable".
 */
function stitch(input: {
  title: string;
  fileName: string;
  source: string;
  header: HeaderItem[];
  pages: { p: number; page: DigitizedPage }[];
}): LogResult {
  const pages = [...input.pages].sort((a, b) => a.page.topDepth - b.page.topDepth);

  // Every curve any page found, in first-seen order, keyed by mnemonic.
  const curves: CurveCalibration[] = [];
  for (const { page } of pages) {
    for (const curve of page.sampled.curves) {
      if (!curves.some((c) => c.mnemonic === curve.mnemonic)) curves.push(curve);
    }
  }

  const rows: { depth: number; values: (number | null)[] }[] = [];
  let overlapFt = 0;
  const gaps: string[] = [];
  let lastDepth = -Infinity;

  for (const { page } of pages) {
    const { depths, values, curves: pageCurves } = page.sampled;
    const columns = curves.map((curve) => pageCurves.findIndex((c) => c.mnemonic === curve.mnemonic));
    if (Number.isFinite(lastDepth)) {
      const first = depths[0];
      if (first > lastDepth + 1) gaps.push(`${feet(lastDepth)}-${feet(first)} ft`);
      if (first <= lastDepth) overlapFt += lastDepth - first;
    }
    depths.forEach((depth, row) => {
      if (depth <= lastDepth) return;
      rows.push({
        depth,
        values: columns.map((col) => (col === -1 ? null : values[col][row])),
      });
    });
    lastDepth = Math.max(lastDepth, depths[depths.length - 1]);
  }

  const top = rows[0]?.depth ?? 0;
  const bottom = rows[rows.length - 1]?.depth ?? 0;
  const well = input.header.filter((h) => h.section === "well" && !["STRT", "STOP", "STEP", "NULL"].includes(h.mnemonic));
  const params = input.header.filter((h) => h.section === "parameter");

  const lines = [
    "~VERSION INFORMATION",
    lasLine("VERS", "", "2.0", "CWLS LOG ASCII STANDARD - VERSION 2.0"),
    lasLine("WRAP", "", "NO", "ONE LINE PER DEPTH STEP"),
    "~WELL INFORMATION",
    lasLine("STRT", "F", top.toFixed(DEPTH_DECIMALS), "START DEPTH"),
    lasLine("STOP", "F", bottom.toFixed(DEPTH_DECIMALS), "STOP DEPTH"),
    lasLine("STEP", "F", "0", "VARIABLE: ONE ROW PER SCANNED PIXEL ROW"),
    lasLine("NULL", "", String(NULL_VALUE), "NULL VALUE"),
    ...well.map((h) => lasLine(h.mnemonic, h.unit, h.value, h.description)),
    "~CURVE INFORMATION",
    lasLine("DEPT", "F", "", "DEPTH"),
    ...curves.map((c) => lasLine(c.mnemonic, c.unit, "", `TRACK ${c.track + 1} ${c.scale.toUpperCase()} ${c.min}-${c.max}`)),
    "~PARAMETER INFORMATION",
    ...params.map((h) => lasLine(h.mnemonic, h.unit, h.value, h.description)),
    lasLine("SRCF", "", input.source, "DIGITIZED FROM"),
    lasLine("SRCP", "", pages.map(({ p }) => p + 1).join(","), "SOURCE PAGES"),
    "~ASCII",
    ...rows.map((r) =>
      [r.depth.toFixed(DEPTH_DECIMALS), ...r.values.map((v) => (v === null ? String(NULL_VALUE) : v.toFixed(VALUE_DECIMALS)))].join(" ")
    ),
  ];

  // Neighbouring pages overlap: the same curve read off both must agree there.
  // A disagreement means one page's redraw swapped or lost a curve, which
  // nothing else in the pipeline can see.
  const overlapChecks: Check[] = [];
  for (let i = 1; i < pages.length; i++) {
    const a = pages[i - 1];
    const b = pages[i];
    for (const curve of curves) {
      const r = overlapCorrelation(a.page, b.page, curve.mnemonic);
      if (r === null) continue;
      overlapChecks.push({
        name: `Pages ${a.p + 1} and ${b.p + 1} agree on ${curve.mnemonic} where they overlap`,
        ok: r >= MIN_OVERLAP_CORRELATION,
        detail: `correlation ${r.toFixed(2)}`,
      });
    }
  }

  const pageChecks = pages.flatMap(({ p, page }) =>
    page.checks.filter((c) => !c.ok).map((c) => ({ ...c, name: `Page ${p + 1}: ${c.name}` }))
  );
  const checks: Check[] = [
    {
      name: "Depth increases down the log",
      ok: rows.every((r, i) => i === 0 || r.depth > rows[i - 1].depth),
      detail: `${rows.length} rows, ${feet(top)}-${feet(bottom)} ft`,
    },
    {
      name: "Pages join without gaps",
      ok: gaps.length === 0,
      detail: gaps.length ? `missing ${gaps.join(", ")}` : `overlap of ${overlapFt.toFixed(1)} ft trimmed`,
    },
    ...overlapChecks,
    ...pageChecks,
  ];

  return {
    title: input.title,
    fileName: input.fileName,
    las: `${lines.join("\n")}\n`,
    pages: pages.map(({ p }) => p + 1),
    topDepth: top,
    bottomDepth: bottom,
    curves: curves.map((c) => c.mnemonic),
    checks,
  };
}

