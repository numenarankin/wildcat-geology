<!-- Source: petrowiki-peh-inflow-outflow-performance -->
<!-- Converted: html2text + recovered MathJax alt-text equations -->

Advertisement

[ _Open Menu_ ](javascript:;)

__Search Dropdown Menu

[Advanced Search](https://onepetro.org/advanced-search)

[ Cart __ ](https://onepetro.org/store/cart)

_User Tools Dropdown_

[ Cart __ ](https://onepetro.org/store/cart)

[Register](https://onepetro.org/my-account/register?siteId=1000201&returnUrl=%2fspe%2fgeneral-information%2f1739%2fInflow-and-outflow-performance)

Sign In _Open Menu_

[ ](https://onepetro.org/SPE)

[_Toggle Menu_ Menu](javascript:;)

Share

  * _Facebook Icon_
  * _X Icon_
  * _LinkedIn Icon_


This content has not been peer-reviewed and was originally developed through collaborative crowdsourcing on PetroWiki.

#  Inflow and outflow performance __

February 5, 2025

[](javascript:;)

[](mailto:\(\))

[](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance)

DOI:https://doi.org/10.2118/PW0521

Content License:FreeView

Publisher:Society of Petroleum Engineers (SPE)

Content Sub Type: [Petrowiki Content](https://onepetro.org/SPE/search-results?f_ArticleTypeDisplayName=Petrowiki+Content&fl_SiteID=1000201)

## Production system

Knowing how fluid moves through the production system makes it easier to estimate well performance and get the most out of the well and reservoir productivity. The production system transfers reservoir fluids from the subsurface reservoir to the surface, processes and treats them, and then prepares them for storage and sale. Single-well production is shown in Fig. 1.1. The production system is consisting of the reservoir, the wellbore, the tubular goods, the surface wellhead, the flowlines, the processing equipment, and the artificial lift equipment.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_002_image_0001.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_002_image_0001.png "Enlarge")

Fig 1.1 Production System and associated pressure losses.

The reservoir supplies manufacturing fluids. It stores reservoir fluids and transports them to the wellbore through porous, permeable media. It provides the production system with primary energy. The wellbore accesses the reservoir. The wellbore is cemented and cased. Tubing and packers are housed in the cased wellbore. Even though fluids can flow through the space between the tubing and the casing, the tubing is the main way fluids move from the reservoir to the surface.

Wellheads, flowlines, and processing equipment control and process reservoir fluids at the surface for sale. Surface mechanical equipment includes wellhead equipment, chokes, manifolds, flowlines, separators, treatment equipment, metering devices, and storage vessels.

Many reservoirs need more energy to produce fluids at economical rates throughout their lifetime. When this happens, artificial lift equipment boosts production by contributing energy. This system component has surface and subsurface elements. Subsurface pumps supply this energy directly to the fluid, surface compression equipment can lower wellhead pressure, or gas can be injected into the production string to lessen the fluid gradient.

Analyzing the complete production system and comprehending its components improves well productivity. The production system's pressure drops as fluid flows from the reservoir. (as Fig. 1.1 shows). The stock tank's transfer line, which is close to atmospheric pressure, comes next to the average reservoir pressure. As reservoir fluids reach the surface, pressure drops significantly. Petroleum engineers must optimize pressure reduction. Both pressure change and output rate depend on each other. Predicting oil and gas well performance requires understanding pressure-production rate relationships.

A systematic approach is required to design a well completion and predict the production rate properly. It is necessary to integrate the production system components. Systems analysis lets petroleum engineers examine production systems and plan well completions. This chapter talks about how well reservoir pressure-rate behavior affects inflow performance and how outflow performance affects reservoir fluid flow through the pipe system.

## Reservoir inflow performance

### Single-phase analytical solutions

The equations for radial diffusivity offer solutions under various initial and boundary conditions to depict the behavior of pressure with respect to flow in a single-phase system. Of particular concern to petroleum engineers is the solution where the flow reaches a constant rate, known as the constant terminal-rate solution. In this scenario, the initial condition involves an equilibrium reservoir pressure at a specified time while the well maintains a steady production rate. The most prevalent, though not exclusive, conditions for seeking solutions pertain to steady-state and semisteady-state flow, where the well operates in a manner where the outer boundary pressure remains consistent. This suggests an open outer boundary where fluid entry precisely balances fluid withdrawal. This condition is relevant when pressure is upheld due to active natural water influx or during the active injection of fluid into the reservoir. The steady-state solution for single-phase liquid flow, expressed in terms of the average reservoir pressure, is applicable in below :

  
${\displaystyle q={\frac {kh{\bigl (}Pr-Pwf{\bigr )}}{141.2B\mu {\Bigl (}\ln {\tfrac {r_{e}}{r_{w}}}-{\tfrac {1}{2}}+S{\Bigr )}}}}$ 

### Gas well performance

In the past, when estimating the performance of gas wells, a method called "open flow" was used. This involved opening the well to the atmosphere and measuring the flow rate. However, this practice had several drawbacks. It resulted in wastage of gas, posed risks to personnel and equipment, and could potentially harm the reservoir. Furthermore, the information obtained from this method was limited when it came to estimating the well's productive capacity under different flow conditions. Nevertheless, this approach did introduce the concept of absolute open flow (AOF), which has become a common indicator of well productivity. AOF refers to the maximum rate at which a well could flow under ideal conditions, with a theoretical atmospheric backpressure at the reservoir.

To assess the productivity of a gas well, deliverability testing is performed. These tests provide valuable insights into the behavior of the well's reservoir, including rate-pressure characteristics, which are then used to generate either an inflow performance curve or a gas-backpressure curve. Currently, there are two main approaches utilized to analyze deliverability test data. One is an empirical relationship introduced by Rawlins and Schellhardt[[1]](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_note-:1-1) in 1935. The other is a theoretical deliverability relationship developed by Houpeurt[[2]](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_note-2), derived from the generalized radial diffusivity equation and accounting for non-Darcy flow effects.

Rawlins and Schellhardt[[1]](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_note-:1-1) developed an empirical backpressure method for testing gas wells, base on their analysis of over 500 well tests. They observed that by plotting the difference between the squared average reservoir pressure and the flowing bottomhole pressures against the corresponding flow rates on logarithmic scales, a linear relationship emerged. This led them to propose the backpressure equation:

${\textstyle q_{g}=C({\bar {p}}_{R}^{2}-p_{wf}^{2})^{n},}$  |  |  |  |   
---|---|---  
  
(1.1)  
  
where C is the flow coefficient and n is the deliverability exponent. The deliverability exponent is calculated as the reciprocal of the slope of the linear curve obtained from plotting the difference between squared average reservoir pressure and flowing bottomhole pressures against corresponding flow rates on logarithmic scales. Once the deliverability exponent (n) is determined, the flow coefficient (C) can be obtained by substituting pressure and rate data, taken directly from the straight-line plot, into Eq. 1.1 and solving the resulting relationship.

As discussed previously, the gas well performance solutions using pressure-squared are only valid when reservoir pressures are low. Therefore, Rawlins and Schellhardt's deliverability equation can be modified to utilize pseudopressure, represented by the equation.

${\displaystyle q_{g}=C[p_{p}({\bar {p}}_{R})-p_{p}(p_{wf})]^{n},}$  |  |  |  |   
---|---|---  
  
(1.2)  
  
The values of the flow coefficient (C) and deliverability exponent (n) for the modified equation are determined in the same way as for Eq. 1.2. The deliverability exponent (n) typically falls within the range of 0.5 to 1.0, depending on the flow characteristics. Flow behavior described by Darcy's equation will have a flow exponent of 1.0, while flow exhibiting non-Darcy flow effects will have a flow exponent ranging from 0.5 to 1.0. Although the Rawlins and Schellhardt deliverability equation lacks rigorous theoretical foundation, it remains widely utilized in deliverability analysis and has produced reasonable outcomes for gas wells with high permeability throughout the years.

Eqs. 1.1 and 1.2 can be reformulated to simplify the development of the inflow performance curve. In terms of pressure-squared, the relationship is

${\displaystyle {\frac {q_{g}}{q_{g,max}}}=\left[1-\left({\frac {p_{wf}}{{\bar {p}}_{R}}}\right)^{2}\right]^{n},}$  |  |  |  |   
---|---|---  
  
(1.3)  
  
and in terms of pseudopressure is

${\displaystyle {\frac {q_{g}}{q_{g,max}}}=\left[1-{\frac {p_{p}({p_{wf}})}{p_{p}({\bar {p}}_{R})}}\right]^{n},}$  |  |  |  |   
---|---|---  
  
(1.4)  
  
After determining the deliverability exponent from a multirate test and estimating the absolute open flow (AOF), Eqs. 1.3 and 1.4 can be easily used to estimate the flow rate at a specific flowing bottomhole pressure.

Houpeurt developed a theoretical deliverability relationship that incorporates a Forchheimer[[3]](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_note-3) velocity term to accommodate non-Darcy flow effects observed in high-velocity gas production. The resulting relationship can be expressed using either pressure-squared or pseudopressure.

${\displaystyle q_{g}={\frac {kh({\bar {p}}_{R}^{2}-p_{wf}^{2})}{1422\mu {\mathsf {z}}T(\ln {\frac {r_{e}}{r_{w}}}-{\frac {3}{4}}+s+Dq_{g})}},}$  |  |  |  |   
---|---|---  
  
(1.5)  
  
or

${\displaystyle q_{g}={\frac {kh(p_{p}({\bar {p}}_{R})-p_{p}(p_{wf}))}{1422\mu {\mathsf {z}}T(\ln {\frac {r_{e}}{r_{w}}}-{\frac {3}{4}}+s+Dq_{g})}},}$  |  |  |  |   
---|---|---  
  
(1.6)  
  
Eqs. 1.5 and 1.6 represent quadratic equations in terms of the flow rate, and for convenience of use, the solutions can be expressed as shown in Eqs. 1.7 and 1.8.

${\displaystyle {\bar {p}}_{R}^{2}-p_{wf}^{2}=aq_{g}+bq_{g}^{2},}$  |  |  |  |   
---|---|---  
  
(1.7)  
  
${\displaystyle p_{p}({\bar {p}}_{R})-p_{p}(p_{wf})=aq_{g}+bq_{g}^{2},}$  |  |  |  |   
---|---|---  
  
(1.8)  
  
Jones, Blount, and Glaze[[4]](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_note-4) proposed a modification to Houpeurt's relationship, presenting it in the form of Eqs. 1.9 and 1.10. This modification enables the analysis of well-test data to predict deliverability.

${\displaystyle {\frac {{\bar {p}}_{R}^{2}-p_{wf}^{2}}{q_{g}}}=a+bq_{g},}$  |  |  |  |   
---|---|---  
  
(1.9)  
  
${\displaystyle {\frac {p_{p}({\bar {p}}_{R})-p_{p}(p_{wf})}{q_{g}}}=a+bq_{g},}$  |  |  |  |   
---|---|---  
  
(1.10)  
  
When plotting the difference in pressures squared divided by the flow rate or the difference in pseudopressure divided by the flow rate against the flow rate, a linear relationship can be observed on a coordinate graph. The intercept of the plot represents the laminar flow coefficient ( ${\textstyle a}$ ), while the slope of the curve provides the turbulence coefficient ( ${\displaystyle b}$ ). Once these two coefficients are determined, deliverability can be estimated using the following relationships, expressed in terms of pressure-squared or pseudopressure.

${\displaystyle q_{g}={\frac {-a+{\sqrt {a^{2}+4b({\bar {p}}_{R}^{2}-p_{wf}^{2})}}}{2b}},}$  |  |  |  |   
---|---|---  
  
(1.11)  
  
and

${\displaystyle q_{g}={\frac {-a+{\sqrt {a^{2}+4b(p_{p}({\bar {p}}_{R})-p_{p}(p_{wf}))}}}{2b}},}$  |  |  |  |   
---|---|---  
  
(1.12)  
  
Once the coefficients of the deliverability equations have been obtained, these relationships can be used to estimate production rates at various bottomhole flowing pressures. This determination of the rate versus pressure is commonly known as the reservoir inflow performance, which measures the reservoir's capacity to produce gas to the wellbore. The inflow performance curve is a graphical representation of the relationship between bottomhole pressure and production rate for a specific well, derived from the gas well deliverability equations. Fig. 1.2 illustrates a typical gas well inflow performance curve. This curve enables the straightforward estimation of production rates for different flowing bottomhole pressures.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/typical_gas_well_inflow_performance_curve.jpg)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/typical_gas_well_inflow_performance_curve.jpg "Enlarge")

Fig 1.2 Typical gas well inflow performance curve

#### Deliverability Test Methods.

Various deliverability test methods have been developed to gather data for use with the fundamental deliverability models. These methods can be categorized into three main groups: tests using all stabilized data, tests combining stabilized and transient data, and tests relying solely on transient data. The flow-after-flow test is a basic deliverability test method that utilizes all stabilized data. It involves conducting a series of flow rates, often referred to as a four-point test, as mandated by regulatory bodies. During this test, the well is produced at different stabilized flow rates, and the corresponding stabilized flowing bottomhole pressures are recorded. Additionally, a stabilized shut-in bottomhole pressure is necessary for analysis. However, a drawback of this method is the time it takes to obtain stabilized data, particularly for low-permeability gas reservoirs.

Other deliverability test methods, such as the isochronal and modified isochronal tests, combine transient and stabilized data. These tests offer a more comprehensive dataset for analysis. An alternative approach is the multiple modified isochronal test, which relies entirely on transient data, eliminating the need for stabilized flow or pressure data. This test can be advantageous in specific situations. The choice of the most suitable deliverability test method depends on the characteristics of the reservoir and the desired scope of data collection.

Example 1.1

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/flow_after_flow_test_data.jpg)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/flow_after_flow_test_data.jpg "Enlarge")

Table 1.1 Flow after flow test data

Table 1.1 presents sample data from a flow-after-flow test, which is analyzed using the Rawlins and Schellhardt as well as the Houpeurt deliverability equations. The conventional Rawlins and Schellhardt analysis involves plotting the difference in pressures squared against the flow rate on logarithmic graph paper and fitting a straight line through the data points. The data should exhibit a linear relationship, which represents the deliverability curve. The slope of this line is used to determine the deliverability exponent (n), which is the reciprocal of the slope. Once the deliverability exponent is determined, the flow coefficient (C) can be calculated using Equation 1.1, utilizing a point taken from the straight-line plot. The same methodology applies when using pseudopressures to analyze the data, except that the differences in pseudopressures are plotted against the flow rate, and Equation 1.2 is used to determine C.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/rawlins_and_schellhardt_analysis_of_flow_after_flow_test_data.jpg)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/rawlins_and_schellhardt_analysis_of_flow_after_flow_test_data.jpg "Enlarge")

Table 1.2 Rawlins and Schellhardt analysis of flow after flow test data.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/rawlins_and_schellhardt_analysis_of_flow-after-flow_test_data_with_the_pressure-squared_approach..jpg)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/rawlins_and_schellhardt_analysis_of_flow-after-flow_test_data_with_the_pressure-squared_approach..jpg "Enlarge")

