"""Crate redistribution as MAX FLOW on a TIME-EXPANDED graph.

What this file is
-----------------
A logistics company runs trucks between 4 depots (A, B, C, D). Empty crates
piggy-back on the regular deliveries; each truck has a limited number of empty-
crate slots, so the empties move at most a few per day along the routes the
trucks actually drive. Because the demand pattern is asymmetric, some depots
accumulate a surplus of empty crates on some days while others run short on
other days. We want to push the empties from the surplus places/times to the
shortage places/times to minimize delayed deliveries.

The natural model is a max flow on a TIME-EXPANDED graph:
  * One node per (location, day): A1, A2, ..., D4 (4 depots * 4 days).
  * Super-source SURPLUS connects to (loc,day) whenever that depot/day has
    EXTRA empty crates, with the surplus count as capacity.
  * Super-sink SHORTAGE is fed by (loc,day) whenever that depot/day has
    UNMET demand for crates, capacity = unmet demand.
  * Inter-day arcs (loc,d) -> (loc',d+1) for every truck route, capacity =
    piggy-back slots per day. Holding crates over at the same depot is the
    special case loc=loc'.

That last bullet is the point of the example: the same depot at different days
becomes different nodes connected by a "stay-put" arc -- the standard trick to
turn temporal/storage capacity into ordinary edge capacity, so a static
max-flow solver (which knows nothing about time) handles the routing in time.

Why it exists
-------------
L08, pillar 3 (Flows). Replaces the wind-power max-flow example with a case
that motivates the time-expansion trick; the wind farm shows capacity-limited
flow but the graph is one snapshot in time, so it does not motivate why one
copies the network across days. Crates motivate that copy directly.

How to run
----------
    conda run -n mo312 python crates_solve.py
writes 01_crates_network.{png,svg}, 02_crates_flow.{png,svg} into the assets/
directory next to it, plus prints a short solve summary.

When to change
--------------
Tune SURPLUS, DEMAND, CAPS to keep the flow non-trivial: total surplus should
exceed maximum deliverable so some crates are stranded (curtailment), and the
min cut should land on the inter-day piggy-back arcs (the interesting part)
rather than trivially on the source/sink arcs. The asserts at the bottom pin
the current instance; relax them if you intentionally retune.
"""

# %% Imports + style
import sys
import pathlib

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parent  # .../slides/assets/

sys.path.insert(
    0,
    str(HERE.parent.parent.parent.parent /
        "week07-l08-graph-algorithms" / "snippets"),
)
import aeviz

np.random.seed(0)
aeviz.init_style()

# %% Instance: 4 depots x 4 days
LOCS = ["A", "B", "C", "D"]
DAYS = [1, 2, 3, 4]

# Surplus crates available at (location, day): source -> node capacity.
# (Sized generously so the bottleneck is the piggy-back routing, not the supply.)
SURPLUS = {
    ("A", 1): 18,
    ("B", 1): 14,
    ("D", 1): 12,
    ("A", 2): 10,
}

# Demand for crates at (location, day): node -> sink capacity (unmet demand).
# (Sized so total demand >= deliverable max flow, i.e. some shortage remains.)
DEMAND = {
    ("C", 2): 12,
    ("D", 3): 12,
    ("C", 3): 10,
    ("B", 4): 12,
    ("D", 4): 14,
}

# Inter-day arcs. Two kinds, both modelled the same way (a capacitated arc
# from (u, d) to (v, d+1)):
#   * "hold": the empty crates simply stay at depot u overnight (u == v).
#   * "truck": empties piggy-back on a truck that drives u -> v on that day.
HOLD_CAP = 12               # how many crates a depot can stockpile overnight
TRUCK_EAST = 8              # eastbound trucks: more frequent in this scenario
TRUCK_WEST = 4              # westbound trucks: less frequent (asymmetric)

EAST_PAIRS = [("A", "B"), ("B", "C"), ("C", "D")]
WEST_PAIRS = [("B", "A"), ("C", "B"), ("D", "C")]

