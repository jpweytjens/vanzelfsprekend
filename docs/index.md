# vanzelfsprekend

*Above all else show the data.* — Edward Tufte

One call, `vzs.apply(ax)`, gives the axes a range frame and mutes its furniture. The box becomes two spines, each ending at the last labelled tick inside its data, so a spine's end always carries a value. The ticks fall on round numbers inside the data. The furniture fades to grey, and the ink goes to the data. Tufte's own frame, spines running to the data's exact edge, is one keyword away, and `line_labels` puts each line's name at its end, in its own colour, in place of the legend.

The data themselves stay as you drew them. Tufte's line is your job,[^tufte] and the library keeps its hands off it: a line stays where you plotted it, a scatter keeps its colour, a bar its width. Everything around the data is a different matter, and Talbot, Lin and Hanrahan say why in the first sentences of their paper on tick labels.[^talbot]

> The non-data components of a visualization, such as axes and legends, can often be just as important as the data itself. They provide contextual information essential to interpreting the data.

Those are the parts vanzelfsprekend owns, and the only parts.

The library is in the tradition of Tufte's range frame and Doumont's direct labels, with Talbot's tick search doing the counting, and it implements none of them to the letter. The [ideas](explanation/ideas.md) page credits each piece, and the [boundary](explanation/boundary.md) page says what the library will never do and why.

<figure markdown>
![The same global-warming plot twice: matplotlib defaults with a boxed legend on the left, the vanzelfsprekend range frame with each emission scenario labelled at its line's end on the right](warming_scenarios.svg)
<figcaption markdown>The same plotting calls twice. The right panel adds `apply`, `line_labels` in place of the legend, and one `label` on the observed record.</figcaption>
</figure>

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

Install it with `uv add vanzelfsprekend` or `pip install vanzelfsprekend`.

Where to go next: the [tutorial](tutorial/old-faithful.md) builds three figures from scratch. The [how-to](how-to/frame-modes.md) pages answer one question each. The [gallery](gallery.md) shows what the range frame does to real data. The [reference](reference/axes.md) is generated from the docstrings, and the [explanation](explanation/ideas.md) pages say where the ideas come from.

The data are yours and stay as you drew them. The frame, the ticks and the labels are vanzelfsprekend's, and their one job is to show the data.

[^tufte]: Edward R. Tufte, *The Visual Display of Quantitative Information* (Cheshire, Connecticut: Graphics Press, 1983), chapter 4, where the line heads his five principles of data-ink.
[^talbot]: Justin Talbot, Sharon Lin and Pat Hanrahan, ["An Extension of Wilkinson's Algorithm for Positioning Tick Labels on Axes"](http://vis.stanford.edu/papers/tick-labels), *IEEE Transactions on Visualization and Computer Graphics* 16, no. 6 (2010): 1036-1043. The quote opens the abstract.
