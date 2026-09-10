# vanzelfsprekend

*Above all else show the data.*

The line is Tufte's, and the data are yours. vanzelfsprekend takes an axes you have already drawn and touches no mark on it: a line stays where you plotted it, a scatter keeps its colour, a bar its width. What it does touch is everything else, and everything else is not decoration. [Talbot, Lin and Hanrahan](http://vis.stanford.edu/papers/tick-labels) open their paper on tick labels with the reason: "The non-data components of a visualization, such as axes and legends, can often be just as important as the data itself. They provide contextual information essential to interpreting the data." Axes and legends are exactly the parts vanzelfsprekend owns.

The box becomes two spines that end where the data ends, so each spine shows its variable's span. The ticks fall on round numbers inside that span. The legend goes, and each line is named at its end in its own colour. The furniture fades to grey, and the ink goes to the data.

The treatment is in the tradition of Tufte's range frame and Doumont's direct labels, with Talbot's tick search doing the counting, and it implements none of them to the letter. The [ideas](explanation/ideas.md) page credits each piece, and the [boundary](explanation/boundary.md) page says what the library will never do and why.

<figure markdown>
![The same global-warming plot twice: matplotlib defaults with a boxed legend on the left, the vanzelfsprekend treatment with each emission scenario labelled at its line's end on the right](figures/warming_scenarios.svg)
<figcaption markdown>The same plotting calls twice. The right panel adds one call, and the legend becomes labels at the line ends.</figcaption>
</figure>

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

Install it with `uv add vanzelfsprekend` or `pip install vanzelfsprekend`.

Where to go next: the [tutorial](tutorial/old-faithful.md) builds three figures from scratch. The [how-to](how-to/frame-modes.md) pages answer one question each. The [gallery](gallery.md) shows what the treatment does to real data. The [reference](reference/axes.md) is generated from the docstrings, and the [explanation](explanation/ideas.md) pages say where the ideas come from.
