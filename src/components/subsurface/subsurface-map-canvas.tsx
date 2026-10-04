"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { LoadingScreen } from "@/components/ui/loading-screen";
import { BASEMAPS, DEFAULT_BASEMAP, MapControls, type Basemap } from "./map-controls";
import type { PaletteId } from "@/lib/subsurface/palette";
import { VALUE_SCALE, encodeValue } from "@/lib/subsurface/png";
import { colorBands, type Band, type MapDatum } from "@/lib/subsurface/bands";
import type { Corners } from "@/lib/subsurface/maps";

export type { MapDatum };

/** One map's layers, as URLs Mapbox loads, plus the frame they sit in. */
export interface SubsurfaceMapLayers {
  rasterUrl: string;
  contoursUrl: string;
  /** `min` / `max`: the colour span the raster is encoded over. */
  meta: { corners: Corners; min: number; max: number; intervalFt: number };
}

const RASTER_SOURCE = "sm-raster";
const CONTOUR_SOURCE = "sm-contours";

/** Texas, for the empty case: the same frame the other maps open on. */
const TEXAS_BOUNDS: mapboxgl.LngLatBoundsLike = [
  [-106.9, 25.5],
  [-93.2, 36.7],
];

type Expr = mapboxgl.ExpressionSpecification;

const EMPTY: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };

/** The bands as a `raster-color` step expression over the raster's 16-bit value. */
function rasterColor(bands: Band[], span: { min: number; max: number }): Expr {
  const steps: (string | number)[] = [bands[0].color];
  for (const b of bands.slice(1)) steps.push(encodeValue(b.from!, span.min, span.max), b.color);
  return ["step", ["raster-value"], ...steps] as unknown as Expr;
}

export function formatFeet(v: number): string {
  return `${Math.round(v).toLocaleString()} ft`;
}

/**
 * Copied from wildcat src/components/structure-maps/structure-map-canvas.tsx.
 * Differences: the legend title is a prop (structure or isopach); the camera
 * fits once, to the first map, because every map shares one grid and a
 * formation switch should keep the view; no well posts; and the raster's
 * `raster-color-mix` is scaled for channels Mapbox reads as 0..1 (Wildcat's
 * [256, 1, 0, 0] assumes 0..255 and decodes every pixel to about 0, which
 * draws the whole surface in one colour).
 *
 * The structure map itself: a coloured depth raster, contour lines with
 * labelled index contours.
 * Same map stack and conventions as the leases map (basemap toggle via
 * `MapControls`, layers rebuilt on `style.load`, ResizeObserver for the
 * collapsing sidebar).
 */
