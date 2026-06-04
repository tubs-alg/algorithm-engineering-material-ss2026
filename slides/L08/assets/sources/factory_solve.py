# %% [markdown]
# Factory shift scheduling as a MIN-COST FLOW (a scheduling problem in disguise).
#
# What this file contains
#   A small factory with timed tasks (fixed begin/end, a station each) that must
#   all be handled by workers. A worker's shift starts at 08:00; a worker is paid
#   for at least 6 hours and can work longer at an overtime rate. Moving between
#   stations costs a CHANGEOVER, so two tasks that merely don't overlap are not
#   necessarily chainable -- this switching constraint is what makes the problem
#   non-trivial. We want to cover every task at minimum total wage.
#
#   The switching constraint is the crux. Ignore stations and a greedy "assign each
#   task to the earliest-free worker" packs these six tasks onto just 2 workers --
#   the obvious plan T1->T3->T5 / T2->T4->T6. But two of that plan's hand-offs cross
#   stations with only 15 min for a 30-min changeover, so it is INFEASIBLE. Once the
#   changeover is enforced, NO 2-worker roster exists; the cheapest legal roster
#   needs 3 workers. The lesson is not headcount arithmetic: it is that the switch
#   defeats the obvious greedy, and only the global (flow) view finds a legal plan.
#
#   Looks like an ILP. It is actually a MIN-COST FLOW, so the LP relaxation is
#   already integral (network matrix is totally unimodular) and it solves in
#   polynomial time -- the second teaching point.
#
#   The flow network (one worker = one unit of flow along a chain of tasks):
#     SHIFT_START --> task --> ... --> task --> SHIFT_END
#   - SHIFT_START -> task: this task may be a worker's FIRST task.            (cap 1, cost 0)
#   - task_i -> task_j: the changeover from i to j fits (j.begin >= i.end + c). (cap 1, cost 0)
#   - task -> SHIFT_END: this task is a worker's LAST task; the EDGE CARRIES
#     THE WORKER'S WHOLE WAGE = max(6h pay, pay until this task ends).         (cap 1, cost = wage)
#   - SHIFT_END -> SHIFT_START recirculates idle workers (cap n, cost 0), so the
#     number of workers is a free variable the optimizer minimizes against wages.
#
#   Forcing coverage (the one honest subtlety): a single node per task does NOT
#   force the task to be done (the empty flow would be free). So each task is
#   SPLIT into task_in -> task_out with a MANDATORY unit through it. networkx has
#   no edge lower bounds, but a mandatory unit is exactly a node-demand pair:
#   task_in must RECEIVE 1 (demand +1) and task_out must SEND 1 (demand -1).
#   That pair is what pins every task into exactly one worker's chain.
#   Non-goal: skills/eligibility, breaks, multiple shift starts. Kept minimal.
#
# Why it exists
#   Teaching snippet for L08, pillar 3 (Flows): a real-sounding scheduling problem
#   that a student would reach for ILP on, revealed to be a min-cost flow ->
#   integral, polynomial, and a clean model. Reinforces "see the graph".
#
# How to run
#   conda activate mo312 && python solve.py
#   Writes 01_tasks_timeline, 02_flow_network, 03_worker_schedule,
#   04_greedy_vs_flow (.png + .svg) and prints the schedule + total wage to stdout.
#
# When it changes
#   If the instance is retuned or the wage scheme changes. Keep it deterministic
#   and small enough that the flow network stays legible at slide size.

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
from matplotlib.patches import FancyBboxPatch

import aeviz

aeviz.init_style()

# Bright red for "illegal / blocked" markers so they read on the dark navy slide
# background (the original dark crimson #d1495b muddied into the background).
BLOCKED = "#ff6b6b"

# %% [markdown]
# ## Instance: timed tasks, stations, wage scheme.

# %%
SHIFT_START = 8.0     # 08:00, every worker's shift begins here
RATE = 20             # EUR / hour, regular
MIN_HOURS = 6         # a worker is paid for at least 6 hours
OT_RATE = 30          # EUR / hour for time beyond 6 hours (the fixed extra rate)
CHANGEOVER = 0.5      # 30 min to move between DIFFERENT stations (0 if same)

