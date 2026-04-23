"""std::unordered_map layout — buckets are pointers to heap-allocated nodes.

Emits chained_hashmap.png. The bucket array runs vertically on the left;
each non-empty bucket points right into a horizontal chain of heap-allocated
nodes. One bucket collided (chain of two). Two buckets are empty.
"""

import matplotlib.pyplot as plt

from _viz_style import (
    CELL, CELL_GAP, CELL_H, CELL_W, FG, NEGATIVE,
    draw_annotation, draw_cell, draw_composite_cell, draw_pointer,
    save, setup_mpl,
)

setup_mpl()

# (bucket_idx, [(key, value), ...])
BUCKETS = [
    (0, [("cat", "C")]),
    (1, []),
    (2, [("dog", "D"), ("owl", "O")]),
    (3, [("fox", "F")]),
    (4, []),
    (5, [("ant", "A")]),
]

# Geometry.
B_W = CELL_W * 1.1           # bucket cell width
ROW_H = CELL_H + 0.35        # vertical spacing between bucket rows
CHAIN_X0 = 2.4               # x where the first node of each chain starts
K_W = CELL_W * 1.0
V_W = CELL_W * 0.7
P_W = CELL_W * 0.6
NODE_W = K_W + V_W + P_W     # total node width (cells, before gap)
CHAIN_DX = NODE_W + 0.55     # horizontal step to the next node in a chain

FIG_W = CHAIN_X0 + 2 * CHAIN_DX + 1.2
FIG_H = len(BUCKETS) * ROW_H + 1.2

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_title(
    "std::unordered_map — bucket array of pointers into separately allocated nodes",
    fontsize=14, fontweight="bold", color=FG, loc="left", pad=10,
)

# Y-coordinate for each bucket row (top bucket = highest y).
def bucket_y(i: int) -> float:
    return (len(BUCKETS) - 1 - i) * ROW_H + 0.3


# -- Bucket column --------------------------------------------------------
BUCKET_X = 0.9
ax.text(
    BUCKET_X + (B_W - CELL_GAP) / 2, bucket_y(0) + CELL_H + 0.25,
    "buckets", ha="center", va="bottom",
    color=CELL["index"], fontfamily="monospace", fontweight="bold", fontsize=13,
)

for i, (bi, chain) in enumerate(BUCKETS):
    y = bucket_y(i)
    if chain:
        draw_cell(ax, BUCKET_X, y, "•", CELL["control"], w=B_W, fontsize=14)
    else:
        draw_cell(ax, BUCKET_X, y, "∅", CELL["cold"],
                  w=B_W, fontsize=13, text_color="#888")
    ax.text(
        BUCKET_X - 0.12, y + CELL_H / 2, f"[{bi}]",
        ha="right", va="center",
        fontsize=11, color=FG, fontfamily="monospace",
    )


# -- Nodes + chains -------------------------------------------------------
def draw_node(x: float, y: float, key: str, value: str, has_next: bool):
    if has_next:
        next_seg = {"w": P_W, "text": "•", "color": CELL["control"], "fontsize": 14}
    else:
        next_seg = {"w": P_W, "text": "∅", "color": CELL["cold"],
                    "fontsize": 12, "text_color": "#888"}
    return draw_composite_cell(
        ax, x, y,
        [
            {"w": K_W, "text": key, "color": CELL["pointer"], "fontsize": 12},
            {"w": V_W, "text": value, "color": CELL["data"], "fontsize": 12},
            next_seg,
        ],
    )


for i, (bi, chain) in enumerate(BUCKETS):
    if not chain:
        continue
    y = bucket_y(i)
    prev_next_x = None
    for j, (k, v) in enumerate(chain):
        x = CHAIN_X0 + j * CHAIN_DX
        has_next = (j < len(chain) - 1)
        left, _ = draw_node(x, y, k, v, has_next)
        if j == 0:
            # Arrow from the bucket cell into the first node of the chain.
            src = (BUCKET_X + (B_W - CELL_GAP), y + CELL_H / 2)
            dst = (left, y + CELL_H / 2)
            draw_pointer(ax, src, dst)
        else:
            src = (prev_next_x, y + CELL_H / 2)
            dst = (left, y + CELL_H / 2)
            draw_pointer(ax, src, dst)
        prev_next_x = x + K_W + V_W + P_W / 2


# Callout: one pointer hop per lookup.
callout_x = CHAIN_X0 + CHAIN_DX + NODE_W / 2
draw_annotation(
    ax, callout_x, bucket_y(len(BUCKETS) - 1) - 0.55,
    "every lookup → pointer hop off the array",
    color=NEGATIVE, fontsize=11,
)

ax.set_xlim(0.0, FIG_W)
ax.set_ylim(-0.3, bucket_y(0) + CELL_H + 0.8)
ax.axis("off")

plt.tight_layout()
save(fig, "chained_hashmap.png")
