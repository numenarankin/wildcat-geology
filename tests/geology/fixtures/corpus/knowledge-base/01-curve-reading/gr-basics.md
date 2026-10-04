# Reading the gamma ray curve

## What the GR curve measures

The gamma ray log records natural radioactivity from potassium, thorium and
uranium. In a clean sandstone the reading is low; in shale it is high, because
clay minerals concentrate potassium and thorium. The curve is therefore read as
a shale indicator, not as a lithology log in its own right.

A high GR reading in a gravel-bearing sandstone does not mean shale. Feldspathic
and micaceous grains carry potassium, and a conglomerate can read as hot as a
shale while being an excellent reservoir.

## Picking clean and shale baselines

Vsh from GR requires two picks: a clean line and a shale line. Both are picked
from the log itself over the interval of interest, never carried in from another
well. The linear gamma ray index is

    IGR = (GR_log - GR_clean) / (GR_shale - GR_clean)

and Vsh equals IGR only under the linear assumption. Larionov, Steiber and
Clavier all return lower Vsh than the linear form for the same IGR, and the
choice among them is a judgment about rock age and clay type.
