"""A* vs. Dijkstra on a grid: the heuristic shrinks the explored region.

What this file contains
    A self-contained, deterministic grid-shortest-path demo for L08. It builds a
    grid with maze-like wall obstacles, then runs ONE instrumented best-first
    search twice: once with a Manhattan heuristic (A*) and once with h == 0
    (Dijkstra). The point is the contrast in EXPANDED (popped) nodes, not the
    path length. The non-goal: this is not a tuned router and does not model
    8-neighborhoods or weighted edges.

    The instance puts START at the CENTER of the grid and GOAL on the right
    BOUNDARY. With the source in the middle, Dijkstra expands a diamond in every
    direction, including the whole left half that points AWAY from the goal:
    wasted work the heuristic avoids. A* instead drives a wedge toward the
    boundary goal. Neither region is clipped by a grid edge near the goal, so the
    heuristic, not the boundary, does the pruning. A few partial walls between
    center and goal make the route bend, giving A*'s wedge some internal
    structure while it still expands far fewer cells than Dijkstra.

Why it exists
    To make Dominik's headline literally true in code ("Dijkstra = A* with a
    zero heuristic") and to produce the side-by-side "directed cone vs. flood"
    figure for the slides.

How to run
    python solve.py
    Writes 00_side_by_side.{png,svg}, 01_dijkstra_explored.{png,svg},
    02_astar_explored.{png,svg}, 03_counts.{png,svg} into this folder and
    prints the expanded-node counts.

When it would change
    Grid size / maze pattern, switching to 8-neighbor + Chebyshev, or wanting a
    multi-instance table. The instrumented-search core should stay untouched.
"""

# %%
import sys

sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/"
    "week07-l08-graph-algorithms/snippets",
)
import aeviz

aeviz.init_style()

# %%
import heapq

import matplotlib

matplotlib.use("Agg")  # headless, slide-asset generation only
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import ListedColormap

