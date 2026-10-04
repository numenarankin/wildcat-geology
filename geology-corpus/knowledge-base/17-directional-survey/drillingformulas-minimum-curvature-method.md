<!-- Source: https://www.drillingformulas.com/minimum-curvature-method/ -->
<!-- Converted: equations hand-transcribed from the page images (the PDF is    -->
<!-- image-only; pdf-inspector classifies it image_based, and Tesseract        -->
<!-- mangles the formulas). Prose is Tesseract output, lightly cleaned.        -->
<!-- The worked example below was recomputed independently and matches the     -->
<!-- published result, which is what validates this transcription.             -->

# Minimum Curvature Method

The Minimum Curvature Method smooths the two straight-line segments of the
Balanced Tangential Method by applying a Ratio Factor (RF). It projects the well
path as a circular arc between two survey stations.

## Formulas

$$North = \frac{MD}{2}\left[\sin(I_1)\cos(A_1) + \sin(I_2)\cos(A_2)\right] \times RF$$

$$East = \frac{MD}{2}\left[\sin(I_1)\sin(A_1) + \sin(I_2)\sin(A_2)\right] \times RF$$

$$TVD = \frac{MD}{2}\left[\cos(I_1) + \cos(I_2)\right] \times RF$$

$$\beta = \cos^{-1}\left[\cos(I_2 - I_1) - \sin(I_1)\sin(I_2)\left(1 - \cos(A_2 - A_1)\right)\right]$$

$$RF = \frac{2}{\beta}\tan\left(\frac{\beta}{2}\right)$$

**β must be in radians.**

Where:

- `MD` = measured depth between surveys, ft
- `I1` = inclination of the upper survey, degrees
- `I2` = inclination of the lower survey, degrees
- `Az1` = azimuth of the upper survey
- `Az2` = azimuth of the lower survey
- `RF` = ratio factor
- `β` = dog leg angle

## Worked example

Survey 1: depth 3500 ft, inclination 15°, azimuth 20°
Survey 2: depth 3600 ft, inclination 25°, azimuth 45°

MD = 3600 − 3500 = 100 ft

$$\beta = \cos^{-1}\left[\cos(25-15) - \left(\sin(15)\sin(25)\right)\left(1 - \cos(45-20)\right)\right]$$

β = 0.22605 radian = 12.95 degree

Recomputed independently from the formula above: β = 0.22605 rad (12.95°),
RF = 1.004280, TVD = 94.012 ft over the 100 ft measured-depth interval. This is
the Layer-1 oracle for `md_to_tvd`.

## Note on a conflicting source

`17-directional-survey/directional-drilling-advanced-trajectory-modelling-thesis`
states the dogleg angle (its Eq. 4.1) as

    cos α1 · cos α2 + sin α1 · sin α2 · (cos β2 − cos β1)

which is **wrong** as it stands — it returns 31.79° on the example above instead
of 12.95°. The error is `(cos β2 − cos β1)` where the correct form is
`cos(β2 − β1)`; the two agree only by coincidence. Whether the thesis printed it
that way or the text flattening corrupted it, do not implement from that
equation. Use the form on this page, which is validated against a published
numeric result.
