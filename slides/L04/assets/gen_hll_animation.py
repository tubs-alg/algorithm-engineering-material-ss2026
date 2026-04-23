"""Step-by-step HyperLogLog walkthrough — one PNG per narrated step.

What this file contains
-----------------------
Emits hll_step_NN.png for a small HyperLogLog (m=8 registers, so
p=3 bits for the bucket index): an empty register array, then three
item insertions showing hash → bucket selection → leading-zero count
→ register max-update, and a final state.

The slide stacks them with `.r-stack` + `.fragment` so each click
advances one step that the speaker narrates.

How to use
----------
Run from the assets/ directory:

    python gen_hll_animation.py
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import ACCENT, CELL, FG, NEGATIVE, setup_mpl

setup_mpl()

# Colours
REG_FILL = CELL["data"]
REG_EMPTY = CELL["cold"]
REG_HOT = ACCENT              # register being updated
HASH_COLOR = "#7ecbff"        # blue for hash bits
BUCKET_COLOR = "#f39c12"      # orange for bucket-index bits
ZEROS_COLOR = CELL["hot"]     # red for leading-zero count

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PREFIX = os.path.join(OUT_DIR, "hll_step_")

# --- Geometry ----------------------------------------------------------------
M = 8          # registers (p = 3 bits)
P = 3
REG_W = 1.0
REG_H = 0.7
REG_GAP = 0.08
REG_X0 = 2.5
REG_Y = 1.4

FIG_W = 13.0
FIG_H = 6.8

CHAR_W = 0.22  # width per monospace character in the hash display

# --- Hand-picked hash values (16-bit for illustration) ----------------------
# Convention: rho = number of leading zeros + 1 = position of first 1-bit.
# The remaining bits must be consistent: first (rho-1) bits are 0, then a 1.
#
# Format: (item_name, bucket_bits_str, bucket_idx, remaining_bits_str, rho)
# Names are equal length so the prefix "hash("xxx") = " has constant width
# and frames don't shift horizontally in the .r-stack.
ITEMS = [
    ("cat",    "010", 2, "0001001101010", 4),   # 3 leading zeros, first 1 at pos 4
    ("dog",    "101", 5, "1010001110010", 1),   # 0 leading zeros, first 1 at pos 1
    ("fox",    "010", 2, "0000001011001", 7),   # 6 leading zeros, first 1 at pos 7
]


def reg_xy(i: int) -> tuple[float, float]:
    return REG_X0 + i * REG_W, REG_Y


def reg_center(i: int) -> tuple[float, float]:
    x, y = reg_xy(i)
    return x + (REG_W - REG_GAP) / 2, y + REG_H / 2


def render_step(
    path: str,
    registers: list[int],
    item: tuple | None,
    phase: str,
    active_reg: int | None,
    caption: str,
    show_formula: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))

    # Title
    ax.text(
        FIG_W / 2, 6.3,
        "HyperLogLog  (m = 8 registers, p = 3 bucket bits)",
        ha="center", va="center",
        fontsize=15, color=FG, fontweight="bold",
    )

    # Draw register array
    for i in range(M):
        x, y = reg_xy(i)
        val = registers[i]

        if active_reg is not None and i == active_reg:
            fill = REG_HOT
            edge = "#ffffff"
            lw = 2.0
        elif val > 0:
            fill = REG_FILL
            edge = FG
            lw = 0.8
        else:
            fill = REG_EMPTY
            edge = FG
            lw = 0.8

        rect = mpatches.FancyBboxPatch(
            (x, y), REG_W - REG_GAP, REG_H,
            boxstyle="round,pad=0.02",
            facecolor=fill, edgecolor=edge, linewidth=lw,
        )
        ax.add_patch(rect)
        ax.text(
            x + (REG_W - REG_GAP) / 2, y + REG_H / 2,
            str(val),
            ha="center", va="center",
            fontsize=14, color="white" if val > 0 else "#888",
            fontfamily="monospace", fontweight="bold",
        )
        # Register index below
        ax.text(
            x + (REG_W - REG_GAP) / 2, y - 0.15,
            f"R[{i}]",
            ha="center", va="top",
            fontsize=8, color="#9aa0ad", fontfamily="monospace",
        )

    # Hash breakdown display — single centered line, no card/arrow clutter
    if item is not None and phase in ("hash", "result"):
        name, bucket_str, bucket, remaining, rho = item
        zero_count = rho - 1  # number of leading zeros
        remaining_clean = remaining.replace(" ", "")

        # --- Top line: hash("name") = [bucket bits] [remaining bits] ---
        top_y = 5.3

        # Prefix: hash("name") =
        prefix = f'hash("{name}") = '
        # Measure prefix width roughly (mix of normal and monospace chars)
        prefix_w = len(prefix) * 0.135

        # Center the whole line in the figure
        n_remaining = len(remaining_clean)
        n_bucket = len(bucket_str)
        bits_total_w = (n_bucket + n_remaining) * CHAR_W + 0.30  # + gap
        total_w = prefix_w + bits_total_w
        line_x0 = (FIG_W - total_w) / 2

        # Draw prefix
        ax.text(
            line_x0, top_y, prefix,
            ha="left", va="center",
            fontsize=13, color=FG, fontfamily="monospace",
        )

        # Bucket bits in orange
        bucket_x0 = line_x0 + prefix_w
        ax.text(
            bucket_x0, top_y, bucket_str,
            ha="left", va="center",
            fontsize=16, color=BUCKET_COLOR, fontfamily="monospace",
            fontweight="bold",
        )
        bucket_x1 = bucket_x0 + n_bucket * CHAR_W

        # Gap between bucket and remaining
        gap = 0.30
        remaining_x0 = bucket_x1 + gap

        # Remaining bits as one string — colour split via two overlapping texts
        # Draw leading zeros in red, rest in blue, no gap between them.
        remaining_all = remaining_clean
        ax.text(
            remaining_x0, top_y, remaining_all,
            ha="left", va="center",
            fontsize=16, color=HASH_COLOR, fontfamily="monospace",
            fontweight="bold",
        )
        # Overdraw leading zeros in red on top
        if zero_count > 0:
            zeros_str = remaining_clean[:zero_count]
            ax.text(
                remaining_x0, top_y, zeros_str,
                ha="left", va="center",
                fontsize=16, color=ZEROS_COLOR, fontfamily="monospace",
                fontweight="bold",
            )

        # --- Bracket annotations below the bit groups ---
        bracket_y = top_y - 0.35
        label_y = top_y - 0.60
        tick = 0.08

        # Bucket bracket + label
        bk_l = bucket_x0
        bk_r = bucket_x1
        ax.plot([bk_l, bk_l, bk_r, bk_r],
                [bracket_y + tick, bracket_y, bracket_y, bracket_y + tick],
                color=BUCKET_COLOR, lw=1.0)
        ax.text(
            (bk_l + bk_r) / 2, label_y,
            f"bucket = {bucket}",
            ha="center", va="top",
            fontsize=10, color=BUCKET_COLOR, fontstyle="italic",
        )

        # Remaining bracket — spans ALL remaining bits (red + blue)
        rem_l = remaining_x0
        rem_r = remaining_x0 + n_remaining * CHAR_W
        ax.plot([rem_l, rem_l, rem_r, rem_r],
                [bracket_y + tick, bracket_y, bracket_y, bracket_y + tick],
                color=ZEROS_COLOR, lw=1.0)
        ax.text(
            (rem_l + rem_r) / 2, label_y,
            f"\u03c1 = {rho}  (pos. of first 1-bit)",
            ha="center", va="top",
            fontsize=10, color=ZEROS_COLOR, fontstyle="italic",
        )

        # --- Arrow from annotation area down to the target register ---
        if phase == "result":
            target_cx, _ = reg_center(bucket)
            arrow_top = label_y - 0.35
            arrow_bot = REG_Y + REG_H
            ax.annotate(
                "", xy=(target_cx, arrow_bot), xytext=(target_cx, arrow_top),
                arrowprops=dict(
                    arrowstyle="-|>", color=REG_HOT, lw=1.5,
                    shrinkA=2, shrinkB=4,
                ),
            )

    # --- Right-side panel: formula + running estimate (always visible) ---
    panel_x = 11.0  # center of the right panel
    formula_y = 4.2

    # Formula (static, every frame)
    ax.text(
        panel_x, formula_y,
        r"$E = \frac{\alpha_m \cdot m^2}{\sum 2^{-R[j]}}$",
        ha="center", va="center",
        fontsize=16, color="#9aa0ad",
    )

    # Compute current estimate
    alpha_m = 0.7213 / (1 + 1.079 / M)
    Z = sum(2.0 ** (-v) for v in registers)
    estimate = alpha_m * M * M / Z
    n_nonzero = sum(1 for v in registers if v > 0)

    # Show estimate below formula
    if n_nonzero == 0:
        est_text = "E = ?"
        est_color = "#9aa0ad"
    else:
        est_text = f"E \u2248 {estimate:.1f}"
        est_color = ACCENT

    ax.text(
        panel_x, formula_y - 0.65,
        est_text,
        ha="center", va="center",
        fontsize=15, color=est_color, fontfamily="monospace",
        fontweight="bold",
    )

    # On the final frame, also show the true count for comparison
    if show_formula:
        ax.text(
            panel_x, formula_y - 1.10,
            f"(true: 3)",
            ha="center", va="center",
            fontsize=11, color="#9aa0ad", fontfamily="monospace",
        )

    # Caption
    ax.text(
        FIG_W / 2, 0.5, caption,
        ha="center", va="center",
        fontsize=14, color=FG, fontweight="bold",
    )

    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0.0, 6.8)
    ax.axis("off")

    fig.savefig(path, dpi=140, transparent=True)
    plt.close(fig)


# --- Build the sequence ------------------------------------------------------

step_num = 0
registers = [0] * M


def save(label: str, **kwargs) -> None:
    global step_num
    path = f"{PREFIX}{step_num:02d}.png"
    render_step(path, registers=list(registers), **kwargs)
    print(f"  step {step_num:02d}  {label}")
    step_num += 1


# Step 0: empty
save("empty",
     item=None, phase="idle", active_reg=None,
     caption="Empty HLL \u2014 every register is 0.")

# Process each item
for item_tuple in ITEMS:
    name, bucket_str, bucket, remaining, rho = item_tuple

    # Show hash breakdown
    save(f'hash "{name}"',
         item=item_tuple, phase="hash", active_reg=None,
         caption=f'hash("{name}") \u2192 bucket {bucket}, \u03c1 = {rho}')

    # Apply update: R[bucket] = max(R[bucket], rho)
    old_val = registers[bucket]
    registers[bucket] = max(registers[bucket], rho)
    updated = registers[bucket] != old_val

    if updated:
        cap = f'R[{bucket}] = max({old_val}, {rho}) = {registers[bucket]} \u2192 updated'
    else:
        cap = f'R[{bucket}] = max({old_val}, {rho}) = {old_val} \u2192 unchanged'

    save(f'update R[{bucket}]',
         item=item_tuple, phase="result", active_reg=bucket,
         caption=cap)

# Final state
save("final state",
     item=None, phase="idle", active_reg=None,
     show_formula=True,
     caption="With only 8 registers, the estimate is rough \u2014 production uses 2\u00b9\u2074 = 16 384.")

print(f"\nwrote {step_num} frames to {PREFIX}NN.png")
