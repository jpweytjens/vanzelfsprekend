# Gallery

*Thirteen figures in the order a reader should meet them, from one call to ticks that are the argument.*

Every figure comes from `examples/gallery.py`; regenerate them with `uv run --group examples examples/gallery.py`. The datasets sit in `examples/data`, each file naming its source and licence; what is not a measurement says so.

<figure markdown>
![The same global-warming plot twice: matplotlib defaults with a boxed legend on the left, the vanzelfsprekend range frame with each emission scenario labelled at its line's end on the right](warming_scenarios.svg)
<figcaption markdown>**The warming scenarios.** The same plotting calls twice. [`apply`](reference/axes.md#vanzelfsprekend.apply) trims the frame, [`line_labels`](how-to/direct-labels.md) turns the legend into names at the line ends, and one `label` names the observed record where it starts. The [tutorial](tutorial/warming-scenarios.md) builds the right panel one call at a time.</figcaption>
</figure>

<figure markdown>
![The same rising warming curve three times under the three frame modes](figures/frame_modes.svg)
<figcaption markdown>**One record, three frame modes.** [`nice`](how-to/frame-modes.md) ends the spines at the outermost ticks, `loose` at round numbers bracketing the data with the spine standing off, `data` at the record's own extremes. The ticks are the same under `nice` and `data`; only the spine ends move. Each panel is titled, so the [y label keeps to the side](how-to/axis-labels.md) rather than taking the space above the frame.</figcaption>
</figure>

<figure markdown>
![Scatter of Old Faithful eruption length against the wait to the next eruption, two clusters, spines ending at the data's extremes](figures/old_faithful.svg)
<figcaption markdown>**Old Faithful.** The plainest range frame: a scatter under [`frame="data"`](how-to/frame-modes.md), each spine reporting one variable's minimum and maximum.</figcaption>
</figure>

<figure markdown>
![Histogram of waiting times between Old Faithful eruptions, two-peaked, with spines running exactly along the bars' span](figures/waiting_times.svg)
<figcaption markdown>**Waiting times.** The same data as a histogram under [`frame="data"`](how-to/frame-modes.md), both spines flush with the bars, the geyser's two modes standing clear.</figcaption>
</figure>

<figure markdown>
![Log-log scatter of orbital period against semi-major axis for the eight planets, the points on a straight line of slope three-halves, Earth alone in blue and named, offset spines ending at powers of ten](figures/kepler.svg)
<figcaption markdown>**Kepler's third law.** The eight planets on log-log axes under [`frame="loose"`](how-to/frame-modes.md): offset spines end at the powers of ten bounding the data, and period against semi-major axis falls on the line _T_ = _a_<sup>3/2</sup>. Earth alone takes a colour, and [`label`](how-to/direct-labels.md) names it in that same colour: one mark picked out of the grey. The [tutorial](tutorial/kepler.md) builds it one call at a time.</figcaption>
</figure>

<figure markdown>
![The same rising warming curve twice, a wide axes with year labels every fifty years and a narrow one with only the first and last, both with the same four temperature ticks](figures/tick_spacing.svg)
<figcaption markdown>**Tick spacing.** The same record at 12 cm and at 2 cm under the same call. The tick count follows the axis's length in tick-label heights, so the wide axes carries four year labels and the narrow one two, and the two y axes agree because they are the same height. The [tick spacing how-to](how-to/tick-spacing.md) has the arguments.</figcaption>
</figure>

<figure markdown>
![Four scatter panels of Anscombe's quartet, each with spines trimmed to its own data and ticks at its own quartiles, differing where the shared statistics cannot](figures/anscombe.svg)
<figcaption markdown>**Anscombe's quartet.** Four sets built to share their summary statistics, under [`frame="data"`](how-to/frame-modes.md) with [`QuartileLocator`](how-to/locators.md) ticks. Each panel's spines span its own data and its ticks sit at its own five-number summary, so the axes refuse to repeat the identity; set IV's bottom axis collapses to two marks because ten of its eleven x values are the same number.</figcaption>
</figure>

<figure markdown>
![Four random-walk series that seaborn drew, trimmed to two spines with no grid, the legend replaced by A to D at the line ends in their colours and the year shown once at the axis end](figures/seaborn_lineplot.svg)
<figcaption markdown>**A seaborn line plot.** vanzelfsprekend reads an axes, not the library that filled it. [`apply`](reference/axes.md#vanzelfsprekend.apply) trims seaborn's `whitegrid` box to two spines and drops the grid; [`line_labels`](how-to/direct-labels.md) stands in for the legend, with the labels passed in because seaborn keeps its legend text on proxy artists.</figcaption>
</figure>

<figure markdown>
![Four modelled power-duration curves on a log time axis in Tol's muted scheme, crossing at staggered durations and labelled at their flat right ends](figures/power_profiles.svg)
<figcaption markdown>**Power profiles.** Four peer series, so the figure opts into colour the house way: a [muted scheme cycle](how-to/colour.md) before the loop, no per-line colour strings, and [`line_labels`](how-to/direct-labels.md) naming each curve in its own colour where they crowd at the right. The model is spelled out in the script; the parameters are illustrative.</figcaption>
</figure>

<figure markdown>
![A sharp resonance peak, black measured points over an orange calculated Lorentzian, x ticks at the band's 16 and 19 GHz edges and the peak's 17.2 GHz](figures/resonance_peak.svg)
<figcaption markdown>**The resonance peak.** After Doumont. [`FeatureLocator`](how-to/locators.md) marks the band edges and the peak's own frequency; `SummaryLocator` sets a minor tick at half power; and the [two labels](how-to/direct-labels.md) anchor at the summit and the flank. The [tutorial](tutorial/resonance-peak.md) builds it one call at a time.</figcaption>
</figure>

<figure markdown>
![Phase-shifted sinusoids on an axis ticked in multiples of π, a matching degree axis along the top, the resistor curve picked out and the rest faded](figures/radian_axes.svg)
<figcaption markdown>**Ticks in π.** Phase-shifted voltages on an axis ticked in multiples of π instead of round decimals: `TalbotLocator(unit=...)` runs the nice-number search in units of π, and [`secondary_frame`](reference/axes.md#vanzelfsprekend.secondary_frame) mirrors those ticks as whole degrees along the top. `V_R` is picked out and the other three fade to grey. The [radian-axes how-to](how-to/radian-axes.md) has the arguments.</figcaption>
</figure>

<figure markdown>
![Three stacked panels of winners' average speeds at the Tour, Giro and Vuelta since 1903, each named at its line's end, each y spine running from that race's slowest to its fastest winner with the median marked between, with gaps during the world wars](figures/grand_tours.svg)
<figcaption markdown>**The grand tours.** [Small multiples](how-to/small-multiples.md) on one shared scale, each panel [ticked at its own race's slowest, median and fastest winner](how-to/locators.md). The wars are holes in every record and the Vuelta's broken start is its own story. The [tutorial](tutorial/grand-tours.md) reads it.</figcaption>
</figure>

<figure markdown>
![A 2x2 grid of monthly CO2 at Barrow, Mauna Loa, Samoa and the South Pole on a shared scale, the seasonal sawtooth shrinking toward the pole, spines and ticks only on the left column and bottom row](figures/small_multiples.svg)
<figcaption markdown>**A small-multiples grid.** Monthly CO₂ at four stations from the Arctic to the South Pole on [one shared scale](how-to/small-multiples.md). Only the left column and bottom row keep furniture, so the seasonal swing shrinking toward the pole reads on equal terms.</figcaption>
</figure>
