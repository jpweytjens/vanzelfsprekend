"""Build the Kepler figure one call at a time, saving a figure per step.

The planet data is `vzs.datasets.load("planets")` (NASA Planetary Fact Sheet);
in AU and years the eight planets are collinear on log-log axes, the law
T = a**1.5. The final step is the gallery's `kepler`; the earlier steps
exist so the tutorial can show what each call buys. Steps two onward draw
inside the `vanzelfsprekend` style, so the line width and mark size come
from there.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

FIGURES = Path(__file__).parents[1] / "docs" / "figures"


def data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the planets' semi-major axis, orbital period, and an Earth mask."""
    # --8<-- [start:data]
    table = vzs.datasets.load("planets")
    axis = table["semi_major_axis_au"]
    period = table["orbital_period_year"]
    earth = table["name"] == "Earth"
    # --8<-- [end:data]
    return axis, period, earth


def draw(axis: np.ndarray, period: np.ndarray) -> tuple[plt.Figure, plt.Axes]:
    """Join the planets on fresh log-log axes, in matplotlib's default colour."""
    # --8<-- [start:draw]
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.plot(axis, period, marker="o")
    # --8<-- [end:draw]
    return fig, ax


def draw_muted(
    axis: np.ndarray, period: np.ndarray, earth: np.ndarray
) -> tuple[plt.Figure, plt.Axes]:
    """Draw the planets in the muted data ink, Earth picked out in a Tol blue."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.set_xscale("log")
    ax.set_yscale("log")
    # --8<-- [start:step3]
    ax.plot(axis, period, marker="o", color=vzs.palettes.DATA_INK)
    ax.plot(
        axis[earth],
        period[earth],
        marker="o",
        markersize=7,
        linestyle="none",
        color="tol:bright.blue",
        label="Earth",
    )
    # --8<-- [end:step3]
    return fig, ax


def save(fig: plt.Figure, step: int) -> None:
    """Write one step's figure for the tutorial."""
    fig.savefig(
        FIGURES / f"kepler_step_{step}.svg", bbox_inches="tight", transparent=True
    )
    plt.close(fig)


def main() -> None:
    """Render the four steps."""
    FIGURES.mkdir(exist_ok=True)
    axis, period, earth = data()

    # Step one: the default figure, drawn outside the style.
    fig, _ = draw(axis, period)
    save(fig, 1)

    # Step two: draw inside the style, trim the frame, raise the labels.
    # --8<-- [start:step2]
    with plt.style.context("vanzelfsprekend"):
        fig, ax = draw(axis, period)
        vzs.apply(ax, frame="loose")
        vzs.xlabel(ax, "semi-major axis (AU)")
        vzs.ylabel(ax, "orbital period (year)")
        # --8<-- [end:step2]
        save(fig, 2)

    # Step three: mute the field to grey and pick Earth out in colour.
    with plt.style.context("vanzelfsprekend"):
        fig, ax = draw_muted(axis, period, earth)
        vzs.apply(ax, frame="loose")
        vzs.xlabel(ax, "semi-major axis (AU)")
        vzs.ylabel(ax, "orbital period (year)")
        save(fig, 3)

    # Step four: name it in its own colour.
    with plt.style.context("vanzelfsprekend"):
        fig, ax = draw_muted(axis, period, earth)
        vzs.apply(ax, frame="loose")
        vzs.xlabel(ax, "semi-major axis (AU)")
        vzs.ylabel(ax, "orbital period (year)")
        # --8<-- [start:step4]
        vzs.label(ax, "Earth")
        # --8<-- [end:step4]
        save(fig, 4)


if __name__ == "__main__":
    main()
