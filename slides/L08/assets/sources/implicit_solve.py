# %% [markdown]
# Shortest path on an implicit, huge graph: the 8-puzzle solved with A*.
#
# What this file contains:
#   A from-scratch A* search over the 8-puzzle state space, driven only by a
#   lazy successors(state) callback and a heap-based frontier. No global graph
#   is ever built for the search. Afterwards we assemble a networkx DiGraph of
#   only the explored states, purely to draw the search tree.
#   Non-goal: this is not a generic puzzle library and not the fastest solver.
#
# Why it exists:
#   Teaching point for L08 (Graph & Network Algorithms): a graph search needs
#   only a successor function plus a frontier. The reachable state space here is
#   ~181,440 states, yet we touch only a tiny reachable fraction. "Graph
#   algorithm" means "a way to generate neighbors", not "I already have an
#   adjacency list".
#
# How to run:
#   python solve.py
#   (conda env mo312: networkx 3.2.1, matplotlib, numpy, scipy)
#   Produces 01_explored_tree.{png,svg} and 02_state_render.{png,svg}.
#
# When it would change:
#   Swap the start board, the heuristic, or the figure styling. Keep the start
#   scrambled enough to be interesting but small enough that the explored tree
#   stays drawable (a few dozen to ~100 expanded nodes).

# %%
import heapq
import sys
from itertools import count

import matplotlib

matplotlib.use("Agg")  # headless, file-only rendering
import matplotlib.pyplot as plt
import networkx as nx

# Shared styling so this figure matches the rest of the L08 snippets.
sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/week07-l08-graph-algorithms/snippets",
)
import aeviz

aeviz.init_style()

# %% [markdown]
# ## The implicit state space
# A state is a 9-tuple: the 3x3 board read row by row, with 0 = blank.
# The goal is the solved board. We never enumerate states ahead of time; the
# only thing the search is allowed to know is `successors(state)`.

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)

# Fixed, deterministic start. Reachable from the goal (even permutation), and
# scrambled enough to need a couple dozen moves while keeping the explored tree
# drawable. No RNG anywhere.
START = (7, 2, 4, 5, 0, 6, 8, 3, 1)

# The full reachable state space of the 8-puzzle: half of 9! states.
REACHABLE_STATE_SPACE = 181440  # = 9! / 2


def successors(state):
    """Lazy neighbor generator: legal blank-slides from `state`.

    Returns a list of (next_state, cost) pairs, each move costing 1. This is the
    entire interface the search depends on. No adjacency list, no precomputation.
    """
    blank = state.index(0)
    row, col = divmod(blank, 3)
    out = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            swap = nr * 3 + nc
            board = list(state)
            board[blank], board[swap] = board[swap], board[blank]
            out.append((tuple(board), 1))
    return out


# %% [markdown]
# ## Heuristic: sum of Manhattan distances of each tile to its goal cell.
# Admissible (never overestimates) and consistent, so A* finds an optimal path.

# Precompute goal cell (row, col) for each tile value once.
_GOAL_POS = {v: divmod(i, 3) for i, v in enumerate(GOAL)}


def manhattan(state):
    total = 0
    for i, v in enumerate(state):
        if v == 0:
            continue
        r, c = divmod(i, 3)
        gr, gc = _GOAL_POS[v]
        total += abs(r - gr) + abs(c - gc)
    return total


# %% [markdown]
# ## A* from scratch: a binary heap frontier plus dicts keyed by state.
# `g` is the best known cost to reach a state; `came_from` rebuilds the path.
# `order` records the expansion order so the figure can show how the tree grew.


