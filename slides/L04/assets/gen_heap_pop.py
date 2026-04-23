"""Binary heap — pop operation as a sequence of step-by-step PNGs.

Emits heap_pop_step1.png .. heap_pop_step3.png. Each PNG is one
snapshot of the same heap at identical canvas size, so the slide
can stack them under ``::: {.r-stack}`` and flip between them with
``::: {.fragment .current-visible}`` for an in-place animation.

Why it exists
-------------
The _05-priority-queues.qmd slide "Pop: sift down" walks through
extracting the minimum: move the last element to the root, then
sift it down. Mirrors ``gen_heap_push.py``.

When to change
--------------
For a max-heap, flip the comparison logic in ``STEPS`` below.
"""

import matplotlib.pyplot as plt

from _heap_tree import draw_heap_array, draw_heap_tree
from _viz_style import FG, save, setup_mpl

setup_mpl()

# Step 1: initial valid min-heap (8 keys). Root is the min we will extract.
# Step 2: extract_min returns 1; the last element (9) takes the root slot
#         so the array stays contiguous — heap property violated.
# Step 3: 9 swaps with smaller child 2 (idx 0 ↔ 1).
# Step 4: 9 swaps with smaller child 5 (idx 1 ↔ 3). Now a leaf — done.
# Every step keeps the array at the same length (8 slots) so the
# viewer's eye can track slot positions across the animation — the
# last slot empties out after the root is extracted.
STEPS = [
    {
        "keys":     [1, 2, 3, 5, 7, 4, 8, 9],
        "highlight": [0],
        "swap":     None,
        "title":    "0. start: valid min-heap — min is at the root",
    },
    {
        "keys":     [9, 2, 3, 5, 7, 4, 8, None],
        "highlight": [0],
        "swap":     (0, 1),
        "title":    "1. return 1; last element (9) → root",
    },
    {
        "keys":     [2, 9, 3, 5, 7, 4, 8, None],
        "highlight": [1],
        "swap":     (1, 3),
        "title":    "2. 9 > min(5, 7) → swap with smaller child",
    },
    {
        "keys":     [2, 5, 3, 9, 7, 4, 8, None],
        "highlight": [3],
        "swap":     None,
        "title":    "3. 9 is a leaf — done",
    },
]

FIG_W = 7.5
FIG_H = 4.8


for idx, step in enumerate(STEPS, start=1):
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    # No figure-level title: the slide already shows the section
    # heading ("pop: swap root with last, then sift down").
    draw_heap_tree(
        ax,
        step["keys"],
        highlight=step["highlight"],
        swap_edge=step["swap"],
        title=step["title"],
        x_span=(0.10, 0.95),
        y_top=0.92,
        level_height=0.20,
        cell_w=0.08,
        cell_h=0.10,
        font_size=12,
    )
    draw_heap_array(
        ax,
        step["keys"],
        highlight=step["highlight"],
        y=0.12,
        x_span=(0.10, 0.95),
        cell_h=0.10,
        font_size=11,
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0.0, 1.05)
    plt.tight_layout()
    save(fig, f"heap_pop_step{idx}.png")
