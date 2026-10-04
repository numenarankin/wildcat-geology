import "server-only";
import { getSupabaseServer, hasSupabase } from "@/lib/supabase/server";
import {
  ALL_PERMISSION_KEYS,
  cleanPermissions,
  expandPermissions,
  type PermissionKey,
} from "@/lib/settings/org";

/**
 * The signed-in user's capabilities in their active org, trimmed from Wildcat's
 * `lib/auth/permissions.ts`. Resolved from the database under the user's own
 * session, never from JWT metadata: an org owner holds everything, a member
 * holds their granted keys plus what those imply.
 */
async function currentPermissions(): Promise<PermissionKey[]> {
  if (!hasSupabase()) return [...ALL_PERMISSION_KEYS];
  try {
    const sb = await getSupabaseServer();
    const [
      {
        data: { user },
      },
      { data: orgId },
    ] = await Promise.all([sb.auth.getUser(), sb.rpc("current_org_id")]);
    if (!user || !orgId) return [];

    const [{ data: org }, { data: member }] = await Promise.all([
      sb
        .from("organizations")
        .select("id")
        .eq("id", orgId)
        .eq("owner_uid", user.id)
        .maybeSingle(),
      sb
        .from("org_members")
        .select("permissions, is_owner")
        .eq("org_id", orgId)
        .eq("auth_user_id", user.id)
        .eq("status", "active")
        .maybeSingle(),
    ]);
    if (org || member?.is_owner) return [...ALL_PERMISSION_KEYS];
    if (!member) return [];
    return expandPermissions(cleanPermissions((member.permissions ?? []) as string[]));
  } catch (error) {
    console.error("currentPermissions failed", error);
    return [];
  }
}

/** A 403 for an API route when the caller holds none of `permission`, else null. */
export async function forbidUnlessPermitted(
  permission: PermissionKey | PermissionKey[]
): Promise<Response | null> {
  const held = new Set(await currentPermissions());
  const wanted = Array.isArray(permission) ? permission : [permission];
  if (wanted.some((p) => held.has(p))) return null;
  return Response.json(
    { error: "forbidden", reason: "missing_permission" },
    { status: 403 }
  );
}
