"""Render sample klaarte figures to PNG for eyeballing."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import klaarte

OUTPUT = Path(__file__).parent / "output"


def scatter(frame):
    fig, ax = plt.subplots(figsize=(5, 3.5))
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12, color="0.2")
    klaarte.range_frame(ax, frame=frame)
    klaarte.xlabel(ax, "time (s)")
    klaarte.ylabel(ax, "voltage", flush=True)
    fig.savefig(OUTPUT / f"scatter_{frame}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def histogram():
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.hist(np.random.default_rng(1).normal(size=300), bins=25, color="0.4")
    klaarte.range_frame(ax)
    klaarte.xlabel(ax, "value")
    klaarte.ylabel(ax, "count", flush=True, labelpad=10)
    fig.savefig(OUTPUT / "histogram.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def custom_ticks():
    fig, ax = plt.subplots(figsize=(5, 3.5))
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12, color="0.2")
    klaarte.range_frame(ax, frame="nice")
    ax.set_xticks([1, 3, 5, 7, 9])
    klaarte.xlabel(ax, "time (s)")
    klaarte.ylabel(ax, "voltage", flush=True)
    fig.savefig(OUTPUT / "custom_ticks.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def minimal():
    fig, ax = plt.subplots(figsize=(5, 3.5))
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 60), rng.uniform(-3.2, 4.1, 60), s=12, color="0.2")
    klaarte.range_frame(ax, frame="data")
    ax.set_xticks([])
    ax.set_yticks([])
    klaarte.xlabel(ax, "time (s)")
    klaarte.ylabel(ax, "voltage", flush=True)
    fig.savefig(OUTPUT / "minimal.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
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
