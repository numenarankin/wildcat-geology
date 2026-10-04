# Petra functionality reference

What S&P Global's Petra (formerly IHS Petra) does, module by module. Petra is the incumbent
Windows desktop tool for well-based subsurface interpretation in independent oil and gas: a
well database plus mapping, cross sections, log correlation, production analysis and 3D.

## Sources and their age

S&P's live product pages and the 2025 brochure return 403 to automated fetches, so this is
built from the official documents that were readable:

| Source | Date | Used for |
|---|---|---|
| [Petra User's Manual v2.0](https://petraftp.ihsenergy.com/Petraman.pdf) (469 pp) | April 2011 | Module behavior, data model, import/export, mapping and cross-section detail |
| [Petra brochure](https://cdn.ihsmarkit.com/www/pdf/Petra-Brochure.pdf) | 2016 | Module list, data products, Sidekick, Advanced Volumetrics, Directional Well |
| [Petra 2022 online help: gridding Method tab](https://onlinehelp.ihs.com/Energy/Petra/2022/Content/map_create_contour_grid___method_t.htm) | 2022 | Current gridding algorithms |

Not read (blocked): the [2025 brochure](https://www.spglobal.com/content/dam/spglobal/ci/en/documents/products/pdf/CI_0625-petra-geology-software-brochure-Upstream.pdf)
and the [product page](https://www.spglobal.com/commodityinsights/en/ci/products/petra-geological-analysis.html).
Features added after 2022 may be missing.

## Architecture

- **Main module plus tool modules.** Main owns the project and well database, runs
  calculations, launches every other module, and coordinates communication between them.
  Each tool module opens in its own window.
- **Linked windows.** Double-clicking a well on the map returns Main to that well; F8 in Main
  highlights the current well on the map. Wells picked on the map define a cross section.
- **Desktop and Windows only.** Licensing was a hardware key (HASP / Rainbow dongle) or
  FlexLM network license in the 2011 manual.
- **Shared projects.** A project can live on a network drive; concurrent users see each other's
  edits live (some spreadsheet views need a manual refresh).

## Data model

- **Project data**: all well data, logs, seismic shotpoints, land grids, and computed data
  such as contour grids.
- **UWI**: 1 to 20 characters, unique per well; in the US normally the API number. Sidetracks
  (API digits 11-12) and recompletions (digits 13-14) are separate wells.
- **WSN** (Well Sequence Number): internal immutable numeric ID, never reused, project-local.
- **Well label**: 1 to 32 character display name composed from other fields (operator, lease,
  section-township-range, and so on).
- **Zones**: unlimited user-defined tables of per-well data items. Built-in zones include
  `FMTOPS` (formation tops) and `WELL` (for example `TD`, computed `CUMGAS`). Interval data
  hangs off zones defined by an upper and lower top.
- **Units**: one unit system per project (feet or meters); display can switch between them.
  XY and depth units are set separately via the map projection.
- **Prospects**: saved well lists (WSN list files) to scope work to a subset of wells.

### Per-well data (Main module tabs)

| Tab | Contents |
|---|---|
| Project | Project-level summary |
| Well | Header, UWI, label; add, rename, delete wells |
| Location | Surface location, deviated-well surveys, projection and location locks |
| Fm Tops | Formation tops, top aliases, tops by source, reordering, top maintenance |
| Zones | User-defined zones and their items |
| Logs | Digital log curves |
| IP Tests | Initial potential tests |
| Fm Tests | Formation tests (DSTs) |
| Cores | Core intervals |
| Perfs | Perforations |
| Shows | Oil and gas shows |
| Production | Monthly production; compute cumulatives |
| Prod Cums | Cumulative production |
| Rasters | Raster log images and their calibrations |
| Other | Casing, fault cuts, production symbols, well history, liners, cement, velocity, pay data |
| Scout | Scout ticket data |
| Intervals | Interval data |

## Data in and out

### Import

- Tabular ASCII well data (headers, tops, zone data).
- LAS digital logs, including batch import.
- Raster log images (TIF) with calibration (LIC) files.
- Directional surveys.
- Monthly production.
- 2D and 3D seismic shotpoint locations and horizon values.
- Cartographic overlays and ESRI shapefiles.
- **Direct Connect** live download from S&P (Enerdeq US and Canada, IHS Canada logs) and from
  MJ Systems via LogSleuth. Requires a subscription.

### Export

- Petra Project File (`.PPF`) and Petra Template File (`.PTF`).
- ASCII tabular well data, ASCII tops, zone data, top definitions.
- Two Landmark formats, SCA-MCS Z data, GES Wellbase V2, LogSleuth well data.
- Log curves, raster logs (TIF) and LIC files, directional surveys.
- Monthly production as tabular, Production Analyst, or MoRe simulator recurrent data.
- Spreadsheet tool to CSV.
- Project summary reports (counts only, or full zone item list).

### S&P data products that feed Petra (2016 figures)

- 4.5M+ current and historic US well records: headers, tops, logs run, completions,
  production tests.
- 3.1M+ depth-registered raster logs, about 300k digital logs, 13M curve-feet digitized per
  month.
- Production for all fluids, operating hours, injection, ratios, cumulatives.
- Directional surveys.
- Interpreted formation tops on a consistent basin-wide stratigraphic framework.

## Calculations (Compute menu)

The manual calls these "the real strength of Petra."

- **User-defined equations** that create new zone data, log curves, monthly production, or
  seismic horizons.
- **Cumulative production** for any item in the monthly production database.
- **Reservoir properties from logs** over depth intervals with cutoffs: net, gross,
  net-to-gross, phi-h, phi-a.
- **Formation thickness** for multiple zones with corrections for deviated wells.
- **True stratigraphic thickness** from structure data.
- **Isopach** at each well from a zone's upper and lower tops.
- **Footage summations** from log data.
- **User models**: multi-line arithmetic expressions with Boolean operators, run across many
  wells, used for multi-well log analysis.
- **Grid calculations**: grid-to-grid math (for example structure minus structure).

## Map module

### Map types

- **Base maps** with up to 50 posted data lines per well, each placed above, below, left or
  right of the well spot, with per-line text size and color.
- **Contour maps** from gridded zone data (structure, isopach, any numeric item), with
  configurable contour range and color palette.
- **Bubble maps**: up to 32 z-data items per bubble as pie segments; radius scaled to value or
  fixed. Used for cumulative production and as a QC view of which wells have a top picked.
- **Attribute maps**.
- **Raster logs and production posted** at well locations.
- Core intervals, completed zones, and top-producer distribution shown spatially.

### Gridding (2022 help)

| Method | Behavior | Faults |
|---|---|---|
| Highly Connected Features (default) | Least-squares gridding; works for most data | Yes |
| Disconnected Features | Linear projection that closes off isolated features | Yes |
| Simple Weighting With Slopes | Computes slopes at data points, projects to nodes, weighted average | |
| Simple Weighting Without Slopes | Weighted average of nearby points; for dense control | |
| Distance Grid | Distance from each node to the nearest data point; drainage patterns | |
| Kingdom Flex Gridding | Minimizes curvature over sparse data while honoring points | |
| Closest Point | Nearest data value, no interpolation; resampling or very dense data | |
| Minimum Curvature | Smooth, evenly spaced contours | No (flexing options can work with faults) |

Other gridding features:

- **Faults**: digitize fault traces or polygons as overlay lines, then enable *Include Faults*
  when creating the grid.
- **Repeated tops along horizontal wellbores** can be added to the grid (Directional Well
  module).
- **Grid parameter comparison** across data types, and viewing grids in 3D.

### Isopachs (three methods)

1. Compute interval thickness at each well, then grid and contour it.
2. Grid the upper and lower structure surfaces, then contour their difference.
3. Grid-to-grid calculation. Only this method's result can be displayed in 3D Viz.

### Overlays and cartography

- Load land grids and culture data; map projections with on-the-fly lat/long to XY.
- **Map Overlay Utility**: draw and edit lines (with line classes), polygons and text.
- **Map Overlay Viewer** (Tools menu): inspect overlay or cartographic files before loading.
- Capture and edit contours by hand.

### Well spotting and editing on the map

- Add a well with the mouse, or move an existing well.
- **Spot a well from footage calls**: pick the four corners of a quarter-section grid (with
  snap-to-overlay, or auto-pick the section from a loaded land grid), then enter the calls.
- Fill in missing well locations.

### Digitizer tablet

- Wintab driver support with tablet registration and calibration check.
- Capture normal lines, contour lines and fault traces from paper maps.
- Add wells, seismic lines and shotpoints with the digitizing cursor.

## Thematic Mapper

ESRI shapefile handling (built on ESRI MapObjects 2.2 in 2011):

- Load a shapefile as a theme with its attributes.
- Create new shapefiles from expression, spatial or distance queries.
- Build a **Well Theme** from Petra well headers, tops and zone data.
- Color by single symbol, unique values, or class breaks.
- Copy, clip and reproject themes.
- Send a theme to a Map module overlay layer.
- Export a WSN list from a Well Theme.

## Cross Section module

- **Section types**: single well, well-to-well, line and wells, line and corridor.
- **Structural or stratigraphic** display, flattened on a top.
- **Contents**: deviated boreholes, digital logs, depth-calibrated raster logs, formation tops,
  faults, posted well data, cored / perforated / tested intervals, production charts,
  attribute symbols, user-drawn overlay interpretations.
- **Interactive correlation** of formation tops (two methods), automatic structural depth from
  tops.
- **Log editing**: digital curve edits, depth shifting, picking high/low cutoffs for log
  normalization.
- **Net pay** picking on raster images.

## Log Correlation module

Built for picking tops fast across a basin or play: smooth scroll and pan, log slipping
(stretch and squeeze), slip boxes. Correlates formations and unassigned markers and picks pay
intervals on digital and raster logs.

## Slip Logs module

Up to four raster logs side by side, laid out horizontally like logs on a desk.

- Scroll independently or locked together.
- Alignment cursor: align on a common feature or on a formation top.
- Pick or modify tops directly on the raster images.
- Fault gaps: insert blank space and shift the image below down in depth.

## Raster log calibration and digitizing

- Straighten skewed scans.
- Depth-calibrate images: calibration depths, interpolated depths, image groups, track edges,
  header and scale sections. Save and reload calibration files.
- **Digitize curves** from the raster: select curve and scale, set track edges, trace the
  curve, handle scale wraps, edit segments, save work in progress, store the curve to the
  database.

## Log analysis tools

- **Log Cross Plot**: XY, XYZ and ternary cross plots for one or many wells; discriminator
  curves to filter; overlay standard lithology charts (digital or scanned); digitize polygons
  on the plot and use them in log transformations to produce facies curves.
- **Z Cross Plot**: the same for tops and zone data (numeric and dates).
- **Log Histogram**: histogram plus vertical curve view; pick high and low values for
  normalization.
- **Log Curve Previewer**.
- **Dipmeter** display (3D Viz).

## Spreadsheet tool

Edit selected columns (well header items, tops, zone items) for a few wells or the whole
project. Tops editable as measured depth or subsea TVD. Global find and replace. CSV export
with optional headings and WSN column.

## Well selection

- **Select Wells By Data**: build a well set from search criteria across categories.
- Saved prospect well lists; *Use Entire Project* to clear the filter.
- The selected well set drives Main, maps and other modules.

## Seismic

- **2D Seismic tool**: import 2D and 3D shotpoint locations and horizon z data; edit line
  names and shotpoint numbers; view and edit z values by shotpoint or line. It does not
  display SEG-Y or seismic rasters.
- **PetraSeis** (sold separately): 2D line and 3D volume interpretation, launched from Main.
- **3D Viz seismic**: cubes, arbitrary lines, horizons, 2D surveys.
- **Kingdom link**: S&P's full seismic interpretation suite (attributes, AVO, microseismic).

## 3D Visualizer

- **Well content**: straight and deviated boreholes, tops, digital logs, perfs, shows, dipmeter.
- **Surfaces**: subsea grids, isopachs, map images, map overlays.
- **Panels and seismic**: cross-section panels, depth/time planes, seismic cubes, arbitrary
  lines, horizons, 2D surveys.
- **View controls**: vertical exaggeration, light source for shading, save and restore views,
  map view, front view.
- **Output**: print or capture an image.

## Directional Well module

- Plan horizontal and directional wells (surface and profile plans).
- Profile view with digital logs, tops, events and surfaces posted along the well path.
- Load drilling data.
- Improve grids with repeated tops along laterals.
- Analyze and post horizontal well performance.
- Jump to 3D Viz.

## Production and reserves

- **Production Analysis**: monthly production cross plots and decline curve analysis. Fit
  exponential or hyperbolic declines graphically; store parameters (for example projected
  reserves) in the database for mapping, drainage-area computation, and other calculations.
- **Production Group Plot**: sum, average, or time-normalize a well set to a common start
  date; derive ratio curves (water-oil, gas-oil, watercut). Used to compare well populations
  by completion technique, reservoir properties, or structural setting.
- **Templates** for wells in an evaluation area that share analysis settings.
- **Advanced Volumetrics**: oil and gas volumetrics and recovery efficiency.
  - **Deterministic**: average reservoir and fluid properties.
  - **Probabilistic**: Monte Carlo over parameter distributions, with statistical reports and
    probability graphs.
- Map EUR, cumulative gas and gas decline rates.

## Petra Sidekick

External utility for the Petra project:

- Single-well or multi-well data view; well statistics by scanning wells.
- Data types: project, well, zone, tops, raster, grid, overlay, table.
- Maintenance: global delete; zone, production, raster log and digital log maintenance.
- Import general ASCII; batch import LAS and raster LIC files; Direct Connect logs.
- Export tabular ASCII.

## Integrations

Kingdom, AccuMap (Western Canada, Montana, North Dakota, Wyoming), Enerdeq Browser, Energy
Web Services (US well and production, international well database), Information Hub,
LOGarc, GeoSyn (synthetic seismograms), PowerTools (production analysis), FieldDIRECT, IHS
PERFORM, MJ Systems LogSleuth, and an ESRI plug-in via PetraDBServer.

## Workflows S&P markets it for

- **Prospecting**: tie well and seismic information.
- **Acreage capture and evaluation**.
- **Geological and geophysical interpretation**.
- **Structural mapping** that updates as new wells arrive.
- **Infill drilling and recompletion targeting**.
- **Reserves and production analysis; unconventional plays**: decline, volumetrics,
  horizontal-well performance.
- **Benchmarking completions**: production after each treatment type.
