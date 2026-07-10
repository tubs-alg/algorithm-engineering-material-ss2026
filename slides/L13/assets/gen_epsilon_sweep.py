"""epsilon_sweep: the epsilon-constraint method as a front generator.

For the epsilon-constraint slide in `_02-one-solution.qmd`. Trade-off points
in (tardiness, changeovers); a bound "changeovers <= 12" excludes part of the
set and the solver minimizes tardiness among the rest. Synthetic illustrative
data. Run: python gen_epsilon_sweep.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    T.init_style()
    pts = np.array([[90, 28], [100, 20], [112, 16], [120, 12], [135, 10],
                    [150, 8], [170, 7]])
    eps = 12
    feas = pts[:, 1] <= eps

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.scatter(*pts[~feas].T, s=130, color=T.FADED, edgecolor=T.MUTED,
               label="excluded by $\\epsilon$")
    ax.scatter(*pts[feas].T, s=150, color=T.BLUE, label="feasible for $\\epsilon$")
    best = pts[feas][np.argmin(pts[feas][:, 0])]
    ax.scatter(*best, s=340, facecolors="none", edgecolors=T.GREEN, linewidth=3,
               label="selected solution")
    ax.axhline(eps, color=T.ORANGE, ls="--", lw=2,
               label=f"$\\epsilon$ = {eps} changeovers")
    ax.set_xlabel("tardiness (minimized)")
    ax.set_ylabel("changeovers (bounded)")
    ax.legend(loc="upper right", fontsize=11)
    T.save(fig, os.path.join(OUT, "epsilon_sweep"))


if __name__ == "__main__":
    main()
