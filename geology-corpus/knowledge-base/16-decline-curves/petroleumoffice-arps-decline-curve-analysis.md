<!-- Source: petroleumoffice-arps-decline-curve-analysis.pdf -->
<!-- Converted: mistral-ocr-latest -->

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

# PETROLEUM OFFICE

Product Guides

Theory & Background

Decline Curve Analysis

Decline Curve Analysis Overview

Ansah-Knowles-Buba (AKB) Decline Model

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

Decline Curve Statistics

Duong Decline Model for Unconventional Wells

Field Production Profiles

Modified Hyperbolic Decline Model

Power Law Exponential (PLE) Decline Model

Stretched Exponential Production Decline (SEPD) Model

Electric Submersible Pump

Equation of State

Field Production Profile

Flow Assurance

Gas Lift

Hydraulic Fracturing

Inflow Performance Relationship

Material Balance Equation

Monte Carlo Simulation

Pressure Transient Analysis

https://petroleumoffice.com/doc/dca-arps

1/10

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

PVT Properties

Rod Pump

Special Core Analysis

Surface Facilities

Utilities

Vertical Flow Performance

Help & Resources

### Get Started

Download Petroleum Office to use these features in Excel.

Download Add-in →

/ Documentation / Theory / Decline Curve Analysis /

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

## Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

### Overview

Decline curve analysis (DCA) is the most widely used technique for estimating ultimate recovery and forecasting future production from oil and gas wells. The methodology assumes that historical production trends can be characterized mathematically and extrapolated into the future.

J.J. Arps published his seminal paper "Analysis of Decline Curves" in 1945 [1], establishing three fundamental decline models based on the behavior of the decline rate \( D \):

|  Model | Decline Rate Behavior | b Value  |
| --- | --- | --- |
|  Exponential | Constant | \( b = 0 \)  |

https://petroleumoffice.com/doc/dca-arps

2/10

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

|  Model | Decline Rate Behavior | b Value  |
| --- | --- | --- |
|  Hyperbolic | Decreasing proportionally | 0 < b < 1  |
|  Harmonic | Decreasing linearly with rate | b = 1  |

The Arps equations remain the industry standard for conventional reservoirs in boundary-dominated flow (BDF).

## Theory

### The Loss Ratio Concept

Arps defined the decline rate D as the fractional change in production rate per unit time:

$$D = - \frac{1}{q} \frac{dq}{dt}$$

He also defined the loss ratio $D^{-1}$ and observed that for many wells, the derivative of the loss ratio with respect to time was approximately constant:

$$b = \frac{d}{dt} \left( \frac{1}{D} \right)$$

This parameter b (sometimes called the Arps exponent or hyperbolic exponent) determines which decline model applies:

- b = 0: Decline rate is constant → Exponential decline
- 0 < b < 1: Decline rate decreases with time → Hyperbolic decline
- b = 1: Special case → Harmonic decline

### Physical Interpretation

The value of b relates to the drive mechanism and reservoir characteristics:

https://petroleumoffice.com/doc/dca-arps

3/10

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

|  b Value | Typical Reservoir Type  |
| --- | --- |
|  b ≈ 0 | Strong water drive, high-pressure gas  |
|  b = 0.3 - 0.5 | Solution gas drive (typical)  |
|  b = 0.4 - 0.5 | Gas expansion drive  |
|  b = 0.5 - 1.0 | Gravity drainage  |
|  b > 1 | Transient flow (not boundary-dominated)  |

Important: Arps equations are only valid during boundary-dominated flow. Values of b > 1 indicate transient flow conditions where alternative models (PLE, SEPD, Duong) should be used.

## Equations

Exponential Decline (b = 0)

When the decline rate D is constant, integration of the decline rate equation yields:

$$q(t) = q_i e^{-D_i t}$$

Cumulative Production:

$$N_p(t) = \frac{q_i - q(t)}{D_i} = \frac{q_i}{D_i} \left(1 - e^{-D_i t}\right)$$

Time to Reach Economic Limit:

$$t_{econ} = \frac{1}{D_i} \ln \left(\frac{q_i}{q_{econ}}\right)$$

Estimated Ultimate Recovery (EUR):

$$EUR = \frac{q_i - q_{econ}}{D_i}$$

https://petroleumoffice.com/doc/dca-arps

4/10

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

Hyperbolic Decline (0 < b < 1)

For a time-varying decline rate where b is constant:

$$q(t) = \frac{q_i}{(1 + b \cdot D_i \cdot t)^{1/b}}$$

Cumulative Production:

$$N_p(t) = \frac{q_i}{(1 - b)D_i} \left[ 1 - (1 + b \cdot D_i \cdot t)^{(1 - 1/b)} \right]$$

Or equivalently:

$$N_p(t) = \frac{q_i^b}{(1 - b)D_i} \left( q_i^{1-b} - q(t)^{1-b} \right)$$

Time to Reach Economic Limit:

$$t_{econ} = \frac{1}{b \cdot D_i} \left[ \left( \frac{q_i}{q_{econ}} \right)^b - 1 \right]$$

EUR:

$$EUR = \frac{q_i^b}{(1 - b)D_i} \left( q_i^{1-b} - q_{econ}^{1-b} \right)$$

Harmonic Decline (b = 1)

The harmonic decline is the limiting case of hyperbolic decline as b → 1:

$$q(t) = \frac{q_i}{1 + D_i \cdot t}$$

Cumulative Production:

$$N_p(t) = \frac{q_i}{D_i} \ln(1 + D_i \cdot t) = \frac{q_i}{D_i} \ln \left( \frac{q_i}{q(t)} \right)$$

Time to Reach Economic Limit:

$$t_{econ} = \frac{1}{D_i} \left( \frac{q_i}{q_{econ}} - 1 \right)$$

EUR:

https://petroleumoffice.com/doc/dca-arps

5/10

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

$$EUR = \frac{q_i}{D_i} \ln \left( \frac{q_i}{q_{econ}} \right)$$

Note: For harmonic decline, cumulative production approaches infinity as $t \to \infty$. This is physically unrealistic for finite reservoirs, which is why harmonic decline should only be used for forecasting over finite time periods.

## Decline Curve Comparison

The following chart illustrates the three Arps decline models with $q_i = 1000$ STB/d and $D_i = 0.5$ /yr:

![img-0.jpeg](img-0.jpeg)

## Parameter Definitions

https://petroleumoffice.com/doc/dca-arps

6/10

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

|  Symbol | Description | Units  |
| --- | --- | --- |
|  q | Production rate at time t | STB/d, Mscf/d, or any consistent [L³/T]  |
|  q_{i} | Initial production rate | STB/d, Mscf/d, or any consistent [L³/T]  |
|  D_{i} | Initial (nominal) decline rate | 1/d, 1/month, 1/yr (must match time units)  |
|  b | Arps hyperbolic exponent | dimensionless  |
|  t | Time since start of decline | d, month, yr (must match decline rate units)  |
|  N_{p} | Cumulative production | STB, Mscf, or consistent [L³]  |
|  q_{econ} | Economic limit rate | Same as q  |
|  EUR | Estimated Ultimate Recovery | Same as N_{p}  |

## Unit Consistency

The Arps equations are **unit-flexible**. The key requirement is that:

$$[D_i] \times [t] = \text{dimensionless}$$

For example:

- If $D_i$ is in 1/day, then $t$ must be in days
- If $D_i$ is in 1/year, then $t$ must be in years

## Applicability and Limitations

## Valid Conditions

Arps decline curves are valid when:

https://petroleumoffice.com/doc/dca-arps

7/10

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

1. **Boundary-dominated flow** has been established
2. **Operating conditions remain constant** (bottomhole pressure, completion, artificial lift)
3. **Drainage area is fixed** (no infill drilling or recompletions)
4. The well is producing at or near **capacity**

# Typical Parameter Ranges

|  Parameter | Typical Range | Notes  |
| --- | --- | --- |
|  $b$ | 0 - 1.0 | Values > 1 indicate transient flow  |
|  $D_i$ | 5% - 95% per year | Higher for tight formations  |
|  $q_i$ | Well-dependent | Must be positive  |

# Limitations

1. **Transient Flow**: When $b > 1$, the well is still in transient flow and Arps equations will overestimate reserves [2, 3].
2. **Infinite EUR for Harmonic**: Harmonic decline ($b = 1$) predicts infinite cumulative production as $t \to \infty$. Use modified hyperbolic or economic limits.
3. **Changing Conditions**: Arps assumes constant operating conditions. Significant changes in:

- Bottomhole pressure
- Artificial lift
- Completion/stimulation
- Regulatory constraints

will invalidate the forecast.

4. **Unconventional Reservoirs**: Tight gas and shale wells exhibit extended transient flow with $b > 1$. Use modern decline models (PLE, SEPD, Duong) for these reservoirs.

https://petroleumoffice.com/doc/dca-arps

8/10

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

## Historical Background

J.J. Arps developed his decline curve methodology while working for Shell Oil Company in the 1940s. His 1945 paper [1] in Transactions of AIME introduced the mathematical framework that remains the foundation of production forecasting today.

The approach was empirical—Arps observed that production decline could be characterized by a few parameters and developed equations to describe the three main types of decline behavior. The simplicity and robustness of the Arps equations led to their widespread adoption.

Subsequent work by Fetkovich (1980) [4] provided a theoretical basis for Arps equations by linking them to material balance and flow equations, showing that:

- Exponential decline corresponds to constant-pressure, single-phase liquid flow
- Hyperbolic decline arises from changing pressure, two-phase flow, or layered reservoirs

## Related Topics

- Modified Hyperbolic Decline - Transition to exponential at limiting D
- Power Law Exponential Decline - For tight/unconventional reservoirs
- Stretched Exponential Decline - Statistical physics approach
- Duong Decline Model - Fracture-dominated unconventional flow
- Decline Overview - Model selection guide

## References

1. Arps, J.J. (1945). "Analysis of Decline Curves." Transactions of AIME, 160, 228-247.

2. Ali, T.A. and Sheng, J.J. (2015). "Production Decline Models: A Comparison Study." SPE-177300-MS, SPE Eastern Regional Meeting, Morgantown, West Virginia, 13-15 October 2015.

3. Lee, W.J. and Sidle, R.E. (2010). "Gas Reserves Estimation in Resource Plays." SPE-130102, SPE Unconventional Gas Conference, Pittsburgh, Pennsylvania, 23-25 February 2010.

4. Fetkovich, M.J. (1980). "Decline Curve Analysis Using Type Curves." Journal of Petroleum Technology, 32(6), 1065-1077. SPE-4629-PA.

https://petroleumoffice.com/doc/dca-arps

9/10

8/4/26, 7:56 PM

Arps Decline Curve Analysis - Exponential, Hyperbolic, and Harmonic Models

# Product

Functions

Lambdas

Blueprints

Unit Converter

Tools

MCP Server

# Resources

Documentation

FAQ

Change Log

Contact

# Company

Pricing

Academics

Download

# Legal

Terms of Service

Privacy Policy

EULA

Legal Notice

© 2026 Petroleum Office. All rights reserved.

https://petroleumoffice.com/doc/dca-arps

10/10