"""Minimum spanning tree on a wind farm: cheapest cabling to connect every turbine.

What this file does: takes the same wind farm as the max-flow example and asks the
collector-layout question for L08 item 6.2: ignore capacities, and connect every
turbine to the grid substation with the minimum total cable length. It builds the
complete Euclidean graph over the turbines plus the substation (cable cost = km of
trench), solves the MST with Kruskal / Prim / Boruvka (asserting they agree), and
draws two slide-ready figures (the candidate cables, then the MST). Non-goal:
capacities / power flow (that is the max-flow example), Steiner points, redundant
(loop) layouts.

Why it exists: covers lecture plan item 6.2, the "return to the same power network"
callback after the max-flow slides (plan 5.2 -> 6.2): same picture, a different
question. It is the power-network analog of the existing communications-network MST
example (../communications-mst), offered so Dominik can choose which to ship.

SHARED INSTANCE: the turbine names, (x, y) coordinates, and the grid node are the
identical wind farm used by ../../03-flows/wind-power-maxflow (same geometry, so
the two figures are recognizably the same farm). The turbine coordinates and node
names MUST stay in sync between the two files. This example ignores the max-flow
example's generation / capacity numbers and uses Euclidean cable length as cost.

How to run:
    python solve.py   # writes 01_network.{png,svg}, 02_mst.{png,svg}
    # if `import networkx` fails: conda run -n mo312 python solve.py

When to change: if the farm geometry changes, edit the SHARED block here AND in the
max-flow example. The cost model is straight-line distance, so the MST is fully
determined by the coordinates.
"""

# %% Imports and deterministic, headless setup
import math
import sys

import matplotlib

matplotlib.use("Agg")  # headless / deterministic raster + svg output

import matplotlib.pyplot as plt
import networkx as nx

sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/"
    "week07-l08-graph-algorithms/snippets",
)

import aeviz

aeviz.init_style()

# %% ----------------------------------------------------------------------------
# SHARED INSTANCE (keep byte-for-byte in sync with
# ../../03-flows/wind-power-maxflow/solve.py). Eight masts in a field (five
# turbines + three collector junctions, a split defined per-example) plus one grid
# substation. Coordinates are hand-placed (km), not random, so the figure is the
# same recognizable farm reused by both examples.
GRID = "GRID"  # the substation / grid connection

TURBINES = {
    "T1": (1.0, 7.0),
    "T2": (3.0, 8.0),
    "T3": (2.0, 5.0),
    "T4": (4.0, 5.5),
    "T5": (1.5, 3.0),
    "T6": (3.5, 2.5),
    "T7": (6.0, 6.5),
    "T8": (6.5, 3.5),
}

POS = dict(TURBINES)
POS[GRID] = (9.0, 5.0)  # substation to the east of the field
# END SHARED INSTANCE -----------------------------------------------------------

# Roles mirror the max-flow example (../../03-flows/wind-power-maxflow): three of
# the inner masts are non-generating collector junctions, drawn as C1/C2/C3 so each
# site is labeled identically across the two slides (the "same farm" callback). The
# MST itself ignores roles entirely; it is a function of the coordinates only.
COLLECTORS = {"T4", "T7", "T8"}
GENERATORS = [t for t in TURBINES if t not in COLLECTORS]
LABEL = {**{t: t for t in GENERATORS},
         "T4": "C1", "T7": "C2", "T8": "C3", GRID: "GRID"}

COST_PER_KM = 1.0  # cable cost is proportional to trench length; report raw km


# %% Build the complete Euclidean graph over turbines + substation
# Every pair of sites is a candidate cable; cost = straight-line km. Capacities are
# deliberately ignored here: the MST question is purely about cabling length.
def euclid(p: tuple[float, float], q: tuple[float, float]) -> float:
    return math.hypot(p[0] - q[0], p[1] - q[1])


SITES = list(TURBINES) + [GRID]
G = nx.Graph()
G.add_nodes_from(SITES)
for i, u in enumerate(SITES):
    for v in SITES[i + 1:]:
        G.add_edge(u, v, weight=COST_PER_KM * euclid(POS[u], POS[v]))

# %% Solve the MST three ways and assert agreement
trees = {
    alg: nx.minimum_spanning_tree(G, algorithm=alg)
    for alg in ("kruskal", "prim", "boruvka")
}
totals = {alg: sum(d["weight"] for *_, d in t.edges(data=True)) for alg, t in trees.items()}
ref = totals["kruskal"]
for alg, tot in totals.items():
    assert math.isclose(tot, ref, rel_tol=1e-9), f"{alg} disagrees: {tot} vs {ref}"

MST = trees["kruskal"]
MST_TOTAL = ref

# The MST must connect all sites: exactly n-1 edges and a single component.
assert MST.number_of_edges() == len(SITES) - 1, "MST does not have n-1 edges"
assert nx.is_connected(MST), "MST does not connect all sites"

# %% Print the stdout summary
print("=== Wind farm MST (cheapest cabling to the grid) ===")
print(f"sites: {len(SITES)} ({len(GENERATORS)} turbines + {len(COLLECTORS)} "
      f"collector junctions + grid)   "
      f"candidate cables: {G.number_of_edges()}")
