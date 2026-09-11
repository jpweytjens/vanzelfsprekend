"""Draw the vanzelfsprekend repo icon with vanzelfsprekend itself.

Three series, a range frame with offset spines, end labels instead of
a legend, and Tol's high-contrast scheme: blue, yellow, red, one per
line. The s series is a sigmoid, echoing its label.

    uv run icon/make_icon.py    # writes icon/vanzelfsprekend-plotted.svg + .png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

OUT = Path(__file__).resolve().parent
SIZE_IN = 5.12  # 512 px at dpi=100
LINE_WIDTH = 7.0  # data ink, in points; roughly the hand icon's stroke
FURNITURE_WIDTH = 3.5  # spines and ticks
TICK_LENGTH = 14.0


def series() -> tuple[np.ndarray, list[np.ndarray]]:
    """Return x and the three series: two power curves and a sigmoid."""
    x = np.linspace(0.0, 10.0, 200)
    return x, [
        0.15 + 0.85 * (x / 10.0) ** 1.8,
        0.10 + 0.55 * (x / 10.0) ** 1.8,
        0.05 + 0.30 / (1.0 + np.exp(-(x - 5.0) / 1.3)),
    ]


def main() -> None:
    """Render the icon to `vanzelfsprekend-plotted.svg` and `.png`."""
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Lucida Grande", "DejaVu Sans"],
            "font.size": 40,
            "svg.fonttype": "none",  # keep the end labels as real text in the SVG
            "figure.facecolor": "none",
            "axes.facecolor": "none",
        }
    )

    fig, ax = plt.subplots(figsize=(SIZE_IN, SIZE_IN))

    # Apply first for the range-frame styling; the three lines take
    # Tol's high-contrast blue, yellow and red explicitly.
    vzs.apply(ax, frame="data", offset=10)

    x, ys = series()
    for y, label, color in zip(
        ys,
        "vzs",
        (
            "tol:high_contrast.blue",
            "tol:high_contrast.yellow",
            "tol:high_contrast.red",
        ),
        strict=True,
    ):
        ax.plot(x, y, label=label, linewidth=LINE_WIDTH, color=color)

    vzs.line_labels(ax)

    # Ticks only at the data extremes, pointing outward, no labels: at
    # icon size the marks have to speak on their own.
    ax.set_xticks([x.min(), x.max()])
    ax.set_yticks([min(y.min() for y in ys), max(y.max() for y in ys)])
    vzs.tick_direction(ax, "out")
    ax.tick_params(
        axis="both",
        which="major",
        length=TICK_LENGTH,
        width=FURNITURE_WIDTH,
        labelbottom=False,
        labelleft=False,
    )
    for spine in ax.spines.values():
        spine.set_linewidth(FURNITURE_WIDTH)

    # Slim margins keep the frame hugging the lines; the end labels are
    # annotations and may overflow into the figure margin on the right.
    ax.margins(0.04)
    fig.subplots_adjust(left=0.12, right=0.86, bottom=0.12, top=0.94)

    for ext, kw in (("svg", {}), ("png", {"dpi": 100})):
        fig.savefig(OUT / f"vanzelfsprekend-plotted.{ext}", transparent=True, **kw)
    plt.close(fig)


if __name__ == "__main__":
    main()
