import "server-only";

import sharp from "sharp";
import { askGeminiJson } from "../digitize/gemini";
import type { GeminiUsage } from "../../ai/gemini";

/**
 * The three things a model reads off a log's pages before any curve is traced:
 * what each page IS, what the heading SAYS, and what the scale legend MEANS.
 * Geometry it returns is in Gemini's box convention, [ymin, xmin, ymax, xmax]
 * normalised to 0-1000, and is converted to pixels by the caller.
 */

export type Box = [number, number, number, number];

export type PageKind = "heading" | "curves" | "other";

export type PageRead = {
  kind: PageKind;
  /** Heading pages: the log's title as printed ("DUAL INDUCTION FOCUSED LOG"). */
  title: string | null;
  /** Curve pages: the depth-indexed curve grid alone. */
  curveArea: Box | null;
  /** Scale legends / track headers anywhere on the page. */
  legendAreas: Box[];
  /** A repeat-section pass on this page, which is not stitched into the main log. */
  repeat: boolean;
  /** What the page is, in a few words, for the user. */
  note: string;
};

/** Sent at this size: enough to see a page's layout, a fraction of the full scan's tokens. */
const OVERVIEW_EDGE = 1600;

async function overview(png: Buffer): Promise<Buffer> {
  return sharp(png).resize({ width: OVERVIEW_EDGE, height: OVERVIEW_EDGE, fit: "inside" }).png().toBuffer();
}

const CLASSIFY_PROMPT = `This is one page of a scanned well log (a wireline log printed on paper and scanned). Say what the page is.

Kinds:
- "heading": the log's front page. Company, well, field, county, location, elevations, the logging company, the log's title. It has no curves.
- "curves": the page carries depth-indexed curves on a grid, with depth numbers in a column.
- "other": anything else (calibration records, a blank page, notes, an insert).

For a "curves" page also give:
- "curveArea": a box around the curve grid ONLY, from the first depth row to the last, spanning every track and the depth column. Exclude any scale legend / track header boxes (the boxes naming each curve with its scale values), the log's title block, and any repeat section.
- "legendAreas": a box around each scale legend / track header block on the page (the blocks naming the curves with their scale end values and a sample of each curve's line style). An empty list if there are none.
- "repeat": true if the page holds a repeat section (a short second pass over an interval, usually labelled REPEAT), else false.

Boxes are [ymin, xmin, ymax, xmax] normalised to 0-1000.

Reply with JSON only:
{"kind": "...", "title": string or null (the heading's printed log title, e.g. "DUAL INDUCTION FOCUSED LOG"), "curveArea": box or null, "legendAreas": [box, ...], "repeat": boolean, "note": "a few words describing the page"}`;

export async function classifyPage(png: Buffer): Promise<{ read: PageRead; usage: GeminiUsage }> {
  const { value, usage } = await askGeminiJson<Partial<PageRead>>(await overview(png), CLASSIFY_PROMPT);
  if (!value || typeof value !== "object") throw new Error("Unexpected reply classifying a page");
  const kind: PageKind = value.kind === "heading" || value.kind === "curves" ? value.kind : "other";
  return {
    read: {
      kind,
      // Printed titles break across lines ("DUAL\nINDUCTION\nFOCUSED\nLOG").
      title:
        typeof value.title === "string" && value.title.trim()
          ? value.title.replace(/\s+/g, " ").trim()
          : null,
      curveArea: isBox(value.curveArea) ? value.curveArea : null,
      legendAreas: Array.isArray(value.legendAreas) ? value.legendAreas.filter(isBox) : [],
      repeat: value.repeat === true,
      note: typeof value.note === "string" ? value.note : "",
    },
    usage,
  };
}

function isBox(value: unknown): value is Box {
  return (
    Array.isArray(value) &&
    value.length === 4 &&
    value.every((n) => typeof n === "number" && Number.isFinite(n)) &&
    value[2] > value[0] &&
    value[3] > value[1]
  );
}

