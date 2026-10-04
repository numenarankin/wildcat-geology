<!-- Source: petroleumoffice-arps-models -->
<!-- Converted: html2text + recovered equations -->

# Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

* * *

## Overview

Decline curve analysis (DCA) is the most widely used technique for estimating ultimate recovery and forecasting future production from oil and gas wells. The methodology assumes that historical production trends can be characterized mathematically and extrapolated into the future.

J.J. Arps published his seminal paper "Analysis of Decline Curves" in 1945 [1], establishing three fundamental decline models based on the behavior of the decline rate  $D$ D:

Model | Decline Rate Behavior | b Value  
---|---|---  
**Exponential** | Constant |  $b=0$ b=0  
**Hyperbolic** | Decreasing proportionally |  $00<b<1  
**Harmonic** | Decreasing linearly with rate |  $b=1$ b=1  
  
The Arps equations remain the industry standard for conventional reservoirs in boundary-dominated flow (BDF).

* * *

## Theory

### The Loss Ratio Concept

Arps defined the **decline rate** $D$ D as the fractional change in production rate per unit time:

$D=-\frac{1}{q}\frac{dq}{dt}$ D=−q1​dtdq​

He also defined the **loss ratio** $D^{-1}$ D−1 and observed that for many wells, the derivative of the loss ratio with respect to time was approximately constant:

$b=\frac{d}{dt}(\frac{1}{D})$ b=dtd​(D1​)

This parameter  $b$ b (sometimes called the Arps exponent or hyperbolic exponent) determines which decline model applies:

  * $b=0$ b=0: Decline rate is constant → **Exponential decline**
  * $00<b<1: Decline rate decreases with time → **Hyperbolic decline**
  * $b=1$ b=1: Special case → **Harmonic decline**


### Physical Interpretation

The value of  $b$ b relates to the drive mechanism and reservoir characteristics:

b Value | Typical Reservoir Type  
---|---  
$b≈0$ b≈0 | Strong water drive, high-pressure gas  
$b=0.3-0.5$ b=0.3−0.5 | Solution gas drive (typical)  
$b=0.4-0.5$ b=0.4−0.5 | Gas expansion drive  
$b=0.5-1.0$ b=0.5−1.0 | Gravity drainage  
$b>1$ b>1 | Transient flow (not boundary-dominated)  
  
> **Important** : Arps equations are only valid during boundary-dominated flow. Values of  $b>1$ b>1 indicate transient flow conditions where alternative models (PLE, SEPD, Duong) should be used.

* * *

## Equations

### Exponential Decline ( $b=0$ b=0)

When the decline rate  $D$ D is constant, integration of the decline rate equation yields:

$q(t)=q_{i}e^{-D_{i}t}$ q(t)=qi​e−Di​t

**Cumulative Production:**

$N_{p}(t)=\frac{q_{i}-q(t)}{D_{i}}=\frac{q_{i}}{D_{i}}(1-e^{-D_{i}t})$ Np​(t)=Di​qi​−q(t)​=Di​qi​​(1−e−Di​t)

**Time to Reach Economic Limit:**

$t_{econ}=\frac{1}{D_{i}}ln(\frac{q_{i}}{q_{econ}})$ tecon​=Di​1​ln(qecon​qi​​)

**Estimated Ultimate Recovery (EUR):**

$EUR=\frac{q_{i}-q_{econ}}{D_{i}}$ EUR=Di​qi​−qecon​​

### Hyperbolic Decline ( $00<b<1)

For a time-varying decline rate where  $b$ b is constant:

$q(t)=\frac{q_{i}}{(1+b⋅D_{i}⋅t)^{1/b}}$ q(t)=(1+b⋅Di​⋅t)1/bqi​​

**Cumulative Production:**

$N_{p}(t)=\frac{q_{i}}{(1-b)D_{i}}[1-(1+b⋅D_{i}⋅t)^{(1-1/b)}]$ Np​(t)=(1−b)Di​qi​​[1−(1+b⋅Di​⋅t)(1−1/b)]

