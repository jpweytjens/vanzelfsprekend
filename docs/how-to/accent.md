# Accent

*Pull a feature tick forward: colour its label, name it, or show it alone.*

A locator that places a tick at a feature, a peak or a median, puts a number on the axis where the reader is looking. `accent` makes that number the one they see first. It reads the feature names off the locator you installed (`FeatureLocator`, `SummaryLocator` or `AugmentedLocator`) and colours those ticks' labels, leaving the tick marks in the frame colour. [What to accent](../explanation/accent.md) is the argument for doing it; this page is the calls.

## Colour the feature ticks

```{.python}
--8<-- "gallery.py:accented_peak"
```

<figure markdown>
![A resonance curve whose x axis is ticked at round numbers and at the peak's own frequency, the peak's label in the accent colour](../figures/accented_peak.svg)
<figcaption markdown>The peak's frequency is one of the ticks; `accent` colours its label and nothing else.</figcaption>
</figure>

With no arguments, `accent` colours every named feature on every axis that has one, in the accent ink. `at=` picks a subset, by name (`at=["peak"]`) or by position, and `color=` takes one colour for all of them or a name-to-colour map, `color={"Jun": "tol:gold", "Dec": "tol:red"}`, when each feature has its own meaning. `axis="x"` or `"y"` confines it to one axis.

## Name the tick instead of the value

`label="name"` writes the feature's name where its value was, so the tick reads "peak" rather than "17.2", and `label="both"` writes both. The value's formatting stays matplotlib's: the range frame [never rewrites a tick label](tick-formats.md), and `accent` only chooses which text and colour it gets.

## Show only the features

`only_features=True` drops the round-number labels and leaves the features, for an axis where the marks are the whole message. The round numbers' tick marks stay, so the scale is still there to read against.

## What it does not do

`accent` adds no tick. The locator places the ticks and names them; `accent` reads the names and colours the labels. To put a tick at a value, install a [locator](locators.md) that has it. Like the frame, the accent re-applies on every draw, so it survives a resize or a re-tick, and `restore` reverts it. The [labour-income decomposition](../tutorial/labour-income.md) uses it on three panels at once, one colour per feature.
