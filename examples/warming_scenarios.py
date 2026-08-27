"""Render the README figure: the same plot with matplotlib defaults and treated.

Observed global mean temperature (HadCRUT5, rebaselined to 1850-1900)
scatters up to the present; the five assessed IPCC AR6 scenarios fan out
from it to 2100. Both panels run the same plotting calls; the right one
adds the treatment, with `line_labels` in place of the legend.
"""

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

DATA = Path(__file__).parent / "data"
DOCS = Path(__file__).parents[1] / "docs"

SCENARIOS = {
    "ssp1_1_9": ("SSP1-1.9", "tol:teal"),
    "ssp1_2_6": ("SSP1-2.6", "tol:blue"),
    "ssp2_4_5": ("SSP2-4.5", "tol:orange"),
    "ssp3_7_0": ("SSP3-7.0", "tol:red"),
    "ssp5_8_5": ("SSP5-8.5", "tol:magenta"),
}


def load(name: str) -> np.ndarray:
    """Read a CSV from `examples/data`, skipping its provenance comments."""
    lines = (DATA / name).read_text().splitlines()
    body = "\n".join(line for line in lines if not line.startswith("#"))
    return np.genfromtxt(io.StringIO(body), delimiter=",", names=True)


def draw_data(ax: plt.Axes) -> None:
    """Draw the observed record and the five scenario fans on `ax`."""
    observed = load("hadcrut5_annual.csv")
    projected = load("spm8_scenarios.csv")
    baseline = observed["anomaly_c"][observed["year"] <= 1900].mean()
    ax.scatter(
        observed["year"],
        observed["anomaly_c"] - baseline,
        s=6,
        color="0.2",
        label="observed",
    )
    for column, (label, color) in SCENARIOS.items():
        ax.plot(
            projected["year"],
            projected[column],
            color=color,
            linewidth=1.4,
            label=label,
        )


def main() -> None:
    """Render the figure into `docs/warming_scenarios.png`."""
    fig, (plain, treated) = plt.subplots(1, 2, figsize=(10, 3.5))
    fig.subplots_adjust(wspace=0.8)

    draw_data(plain)
    plain.set_ylabel("warming (°C vs 1850–1900)")  # noqa: RUF001
    plain.legend()
    plain.set_title("matplotlib")

    vzs.apply(treated, frame=("data", "loose"))
    draw_data(treated)
    treated.text(1905, 0.8, "observed", color=vzs.palettes.DATA_INK)
    vzs.line_labels(treated)
    vzs.ylabel(treated, "warming\n(°C vs 1850–1900)", flush=True)  # noqa: RUF001
    treated.set_title("vanzelfsprekend")

    fig.savefig(DOCS / "warming_scenarios.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
