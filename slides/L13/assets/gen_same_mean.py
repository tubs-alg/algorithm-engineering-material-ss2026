"""same_mean_different_risk: a point forecast hides the uncertainty structure.

For the predict-then-optimize slides in `_04-fragile-forecasts.qmd`. Two demand
distributions with the same mean (100) but different spread; with Cu=9, Co=1
the newsvendor needs the 90% quantile, which differs sharply between them.
A deterministic optimizer fed only "100" cannot tell them apart.
Run: python gen_same_mean.py
"""

import math
import os
from statistics import NormalDist

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

MU = 100.0
ALPHA = 0.9


def main() -> None:
    T.init_style()
    x = np.linspace(0, 220, 600)

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    for sigma, color in [(10.0, T.BLUE), (30.0, T.PURPLE)]:
        pdf = np.exp(-0.5 * ((x - MU) / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))
        q = MU + sigma * NormalDist().inv_cdf(ALPHA)
        ax.plot(x, pdf, lw=2.5, color=color,
                label=f"$\\sigma$ = {sigma:.0f}: 90% quantile = {q:.0f}")
        ax.axvline(q, ls="--", lw=1.8, color=color, alpha=0.8)
    ax.axvline(MU, lw=2, color=T.MUTED, label="same mean = 100")
    ax.set_xlabel("demand")
    ax.set_ylabel("density")
    ax.set_yticks([])
    ax.legend(loc="upper left", fontsize=11)
    T.save(fig, os.path.join(OUT, "same_mean_different_risk"))


if __name__ == "__main__":
    main()
