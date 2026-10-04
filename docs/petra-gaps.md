# Petra gap analysis

What Petra does that Wildcat and this repo do not, and which open-source package (if any) fills
each gap during prototyping. Companion to [petra-functionality.md](petra-functionality.md).

## Ground rules

- **Prototype phase.** GPL code (QGIS, OpendTect) is acceptable now; anything GPL that ships
  gets a written replacement later. Each gap below notes the license of its stand-in.
- **Already covered, not gaps:** Mapbox map rendering, raster log calibration and
  digitizing, production data and decline / EUR.
- **Method.** Coverage was checked by searching the Wildcat source (`~/dev/wildcat/src`) for
  each Petra feature, not by running the app. Open-source coverage comes from each repo's
  README and source in `vendor/`.

## What Wildcat already has

| Petra area | Wildcat today | Where |
|---|---|---|
| Structure maps | Tops gridded by TPS or IDW, contoured, rendered on Mapbox; subsea or TVD datum; KB elevation resolved per well | `src/lib/structure-maps/` (`grid.ts`, `contours.ts`, `data.ts`) |
| Raster log calibration and digitizing | Depth calibration, curve tracing, write to database | `src/lib/raster-log/` |
| Decline curves | Arps fits, decline plot, decline lab | `src/lib/wells/arps.ts`, `src/components/charts/decline-plot.tsx` |
| Petrophysics and reservoir engineering | 153 geology-agent Python tools, including `volumetrics`, `volumetrics_probabilistic`, `isopach`, `auto_correlate`, `md_to_tvd`, `crossplot_porosity`, `net_pay_cutoffs`, `curve_normalize`, `structural_dip`, `decline_eur` | `src/lib/ai/geology/tool-catalog.json` |

The agent tools are reachable only through chat. Several gaps below are "engine exists,
no screen".

## Gaps: nothing exists

### 1. Cross sections

**Petra:** single-well, well-to-well, line-and-wells and line-and-corridor sections;
structural or stratigraphic (flattened on a top); deviated wells, digital and raster logs,
tops, faults, perfs, cores, tests, production charts, user-drawn interpretation.

**Wildcat:** none.

**Open source:** xtgeo `RegularSurface.get_fence` / `get_randomline` return surface traces
along a section line; xtgeo `Well` gives log data along the path. The panel itself (log
tracks, correlation lines, hang-on-datum) has to be built.

**Priority:** largest gap. This is the screen Petra users live in, and it is the frame for
gap 2. It is third in the suggested order below only because it is a bigger build than the
two map fixes ahead of it.

### 2. Interactive tops picking and correlation

**Petra:** Log Correlation module (smooth scroll, slip boxes, stretch/squeeze), Slip Logs
(four raster logs side by side, align on a top, fault gaps), correlating tops directly on a
cross section, edits flowing to the map.

**Wildcat:** `auto_correlate` agent tool only; no hands-on picking.

**Open source:** none of the nine packages.

**Depends on:** gap 1 for the section view; the existing raster-log viewer for raster tracks.

### 3. Fault-aware gridding

**Petra:** faults digitized as overlay lines or polygons, then *Include Faults* at grid
time. Its default method (Highly Connected Features) and Disconnected Features both honor
faults.

**Wildcat:** TPS and IDW with no fault handling (`src/lib/structure-maps/grid.ts`).

**Open source:**

| Package | What it gives | Why it falls short |
|---|---|---|
| GMT `surface -D` | Soft breaklines | Pins nodes to a line; does not break the surface |
| GemPy (EUPL-1.2) | Faults in an implicit 3D model | Full 3D modeling; heavy for a structure map |
| verde, PyKrige, GSTools, xtgeo | Gridding | No fault input |

**Recommended build:** split control points into fault blocks using fault polygons, grid
each block separately, merge with the fault trace as the seam. Also needs a way to draw or
import fault traces on the map.

### 4. Seismic

**Petra:** shotpoint and horizon import (2D Seismic tool), PetraSeis for 2D/3D
interpretation, seismic cubes and horizons in 3D Viz, Kingdom link.

**Wildcat:** none.

