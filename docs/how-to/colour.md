# Colour

*Stay in ink until colour distinguishes series, then take it from a colour-blind-safe scheme.*

Colour is a choice you make, not one vanzelfsprekend makes for you. Three greys carry the roles: `DATA_INK` for the marks, `TEXT_INK` for labels and titles, `LINE_INK` for the frame — a value hierarchy, darkest for the data and lightest for the furniture, not a palette. `distill` installs the neutral ink cycle (`vzs.palettes.cycle()`) in place of matplotlib's default, so a lone series stays near-black and nothing turns colourful on its own; a cycle you set yourself, before or after the call, is left alone, and `restore` gives it back. Opt into colour only once it distinguishes series: install a scheme cycle before you draw, and keep the lines solid and directly labelled rather than adding a second, redundant channel:

```python
ax.set_prop_cycle(vzs.palettes.cycle("muted"))  # then plot; line_labels names them
```

A single colour comes from Paul Tol's schemes through matplotlib's named-colour registry: a bare `tol:orange` is the vibrant default, and a qualified `tol:scheme.name` (`tol:muted.rose`, `tol:bright.blue`) reaches the rest. The two spaces stay distinct: the `tol:` prefix disambiguates a colour name in matplotlib's global registry, while `cycle` takes the bare scheme name (`"muted"`) since it is already in vanzelfsprekend's own namespace. `vzs.palettes.SCHEMES` enumerates them in code, and the sheet below names every swatch:

<figure markdown>
![Eight rows of Paul Tol's colour schemes (bright, high-contrast, vibrant, muted, medium-contrast, pale, dark and light), each swatch labelled with the colour name to type after tol:](../figures/palettes.svg)
<figcaption markdown>Every swatch, named as you type it after `tol:`.</figcaption>
</figure>

What you reach for depends on what you bring. Hand a finished plot to `distill` and it trims the frame and greys the furniture, touching nothing you drew — that is the only step. When you draw the plot yourself and want it restrained from the start, three orthogonal knobs shape the ink: `distill` (and `mute`) own the frame, `cycle` owns the colour, and the `vanzelfsprekend` style owns the marks' geometry — lighter lines, smaller marks, quieter titles. Each answers one question and none overlaps, so you compose the ones you want and `distill` is always the last word:

```python
with plt.style.context("vanzelfsprekend"):  # geometry knob
    fig, ax = plt.subplots()
    ax.set_prop_cycle(vzs.palettes.cycle("muted"))  # colour knob (or leave neutral)
    ax.plot(...)
    vzs.distill(ax, frame="data")  # frame knob: trim, grey, declutter
    fig.savefig("figure.png")
```

Keep the drawing, `distill` and save inside the `style.context`: matplotlib reads these defaults when it renders, not when you call `plot`, so leaving the context early would drop them before the figure is drawn.
