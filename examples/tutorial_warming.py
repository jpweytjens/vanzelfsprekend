"""Build the warming scenarios figure one call at a time, saving a figure per step.

Observed global mean temperature (HadCRUT5, rebaselined to 1850-1900)
scatters up to the present; the five assessed IPCC AR6 scenarios fan out
from it to 2100. The final step is the right panel of the front page's
figure; the earlier steps exist so the tutorial can show what each call buys.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

DATA = Path(__file__).parent / "data"
FIGURES = Path(__file__).parents[1] / "docs" / "figures"

SCENARIOS = {
    "ssp1_1_9": ("SSP1-1.9", "tol:teal"),
    "ssp1_2_6": ("SSP1-2.6", "tol:blue"),
    "ssp2_4_5": ("SSP2-4.5", "tol:orange"),
    "ssp3_7_0": ("SSP3-7.0", "tol:red"),
    "ssp5_8_5": ("SSP5-8.5", "tol:magenta"),
}


def data() -> tuple[np.ndarray, np.ndarray, float]:
    """Return the observed record, the scenarios, and the 1850-1900 baseline."""
    # --8<-- [start:data]
    observed = np.genfromtxt(
        DATA / "hadcrut5_annual.csv", delimiter=",", names=True, skip_header=4
    )
    projected = np.genfromtxt(
        DATA / "spm8_scenarios.csv", delimiter=",", names=True, skip_header=4
    )
    baseline = observed["anomaly_c"][observed["year"] <= 1900].mean()
    # --8<-- [end:data]
    return observed, projected, baseline


def draw(
    observed: np.ndarray, projected: np.ndarray, baseline: float
) -> tuple[plt.Figure, plt.Axes]:
    """Plot the record and the five scenarios on a fresh axes."""
    # --8<-- [start:draw]
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.scatter(
        observed["year"],
        observed["anomaly_c"] - baseline,
        s=6,
        color="0.2",
        label="observed",
        zorder=3,
    )
    for column, (label, color) in SCENARIOS.items():
        ax.plot(
            projected["year"],
            projected[column],
            color=color,
            linewidth=1.4,
            label=label,
        )
    # --8<-- [end:draw]
    return fig, ax


def save(fig: plt.Figure, step: int) -> None:
    """Write one step's figure for the tutorial."""
    fig.savefig(
        FIGURES / f"warming_step_{step}.svg", bbox_inches="tight", transparent=True
    )
    plt.close(fig)


def main() -> None:
    """Render the five steps."""
    FIGURES.mkdir(exist_ok=True)
    observed, projected, baseline = data()

    fig, ax = draw(observed, projected, baseline)
    ax.legend()
    save(fig, 1)

    fig, ax = draw(observed, projected, baseline)
    # --8<-- [start:step2]
    vzs.apply(ax, frame=("data", "nice"))
    # --8<-- [end:step2]
    ax.legend()
    save(fig, 2)

    fig, ax = draw(observed, projected, baseline)
    vzs.apply(ax, frame=("data", "nice"))
    # --8<-- [start:step3]
    vzs.ylabel(ax, "warming (°C vs 1850–1900)")
    # --8<-- [end:step3]
    ax.legend()
    save(fig, 3)

    fig, ax = draw(observed, projected, baseline)
    vzs.apply(ax, frame=("data", "nice"))
    vzs.ylabel(ax, "warming (°C vs 1850–1900)")
    # --8<-- [start:step4]
    vzs.line_labels(ax)
    # --8<-- [end:step4]
    save(fig, 4)

    fig, ax = draw(observed, projected, baseline)
    vzs.apply(ax, frame=("data", "nice"))
    vzs.ylabel(ax, "warming (°C vs 1850–1900)")
    vzs.line_labels(ax)
    # --8<-- [start:step5]
    vzs.label(ax, "observed", x=1930)
    # --8<-- [end:step5]
    save(fig, 5)


if __name__ == "__main__":
    main()
