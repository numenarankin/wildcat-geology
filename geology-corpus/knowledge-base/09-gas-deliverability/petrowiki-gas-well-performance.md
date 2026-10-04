<!-- Source: https://petrowiki.org/Gas_well_performance -->
<!-- Converted: html2text (manually downloaded) -->

Advertisement

[ _Open Menu_ ](javascript:;)

__Search Dropdown Menu

[Advanced Search](https://onepetro.org/advanced-search)

[ Cart __ ](https://onepetro.org/store/cart)

_User Tools Dropdown_

[ Cart __ ](https://onepetro.org/store/cart)

[Register](https://onepetro.org/my-account/register?siteId=1000201&returnUrl=%2fspe%2fgeneral-information%2f1653%2fGas-well-performance)

Sign In _Open Menu_

[ ](https://onepetro.org/SPE)

[_Toggle Menu_ Menu](javascript:;)

Share

  * _Facebook Icon_
  * _X Icon_
  * _LinkedIn Icon_


This content has not been peer-reviewed and was originally developed through collaborative crowdsourcing on PetroWiki.

#  Gas well performance __

January 28, 2025

This page deals with methods for analyzing and predicting the performance of producing natural-gas wells. Steady-state-, pseudosteady-state-, and transient-flow concepts are developed, resulting in a variety of specific techniques and empirical relationships for both testing wells and predicting their future performance under different operating conditions. 

[](javascript:;)

[](mailto:\(\))

[](https://onepetro.org/spe/general-information/1653/Gas-well-performance)

DOI:https://doi.org/10.2118/PW0434

Content License:FreeView

Publisher:Society of Petroleum Engineers (SPE)

Content Sub Type: [Petrowiki Content](https://onepetro.org/SPE/search-results?f_ArticleTypeDisplayName=Petrowiki+Content&fl_SiteID=1000201)

## Basic equations

The basis for all well-performance relationships is Darcy’s law, which in its fundamental differential form applies to any fluid—gas or liquid. However, different forms of Darcy’s law arise for different fluids when flow rates are measured at standard conditions. The different forms of the equations are based on appropriate equations of state (i.e., density as a function of pressure) for a particular fluid. In the resulting equations, presented next, flow rate is taken as being positive in the direction opposite to the pressure gradient, thus dropping the minus sign from Darcy’s law. When multiple-line equations are presented, the first will be in fundamental units, the second in oilfield units, and the third in SI units. 

Four different fluid representations are considered: 

  1. Liquid (small and constant compressibility)
  2. Real gas
  3. Approximate high-pressure gas
  4. Approximate low-pressure gas


### Steady-state radial horizontal liquid flow

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0996_eq_001.png "RTENOTITLE")....................(1) 

### Steady-state radial horizontal gas flow

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0996_eq_002.png "RTENOTITLE")....................(2) 

For liquids, the product of _B_ _o_ _μ_ _o_ is approximately constant over a fairly wide pressure range so that for practical purposes, **Eq. 1** can be written as 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0996_eq_003.png "RTENOTITLE")....................(3) 

where Δ _p_ = _p_ 2 \- _p_ 1 and [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0996_inline_001.png "RTENOTITLE") is evaluated at some average pressure between _p_ 1 and _p_ 2. The exact pressure at which the oil formation volume factor and viscosity are evaluated is not critical because the product of [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0996_inline_001.png "RTENOTITLE") is approximately constant. 

Because this approximation is not generally valid for gases, the steady-state radial gas-flow equation is written as 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0996_eq_004.png "RTENOTITLE")....................(4) 

where the real-gas potential Δ _m_[[1]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r1-1) is defined by 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0996_eq_005.png "RTENOTITLE")....................(5) 

**Fig. 1** shows a typical plot of _p_ /_μz_ vs. _p_. Twice the area under the curve between any two pressures represents the real-gas potential difference. Note that at high pressures, _p_ /_μz_ is approximately constant. Also, although it is not readily apparent from the plot, at low pressures the product _μz_ is approximately constant. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0997_image_0001.png "Fig. 1 – Typical plot of p/μz vs. p.")

**Fig. 1 – Typical plot of _p_ /_μz_ vs. _p_.**


Values for Δ _m_ are usually determined by numerically integrating **Eq. 5** using gas viscosity and _z_ -factor data from measurements or correlations. Typical results are shown in **Fig. 2**. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0998_image_0001.png "Fig. 2 – Example graph of real-gas potential vs. pressure.")

