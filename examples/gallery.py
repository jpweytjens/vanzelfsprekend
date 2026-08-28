"""Render sample vanzelfsprekend figures to PNG for eyeballing.

Every figure draws a dataset from `examples/data` (each file carries its
source and licence in its header) or an honest construction that says so:
Anscombe built his quartet by hand, and the power profiles are model
curves, not measurements.
"""

import datetime as dt
import io
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

DATA = Path(__file__).parent / "data"
OUTPUT = Path(__file__).parent / "output"
DOCS = Path(__file__).parents[1] / "docs"
README_FIGURES = (
    "anscombe.png",
    "grand_tours.png",
    "brain_body.png",
    "waiting_times.png",
    "power_profiles.png",
    "small_multiples.png",
)


def load(name: str, usecols: tuple[int, ...] | None = None) -> np.ndarray:
    """Read a CSV from `examples/data` into a named array.

    Strips the provenance comments first: `genfromtxt` with `names=True`
    would read the field names from the first line even when commented.
    """
    lines = (DATA / name).read_text().splitlines()
    body = "\n".join(line for line in lines if not line.startswith("#"))
    return np.genfromtxt(io.StringIO(body), delimiter=",", names=True, usecols=usecols)


def anscombe() -> None:
    """Render Anscombe's quartet with data frames and quartile ticks."""
    table = load("anscombe.csv")
    fig, axes = plt.subplots(2, 2, figsize=(7, 5))
    fig.subplots_adjust(hspace=0.55, wspace=0.35)
    numerals = ["I", "II", "III", "IV"]
    for i, (ax, numeral) in enumerate(zip(axes.flat, numerals, strict=True), 1):
        x, y = table[f"x{i}"], table[f"y{i}"]
        vzs.apply(ax, frame="data")
        ax.scatter(x, y, s=12)
        ax.xaxis.set_major_locator(vzs.QuartileLocator(x))
        ax.yaxis.set_major_locator(vzs.QuartileLocator(y))
        ax.xaxis.set_major_formatter("{x:.0f}")
        ax.yaxis.set_major_formatter("{x:.1f}")
        ax.set_title(numeral, fontsize=10, color=vzs.palettes.TEXT_INK)
    fig.savefig(OUTPUT / "anscombe.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def grand_tours() -> None:
    """Render a century of grand tour winners' speeds with direct labels."""
    table = load("grand_tour_speeds.csv")
    first, last = int(table["year"][0]), int(table["year"][-1])
    years = np.arange(first, last + 1)
    dates = [dt.date(year, 7, 1) for year in years]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    jerseys = {
        "tour": ("Tour", "tol:high_contrast.yellow"),
        "giro": ("Giro", "tol:magenta"),
        "vuelta": ("Vuelta", "tol:red"),
    }
    for column, (label, color) in jerseys.items():
        speeds = np.full(years.size, np.nan)
        speeds[table["year"].astype(int) - first] = table[column]
        ax.plot(dates, speeds, color=color, linewidth=1.2, label=label)
    # Plot before apply: the axis becomes a date axis when date data
    # arrives, and apply detects date-ness at call time.
    vzs.apply(ax, frame=("data", "loose"))
    vzs.line_labels(ax)
    vzs.ylabel(ax, "winner's\naverage speed (km/h)", flush=True)
    fig.savefig(OUTPUT / "grand_tours.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def brain_body() -> None:
    """Render the mammal brain-body allometry on log-log axes."""
    table = load("mammals.csv", usecols=(1, 2))
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.set_xscale("log")
    ax.set_yscale("log")
    vzs.apply(ax, frame="loose")
    ax.scatter(table["body_kg"], table["brain_g"], s=12)
    vzs.xlabel(ax, "body mass (kg)")
    vzs.ylabel(ax, "brain mass (g)", flush=True)
    fig.savefig(OUTPUT / "brain_body.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def waiting_times() -> None:
    """Render the bimodal Old Faithful waiting times as a histogram."""
    table = load("old_faithful.csv")
    fig, ax = plt.subplots(figsize=(5, 3.5))
    vzs.apply(ax, frame="data")
    ax.hist(table["waiting"], bins=27)
    vzs.xlabel(ax, "minutes to the next eruption")
    vzs.ylabel(ax, "eruptions", flush=True, labelpad=10)
    fig.savefig(OUTPUT / "waiting_times.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# Morton's 3-parameter critical-power model with illustrative parameters,
# anchored to trained-cyclist means (CP 301 +/- 35 W, W' 12.7 +/- 3.4 kJ;
# Chorley et al. 2020, doi:10.1007/s00421-020-04459-6) with the contrasts
# between archetypes exaggerated. The curves are the model, not riders.
ARCHETYPES = {
    "sprinter": (290, 24000, 1750, "tol:orange"),
    "puncheur": (340, 20000, 1500, "tol:blue"),
    "climber": (370, 16000, 1250, "tol:teal"),
    "time-trialist": (400, 13000, 1150, "tol:magenta"),
}


def power_profiles() -> None:
    """Render critical-power model curves per rider archetype."""
    seconds = np.geomspace(1, 10_000, 400)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.set_xscale("log")
    vzs.apply(ax, frame=("data", "nice"))
    for label, (cp, w_prime, p_max, color) in ARCHETYPES.items():
        power = cp + w_prime / (seconds + w_prime / (p_max - cp))
        ax.plot(seconds, power, color=color, linewidth=1.2, label=label)
    vzs.line_labels(ax)
    vzs.xlabel(ax, "duration (s)")
    vzs.ylabel(ax, "power (W)", flush=True)
    fig.savefig(OUTPUT / "power_profiles.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def small_multiples_grid() -> None:
    """Render a 2x2 small-multiples grid of logistic adoption curves.

    Model curves, not measurements: four logistic functions with
    different midpoints and rates, the classic technology-adoption
    shape.
    """
    t = np.linspace(0, 30, 200)
    curves = {
        "A": 1 / (1 + np.exp(-0.55 * (t - 8))),
        "B": 1 / (1 + np.exp(-0.30 * (t - 14))),
        "C": 1 / (1 + np.exp(-0.80 * (t - 18))),
        "D": 1 / (1 + np.exp(-0.45 * (t - 23))),
    }
    fig, axes = plt.subplots(2, 2, figsize=(7, 5))
    for ax, (name, y) in zip(axes.flat, curves.items(), strict=True):
        ax.plot(t, 100 * y)
        ax.set_title(name, fontsize=10, color=vzs.palettes.TEXT_INK)
    vzs.small_multiples(axes.flat, xlabel="years since launch", ylabel="adoption (%)")
    fig.savefig(OUTPUT / "small_multiples.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    """Render every gallery figure into `examples/output`."""
    OUTPUT.mkdir(exist_ok=True)
    anscombe()
    grand_tours()
    brain_body()
    waiting_times()
    power_profiles()
    small_multiples_grid()
    for name in README_FIGURES:
        shutil.copyfile(OUTPUT / name, DOCS / name)
    print(f"wrote {len(list(OUTPUT.glob('*.png')))} figures to {OUTPUT}")
    print(f"copied {len(README_FIGURES)} README figures to {DOCS}")


if __name__ == "__main__":
    main()
