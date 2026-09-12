# Old Faithful

*Four calls turn a default scatter into a range frame that reports both variables' extremes for free.*

Old Faithful erupts for between one and five minutes, and the wait until the next eruption is between forty and a hundred minutes. Plotted against each other the two form two clusters: short eruptions are followed by short waits, long by long. The data are 272 observations from Azzalini and Bowman's 1990 paper, shipped with the examples.

Start with the scatter as matplotlib draws it, then add the frame and the labels one call at a time.

## Draw the data

```python
import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

table = np.genfromtxt(
    "examples/data/old_faithful.csv", delimiter=",", names=True, skip_header=4
)
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.scatter(table["eruptions"], table["waiting"], s=10, color=vzs.palettes.DATA_INK)
```

The file's first four lines name its source, so `skip_header` steps over them to the column names. The colour is yours to set: vanzelfsprekend never recolours a mark, so a scatter drawn before `apply` keeps whatever you gave it. Draw it after `apply` instead and the neutral cycle hands you the same near-black.

This is the figure every matplotlib user knows: a box, ticks at round numbers whether or not the data reaches them, and the axis labels still to come.

## Apply the range frame

```python
vzs.apply(ax, frame="data")
```

The box becomes two spines. Each runs from that variable's minimum to its maximum and no further, so the frame now says that the shortest eruption was a little under two minutes and the longest over five, and that nobody waited less than about forty-five minutes. The ticks stayed on round numbers but only the ones inside the data survive, and the tick marks, tick labels and spines turned grey. The points are untouched.

The `frame="data"` argument is what puts the spine ends exactly at the extremes. The default, `nice`, ends them at the outermost round tick instead. The [frame modes how-to](../how-to/frame-modes.md) has the three modes side by side.

The same call is also a method on the axes, `ax.vzs.apply(frame="data")`. Every entry point is, with matplotlib's spelling where it has one, so the `vzs.xlabel(ax, ...)` below is also `ax.vzs.set_xlabel(...)`. The how-to pages use that form; the [registration reference](../reference/registration.md) has the rule.

## Name the axes

```python
vzs.xlabel(ax, "eruption length (min)")
vzs.ylabel(ax, "minutes to the next")
```

The x label sits under the right end of the bottom spine and the y label sits horizontal at the top of the left spine, where the eye arrives after reading the last tick. Neither is rotated.

## The result

All four calls, as the gallery script draws it:

```{.python}
--8<-- "gallery.py:old_faithful"
```

<figure markdown>
![Scatter of Old Faithful eruption length against the wait to the next eruption, two clusters, spines ending at the data's extremes](../figures/old_faithful.svg)
<figcaption markdown>Two clusters, and a frame that reports the range of both variables without a caption.</figcaption>
</figure>

Save it with `fig.savefig("old_faithful.svg", bbox_inches="tight")`. The frame is installed as a draw hook, so it follows any later change to the limits or the ticks, and `vzs.restore(ax)` undoes it exactly.

Next: [Kepler's third law](kepler.md), where one planet is picked out of eight and named in its colour.
