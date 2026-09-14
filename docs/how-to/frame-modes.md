# Frame modes

*Choose where each spine ends: at the outermost tick, at a round number bracketing the data, at the data itself, or at a mark you place.*

`apply(ax)` ends the spines at the outermost ticks, and so does `range_frame(ax)`, the framing step on its own; the two take the same arguments, so everything below holds for either. Two other modes end the spines at the data itself, or at round numbers bracketing it:

```python
ax.vzs.range_frame(frame="data")
ax.vzs.range_frame(frame="loose")
```

The ticks and the spine are two separate decisions. The ticks are the locator's: nice numbers inside the data, except under `feature`, where they're the marks a `FixedLocator` sets. Where the spine ends is the frame mode's, and `nice`, `loose`, and `feature` all make it follow the ticks:

| `frame` | ticks | spine ends at |
|---|---|---|
| `nice` | nice numbers inside the data | the outermost ticks |
| `loose` | nice numbers bracketing the data | the outermost ticks |
| `data` | nice numbers inside the data | the data's exact min and max |
| `feature` | the marks a `FixedLocator` sets | the outermost marks |

So under `data` the spine runs a little past its last tick at each end, and a tick sits at the data's extreme only when a locator you set puts one there, as `QuartileLocator` does in the [Anscombe figure](../gallery.md). The same warming record sits under all four modes below. `nice`, `loose` and `data` share their ticks, nice numbers inside the data, and move only where the spine ends; `feature` instead sets its ticks at the marks you place and carries the spine out to one beyond the data, here the 2 °C target the record has not reached:

<figure markdown>
![The same rising warming curve four times. Under nice the spines end at the 2000 and 1.0 ticks; under loose they stand off the plot and reach 2150 and 1.5; under data they run past the same ticks to the last year and the highest value; under feature the y ticks are 0, 1 and 2 and the left spine climbs past the curve to the 2 °C mark the warming never reaches](../figures/frame_modes.svg)
<figcaption markdown>`nice`, `loose` and `data` share their ticks and move only the spine; `feature` ticks the marks instead and reaches the 2 °C target beyond the data.</figcaption>
</figure>

Both columns read the data, never the view's padding: matplotlib's autoscale leaves 5% of air around the data, and the frame ignores it. A view you pin inside the data with `set_xlim` or `set_ylim` crops the frame to the data left on screen, and the ticks re-fit it as matplotlib's own would. A view wider than the data changes nothing, and is how you make room for a fixed tick outside it, as the [resonance figure](../tutorial/resonance-peak.md) does for its zero baseline.

A tuple sets the modes per spine, `(x, y)`, so a measurement record can end exactly where the data does while the value axis keeps nice bounds:

```python
ax.vzs.range_frame(frame=("data", "loose"))
```

Either entry can itself be a pair `(low, high)` that sets the two ends of one spine apart. A record that begins in 1903 reads better from a round 1900 yet should still stop at its last observation, which is one spine with a loose start and a data end:

```python
ax.vzs.range_frame(frame=(("loose", "data"), "nice"))
```

The ticks follow the ends: the loose end takes the round number just beyond the data while the other end keeps its ticks inside, so that record gets ticks at 1900, 1950 and 2000 under a spine from 1900 to 2023.

A spine with a `loose` end also stands off the plot by 8 points: a loose frame rounds outward past the data, so the spine is a detached reference scale rather than the data's own edge, and the gap says so (`data` and `nice` sit flush). The `offset` argument sets that gap yourself, in points, and like `frame` takes a tuple `(x, y)` to move the bottom and left spine apart; a `None` in either slot keeps that spine's mode default:

```python
ax.vzs.range_frame(frame="loose", offset=(8, 2))
```

`feature` ends each spine at the outermost mark a `FeatureLocator`, `SummaryLocator`, `QuartileLocator`, or bare `FixedLocator` sets on that axis, or an `AugmentedLocator` sets through its `.extra` side (the marks, not the nice-number ticks it also carries): the peak, the quartiles, a zero baseline. A mark can sit beyond the data, and the spine reaches it anyway, growing the view to keep it on screen. Like `data` and `nice` it sits flush, offset 0 by default rather than `loose`'s 8, because the mark is the data's own landmark rather than a detached reference scale. Set the locator before framing:

```python
ax.yaxis.set_major_locator(vzs.FeatureLocator(...))
ax.vzs.apply(frame=("data", "feature"))
```
