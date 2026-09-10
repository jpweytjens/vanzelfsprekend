# Gallery

*Twelve figures in the order a reader should meet them, from one call to ticks that are the argument.*

Every figure comes from `examples/gallery.py`; regenerate them with `uv run --group examples examples/gallery.py`. The datasets sit in `examples/data`, each file naming its source and licence; what is not a measurement says so.

<figure markdown>
![The same global-warming plot twice: matplotlib defaults with a boxed legend on the left, the vanzelfsprekend treatment with each emission scenario labelled at its line's end on the right](figures/warming_scenarios.svg)
<figcaption markdown>**The warming scenarios.** The same plotting calls twice. One call trims the frame and the legend becomes names at the line ends, the record labelled where it starts.</figcaption>
</figure>

<figure markdown>
![The same rising warming curve three times under the three frame modes](figures/frame_modes.svg)
<figcaption markdown>**One record, three frame modes.** `nice` ends the spines at the outermost ticks, `loose` at round numbers bracketing the data with the spine standing off, `data` at the record's own extremes. The ticks are the same under `nice` and `data`; only the spine ends move. Each panel is titled, so the y label keeps to the side rather than taking the space above the frame.</figcaption>
</figure>

<figure markdown>
![Scatter of Old Faithful eruption length against the wait to the next eruption, two clusters, spines ending at the data's extremes](figures/old_faithful.svg)
<figcaption markdown>**Old Faithful.** The plainest range frame: a scatter under `frame="data"`, each spine reporting one variable's minimum and maximum.</figcaption>
</figure>

<figure markdown>
![Histogram of waiting times between Old Faithful eruptions, two-peaked, with spines running exactly along the bars' span](figures/waiting_times.svg)
<figcaption markdown>**Waiting times.** The same data as a histogram under `frame="data"`, both spines flush with the bars, the geyser's two modes standing clear.</figcaption>
</figure>

<figure markdown>
![Log-log scatter of mammal brain mass against body mass, offset spines ending at powers of ten bounding the data](figures/brain_body.svg)
<figcaption markdown>**Brain and body mass.** Sixty-two mammals on log-log axes under `frame="loose"`: offset spines end at the powers of ten bounding the data, the minor ticks disappear, and the allometry reads as the straight line it is.</figcaption>
</figure>

<figure markdown>
![The same rising warming curve twice, a wide axes with year labels every fifty years and a narrow one with only the first and last, both with the same four temperature ticks](figures/tick_spacing.svg)
<figcaption markdown>**Tick spacing.** The same record at 12 cm and at 2 cm under the same call. The tick count follows the axis's length in tick-label heights, so the wide axes carries four year labels and the narrow one two, and the two y axes agree because they are the same height.</figcaption>
</figure>

<figure markdown>
![Four scatter panels of Anscombe's quartet, each with spines trimmed to its own data and ticks at its own quartiles, differing where the shared statistics cannot](figures/anscombe.svg)
<figcaption markdown>**Anscombe's quartet.** Four sets built to share their summary statistics, under `frame="data"` with `QuartileLocator` ticks. Each panel's spines span its own data and its ticks sit at its own five-number summary, so the axes refuse to repeat the identity; set IV's bottom axis collapses to two marks because ten of its eleven x values are the same number.</figcaption>
</figure>

<figure markdown>
![Four random-walk series that seaborn drew, distilled to two spines with no grid, the legend replaced by A to D at the line ends in their colours and the year shown once at the axis end](figures/seaborn_lineplot.svg)
<figcaption markdown>**A seaborn line plot.** The treatment reads an axes, not the library that filled it. `distill` trims seaborn's `whitegrid` box to two spines and drops the grid; `line_labels` stands in for the legend, with the labels passed in because seaborn keeps its legend text on proxy artists.</figcaption>
</figure>

<figure markdown>
![Four modelled power-duration curves on a log time axis in Tol's muted scheme, crossing at staggered durations and labelled at their flat right ends](figures/power_profiles.svg)
<figcaption markdown>**Power profiles.** Four peer series, so the figure opts into colour the house way: a muted scheme cycle before the loop, no per-line colour strings, and `line_labels` naming each curve in its own colour where they crowd at the right. The model is spelled out in the script; the parameters are illustrative.</figcaption>
</figure>

<figure markdown>
![A sharp resonance peak, black measured points over an orange calculated Lorentzian, x ticks at the band's 16 and 19 GHz edges and the peak's 17.2 GHz](figures/resonance_peak.svg)
<figcaption markdown>**The resonance peak.** After Doumont. `FeatureLocator` marks the band edges and the peak's own frequency; `SummaryLocator` sets a minor tick at half power; and the two labels anchor at the summit and the flank. The [tutorial](tutorial/resonance-peak.md) builds it one call at a time.</figcaption>
</figure>

<figure markdown>
![Three stacked panels of winners' average speeds at the Tour, Giro and Vuelta since 1903, each named at its line's end, each y spine running from that race's slowest to its fastest winner with the median marked between, with gaps during the world wars](figures/grand_tours.svg)
<figcaption markdown>**The grand tours.** Small multiples on one shared scale, each panel ticked at its own race's slowest, median and fastest winner. The wars are holes in every record and the Vuelta's broken start is its own story. The [tutorial](tutorial/grand-tours.md) reads it.</figcaption>
</figure>

<figure markdown>
![A 2x2 grid of monthly CO2 at Barrow, Mauna Loa, Samoa and the South Pole on a shared scale, the seasonal sawtooth shrinking toward the pole, spines and ticks only on the left column and bottom row](figures/small_multiples.svg)
<figcaption markdown>**A small-multiples grid.** Monthly CO₂ at four stations from the Arctic to the South Pole on one shared scale. Only the left column and bottom row keep furniture, so the seasonal swing shrinking toward the pole reads on equal terms.</figcaption>
</figure>

## Which figure shows what

This index is written by hand until the gallery declares its own features; then it is generated from those declarations.

- **One call, `distill`**: every figure; on its own in the warming scenarios and Old Faithful.
- **`frame="data"`**: Old Faithful, waiting times, Anscombe, the grand tours.
- **`frame="loose"` and the spine offset**: brain and body mass, the resonance peak, one panel of the frame modes.
- **Ticks that follow the axis's length**: tick spacing.
- **Ticks as a summary of the data**: Anscombe (`QuartileLocator`), the grand tours (`SummaryLocator`).
- **Ticks as annotation**: the resonance peak (`FeatureLocator`, `SummaryLocator`).
- **Log axes**: brain and body mass, power profiles.
- **Date axes**: the seaborn line plot, the grand tours.
- **A figure another library drew**: the seaborn line plot.
- **Line labels in place of a legend**: the warming scenarios, the seaborn line plot, power profiles, the grand tours.
- **A label beside a point or curve**: the resonance peak.
- **Colour opted in**: power profiles (a scheme cycle), the grand tours (the jerseys).
- **Small multiples**: the grand tours (`compare="column"`), the CO₂ grid.
- **Axis labels raised and flush**: every figure with labels; `place="beside"` where a title takes the space above the frame, in the frame modes and the warming scenarios.
