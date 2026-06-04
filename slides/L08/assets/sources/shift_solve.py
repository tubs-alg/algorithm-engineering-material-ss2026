"""
DAG shortest path with negative weights -> shift-planning / pricing intuition.

What this file contains:
  A small, synthetic layered shift DAG for ONE employee over a 5-day horizon.
  EVERY day offers the SAME four options -- Early / Late / Night / Rest -- so the
  nodes form a clean R-E-L-N x day grid. All the scheduling rules live on the
  EDGES: an arc day_d -> day_{d+1} exists only if the rest law permits that
  transition. Edge weight = shift cost minus a bonus that is larger for
  hard-to-fill slots, so some NET weights are negative. The most-negative path is
  the roster that best relieves the hard slots while staying legal.

Non-goal:
  This is NOT a column-generation implementation. No LP duals, no reduced-cost
  derivation. We only open the door: a shortest path through a per-employee
  shift DAG is exactly the "pricing" subproblem that generates one promising
  candidate schedule (a column). We then politely close it again.

Why it exists:
  Teaching point for L08 (Shortest Paths): on a DAG you can run shortest path
  with NEGATIVE edge weights in LINEAR time via a single relaxation pass in
  topological order. Dijkstra cannot do this; Bellman-Ford can but is slower.
  Secondary point: realistic constraints (rest law) are pure EDGE structure --
  same nodes every day, the legality is what arcs you draw.

How to run:
  python solve.py
  (conda env mo312: networkx 3.2.1, matplotlib, numpy). Writes PNG + SVG into
  this folder and prints a short summary.

When it would change:
  If the lecture wants a different horizon, different rest thresholds, or a
  different bonus scheme. Keep it light and heuristic; do not grow it into a
  real CG loop.
"""

# %%
import matplotlib

matplotlib.use("Agg")  # headless, deterministic file output

import sys

sys.path.insert(0, "/home/krupke/Cloud/Dropbox/Secretary/cases/"
                   "course-ae-ss26-internal/week07-l08-graph-algorithms/snippets")
import aeviz

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

aeviz.init_style()

HERE = __file__.rsplit("/", 1)[0]

# %%
# ---------------------------------------------------------------------------
# Instance: a layered shift grid for one employee over a 5-day horizon.
#
# Every day offers the SAME four options. Keeping the node set uniform is the
# point: the realistic scheduling rules are NOT about which shifts exist on a
# given day, they are about which TRANSITIONS between consecutive days are
# allowed. So nodes = {E, L, N, R} x {Mon..Fri}; the rules live on the edges.
#
# Clock times (used only to derive legality and to label the rows):
#   E  early   06:00 - 14:00
#   L  late    14:00 - 22:00
#   N  night   22:00 - 06:00 (+1 day)   <- hard to fill
#   R  rest    (day off)
# ---------------------------------------------------------------------------

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
SHIFTS = ["E", "L", "N", "R"]  # same options every day

# Clock hours for the rest-law calculation (N ends at 06:00 the NEXT day = 30).
START = {"E": 6.0, "L": 14.0, "N": 22.0}
END = {"E": 14.0, "L": 22.0, "N": 30.0}
MIN_REST = 11.0  # EU/German working-time minimum daily rest, in hours.

# Base cost of working each shift (rest is a cheap, mildly positive filler).
BASE_COST = {"E": 5, "L": 5, "N": 7, "R": 1}

# Hard-to-fill slots carry a bonus (cost - bonus < 0 => the path is PULLED here).
# Mostly understaffed nights, plus one critical early shift -- which is exactly
# the slot the rest law makes awkward to reach (see the N->E rule below).
BONUS = {
    ("Tue", "N"): 12,   # net -5  hard night
    ("Thu", "N"): 13,   # net -6  hard night
    ("Wed", "E"): 9,    # net -4  hard early (critical morning delivery)
}

HARD = set(BONUS)  # the slots with a bonus, ringed in the figures


