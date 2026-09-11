# Where the frame stops

*The range frame assumes an x-y plane: two cartesian spines, each on a scale it can put round numbers on. Where that assumption fails, vanzelfsprekend declines rather than guesses, and says so once.*

## What the frame fits

A range frame is built for the ordinary case: a rectilinear axes, the kind `plt.subplots` hands back by default, with an x-axis and a y-axis each on a linear or a log scale. Dates are the one variation the frame reads on its own; a datetime axis gets [`DateBreaksLocator`](../reference/locators.md) instead of the numeric search, but it is still an x-y plane underneath, so it fits the same assumption. That covers the [resonance peak](../tutorial/resonance-peak.md), the [grand tours](../tutorial/grand-tours.md) and most of what matplotlib draws by default.

## What it declines, and how

Two things can put the plane out of reach, and vanzelfsprekend treats both the same way: warn, and leave the axes exactly as it found them.

An axis can carry a scale the locator has no round numbers for, such as `symlog` or `logit`, or a unit converter the frame does not read, such as a categorical axis. Either failure is local to that one axis; the other axis of the same axes can still be framed on its own.

An axes itself can be the wrong shape for a plane at all. Polar and 3D axes have no pair of cartesian spines to trim, so there the whole axes is declined, not just one side of it.

Both paths raise a `UserWarning` and touch nothing. Framing a polar axes, for instance:

```python
fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
vzs.range_frame(ax)
# UserWarning: vanzelfsprekend: axes uses the 'polar' projection; only
# rectilinear (x-y) axes are supported, leaving it untouched
```

leaves `ax` exactly as plain matplotlib would have drawn it, spines, ticks and all. Nothing about the plot below the warning tells you the frame passed through it.

## The seam this closes

That was not always the outcome. A polar axes used to reach into `range_frame`'s cartesian assumptions and crash. A 3D axes was worse: no crash, but ticks and spines built for two dimensions applied to three, corrupting the plot instead of refusing it. Both are projections now, in the same sense the frame already used for scales, and both decline the same way an unsupported scale does: a warning, an untouched axes, nothing corrupted.

## A stale frame still says so

The frame keeps itself glued to the data on every redraw, and redraws happen off in matplotlib's event loop where nothing is watching for exceptions. Left alone, a failure there would just stop updating the frame with no sign anything had gone wrong. Instead the first draw-time failure on a given axes raises a `UserWarning` with the traceback attached; later draws on the same axes fail quietly, because the frame is already known to be stale and repeating the warning on every redraw would only be noise.

## `small_multiples` wants one shared plane

`small_multiples` frames a grid on a common scale, and a common scale means one kind of plane under every panel. A panel that fails the rectilinear check declines on its own terms, the same warning as anywhere else, and drops out of the grid rather than forcing its neighbours to a scale it cannot share. Mixing projections into one grid is not a supported way to compare panels; a grid of polar plots wants a different kind of comparison than `small_multiples` was built to frame.
