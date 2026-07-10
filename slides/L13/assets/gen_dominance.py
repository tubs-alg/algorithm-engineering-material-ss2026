"""dominance_scatter: repair schedules in objective space, dominated vs. nondominated.

For the dominance slide in `_01-what-is-better.qmd`. Ten candidate repair
schedules plotted in (tardiness, changeovers); nondominated points highlighted
with a staircase front, dominated points faded. A, B, C match the table on the
preceding slide (C is dominated by A and B; A vs. B is a genuine trade-off).
Synthetic illustrative data. Run: python gen_dominance.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

POINTS = np.array([
    [100, 20], [120, 12], [150, 25], [90, 30], [140, 9],
    [115, 18], [130, 15], [160, 8], [105, 23], [145, 20],
])
LABELS = list("ABCDEFGHIJ")


def dominated_mask(points: np.ndarray) -> np.ndarray:
    dom = []
    for i, p in enumerate(points):
        dom.append(any(
            np.all(q <= p) and np.any(q < p)
            for j, q in enumerate(points) if i != j
        ))
    return np.array(dom)


def main() -> None:
    T.init_style()
    dom = dominated_mask(POINTS)

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    front = POINTS[~dom][np.argsort(POINTS[~dom][:, 0])]
    # Staircase through the nondominated points (minimization in both axes).
    xs, ys = [], []
    for k, (x, y) in enumerate(front):
        if k > 0:
            xs.append(x)
            ys.append(front[k - 1][1])
        xs.append(x)
        ys.append(y)
    ax.plot(xs, ys, color=T.BLUE, alpha=0.45, lw=2, zorder=1)

    ax.scatter(*POINTS[~dom].T, s=150, color=T.BLUE, zorder=3, label="nondominated")
    ax.scatter(*POINTS[dom].T, s=120, color=T.FADED, edgecolor=T.MUTED,
               zorder=2, label="dominated")
    for (x, y), lab in zip(POINTS, LABELS):
        ax.text(x + 1.6, y + 0.4, lab, fontsize=13, color=T.FG)

    ax.set_xlabel("total tardiness")
    ax.set_ylabel("changeovers")
    ax.legend(loc="upper right")
    T.save(fig, os.path.join(OUT, "dominance_scatter"))


if __name__ == "__main__":
    main()
