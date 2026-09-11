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
