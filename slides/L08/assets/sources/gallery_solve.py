"""
Problem gallery for the L08 graph-algorithm lecture (sections 2 and the 3.1 /
4.1 / 5.1 / 5.3 / 6.1 definition figures).

What this file contains
-----------------------
Concept slide art for the six problem families: (a) an abstract glyph per
family (from glyphs.py), (b) a small labeled worked example per family whose
highlighted answer is actually computed with networkx and asserted, and (c) an
overview grid arranging the six glyphs (the section-2 "what we will cover"
slide). The labeled examples double as the per-pillar definition figures.
Non-goal: these are figures, not a solved real-world scenario; the only "solve"
is the honest tiny instance behind each definition example.

Why it exists
-------------
Section 2 opens with the gallery grid; each pillar opens with its definition
figure. This pack produces both from one consistent visual style.

How to run
----------
    python solve.py          # writes all glyph / example / grid PNGs + SVGs
    # if a bare import fails: conda run -n mo312 python solve.py

When it would change
--------------------
Add/retune a family, change the canonical instance for a definition figure, or
restyle the glyphs (edit glyphs.py, the shared mark source).
"""

# %%
import math
import sys
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import FancyArrowPatch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # -> snippets/
import aeviz  # noqa: E402
import glyphs  # noqa: E402  (local: the shared glyph painters)

glyphs.init()
P = aeviz.PALETTE
GOOD, WARN, PATH, ACCENT = P["good"], P["warn"], P["path"], P["accent"]
DOT, FADE = P["settled"], P["faded"]
NODE_EDGE = "#333333"


def save_close(fig, stem):
    """Write PNG + SVG via aeviz, then close the figure."""
    aeviz.save(fig, stem)
    plt.close(fig)


# %% Small shared drawing helper for the labeled examples ---------------------
def draw_graph(ax, G, pos, *, directed, hi_edges, edge_labels=None,
               node_colors=None, node_size=900, rad=0.0):
    """Draw a small instance: faded base edges + highlighted solution edges."""
    base = [e for e in G.edges() if e not in hi_edges
            and (e[1], e[0]) not in hi_edges]
    arrow_kw = (dict(arrowsize=18, min_target_margin=18,
                     connectionstyle=f"arc3,rad={rad}") if directed else {})
    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=base, edge_color=FADE,
                           width=2.0, arrows=directed, node_size=node_size,
                           **arrow_kw)
    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=list(hi_edges),
                           edge_color=PATH, width=4.4, arrows=directed,
                           node_size=node_size, **arrow_kw)
    if node_colors is None:
        node_colors = {n: DOT for n in G.nodes}
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_size,
                           node_color=[node_colors[n] for n in G.nodes],
                           edgecolors=NODE_EDGE, linewidths=1.5)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=11, font_weight="bold",
                            font_color="white")
    if edge_labels:
        aeviz.straight_edge_labels(ax, pos, edge_labels, font_size=10)
    ax.axis("off")
    ax.margins(0.14)


def st_colors(G, s, t):
    c = {n: DOT for n in G.nodes}
    c[s] = GOOD
    c[t] = WARN
    return c


# %% Flow-network drawing: width carries the quantity --------------------------
# Shared rule for the two flow definition figures (31 max flow, 41 min-cost):
# each arc is a grey "pipe" whose width = capacity, with a colored "fill" on top
# whose width = the flow actually pushed. An unused arc is an empty grey pipe; a
# fully used (saturated) arc has its fill cover the pipe. One scale (points of
# linewidth per unit) is shared so "thicker = more flow" reads the same in both.
FLOW_PT = 2.0        # linewidth points per unit of flow / capacity
PIPE = "#73809a"     # capacity-pipe slate: light enough to read on the dark slide
FLOW_RAD = 0.12      # arc curvature; pipe and fill share it so they overlay


