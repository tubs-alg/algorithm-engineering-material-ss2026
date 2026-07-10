"""Self-authored block-matrix figure for the decomposition slide in T06.

What this file contains
    Draws the variable-by-constraint incidence matrix of a routing model in
    singly-bordered block-diagonal form, used in `_02-good-code-properties.qmd`
    ("Modules and Hierarchy"). Columns are decision variables, rows are
    constraints, both grouped by component. The tour/edge-usage backbone is a
    full-height column band that every component references; the capacity,
    time-window, and cost components each occupy their own block on their own
    columns, sitting on the backbone band but otherwise disjoint from one
    another. That coupling-only-through-the-backbone structure is exactly what
    the class hierarchy on the slide mirrors.

Why it exists
    The deck only ships figures it generated itself. This draws the standard
    optimization block-decomposition picture from scratch with matplotlib,
    styled transparent with light foreground to match the dark slide theme
    used across the course (same palette as gen_debugging_figs.py).

How to use
    uv run --with matplotlib \\
        week12-t06-tdd/slides/assets/gen_decomposition_fig.py
    Writes decomposition_blocks.png (+ .svg) into this directory.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT = os.path.dirname(os.path.abspath(__file__))

INK = "#e6e6e6"
FADED = "#5b6472"
BACKBONE = "#4ea8de"  # tour / edge-usage: the shared spine
CAPACITY = "#7fbf7b"
TIMEWIN = "#e69138"
COST = "#b39ddb"

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


def gen_decomposition_blocks():
    # Each component contributes a column group (its variables) and a row group
    # (its constraints). Widths/heights are in "cells"; the backbone is wider
    # because every component leans on it.
    # Per group: (column label = its variables, row label = its constraints,
    # size in cells, color). Naming each axis directly is clearer than a single
    # generic "variables"/"constraints" arrow.
    comps = [
        ("Edge\nvariables", "Tour\nconstraints", 6, BACKBONE),
        ("Capacity\nvariables", "Capacity\nconstraints", 4, CAPACITY),
        ("Time-window\nvariables", "Time-window\nconstraints", 4, TIMEWIN),
        ("Cost\nvariables", "Cost\nconstraints", 4, COST),
    ]
    col_names = [c[0] for c in comps]
    row_names = [c[1] for c in comps]
    sizes = [c[2] for c in comps]
    colors = [c[3] for c in comps]

    # Contiguous matrix, no gaps. Columns are stretched wider than rows are tall
    # (XS) so the multi-word variable labels have horizontal room to sit over
    # their groups without crowding their neighbours.
    XS = 1.7
    col_w = [s * XS for s in sizes]
    col_start = [sum(col_w[:i]) for i in range(len(sizes))]
    span_x = sum(col_w)
    span_y = sum(sizes)
    # Rows are drawn top-to-bottom, so the backbone group sits at the top-left
    # like a matrix; row_top is the top edge y of each group.
    row_top = [span_y - sum(sizes[:i]) for i in range(len(sizes))]

    fig, ax = plt.subplots(figsize=(9.2, 6.2))

    # Full-height backbone band: every constraint references the tour variables.
    ax.add_patch(
        Rectangle(
            (col_start[0], 0),
            col_w[0],
            span_y,
            fc=BACKBONE,
            ec="none",
            alpha=0.28,
            zorder=2,
        )
    )

    # Off-backbone couplings between components, keyed by row-group index ->
    # the column-group indices it also references. The cost component composes
    # both the backbone and the time-window component, so its row band reaches
    # into the time-window columns as well (CostComp(TourComp, TimeWindowComp)).
    extra_coupling = {3: [2]}  # cost rows -> time-window columns

    # Per-component blocks: each component's rows over its own columns, plus a
    # denser overlay on the backbone columns to show the shared coupling.
    for i in range(len(comps)):
        h, color = sizes[i], colors[i]
        y0 = row_top[i] - h  # bottom edge of this row band
        x0 = col_start[i]
        # Own block (own columns x own rows) — solid, this is the component core.
        ax.add_patch(
            Rectangle((x0, y0), col_w[i], h, fc=color, ec=INK, lw=1.3, alpha=0.92, zorder=3)
        )
        if i > 0:
            # Coupling into the backbone columns (own rows x backbone columns).
            ax.add_patch(
                Rectangle(
                    (col_start[0], y0), col_w[0], h, fc=color, ec="none", alpha=0.55, zorder=3
                )
            )
        # Coupling into another component's columns (e.g. cost -> time-window).
        for j in extra_coupling.get(i, []):
            ax.add_patch(
                Rectangle(
                    (col_start[j], y0),
                    col_w[j],
                    h,
                    fc=color,
                    ec="none",
                    alpha=0.55,
                    zorder=3,
                )
            )

    # Column-group labels along the top (the variables of each component).
    for i, name in enumerate(col_names):
        ax.text(
            col_start[i] + col_w[i] / 2,
            span_y + 0.5,
            name,
            ha="center",
            va="bottom",
            fontsize=12,
            color=colors[i],
        )
    # Row-group labels along the left (the constraints of each component).
    for i, name in enumerate(row_names):
        ax.text(
            -0.9,
            row_top[i] - sizes[i] / 2,
            name,
            ha="right",
            va="center",
            fontsize=12,
            color=colors[i],
        )

    ax.set_xlim(-7.2, span_x + 0.6)
    ax.set_ylim(-1.0, span_y + 2.2)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "decomposition_blocks")


if __name__ == "__main__":
    gen_decomposition_blocks()
    print("Wrote decomposition_blocks (PNG+SVG) to", OUT)
