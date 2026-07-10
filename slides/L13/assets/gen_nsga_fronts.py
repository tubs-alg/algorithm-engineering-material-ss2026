"""nsga_fronts: nondominated sorting peels a population into ranked fronts.

For the NSGA-II slide in `_03-many-solutions.qmd`. A candidate population in
objective space is partitioned into nondominated layers (rank 1, 2, 3, rest);
orange spacing arrows on the best front mark the crowding-distance diversity
pressure. Synthetic illustrative data. Run: python gen_nsga_fronts.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))


def nondominated_mask(points: np.ndarray) -> np.ndarray:
    dom = []
    for i, p in enumerate(points):
        dom.append(any(
            np.all(q <= p) and np.any(q < p)
            for j, q in enumerate(points) if i != j
        ))
    return ~np.array(dom)


def peel_fronts(points: np.ndarray, n_fronts: int) -> list[np.ndarray]:
    remaining = points.copy()
    fronts = []
    for _ in range(n_fronts):
        mask = nondominated_mask(remaining)
        fronts.append(remaining[mask])
        remaining = remaining[~mask]
        if len(remaining) == 0:
            break
    fronts.append(remaining)
    return fronts


def main() -> None:
    T.init_style()
    # Explicit illustrative population.  The fronts are deliberately separated
    # enough for a slide; ranks are still computed by nondominated sorting.
    rank1_seed = np.array([
        [0.10, 0.76],
        [0.20, 0.56],
        [0.34, 0.39],
        [0.50, 0.27],
        [0.66, 0.19],
        [0.82, 0.14],
        [0.94, 0.115],
    ])
    rank2_seed = rank1_seed + np.array([0.045, 0.115])
    rank3_seed = rank1_seed[[1, 2, 3, 4, 5]] + np.array([0.080, 0.225])
    cloud = np.array([
        [0.30, 0.91],
        [0.40, 0.82],
        [0.48, 0.70],
        [0.58, 0.58],
        [0.70, 0.47],
        [0.82, 0.38],
        [0.93, 0.31],
        [0.96, 0.72],
    ])
    pts = np.vstack([rank1_seed, rank2_seed, rank3_seed, cloud])
    fronts = peel_fronts(pts, 3)

    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    styles = [
        (T.BLUE, 160, "rank 1"),
        (T.GOLD, 120, "rank 2"),
        (T.PURPLE, 105, "rank 3"),
    ]
    for front, (color, size, label) in zip(fronts[:3], styles):
        order = front[np.argsort(front[:, 0])]
        ax.plot(*order.T, color=color, alpha=0.52, lw=2.0, zorder=2)
        ax.scatter(*front.T, s=size, color=color, edgecolor="#0f1724",
                   linewidth=0.9, zorder=3, label=label)
    if len(fronts) > 3 and len(fronts[3]):
        ax.scatter(*fronts[3].T, s=54, color=T.FADED, edgecolor=T.MUTED,
                   alpha=0.78, linewidth=1.0, label="worse ranks", zorder=1)
    # Crowding-distance pressure: draw a few readable neighbor gaps on rank 1.
    best = fronts[0][np.argsort(fronts[0][:, 0])]
    for i in [1, 3, 5]:
        ax.annotate("", xy=best[i], xytext=best[i + 1],
                    arrowprops=dict(arrowstyle="<->", color=T.ORANGE, lw=2.0,
                                    shrinkA=10, shrinkB=10, alpha=0.95))
    ax.annotate("crowding distance\nkeeps spread", xy=(0.59, 0.22),
                xytext=(0.51, 0.78), color=T.ORANGE, fontsize=12,
                arrowprops=dict(arrowstyle="->", color=T.ORANGE, lw=1.7),
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                          edgecolor="none", alpha=0.88))
    ax.set_xlabel("objective 1")
    ax.set_ylabel("objective 2")
    ax.set_xlim(0.05, 1.03)
    ax.set_ylim(0.06, 1.04)
    ax.legend(loc="upper right", fontsize=10.5, frameon=True,
              facecolor="#192433", edgecolor="none", framealpha=0.92)
    T.save(fig, os.path.join(OUT, "nsga_fronts"))


if __name__ == "__main__":
    main()
