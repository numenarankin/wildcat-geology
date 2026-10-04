# rfour-arps-dca-practical-guide

**Covers:** A practical working guide to Arps decline-curve analysis: the three decline forms (exponential, hyperbolic, harmonic), interpretation of the b-factor, fit-window selection, terminal decline switching, and EUR estimation, with an FAQ and references.

**Authoritative for:** choosing between exponential, hyperbolic, and harmonic Arps forms, interpreting the decline exponent b and its link to drive mechanism, expected b ranges for solution-gas drive, water drive, and other reservoir types, diagnosing and handling b > 1 fits, selecting the fit window and applying terminal-decline limits, estimating EUR and remaining reserves from a decline fit

**Not good for:** rate-transient analysis, type-curve matching, or flowing-material-balance methods, unconventional/shale-specific alternatives (Duong, SEPD, power-law exponential, Modified Arps constraints), probabilistic reserves, SEC/PRMS reserves classification, or economic limit and cash-flow modelling, numerical or analytical reservoir simulation and pressure-transient well testing, petrophysical inputs, volumetric OOIP/OGIP estimation, or geologic characterisation, field- or basin-specific decline parameters and benchmark datasets

**Scope:** Method-focused and empirical rather than region-specific: presents the classical Arps (1945) framework for boundary-dominated single-well production decline. Assumes constant operating conditions and stable drawdown; results are unreliable during transient/linear flow, after workovers, artificial-lift changes, or with heavy shut-in and allocation noise. Treat b-factor/drive-mechanism guidance as rules of thumb, not local calibration, and verify against modern unconventional-specific literature before applying to shale wells.

_2 segments._

---

### Arps decline curve analysis — forms, b-factor, fit window, EUR, terminal decline  `16-decline-curves/rfour-arps-dca-practical-guide#0` (chars 0-10628)
Answers: Which Arps decline form should I use — exponential, hyperbolic, or harmonic? · What does the b-factor tell me about reservoir drive mechanism? · What b value should I expect for solution-gas drive or water drive? · Why is my b-factor greater than 1 and can I trust it? · How much production history do I need before fitting a decline curve? · Should I include the first 6 months of transient data in my Arps fit? · How do I calculate EUR from an exponential or hyperbolic decline fit? · Why does harmonic decline give infinite EUR? · What is the terminal decline switch and when do I apply it? · How do I set up a per-well DCA workflow for a mature field? · When does decline curve analysis stop working? · What R² is acceptable for a decline curve fit? · What is the equation for hyperbolic decline rate vs time?
Entities: Arps, Jan Arps, qi, Di, qeco, Np, De, Dterminal, BOPD, L'Hôpital's rule, Coleman-Turner critical rate, EUR, R², pseudosteady-state
Equations: Arps general hyperbolic q(t) = qi / (1 + b·Di·t)^(1/b), Exponential decline q(t) = qi·exp(−D·t), Harmonic decline q(t) = qi / (1 + Di·t), EUR exponential = Np + (qi − qeco)/D, EUR hyperbolic = Np + qi^b(qi^(1−b) − qeco^(1−b))/((1−b)Di), Modified hyperbolic with terminal decline switch

### Arps DCA takeaways, references, and FAQ  `16-decline-curves/rfour-arps-dca-practical-guide#1` (chars 10628-13623)
Answers: What is Arps decline-curve analysis? · What are the three Arps decline models? · What does the decline exponent b mean and what values does it take? · How are reserves (EUR) estimated from decline curves? · Why should I apply a terminal decline instead of forecasting hyperbolic to infinity? · Does window selection matter more than which decline equation I pick? · Where can I find the original Arps 1945 paper or other DCA references? · Is there a free Excel tool for multi-b Arps fitting?
Entities: Cronquist, C. (2001), Poston, S. W., Poe, B. D. (2008), RFour Energy, GOWIS, Ershaghi X-plot, Chan diagnostic, Coleman-Turner
Equations: Arps exponential (b = 0), Arps hyperbolic (0 < b < 1), Arps harmonic (b = 1)
