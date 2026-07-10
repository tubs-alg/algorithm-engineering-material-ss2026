"""Newsvendor figures: expected profit curve + the quantile the economics select.

For `_04-fragile-forecasts.qmd`. Two figures with the bakery numbers used on
the slides (p=10, c=4, v=1, so Cu=6, Co=3, alpha=2/3; D ~ Normal(100, 20^2)):

  newsvendor_expected_profit  expected profit vs. order quantity; the optimum
                              sits above mean demand because Cu > Co.
  newsvendor_quantile         demand density with the mean and the 67% quantile;
                              the shaded area is the critical fractile.

Run: python gen_newsvendor.py
"""

import math
import os
from statistics import NormalDist

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

P, C, V = 10.0, 4.0, 1.0
CU, CO = P - C, C - V
ALPHA = CU / (CU + CO)
MU, SIGMA = 100.0, 20.0
Q_STAR = MU + SIGMA * NormalDist().inv_cdf(ALPHA)


def expected_profit_fig() -> None:
    rng = np.random.default_rng(7)
    samples = np.maximum(0, rng.normal(MU, SIGMA, 200_000))
    qs = np.linspace(40, 170, 300)
    ep = [np.mean(P * np.minimum(q, samples) + V * np.maximum(q - samples, 0)
                  - C * q) for q in qs]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(qs, ep, lw=2.5, color=T.BLUE)
    ax.axvline(MU, ls="--", lw=1.6, color=T.MUTED, label="mean demand = 100")
    ax.axvline(Q_STAR, ls=":", lw=2.4, color=T.ORANGE,
               label=f"optimum $q^*$ = {Q_STAR:.0f}")
    ax.set_xlabel("order quantity $q$")
    ax.set_ylabel("expected profit")
    ax.legend(loc="lower right", fontsize=11)
    T.save(fig, os.path.join(OUT, "newsvendor_expected_profit"))


def quantile_fig() -> None:
    x = np.linspace(MU - 4 * SIGMA, MU + 4 * SIGMA, 500)
    pdf = np.exp(-0.5 * ((x - MU) / SIGMA) ** 2) / (SIGMA * math.sqrt(2 * math.pi))

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(x, pdf, lw=2.5, color=T.BLUE)
    ax.fill_between(x[x <= Q_STAR], pdf[x <= Q_STAR], alpha=0.25, color=T.BLUE)
    ax.axvline(MU, ls="--", lw=1.6, color=T.MUTED, label="mean = 100")
    ax.axvline(Q_STAR, ls=":", lw=2.4, color=T.ORANGE,
               label=f"{ALPHA:.0%} quantile = {Q_STAR:.0f}")
    ax.text(84, 0.004, f"$F(q^*) = {ALPHA:.2f}$", fontsize=13, color=T.FG,
            ha="center", bbox=T.LABEL_BBOX)
    ax.set_xlabel("demand")
    ax.set_ylabel("density")
    ax.set_yticks([])
    ax.legend(loc="upper right", fontsize=11)
    T.save(fig, os.path.join(OUT, "newsvendor_quantile"))


if __name__ == "__main__":
    T.init_style()
    expected_profit_fig()
    quantile_fig()
