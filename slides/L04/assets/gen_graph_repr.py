"""Graph representations: edge list and adjacency matrix.

Emits two PNGs that share the five-vertex example graph:

  - edge_list.png     flat array of (u, v, weight) triples
  - adj_matrix.png    V×V matrix, one bit per (u, v) pair

The adjacency-list and CSR figures for the L04 deck now come from the
T01 generator (`gen_adjlist_vs_csr_memory.py`, producing
`adjlist_memory.png` and `csr_memory.png`). That version is visually
cleaner and already uses the shared `_viz_style` palette, so both decks
stay in one visual language.
"""

from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, CELL_GAP, CELL_H, CELL_W, FG,
    draw_annotation, draw_cell, save, setup_mpl,
)

setup_mpl()

# Shared example graph (directed). 5 vertices, 10 directed edges.
ADJ = {
    0: [1, 2],
    1: [0, 3],
    2: [0, 3, 4],
    3: [1, 2],
    4: [2],
}
V = 5
# Edge list (with a toy weight) for the edge-list figure.
EDGES = [(u, v, 1 + (u + v) % 5) for u in range(V) for v in ADJ[u]]
# Edge set for the adjacency-matrix figure.
EDGE_SET = {(u, v) for u, nbrs in ADJ.items() for v in nbrs}


# =========================================================================
# Figure 1: edge list
# =========================================================================
FIG_W = 13.0
fig, ax = plt.subplots(figsize=(FIG_W, 2.8))
ax.set_title(
    "Edge list — one allocation, sort by weight or by source, stream through",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

# Render the first 8 edges, then a "..." trailing cell.
shown = EDGES[:8]
EL_X0 = 1.3
EL_Y = 0.6
TRIPLE_W = CELL_W * 2.4   # three sub-cells per edge
U_W = CELL_W * 0.75
V_W = CELL_W * 0.75
W_W = CELL_W * 0.75

for i, (u, v, w) in enumerate(shown):
    x = EL_X0 + i * TRIPLE_W
    draw_cell(ax, x, EL_Y, u, CELL["pointer"], w=U_W)
    draw_cell(ax, x + U_W, EL_Y, v, CELL["pointer"], w=V_W)
    draw_cell(ax, x + U_W + V_W, EL_Y, w, CELL["index"], w=W_W)
    # Subscript label
    ax.text(
        x + TRIPLE_W / 2 - CELL_GAP / 2, EL_Y - 0.24,
        f"e{i}", ha="center", va="top",
        fontsize=7, color=FG, fontfamily="monospace",
    )

# Trailing "..." marker
tail_x = EL_X0 + len(shown) * TRIPLE_W + 0.1
ax.text(
    tail_x, EL_Y + CELL_H / 2, "...",
    ha="left", va="center", color=FG, fontsize=16, fontfamily="monospace",
)

# Legend above one triple explaining the three sub-cells.
legend_x = EL_X0
legend_y = EL_Y + CELL_H + 0.35
for label, sub_x, color in [
    ("u",      legend_x + U_W / 2 - CELL_GAP / 2, CELL["pointer"]),
    ("v",      legend_x + U_W + V_W / 2 - CELL_GAP / 2, CELL["pointer"]),
    ("weight", legend_x + U_W + V_W + W_W / 2 - CELL_GAP / 2, CELL["index"]),
]:
    ax.text(
        sub_x, legend_y, label,
        ha="center", va="bottom",
        fontsize=8, color=color, fontstyle="italic", fontweight="bold",
    )

draw_annotation(
    ax, FIG_W - 0.3, EL_Y + CELL_H / 2,
    "ideal for Kruskal\nand bulk loads",
    color=ACCENT, ha="right",
)

ax.set_xlim(-0.3, FIG_W + 0.3)
ax.set_ylim(-0.5, 1.7)
ax.axis("off")

plt.tight_layout()
save(fig, "edge_list.png")


# =========================================================================
# Figure 2: adjacency matrix
# =========================================================================
FIG_W = 6.0
fig, ax = plt.subplots(figsize=(FIG_W, 5.2))
ax.set_title(
    "Adjacency matrix — V×V, one bit per pair",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

M_CELL = 0.7
M_X0 = 1.1
M_Y0 = 0.6
# Row index 0 at the top, so draw row r at y = M_Y0 + (V-1-r) * M_CELL.

# Column headers (v) across the top.
for c in range(V):
    ax.text(
        M_X0 + c * M_CELL + M_CELL / 2, M_Y0 + V * M_CELL + 0.15,
        str(c), ha="center", va="bottom",
        fontsize=10, color=CELL["index"],
        fontfamily="monospace", fontweight="bold",
    )
ax.text(
    M_X0 + V * M_CELL / 2, M_Y0 + V * M_CELL + 0.55,
    "destination v", ha="center", va="bottom",
    fontsize=9, color=CELL["index"], fontstyle="italic",
)

# Row headers (u) down the left.
for r in range(V):
    y = M_Y0 + (V - 1 - r) * M_CELL + M_CELL / 2
    ax.text(
        M_X0 - 0.15, y, str(r), ha="right", va="center",
        fontsize=10, color=CELL["index"],
        fontfamily="monospace", fontweight="bold",
    )
ax.text(
    M_X0 - 0.6, M_Y0 + V * M_CELL / 2,
    "source u", ha="center", va="center",
    fontsize=9, color=CELL["index"], fontstyle="italic",
    rotation=90,
)

# Matrix cells.
for r in range(V):
    for c in range(V):
        x = M_X0 + c * M_CELL
        y = M_Y0 + (V - 1 - r) * M_CELL
        is_edge = (r, c) in EDGE_SET
        color = CELL["data"] if is_edge else "#1a1a2e"
        label = "1" if is_edge else "·"
        tc = "white" if is_edge else "#555"
        rect = mpatches.FancyBboxPatch(
            (x + 0.02, y + 0.02), M_CELL - 0.04, M_CELL - 0.04,
            boxstyle="round,pad=0.02",
            facecolor=color, edgecolor=FG, linewidth=0.5,
        )
        ax.add_patch(rect)
        ax.text(
            x + M_CELL / 2, y + M_CELL / 2, label,
            ha="center", va="center",
            color=tc, fontsize=10, fontweight="bold", fontfamily="monospace",
        )

# Density annotation.
n_edges = len(EDGE_SET)
draw_annotation(
    ax, M_X0 + V * M_CELL + 0.3, M_Y0 + V * M_CELL / 2,
    f"{n_edges} of {V*V} cells set\n= V² memory always",
    color=ACCENT, ha="left",
)

ax.set_xlim(0, FIG_W + 0.3)
ax.set_ylim(0, M_Y0 + V * M_CELL + 1.2)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
save(fig, "adj_matrix.png")
