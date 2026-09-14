# The labour-income decomposition

*Put the components on one scale so they can be compared, then let the ticks carry what the decomposition found.*

A simulated monthly labour income, split into a permanent component and a transient residual. The permanent component is recovered by penalized median segmentation, a piecewise-constant fit whose segments take their own median; the transient component is what is left. The decomposition is inspired by a working paper on consumption responses to labour income changes,[^wp] simplified here to a clean example. The recurrent June holiday pay and December bonuses fall in the transient component; a one-off raise steps the permanent one. This lesson is about the graphics that make those readable, and it builds the figure one call at a time, as the [grand tours](grand-tours.md) did; the script is `examples/tutorial_income.py`.

[^wp]: Kris Boudt, Koen Schoors, Milan van den Heuvel and Johannes Weytjens, [*Taming the Zoo of Consumption Responses to Labour Income Changes*](https://wps-feb.ugent.be/Papers/wp_23_1067.pdf), Ghent University Working Paper 2023/1067, April 2023.

## The decomposition, in default boxes

```{.python}
--8<-- "tutorial_income.py:draw"
```

<figure markdown>
![Three stacked matplotlib boxes: monthly labour income with a step up partway along, a flat two-level permanent component, and a spiky transient residual inside a dashed band, each panel with its own y range and its own copy of the year axis](../figures/labour_income_step_1.svg)
<figcaption markdown>Step one. Three boxes: labour income, the permanent step and the transient residual. Each panel sets its own y range, so the permanent step floats on a scale of its own and cannot be read against the income it came from.</figcaption>
</figure>

The three series are drawn and nothing reads across them. The permanent panel autoscales to its own two levels, which fills the box but says nothing about how big the raise is against the income around it. A decomposition you cannot compare across is three plots, not one figure.

## The comparison the decomposition needs

```{.python}
--8<-- "tutorial_income.py:compare"
```

<figure markdown>
![The same three panels reduced to two spines each; labour income and the permanent component now on one shared y scale so the permanent step is small against income's swings, the transient residual framed on its own below](../figures/labour_income_step_2.svg)
<figcaption markdown>Step two. Income and the permanent component share one scale, so the raise reads against income's own variation; the transient stands on its own below. Each box drops to two spines and each y label sits at the top of its spine.</figcaption>
</figure>

`small_multiples` frames income and the permanent component together, and `compare="figure"` puts them on one shared scale. The permanent step is now the right size on the page: the raise reads against the month-to-month swing of the income above it, which is the comparison the decomposition was for. The transient residual is a different quantity on a different scale, so it takes its own `apply` and stands alone. Every panel takes the same frame, `(("data", "loose"), "loose")`: the x starts firm at the first month of 2012 and runs loose to a round year at the open end, and the y runs out to round numbers.

## Mark what the decomposition surfaced

```{.python}
--8<-- "tutorial_income.py:mark"
```

<figure markdown>
![The framed figure with the decomposition's own numbers on the axes: the permanent panel ticked at its two recovered levels 8.51 and 8.76, the transient at zero, the June and December bumps and the raise picked out as points, and Jun and Dec marked on the time axis](../figures/labour_income_step_3.svg)
<figcaption markdown>Step three. The ticks now carry the decomposition's own numbers: the permanent panel at its two recovered levels, the transient at zero and at the months it recurs on. The bumps and the raise are marked where they happen.</figcaption>
</figure>

Decomposing the series produced particular numbers, and those are what the axis should carry. `AugmentedLocator` puts them there without giving up the round-number ticks, by unioning the frame's nice ticks with positions you supply. The permanent y gains its two recovered levels, so the raise is the gap between two ticks a reader can read straight off. The transient y gains a zero line, and its x gains the June and December the bumps fall on, named as features so the next step can pick them out. `FeatureLocator` carries those named positions; `set_major_formatter("{x:.2f}")` rounds each panel's y labels, and where a level tick lands beside a round one the two labels separate on their own.

## Name the recurrence

```{.python}
--8<-- "tutorial_income.py:name"
```

<figure markdown>
![The finished figure: the Jun and Dec ticks now in gold and red to match the holiday-pay and bonus points, one holiday pay, one bonus and the raise named beside their points](../figures/labour_income_step_4.svg)
<figcaption markdown>Step four. The June and December ticks take the colours of the bumps they mark, and one holiday pay, one bonus and the raise are named where they happen.</figcaption>
</figure>

`accent` colours the named June and December ticks to match their points, gold for holiday pay and red for the bonus, so an axis mark and the point it stands for read as one thing. `label` then names one holiday pay, one bonus and the raise, each at its own date. Because a name, its tick and its point all share a single anchor date, they cannot drift apart when the figure is redrawn. The colour is data here rather than decoration: holiday pay and the year-end bonus are two kinds of recurrent income, which is why these marks carry colour where the rest of the figure stays in ink.[^robust]

[^robust]: The median cost in the segmentation is what lets the recurrence stay in the transient panel at all. A June bump is larger than the raise but rare within any run of months, so a segment's median steps over it; a least-squares fit would chase the bumps and break the permanent level into steps that were never there.

## What the frame says without a caption

The permanent panel answers "how big was the raise?" with two ticks: 8.51 before, 8.76 after, and the distance between them is the answer. Because that panel shares income's scale, the same raise is visibly small against income's month-to-month swing, so "large or small?" is answered on the page as well as in the number.

The transient panel answers "when does income jump, and by how much?" The zero line is the baseline, the dashed band is the threshold a bump has to clear to count, and the coloured points are the months that clear it. Read down the year axis and the recurrence is plain: a gold June and a red December, every year, in the residual rather than the trend.

## Going further

`small_multiples` set the shared scale here; its [how-to](../how-to/small-multiples.md) has the three `compare` scopes. The union of nice ticks with your own is `AugmentedLocator` and the colouring is `accent`, both in the [locators reference](../reference/locators.md); the [locators how-to](../how-to/locators.md) covers setting your own ticks in general. The [gallery](../gallery.md) has the finished figure among the rest.
