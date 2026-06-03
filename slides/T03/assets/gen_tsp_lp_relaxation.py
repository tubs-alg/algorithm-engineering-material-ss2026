"""Generate side-by-side TSP LP relaxation figure: MTZ (weak) vs DFJ (tight).

Produces one PNG (transparent background, dark-theme palette):

  tsp_lp_relaxation.png   2 panels on a 50-node random 2D Euclidean instance.
                          Left:  MTZ LP relaxation (big-M, fractional spaghetti).
                          Right: DFJ LP relaxation (subtour cuts, near-tour).

Why this exists. The strong-vs-weak section ends with the claim that MTZ has a
weak LP relaxation while DFJ has a tight one. The numbers and the picture have
to be shown together for the claim to land — students see the same instance,
the same nodes, but two very different fractional solutions and two very
different LP bounds.

How to use. `python assets/gen_tsp_lp_relaxation.py` from the slides/ directory.
Requires scipy (HiGHS LP) and networkx (min-cut separation oracle).

When to change. Reseed or change N for a different instance shape. The
visualization assumes asymmetric TSP variables x_ij; symmetric drawings sum
x_ij + x_ji per pair so the LP fractionality reads off the line thickness.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from scipy.optimize import linprog
from scipy.sparse import lil_matrix, csr_matrix, vstack
from pathlib import Path

OUT = Path(__file__).parent

FG = "#e0e0e0"
NODE_FILL = "#2d4059"
NODE_EDGE = "#9ad0f5"
EDGE_FRAC = "#9ad0f5"
EDGE_INT = "#f5d76e"
GRID = "#37474f"

plt.rcParams.update({
    "savefig.transparent": True,
    "text.color": FG,
    "axes.titlecolor": FG,
    "font.size": 12,
})

N = 70
RNG_SEED = 7
SCALE = 100.0
N_CLUSTERS = 5
CLUSTER_STD = 6.0


def build_instance():
    """Clustered Euclidean instance.

    Uniform-random points let MTZ (with 2-cycle elimination) look almost as
    strong as DFJ, because the dominant LP pathology is just 2-cycles. With
    well-separated clusters, the LP wants to form one mini-tour per cluster
    — exactly the subtour structure MTZ cannot forbid at the LP level and
    DFJ does. That makes the strong-vs-weak picture honest.
    """
    rng = np.random.default_rng(RNG_SEED)
    centers = rng.random((N_CLUSTERS, 2)) * SCALE
    cluster_ids = rng.integers(0, N_CLUSTERS, size=N)
    pts = centers[cluster_ids] + rng.standard_normal((N, 2)) * CLUSTER_STD
    D = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
    return pts, D


def build_var_index():
    idx = {}
    k = 0
    for i in range(N):
        for j in range(N):
            if i != j:
                idx[(i, j)] = k
                k += 1
    return idx, k


def degree_constraints(var_idx, nvars):
    A = lil_matrix((2 * N, nvars))
    for (i, j), k in var_idx.items():
        A[i, k] = 1.0       # out-degree of i
        A[N + j, k] = 1.0   # in-degree of j
    return A.tocsr(), np.ones(2 * N)


def solve_mtz(D, var_idx, nvars):
    """MTZ LP relaxation: x in [0,1], u in [1, N-1], MTZ big-M cuts."""
    nu = N - 1  # u_1, ..., u_{N-1}; u_0 fixed at 0 implicitly
    total = nvars + nu
    c = np.zeros(total)
    for (i, j), k in var_idx.items():
        c[k] = D[i, j]

    A_eq_x, b_eq = degree_constraints(var_idx, nvars)
    # extend equality matrix with zero columns for u variables
    A_eq = lil_matrix((2 * N, total))
    A_eq[:, :nvars] = A_eq_x
    A_eq = A_eq.tocsr()

    # MTZ: u_i - u_j + N x_ij <= N - 1 for i, j in {1,...,N-1}, i != j
    rows = []
    rhs = []
    for i in range(1, N):
        for j in range(1, N):
            if i == j:
                continue
            r = lil_matrix((1, total))
            r[0, nvars + (i - 1)] = 1.0
            r[0, nvars + (j - 1)] = -1.0
            r[0, var_idx[(i, j)]] = float(N)
            rows.append(r)
            rhs.append(N - 1)
    # 2-cycle elimination: x_ij + x_ji <= 1. Implied integrally by MTZ
    # (sum of the two potential rows gives x_ij + x_ji <= 2 - 2/N), but
    # not at the LP level. Adding it explicitly removes the most blatant
    # 2-cycle pathology so the remaining weakness is the real story.
    for i in range(N):
        for j in range(i + 1, N):
            r = lil_matrix((1, total))
            r[0, var_idx[(i, j)]] = 1.0
            r[0, var_idx[(j, i)]] = 1.0
            rows.append(r)
            rhs.append(1)
    A_ub = vstack(rows).tocsr()
    b_ub = np.array(rhs)

    bounds = [(0.0, 1.0)] * nvars + [(1.0, N - 1.0)] * nu
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")
    return res.fun, res.x[:nvars]


def support_digraph(x, var_idx, eps=1e-7):
    G = nx.DiGraph()
    G.add_nodes_from(range(N))
    for (i, j), k in var_idx.items():
        if x[k] > eps:
            G.add_edge(i, j, capacity=float(x[k]))
    return G


def find_violated_subtour(x, var_idx, tol=1e-6):
    """Return a set S with sum_{i in S, j not in S} x_ij < 1, or None."""
    G = support_digraph(x, var_idx)
    best_val = float("inf")
    best_S = None
    s = 0
    for t in range(1, N):
        for (src, dst) in ((s, t), (t, s)):
            try:
                val, (S, _) = nx.minimum_cut(G, src, dst)
            except nx.NetworkXUnbounded:
                continue
            if val < best_val - 1e-12:
                best_val = val
                best_S = S if src in S else (set(range(N)) - S)
    if best_val >= 1.0 - tol:
        return None, best_val
    # Always cut on S that excludes a "depot" node so we don't add the trivial S=V
    if best_S is None or len(best_S) == 0 or len(best_S) == N:
        return None, best_val
    return best_S, best_val


def solve_dfj(D, var_idx, nvars, max_iter=400):
    c = np.zeros(nvars)
    for (i, j), k in var_idx.items():
        c[k] = D[i, j]
    A_eq, b_eq = degree_constraints(var_idx, nvars)
    bounds = [(0.0, 1.0)] * nvars

    ub_rows = []
    ub_rhs = []
    iters = 0
    last_obj = None
    for iters in range(max_iter):
        if ub_rows:
            A_ub = vstack(ub_rows).tocsr()
            b_ub = np.array(ub_rhs)
        else:
            A_ub = None
            b_ub = None
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                      bounds=bounds, method="highs")
        last_obj = res.fun
        S, cut_val = find_violated_subtour(res.x, var_idx)
        if S is None:
            break
        # sum_{i in S, j notin S} x_ij >= 1  ->  -sum <= -1
        r = lil_matrix((1, nvars))
        not_S = [j for j in range(N) if j not in S]
        for i in S:
            for j in not_S:
                if (i, j) in var_idx:
                    r[0, var_idx[(i, j)]] = -1.0
        ub_rows.append(r)
        ub_rhs.append(-1.0)
    return last_obj, res.x, iters + 1


def draw_panel(ax, pts, x, var_idx, title):
    # Sum directions for visual line weight. Both panels use the same
    # color/thickness encoding so the viewer can compare them on equal
    # footing — the story we want to land is structural (subtours vs
    # global tour), not "yellow vs blue".
    weight = {}
    for (i, j), k in var_idx.items():
        a, b = (i, j) if i < j else (j, i)
        weight[(a, b)] = weight.get((a, b), 0.0) + float(x[k])
    for (i, j), w in weight.items():
        if w < 1e-3:
            continue
        color = EDGE_INT
        s = min(w, 1.0) ** 0.5
        lw = 0.6 + 3.4 * s
        alpha = 0.35 + 0.60 * s
        ax.plot([pts[i, 0], pts[j, 0]], [pts[i, 1], pts[j, 1]],
                color=color, lw=lw, alpha=alpha, zorder=1,
                solid_capstyle="round")
    ax.scatter(pts[:, 0], pts[:, 1], s=36, facecolor=NODE_FILL,
               edgecolor=NODE_EDGE, linewidth=1.4, zorder=3)
    ax.set_title(title, pad=10, fontsize=13)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ("top", "right", "bottom", "left"):
        ax.spines[s].set_color(GRID)
        ax.spines[s].set_alpha(0.4)


def main():
    pts, D = build_instance()
    var_idx, nvars = build_var_index()

    print(f"Solving MTZ LP relaxation on N={N} ...")
    mtz_obj, mtz_x = solve_mtz(D, var_idx, nvars)
    print(f"  MTZ LP bound = {mtz_obj:.3f}")

    print("Solving DFJ LP relaxation (subtour separation) ...")
    dfj_obj, dfj_x, dfj_iters = solve_dfj(D, var_idx, nvars)
    print(f"  DFJ LP bound = {dfj_obj:.3f}  ({dfj_iters} separation rounds)")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6.5))
    draw_panel(axes[0], pts, mtz_x, var_idx,
               f"MTZ LP relaxation     bound = {mtz_obj:.1f}")
    draw_panel(axes[1], pts, dfj_x, var_idx,
               f"DFJ LP relaxation     bound = {dfj_obj:.1f}")

    fig.tight_layout()
    out = OUT / "tsp_lp_relaxation.png"
    fig.savefig(out, dpi=160, bbox_inches="tight", transparent=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