/** A box in pixels, clamped to the image, for sharp's extract. */
export function boxToPixels(box: Box, width: number, height: number) {
  const top = Math.max(0, Math.floor((box[0] / 1000) * height));
  const left = Math.max(0, Math.floor((box[1] / 1000) * width));
  const bottom = Math.min(height, Math.ceil((box[2] / 1000) * height));
  const right = Math.min(width, Math.ceil((box[3] / 1000) * width));
  return { top, left, width: right - left, height: bottom - top };
}

// ------------------------------------------------------------------ heading

/** One LAS header line read off the heading. */
export type HeaderItem = {
  section: "well" | "parameter";
  mnemonic: string;
  unit: string;
  value: string;
  description: string;
};

const HEADING_PROMPT = `This is the heading (front page) of a scanned well log. Transcribe everything printed on it into LAS 2.0 header lines.

Use the standard LAS 2.0 mnemonic for each field where one exists:
- Well section ("well"): COMP company, WELL well name, FLD field, LOC location (whole location text on one line), CNTY county, STAT state, CTRY country, SRVC logging company, DATE log date, API API number, UWI unique well id.
- Parameter section ("parameter"): LOG log title, RUN run number, EKB / EDF / EGL elevations (kelly bushing, derrick floor, ground level), PDAT permanent datum, EPD elevation of permanent datum, APD height of the log zero above the permanent datum, LMF log measured from, DMF drilling measured from, TDD total depth driller, TDL total depth logger, BLI bottom logged interval, TLI top logged interval, BS bit size, CSGS casing size, CSGD casing driller, CSGL casing logger, MUD mud type, MUDD mud density, MUDV mud viscosity, PH mud pH, FL fluid loss, RM mud resistivity, RMT its temperature, RMF mud filtrate resistivity, RMFT its temperature, RMC mud cake resistivity, RMCT its temperature, BHT bottom hole temperature, ENG recorded by, WIT witnessed by.
- Anything printed that has no standard mnemonic: invent a short uppercase one (at most 4 characters) and put it in "parameter".

Rules:
- Copy values exactly as printed. Do not convert units, do not correct spelling, do not fill in anything that is not printed. Leave out fields that are blank on the page.
- "unit": the unit the value is in, as LAS writes it (F for feet, IN for inches, OHMM, DEGF, LB/G), or "" when there is none.
- "description": the field's label as printed, in capitals.

Reply with JSON only: [{"section": "well" | "parameter", "mnemonic": "...", "unit": "...", "value": "...", "description": "..."}, ...]`;

/** The heading read at a size where small print stays legible. */
const HEADING_EDGE = 2400;

export async function readHeading(png: Buffer): Promise<{ items: HeaderItem[]; usage: GeminiUsage }> {
  const image = await sharp(png)
    .resize({ width: HEADING_EDGE, height: HEADING_EDGE, fit: "inside", withoutEnlargement: true })
    .png()
    .toBuffer();
  const { value, usage } = await askGeminiJson<HeaderItem[]>(image, HEADING_PROMPT);
  const items = (Array.isArray(value) ? value : []).filter(
    (item): item is HeaderItem =>
      !!item &&
      (item.section === "well" || item.section === "parameter") &&
      typeof item.mnemonic === "string" &&
      /^[A-Z0-9_]{1,8}$/i.test(item.mnemonic.trim()) &&
      typeof item.value === "string" &&
      item.value.trim() !== ""
  );
  return {
    items: items.map((item) => ({
      section: item.section,
      mnemonic: item.mnemonic.trim().toUpperCase(),
      unit: typeof item.unit === "string" ? item.unit.trim().toUpperCase() : "",
      value: item.value.trim(),
      description: typeof item.description === "string" ? item.description.trim().toUpperCase() : "",
    })),
    usage,
  };
}

// ------------------------------------------------------------------- legend

export type LineStyle = "solid" | "dashed" | "dotted";

