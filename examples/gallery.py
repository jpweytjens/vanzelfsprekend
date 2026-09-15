"""Render sample vanzelfsprekend figures to PNG and SVG for eyeballing.

Every figure draws one of the package's datasets (`vzs.datasets.describe`
names each one's source and licence) or an honest construction that says so:
Anscombe built his quartet by hand, and the power profiles are model
curves, not measurements.
"""

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
FIGURES = DOCS / "figures"
README_FIGURES = (
    "anscombe.png",
    "grand_tours.png",
    "seaborn_lineplot.png",
    "kepler.png",
    "waiting_times.png",
    "power_profiles.png",
    "resonance_peak.png",
    "small_multiples.png",
    "tick_spacing.png",
    "frame_modes.png",
)


def save(fig: plt.Figure, name: str) -> None:
    """Write `name.png` for the README and a transparent `name.svg` for the site."""
    fig.savefig(OUTPUT / f"{name}.png", dpi=150, bbox_inches="tight")
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight", transparent=True)
    plt.close(fig)


def anscombe() -> None:
    """Render Anscombe's quartet with data frames and quartile ticks."""
    table = vzs.datasets.load("anscombe")
    fig, axes = plt.subplots(2, 2, figsize=(7, 5))
    fig.subplots_adjust(hspace=0.55, wspace=0.35)
    numerals = ["I", "II", "III", "IV"]
    for i, (ax, numeral) in enumerate(zip(axes.flat, numerals, strict=True), 1):
        x, y = table[f"x{i}"], table[f"y{i}"]
        ax.scatter(x, y, s=12)
        ax.xaxis.set_major_locator(vzs.QuartileLocator(x))
        ax.yaxis.set_major_locator(vzs.QuartileLocator(y))
        ax.xaxis.set_major_formatter("{x:.0f}")
        ax.yaxis.set_major_formatter("{x:.1f}")
        vzs.apply(ax, frame="data")
        ax.set_title(numeral, color=vzs.palettes.TEXT_INK)
    save(fig, "anscombe")


def grand_tours() -> None:
    """Render a century of grand tour winners' speeds, one race per panel."""
    table = vzs.datasets.load("grand_tour_speeds")
    first, last = int(table["year"][0]), int(table["year"][-1])
    years = np.arange(first, last + 1)
    dates = [dt.date(year, 7, 1) for year in years]
    fig, axes = plt.subplots(3, 1, figsize=(5, 4.5), sharex=True)
    fig.subplots_adjust(hspace=0.45)
    jerseys = {
        "tour": ("Tour", "tol:high_contrast.yellow"),  # maillot jaune
        "giro": ("Giro", "tol:medium_contrast.light_red"),  # maglia rosa
        "vuelta": ("Vuelta", "tol:red"),  # maillot rojo
    }
    speeds_of = {}
    for ax, (column, (label, color)) in zip(axes, jerseys.items(), strict=True):
        speeds = np.full(years.size, np.nan)
        speeds[table["year"].astype(int) - first] = table[column]
        speeds_of[ax] = speeds
        ax.plot(dates, speeds, color=color, label=label)
    # Plot before apply: the axis becomes a date axis when date data
    # arrives, and apply detects date-ness at call time.
    vzs.small_multiples(
        axes,
        compare="column",
        frame="data",
        spacing=(5, 4),
        ylabel="winner's average\nspeed (km/h)",
    )
    for ax, speeds in speeds_of.items():
        ax.yaxis.set_major_locator(
            vzs.SummaryLocator(speeds, [np.nanmin, np.nanmedian, np.nanmax])
        )
        ax.yaxis.set_major_formatter("{x:.1f}")
    for ax in axes:
        vzs.line_labels(ax)
    save(fig, "grand_tours")


def seaborn_lineplot() -> None:
    """Apply vanzelfsprekend to a plot seaborn drew: the same calls, another producer.

    The four series are a constructed random walk, not a measurement.
    seaborn keeps each legend entry's text on a proxy artist separate
    from the drawn line, so the end labels come from `labels=` rather
    than the lines' own `label=`.
    """
    import pandas as pd
    import seaborn as sns

    rng = np.random.default_rng(365)
    dates = pd.date_range("2016-01-01", periods=365, freq="D")
    walks = rng.standard_normal((365, 4)).cumsum(axis=0)
    frame = pd.DataFrame(walks, index=dates, columns=list("ABCD")).rolling(7).mean()
    # seaborn's common whitegrid, scoped so it does not leak into the
    # other gallery figures; apply strips the grid it draws.
    with sns.axes_style("whitegrid"):
        fig, ax = plt.subplots(figsize=(7, 3.5))
        sns.lineplot(data=frame, palette="tab10", linewidth=2.0, ax=ax)
    # Plot before apply: the axis becomes a date axis when date data
    # arrives, and apply detects date-ness at call time. line_labels
    # replaces seaborn's legend, hiding it in the process.
    vzs.apply(ax, frame=("data", "nice"))
    vzs.line_labels(ax, labels=list("ABCD"))
    save(fig, "seaborn_lineplot")


