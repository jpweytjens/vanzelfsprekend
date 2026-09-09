# Small multiples

*Treat a grid of panels as one figure: shared scales, furniture only where it is read.*

Panels tied with `sharex` or `sharey` are distilled together, whichever one you pass: each shared axis is ticked and framed from the union of the panels' data, so the two stay comparable and every tick lands on a spine. `restore` undoes them together. A twin from `twinx` or `twiny` is left out with a warning and keeps its box. For a grid, `small_multiples` is the same treatment with the inner furniture hidden.

Monthly CO₂ at four NOAA stations from the Arctic to the South Pole in a 2x2 grid under `small_multiples`, sharing one scale. Every panel keeps its plotted line, but only the left column and bottom row keep spines, ticks and axis labels, so the seasonal swing shrinking toward the pole reads on equal terms without repeating furniture. The panels are 7 cm wide, which the default spacing reads as two year labels; a tighter x spacing asks for a label every two years instead:

```python
vzs.small_multiples(axes.flat, spacing=(5, 4), ylabel="CO₂ (ppm)")
```

<figure markdown>
![A 2x2 grid of monthly CO2 at Barrow, Mauna Loa, Samoa and the South Pole on a shared scale, the seasonal sawtooth shrinking toward the pole, spines and ticks only on the left column and bottom row](../figures/small_multiples.svg)
<figcaption markdown>Only the left column and bottom row keep spines, ticks and axis labels; every panel keeps its line.</figcaption>
</figure>

`compare` sets the smallest set of panels that are fully comparable. `"figure"`, the default, shares one scale per axis across the whole grid, as the CO₂ panels do. `"column"` scopes x per column and leaves y shared across the grid; `"row"` is the transpose, scoping y per row and leaving x shared. Narrowing one axis's scope never widens the other's, so a single-column grid such as the [grand tours](../tutorial/grand-tours.md) comes out the same under `"column"` as under `"figure"`.
