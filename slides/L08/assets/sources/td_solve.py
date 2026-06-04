# %% [markdown]
# Time-dependent shortest paths and the FIFO property.
#
# What this file contains
#   A small road network where every arc's travel time depends on WHEN you depart
#   (rush hour). We compute the EARLIEST-ARRIVAL path from a source to a target for
#   a fixed departure time, using a hand-written time-dependent Dijkstra (label-
#   setting on arrival times: relaxing arc u->v sets arrival_v = arrival_u +
#   tt_uv(arrival_u)). networkx has no built-in time-dependent shortest path, so the
#   tiny label-setting loop is implemented here; networkx is used only as the graph
#   container and for drawing.
#
#   The teaching point is the FIFO ("no overtaking") property. An arc is FIFO if its
#   ARRIVAL function arr(t) = t + tt(t) is non-decreasing in the departure time t:
#   leaving later never lets you arrive earlier. When every arc is FIFO, the earliest-
#   arrival problem still obeys the optimality principle, so plain Dijkstra still works
#   with the ONLY change being to evaluate tt at the current arrival time. We show the
#   clean FIFO half (the main instance) and then a deliberately non-FIFO arc where
#   arr(t) briefly DIPS, so WAITING before entering beats departing immediately and the
#   "never wait" assumption (and the simple result) breaks.
#
#   Non-goal: continuous-time function algebra, parametric shortest paths, or proving
#   the optimality principle. Just: build it, run TD-Dijkstra, show FIFO vs non-FIFO.
#
# Why it exists
#   Teaching snippet for L08, pillar 1 (Shortest Paths): travel times are time
#   dependent in real navigation, yet under the mild and common FIFO assumption the
#   shortest-path machinery is unchanged. A cool, simple, practical result -- with a
#   crisp counterexample showing exactly which assumption it rests on.
#
# How to run
#   conda activate mo312 && python solve.py
#   Writes 01_network, 02_travel_time_profiles, 03_earliest_arrival_path (.png + .svg)
#   and prints the earliest-arrival result, the free-flow comparison, and the non-FIFO
#   waiting counterexample to stdout.
#
# When it changes
#   If the network or the congestion windows are retuned. Keep it deterministic and
#   small; the peak-dodging path must stay non-obvious and the FIFO assertions must hold.

# %%
import matplotlib

matplotlib.use("Agg")  # headless: write files, never open a window

import sys

sys.path.insert(
    0,
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/week07-l08-graph-algorithms/snippets",
)

import heapq

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

import aeviz

aeviz.init_style()

# %% [markdown]
# ## Instance: a road network with time-dependent arc travel times.
# Times are in MINUTES past midnight (so 08:00 = 480). Travel times are in minutes.
# Each arc has a free-flow travel time and (optionally) a congested window where the
# travel time rises to a peak and falls back -- a simple piecewise-linear "tent" added
# on top of free flow. The peak is centered on the morning rush, ~08:30 (510).

# %%
H = 60  # minutes per hour


def hm(t: float) -> str:
    """Minutes past midnight -> 'H:MM'."""
    h = int(t) // H
    m = int(round(t)) % H
    return f"{h}:{m:02d}"


def tent(t: float, center: float, half_width: float, peak: float) -> float:
    """Piecewise-linear bump: 0 outside [center-hw, center+hw], `peak` at the center."""
    d = abs(t - center)
    if d >= half_width:
        return 0.0
    return peak * (1.0 - d / half_width)


# Place-like nodes with hand-placed 2D positions (x = roughly east, y = north).
# S = Start (suburb), T = Target (downtown across the river). MID is the congested
# city-center crossing; RING/PARK form a longer free-flow bypass that dodges the peak.
POS = {
    "Start":     (0.0, 1.0),
    "Center":    (2.0, 1.6),   # the congested downtown crossing
    "Riverside": (2.2, 0.0),   # bypass leg 1
    "Parkway":   (4.0, 0.4),   # bypass leg 2
    "Target":    (5.0, 1.3),
}

