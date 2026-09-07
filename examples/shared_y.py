"""Two panels under `sharey="row"`, distilled from one of them.

matplotlib's `sharey` gives both panels one y view and one set of y
ticks, and `distill` treats them as one scale group: both left spines
span the union of the panels' data, so the left panel's ticks at 4 and
5 sit on its spine although its own line stops at 3. The x axes are
not shared, and the right panel runs over a different x range to show
that only the shared axis is grouped. The second row is the same pair
through `small_multiples(compare="row")`, which hides the inner
furniture and, being a claim about a grid, also ties x across the row:
both bottom spines there span the union of the two x ranges.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

import vanzelfsprekend as vzs

OUTPUT = Path(__file__).parent / "output"

X_LEFT = [0, 1, 2]
X_RIGHT = [1, 2, 3, 4]
LEFT = [0, 1, 3]
RIGHT = [0, 2, 4, 5]


def main() -> None:
    """Render both rows into `examples/output/shared_y.png`."""
    fig, axes = plt.subplots(2, 2, sharey="row", figsize=(8, 6))
    fig.subplots_adjust(hspace=0.6)

    (a, b), (c, d) = axes
    for left, right in ((a, b), (c, d)):
        left.plot(X_LEFT, LEFT, label="left", color=vzs.palettes.DATA_INK)
        right.plot(X_RIGHT, RIGHT, label="right", color=vzs.palettes.DATA_INK)

    vzs.distill(a)
    a.set_title('sharey="row", distill(a)')

    vzs.small_multiples((c, d), compare="row")
    c.set_title('sharey="row", small_multiples(compare="row")')

    for ax in axes.flat:
        vzs.line_labels(ax)

    OUTPUT.mkdir(exist_ok=True)
    fig.savefig(OUTPUT / "shared_y.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
