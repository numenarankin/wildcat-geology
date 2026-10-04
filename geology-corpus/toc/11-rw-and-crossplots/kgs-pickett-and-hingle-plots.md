# kgs-pickett-and-hingle-plots

**Covers:** A Kansas Geological Survey web-app page explaining Pickett and Hingle porosity-resistivity crossplots for graphically determining Archie parameters (Rw, m, n).

**Authoritative for:** how to construct and read a Pickett plot (log porosity vs log Rt) and the underlying Archie-based equation, how the Hingle plot's non-linear resistivity axis is built and how the cementation exponent m controls the grid, graphical estimation of formation water resistivity Rw, cementation exponent m, and saturation exponent n from log data, choosing between Pickett and Hingle approaches for quick-look Archie parameter picking

**Not good for:** stratigraphy, formation names, or basin geology, full quantitative saturation workflows in shaly sands (Waxman-Smits, dual-water, Indonesia equations), core-measured electrical properties, SCAL procedures, or laboratory m and n determination, log tool physics, borehole environmental corrections, or log QC, capillary pressure, permeability prediction, or reservoir modeling, regional Rw values or produced-water chemistry for a specific field

**Scope:** Method/tool documentation, not a regional study: technique is generic and lithology-independent in principle but assumes clean, water-wet, Archie-type formations with a single Rw and a reasonably homogeneous zone; examples and defaults reflect Kansas mid-continent carbonate/sandstone log practice. Treat outputs as graphical approximations to be confirmed against core or SCAL data.

_2 segments._

---

### Pickett & Hingle Plot web app — graphical determination of Archie parameters  `11-rw-and-crossplots/kgs-pickett-and-hingle-plots#1` (chars 180-3635)
Answers: how do I get Rw, m and n from a porosity-resistivity crossplot? · what is a Pickett plot and how do I read it? · what is the Pickett plot equation relating porosity and Rt? · how does a Hingle plot axis work and what does m do to the grid? · how do I fit the 100% water saturation line on a Pickett plot? · can I add Sw, bulk volume water, or permeability lines to a Pickett plot? · what are the original references for the Hingle and Pickett plots?
Entities: Hingle (1959), Pickett (1973), Archie, Sw, Rw, M, N, Rt, a*Rw, Bvw, K, Kansas Geological Survey, KGS, GEMINI, U.S. Department of Energy, NETL, DE-FE0002056, John R. Victorine, The Log Analyst, SEG 29th Annual Meeting
Equations: Archie's equation, Pickett plot: log(Φ) = (-1/M)*log(Rt) + log(a*Rw)/M - N*log(Sw)/M, Hingle y-axis: (1/Rt)^(1/m)
