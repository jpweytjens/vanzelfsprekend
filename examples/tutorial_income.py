"""WORK IN PROGRESS -- the labour-income decomposition figure.

A simulated monthly labour-income series decomposed, as in the phd, into a
permanent component (a double rolling median) and a transient component (the
residual). Recurrent June holiday pay and December bonuses (positive
recurrent) and a one-off raise (positive permanent) are the changes the
decomposition surfaces. Meant to become a gallery figure + a datetime tutorial.

Settled so far
--------------
- Two y-groups on one x: income + permanent share a level scale (compare=
  "figure", so P reads relative to I), the transient stands alone (apply).
  small_multiples has no single `compare` mode for "union rows 0-1, row 2
  apart", so it is two frame calls; identical dates + x-mode keep the x
  aligned without sharex (sharex breaks the shared y-scale, see below).
- frame y="data" on BOTH groups: the spines hug their own data with equal
  margins, so all three align as a column, and the troughs no longer hang
  below the lowest nice tick (the "nice" mode symptom).
- x per-end ("data","loose"): a firm 2012 start, a loose (ongoing) end.
- Highlight rule (phd): transient/recurrent when |nu| >= 1.645 * MAD(nu)
  (one-sided 95% normal quantile, a single band); permanent when |dP| > eps.
  Recovered P-hat is shown, not the true step, so the running median is on
  display; the shared scale hides its noise wander.
- High-contrast scheme: gold for recurrent, blue for the raise. One label
  per category via vzs.label. 0 marked as a MINOR tick on the transient y,
  so both axes read the same way: nice majors + feature minors (jun/dec on
  x, 0 on y).

Open threads
------------
- The 0 reference is a minor tick. Alternative: a labelled major via custom
  fixed offsets (union the frame's nice ticks with 0; safe under "data" mode
  because the spine hugs data, not the ticks). Decide minor vs major.
- Library candidate (out of scope for this docs branch): teach a locator to
  union nice breaks with explicit feature positions, so "nice + feature" can
  share the major slot instead of one overwriting the other. Sibling of the
  pi-axis / breaks_date Q-equivalent candidates.
- Not yet done: restructure into the tutorial step form (data/decompose/
  draw/save/main + --8<-- snippet markers, like tutorial_grand_tours.py);
  the datetime three-way tick story (nice breaks / jun-dec annotation minors
  / RRuleLocator recurrence-as-axis) for the tutorial page; the gallery entry
  + "which figure shows what" index + its guard tests; mkdocs nav.
- Calibration knobs (noise, bump sizes, raise size, c) are illustrative.
"""

import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ruptures as rpt
from matplotlib.dates import date2num, num2date

import vanzelfsprekend as vzs

FIGURES = Path(__file__).parents[1] / "docs" / "figures"

# --- model (simulated, not a measurement) ---
SEED = 20260912
BASE = 8.5  # log labour income, stable level
RAISE = 0.25  # permanent up-step (a pay rise)
RAISE_AT = (2018 - 2012) * 12 + 5  # 2018-06
HOLIDAY_PAY = 0.30  # June recurrent bump (vakantiegeld)
BONUS = 0.40  # December recurrent bump (eindejaarspremie)
RECUR_NOISE = 0.03  # year-to-year variation in the recurrent bumps
NOISE_SD = 0.04  # small monthly transient wobble

# --- decomposition (inspired by the phd; here a penalized median fit) ---
PEN = 2.0  # segmentation penalty: cost per extra piecewise-constant segment
MAD_WINDOW = 12
EPS_SIGMA = 0.005  # floor on the scale estimate
EPS_PERM = 0.02  # a permanent change must exceed this
C = 1.645  # one-sided 95% normal quantile

RECUR = "tol:high_contrast.yellow"
RAISE_C = "tol:high_contrast.blue"


def data() -> tuple[list[dt.date], np.ndarray]:
    """Return monthly dates and the simulated log labour-income series."""
    rng = np.random.default_rng(SEED)
    dates = [dt.date(y, m, 15) for y in range(2012, 2024) for m in range(1, 13)]
    months = np.array([d.month for d in dates])
    t = np.arange(len(dates))
    permanent = np.where(t < RAISE_AT, BASE, BASE + RAISE)
    recurrent = np.zeros(t.size)
    recurrent[months == 6] = HOLIDAY_PAY + rng.normal(
        0, RECUR_NOISE, (months == 6).sum()
    )
    recurrent[months == 12] = BONUS + rng.normal(0, RECUR_NOISE, (months == 12).sum())
    income = permanent + recurrent + rng.normal(0, NOISE_SD, t.size)
    return dates, income


