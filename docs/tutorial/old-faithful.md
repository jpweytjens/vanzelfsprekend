# Old Faithful

*Four calls turn a default scatter into a range frame that reports both variables' extremes for free.*

Old Faithful erupts for between one and five minutes, and the wait until the next eruption is between forty and a hundred minutes. Plotted against each other the two form two clusters: short eruptions are followed by short waits, long by long. The data are 272 observations from Azzalini and Bowman's 1990 paper, `vzs.datasets.load("old_faithful")`. The [complete script](https://github.com/jpweytjens/vanzelfsprekend/blob/main/examples/tutorial_old_faithful.py) draws every step and saves each figure.

Start with the scatter as matplotlib draws it, then add the frame and the labels one call at a time.

## Draw the data

```{.python}
--8<-- "tutorial_old_faithful.py:data"
```

```{.python}
--8<-- "tutorial_old_faithful.py:draw"
```

<figure markdown>
![Scatter of Old Faithful eruption length against the wait to the next eruption in a default matplotlib box, ticks at round numbers past the data on both axes](../figures/old_faithful_step_1.svg)
<figcaption markdown>Step one. The scatter as matplotlib draws it: a box, and ticks at round numbers whether or not the data reach them.</figcaption>
</figure>

The data ship with the package, and `vzs.datasets.describe("old_faithful")` names their source. The colour is yours to set: vanzelfsprekend never recolours a mark, so a scatter drawn before `apply` keeps whatever you gave it. Draw it after `apply` instead and the neutral cycle hands you the same near-black.

## Apply the range frame

```{.python}
--8<-- "tutorial_old_faithful.py:step2"
```

<figure markdown>
![The same scatter with the box reduced to two grey spines that end at each variable's extremes](../figures/old_faithful_step_2.svg)
<figcaption markdown>Step two. Two spines, each running from its variable's minimum to its maximum, and the furniture in grey.</figcaption>
</figure>

The box becomes two spines. Each runs from that variable's minimum to its maximum and no further, so the frame now says that the shortest eruption was a little under two minutes and the longest over five, and that nobody waited less than about forty-five minutes. The ticks stayed on round numbers but only the ones inside the data survive, and the tick marks, tick labels and spines turned grey. The points are untouched.

The `frame="data"` argument is what puts the spine ends exactly at the extremes. The default, `nice`, ends them at the outermost round tick instead. The [frame modes how-to](../how-to/frame-modes.md) has the four modes side by side.

The same call is also a method on the axes, `ax.vzs.apply(frame="data")`. Every entry point is, with matplotlib's spelling where it has one, so the `vzs.xlabel(ax, ...)` below is also `ax.vzs.set_xlabel(...)`. The how-to pages use that form; the [registration reference](../reference/registration.md) has the rule.

## Name the axes

```{.python}
--8<-- "tutorial_old_faithful.py:step3"
```

<figure markdown>
![The finished figure: the x label under the right end of the bottom spine, the y label horizontal above the left spine](../figures/old_faithful_step_3.svg)
<figcaption markdown>Step three. The x label sits under the right end of the bottom spine and the y label horizontal at the top of the left one.</figcaption>
</figure>

The x label sits under the right end of the bottom spine and the y label sits horizontal at the top of the left spine, where the eye arrives after reading the last tick. Neither is rotated.

## The result

<figure markdown>
![Scatter of Old Faithful eruption length against the wait to the next eruption, two clusters, spines ending at the data's extremes](../figures/old_faithful.svg)
<figcaption markdown>Two clusters, and a frame that reports the range of both variables without a caption.</figcaption>
</figure>

Save it with `fig.savefig("old_faithful.svg", bbox_inches="tight")`. The frame is installed as a draw hook, so it follows any later change to the limits or the ticks, and `vzs.restore(ax)` undoes it exactly.

Next: [Kepler's third law](kepler.md), where one planet is picked out of eight and named in its colour.
