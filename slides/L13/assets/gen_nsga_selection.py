"""nsga_selection: step-by-step survivor selection in NSGA-II.

For the NSGA-II intuition slide in `_03-many-solutions.qmd`. The frames show
how a fixed-size survivor pool reacts to quality pressure (front rank) and
diversity pressure (crowding distance when the next front does not fit).
Synthetic illustrative data. Run: python gen_nsga_selection.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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
    if len(remaining):
        fronts.append(remaining)
    return fronts


def crowding_distance(front: np.ndarray) -> np.ndarray:
    """NSGA-II crowding distance for a minimization front."""
    n, m = front.shape
    d = np.zeros(n)
    if n <= 2:
        d[:] = np.inf
        return d
    for j in range(m):
        order = np.argsort(front[:, j])
        vals = front[order, j]
        d[order[0]] = np.inf
        d[order[-1]] = np.inf
        span = vals[-1] - vals[0]
        if span == 0:
            continue
        for k in range(1, n - 1):
            d[order[k]] += (vals[k + 1] - vals[k - 1]) / span
    return d


def base_points() -> tuple[np.ndarray, np.ndarray]:
    rank1 = np.array([
        [0.10, 0.78],
        [0.22, 0.56],
        [0.36, 0.39],
        [0.54, 0.27],
        [0.74, 0.18],
        [0.93, 0.13],
    ])
    rank2 = np.array([
        [0.16, 0.86],
        [0.31, 0.65],
        [0.48, 0.49],
        [0.515, 0.46],
        [0.55, 0.43],
        [0.585, 0.40],
        [0.76, 0.32],
        [0.96, 0.25],
    ])
    cloud = np.array([
        [0.38, 0.79],
        [0.62, 0.68],
        [0.86, 0.50],
    ])
    parents = np.array([
        rank1[0],
        rank1[2],
        rank1[4],
        rank2[0],
        rank2[2],
        rank2[4],
        rank2[6],
        cloud[0],
    ])
    offspring = np.array([
        rank1[1],
        rank1[3],
        rank1[5],
        rank2[1],
        rank2[3],
        rank2[5],
        rank2[7],
        cloud[2],
        cloud[1],
    ])
    return parents, offspring


def setup_ax(title: str):
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.set_title(title, loc="left", pad=10)
    ax.set_xlabel("objective 1")
    ax.set_ylabel("objective 2")
    ax.set_xlim(0.06, 1.00)
    ax.set_ylim(0.09, 0.91)
    return fig, ax


def plot_front(ax, front: np.ndarray, color: str, label: str, size: int = 120,
               alpha: float = 1.0, zorder: int = 3) -> None:
    order = front[np.argsort(front[:, 0])]
    ax.plot(*order.T, color=color, lw=2.0, alpha=0.55 * alpha, zorder=zorder - 1)
    ax.scatter(*front.T, s=size, color=color, edgecolor="#0f1724",
               linewidth=0.9, alpha=alpha, label=label, zorder=zorder)


def objective_neighbor_box(front: np.ndarray, point: np.ndarray) -> tuple[float, float, float, float]:
    """Return the 2D box spanned by previous/next neighbors per objective."""
    idx = int(np.where(np.all(np.isclose(front, point), axis=1))[0][0])
    bounds = []
    for objective in range(front.shape[1]):
        order = np.argsort(front[:, objective])
        pos = int(np.where(order == idx)[0][0])
        lo_pos = max(pos - 1, 0)
        hi_pos = min(pos + 1, len(front) - 1)
        lo = min(front[order[lo_pos], objective], front[order[hi_pos], objective])
        hi = max(front[order[lo_pos], objective], front[order[hi_pos], objective])
        bounds.append((lo, hi))
    return bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]


def draw_neighbor_box(ax, front: np.ndarray, point: np.ndarray, color: str,
                      label: str, text_xy: tuple[float, float]) -> None:
    x0, x1, y0, y1 = objective_neighbor_box(front, point)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False,
                           edgecolor=color, linewidth=2.4, linestyle="-",
                           alpha=0.95, zorder=4))
    ax.annotate(label, xy=point, xytext=text_xy, color=color, fontsize=11.5,
                arrowprops=dict(arrowstyle="->", color=color, lw=1.5),
                bbox=T.LABEL_BBOX, zorder=6)


def save_frame(fig, idx: int) -> None:
    T.save(fig, os.path.join(OUT, f"nsga_selection_{idx}"))


def main() -> None:
    T.init_style(base_fontsize=13)
    parents, offspring = base_points()
    points = np.vstack([parents, offspring])
    fronts = peel_fronts(points, 4)
    capacity = 12
    slots_after_rank1 = capacity - len(fronts[0])
    rank2 = fronts[1]
    distances = crowding_distance(rank2)
    keep_rank2 = np.argsort(-distances)[:slots_after_rank1]
    drop_rank2 = np.setdiff1d(np.arange(len(rank2)), keep_rank2)
    selected = np.vstack([fronts[0], rank2[keep_rank2]])

    fig, ax = setup_ax("1  Generate candidates and merge with the current pool")
    ax.scatter(*parents.T, s=115, color=T.BLUE, edgecolor="#0f1724",
               linewidth=0.9, label="current pool")
    ax.scatter(*offspring.T, s=120, marker="D", color=T.ORANGE,
               edgecolor="#0f1724", linewidth=0.9, label="new candidates")
    ax.text(0.07, 0.12, "temporary pool is larger than the survivor budget",
            color=T.MUTED, bbox=T.LABEL_BBOX)
    ax.legend(loc="upper right", fontsize=10.5, frameon=True,
              facecolor="#192433", edgecolor="none", framealpha=0.92)
    save_frame(fig, 1)

    fig, ax = setup_ax("2  Sort the merged pool into nondominated fronts")
    colors = [T.BLUE, T.GOLD, T.PURPLE, T.FADED]
    labels = ["rank 1", "rank 2", "rank 3", "later ranks"]
    for front, color, label in zip(fronts, colors, labels):
        plot_front(ax, front, color, label, size=118 if label != "later ranks" else 72,
                   alpha=0.85 if label != "later ranks" else 0.65)
    ax.text(0.07, 0.12, "quality pressure: lower rank survives first",
            color=T.FG, bbox=T.LABEL_BBOX)
    ax.legend(loc="upper right", fontsize=10.5, frameon=True,
              facecolor="#192433", edgecolor="none", framealpha=0.92)
    save_frame(fig, 2)

    fig, ax = setup_ax("3  Fill the survivor pool front by front")
    plot_front(ax, fronts[0], T.GREEN, f"rank 1 accepted ({len(fronts[0])} slots)")
    plot_front(ax, rank2, T.GOLD, "rank 2 waits", alpha=0.85)
    if len(fronts) > 2:
        ax.scatter(*np.vstack(fronts[2:]).T, s=65, color=T.FADED,
                   edgecolor=T.MUTED, alpha=0.55, label="not reached")
    ax.text(0.07, 0.12,
            f"budget {capacity}: rank 1 fits, only {slots_after_rank1} slots remain",
            color=T.FG, bbox=T.LABEL_BBOX)
    ax.legend(loc="upper right", fontsize=10.5, frameon=True,
              facecolor="#192433", edgecolor="none", framealpha=0.92)
    save_frame(fig, 3)

    fig, ax = setup_ax("4  Rank 2 does not fit: use crowding distance")
    plot_front(ax, fronts[0], T.BLUE, "already accepted", alpha=0.6)
    order = rank2[np.argsort(rank2[:, 0])]
    ax.plot(*order.T, color=T.GOLD, lw=2.0, alpha=0.35)
    ax.scatter(*rank2[keep_rank2].T, s=145, color=T.GREEN,
               edgecolor="#0f1724", linewidth=0.9, label="kept: high distance")
    ax.scatter(*rank2[drop_rank2].T, s=145, facecolors="none", edgecolors=T.RED,
               linewidth=2.3, label="dropped: smallest distance")
    draw_neighbor_box(ax, rank2, np.array([0.31, 0.65]), T.ORANGE,
                      "large objective-wise\nneighbor box", (0.29, 0.78))
    draw_neighbor_box(ax, rank2, np.array([0.515, 0.46]), T.RED,
                      "small box:\ncrowded region", (0.63, 0.54))
    ax.text(0.07, 0.12,
            "crowding distance sums previous/next gaps per objective",
            color=T.FG, fontsize=11.5, bbox=T.LABEL_BBOX)
    ax.legend(loc="upper right", fontsize=10.5, frameon=True,
              facecolor="#192433", edgecolor="none", framealpha=0.92)
    save_frame(fig, 4)

    fig, ax = setup_ax("5  The next generation keeps quality and spread")
    ax.scatter(*selected.T, s=150, color=T.GREEN, edgecolor="#0f1724",
               linewidth=0.9, label="survivor pool")
    rejected = np.array([p for p in points if not np.any(np.all(selected == p, axis=1))])
    ax.scatter(*rejected.T, s=75, color=T.FADED, edgecolor=T.MUTED,
               alpha=0.55, label="discarded")
    ax.text(0.07, 0.12,
            "reaction: dominated/crowded candidates lose their pool slots",
            color=T.FG, bbox=T.LABEL_BBOX)
    ax.legend(loc="upper right", fontsize=10.5, frameon=True,
              facecolor="#192433", edgecolor="none", framealpha=0.92)
    save_frame(fig, 5)


if __name__ == "__main__":
    main()