def _segment_median(income: np.ndarray) -> np.ndarray:
    """Penalized median segmentation of the income series.

    A piecewise-constant fit whose segments take the median of their span.
    The L1 (median) cost is robust to the June/December bumps -- larger than
    the raise, but a minority in any span -- so they land in the residual,
    not as spurious steps.
    """
    algo = rpt.Pelt(model="l1", min_size=2, jump=1).fit(income)
    perm = np.empty(income.size)
    start = 0
    for end in algo.predict(pen=PEN):
        perm[start:end] = np.median(income[start:end])
        start = end
    return perm


def decompose(
    income: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return P-hat, nu-hat, the rolling scale sigma-hat, and dP-hat."""
    perm = _segment_median(income)
    nu = pd.Series(income - perm)

    def mad(x: np.ndarray) -> float:
        return np.median(np.abs(x - np.median(x)))

    sigma = (
        nu.rolling(MAD_WINDOW, min_periods=4).apply(mad, raw=True).bfill() * 1.4826
    ).clip(lower=EPS_SIGMA)
    dperm = pd.Series(perm).diff()
    return perm, nu.to_numpy(), sigma.to_numpy(), dperm.to_numpy()


def render() -> None:
    """Render the current three-panel decomposition figure."""
    dates, income = data()
    perm, nu, sigma, dperm = decompose(income)
    months = np.array([d.month for d in dates])
    dnum = np.array(dates)

    substantial = np.abs(nu) >= C * sigma
    jun = substantial & (months == 6) & (nu > 0)
    dec = substantial & (months == 12) & (nu > 0)
    raise_pts = np.abs(dperm) > EPS_PERM

    # Two y-groups (income+permanent, transient) on one x: both frame calls use
    # the same dates and x-mode, so the x-limits match and the panels align.
    fig, axes = plt.subplots(3, 1, figsize=(5.6, 6.2))
    fig.subplots_adjust(hspace=0.55)
    a_income, a_perm, a_nu = axes

    grey = {
        "color": vzs.palettes.LINE_INK,
        "marker": "o",
        "markersize": 2.2,
        "linewidth": 0.8,
    }
    a_income.plot(dates, income, **grey)
    a_perm.plot(dates, perm, **grey)
    a_perm.scatter(
        dnum[raise_pts], perm[raise_pts], s=24, color=RAISE_C, zorder=5, label="raise"
    )

    a_nu.plot(dates, nu, **grey)
    band = {"color": vzs.palettes.LINE_INK, "linewidth": 0.7, "linestyle": (0, (3, 3))}
    a_nu.plot(dates, C * sigma, **band)
    a_nu.plot(dates, -C * sigma, **band)
    a_nu.scatter(dnum[jun], nu[jun], s=14, color=RECUR, zorder=5, label="holiday pay")
    a_nu.scatter(dnum[dec], nu[dec], s=14, color=RECUR, zorder=5, label="bonus")

    # x: firm data start, loose (ongoing) end. y="data" on both groups.
    vzs.small_multiples(
        [a_income, a_perm],
        compare="figure",
        frame=(("data", "loose"), "data"),
        spacing=(6, 4),
    )
    vzs.apply(a_nu, frame=(("data", "loose"), "data"), spacing=(6, 4))

    vzs.ylabel(a_income, "Labour income")
    vzs.ylabel(a_perm, "Permanent component")
    vzs.ylabel(a_nu, "Transient component")

    # keep the frame's nice y ticks; add 0 as a minor reference
    a_nu.yaxis.set_minor_locator(vzs.FeatureLocator(date2num(dates), nu, [0.0]))
    a_nu.xaxis.set_minor_locator(
        vzs.FeatureLocator(
            date2num(dates),
            nu,
            [lambda x, y: x[np.isin([num2date(v).month for v in x], (6, 12))]],
        )
    )

    vzs.label(a_perm, "raise", x=date2num(dt.date(2018, 6, 15)))
    vzs.label(a_nu, "holiday pay", x=date2num(dt.date(2016, 6, 15)))
    vzs.label(a_nu, "bonus", x=date2num(dt.date(2021, 12, 15)))

    FIGURES.mkdir(exist_ok=True)
    fig.savefig(
        FIGURES / "labour_income_decomposition.svg",
        bbox_inches="tight",
        transparent=True,
    )
    plt.close(fig)


if __name__ == "__main__":
    render()
