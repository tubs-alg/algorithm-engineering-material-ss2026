"""R-tree walkthrough — one PNG per narrated step.

What this file contains
-----------------------
Emits rtree_step_00..rtree_step_04.png. Mirrors the BVH animation in
structure but shifts the pedagogy to the R-tree specifics: sibling
MBRs may overlap, so a query rectangle can descend into more than one.

  step_00  raw spatial rectangles — the data
  step_01  + parent MBRs grouping siblings (allowed to overlap)
  step_02  + root MBR
  step_03  + query rectangle drawn
  step_04  query evaluation: MBRs disjoint from the query fade;
           the query rectangle straddles N2 and N3 so both stay lit

Why it exists
-------------
The static rtree.png collapses the whole story — grouping, overlap,
query — into one frame. Per-step reveals let the speaker introduce
"each node is the MBR of its children" before the overlap property,
and the overlap only bites in the query step when two siblings both
have to be explored.

How to use
----------
Run from the assets/ directory:

    python gen_rtree_animation.py

When to change
--------------
The leaf rectangles, parent MBRs, and query rectangle are hand-placed
so the query cleanly intersects N2 and N3 but misses N1. If you edit
any geometry, re-verify the query still straddles exactly two parents.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import ACCENT, CELL, FG, NEGATIVE, draw_annotation, save, setup_mpl

setup_mpl()

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PREFIX = os.path.join(OUT_DIR, "rtree_step_")

# --- Geometry (shared with gen_spatial.py's rtree figure) -----------------
LEAF_RECTS = [
    # (xy0, xy1, label, parent_key)
    ((0.5, 3.4), (1.9, 4.3), "a", "N1"),
    ((1.1, 2.5), (2.4, 3.5), "b", "N1"),
    ((0.3, 1.7), (1.5, 2.6), "c", "N1"),
    ((2.6, 1.8), (4.1, 3.0), "d", "N2"),
    ((3.4, 2.8), (4.8, 4.1), "e", "N2"),
    ((5.7, 2.2), (7.0, 3.4), "f", "N3"),
    ((6.5, 3.2), (7.9, 4.2), "g", "N3"),
    ((6.3, 1.0), (7.6, 2.1), "h", "N3"),
]
GROUPS = [
    ((0.2, 1.5), (2.5, 4.5), "N1"),
    ((2.4, 1.6), (5.0, 4.3), "N2"),
    ((5.5, 0.8), (8.1, 4.4), "N3"),
]
ROOT = ((0.1, 0.7), (8.2, 4.6))
# Query straddles N2 and N3; misses N1 entirely.
QUERY = ((3.2, 2.2), (6.8, 3.8))

XLIM = (-0.3, 10.2)
YLIM = (0.0, 5.3)


# --- Helpers --------------------------------------------------------------
def _new_fig():
    fig, ax = plt.subplots(figsize=(10.0, 5.5))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    return fig, ax


def _rects_overlap(a, b) -> bool:
    (ax0, ay0), (ax1, ay1) = a
    (bx0, by0), (bx1, by1) = b
    return not (ax1 < bx0 or bx1 < ax0 or ay1 < by0 or by1 < ay0)


def _draw_leaf(ax, xy0, xy1, label, *, alpha: float):
    ax.add_patch(mpatches.Rectangle(
        xy0, xy1[0] - xy0[0], xy1[1] - xy0[1],
        facecolor=CELL["data"], alpha=0.25 * alpha,
        edgecolor=CELL["data"], lw=1.2 * alpha + 0.2,
    ))
    ax.text(
        (xy0[0] + xy1[0]) / 2, (xy0[1] + xy1[1]) / 2, label,
        ha="center", va="center",
        color="white", fontsize=9, fontweight="bold",
        fontfamily="monospace", alpha=alpha,
    )


def _draw_group(ax, xy0, xy1, label, *, alpha: float):
    ax.add_patch(mpatches.Rectangle(
        xy0, xy1[0] - xy0[0], xy1[1] - xy0[1],
        facecolor="none",
        edgecolor=CELL["warn"], lw=1.6,
        linestyle=(0, (5, 2)),
        alpha=alpha,
    ))
    ax.text(
        xy0[0] + 0.05, xy1[1] - 0.05, label,
        ha="left", va="top",
        color=CELL["warn"], fontsize=10, fontweight="bold",
        alpha=alpha,
    )


def _draw_root(ax):
    ax.add_patch(mpatches.Rectangle(
        ROOT[0], ROOT[1][0] - ROOT[0][0], ROOT[1][1] - ROOT[0][1],
        facecolor="none", edgecolor=CELL["hot"], lw=2.0,
    ))
    ax.text(ROOT[0][0] + 0.05, ROOT[1][1] + 0.1, "root",
            color=CELL["hot"], fontsize=10, fontweight="bold")


def _draw_query(ax):
    ax.add_patch(mpatches.Rectangle(
        QUERY[0], QUERY[1][0] - QUERY[0][0], QUERY[1][1] - QUERY[0][1],
        facecolor=CELL["cache"], alpha=0.18,
        edgecolor=CELL["cache"], lw=1.8, linestyle=(0, (2, 2)),
    ))
    ax.text(QUERY[0][0] + 0.05, QUERY[0][1] - 0.18, "query",
            color=CELL["cache"], fontsize=10,
            fontstyle="italic", fontweight="bold")


# --- Frame composer -------------------------------------------------------
def frame(step: int, *, show_groups: bool, show_root: bool,
          show_query: bool, evaluate: bool):
    fig, ax = _new_fig()

    # Which parent groups the query hits (only matters in evaluate mode).
    hit_groups = set()
    if evaluate:
        for xy0, xy1, label in GROUPS:
            if _rects_overlap((xy0, xy1), QUERY):
                hit_groups.add(label)

    for xy0, xy1, label, parent in LEAF_RECTS:
        alpha = 1.0
        if evaluate and parent not in hit_groups:
            alpha = 0.22
        _draw_leaf(ax, xy0, xy1, label, alpha=alpha)

    if show_groups:
        for xy0, xy1, label in GROUPS:
            alpha = 1.0
            if evaluate and label not in hit_groups:
                alpha = 0.22
            _draw_group(ax, xy0, xy1, label, alpha=alpha)

    if show_root:
        _draw_root(ax)

    if show_query:
        _draw_query(ax)

    if evaluate:
        draw_annotation(
            ax, 9.3, 4.2,
            "sibling MBRs\nmay overlap →\nquery descends\ninto both",
            color=ACCENT, ha="right",
        )
        draw_annotation(
            ax, 9.3, 1.2,
            "disjoint subtree\n→ pruned",
            color=NEGATIVE, ha="right",
        )

    plt.tight_layout()
    save(fig, f"{PREFIX}{step:02d}.png")
    plt.close(fig)


# --- Steps ---------------------------------------------------------------
frame(0, show_groups=False, show_root=False, show_query=False, evaluate=False)
frame(1, show_groups=True,  show_root=False, show_query=False, evaluate=False)
frame(2, show_groups=True,  show_root=True,  show_query=False, evaluate=False)
frame(3, show_groups=True,  show_root=True,  show_query=True,  evaluate=False)
frame(4, show_groups=True,  show_root=True,  show_query=True,  evaluate=True)
