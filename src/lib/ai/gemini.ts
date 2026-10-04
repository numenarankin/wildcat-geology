import "server-only";

import type { AspectRatio } from "./image-blocks";

/**
 * The Gemini client: the image model that draws (the raster-log digitizer's
 * redraw, Orion's generate_image) and the text model that reads pictures and
 * answers in JSON. One place holds the model ids and the per-token rates, so
 * every caller meters an image at the same price. Every call returns its token
 * usage so the caller can meter it.
 */

export const IMAGE_MODEL = "gemini-3-pro-image";
export const VISION_MODEL = "gemini-3.1-pro-preview";
const ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models";

/**
 * Google's paid-tier rates, USD per token. Image output is its own line: a
 * 1K/2K image is a flat 1,120 tokens, so $0.134 apiece. Thinking bills as
 * output on both models.
 */
export const RATES = {
  [IMAGE_MODEL]: { input: 2 / 1e6, output: 12 / 1e6, imageOutput: 120 / 1e6 },
  [VISION_MODEL]: { input: 2 / 1e6, output: 12 / 1e6, imageOutput: 0 },
} as const;

export type GeminiModel = keyof typeof RATES;

export interface GeminiUsage {
  model: string;
  inputTokens: number;
  outputTokens: number;
  /** Output tokens that were image, billed at the image rate. */
  imageOutputTokens: number;
  thoughtTokens: number;
  costUsd: number;
}

type InlineData = { mimeType: string; data: string };

export type GenerateResponse = {
  candidates?: {
    content?: { parts?: { text?: string; inlineData?: InlineData }[] };
    /** Why generation stopped: STOP, IMAGE_SAFETY, PROHIBITED_CONTENT, NO_IMAGE, ... */
    finishReason?: string;
    finishMessage?: string;
  }[];
  /** Set when the PROMPT was refused before any candidate was generated. */
  promptFeedback?: { blockReason?: string; blockReasonMessage?: string };
  usageMetadata?: {
    promptTokenCount?: number;
    candidatesTokenCount?: number;
    thoughtsTokenCount?: number;
    candidatesTokensDetails?: { modality?: string; tokenCount?: number }[];
  };
};

export function usageOf(model: GeminiModel, body: GenerateResponse): GeminiUsage {
  const meta = body.usageMetadata ?? {};
  const input = meta.promptTokenCount ?? 0;
  const candidates = meta.candidatesTokenCount ?? 0;
  const thoughts = meta.thoughtsTokenCount ?? 0;
  const image =
    meta.candidatesTokensDetails?.find((d) => d.modality === "IMAGE")?.tokenCount ?? 0;
  const rate = RATES[model];
  const text = Math.max(0, candidates - image) + thoughts;
  return {
    model,
    inputTokens: input,
    outputTokens: candidates + thoughts,
    imageOutputTokens: image,
    thoughtTokens: thoughts,
    costUsd: input * rate.input + text * rate.output + image * rate.imageOutput,
  };
}

export async function generate(
  model: GeminiModel,
  parts: unknown[],
  generationConfig: Record<string, unknown>
): Promise<GenerateResponse> {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new Error("GEMINI_API_KEY is not set");

  const response = await fetch(`${ENDPOINT}/${model}:generateContent`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-goog-api-key": apiKey },
    body: JSON.stringify({ contents: [{ parts }], generationConfig }),
  });
  if (!response.ok) {
    throw new Error(`Gemini ${response.status}: ${(await response.text()).slice(0, 300)}`);
  }
  return (await response.json()) as GenerateResponse;
}

export type GeneratedImage = { image: Buffer; mimeType: string; usage: GeminiUsage };

/** The image part of an image-model reply, or the reason there is none. */
export function imageOf(body: GenerateResponse): GeneratedImage {
  const parts = body.candidates?.[0]?.content?.parts ?? [];
  const image = parts.find((part) => part.inlineData)?.inlineData;
  if (!image) {
    const text = parts.find((part) => part.text)?.text;
    // Gemini's own reason, when it gave one: "no image" alone cannot tell a
    // safety refusal from a blocked prompt from an image it declined to draw.
    const candidate = body.candidates?.[0];
    const why = [
      body.promptFeedback?.blockReason && `prompt blocked: ${body.promptFeedback.blockReason}`,
      body.promptFeedback?.blockReasonMessage,
      candidate?.finishReason && candidate.finishReason !== "STOP" && `finish: ${candidate.finishReason}`,
      candidate?.finishMessage,
    ]
      .filter(Boolean)
      .join("; ");
    const base = text ? `Gemini returned text only: ${text.slice(0, 200)}` : "Gemini returned no image";
    throw new Error(why ? `${base} (${why})` : base);
  }
  return {
    image: Buffer.from(image.data, "base64"),
    mimeType: image.mimeType,
    usage: usageOf(IMAGE_MODEL, body),
  };
}

/** Draws `prompt` from scratch. The prompt is the whole brief: Gemini sees nothing else. */
export async function generateImage(
  prompt: string,
  opts: { aspectRatio: AspectRatio }
): Promise<GeneratedImage> {
  const body = await generate(IMAGE_MODEL, [{ text: prompt }], {
    responseModalities: ["TEXT", "IMAGE"],
    imageConfig: { aspectRatio: opts.aspectRatio },
  });
  return imageOf(body);
}
