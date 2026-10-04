import "server-only";
import { cache } from "react";
import { getSupabaseServer, hasSupabase } from "@/lib/supabase/server";
import type { OrgOption } from "@/lib/auth/org-types";

/**
 * Everything the account menu shows, read once per request as the signed-in
 * user. The same reads as Wildcat's layout (`getProfile`, `getCreditBalance`,
 * `listMyOrgs`, `getActiveOrgId`), against the same tables and RPCs, under RLS.
 */
export interface Account {
  name: string;
  email: string;
  avatarUrl: string | null;
  /** Total AI credits remaining for the org (0 when unreadable). */
  credits: number;
  orgs: OrgOption[];
  currentOrgId: string | null;
}

const AVATAR_BUCKET = "avatars";

interface MyOrgRow {
  org_id: string;
  name: string | null;
  is_owner: boolean | null;
}

export const getAccount = cache(async (): Promise<Account | null> => {
  if (!hasSupabase()) return null;
  const sb = await getSupabaseServer();
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return null;

  const [profile, credits, orgs, currentOrgId] = await Promise.all([
    sb
      .from("profile")
      .select("name, avatar_url")
      .maybeSingle<{ name: string | null; avatar_url: string | null }>(),
    sb
      .from("org_credits")
      .select("free_remaining, paid_balance")
      .maybeSingle<{ free_remaining: number | null; paid_balance: number | null }>(),
    sb.rpc("my_orgs"),
    sb.rpc("current_org_id"),
  ]);

  return {
    name: (profile.data?.name ?? "").trim(),
    email: user.email ?? "",
    avatarUrl: await signedAvatar(profile.data?.avatar_url ?? null),
    credits: credits.data
      ? Number(credits.data.free_remaining ?? 0) + Number(credits.data.paid_balance ?? 0)
      : 0,
    orgs: ((orgs.data ?? []) as MyOrgRow[]).map((row) => ({
      id: row.org_id,
      name: row.name ?? "Workspace",
      isOwner: Boolean(row.is_owner),
    })),
    currentOrgId: (currentOrgId.data as string | null) ?? null,
  };
});

/**
 * A signed URL for the stored avatar. Wildcat signs with its service key; here
 * it is the user's own session, so a storage policy that does not let them read
 * their own avatar shows initials instead, which is the menu's fallback anyway.
 */
async function signedAvatar(key: string | null): Promise<string | null> {
  if (!key) return null;
  if (key.startsWith("http")) return key;
  const sb = await getSupabaseServer();
  const { data } = await sb.storage.from(AVATAR_BUCKET).createSignedUrl(key, 60 * 60);
  return data?.signedUrl ?? null;
}
