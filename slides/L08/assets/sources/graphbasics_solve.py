"""
Graph-vocabulary concept graphics for the L08 "Quick Recap of Graphs" opener.

What this file contains:
  Pure slide art that builds graph vocabulary incrementally on ONE small ~6-node
  graph with hand-placed, deterministic positions: undirected nodes+edges, then
  edge weights / a node annotation, then a directed version, then a layered DAG
  (with a faded would-be back-edge marked as not allowed), plus a 2x2 overview
  panel composing all four for a one-slide recap.
  Non-goal: nothing is solved here (no shortest path, no traversal, no objective).
  These are concept figures only; there is no instance to optimize.

Why it exists:
  These are the FIRST slides of L08. The look sets the tone for the whole deck:
  clean, minimal, high-contrast, colorblind-friendly, terse labels, no clutter.
  Reusing the same graph + positions lets the lecturer reveal it step by step.

How to run:
  python solve.py     # writes 00_overview, 01_nodes_edges, 02_weighted,
                      # 03_directed, 04_dag (+ 04b_cycle) as PNG and SVG.
  If networkx/matplotlib import fails the env is conda mo312:
  conda run -n mo312 python solve.py

When it would change:
  If the recap wants a different vocabulary order, a larger/smaller base graph,
  or extra concepts (e.g. multigraph, self-loop). Drawing primitives live in
  helpers.py in this folder.
"""

# %%
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/"
    "week07-l08-graph-algorithms/snippets",
)
import aeviz  # noqa: E402

from helpers import (  # noqa: E402
    draw_dag,
    draw_directed,
    draw_undirected,
    draw_weighted,
)

aeviz.init_style()

# %% Shared instance ---------------------------------------------------------
# ONE small undirected graph, hand-placed so the geometry stays readable and
# stable across figures 01-03. Six nodes, seven edges: connected, one short
# cycle, no clutter.
NODES = ["a", "b", "c", "d", "e", "f"]
EDGES = [
    ("a", "b"),
    ("a", "c"),
    ("b", "c"),
    ("b", "d"),
    ("c", "e"),
    ("d", "e"),
    ("e", "f"),
]
# Hand-placed positions (deterministic, no layout solver).
POS = {
    "a": (0.0, 1.25),
    "b": (1.15, 2.25),
    "c": (1.3, 0.2),
    "d": (2.45, 2.05),
    "e": (2.6, 0.45),
    "f": (3.35, 1.3),
}
# Edge weights for figure 02 (terse integers).
WEIGHTS = {
    ("a", "b"): 4,
    ("a", "c"): 2,
    ("b", "c"): 1,
    ("b", "d"): 5,
    ("c", "e"): 3,
    ("d", "e"): 2,
    ("e", "f"): 6,
}
# One node annotation to show nodes can carry data too.
NODE_ANNOTATION = ("a", "depot")

# %% Directed orientation ----------------------------------------------------
# Orient each undirected edge one way to make figure 03 directed (one-way arcs).
# d<->e is kept two-way (both arcs) to show a bidirectional edge is still allowed
# in a directed graph; draw_directed bows the reciprocal pair apart.
DIR_EDGES = [
    ("a", "b"),
    ("a", "c"),
    ("c", "b"),
    ("b", "d"),
    ("c", "e"),
    ("d", "e"),
    ("e", "d"),
    ("e", "f"),
]

# %% DAG instance ------------------------------------------------------------
# A separate small DAG laid out strictly left-to-right in layers so acyclicity
# reads at a glance. One faded right-to-left arc is drawn as the would-be back
# edge, marked "not allowed".
DAG_NODES = ["s", "t", "u", "v", "w", "x"]
DAG_EDGES = [
    ("s", "t"),
    ("s", "u"),
    ("t", "v"),
    ("u", "v"),
    ("u", "w"),
    ("v", "x"),
    ("w", "x"),
]
# Layered positions: x increases with topological depth, so every solid arc
# points rightward and the layout itself proves there is no cycle.
DAG_POS = {
    "s": (0.0, 1.3),
    "t": (1.5, 2.2),
    "u": (1.5, 0.4),
    "v": (3.0, 1.6),
    "w": (3.0, 0.2),
    "x": (4.5, 1.0),
}
# A would-be back edge from an interior node back to the source: drawn faded +
# dashed + "not allowed". It closes a real cycle (s -> t -> v -> s), so it reads
# as "no cycles", not just "this one edge cannot be two-way". Kept to v (not the
# far sink x) so the arc stays compact instead of sweeping the whole width.
DAG_BACK_EDGE = ("v", "s")

