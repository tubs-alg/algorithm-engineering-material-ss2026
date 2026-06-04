"""
Drawing primitives for the graph-vocabulary concept graphics (solve.py).

What this file contains:
  Four small, self-contained draw_* helpers that render the same node set with a
  consistent clean look: undirected edges, weighted edges (+ optional node
  annotation), directed arcs, and a layered DAG with a faded would-be back edge.
  Each takes an Axes so the same primitive serves both the standalone figures and
  the 2x2 overview panel. Non-goal: no graph algorithms, no layout solving;
  positions are passed in by the caller.

Why it exists:
  Keeps solve.py terse and under the LOC budget, and guarantees the four figures
  and the overview panel share identical node/edge styling.

How to use it:
  from helpers import draw_undirected, draw_weighted, draw_directed, draw_dag
  draw_undirected(ax, pos, edges, title="...")

When it would change:
  If a new vocabulary figure is added (e.g. multigraph, self-loop) or the visual
  language of the recap is retuned.
"""

from __future__ import annotations

import sys

import numpy as np
from matplotlib.patches import FancyArrowPatch

sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/"
    "week07-l08-graph-algorithms/snippets",
)
import aeviz  # noqa: E402

NODE_SIZE = 900
NODE_FACE = aeviz.PALETTE["node_face"]
NODE_EDGE = aeviz.PALETTE["node_edge"]
NODE_LW = 2.0
LABEL_COLOR = aeviz.PALETTE["ink"]
EDGE_COLOR = aeviz.PALETTE["edge"]
EDGE_WIDTH = 2.0
_LABEL_BBOX = dict(boxstyle="round,pad=0.18", fc=(0.10, 0.14, 0.20, 0.85), ec="none")


def _node_radius_pts() -> float:
    """Marker radius in points (node_size is the area in points^2)."""
    return np.sqrt(NODE_SIZE) / 2.0


def _draw_nodes(ax, pos, nodes, *, highlight=None):
    """Draw node disks + bold single-letter labels. `highlight` recolors one node."""
    highlight = highlight or set()
    for n in nodes:
        face = aeviz.PALETTE["good"] if n in highlight else NODE_FACE
        txt_color = "white" if n in highlight else LABEL_COLOR
        ax.scatter(
            *pos[n], s=NODE_SIZE, c=face, edgecolors=NODE_EDGE,
            linewidths=NODE_LW, zorder=3,
        )
        ax.text(
            *pos[n], n, ha="center", va="center", fontsize=13,
            fontweight="bold", color=txt_color, zorder=4,
        )


def _frame(ax, pos, *, title=None, pad=0.55):
    """Equal aspect, no axis, tight margins, optional terse title."""
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
    ax.set_aspect("equal")
    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=14, color=LABEL_COLOR)


def _straight(ax, pos, edges, *, color=EDGE_COLOR, width=EDGE_WIDTH):
    """Straight line segments between node centers (undirected look)."""
    for u, v in edges:
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        ax.plot([x0, x1], [y0, y1], color=color, lw=width, zorder=1,
                solid_capstyle="round")


def draw_undirected(ax, pos, edges, *, title=None):
    """Figure 01: the bare graph, nodes and unweighted undirected edges."""
    _straight(ax, pos, edges)
    _draw_nodes(ax, pos, pos.keys())
    _frame(ax, pos, title=title)


def draw_weighted(ax, pos, edges, weights, *, node_annotation=None, title=None):
    """Figure 02: same graph with edge weights, optional one-node annotation."""
    _straight(ax, pos, edges)
    for (u, v), w in weights.items():
        mx = (pos[u][0] + pos[v][0]) / 2.0
        my = (pos[u][1] + pos[v][1]) / 2.0
        ax.text(mx, my, str(w), ha="center", va="center", fontsize=12,
                color=aeviz.PALETTE["weight"], fontweight="bold",
                bbox=_LABEL_BBOX, zorder=2)
    hl = {node_annotation[0]} if node_annotation else set()
    _draw_nodes(ax, pos, pos.keys(), highlight=hl)
    if node_annotation:
        n, text = node_annotation
        x, y = pos[n]
        r = 0.42
        # Sit the tag just above the node disk so it labels THAT node, not the
        # whole figure (a high, detached label reads like a title).
        ax.annotate(
            text, xy=(x, y), xytext=(x, y + r + 0.06),
            ha="center", va="bottom", fontsize=11,
            color=aeviz.PALETTE["good"], fontweight="bold",
        )
    _frame(ax, pos, title=title)