**Fig. 2 – Example graph of real-gas potential vs. pressure.**


Note that for ideal gases, _z_ = 1 and does not vary with pressure, resulting in the identity [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0997_inline_001.png "RTENOTITLE"). The steady-state radial-flow equation for an ideal gas is thus 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0997_eq_001.png "RTENOTITLE")....................(6) 

where [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0997_inline_002.png "RTENOTITLE"). 

To avoid numerical evaluation of Δ _m_ , which can be time-consuming if done by hand, it is sometimes useful to have two other approximate real-gas forms of each of the flow equations. These approximate forms are derived by noting that for most natural gases at low pressures (i.e., less than approximately 2,000 psia, or 14 MPa), the product _μ_ _g_ _z_ is approximately constant. Under these conditions, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0997_eq_002.png "RTENOTITLE")....................(7) 

Both _μ_ _g_ and _z_ should be evaluated at some average pressure between the two pressures. The specific value of average pressure used is not very significant because the product _μ_ _g_ _z_ is relatively constant, as demonstrated in **Fig. 3**. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0999_image_0001.png "Fig. 3 – Example showing that μgz is approximately constant at < 2,000 psia.")

**Fig. 3 – Example showing that _μ gz_ is approximately constant at < 2,000 psia.**


At high pressures (i.e., greater than approximately 2,000 psia, or 14 MPa), for most natural gases the product of _μ_ _g_ _β_ _g_ is relatively constant (see **Fig. 4** for an example). 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1000_image_0001.png "Fig. 4 – Example graph showing that the product μgBg is approximately constant for gases at pressures greater than approximately 2,000 psia.")

**Fig. 4 – Example graph showing that the product _μ gBg_ is approximately constant for gases at pressures greater than approximately 2,000 psia.**


This means that 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0998_eq_001.png "RTENOTITLE")....................(8) 

Note that the conversion between the real-gas potential in oilfield vs. SI units is 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0998_eq_002.png "RTENOTITLE")....................(9) 

So that one simplified set of equations can be used throughout the remainder of the chapter, some additional parameters will be defined. First, a "generic" potential difference, Δ _ψ_ , can be expressed for each of the fluid cases according to **Table 1**. 

A general radial-flow equation can then be expressed for all cases as 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0998_eq_003.png "RTENOTITLE")....................(10) 

where _β_ is given by the following expressions, which include the unit conversions necessary to apply **Eq. 10**. The first line of each equation is in fundamental units, the second in oilfield units, and the third in SI units. 

_Liquids_ (_β_ units are psi-md-ft-D/STB, kPa-m2-m-d/std m3). 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0999_eq_001.png "RTENOTITLE")....................(11) 

_Real Gases_ (_β_ units are psi2-md-ft-D/Mscf/cp, kPa2•m2•m•d/std m3/mPa•s). 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0999_eq_002.png "RTENOTITLE")....................(12) 

_High-Pressure Gases (approximate)_ (_β_ units are psi-md-ft•D/Mscf, kPa•m2•m•d/std m3). 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0999_eq_003.png "RTENOTITLE")....................(13) 

_Low-Pressure Gases (approximate)_ (_β_ units are psia2-md-ft-D/Mscf, kPa2•m2•m•d/std m3). 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1000_eq_001.png "RTENOTITLE")....................(14) 

To concentrate on the specifics of well flow, in the remainder of the chapter the subscript _e_ will refer to an external drainage radius, and the subscript _wf_ will refer to pressure at the inlet sandface of a flowing well. 

## Skin

Sometimes wells experience near-wellbore phenomena (e.g., fractures and mud-filtrate damage) that cause production to be different from that calculated by Darcy’s law. These near-wellbore effects are often very complex. Their total effect is normally characterized with the use of a skin factor, _S_ , which appears in the steady-state radial-flow equation as 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1000_eq_002.png "RTENOTITLE")....................(15) 

Skin is a dimensionless parameter treated mathematically as an infinitely thin damaged or stimulated zone, regardless of the actual dimensions of the altered zone. Positive values indicate well damage (decreased productivity). Negative values indicate well stimulation (increased productivity). **Fig. 5** shows a typical pressure profile for a well with a positive skin. Wells with formation damage, partially penetrating wells, and wells with significant pressure drops in their completions have positive skins. Hydraulically fractured wells have negative skins. In general, skin must be determined empirically, usually from pressure-transient tests. Further discussion of the physical meaning of skin is given in the section on pressure-transient analysis. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1001_image_0001.png "Fig. 5 – Pressure distribution in a reservoir with a positive skin.")

