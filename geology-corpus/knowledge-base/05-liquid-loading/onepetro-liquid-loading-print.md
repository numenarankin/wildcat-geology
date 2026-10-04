<!-- Source: onepetro-liquid-loading-print.pdf -->
<!-- Converted: mistral-ocr-latest -->

8/4/26, 7:34 PM

Liquid loading | Society of Petroleum Engineers (SPE) | OnePetro

This content has not been peer-reviewed and was originally developed through collaborative crowdsourcing on PetroWiki.

# Liquid loading FREE

February 5, 2025

Liquid loading is a phenomenon of multiphase flow in which the liquid phase begins to accumulate when the gas velocity is not sufficient to transport it. This is a common problem in gas wells and can cause various consequences such as reduced or ceased production or increased risks to damage surface facilities. Water accumulation in pipeline systems can also lead to internal corrosion.

DOI: https://doi.org/10.2118/PW0554

Content License: FreeView

Publisher: Society of Petroleum Engineers (SPE)

Content Sub Type: Petrowiki Content

# Introduction

## Definition and mechanisms

Various liquid phases can be co-produced during natural gas production. These can be reservoir water and/or hydrocarbons (condensate). Before introducing liquid loading, it is important to know several important concepts related with multiphase flow. Superficial velocity describes the velocity of the individual phase if it was to occupy the entire cross-sectional area of the flow. Thus, it is defined by the ratio of the volumetric flow rate of the phase over the cross-sectional area of the flow. The portion of the cross-sectional area of the flow that is occupied by the liquid phase is referred to as the liquid holdup. Flow pattern, which describes the geometrical distribution of the liquid and gas phases, is determined by the superficial velocities, and fluid properties. Further influencing variables for the flow pattern can be the inclination angle and cross-sectional area/diameter of the pipe. Due to different pressure and temperature conditions, different flow patterns can occur at different depths/sections of the

https://onepetro.org/spe/general-information/1772/Liquid-loading

1/9

8/4/26, 7:34 PM

Liquid loading | Society of Petroleum Engineers (SPE) | OnePetro

production tubing or flow line. In gas wells, the superficial velocity of the gas phase must be sufficiently high to be able to lift the liquid portions of the production fluid.[1]

![img-0.jpeg](img-0.jpeg)

Figure 1: Flow pattern of a gas well over time from beginning (a) to cessation of production (d)[2].

As the reservoir pressure naturally decreases, gas velocity steadily decreases. This leads to a change in the flow pattern and ultimately to backflow or accumulation of the liquid components. This accumulating liquid creates backpressure, reduces production until it is completely extinguished, and is therefore highly undesirable. In addition, water accumulation in pipeline systems can lead to corrosion problems and intermittent flow patterns such as slug flow that can cause damage to the piping system and surface equipment. Figure 1 shows the development of a gas well over time until production ceases. Initially, the liquid phase is transported in the form of liquid film and entrained droplets with the gas phase continuously upward without backflow, shown in stage (a). This flow pattern is called annular flow. In stage (b), the gas velocity is no longer high enough to lift the entire liquid phase, and backflow occurs. The cross-sectional area available for gas flow steadily decreases. Step (c) finally shows the transition to a flow pattern consisting of alternating intermittent production of the gas phase and liquid phase. In the last stage (d), enough liquid accumulates to build up sufficient counterpressure against the formation pressure, which leads to the complete cessation of production.[2]

Various mechanisms are held responsible for the occurrence of liquid loading, although the main mechanisms responsible are disputed. The backflow of large droplets which can no longer be lifted in the gas flow, the backflow of the liquid film on the pipe wall and the occurrence of intermittent flow patterns are the most widespread and acknowledged
Skip to Main Content
explanations for the onset of liquid loading.

## Causes for liquid loading

https://onepetro.org/spe/general-information/1772/Liquid-loading

2/9

8/4/26, 7:34 PM

Liquid loading | Society of Petroleum Engineers (SPE) | OnePetro

Critical gas velocity is defined as the superficial gas velocity below which liquid loading occurs. It is impacted by many parameters, such as inclination angle, pipe diameter, fluid properties, and liquid velocity[3].

![img-1.jpeg](img-1.jpeg)

Figure 2: Effect of inclination angle on maximum liquid film thickness[4].

The inclination angle of the pipeline or wellbore can influence the backflow or the behavior of the liquid film on the tube wall. The critical gas velocity increases with increasing inclination angle first, which promotes the occurrence of liquid loading due to the increased gravitational force on the liquid film. On the other hand, the maximum thickness of the liquid film decreases with increasing inclination angle (Figure 2), that reduces the gas velocity required to transport it. The critical gas velocity increases first and then decreases as inclination angle increases from a horizontal to a vertical position[3].

