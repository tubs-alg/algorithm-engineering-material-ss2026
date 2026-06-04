# %% [markdown]
# Kidney exchange as maximum-weight matching on a GENERAL (non-bipartite) graph.
#
# What this file contains
#   A small synthetic kidney-exchange instance whose nodes are patient-donor
#   PAIRS, drawn so the two roles are explicit: every pair shows its DONOR (gives
#   a kidney) and its PATIENT/RECEIVER (needs one). A feasible 2-way swap between
#   pairs A and B is the MUTUAL pair of directed donations
#       A.donor -> B.patient   AND   B.donor -> A.patient,
#   which collapses to one undirected edge. The maximum set of disjoint swaps is a
#   maximum-weight matching, solved with networkx (Edmonds' blossom). The instance
#   contains an odd cycle (triangle), so the graph is NOT bipartite and the LP
#   relaxation is no longer integral.
#   Non-goal: 3-way and longer exchanges (directed cycle cover / ILP, not plain
#   matching). We model 2-way swaps only and say so.
#
# Why it exists
#   Teaching snippet for L08 (Graph & Network Algorithms), pillar 2 (Matching):
#   (1) compatibility is DIRECTIONAL -- a donor gives to the OTHER pair's patient,
#   so a node is really a (donor, receiver) unit, and a swap is two crossing
#   donations; (2) the moment the swap graph stops being bipartite you leave the
#   easy world -- blossom still solves it in P, LP rounding does not.
#
#   Honesty note baked into the design: with BLOOD TYPE alone, 2-way exchange is
#   provably BIPARTITE (O-receivers need O-donors, who never join the pool; so
#   matchable receivers are A or B, and two same-type receivers can never swap).
#   The odd cycles come from HLA tissue CROSSMATCH (patient sensitization), not
#   ABO. We therefore treat compatibility as given clinical data (ABO + crossmatch)
#   rather than deriving every arc from a blood-type label that would imply a
#   bipartite graph.
#
# How to run
#   conda activate mo312 && python solve.py
#   Produces 00_swap_anatomy, 01_compatibility_graph, 02_matching,
#   03_odd_cycle_lp (.png + .svg) and prints a short summary to stdout.
#
# When it changes
#   If the instance is retuned (more pairs, different weights) or the figure
#   styling needs to match the slide deck. Keep it deterministic and self-contained.

# %%
import matplotlib

matplotlib.use("Agg")  # headless: write files, never open a window

import sys

sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/week07-l08-graph-algorithms/snippets",
)

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import aeviz

aeviz.init_style()

SEED = 7
np.random.seed(SEED)

# Role colors: donor "gives" (green), patient "needs" (amber). Shared palette.
DONOR_C = aeviz.PALETTE["good"]     # green: the donor (gives a kidney)
RECV_C = aeviz.PALETTE["warn"]      # amber: the patient/receiver (needs one)
CAPSULE = "#39526d"                 # dark panel capsule behind a pair's two roles
CAPSULE_EDGE = "#9fb0c0"
ODD_COLOR = "#d1495b"
PICK_COLOR = "#7fbf7b"
GREY_CAP = "#39414d"
GREY_EDGE = "#5a6470"
GREY_TEXT = "#9a9a9a"

# %% [markdown]
# ## Instance
# 9 incompatible patient-donor pairs P0..P8. Compatibility (ABO blood type AND a
# negative tissue crossmatch) is GIVEN. A feasible 2-way swap {A, B} exists when
# A.donor -> B.patient and B.donor -> A.patient are both compatible; weight =
# expected transplant quality (1..10). The instance is hand-built so that:
#   - it contains a triangle P0-P1-P2 (an odd cycle => non-bipartite),
#   - a 6-pair cluster on the right matches perfectly on its own,
#   - so one triangle pair is FORCED to stay unmatched (the odd-cycle obstruction).

# %%
# Pair CENTER positions (hand-placed for stable, readable geometry).
center = {
    # the triangle (odd cycle), reaching the rest by a single stem from P2
    "P0": (0.4, 3.0),
    "P1": (2.1, 3.5),
    "P2": (2.1, 1.9),
    # a matchable 6-pair cluster on the right (even, easily perfectly matched)
    "P3": (4.1, 3.3),
    "P4": (6.0, 3.0),
    "P5": (6.8, 1.4),
    "P6": (5.6, 0.1),
    "P7": (3.7, 0.2),
    "P8": (3.5, 1.7),
}

# Within a capsule: donor sub-node left, receiver sub-node right.
ROLE_DX = 0.30
CAP_W, CAP_H = 0.96, 0.62


def donor_xy(p):
    x, y = center[p]
    return (x - ROLE_DX, y)


def recv_xy(p):
    x, y = center[p]
    return (x + ROLE_DX, y)


