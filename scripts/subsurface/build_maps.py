# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "numpy",
#   "scipy",
#   "verde>=1.8",
#   "numba",
#   "xtgeo>=4",
#   "psycopg[binary]>=3.2",
# ]
# ///
"""
Subsurface maps from a Petra-style tops export, built offline.

    uv run scripts/subsurface/build_maps.py            # or: npm run build:subsurface
    uv run scripts/subsurface/build_maps.py --refresh-locations

Reads the fixed-width tops file, places each well from the RRC mirror
(`rrc.well_location`, cached to `data/subsurface/well-locations.csv` so a
rebuild never touches the database), grids each formation's subsea tops with
verde, derives isopachs grid-to-grid with xtgeo, and writes one JSON per map to
`data/subsurface/maps/` plus an `index.json`. The /map page reads those files;
it contours and colours them with the same code Wildcat's structure maps use.

Kept out of `api/` on purpose: requirements.txt pins the deployed Python to the
standard library, and gridding needs numpy and scipy.

Conventions match Wildcat's structure maps (src/lib/structure-maps):
- One local equirectangular frame in feet, x east and y north, centred on the
  wells (`geo.ts`). Every map shares it, so isopach grids align cell for cell.
- `values` is row-major, `values[j * nx + i]`, j increasing northward, finite
  everywhere; `mask` says which cells are within reach of a well.
- Masking differs: Wildcat masks beyond 1.5 x the MEDIAN well spacing, which
  on this file (median about 1,100 ft, wells in clusters miles apart) cut the
  map into a disc around each well. Here it is 1.5 x the 90th-percentile
  spacing, so the surface spans the gaps nine wells in ten have to a neighbour
  and stops at the larger gaps between fields.
- The colour ramp spans the 2nd to 98th percentile of the masked grid, so one
  bad pick's bullseye does not flatten the rest of the map. Contours still run
  over the full range.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import math
import os
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import verde as vd
import xtgeo
from scipy.spatial import cKDTree

# verde 1.x deprecation notices, raised once per CV fold: SplineCV still passes
# the old `mindist` through, and R² (what this script reports) stops being the
# default scorer in 2.0. Neither changes this build.
warnings.filterwarnings("ignore", category=FutureWarning, module="verde")

ROOT = Path(__file__).resolve().parents[2]
TOPS_FILE = ROOT / "WildcatIQ-tops (1).TXT"
OUT_DIR = ROOT / "data" / "subsurface"
MAPS_DIR = OUT_DIR / "maps"
LOCATIONS_CSV = OUT_DIR / "well-locations.csv"

# Feet per degree of latitude, the constant in Wildcat's geo.ts.
FT_PER_DEG_LAT = 364_000.0
CELL_FT = 500.0
# Grid padding beyond the outermost wells. Larger than any formation's mask
# radius, so a mask is never clipped by the grid edge.
PAD_FT = 10_560.0
MASK_NN_QUANTILE = 0.9
MASK_NN_FACTOR = 1.5
# Candidate spline dampings; SplineCV picks one per formation by block k-fold.
DAMPINGS = (1e-8, 1e-6, 1e-4, 1e-2)

# Column layout of the export, 0-based [start, end). The header labels are not
# aligned with their data (they are centred and the formation names are cut to
# 12 characters), so the layout is fixed here and checked against the header.
UWI = (0, 20)
OPER = (20, 40)
LEASE = (40, 60)
WELLNO = (60, 83)
DATUM = (83, 92)
TOP_WIDTH = 12
TOP_START = 92


@dataclass(frozen=True)
class Formation:
    id: str
    name: str
    header: str  # the header text at this column, as the export truncates it


# Shallow to deep, in column order.
FORMATIONS = [
    Formation("caddo", "Caddo", "CADDO"),
    Formation("marble-falls", "Marble Falls", "MARBLE_FALLS"),
    Formation("barnett", "Barnett", "BARNETT"),
    Formation("miss-lime", "Miss Lime", "MISS_LS"),
]


@dataclass
class Well:
    uwi: str
    api10: str | None
    operator: str
    lease: str
    well_no: str
    datum: float | None
    tops_md: dict[str, float]


def field(line: str, span: tuple[int, int]) -> str:
    return line[span[0] : span[1]].strip()


def parse_number(text: str) -> float | None:
    try:
        return float(text) if text else None
    except ValueError:
        return None


def parse_tops(path: Path) -> list[Well]:
    lines = path.read_text(encoding="latin-1").replace("\r", "").split("\n")
    header = lines[0]
    for k, f in enumerate(FORMATIONS):
        start = TOP_START + k * TOP_WIDTH
        if not header[start : start + TOP_WIDTH].strip().startswith(f.header):
            sys.exit(f"Header does not have {f.header} at column {start + 1}: the export layout changed.")
    wells: list[Well] = []
    for line in lines[2:]:
        if not line.strip():
            continue
        uwi = field(line, UWI)
        digits = uwi.replace("-", "")
        api10 = digits if len(digits) == 10 and digits.isdigit() and digits.startswith("42") else None
        tops = {}
        for k, f in enumerate(FORMATIONS):
            start = TOP_START + k * TOP_WIDTH
            v = parse_number(line[start : start + TOP_WIDTH].strip())
            if v is not None:
                tops[f.id] = v
        datum = parse_number(field(line, DATUM))
        wells.append(
            Well(
                uwi=uwi,
                api10=api10,
                operator=field(line, OPER),
                lease=field(line, LEASE),
                well_no=field(line, WELLNO),
                datum=datum if datum and datum > 0 else None,
                tops_md=tops,
            )
        )
    return wells


def read_env(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    env = ROOT / ".env"
    if not env.exists():
        return None
    for line in env.read_text().splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"')
    return None


def load_locations(apis: list[str], refresh: bool) -> dict[str, tuple[float, float]]:
    """api10 -> (lat, lon). The mirror keys wells by county + unique number
    (8 digits, no state code); `distinct on` + `reliability` is its own rule
    for choosing among a wellbore's recorded points (Wildcat's locate.ts)."""
    if LOCATIONS_CSV.exists() and not refresh:
        with LOCATIONS_CSV.open() as fh:
            return {r["api10"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(fh)}

    import psycopg

    url = read_env("RRC_DATABASE_URL")
    if not url:
        sys.exit("RRC_DATABASE_URL is not set and there is no cached well-locations.csv.")
    keys = sorted({a[2:] for a in apis})
    with psycopg.connect(url, options="-c default_transaction_read_only=on") as conn:
        rows = conn.execute(
            """select distinct on (api_number) btrim(api_number), lat, lon
                 from rrc.well_location
                where btrim(api_number) = any(%s) and lat is not null and lon is not null
                order by api_number, reliability""",
            (keys,),
        ).fetchall()
    out = {"42" + api: (float(lat), float(lon)) for api, lat, lon in rows}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with LOCATIONS_CSV.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["api10", "lat", "lon"])
        for api in sorted(out):
            w.writerow([api, out[api][0], out[api][1]])
    return out


@dataclass
class Frame:
    lng0: float
    lat0: float

    @property
    def ft_per_deg_lng(self) -> float:
        return FT_PER_DEG_LAT * math.cos(math.radians(self.lat0))

    def to_local(self, lng: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return (lng - self.lng0) * self.ft_per_deg_lng, (lat - self.lat0) * FT_PER_DEG_LAT


@dataclass
class GridSpec:
    nx: int
    ny: int
    origin_x: float
    origin_y: float
    cell: float

    def coords(self) -> tuple[np.ndarray, np.ndarray]:
        xs = self.origin_x + np.arange(self.nx) * self.cell
        ys = self.origin_y + np.arange(self.ny) * self.cell
        return np.meshgrid(xs, ys)  # shape (ny, nx): row j is northing j


def nn_quantile(x: np.ndarray, y: np.ndarray, q: float) -> float:
    """Quantile of each well's distance to its nearest other well."""
    pts = np.column_stack([x, y])
    d, _ = cKDTree(pts).query(pts, k=2)
    nn = d[:, 1]
    nn = nn[nn > 0]
    return float(np.quantile(nn, q)) if len(nn) else CELL_FT


