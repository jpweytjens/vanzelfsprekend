# The warming scenarios

*The legend goes, each scenario is named where its line ends, and the frame's right end is the last projected year.*

The observed global mean temperature, one point per year since 1850, and the five scenarios the IPCC assessed for the rest of the century, fanning out from the present. The observations are the Met Office's HadCRUT5 record and the scenarios are the best estimates behind figure SPM.8 of the sixth assessment report, both shipped with the examples and each file naming its source. This is the right half of the front page's figure, built one call at a time; the script is `examples/tutorial_warming.py`.

## The data and the default figure

```{.python}
--8<-- "tutorial_warming.py:data"
```

Each file opens with four lines naming its source, which `skip_header` steps over. The record is published against a 1961–1990 mean, and the scenarios against 1850–1900, so the observations are shifted to the scenarios' baseline before the two are drawn together.

```{.python}
--8<-- "tutorial_warming.py:draw"
```

<figure markdown>
![The observed warming record and five scenario lines in a default matplotlib box, a legend of six entries in the corner](../figures/warming_step_1.svg)
<figcaption markdown>Step one. Six entries in a legend, and a reader who wants to know which line is SSP2-4.5 goes to the corner, matches a colour, and comes back.</figcaption>
</figure>

Every mark carries its name in `label=`. The legend reads those names now, and the direct labels will read the same ones later. The colours are [Paul Tol's](../how-to/colour.md), by name.

## Apply the range frame

```{.python}
--8<-- "tutorial_warming.py:step2"
```

<figure markdown>
![The same figure with the box gone: a bottom spine from 1850 to 2100 and a left spine from 0 to 4, both grey](../figures/warming_step_2.svg)
<figcaption markdown>Step two. The bottom spine runs from the first observed year to the last projected one, and the left spine from 0 to 4, the last round numbers inside the data.</figcaption>
</figure>

The two axes get different frame modes because they mean different things. The years are a record with two ends, so `data` runs the bottom spine exactly from 1850 to 2100, past the last tick label at 2050. The degrees are a scale, so `nice` ends the left spine at the outermost round ticks inside the data, and the worst scenario runs past the top of it: SSP5-8.5 goes, literally, off the chart. `loose` would have carried the spine to 5 and covered the line, which is the conventional look and one the spine can drop when the overrun is the story. The [frame modes how-to](../how-to/frame-modes.md) has the three modes side by side. The same call turned the spines and ticks grey; the points and lines are untouched.

## Name the axis

```{.python}
--8<-- "tutorial_warming.py:step3"
```

<figure markdown>
![The same figure with "warming (°C vs 1850–1900)" standing horizontal above the top of the left spine](../figures/warming_step_3.svg)
<figcaption markdown>Step three. The y label stands horizontal above the top tick, where the eye arrives after reading the scale. The years need no label.</figcaption>
</figure>

## Replace the legend with names

```{.python}
--8<-- "tutorial_warming.py:step4"
```

<figure markdown>
![The same figure with the legend gone and each scenario's name at its line's right end, in the line's colour](../figures/warming_step_4.svg)
<figcaption markdown>Step four. Each line's name sits at its end, in its own colour. SSP1-2.6 and SSP1-1.9 end a third of a degree apart, and their names just fit.</figcaption>
</figure>

`line_labels` reads the `label=` of every line on the axes, so the names are the ones the legend showed, and the legend is simply not drawn. Had the two SSP1 lines ended closer, their names would slide apart by the least distance that separates them, and no further, keeping their order. The [direct labels how-to](../how-to/direct-labels.md) has the other end and the other colours.

## Name the record

```{.python}
--8<-- "tutorial_warming.py:step5"
```

<figure markdown>
![The finished figure: "observed" above the early points of the record, five scenario names at the line ends, no legend](../figures/warming_step_5.svg)
<figcaption markdown>Step five. The scatter has no end to be named at, so `label` anchors its name at a year you choose and slides it clear of the points.</figcaption>
</figure>

`line_labels` names lines, and the observations are a scatter, so they get their name from `label`, anchored on the artist called "observed" at 1930. Any year in the flat early record would do; the anchor is yours, and the library decides only how far the text moves to clear the ink.

Next: [the resonance peak](resonance-peak.md), where the ticks stop being round numbers and start being the argument.
