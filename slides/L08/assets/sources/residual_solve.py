# %%
"""
Residual graph and augmenting paths (Edmonds-Karp, hand-rolled) for L08.

What this contains:
    A tiny max-flow network (6 nodes) solved by a from-scratch Edmonds-Karp:
    BFS the residual graph for a shortest s-t path, push the bottleneck, update
    forward and backward residuals, repeat. The instance is chosen so the third
    augmenting path must traverse a BACKWARD residual arc (a flow cancellation),
    making the back-arc's purpose concrete. Each augmentation is exported as a
    coupled pair of frames: the flow on the original network, and the residual
    graph with the chosen path highlighted.
    Non-goal: not a fast/production max-flow, not a scenario example.

Why it exists:
    The conceptual heart of flow algorithms and the explicit loop back to
    shortest paths: an augmenting path is just an s-t path in the residual graph.
    The manual implementation IS the lesson, so we expose every residual state.

How to run:
    python solve.py      (env mo312: networkx 3.2.1, matplotlib, numpy, scipy)
    Emits 0N_stepN_flow.png / 0N_stepN_residual.png frame pairs, a final
    0N_final.png, SVGs for the clean frames, and a stdout augmentation log.

When to change:
    Edit CAP / POS to retarget the network or the geometry. The back-arc demo
    depends on the specific capacities; re-verify against nx.maximum_flow if you
    change them (the script asserts agreement on every run).
"""

import sys
from collections import deque

import matplotlib

matplotlib.use("Agg")  # headless, file-only rendering
import matplotlib.pyplot as plt
import networkx as nx

sys.path.insert(0, "/home/krupke/Cloud/Dropbox/Secretary/cases/"
                   "course-ae-ss26-internal/week07-l08-graph-algorithms/snippets")
import aeviz  # noqa: E402  (path injected above)

aeviz.init_style()

# %%
# --- Instance ---------------------------------------------------------------
# Clean LEFT-TO-RIGHT layered layout (four columns):
#     col 0 = s | col 1 = a (top) b (bottom) | col 2 = c (top) d (bottom) | col 3 = t.
# Capacities chosen (via a small offline search) so Edmonds-Karp needs exactly
# three augmentations and the third one routes through the backward arc c->a,
# cancelling flow that the greedy first path pushed along a->c.

CAP = {
    "s": {"a": 4, "b": 5},
    "a": {"c": 4, "d": 4},
    "b": {"c": 5, "d": 3},
    "c": {"t": 4},
    "d": {"t": 5},
}

# Hand-placed positions: four columns, generously spaced horizontally so the
# graph reads as left-to-right layers (not a compact diamond). Forward edges all
# advance left-to-right; the only right-to-left arcs are the residual back-arcs,
# which is exactly the teaching point.
POS = {
    "s": (0.0, 0.0),
    "a": (2.0, 1.0),
    "b": (2.0, -1.0),
    "c": (4.0, 1.0),
    "d": (4.0, -1.0),
    "t": (6.0, 0.0),
}

SOURCE, SINK = "s", "t"

# The K2,2 cross-pair between {a,b} and {c,d}: a->d (top->bottom) and b->c
# (bottom->top) inevitably cross. We draw them as gentle opposite curves so they
# bow apart instead of forming a hard X dead-center: a->d bows down, b->c bows up.
CURVED_FWD = {("a", "d"): -0.28, ("b", "c"): 0.28}

# Palette (colorblind-friendly, shared aeviz vocabulary).
C_FWD = aeviz.PALETTE["path"]      # forward residual capacity (solid blue)
C_BACK = aeviz.PALETTE["accent"]   # backward residual arc (dashed vermillion)
C_PATH = aeviz.PALETTE["warn"]     # highlighted augmenting path (amber halo)
C_FLOW = aeviz.PALETTE["good"]     # carried flow on the original network (green)
C_GRAY = aeviz.PALETTE["faded"]    # de-emphasized / empty
C_NODE = aeviz.PALETTE["node_face"]   # navy node fill on the dark slide
C_NODE_EDGE = aeviz.PALETTE["node_edge"]  # light-blue node ring
C_INK = aeviz.PALETTE["ink"]       # light foreground for text on dark
C_WEIGHT = aeviz.PALETTE["weight"] # gold flow/capacity labels
LABEL_BBOX_FC = (0.10, 0.14, 0.20, 0.85)  # translucent dark backing for labels


# %%
# --- Hand-rolled Edmonds-Karp -----------------------------------------------


