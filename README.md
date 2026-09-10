# vanzelfsprekend

[![PyPI](https://img.shields.io/pypi/v/vanzelfsprekend.svg)](https://pypi.org/project/vanzelfsprekend/)
[![CI](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml/badge.svg)](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/vanzelfsprekend.svg)](https://pypi.org/project/vanzelfsprekend/)
[![License](https://img.shields.io/github/license/jpweytjens/vanzelfsprekend.svg)](https://github.com/jpweytjens/vanzelfsprekend/blob/main/LICENSE)

<img align="right" width="160" src="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/icon/vanzelfsprekend-plotted.svg" alt="Three rising lines in a range frame, labelled v, z and s at their ends; the s line is a sigmoid">

*Above all else show the data.*

One call, `vzs.distill(ax)`, puts the frame, the ticks and the labels around your data to work for the reader. The box becomes two spines that end where the data ends, so each spine shows its variable's span. The ticks fall on round numbers inside that span. The legend goes, and each line is named at its end in its own colour. The furniture fades to grey, and the ink goes to the data. The name is Dutch for self-evident, literally "self-speaking".

The data themselves stay as you drew them. Tufte's line is your job, and the library keeps its hands off it: a line stays where you plotted it, a scatter keeps its colour, a bar its width. Everything around the data is a different matter. [Talbot, Lin and Hanrahan](http://vis.stanford.edu/papers/tick-labels) open their paper on tick labels with the reason: "The non-data components of a visualization, such as axes and legends, can often be just as important as the data itself. They provide contextual information essential to interpreting the data." Those are the parts vanzelfsprekend owns, and the only parts.

The treatment is in the tradition of [Tufte](https://www.edwardtufte.com/book/the-visual-display-of-quantitative-information/)'s range frame and [Doumont](https://www.principiae.be/)'s direct labels, with Talbot's tick search doing the counting, and it implements none of them to the letter. The docs credit [each piece](https://vanzelfsprekend.johannesweytjens.be/explanation/ideas/) and say [what the library will never do](https://vanzelfsprekend.johannesweytjens.be/explanation/boundary/) and why.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/warming_scenarios-dark.svg">
  <img src="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/warming_scenarios.svg" alt="The same global-warming plot twice: matplotlib defaults with a boxed legend on the left, the vanzelfsprekend treatment with each emission scenario labelled at its line's end on the right">
</picture>

[The script behind the figure](https://github.com/jpweytjens/vanzelfsprekend/blob/main/examples/warming_scenarios.py) produces both axes from the same plotting calls, drawing the observed warming record and the five assessed IPCC scenarios; the right one adds `distill(ax, frame=("data", "loose"))`, `line_labels(ax)` in place of the legend, and `label(ax, "observed", x=1905)` to name the record where it starts.

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

`distill` installs a draw hook that keeps the treatment glued to the data through autoscaling and tick changes, and `restore(ax)` undoes it exactly.

## Documentation

The documentation is at [vanzelfsprekend.johannesweytjens.be](https://vanzelfsprekend.johannesweytjens.be/): a [tutorial](https://vanzelfsprekend.johannesweytjens.be/tutorial/old-faithful/) that builds three figures, [how-to](https://vanzelfsprekend.johannesweytjens.be/how-to/frame-modes/) pages that answer one question each, the [gallery](https://vanzelfsprekend.johannesweytjens.be/gallery/), the [reference](https://vanzelfsprekend.johannesweytjens.be/reference/axes/) generated from the docstrings, and [where the ideas come from](https://vanzelfsprekend.johannesweytjens.be/explanation/ideas/).

The data are yours and stay as you drew them. The frame, the ticks and the labels are vanzelfsprekend's, and their one job is to show the data.
