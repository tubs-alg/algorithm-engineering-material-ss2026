"""price_of_robustness: protection rises with the uncertainty budget, so does cost.

For `_06-robust.qmd`. Nominal-cost increase and protection level against the
uncertainty budget Gamma on one axis pair: growing the set buys protection and
pays with conservatism. Synthetic illustrative curves (shape follows the
budgeted-uncertainty story of Bertsimas & Sim 2004).
Run: python gen_price_robustness.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    T.init_style()
    gamma = np.linspace(0, 10, 101)
    gamma_mark = np.arange(0, 11)
    # Protection saturates fast; cost stays flat early, then accelerates so the
    # "cheap protection now, paying for corner cases later" story is visible.
    protection = 1 - np.exp(-0.55 * gamma)
    rel_cost = 1 + 0.004 * gamma + 0.0062 * gamma ** 2
    protection_mark = 1 - np.exp(-0.55 * gamma_mark)
    rel_cost_mark = 1 + 0.004 * gamma_mark + 0.0062 * gamma_mark ** 2

    fig, ax1 = plt.subplots(figsize=(7.4, 4.4))
    ax1.plot(gamma, rel_cost, lw=2.5, color=T.ORANGE)
    ax1.plot(gamma_mark, rel_cost_mark, "o", color=T.ORANGE)
    ax1.set_xlabel("uncertainty budget $\\Gamma$")
    ax1.set_ylabel("relative nominal cost", color=T.ORANGE)
    ax1.tick_params(axis="y", labelcolor=T.ORANGE)
    ax1.set_ylim(0.95, 1.72)

    ax2 = ax1.twinx()
    ax2.plot(gamma, protection, ls="--", lw=2.5, color=T.BLUE)
    ax2.plot(gamma_mark, protection_mark, "s", color=T.BLUE)
    ax2.set_ylabel("protection level", color=T.BLUE)
    ax2.tick_params(axis="y", labelcolor=T.BLUE)
    ax2.set_ylim(0, 1.05)
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(T.GRID)

    ax1.annotate("cheap protection", xy=(1.5, 1.023), xytext=(2.2, 1.16),
                 color=T.FG, fontsize=12, ha="center",
                 arrowprops=dict(arrowstyle="->", color=T.MUTED))
    ax1.annotate("paying for corner cases", xy=(8.7, 1.50), xytext=(6.9, 1.60),
                 color=T.FG, fontsize=12, ha="center",
                 arrowprops=dict(arrowstyle="->", color=T.MUTED))

    T.save(fig, os.path.join(OUT, "price_of_robustness"))


if __name__ == "__main__":
    main()
