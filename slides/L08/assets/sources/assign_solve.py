"""
Assignment: orders to machines (minimum-cost perfect bipartite matching).

What this contains
  Solves the [OR] 4.18 "Planning Customers Orders" instance: five orders P1..P5
  must each be served by exactly one of five machines M1..M5, minimizing total
  production cost. This is the assignment problem = minimum-cost perfect
  bipartite matching, solved classically by the Hungarian algorithm in O(n^3).
  Non-goal: we do not reproduce the book's by-hand min-cost-flow iteration.

Why it exists
  Candidate visualization for the L08 graph-algorithms lecture (matching pillar,
  the weighted half). The deliverable is slide-ready figures, not just an answer.

How to run
  python solve.py
  (conda env mo312: networkx 3.2.1, scipy, numpy, matplotlib)

When it changes
  If we swap the instance (4.6 lawyers backup), retune the figures, or change the
  highlight styling for slides.
"""

# %%
import matplotlib

matplotlib.use("Agg")  # headless, deterministic raster/vector output

import pathlib
import sys

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # -> snippets/
import aeviz

aeviz.init_style()

# %%
# Instance, transcribed verbatim from [OR] 4.18, Table 4.17 (production costs).
# Rows = orders P1..P5, columns = machines M1..M5.
ORDERS = ["P1", "P2", "P3", "P4", "P5"]
MACHINES = ["M1", "M2", "M3", "M4", "M5"]

COST = np.array(
    [
        [16, 4, 9, 5, 6],   # P1
        [2, 14, 7, 5, 13],  # P2
        [8, 10, 3, 12, 11], # P3
        [3, 7, 6, 10, 5],   # P4
        [3, 6, 8, 11, 7],   # P5
    ],
    dtype=int,
)
n = len(ORDERS)

# %%
# Solve with networkx: minimum-weight FULL (perfect) matching on the complete
# bipartite graph. Orders on one side, machines on the other; machine node names
# are prefixed so they never collide with order node names.
G = nx.Graph()
G.add_nodes_from(ORDERS, bipartite=0)
machine_nodes = [f"m:{m}" for m in MACHINES]
G.add_nodes_from(machine_nodes, bipartite=1)
for i, o in enumerate(ORDERS):
    for j, m in enumerate(MACHINES):
        G.add_edge(o, f"m:{m}", weight=int(COST[i, j]))

nx_matching = nx.algorithms.bipartite.minimum_weight_full_matching(
    G, top_nodes=ORDERS, weight="weight"
)

# Extract order -> machine pairs (dict is symmetric; keep the order side).
assignment = {}  # order index -> machine index
for o in ORDERS:
    m_node = nx_matching[o]
    i = ORDERS.index(o)
    j = MACHINES.index(m_node.split(":", 1)[1])
    assignment[i] = j

nx_total = sum(COST[i, j] for i, j in assignment.items())

# %%
# Cross-check with the Hungarian algorithm via scipy.optimize.linear_sum_assignment.
row_ind, col_ind = linear_sum_assignment(COST)
hungarian_pairs = dict(zip(row_ind.tolist(), col_ind.tolist()))
hungarian_total = int(COST[row_ind, col_ind].sum())

assert nx_total == hungarian_total, (
    f"networkx ({nx_total}) and Hungarian/scipy ({hungarian_total}) disagree"
)
# Cost agreement is the guarantee; the specific pairs can differ if costs tie.

# %%
# Greedy baseline (cheapest available cell, repeatedly) to show optimal beats it.
def greedy_assignment(cost: np.ndarray):
    cost = cost.copy().astype(float)
    pairs = {}
    for _ in range(cost.shape[0]):
        i, j = np.unravel_index(np.argmin(cost), cost.shape)
        pairs[int(i)] = int(j)
        cost[i, :] = np.inf
        cost[:, j] = np.inf
    return pairs


greedy_pairs = greedy_assignment(COST)
greedy_total = sum(COST[i, j] for i, j in greedy_pairs.items())

# %%
# stdout summary.
print("Assignment problem: orders -> machines (min-cost perfect matching)")
print(f"  instance: {n}x{n} cost matrix [OR] 4.18\n")
print("  optimal assignment (Hungarian / networkx agree):")
for i in range(n):
    j = assignment[i]
    print(f"    {ORDERS[i]} -> {MACHINES[j]}   cost {COST[i, j]:>2d}")
print(f"  total optimal cost : {nx_total}")
print(f"  greedy total cost  : {greedy_total}  (gap +{greedy_total - nx_total})")

