"use client";

import { useState } from "react";
import { EyeIcon, EyeOffIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AuthShell } from "@/components/auth/auth-shell";
import { Spokes } from "@/components/ui/spokes";
import { getSupabaseBrowser } from "@/lib/supabase/client";
import { wildcatUrl } from "@/lib/wildcat";

/**
 * Sign in with a Wildcat account.
 *
 * Wildcat's `auth-page.tsx`, sign-in view, unchanged in look. The other two
 * views are Wildcat's to run: sign-up creates an org and recovery mails a reset
 * link, both with Wildcat's service key, which this app does not hold. So
 * "Forgot password?" and "Sign up" go to Wildcat's own /auth.
 */

/**
 * Where to land after sign-in: the `next` path the proxy stashed when it
 * bounced an unauthenticated request here, or home. Validated to a same-origin
 * relative path to avoid an open-redirect.
 */
function safeNext(): string {
  if (typeof window === "undefined") return "/";
  const next = new URLSearchParams(window.location.search).get("next");
  if (next && next.startsWith("/") && !next.startsWith("//") && next !== "/auth") {
    return next;
  }
  return "/";
}

/**
 * GoTrue's one answer covers both "no such account" and "wrong password".
 * Wildcat tells them apart with a service-role lookup; without one, say the
 * true, vaguer thing (Wildcat's own wording for when it cannot tell).
 */
function describeSignInFailure(message: string): Error {
  if (!/invalid login credentials/i.test(message)) return new Error(message);
  return new Error("That email and password don't match an account.");
}

export function AuthPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { error } = await getSupabaseBrowser().auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw describeSignInFailure(error.message);
      // Hard navigation so the fresh session cookie is sent on the next
      // request and the proxy lets us through (a soft push can race the
      // cookie and bounce back to /auth).
      window.location.assign(safeNext());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to your WildcatIQ account." pane="signin">
      <div className="space-y-6">
        <form onSubmit={handleSubmit} className="space-y-3">
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium">Email</span>
            <Input
              type="email"
              autoComplete="email"
              required
              autoFocus
              className="h-11"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
            />
          </label>

          <div className="flex flex-col gap-1.5">
            <div className="flex items-baseline justify-between gap-3">
              <label htmlFor="auth-password" className="text-sm font-medium">
                Password
              </label>
              <a
                href={wildcatUrl("/auth?mode=forgot")}
                className="text-xs font-medium text-muted-foreground underline underline-offset-4 hover:text-foreground"
              >
                Forgot password?
              </a>
            </div>
            <div className="relative">
              <Input
                id="auth-password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                className="h-11 pr-11"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
                tabIndex={-1}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-muted-foreground transition-colors hover:text-foreground"
              >
                {showPassword ? <EyeOffIcon className="size-4" /> : <EyeIcon className="size-4" />}
              </button>
            </div>
          </div>

          {error && (
            <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          <Button type="submit" className="h-11 w-full" disabled={loading}>
            {loading && <Spokes data-icon="inline-start" />}
            Sign in
          </Button>
        </form>

        <p className="text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <a
            href={wildcatUrl("/auth?mode=signup")}
            className="font-medium text-primary underline underline-offset-4 hover:text-primary/80"
          >
            Sign up
          </a>
        </p>
      </div>
    </AuthShell>
  );
}
