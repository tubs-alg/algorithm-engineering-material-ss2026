"""Scheduling-as-a-graph motivation figure for the graphs opener.

What this file contains
-----------------------
A single wide figure (``graph_scheduling.png``) that simultaneously shows
a concrete staff-duty scheduling instance *and* the graph derived from
it. Duties appear as time-bars on a calendar timeline; a pseudo source
node ``s`` and sink node ``t`` bookend the figure so the structure reads
as the classical min-cost-flow / min-path-cover construction. Three
coloured shift paths zig-zag across rows, covering every duty exactly
once.

The domain is deliberately not a street/route network — "graphs = maps"
is the cliché the slide is pushing back against. Duties here are ward
activities (rounds, medication runs, lab draws, …) with fixed time
slots; the edges are "same staffer can go from duty u to duty v" and
have a cost equal to the handover/prep time in between.

Why it exists
-------------
The "Why graphs matter" slide previously cycled through four standard
graph flavours. One strong non-obvious example lands better than four
familiar ones. Scheduling is that example: the graph is *constructed*
from the problem — nodes and edges only exist because we chose this
reduction — and the algorithmic answer (min-cost flow from s to t) is
itself purely graph-theoretic.

How to use
----------
    python gen_graph_scheduling.py

Writes ``graph_scheduling.png`` next to this script.

When to change
--------------
Tweak ``TASKS``, ``EDGES``, and ``SHIFTS`` if a different instance reads
more clearly. Rows are assigned manually so that every shift's path
actually crosses rows — if you change the instance, re-check the
zig-zag property visually.
"""

from __future__ import annotations

import pathlib

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import CELL, FG, setup_mpl

HERE = pathlib.Path(__file__).resolve().parent


# Tasks: (id, label, start_hour, end_hour, row).
# Rows: 0=top, 1=middle, 2=bottom. Concurrent tasks must be on different rows.
# Times chosen so min path cover = 3 AND every chosen path zig-zags rows.
TASKS = [
    ("D1", "Ward round",   8.0,  9.5, 0),
    ("D2", "Med round",    8.5, 10.0, 1),
    ("D3", "Admissions",   9.0, 10.5, 2),
    ("D4", "ICU check",   10.5, 12.0, 0),
    ("D5", "Lab draws",   11.0, 12.5, 1),
    ("D6", "Triage",      11.5, 13.0, 2),
    ("D7", "Ward round",  12.5, 14.0, 0),
    ("D8", "Med round",   13.0, 14.5, 1),
    ("D9", "Handover",    13.5, 15.0, 2),
]


# All feasible transitions (u.end <= v.start). Costs are transit minutes
# between the two routes. We display *all* of these as background arrows to
# make the graph structure visible; the shift paths then highlight which
# ones a particular cover selects.
EDGES = [
    # From D1 (ends 9:30)
    ("D1", "D4", 60),
    ("D1", "D5", 90),
    ("D1", "D6", 120),
    # From D2 (ends 10:00)
    ("D2", "D4", 30),
    ("D2", "D5", 60),
    ("D2", "D6", 90),
    # From D3 (ends 10:30)
    ("D3", "D4",  0),
    ("D3", "D5", 30),
    ("D3", "D6", 60),
    ("D3", "D7", 120),
    # From D4 (ends 12:00)
    ("D4", "D7", 30),
    ("D4", "D8", 60),
    ("D4", "D9", 90),
    # From D5 (ends 12:30)
    ("D5", "D7",  0),
    ("D5", "D8", 30),
    ("D5", "D9", 60),
    # From D6 (ends 13:00)
    ("D6", "D8",  0),
    ("D6", "D9", 30),
]


# Three shifts (paths from source to sink). Every path crosses rows.
SHIFTS = [
    {"path": ["D1", "D6", "D8"], "color": "#4ea8de", "label": "Shift 1"},  # r0→r2→r1
    {"path": ["D2", "D4", "D9"], "color": "#f39c12", "label": "Shift 2"},  # r1→r0→r2
    {"path": ["D3", "D5", "D7"], "color": "#2ecc71", "label": "Shift 3"},  # r2→r1→r0
]


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

BAR_HEIGHT = 0.55
ROW_SPACING = 1.0      # vertical gap between row centres
ROW_TOP_Y = 2.5        # y-centre of row 0
TIMELINE_Y = -0.35
SOURCE_X = 6.4
SINK_X = 17.0


def task_by_id(tid: str):
    for t in TASKS:
        if t[0] == tid:
            return t
    raise KeyError(tid)


def bar_geom(task):
    """Return geometry for a task bar: (x, y, w, h, x_left, x_right, y_centre)."""
    _, _, s, e, row = task
    h = BAR_HEIGHT
    y_centre = ROW_TOP_Y - row * ROW_SPACING
    y = y_centre - h / 2
    x = s
    w = e - s
    return x, y, w, h, x, x + w, y_centre


