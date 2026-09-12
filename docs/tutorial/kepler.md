# Kepler's third law

*Colour one planet and name it, and the eye finds it before a word is read.*

The eight planets obey Kepler's third law: the square of a planet's orbital period _T_ equals the cube of its semi-major axis _a_. In astronomical units and years the constant is one, so _T_ = _a_<sup>3/2</sup>, and on log-log axes the planets fall on a single straight line. This lesson builds the gallery's `kepler` one call at a time, drawing that line and picking Earth out of the other seven. The measurements are the NASA Planetary Fact Sheet, and the script is `examples/tutorial_kepler.py`.

## The data and the default figure

The three arrays are the semi-major axis, the orbital period, and a mask marking which planet is Earth.

```{.python}
--8<-- "tutorial_kepler.py:data"
```

Joining the planets in order of distance draws the line they sit on. Because they obey the law, the joined points and the law are the same line, so a single `plot` says both.

```{.python}
--8<-- "tutorial_kepler.py:draw"
```

<figure markdown>
![Eight planets joined by a heavy line inside a full matplotlib box, rising straight across log-log axes with default tick labels](../figures/kepler_step_1.svg)
<figcaption markdown>Step one. matplotlib boxes the plot on four spines and draws a heavy line, but the planets already fall straight.</figcaption>
</figure>

## Draw with restraint

Three things decide how restrained a figure looks, and vanzelfsprekend keeps them apart: the frame, the colour, and the drawing geometry. Two of them do the work here. Drawing inside the `vanzelfsprekend` style lightens the line and shrinks the marks, `apply` trims the box to two spines standing off the data, and the axis labels rise to the spine ends.

```{.python}
--8<-- "tutorial_kepler.py:step2"
```

<figure markdown>
![The same planets with the box gone, two grey offset spines ending at powers of ten, the axis labels raised to the spine ends, and lighter line and marks](../figures/kepler_step_2.svg)
<figcaption markdown>Step two. The box becomes two offset spines at powers of ten, the labels sit at their ends, and the line and marks are lighter.</figcaption>
</figure>

The style is matplotlib's own, reached through `plt.style.context`. It sets the line width and mark size and nothing else, no colour and no spine, so it composes with `apply` rather than overriding it. Draw and save inside the context, since matplotlib reads these defaults when it renders the figure, not when you call `plot`. `apply` greys the spines and ticks and leaves the data line as you drew it, still in matplotlib's default colour; the colour of the data is yours to set, and the next step sets it.

## Pick Earth out of the grey

A single mark in colour is found first only when the rest recede. Muting the seven planets to a neutral grey and giving Earth one Tol-blue mark, a little larger, does both at once: the field steps back and the one planet comes forward.

```{.python}
--8<-- "tutorial_kepler.py:step3"
```

<figure markdown>
![The same line with the seven planets in grey and Earth in one larger blue mark at one astronomical unit and one year](../figures/kepler_step_3.svg)
<figcaption markdown>Step three. The seven go grey and Earth takes a Tol blue, so the eye lands on the one before reading the axes.</figcaption>
</figure>

This is the point of the muting. Colour spent on every planet names none of them; spent on one, it says which planet the figure is about.

## Name it

The blue mark still needs a name, and a legend would send the eye to a corner and back. `label` writes the name beside the mark instead, in the mark's own colour.

```{.python}
--8<-- "tutorial_kepler.py:step4"
```

<figure markdown>
![The finished figure: the blue Earth mark labelled "Earth" beside it in the same blue, no legend](../figures/kepler_step_4.svg)
<figcaption markdown>Step four. `label` names Earth in its own blue, beside the point, where a legend would have sat in a corner.</figcaption>
</figure>

Earth is one point, so `label` needs no anchor. It reads the name from the mark's `label=`, takes the mark's colour, and slides the text just clear of the ink.

Next: [the warming scenarios](warming-scenarios.md), where the legend goes for good and every line is named where it ends.
