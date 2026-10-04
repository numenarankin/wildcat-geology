/**
 * GET / — the front door. A Route Handler rather than a page so the redirect
 * is a real 307 before any rendering starts (see Wildcat's `app/route.ts`).
 *
 * The Location is RELATIVE on purpose. `new URL("/orion", request.url)` takes
 * the host Next binds to (`localhost:3000`), so a browser reaching the dev
 * server by IP was sent to its own localhost and never arrived.
 */
export function GET() {
  return new Response(null, { status: 307, headers: { Location: "/orion" } });
}