Or equivalently:

$N_{p}(t)=\frac{q_{i}^{b}}{(1-b)D_{i}}(q_{i}^{1-b}-q(t)^{1-b})$ Np​(t)=(1−b)Di​qib​​(qi1−b​−q(t)1−b)

**Time to Reach Economic Limit:**

$t_{econ}=\frac{1}{b⋅D_{i}}[(\frac{q_{i}}{q_{econ}})^{b}-1]$ tecon​=b⋅Di​1​[(qecon​qi​​)b−1]

**EUR:**

$EUR=\frac{q_{i}^{b}}{(1-b)D_{i}}(q_{i}^{1-b}-q_{econ}^{1-b})$ EUR=(1−b)Di​qib​​(qi1−b​−qecon1−b​)

### Harmonic Decline ( $b=1$ b=1)

The harmonic decline is the limiting case of hyperbolic decline as  $b→1$ b→1:

$q(t)=\frac{q_{i}}{1+D_{i}⋅t}$ q(t)=1+Di​⋅tqi​​

**Cumulative Production:**

$N_{p}(t)=\frac{q_{i}}{D_{i}}ln(1+D_{i}⋅t)=\frac{q_{i}}{D_{i}}ln(\frac{q_{i}}{q(t)})$ Np​(t)=Di​qi​​ln(1+Di​⋅t)=Di​qi​​ln(q(t)qi​​)

**Time to Reach Economic Limit:**

$t_{econ}=\frac{1}{D_{i}}(\frac{q_{i}}{q_{econ}}-1)$ tecon​=Di​1​(qecon​qi​​−1)

**EUR:**

$EUR=\frac{q_{i}}{D_{i}}ln(\frac{q_{i}}{q_{econ}})$ EUR=Di​qi​​ln(qecon​qi​​)

> **Note** : For harmonic decline, cumulative production approaches infinity as  $t→∞$ t→∞. This is physically unrealistic for finite reservoirs, which is why harmonic decline should only be used for forecasting over finite time periods.

### Decline Curve Comparison

The following chart illustrates the three Arps decline models with  $q_{i}=1000$ qi​=1000 STB/d and  $D_{i}=0.5$ Di​=0.5/yr:

0.02.04.06.08.010.002004006008001000Time (years)Rate (STB/d)Arps Decline CurvesExponential (b=0)Hyperbolic (b=0.5)Harmonic (b=1)

* * *

## Parameter Definitions

Symbol | Description | Units  
---|---|---  
$q$ q | Production rate at time  $t$ t | STB/d, Mscf/d, or any consistent [L³/T]  
$q_{i}$ qi​ | Initial production rate | STB/d, Mscf/d, or any consistent [L³/T]  
$D_{i}$ Di​ | Initial (nominal) decline rate | 1/d, 1/month, 1/yr (must match time units)  
$b$ b | Arps hyperbolic exponent | dimensionless  
$t$ t | Time since start of decline | d, month, yr (must match decline rate units)  
$N_{p}$ Np​ | Cumulative production | STB, Mscf, or consistent [L³]  
$q_{econ}$ qecon​ | Economic limit rate | Same as  $q$ q  
$EUR$ EUR | Estimated Ultimate Recovery | Same as  $N_{p}$ Np​  
  
### Unit Consistency

The Arps equations are **unit-flexible**. The key requirement is that:

$[D_{i}]×[t]=dimensionless$ [Di​]×[t]=dimensionless

For example:

  * If  $D_{i}$ Di​ is in 1/day, then  $t$ t must be in days
  * If  $D_{i}$ Di​ is in 1/year, then  $t$ t must be in years


* * *

## Applicability and Limitations

### Valid Conditions

