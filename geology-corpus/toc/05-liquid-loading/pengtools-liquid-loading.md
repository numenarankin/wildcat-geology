# pengtools-liquid-loading

**Covers:** A pengtools software documentation page on gas-well liquid loading, centered on the Turner correlation for critical gas velocity and the conversion to critical gas rate.

**Authoritative for:** Turner critical gas velocity equation and its unit-dependent constants (20.4, 2.04, 1.593), converting critical velocity to critical gas rate in MMscfd using pressure, temperature, z-factor and tubing area, screening whether a gas well is likely to be liquid loaded, interpreting pengtools' liquid-loading calculator inputs and outputs

**Not good for:** multiphase flow modeling, nodal analysis, or full vertical lift performance curves, alternative or corrected loading criteria (Coleman, Nosseir, Li, Turner with adjustment factors) unless explicitly covered, deviated, horizontal, or slug-flow-dominated wellbore geometries, liquid unloading remediation design (plunger lift, velocity strings, foamers, compression sizing), oil-well or pipeline liquid holdup problems, reservoir engineering, PVT correlation derivation, or well-test interpretation

**Scope:** Vendor/tool documentation, not a peer-reviewed source; scope is vertical gas wells under the entrained-droplet assumption of the original 1969 Turner work, with pengtools' unit conventions and field-units constants. Treat it as an equation and unit-handling reference rather than a review of loading physics or basin-specific field practice.

_1 segments._

---

### Liquid loading: Turner critical gas velocity and rate  `05-liquid-loading/pengtools-liquid-loading#0` (chars 0-4672)
Answers: how do I calculate the critical gas velocity to lift liquids out of a gas well · what is the Turner correlation for liquid loading · how do I compute critical gas rate in MMscfd from critical velocity · why is the Turner constant 20.4 vs 2.04 vs 1.593 · how does PQplot determine the liquid loading point on a VLP curve · what surface tension should I use for water vs condensate in Turner · how does tubing ID affect liquid loading · worked example of critical gas velocity for 2-3/8 in tubing at 400 psia · how do I calculate gas density from specific gravity, pressure, temperature and z
Entities: Turner, PQplot, PROSPER, VLP, Gray correlation, Turner, R. G., Hubbard, A. E., Dukler, Journal of Petroleum Technology, SPE-2198-PA, Lea, J. F., Nickens, M., Wells, Gas Well Deliquification, Energy Tribune Publishing Inc.
Equations: Turner minimum gas velocity correlation, critical gas rate equation q_g = 3.067 P v_g A / (T z), wellhead gas velocity equation, real gas density equation
