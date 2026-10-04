"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
} from "@/components/ui/select";
import type {
  Corners,
  GridFrame,
  SubsurfaceMapMeta,
} from "@/lib/subsurface/maps";
import {
  DEFAULT_PALETTE,
  PALETTES,
  PALETTE_IDS,
  type PaletteId,
} from "@/lib/subsurface/palette";
import {
  SubsurfaceMapCanvas,
  formatFeet,
  type SubsurfaceMapLayers,
} from "./subsurface-map-canvas";

/*
 * The bar's furniture, copied from wildcat
 * src/components/structure-maps/structure-map-workspace.tsx (BarField,
 * Divider, FeetInput), which copies it from Recon's control bar.
 */

function BarField({
  label,
  children,
}: {
  label?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex shrink-0 items-center gap-1.5">
      {label && (
        <span className="text-[11px] font-medium text-muted-foreground">
          {label}
        </span>
      )}
      {children}
    </div>
  );
}

/** Client-only: deck.gl needs WebGL and the viewer starts workers on import. */
const Subsurface3DView = dynamic(() => import("./subsurface-3d-view"), {
  ssr: false,
});

function Divider() {
  return <div aria-hidden className="h-5 w-px shrink-0 bg-border" />;
}

function Seg<T extends string>({
  value,
  options,
  onSelect,
}: {
  value: T;
  options: { label: string; v: T }[];
  onSelect: (v: T) => void;
}) {
  return (
    <div className="flex gap-1">
      {options.map((o) => (
        <Button
          key={o.v}
          size="sm"
          variant={value === o.v ? "default" : "outline"}
          onClick={() => onSelect(o.v)}
        >
          {o.label}
        </Button>
      ))}
    </div>
  );
}

/** A number the bar commits on blur or Enter, so typing "20" on the way to
 * "200" does not refetch the contours per keystroke. */
function FeetInput({
  value,
  onCommit,
  label,
  min,
  max,
}: {
  value: number;
  onCommit: (v: number) => void;
  label: string;
  min: number;
  max: number;
}) {
  const [text, setText] = useState(String(value));
  const [synced, setSynced] = useState(value);
  if (synced !== value) {
    setSynced(value);
    setText(String(value));
  }
  function commit() {
    const n = Number(text.replace(/,/g, ""));
    if (!Number.isFinite(n) || n === value) {
      setText(String(value));
      return;
    }
    onCommit(Math.min(max, Math.max(min, n)));
  }
  return (
    <Input
      type="text"
      inputMode="numeric"
      autoComplete="off"
      aria-label={label}
      value={text}
      onChange={(e) => setText(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") (e.target as HTMLInputElement).blur();
      }}
      className="h-7 w-20 text-xs tabular-nums"
    />
  );
}

/**
 * The /map page: Wildcat's structure-map layout (a control bar over the map)
 * showing the maps `npm run build:subsurface` built from the tops file. Maps
 * are read-only here; the bar picks one, sets its contour interval, and
 * colours it.
 */
