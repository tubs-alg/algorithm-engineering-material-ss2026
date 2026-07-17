"""Newsvendor critical-fractile figure: demand density, mean, and the quantile
the economics select.

For `_02-sda.qmd` (the newsvendor slide). Numbers: underage Cu=6, overage Co=3,
so the critical fractile alpha = Cu/(Cu+Co) = 2/3; demand D ~ Normal(100, 20^2).
The optimal order sits *above* the mean because a lost sale hurts more than a
wasted unit. Adapted from the L13 gen_newsvendor.py.

Run: python gen_newsvendor.py
"""

import math
import os
from statistics import NormalDist

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

CU, CO = 6.0, 3.0
ALPHA = CU / (CU + CO)
MU, SIGMA = 100.0, 20.0
Q_STAR = MU + SIGMA * NormalDist().inv_cdf(ALPHA)


def main() -> None:
    x = np.linspace(MU - 4 * SIGMA, MU + 4 * SIGMA, 500)
    pdf = np.exp(-0.5 * ((x - MU) / SIGMA) ** 2) / (SIGMA * math.sqrt(2 * math.pi))

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.plot(x, pdf, lw=2.5, color=T.BLUE)
    ax.fill_between(x[x <= Q_STAR], pdf[x <= Q_STAR], alpha=0.22, color=T.BLUE)
    ax.axvline(MU, ls="--", lw=1.6, color=T.MUTED, label="mean demand = 100")
    ax.axvline(Q_STAR, ls=":", lw=2.6, color=T.ORANGE,
               label=f"optimal order $q^*$ = {Q_STAR:.0f}")
    ax.text(84, 0.004, f"$F(q^*)=\\dfrac{{C_u}}{{C_u+C_o}}={ALPHA:.2f}$",
            fontsize=13, color=T.FG, ha="center", bbox=T.LABEL_BBOX)
    ax.set_xlabel("demand")
    ax.set_ylabel("density")
    ax.set_yticks([])
    ax.legend(loc="upper right", fontsize=11)
    T.save(fig, os.path.join(OUT, "newsvendor_quantile"))


if __name__ == "__main__":
    T.init_style()
    main()
