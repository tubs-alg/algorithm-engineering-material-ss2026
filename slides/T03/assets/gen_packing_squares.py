"""Generate the packing-squares illustration for the LP-preserving section.

Produces `packing_squares.png` — a container of side B with two axis-aligned
squares, labeled with center variables (x_i, y_i) and half-side parameters
s_i. Used on the naive-linearization slide so the reader can match each LP
symbol to a geometric quantity before reading the constraints.

Why this exists. The wish max(|x_i - x_j|, |y_i - y_j|) >= s_i + s_j reads
better with the picture next to it: centers as decision variables, half-sides
as parameters, container side as the only structural constant. The figure
also primes the next slide's collapse — two unit squares the LP cheerfully
stacks on top of each other.

Palette matches gen_pwla.py and gen_l1_regression.py: dark transparent
background, light foreground, blue + green squares, orange dimension arrows.

Usage. `python assets/gen_packing_squares.py` from slides/.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

OUT = Path(__file__).parent

BG = "none"
FG = "#e0e0e0"
SQ1 = "#9ad0f5"          # square 1 (light blue)
SQ2 = "#7fbf7b"          # square 2 (green)
DIM = "#e69138"          # half-side arrows (orange)
GUIDE = "#c27ba0"        # center-distance guides (mauve)

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
    B = 10.0
    s1, s2 = 1.6, 1.1
    x1, y1 = 2.8, 7.2
    x2, y2 = 7.0, 3.0

    fig, ax = plt.subplots(figsize=(6.2, 6.6))

    # Container box
    cont = patches.Rectangle((0, 0), B, B, linewidth=2.0, edgecolor=FG,
                             facecolor="none", zorder=1)
    ax.add_patch(cont)

    # Squares (filled with low alpha so labels stay readable)
    sq1 = patches.Rectangle((x1 - s1, y1 - s1), 2 * s1, 2 * s1, linewidth=1.8,
                            edgecolor=SQ1, facecolor=SQ1, alpha=0.28, zorder=2)
    ax.add_patch(sq1)
    sq2 = patches.Rectangle((x2 - s2, y2 - s2), 2 * s2, 2 * s2, linewidth=1.8,
                            edgecolor=SQ2, facecolor=SQ2, alpha=0.28, zorder=2)
    ax.add_patch(sq2)

    # Center dots
    ax.plot([x1], [y1], 'o', color=FG, markersize=5, zorder=6)
    ax.plot([x2], [y2], 'o', color=FG, markersize=5, zorder=6)

    # Center labels — placed directly beneath the center dot. The squares are
    # filled with low alpha so the label remains legible over the interior.
    ax.annotate(r"$(x_1, y_1)$", xy=(x1, y1 - 0.4),
                color=FG, fontsize=14, ha="center", va="top")
    ax.annotate(r"$(x_2, y_2)$", xy=(x2, y2 - 0.4),
                color=FG, fontsize=14, ha="center", va="top")

    # Half-side arrow on square 1: center -> top edge (vertical), label to
    # the right of the arrow's midpoint.
    ax.annotate("", xy=(x1, y1 + s1), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=DIM, lw=1.6,
                                shrinkA=2, shrinkB=0, mutation_scale=12))
    ax.annotate(r"$s_1$", xy=(x1 + 0.22, y1 + s1 / 2), color=DIM,
                fontsize=14, ha="left", va="center")

    # Half-side arrow on square 2: center -> right edge (horizontal), label
    # above the arrow's midpoint.
    ax.annotate("", xy=(x2 + s2, y2), xytext=(x2, y2),
                arrowprops=dict(arrowstyle="-|>", color=DIM, lw=1.6,
                                shrinkA=2, shrinkB=0, mutation_scale=12))
    ax.annotate(r"$s_2$", xy=(x2 + s2 / 2, y2 + 0.22), color=DIM,
                fontsize=14, ha="center", va="bottom")

    # Center-distance guides — dashed lines projecting each center onto the
    # opposite center's row/column, with the L-infinity gap labeled.
    ax.plot([x1, x2], [y1, y1], linestyle=(0, (4, 3)), color=GUIDE,
            linewidth=1.0, alpha=0.7, zorder=3)
    ax.plot([x2, x2], [y1, y2], linestyle=(0, (4, 3)), color=GUIDE,
            linewidth=1.0, alpha=0.7, zorder=3)
    ax.annotate(r"$|x_1 - x_2|$", xy=((x1 + x2) / 2 + 0.6, y1 + 0.1),
                color=GUIDE, fontsize=12, ha="center", va="bottom")
    ax.annotate(r"$|y_1 - y_2|$", xy=(x2 + 0.15, (y1 + y2) / 2),
                color=GUIDE, fontsize=12, ha="left", va="center")

    # Container side label B — dimension arrow underneath
    ax.annotate("", xy=(B, -0.55), xytext=(0, -0.55),
                arrowprops=dict(arrowstyle="<->", color=FG, lw=1.2,
                                shrinkA=0, shrinkB=0, mutation_scale=12))
    ax.annotate(r"$B$", xy=(B / 2, -1.05), color=FG, fontsize=14,
                ha="center", va="top")

    # Containment + non-overlap wish — placed above the container as a
    # two-line header so the diagram is self-contained.
    ax.annotate(
        r"$s_i \;\leq\; x_i,\ y_i \;\leq\; B - s_i$",
        xy=(B / 2, B + 1.7), color=FG, fontsize=15,
        ha="center", va="center",
    )
    ax.annotate(
        r"$\max\,(\,|x_i - x_j|,\ |y_i - y_j|\,) \;\geq\; s_i + s_j$",
        xy=(B / 2, B + 0.7), color=FG, fontsize=15,
        ha="center", va="center",
    )

    ax.set_xlim(-0.4, B + 0.4)
    ax.set_ylim(-1.6, B + 2.5)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.tight_layout()
    out = OUT / "packing_squares.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", transparent=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
