"""Generate the "branching tightens the LP" figure for the Big-M section.

Produces `packing_lp_branched.png` — three side-by-side panels of the
same 20-square instance used by `gen_packing_lp_relax.py`. Reading
left to right:

  (1) Base LP relaxation. All directional binaries split 1/4 each;
      every separation constraint is non-binding; the bound collapses
      to B^LP = 2 s_max with all centers stacked.

  (2) LP with five b_ij*'s fixed. To guarantee the MIP optimum stays
      in the branched subtree, every fixed binary points in the
      direction the MIP solution actually uses. We then search over
      which 5 pairs (among the largest squares) to fix, scoring by
      B_lp pushed up minus a penalty on remaining pairwise overlap in
      the LP layout. This mirrors what a sane strong-branching rule
      would converge to: branches along the MIP frontier that tighten
      the bound the most.

  (3) MIP optimum from `solve_packing.py` — the same picture as on the
      previous slide for reference.

Why this exists. The previous slide shows the LP relaxation collapsing
to a useless bound; this slide shows that branch-and-bound is not
helpless. A small amount of branching on the right binaries already
removes most of the Big-M slack and produces a feasible-looking
lookahead the solver can exploit.

Reads `packing_solution.json` written by `solve_packing.py`.

Usage. `python assets/gen_packing_lp_branched.py` from slides/.
"""

import json
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import numpy as np

from ortools.math_opt.python import mathopt

OUT = Path(__file__).parent

BG = "none"
FG = "#e0e0e0"
HILITE = "#ffb300"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.transparent": True,
    "text.color": FG,
    "axes.labelcolor": FG,
    "axes.titlecolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "font.size": 14,
})


# Search configuration. Branch only among the K largest squares (the
# binaries a sane branching rule would touch first). Directions come
# from the MIP optimum, so the integer optimum is never cut off; we
# enumerate every C(K_TOP*(K_TOP-1)/2, N_BRANCHES) subset of pairs.
K_TOP = 6           # consider pairs among the 6 largest squares
N_BRANCHES = 5      # how many b's to fix
OVERLAP_WEIGHT = 0.5  # penalty on remaining pairwise overlap area


def build_lp(sides, branches):
    """Construct the packing LP relaxation with the given list of
    branch fixings. Each branch is a tuple (i, j, side) with i<j and
    side in {"L","R","A","B"}. Returns the result and the centers."""
    s_list = [side / 2 for side in sides]
    n = len(s_list)
    U_B = sum(sides)
    M = U_B

    model = mathopt.Model(name="packing-lp-branched")
    B = model.add_variable(lb=0, ub=U_B, name="B")
    x = [model.add_variable(lb=0, ub=U_B, name=f"x_{i}") for i in range(n)]
    y = [model.add_variable(lb=0, ub=U_B, name=f"y_{i}") for i in range(n)]

    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    bL = {p: model.add_variable(lb=0, ub=1, name=f"bL_{p}") for p in pairs}
    bR = {p: model.add_variable(lb=0, ub=1, name=f"bR_{p}") for p in pairs}
    bA = {p: model.add_variable(lb=0, ub=1, name=f"bA_{p}") for p in pairs}
    bBt = {p: model.add_variable(lb=0, ub=1, name=f"bB_{p}") for p in pairs}

    for (i, j, side) in branches:
        var = {"L": bL, "R": bR, "A": bA, "B": bBt}[side][i, j]
        model.add_linear_constraint(var == 1)

    for i in range(n):
        model.add_linear_constraint(x[i] >= s_list[i])
        model.add_linear_constraint(y[i] >= s_list[i])
        model.add_linear_constraint(x[i] + s_list[i] <= B)
        model.add_linear_constraint(y[i] + s_list[i] <= B)

    for (i, j) in pairs:
        sij = s_list[i] + s_list[j]
        model.add_linear_constraint(x[i] - x[j] >= sij - M * (1 - bL[i, j]))
        model.add_linear_constraint(x[j] - x[i] >= sij - M * (1 - bR[i, j]))
        model.add_linear_constraint(y[j] - y[i] >= sij - M * (1 - bA[i, j]))
        model.add_linear_constraint(y[i] - y[j] >= sij - M * (1 - bBt[i, j]))
        model.add_linear_constraint(bL[i, j] + bR[i, j] + bA[i, j] + bBt[i, j] == 1)

    model.minimize(B)
    result = mathopt.solve(model, mathopt.SolverType.HIGHS)
    if result.termination.reason != mathopt.TerminationReason.OPTIMAL:
        return None, None
    centers = [(result.variable_values()[x[i]],
                result.variable_values()[y[i]]) for i in range(n)]
    return result.objective_value(), centers


def total_overlap(centers, s_list):
    """Sum of pairwise overlap areas in the current layout."""
    total = 0.0
    n = len(s_list)
    for i in range(n):
        for j in range(i + 1, n):
            cxi, cyi = centers[i]
            cxj, cyj = centers[j]
            dx = (s_list[i] + s_list[j]) - abs(cxi - cxj)
            dy = (s_list[i] + s_list[j]) - abs(cyi - cyj)
            if dx > 0 and dy > 0:
                total += dx * dy
    return total


