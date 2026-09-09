# The grand tours

*When the ticks are the slowest, the median and the fastest winner, the axis tells the story and the caption can go.*

A century of winners' average speeds at the Tour de France, the Giro d'Italia and the Vuelta a España, one race per panel. The data are the editions' published averages, compiled in `examples/data/grand_tour_speeds.csv` with its sources. This lesson builds the figure one call at a time, as the resonance peak did; the script is `examples/tutorial_grand_tours.py`.

## The data and the default figure

Each race gets a column in the file and a row of `NaN` where no edition was held, so the gaps stay gaps rather than a line drawn across them.

```{.python}
--8<-- "tutorial_grand_tours.py:data"
```

```{.python}
--8<-- "tutorial_grand_tours.py:draw"
```

<figure markdown>
![Three stacked panels of grand tour speeds in default matplotlib boxes, each with its own y range and a legend in the corner](../figures/grand_tours_step_1.svg)
<figcaption markdown>Step one. Three boxes, three legends, and three y axes that each cover a different range of speeds, so no reading crosses from one panel to the next.</figcaption>
</figure>

## Treat the three panels as one figure

```{.python}
--8<-- "tutorial_grand_tours.py:step2"
```

<figure markdown>
![The same three panels reduced to two spines each on one shared speed scale, the year axis kept only under the bottom panel and one y label serving the column](../figures/grand_tours_step_2.svg)
<figcaption markdown>Step two. One shared scale, one year axis under the bottom panel, one axis label for the column, and each box reduced to two spines.</figcaption>
</figure>

`small_multiples` treats the three axes together rather than one at a time. `compare="column"` scopes the time axis to the column, and since there is one column the three panels come out on one shared scale: every left spine now runs from the slowest winner in any of the three races to the fastest in any of them. The inner furniture goes with it. Only the bottom panel keeps the year axis and only the left column keeps the axis label, because that is where a reader looks for them.

## Tick each race at its own extremes

```{.python}
--8<-- "tutorial_grand_tours.py:step3"
```

<figure markdown>
![The same figure with each panel's y ticks at that race's slowest, median and fastest winner rather than at round numbers](../figures/grand_tours_step_3.svg)
<figcaption markdown>Step three. The round numbers give way to three numbers per race: its slowest winner, its median and its fastest.</figcaption>
</figure>

`SummaryLocator` reduces one axis's own values, here with `nanmin`, `nanmedian` and `nanmax`, so each panel is ticked by its own race while the scale behind it stays common to all three.[^shared] Read the ticks straight down and the question a reader brings is answered: which race is fastest, and by how much.

[^shared]: Because the scale is shared, the comparison is on the page as well as in the numbers: the Tour's top tick sits higher than the Giro's, and the gap between them is to scale.

## Replace the legends with labels

```{.python}
--8<-- "tutorial_grand_tours.py:step4"
```

<figure markdown>
![Three stacked panels of winners' average speeds at the Tour, Giro and Vuelta since 1903, each named at its line's end, each y spine running from that race's slowest to its fastest winner with the median marked between, with gaps during the world wars](../figures/grand_tours_step_4.svg)
<figcaption markdown>Step four. Each race is named at the end of its line, in its jersey's colour, and the three legends go.</figcaption>
</figure>

The colour is the jersey's: yellow, pink and red are the data here, not decoration, which is why these three lines carry colour when most vanzelfsprekend figures stay in ink.

## What the frame says without a caption

The y ticks answer the question a reader brings. Which race is fastest? The top ticks say so. Is the Giro's median higher than the Vuelta's? Two numbers, one glance. No round number sits between them to be read past.

The gaps are data too. Both world wars are holes in every record, because no race was run and the line is not interpolated across the years. The Vuelta starts late, in 1935, and its first decade is broken, which the frame reports by starting the line where the data starts rather than at a round 1900.

## Going further

The scope is `compare`'s to set. `"row"` would give each row its own y scale, so each race would be framed and ticked by its own record alone; every line would then fill its panel and nothing could be read across the three. The [small multiples how-to](../how-to/small-multiples.md) has the three scopes.

That is the tutorial. The [how-to](../how-to/frame-modes.md) pages answer one question each, and the [gallery](../gallery.md) has the full progression of figures.