def node_id(day: str, label: str) -> str:
    return f"{day}:{label}"


def net_weight(day: str, label: str) -> float:
    """Cost of WORKING (day, label): base cost minus any hard-to-fill bonus."""
    return BASE_COST[label] - BONUS.get((day, label), 0)


# %%
# ---------------------------------------------------------------------------
# Legality between consecutive days = the rest law, computed from clock times.
#
# A worker needs at least MIN_REST hours between the END of one shift and the
# START of the next day's shift. With E/L/N at 06/14/22 this forbids exactly the
# "rotate backwards" transitions:
#   L -> E   (22:00 -> 06:00 = 8 h rest)   forbidden
#   N -> L   (06:00 -> 14:00 = 8 h rest)   forbidden
#   N -> E   (06:00 -> 06:00 = 0 h rest)   forbidden   <- the headline rule
# Forward rotation E -> L -> N is always fine, as is N -> N (16 h), and a rest
# day R breaks any chain (you are off, so no rest-law violation either way).
# ---------------------------------------------------------------------------


def legal(prev_label: str, next_label: str) -> bool:
    if prev_label == "R" or next_label == "R":
        return True  # a day off never violates the rest rule
    rest_hours = (START[next_label] + 24.0) - END[prev_label]
    return rest_hours >= MIN_REST


# Sanity: the three rules we advertise really are the forbidden ones.
assert not legal("N", "E") and not legal("N", "L") and not legal("L", "E")
assert legal("E", "L") and legal("L", "N") and legal("N", "N")


def build_graph(transition_ok) -> nx.DiGraph:
    """Layered shift DAG. `transition_ok(prev, next)` decides which day_d ->
    day_{d+1} arcs exist; passing `legal` gives the realistic graph, passing
    `lambda *_: True` gives the rule-ignoring 'naive' graph for contrast."""
    g = nx.DiGraph()
    g.add_node("SRC")
    g.add_node("SNK")
    for day in DAYS:
        for label in SHIFTS:
            g.add_node(node_id(day, label))
    # SRC -> first day (a fresh worker may start on any shift).
    for label in SHIFTS:
        g.add_edge("SRC", node_id(DAYS[0], label),
                   weight=net_weight(DAYS[0], label))
    # day d -> day d+1, only legal transitions.
    for d in range(len(DAYS) - 1):
        day, nxt = DAYS[d], DAYS[d + 1]
        for p in SHIFTS:
            for n in SHIFTS:
                if transition_ok(p, n):
                    g.add_edge(node_id(day, p), node_id(nxt, n),
                               weight=net_weight(nxt, n))
    # last day -> SNK (worker goes home; no constraint, no cost).
    for label in SHIFTS:
        g.add_edge(node_id(DAYS[-1], label), "SNK", weight=0)
    assert nx.is_directed_acyclic_graph(g), "graph must be a DAG"
    return g


G = build_graph(legal)
G_naive = build_graph(lambda *_: True)  # ignores the rest law, for the contrast

# %%
# ---------------------------------------------------------------------------
# Linear-time DAG shortest path with NEGATIVE weights.
#
# One relaxation pass in topological order. No priority queue, no reweighting,
# negatives are fine. This is the whole point: Dijkstra would be WRONG here
# because a later, cheaper edge could improve an already-"settled" node.
# ---------------------------------------------------------------------------


def dag_shortest_path(graph: nx.DiGraph, source: str, sink: str):
    order = list(nx.topological_sort(graph))
    dist = {v: np.inf for v in graph.nodes}
    pred = {v: None for v in graph.nodes}
    dist[source] = 0.0
    for u in order:  # topological order => all predecessors of v done before v
        if dist[u] == np.inf:
            continue
        for v in graph.successors(u):
            cand = dist[u] + graph[u][v]["weight"]
            if cand < dist[v]:
                dist[v] = cand
                pred[v] = u
    path = []
    cur = sink
    while cur is not None:
        path.append(cur)
        cur = pred[cur]
    path.reverse()
    return path, dist[sink]


