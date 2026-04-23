"""kd-tree walkthrough — one PNG per narrated step.

What this file contains
-----------------------
Emits kd_step_00..kd_step_04.png. Each frame shares a 2-panel layout:
point plane on the left, growing binary tree on the right. Steps:

  step_00  points only; empty tree placeholder
  step_01  depth-0 x-split on plane; tree = root (x)
  step_02  left half gets its y-split; tree adds the left y-node
  step_03  right half gets its y-split; tree adds the right y-node
  step_04  depth-2 x-splits across all four strips; tree gains leaves

Tree edges carry "≤" and ">" labels so the recursion reads as a decision
procedure, not just a picture.

Why it exists
-------------
The static kd_tree.png collapses three levels of recursion into one
frame. Per-frame reveals let the speaker name each level and point at
the exact split being introduced. It also replaces the unlabelled tree
edges with the decision semantics that actually define the structure.

How to use
----------
Run from the assets/ directory:

    python gen_kdtree_animation.py

When to change
--------------
KD_POINTS is hand-picked so the median splits land cleanly at depth
0..2 with a balanced tree. If the point set changes, verify each
depth still produces a clean median along the active axis.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import CELL, FG, save, setup_mpl

setup_mpl()

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PREFIX = os.path.join(OUT_DIR, "kd_step_")

# 12 hand-picked points — same set as the static kd_tree.png.
KD_POINTS = [
    (1.0, 6.0), (2.0, 2.0), (2.5, 8.5),
    (3.0, 4.0), (4.5, 7.5), (5.0, 1.5),
    (5.5, 5.5), (6.0, 3.0), (7.0, 8.0),
    (7.5, 5.0), (8.5, 2.5), (9.0, 7.0),
]
BOUNDS = (0.0, 10.0, 0.0, 10.0)  # xmin, xmax, ymin, ymax


def _median_split(points, axis):
    """Median split along `axis` (0=x, 1=y). Returns (value, left, right)."""
    pts_sorted = sorted(points, key=lambda p: p[axis])
    med = pts_sorted[len(pts_sorted) // 2][axis]
    left = [p for p in points if p[axis] < med]
    right = [p for p in points if p[axis] >= med]
    return med, left, right


# --- Recursive split plan -------------------------------------------------
# depth 0 (x): one median for the whole set.
MED_X0, LEFT0, RIGHT0 = _median_split(KD_POINTS, 0)
# depth 1 (y): one median for each side.
MED_Y_L, LL_y, LR_y = _median_split(LEFT0, 1)
MED_Y_R, RL_y, RR_y = _median_split(RIGHT0, 1)
# depth 2 (x): one median for each of the four subsets.
MED_X_LL, _, _ = _median_split(LL_y, 0)
MED_X_LR, _, _ = _median_split(LR_y, 0)
MED_X_RL, _, _ = _median_split(RL_y, 0)
MED_X_RR, _, _ = _median_split(RR_y, 0)


# --- Tree layout (right panel) -------------------------------------------
ROOT = (5.0, 5.0)
L1_L, L1_R = (2.0, 3.5), (8.0, 3.5)
L2 = {
    "LL": (0.7, 2.0),
    "LR": (3.3, 2.0),
    "RL": (6.7, 2.0),
    "RR": (9.3, 2.0),
}
LEAVES = {
    "LL": [(0.15, 0.5), (1.25, 0.5)],
    "LR": [(2.75, 0.5), (3.85, 0.5)],
    "RL": [(6.15, 0.5), (7.25, 0.5)],
    "RR": [(8.75, 0.5), (9.85, 0.5)],
}

COLOR_X = CELL["warn"]
COLOR_Y = CELL["ok"]
COLOR_LEAF = CELL["data"]


# --- Drawing primitives ---------------------------------------------------
def _new_fig():
    fig, (ax_plane, ax_tree) = plt.subplots(
        1, 2, figsize=(14.0, 5.6),
        gridspec_kw={"width_ratios": [1.05, 1.1]},
    )
    for a in (ax_plane, ax_tree):
        a.set_aspect("equal")
        a.axis("off")

    xmin, xmax, ymin, ymax = BOUNDS
    ax_plane.add_patch(mpatches.Rectangle(
        (xmin, ymin), xmax - xmin, ymax - ymin,
        facecolor="none", edgecolor=FG, lw=0.8,
    ))
    ax_plane.set_xlim(xmin - 0.3, xmax + 0.3)
    ax_plane.set_ylim(ymin - 0.3, ymax + 0.3)

    ax_tree.set_xlim(-1.0, 11.0)
    ax_tree.set_ylim(-0.2, 6.2)
    return fig, ax_plane, ax_tree


def _draw_points(ax):
    for p in KD_POINTS:
        ax.plot(*p, "o", markersize=6, color=COLOR_LEAF,
                markeredgecolor=FG, markeredgewidth=0.5)


def _vline(ax, x, y0, y1, color, lw=2.0):
    ax.plot([x, x], [y0, y1], color=color, lw=lw)


def _hline(ax, x0, x1, y, color, lw=1.6):
    ax.plot([x0, x1], [y, y], color=color, lw=lw)


def _tree_node(ax, xy, label, color, rad=0.42):
    circ = mpatches.Circle(xy, rad, facecolor=color,
                           edgecolor=FG, lw=0.6, zorder=3)
    ax.add_patch(circ)
    ax.text(xy[0], xy[1], label, ha="center", va="center",
            color="white", fontsize=11, fontweight="bold",
            fontfamily="monospace", zorder=4)


def _tree_edge(ax, a, b, label=None):
    ax.plot([a[0], b[0]], [a[1], b[1]], color=FG, lw=0.8, alpha=0.6)
    if label is None:
        return
    # Place label at ~40% from parent, slightly offset to the outer side.
    mx = a[0] + 0.40 * (b[0] - a[0])
    my = a[1] + 0.40 * (b[1] - a[1])
    dx = -0.25 if b[0] < a[0] else 0.25
    ax.text(mx + dx, my, label, ha="center", va="center",
            color=FG, fontsize=10, fontstyle="italic",
            bbox=dict(facecolor="black", edgecolor="none",
                      alpha=0.0, pad=1.0))


def _draw_tree(ax, *, show_root: bool, show_left_y: bool,
               show_right_y: bool, show_depth2: bool):
    if not show_root:
        ax.text(5.0, 3.0, "(empty tree)", ha="center", va="center",
                color=FG, fontsize=11, fontstyle="italic", alpha=0.5)
        return

    _tree_node(ax, ROOT, "x", COLOR_X)

    if show_left_y:
        _tree_edge(ax, ROOT, L1_L, "≤")
        _tree_node(ax, L1_L, "y", COLOR_Y)
    if show_right_y:
        _tree_edge(ax, ROOT, L1_R, ">")
        _tree_node(ax, L1_R, "y", COLOR_Y)

    if show_depth2:
        for parent, key_l, key_r in [(L1_L, "LL", "LR"), (L1_R, "RL", "RR")]:
            _tree_edge(ax, parent, L2[key_l], "≤")
            _tree_edge(ax, parent, L2[key_r], ">")
            _tree_node(ax, L2[key_l], "x", COLOR_X)
            _tree_node(ax, L2[key_r], "x", COLOR_X)
        for key, pos in L2.items():
            for leaf_pos in LEAVES[key]:
                _tree_edge(ax, pos, leaf_pos)
                _tree_node(ax, leaf_pos, "·", COLOR_LEAF, rad=0.28)


def _draw_splits(ax, *, show_root: bool, show_left_y: bool,
                 show_right_y: bool, show_depth2: bool):
    xmin, xmax, ymin, ymax = BOUNDS

    if show_root:
        _vline(ax, MED_X0, ymin, ymax, COLOR_X, lw=2.2)

    if show_left_y:
        _hline(ax, xmin, MED_X0, MED_Y_L, COLOR_Y)
    if show_right_y:
        _hline(ax, MED_X0, xmax, MED_Y_R, COLOR_Y)

    if show_depth2:
        _vline(ax, MED_X_LL, ymin, MED_Y_L, COLOR_X, lw=1.4)
        _vline(ax, MED_X_LR, MED_Y_L, ymax, COLOR_X, lw=1.4)
        _vline(ax, MED_X_RL, ymin, MED_Y_R, COLOR_X, lw=1.4)
        _vline(ax, MED_X_RR, MED_Y_R, ymax, COLOR_X, lw=1.4)


# --- Steps ---------------------------------------------------------------
STEPS = [
    # (step, show_root, show_left_y, show_right_y, show_depth2)
    (0, False, False, False, False),
    (1, True,  False, False, False),
    (2, True,  True,  False, False),
    (3, True,  True,  True,  False),
    (4, True,  True,  True,  True),
]

for step, root, ly, ry, d2 in STEPS:
    fig, ax_plane, ax_tree = _new_fig()
    _draw_splits(ax_plane, show_root=root, show_left_y=ly,
                 show_right_y=ry, show_depth2=d2)
    _draw_points(ax_plane)
    _draw_tree(ax_tree, show_root=root, show_left_y=ly,
               show_right_y=ry, show_depth2=d2)
    plt.tight_layout()
    save(fig, f"{PREFIX}{step:02d}.png")
    plt.close(fig)
