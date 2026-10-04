# petroleumoffice-arps-models

**Covers:** A short reference section on Arps decline curve models (exponential, hyperbolic, harmonic) as documented in PetroleumOffice spreadsheet software help, including rate-time/rate-cumulative equations, the b-exponent, and EUR calculation.

**Authoritative for:** Arps exponential, hyperbolic, and harmonic decline equations in rate-time and rate-cumulative form, definition and interpretation of the b-factor and nominal/effective decline rate conversions, calculating EUR and remaining reserves from a fitted decline curve to an economic limit, typical b-value ranges associated with drive mechanisms such as solution gas drive and water drive, meaning and caveats of b > 1 behavior

**Not good for:** unconventional/shale flow regimes requiring Duong, SEPD, power-law exponential, or modified-hyperbolic terminal-decline methods, rate-transient analysis, type curves, or pressure-transient interpretation, probabilistic reserves, SEC/PRMS reserves classification, or economics beyond a simple economic limit, field-specific or basin-specific decline parameters, well data, or case studies, material balance, volumetrics, or reservoir simulation

**Scope:** Empirical curve-fitting only; classical Arps (1945) formulation as presented in vendor software documentation, assuming boundary-dominated flow at constant operating conditions. No basin, era, or fluid-system restriction, but also no calibration data — treat b-value guidance as rules of thumb, not measurements.

_1 segments._

---

### Arps decline curve models: exponential, hyperbolic, harmonic equations and b-factor  `16-decline-curves/petroleumoffice-arps-models#0` (chars 0-9301)
Answers: What are the Arps decline equations for exponential, hyperbolic, and harmonic decline? · How do I calculate EUR from a decline curve? · What b value should I use for solution gas drive or water drive? · What does a b factor greater than 1 mean? · How do I compute time to reach the economic limit rate? · What is the loss ratio and how does it define the b exponent? · When are Arps decline curves valid — do I need boundary-dominated flow? · Why does harmonic decline give infinite cumulative production? · What units must Di and t be in for Arps equations? · Which decline model should I use for shale or tight gas wells? · What is the cumulative production equation for hyperbolic decline?
Entities: Arps, J.J. Arps, Analysis of Decline Curves, Transactions of AIME, Fetkovich, Shell Oil Company, PLE, SEPD, Duong, Ali, T.A., Sheng, J.J., Lee, W.J., Sidle, R.E., Blasingame, T.A., Rushing, J.A., SPE-177300-MS, SPE-130102, SPE-4629-PA, SPE-98042, BDF, STB/d, Mscf/d, EUR
Equations: Arps exponential decline q(t)=qi·e^(-Di·t), Arps hyperbolic decline q(t)=qi/(1+b·Di·t)^(1/b), Arps harmonic decline q(t)=qi/(1+Di·t), decline rate definition D=-(1/q)dq/dt, loss ratio derivative b=d/dt(1/D), cumulative production Np for exponential, hyperbolic, harmonic, time to economic limit t_econ, EUR expressions for each model
