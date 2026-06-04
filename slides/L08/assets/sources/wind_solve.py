"""Max flow on a wind farm: how much power reaches the grid, and where is the bottleneck?

What this file does: models an offshore-style wind farm as a capacitated flow
network and answers two questions for L08. (1) Max flow: given the MW capacity of
each collector cable, what is the maximum power deliverable to the grid
substation? (2) Min cut: which small set of cables is the bottleneck that caps the
answer? It solves with networkx (maximum_flow / minimum_cut), checks max-flow =
min-cut, and draws two slide-ready figures (the capacitated network, and the
optimal flow with the min cut highlighted). Non-goal: cable sizing / layout
optimization, AC power-flow physics, residual-graph iteration tables.

Why it exists: covers lecture plan items 5.2 (max power to the grid) and 5.3 (read
the bottleneck off the min cut). It is the power-network analog of the existing
water-network max-flow example (../water-network-maxflow), offered so Dominik can
choose which scenario to ship.

SHARED INSTANCE: the mast names, (x, y) coordinates, and the grid node are the
identical wind farm used by ../../05-spanning-trees/wind-power-mst (the "return to
the same picture" callback, plan 5.2 -> 6.2). The coordinates and node names MUST
stay in sync between the two files. This file additionally assigns roles (five
generating turbines + three non-generating collector junctions), per-generator
output, and per-cable MW capacities (all ignored by the MST example, which uses
only the coordinates).

Why three of the masts carry no generator: with a super-source feeding every
generator, a generating node is always reachable from the source in the residual
graph, so a *physical* min cut is forced to the cables at the grid -- a trivial
bottleneck that the min cut adds no insight to. Non-generating relays let the cut
land in the middle of the array (here the two cross-field trunks T3->C1, T6->C3),
which is the whole point of item 5.3.

How to run:
    python solve.py   # writes 01_network.{png,svg}, 02_maxflow.{png,svg}
    # if `import networkx` fails: conda run -n mo312 python solve.py

When to change: if the farm geometry changes, edit the SHARED block here AND in the
MST example. If the capacities change, keep the interior cut (the asserts below pin
it to the two trunks) so item 5.3 still has a non-trivial bottleneck to point at.
"""

# %% Imports and deterministic, headless setup
import sys

import matplotlib

matplotlib.use("Agg")  # headless / deterministic raster + svg output

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/"
    "week07-l08-graph-algorithms/snippets",
)

import aeviz

np.random.seed(0)
aeviz.init_style()

# %% ----------------------------------------------------------------------------
# SHARED INSTANCE (keep byte-for-byte in sync with
# ../../05-spanning-trees/wind-power-mst/solve.py). Eight turbines in a field plus
# one grid substation. Coordinates are hand-placed (km), not random, so the figure
# is a recognizable farm reused by both examples.
GRID = "GRID"  # the substation / grid connection (the flow sink)

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

# %% Max-flow-specific roles + data (NOT part of the shared geometry).
# Of the eight masts, three inner ones carry NO generator: they are collector
# junctions (no source arc) that only gather and forward power. This matters for
# the min cut: with a super-source feeding every generator, a generating node is
# always reachable from the source, which forces any physical min cut to the grid
# feeders. Making the inner nodes non-generating relays lets the min cut land in
# the MIDDLE of the array instead of trivially at the substation.
COLLECTORS = {"T4", "T7", "T8"}                         # relays, drawn as C1/C2/C3
GENERATORS = [t for t in TURBINES if t not in COLLECTORS]  # T1,T2,T3,T5,T6
LABEL = {**{t: t for t in GENERATORS},
         "T4": "C1", "T7": "C2", "T8": "C3", GRID: "GRID"}

# Per-generator output (MW). Total exceeds what the trunks can carry, so a real
# bottleneck exists and some power is curtailed.
GEN = {"T1": 6, "T2": 4, "T3": 4, "T5": 6, "T6": 6}
TOTAL_GEN = sum(GEN.values())  # 26 MW of nameplate generation