# (id, station, begin, end) in decimal hours. No two tasks at the SAME station
# overlap (a station is one machine). Tuned so the SWITCHING constraint is the crux:
# the obvious station-blind plan T1->T3->T5 / T2->T4->T6 uses 2 workers, but its
# A->B (T1->T3) and D->C (T2->T4) hand-offs have only 15 min for a 30-min changeover,
# so no 2-worker roster is legal; the cheapest legal roster needs 3 workers.
TASKS = [
    ("T1", "A", 8.0, 10.0),
    ("T2", "D", 8.5, 10.25),
    ("T3", "B", 10.25, 12.0),
    ("T4", "C", 10.5, 12.25),
    ("T5", "B", 12.25, 14.0),
    ("T6", "A", 14.0, 16.0),
]
STATION = {t[0]: t[1] for t in TASKS}
BEGIN = {t[0]: t[2] for t in TASKS}
END = {t[0]: t[3] for t in TASKS}
IDS = [t[0] for t in TASKS]


def hm(t: float) -> str:
    """Decimal hours -> 'H:MM'."""
    h = int(t)
    m = int(round((t - h) * 60))
    return f"{h}:{m:02d}"


def changeover(a: str, b: str) -> float:
    return 0.0 if STATION[a] == STATION[b] else CHANGEOVER


def can_follow(i: str, j: str) -> bool:
    """Task j can be done right after task i by the same worker."""
    return BEGIN[j] >= END[i] + changeover(i, j)


def wage(last_task: str) -> int:
    """Whole-shift wage if `last_task` is a worker's final task.

    Paid from 08:00 to the task's end, at least MIN_HOURS, overtime beyond that.
    """
    worked = END[last_task] - SHIFT_START
    base = RATE * MIN_HOURS
    if worked <= MIN_HOURS:
        return int(base)
    return int(base + OT_RATE * (worked - MIN_HOURS))


TRANSITIONS = [(i, j) for i in IDS for j in IDS if i != j and can_follow(i, j)]

# %% [markdown]
# ## The naive baseline the switch defeats: a station-blind greedy.
# Assign each task (in start order) to the earliest-free worker, treating "free" as
# "previous task has ended" while IGNORING the changeover -- the classic interval-
# packing greedy. It hires few workers, but some of its hand-offs cross stations
# with too little time, so they are illegal once the changeover is enforced.

# %%
def station_blind_greedy() -> list[list[str]]:
    rosters: list[list[str]] = []
    for t in sorted(IDS, key=lambda t: BEGIN[t]):
        free = [r for r in rosters if END[r[-1]] <= BEGIN[t]]   # ignores changeover
        if free:
            min(free, key=lambda r: END[r[-1]]).append(t)
        else:
            rosters.append([t])
    return rosters


GREEDY = station_blind_greedy()
GREEDY_ILLEGAL = [(a, b) for r in GREEDY for a, b in zip(r[:-1], r[1:])
                  if not can_follow(a, b)]

# %% [markdown]
# ## Build the min-cost flow network (split nodes + node demands force coverage).

# %%
SIGMA, TAU = "SHIFT_START", "SHIFT_END"
G = nx.DiGraph()
G.add_node(SIGMA, demand=0)
G.add_node(TAU, demand=0)

for t in IDS:
    G.add_node(("in", t), demand=1)    # task_in must RECEIVE 1  -> task is entered
    G.add_node(("out", t), demand=-1)  # task_out must SEND 1    -> task is left
    G.add_edge(SIGMA, ("in", t), capacity=1, weight=0)        # may be first task
    G.add_edge(("out", t), TAU, capacity=1, weight=wage(t))   # may be last task (wage here)

for i, j in TRANSITIONS:
    G.add_edge(("out", i), ("in", j), capacity=1, weight=0)   # chain i -> j

G.add_edge(TAU, SIGMA, capacity=len(IDS), weight=0)           # recirculate workers

flow = nx.min_cost_flow(G)
total_wage = nx.cost_of_flow(G, flow)
n_workers = flow[TAU][SIGMA]

# %% [markdown]
# ## Reconstruct each worker's chain from the flow.

# %%
first_tasks = [t for t in IDS if flow[SIGMA][("in", t)] == 1]


def chain_from(start: str) -> list[str]:
    chain, cur = [start], start
    while flow[("out", cur)][TAU] != 1:  # not yet the last task
        nxt = next(j for j in IDS if flow[("out", cur)].get(("in", j), 0) == 1)
        chain.append(nxt)
        cur = nxt
    return chain