# Arc definitions: (u, v, free_flow_minutes, congestion).
# congestion = None for a constant arc, else (center, half_width, peak_extra_minutes).
# The Start->Center->Target route is short in free flow (8 + 9 = 17 min) but Center is
# the rush-hour crossing: at the peak its travel time roughly triples. The bypass
# Start->Riverside->Parkway->Target is longer in free flow (12 + 11 + 9 = 32 min) but
# barely congested, so departing into the peak it wins. Designed so the earliest-
# arrival path is NOT the free-flow-shortest path.
ARCS = [
    ("Start", "Center", 8.0, (510.0, 75.0, 34.0)),     # rush-hour crossing approach
    ("Center", "Target", 9.0, (510.0, 75.0, 30.0)),    # the downtown bottleneck
    ("Start", "Riverside", 12.0, None),                # quiet bypass leg
    ("Riverside", "Parkway", 11.0, (510.0, 60.0, 6.0)),# mildly busy
    ("Parkway", "Target", 9.0, None),                  # quiet bypass leg
]


def make_tt(free_flow: float, cong):
    """Return a travel-time function tt(t) for one arc (t = departure, minutes)."""
    if cong is None:
        return lambda t: free_flow
    center, half_width, peak = cong
    return lambda t: free_flow + tent(t, center, half_width, peak)


TT = {(u, v): make_tt(ff, cong) for (u, v, ff, cong) in ARCS}
FREE_FLOW = {(u, v): ff for (u, v, ff, cong) in ARCS}

G = nx.DiGraph()
for (u, v, ff, cong) in ARCS:
    G.add_edge(u, v, free_flow=ff)

# %% [markdown]
# ## FIFO check: an arc is FIFO iff arr(t) = t + tt(t) is non-decreasing.
# We sample the function densely over the day and assert monotonicity. A "tent" bump
# of slope < 1 keeps arr non-decreasing (it rises slower than +1 min of delay per +1
# min of departure), so all main arcs are FIFO by construction.

# %%
DAY = np.arange(360.0, 720.0, 0.5)  # sample 06:00..12:00 at 30-second resolution


def arrival_fn(tt):
    return lambda t: t + tt(t)


def is_fifo(tt, ts=DAY, tol=1e-9) -> bool:
    """True iff arr(t) = t + tt(t) is non-decreasing across the sampled departures."""
    arr = np.array([t + tt(t) for t in ts])
    return bool(np.all(np.diff(arr) >= -tol))


for (u, v) in TT:
    assert is_fifo(TT[(u, v)]), f"arc {u}->{v} is not FIFO; retune its congestion bump"

# %% [markdown]
# ## Time-dependent Dijkstra (label-setting on arrival times).
# Only ONE thing differs from textbook Dijkstra: when we relax arc u->v we evaluate the
# travel time AT the current arrival time at u. Because every arc is FIFO, the first time
# we settle a node we have its earliest possible arrival (the optimality principle still
# holds), so the standard label-setting argument carries over unchanged.

# %%
def td_dijkstra(source: str, depart: float):
    """Earliest arrival time and predecessor map from `source` departing at `depart`."""
    arrival = {n: float("inf") for n in G.nodes}
    arrival[source] = depart
    pred: dict[str, str] = {}
    settled: set[str] = set()
    pq = [(depart, source)]
    order: list[str] = []  # settle order, for the slide narrative
    while pq:
        a_u, u = heapq.heappop(pq)
        if u in settled:
            continue
        settled.add(u)
        order.append(u)
        for v in G.successors(u):
            a_v = a_u + TT[(u, v)](a_u)  # <-- the only change: tt at current arrival
            if a_v < arrival[v]:
                arrival[v] = a_v
                pred[v] = u
                heapq.heappush(pq, (a_v, v))
    return arrival, pred, order


def reconstruct(pred: dict[str, str], source: str, target: str) -> list[str]:
    path, cur = [target], target
    while cur != source:
        cur = pred[cur]
        path.append(cur)
    return path[::-1]


SOURCE, TARGET = "Start", "Target"
T0 = 8 * H  # depart 08:00, straight into the building rush

arrival, pred, order = td_dijkstra(SOURCE, T0)
ea_path = reconstruct(pred, SOURCE, TARGET)
ea_time = arrival[TARGET]

# %% [markdown]
# ## Free-flow baseline: shortest path ignoring time dependence, then its REAL cost.
# A planner using static (free-flow) travel times picks the short downtown route, then
# pays for it because it departs straight into the peak.

# %%
ff_path = nx.shortest_path(G, SOURCE, TARGET, weight="free_flow")


def arrival_along(path: list[str], depart: float) -> float:
    """Actual time-dependent arrival when following `path` from `depart`, no waiting."""
    t = depart
    for u, v in zip(path[:-1], path[1:]):
        t += TT[(u, v)](t)
    return t


