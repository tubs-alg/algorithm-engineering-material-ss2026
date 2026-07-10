"""Two label-free icons for the "Two assumptions worth dropping" intro slide.

What this file contains
------------------------
`intro_multiobjective.png`: a bare Pareto scatter (dominated cloud + nondominated
staircase front, no axes/legend/labels) illustrating "quality is multidimensional".
`intro_uncertainty.png`: a bare density curve with a dashed point-forecast line and
scattered realized outcomes, illustrating "reality is uncertain". Both mirror the
textless-icon convention from week08-t04's gen_intro_figs.py: same vocabulary as the
deck's later, labeled figures (dominance_scatter.py, same_mean_different_risk.py),
just stripped down to read at small column width.

Why it exists
-------------
The intro slide previously stated both assumptions as bullet text only. Created
2026-07-07 to give each column a genuine small visual instead of relying on layout
alone, per Dominik's request to match the T04/T05 two/three-column intro pattern.

How to run
----------
    conda run -n mo312 python gen_intro_icons.py
    # writes intro_multiobjective.png and intro_uncertainty.png (transparent, dark style)

When it should change
----------------------
Retune if the intro's framing of either assumption changes, or if the icon style
drifts from the deck's other bare icons.
"""

import os

import numpy as np
from scipy.stats import norm

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))
ICON_SIZE = (5.0, 2.0)


def _bare(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def dominated_mask(points: np.ndarray) -> np.ndarray:
    dom = []
    for i, p in enumerate(points):
        dom.append(any(
            np.all(q <= p) and np.any(q < p)
            for j, q in enumerate(points) if i != j
        ))
    return np.array(dom)


def fig_multiobjective() -> None:
    rng = np.random.default_rng(3)
    x = np.linspace(0.05, 1.0, 9)
    y = 1.1 / (x + 0.15) + 0.05 * rng.normal(size=len(x))
    front = np.c_[x, y]
    cloud = front + np.c_[0.10 + 0.22 * rng.random(len(x)),
                          0.30 + 0.9 * rng.random(len(x))]
    all_pts = np.vstack([front, cloud])
    x0, x1 = all_pts[:, 0].min() - 0.10, all_pts[:, 0].max() + 0.15
    y0, y1 = all_pts[:, 1].min() - 0.35, all_pts[:, 1].max() + 0.55

    fig, ax = plt.subplots(figsize=ICON_SIZE)
    ax.scatter(*cloud.T, s=110, color=T.FADED, edgecolor=T.MUTED, zorder=2)
    ax.plot(*front.T, color=T.BLUE, alpha=0.5, lw=2.4, zorder=1)
    ax.scatter(*front.T, s=150, color=T.BLUE, zorder=3)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    _bare(ax)
    # Minimal coordinate frame (two arrows from the plot's own corner) instead
    # of numeric ticks: enough to read this as "objective space", not a chart.
    ax.annotate("", xy=(x1, y0), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=T.MUTED, lw=1.6))
    ax.annotate("", xy=(x0, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=T.MUTED, lw=1.6))
    ax.annotate("objective 1", xy=(x1, y0), xytext=(-2, -8),
                textcoords="offset points", color=T.MUTED, fontsize=13,
                ha="right", va="top")
    ax.annotate("objective 2", xy=(x0, y1), xytext=(-10, -2),
                textcoords="offset points", color=T.MUTED, fontsize=13,
                ha="right", va="top", rotation=90)
    T.save(fig, os.path.join(OUT, "intro_multiobjective"), pad=0.06)


def fig_uncertainty() -> None:
    mu, sigma = 0.0, 1.0
    x = np.linspace(mu - 3.4 * sigma, mu + 3.4 * sigma, 400)
    pdf = np.exp(-0.5 * ((x - mu) / sigma) ** 2)

    fig, ax = plt.subplots(figsize=ICON_SIZE)
    ax.fill_between(x, pdf, color=T.PURPLE, alpha=0.35, zorder=1)
    ax.plot(x, pdf, color=T.PURPLE, lw=2.2, zorder=2)
    ax.axvline(mu, color=T.FG, ls="--", lw=2.0, zorder=3)
    # Evenly spaced probability mass (not evenly spaced z-scores), mapped
    # through the inverse CDF: samples cluster near the mean and thin out in
    # the tails exactly as real draws from this distribution would.
    probs = (np.arange(11) + 0.5) / 11
    samples = norm.ppf(probs, loc=mu, scale=sigma)
    ax.scatter(samples, -0.05 * np.ones_like(samples), s=90, color=T.GOLD,
               edgecolor=T.MUTED, zorder=4, clip_on=False)
    ax.set_ylim(-0.08, 1.05)
    _bare(ax)
    T.save(fig, os.path.join(OUT, "intro_uncertainty"), pad=0.04)


def main() -> None:
    T.init_style()
    fig_multiobjective()
    fig_uncertainty()


if __name__ == "__main__":
    main()
