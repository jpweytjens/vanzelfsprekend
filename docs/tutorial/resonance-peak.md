# The resonance peak

*Ticks can sit where the reader is looking, and then the axis annotates the figure.*

Jean-luc Doumont's *Trees, maps and theorems* redraws a resonance curve three times, from the software's default to a version where every mark on the page earns its place. This lesson follows his sequence with vanzelfsprekend, one call per step, so you can see what each one buys. The curve is a Lorentzian with sampled points around it, a construction rather than a measurement, and the script is `examples/tutorial_resonance.py`.

## The data and the default figure

```{.python}
--8<-- "tutorial_resonance.py:data"
```

```{.python}
--8<-- "tutorial_resonance.py:draw"
```

<figure markdown>
![A resonance curve with sampled points in a default matplotlib box, a legend in the corner](../figures/resonance_step_1.svg)
<figcaption markdown>Step one. The frame reaches round numbers the data never touches, and the legend sends the eye to the corner and back.</figcaption>
</figure>

## Trim the frame

```{.python}
--8<-- "tutorial_resonance.py:step2"
```

<figure markdown>
![The same curve with two spines standing off the plot, ending at round numbers just outside the data](../figures/resonance_step_2.svg)
<figcaption markdown>Step two. `loose` ends each spine at the round number just past the data, and the offset stands the spines off the plot to say they are a reference scale, not the data's edge.</figcaption>
</figure>

The bottom spine stands 24 points off and the left spine sits 6 points inside, which is where Doumont puts them: the frequency axis is a scale read against, the power axis is a baseline the curve rises from.

## Move the labels to the spine ends

```{.python}
--8<-- "tutorial_resonance.py:step3"
```

<figure markdown>
![The same figure with the x label flush under the spine's right end and the y label stacked above the top tick](../figures/resonance_step_3.svg)
<figcaption markdown>Step three. `flush` puts the x label under the spine's end. `place="above"` stacks the y label over the top tick, Doumont's raised label from his "better" graph.</figcaption>
</figure>

## Put the ticks where the reader looks

```{.python}
--8<-- "tutorial_resonance.py:step4"
```

<figure markdown>
![The same figure with x ticks at 16, 17.2 and 19 and y ticks at 0 and the peak, a minor tick at half power](../figures/resonance_step_4.svg)
<figcaption markdown>Step four. The x ticks mark the band edges and the peak's own frequency. The y ticks mark zero and the maximum, with a minor tick at half power, where the linewidth is read.</figcaption>
</figure>

`FeatureLocator` takes fixed numbers and callables in one list. The `16` and `19` are the band edges; the callable finds the frequency of the highest measured point, 17.2 GHz here. A tick at the peak is worth more than a tick at 17 because the peak is what the reader came to find. `SummaryLocator` is the same idea over one axis's own values, and it sets the half-power minor tick. Inward ticks keep the marks off the labels now that the labels do the talking.

## Replace the legend with labels

```{.python}
--8<-- "tutorial_resonance.py:step5"
```

<figure markdown>
![The finished figure: "measured" beside the topmost point and "calculated" beside the right flank, no legend](../figures/resonance_step_5.svg)
<figcaption markdown>Step five. Each label anchors where Doumont puts it, the summit for the points and the flank for the curve, and slides just far enough to clear the ink.</figcaption>
</figure>

`label` takes the same features as `FeatureLocator`, so "measured" anchors at the summit with the peak's own `x[argmax(y)]` and "calculated" at a fixed frequency on the flank. You name each label and choose its anchor; the library decides only how far the text moves.

Next: [the grand tours](grand-tours.md), where the ticks summarise a century of data and three panels tell three stories.
