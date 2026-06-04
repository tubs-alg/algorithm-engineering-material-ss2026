# %% [markdown]
# Resource-Constrained Shortest Path (RCSP): one side budget flips SP to NP-hard.
#
# What this file contains
#   A small directed graph from a source S to a sink T. Each arc carries TWO
#   numbers: a `cost` (some NEGATIVE, so this reads as a column-generation pricing
#   problem) and a non-negative `resource` consumption (think driving time / fuel /
#   route duration). A global budget R caps the total resource along the chosen
#   S->T path.
#
#   The whole point in one instance:
#   - PLAIN shortest path (minimize cost, ignore the resource) is polynomial. We
#     solve it with networkx (Bellman-Ford, because some costs are negative). The
#     cheapest path here SPENDS MORE RESOURCE THAN R: it is illegal for a route.
#   - Add the ONE budget R <= total resource and the problem becomes the
#     RESOURCE-CONSTRAINED SHORTEST PATH, which is (weakly) NP-hard. The optimum is
#     a DIFFERENT, MORE EXPENSIVE path that fits under R. We solve it with a
#     hand-written LABEL-SETTING / labeling DP that keeps Pareto-nondominated
#     (cost, resource) labels per node, extends them along arcs, and prunes
#     dominated labels and labels that would exceed R. This is exactly the standard
#     RCSP pricing algorithm (pseudo-polynomial in the integer resource).
#   - A brute-force enumeration of all simple S->T paths cross-checks the labeling
#     optimum on this small instance (they must agree).
#
#   The lesson: a tiny side constraint flips complexity, and the now-hard SP is the
#   PRICING SUBPROBLEM at the core of column generation (vehicle/crew routing): the
#   master hands down arc reduced costs (negative allowed), pricing seeks a
#   min-reduced-cost path respecting a resource limit (capacity, duration, legal
#   driving time). The trivially-fast SP becomes the hard heart of a real solver.
#   Non-goal: an actual column-generation loop, multiple resources, or a generic
#   RCSP library. Kept to one budget and one tiny graph that stays legible.
#
# Why it exists
#   Teaching snippet for L08, pillar 1 (Shortest Paths), item 3.7: the NP-hard case.
#   It is the resource-constrained extension of the sibling DAG pricing example
#   (../dag-shift-planning-pricing/), which establishes the negative-reduced-cost /
#   column-generation framing on a polynomial DAG. Here we add the budget and break
#   polynomiality.
#
# How to run
#   conda activate mo312 && python solve.py
#   (or: conda run -n mo312 python solve.py)
#   Writes 01_network, 02_two_paths, 03_pareto_labels (.png + .svg) and prints the
#   unconstrained vs constrained result plus the brute-force agreement to stdout.
#
# When it changes
#   If the instance is retuned. Keep it deterministic, keep the cheapest path over
#   budget and the constrained optimum strictly more expensive, and keep the graph
#   small enough that the network and the Pareto frontier stay legible at slide size.

# %%
import matplotlib

matplotlib.use("Agg")  # headless: write files, never open a window

import sys

sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/week07-l08-graph-algorithms/snippets",
)

from itertools import count

import matplotlib.pyplot as plt
import networkx as nx

import aeviz

aeviz.init_style()

# %% [markdown]
# ## Instance: a tiny directed graph with (cost, resource) on every arc.
# S = source, T = sink. Costs include negatives (pricing flavor). Resource is the
# side budget: total resource along the path must stay <= R. Tuned so the cheapest
# path (ignoring resource) is OVER budget, and the cheapest feasible path is a
# different, more expensive route.

# %%
S, T = "S", "T"
R = 10  # resource budget: total resource consumed along the S->T path must be <= R

# Hand-placed positions (NOT random) for a stable, readable left-to-right layout.
POS = {
    "S": (0.0, 0.0),
    "A": (1.0, 1.1),
    "B": (1.0, -1.1),
    "C": (2.0, 1.1),
    "D": (2.0, -1.1),
    "E": (3.0, 0.0),
    "T": (4.0, 0.0),
}

