// Copied verbatim from wildcat src/lib/structure-maps/png.ts. Keep in sync.
import { deflateSync } from "node:zlib";
import type { DepthGrid } from "./grid";

/**
 * The depth grid as a PNG Mapbox can colour on the GPU.
 *
 * Mapbox's `raster-color` colours an image by a value it computes per pixel as
 * `mix.r * R + mix.g * G + mix.b * B + mix.a` over 0..255 channels, the same
 * trick Terrain-RGB uses for elevation. The grid value is scaled to a 16-bit
 * integer over [min, max] and split across R (high byte) and G (low byte), so
 * the client decodes it with `raster-color-mix: [256, 1, 0, 0]` and a
 * `raster-color-range` of [0, 65535]. The page maps a colour ramp onto that
 * range and reads depths back with the min/max in the grid's metadata.
 *
 * Every pixel carries its value, including masked ones, so bilinear
 * resampling at the mask edge blends real depths rather than black; only the
 * alpha channel says where the data stops.
 */

export const VALUE_SCALE = 65535;

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(buf: Buffer): number {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type: string, data: Buffer): Buffer {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const typeBuf = Buffer.from(type, "ascii");
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([len, typeBuf, data, crc]);
}

/** Encode RGBA pixels (row 0 at the top) as a PNG. */
export function encodePng(width: number, height: number, rgba: Uint8Array): Buffer {
  const stride = width * 4;
  const raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y++) {
    raw[y * (stride + 1)] = 0; // filter type: none
    raw.set(rgba.subarray(y * stride, (y + 1) * stride), y * (stride + 1) + 1);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // colour type: RGBA
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", deflateSync(raw)),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

/** Scale a depth to the 16-bit raster value over the grid's [min, max]. */
export function encodeValue(v: number, min: number, max: number): number {
  const span = max - min;
  if (!(span > 0)) return 0;
  const t = (v - min) / span;
  return Math.max(0, Math.min(VALUE_SCALE, Math.round(t * VALUE_SCALE)));
}

/** The grid as a PNG, north row first, masked cells transparent. */
export function gridToPng(g: DepthGrid): Buffer {
  const rgba = new Uint8Array(g.nx * g.ny * 4);
  for (let j = 0; j < g.ny; j++) {
    const row = g.ny - 1 - j; // image row 0 is the northernmost grid row
    for (let i = 0; i < g.nx; i++) {
      const k = j * g.nx + i;
      const v = encodeValue(g.values[k], g.min, g.max);
      const o = (row * g.nx + i) * 4;
      rgba[o] = v >> 8;
      rgba[o + 1] = v & 0xff;
      rgba[o + 2] = 0;
      rgba[o + 3] = g.mask[k] ? 255 : 0;
    }
  }
  return encodePng(g.nx, g.ny, rgba);
}
