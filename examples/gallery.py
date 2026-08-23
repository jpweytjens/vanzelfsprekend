"""Render sample vanzelfsprekend figures to PNG for eyeballing."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

OUTPUT = Path(__file__).parent / "output"


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
    minimal()
    print(f"wrote {len(list(OUTPUT.glob('*.png')))} figures to {OUTPUT}")


if __name__ == "__main__":
    main()