SEED = 7
# Square grid with the source at the CENTER and the goal on the right boundary.
# Centering the source is the whole point: Dijkstra's flood then spreads equally
# in all directions, so the leftward half (pointing away from the goal) is
# visibly explored, while A* heads straight for the boundary.
W, H = 41, 41  # odd so the exact center is a single cell
START = (W // 2, H // 2)  # CENTER of the grid
GOAL = (W - 1, H // 2)    # right BOUNDARY, vertical middle

# %%
# --- Build a deterministic maze-like wall layout ----------------------------
# The route runs left -> right across the vertical middle. To make A*'s cone
# show real structure (probe + back out of a dead end), we drop a few vertical
# barriers that span most of the height with a single OFFSET gap each, so the
# only way through alternates up and down. A couple of horizontal nubs seed
# shallow dead ends near the corridor. Everything is seeded for determinism.


def build_obstacles(w: int, h: int, seed: int) -> set[tuple[int, int]]:
    """Return a set of blocked (x, y) cells forming a solvable maze.

    Design goal: a route that bends enough to be non-trivial yet stays roughly
    monotone toward the goal, so the Manhattan heuristic stays informative and
    A*'s cone is tight. Two ingredients:

    1. Partial vertical walls with a single gap each, gaps OFFSET modestly from
       the midline (alternating sides). These nudge the corridor up and down so
       the optimal path zig-zags gently instead of running straight. The walls
       deliberately do NOT span the full height: the flood spreads past them on
       both sides, which is what makes Dijkstra's region a big diamond while A*
       stays in the corridor band.
    2. Short horizontal "finger" walls that dead-end into the corridor. A* runs
       into them, probes a few cells, and backs out -- this is the visible
       internal structure in the cone without inflating the global path length.
    """
    rng = np.random.default_rng(seed)
    blocked: set[tuple[int, int]] = set()
    mid = h // 2

    # Partial vertical barriers, placed BETWEEN the center and the right-edge
    # goal, so the route from center to boundary must weave. Each wall spans
    # [y_lo, y_hi] minus a gap around gap_center; gaps alternate above/below mid.
    # The left half is left OPEN on purpose: that is where Dijkstra's wasted
    # flood (away from the goal) shows up while A* never goes there.
    walls = [
        (mid + 6, mid + 5, 3, h - 4),    # gap above mid
        (mid + 12, mid - 5, 3, h - 4),   # gap below mid, nearer the goal
    ]
    gap_half = 2  # gap is 2*gap_half+1 cells tall
    gap_cells: set[tuple[int, int]] = set()  # protect from the random scatter
    for x, gap, y_lo, y_hi in walls:
        for y in range(y_lo, y_hi + 1):
            if abs(y - gap) <= gap_half:
                gap_cells.add((x, y))  # leave the gap open
                continue
            blocked.add((x, y))

    # Short horizontal finger walls dead-ending toward the corridor on the goal
    # side: A* probes the pocket, finds no through-gap, and backs out. These give
    # the wedge internal structure without forcing a global detour.
    fingers = [
        (mid + 2, mid + 6, mid),
        (mid + 8, mid + 12, mid + 3),
    ]
    for x0, x1, y in fingers:
        for x in range(x0, x1):
            blocked.add((x, y))

    # Light random scatter for texture, never on start/goal or sealing a gap.
    for x in range(w):
        for y in range(h):
            if (x, y) in (START, GOAL) or (x, y) in gap_cells:
                continue
            if (x, y) not in blocked and rng.random() < 0.05:
                blocked.add((x, y))

    blocked.discard(START)
    blocked.discard(GOAL)
    return blocked


OBSTACLES = build_obstacles(W, H, SEED)


def build_graph(w: int, h: int, blocked: set[tuple[int, int]]) -> nx.Graph:
    """4-neighbor grid graph with unit edge cost, obstacle nodes removed."""
    g = nx.grid_2d_graph(w, h)  # nodes are (x, y), 4-neighborhood
    g.remove_nodes_from(blocked)
    nx.set_edge_attributes(g, 1, "weight")
    return g


G = build_graph(W, H, OBSTACLES)
assert nx.has_path(G, START, GOAL), "instance is unsolvable; change SEED"


# %%
# --- One instrumented best-first search, parametrized by the heuristic ------
# Dijkstra is recovered exactly by passing h(n) == 0. Same code, same tie-break,
# so the only difference between the two runs is the heuristic.
#
# Tie-break note: on a unit-cost 4-grid the Manhattan heuristic is "flat" along
# whole anti-diagonals (many nodes share the same f), and there are exponentially
# many shortest paths. With an arbitrary tie-break A* would still settle nearly
# the entire reachable region, hiding its advantage. So among equal-f nodes we
# prefer the one closer to the goal (smaller h) -- the textbook A* tie-break.
# This is what funnels A* into a narrow cone. For Dijkstra (h == 0) the
# tie-break is inert (all h are 0), so it keeps flooding outward: the contrast is
# honest, not an artifact of the heap order.


def manhattan(node: tuple[int, int], goal: tuple[int, int]) -> int:
    return abs(node[0] - goal[0]) + abs(node[1] - goal[1])


def zero(node: tuple[int, int], goal: tuple[int, int]) -> int:
    return 0


def search(graph, start, goal, heuristic):
    """Instrumented A*. Returns (path, expanded_order).

    expanded_order = nodes in the order they were popped from the open heap
    (i.e. settled / closed). Length of this list is the headline count.
    """
    g_cost = {start: 0}
    came_from: dict = {}
    counter = 0  # stable FIFO break for full ties (f and h both equal)
    h0 = heuristic(start, goal)
    # heap key: (f, h, counter, node) -- secondary key h realizes the
    # closer-to-goal tie-break described above.
    open_heap = [(h0, h0, counter, start)]
    closed: set = set()
    expanded_order: list = []

    while open_heap:
        _f, _h, _c, node = heapq.heappop(open_heap)
        if node in closed:
            continue
        closed.add(node)
        expanded_order.append(node)
        if node == goal:
            break
        gc = g_cost[node]
        for nbr in graph.neighbors(node):
            if nbr in closed:
                continue
            tentative = gc + graph[node][nbr]["weight"]
            if tentative < g_cost.get(nbr, float("inf")):
                g_cost[nbr] = tentative
                came_from[nbr] = node
                counter += 1
                h = heuristic(nbr, goal)
                f = tentative + h
                heapq.heappush(open_heap, (f, h, counter, nbr))

    # Reconstruct path.
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path, expanded_order


# %%
# --- Run both and cross-check against networkx ------------------------------
astar_path, astar_expanded = search(G, START, GOAL, manhattan)
dijkstra_path, dijkstra_expanded = search(G, START, GOAL, zero)

len_astar = len(astar_path) - 1  # path length in edges (= unit cost)
len_dijkstra = len(dijkstra_path) - 1

# networkx cross-check: same optimal cost.
nx_astar = nx.astar_path_length(G, START, GOAL, heuristic=manhattan, weight="weight")
nx_dijkstra = nx.dijkstra_path_length(G, START, GOAL, weight="weight")

assert len_astar == len_dijkstra, "A* and Dijkstra disagree on path length!"
assert len_astar == nx_astar == nx_dijkstra, "disagreement with networkx cost!"
# The route must bend (not a straight line) for the wedge to have structure:
# optimal length must exceed the straight-line (Manhattan) center-to-goal distance.
assert len_astar > manhattan(START, GOAL), "path is too straight; tighten the maze gaps"

n_astar = len(astar_expanded)
n_dijkstra = len(dijkstra_expanded)
ratio = n_dijkstra / n_astar

print("=" * 56)
print(f"Grid: {W}x{H}  free cells: {G.number_of_nodes()}  walls: {len(OBSTACLES)}")
print(f"Start {START} (center) -> Goal {GOAL} (right boundary)")
print(f"Optimal path length (edges): {len_astar}  (nx confirms: {nx_astar})")
print("-" * 56)
print(f"Dijkstra (h=0)   expanded: {n_dijkstra:4d} nodes")
print(f"A* (Manhattan)   expanded: {n_astar:4d} nodes")
print(f"Speedup in expanded nodes: {ratio:.1f}x fewer for A*")
print("=" * 56)


# %%
# --- Plotting helpers -------------------------------------------------------
# Layer per cell: 0 = free/unexplored, 1 = explored, 2 = obstacle, 3 = path.
# Dark-theme cells: free = navy (matches the slide background so unexplored cells
# recede), explored = frontier blue, walls = light-neutral so they read on dark,
# path = accent orange. No near-white background, no dark-on-dark walls.
FREE, EXPLORED, WALL, PATH = 0, 1, 2, 3
CMAP = ListedColormap(["#243549", "#56B4E9", "#9aa6b5", "#ff8c42"])


def grid_layers(expanded, path) -> np.ndarray:
    """Build a (H, W) image array. Row index = y, col index = x; y flipped on plot."""
    img = np.full((H, W), FREE, dtype=int)
    for (x, y) in expanded:
        img[y, x] = EXPLORED
    for (x, y) in OBSTACLES:
        img[y, x] = WALL
    for (x, y) in path:
        img[y, x] = PATH
    return img


def pick_heuristic_sample(goal: tuple[int, int]) -> tuple[int, int]:
    """A free cell in the upper-right region to anchor the heuristic illustration.

    The guide line shows h(n) = L1 distance from one sample cell to the goal. We
    want that cell in clean unexplored space (upper-right quadrant of the A* run),
    so the thin red connector reads against the navy background instead of
    crossing the explored cone. Deterministic: nearest free cell to the quadrant
    center, never the goal or a wall.
    """
    target = (3 * W // 4, 3 * H // 4)  # upper-right quadrant center
    best: tuple[int, tuple[int, int]] | None = None
    for x in range(W // 2, W):
        for y in range(H // 2, H):
            if (x, y) in OBSTACLES or (x, y) == goal:
                continue
            d = abs(x - target[0]) + abs(y - target[1])
            if best is None or d < best[0]:
                best = (d, (x, y))
    assert best is not None, "no free cell in the upper-right quadrant"
    return best[1]


def draw_heuristic_guide(ax, sample: tuple[int, int], goal: tuple[int, int]):
    """Overlay one Manhattan-distance estimate as a thin red L-shaped connector.

    Horizontal leg (length |dx|) then vertical leg (length |dy|) from the sample
    cell to the goal; the two legs are labeled and their sum is the heuristic
    value h. This makes the heuristic that drives A* a visible object on the
    slide rather than just a word in the caption.
    """
    red = "#ff5d5d"
    sx, sy = sample
    gx, gy = goal
    dx, dy = abs(sx - gx), abs(sy - gy)
    # Horizontal leg along the top, then down the right edge: both legs stay in
    # the unexplored navy band, clear of the path and explored cells.
    ax.plot([sx, gx], [sy, sy], color=red, lw=1.4, zorder=6, solid_capstyle="round")
    ax.plot([gx, gx], [sy, gy], color=red, lw=1.4, zorder=6, solid_capstyle="round")
    ax.scatter([sx], [sy], s=34, c=red, edgecolors="white", linewidths=0.8, zorder=7)
    ax.annotate(f"|Δx| = {dx}", ((sx + gx) / 2, sy), textcoords="offset points",
                xytext=(0, 6), ha="center", va="bottom", fontsize=9, color=red)
    ax.annotate(f"|Δy| = {dy}", (gx, (sy + gy) / 2), textcoords="offset points",
                xytext=(-6, 0), ha="right", va="center", fontsize=9, color=red)
    ax.annotate(f"h = |Δx| + |Δy| = {dx + dy}", (sx, sy),
                textcoords="offset points", xytext=(-8, -10), ha="right", va="top",
                fontsize=10, color=red, fontweight="bold")


def draw_grid(ax, img, title, n_expanded):
    ax.imshow(img, cmap=CMAP, origin="lower", interpolation="nearest", vmin=0, vmax=3)
    ax.set_title(f"{title}\n{n_expanded} nodes explored", fontsize=14, pad=10)
    ax.set_xticks([])
    ax.set_yticks([])
    # Mark start and goal.
    ax.scatter([START[0]], [START[1]], marker="o", s=70, c="#7fbf7b",
               edgecolors="white", linewidths=1.2, zorder=5)
    ax.scatter([GOAL[0]], [GOAL[1]], marker="*", s=220, c="#ff5d5d",
               edgecolors="white", linewidths=1.0, zorder=5)
    for spine in ax.spines.values():
        spine.set_visible(False)


# %%
# --- Figure 1+2: side-by-side explored regions ------------------------------
img_d = grid_layers(dijkstra_expanded, dijkstra_path)
img_a = grid_layers(astar_expanded, astar_path)

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
draw_grid(axes[0], img_d, "Dijkstra (zero heuristic): floods outward", n_dijkstra)
draw_grid(axes[1], img_a, "A* (Manhattan heuristic): directed cone", n_astar)
# Make the heuristic visible on the A* panel: one L1 estimate to the goal.
HEUR_SAMPLE = pick_heuristic_sample(GOAL)
draw_heuristic_guide(axes[1], HEUR_SAMPLE, GOAL)
fig.suptitle("Same optimal path, far fewer nodes explored with a heuristic",
             fontsize=15, y=1.02)
fig.tight_layout()

# Single combined figure (best for the slide), plus the two individual panels.
aeviz.save(fig, "00_side_by_side")

for fname, img, title, n in [
    ("01_dijkstra_explored", img_d, "Dijkstra (zero heuristic)", n_dijkstra),
    ("02_astar_explored", img_a, "A* (Manhattan heuristic)", n_astar),
]:
    f, ax = plt.subplots(figsize=(6, 6))
    draw_grid(ax, img, title, n)
    f.tight_layout()
    aeviz.save(f, fname)
    plt.close(f)

# %%
# --- Figure 3: bar chart of expanded counts ---------------------------------
fig2, ax = plt.subplots(figsize=(6, 5))
bars = ax.bar(
    ["Dijkstra\n(h = 0)", "A*\n(Manhattan)"],
    [n_dijkstra, n_astar],
    color=["#9aa6b5", "#56B4E9"],
    width=0.6,
)
ax.bar_label(bars, fontsize=13, padding=3)
ax.set_ylabel("Nodes expanded (popped)", fontsize=12)
ax.set_title(f"A* explores {ratio:.1f}x fewer nodes", fontsize=14)
ax.spines[["top", "right"]].set_visible(False)
ax.set_ylim(0, n_dijkstra * 1.15)
fig2.tight_layout()
aeviz.save(fig2, "03_counts")
plt.close("all")

print("Wrote: 00_side_by_side, 01_dijkstra_explored, 02_astar_explored, 03_counts (.png/.svg)")
