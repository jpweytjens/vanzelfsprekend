# The frame follows the axes

*`apply` is a standing arrangement, not an edit. The library re-reads the axes at every draw, which is why the order of your calls stops mattering, why the ticks follow the figure's size, and why `restore` is exact.*

A matplotlib call edits the axes once. `set_xlim` sets the limits and returns, and what happens to the ticks afterwards is matplotlib's business at draw time. `apply` edits once too: it hides two spines, installs the locators and greys the furniture on the spot. But a spine that ends at the last tick inside the data cannot be set once, because the ticks are not known until matplotlib lays the figure out, and the data can still change. So `apply` also leaves something behind, a hook that runs on every draw, reads the ticks and the data as they are at that moment, and moves the spine ends to match. Every feature that depends on the finished layout works the same way: the direct labels re-solve their positions, the raised axis label re-finds the top tick label, and a grid framed on one scale re-takes the union of its panels.

## The order of your calls stops mattering

Because the hook reads the axes at draw time, the order of your calls is mostly free. The [tick spacing figure](../how-to/tick-spacing.md) calls `apply` on an empty axes and plots afterwards; the frame meets the data when the figure is drawn. A `set_xlim` after `apply` crops the frame to the data left on screen, and a locator set after `apply` is read like any other ticks. The one order that does matter is not the hook's: `apply` installs the default locator when called, so a locator of your own goes after it, or `apply` would overwrite yours. The [locators how-to](../how-to/locators.md) states that rule.

## The ticks follow the figure

The tick count is the locator's doing, not the hook's, and it works for the same reason. The default locator takes no count. When matplotlib asks it for ticks, at draw time, it reads the axis's length in tick-label heights and aims for a gap of seven along x and four along y. Change the figure size, the font size or the panel's share of the grid, and the next draw asks again with the new length. That is the whole mechanism behind one call producing four year labels at 12 cm and two at 2 cm, and behind a poster's 24 pt labels thinning the ticks out by themselves. The hook's part comes after: with the ticks re-fitted, it re-reads them and moves the spine ends onto the new outermost ones.

## Restore is exact

A hook that only reads and writes furniture can be undone. `apply` records the state of everything it is about to touch, the spines, ticks, tick labels, axis labels and colour cycle, and `restore` puts the record back and disconnects the hook. Nothing else was touched, so nothing else needs putting back, and the marks were never touched at all. [Whose decision is which](decisions.md) is the rule that keeps that true.

## The cost

A hook that runs at draw time also fails at draw time, inside matplotlib's rendering, where an exception would abort the draw and leave a blank figure. So the hook catches errors and gives up on that draw, and a bug in the library shows as a frame that did not update rather than as a traceback. The entry points run the hook once when called and let errors through, so a mistake in your arguments still surfaces where you made it. A switch to surface draw-time errors is a planned addition.