def free_flow_len(path: list[str]) -> float:
    return sum(FREE_FLOW[(u, v)] for u, v in zip(path[:-1], path[1:]))


ff_real_arrival = arrival_along(ff_path, T0)

# %% [markdown]
# ## Non-FIFO counterexample (a clearly-labeled SECONDARY scenario).
# Build a single arc whose travel time spikes so hard that its arrival function arr(t)
# briefly DECREASES: a slope steeper than -1 on the way up means departing a little
# LATER (just before the spike clears) arrives EARLIER than leaving now. On a path that
# enters this arc, WAITING beats leaving immediately, so the "never wait" assumption that
# makes plain TD-Dijkstra correct fails. This is why FIFO is the load-bearing hypothesis.

# %%
# A near-instantaneous closure: travel time jumps to 60 min during [510, 520] then drops.
# (Think: a drawbridge up for 10 minutes.) free flow 5 min otherwise.
def tt_nonfifo(t: float) -> float:
    return 60.0 if 510.0 <= t < 520.0 else 5.0


assert not is_fifo(tt_nonfifo), "counterexample arc should be non-FIFO but tested FIFO"

arr_nonfifo = arrival_fn(tt_nonfifo)
DEPART_NOW = 512.0           # 08:32: arrive at the bridge while it is up
arr_leave_now = arr_nonfifo(DEPART_NOW)          # 512 -> hits closure -> 512 + 60 = 572
DEPART_WAIT = 520.0          # wait 8 min, enter at 08:40 after it reopens
arr_after_wait = arr_nonfifo(DEPART_WAIT)        # 520 + 5 = 525
waiting_gain = arr_leave_now - arr_after_wait

assert arr_after_wait < arr_leave_now, "waiting should beat leaving on the non-FIFO arc"

# %% [markdown]
# ## stdout summary.

# %%
print("=== Time-dependent shortest path (earliest arrival) ===")
print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} arcs; "
      "every arc travel time depends on departure time (morning rush ~08:30).")
print(f"All {len(TT)} arcs verified FIFO (arr(t)=t+tt(t) non-decreasing).")
print()
print(f"Depart {SOURCE} at {hm(T0)}.")
print(f"  Time-dependent Dijkstra settle order: {' -> '.join(order)}")
print(f"  EARLIEST-ARRIVAL path : {' -> '.join(ea_path)}")
print(f"     free-flow length {free_flow_len(ea_path):.0f} min, "
      f"arrives {hm(ea_time)} ({ea_time - T0:.1f} min on the road)")
print()
print(f"  FREE-FLOW-shortest path: {' -> '.join(ff_path)}")
print(f"     free-flow length {free_flow_len(ff_path):.0f} min (looks shorter), but "
      f"departing into the peak it actually arrives {hm(ff_real_arrival)} "
      f"({ff_real_arrival - T0:.1f} min on the road)")
loss = ff_real_arrival - ea_time
print(f"  => the longer-looking bypass dodges the rush and wins by {loss:.1f} min.")
print()
print("--- Secondary scenario: a NON-FIFO arc (a 10-min bridge closure) ---")
print("    travel time = 5 min normally, 60 min while closed during 08:30..08:40.")
print(f"    Leave NOW at {hm(DEPART_NOW)}: hit the closure, arrive {hm(arr_leave_now)}.")
print(f"    WAIT until {hm(DEPART_WAIT)} (bridge reopens), arrive {hm(arr_after_wait)}.")
print(f"    => waiting arrives {waiting_gain:.0f} min EARLIER: departing later beats "
      "departing now,")
print("       so arr(t) is NOT monotone and the 'never wait' assumption fails. FIFO is")
print("       exactly the hypothesis that rules this out and keeps plain Dijkstra correct.")

# %% [markdown]
# ## Shared drawing helpers.

# %%
NODE_SIZE = 1500
EA_EDGES = set(zip(ea_path[:-1], ea_path[1:]))
FF_EDGES = set(zip(ff_path[:-1], ff_path[1:]))


