import "server-only";

import { readFile } from "node:fs/promises";
import path from "node:path";
import {
  IMAGE_MODEL,
  VISION_MODEL,
  generate,
  imageOf,
  usageOf,
  type GeminiUsage,
  type GeneratedImage,
} from "../../ai/gemini";

export type { GeminiUsage };

/**
 * The two Gemini calls behind digitizing a raster log: the image model that
 * redraws the scan as a traceable figure, and the text model that reads
 * pictures and answers in JSON (the depth labels). The client, models and
 * rates are shared with Orion in `@/lib/ai/gemini`.
 */

const PROMPT_PATH = path.join(
  process.cwd(),
  "src/lib/raster-log/digitize/clean-up-log.md"
);

export type CleanedLog = GeneratedImage;

/** Sends the scan (as PNG) and clean-up-log.md to Gemini, returns its image. */
export async function cleanLogImage(png: Buffer): Promise<CleanedLog> {
  const prompt = await readFile(PROMPT_PATH, "utf8");
  const body = await generate(
    IMAGE_MODEL,
    [{ text: prompt }, { inline_data: { mime_type: "image/png", data: png.toString("base64") } }],
    { responseModalities: ["TEXT", "IMAGE"] }
  );
  return imageOf(body);
}

/** Asks Gemini about one or more images and parses the JSON it replies with. */
export async function askGeminiJson<T>(
  image: Buffer | Buffer[],
  prompt: string
): Promise<{ value: T | null; usage: GeminiUsage }> {
  const images = Array.isArray(image) ? image : [image];
  const body = await generate(
    VISION_MODEL,
    [
      { text: prompt },
      ...images.map((data) => ({
        inline_data: { mime_type: "image/png", data: data.toString("base64") },
      })),
    ],
    { responseMimeType: "application/json" }
  );
  const usage = usageOf(VISION_MODEL, body);
  const text = body.candidates?.[0]?.content?.parts
    ?.map((part) => part.text ?? "")
    .join("")
    .trim();
  if (!text) return { value: null, usage };
  try {
    return { value: JSON.parse(text) as T, usage };
  } catch {
    return { value: null, usage };
  }
}
