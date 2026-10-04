<!-- Source: utp-thesis-cullender-smith-bottomhole-flowing-pressure.pdf -->
<!-- Converted: pdf-inspector (text_based, confidence 0.75) -->

NORHAZILAH ABDUL RAHMAN

MAY 2013

DEVELOPING A MATHEMATICAL MODEL FOR PREDICTING THE BOTTOM-HOLE FLOWING PRESSURE OF A GAS WELL

B.ENG. (HONS) PETROLEUM
NORHAZILAH BINTI ABDUL RAHMAN

ENGINEERING PETROLEUM ENGINEERING

UNIVERSITI TEKNOLOGI PETRONAS

MAY 2013

## CERTIFICATE OF APPROVAL

Developing a Mathematical Model for Predicting the Bottom-hole Flowing Pressure of a Gas Well

by Norhazilah Binti Abdul Rahman

Dissertation submitted in partial fulfillment of The requirement for the Bachelor of Engineering (Hons) (Petroleum Engineering) MAY 2013

Approved By, ____________________________ Muhammad Aslam Bin Md Yusuf

UNIVERSITI TEKNOLOGI PETRONAS TRONOH, PERAK

i

## CERTIFICATE OF ORIGINALITY

This is to certify that we are responsible for the work submitted in this project, that the original work is my own except as specified in the reference and acknowledgements, and that the original work contained herein have not been undertaken or done by unspecified sources or persons. ___________________________________________ NORHAZILAH ABDUL RAHMAN

ii

## ABSTRACT

As the economic importance of natural gas continues to grow, gas well surveillance equally generates more interest to the petroleum industry. The flowing bottom-hole pressures must be known in order to predict the productivity or absolute open flow potential of gas wells. These parameters are measured using down-hole gauges method of gas well test. In gas wells, down-hole parameters could be estimated using mathematical expressions instead of measured directly using gas well test procedure so that it will saving lots of dollars. The conventional method of gas parameter measurement include the iterative method, the Sukkar and Cornell method, Cullender and Smith method. Others are Crawford and Fancher and the Poettman method. All these methods involve very long and cumbersome iterative procedures. This makes the job of the field men very tedious, especially when the unit system changes. Similarly, data integrity is not guaranteed because data is far from actual. This research work presents a mathematical model for the predicting flowing bottom-hole pressure in gas wells, using the Average temperature and deviation method and the Cullender and Smith method. It utilizes a user- friendly window based Visual Basic for Application in Excels with adjustable unit system..

iii

## ACKNOWLEDGMENTS

My first gratitude would go to Allah SWT, all praise is due to Allah and this project would not have been possible without His help. My sincere gratitude is extended to my supervisor Mr. Muhammad Aslam Bin Md Yusof, I am grateful to his commitment and encouragement throughout the project. I would also like to thank my family for their help and support during my project. Finally, my gratitude goes to my friends for their friendship and help throughout the project.

iv

## TABLE OF CONTENTS

**CHAPTER 1**

1.1 BACKGROUND OF STUDY............................................................................ 1
1.2 PROBLEM STATEMENT ................................................................................3
1.3 OBJECTIVES.................................................................................................... 3
1.4 SCOPE OF STUDY ...........................................................................................4 **CHAPTER 2**
LITERATURE REVIEW……………………...………………………………..…...5

**CHAPTER 3.**

3.1 RESEARCH METHODOLOGY .......................................................................12
3.2 PROJECT ACTIVITES.....................................................................................12
3.3 KEY MILESTONE........................................................................................... 13
3.4 GANTT CHARTMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM........................................................ 14
3.5 RUNNING DIAGR�����������������..........�������
3.6 MATHEMATICAL MODEL0IN MS EXCEL������������PW
3.7 WORKFLOW SU����������������������MRO
v

## CHAPTER 4

4.1 DATA AVAILABILITY………………………………………………MMM 21
4.2 MANUAL CALCULATION……………..…MMM…………………………MMRR
4.3 RESULTS FROM THE MATHEMATICAL MODELLING IN THE VBA…. 26
4.4 DISC866I21������������������������MM0UP
## CHAPTER 5

5.1 CONCLUSIONS ............................................................................................. 53
5.2 RECOMMENDATIONS ................................................................................. 54
REFERENCES.............................................................................................................55

APPENDI������������������������������.58

vi

## LIST OF FIGURES

FIGURE 1: Mathematical model

FIGURE 2: Project activities

FIGURE 3: Microsoft Excel 2007 versus Microsoft Excel 2012

FIGURE 4: Developer Tab

FIGURE 5: Visual Basic Window

FIGURE 6: Macros Windows

FIGURE 7: User form in Visual Basic for Application Window

FIGURE 8: Workflow summary

FIGURE 9: Bottom-hole flowing pressure obtained from the mathematical modelling

FIGURE 10: Percentage error of Cullender and Smith method

FIGURE 11: Comparison of bottom-hole pressure for VBA and VB.NET

FIGURE 12: Error of bottom-hole flowing pressure calculated by using VBA for excel

and VB.NET

FIGURE 13: Bottom-hole flowing pressure by using Average Temperature and Deviation

method

FIGURE 14: Percentage Error for Average Temperature and deviation method.

FIGURE 15: Comparison between the Bottom-hole flowing pressures obtained from

VBA and VB.NET

FIGURE 16: Percentage error for VBA and VB.NET

FIGURE 17: Comparison between the actual pressures with the calculated pressures.

FIGURE 18: A logic flow chart for programming this method in digital computer

vii

## LIST OF TABLES

TABLE 1: Formula generated for Cullender and Smith method.

TABLE 2: Well data

TABLE 3: Bottom-hole flowing pressure

TABLE 4: Error calculated from the mathematical modelling

TABLE 5: Difference between the bottom-hole flowing pressures calculated from VBA

and VB.NET

TABLE 6: Error of bottom-hole flowing pressure calculated by using VBA for excel

and VB.NET

TABLE 7: Formula generated for Average Temperature and Deviation method

TABLE 8: Well data

TABLE 9: Bottom-hole flowing pressure from Average Temperature and deviation

method.

TABLE 10: Percentage error calculated for Average Temperature and deviation method.

TABLE 11: Comparison between the Bottom-hole flowing pressure obtained from VBA

and VB.NET

TABLE 12: Percentage error for VBA and VBA.NET

TABLE 13: Comparison between the actual pressures with the calculated pressure.

viii

## NOMENCLATURES

|Symbol|Description|
|---|---|
|λ|density of gas, Ibm/cuft|
|P|pressure, psia.|
|u|average velocity of the fluid|
|t|distance in vertical direction|
|f|moody friction factor|
|D|Inside diameter of the pipe, ft.|
|L|Length of the flow string, ft.|
|g|acceleration due to gravity, ft./sec2|
|gc|conversion factor, 32.17 lb. ft./lbfsec2|
|ws|mechanical work done on or by the gas|
|Pwf|flowing bottom-hole pressure, psia|
|Ptf|flowing well head pressure, psia|
|T|arithmetic average of bottom hole and wellhead temperatures|
|f|moody friction factor at arithmetic average temperature and pressure.|
|L|length of flow string, ft|
|Z|vertical distance of reservoir from surface|
|q|gas flow rate, MMcfd at 1465 psia and 60of|

D flow string diameter, in

ix

## CHAPTER 1

## INTRODUCTION

## 1.1 BACKGROUND OF STUDY

The increasing importance of gas in world economy has raised a lot of interest in gas well surveillance and parameters estimation. In oil wells, parameters like static pressure, flow bottom hole pressure and flow rate are measured using down hole gauges which is often inconvenient and expensive though more reliable. This justifies why the parameters used for gas well performance prediction surveillance are often estimated instead of measured directly.

