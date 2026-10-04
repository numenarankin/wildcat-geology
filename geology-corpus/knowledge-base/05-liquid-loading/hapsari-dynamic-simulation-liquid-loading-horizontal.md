<!-- Source: hapsari-dynamic-simulation-liquid-loading-horizontal.pdf -->
<!-- Converted: mistral-ocr-latest -->

Journal of Earth Energy Science, Engineering, and Technology, Vol. 5, No. 3, 2022
URL: https://e-journal.trisakti.ac.id/index.php/jeeset, DOI: https://dx.doi.org/10.25105/jeeset.v5i3.14611
Received: 22 August 2022, Accepted: 25 December 2022, Published: 30 December 2022

# Dynamic Simulation Approach for Liquid Loading in Horizontal Gas Well X Field Indonesia

(Pendekatan Simulasi Dinamis untuk Pemuatan Cairan dalam Sumur Gas Horizontal Lapangan X Indonesia)

Hairuni Hapsari¹*, Dwi Atty Mardiana², Shabrina Sri Riswati², Pri Agung Rakhmanto²

¹PT. Schlumberger Geophysics Nusantara, Indonesia

²Department of Petroleum Engineering, Universitas Trisakti, Jakarta, Indonesia

# Abstract

There has been intensive investigation on the understanding of the liquid loading phenomenon lately via experiment and transient approach. This is driven due to the limitation of the traditional approach using steady state Turner correlation to be used over a wide range of actual conditions (i.e such as under various tubing diameters, fluid condition (CGR/WGR), and horizontal or deviated trajectory of the well) which can lead to underpredict critical gas rate and mitigation action which directly impact the production and economics limit of the field. By nature, the liquid loading phenomena classified as transient or dynamic phenomena and hence couldn't be able to be explained under the steady state approach. The application of dynamic well modeling itself has been applied worldwide recently. Therefore, utilizing this new approach for estimating the critical gas rate for horizontal well bring benefit by reducing the uncertainty of the outcome and providing more accurate prediction compare to the traditional approach. The selection of the de-liquification method which uses the bullheading for the horizontal gas well in X field provides the highest production optimization and the most economical approach to the field as there is no additional opex cost required.

Keywords: Liquid Loading; Horizontal Well; De-liquification; Dynamic Well Modeling; Multiphase Flow

# Sari

Telah ada penyelidikan intensif tentang pemahaman fenomena pemuatan cairan akhir-akhir ini melalui eksperimen dan pendekatan transien. Hal ini didorong oleh keterbatasan pendekatan tradisional yang menggunakan korelasi Turner keadaan tunak untuk digunakan pada rentang kondisi aktual yang luas (misalnya, pada berbagai diameter tubing, kondisi fluida (CGR/WGR), dan lintasan sumur horizontal atau berarah) yang dapat menyebabkan tingkat gas kritis yang tidak dapat diprediksi dan tindakan mitigasi yang secara langsung berdampak pada batas produksi dan keekonomian lapangan. Secara alami, fenomena pemuatan cairan diklasifikasikan sebagai fenomena sementara atau dinamis dan karenanya tidak dapat dijelaskan dengan pendekatan keadaan tunak. Penerapan pemodelan sumur dinamis sendiri telah diterapkan di seluruh dunia akhir-akhir ini. Oleh karena itu, memanfaatkan pendekatan baru ini untuk memperkirakan laju gas kritis untuk sumur horizontal membawa manfaat dengan mengurangi ketidakpastian hasil dan memberikan prediksi yang lebih akurat dibandingkan dengan pendekatan tradisional. Pemilihan metode de-liquifikasi yang menggunakan bullheading untuk sumur gas horizontal di lapangan X memberikan optimalisasi produksi tertinggi dan pendekatan yang paling ekonomis untuk lapangan tersebut karena tidak diperlukan biaya opex tambahan..

Kata-kata kunci: Pemuatan Cairan; Sumur Horisontal; De-liquifikasi; Pemodelan Sumur Dinamis; Aliran Multifasa

*Corresponding author

E-mail: hhapsari30@gmail.com

# I. INTRODUCTION

One of the main problems with mature gas wells is liquid loading which has a direct impact on decreasing gas production. Planning the right de-liquification technique plays a very important role in reducing the risk of implementation failure and returns on investment in wells produced. [1]

Turner et al (1969) observed the characteristics of liquid loading in a number of wells in the US onshore field using 106 data points. They found that a free-falling particle in a fluid medium will reach a terminal velocity. The velocity is a function of particle density, shape, and size. In addition, it is also a function of the viscosity and density of the fluid medium. Based on the concept, they introduced the correlation for

calculating the terminal velocity of liquid droplets in a flowing gas column as follows [2].

