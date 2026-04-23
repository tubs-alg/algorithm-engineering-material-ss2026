"""Open-addressed hash table — probing stays in the same cache line.

Emits open_addressing.png. A single flat array of [key|value] slots. One
key hashes to slot 3 but slot 3 is taken, so the probe walks forward to
slot 4, then 5 where it lands. A cache-line overlay shows that slots
3..5 are all in the same line — the "collision" costs nothing extra.
"""

import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, CELL_GAP, CELL_H, CELL_W, FG, PTR,
    draw_annotation, draw_cache_line, draw_composite_cell, draw_pointer,
    save, setup_mpl,
)

setup_mpl()

N = 12
# (key, value) or None for empty
SLOTS = [
    ("ant", "A"), ("bee", "B"), None,
    ("cat", "C"), ("dog", "D"), ("owl", "O"),   # <- probing here
    None, ("fox", "F"), None,
    ("pig", "P"), None, ("rat", "R"),
]

K_W = CELL_W * 1.0
V_W = CELL_W * 0.7
PAIR_W = K_W + V_W         # pitch: step from one slot's x to the next
INNER_W = PAIR_W - CELL_GAP  # visible width of one slot (leaves a gap between slots)
K_INNER = K_W * (INNER_W / PAIR_W)
V_INNER = INNER_W - K_INNER
Y = 0.5
X0 = 0.6

FIG_W = 15.5
fig, ax = plt.subplots(figsize=(FIG_W, 3.3))
ax.set_title(
    "Open addressing — (key, value) pairs inline; collisions probe adjacent slots",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

# Draw slots
for i, slot in enumerate(SLOTS):
    x = X0 + i * PAIR_W
    if slot is None:
        segs = [
            {"w": K_INNER, "text": "·", "color": CELL["cold"], "text_color": "#666"},
            {"w": V_INNER, "text": "·", "color": CELL["cold"], "text_color": "#666"},
        ]
    else:
        k, v = slot
        segs = [
            {"w": K_INNER, "text": k, "color": CELL["data"]},
            {"w": V_INNER, "text": v, "color": CELL["index"]},
        ]
    draw_composite_cell(ax, x, Y, segs)
    ax.text(
        x + INNER_W / 2, Y - 0.22,
        f"[{i}]", ha="center", va="top",
        fontsize=7, color=FG, fontfamily="monospace",
    )

# Cache-line overlay covering slots 3..6.
first, last = 3, 6
cl_x = X0 + first * PAIR_W - 0.04
cl_w = (last - first + 1) * PAIR_W - CELL_GAP + 0.02
draw_cache_line(ax, cl_x, Y - 0.08, cl_w, CELL_H + 0.16,
                label="one cache line")

# Mark the target slot (hash(target) = 3) and the probe path 3 -> 4 -> 5.
# Put a "hash →" arrow from above onto slot 3.
hash_x = X0 + 3 * PAIR_W + INNER_W / 2
ax.annotate(
    "hash(k) = 3", xy=(hash_x, Y + CELL_H + 0.04),
    xytext=(hash_x, Y + CELL_H + 0.6),
    ha="center", va="bottom", color=CELL["warn"],
    fontsize=9, fontfamily="monospace", fontweight="bold",
    arrowprops=dict(arrowstyle="-|>", color=CELL["warn"], lw=1.2),
)

# Probing arrows: 3 -> 4, 4 -> 5. Vertical legs sit in the gap to the
# right of each slot's [i] label so they don't overlap the labels.
probe_y = Y - 0.55
label_offset = 0.48                                  # right of the [i] label
arrow_top = Y - 0.04
# xs along the path — each source and each destination is one x.
path_xs = [X0 + i * PAIR_W + label_offset for i in (3, 4, 5)]
# One vertical down at each slot on the path (drawn once, even when a
# slot acts as both a destination and the next source).
for px in path_xs:
    ax.plot([px, px], [arrow_top, probe_y],
            color=PTR, lw=1.1, solid_capstyle="butt")
# Horizontal legs connecting consecutive slots.
for a, b in zip(path_xs, path_xs[1:]):
    ax.plot([a, b], [probe_y, probe_y],
            color=PTR, lw=1.1, solid_capstyle="butt")
# Arrowheads at the top of each destination vertical.
for dx in path_xs[1:]:
    ax.annotate(
        "", xy=(dx, arrow_top), xytext=(dx, arrow_top - 0.15),
        arrowprops=dict(arrowstyle="-|>", color=PTR, lw=1.1,
                        shrinkA=0, shrinkB=0),
    )
ax.text(
    X0 + 4 * PAIR_W + label_offset, probe_y - 0.12,
    "probe +1", ha="center", va="top",
    fontsize=8, color=PTR, fontstyle="italic", fontweight="bold",
)

draw_annotation(
    ax, X0 + N * PAIR_W, Y + CELL_H + 0.55,
    "short probe → same line\nno extra miss",
    color=ACCENT, ha="right",
)

right_edge = X0 + N * PAIR_W
ax.set_xlim(-0.3, right_edge + 0.3)
ax.set_ylim(-1.3, 1.7)
ax.axis("off")

plt.tight_layout()
save(fig, "open_addressing.png")