Interest in the knowledge of parameters like the flowing bottom-hole pressure is due to their importance in real time gas well surveillance involving the prediction of the productivity or absolute open-hole flow potential of gas wells as well as gas condensate wells. Though for gas condensate wells, the gas equivalent of the liquid produced is calculated and used to modify the flow rate, specific gravity and gas deviation of the well efficiency. One of the key problems with the estimation of these parameters lies in the integrity of data used. Often, the data collected sometimes mar the estimation because the area vary far from the actual. Another key problem with the method of estimation of parameters using equations and tables is that it is very difficult and time consuming for the iteration, look-up and interpolation in each run and the calculation is simplified at the

expense of accuracy. With the popularity of computers and microcomputer software, the estimation of these parameters could be done with ease if the parameters and the procedures are carefully and intelligently programmed into the computer.

The objective of this study is to develop a microcomputer computer software using Visual Basic for Application in Excels for the estimation of flowing bottom-hole pressure. Bottom-hole flowing pressure is the pressure that is measured or in some cases calculated at the bottom of the well when the well is flowing or producing hydrocarbons. It will always be higher than the flowing pressure at the surface, but lower than the shut in bottom-hole pressure.

There is nothing more important in petroleum engineering than a definite knowledge of the pressure at the bottom of a gas well at any existing operating condition, and the relation of this pressure to the pressure within the producing formation. A knowledge of bottom- hole pressures is fundamental in determining the most efficient methods of recovery and the most efficient lifting procedure, yet there is less information about these pressures than about any other part of the general problem of producing gas. Many computer software programs have been developed to assist petroleum engineers and scientists for calculating bottom hole flowing pressure. These programs use analytical, numerical or empirical methods .A simple, fast and accurate method for predicting flowing bottom- hole pressure in gas wells is presented. The proposed mathematical modelling may be easily programmed for digital computers or it may be used for hand calculations. The mathematical modelling is superior to previously proposed methods in accuracy and rate of convergence. Accuracy of the method depends mainly on the type of input data

The advantage of using the microcomputer approach to parameters estimation is in two parts. First, it reduces the chances of errors in the calculation and hence increases the integrity of results obtained. Second, it makes it very easy for any person irrespective of their background the estimate the parameters with the user friendly dialog based windows- basic Visual Basic programs in any unit system. This project shows that instead of actual field data, bottom-hole pressures are calculated with a computer using any of several

methods such as Aziz, Cullender-Smith, and Gray. These calculated "experimental" values are used to determine an algebraic equation which best fits the data. The resulting algebraic equation is very simple and can be performed by field personnel using a hand- held calculator for any wellhead pressure for the particular field.

## 1.2 PROBLEM STATEMENT

The real time prediction of the bottom-hole pressure is one of the most important steps towards realizing real time monitoring of well performance. Flowing bottom-hole pressure is such an important parameter even at very early life of the well. The major problem is getting down-hole information without running tools into the well to make this measurement.

The measurement of flowing bottom-hole pressures in gas wells is a frequently incurred and costly operation in natural gas production. The calculation of this pressure from surface data is complex involving a trial and error solution of Bernoulli’s differential equation. A number of methods have been used previously for these solution usually requiring computer methods. A new procedure for calculating flowing bottom-hole pressures using only simple algebraic equations need to be developed so that this problem can be settled. Based on the foregoing the following recommendations are made computer programs for down-hole pressure estimation from surface measurement should be developed.

## 1.3 OBJECTIVES

The main objectives to developing a mathematical model for predicting a bottom hole flowing pressure for the gas well is to find the most accurate method to calculated the bottom hole flowing pressure for the gas well by using a mathematical model. Therefore, this research aims to:

1) To develop a mathematical model for predicting the bottom-hole flowing pressure of a gas well by using VBA for Microsoft Excel.

## 1.4 SCOPE OF STUDY

The scope of this project is studying how to design a mathematical model for predicting the bottom-hole flowing pressure in Microsoft Excel environment. I need to develop macro functions in Microsoft Excel using the formulas of bottom-hole flowing pressure calculation and creates necessary user form base in macro functions. In the beginning, author needs to study and research calculations of bottom-hole flowing pressure, what parameters and formulas need to use in calculating bottom hole flowing pressure of gas well. Author also need to understand the procedures of calculating the bottom hole flowing pressure to have an over view of software program. In the next step, author needs to learn how to create macro functions and user form in Microsoft Excel. In the final step, author will design a mathematical model using formulas, procedures of bottom-hole flowing pressure program and create interface of software base on macro functions and user form.

This project is actually about developing a mathematical modeling for predicting the bottom hole flowing pressure for gas well. Accurate flowing bottom-hole pressure are very important for gas reservoir calculations. Normally, these pressures are measured directly with pressure gauges placed at the well bottom. However, bottom-hole pressure are often impractical. Thus, several methods have been developed for estimating flowing bottom-hole pressure from surface measurements.

For the purpose of this research, two type of methods for predicting the bottom hole flowing pressure will be used to create the mathematical model which are, the Cullender and Smith methods and also Average Temperature and deviation method. For each method, analysis and comparison will be done.

## CHAPTER 2 LITERATURE REVIEW

## Mathematical model

“A mathematical model is a description of a system using mathematical concepts and language. In general, mathematical models may include logical models, as far as logic is taken as a part of mathematics. Lack of agreement between theoretical mathematical models and experimental measurements often leads to important advances as better theories are developed.” (Wikipedia)

FIGURE 1: Mathematical model (Carson and Cobelli, 2001).

## Definition of bottom-hole flowing pressure

Bottom hole flowing pressure is the pressure measured in pounds per square inch (psi), at the bottom of the hole. The methods developed for computing bottom- hole flowing pressure from surface measurements consider the flowing wellhead pressure, the pressure exerted by the weight of the gas column in the production string, and the energy losses resulting from gas flowing through pipe.

## Calculating the Bottom-Hole Flowing Pressure for Gas Wells.

All methods of calculating bottom-hole flowing pressure in gas wells involve a trial-and-error procedure. The number of trials necessary may be greatly reduced by the Newton-Raphson method proposed. Assuming that all trial-and-error method is equally useful along with other methods of calculating bottom-hole pressure. (Khalid Aziz) .The method may be expressed as in the figure 18 in the appendix.

Bottom-hole flowing pressure can be calculated by using the wellhead data:

- Gas specific gravity
- Wellhead pressure
- Wellhead temperature
- Formation temperature
- Well depth
Flowing bottom hole pressure calculation is the modification of static flowing bottom-hole pressure method which utilize Moody Friction Factor and average compressibility factor and average temperature. All the flowing bottom hole flowing pressure calculation techniques presented are based on an energy balance in the wellbore.

Several methods have been used to calculate the Bottom-hole flowing pressure (*Pwf)*

P𝑤𝑓 = flowing wellhead pressure + the pressure exerted by the weight of the gas column + the kinetic change + energy losses from friction. This equation is the basis for all methods of calculating flowing bottom-hole pressures from wellhead observation with assumptions:

1) Single phase gas flow
2) Negligible kinetic energy change
2

<u>53.34 Tz f Tz</u>
2 dp + dZ + 0<u>.</u>00268 5 () q dL γg p D p <u>Cullender and Smith method.</u> This methods makes no simplifying assumptions for the variation of either temperature or z factor in the wellbore. This calculation technique is applicable over a much wider range of gas well pressures and temperatures. To achieve The assumptions for this method are:

a) Steady-state flow
b) Single-phase flow
c) Change in kinetic energy is small and may be neglected
pw <u>p</u> <u>dp 1000γg Z</u> <u>Tz</u> ∫ = pi <u>f</u>

253.34
<u>2.6665 () q</u>
<u>1 p</u> 2 <u>4</u> 5 + () d 1000 Tz

*f*= moody friction factor *P*𝑤𝑓= bottom-hole pressure, psia *P*𝑡𝑓= wellhead (tubing) pressure, psia *ˠg* = gas gravity (air = 1.00) *L* = length of pipe, ft *Q*= gas flow rate MMscfd *T*= absolute temperature *z*= gas deviation factor *D*= internal diameter *Z*= depth of well