Fig 1.3 Rawlins and Schellhardt analysis of flow-after-flow test data with the pressure-squared approach.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_002_image_0001.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_002_image_0001.png "Enlarge")

Fig 1.4 Rawlins and Schellhardt analysis of flow-after-flow test data with pseudopressure approach.

Table 1.2 provides the dataset that will be used for the Rawlins and Schellhardt analysis. The corresponding logarithmic plots for the pressure-squared analysis and the pseudopressure analysis can be observed in Figures 1.3 and 1.4, respectively.

To analyze the pressure-squared data, a straight line is drawn through the four data points, resulting in a slope of 1.54. The deliverability exponent, n, is determined as the reciprocal of the slope, which gives a value of 0.651. To calculate the flow coefficient, C, a point from the straight line is selected. In this case, the third test point lies on the line, and by using Equation 1.13, a flow coefficient of 0.2874 Mscf/D/psia2n is obtained.

${\displaystyle C={\frac {q_{g}}{({\bar {p}}_{R}^{2}-p_{wf}^{2})^{n}}}={\frac {3,832}{(2,169,200)^{0.651}}}=0.2878}$  |  |  |  |   
---|---|---  
  
(1.13)  
  
After determining the values of n and C, the deliverability equation can be formulated and utilized to calculate the AOF as well as the production rate for any desired flowing bottomhole pressure. Equation 1.14 represents the deliverability equation specific to this example well.

${\displaystyle q_{g}=0.2878({\bar {p}}_{R}^{2}-p_{wf}^{2})^{0.651}}$  |  |  |  |   
---|---|---  
  
(1.14)  
  
The AOF is calculated by setting the flowing bottomhole pressure equal to the atmospheric pressure, considering the average reservoir pressure of 3,360 psia. In this case, assuming the atmospheric pressure is 14.65 psia, the AOF is determined to be 11,200 Mscf/D.

When analyzing the data using pseudopressures, a similar method is employed. By referring to Figure 1.4, the slope of the straight line through the data points is 1.57, resulting in an n value of 0.637. Using the third test point, Equation 1.15 provides the flow coefficient, C, as 0.0269 Mscf/D/(psia2/cp)n.

${\displaystyle C={\frac {q_{g}}{[p_{p}({\bar {p}}_{R})-p_{p}(p_{wf})]^{n}}}={\frac {3,832}{(123,050,000)^{0.637}}}=0.0269}$  |  |  |  |   
---|---|---  
  
(1.15)  
  
The resulting deliverability equation is

${\displaystyle q_{g}=0.0269(p_{p}({\bar {p}}_{R})-p_{p}(p_{wf}))^{0.637}}$  |  |  |  |   
---|---|---  
  
(1.16)  
  
Using the appropriate pseudopressure values at the current reservoir pressure of 3,360 psia and atmospheric pressure of 14.65 psia, the AOF is calculated to be 12,200 Mscf/D.

The calculated AOF using the pressure-squared approach and the pseudopressure method differs noticeably. This difference arises because the pseudopressure term takes into account the impact of the pressure-dependent gas viscosity and gas deviation factor. As mentioned earlier, the pressure-squared approach is suitable only for low pressures, whereas the pseudopressure method is applicable across all pressure ranges. Additionally, it should be noted that the Rawlins and Schellhardt method lacks theoretical rigor, despite its widespread usage.

The test data can also be analyzed using the Houpeurt approach, utilizing both the pressure-squared and pseudopressure methods. Table 1.3 provides the data necessary for plotting in the Houpeurt analysis. Figure 1.5 presents the Houpeurt plot based on the pressure squared data, while Figure 1.6 displays the plot using pseudopressure data. By constructing a best-fit line through the data points in Figure 1.5, the slope and intercept of the line can be determined. The slope, represented as b, equals 0.0936 psia2/(Mscf/D)2, while the intercept, denoted as a, is found to be 200 psia2/Mscf/D. These deliverability coefficients can be used to establish a deliverability equation in the form of Equation 1.11, as shown in Equation 1.17.