def build_residual(cap):
    """Residual capacity dict: forward arcs = cap, reverse arcs start at 0."""
    res = {u: {} for u in cap}
    for u in cap:
        for v, c in cap[u].items():
            res.setdefault(u, {})[v] = c
            res.setdefault(v, {}).setdefault(u, 0)
    return res


def bfs_path(res, s, t):
    """Shortest (fewest-edges) s-t path over arcs with positive residual.

    Neighbors are visited in sorted order so the chosen paths are reproducible
    (BFS ties are otherwise resolved by dict insertion order). This determinism
    is what makes the back-arc augmentation a fixed teaching frame.
    """
    parent = {s: None}
    q = deque([s])
    while q:
        u = q.popleft()
        if u == t:
            break
        for v in sorted(res[u]):
            if res[u][v] > 0 and v not in parent:
                parent[v] = u
                q.append(v)
    if t not in parent:
        return None
    path = []
    v = t
    while v is not None:
        path.append(v)
        v = parent[v]
    return path[::-1]


def edmonds_karp(cap, s, t):
    """Run Edmonds-Karp, recording a snapshot before each augmentation.

    Returns (max_flow_value, snapshots). Each snapshot captures the residual
    graph the BFS searched, the path it found, the bottleneck, the resulting
    flow per original edge, and which path arcs were backward (cancellations).
    """
    res = build_residual(cap)
    flow = {u: {v: 0 for v in cap[u]} for u in cap}
    total = 0
    snapshots = []

    while True:
        path = bfs_path(res, s, t)
        if path is None:
            break
        # snapshot the residual graph BEFORE pushing flow along this path
        res_before = {u: dict(d) for u, d in res.items()}
        bottleneck = min(res[path[i]][path[i + 1]] for i in range(len(path) - 1))

        back_arcs = []
        for i in range(len(path) - 1):
            u, w = path[i], path[i + 1]
            res[u][w] -= bottleneck
            res[w][u] += bottleneck
            if cap.get(u, {}).get(w, 0) > 0:
                flow[u][w] += bottleneck          # forward edge: add flow
            else:
                flow[w][u] -= bottleneck          # backward arc: cancel flow
                back_arcs.append((u, w))
        total += bottleneck

        snapshots.append({
            "res_before": res_before,
            "path": path,
            "bottleneck": bottleneck,
            "back_arcs": back_arcs,
            "flow": {u: dict(d) for u, d in flow.items()},
            "total": total,
        })
    return total, snapshots


# %%
# --- Solve + cross-check ----------------------------------------------------

max_flow, snaps = edmonds_karp(CAP, SOURCE, SINK)

G = nx.DiGraph()
for u in CAP:
    for v, c in CAP[u].items():
        G.add_edge(u, v, capacity=c)
nx_value = nx.maximum_flow_value(G, SOURCE, SINK)
assert max_flow == nx_value, f"EK {max_flow} != nx {nx_value}"

print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, "
      f"source {SOURCE} -> sink {SINK}")
print(f"Edmonds-Karp augmentations: {len(snaps)}\n")
for i, s in enumerate(snaps, 1):
    arrow = " -> ".join(s["path"])
    back = ""
    if s["back_arcs"]:
        used = ", ".join(f"{u}->{w}" for (u, w) in s["back_arcs"])
        cancels = ", ".join(f"{w}->{u}" for (u, w) in s["back_arcs"])
        back = f"   [back-arc {used} cancels flow on {cancels}]"
    print(f"  step {i}: {arrow}   bottleneck {s['bottleneck']}   "
          f"flow now {s['total']}{back}")
print(f"\nMax flow value: {max_flow}  (networkx agrees: {nx_value})")


# %%
# --- Drawing helpers --------------------------------------------------------


def _node_colors(g):
    return [
        C_FLOW if n == SOURCE else C_FWD if n == SINK else C_NODE
        for n in g.nodes()
    ]


def _draw_nodes(ax, nodes):
    nx.draw_networkx_nodes(nodes, POS, ax=ax, node_size=900,
                           node_color=_node_colors(nodes),
                           edgecolors=C_NODE_EDGE, linewidths=1.4)
    nx.draw_networkx_labels(nodes, POS, ax=ax, font_size=13,
                            font_weight="bold", font_color=C_INK)


def _fwd_rad(u, v):
    """Curvature for a forward edge: bow the K2,2 cross-pair apart, else straight."""
    return CURVED_FWD.get((u, v), 0.0)


