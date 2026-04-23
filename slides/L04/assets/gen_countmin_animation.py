"""Step-by-step Count-Min sketch walkthrough — one PNG per narrated step.

What this file contains
-----------------------
Emits countmin_step_NN.png for a small Count-Min sketch (d=3 rows,
w=8 columns): an empty grid, two inserts showing per-row hashing and
counter increments, and one query showing the min-across-rows read.

The slide stacks them with `.r-stack` + `.fragment` so each click
advances one step that the speaker narrates.

How to use
----------
Run from the assets/ directory:

    python gen_countmin_animation.py
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import ACCENT, CELL, FG, NEGATIVE, setup_mpl

setup_mpl()

# Colours — reuse palette, add local overrides for clarity
INSERT_ARROW = "#7af09c"       # bright green (same as Bloom insert)
QUERY_ARROW = "#7ecbff"        # bright blue  (same as Bloom query)
COUNTER_FILL = CELL["data"]    # default counter cell
COUNTER_HOT = CELL["hot"]      # the min cell in a query
COUNTER_HIT = ACCENT           # cells touched by an operation
COUNTER_EMPTY = CELL["cold"]   # zero-valued cells

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PREFIX = os.path.join(OUT_DIR, "countmin_step_")

# --- Geometry ----------------------------------------------------------------
D = 3          # rows (hash functions)
W = 8          # columns (width)
CELL_W = 1.0
CELL_H = 0.7
CELL_GAP = 0.06
GRID_X0 = 2.5
GRID_Y0 = 1.4

FIG_W = 13.0
FIG_H = 6.2

ROW_LABELS = ["h\u2081", "h\u2082", "h\u2083"]


# --- Hand-picked hash outputs ------------------------------------------------
# Each insert/query maps to one column index per row.
OPERATIONS = [
    ("insert", "x", [2, 5, 1]),
    ("insert", "y", [2, 3, 6]),      # h1 collision with "x" at col 2
    ("insert", "x", [2, 5, 1]),      # second x — counters go to 2 (col 2 → 3)
    ("query",  "x", [2, 5, 1]),      # min across rows: [3, 2, 2] → 2 ✓
]


def cell_xy(row: int, col: int) -> tuple[float, float]:
    """Bottom-left corner of cell (row, col)."""
    x = GRID_X0 + col * CELL_W
    y = GRID_Y0 + (D - 1 - row) * CELL_H  # row 0 at top
    return x, y


def cell_center(row: int, col: int) -> tuple[float, float]:
    x, y = cell_xy(row, col)
    return x + (CELL_W - CELL_GAP) / 2, y + CELL_H / 2


def render_step(
    path: str,
    grid: list[list[int]],
    op: tuple | None,
    phase: str,
    highlight_cells: list[tuple[int, int]] | None,
    min_cell: tuple[int, int] | None,
    caption: str,
) -> None:
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))

    # Title
    ax.text(
        FIG_W / 2, 5.6,
        "Count-Min sketch  (d = 3 rows, w = 8 columns)",
        ha="center", va="center",
        fontsize=15, color=FG, fontweight="bold",
    )

    highlight_set = set(highlight_cells) if highlight_cells else set()

    # Draw grid
    for r in range(D):
        # Row label
        lx, ly = cell_xy(r, 0)
        ax.text(
            lx - 0.35, ly + CELL_H / 2,
            ROW_LABELS[r],
            ha="center", va="center",
            fontsize=13, color="#9aa0ad", fontfamily="monospace",
            fontweight="bold",
        )
        for c in range(W):
            x, y = cell_xy(r, c)
            val = grid[r][c]

            # Pick fill colour
            if min_cell and (r, c) == min_cell:
                fill = COUNTER_HOT
            elif (r, c) in highlight_set:
                fill = COUNTER_HIT
            elif val > 0:
                fill = COUNTER_FILL
            else:
                fill = COUNTER_EMPTY

            edge = FG
            lw = 0.8
            if (r, c) in highlight_set or (min_cell and (r, c) == min_cell):
                edge = "#ffffff"
                lw = 1.8

            rect = mpatches.FancyBboxPatch(
                (x, y), CELL_W - CELL_GAP, CELL_H,
                boxstyle="round,pad=0.02",
                facecolor=fill, edgecolor=edge, linewidth=lw,
            )
            ax.add_patch(rect)
            ax.text(
                x + (CELL_W - CELL_GAP) / 2, y + CELL_H / 2,
                str(val),
                ha="center", va="center",
                fontsize=13, color="white" if val > 0 else "#888",
                fontfamily="monospace", fontweight="bold",
            )

    # Column indices along the top
    top_row_y = GRID_Y0 + (D - 1) * CELL_H
    for c in range(W):
        x, _ = cell_xy(0, c)
        ax.text(
            x + (CELL_W - CELL_GAP) / 2, top_row_y + CELL_H + 0.12,
            str(c),
            ha="center", va="bottom",
            fontsize=8, color="#9aa0ad", fontfamily="monospace",
        )

    # Operation card + arrows
    if op is not None:
        kind, word, cols = op
        op_color = INSERT_ARROW if kind == "insert" else QUERY_ARROW

        card_y = 4.6
        card_w = 2.4
        card_x = FIG_W / 2 - card_w / 2
        box = mpatches.FancyBboxPatch(
            (card_x, card_y - 0.35), card_w, 0.7,
            boxstyle="round,pad=0.05",
            facecolor="#1e1e2e", edgecolor=op_color, linewidth=1.6,
        )
        ax.add_patch(box)
        ax.text(
            card_x + card_w / 2, card_y,
            f'{kind}  "{word}"',
            ha="center", va="center", color=op_color,
            fontsize=14, fontfamily="monospace", fontweight="bold",
        )

        # Arrows from card to each row's target cell
        start = (card_x + card_w / 2, card_y - 0.38)
        for r, c in enumerate(cols):
            end = cell_center(r, c)
            # Nudge end upward so arrow hits top of cell
            end = (end[0], cell_xy(r, c)[1] + CELL_H)
            ax.annotate(
                "", xy=end, xytext=start,
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=op_color,
                    lw=1.2,
                    shrinkA=2, shrinkB=4,
                ),
            )

    # Min annotation for query result
    if min_cell is not None and phase == "result":
        cx, cy = cell_center(*min_cell)
        ax.text(
            cx, cy - CELL_H / 2 - 0.25,
            "min",
            ha="center", va="top",
            fontsize=11, color=COUNTER_HOT, fontweight="bold",
            fontstyle="italic",
        )

    # Caption
    caption_color = FG
    if phase == "result" and op and op[0] == "query":
        caption_color = QUERY_ARROW

    ax.text(
        FIG_W / 2, 0.6, caption,
        ha="center", va="center",
        fontsize=15, color=caption_color, fontweight="bold",
    )

    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0.0, 6.0)
    ax.axis("off")

    fig.savefig(path, dpi=140, transparent=True)
    plt.close(fig)


# --- Build the sequence ------------------------------------------------------

step = 0
grid = [[0] * W for _ in range(D)]


def save(label: str, **kwargs) -> None:
    global step
    path = f"{PREFIX}{step:02d}.png"
    render_step(path, grid=grid, **kwargs)
    print(f"  step {step:02d}  {label}")
    step += 1


# Step 0: empty
save("empty",
     op=None, phase="idle", highlight_cells=None, min_cell=None,
     caption="Empty sketch \u2014 every counter is 0.")

# Inserts
for op_tuple in OPERATIONS[:3]:
    kind, word, cols = op_tuple
    cells = [(r, c) for r, c in enumerate(cols)]

    # Show arrows
    save(f'{kind} "{word}" \u2192 arrows',
         op=op_tuple, phase="arrows", highlight_cells=cells, min_cell=None,
         caption=f'{kind} "{word}" \u2192 hash to columns {cols}')

    # Apply increment
    for r, c in enumerate(cols):
        grid[r][c] += 1

    # Show updated counters
    collision_note = ""
    if kind == "insert" and word == "y":
        collision_note = "  (h\u2081 collides with \"x\" at column 2)"
    save(f'{kind} "{word}" \u2192 incremented',
         op=op_tuple, phase="result", highlight_cells=cells, min_cell=None,
         caption=f'"{word}" counters incremented{collision_note}')

# Query "x"
q_op = OPERATIONS[3]
_, q_word, q_cols = q_op
q_cells = [(r, c) for r, c in enumerate(q_cols)]
vals = [grid[r][c] for r, c in q_cells]
min_val = min(vals)
min_idx = next(i for i, v in enumerate(vals) if v == min_val)
min_rc = q_cells[min_idx]

# Show arrows
save(f'query "{q_word}" \u2192 arrows',
     op=q_op, phase="arrows", highlight_cells=q_cells, min_cell=None,
     caption=f'query "{q_word}" \u2192 check columns {q_cols}')

# Show result with min highlighted
save(f'query "{q_word}" \u2192 result',
     op=q_op, phase="result", highlight_cells=q_cells, min_cell=min_rc,
     caption=f'query "{q_word}": counters = {vals}, min = {min_val} \u2192 estimate f\u0302("{q_word}") = {min_val}')

print(f"\nwrote {step} frames to {PREFIX}NN.png")
