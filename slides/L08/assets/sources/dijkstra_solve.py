"""
Dijkstra walk-through for the L08 shortest-paths recap.

What this file contains:
  Reconstruction of the Dijkstra example from [P] (Postek et al.,
  Hands-On Mathematical Optimization with Python, Example 4.4): a small directed
  weighted graph, source a, target c. It solves the s->t shortest path with
  networkx and renders an animation-style frame sequence (instance, per-settle
  frames, final solution) that shows label-setting: settled set grows while
  tentative labels relax.
  Non-goal: this is not a general Dijkstra library and does not reproduce the
  book's hand-iteration tables verbatim.

Why it exists:
  Recap anchor that opens the Shortest Paths pillar. The frontier/settled
  animation is the product; the numeric answer is secondary.

How to run:
  python solve.py          # writes 01_instance.png, 02_step_*.png, 03_solution.png

When it would change:
  If the chosen instance changes, or if the slide wants different framing
  (undirected variant, A* overlay, more/fewer frames).

Instance source: edge weights recovered from the label-update table (Table 4.3)
in [P] Ex 4.4 (the figure weights themselves are images, not text). Recovered
edges reproduce the book's settle order (a, d, e, b, c) and answer exactly:
  a->b:10, a->d:5, d->b:3, d->c:9, d->e:2, e->c:6, b->c:1
Shortest path a->c = [a, d, b, c], length 9.
"""

# %%
import heapq
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

# Shared L08 visualization helpers: uniform style, legends OUTSIDE the axes (so
# nothing crowds node e), and horizontal edge-weight labels.
sys.path.insert(0, "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/week07-l08-graph-algorithms/snippets")
import aeviz

aeviz.init_style()

# %% Instance ----------------------------------------------------------------
# Directed weighted graph from [P] Example 4.4. Source a, target c.
EDGES = [
    ("a", "b", 10),
    ("a", "d", 5),
    ("d", "b", 3),
    ("d", "c", 9),
    ("d", "e", 2),
    ("e", "c", 6),
    ("b", "c", 1),
]
SOURCE, TARGET = "a", "c"

G = nx.DiGraph()
for u, v, w in EDGES:
    G.add_edge(u, v, weight=w)

# Hand-placed positions for a stable, readable layout (matches book topology:
# a left, d/b in a vertical pair, e low, c right).
POS = {
    "a": (0.0, 1.0),
    "b": (1.6, 1.7),
    "d": (1.6, 0.3),
    "e": (2.8, -0.6),
    "c": (4.2, 1.0),
}

# %% Solve with networkx -----------------------------------------------------
sp_path = nx.dijkstra_path(G, SOURCE, TARGET, weight="weight")
sp_len = nx.dijkstra_path_length(G, SOURCE, TARGET, weight="weight")
path_edges = set(zip(sp_path, sp_path[1:]))


