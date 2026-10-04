import { createServerClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

/**
 * Request-scoped Supabase client bound to the signed-in user's session.
 *
 * Wildcat's project, with the **publishable** key and the user's session
 * cookies, so every query runs as that user and Row Level Security applies.
 * Geology deliberately has no service-role client: the account, its org and its
 * credits are all readable by their owner, and a secret key here would hand
 * every collaborator the whole Wildcat database.
 *
 * Trimmed from Wildcat's `lib/supabase/server.ts` (no bearer path; there is no
 * tablet app here).
 */
export async function getSupabaseServer(): Promise<SupabaseClient> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) {
    throw new Error(
      "Supabase is not configured: set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY in .env"
    );
  }
  // Imported lazily so `next/headers` never enters a client bundle's graph.
  const { cookies } = await import("next/headers");
  const cookieStore = await cookies();
  return createServerClient(url, key, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          for (const { name, value, options } of cookiesToSet) {
            cookieStore.set(name, value, options);
          }
        } catch {
          // Called from a Server Component, where cookies are read-only. Safe to
          // ignore: Proxy refreshes the session cookie.
        }
      },
    },
  });
}

export function hasSupabase(): boolean {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
  );
}