**Fig. 5 – Pressure distribution in a reservoir with a positive skin.**


## Non-darcy flow

In gas wells, there may be a significant non-Darcy component of flow that results in an additional potential difference that depends on the square of the flow rate. The non-Darcy effect appears in well-deliverability equations as a flow-rate-dependent skin, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1001_eq_001.png "RTENOTITLE")....................(16) 

where _S_ is the fixed or "mechanical" skin, and _S_ ′ represents the total apparent skin including non-Darcy effects. _D_ is called the non-Darcy-flow coefficient, having units of D/Mscf or d/std m3. Although the non-Darcy coefficient may be calculated from laboratory measurements of the non-Darcy coefficient, it is typically determined in the field from well tests. 

## Transient flow

At early times after a well has been put on production and at early times after a well has been shut in, flow occurs in a transient mode, making the steady-state forms of Darcy’s law inappropriate. To mathematically represent transient flow, the relationship between density and pressure and material-balance (continuity) relationships must also be considered. When combined with Darcy’s law, the result is the diffusivity equation, which in radial coordinates is 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1001_eq_002.png "RTENOTITLE")....................(17) 

Note that the generic potential _ψ_ is used in **Eq. 17**. This will be discussed further with regard to transient solutions for different fluid systems. 

It is useful to distinguish between four different time periods when dealing with solutions to **Eq. 17** (**Fig. 6**): 

  1. Early time
  2. Infinite-acting time
  3. Transition time
  4. Stabilized time


  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1002_image_0001.png "Fig. 6 – Pressure/time history for a well produced at constant rate. Stabilized time occurs after all drainage-volume boundaries are fully “felt” and the well enters either steady-state or pseudosteady-state flow.")

**Fig. 6 – Pressure/time history for a well produced at constant rate. Stabilized time occurs after all drainage-volume boundaries are fully “felt” and the well enters either steady-state or pseudosteady-state flow.**


Early time is dominated by wellbore, rather than reservoir, effects. During this time, little can be determined about the reservoir. This time may last from a few minutes to a few days. 

During infinite-acting time, however, well response is the same as a well being produced from an infinite reservoir. Most pressure-transient tests analyze data during this time period. Because all reservoirs are finite, however, this time must end. It does so when the well response is affected by a part of the outer boundary of the well’s drainage volume. 

Steady-state flow is characterized by pressures being constant with time, requiring that the outer boundary of the system be maintained at constant pressure and the well be kept at either constant pressure or constant rate. This flow regime applies to certain water-influx situations or fluid-injection projects. 

Pseudosteady-state flow occurs at late time in closed systems with a well produced at constant rate. Although pressures still change with time in pseudosteady state, all pressures everywhere in the reservoir decline at the same rate. This means that the pressure profile reduces uniformly throughout the reservoir. 

Transition time occurs between infinite-acting and late time. During the transition period, the outer drainage boundaries are being felt in succession, causing the shift from infinite-acting to late time to occur over some length of time. In regularly shaped drainage areas (e.g., circles and squares), transition time may not exist. In irregularly shaped drainage areas, particularly with a well placed off-center, transition time can be quite long. 

### Infinite-acting flow

The time of primary interest in pressure-transient testing is the infinite-acting period, the mathematical solution for which comes from the diffusivity equation, expressed with the following dimensionless variables. 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1003_eq_001.png "RTENOTITLE")....................(18) 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1003_eq_002.png "RTENOTITLE")....................(19) 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1003_eq_003.png "RTENOTITLE")....................(20) 

The subscript i refers to the initial conditions of the well’s drainage volume. Time is in hours for both dimensionless-time equations. 

At sufficiently large values of [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1003_inline_001.png "RTENOTITLE"), which are typical for most reservoir conditions, the solution can be mathematically approximated by 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1003_eq_004.png "RTENOTITLE")....................(21) 

This approximation is good to within 2% accuracy for [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1003_inline_001.png "RTENOTITLE") > 5 , within 1% accuracy for [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1003_inline_001.png "RTENOTITLE") > 8.5 , and essentially identical to [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1003_inline_001.png "RTENOTITLE") > 100.[[2]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r2-2)

