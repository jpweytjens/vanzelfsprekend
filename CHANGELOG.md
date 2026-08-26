# Changelog

## 0.1.0

First release.

Range frame:
- The top and right spines are gone, and the two that remain end at the data, so each spine shows its variable's span
- Three ways to end them: at the outermost ticks (the default), at the exact data extremes, or at round numbers just beyond the data, settable per axis
- Ticks land on round numbers strictly inside the data range, computed from the data rather than the view limits
- Works on linear, log and date axes; any other scale is left alone with a warning

Labels:
- Axis labels sit at the ends of the spines, and the y label reads horizontally at the top instead of rotated along the side
- Line labels replace the legend: each line gets its name at its end, in its own colour, and labels that would collide move apart just far enough to stay readable

Colour:
- The axis furniture fades to grey so the ink goes to the data
- Paul Tol's colour schemes as the default cycle: a single line stays near-black, colour arrives with the second
- The scheme colours work anywhere matplotlib takes a colour, as tol:orange and friends

Undo:
- restore(ax) puts the axes back exactly as they were before apply(ax)
- register() makes both available as methods, ax.apply() and ax.restore(), on every axes
