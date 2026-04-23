"""Uniform-grid walkthrough — one PNG per narrated step.

What this file contains
-----------------------
Emits grid_step_00..grid_step_03.png with identical axes so the slide
can stack them with `.r-stack` + `.fragment` and each click lands one
teaching beat:

  step_00  scattered points only — "here is the data"
  step_01  grid overlay on top    — "we lay a grid over it"
  step_02  query cell + 8 neighbours highlighted with the query star
           — "a near-neighbour query touches only these 9 cells"
  step_03  + a non-point polygon (irregular convex shape) straddling
           several cells, with every overlapping cell tinted — "an
           extent object is inserted into every cell it touches"

Why it exists
-------------
The static spatial_grid.png shows the final state all at once. Breaking
it into three frames lets the speaker narrate the setup before the
answer is visible, which is the whole reason the structure is simple.

How to use
----------
Run from the assets/ directory:

    python gen_grid_animation.py

When to change
--------------
The point cloud, grid resolution, and query position are shared with
gen_spatial.py's uniform-grid figure so the two read as one. Update
together if you re-tune the cell size, point count, or query.
"""

from __future__ import annotations

import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import ACCENT, CELL, FG, draw_annotation, save, setup_mpl

setup_mpl()

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PREFIX = os.path.join(OUT_DIR, "grid_step_")

GRID_N = 8
CELL_SIZE = 1.0
POINT_COUNT = 90

# Deterministic point cloud, matched to gen_spatial.py's seed.
rng = random.Random(42)
POINTS = [
    (
        rng.uniform(0.1, GRID_N * CELL_SIZE - 0.1),
        rng.uniform(0.1, GRID_N * CELL_SIZE - 0.1),
    )
    for _ in range(POINT_COUNT)
]

QUERY = (4.55, 3.2)

# Shared axis window across all frames so fragments swap without jitter.
XLIM = (-0.3, GRID_N * CELL_SIZE + 4.5)
YLIM = (-0.3, GRID_N * CELL_SIZE + 0.5)

def _new_fig():
    fig, ax = plt.subplots(figsize=(10.0, 5.0))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    return fig, ax


def _draw_points(ax):
    for px, py in POINTS:
        ax.plot(
            px, py, "o", markersize=4, color=CELL["data"],
            markeredgecolor=FG, markeredgewidth=0.4,
        )


def _draw_grid(ax):
    for i in range(GRID_N + 1):
        ax.plot(
            [0, GRID_N * CELL_SIZE], [i * CELL_SIZE, i * CELL_SIZE],
            color=FG, lw=0.4, alpha=0.4,
        )
        ax.plot(
            [i * CELL_SIZE, i * CELL_SIZE], [0, GRID_N * CELL_SIZE],
            color=FG, lw=0.4, alpha=0.4,
        )


def _draw_query(ax):
    qcx, qcy = int(QUERY[0]), int(QUERY[1])
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx, cy = qcx + dx, qcy + dy
            if not (0 <= cx < GRID_N and 0 <= cy < GRID_N):
                continue
            color = CELL["hot"] if (dx, dy) == (0, 0) else CELL["warn"]
            alpha = 0.35 if (dx, dy) == (0, 0) else 0.18
            ax.add_patch(mpatches.Rectangle(
                (cx, cy), CELL_SIZE, CELL_SIZE,
                facecolor=color, alpha=alpha, edgecolor=color, lw=1.1,
            ))
    ax.plot(
        *QUERY, "*", markersize=16, color=CELL["hot"],
        markeredgecolor="white", markeredgewidth=0.8, zorder=6,
    )
    draw_annotation(
        ax, GRID_N * CELL_SIZE + 0.3, 5.0,
        "query cell + 8 neighbours\n= all the work",
        color=ACCENT, ha="left",
    )


# --- step 00: just the points ---------------------------------------------
fig, ax = _new_fig()
_draw_points(ax)
plt.tight_layout()
save(fig, f"{PREFIX}00.png")
plt.close(fig)

# --- step 01: points + grid overlay ---------------------------------------
fig, ax = _new_fig()
_draw_grid(ax)
_draw_points(ax)
plt.tight_layout()
save(fig, f"{PREFIX}01.png")
plt.close(fig)

# --- step 02: + query cell, neighbours, query star ------------------------
fig, ax = _new_fig()
_draw_grid(ax)
_draw_points(ax)
_draw_query(ax)
plt.tight_layout()
save(fig, f"{PREFIX}02.png")
plt.close(fig)

# --- step 03: + a non-point polygon straddling several cells --------------
# Placed away from the query region so the two highlights don't fight.
# An irregular convex hexagon — visibly non-axis-aligned, so the point
# "insert into every overlapping cell" doesn't look like a trivial AABB.
from matplotlib.path import Path  # noqa: E402

OBJ_POLY = [
    (1.25, 5.60),
    (1.85, 5.05),
    (3.40, 5.10),
    (3.95, 6.05),
    (3.30, 6.85),
    (1.70, 6.75),
]


def _cell_overlaps_poly(cx: int, cy: int, poly_path: Path, samples: int = 9) -> bool:
    """True iff any sampled point inside cell (cx, cy) lies in the polygon.

    9x9 sub-sampling catches thin overlaps at the cell edge reliably for
    the 1-unit cells used here.
    """
    xs = [cx + (i + 0.5) / samples for i in range(samples)]
    ys = [cy + (j + 0.5) / samples for j in range(samples)]
    pts = [(x, y) for x in xs for y in ys]
    return bool(poly_path.contains_points(pts).any())


def _draw_object(ax):
    poly_path = Path(OBJ_POLY + [OBJ_POLY[0]], closed=True)

    xs = [p[0] for p in OBJ_POLY]
    ys = [p[1] for p in OBJ_POLY]
    cx0, cx1 = int(min(xs)), int(max(xs))
    cy0, cy1 = int(min(ys)), int(max(ys))

    for cx in range(cx0, cx1 + 1):
        for cy in range(cy0, cy1 + 1):
            if not (0 <= cx < GRID_N and 0 <= cy < GRID_N):
                continue
            if not _cell_overlaps_poly(cx, cy, poly_path):
                continue
            ax.add_patch(mpatches.Rectangle(
                (cx, cy), CELL_SIZE, CELL_SIZE,
                facecolor=CELL["ok"], alpha=0.22,
                edgecolor=CELL["ok"], lw=1.0,
            ))

    ax.add_patch(mpatches.Polygon(
        OBJ_POLY, closed=True,
        facecolor=CELL["ok"], alpha=0.55,
        edgecolor=CELL["ok"], lw=1.8, zorder=5,
    ))


fig, ax = _new_fig()
_draw_grid(ax)
_draw_points(ax)
_draw_query(ax)
_draw_object(ax)
plt.tight_layout()
save(fig, f"{PREFIX}03.png")
plt.close(fig)
