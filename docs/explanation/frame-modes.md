# Ticks and spines are two decisions

*The locator chooses the ticks from the data; the frame mode chooses where the spine ends; only two of the three modes make the spine follow the ticks.*

matplotlib decides both at once: the view limits set the spine's extent, and the ticks are whatever round numbers fall inside the view. That couples two things that have different jobs. Ticks are for reading values off; the spine's extent is a claim about the data's range. vanzelfsprekend separates them.

The ticks are the locator's. By default that is a Talbot, Lin and Hanrahan search over the data on screen, not over the view, for round numbers inside the data's range, as many as the axis's length in tick-label heights asks for. A locator you set yourself, `QuartileLocator` or `FeatureLocator` or any of matplotlib's, replaces the search and the frame reads your ticks instead.

Where the spine ends is the frame mode's. Under `nice` it ends at the outermost tick, so the spine is exactly the ticks' span and a reader who sees a spine end knows a labelled value sits there. Under `loose` the search is re-run without the stay-inside constraint, so the ticks bracket the data, the spine ends at those bracketing round numbers and stands off the plot to say it is a reference scale rather than the data's edge. Under `data` the spine ends at the data's exact minimum and maximum, a tick sits there only if a locator puts one there, and the spine may run a little past its last tick at each end.

The tuple form lets each spine, and each end of a spine, take its own mode, because a record that starts in 1903 reads better from a round 1900 and should still stop at its last observation. The [frame modes how-to](../how-to/frame-modes.md) has the calls; the frame modes figure in the [gallery](../gallery.md) shows one record under all three.

The vocabulary is the literature's. "Nice" numbers, one, two or five times a power of ten, are Heckbert's from *Graphics Gems*; "loose" is Talbot, Lin and Hanrahan's word for labelling that encloses the data; the range frame is Tufte's.