# Arc list: (u, v, cost, resource). Resource >= 0 everywhere. Some costs negative.
# Design (verified by the asserts at the bottom):
#   - The min-COST path ignoring resource is the "fast-but-illegal" one and spends
#     more than R units of resource.
#   - The min-cost path with total resource <= R is a different, MORE EXPENSIVE path.
ARCS = [
    ("S", "A", 2, 3),
    ("S", "B", 1, 2),
    ("A", "C", -3, 7),    # cheap but resource-heavy: the tempting illegal leg
    ("A", "D", 1, 2),
    ("B", "C", 4, 2),
    ("B", "D", 2, 3),
    ("C", "E", -2, 4),    # again cheap but heavy
    ("C", "T", 3, 2),
    ("D", "E", 2, 2),
    ("D", "T", 5, 1),
    ("E", "T", -1, 3),
]

G = nx.DiGraph()
for u, v, cost, res in ARCS:
    G.add_edge(u, v, cost=cost, resource=res)

NODES = list(POS)
assert nx.is_directed_acyclic_graph(G), "instance must be acyclic for clean enumeration"
assert all(d["resource"] >= 0 for _, _, d in G.edges(data=True)), "resource must be >= 0"


def path_cost(path: list[str]) -> int:
    return sum(G[u][v]["cost"] for u, v in zip(path[:-1], path[1:]))


def path_resource(path: list[str]) -> int:
    return sum(G[u][v]["resource"] for u, v in zip(path[:-1], path[1:]))


# %% [markdown]
# ## Plain shortest path (POLYNOMIAL): minimize cost, ignore the resource.
# Some costs are negative, so Dijkstra would be wrong; Bellman-Ford is correct on a
# graph with negative weights and no negative cycle (a DAG has none).

# %%
unconstrained_path = nx.bellman_ford_path(G, S, T, weight="cost")
unconstrained_cost = path_cost(unconstrained_path)
unconstrained_resource = path_resource(unconstrained_path)

# %% [markdown]
# ## Resource-constrained shortest path (NP-HARD): label-setting DP.
# Keep, per node, a set of Pareto-nondominated (cost, resource) labels. A label
# (c1, r1) DOMINATES (c2, r2) if c1 <= c2 and r1 <= r2 (and not equal): the
# dominated one can never lead to a better feasible path, so we prune it. Extend
# every label along outgoing arcs, dropping any extension whose resource exceeds R.
# This is the standard RCSP pricing algorithm; it is pseudo-polynomial in R, which
# is why "one integer resource" is only WEAKLY NP-hard. Each label remembers its
# predecessor so we can rebuild the path.

# %%
class Label:
    """A partial path arriving at `node` with total `cost` and `resource`."""

    __slots__ = ("node", "cost", "resource", "parent", "id")
    _ids = count()

    def __init__(self, node, cost, resource, parent):
        self.node = node
        self.cost = cost
        self.resource = resource
        self.parent = parent
        self.id = next(self._ids)


def dominates(a: Label, b: Label) -> bool:
    """True if label a weakly dominates b and is not identical in both objectives."""
    return a.cost <= b.cost and a.resource <= b.resource and (
        a.cost < b.cost or a.resource < b.resource
    )


def rcsp_label_setting(budget: int):
    """Min-cost S->T path with total resource <= budget, via Pareto labels.

    Returns (best_label_at_T, labels_by_node). Processes nodes in topological order
    so every label is final when its node is expanded (label-SETTING on a DAG).
    """
    labels: dict[str, list[Label]] = {n: [] for n in G.nodes}
    labels[S] = [Label(S, 0, 0, None)]
    for u in nx.topological_sort(G):
        for lab in labels[u]:
            for v in G.successors(u):
                d = G[u][v]
                nr = lab.resource + d["resource"]
                if nr > budget:
                    continue  # prune: would break the resource budget
                cand = Label(v, lab.cost + d["cost"], nr, lab)
                bucket = labels[v]
                if any(dominates(ex, cand) for ex in bucket):
                    continue  # prune: dominated by an existing label
                bucket[:] = [ex for ex in bucket if not dominates(cand, ex)]
                bucket.append(cand)
    feasible = labels[T]
    best = min(feasible, key=lambda x: x.cost) if feasible else None
    return best, labels


