# Axis labels

*Put the axis label where the eye arrives after the last tick.*

`xlabel` sits below the right end of the bottom spine, its right edge lined up with the last tick label's, so the label and the tick-label row share one right margin. `ylabel` sits horizontal above the top tick label, left edges aligned. Those are Doumont's better graph, and both come for free:

```python
vzs.xlabel(ax, "year")
vzs.ylabel(ax, "count")
```

`place="beside"` puts the y label back level with the top tick and to its left, Doumont's good graph. Reach for it where the space above the frame is already taken, by a panel title or by the panel above: the frame modes and the warming comparison in the [gallery](../gallery.md) both do.[^cost] `labelpad` widens the gap to the tick labels in either placement, and `flush=False` returns the x label to the spine's end, level with the centre of the last tick label rather than its right edge:

```python
vzs.ylabel(ax, "count", place="beside", labelpad=10)
vzs.xlabel(ax, "year", flush=False)
```

[^cost]: A label beside the ticks costs its own text width, and matplotlib charges it one of two ways: with `bbox_inches="tight"` the saved image grows to the left, while `constrained_layout` shrinks the axes instead. On a 5 by 3.5 inch figure, "output power (mW)" was worth 1.4 inches either way. The raised label costs a line of height and no width, and constrained layout reserves that line between stacked panels, where a hand-set `subplots_adjust` will not.
