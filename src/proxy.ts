import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";

/**
 * Proxy (Next.js 16's renamed Middleware), from Wildcat's `src/proxy.ts`:
 *  1. refresh the Supabase auth session cookie, and
 *  2. OPTIMISTICALLY redirect signed-out users to /auth.
 *
 * The real boundary is RLS in Wildcat's database: every read here runs as the
 * signed-in user. Wildcat's two account gates (unfinished onboarding, and a
 * multi-workspace user who has not picked one) send the user to Wildcat, which
 * owns both flows. Its billing-lockout hint is a cookie Wildcat sets on its own
 * origin, so it never reaches this one and is not checked here.
 */

const PUBLIC_PATHS = ["/auth"];

function isPublic(pathname: string): boolean {
  return PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

function toWildcat(path: string): NextResponse {
  const base = (process.env.NEXT_PUBLIC_WILDCAT_URL ?? "").replace(/\/+$/, "");
  return NextResponse.redirect(`${base}${path}`);
}

export async function proxy(request: NextRequest) {
  const isApi = request.nextUrl.pathname.startsWith("/api/");

  // Response we can attach refreshed auth cookies to.
  let response = NextResponse.next({ request });

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  // If Supabase isn't configured, don't lock the app out — just pass through.
  if (!url || !key) return response;

  const supabase = createServerClient(url, key, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        for (const { name, value } of cookiesToSet) {
          request.cookies.set(name, value);
        }
        response = NextResponse.next({ request });
        for (const { name, value, options } of cookiesToSet) {
          response.cookies.set(name, value, options);
        }
      },
    },
  });

  // IMPORTANT: getUser() re-validates the token and triggers the cookie refresh.
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;

  // API routes authenticate themselves and must answer JSON, never a redirect.
  if (!user && !isPublic(pathname) && !isApi) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/auth";
    redirectUrl.search = "";
    // Remember where they were headed so /auth can send them back after login.
    if (pathname !== "/") {
      redirectUrl.searchParams.set("next", pathname + request.nextUrl.search);
    }
    // On the host the BROWSER used. `nextUrl` carries the one Next binds to
    // (localhost), which sends a remote browser to its own machine; and a
    // proxy redirect must be absolute, so a relative Location is not an option.
    const host = request.headers.get("x-forwarded-host") ?? request.headers.get("host");
    if (host) {
      redirectUrl.host = host;
      redirectUrl.protocol = request.headers.get("x-forwarded-proto") ?? redirectUrl.protocol;
    }
    return NextResponse.redirect(redirectUrl);
  }

  if (user && request.method === "GET" && !isApi && !isPublic(pathname)) {
    // Onboarding gate: an org OWNER who has not finished setting up, while in
    // their own unfinished org. Same check as Wildcat's.
    const { data: ownedOrg } = await supabase
      .from("organizations")
      .select("id, onboarding_completed_at")
      .eq("owner_uid", user.id)
      .maybeSingle<{ id: string; onboarding_completed_at: string | null }>();
    if (ownedOrg && ownedOrg.onboarding_completed_at === null) {
      const { data: activeOrgId } = await supabase.rpc("current_org_id");
      if (!activeOrgId || activeOrgId === ownedOrg.id) return toWildcat("/onboarding");
    }

    // Workspace picker gate: several workspaces and none chosen yet.
    const { data: mustChoose } = await supabase.rpc("needs_org_choice");
    if (mustChoose === true) return toWildcat("/select-org");
  }

  return response;
}

export const config = {
  // Everything except Next internals, static asset files, and the log upload.
  //
  // `api/digitize` is excluded because the proxy BUFFERS a request body it
  // runs on, capped at 10 MB, and a scanned log is routinely bigger. The route
  // checks the session itself, so nothing is gated by the proxy there anyway.
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api/digitize|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|woff2?)$).*)",
  ],
};
