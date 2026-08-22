# vanzelfsprekend

A matplotlib plot arrives framed in a box: four spines at the view limits, none of them saying anything about the data inside. A range frame makes those lines work. The top and right spines go, and the two that remain are trimmed to the data, so each spine reports its variable's minimum and maximum. Ticks land on nice numbers strictly inside the data range, and the axis labels sit at the spine ends instead of the middle. Range frames come from Tufte's *The Visual Display of Quantitative Information*; the tick placement is Talbot, Lin and Hanrahan's extended Wilkinson algorithm (mizani's `breaks_extended`). The name is Dutch for self-evident, literally "self-speaking": the plot speaks for itself.

![A scatter of measured cycling speeds against gradient, with a backsolved model curve in orange inside a range frame](docs/quickstart.png)

## Install

Not on PyPI yet. Install from a checkout:

```sh
uv add /path/to/vanzelfsprekend
```

## Quickstart

The figure above, in full. A rider is three scalars (flat cruising speed, critical climbing rate, a descent comfort cap); a force-balance cubic backsolves the speed they imply at any gradient, and measured speeds scatter around that curve:

```python
import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vfs

G0, MASS, CDA, CRR, RHO, WIND = 9.81, 78.0, 0.35, 0.005, 1.225, 2.22
V_FLAT, VAM_CP, V_CAP = 29 / 3.6, 1150.0, 52 / 3.6  # the three rider scalars
K_A = 0.5 * RHO * CDA


def solve_speed(power, gradient):
    """Largest real root of the force-balance cubic, per gradient."""
    theta = np.arctan(gradient)
    speeds = []
    for p, th in zip(*np.broadcast_arrays(power, theta)):
        drag = K_A * WIND**2 + MASS * G0 * (CRR * np.cos(th) + np.sin(th))
        roots = np.roots([K_A, 2 * K_A * WIND, drag, -p])
        speeds.append(roots[np.isreal(roots)].real.max())
    return np.array(speeds)


def backsolved_speed(gradient):
    """Speed at any gradient from the three scalars."""
    p_flat = K_A * (V_FLAT + WIND) ** 2 * V_FLAT + CRR * MASS * G0 * V_FLAT
    cp = MASS * G0 * VAM_CP / 3600
    climb = p_flat + (cp - p_flat) * np.clip(gradient / 0.03, 0, 1)
    descent = p_flat * np.exp(-25 * np.abs(gradient))
    power = np.where(gradient >= 0, climb, descent)
    return 3.6 * np.minimum(solve_speed(power, gradient), V_CAP)


rng = np.random.default_rng(7)
gradient = rng.uniform(-0.099, 0.099, 45)
speed = backsolved_speed(gradient) + rng.normal(0, 1.5, gradient.size)
grid = np.linspace(-0.10, 0.10, 300)

fig, ax = plt.subplots(figsize=(5, 3.5))
ax.scatter(100 * gradient, speed, s=12, color="#333333", zorder=3)
ax.plot(100 * grid, backsolved_speed(grid), color="#EE7733", linewidth=1.8)
ax.text(-6.0, 50, "measured", color="#333333")
ax.text(4.0, 28, "backsolved", color="#EE7733")
vfs.apply(ax, frame="loose")
vfs.xlabel(ax, "gradient (%)")
vfs.ylabel(ax, "speed (km/h)", flush=True)
fig.savefig("scatter.png", dpi=150, bbox_inches="tight")
```

`apply` trims the spines on every draw, so the frame keeps hugging the data through later autoscales and tick changes. `restore` puts the axes back exactly as they were.

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
