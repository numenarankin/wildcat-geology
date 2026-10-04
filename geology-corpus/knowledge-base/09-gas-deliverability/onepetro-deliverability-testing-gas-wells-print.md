<!-- Source: onepetro-deliverability-testing-gas-wells-print.pdf -->
<!-- Converted: mistral-ocr-latest -->

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

This content has not been peer-reviewed and was originally developed through collaborative crowdsourcing on PetroWiki.

## Deliverability testing of gas wells FREE

January 27, 2025

This article summarizes the fundamental gas-flow equations, both theoretical and empirical, used to analyze deliverability tests in terms of pseudopressure. The four most common types of gas-well deliverability tests are discussed in separate articles: flow-after-flow, single-point, isochronal, and modified isochronal tests.

DOI: https://doi.org/10.2118/PW0198

Content License: FreeView

Publisher: Society of Petroleum Engineers (SPE)

Content Sub Type: Petrowiki Content

## Types and purposes of deliverability tests

Deliverability testing refers to the testing of a gas well to measure its production capabilities under specific conditions of reservoir and bottomhole flowing pressures (BHFPs). A common productivity indicator obtained from these tests is the absolute open flow (AOF) potential. The AOF is the maximum rate at which a well could flow against a theoretical atmospheric backpressure at the sandface. Although in practice the well cannot produce at this rate, regulatory agencies sometimes use the AOF to allocate allowable production among wells or to set maximum production rates for individual wells.

Another application of deliverability testing is to generate a reservoir inflow performance relationship (IPR) or gas backpressure curve. The IPR curve describes the relationship between surface production rate and BHFP for a specific value of reservoir pressure (that is, either the original pressure or the current average value). The IPR curve can be used to evaluate gas-well current deliverability potential under a variety of surface conditions, such as

https://onepetro.org/spe/general-information/1418

1/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

production against a fixed backpressure. In addition, the IPR can be used to forecast future production at any stage in the reservoir's life.

Several deliverability testing methods have been developed for gas wells. Flow-after-flow tests are conducted by producing the well at a series of different stabilized flow rates and measuring the stabilized BHP. Each flow rate is established in succession without an intermediate shut-in period. A single-point test is conducted by flowing the well at a single rate until the BHFP is stabilized. This type of test was developed to overcome the limitation of long testing times required to reach stabilization at each rate in the flow-after-flow test.

Isochronal and modified isochronal tests were developed to shorten tests times for wells that need long times to stabilize. An isochronal test consists of a series of single-point tests usually conducted by alternately producing at a slowly declining sandface rate without pressure stabilization and then shutting in and allowing the well to build to the average reservoir pressure before the next flow period. The modified isochronal test is conducted similarly, except the flow periods are of equal duration and the shut-in periods are of equal duration (but not necessarily the same as the flow periods).

## Theory of deliverability test analysis

The theoretical equations developed by Houpeurt[1] are exact solutions to the generalized radial-flow diffusivity equation, while the Rawlins and Schellhardt[2] equation was developed empirically. All basic equations presented here assume radial flow in a homogeneous, isotropic reservoir and therefore may not be applicable to the analysis of deliverability tests from reservoirs with heterogeneities, such as natural fractures or layered pay zones. These equations should not be used to analyze tests from hydraulically fractured wells during the fracture-dominated linear or bilinear flow periods. Finally, these equations assume that wellbore-storage effects have ceased. Unfortunately, wellbore-storage distortion may affect the entire test period in short tests, especially those conducted in low-permeability reservoirs.

## Theoretical deliverability equations

The early-time transient solution to the diffusivity equation for gases for constant-rate production from a well in a reservoir with closed outer boundaries, written in terms of pseudopressure, $p_p$,[3] is

Ski- to Main Content

$$p_p(p_s) - p_p(p_{wf}) = \frac{1.422 \times 10^6 qT}{k_g h} \times \left[ 1.151 \log \left( \frac{k_g t}{1.688 \phi \bar{\mu}_g \bar{c}_t r_w^2} \right) + s + Dq \right], \tag{1}$$

https://onepetro.org/spe/general-information/1418

2/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

