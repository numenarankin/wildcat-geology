<!-- Source: phdwin-arps-equations-rate-time.pdf -->
<!-- Converted: mistral-ocr-latest -->

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

Calculation of Arp's Equations for Rate Time Calculations in PHDWin™

Exponential Rate Equation

$$q = q_i e^{-Dt}$$

Where:

= Instantaneous Rate at time before or after [Volume / Unit Time]
= Initial Instantaneous Rate (time 0), [Volume / Unit Time]
= Nominal Decline, [Fraction / Unit Time]
= Time in units consistent with Unite Time in the decline and rate.

Note: D is a fraction in this equation. A percentage must be converted to a fraction by dividing by 100. Time is usually in years and fractional years because usually in volume per year.

Note: Nominal decline ( D ) with units of volume per year can be converted to a decline with units of volume per month by dividing by 12. This is because the decline is a nominal decline.

TRC CONSULTANTS, LC

Exponential Rate Equation

1

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

Hyperbolic Rate Equation

$$q = q_{i} (1 + b D_{i} t)^{-1/b}$$

Where:

$q$ = Instantaneous Rate at time before or after $q_{i}$ [Volume / Unit Time]

$q_{i}$ = Initial Instantaneous Rate (time 0), [Volume / Unit Time]

$D_{i}$ = Initial Nominal Decline, [Fraction / Unit Time]

$b$ = Hyperbolic Exponent factor (some authors use the term "n")

$t$ = Time in units consistent with Unite Time in the decline and rate.

Note: Any set of units can be used as long as $D_{i}$ times $t$ is dimensionless.

Note: Commonly accepted theoretical $b$ values for single porosity reservoirs with good drive energy usually range between 0 and 1. Reservoirs with duel porosity, multi-porosity, fracture stimulated or poor reservoir drive energy (i.e. only gravity drainage) will demonstrate larger $b$ factors but seldom go above 2.0 or 2.5.

Note: Exponential and Harmonic declines are specific types of hyperbolic declines where the $b$ factor is equal to 0 for exponential declines or equal to 1 for Harmonic declines.

TRC CONSULTANTS, LC

Hyperbolic Rate Equation

2

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

Effective Decline Equation

$$D_{e} = \frac{q_{i} - q}{q_{i}}$$

Where:

$D_{e}$ = Effective Decline rate, [Fraction / Unit Time]

$q_{i}$ = Initial Instantaneous Rate [Volume / Unit Time]

$q$ = Instantaneous Rate at one time period after $q_{i}$ [Volume / Unit Time]

Note: Effective Decline is the most intuitive decline measurement. Unlike Nominal decline, it can be read directly from a graph.

Note: The most common unit time period used to value $D_{e}$ is one year. If no time period is stated, a yearly rate is usually implied. The Effective Decline rate ($D_{e}$) is based on the Tangent line at the time of $q_{i}$ for Hyperbolic projections. $D_{e}$ is a fraction in this equation. A percentage must be converted to a fraction by dividing by 100.

Note: Effective decline ($D_{e}$) in units of volume per year can be converted to an effective decline with units of volume per month by taking the declines (as a fraction) 12 root. This is because the decline is an effective decline.

TRC CONSULTANTS, LC

Effective Decline Equation

3

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

Types of Effective Decline in Hyperbolic Projections

Effective declines can be read directly from a production graph. Reviewing the "Effective Decline Equation",

$$D_{e} = \frac{q_{i} - q}{q_{i}}$$

two values are needed to calculate $D_{e}$. They are $q_{i}$ and $q$.

The value for $q_{i}$ is the initial instantaneous rate at time = 0. This rate is usually easily read from the graph but it should be remembered that this rate will be higher then a given monthly produced volume if the projection is started at the beginning of the month. This is because the initial instantaneous rate at the beginning of that month must decline throughout the month but cumulate to the produced volume of that month. The instantaneous rate at the beginning of a month will be higher then the produced monthly volume while the instantaneous rate will drop below the produced monthly volume at the end of the month.

A common simplification is to start the projection mid-month with a $q_{i}$ equal to the produced volume of that month. This simplification basically assumes that the produced volume of that month is equal to the instantaneous rate (in volume per month) at the mid point of the month. If this simplification is implemented, the $q_{i}$ is easily read from the production graph but if this projection is later moved to a case without scheduled production, integration of the decline curve will yield volumes missing for the first half of the first month. Since initial rates are usually the highest rates, significant production can be lost.

For this reason, PHDWin's curve fit algorithms "back up" the curve fit projections to the beginning of a month. This results in values of initial instantaneous rate ($q_{i}$) greater then the average rate (produced volume) for that month but will result in integrated volumes for that month approximately equal to that actually produced for that month.

