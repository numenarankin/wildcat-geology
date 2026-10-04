<!-- Source: mcinerney-lea-cox-uncertainty-critical-velocity.pdf -->
<!-- Converted: mistral-ocr-latest -->

# UNCERTAINTY IN GAS WELL CRITICAL VELOCITY PREDICTIONS

Joe McInerney, J. Lea & James C. Cox
Texas Tech University

## INTRODUCTION

Turner et al.¹ developed the first widely used correlation for critical flow rate of gas to prevent liquid loading. Later, Coleman et al.² used lower wellhead pressure and found that the Turner method over-predicted the required critical rate by about 20%. The 20% is the adjustment to theory that Turner used in the original. Recently Kees⁷ showed a correlation of critical rates that show the required critical rate at lower wellhead or flowing tubing pressures, to be more than the Turner correlation. This paper discusses the spread in possible predicted values of critical rates that a user could see using different correlations. Some low pressure measured data is presented as well.

## BACKGROUND

Turner et al.¹ found that a weight vs. drag model on liquid droplets fit his well data the best. His result for critical velocity is one where if the critical velocity is exceeded the well is predicted to not liquid load and has sufficient velocity to carry liquids from the well. One form of his result is:

$$V_{C} = 1.593 \left( \frac{\rho_{L} - \rho_{G}}{\rho_{G}^{2}} \sigma \right)^{1/4} ft/s$$

Equation 1

This equation shows that the critical velocity is a function of liquid and gas density and the surface tension between the two. The complete development is in Appendix A along with the definition of all terms. His final result for velocity to lift salt water is:

$$V_{C,water} = 5.321 \frac{(67 - .0031P)^{1/4}}{(.0031P)^{1/2}} ft/s$$

Equation 2

The above equation includes a 20% upward adjustment to fit the data. The data used by Turner was in general for gas wells with a high surface pressure. Turners work was later re-examined by Coleman et al.² and found that to fit a group of data from wells with lower wellhead pressures, typically well less than 1000 psi, and the equation could fit the data without the 20% adjustment to the model.

Recently Kees et al.⁷ presented a correlation to predict liquid loading in a group of gas wells in the Netherlands, and their correlation presented in Appendix B, has a trend to show that even more velocity or critical rate is necessary to prevent liquid loading than Turner would predict, at lower wellhead pressures. For the Shell correlation, if A = (0.1678)(Pwf,psi)(Pr,psi) / (Mscf/D) is equal to a value of one, then the Shell correlation indicates more rate to be above critical is necessary than Turner would predict. For high values of A, then the Shell correlation can show required rates less than Turner would predict. See Figure B-1 to see the Shell correlation illustrated. See Figure B-2 to see a comparison of the Turner¹, Coleman² and Kees⁷ correlations on ones set of coordinates.

The main discrepancies seem to lie with the lower wellhead pressure data. In Appendix C, some measured data is presented taken at very low pressures. The data seems to come closest to the Coleman² predications.

## SUMMARY

The Turner correlation for critical velocity and rate was correlated from well data with high surface pressures. It required a 20% adjustment to theory to fit the data best. The Coleman² correlation found that for well data with surface pressures of a few hundred psi (mostly all below 1000 psi), the 20% adjustment was not required to fit the data. The Shell correlation⁷ is more detailed, but for lower wellhead pressures, it shows required velocities and rates higher than for the Turner correlation. For higher wellhead pressures, the Shell correlation can predict critical values lower than Turner. Measured lab data at very low pressures seem to fit the Coleman² model best.

At present confusion exists as to what correlation to use. The Coleman² correlation seems attractive since it uses well data with a few hundred psi wellhead pressures to develop the correlation and its the model without an adjustment to fit theory to data as Turner found. The Shell correlation is more detailed, but shows more velocity and rate needed at low pressures than other correlations. A better model or correlation or a more accurate and extensive data base/s can provide direction for future work.

# REFERENCES

1. Turner, R. G.; Hubbard, M. G. and Dukler, A. E. “Analysis and Prediction of Minimum Flow Rate for the Continuous Removal of Liquids from Gas Wells”, J. Petroleum Technology, Nov. 1969. pp.1475-1482.

2. Coleman, S. B, Clay, H. B., McCurdy, D. G and Norris, H. L. III, “A New Look at Predicting Gas-Well Load Up”, Journal of Petroleum Technology, March, 1991, pp. 329-333

3. Trammel, P., & Praisnar, A., “Continuous Removal of Liquids from Gas Wells by use of Gas Lift” SWPSC, Lubbock, Texas, 1976, P. 139

4. Bizanti, M.S., and Moonesan, A., “How to Determine Minimum Flowrate for Liquid Removal”, World Oil, September 1989, pp 71-73.

5. Nosseir, M.A., et al.,: ” A New Approach for Accurate Predication of Loading in Gas Wells Under Different Flowing Conditions”, SPE 37408, presented at the 1997 Middle East Oil Show in Bahrain, March 15-18, 1997.