where $p_s$ is the stabilized shut-in BHP measured before the deliverability test. In new reservoirs with little or no pressure depletion, this shut-in pressure equals the initial reservoir pressure, $p_s = p_i$, while in developed reservoirs, $p_s < p_i$.

The late-time or pseudosteady-state solution is

$$p_p(\overline{p}) - p_p(p_{wf}) = \frac{1.422 \times 10^6 qT}{k_g h} \times \left[ 1.151 \log \left( \frac{10.064 A}{C_A r_w^2} \right) - \frac{3}{4} + s + Dq \right], \tag{2}$$

where $\overline{p}$ is current drainage-area pressure. Gas wells cannot reach true pseudosteady state because $\mu_g(p)c_t(p)$ changes as $\overline{p}$ decreases. Note that, unlike $\overline{p}$, which decreases during pseudosteady-state flow, $p_s$ is a constant.

Eqs. 1 and 2 are quadratic in terms of the gas flow rate, $q$. For convenience, Houpeurt$^{[1]}$ wrote the transient flow equation as

$$\Delta p_p = p_p(p_s) - p_p(p_{wf}) = a_t q + b q^2, \tag{3}$$

and the pseudosteady-state flow equation as

$$\Delta p_p = p_p(\overline{p}) - p_p(p_{wf}) = a q + b q^2, \tag{4}$$

where

$$a_t = \frac{1.422 \times 10^6 T}{k_g h} \left[ 1.151 \log \left( \frac{k_g t}{1.688 \phi \overline{\mu_g c_t r_w^2}} \right) + s \right], \tag{5}$$

$$a = \frac{1.422 \times 10^6 T}{k_g h} \left[ 1.151 \log \left( \frac{10.06 A}{C_A r_w^2} \right) - \frac{3}{4} + s \right], \tag{6}$$

$$b = \frac{1.422 \times 10^6 T D}{k_g h}. \tag{7}$$

The coefficients of $q$ ($a_t$ for transient flow and a for pseudosteady-state flow) include the Darcy flow and skin effects and are measured in (psia$^2$/cp)/(MMscf/D) when $q$ is in MMscf/D. The Skip to Main Content coefficient of $q^2$ represents the inertial and turbulent flow effects and is measured in (psia$^2$/cp)/(MMscf/D)$^2$ when $q$ is in MMscf/D.

https://onepetro.org/spe/general-information/1418

3/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

The Houpeurt equations also can be written in terms of pressure squared and are derived directly from the solutions to the gas-diffusivity equation, assuming that $\mu_g z$ is constant over the pressure range considered. For transient flow,

$$\Delta p^2 = p_s^2 - p_{wf}^2 = a_t q + b q^2, \tag{8}$$

and for pseudosteady-state flow,

$$\Delta p^2 = \overline{p}^2 - p_{wf}^2 = a q + b q^2. \tag{9}$$

The flow coefficients are

$$a_t = \frac{1.422 \times 10^6 \overline{\mu}_g \overline{z} T}{k_g h} \left[ 1.151 \log \left( \frac{k_g t}{1.688 \phi \overline{\mu}_g \overline{c}_t r_w^2} \right) + s \right], \tag{10}$$

$$a = \frac{1.422 \times 10^6 \overline{\mu}_g \overline{z} T}{k_g h} \left[ 1.151 \log \left( \frac{10.06 A}{C_A r_w^2} \right) - \frac{3}{4} + s \right], \tag{11}$$

$$b = \frac{1.422 \times 10^6 \overline{\mu}_g \overline{z} T D}{k_g h}, \tag{12}$$

and

When the Houpeurt equation is presented in terms of pressure squared, the coefficients of $q$ are measured in psia$^2$/(MMscf/D) when $q$ is in MMscf/D, while the coefficient of $q^2$ is measured in units of psia$^2$/(MMscf/D)$^2$ when $q$ is in MMscf/D. For convenience, all equations and examples in this section are presented with $q$ measured in MMScf/D.

The pressure-squared form of the equation should be used only for gas reservoirs at low pressures (less than 2,000 psia) and high temperatures. To eliminate doubt about which equations to choose, use of the pseudopressure equations, which are applicable at all pressures and temperatures, is recommended. Consequently, all the analysis procedures in this section are presented in terms of pseudopressure.

