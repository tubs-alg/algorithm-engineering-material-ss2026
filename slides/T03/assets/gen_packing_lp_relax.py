"""Generate the LP-relaxation gap figure for the Big-M section.

Produces `packing_lp_relax.png` — two side-by-side packings of the
same 20 mixed-size squares, drawn at the same visual scale. On the
left, the LP relaxation of the min-B Big-M model: every directional
binary splits 1/4 across L/R/A/B, each separation constraint relaxes
by 3/4 M, and the bounding box collapses to B^LP = 2 s_max with every
center forced to the same containment point. On the right, the best
MIP solution found by `solve_packing.py` — a real packing with B*
roughly 4.5 — for the same 20 squares.

Why this exists. With B turned into a decision variable and
minimized, the LP/MIP gap stops being abstract and becomes a number
on the slide. For this instance the LP halves the MIP bound; the
side-by-side picture makes the contrast immediate.

Reads `packing_solution.json` written by `solve_packing.py`. Re-run
the solver if you change the instance. Same dark-theme palette as
gen_packing_squares.py.

Usage. `python assets/gen_packing_lp_relax.py` from slides/.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import numpy as np

OUT = Path(__file__).parent

BG = "none"
FG = "#e0e0e0"

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


def draw_panel(ax, B, centers, s_list, colors, title, view_max):
    """Draw a B-by-B container with squares of half-side s_list at centers."""
    # Container outline drawn last (zorder=10) so it sits on top of squares.
    cont = patches.Rectangle((0, 0), B, B, linewidth=2.0, edgecolor=FG,
                             facecolor="none", zorder=10)
    ax.add_patch(cont)

    # Draw squares largest first so smaller ones layer visibly on top.
    order = np.argsort(s_list)[::-1]
    for rank, idx in enumerate(order):
        cx, cy = centers[idx]
        s = s_list[idx]
        sq = patches.Rectangle((cx - s, cy - s), 2 * s, 2 * s, linewidth=0.7,
                               edgecolor=colors[idx], facecolor=colors[idx],
                               alpha=0.55, zorder=2 + rank)
        ax.add_patch(sq)

    ax.annotate("", xy=(B, -0.6), xytext=(0, -0.6),
                arrowprops=dict(arrowstyle="<->", color=FG, lw=1.2,
                                shrinkA=0, shrinkB=0, mutation_scale=12))
    ax.annotate(title, xy=(B / 2, -1.25), color=FG, fontsize=16,
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

    # LP relaxation: with binaries split 1/4 each and M loose, every
    # separation constraint relaxes to a non-binding inequality.
    # Containment then drives the LP bound: B^LP = 2 * s_max, with
    # every center forced to (s_max, s_max).
    s_max = max(s_list)
    B_lp = 2 * s_max
    centers_lp = [(s_max, s_max)] * n

    colors = cm.viridis(np.linspace(0.08, 0.95, n))

    fig, (ax_lp, ax_mip) = plt.subplots(1, 2, figsize=(12.5, 6.8))

    # Shared scale so the LP box sits visibly small next to the MIP box.
    view_max = max(B_star, B_lp)

    draw_panel(ax_lp, B=B_lp, centers=centers_lp, s_list=s_list,
               colors=colors,
               title=rf"LP relaxation:  $B^{{\rm LP}} = {B_lp:.1f}$",
               view_max=view_max)
    draw_panel(ax_mip, B=B_star, centers=centers_mip, s_list=s_list,
               colors=colors,
               title=rf"MIP solution:  $B \approx {B_star:.2f}$",
               view_max=view_max)

    fig.tight_layout()
    out = OUT / "packing_lp_relax.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", transparent=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