dag_path, dag_cost = dag_shortest_path(G, "SRC", "SNK")
naive_path, naive_cost = dag_shortest_path(G_naive, "SRC", "SNK")

# Cross-check with Bellman-Ford (handles negatives too); must agree.
bf_path = nx.bellman_ford_path(G, "SRC", "SNK", weight="weight")
bf_cost = nx.bellman_ford_path_length(G, "SRC", "SNK", weight="weight")
assert abs(dag_cost - bf_cost) < 1e-9, (dag_cost, bf_cost)

# %%
# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
roster = [n for n in dag_path if n not in ("SRC", "SNK")]
covered_hard = [n for n in roster if tuple(n.split(":")) in HARD]
naive_roster = [n for n in naive_path if n not in ("SRC", "SNK")]
naive_hard = [n for n in naive_roster if tuple(n.split(":")) in HARD]

print("=" * 68)
print("DAG shift planning -- linear-time shortest path with negatives")
print("=" * 68)
print(f"DAG?           {nx.is_directed_acyclic_graph(G)}")
print(f"nodes / arcs:  {G.number_of_nodes()} / {G.number_of_edges()} "
      f"(uniform R/E/L/N grid; legality is pure edge structure)")
print("rest law:      forbids L->E, N->L, N->E (rotate-back < 11 h rest)")
print()
print("Legal roster (most-negative path that obeys the rest law):")
print("   " + "  ->  ".join(roster))
print(f"Net cost:      {dag_cost:.0f}   covers hard slots: "
      f"{', '.join(covered_hard) if covered_hard else 'none'}")
print()
print("Naive roster (IGNORES the rest law -- illegal in reality):")
print("   " + "  ->  ".join(naive_roster))
print(f"Net cost:      {naive_cost:.0f}   covers hard slots: "
      f"{', '.join(naive_hard)}")
print(f"=> the rest law costs {dag_cost - naive_cost:+.0f}: it forbids grabbing "
      "the hard Wed-early right after the Tue night (N->E),")
print("   so the legal plan rests Wednesday instead of chaining night->early.")
print()
print(f"Bellman-Ford agrees:  cost = {bf_cost:.0f}, same path = {bf_path == dag_path}")
print()
print("Pricing intuition: this single shortest path is one promising candidate")
print("schedule (a 'column'). Repeating it per employee with updated weights is")
print("the seed of column generation / pricing -- machinery revisited later.")

# %%
# ---------------------------------------------------------------------------
# Layout: a uniform grid. Columns = days; rows = shift type, ordered by time of
# day so that forward rotation E->L->N reads DOWNWARD and the forbidden
# "rotate-back" arcs (N->E, N->L, L->E) read as upward jumps. Rest sits below.
# ---------------------------------------------------------------------------

ROW_Y = {"E": 2.0, "L": 1.0, "N": 0.0, "R": -1.0}
ROW_LABEL = {"E": "Early", "L": "Late", "N": "Night", "R": "Rest"}
x_of_day = {day: i + 1 for i, day in enumerate(DAYS)}

pos = {"SRC": (0.0, 0.6), "SNK": (len(DAYS) + 1.0, 0.6)}
for day in DAYS:
    for label in SHIFTS:
        pos[node_id(day, label)] = (float(x_of_day[day]), ROW_Y[label])

