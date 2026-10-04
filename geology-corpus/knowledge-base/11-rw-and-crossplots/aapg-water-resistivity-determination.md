<!-- Source: aapg-water-resistivity-determination.pdf -->
<!-- Converted: mistral-ocr-latest -->

8/4/26, 7:58 PM

Water resistivity determination - AAPG Wiki

# Water resistivity determination

From AAPG Wiki

It has been suggested that some portions of this article be split into multiple articles.

The most direct way of finding water resistivity ($R_w$) is to obtain a sample of formation water and measure its resistivity. However, this is seldom possible in practice, as formation water samples, if available, are invariably contaminated by mud filtrate. $R_w$ is therefore usually calculated, and there are three methods available for this purpose:

- SP method
- Archie equation

Development Geology Reference Manual

![img-0.jpeg](img-0.jpeg)

Series Methods in Exploration

Part Wireline methods

Chapter Determination of water resistivity

Author Roberto Peveraro

Link Web page (http://archives.datapages.com/data/alt-browse/aapg-special-volumes/me10.htm)

Store AAPG Store (http://store.aapg.org/detail.aspx?id=612)

https://wiki.aapg.org/Water_resistivity_determination

1/9

8/4/26, 7:58 PM

Water resistivity determination - AAPG Wiki

- Resistivity ratio method

## Contents

**SP method**

Principle

Procedure

Assumptions and limitations

**Archie equation**

Principle

Procedure

Assumptions and limitations

**Resistivity ratio method**

Principle

Procedure

Limitations

**Concluding remarks**

**See also**

**References**

**External links**

## SP method

https://wiki.aapg.org/Water_resistivity_determination

2/9

8/4/26, 7:58 PM

Water resistivity determination - AAPG Wiki

![img-1.jpeg](img-1.jpeg)

![img-2.jpeg](img-2.jpeg)

![img-3.jpeg](img-3.jpeg)

Figure 1 Example of a normal SP deflection. Figure 2 Example of a reverse SP deflection.[1] Copyright: Schlumberger Educational Services, 1987.

## Principle

The first step in the interpretation of the SP log is the establishment of “sand” and “shale” lines, as shown in Figure 1. These are arbitrary limits, with the sand lines normally representing the maximum deflection to the left and shale lines representing the maximum deflection to the right (in shales). Deflections to the left of the shale line are regarded as normal or negative, and correspond to porous and permeable zones containing a more saline interstitial water than the drilling mud ($R_w R_{mf}$).

If the mud is more saline than the formation water, the SP currents flow in the opposite direction and the corresponding deflection will be to the right of the shale line. Such a deflection is considered to be reversed or positive (Figure 2). If there is no salinity contrast between the mud and the formation water, no SP currents are generated and no deflection will be observed (SP = 0).

The magnitude of deflection from the shale base line to the maximum deflection developed in a thick, clean, waterbearing sand is referred to as the static SP, or SSP.

https://wiki.aapg.org/Water_resistivity_determination

3/9

8/4/26, 7:58 PM

Water resistivity determination - AAPG Wiki

Knowledge of the SSP is essential for the derivation of $R_w$, which is required for the calculation of water saturation in the uninvaded zone. The equation that relates the SSP to measurable quantities, namely, $R_w$ and $R_{mf}$, introduces values that are linearly related to their respective chemical activities. These values are referred to as equivalent resistivities and are denoted by $R_{we}$ and $R_{mfe}$. Thus, the standard equation that relates the SSP to the mud filtrate and uninvaded formation water resistivities is

$$\mathrm{SSP} = -K \log \left( \frac{R_{\mathrm{mfe}}}{R_{\mathrm{me}}} \right)$$

where $K$ is a constant, the value of which is dependent on the formation temperature. Usually,

$$K = 61 + 0.133 \mathrm{T}(^{\circ}\mathrm{F}) \text{ or } 65 + 0.24 \mathrm{T}(^{\circ}\mathrm{C})$$

Equation 1 is used in the quantitative interpretation of the SP log.

## Procedure

The procedure to determine $R_w$ from the SP is outlined as follows. The data required include the SP, the invaded zone resistivity, the formation temperature, and the mud and mud filtrate resistivities at the given formation temperature.

- After selecting on the log the zone in which water resistivity will be determined, the formation temperature is established and the values of mud and mud filtrate resistivity are corrected accordingly.
- The shale and sand lines are established, the bed boundaries on the SP curve are determined, and maximum SP inflection for that permeable bed are read off the log.
- If the bed was too thin for the SP to develop fully (beds thinner than 20 ft), the appropriate correction is applied from the charts.
- Charts supplied by logging companies permit the determination of $R_{mfe}/R_{we}$ from the SP and, from that, $R_{we}$.
- Finally, the true value of $R_w$ is derived from its equivalent $R_{we}$ value, again using the appropriate charts.

![img-4.jpeg](img-4.jpeg)

Figure 3 Log used in example of calculation of water resistivity. Copyright: the SP method. (From Western Atlas International; [2] courtesy of Atlas Wireline Division of Western Atlas.

An example of calculating $R_w$ by using the SP method is as follows. Figure 3 shows the log used in this example. The following charts are required:

https://wiki.aapg.org/Water_resistivity_determination

4/9

8/4/26, 7:58 PM

Water resistivity determination - AAPG Wiki

|   | Schlumberger 1989 | Western Atlas 1985  |
| --- | --- | --- |
|  Chart 1 | GEN-6 | 1-1  |
|  Chart 2 | GEN-9 | 1-5  |
|  Chart 3 | SP-3 | 2-1  |
|  Chart 4 | SP-1 | 2-2  |
|  Chart 5 | SP-2 | 2-3  |

# Given:

- $R_m = 2.5 \ \Omega$-m at temperature::$70^\circ$F
- $R_{mf} = 2.0 \ \Omega$-m at temperature::$70^\circ$F
- Hole diameter = 8 in.
- Surface temperature = temperature::$60^\circ$F
- BHT = temperature::$164^\circ$F at 10,500 ft

# From the log:

- SP deflection = 70 mV
- Bed thickness = 24 ft
- Short normal resistivity = 65 $\Omega$-m

# Calculations:

- Bed is from 8114 to depth::8138 ft.
- From Chart 1, using BHT = temperature::$164^\circ$F at depth::10,500 ft and surface temperature = temperature::$60^\circ$F: formation temperature $T_f$ at 8100 ft=temperature::$140^\circ$F.
- From Chart 2, using $R_m = 2.5 \ \Omega$-m at temperature::$70^\circ$F and $R_{mf} = 2.0 \ \Omega$-m at temperature::$70^\circ$F: $R_m = 1.3 \ \Omega$-m at temperature::$140^\circ$F and $R_{mf} = 1.0 \ \Omega$-m at temperature::$140^\circ$F.
- Shale baseline is two divisions left of depth column.
- Bed thickness is 8138 to depth::8114 ft = length::24 ft.
- SP deflection = -70 mV.
- Use Chart 3 to correct the SP. Use short normal resistivity, $R_{SN}$, for invaded-zone resistivity, $R_i$. This gives $R_i/R_m = R_{SN}/R_m = 65/1.3 = 50$. This SP correction factor is 1.07, giving a corrected SP of 1.07 $\times -70 = -75$ mV.
- From Chart 4, using SP corrected and $T_f$: $R_{mf}/R_{we} = 9.7$.
- $R_{we} = R_{mf}/(R_{mf}/R_{we}) = 1.0/9.7 = 0.103 \ \Omega$-m.
- From Chart 5, using $R_{we}$ and $T_f$: $R_w = 0.103 \ \Omega$-m at temperature::$140^\circ$F (no change).

# Assumptions and limitations

https://wiki.aapg.org/Water_resistivity_determination

5/9

8/4/26, 7:58 PM

Water resistivity determination - AAPG Wiki

It is assumed that all salts in solution in the fluids are NaCl or equivalent and that the beds are clay free. This method does not work for oil-based muds. Also, it does not give correct estimations of $R_w$ in hydrocarbon-bearing zones.

# Archie equation

## Principle

If a clean, water-bearing zone is present or can be assumed, $R_w$ can be calculated by using the Archie equation. The zone or permeable bed in which water resistivity is determined is selected on the log. This zone must be 100% water saturated and must not contain any clay or shale. The bed must be thick so that the deep investigation resistivity device is not affected by shoulder beds.

The water saturation equation in general form is

$$S_w^n = \frac{a R_w}{\phi^m R_t}$$

Let's assume for $a$, $m$, and $n$ the usual initial values of 1, 2, and 2, respectively (although other values for $a$, $m$, and $n$ may be more appropriate). We have

$$R_w = S_w^2 \phi^2 R_t$$

In a water zone, $S_w = 1$, thus Equation 4 becomes

$$R_w = \phi^2 R_t$$

Porosity ($\phi$) can be derived from logs. (For more information on methods to derive porosity and the Archie equation, see Standard interpretation. For more on deriving $R_t$, see Preprocessing of logging data.)

## Procedure

The procedure to determine $R_w$ from the Archie equation is outlined as follows. The data that are required include $R_t$ (or $R_o$) from deep-reading resistivity tools such as deep induction (ILd) or deep laterolog (LLd) and porosity log(s).

- After correlating logs for depth mismatch, a clean, water-bearing zone is located. If using an induction log, the minimum thickness should be length::15 ft. For a laterolog, the minimum thickness should be length::4 ft.
- Read $R_o$ ($= R_f$) from the resistivity log, and determine the porosity from logs or otherwise.
- Calculate $R_w$ from Equation (4a).

## Assumptions and limitations

https://wiki.aapg.org/Water_resistivity_determination

6/9

8/4/26, 7:58 PM

Water resistivity determination - AAPG Wiki

It is assumed that there are no clay or conductive minerals in the water-bearing zone, that the zone is clean, and that the invasion is shallow enough for resistivity tools to be unaffected by it. This method only works in clean, waterbearing reservoirs. It is typically unreliable in highly fractured or vuggy reservoirs.

# Resistivity ratio method

## Principle

In a clean, water-bearing zone, the following relationships can be obtained from application of the Archie equation in the uninvaded and invaded zones:

$$R_{\mathrm{t}} = \frac{a R_{\mathrm{w}}}{\phi^2 S_{\mathrm{w}}^2}$$

$$R_{\mathrm{xo}} = \frac{a R_{\mathrm{mf}}}{\phi^2 S_{\mathrm{xo}}^2}$$

In such a zone, $S_{\mathrm{w}} = S_{\mathrm{xo}} = 1$ and $a$ and $\phi$ are the same in both the flushed and uninvaded zones.

Dividing Equation 5 by Equation 6 gives

$$\frac{R_{\mathrm{t}}}{R_{\mathrm{xo}}} = \frac{R_{\mathrm{w}}}{R_{\mathrm{mf}}}$$

or

$$R_{\mathrm{w}} = \frac{R_{\mathrm{t}}}{R_{\mathrm{xo}}} R_{\mathrm{mf}}$$

$R_{\mathrm{t}}$ and $R_{\mathrm{xo}}$ are obtained from deep and shallow resistivity logs, and $R_{\mathrm{mf}}$ is at formation temperature.

## Procedure

The procedure for determining $R_{\mathrm{w}}$ from the resistivity ratio method is outlined as follows. The data that are required include $R_{\mathrm{t}}$ from ILd or LLd, $R_{\mathrm{xo}}$ from SFL or another shallow-reading resistivity device, $R_{\mathrm{mf}}$, and $T_{\mathrm{f}}$.

- After correlating logs for depth mismatch, locate a clean, water-bearing zone. If using an induction log, the minimum thickness should be length::15 ft. For a laterolog, the minimum thickness should be length::4 ft.
- Read $R_{\mathrm{t}}$ and $R_{\mathrm{xo}}$.
- Correct $R_{\mathrm{mf}}$ to the appropriate formation temperature ($T_{\mathrm{f}}$) value.
- Calculate $R_{\mathrm{w}}$ from Equation 8.

https://wiki.aapg.org/Water_resistivity_determination

7/9

8/4/26, 7:58 PM

Water resistivity determination - AAPG Wiki

Note that an equivalent “quick look” solution can be obtained by an overlay technique using logarithmically scaled $R_t$ and $R_{x0}$ logs. If one log is placed over the other and shifted so that the two curves coincide in clean, water-bearing zones, the 1 ohm-m line on the $R_{x0}$ log grid will lie on the $R_t$ grid at a value equal to $R_w/R_{mf}$. Since $R_{mf}$ is known, $R_w$ can then be easily calculated. Figure 4 shows an example of original and shifted logs indicating a $R_t/R_{mf}$ ratio of 0.45.

![img-5.jpeg](img-5.jpeg)

![img-6.jpeg](img-6.jpeg)

Figure 4 Example problem showing determination of $R_w$ from resistivity ratio.

## Limitations

This method is unreliable in fractured or vuggy reservoirs. It requires a reliable measurement of $R_{x0}$. Results can be questionable if the mud resistivity properties have varied significantly after drilling the zone to be analyzed.

## Concluding remarks

It is quite common and good practice to determine $R_w$ with more than one method, if possible, to check for consistency and reliability. Variations may occur in the $R_w$ values determined by the three methods outlined here. If this is the case, then the values obtained can be averaged. Once determined, $R_w$ is assumed to be constant throughout the formation being evaluated, unless local knowledge or clear SP log amplitude changes indicate otherwise.

## See also

- Difficult lithologies
- Dipmeters
- Formation evaluation of naturally fractured reservoirs
- Basic open hole tools
- Basic tool table
- Introduction to wireline methods
- Preprocessing of logging data
- Wireline formation testers
- Basic cased hole tools
- Standard interpretation
- Quick-look lithology from logs
- Borehole imaging devices

## References

1. Dewan, J. T., 1983, Essentials of modern open-hole log interpretation: Tulsa, OK, Penn Well Books.

https://wiki.aapg.org/Water_resistivity_determination

8/9

8/4/26, 7:58 PM

Water resistivity determination - AAPG Wiki

2. Western Atlas International, 1985, Atlas log interpretation charts: Houston, TX.

## External links

- Original content in Datapages (http://archives.datapages.com/data/alt-browse/aapg-special-volumes/me10.htm)

find literature about

Water resistivity determination

- Find the book in the AAPG Store (http://store.aapg.org/detail.aspx?id=612)

Retrieved from "https://wiki.aapg.org/index.php?title=Water_resistivity_determination&oldid=27079"

This page was last edited on 18 January 2022, at 17:26.

Content is available under Attribution-ShareAlike 3.0 Unported unless otherwise noted.

https://wiki.aapg.org/Water_resistivity_determination

9/9