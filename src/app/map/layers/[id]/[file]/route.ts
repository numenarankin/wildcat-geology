import { getMapContours, getMapMesh, getMapPosts, getMapRaster } from "@/lib/subsurface/maps";

/**
 * A subsurface map's layers, one file each, so Mapbox can load them by URL:
 * `raster.png` (the 16-bit depth image), `contours.json` (`?interval=` feet,
 * defaulting to the map's own), `posts.json`, and `mesh.f32` (a structure
 * map as the 3D viewer's float32 depth mesh).
 */
export async function GET(req: Request, ctx: { params: Promise<{ id: string; file: string }> }) {
  const { id, file } = await ctx.params;
  if (file === "raster.png") {
    const png = await getMapRaster(id);
    if (!png) return new Response("Not found", { status: 404 });
    return new Response(new Uint8Array(png), { headers: { "content-type": "image/png", "cache-control": "private, max-age=300" } });
  }
  if (file === "contours.json") {
    const interval = Number(new URL(req.url).searchParams.get("interval"));
    const fc = await getMapContours(id, interval || undefined);
    return fc ? Response.json(fc) : new Response("Not found", { status: 404 });
  }
  if (file === "mesh.f32") {
    const mesh = await getMapMesh(id);
    if (!mesh) return new Response("Not found", { status: 404 });
    return new Response(new Uint8Array(mesh), { headers: { "content-type": "application/octet-stream", "cache-control": "private, max-age=300" } });
  }
  if (file === "posts.json") {
    const fc = await getMapPosts(id);
    return fc ? Response.json(fc) : new Response("Not found", { status: 404 });
  }
  return new Response("Not found", { status: 404 });
}
