<!-- Source: https://petrowiki.org/Deliverability_testing_of_gas_wells -->
<!-- Converted: html2text (manually downloaded) -->

Advertisement

[ _Open Menu_ ](javascript:;)

__Search Dropdown Menu

[Advanced Search](https://onepetro.org/advanced-search)

[ Cart __ ](https://onepetro.org/store/cart)

_User Tools Dropdown_

[ Cart __ ](https://onepetro.org/store/cart)

[Register](https://onepetro.org/my-account/register?siteId=1000201&returnUrl=%2fspe%2fgeneral-information%2f1418%2fDeliverability-testing-of-gas-wells)

Sign In _Open Menu_

[ ](https://onepetro.org/SPE)

[_Toggle Menu_ Menu](javascript:;)

Share

  * _Facebook Icon_
  * _X Icon_
  * _LinkedIn Icon_


This content has not been peer-reviewed and was originally developed through collaborative crowdsourcing on PetroWiki.

#  Deliverability testing of gas wells __

January 27, 2025

This article summarizes the fundamental gas-flow equations, both theoretical and empirical, used to analyze deliverability tests in terms of pseudopressure. The four most common types of gas-well deliverability tests are discussed in separate articles: flow-after-flow, single-point, isochronal, and modified isochronal tests. 

[](javascript:;)

[](mailto:\(\))

[](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells)

DOI:https://doi.org/10.2118/PW0198

Content License:FreeView

Publisher:Society of Petroleum Engineers (SPE)

Content Sub Type: [Petrowiki Content](https://onepetro.org/SPE/search-results?f_ArticleTypeDisplayName=Petrowiki+Content&fl_SiteID=1000201)

## Types and purposes of deliverability tests

Deliverability testing refers to the testing of a gas well to measure its production capabilities under specific conditions of reservoir and bottomhole flowing pressures (BHFPs). A common productivity indicator obtained from these tests is the absolute open flow (AOF) potential. The AOF is the maximum rate at which a well could flow against a theoretical atmospheric backpressure at the sandface. Although in practice the well cannot produce at this rate, regulatory agencies sometimes use the AOF to allocate allowable production among wells or to set maximum production rates for individual wells. 

Another application of deliverability testing is to generate a reservoir inflow performance relationship (IPR) or gas backpressure curve. The IPR curve describes the relationship between surface production rate and BHFP for a specific value of reservoir pressure (that is, either the original pressure or the current average value). The IPR curve can be used to evaluate gas-well current deliverability potential under a variety of surface conditions, such as production against a fixed backpressure. In addition, the IPR can be used to forecast future production at any stage in the reservoir’s life. 

Several deliverability testing methods have been developed for gas wells. Flow-after-flow tests are conducted by producing the well at a series of different stabilized flow rates and measuring the stabilized BHP. Each flow rate is established in succession without an intermediate shut-in period. A single-point test is conducted by flowing the well at a single rate until the BHFP is stabilized. This type of test was developed to overcome the limitation of long testing times required to reach stabilization at each rate in the flow-after-flow test. 

Isochronal and modified isochronal tests were developed to shorten tests times for wells that need long times to stabilize. An isochronal test consists of a series of single-point tests usually conducted by alternately producing at a slowly declining sandface rate without pressure stabilization and then shutting in and allowing the well to build to the average reservoir pressure before the next flow period. The modified isochronal test is conducted similarly, except the flow periods are of equal duration and the shut-in periods are of equal duration (but not necessarily the same as the flow periods). 

## Theory of deliverability test analysis

The theoretical equations developed by Houpeurt[[1]](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_note-r1-1) are exact solutions to the generalized radial-flow diffusivity equation, while the Rawlins and Schellhardt[[2]](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_note-r2-2) equation was developed empirically. All basic equations presented here assume radial flow in a homogeneous, isotropic reservoir and therefore may not be applicable to the analysis of deliverability tests from reservoirs with heterogeneities, such as natural fractures or layered pay zones. These equations should not be used to analyze tests from hydraulically fractured wells during the fracture-dominated linear or bilinear flow periods. Finally, these equations assume that wellbore-storage effects have ceased. Unfortunately, wellbore-storage distortion may affect the entire test period in short tests, especially those conducted in low-permeability reservoirs. 

### Theoretical deliverability equations

The early-time transient solution to the diffusivity equation for gases for constant-rate production from a well in a reservoir with closed outer boundaries, written in terms of pseudopressure, _p_ _p_ ,[[3]](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_note-r3-3) is 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0841_eq_001.png "RTENOTITLE")....................(1) 

where _p_ _s_ is the stabilized shut-in BHP measured before the deliverability test. In new reservoirs with little or no pressure depletion, this shut-in pressure equals the initial reservoir pressure, _p_ _s_ = _p_ _i_ , while in developed reservoirs, _p_ _s_ < _p_ _i_. 

The late-time or pseudosteady-state solution is 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0841_eq_002.png "RTENOTITLE")....................(2) 

where [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0781_inline_001.png "RTENOTITLE") is current drainage-area pressure. Gas wells cannot reach true pseudosteady state because _μ_ _g_(_p_)_c_ _t_(_p_) changes as [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0781_inline_001.png "RTENOTITLE") decreases. Note that, unlike [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0781_inline_001.png "RTENOTITLE"), which decreases during pseudosteady-state flow, _p_ _s_ is a constant. 

**Eqs. 1** and **2** are quadratic in terms of the gas flow rate, _q_. For convenience, Houpeurt[[1]](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_note-r1-1) wrote the transient flow equation as 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0841_eq_003.png "RTENOTITLE")....................(3) 

and the pseudosteady-state flow equation as 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0841_eq_004.png "RTENOTITLE")....................(4) 

where 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0841_eq_005.png "RTENOTITLE")....................(5) 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0841_eq_006.png "RTENOTITLE")....................(6) 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0841_eq_007.png "RTENOTITLE")....................(7) 