PIGGY = {}   # (u, d, v, d+1) -> capacity
for d in DAYS[:-1]:
    for x in LOCS:
        PIGGY[(x, d, x, d + 1)] = HOLD_CAP
    for u, v in EAST_PAIRS:
        PIGGY[(u, d, v, d + 1)] = TRUCK_EAST
    for u, v in WEST_PAIRS:
        PIGGY[(u, d, v, d + 1)] = TRUCK_WEST

# %% Build the time-expanded flow network
SRC = "SURPLUS"
SNK = "SHORTAGE"
G = nx.DiGraph()
G.add_node(SRC)
G.add_node(SNK)
for x in LOCS:
    for d in DAYS:
        G.add_node((x, d))
for (x, d), cap in SURPLUS.items():
    G.add_edge(SRC, (x, d), capacity=cap)
for (x, d), cap in DEMAND.items():
    G.add_edge((x, d), SNK, capacity=cap)
for (u, du, v, dv), cap in PIGGY.items():
    G.add_edge((u, du), (v, dv), capacity=cap)

# %% Solve
total_surplus = sum(SURPLUS.values())
total_demand = sum(DEMAND.values())
flow_value, flow_dict = nx.maximum_flow(G, SRC, SNK)
cut_value, (S_side, T_side) = nx.minimum_cut(G, SRC, SNK)
assert cut_value == flow_value

# Per-arc flow
piggy_flow = {key: flow_dict[(key[0], key[1])][(key[2], key[3])]
              for key in PIGGY}
saturated_piggy = [k for k in PIGGY if piggy_flow[k] == PIGGY[k]]

# Min-cut edges that fall on piggy-back arcs (the interesting bottleneck).
cut_piggy = [k for k in PIGGY
             if (k[0], k[1]) in S_side and (k[2], k[3]) in T_side]
# Source/sink arcs in the cut (less interesting, but record for completeness).
cut_source = [(x, d) for (x, d), cap in SURPLUS.items()
              if SRC in S_side and (x, d) in T_side]
cut_sink = [(x, d) for (x, d), cap in DEMAND.items()
            if (x, d) in S_side and SNK in T_side]

print("=== Crate redistribution: max flow on a time-expanded graph ===")
print(f"locations: {LOCS}   days: {DAYS}")
print(f"total surplus crates: {total_surplus}")
print(f"total demand for crates: {total_demand}")
print(f"max flow (crates delivered on time): {flow_value}")
print(f"min cut value: {cut_value}")
print(f"stranded surplus: {total_surplus - flow_value}")
print(f"unmet demand (delayed): {total_demand - flow_value}")
print(f"\npiggy-back arcs (flow / cap), saturated marked:")
for k in PIGGY:
    u, du, v, dv = k
    mark = "  <- saturated" if k in saturated_piggy else ""
    print(f"  ({u}{du})->({v}{dv}): {piggy_flow[k]}/{PIGGY[k]}{mark}")
print(f"\nmin cut piggy arcs: {[f'({u}{du})->({v}{dv})' for (u,du,v,dv) in cut_piggy]}")
print(f"min cut source arcs: {cut_source}")
print(f"min cut sink arcs:   {cut_sink}")

# %% Positions: grid of (location row) x (day column), SURPLUS to the upper-left
# and SHORTAGE to the lower-right of the grid, so the source/sink arcs fan out
# instead of crossing the grid like a starburst from the centre top/bottom.
X_DAY = {1: 1.0, 2: 4.5, 3: 8.0, 4: 11.5}
Y_LOC = {"A": 4.5, "B": 3.2, "C": 1.9, "D": 0.6}

POS = {(x, d): (X_DAY[d], Y_LOC[x]) for x in LOCS for d in DAYS}
POS[SRC] = (3.20, 6.5)
POS[SNK] = (10.20, -0.8)

# %% Drawing helpers (matches gallery_solve.py: pipe width = capacity, fill = flow)
import math
from matplotlib.patches import FancyArrowPatch

P = aeviz.PALETTE
NODE_FILL = P["node_face"]
NODE_EDGE = "#333333"
SRC_FILL = P["good"]
SNK_FILL = P["warn"]
LABEL_INK = P["ink"]
DARK_INK = "#16261c"
PIPE = "#73809a"        # capacity-pipe slate (matches gallery)
FILL = P["path"]        # active flow
SAT_FILL = P["accent"]  # saturated arc

