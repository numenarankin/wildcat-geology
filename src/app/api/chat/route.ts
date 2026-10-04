import { anthropic } from "@ai-sdk/anthropic";
import {
  convertToModelMessages,
  createUIMessageStream,
  createUIMessageStreamResponse,
  stepCountIs,
  streamText,
  type UIMessage,
} from "ai";
import "@/lib/geology-host";
import { geologyHost } from "@/lib/host";
import { runGeology } from "@/lib/ai/geology/entry";
import { geologyTrace, traceSummary } from "@/lib/ai/geology/trace";
import { geologyKbTools } from "@/lib/ai/geology-kb-tools";
import { rrcTools } from "@/lib/ai/rrc-tools";
import { FABLE_MODEL } from "@/lib/ai/geology/stage3-reason";
import { GATHERER_MODEL } from "@/lib/ai/geology/gatherer-model";
import { describeAIError, userFacingError } from "@/lib/ai/errors";
import { forbidUnlessPermitted } from "@/lib/auth/permissions";
import {
  cacheWriteTokens,
  creditStatusHeaders,
  gateAI,
  meterAnthropic,
} from "@/lib/billing/credits";
import { geologyCreditMultiplier } from "@/lib/billing/tiers";
import { getSupabaseServer } from "@/lib/supabase/server";

/**
 * POST /api/chat — geology's Orion.
 *
 * Wildcat's route (`app/api/chat/route.ts`) routes each turn and sends only
 * geology-only turns to the harness. Here every turn is geology, so every turn
 * goes to the harness first. When it declines (flag off, corpus missing, a
 * stage that failed), the turn is answered on a plain tool loop over the same
 * reference library and the public RRC record, never refused.
 *
 * Gated and metered as in Wildcat: `use_ai` is required, and the turn checks
 * and spends the org's AI credits (both as the signed-in user, through
 * Wildcat's billing RPCs). Not ported: the manifest of the org's own wells,
 * reflection, and Orion's operational tools.
 */

export const maxDuration = 300;

/** Tool steps per turn on the fallback path, as a runaway/cost guard. */
const MAX_STEPS = 10;

/** The fallback path's model. Claude 5 is unknown to the AI SDK, so its output cap is set explicitly. */
const FALLBACK_MODEL = "claude-opus-5";
const FALLBACK_MAX_OUTPUT_TOKENS = 16_000;

const FALLBACK_SYSTEM =
  "You are Orion, the geology assistant in WildcatIQ. You answer subsurface questions: " +
  "well logs and petrophysics, formations, reservoirs, and the public Texas Railroad " +
  "Commission record. Start with the reference library (geology_kb_index) for any " +
  "petrophysics or geology question rather than answering from memory, and use the rrc_* " +
  "tools for anything about specific wells, leases, operators or fields. Say plainly when " +
  "something cannot be found.";

interface ChatRequest {
  messages: UIMessage[];
  /** Present when the chat runs inside a project. */
  folderId?: string;
  projectName?: string;
  /** Where the user currently is (route + selected file/folder), if known. */
  pageContext?: string;
}

