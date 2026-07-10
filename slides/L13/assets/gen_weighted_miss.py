"""weighted_miss: weighted sums only reach supported Pareto points.

For the weighted-sum traps slide in `_02-one-solution.qmd`. A discrete Pareto
front with one efficient point lying inside the concave region between its
neighbors: no linear weight vector makes it optimal. Synthetic illustrative
data. Run: python gen_weighted_miss.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    T.init_style()
    front = np.array([[1, 8], [2, 5.5], [3.2, 4.6], [6.8, 3.2], [8, 1]])
    others = np.array([[3.5, 7], [5.5, 6.5], [7, 5.5]])
    unsupported = np.array([6.8, 3.2])

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.scatter(*front.T, s=150, color=T.BLUE, zorder=3, label="efficient")
    ax.scatter(*others.T, s=110, color=T.FADED, edgecolor=T.MUTED, zorder=2,
               label="dominated")
    ax.plot([3.2, 8.0], [4.6, 1.0], ls="--", color=T.MUTED, lw=1.8,
            label="convex-hull edge", zorder=2)
    ax.scatter(*unsupported, s=320, facecolors="none", edgecolors=T.ORANGE,
               linewidth=3, zorder=4)
    ax.annotate("optimal for no\nweighted sum", xy=unsupported, xytext=(4.6, 7.35),
                arrowprops=dict(arrowstyle="->", color=T.ORANGE), color=T.ORANGE,
                fontsize=13)
    ax.set_xlabel("objective 1")
    ax.set_ylabel("objective 2")
    # Keep the legend in genuinely empty space. The previous vertical legend
    # covered the low-objective points and made its marker samples look like
    # additional observations.
    ax.legend(loc="lower center", ncol=3, fontsize=9.5, frameon=True,
              facecolor="#192433", edgecolor="none", framealpha=0.92,
              columnspacing=1.2, handletextpad=0.5)
    T.save(fig, os.path.join(OUT, "weighted_miss"))


if __name__ == "__main__":
    main()
