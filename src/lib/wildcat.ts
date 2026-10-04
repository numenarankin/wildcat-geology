/**
 * A page on Wildcat's web app.
 *
 * Geology signs in with Wildcat accounts but does not own them: creating an
 * account (which provisions an org), resetting a password (mailed with
 * Wildcat's service key), onboarding, settings, billing and help all live in
 * Wildcat, and geology links there instead of keeping second copies.
 */
export function wildcatUrl(path: string): string {
  const base = (process.env.NEXT_PUBLIC_WILDCAT_URL ?? "").replace(/\/+$/, "");
  return `${base}${path}`;
}
