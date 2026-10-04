# phdwin-arps-equations-rate-time

**Covers:** Reference sheet for Arps decline-curve rate-time and cumulative-production equations as implemented in PHDWin reserves software, covering exponential, hyperbolic, and harmonic cases plus nominal/effective decline conversions.

**Authoritative for:** Arps exponential, hyperbolic, and harmonic rate-time equation forms and variable definitions (qi, Di, b, t), Cumulative production (Np) formulas for each decline type, including the harmonic log form, Converting between nominal and effective decline rates, and annual to monthly decline, Computing volume produced within a single month from a decline segment, PHDWin's specific conventions for decline-curve arithmetic, Typical b-factor ranges cited for single-porosity vs dual-porosity or fracture-stimulated reservoirs

**Not good for:** Reservoir-engineering justification or derivation of Arps behavior from flow physics, Unconventional/shale forecasting methods beyond Arps (Duong, SEPD, power-law, modified hyperbolic terminal-decline practice is only lightly implied), Type-curve matching, rate-transient analysis, or pressure-transient interpretation, Reserves classification, SEC/PRMS booking rules, or economic evaluation, Basin- or field-specific decline parameters and analog b-factor datasets, Software workflow instructions for other packages (Aries, Val Nav, ComboCurve) or for PHDWin UI/menu navigation

**Scope:** Empirical curve-fitting mathematics only, vendor-specific to PHDWin conventions and units (typically monthly time steps, oilfield units). b-factor guidance is generic rule-of-thumb, not calibrated to any named basin or play, and should not substitute for local production history.

_2 segments._

---

### Arps rate-time and cumulative equations in PHDWin (exponential, hyperbolic, harmonic), nominal vs effective decline  `16-decline-curves/phdwin-arps-equations-rate-time#0` (chars 0-11955)
Answers: What is the exponential decline rate equation and what are its units? · What is the hyperbolic rate equation q = qi(1+bDit)^(-1/b)? · What b factor values are typical for single vs dual porosity or fracture-stimulated reservoirs? · How do I convert a nominal annual decline to a monthly decline? · How do I convert an effective annual decline to a monthly effective decline? · How do I convert between nominal and effective decline? · What is the difference between tangent and secant effective decline, and which does PHDWin use? · How do I convert secant effective decline to tangent effective decline? · Why does PHDWin back up the curve fit to the beginning of the month instead of mid-month qi? · Is monthly produced volume equal to the instantaneous rate at mid-month? · How do I calculate cumulative production Np for an exponential decline? · How do I calculate cumulative production for a hyperbolic decline when b is not 1? · What b value corresponds to exponential vs harmonic decline?
Entities: PHDWin, PHDWIN, TRC CONSULTANTS, LC, Arp's Equations, D_Tei, D_Sei, b
Equations: Exponential rate equation q = qi e^(-Dt), Hyperbolic rate equation q = qi(1+bDit)^(-1/b), Effective decline De = (qi-q)/qi, D = -ln(1-D_Tei); D_Tei = 1-e^(-D), D = ((1-D_Sei)^(-b) - 1)/b, D_Te = 1 - e^(-(((1-D_Sei)^(-b)-1)/b)), Exponential cumulative Np = (qi-q)/D and Np = (qi-q)/(-ln(1-De)), Hyperbolic cumulative Np = qi^b/((1-b)Di) * (qi^(1-b) - q^(1-b))

### Hyperbolic and harmonic cumulative production (Np) calculations in PHDWin  `16-decline-curves/phdwin-arps-equations-rate-time#1` (chars 11955-14888)
Answers: How does PHDWin calculate cumulative production for a hyperbolic decline? · What is the Np equation for a harmonic decline (b = 1)? · How do I get the volume produced within a single month from a decline curve? · What is the hyperbolic rate-time equation using qi, b, and Di? · Do time units need to be consistent between q, qi and Di in Arps equations? · Can I use non-integer time values to handle varying day counts per month?
Entities: PHDWin, TRC CONSULTANTS, LC, Arp's Equations, Di, b, Hyperbolic Exponent factor
Equations: Harmonic cumulative production: Np = (qi/Di) ln(qi/q), Hyperbolic cumulative production: Np = qi^b/((1-b)Di)(qi^(1-b) - q^(1-b)), Hyperbolic rate-time: q = qi(1 + b Di t)^(-1/b)