The tube diameter mainly influences the maximum film thickness. Smaller tube diameters cause smaller film thicknesses, which leads to the liquid film reversal occurring at a lower superficial gas velocity. Smaller tubing diameter therefore leads to a lower critical gas velocity and thus to a lower risk of liquid loading[3].

The pressure in the system mainly influences the density of the gas produced. Higher pressures result in higher densities, which increases the ability of the gas to act on the liquid through shear stresses at the interface of the phases. This in turn lowers the critical gas velocity and delays the onset of liquid loading.[3]

## Modeling and prediction of liquid loading

Since liquid loading is highly undesirable, numerous models exist to predict their onset under given conditions. These are based on different concepts, which have already been briefly described under mechanisms. The most common ones will be briefly described in the following.

### Droplet removal model

The Droplet Removal Model defines the criterion for the critical gas velocity based on the liquid Ship to Main Content droplets transported in the gas stream. In the case of the critical velocity, there is a force equilibrium of the three acting forces, namely gravity FG, drag force FD, and buoyancy force FB

https://onepetro.org/spe/general-information/1772/Liquid-loading

3/9

8/4/26, 7:34 PM

Liquid loading | Society of Petroleum Engineers (SPE) | OnePetro

on the liquid droplet (see Figure 3). Drag force and buoyancy force act (in the vertical case) in the direction of the flow, and gravity acts in the opposite direction. If the former is predominate, the droplet is transported upward and no liquid loading occurs; if gravity predominates, the droplets fall back, which marks the beginning of liquid loading.

![img-2.jpeg](img-2.jpeg)

![img-3.jpeg](img-3.jpeg)

Figure 3: Droplet Removal Model: Acting forces on the liquid droplet[5].

Turner et al. (1969)[6] developed the following relation for the terminal velocity based on this concept:

$$v_t = \frac{1.593\sigma^{1/4}(\rho_L - \rho_g)^{1/4}}{\rho_g^{1/2}}$$

$v_t$ = Terminal velocity (ft/s)

$\rho_g$ = Gas density (lbm/ft³)

$\rho_L$ = Liquid density (lbm/ft³)

$\sigma$ = Surface tension (dyn/cm)

By comparison with field data, they found a critical gas velocity 20% higher than the terminal velocity determined by the developed formula. This 20% should include effects not taken into account, such as the shape of the liquid droplet (Relation assumes a spherical shape). Thus, if the gas superficial velocity is higher than 1.2 times the terminal velocity, no liquid loading occurs.

Coleman et. al (1991)[7] evaluated the above criterion and came to the conclusion that the critical velocity, which was assumed 20% higher than the terminal velocity by Turner et al. (1969), was based on wrong interpretation of the field data. Therefore, they recommended that Skipp et al. (2001) be consistent was not needed, and the critical gas velocity equaled the terminal velocity. Other improved models that emerged later based on this concept are Lie et al. (2001)[8], Wang

https://onepetro.org/spe/general-information/1772/Liquid-loading

4/9

8/4/26, 7:34 PM

Liquid loading | Society of Petroleum Engineers (SPE) | OnePetro

and Liu (2007)[9], and Belfroid et al. (2008)[10], which among others dealt with the influence of the inclination.[5]

## Film reversal model

Barnea (1986)[11] proposed two mechanisms for the onset of intermittent flow, namely the instability of annular flow that prevents a stable annular configuration and the liquid film bridging. The first criterion assumes that if the interfacial shear stress is not high enough to overcome the shear stress between the liquid and the borehole wall and the gravity acting on the film, film instability occurs leading to liquid film reversal and liquid loading (Figure 4a). Bridging may occur at high liquid holdup conditions, preventing continuous gas flow and initiating intermittent production (Figure 4b).

![img-4.jpeg](img-4.jpeg)

Figure 4: Film Reversal Model. (a): Film instability. (b) Bridging of liquid in the center of the wellbore marking transition to intermittent flow[12].

The following equations show the relationship between the liquid film thickness and the interfacial shear stress by Barnea (1986):

$$\tau_{i} = \frac{g (\rho_{L} - \rho_{g}) \sin \theta + \tau_{L} \frac{S_{L}}{A_{L}}}{S_{I} \left( \frac{1}{A_{L}} + \frac{1}{A_{G}} \right)}$$

$$\tau_{L} = f_{L} \frac{\rho_{g} U_{L}^{2}}{2}$$

Skip to Main Content