def kepler() -> None:
    """Render Kepler's third law on log-log axes, Earth picked out in Tol blue.

    Period against semi-major axis for the eight planets; in AU and years
    the law is T = a**1.5, so the planets are collinear on log-log axes.
    Joining them draws the line, Earth alone is coloured, and `label` names
    it in that colour. The gallery renders under the `vanzelfsprekend` style,
    so the line width and mark size come from there, not from this figure.
    """
    table = vzs.datasets.load("planets")
    axis, period, earth = (
        table["semi_major_axis_au"],
        table["orbital_period_year"],
        table["name"] == "Earth",
    )
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.set_xscale("log")
    ax.set_yscale("log")
    # The planets in order of distance, joined into the law they obey.
    ax.plot(axis, period, marker="o", color=vzs.palettes.DATA_INK)
    # Earth alone in a Tol blue, a larger mark, named in its colour.
    ax.plot(
        axis[earth],
        period[earth],
        marker="o",
        markersize=7,
        linestyle="none",
        color="tol:bright.blue",
        label="Earth",
    )
    vzs.apply(ax, frame="loose")
    vzs.xlabel(ax, "semi-major axis (AU)")
    vzs.ylabel(ax, "orbital period (year)")
    vzs.label(ax, "Earth")
    save(fig, "kepler")


def waiting_times() -> None:
    """Render the bimodal Old Faithful waiting times as a histogram."""
    table = vzs.datasets.load("old_faithful")
    fig, ax = plt.subplots(figsize=(5, 3.5))
    vzs.apply(ax, frame="data")
    ax.hist(table["waiting"], bins=27)
    vzs.xlabel(ax, "minutes to the next eruption")
    vzs.ylabel(ax, "eruptions", labelpad=10)
    save(fig, "waiting_times")


def old_faithful() -> None:
    """Render Old Faithful's eruption durations against the wait to the next."""
    table = vzs.datasets.load("old_faithful")
    fig, ax = plt.subplots(figsize=(5, 3.5))
    # --8<-- [start:old_faithful]
    ax.scatter(table["eruptions"], table["waiting"], s=10, color=vzs.palettes.DATA_INK)
    vzs.apply(ax, frame="data")
    vzs.xlabel(ax, "eruption length (min)")
    vzs.ylabel(ax, "minutes to the next")
    # --8<-- [end:old_faithful]
    save(fig, "old_faithful")


def frame_modes() -> None:
    """Render one warming record under the four frame modes."""
    table = vzs.datasets.load("hadcrut5_annual")
    year, anomaly = table["year"], table["anomaly_c"]
    fig, axes = plt.subplots(2, 2, figsize=(6.5, 5))
    fig.subplots_adjust(hspace=0.55, wspace=0.4)
    for ax, mode in zip(axes.flat, ("nice", "loose", "data", "feature"), strict=True):
        if mode == "feature":
            # Mark the 2 °C Paris target the record has not reached: the spine
            # climbs to it while the low end stays at the data. Set the marks
            # before apply so mute's ink cycle still colours the line below.
            ax.yaxis.set_major_locator(vzs.FeatureLocator(year, anomaly, [0, 1, 2]))
            vzs.apply(ax, frame=("data", ("data", "feature")))
        else:
            vzs.apply(ax, frame=mode)
        ax.plot(year, anomaly)
        ax.set_title(f'frame="{mode}"', color=vzs.palettes.TEXT_INK)
    save(fig, "frame_modes")


def spine_reach() -> None:
    """Render Old Faithful under two tick counts, the nice spine's reach following."""
    table = vzs.datasets.load("old_faithful")
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.2))
    fig.subplots_adjust(wspace=0.45)
    # `n` rather than `spacing`, so the panel's size cannot change what the
    # figure shows: a count is absolute where a gap in label heights is not.
    for ax, n in zip(axes, (None, 8), strict=True):
        ax.scatter(
            table["eruptions"], table["waiting"], s=10, color=vzs.palettes.DATA_INK
        )
        vzs.apply(ax, n=n)
        vzs.xlabel(ax, "eruption length (min)")
        ax.set_title(
            "apply(ax)" if n is None else f"apply(ax, n={n})",
            color=vzs.palettes.TEXT_INK,
        )
    vzs.ylabel(axes[0], "minutes to the next")
    save(fig, "spine_reach")


