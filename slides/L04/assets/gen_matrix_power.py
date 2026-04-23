"""Matrix-power path-counting visual: A^k counts k-edge walks.

Emits THREE PNGs — matrix_power_1.png, matrix_power_2.png,
matrix_power_3.png — one per power. Each frame shows the same 6-node
layered DAG on the left (straight-line drawing, no curved edges) with
the length-k walks highlighted, and the corresponding matrix A^k on
the right with one cell highlighted.

The three frames are designed to be shown as successive slide fragments,
so the visual "story" is: 1 walk -> 2 walks -> 3 walks, matching the
highlighted matrix entry growing 1 -> 2 -> 3.

    A[0][1]   = 1   -- 0 -> 1
    A^2[0][4] = 2   -- 0 -> 1 -> 4,       0 -> 2 -> 4
    A^3[0][5] = 3   -- 0 -> 1 -> 3 -> 5,  0 -> 1 -> 4 -> 5,  0 -> 2 -> 4 -> 5

The graph is a DAG (no back edges) so every edge is a clean straight
line between layers; the matrices are upper-triangular with a nilpotent
tail (A^4 = 0) which is conceptually pleasing but not shown here.

Regenerate with `python gen_matrix_power.py`.
"""

from __future__ import annotations

import numpy as np
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, FG, NEGATIVE, setup_mpl,
)

setup_mpl()


# --- Graph: 6-node layered DAG, straight-line drawing ---------------------
N = 6
EDGES = [
    (0, 1), (0, 2),
    (1, 3), (1, 4),
    (2, 4),
    (3, 5),
    (4, 5),
]

A = np.zeros((N, N), dtype=int)
for u, v in EDGES:
    A[u, v] = 1
A2 = A @ A
A3 = A2 @ A

# Node positions — chosen so every edge can be drawn as a straight line
# without passing through any other node. Layers at x = 0, 1.4, 2.8, 4.2.
POS = {
    0: (0.0, 1.5),
    1: (1.4, 2.7),
    2: (1.4, 0.3),
    3: (2.8, 2.7),
    4: (2.8, 1.5),
    5: (4.2, 1.5),
}

WALK_COLORS = [NEGATIVE, ACCENT, CELL["index"]]

FRAMES = {
    1: {
        "matrix": A,
        "title": "A",
        "cell": (0, 1),
        "walks": [[(0, 1)]],
        "walk_strs": ["0 → 1"],
        "header": "1 length-1 walk from 0 to 1",
    },
    2: {
        "matrix": A2,
        "title": "A²  =  A · A",
        "cell": (0, 4),
        "walks": [[(0, 1), (1, 4)], [(0, 2), (2, 4)]],
        "walk_strs": ["0 → 1 → 4", "0 → 2 → 4"],
        "header": "2 length-2 walks from 0 to 4",
    },
    3: {
        "matrix": A3,
        "title": "A³  =  A² · A",
        "cell": (0, 5),
        "walks": [
            [(0, 1), (1, 3), (3, 5)],
            [(0, 1), (1, 4), (4, 5)],
            [(0, 2), (2, 4), (4, 5)],
        ],
        "walk_strs": [
            "0 → 1 → 3 → 5",
            "0 → 1 → 4 → 5",
            "0 → 2 → 4 → 5",
        ],
        "header": "3 length-3 walks from 0 to 5",
    },
}


