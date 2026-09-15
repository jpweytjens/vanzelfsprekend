"""Build the Old Faithful figure one call at a time, saving a figure per step.

Eruption duration against the wait to the next eruption, 272 observations.
The final step is the gallery's `old_faithful`; the earlier steps exist so
the tutorial can show what each call buys.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

FIGURES = Path(__file__).parents[1] / "docs" / "figures"


def data() -> np.ndarray:
    """Return the 272 observations, one row each."""
    # --8<-- [start:data]
    table = vzs.datasets.load("old_faithful")
    # --8<-- [end:data]
    return table  # noqa: RET504  (named to match the snippet shown in the docs)


def draw(table: np.ndarray) -> tuple[plt.Figure, plt.Axes]:
    """Scatter the two variables on a fresh axes."""
    # --8<-- [start:draw]
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.scatter(table["eruptions"], table["waiting"], s=10, color=vzs.palettes.DATA_INK)
    # --8<-- [end:draw]
    return fig, ax


def save(fig: plt.Figure, step: int) -> None:
    """Write one step's figure for the tutorial."""
    fig.savefig(
        FIGURES / f"old_faithful_step_{step}.svg", bbox_inches="tight", transparent=True
    )
    plt.close(fig)


def main() -> None:
    """Render the three steps."""
    FIGURES.mkdir(exist_ok=True)
    table = data()

    fig, ax = draw(table)
    save(fig, 1)

    fig, ax = draw(table)
    # --8<-- [start:step2]
    vzs.apply(ax, frame="data")
    # --8<-- [end:step2]
    save(fig, 2)

    fig, ax = draw(table)
    vzs.apply(ax, frame="data")
    # --8<-- [start:step3]
    vzs.xlabel(ax, "eruption length (min)")
    vzs.ylabel(ax, "minutes to the next")
    # --8<-- [end:step3]
    save(fig, 3)


if __name__ == "__main__":
    main()