workers = [chain_from(s) for s in first_tasks]
workers.sort(key=lambda c: BEGIN[c[0]])

co_min = int(CHANGEOVER * 60)
print("=== Factory shift scheduling as min-cost flow ===")
print(f"Tasks: {len(IDS)}   stations: {'/'.join(sorted(set(STATION.values())))}   "
      f"changeover between stations: {co_min} min")
print(f"Feasible task->task transitions (switch respected): {len(TRANSITIONS)}")
print()
print(f"NAIVE station-blind greedy (ignores switching): {len(GREEDY)} workers")
for k, r in enumerate(GREEDY, 1):
    print(f"  W{k}: " + " -> ".join(f"{t}@{STATION[t]}" for t in r))
print(f"  ...but {len(GREEDY_ILLEGAL)} hand-off(s) are ILLEGAL once the {co_min}-min "
      "changeover is enforced:")
for a, b in GREEDY_ILLEGAL:
    print(f"     {a}->{b}  ({STATION[a]}->{STATION[b]}, only "
          f"{(BEGIN[b] - END[a]) * 60:.0f} min for a {co_min}-min changeover)")
print(f"  => that 'obvious' {len(GREEDY)}-worker plan does NOT exist.")
print()
print(f"MIN-COST FLOW (switch respected): {n_workers} workers, total wage EUR {total_wage}")
for k, c in enumerate(workers, 1):
    seq = "  ->  ".join(f"{t} ({hm(BEGIN[t])}-{hm(END[t])} @{STATION[t]})" for t in c)
    last = c[-1]
    worked = END[last] - SHIFT_START
    ot = max(0.0, worked - MIN_HOURS)
    tag = f"{worked:.1f}h paid" + (f", {ot:.1f}h overtime" if ot else " (6h minimum)")
    print(f"  Worker {k}: {seq}")
    print(f"            ends {hm(END[last])} -> EUR {wage(last)}  [{tag}]")
print()
print("Why a FLOW: one worker = one unit from SHIFT_START to SHIFT_END through a")
print("chain of tasks. Integer capacities + the network (totally unimodular)")
print("structure => the LP optimum is already integral. No branch-and-bound.")

# Sanity: every task covered exactly once.
covered = sorted(t for c in workers for t in c)
assert covered == IDS, ("coverage broken", covered)

# Guard the teaching point: the switch must defeat the greedy and force more workers.
assert GREEDY_ILLEGAL, "instance no longer exhibits an illegal station-blind hand-off"
assert len(GREEDY) < n_workers, "switch no longer forces extra workers; retune instance"

# %% [markdown]
# ## Shared styling.

# %%
STATIONS = sorted({s for s in STATION.values()})          # ['A','B','C']
SY = {s: i for i, s in enumerate(reversed(STATIONS))}     # A on top
WORKER_C = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]   # per-worker (Okabe-Ito)
worker_of = {t: k for k, c in enumerate(workers) for t in c}

X0, X1 = SHIFT_START - 0.8, max(END.values()) + 0.8


def task_color(t):
    return WORKER_C[worker_of[t] % len(WORKER_C)]


# %% [markdown]
# ## Figure 1: the task instance on a station timeline (sets up the problem).
# All tasks as bars on station rows, plus one feasible and one INFEASIBLE
# transition annotated, so "no overlap but changeover too short" is concrete.

# %%
fig, ax = plt.subplots(figsize=(10, 4.4))
for t in IDS:
    y = SY[STATION[t]]
    ax.add_patch(FancyBboxPatch(
        (BEGIN[t], y - 0.28), END[t] - BEGIN[t], 0.56,
        boxstyle="round,pad=0.0,rounding_size=0.06",
        fc=aeviz.PALETTE["settled"], ec=aeviz.PALETTE["node_edge"], lw=1.4, zorder=3))
    ax.text((BEGIN[t] + END[t]) / 2, y, f"{t}\n{hm(BEGIN[t])}-{hm(END[t])}",
            ha="center", va="center", fontsize=9, zorder=4, color=aeviz.PALETTE["ink"])

