"""Binary heap — array storage and implicit tree view.

Emits binary_heap_array.png. One figure, two halves:
  Top:    A flat array of seven keys, indices 0..6, each cell shaded
          by its depth in the implicit tree. The shading ties the
          array positions directly to the tree levels below.
  Bottom: The same seven keys drawn as a binary tree, with each node
          shaded the same as its array cell.

Why it exists
-------------
The _05-priority-queues.qmd slide "Binary heap in a vector" needs one
picture that shows the implicit tree — parent at (i-1)/2, children at
2i+1 and 2i+2 — and makes the "height = cache misses" story visible
at a glance. Colouring cells by depth keeps that point vivid without
any extra annotation.

When to change
--------------
If the heap section gains a d-ary heap comparison figure, consider
extending this into a two-panel "binary vs 4-ary" layout rather than
writing a second generator.
"""

import matplotlib.pyplot as plt

from _heap_tree import draw_heap_array, draw_heap_tree
from _viz_style import CELL, FG, draw_annotation, save, setup_mpl

setup_mpl()

# Heap keys for a min-heap. Seven keys fit exactly into three levels
# of a complete binary tree. Chosen to produce a valid heap-ordered
# tree without being trivially sorted.
KEYS = [2, 5, 3, 9, 7, 4, 8]

FIG_W = 7.5
FIG_H = 4.8

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))

draw_heap_tree(
    ax,
    KEYS,
    x_span=(0.10, 0.95),
    y_top=0.92,
    level_height=0.20,
    cell_w=0.08,
    cell_h=0.10,
    font_size=12,
)
draw_heap_array(
    ax,
    KEYS,
    y=0.12,
    x_span=(0.10, 0.95),
    cell_h=0.10,
    font_size=11,
)

# Caption the index arithmetic in the lower-right corner.
draw_annotation(
    ax, 0.97, 0.30,
    "parent(i) = (i − 1) / 2\n"
    "left(i)   = 2i + 1\n"
    "right(i)  = 2i + 2",
    color=CELL["ok"], ha="right",
)

ax.set_xlim(0, 1)
ax.set_ylim(0.0, 1.05)
ax.axis("off")

plt.tight_layout()
save(fig, "binary_heap_array.png")
