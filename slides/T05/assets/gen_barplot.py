"""
Generate the grouped bar plot for `_02-benchmarking-visualization.qmd`.

What this contains (and non-goals)
-----------------------------------
A single PNG/SVG, `barplot.png`: a grouped bar chart of median solve time per
instance class (n = 50/100/200/400), with two solver configurations (baseline,
tuned) side by side and IQR whiskers. NON-goals: this is an illustrative figure
with synthetic-but-plausible numbers, not a real benchmark. The point is the
*shape* of the comparison a bar plot is good at: a few discrete categories, an
aggregate per category, read at a glance.

Why it exists
-------------
`_02` walks through one plot per benchmarking question. Bar plots are the most
familiar aggregate view and genuinely useful when every run finishes and the
data splits into a handful of categories (instance classes, or solvers). They
also make a teaching point: a bar shows one aggregate and hides the distribution,
so they pair with a scatter/cactus rather than replace them.

How to use it
-------------
    python gen_barplot.py
writes `barplot.png` (+ `.svg`) next to this script.

When it should change
---------------------
Adjust `CLASSES` or the per-class medians/IQRs if the pedagogy shifts. Keep the
"tuned scales better on the large class" story visible -- that is what makes the
grouped comparison worth a bar plot.
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
CONFIG_COLORS = ["#9ad0f5", "#7fbf7b"]  # blue / green

CLASSES = ["n=50", "n=100", "n=200", "n=400"]

# (label, color, per-class median runtime [s], per-class IQR half-width [s])
CONFIGS = [
    ("baseline", CONFIG_COLORS[0], [0.9, 3.4, 12.0, 41.0], [0.3, 1.2, 4.5, 14.0]),
    ("tuned", CONFIG_COLORS[1], [1.1, 3.0, 8.5, 22.0], [0.3, 0.9, 2.6, 6.5]),
]


def main() -> None:
    plt.rcParams.update({
        "savefig.dpi": 200,
        "savefig.transparent": True,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "font.family": "DejaVu Sans",
        "text.color": C_FG,
    })

    fig, ax = plt.subplots(figsize=(8.6, 6.0))

    x = np.arange(len(CLASSES))
    n_cfg = len(CONFIGS)
    width = 0.8 / n_cfg

    for i, (label, color, medians, iqr) in enumerate(CONFIGS):
        offset = (i - (n_cfg - 1) / 2) * width
        ax.bar(x + offset, medians, width=width * 0.92, color=color,
               label=label, zorder=2,
               yerr=iqr, capsize=4,
               error_kw=dict(ecolor=C_MUTED, elinewidth=1.2, capthick=1.2))

    ax.set_xticks(x)
    ax.set_xticklabels(CLASSES, color=C_FG, fontsize=12)
    ax.set_xlabel("instance class", color=C_FG, fontsize=12)
    ax.set_ylabel("median solve time (s)", color=C_FG, fontsize=12)
    ax.set_title("Bar plot: median runtime per instance class (IQR whiskers)",
                 color=C_FG, fontsize=14, pad=12)

    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.tick_params(colors=C_MUTED)
    ax.grid(True, axis="y", color=C_GRID, linewidth=0.5, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)

    leg = ax.legend(loc="upper left", framealpha=0.0, fontsize=11,
                    labelcolor=C_FG)
    leg.set_title(None)

    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT_DIR, f"barplot.{ext}"),
                    bbox_inches="tight", pad_inches=0.06)
    print("wrote barplot.png / .svg")


if __name__ == "__main__":
    main()