def astar(start, goal):
    frontier = []  # heap of (f, tie, state)
    tie = count()  # stable tie-breaker, keeps the search deterministic
    heapq.heappush(frontier, (manhattan(start), next(tie), start))

    g = {start: 0}
    came_from = {start: None}
    order = {}  # state -> expansion index (only for visualization)
    closed = set()

    while frontier:
        _, _, state = heapq.heappop(frontier)
        if state in closed:
            continue  # stale heap entry, already expanded via a better path
        closed.add(state)
        order[state] = len(order)

        if state == goal:
            break

        for nxt, cost in successors(state):
            tentative = g[state] + cost
            if tentative < g.get(nxt, float("inf")):
                g[nxt] = tentative
                came_from[nxt] = state
                heapq.heappush(frontier, (tentative + manhattan(nxt), next(tie), nxt))

    return came_from, g, order


# %%
came_from, g, order = astar(START, GOAL)

# Reconstruct the optimal path root -> goal.
path = []
node = GOAL
while node is not None:
    path.append(node)
    node = came_from[node]
path.reverse()

solution_length = len(path) - 1
expanded = len(order)
fraction = expanded / REACHABLE_STATE_SPACE

print("8-puzzle solved with A* (Manhattan heuristic)")
print(f"  start board:        {START}")
print(f"  solution length:    {solution_length} moves (optimal)")
print(f"  states expanded:    {expanded}")
print(f"  states discovered:  {len(g)} (in g-score dict)")
print(f"  reachable space:    {REACHABLE_STATE_SPACE:,} states")
print(f"  fraction expanded:  {fraction:.2%}  (1 in {REACHABLE_STATE_SPACE // expanded:,})")

# %% [markdown]
# ## Build a DiGraph of ONLY the explored states, purely for drawing.
# This is the post-hoc graph. The search above never needed it.

G = nx.DiGraph()
for state, parent in came_from.items():
    G.add_node(state)
    if parent is not None:
        G.add_edge(parent, state)

path_set = set(path)
path_edges = set(zip(path[:-1], path[1:]))

# %% [markdown]
# ## Figure 1: the explored search tree, solution path as a thin tendril.
# We lay the tree out top-down with a self-contained "tidy tree" sweep: depth
# sets y, and x is assigned by a leaf-order DFS so siblings spread and subtrees
# never overlap. Each leaf gets the next free x; each internal node sits at the
# mean of its children's x. This is what untangles the hairball into a tree.


def tidy_tree_pos(graph, root):
    """Deterministic tidy-tree layout (no external deps, no overlap).

    y = -depth (root on top, tree grows downward). x is assigned by an in-order
    leaf sweep: walk the tree depth-first, give each leaf the next integer x, and
    set every internal node to the mean of its children's x. Subtrees occupy
    disjoint x-intervals, so they cannot overlap -- that is the whole point.
    """
    # Stable child ordering keeps the layout deterministic across runs.
    children = {u: sorted(graph.successors(u)) for u in graph.nodes}
    depth = {}
    x = {}
    next_leaf = count()  # increasing x slot for each leaf, left to right

    # Iterative post-order DFS so deep 8-puzzle trees never blow the stack.
    stack = [(root, 0, False)]
    while stack:
        node, d, processed = stack.pop()
        if not processed:
            depth[node] = d
            kids = children[node]
            if not kids:
                x[node] = float(next(next_leaf))  # leaf: claim the next x slot
            else:
                # Re-push this node to finish AFTER its children are placed,
                # then push children (reversed so they pop left-to-right).
                stack.append((node, d, True))
                for child in reversed(kids):
                    stack.append((child, d + 1, False))
        else:
            kids = children[node]
            x[node] = sum(x[c] for c in kids) / len(kids)  # mean of children

    return {n: (x[n], -depth[n]) for n in graph.nodes}


pos = tidy_tree_pos(G, START)
tree_depth = max(-y for _, y in pos.values())

# Tall figure: the tree is ~20 deep, so give depth real vertical room and 200 dpi.
fig, ax = plt.subplots(figsize=(13, 16))

other_nodes = [n for n in G.nodes if n not in path_set]
other_edges = [e for e in G.edges if e not in path_edges]

