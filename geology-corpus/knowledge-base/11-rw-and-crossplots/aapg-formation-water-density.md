<!-- Source: aapg-formation-water-density.pdf -->
<!-- Converted: mistral-ocr-latest -->

8/4/26, 7:58 PM

Formation water density - AAPG Wiki

# Formation water density

From AAPG Wiki

Formation water density is a function of three variables:

- Temperature
- Pressure
- Total dissolved solids (TDS)

It is the mass of the formation water per unit volume of the formation water and is given in metric units (g/cm³). For reservoir engineering calculations, it is considered equivalent to specific gravity.

## Contents

Estimating density from TDS

Procedure: estimating density from r_w

Gather data

Determine NaCl concentration from r_w

Estimate density

See also

References

External links

Exploring for Oil and Gas Traps

![img-0.jpeg](img-0.jpeg)

Series Treatise in Petroleum Geology

Part Critical elements of the petroleum system

Chapter Formation fluid pressure and its application

Author Edward A. Beaumont, Forrest Fiedler

Link Web page (http://archives.datapages.com/data/specpubs/beaumont/ch05/ch05.htm)

Store AAPG Store (http://store.aapg.org/detail.aspx?id=545)

## Estimating density from TDS

If TDS is known from a chemical analysis of formation water, then the formula below can be used to estimate formation water density (ρ_w):[1]

$$\rho_w = 1 + \text{TDS} \times 0.695 \times 10^{-6} \text{ g/cm}^3$$

## Procedure: estimating density from r_w

Use the procedure outlined in the table below to estimate formation water density at reservoir conditions using R_w. The approximate error is ±10% (after [1]).

1. Gather data: formation temperature (T_f), water resistivity (R_w), and formation pressure. Estimate pressure by multiplying depth by 0.433 psi/ft or other appropriate gradient. Check for T_f errors.
2. Estimate sodium chloride (NaCl) concentration from R using Figure 1.

https://wiki.aapg.org/Formation_water_density

1/3

8/4/26, 7:58 PM

Formation water density - AAPG Wiki

3. Estimate density from wt % NaCl and temperature using Figure 2.

## Gather data

To estimate formation water density, collect estimates of the following:

- Formation temperature
- Formation pressure
- Formation water resistivity

1. Estimate formation temperature $T_f$ using the following formula:

$$T_f = T_s + D_f \left( BHT - \frac{T_s}{TD} \right)$$

where:

$T_s$ = average surface temperature (°F)
$D_f$ = depth to the formation (ft)
BHT = bottom-hole temperature (found on log header) (°F)
TD = total depth (BHT and TD must be from the same log run) (ft)

2. Estimate formation pressure (psi) by multiplying 0.433 (freshwater gradient) by formation depth.
3. Obtain formation water resistivity $R_w$ [ohm.m] in one of three ways:

- From a sample of water from the formation of interest measured for $R_w$
- Using a water catalog
- Calculating it from an SP log

![img-1.jpeg](img-1.jpeg)

Figure 1 Determining NaCl concentration.

Copyright: Schlumberger.

![img-2.jpeg](img-2.jpeg)

Figure 2 Use to estimate formation water density from ppm NaCl and temperature. Copyright: Gearhart-Owens.[2]

## Determine NaCl concentration from $r_w$

The predominant solute in most formation water is sodium chloride (NaCl). Its concentration determines formation water density and $R_w$. When only $R_w$ is available, we can use NaCl concentration to determine density.

https://wiki.aapg.org/Formation_water_density

2/3

8/4/26, 7:58 PM

Formation water density - AAPG Wiki

Use Figure 1 to determine NaCl concentration. At the intersection of formation temperature (from Y-axis) and Rw (from X-axis), find the NaCl concentration (in ppm) by reading diagonal line labels and interpolating.

## Estimate density

Estimate formation water density from ppm NaCl and temperature using the chart in Figure 2. The following table describes the procedure to use with the chart.

1. Enter the chart along the X-axis using formation temperature.
2. Proceed vertically to the appropriate salt concentration expected in the zone.
3. Proceed horizontally to read the liquid density at atmospheric pressure.
4. Using the "Effects of Pressure" segment of the chart, add a density increment to the above-computed density to correct for pressure effects.

## See also

- Determining hydrostatic pressure gradient

## References

1. Collins, A., G., 1987, Properties of produced waters, in Bradley, H., B., eds., Petroleum Engineering Handbook: Dallas, SPE, p. 24-1–24-23.
2. Gearhart-Owens Industries, 1972, GO Log Interpretation Reference Data Handbook: Fort Worth, Gearhart-Owens Industries Inc., 226 p

## External links

- Original content in Datapages (http://archives.datapages.com/data/specpubs/beaumont/ch05/ch05.htm)

- Find the book in the AAPG Store (http://store.aapg.org/detail.aspx?id=545)

find literature about

Formation water density

Retrieved from "https://wiki.aapg.org/index.php?title=Formation_water_density&oldid=28125"

This page was last edited on 13 September 2022, at 15:19.

Content is available under Attribution-ShareAlike 3.0 Unported unless otherwise noted.

https://wiki.aapg.org/Formation_water_density

3/3