Noting that the dimensionless potential at the well differs from the dimensionless potential at the wellbore radius (_r_ _D_ = 1) by the skin factor, the basic radial well flow equation used for most well-testing purposes is 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1003_eq_005.png "RTENOTITLE")....................(22) 

A graph of _ψ_ _wf_ vs. the logarithm of time is a straight line. This slope is the basis for much pressure-drawdown and -buildup testing. 

When predicting well performance, it is important to recognize when data are being collected during transient flow and to take into account the continuing decline in well deliverability until a steady-state or pseudosteady-state condition is established. 

### Pseudosteady state

In a closed drainage volume, once all the outer boundaries have been fully felt, a constant-rate well will experience pseudosteady-state flow. Because all pressures in the reservoir decline at the same rate during pseudosteady-state flow, the difference between reservoir pressures and the well pressure remains constant, even though both individually are changing with time. Because the resulting equation does not explicitly show a time dependence, the term pseudosteady state is used. Some authors also refer to this time period as "semisteady state." 

Because pressure differences remain constant during pseudosteady-state flow, the following equations can be written to represent well performance during this period.[[2]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r2-2)

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_eq_001.png "RTENOTITLE")....................(23) 

where _C_ _A_ is the Dietz shape factor, dimensionless. 

Because [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_inline_001.png "RTENOTITLE"), **Eq. 23** can also be written in a more usable engineering form as 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_eq_002.png "RTENOTITLE")....................(24) 

where [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_inline_002.png "RTENOTITLE"). 

The shape factor can be determined empirically from mathematical solutions to the diffusivity equation in closed systems. **Tables 1 and 2** provide a list of shape factors for different drainage shapes and well placements. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1005_image_0001.png "Table 1")

**Table 1**

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1006_image_0001.png "Table 2")

**Table 2**


For a well in a closed circle, the pseudosteady-state equation can also be written as follows, which is equivalent to having a shape factor of 31.62. 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_eq_003.png "RTENOTITLE")....................(25) 

This equation also works for a well in the center of a closed square or other regular shape by calculating an equivalent-radius circle: 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_eq_004.png "RTENOTITLE")....................(26) 

### Transient drainage radius

To simplify the flow equations, it is sometimes useful to use what has been called a transient drainage radius, defined by 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_eq_005.png "RTENOTITLE")....................(27) 

This drainage radius is defined so that it represents the radius out to which there is a significant pressure drop. 

During infinite-acting time, [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_inline_003.png "RTENOTITLE") because there has been little withdrawal from the reservoir, which means that 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_eq_006.png "RTENOTITLE")....................(28) 

or, equivalently, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1004_eq_007.png "RTENOTITLE")....................(29) 

Note that the product [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1005_inline_001.png "RTENOTITLE") is simply dimensionless time without the wellbore radius in the denominator. 

During pseudosteady-state time, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1005_eq_001.png "RTENOTITLE")....................(30) 

For a circular or equivalent square drainage area, it can be shown that 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1006_eq_001.png "RTENOTITLE")....................(31) 

The deliverability equation for wells can then be written in the following simplified form for all times: 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1007_eq_001.png "RTENOTITLE")....................(32) 

Note that pressures decline in proportion to the logarithm of time during infinite-acting time, while in pseudosteady state, pressures decline approximately in direct proportion to time. 

Another way to determine the onset of pseudosteady state is through knowledge of the drainage shape and reservoir parameters. **Tables 1** and **2** give times for the end of the infinite-acting period and for the beginning of time when the pseudosteady-state equation can be used. These tables use a dimensionless time based on drainage area, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1007_eq_002.png "RTENOTITLE")....................(33) 

## Estimating drainage shapes

With little effort, it is possible to make a reasonable approximation of well drainage volumes and shapes. The process is based on the following assumptions: 

  1. The volume drained by an individual well is proportional to its flow rate.
  2. Distance to a "no-flow" boundary between pairs of wells is proportional to each competing well’s flow rate.


The following technique can then be used to estimate the drainage area at a given time. Assign a flow rate to each well based on an average production over some reasonable time period. 

  1. Using assumption 2 above, assign no-flow points between pairs of wells.
  2. Sketch no-flow lines by connecting up no-flow points.
  3. Adjust the lines near reservoir boundaries to ensure that assumption 1 is satisfied. Make adjustments for variations in thickness and known geologic features (e.g., faults).


Although this process is fairly rough, it can give a reasonable estimate of the drainage areas of each well in a reservoir. 

## Radius of investigation

