# Changelog

## Unreleased

Furniture:
- Gridlines come off with the rest of the axis furniture, so a plot drawn under a grid theme like seaborn's whitegrid distills to a clean frame
- The bottom and left tick marks are kept even when a theme has switched them off, so each tick label still has a mark to sit against

Labels:
- line_labels takes a labels= list to set the text itself, for plots where the drawing library keeps the legend text on a separate artist from the line, as seaborn does; with no line to label it now warns instead of doing nothing
- line_labels hides the legend it replaces, rather than leaving both on the axes
- On a date axis the shared year that ConciseDateFormatter prints once, the "2016" under the ticks, now sits at the right end of the bottom spine where the x label goes, and stacks above an x label when you set one

## 0.1.0

First release.

Range frame:
- The top and right spines are gone, and the two that remain end at the data, so each spine shows its variable's span
- Three ways to end them: at the outermost ticks (the default), at the exact data extremes, or at round numbers just beyond the data, settable per axis
- The remaining spines can stand off the data by a chosen distance, set per axis, so a loose frame reads as a reference scale rather than the data's own edge
- Ticks land on round numbers strictly inside the data range, computed from the data rather than the view limits
- Works on linear, log and date axes; any other scale is left alone with a warning

Ticks:
- Ticks can mark meaningful values instead of round numbers: the five-number summary (QuartileLocator), any reduction of one axis such as its mean (SummaryLocator), or a feature of the paired data such as a peak, x[argmax(y)] (FeatureLocator)
- A feature or reduction is a callable or a fixed number, so a constant mark such as a baseline sits beside a computed one

Labels:
- Axis labels sit at the ends of the spines, and the y label reads horizontally at the top instead of rotated along the side
- The horizontal y label sits beside the top tick, or with place="above" stacks over it with left edges aligned, Doumont's good and better graphs
- The x label ends at the spine, or with flush=True its right edge lines up with the last tick label instead, for a clean right margin
- Line labels replace the legend: each line gets its name at its end, in its own colour, and labels that would collide move apart just far enough to stay readable

Colour:
- The axis furniture fades to grey so the ink goes to the data
- Paul Tol's colour schemes as the default cycle: a single line stays near-black, colour arrives with the second
- The scheme colours work anywhere matplotlib takes a colour, as tol:orange and friends

Undo:
- restore(ax) puts the axes back exactly as they were before distill(ax)
- register() adds a vzs accessor to every axes, so ax.vzs.distill(), ax.vzs.set_xlabel() and the other entry points work anywhere
