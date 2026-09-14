"""Draw the vanzelfsprekend repo icon with vanzelfsprekend itself.

Three series, a range frame with offset spines, end labels instead of
a legend, and Tol's high-contrast scheme: blue, yellow, red, one per
line. The s series is a sigmoid, echoing its label.

The same three curve shapes, spread apart and stripped of frame and
labels, also make the docs-site favicon: a simplified mark that stays
legible as three lines down to 16 px.

    uv run icon/make_icon.py
    # writes icon/vanzelfsprekend-plotted.svg + .png
    # and docs/theme/favicon.svg + favicon.ico
"""

import io
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import vanzelfsprekend as vzs

OUT = Path(__file__).resolve().parent
THEME = OUT.parent / "docs" / "theme"  # favicon lives with the served assets
SIZE_IN = 5.12  # 512 px at dpi=100
LINE_WIDTH = 7.0  # data ink, in points; roughly the hand icon's stroke
FURNITURE_WIDTH = 3.5  # spines and ticks
TICK_LENGTH = 14.0

# Tol's high-contrast scheme, one colour per line, shared by both marks.
COLORS = (
    "tol:high_contrast.blue",
    "tol:high_contrast.yellow",
    "tol:high_contrast.red",
)

FAVICON_SPREAD = 0.09  # minor extra gap between the lines; keeps the fan
FAVICON_LINE_WIDTH = 36.0  # fat strokes survive rasterisation at tab size
FAVICON_ICO_SIZES = (16, 32, 48)  # sizes bundled into the .ico fallback


def rise_shapes(x: np.ndarray) -> list[np.ndarray]:
    """Return the three normalised rise shapes: two powers and a sigmoid.

    The authority for what the three curves *are*; the icon and the
    favicon each place these shapes at their own offsets.
    """
    return [
        (x / 10.0) ** 1.8,
        (x / 10.0) ** 1.8,
        1.0 / (1.0 + np.exp(-(x - 5.0) / 1.3)),
    ]


def series() -> tuple[np.ndarray, list[np.ndarray]]:
    """Return x and the three icon series: two power curves and a sigmoid."""
    x = np.linspace(0.0, 10.0, 200)
    top, mid, bot = rise_shapes(x)
    return x, [0.15 + 0.85 * top, 0.10 + 0.55 * mid, 0.05 + 0.30 * bot]


def favicon_series() -> tuple[np.ndarray, list[np.ndarray]]:
    """Return x and the three favicon series, spread apart for 16 px.

    The extra vertical gap keeps them three distinct lines instead of
    merging near the origin.
    """
    x = np.linspace(0.0, 10.0, 200)
    top, mid, bot = rise_shapes(x)
    s = FAVICON_SPREAD
    return x, [2 * s + (1.0 - 2 * s) * top, s + (0.62 - s) * mid, 0.30 * bot]


def make_favicon() -> None:
    """Render the favicon to docs/theme/favicon.svg and favicon.ico.

    No frame, ticks or labels: three fat round-capped lines that read at
    tab size.
    """
    mpl.rcParams.update({"figure.facecolor": "none", "axes.facecolor": "none"})
    fig, ax = plt.subplots(figsize=(SIZE_IN, SIZE_IN))

    x, ys = favicon_series()
    for y, color in zip(ys, COLORS, strict=True):
        # clip_on=False so the round caps aren't sliced flat by the axes
        # box, which would read as a square clipping the mark.
        ax.plot(
            x,
            y,
            linewidth=FAVICON_LINE_WIDTH,
            color=color,
            solid_capstyle="round",
            clip_on=False,
        )

    ax.set_ylim(-0.02, 1.02)
    ax.axis("off")
    ax.margins(0.06)
    # Wide figure margin so the unclipped round caps clear the SVG
    # viewport instead of being cut by its edge.
    fig.subplots_adjust(left=0.06, right=0.94, bottom=0.06, top=0.94)

    fig.savefig(THEME / "favicon.svg", transparent=True)

    # Rasterise once at full size; let Pillow derive the .ico sizes.
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, transparent=True)
    buf.seek(0)
    Image.open(buf).convert("RGBA").save(
        THEME / "favicon.ico", sizes=[(s, s) for s in FAVICON_ICO_SIZES]
    )
    plt.close(fig)


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
    for y, label, color in zip(ys, "vzs", COLORS, strict=True):
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

    make_favicon()


if __name__ == "__main__":
    main()