print("total cable length agrees across kruskal / prim / boruvka:")
for alg, tot in totals.items():
    print(f"  {alg:8s}  {tot:7.2f} km")
print(f"MST edges ({MST.number_of_edges()} = {len(SITES)} sites - 1), cost order:")
for u, v, d in sorted(MST.edges(data=True), key=lambda e: e[2]["weight"]):
    print(f"  {u}-{v}   {d['weight']:5.2f} km")
print(f"total cable length: {MST_TOTAL:.2f} km")

# %% Shared drawing helpers
NODE_FILL = aeviz.PALETTE["node_face"]   # navy turbine fill, light text on top
COLL_FILL = aeviz.PALETTE["faded"]       # grey-blue collector junction (no generator)
NODE_EDGE = aeviz.PALETTE["node_edge"]   # light-blue node ring (reads on dark)
NODE_TEXT = aeviz.PALETTE["ink"]         # light node labels / annotations
GRID_FILL = aeviz.PALETTE["good"]        # green substation, kept semantic on dark
GRAY = aeviz.PALETTE["faded_dark"]       # neutral candidate cables (lighter than the
#                                          collector squares, so they stay distinct)
BOLD = aeviz.PALETTE["path"]             # blue for the chosen tree


def _draw_nodes(ax):
    # Generators: navy circles. Collector junctions: grey-blue squares. Grid: green.
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=GENERATORS, node_size=1300,
                           node_color=NODE_FILL, edgecolors=NODE_EDGE, linewidths=1.6)
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=sorted(COLLECTORS), node_size=1150,
                           node_shape="s", node_color=COLL_FILL,
                           edgecolors=NODE_EDGE, linewidths=1.6)
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=[GRID], node_size=1500,
                           node_color=GRID_FILL, edgecolors=NODE_EDGE, linewidths=1.6)
    # GRID node has a bright green fill: use dark text there for contrast, light
    # text on the dark turbine / collector nodes.
    nx.draw_networkx_labels(
        G, POS, labels={GRID: "GRID"}, ax=ax, font_size=10,
        font_weight="bold", font_color="#16261c")
    nx.draw_networkx_labels(
        G, POS, labels={n: LABEL[n] for n in TURBINES}, ax=ax, font_size=10,
        font_weight="bold", font_color=NODE_TEXT)
    ax.annotate("substation", POS[GRID], textcoords="offset points",
                xytext=(0, 24), ha="center", fontsize=9, color=NODE_TEXT)


def _frame(ax, title):
    ax.set_title(title, fontsize=13)
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(1.0, 9.5)
    ax.set_aspect("equal")
    ax.axis("off")


def km_label(u: str, v: str) -> str:
    return f"{euclid(POS[u], POS[v]):.1f}"


# %% Figure 1: the instance (all candidate cables, faded, with lengths)
fig_net, ax = plt.subplots(figsize=(8.5, 6.0))
nx.draw_networkx_edges(G, POS, ax=ax, edgelist=list(G.edges()),
                       edge_color=GRAY, width=1.0, alpha=0.6)
_draw_nodes(ax)
_frame(ax, "Wind farm: all candidate cables (cost = trench length in km)")
cand_handle, = ax.plot([], [], color=GRAY, lw=1.0, label="candidate cable")
aeviz.legend_outside(ax, [cand_handle], ["candidate cable"],
                     loc="upper left", fontsize=9)
# No tight_layout: save_aligned crops the group to one common bbox (below).

# %% Figure 2: the MST, bold over the faded non-tree cables
fig_mst, ax = plt.subplots(figsize=(8.5, 6.0))
non_tree = [e for e in G.edges() if not MST.has_edge(*e)]
nx.draw_networkx_edges(G, POS, ax=ax, edgelist=non_tree, edge_color=GRAY,
                       width=0.8, alpha=0.35)
nx.draw_networkx_edges(G, POS, ax=ax, edgelist=list(MST.edges()),
                       edge_color=BOLD, width=3.2)
_draw_nodes(ax)
aeviz.straight_edge_labels(
    ax, POS, {(u, v): km_label(u, v) for u, v in MST.edges()}, font_size=10,
    color=aeviz.PALETTE["weight"])
mst_handle, = ax.plot([], [], color=BOLD, lw=3.2, label="chosen cable (MST)")
aeviz.legend_outside(ax, [mst_handle], ["chosen cable (MST)"],
                     loc="upper left", fontsize=9)
_frame(ax, f"Minimum spanning tree: {MST_TOTAL:.1f} km of cable (lengths in km)")

# Crop both frames to one common bbox so the wind farm sits at identical pixels
# across the .r-stack overlay (frame 2 adds edge-length labels that would widen
# its own tight crop and make the network jump when the MST fades in).
aeviz.save_aligned([(fig_net, "01_network"), (fig_mst, "02_mst")])

print("\nwrote 01_network.{png,svg}, 02_mst.{png,svg}")
