"""archive: pool-based search keeps a nondominated archive, balanced for spread.

For the archive slide in `_03-many-solutions.qmd`. A candidate pool in
objective space; the nondominated archive highlighted, with spacing arrows
marking the diversity pressure (do not crowd one region of the front).
Synthetic illustrative data. Run: python gen_archive.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))


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
    rng = np.random.default_rng(3)
    pts = rng.uniform([0.1, 0.1], [1.0, 1.0], size=(60, 2))
    pts[:12, 1] = 1.05 / (pts[:12, 0] + 0.2) / 3.0
    pts[:12] = np.clip(pts[:12], 0.05, 1.0)
    dom = dominated_mask(pts)

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.scatter(*pts[dom].T, s=80, color=T.FADED, edgecolor=T.MUTED,
               label="candidate pool")
    ax.scatter(*pts[~dom].T, s=160, color=T.BLUE, zorder=3,
               label="nondominated archive")
    front = pts[~dom][np.argsort(pts[~dom][:, 0])]
    ax.plot(*front.T, color=T.BLUE, alpha=0.4, zorder=2)
    # Show representative adjacent gaps. Spanning across the middle point made
    # the arrows look like search transitions rather than spacing measurements.
    for i in range(0, len(front) - 1, 2):
        ax.annotate("", xy=front[i], xytext=front[i + 1],
                    arrowprops=dict(arrowstyle="<->", color=T.ORANGE, lw=1.6,
                                    alpha=0.9))
    ax.set_xlabel("objective 1")
    ax.set_ylabel("objective 2")
    ax.legend(loc="upper right", fontsize=11)
    T.save(fig, os.path.join(OUT, "archive"))


if __name__ == "__main__":
    main()
