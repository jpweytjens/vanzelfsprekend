# vanzelfsprekend

[![PyPI](https://img.shields.io/pypi/v/vanzelfsprekend.svg)](https://pypi.org/project/vanzelfsprekend/)
[![CI](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml/badge.svg)](https://github.com/jpweytjens/vanzelfsprekend/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/vanzelfsprekend.svg)](https://pypi.org/project/vanzelfsprekend/)
[![License](https://img.shields.io/github/license/jpweytjens/vanzelfsprekend.svg)](https://github.com/jpweytjens/vanzelfsprekend/blob/main/LICENSE)

<img align="right" width="160" src="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/icon/vanzelfsprekend-plotted.svg" alt="Three rising lines in a range frame, labelled v, z and s at their ends; the s line is a sigmoid">

*Above all else show the data.* — Edward Tufte

vanzelfsprekend does three things to show the data. It frames them, mutes the furniture around them, and accents the features you name. The name is Dutch for self-evident, literally "self-speaking".

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/warming_scenarios-dark.svg">
  <img src="https://raw.githubusercontent.com/jpweytjens/vanzelfsprekend/main/docs/warming_scenarios.svg" alt="The same global-warming plot twice: matplotlib defaults with a boxed legend on the left, the vanzelfsprekend range frame with each emission scenario labelled at its line's end on the right">
</picture>

The same plotting calls twice, matplotlib's defaults on the left. The right panel adds `apply`, `line_labels` in place of the legend, and one `label` on the observed record; [the script](https://github.com/jpweytjens/vanzelfsprekend/blob/main/examples/warming_scenarios.py) draws both.

It frames the data. The box becomes two spines, each ending at the last labelled tick inside its data, so a spine's end always carries a value. Between the ends the ticks fall on round numbers,[^talbot] chosen by a [locator](https://vanzelfsprekend.johannesweytjens.be/how-to/locators/) that reads the data rather than the view limits.

It mutes the furniture. The spines, tick marks and labels go grey and the grid goes, so the data carry the only dark ink on the page. `ax.vzs.apply()` does these first two in one call.

It accents the features. A line is named where it ends instead of in a legend (`line_labels`), a point you name gets a label beside it in the plot (`label`), and a feature the locator already ticks, a peak or a median, gets its tick label pulled forward in colour (`accent`).

The marks stay yours throughout. The library never moves, resizes or recolours a mark you drew, so it can read a finished figure, and `restore` puts everything back. [Furniture and meaning](https://vanzelfsprekend.johannesweytjens.be/explanation/furniture/) draws that line.

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
ax.vzs.apply()
ax.vzs.set_xlabel("time (s)")
ax.vzs.set_ylabel("voltage")
fig.savefig("scatter.png", dpi=150, bbox_inches="tight")
```

`apply` installs a draw hook that keeps the frame glued to the data through autoscaling and tick changes, and `ax.vzs.restore()` undoes it exactly.

## Documentation

The [documentation](https://vanzelfsprekend.johannesweytjens.be/) has a [tutorial](https://vanzelfsprekend.johannesweytjens.be/tutorial/old-faithful/) that builds six figures, [how-to](https://vanzelfsprekend.johannesweytjens.be/how-to/) pages that answer one question each, the [gallery](https://vanzelfsprekend.johannesweytjens.be/gallery/), the [reference](https://vanzelfsprekend.johannesweytjens.be/reference/axes/) generated from the docstrings, and the explanation pages: [What to accent](https://vanzelfsprekend.johannesweytjens.be/explanation/accent/) says what the furniture is for, [The frame follows the axes](https://vanzelfsprekend.johannesweytjens.be/explanation/hook/) why the order of your calls is free, and [Sources and influences](https://vanzelfsprekend.johannesweytjens.be/explanation/sources/) where the ideas come from.

The frame is Tufte's,[^tufte] the muting and the labels are Doumont's,[^doumont] and his caption to a graph he redrew says the first two in one line.

> The graph shows the data and nothing but the data: tick marks are relevant, not arbitrarily equidistant; nondata lines are gray, to make the data prominent.

[^tufte]: Edward R. Tufte, *The Visual Display of Quantitative Information* (Cheshire, Connecticut: Graphics Press, 1983), chapter 4, where the epigraph heads his five principles of data-ink.
[^doumont]: Jean-luc Doumont, *Trees, Maps, and Theorems: Effective Communication for Rational Minds* (Brussels: Principiae, 2009), from the caption to the graph he redraws.
[^talbot]: The round numbers are Talbot, Lin and Hanrahan's search, and their paper opens with the reason the choice deserves one: "The non-data components of a visualization, such as axes and legends, can often be just as important as the data itself." Justin Talbot, Sharon Lin and Pat Hanrahan, ["An Extension of Wilkinson's Algorithm for Positioning Tick Labels on Axes"](http://vis.stanford.edu/papers/tick-labels), *IEEE Transactions on Visualization and Computer Graphics* 16, no. 6 (2010): 1036-1043.