$$v_t = 1.912 \left[ \frac{\sigma^{0.25} (\rho_L - \rho_g)^{0.25}}{(\rho_g)^{0.5}} \right] \tag{1}$$

For 50 years, Turner's correlation (1969) has been used to predict the minimum gas velocity before liquid loading occurs which is accurate for wells with small diameter tubing and for vertical wells [2].

In contrast to Turner, Coleman (1991) predicted that there was a need a correction factor to reduce 20% from Turner correlation for wells where the pressure

eISSN: 2614-0268

104

pISSN: 2615-3653

Journal of Earth Energy Science, Engineering, and Technology, Vol. 5, No. 3, 2022

URL: https://e-journal.trisakti.ac.id/index.php/jeeset, DOI: https://dx.doi.org/10.25105/jeeset.v5i3.14611

Received: 22 August 2022, Accepted: 25 December 2022, Published: 30 December 2022

in the well was already low. Coleman used experiments on North Sea gas wells (66 data sets) and proposed the following equation [3, 4].

\[
\mathrm{v} _ {\mathrm{t}} = 1. 5 9 3 \left[ \frac {\sigma^ {0 . 2 5} \left(\rho_ {\mathrm{L}} - \rho_ {\mathrm{g}}\right) ^ {0 . 2 5}}{\left(\rho_ {\mathrm{g}}\right) ^ {0 . 5}} \right] \tag {2}
\]

However, based on research by Veeken et al, Turner correlation for deviated wells and large tubing sizes was not appropriate where the minimum gas velocity could be different from actual/field results where the difference in results could reach the range of 20-200% [5]. Yusuf et al. (2010) reported that liquid loading was a dynamic phenomenon where there was a change in the flow regime [6].

![img-0.jpeg](img-0.jpeg)

Figure 1. Comparison of critical flow rate predictions between Turner correlation, OLGA simulation, and actual data from the field [6]

Critical gas rate is defined as minimum gas flow rate for the continuous removal of liquids from a wellbore  \( [7,8] \) . Coleman et al. proposed a critical gas rate ( \( q_{c} \) ) equation as follows  \( [3,9-11] \) :

\[
\mathrm{q} _ {\mathrm{c}} = 3. 0 6 \left(\frac {\mathrm{pv} _ {\mathrm{t}} \mathrm{A}}{\mathrm{Tz}}\right) \tag {3}
\]

Prediction using empirical correlation (steady state), such as Turner or Coleman correlations, cannot capture changes in the flow regime in the system. There is a need for a new approach that is accurate in analyzing liquid loading, especially for horizontal wells.

## II. METHOD

The research was conducted in 5 stages as indicated in Figure 2. The explanation of the figure is as follows:

1. Collecting data for horizontal well experiencing liquid loading such as fluid composition, well survey data, completion data, reservoir data, and well production data.
2. Horizontal well modeling and validation using

field data (actual gas rate is 6 MMscfd).

3. Estimate the critical gas flow rate for liquid loading with two methods, namely

a. Using empirical calculations based on Turner and Coleman correlations.
b. Using OLGA dynamic modeling to determine the gas rate critical for liquid loading [12].

4. Conducting sensitivity de-liquification method to get estimates of gas production and well intervention costs. The methods used are:

a. Doing bullheading with dynamic modeling.
b. Perform velocity strings with dynamic modeling.

5. Comparing economic projects for the right selection of production optimization.

![img-1.jpeg](img-1.jpeg)

Figure 2. Research Method

## III. RESULTS AND DISCUSSION

This section discusses the analysis of the critical gas flow rate between the empirical approach (Turner

eISSN: 2614-0268

105

pISSN: 2615-3653

Journal of Earth Energy Science, Engineering, and Technology, Vol. 5, No. 3, 2022

URL: https://e-journal.trisakti.ac.id/index.php/jeeset, DOI: https://dx.doi.org/10.25105/jeeset.v5i3.14611

Received: 22 August 2022, Accepted: 25 December 2022, Published: 30 December 2022

and Coleman correlations) and the OLGA dynamic approach for liquid loading in the horizontal gas well X-1 as well as the selection of the de-liquification solutions to overcome these problems.

### 3.1 Critical Gas Rate

#### 3.1.1 Empirical Correlation

Based on the empirical equations of Turner and Coleman, terminal velocity ( \( V_{t} \) ) and critical gas rate ( \( Q_{c} \) ) for X-1 well can be calculated. The calculation results are summarized in Table 1.

Table 1. Terminal Velocity and Critical Gas Rate Using Turner and Coleman Correlations for X-1 Well

|  No | Parameter | Unit | Turner | Coleman  |
| --- | --- | --- | --- | --- |
|  1 | \( v_t \) | ft/sec | 11.1 | 9.2  |
|  2 | \( q_c \) | MMscfd | 4.1 | 3.4  |