# %% Hand-written Dijkstra to capture per-step state -------------------------
def dijkstra_trace(graph, source):
    """Run Dijkstra, recording one snapshot each time a node is settled.

    Returns the settle order and a list of frames. Each frame holds the
    settled set, the just-settled node, its current tentative labels, and the
    edges relaxed (improved) while scanning that node. We expect the settle
    order to match the book: a, d, e, b, c.
    """
    dist = {n: float("inf") for n in graph.nodes}
    dist[source] = 0
    settled = set()
    order = []
    frames = []
    heap = [(0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in settled:
            continue
        settled.add(u)
        order.append(u)
        relaxed = []
        for v in graph.successors(u):
            nd = d + graph[u][v]["weight"]
            if nd < dist[v]:
                dist[v] = nd
                relaxed.append((u, v))
                heapq.heappush(heap, (nd, v))
        frames.append(
            {
                "settled": set(settled),
                "current": u,
                "labels": dict(dist),
                "relaxed": list(relaxed),
            }
        )
    return order, frames


order, frames = dijkstra_trace(G, SOURCE)

# %% Stdout summary ----------------------------------------------------------
print("Dijkstra walk-through  (from [P] Example 4.4)")
print(f"  source = {SOURCE}, target = {TARGET}")
print(f"  shortest path : {' -> '.join(sp_path)}")
print(f"  length        : {sp_len}")
print(f"  settle order  : {', '.join(order)}")
print("  final labels  : " + ", ".join(f"{n}={frames[-1]['labels'][n]}" for n in sorted(G.nodes)))


# %% Drawing helpers ---------------------------------------------------------
# Every frame is drawn on ONE fixed canvas: same figsize, same axis limits, same
# legend in the same reserved strip. Only node/edge colors and labels change
# between frames. This is what lets the slide stack them in an .r-stack overlay
# (fade-in-then-out) without the graph jumping or rescaling between clicks. With
# matplotlib's default tight bbox, each frame was cropped to its own content, so
# the instance, the steps, and the solution came out at different aspect ratios.
from matplotlib.lines import Line2D  # noqa: E402

SETTLED_C = "#1b3a5c"   # dark blue
CURRENT_C = "#e07b39"   # orange (just settled / being scanned)
FRONTIER_C = "#6fa8dc"  # mid blue (reached, tentative)
UNTOUCHED_C = "#dfe3e8"  # light gray
PATH_C = "#c0392b"      # red for the final path
RELAX_C = "#e07b39"     # orange for the relaxed edge

# Fixed canvas geometry. Limits derived from POS with padding; equal aspect so
# the book topology is preserved. The right ~24% is reserved for the legend via
# subplots_adjust, identical on every frame.
FIGSIZE = (8.0, 4.4)
XLIM = (-0.5, 4.7)
YLIM = (-1.15, 2.25)

# One shared legend, drawn identically on all seven frames. Because it never
# changes, it reads as a static key in the overlay.
LEGEND_HANDLES = [
    Line2D([], [], marker="o", linestyle="none", markersize=11,
           markerfacecolor=SETTLED_C, markeredgecolor="#333333", label="settled (final)"),
    Line2D([], [], marker="o", linestyle="none", markersize=11,
           markerfacecolor=CURRENT_C, markeredgecolor="#333333", label="just settled"),
    Line2D([], [], marker="o", linestyle="none", markersize=11,
           markerfacecolor=FRONTIER_C, markeredgecolor="#333333", label="frontier (tentative)"),
    Line2D([], [], marker="o", linestyle="none", markersize=11,
           markerfacecolor=UNTOUCHED_C, markeredgecolor="#333333", label="untouched"),
    Line2D([], [], color=PATH_C, linewidth=3.4, label="shortest path"),
]


def label_str(labels, n):
    # Show the tentative distance under every node, including the initial value
    # infinity for not-yet-reached nodes. Making the label-setting model explicit
    # (every node always carries a g-value, starting at infinity) is what the A*
    # slide builds on: f(v) = g(v) + h(v), Dijkstra is A* with h == 0.
    v = labels[n]
    return f"{n}\n∞" if v == float("inf") else f"{n}\n{int(v)}"


def new_canvas():
    """Fresh figure/axes with the fixed geometry and reserved legend strip."""
    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.subplots_adjust(left=0.02, right=0.76, top=0.90, bottom=0.02)
    return fig, ax


def draw_base(ax, edge_colors, edge_widths, node_colors, labels, font_colors):
    nx.draw_networkx_edges(
        G, POS, ax=ax, edge_color=edge_colors, width=edge_widths,
        arrows=True, arrowsize=18, node_size=1500,
        connectionstyle="arc3,rad=0.0", min_target_margin=22,
    )
    nx.draw_networkx_nodes(
        G, POS, ax=ax, node_color=node_colors, node_size=1500,
        edgecolors="#333333", linewidths=1.5,
    )
    for n in G.nodes:
        ax.text(
            *POS[n], labels[n], ha="center", va="center",
            fontsize=11, fontweight="bold", color=font_colors[n], zorder=5,
        )
    elabels = {(u, v): G[u][v]["weight"] for u, v in G.edges}
    # Horizontal weight labels with a dark backing chip (no chord-angle rotation).
    aeviz.straight_edge_labels(ax, POS, elabels, font_size=10)
    ax.set_axis_off()
    ax.set_aspect("equal")
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)


def add_legend(ax):
    leg = ax.legend(
        handles=LEGEND_HANDLES, loc="center left", bbox_to_anchor=(1.02, 0.5),
        frameon=True, borderaxespad=0.0, fontsize=9, handletextpad=0.6,
        labelspacing=0.8,
    )
    aeviz._style_legend(leg)


def save(fig, stem):
    # Override the global tight bbox so every frame keeps the SAME fixed canvas
    # (bbox_inches=None) -- this is the whole point: identical dimensions so the
    # r-stack overlay does not rescale the graph between clicks. PNG + SVG.
    for ext in ("png", "svg"):
        fig.savefig(f"{stem}.{ext}", bbox_inches=None)
    plt.close(fig)


# %% Figure 1: instance ------------------------------------------------------
fig, ax = new_canvas()
ncolors, fcolors = [], {}
for n in G.nodes:
    if n == SOURCE:
        ncolors.append(SETTLED_C); fcolors[n] = "white"
    elif n == TARGET:
        ncolors.append(PATH_C); fcolors[n] = "white"
    else:
        ncolors.append(UNTOUCHED_C); fcolors[n] = "#222222"
# Initialized tentative distances: source 0, every other node infinity. This is
# the state the narration describes ("every node carries a tentative distance").
init_labels = {n: (0 if n == SOURCE else float("inf")) for n in G.nodes}
draw_base(
    ax,
    edge_colors=["#9aa3ad"] * G.number_of_edges(),
    edge_widths=[1.8] * G.number_of_edges(),
    node_colors=ncolors,
    labels={n: label_str(init_labels, n) for n in G.nodes},
    font_colors=fcolors,
)
ax.set_title(f"Instance: shortest path {SOURCE} → {TARGET}", fontsize=13)
add_legend(ax)
save(fig, "01_instance")


# %% Figures 2..: per-settle-step frames -------------------------------------
def node_color_for(n, frame):
    if n == frame["current"]:
        return CURRENT_C, "white"
    if n in frame["settled"]:
        return SETTLED_C, "white"
    if frame["labels"][n] != float("inf"):
        return FRONTIER_C, "#10243a"
    return UNTOUCHED_C, "#222222"


for i, frame in enumerate(frames, start=1):
    fig, ax = new_canvas()
    ncolors, fcolors = [], {}
    for n in G.nodes:
        c, fc = node_color_for(n, frame)
        ncolors.append(c)
        fcolors[n] = fc
    relaxed = set(frame["relaxed"])
    ecolors, ewidths = [], []
    for u, v in G.edges:
        if (u, v) in relaxed:
            ecolors.append(RELAX_C); ewidths.append(3.2)
        else:
            ecolors.append("#c7ccd2"); ewidths.append(1.4)
    labels = {n: label_str(frame["labels"], n) for n in G.nodes}
    draw_base(ax, ecolors, ewidths, ncolors, labels, fcolors)
    cur = frame["current"]
    ax.set_title(
        f"Step {i}: settle {cur} (label {int(frame['labels'][cur])})",
        fontsize=13,
    )
    add_legend(ax)
    save(fig, f"02_step_{i}")


# %% Final figure: solution highlighted --------------------------------------
fig, ax = new_canvas()
ncolors, fcolors = [], {}
for n in G.nodes:
    if n in sp_path:
        ncolors.append(PATH_C); fcolors[n] = "white"
    else:
        ncolors.append(UNTOUCHED_C); fcolors[n] = "#222222"
ecolors, ewidths = [], []
for u, v in G.edges:
    if (u, v) in path_edges:
        ecolors.append(PATH_C); ewidths.append(3.6)
    else:
        ecolors.append("#d6dade"); ewidths.append(1.3)
labels = {n: label_str(frames[-1]["labels"], n) for n in G.nodes}
draw_base(ax, ecolors, ewidths, ncolors, labels, fcolors)
ax.set_title(
    f"Shortest path  {' → '.join(sp_path)}  (length {sp_len})", fontsize=13,
)
add_legend(ax)
save(fig, "03_solution")

print("\nWrote 7 fixed-canvas frames (png + svg): 01_instance, "
      f"02_step_1..{len(frames)}, 03_solution")