def _flow_arc(ax, p0, p2, width, color, *, arrow, alpha=1.0, node_size=900,
              z=1.0, rad=FLOW_RAD):
    """One curved arc with round caps. width is a matplotlib linewidth (pt).

    shrink ends land the arrow on the node boundary. A scatter node of area
    `node_size` (pt^2) has on-screen radius ~ sqrt(node_size)/2 pt; matching the
    shrink to that radius makes the head touch the disk in vector renderers
    (browsers clip nothing for us), instead of floating short of it.
    """
    radius = math.sqrt(node_size) / 2.0
    ax.add_patch(FancyArrowPatch(
        p0, p2, connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>" if arrow else "-", mutation_scale=16 if arrow else 0,
        lw=width, color=color, alpha=alpha, shrinkA=radius, shrinkB=radius,
        zorder=z, capstyle="round", joinstyle="round"))


def draw_flow_network(ax, G, pos, arc_data, *, node_colors, edge_labels,
                      node_size=900, saturate_color=False, pipe_alpha=0.9,
                      rad=None):
    """Draw a capacitated flow: pipe width = capacity, fill width = flow.

    arc_data: iterable of (u, v, flow, cap). With saturate_color=True a fully
    used arc (flow == cap) is filled in ACCENT instead of PATH, flagging the
    binding arcs that the min-cut slide later highlights. rad: optional
    {(u, v): curvature} to bow individual arcs apart (e.g. crossing diagonals);
    arcs not listed use FLOW_RAD.
    """
    rad = rad or {}
    for u, v, flow, cap in arc_data:
        r = rad.get((u, v), FLOW_RAD)
        _flow_arc(ax, pos[u], pos[v], FLOW_PT * cap, PIPE, arrow=(flow == 0),
                  alpha=pipe_alpha, node_size=node_size, z=1.0, rad=r)
        if flow > 0:
            color = ACCENT if (saturate_color and flow == cap) else PATH
            _flow_arc(ax, pos[u], pos[v], FLOW_PT * flow, color, arrow=True,
                      node_size=node_size, z=2.0, rad=r)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_size,
                           node_color=[node_colors[n] for n in G.nodes],
                           edgecolors=NODE_EDGE, linewidths=1.5)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=11, font_weight="bold",
                            font_color="white")
    for (u, v), txt in edge_labels.items():
        lx, ly = aeviz._arc3_label_pos(pos[u], pos[v], rad.get((u, v), FLOW_RAD))
        ax.text(lx, ly, txt, fontsize=10, color=P["ink"], ha="center",
                va="center", bbox=aeviz._LABEL_BBOX, zorder=6)
    ax.axis("off")
    ax.margins(0.14)
    ax.set_aspect("equal")


# %% =========================================================================
# WORKED EXAMPLES (each solved by networkx; the highlighted answer is asserted)
# ============================================================================
summary = []

# %% 11 shortest path --------------------------------------------------------
spG = nx.Graph()
sp_edges = [("s", "a", 2), ("s", "b", 5), ("a", "b", 1), ("a", "c", 6),
            ("b", "c", 2), ("b", "t", 7), ("c", "t", 1)]
for u, v, w in sp_edges:
    spG.add_edge(u, v, weight=w)
sp_pos = {"s": (0, 0.5), "a": (1, 1), "b": (1, 0), "c": (2, 0.7), "t": (3, 0.4)}
sp_path = nx.dijkstra_path(spG, "s", "t", weight="weight")
sp_len = nx.dijkstra_path_length(spG, "s", "t", weight="weight")
assert sp_path == ["s", "a", "b", "c", "t"] and sp_len == 6, (sp_path, sp_len)
sp_hi = set(zip(sp_path, sp_path[1:]))
fig, ax = plt.subplots(figsize=(5.4, 3.4))
draw_graph(ax, spG, sp_pos, directed=False, hi_edges=sp_hi,
           edge_labels={(u, v): w for u, v, w in sp_edges},
           node_colors=st_colors(spG, "s", "t"))