# feasible transition T3 -> T5 (same station B, no changeover needed): a shallow
# arch over the 15-min gap, anchored slightly inside each box top so the shaft is
# long enough that the arrowhead stays proportionate (a tiny edge-to-edge hop
# turns the head into a blob). Drawn above the B row so the label sits in empty
# space rather than over the C row below.
ax.annotate("", xy=(BEGIN["T5"] + 0.25, SY["B"] + 0.30),
            xytext=(END["T3"] - 0.25, SY["B"] + 0.30),
            arrowprops=dict(arrowstyle="-|>", color=aeviz.PALETTE["good"], lw=2.0,
                            mutation_scale=14, shrinkA=0, shrinkB=0,
                            connectionstyle="arc3,rad=-0.4"))
ax.text((END["T3"] + BEGIN["T5"]) / 2, SY["B"] + 0.74,
        "T3->T5 ok\n(same station)", ha="center", va="center", fontsize=8.5,
        color=aeviz.PALETTE["good"])

# INFEASIBLE T1 -> T3 (A->B needs 30 min, only 15 min gap) -- the link the
# obvious 2-worker plan relies on, and the reason that plan does not exist.
# A diagonal arc from the bottom-right of T1 down to the top-left of T3.
ax.annotate("", xy=(BEGIN["T3"] + 0.08, SY["B"] + 0.30),
            xytext=(END["T1"] - 0.08, SY["A"] - 0.30),
            arrowprops=dict(arrowstyle="-|>", color=BLOCKED, lw=2.0,
                            mutation_scale=14, shrinkA=0, shrinkB=0,
                            ls=(0, (4, 3)), connectionstyle="arc3,rad=0.25"))
ax.text(END["T1"] - 0.15, (SY["A"] + SY["B"]) / 2 - 0.1,
        "T1->T3 blocked\n(A->B: 30-min changeover,\nonly 15 min)",
        ha="right", va="center", fontsize=8.5, color=BLOCKED)

ax.axvline(SHIFT_START, color=aeviz.PALETTE["faded"], ls=":", lw=1.2, zorder=1)
ax.text(SHIFT_START, len(STATIONS) - 0.62, " shift start 8:00", fontsize=8.5,
        color=aeviz.PALETTE["faded_dark"], ha="left", va="top")
ax.set_yticks(list(SY.values()))
ax.set_yticklabels([f"station {s}" for s in SY])
ax.set_ylim(-1.2, len(STATIONS) - 0.4)
ax.set_xlim(X0, X1)
ax.set_xticks(range(int(X0) + 1, int(X1) + 1))
ax.set_xticklabels([hm(h) for h in range(int(X0) + 1, int(X1) + 1)])
ax.set_xlabel("time of day")
ax.set_title("Factory tasks: fixed times, stations, and changeover constraints",
             fontsize=12, color=aeviz.PALETTE["ink"], pad=14)
for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)
aeviz.save(fig, "01_tasks_timeline")
plt.close(fig)

# %% [markdown]
# ## Figure 2: the min-cost flow network with the chosen worker chains.

# %%
fig, ax = plt.subplots(figsize=(11, 5.2))
pos = {SIGMA: (X0 - 0.4, (len(STATIONS) - 1) / 2),
       TAU: (X1 + 0.6, (len(STATIONS) - 1) / 2)}
for t in IDS:
    pos[t] = (BEGIN[t], SY[STATION[t]])

chosen = set()
for c in workers:
    for a, b in zip(c[:-1], c[1:]):
        chosen.add((a, b))

# faded background: all feasible transitions + start/end stubs
aeviz.draw_curved_edges(ax, pos, [(i, j) for i, j in TRANSITIONS if (i, j) not in chosen],
                        rad=0.18, color=aeviz.PALETTE["faded"], width=1.1,
                        node_size=900, zorder=1)
for t in IDS:
    aeviz.draw_curved_edges(ax, pos, [(SIGMA, t)], rad=0.06,
                            color=aeviz.PALETTE["faded"], width=0.9,
                            node_size=900, zorder=1)
    # every task may also END the shift -> a faded stub to SHIFT_END for all of them
    aeviz.draw_curved_edges(ax, pos, [(t, TAU)], rad=0.06,
                            color=aeviz.PALETTE["faded"], width=0.9,
                            node_size=900, zorder=1)