The usual procedure in bottom-hole flowing pressure calculations is to

1) Assume a value of *Pwf*
*2)*Compute the right-hand side of the equation.
3)Check to see if the computer value of the integral is equal to the known-left hand side of the equation. If the two sides of the equation are not equal within a certain allowable tolerance, the calculations are repeated with a new estimate of *Pwf*. The mathematical model used for evaluating the integral is usually either the trapezoidal rule or Simpson rule.
## <u>Average Temperature and Deviation Factor method.</u>

This method relates the change in wellbore pressure as a function of depth and gas density.

Assumptions in the average temperature and average gas deviation factor method are:

- Single-phase gas flow, although it may be used for condensate flow if proper adjustments are made in the flow rate, gas gravity and *z*-factor

- Steady-state flow
- Change in kinetic energy is small and may be neglected
- Constant temperature at some average value
- Constant gas deviation factor at some average value
- Constant friction factor over the length of the conduit
2 2 5 <u>25𝛾𝑔𝑇𝑧𝑓𝐿(𝑒⁵ − 1)𝑞²</u> 𝑃𝑤𝑓 = 𝑃𝑡𝑓 𝑒 + 5 𝑠𝐷

## Pwf= flowing bootom-hole pressure

## P𝑡𝑓 =Flowing wellhead pressure, psia

*T* = arithmetic average of bottom hole and wellhead temperatures, °R

*Z* = Gas deviation factor at the arithmetic average temperature and arithmetic average pressure

*F* = Moody friction factor at arithmetic average temperature and pressure.

*L* = Length of flow string, *ft*

*Z*= vertical distance of reservoir from surface, *ft*

*q*= gas flow rate, MMscfd at 14.65 psia and 60 °F

*D*= flow string diameter, in

If Fanning friction factor is used, use the following equation.

<u>100𝛾𝑔𝑇𝑧𝑓𝐹𝐿(𝑒⁵ − 1)𝑞²</u> 𝑃𝑤𝑓 = 𝑝𝑡𝑓 𝑒 + 𝑠𝐷

## CULLANDER AND SMITH METHOD

𝑃𝑤𝑓 <u>𝑝</u> <u>𝑑𝑝</u> <u>𝑇𝑧</u> ∫ 2 𝑃𝑡𝑓<u>𝑃 6.67𝑋10</u> −4 <u>𝑓𝑞²𝑔</u> () 𝑐𝑜𝑠𝜃 + 5 𝑇𝑧 𝑑 <u>(𝐼𝑚𝑝 + 𝐼𝑡𝑓) (𝐼𝑤𝑓 + 𝐼𝑡𝑓)</u> = (𝑃𝑚𝑝 + 𝑃𝑡𝑓) + (𝑃𝑤𝑓 − 𝑃𝑚𝑝) 2 2

Calculate the quantity on the right side of the equation defined as α. Α=0.01875ˠg L

Calculate the gas viscosity. Evaluate gas viscosity at flowing wellhead and temperature

Calculate Reynolds number

Calculate f by depending on Reynolds number

Calculate the friction factor

Calculate the integrand, I at the wellhead and temperature and pressure conditions Itf

Calculate the midpoint pressure P𝑚𝑝.

Compute P𝑤𝑓 of the production string

Use Simpson’s rule to obtain more accurate value of P𝑤𝑓

## AVERAGE TEMPERATURE AND DEVIATION METHOD

5 2 <u>25𝛾𝑔𝑇𝑧𝑓𝐿(𝑒 − 1)𝑞</u> 2 2 5 𝑃𝑤𝑓 = 𝑃𝑡𝑓 𝑒 + 𝑠𝐷⁵

Assume Pwf

Find average pressure

Calculate Ppr

Find average temperature

Calculate Tpr

Find z

Find viscosity

Calculate Reynolds number

From moody friction chart/ by applying Jain, determine f

Calculate Pwf by using formula

## CHAPTER 3 METHODOLOGY

## 3.1 RESEARCH METHODOLOGY

The methodology of the research is explained in the following flow chart. This methodology explains the flow of the research for the whole project duration In other words, this methodology will be the guideline, to ensure the research to be executed in a manageable approach in term of time, cost, and feasibility of the research itself.

## 3.2 PROJECT ACTIVITIES

Selecting the scope Finalizing the topic First research on of studies of the of FYP the topic (overall) project

|Testing the|Developing the|Detailed research on the research|
|---|---|---|
|mathematical|mathematical|based on scope of|

model model. studies

Conduct case study Finalizing the to support the mathematical theory model.

FIGURE 2: Project activities

The time given to complete the research is approximately 8 months and several steps as explained in research methodology. For a better research execution, the whole duration of the research is divided into three main phase; Early Research Development, Middle Research Development, and Final Research Development.

## 3.3 KEY MILESTONE

Below are the key milestones that need to be achieved by the author throughout the period of the research which is approximately 26 weeks.

|Milestone|Week|
|---|---|
|Early Research Development Research background Scope of studies and Assumptions|1-9|
|Middle Research Development Detailed research Developing the mathematical model Data gathering Testing the mathematical model|10-12|
|Final Research Finalizing the mathematical modelling Completing the documentation|22-26|

• •

• • • •

• •

## 3.4 GANTT CHART

|NO|DETAIL/WEEK 1 2 3 4 5 6 7 8 9 10 11 12 13 14|
|---|---|
|1|Project work continue|
|2|Project work continue|
|3|Submission of progress report|
|4|Project work continue|
|5|Project work continue|
|6|Poster exhibition|
|7|Submission of dissertation|
|8|Oral presentation|
|9|Submission of project dissertation|

## : Objective achieved.

## 3.5 RUNNING DIAGRAM

Mathematical model flow chart for calculating bottom hole flowing pressure for average temperature and deviation method

START

COLLECT WELL DATA

SELECT METHOD

INSERT DATA FOR WELL

ASSUME/INSERT PWF

CALCULATE Z

CALCULATE RE

CALCULATE SKIN

NOT SATISFIED PWF OBTAINED

SATISFIED

END

Mathematical model flow chart for calculating bottom hole flowing pressure with Cullender and Smith method.

START

COLLECT WELL DATA

INSERT DATA FOR WELL

CALCULATER RE

CALCULATE f

CALCULATE THE INTEGRAND I

CALCULATE THE Pmp

CALCULATE Pwf

USE SIMPSON’S RULE

## 3.6 MATHEMATICAL MODEL IN MS EXCEL

This project has been working on Microsoft Excel, all the necessary formulas will be inserted in Excel file as the macro function and user form. User need to add data for specific well.

In this project, a mathematical model of predicting of Bottom-hole flowing pressure of gas well is developed in Microsoft Office 2007 in the computer laboratory in Building 15 and Microsoft Office 2010 in personal laptop. In the general, the function of both versions are quite same, they have a bit difference in the interface and option menu

FIGURE 3: Microsoft Excel 2007 versus Microsoft Excel 201

In the first, author need to activate Developer Tool.

FIGURE 4: Developer Tab

In the developer tab, there are showed Visual Basic and Macros

FIGURE 5: Visual Basic Window

FIGURE 6: Macros Windows

In the visual basic window, author has written code to create macros function. An in macro window, all functions have been created will show there.

FIGURE 7: User form in Visual Basic for Application Window

In user form, author assigned function in the buttons for calculation function.

## 3.7 WORKFLOW SUMMARY

||MODEL|
|---|---|
|START LITERATURE REVIEW AND DATA GATHERING|COMPARISON AND STOP ANALYSIS CODING DESIGN|
|INCORPORATE DATA|MANUAL CALCULATION FOR DATA VALIDATION|

FIGURE 8: Workflow summary

## CHAPTER 4

## RESULTS AND DISCUSSION

## RESULTS 4.1 DATA AVAILABILITY