def label_path(lab: Label) -> list[str]:
    seq = []
    while lab is not None:
        seq.append(lab.node)
        lab = lab.parent
    return seq[::-1]


best_label, all_labels = rcsp_label_setting(R)
assert best_label is not None, "no feasible path within budget; retune instance"
constrained_path = label_path(best_label)
constrained_cost = best_label.cost
constrained_resource = best_label.resource

# %% [markdown]
# ## Brute-force cross-check: enumerate all simple S->T paths (small instance only).

# %%
all_paths = list(nx.all_simple_paths(G, S, T))
feasible_paths = [p for p in all_paths if path_resource(p) <= R]
bf_best = min(feasible_paths, key=path_cost)
bf_cost = path_cost(bf_best)
bf_resource = path_resource(bf_best)

# The labeling DP optimum must equal the brute-force optimum (cost + resource).
assert constrained_cost == bf_cost, (constrained_cost, bf_cost)
assert constrained_resource == bf_resource, (constrained_resource, bf_resource)

# The teaching contrast must hold: cheapest path is over budget; constrained
# optimum respects it and is strictly more expensive.
assert unconstrained_resource > R, "cheapest path must VIOLATE the budget"
assert constrained_resource <= R, "constrained optimum must respect the budget"
assert constrained_cost > unconstrained_cost, "constrained optimum must cost more"

# %% [markdown]
# ## stdout summary.

# %%
print("=== Resource-Constrained Shortest Path (RCSP) ===")
print(f"Instance: {G.number_of_nodes()} nodes, {G.number_of_edges()} arcs, "
      f"S={S} -> T={T}, resource budget R = {R}")
print(f"Each arc carries (cost, resource); {sum(1 for *_ , c, _ in ARCS if c < 0)} "
      "arcs have negative cost (pricing flavor).")
print()
print("PLAIN shortest path (minimize cost, ignore resource) -- POLYNOMIAL (Bellman-Ford):")
print(f"  path     : {' -> '.join(unconstrained_path)}")
print(f"  cost     : {unconstrained_cost}")
print(f"  resource : {unconstrained_resource}   (budget R = {R}) "
      f"-> {'OVER BUDGET, infeasible as a route' if unconstrained_resource > R else 'ok'}")
print()
print(f"RESOURCE-CONSTRAINED shortest path (cost min s.t. resource <= {R}) -- NP-HARD "
      "(label-setting DP):")
print(f"  path     : {' -> '.join(constrained_path)}")
print(f"  cost     : {constrained_cost}   (+{constrained_cost - unconstrained_cost} "
      "vs the illegal cheapest path)")
print(f"  resource : {constrained_resource}   (<= {R}, feasible)")
n_labels = sum(len(v) for v in all_labels.values())
print(f"  Pareto labels kept across all nodes: {n_labels}; "
      f"labels arriving at T: {len(all_labels[T])}")
print()
print(f"Brute force over all {len(all_paths)} simple S->T paths "
      f"({len(feasible_paths)} within budget): "
      f"optimum {' -> '.join(bf_best)}, cost {bf_cost}, resource {bf_resource}")
print(f"  labeling DP == brute force: {constrained_cost == bf_cost and constrained_resource == bf_resource}")
print()
print("Takeaway: plain SP is polynomial; ONE resource budget makes it the")
print("Resource-Constrained Shortest Path -- (weakly) NP-hard with one integer")
print("resource, the pseudo-polynomial labeling DP above. It is the PRICING")
print("subproblem inside column generation: min-reduced-cost path under a route limit.")

# %% [markdown]
# ## Shared styling helpers for the figures.

# %%
NODE_SIZE = 1100

