# seg-wiki-pickett-plot

**Covers:** An SEG-Wiki style tutorial on the Pickett plot: a log-log resistivity-versus-porosity crossplot used to estimate Rw, Archie parameters, and water saturation graphically from well logs.

**Authoritative for:** step-by-step construction of a Pickett plot (axis choice, log-log scaling, plotting deep resistivity vs. porosity), reading Rw off the plot as the intercept of the 100% water-saturated line at 100% porosity, graphical estimation of water saturation without a pre-known Rw, interpreting the slope of the water line as the cementation exponent m, quick-look formation-water-resistivity and Archie-parameter QC from log data

**Not good for:** numerical/deterministic petrophysical workflows or software-based saturation solvers, shaly-sand and low-resistivity-pay saturation models (Waxman-Smits, dual-water, Indonesia equation), porosity-tool physics, log corrections, or environmental corrections upstream of the plot, determining saturation exponent n or measuring m and n in the laboratory (SCAL), permeability, capillary pressure, or reserves calculations, carbonate or fractured-reservoir cases where a single clean water line is invalid, any basin-, field-, or well-specific parameter values

**Scope:** Generic, non-localized log-interpretation methodology grounded in the Archie equation; assumes clean, water-bearing intervals of relatively constant Rw and lithology within the plotted zone. Educational/reference wiki content rather than a peer-reviewed study; no dataset, age, or basin ties, and results are only as good as the Archie assumptions and porosity input.

_1 segments._

---

### Pickett plot: theory and step-by-step construction  `11-rw-and-crossplots/seg-wiki-pickett-plot#0` (chars 0-8785)
Answers: How do I build a Pickett plot from resistivity and porosity? · How do I get water saturation graphically without knowing Rw? · What axes does a Pickett plot use and what scale? · Where do I plot Rw on a Pickett plot and why at 100% porosity? · How do I set the slope of the 100% Sw line — what value of m should I use? · What if I have no Rw data for the Pickett plot? · How do I draw the remaining Sw lines (71, 50, 41, 35, 27, 22%)? · What are typical ranges for a, m, and n in Archie's equation? · How do I convert water saturation to hydrocarbon volume? · What is the difference between oil wet and water wet reservoirs for recovery? · What are the assumptions/limitations of the pattern recognition approach to Archie?
Entities: Pickett plot, George Pickett, Archie's equation, SEG Wiki, AAPG Wiki, Crain's Petrophysical Handbook, The Log Analyst, Krygowski, Cluff, Rw, Rt, Ro, Sw, SH, spontaneous potential
Equations: Archie's equation F = Ro/Rw = a/phi^m, Archie Sw^n = Ro/Rt, m log(phi) = log(a Rw) - log(Rt) - n log(Sw), SH = 1 - Sw