Table below shows the hypothetical reservoir and well data taken from SPE website and research papers. This data was used for the same purpose that is to predicting the bottom- hole flowing pressure of a gas well.

|Well no|Well name|Depth|Gas gravity|Length of tubing|Flow rate|Flowing pressure|Tubing temperature|Flowing well temperature|Diameter|
|---|---|---|---|---|---|---|---|---|---|
|1|A13|5790|0.60|5700|5.153|2222|89|180|1.9956|
|2|A27|5840|0.63|5750|5.181|2204|85|184|1.9551|
|3|B37|6000|0.70|5910|5.954|2206|87|190|1.7586|
|4|B25|5900|0.69|5810|5.966|2171|93|196|1.7002|
|5|B63|6800|0.71|6710|5.450|2156|87|205|1.8076|
|6|C18|7400|0.73|7320|5.838|2159|90|220|1.6516|
|7|C19|8000|0.74|7930|5.835|2196|87|224|1.9197|
|8|D23|8400|0.68|8300|5.354|2127|93|190|1.5507|
|9|D40|6200|0.67|6110|6.094|2176|88|187|1.7653|

## 4.2 MANUAL CALCULATION

Method: **Average temperature and deviation method**

## Data given:

|g = 0.65 g|T𝑤𝑓= 216 °F|
|---|---|
|P𝑝𝑐=667 psia|L = 6818 ft|
|T𝑝𝑐=366 °R|ℯ= 0.0023|
|P𝑡𝑓=2175 psia T𝑡𝑓=118 °F q = 6300 Mscfd g|d= 2.441 inch|

Steps:

1) Assume a value of bottom-hole flowing pressure (P𝑤𝑓).
2) Compute the arithmetic pressure and temperature averages ad calculate 𝑧 factor and viscosity.

|T= 627 R|Tpr=1.71|
|---|---|
|P= 2361 psia|Z=0.865|
|Ppr= 3.54|µg= 0.017 cp|

3) Calculate Reynolds number
<u>20 ∗ 0.65 ∗ 6300</u> 𝑁𝑟𝑒 = = 1974000

0.017 ∗ 2.441

So that’s means it’s a turbulent flow.

4) Calculate friction factor (𝑓)
−2

<u>0.0023 21.25</u>
𝑓 = 4 {2.28 − 4 log [ +

0.9]} = 0.0196
0.017 1974000
5) Compute (P𝑤𝑓) using the equation.
<u>0.0375(0.65)(6818)</u>
𝑠 = = 0.31

0.865 ∗ 627

||2|2|2|
|---|---|---|---|
|2 0.31|||0.31|
||5|||

<u>6.67 ∗ 10</u> −4
<u>(0.0196)(6300)(627)(0.865)</u> 𝑝𝑤𝑓 = √2175 ℯ + (ℯ − 1)

2.441 ∗ cos(0°)
=2565 psia

6) Compare the calculated Pwf against the guess Pwf
<u>2546 − 2656</u> 𝑒𝑟𝑟𝑜𝑟 = ∗ 100 = 4% 2546

7) Repeat the same iteration (steps 2-5) for the following average pressure.
<u>(2656 + 2175)</u> 𝑃 = = 2415 𝑝𝑠𝑖 2 Pwf = 2656 Error < 1%

Method: **Cullender and smith method** Data given:

|g = 0.65 g|T𝑤𝑓= 216 °F|
|---|---|
|P𝑝𝑐=667 psia|L = 6818 ft|
|T𝑝𝑐=366 °R|ℯ = 0.0023|
|P𝑡𝑓=2175 psia T𝑡𝑓=118 °F q = 6300 Mscfd g|d= 2.441 inch|

|𝑃𝑤𝑓|||𝑇𝑧 𝑝𝑑𝑝||
|---|---|---|---|---|
|𝑃𝑡𝑓|𝑝 (𝑇𝑧)|2 𝑐𝑜𝑠|6.67×10−4𝑓𝑞2 +|𝑑 5|

## ∫ = 0.01875ggL

1) Calculate the quatity on the right side of the equation defined as α. α=0.0187ggL = (0.01875)(0.65)(6818)= 83.09
2) Calculate the friction factor, W
a) Evaluate the gas viscosity. µg=0.0162
b) Calculate the Reynolds number, Nre
<u>20gq</u> 𝑁𝑟𝑒 = µ𝑔𝐷 <u>(20)(0.65)(6300)</u> = =2071100 (0.0162)(2441)

c) Calculate f.
−2

<u>0.0023 21.25</u>
𝑓 = 4 [2.28 − 4 log ( +

0.9 )] = 0.0195
2.441 2071100
d) The friction factor term is
<u>6.67 × 1𝑜</u> −4
<u>𝑓𝑞²</u> W = 𝑑

−4 2

<u>6.67×1𝑜 (0,0195)(6300)</u>
= (2.441)5 =5.95

3) Evaluate Itf using the pseudo reduced wellhead pressure and temperature and the z factor. Ppr, tf = 3.26, Tpr, tf =1.58, and ztf = 0.815.
<u>𝑝</u>

||𝑇𝑧|
|---|---|
|(𝑇𝑧 𝑝)|𝑍 𝐿 + W|

𝐼 = 2

Itf = 1.58

4) Compute the midpoint pressure pressure. Pmp, of the production string. For this initial estimate, assume Imp = Itf.
𝛼 83.09 𝑃𝑚𝑝 = 𝑃𝑡𝑓 + = 2175 + = 2421 𝑝𝑠𝑖𝑎 𝐼𝑚𝑝 + 𝐼𝑡𝑓 0.169 + 0.619 Second iteration, Using Pmp = 2421 psia and W=5.99, we calculate the Imp = 0.172. Then, 𝛼 83.09 𝑃𝑚𝑝 = 𝑃𝑡𝑓 + = 2175 + = 2419 𝑝𝑠𝑖𝑎 𝐼𝑚𝑝 + 𝐼𝑡𝑓 0.172 + 0.169 The latest Pmp agrees with initial value, so we have converged to Pmp=2419 psia.

5) Compute the BHFP, Pwf. Assume Iwf = Imp
𝛼 83.09 𝑃𝑤𝑓 = 𝑃𝑚𝑝 + = 2419 + = 2661 𝑝𝑠𝑖𝑎 𝐼𝑤𝑓 + 𝐼𝑚𝑝 0.172 + 0.172 Second iteration,

<u>83.09</u>
= 2419 + = 2661 𝑝𝑠𝑖𝑎

0.175 + 0.172
Thus, Pwf = 2658 psia

6) Use simpson’s rule to obtain more accurate estimate of BHFP.
<u>6𝛼 6(83.09)</u> 𝑃𝑤𝑓 = 𝑃𝑡𝑓 + = 2175 + 𝐼𝑡𝑓 + 4𝐼𝑚𝑓 + 𝐼𝑤𝑓 0.169 + 4(0.172) + 0.175 = 2658 psia.

## 4.3 RESULTS FROM THE MATHEMATICAL MODELLING IN THE VBA <u>For Cullender and Smith method</u>

The view when we open the spreadsheet for the Cullender- Smith method.

||Flowing Bottom-hole flowing pressure|||||
|---|---|---|---|---|---|
|Description:|with Cullender-Smith method.||This spreadsheet calculates bottom hole pressure|||
|Instructions:|Step 2: Click "Solution" button to get results.|Step 1: Input your data in the "Input Data" section.||||
|Input Data:||||||
|= g|0.65|||||
|d =|2.441 0.0009|in||||
|L =|6818 0|ft Deg||||
|p = hf|2175|psia||||
|T = hf|118|o F||||
|T = wf|216|o F||||
|q = msc|6.3 Pwf=|MMscf/d 2662||||
|f =|0.019133|||||
|Depth (ft)|o T (R)|p (psia)|Z|p/ZT|I|
|0|578|2175|0.7934|4.74272|167.383|

