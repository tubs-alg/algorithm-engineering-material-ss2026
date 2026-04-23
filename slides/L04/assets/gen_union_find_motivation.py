"""Union-Find motivation animation.

What this file contains
-----------------------
Emits a sequence of step PNGs (``union_find_motivation_step_NN.png``) that
show a graph over eight vertices with edges added one unite at a time.
Each connected component is drawn in a single colour so the partition is
visually obvious. The last step highlights a ``find`` query.

Why it exists
-------------
Replaces the earlier math-only animation on the motivation slide. A graph
is a much more natural way to convey "what unite does" — every new edge
merges two components, and the colour collapse shows the partition state
without reading a set-notation line.

How to use
----------
    python gen_union_find_motivation.py

Steps reproduced on the slide (via ``r-stack`` + fragments):
  00  eight isolated singletons
  01  unite(0, 1)
  02  unite(2, 3)
  03  unite(4, 5)
  04  unite(1, 3)      -> {0,1,2,3} collapses into one colour
  05  find(0) == find(2) -> highlight both endpoints, green "same"

When to change
--------------
Tweak ``NODE_POS`` or the edge sequence here and re-run. Do not edit the
PNGs by hand.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import ACCENT, CELL, FG, save, setup_mpl

setup_mpl()

OUT_DIR = Path(__file__).parent

# Eight nodes arranged on a circle — any pair of vertices can be joined
# with a straight edge that does not cross unrelated nodes.
N = 8
RADIUS = 2.4
NODE_POS = {
    i: (
        RADIUS * math.cos(math.radians(90 - i * 360 / N)),
        RADIUS * math.sin(math.radians(90 - i * 360 / N)),
    )
    for i in range(N)
}

# Fixed colour per root (smallest element in component). Roots 6 and 7
# stay singletons throughout, so they keep the neutral colour.
ROOT_COLOR = {
    0: CELL["ok"],       # green    — {0,1} then {0,1,2,3}
    2: CELL["index"],    # blue     — {2,3} before the merge
    4: CELL["warn"],     # orange   — {4,5}
}
SINGLETON_COLOR = CELL["cold"]
EDGE_COLOR = FG
HIGHLIGHT = CELL["hot"]      # the find-query pulse colour

# Edge sequence mirrors the speaker narration.
EDGES_BY_STEP = [
    [],                                      # step 00
    [(0, 1)],                                # step 01
    [(0, 1), (2, 3)],                        # step 02
    [(0, 1), (2, 3), (4, 5)],                # step 03
    [(0, 1), (2, 3), (4, 5), (1, 3)],        # step 04
    [(0, 1), (2, 3), (4, 5), (1, 3)],        # step 05 — same edges, query overlay
]

# Labels above the graph, describing the current call.
CALL_LABEL = [
    "",
    "unite(0, 1)",
    "unite(2, 3)",
    "unite(4, 5)",
    "unite(1, 3)",
    "find(0) == find(2)",
]


def components(edges: list[tuple[int, int]]) -> dict[int, int]:
    """Union-find on the edges we have so far; return node -> root."""
    parent = list(range(N))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[min(ra, rb)] = min(ra, rb)
            parent[max(ra, rb)] = min(ra, rb)
    return {i: find(i) for i in range(N)}


def node_color(root: int, *, is_singleton: bool) -> str:
    if is_singleton:
        return SINGLETON_COLOR
    return ROOT_COLOR.get(root, CELL["pointer"])


def render_step(step: int, edges: list[tuple[int, int]], *, query: tuple[int, int] | None = None) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.2))

    # Draw edges first so the nodes sit on top.
    for a, b in edges:
        xa, ya = NODE_POS[a]
        xb, yb = NODE_POS[b]
        ax.plot([xa, xb], [ya, yb], color=EDGE_COLOR, lw=2.0, zorder=1, alpha=0.85)

    roots = components(edges)
    sizes: dict[int, int] = {}
    for r in roots.values():
        sizes[r] = sizes.get(r, 0) + 1

    # Draw nodes.
    for i in range(N):
        x, y = NODE_POS[i]
        root = roots[i]
        color = node_color(root, is_singleton=sizes[root] == 1)
        edge = FG
        lw = 1.2
        if query is not None and i in query:
            edge = HIGHLIGHT
            lw = 2.6
        circle = mpatches.Circle(
            (x, y), 0.36, facecolor=color, edgecolor=edge, linewidth=lw, zorder=2,
        )
        ax.add_patch(circle)
        ax.text(
            x, y, str(i),
            ha="center", va="center",
            fontsize=15, color="white", fontweight="bold",
            fontfamily="monospace", zorder=3,
        )

    # Call label above the graph.
    if CALL_LABEL[step]:
        ax.text(
            0, RADIUS + 1.0, CALL_LABEL[step],
            ha="center", va="center",
            fontsize=18, color=FG, fontfamily="monospace", fontweight="bold",
        )

    # Query verdict below the graph.
    if query is not None:
        a, b = query
        same = roots[a] == roots[b]
        verdict = "same set ✓" if same else "different sets ✗"
        ax.text(
            0, -RADIUS - 0.9, verdict,
            ha="center", va="center",
            fontsize=16, color=ACCENT if same else HIGHLIGHT,
            fontweight="bold",
        )

    pad = 1.4
    ax.set_xlim(-RADIUS - pad, RADIUS + pad)
    ax.set_ylim(-RADIUS - pad, RADIUS + pad)
    ax.set_aspect("equal")
    ax.axis("off")

    path = OUT_DIR / f"union_find_motivation_step_{step:02d}.png"
    save(fig, str(path))


def main() -> None:
    for step, edges in enumerate(EDGES_BY_STEP):
        query = (0, 2) if step == 5 else None
        render_step(step, edges, query=query)


if __name__ == "__main__":
    main()