def _arc_mid(u, v, rad, lift=0.0):
    """Midpoint of matplotlib's 'arc3,rad' Bezier, optionally lifted off the arc.

    `lift` adds extra curvature only for label placement, so a label sits just
    outside its arc instead of sitting on top of the line.
    """
    return aeviz._arc3_label_pos(POS[u], POS[v], rad + lift)


def draw_flow(ax, flow, title):
    """Original network with flow/capacity labels; carried edges in green."""
    ax.set_title(title, fontsize=12)
    straight_labels = {}
    for u in CAP:
        for v, c in CAP[u].items():
            f = flow[u][v]
            color = C_FLOW if f > 0 else C_GRAY
            width = 3.2 if f > 0 else 1.4
            rad = _fwd_rad(u, v)
            nx.draw_networkx_edges(
                G, POS, ax=ax, edgelist=[(u, v)], width=width,
                edge_color=color, arrows=True, arrowsize=18,
                arrowstyle="-|>", node_size=900,
                connectionstyle=f"arc3,rad={rad}",
                min_source_margin=16, min_target_margin=16,
            )
            label = f"{f}/{c}"
            if rad:  # curved cross-edge: place label on the bowed arc midpoint
                mx, my = _arc_mid(u, v, rad)
                ax.text(mx, my, label, fontsize=10, ha="center", va="center",
                        color=C_WEIGHT,
                        bbox=dict(boxstyle="round,pad=0.12", fc=LABEL_BBOX_FC,
                                  ec="none", alpha=0.9))
            else:
                straight_labels[(u, v)] = label
    aeviz.straight_edge_labels(ax, POS, straight_labels, font_size=10,
                               color=C_WEIGHT)
    _draw_nodes(ax, G)
    ax.axis("off")
    ax.margins(0.10)


def draw_residual(ax, res, path, title):
    """Residual graph: forward residual solid, backward arcs dashed, path bold.

    Only arcs with positive residual are drawn. The augmenting path (an s-t path
    in THIS graph) is highlighted in amber underneath. Forward edges advance
    left-to-right; backward arcs curve back right-to-left -- the teaching point.
    """
    ax.set_title(title, fontsize=12)
    rg = nx.DiGraph()
    rg.add_nodes_from(POS)
    path_arcs = set(zip(path, path[1:])) if path else set()
    straight_labels = {}

    for u in res:
        for v, c in res[u].items():
            if c <= 0:
                continue
            is_forward = CAP.get(u, {}).get(v, 0) > 0
            on_path = (u, v) in path_arcs
            # forward edges: straight, or bowed for the K2,2 cross-pair.
            # backward arcs: also straight (no curve). A curved back-arc bows out
            # by a frame-dependent amount, so it shifts the graph's position
            # within each tight-cropped frame and the layout jumps between the
            # r-stack animation steps. The dashed vermillion style already
            # distinguishes a back-arc from its forward partner.
            rad = _fwd_rad(u, v)
            cstyle = f"arc3,rad={rad}"
            if on_path:  # amber halo underneath
                nx.draw_networkx_edges(
                    rg, POS, ax=ax, edgelist=[(u, v)], width=8.0,
                    edge_color=C_PATH, alpha=0.55, arrows=True, arrowsize=1,
                    arrowstyle="-", node_size=900, connectionstyle=cstyle,
                    min_source_margin=16, min_target_margin=16,
                )
            color = C_FWD if is_forward else C_BACK
            style = "solid" if is_forward else (4, (5, 3))
            nx.draw_networkx_edges(
                rg, POS, ax=ax, edgelist=[(u, v)], width=2.6,
                edge_color=color, style=style, arrows=True, arrowsize=18,
                arrowstyle="-|>", node_size=900, connectionstyle=cstyle,
                min_source_margin=16, min_target_margin=16,
            )
            # straight forward edges -> batch into nx label routine; curved
            # forward + curved backward arcs -> place on their Bezier midpoint.
            if is_forward and not rad:
                straight_labels[(u, v)] = str(c)
            else:
                lift = 0.10 if not is_forward else 0.0  # push back-arc labels out
                mx, my = _arc_mid(u, v, rad, lift=lift)
                ax.annotate(
                    str(c), xy=(mx, my), fontsize=9.5, ha="center", va="center",
                    color=color, bbox=dict(boxstyle="round,pad=0.1",
                                           fc=LABEL_BBOX_FC, ec="none", alpha=0.9),
                )
    aeviz.straight_edge_labels(ax, POS, straight_labels, font_size=9.5,
                               color=C_FWD)
    _draw_nodes(ax, rg)
    ax.axis("off")
    ax.margins(0.10)
    ax.text(0.5, -0.04, "augmenting path = shortest s->t path in this graph",
            transform=ax.transAxes, ha="center", va="top", fontsize=10.5,
            style="italic", color=C_INK)


