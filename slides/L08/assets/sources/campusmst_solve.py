"""Minimum spanning tree on a campus: cheapest fiber backbone connecting every building.

What this file does: places nine buildings on a campus map and asks the MST
question for L08. Every pair of buildings could in principle be trenched and
fibered; cost is straight-line km of trench. Goal: lay the fewest meters of
fiber so every building reaches the central data center. Solves with Kruskal /
Prim / Boruvka (asserting they agree), and draws two slide-ready figures (the
candidate trenches, then the MST). Non-goal: bandwidth/throughput, redundancy,
Steiner points.

Why it exists: covers lecture plan item 6.2 (MST as a connection question), the
counterpart to the max-flow logistics example. The wind-farm framing was
retired together with the wind-farm flow example; this campus framing tells the
same MST story on the same picture but stands on its own.

How to run:
    python solve.py   # writes 01_network.{png,svg}, 02_mst.{png,svg}
    # if `import networkx` fails: conda run -n mo312 python solve.py
"""

# %% Imports and deterministic, headless setup
import math
import sys

import matplotlib

matplotlib.use("Agg")  # headless / deterministic raster + svg output

import matplotlib.pyplot as plt
import networkx as nx

import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "snippets"))

import aeviz

aeviz.init_style()

# %% ----------------------------------------------------------------------------
# Instance: eight buildings on a campus plus one central data center.
# Coordinates are hand-placed (km), not random, so the figure is recognizable
# and the MST has a clean radial shape. Geometry is inherited from the earlier
# wind-farm MST instance so the same picture keeps working on the slide.
HUB = "DC"  # central data center / network core

BUILDINGS = {
    "B1": (1.0, 7.0),
    "B2": (3.0, 8.0),
    "B3": (2.0, 5.0),
    "B4": (4.0, 5.5),
    "B5": (1.5, 3.0),
    "B6": (3.5, 2.5),
    "B7": (6.0, 6.5),
    "B8": (6.5, 3.5),
}

POS = dict(BUILDINGS)
POS[HUB] = (9.0, 5.0)  # data center sits to the east

LABEL = {**{b: b for b in BUILDINGS}, HUB: "DC"}

COST_PER_KM = 1.0  # trenching cost is proportional to length; report raw km


# %% Build the complete Euclidean graph over buildings + data center
def euclid(p: tuple[float, float], q: tuple[float, float]) -> float:
    return math.hypot(p[0] - q[0], p[1] - q[1])


SITES = list(BUILDINGS) + [HUB]
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

assert MST.number_of_edges() == len(SITES) - 1, "MST does not have n-1 edges"
assert nx.is_connected(MST), "MST does not connect all sites"

# %% Print the stdout summary
print("=== Campus MST (cheapest fiber backbone to the data center) ===")
print(f"sites: {len(SITES)} ({len(BUILDINGS)} buildings + data center)   "
      f"candidate trenches: {G.number_of_edges()}")
print("total trench length agrees across kruskal / prim / boruvka:")
for alg, tot in totals.items():
    print(f"  {alg:8s}  {tot:7.2f} km")
print(f"MST edges ({MST.number_of_edges()} = {len(SITES)} sites - 1), cost order:")
for u, v, d in sorted(MST.edges(data=True), key=lambda e: e[2]["weight"]):
    print(f"  {u}-{v}   {d['weight']:5.2f} km")
print(f"total trench length: {MST_TOTAL:.2f} km")

# %% Shared drawing helpers
NODE_FILL = aeviz.PALETTE["node_face"]   # navy building fill, light text on top
NODE_EDGE = aeviz.PALETTE["node_edge"]   # light-blue node ring (reads on dark)
NODE_TEXT = aeviz.PALETTE["ink"]         # light node labels / annotations
HUB_FILL = aeviz.PALETTE["good"]         # green data center, semantically distinct
GRAY = aeviz.PALETTE["faded_dark"]       # neutral candidate trenches
BOLD = aeviz.PALETTE["path"]             # blue for the chosen tree


def _draw_nodes(ax):
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=list(BUILDINGS), node_size=1300,
                           node_color=NODE_FILL, edgecolors=NODE_EDGE, linewidths=1.6)
    nx.draw_networkx_nodes(G, POS, ax=ax, nodelist=[HUB], node_size=1500,
                           node_color=HUB_FILL, edgecolors=NODE_EDGE, linewidths=1.6)
    nx.draw_networkx_labels(
        G, POS, labels={HUB: "DC"}, ax=ax, font_size=10,
        font_weight="bold", font_color="#16261c")
    nx.draw_networkx_labels(
        G, POS, labels={n: LABEL[n] for n in BUILDINGS}, ax=ax, font_size=10,
        font_weight="bold", font_color=NODE_TEXT)
    ax.annotate("data center", POS[HUB], textcoords="offset points",
                xytext=(0, 24), ha="center", fontsize=9, color=NODE_TEXT)


def _frame(ax, title):
    ax.set_title(title, fontsize=13)
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(1.0, 9.5)
    ax.set_aspect("equal")
    ax.axis("off")


def km_label(u: str, v: str) -> str:
    return f"{euclid(POS[u], POS[v]):.1f}"


# %% Figure 1: the instance (all candidate trenches, faded, no lengths yet)
fig_net, ax = plt.subplots(figsize=(8.5, 6.0))
nx.draw_networkx_edges(G, POS, ax=ax, edgelist=list(G.edges()),
                       edge_color=GRAY, width=1.0, alpha=0.6)
_draw_nodes(ax)
_frame(ax, "Campus: all candidate fiber trenches (cost = length in km)")
cand_handle, = ax.plot([], [], color=GRAY, lw=1.0, label="candidate trench")
aeviz.legend_outside(ax, [cand_handle], ["candidate trench"],
                     loc="upper left", fontsize=9)

# %% Figure 2: the MST, bold over the faded non-tree trenches
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
mst_handle, = ax.plot([], [], color=BOLD, lw=3.2, label="chosen trench (MST)")
aeviz.legend_outside(ax, [mst_handle], ["chosen trench (MST)"],
                     loc="upper left", fontsize=9)
_frame(ax, f"Minimum spanning tree: {MST_TOTAL:.1f} km of fiber (lengths in km)")

# Crop both frames to one common bbox so the campus sits at identical pixels
# across the .r-stack overlay.
aeviz.save_aligned([(fig_net, "campusmst_network"), (fig_mst, "campusmst_mst")])

print("\nwrote campusmst_network.{png,svg}, campusmst_mst.{png,svg}")