# Colors / styling. Shared aeviz palette so this figure matches the rest of the
# set; green ("good") = attractive net-negative, navy = non-negative.
ATTRACT = aeviz.PALETTE["good"]    # green: net-negative (attractive) shift node
HARDRING = aeviz.PALETTE["weight"] # gold ring: carries a hard-to-fill bonus
NORMAL = aeviz.PALETTE["settled"]  # navy: regular shift node
REST_FACE = aeviz.PALETTE["node_face"]  # darker navy: rest (clearly "off")
TERMINAL = aeviz.PALETTE["faded"]  # slate terminal nodes
NODE_RING = aeviz.PALETTE["node_edge"]  # light-blue ring on regular nodes
INK = aeviz.PALETTE["ink"]         # light text
PATH_EDGE = "#ff6f6f"              # bright red highlight for the chosen roster
FORBID = "#ff7a8a"                 # dashed red: a forbidden (illegal) transition
NEG_EDGE = aeviz.PALETTE["good"]   # green for negative-weight (attractive) arcs
POS_EDGE = aeviz.PALETTE["faded"]  # faint slate for non-negative arcs

path_edges = set(zip(dag_path[:-1], dag_path[1:]))

# The single forbidden arc we draw explicitly to make the rest law concrete:
# the path would love Tue:N -> Wed:E (hard night straight into hard early), but
# night->early gives zero rest, so it is illegal and absent from G.
FORBID_ARC = (node_id("Tue", "N"), node_id("Wed", "E"))


def node_face(n: str) -> str:
    if n in ("SRC", "SNK"):
        return TERMINAL
    day, lab = n.split(":")
    if net_weight(day, lab) < 0:
        return ATTRACT
    return REST_FACE if lab == "R" else NORMAL


def node_text(n: str) -> str:
    if n == "SRC":
        return "start"
    if n == "SNK":
        return "end"
    return n.split(":")[1]


def node_text_color(n: str) -> str:
    """Dark ink on the bright green attractive nodes; light ink on dark faces."""
    if node_face(n) == ATTRACT:
        return "#102027"
    return INK


# %%
# ---------------------------------------------------------------------------
# Figure drawing. Arcs are straight (layered DAG, adjacent columns only). To cut
# clutter we label ONLY the green negative-weight arcs (the teaching point);
# non-negative arcs recede to faint gray with no label.
# ---------------------------------------------------------------------------


def draw(ax, highlight_path: bool, show_forbidden: bool):
    # legal arcs of G
    for u, v, data in G.edges(data=True):
        w = data["weight"]
        on_path = highlight_path and (u, v) in path_edges
        show_label = (w < 0) and (v != "SNK")
        labels = {(u, v): f"{w:+.0f}"} if show_label else None

        if on_path:
            color, lw, lab_col, z = PATH_EDGE, 3.2, NEG_EDGE, 3.0
        elif w < 0:
            color, lw, lab_col, z = NEG_EDGE, 2.0, NEG_EDGE, 2.0
        else:
            color, lw, lab_col, z = POS_EDGE, 0.7, NEG_EDGE, 1.0

        aeviz.draw_curved_edges(
            ax, pos, [(u, v)], rad=0.0,
            color=color, width=lw, node_size=620,
            labels=labels, label_color=lab_col, label_fontsize=9.0,
            zorder=z,
        )

    # one explicit FORBIDDEN arc (not in G) to make the rest law visible
    if show_forbidden:
        (fu, fv) = FORBID_ARC
        ax.annotate(
            "", xy=pos[fv], xytext=pos[fu],
            arrowprops=dict(arrowstyle="-|>", color=FORBID, lw=2.2,
                            linestyle=(0, (4, 3)), shrinkA=15, shrinkB=15),
            zorder=4,
        )
        mx = (pos[fu][0] + pos[fv][0]) / 2.0
        my = (pos[fu][1] + pos[fv][1]) / 2.0
        # The arc's midpoint falls on the L row (y=1.0); drop the label below it
        # so it does not overlap the L nodes.
        ax.text(mx - 0.05, my - 0.5, "  night to early\n  forbidden (0 h rest)",
                color=FORBID, fontsize=8.5, fontweight="bold",
                ha="left", va="center", zorder=7)

    # nodes
    for n in G.nodes:
        x, y = pos[n]
        face = node_face(n)
        is_hard = (n not in ("SRC", "SNK")) and (tuple(n.split(":")) in HARD)
        ax.scatter(
            [x], [y], s=620, c=face,
            edgecolors=HARDRING if is_hard else NODE_RING,
            linewidths=2.6 if is_hard else 1.2,
            zorder=5,
        )
        ax.text(x, y, node_text(n), fontsize=8.5, fontweight="bold",
                ha="center", va="center", color=node_text_color(n), zorder=6)

    # day column headers
    for day in DAYS:
        ax.text(x_of_day[day], 2.5, day, fontsize=10, fontweight="bold",
                ha="center", va="center", color=INK)
    # row labels (with clock times) on the far left
    for lab, y in ROW_Y.items():
        ax.text(-0.55, y, ROW_LABEL[lab], fontsize=8, ha="left", va="center",
                color=aeviz.PALETTE["faded_dark"])

    ax.set_xlim(-0.7, len(DAYS) + 1.25)
    ax.set_ylim(-1.35, 2.7)
    ax.axis("off")