An advantage of the pseudopressure form of the theoretical deliverability equation is that the flow coefficients are independent of the average reservoir pressure and, therefore, do not change as $\overline{p}$ decreases during a flow test conducted under pseudosteady-state flow unless $s$, $k$, or $A$ changes. Because the non-Darcy flow coefficient is a function of $\mu_g(p_{wf})$, the coefficient

https://onepetro.org/spe/general-information/1418

4/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

b will change slightly if the BHFP is changed. In contrast, because of the pressure dependency of the gas properties on average reservoir pressure, the flow coefficients for the pressure-squared form of the deliverability equation must be recalculated for every new $\overline{p}$ value. When s, k, or A changes with time, the only way to update the deliverability curve is to retest the well.

## Empirical deliverability equations

In 1935, Rawlins and Schellhardt$^{[2]}$ presented an empirical relationship that is used frequently in deliverability test analysis. The original form of their relation, given by Eq. 13 in terms of pressure squared, is applicable only at low pressures:

$$q = C \left( \overline{p}^2 - p_{wf}^2 \right)^n, \tag{13}$$

In terms of pseudopressure, Eq. 13 becomes

$$q = C \left[ p_p(\overline{p}) - p_p(p_{wf}) \right]^n, \tag{14}$$

which is applicable over all pressure ranges. In Eqs. 13 and 14, C is the stabilized performance coefficient and n is the inverse slope of the line on a log-log plot of the change in pressure squared or pseudopressure vs. gas flow rate. Depending on the flowing conditions, the theoretical value of n ranges from 0.5, indicating turbulent flow throughout a well's drainage area, to 1.0, indicating laminar flow behavior modeled by Darcy's law. The value of C changes depending on the units of flow rate and whether Eq. 13 or 14 is used. All equations and examples in this section are presented with q measured in MMscf/D.

Houpeurt proved that neither Eq. 13 nor Eq. 14 can be derived from the generalized diffusivity equation for radial flow of real gas through porous media. Although the Rawlins and Shellhardt equation is not theoretically rigorous, it is still widely used in deliverability analysis and has worked well over the years, especially when the test rates approach the AOF potential of the well and the extrapolation from test rates to AOF is minimal.

## Stabilization time

Unlike pressure-transient tests, the analysis techniques for conventional flow-after-flow and single-point tests require data obtained under stabilized flowing conditions. Although isochronal and modified isochronal tests were developed to circumvent the requirement of stabilized flow, they may still require a single, stabilized flow period at the end of the test. Consequently, there

https://onepetro.org/spe/general-information/1418

5/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

is a need to understand the meaning of stabilization time and have a method to estimate its value.

Stabilization time is defined as the time when the flowing pressure is no longer changing or is no longer changing significantly. Physically, stabilized flow can be interpreted as the time when the pressure transient is affected by the no-flow boundaries, either natural reservoir boundaries or an artificial boundaries created by active wells surrounding the tested well. Consider a graph of pressure as a function of radius for constant-rate flow at various times since the beginning of flow. As Fig. 1 shows, the pressure in the wellbore continues to decrease as flow time increases. Simultaneously, the area from which fluid is drained increases, and the pressure transient moves farther out into the reservoir.

![img-0.jpeg](img-0.jpeg)

Fig. 1 – Pressure distributions at increasing times.

The radius of investigation, the point in the formation beyond which the pressure drawdown is negligible, is a measure of how far a transient has moved into a formation following any rate change in a well. The approximate position of the radius of investigation at any time for a gas well is estimated by Eq. 15[4]:

$$r_{i} = \sqrt{\frac{k_{g}t}{948\phi\mu_{g}\overline{c}_{t}}}$$ ...(15)

Stabilized flowing conditions occur when the calculated radius of investigation equals or exceeds the distance to the drainage boundaries of the well (i.e., $r_{i} \geq r_{e}$). Substituting r e and rearranging Eq. 15, yields an equation for estimating the stabilization time, $t_{s}$, for a gas well centered in a circular drainage area:

https://onepetro.org/spe/general-information/1418

6/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

$$t_{s} = \frac{948 \phi \bar{\mu}_{g} \bar{c}_{t} r_{e}^{2}}{k_{g}} \tag{16}$$

