/**
 * HEIC/HEIF: what an iPhone camera saves by default. Client-safe.
 *
 * Uploaded and stored as-is. Only Safari can draw one and no model reads one,
 * so it is converted on the server where it is used: to JPEG for the model
 * (`document-part.ts`, `heic-parts.ts`) and for OCR (`retrieval.ts`), to PNG
 * for the viewer (`/api/files/[id]/png`).
 */

const HEIC_NAME = /\.(heic|heif)$/i;
const HEIC_MIMES = new Set([
  "image/heic",
  "image/heif",
  "image/heic-sequence",
  "image/heif-sequence",
]);

export function isHeicName(name: string): boolean {
  return HEIC_NAME.test(name);
}

export function isHeicFile(file: { name: string; type: string }): boolean {
  return HEIC_MIMES.has(file.type.toLowerCase()) || isHeicName(file.name);
}

/** The JPEG copy's file name: `IMG_0412.HEIC` → `IMG_0412.jpg`. */
export function jpegNameFor(name: string): string {
  return HEIC_NAME.test(name) ? name.replace(HEIC_NAME, ".jpg") : `${name}.jpg`;
}

/** For a picker's `accept`: extensions plus MIME types, since iOS matches on
 * either. */
export const HEIC_ACCEPT = ".heic,.heif,image/heic,image/heif";
