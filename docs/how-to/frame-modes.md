# Frame modes

*Choose where each spine ends: at a tick, placed inside the data, beyond it, or on whichever side reads best; at the data itself; or at a mark you place.*

`apply(ax)` ends the spines at the outermost ticks inside the data, and so does `range_frame(ax)`, the framing step on its own; the two take the same arguments, so everything below holds for either. The other modes let those ticks reach past the data, or end the spines at the data itself:

```python
ax.vzs.range_frame(frame="loose")
ax.vzs.range_frame(frame="flexible")
ax.vzs.range_frame(frame="data")
```

Three modes end the spine at the outermost tick and differ only in where that tick may fall. `inside` keeps it within the data, `loose` puts it at or beyond the data, and `flexible` lets the tick search take whichever side reads better, so one spine can stop just short of the data at one end and run just past it at the other. These are the three labelings of Talbot, Lin and Hanrahan,[^labelings] and each of them fills the data: an inside tick sits less than one tick gap from the data's end, so the data never runs far past the spine. `flexible` needs a linear axis and raises on a log or date axis. The other two modes keep the ticks inside the data and move only the spine:

| `frame` | outermost ticks | spine ends at |
|---|---|---|
| `inside` | inside the data | the outermost ticks |
| `flexible` | inside or beyond the data | the outermost ticks |
| `loose` | at or beyond the data | the outermost ticks |
| `data` | inside the data | the data's exact min and max |
| `feature` | the marks a `FixedLocator` sets | the outermost marks |

So under `data` the spine runs a little past its last tick at each end, and a tick sits at the data's extreme only when a locator you set puts one there, as `QuartileLocator` does in the [Anscombe figure](../gallery.md). Below, the 23 shuttle flights before Challenger sit under all five modes: Tufte's O-ring damage index against the temperature at launch.[^challenger] The coldest flight did the most damage, and `inside` strands it beyond both spines. `flexible` brackets the cold end at 50 and stops inside the warm one at 80, and `loose` rounds both axes out past the data. `data` and `feature` keep the inside ticks and move only the spine, and `feature` adds [marks of your own](locators.md) among them and carries the spine out to one beyond the data, here the 26–29 °F forecast for the launch morning, colder than any flight before it:

<figure markdown>
![O-ring damage against launch temperature for the 23 flights before Challenger, five times. Under inside the spines end at 60 and 80 and at 0 and 10, and the coldest flight, 53 °F with damage 11, sits beyond both; under flexible the bottom spine runs from 50 to 80; under loose the spines stand off the plot and run from 52 to 84 and from 0 to 12; under data they end at the extremes, 53 to 81 and 0 to 11; under feature the bottom spine runs out to a tick at 28, far left of every flight](../figures/frame_modes.svg)
<figcaption markdown>`flexible` brackets the cold end and stops inside the warm one, and `loose` rounds out past the data; `data` and `feature` move only the spine, `feature` out to the forecast at 28 °F.</figcaption>
</figure>

Both columns read the data, never the view's padding: matplotlib's autoscale leaves 5% of air around the data, and the frame ignores it. A view you pin inside the data with `set_xlim` or `set_ylim` crops the frame to the data left on screen, and the ticks re-fit it as matplotlib's own would. A view wider than the data changes nothing, and is how you make room for a fixed tick outside it, as the [resonance figure](../tutorial/resonance-peak.md) does for its zero baseline.

A tuple sets the modes per spine, `(x, y)`, so a measurement record can end exactly where the data does while the value axis keeps nice bounds:

```python
ax.vzs.range_frame(frame=("data", "loose"))
```

Either entry can itself be a pair `(low, high)` that sets the two ends of one spine apart. A record that begins in 1903 reads better from a round 1900 yet should still stop at its last observation, which is one spine with a loose start and a data end:

```python
ax.vzs.range_frame(frame=(("loose", "data"), "inside"))
```

The ticks follow the ends: the loose end takes the round year just below the data, 1900, while the other end stops at the last observation, so the spine runs from 1900 to 2023.

A spine with a `loose` end also stands off the plot by 8 points: a loose frame rounds outward past the data, so the spine is a detached reference scale rather than the data's own edge, and the gap says so. The other modes sit flush, `flexible` included, since its ticks fall on either side of the data. The `offset` argument sets that gap yourself, in points, and like `frame` takes a tuple `(x, y)` to move the bottom and left spine apart; a `None` in either slot keeps that spine's mode default:

```python
ax.vzs.range_frame(frame="loose", offset=(8, 2))
```

`feature` ends each spine at the outermost mark a `FeatureLocator`, `SummaryLocator`, `QuartileLocator`, or bare `FixedLocator` sets on that axis, or an `AugmentedLocator` sets through its `.extra` side (the marks, not the nice-number ticks it also carries): the peak, the quartiles, a zero baseline. A mark can sit beyond the data, and the spine reaches it anyway, growing the view to keep it on screen. Like `data` and `inside` it sits flush, offset 0 by default rather than `loose`'s 8, because the mark is the data's own landmark rather than a detached reference scale. Set the locator before framing:

```python
ax.yaxis.set_major_locator(vzs.FeatureLocator(...))
ax.vzs.apply(frame=("data", "feature"))
```

[^labelings]: Justin Talbot, Sharon Lin and Pat Hanrahan, ["An Extension of Wilkinson's Algorithm for Positioning Tick Labels on Axes"](http://vis.stanford.edu/papers/tick-labels), *IEEE Transactions on Visualization and Computer Graphics* 16, no. 6 (2010): 1036-1043. Their search requires every labeling to fill the data, so no further tick at the same step would fit inside it; `inside`, `flexible` and `loose` add only the constraint on the outermost ticks.

[^challenger]: Edward R. Tufte, [*Visual Explanations*](https://www.edwardtufte.com/book/visual-explanations-images-and-quantities-evidence-and-narrative/) (Graphics Press, 1997), whose Challenger chapter redraws the engineers' evidence as this scatter and marks the forecast. The damage index is his, a severity-weighted count of O-ring erosion, heating and blow-by.
