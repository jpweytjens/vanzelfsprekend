# vanzelfsprekend

Let the plot speak for itself: a matplotlib treatment inspired by [Edward Tufte](https://www.edwardtufte.com/book/the-visual-display-of-quantitative-information/) and [Jean-luc Doumont](https://www.principiae.be/). The name is Dutch for self-evident, literally "self-speaking".

What it adds today:

- Range frames: the top and right spines go, the remaining two are trimmed to the data, so each spine shows its variable's minimum and maximum ([Tufte](https://www.edwardtufte.com/book/the-visual-display-of-quantitative-information/), *The Visual Display of Quantitative Information*).
- Ticks on nice numbers strictly inside the data range, computed from the data rather than the view limits ([Talbot, Lin and Hanrahan's extended Wilkinson algorithm](http://vis.stanford.edu/papers/tick-labels), via [mizani](https://mizani.readthedocs.io/en/stable/)'s `breaks_extended`).
- Axis labels at the spine ends instead of centered along them.
- Line labels at the lines' ends in place of a legend, each in its line's colour, pushed apart only as far as needed to never overlap ([Doumont](https://www.principiae.be/), *Trees, maps and theorems*).
- A draw hook that keeps all of this glued to the data through autoscaling and tick changes, and `restore` to undo it exactly.
- Greyed axis furniture and an ink-first colour cycle built on
  [Paul Tol's colour schemes](https://sronpersonalpages.nl/~pault/):
  single-series plots stay near-black, colour enters at series two of
  the same kind, and `color="tol:orange"` works anywhere matplotlib
  takes a colour.

![A scatter of measured cycling speeds against gradient, with modelled and backsolved speed curves labelled at their right ends inside a range frame](docs/backsolved_speed.png)

The figure comes from [`examples/backsolved_speed.py`](examples/backsolved_speed.py): the treatment with `frame="loose"` around modelled and backsolved speed curves, their labels stacked by `line_labels` where the curves merge.

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

`line_labels` replaces a legend: delete `ax.legend()` and each line gets its `label=` text at its right end, in its line's colour. Where lines converge, the labels shift apart just enough to stay readable, keeping their order (the placement is the exact least-squares optimum, re-solved on every draw). `at="start"` labels the left ends instead, slopegraph-style, which pairs well with `frame="loose"` since the offset spine leaves room for the text:

```python
vfs.line_labels(ax)              # label every line at its right end
vfs.line_labels(ax, at="start")  # and/or at its left end
```

Only plain linear axes are handled. A log-scaled axis, or one with a units converter (dates, categories), is left untouched with a warning.

## API

| Name | Does |
| --- | --- |
| `apply(ax, ...)` | the full treatment with defaults |
| `restore(ax)` | put the axes back as they were |
| `range_frame(ax, frame, n, offset, ...)` | the range frame, with every knob |
| `xlabel(ax, text)`, `ylabel(ax, text, flush)` | end-of-spine axis labels |
| `line_labels(ax, at, labelcolor, pad, gap)` | non-overlapping labels at the lines' ends |
| `register()`, `unregister()` | add or remove the `ax.apply` and `ax.restore` methods |
| `TalbotLocator(n, loose, ...)` | the tick locator, usable on its own |
| `mute(ax, text_ink, line_ink, line_width)` | grey the axis furniture, leaving the data ink alone |
| `tick_direction(ax, direction)` | point the tick marks `in` or `out`, or remove them with `none` |
| `palettes` | Tol's schemes as constants; registers the `tol:` colour names |

Parameters and behavior are documented in the docstrings.

## Credits and prior art

vanzelfsprekend joins a long line of Tufte-in-matplotlib work, and its neighbours deserve direct credit:

- [dufte](https://github.com/nschloe/dufte), since merged into [matplotx](https://github.com/nschloe/matplotx), is the closest kin: the same minimal-ink instinct, and its `line_labels` first framed label placement as a least-squares problem under minimum-distance constraints. vanzelfsprekend solves that same problem, exactly, with the pool-adjacent-violators algorithm.
- [adjustText](https://github.com/Phlya/adjustText), following R's [ggrepel](https://ggrepel.slowkow.com/), tackles the harder general problem of untangling arbitrary 2-D annotations, which takes iterative approximation. Restricting labels to line ends is what lets vanzelfsprekend place them exactly instead.
- [matplotlib-label-lines](https://github.com/cphyc/matplotlib-label-lines) and [matplotlib-inline-labels](https://pypi.org/project/matplotlib-inline-labels/) set labels on the line itself, rotated or curved along it. vanzelfsprekend labels line ends instead; for inline labels, use those.
- [etframes](https://github.com/ahupp/etframes) drew range frames in matplotlib first, part of an older generation of Tufte scripts this library hopes to outlive.