# Collector cables, with MW capacity. The farm runs as two strings that gather the
# generators and cross the field through ONE trunk each:
#   north string  T1,T2,T3 -> T3 ==11==> C1   (cut)
#   south string  T5,T6    -> T6 == 9==> C3   (cut)
# East of those trunks the collector grid and the export to the substation are
# deliberately generous, so the bottleneck is the pair of cross-field trunks, not
# the grid connection. The min cut is { T3->C1, T6->C3 } = 20 MW, mid-array.
CABLES = {
    # north string gathers at T3
    ("T1", "T3"): 9,
    ("T2", "T3"): 7,
    # south string gathers at T6
    ("T5", "T6"): 7,
    # the two cross-field trunks (the bottleneck = the min cut)
    ("T3", "T4"): 11,   # T3 -> C1, north trunk
    ("T6", "T8"): 9,    # T6 -> C3, south trunk
    # collector grid east of the trunks (generous; C1->C3 stays an empty relief
    # line, showing the limit is upstream, not here)
    ("T4", "T7"): 30,   # C1 -> C2
    ("T4", "T8"): 30,   # C1 -> C3 (relief, unused)
    # export to the substation (generous, NOT the bottleneck)
    ("T7", "GRID"): 30,  # C2 -> GRID
    ("T8", "GRID"): 30,  # C3 -> GRID
}

SOURCE = "SRC"  # super-source feeding each generator its output

# %% Build the capacitated flow network
G = nx.DiGraph()
G.add_node(SOURCE)
for t in TURBINES:
    G.add_node(t)
G.add_node(GRID)
for t in GENERATORS:
    G.add_edge(SOURCE, t, capacity=GEN[t])  # generation as a source arc
for (u, v), cap in CABLES.items():
    G.add_edge(u, v, capacity=cap)

# %% Solve max flow and min cut
flow_value, flow_dict = nx.maximum_flow(G, SOURCE, GRID)
cut_value, (S_side, T_side) = nx.minimum_cut(G, SOURCE, GRID)

assert cut_value == flow_value, f"max-flow {flow_value} != min-cut {cut_value}"
assert flow_value < TOTAL_GEN, (
    f"no bottleneck: max flow {flow_value} >= total generation {TOTAL_GEN}"
)

# Cable flow on the physical cables only (exclude the synthetic source arcs).
cable_flow = {(u, v): flow_dict[u][v] for (u, v) in CABLES}
saturated = [e for e in CABLES if cable_flow[e] == CABLES[e]]

# Min-cut edges: physical cables crossing from the source side to the sink side.
cut_edges = [
    (u, v)
    for (u, v) in CABLES
    if u in S_side and v in T_side
]
cut_capacity = sum(CABLES[e] for e in cut_edges)
# The min cut must lie entirely on physical cables (not on synthetic source arcs),
# so the highlighted cut in the figure is the literal bottleneck of MW = max flow.
assert cut_capacity == cut_value, (
    f"min cut crosses a source arc (cut_value {cut_value} != cable sum "
    f"{cut_capacity}); retune capacities so the bottleneck is physical cables"
)
# The whole point of this instance: the bottleneck is a pair of cross-field trunks
# in the MIDDLE of the array, NOT the cables into the grid. Pin it so a future
# capacity edit cannot silently regress to a trivial at-the-grid cut.
assert set(cut_edges) == {("T3", "T4"), ("T6", "T8")}, sorted(cut_edges)
assert flow_value == 20, flow_value
assert all(v in T_side for v in COLLECTORS) and GRID in T_side, sorted(T_side)
assert all(g in S_side for g in GENERATORS), sorted(S_side)

# %% Print the stdout summary
print("=== Wind farm max flow (power to the grid) ===")
print(f"generators: {len(GENERATORS)}   collector junctions: {len(COLLECTORS)}   "
      f"grid node: {GRID}   super-source: {SOURCE}")