${\displaystyle q_{g}={\frac {-200+{\sqrt {200^{2}+4(0.0936)({\bar {p}}_{R}^{2}-p_{wf}^{2})}}}{2(0.0936)}}}$  |  |  |  |   
---|---|---  
  
(1.17)  
  
The estimated AOF for the reservoir pressure of 3,360 psia is calculated to be 9,970 Mscf/D.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/houpeurt_analysis_of_flow_after_flow_test_data.jpg)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/houpeurt_analysis_of_flow_after_flow_test_data.jpg "Enlarge")

Table 1.3 Houpeurt analysis of flow after flow test data.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/houpeurt_analysis_of_flow-after-flow_test_data_with_pressure-squared_approach..jpg)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/houpeurt_analysis_of_flow-after-flow_test_data_with_pressure-squared_approach..jpg "Enlarge")

Fig 1.5 Houpeurt analysis of flow-after-flow test data with pressure-squared approach.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/houpeurt_analysis_of_flow-after-flow_test_data_with_the_pseudopressure_approach..jpg)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/houpeurt_analysis_of_flow-after-flow_test_data_with_the_pseudopressure_approach..jpg "Enlarge")

Fig 1.6 Houpeurt analysis of flow-after-flow test data with the pseudopressure approach.

The pseudopressure data shown in Figure 1.6 can be subjected to a similar analysis. By determining the intercept of the best-fit line constructed through the plot, it is determined to be 10,252 psia2/cp/Mscf/D, while the slope is calculated as 5.69 psia2/cp/(Mscf/D)2. These coefficients are used in formulating the deliverability equation as follows:

${\displaystyle q_{g}={\frac {-10,252+{\sqrt {10,252^{2}+4(5.69)(p_{p}({\bar {p}}_{R})-p_{p}(p_{wf}))}}}{2(5.69)}}}$  |  |  |  |   
---|---|---  
  
(1.18)  
  
Using this equation for the current reservoir pressure, the AOF is approximated to be 10,700 Mscf/D. Similar to the Rawlins and Schellhardt analysis, the AOFs obtained through the pressure-squared method and the pseudopressure approach differ due to the influence of the pressure dependence of the μz product.

#### Isochronal

Cullender introduced the isochronal test as a solution for dealing with slow-to-stabilize wells, eliminating the need for a series of stabilized flow rates as required in the flow-after-flow test. This test involves producing the well at various flow rates, each with equal durations, and separating them with shut-in periods to allow the bottomhole pressure to stabilize at the average reservoir pressure. Additionally, the test requires obtaining an extended stabilized flow point. The underlying principle of the test is that the investigation radius depends on the flow period rather than the flow rate. Therefore, equal flow periods result in the exploration of the same drainage radius, regardless of the actual flow rates.

To analyze the data obtained from an isochronal test, the flow data from the equal flow periods are plotted using the Rawlins and Schellhardt or Houpeurt methods. These plotted data points are utilized to determine the slope of the deliverability curve. The stabilized flow point is then utilized to estimate the flow coefficient, C, for the Rawlins and Schellhardt method or the intercept, a, for the Houpert method by extending the slope of the multi-rate data to the stabilized flow point.

Example 1.2

Table 1.4 provides information on isochronal test data for a specific well, where each flow period lasts for one hour. The analysis of this data is conducted using two approaches: the Rawlins and Schellhardt method with pressures, and the Houpeurt method with pseudopressures. The plotting data for both methods is presented in Table 1.5. Figure 1.7 illustrates the logarithmic representation of the pressure data for the Rawlins and Schellhardt analysis.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/isochronal_test_data.jpg)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/isochronal_test_data.jpg "Enlarge")

Table 1.4 Isochronal test data.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/plotting_data_for_ischronal_test.jpg)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/plotting_data_for_ischronal_test.jpg "Enlarge")

Table 1.5 Plotting data for ischronal test

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_014_image_0001.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_014_image_0001.png "Enlarge")

Fig 1.7 Rawlins and Schellhardt analysis of isochronal test data with the pressure-squared approach

Solution

By connecting the three transient points with a straight line, a slope of 1.076 can be obtained. The inverse of this slope determines the deliverability exponent, denoted as n, which in this particular case is calculated to be 0.9294. The line extending through the transient points is further extended to the stabilized flow point, allowing the depiction of the deliverability curve. The flow coefficient, represented as C, is determined based on the stabilized flow point.

${\displaystyle C={q_{g} \over {\bar {p}}_{R}^{2}-p_{wf}^{2}}={6,300 \over (672,804)^{0.9294}}=0.0242}$  |  |  |  |   
---|---|---  
  
(1.29)  
  
The flow coefficient, determined as 0.0242 Mscf/D/psia2n, along with the deliverability exponent, is utilized to define the Rawlins and Schellhardt deliverability equation for this particular well.

${\displaystyle q_{g}=0.0242({\bar {p}}_{R}^{2}-p_{wf}^{2})^{0.9294}}$  |  |  |  |   
---|---|---  
  
(1.30)  
  
This equation is then employed to calculate the Absolute Open Flow (AOF) of the well. In this case, with an atmospheric pressure of 14.65 psia, the AOF is estimated to be 27,100 Mscf/D. Additionally, a comparable analysis can be conducted using pseudopressures, employing the same methodology as described for squared pressures.

By employing the Houpeurt approach, the transient flow points are utilized to determine the slope of the best-fit straight line, which is constructed through the data points. This slope is then employed to calculate the intercept from the stabilized flow point. Figure 1.8 displays the plot of the pseudopressure data for the Houpeurt analysis. Based on this plot, the slope is determined to be 0.1184 psia2/cp/(Mscf/D)2. This slope is then used in Eq. 1.31 to calculate an intercept from the stabilized flow point, resulting in a value of 8,814 psia2/cp/Mscf/D.

${\displaystyle a={p_{p}({\bar {p}}_{R})-p_{p}(p) \over q_{g}}-bq_{g}={284,360,000-228,830,000 \over 6,300}-0.1184(6,300)=8,065}$  |  |  |  |   
---|---|---  
  
(1.31)  
  
The deliverability equation can be expressed in a similar format as Eq. 1.22, resulting in Eq. 1.32.

${\displaystyle q_{g}=-8065+{\sqrt {8065^{2}+4(0.1184)[p_{p}({\bar {p}}_{R})-p_{p}(p_{w}f)]}} \over 2(0.1184)}$  |  |  |  |   
---|---|---  
  
(1.32)  
  
This equation can be employed to estimate the Absolute Open Flow (AOF) of 25,600 Mscf/D for the well, or to estimate the production rate at any other flowing bottomhole pressure. It is important to note that the analysis of the flow-after-flow test data revealed that the Rawlins and Schellhardt and Houpeurt methods produce different estimates of deliverability.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_015_image_0001.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_015_image_0001.png "Enlarge")

Fig 1.8 Houpert analysis of isochronal test data with the pseudopressure approach.

#### Modified Isochronal Test

To address the challenge of obtaining stabilized shut-in pressures in low-permeability wells, Katz et al. proposed a modification to the isochronal test. This modification requires equal or longer shut-in periods compared to the flow periods. The modified isochronal test closely resembles the standard isochronal test, with the key difference being the duration of the shut-in periods.

In this modified method, the extended stabilized flow point and a stabilized shut-in bottomhole pressure are still required. However, it is important to note that the modified isochronal test is less accurate than the standard isochronal method. This is due to the fact that the shut-in pressure does not return to the average reservoir pressure.

During the analysis of the collected data, the measured bottomhole pressure just before the start of each flow period is used in Eqs. 1.11 and 1.12, or Eqs. 1.19 and 1.20. This replaces the use of the average reservoir pressure in these equations.

The analysis of the data in the modified isochronal test follows the same methodology as that used for analyzing the standard isochronal test data. In the Rawlins and Schellhardt approach, a best-fit straight line is constructed using the transient flow points. The inverse of the slope of this line provides the deliverability exponent, denoted as n. This deliverability exponent, along with the data from the stabilized flow point, is then utilized to estimate the flow coefficient, denoted as C, using either Eq. 1.11 or 1.12, depending on whether pressure or pseudopressure data is employed.

In the Houpeurt analysis, a best-fit straight line is constructed using the transient flow points to determine the slope, denoted as b. Once the slope is determined, it is utilized with the data from the stabilized flow point and the appropriate equation for either pressure or pseudopressure analysis (Eqs. 1.19 and 1.20) to calculate the intercept, denoted as a.

After determining the flow coefficients through either analysis method, the deliverability equation can be formulated and employed to estimate the Absolute Open Flow (AOF) and production rates for the well.

#### Transient Test Methods

The multiple modified isochronal test approach involves conducting transient tests without the need for stabilized flow or pressure data. However, this analysis method requires additional information such as estimates of drainage area, shape, reservoir properties, and fluid properties, which are not necessary for previous deliverability test methods. Consequently, the analysis techniques for multiple modified isochronal tests are more complex compared to flow-after-flow, isochronal, or single modified isochronal tests.

To estimate the deliverability of slow-in-stabilizing wells, a minimum of three modified isochronal tests are performed, and each test includes a minimum of three different flow rates. Analyzing the test data involves modifications to the Rawlins and Schellhardt analysis proposed by Hinchman, Kazemi, and Poettmann [12], as well as modifications to the Houpeurt pressure-squared technique suggested by Brar and Aziz [13], Poettmann [14], and Brar and Mattar [15]. These modifications have also been extended to the pseudopressure analysis technique by Poe [16]. For comprehensive information on estimating deliverability from transient test data, it is recommended to refer to the literature sources [12][13][14][15][16].

