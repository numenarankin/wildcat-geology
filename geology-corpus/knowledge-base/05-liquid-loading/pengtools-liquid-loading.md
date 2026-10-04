<!-- Source: pengtools-liquid-loading -->
<!-- Converted: html2text + recovered MathJax alt-text equations -->

## Contents

  * 1 Brief
  * 2 Math & Physics
  * 3 PQplot workflow
  * 4 Discussion
  * 5 Example. Calculating critical gas velocity and rate
    * 5.1 Input data
    * 5.2 Solution
    * 5.3 Solution with PQplot
  * 6 Nomenclature
  * 7 See also
  * 8 References


## Brief

**Liquid loading** is a phenomenon when the gas phase does't provide sufficient transport energy to lift the liquids out of the well. 

In **1969** Turner et al. published an empirical correlation defining the **Liquid loading** gas velocity[1]. 

[](/index.php?title=File:Liquid_Loading.png "Liquid Loading")

## Math & Physics

The minimum gas velocity to remove the liquid equation: 

     $v_g = 1.593\ \sigma^{1/4}\ \frac{({\rho_L-\rho_g})^{1/4}}{\rho_g^{1/2}}$ [2] (1)

_Note that original paper[1] uses 20.4 constant which is good if the surface tension units are in 'lbf/ft'. Also 20.4 is calculated by adjusting the theoretical equation constant by 20 percent. For the reference PROSPER uses 2.04. PQplot uses 1.593._

The minimum gas rate to remove the liquid equation: 

     $q_g = 3.067\ \frac{P\ v_g\ A}{T\ z}$ (2)

## PQplot workflow

In order to calculate the liquid loading point in [PQplot](/index.php?title=PQplot "PQplot"):  
For every point in the [VLP](/index.php?title=VLP "VLP") curve:  
1\. Critical gas velocity at the wellhead is calculated by eq (1)  
2\. Wellhead flowing gas velocity is calculated 

     $v_{g wellhead} = \frac{q_g \times 10^6}{86400 A}\ \frac{14.7}{P}\ \frac{T}{520}\ \frac{z}{1}$ 

3\. Liquid loading flag is 1 if: 

     $v_{g wellhead} < v_{g critical}$ 

4\. Critical gas rate is the last [VLP](/index.php?title=VLP "VLP") curve point at which liquid loading flag is 1. 

## Discussion

To avoid the **Liquid loading** the gas velocity should be above the **Liquid loading** velocity. 

The higher the gas rate the higher the gas velocity. 

The lower the wellhead flowing pressure the higher the gas rate. 

The bigger the tubing ID the higher the gas rate. 

In case when the gas rate is limited by the [Reservoir](/index.php?title=Reservoirs "Reservoirs") deliverability smaller tubing ID will increase the gas velocity. 

## Example. Calculating critical gas velocity and rate

Example 3-2 from [2]

### Input data

     $P = 400$ , flowing wellhead pressure, psia
     $T =120$ , flowing wellhead temperature, °F
     $\rho_L =67$ , liquid density, lbm/ft3
     $\sigma = 60$ , water surface tension, dyne/cm
     $SG_g = 0.6$ , gas specific gravity
     $z =0.9$ , gas compressibility factor

Production string = 2-3/8 inch tubing with 1.995 in ID, A = .0217 ft2  
Water is the produced liquid 

### Solution

Calculate the gas density: 

     $\rho_g = \frac{28.967\ SG_g\ p}{z\ 10.732\ T_R} = \frac{28.967\ 0.6\ 400}{0.9\ 10.732\ (120+460)}=1.24$ , lbm/ft2

  
Calculate the critical gas velocity form (1): 

     $v_g = 1.593\ \sigma^{1/4}\ \frac{({\rho_L-\rho_g})^{1/4}}{\rho_g^{1/2}} = 1.593\ 60^{1/4}\ \frac{({67-1.24})^{1/4}}{1.24^{1/2}}=11.3$ , ft/sec

  
Calculate the critical gas rate form (2): 

     $q_g = 3.067\ \frac{P\ v_g\ A}{T\ z} = 3.067\ \frac{400\ 11.3\ 0.0217}{(120+460)\ 0.9}=0.578$ , MMscfd

### Solution with PQplot

[PQplot](/index.php?title=PQplot "PQplot") calculates the following critical gas rate: 

     $q_g = 0.56$ , MMscfd

[](/index.php?title=File:Liquid_loading_example_3-1.png "Liquid loading example 3-1")  
[Liquid loading example 3-1 (Public model)](https://www.pengtools.com/pqPlot?paramsToken=c97c4f3b499cf59b82d61c374d3ab21a)

## Nomenclature

     $A$ = flow area, ft^2
     $P$ = flowing wellhead pressure, psia
     $q_g$ = gas rate, MMscf/d
     $\rho_g$ = gas density, lbm/ft3
     $\rho_L$ = liquid density, lbm/ft3
     $\sigma$ = surface tension, dyne/cm (ref values: 60 - water, 20 - condensate) [1]
     $SG_g$ = gas specific gravity
     $T$ = flowing wellhead temperature, °R
     $v_g$ = gas velocity, ft/sec
     $z$ = gas compressibility factor at flowing P & T, dimensionless

## See also

[Gray correlation](/index.php?title=Gray "Gray")

## References

  1. ↑ 1.0 1.1 1.2 Turner, R. G.; Hubbard, A. E.; Dukler (Nov 1969). ["Analysis and Prediction of Minimum Flow Rate for the Continuous Removal of Liquids from Gas Wells"](https://www.scribd.com/doc/269398353/Friction-Factors-for-Pipe-Flow-MoodyLFpaper1944). _Journal of Petroleum Technology_ (SPE-2198-PA): 1475–1482.
  2. ↑ 2.0 2.1 Lea, J. F.; Nickens, M.; Wells (2011). [_Gas Well Deliquification_](https://www.sciencedirect.com/book/9780750682800/gas-well-deliquification). Energy Tribune Publishing Inc.
