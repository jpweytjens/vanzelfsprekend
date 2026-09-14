"""Build the labour-income decomposition figure one call at a time.

A simulated monthly labour-income series decomposed, inspired by a working
paper on consumption responses to labour income (not reproducing it), into a
permanent component and a transient component (the residual). Recurrent June
holiday pay and December bonuses (transient) and a one-off raise (permanent)
are the changes the decomposition surfaces. The final
step is the gallery's `labour_income_decomposition`; the earlier steps exist so
the tutorial can show what each call buys.

Settled so far
--------------
- Permanent component by penalized median segmentation (ruptures' Pelt, L1
  cost): one clean piecewise-constant step. The median cost is robust to the
  June/December bumps -- larger than the raise, but a minority in any span --
  so they land in the residual, not as spurious steps.
- Three stacked panels, each framed with apply. income + permanent share one y
  scale (small_multiples, compare="figure"), so the permanent step reads
  against income's variation; the transient stands alone. x per-end
  ("data","loose"): a firm 2012 start, a loose (ongoing) end; y="loose".
- Ticks live in the major slot via AugmentedLocator (nice union feature):
  transient y = nice union 0; transient x = nice years union named Jun/Dec;
  permanent y = nice union the two recovered levels (full-range spine, the
  colliding labels separate on their own). accent colours the named Jun/Dec
  ticks (holiday gold, bonus red) to match their scatter points, tying each
  axis mark to the example it stands for.
- Two-colour recurrent scheme (holiday gold, bonus red), blue raise. One
  callout per category via vzs.label; each recurrent example's callout, accent
  tick and scatter point share one anchor date so they cannot drift apart.
- Samples on the 1st of the month, so the firm start lands on a 2012 tick;
  two-decimal y labels on every panel.

Open threads
------------
- Not yet done: the gallery entry + its guard test. (The script is in the step
  form -- draw/compare/mark/name + --8<-- markers; `decomposition()` assembles
  the final gallery figure; the tutorial page is docs/tutorial/labour-income.md
  and the mkdocs nav points at it.)
- The tutorial cites the working paper it is inspired by in a sidenote
  (https://wps-feb.ugent.be/Papers/wp_23_1067.pdf).
- Library candidate (separate branch): give the vzs label family **kwargs
  routed to Text, like matplotlib's set_xlabel; a fontsize at label() creation
  feeds the placement solver (set_fontsize after placement does not).
- Calibration knobs (noise, bump sizes, raise size, C, PEN) are illustrative.
"""

import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ruptures as rpt
from matplotlib.dates import date2num

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

HOLIDAY_C = "tol:high_contrast.yellow"  # June holiday pay
BONUS_C = "tol:high_contrast.red"  # December bonus
RAISE_C = "tol:high_contrast.blue"  # the one-off raise
# One holiday pay and one bonus stand as the recurrent examples: each carries a
# label, an accented tick and the scatter point, all anchored to one date so
# they cannot drift apart.
HOLIDAY_AT = dt.date(2017, 6, 1)
BONUS_AT = dt.date(2017, 12, 1)
RAISE_AT_DATE = dt.date(2018, 6, 1)


def data() -> tuple[list[dt.date], np.ndarray]:
    """Return monthly dates and the simulated log labour-income series."""
    rng = np.random.default_rng(SEED)
    dates = [dt.date(y, m, 1) for y in range(2012, 2024) for m in range(1, 13)]
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