# Feasible 2-way swaps with expected transplant quality. Same topology as the
# original instance: the right cluster matches internally (high weights), the
# stem P2-P8 is never used at optimum, the triangle keeps one pair unmatched.
swaps = [
    # the odd cycle (triangle): three mutually feasible swaps
    ("P0", "P1", 6.0),
    ("P1", "P2", 7.0),
    ("P0", "P2", 5.0),
    # the triangle's ONLY link to the rest (single stem from P2)
    ("P2", "P8", 3.0),
    # right cluster: a 6-cycle P3-P4-P5-P6-P7-P8 plus a chord, perfectly matchable
    ("P3", "P4", 9.0),
    ("P4", "P5", 8.0),
    ("P5", "P6", 9.0),
    ("P6", "P7", 8.0),
    ("P7", "P8", 9.0),
    ("P8", "P3", 8.0),
    ("P3", "P6", 5.0),
]

G = nx.Graph()
G.add_nodes_from(center)
for u, v, w in swaps:
    G.add_edge(u, v, weight=w)

ODD_CYCLE = ["P0", "P1", "P2"]
odd_cycle_edges = [("P0", "P1"), ("P1", "P2"), ("P0", "P2")]

assert not nx.is_bipartite(G), "instance must be non-bipartite to make the point"

# %% [markdown]
# ## Solve: Edmonds' blossom (maximum-cardinality, maximum-weight matching)

# %%
matching = nx.max_weight_matching(G, maxcardinality=True)
matched_edges = sorted(tuple(sorted(e)) for e in matching)
matched_nodes = set()
for u, v in matched_edges:
    matched_nodes.update((u, v))

total_quality = sum(G[u][v]["weight"] for u, v in matched_edges)
n_pairs = G.number_of_nodes()
n_transplanted = 2 * len(matched_edges)  # each swap transplants both patients
unmatched = sorted(set(G.nodes) - matched_nodes)

print("=== Kidney exchange (2-way swaps, general-graph matching) ===")
print(f"Pairs (nodes):            {n_pairs}")
print(f"Feasible swaps (edges):   {G.number_of_edges()}")
print(f"Chosen swaps (matching):  {len(matched_edges)}")
for u, v in matched_edges:
    print(f"    {u} <-> {v}   quality {G[u][v]['weight']:.0f}")
print(f"Patients transplanted:    {n_transplanted} / {n_pairs}")
print(f"Total expected quality:   {total_quality:.0f}")
print(f"Unmatched pairs:          {unmatched if unmatched else 'none'}")

print()
print("Each node is a (donor, patient) PAIR; a swap is two crossing donations:")
print("  A.donor -> B.patient and B.donor -> A.patient (mutual => one edge).")
print(f"Odd cycle (blossom):      {' - '.join(ODD_CYCLE)} - {ODD_CYCLE[0]}")
print("  Length 3 => not bipartite. A triangle holds at most ONE matching edge,")
print("  so one of its 3 pairs is forced to stay unmatched (here P0). The LP")
print("  relaxation would put x=0.5 on each triangle edge (value 1.5), a")
print("  fractional vertex no rounding fixes: the integrality gap.")
print()
print("ABO footnote: blood type ALONE makes 2-way exchange bipartite; the odd")
print("cycle here is driven by HLA crossmatch (patient sensitization), as in reality.")

# %% [markdown]
# ## Drawing helpers: a pair is a capsule holding a donor + a receiver glyph.

# %%
def draw_pair(ax, p, *, capsule=CAPSULE, capsule_edge=CAPSULE_EDGE,
              donor_c=DONOR_C, recv_c=RECV_C, label_color=aeviz.PALETTE["ink"],
              ring_color=None, ring_w=0.0, dim=False):
    """Draw one patient-donor pair as a capsule with a donor and a receiver glyph.

    donor = filled circle 'D' (gives), receiver = ring 'R' (needs). `dim` greys
    the whole pair (used for the forced-unmatched pair). `ring_color`/`ring_w`
    draw an outer ring around the capsule (used to flag the odd cycle).
    """
    cx, cy = center[p]
    if dim:
        capsule, capsule_edge = GREY_CAP, GREY_EDGE
        donor_c = recv_c = "#d7d7d7"
        label_color = GREY_TEXT
    # capsule
    box = FancyBboxPatch(
        (cx - CAP_W / 2, cy - CAP_H / 2), CAP_W, CAP_H,
        boxstyle="round,pad=0.02,rounding_size=0.16",
        fc=capsule, ec=ring_color or capsule_edge,
        lw=ring_w if ring_color else 1.2, zorder=2,
    )
    ax.add_patch(box)
    # pair label above the capsule
    ax.text(cx, cy + CAP_H / 2 + 0.16, p, fontsize=10.5, fontweight="bold",
            ha="center", va="bottom", color=label_color, zorder=6)
    # donor (filled) and receiver (ring)
    dx, dy = donor_xy(p)
    rx, ry = recv_xy(p)
    ax.scatter([dx], [dy], s=430, c=donor_c, edgecolors="#2b3a2b",
               linewidths=1.2, zorder=4)
    ax.scatter([rx], [ry], s=430, facecolors="white", edgecolors=recv_c,
               linewidths=2.6, zorder=4)
    ax.text(dx, dy, "D", fontsize=8.5, fontweight="bold", ha="center",
            va="center", color="white" if not dim else GREY_TEXT, zorder=5)
    ax.text(rx, ry, "R", fontsize=8.5, fontweight="bold", ha="center",
            va="center", color=recv_c if not dim else GREY_TEXT, zorder=5)


