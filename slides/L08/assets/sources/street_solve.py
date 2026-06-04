# %% [markdown]
# Shortest path on a REAL street network (central Hannover, OpenStreetMap).
#
# What this file contains
#   The textbook navigation example, but on genuine map data instead of a toy graph.
#   We pull the drivable street network of central Hannover from OpenStreetMap with
#   osmnx (nodes = intersections, edges = road segments with real geometry), weight
#   every road by its travel time (length / imputed speed), pick a START and a
#   DESTINATION intersection, and compute the fastest route as a plain shortest path.
#   This is exactly what a navigation app does.
#
#   It is the FAMILIAR case with no twist: it grounds the shortest-path concept on a
#   real map before the lecture moves to a less obvious application (shift rostering
#   as a DAG shortest path). Same city the bike-redistribution exercise (T02) used,
#   so the network is a callback, not a one-off. Non-goal: turn penalties, live
#   traffic, time-dependent travel times; those refinements come later in the lecture.
#
# Why it exists
#   Teaching snippet for L08, pillar 1 (Shortest Paths): the concrete grounding
#   example. The audience sees a weighted graph, a source, a target, and the fastest
#   route drawn on an actual street map.
#
# How to run
#   conda activate mo312 && python solve.py
#   First run downloads the OSM network and caches it to street_hannover.graphml
#   (subsequent runs load from disk, so it is reproducible and works offline).
#   Writes 01_network, 02_route (.png + .svg) and prints the route distance and time.
#
# When it changes
#   If the endpoints, the city, or the styling change. Keep the cached graphml in the
#   repo so the figure rebuilds without network access. Keep the area small enough
#   that individual streets stay legible at slide size.

# %%
import matplotlib

matplotlib.use("Agg")  # headless: write files, never open a window

import sys
from pathlib import Path

sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/week07-l08-graph-algorithms/snippets",
)

import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox

import aeviz

aeviz.init_style()

# %% [markdown]
# ## Instance: fetch (or load) the central-Hannover drive network and weight it by
# travel time. The area is a box around the city center; START and DESTINATION are
# two recognizable points inside it.

# %%
HERE = Path(__file__).parent
GRAPH_PATH = HERE / "street_hannover.graphml"

# Box center (Kröpcke-ish) and half-size; both endpoints lie inside.
CENTER = (52.3729, 9.7316)
DIST_M = 1300

# Endpoints (lat, lon): Hauptbahnhof (main station) -> Goetheplatz (Calenberger
# Neustadt). A cross-center route with a few turns.
START_LL = (52.3768, 9.7411)
DEST_LL = (52.3699, 9.7223)


def load_graph() -> nx.MultiDiGraph:
    """Load the cached central-Hannover drive graph, fetching it on first use."""
    if GRAPH_PATH.exists():
        g = ox.load_graphml(GRAPH_PATH)
    else:
        ox.settings.use_cache = True
        ox.settings.cache_folder = str(HERE / ".osm_cache")
        g = ox.graph_from_point(CENTER, dist=DIST_M, network_type="drive")
        # keep the largest strongly-connected component so a route always exists
        largest = max(nx.strongly_connected_components(g), key=len)
        g = g.subgraph(largest).copy()
        ox.save_graphml(g, GRAPH_PATH)
    # (Re)impute speeds and travel times; deterministic, and robust to graphml reload.
    g = ox.add_edge_speeds(g)
    g = ox.add_edge_travel_times(g)
    return g


G = load_graph()

# %% [markdown]
# ## Find the fastest route with Dijkstra (weight = travel time).
# Travel times are non-negative, so Dijkstra is the canonical tool. The graph is
# directed because of one-way streets, exactly like real routing data.

# %%
orig = ox.distance.nearest_nodes(G, X=START_LL[1], Y=START_LL[0])
dest = ox.distance.nearest_nodes(G, X=DEST_LL[1], Y=DEST_LL[0])

route = nx.shortest_path(G, orig, dest, weight="travel_time")
route_edges = list(zip(route[:-1], route[1:]))


def _min_attr(u, v, attr):
    """Smallest attr over the parallel edges u->v (MultiDiGraph)."""
    return min(d[attr] for d in G[u][v].values())


route_time_s = sum(_min_attr(u, v, "travel_time") for u, v in route_edges)
route_len_m = sum(_min_attr(u, v, "length") for u, v in route_edges)
route_min = route_time_s / 60.0
route_km = route_len_m / 1000.0

assert len(route) >= 6, ("route too short to be illustrative; move the endpoints", len(route))

# %% [markdown]
# ## Print the route summary.

# %%
print("=== Shortest path on a real street network (central Hannover, OSM) ===")
print(f"Network: {G.number_of_nodes()} intersections, {G.number_of_edges()} road segments")
print(f"From node {orig} (near Hauptbahnhof) to node {dest} (near Goetheplatz).")
print(f"Fastest route: {len(route)} intersections, "
      f"{route_km:.2f} km, {route_min:.1f} min driving.")

# %% [markdown]
# ## Project to meters (correct aspect) and draw with osmnx + the shared palette.

# %%
Gp = ox.project_graph(G)
SOURCE_C = aeviz.PALETTE["good"]    # green: start
TARGET_C = aeviz.PALETTE["accent"]  # vermillion: destination
ROUTE_C = aeviz.PALETTE["path"]     # blue: fastest route
ROAD_C = "#c4ccd4"
NODE_C = "#9aa6b2"                   # intersections: dots a shade darker than roads


def endpoints_xy():
    return ((Gp.nodes[orig]["x"], Gp.nodes[orig]["y"]),
            (Gp.nodes[dest]["x"], Gp.nodes[dest]["y"]))


def mark_endpoints(ax):
    (sx, sy), (dx, dy) = endpoints_xy()
    ax.scatter([sx], [sy], s=170, c=SOURCE_C, edgecolors="white", linewidths=1.6,
               zorder=6)
    ax.scatter([dx], [dy], s=170, c=TARGET_C, edgecolors="white", linewidths=1.6,
               zorder=6)
    ax.annotate("START", (sx, sy), textcoords="offset points", xytext=(8, 8),
                fontsize=10, fontweight="bold", color=SOURCE_C, zorder=7)
    ax.annotate("DESTINATION", (dx, dy), textcoords="offset points", xytext=(8, -14),
                fontsize=10, fontweight="bold", color=TARGET_C, zorder=7)


# %% [markdown]
# ## Figure 1: the street network (the instance), START and DESTINATION marked.

# %%
fig, ax = ox.plot_graph(
    Gp, node_size=9, node_color=NODE_C, node_edgecolor="none",
    edge_color=ROAD_C, edge_linewidth=0.8, bgcolor="none",
    show=False, close=False, figsize=(11, 6.2),
)
mark_endpoints(ax)
aeviz.save(fig, "01_network")
plt.close(fig)

# %% [markdown]
# ## Figure 2: the solution. The fastest START -> DESTINATION route highlighted.

# %%
fig, ax = ox.plot_graph_route(
    Gp, route, route_color=ROUTE_C, route_linewidth=3.6, route_alpha=0.95,
    orig_dest_size=0, node_size=9, node_color=NODE_C, node_edgecolor="none",
    edge_color=ROAD_C, edge_linewidth=0.8,
    bgcolor="none", show=False, close=False, figsize=(11, 6.2),
)
mark_endpoints(ax)
aeviz.save(fig, "02_route")
plt.close(fig)

print("\nFigures written: 01_network, 02_route (.png + .svg)")
