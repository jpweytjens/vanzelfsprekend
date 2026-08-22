# vanzelfsprekend

Let the plot speak for itself: a matplotlib treatment inspired by Edward Tufte and Jean-luc Doumont. The name is Dutch for self-evident, literally "self-speaking".

What it adds today:

- Range frames: the top and right spines go, the remaining two are trimmed to the data, so each spine shows its variable's minimum and maximum (Tufte, *The Visual Display of Quantitative Information*).
- Ticks on nice numbers strictly inside the data range, computed from the data rather than the view limits (Talbot, Lin and Hanrahan's extended Wilkinson algorithm, via mizani's `breaks_extended`).
- Axis labels at the spine ends instead of centered along them.
- A draw hook that keeps all of this glued to the data through autoscaling and tick changes, and `restore` to undo it exactly.

![A scatter of measured cycling speeds against gradient, with a backsolved model curve in orange inside a range frame](docs/backsolved_speed.png)

The figure comes from [`examples/backsolved_speed.py`](examples/backsolved_speed.py): the treatment with `frame="loose"` around a modelled speed curve.

## Install

Not on PyPI yet. Install from a checkout:

```sh
uv add /path/to/vanzelfsprekend
```

## Quickstart

The smallest complete example, in the default `nice` mode:

```python
import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vfs

rng = np.random.default_rng(0)
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12, color="0.2")
vfs.apply(ax)
vfs.xlabel(ax, "time (s)")
vfs.ylabel(ax, "voltage", flush=True)
fig.savefig("scatter.png", dpi=150, bbox_inches="tight")
```

## Usage

`apply(ax)` ends the spines at the outermost ticks. Two other modes:

```python
vfs.apply(ax, frame="data")   # spines end at the exact data min and max
vfs.apply(ax, frame="loose")  # spines end at nice numbers bounding the data
```

`xlabel` sits below the right end of the bottom spine; `ylabel` sits horizontal at the top of the left spine. `flush=True` anchors the y-label at the topmost tick label; `labelpad` widens the gap to the tick labels:

```python
vfs.ylabel(ax, "count", flush=True, labelpad=10)
```

`register()` adds the entry points as Axes methods, so `ax.apply()` and `ax.restore()` work anywhere; `unregister()` removes them again.

Only plain linear axes are handled. A log-scaled axis, or one with a units converter (dates, categories), is left untouched with a warning.

## API

| Name | Does |
| --- | --- |
| `apply(ax, ...)` | the full treatment with defaults |
| `restore(ax)` | put the axes back as they were |
| `range_frame(ax, frame, n, offset, ...)` | the range frame, with every knob |
| `xlabel(ax, text)`, `ylabel(ax, text, flush)` | end-of-spine axis labels |
| `register()`, `unregister()` | add or remove the `ax.apply` and `ax.restore` methods |
| `TalbotLocator(n, loose, ...)` | the tick locator, usable on its own |

Parameters and behavior are documented in the docstrings.