#### Future Performance Methods

The petroleum engineer's task involves forecasting or predicting the performance of a gas well as the reservoir pressure declines. Various methods can aid in making these future performance estimates, including directly applying the appropriate analytical solution to obtain rate vs. pressure estimates for different average reservoir pressures. However, this approach, using Eqs. 1.7 through 1.10, necessitates knowledge of rock and fluid properties specific to the well in question

Another technique, which also relies on understanding rock and fluid properties, involves estimating the flow coefficients, a and b, in Houpeurt's relationships (Eqs. 1.17 and 1.18). When using Houpeurt's method in terms of pressure-squared, the flow coefficients a and b are

${\displaystyle a={1422\mu zT(\ln {r_{e} \over r_{w}}-{3 \over 4}+s) \over kh}}$  |  |  |  |   
---|---|---  
  
(1.33)  
  
and

${\displaystyle b={1422\mu zT \over kh}D}$  |  |  |  |   
---|---|---  
  
(1.34)  
  
with the non-Darcy flow coefficient as below.

${\displaystyle D={2.715\times 10^{-15}\beta kMp_{sc} \over h\mu _{g}r_{w}T_{sc}}}$  |  |  |  |   
---|---|---  
  
(1.35)  
  
where the value of β (the turbulence factor) [17] can be estimated from

${\displaystyle \beta =1.88\times 10^{10}k^{-1.47}\phi ^{-0.53}}$  |  |  |  |   
---|---|---  
  
(1.36)  
  
When Houpeurt's relationship is expressed in terms of pseudopressure, the estimation of flow coefficients a and b is conducted using the following equation.

${\displaystyle a={1422T(\ln {r_{e} \over r_{w}}-{3 \over 4}+s) \over kh}}$  |  |  |  |   
---|---|---  
  
(1.37)  
  
and

${\displaystyle b={1422T \over kh}D}$  |  |  |  |   
---|---|---  
  
(1.38)  
  
To estimate the variables D and β, Eqs. 1.35 and 1.36 are used. Once the flow coefficients a and b are determined for new average reservoir pressures, Eqs. 1.21 and 1.22 can be employed to estimate rates for different pressures and generate the inflow performance curve.

In the field of gas well depletion performance, Russell et al. [18] conducted a study and proposed a technique that takes into account gas compressibility and viscosity to estimate gas well performance. Based on this study, Greene [19] presented a relationship to describe well performance.

${\displaystyle q={C_{1} \over \mu ({\bar {p}})z({\bar {p}})}({\bar {p}}_{R}^{2}-p_{wf}^{2})}$  |  |  |  |   
---|---|---  
  
(1.39)  
  
In the given equation, C_1 represents a constant that depends on factors such as permeability, reservoir thickness, and drainage area. This constant can be estimated from a single-point flow test by considering gas compressibility and viscosity. It is important to note that C_1 is distinct from the flow coefficient C in Eqs. 1.11 and 1.12. C_1 remains constant throughout the well's life, assuming no changes in permeability. Once C_1 is determined, future performance can be estimated using Eq. 1.39, with the gas compressibility and viscosity estimated at the average bottomhole pressure, as defined by

${\displaystyle {\bar {p}}={({\bar {p}}_{R}+p_{wf}) \over 2}}$  |  |  |  |   
---|---|---  
  
(1.40)  
  
A method that eliminates the need for rock and fluid properties assumes a constant deliverability exponent, denoted as n, throughout the well's lifespan. Although this assumption may not always hold true, it has been observed that the deliverability exponent tends to change gradually over time in many gas wells. Based on this assumption, future well performance can be forecasted using the following relationships, expressed in terms of pressure-squared and pseudopressure, respectively.

${\displaystyle q_{g,max,f}={q_{g,max,p}\left({{\bar {p}}_{R,f} \over {\bar {p}}_{R,p}}\right)^{2n}}}$  |  |  |  |   
---|---|---  
  
(1.41)  
  
${\displaystyle q_{g,max,f}=q_{g,max,p}\left[{{\bar {p}}_{p}({\bar {p}}_{R,f}) \over {\bar {p}}_{p}({\bar {p}}_{R,p})}\right]^{2n}}$  |  |  |  |   
---|---|---  
  
(1.42)  
  
After determining the new Absolute Open Flow (AOF) at the anticipated future reservoir pressure, it becomes possible to construct the inflow performance curve using a modified form of the deliverability equation, as illustrated in Eqs. 1.13 and 1.14.

### Oil Well Performance

It is frequently considered that the productivity index can be used to estimate an oil well’s performance. The straight-line productivity index was not applicable to multiphase flow, according to Evinger and Muskat, who also noted that there was a curved relationship between flow rate and pressure for multiphase flow. Other methods besides the productivity index must be applied to forecast oil well performance for reservoir pressures lower than the bubblepoint pressure when the reservoir fluid exists as vapor and liquid.

  
Inflow Performance. Numerous empirical relationships have been put forth to forecast oilwell performance in two-phase flow scenarios. A simple technique for forecasting oil performance was proposed by Vogel. His empirical inflow performance relationship (IPR) is provided by and is based on the outcomes of computer simulations[[5]](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_note-:0-5).

${\displaystyle {q_{o} \over q_{o,max}}=1.0-0.2{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}-0.8{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}^{2}}$  |  |  |  |   
---|---|---  
  
(1.43)  
  
Oil production rate, flowing bottomhole pressure, and average reservoir pressure estimation must all be obtained from a production test to apply this relationship. By applying this relationship, the maximum oil production rate and production rate at any flowing bottomhole pressures at the current average reservoir can be predicted[[5]](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_note-:0-5).

Fetkovich suggested an isochronal oil well testing to evaluate the well productivity. The equation is based on Rawlins and Schellhardt empirical gas-well deliverability equation.

${\displaystyle q_{o}=C({\bar {P_{R}^{2}}}-P_{wf}^{2})^{n}}$  |  |  |  |   
---|---|---  
  
(1.44)  
  
Flow coefficient (C) and flow exponent (n) variable is obtained from a log-log plot of pressure-squared difference vs. flow rate. A straight-line is expected to occur in the plot and is estimated through the plot slop’s inverse. By choosing a flow rate and pressure on the log-log plot, can be estimated. Fetkovich’s deliverability equation can be rearranged to obtain a developed IPR equation.

${\displaystyle {q_{o} \over q_{o,max}}={\Bigl [}1-{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}^{2}{\Bigr ]}^{n}}$  |  |  |  |   
---|---|---  
  
(1.45)  
  
Hereinafter, other multirate test methods were also put forth by Jones, Blount, and Glaze to encompass non-Darcy flow effects. Oil flow rate can be predicted by using the equation below.

${\displaystyle {{\bar {P_{R}}}-P_{wf} \over q_{o}}=a+bq_{o}}$  |  |  |  |   
---|---|---  
  
(1.46)  
  
a represents laminar flow coefficient and is the turbulence coefficient. Multiple rate test information should be obtained as in Fetkovich’s method. A straight line should be obtained by plotting the pressure difference to flow rate ratio vs flow rate on coordinate paper. From that plot, is the plot intercept while is the curve slope. After both coefficients have been identified, the flow rate can be obtained by using formula:

${\displaystyle q_{o}={-a+{\sqrt {a^{2}+4b({\bar {P_{R}}}-P_{wf})}} \over 2b}}$  |  |  |  |   
---|---|---  
  
(1.47)  
  
There are numerous alternative two-phase IPR methods in the literature. Klins and Majcher devised an IPR method that integrated the bubblepoint pressure, resulting in the simulation of 21 wells based on Vogel’s data and the generation of 1,344 IPR curves. They introduced the subsequent IPR by employing nonlinear regression analysis:

${\displaystyle q_{o}=1.0-0.295{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}-0.705{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}^{n}}$  |  |  |  |   
---|---|---  
  
(1.48)  
  
where n is polynomial exponent with equation of

${\displaystyle n={\Bigl (}0.28+0.72{P_{R} \over P_{b}}{\Bigr )}(1.235+0.001P_{b})}$  |  |  |  |   
---|---|---  
  
(1.49)  
  
Besides, Sukarno and Winogroho already devised an IPR by leveraging simulation outcomes, aiming to consider the fluctuation in flow efficiency resulting from rate-dependent skin as the flowing bottomhole pressure undergoes changes. The authors established the subsequent correlation through the utilization of nonlinear regression analysis.

${\displaystyle {q_{o,actual} \over q_{o,max,r=0}}=F_{E}{\Bigl [}1.0-0.1489{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}-0.4416{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}^{2}-0.4093{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}^{3}{\Bigr ]}}$  |  |  |  |   
---|---|---  
  
(1.50)  
  
in which

${\displaystyle F_{E}=a_{0}+a_{1}{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}+a_{2}{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}^{2}+a_{3}{\Bigl (}{P_{wf} \over P_{R}}{\Bigr )}^{3}}$  |  |  |  |   
---|---|---  
  
(1.51)  
  
and

${\displaystyle a_{R}=b_{0}+b_{1}s+b_{2}s^{2}+b_{3}s^{3}}$  |  |  |  |   
---|---|---  
  
(1.52)  
  
The variable of a and b are the fitting coefficients as can be seen in Table 1.6, while s is the skin factor.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/table_1.6._new.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/table_1.6._new.png "Enlarge")

Table 1.6 Constants for Sukarno and Wisnugroho IPR

