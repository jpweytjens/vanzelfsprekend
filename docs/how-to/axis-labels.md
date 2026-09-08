# Axis labels

*Put the axis label where the eye arrives after the last tick.*

`xlabel` sits below the right end of the bottom spine; `ylabel` sits horizontal at the top of the left spine. `place="beside"` (the default) anchors it level with the top tick label; `place="above"` stacks it over the top tick, its left edge aligned with the tick label's, Doumont's two y-labels, from his "good" and "better" graphs. `labelpad` widens the gap to the tick labels:

```python
vzs.ylabel(ax, "count", labelpad=10)  # beside the top tick (default)
vzs.ylabel(ax, "count", place="above")  # stacked above it, left-aligned
```

`flush=True` on `xlabel` aligns the label's right edge with the spine's end, which the [resonance tutorial](../tutorial/resonance-peak.md) uses.
