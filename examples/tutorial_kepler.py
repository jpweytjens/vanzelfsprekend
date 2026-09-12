"""Build the Kepler figure one call at a time, saving a figure per step.

The planet data is `examples/data/planets.csv` (NASA Planetary Fact Sheet);
in AU and years the eight planets are collinear on log-log axes, the law
T = a**1.5. The final step is the gallery's `kepler`; the earlier steps
exist so the tutorial can show what each call buys. Steps two onward draw
inside the `vanzelfsprekend` style, so the line width and mark size come
from there.
"""

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

DATA = Path(__file__).parent / "data"
FIGURES = Path(__file__).parents[1] / "docs" / "figures"


def data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the planets' semi-major axis, orbital period, and an Earth mask."""
    # --8<-- [start:data]
    lines = (DATA / "planets.csv").read_text().splitlines()
    body = "\n".join(line for line in lines if not line.startswith("#"))
    table = np.genfromtxt(
        io.StringIO(body), delimiter=",", names=True, dtype=None, encoding="utf-8"
    )
    axis = table["semi_major_axis_au"]
    period = table["orbital_period_year"]
    earth = table["name"] == "Earth"
    # --8<-- [end:data]
    return axis, period, earth


def draw(axis: np.ndarray, period: np.ndarray) -> tuple[plt.Figure, plt.Axes]:
    """Join the planets on fresh log-log axes."""
    # --8<-- [start:draw]
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.set_xscale("log")
    ax.set_yscale("log")
    # The planets in order of distance, joined into the line they obey.
    ax.plot(axis, period, marker="o", color=vzs.palettes.DATA_INK)
    # --8<-- [end:draw]
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

    # Step three: pick Earth out of the grey.
    with plt.style.context("vanzelfsprekend"):
        fig, ax = draw(axis, period)
        vzs.apply(ax, frame="loose")
        vzs.xlabel(ax, "semi-major axis (AU)")
        vzs.ylabel(ax, "orbital period (year)")
        # --8<-- [start:step3]
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
        save(fig, 3)

    # Step four: name it in its own colour.
    with plt.style.context("vanzelfsprekend"):
        fig, ax = draw(axis, period)
        vzs.apply(ax, frame="loose")
        vzs.xlabel(ax, "semi-major axis (AU)")
        vzs.ylabel(ax, "orbital period (year)")
        ax.plot(
            axis[earth],
            period[earth],
            marker="o",
            markersize=7,
            linestyle="none",
            color="tol:bright.blue",
            label="Earth",
        )
        # --8<-- [start:step4]
        vzs.label(ax, "Earth")
        # --8<-- [end:step4]
        save(fig, 4)


if __name__ == "__main__":
    main()