Additionally, for non-exponential declines, the assumption that the monthly produced volume is equal to the instantaneous rate (in volume per month) at the mid point of the month is erroneous. As $b$ factors and declines become larger (concavity increases), the point along the decline curve where the instantaneous rate (in volume per month) equals the volume produced in that month (integrated volume for the month), moves to

TRC CONSULTANTS, LC

Types of Effective Decline in Hyperbolic

Projections

4

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

an earlier and earlier point in the month. This assumes declining projections. Inclining projections move toward the end of the month.

The second value needed to calculate $D_e$ is a second rate, $q$. Two theoretically possible values for this second rate ($q$) are commonly discussed. They are based on either a line tangent to the projection at the point of $q_i$ (Tangent method) OR the actual production or rate projection along the projection (Secant method).

For simplicity of calculation, this second rate is usually the rate after one time period (usually one year) of production. Since decline rates are usually reported as annual decline rates, no conversion is needed if the second rate is exactly one year after time = 0.

To pick $q$ using the Tangent method, a line is drawn tangent to the curve at $q_i$.

$q$ is then the value on the tangent line one time period (usually one year) beyond $q_i$. The volume and time units of $q_i$ and $q$ must be the same and the time units will define the time units of the decline.

For the Secant method, $q$ can be picked directly from the projection or historical production data. For this method $q$ is the rate value read directly from the projection one time period (usually one year) beyond $q_i$. The volume and time units of $q_i$ and $q$ must be the same and the time units will define the time units of the decline.

Much confusion exists regarding these methods but both the Tangent and Secant methods are theoretically correct. Most authors and commercial programs use the Tangent method when specifics are not noted. To minimize confusion, PHDWin supports only the more common Tangent method.

TRC CONSULTANTS, LC

Types of Effective Decline in Hyperbolic

Projections

5

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

Conversion between Effective and Nominal Declines

By substitution, the relationship between Nominal and Effective decline can be calculated for exponential declines.

For Exponential or Tangent Effective Instantaneous Decline only

$$D = - \ln(1 - D_{Tei})$$

or

$$D_{Tei} = 1 - e^{-D}$$

Where:

D = Nominal Decline, [Fraction / Unit Time]

D_Tei = Tangent Effective Instantaneous Decline rate, [Fraction / Unit Time]

For Secant Effective Instantaneous Decline only

$$D = \frac{(1 - D_{Sei})^{-b} - 1}{b}$$

Where:

D = Nominal Decline, [Fraction / Unit Time]

D_Sei = Secant Effective Instantaneous Decline rate, [Fraction / Unit Time]

Note: Unit time for D, D_Sei and D_Tei must be the same and is usually one year. D and all D_e are fractions in these equations. Percentages must be converted to fractions by dividing by 100.

TRC CONSULTANTS, LC

Conversion between Effective and Nominal

Declines

6

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

Secant Effective Decline to Tangent Effective decline Calculation

Substituting

$$D = \frac{(1 - D_{Sei})^{-b} - 1}{b}$$

Into

$$D_{Te} = 1 - e^{-D}$$

The following equation can be generated to convert Secant Effective Instantaneous Decline Rate into Tangent Effective Instantaneous Decline Rate.

$$D_{Te} = 1 - e^{-(\frac{(1 - D_{Sei})^{-b} - 1}{b})}$$

Where:

D = Nominal Decline, [Fraction / Unit Time]

DSei = Secant Effective Instantaneous Decline rate, [Fraction / Unit Time]

DTei = Tangent Effective Instantaneous Decline rate, [Fraction / Unit Time]

b = Hyperbolic Exponent factor (some authors use the term "n")

Note: Unit time for D, DSei and DTei must be the same and is usually one year. D and all De are fractions in these equations. Percentages must be converted to fractions by dividing by 100.

TRC CONSULTANTS, LC

Conversion between Effective and Nominal

Declines

7

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

Exponential Decline Cumulative Production Calculation

The exponential rate equation can be integrated with respect to time. This results in an equation that calculates the cumulative volume produced since time 0 (at time 0, $q=q_i$).

Using $D$ (Nominal Decline) $N_p = \frac{q_i - q}{D}$

Or

Using $D_e$ (Effective Decline) $N_p = \frac{q_i - q}{-\ln(1 - D_e)}$

Where:

$N_p$ = Volume produced to $q$ rate from time zero.

$q$ = Instantaneous Rate at time before or after $q_i$ [Volume / Unit Time]

$q_i$ = Initial Instantaneous Rate at time 0, [Volume / Unit Time]