**Tables 1** and **2** list times for the end of the infinite-acting-flow period and the beginning of the pseudosteady-state-flow period. These times can be used to define a "radius of investigation." The physical meaning of the radius of investigation is that it represents the minimum radius at which a boundary could exist, but which has not yet been "felt" at a given time (usually meaning the time at the end of a drawdown test that has not yet been affected by a reservoir boundary). 

Thus, if [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1007_inline_001.png "RTENOTITLE") is the area-based dimensionless time that defines the end of the infinite-acting period for a circular drainage area, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1007_eq_003.png "RTENOTITLE")....................(34) 

Depending on the level of precision that would define the end of the infinite-acting period, the radius of investigation would have different values. If a 1% criterion is used, [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1007_inline_001.png "RTENOTITLE") is equal to 0.06, and 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1008_eq_001.png "RTENOTITLE")....................(35) 

Another common cutoff criterion is a [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1007_inline_001.png "RTENOTITLE") of 0.1, after which the pseudosteady-state solution is listed by Earlougher[[2]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r2-2) as being "exact" (probably to within the number of significant digits of one’s computer). With this criterion, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1008_eq_002.png "RTENOTITLE")....................(36) 

For practical purposes, it is reasonable to use what many authors recommend for the radius of investigation, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1008_eq_003.png "RTENOTITLE")....................(37) 

### Pressure-transient testing of gas wells

Refer to Pressure transient testing for detailed discussions of interpreting pressure-transient tests of gas wells. 

### Deliverability testing

Gas wells have historically been tested at a series of bottomhole pressures and rates to develop stabilized-deliverability relationships. One of the reasons for this is the importance of the non-Darcy flow contribution to well performance. A single-rate test cannot address this contribution. This section describes the types of tests typically run, along with their appropriate analysis techniques. 

### Stabilized-deliverability test

A stabilized deliverability, sometimes called a four-point or backpressure test, is conducted by producing a well at four rates (**Fig. 7[[3]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r3-3)**). In this test, each rate is run long enough to reach stabilized conditions. To be theoretically valid, "stabilized" should mean to pseudosteady state, although in practice tests are sometimes run only until little variation in well flowing pressure is observed. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1009_image_0001.png "Fig. 7 – Rate vs. time history of a stabilized deliverability test.\[3\]")

**Fig. 7 – Rate vs. time history of a stabilized deliverability test.[[3]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r3-3)**


The most widely used method of presenting such data was first suggested by Rawlins and Schellhardt.[[4]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r4-4) This method is not based on the pseudosteady-state-flow equations but is based on an empirical observation that Δ _p_ 2 vs. _q_ _g_ plotted on a log-log graph typically lies on a straight line (**Fig. 8**). The equation for a straight line on a log-log graph is 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1008_eq_004.png "RTENOTITLE")....................(38) 

The slope of the straight line on a log-log graph is 1/_n_. The easiest way to determine slopes on a log-log graph is to recall that differences in the run and rise of the line must be taken in terms of logarithms, so that if [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1008_inline_001.png "RTENOTITLE") and [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1008_inline_002.png "RTENOTITLE") are two points on the straight line, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1008_eq_005.png "RTENOTITLE")....................(39) 

A value of _n_ = 1 corresponds to Darcy (laminar) flow, while _n_ = 0.5 (slope= 2) corresponds to completely turbulent flow. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1010_image_0001.png "Fig. 8 – Typical gas-well stabilized-deliverability plot.\[3\]")

**Fig. 8 – Typical gas-well stabilized-deliverability plot.[[3]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r3-3)**


A parameter usually presented with this data is the absolute open flow (AOF) potential. The AOF may be found by extrapolating the log-log plot and reading the flow rate at a value of [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1009_inline_001.png "RTENOTITLE"). The value of _C_ is calculated from any point on the straight line but is perhaps easiest to calculate as 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1009_eq_001.png "RTENOTITLE")....................(40) 

An alternative is to write the deliverability equation in terms of AOF instead of the parameter _C_ : 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1009_eq_002.png "RTENOTITLE")....................(41) 

The AOF is sometimes used as a measure of a well’s potential flow capacity for regulatory and other purposes. 

A more accurate way to analyze the stabilized deliverability test is to use the following equation, which is simply an alternative algebraic form of **Eq. 32**. 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1009_eq_003.png "RTENOTITLE")....................(42) 

