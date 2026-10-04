"use server";

import { getSupabaseServer, hasSupabase } from "@/lib/supabase/server";

/**
 * Enter a workspace. Wildcat's `enterOrg`, unchanged: the database function
 * checks membership, and the active org it sets is the same one Wildcat reads,
 * so switching here switches there too.
 */
export async function enterOrg(orgId: string): Promise<void> {
  if (!hasSupabase()) return;
  const sb = await getSupabaseServer();
  const { error } = await sb.rpc("set_active_org", { org: orgId });
  if (error) {
    console.error("enterOrg failed", error);
    throw new Error("You are not a member of that workspace.");
  }
}