def tick_spacing() -> None:
    """Render one warming record at two widths, the tick count following."""
    table = vzs.datasets.load("hadcrut5_annual")
    fig = plt.figure(figsize=(9, 2.8))
    grid = fig.add_gridspec(1, 2, width_ratios=[5, 1], wspace=0.4)
    for spec in grid:
        ax = fig.add_subplot(spec)
        vzs.apply(ax)
        ax.plot(table["year"], table["anomaly_c"])
        width_cm = ax.get_position().width * fig.get_figwidth() * 2.54
        ax.set_title(f"{width_cm:.0f} cm wide", color=vzs.palettes.TEXT_INK)
    vzs.ylabel(fig.axes[0], "warming (°C)")
    save(fig, "tick_spacing")


# Morton's 3-parameter critical-power model, (CP, W', Pmax), with
# critical power near trained-cyclist means (CP 301 +/- 35 W; Chorley et
# al. 2020, doi:10.1007/s00421-020-04459-6) and W' and Pmax stylised to
# fan the archetypes apart: the explosive types carry a large anaerobic
# reserve, the aerobic diesels a small one, so the curves cross at
# staggered durations instead of a single knot. The curves are the
# model, not riders.
ARCHETYPES = {
    "sprinter": (300, 28000, 1800),
    "puncheur": (345, 33000, 1500),
    "climber": (380, 9500, 1220),
    "time-trialist": (415, 10000, 1080),
}


def power_profiles() -> None:
    """Render critical-power model curves per rider archetype."""
    seconds = np.geomspace(1, 10_000, 400)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.set_xscale("log")
    # The sprinter's one-second power runs above the outermost tick, so a
    # 'nice' y end would leave the curve spilling over the ylabel. A 'data'
    # end takes the spine, and with it the label, up past the peak.
    vzs.apply(ax, frame=("data", "data"))
    # Four peer series, so opt into colour: the muted scheme carries the
    # distinction, and line_labels names each curve in its own colour.
    ax.set_prop_cycle(vzs.palettes.cycle("muted"))
    for label, (cp, w_prime, p_max) in ARCHETYPES.items():
        power = cp + w_prime / (seconds + w_prime / (p_max - cp))
        ax.plot(seconds, power, label=label)
    vzs.line_labels(ax)
    vzs.xlabel(ax, "duration (s)")
    vzs.ylabel(ax, "power (W)")
    save(fig, "power_profiles")