print(f"total nameplate generation: {TOTAL_GEN} MW")
print(f"max power to grid (max flow): {flow_value} MW")
print(f"min cut value: {cut_value} MW   (max-flow = min-cut: {cut_value == flow_value})")
print(f"curtailed (cannot be delivered): {TOTAL_GEN - flow_value} MW")
print("\nper-cable flow / capacity (MW):")
for (u, v) in CABLES:
    mark = "  <- saturated" if (u, v) in saturated else ""
    print(f"  {u}->{v}: {cable_flow[(u, v)]}/{CABLES[(u, v)]}{mark}")
print(f"\nmin-cut (the bottleneck) cables: {[f'{u}->{v}' for (u, v) in cut_edges]}"
      f"  capacities sum = {cut_capacity} MW")
print(f"source side S = {sorted(S_side)}")
print(f"sink side   T = {sorted(T_side)}")

# %% Shared drawing helpers
NODE_FILL = aeviz.PALETTE["node_face"]    # slide navy turbine fill
COLL_FILL = aeviz.PALETTE["faded"]        # grey-blue: passive collector junction
NODE_EDGE = aeviz.PALETTE["node_edge"]    # light-blue node ring
GRID_FILL = aeviz.PALETTE["good"]         # green substation (the sink)
LABEL_INK = aeviz.PALETTE["ink"]          # light text on dark nodes / annotations
GRAY = aeviz.PALETTE["edge"]              # light-blue neutral cable
SAT_COLOR = aeviz.PALETTE["warn"]         # amber for saturated (but not cut) cables
HILITE = aeviz.PALETTE["accent"]          # orange for the cut / bottleneck cables


def _draw_nodes(ax):
    # Generators: navy circles. Collector junctions: grey-blue squares (passive
    # relays, no generator). Substation: green circle (the sink).
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=GENERATORS, node_size=1300,
                           node_color=NODE_FILL, edgecolors=NODE_EDGE, linewidths=1.6)
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=sorted(COLLECTORS), node_size=1150,
                           node_shape="s", node_color=COLL_FILL,
                           edgecolors=NODE_EDGE, linewidths=1.6)
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=[GRID], node_size=1500,
                           node_color=GRID_FILL, edgecolors=NODE_EDGE, linewidths=1.6)
    # Dark nodes get light labels; the light-green grid node gets a dark label.
    nx.draw_networkx_labels(G, POS, labels={n: LABEL[n] for n in TURBINES}, ax=ax,
                            font_size=10, font_weight="bold", font_color=LABEL_INK)
    nx.draw_networkx_labels(G, POS, labels={GRID: "GRID"}, ax=ax, font_size=10,
                            font_weight="bold", font_color="#16261c")
    # Generation note near each generator only (collectors produce nothing).
    gen_offset = {t: (0, 20) for t in GENERATORS}
    gen_offset["T3"] = (-24, 2)   # T3 is a gather hub crowded by cable labels
    for t in GENERATORS:
        ax.annotate(f"{GEN[t]} MW", POS[t], textcoords="offset points",
                    xytext=gen_offset[t], ha="center", fontsize=8,
                    color=aeviz.PALETTE["good"])
    ax.annotate("substation", POS[GRID], textcoords="offset points",
                xytext=(0, 24), ha="center", fontsize=9, color=LABEL_INK)


def _frame(ax, title):
    ax.set_title(title, fontsize=13)
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(1.0, 9.5)
    ax.set_aspect("equal")
    ax.axis("off")


# %% Figure 1: the instance (cable capacities + per-turbine generation)
fig_net, ax = plt.subplots(figsize=(8.5, 6.0))
nx.draw_networkx_edges(G, POS, ax=ax, edgelist=list(CABLES), edge_color=GRAY,
                       width=2.2, arrowsize=18, node_size=1300)
