"use client";

import { GlobeIcon, MapIcon, MinusIcon, PlusIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * The basemap toggle and zoom bar from wildcat src/components/scout/map-controls.tsx,
 * without Recon's draw-tool rail. Icons are lucide's equivalents of the
 * Untitled UI ones Wildcat uses.
 */

export const BASEMAPS = {
  map: "mapbox://styles/mapbox/light-v11",
  satellite: "mapbox://styles/mapbox/satellite-streets-v12",
} as const;

export type Basemap = keyof typeof BASEMAPS;

export const DEFAULT_BASEMAP: Basemap = "satellite";

export function MapControls({
  basemap,
  onBasemap,
  onZoomIn,
  onZoomOut,
}: {
  basemap: Basemap;
  onBasemap: (b: Basemap) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
}) {
  const satellite = basemap === "satellite";
  return (
    <div className="absolute right-3 bottom-8 z-10 flex items-center gap-1.5">
      <div className="flex items-center overflow-hidden rounded-md border bg-background shadow-sm">
        <Button
          type="button"
          size="sm"
          variant={satellite ? "ghost" : "secondary"}
          className={cn("h-8 gap-1.5 rounded-none px-2.5", !satellite && "font-medium")}
          aria-pressed={!satellite}
          onClick={() => onBasemap("map")}
        >
          <MapIcon className="size-3.5" />
          Map
        </Button>
        <div aria-hidden className="h-5 w-px bg-border" />
        <Button
          type="button"
          size="sm"
          variant={satellite ? "secondary" : "ghost"}
          className={cn("h-8 gap-1.5 rounded-none px-2.5", satellite && "font-medium")}
          aria-pressed={satellite}
          onClick={() => onBasemap("satellite")}
        >
          <GlobeIcon className="size-3.5" />
          Satellite
        </Button>
      </div>

      <div className="flex items-center overflow-hidden rounded-md border bg-background shadow-sm">
        <Button
          type="button"
          size="icon-sm"
          variant="ghost"
          className="h-8 w-8 rounded-none"
          aria-label="Zoom out"
          onClick={onZoomOut}
        >
          <MinusIcon className="size-4" />
        </Button>
        <div aria-hidden className="h-5 w-px bg-border" />
        <Button
          type="button"
          size="icon-sm"
          variant="ghost"
          className="h-8 w-8 rounded-none"
          aria-label="Zoom in"
          onClick={onZoomIn}
        >
          <PlusIcon className="size-4" />
        </Button>
      </div>
    </div>
  );
}