# chosen chains, one color per worker; wage on the SHIFT_END arc
for k, c in enumerate(workers):
    col = WORKER_C[k % len(WORKER_C)]
    aeviz.draw_curved_edges(ax, pos, [(SIGMA, c[0])], rad=0.06, color=col,
                            width=2.4, node_size=900, zorder=3)
    aeviz.draw_curved_edges(ax, pos, list(zip(c[:-1], c[1:])), rad=0.18, color=col,
                            width=2.8, node_size=900, zorder=3)
    aeviz.draw_curved_edges(ax, pos, [(c[-1], TAU)], rad=0.06, color=col, width=2.8,
                            node_size=900, zorder=3,
                            labels={(c[-1], TAU): f"EUR {wage(c[-1])}"},
                            label_color=col, label_fontsize=10)

# nodes
for t in IDS:
    x, y = pos[t]
    ax.scatter([x], [y], s=900, c=task_color(t), edgecolors=aeviz.PALETTE["node_edge"],
               linewidths=1.5, zorder=4)
    ax.text(x, y, t, ha="center", va="center", fontsize=9.5, fontweight="bold",
            color="white", zorder=5)
for term, lab in ((SIGMA, "shift\nstart"), (TAU, "shift\nend")):
    x, y = pos[term]
    ax.scatter([x], [y], s=1500, c="#5a6b7a", edgecolors=aeviz.PALETTE["node_edge"],
               linewidths=1.5, zorder=4)
    ax.text(x, y, lab, ha="center", va="center", fontsize=9, fontweight="bold",
            color="white", zorder=5)

ax.set_xlim(X0 - 1.1, X1 + 1.4)
ax.set_ylim(-1.0, len(STATIONS) - 0.3)
ax.axis("off")
ax.set_title(
    f"Min-cost flow = optimal roster: {n_workers} workers, total wage EUR {total_wage}\n"
    "one worker = one unit of flow along a chain; wage sits on the shift-end arc",
    fontsize=12, color=aeviz.PALETTE["ink"])
aeviz.save(fig, "02_flow_network")
plt.close(fig)

# %% [markdown]
# ## Figure 3: the resulting schedule, one lane per worker (the payoff).
# Shows each worker's task sequence, idle gaps, and the paid span from 08:00 to
# the last task's end with overtime shaded.

# %%
fig, ax = plt.subplots(figsize=(10, 0.9 * n_workers + 1.8))
for k, c in enumerate(workers):
    y = n_workers - 1 - k
    col = WORKER_C[k % len(WORKER_C)]
    last_end = END[c[-1]]
    # paid span 08:00 -> last end (light), overtime portion (beyond 6h) darker
    ot_start = SHIFT_START + MIN_HOURS
    ax.add_patch(plt.Rectangle((SHIFT_START, y - 0.34), last_end - SHIFT_START, 0.68,
                               fc=(1.0, 1.0, 1.0, 0.10), ec="none", zorder=1))
    if last_end > ot_start:
        ax.add_patch(plt.Rectangle((ot_start, y - 0.34), last_end - ot_start, 0.68,
                                   fc=(0.90, 0.57, 0.22, 0.30), ec="none", zorder=1))
    # task bars
    for t in c:
        ax.add_patch(FancyBboxPatch(
            (BEGIN[t], y - 0.26), END[t] - BEGIN[t], 0.52,
            boxstyle="round,pad=0.0,rounding_size=0.05", fc=col, ec="none", zorder=3))
        ax.text((BEGIN[t] + END[t]) / 2, y, f"{t} @{STATION[t]}", ha="center",
                va="center", fontsize=8.5, color="white", fontweight="bold", zorder=4)
    worked = last_end - SHIFT_START
    ot = max(0.0, worked - MIN_HOURS)
    note = f"EUR {wage(c[-1])}  ({worked:.1f}h" + (f", +{ot:.1f}h OT)" if ot else ", 6h min)")
    ax.text(last_end + 0.15, y, note, ha="left", va="center", fontsize=9, color=col)

ax.axvline(SHIFT_START, color=aeviz.PALETTE["faded"], ls=":", lw=1.2)
ax.axvline(SHIFT_START + MIN_HOURS, color=aeviz.PALETTE["warn"], ls=":", lw=1.2)
ax.text(SHIFT_START + MIN_HOURS, n_workers - 0.3, " 6h mark (overtime starts)",
        fontsize=8.5, color=aeviz.PALETTE["warn"], ha="left", va="bottom")
