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
from matplotlib.patches import Rectangle

import vanzelfsprekend as vzs

matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Lucida Grande", "DejaVu Sans"],
        "font.size": 10,
        # "svg.fonttype": "none",  # keep the end labels as real text in the SVG
        # "figure.facecolor": "none",
        # "axes.facecolor": "none",
    }
)

DATA = Path(__file__).parent / "data"
OUTPUT = Path(__file__).parent / "output"
DOCS = Path(__file__).parents[1] / "docs"
README_FIGURES = (
    "anscombe.png",
    "grand_tours.png",
    "brain_body.png",
    "waiting_times.png",
    "power_profiles.png",
    "resonance_peak.png",
    "small_multiples.png",
    "palettes.png",
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
        vzs.distill(ax, frame="data")
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
        "tour": ("Tour", "#FFCC00"),  # maillot jaune
        "giro": ("Giro", "#EE2A7B"),  # maglia rosa
        "vuelta": ("Vuelta", "#E4002B"),  # maillot rojo
    }
    for column, (label, color) in jerseys.items():
        speeds = np.full(years.size, np.nan)
        speeds[table["year"].astype(int) - first] = table[column]
        ax.plot(dates, speeds, color=color, linewidth=1.2, label=label)
    # Plot before distill: the axis becomes a date axis when date data
    # arrives, and distill detects date-ness at call time.
    vzs.distill(ax, frame=("data", "loose"))
    vzs.line_labels(ax)
    vzs.ylabel(ax, "winner's\naverage speed (km/h)", place="above")
    fig.savefig(OUTPUT / "grand_tours.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def brain_body() -> None:
    """Render the mammal brain-body allometry on log-log axes."""
    table = load("mammals.csv", usecols=(1, 2))
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.set_xscale("log")
    ax.set_yscale("log")
    vzs.distill(ax, frame="loose")
    ax.scatter(table["body_kg"], table["brain_g"], s=12)
    vzs.xlabel(ax, "body mass (kg)")
    vzs.ylabel(ax, "brain mass (g)")
    fig.savefig(OUTPUT / "brain_body.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def waiting_times() -> None:
    """Render the bimodal Old Faithful waiting times as a histogram."""
    table = load("old_faithful.csv")
    fig, ax = plt.subplots(figsize=(5, 3.5))
    vzs.distill(ax, frame="data")
    ax.hist(table["waiting"], bins=27)
    vzs.xlabel(ax, "minutes to the next eruption")
    vzs.ylabel(ax, "eruptions", labelpad=10)
    fig.savefig(OUTPUT / "waiting_times.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# Morton's 3-parameter critical-power model, (CP, W', Pmax), with
# critical power near trained-cyclist means (CP 301 +/- 35 W; Chorley et
# al. 2020, doi:10.1007/s00421-020-04459-6) and W' and Pmax stylised to
# fan the archetypes apart: the explosive types carry a large anaerobic
# reserve, the aerobic diesels a small one, so the curves cross at
# staggered durations instead of a single knot. The curves are the
# model, not riders.
ARCHETYPES = {
    "sprinter": (300, 28000, 1800, "tol:bright.blue"),
    "puncheur": (345, 33000, 1500, "tol:bright.red"),
    "climber": (380, 9500, 1220, "tol:bright.green"),
    "time-trialist": (415, 10000, 1080, "tol:bright.yellow"),
}


def power_profiles() -> None:
    """Render critical-power model curves per rider archetype."""
    seconds = np.geomspace(1, 10_000, 400)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.set_xscale("log")
    vzs.distill(ax, frame=("data", "nice"))
    for label, (cp, w_prime, p_max, color) in ARCHETYPES.items():
        power = cp + w_prime / (seconds + w_prime / (p_max - cp))
        ax.plot(seconds, power, color=color, linewidth=1.2, label=label)
    vzs.line_labels(ax)
    vzs.xlabel(ax, "duration (s)")
    vzs.ylabel(ax, "power (W)")
    fig.savefig(OUTPUT / "power_profiles.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def resonance_peak() -> None:
    """Render a resonance curve with its peak labelled by `FeatureLocator`.

    After Doumont's *Trees, maps and theorems*: the x ticks mark the
    band edges, 16 and 19 GHz, and between them the peak's location
    `x[argmax(y)]`, which is not the mean. The calculated curve spills
    past the frame the way Doumont draws it, so the band edges are fixed
    constants, not the data's extent. The Lorentzian and its sampled
    points are a construction, not measurements.
    """
    rng = np.random.default_rng(0)
    frequency = np.linspace(15.6, 19.4, 500)
    sampled = np.linspace(16, 19, 61)

    def lorentzian(f: np.ndarray) -> np.ndarray:
        return 650 / (1 + ((f - 17.2) / 0.35) ** 2)

    calculated = lorentzian(frequency)
    random_sampled = sampled + rng.normal(0, 0.04, sampled.size)
    measured = lorentzian(sampled) + rng.normal(0, 12, sampled.size)
    fig, ax = plt.subplots(figsize=(5, 4))
    vzs.distill(ax, frame="loose", offset=(24, -6))
    ax.plot(frequency, calculated, color="tol:orange", linewidth=1.2)
    ax.scatter(random_sampled, measured, s=10, color=vzs.palettes.DATA_INK, zorder=3)
    # Output power has a true zero, so show the axis from the 0 baseline
    # up past the measured peak that pokes above the calculated curve.
    ax.set_ylim(0, measured.max() * 1.05)
    ax.xaxis.set_major_locator(
        vzs.FeatureLocator(sampled, measured, [16, lambda x, y: x[np.argmax(y)], 19])
    )
    ax.yaxis.set_major_locator(
        vzs.FeatureLocator(frequency, calculated, [0, lambda x, y: y.max()])
    )
    ax.yaxis.set_minor_locator(
        vzs.SummaryLocator(calculated, reducers=[lambda y: y.max() / 2])
    )
    ax.xaxis.set_major_formatter("{x:g}")
    ax.yaxis.set_major_formatter("{x:.0f}")
    vzs.tick_direction(ax, "in")
    vzs.xlabel(ax, "frequency (GHz)", flush=True)
    vzs.ylabel(ax, "output power (mW)", place="above")
    fig.savefig(OUTPUT / "resonance_peak.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def small_multiples_grid() -> None:
    """Render monthly CO2 at four latitude-spanning stations.

    Real flask measurements from NOAA GML (the data file's header carries
    the source and citation). One shared scale across the panels shows
    the seasonal sawtooth collapsing from the Arctic (Barrow) to the
    South Pole, while the northern stations ride a few ppm above the
    southern.
    """
    table = load("co2_stations_monthly.csv")
    dates = [
        dt.date(int(year), int(month), 15)
        for year, month in zip(table["year"], table["month"], strict=True)
    ]
    panels = [
        ("barrow", "Barrow 71°N"),
        ("mauna_loa", "Mauna Loa 20°N"),
        ("samoa", "Samoa 14°S"),
        ("south_pole", "South Pole 90°S"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(7, 5))
    for ax, (column, title) in zip(axes.flat, panels, strict=True):
        ax.plot(dates, table[column], color=vzs.palettes.DATA_INK)
        ax.set_title(title, fontsize=10, color=vzs.palettes.TEXT_INK)
    vzs.small_multiples(axes.flat, frame=("data", "nice"), ylabel="CO₂ (ppm)")
    fig.savefig(OUTPUT / "small_multiples.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (channel / 255 for channel in rgb)
    y = 0.2126729 * r**2.4 + 0.7151522 * g**2.4 + 0.0721750 * b**2.4
    return y + (0.022 - y) ** 1.414 if y < 0.022 else y


def _apca_lc(text: tuple[int, int, int], background: tuple[int, int, int]) -> float:
    """Lightness contrast of `text` on `background`, by the APCA algorithm."""
    text_y = _relative_luminance(text)
    background_y = _relative_luminance(background)
    if abs(background_y - text_y) < 0.0005:
        return 0.0
    if background_y > text_y:  # dark text on a light background
        sapc = (background_y**0.56 - text_y**0.57) * 1.14
        lc = 0.0 if sapc < 0.1 else sapc - 0.027
    else:  # light text on a dark background
        sapc = (background_y**0.65 - text_y**0.62) * 1.14
        lc = 0.0 if sapc > -0.1 else sapc + 0.027
    return lc * 100


def _label_ink(hex_colour: str) -> str:
    """White or near-black, whichever has the stronger APCA contrast on `hex_colour`."""
    background = (
        int(hex_colour[1:3], 16),
        int(hex_colour[3:5], 16),
        int(hex_colour[5:7], 16),
    )
    dark_lc = abs(_apca_lc((34, 34, 34), background))
    light_lc = abs(_apca_lc((255, 255, 255), background))
    return "#222222" if dark_lc >= light_lc else "#ffffff"


def palette_swatches() -> None:
    """Render every Tol scheme as labelled swatches, a colour reference.

    Drawn straight from `vzs.palettes.SCHEMES`, so the swatches and names
    cannot drift from the registered `tol:` colours. A bare `tol:orange`
    is the vibrant default; a qualified `tol:scheme.name` reaches any of
    the eight schemes.
    """
    schemes = vzs.palettes.SCHEMES
    ncols = max(len(colours) for colours in schemes.values())
    x0, span = 0.2, 0.78
    cell = span / ncols
    fig, ax = plt.subplots(figsize=(1.25 * ncols, 0.85 * len(schemes) + 0.7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(schemes))
    ax.axis("off")
    by_size = sorted(schemes.items(), key=lambda kv: len(kv[1]), reverse=True)
    for row, (scheme, colours) in enumerate(by_size):
        y = row + 0.5
        ax.text(
            x0 - 0.02,
            y,
            scheme,
            ha="right",
            va="center",
            fontsize=10,
            color=vzs.palettes.TEXT_INK,
        )
        for i, (name, hex_colour) in enumerate(colours.items()):
            cx = x0 + i * cell
            ax.add_patch(
                Rectangle((cx, y - 0.25), cell * 0.86, 0.5, facecolor=hex_colour, lw=0)
            )
            ax.text(
                cx + cell * 0.43,
                y,
                name,
                ha="center",
                va="center",
                fontsize=7,
                color=_label_ink(hex_colour),
            )
    fig.savefig(OUTPUT / "palettes.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    """Render every gallery figure into `examples/output`."""
    OUTPUT.mkdir(exist_ok=True)
    anscombe()
    grand_tours()
    brain_body()
    waiting_times()
    power_profiles()
    resonance_peak()
    small_multiples_grid()
    palette_swatches()
    for name in README_FIGURES:
        shutil.copyfile(OUTPUT / name, DOCS / name)
    print(f"wrote {len(list(OUTPUT.glob('*.png')))} figures to {OUTPUT}")
    print(f"copied {len(README_FIGURES)} README figures to {DOCS}")


if __name__ == "__main__":
    main()