A Cartesian plot of Δ _ψ_ /_q_ _g_ vs. _q_ _g_ will yield a slope of _b_ and an intercept of _a_ (**Fig. 9**). The advantage of this approach is that _a_ and _b_ have physical meaning based on reservoir parameters and thus can be compared to what is known about well and reservoir properties. _C_ and _n_ , on the other hand, have no such physical meanings. One disadvantage of this approach is that it is often more difficult to find a good straight line. However, this is a vagary of using Cartesian rather than log-log plots and does not represent any actual degradation of the data. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1011_image_0001.png "Fig. 9 – Theoretical gas-well stabilized-deliverability plot.")

**Fig. 9 – Theoretical gas-well stabilized-deliverability plot.**


Once _a_ and _b_ are determined from the graph, the AOF using this approach is calculated by 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1010_eq_001.png "RTENOTITLE")....................(43) 

The second factor in **Eq. 43** represents the reduction in the AOF caused by non-Darcy effects. The AOF determined from the _a_ /_b_ approach is usually lower than that calculated from the _C_ /_n_ approach. 

### Isochronal tests

Another type of test often run on gas wells is the isochronal test. The difference between an isochronal test and a stabilized-deliverability test is that the flow periods are not run long enough to reach stabilized flow. This is done to shorten testing time and to conserve gas, particularly where no pipeline is available. **Fig. 10** shows a rate-vs.-time history for a typical isochronal test. Note that although the shut-in times are sufficiently long to approach initial reservoir pressure, the producing times are not long enough to reach pseudosteady state. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1011_image_0002.png "Fig. 10 – Rate-vs.-time history for a typical isochronal test.\[3\]")

**Fig. 10 – Rate-vs.-time history for a typical isochronal test.[[3]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r3-3)**


Lines are drawn through a Δ _p_ 2-vs.-_q_ _g_ (**Fig. 11**) or Δ _ψ_ /_q_ _sc_ -vs.-_q_ _sc_ plot (**Fig. 12**) at common producing times; that is, during each flowing period, pressures are read at fixed times since the initiation of flow. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1012_image_0001.png "Fig. 11 – Results of a typical isochronal test.")

**Fig. 11 – Results of a typical isochronal test.**

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1013_image_0001.png "Fig. 12 – Modified isochronal test analyzed by a/b analysis.")

**Fig. 12 – Modified isochronal test analyzed by _a/b_ analysis.**


For a given producing time, a line through the data should have a constant slope. This slope should be the same no matter what the producing time because the transient drainage radius does not depend on flow rate. Thus, from each flow period, data are plotted for identical producing times (**Fig. 11** or **Fig. 12**). 

Finally, an extended flow period (to stabilization) is run at one rate. A line is passed through this single stabilized point, with the same slope as the other isochronal lines. If properly conducted, this test has been shown to give results combrble to a stabilized-deliverability test. 

A modified isochronal test is also sometimes run in which the shut-in times are also shortened (**Fig. 13**). This type of test also works well if the value of pressure at the end of the last shut-in period is used in place of the average reservoir pressure. 

  * [](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1014_image_0001.png "Fig. 13 – Rate vs. time history for a typical modified isochronal test.\[3\]")

**Fig. 13 – Rate vs. time history for a typical modified isochronal test.[[3]](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_note-r3-3)**


## Using gas-well deliverability relationships

Single-well deliverability equations can be used for a variety of purposes, including the following: 

  * Prediction of flow-rate changes caused by changing reservoir pressure (i.e., during reservoir depletion over time)
  * Prediction of flow-rate changes caused by changing well flowing pressure resulting from production-equipment changes (e.g., compression)
  * Prediction of bottomhole-flowing-pressure changes caused by changing well rates


In general, the most theoretically valid deliverability equation should be used: 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1013_eq_001.png "RTENOTITLE")....................(44) 

The use of **Eq. 44** to solve for well flowing pressure is straightforward, except for the requirement to convert the generic potential ψ to actual pressure when using the real-gas potential _m_(_p_). The conversion of _m_(_p_) to p can be done either graphically or numerically with a computational algorithm (preferred). 

**Eq. 44** is a quadratic equation in flow rate, so when flow rate is being calculated from known pressures, the following can be used. 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1013_eq_002.png "RTENOTITLE")....................(45) 

In some circumstances, it may be desirable to use either the _C_ /_n_ equation, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1013_eq_003.png "RTENOTITLE")....................(46) 

