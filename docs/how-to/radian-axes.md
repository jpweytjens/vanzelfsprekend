# Non-decimal ticks

*The locator's ticks are `unit * q * 10**x`: nice numbers `q` tiled across the decades. Change `unit` to count in π or any other step, or `nice_numbers` to pick a different set of round values.*

The nice numbers are a small seed set, 1, 2, 5 and a few more (2.5, 3, 4), the values a reader takes in at a glance. Talbot does not stop at the seed: it multiplies each by every power of ten, so `q * 10**x` tiles `0.2, 0.5, 1, 2, 5, 10, 20` across the decades, and every default tick is one of those. That is why the grid is decimal, and why a radian axis over `[0, 2π]` ticks `0, 2, 4, 6`, round numbers that fall nowhere near π.

The full grid the locator searches is `unit * q * 10**x`, with `unit` at 1 by default. Two dials move the ticks off the decimal grid, one for each factor you might want to change: `unit` rescales the whole step, and `nice_numbers` swaps the seed.

## A change of unit

Set `unit` to count in that step instead of in ones. `TalbotLocator(unit=np.pi)` runs the search in units of π and lands the ticks on `0, π, 2π, 3π, 4π`, the step now `π * q * 10**x`. Multiplying the grid by a constant is a linear rescaling, exact here because the nice-number search is scale-invariant, and it is the only way onto multiples of an irrational step, which no choice of `q` can reach. Set it *after* `apply` (or `range_frame`), the way [every locator goes on after the frame](locators.md), since `apply` installs the default locator and would otherwise overwrite yours.

The locator places the ticks; matplotlib still writes them, and left alone it writes `3.14`, not `π`. Turning the value into "π/2" is a `FuncFormatter` you supply, because the library ships none: a tick label [stays a string matplotlib wrote](tick-formats.md), and the range frame does not touch it. This names π twice, once as the locator's `unit` and once inside the formatter that divides by π to find the fraction, so declare it once and read it in both places:

```python
pi = np.pi  # one authority: the locator and the formatter both read it

ax.xaxis.set_major_locator(vzs.TalbotLocator(unit=pi))
ax.xaxis.set_major_formatter(FuncFormatter(pi_fraction))
```

Change that one `pi` and the ticks and their labels move together, where two separate literals would drift apart the moment one was edited.

## The other unit on top

A second axis carrying the same data in the other unit is one call. `vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))` adds a degree axis along the top, the pair of functions converting each way between radians and degrees:

```python
secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
```

It mirrors the host's ticks rather than running a search of its own, so `0, 180, 360, 540, 720` land directly under the π ticks and whole degrees need no formatter. Because it mirrors, neither `unit` nor `nice_numbers` applies to it: the degree ticks are wherever the π ticks are. The [axes reference](../reference/axes.md) has the rest of what `secondary_frame` takes.

## A different set of nice numbers

When your step *is* on the decimal ladder but the seed is wrong, change `q` instead of `unit`. A degrees-*primary* axis over `[0, 360]` gets `0, 100, 200, 300` from the default seed; the ticks you want, `0, 90, 180, 270, 360`, are `q * 10**1` for a different set. Hand `TalbotLocator` that set:

```python
ax.xaxis.set_major_locator(vzs.TalbotLocator(nice_numbers=(9, 4.5, 3, 1.5, 6)))
```

No unit, no formatter. The two dials do not overlap: `nice_numbers` swaps `q` but keeps the powers of ten, so it lands any decimal-scaled set (degrees, dozens) and never a π grid; `unit` rescales the whole step, and only that reaches a unit off the decimal ladder. The [locators reference](../reference/locators.md) lists both arguments.

The figure below sets `unit` and the degree axis on the same plot, as the gallery script draws it[^doumont]:

```{.python}
--8<-- "gallery.py:radian_axes"
```

<figure markdown>
![Phase-shifted sinusoids on an axis ticked in multiples of π, a matching degree axis along the top, the resistor curve picked out and the rest faded](../figures/radian_axes.svg)
<figcaption markdown>Radians below, degrees above, both reading off the same ticks.</figcaption>
</figure>

[^doumont]: Jean-luc Doumont, *Trees, Maps, and Theorems: Effective Communication for Rational Minds* (Brussels: Principiae, 2009), whose RLC phasor example this figure follows, and whose y-label placements the range frame takes.
