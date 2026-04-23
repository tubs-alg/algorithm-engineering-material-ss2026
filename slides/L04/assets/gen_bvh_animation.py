"""BVH walkthrough — one PNG per narrated step.

What this file contains
-----------------------
Emits bvh_step_00..bvh_step_04.png. Bottom-up build, then ray query:

  step_00  triangles only — the raw geometry
  step_01  + leaf AABBs wrapping each tight cluster
  step_02  + intermediate nodes grouping leaf pairs
  step_03  + root box enclosing the whole hierarchy
  step_04  + a ray: subtrees the ray misses fade out, showing prune

All five frames share identical axes/layout so fragment swaps don't
jitter.

Why it exists
-------------
The static bvh.png collapses the whole hierarchy into one frame. Per
step reveals let the speaker narrate the build bottom-up, and then the
last frame turns the structure into a query: the ray descends only
into boxes it intersects, everything else is discarded.

How to use
----------
Run from the assets/ directory:

    python gen_bvh_animation.py

When to change
--------------
Triangle positions, box extents, and the ray are hand-picked so that
the ray cleanly misses one intermediate (pruning two leaves) and hits
the other (descending into both its leaves). If you move geometry,
re-check `_ray_hits_box` on every intermediate/leaf so the pedagogy
still holds.
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
PREFIX = os.path.join(OUT_DIR, "bvh_step_")

# --- Geometry (shared with gen_spatial.py; tweaked ray) ------------------
LEAF_BOXES = [
    # (xy0, xy1, key)
    ((0.6, 1.0), (2.6, 2.5), "A"),
    ((3.4, 0.7), (5.6, 2.3), "B"),
    ((7.2, 2.0), (9.4, 3.6), "C"),
    ((9.8, 0.6), (11.8, 2.4), "D"),
]
TRI_PTS = {
    "A": [
        [(1.0, 1.3), (1.9, 1.2), (1.3, 2.2)],
        [(1.8, 1.8), (2.4, 1.4), (2.2, 2.3)],
    ],
    "B": [
        [(3.7, 1.0), (4.5, 1.2), (4.0, 2.0)],
        [(4.6, 1.4), (5.3, 1.2), (5.2, 2.1)],
    ],
    "C": [
        [(7.5, 2.4), (8.3, 2.3), (7.8, 3.3)],
        [(8.4, 2.6), (9.2, 2.5), (9.0, 3.4)],
    ],
    "D": [
        [(10.1, 0.9), (10.9, 1.0), (10.4, 2.0)],
        [(11.0, 1.3), (11.6, 1.2), (11.4, 2.2)],
    ],
}
INTER = [
    # (xy0, xy1, key, children)
    ((0.3, 0.4), (5.9, 2.8), "L", ("A", "B")),
    ((6.9, 0.3), (12.1, 3.9), "R", ("C", "D")),
]
ROOT = ((0.1, 0.2), (12.3, 4.1))

# Ray: misses node L entirely, hits node R and both its leaves C and D.
RAY_START = (0.5, 5.3)
RAY_END = (12.5, 1.5)

XLIM = (-0.8, 13.2)
YLIM = (-0.2, 5.6)


# --- Helpers --------------------------------------------------------------
def _new_fig():
    fig, ax = plt.subplots(figsize=(13.0, 5.5))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    return fig, ax


def _ray_hits_box(box) -> bool:
    """Slab test for segment RAY_START..RAY_END against axis-aligned box."""
    (x0, y0), (x1, y1) = box
    rx0, ry0 = RAY_START
    rx1, ry1 = RAY_END
    dx, dy = rx1 - rx0, ry1 - ry0

    tmin, tmax = 0.0, 1.0
    for p, d, lo, hi in ((rx0, dx, x0, x1), (ry0, dy, y0, y1)):
        if abs(d) < 1e-12:
            if p < lo or p > hi:
                return False
            continue
        t1 = (lo - p) / d
        t2 = (hi - p) / d
        if t1 > t2:
            t1, t2 = t2, t1
        tmin = max(tmin, t1)
        tmax = min(tmax, t2)
        if tmin > tmax:
            return False
    return True


def _draw_triangles(ax, key: str, dim: bool = False):
    alpha = 0.15 if dim else 0.85
    for tri in TRI_PTS[key]:
        ax.add_patch(mpatches.Polygon(
            tri, closed=True,
            facecolor=CELL["data"], edgecolor="white",
            alpha=alpha, lw=0.6,
        ))


def _draw_rect(ax, box, color, lw, dashes=None, alpha=1.0):
    (x0, y0), (x1, y1) = box
    kwargs = dict(facecolor="none", edgecolor=color, lw=lw, alpha=alpha)
    if dashes is not None:
        kwargs["linestyle"] = (0, dashes)
    ax.add_patch(mpatches.Rectangle((x0, y0), x1 - x0, y1 - y0, **kwargs))


def _draw_ray(ax):
    ax.annotate(
        "", xy=RAY_END, xytext=RAY_START,
        arrowprops=dict(arrowstyle="-|>", color=CELL["cache"], lw=2.4),
    )
    ax.text(RAY_START[0] - 0.1, RAY_START[1] + 0.1, "ray",
            color=CELL["cache"], fontsize=11, fontweight="bold",
            fontstyle="italic")


# --- Frame composers ------------------------------------------------------
def frame(step: int, *, show_leaves: bool, show_inter: bool,
          show_root: bool, show_ray: bool):
    fig, ax = _new_fig()

    # Triangles: dim the missed subtree on the query step.
    if show_ray:
        hit_keys = {k for (xy0, xy1, k) in LEAF_BOXES
                    if _ray_hits_box((xy0, xy1))}
    else:
        hit_keys = {k for (_, _, k) in LEAF_BOXES}

    for (_, _, key) in LEAF_BOXES:
        _draw_triangles(ax, key, dim=show_ray and key not in hit_keys)

    # Leaf AABBs.
    if show_leaves:
        for xy0, xy1, key in LEAF_BOXES:
            lit = (key in hit_keys) if show_ray else True
            _draw_rect(
                ax, (xy0, xy1),
                color=CELL["ok"] if lit else CELL["ok"],
                lw=1.4, dashes=(3, 2),
                alpha=1.0 if lit else 0.18,
            )

    # Intermediates.
    if show_inter:
        for xy0, xy1, key, kids in INTER:
            lit = any(k in hit_keys for k in kids) if show_ray else True
            _draw_rect(
                ax, (xy0, xy1),
                color=CELL["warn"], lw=1.7, dashes=(5, 2),
                alpha=1.0 if lit else 0.18,
            )
            ax.text(xy0[0] + 0.1, xy1[1] + 0.08,
                    f"node {key}",
                    color=CELL["warn"], fontsize=9,
                    fontstyle="italic", fontweight="bold",
                    alpha=1.0 if lit else 0.3)

    # Root.
    if show_root:
        _draw_rect(ax, ROOT, color=CELL["hot"], lw=2.0)
        ax.text(ROOT[0][0] + 0.1, ROOT[1][1] + 0.15, "root",
                color=CELL["hot"], fontsize=10, fontweight="bold")

    # Ray + prune annotation.
    if show_ray:
        _draw_ray(ax)
        draw_annotation(
            ax, 12.8, 3.0,
            "subtree missed\n→ pruned",
            color=NEGATIVE, ha="right",
        )
        draw_annotation(
            ax, 12.8, 0.9,
            "hit subtree\n→ descend",
            color=ACCENT, ha="right",
        )

    plt.tight_layout()
    save(fig, f"{PREFIX}{step:02d}.png")
    plt.close(fig)


# --- Steps ---------------------------------------------------------------
frame(0, show_leaves=False, show_inter=False, show_root=False, show_ray=False)
frame(1, show_leaves=True,  show_inter=False, show_root=False, show_ray=False)
frame(2, show_leaves=True,  show_inter=True,  show_root=False, show_ray=False)
frame(3, show_leaves=True,  show_inter=True,  show_root=True,  show_ray=False)
frame(4, show_leaves=True,  show_inter=True,  show_root=True,  show_ray=True)