# Background frontier: hairline gray edges + tiny gray dots so it reads as the
# explored cloud, not as noise competing with the solution.
nx.draw_networkx_edges(
    G, pos, edgelist=other_edges, ax=ax,
    edge_color=aeviz.PALETTE["faded"], width=0.4, arrows=False,
)
nx.draw_networkx_nodes(
    G, pos, nodelist=other_nodes, ax=ax,
    node_color=aeviz.PALETTE["faded"], node_size=6, linewidths=0.0,
)

# The solution: BOLD RED tendril from root to goal, drawn on top.
nx.draw_networkx_edges(
    G, pos, edgelist=list(path_edges), ax=ax,
    edge_color=aeviz.PALETTE["accent"], width=2.8, arrows=False,
)
nx.draw_networkx_nodes(
    G, pos, nodelist=[n for n in path if n not in (START, GOAL)], ax=ax,
    node_color=aeviz.PALETTE["accent"], node_size=70,
    edgecolors="white", linewidths=0.6,
)
# Mark start and goal distinctly.
nx.draw_networkx_nodes(
    G, pos, nodelist=[START], ax=ax, node_color=aeviz.PALETTE["good"],
    node_size=340, edgecolors="white", linewidths=1.4,
)
nx.draw_networkx_nodes(
    G, pos, nodelist=[GOAL], ax=ax, node_color=aeviz.PALETTE["warn"],
    node_size=340, edgecolors="white", linewidths=1.4,
)

ax.text(*pos[START], "  start", fontsize=13, va="center", ha="left",
        fontweight="bold", color=aeviz.PALETTE["ink"])
ax.text(*pos[GOAL], "  goal", fontsize=13, va="center", ha="left",
        fontweight="bold", color=aeviz.PALETTE["ink"])

ax.set_axis_off()
ax.margins(0.04)
ax.set_title(
    f"A* on the 8-puzzle: {REACHABLE_STATE_SPACE:,} states exist, we explored {expanded}\n"
    f"the red solution path ({solution_length} moves) is one thin tendril "
    f"through that explored frontier",
    pad=16,
)
aeviz.save(fig, "01_explored_tree")
plt.close(fig)

# %% [markdown]
# ## Figure 2: what a "move" actually is. We show the FIRST move and the LAST
# move along the optimal path as before/after 3x3 boards, so the audience sees
# the successor rule concretely: the blank swaps with one adjacent tile. Start
# and target are framed distinctly; the middle of the path is an ellipsis.

TILE_FILL = "#2a9d8f"          # teal tile
BLANK_FILL = "#243447"         # dark blank cell
MOVE_TILE = aeviz.PALETTE["path"]    # blue: the tile that slides this move
MOVE_ARROW = aeviz.PALETTE["accent"]  # orange: the move / slide arrow
START_FRAME = aeviz.PALETTE["good"]   # green frame: start
TARGET_FRAME = aeviz.PALETTE["warn"]  # amber frame: target


def moved_tile(prev, nxt):
    """Identify the single tile that slid between two adjacent path states.

    Returns (from_pos, to_pos): the cell the tile slid OUT of (prev's blank
    destination) and the cell it slid INTO (prev's blank). The blank moves the
    opposite way. Positions are 0..8 indices into the row-major board.
    """
    blank_prev = prev.index(0)   # where the blank was -> tile slides in here
    blank_next = nxt.index(0)    # where the blank ends up -> tile came from here
    return blank_next, blank_prev


def _cell_center(ox, oy, pos):
    r, c = divmod(pos, 3)
    return ox + c + 0.5, oy + (2 - r) + 0.5


