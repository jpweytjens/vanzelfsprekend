"""Build Doumont's resonance figure one call at a time, saving a figure per step.

The Lorentzian and its sampled points are a construction, not measurements,
after the resonance curve in Doumont's *Trees, maps and theorems*. The final
step is the gallery's `resonance_peak`; the earlier steps exist so the
tutorial can show what each call buys.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

FIGURES = Path(__file__).parents[1] / "docs" / "figures"


def data() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return frequency, calculated curve, sampled frequency, its jitter and power."""
    # --8<-- [start:data]
    rng = np.random.default_rng(0)
    frequency = np.linspace(15.6, 19.4, 500)
    sampled = np.linspace(16, 19, 61)

    def lorentzian(f: np.ndarray) -> np.ndarray:
        return 650 / (1 + ((f - 17.2) / 0.35) ** 2)

    calculated = lorentzian(frequency)
    random_sampled = sampled + rng.normal(0, 0.04, sampled.size)
    measured = lorentzian(sampled) + rng.normal(0, 12, sampled.size)
    # --8<-- [end:data]
    return frequency, calculated, sampled, random_sampled, measured


def draw(
    frequency: np.ndarray,
    calculated: np.ndarray,
    random_sampled: np.ndarray,
    measured: np.ndarray,
) -> tuple[plt.Figure, plt.Axes]:
    """Plot the curve and the points on fresh axes."""
    # --8<-- [start:draw]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(
        frequency, calculated, color="tol:orange", linewidth=1.2, label="calculated"
    )
    ax.scatter(
        random_sampled,
        measured,
        s=10,
        color=vzs.palettes.DATA_INK,
        zorder=3,
        label="measured",
    )
    ax.set_ylim(0, measured.max() * 1.05)
    # --8<-- [end:draw]
    return fig, ax


def save(fig: plt.Figure, step: int) -> None:
    """Write one step's figure for the tutorial."""
    fig.savefig(
        FIGURES / f"resonance_step_{step}.svg", bbox_inches="tight", transparent=True
    )
    plt.close(fig)


def main() -> None:
    """Render the five steps."""
    FIGURES.mkdir(exist_ok=True)
    frequency, calculated, sampled, random_sampled, measured = data()

    fig, ax = draw(frequency, calculated, random_sampled, measured)
    ax.legend()
    save(fig, 1)

    fig, ax = draw(frequency, calculated, random_sampled, measured)
    # --8<-- [start:step2]
    vzs.distill(ax, frame="loose", offset=(24, -6))
    # --8<-- [end:step2]
    ax.legend()
    save(fig, 2)

    fig, ax = draw(frequency, calculated, random_sampled, measured)
    vzs.distill(ax, frame="loose", offset=(24, -6))
    # --8<-- [start:step3]
    vzs.xlabel(ax, "frequency (GHz)")
    vzs.ylabel(ax, "output power (mW)")
    # --8<-- [end:step3]
    ax.legend()
    save(fig, 3)

    fig, ax = draw(frequency, calculated, random_sampled, measured)
    vzs.distill(ax, frame="loose", offset=(24, -6))
    vzs.xlabel(ax, "frequency (GHz)")
    vzs.ylabel(ax, "output power (mW)")
    # --8<-- [start:step4]
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
    # --8<-- [end:step4]
    ax.legend()
    save(fig, 4)

    fig, ax = draw(frequency, calculated, random_sampled, measured)
    vzs.distill(ax, frame="loose", offset=(24, -6))
    vzs.xlabel(ax, "frequency (GHz)")
    vzs.ylabel(ax, "output power (mW)")
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
    # --8<-- [start:step5]
    vzs.label(ax, "measured", x=lambda x, y: x[np.argmax(y)])
    vzs.label(ax, "calculated", x=17.5)
    # --8<-- [end:step5]
    save(fig, 5)


if __name__ == "__main__":
    main()