def resonance_peak() -> None:
    """Render a resonance curve with its peak labelled by `FeatureLocator`.

    After Doumont's *Trees, maps and theorems*: the x ticks mark the
    band edges, 16 and 19 GHz, and between them the peak's location
    `x[argmax(y)]`, which is not the mean. The calculated curve spills
    past the frame the way Doumont draws it, so the band edges are fixed
    constants, not the data's extent. The Lorentzian and its sampled
    points are a construction, not measurements. The two labels sit where
    Doumont puts them, beside the topmost point and beside the right flank.
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
    ax.plot(frequency, calculated, color="tol:orange", label="calculated")
    ax.scatter(
        random_sampled,
        measured,
        s=10,
        color=vzs.palettes.DATA_INK,
        zorder=3,
        label="measured",
    )
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
    vzs.apply(ax, frame="feature", offset=(24, -6))
    vzs.tick_direction(ax, "in")
    vzs.xlabel(ax, "frequency (GHz)")
    vzs.ylabel(ax, "output power (mW)")
    # Doumont names the points beside the summit and the curve beside the
    # flank under it; the anchors are his, the sliding is ours. The summit
    # is a feature of the points, the same one the x tick reads.
    vzs.label(ax, "measured", x=lambda x, y: x[np.argmax(y)])
    vzs.label(ax, "calculated", x=17.5)
    save(fig, "resonance_peak")


def small_multiples_grid() -> None:
    """Render monthly CO2 at four latitude-spanning stations.

    Real flask measurements from NOAA GML (the data file's header carries
    the source and citation). One shared scale across the panels shows
    the seasonal sawtooth collapsing from the Arctic (Barrow) to the
    South Pole, while the northern stations ride a few ppm above the
    southern.
    """
    table = vzs.datasets.load("co2_stations_monthly")
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
        ax.set_title(title, color=vzs.palettes.TEXT_INK)
    vzs.small_multiples(
        axes.flat, frame=("data", "nice"), spacing=(5, 4), ylabel="CO₂ (ppm)"
    )
    save(fig, "small_multiples")


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


def radian_axes() -> None:
    """Render phase-shifted sinusoids on a pi-fraction axis, degrees on top.

    A constructed set in the spirit of a Doumont RLC figure, not data:
    the lead and lag are quarter-turn phase shifts and V_tot is the exact
    sum of the other three.
    """
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    # --8<-- [start:radian_axes]
    from fractions import Fraction

    from matplotlib.ticker import FuncFormatter

    def pi_fraction(value: float, _pos: int) -> str:
        turns = Fraction(value / np.pi).limit_denominator(100)
        if turns == 0:
            return "0"
        sign = "-" if turns < 0 else ""
        num, den = abs(turns.numerator), turns.denominator
        head = "π" if num == 1 else f"{num}π"
        return f"{sign}{head}" if den == 1 else f"{sign}{head}/{den}"

    theta = np.linspace(0, 4 * np.pi, 400)
    v_l = 9.7 * np.sin(theta + np.pi / 3)  # leads
    v_c = 6.7 * np.sin(theta - np.pi / 3)  # lags
    v_r = 8.7 * np.sin(theta - np.pi / 8)
    v_tot = (v_l + v_r + v_c) / np.sqrt(3)  # their exact sum

    yellow = "tol:high_contrast.yellow"
    ax.hlines(
        xmin=0,
        xmax=4 * np.pi,
        y=0,
        color=vzs.palettes.DATA_INK,
        linewidth=1,
        alpha=0.15,
    )
    ax.plot(theta, v_l, color=yellow, alpha=0.3, label="$V_L$")
    ax.plot(theta, v_c, color=yellow, alpha=0.3, label="$V_C$")
    ax.plot(theta, v_tot, color=vzs.palettes.DATA_INK, alpha=0.15, label="$V_{tot}$")
    ax.plot(theta, v_r, color=yellow, label="$V_R$")

    ax.yaxis.set_major_locator(vzs.FeatureLocator(theta, v_r, [-10, 0, 10]))
    vzs.apply(ax, frame=("data", "feature"), offset=(10, 5))
    vzs.tick_direction(ax, "in")

    ax.xaxis.set_major_locator(vzs.TalbotLocator(unit=np.pi))
    ax.xaxis.set_major_formatter(FuncFormatter(pi_fraction))

    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    secax.tick_params(direction="in")

    vzs.xlabel(ax, "phase (rad)")
    vzs.ylabel(ax, "voltage (V)", place="beside")
    vzs.line_labels(ax)
    # --8<-- [end:radian_axes]
    save(fig, "radian_axes")


def accented_peak() -> None:
    """Render the accent how-to figure: a peak's own frequency pulled forward."""
    frequency = np.linspace(15, 20, 400)
    power = 1 / (1 + ((frequency - 17.2) / 0.3) ** 2)
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(frequency, power, color=vzs.palettes.DATA_INK)
    # --8<-- [start:accented_peak]
    peak = vzs.FeatureLocator(frequency, power, {"peak": lambda x, y: x[np.argmax(y)]})
    ax.xaxis.set_major_locator(vzs.AugmentedLocator(vzs.TalbotLocator(), peak))
    ax.xaxis.set_major_formatter("{x:.1f}")
    vzs.apply(ax)
    vzs.xlabel(ax, "frequency (GHz)")
    vzs.ylabel(ax, "output power (mW)")
    ax.vzs.accent(axis="x")
    # --8<-- [end:accented_peak]
    save(fig, "accented_peak")


def labour_income() -> None:
    """Save the labour-income decomposition, assembled by the tutorial script."""
    from tutorial_income import decomposition

    save(decomposition(), "labour_income_decomposition")


def main() -> None:
    """Render every gallery figure into `examples/output`."""
    OUTPUT.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    # The gallery draws under vanzelfsprekend's style, the one authority for
    # line width and mark size; figures set only what deviates from it.
    plt.style.use("vanzelfsprekend")
    anscombe()
    grand_tours()
    seaborn_lineplot()
    kepler()
    waiting_times()
    old_faithful()
    power_profiles()
    resonance_peak()
    small_multiples_grid()
    tick_spacing()
    spine_reach()
    frame_modes()
    radian_axes()
    accented_peak()
    seaborn_lineplot()
    labour_income()  # last: draw() sets font rcParams that would leak to others
    for name in README_FIGURES:
        shutil.copyfile(OUTPUT / name, DOCS / name)
    print(f"wrote {len(list(OUTPUT.glob('*.png')))} figures to {OUTPUT}")
    print(f"copied {len(README_FIGURES)} README figures to {DOCS}")


if __name__ == "__main__":
    main()
