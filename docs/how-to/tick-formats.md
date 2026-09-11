# Tick formats

*The locator chooses a tick's value and matplotlib writes it; its two rules are Talbot's legibility criterion at work, and the unit belongs in the axis label, once.*

A tick at five million can read `5000000`, `5` with `1e6` in a corner, or `5` under an axis labelled "revenue (millions)". The range frame decides where the tick sits and leaves the writing to matplotlib, which follows two rules that stay invisible until a figure comes out wrong.

## Matplotlib's two rules

The first is a window. From a hundred-thousandth up to a million, every tick is written out in full. Outside it, matplotlib divides all the labels by a common power of ten and parks the factor in the corner of the axes, so revenue from 1 to 9.4 million ticks as `2`, `4`, `6`, `8` with `1e6` sitting in the corner. `axes.formatter.limits` holds the window's edges.

The second fires inside the window, when the data cover a narrow band far from zero. Matplotlib then subtracts a common value as well, so an index hovering around 100 ticks like this:

```
99.900 .. 100.075   →   −0.100  −0.075  −0.050  −0.025  0.000  0.025  ...   +1e2
```

Both rules exist to make the labels shorter. That is Talbot, Lin and Hanrahan's fourth criterion, legibility, which their tick search scores and mizani's leaves out; matplotlib's formatter applies it after the search instead, and [whose decision is which](../explanation/decisions.md) says why the library leaves it there.

## Say it in the label, once

The offset labels are not wrong. They are a claim: that the deviation is what matters and the level is context. For an index that is often exactly right, and the offset makes a comparison legible that `99.900, 99.925, 99.950` would bury. What the formatter cannot know is when the level is the story instead, and it makes its claim silently, with the evidence in a corner the reader may never look at.

So make the claim yourself, and make it where the reader arrives: at the end of the axis, in the label, which is where Tufte and Doumont put a unit rather than on every tick. When the deviation is the story, keep the offset and name it:

```python
ax.plot(year, index)
vzs.apply(ax)
vzs.ylabel(ax, "index (deviation from 100)")
```

When the level is the story, divide the data and name the unit:

```python
ax.plot(year, revenue / 1e6)
vzs.apply(ax)
vzs.ylabel(ax, "revenue (millions)")
```

The ticks read `2` through `8` either way. The difference is that "millions" now sits at the end of the axis in your own words, where `xlabel` and `ylabel` put it, instead of `1e6` in a corner that the range frame does not place: the corner text is matplotlib's, so on a numeric axis it can land far from a spine that stops at the data.

Either rule turns off on its own, after `apply`:

```python
ax.ticklabel_format(axis="y", useOffset=False)  # no common value subtracted
ax.ticklabel_format(axis="y", style="plain")  # no common factor divided out
```

For a whole figure or session, `axes.formatter.useoffset` and `axes.formatter.limits` do the same as rc parameters.

## Dates

A date axis gets the same treatment from a different formatter. `apply` installs `ConciseDateFormatter`, so the labels shorten to what changes between ticks, a run of months does not repeat the year, and the shared year is the offset rule in date form: it moves to the right end of the bottom spine, where `xlabel` goes, and stacks above an `xlabel` if you set one. The ticks themselves sit on calendar starts, a year, a month, a day, chosen by the [locator](locators.md).

Where every tick should carry the same stamp, set a formatter after `apply`:

```python
import matplotlib.dates as mdates

ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))  # Jan 26, Apr 26
```