ax.set_title(f"Shortest path s to t: length {sp_len}", fontsize=13)
save_close(fig, "11_shortest_path_example")
summary.append(("shortest path", f"s->a->b->c->t, length {sp_len}"))

# %% 21 matching (bipartite) -------------------------------------------------
mG = nx.Graph()
L = ["w1", "w2", "w3"]   # workers
Rr = ["j1", "j2", "j3"]  # jobs
m_edges = [("w1", "j1"), ("w1", "j2"), ("w2", "j2"), ("w2", "j3"),
           ("w3", "j3")]
mG.add_nodes_from(L, bipartite=0)
mG.add_nodes_from(Rr, bipartite=1)
mG.add_edges_from(m_edges)
m_match = nx.algorithms.bipartite.hopcroft_karp_matching(mG, top_nodes=L)
m_pairs = {frozenset((u, v)) for u, v in m_match.items() if u in L}
assert len(m_pairs) == 3, m_pairs  # perfect matching exists
m_hi = {tuple(p) for p in m_pairs}
m_pos = {"w1": (0, 2), "w2": (0, 1), "w3": (0, 0),
         "j1": (1.3, 2), "j2": (1.3, 1), "j3": (1.3, 0)}
m_colors = {n: GOOD for n in L}
m_colors.update({n: WARN for n in Rr})
fig, ax = plt.subplots(figsize=(4.2, 3.6))
draw_graph(ax, mG, m_pos, directed=False, hi_edges=m_hi, node_colors=m_colors)
ax.set_title(f"Maximum matching: {len(m_pairs)} pairs", fontsize=13)
save_close(fig, "21_matching_example")
summary.append(("matching", f"{len(m_pairs)} matched pairs (perfect)"))

# tiny general (non-bipartite) hint: a 5-cycle, max matching = 2 edges
gG = nx.cycle_graph(["p", "q", "r", "x", "y"])
g_match = nx.max_weight_matching(gG, maxcardinality=True)
assert len(g_match) == 2, g_match
g_hi = {tuple(e) for e in g_match}
g_pos = {n: (math.cos(2 * math.pi * i / 5 + math.pi / 2),
             math.sin(2 * math.pi * i / 5 + math.pi / 2))
         for i, n in enumerate(["p", "q", "r", "x", "y"])}
fig, ax = plt.subplots(figsize=(3.6, 3.6))
draw_graph(ax, gG, g_pos, directed=False, hi_edges=g_hi,
           node_colors={n: DOT for n in gG.nodes}, node_size=750)
ax.set_title("General graph: max matching = 2\n(odd cycle, one node unmatched)",
             fontsize=11)
save_close(fig, "22_matching_general_example")
summary.append(("matching (general)", "5-cycle, max matching 2 edges"))

# %% 31 max flow -------------------------------------------------------------
# Tuned so the min cut (reused in 51) is a genuine middle bottleneck, not just
# the arcs into t: max flow = 5, min cut splits {s,b} | {a,t}.
fG = nx.DiGraph()
f_arcs = [("s", "a", 3), ("s", "b", 4), ("a", "b", 3), ("a", "t", 5),
          ("b", "t", 2)]
for u, v, c in f_arcs:
    fG.add_edge(u, v, capacity=c)
# Hand-placed so the s-side cluster {s,b} sits lower-left and {a,t} upper-right.
f_pos = {"s": (0, 0.35), "b": (0.75, -0.25), "a": (1.3, 1.05), "t": (2.1, 0.55)}
f_val, f_dict = nx.maximum_flow(fG, "s", "t")
assert f_val == 5, f_val
# Pipe width = capacity, fill width = flow; saturated arcs filled orange.
f_data = [(u, v, f_dict[u][v], c) for u, v, c in f_arcs]
f_lbls = {(u, v): f"{f_dict[u][v]}/{c}" for u, v, c in f_arcs}
fig, ax = plt.subplots(figsize=(5.0, 3.4))
draw_flow_network(ax, fG, f_pos, f_data, node_colors=st_colors(fG, "s", "t"),
                  edge_labels=f_lbls, saturate_color=True)
