# aapg-formation-water-density

**Covers:** A short technical note on estimating formation water density from total dissolved solids or measured Rw, with a supporting formation-temperature estimate from BHT and total depth.

**Authoritative for:** converting TDS (ppm or mg/L) to formation water density in g/cm3, estimating water density when only Rw is available, approximating formation temperature by linear gradient interpolation from BHT and TD, supplying the Rw/water-density input needed for log water-saturation and crossplot work

**Not good for:** full brine PVT behavior (compressibility, formation volume factor, gas solubility) at reservoir P/T, water chemistry speciation, ionic composition, or scaling/compatibility prediction, hydrocarbon density, mud density, or pore-pressure gradient calculations, Archie parameter selection, shaly-sand saturation models, or the crossplot interpretation itself, measured lab brine density — these are empirical approximations only

**Scope:** Generic petrophysical/log-analysis practice, not tied to any basin or age; equations are empirical correlations valid for typical NaCl-dominated oilfield brines and near-surface-to-moderate reservoir temperatures. The BHT-based temperature estimate assumes a single linear geothermal gradient and uncorrected BHT, so it degrades in overpressured, geothermal, or thermally disturbed sections. Verify against local water analyses before use in reserves-grade calculations.

_1 segments._

---

### Estimating formation water density from TDS or Rw  `11-rw-and-crossplots/aapg-formation-water-density#0` (chars 0-5050)
Answers: How do I calculate formation water density from total dissolved solids? · What formula converts TDS to water density in g/cm3? · How do I estimate formation water density when I only have Rw? · How do I estimate formation temperature from BHT and total depth? · How do I get NaCl concentration in ppm from Rw and formation temperature? · Where do I get Rw if I have no water sample? · How do I correct water density for pressure effects? · What pressure gradient do I use to estimate formation pressure from depth? · How accurate is estimating water density from Rw?
Entities: AAPG Wiki, Edward A. Beaumont, Forrest Fiedler, Exploring for Oil and Gas Traps, Treatise in Petroleum Geology, Schlumberger, Gearhart-Owens, Collins, A., G., Petroleum Engineering Handbook, SPE, GO Log Interpretation Reference Data Handbook, BHT, TD, R_w, SP log, 0.433 psi/ft, Figure 1, Figure 2
Equations: ρ_w = 1 + TDS × 0.695 × 10^-6 g/cm3, T_f = T_s + D_f(BHT - T_s/TD), formation pressure = 0.433 × depth