def draw_nodes(ax, highlight=()):
    for n, (x, y) in POS.items():
        if n == SOURCE:
            c = aeviz.PALETTE["good"]
        elif n == TARGET:
            c = aeviz.PALETTE["warn"]
        elif n in highlight:
            c = aeviz.PALETTE["path"]
        else:
            c = aeviz.PALETTE["node_face"]
        ax.scatter([x], [y], s=NODE_SIZE, c=c, edgecolors=aeviz.PALETTE["node_edge"],
                   linewidths=1.5, zorder=4)
        ax.text(x, y - 0.17, n, ha="center", va="top", fontsize=10.5,
                fontweight="bold", color=aeviz.PALETTE["ink"], zorder=5)


# %% [markdown]
# ## Figure 1: the network (free-flow times, congested arcs marked).

# %%
fig, ax = plt.subplots(figsize=(9.5, 5.0))
cong_arcs = {(u, v) for (u, v, ff, cong) in ARCS if cong is not None}

# congested arcs in amber, quiet arcs in gray; free-flow time on each.
aeviz.draw_curved_edges(
    ax, POS, [e for e in TT if e not in cong_arcs], rad=0.0,
    color=aeviz.PALETTE["faded_dark"], width=2.0, node_size=NODE_SIZE,
    labels={e: f"{int(FREE_FLOW[e])} min" for e in TT if e not in cong_arcs},
    label_fontsize=10, zorder=2)
aeviz.draw_curved_edges(
    ax, POS, list(cong_arcs), rad=0.0,
    color=aeviz.PALETTE["warn"], width=3.0, node_size=NODE_SIZE,
    labels={e: f"{int(FREE_FLOW[e])} min*" for e in cong_arcs},
    label_color=aeviz.PALETTE["warn"], label_fontsize=10, zorder=2)

draw_nodes(ax)
ax.scatter([], [], s=120, c=aeviz.PALETTE["warn"], label="congested arc (peak ~08:30)")
ax.scatter([], [], s=120, c=aeviz.PALETTE["faded_dark"], label="free-flow arc")
aeviz.legend_outside(ax, loc="lower left", anchor=(0.0, -0.02), fontsize=9)
ax.set_title("Road network: free-flow travel times (* = time-dependent, peaks at rush hour)",
             fontsize=12, color=aeviz.PALETTE["ink"])
ax.margins(0.18)
ax.axis("off")
aeviz.save(fig, "01_network")
plt.close(fig)

# %% [markdown]
# ## Figure 2: travel-time / arrival profiles (the conceptual heart).
# Left: travel time vs departure for three arcs (two FIFO peaks + the non-FIFO spike).
# Right: arrival arr(t)=t+tt(t) for one FIFO arc (monotone) and the non-FIFO arc (dips),
# with the waiting move marked. Monotone arrival = FIFO = "departing later never arrives
# earlier"; the dip is exactly where waiting pays off.

# %%
fig, (axl, axr) = plt.subplots(1, 2, figsize=(12.5, 5.0))
ts = np.arange(450.0, 600.0, 0.5)  # 07:30..10:00
xt = np.arange(450.0, 601.0, 30.0)
xl = [hm(t) for t in xt]

# -- left: travel time vs departure --
profile_arcs = [("Start", "Center"), ("Center", "Target"), ("Riverside", "Parkway")]
cols = [aeviz.PALETTE["path"], aeviz.PALETTE["accent"], aeviz.PALETTE["good"]]
for (u, v), c in zip(profile_arcs, cols):
    axl.plot(ts, [TT[(u, v)](t) for t in ts], color=c, lw=2.4, label=f"{u}->{v}")
axl.plot(ts, [tt_nonfifo(t) for t in ts], color="#d1495b", lw=2.4, ls=(0, (4, 2)),
         label="bridge (non-FIFO)")
axl.set_title("Travel time vs departure time", fontsize=12, color=aeviz.PALETTE["ink"])
axl.set_xlabel("departure time")
axl.set_ylabel("travel time (min)")
axl.set_xticks(xt)
axl.set_xticklabels(xl)
_legl = axl.legend(fontsize=9, frameon=True)
_legl.get_frame().set_facecolor((0.10, 0.14, 0.20, 0.82))
_legl.get_frame().set_edgecolor(aeviz.PALETTE["faded_dark"])
for _t in _legl.get_texts():
    _t.set_color(aeviz.PALETTE["ink"])
axl.grid(alpha=0.25, color=aeviz.PALETTE["faded_dark"])

# -- right: arrival function arr(t) = t + tt(t) --
fifo_arc = ("Center", "Target")
axr.plot(ts, [t + TT[fifo_arc](t) for t in ts], color=aeviz.PALETTE["accent"], lw=2.6,
         label=f"{fifo_arc[0]}->{fifo_arc[1]} (FIFO: non-decreasing)")