# %%
# Figure 1: cost matrix heatmap with the optimal cells boxed.
plt.rcParams.update({"font.size": 12})
fig1, ax1 = plt.subplots(figsize=(6.2, 5.4))
im = ax1.imshow(COST, cmap="YlGnBu", aspect="equal")

for i in range(n):
    for j in range(n):
        chosen = assignment[i] == j
        ax1.text(
            j,
            i,
            str(COST[i, j]),
            ha="center",
            va="center",
            color="white" if COST[i, j] > COST.max() * 0.6 else "black",
            fontweight="bold" if chosen else "normal",
            fontsize=13 if chosen else 11,
        )

# Box the chosen (optimal) cells.
for i in range(n):
    j = assignment[i]
    ax1.add_patch(
        plt.Rectangle(
            (j - 0.5, i - 0.5), 1, 1, fill=False, edgecolor="#d62728", linewidth=3.0
        )
    )

ax1.set_xticks(range(n))
ax1.set_yticks(range(n))
ax1.set_xticklabels(MACHINES)
ax1.set_yticklabels(ORDERS)
ax1.set_xlabel("machine")
ax1.set_ylabel("order")
ax1.set_title(f"Cost matrix with optimal assignment (total cost {nx_total})")
cbar = fig1.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
cbar.set_label("cost")
fig1.tight_layout()
fig1.savefig("01_cost_matrix.png", dpi=200, bbox_inches="tight")
fig1.savefig("01_cost_matrix.svg", bbox_inches="tight")
plt.close(fig1)

# %%
# Figure 2: bipartite graph, chosen edges bold red with cost labels.
fig2, ax2 = plt.subplots(figsize=(6.4, 6.0))

# Hand-placed positions: orders on the left, machines on the right, top-down.
pos = {}
for idx, o in enumerate(ORDERS):
    pos[o] = (0.0, n - 1 - idx)
for idx, m in enumerate(MACHINES):
    pos[f"m:{m}"] = (3.0, n - 1 - idx)

chosen_edges = {(ORDERS[i], f"m:{MACHINES[assignment[i]]}") for i in range(n)}
other_edges = [e for e in G.edges() if (e[0], e[1]) not in chosen_edges and (e[1], e[0]) not in chosen_edges]

order_color = aeviz.PALETTE["path"]      # bright blue, reads on dark
machine_color = aeviz.PALETTE["good"]    # green, reads on dark
match_color = aeviz.PALETTE["accent"]    # warm orange: the matching highlight

nx.draw_networkx_edges(
    G, pos, edgelist=other_edges, edge_color=aeviz.PALETTE["faded"], width=0.8, ax=ax2
)
nx.draw_networkx_edges(
    G, pos, edgelist=list(chosen_edges), edge_color=match_color, width=3.0, ax=ax2
)

nx.draw_networkx_nodes(
    G, pos, nodelist=ORDERS, node_color=order_color,
    edgecolors=aeviz.PALETTE["node_edge"], node_size=1100, ax=ax2,
)
nx.draw_networkx_nodes(
    G, pos, nodelist=machine_nodes, node_color=machine_color,
    edgecolors=aeviz.PALETTE["node_edge"], node_size=1100, ax=ax2,
)

labels = {o: o for o in ORDERS}
labels.update({f"m:{m}": m for m in MACHINES})
nx.draw_networkx_labels(G, pos, labels=labels, font_color="white", font_weight="bold", ax=ax2)

# Cost labels for the chosen edges. Crossing edges make mid-edge labels collide,
# so place each cost as a small tag just to the right of its order node (cost is
# a property of the order's choice). This stays readable regardless of crossings.
for i in range(n):
    ax2.text(
        0.32,
        n - 1 - i,
        f"{COST[i, assignment[i]]}",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=match_color,
        bbox={"boxstyle": "round,pad=0.18", "fc": (0.10, 0.14, 0.20, 0.85),
              "ec": match_color, "lw": 1.2},
    )

ax2.text(0.0, n + 0.25, "orders", ha="center", fontsize=13, fontweight="bold", color=order_color)
ax2.text(3.0, n + 0.25, "machines", ha="center", fontsize=13, fontweight="bold", color=machine_color)
ax2.set_title(f"Minimum-cost perfect matching (total cost {nx_total})", pad=24)
ax2.axis("off")
ax2.set_xlim(-0.7, 3.7)
ax2.set_ylim(-0.6, n + 0.7)
fig2.tight_layout()
fig2.savefig("02_matching.png", dpi=200, bbox_inches="tight")
fig2.savefig("02_matching.svg", bbox_inches="tight")
plt.close(fig2)

print("\nwrote 01_cost_matrix.png/.svg and 02_matching.png/.svg")
