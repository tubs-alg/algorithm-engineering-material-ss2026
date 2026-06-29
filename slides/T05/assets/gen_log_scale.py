"""
Generate the linear-vs-log scatter figure for `_02-benchmarking-visualization.qmd`.

What this contains (and non-goals)
-----------------------------------
A single PNG/SVG, `log_scale_linear_vs_log.png`: ONE scatter dataset drawn twice,
linear (left) and log (right). One point per instance: baseline runtime on x, a
candidate config's runtime on y, with a parity (y = x) diagonal. The set is
realistic in that it has MANY small/fast instances and only a FEW slow ones.

The figure makes a single trade-off visible without prose:
  - LINEAR: the few big/slow instances are easy to read and absolute differences
    are honest, but the dense cluster of fast instances collapses into the corner
    and individual points there are indistinguishable.
  - LOG: the fast cluster fans out so every point is distinguishable across all
    scales (you can read the parity relationship for small AND large instances),
    at the cost of absolute magnitude -- the big outliers no longer look big.

NON-goals: not a real benchmark; synthetic-but-plausible lognormal runtimes. The
point is the perceptual trade-off the scale introduces, not the numbers.

Why it exists
-------------
The cactus and performance plots default to a log y-axis. This slide pays off the
trade-off behind that default: log buys distinguishability of a crowded small-end
at the cost of absolute magnitude; linear does the reverse.

How to use it
-------------
    python gen_log_scale.py
writes `log_scale_linear_vs_log.png` (+ `.svg`) next to this script.

When it should change
---------------------
Keep the runtime distribution heavy-tailed (many fast instances, a few slow ones)
so the linear panel crowds the cluster and the log panel spreads it. That skew is
the whole point.
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
C_PARITY = "#9aa6b5"    # parity (y = x) diagonal
C_PT = "#9ad0f5"        # data points
C_BAD = "#e74c3c"       # "bad" outliers: large regressions (candidate >> baseline)

N = 140
SEED = 7


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
    # heavy-tailed instance difficulty: most instances are fast, a few are slow.
    base = rng.lognormal(mean=np.log(0.28), sigma=1.55, size=N)
    # The candidate is a systematic WIN on the bulk: on average ~30% faster, so the
    # cluster sits clearly below the parity line.
    cand = base * rng.lognormal(mean=np.log(0.7), sigma=0.28, size=N)

    # ...but it has a few catastrophic regressions on hard instances (tens of
    # seconds), well above parity. This one-sided story is the interesting one: on
    # the linear axis these red points dominate and the consistent speedup of the
    # whole cluster is invisible; on log you can see BOTH the systematic win and
    # the regressions at once.
    out_base = np.array([18.0, 30.0, 9.0])
    out_cand = np.array([48.0, 75.0, 30.0])  # all ~2.5-3x slower: bad regressions
    out_bad = np.array([True, True, True])
    base = np.concatenate([base, out_base])
    cand = np.concatenate([cand, out_cand])

    # Highlight only the planted bad outliers (slow instances where the candidate
    # is markedly worse than the baseline) red in both panels.
    bad = np.concatenate([np.zeros(N, dtype=bool), out_bad])
    good = ~bad

    lo = min(base.min(), cand.min()) * 0.7
    hi = max(base.max(), cand.max()) * 1.3
    diag = np.array([max(lo, 1e-3), hi])

    fig, (ax_lin, ax_log) = plt.subplots(1, 2, figsize=(12.4, 5.8))

    for ax in (ax_lin, ax_log):
        ax.plot(diag, diag, color=C_PARITY, linewidth=1.4, linestyle="--",
                zorder=2, label="parity (y = x)")
        ax.scatter(base[good], cand[good], s=22, color=C_PT, alpha=0.7,
                   edgecolor="none", zorder=3)
        ax.scatter(base[bad], cand[bad], s=46, color=C_BAD, alpha=0.95,
                   edgecolor="none", zorder=4, label="bad outlier (regression)")
        ax.set_xlabel("baseline runtime (s)", color=C_FG, fontsize=12)
        for spine in ax.spines.values():
            spine.set_color(C_GRID)
        ax.tick_params(colors=C_MUTED)
        ax.grid(True, which="major", color=C_GRID, linewidth=0.5, alpha=0.5)
        ax.set_aspect("equal", adjustable="box")

    ax_lin.set_ylabel("candidate runtime (s)", color=C_FG, fontsize=12)
    ax_lin.set_xlim(0, hi)
    ax_lin.set_ylim(0, hi)
    ax_lin.set_title("linear scale", color=C_FG, fontsize=14, pad=10)

    ax_log.set_xscale("log")
    ax_log.set_yscale("log")
    ax_log.set_xlim(lo, hi)
    ax_log.set_ylim(lo, hi)
    ax_log.set_title("log scale", color=C_FG, fontsize=14, pad=10)

    ax_lin.legend(loc="upper left", framealpha=0.0, fontsize=10, labelcolor=C_FG)

    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT_DIR, f"log_scale_linear_vs_log.{ext}"),
                    bbox_inches="tight", pad_inches=0.06)
    print("wrote log_scale_linear_vs_log.png / .svg")


if __name__ == "__main__":
    main()
