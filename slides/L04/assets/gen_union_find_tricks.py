"""Union-Find tricks animation — path compression.

What this file contains
-----------------------
Emits a sequence of step PNGs (``union_find_tricks_step_NN.png``) that
walk through a naive unite sequence, build a long chain, and then show
``find`` triggering path compression. The parent array is drawn below
the node row so students see the actual O(n) storage state evolve in
lockstep with the tree.

Why it exists
-------------
The static ``union_find_compression.png`` showed before/after as two
panels next to each other. An animation makes the collapse visceral —
five arrows all swing to the root in a single click — and ties the
picture back to the integer array from the implementation.

How to use
----------
    python gen_union_find_tricks.py

Steps (on the slide via ``r-stack`` + fragments):
  00  six singletons, parent[i] = i
  01  unite(0, 1)
  02  unite(1, 2)   -> chain of length 2
  03  unite(2, 3)   -> chain of length 3
  04  unite(4, 5)   -> side component
  05  unite(3, 5)   -> chain of length 4, with 4 as branch
  06  find(0)       -> walk path highlighted
  07  path compression -> every visited node re-parents directly to 5

When to change
--------------
Adjust ``STEPS`` here. The node layout is a fixed row so arrow arcs
stay comparable across frames; do not change node positions per step.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, CELL_GAP, CELL_H, CELL_W, FG, NEGATIVE, PTR,
    draw_cell, save, setup_mpl,
)

setup_mpl()

OUT_DIR = Path(__file__).parent

N = 10
NODE_SPACING = 1.3
X = [i * NODE_SPACING for i in range(N)]
Y_NODE = 0.0
NODE_R = 0.34

ROW_LABEL_X = -1.1  # x for "parent:" / "index:" labels

# Semantic colours.
NODE_COLOR = CELL["data"]       # plain node
ROOT_COLOR = CELL["ok"]          # current root
WALK_COLOR = CELL["hot"]         # node on the find-walk path
NEW_EDGE_COLOR = ACCENT          # edge just added
STALE_EDGE_COLOR = CELL["cold"]  # old parent pointer being replaced
COMPRESSED_EDGE_COLOR = ACCENT   # new direct-to-root pointer


def find_root(parent: list[int], x: int) -> int:
    while parent[x] != x:
        x = parent[x]
    return x


def walk_path(parent: list[int], x: int) -> list[int]:
    """Nodes visited by `find(x)`, from `x` up to (and including) the root."""
    out = [x]
    while parent[out[-1]] != out[-1]:
        out.append(parent[out[-1]])
    return out


def _apply_unite(parent: list[int], x: int, y: int) -> list[int]:
    """Naive unite: make find(x) a child of find(y)."""
    out = list(parent)
    rx = x
    while out[rx] != rx:
        rx = out[rx]
    ry = y
    while out[ry] != ry:
        ry = out[ry]
    if rx != ry:
        out[rx] = ry
    return out


def _annotate_changes(steps: list[dict]) -> None:
    """Fill in ``changed_cells`` per step by diffing against the previous one.

    A cell is "changed" if ``parent[i]`` differs from the previous step. This
    is the single source of truth for green highlighting: edge arrows and
    parent-array cells both key off the same diff, so the animation can
    never disagree with itself (no more "compression lit up a node that
    wasn't on the walk").
    """
    prev = None
    for step in steps:
        changed: set[int] = set()
        if prev is not None:
            for i, (a, b) in enumerate(zip(prev, step["parent"])):
                if a != b:
                    changed.add(i)
        step["changed_cells"] = changed
        prev = step["parent"]


def _build_steps() -> list[dict]:
    """Ten singletons, a worst-case unite sequence, find, then compression."""
    steps: list[dict] = []
    parent = list(range(N))

    steps.append({
        "label": "",
        "parent": parent,
        "new_edge": None,
        "walk": None,
        "compressed": False,
        "note": "ten singletons — parent[i] = i",
    })

    unites = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5),  # chain 0..5, depth 5
        (6, 7), (5, 7),                          # attach side pair 6→7, then chain→7
        (8, 9), (7, 9),                          # side pair 8→9, then all under 9
    ]
    for x, y in unites:
        rx = x
        while parent[rx] != rx:
            rx = parent[rx]
        parent = _apply_unite(parent, x, y)
        steps.append({
            "label": f"unite({x}, {y})",
            "parent": parent,
            "new_edge": (rx, parent[rx]),
            "walk": None,
            "compressed": False,
            "note": "",
        })
    steps[-1]["note"] = "worst-case chain: depth 7"

    # find(0) walks the chain from leaf to root.
    path = [0]
    while parent[path[-1]] != path[-1]:
        path.append(parent[path[-1]])
    steps.append({
        "label": "find(0)",
        "parent": parent,
        "new_edge": None,
        "walk": path,
        "compressed": False,
        "note": "walks " + " → ".join(str(n) for n in path),
    })

    # Path compression: every visited node re-parents to the root.
    root = path[-1]
    compressed = list(parent)
    for n in path:
        compressed[n] = root
    steps.append({
        "label": "path compression",
        "parent": compressed,
        "new_edge": None,
        "walk": None,
        "compressed": True,
        "note": "every visited node re-parents to the root",
    })

    _annotate_changes(steps)
    return steps


STEPS: list[dict] = _build_steps()


def arc_rad(x_from: float, x_to: float) -> float:
    """Curve upward, clearing any nodes in between.

    ``rad`` sets the perpendicular offset of the control point as a
    fraction of the chord length. Short hops need a bigger |rad| to
    clear their own node; long hops need less to stay within the frame.
    """
    span = abs(x_to - x_from) / NODE_SPACING
    if span == 0:
        return 0.0
    if span <= 1.1:
        return -0.70   # one-step hop: a generous arc above the target
    if span <= 2.1:
        return -0.50
    if span <= 3.1:
        return -0.38
    return -0.28


def draw_arrow(
    ax,
    i_from: int,
    i_to: int,
    *,
    color: str = PTR,
    lw: float = 1.8,
    alpha: float = 1.0,
    linestyle: str = "-",
) -> None:
    x_from = X[i_from]
    x_to = X[i_to]
    patch = mpatches.FancyArrowPatch(
        (x_from, Y_NODE + NODE_R * 0.2),
        (x_to, Y_NODE + NODE_R * 0.2),
        connectionstyle=f"arc3,rad={arc_rad(x_from, x_to)}",
        arrowstyle="-|>",
        color=color,
        lw=lw,
        mutation_scale=16,
        linestyle=linestyle,
        shrinkA=NODE_R * 28,   # matplotlib units: points
        shrinkB=NODE_R * 28,
        alpha=alpha,
        zorder=5,              # draw on top of nodes
    )
    ax.add_patch(patch)


def render_step(idx: int, step: dict) -> None:
    fig, ax = plt.subplots(figsize=(14.5, 5.4))

    parent = step["parent"]
    walk = step["walk"] or []
    changed_cells: set[int] = step.get("changed_cells", set())
    roots = {find_root(parent, i) for i in range(N)}

    # Step label at the top.
    if step["label"]:
        ax.text(
            (X[0] + X[-1]) / 2, 2.15, step["label"],
            ha="center", va="center",
            fontsize=22, color=FG,
            fontfamily="monospace", fontweight="bold",
        )
    if step["note"]:
        ax.text(
            (X[0] + X[-1]) / 2, 1.75, step["note"],
            ha="center", va="center",
            fontsize=12, color=CELL["index"], fontstyle="italic",
        )

    # Parent arrows. Highlight rules:
    #   - cell changed this step  -> green (new/compressed edge)
    #   - on the find walk         -> red
    #   - otherwise                -> orange (old parent pointer)
    for i in range(N):
        p = parent[i]
        if p == i:
            continue  # root; no arrow
        if i in changed_cells:
            draw_arrow(ax, i, p, color=NEW_EDGE_COLOR, lw=2.4)
        elif walk and i in walk and p in walk:
            draw_arrow(ax, i, p, color=WALK_COLOR, lw=2.4)
        else:
            draw_arrow(ax, i, p, color=PTR, lw=1.6, alpha=0.9)

    # Nodes. Uniform colour throughout — roots are identified by the
    # absence of an outgoing arrow, not by fill. Only the find-walk
    # highlights nodes (in red) so that green stays reserved for
    # "something changed this step".
    for i in range(N):
        x = X[i]
        if i in walk:
            fc = WALK_COLOR
            ec = WALK_COLOR
        else:
            fc = NODE_COLOR
            ec = FG
        circle = mpatches.Circle(
            (x, Y_NODE), NODE_R,
            facecolor=fc, edgecolor=ec, linewidth=1.2, zorder=3,
        )
        ax.add_patch(circle)
        ax.text(
            x, Y_NODE, str(i),
            ha="center", va="center",
            fontsize=16, color="white",
            fontfamily="monospace", fontweight="bold",
            zorder=4,
        )

    # Parent array below — shows the actual storage.
    array_y = -1.9
    ax.text(
        ROW_LABEL_X, array_y + CELL_H / 2, "parent",
        ha="right", va="center",
        fontsize=11, color=FG, fontstyle="italic",
    )
    for i in range(N):
        x_cell = X[i] - CELL_W / 2 + CELL_GAP / 2
        fill = CELL["ok"] if i in changed_cells else CELL["data"]
        draw_cell(ax, x_cell, array_y, parent[i], fill)

    # Index strip underneath the array (i = 0..5 labels).
    index_y = array_y - 0.4
    ax.text(
        ROW_LABEL_X, index_y, "index",
        ha="right", va="center",
        fontsize=10, color=CELL["index"], fontstyle="italic",
    )
    for i in range(N):
        ax.text(
            X[i], index_y, str(i),
            ha="center", va="center",
            fontsize=10, color=CELL["index"], fontfamily="monospace",
        )

    # Axes / limits.
    x_pad = 1.0
    ax.set_xlim(X[0] - 1.6, X[-1] + x_pad)
    ax.set_ylim(array_y - 0.9, 2.6)
    ax.set_aspect("equal")
    ax.axis("off")

    path = OUT_DIR / f"union_find_tricks_step_{idx:02d}.png"
    save(fig, str(path))


def main() -> None:
    for i, step in enumerate(STEPS):
        render_step(i, step)


if __name__ == "__main__":
    main()
