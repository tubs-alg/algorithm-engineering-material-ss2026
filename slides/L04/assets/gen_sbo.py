"""Small-buffer optimization — inline storage vs. heap storage.

Emits sbo.png. Two stacked rows:
  Top:   std::vector<int> layout — control block on the stack, data on
         the heap, always.
  Bot:   InlinedVector<int, 4> with size<=4 — data lives inside the
         control block; no heap allocation.
"""

import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, CELL_GAP, CELL_H, CELL_W, FG, PTR,
    draw_annotation, draw_cell, draw_pointer, draw_routed_pointer,
    save, setup_mpl,
)

setup_mpl()

FIG_WIDTH = 12.0
CTRL_W = CELL_W * 1.35   # control-block cells are wider for labels


def draw_control(ax, x0, y, fields, label):
    """Draw a 3-wide control block: each field is one cell."""
    for i, (name, value, color) in enumerate(fields):
        draw_cell(
            ax, x0 + i * CTRL_W, y, value,
            color, w=CTRL_W, fontsize=9,
        )
        ax.text(
            x0 + i * CTRL_W + (CTRL_W - CELL_GAP) / 2, y - 0.16, name,
            ha="center", va="top", fontsize=7, color=FG,
            fontfamily="monospace",
        )
    ax.text(
        x0 - 0.2, y + CELL_H / 2, label,
        ha="right", va="center", color=FG,
        fontsize=10, fontfamily="monospace", fontweight="bold",
    )


def draw_heap_block(ax, x, y, values, color):
    for i, v in enumerate(values):
        draw_cell(ax, x + i * CELL_W, y, v, color)


fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(FIG_WIDTH, 4.8))


# -- std::vector<int> --
ax1.set_title(
    "std::vector<int> — control block on the stack, elements on the heap",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

ctrl_x = 1.4
ctrl_y = 0.3
draw_control(
    ax1, ctrl_x, ctrl_y,
    [("data", "•", CELL["control"]),
     ("size", "4", CELL["index"]),
     ("cap",  "8", CELL["index"])],
    "vec",
)

# Heap block to the right
heap_x = ctrl_x + 3 * CTRL_W + 1.6
draw_heap_block(ax1, heap_x, ctrl_y, [7, 3, 9, 1, "·", "·", "·", "·"], CELL["data"])
# Note: trailing "·" cells represent unused capacity; reuse cold colour.
for j in range(4, 8):
    # Overwrite with cold-coloured cell to signal uninitialised tail.
    draw_cell(ax1, heap_x + j * CELL_W, ctrl_y, "·",
              CELL["cold"], text_color="#777")

ax1.text(
    heap_x + 4 * CELL_W - CELL_GAP / 2, ctrl_y + CELL_H + 0.1,
    "heap allocation", ha="center", va="bottom",
    fontsize=8, color=FG, fontstyle="italic",
)

# Route the pointer above the control block so it doesn't cross the
# size/cap cells between 'data' and the heap block.
draw_routed_pointer(
    ax1,
    (ctrl_x + (CTRL_W - CELL_GAP) / 2, ctrl_y + CELL_H + 0.02),
    (heap_x + (CELL_W - CELL_GAP) / 2, ctrl_y + CELL_H + 0.02),
    clearance=0.35,
)

draw_annotation(
    ax1, heap_x + 8 * CELL_W + 0.5, ctrl_y + CELL_H / 2,
    "one indirection\neven for 4 ints",
    color=CELL["hot"], ha="left",
)

ax1.set_xlim(0, FIG_WIDTH - 0.5)
ax1.set_ylim(-0.55, 1.25)
ax1.axis("off")


# -- InlinedVector<int, 4> --
ax2.set_title(
    "InlinedVector<int, 4> — elements live inside the control block",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

inl_x = 1.4
inl_y = 0.3
# Control fields first, then four inline slots.
for i, (name, value, color) in enumerate([
    ("size", "4", CELL["index"]),
    ("cap",  "4", CELL["index"]),
]):
    draw_cell(ax2, inl_x + i * CTRL_W, inl_y, value,
              color, w=CTRL_W, fontsize=9)
    ax2.text(
        inl_x + i * CTRL_W + (CTRL_W - CELL_GAP) / 2, inl_y - 0.16, name,
        ha="center", va="top", fontsize=7, color=FG, fontfamily="monospace",
    )

inline_x = inl_x + 2 * CTRL_W
inline_values = [7, 3, 9, 1]
for j, v in enumerate(inline_values):
    draw_cell(ax2, inline_x + j * CELL_W, inl_y, v, CELL["ok"])
ax2.text(
    inline_x + 4 * CELL_W / 2 - CELL_GAP / 2, inl_y - 0.16, "inline buffer",
    ha="center", va="top", fontsize=7, color=FG, fontfamily="monospace",
)

ax2.text(
    0.8, inl_y + CELL_H / 2, "vec",
    ha="right", va="center", color=FG,
    fontsize=10, fontfamily="monospace", fontweight="bold",
)

draw_annotation(
    ax2, inline_x + 4 * CELL_W + 1.2, inl_y + CELL_H / 2,
    "no heap allocation\nwhile size ≤ 4",
    color=ACCENT, ha="left",
)

ax2.set_xlim(0, FIG_WIDTH - 0.5)
ax2.set_ylim(-0.55, 1.25)
ax2.axis("off")

plt.tight_layout()
save(fig, "sbo.png")
