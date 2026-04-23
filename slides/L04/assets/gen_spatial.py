"""Spatial data-structure diagrams.

Emits:
  - spatial_grid.png   uniform grid over scattered points, with one query
                       cell + 8 neighbour cells highlighted.
  - kd_tree.png        2D point cloud with alternating axis-aligned splits,
                       plus the matching binary-tree schematic next to it.
  - bvh.png            bounding-volume hierarchy: triangles wrapped in
                       nested AABBs, with a ray traversal highlighted.
  - rtree.png          overlapping minimum bounding rectangles with
                       children grouped into parent MBRs.

All figures share the _viz_style palette so they read as part of the same
deck as the other diagrams.
"""

from __future__ import annotations

import random

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, FG, NEGATIVE, PTR,
    draw_annotation, save, setup_mpl,
)

setup_mpl()

# Deterministic: we want the figures reproducible.
rng = random.Random(42)


def _mk_ax(fig_w: float, fig_h: float, title: str):
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_title(
        title, fontsize=12, fontweight="bold",
        color=FG, loc="left", pad=10,
    )
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


# =========================================================================
# Figure 1: uniform grid
# =========================================================================
GRID_N = 8            # 8 x 8 cells
CELL_SIZE = 1.0
POINT_COUNT = 90

fig, ax = _mk_ax(
    10.0, 5.0,
    "Uniform grid — one array of bucket lists, O(1) expected near-neighbour query",
)

# Cell outlines.
for i in range(GRID_N + 1):
    ax.plot([0, GRID_N * CELL_SIZE], [i * CELL_SIZE, i * CELL_SIZE],
            color=FG, lw=0.4, alpha=0.4)
    ax.plot([i * CELL_SIZE, i * CELL_SIZE], [0, GRID_N * CELL_SIZE],
            color=FG, lw=0.4, alpha=0.4)

# Scatter points.
points = []
for _ in range(POINT_COUNT):
    px = rng.uniform(0.1, GRID_N * CELL_SIZE - 0.1)
    py = rng.uniform(0.1, GRID_N * CELL_SIZE - 0.1)
    points.append((px, py))
    ax.plot(px, py, "o", markersize=4, color=CELL["data"],
            markeredgecolor=FG, markeredgewidth=0.4)

# Query point + its cell + 8 neighbours.
q = (4.55, 3.2)
qcx, qcy = int(q[0]), int(q[1])
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        cx = qcx + dx
        cy = qcy + dy
        if not (0 <= cx < GRID_N and 0 <= cy < GRID_N):
            continue
        color = CELL["hot"] if (dx, dy) == (0, 0) else CELL["warn"]
        alpha = 0.35 if (dx, dy) == (0, 0) else 0.18
        rect = mpatches.Rectangle(
            (cx, cy), CELL_SIZE, CELL_SIZE,
            facecolor=color, alpha=alpha, edgecolor=color, lw=1.1,
        )
        ax.add_patch(rect)

ax.plot(*q, "*", markersize=16, color=CELL["hot"],
        markeredgecolor="white", markeredgewidth=0.8, zorder=6)

draw_annotation(
    ax, GRID_N * CELL_SIZE + 0.3, 5.0,
    "query cell + 8 neighbours\n= all the work",
    color=ACCENT, ha="left",
)
draw_annotation(
    ax, GRID_N * CELL_SIZE + 0.3, 2.0,
    "non-uniform clusters\n→ one cell explodes",
    color=NEGATIVE, ha="left",
)

ax.set_xlim(-0.3, GRID_N * CELL_SIZE + 4.5)
ax.set_ylim(-0.3, GRID_N * CELL_SIZE + 0.5)

plt.tight_layout()
save(fig, "spatial_grid.png")


# =========================================================================
# Figure 2: kd-tree over a 2D point cloud
# =========================================================================
# Hand-picked 12 points so the splits land cleanly and the tree stays
# shallow enough to render next to the plane.
KD_POINTS = [
    (1.0, 6.0), (2.0, 2.0), (2.5, 8.5),
    (3.0, 4.0), (4.5, 7.5), (5.0, 1.5),
    (5.5, 5.5), (6.0, 3.0), (7.0, 8.0),
    (7.5, 5.0), (8.5, 2.5), (9.0, 7.0),
]
BOUNDS = (0.0, 10.0, 0.0, 10.0)  # xmin, xmax, ymin, ymax

