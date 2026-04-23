"""Delaunay triangulation walkthrough — one PNG per narrated step.

What this file contains
-----------------------
Emits delaunay_step_00..delaunay_step_02.png:

  step_00  scattered points — "a pile of points, no structure yet"
  step_01  + Delaunay edges — every edge is a local proximity relation
  step_02  one vertex's 1-ring highlighted (incident edges + neighbours)
           — the "neighbourhood" concept made concrete

Why it exists
-------------
Every other spatial structure in this section accelerates a query.
Delaunay is the odd one out: it converts a point cloud into a sparse
planar graph. Downstream you run graph algorithms on it — shortest
paths, clustering, mesh traversal. The slide exists to flag that
different job.

How to use
----------
Run from the assets/ directory:

    python gen_delaunay_animation.py

When to change
--------------
Point count and seed are tuned so the triangulation is dense enough to
look interesting but sparse enough that one 1-ring stands out. If the
1-ring vertex changes, re-pick one near the centre so its neighbours
do not overlap the figure's edges.
"""

from __future__ import annotations

import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scipy.spatial import Delaunay

from _viz_style import ACCENT, CELL, FG, save, setup_mpl

setup_mpl()

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PREFIX = os.path.join(OUT_DIR, "delaunay_step_")

# --- Points ---------------------------------------------------------------
rng = random.Random(7)
N = 38
POINTS = [(rng.uniform(0.4, 9.6), rng.uniform(0.4, 6.6)) for _ in range(N)]

# Add a small deterministic jitter-free anchor near the centre so we can
# reliably pick it as the "1-ring vertex" regardless of random draw.
FOCUS = (5.0, 3.5)
POINTS.append(FOCUS)
FOCUS_IDX = len(POINTS) - 1

XS = [p[0] for p in POINTS]
YS = [p[1] for p in POINTS]

tri = Delaunay(POINTS)

# --- Derive 1-ring neighbours of FOCUS_IDX -------------------------------
NEIGHBOURS: set[int] = set()
FOCUS_TRIS: list[tuple[int, int, int]] = []
for simplex in tri.simplices:
    if FOCUS_IDX in simplex:
        FOCUS_TRIS.append(tuple(int(i) for i in simplex))
        for j in simplex:
            if int(j) != FOCUS_IDX:
                NEIGHBOURS.add(int(j))


# --- Helpers --------------------------------------------------------------
XLIM = (-0.2, 10.2)
YLIM = (-0.2, 7.2)


def _new_fig():
    fig, ax = plt.subplots(figsize=(10.0, 5.5))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    return fig, ax


def _draw_points(ax, *, dim_focus: bool = False):
    for i, (px, py) in enumerate(POINTS):
        if i == FOCUS_IDX and dim_focus:
            continue  # drawn separately, on top
        ax.plot(
            px, py, "o", markersize=5, color=CELL["data"],
            markeredgecolor=FG, markeredgewidth=0.5, zorder=3,
        )


def _draw_edges(ax, *, highlight_focus: bool = False):
    # All Delaunay edges, drawn once, deduped by sorted endpoint tuple.
    seen: set[tuple[int, int]] = set()
    for simplex in tri.simplices:
        for a, b in (
            (simplex[0], simplex[1]),
            (simplex[1], simplex[2]),
            (simplex[2], simplex[0]),
        ):
            key = (int(min(a, b)), int(max(a, b)))
            if key in seen:
                continue
            seen.add(key)

            is_focus_edge = highlight_focus and FOCUS_IDX in key
            color = ACCENT if is_focus_edge else CELL["warn"]
            alpha = 1.0 if is_focus_edge else (0.35 if highlight_focus else 0.75)
            lw = 2.2 if is_focus_edge else 1.0

            p0 = POINTS[key[0]]
            p1 = POINTS[key[1]]
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                    color=color, lw=lw, alpha=alpha, zorder=2)


def _draw_focus(ax):
    fx, fy = POINTS[FOCUS_IDX]
    ax.plot(fx, fy, "o", markersize=9, color=ACCENT,
            markeredgecolor="white", markeredgewidth=1.2, zorder=5)
    for ni in NEIGHBOURS:
        nx, ny = POINTS[ni]
        ax.plot(nx, ny, "o", markersize=7, color=ACCENT,
                markeredgecolor="white", markeredgewidth=0.8, zorder=4)


# --- Steps ---------------------------------------------------------------
# step_00
fig, ax = _new_fig()
_draw_points(ax)
plt.tight_layout()
save(fig, f"{PREFIX}00.png")
plt.close(fig)

# step_01
fig, ax = _new_fig()
_draw_edges(ax)
_draw_points(ax)
plt.tight_layout()
save(fig, f"{PREFIX}01.png")
plt.close(fig)

# step_02
fig, ax = _new_fig()
_draw_edges(ax, highlight_focus=True)
_draw_points(ax, dim_focus=True)
_draw_focus(ax)
plt.tight_layout()
save(fig, f"{PREFIX}02.png")
plt.close(fig)