# The two long crossing arcs (A->D and B->C) pass through the center; give them a
# stronger curve so their labels separate instead of stacking at the midpoint.
CROSS = {("A", "D"), ("B", "C")}


def rad_of(u, v):
    return 0.30 if (u, v) in CROSS else 0.12


def arc_label(u, v):
    d = G[u][v]
    return f"{d['cost']} / {d['resource']}"


def draw_edge_group(ax, edges, color, width, zorder, style="-", label_color=None,
                    label_fs=10, labels=True):
    """Draw a set of edges, each with its own curvature, labels on-arc."""
    for u, v in edges:
        lab = {(u, v): arc_label(u, v)} if labels else None
        aeviz.draw_curved_edges(
            ax, POS, [(u, v)], rad=rad_of(u, v), color=color, width=width,
            node_size=NODE_SIZE, zorder=zorder, style=style, labels=lab,
            label_color=label_color or aeviz.PALETTE["ink"], label_fontsize=label_fs)


def draw_nodes(ax):
    for n in NODES:
        x, y = POS[n]
        if n in (S, T):
            fc, tc = aeviz.PALETTE["good"] if n == S else aeviz.PALETTE["warn"], "white"
        else:
            fc, tc = aeviz.PALETTE["node_face"], "white"
        ax.scatter([x], [y], s=NODE_SIZE, c=fc, edgecolors=aeviz.PALETTE["node_edge"],
                   linewidths=1.6, zorder=4)
        ax.text(x, y, n, ha="center", va="center", fontsize=12, fontweight="bold",
                color=tc, zorder=5)


def frame(ax, title):
    xs = [p[0] for p in POS.values()]
    ys = [p[1] for p in POS.values()]
    ax.set_xlim(min(xs) - 0.5, max(xs) + 0.7)
    ax.set_ylim(min(ys) - 0.7, max(ys) + 0.7)
    ax.axis("off")
    ax.set_title(title, fontsize=12.5, color=aeviz.PALETTE["ink"])


# %% [markdown]
# ## Figure 1: the instance. Each arc labeled `cost / resource`. S and T marked.

# %%
fig, ax = plt.subplots(figsize=(9.5, 5.2))
draw_edge_group(ax, G.edges(), aeviz.PALETTE["faded_dark"], 1.6, zorder=1)
draw_nodes(ax)
frame(ax, f"Instance: arcs labeled  cost / resource    (budget R = {R})")
ax.text(0.5 * (POS[S][0] + POS[T][0]), min(p[1] for p in POS.values()) - 0.55,
        "each arc spends `resource`; the total along the S->T path must stay <= R",
        ha="center", va="center", fontsize=9.5, color=aeviz.PALETTE["faded_dark"])
aeviz.save(fig, "01_network")
plt.close(fig)

# %% [markdown]
# ## Figure 2: the punchline. Cheapest-but-INFEASIBLE path vs constrained optimum.

# %%
def edge_pairs(path):
    return set(zip(path[:-1], path[1:]))


unc_edges = edge_pairs(unconstrained_path)
con_edges = edge_pairs(constrained_path)
bg_edges = [e for e in G.edges() if e not in unc_edges and e not in con_edges]

fig, ax = plt.subplots(figsize=(9.5, 5.4))
draw_edge_group(ax, bg_edges, aeviz.PALETTE["faded"], 1.2, zorder=1,
                label_color=aeviz.PALETTE["faded_dark"], label_fs=9)
# cheapest but over budget: red, dashed
draw_edge_group(ax, unc_edges, "#d1495b", 3.0, zorder=2, style=(0, (5, 3)),
                label_color="#d1495b")
# constrained optimum: blue, solid
draw_edge_group(ax, con_edges, aeviz.PALETTE["path"], 3.0, zorder=3,
                label_color=aeviz.PALETTE["path"])
draw_nodes(ax)
frame(ax, "Cheapest path is illegal; the legal path costs more")