The coefficients of _q_ (_a_ _t_ for transient flow and a for pseudosteady-state flow) include the Darcy flow and skin effects and are measured in (psia2/cp)/(MMscf/D) when _q_ is in MMscf/D. The coefficient of _q_ 2 represents the inertial and turbulent flow effects and is measured in (psia2/cp)/(MMscf/D)2 when _q_ is in MMscf/D. 

The Houpeurt equations also can be written in terms of pressure squared and are derived directly from the solutions to the gas-diffusivity equation, assuming that _μ_ _g_ _z_ is constant over the pressure range considered. For transient flow, 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0841_eq_008.png "RTENOTITLE")....................(8) 

and for pseudosteady-state flow, 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0842_eq_001.png "RTENOTITLE")....................(9) 

The flow coefficients are 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0842_eq_002.png "RTENOTITLE")....................(10) 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0842_eq_003.png "RTENOTITLE")....................(11) 

and [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0842_eq_004.png "RTENOTITLE")....................(12) 

When the Houpeurt equation is presented in terms of pressure squared, the coefficients of _q_ are measured in psia2/(MMscf/D) when _q_ is in MMscf/D, while the coefficient of _q_ 2 is measured in units of psia2/(MMscf/D)2 when _q_ is in MMscf/D. For convenience, all equations and examples in this section are presented with _q_ measured in MMScf/D. 

The pressure-squared form of the equation should be used only for gas reservoirs at low pressures (less than 2,000 psia) and high temperatures. To eliminate doubt about which equations to choose, use of the pseudopressure equations, which are applicable at all pressures and temperatures, is recommended. Consequently, all the analysis procedures in this section are presented in terms of pseudopressure. 

An advantage of the pseudopressure form of the theoretical deliverability equation is that the flow coefficients are independent of the average reservoir pressure and, therefore, do not change as [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0781_inline_001.png "RTENOTITLE") decreases during a flow test conducted under pseudosteady-state flow unless _s_ , _k_ , or _A_ changes. Because the non-Darcy flow coefficient is a function of _μ_ _g_(_p_ _wf_ ), the coefficient b will change slightly if the BHFP is changed. In contrast, because of the pressure dependency of the gas properties on average reservoir pressure, the flow coefficients for the pressure-squared form of the deliverability equation must be recalculated for every new [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0781_inline_001.png "RTENOTITLE") value. When _s_ , _k_ , or _A_ changes with time, the only way to update the deliverability curve is to retest the well. 

### Empirical deliverability equations

In 1935, Rawlins and Schellhardt[[2]](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_note-r2-2) presented an empirical relationship that is used frequently in deliverability test analysis. The original form of their relation, given by **Eq. 13** in terms of pressure squared, is applicable only at low pressures: 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0842_eq_005.png "RTENOTITLE")....................(13) 

In terms of pseudopressure, **Eq. 13** becomes 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0842_eq_006.png "RTENOTITLE")....................(14) 

which is applicable over all pressure ranges. In **Eqs. 13** and **14** , _C_ is the stabilized performance coefficient and _n_ is the inverse slope of the line on a log-log plot of the change in pressure squared or pseudopressure vs. gas flow rate. Depending on the flowing conditions, the theoretical value of _n_ ranges from 0.5, indicating turbulent flow throughout a well’s drainage area, to 1.0, indicating laminar flow behavior modeled by Darcy’s law. The value of _C_ changes depending on the units of flow rate and whether **Eq. 13** or **14** is used. All equations and examples in this section are presented with q measured in MMscf/D. 

