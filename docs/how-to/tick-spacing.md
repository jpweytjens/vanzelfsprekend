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

<figure markdown>
![The Old Faithful scatter twice. On the left the y spine runs from 50 to 90 under three labels, with points falling outside both of its ends; on the right a label every five minutes and the spine reaching from 45 to 95, close to the data](../figures/spine_reach.svg)
<figcaption markdown>The same scatter at the panel's own count and at `n=8`. The finer step carries the y spine out from 50–90 to 45–95, and crowds the x axis without moving its ends.</figcaption>
</figure>

The spine now falls two minutes short at the bottom and one at the top, where it was seven and six. The bill arrives on the other axis: `n` is one count for both, so the x axis picks up a tick every half minute and still ends where it did, at 2 and at 5. `spacing` takes a tuple when only one axis should change, at the price of being relative to the panel, since a count is absolute where a gap measured in label heights is not.

None of this is the direct route to the extremes. If the spine ends are what you want, `frame="data"` puts them there and leaves the ticks round, and the count goes back to being a decision about labels. The [frame modes how-to](frame-modes.md) has the modes side by side.
