"""Generate a simple ReLU plot for the activation-patterns section.

Produces `relu.png` — the curve $y = \\max(0, x)$ on a bounded domain
$[L, U]$ with $L < 0 < U$. The two linear branches are coloured
distinctly so the slide can talk about the off-branch (b = 0) and the
identity-branch (b = 1) without ambiguity. Bound markers L and U are
labelled at the domain endpoints.

Why this exists. The ReLU slide poses an A/B/C puzzle about the
correct bounded MIP formulation. A small picture next to the candidate
list makes the two-branch structure visible — the kink at zero and
the finite domain that the encoding needs.

Palette matches the other slide plots in this deck (dark theme, soft
foreground grey).

Usage. `python assets/gen_relu.py` from the slides/ directory.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).parent

BG = "none"
FG = "#e0e0e0"
OFF = "#7a8a99"         # off branch y = 0
IDENT = "#7fbf7b"       # identity branch y = x
BOUND = "#e69138"       # L and U markers
GRID = "#37474f"

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


def main():
    L, U = -2.0, 3.0
    x_off = np.linspace(L, 0, 50)
    x_on = np.linspace(0, U, 50)

    fig, ax = plt.subplots(figsize=(5.4, 3.6))

    ax.plot(x_off, np.zeros_like(x_off), color=OFF, lw=3.0,
            label=r"$y = 0$  ($x \leq 0$)")
    ax.plot(x_on, x_on, color=IDENT, lw=3.0,
            label=r"$y = x$  ($x \geq 0$)")

    # Kink marker.
    ax.scatter([0], [0], s=40, color=FG, zorder=5)

    # Domain boundary markers.
    for xv, name in [(L, "L"), (U, "U")]:
        ax.axvline(xv, color=BOUND, lw=1.0, linestyle=":", alpha=0.7)
        ax.annotate(name, xy=(xv, -0.4), color=BOUND, fontsize=14,
                    ha="center", va="top")

    ax.axhline(0, color=GRID, lw=0.8)
    ax.axvline(0, color=GRID, lw=0.8)

    ax.set_xlim(L - 0.4, U + 0.4)
    ax.set_ylim(-0.8, U + 0.4)
    ax.set_xlabel("$x$")
    ax.set_ylabel("$y$")
    ax.set_aspect("equal")
    ax.legend(loc="upper left", frameon=False, fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(FG)
    ax.spines["bottom"].set_color(FG)

    fig.tight_layout()
    out = OUT / "relu.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", transparent=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
