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
![The same scatter with the box reduced to two grey spines running between round ticks, the most extreme points falling outside the spines at all four ends](../figures/old_faithful_step_2.svg)
<figcaption markdown>Step two. The box becomes two grey spines running between round ticks, and the extreme points fall outside them.</figcaption>
</figure>

The box becomes two spines, and the tick marks, tick labels and spines turn grey. The ticks stayed on round numbers but only the ones inside the data survive, so the x spine runs from 2 to 5 and the y spine from 50 to 90. The points are untouched.

That leaves the extremes outside the frame. The eruptions run from 1.6 minutes to 5.1 against a spine that stops at 2 and at 5, and the waits from 43 minutes to 96 against a spine from 50 to 90. Nothing is broken: a bare `apply` uses the `inside` mode, which ends each spine at the outermost tick, and the outermost tick is inside the data by construction.

## End the spines at the data

```{.python}
--8<-- "tutorial_old_faithful.py:step3"
```

<figure markdown>
![The same scatter with the spines reaching a little past their outermost ticks to end at the data's extremes](../figures/old_faithful_step_3.svg)
<figcaption markdown>Step three. The ticks do not move; the spines reach out past them to the extremes.</figcaption>
</figure>

The ticks do not move. Each spine now runs from that variable's minimum to its maximum and no further, reaching a little past its outermost tick at both ends, so the frame says that the shortest eruption was a little under two minutes and the longest a little over five, and that nobody waited less than about forty-five minutes or more than about ninety-five. That reading is free: it costs no caption and no extra ink, and it is where the range frame gets its name.

Which mode suits a figure depends on where the extremes fall. Under `inside` the spine ends on a labelled tick, which reads cleanly when the extremes sit near round numbers and strands points outside the frame when they do not, as here. `loose` strands nothing, and pays for it in air: on this data it brackets out to 1.5 and 5.5 minutes and to waits of 40 and 100. `flexible` decides each end on its own, keeping 2 and 5 minutes but bracketing the waits at 40 and 100. `data` is the one that does not depend on where the round numbers happen to fall, since the ends are the extremes themselves. The [frame modes how-to](../how-to/frame-modes.md) has the five side by side.

The same call is also a method on the axes, `ax.vzs.apply(frame="data")`. Every entry point is, with matplotlib's spelling where it has one, so the `vzs.xlabel(ax, ...)` below is also `ax.vzs.set_xlabel(...)`. The how-to pages use that form; the [registration reference](../reference/registration.md) has the rule.

## Name the axes

```{.python}
--8<-- "tutorial_old_faithful.py:step4"
```

<figure markdown>
![The finished figure: the x label under the right end of the bottom spine, the y label horizontal above the left spine](../figures/old_faithful_step_4.svg)
<figcaption markdown>Step four. The x label sits under the right end of the bottom spine and the y label horizontal at the top of the left one.</figcaption>
</figure>

The x label sits under the right end of the bottom spine and the y label sits horizontal at the top of the left spine, where the eye arrives after reading the last tick. Neither is rotated.

## The result

<figure markdown>
![Scatter of Old Faithful eruption length against the wait to the next eruption, two clusters, spines ending at the data's extremes](../figures/old_faithful.svg)
<figcaption markdown>Two clusters, and a frame that reports the range of both variables without a caption.</figcaption>
</figure>

Save it with `fig.savefig("old_faithful.svg", bbox_inches="tight")`. The frame is installed as a draw hook, so it follows any later change to the limits or the ticks, and `vzs.restore(ax)` undoes it exactly.

Next: [Kepler's third law](kepler.md), where one planet is picked out of eight and named in its colour.
