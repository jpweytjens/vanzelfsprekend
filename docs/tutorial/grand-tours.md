# The grand tours

*When the ticks are the slowest, the median and the fastest winner, the axis tells the story and the caption can go.*

A century of winners' average speeds at the Tour de France, the Giro d'Italia and the Vuelta a España, one race per panel. The data are the editions' published averages, compiled in `examples/data/grand_tour_speeds.csv` with its sources.

## Three panels, one time axis

```{.python}
--8<-- "gallery.py:grand_tours"
```

`small_multiples` treats the three axes together. `compare="column"` shares the time axis down the column and gives each race its own y scale, so every panel's left spine is that race's range frame. Under `frame="data"` the spine runs from the slowest winner to the fastest, and `SummaryLocator` puts a tick at each end and one at the median.

<figure markdown>
![Three stacked panels of winners' average speeds at the Tour, Giro and Vuelta since 1903, each named at its line's end, each y spine running from that race's slowest to its fastest winner with the median marked between, with gaps during the world wars](../figures/grand_tours.svg)
<figcaption markdown>Read the y ticks straight down: the Tour's slowest, median and fastest winner against the Giro's and the Vuelta's, without a round number between them.</figcaption>
</figure>

## What the frame says without a caption

The y ticks answer the question a reader brings. Which race is fastest? The top ticks say so. Is the Giro's median higher than the Vuelta's? Two numbers, one glance. No round number sits between them to be read past.

The gaps are data too. Both world wars are holes in every record, because no race was run and the line is not interpolated across the years. The Vuelta starts late, in 1935, and its first decade is broken, which the frame reports by starting the spine where the data starts rather than at a round 1900.

The line labels replace the legend. Each race is named at the end of its line, in its colour, and the colour is the jersey's: yellow, pink and red are the data here, not decoration, which is why these three lines carry colour when most vanzelfsprekend figures stay in ink.

## Going further

Change `compare="column"` to `compare="figure"` and every panel shares one y scale; the Vuelta's early slowness then reads against the Tour's on equal terms, and the ticks come from the union of the three records. The [small multiples how-to](../how-to/small-multiples.md) has the three scopes.

That is the tutorial. The [how-to](../how-to/frame-modes.md) pages answer one question each, and the [gallery](../gallery.md) has the full progression of figures.