|3409|627|2421|0.8429|4.58011|170.782|
|---|---|---|---|---|---|
|6818|676|2662|0.8866|4.44159|173.711|

The instructions for this excel is put at the top of the document

## Insert all the parameters

Table to calculate the *z* factor and *f* factor.

Before we find the *z*, we must put in the objective function so that *z* factor can be found

Click the bottom-hole flowing pressure button Solution. The results of the process will appear in the results box.

The results of the Bottom-hole flowing pressure of the gas well calculated using the mathematical model from the data given is 2662 psia, whereas the pressure that calculated manually is 2658 psia. The difference between those two pressures is just 4 psia.

In the Microsoft excel, certain formula had been generated, there are;

TABLE 1: Formula generated for Cullender and Smith method.

|Column|Row|Formula|
|---|---|---|
|I|6|=677+15*B4-37.5*B4^2|
|1|7|=168+325*B4-12.5*B4^2|
|C|21|=(1/(1.74-2*LOG(2*B6)))^2|
|A|26|=B7/4|
|A|27|=B7/2|
|A|28|=B7*3/4|
|A|29|B7|
|B|25|=B$9+(B$10-B$9)/B$7*A25+460|
|B|26|=B$9+(B$10-B$9)/B$7*A26+460|
|B|27|=B$9+(B$10-B$9)/B$7*A27+460|
|B|28|=B$9+(B$10-B$9)/B$7*A28+460|
|B|29|=B$9+(B$10-B$9)/B$7*A29+460|
|D|25|=F35+(1-F35)/EXP(G35)+H35*D35^I35|
|D|26|=F35+(1-F36)/EXP(G36)+H36*D36^I36|
|D|27|=F37+(1-F37)/EXP(G37)+H37*D37^I37|
|D|28|=F38+(1-F38)/EXP(G38)+H38*D38^I38|
|D|29|=F39+(1-F39)/EXP(G39)+H39*D39^I39|
|E|25|=C25/D25/B25|
|E|26|=C26/D26/B26|
|E|27|=C27/D27/B27|