save_close(fig, "31_maxflow_example")
summary.append(("max flow", f"value {f_val}, saturated arcs bold"))

# %% 41 min-cost flow --------------------------------------------------------
# Transport: 2 suppliers -> 3 customers, per-arc COST and CAPACITY. Both
# constraint families are visible: node badges show supply/demand (the balance
# constraint), the grey pipe shows capacity (the bound). Two things make the
# optimum interesting:
#   (1) a capacity BINDS -- S1->D1 is the cheapest arc into D1 (cost 1) but caps
#       at 2 while D1 needs 3, forcing D1's last unit onto the pricier S2->D1;
#   (2) a TRANSSHIPMENT edge between customers is used -- D3 is served not by the
#       expensive direct S2->D3 (cost 6, left as an empty pipe) but by routing
#       extra units into D2 and forwarding them D2->D3 (cost 1). So D2 receives
#       more than its own demand and re-ships the surplus to D3.
# The saturated (binding) arc is filled orange, as on max flow.
c_supply = {"S1": 5, "S2": 3}
c_demand = {"D1": 3, "D2": 2, "D3": 3}
cG = nx.DiGraph()
for n, b in c_supply.items():
    cG.add_node(n, demand=-b)
for n, b in c_demand.items():
    cG.add_node(n, demand=b)
c_arcs = [("S1", "D1", 1, 2), ("S2", "D1", 4, 3),    # D1: cheap arc caps at 2
          ("S1", "D2", 2, 5), ("S2", "D2", 1, 4),    # feed the D2 hub
          ("S2", "D3", 6, 5), ("D2", "D3", 1, 4)]    # direct (dear) vs transship
for u, v, w, cap in c_arcs:
    cG.add_edge(u, v, weight=w, capacity=cap)
c_flow = nx.min_cost_flow(cG)
c_cost = nx.cost_of_flow(cG, c_flow)
# Optimal: S1->D1 2@1 (capped), S2->D1 1@4, S1->D2 3@2, S2->D2 2@1, D2->D3 3@1,
# S2->D3 0@6 (unused). Cost 2+4+6+2+3 = 17.
assert c_cost == 17, c_cost
assert c_flow["S1"]["D1"] == 2, c_flow   # the cheap arc into D1 is capacity-bound
assert c_flow["D2"]["D3"] == 3, c_flow   # D3 served via transshipment, not direct
assert c_flow["S2"]["D3"] == 0, c_flow   # the expensive direct arc stays empty
# Landscape layout: suppliers left, the two end customers far right, and the D2
# hub set CENTRALLY between them -- so the relay D2->D3 reads as a left-to-right
# forwarding step, and the figure stays wide (matches the max-flow aspect).
c_pos = {"S1": (0, 1.5), "S2": (0, 0.0),
         "D2": (1.75, 0.78), "D1": (3.3, 1.5), "D3": (3.3, 0.0)}
c_data = [(u, v, c_flow[u][v], cap) for u, v, w, cap in c_arcs]
c_lbls = {(u, v): f"{c_flow[u][v]} @{w}" for u, v, w, cap in c_arcs}
c_colors = {"S1": GOOD, "S2": GOOD, "D1": WARN, "D2": WARN, "D3": WARN}
# Straighten the two long horizontals (top S1->D1, bottom S2->D3) and bow the
# crossing diagonals apart so their labels don't pile up near the hub.
c_rad = {("S1", "D1"): 0.0, ("S2", "D3"): 0.0,
         ("S2", "D1"): -0.18, ("S1", "D2"): 0.22, ("D2", "D3"): 0.14}
fig, ax = plt.subplots(figsize=(6.6, 3.6))
draw_flow_network(ax, cG, c_pos, c_data, node_colors=c_colors,
                  edge_labels=c_lbls, pipe_alpha=0.5, rad=c_rad,
                  saturate_color=True)
