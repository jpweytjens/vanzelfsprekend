# Colour

*Stay in ink until colour distinguishes series, then take it from a colour-blind-safe scheme.*

Colour is yours to choose; vanzelfsprekend only chooses the greys. Three carry the roles: `DATA_INK` for the marks, `TEXT_INK` for labels and titles, `LINE_INK` for the frame, darkest for the data and lightest for the furniture. `apply` installs the neutral ink cycle in place of matplotlib's default, so a lone series stays near-black and nothing turns colourful on its own. A cycle you set yourself, before or after the call, is left alone, and `restore` gives matplotlib's back.

Opt into colour once it tells series apart, with a scheme cycle installed before you draw. Keep the lines solid and directly labelled: a dash pattern or a legend would say the same thing twice.

```python
ax.set_prop_cycle(vzs.palettes.cycle("muted"))
```

The schemes are [Paul Tol's](https://sronpersonalpages.nl/~pault/), colour-blind-safe and ordered by his technote's picking sequence, so in each row below the colours to reach for first are on the left. A single colour goes anywhere matplotlib takes one, by name: `tol:orange` is the vibrant default, and `tol:muted.rose` or `tol:bright.blue` reaches into a scheme. The `tol:` prefix keeps these names apart from matplotlib's own in its global registry; `cycle` takes the bare scheme name, `"muted"`, since it already lives in vanzelfsprekend's namespace. `vzs.palettes.SCHEMES` enumerates them in code.

<!-- palette-sheet -->

Hand a finished plot to `apply` and it trims the frame and greys the furniture, touching nothing you drew. When you draw with restraint in mind from the start, three knobs each own one thing: `apply`, or `range_frame` and `mute` as separate steps, the frame and its ink; `cycle` the colour; the `vanzelfsprekend` style the marks' geometry, lighter lines, smaller marks, quieter titles. None overlaps, so you compose the ones you want, and `apply` is the last word:

```python
with plt.style.context("vanzelfsprekend"):
    fig, ax = plt.subplots()
    ax.set_prop_cycle(vzs.palettes.cycle("muted"))
    ax.plot(...)
    vzs.apply(ax, frame="data")
    fig.savefig("figure.png")
```

Keep the drawing, `apply` and save inside the `style.context`: matplotlib reads these defaults when it renders, not when you call `plot`, so leaving the context early drops them before the figure is drawn.