def draw_graph(ax, walks):
    """Draw the shared 6-node graph with the given walks highlighted.

    `walks` is a list of walks; each walk is a list of directed edges.
    All edges in any walk are drawn in the accent colour with heavier
    stroke. All other edges are drawn muted. Every edge is a straight
    line between node centres — this is what the user asked for.
    """
    ax.set_title(
        "Graph  (6 nodes, 7 directed edges, DAG)",
        fontsize=11, color=FG, loc="left", pad=8,
    )

    NODE_R = 0.17

    highlighted: set[tuple[int, int]] = set()
    for w in walks:
        highlighted.update(w)

    def _shrink(x1, y1, x2, y2, r=NODE_R):
        dx, dy = x2 - x1, y2 - y1
        d = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / d, dy / d
        return x1 + ux * r, y1 + uy * r, x2 - ux * r, y2 - uy * r

    # Muted edges first, highlighted on top.
    for (u, v) in EDGES:
        x1, y1 = POS[u]
        x2, y2 = POS[v]
        sx, sy, ex, ey = _shrink(x1, y1, x2, y2)
        is_hl = (u, v) in highlighted
        color = CELL["warn"] if is_hl else "#6a6a80"
        lw = 2.4 if is_hl else 1.3
        ax.annotate(
            "", xy=(ex, ey), xytext=(sx, sy),
            arrowprops=dict(
                arrowstyle="-|>", color=color, lw=lw,
                shrinkA=0, shrinkB=0,
                connectionstyle="arc3,rad=0",
            ),
        )

    # Nodes — endpoints of the highlighted walks get the accent fill.
    endpoints = set()
    for w in walks:
        if w:
            endpoints.add(w[0][0])
            endpoints.add(w[-1][1])
    for n, (x, y) in POS.items():
        face = CELL["warn"] if n in endpoints else CELL["data"]
        circ = mpatches.Circle(
            (x, y), NODE_R, facecolor=face, edgecolor=FG, lw=1.2, zorder=5,
        )
        ax.add_patch(circ)
        ax.text(
            x, y, str(n), ha="center", va="center",
            fontsize=11, color="white", fontweight="bold",
            fontfamily="monospace", zorder=6,
        )

    ax.set_xlim(-0.5, 4.7)
    ax.set_ylim(-0.4, 3.3)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_matrix(ax, M, title, *, highlight):
    ax.set_title(title, fontsize=12, color=FG, loc="left", pad=8)
    n = M.shape[0]
    cell = 0.6
    x0, y0 = 0.4, 0.3

    for c in range(n):
        ax.text(
            x0 + c * cell + cell / 2, y0 + n * cell + 0.15, str(c),
            ha="center", va="bottom",
            fontsize=10, color=CELL["index"],
            fontfamily="monospace", fontweight="bold",
        )
    for r in range(n):
        y = y0 + (n - 1 - r) * cell + cell / 2
        ax.text(
            x0 - 0.12, y, str(r),
            ha="right", va="center",
            fontsize=10, color=CELL["index"],
            fontfamily="monospace", fontweight="bold",
        )

    for r in range(n):
        for c in range(n):
            x = x0 + c * cell
            y = y0 + (n - 1 - r) * cell
            v = int(M[r, c])
            is_hero = (r, c) == highlight
            if is_hero:
                face = CELL["warn"]
                tc = "white"
                lw = 1.8
                edge = CELL["cache"]
            elif v > 0:
                face = CELL["data"] if v == 1 else "#5a8ab0"
                tc = "white"
                lw = 0.5
                edge = FG
            else:
                face = "#1a1a2e"
                tc = "#555"
                lw = 0.5
                edge = FG
            rect = mpatches.FancyBboxPatch(
                (x + 0.02, y + 0.02), cell - 0.04, cell - 0.04,
                boxstyle="round,pad=0.02",
                facecolor=face, edgecolor=edge, linewidth=lw,
            )
            ax.add_patch(rect)
            label = str(v) if v > 0 else "·"
            ax.text(
                x + cell / 2, y + cell / 2, label,
                ha="center", va="center",
                color=tc, fontsize=11, fontweight="bold", fontfamily="monospace",
            )

    ax.set_xlim(0, x0 + n * cell + 0.4)
    ax.set_ylim(-2.3, y0 + n * cell + 0.6)
    ax.set_aspect("equal")
    ax.axis("off")
    return x0, y0, cell


for k, frame in FRAMES.items():
    fig = plt.figure(figsize=(12.5, 5.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.12)
    ax_g = fig.add_subplot(gs[0, 0])
    ax_m = fig.add_subplot(gs[0, 1])

    fig.suptitle(
        "A$^k$[i][j]  =  number of length-$k$ walks from $i$ to $j$",
        fontsize=14, fontweight="bold", color=FG, y=1.02,
    )

    draw_graph(ax_g, frame["walks"])
    x0, y0, cell = draw_matrix(
        ax_m, frame["matrix"], frame["title"], highlight=frame["cell"],
    )

    hr, hc = frame["cell"]
    n_walks = int(frame["matrix"][hr, hc])
    power_mark = {1: "", 2: "²", 3: "³"}[k]
    centre_x = x0 + frame["matrix"].shape[0] * cell / 2

    ax_m.text(
        centre_x, -0.15,
        f"A{power_mark}[{hr}][{hc}]  =  {n_walks}",
        ha="center", va="top",
        fontsize=12, color=CELL["warn"], fontfamily="monospace",
        fontweight="bold",
    )
    ax_m.text(
        centre_x, -0.55, frame["header"],
        ha="center", va="top",
        fontsize=10, color=FG, fontstyle="italic",
    )
    for i, walk_str in enumerate(frame["walk_strs"]):
        ax_m.text(
            centre_x, -0.95 - i * 0.32, walk_str,
            ha="center", va="top",
            fontsize=11, color=WALK_COLORS[i % len(WALK_COLORS)],
            fontfamily="monospace", fontweight="bold",
        )

    path = f"matrix_power_{k}.png"
    plt.savefig(path, dpi=200, transparent=True,
                bbox_inches="tight", edgecolor="none")
    plt.close(fig)
    print(f"Saved {path}")