@dataclass
class Surface:
    values: np.ndarray  # (ny, nx), finite everywhere
    mask: np.ndarray  # (ny, nx) bool, True = within reach of a well
    damping: float | None
    cv_score: float | None
    control: int  # distinct block-reduced locations
    max_distance: float


def grid_formation(x: np.ndarray, y: np.ndarray, z: np.ndarray, spec: GridSpec) -> Surface:
    """Planar trend plus a biharmonic spline on the residual, damping chosen by
    block k-fold cross-validation. Wells closer than a cell are merged to their
    median first, so two picks at one pad cannot fight."""
    (bx, by), bz = vd.BlockReduce(np.median, spacing=spec.cell).filter((x, y), z)
    spline = vd.SplineCV(dampings=DAMPINGS, cv=vd.BlockKFold(spacing=10 * spec.cell, n_splits=5, shuffle=True, random_state=0))
    chain = vd.Chain([("trend", vd.Trend(degree=1)), ("spline", spline)])
    chain.fit((bx, by), bz)
    gx, gy = spec.coords()
    values = chain.predict((gx, gy))
    maxdist = MASK_NN_FACTOR * nn_quantile(bx, by, MASK_NN_QUANTILE)
    if maxdist > PAD_FT:
        sys.exit(f"Mask radius {maxdist:.0f} ft exceeds the grid padding {PAD_FT:.0f} ft; raise PAD_FT.")
    mask = vd.distance_mask((bx, by), maxdist=maxdist, coordinates=(gx, gy))
    fitted = chain.named_steps["spline"]
    return Surface(
        values=np.asarray(values, dtype=np.float64),
        mask=np.asarray(mask, dtype=bool),
        damping=getattr(fitted, "damping_", None),
        cv_score=float(np.max(fitted.scores_)) if getattr(fitted, "scores_", None) is not None else None,
        control=len(bz),
        max_distance=maxdist,
    )