def _legend_handles():
    return [
        plt.Line2D([0], [0], color=C_FWD, lw=2.6, label="forward residual"),
        plt.Line2D([0], [0], color=C_BACK, lw=2.6, ls="--",
                   label="backward arc (undo flow)"),
        plt.Line2D([0], [0], color=C_PATH, lw=7, alpha=0.55,
                   label="augmenting path"),
    ]


# %%
# --- Frame sequence ---------------------------------------------------------
# For each augmentation i: (a) flow on the original network, (b) residual graph
# with the chosen path highlighted. Flow frame shows the flow that EXISTS when
# the BFS runs (i.e. result of the previous augmentation).

n = len(snaps)
empty_flow = {u: {v: 0 for v in CAP[u]} for u in CAP}

# The flow panels (one per augmentation) plus the final max-flow panel form one
# .r-stack overlay on the slide, so they must come out at identical pixel sizes.
# Collect them here and crop them to a single common bbox at the end instead of
# saving each with its own tight crop.
flow_items = []

for i, s in enumerate(snaps):
    prev_flow = snaps[i - 1]["flow"] if i > 0 else empty_flow
    tag = f"step{i + 1}"

    # (a) flow state going INTO this augmentation. Collected, not saved yet (see
    # flow_items / save_aligned below). No tight_layout: that would let each
    # panel's decorations move the axes, defeating the alignment.
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    draw_flow(ax, prev_flow,
              f"Flow before augmentation {i + 1}   (value {snaps[i-1]['total'] if i>0 else 0})")
    flow_items.append((fig, f"0{i+1}_{tag}_flow"))

    # (b) residual graph + chosen path -- deliberately LARGER/clearer than the
    # flow panel, since the residual graph is inherently denser (every saturated
    # forward edge spawns a backward arc).
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    title = (f"Residual graph: BFS finds {' -> '.join(s['path'])}"
             f"  (bottleneck {s['bottleneck']})")
    if s["back_arcs"]:
        title += "  [uses a back-arc!]"
    draw_residual(ax, s["res_before"], s["path"], title)
    aeviz.legend_outside(ax, handles=_legend_handles(), loc="lower center",
                         anchor=(0.5, -0.16), ncol=3)
    fig.tight_layout()
    aeviz.save(fig, f"0{i+1}_{tag}_residual")
    plt.close(fig)

# %%
# --- Final frame: max flow on the original network --------------------------

# Same figsize as the flow panels so the network lands at the same axes inches;
# save_aligned then crops the whole group to one common bbox.
fig, ax = plt.subplots(figsize=(6.4, 3.8))
draw_flow(ax, snaps[-1]["flow"], f"Maximum flow: value {max_flow}")
# annotate the min cut for context
cut_value, (reach, _) = nx.minimum_cut(G, SOURCE, SINK)
cut_edges = [(u, v) for u in reach for v in G[u] if v not in reach]
for (u, v) in cut_edges:
    nx.draw_networkx_edges(G, POS, ax=ax, edgelist=[(u, v)], width=4.0,
                           edge_color=C_BACK, style=(0, (1, 1)),
                           arrows=True, arrowsize=18, arrowstyle="-|>",
                           node_size=900,
                           connectionstyle=f"arc3,rad={_fwd_rad(u, v)}",
                           min_source_margin=16, min_target_margin=16)
ax.text(0.5, -0.02, f"min cut = {cut_value} (saturated: "
        + ", ".join(f"{u}->{v}" for u, v in cut_edges) + ")",
        transform=ax.transAxes, ha="center", va="top", fontsize=10,
        color=C_BACK)
flow_items.append((fig, f"0{n+1}_final"))

# Crop every flow panel (augmentation steps + final) to one common bbox so the
# network does not jump when the final flow fades in over the step frames.
aeviz.save_aligned(flow_items)

print(f"\nWrote {n} flow/residual frame pairs + 0{n+1}_final.{{png,svg}}")
print(f"Min cut value {cut_value} matches max flow {max_flow}: "
      f"{cut_value == max_flow}")
