# What to accent

*Compared to what?[^compare] A graph answers a comparison. In one graph the ticks can carry it, and across graphs a shared scale.*

A graph, like a paragraph, is there to answer a question.[^doumont] Doumont lists the usual ones: how items compare, how values spread along a scale, how two variables relate, how one changes over time. One level up sits the comparison of comparisons, how those answers differ across subsets of the data. The marks carry the data. The furniture around them decides how easily the question gets answered, and the furniture is the part vanzelfsprekend owns. The [accent how-to](../how-to/accent.md) has the calls.

## Ticks that answer the question

A default axis ticks at round numbers whether or not the data reach them, which answers no question in particular. Ticks that sit where the reader is looking answer the graph's own. The [resonance peak](../tutorial/resonance-peak.md) ticks at the band's edges and at the peak's measured frequency, so the reader finds the resonance on the axis instead of estimating it between 17 and 18. The [grand tours](../tutorial/grand-tours.md) tick each race at its slowest, median and fastest winner, so the axis says what a caption would have. Each is one locator: `FeatureLocator` for the peak, set before or after `apply` on its lone axes, and `SummaryLocator` for the winners, set after `small_multiples` on its panels, and the frame reads them like any other ticks. The [locators how-to](../how-to/locators.md) has the calls.

The spine's end can say something too. Under `nice` the spine stops at the last round tick inside the data, and in the [warming scenarios](../tutorial/warming-scenarios.md) the worst one runs past it: SSP5-8.5 goes, literally, off the chart. A spine carried on to 5 would have covered the line and said nothing.

The names are the last of it. A legend answers "which line is this" by a round trip to the corner. A name at the line's end answers it where the line is.

## Panels compare on one scale

Comparing comparisons takes panels, and panels compare only on a shared scale. `small_multiples` frames a grid on one x and one y by default, so a line that fills its panel is fast and a line that sits low is slow, across the whole figure. The grand tours read across three races only because of that. Framed each by its own record, every line would fill its panel, and the question "which race is fastest" would have no answer on the page. The scope, `"figure"`, `"column"` or `"row"`, is the choice of which comparison the reader is meant to make, and the [small multiples how-to](../how-to/small-multiples.md) has the three.

## What to accent is yours

None of this the library can choose. It cannot know whether the peak or the band matters, whether the slowest winner is a story, whether three races are to be compared or read alone. The locator, the anchor and the scope are yours. The library's part is that once you have chosen, the frame, the ticks and the labels make the answer legible without a caption. [Furniture and meaning](furniture.md) draws that line in full.

[^doumont]: Jean-luc Doumont, *Trees, Maps, and Theorems: Effective Communication for Rational Minds* (Brussels: Principiae, 2009), on graphs, where the list of questions opens the discussion.
[^compare]: Edward R. Tufte, *Envisioning Information* (Cheshire, Connecticut: Graphics Press, 1990), the small multiples chapter, where the question a small multiple answers is put this way; and *Beautiful Evidence* (Cheshire, Connecticut: Graphics Press, 2006), the first principle of analytical design, "Show comparisons, contrasts, differences", with his gloss that in experiments, regressions and evidence-based reasoning alike the essential point is to make appropriate comparisons.
