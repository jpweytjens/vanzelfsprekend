"""Render sample tufty figures to PNG for eyeballing."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import tufty

OUTPUT = Path(__file__).parent / "output"


def scatter(frame):
    fig, ax = plt.subplots(figsize=(5, 3.5))
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12, color="0.2")
    tufty.tuftify(ax, frame=frame)
    tufty.xlabel(ax, "time (s)")
    tufty.ylabel(ax, "voltage")
    fig.savefig(OUTPUT / f"scatter_{frame}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def histogram():
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.hist(np.random.default_rng(1).normal(size=300), bins=25, color="0.4")
    tufty.tuftify(ax)
    tufty.xlabel(ax, "value")
    tufty.ylabel(ax, "count", flush=True)
    fig.savefig(OUTPUT / "histogram.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    OUTPUT.mkdir(exist_ok=True)
    scatter("nice")
    scatter("data")
    scatter("loose")
    histogram()
    print(f"wrote {len(list(OUTPUT.glob('*.png')))} figures to {OUTPUT}")


if __name__ == "__main__":
    main()