export function SubsurfaceMapCanvas({
  layers,
  palette,
  datum,
  legendTitle,
  loading,
  error,
}: {
  /** The selected map's built layers, or null when it has none yet. */
  layers: SubsurfaceMapLayers | null;
  palette: PaletteId;
  datum: MapDatum;
  legendTitle: string;
  loading: boolean;
  error: string | null;
}) {
  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const [ready, setReady] = useState(false);
  const [drawn, setDrawn] = useState(false);
  const [basemap, setBasemap] = useState<Basemap>(DEFAULT_BASEMAP);
  const appliedBasemapRef = useRef<Basemap>(DEFAULT_BASEMAP);
  const [styleEpoch, setStyleEpoch] = useState(0);
  /** Which layer set the camera was last fitted to, so a palette change or a
   * basemap swap never yanks the view. */
  const fittedRef = useRef<string | null>(null);

  const bands = useMemo(
    () => (layers ? colorBands(palette, datum, layers.meta, layers.meta.intervalFt) : null),
    [palette, datum, layers]
  );
  const colorExpr = useMemo<Expr>(
    () => (bands && layers ? rasterColor(bands, layers.meta) : (["literal", "rgba(0,0,0,0)"] as unknown as Expr)),
    [bands, layers]
  );

  useEffect(() => {
    if (!token || !containerRef.current || mapRef.current) return;
    mapboxgl.accessToken = token;
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: BASEMAPS[DEFAULT_BASEMAP],
      bounds: TEXAS_BOUNDS,
      fitBoundsOptions: { padding: 24 },
    });
    mapRef.current = map;
    map.once("idle", () => setDrawn(true));

    map.on("style.load", () => {
      if (!map.getSource(CONTOUR_SOURCE)) map.addSource(CONTOUR_SOURCE, { type: "geojson", data: EMPTY });
      // The raster source needs its corners, which come with the layers; it is
      // added in the data effect below. The vector layers can be declared now.
      if (!map.getLayer("sm-contour-line")) {
        map.addLayer({
          id: "sm-contour-line",
          type: "line",
          source: CONTOUR_SOURCE,
          paint: {
            "line-color": "#111827",
            "line-width": ["case", ["boolean", ["get", "index"], false], 1.8, 0.8] as unknown as Expr,
            "line-opacity": 0.85,
          },
        });
      }
      if (!map.getLayer("sm-contour-label")) {
        map.addLayer({
          id: "sm-contour-label",
          type: "symbol",
          source: CONTOUR_SOURCE,
          filter: ["==", ["get", "index"], true],
          layout: {
            "symbol-placement": "line",
            "text-field": ["to-string", ["round", ["get", "value"]]] as unknown as Expr,
            "text-size": 11,
            "text-max-angle": 30,
            "symbol-spacing": 300,
            "text-rotation-alignment": "map",
          },
          paint: {
            "text-color": "#111827",
            "text-halo-color": "rgba(255,255,255,0.9)",
            "text-halo-width": 1.6,
          },
        });
      }
      setReady(true);
      setStyleEpoch((n) => n + 1);
    });

    const ro = new ResizeObserver(() => map.resize());
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      map.remove();
      mapRef.current = null;
      setReady(false);
      setDrawn(false);
    };
  }, [token]);

  // Layers in, or out. `styleEpoch` because a basemap swap empties the style.
  // The colour ramp is read through a ref here so a palette change does not
  // tear the raster down; the effect after this one restyles it in place.
  const colorRef = useRef(colorExpr);
  useEffect(() => {
    colorRef.current = colorExpr;
  }, [colorExpr]);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;

    if (map.getLayer("sm-raster")) map.removeLayer("sm-raster");
    if (map.getSource(RASTER_SOURCE)) map.removeSource(RASTER_SOURCE);
    const contourSrc = map.getSource(CONTOUR_SOURCE) as mapboxgl.GeoJSONSource | undefined;

    if (!layers) {
      contourSrc?.setData(EMPTY);
      return;
    }

    map.addSource(RASTER_SOURCE, { type: "image", url: layers.rasterUrl, coordinates: layers.meta.corners });
    map.addLayer(
      {
        id: "sm-raster",
        type: "raster",
        source: RASTER_SOURCE,
        paint: {
          "raster-color": colorRef.current,
          // Channels arrive as 0..1: R carries the high byte, G the low byte.
          "raster-color-mix": [255 * 256, 255, 0, 0],
          "raster-color-range": [0, VALUE_SCALE],
          "raster-opacity": 0.95,
          "raster-resampling": "linear",
          "raster-fade-duration": 0,
        },
      },
      "sm-contour-line"
    );
    contourSrc?.setData(layers.contoursUrl as unknown as GeoJSON.FeatureCollection);

    if (fittedRef.current === null) {
      const b = new mapboxgl.LngLatBounds();
      for (const c of layers.meta.corners) b.extend(c as [number, number]);
      map.fitBounds(b, { padding: 60, maxZoom: 14, duration: 800 });
      fittedRef.current = layers.rasterUrl;
    }
  }, [layers, ready, styleEpoch]);

  // Palette change: restyle the raster that is already there.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !map.getLayer("sm-raster")) return;
    map.setPaintProperty("sm-raster", "raster-color", colorExpr);
  }, [colorExpr, ready, layers, styleEpoch]);

  // Basemap swap, in its own effect so it never rebuilds the map.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || appliedBasemapRef.current === basemap) return;
    appliedBasemapRef.current = basemap;
    map.setStyle(BASEMAPS[basemap]);
  }, [basemap, ready]);

  if (!token) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-sm text-muted-foreground">
        The map needs <code className="font-mono">NEXT_PUBLIC_MAPBOX_TOKEN</code>.
      </div>
    );
  }

  const legendBands = bands ? (datum === "subsea" ? [...bands].reverse() : bands) : [];
  const legend = layers
    ? datum === "subsea"
      ? { left: layers.meta.max, right: layers.meta.min }
      : { left: layers.meta.min, right: layers.meta.max }
    : null;

  return (
    <div className="relative min-h-0 flex-1 overflow-hidden">
      <div ref={containerRef} className="h-full w-full" />
      {!drawn && !error && (
        <div className="absolute inset-0 z-10 flex bg-background">
          <LoadingScreen label="Loading map" />
        </div>
      )}
      {error && (
        <div className="absolute inset-x-0 top-0 z-10 flex justify-center p-4">
          <div className="rounded-md border border-destructive/30 bg-background/95 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        </div>
      )}
      {loading && drawn && !error && (
        <div className="absolute inset-x-0 top-0 z-10 flex justify-center p-4">
          <div className="rounded-md border bg-background/95 px-3 py-2 text-sm text-muted-foreground">Loading layers</div>
        </div>
      )}
      {legend && (
        <div className="absolute bottom-4 left-4 z-10 rounded-md border bg-background/95 px-3 py-2 text-xs shadow-sm">
          <div className="mb-1 font-medium">{legendTitle}</div>
          <div
            className="h-2.5 w-48 rounded-sm"
            style={{
              background: `linear-gradient(to right, ${legendBands
                .map((b, i) => `${b.color} ${(i / legendBands.length) * 100}% ${((i + 1) / legendBands.length) * 100}%`)
                .join(", ")})`,
            }}
          />
          <div className="mt-1 flex justify-between tabular-nums text-muted-foreground">
            <span>{formatFeet(legend.left)}</span>
            <span>{formatFeet(legend.right)}</span>
          </div>
        </div>
      )}
      {drawn && (
        <MapControls
          basemap={basemap}
          onBasemap={setBasemap}
          onZoomIn={() => mapRef.current?.zoomIn()}
          onZoomOut={() => mapRef.current?.zoomOut()}
        />
      )}
    </div>
  );
}