FLOW_PT = 0.7           # linewidth (pt) per unit of flow/capacity
FLOW_RAD = 0.10         # arc curvature shared by pipe + fill
NODE_SIZE = 1200


def _flow_arc(ax, p0, p2, width, color, *, arrow, alpha=1.0, z=1.0,
              rad=FLOW_RAD, node_size=NODE_SIZE):
    """One curved arc with round caps; width is a matplotlib linewidth (pt).

    The arrowhead is rendered with head_length >> head_width so it stays POINTY
    even on thick pipes (default '-|>' becomes a stubby triangle once the
    linewidth grows -- looked obscene on capacities >= 10).
    """
    radius = math.sqrt(node_size) / 2.0
    style = "-|>,head_length=1.1,head_width=0.4" if arrow else "-"
    ax.add_patch(FancyArrowPatch(
        p0, p2, connectionstyle=f"arc3,rad={rad}",
        arrowstyle=style, mutation_scale=12 if arrow else 0,
        lw=width, color=color, alpha=alpha, shrinkA=radius, shrinkB=radius,
        zorder=z, capstyle="round", joinstyle="round"))


def _draw_capacity_only(ax, u, v, cap, *, rad=FLOW_RAD):
    """Faded capacity pipe (no flow drawn yet) for the instance figure."""
    _flow_arc(ax, POS[u], POS[v], FLOW_PT * cap, PIPE, arrow=True,
              alpha=0.85, z=1.0, rad=rad)


def _draw_flow(ax, u, v, flow, cap, *, rad=FLOW_RAD):
    """Pipe (capacity) + colored fill (flow). Saturated -> accent fill."""
    _flow_arc(ax, POS[u], POS[v], FLOW_PT * cap, PIPE,
              arrow=(flow == 0), alpha=0.85, z=1.0, rad=rad)
    if flow > 0:
        color = SAT_FILL if flow == cap else FILL
        _flow_arc(ax, POS[u], POS[v], FLOW_PT * flow, color,
                  arrow=True, z=2.0, rad=rad)


def _arc3_pos_at(p0, p2, rad, t):
    """Point on the matplotlib 'arc3,rad=r' quadratic Bezier at parameter t.

    matplotlib's control point is C = M + rad*(dy,-dx); the Bezier is
    B(t) = (1-t)^2 p0 + 2(1-t)t C + t^2 p2.
    Used to drop edge labels off the midpoint (t=1/3 here) so parallel
    diagonals on a dense grid stop colliding label-on-label.
    """
    import numpy as _np
    p0 = _np.asarray(p0, float); p2 = _np.asarray(p2, float)
    m = (p0 + p2) / 2.0
    dx, dy = p2 - p0
    c = m + rad * _np.array([dy, -dx])
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p2


def _edge_label(ax, u, v, text, *, color=None, rad=FLOW_RAD, t=0.5):
    lx, ly = _arc3_pos_at(POS[u], POS[v], rad, t)
    ax.text(lx, ly, text, fontsize=10, color=color or LABEL_INK,
            ha="center", va="center", bbox=aeviz._LABEL_BBOX, zorder=6)


def _draw_nodes(ax):
    grid_nodes = [(x, d) for x in LOCS for d in DAYS]
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=grid_nodes,
                           node_size=NODE_SIZE, node_color=NODE_FILL,
                           edgecolors=NODE_EDGE, linewidths=1.4)
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=[SRC], node_size=1700,
                           node_color=SRC_FILL, edgecolors=NODE_EDGE, linewidths=1.6)
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=[SNK], node_size=1700,
                           node_color=SNK_FILL, edgecolors=NODE_EDGE, linewidths=1.6)
    grid_labels = {(x, d): f"{x}{d}" for x in LOCS for d in DAYS}
    nx.draw_networkx_labels(G, POS, labels=grid_labels, ax=ax,
                            font_size=10, font_weight="bold", font_color="white")
    nx.draw_networkx_labels(G, POS, labels={SRC: "surplus"}, ax=ax,
                            font_size=10, font_weight="bold", font_color="white")
    nx.draw_networkx_labels(G, POS, labels={SNK: "shortage"}, ax=ax,
                            font_size=10, font_weight="bold", font_color="white")
    # Day column headers across the top.
    for d, xc in X_DAY.items():
        ax.text(xc, 5.55, f"Day {d}", ha="center", fontsize=13,
                color=LABEL_INK, fontweight="bold")