export function SubsurfaceMapWorkspace({
  maps,
  corners,
  frame,
}: {
  maps: SubsurfaceMapMeta[];
  corners: Corners;
  frame: GridFrame | null;
}) {
  const [view, setView] = useState<"2d" | "3d">("2d");
  const [verticalScale, setVerticalScale] = useState(50);
  const [resetCount, setResetCount] = useState(0);
  const [shown3d, setShown3d] = useState<string[]>(() =>
    maps.filter((m) => m.kind === "structure").map((m) => m.id),
  );
  const [selectedId, setSelectedId] = useState(maps[0]?.id ?? null);
  const selected = maps.find((m) => m.id === selectedId) ?? null;
  const [intervals, setIntervals] = useState<Record<string, number>>({});
  const [palette, setPalette] = useState<PaletteId>(DEFAULT_PALETTE);
  const interval = selected
    ? (intervals[selected.id] ?? selected.contourIntervalFt)
    : 0;

  const layers = useMemo<SubsurfaceMapLayers | null>(() => {
    if (!selected) return null;
    const base = `/map/layers/${encodeURIComponent(selected.id)}`;
    return {
      rasterUrl: `${base}/raster.png`,
      contoursUrl: `${base}/contours.json?interval=${interval}`,
      meta: {
        corners,
        min: selected.colorMin,
        max: selected.colorMax,
        intervalFt: interval,
      },
    };
  }, [selected, interval, corners]);

  const structures = maps.filter((m) => m.kind === "structure");
  const surfaces3d = structures.filter((m) => shown3d.includes(m.id));
  const interval3d = intervals.__3d ?? 25;
  const isopachs = maps.filter((m) => m.kind === "isopach");

  return (
    <div className="flex h-full w-full flex-col">
      <div className="relative z-20 flex shrink-0 flex-col border-b border-border bg-background">
        <div className="flex min-h-11 flex-wrap items-center gap-x-2 gap-y-3 px-3 py-2">
          <BarField label="View">
            <Seg
              value={view}
              onSelect={setView}
              options={[
                { label: "2D", v: "2d" },
                { label: "3D", v: "3d" },
              ]}
            />
          </BarField>
          <Divider />
          {view === "3d" ? (
            <>
              <BarField label="Surfaces">
                <div className="flex gap-1">
                  {structures.map((m) => {
                    const on = shown3d.includes(m.id);
                    return (
                      <Button
                        key={m.id}
                        size="sm"
                        variant={on ? "default" : "outline"}
                        aria-pressed={on}
                        onClick={() =>
                          setShown3d((prev) =>
                            on
                              ? prev.length > 1
                                ? prev.filter((id) => id !== m.id)
                                : prev
                              : structures
                                  .map((x) => x.id)
                                  .filter(
                                    (id) => id === m.id || prev.includes(id),
                                  ),
                          )
                        }
                      >
                        {m.name}
                      </Button>
                    );
                  })}
                </div>
              </BarField>
              <Divider />
              <BarField label="Vertical ×">
                <FeetInput
                  label="Vertical exaggeration"
                  value={verticalScale}
                  min={1}
                  max={500}
                  onCommit={setVerticalScale}
                />
              </BarField>
              <Button size="sm" variant="outline" onClick={() => setResetCount((n) => n + 1)}>
                Reset view
              </Button>
              <BarField label="Interval ft">
                <FeetInput
                  label="Contour interval, feet"
                  value={interval3d}
                  min={5}
                  max={1000}
                  onCommit={(v) =>
                    setIntervals((prev) => ({ ...prev, __3d: v }))
                  }
                />
              </BarField>
              <BarField label="Colors">
                <Select
                  value={palette}
                  onValueChange={(v) => v && setPalette(v as PaletteId)}
                >
                  <SelectTrigger className="h-7 w-28 text-xs">
                    <span>{PALETTES[palette].label}</span>
                  </SelectTrigger>
                  <SelectContent>
                    {PALETTE_IDS.map((id) => (
                      <SelectItem key={id} value={id}>
                        {PALETTES[id].label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </BarField>
            </>
          ) : (
            <>
              <BarField label="Map">
                <Select
                  value={selectedId ?? ""}
                  onValueChange={(v) => v && setSelectedId(v)}
                >
                  <SelectTrigger className="h-7 w-56 text-xs">
                    <span className="truncate">
                      {selected
                        ? `${selected.name}${selected.kind === "isopach" ? " isopach" : ""}`
                        : "Choose a map"}
                    </span>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectLabel>Structure</SelectLabel>
                      {structures.map((m) => (
                        <SelectItem key={m.id} value={m.id}>
                          {m.name}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                    <SelectGroup>
                      <SelectLabel>Isopach</SelectLabel>
                      {isopachs.map((m) => (
                        <SelectItem key={m.id} value={m.id}>
                          {m.name}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </BarField>

              {selected && (
                <>
                  <Divider />
                  <BarField label="Interval ft">
                    <FeetInput
                      label="Contour interval, feet"
                      value={interval}
                      min={5}
                      max={1000}
                      onCommit={(v) =>
                        setIntervals((prev) => ({ ...prev, [selected.id]: v }))
                      }
                    />
                  </BarField>
                  <BarField label="Colors">
                    <Select
                      value={palette}
                      onValueChange={(v) => v && setPalette(v as PaletteId)}
                    >
                      <SelectTrigger className="h-7 w-28 text-xs">
                        <span>{PALETTES[palette].label}</span>
                      </SelectTrigger>
                      <SelectContent>
                        {PALETTE_IDS.map((id) => (
                          <SelectItem key={id} value={id}>
                            {PALETTES[id].label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </BarField>
                </>
              )}
            </>
          )}

          {view === "2d" && selected && (
            <div className="ml-auto flex shrink-0 items-center gap-2">
              <span className="text-xs tabular-nums text-muted-foreground">
                {selected.wells.toLocaleString()} wells ·{" "}
                {formatFeet(Math.min(selected.min, selected.max))} to{" "}
                {formatFeet(Math.max(selected.min, selected.max))}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="relative flex min-h-0 flex-1 flex-col">
        {maps.length === 0 && (
          <div className="absolute inset-x-0 top-0 z-10 flex justify-center p-4">
            <div className="rounded-md border bg-background/95 px-3 py-2 text-sm text-muted-foreground">
              No maps built yet. Run npm run build:subsurface.
            </div>
          </div>
        )}
        {view === "3d" && frame ? (
          <Subsurface3DView
            surfaces={surfaces3d}
            frame={frame}
            palette={palette}
            intervalFt={interval3d}
            verticalScale={verticalScale}
            resetCount={resetCount}
          />
        ) : (
          <SubsurfaceMapCanvas
            layers={layers}
            palette={palette}
            datum="subsea"
            legendTitle={selected?.kind === "isopach" ? "Thickness" : "Subsea"}
            loading={false}
            error={null}
          />
        )}
      </div>
    </div>
  );
}