#### 3.1.2. Mechanistic Correlation (Dynamic Simulation)

In a dynamic simulation, determination of the critical flow rate of the X-1 well can be determined by performing a sensitivity production rate where the accumulation of liquid continues to increase so that it reaches a point where the production rate of the well cannot flow continuously. This point is taken as the critical gas flow point for liquid loading. The sensitivity of gas production and liquid accumulation is shown in Figure 3.

Based on the figure, it can be concluded that for the dynamic approach, the critical gas flow rate is at 5 MMscfd where the total accumulated liquid increases drastically with time. The lower the gas flow rate, the higher the accumulation of liquid in the well. This is due to the lower the gas velocity to push water

droplets to the surface and the liquid film will accumulate in the tubing wall, so that liquid loading occurs.

The results of the critical gas flow rate using the OLGA dynamic/mechanistic approach have a relatively smaller percentage difference compared to the Turner and Coleman correlations as shown in Table 2. It can be concluded that the dynamic approach can provide more accurate results for horizontal wells.

### 3.2 De-liquification Selection

In order to solve the problem of liquid loading in the X-1 well, several production optimizations were carried out. The results are as follows.

#### 3.2.1 Bullheading Method

The objective of the bullheading method is to push the fluid that has accumulated in the well into the formation. This method was carried out using production facilities that were already available, namely using umbilical corrosion inhibitors and production gas. Based on the dynamic simulation, it is estimated that the production of the well will reach a production of 7 MMscfd as shown in Figure 4. The lower the gas flow rate, the higher the accumulation of liquid in the well. This is due to the lower the gas velocity to push water droplets to the surface and collect on the tubing wall, so that fluid loading occurs.

#### 3.2.2 Velocity String Method

To solve the problem of liquid loading in the X-1 well, sensitivity tubing sizes were carried out, namely 3" and 4" tubing. The results are shown in Figure 5.

![img-2.jpeg](img-2.jpeg)

![img-3.jpeg](img-3.jpeg)

Figure 3. Determination of Critical Gas Rate Using Dynamic Simulation

eISSN: 2614-0268

106

pISSN: 2615-3653

Journal of Earth Energy Science, Engineering, and Technology, Vol. 5, No. 3, 2022

URL: https://e-journal.trisakti.ac.id/index.php/jeeset, DOI: https://dx.doi.org/10.25105/jeeset.v5i3.14611

Received: 22 August 2022, Accepted: 25 December 2022, Published: 30 December 2022

Table 2. Critical Gas Rate Result Using Dynamic Simulation

|  No. | Method | Critical Gas Rate, MMscfd |   | % Diff.  |
| --- | --- | --- | --- | --- |
|   |   |  Predicted | Actual  |   |
|  1 | Turner | 4.1 | 6 | 31.7  |
|  2 | Coleman | 3.4 |   | 43.3  |
|  3 | OLGA | 5 |   | 16,7  |

![img-4.jpeg](img-4.jpeg)

![img-5.jpeg](img-5.jpeg)

Figure 4. Determination of Production Optimization Using Bullheading Method

![img-6.jpeg](img-6.jpeg)

![img-7.jpeg](img-7.jpeg)

|  Tubing Size | Tubing Rate | Accumulation Liquid in the Tubing | Critical Gas Rate  |
| --- | --- | --- | --- |
|  3” | 2.2 MMscfd | 1.1 \( m^{3} \) | 0.7 MMscfd  |
|  4” | 3.8 MMscfd | 1.7 \( m^{3} \) | 1.5 MMscfd  |

Figure 5. Production Optimization Using Velocity String Method

Table 3. De-liquification Selection

|  Production Optimization | Rate, MMscfd | Cost, USD | Analysis  |
| --- | --- | --- | --- |
|  Bulheading | 7.2 | 0 | Using existing facilities:☐ Injection facilities using available chemical umbilical☐ Using gas production on existing platforms  |
|  Velocity String | 3.8 | 750K | Installation Velocity String and Workover Rig NPV = -750kIRR = -13.5%  |

The economics of the X-1 Well production optimization method is given in Table 3. The Bullheading method can produce higher yields than velocity strings without requiring additional investment. Meanwhile, the application of velocity

strings in subsurface facilities requires a large additional cost, namely the use of workover rigs during tubing installation. It can be concluded that the bullheading method is the most appropriate solution for the X-1 well.

eISSN: 2614-0268

107

pISSN: 2615-3653

Journal of Earth Energy Science, Engineering, and Technology, Vol. 5, No. 3, 2022

URL: https://e-journal.trisakti.ac.id/index.php/jeeset, DOI: https://dx.doi.org/10.25105/jeeset.v5i3.14611

Received: 22 August 2022, Accepted: 25 December 2022, Published: 30 December 2022

## IV. CONCLUSION

Based on the results and discussion above, two statements are made as follows:

1. The dynamic simulation approach (OLGA software) can provide more accurate results for horizontal wells.
2. The bullheading method is the most appropriate solution for X-1 well where no additional investment is required.

## NOMENCLATURE

|  A | = flow area of conduit, ft\( ^{2} \)  |
| --- | --- |
|  p | = pressure, psia  |
|  q\( _{c} \) | = critical gas flow rate, MMscfd  |
|  T | = temperature, °R  |
|  v\( _{i} \) | = particle terminal velocity, ft/sec  |
|  z | = gas compressibility factor  |
|  ρ\( _{g} \) | = gas phase density, lbm/ft\( ^{3} \)  |
|  ρ\( _{L} \) | = liquid phase density, lbm/ft\( ^{3} \)  |
|  σ | = interfacial tension, dyne/cm  |

## ACKNOWLEDGEMENT

This study acknowledged Trisakti University and PT Schlumberger for Grant-in-aid for data processing and analysis purposes.

## REFERENCES

[1] Fernandez, J., Falcone, G., and Teodoriu, C. 2009. Design of a High-Pressure Research Flow Loop for the Experimental Investigation of Liquid Loading in Gas Wells. SPE-122786-MS, the Latin American and Caribbean Petroleum Engineering Conference, Cartagena de Indias, Colombia, May 2009. https://doi.org/10.2118/122786-MS.

[2] Turner, R.G., Hubbard, M.G., and Dukler, A.E. 1969. Analysis and Prediction of Minimum Flow Rate for the Continuous Removal of Liquids from Gas Wells. Society of Petroleum Engineers, Journal of Petroleum Technology, Vol. 21, No. 11, pp. 1475-1482. SPE-2198-PA. https://doi.org/10.2118/2198-PA

[3] Coleman, S.B., Clay, H.B., McCurdy, D.G., and Norris, L.H. 1991. A New Look at Predicting Gas-Well Load-Up. SPE-20280-PA, Journal of Petroleum Technology, Vol. 43, No. 3, pp. 329–333. https://doi.org/10.2118/20280-PA

[4] Falcone G. and Barbosa Jr., J.R. 2013. State of the Art Review of Liquid Loading in Gas Well. DGMK/ÖGEW Frühjahrstagung 2013, Fachbereich Aufsuchung und Gewinnung Celle, 18-19 April 2013.

[5] Veeken, K., Hu, B., and Schiferli, W. 2009. Transient Multiphase Flow Modeling of Gas Well Liquid Loading. SPE-123657-MS, the SPE Offshore Europe Oil and Gas Conference and Exhibition, September 8–11, 2009. https://doi.org/10.2118/123657-MS.

[6] Yusuf, R., Veeken, K., and Hu, B. 2010. Investigation of Gas Well Liquid Loading with a Transient Multiphase Flow Model. SPE-128470-MS, the SPE Oil and Gas India Conference and Exhibition, January 20–22, 2010. https://doi.org/10.2118/128470-MS.

[7] Veeken, K., Bakker, E., and Dousi, N. 2003. Liquid Loading in Gas Wells Symptoms and Cures. The 2003 SPE Annual Technical Conference and Exhibition, Denver, Colorado, 16-17 June.

[8] Veeken, K. and Belfroid, S. 2011. New Perspective on Gas-Well Liquid Loading and Unloading. SPE Prod & Oper., Vol. 26, No. 4, pp. 343–356. SPE-134483-PA. https://doi.org/10.2118/134483-PA.

[9] Sutton, R.P., Cox, S.A., Williams, Jr. E.G., Stoltz, R.P., Gilbert, J.V. 2003. Gas Well Performance at Subcritical Rates. SPE-80887-MS, the SPE Production and Operations Symposium, Oklahoma, 22–25 March 2003. https://doi.org/10.2118/80887-MS.

[10] Zhou, C., Wu, X., Li, H., Tang, J., and Liu, X. 2016. Research of Improvement and Optimization of Critical Flow Rate Model in Condensate Gas Well. OTC-26661-MS, the Offshore Technology Conference Asia held in Kuala Lumpur, Malaysia, 22–25 March 2016. https://doi.org/10.4043/26661-MS.

[11] El Fadili, Y. and Shah, S. 2017. A new model for predicting critical gas rate in horizontal and deviated wells. Journal of Petroleum Science and Engineering, Vol. 150, pp. 154-161. https://doi.org/10.1016/j.petrol.2016.11.038

[12] Biberg, D., Staff, G., Hoyer, N., and Holm, H. 2015. Accounting for flow model uncertainties in gas-condensate field design using the OLGA High Definition Stratified Flow Model. BHR-2015-G5, the 17th International Conference on Multiphase Production Technology, Cannes, France, June 2015.

eISSN: 2614-0268

108

pISSN: 2615-3653