$$\tau_{i} = \frac{1}{2} f_{i} \rho_{g} \frac{U_{GS}^{2}}{\left( 1 - 2\tilde{\delta} \right)^{4}}$$

https://onepetro.org/spe/general-information/1772/Liquid-loading

5/9

8/4/26, 7:34 PM

Liquid loading | Society of Petroleum Engineers (SPE) | OnePetro

$$\tilde{\delta} = \delta/D$$

$$\tau_i = \text{Interfacial shear stress (N/m}^2\text{)}$$

$$\tau_L = \text{Shear stress between liquid film and pipe wall (N/m}^2\text{)}$$

$$S_I = \text{Gas and liquid interfacial perimeter (m)}$$

$$S_L = \text{Liquid wetted perimeter (m)}$$

$$f_i = \text{Interfacial friction factor (-)}$$

$$f_L = \text{Friction factor between liquid film and pipe wall (-)}$$

$$\rho_g = \text{Gas density (kg/m}^3\text{)}$$

$$\rho_L = \text{Liquid density (kg/m}^3\text{)}$$

$$U_{GS} = \text{Superficial gas velocity (m/s)}$$

$$U_L = \text{Actual liquid velocity (m/s)}$$

$$\theta = \text{Inclination angle (}^\circ\text{)}$$

$$\tilde{\delta} = \text{Dimensionless liquid film thickness (-)}$$

$$\delta = \text{Liquid film thickness (m)}$$

$$D = \text{Pipe diameter (m)}$$

When plotting the above equations for different liquid and gas superficial velocities, the intersection of the respective functions represents a steady-state solution for annular flow.

Barnea (1986) showed that solutions to the right of the minimum of the interfacial shear stress curve as a function of the liquid film thickness represent a negative velocity profile near the borehole wall, thus being unstable solutions, leading to intermittent flow and thus to the reversal of the liquid film and liquid loading.[5]

The underlying concept has since been used to develop many other models, such as Luo et al. (2014)[13] which incorporated the inclination angle effects.

Rastogi and Fan (2020)[14] use another approach to determine the liquid wall shear stress at the pipe bottom. When the liquid wall shear stress at the pipe bottom is negative, which means liquid film reversal occurs at the pipe bottom, liquid loading happens. This model captures well

https://onepetro.org/spe/general-information/1772/Liquid-loading

6/9

8/4/26, 7:34 PM

Liquid loading | Society of Petroleum Engineers (SPE) | OnePetro

the effects of inclination angle, liquid flow rate, gas and liquid density, and the pipe diameter on the critical gas velocity.

## Prevention and remediation

Besides the prediction by models, there are technical possibilities to diagnose liquid loading or remediate it to prevent reduced or stopped production.

### Symptoms of liquid loading

Various signs in the production data can indicate the onset of liquid loading. The first sign may be a deviation from the originally determined target decline curve. In the case of a completion without a packer, an increasing pressure difference between the surface casing pressure and the surface tubing pressure may indicate an accumulation of liquids in the annulus.

Furthermore, if a pressure survey is performed along the length of the well, a sudden change in the pressure gradient may indicate the presence of two different phases. Also, if liquid slug flow is detected at the surface facilities, liquid loading can be assumed.[1]

### Remediation methods

#### Velocity strings

The completion with a production tubing of a smaller diameter is called velocity string. Due to the smaller cross-sectional area, higher gas velocities and lower critical gas velocity are achieved, resulting in a lower probability of liquid loading.[1]

#### Surfactants

By introducing surfactants into the fluid to be produced, an attempt is made to reduce the interfacial tension between the phases and form a foam. This leads to a better mixing of the phases, which reduces the slip velocity (velocity difference between the actual gas and liquid velocities) between the gas and liquid phases. This in turn results in a lower liquid holdup, thus a lower mixing density and a lower gravitational pressure drop. Lower bottomhole pressure results in a higher flow rate, which counteracts liquid loading.[1]

#### Artificial lift

Artificial lift is another way to prevent liquid loading. Various artificial lift methods can be used, such as plunger lift, gas lift, sucker rod pumps, electric submersible pumps (ESP) or progressive cavity pumps (PCP) depending on the field conditions. By using artificial lift, additional external energy is introduced into the system to compensate for pressure losses, lower therefore the bottom hole pressure and to enhance the production rate. This again results in higher velocities and therefore better conditions to counter liquid loading.[1]

https://onepetro.org/spe/general-information/1772/Liquid-loading

7/9

8/4/26, 7:34 PM

Liquid loading | Society of Petroleum Engineers (SPE) | OnePetro

# References

1. ↑ 1.0 1.1 1.2 1.3 1.4 Lea, James F., and Lynn Rowlan. 2019. Gas Well Deliquification. Elsevier Science.

