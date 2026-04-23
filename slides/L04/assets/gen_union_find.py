"""Union-Find diagrams.

Emits:
  - union_find_forest.png       (naive parent-pointer forest with a degenerate
                                 chain next to a balanced tree; parent array
                                 below shows the flat storage.)
  - union_find_compression.png  (before/after path compression — tall chain
                                 collapses into a star after one find.)

Both figures use the shared _viz_style palette so they read as part of the
same deck as the linear-structures and hash-map diagrams.
"""

from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, CELL_GAP, CELL_H, CELL_W, FG, NEGATIVE, PTR,
    draw_annotation, draw_cell, draw_pointer, save, setup_mpl,
)

setup_mpl()


def draw_node(ax, x: float, y: float, label: str, *, root: bool = False) -> None:
    """A circular tree node. Roots get the accent colour."""
    color = CELL["ok"] if root else CELL["pointer"]
    circle = mpatches.Circle(
        (x, y), 0.26, facecolor=color, edgecolor=FG, linewidth=0.8,
    )
    ax.add_patch(circle)
    ax.text(
        x, y, label, ha="center", va="center",
        color="white", fontsize=10, fontweight="bold", fontfamily="monospace",
    )


def draw_parent_edge(ax, child: tuple[float, float],
                     parent: tuple[float, float], *,
                     color: str = PTR) -> None:
    """Arrow from child up to parent. Shrinks so it touches the node rim."""
    ax.annotate(
        "", xy=parent, xytext=child,
        arrowprops=dict(
            arrowstyle="-|>", color=color, lw=1.2,
            shrinkA=12, shrinkB=12,
        ),
    )


def draw_parent_array(ax, y: float, values: list[int], *,
                      highlight: set[int] | None = None,
                      label: str = "parent →") -> None:
    """Draw the flat parent array below a tree picture."""
    highlight = highlight or set()
    ax.text(
        0.3, y + CELL_H / 2, label,
        ha="right", va="center", color=CELL["index"],
        fontfamily="monospace", fontweight="bold", fontsize=10,
    )
    x0 = 0.5
    for i, p in enumerate(values):
        color = CELL["warn"] if i in highlight else CELL["data"]
        draw_cell(ax, x0 + i * CELL_W, y, str(p), color)
        ax.text(
            x0 + i * CELL_W + (CELL_W - CELL_GAP) / 2, y - 0.22,
            f"[{i}]", ha="center", va="top",
            fontsize=7, color=FG, fontfamily="monospace",
        )


# =========================================================================
# Figure 1: forest — balanced tree + degenerate chain
# =========================================================================
# Elements 0..7. Two disjoint sets:
#   Set A (balanced): root=0, children 1, 2; grandchildren 3 (under 1), 4 (under 2)
#   Set B (chain):    root=5, 6 -> 5, 7 -> 6
BALANCED_POS = {
    0: (2.0, 3.4),
    1: (1.2, 2.4),
    2: (2.8, 2.4),
    3: (0.6, 1.4),
    4: (2.4, 1.4),
}
BALANCED_PARENT = {0: 0, 1: 0, 2: 0, 3: 1, 4: 2}

CHAIN_POS = {
    5: (5.4, 3.4),
    6: (5.4, 2.4),
    7: (5.4, 1.4),
    # extend chain a little to make the point
    8: (5.4, 0.4),
}
CHAIN_PARENT = {5: 5, 6: 5, 7: 6, 8: 7}

N = 9
PARENT_ARRAY_Y = -0.9

