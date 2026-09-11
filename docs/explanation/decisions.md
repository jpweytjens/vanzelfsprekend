# Whose decision is which

*The marks are yours. The frame and the ticks are the library's, and they are two decisions, not one. Anything that says what a number means stays yours.*

[What the axis answers](axis.md) says what the furniture is for. This page says who decides each part of it, because that answer is what makes the library safe to apply to a finished figure.

## The marks are yours

vanzelfsprekend never moves, resizes or recolours a mark you drew. A line stays where you plotted it, a scatter keeps its colour, a bar its width. That is why `apply` can read any axes, from a bare `plt.plot` to a seaborn grid: it has nothing to say about the marks and so nothing to get wrong about them. It is also what makes `restore` exact, since the library only ever touched things it can put back.

## The furniture is the library's, and it is two decisions

matplotlib decides the spine and the ticks at once: the view limits set the spine's extent, and the ticks are whatever round numbers fall inside the view. Those are two jobs. Ticks are for reading values off; the spine's extent is a claim about the data's range. vanzelfsprekend separates them.

The ticks are the locator's. By default that is Talbot, Lin and Hanrahan's search, run over the data on screen rather than the view, for round numbers inside the data's range, as many as the axis's length in tick-label heights asks for. A locator you set yourself replaces the search, and the frame reads your ticks instead.

Where the spine ends is the frame mode's. Under `nice` it ends at the outermost tick, so a spine end always carries a labelled value. Under `loose` the search is re-run without the stay-inside constraint, so the ticks bracket the data, the spine ends on those bracketing numbers and stands off the plot to say it is a reference scale rather than the data's edge. Under `data` the spine ends at the data's exact extremes, a tick sits there only if a locator puts one there, and the spine may run a little past its last tick. Each spine, and each end of a spine, can take its own mode, because a record that starts in 1903 reads better from a round 1900 and should still stop at its last observation. The [frame modes how-to](../how-to/frame-modes.md) has the calls.

## Meaning stays yours

Three things look like omissions and are one rule. A choice that says what the reader should compare is a claim about meaning, and the library makes none.

Colour is yours. The neutral ink cycle keeps a lone series near-black, and Paul Tol's schemes are one word away under `tol:`, but which series gets which colour is never decided for you. In the grand tours the yellow, pink and red are the jerseys; a recolouring would have overwritten meaning with decoration, and no library can tell "yellow because careless" from "yellow because Tour de France".

Labels are named, not found. `line_labels` reads the `label=` you gave each line, and `label` places the text you name beside the artist you name, anchored where you say. Naming many points in one cloud, the problem [adjustText](https://github.com/Phlya/adjustText) and [textalloc](https://github.com/ckjellson/textalloc) solve, is a different task, and vanzelfsprekend does not attempt it. What it does instead is exact: a label slid the minimum distance to clear the other ink, solved rather than iterated.

How a number reads is yours as well. A tick at five million can be written `5000000`, `5M`, or `5` under a label that says millions, and each is a further claim about what the reader is comparing. Matplotlib's formatter makes that claim already, and vanzelfsprekend does not overrule it; the [tick formats how-to](../how-to/tick-formats.md) has its two rules and how to take the decision back.[^legibility]

The same rule is why bar charts and categorical axes are not handled yet. Positioning bars is drawing, and drawing is on the other side of the line; a categorical frame that respects the rule is work for a later release.

[^legibility]: Talbot's search scores a fourth criterion, legibility, which rates label format, font size, orientation and overlap together, and the library holds it at the constant mizani ships. Three of the four have nothing to weigh here: the labels stay horizontal, the count already comes from the label height so they never crowd, and a font shrinking to fit would fight the size you set. That leaves format, which is the claim above.