# Legend handles (shared)
legend_instance = [
    Patch(fc=ATTRACT, ec=NODE_RING, label="hard-to-fill slot (net cost < 0)"),
    Patch(fc=NORMAL, ec=NODE_RING, label="regular shift"),
    Patch(fc=REST_FACE, ec=NODE_RING, label="rest (day off)"),
    Line2D([0], [0], color=NEG_EDGE, lw=2, label="negative-weight arc"),
    Line2D([0], [0], color=POS_EDGE, lw=1, label="legal transition"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=NORMAL,
           markeredgecolor=HARDRING, markeredgewidth=2.4, markersize=11,
           label="carries hard-to-fill bonus"),
]

# Both figures share ONE fixed canvas layout: identical axes box plus a reserved
# legend BAND along the bottom. Putting the legend below (not on the right) keeps
# the figure close to a 5:4 aspect instead of a wide 2:1, so the diagram fills the
# width and grows taller when the slide places it in a column. Saving without a
# tight crop keeps the diagram in exactly the same place across the two reveal
# steps, even though the legend contents (and lengths) differ between them.
FIGSIZE = (9.0, 5.3)
LAYOUT = dict(left=0.03, right=0.99, top=0.90, bottom=0.10)
LEGEND_KW = dict(loc="upper center", anchor=(0.5, -0.025), ncol=3, fontsize=8)
plt.rcParams["savefig.bbox"] = None   # keep the full fixed canvas, not a tight crop

fig1, ax1 = plt.subplots(figsize=FIGSIZE)
fig1.subplots_adjust(**LAYOUT)
draw(ax1, highlight_path=False, show_forbidden=False)
ax1.set_title(
    "Shift DAG: same E/L/N/R options every day, the rest law lives on the edges",
    fontsize=12, color=INK, pad=12,
)
aeviz.legend_outside(ax1, handles=legend_instance, **LEGEND_KW)
aeviz.save(fig1, f"{HERE}/01_shift_dag")

# %%
# ---------------------------------------------------------------------------
# Figure 2: the chosen roster path highlighted = one generated column, with the
# forbidden night->early arc shown to explain why it rests on Wednesday.
# ---------------------------------------------------------------------------

legend_solution = [
    Line2D([0], [0], color=PATH_EDGE, lw=3, label="chosen roster (shortest path)"),
    Line2D([0], [0], color=FORBID, lw=2.2, linestyle=(0, (4, 3)),
           label="forbidden by rest law (night to early)"),
    Patch(fc=ATTRACT, ec=NODE_RING, label="hard-to-fill slot (net cost < 0)"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=NORMAL,
           markeredgecolor=HARDRING, markeredgewidth=2.4, markersize=11,
           label="carries hard-to-fill bonus"),
]