|E|28|=C28/D28/B28|
|---|---|---|
|E|29|=C29/D29/B29|
|F|25|=E25/(0.001*COS(B$8/57.3)*E25^2+0.6666*|
|F|26|=E26/(0.001*COS(B$8/57.3)*E26^2+0.6666*|
|F|27|=E27/(0.001*COS(B$8/57.3)*E27^2+0.6666*|
|F|28|=E28/(0.001*COS(B$8/57.3)*E28^2+0.6666*|
|F|29|=E29/(0.001*COS(B$8/57.3)*E29^2+0.6666*|
|B|35|B25|
|B|36|B26|
|B|37|B27|
|B|38|B28|
|B|39|B27|
|C|35|C25|
|C|36|C26|
|C|37|C27|
|C|38|C28|
|C|39|C29|
|D|35|=B35/I$6|
|D|36|=B36/I$6|
|D|37|=B37/I$6|
|D|38|=B38/I$6|
|D|39|=B39/I$6|
|E|35|=B35/I$7|

|E|36|=B36/I$7|
|---|---|---|
|E|37|=B37/I$7|
|E|38|=B38/I$7|
|E|39|=B39/I$7|
|F|35|=1.39*(E35-0.92)^0.5-0.36*E35-0.101|
|F|36|=1.39*(E36-0.92)^0.5-0.36*E36-0.101|
|F|37|=1.39*(E37-0.92)^0.5-0.36*E37-0.101|
|F|38|=1.39*(E38-0.92)^0.5-0.36*E38-0.101|
|F|39|=1.39*(E39-0.92)^0.5-0.36*E39-0.101|
|G|35|=(0.62-0.23*E35)*D35+(0.066/(E35-0.86)-0.037)*D35^2+0.32/10^(9*E35- 1)*D35^6|
|G|36|=(0.62-0.23*E36)*D36+(0.066/(E36-0.86)-0.037)*D36^2+0.32/10^(9*E36- 1)*D36^6|
|G|37|=(0.62-0.23*E37)*D37+(0.066/(E37-0.86)-0.037)*D37^2+0.32/10^(9*E37- 1)*D37^6|
|G|38|=(0.62-0.23*E38)*D38+(0.066/(E38-0.86)-0.037)*D38^2+0.32/10^(9*E38- 1)*D38^6|
|G|39|=(0.62-0.23*E39)*D39+(0.066/(E39-0.86)-0.037)*D39^2+0.32/10^(9*E39- 1)*D39^6|
|H|35|=0.132-0.32*LOG(E35)|
|H|36|=0.132-0.32*LOG(E36)|
|H|37|=0.132-0.32*LOG(E37)|
|H|38|=0.132-0.32*LOG(E38)|
|H|39|=0.132-0.32*LOG(E39)|
|I|35|=10^(0.3106-0.49*E35+0.1824*E35^2)|

|I|36|=10^(0.3106-0.49*E36+0.1824*E36^2)|
|---|---|---|
|I|37|=10^(0.3106-0.49*E37+0.1824*E37^2)|
|I|38|=10^(0.3106-0.49*E38+0.1824*E38^2)|
|I|39|=10^(0.3106-0.49*E39+0.1824*E39^2)|

The model is validated by using the data from SPE paper.

TABLE 2: Well data

|Well no|Well name|Depth|Gas gravity|Length of tubing|Flow rate|Flowing pressure|Tubing temperature|Flowing well temperature|Diameter|
|---|---|---|---|---|---|---|---|---|---|
|1|A13|5790|0.60|5700|5.153|2222|89|180|1.9956|
|2|A27|5840|0.63|5750|5.181|2204|85|184|1.9551|
|3|B37|6000|0.70|5910|5.954|2206|87|190|1.7586|
|4|B25|5900|0.69|5810|5.966|2171|93|196|1.7002|
|5|B63|6800|0.71|6710|5.450|2156|87|205|1.8076|
|6|C18|7400|0.73|7320|5.838|2159|90|220|1.6516|
|7|C19|8000|0.74|7930|5.835|2196|87|224|1.9197|
|8|D23|8400|0.68|8300|5.354|2127|93|190|1.5507|
|9|D40|6200|0.67|6110|6.094|2176|88|187|1.7653|

TABLE 3: Bottom-hole flowing pressure

|Well no|Well name|Actual (psia)|Cullender and smith (psia)|
|---|---|---|---|
|1|A13|2659.10|2665|
|2|A27|2693.35|2694|
|3|B37|2955.08|2978|
|4|B25|2969.99|2981|
|5|B63|2909.30|2932|
|6|C18|3273.15|3295|
|7|C19|3074.28|3107|
|8|D23|3407.78|3421|
|9|D40|3023.65|2947|

BOTTOMHOLE FLOWING PRESSURE 4000 3500 3000 2500 2000 1500 1000 500

|0|||
|---|---|---|
||B37|B25|
||ACTUAL|CULLENDER & SMITH METHOD|

A13 A27 B63 C18 C19 D23 D40

BOTTOM-HOLE FLOWING PRESSURE 4000 3500 3000 2500 2000 1500 1000 500 0 1 2 3 4 5 6 7 8 9

||2 3|4|5|
|---|---|---|---|
||ACTUAL|CULLENDER & SMITH METHOD||

FIGURE 9: Bottom-hole flowing pressure obtained from the mathematical modelling

TABLE 4: Error calculated from the mathematical modelling

|Well name|Error|
|---|---|
|A13|0.22|
|A27|0.02|
|B37|0.77|
|B25|0.37|
|B63|0.78|
|C18|0.06|
|C19|1.06|
|D23|0.36|
|D40|2.54|

# ERROR (%)

2.5 2
1.5 1
0.5 0 A13 A27 B37 B25 B63 C18 C19 D23 D40
ERROR (%) 3

2.5 2
1.5 1
0.5 0 A13 A27 B37 B25 B63 C18 C19 D23 D40
FIGURE 10:Percentage error of Cullender and Smith method

TABLE 5: Difference between the bottom-hole flowing pressures calculated from VBA

and VB.NET

|Well name|Actual pressure (Psia)|VBA (Psia)|VB.NET (Psia)|
|---|---|---|---|
|1|2659.1|2665|2652.39|
|2|2693.35|2694|2679.52|
|3|2955.08|2978|2955.38|
|4|2969.99|2981|2958.19|
|5|2909.3|2932|2909.3|
|6|3273.15|3295|3273.14|
|7|3074.28|3107|3074.28|
|8|3407.78|3421|2297.78|
|9|3023.65|2947|2923.87|

COMPARISON BETWEEN VBA FOR MICROSOFT EXCELL AND VB.NET 4000 3500 3000 2500 2000 1500 1000 500 0 A13 A27 B37 B25 B63 C18 C19 D23 D40

|A13|A27 B37|B25 B63|C18 C19|
|---|---|---|---|
||actual pressure|VBA FOR EXCELL|VB.NET|

COMPARISON BETWEEN VBA FOR MICROSOFT EXCELL AND VB.NET 4000 3500 3000 2500 2000 1500 1000 500 0 0 1 2 3 4 5 6 7 8 9 10

|0|2|4 5|7|8|
|---|---|---|---|---|
||actual pressure|VBA FOR EXCELL|VB.NET||

FIGURE 11: Comparison of bottom-hole pressure for VBA and VB.NET

TABLE 6: Error of bottom-hole flowing pressure calculated by using VBA for excel

and VB.NET

|Well name|Error (%)|
|---|---|
|A13|0.47|
|A27|0.53|
|B37|0.76|
|B25|0.77|
|B63|0.77|
|C18|0.66|
|C19|1.05|
|D23|0.68|
|D40|0.79|

ERROR (%)

1.2 1
0.8
0.6
0.4
0.2 0 A13 A27 B37 B25 B63 C18 C19 D23 D40
## ERROR (%)

1.2 1
0.8
0.6
0.4
0.2 0 A13 A27 B37 B25 B63 C18 C19 D23 D40
FIGURE 12: Error of bottom-hole flowing pressure calculated by using VBA for excel

and VB.NET The flowing bottom hole pressure estimated using Visual Basic for Application in Microsoft Excel for each of the wells whose data were presented in table are tabulated in table along with the actual flowing bottom hole pressure. A comparison plot for Cullender and Smith method with the actual is as shown in the multiple bar chart of Figure. From the chart and graph, and the results obtained, it is observed that the result obtained shows that apart from a few well Cullender and Smith method gave results that are very close to the actual data.

## <u>FOR AVERAGE TEMPERATURE AND DEVIATION METHOD</u>

The view when we open the excel,

First of all, the user need to insert the data obtained in the parameters table. Make sure the unit is correct.

|Parameters|||
|---|---|---|
|Specific gravity|0.65||
|Diameter|3|in|
|Relative roughness|0.0002||
|Length of tubing|4000|ft|
|Tube head pressure|2000|psia|
|Tube head temperature|95|F|
|Bottomhole temperature|150|F|
|Flowrate|2|MMscf/d|
|z-compressibility factor|0.0000||
|density|1.5||
|velocity|56||
|viscosity|1.5||

The column for the intermediate calculations, to calculate f and z.

|Intermediate Calculations||||
|---|---|---|---|
|Friction|f = o T (R)|0.013725 p (psia)|Z|
||555|2000|0.9209|

The f and z will be obtained by putting the objective function. Objective Function 555 2000 0.827239 1.484081 0.408695 0.277571 0.077133545 0.966353

## Calculate Reynolds number and skin factor

Reynolds Number 168

Skin 0.000199

Results Bottomhole flowing pressure (psia) 4000796

Click on the button and the results will be appear;

The results for this modelling not accurate compared to the Cullander and Smith method. The manual calculation result and the mathematical modelling result are very far awak from each other.

In the Microsoft excel, certain formula had been generated, there are;

TABLE 7: Formula generated for Average Temperature and Deviation method

|Column|Row|Formula|
|---|---|---|
|B|35|=B25|
|C|35|=C25|
|D|35|=B35/I$6|
|E|35|=B35/I$7|
|F|35|=1.39*(E35-0.92)^0.5-0.36*E35-0.101|
|G|35|=(0.62-0.23*E35)*D35+(0.066/(E35-0.86)-0.037)*D35^2+0.32/10^(9*E35-1)*D35^6|
|H|35|=0.132-0.32*LOG(E35)|
|I|35|=10^(0.3106-0.49*E35+0.1824*E35^2)|
|I|6|=677+15*B4-37.5*B4^2|
|I|7|=168+325*B4-12.5*B4^2|

The following well data were collected and used to validate the program. These data are presented in table.

TABLE 8: Well data

|Well no|Well name|Depth|Gas gravity|Length of tubing|Flow rate|Flowing pressure|Tubing temperature|Flowing well temperature|diameter|
|---|---|---|---|---|---|---|---|---|---|
|1|A13|5790|0.60|5700|5.153|2222|89|180|1.9956|
|2|A27|5840|0.63|5750|5.181|2204|85|184|1.9551|
|3|B37|6000|0.70|5910|5.954|2206|87|190|1.7586|
|4|B25|5900|0.69|5810|5.966|2171|93|196|1.7002|

|5|B63|6800|0.71|6710|5.450|2156|87|205|1.8076|
|---|---|---|---|---|---|---|---|---|---|
|6|C18|7400|0.73|7320|5.838|2159|90|220|1.6516|
|7|C19|8000|0.74|7930|5.835|2196|87|224|1.9197|
|8|D23|8400|0.68|8300|5.354|2127|93|190|1.5507|
|9|D40|6200|0.67|6110|6.094|2176|88|187|1.7653|

TABLE 9: Bottom-hole flowing pressure from Average Temperature and deviation method.

|Well no|Well name|Actual|Average temperature|
|---|---|---|---|
|1|A13|2659.10|2477.75|
|2|A27|2693.35|2478.34|
|3|B37|2955.08|2515.80|
|4|B25|2969.99|2467|
|5|B63|2909.30|2503.58|
|6|C18|3273.15|2547|
|7|C19|3074.28|2632|
|8|D23|3407.78|2542.08|
|9|D40|3023.65|2478.33|

||||BOTTOM-HOLE FLOWING PRESSURE|
|---|---|---|---|
|A27|B37|B25|B63 C18 C19 D23 D40|
||Actual||Average temperature|

4000 3500 3000 2500 2000 1500 1000 500 0 A13

|||BOTTOM-HOLE FLOWING PRESSURE|
|---|---|---|
|2|4|6 8 10|
||Actual|Average temperature|

4000 3500 3000 2500 2000 1500 1000 500 0 0

FIGURE 13: Bottom-hole flowing pressure by using Average Temperature and Deviation

method.

TABLE 10: Percentage error calculated for Average Temperature and deviation method.

|Well name|Error (%)|
|---|---|
|A13|7.3|
|A27|8.7|
|B37|17.5|
|B25|20|
|B63|16|
|C18|29|
|C19|17|
|D23|34|
|D40|22|

Error (%) 40 35 30 25 20 15 10 5 0 A13 A27 B37 B25 B63 C18 C19 D23 D40

Error (%) 40 35 30 25 20 15 10 5 0 0 2 4 6 8 10

FIGURE 14: Percentage Error for Average Temperature and deviation method.

TABLE 11: Comparison between the Bottom-hole flowing pressure obtained from VBA

and VB.NET

|Well name|Actual pressure (Psia)|VBA|VB.NET (Psia)|
|---|---|---|---|
|A13|2659.1|2477.75|2557.74|
|A27|2693.35|2478.34|2568.03|
|B37|2955.08|2515.80|2681.28|
|B25|2969.99|2467|2635.89|
|B63|2909.3|2503.58|2668.27|
|C18|3273.15|2547|2795.57|
|C19|3074.28|2632|2824.24|
|D23|3407.78|2542.08|2828.97|
|D40|3023.65|2478.33|2639.23|

COMPARISON OF Pwf OBTAINED FROM VBA AND VB.NET 4000 3500 3000 2500 2000 1500 1000 500 0 A13 A27 B37 B25 B63 C18 C19 D23 D40

||A27|B37|B63|C18|
|---|---|---|---|---|
||Actual pressure (Psia)||VBA|VB.NET (Psia)|

COMPARISON OF Pwf OBTAINED FROM VBA AND VB.NET 4000 3500 3000 2500 2000 1500 1000 500 0

|0|||
|---|---|---|
|0|2|6|
||Actual pressure (Psia)|VBA|

4 8 10 VB.NET (Psia)

FIGURE 15: Comparison between the Bottom-hole flowing pressures obtained from

VBA and VB.NET

TABLE 12: Percentage error for VBA and VBA.NET

|Well name|Error (%)|
|---|---|
|A13|3.13|
|A27|3.5|
|B37|6.17|
|B25|6.4|
|B63|6.2|
|C18|8.9|
|C19|6.8|
|D23|10.1|
|D40|6.8|

Error (%) 12 10 8 6 4 2 0 0 2 4 6 8 10

Error (%) 12 10 8 6 4 2 0 A13 A27 B37 B25 B63 C18 C19 D23 D40

FIGURE 16: Percentage error for VBA and VB.NET

TABLE 13: COMPARISON BETWEEN THE ACTUAL PRESSURES WITH THE

CALCULATED PRESSURE

|Well name|Actual|Average Temperature|Cullender and Smith|
|---|---|---|---|
|A13|2659.1|2477.75|2665|
|A27|2693.35|2478.34|2694|
|B37|2955.08|2515.8|2978|
|B25|2969.99|2467|2981|
|B63|2909.3|2503.58|2932|
|C18|3273.15|2547|3295|
|C19|3074.28|2632|3107|
|D23|3407.78|2542.08|3421|
|D40|3023.65|2478.33|2947|

4000 3500 3000 2500 2000 1500 1000 500 0 0 2 4 6 8 10 Actual Average temperature Cullender and smith

4000 3500 3000 2500 2000 1500 1000 500 0 A13 A27 B37 B25 B63 C18 C19 D23 D40

||A27|B37|C18|
|---|---|---|---|
||Actual|Average temperature|Cullender and smith|

FIGURE 17: Comparison between the actual pressures with the calculated pressures.

## 4.4 USER MANUAL FOR CALCULATING THE BOTTOMHOLE FLOWING

## PRESSURE FOR BOTH METHO

USER MANUAL

1) CHOOSE THE METHOD THAT YOU WANT TO USE
2) INSERT ALL REQUIRED DATA IN THE TABLE
3) MAKE SURE ALL THE DATA INSERTED IS IN THE CORRECT UNIT
4) ASSUME BOTTOMHOLE FLOWING PRESSURE
5) CLICK ON THE BOTTOM-HOLE FLOWING PRESSURE BUTTON TO CALCULATE THE FLOWING BOTTOM-HOLE PRESSURE