2. ↑ 2.0 2.1 Fernandez, J., G., Falcone, and C., Teodoriu. 2010. „Design of a High-Pressure Research Flow Loop for the Experimental Investigation of Liquid Loading in Gas Wells“. SPE Projects, Facilities & Construction 5 (02): 76–88. https://doi.org/10.2118/122786-PA.

3. ↑ 3.0 3.1 3.2 3.3 Rastogi, Ayush, and Yilin Fan. 2019. „Experimental Investigation and Modeling of Onset of Liquid Accumulation in Large- Diameter Deviated Gas Wells“. In Day 1 Mon, September 30, 2019, D011S009R003. Calgary, Alberta, Canada: SPE. https://doi.org/10.2118/196130-MS.

4. ↑ Rastogi, Ayush, and Yilin Fan. 2019. „Experimental Investigation and Modeling of Onset of Liquid Accumulation in Large- Diameter Deviated Gas Wells“. In Day 1 Mon, September 30, 2019, D011S009R003. Calgary, Alberta, Canada: SPE. https://doi.org/10.2118/196130-MS.

5. ↑ 5.0 5.1 5.2 Jia, Hao, Jianjun Zhu, Guangqiang Cao, Yingda Lu, Bo Lu, and Haiwen Zhu. 2022. „A Model Ranking Approach for Liquid Loading Onset Predictions“. SPE Production & Operations 37 (03): 370–82. https://doi.org/10.2118/209578-PA.

6. ↑ Turner, R.G., M.G. Hubbard, and A.E. Dukler. 1969. „Analysis and Prediction of Minimum Flow Rate for the Continuous Removal of Liquids from Gas Wells“. Journal of Petroleum Technology 21 (11): 1475–82. https://doi.org/10.2118/2198-PA.

7. ↑ Coleman, Steve B., Hartley B. Clay, David G. McCurdy, and Lee H. Norris III. 1991. „A New Look at Predicting Gas-Well Load-Up“. Journal of Petroleum Technology 43 (03): 329–33. https://doi.org/10.2118/20280-PA.

8. ↑ Li, Min, Sun Lei, and Shilun Li. 2001. „New View on Continuous-Removal Liquids from Gas Wells“. https://doi.org/10.2118/70016-MS.

9. ↑ Wang, Y. and Liu, Q. 2007. A New Method to Calculate the Minimum Critical Liquids Carrying Flow Rate for Gas Wells. Petroleum Geology & Oilfield Development in Daqing 266 (6): 82–85.

10. ↑ Belfroid, S. P. C., W. Schiferli, G. J. N. Alberts, C. a. M. Veeken, and E. Biezen. 2008. „Prediction Onset and Dynamic Behaviour of Liquid Loading Gas Wells“. https://doi.org/10.2118/115567-MS.

11. ↑ Barnea, D. 1986. „Transition from Annular Flow and from Dispersed Bubble Flow—Unified Models for the Whole Range of Pipe Inclinations“. International Journal of Multiphase Flow 12 (5): 733–44. https://doi.org/10.1016/0301-9322(86)90048-0.

12. ↑ Alsanea, Maziad, Camilo Mateus-Rubiano, and Hamidreza Karami. 2022. „Liquid Loading in Natural Gas Vertical Wells: A Review and Experimental Study“. SPE Production & Operations 37 (03): 554–71. https://doi.org/10.2118/209819-PA.

13. ↑ Luo, S., Kelkar, M., Pereyra, E., and Sarica, C. 2014. A New Comprehensive Model for Predicting Liquid Loading in Gas Wells. SPE Prod & Oper 29 (4): 337–349. SPE-172501-PA. https://doi.org/10.2118/172501-PA

14. ↑ Rastogi, Ayush, and Yilin Fan. 2020. „Experimental and Modeling Study of Onset of Liquid Accumulation“. Journal of Natural Gas Science and Engineering 73 (Januar): 103064. https://doi.org/10.1016/j.jngse.2019.103064.

Copyright 2012-2025, Society of Petroleum Engineers

Skip to Main Content

https://onepetro.org/spe/general-information/1772/Liquid-loading

8/9

8/4/26, 7:34 PM

Liquid loading | Society of Petroleum Engineers (SPE) | OnePetro

## Explore

Journals

Conferences

eBooks

Publishers

## Connect

About Us

Contact Us

Content Alerts

SPE Member Pricing

## Resources

Terms of Use

Privacy

Help

KBART

## Engage

Subscribe

Advertise

https://onepetro.org/spe/general-information/1772/Liquid-loading

9/9