handles = [
    plt.Line2D([0], [0], color="#d1495b", lw=3, ls="--",
               label=f"cheapest (ignore R): cost {unconstrained_cost}, "
                     f"resource {unconstrained_resource} > {R}  INFEASIBLE"),
    plt.Line2D([0], [0], color=aeviz.PALETTE["path"], lw=3,
               label=f"constrained optimum: cost {constrained_cost}, "
                     f"resource {constrained_resource} <= {R}"),
]
leg = ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.16),
                frameon=True, fontsize=9.5, ncol=1)
leg.get_frame().set_facecolor((0.10, 0.14, 0.20, 0.82))
leg.get_frame().set_edgecolor(aeviz.PALETTE["ink"])
for txt in leg.get_texts():
    txt.set_color(aeviz.PALETTE["ink"])
aeviz.save(fig, "02_two_paths")
plt.close(fig)

# %% [markdown]
# ## Figure 3: the (resource, cost) trade-off of S->T paths, with the budget cut.
# Faded gray dots = every simple S->T path (the cheapest one sits to the RIGHT of
# the budget line: low cost, too much resource). Blue dots = the Pareto-nondominated
# feasible labels the label-setting DP actually keeps. The chosen optimum (cheapest
# feasible) is circled. Shows WHY the cheap path loses: it is right of the budget.

# %%
fig, ax = plt.subplots(figsize=(7.8, 5.0))
all_pts = [(path_resource(p), path_cost(p)) for p in all_paths]
ymax = max(c for _, c in all_pts)

# budget line
ax.axvline(R, color=aeviz.PALETTE["warn"], ls=":", lw=1.6, zorder=1)
ax.text(R - 0.2, ymax - 1.0, "budget\nR = 10",
        color=aeviz.PALETTE["weight"], fontsize=10, ha="right", va="top")

# all enumerated S->T paths (background): light dots; those right of R are illegal
ax.scatter([r for r, _ in all_pts], [c for _, c in all_pts], s=70,
           c=aeviz.PALETTE["faded"], edgecolors=aeviz.PALETTE["faded_dark"],
           linewidths=1.0, zorder=2, label="some S->T path")

# the cheapest path overall (illegal: over budget) -- annotate it as the temptation
ax.annotate(f"cheapest path\ncost {unconstrained_cost}, resource "
            f"{unconstrained_resource} > {R}\n(over budget)",
            (unconstrained_resource, unconstrained_cost),
            textcoords="offset points", xytext=(-12, 6), ha="right", fontsize=9,
            color="#d1495b")

# feasible Pareto labels kept by the DP
feas = sorted(all_labels[T], key=lambda x: x.resource)
ax.scatter([x.resource for x in feas], [x.cost for x in feas], s=95,
           c=aeviz.PALETTE["path"], edgecolors="white", linewidths=1.2,
           zorder=3, label="feasible Pareto label (kept by DP)")

# the cheapest feasible label (the chosen optimum): circle it
ax.scatter([best_label.resource], [best_label.cost], s=320, facecolors="none",
           edgecolors="#d1495b", linewidths=2.4, zorder=4)
ax.annotate(f"chosen: cost {best_label.cost}, res {best_label.resource}",
            (best_label.resource, best_label.cost),
            textcoords="offset points", xytext=(10, 12), fontsize=9.5,
            color="#d1495b")

ax.set_xlabel("resource consumed along S->T path")
ax.set_ylabel("path cost")
ax.set_title("Pareto labels arriving at T (label-setting DP frontier)",
             fontsize=12.5, color=aeviz.PALETTE["ink"])
ax.grid(True, color=aeviz.PALETTE["faded"], lw=0.8, alpha=0.4)
leg = ax.legend(loc="upper right", frameon=True, fontsize=9)
leg.get_frame().set_facecolor((0.10, 0.14, 0.20, 0.82))
leg.get_frame().set_edgecolor(aeviz.PALETTE["ink"])
for txt in leg.get_texts():
    txt.set_color(aeviz.PALETTE["ink"])
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
aeviz.save(fig, "03_pareto_labels")
plt.close(fig)

print("\nFigures written: 01_network, 02_two_paths, 03_pareto_labels (.png + .svg)")