fig, ax = plt.subplots(figsize=(13.0, 5.0))
ax.set_title(
    "Union-Find as a forest — one integer per element, pointing at its parent",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

# Balanced tree
for i, (x, y) in BALANCED_POS.items():
    draw_node(ax, x, y, str(i), root=(BALANCED_PARENT[i] == i))
for i, p in BALANCED_PARENT.items():
    if p == i:
        continue
    draw_parent_edge(ax, BALANCED_POS[i], BALANCED_POS[p])
ax.text(
    2.0, 3.95, "balanced", ha="center", va="bottom",
    fontsize=9, color=ACCENT, fontstyle="italic", fontweight="bold",
)

# Chain
for i, (x, y) in CHAIN_POS.items():
    draw_node(ax, x, y, str(i), root=(CHAIN_PARENT[i] == i))
for i, p in CHAIN_PARENT.items():
    if p == i:
        continue
    draw_parent_edge(ax, CHAIN_POS[i], CHAIN_POS[p])
ax.text(
    5.4, 3.95, "degenerate chain", ha="center", va="bottom",
    fontsize=9, color=NEGATIVE, fontstyle="italic", fontweight="bold",
)

# Annotation pointing at the chain
draw_annotation(
    ax, 8.0, 2.0,
    "find(8) walks\nthe whole chain",
    color=NEGATIVE, ha="left",
)

# Parent array
full_parent = [0] * N
for i, p in BALANCED_PARENT.items():
    full_parent[i] = p
for i, p in CHAIN_PARENT.items():
    full_parent[i] = p
draw_parent_array(ax, PARENT_ARRAY_Y, full_parent)

ax.set_xlim(-0.3, 13.0)
ax.set_ylim(PARENT_ARRAY_Y - 0.6, 4.4)
ax.axis("off")

plt.tight_layout()
save(fig, "union_find_forest.png")


# =========================================================================
# Figure 2: path compression — before / after
# =========================================================================
# A chain 4 -> 3 -> 2 -> 1 -> 0 (0 is root). After find(4), path halving
# points each node directly at the root: 1,2,3,4 -> 0.
BEFORE_POS = {
    0: (1.6, 3.6),
    1: (1.6, 2.6),
    2: (1.6, 1.6),
    3: (1.6, 0.6),
    4: (1.6, -0.4),
}
BEFORE_PARENT = {0: 0, 1: 0, 2: 1, 3: 2, 4: 3}

AFTER_POS = {
    0: (8.6, 2.8),
    1: (7.0, 1.2),
    2: (8.0, 1.2),
    3: (9.2, 1.2),
    4: (10.4, 1.2),
}
AFTER_PARENT = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

fig, ax = plt.subplots(figsize=(13.0, 5.6))
ax.set_title(
    "Path compression — one find flattens the tree for every ancestor visited",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

# -- Before --
for i, (x, y) in BEFORE_POS.items():
    draw_node(ax, x, y, str(i), root=(BEFORE_PARENT[i] == i))
for i, p in BEFORE_PARENT.items():
    if p == i:
        continue
    draw_parent_edge(ax, BEFORE_POS[i], BEFORE_POS[p])
ax.text(
    1.6, 4.3, "before find(4)",
    ha="center", va="bottom",
    fontsize=10, color=FG, fontweight="bold",
)

# Big arrow between panels
ax.annotate(
    "", xy=(6.0, 1.6), xytext=(3.0, 1.6),
    arrowprops=dict(arrowstyle="-|>", color=CELL["warn"], lw=2.2),
)
ax.text(
    4.5, 2.0, "find(4)\n+ path compression",
    ha="center", va="bottom",
    fontsize=10, color=CELL["warn"], fontstyle="italic", fontweight="bold",
)

# -- After --
for i, (x, y) in AFTER_POS.items():
    draw_node(ax, x, y, str(i), root=(AFTER_PARENT[i] == i))
for i, p in AFTER_PARENT.items():
    if p == i:
        continue
    draw_parent_edge(ax, AFTER_POS[i], AFTER_POS[p], color=ACCENT)
ax.text(
    8.6, 4.3, "after find(4)",
    ha="center", va="bottom",
    fontsize=10, color=FG, fontweight="bold",
)

draw_annotation(
    ax, 11.8, 1.2,
    "every node on the path\nnow one hop from root",
    color=ACCENT, ha="right",
)

# Parent arrays below the two panels.
draw_parent_array(
    ax, -1.4, [0, 0, 1, 2, 3], highlight={1, 2, 3, 4},
    label="parent →",
)
ax.text(
    0.5 + 2.5 * CELL_W, -2.1, "before",
    ha="center", va="top", fontsize=9, color=FG, fontstyle="italic",
)

# Shift the 'after' array further right so the two line up visually under
# their respective trees.
AFTER_ARR_X0 = 7.2
ax.text(
    AFTER_ARR_X0 - 0.2, -1.4 + CELL_H / 2, "parent →",
    ha="right", va="center", color=CELL["index"],
    fontfamily="monospace", fontweight="bold", fontsize=10,
)
after_parent_arr = [0, 0, 0, 0, 0]
for i, p in enumerate(after_parent_arr):
    color = ACCENT if i != 0 else CELL["data"]
    draw_cell(ax, AFTER_ARR_X0 + i * CELL_W, -1.4, str(p), color)
    ax.text(
        AFTER_ARR_X0 + i * CELL_W + (CELL_W - CELL_GAP) / 2, -1.62,
        f"[{i}]", ha="center", va="top",
        fontsize=7, color=FG, fontfamily="monospace",
    )
ax.text(
    AFTER_ARR_X0 + 2.5 * CELL_W, -2.1, "after",
    ha="center", va="top", fontsize=9, color=FG, fontstyle="italic",
)

ax.set_xlim(-0.3, 13.0)
ax.set_ylim(-2.4, 4.8)
ax.axis("off")

plt.tight_layout()
save(fig, "union_find_compression.png")
