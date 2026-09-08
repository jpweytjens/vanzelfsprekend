# What vanzelfsprekend never does

*It owns the frame and never positions or recolours a mark, so what you drew is what the reader sees.*

vanzelfsprekend has one sentence of scope. It owns the furniture: spines, ticks, tick labels, axis labels, and the labels it adds itself. It never moves, resizes or recolours a mark you drew. A line stays where you plotted it, a scatter keeps its colour, a bar its width.

The rule is what makes the treatment safe to apply to a finished figure. `distill` can read any axes, from a bare `plt.plot` to a seaborn grid, because it has nothing to say about the marks and so nothing to get wrong about them. It is also what makes `restore` exact: the treatment only ever touched things it can put back.

Two things follow that look like omissions and are not.

Colour is yours. The library installs a neutral ink cycle so a lone series stays near-black, and it registers Paul Tol's schemes under `tol:` so colour is one word away, but it never decides which series gets which colour. In the grand tours the yellow, pink and red are the jerseys; an automatic recolouring would have overwritten meaning with decoration, and no library can tell "yellow because careless" from "yellow because Tour de France".

Labels are named, not found. `line_labels` reads the `label=` you gave each line, and `label` places the text you name beside the artist you name. Naming many points in one cloud, the problem [adjustText](https://github.com/Phlya/adjustText) and [textalloc](https://github.com/ckjellson/textalloc) solve, is a different task, and vanzelfsprekend does not attempt it. What it does instead is exact: a label anchored where you say and slid the minimum distance to clear the other ink, solved rather than iterated.

The boundary is also why there is no bar-chart or categorical treatment yet. Positioning bars is drawing, and drawing is on the other side of the line; a categorical frame that respects the rule is work for a later release.