**Open source:** xtgeo reads SEG-Y (via segyio, Apache-2.0) and slices surfaces through cubes
(LGPL-3.0). OpendTect (GPL-3.0) is the full interpretation reference; desktop only.

**Priority:** low for the current users (independent operators working from well control).

### 5. 3D visualization

**Petra:** wellbores, tops, logs, perfs, shows, grids, isopachs, map overlays, cross-section
panels and seismic in one rotatable scene.

**Wildcat:** none.

**Open source:** GemPy for a 3D structural model; xtgeo for 3D grids. Neither is a web
viewer; rendering needs a browser 3D library.

### 6. Directional well profiles and planning

**Petra:** plan horizontal and directional wells, profile view with logs, tops and surfaces
along the path, repeated tops along laterals fed back into gridding, lateral performance.

**Wildcat:** `md_to_tvd` agent tool and RRC directional survey data; no profile view or
planning.

**Open source:** xtgeo `Well` handles path geometry (`get_fence_polyline`,
`create_relative_hlen`, `get_surface_picks`, `get_zonation_points`). No planning tool.

### 7. Bubble and posted-data maps

**Petra:** bubble maps with up to 32 pie segments per well sized by value (cumulative
production, QC of which wells have a top picked); base maps with up to 50 posted data lines
per well.

**Wildcat:** none on the structure map.

**Open source:** not needed; Mapbox circle and symbol layers do this.

### 8. Group production plots

**Petra:** sum, average, or time-normalize a well set to a common start date; water-oil,
gas-oil and watercut ratio curves; compare populations by completion or structural setting.

**Wildcat:** per-well production and decline; no time-normalized group or type-curve view
found.

**Open source:** none needed; pandas.

### 9. GIS layers (Thematic Mapper)

**Petra:** load shapefiles, query by attribute or distance, color by class, clip and
reproject, send to the map.

**Wildcat:** no shapefile import found.

**Open source:** QGIS (GPL-2.0) for prototyping; GDAL/OGR (MIT) and pyproj (MIT) are the
long-term replacement.

## Gaps: engine exists, no screen

| Feature | Engine today | Missing | Open-source help |
|---|---|---|---|
| Isopach and grid-to-grid maps | `isopach` agent tool | Isopach option on the structure-map page; subtract, add and mask grids | xtgeo `subtract`, `add`, `*_inside` / `*_outside`, `fill`, `smooth`, `resample` (LGPL-3.0) |
| Volumetrics (deterministic and Monte Carlo) | `volumetrics`, `volumetrics_probabilistic` agent tools | Module with inputs, maps and P10/P50/P90 output | GSTools conditioned simulation for property-map realizations (LGPL-3.0) |
| Log crossplots, histograms, normalization | `crossplot_porosity`, `wor_xplot`, `curve_normalize` agent tools | Interactive crossplot and histogram with picks | None needed |
| Net pay and reservoir properties over intervals | `net_pay_cutoffs`, `hcpv_thickness` agent tools | Screen, and results stored per zone for mapping | None needed |

## New capability Petra lacks

| Feature | Package | License |
|---|---|---|
| Kriging (ordinary, universal, external drift) beside TPS and IDW | PyKrige (BSD-3), GSTools (LGPL-3.0) | Permissive / weak copyleft |
| Uncertainty maps from conditioned simulation | GSTools | LGPL-3.0 |
| Cross-validated gridding parameters | verde (BSD-3) | Permissive |
| Tension splines (avoid minimum-curvature overshoot) | GMT `surface -T` (LGPL-3.0), PyGMT (BSD-3) | Weak copyleft |

## Out of scope

- **Footage-call well spotting and digitizer tablets.** RRC supplies locations; paper-map
  digitizing is obsolete.
- **S&P data feeds** (Enerdeq, raster log library). Wildcat uses the RRC mirror instead.

## Suggested order

1. **Isopach and grid math** on the existing structure-map page (smallest step; xtgeo).
2. **Fault-aware gridding** (structure maps are wrong in faulted areas without it).
3. **Cross sections.**
4. **Interactive tops picking** on the cross section.
5. **Bubble and posted-data maps** (cheap with Mapbox).
6. **Volumetrics screen** over the existing agent tools.
7. **Directional profiles, 3D, seismic, GIS layers** as users ask.