## 4 4 DISCUSSION

The aim of this project is to develop a mathematical model for predicting the bottom hole flowing pressure for gas well. Cullender and Smith method and Average temperature and deviation method has been used. Based on the results it can be conclude that the mathematical modelling that have been made is quite accurate..

From the table of the bottom-hole flowing pressure using Cullender and Smith method, the value of the pressure obtained from the modelling is very near to the actual pressure at the well. All nine wells that had been tested show a very good result. Compare to the Average Temperature and deviation method, the value for the pressure obtained is quite far and not accurate. It must be because the modelling is not correct. The coding and the flow of the steps in the Average temperature and deviation method might be wrong somewhere and must be improved.

As we can see from the table of results for the Cullender and Smith method, the error of the method from the actual pressure and calculate manually pressure is very small. The highest error for this method is 2.54 % and the lowest error for this method is 0.02%. For Average Temperature and deviation method, the error of the bottom-hole flowing pressure obtained is quite high. As stated in the table of percentage error, the highest error is 34% and the lowest error is 7.3%. the error is calculated by using;

<u>𝑃𝑐𝑎𝑙𝑐𝑢𝑙𝑎𝑡𝑒 − 𝑃𝑚𝑒𝑎𝑠𝑢𝑟𝑒𝑑</u> 𝐸𝑟𝑟𝑜𝑟: × 100% 𝑃𝑚𝑒𝑎𝑠𝑢𝑟𝑒𝑑

As we compared the results obtained from the mathematical model created with the results obtained from other computer program which is VB.NET. For Cullender and Smith method, all well are quite accurate in VBA. For VB.NET at the well D23, the value is far from other well. As shown in the figure of error, the highest error is at C19.

<u>𝑃𝑣𝑏𝑎 − 𝑃𝑣𝑏. 𝑛𝑒𝑡</u> 𝐸𝑟𝑟𝑜𝑟: × 100% 𝑃𝑣𝑏. 𝑛𝑒𝑡

In the table comparison between the actual pressures with calculated pressures. The average temperature method value is very far compare to the Cullender and Smith method. Most of the well are on the same value as actual value for Cullender and Smith method whereas for Average temperature and deviation method all the value are far from actual. Besides that the value is quite low. Some of the reasons responsible for the difference in results obtained include the program requires gas viscosity and the Carr et al chart was regressed and the equation obtained from Microsoft Excel were used in the program. Also, the friction factor is required in each iteration and hence a correlation was used to determine the friction factor. This is another reason why there exist a variance in the results obtained. The z factor was calculated in each iteration from the Gopal equation. This also added variance in the results. A hypothesis test was eared out and the results obtained confirm the following.

## CHAPTER 5

## CONCLUSION AND RECOMMENDATIONS

## 5.1 CONCLUSION

It has been shown in the foregoing that an easy to handle calculation method of reliable calculation method of reliable accuracy can be developed for calculating bottom-hole pressures of gas wells by using the mathematical modelling by using VBA. All methods of calculating bottom-hole pressure in gas involve a trial and error procedure. Not all the methods will produce the accurate results. The Cullender and Smith method will produce the most accurate result with the lowest error if we compare the flowing bottom-hole flowing pressure of a gas well using the VBA and VBA.NET.

Based on the work carried out, the following conclusions are made computer programs help to simplify complex iterations. Mathematical modelling by using VBA produces a more accurate method of calculating bottom-hole flowing pressure of gas well. The error of calculated and measured pressure is not quite difference. Cullender and Smith method is having the best result.Results obtained from computer programs could be improved if they are well validated.Visual Basic for Applications makes programming interesting because of its window-like interfaces. With very good programs and accurate well data bottom hole flowing pressure can be estimated with high degree of certainty and accuracy from surface measurements. Estimation of down-hole parameters from surface measurements could help to save dollars spent doing down-hole measurement directly. By taking continuous results, computer program can be used to perform gas well testing.

Application of the simple mathematical modelling developed for the given conditions of a given field, or group of wells offers the following advantages.

a) There is no need for the bottom-hole to be calculated by using relatively complicated pressure drop computation method.
b) The simple relationship requires manual calculation or, at most use of a pocket calculator, whereas a computer is needed with the conventional methods.
As a conclusion to this project, the objectives to develop a mathematical modelling for predicting the bottom-hole flowing pressure of a gas well is achieved. Although there is some lack and error but it can be improvise more in the future.

## 5.2 RECOMMENDATIONS

Due to the some problems and error encounter in the results, the following recommendations are made. The first recommendations is numerical integration using Simpson’s and Gaussian quadrature should be carried out to improve the accuracy of Cullender and Smith method. The error of result obtained from this mathematical model will be minimized for the future. Digital discretisation should be carried out during chart regression to improve the value read from charts. This is one of the way to improve the accuracy of the result so that this mathematical model will be used in the industry to help the workers to calculate the bottom-hole flowing pressure of a gas well with a very easy way and cost reducing.