$D$ = Nominal Decline, [Fraction / Unit Time]

$D_e$ = Effective Decline rate, For Exponential projections no distinction is made between Tangent or Secant Effective decline [Fraction / Unit Time]

Note: Units for unit time need to be consistent for $q$, $q_i$, $D$, and $D_e$. If units are not consistent erroneous results are calculated.

TRC CONSULTANTS, LC

Exponential Decline Cumulative Production

Calculation

8

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

Hyperbolic Decline Cumulative Production Calculation

Integrating the rate equation with respect to time generates the following formulas.

For all hyperbolic declines except harmonic (b = 1).

$$N_{p} = \frac{q_{i}^{b}}{(1-b)D_{i}}(q_{i}^{1-b} - q^{1-b})$$

Where:

$N_{p}$ = Volume produced to $q$ rate from time zero.

$q$ = Instantaneous Rate at time before or after $q_{i}$ [Volume / Unit Time]

$q_{i}$ = Initial Instantaneous Rate at time 0, [Volume / Unit Time]

$D_{i}$ = Initial Nominal Decline, [Fraction / Unit Time]

$b$ = Hyperbolic Exponent factor (some authors use the term "n")

Note: Units for unit time need to be consistent for $q$, $q_{i}$, $D$, and $D_{i}$. If units are not consistent erroneous results are calculated.

Note: A $b$ factor of 0 is exponential.

Note: $b = 1.0$ is not supported in this equation.

For harmonic (b = 1) declines only.

$$N_{p} = \frac{q_{i}}{D_{i}} \ln(\frac{q_{i}}{q})$$

Where:

$N_{p}$ = Volume produced to $q$ rate from time zero.

$q$ = Instantaneous Rate at time before or after $q_{i}$ [Volume / Unit Time]

$q_{i}$ = Initial Instantaneous Rate at time 0, [Volume / Unit Time]

$D_{i}$ = Initial Nominal Decline, [Fraction / Unit Time]

Note: Units for unit time need to be consistent for $q$, $q_{i}$, $D$, and $D_{i}$. If units are not consistent erroneous results are calculated.

TRC CONSULTANTS, LC

Hyperbolic Decline Cumulative Production

Calculation

9

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

Arp's Volume Calculations in PHDWin

Using the hyperbolic rate equation previously presented:

$$q = q_{i} (1 + b D_{i} t)^{-1/b}$$

Where:

$q$ = Instantaneous Rate at time before or after $q_{i}$ [Volume / Unit Time]

$q_{i}$ = Initial Instantaneous Rate (time 0), [Volume / Unit Time]

$D_{i}$ = Initial Nominal Decline, [Fraction / Unit Time]

$b$ = Hyperbolic Exponent factor (some authors use the term "n")

$t$ = Time in units consistent with Unite Time in the decline and rate.

the instantaneous production rate ($q$) can be calculated at any time. Commonly, this rate is calculated at the beginning of each time period of interest (i.e. monthly). Please note that the time ($t$) does not have to be an integer. If decimal values are used, months or years with varying day counts can be easily supported.

Having calculated the rate ($q$) at each time ($t$) of interest, the two hyperbolic equations previously noted can be used to calculate cumulative production at each rate ($q$) of interest.

(Continued on next page.)

TRC CONSULTANTS, LC

Arp's Volume Calculations in PHDWin

10

PHDWIN

Integrated Economics &

Decline Curve Analysis

Calculation of Arp's Equations for Rate Time

Calculations in PHDWin™

For all hyperbolic declines except harmonic (b = 1).

$$N_{p} = \frac{q_{i}^{b}}{(1-b)D_{i}}(q_{i}^{1-b} - q^{1-b})$$

For harmonic (b = 1) declines only.

$$N_{p} = \frac{q_{i}}{D_{i}} \ln(\frac{q_{i}}{q})$$

Where:

$N_{p}$ = Volume produced to $q$ rate from time zero.

$q$ = Instantaneous Rate at time before or after $q_{i}$ [Volume / Unit Time]

$q_{i}$ = Initial Instantaneous Rate at time 0, [Volume / Unit Time]

$D_{i}$ = Initial Nominal Decline, [Fraction / Unit Time]

$b$ = Hyperbolic Exponent factor (some authors use the term "n")

The difference between the cumulative production at the beginning of a time period and the end of that time period would be the volume produced within that time period. When calculating volumes during consecutive periods, the end rate of one period should be used as the starting rate of the next period. One major advantage in using cumulative volumes calculations is that rounding and truncation errors can be minimized.

TRC CONSULTANTS, LC

Arp's Volume Calculations in PHDWin

11