Houpeurt proved that neither **Eq. 13** nor **Eq. 14** can be derived from the generalized diffusivity equation for radial flow of real gas through porous media. Although the Rawlins and Shellhardt equation is not theoretically rigorous, it is still widely used in deliverability analysis and has worked well over the years, especially when the test rates approach the AOF potential of the well and the extrapolation from test rates to AOF is minimal. 

## Stabilization time

Unlike pressure-transient tests, the analysis techniques for conventional flow-after-flow and single-point tests require data obtained under stabilized flowing conditions. Although isochronal and modified isochronal tests were developed to circumvent the requirement of stabilized flow, they may still require a single, stabilized flow period at the end of the test. Consequently, there is a need to understand the meaning of stabilization time and have a method to estimate its value. 

Stabilization time is defined as the time when the flowing pressure is no longer changing or is no longer changing significantly. Physically, stabilized flow can be interpreted as the time when the pressure transient is affected by the no-flow boundaries, either natural reservoir boundaries or an artificial boundaries created by active wells surrounding the tested well. Consider a graph of pressure as a function of radius for constant-rate flow at various times since the beginning of flow. As **Fig. 1** shows, the pressure in the wellbore continues to decrease as flow time increases. Simultaneously, the area from which fluid is drained increases, and the pressure transient moves farther out into the reservoir. 

  * [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0722_image_0001.png "Fig. 1 – Pressure distributions at increasing times.")

**Fig. 1 – Pressure distributions at increasing times.**


The radius of investigation, the point in the formation beyond which the pressure drawdown is negligible, is a measure of how far a transient has moved into a formation following any rate change in a well. The approximate position of the radius of investigation at any time for a gas well is estimated by **Eq. 15**[[4]](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_note-r4-4): 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0843_eq_001.png "RTENOTITLE")....................(15) 

Stabilized flowing conditions occur when the calculated radius of investigation equals or exceeds the distance to the drainage boundaries of the well (i.e., _r_ _i_ ≥ _r_ _e_). Substituting r e and rearranging **Eq. 15** , yields an equation for estimating the stabilization time, _t_ _s_ , for a gas well centered in a circular drainage area: 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0843_eq_002.png "RTENOTITLE")....................(16) 

As long as the radius of investigation is less than the distance to the no-flow boundary, stabilization has not been attained and the pressure behavior is transient. To illustrate the importance of stabilization times in deliverability testing, stabilization times were calculated as a function of permeability and drainage area for a well producing a gas with a specific gravity of 0.6 from a formation at 210°F and an average pressure of 3,500 psia [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0843_inline_001.png "RTENOTITLE"), with a porosity of 10%. Table 1 shows that, for wells completed in low-permeability reservoirs, several days—or even years—are required to reach stabilized flow, while wells completed in high-permeability reservoirs stabilize in a short time. 

  * [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0844_image_0001.png "Table 1")

**Table 1**


A more general equation for calculating stabilization time is 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0844_eq_001.png "RTENOTITLE")....................(17) 

where _t_ _DA_ is dimensionless time for the beginning of pseudosteady-state flow. Values for _t_ _DA_ are given in **Table 2** for various reservoir shapes and well locations. [[5]](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_note-r5-5) The time required for the pseudosteady-state equation to be exact is found from the entry in the column "Exact for _t_ _DA_ >." 

  * [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0889_image_0001.png "Table 2")

**Table 2**

  * [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0890_image_0001.png "Table 2")

**Table 2**

  * [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0891_image_0001.png "Table 2")

**Table 2**


The Rawlins-Schellhardt and Houpeurt deliverability equations assume radial flow. If pseudoradial flow has been achieved, however, these analysis techniques can be used for hydraulically fractured wells. The time to reach the pseudoradial flow regime, _t_ prf, occurs[[6]](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_note-r6-6) at [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0844_inline_001.png "RTENOTITLE") and is estimated with 

[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0844_eq_002.png "RTENOTITLE")....................(18) 

To illustrate the importance of achieving pseudoradial flow during a deliverability test, values of tprf were calculated for a hydraulically fractured well completed in a reservoir with _ϕ_ = 0.15, [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0844_inline_002.png "RTENOTITLE") = 0.03 cp, and [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0789_inline_002.png "RTENOTITLE") = 1 × 10−4 psia−1 and with the range of permeabilities and hydraulic fracture half-lengths in **Table 3**. The results illustrate that a well with a long fracture in a low-permeability formation will take far too long to stabilize for conventional deliverability testing. 

  * [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0844_image_0002.png "Table 3")

