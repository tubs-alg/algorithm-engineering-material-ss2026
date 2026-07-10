"""pareto_front_knee: a Pareto-front approximation with a knee region.

For the "expose the alternatives" slide in `_03-many-solutions.qmd`. Dominated
cloud, front approximation, and a circled knee where a small sacrifice in one
objective buys a lot in the other. Synthetic illustrative data.
Run: python gen_pareto_front.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    T.init_style()
    rng = np.random.default_rng(7)
    x = np.linspace(0.05, 1.0, 16)
    y = 1.1 / (x + 0.15) + 0.04 * rng.normal(size=len(x))
    front = np.c_[x, y]
    cloud = front + np.c_[0.10 + 0.25 * rng.random(len(x)),
                          0.35 + 1.1 * rng.random(len(x))]

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.scatter(*cloud.T, s=90, color=T.FADED, edgecolor=T.MUTED,
               label="dominated alternatives")
    ax.scatter(*front.T, s=130, color=T.BLUE, zorder=3,
               label="Pareto-front approximation")
    ax.plot(*front.T, color=T.BLUE, alpha=0.5, zorder=2)
    knee = front[5]
    ax.scatter(*knee, s=340, facecolors="none", edgecolors=T.ORANGE, lw=3,
               zorder=4, label="knee region")
    # Anchor the extreme labels to their points and keep the text clear of the
    # upper boundary, the dominated cloud, and the legend.
    ax.annotate("best objective 1", xy=front[0], xytext=(0.22, 5.78),
                color=T.MUTED, fontsize=11, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=T.MUTED, lw=1.3),
                bbox=T.LABEL_BBOX)
    ax.annotate("best objective 2", xy=front[-1], xytext=(1.11, 1.55),
                color=T.MUTED, fontsize=11, ha="right", va="center",
                arrowprops=dict(arrowstyle="->", color=T.MUTED, lw=1.3),
                bbox=T.LABEL_BBOX)
    ax.set_xlabel("objective 1")
    ax.set_ylabel("objective 2")
    ax.legend(loc="upper right", fontsize=10.5, frameon=True,
              facecolor="#192433", edgecolor="none", framealpha=0.92)
    T.save(fig, os.path.join(OUT, "pareto_front_knee"))


if __name__ == "__main__":
    main()
