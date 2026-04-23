"""Binary heap — push operation as a sequence of step-by-step PNGs.

Emits heap_push_step1.png .. heap_push_step4.png. Each PNG is one
snapshot of the same heap at identical canvas size, so the slide
can stack them under ``::: {.r-stack}`` and flip between them with
``::: {.fragment .current-visible}`` for an in-place animation.

Why per-step PNGs
-----------------
A single combined figure forces the reader to parse a row of small
trees at once. Separate PNGs with reveal.js fragments animate the
sift-up one swap at a time — the same visual pattern the rest of
the deck uses for algorithm walk-throughs.

Why it exists
-------------
The _05-priority-queues.qmd slide "Push: bubble up" walks through
inserting a new minimum into a valid heap and bubbling it to the
root. The step figures are the core of that slide.

When to change
--------------
For a max-heap, flip the comparison logic in ``STEPS`` below. The
helper ``_heap_tree.draw_heap_tree`` is heap-arity agnostic.
"""

import matplotlib.pyplot as plt

from _heap_tree import draw_heap_array, draw_heap_tree
from _viz_style import FG, save, setup_mpl

setup_mpl()

# Step 1: initial valid min-heap (7 keys, 3 levels).
# Step 2: new key 1 appended at the end — heap property violated.
# Step 3: 1 swaps with parent 5 (idx 1 ↔ 3).
# Step 4: 1 swaps with parent 2 (idx 0 ↔ 1).
# Step 5: final heap — 1 is the new root, heap property restored.
# Every step keeps the array at the same length (8 slots) so the
# viewer's eye can track slot positions across the animation — an
# empty trailing cell (``None``) marks the as-yet-unused slot in the
# initial state.
STEPS = [
    {
        "keys":     [2, 5, 3, 9, 7, 4, 8, None],
        "highlight": [],
        "swap":     None,
        "title":    "0. start: valid min-heap (7 keys, one empty slot)",
    },
    {
        "keys":     [2, 5, 3, 9, 7, 4, 8, 1],
        "highlight": [7],
        "swap":     (3, 7),
        "title":    "1. append 1 at the end — heap property violated",
    },
    {
        "keys":     [2, 5, 3, 1, 7, 4, 8, 9],
        "highlight": [3],
        "swap":     (1, 3),
        "title":    "2. 1 < 5 → swap with parent",
    },
    {
        "keys":     [2, 1, 3, 5, 7, 4, 8, 9],
        "highlight": [1],
        "swap":     (0, 1),
        "title":    "3. 1 < 2 → swap with parent",
    },
    {
        "keys":     [1, 2, 3, 5, 7, 4, 8, 9],
        "highlight": [0],
        "swap":     None,
        "title":    "4. 1 is the root — done",
    },
]

FIG_W = 7.5
FIG_H = 4.8


for idx, step in enumerate(STEPS, start=1):
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    # No figure-level title: the slide already shows the section
    # heading ("push: append, then bubble up"). Per-step captions
    # stay inside the axes.
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
    save(fig, f"heap_push_step{idx}.png")