# A tiny cyclic digraph beside the DAG to sharpen the contrast (figure 04b).
CYC_NODES = ["p", "q", "r"]
CYC_EDGES = [("p", "q"), ("q", "r"), ("r", "p")]
CYC_POS = {
    "p": (0.0, 0.0),
    "q": (1.4, 1.0),
    "r": (1.4, -1.0),
}

# An undirected tree: the cycle-free case without direction. Connected, n-1 edges,
# a unique path between any two nodes. Sits beside the DAG (figure 04c) so the
# recap shows both flavors of "cycle-free".
TREE_NODES = ["a", "b", "c", "d", "e", "f"]
TREE_EDGES = [("a", "b"), ("a", "c"), ("b", "d"), ("b", "e"), ("c", "f")]
TREE_POS = {
    "a": (1.5, 2.4),
    "b": (0.7, 1.3),
    "c": (2.5, 1.3),
    "d": (0.0, 0.2),
    "e": (1.3, 0.2),
    "f": (2.5, 0.2),
}

# %% Figure 01: nodes and edges ----------------------------------------------
fig, ax = plt.subplots(figsize=(7.0, 4.4))
draw_undirected(ax, POS, EDGES)
aeviz.save(fig, "01_nodes_edges")
plt.close(fig)

# %% Figure 02: edge weights + a node annotation -----------------------------
fig, ax = plt.subplots(figsize=(7.0, 4.4))
draw_weighted(ax, POS, EDGES, WEIGHTS, node_annotation=NODE_ANNOTATION)
aeviz.save(fig, "02_weighted")
plt.close(fig)

# %% Figure 03: directed -----------------------------------------------------
fig, ax = plt.subplots(figsize=(7.0, 4.4))
draw_directed(ax, POS, DIR_EDGES)
aeviz.save(fig, "03_directed")
plt.close(fig)

# %% Figure 04: DAG (layered, with a marked would-be back edge) --------------
fig, ax = plt.subplots(figsize=(7.0, 4.4))
draw_dag(ax, DAG_POS, DAG_EDGES, back_edge=DAG_BACK_EDGE)
# tight: the wide-and-short DAG + equal aspect otherwise bakes a tall empty band
# above and below into the SVG, which scales up in the slide column.
aeviz.save(fig, "04_dag", tight=True)
plt.close(fig)

# %% Figure 04b: cyclic digraph contrast -------------------------------------
fig, ax = plt.subplots(figsize=(3.6, 3.2))
draw_directed(ax, CYC_POS, CYC_EDGES, rad=0.16, label="has a cycle")
aeviz.save(fig, "04b_cycle")
plt.close(fig)

# %% Figure 04c: undirected tree (cycle-free, undirected) --------------------
fig, ax = plt.subplots(figsize=(5.4, 4.4))
draw_undirected(ax, TREE_POS, TREE_EDGES)
aeviz.save(fig, "04c_tree", tight=True)  # sit flush beside the DAG, no margin band
plt.close(fig)

# %% Figure 00: 2x2 overview -------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.0))
draw_undirected(axes[0, 0], POS, EDGES, title="Nodes and edges")
draw_weighted(
    axes[0, 1], POS, EDGES, WEIGHTS, node_annotation=NODE_ANNOTATION,
    title="Weights and annotations",
)
draw_directed(axes[1, 0], POS, DIR_EDGES, title="Directed: one-way edges")
draw_dag(axes[1, 1], DAG_POS, DAG_EDGES, back_edge=DAG_BACK_EDGE, title="DAG: no cycles")
fig.tight_layout()
aeviz.save(fig, "00_overview")
plt.close(fig)

# %% Summary -----------------------------------------------------------------
print("wrote 7 figures (PNG+SVG): 00_overview, 01_nodes_edges, 02_weighted, "
      "03_directed, 04_dag, 04b_cycle, 04c_tree")
