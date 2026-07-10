"""Self-authored replacements for the debugging-section figures in T06.

What this file contains
    Generates the sequence diagram and the four running graph-coloring
    pictures used in `_05-debugging-explainability.qmd`: a user/solver
    "ask why" interaction diagram, plus the same small graph shown
    uncolored, colored, with every constraint implicated, with only the
    MUS highlighted, and with a single MCS edge highlighted. All six PNGs
    (+ matching SVGs) render transparent with light foreground, matching
    the dark slide theme used across this course.

Why it exists
    The section is conceptually adapted from Guns & Tsouros's KU Leuven
    constraint-solving course (credited in the section notes), but the
    figures themselves were previously copied image files from that
    course's repository. Copied image assets do not belong in this repo;
    this script draws the same running example from scratch with
    matplotlib/networkx instead, so the deck only ever ships figures it
    generated itself.

How to use
    uv run --with matplotlib --with networkx \\
        week12-t06-tdd/slides/assets/gen_debugging_figs.py
    Regenerates all six images in this directory. Safe to re-run any time;
    the graph layout is seeded for a stable running-example look.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = os.path.dirname(os.path.abspath(__file__))

INK = "#e6e6e6"
FADED = "#5b6472"
BAD = "#e45756"
NODE_FACE = "#2d4059"
NODE_EDGE = "#9ad0f5"
COLOR_A = "#7fbf7b"  # good
COLOR_B = "#4ea8de"  # path
COLOR_C = "#e69138"  # warn

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


# ---------------------------------------------------------------------------
# Sequence diagram: the ask-why interaction loop between modeler and solver.
# ---------------------------------------------------------------------------


def gen_interaction_sequence():
    fig, ax = plt.subplots(figsize=(5.2, 6.4))
    x_you, x_solver = 0.15, 0.85

    for x, label in ((x_you, "You"), (x_solver, "Solver")):
        box = FancyBboxPatch(
            (x - 0.11, 0.93),
            0.22,
            0.07,
            boxstyle="round,pad=0.02",
            fc="none",
            ec=INK,
            lw=1.4,
        )
        ax.add_patch(box)
        ax.text(x, 0.965, label, ha="center", va="center", fontsize=15, color=INK)

    ax.plot([x_you, x_you], [0.0, 0.93], ls=(0, (4, 3)), color=FADED, lw=1.2)
    ax.plot([x_solver, x_solver], [0.0, 0.93], ls=(0, (4, 3)), color=FADED, lw=1.2)

    messages = [
        (x_you, x_solver, 0.83, 0.71, "model"),
        (x_solver, x_you, 0.63, 0.51, "answer\n(SAT / UNSAT / solution)"),
        (x_you, x_solver, 0.43, 0.31, "why?"),
        (x_solver, x_you, 0.23, 0.11, "explanation\n(e.g. a MUS)"),
    ]
    for x_from, x_to, y_top, y_bot, label in messages:
        arrow = FancyArrowPatch(
            (x_from, y_top),
            (x_to, y_bot),
            arrowstyle="-|>",
            mutation_scale=16,
            lw=1.6,
            color=INK,
            linestyle=(0, (5, 3)),
            shrinkA=0,
            shrinkB=2,
        )
        ax.add_patch(arrow)
        offset = 0.05 if "\n" in label else 0.02
        ax.text(
            (x_you + x_solver) / 2,
            (y_top + y_bot) / 2 + offset,
            label,
            ha="center",
            va="bottom",
            fontsize=12.5,
            color=INK,
            bbox=dict(boxstyle="round,pad=0.2", fc=(0.10, 0.14, 0.20, 0.82), ec="none"),
        )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    save(fig, "debug_interaction_sequence")


# ---------------------------------------------------------------------------
# Running example: one small graph-coloring instance, reused across every
# figure in the section so positions stay identical from slide to slide.
# ---------------------------------------------------------------------------


def build_graph():
    g = nx.Graph()
    g.add_edges_from(
        [
            ("A", "B"),
            ("B", "C"),
            ("C", "A"),  # the triangle: forces a third color
            ("A", "D"),
            ("B", "E"),
            ("C", "F"),
            ("F", "G"),
        ]
    )
    pos = nx.spring_layout(g, seed=7, k=0.9)
    return g, pos


def draw_base(ax, g, pos, edge_colors=None, edge_widths=None):
    edge_colors = edge_colors or {e: FADED for e in g.edges}
    edge_widths = edge_widths or {e: 1.6 for e in g.edges}
    for u, v in g.edges:
        key = (u, v) if (u, v) in edge_colors else (v, u)
        nx.draw_networkx_edges(
            g,
            pos,
            edgelist=[(u, v)],
            ax=ax,
            edge_color=edge_colors.get(key, FADED),
            width=edge_widths.get(key, 1.6),
        )


def draw_nodes(ax, g, pos, node_colors=None):
    node_colors = node_colors or {n: NODE_FACE for n in g.nodes}
    nx.draw_networkx_nodes(
        g,
        pos,
        ax=ax,
        node_color=[node_colors[n] for n in g.nodes],
        edgecolors=NODE_EDGE,
        linewidths=1.6,
        node_size=900,
    )
    nx.draw_networkx_labels(g, pos, ax=ax, font_color=INK, font_size=13)


def new_axes():
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    ax.axis("off")
    ax.margins(0.18)
    return fig, ax


def gen_graph_uncolored():
    g, pos = build_graph()
    fig, ax = new_axes()
    draw_base(ax, g, pos)
    draw_nodes(ax, g, pos)
    save(fig, "debug_graph_uncolored")


def gen_graph_colored():
    g, pos = build_graph()
    fig, ax = new_axes()
    draw_base(ax, g, pos)
    coloring = {
        "A": COLOR_A,
        "B": COLOR_B,
        "C": COLOR_C,
        "D": COLOR_B,
        "E": COLOR_A,
        "F": COLOR_A,
        "G": COLOR_B,
    }
    draw_nodes(ax, g, pos, node_colors=coloring)
    save(fig, "debug_graph_colored")


def gen_graph_all_constraints():
    g, pos = build_graph()
    fig, ax = new_axes()
    edge_colors = {e: BAD for e in g.edges}
    edge_widths = {e: 2.2 for e in g.edges}
    draw_base(ax, g, pos, edge_colors, edge_widths)
    draw_nodes(ax, g, pos)
    save(fig, "debug_graph_all_constraints")


def gen_graph_mus():
    g, pos = build_graph()
    fig, ax = new_axes()
    triangle = {("A", "B"), ("B", "C"), ("C", "A")}
    edge_colors = {e: (BAD if e in triangle or (e[1], e[0]) in triangle else FADED) for e in g.edges}
    edge_widths = {e: (2.6 if edge_colors[e] == BAD else 1.2) for e in g.edges}
    draw_base(ax, g, pos, edge_colors, edge_widths)
    draw_nodes(ax, g, pos)
    save(fig, "debug_graph_mus")


def gen_graph_mcs():
    g, pos = build_graph()
    fig, ax = new_axes()
    drop = {("B", "C")}
    edge_colors = {e: (BAD if e in drop or (e[1], e[0]) in drop else FADED) for e in g.edges}
    edge_widths = {e: (2.6 if edge_colors[e] == BAD else 1.2) for e in g.edges}
    draw_base(ax, g, pos, edge_colors, edge_widths)
    draw_nodes(ax, g, pos)
    save(fig, "debug_graph_mcs")


if __name__ == "__main__":
    gen_interaction_sequence()
    gen_graph_uncolored()
    gen_graph_colored()
    gen_graph_all_constraints()
    gen_graph_mus()
    gen_graph_mcs()
    print("Wrote 6 figures (PNG+SVG) to", OUT)
