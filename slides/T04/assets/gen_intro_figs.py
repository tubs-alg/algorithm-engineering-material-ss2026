"""Generate the three label-free "base problem" icons for the T04 intro slide.

What this file contains
-----------------------
One clean, unlabeled representation per family for the "Three families today"
overview (_00-intro.qmd): a job-shop Gantt, a rostering grid, and a VRP route
map. Each is the *recognizable shape* of the problem with all text stripped
(no title, legend, axis ticks, cell codes, or node labels) so they read as
icons at small column width. Non-goal: these are not solver outputs and not the
labeled section figures (those live in gen_jsp/rostering/vrp_figs.py).

Why it exists
-------------
The intro previously used AI-rendered "symbol" photos (symbol_assembly_line,
symbol_shift_planning, symbol_logistics). Those are decorative, not the actual
problems. This pack replaces them with the genuine base-problem visuals — the
same Gantt / grid / route-map vocabulary the three sections then build on — so
the overview previews what is coming instead of a mood image.

How to run
----------
    conda run -n mo312 python gen_intro_figs.py
    # writes intro_jsp.png, intro_roster.png, intro_vrp.png (transparent, dark style)

When it should change
---------------------
Retune an icon if a family's canonical look changes, or if the intro adds /
drops a family. Keep every icon textless and in the shared _dark_style palette
so the three rhyme visually.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

import _dark_style

OUT = Path(__file__).parent

# One palette shared with the section generators (job / route colors).
PALETTE = ["#4C78A8", "#F58518", "#54A24B", "#E45756",
           "#72B7B2", "#EECA3B", "#B279A2", "#9D755D"]
# Shift colors, matching gen_rostering_figs.SHIFTS (M / A / N / off).
SHIFT_COLORS = {"M": "#7FB3D5", "A": "#F4A261", "N": "#5D4E8C", "-": "#2a2a2a"}

_dark_style.apply()
EDGE = "#888888"
ICON_SIZE = (4.4, 3.1)   # one figsize for all three so the columns align


def _bare(ax):
    """Strip an axes down to its drawn content: no ticks, labels, or spines."""
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# ---------------------------------------------------------------------------
# Shop scheduling — a job-shop Gantt (colored job blocks across machines)
# ---------------------------------------------------------------------------
def fig_jsp():
    # The basic 3x3 job-shop schedule from gen_jsp_figs.fig_basic_jsp, stripped.
    sched = [
        (0, 0, 3, 0), (1, 3, 2, 0), (2, 5, 2, 0),    # Job 1
        (1, 0, 2, 1), (2, 4, 1, 1), (0, 5, 4, 1),    # Job 2
        (2, 0, 4, 2), (0, 9, 3, 2), (1, 12, 3, 2),   # Job 3
    ]
    fig, ax = plt.subplots(figsize=ICON_SIZE)
    for m in range(3):
        ax.axhline(m, color="#555555", linewidth=0.8, zorder=0)
    for m_idx, start, dur, job in sched:
        ax.barh(m_idx, dur, left=start, height=0.62,
                color=PALETTE[job], edgecolor=EDGE, linewidth=0.8, zorder=2)
    ax.set_xlim(0, 16)
    ax.set_ylim(2.7, -0.7)   # inverted, with margin
    _bare(ax)
    fig.savefig(OUT / "intro_jsp.png", transparent=True, bbox_inches="tight",
                pad_inches=0.04)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Employee rostering — a shift grid (colored cells, no codes)
# ---------------------------------------------------------------------------
def fig_roster():
    # 5 employees x 7 days, a balanced M/A/N/off mix so each column is covered.
    roster = [
        list("MMM--AN"),
        list("AAN-NM-"),
        list("N-MMA-A"),
        list("--ANNM N".replace(" ", "")),
        list("-N-MA-M"),
    ]
    n_emp = len(roster)
    n_days = len(roster[0])
    fig, ax = plt.subplots(figsize=ICON_SIZE)
    for r in range(n_emp):
        for c in range(n_days):
            ax.add_patch(plt.Rectangle((c, n_emp - 1 - r), 1, 1,
                                       facecolor=SHIFT_COLORS[roster[r][c]],
                                       edgecolor=EDGE, linewidth=0.8))
    ax.set_xlim(0, n_days)
    ax.set_ylim(0, n_emp)
    ax.set_aspect("equal")
    _bare(ax)
    fig.savefig(OUT / "intro_roster.png", transparent=True, bbox_inches="tight",
                pad_inches=0.04)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Vehicle routing — one depot, two routes over clients
# ---------------------------------------------------------------------------
def fig_vrp():
    # The core-VRP layout from gen_vrp_figs.fig_core_vrp, stripped of labels.
    depot = (5, 4)
    A = [(2.0, 6.5), (1.0, 4.5), (2.2, 2.5)]
    B = [(8.0, 6.8), (9.5, 5.0), (8.8, 2.5), (6.5, 1.8)]
    fig, ax = plt.subplots(figsize=ICON_SIZE)

    def route(coords, color):
        for (x1, y1), (x2, y2) in zip(coords[:-1], coords[1:]):
            ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=2.2,
                                        shrinkA=9, shrinkB=11), zorder=3)

    route([depot] + A + [depot], PALETTE[0])
    route([depot] + B + [depot], PALETTE[1])
    for x, y in A + B:
        ax.add_patch(plt.Circle((x, y), 0.30, facecolor="white",
                                edgecolor=EDGE, linewidth=1.2, zorder=4))
    ax.add_patch(plt.Rectangle((depot[0] - 0.35, depot[1] - 0.35), 0.7, 0.7,
                               facecolor="#dddddd", edgecolor=EDGE,
                               linewidth=1.0, zorder=5))
    ax.set_xlim(-0.2, 11)
    ax.set_ylim(0.5, 8)
    ax.set_aspect("equal")
    _bare(ax)
    fig.savefig(OUT / "intro_vrp.png", transparent=True, bbox_inches="tight",
                pad_inches=0.04)
    plt.close(fig)


def main():
    for f in (fig_jsp, fig_roster, fig_vrp):
        f()
        print(f"  ✓ {f.__name__}")


if __name__ == "__main__":
    main()
