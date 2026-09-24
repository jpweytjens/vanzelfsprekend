# Tick spacing

*The tick count follows the axis's length and the labels' size; `spacing` and `n` set it yourself.*

How many ticks an axis carries is not fixed. `apply` and `range_frame` aim for a gap between ticks measured in tick-label heights, seven along x and four along y, so a postage-stamp panel gets two or three ticks, a full-width figure five or six, and a poster with 24 pt labels thins its ticks out without being told. The same call at two widths:

<figure markdown>
![The same rising warming curve twice, a wide axes with year labels every fifty years and a narrow one with only the first and last, both with the same four temperature ticks](../figures/tick_spacing.svg)
<figcaption markdown>The same record at 12 cm and at 2 cm under the same call. The wide axes carries four year labels and the narrow one two, and the two y axes agree because they are the same height.</figcaption>
</figure>

`spacing` sets that gap, a number for both axes or a tuple `(x, y)`, and `n` asks for a count outright when you already know it:

```python
ax.vzs.range_frame(spacing=(10, 4))
ax.vzs.range_frame(n=3)
```

Both go to the default locator, so a locator you set afterwards replaces them along with the rest of it; the [locators how-to](locators.md) has that order. The count is read when the ticks are computed, not when you call `apply`, which is why the figure above needs no per-panel argument; [the frame follows the axes](../explanation/hook.md) says how.

## The count sets how far an `inside` spine reaches

More ticks is not only a denser axis. Under the default `inside` frame each spine ends at the outermost tick, so the tick step also decides how much of the data the frame covers, and a step too coarse for the data leaves the extremes outside it.

Old Faithful's waits run from 43 minutes to 96. At the count this panel chooses, the y axis steps by ten, the outermost ticks inside the data are 50 and 90, and the spine between them leaves the shortest and longest waits outside. Asking for more ticks on that axis moves the step to five, and the spine reaches 45 and 95 instead:

```python
ax.vzs.apply(n=(None, 8))
```

The reach arrives with a bill: eleven labels where three were readable. Density is the wrong lever here, because what the figure wants is for the labels to span the data, and that is a criterion the locator already scores.

## Ask for coverage instead

`TalbotLocator` chooses a labelling by weighing four criteria against each other, and `weights` sets their say:

```python
{"simplicity": 0.25, "coverage": 0.2, "density": 0.5, "legibility": 0.05}
```

`coverage` is how far the labels span the data and `density` how near their count is to the target, so raising coverage asks for the reach directly instead of buying it with labels. The weights reach both axes at once and usually one axis needs them, so set the locator on that axis and leave the other to the call:

```python
ax.yaxis.set_major_locator(vzs.TalbotLocator(weights={"coverage": 0.5}))
ax.vzs.apply()
```

<figure markdown>
![The Old Faithful scatter three times over identical x axes. Under a bare apply the y spine runs from 50 to 90 with points outside both of its ends; under n=(None, 8) it reaches 45 to 95 under eleven labels; under a coverage weight set on the y axis it reaches the same 45 to 95 under six](../figures/spine_reach.svg)
<figcaption markdown>The same scatter three ways, differing along y alone. `n=(None, 8)` and a raised coverage weight reach the same spine, from 45 to 95, on eleven labels and on six.</figcaption>
</figure>

Six labels against eleven for the same spine, and the labels stay round, 45 to 95 in tens. The count still follows the panel, so the same locator on a 3 cm panel gives 45, 70 and 95 and keeps the reach.

These four numbers are a starting point rather than a law, and the authors are the ones who say so: they call their components and their chosen weights ad hoc.[^adhoc] A figure that is not reading right is reason enough to turn them and look.

Only the ratios matter, so raising one entry is the same edit as lowering the rest. `coverage` has a ceiling worth knowing: past about 5 the search abandons round numbers for the data's own extremes, `1.6, 2.1, 2.6` and so on. And `legibility` is the one dial that does nothing, held at a constant; [whose decision is which](../explanation/furniture.md) says why it stays there.

`spacing` and `n` take an `(x, y)` tuple. `nice_numbers` and `weights` reach both axes, and the locator above is their per-axis spelling: a locator you set is kept, which is matplotlib's own arrangement, since `apply` installs one on both axes for you and dropping to `ax.yaxis` is how you tune one. The [locators how-to](locators.md) has that order, and both arguments reach the locator on linear axes only.

If the spine ends are what you want rather than a labelling that happens to reach them, `frame="data"` puts them there and leaves the ticks alone. The [frame modes how-to](frame-modes.md) has the modes side by side.

[^adhoc]: "To some extent, our proposed optimization components and the chosen weights are ad hoc." Justin Talbot, Sharon Lin and Pat Hanrahan, ["An Extension of Wilkinson's Algorithm for Positioning Tick Labels on Axes"](http://vis.stanford.edu/papers/tick-labels), *IEEE Transactions on Visualization and Computer Graphics* 16, no. 6 (2010): 1036-1043.
