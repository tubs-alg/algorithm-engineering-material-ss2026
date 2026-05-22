"""Single-panel visualization for the separation theorem slide.

Produces one PNG (opaque dark background, dark-theme palette):

  tsp_separation.png   One fractional LP solution (degree-only) with a red
                       cut path enclosing a subset S whose cut value lies
                       strictly between 0 and 2 — a violated DFJ inequality.

Why this exists. The separation theorem is the bridge between "exponentially
many DFJ constraints" and "polynomial-time LP". The picture has to make the
oracle concrete: input is a fractional point, output is a single violated
constraint (the min-cut) that the LP did not see before. Drawing the cut as
a closed jagged curve through the figure visualises the subset boundary
geometrically — cross-edges crossing the curve carry the small fractional
weight that the cut constraint will force up to 2.

How to use. `python assets/gen_tsp_separation.py` from the slides/ directory.
Requires scipy (HiGHS LP) and networkx (min-cut).
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from scipy.optimize import linprog
from scipy.sparse import lil_matrix, vstack
from pathlib import Path

OUT = Path(__file__).parent

FG = "#e0e0e0"
NODE_FILL = "#2d4059"
NODE_EDGE = "#9ad0f5"
EDGE = "#f5d76e"
CUT_EDGE = "#e74c3c"
S_FILL = "#c27ba0"
GRID = "#37474f"
SLIDE_BG = "#191919"

plt.rcParams.update({
    "text.color": FG,
    "axes.titlecolor": FG,
    "font.size": 12,
})


def build_instance():
    """Two clusters of 5 nodes plus one bridge node. The degree-only LP
    returns a fractional vertex with a min-cut of value 1.0 carved out of
    the left cluster — two half-integer edges (x=0.5 each) crossing the
    boundary of a small subset S. Picked from a seed sweep; see comment
    block below for the search."""
    rng = np.random.default_rng(33)
    left = rng.standard_normal((5, 2)) * np.array([0.7, 0.9]) + np.array([-2.5, 0.0])
    right = rng.standard_normal((5, 2)) * np.array([0.7, 0.9]) + np.array([+2.5, 0.0])
    bridge = rng.standard_normal((1, 2)) * 0.3 + np.array([0.0, 0.0])
    pts = np.vstack([left, right, bridge])
    D = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
    return pts, D


def build_var_index(n):
    idx = {}
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            idx[(i, j)] = k
            k += 1
    return idx, k


def solve_relaxation(D, var_idx, nvars, n, ub_rows=None, ub_rhs=None):
    c = np.zeros(nvars)
    for (i, j), k in var_idx.items():
        c[k] = D[i, j]
    A_eq = lil_matrix((n, nvars))
    b_eq = np.full(n, 2.0)
    for (i, j), k in var_idx.items():
        A_eq[i, k] = 1.0
        A_eq[j, k] = 1.0
    A_eq = A_eq.tocsr()
    bounds = [(0.0, 1.0)] * nvars
    A_ub = b_ub = None
    if ub_rows:
        A_ub = vstack(ub_rows).tocsr()
        b_ub = np.array(ub_rhs)
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")
    return res.fun, res.x


def find_min_cut(x, var_idx, n, eps=1e-6):
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for (i, j), k in var_idx.items():
        if x[k] > eps:
            G.add_edge(i, j, capacity=float(x[k]))
    best_val = float("inf")
    best_S = None
    for t in range(1, n):
        try:
            val, (S, _) = nx.minimum_cut(G, 0, t)
        except (nx.NetworkXError, nx.NetworkXUnbounded):
            continue
        if val < best_val - 1e-12:
            best_val = val
            best_S = S if 0 in S else (set(range(n)) - S)
    return best_S, best_val


def draw_panel(ax, pts, x, var_idx, n, title=None, S=None,
               highlight_cut=False, show_S_labels=False, cut_value=None):
    cut_edges = set()
    if highlight_cut and S is not None:
        for (i, j) in var_idx:
            if (i in S) ^ (j in S):
                cut_edges.add((i, j))

    # Edges first (under nodes). Thickness/opacity encode x linearly so
    # half-integer edges read as visibly thinner than x=1 edges.
    for (i, j), k in var_idx.items():
        w = float(x[k])
        if w < 1e-3:
            continue
        if (i, j) in cut_edges:
            color = CUT_EDGE
            lw = 0.8 + 5.0 * w
            alpha = 0.95
        else:
            color = EDGE
            lw = 0.5 + 5.0 * w
            alpha = 0.30 + 0.65 * w
        ax.plot([pts[i, 0], pts[j, 0]], [pts[i, 1], pts[j, 1]],
                color=color, lw=lw, alpha=alpha, zorder=1,
                solid_capstyle="round")

    # Nodes — S shaded in panel 2 and 3.
    node_colors = [S_FILL if (S is not None and i in S) else NODE_FILL
                   for i in range(n)]
    ax.scatter(pts[:, 0], pts[:, 1], s=130, c=node_colors,
               edgecolor=NODE_EDGE, linewidth=1.4, zorder=3)

    if show_S_labels and S is not None:
        # Geometric cut: a closed jagged red curve around S. A graph cut
        # is the boundary of S, so the honest visualization is a closed
        # loop, not a straight line. Half-integer cross-edges drawn in
        # red above pierce this boundary visibly.
        from scipy.spatial import ConvexHull
        S_pts = pts[list(S)]
        if len(S_pts) >= 3:
            hull = ConvexHull(S_pts)
            hull_pts = S_pts[hull.vertices]
        else:
            hull_pts = S_pts
        centroid = hull_pts.mean(axis=0)
        # Expand outward and densify with a zigzag to evoke a scissors cut.
        pad = 0.55
        expanded = []
        for p in hull_pts:
            d = p - centroid
            norm = np.linalg.norm(d)
            if norm < 1e-9:
                continue
            expanded.append(p + d / norm * pad)
        expanded = np.array(expanded)
        # Densify the polygon and add a small zigzag along its perimeter.
        loop = np.vstack([expanded, expanded[:1]])
        densified = []
        for k in range(len(loop) - 1):
            a, b = loop[k], loop[k + 1]
            for t in np.linspace(0, 1, 8, endpoint=False):
                densified.append(a * (1 - t) + b * t)
        densified.append(loop[-1])
        densified = np.array(densified)
        # Add perpendicular zigzag jitter
        c2 = densified.mean(axis=0)
        normals = densified - c2
        normals = normals / (np.linalg.norm(normals, axis=1, keepdims=True) + 1e-9)
        jitter = 0.05 * np.array([(-1) ** k for k in range(len(densified))])
        cut_curve = densified + normals * jitter[:, None]
        ax.plot(cut_curve[:, 0], cut_curve[:, 1], color=CUT_EDGE,
                lw=2.6, alpha=0.9, solid_capstyle="round",
                solid_joinstyle="round", zorder=2)

        # S / V\S labels placed BELOW the nodes inside the axes so they
        # never collide with the title.
        notS = [i for i in range(n) if i not in S]
        notS_pts = pts[notS]
        y_label = min(S_pts[:, 1].min(), notS_pts[:, 1].min()) - 0.3
        ax.text(S_pts[:, 0].mean(), y_label, r"$S$",
                color=S_FILL, fontsize=26, ha="center", va="top",
                fontweight="bold")
        # V\S label centered over the non-S majority (right side here).
        ax.text(np.median(notS_pts[:, 0]), y_label, r"$V \setminus S$",
                color=NODE_EDGE, fontsize=26, ha="center", va="top",
                fontweight="bold")

    if title:
        ax.set_title(title, pad=10, fontsize=12)
    if cut_value is not None:
        # Inline cut-value annotation inside the plot (top-right) so we
        # don't burn vertical space on a full title.
        ax.text(0.98, 0.96,
                rf"min-cut on $\hat x$ = {cut_value:.2f} $< 2$",
                transform=ax.transAxes, ha="right", va="top",
                color=CUT_EDGE, fontsize=13, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.35",
                          facecolor=SLIDE_BG, edgecolor=CUT_EDGE,
                          linewidth=1.0))
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    # Tight margins; the S / V\S labels are placed just below the data.
    ax.margins(x=0.02, y=0.05)
    for sp in ("top", "right", "bottom", "left"):
        ax.spines[sp].set_color(GRID)
        ax.spines[sp].set_alpha(0.4)


def main():
    pts, D = build_instance()
    n = len(pts)
    var_idx, nvars = build_var_index(n)

    obj0, x0 = solve_relaxation(D, var_idx, nvars, n)
    S, cut_val = find_min_cut(x0, var_idx, n)
    print(f"Degree-only LP: bound={obj0:.2f}, min-cut={cut_val:.3f}, |S|={len(S)}")

    fig, ax = plt.subplots(figsize=(9.5, 4.4),
                           facecolor=SLIDE_BG, constrained_layout=True)
    ax.set_facecolor(SLIDE_BG)
    draw_panel(ax, pts, x0, var_idx, n, title=None,
               S=S, highlight_cut=True, show_S_labels=True,
               cut_value=cut_val)

    out = OUT / "tsp_separation.png"
    fig.savefig(out, dpi=180, bbox_inches="tight",
                facecolor=SLIDE_BG, transparent=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
