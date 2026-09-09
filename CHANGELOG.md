# Changelog

## 0.1.0

First release.

Range frame:
- distill(ax) turns the box around a matplotlib plot into two spines that end at the data, so each spine shows its variable's span
- The spines end at the outermost ticks, at the exact data extremes, or at round numbers just beyond the data, settable per axis and per end of a spine, so a record that begins in 1903 can run from a round 1900 to its last observation
- A spine can stand off the plot by a chosen distance, so a loose frame reads as a reference scale rather than the data's own edge
- Ticks land on round numbers strictly inside the data range, computed from the data rather than the view's padding; a view pinned inside the data crops the frame to the data on screen
- How many ticks an axis carries follows its length and its labels' size, a gap in tick-label heights rather than a fixed count, so a small panel gets few and a poster's large labels thin them out; a count can still be asked for outright
- Linear, log and date axes are handled; anything else is left untouched with a warning
- Panels that share an axis are distilled together, so a sharey pair keeps one scale and every tick lands on a spine; a twin axes is left out with a warning
- Gridlines come off with the rest of the furniture, so a plot drawn under a grid theme like seaborn's whitegrid distills to a clean frame, and the bottom and left tick marks stay even when the theme had switched them off

Ticks:
- Ticks can mark meaningful values instead of round numbers: the data's minimum, quartiles and maximum, a summary of one axis such as its mean, or a feature of the pair such as a peak
- A feature or summary is a callable or a fixed number, so a constant mark such as a baseline sits beside a computed one
- Tick labels that would crowd drift apart just far enough to stay readable; the marks stay at their values
- Tick marks point in or out, or disappear

Labels:
- Axis labels sit at the ends of the spines, the y label horizontal at the top rather than rotated along the side
- The y label stacks above the top tick with left edges aligned, and sits beside it instead when asked, Doumont's better and good graphs; beside is what to reach for when a title already takes the space above the frame
- The x label lines its right edge up with the last tick label, so the label and the tick-label row share one right margin, and falls back to the spine's end when asked
- Line labels replace the legend: each line gets its name at its end, in its own colour, and labels that would collide move apart just far enough to stay readable, keeping their order
- Lines can be labelled at their starts instead, slopegraph-style, and a labels= list names them when the drawing library keeps the legend text away from the line, as seaborn does
- On a date axis the year the tick labels share sits at the right end of the bottom spine, and stacks above an x label when you set one
- label puts one label beside a named line or scatter at a chosen x or y, the text sliding just far enough along a helper line through the anchor to clear every mark and text in its way; right of the anchor by default, and left, above or below when the right is blocked
- The x or y can be a feature of the artist's own points, a callable as the tick locators take, so a label anchors at a peak with the same x[argmax(y)] that marks its tick, and follows the data when it changes
- Several names with one coordinate form a column that stacks in order, and a single point gets a name by being drawn as its own artist; labelling is deliberate, one name per label, never automatic

Small multiples:
- One call treats a grid of axes on a shared scale, per figure, row or column, and keeps spines, ticks and axis labels only on the left column and bottom row

Colour:
- The axis furniture fades to grey so the ink goes to the data
- Marks drawn after distill stay near-black; colour is opted into with a cycle of Paul Tol's colour-blind-safe schemes, minus each scheme's bad-data grey
- The scheme colours work anywhere matplotlib takes a colour, as tol:orange and friends
- The three greys are named by role: one for marks, one for text, one for the frame

Style:
- A "vanzelfsprekend" matplotlib style for the plot you draw yourself: lighter lines, smaller marks, quieter titles. It sets no colour or frame property, so it composes with distill and the colour cycle without overlap

Undo:
- restore(ax) puts the axes back exactly as they were, together with every panel that was distilled with it
- An ax.vzs accessor on every axes, so ax.vzs.distill(), ax.vzs.set_xlabel() and the other entry points work anywhere
