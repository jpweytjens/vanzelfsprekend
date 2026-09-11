# vanzelfsprekend

[![PyPI](https://img.shields.io/pypi/v/vanzelfsprekend.svg)](https://pypi.org/project/vanzelfsprekend/)
[![CI](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml/badge.svg)](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/vanzelfsprekend.svg)](https://pypi.org/project/vanzelfsprekend/)
[![License](https://img.shields.io/github/license/jpweytjens/vanzelfsprekend.svg)](https://github.com/jpweytjens/vanzelfsprekend/blob/main/LICENSE)

<img align="right" width="160" src="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/icon/vanzelfsprekend-plotted.svg" alt="Three rising lines in a range frame, labelled v, z and s at their ends; the s line is a sigmoid">

*Above all else show the data.* — Edward Tufte

One call, `vzs.apply(ax)`, gives the axes a range frame and mutes its furniture. The box becomes two spines, each ending at the last labelled tick inside its data, so a spine's end always carries a value. The ticks fall on round numbers inside the data. The furniture fades to grey, and the ink goes to the data. The name is Dutch for self-evident, literally "self-speaking".

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/warming_scenarios-dark.svg">
  <img src="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/warming_scenarios.svg" alt="The same global-warming plot twice: matplotlib defaults with a boxed legend on the left, the vanzelfsprekend range frame with each emission scenario labelled at its line's end on the right">
</picture>

The same plotting calls twice, matplotlib's defaults on the left. The right panel adds `apply`, `line_labels` in place of the legend, and one `label` on the observed record; [the script](https://github.com/jpweytjens/vanzelfsprekend/blob/main/examples/warming_scenarios.py) draws both.

The data are yours: you draw them, and you know which line is the message. Everything around the data is vanzelfsprekend's, to two ends. The range frame is Tufte's and shows the data above all else: each spine ends on a labelled value inside its data, with round numbers between,[^talbot] so the frame reports the range instead of boxing it.[^tufte] The muting and the direct labels are Doumont's and let the figure speak for itself: the furniture goes grey so the data stand out, and each line is named where it ends, so no legend is needed. His caption to a graph he redrew says both at once.[^doumont]

> The graph shows the data and nothing but the data: tick marks are relevant, not arbitrarily equidistant; nondata lines are gray, to make the data prominent.

## Install

```sh
uv add vanzelfsprekend
# or
pip install vanzelfsprekend
```

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
vzs.ylabel(ax, "voltage")
fig.savefig("scatter.png", dpi=150, bbox_inches="tight")
```

`apply` installs a draw hook that keeps the frame glued to the data through autoscaling and tick changes, and `restore(ax)` undoes it exactly.

## Documentation

The [documentation](https://vanzelfsprekend.johannesweytjens.be/) has a [tutorial](https://vanzelfsprekend.johannesweytjens.be/tutorial/old-faithful/) that builds four figures, [how-to](https://vanzelfsprekend.johannesweytjens.be/how-to/frame-modes/) pages that answer one question each, the [gallery](https://vanzelfsprekend.johannesweytjens.be/gallery/), the [reference](https://vanzelfsprekend.johannesweytjens.be/reference/axes/) generated from the docstrings, and the explanation pages on [what the axis answers](https://vanzelfsprekend.johannesweytjens.be/explanation/axis/), [whose decision is which](https://vanzelfsprekend.johannesweytjens.be/explanation/decisions/) and [where the ideas come from](https://vanzelfsprekend.johannesweytjens.be/explanation/ideas/).

The data are yours and [stay as you drew them](https://vanzelfsprekend.johannesweytjens.be/explanation/decisions/). The frame, the ticks and the labels are vanzelfsprekend's, and their one job is to show the data.

[^tufte]: Edward R. Tufte, *The Visual Display of Quantitative Information* (Cheshire, Connecticut: Graphics Press, 1983), chapter 4, where the epigraph heads his five principles of data-ink.
[^doumont]: Jean-luc Doumont, *Trees, Maps, and Theorems: Effective Communication for Rational Minds* (Brussels: Principiae, 2009), from the caption to the graph he redraws.
[^talbot]: The round numbers are chosen by Talbot, Lin and Hanrahan's search, and their paper opens with Doumont's point from the other side: "The non-data components of a visualization, such as axes and legends, can often be just as important as the data itself." Justin Talbot, Sharon Lin and Pat Hanrahan, ["An Extension of Wilkinson's Algorithm for Positioning Tick Labels on Axes"](http://vis.stanford.edu/papers/tick-labels), *IEEE Transactions on Visualization and Computer Graphics* 16, no. 6 (2010): 1036-1043.