def swap_edge(ax, u, v, *, color, width, zorder=1.2, alpha=1.0):
    """Undirected swap edge between two pair capsules.

    Drawn at low zorder so it tucks BEHIND the capsules (zorder 2): the line
    appears to connect capsule borders instead of crossing their interiors.
    """
    p0, p1 = center[u], center[v]
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=color, lw=width,
            alpha=alpha, zorder=zorder, solid_capstyle="round")


def edge_label(ax, u, v, text, color):
    mx = (center[u][0] + center[v][0]) / 2
    my = (center[u][1] + center[v][1]) / 2
    ax.text(mx, my, text, fontsize=9, ha="center", va="center", color=color,
            bbox=dict(boxstyle="round,pad=0.15", fc=(0.10, 0.14, 0.20, 0.85),
                      ec="none"), zorder=7)


def role_legend(ax):
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=DONOR_C,
               markeredgecolor="#2b3a2b", markersize=12, label="donor (gives a kidney)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
               markeredgecolor=RECV_C, markeredgewidth=2.4, markersize=12,
               label="patient (needs a kidney)"),
        Line2D([0], [0], color=ODD_COLOR, lw=3.2, label="odd cycle (not bipartite)"),
        Line2D([0], [0], color=PICK_COLOR, lw=4.0, label="chosen 2-way swap"),
    ]
    return handles


# %% [markdown]
# ## Figure 0 (NEW): anatomy of a 2-way swap -- the donor/receiver distinction.
# Two pairs, the two crossing directed donations, and the note that together they
# collapse to ONE undirected matching edge.

# %%
fig, ax = plt.subplots(figsize=(8.4, 4.2))

# local centers for a clean two-pair picture
anat = {"A": (1.2, 1.4), "B": (5.4, 1.4)}
old_center = center
center = anat  # reuse draw_pair for the two anatomy pairs


def _arrow(ax, p0, p1, color, rad, label, lx_dy):
    a = FancyArrowPatch(p0, p1, connectionstyle=f"arc3,rad={rad}",
                        arrowstyle="-|>", mutation_scale=18, lw=2.6,
                        color=color, shrinkA=10, shrinkB=10, zorder=3)
    ax.add_patch(a)
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    ax.text(mx, my + lx_dy, label, fontsize=10, ha="center", va="center",
            color=color, bbox=dict(boxstyle="round,pad=0.2",
                                   fc=(0.10, 0.14, 0.20, 0.85),
                                   ec="none"), zorder=6)


draw_pair(ax, "A")
draw_pair(ax, "B")
# A.donor -> B.patient (curve up), B.donor -> A.patient (curve down)
_arrow(ax, donor_xy("A"), recv_xy("B"), DONOR_C, 0.32,
       "A's donor  →  B's patient", 0.95)
_arrow(ax, donor_xy("B"), recv_xy("A"), "#5aa86f", -0.32,
       "B's donor  →  A's patient", -0.95)
ax.text(3.3, 1.4, "=\none\nmatching\nedge", fontsize=10, ha="center",
        va="center", color=aeviz.PALETTE["ink"], fontweight="bold")
ax.set_xlim(-0.2, 7.0)
ax.set_ylim(-0.9, 3.7)
ax.set_axis_off()
ax.set_title(
    "Anatomy of a 2-way swap: each node is a (donor, patient) pair\n"
    "compatibility is directional -- a donor gives to the OTHER pair's patient",
    fontsize=11.5, color=aeviz.PALETTE["ink"],
)
aeviz.legend_outside(ax, handles=role_legend(ax)[:2], fontsize=9, loc="lower center",
                     anchor=(0.5, -0.02), ncol=2)
aeviz.save(fig, "00_swap_anatomy")
plt.close(fig)
center = old_center  # restore the instance geometry

# %% [markdown]
# ## Figure 1: compatibility graph -- pairs as donor/receiver capsules, odd cycle red.

# %%
fig_graph, ax = plt.subplots(figsize=(9.0, 6.0))
odd_set = {tuple(sorted(e)) for e in odd_cycle_edges}

