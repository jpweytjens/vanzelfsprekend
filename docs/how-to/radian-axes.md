# Radian axes

*Count ticks in π by giving the locator a `unit`, write the fractions with a formatter that reads the same π, and add the degree axis on top with one call.*

A radian axis wants its ticks on fractions of π, but the default locator counts in decimals and lands them on `0, 2, 4, 6`. Give `TalbotLocator` a `unit` and it counts in that unit instead: `TalbotLocator(unit=np.pi)` puts the ticks on `0, π, 2π, 3π, 4π`, the multiples of π the [Talbot search](../reference/locators.md) settles on once π is its counting step. Set it *after* `apply` (or `range_frame`), the way [every locator goes on after the frame](locators.md), since `apply` installs the default locator and would otherwise overwrite yours.

The locator places the ticks; matplotlib still writes them, and left alone it writes the raw number, `3.14`, not `π`. Turning the value into "π/2" is a `FuncFormatter` you supply, because the library ships none: a tick label [stays a string matplotlib wrote](tick-formats.md), and the range frame does not touch it. This names π twice, once as the locator's `unit` and once inside the formatter that divides by π to find the fraction, and nothing makes the two agree. So declare π once and read it in both places. The snippet's `pi = np.pi` is that single authority; change it and the ticks and their labels move together, where two separate literals would drift apart the moment one was edited.

The degree axis on top is `vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))`, the pair of functions converting each way between the two units. It mirrors the host's ticks rather than choosing its own, so `0, 180, 360, 540, 720` land directly under the π ticks, and whole degrees need no formatter. The [axes reference](../reference/axes.md) has the rest of what `secondary_frame` takes.

When degrees are the *primary* axis instead, the unit trick is the wrong tool: the numbers are already plain, they just fall on ugly multiples. `TalbotLocator` chooses its step from a set of nice numbers, decimal by default (1, 2, 5 and their powers of ten), which on `[0, 360]` gives `0, 100, 200, 300`. Hand it the multiples that suit degrees, `TalbotLocator(nice_numbers=(9, 4.5, 3, 1.5, 6))`, and the same axis ticks `0, 90, 180, 270, 360`. No unit, no formatter.

The figure, as the gallery script draws it:

```{.python}
--8<-- "gallery.py:radian_axes"
```

<figure markdown>
![Phase-shifted sinusoids on an axis ticked in multiples of π, a matching degree axis along the top, the resistor curve picked out and the rest faded](../figures/radian_axes.svg)
<figcaption markdown>Radians below, degrees above, both reading off the same ticks.</figcaption>
</figure>