Gallice & Wiggins has been comparing those two-phase IPR methods and shown that evert test does not have a single method that is universally appropriate by evaluate some field cases performance. Nevertheless, the multipoint approach developed by Fetkovich demonstrated a tendency to be the most dependable due to overall absolute difference and consistent performance predictions throughout the pressure drawdown range. The comparison of those IPR methods can be seen in Table 1.7.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/1.7._new.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/1.7._new.png "Enlarge")

Table 1.7 Summary of performance predictions for all methods and cases

The reservoir may exhibit both single-phase and two-phase flow phenomena when the average reservoir pressure exceeds the bubblepoint pressure of the reservoir oil, while the flowing bottomhole pressure remains below the bubblepoint pressure. Neely introduced a combined IPR that is exemplified by Brown by integrating Vogel’s two-phase flow IPR with the single-phase productivity index. The maximum oil production rate can be determined by the following equation.

${\displaystyle q_{o,max}=J{\Bigl (}{\bar {P_{R}}}-P_{b}+{P_{b} \over 1.8}{\Bigr )}}$  |  |  |  |   
---|---|---  
  
(1.53)  
  
Oil production rate at various flowing bottomhole pressures is listed below. The equation below can be applied when the flowing bottomhole pressures is greater than the bubblepoint pressure.

${\displaystyle q_{o}=J({\bar {P_{R}}}-P_{wf}),P_{wf}\geq P_{b}}$  |  |  |  |   
---|---|---  
  
(1.54)  
  
And the equation below can be applied when the bottomhole pressure is less than bubblepoint pressure.

${\displaystyle q_{o}=(q_{o,max}-q_{b}){\Bigl [}1.0-0.2{\Bigl (}{P_{wf} \over P_{b}}{\Bigr )}-0.8{\Bigl (}{P_{wf} \over P_{b}}{\Bigr )}^{2}{\Bigr ]}+q_{b},P_{wf}\leq P_{b}}$  |  |  |  |   
---|---|---  
  
(1.55)  
  
The flow rate at the bubblepoint pressure, used in Eq. 1.55, is calculated using Eq. 1.54, where the bottomhole pressure is equal to the bubblepoint pressure (Pb). The suitable value to employ in both equations relies on the flowing bottomhole pressure (Pwf) of the test point. Single-phase flow conditions occurs when the flowing bottomhole pressure surpasses the bubblepoint pressure, and can be determined by

${\displaystyle J={q_{o} \over {\bar {P_{R}}}-P_{wf}},{\bar {P_{R}}}\geq P_{wf}\geq P_{b}}$  |  |  |  |   
---|---|---  
  
(1.56)  
  
Then, if flowing bottomhole pressure is less than the bubblepoint pressure, J can be determined by

${\displaystyle J={q_{o} \over {\bar {P_{R}}}-P_{b}+{P_{b} \over 1.8}{\Bigl [}1.0-0.2{\Bigl (}{P_{wf} \over P_{b}}{\Bigr )}-0.8{\Bigl (}{P_{wf} \over P_{b}}{\Bigr )}^{2}{\Bigr ]}},{\bar {P_{R}}}\geq P_{b}\geq P_{wf}}$  |  |  |  |   
---|---|---  
  
(1.57)  
  
As a reminder, the composite IPR is solely relevant in cases where the average reservoir pressure exceeds the bubblepoint pressure.

Wiggins introduced an easy-to-use three-phase flow IPR, which bears resemblance to Vogel’s IPR in terms of its structure. This IPR was developed through a series of simulation studies and produces results like two three-phase flow models, while offering easier implementation. Both equations below provide the generalized three-phase IPRs for oil and water each.

${\displaystyle {q_{o} \over q_{o,max}}=1-0.52{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}-0.48{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}^{2}}$  |  |  |  |   
---|---|---  
  
(1.58)  
  
${\displaystyle {q_{w} \over q_{w,max}}=1-0.72{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}-0.28{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}^{2}}$  |  |  |  |   
---|---|---  
  
(1.59)  
  
* * *

Example 1.3

Data from a multipoint test on an oil well that was used to illustrate the two-phase IPR approaches are shown in Table 1.8. 1,734 psia serves as the typical reservoir pressure in this scenario.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/1.8..png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/1.8..png "Enlarge")

Table 1.8 Oilwell test data for Example 1.1*

Solution

To implement the IPR techniques, gather testing data comprising production rates, flowing bottomhole pressures, and an approximation of the average reservoir pressure. Vogel's IPR represents a relationship at a singular rate, and the highest recorded test rate is employed to illustrate this IPR. The information collected during the most significant pressure reduction can be applied with eq 1.55 to determine the peak oil production rate.

${\displaystyle q_{o,max}={q_{o} \over 1.0-0.2{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}-0.8{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}^{2}}={768 \over 1.0-0.2{\Bigl (}{1,335 \over 1,734}{\Bigr )}-0.8{\Bigl (}{1,335 \over 1,734}{\Bigr )}^{2}}=2,065STB/D}$  |  |  |  |   
---|---|---  
  
(1.60)  
  
The estimated peak oil production is 2,065 STB/D. This result is then employed to predict the production rate at different levels of flowing bottomhole pressures in order to construct a comprehensive inflow performance curve. Once more, eq 1.55 will be adjusted to compute the production rate for a flowing bottomhole pressure of 800 psia.

${\displaystyle q_{o}=q_{o,max}{\Bigl [}{1.0-0.2{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}-0.8{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}^{2}}{\Bigr ]}=2,065{\Bigl [}{1.0-0.2{\Bigl (}{800 \over 1,734}{\Bigr )}-0.8{\Bigl (}{800 \over 1,734}{\Bigr )}^{2}}{\Bigr ]}=1,523STB/D}$  |  |  |  |   
---|---|---  
  
(1.61)  
  
Fetkovich's IPR relies on multiple test points to determine the deliverability exponent 'n'. Table 1.9 outlines the test data organized for plotting. These data points are graphed on a logarithmic scale, facilitating the calculation of the slope for the most accurate straight line fit. The deliverability exponent 'n' is the reciprocal of this slope. With 'n' established, EQXX can be employed to estimate the peak oil production rate. Fig 1.9 depicts the graph of the data, revealing a best-fit straight line with a slope of 1.347, resulting in an 'n' value of 0.743. Consequently, the anticipated maximum oil production rate is 1,497 STB/D, as indicated by eq 1.62.

${\displaystyle q_{o,max}={q_{o} \over 1.0-0.2{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}-0.8{\Bigl (}{P_{wf} \over {\bar {P_{R}}}}{\Bigr )}^{2}}={768 \over 1.0-0.2{\Bigl (}{1,347 \over 1,734}{\Bigr )}-0.8{\Bigl (}{1,347 \over 1,734}{\Bigr )}^{2}}=1,497STB/D}$  |  |  |  |   
---|---|---  
  
(1.62)  
  
After ascertaining the maximum rate, it is utilized in conjunction with eq 1.62 to forecast production rates at different flowing bottomhole pressures, employing a similar approach as demonstrated in Vogel’s IPR. Applying Fetkovich’s method, the production rate is projected to be 1,253 STB/D at a flowing bottomhole pressure of 800 psia.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/1.9..png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/1.9..png "Enlarge")

Table 1.9 Plotting data for Fetkovich IPR

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/fig1.9_new.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/fig1.9_new.png "Enlarge")

Fig. 1.9 Fetkovich analysis of multirate oilwell data

To employ the Jones, Blount, and Glaze method with this dataset, Table 1.10 was prepared, and the data was graphed on a coordinate grid as depicted in Fig. 1.10. The best-fit straight line resulted in a slope of 0.0004 psia/(STB/D)2, representing the turbulence coefficient 'b'. The intercept corresponds to the laminar flow coefficient and is calculated to be 0.23 psia/STB/D. These values are applied in Eq 1.47 to ascertain the maximum oil production rate of 1,814 STB/D under a flowing bottomhole pressure of 0 psig.

${\displaystyle q_{o,max}={-0.23+{\sqrt {0.23^{2}+4(0.0004)(1,734-0)}} \over 2(0.0004)}=1,814STB/D}$  |  |  |  |   
---|---|---  
  
(1.63)  
  
The inflow performance curve is created using the same approach, which is also used to predict the production rate at various flowing bottomhole pressures. The production rate is predicted to be 1,267 STB/D with a flowing bottomhole pressure of 800 psia.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/1.10..png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/1.10..png "Enlarge")

Table 1.10. Plotting data for Jones, Blount, and Glaze IPR

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/fig1.10..png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/fig1.10..png "Enlarge")

Fig. 1.10. Jones, Blount, and Glaze analysis of multirate oilwell test data

From this example, the maximum oil production rate and the production rate at an 800 psia flowing bottomhole pressure varied for each of the three ways. As a result, the IPR utilized in the study will determine the production estimates, and the petroleum engineer should be aware of this risk in any analysis they perform.

* * *

  
Implementing the composite IPR and Wiggins’ IPR parallels the approach used for Vogel’s IPR. For the composite IPR, it's important to choose the appropriate relationship to estimate 'J' based on the flowing bottomhole pressure of the test point. Meanwhile, Wiggins’ IPR provides projections for both oil and water production rates. The inflow performance curve is subsequently crafted by adding the anticipated oil rates to the water rates to yield the overall liquid rate.

  
Future Performance Methods. After a petroleum engineer has assessed the current productive capacity of a well, there is often a need to forecast its future performance for planning purposes. Standing was one of the early pioneers in addressing the prediction of future well performance based on IPRs. He utilized Vogel’s IPR along with a modified multiphase productivity index to establish a connection between current well performance and future projections. Unfortunately, this method has a drawback; it requires information about fluid properties and relative permeability behaviors. This makes Standing’s approach challenging to implement, as it entails estimating saturations, relative permeabilities, and fluid properties at a future reservoir pressure.

