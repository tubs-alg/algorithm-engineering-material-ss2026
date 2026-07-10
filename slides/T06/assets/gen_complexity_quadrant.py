"""Self-authored quadrant figure for the intro slide in T06.

What this file contains
    A 2x2 quadrant that frames when the coding patterns of this deck pay off.
    The x-axis runs from one-time use to continuous use; the y-axis from clear,
    fixed specifications to changing requirements. The four corners map to how
    much structure the code has to earn: a throwaway script in clear conditions
    needs almost none; a continuously used model under changing requirements
    needs the full toolkit (schemas, solver classes, indices, submodels, tests).
    A soft diagonal shading darkens toward the top-right to show that the cost
    of getting the structure wrong grows along both axes at once.

Why it exists
    The deck only ships figures it generated itself. Styled transparent with a
    light foreground to match the dark slide theme used across the course (same
    palette as gen_decomposition_fig.py / gen_debugging_figs.py).

How to use
    uv run --with matplotlib \\
        week12-t06-tdd/slides/assets/gen_complexity_quadrant.py
    Writes complexity_quadrant.png (+ .svg) into this directory.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = os.path.dirname(os.path.abspath(__file__))

INK = "#e6e6e6"
FADED = "#5b6472"
AXIS = "#9aa4b2"
LOW = "#7fbf7b"   # green: little structure needed
MID = "#e69138"   # orange: moderate
HIGH = "#e05a5a"  # red: the demanding corner

plt.rcParams.update(
    {
        "figure.dpi": 120,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.transparent": True,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "text.color": INK,
        "font.family": "DejaVu Sans",
        "svg.fonttype": "none",
    }
)


def save(fig, stem: str) -> None:
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT, f"{stem}.{ext}"))
    plt.close(fig)


# Geometry (data units), tuned so the whole picture fills a 16:9 slide. The axis
# cross sits at the origin; each quadrant card is centered at (+-CX, +-CY), wide
# and landscape so long titles fit on one line and a clean gutter stays open
# around the cross for the arrows and their end labels. Nothing overlaps.
CX = 1.62
CY = 1.0
CARD_W = 2.5
CARD_H = 1.5
AX_END_X = CX + CARD_W / 2 + 0.2  # x-arrow reaches just past the outer card edge
AX_END_Y = CY + CARD_H / 2 + 0.2


def card(ax, cx, cy, title, body, color):
    """A rounded quadrant card centered at (cx, cy)."""
    x0, y0 = cx - CARD_W / 2, cy - CARD_H / 2
    ax.add_patch(
        FancyBboxPatch(
            (x0, y0), CARD_W, CARD_H,
            boxstyle="round,pad=0.0,rounding_size=0.1",
            fc=color, ec=color, alpha=0.15, lw=0, zorder=2,
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (x0, y0), CARD_W, CARD_H,
            boxstyle="round,pad=0.0,rounding_size=0.1",
            fc="none", ec=color, alpha=0.9, lw=1.6, zorder=3,
        )
    )
    ax.text(cx, cy + 0.44, title, ha="center", va="center", fontsize=17,
            fontweight="bold", color=color, zorder=4)
    ax.text(cx, cy - 0.14, body, ha="center", va="center", fontsize=12.5,
            color=INK, zorder=4, linespacing=1.5)


def gen_quadrant():
    fig, ax = plt.subplots(figsize=(13.4, 7.54))  # 16:9

    # Bottom-left: one-time + clear specs -> minimal structure.
    card(ax, -CX, -CY, "A single function",
         "One pass, clear rules.\nStructure would be noise.", LOW)
    # Bottom-right: continuous + clear specs -> schemas, classes, tests.
    card(ax, CX, -CY, "Structured & tested",
         "Schemas, a solver class,\nregression tests.\nStable, but load-bearing.", MID)
    # Top-left: one-time + changing specs -> keep it malleable, cheap to redo.
    card(ax, -CX, CY, "Kept malleable",
         "Requirements move, but it\nis thrown away soon.\nFavor easy rewrites.", MID)
    # Top-right: continuous + changing -> the full toolkit.
    card(ax, CX, CY, "The full toolkit",
         "Schemas, classes, indices,\nsubmodels, tests.\nEvery pattern earns its keep.", HIGH)

    # Axes as arrows crossing at the origin, running through the open gutter.
    ax.annotate("", xy=(AX_END_X, 0), xytext=(-AX_END_X, 0),
                arrowprops=dict(arrowstyle="-|>", color=AXIS, lw=1.8))
    ax.annotate("", xy=(0, AX_END_Y), xytext=(0, -AX_END_Y),
                arrowprops=dict(arrowstyle="-|>", color=AXIS, lw=1.8))

    # Axis end labels, set outside the arrow tips.
    ax.text(-AX_END_X - 0.15, 0, "One-time\nuse", ha="right", va="center",
            fontsize=14, color=AXIS)
    ax.text(AX_END_X + 0.15, 0, "Continuous\nuse", ha="left", va="center",
            fontsize=14, color=AXIS)
    ax.text(0, -AX_END_Y - 0.16, "Clear specifications", ha="center", va="top",
            fontsize=14, color=AXIS)
    ax.text(0, AX_END_Y + 0.16, "Changing requirements", ha="center", va="bottom",
            fontsize=14, color=AXIS)

    ax.set_xlim(-AX_END_X - 1.05, AX_END_X + 1.05)
    ax.set_ylim(-AX_END_Y - 0.42, AX_END_Y + 0.42)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "complexity_quadrant")


if __name__ == "__main__":
    gen_quadrant()
    print("Wrote complexity_quadrant (PNG+SVG) to", OUT)