axr.plot(ts, [arr_nonfifo(t) for t in ts], color="#d1495b", lw=2.6, ls=(0, (4, 2)),
         label="bridge (non-FIFO: arr dips)")
# mark the waiting move on the non-FIFO curve
axr.scatter([DEPART_NOW], [arr_leave_now], s=70, color="#d1495b", zorder=5)
axr.scatter([DEPART_WAIT], [arr_after_wait], s=70, color=aeviz.PALETTE["good"], zorder=5)
axr.annotate("leave now\n-> arrive late", (DEPART_NOW, arr_leave_now),
             xytext=(DEPART_NOW - 58, arr_leave_now + 4), fontsize=8.5, color="#d1495b",
             ha="left")
axr.annotate("wait, then leave\n-> arrive earlier", (DEPART_WAIT, arr_after_wait),
             xytext=(DEPART_WAIT + 6, arr_after_wait - 30), fontsize=8.5,
             color=aeviz.PALETTE["good"],
             arrowprops=dict(arrowstyle="-|>", color=aeviz.PALETTE["good"], lw=1.4))
axr.set_title("Arrival arr(t) = t + tt(t): monotone (FIFO) vs dipping (non-FIFO)",
              fontsize=12, color=aeviz.PALETTE["ink"])
axr.set_xlabel("departure time")
axr.set_ylabel("arrival time")
axr.set_xticks(xt)
axr.set_xticklabels(xl)
yt = np.arange(480.0, 601.0, 30.0)
axr.set_yticks(yt)
axr.set_yticklabels([hm(t) for t in yt])
_legr = axr.legend(fontsize=9, frameon=True, loc="upper left")
_legr.get_frame().set_facecolor((0.10, 0.14, 0.20, 0.82))
_legr.get_frame().set_edgecolor(aeviz.PALETTE["faded_dark"])
for _t in _legr.get_texts():
    _t.set_color(aeviz.PALETTE["ink"])
axr.grid(alpha=0.25, color=aeviz.PALETTE["faded_dark"])

aeviz.save(fig, "02_travel_time_profiles")
plt.close(fig)

# %% [markdown]
# ## Figure 3: the earliest-arrival path vs the free-flow-shortest path.
# Bold blue = the time-dependent earliest-arrival path (dodges the peak); dashed amber
# = the free-flow-shortest path (short on paper, hits the rush). Arrival times annotated.

# %%
fig, ax = plt.subplots(figsize=(9.5, 5.0))

# faded everything first
aeviz.draw_curved_edges(ax, POS, list(TT), rad=0.0, color=aeviz.PALETTE["faded"],
                        width=1.6, node_size=NODE_SIZE, zorder=1)
# free-flow-shortest path: dashed amber (the loser)
aeviz.draw_curved_edges(ax, POS, [e for e in FF_EDGES if e not in EA_EDGES], rad=0.0,
                        color=aeviz.PALETTE["warn"], width=3.0, style=(0, (5, 3)),
                        node_size=NODE_SIZE, zorder=2)
# earliest-arrival path: bold blue (the winner)
aeviz.draw_curved_edges(ax, POS, list(EA_EDGES), rad=0.0, color=aeviz.PALETTE["path"],
                        width=4.0, node_size=NODE_SIZE, zorder=3)

draw_nodes(ax, highlight=set(ea_path))
ax.scatter([], [], s=120, c=aeviz.PALETTE["path"],
           label=f"earliest arrival: arrives {hm(ea_time)}")
ax.scatter([], [], s=120, c=aeviz.PALETTE["warn"],
           label=f"free-flow shortest: arrives {hm(ff_real_arrival)}")
aeviz.legend_outside(ax, loc="lower left", anchor=(0.0, -0.04), fontsize=9)
ax.set_title(
    f"Depart {hm(T0)}: the longer free-flow route (bold) dodges the rush and wins by "
    f"{loss:.0f} min",
    fontsize=11.5, color=aeviz.PALETTE["ink"])
ax.margins(0.18)
ax.axis("off")
aeviz.save(fig, "03_earliest_arrival_path")
plt.close(fig)

print("\nFigures written: 01_network, 02_travel_time_profiles, "
      "03_earliest_arrival_path (.png + .svg)")