Fetkovich proposed an approximation for Standing’s modified multiphase productivity index ratios, suggesting they could be represented by the ratio of pressures. He put forward the idea that the anticipated maximum oil production rate in the future could be estimated from the current maximum production rate using this formula.

${\displaystyle {q_{o,max,f} \over q_{o,max,p}}={{\bar {P_{r,f}}} \over {\bar {P_{r,p}}}}{\Bigl (}{{\bar {P_{r,f}}} \over {\bar {P_{r,p}}}}{\Bigr )}^{2n}={\Bigl (}{{\bar {P_{r,f}}} \over {\bar {P_{r,p}}}}{\Bigr )}^{2n+1}}$  |  |  |  |   
---|---|---  
  
(1.64)  
  
Fetkovich extended this concept to incorporate into his IPR model. The 'n' exponent in Equation 1.59 represents the deliverability exponent in his IPR. However, Fetkovich's approach to future performance has been adapted for other IPR methods by setting the exponent to one, which often yields satisfactory results. This technique necessitates no additional information beyond what is already gathered for applying the various IPRs. It's important to note that Fetkovich's method assumes a constant deliverability exponent between current and future conditions. Additionally, Uhri and Blount[30] as well as Kelkar and Cox[31] have introduced future performance approaches for two-phase flow, which rely on rate and pressure data at two average reservoir pressures.

Wiggins[27] also introduced future performance relationships for both the oil and water phases when he introduced his three-phase IPRs. These relationships are expressed in eq 1.65 and eq 1.66.

${\displaystyle {q_{o,max,f} \over q_{o,max,p}}=0.15{{\bar {P_{r,f}}} \over {\bar {P_{r,p}}}}+0.84{\Bigl (}{{\bar {P_{r,f}}} \over {\bar {P_{r,p}}}}{\Bigr )}^{2}}$  |  |  |  |   
---|---|---  
  
(1.65)  
  
${\displaystyle {q_{w,max,f} \over q_{w,max,p}}=0.59{{\bar {P_{r,f}}} \over {\bar {P_{r,p}}}}+0.36{\Bigl (}{{\bar {P_{r,f}}} \over {\bar {P_{r,p}}}}{\Bigr )}^{2}}$  |  |  |  |   
---|---|---  
  
(1.66)  
  
In every scenario, after projecting the future maximum production rate based on current data, one can construct inflow performance curves at the desired future average reservoir pressure using their selected IPR method.

* * *

### Geothermal Well Performance

Reservoir performance, inflow performance, and wellbore performance are used to assess the deliverability of liquid-dominated geothermal reservoirs. For liquid-only flow, the inflow performance is expressed as a linear productivity index, and for two-phase flow, as a solution-gas drive relationship.

The connection between mass flow rate w and driving pressure (pr- PwJ) is likely to become non-linear at reasonably high flow rates and when a steam/water mixture flows from the reservoir into the wellbore. Vogel investigated this problem for solution-gas drive reservoirs; Menzies investigated the same problem of steam/water flow in fractures, including the influence of heat transmission from the rock to the two-phase mixture.

The main resource of a geothermal reservoir is its heat content which is extracted from subsurface by the produced fluid. The rate of production is influenced by the pressure, temperature, enthalpy, permeability, and reservoir dimensions, as well as by the thermophysical properties of the fluid. The correlations and methodologies develop in petroleum engineering have been adapted for use in the analysis of geothermal reservoir.

Garg and Kassoy (1981) analyzed a number of these curve to determine the thermal power output of a well, while Kjaran and Elliasson (1982) used data from the Svartsengi (Iceland) geothermal field and obtained a general output equation. Grant et al. (1982) discussed the behavior of different output curves by relating their form to well type. The major parameter associated with the shape of these curves, besides pressure and flowrate, are the enthalpy, temperature, density and viscosity.

Chu (1988) used the compared the techniques proposed by Fetkovich (1973) and Jones et al. 1976) and determined their applicability to the diagnosis of the well conditions. The author also showed that the productivity index (J) geothermal wells changes with the extracted volume of fluid and with exploitation time. Freeston and Hadgu (1988) used a wellbore flow simulator to obtain the inflow curves of geothermal wells.

Iglesias and Moya (1990) develop the first dimensionless inflow curve for geothermal reservoir, assuming that the geothermal fluid as being compress pure liquid water. The corresponding inflow curve for thermal productivity (thermal power) is

${\displaystyle \left({\frac {Pot}{Potmax}}\right)=0.7\left({\frac {W}{Wmax}}\right)+0.3\left({\frac {W}{Wmax}}\right)^{2}}$  |  |  |  |   
---|---|---  
  
(1.67)  
  
Where Pot (=Wh) is the thermal power and h is the flowing enthalpy of the liquid water.

Moya (1994) obtained the dimensionless inflow curves assuming that the geothermal fluid was a binary system composed of H2O and CO2, the effects of non-condensable gases were included using a CO2 concentration of 0.5% by mass. The expression for mass productivity is given by

${\displaystyle \left({\frac {W}{Wmax}}\right)=1.0-0.256\left({\frac {Pwf}{pe}}\right)-0.525\left({\frac {Pwf}{pe}}\right)^{2}-0.057\left({\frac {Pwf}{pe}}\right)^{3}-0.162\left({\frac {Pwf}{pe}}\right)^{4}}$  |  |  |  |   
---|---|---  
  
(1.68)  
  
## Wellbore Flow Performance

The pressure differential encountered during the upward movement of reservoir fluids to the surface represents a critical parameter influencing the deliverability of wells. This phenomenon accounts for a significant portion, potentially reaching 80%, of the overall pressure loss experienced in a flowing well. The performance of wellbore flow is contingent upon the estimation of the pressure-rate relationship within the wellbore as reservoir fluids traverse the tubular conduits towards the surface. This flow path encompasses the passage of fluids through perforations, a screen and liner system, and packers before entering the tubing for further transportation to the surface. Notably, the tubing may incorporate completion equipment, such as profile nipples, sliding sleeves, or subsurface flow-control devices, which serve as flow constrictions. Furthermore, the tubing string may exhibit variations in tubing diameters or permit the flow of fluids through the tubing/annulus to reach the surface. Upon reaching the surface, the fluid must navigate through wellhead valves, surface chokes, and the flowline, which encompasses surface piping, valves, and fittings leading to the surface-processing equipment. The pressure decline encountered during the fluid's journey from the reservoir sandface to the surface is contingent upon the mechanical configuration of the wellbore, fluid properties, and the production rate.

Relationships to estimate this pressure drop in the wellbore are based on the mechanical energy equation for flow between two points in a system as written in below :

${\displaystyle {\frac {P_{1}}{\rho }}+{\frac {g}{g_{c}}}Z_{1}+\alpha {\frac {v_{1}^{2}}{2g_{c}}}={\frac {p_{2}}{\rho }}+{\frac {g}{g_{c}}}+\alpha {\frac {v_{2}^{2}}{2g_{c}}}+W+E_{i}}$  |  |  |  |   
---|---|---  
  
(1.69)  
  
Within this correlation, α represents the correction factor for the velocity distribution's kinetic energy, W symbolizes the work executed by the fluid in motion, and El represents the irreversible energy losses within the system, encompassing viscous or frictional losses. In the majority of practical scenarios, no work is performed either by or on the fluid, and it is commonly assumed that the kinetic energy correction factor is equal to one. Under these conditions, Eq. 1.70 can be rewritten in terms of the pressure change as

${\displaystyle {\frac {\Delta p}{\rho }}={\frac {g}{g_{c}}}\Delta Z+\left({\frac {\Delta (v^{2}}{2gc}}\right)+E_{i}}$  |  |  |  |   
---|---|---  
  
(1.70)  
  
The presented equation establishes that the total pressure drop experienced by a fluid system corresponds to the cumulative effect of alterations in potential energy (resulting from changes in elevation), modifications in kinetic energy (due to acceleration), and energy losses occurring within the system. This equation can be expressed differentially to encompass fluid flows in pipes with varying inclinations

${\displaystyle {\frac {dp}{dL}}={\frac {g}{g_{c}}}\rho \sin \theta +{\frac {pv}{gc}}{\frac {dv}{dL}}+{\frac {f\rho v^{2}}{2g_{c}d}}}$  |  |  |  |   
---|---|---  
  
(1.71)  
  
With Equation 1.64, it becomes possible to estimate the pressure drop associated with a specific flow rate and subsequently plot it as a function of the said rate. In typical applications, the wellhead pressure remains constant while the bottomhole flowing pressure, represented by pwf, is determined by evaluating the pressure drop. Employing this methodology facilitates the generation of a wellbore flow performance curve, where the pressure is graphed against the flow rate, as exemplified in Figure below. Specifically, this case study maintains a fixed wellhead pressure, while the flowing bottomhole pressure is computed based on the corresponding rate. This curve is commonly referred to as a tubing-performance curve, as it provides insight into the requisite flowing bottomhole pressure for various rates.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/figure_xx.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/figure_xx.png "Enlarge")

Fig 1.11 Typical tubing performance curve for constant wellhead pressure.

### Single-Phase Liquid Flow