Arps decline curves are valid when:

  1. **Boundary-dominated flow** has been established
  2. **Operating conditions remain constant** (bottomhole pressure, completion, artificial lift)
  3. **Drainage area is fixed** (no infill drilling or recompletions)
  4. The well is producing at or near **capacity**


### Typical Parameter Ranges

Parameter | Typical Range | Notes  
---|---|---  
$b$ b | 0 - 1.0 | Values > 1 indicate transient flow  
$D_{i}$ Di​ | 5% - 95% per year | Higher for tight formations  
$q_{i}$ qi​ | Well-dependent | Must be positive  
  
### Limitations

  1. **Transient Flow** : When  $b>1$ b>1, the well is still in transient flow and Arps equations will overestimate reserves [2, 3].

  2. **Infinite EUR for Harmonic** : Harmonic decline ( $b=1$ b=1) predicts infinite cumulative production as  $t→∞$ t→∞. Use modified hyperbolic or economic limits.

  3. **Changing Conditions** : Arps assumes constant operating conditions. Significant changes in:

     * Bottomhole pressure
     * Artificial lift
     * Completion/stimulation
     * Regulatory constraints

will invalidate the forecast.

  4. **Unconventional Reservoirs** : Tight gas and shale wells exhibit extended transient flow with  $b>1$ b>1. Use modern decline models (PLE, SEPD, Duong) for these reservoirs.


* * *

## Historical Background

J.J. Arps developed his decline curve methodology while working for Shell Oil Company in the 1940s. His 1945 paper [1] in _Transactions of AIME_ introduced the mathematical framework that remains the foundation of production forecasting today.

The approach was empirical—Arps observed that production decline could be characterized by a few parameters and developed equations to describe the three main types of decline behavior. The simplicity and robustness of the Arps equations led to their widespread adoption.

Subsequent work by Fetkovich (1980) [4] provided a theoretical basis for Arps equations by linking them to material balance and flow equations, showing that:

  * Exponential decline corresponds to constant-pressure, single-phase liquid flow
  * Hyperbolic decline arises from changing pressure, two-phase flow, or layered reservoirs


* * *

## Related Topics

  * [Modified Hyperbolic Decline](https://petroleumoffice.com/doc/dca-modified-hyperbolic) \- Transition to exponential at limiting  $D$ D
  * [Power Law Exponential Decline](https://petroleumoffice.com/doc/dca-power-law-exponential) \- For tight/unconventional reservoirs
  * [Stretched Exponential Decline](https://petroleumoffice.com/doc/dca-stretched-exponential) \- Statistical physics approach
  * [Duong Decline Model](https://petroleumoffice.com/doc/dca-duong) \- Fracture-dominated unconventional flow
  * [Decline Overview](https://petroleumoffice.com/doc/dca-overview) \- Model selection guide


* * *

## References

  1. Arps, J.J. (1945). "Analysis of Decline Curves." _Transactions of AIME_ , 160, 228-247.

  2. Ali, T.A. and Sheng, J.J. (2015). "Production Decline Models: A Comparison Study." _SPE-177300-MS_ , SPE Eastern Regional Meeting, Morgantown, West Virginia, 13-15 October 2015.

  3. Lee, W.J. and Sidle, R.E. (2010). "Gas Reserves Estimation in Resource Plays." _SPE-130102_ , SPE Unconventional Gas Conference, Pittsburgh, Pennsylvania, 23-25 February 2010.

  4. Fetkovich, M.J. (1980). "Decline Curve Analysis Using Type Curves." _Journal of Petroleum Technology_ , 32(6), 1065-1077. SPE-4629-PA.

  5. Blasingame, T.A. and Rushing, J.A. (2005). "A Production-Based Method for Direct Estimation of Gas-in-Place and Reserves." _SPE-98042_ , SPE Eastern Regional Meeting, Morgantown, West Virginia, 14-16 September 2005.


**Tags:**

conventionalexponentialhyperbolicharmonicb-factorEUR