6. Beggs, H. D. and Brill, J. P.:”A Study of Two-Phase Flow in Inclined Pipes”, Journal of Petroleum Technology, May, 1973, p. 607

7. Kees Veeken & Eelco Bakker, NAM, Paul Verbeek, Shell, The Netherlands, ”Evaluating Liquid Loading Field Data & Remedial Measures”, presented at the Gas Well De-Watering Forum, Denver CO, March 3-4, 2003

# Appendix A:
Derivation of Critical Velocity

Turner¹ studied a film forming on the walls of a well beginning to liquid load and also the velocity required to move liquid droplets upward in a tubing flow. It was found that the model of the droplet best fit the data.

# Liquid Transport in a Vertical Gas Well

![img-0.jpeg](img-0.jpeg)

Figure A-1: Film Model and Droplet Model Considered by Turner

Considering the droplet, the downward gravity force and the upward acting drag force on the droplet are:

$$F_{Gravity} = \frac{g}{g_C} (\rho_L - \rho_G) \times \frac{\pi d^3}{6}$$

Equation A-1

$$F_{Drag,UP} = \frac{1}{2g_C} \rho_G C_D A_d (V_G - V_d)^2 COS(\phi)$$

Equation A-2

Where:

$$g = \text{constant} = 32.17 \text{ ft/s}^2$$

$$g_c = 32.17 \text{ lbm-ft/lbf-s}^2$$

$$d = \text{droplet diameter}$$

$$\rho_L = \text{liquid density, lbm/ft}^3$$

$$\rho_g = \text{gas density, lbm/ft}^3$$

$$C_D = \text{drag coefficient}$$

$$A_d = \text{droplet projected area, ft}^2$$

$$V_g = \text{gas velocity, ft/sec}$$

$$V_d = \text{droplet velocity, ft/sec}$$

Set the gravity force to the drag force for the droplet:

$$F_G = F_D$$

Equation A-3

$$\frac{g}{g_C} (\rho_L - \rho_G) \frac{\pi d^3}{6} = \frac{1}{2g_C} \rho_G C_D A_d V_C^2 COS(\phi)$$

Equation A-4

Substituting $A_d = \pi d^2/4$ and solving for $V_C$ gives,

$$V_C = \sqrt{\frac{4g}{3} \frac{(\rho_L - \rho_G)}{\rho_G} \frac{d}{C_D COS(\phi)}}$$

Equation A-5

Hinze, AICHE Journal Sept 1955, shows that droplet diameter dependence can be expressed in terms of the dimensionless Weber number

$$N_{WE} = \frac{V_C^2 \rho_G d}{\sigma g_C} = 30$$

Equation A-6

Solving for the droplet diameter gives

$$d = 30 \frac{\sigma g_C}{\rho_G V_C^2}$$

Equation A-7

substituting into Equation A-1 gives

$$V_C = \sqrt{\frac{4g}{3} \frac{(\rho_L - \rho_G)}{\rho_G} \frac{30}{C_D COS(\phi)} \frac{\sigma g_C}{\rho_G V_C^2}}$$

Equation A-8

$$V_C = \left( \frac{40 g g_C}{C_D COS(\phi)} \right)^{1/4} \left( \frac{\rho_L - \rho_G}{\rho_G^2} \sigma \right)^{1/4}$$

Equation A-9

Turner$^1$ assumed a drag coefficient of $C_D = .44$ that is valid for fully turbulent conditions. Substituting the turbulent drag coefficient and values for g and $g_C$ gives:

$$V_C = 17.514 \left( \frac{\rho_L - \rho_G}{\rho_G^2} \sigma \right)^{1/4}, ft/s$$

Equation A-10

Where

$$\rho_f = \text{liquid density, lbm/ft}^3$$

$$\rho_g = \text{gas density, lbm/ft}^3$$

$\sigma$=surface tension, lbf/ft

Equation A-10 can be written for surface tension in dyne/cm units using lbf/ft = .00006852 dyne/cm:

$$V_{C} = 1.593 \left( \frac{\rho_{L} - \rho_{G}}{\rho_{G}^{2}} \sigma \right)^{1/4} ft/s$$

Equation A-11

Where:

$\rho_{L}$=liquid density, lbm/ft$^{3}$

$\rho_{G}$=gas density, lbm/ft$^{3}$

$\sigma$=surface tension, dyne/cm

For Gas gravity, $\gamma$g = 0.6, temperature, T=20°F & Gas deviation factor, Z = 0.9

$$\rho_{G} = 2.715 \times .6 \frac{P}{(460 + 120) \times .9} = .0031 P \text{ lbm/ft}^{3}$$

Equation A-12

Typical values for density and surface tension are:

Water density 67 = lbm/ft$^{3}$ Condensate density: 45 lbm/ft$^{3}$

Water surface tension: 60 dyne/cm Condensate surface tension: 20 dyne/cm

Coleman, et al., (Exxon)$^{2}$

