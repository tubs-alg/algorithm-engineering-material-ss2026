"""
Generate the cactus (survival) plot for `_02-benchmarking-visualization.qmd`.

What this contains (and non-goals)
-----------------------------------
A single PNG/SVG, `cactus_plot.png`: a cactus (a.k.a. survival) plot for three
solver configurations over one benchmark set with a fixed time limit. The x-axis
counts how many instances a configuration has solved; the y-axis is the per-instance
solve time, sorted ascending per config. A horizontal line marks the time limit;
runs that hit it are censored (never solved): they are capped at the limit, so the
curve steps up to the time-limit line and runs flat to the right edge.
NON-goals: this is an illustrative figure with synthetic-but-plausible runtimes,
not a real benchmark; the point is the *shape* of the censored-data story, not
the specific numbers. (PAR-style penalized scalars are discussed in `_01`; we do
not overlay them on this figure.)

Why it exists
-------------
The primer has no cactus-plot image, and `_02` needs one to pay off the
"timeouts dominate, means lie" point from `_01`. A cactus plot is the standard
answer: it shows the whole runtime distribution and treats timeouts gracefully
(they just stop a curve).

How to use it
-------------
    python gen_cactus.py
writes `cactus_plot.png` (+ `.svg`) next to this script.

When it should change
---------------------
Adjust `N_INSTANCES`, `TIME_LIMIT_S`, or the per-config runtime models if the
pedagogy shifts. Keep at least one config visibly censored (a curve that flattens
onto the time-limit line before N_INSTANCES) -- the censoring is the whole point.
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
C_LIMIT = "#ff8c42"     # time-limit line (warm orange)
CONFIG_COLORS = ["#9ad0f5", "#7fbf7b", "#c792ea"]  # blue / green / violet

N_INSTANCES = 80
TIME_LIMIT_S = 60.0
SEED = 7


def _runtimes(rng: np.random.Generator, median: float, sigma: float) -> np.ndarray:
    """Lognormal per-instance runtimes; anything over the limit is censored."""
    t = rng.lognormal(mean=np.log(median), sigma=sigma, size=N_INSTANCES)
    return t


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
    # Three configs that tell a story the *mean* runtime would hide:
    #  - baseline: fast on easy instances but a long censored tail (many timeouts)
    #  - tuned: slightly slower start, far fewer timeouts -> wins the cactus race
    #  - alt model: steady middle, moderate tail
    configs = [
        ("baseline", _runtimes(rng, median=4.0, sigma=1.55)),
        ("tuned", _runtimes(rng, median=6.0, sigma=0.95)),
        ("alt model", _runtimes(rng, median=9.0, sigma=1.10)),
    ]

    fig, ax = plt.subplots(figsize=(8.6, 6.0))

    for (label, times), color in zip(configs, CONFIG_COLORS):
        n_solved = int(np.sum(times <= TIME_LIMIT_S))
        # all instances, sorted; censored runs are capped at the limit so the
        # curve steps up to the time-limit line and continues to the right edge.
        capped = np.sort(np.minimum(times, TIME_LIMIT_S))
        xs = np.arange(1, N_INSTANCES + 1)
        ax.step(xs, capped, where="post", color=color, linewidth=2.4,
                label=f"{label}  ({n_solved}/{N_INSTANCES})")
        # markers only on the genuinely solved instances
        ax.scatter(xs[:n_solved], capped[:n_solved], s=10, color=color,
                   alpha=0.55, zorder=3)

    ax.axhline(TIME_LIMIT_S, color=C_LIMIT, linewidth=1.6, linestyle="--")
    ax.text(N_INSTANCES - 1, TIME_LIMIT_S * 1.03,
            "time limit (timeouts censored above)",
            color=C_LIMIT, fontsize=10, va="bottom", ha="right")

    ax.set_xlabel("# instances solved (sorted by difficulty per config)",
                  color=C_FG, fontsize=12)
    ax.set_ylabel("solve time (s, log scale)", color=C_FG, fontsize=12)
    ax.set_yscale("log")
    ax.set_xlim(0, N_INSTANCES)
    ax.set_ylim(0.4, TIME_LIMIT_S * 1.8)

    ax.set_title("Cactus plot: further right / lower is better",
                 color=C_FG, fontsize=14, pad=12)

    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.tick_params(colors=C_MUTED)
    ax.grid(True, which="both", color=C_GRID, linewidth=0.5, alpha=0.5)

    leg = ax.legend(loc="upper left", framealpha=0.0, fontsize=11,
                    labelcolor=C_FG)
    leg.set_title(None)

    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT_DIR, f"cactus_plot.{ext}"),
                    bbox_inches="tight", pad_inches=0.06)
    print("wrote cactus_plot.png / .svg")


if __name__ == "__main__":
    main()
