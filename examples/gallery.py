"""Render sample vanzelfsprekend figures to PNG for eyeballing."""

import datetime as dt
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

OUTPUT = Path(__file__).parent / "output"
DOCS = Path(__file__).parents[1] / "docs"
README_FIGURES = (
    "quartile_ticks.png",
    "scatter_loose.png",
    "histogram.png",
    "scatter_loglog.png",
    "timeseries.png",
)


# Monthly mean CO2 at Mauna Loa in ppm, August 2016 through July 2026.
# Source: NOAA Global Monitoring Laboratory, public domain.
# https://gml.noaa.gov/ccgg/trends/data.html
CO2_START = dt.date(2016, 8, 1)
# fmt: off
CO2_PPM = (
    402.45, 401.23, 401.79, 403.72, 404.64, 406.36, 406.66, 407.54,
    409.22, 409.89, 409.08, 407.33, 405.32, 403.57, 403.82, 405.31,
    407.00, 408.15, 408.52, 409.59, 410.45, 411.44, 410.99, 408.90,
    407.16, 405.71, 406.19, 408.21, 409.27, 411.03, 411.96, 412.18,
    413.54, 414.86, 414.15, 411.96, 410.17, 408.76, 408.74, 410.47,
    411.97, 413.59, 414.32, 414.72, 416.42, 417.28, 416.58, 414.58,
    412.75, 411.50, 411.49, 413.10, 414.23, 415.49, 416.72, 417.61,
    419.01, 419.09, 418.93, 416.90, 414.42, 413.26, 413.90, 414.97,
    416.67, 418.13, 419.24, 418.76, 420.19, 420.97, 420.94, 418.85,
    417.15, 415.91, 415.74, 417.47, 418.99, 419.47, 420.31, 421.00,
    423.30, 424.01, 423.68, 421.83, 419.68, 418.50, 418.82, 420.46,
    421.86, 422.80, 424.55, 425.38, 426.51, 426.90, 426.91, 425.55,
    422.99, 422.03, 422.38, 423.85, 425.40, 426.65, 427.09, 428.15,
    429.64, 430.51, 429.61, 427.87, 425.48, 424.37, 424.87, 426.46,
    427.49, 428.62, 429.35, 430.15, 431.12, 432.34, 431.44, 429.12,
)
# fmt: on


def timeseries() -> None:
    """Render the Mauna Loa CO2 record with a date range frame."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    vzs.apply(ax)
    months = [
        dt.date(
            CO2_START.year + (CO2_START.month - 1 + i) // 12,
            (CO2_START.month - 1 + i) % 12 + 1,
            1,
        )
        for i in range(len(CO2_PPM))
    ]
    ax.plot(months, CO2_PPM)
    vzs.ylabel(ax, "CO₂ (ppm)", flush=True)
    fig.savefig(OUTPUT / "timeseries.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def scatter(frame: str) -> None:
    """Render a scatter plot with the given frame mode."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    vzs.apply(ax, frame=frame)
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12)
    vzs.xlabel(ax, "time (s)")
    vzs.ylabel(ax, "voltage", flush=True)
    fig.savefig(OUTPUT / f"scatter_{frame}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def histogram() -> None:
    """Render a histogram with a range frame."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    vzs.apply(ax)
    ax.hist(np.random.default_rng(1).normal(size=300), bins=25)
    vzs.xlabel(ax, "value")
    vzs.ylabel(ax, "count", flush=True, labelpad=10)
    fig.savefig(OUTPUT / "histogram.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def quartile_ticks() -> None:
    """Render a quartile plot: ticks at the five-number summary of the data."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    vzs.apply(ax, frame="data")
    rng = np.random.default_rng(0)
    x = rng.uniform(0.3, 9.7, 60)
    y = rng.uniform(-3.2, 4.1, 60)
    ax.scatter(x, y, s=12)
    ax.xaxis.set_major_locator(vzs.QuartileLocator(x))
    ax.yaxis.set_major_locator(vzs.QuartileLocator(y))
    ax.xaxis.set_major_formatter("{x:.1f}")
    ax.yaxis.set_major_formatter("{x:.1f}")
    vzs.xlabel(ax, "time (s)")
    vzs.ylabel(ax, "voltage", flush=True)
    fig.savefig(OUTPUT / "quartile_ticks.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def scatter_loglog() -> None:
    """Render a log-log scatter of a power law with a range frame."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.set_xscale("log")
    ax.set_yscale("log")
    vzs.apply(ax, frame="loose")
    rng = np.random.default_rng(0)
    x = 10 ** rng.uniform(0.5, 3.5, 60)
    y = 3 * x**0.8 * 10 ** rng.normal(0, 0.15, 60)
    ax.scatter(x, y, s=12)
    vzs.xlabel(ax, "body mass (g)")
    vzs.ylabel(ax, "metabolic rate", flush=True)
    fig.savefig(OUTPUT / "scatter_loglog.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def minimal() -> None:
    """Render a scatter plot with a data frame and no ticks."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    vzs.apply(ax, frame="data")
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12)
    ax.set_xticks([])
    ax.set_yticks([])
    vzs.xlabel(ax, "time (s)")
    vzs.ylabel(ax, "voltage", flush=True)
    fig.savefig(OUTPUT / "minimal.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    """Render every gallery figure into `examples/output`."""
    OUTPUT.mkdir(exist_ok=True)
    scatter("nice")
    scatter("data")
    scatter("loose")
    histogram()
    quartile_ticks()
    scatter_loglog()
    timeseries()
    minimal()
    for name in README_FIGURES:
        shutil.copyfile(OUTPUT / name, DOCS / name)
    print(f"wrote {len(list(OUTPUT.glob('*.png')))} figures to {OUTPUT}")
    print(f"copied {len(README_FIGURES)} README figures to {DOCS}")


if __name__ == "__main__":
    main()