# Axis-aligned splits: alternate x, y, x (depth 0, 1, 2).
# depth 0: split by x at median x.
pts_sorted_x = sorted(KD_POINTS, key=lambda p: p[0])
median_x = pts_sorted_x[len(pts_sorted_x) // 2][0]
# left subtree: depth 1 split by y at median y of left points.
left_pts = [p for p in KD_POINTS if p[0] < median_x]
right_pts = [p for p in KD_POINTS if p[0] >= median_x]
median_y_left = sorted(left_pts, key=lambda p: p[1])[len(left_pts) // 2][1]
median_y_right = sorted(right_pts, key=lambda p: p[1])[len(right_pts) // 2][1]

fig, (ax_plane, ax_tree) = plt.subplots(
    1, 2, figsize=(14.0, 5.2),
    gridspec_kw={"width_ratios": [1.1, 1.0]},
)
for a in (ax_plane, ax_tree):
    a.set_aspect("equal")
    a.axis("off")

ax_plane.set_title(
    "kd-tree — alternating axis-aligned splits at each level",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

# Plane frame.
xmin, xmax, ymin, ymax = BOUNDS
ax_plane.add_patch(mpatches.Rectangle(
    (xmin, ymin), xmax - xmin, ymax - ymin,
    facecolor="none", edgecolor=FG, lw=0.8,
))

# Depth 0 (vertical, full height).
ax_plane.plot([median_x, median_x], [ymin, ymax],
              color=CELL["warn"], lw=2.0)
ax_plane.text(median_x + 0.1, ymax - 0.3, "x-split",
              color=CELL["warn"], fontsize=9, fontstyle="italic")

# Depth 1 (horizontal, on each side).
ax_plane.plot([xmin, median_x], [median_y_left, median_y_left],
              color=CELL["ok"], lw=1.6)
ax_plane.plot([median_x, xmax], [median_y_right, median_y_right],
              color=CELL["ok"], lw=1.6)

# Points.
for p in KD_POINTS:
    ax_plane.plot(*p, "o", markersize=6, color=CELL["data"],
                  markeredgecolor=FG, markeredgewidth=0.5)

ax_plane.set_xlim(xmin - 0.3, xmax + 0.3)
ax_plane.set_ylim(ymin - 0.3, ymax + 0.3)

# Tree schematic on the right.
def tree_node(ax, x, y, label, color=CELL["data"], rad=0.45):
    circ = mpatches.Circle((x, y), rad, facecolor=color,
                           edgecolor=FG, lw=0.6)
    ax.add_patch(circ)
    ax.text(x, y, label, ha="center", va="center",
            color="white", fontsize=9, fontweight="bold", fontfamily="monospace")


def tree_edge(ax, a, b):
    ax.plot([a[0], b[0]], [a[1], b[1]], color=FG, lw=0.8, alpha=0.6)


ax_tree.set_title(
    "      ...and the matching binary tree",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

# Positions.
root = (5.0, 4.5)
L = (2.2, 3.0)
R = (7.8, 3.0)
LL, LR = (0.9, 1.5), (3.5, 1.5)
RL, RR = (6.5, 1.5), (9.1, 1.5)

for a, b in [(root, L), (root, R), (L, LL), (L, LR), (R, RL), (R, RR)]:
    tree_edge(ax_tree, a, b)

tree_node(ax_tree, *root, "x", CELL["warn"])
tree_node(ax_tree, *L,    "y", CELL["ok"])
tree_node(ax_tree, *R,    "y", CELL["ok"])
for pos in (LL, LR, RL, RR):
    tree_node(ax_tree, *pos, "·", CELL["data"], rad=0.35)

ax_tree.text(root[0], root[1] + 0.8, "depth 0 — split x",
             ha="center", va="bottom", fontsize=8,
             color=CELL["warn"], fontstyle="italic")
ax_tree.text(L[0] - 1.3, L[1], "depth 1 — split y",
             ha="right", va="center", fontsize=8,
             color=CELL["ok"], fontstyle="italic")
ax_tree.text(RR[0] + 0.7, RR[1], "depth 2 — leaves",
             ha="left", va="center", fontsize=8,
             color=FG, fontstyle="italic")

ax_tree.set_xlim(-1.2, 11.5)
ax_tree.set_ylim(0.2, 6.0)

plt.tight_layout()
save(fig, "kd_tree.png")


# =========================================================================
# Figure 3: BVH
# =========================================================================
fig, ax = _mk_ax(
    13.0, 5.5,
    "BVH — axis-aligned bounding boxes; a ray descends only into boxes it hits",
)

# Three leaf clusters (triangles) with tight AABBs, wrapped by two
# intermediate nodes and a root box.
LEAF_BOXES = [
    ((0.6, 1.0), (2.6, 2.5), CELL["data"]),   # cluster A
    ((3.4, 0.7), (5.6, 2.3), CELL["data"]),   # cluster B
    ((7.2, 2.0), (9.4, 3.6), CELL["data"]),   # cluster C
    ((9.8, 0.6), (11.8, 2.4), CELL["data"]),  # cluster D
]

TRI_PTS = [
    # Cluster A (2 triangles)
    [(1.0, 1.3), (1.9, 1.2), (1.3, 2.2)],
    [(1.8, 1.8), (2.4, 1.4), (2.2, 2.3)],
    # Cluster B (2 triangles)
    [(3.7, 1.0), (4.5, 1.2), (4.0, 2.0)],
    [(4.6, 1.4), (5.3, 1.2), (5.2, 2.1)],
    # Cluster C (2 triangles)
    [(7.5, 2.4), (8.3, 2.3), (7.8, 3.3)],
    [(8.4, 2.6), (9.2, 2.5), (9.0, 3.4)],
    # Cluster D (2 triangles)
    [(10.1, 0.9), (10.9, 1.0), (10.4, 2.0)],
    [(11.0, 1.3), (11.6, 1.2), (11.4, 2.2)],
]

# Draw triangles.
for tri in TRI_PTS:
    poly = mpatches.Polygon(tri, closed=True,
                            facecolor=CELL["data"], edgecolor="white",
                            alpha=0.85, lw=0.6)
    ax.add_patch(poly)

# Leaf AABBs.
for (x0, y0), (x1, y1), color in LEAF_BOXES:
    rect = mpatches.Rectangle(
        (x0, y0), x1 - x0, y1 - y0,
        facecolor="none", edgecolor=CELL["ok"], lw=1.3, linestyle=(0, (3, 2)),
    )
    ax.add_patch(rect)

# Intermediate node boxes (group A+B, group C+D).
INTER = [
    ((0.3, 0.4), (5.9, 2.8), "node L"),
    ((6.9, 0.3), (12.1, 3.9), "node R"),
]
for (x0, y0), (x1, y1), label in INTER:
    rect = mpatches.Rectangle(
        (x0, y0), x1 - x0, y1 - y0,
        facecolor="none", edgecolor=CELL["warn"], lw=1.5, linestyle=(0, (5, 2)),
    )
    ax.add_patch(rect)
    ax.text(x0 + 0.1, y1 + 0.05, label,
            color=CELL["warn"], fontsize=8, fontstyle="italic", fontweight="bold")

# Root box.
root = ((0.1, 0.2), (12.3, 4.1))
ax.add_patch(mpatches.Rectangle(
    root[0], root[1][0] - root[0][0], root[1][1] - root[0][1],
    facecolor="none", edgecolor=CELL["hot"], lw=1.8, linestyle="-",
))
ax.text(root[0][0] + 0.1, root[1][1] + 0.15, "root",
        color=CELL["hot"], fontsize=9, fontweight="bold")

# A ray that hits root, hits node R, hits cluster D, misses cluster C.
ray_start = (-0.6, 4.9)
ray_end = (12.5, 0.4)
ax.annotate(
    "", xy=ray_end, xytext=ray_start,
    arrowprops=dict(arrowstyle="-|>", color=CELL["cache"], lw=2.2),
)
ax.text(-0.5, 5.2, "ray",
        color=CELL["cache"], fontsize=10, fontweight="bold", fontstyle="italic")

# Legend boxes explaining line styles.
ax.plot([0.1, 0.6], [5.1, 5.1], color=CELL["hot"], lw=1.8)
ax.text(0.7, 5.1, "root", ha="left", va="center",
        color=CELL["hot"], fontsize=8)
ax.plot([1.8, 2.3], [5.1, 5.1], color=CELL["warn"], lw=1.5, linestyle=(0, (5, 2)))
ax.text(2.4, 5.1, "intermediate", ha="left", va="center",
        color=CELL["warn"], fontsize=8)
ax.plot([4.3, 4.8], [5.1, 5.1], color=CELL["ok"], lw=1.3, linestyle=(0, (3, 2)))
ax.text(4.9, 5.1, "leaf AABB", ha="left", va="center",
        color=CELL["ok"], fontsize=8)

draw_annotation(
    ax, 12.5, 3.0,
    "prune subtrees\nwhose box the ray\ndoes not intersect",
    color=ACCENT, ha="right",
)

ax.set_xlim(-0.8, 13.2)
ax.set_ylim(-0.2, 5.6)

plt.tight_layout()
save(fig, "bvh.png")


# =========================================================================
# Figure 4: R-tree (overlapping MBRs, grouped into parent MBRs)
# =========================================================================
fig, ax = _mk_ax(
    10.0, 5.5,
    "R-tree — each node is the minimum bounding rectangle of its children",
)

# Leaf rectangles (real data: road bounding boxes / building footprints).
LEAF_RECTS = [
    # Group 1
    ((0.5, 3.4), (1.9, 4.3), "a"),
    ((1.1, 2.5), (2.4, 3.5), "b"),
    ((0.3, 1.7), (1.5, 2.6), "c"),
    # Group 2 (overlaps a little with group 1 — R-tree allows this)
    ((2.6, 1.8), (4.1, 3.0), "d"),
    ((3.4, 2.8), (4.8, 4.1), "e"),
    # Group 3
    ((5.7, 2.2), (7.0, 3.4), "f"),
    ((6.5, 3.2), (7.9, 4.2), "g"),
    ((6.3, 1.0), (7.6, 2.1), "h"),
]

# Draw leaves.
for (x0, y0), (x1, y1), label in LEAF_RECTS:
    rect = mpatches.Rectangle(
        (x0, y0), x1 - x0, y1 - y0,
        facecolor=CELL["data"], alpha=0.25,
        edgecolor=CELL["data"], lw=1.2,
    )
    ax.add_patch(rect)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, label,
            ha="center", va="center",
            color="white", fontsize=9, fontweight="bold",
            fontfamily="monospace")

# Parent MBRs (groups).
GROUPS = [
    ((0.2, 1.5), (2.5, 4.5), "N1"),
    ((2.4, 1.6), (5.0, 4.3), "N2"),
    ((5.5, 0.8), (8.1, 4.4), "N3"),
]
for (x0, y0), (x1, y1), label in GROUPS:
    rect = mpatches.Rectangle(
        (x0, y0), x1 - x0, y1 - y0,
        facecolor="none", edgecolor=CELL["warn"], lw=1.6,
        linestyle=(0, (5, 2)),
    )
    ax.add_patch(rect)
    ax.text(x0 + 0.05, y1 - 0.05, label,
            ha="left", va="top",
            color=CELL["warn"], fontsize=10, fontweight="bold")

# Root MBR.
ROOT = ((0.1, 0.7), (8.2, 4.6))
ax.add_patch(mpatches.Rectangle(
    ROOT[0], ROOT[1][0] - ROOT[0][0], ROOT[1][1] - ROOT[0][1],
    facecolor="none", edgecolor=CELL["hot"], lw=2.0,
))
ax.text(ROOT[0][0] + 0.05, ROOT[1][1] + 0.1, "root",
        color=CELL["hot"], fontsize=10, fontweight="bold")

# A query rectangle that intersects N2 and N3 (but not N1).
QUERY = ((3.2, 2.2), (6.8, 3.8))
ax.add_patch(mpatches.Rectangle(
    QUERY[0], QUERY[1][0] - QUERY[0][0], QUERY[1][1] - QUERY[0][1],
    facecolor=CELL["cache"], alpha=0.18,
    edgecolor=CELL["cache"], lw=1.6, linestyle=(0, (2, 2)),
))
ax.text(QUERY[0][0] + 0.05, QUERY[0][1] - 0.15, "query",
        color=CELL["cache"], fontsize=9, fontstyle="italic", fontweight="bold")

draw_annotation(
    ax, 9.3, 4.2,
    "sibling MBRs\nmay overlap",
    color=NEGATIVE, ha="right",
)
draw_annotation(
    ax, 9.3, 1.2,
    "nodes sized for\none disk page",
    color=ACCENT, ha="right",
)

ax.set_xlim(-0.3, 10.2)
ax.set_ylim(0.0, 5.3)

plt.tight_layout()
save(fig, "rtree.png")
