"""Build the grand tours figure one call at a time, saving a figure per step.

A century of winners' average speeds at the Tour, the Giro and the Vuelta,
one race per panel. The final step is the gallery's `grand_tours`; the
earlier steps exist so the tutorial can show what each call buys.
"""

import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

DATA = Path(__file__).parent / "data"
FIGURES = Path(__file__).parents[1] / "docs" / "figures"

JERSEYS = {
    "tour": ("Tour", "tol:high_contrast.yellow"),  # maillot jaune
    "giro": ("Giro", "tol:medium_contrast.light_red"),  # maglia rosa
    "vuelta": ("Vuelta", "tol:red"),  # maillot rojo
}


def data() -> tuple[list[dt.date], dict[str, np.ndarray]]:
    """Return one date per year and each race's speeds, gaps left as NaN."""
    # --8<-- [start:data]
    table = np.genfromtxt(
        DATA / "grand_tour_speeds.csv", delimiter=",", names=True, skip_header=5
    )
    first, last = int(table["year"][0]), int(table["year"][-1])
    years = np.arange(first, last + 1)
    dates = [dt.date(year, 7, 1) for year in years]
    speeds_of = {}
    for race in JERSEYS:
        speeds = np.full(years.size, np.nan)
        speeds[table["year"].astype(int) - first] = table[race]
        speeds_of[race] = speeds
    # --8<-- [end:data]
    return dates, speeds_of


def draw(
    dates: list[dt.date], speeds_of: dict[str, np.ndarray]
) -> tuple[plt.Figure, np.ndarray]:
    """Plot one race per panel on a fresh stack of three axes."""
    # --8<-- [start:draw]
    fig, axes = plt.subplots(3, 1, figsize=(5, 4.5))
    fig.subplots_adjust(hspace=0.45)
    for ax, (race, (label, color)) in zip(axes, JERSEYS.items(), strict=True):
        ax.plot(dates, speeds_of[race], color=color, linewidth=1.2, label=label)
    # --8<-- [end:draw]
    return fig, axes


def save(fig: plt.Figure, step: int) -> None:
    """Write one step's figure for the tutorial."""
    fig.savefig(
        FIGURES / f"grand_tours_step_{step}.svg", bbox_inches="tight", transparent=True
    )
    plt.close(fig)


def main() -> None:
    """Render the four steps."""
    FIGURES.mkdir(exist_ok=True)
    dates, speeds_of = data()

    fig, axes = draw(dates, speeds_of)
    for ax in axes:
        ax.legend()
    save(fig, 1)

    fig, axes = draw(dates, speeds_of)
    # --8<-- [start:step2]
    vzs.small_multiples(
        axes,
        compare="column",
        frame="data",
        spacing=(5, 4),
        ylabel="winner's average\nspeed (km/h)",
    )
    # --8<-- [end:step2]
    for ax in axes:
        ax.legend()
    save(fig, 2)

    fig, axes = draw(dates, speeds_of)
    vzs.small_multiples(
        axes,
        compare="column",
        frame="data",
        spacing=(5, 4),
        ylabel="winner's average\nspeed (km/h)",
    )
    # --8<-- [start:step3]
    for ax, speeds in zip(axes, speeds_of.values(), strict=True):
        ax.yaxis.set_major_locator(
            vzs.SummaryLocator(speeds, [np.nanmin, np.nanmedian, np.nanmax])
        )
        ax.yaxis.set_major_formatter("{x:.1f}")
    # --8<-- [end:step3]
    for ax in axes:
        ax.legend()
    save(fig, 3)

    fig, axes = draw(dates, speeds_of)
    vzs.small_multiples(
        axes,
        compare="column",
        frame="data",
        spacing=(5, 4),
        ylabel="winner's average\nspeed (km/h)",
    )
    for ax, speeds in zip(axes, speeds_of.values(), strict=True):
        ax.yaxis.set_major_locator(
            vzs.SummaryLocator(speeds, [np.nanmin, np.nanmedian, np.nanmax])
        )
        ax.yaxis.set_major_formatter("{x:.1f}")
    # --8<-- [start:step4]
    for ax in axes:
        vzs.line_labels(ax)
    # --8<-- [end:step4]
    save(fig, 4)


if __name__ == "__main__":
    main()