def to_xtgeo(s: Surface, spec: GridSpec) -> xtgeo.RegularSurface:
    # xtgeo indexes values[i, j] (column = easting first); ours are [j, i].
    return xtgeo.RegularSurface(
        ncol=spec.nx,
        nrow=spec.ny,
        xinc=spec.cell,
        yinc=spec.cell,
        xori=spec.origin_x,
        yori=spec.origin_y,
        values=np.ma.array(s.values.T, mask=~s.mask.T),
    )


def isopach(upper: Surface, lower: Surface, spec: GridSpec) -> Surface:
    """Thickness = upper subsea - lower subsea, grid to grid (Petra's isopach
    method 3). xtgeo masks the result to cells both surfaces cover; `fill`
    then extrapolates under the mask so the contour geometry stays clean at
    the edge, the same reason the structure grids are finite everywhere."""
    thick = to_xtgeo(upper, spec)
    thick.subtract(to_xtgeo(lower, spec))
    mask = ~np.ma.getmaskarray(thick.values).T
    thick.fill()
    return Surface(
        values=np.asarray(thick.values.filled(np.nan)).T.astype(np.float64),
        mask=mask,
        damping=None,
        cv_score=None,
        control=min(upper.control, lower.control),
        max_distance=min(upper.max_distance, lower.max_distance),
    )


def b64(arr: np.ndarray, dtype) -> str:
    return base64.b64encode(np.ascontiguousarray(arr, dtype=dtype).tobytes()).decode("ascii")


def write_map(
    map_id: str,
    name: str,
    kind: str,
    s: Surface,
    spec: GridSpec,
    frame: Frame,
    posts: list[dict],
    contour_interval: float,
    note: dict,
) -> dict:
    inside = s.values[s.mask]
    meta = {
        "id": map_id,
        "name": name,
        "kind": kind,
        "wells": len(posts),
        "control": s.control,
        "min": float(inside.min()),
        "max": float(inside.max()),
        "colorMin": float(np.quantile(inside, 0.02)),
        "colorMax": float(np.quantile(inside, 0.98)),
        "contourIntervalFt": contour_interval,
        "damping": s.damping,
        "cvScore": s.cv_score,
        **note,
    }
    doc = {
        **meta,
        "frame": {"lng0": frame.lng0, "lat0": frame.lat0, "ftPerDegLng": frame.ft_per_deg_lng},
        "nx": spec.nx,
        "ny": spec.ny,
        "cellFt": spec.cell,
        "originX": spec.origin_x,
        "originY": spec.origin_y,
        "maxDistanceFt": s.max_distance,
        "values": b64(s.values.ravel(), "<f4"),
        "mask": b64(s.mask.ravel(), np.uint8),
        "posts": posts,
    }
    (MAPS_DIR / f"{map_id}.json").write_text(json.dumps(doc))
    return meta


