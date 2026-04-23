"""4-ary heap — pop walked step by step with cache-line highlight.

Emits dary_pop_step1.png .. dary_pop_step4.png. Each frame shows
the same heap (21 slots, depth-shaded) with the tree on top and
the backing array below. The sift step highlights the node being
moved, marks the 4 children being compared with an orange edge,
and overlays a dashed rectangle over the same 4 array slots —
one contiguous cache line holds *all* children of any inner node
in a 4-ary heap.

Why it exists
-------------
The _05-priority-queues.qmd slide "Height is the cost — widen the
tree" needs to show the pop walk on a 4-ary heap so the student
sees both the shallower depth and the "4 children = 1 cache line"
property on the same picture as the binary-heap pop earlier in the
deck. Uses the same step-by-step pattern as gen_heap_pop.py.

When to change
--------------
For an 8-ary variant, bump ``D`` and ``N`` and rewrite the step
definitions accordingly.
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _heap_tree import DEPTH_COLORS, draw_heap_array
from _viz_style import CELL, FG, save, setup_mpl

setup_mpl()

D = 4
N = 21  # 1 + 4 + 16 — three levels exactly.


def depth_dary(i: int, d: int = D) -> int:
    if i == 0:
        return 0
    level = 0
    upper = 0
    size = 1
    while upper < i:
        level += 1
        size *= d
        upper += size
    return level


def first_index_at_level(level: int, d: int = D) -> int:
    if level == 0:
        return 0
    total = 1
    s = 1
    for _ in range(level):
        total += s * d
        s *= d
    return total - s


def count_at_level(level: int, n: int, d: int = D) -> int:
    start = first_index_at_level(level, d)
    end = first_index_at_level(level + 1, d)
    return max(0, min(end, n) - start)


# --- step definitions --------------------------------------------------
# Start: valid 4-ary min-heap with keys 1..21 in level order.
# pop returns 1; move last element (21) into the root slot; sift down.
STEPS = [
    {
        "title":    "0. start: valid 4-ary min-heap (21 keys)",
        "keys":     list(range(1, 22)) + [None] * 0,  # all 21 slots filled
        "highlight": [0],
        "child_range": None,
    },
    {
        "title":    "1. return 1; last element (21) → root",
        # Array loses one slot. Drawn as None at the end to preserve width.
        "keys":     [21, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                     11, 12, 13, 14, 15, 16, 17, 18, 19, 20, None],
        "highlight": [0],
        "child_range": (1, 4),   # will compare against children 1..4
    },
    {
        "title":    "2. 21 > min(2, 3, 4, 5) = 2 → swap with idx 1",
        "keys":     [2, 21, 3, 4, 5, 6, 7, 8, 9, 10,
                     11, 12, 13, 14, 15, 16, 17, 18, 19, 20, None],
        "highlight": [1],
        "child_range": (5, 8),   # children of idx 1 are idx 5..8
    },
    {
        "title":    "3. 21 > min(6, 7, 8, 9) = 6 → swap with idx 5; now a leaf → done",
        "keys":     [2, 6, 3, 4, 5, 21, 7, 8, 9, 10,
                     11, 12, 13, 14, 15, 16, 17, 18, 19, 20, None],
        "highlight": [5],
        "child_range": None,     # leaf — no further comparison
    },
]


def draw_tree(
    ax,
    keys,
    *,
    highlight: list[int] | None = None,
    cache_children: tuple[int, int] | None = None,
    x_span: tuple[float, float] = (0.04, 0.96),
    y_top: float = 0.88,
    level_height: float = 0.20,
    cell_w: float = 0.05,
    cell_h: float = 0.085,
) -> None:
    highlight = highlight or []
    left, right = x_span
    n = len(keys)

    def pos(i: int) -> tuple[float, float]:
        level = depth_dary(i)
        start = first_index_at_level(level)
        idx_in_level = i - start
        count = count_at_level(level, n)
        if count == 1:
            x = (left + right) / 2
        else:
            x = left + (right - left) * (idx_in_level + 0.5) / count
        y = y_top - level * level_height
        return x, y

    cache_range = None
    if cache_children is not None:
        cache_range = set(range(cache_children[0], cache_children[1] + 1))

    # Edges (orange for the 4 children being compared).
    for i in range(n):
        if keys[i] is None:
            continue
        for k in range(1, D + 1):
            child = D * i + k
            if child >= n or keys[child] is None:
                continue
            xp, yp = pos(i)
            xc, yc = pos(child)
            is_hl = cache_range is not None and child in cache_range and i in highlight
            ax.plot(
                [xp, xc],
                [yp - cell_h / 2, yc + cell_h / 2],
                color=CELL["warn"] if is_hl else FG,
                lw=2.0 if is_hl else 0.7,
                solid_capstyle="round", zorder=1,
            )

    # Nodes.
    for i, k in enumerate(keys):
        if k is None:
            continue
        x, y = pos(i)
        color = DEPTH_COLORS[min(depth_dary(i), len(DEPTH_COLORS) - 1)]
        rect = mpatches.FancyBboxPatch(
            (x - cell_w / 2, y - cell_h / 2),
            cell_w, cell_h,
            boxstyle="round,pad=0.003",
            facecolor=color, edgecolor=FG, linewidth=0.5,
            zorder=2,
        )
        ax.add_patch(rect)
        ax.text(
            x, y, str(k),
            ha="center", va="center",
            fontsize=8, color="white",
            fontfamily="monospace", fontweight="bold",
            zorder=3,
        )
        if i in highlight:
            ring = mpatches.FancyBboxPatch(
                (x - cell_w / 2 - 0.006, y - cell_h / 2 - 0.006),
                cell_w + 0.012, cell_h + 0.012,
                boxstyle="round,pad=0.003",
                facecolor="none", edgecolor=CELL["warn"], linewidth=2.0,
                zorder=4,
            )
            ax.add_patch(ring)


FIG_W = 12.0
FIG_H = 5.5
ARRAY_Y = 0.22
ARRAY_SPAN = (0.06, 0.94)
ARRAY_CELL_H = 0.09


for idx, step in enumerate(STEPS, start=1):
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    # No figure-level title: the slide already shows the section heading.
    draw_tree(
        ax,
        step["keys"],
        highlight=step["highlight"],
        cache_children=step["child_range"],
    )

    # Per-step caption stays inside the axes.
    ax.text(
        0.5, 0.97, step["title"],
        ha="center", va="bottom",
        fontsize=10, color=FG, fontstyle="italic",
    )

    draw_heap_array(
        ax,
        step["keys"],
        y=ARRAY_Y,
        x_span=ARRAY_SPAN,
        cell_h=ARRAY_CELL_H,
        font_size=10,
        show_indices=True,
        label="heap[]",
        depth_fn=depth_dary,   # match the 4-ary tree colouring
    )

    # Cache-line overlay on the 4 children currently being compared.
    if step["child_range"] is not None:
        lo, hi = step["child_range"]  # inclusive
        array_left, array_right = ARRAY_SPAN
        cell_w_arr = (array_right - array_left) / len(step["keys"])
        cache_x0 = array_left + lo * cell_w_arr
        cache_x1 = array_left + (hi + 1) * cell_w_arr
        pad = 0.006
        cache_rect = mpatches.Rectangle(
            (cache_x0 - pad, ARRAY_Y - ARRAY_CELL_H / 2 - pad),
            (cache_x1 - cache_x0) + 2 * pad,
            ARRAY_CELL_H + 2 * pad,
            facecolor="none",
            edgecolor=CELL["cache"], linewidth=1.8,
            linestyle=(0, (3, 2)),
            zorder=5,
        )
        ax.add_patch(cache_rect)
        ax.text(
            (cache_x0 + cache_x1) / 2,
            ARRAY_Y + ARRAY_CELL_H / 2 + pad + 0.02,
            "one cache-line fetch → all 4 children",
            ha="center", va="bottom",
            fontsize=9, color=CELL["cache"], fontstyle="italic",
            fontweight="bold",
        )

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.02, 1.05)
    ax.axis("off")
    plt.tight_layout()
    save(fig, f"dary_pop_step{idx}.png")