def features(
    dates: list[dt.date], nu: np.ndarray, sigma: np.ndarray, dperm: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the points the decomposition surfaces: the bumps and the raise.

    A transient value is substantial when |nu| clears the one-sided 95% band
    C * sigma; the recurrent ones fall in June and December, the raise where the
    permanent level steps.
    """
    months = np.array([d.month for d in dates])
    substantial = np.abs(nu) >= C * sigma
    jun = substantial & (months == 6) & (nu > 0)
    dec = substantial & (months == 12) & (nu > 0)
    raise_pts = np.abs(dperm) > EPS_PERM
    return jun, dec, raise_pts


def draw(
    dates: list[dt.date],
    income: np.ndarray,
    perm: np.ndarray,
    nu: np.ndarray,
    sigma: np.ndarray,
) -> tuple[plt.Figure, np.ndarray]:
    """Plot the three raw components on a fresh stack of axes."""
    plt.rcParams.update({"font.size": 8, "xtick.labelsize": 8, "ytick.labelsize": 8})
    # --8<-- [start:draw]
    fig, axes = plt.subplots(3, 1, figsize=(5.6, 6.2))
    fig.subplots_adjust(hspace=0.55)
    a_income, a_perm, a_nu = axes

    grey = {"color": vzs.palettes.LINE_INK, "marker": "o", "markersize": 2.2}
    a_income.plot(dates, income, linewidth=0.8, **grey)
    a_perm.plot(dates, perm, linewidth=0.8, **grey)
    a_nu.plot(dates, nu, linewidth=0.8, **grey)

    band = {"color": vzs.palettes.LINE_INK, "linewidth": 0.7, "linestyle": (0, (3, 3))}
    a_nu.plot(dates, C * sigma, **band)
    a_nu.plot(dates, -C * sigma, **band)
    # --8<-- [end:draw]
    return fig, axes


def compare(axes: np.ndarray) -> None:
    """Put income and the permanent step on one scale; frame the transient alone."""
    a_income, a_perm, a_nu = axes
    # --8<-- [start:compare]
    vzs.small_multiples(
        [a_income, a_perm],
        compare="figure",
        frame=(("data", "loose"), "loose"),
        spacing=(6, 4),
    )
    vzs.apply(a_nu, frame=(("data", "loose"), "loose"), spacing=(6, 4))
    vzs.ylabel(a_income, "Labour income")
    vzs.ylabel(a_perm, "Permanent component")
    vzs.ylabel(a_nu, "Transient component")
    # --8<-- [end:compare]


def mark(
    axes: np.ndarray,
    dates: list[dt.date],
    perm: np.ndarray,
    nu: np.ndarray,
    jun: np.ndarray,
    dec: np.ndarray,
    raise_pts: np.ndarray,
) -> None:
    """Union the frame's nice ticks with the decomposition's own features."""
    _, a_perm, a_nu = axes
    dnum = np.array(dates)
    # --8<-- [start:mark]
    a_perm.scatter(dnum[raise_pts], perm[raise_pts], s=24, color=RAISE_C, label="raise")
    a_nu.scatter(dnum[jun], nu[jun], s=14, color=HOLIDAY_C, label="holiday pay")
    a_nu.scatter(dnum[dec], nu[dec], s=14, color=BONUS_C, label="bonus")

    recur = vzs.FeatureLocator(
        date2num(dates), nu, {"Jun": date2num(HOLIDAY_AT), "Dec": date2num(BONUS_AT)}
    )
    a_nu.xaxis.set_major_locator(
        vzs.AugmentedLocator(a_nu.xaxis.get_major_locator(), recur)
    )
    a_nu.yaxis.set_major_locator(
        vzs.AugmentedLocator(a_nu.yaxis.get_major_locator(), [0.0])
    )
    a_perm.yaxis.set_major_locator(
        vzs.AugmentedLocator(a_perm.yaxis.get_major_locator(), np.unique(perm).tolist())
    )
    for panel in axes:
        panel.yaxis.set_major_formatter("{x:.2f}")
    # --8<-- [end:mark]


def name(axes: np.ndarray) -> None:
    """Name and colour the recurrent ticks; call out one of each and the raise."""
    _, a_perm, a_nu = axes
    # --8<-- [start:name]
    a_nu.vzs.accent(axis="x", label="name", color={"Jun": HOLIDAY_C, "Dec": BONUS_C})
    vzs.label(a_perm, "raise", x=date2num(RAISE_AT_DATE))
    vzs.label(a_nu, "holiday pay", x=date2num(HOLIDAY_AT))
    vzs.label(a_nu, "bonus", x=date2num(BONUS_AT))
    # --8<-- [end:name]


def decomposition() -> plt.Figure:
    """Assemble the final figure -- the gallery's `labour_income_decomposition`."""
    dates, income = data()
    perm, nu, sigma, dperm = decompose(income)
    jun, dec, raise_pts = features(dates, nu, sigma, dperm)
    fig, axes = draw(dates, income, perm, nu, sigma)
    compare(axes)
    mark(axes, dates, perm, nu, jun, dec, raise_pts)
    name(axes)
    return fig


def save(fig: plt.Figure, step: int) -> None:
    """Write one step's figure for the tutorial."""
    fig.savefig(
        FIGURES / f"labour_income_step_{step}.svg",
        bbox_inches="tight",
        transparent=True,
    )
    plt.close(fig)


def main() -> None:
    """Render the four tutorial steps."""
    FIGURES.mkdir(exist_ok=True)
    dates, income = data()
    perm, nu, sigma, dperm = decompose(income)
    jun, dec, raise_pts = features(dates, nu, sigma, dperm)

    fig, axes = draw(dates, income, perm, nu, sigma)
    save(fig, 1)

    fig, axes = draw(dates, income, perm, nu, sigma)
    compare(axes)
    save(fig, 2)

    fig, axes = draw(dates, income, perm, nu, sigma)
    compare(axes)
    mark(axes, dates, perm, nu, jun, dec, raise_pts)
    save(fig, 3)

    fig, axes = draw(dates, income, perm, nu, sigma)
    compare(axes)
    mark(axes, dates, perm, nu, jun, dec, raise_pts)
    name(axes)
    save(fig, 4)


if __name__ == "__main__":
    main()
