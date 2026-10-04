import "server-only";

import sharp from "sharp";
import { heicToJpeg } from "./heic-server";

/**
 * Any uploaded log, as page images `digitizeScan` can read.
 *
 * `digitizeScan` hands the bytes to sharp, which reads TIFF (every page), PNG,
 * JPEG, WebP, GIF, AVIF and SVG. Those pass through untouched, so the digitizer
 * sees the original scan. The rest are converted here, invisibly:
 *
 *  - HEIC/HEIF (phone photos of a paper log): sharp's prebuilt libvips reads
 *    AVIF but not HEVC, so `heic-convert`, as Wildcat does.
 *  - PDF: MuPDF, every page, each at its scan's own resolution.
 *  - Raster formats sharp lacks (BMP, JPEG 2000, PNM, PSD): MuPDF decodes
 *    them at their own pixel size, never resampled.
 *
 * Anything else is refused by its bytes, not its name. MuPDF would happily
 * typeset a .txt or .html as a page, and a picture of prose sent to the
 * digitizer is a wasted Gemini call that returns a nonsense LAS.
 */

/** A scanned log page at 200 dpi keeps 0.5 ft depth ticks several pixels apart. */
const PDF_DPI = 200;

/** Long logs are tall: cap the render so a 30-foot PDF page cannot exhaust memory. */
const MAX_RENDER_PIXELS = 200_000_000;

export class UnreadableLog extends Error {}

function isHeic(bytes: Buffer): boolean {
  // ISO-BMFF `ftyp` box with a HEVC-image brand. AVIF shares the box and is
  // left to sharp, which reads it.
  if (bytes.length < 12 || bytes.toString("latin1", 4, 8) !== "ftyp") return false;
  const brand = bytes.toString("latin1", 8, 12);
  return ["heic", "heix", "hevc", "hevx", "heim", "heis", "mif1", "msf1"].includes(brand);
}

function isPdf(bytes: Buffer): boolean {
  // Some writers put junk before the header; the spec allows it in the first 1 KB.
  return bytes.subarray(0, 1024).includes("%PDF-");
}

/** Raster signatures MuPDF decodes and sharp does not. */
function isOtherRaster(bytes: Buffer): boolean {
  const head = bytes.toString("latin1", 0, 12);
  return (
    head.startsWith("BM") || // BMP
    head.startsWith("8BPS") || // Photoshop
    /^P[1-7]\s/.test(head) || // PNM / PAM
    bytes.subarray(0, 4).equals(Buffer.from([0xff, 0x4f, 0xff, 0x51])) || // JPEG 2000 codestream
    head.slice(4, 8) === "jP  " // JPEG 2000 (JP2)
  );
}

async function sharpReads(bytes: Buffer): Promise<boolean> {
  try {
    const { width, height } = await sharp(bytes, { page: 0 }).metadata();
    return Boolean(width && height);
  } catch {
    return false;
  }
}

async function decodeRaster(bytes: Buffer): Promise<Buffer> {
  const mupdf = await import("mupdf");
  const image = new mupdf.Image(bytes);
  try {
    return Buffer.from(image.toPixmap().asPNG());
  } finally {
    image.destroy();
  }
}

type MupdfModule = typeof import("mupdf");
type MupdfPage = ReturnType<InstanceType<MupdfModule["Document"]>["loadPage"]>;

/**
 * One PDF page as PNG. A scanned PDF is one image per page: render at that
 * image's own resolution, so the digitizer sees the scan's pixels rather than a
 * resample. A page that is not one big image (vector, or text and figures)
 * renders at PDF_DPI. Capped so a very long page stays in memory.
 */
function renderPdfPage(mupdf: MupdfModule, page: MupdfPage): Buffer {
  const [x0, y0, x1, y1] = page.getBounds();
  const widthPt = x1 - x0;
  const heightPt = y1 - y0;
  let zoom = PDF_DPI / 72;
  let scan: { width: number; bboxWidth: number } | null = null;
  page.toStructuredText("preserve-images").walk({
    onImageBlock(bbox, _transform, image) {
      const bboxWidth = bbox[2] - bbox[0];
      if (bboxWidth > 0 && (!scan || bboxWidth > scan.bboxWidth)) {
        scan = { width: image.getWidth(), bboxWidth };
      }
    },
  });
  const largest = scan as { width: number; bboxWidth: number } | null;
  if (largest && largest.bboxWidth >= 0.8 * widthPt) zoom = largest.width / largest.bboxWidth;
  const pixels = widthPt * heightPt * zoom * zoom;
  if (pixels > MAX_RENDER_PIXELS) zoom *= Math.sqrt(MAX_RENDER_PIXELS / pixels);
  const pixmap = page.toPixmap(
    mupdf.Matrix.scale(zoom, zoom),
    mupdf.ColorSpace.DeviceRGB,
    false,
    true
  );
  return Buffer.from(pixmap.asPNG());
}

async function renderPdfPages(bytes: Buffer): Promise<Buffer[]> {
  const mupdf = await import("mupdf");
  let doc;
  try {
    doc = mupdf.Document.openDocument(bytes, "application/pdf");
  } catch {
    throw new UnreadableLog("This PDF couldn't be opened. It may be damaged or password-protected.");
  }
  try {
    const count = doc.countPages();
    if (count < 1) throw new UnreadableLog("This document has no pages.");
    const pages: Buffer[] = [];
    for (let i = 0; i < count; i++) pages.push(renderPdfPage(mupdf, doc.loadPage(i)));
    return pages;
  } finally {
    doc.destroy();
  }
}

/** Every page of a multi-page TIFF (or animated GIF/WebP) as PNG; one-page images as they are. */
async function rasterPages(bytes: Buffer): Promise<Buffer[]> {
  const { pages = 1 } = await sharp(bytes, { page: 0 }).metadata();
  if (pages <= 1) return [bytes];
  return Promise.all(
    Array.from({ length: pages }, (_, page) => sharp(bytes, { page }).png().toBuffer())
  );
}

/**
 * Every page of an uploaded log, in order, as bytes `digitizeScan` can read.
 * A log is routinely several pages: a heading, the curve sections, a legend.
 * Deciding what each one is happens later (`multipage/`); this only gets them
 * out of their container without dropping any.
 */
export async function toPages(bytes: Buffer, name: string): Promise<Buffer[]> {
  if (isHeic(bytes)) return [await heicToJpeg(bytes)];
  if (await sharpReads(bytes)) return rasterPages(bytes);
  if (isPdf(bytes)) return renderPdfPages(bytes);
  if (isOtherRaster(bytes)) {
    try {
      return [await decodeRaster(bytes)];
    } catch {
      throw new UnreadableLog(`${name} couldn't be decoded. It may be damaged.`);
    }
  }
  throw new UnreadableLog(`${name} isn't an image or PDF, so there is no log to digitize.`);
}