$$V_{C,water} = 1.593 \left( \frac{67 - .0031 P}{(.0031 P)^{2}} 60 \right)^{1/4} = 4.434 \frac{(67 - .0031 P)^{1/4}}{(.0031 P)^{1/2}} ft/s$$

Equation A-13

$$V_{C,cond} = 1.593 \left( \frac{45 - .0031 P}{(.0031 P)^{2}} 20 \right)^{1/4} = 3.369 \frac{(45 - .0031 P)^{1/4}}{(.0031 P)^{1/2}} ft/s$$

Equation A-14

Turner et al.$^{1}$, (with 20% adjustment to fit data)

$$V_{C,water} = 5.321 \frac{(67 - .0031 P)^{1/4}}{(.0031 P)^{1/2}} ft/s$$

Equation A-15

$$V_{C,cond} = 4.043 \frac{(45 - .0031 P)^{1/4}}{(.0031 P)^{1/2}} ft/s$$

Equation A-16

$$Q(MMscf/D) = \frac{3.06 pAv}{(T - 460)Z}$$

Equation A-17

Where:

A = area, ft2

## Appendix B
Shell Correlation, Kees et al. \( ^{7} \)

### Comparing to Turner (Ref. (7))

Turner Ratio vs Best Fit Combination of A and FTHP

![img-1.jpeg](img-1.jpeg)

Figure B.1 - Shell correlation from Reference 7

The above correlation shows that at lower wellhead pressures (FTHP), that the required critical rate is more than Turner. This is an opposite effect compared to what Coleman et al. \( ^{2} \) found.

The Turner Ratio (TR) is ratio between actual and Turner

Best fit TR = 3.77 (A\( ^{0.5} \) x FTHP) -0.172

Inflow resistance A ~ (Pdd / Q)xPr [ bar\( ^{2} \) / 1000 m\( ^{3} \)/d ]

Or:

\(\mathrm{TR} = 3.77(\mathrm{A}^{0.5}\times \mathrm{FTHP},\mathrm{psi} / 14.5) - .172\)

\(\mathrm{A} = (0.1678)(\mathrm{Pwf},\mathrm{psi})(\mathrm{Pr},\mathrm{psi}) / (\mathrm{Mscf} / \mathrm{D})\)

Example-1:

Pwf = 300 psi

Pr = 800 psi

Mscf/D = 300

A = 134 psi\( ^{2} \)/Mscf/D

FTP = 100 psi

\(\mathrm{TR} = 3.77(134^{-5}\times 100 / 14.5)^{-172} = 1.77\)

Or in other words, or predicted critical velocity is 1.77 times the Turner predicted value.

Plotted comparisons between Turner \( ^{1} \) , Coleman et al. \( ^{2} \) , and Shell Nam \( ^{7} \) .

# CRITICAL RATE VS. FTP, DIA=1.995

![img-2.jpeg](img-2.jpeg)

Figure B.2 - Comparison of Turner¹, Coleman² and Kees⁷ Predictions for Required Critical Rate

## Appendix C
Some Measured Data

Because of the scatter in predictions for critical velocity, especially at low pressures, some additional tests to determine critical velocity were made in the flow and plunger test facility at Texas Tech Petroleum Engineering Department. This consists of a two inch ID plastic tube, 40 feet high, with flow and pressure instrumentation and with an air supply from a compressor and a build- tank.

![img-3.jpeg](img-3.jpeg)

Figure C.1 - Texas Tech Facility:

Data Collection Procedure:

The procedure was:

Determine the rate of water flow needed (for a given gas flow rate) attempting to achieve 20 bbl-water/MMscf. This was done by measuring the time to flow a given volume into the tubing.

Set the flow rate of air. Check to see water moving up. Run for 10 minutes and shut-off and read volume of fluid left in tubing. If the water level is less then reduce the gas (and liquid) and run again. If the water level is more then increase the gas rate (and liquid rate). If the fluid rate is constant before and after the test, then record the data.

Some data were recorded with some back pressure on top of the tubing.

The data shown in the below figure, is more in line with the Coleman et al.² data and is not expected to compare exactly to any of the correlations as they all were fit to wellhead pressures, for the most part, greater than in the below plot.

# Measured vs. Predicted Critical Rates

![img-4.jpeg](img-4.jpeg)

Figure C.2 - Turner¹, Coleman² and some pressure air-water very low pressure data.

The Turner critical velocity equation for salt water and natural gas is Equation A-15
For fresh water and air it becomes:

$$V_{C,water} = 5.321 \frac{(62.4 - .0049P)^{1/4}}{(.0049P)^{1/2}} ft/s$$

Equation C-1

The temperature was estimated at 90 F, the Z factor was used as 1.0 and the gravity of gas was 1.00 for air.
Fresh water was used for testing.

Also the above uses the same surface tension value as in Turner of 60 dynes/cm for water or .00411 lbf/ft
although water/air may be more like .00499 lbf/ft which would increase the predicted values by about 5%
(5% larger coefficient in above equation) leaving the measurements the same.