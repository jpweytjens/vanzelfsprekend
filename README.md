# vanzelfsprekend

[![PyPI](https://img.shields.io/pypi/v/vanzelfsprekend.svg)](https://pypi.org/project/vanzelfsprekend/)
[![CI](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml/badge.svg)](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml)

<img align="right" width="160" src="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/icon/vanzelfsprekend-plotted.png" alt="Three rising lines in a range frame, labelled v, z and s at their ends; the s line is a sigmoid">

Distill a matplotlib plot until it speaks for itself: a treatment in the tradition of [Edward Tufte](https://www.edwardtufte.com/book/the-visual-display-of-quantitative-information/) and [Jean-luc Doumont](https://www.principiae.be/). The name is Dutch for self-evident, literally "self-speaking".

One call, `vzs.distill(ax)`, turns a default matplotlib axes into a quiet one where everything left on the page is information. The box around the plot becomes two spines that end at the data, so each spine shows its variable's span. Ticks land on round numbers strictly inside that span. The legend gives way to labels at the lines' ends, each in its line's colour. The axis furniture fades to grey, and the ink goes to the data.

![The same global-warming plot twice: matplotlib defaults with a boxed legend on the left, the vanzelfsprekend treatment with each emission scenario labelled at its line's end on the right](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/warming_scenarios.png)

[The script behind the figure](https://github.com/jpweytjens/vanzelfsprekend/blob/main/examples/warming_scenarios.py) produces both axes from the same plotting calls, drawing the observed warming record and the five assessed IPCC scenarios; the right one adds `distill(ax, frame=("data", "loose"))` and `line_labels(ax)` in place of the legend.

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
vzs.distill(ax)
vzs.xlabel(ax, "time (s)")
vzs.ylabel(ax, "voltage")
fig.savefig("scatter.png", dpi=150, bbox_inches="tight")
```

`distill` installs a draw hook that keeps the treatment glued to the data through autoscaling and tick changes, and `restore(ax)` undoes it exactly. More examples are in the [gallery](#gallery).

## Usage

`distill(ax)` ends the spines at the outermost ticks. Two other modes:

```python
vzs.distill(ax, frame="data")  # spines end at the exact data min and max
vzs.distill(ax, frame="loose")  # spines end at nice numbers bounding the data
```

A tuple sets the modes per spine, `(x, y)`, so a measurement record can end exactly where the data does while the value axis keeps nice bounds:

```python
vzs.distill(ax, frame=("data", "loose"))
```

Under `loose` the spines also stand off the plot by 8 points: a loose frame rounds outward past the data, so the spine is a detached reference scale rather than the data's own edge, and the gap says so (`data` and `nice` sit flush). The `offset` argument sets that gap yourself, in points, and like `frame` takes a tuple `(x, y)` to move the bottom and left spine apart; a `None` in either slot keeps that spine's mode default:

```python
vzs.distill(ax, frame="loose", offset=(8, 2))  # bottom stands well off, left just clear
```

`xlabel` sits below the right end of the bottom spine; `ylabel` sits horizontal at the top of the left spine. `place="beside"` (the default) anchors it level with the top tick label; `place="above"` stacks it over the top tick, its left edge aligned with the tick label's, Doumont's two y-labels, from his "good" and "better" graphs. `labelpad` widens the gap to the tick labels:

```python
vzs.ylabel(ax, "count", labelpad=10)  # beside the top tick (default)
vzs.ylabel(ax, "count", place="above")  # stacked above it, left-aligned
```

Importing `vanzelfsprekend` adds a `vzs` accessor to every axes, in the style of pandas and xarray accessors, so the entry points work anywhere as `ax.vzs.distill()`, `ax.vzs.line_labels()` and so on; `unregister()` removes it again, and `register()` puts it back. The accessor mimics matplotlib's method names where one exists with the same contract: `ax.vzs.set_xlabel("time (s)")` is `vzs.xlabel(ax, "time (s)")`.

`line_labels` replaces a legend: delete `ax.legend()` and each line gets its `label=` text at its right end, in its line's colour. Where lines converge, the labels shift apart just enough to stay readable, keeping their order. `at="start"` labels the left ends instead, slopegraph-style, which pairs well with `frame="loose"` since the offset spine leaves room for the text:

```python
vzs.line_labels(ax)  # label every line at its right end
vzs.line_labels(ax, at="start")  # and/or at its left end
```

Tick labels get the same care: ticks placed by the data, such as `QuartileLocator`'s, can land arbitrarily close, and where their labels crowd they shift apart just enough to stay readable, keeping their order. The tick marks stay exactly at their values.

To place ticks yourself (`QuartileLocator`, `FeatureLocator`, or any matplotlib locator) set it *after* `distill`, which installs the default locator and would otherwise overwrite yours. The frame mode still decides where the spine ends, now reading your ticks: `nice` and `loose` bound it to your outermost ticks, `data` to the data's extent. That is how the resonance figure below holds its spine at 16–19 while the curve spills past.

Linear, log and date axes are handled; set the scale before calling `distill`, and plot date data first, since an axis only becomes a date axis once dates arrive on it. On a log axis the ticks sit on powers of the base and the minor ticks disappear with them; `ax.xaxis.set_minor_locator(matplotlib.ticker.LogLocator(subs="auto"))` brings the minors back. On a date axis the ticks sit on calendar starts (a year, a month, a day, an hour) and the labels shorten to what changes between ticks, so a run of months does not repeat the year. That shared year sits at the right end of the bottom spine, where `xlabel` goes, and stacks above an `xlabel` if you set one. Anything else (`symlog`, `logit`, categorical axes) is left untouched with a warning. The warning covers the frame and ticks only; `line_labels` places its labels on any scale.

Colours come from Paul Tol's schemes. The default cycle is ink-first vibrant (a lone series stays near-black, and colour enters at the second), but any of the eight schemes is one colour string away: a bare `tol:orange` is the vibrant default, and a qualified `tol:scheme.name` (`tol:muted.rose`, `tol:bright.blue`) reaches the rest. `vzs.palettes.SCHEMES` enumerates them in code, and the reference below names every swatch:

![Eight rows of Paul Tol's colour schemes (bright, high-contrast, vibrant, muted, medium-contrast, pale, dark and light), each swatch labelled with the colour name to type after tol:](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/palettes.png)

## Gallery

Every figure below comes from [a single script](https://github.com/jpweytjens/vanzelfsprekend/blob/main/examples/gallery.py); regenerate them with `uv run --group examples examples/gallery.py`. The datasets sit in [`examples/data`](https://github.com/jpweytjens/vanzelfsprekend/tree/main/examples/data), each file naming its source and licence; what is not a measurement says so, from Anscombe's hand-built quartet to the modelled power profiles.

Anscombe's quartet, four sets built to share their summary statistics, with `frame="data"` and `QuartileLocator` ticks. The axes refuse to repeat the identity: each panel's spines span that panel's own data, its ticks sit at its minimum, quartiles and maximum, and set IV's bottom axis collapses to two marks because ten of its eleven x values are the same number:

```python
vzs.distill(ax, frame="data")
ax.xaxis.set_major_locator(vzs.QuartileLocator(x))
ax.xaxis.set_major_formatter("{x:.0f}")
```

![Four scatter panels of Anscombe's quartet, each with spines trimmed to its own data and ticks at its own quartiles, differing where the shared statistics cannot](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/anscombe.png)

A century of grand tour winners' average speeds, each race in its jersey's colour, labelled at the lines' ends. The Tour and the Vuelta arrive too close together for unaided text, so the labels shift just apart; the time spine ends exactly at the first and last editions, and the world wars stay visible as holes in the record:

![Line chart of winners' average speeds at the Tour, Giro and Vuelta since 1903, each line labelled at its right end, with gaps during the world wars](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/grand_tours.png)

A wide-form line chart that seaborn drew, distilled by the same one call: the treatment reads an axes, not the library that filled it, so it reaches a seaborn plot as readily as a bare matplotlib one. The four series are a constructed random walk under seaborn's `whitegrid` theme; `distill` trims the box to two spines, drops the grid, and keeps the tick marks the theme had switched off, while `line_labels` stands in for the legend. seaborn keeps each legend entry's text on a proxy artist away from the drawn line, so the labels come from `labels=` rather than the lines' own names:

```python
with sns.axes_style("whitegrid"):
    ax = sns.lineplot(data=frame, palette="tab10")
vzs.distill(ax, frame=("data", "nice"))
vzs.line_labels(ax, labels=list("ABCD"))
```

![Four random-walk series that seaborn drew, distilled to two spines with no grid, the legend replaced by A to D at the line ends in their colours and the year shown once at the axis end](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/seaborn_lineplot.png)

The brain and body masses of 62 mammal species on log-log axes with `frame="loose"`: offset spines end at the powers of ten bounding the data, the minor ticks disappear, and the allometry reads as the straight line it is:

![Log-log scatter of mammal brain mass against body mass, offset spines ending at powers of ten bounding the data](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/brain_body.png)

Old Faithful's waiting times as a histogram under `frame="data"`, both spines flush with the bars, the geyser's two modes standing clear:

![Histogram of waiting times between Old Faithful eruptions, two-peaked, with spines running exactly along the bars' span](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/waiting_times.png)

The critical-power model for four rider archetypes on a log time axis, drawn in Tol's `bright` scheme instead of the vibrant default; a qualified colour name (`color="tol:bright.blue"`) reaches any scheme. The curves cross at staggered durations, then flatten toward the right to each rider's sustainable power and crowd within a few percent, which is where the end-of-line labels earn their keep; the parameters are illustrative, and the model is spelled out in the script:

![Four modelled power-duration curves on a log time axis in Tol's bright scheme, crossing at staggered durations and labelled at their flat right ends](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/power_profiles.png)

A resonance curve after Doumont, measured points over a calculated Lorentzian that spills past the frame. `FeatureLocator` marks the band edges and, between them, the one place the reader came to find; a feature is a callable or a fixed number, so the `16` and `19` edges sit beside the peak `x[argmax(y)]`, whose tick lands at 17.2 GHz whether or not that is the mean. `SummaryLocator` (the same idea reduced to one axis's own values) sets a minor tick at half power, the level the linewidth is read at. The y-label is stacked above the top tick with `ylabel(ax, ..., place="above")`, the one place Doumont raises his y-label over the spine, his "better graph":

```python
ax.xaxis.set_major_locator(
    vzs.FeatureLocator(x, y, [16, lambda x, y: x[np.argmax(y)], 19])
)
ax.yaxis.set_minor_locator(vzs.SummaryLocator(y, [lambda y: y.max() / 2]))
```

![A sharp resonance peak, black measured points over an orange calculated Lorentzian, x ticks at the band's 16 and 19 GHz edges and the peak's 17.2 GHz](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/resonance_peak.png)

Monthly CO₂ at four NOAA stations from the Arctic to the South Pole in a 2x2 grid under `small_multiples`, sharing one scale. Every panel keeps its plotted line, but only the left column and bottom row keep spines, ticks and axis labels, so the seasonal swing shrinking toward the pole reads on equal terms without repeating furniture:

```python
vzs.small_multiples(axes.flat, ylabel="CO₂ (ppm)")
```

![A 2x2 grid of monthly CO2 at Barrow, Mauna Loa, Samoa and the South Pole on a shared scale, the seasonal sawtooth shrinking toward the pole, spines and ticks only on the left column and bottom row](https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/small_multiples.png)

## Where the ideas come from

The treatment compresses a few small books' worth of advice:

- The range frame is Tufte's (*The Visual Display of Quantitative Information*): a frame that shows nothing becomes two spines that show each variable's minimum and maximum.
- Direct labels are Doumont's (*Trees, maps and theorems*): a legend sends the reader on a round trip between line and key, and a label at the line's end deletes the detour. The label placement is the exact least-squares optimum under no-overlap constraints, re-solved on every draw via the pool-adjacent-violators algorithm.
- The round-number ticks come from [Talbot, Lin and Hanrahan's extended Wilkinson algorithm](http://vis.stanford.edu/papers/tick-labels), through [mizani](https://mizani.readthedocs.io/en/stable/)'s breaks, computed from the data rather than the view limits. The frame modes keep that literature's vocabulary: "nice" numbers (1, 2 or 5 times a power of ten) are [Heckbert's](https://dl.acm.org/doi/10.5555/90767.90783) (*Graphics Gems*, 1990), and "loose" is the paper's word for bounds that enclose the data.
- The colours are [Paul Tol's](https://sronpersonalpages.nl/~pault/) colour-blind-safe schemes, arranged ink-first: a single series stays near-black, and colour enters at series two of the same kind. `color="tol:orange"` works anywhere matplotlib takes a colour.

vanzelfsprekend also joins a long line of Tufte-in-matplotlib work, and its neighbours deserve direct credit:

- [dufte](https://github.com/nschloe/dufte), since merged into [matplotx](https://github.com/nschloe/matplotx), is the closest kin: the same minimal-ink instinct, and its `line_labels` first framed label placement as a least-squares problem under minimum-distance constraints. vanzelfsprekend solves that same problem, exactly.
- [adjustText](https://github.com/Phlya/adjustText), following R's [ggrepel](https://ggrepel.slowkow.com/), tackles the harder general problem of untangling arbitrary 2-D annotations, which takes iterative approximation. Restricting labels to line ends is what lets vanzelfsprekend place them exactly instead.
- [etframes](https://github.com/ahupp/etframes) is the original, drawing range frames in matplotlib since 2007.

## API

### Axes

| Name | Does |
| --- | --- |
| `distill(ax, ...)` | the full treatment with defaults |
| `restore(ax)` | put the axes back as they were |
| `range_frame(ax, frame, n, offset, ...)` | the range frame, with every knob |
| `small_multiples(axes, compare, ...)` | one treatment for a grid of axes on a shared scale |
| `mute(ax, text_ink, line_ink, line_width)` | grey the axis furniture, leaving the data ink alone |
| `tick_direction(ax, direction)` | point the tick marks `in` or `out`, or remove them with `none` |

### Labels

| Name | Does |
| --- | --- |
| `xlabel(ax, text)`, `ylabel(ax, text, place)` | end-of-spine axis labels |
| `line_labels(ax, at, labelcolor, pad, gap)` | non-overlapping labels at the lines' ends |

### Locators

Each works on its own, on any matplotlib axes:

| Name | Does |
| --- | --- |
| `TalbotLocator(n, loose, ...)` | nice-number ticks inside the data range |
| `LogBreaksLocator(n, loose, base)` | the same for log axes |
| `DateBreaksLocator(n, loose)` | the same for date axes |
| `FeatureLocator(x, y, features)` | ticks at features of the pair, each a callable or a fixed number, such as a peak `x[argmax(y)]` |
| `SummaryLocator(values, reducers)` | ticks at summaries of one axis, each a callable or a fixed number, such as its mean |
| `QuartileLocator(data)` | ticks at the data's minimum, quartiles and maximum |

### Palettes

| Name | Does |
| --- | --- |
| `palettes` | Tol's schemes as constants; registers the `tol:` colour names |

### Registration

| Name | Does |
| --- | --- |
| `register()`, `unregister()` | add or remove the `ax.vzs` accessor (import adds it) |

Parameters and behavior are documented in the docstrings.
