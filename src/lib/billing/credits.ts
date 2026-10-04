import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { getSupabaseServer, hasSupabase } from "@/lib/supabase/server";
import { anthropicCredits, providerCostUsd } from "@/lib/billing/tiers";

/**
 * AI-credit gate + usage metering, trimmed from Wildcat's
 * `lib/billing/credits.ts`.
 *
 * Both halves run as the signed-in user: `billing_gate` and `billing_spend` are
 * SECURITY DEFINER RPCs that resolve the org from `current_org_id()`, so no
 * service key is involved. Geology spends from the same org balance Wildcat
 * does. The Stripe reset path, overdraft for the phone app, web search and
 * ElevenLabs meters are Wildcat-only and not here.
 */

/** Master billing switch, as in Wildcat's `lib/env.ts`. Off means everything is allowed. */
function isPaidMode(): boolean {
  return process.env.PAID_MODE === "true";
}

export interface GateResult {
  allowed: boolean;
  reason: string;
  orgId?: string;
  freeRemaining?: number;
  paidBalance?: number;
  balance?: number;
}

interface GateRow {
  allowed: boolean;
  reason: string;
  org_id?: string;
  free_remaining?: number;
  paid_balance?: number;
  balance?: number;
}

export const CREDIT_STATUS_HEADER = "x-wildcat-credits";
export const CREDIT_STATUS_OVERDRAWN = "overdrawn";

/** Response headers that tell the client the balance went negative. */
export function creditStatusHeaders(gate: GateResult): Record<string, string> {
  return gate.reason === CREDIT_STATUS_OVERDRAWN
    ? { [CREDIT_STATUS_HEADER]: CREDIT_STATUS_OVERDRAWN }
    : {};
}

/** Block before doing any AI work when the org is out of credits or its subscription is inactive. Fails closed. */
export async function gateAI(client?: SupabaseClient): Promise<GateResult> {
  if (!isPaidMode()) return { allowed: true, reason: "paid_mode_off" };
  if (!hasSupabase()) return { allowed: true, reason: "billing_disabled" };
  try {
    const sb = client ?? (await getSupabaseServer());
    const { data, error } = await sb.rpc("billing_gate", { p_allow_overdraft: false });
    if (error) {
      console.error("gateAI: billing_gate failed, denying", error.message);
      return { allowed: false, reason: "gate_error" };
    }
    const row = data as GateRow;
    return {
      allowed: Boolean(row?.allowed),
      reason: row?.reason ?? "unknown",
      orgId: row?.org_id,
      freeRemaining: row?.free_remaining,
      paidBalance: row?.paid_balance,
      balance: row?.balance,
    };
  } catch (err) {
    console.error("gateAI: unexpected error, denying", err);
    return { allowed: false, reason: "gate_exception" };
  }
}

/** Deduct credits from the caller's org. Never throws: a failed meter is logged, not shown. */
async function spend(
  amount: number,
  reason: string,
  meta: Record<string, unknown>,
  client?: SupabaseClient
): Promise<void> {
  if (!isPaidMode() || !hasSupabase() || amount <= 0) return;
  try {
    const sb = client ?? (await getSupabaseServer());
    const { error } = await sb.rpc("billing_spend", {
      p_amount: amount,
      p_reason: reason,
      p_meta: meta,
    });
    if (error) console.error("spend: billing_spend failed", error.message);
  } catch (err) {
    console.error("spend: unexpected error", err);
  }
}

export interface AnthropicMeterUsage {
  inputTokens?: number;
  outputTokens?: number;
  cacheReadTokens?: number;
  cacheWriteTokens?: number;
  model?: string;
  /** Geology's per-model rate (`geologyCreditMultiplier`). */
  creditMultiplier?: number;
}

/** Meter one Anthropic call's token usage against the org's credits. */
export async function meterAnthropic(
  usage: AnthropicMeterUsage,
  reason: string,
  client?: SupabaseClient
): Promise<void> {
  const input = usage.inputTokens ?? 0;
  const output = usage.outputTokens ?? 0;
  const cacheRead = usage.cacheReadTokens ?? 0;
  const cacheWrite = usage.cacheWriteTokens ?? 0;
  const multiplier = usage.creditMultiplier ?? 1;
  const credits = anthropicCredits(input, output, multiplier);
  const costUsd = providerCostUsd(usage.model ?? "claude-opus-5", {
    inputTokens: Math.max(0, input - cacheRead - cacheWrite),
    outputTokens: output,
    cacheReadTokens: cacheRead,
    cacheWriteTokens: cacheWrite,
  });
  await spend(
    credits,
    reason,
    {
      provider: "anthropic",
      input,
      output,
      ...(cacheRead ? { cacheRead } : {}),
      ...(cacheWrite ? { cacheWrite } : {}),
      ...(usage.model ? { model: usage.model } : {}),
      ...(multiplier !== 1 ? { creditMultiplier: multiplier } : {}),
      costUsd: Number(costUsd.toFixed(6)),
    },
    client
  );
}

/** Prompt-cache writes across a run's steps (the SDK's usage total omits them). */
export function cacheWriteTokens(
  steps: ReadonlyArray<{ providerMetadata?: unknown }> | undefined
): number {
  let total = 0;
  for (const step of steps ?? []) {
    const written = (
      step.providerMetadata as
        | { anthropic?: { usage?: { cache_creation_input_tokens?: unknown } } }
        | undefined
    )?.anthropic?.usage?.cache_creation_input_tokens;
    if (typeof written === "number") total += written;
  }
  return total;
}
