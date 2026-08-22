"""Render the README figure: measured speeds against modelled and backsolved curves.

A rider is three scalars (flat cruising speed, critical climbing rate,
a descent comfort cap); a force-balance cubic backsolves the speed they
imply at any gradient. The modelled curve holds flat cruising power at
every gradient, so it undershoots climbs and overshoots descents; the
backsolved curve prices the effort per gradient, uncapped. Measured
speeds scatter around the backsolved curve, held at the comfort cap on
descents.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs

DOCS = Path(__file__).parents[1] / "docs"

G0, MASS, CDA, CRR, RHO, WIND = 9.81, 78.0, 0.35, 0.005, 1.225, 2.22
V_FLAT, VAM_CP, V_CAP = 29 / 3.6, 1150.0, 52 / 3.6  # the three rider scalars
K_A = 0.5 * RHO * CDA


def solve_speed(power: np.ndarray, gradient: np.ndarray) -> np.ndarray:
    """Largest real root of the force-balance cubic, per gradient."""
    theta = np.arctan(gradient)
    speeds = []
    for p, th in zip(*np.broadcast_arrays(power, theta), strict=True):
        drag = K_A * WIND**2 + MASS * G0 * (CRR * np.cos(th) + np.sin(th))
        roots = np.roots([K_A, 2 * K_A * WIND, drag, -p])
        speeds.append(roots[np.isreal(roots)].real.max())
    return np.array(speeds)


P_FLAT = K_A * (V_FLAT + WIND) ** 2 * V_FLAT + CRR * MASS * G0 * V_FLAT


def backsolved_speed(gradient: np.ndarray) -> np.ndarray:
    """Speed at any gradient from the three scalars, uncapped."""
    cp = MASS * G0 * VAM_CP / 3600
    climb = P_FLAT + (cp - P_FLAT) * np.clip(gradient / 0.03, 0, 1)
    descent = P_FLAT * np.exp(-25 * np.abs(gradient))
    power = np.where(gradient >= 0, climb, descent)
    return 3.6 * solve_speed(power, gradient)


def modelled_speed(gradient: np.ndarray) -> np.ndarray:
    """Constant-power cubic: flat cruising power at every gradient."""
    return 3.6 * solve_speed(np.full_like(gradient, P_FLAT), gradient)


def main() -> None:
    """Render the figure into `docs/backsolved_speed.png`."""
    rng = np.random.default_rng(7)
    gradient = rng.uniform(-0.099, 0.099, 45)
    speed = np.minimum(backsolved_speed(gradient), 3.6 * V_CAP) + rng.normal(
        0, 1.5, gradient.size
    )
    grid = np.linspace(-0.10, 0.10, 300)

    fig, ax = plt.subplots(figsize=(5, 3.5))
    vzs.apply(ax, frame="loose")
    ax.scatter(100 * gradient, speed, s=12, zorder=3)
    ax.plot(
        100 * grid,
        modelled_speed(grid),
        color="tol:cyan",
        linewidth=1.8,
        label="modelled",
    )
    ax.plot(
        100 * grid,
        backsolved_speed(grid),
        color="tol:orange",
        linewidth=1.8,
        label="backsolved",
    )
    ax.text(0.5, 34, "measured", color=vzs.palettes.DATA_INK)
    vzs.line_labels(ax)
    vzs.xlabel(ax, "gradient (%)")
    vzs.ylabel(ax, "speed (km/h)", flush=True)
    fig.savefig(DOCS / "backsolved_speed.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
