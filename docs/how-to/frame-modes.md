# Frame modes

*Choose where each spine ends: at the outermost tick, at a round number bracketing the data, or at the data itself.*

`apply(ax)` ends the spines at the outermost ticks, and so does `range_frame(ax)`, the framing step on its own; the two take the same arguments, so everything below holds for either. Two other modes end the spines at the data itself, or at round numbers bracketing it:

```python
vzs.range_frame(ax, frame="data")
vzs.range_frame(ax, frame="loose")
```

The ticks and the spine are two separate decisions. The ticks are the locator's, nice numbers inside the data whatever the mode. Where the spine ends is the frame mode's, and only `nice` and `loose` make it follow the ticks:

| `frame` | ticks | spine ends at |
|---|---|---|
| `nice` | nice numbers inside the data | the outermost ticks |
| `loose` | nice numbers bracketing the data | the outermost ticks |
| `data` | nice numbers inside the data | the data's exact min and max |

So under `data` the spine runs a little past its last tick at each end, and a tick sits at the data's extreme only when a locator you set puts one there, as `QuartileLocator` does in the [Anscombe figure](../gallery.md). The same record under the three modes carries the same ticks under `nice` and `data`; only the spine ends move:

<figure markdown>
![The same rising warming curve three times, ticks at 1850 and 2000 and at -0.5 to 1.0: under nice the spines end at the 2000 and 1.0 ticks, under loose they stand off the plot and reach 2150 and 1.5, under data they run past the same ticks to the last year and the highest value](../figures/frame_modes.svg)
<figcaption markdown>The same record under the three modes carries the same ticks under `nice` and `data`; only the spine ends move.</figcaption>
</figure>

Both columns read the data, never the view's padding: matplotlib's autoscale leaves 5% of air around the data, and the frame ignores it. A view you pin inside the data with `set_xlim` or `set_ylim` crops the frame to the data left on screen, and the ticks re-fit it as matplotlib's own would. A view wider than the data changes nothing, and is how you make room for a fixed tick outside it, as the [resonance figure](../tutorial/resonance-peak.md) does for its zero baseline.

A tuple sets the modes per spine, `(x, y)`, so a measurement record can end exactly where the data does while the value axis keeps nice bounds:

```python
vzs.range_frame(ax, frame=("data", "loose"))
```

Either entry can itself be a pair `(low, high)` that sets the two ends of one spine apart. A record that begins in 1903 reads better from a round 1900 yet should still stop at its last observation, which is one spine with a loose start and a data end:

```python
vzs.range_frame(ax, frame=(("loose", "data"), "nice"))
```

The ticks follow the ends: the loose end takes the round number just beyond the data while the other end keeps its ticks inside, so that record gets ticks at 1900, 1950 and 2000 under a spine from 1900 to 2023.

A spine with a `loose` end also stands off the plot by 8 points: a loose frame rounds outward past the data, so the spine is a detached reference scale rather than the data's own edge, and the gap says so (`data` and `nice` sit flush). The `offset` argument sets that gap yourself, in points, and like `frame` takes a tuple `(x, y)` to move the bottom and left spine apart; a `None` in either slot keeps that spine's mode default:

```python
vzs.range_frame(ax, frame="loose", offset=(8, 2))
```