def _frame(ax, title):
    ax.set_title(title, fontsize=14)
    # Hug the content tightly: x covers the grid (cols at 1.0..8.8 plus node
    # halos) and y covers SHORTAGE at the bottom up to SURPLUS at the top.
    # Wider limits were pushing big transparent margins into save_aligned's
    # tight bbox, which then made the figure render small inside the slide
    # column.
    ax.set_xlim(-0.3, 12.5)
    ax.set_ylim(-1.4, 7.1)
    ax.set_aspect("equal")
    ax.axis("off")


# %% Figure 1: the instance (capacities only)
fig_net, ax = plt.subplots(figsize=(12.8, 8.5))

# Inter-day piggy-back arcs: faded grey pipes whose THICKNESS encodes capacity.
for (u, du, v, dv), cap in PIGGY.items():
    _draw_capacity_only(ax, (u, du), (v, dv), cap)
    _edge_label(ax, (u, du), (v, dv), str(cap), color=P["weight"], t=1/3)

# Source/sink arcs in their own colors (still pipe-width = capacity).
for (x, d), cap in SURPLUS.items():
    _flow_arc(ax, POS[SRC], POS[(x, d)], FLOW_PT * cap, P["good"],
              arrow=True, alpha=0.9, z=1.2, rad=FLOW_RAD)
    _edge_label(ax, SRC, (x, d), f"+{cap}", color=P["good"])
for (x, d), cap in DEMAND.items():
    _flow_arc(ax, POS[(x, d)], POS[SNK], FLOW_PT * cap, P["accent"],
              arrow=True, alpha=0.9, z=1.2, rad=FLOW_RAD)
    _edge_label(ax, (x, d), SNK, f"-{cap}", color=P["accent"])

_draw_nodes(ax)
_frame(ax, "")

# %% Figure 2: the max-flow solution
fig_flow, ax = plt.subplots(figsize=(12.8, 8.5))

for (u, du, v, dv), cap in PIGGY.items():
    f = piggy_flow[(u, du, v, dv)]
    _draw_flow(ax, (u, du), (v, dv), f, cap)
    _edge_label(ax, (u, du), (v, dv), f"{f}/{cap}", color=P["weight"], t=1/3)

for (x, d), cap in SURPLUS.items():
    f = flow_dict[SRC][(x, d)]
    _flow_arc(ax, POS[SRC], POS[(x, d)], FLOW_PT * cap, PIPE,
              arrow=(f == 0), alpha=0.85, z=1.0, rad=FLOW_RAD)
    if f > 0:
        color = SAT_FILL if f == cap else P["good"]
        _flow_arc(ax, POS[SRC], POS[(x, d)], FLOW_PT * f, color,
                  arrow=True, z=2.0, rad=FLOW_RAD)
    _edge_label(ax, SRC, (x, d), f"{f}/{cap}", color=P["good"])

for (x, d), cap in DEMAND.items():
    f = flow_dict[(x, d)][SNK]
    _flow_arc(ax, POS[(x, d)], POS[SNK], FLOW_PT * cap, PIPE,
              arrow=(f == 0), alpha=0.85, z=1.0, rad=FLOW_RAD)
    if f > 0:
        color = SAT_FILL if f == cap else P["accent"]
        _flow_arc(ax, POS[(x, d)], POS[SNK], FLOW_PT * f, color,
                  arrow=True, z=2.0, rad=FLOW_RAD)
    _edge_label(ax, (x, d), SNK, f"{f}/{cap}", color=P["accent"])

_draw_nodes(ax)
_frame(ax, "")

# %% Save aligned (so the two frames overlay pixel-for-pixel in an r-stack)
out = aeviz.save_aligned([
    (fig_net, str(ASSETS / "crates_network")),
    (fig_flow, str(ASSETS / "crates_flow")),
])
print("\nwrote:", out)
