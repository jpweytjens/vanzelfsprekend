"""Render the README figure: the same plot with matplotlib defaults and treated.

Observed global mean temperature (HadCRUT5, rebaselined to 1850-1900)
scatters up to the present; the five assessed IPCC AR6 scenarios fan out
from it to 2100. Both panels run the same plotting calls; the right one
adds the treatment, with `line_labels` in place of the legend.
"""

import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

sys.path.insert(0, str(Path(__file__).parents[1]))  # docs_hooks.py is at the repo root

import docs_hooks

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


def main() -> None:
    """Render the figure into `docs/`, once for each ground."""
    fig, (plain, treated) = plt.subplots(1, 2, figsize=(10, 3.5))
    fig.subplots_adjust(wspace=0.8)

    draw_data(plain)
    plain.set_ylabel("warming (°C vs 1850–1900)")  # noqa: RUF001
    plain.legend()
    plain.set_title("matplotlib")

    vzs.distill(treated, frame=("data", "loose"))
    draw_data(treated)
    vzs.line_labels(treated)
    vzs.label(treated, "observed", x=1905)
    # the panel carries a title, so the label keeps to the side
    vzs.ylabel(treated, "warming\n(°C vs 1850–1900)", place="beside")  # noqa: RUF001
    treated.set_title("vanzelfsprekend")

    light = io.StringIO()
    fig.savefig(light, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    (DOCS / "warming_scenarios.svg").write_text(light.getvalue(), encoding="utf-8")
    (DOCS / "warming_scenarios-dark.svg").write_text(
        docs_hooks.dark_svg(light.getvalue()), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
