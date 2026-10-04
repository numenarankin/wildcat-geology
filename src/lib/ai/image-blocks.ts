/**
 * The generate_image contract between the tool and the chat. Pure and
 * framework-free: the tool (server), the message renderer and the chat route
 * all read it, and it unit-tests without a DB or a browser.
 */

export const IMAGE_TOOL = "generate_image";
const IMAGE_PART = `tool-${IMAGE_TOOL}`;

export const ASPECT_RATIOS = ["1:1", "4:3", "3:4", "16:9", "9:16"] as const;
export type AspectRatio = (typeof ASPECT_RATIOS)[number];

/** A picture is ~70 credits; one answer may draw this many. */
export const MAX_IMAGES_PER_TURN = 2;

export type ImageBlock = {
  kind: "image";
  state: "drawing" | "done" | "failed";
  aspectRatio: AspectRatio;
  fileId?: string;
  name?: string;
};

type ToolPartLike = {
  type?: string;
  state?: string;
  input?: unknown;
  output?: unknown;
  approval?: { approved?: boolean };
};

function aspectOf(input: unknown): AspectRatio {
  const ratio = (input as { aspectRatio?: unknown } | null)?.aspectRatio;
  return ASPECT_RATIOS.includes(ratio as AspectRatio) ? (ratio as AspectRatio) : "4:3";
}

/**
 * The block a generate_image part renders as, or null for none. The tool runs
 * without approval; the approval states are handled only so a conversation
 * saved while it still asked renders sensibly.
 */
export function imageBlockOf(part: unknown): ImageBlock | null {
  const p = part as ToolPartLike | null;
  if (p?.type !== IMAGE_PART) return null;
  const aspectRatio = aspectOf(p.input);
  switch (p.state) {
    case "approval-responded":
      return p.approval?.approved ? { kind: "image", state: "drawing", aspectRatio } : null;
    case "input-available":
      return { kind: "image", state: "drawing", aspectRatio };
    case "output-available": {
      const out = p.output as { ok?: boolean; fileId?: unknown; name?: unknown } | null;
      if (out?.ok && typeof out.fileId === "string") {
        return {
          kind: "image",
          state: "done",
          aspectRatio,
          fileId: out.fileId,
          name: typeof out.name === "string" ? out.name : undefined,
        };
      }
      return { kind: "image", state: "failed", aspectRatio };
    }
    case "output-error":
      return { kind: "image", state: "failed", aspectRatio };
    default:
      return null;
  }
}

/**
 * Images already drawn in the answer being written: generate_image calls since
 * the last user message that produced a file. Seeds the per-turn cap, because
 * approving any other tool resumes the run as a fresh POST and per-request
 * state starts empty.
 */
export function imagesDrawnThisTurn(
  messages: readonly { role?: string; parts?: readonly unknown[] }[]
): number {
  let count = 0;
  for (let i = messages.length - 1; i >= 0; i--) {
    const message = messages[i];
    if (message.role === "user") break;
    for (const part of message.parts ?? []) {
      if (imageBlockOf(part)?.state === "done") count += 1;
    }
  }
  return count;
}
