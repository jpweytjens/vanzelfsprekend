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

## The count sets how far a `nice` spine reaches

More ticks is not only a denser axis. Under the default `nice` frame each spine ends at the outermost tick, so the tick step also decides how much of the data the frame covers, and a step too coarse for the data leaves the extremes outside it.

Old Faithful's waits run from 43 minutes to 96. At the count this panel chooses, the y axis steps by ten, the outermost ticks inside the data are 50 and 90, and the spine between them leaves the shortest and longest waits outside. Asking for more ticks moves the step to five, and the spine reaches 45 and 95 instead:

```python
ax.vzs.apply(n=8)
```

The reach arrives with a bill. `n` is one count for both axes, so the x axis picks up a tick every half minute and still ends where it did, at 2 and at 5, while the y axis carries eleven labels where three were readable. Density is the wrong lever here: what the figure wants is for the labels to span the data, and that is a criterion the locator already scores.

## Ask for coverage instead

`TalbotLocator` chooses a labelling by weighing four criteria against each other, and `weights` sets their say:

```python
{"simplicity": 0.25, "coverage": 0.2, "density": 0.5, "legibility": 0.05}
```

`coverage` is how far the labels span the data and `density` how near their count is to the target, so raising coverage asks for the reach directly rather than buying it with labels:

```python
ax.vzs.apply(weights={"coverage": 0.5})
```

<figure markdown>
![The Old Faithful scatter three times. Under a bare apply the y spine runs from 50 to 90 with points outside both ends; under n=8 it reaches 45 to 95 under eleven labels, with the x axis crowded to a label every half minute; under a raised coverage weight it reaches the same 45 to 95 under six labels, with the x axis back to two](../figures/spine_reach.svg)
<figcaption markdown>The same scatter three ways. `n=8` and `weights={"coverage": 0.5}` reach the same spine, from 45 to 95, on eleven labels and on six.</figcaption>
</figure>

Six labels against eleven for the same spine, and the x axis is back to the two ticks it chose on its own. The labels stay round, 45 to 95 in tens, and the count still follows the panel, so the same call on a small panel gives 45, 70 and 95 and keeps the reach.

## Which arguments take one axis at a time

| argument | sets | per axis |
|---|---|---|
| `spacing` | the gap between ticks, in label heights | yes, `(x, y)` |
| `n` | the tick count, overriding `spacing` | no, one count for both |
| `nice_numbers` | the seed set the step is built from | no |
| `weights` | the four criteria's say | no |

Where only one axis should change, set a `TalbotLocator` on it and leave the other to the call, since a locator you set is kept: `ax.yaxis.set_major_locator(vzs.TalbotLocator(weights={"coverage": 0.5}))` gives the y axis the reach above and leaves x at its own count. The [locators how-to](locators.md) has that order, and `nice_numbers` and `weights` reach the locator on linear axes only.

If the spine ends are what you want rather than a labelling that happens to reach them, `frame="data"` puts them there and leaves the ticks alone. The [frame modes how-to](frame-modes.md) has the modes side by side.
