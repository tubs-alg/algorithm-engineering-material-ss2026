"""std::deque layout — map of pointers to fixed-size blocks.

Emits deque_layout.png. The map array runs vertically on the left;
each map entry points right into a separately allocated block of
BLOCK_SIZE elements. Every random-access lookup does one indirection;
every traversal crosses block boundaries.

Layout mirrors gen_chained_map.py so the two figures read as one
visual language (vertical control array + horizontal heap payload).
"""

import matplotlib.pyplot as plt

from _viz_style import (
    CELL, CELL_GAP, CELL_H, CELL_W, FG, NEGATIVE,
    draw_annotation, draw_cell, draw_pointer, save, setup_mpl,
)

setup_mpl()

BLOCK_SIZE = 4
BLOCKS = [
    [1, 4, 1, 5],   # first block partial: deque can push to front too
    [9, 2, 6, 5],
    [3, 5, 8, 9],
    [7, 9, None, None],  # last partial
]

# Geometry — mirrors gen_chained_map.py.
B_W = CELL_W * 1.1           # map cell width
ROW_H = CELL_H + 0.45        # vertical spacing between map rows
BLOCK_X0 = 2.4               # x where each block starts
MAP_X = 0.9

FIG_W = BLOCK_X0 + BLOCK_SIZE * CELL_W + 1.4
FIG_H = len(BLOCKS) * ROW_H + 1.2


def row_y(i: int) -> float:
    """Top-to-bottom: map[0] at the top."""
    return (len(BLOCKS) - 1 - i) * ROW_H + 0.3


fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_title(
    "std::deque — map of block pointers; each block is a separate heap allocation",
    fontsize=13, fontweight="bold", color=FG, loc="left", pad=10,
)

# -- Map column (control array) ------------------------------------------
ax.text(
    MAP_X + (B_W - CELL_GAP) / 2, row_y(0) + CELL_H + 0.25,
    "map", ha="center", va="bottom",
    color=CELL["index"], fontfamily="monospace", fontweight="bold", fontsize=13,
)

for i in range(len(BLOCKS)):
    y = row_y(i)
    draw_cell(ax, MAP_X, y, "•", CELL["control"], w=B_W, fontsize=14)
    ax.text(
        MAP_X - 0.12, y + CELL_H / 2, f"[{i}]",
        ha="right", va="center",
        fontsize=11, color=FG, fontfamily="monospace",
    )


# -- Blocks --------------------------------------------------------------
for i, block in enumerate(BLOCKS):
    y = row_y(i)
    for j, v in enumerate(block):
        x = BLOCK_X0 + j * CELL_W
        if v is None:
            draw_cell(ax, x, y, "·", "#1a1a2e", text_color="#555")
        else:
            draw_cell(ax, x, y, v, CELL["data"])

    ax.text(
        BLOCK_X0 + BLOCK_SIZE * CELL_W + 0.15, y + CELL_H / 2,
        f"block {i}", ha="left", va="center",
        fontsize=9, color=FG, fontstyle="italic",
    )

    # Arrow from map cell into block[0].
    src = (MAP_X + (B_W - CELL_GAP), y + CELL_H / 2)
    dst = (BLOCK_X0, y + CELL_H / 2)
    draw_pointer(ax, src, dst)


# Callout: iteration crosses block boundaries.
draw_annotation(
    ax, BLOCK_X0 + BLOCK_SIZE * CELL_W / 2, row_y(len(BLOCKS) - 1) - 0.55,
    "iteration crosses block boundaries",
    color=NEGATIVE, fontsize=11,
)

ax.set_xlim(0.0, FIG_W)
ax.set_ylim(-0.3, row_y(0) + CELL_H + 0.8)
ax.axis("off")

plt.tight_layout()
save(fig, "deque_layout.png")
