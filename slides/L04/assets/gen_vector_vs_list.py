"""Memory-layout contrast: std::vector vs std::list.

Emits:
  - vector_vs_list.png        (both panels stacked)
  - vector_layout.png         (vector panel only)
  - list_layout.png           (list panel only)

Vector panel: 16 contiguous int cells, two cache lines overlaid showing
that one fetch brings in eight elements.

List panel: same 16 ints as scattered heap nodes (value + next pointer),
pointer arrows in the warning colour. Each hop is a potential cache miss.
"""

import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, CELL_H, CELL_W, FG, NEGATIVE, PTR,
    check_no_overlap, draw_annotation, draw_cache_line, draw_cell,
    draw_pointer, save, setup_mpl,
)

setup_mpl()

N = 16
VALUES = [7, 3, 9, 1, 4, 8, 2, 6, 5, 0, 11, 13, 10, 15, 12, 14]
FIG_WIDTH = 13.0


def draw_vector(ax):
    ax.set_title(
        "std::vector<int> — contiguous in memory",
        fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
    )

    y = 0.3
    # Two cache-line overlays (8 ints = 32 B; typical line = 64 B fits 16,
    # but 8 is a clearer pedagogical unit and matches 32-bit integers
    # vs 32-byte half-line or 64-bit ints on a 64-byte line).
    for k in range(2):
        x0 = k * 8 * CELL_W
        draw_cache_line(
            ax, x0, y - 0.08, 8 * CELL_W - 0.04, CELL_H + 0.16,
            label=f"cache line {k}",
        )

    for i, v in enumerate(VALUES):
        draw_cell(ax, i * CELL_W, y, v, CELL["data"])

    # Index labels underneath
    for i in (0, 7, 8, 15):
        ax.text(
            i * CELL_W + (CELL_W - 0.06) / 2, y - 0.18,
            f"[{i}]", ha="center", va="top",
            fontsize=7, color=FG, fontfamily="monospace",
        )

    draw_annotation(
        ax, N * CELL_W + 0.6, y + CELL_H / 2,
        "1 fetch → 8 elements\nprefetcher streams ahead",
        color=ACCENT, ha="left",
    )

    ax.set_xlim(-0.3, N * CELL_W + 4.5)
    ax.set_ylim(-0.5, 1.4)
    ax.axis("off")


def draw_list(ax):
    ax.set_title(
        "std::list<int> — one heap node per element, scattered",
        fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
    )

    # Node = [value | next-ptr]. Cells stay visible so the pointer cost
    # is explicit. Seven visible nodes on non-overlapping x-slots; logical
    # traversal order crosses the slots in a jumbled sequence to suggest
    # random heap placement.
    val_w = CELL_W
    ptr_w = CELL_W * 0.55
    node_w = val_w + ptr_w

    # Nodes proceed left-to-right in logical order; vertical jitter alone
    # conveys "scattered on the heap". X-slots are spaced wider than a
    # node so cells never touch.
    x_slots = [0.3, 2.0, 3.7, 5.4, 7.1, 8.8, 10.5]
    y_of    = [1.4, 0.3, 1.8, 0.6, 2.0, 0.4, 1.5]

    values = VALUES[: len(x_slots)]
    node_positions = [(x_slots[i], y_of[i]) for i in range(len(values))]

    # Sanity check — warn if any two boxes overlap.
    check_no_overlap(
        [(x, y, node_w, CELL_H) for (x, y) in node_positions],
        pad=0.1,
        labels=[f"node{i}" for i in range(len(values))],
    )

    anchors = []  # (value_left, value_right, ptr_cell_center_x, y)
    for (x, y), v in zip(node_positions, values):
        draw_cell(ax, x, y, v, CELL["pointer"], w=val_w)
        draw_cell(
            ax, x + val_w, y, "•", CELL["control"],
            w=ptr_w, fontsize=11,
        )
        ptr_cx = x + val_w + (ptr_w - 0.06) / 2
        anchors.append((x, x + node_w - 0.06, ptr_cx, y))

    # Straight pointer arrows from each next-cell to the following node.
    for (_, _, src_ptr_cx, src_y), (dst_left, _, _, dst_y) in zip(anchors, anchors[1:]):
        start = (src_ptr_cx, src_y + CELL_H / 2)
        end = (dst_left, dst_y + CELL_H / 2)
        draw_pointer(ax, start, end)

    # Final arrow trails off to "..."
    last_left, last_right, last_ptr_cx, last_y = anchors[-1]
    ax.text(
        last_right + 0.7, last_y + CELL_H / 2, "...",
        ha="left", va="center", color=FG, fontsize=14,
        fontfamily="monospace",
    )
    draw_pointer(
        ax,
        (last_ptr_cx, last_y + CELL_H / 2),
        (last_right + 0.65, last_y + CELL_H / 2),
    )

    draw_annotation(
        ax, 13.2, 2.6,
        "each hop →\npotential cache miss",
        color=NEGATIVE,
    )

    ax.set_xlim(-0.3, 15.5)
    ax.set_ylim(-0.2, 3.0)
    ax.axis("off")


# Combined
fig, (top, bot) = plt.subplots(
    2, 1, figsize=(FIG_WIDTH, 5.6),
    gridspec_kw={"height_ratios": [1.2, 3.2]},
)
draw_vector(top)
draw_list(bot)
plt.tight_layout()
save(fig, "vector_vs_list.png")

# Singles — same figure width so horizontal pixel columns align when
# the slide reveals one above the other.
fig, ax = plt.subplots(figsize=(FIG_WIDTH, 1.9))
draw_vector(ax)
plt.tight_layout()
save(fig, "vector_layout.png")

fig, ax = plt.subplots(figsize=(FIG_WIDTH, 3.6))
draw_list(ax)
plt.tight_layout()
save(fig, "list_layout.png")
