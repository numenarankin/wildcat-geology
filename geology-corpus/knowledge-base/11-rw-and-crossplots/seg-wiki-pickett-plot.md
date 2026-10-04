<!-- Source: seg-wiki-pickett-plot.pdf -->
<!-- Converted: mistral-ocr-latest -->

8/4/26, 7:37 PM

Pickett plot - SEG Wiki

# Pickett plot

A Pickett plot is a method used in petrophysical analysis to evaluate formation characteristics of conventional, granular reservoirs. It was developed by professor George Pickett. The method provides a graphical solution to Archie's equation to determine water saturation of a reservoir by plotting resistivity versus porosity on a log-log scale.[1]

## Contents

**Background**

Archie's Equations

Manipulation of Archie's Equations

Water/Hydrocarbon Saturation

**Construction[1][5]**

Step 1: Plot Reservoir Data Points

Step 2: Plot $R_w$

Step 3: Plot 100% $S_w$ Line

Step 4: Plot Remaining $S_w$ lines

**External Links**

**References**

## Background

The Pickett plot is based on a pattern recognition approach to solving Archie's equation without the need for many of the constants that are often unknown. One benefit to this pattern recognition approach is that the water saturation can be derived without having any calibration data for the porosity measuring device, including grain density, etc. as well as not having to know the resistivity of the formation water. The important aspect of the pattern recognition approach is that there must be a statistically significant number of zones plotted in order to provide accurate calculations. Additionally the unknown constants in Archie's equations must be relatively constant for the reservoirs. Nevertheless, the Pickett plot has become a powerful tool to characterize reservoirs with a simple, quick plot.[1]

## Archie's Equations

Archie's Equations describe the empirical relationship between the formation factor $F$, porosity $\phi$, water saturation $S_w$, and resistivities $R$, in granular rocks.[2]

https://wiki.seg.org/wiki/Pickett_plot

1/5

8/4/26, 7:37 PM

Pickett plot - SEG Wiki

$$\underline{F} = \frac{R_o}{R_w} = \frac{a}{\phi^m} eq. (1)$$

$$\underline{S_w^n} = \frac{R_o}{R_t} eq. (2)$$

Where:

$a$ = proportionality constant varying from 0.6 to 1.5

$m$ = cementation factor that varies between 1.3 and 3

$n$ = saturation exponent, often assumed to be 2

$R_o$ = resistivity of the formation when 100% saturated with formation water

$R_w$ = resistivity of the formation water

$R_t$ = true resistivity of the formation$^{[2]}$

### Manipulation of Archie's Equations

Solving for $R_o$ in equation (2) and plugging into equation (1) yields

$$\frac{R_t S_w^n}{R_w} = \frac{a}{\phi^m}$$

Isolate $\phi^m$ on the left hand side and take logarithms of both sides of the equation to obtain

$$m log(\phi) = log(a R_w) - log(R_t) - n log(S_w) \quad \text{eq. (3)}$$

Equation (3) describes a set of parallel lines on the Pickett plot that indicate water saturation, $S_w$.$^{[1][3]}$

### Water/Hydrocarbon Saturation

Determining water saturation, $S_w$, is an important step in characterizing a reservoir during hydrocarbon exploration. Water saturation is defined as the ratio of water volume to pore volume. Total volume of fluids in a given reservoir depends on two metrics: water saturation and porosity. Porosity is a rock's capacity to hold fluids. Porosity ranges from 0 to 1. Higher values correspond to greater amount of pore space, i.e. 0.25 porosity means that 1/4 of the rock has the potential to hold fluids$^{[4]}$. The pore space volume can then be determined in a reservoir by multiplying the porosity by the volume of the reservoir. Determining the water saturation by using Archie's equations and the associated Pickett plot can be used to further calculate Hydrocarbon saturation, $S_H$, where

https://wiki.seg.org/wiki/Pickett_plot

2/5

8/4/26, 7:37 PM

Pickett plot - SEG Wiki

$$S_{H} = 1 - S_{w}$$

Assuming the reservoir is fully saturated with fluids the volume of hydrocarbons can be estimated by multiplying the hydrocarbon saturation by the total pore space.

The volume of hydrocarbons determined by this method must be taken with caution. Firstly, that the full volume of hydrocarbons is not recoverable from a reservoir. Recovery rates are affected by many factors including the weight of the hydrocarbons and the relationship between the grains of the rock and the fluids. Lighter hydrocarbons such as gas are recovered at higher amounts whereas heavier oil is recovered less. Reservoirs can be 'oil wet' or 'water wet.' Oil wet reservoirs are where the grains of the rock are coated in oil and the water surrounds the oil coated grains. Water wet reservoirs have grains coated in water and the oil surrounds the water coated grains. Oil wet reservoirs typically are poor producers even if the volume of oil is significant.[4]