Single-phase liquid flow holds limited significance, with the exception of situations involving water supply or injection wells. However, in such cases, Equation 1.64 can be employed, wherein the friction factor, denoted as f, is contingent upon both the Reynolds number and the roughness of the pipe. Typically, the friction factor is estimated using the Moody friction factor diagram, which offers a graphical representation of this parameter. It is important to note that the friction factor relies on empirical determination and is susceptible to errors due to its reliance on pipe roughness, which can be influenced by factors like erosion, corrosion, or deposition.

### Single-Phase Vapor Flow

Multiple techniques are available for estimating pressure drops in single-phase gas flow, both in static and flowing states. Among these methods, the average temperature and compressibility approach, as well as the original and modified Cullendar and Smith methods, are commonly employed. However, due to the compressible nature of gas, these approaches necessitate a trial-and-error or iterative methodology to determine the pressure drop for a given flow rate. Although these techniques require intensive calculations, they can be easily implemented within computer programs. Lee and Wattenbarger provide an extensive analysis and discussion of various methods utilized for estimating pressure drops in gas wells

Katz et al. introduced a streamlined approach for computing pressure drops in gas wells, employing the assumption of average temperature and average compressibility throughout the flow length. This simplified method provides a practical means of estimating the pressure drop in gas wells.

${\displaystyle q_{g}=200\left\lfloor {\frac {Sd^{5}{\Bigl (}(P_{w}f)^{2}-e^{s}(p_{w}h)^{2}{\Big )}}{\gamma _{g}T_{z}Lf_{M}(e^{S}-1)}}\right\rfloor }$  |  |  |  |   
---|---|---  
  
(1.72)  
  
Extensive literature exists regarding the intricate nature of multiphase fluid flow within pipes. This phenomenon proves significantly more complex than single-phase flow due to the simultaneous movement of both liquid components (such as oil, condensate, and water) and vapor (gas). The mechanical energy equation (Eq. 1.64) serves as the foundation for methods employed to estimate pressure drops in multiphase flow scenarios. However, a challenge arises in determining the appropriate values for velocity, friction factor, and density that should be considered for the multiphase mixture during calculations. Furthermore, the problem is further compounded by the fact that velocities, fluid properties, and the vapor-to-liquid fraction undergo alterations as the fluid progresses towards the surface due to changes in pressure.

Numerous researchers have proposed various methodologies to estimate pressure drops in multiphase flow, incorporating a combination of theoretical principles, experimental investigations, and field observations. Consequently, some researchers have sought to establish correlations between pressure-drop calculations and distinct flow patterns that emerge within the system. These flow patterns, or flow regimes, relate to the distribution of each fluid phase within the pipe. Therefore, accurate pressure calculations are contingent upon predicting the specific flow pattern being experienced. In the simplest classification of flow regimes, four primary flow patterns have been identified: bubble flow, slug flow, transition flow, and mist flow, each exhibiting an escalating proportion of vapor to liquid from bubble to mist flow. Bubble flow arises when the liquid phase maintains continuity, with small gas bubbles dispersed randomly within the liquid medium. Slug flow, on the other hand, manifests as large gas bubbles that separate liquid slugs within the flow stream. As the flow transitions to the transition flow regime, the liquid slugs diminish, and the gas phase becomes the dominant continuous phase, with gas bubbles prevailing between intermittent liquid regions. Finally, in the mist-flow pattern, the liquid phase is fragmented into small droplets entrained within the gas phase.

Poettman and Carpenter were among the pioneering researchers who focused on developing a correlation for multiphase flow in oil wells, whereas Gray introduced an early correlation for gas wells. Numerous studies have since been conducted concerning multiphase flow in pipe systems. Notably, Brill and Mukerjee, as well as Brown and Beggs, have compiled comprehensive reviews encompassing several correlations proposed in this field. The application of multiphase flow correlations necessitates an iterative and trial-and-error approach to accommodate the varying flow parameters dependent on pressure. This iterative process entails intensive calculations and is most effectively executed using computer programs.

### Multiphase Flow

Extensive literature exists regarding the intricate nature of multiphase fluid flow within pipes. This phenomenon proves significantly more complex than single-phase flow due to the simultaneous movement of both liquid components (such as oil, condensate, and water) and vapor (gas). The mechanical energy equation (Eq. 1.64) serves as the foundation for methods employed to estimate pressure drops in multiphase flow scenarios. However, a challenge arises in determining the appropriate values for velocity, friction factor, and density that should be considered for the multiphase mixture during calculations. Furthermore, the problem is further compounded by the fact that velocities, fluid properties, and the vapor-to-liquid fraction undergo alterations as the fluid progresses towards the surface due to changes in pressure.

Numerous researchers have proposed various methodologies to estimate pressure drops in multiphase flow, incorporating a combination of theoretical principles, experimental investigations, and field observations. Consequently, some researchers have sought to establish correlations between pressure-drop calculations and distinct flow patterns that emerge within the system. These flow patterns, or flow regimes, relate to the distribution of each fluid phase within the pipe. Therefore, accurate pressure calculations are contingent upon predicting the specific flow pattern being experienced. In the simplest classification of flow regimes, four primary flow patterns have been identified: bubble flow, slug flow, transition flow, and mist flow, each exhibiting an escalating proportion of vapor to liquid from bubble to mist flow. Bubble flow arises when the liquid phase maintains continuity, with small gas bubbles dispersed randomly within the liquid medium. Slug flow, on the other hand, manifests as large gas bubbles that separate liquid slugs within the flow stream. As the flow transitions to the transition flow regime, the liquid slugs diminish, and the gas phase becomes the dominant continuous phase, with gas bubbles prevailing between intermittent liquid regions. Finally, in the mist-flow pattern, the liquid phase is fragmented into small droplets entrained within the gas phase.

Poettman and Carpenter were among the pioneering researchers who focused on developing a correlation for multiphase flow in oil wells, whereas Gray introduced an early correlation for gas wells. Numerous studies have since been conducted concerning multiphase flow in pipe systems. Notably, Brill and Mukerjee, as well as Brown and Beggs, have compiled comprehensive reviews encompassing several correlations proposed in this field. The application of multiphase flow correlations necessitates an iterative and trial-and-error approach to accommodate the varying flow parameters dependent on pressure. This iterative process entails intensive calculations and is most effectively executed using computer programs.

Pressure calculations are commonly depicted as pressure-traverse curves, similar to the one illustrated in Figure 1.12, for specific tubing diameters, production rates, and fluid properties. These pressure-traverse curves are constructed for a range of gas-liquid ratios and offer estimates of pressure as a function of depth. Such curves can be employed for rapid manual calculations.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/image_xx.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/image_xx.png "Enlarge")

Fig 1.12 Pressure traverse curves

## Flow Through Chokes

The wellhead choke plays a crucial role in regulating both the surface pressure and production rate of a well. Choke selection is typically aimed at ensuring that variations in line pressure beyond the choke have no impact on the production rate. This necessitates operating the choke under critical flow conditions, where the flow rate is solely determined by the upstream or tubing pressure. To achieve critical flow, the downstream pressure should ideally be approximately 0.55 or less of the tubing pressure.

For single-phase gas flow, Beggs presents Eq. 1.68, which relates the gas production rate through a choke to the wellhead pressure.

${\displaystyle q_{g}={\frac {27.611C_{d}p_{w}hd^{2}T_{s}c}{p_{s}c{\sqrt {\gamma _{g}T_{w}hZ}}}}{\sqrt {({\frac {k}{k-1}})({y^{\tfrac {2}{k}}-y^{\tfrac {k+1}{k}})}}}}$ 

The pressure ratio, denoted as y, represents the ratio between the downstream pressure and the wellhead pressure. When the flow reaches critical conditions, the pressure ratio is substituted with the critical pressure ratio, yc. The critical pressure ratio signifies the threshold pressure ratio at which the flow transitions to a critical state. The specific value of this critical pressure ratio is contingent upon the ratio of the specific heats of the gas being produced, as indicated in Equation 1.69.

${\displaystyle y_{c}=({\frac {2}{k+1}})^{(}{\tfrac {k}{k}}-1)}$ 

Empirical equations have been formulated to estimate the correlation between the production rate and wellhead pressure specifically for two-phase critical flow scenarios. These correlations can be expressed in a manner resembling Equation 1.70, where the relationship between the production rate and wellhead pressure can be effectively described.

${\displaystyle Pwh=A_{1}q_{L}R^{A}}$ 

Gilbert was the initial researcher to introduce a relationship of this nature, utilizing field data obtained from California's Ten Section field. Subsequently, Ros and Beggs have also proposed relationships that have gained significant usage. Table 1.9 provides a comprehensive overview of the parameters associated with each equation.Tabel 1.9

TABLE 1.9 - Multiphase Choke Coefficients  
---  
| Researcher |  | A1 |  | A2 |  | A3 |   
| Gilbert |  | 3.86 x 10-3 |  | 0.546 |  | 1.89 |   
| Ros |  | 4.26 x 10-3 |  | 0.500 |  | 2.00 |   
| Baxendell |  | 3.12 x 10-3 |  | 0.546 |  | 1.93 |   
| Achong |  | 1.54 x 10-3 |  | 0.650 |  | 1.88 |   
  
Example

This example illustrates the use of the multiphase choke equation (Eq. 1.70) to estimate the flowing wellhead pressure for a given set of well conditions. However, this equation can be used to estimate flow rate or choke diameter. The example well is producing 400 STB/D of oil with a gas-liquid ratio of 800 Scf/STB. Estimate the flowing wellhead pressure for a choke size of 12/64 in. with Gilbert’s choke equation.

Under the specified conditions, the anticipated flowing wellhead pressure is determined to be 1,405 psia. However, when the Ros choke equation is employed, the calculated estimate for the flowing wellhead pressure amounts to 1,371 psia. It is noteworthy that each of these relationships offers marginally distinct approximations for the calculated value.