export async function POST(req: Request) {
  // One id per turn, on every log line and handed to the browser on failure.
  const turnId = crypto.randomUUID().slice(0, 8);
  const startedAt = Date.now();

  try {
    try {
      await geologyHost().auth.assertSignedIn();
    } catch {
      return Response.json({ error: "unauthorized", turnId }, { status: 401 });
    }
    const denied = await forbidUnlessPermitted("use_ai");
    if (denied) return denied;

    // AI-credit gate: refuse before doing any work when the org is out of
    // credits. One request-scoped client for the gate and the metering, so the
    // RPCs resolve the same org.
    const sb = await getSupabaseServer();
    const gate = await gateAI(sb);
    if (!gate.allowed) {
      console.warn("orion:gate-refused", { turnId, reason: gate.reason });
      return Response.json(
        { error: "ai_unavailable", reason: gate.reason, turnId },
        { status: 402 },
      );
    }

    const { messages, folderId, pageContext }: ChatRequest = await req.json();
    const reason = folderId ? "chat:project" : "chat";

    const geology = await runGeology({ messages, pageContext });
    if (!geology) {
      console.warn("orion:geology-declined", { turnId });
    } else {
      console.info("orion:geology-turn", { turnId, kind: geology.kind });
    }

    const answer = async () => {
      if (geology) return geology.stream;
      const modelMessages = await convertToModelMessages(messages);
      if (pageContext) {
        const last = modelMessages[modelMessages.length - 1];
        if (last?.role === "user") {
          const where = `\n\n---\n\n## Where the user is\n\n${pageContext}`;
          if (typeof last.content === "string") last.content += where;
          else last.content.push({ type: "text", text: where });
        }
      }
      return streamText({
        model: anthropic(FALLBACK_MODEL),
        system: FALLBACK_SYSTEM,
        messages: modelMessages,
        tools: { ...geologyKbTools(), ...rrcTools() },
        maxOutputTokens: FALLBACK_MAX_OUTPUT_TOKENS,
        providerOptions: {
          anthropic: {
            effort: "medium",
            cacheControl: { type: "ephemeral" },
          },
        },
        stopWhen: stepCountIs(MAX_STEPS),
        onFinish: ({ totalUsage, steps }) => {
          void meterAnthropic(
            {
              inputTokens: totalUsage.inputTokens ?? 0,
              outputTokens: totalUsage.outputTokens ?? 0,
              cacheReadTokens: totalUsage.cachedInputTokens ?? 0,
              cacheWriteTokens: cacheWriteTokens(steps),
              model: FALLBACK_MODEL,
            },
            reason,
            sb,
          );
        },
        onError: ({ error }) => {
          console.error("orion:stream-error", {
            turnId,
            ms: Date.now() - startedAt,
            error: describeAIError(error),
          });
        },
      });
    };

    const stream = createUIMessageStream({
      onError: (error) => {
        console.error("orion:stream-failed", {
          turnId,
          ms: Date.now() - startedAt,
          error: describeAIError(error),
        });
        return userFacingError(error, turnId);
      },
      execute: async ({ writer }) => {
        // The geology side channel, read by the browser console
        // (`logGeologyTrace`). Transient: nothing renders or persists from it.
        if (!geology) {
          writer.write({
            type: "data-geology",
            data: {
              phase: "declined",
              turnId,
              summary:
                "the geology harness declined this turn; it was answered on the fallback tool loop " +
                "(search the server log for `geology:skipped` or `geology:failed`).",
            },
            transient: true,
          });
        } else {
          const opening = geologyTrace(geology);
          writer.write({
            type: "data-geology",
            data: { phase: "context", turnId, summary: traceSummary(opening), ...opening },
            transient: true,
          });
        }

        const result = await answer();
        writer.merge(result.toUIMessageStream());
        await result.text;

        if (geology) {
          try {
            const closing = geologyTrace(geology);
            writer.write({
              type: "data-geology",
              data: { phase: "answered", turnId, summary: traceSummary(closing), ...closing },
              transient: true,
            });
          } catch (err) {
            console.error("orion:geology-trace-failed", { turnId, error: describeAIError(err) });
          }
          // Two models answered a harness turn and are priced separately: Fable
          // and the Sonnet gatherer, each at its geology rate. The gatherer is
          // metered only when it spent something, since a credit floors at 1.
          try {
            const usage = await result.totalUsage;
            void meterAnthropic(
              {
                inputTokens: usage.inputTokens ?? 0,
                outputTokens: usage.outputTokens ?? 0,
                cacheReadTokens: usage.cachedInputTokens ?? 0,
                cacheWriteTokens: 0,
                model: FABLE_MODEL,
                creditMultiplier: geologyCreditMultiplier(FABLE_MODEL),
              },
              `${reason}:geology`,
              sb,
            );
            const gather = geology.gathererUsage;
            if (gather.inputTokens > 0 || gather.outputTokens > 0) {
              void meterAnthropic(
                {
                  inputTokens: gather.inputTokens,
                  outputTokens: gather.outputTokens,
                  cacheReadTokens: gather.cacheReadTokens,
                  cacheWriteTokens: 0,
                  model: GATHERER_MODEL,
                  creditMultiplier: geologyCreditMultiplier(GATHERER_MODEL),
                },
                `${reason}:geology:gatherer`,
                sb,
              );
            }
          } catch (err) {
            console.error("orion:geology-meter-failed", { turnId, error: describeAIError(err) });
          }
        }
      },
    });

    return createUIMessageStreamResponse({
      stream,
      headers: { "x-orion-turn-id": turnId, ...creditStatusHeaders(gate) },
    });
  } catch (err) {
    console.error("orion:request-failed", {
      turnId,
      ms: Date.now() - startedAt,
      error: describeAIError(err),
    });
    return Response.json(
      { error: "orion_failed", message: userFacingError(err, turnId), turnId },
      { status: 500, headers: { "x-orion-turn-id": turnId } },
    );
  }
}