fig2, ax2 = plt.subplots(figsize=FIGSIZE)
fig2.subplots_adjust(**LAYOUT)
draw(ax2, highlight_path=True, show_forbidden=True)
ax2.set_title(
    f"One generated column: legal roster net cost = {dag_cost:.0f}, "
    f"covers {len(covered_hard)} hard night(s)",
    fontsize=12, color=INK, pad=12,
)
aeviz.legend_outside(ax2, handles=legend_solution, **LEGEND_KW)
aeviz.save(fig2, f"{HERE}/02_solution")

# %%
# ---------------------------------------------------------------------------
# Figures 3 + 4: the staffing-difficulty grid that MOTIVATES the DAG.
#
# Before any graph, a planner sees a demand table: for each (day, shift), how
# hard is that slot to staff. Color = difficulty (green easy -> red hard); the
# difficulty is tied to BONUS so the grid and the DAG tell the same story. A
# slot-by-slot greedy would grab the reddest cells first, but consecutive picks
# must obey the rest law: the Tue night and the very next Wed early are both
# critical, yet night->early gives zero rest and is illegal. So the slots cannot
# be filled one at a time; the whole week of transitions must be planned at once,
# which is the DAG shortest path on the following slide.
# ---------------------------------------------------------------------------

DEMAND_SHIFTS = ["E", "L", "N"]  # rest is not a slot that has to be staffed
DIFF_BASE = {"E": 0.30, "L": 0.20, "N": 0.55}
DIFF_WOBBLE = {  # small per-day variation so the grid is not perfectly banded
    ("Mon", "E"): -0.04, ("Thu", "E"): 0.05,
    ("Fri", "L"): 0.15,
    ("Mon", "N"): -0.07, ("Fri", "N"): 0.05,
}


def difficulty(day: str, label: str) -> float:
    """0 (easy) .. 1 (hard). The three BONUS slots are the hardest; deriving the
    difficulty from BONUS keeps this grid consistent with the DAG edge weights."""
    if (day, label) in BONUS:
        return min(1.0, 0.70 + 0.02 * BONUS[(day, label)])
    return DIFF_BASE[label] + DIFF_WOBBLE.get((day, label), 0.0)


DIFF = np.array([[difficulty(d, s) for d in DAYS] for s in DEMAND_SHIFTS])

