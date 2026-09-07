"""Two panels under `sharey=True`, distilled from one of them.

matplotlib's `sharey` gives both panels one y view and one set of y
ticks, and `distill` treats them as one scale group: both left spines
span the union of the panels' data, so the left panel's ticks at 4 and
5 sit on its spine although its own line stops at 3. The second row is
the same pair through `small_multiples`, which adds the hidden inner
furniture; the two rows agree on ticks and spines.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

import vanzelfsprekend as vzs

OUTPUT = Path(__file__).parent / "output"

X = [0, 1, 2]
LEFT = [0, 1, 3]
RIGHT = [0, 2, 5]


def main() -> None:
    """Render both rows into `examples/output/shared_y.png`."""
    fig, axes = plt.subplots(2, 2, sharey="row", figsize=(8, 6))
    fig.subplots_adjust(hspace=0.6)

    (a, b), (c, d) = axes
    for left, right in ((a, b), (c, d)):
        left.plot(X, LEFT, label="left")
        right.plot(X, RIGHT, label="right")

    vzs.distill(a)
    a.set_title("sharey, distill(a)")

    vzs.small_multiples((c, d), compare="row")
    c.set_title("sharey, small_multiples")

    for ax in axes.flat:
        vzs.line_labels(ax)

    OUTPUT.mkdir(exist_ok=True)
    fig.savefig(OUTPUT / "shared_y.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
