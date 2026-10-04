# jmest-waxman-smits-saturation-modelling

**Covers:** A journal-style technical paper (JMEST) explaining and deriving the Waxman-Smits shaly-sand saturation model and comparing it with Archie for dispersed-clay sandstones.

**Authoritative for:** Waxman-Smits equation form and its derivation from Archie for both water-bearing and hydrocarbon-bearing shaly sands, definitions and roles of F*, m*, B (counterion equivalent conductance) and Qv (cation exchange capacity per unit pore volume), when shaliness can be neglected in saturation calculation (the Rw·B·Qv/Sw threshold rule of thumb), conceptual distinction between laminar, structural and dispersed shale distribution and which saturation model suits each, explaining why Archie underestimates hydrocarbon saturation and why resistivity is depressed in shaly sands, iterative solution scheme for Sw in Waxman-Smits

**Not good for:** field-specific or basin-specific saturation results, cutoffs or reservoir volumetrics, laboratory procedures or measured Qv/CEC datasets for particular formations, laminated-shale or thin-bed anisotropy modelling (Thomas-Stieber, tensor resistivity, triaxial induction), alternative shaly-sand models in depth (Dual Water, Indonesia/Poupon, Simandoux, Juhasz normalised Qv), NMR, dielectric or capillary-pressure-based saturation methods, core-log integration workflows, log QC, environmental corrections or petrophysical software mechanics, stratigraphy, depositional facies or clay mineralogy identification

**Scope:** Generic petrophysical theory and worked equations for dispersed-clay shaly sandstones; no named field, well or region, and no era-specific data — treat as a tutorial/derivation reference rather than a source of empirical parameters, and calibrate B, Qv, F* and m* locally before use.

_6 segments._

---

### Waxman-Smits saturation modelling in dispersed shaly sands — title/abstract  `01-curve-reading/jmest-waxman-smits-saturation-modelling#0` (chars 0-2033)
Answers: Why does Archie's equation underestimate hydrocarbon saturation in shaly sands? · When should I use Waxman-Smits instead of Archie? · How much can hydrocarbon saturation change if I use Waxman-Smits in dispersed clay? · Why is resistivity lower in shaly sands than clean sands at the same porosity? · What causes the extra conductivity in shaly sand — clay exchange cations?
Entities: Waxman-Smits, Archie, Dual-Water, Qv, Rw, B, Elvis Onovughe, Effurun, Delta State, Nigeria, Journal of Multidisciplinary Engineering Science and Technology (JMEST)
Equations: Archie, Waxman-Smits, Dual-Water

### Introduction: shale distribution forms and shaly-sand saturation models  `01-curve-reading/jmest-waxman-smits-saturation-modelling#1` (chars 2033-7375)
Answers: why does shale mess up water saturation from logs · what are the three forms of shale distribution in a sand (laminar, structural, dispersed) · when should I use Waxman-Smits instead of Archie · which shaly sand model applies to laminated clay versus dispersed clay · why does Archie give too-low hydrocarbon saturation in shaly sand · what does dispersed shale do to permeability · what is the dual-water model assumption
Entities: Adekunle Sofolabo, University of Port Harcourt, Port Harcourt, Rivers State, Nigeria, Niger Delta, Archie, Waxman-Smits, Simandoux, Indonesia model, dual-water model, JMEST
Equations: Archie's equation, Waxman-Smits equation, Simandoux/Indonesia equation, Dual-water equation

### Saturation Models: Archie and Waxman-Smits Background and Equations  `01-curve-reading/jmest-waxman-smits-saturation-modelling#2` (chars 7375-12911)
Answers: What saturation models are used to get hydrocarbon saturation from resistivity logs? · Why do shaly sands need a correction to Archie's equation? · What is the Archie equation for water saturation and how is it derived? · What is the formation resistivity factor F and how does it relate to porosity? · What is the resistivity index I-Sw curve and why is extrapolating it hard in shaly sands? · When should I use Waxman-Smits instead of Archie? · Is Waxman-Smits empirical or theoretical? · Why can't lab I-Sw measurements reach low water saturations? · Which model applies to dispersed versus laminated shaly sandstones?
Entities: Archie, Waxman-Smits, Dual-Water model, Indonesia Model, Schlumberger, M. Waxman, L. Smits, Effective Medium Models (EMM), Rw, R0, Rt, Sw, resistivity index, cementation factor
Equations: F = R0/Rw, F = 1/phi^m, R0 = aRw/phi^m, Rt = I*R0, I = 1/Sw^m, Archie water saturation Sw = (aRw/(phi^m Rt))^(1/n)

### Deriving the Waxman-Smits equation for water-bearing shaly sandstone (Ro, F*, B, Qv)  `01-curve-reading/jmest-waxman-smits-saturation-modelling#3` (chars 12911-16700)
Answers: How is the Waxman-Smits equation derived from Archie for a fully water-bearing sandstone? · What is B in the Waxman-Smits equation and what does it depend on? · How do I get clay conductivity Ce from B and Qv? · Why is the F versus porosity log-log plot curved in shaly sands? · What is the modified formation resistivity factor F* and how is Ro* calculated? · What are the units of B and Qv (cation exchange capacity)? · How does m* differ from m? · How do I read the B chart from water resistivity and temperature?
Entities: Waxman-Smits, Archie's equation, Formation Resistivity Factor, Clay Bound Water Layer, Cation Exchange Capacity, Ro, Rw, Cw, Ce, JMEST, Figure 2, Figure 3
Equations: Archie: Ro = φ^m Rw, F = Ro/Rw = φ^m, Co = φ^m Cw, Waxman-Smits: Co = φ^-m*(Cw + B·Qv), Ce = B·Qv, Ro = φ^-m* Rw/(1 + Rw·B·Qv), F* = Ro*/Rw = φ^-m*, Ro* = Ro(1 + Rw·B·Qv)

### Waxman-Smits for hydrocarbon-bearing shaly sand, shaliness effect on Sw, and Qv determination  `01-curve-reading/jmest-waxman-smits-saturation-modelling#4` (chars 16700-25687)
Answers: How do I write the Waxman-Smits equation for a hydrocarbon-bearing shaly sand? · How do I solve for Sw with Waxman-Smits and why is it iterative? · When can I ignore shaliness in saturation calculation (Rw.B.Qv/Sw < 0.1)? · How much more hydrocarbon does Waxman-Smits give than Archie? · What is the modified Resistivity Index I' and why is the standard resistivity index curve non-linear? · How do I determine Qv or CEC — from core, from logs in a water zone, or from shale? · What is the Juhasz normalised Qv method? · How do I get Vsh for normalised Qv, and what does the Thomas-Stieber density/neutron crossplot tell me about clay distribution? · Where do m*, n*, Rw and B come from in the Waxman-Smits procedure? · Does Waxman-Smits apply to laminar or structural clay?
Entities: Waxman-Smits, Archie, Pickett plot, Resistivity Index, Cation Exchange Capacity (CEC), Qv, B.Qv, Juhasz method, normalised Qv, Thomas-Stieber, Density/Neutron Xplot, gamma-ray log, Vsh, Shell Petroleum Development Company (SPDC), JMEST, C0-Cw, titration, m*, n*
Equations: Archie equation (Rt = φ^m Sw^-n Rw), Resistivity Index I = Rt/Ro = Sw^-n, Waxman-Smits Ct = φ^m* Sw^n* (Cw + B.Qv/Sw), modified Resistivity Index I' = Rt*/Ro*, Sw^n* solved form of Waxman-Smits, Juhasz normalised Qv, Pickett plot fit, Thomas-Stieber analysis
