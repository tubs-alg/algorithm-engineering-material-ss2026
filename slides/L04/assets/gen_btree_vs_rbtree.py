"""Red-black tree vs. B-tree — allocations and cache-line occupancy.

Emits btree_vs_rbtree.png. Two stacked panels sharing a common layout:
  Top:    std::map — one allocation per key. Each node holds one key
          plus color/parent/left/right pointers. Keys scattered across
          unpredictable cache lines.
  Bottom: absl::btree_map — wide nodes sized to one cache line, each
          holding many keys and a handful of child pointers.

Why it exists
-------------
The _04-sorted.qmd slide "When the workload mutates: B-trees" needs one
picture that makes the allocation-count and cache-line story obvious at
a glance. Reuses the shared palette so it reads alongside the vector /
list / deque diagrams.

When to change
--------------
If the sorted-containers section gains a third variant (e.g. a skip
list), extend this generator rather than spawning a new one so the
visual vocabulary stays consistent.
"""

import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, CELL_GAP, CELL_H, CELL_W, FG, PTR,
    draw_annotation, draw_cache_line, draw_cell, draw_pointer,
    save, setup_mpl,
)

setup_mpl()

FIG_WIDTH = 13.0
FIG_HEIGHT = 6.8


def draw_rb_node(ax, cx, cy, key, *, color=CELL["pointer"]):
    """Draw a red-black node: one key cell flanked by three pointer stubs."""
    draw_cell(ax, cx - CELL_W / 2, cy, key, color)
    # Three stub pointers (left child, right child, parent) to evoke the
    # node's fan-out of one.
    for dx, dy in [(-0.25, -0.18), (0.25, -0.18), (0.0, 0.18 + CELL_H)]:
        ax.plot(
            [cx, cx + dx], [cy + CELL_H / 2, cy + dy],
            color=PTR, lw=0.9, solid_capstyle="round",
        )


def draw_btree_node(ax, x0, y, keys, *, color=CELL["data"]):
    """Draw a B-tree node: a run of key cells inside one cache line."""
    for i, k in enumerate(keys):
        draw_cell(ax, x0 + i * CELL_W, y, k, color)
    # Surround with a cache-line rectangle so the "one line per node"
    # point is visible without a caption.
    draw_cache_line(
        ax,
        x0 - 0.05,
        y - 0.05,
        len(keys) * CELL_W - CELL_GAP + 0.1,
        CELL_H + 0.1,
        label="one cache line",
    )


fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(FIG_WIDTH, FIG_HEIGHT))


# --------------------------------------------------------------------------
# std::map (red-black tree) — scattered one-key allocations
# --------------------------------------------------------------------------
ax1.set_title(
    "std::map  —  one heap allocation per key, one key per cache line",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

# Lay keys out at deliberately irregular positions to evoke the allocator
# scatter pattern. Coordinates picked by hand; no simulated randomness.
rb_layout = [
    (1.2,  1.4, 17),
    (3.0,  1.9,  8),
    (4.6,  0.9, 25),
    (6.3,  1.6,  3),
    (7.9,  0.7, 11),
    (9.4,  1.5, 30),
    (11.0, 1.0, 22),
]
for cx, cy, k in rb_layout:
    draw_rb_node(ax1, cx, cy, k)

# Pointer chain along the successor path, deliberately crossing back and
# forth to emphasise unpredictable memory order.
for (x1, y1, _), (x2, y2, _) in zip(rb_layout, rb_layout[1:]):
    draw_pointer(
        ax1, (x1, y1 + CELL_H / 2), (x2, y2 + CELL_H / 2),
        curve=0.25 if x2 > x1 else -0.25,
    )

# One translucent cache-line box around each lonely node, to drive home
# "each node burns its own cache line".
for cx, cy, _ in rb_layout:
    draw_cache_line(
        ax1,
        cx - CELL_W / 2 - 0.08,
        cy - 0.08,
        CELL_W - CELL_GAP + 0.16,
        CELL_H + 0.16,
    )

draw_annotation(
    ax1, 12.3, 1.3,
    "7 keys\n7 allocations\n7 cache lines",
    color=CELL["hot"], ha="left",
)

ax1.set_xlim(0, FIG_WIDTH)
ax1.set_ylim(0, 2.7)
ax1.axis("off")


# --------------------------------------------------------------------------
# absl::btree_map — wide nodes, one cache line per node
# --------------------------------------------------------------------------
ax2.set_title(
    "absl::btree_map  —  many keys per node, one cache line per allocation",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

# Root node with 3 keys, two leaf nodes with 6 keys each. Enough to make
# the density obvious without implying a specific fan-out.
root_keys = [10, 20, 30]
root_x0 = 5.4
root_y = 1.9
draw_btree_node(ax2, root_x0, root_y, root_keys)

leaf1_keys = [2, 4, 6, 8, 9, 11]
leaf1_x0 = 0.9
leaf1_y = 0.4
draw_btree_node(ax2, leaf1_x0, leaf1_y, leaf1_keys)

leaf2_keys = [22, 24, 26, 28, 29, 31]
leaf2_x0 = 7.6
leaf2_y = 0.4
draw_btree_node(ax2, leaf2_x0, leaf2_y, leaf2_keys)

# Root → leaf pointers. Start from the gaps between root keys.
root_gap_y = root_y
draw_pointer(
    ax2,
    (root_x0, root_y),
    (leaf1_x0 + 3 * CELL_W - CELL_GAP / 2, leaf1_y + CELL_H),
    curve=-0.2,
)
draw_pointer(
    ax2,
    (root_x0 + 3 * CELL_W - CELL_GAP, root_y),
    (leaf2_x0 + 3 * CELL_W - CELL_GAP / 2, leaf2_y + CELL_H),
    curve=0.2,
)

draw_annotation(
    ax2, 12.3, 1.3,
    "15 keys\n3 allocations\n3 cache lines",
    color=ACCENT, ha="left",
)

ax2.set_xlim(0, FIG_WIDTH)
ax2.set_ylim(0, 2.7)
ax2.axis("off")


plt.tight_layout()
save(fig, "btree_vs_rbtree.png")