# Supply/demand badges: +b (green) at sources on the left, -b (orange) at sinks
# on the right -- the node-balance constraint that forces the routing.
_sup_bbox = dict(boxstyle="round,pad=0.22", fc=(0.12, 0.30, 0.14, 0.94), ec="none")
_dem_bbox = dict(boxstyle="round,pad=0.22", fc=(0.42, 0.24, 0.06, 0.94), ec="none")
for n, b in c_supply.items():
    ax.text(c_pos[n][0] - 0.42, c_pos[n][1], f"+{b}", fontsize=11, color="white",
            ha="center", va="center", fontweight="bold", bbox=_sup_bbox, zorder=7)
for n, b in c_demand.items():
    ax.text(c_pos[n][0] + 0.42, c_pos[n][1], f"−{b}", fontsize=11,
            color="white", ha="center", va="center", fontweight="bold",
            bbox=_dem_bbox, zorder=7)
ax.margins(0.20)
save_close(fig, "41_mincostflow_example")
summary.append(("min-cost flow", f"min cost {c_cost}, D1 cap-bound + D2->D3 transship"))

# %% 51 min cut (reuse the max-flow network) ---------------------------------
cut_val, (Sset, Tset) = nx.minimum_cut(fG, "s", "t")
assert cut_val == f_val, (cut_val, f_val)  # max-flow = min-cut
cut_edges = {(u, v) for u, v, c in f_arcs if u in Sset and v in Tset}
fig, ax = plt.subplots(figsize=(5.0, 3.4))
# Shade the two sides with a dashed diagonal boundary. The layout puts the
# s-side cluster {s,b} lower-left and the t-side {a,t} upper-right, so a line
# from lower-right to upper-left separates them cleanly.
from matplotlib.patches import Polygon as _Poly  # noqa: E402
_x0, _x1, _y0, _y1 = -0.45, 2.45, -0.75, 1.45
# boundary line y = m*x + b chosen by hand to pass between the clusters
_m, _b = 1.05, -0.35
def _by(x):
    return _m * x + _b
ax.add_patch(_Poly([(_x0, _by(_x0)), (_x1, _by(_x1)), (_x1, _y1), (_x0, _y1)],
                   closed=True, facecolor=GOOD, alpha=0.10, ec="none", zorder=0))
ax.add_patch(_Poly([(_x0, _by(_x0)), (_x1, _by(_x1)), (_x1, _y0), (_x0, _y0)],
                   closed=True, facecolor=WARN, alpha=0.10, ec="none", zorder=0))
ax.plot([_x0, _x1], [_by(_x0), _by(_x1)], color=P["ink"], lw=1.6,
        ls=(0, (5, 4)), zorder=1)
ax.set_xlim(_x0, _x1)
ax.set_ylim(_y0, _y1)
base = [e for e in fG.edges() if e not in cut_edges]
nx.draw_networkx_edges(fG, f_pos, ax=ax, edgelist=base, edge_color=FADE,
                       width=2.0, arrows=True, arrowsize=16, node_size=900,
                       connectionstyle="arc3,rad=0.12", min_target_margin=16)
nx.draw_networkx_edges(fG, f_pos, ax=ax, edgelist=list(cut_edges),
                       edge_color=ACCENT, width=4.4, arrows=True, arrowsize=20,
                       node_size=900, connectionstyle="arc3,rad=0.12",
                       min_target_margin=18)
cut_colors = {n: (GOOD if n in Sset else WARN) for n in fG.nodes}
nx.draw_networkx_nodes(fG, f_pos, ax=ax, node_size=900,
                       node_color=[cut_colors[n] for n in fG.nodes],
                       edgecolors=NODE_EDGE, linewidths=1.5)
nx.draw_networkx_labels(fG, f_pos, ax=ax, font_size=11, font_weight="bold",
                        font_color="white")