def draw_directed(ax, pos, edges, *, rad=0.0, title=None, label=None):
    """Figure 03 / 04b: directed edges as arrowed arcs (one-way). A reciprocal
    pair (both u->v and v->u present) is bowed to opposite sides so a two-way
    edge reads as two parallel arcs rather than one overlapping line."""
    shrink = _node_radius_pts() + 3.0
    edge_set = set(edges)
    for u, v in edges:
        this_rad = rad
        if rad == 0.0 and (v, u) in edge_set:
            # arc3 already mirrors the curve when start/end swap, so both
            # directions need the SAME rad sign to land on opposite sides.
            this_rad = 0.18
        patch = FancyArrowPatch(
            pos[u], pos[v], connectionstyle=f"arc3,rad={this_rad}",
            arrowstyle="-|>", mutation_scale=18, lw=EDGE_WIDTH,
            color=EDGE_COLOR, shrinkA=shrink, shrinkB=shrink, zorder=1,
        )
        ax.add_patch(patch)
    _draw_nodes(ax, pos, pos.keys())
    if label:
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        ax.text((min(xs) + max(xs)) / 2.0, max(ys) + 0.45, label,
                ha="center", va="bottom", fontsize=11,
                color=aeviz.PALETTE["accent"], fontweight="bold")
    _frame(ax, pos, title=title)


def draw_dag(ax, pos, edges, *, back_edge=None, title=None):
    """Figure 04: layered DAG. Solid arcs point right; a faded dashed arc shows
    the forbidden back edge (annotated "not allowed")."""
    shrink = _node_radius_pts() + 3.0
    for u, v in edges:
        patch = FancyArrowPatch(
            pos[u], pos[v], connectionstyle="arc3,rad=0.0",
            arrowstyle="-|>", mutation_scale=18, lw=EDGE_WIDTH,
            color=aeviz.PALETTE["path"], shrinkA=shrink, shrinkB=shrink,
            zorder=1,
        )
        ax.add_patch(patch)
    if back_edge:
        u, v = back_edge
        # Bow the return arc down into the open center of the layout (negative
        # rad). It closes a real cycle from an interior node back to the source,
        # so it reads as "cycles are forbidden", not "this edge cannot be
        # two-way".
        rad = -0.32
        patch = FancyArrowPatch(
            pos[u], pos[v], connectionstyle=f"arc3,rad={rad}",
            arrowstyle="-|>", mutation_scale=16, lw=1.8,
            color=aeviz.PALETTE["accent"], linestyle=(0, (4, 3)),
            alpha=0.6, shrinkA=shrink, shrinkB=shrink, zorder=1,
        )
        ax.add_patch(patch)
        # Label at the arc's apex. matplotlib's arc3 bows toward [dy, -dx] for
        # positive rad, so the t=0.5 apex is m + 0.5*rad*[dy, -dx].
        p0 = np.asarray(pos[u], float)
        p2 = np.asarray(pos[v], float)
        m = (p0 + p2) / 2.0
        dx, dy = p2 - p0
        apex = m + 0.5 * rad * np.array([dy, -dx])
        ax.text(apex[0], apex[1] + 0.30, "no back edges", ha="center",
                va="bottom", fontsize=10.5, color=aeviz.PALETTE["accent"],
                fontstyle="italic")
    _draw_nodes(ax, pos, pos.keys())
    _frame(ax, pos, title=title, pad=0.7)
