# Direct labels

*Delete the legend; name each line at its end, or beside the point the reader is looking at.*

`line_labels` replaces a legend: delete `ax.legend()` and each line gets its `label=` text at its right end, in its line's colour. Where lines converge, the labels shift apart just enough to stay readable, keeping their order. `at="start"` labels the left ends instead, slopegraph-style, which pairs well with `frame="loose"` since the offset spine leaves room for the text:

```python
vzs.line_labels(ax)  # label every line at its right end
vzs.line_labels(ax, at="start")  # and/or at its left end
```

`label` puts a label beside a named artist at a spine coordinate you choose, where the reader will look for it. The text is the artist's `label=`, the anchor is the line's crossing or the scatter's nearest point, and from there the text slides just far enough to clear the other ink: right of the anchor by default, left, above or below when the right is blocked, or where `side=` says:

```python
vzs.label(ax, "measured", x=17.2)  # resonance figure: beside the nearest point
vzs.label(ax, ["SSP1-1.9", "SSP2-4.5"], x=2060)  # warming figure: a column at one year
ax.scatter([x], [y], label="Belgium")  # any scatter: draw the point you want to name
vzs.label(ax, "Belgium")  # then name it; a one-point artist needs no anchor
ax.vzs.label("Belgium")  # the same through the accessor
```

Doumont's resonance figure is the model: "measured" beside the topmost point and "calculated" beside the flank under it, each anchored where the reader looks and slid just clear of the ink:

<figure markdown>
![A sharp resonance peak with "measured" above and right of the topmost point and "calculated" right of the falling flank, neither touching the points or the curve](../figures/resonance_peak.svg)
<figcaption markdown>"measured" beside the topmost point and "calculated" beside the flank under it, each anchored where the reader looks and slid just clear of the ink.</figcaption>
</figure>

Labelling is deliberate: you name each label, the library decides only how far it moves. Naming many points of one cloud is a different problem, and [textalloc](https://github.com/ckjellson/textalloc) and [adjustText](https://github.com/Phlya/adjustText) solve it.

Tick labels get the same care: ticks placed by the data, such as `QuartileLocator`'s, can land arbitrarily close, and where their labels crowd they shift apart just enough to stay readable, keeping their order. The tick marks stay exactly at their values.
