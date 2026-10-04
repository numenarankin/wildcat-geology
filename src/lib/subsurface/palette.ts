// Copied from wildcat src/lib/structure-maps/palette.ts, plus three ramps for
// the banded fill: `redblue` (the default; diverging, structural highs red and
// lows blue, white between), `earth` (teal through green, yellow and orange to
// red, deep to shallow) and `rainbow` (full spectrum, a Petra / Kingdom fill).
/**
 * Colour ramps for a structure map, shared by the server (which only stores
 * the choice) and the client (which hands the stops to Mapbox).
 *
 * Every ramp is listed SHALLOW to DEEP. A structure map is drawn in subsea
 * feet, where deeper is a smaller number, so the client reverses the ramp
 * along the value axis: the largest value (structurally highest) takes the
 * first stop. The convention geologists expect on a structure map is warm on
 * the high, cool on the low, which is what `spectral` gives.
 */

export type PaletteId = "redblue" | "earth" | "rainbow" | "spectral" | "terrain" | "viridis" | "grey";

export interface Palette {
  id: PaletteId;
  label: string;
  /** Evenly spaced hex stops, shallow (structural high) first. */
  stops: string[];
}

export const PALETTES: Record<PaletteId, Palette> = {
  redblue: {
    id: "redblue",
    label: "Red-blue",
    stops: ["#8b1a1a", "#b8432f", "#d6714f", "#e9a07e", "#f5cdb4", "#f2ece6", "#c9dcea", "#97bfdb", "#5c97c4", "#2e6aa3", "#0b3a6e"],
  },
  earth: {
    id: "earth",
    label: "Earth",
    stops: ["#d7402a", "#ec7a3c", "#f6ad5a", "#fbd77e", "#f3ef9b", "#cfe6a0", "#9fd39c", "#6fbf9b", "#3f9f98", "#1f7a8c"],
  },
  rainbow: {
    id: "rainbow",
    label: "Rainbow",
    stops: ["#d7191c", "#f46d00", "#ffb000", "#ffff00", "#7fd400", "#00b050", "#00c0c0", "#0080ff", "#0030c0", "#6a00b0", "#b000b0"],
  },
  spectral: {
    id: "spectral",
    label: "Spectral",
    stops: ["#9e0142", "#d53e4f", "#f46d43", "#fdae61", "#fee08b", "#e6f598", "#abdda4", "#66c2a5", "#3288bd", "#5e4fa2"],
  },
  terrain: {
    id: "terrain",
    label: "Terrain",
    stops: ["#ffffff", "#c9b47c", "#8c6d3f", "#5a8f3c", "#2f6b3a", "#1e5f7a", "#163e6b", "#0d2352"],
  },
  viridis: {
    id: "viridis",
    label: "Viridis",
    stops: ["#fde725", "#b5de2b", "#6ece58", "#35b779", "#1f9e89", "#26828e", "#31688e", "#3e4989", "#482878", "#440154"],
  },
  grey: {
    id: "grey",
    label: "Grey",
    stops: ["#f5f5f5", "#bdbdbd", "#737373", "#252525"],
  },
};

export const PALETTE_IDS = Object.keys(PALETTES) as PaletteId[];
export const DEFAULT_PALETTE: PaletteId = "redblue";

export function isPaletteId(v: unknown): v is PaletteId {
  return typeof v === "string" && v in PALETTES;
}