def mip_direction(i, j, centers, s_list):
    """Return the directional binary (L/R/A/B) consistent with the MIP
    layout for pair (i, j). Pick the direction with the largest margin
    so we fix the most informative branch."""
    cxi, cyi = centers[i]
    cxj, cyj = centers[j]
    sij = s_list[i] + s_list[j]
    margins = {
        "L": (cxi - cxj) - sij,   # x_i - x_j >= sij
        "R": (cxj - cxi) - sij,   # x_j - x_i >= sij
        "A": (cyj - cyi) - sij,   # y_j - y_i >= sij
        "B": (cyi - cyj) - sij,   # y_i - y_j >= sij
    }
    # The MIP solution satisfies at least one of these with margin >= -eps.
    return max(margins, key=margins.get)


def search_branches(sides, mip_centers):
    """Enumerate every N_BRANCHES-subset of pairs among the K_TOP
    largest squares, with directions taken from the MIP optimum.
    Return the highest-scoring branch set."""
    s_list = [side / 2 for side in sides]
    top_indices = list(range(K_TOP))
    candidate_pairs = list(combinations(top_indices, 2))
    pair_direction = {
        (i, j): mip_direction(i, j, mip_centers, s_list)
        for (i, j) in candidate_pairs
    }

    best = None
    n_tried = 0
    for chosen_pairs in combinations(candidate_pairs, N_BRANCHES):
        branches = [(i, j, pair_direction[i, j]) for (i, j) in chosen_pairs]
        B_lp, centers = build_lp(sides, branches)
        n_tried += 1
        if B_lp is None:
            continue
        overlap = total_overlap(centers, s_list)
        score = B_lp - OVERLAP_WEIGHT * overlap
        if best is None or score > best["score"]:
            best = {
                "branches": branches,
                "B_lp": B_lp,
                "centers": centers,
                "overlap": overlap,
                "score": score,
            }
    print(f"searched {n_tried} branch subsets")
    return best


def draw_panel(ax, B, centers, s_list, colors, title, view_max,
               highlight=None):
    """Draw a B-by-B container with squares of half-side s_list at centers."""
    cont = patches.Rectangle((0, 0), B, B, linewidth=2.0, edgecolor=FG,
                             facecolor="none", zorder=10)
    ax.add_patch(cont)

    highlight = highlight or set()
    order = np.argsort(s_list)[::-1]
    for rank, idx in enumerate(order):
        cx, cy = centers[idx]
        s = s_list[idx]
        edge = HILITE if idx in highlight else colors[idx]
        lw = 1.8 if idx in highlight else 0.7
        sq = patches.Rectangle((cx - s, cy - s), 2 * s, 2 * s, linewidth=lw,
                               edgecolor=edge, facecolor=colors[idx],
                               alpha=0.55, zorder=2 + rank)
        ax.add_patch(sq)

    ax.annotate("", xy=(B, -0.6), xytext=(0, -0.6),
                arrowprops=dict(arrowstyle="<->", color=FG, lw=1.2,
                                shrinkA=0, shrinkB=0, mutation_scale=12))
    ax.annotate(title, xy=(B / 2, -1.25), color=FG, fontsize=15,
                ha="center", va="top")

    ax.set_xlim(-0.4, view_max + 0.4)
    ax.set_ylim(-2.1, view_max + 0.4)
    ax.set_aspect("equal")
    ax.axis("off")


def main():
    with open(OUT / "packing_solution.json") as f:
        data = json.load(f)
    sides = data["sides"]
    s_list = [side / 2 for side in sides]
    B_star = data["B_star"]
    centers_mip = data["centers"]
    n = len(s_list)

    s_max = max(s_list)
    B_lp = 2 * s_max
    centers_lp = [(s_max, s_max)] * n

    best = search_branches(sides, centers_mip)
    print("best branches (i, j, dir):")
    for b in best["branches"]:
        print(f"  {b}")
    print(f"  B_lp        = {best['B_lp']:.3f}")
    print(f"  overlap     = {best['overlap']:.3f}")
    print(f"  score       = {best['score']:.3f}")
    print(f"  base LP     = {B_lp:.3f}")
    print(f"  MIP optimum = {B_star:.3f}")

    colors = cm.viridis(np.linspace(0.08, 0.95, n))
    branched_squares = {i for (i, j, _) in best["branches"]} | \
                       {j for (i, j, _) in best["branches"]}

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 6.0))
    view_max = max(B_star, B_lp, best["B_lp"])

    draw_panel(axes[0], B=B_lp, centers=centers_lp, s_list=s_list,
               colors=colors,
               title=rf"Base LP:  $B^{{\rm LP}} = {B_lp:.1f}$",
               view_max=view_max)
    draw_panel(axes[1], B=best["B_lp"], centers=best["centers"], s_list=s_list,
               colors=colors,
               title=rf"LP after 5 branches:  $B = {best['B_lp']:.2f}$",
               view_max=view_max,
               highlight=branched_squares)
    draw_panel(axes[2], B=B_star, centers=centers_mip, s_list=s_list,
               colors=colors,
               title=rf"MIP optimum:  $B \approx {B_star:.2f}$",
               view_max=view_max)

    fig.tight_layout()
    out = OUT / "packing_lp_branched.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", transparent=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