def main() -> None:
    setup_mpl()

    fig, ax = plt.subplots(figsize=(16, 5.6))
    ax.set_xlim(SOURCE_X - 0.7, SINK_X + 0.9)
    ax.set_ylim(-1.0, 3.4)

    # --- Timeline axis (hours) -------------------------------------------
    for h in range(8, 16):
        ax.axvline(h, color=FG, alpha=0.07, lw=0.8, zorder=0)
        ax.text(h, TIMELINE_Y - 0.08, f"{h:02d}:00",
                ha="center", va="top", color=FG, alpha=0.55, fontsize=9)
    ax.plot([7.8, 15.2], [TIMELINE_Y, TIMELINE_Y],
            color=FG, alpha=0.30, lw=1.0, zorder=1)

    # --- Task bars --------------------------------------------------------
    bar_index: dict[str, tuple] = {}
    for task in TASKS:
        tid, label, _s, _e, _row = task
        x, y, w, h, xl, xr, cy = bar_geom(task)
        bar_index[tid] = (x, y, w, h, xl, xr, cy)
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.0,rounding_size=0.10",
            facecolor=CELL["data"], edgecolor=FG, linewidth=0.9, zorder=3,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, cy, f"{tid}  {label}",
                ha="center", va="center",
                color="white", fontsize=9, fontweight="bold", zorder=4)

    # --- Source and sink nodes -------------------------------------------
    node_r = 0.28
    source_y = ROW_TOP_Y - ROW_SPACING  # align with middle row
    sink_y = source_y
    for cx, cy, label in [(SOURCE_X, source_y, "s"), (SINK_X, sink_y, "t")]:
        circ = mpatches.Circle(
            (cx, cy), node_r,
            facecolor=CELL["control"], edgecolor=FG, linewidth=1.1, zorder=4,
        )
        ax.add_patch(circ)
        ax.text(cx, cy, label,
                ha="center", va="center",
                color="white", fontsize=13, fontweight="bold",
                fontfamily="serif", fontstyle="italic", zorder=5)

    source_attach = (SOURCE_X + node_r, source_y)
    sink_attach = (SINK_X - node_r, sink_y)

    # --- Collect shift-edges so we skip them in the faded pass -----------
    shift_edge_set: set[tuple[str, str]] = set()
    for s in SHIFTS:
        p = s["path"]
        for a, b in zip(p, p[1:]):
            shift_edge_set.add((a, b))

    # --- Faded "all feasible transitions" arrows -------------------------
    for u, v, _cost in EDGES:
        if (u, v) in shift_edge_set:
            continue
        _, _, _, _, _, xr_u, cy_u = bar_index[u]
        _, _, _, _, xl_v, _, cy_v = bar_index[v]
        start = (xr_u, cy_u)
        end = (xl_v, cy_v)
        # curvature sign depends on direction of row change so arrows don't
        # collapse onto each other when endpoints are on the same row
        if cy_v > cy_u:
            curve = 0.25
        elif cy_v < cy_u:
            curve = -0.25
        else:
            curve = 0.35 if (ord(u[1]) % 2 == 0) else -0.35
        ax.annotate(
            "", xy=end, xytext=start,
            arrowprops=dict(
                arrowstyle="-|>", color=FG, alpha=0.28, lw=1.0,
                connectionstyle=f"arc3,rad={curve}",
                shrinkA=3, shrinkB=3,
            ),
            zorder=2,
        )

    # --- Shift paths (highlighted) ---------------------------------------
    for shift in SHIFTS:
        color = shift["color"]
        path = shift["path"]

        # s -> first task
        _, _, _, _, xl_first, _, cy_first = bar_index[path[0]]
        first_entry = (xl_first, cy_first)
        curve = 0.12 if cy_first >= source_y else -0.12
        ax.annotate(
            "", xy=first_entry, xytext=source_attach,
            arrowprops=dict(
                arrowstyle="-|>", color=color, lw=2.3,
                connectionstyle=f"arc3,rad={curve}",
                shrinkA=4, shrinkB=4,
            ),
            zorder=5,
        )

        # task -> task
        for a, b in zip(path, path[1:]):
            _, _, _, _, _, xr_u, cy_u = bar_index[a]
            _, _, _, _, xl_v, _, cy_v = bar_index[b]
            start = (xr_u, cy_u)
            end = (xl_v, cy_v)
            if cy_v > cy_u:
                curve = 0.25
            elif cy_v < cy_u:
                curve = -0.25
            else:
                curve = 0.3
            ax.annotate(
                "", xy=end, xytext=start,
                arrowprops=dict(
                    arrowstyle="-|>", color=color, lw=2.4,
                    connectionstyle=f"arc3,rad={curve}",
                    shrinkA=4, shrinkB=4,
                ),
                zorder=5,
            )

        # last task -> t
        _, _, _, _, _, xr_last, cy_last = bar_index[path[-1]]
        last_exit = (xr_last, cy_last)
        curve = -0.12 if cy_last >= sink_y else 0.12
        ax.annotate(
            "", xy=sink_attach, xytext=last_exit,
            arrowprops=dict(
                arrowstyle="-|>", color=color, lw=2.3,
                connectionstyle=f"arc3,rad={curve}",
                shrinkA=4, shrinkB=4,
            ),
            zorder=5,
        )

    # --- Legend ----------------------------------------------------------
    legend_y = 3.15
    legend_x0 = SOURCE_X
    for i, shift in enumerate(SHIFTS):
        x0 = legend_x0 + i * 1.9
        ax.plot([x0, x0 + 0.45], [legend_y, legend_y],
                color=shift["color"], lw=2.8, solid_capstyle="round")
        ax.text(x0 + 0.55, legend_y, shift["label"],
                color=FG, fontsize=10, va="center", fontweight="bold")

    ax.text(legend_x0 + 3 * 1.9 + 0.4, legend_y,
            "faded arrows = all other feasible transitions",
            color=FG, alpha=0.55, fontsize=9, va="center", fontstyle="italic")

    # --- Caption below timeline -----------------------------------------
    ax.text(
        (SOURCE_X + SINK_X) / 2, -0.85,
        "9 duties, 3 shifts (min path cover); min-cost s→t flow ⇒ cheapest staffing",
        ha="center", va="center",
        color=FG, alpha=0.75, fontsize=10, fontstyle="italic",
    )

    # --- Chrome ----------------------------------------------------------
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_aspect("auto")

    fig.tight_layout()
    out = HERE / "graph_scheduling.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", transparent=True)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