**REFERENCES**

1. Amanat Chaundry. (2003). Computing Flowing Bottom-Hole Pressure from Wellhead Pressure
2. *A. Khalid. Calculation of Bottom-Hole Pressure in Gas Wells.*
*3.* Aziz, K.: "Calculation of Bottom-Hole Pressure in Gas Wells." J. Petro Techn. 7 (1967) 897-9.
4. A. Hasan, C. Kabir. Heat transfer during two phase flow in wellbores: Part1 formation temperature. Society of Petroleum Engineers of AIME 22866, 1991: 469–487.
*5.* Cullender, M.H., Smith, R.V.: "Practical Solution of Gas-Flow Equations for Wells and Pipelines with Large Temperature Gradients." Trans. AIME 207 (1956). 281- 7.
6. Chi U. Ikoku. ( 1992) Natural Gas Production Engineering. Krieger Publication Company.
*7.* Dranchuk, P.M., Quon, D.: "A General Solution of the Equations Describing Steady State Turbulent Compressible Flow 10. in Circular Conduits." J. Can. Petro Techn. 2 (1964). 60-5.
*8.* Dranchuk, P.M., McFarland, J. D.: "The 11. Effect of the Time Rate of Change of Momentum on Bottom-Hole Pressure in Flowing Gas Wells." J. Can. Pet. Techn. 3 (1974). 34-8.
*9.* Duns, H., Ros, N. O. D.: "vertical Flow of Gas and Liquid Mixtures in Wells." 6th World Petroleum Congress Frankfurt 1963
10. G. Takacs and C.G. Guffey, Texas Tech U. (1989). Prediction of Bottom hole Pressures in Gas Well. *SPE.*
*11.* Govier, G.W., Fogarasi, and M.: Drop in Wells Producing Condensate." J. Can. Petro (1975) 28-41. "Pressure Gas and Techn. 4
12. John Lee and Wattenbarger. R. A. “Gas Reservoir Engineering” vol 5. Pp. 58-
66.
13. K. Aziz. Calculation of bottom-hole pressure in gas wells. Journal of Petroleum Technology, 1967, 19(7): 897–899

*14.* Korn, G.A., Korn, T.M.: Mathematical Handbook for Scientists and Engineers. 2nd Ed. McGraw-Hill Book Co. 1965.
*15.* K. Aziz. Calculation of bottom-hole pressure in gas wells. Journal of Petroleum Technology, 1967, 19(7): 897–899.
*16.* K. Hall, L. Yarborough. How to solve equation of state for Z-factors. Oil and Gas J, 1974, 72(7): 86-88.
*17.* K. Shiu, H. Beggs. Predicting temperatures in flowing oil wells. Journal Energy Resource Tech. Trans., AIME, 1980, 102(1): 2–11.
*18.* M. Standing, D. Katz. Density of natural gases. Trans., AIME, 1942, (46): 140–
149. [18] G. Takacs, C. Guffey. Prediction of flowing bottomhole pressures in gas wells. Society of Petroleum Engineers of AIME 19107, 1989: 503–512.
*19.* M. Cullender, R. Smith. Practical solution of gas flow equation for wells and Pipelines with large temperature gradient. Trans., AIME, 1956, 205: 281–2871.
20. Messer, P.H., R. Raghavan, and H.J. Ramsy, Jr. “Calculation of Bottom-hole pressures for Deep, Hot, Sour Gas Wells. Journal OF Petroleum Technology, pp. 85-92, January 1974.
*21.* M. Rzasa, Katz. Calculation of Static Pressure Gradients in Gas Wells. Trans., AIME, 1945.
*22.* N. Borislav. Test diversity. Information and Software Technology, 2006, (48): 1083-1094.
*23.* Sawyer, D.N., Cobb, W.M., Stalkup, F.I., Braun, P.H.: "Factorial Design Analysis of the Wet Combustion Drive." SPE Preprint No. 4140 (1972).
24. Sukkar, Y. K., and D. Cornell “Direct Calculation of Bottom-hole Pressures in Natural Gas Wells.” Trans. AIME 204, pp. 43-8, 1955.
25. S. N. Zakirov and Kolbikov (1982). Mathematical Modelling of Gas Field Development and Production Optimization. *SPE.*
*26.* World Journal of Modelling and Simulation, Vol. 4 (2008) No. 3, pp. 172-181 181
*27.* W. Mao, Z. Liang. New Method of Calculating Wellbore Temperature in Gas Wells. Journal of Southwest Petroleum Institute, 1999, 21(1): 56–58. (in Chinese)

*28.* Young, K.L.: "Effect of Assumptions Used to Calculate Bottom-Hole Pressures in Gas Wells." J. Petro Techn. 4 (1967) 547-50.

## APPENDIX

FIGURE 18 : A logic flow chart for programming this method in digital computer

## <u>Coding for average deviation and temperature method</u>

Private Sub CommandButton1_ Click() Sheet1.Cells (17, 8) = "Reynolds Number"

SG = Val(Sheet1.Cells(4, 2)) D = Val(Sheet1.Cells(5, 2)) E = Val(Sheet1.Cells(6, 2)) L = Val(Sheet1.Cells(7, 2)) Pt = Val(Sheet1.Cells(8, 2)) Tt = Val(Sheet1.Cells(9, 2)) Tf = Val(Sheet1.Cells(10, 2)) Q = Val(Sheet1.Cells(11, 2)) z = Val(Sheet1.Cells(12, 2)) rho = Val(Sheet1.Cells(13, 2)) vel = Val(Sheet1.Cells(14, 2)) vis = Val(Sheet1.Cells(15, 2))

re = (rho * vel * D) / vis Sheet1.Cells(17, 9) = re

S = (2 * SG * z) / (53.34 * ((Tt + Tf) / 2) * z) Sheet1.Cells(19, 9) = S

Pwf = Pt ^ 2 * Exp(S) + ((25 * SG * ((Tf + Tt) / 2) * z * f * L * (Exp(S) - 1) * Q ^ 2) / (S * D ^ 5)) Sheet1.Cells(11, 15) = Pwf

End Sub

## <u>Coding for Cullender and Smith method</u>

Sub Solution() ' Solution Macro ' Macro recorded 9/7/2013 by zilah ' ' Keyboard Shortcut: Ctrl+Shift+S ' Range("G23").Select Range("G23").GoalSeek Goal:=0, ChangingCell:=Range("C23") Range("G24").Select Range("G24").GoalSeek Goal:=0, ChangingCell:=Range("C24") Range("c24").Select End Sub

Private Sub CommandButton1_Click() Sheet1.Cells(17, 8) = "Reynolds Number"

SG = Val(Sheet1.Cells(4, 2)) D = Val(Sheet1.Cells(5, 2)) E = Val(Sheet1.Cells(6, 2)) L = Val(Sheet1.Cells(7, 2)) Pt = Val(Sheet1.Cells(8, 2)) Tt = Val(Sheet1.Cells(9, 2)) Tf = Val(Sheet1.Cells(10, 2)) Q = Val(Sheet1.Cells(11, 2)) z = Val(Sheet1.Cells(12, 2)) rho = Val(Sheet1.Cells(13, 2)) vel = Val(Sheet1.Cells(14, 2)) vis = Val(Sheet1.Cells(15, 2))

re = (rho * vel * D) / vis Sheet1.Cells(17, 9) = re

S = (2 * SG * z) / (53.34 * ((Tt + Tf) / 2) * z) Sheet1.Cells(19, 9) = S

Pwf = Pt ^ 2 * Exp(S) + ((25 * SG * ((Tf + Tt) / 2) * z * f * L * (Exp(S) - 1) * Q ^ 2) / (S * D ^ 5)) Sheet1.Cells(11, 15) = Pwf

End Sub

## Appendix

## Z-compressibility factor chart

## Moody fraction chart

