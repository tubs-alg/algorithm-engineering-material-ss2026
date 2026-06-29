"""Generate the split plot (scalability of a single model) for `_02-benchmarking-visualization.qmd`.

What this contains (and non-goals)
-----------------------------------
A single PNG/SVG, `split_plot.png`, with ONE axis and a transformed y, exactly like
the primer's split plot:
  below the divider -- solved instances: per-instance solve time (s);
  above the divider -- unsolved instances: the optimality gap [ratio] left when the
                       time limit was hit.
x is the instance size. A dashed divider marks the time limit / zero-gap boundary.
NON-goals: this is an illustrative figure with synthetic-but-plausible numbers, not
a real benchmark; the point is the *shape* -- a model solves cleanly up to some
size, then falls off a cliff and only the gap is left to report.

Faithful to the primer
-----------------------
Reproduces the single-axis, transformed-y layout of the cpsat-primer split plot
(runtime in the lower region, optimality gap in the upper region, divided by the
time-limit line), in the course dark theme so it matches the rest of the deck.

How to use it
-------------
    python gen_split_plot.py
writes `split_plot.png` (+ `.svg`) next to this script.

When it should change
---------------------
Adjust `MAX_SIZE`, `CLIFF`, or the runtime/gap models if the pedagogy shifts. Keep a
clear cliff -- solved cleanly to one side, only gaps to the other -- that transition
is the teaching point.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- dark-theme palette (matches the course decks: transparent fig, light fg) ----
C_FG = "#e6e6e6"        # light foreground: titles, labels, ticks
C_MUTED = "#9aa6b5"     # secondary text / captions
C_GRID = "#3a4757"      # grid lines
C_DIV = "#ff8c42"       # time-limit / zero-gap divider (warm orange)
C_SOLVED = "#9ad0f5"    # solved instances -> runtime (blue)
C_GAP = "#ffb454"       # unsolved instances -> optimality gap (amber)

MAX_SIZE = 30
CLIFF = 20              # instances stop solving reliably beyond this size
N_PER_SIZE = 5
TIME_LIMIT_S = 300.0
SEED = 23

# Axis transform: time region [0, TIME_LIMIT] -> [0, DIV]; gap region [0, 1] -> [DIV, 1].
DIV = 0.56              # divider position in axis fraction (time region is taller)
GAP_SPAN = 1.0 - DIV


def main() -> None:
    plt.rcParams.update({
        "savefig.dpi": 200,
        "savefig.transparent": True,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "font.family": "DejaVu Sans",
        "text.color": C_FG,
    })

    rng = np.random.default_rng(SEED)

    solved_x, solved_t = [], []
    gap_x, gap_g = [], []
    for size in range(1, MAX_SIZE + 1):
        for _ in range(N_PER_SIZE):
            p_solve = 1.0 / (1.0 + np.exp((size - CLIFF) * 0.9))
            if rng.random() < p_solve:
                t = 0.6 * np.exp(0.30 * size) * np.exp(rng.normal(0, 0.30))
                t = min(t, TIME_LIMIT_S)
                solved_x.append(size)
                solved_t.append(t)
            else:
                g = (0.03 + 0.018 * (size - CLIFF)) * np.exp(rng.normal(0, 0.28))
                gap_x.append(size)
                gap_g.append(float(np.clip(g, 0.01, 1.0)))

    # Map data onto the single transformed axis (0..1).
    solved_y = [t / TIME_LIMIT_S * DIV for t in solved_t]
    gap_y = [DIV + g * GAP_SPAN for g in gap_g]

    fig, ax = plt.subplots(figsize=(8.4, 6.2))

    ax.scatter(solved_x, solved_y, s=28, color=C_SOLVED, alpha=0.8,
               edgecolors="none", zorder=3)
    ax.scatter(gap_x, gap_y, s=28, color=C_GAP, alpha=0.85,
               edgecolors="none", zorder=3)

    # Divider: time limit below, zero gap above.
    ax.axhline(DIV, color=C_DIV, linestyle="--", linewidth=1.5, alpha=0.9)
    ax.axvline(CLIFF, color=C_DIV, linestyle=":", linewidth=1.2, alpha=0.6)

    # Custom y-ticks: runtime in the lower region, gap [ratio] in the upper region.
    time_ticks = [0, 100, 200, 300]
    gap_ticks = [0.0, 1 / 3, 2 / 3, 1.0]
    yticks = [t / TIME_LIMIT_S * DIV for t in time_ticks] + \
             [DIV + g * GAP_SPAN for g in gap_ticks]
    ylabels = [str(t) for t in time_ticks] + \
              ["0", "0.333", "0.667", "1"]
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)

    ax.set_xlim(0, MAX_SIZE + 1)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("instance size", color=C_FG, fontsize=12)
    ax.set_ylabel("time [s]   /   opt. gap [ratio]", color=C_FG, fontsize=12)
    ax.set_title("Split plot: runtime below the limit, gap above it",
                 color=C_FG, fontsize=14, pad=12)

    ax.text(MAX_SIZE + 0.6, DIV + GAP_SPAN * 0.5, "unsolved\n(gap)",
            color=C_GAP, fontsize=10, ha="right", va="center")
    ax.text(MAX_SIZE + 0.6, DIV * 0.45, "solved\n(runtime)",
            color=C_SOLVED, fontsize=10, ha="right", va="center")

    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.tick_params(colors=C_MUTED)
    ax.grid(True, axis="x", color=C_GRID, linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)

    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT_DIR, f"split_plot.{ext}"),
                    bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    print("wrote split_plot.png / .svg")


if __name__ == "__main__":
    main()
