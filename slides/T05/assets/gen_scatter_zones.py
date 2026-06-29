"""Generate the scatter + performance-zones panel for `_02-benchmarking-visualization.qmd`.

What this contains (and non-goals)
-----------------------------------
A single PNG/SVG, `scatter_zones.png`: one point per instance, baseline runtime on
x and the prototype's runtime on y. The diagonal is parity; the half-plane below it
is "prototype faster" (green), above it is "prototype slower" (red). A thin vertical
line drops from the diagonal to each point -- the honest read is the *vertical* gap
`y - x`, not the perpendicular distance to the line. NON-goals: this is an
illustrative figure with synthetic-but-plausible runtimes, not a real benchmark.

Faithful to the primer
-----------------------
Mirrors `plot_performance_scatter` from the cpsat-primer benchmarking chapter
(linear axes, full improve/decline half-plane fill, diagonal connector lines), in
the course dark theme so it matches the rest of the deck.

How to use it
-------------
    python gen_scatter_zones.py
writes `scatter_zones.png` (+ `.svg`) next to this script.

When it should change
---------------------
Adjust `N_INSTANCES` or the runtime model if the pedagogy shifts. Keep the cloud
mostly on the "faster" side with a few clear regressions -- that asymmetry is the
teaching point (a real change wins on most instances but loses on some).
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
C_PARITY = "#e6e6e6"    # parity diagonal (light, like a "no change" line)
C_WIN = "#7fbf7b"       # "prototype faster" zone / connectors (green)
C_LOSS = "#e86f6f"      # "prototype slower" zone / connectors (red)
C_POINT = "#9ad0f5"     # data points (blue)

N_INSTANCES = 70
SEED = 11


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
    # Baseline runtimes spread across the range (linear axes, like the primer).
    base = rng.uniform(8.0, 135.0, size=N_INSTANCES)
    # Prototype is usually faster (speedup > 1), but a minority regress.
    speedup = np.exp(rng.normal(0.30, 0.40, size=N_INSTANCES))
    new = base / speedup

    lo = 0.0
    hi = max(base.max(), new.max()) * 1.05

    fig, ax = plt.subplots(figsize=(8.6, 6.0))

    # Full improve/decline half-planes (lower_is_better): below diagonal = win.
    xs = np.array([lo, hi])
    ax.fill_between(xs, lo, xs, color=C_WIN, alpha=0.16, zorder=0)
    ax.fill_between(xs, xs, hi, color=C_LOSS, alpha=0.16, zorder=0)

    # Parity diagonal.
    ax.plot([lo, hi], [lo, hi], color=C_PARITY, linestyle="--", linewidth=1.4,
            zorder=1, alpha=0.8)

    # Connector lines from the diagonal to each point: read y - x, not distance.
    for x_val, y_val in zip(base, new):
        c = C_WIN if y_val < x_val else C_LOSS
        ax.plot([x_val, x_val], [x_val, y_val], color=c, linewidth=0.8,
                alpha=0.7, zorder=1)

    ax.scatter(base, new, marker="x", s=34, color=C_POINT, linewidths=1.4,
               zorder=3)

    ax.text(hi * 0.96, hi * 0.12, "prototype faster", color=C_WIN, fontsize=11,
            ha="right", va="bottom")
    ax.text(hi * 0.06, hi * 0.94, "prototype slower", color=C_LOSS, fontsize=11,
            ha="left", va="top")

    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    # NB: no equal aspect (the primer's plot_performance_scatter doesn't force it).
    # Equal xlim/ylim keep the diagonal a true parity line, corner to corner, while
    # a landscape box fills the slide column the way the bar plot does.
    ax.set_xlabel("baseline runtime (s)", color=C_FG, fontsize=12)
    ax.set_ylabel("prototype runtime (s)", color=C_FG, fontsize=12)
    ax.set_title("Scatter vs. baseline: below the line is faster",
                 color=C_FG, fontsize=14, pad=12)

    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.tick_params(colors=C_MUTED)
    ax.grid(True, which="both", color=C_GRID, linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)

    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT_DIR, f"scatter_zones.{ext}"),
                    bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    print("wrote scatter_zones.png / .svg")


if __name__ == "__main__":
    main()
