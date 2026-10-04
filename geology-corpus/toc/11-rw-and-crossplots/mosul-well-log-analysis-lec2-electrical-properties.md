# mosul-well-log-analysis-lec2-electrical-properties

**Covers:** Lecture 2 of a University of Mosul well-log analysis course, covering the electrical properties of reservoir rocks: conduction mechanisms, resistivity/temperature corrections, Rw determination, Archie's laws, and mud-filtrate invasion zones.

**Authoritative for:** definitions of resistance vs resistivity and conductivity unit conversion (mS/m to ohm.m), geothermal gradient and formation-temperature-at-depth calculations from BHT, surface temperature and TD, Archie's first and second laws: formation factor F, cementation exponent m, tortuosity constant a, saturation exponent n, and typical value ranges for sandstone vs carbonate, the Humble formula and other F-porosity relations, why hydrocarbons and rock matrix are non-conductive and connate-water salinity controls conduction, Rw estimation workflow and resistivity crossplot basics, terminology and symbols for flushed, transition and un-invaded zones, Rmf, Rxo, Rt, mudcake effects on hole diameter

**Not good for:** field-specific or basin-specific petrophysical parameters (a, m, n must be core-calibrated locally), shaly-sand saturation models (Waxman-Smits, Indonesia, Simandoux) and clay-conductivity corrections, tool physics, tool-specific response curves, vendor chart books or environmental correction charts, nuclear, acoustic, NMR or imaging log interpretation, modern inversion, uncertainty quantification or automated log-analysis software workflows, case studies, well-by-well interpretation examples or regional stratigraphy

**Scope:** Introductory undergraduate teaching material, generic and non-regional; presents classic Archie-era empirical relations for clean, water-wet, non-shaly formations. Numbers quoted are textbook typical ranges, not measured data, and equations assume simple homogeneous porous media.

_4 segments._

---

### Electrical current flow through reservoir rocks  `11-rw-and-crossplots/mosul-well-log-analysis-lec2-electrical-properties#0` (chars 0-615)
Answers: what part of a reservoir rock actually conducts electricity · do oil and gas conduct electrical current in a formation · why does connate water need dissolved salts for current to flow · is the rock matrix or cement conductive
Entities: Petroleum Engineering Department, Well Log Analysis

### Resistance, resistivity, temperature correction and Rw basics  `11-rw-and-crossplots/mosul-well-log-analysis-lec2-electrical-properties#1` (chars 615-11782)
Answers: How do I convert conductivity in mS/m to resistivity in ohm.m? · What is the relationship between resistance, resistivity, sample length and area? · How do I calculate geothermal gradient from BHT, surface temperature and total depth? · How do I calculate formation temperature at any depth? · How do I correct water resistivity measured in the lab to formation temperature using Arp's formula? · What factors affect the resistivity of reservoir rocks? · What is the resistivity of fresh water versus saturated salt water? · How do I convert other salts to equivalent NaCl salinity using multipliers? · How do I get resistivity from equivalent NaCl ppm? · What methods are available for determining formation water resistivity Rw? · How do I convert F/100ft to C/100m geothermal gradient?
Entities: Ohm's Law, Siemens, ohm.m, mS/m, BHT, Arp's Formula, NaCl, MgCl₂, CaSO₄, Na₂SO₄, KCl, CaCl₂, MgSO₄, Fig.1, Fig.2, Fig.3, Gen-6, SP, Archie's equation, drill stem (DST) test, connate water, interstitial water, Well Log Analysis, Petroleum Engineering Department
Equations: Ohm's Law (I = cΔE), r = R(L/A), C = 1/R, geothermal gradient G.G = 100(BHT-To)/TD, Tf = (G.G/100)Df + To, Arp's Formula (R2 = R1[(T1+6.77)/(T2+6.77)])

### Archie's First and Second Laws: Formation Factor, Saturation Exponent, Error Propagation  `11-rw-and-crossplots/mosul-well-log-analysis-lec2-electrical-properties#2` (chars 11782-22009)
Answers: What is the formation resistivity factor F and how does it relate Ro and Rw? · What values of a and m should I use for carbonates versus consolidated and unconsolidated sandstone? · What is the Humble formula? · What is the typical range of cementation exponent m in sandstone and carbonate? · How do I get m graphically from core plug measurements? · What is the resistivity index I and how does it relate to water saturation? · How do I combine Archie's first and second laws to compute Sw? · Where do I get Rt, Rw, a, m, n and porosity from for the Archie equation? · How is the saturation exponent n measured in the lab on core samples? · How does wettability affect the saturation exponent n? · How much error in Sw results from a 20% error in Rt, Rw, porosity, m or n?
Entities: Ro, Rw, Rt, Humble formula, Archie, SP log, Sonic log, Density log, Neutron log, STOOIP, OOIP
Equations: Archie's first law (Ro = F·Rw, F = a/Φ^m), Archie's second law (Rt = Ro/Sw^n, I = Sw^-n), Combined Archie equation Sw^n = aRw/(Φ^m Rt), Humble formula F = 0.62/φ^2.15, log-log plot of I vs Sw with slope -n

### Invasion, mud filtrate zones and resistivity symbols  `11-rw-and-crossplots/mosul-well-log-analysis-lec2-electrical-properties#3` (chars 22009-24416)
Answers: what causes mud filtrate invasion into the formation · what is the difference between the flushed zone, transition zone and un-invaded zone · how does mud cake form and how does it affect hole diameter · what borehole conditions affect log measurements · what do Rt, Rxo, Rmf, Rmc, Rm and Rs stand for on a log · what is dh, di, dj and hmc in the borehole invasion diagram · which resistivity and saturation symbols apply to each invaded zone · why must mud pressure exceed formation pressure while drilling
Entities: mud filtrate, flushed zone, transition zone, un-invaded zone, dh, di, dj, Drj, hmc, Rm, Rmc, Rmf, Rs, Rt, Ri, Petroleum Engineering Department, Well Log Analysis