for u, v, d in G.edges(data=True):
    is_odd = tuple(sorted((u, v))) in odd_set
    swap_edge(ax, u, v, color=ODD_COLOR if is_odd else aeviz.PALETTE["faded_dark"],
              width=3.6 if is_odd else 2.0, zorder=1.6 if is_odd else 1.2)
    edge_label(ax, u, v, f"{d['weight']:.0f}",
               ODD_COLOR if is_odd else aeviz.PALETTE["weight"])

for p in G.nodes:
    if p in ODD_CYCLE:
        draw_pair(ax, p, ring_color=ODD_COLOR, ring_w=2.8)
    else:
        draw_pair(ax, p)

ax.set_xlim(-0.7, 7.6)
ax.set_ylim(-0.9, 4.4)
ax.set_axis_off()
ax.set_title(
    "Kidney exchange: each node is a (donor D, patient R) pair, each edge a feasible 2-way swap\n"
    "Odd cycle P0-P1-P2 (red) makes the swap graph non-bipartite",
    fontsize=11.5, color=aeviz.PALETTE["ink"],
)
aeviz.legend_outside(ax, handles=role_legend(ax)[:3], fontsize=9)
# Saved together with figure 2 by save_aligned (below) so they share one canvas.

# %% [markdown]
# ## Figure 2: chosen disjoint swaps bold, the forced-unmatched pair greyed.

# %%
fig_match, ax = plt.subplots(figsize=(9.0, 6.0))
matched_set = set(matched_edges)

for u, v, d in G.edges(data=True):
    if tuple(sorted((u, v))) in matched_set:
        swap_edge(ax, u, v, color=PICK_COLOR, width=4.4, zorder=1.6)
        edge_label(ax, u, v, f"{d['weight']:.0f}", PICK_COLOR)
    else:
        swap_edge(ax, u, v, color=aeviz.PALETTE["faded"], width=1.5, zorder=1.0)

for p in G.nodes:
    draw_pair(ax, p, dim=(p in unmatched),
              capsule="#2f4a3a" if p in matched_nodes else CAPSULE,
              capsule_edge=PICK_COLOR if p in matched_nodes else CAPSULE_EDGE)

ax.set_xlim(-0.7, 7.6)
ax.set_ylim(-0.9, 4.4)
ax.set_axis_off()
ax.set_title(
    f"Maximum matching (Edmonds' blossom): {len(matched_edges)} swaps, "
    f"{n_transplanted}/{n_pairs} patients transplanted, quality {total_quality:.0f}\n"
    "Bold green = chosen swaps; grey = forced unmatched (the odd-cycle leftover)",
    fontsize=11.5, color=aeviz.PALETTE["ink"],
)
aeviz.legend_outside(ax, handles=role_legend(ax)[3:], fontsize=9)
# Crop the compatibility graph and the matching to one common bbox so the pair
# capsules sit at identical pixels across the .r-stack overlay (the two frames
# have different titles/legends that would otherwise size their crops apart).
aeviz.save_aligned([(fig_graph, "01_compatibility_graph"),
                    (fig_match, "02_matching")])

# %% [markdown]
# ## Figure 3 (optional): the integrality gap on a triangle.
# A standalone triangle. The LP relaxation of the matching polytope (without
# blossom inequalities) puts x=0.5 on every edge: each node's degree constraint
# is met (0.5 + 0.5 = 1), total value 1.5 > the integral optimum of 1.

# %%
tri_pos = {"A": (0.0, 0.0), "B": (2.0, 0.0), "C": (1.0, 1.7)}
T = nx.Graph()
T.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])

fig, ax = plt.subplots(figsize=(5.6, 4.6))
nx.draw_networkx_edges(T, tri_pos, ax=ax, edge_color=ODD_COLOR, width=3.4)
nx.draw_networkx_nodes(T, tri_pos, ax=ax, node_size=1400, node_color="#5a2730",
                       edgecolors=ODD_COLOR, linewidths=2.4)
nx.draw_networkx_labels(T, tri_pos, ax=ax, font_size=13, font_weight="bold",
                        font_color="#ffffff")
aeviz.straight_edge_labels(
    ax, tri_pos, {e: "x = 0.5" for e in T.edges}, font_size=11,
    color=aeviz.PALETTE["ink"]
)
ax.set_axis_off()
ax.margins(0.18)
ax.set_title(
    "LP relaxation is fractional here\n"
    "x=0.5 on each edge: LP value 1.5, integral optimum 1",
    fontsize=12, color=aeviz.PALETTE["ink"],
)
aeviz.save(fig, "03_odd_cycle_lp")
plt.close(fig)

# %%
print("\nFigures written: 00_swap_anatomy, 01_compatibility_graph, "
      "02_matching, 03_odd_cycle_lp (.png + .svg)")
