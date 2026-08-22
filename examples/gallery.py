"""Render sample vanzelfsprekend figures to PNG for eyeballing."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend

OUTPUT = Path(__file__).parent / "output"


def scatter(frame: str) -> None:
    """Render a scatter plot with the given frame mode."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12, color="0.2")
    vanzelfsprekend.range_frame(ax, frame=frame)
    vanzelfsprekend.xlabel(ax, "time (s)")
    vanzelfsprekend.ylabel(ax, "voltage", flush=True)
    fig.savefig(OUTPUT / f"scatter_{frame}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def histogram() -> None:
    """Render a histogram with a range frame."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.hist(np.random.default_rng(1).normal(size=300), bins=25, color="0.4")
    vanzelfsprekend.range_frame(ax)
    vanzelfsprekend.xlabel(ax, "value")
    vanzelfsprekend.ylabel(ax, "count", flush=True, labelpad=10)
    fig.savefig(OUTPUT / "histogram.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def custom_ticks() -> None:
    """Render a scatter plot with user-set ticks."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12, color="0.2")
    vanzelfsprekend.range_frame(ax, frame="nice")
    ax.set_xticks([1, 3, 5, 7, 9])
    vanzelfsprekend.xlabel(ax, "time (s)")
    vanzelfsprekend.ylabel(ax, "voltage", flush=True)
    fig.savefig(OUTPUT / "custom_ticks.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def minimal() -> None:
    """Render a scatter plot with a data frame and no ticks."""
    fig, ax = plt.subplots(figsize=(5, 3.5))
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12, color="0.2")
    vanzelfsprekend.range_frame(ax, frame="data")
    ax.set_xticks([])
    ax.set_yticks([])
    vanzelfsprekend.xlabel(ax, "time (s)")
    vanzelfsprekend.ylabel(ax, "voltage", flush=True)
    fig.savefig(OUTPUT / "minimal.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    """Render every gallery figure into `examples/output`."""
    OUTPUT.mkdir(exist_ok=True)
    scatter("nice")
    scatter("data")
    scatter("loose")
    histogram()
    custom_ticks()
    minimal()
    print(f"wrote {len(list(OUTPUT.glob('*.png')))} figures to {OUTPUT}")


if __name__ == "__main__":
    main()
