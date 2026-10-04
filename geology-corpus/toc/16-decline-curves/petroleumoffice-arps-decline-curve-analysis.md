# petroleumoffice-arps-decline-curve-analysis

**Covers:** A single-section technical reference on Arps decline curve analysis, giving the exponential, hyperbolic, and harmonic rate-time and rate-cumulative equations, b-exponent interpretation, and EUR calculation.

**Authoritative for:** Arps decline equations (exponential, hyperbolic, harmonic) in rate-time and rate-cumulative form, meaning of the decline exponent b and typical b ranges by drive mechanism (e.g. solution gas drive, water drive), computing EUR and remaining reserves from a fitted decline curve, nominal vs effective decline rate conversions, why harmonic decline yields an unbounded cumulative and the need for an economic limit

**Not good for:** unconventional/shale wells in transient linear flow, where Arps b>1 overestimates reserves — use Duong, power-law exponential, or modified hyperbolic instead, type-curve matching (Fetkovich, Blasingame), rate-transient analysis, or pressure-transient interpretation, volumetric, material-balance, or simulation-based reserve estimates, probabilistic reserves, SEC/PRMS reserve classification, or economic valuation workflows, field- or basin-specific decline parameters and case histories, diagnosing the cause of a decline change (workover, choke change, artificial lift) from production data

**Scope:** Generic empirical curve-fitting method originating from Arps (1945), applicable to boundary-dominated flow in conventional wells producing at essentially constant operating conditions; not tied to any basin, formation, or era of data, and it assumes the underlying drive mechanism and completion state remain unchanged over the fitted interval.

_1 segments._

---

### Arps Decline Curve Analysis — exponential, hyperbolic, harmonic equations, b-values, EUR  `16-decline-curves/petroleumoffice-arps-decline-curve-analysis#0` (chars 0-10886)
Answers: What are the Arps exponential, hyperbolic, and harmonic decline equations? · How do I calculate EUR from a decline curve? · What does the b exponent mean and what values are typical for solution gas drive or water drive? · Why does harmonic decline give infinite cumulative production? · How do I compute time to reach the economic limit rate? · When are Arps equations invalid — what if b > 1? · What units must Di and t be in for Arps equations? · Which decline model should I use for shale or tight gas wells? · What is the loss ratio concept in decline curve analysis? · What did Fetkovich add to Arps decline theory?
Entities: Arps, J.J. Arps, Analysis of Decline Curves, Transactions of AIME, Fetkovich, Petroleum Office, Duong, PLE, SEPD, Power Law Exponential (PLE) Decline Model, Stretched Exponential Production Decline (SEPD) Model, Modified Hyperbolic Decline Model, Ansah-Knowles-Buba (AKB) Decline Model, Shell Oil Company, Ali, T.A. and Sheng, J.J., Lee, W.J. and Sidle, R.E., SPE-177300-MS, SPE-130102, SPE-4629-PA, Journal of Petroleum Technology, boundary-dominated flow (BDF), EUR, N_p
Equations: Arps exponential decline q(t)=qi*e^(-Di t), Arps hyperbolic decline q(t)=qi/(1+b Di t)^(1/b), Arps harmonic decline q(t)=qi/(1+Di t), Cumulative production Np for exponential/hyperbolic/harmonic, Time to economic limit t_econ, EUR formulas, decline rate definition D = -(1/q)dq/dt, loss ratio derivative b = d/dt(1/D)
