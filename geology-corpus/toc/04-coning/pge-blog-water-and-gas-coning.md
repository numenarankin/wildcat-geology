# pge-blog-water-and-gas-coning

**Covers:** A petroleum-engineering blog article on water and gas coning in producing wells: definitions, controlling variables, critical-rate correlations (Chaperon, Schols, Chierici et al.), partial penetration/perforation design, and worked calculation examples.

**Authoritative for:** definitions and distinction of water coning, gas coning, and free-gas or rising-contact production, analytical critical-rate correlations for coning (Chaperon, Schols, Chierici et al.) and the input variables each requires, estimating optimum perforation interval and length to delay or avoid coning, partially penetrating well inflow, including the Kozeny expression, qualitative and quantitative comparison of vertical versus horizontal wells for coning avoidance, coning control strategies and rate-sensitivity reasoning

**Not good for:** reservoir geology, stratigraphy, or basin-specific formation descriptions, numerical reservoir simulation workflows or history matching, water shutoff chemistry, gels, or mechanical remediation hardware, petrophysical log interpretation or saturation calculation, field-specific production histories or case-study data, non-coning production problems such as sand control, scale, or artificial lift design

**Scope:** Generic engineering theory for single-well coning in homogeneous, anisotropic-permeability reservoirs; correlation-based rather than simulation- or field-calibrated, with assumptions (steady state, sharp interfaces, simple geometry) that limit use in strongly heterogeneous, fractured, or multilayer settings. Blog-level treatment, no basin or era restriction, and no primary data.

_5 segments._

---

### Water and gas coning: definitions, impact, and article outline  `04-coning/pge-blog-water-and-gas-coning#0` (chars 0-3641)
Answers: what is water coning and gas coning in a producing well · how is coning different from free-gas production from an expanding gas cap or a rising water/oil contact · why is coning rate-sensitive · why does a horizontal well produce less unwanted water or gas than a vertical well · what problems does coning cause at surface and for reservoir pressure · what strategies exist for wells that may cone
Entities: water/oil contact (WOC), Schols’ correlation, Chierici et al. correlation, gas cap, bottomwater drive

### Predicting coning: critical rate methods and Chaperon example  `04-coning/pge-blog-water-and-gas-coning#1` (chars 3641-8849)
Answers: how do I calculate the critical production rate before water or gas coning occurs · what does the Chaperon method calculate and what variables does it need · what controls whether a cone reaches the perforations · how much better is a horizontal well than a vertical well for avoiding gas coning · does vertical permeability matter for critical coning rate · can critical rate methods tell me when breakthrough happens or what GOR to expect after breakthrough · why does critical rate decrease over time as bottom water rises · worked example of critical rate for a 160-acre unit with a gas cap
Entities: Chaperon, GOR, GOC, 160-acre, Isotropic Reservoir A, Anisotropic Reservoir B
Equations: Chaperon critical rate for vertical wells, Chaperon critical rate for horizontal wells

### Coning control strategies and critical-rate correlations (Schols, Chierici et al.)  `04-coning/pge-blog-water-and-gas-coning#2` (chars 8849-19292)
Answers: How do I minimize water or gas coning in a producing well? · What is partial perforation and how do I pick the perforation interval to avoid coning? · What is the critical producing rate below which a cone stabilizes? · How do I calculate critical oil rate to avoid water or gas coning? · How do I use Schols' correlation for dimensionless critical rate? · How do I use the Chierici et al. charts to get critical rates for simultaneous gas and water coning? · How do I find the optimum perforation length and position for a gas-cap, bottomwater reservoir? · Why is gas coning less problematic than water coning? · What does vertical-to-horizontal permeability ratio do to coning?
Entities: Schols, Chierici, Muskat and Wyckoff, Chaney, Wheatley, GOC, WOC, STB/D, finite-difference simulator
Equations: Critical producing rate equation (Eq. 8) with Δρ, Bo, μo, ko, qDc, h, Schols' correlation for dimensionless critical rate (Eq. 9) using b/h and re, Chierici et al. dimensionless variables ε, δ, rDe (Eqs. 10–13), Eq. 14 theoretical producing rate of partially penetrating well (referenced)

### Partially penetrating wells, coning variables, and worked critical-rate/perforation-length examples  `04-coning/pge-blog-water-and-gas-coning#3` (chars 19292-27178)
Answers: How do I compute the optimum perforation length to avoid gas coning? · What flow rate does a partially penetrating well deliver and how do I estimate it? · What is the Kozeny expression for a partially penetrating well flow rate? · Which variables control whether coning can be avoided? · Does horizontal permeability affect the likelihood of controlling coning? · How do I compute critical rate for a well in a gas-cap reservoir using Schols' correlation? · How do I use the Chierici et al. charts to get psi and delta_g? · Why does Chierici et al. give a longer perforation interval than Schols? · Where should I place the perforation interval in a gas-cap reservoir with bottom water? · What techniques besides rate control can suppress coning? · Why is coning hard to control in a thin reservoir?
Entities: Kozeny, Schols, Chierici et al., Cherici et al., GOC, WOC, STB/D, md, cp, psia, 80-acre well spacing
Equations: Kozeny expression (Eq. 14) for partially penetrating well rate, Eq. 8 critical rate, Eq. 9 dimensionless critical rate (Schols), Eq. 15 proportionality for q_c/q
