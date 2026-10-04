import "server-only";

/**
 * HEIC/HEIF → JPEG bytes via `heic-convert` (pure JS + libheif wasm, so it needs
 * no native binary and runs on serverless, unlike the `soffice` fallback).
 *
 * Quality 0.92: an OCR target, so visible compression artifacts around small
 * digits are the failure mode to avoid — a run ticket's net-barrels figure has to
 * survive the transcode. Loaded lazily to keep it off the cold-start path for the
 * uploads that aren't HEIC.
 */
export async function heicToJpeg(buf: Buffer): Promise<Buffer> {
  const spec = "heic-convert";
  const mod = (await import(spec as string)) as {
    default: (opts: {
      buffer: Buffer;
      format: "JPEG" | "PNG";
      quality?: number;
    }) => Promise<ArrayBuffer>;
  };
  const out = await mod.default({ buffer: buf, format: "JPEG", quality: 0.92 });
  return Buffer.from(out);
}
