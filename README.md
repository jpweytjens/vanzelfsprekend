# vanzelfsprekend

[![PyPI](https://img.shields.io/pypi/v/vanzelfsprekend.svg)](https://pypi.org/project/vanzelfsprekend/)
[![CI](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml/badge.svg)](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml)

<img align="right" width="160" src="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/icon/vanzelfsprekend-plotted.png" alt="Three rising lines in a range frame, labelled v, z and s at their ends; the s line is a sigmoid">

Let the plot speak for itself: a matplotlib treatment in the tradition of [Edward Tufte](https://www.edwardtufte.com/book/the-visual-display-of-quantitative-information/) and [Jean-luc Doumont](https://www.principiae.be/). The name is Dutch for self-evident, literally "self-speaking".

One call, `vzs.apply(ax)`, turns a default matplotlib axes into a quiet one where everything left on the page is information. The box around the plot becomes two spines that end at the data, so each spine shows its variable's span. Ticks land on round numbers strictly inside that span. The legend gives way to labels at the lines' ends, each in its line's colour. The axis furniture fades to grey, and the ink goes to the data.

![The same speed-gradient plot twice: matplotlib defaults with a boxed legend on the left, the vanzelfsprekend treatment with direct line labels on the right](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/backsolved_speed.png)

The same plotting calls produce both axes; the right one adds `apply(ax, frame="loose")` and `line_labels(ax)` in place of the legend ([`examples/backsolved_speed.py`](https://github.com/jpweytjens/vanzelfsprekend/blob/main/examples/backsolved_speed.py)).

## Install

```sh
uv add vanzelfsprekend
```

or `pip install vanzelfsprekend`.

## Quickstart

The smallest complete example:

```python
import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

rng = np.random.default_rng(0)
fig, ax = plt.subplots(figsize=(5, 3.5))
ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12, color="0.2")
vzs.apply(ax)
vzs.xlabel(ax, "time (s)")
vzs.ylabel(ax, "voltage", flush=True)
fig.savefig("scatter.png", dpi=150, bbox_inches="tight")
```

`apply` installs a draw hook that keeps the treatment glued to the data through autoscaling and tick changes, and `restore(ax)` undoes it exactly.

## Usage

`apply(ax)` ends the spines at the outermost ticks. Two other modes:

```python
vzs.apply(ax, frame="data")  # spines end at the exact data min and max
vzs.apply(ax, frame="loose")  # spines end at nice numbers bounding the data
```

A tuple sets the modes per spine, `(x, y)`, so a measurement record can end exactly where the data does while the value axis keeps nice bounds:

```python
vzs.apply(ax, frame=("data", "loose"))
```

`xlabel` sits below the right end of the bottom spine; `ylabel` sits horizontal at the top of the left spine. `flush=True` anchors the y-label at the topmost tick label; `labelpad` widens the gap to the tick labels:

```python
vzs.ylabel(ax, "count", flush=True, labelpad=10)
```

`register()` adds a `vzs` accessor to every axes, in the style of pandas and xarray accessors, so the entry points work anywhere as `ax.vzs.apply()`, `ax.vzs.line_labels()` and so on; `unregister()` removes it again. The accessor mimics matplotlib's method names where one exists with the same contract: `ax.vzs.set_xlabel("time (s)")` is `vzs.xlabel(ax, "time (s)")`.

`line_labels` replaces a legend: delete `ax.legend()` and each line gets its `label=` text at its right end, in its line's colour. Where lines converge, the labels shift apart just enough to stay readable, keeping their order. `at="start"` labels the left ends instead, slopegraph-style, which pairs well with `frame="loose"` since the offset spine leaves room for the text:

```python
vzs.line_labels(ax)  # label every line at its right end
vzs.line_labels(ax, at="start")  # and/or at its left end
```

Linear, log and date axes are handled; set the scale before calling `apply`. On a log axis the ticks sit on powers of the base and the minor ticks disappear with them; `ax.xaxis.set_minor_locator(matplotlib.ticker.LogLocator(subs="auto"))` brings the minors back. On a date axis the ticks sit on calendar starts (a year, a month, a day, an hour) and the labels shorten to what changes between ticks, so a run of months does not repeat the year. Anything else (`symlog`, `logit`, categorical axes) is left untouched with a warning. The warning covers the frame and ticks only; `line_labels` places its labels on any scale.

## Gallery

From [`examples/gallery.py`](https://github.com/jpweytjens/vanzelfsprekend/blob/main/examples/gallery.py), which regenerates these figures (`uv run examples/gallery.py`).

Tufte's quartile plot: `frame="data"` ends the spines at the data extremes, and `QuartileLocator` puts the ticks at each variable's minimum, quartiles and maximum:

```python
vzs.apply(ax, frame="data")
ax.xaxis.set_major_locator(vzs.QuartileLocator(x))
ax.xaxis.set_major_formatter("{x:.1f}")
```

![Scatter plot whose spines end at the data extremes, with ticks marking the minimum, quartiles and maximum of each variable](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/quartile_ticks.png)

`frame="loose"` on offset spines, ending at nice numbers that bound the data:

![Scatter plot with offset spines ending at nice numbers just beyond the data](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/scatter_loose.png)

The range frame on a histogram:

![Histogram with trimmed spines and ticks inside the data range](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/histogram.png)

A power law on log-log axes with `frame="loose"`: offset spines end at the powers of ten bounding the data, minor ticks gone:

![Log-log scatter plot of a power law with offset spines ending at powers of ten bounding the data](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/scatter_loglog.png)

The Mauna Loa CO₂ record on a date axis, with per-spine modes `frame=("data", "loose")`: the time spine ends exactly where the record does, the value spine at nice numbers bounding it:

![Line chart of a decade of monthly CO₂ measurements, the bottom spine trimmed to year ticks inside the data range](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/timeseries.png)

## Where the ideas come from

The treatment compresses a few small books' worth of advice:

- The range frame is Tufte's (*The Visual Display of Quantitative Information*): a frame that shows nothing becomes two spines that show each variable's minimum and maximum.
- Direct labels are Doumont's (*Trees, maps and theorems*): a legend sends the reader on a round trip between line and key, and a label at the line's end deletes the detour. The label placement is the exact least-squares optimum under no-overlap constraints, re-solved on every draw via the pool-adjacent-violators algorithm.
- The round-number ticks come from [Talbot, Lin and Hanrahan's extended Wilkinson algorithm](http://vis.stanford.edu/papers/tick-labels), through [mizani](https://mizani.readthedocs.io/en/stable/)'s breaks, computed from the data rather than the view limits.
- The colours are [Paul Tol's](https://sronpersonalpages.nl/~pault/) colour-blind-safe schemes, arranged ink-first: a single series stays near-black, and colour enters at series two of the same kind. `color="tol:orange"` works anywhere matplotlib takes a colour.

vanzelfsprekend also joins a long line of Tufte-in-matplotlib work, and its neighbours deserve direct credit:

- [dufte](https://github.com/nschloe/dufte), since merged into [matplotx](https://github.com/nschloe/matplotx), is the closest kin: the same minimal-ink instinct, and its `line_labels` first framed label placement as a least-squares problem under minimum-distance constraints. vanzelfsprekend solves that same problem, exactly.
- [adjustText](https://github.com/Phlya/adjustText), following R's [ggrepel](https://ggrepel.slowkow.com/), tackles the harder general problem of untangling arbitrary 2-D annotations, which takes iterative approximation. Restricting labels to line ends is what lets vanzelfsprekend place them exactly instead.
- [matplotlib-label-lines](https://github.com/cphyc/matplotlib-label-lines) and [matplotlib-inline-labels](https://pypi.org/project/matplotlib-inline-labels/) set labels on the line itself, rotated or curved along it. vanzelfsprekend labels line ends instead; for inline labels, use those.
- [etframes](https://github.com/ahupp/etframes) drew range frames in matplotlib first, part of an older generation of Tufte scripts this library hopes to outlive.

## API

| Name | Does |
| --- | --- |
| `apply(ax, ...)` | the full treatment with defaults |
| `restore(ax)` | put the axes back as they were |
| `range_frame(ax, frame, n, offset, ...)` | the range frame, with every knob |
| `xlabel(ax, text)`, `ylabel(ax, text, flush)` | end-of-spine axis labels |
| `line_labels(ax, at, labelcolor, pad, gap)` | non-overlapping labels at the lines' ends |
| `register()`, `unregister()` | add or remove the `ax.vzs` accessor |
| `TalbotLocator(n, loose, ...)` | the tick locator, usable on its own |
| `QuartileLocator(data)` | ticks at the data's minimum, quartiles and maximum |
| `LogBreaksLocator(n, loose, base)` | the tick locator for log axes, usable on its own |
| `DateBreaksLocator(n, loose)` | the tick locator for date axes, usable on its own |
| `mute(ax, text_ink, line_ink, line_width)` | grey the axis furniture, leaving the data ink alone |
| `tick_direction(ax, direction)` | point the tick marks `in` or `out`, or remove them with `none` |
| `palettes` | Tol's schemes as constants; registers the `tol:` colour names |

Parameters and behavior are documented in the docstrings.
