"use client";

import { useEffect, useMemo, useState } from "react";
import { OrbitView } from "@deck.gl/core";
import SubsurfaceViewer, { type ViewsType } from "@webviz/subsurface-viewer";
import { AxesLayer, MapLayer, type MapLayerProps } from "@webviz/subsurface-viewer/dist/layers";
import { LoadingScreen } from "@/components/ui/loading-screen";
import { bandRgbAt, colorBands } from "@/lib/subsurface/bands";
import type { GridFrame, SubsurfaceMapMeta } from "@/lib/subsurface/maps";
import type { PaletteId } from "@/lib/subsurface/palette";

/**
 * The structure surfaces in 3D, with Equinor's subsurface-viewer (deck.gl).
 *
 * Every surface is a MapLayer on the shared grid: the mesh is depth in feet,
 * positive down (`mesh.f32`), and the same array is the colour property, so
 * each surface carries the same banded fill as the 2D map (one band per
 * contour interval, over that surface's own colour span) plus its contour
 * lines. The viewer works in its own cartesian frame, here the build's local
 * frame in feet (x east, y north), so it sits on no basemap.
 *
 * Loaded client-only (`next/dynamic`, `ssr: false`): deck.gl needs WebGL, and
 * the viewer starts a web-worker pool when it is imported.
 */

/*
 * Gestures match the Mapbox map on the 2D view, not deck.gl's orbit defaults
 * (left-drag rotate, Shift/right-drag pan): left-drag pans, right-drag or
 * Shift-drag rotates and tilts, the wheel zooms smoothly.
 */
const VIEWS: ViewsType = {
  layout: [1, 1],
  viewports: [
    {
      id: "view_3d",
      viewType: OrbitView,
      controller: { dragMode: "pan", scrollZoom: { speed: 0.01, smooth: true }, inertia: 300 },
    },
  ],
};

/*
 * Without lights the banded fill is flat colour and the relief does not read.
 * A head light follows the camera; the directional light comes from the
 * north-west and above (travelling east, south and down; the scene is z-up,
 * depth is negated for display), the cartographic convention for shaded relief.
 */
const LIGHTS = {
  headLight: { intensity: 0.35 },
  ambientLight: { intensity: 0.65 },
  directionalLights: [{ intensity: 0.45, direction: [1, -1, -1] as [number, number, number] }],
};

/**
 * The viewer samples this at t in [0, 1] across `colorMapRange` to build its
 * 256-entry colormap texture. The range is depth (positive), the bands are
 * built in subsea (negative) feet as on the 2D map, so t maps to depth
 * lo + t (hi - lo) and that depth to its band. (A Uint8Array colormap would be
 * read as discrete categories, not as a continuous ramp.)
 */
function colormapFor(map: SubsurfaceMapMeta, palette: PaletteId, intervalFt: number): MapLayerProps["colorMapFunction"] {
  const bands = colorBands(palette, "subsea", { min: map.colorMin, max: map.colorMax }, intervalFt);
  const lo = -map.colorMax;
  const hi = -map.colorMin;
  const fn = (t: number) => {
    const depth = lo + (hi - lo) * t;
    return [...bandRgbAt(bands, -depth), 255] as [number, number, number, number];
  };
  return fn as unknown as MapLayerProps["colorMapFunction"];
}