cap_lbls = {e: f"cap {fG[e[0]][e[1]]['capacity']}" for e in cut_edges}
aeviz.straight_edge_labels(ax, f_pos, cap_lbls, font_size=10, color=ACCENT)
ax.set_title(f"Min cut = {cut_val} = max flow", fontsize=12)
ax.axis("off")
ax.margins(0.14)
save_close(fig, "51_mincut_example")
summary.append(("min cut", f"cut value {cut_val} = max flow {f_val}"))

# %% 61 MST ------------------------------------------------------------------
tG = nx.Graph()
t_edges = [("A", "B", 3), ("A", "C", 1), ("B", "C", 2), ("B", "D", 4),
           ("C", "D", 5), ("C", "E", 6), ("D", "E", 2)]
for u, v, w in t_edges:
    tG.add_edge(u, v, weight=w)
t_pos = {"A": (0, 1), "B": (1, 1.6), "C": (1, 0.3), "D": (2, 1.3),
         "E": (2.2, 0.1)}
MST = nx.minimum_spanning_tree(tG, algorithm="kruskal")
mst_w = sum(d["weight"] for *_, d in MST.edges(data=True))
# Optimal tree: A-C 1, B-C 2, D-E 2, B-D 4 = 9.
assert mst_w == 9, mst_w
mst_hi = {frozenset((u, v)) for u, v in MST.edges()}
mst_hi = {tuple(p) for p in mst_hi}
fig, ax = plt.subplots(figsize=(5.0, 3.4))
draw_graph(ax, tG, t_pos, directed=False, hi_edges=mst_hi,
           edge_labels={(u, v): w for u, v, w in t_edges},
           node_colors={n: DOT for n in tG.nodes})
ax.set_title(f"Minimum spanning tree: weight {mst_w}", fontsize=12)
save_close(fig, "61_mst_example")
summary.append(("MST", f"total weight {mst_w}"))


# %% =========================================================================
# ABSTRACT GLYPHS (one figure each)
# ============================================================================
GLYPH_FILES = {
    "shortest_path": "10_shortest_path_glyph",
    "matching": "20_matching_glyph",
    "maxflow": "30_maxflow_glyph",
    "mincostflow": "40_mincostflow_glyph",
    "mincut": "50_mincut_glyph",
    "mst": "60_mst_glyph",
}
for key, stem in GLYPH_FILES.items():
    _title, fn = glyphs.GLYPHS[key]
    fig, ax = plt.subplots(figsize=(2.4, 2.4))
    fn(ax)
    save_close(fig, stem)


# %% =========================================================================
# OVERVIEW GRID (section 2: "here is what we will cover")
# ============================================================================
fig, axes = plt.subplots(2, 3, figsize=(9.6, 6.6))
for ax, (key, (title, fn)) in zip(axes.flat, glyphs.GLYPHS.items()):
    fn(ax)
    ax.set_title(title, fontsize=14, pad=6, color=P["ink"])
fig.suptitle("Graph and network problems we will cover", fontsize=16,
             fontweight="bold", y=0.99)
fig.tight_layout(rect=(0, 0, 1, 0.97))
save_close(fig, "01_overview_grid")


# %% Stdout summary ----------------------------------------------------------
print("=== Problem gallery (L08 sections 2 / 3.1 / 4.1 / 5.1 / 5.3 / 6.1) ===")
print("Worked examples (networkx-verified answers):")
for name, ans in summary:
    print(f"  {name:18s}: {ans}")
print("\nMin-cost-flow detail:", {f"{u}->{v}": c_flow[u][v]
      for u, v, _w, _cap in c_arcs if c_flow[u][v] > 0}, f"= {c_cost}")
print("MST edges:", sorted((u, v, d["weight"])
      for u, v, d in MST.edges(data=True)), f"= {mst_w}")
print(f"\nGlyphs: {', '.join(GLYPH_FILES.values())}")
print("Grid: 01_overview_grid")
print("All figures written as PNG + SVG.")