export type LegendCurve = {
  name: string;
  mnemonic: string;
  unit: string;
  left: number;
  right: number;
  scale: "linear" | "log";
  line: LineStyle;
  /** The share of the track's width the scale runs across, [from, to] in 0-1. */
  span: [number, number];
};

export type Legend = { tracks: { curves: LegendCurve[] }[] };

const LEGEND_PROMPT = `These images are the scale legend (track header) of one scanned well log: the boxes that name each curve, print its scale, and show a sample of its line.

Describe every curve, track by track, left to right. The depth column is not a track. Where one logarithmic grid runs continuously across what look like two tracks, it is ONE track.

For each curve:
- "name": as printed (e.g. "DEEP INDUCTION").
- "mnemonic": its standard LAS mnemonic (e.g. GR, SP, CALI, ILD, ILM, SFL, LLD, LLS, MSFL, RHOB, DRHO, NPHI, DPHI, PE, MINV, MNOR, DT).
- "unit": its LAS unit (GAPI, MV, IN, OHMM, G/C3, V/V, US/F).
- "left" and "right": the PRIMARY scale's values at the track's left and right edges. A curve often prints several scale lines (backup scales for when the curve wraps); the primary is the one printed directly beside that curve's line-style sample. If the right end value is cut off or not printed on a logarithmic scale, set "right" to null and give "decades".
- "scale": "linear" or "log".
- "decades": for a log scale, how many decades (factor-of-ten cycles) the track spans, counted from the tick marks or grid. null for linear.
- "line": the curve's line style in the sample: "solid", "dashed" (long dashes), or "dotted" (dots or short dashes).
- "span": the part of the track's width this curve's scale runs across, as [from, to] fractions of the track width (0 = left edge, 1 = right edge). Most curves use the whole track, [0, 1]; some use half of it, e.g. [0.5, 1] for a scale printed across the right half only.

Reply with JSON only: {"tracks": [{"curves": [{"name": ..., "mnemonic": ..., "unit": ..., "left": number, "right": number or null, "scale": ..., "decades": number or null, "line": ..., "span": [from, to]}]}]}`;

type RawLegendCurve = Omit<LegendCurve, "right" | "span"> & {
  right: number | null;
  decades?: number | null;
  span?: unknown;
};

export async function readLegend(crops: Buffer[]): Promise<{ legend: Legend | null; usage: GeminiUsage }> {
  const { value, usage } = await askGeminiJson<{ tracks?: { curves?: RawLegendCurve[] }[] }>(
    crops,
    LEGEND_PROMPT
  );
  if (!value || !Array.isArray(value.tracks)) return { legend: null, usage };
  const tracks = value.tracks.map((track) => ({
    curves: (Array.isArray(track?.curves) ? track.curves : []).flatMap((c): LegendCurve[] => {
      if (!c || typeof c.mnemonic !== "string" || typeof c.left !== "number") return [];
      const scale = c.scale === "log" ? "log" : "linear";
      const right =
        typeof c.right === "number"
          ? c.right
          : scale === "log" && typeof c.decades === "number" && c.decades > 0
            ? c.left * 10 ** c.decades
            : null;
      if (right === null || right === c.left) return [];
      if (scale === "log" && (c.left <= 0 || right <= 0)) return [];
      const line: LineStyle = c.line === "dashed" || c.line === "dotted" ? c.line : "solid";
      const span: [number, number] =
        Array.isArray(c.span) &&
        c.span.length === 2 &&
        c.span.every((n) => typeof n === "number" && n >= 0 && n <= 1) &&
        c.span[1] - c.span[0] >= 0.1
          ? [c.span[0], c.span[1]]
          : [0, 1];
      return [
        {
          name: typeof c.name === "string" ? c.name : c.mnemonic,
          mnemonic: c.mnemonic.trim().toUpperCase(),
          unit: typeof c.unit === "string" ? c.unit.trim().toUpperCase() : "",
          left: c.left,
          right,
          scale,
          line,
          span,
        },
      ];
    }),
  }));
  return { legend: { tracks: tracks.filter((t) => t.curves.length > 0) }, usage };
}