export default function Subsurface3DView({
  surfaces,
  frame,
  palette,
  intervalFt,
  verticalScale,
  resetCount,
}: {
  /** Structure maps to draw, shallow first. */
  surfaces: SubsurfaceMapMeta[];
  frame: GridFrame;
  palette: PaletteId;
  intervalFt: number;
  verticalScale: number;
  /** Bumped by the bar's Reset view button: returns the camera home. */
  resetCount: number;
}) {
  const [meshes, setMeshes] = useState<Record<string, Float32Array>>({});
  const [error, setError] = useState<string | null>(null);

  const ids = surfaces.map((s) => s.id).join(",");
  useEffect(() => {
    let cancelled = false;
    const missing = surfaces.filter((s) => !meshes[s.id]);
    if (missing.length === 0) return;
    Promise.all(
      missing.map(async (s) => {
        const res = await fetch(`/map/layers/${encodeURIComponent(s.id)}/mesh.f32`);
        if (!res.ok) throw new Error(`Could not load the ${s.name} surface.`);
        return [s.id, new Float32Array(await res.arrayBuffer())] as const;
      })
    )
      .then((loaded) => {
        if (!cancelled) setMeshes((prev) => ({ ...prev, ...Object.fromEntries(loaded) }));
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not load the surfaces.");
      });
    return () => {
      cancelled = true;
    };
    // `meshes` is read to skip what is already loaded, not to refetch on it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids]);

  const ready = surfaces.every((s) => meshes[s.id]);

  // Depth extent of everything drawn, for the axes box and the camera.
  const [ox, oy] = frame.origin;
  const maxX = ox + (frame.count[0] - 1) * frame.increment[0];
  const maxY = oy + (frame.count[1] - 1) * frame.increment[1];
  const minDepth = Math.min(...surfaces.map((s) => -s.max));
  const maxDepth = Math.max(...surfaces.map((s) => -s.min));

  /*
   * The opening camera, set outright rather than from a fit box: the viewer's
   * box fit does not account for `verticalScale`, so an exaggerated scene
   * opened off-centre and at the wrong size. Target is the centre of the data
   * in display space before scaling (z is up, so depth is negated; the viewer
   * multiplies the target's z by `verticalScale` itself). Zoom is log2 of
   * pixels per foot, chosen so the larger of the map's diagonal and the
   * exaggerated depth range fills about 70% of the panel width.
   */
  const cx = (ox + maxX) / 2;
  const cy = (oy + maxY) / 2;
  const cz = -(minDepth + maxDepth) / 2;
  const extentFt = Math.max(Math.hypot(maxX - ox, maxY - oy), (maxDepth - minDepth) * verticalScale);
  const panelPx = typeof window === "undefined" ? 1200 : window.innerWidth;
  const zoom = Math.log2((0.7 * panelPx) / extentFt);

  const layers = useMemo(() => {
    if (!ready) return [];
    return [
      new AxesLayer({
        id: "axes",
        bounds: [ox, oy, minDepth, maxX, maxY, maxDepth],
        ZIncreasingDownwards: true,
      }),
      ...surfaces.map(
        (s) =>
          new MapLayer({
        id: `surface-${s.id}`,
        frame: { origin: frame.origin, increment: frame.increment, count: frame.count, rotDeg: 0 },
        meshData: meshes[s.id],
        propertiesData: meshes[s.id],
        colorMapRange: [-s.colorMax, -s.colorMin],
        colorMapClampColor: true,
        colorMapFunction: colormapFor(s, palette, intervalFt),
        contours: [0, intervalFt],
        isContoursDepth: true,
        gridLines: false,
        material: true,
        smoothShading: true,
        ZIncreasingDownwards: true,
          })
      ),
    ];
  }, [ready, surfaces, meshes, frame, palette, intervalFt, ox, oy, maxX, maxY, minDepth, maxDepth]);

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-sm text-destructive">{error}</div>
    );
  }
  if (!ready) {
    return (
      <div className="flex flex-1 bg-background">
        <LoadingScreen label="Loading surfaces" />
      </div>
    );
  }
  return (
    <div className="relative min-h-0 flex-1 overflow-hidden">
      <SubsurfaceViewer
        id="subsurface-3d"
        layers={layers}
        views={VIEWS}
        coordinateUnit="ft"
        verticalScale={verticalScale}
        lights={LIGHTS}
        triggerHome={resetCount}
        cameraPosition={{
          rotationOrbit: 30,
          rotationX: 35,
          zoom,
          target: [cx, cy, cz],
        }}
      />
    </div>
  );
}