As long as the radius of investigation is less than the distance to the no-flow boundary, stabilization has not been attained and the pressure behavior is transient. To illustrate the importance of stabilization times in deliverability testing, stabilization times were calculated as a function of permeability and drainage area for a well producing a gas with a specific gravity of 0.6 from a formation at 210°F and an average pressure of 3,500 psia

($\bar{\mu}_{g} = 0.02$ cp and $\bar{c}_{t} = 2.468 \times 10^{-4} \text{psia}^{-1}$), with a porosity of 10%. Table 1 shows that, for wells completed in low-permeability reservoirs, several days—or even years—are required to reach stabilized flow, while wells completed in high-permeability reservoirs stabilize in a short time.

|  TABLE 8.11—EFFECTS OF PERMEABILITY AND DRAINAGE AREA ON STABILIZATION TIME  |   |   |   |   |
| --- | --- | --- | --- | --- |
|   | A = 40 acres |   | A = 640 acres  |   |
|  k (md) | t_{s} (hours) | t_{s} (days or years) | t_{s} (hours) | t_{s} (days or years)  |
|  0.01 | 25.953 | 3 years | 415.242 | 47 years  |
|  0.1 | 2.595 | 108 days | 41.524 | 4.7 years  |
|  1.0 | 259.5 | 10.8 days | 4.152.4 | 173 days  |
|  10.0 | 25.55 | 1.1 days | 415.2 | 17.3 days  |
|  100.0 | 2.59 | 0.11 days | 41.52 | 1.73 days  |
|  1000.0 | 0.259 | 0.011 days | 4.15 | 0.173 days  |

### Table 1

A more general equation for calculating stabilization time is

$$t_{s} = \frac{\phi \bar{\mu}_{g} \bar{c}_{t} A t_{DA}}{0.0002637 k_{g}} \tag{17}$$

where $t_{DA}$ is dimensionless time for the beginning of pseudosteady-state flow. Values for $t_{DA}$ are given in Table 2 for various reservoir shapes and well locations. [5] The time required for the pseudosteady-state equation to be exact is found from the entry in the column "Exact for $t_{DA}$ >."

Skip to Main Content

https://onepetro.org/spe/general-information/1418

7/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

![img-1.jpeg](img-1.jpeg)

Table 2

![img-2.jpeg](img-2.jpeg)

Table 2

![img-3.jpeg](img-3.jpeg)

Table 2

The Rawlins-Schellhardt and Houpeurt deliverability equations assume radial flow. If pseudoradial flow has been achieved, however, these analysis techniques can be used for hydraulically fractured wells. The time to reach the pseudoradial flow regime, $t_{prf}$, occurs$^{[6]}$ at $t_{L_fD} = 3$ and is estimated with Skip to Main Content

https://onepetro.org/spe/general-information/1418

8/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

$$t_{\text{prf}} = \frac{11,400 \phi \bar{\mu}_g \bar{c}_t L_f^2}{k_g} \tag{18}$$

To illustrate the importance of achieving pseudoradial flow during a deliverability test, values of $t_{\text{prf}}$ were calculated for a hydraulically fractured well completed in a reservoir with $\phi = 0.15$, $\bar{\mu}_g = 0.03$ cp, and $\bar{c}_t = 1 \times 10^{-4}$ psia$^{-1}$ and with the range of permeabilities and hydraulic fracture half-lengths in Table 3. The results illustrate that a well with a long fracture in a low-permeability formation will take far too long to stabilize for conventional deliverability testing.

|  TABLE 8.12—EFFECTS OF PERMEABILITY AND HYDRAULIC FRACTURE HALF-LENGTH ON TIME TO REACH PSEUDORADIAL FLOW  |   |   |   |
| --- | --- | --- | --- |
|  Case | x (md) | L_{f} (ft) | t_{prf} (hours)  |
|  1 | 1 | 100 | 51.2  |
|  2 | 0.01 | 100 | 5,120 (213 days)  |
|  3 | 0.01 | 1,000 | 512,000 (58 years)  |

Table 3

# Nomenclature