ax.set_yticks([n_workers - 1 - k for k in range(n_workers)])
ax.set_yticklabels([f"worker {k + 1}" for k in range(n_workers)])
ax.set_ylim(-0.8, n_workers - 0.1)
ax.set_xlim(X0, X1 + 2.4)
ax.set_xticks(range(int(X0) + 1, int(X1) + 1))
ax.set_xticklabels([hm(h) for h in range(int(X0) + 1, int(X1) + 1)])
ax.set_xlabel("time of day")
ax.set_title(f"Resulting schedule: {n_workers} workers, total wage EUR {total_wage}",
             fontsize=12, color=aeviz.PALETTE["ink"])
for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)
aeviz.save(fig, "03_worker_schedule")
plt.close(fig)

# %% [markdown]
# ## Figure 4: the punchline -- station-blind greedy (infeasible) vs min-cost flow.
# Top: the greedy's 2-worker plan, with its illegal cross-station hand-offs in red.
# Bottom: the flow's 3-worker plan, every hand-off legal. The switch is the reason
# the cheap-looking plan does not exist.

# %%
def draw_roster(ax, rosters, by_worker, illegal=()):
    illegal = set(illegal)
    n = len(rosters)
    for k, r in enumerate(rosters):
        y = n - 1 - k
        col = WORKER_C[k % len(WORKER_C)] if by_worker else "#90a4ae"
        for a, b in zip(r[:-1], r[1:]):       # hand-off arcs between consecutive tasks
            bad = (a, b) in illegal
            ax.annotate("", xy=(BEGIN[b], y), xytext=(END[a], y),
                        arrowprops=dict(arrowstyle="-|>",
                                        color=BLOCKED if bad else aeviz.PALETTE["faded_dark"],
                                        lw=2.2 if bad else 1.3,
                                        ls=(0, (3, 2)) if bad else "-",
                                        connectionstyle="arc3,rad=-0.12"))
            if bad:
                ax.text((END[a] + BEGIN[b]) / 2, y + 0.42,
                        f"{STATION[a]}->{STATION[b]}\nchangeover\ndoesn't fit",
                        ha="center", va="bottom", fontsize=7, color=BLOCKED)
        for t in r:
            ax.add_patch(FancyBboxPatch(
                (BEGIN[t], y - 0.26), END[t] - BEGIN[t], 0.52,
                boxstyle="round,pad=0.0,rounding_size=0.05", fc=col, ec="none", zorder=3))
            ax.text((BEGIN[t] + END[t]) / 2, y, f"{t}@{STATION[t]}", ha="center",
                    va="center", fontsize=8, color="white", fontweight="bold", zorder=4)
    ax.set_yticks([n - 1 - k for k in range(n)])
    ax.set_yticklabels([f"worker {k + 1}" for k in range(n)])
    ax.set_ylim(-0.9, n - 0.1)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)


fig, (axg, axf) = plt.subplots(
    2, 1, figsize=(10, 5.8), sharex=True,
    gridspec_kw=dict(height_ratios=[len(GREEDY), n_workers], hspace=0.45))
draw_roster(axg, GREEDY, by_worker=False, illegal=GREEDY_ILLEGAL)
axg.set_title(
    f"Station-blind greedy: {len(GREEDY)} workers, but {len(GREEDY_ILLEGAL)} hand-offs "
    "need a 30-min changeover that does not fit -> INFEASIBLE",
    fontsize=11, color=BLOCKED)
draw_roster(axf, workers, by_worker=True)
axf.set_title(
    f"Min-cost flow: {n_workers} workers, total wage EUR {total_wage} -> every hand-off legal",
    fontsize=11, color=aeviz.PALETTE["ink"])
axf.set_xlim(X0, X1)
axf.set_xticks(range(int(X0) + 1, int(X1) + 1))
axf.set_xticklabels([hm(h) for h in range(int(X0) + 1, int(X1) + 1)])
axf.set_xlabel("time of day")
aeviz.save(fig, "04_greedy_vs_flow")
plt.close(fig)

print("\nFigures written: 01_tasks_timeline, 02_flow_network, 03_worker_schedule, "
      "04_greedy_vs_flow (.png + .svg)")
