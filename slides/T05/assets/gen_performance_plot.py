"""Generate the two performance-profile panels for `_02-benchmarking-visualization.qmd`.

What this contains (and non-goals)
-----------------------------------
Two PNG/SVG panels in the course dark theme:
  performance_plot_objective.png -- performance profile on the objective (minimize)
  performance_plot_bound.png     -- performance profile on the lower bound (maximize)
A performance profile is the ECDF over instances of "within this factor of the
best": for each config, the fraction of instances whose metric is within factor x
of the best result on that instance. Higher/earlier is better; the curve that
climbs to 1.0 at the smallest x dominates. NON-goals: this is an illustrative
figure with synthetic-but-plausible step curves modeled on a TSP study (three
encodings: add_circuit, mtz, multiple_circuits); not a live benchmark.

Why it exists
-------------
`_02` needs a dark-theme performance plot that matches the rest of the deck.
The objective panel keeps a TIGHT x-range (ratios cluster just above 1.0), so the
discriminating region is not crushed against the left edge by a few outliers; the
bound panel needs a wider range because bound ratios spread much further.

How to use it
-------------
    python gen_performance_plot.py
writes performance_plot_objective.png/.svg and performance_plot_bound.png/.svg
next to this script.

When it should change
---------------------
Adjust the per-config breakpoints below if the pedagogy shifts. Keep one config
clearly dominating each panel (mtz on objective, add_circuit on the bound) and
keep the objective x-range tight -- that contrast is the teaching point.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- dark-theme palette (matches the course decks: transparent fig, light fg) ----
C_FG = "#e6e6e6"        # light foreground: titles, labels, ticks
C_MUTED = "#9aa6b5"     # secondary text / captions
C_GRID = "#3a4757"      # grid lines
C_BASELINE = "#ff8c42"  # x = 1 reference line (warm orange)

# One stable color per encoding, shared across both panels.
COLORS = {
    "add_circuit": "#9ad0f5",        # blue
    "mtz": "#ffd27f",                # warm gold (the highlight on the objective panel)
    "multiple_circuits": "#7fbf7b",  # green
}

# Step curves as (x, proportion) breakpoints, where="post".
# Objective: ratios sit just above 1.0; mtz dominates (reaches ~1.0 fastest).
OBJECTIVE = {
    "mtz": [(1.000, 0.85), (1.002, 0.93), (1.005, 0.96), (1.008, 1.00)],
    "multiple_circuits": [(1.000, 0.22), (1.004, 0.40), (1.008, 0.55),
                          (1.013, 0.70), (1.018, 0.82), (1.025, 0.88),
                          (1.035, 0.92), (1.046, 0.95)],
    "add_circuit": [(1.000, 0.10), (1.004, 0.18), (1.008, 0.32),
                    (1.013, 0.50), (1.018, 0.65), (1.023, 0.78),
                    (1.030, 0.88), (1.040, 0.92), (1.046, 0.95)],
}
OBJ_XMAX = 1.05

# Lower bound: ratios spread much wider; add_circuit dominates (proves best bound everywhere).
BOUND = {
    "add_circuit": [(1.00, 1.00)],
    "multiple_circuits": [(1.00, 0.00), (1.20, 0.05), (1.25, 0.30), (1.30, 0.55),
                          (1.40, 0.68), (1.50, 0.80), (1.58, 0.85), (1.72, 0.90),
                          (1.90, 0.95), (2.08, 1.00)],
    "mtz": [(1.00, 0.00), (1.23, 0.05), (1.28, 0.20), (1.35, 0.45), (1.42, 0.62),
            (1.50, 0.75), (1.60, 0.80), (1.78, 0.85), (1.98, 0.90), (2.10, 0.95),
            (2.20, 1.00)],
}
BOUND_XMAX = 2.3


def _draw(ax, curves, xmax, dominant, title):
    for name, pts in curves.items():
        xs = [p[0] for p in pts] + [xmax]
        ys = [p[1] for p in pts] + [pts[-1][1]]
        lw = 3.0 if name == dominant else 1.8
        alpha = 1.0 if name == dominant else 0.85
        ax.step(xs, ys, where="post", color=COLORS[name], linewidth=lw,
                alpha=alpha, label=name, solid_capstyle="round")

    ax.axvline(1.0, color=C_BASELINE, linestyle="--", linewidth=1.2, alpha=0.7)
    ax.set_xlim(1.0, xmax)
    ax.set_ylim(0.0, 1.03)
    ax.set_xlabel("within this factor of the best", color=C_FG, fontsize=12)
    ax.set_ylabel("proportion of instances", color=C_FG, fontsize=12)
    ax.set_title(title, color=C_FG, fontsize=14, pad=12)

    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.tick_params(colors=C_MUTED)
    ax.grid(True, which="both", color=C_GRID, linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)

    leg = ax.legend(loc="lower right", framealpha=0.0, fontsize=11, labelcolor=C_FG)
    leg.set_title(None)


def main() -> None:
    plt.rcParams.update({
        "savefig.dpi": 200,
        "savefig.transparent": True,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "font.family": "DejaVu Sans",
        "text.color": C_FG,
    })

    panels = [
        ("objective", OBJECTIVE, OBJ_XMAX, "mtz",
         "Performance profile: objective quality"),
        ("bound", BOUND, BOUND_XMAX, "add_circuit",
         "Performance profile: bound quality"),
    ]
    for key, curves, xmax, dominant, title in panels:
        fig, ax = plt.subplots(figsize=(7.4, 4.6))
        _draw(ax, curves, xmax, dominant, title)
        fig.tight_layout()
        for ext in ("png", "svg"):
            fig.savefig(os.path.join(OUT_DIR, f"performance_plot_{key}.{ext}"),
                        bbox_inches="tight", pad_inches=0.06)
        plt.close(fig)
    print("wrote performance_plot_objective.png/.svg and performance_plot_bound.png/.svg")


if __name__ == "__main__":
    main()