|  a | = | $$\frac{1.422 \times 10^6}{k_g h} \left[ 1.151 \log \left( \frac{10.06 A}{C_A r_w^2} \right) - \frac{3}{4} + s \right]$$, stabilized deliverability coefficient, psia^{2}-cp/MMscf-D  |
| --- | --- | --- |
|  a_{f} | = | $$\sqrt{L_f^2 + b_f^2}$$, depth of investigation along major axis in fractured well, ft  |
|  a_{t} | = | $$\sqrt{L_f^2 + b_f^2}$$, transient deliverability coefficient, psia^{2}-cp/MMscf-D  |
|  A | = | drainage area, sq ft  |
|  A | = | $$\pi a_f b_f$$, area of investigation in fractured well, ft^{2}  |
|  b | = | $$\frac{1.422 \times 10^6 T D}{k g h}$$ (gas flow equation)  |

https://onepetro.org/spe/general-information/1418

9/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

|  $$b_f$$ | = | $$0.02878 \left[ \frac{kt}{\phi \mu c_t} \right]^{1/2}$$, depth of investigation of along minor axis in fractured well, ft  |
| --- | --- | --- |
|  $$\overline{c}_t$$ | = | total compressibility evaluated at average drainage area pressure, psi$$^{-1}$$  |
|  $$D$$ | = | non-Darcy flow constant, D/Mscf  |
|  $$h$$ | = | net formation thickness, ft  |
|  $$k_g$$ | = | permeability to gas, md  |
|  $$L_f$$ | = | fracture half length, ft  |
|  $$n$$ | = | inverse slope of the line on a log-log plot of the change in pressure squared or pseudopressure vs. gas flow rate  |
|  $$p$$ | = | pressure, psi  |
|  $$\overline{p}$$ | = | volumetric average or static drainage-area pressure, psi  |
|  $$p_p$$ | = | pseudopressure, psia$$^2$$/cp  |
|  $$p_{wf}$$ | = | flowing BHP, psi  |
|  $$q$$ | = | flow rate at surface, STB/D  |
|  $$t_{prf}$$ | = | time required to reach the pseudoradial flow regime, hours  |
|  $$t_s$$ | = | time required for stabilization, hours  |
|  $$T$$ | = | reservoir temperature, °R  |
|  $$\Delta p$$ | = | pressure change since start of transient test, psi  |
|  $$\overline{\mu}_g$$ | = | gas viscosity evaluated at average pressure, cp  |
|  $$\phi$$ | = | porosity, dimensionless  |

Skip to Main Content

# References

1. ↑ 1.0 1.1 Houpeurt, A. 1959. On the Flow of Gases in Porous Media. Revue de L'Institut Francais du Petrole 14 (11): 1468.

https://onepetro.org/spe/general-information/1418

10/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

2. ↑ 2.0 2.1 Rawlins, E.L. and Schellhardt, M.A. 1935. Backpressure Data on Natural Gas Wells and Their Application to Production Practices, Vol. 7. Monograph Series, USBM.
3. ↑ Al-Hussainy, R., Jr., H.J.R., and Crawford, P.B. 1966. The Flow of Real Gases Through Porous Media. J Pet Technol 18 (5): 624-636. http://dx.doi.org/10.2118/1243-A-PA.
4. ↑ Lee, W.J. 1977. Well Testing, Vol. 1. Richardson, Texas: Textbook Series, SPE.
5. ↑ Earlougher, R.C. Jr. 1977. Advances in Well Test Analysis, Vol. 5. Richardson, Texas: Monograph Series, SPE.
6. ↑ Lee, W.J. 1989. Postfracture Formation Evaluation. In Recent Advances in Hydraulic Fracturing, J.L. Gidley, S.A. Holditch, D.E. Nierode, and R.W. Veatch Jr. eds., Vol. 12. Richardson, Texas: Monograph Series, SPE.

Copyright 2012-2025, Society of Petroleum Engineers

# **Explore**

Journals

Conferences

eBooks

Publishers

# **Connect**

About Us

Contact Us

Content Alerts

SPE Member Pricing

# **Resources**

Terms of Use

Privacy

Help

KBART

# **Engage**

Subscribe

Advertise

Skip to Main Content

https://onepetro.org/spe/general-information/1418

11/12

8/4/26, 7:36 PM

Deliverability testing of gas wells | Society of Petroleum Engineers (SPE) | OnePetro

https://onepetro.org/spe/general-information/1418

12/12