**Table 3**


## Nomenclature

_a_ | =  | [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0879_inline_001.png "RTENOTITLE"), stabilized deliverability coefficient, psia2-cp/MMscf-D   
---|---|---  
_a_ _f_ | =  | [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0879_inline_002.png "RTENOTITLE"), depth of investigation along major axis in fractured well, ft   
_a_ _t_ | =  | [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0879_inline_002.png "RTENOTITLE"), transient deliverability coefficient, psia2-cp/MMscf-D   
_A_ | =  | drainage area, sq ft   
_A_ | =  | _πa_ _f_ _b_ _f_ , area of investigation in fractured well, ft2  
_b_ | =  | [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0880_inline_001.png "RTENOTITLE") (gas flow equation)   
_b_ _f_ | =  | [](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0880_inline_002.png "RTENOTITLE"), depth of investigation of along minor axis in fractured well, ft   
[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0789_inline_002.png "RTENOTITLE") | =  | total compressibility evaluated at average drainage area pressure, psi–1  
_D_ | =  | non-Darcy flow constant, D/Mscf   
_h_ | =  | net formation thickness, ft   
_k_ _g_ | =  | permeability to gas, md   
_L_ _f_ | =  | fracture half length, ft   
_n_ | =  | inverse slope of the line on a log-log plot of the change in pressure squared or pseudopressure vs. gas flow rate   
_p_ | =  | pressure, psi   
[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0781_inline_001.png "RTENOTITLE") | =  | volumetric average or static drainage-area pressure, psi   
_p_ _p_ | =  | pseudopressure, psia2/cp   
_p_ _wf_ | =  | flowing BHP, psi   
_q_ | =  | flow rate at surface, STB/D   
_t_ prf | =  | time required to reach the pseudoradial flow regime, hours   
_t_ _s_ | =  | time required for stabilization, hours   
_T_ | =  | reservoir temperature, °R   
Δ _p_ | =  | pressure change since start of transient test, psi   
[](https://petrowiki.org/Deliverability testing of gas wells _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol5_page_0844_inline_002.png "RTENOTITLE") | =  | gas viscosity evaluated at average pressure, cp   
_ϕ_ | =  | porosity, dimensionless   
  
## References

  1. ↑ [1.0](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_ref-r1_1-0) [1.1](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_ref-r1_1-1) Houpeurt, A. 1959. On the Flow of Gases in Porous Media. Revue de L’lnstitut Francais du Petrole 14 (11): 1468.
  2. ↑ [2.0](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_ref-r2_2-0) [2.1](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_ref-r2_2-1) Rawlins, E.L. and Schellhardt, M.A. 1935. Backpressure Data on Natural Gas Wells and Their Application to Production Practices, Vol. 7. Monograph Series, USBM.
  3. [↑](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_ref-r3_3-0) Al-Hussainy, R., Jr., H.J.R., and Crawford, P.B. 1966. The Flow of Real Gases Through Porous Media. J Pet Technol 18 (5): 624-636. <http://dx.doi.org/10.2118/1243-A-PA>.
  4. [↑](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_ref-r4_4-0) Lee, W.J. 1977. Well Testing, Vol. 1. Richardson, Texas: Textbook Series, SPE.
  5. [↑](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_ref-r5_5-0) Earlougher, R.C. Jr. 1977. Advances in Well Test Analysis, Vol. 5. Richardson, Texas: Monograph Series, SPE.
  6. [↑](https://onepetro.org/spe/general-information/1418/Deliverability-testing-of-gas-wells#cite_ref-r6_6-0) Lee, W.J. 1989. Postfracture Formation Evaluation. In Recent Advances in Hydraulic Fracturing, J.L. Gidley, S.A. Holditch, D.E. Nierode, and R.W. Veatch Jr. eds., Vol. 12. Richardson, Texas: Monograph Series, SPE.


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

[Sign In](https://onepetro.org/sign-in?returnUrl=%2fspe%2fgeneral-information%2f1418%2fDeliverability-testing-of-gas-wells) or [Register](https://onepetro.org/my-account/register?siteId=1000201&returnUrl=%2fspe%2fgeneral-information%2f1418%2fDeliverability-testing-of-gas-wells)

[_Close Modal_](javascript:;)

[_Close Modal_](javascript:;)

## Sharing Unavailable

Sharing content requires targeting cookies to be enabled. Please update your cookie preferences to use this feature.

Update Cookie Preferences Cancel

This site uses cookies. By continuing to use our website, you are agreeing to [our privacy policy.](https://www.spe.org/en/about/privacypolicy/)

[Accept](javascript:;)