## Systems Analysis

For many years, systems analysis has been used to evaluate the performance of complex systems comprising multiple interacting components. While Gilbert is credited with introducing this approach to oil and gas wells, Mach, Proano, and Brown played a significant role in popularizing it within the industry, often referred to as Nodal Analysis™. The main objective of systems analysis in the oil and gas sector is to combine the different elements of a production system for an individual well, enabling the estimation of production rates and optimization of the system's components.

To understand the flow of reservoir fluids from subsurface reservoirs to stock tanks or sales lines, it is necessary to comprehend the principles governing fluid flow through porous media and well tubulars. As fluids traverse the production system, there will be a pressure drop associated with the fluid flow. This pressure drop is the cumulative effect of pressure drops occurring across various components in the production system. Given the compressible nature of fluids produced in oil and gas operations, the pressure drop is influenced by the interaction among the system's components. This is because the pressure drop in a specific component is not solely dependent on the flow rate through that component, but also on the average pressure within the component.

As a result, the design of a production system requires an integrated approach, as it cannot be treated as separate reservoir and piping components to be analyzed independently. The quantity of oil and gas produced from the reservoir to the surface is contingent upon the total pressure drop within the production system, and this pressure drop is influenced by the fluid flow rate through the system. Therefore, it is essential to analyze the entire production system as a cohesive unit or system.

The total pressure drop in the production system, illustrated in Figure 1.1, varies depending on the endpoint of the system. When the separator serves as the termination point of the production system, the total pressure drop is determined by the disparity between the average reservoir pressure and the pressure at the separator.

${\displaystyle \Delta p_{T}={\bar {p}}_{R}-p_{s}}$  |  |  |  |   
---|---|---  
  
(1.72)  
  
The overall pressure drop comprises several individual pressure drops that occur at different stages as the reservoir fluid travels to the surface. These pressure drops arise as the fluid passes through the reservoir, well completion, tubing, wellhead equipment, choke, and surface flowlines before reaching the separator. Hence, the total pressure drop described in Equation 1.72 can be represented by Equation 1.73.

${\displaystyle \Delta p_{T}=\Delta p_{1}+\Delta p_{2}+\Delta p_{3}+\Delta p_{4}}$  |  |  |  |   
---|---|---  
  
(1.73)  
  
The individual pressure drops can be further divided to account for various restrictions, subsurface safety valves, tubing accessories, and other factors.

Systems analysis is built upon the principle of continuity. At any given point within the production system, there exists a specific pressure and production rate associated with that point under certain conditions. If any changes occur within the system, the pressure and/or production rate at that same point will be affected accordingly. This concept allows the production system to be divided at a specific point of interest, enabling the evaluation of the two segments of the system. By evaluating the conditions of pressure and production rate continuity at the division point, the estimated operating conditions for the evaluated system can be determined.

This approach offers the flexibility to divide the production system at any desired point within the system to assess a particular component. The most common division points are either at the wellhead or at the perforations, either at the reservoir sandface or within the wellbore. The upstream end of the system comprises the reservoir, while the downstream end is represented by the separator or the wellhead if a wellhead choke controls the well.

The components upstream of the division point or node constitute the inflow section of the system, while the components following the node represent the outflow section. Once the system is divided into inflow and outflow sections, relationships are established to describe the rate-pressure correlation within each section. The flow rate through the system is determined once the conditions of continuity are satisfied: the inflow equals the outflow at the division point, and the pressure at the division point remains consistent in both the inflow and outflow sections of the system.

After selecting the division point, pressure relationships are formulated for the inflow and outflow sections of the system to estimate the pressure at the node. The pressure in the inflow section is determined using Equation 1.74, while the pressure drop in the outflow section is calculated using Equation 1.75.

${\displaystyle {\bar {p}}_{R}-\Delta p_{u}=p_{n}}$  |  |  |  |   
---|---|---  
  
(1.74)  
  
${\displaystyle p_{s}+\Delta p_{d}=p_{n}}$  |  |  |  |   
---|---|---  
  
(1.75)  
  
The pressure drop experienced in any component, whether in the inflow or outflow section of the system, varies in relation to the flow rate. As a result, a range of flow rates is employed to calculate node pressures for each section of the system. Subsequently, plots are created to illustrate the relationship between node pressure and production rate for both the inflow and outflow sections. The curve representing the inflow section is referred to as the inflow curve, while the curve representing the outflow section is known as the outflow curve. The point of intersection between these two curves signifies the point of continuity, which is essential in the systems analysis approach. This intersection indicates the expected production rate and pressure for the analyzed system.

Figure 1.13 presents a systems graph that illustrates a sensitivity study involving three different combinations of outflow components labeled as A, B, and C. In the case of outflow curve A, there is no intersection with the inflow performance curve. Because there is no intersection it indicates a lack of continuity within the system, implying that the well is not expected to produce under System A. In the other hand, the inflow and outflow performance curves intersect for System B, demonstrating continuity and suggesting that the well is expected to produce at a rate and pressure indicated by the intersection of the inflow and outflow curves. System C also exhibits an intersection, and it is anticipated to produce at a higher rate and lower pressure compared to System B, as indicated by the graph.

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_030_image_0001.png)

[](Inflow and outflow performance _ Society of Petroleum Engineers \(SPE\) _ OnePetro_files/vol4_page_030_image_0001.png "Enlarge")

Fig 1.3 Inflow and outflow performance curves for systems analysis.

The outflow curve for System C exhibits a pattern where the pressure rapidly decreases at low flow rates, reaches a minimum, and then gradually increases as the flow rate increases. This behavior is commonly observed in many outflow curves, which sometimes result in two intersection points with the inflow curve. However, the intersection at the lower flow rate is not a stable solution and holds no meaningful significance. The correct intersection point between the inflow and outflow curves should be located to the right of the minimum pressure on the outflow curve and several pressure units higher.

To evaluate the impact of changing any component within the system, the node pressure needs to be recalculated based on the new characteristics of the system. If a modification is made to an upstream component, the inflow curve will be altered while the outflow curve remains unchanged. In the other hand, if a change occurs in a downstream component, the inflow curve remains the same while the outflow curve is modified. Altering the fixed pressures within the system, such as reservoir depletion, separator conditions, or wellhead pressures, will result in shifts of both the inflow and outflow curves.

Systems analysis finds numerous applications in the analysis and design of oil and gas wells. It is suitable for evaluating both flowing wells and artificial lift applications. The approach offers valuable insights during the initial completion design phase. Even with limited data, various completion scenarios can be assessed to provide a qualitative estimation of the expected behavior of the well. This process proves useful in analyzing existing producing wells to identify flow restrictions or opportunities for performance enhancement.

Typical applications of systems analysis include estimating flow rates, selecting appropriate tubing and flowline sizes, determining optimal wellhead pressures and surface choke sizes, assessing the effects of reservoir pressure depletion, and identifying flow restrictions. It is also used for sizing subsurface safety valves, evaluating perforation density, designing gravel packs, optimizing gas-liquid ratios for gas lift operations, analyzing the effects of lower wellhead pressures or the installation of compression, and evaluating well stimulation treatments. Additionally, systems analysis can be employed to evaluate multiwell production systems. Overall, systems analysis is a robust and flexible methodology that supports the design of well completions and enhances the performance of producing wells.

## References

  1. ↑ [1.0](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_ref-:1_1-0) [1.1](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_ref-:1_1-1) Rawlins, E.L. and Schellhardt, M.A. 1935. Backpressure Data on Natural Gas Wells and Their Application to Production Practices, Vol. 7. Baltimore, Maryland: Monograph Series, US Bureau of Mines.
  2. [↑](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_ref-2) Houpeurt, A. 1959. On the Flow of Gases in Porous Media. Revue de L’Institut Francais du Petrole XIV (11): 1468–1684.
  3. [↑](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_ref-3) Forchheimer, P. 1901. Wasserbewegung durch Boden. Zeitz ver deutsch Ing 45: 2145.
  4. [↑](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_ref-4) Jones, L.G., Blount, E.M., and Glaze, O.H. 1976. Use of Short Term Multiple Rate Flow Tests To Predict Performance of Wells Having Turbulence. Presented at the SPE Annual Fall Technical Conference and Exhibition, New Orleans, Louisiana, 3-6 October 1976. SPE-6133-MS. http://dx.doi.org/10.2118/6133-MS
  5. ↑ [5.0](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_ref-:0_5-0) [5.1](https://onepetro.org/spe/general-information/1739/Inflow-and-outflow-performance#cite_ref-:0_5-1) Vogel, J.V. 1968. Inflow Performance Relationships for Solution-Gas Drive Wells. J Pet Technol 20 (1): 83–92. SPE 1476-PA. http://dx.doi.org/10.2118/1476-PA 


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

[Sign In](https://onepetro.org/sign-in?returnUrl=%2fspe%2fgeneral-information%2f1739%2fInflow-and-outflow-performance) or [Register](https://onepetro.org/my-account/register?siteId=1000201&returnUrl=%2fspe%2fgeneral-information%2f1739%2fInflow-and-outflow-performance)

[_Close Modal_](javascript:;)

[_Close Modal_](javascript:;)

## Sharing Unavailable

Sharing content requires targeting cookies to be enabled. Please update your cookie preferences to use this feature.

Update Cookie Preferences Cancel

This site uses cookies. By continuing to use our website, you are agreeing to [our privacy policy.](https://www.spe.org/en/about/privacypolicy/)

[Accept](javascript:;)