# Each slot needs a HEADCOUNT of qualified workers, not one person. Capacities
# plus skill requirements are what make the real problem a big rostering / set-
# cover instance (many workers, many slots), NOT a single schedule. The single
# DAG shortest path below generates ONE worker's week (a column); covering the
# whole grid needs many. Scarce skills (star) are why the red slots are hard.
DEMAND = {  # workers required per (shift, day)
    "E": {"Mon": 3, "Tue": 3, "Wed": 4, "Thu": 3, "Fri": 3},
    "L": {"Mon": 2, "Tue": 2, "Wed": 2, "Thu": 2, "Fri": 2},
    "N": {"Mon": 2, "Tue": 2, "Wed": 1, "Thu": 2, "Fri": 2},
}
STAR = "★"  # scarce special qualification; only a few workers hold it
SKILLS = {  # skills at least one assigned worker must carry; "" = none shown
    "E": {"Mon": [], "Tue": [], "Wed": [STAR], "Thu": [], "Fri": []},
    "L": {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": []},
    "N": {"Mon": ["Sr"], "Tue": ["Sr", STAR], "Wed": ["Sr"],
          "Thu": ["Sr", STAR], "Fri": ["Sr"]},
}
TOTAL_DEMAND = sum(DEMAND[s][d] for s in DEMAND_SHIFTS for d in DAYS)

# The two hardest neighbors a greedy would want back-to-back, but the rest law
# forbids: Tue night straight into Wed early (06:00 -> 06:00 = 0 h rest).
COLLISION = (("Tue", "N"), ("Wed", "E"))

GRID_FIGSIZE = (8.2, 4.8)
GRID_LAYOUT = dict(left=0.08, right=0.995, top=0.96, bottom=0.03)


def draw_demand(ax, show_greedy: bool):
    # aspect="auto": cells fill the axes width instead of being square and
    # letterboxed (which would float the grid centered with big side margins)
    ax.imshow(DIFF, cmap="RdYlGn_r", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(DAYS)))
    ax.set_xticklabels(DAYS, fontsize=11)
    ax.xaxis.tick_top()  # days read as column headers above the grid
    ax.set_yticks(range(len(DEMAND_SHIFTS)))
    ax.set_yticklabels([ROW_LABEL[s] for s in DEMAND_SHIFTS], fontsize=9)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    # thin separators (slide-bg color) bounded to the grid, so they read as
    # tiles and do not stub down into the note band below the last row
    sep = aeviz.PALETTE["node_face"]
    nD, nS = len(DAYS), len(DEMAND_SHIFTS)
    for gx in np.arange(-0.5, nD + 0.5, 1):
        ax.plot([gx, gx], [-0.5, nS - 0.5], color=sep, lw=2.5, zorder=2)
    for gy in np.arange(-0.5, nS + 0.5, 1):
        ax.plot([-0.5, nD - 0.5], [gy, gy], color=sep, lw=2.5, zorder=2)

    for i, s in enumerate(DEMAND_SHIFTS):
        for j, d in enumerate(DAYS):
            hard = (d, s) in BONUS
            cap = DEMAND[s][d]
            sk = SKILLS[s][d]
            # headcount (capacity) stays centered in EVERY cell so the numbers
            # line up across a row; skills, when present, sit at the cell bottom
            ax.text(j, i, str(cap), ha="center", va="center", color="#102027",
                    fontweight="bold", fontsize=17 if hard else 15, zorder=4)
            if sk:
                ax.text(j, i + 0.32, "  ".join(sk), ha="center", va="center",
                        color="#16240f", fontsize=9.5, fontweight="bold",
                        zorder=4)
    for (d, s) in BONUS:  # ring the hard-to-fill slots
        j, i = DAYS.index(d), DEMAND_SHIFTS.index(s)
        ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                   edgecolor=HARDRING, linewidth=3.0, zorder=5))

    if show_greedy:
        (au, av) = COLLISION
        ju, iu = DAYS.index(au[0]), DEMAND_SHIFTS.index(au[1])
        jv, iv = DAYS.index(av[0]), DEMAND_SHIFTS.index(av[1])
        # straight dashed arrow from just inside the top of the night cell to
        # just inside the bottom of the early cell, clear of the centered digits
        ax.annotate("", xy=(jv, iv + 0.40), xytext=(ju, iu - 0.40),
                    arrowprops=dict(arrowstyle="-|>", color=FORBID, lw=2.4,
                                    linestyle=(0, (5, 3)), shrinkA=2, shrinkB=2),
                    zorder=6)
        ax.text((len(DAYS) - 1) / 2.0, len(DEMAND_SHIFTS) - 0.5 + 0.24,
                "night to early: 0 h rest, forbidden", color=FORBID,
                fontsize=9.5, fontweight="bold", ha="center", va="center",
                zorder=7)

    ax.set_xlim(-0.5, len(DAYS) - 0.5)
    ax.set_ylim(len(DEMAND_SHIFTS) - 0.5 + 0.42, -0.5)  # slim note band only


fig3, ax3 = plt.subplots(figsize=GRID_FIGSIZE)
fig3.subplots_adjust(**GRID_LAYOUT)
draw_demand(ax3, show_greedy=False)
aeviz.save(fig3, f"{HERE}/03_demand")

fig4, ax4 = plt.subplots(figsize=GRID_FIGSIZE)
fig4.subplots_adjust(**GRID_LAYOUT)
draw_demand(ax4, show_greedy=True)
aeviz.save(fig4, f"{HERE}/04_greedy")

print()
print("Wrote 01_shift_dag, 02_solution, 03_demand, 04_greedy .{png,svg}")