## Construction[1][5]

### Step 1: Plot Reservoir Data Points

Select reservoirs for evaluation from the well log. Plot the points on a 2x4 cycle log-log graph by using the true resistivity, $R_t$, on the x-axis and porosity, $\phi$, on the y-axis.

### Step 2: Plot $R_w$

Plot the point for the resistivity of the formation water, $R_w$. This point should be plotted at 100% porosity since it is accounting for only the resistivity of the water

and not the resistivity of the reservoir rock. The value of the resistivity can be obtained from logging reports or calculated from the spontaneous potential. If no data on $R_w$ is available continue to step 3.

![img-0.jpeg](img-0.jpeg)

Figure 1: Pickett plot construction step 1. Credit: AAPG Wiki: Pickett plot construction

### Step 3: Plot 100% $S_w$ Line

As seen in the manipulated Archie's equation, the slope of the $S_w$ lines comes from the cementation factor, $m$. If the porosity type is known then $m$ can be obtained from a table of empirical values. If not, then a value of $m = 2$ for clean sandstone is commonly used. To plot the 100% saturation line begin at

https://wiki.seg.org/wiki/Pickett_plot

3/5

8/4/26, 7:37 PM

Pickett plot - SEG Wiki

the $R_w$ point and draw a line with a slope of -m using a linear scale. When there is limited data about porosity type and/or $R_w$, an alternative option is to assume that there are fully saturated water zones in the reservoir and therefore plot the 100% Sw line at the most "southwest" edge of the data points

### Step 4: Plot Remaining $S_w$ lines

Mark the intercept of the 100% $S_w$ line and $R_t = 1$. Draw a line from this point towards the right, parallel to the x-axis. Mark where this line passes through the $R_t$ values of 2, 4, 6, 8, 14, and 20. Draw lines through these points parallel to the 100% $S_w$ line. These lines represent $S_w$ percentages of 71, 50, 41, 35, 27, and 22.

## External Links

AAPG Wiki, well log analysis for reservoir characterization:

![img-1.jpeg](img-1.jpeg)

Figure 2: Pickett plot construction step 2. Credit: AAPG Wiki: Pickett plot construction (http://wiki.aapg.org/Pickett_plot_construction)

![img-2.jpeg](img-2.jpeg)

Figure 3: Pickett plot construction step 3. Credit: AAPG Wiki: Pickett plot construction (http://wiki.aapg.org/Pickett_plot_construction)

http://wiki.aapg.org/Well_log_analysis_for_reservoir_characterization

Crain's Petrophysical Handbook, water saturation basics: https://www.spec2000.net/14-swbasics.htm

Crain's Petrophysical Handbook, water saturation crossplots: https://www.spec2000.net/14-swxplot.htm

AAPG Wiki, Pickett plot construction: http://wiki.aapg.org/Pickett_plot_construction

## References

1. [ Pickett, G., R., 1973, Pattern recognition as a means of formation evaluation: The Log Analyst,

https://wiki.seg.org/wiki/Pickett_plot

4/5

8/4/26, 7:37 PM

Pickett plot - SEG Wiki

vol. 14, no. 4, p. 3–11.]

2. [Archie, G. E., 1942, The electrical resistivity log as an aid in determining some reservoir characteristics: Petroleum Transactions of AIME 146: 54–62.]
3. [Krygowski, D. A., & Cluff, R. M. (2013). Pattern Recognition in a Digital Age: A Gameboard Approach to Determining Petrophysical Parameters. Retrieved March 19, 2018, from

![img-3.jpeg](img-3.jpeg)

Figure 4: Pickett plot construction step 4. Credit: AAPG Wiki: Pickett plot construction (http://wiki.aapg.org/Pickett_plot_construction)

https://library.seg.org/doi/pdf/10.1190/urtec2013-266%5D

4. [Crain, E.R., Crain's Petrophysical Handbook. Retrieved March 19, 2018, from https://spec2000.net/00-index.htm] Cite error: Invalid <ref> tag; name ":2" defined multiple times with different content
5. AAPG Wiki: Pickett plot construction. retrieved from http://wiki.aapg.org/Pickett_plot_construction</ref>

Retrieved from "http://wiki.seg.org/w/index.php?title=Pickett_plot&oldid=107889"

This page was last edited on 24 April 2018, at 02:50.

Content is available under the Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA) unless otherwise noted.

https://wiki.seg.org/wiki/Pickett_plot

5/5