or a productivity index (PI) equation, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1013_eq_004.png "RTENOTITLE")....................(47) 

for deliverability calculations. Both can be used in a similar manner, as described above. 

## Effects of skin

There are several ways to look at the physical effects attributable to skin. The first is in terms of a flow efficiency (FE), which is defined as the well productivity with skin compared to the no-skin case: 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1014_eq_001.png "RTENOTITLE")....................(48) 

The effective potential drop caused by skin also can be calculated as 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1014_eq_002.png "RTENOTITLE")....................(49) 

Some prefer to consider skin in terms of an effective wellbore radius, 

[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1014_eq_003.png "RTENOTITLE")....................(50) 

It should be remembered that the skin in these equations is rate-dependent because of the non-Darcy effect. To determine the two different components of skin, mechanical-vs.-non-Darcy pressure-buildup or -drawdown tests must be run at more than one rate. If multirate transient tests are run, a simple plot of _S_ ′ vs. _q_ _g_ will yield a slope of _D_ and an intercept of _S_. 

## Nomenclature

_a_ | =  | empirical constant   
---|---|---  
_A_ | =  | drainage area, reservoir area, L2  
AOF  | =  | absolute open flow potential, std L3/t   
_b_ | =  | empirical constant   
_B_ | =  | formation volume factor, L3/std L3  
_B_ _gi_ | =  | initial gas formation volume factor, L3/std L3  
_c_ | =  | compressibility, Lt2/m   
_c_ _f_ | =  | pore-volume compressibility, Lt2/m   
_c_ _w_ | =  | water compressibility, Lt2/m   
_C_ | =  | constant in gas-deliverability equation   
_C_ _A_ | =  | Dietz shape factor, dimensionless   
_D_ | =  | non-Darcy-flow coefficient, t/std L3  
_E_ _fw_ | =  | cumulative formation and water expansion, L3  
_E_ _g_ | =  | cumulative gas expansion, L3  
_E_ _R_ | =  | recovery efficiency, fraction   
_E_ _t_ | =  | total cumulative expansion, L3  
_E_ _v_ | =  | volumetric sweep efficiency, fraction   
_F_ | =  | cumulative reservoir voidage, L3  
_G_ | =  | original gas in place, std L3  
_GE_ | =  | gas equivalent, std L3/std L3  
_G_ _pc_ | =  | cumulative gas production during a period of constant rate, std L3  
_h_ | =  | average reservoir thickness, L   
_k g_ | =  | measured gas permeability, L2  
_k_ _l_ | =  | effective liquid permeability, L2  
_K_ | =  | parameter in Lee _et al._ 2 viscosity correlation   
_m_ | =  | real-gas potential, m/Lt2  
_M_ | =  | molecular weight   
_n_ | =  | number of moles of gas or exponent in gas-deliverability equation   
_n_ _c_ | =  | total number of components in gas mixture   
_n_ _w_ | =  | number of wells   
[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1033_inline_001.png "RTENOTITLE") | =  | relative number of total moles in gaseous phase, fraction   
[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1033_inline_002.png "RTENOTITLE") | =  | relative number of total moles in oil phase, fraction   
_N_ _p_ | =  | cumulative condensate production, std L3  
_p_ | =  | pressure, m/Lt2  
[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1033_inline_003.png "RTENOTITLE") | =  | average pressure, m/Lt2  
[](https://petrowiki.org/Gas well performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_1033_inline_004.png "RTENOTITLE") | =  | variable of integration in real-gas potential equation, m/Lt2  
_PI_ | =  | productivity index, std L3/t/m/Lt2  
_q_ | =  | production rate, std L3/t   
_q_ _c_ | =  | production rate during period of constant rate, std L3/t   
_q_ _R_ | =  | total reservoir gas production rate, std L3/t   
_r_ 1 | =  | radial distance at which pressure _p_ 1 is measured, L   
_r_ 2 | =  | radial distance at which pressure _p_ 2 is measured, L   
_R_ | =  | universal gas constant, mL2/nt2T   
_S_ | =  | mechanical skin, dimensionless   
_S_ ′  | =  | total skin, dimensionless   
_S_ _gi_ | =  | initial average gas saturation, fraction   
_S_ _wi_ | =  | initial water saturation, fraction   
_t_ | =  | time, t   
_t_ _c_ | =  | time of constant-rate production, t   
_T_ | =  | temperature, T   
_u_ | =  | volumetric flux ( q/A ), L3/t/L2  
_V_ | =  | volume, L3  
_V_ _m_ | =  | molar volume, L3/n   
_W_ _e_ | =  | cumulative water influx, L3  
_W_ _p_ | =  | cumulative water produced, std L3  
_x_ _j_ | =  | mole fraction of component j in liquid phase   
_X_ | =  | parameter in Lee _et al._ 2 viscosity correlation   
_y_ _j_ | =  | mole fraction of component _j_ in gaseous phase   
_Y_ | =  | produced condensate yield, std L3/std L3  
_z_ | =  | gas deviation factor, dimensionless   
_z_ _j_ | =  | mole fraction of component j in mixture   
_α_ | =  | cubic equation-of-state parameter   
_α_ _c_ | =  | empirical constant   
_β_ | =  | defined in **Eq. 11**  
_ρ_ | =  | density, m/L3  
_ϕ_ | =  | porosity, fraction   
_γ_ | =  | specific gravity (air = 1.0 for gas)   
_μ_ | =  | viscosity, cp   
_ψ_ | =  | generic potential   
Δ _ψ_ | =  | generic-potential difference   
  
## References

  1. [↑](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r1_1-0) Al-Hussainy, R., Jr., H.J.R., and Crawford, P.B. 1966. The Flow of Real Gases Through Porous Media. J Pet Technol 18 (5): 624-636. <http://dx.doi.org/10.2118/1243-A-PA>
  2. ↑ [2.0](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r2_2-0) [2.1](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r2_2-1) [2.2](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r2_2-2) Earlougher, R.C. Jr.: Advances in Well Test Analysis, Monograph Series, SPE, Dallas (1977) 5.
  3. ↑ [3.0](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r3_3-0) [3.1](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r3_3-1) [3.2](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r3_3-2) [3.3](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r3_3-3) [3.4](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r3_3-4) Beggs, H.D.: Gas Production Operations, OGCI Publications, Tulsa (1984).
  4. [↑](https://onepetro.org/spe/general-information/1653/Gas-well-performance#cite_ref-r4_4-0) Rawlins, E.L. and Schellhardt, M.A.: Backpressure Data on Natural Gas Wells and Their Application to Production Practices, U.S. Bureau of Mines Monograph 7 (1936).


Copyright 2012-2025, Society of Petroleum Engineers

Advertisement

#### Explore

  * [Journals](https://onepetro.org/journals)
  * [Conferences](https://onepetro.org/conferences)
  * [eBooks](https://onepetro.org/books)
  * [Publishers](https://onepetro.org/pages/partners)


#### Connect

  * [About Us](https://onepetro.org/pages/about-us)
  * [Contact Us](https://onepetro.org/pages/contact-us)
  * [Content Alerts](https://onepetro.org/my-account/alerts)
  * [SPE Member Pricing](https://onepetro.org/pages/spemember)


#### Resources

  * [Terms of Use](https://onepetro.org/pages/terms)
  * [Privacy](https://www.spe.org/en/about/privacypolicy)
  * [Help](https://onepetro.org/pages/help)
  * [KBART](https://onepetro.org/pages/kbart)


#### Engage

  * [Subscribe](https://onepetro.org/pages/subscribe)
  * [Advertise](https://www.spe.org/en/sales/)


[ ](https://onepetro.org/)

  * [Facebook](https://www.facebook.com/spemembers)
  * [Twitter](https://twitter.com/SPEtweets)
  * [LinkedIn](https://www.linkedin.com/company/23356/)
  * [YouTube ](https://www.youtube.com/2012SPE)
  * [Instagram](https://instagram.com/spengineers/)


[_Close Modal_](javascript:;)

[ __ Close Modal ](javascript:;)

Sign In or Register to Continue

[Sign In](https://onepetro.org/sign-in?returnUrl=%2fspe%2fgeneral-information%2f1653%2fGas-well-performance) or [Register](https://onepetro.org/my-account/register?siteId=1000201&returnUrl=%2fspe%2fgeneral-information%2f1653%2fGas-well-performance)

[_Close Modal_](javascript:;)

[_Close Modal_](javascript:;)

## Sharing Unavailable

Sharing content requires targeting cookies to be enabled. Please update your cookie preferences to use this feature.

Update Cookie Preferences Cancel

This site uses cookies. By continuing to use our website, you are agreeing to [our privacy policy.](https://www.spe.org/en/about/privacypolicy/)

[Accept](javascript:;)
