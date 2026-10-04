// Copied verbatim from wildcat src/lib/structure-maps/geo.ts. Keep in sync.
/**
 * Local planar frame for a structure map. A map covers a field or a county, a
 * few tens of miles at most, so an equirectangular projection centred on the
 * wells is flat enough: x runs east in feet, y runs north in feet, and lines of
 * constant x / y are lines of constant longitude / latitude. That last property
 * is what lets the raster be placed on Mapbox by its four lng/lat corners.
 */

/** Feet per degree of latitude (WGS84 mean). */
export const FT_PER_DEG_LAT = 364_000;

export interface LocalFrame {
  /** Longitude / latitude the frame is centred on. */
  lng0: number;
  lat0: number;
  /** Feet per degree of longitude at lat0. */
  ftPerDegLng: number;
}

export function makeFrame(lng0: number, lat0: number): LocalFrame {
  return {
    lng0,
    lat0,
    ftPerDegLng: FT_PER_DEG_LAT * Math.cos((lat0 * Math.PI) / 180),
  };
}

export function toLocal(f: LocalFrame, lng: number, lat: number): [number, number] {
  return [(lng - f.lng0) * f.ftPerDegLng, (lat - f.lat0) * FT_PER_DEG_LAT];
}

export function toLngLat(f: LocalFrame, x: number, y: number): [number, number] {
  return [f.lng0 + x / f.ftPerDegLng, f.lat0 + y / FT_PER_DEG_LAT];
}
