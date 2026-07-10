"""scenario_tree: one shared first-stage decision, scenario-specific recourse.

For `_07-stochastic.qmd`. Two-stage structure: choose x, observe the scenario,
then react with a scenario-specific y. The single x node is the visual anchor
for nonanticipativity. Run: python gen_scenario_tree.py
"""

import os

import _theme as T
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = os.path.dirname(os.path.abspath(__file__))


def box(ax, x, y, w, h, text, edge, fontsize=14):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.012,rounding_size=0.02",
                                lw=2, facecolor=T.NAVY, edgecolor=edge))
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, color=T.FG)


def main() -> None:
    T.init_style()
    fig, ax = plt.subplots(figsize=(9.4, 4.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box(ax, 0.12, 0.5, 0.17, 0.22, "commit $x$", T.BLUE)
    ax.text(0.12, 0.27, "first stage\n(here and now)", ha="center", va="top",
            fontsize=11.5, color=T.MUTED)

    leaves = [(0.80, 0.82, "low demand", "$y_{\\mathrm{low}}$", "$p_1 = 0.2$"),
              (0.80, 0.50, "normal demand", "$y_{\\mathrm{normal}}$", "$p_2 = 0.5$"),
              (0.80, 0.18, "high demand", "$y_{\\mathrm{high}}$", "$p_3 = 0.3$")]

    ax.scatter([0.44], [0.5], s=180, color=T.ORANGE, zorder=5)
    ax.text(0.44, 0.63, "observe $\\xi$", ha="center", fontsize=13, color=T.ORANGE)
    ax.add_patch(FancyArrowPatch((0.215, 0.5), (0.42, 0.5), arrowstyle="-|>",
                                 mutation_scale=18, lw=2, color=T.MUTED))

    for x, y, scen, dec, p in leaves:
        ax.add_patch(FancyArrowPatch((0.455, 0.5), (x - 0.115, y),
                                     arrowstyle="-|>", mutation_scale=16,
                                     lw=2, color=T.MUTED))
        box(ax, x, y, 0.20, 0.19, f"react {dec}", T.GREEN, fontsize=13)
        ax.text(x + 0.125, y, scen + "\n" + p, ha="left", va="center",
                fontsize=11.5, color=T.MUTED)

    ax.text(0.30, 0.86, "shared across\nall scenarios", ha="center", fontsize=11.5,
            color=T.BLUE)
    ax.add_patch(FancyArrowPatch((0.26, 0.78), (0.16, 0.63), arrowstyle="-|>",
                                 mutation_scale=13, lw=1.6, color=T.BLUE))

    T.save(fig, os.path.join(OUT, "scenario_tree"), pad=0.1)


if __name__ == "__main__":
    main()