def well_name(w: Well) -> str:
    return " ".join(p for p in [w.lease or w.operator, w.well_no] if p).strip() or w.uwi


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tops", type=Path, default=TOPS_FILE)
    ap.add_argument("--refresh-locations", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    wells = parse_tops(args.tops)
    apis = [w.api10 for w in wells if w.api10]
    located = load_locations(apis, args.refresh_locations)
    placed = [w for w in wells if w.api10 in located and w.datum is not None]
    print(f"{len(wells)} wells in file, {len(apis)} with an API number, {len(placed)} located with a datum")

    lat = np.array([located[w.api10][0] for w in placed])
    lng = np.array([located[w.api10][1] for w in placed])
    frame = Frame(lng0=float(lng.mean()), lat0=float(lat.mean()))
    x, y = frame.to_local(lng, lat)

    # One grid for every map, so isopachs subtract cell for cell.
    pad = PAD_FT
    nx = int(math.ceil((x.max() - x.min() + 2 * pad) / CELL_FT)) + 1
    ny = int(math.ceil((y.max() - y.min() + 2 * pad) / CELL_FT)) + 1
    spec = GridSpec(nx=nx, ny=ny, origin_x=float(x.min() - pad), origin_y=float(y.min() - pad), cell=CELL_FT)
    print(f"grid {nx} x {ny} at {CELL_FT:.0f} ft")

    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    for old in MAPS_DIR.glob("*.json"):
        old.unlink()

    index = []
    surfaces: dict[str, Surface] = {}
    for f in FORMATIONS:
        sel = [k for k, w in enumerate(placed) if f.id in w.tops_md]
        z = np.array([placed[k].datum - placed[k].tops_md[f.id] for k in sel])
        s = grid_formation(x[sel], y[sel], z, spec)
        surfaces[f.id] = s
        posts = [
            {"id": placed[k].uwi, "name": well_name(placed[k]), "lng": float(lng[k]), "lat": float(lat[k]), "value": float(v)}
            for k, v in zip(sel, z)
        ]
        index.append(write_map(f.id, f.name, "structure", s, spec, frame, posts, 25.0, {"formation": f.name}))
        print(f"  {f.name}: {len(sel)} wells, {s.control} control points, damping {s.damping}, R2 {s.cv_score:.3f}")

    for upper, lower in zip(FORMATIONS, FORMATIONS[1:]):
        s = isopach(surfaces[upper.id], surfaces[lower.id], spec)
        sel = [k for k, w in enumerate(placed) if upper.id in w.tops_md and lower.id in w.tops_md]
        posts = [
            {
                "id": placed[k].uwi,
                "name": well_name(placed[k]),
                "lng": float(lng[k]),
                "lat": float(lat[k]),
                "value": float(placed[k].tops_md[lower.id] - placed[k].tops_md[upper.id]),
            }
            for k in sel
        ]
        map_id = f"{upper.id}-to-{lower.id}"
        index.append(
            write_map(map_id, f"{upper.name} to {lower.name}", "isopach", s, spec, frame, posts, 10.0, {"upper": upper.name, "lower": lower.name})
        )
        print(f"  {upper.name} to {lower.name}: {len(sel)} wells")

    summary = {
        "source": args.tops.name,
        "wellsInFile": len(wells),
        "withApi": len(apis),
        "placed": len(placed),
        "cellFt": CELL_FT,
        "maps": index,
    }
    (MAPS_DIR / "index.json").write_text(json.dumps(summary, indent=2))
    print(f"wrote {len(index)} maps to {MAPS_DIR.relative_to(ROOT)} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