_draw_nodes(ax)
aeviz.straight_edge_labels(ax, POS, {(u, v): f"{CABLES[(u, v)]}" for (u, v) in CABLES},
                           color=aeviz.PALETTE["weight"])
_frame(ax, "Wind farm: collector cable capacities (MW), generation per turbine")
cap_handle, = ax.plot([], [], color=GRAY, lw=2.2, label="cable (number = capacity MW)")
gen_handle, = ax.plot([], [], color=NODE_FILL, lw=0, marker="o", markersize=10,
                      markeredgecolor=NODE_EDGE, label="turbine + generation (MW)")
coll_handle, = ax.plot([], [], color=COLL_FILL, lw=0, marker="s", markersize=10,
                       markeredgecolor=NODE_EDGE, label="collector junction (no generator)")
aeviz.legend_outside(ax, [cap_handle, gen_handle, coll_handle],
                     ["cable capacity (MW)", "turbine + generation (MW)",
                      "collector junction (no generator)"],
                     loc="upper left", fontsize=9)
# No tight_layout: the group is cropped to one common bbox by save_aligned below,
# which keeps the network at identical pixels across both frames.

# %% Figure 2: the max-flow solution with the min cut highlighted
fig_flow, ax = plt.subplots(figsize=(8.5, 6.0))
sat_only = [e for e in saturated if e not in cut_edges]  # saturated but not the cut
unsat = [e for e in CABLES if e not in saturated]
nx.draw_networkx_edges(G, POS, ax=ax, edgelist=unsat, edge_color=GRAY,
                       width=2.0, arrowsize=18, node_size=1300)
if sat_only:
    nx.draw_networkx_edges(G, POS, ax=ax, edgelist=sat_only, edge_color=SAT_COLOR,
                           width=3.4, arrowsize=20, node_size=1300)
# The min-cut cables get the strongest highlight (the bottleneck).
nx.draw_networkx_edges(G, POS, ax=ax, edgelist=cut_edges, edge_color=HILITE,
                       width=4.4, arrowsize=22, node_size=1300)
_draw_nodes(ax)
fc_labels = {(u, v): f"{cable_flow[(u, v)]}/{CABLES[(u, v)]}" for (u, v) in CABLES}
plain = {e: t for e, t in fc_labels.items() if e not in cut_edges}
aeviz.straight_edge_labels(ax, POS, plain, color=aeviz.PALETTE["weight"])
cut_texts = aeviz.straight_edge_labels(
    ax, POS, {e: t for e, t in fc_labels.items() if e in cut_edges}, color=HILITE)
for txt in cut_texts.values():
    txt.set_fontweight("bold")
ax.text(8.0, 2.2, f"max power to grid = {flow_value} MW", ha="center",
        fontsize=12, fontweight="bold", color=HILITE)
cut_handle, = ax.plot([], [], color=HILITE, lw=4.4, label="min cut (bottleneck)")
slack_handle, = ax.plot([], [], color=GRAY, lw=2.0, label="slack remaining")
handles = [cut_handle]
labels = [f"min cut = {cut_capacity} MW (bottleneck)"]
if sat_only:  # only if some saturated cable is not itself part of the cut
    sat_handle, = ax.plot([], [], color=SAT_COLOR, lw=3.4, label="saturated cable")
    handles.append(sat_handle)
    labels.append("saturated (flow = capacity)")
handles.append(slack_handle)
labels.append("slack remaining")
aeviz.legend_outside(ax, handles, labels, loc="upper left", fontsize=9)
_frame(ax, f"Maximum flow: {flow_value} MW to grid (flow / capacity per cable)")

# Crop both frames to one common bbox so the network sits at identical pixels in
# the .r-stack overlay (frame 2's longer 3-row legend would otherwise widen and
# heighten its own tight crop, making the network jump when it fades in).
aeviz.save_aligned([(fig_net, "01_network"), (fig_flow, "02_maxflow")])

print("\nwrote 01_network.{png,svg}, 02_maxflow.{png,svg}")