def draw_board_at(ax, state, ox, oy, *, frame=None, highlight=None, slide=None):
    """Draw a 3x3 board with its lower-left at (ox, oy) on a shared axes.

    highlight: set of board indices to paint in MOVE_TILE (the sliding tile).
    slide: (from_pos, to_pos) draws a white in-board arrow tile -> blank.
    frame: edge color for a box around the board (start / target marker).
    """
    highlight = highlight or set()
    for i, v in enumerate(state):
        r, c = divmod(i, 3)
        x, y = ox + c, oy + (2 - r)  # row 0 on top
        if v == 0:
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor=BLANK_FILL,
                                       edgecolor=aeviz.PALETTE["faded_dark"], lw=1.0))
        else:
            face = MOVE_TILE if i in highlight else TILE_FILL
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor=face,
                                       edgecolor=aeviz.PALETTE["node_edge"], lw=1.3))
            ax.text(x + 0.5, y + 0.5, str(v), ha="center", va="center",
                    fontsize=27, color="white", fontweight="bold")
    if slide is not None:
        x0, y0 = _cell_center(ox, oy, slide[0])
        x1, y1 = _cell_center(ox, oy, slide[1])
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=6,
                    arrowprops=dict(arrowstyle="-|>", color="white", lw=3.2,
                                    shrinkA=12, shrinkB=12, mutation_scale=22))
    if frame is not None:
        ax.add_patch(plt.Rectangle((ox - 0.05, oy - 0.05), 3.10, 3.10, fill=False,
                                   edgecolor=frame, lw=3.0, zorder=5))


def between_arrow(ax, x0, x1, y, label):
    ax.annotate("", xy=(x1, y), xytext=(x0, y), zorder=4,
                arrowprops=dict(arrowstyle="-|>", color=MOVE_ARROW, lw=3.5,
                                mutation_scale=26))
    ax.text((x0 + x1) / 2, y + 0.5, label, ha="center", va="bottom",
            fontsize=15, color=MOVE_ARROW, fontweight="bold")


# First move (start -> next) and last move (penultimate -> goal).
A, B = path[0], path[1]
C, D = path[-2], path[-1]
f1, t1 = moved_tile(A, B)   # in A, tile at f1 slides to t1 (the blank)
f2, t2 = moved_tile(C, D)

oy = 0.0
OX = {"A": 0.0, "B": 4.6, "C": 10.0, "D": 14.6}
ymid = oy + 1.5

fig2, ax = plt.subplots(figsize=(15.5, 4.2))
# Start: green frame, the sliding tile lit, white arrow into the blank.
draw_board_at(ax, A, OX["A"], oy, frame=START_FRAME, highlight={f1}, slide=(f1, t1))
# After one move: same tile now in its new cell, still lit.
draw_board_at(ax, B, OX["B"], oy, highlight={t1})
# Before the last move: the next sliding tile lit + its slide arrow.
draw_board_at(ax, C, OX["C"], oy, highlight={f2}, slide=(f2, t2))
# Target: amber frame, the last-moved tile lit in place.
draw_board_at(ax, D, OX["D"], oy, frame=TARGET_FRAME, highlight={t2})

between_arrow(ax, OX["A"] + 3.05, OX["B"] - 0.05, ymid, "one move")
between_arrow(ax, OX["C"] + 3.05, OX["D"] - 0.05, ymid, "last move")
ax.text((OX["B"] + 3 + OX["C"]) / 2, ymid, "· · ·", ha="center", va="center",
        fontsize=42, color=aeviz.PALETTE["faded"], fontweight="bold")

ax.text(OX["A"] + 1.5, oy - 0.75, "start", ha="center", va="top", fontsize=21,
        fontweight="bold", color=START_FRAME)
ax.text(OX["D"] + 1.5, oy - 0.75, "target", ha="center", va="top", fontsize=21,
        fontweight="bold", color=TARGET_FRAME)

ax.set_xlim(-0.4, OX["D"] + 3.4)
ax.set_ylim(-1.5, 3.4)
ax.set_aspect("equal")
ax.set_axis_off()
fig2.tight_layout()
fig2.savefig("02_state_render.png", dpi=180, bbox_inches="tight", transparent=True)
fig2.savefig("02_state_render.svg", bbox_inches="tight", transparent=True)
plt.close(fig2)

print("\nwrote 01_explored_tree.{png,svg} and 02_state_render.{png,svg}")
