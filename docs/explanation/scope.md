# Scope and limits

*The range frame assumes an x-y plane: two cartesian spines, each on a scale it can put round numbers on. Where that assumption fails, vanzelfsprekend declines rather than guesses, and says so once.*

## What the frame fits

A range frame is built for the ordinary case: a rectilinear axes, the kind `plt.subplots` hands back by default, with an x-axis and a y-axis each on a linear or a log scale. Dates are the one variation the frame reads on its own; a datetime axis gets [`DateBreaksLocator`](../reference/locators.md) instead of the numeric search, but it is still an x-y plane underneath, so it fits the same assumption. That covers the [resonance peak](../tutorial/resonance-peak.md), the [grand tours](../tutorial/grand-tours.md) and most of what matplotlib draws by default.

## What it declines, and how

Two things can put the plane out of reach, and vanzelfsprekend treats both the same way: warn, and leave the axes exactly as it found them.

An axis can carry a scale the locator has no round numbers for, such as `symlog` or `logit`, or a unit converter the frame does not read, such as a categorical axis. Either failure is local to that one axis; the other axis of the same axes can still be framed on its own.

An axes itself can be the wrong shape for a plane at all. Polar and 3D axes have no pair of cartesian spines to trim, so there the whole axes is declined, not just one side of it.

Declining is the point, not a shortfall. A frame forced onto an axes it does not fit (three-dimensional data flattened onto ticks built for a plane) would corrupt the reading more quietly than drawing no frame at all, so vanzelfsprekend leaves the axes untouched and says why:

```python
fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
vzs.range_frame(ax)
# UserWarning: vanzelfsprekend: axes uses the 'polar' projection; only
# rectilinear (x-y) axes are supported, leaving it untouched
```

The axes is left exactly as plain matplotlib would have drawn it, spines, ticks and all.

## If a redraw fails

The frame keeps itself glued to the data on every redraw. If one of those updates ever fails, the frame would just stop tracking the data with no sign anything had gone wrong, so the first failure on an axes raises a `UserWarning` with the traceback attached and later redraws stay quiet.

## `small_multiples` wants one shared plane

`small_multiples` frames a grid on a common scale, and a common scale means one kind of plane under every panel. A panel that fails the rectilinear check declines on its own terms, the same warning as anywhere else, and drops out of the grid rather than forcing its neighbours to a scale it cannot share. Mixing projections into one grid is not a supported way to compare panels; a grid of polar plots wants a different kind of comparison than `small_multiples` was built to frame.
