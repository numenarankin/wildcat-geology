Task: Redraw the provided well-log image as a clean, machine-traceable figure. The output is read by a program, not a person: colour is the only thing that identifies a curve, so colours must be pure and never blend.

Input Image: A scanned, black-and-white well-log containing multiple curves overlaid on a dense grid background.

What you are looking at: the image holds exactly two kinds of line, and telling them apart is the whole job.

- Grid lines are the printed background: perfectly straight, horizontal or vertical, evenly spaced, thin, and they run the full width or height of a track. Every track has them and they never wander.
- Curves are the measurements: thicker than grid lines, continuous, and they wander from side to side as they go down. They are the lines that are not part of the regular pattern.

A curve can run straight down on top of a vertical grid line for a stretch, or cross many horizontal ones. It is still the curve. Follow it through and keep drawing it; it does not stop where it meets the grid. A curve only ends where it visibly runs off the edge of the track or where the printed line clearly stops, never in the middle of the track.

Instructions:

Grid Stripping & Background Cleanup:

Remove the existing black gridlines and vertical track dividers entirely.

Remove background noise, scan artifacts and watermarks. The background must be pure white (#FFFFFF), with no texture, shading or gradient.

Curve Separation & Colour Coding:

Isolate each curve trace by its line style (solid, dashed, short-dashed/dotted).

Draw each curve in a pure, fully saturated primary, and use no other colours anywhere:
- Solid = pure red #FF0000
- Dashed = pure green #00FF00
- Short-dashed/dotted = pure blue #0000FF

The colour is what identifies a curve, so the line style does not need to be reproduced. Draw every curve as one continuous unbroken line, including the ones that are dashed or dotted in the original: join each dash to the next along the path the printed curve follows. Do not draw dashes, dots or breaks anywhere.

Draw every curve 3 pixels wide, at full opacity, with hard aliased edges. No anti-aliasing, no soft edges, no gradients, no shadows, no transparency, no glow. A pixel is either the exact curve colour or pure white.

Where a curve genuinely stops in the original, stop it there. Do not extend a curve past where it was printed, and do not invent a curve that is not there.

Grid Reconstruction:

Redraw the grid as 1-pixel lines in light grey #C8C8C8 — never in any of the curve colours.

Where a curve crosses a grid line, the crossing is just the curve's own 3-pixel width. Curve colour must never spread along a grid line in either direction; the grid line stays grey right up to the curve's edge on both sides.

Keep standard track margins, vertical track boundaries and the original linear/logarithmic division spacing.

Keep the depth labels in pure black in the centre depth column, at their original depths, with exactly the digits printed in the original. Where a label cannot be made out, leave it out rather than guessing. Do not add labels where none exist.

Final Output:

No legend, no colour key, no title block, no added annotation of any kind.

Keep the pixel dimensions identical to the input. Do not invent curves, values or labels that are not in the original.
