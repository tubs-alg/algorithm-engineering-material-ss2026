"""Step-by-step Bloom filter walkthrough — one PNG per narrated step.

What this file contains
-----------------------
Emits bloom_filter_step_NN.png for a small Bloom filter (m = 16 bits,
k = 3 hashes): an empty state, three inserts (arrows → set-bits), and
three queries illustrating the three canonical outcomes — true
positive, definite miss, and a false positive caused by collisions.

The slide stacks them with `.r-stack` + `.fragment` so each click
advances one step that the speaker narrates.

Why it exists
-------------
A GIF makes the bits flip but gives the speaker no control. One frame
per click lets each outcome — especially the false positive — land on
its own beat.

How to use
----------
Run from the assets/ directory:

    python gen_bloom_filter_animation.py

When to change
--------------
The bit assignments are hand-picked so the three queries hit their
three cases (true positive, definite miss, false positive on "fox")
given the three inserts. Update the OPERATIONS list together if you
change the story.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from _viz_style import ACCENT, CELL, FG, NEGATIVE, setup_mpl

setup_mpl()

# Local overrides: the shared ok-green (#2ecc71) is so close to the shared
# ACCENT arrow colour that insert arrows vanish over set bits. Use a
# darker bit fill and brighter arrow colours for this figure only.
BIT_SET_FILL = "#1f6b3a"          # darker green for "1" cells
INSERT_ARROW_COLOR = "#7af09c"     # brighter green — stands out on BIT_SET_FILL
QUERY_ARROW_COLOR = "#7ecbff"      # brighter blue — stands out on BIT_SET_FILL

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PREFIX = os.path.join(OUT_DIR, "bloom_filter_step_")

# --- Geometry ----------------------------------------------------------------
M = 16
BIT_W = 0.6
BIT_H = 0.7
BIT_GAP = 0.08
BITS_Y = 2.2
BITS_X0 = 0.6

FIG_W = 13.0
FIG_H = 6.2

# --- Hand-picked hash outputs -------------------------------------------------
OPERATIONS = [
    ("insert", "cat",  [2, 7, 11]),
    ("insert", "dog",  [4, 7, 13]),
    ("insert", "fish", [1, 9, 14]),
    ("query",  "cat",  [2, 7, 11]),   # true positive
    ("query",  "owl",  [3, 9, 15]),   # definite miss (bits 3, 15 are 0)
    ("query",  "fox",  [2, 4, 13]),   # false positive
]


def bit_x(i: int) -> float:
    return BITS_X0 + i * BIT_W


def bit_center(i: int) -> tuple[float, float]:
    return bit_x(i) + (BIT_W - BIT_GAP) / 2, BITS_Y + BIT_H / 2


def render_step(path: str,
                bits_set: set[int],
                op: tuple | None,
                phase: str,
                verdict: str | None,
                caption: str) -> None:
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))

    ax.text(
        FIG_W / 2, 5.6,
        "Bloom filter  (m = 16 bits, k = 3 hashes)",
        ha="center", va="center",
        fontsize=15, color=FG, fontweight="bold",
    )

    highlight = set(op[2]) if op is not None else set()
    missing: set[int] = set()
    if phase == "result" and verdict == "no" and op is not None:
        missing = {b for b in op[2] if b not in bits_set}

    for i in range(M):
        x0 = bit_x(i)
        is_set = i in bits_set
        base_color = BIT_SET_FILL if is_set else CELL["cold"]
        edge = FG
        lw = 0.8

        if i in highlight:
            if phase == "result" and verdict == "false-positive":
                edge = CELL["warn"]
                lw = 2.4
            elif phase == "result" and verdict == "yes":
                edge = ACCENT
                lw = 2.4
            elif phase == "result" and verdict == "no":
                edge = NEGATIVE if i in missing else FG
                lw = 2.4 if i in missing else 1.2
            else:
                edge = "#ffffff"
                lw = 1.8

        rect = mpatches.FancyBboxPatch(
            (x0, BITS_Y), BIT_W - BIT_GAP, BIT_H,
            boxstyle="round,pad=0.02",
            facecolor=base_color, edgecolor=edge, linewidth=lw,
        )
        ax.add_patch(rect)
        ax.text(
            x0 + (BIT_W - BIT_GAP) / 2, BITS_Y + BIT_H / 2,
            "1" if is_set else "0",
            ha="center", va="center",
            fontsize=13, color="white" if is_set else "#888",
            fontfamily="monospace", fontweight="bold",
        )
        ax.text(
            x0 + (BIT_W - BIT_GAP) / 2, BITS_Y + BIT_H + 0.12, str(i),
            ha="center", va="bottom",
            fontsize=8, color="#9aa0ad", fontfamily="monospace",
        )

    if op is not None:
        kind, word, bits = op
        op_color = {"insert": INSERT_ARROW_COLOR,
                    "query":  QUERY_ARROW_COLOR}[kind]

        card_y = 4.4
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

        start = (card_x + card_w / 2, card_y - 0.38)
        for b in bits:
            end = bit_center(b)
            ax.annotate(
                "", xy=end, xytext=start,
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=op_color,
                    lw=1.2,
                    shrinkA=2, shrinkB=4,
                ),
            )

        if phase == "result" and verdict == "no":
            for b in missing:
                cx, cy = bit_center(b)
                r = 0.18
                ax.plot([cx - r, cx + r], [cy - r, cy + r],
                        color=NEGATIVE, lw=2.6, solid_capstyle="round", zorder=6)
                ax.plot([cx - r, cx + r], [cy + r, cy - r],
                        color=NEGATIVE, lw=2.6, solid_capstyle="round", zorder=6)

    caption_color = FG
    if verdict == "yes":
        caption_color = ACCENT
    elif verdict == "no":
        caption_color = NEGATIVE
    elif verdict == "false-positive":
        caption_color = CELL["warn"]

    ax.text(
        FIG_W / 2, 1.2, caption,
        ha="center", va="center",
        fontsize=15, color=caption_color, fontweight="bold",
    )

    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0.4, 6.0)
    ax.axis("off")

    # Transparent background + fixed figure size (no bbox_inches="tight")
    # so every frame has identical pixel dimensions. That is required for
    # .r-stack in the slide — tight crop varies per frame (arrows extend
    # differently), which made frames land at different positions.
    fig.savefig(path, dpi=140, transparent=True)
    plt.close(fig)


# --- Build the sequence ------------------------------------------------------

step = 0
bits_set: set[int] = set()


def save(label: str, **kwargs) -> None:
    global step
    path = f"{PREFIX}{step:02d}.png"
    render_step(path, **kwargs)
    print(f"  step {step:02d}  {label}")
    step += 1


save("empty",
     bits_set=set(), op=None, phase="idle", verdict=None,
     caption="Empty filter — every bit is 0.")

for op in OPERATIONS:
    kind, word, bits = op

    if kind == "insert":
        save(f'insert "{word}" → arrows',
             bits_set=set(bits_set), op=op, phase="arrows", verdict=None,
             caption=f'insert "{word}" → hash to bits {bits}')
        bits_set |= set(bits)
        save(f'insert "{word}" → set',
             bits_set=set(bits_set), op=op, phase="result", verdict="set",
             caption=f'"{word}" inserted — bits {bits} set to 1')
    else:
        save(f'query "{word}" → arrows',
             bits_set=set(bits_set), op=op, phase="arrows", verdict=None,
             caption=f'query "{word}" → check bits {bits}')
        if all(b in bits_set for b in bits):
            if word == "fox":
                verdict = "false-positive"
                cap = f'"{word}": all 3 bits are 1 → probably yes (false positive!)'
            else:
                verdict = "yes"
                cap = f'"{word}": all 3 bits are 1 → probably yes'
        else:
            verdict = "no"
            zeros = [b for b in bits if b not in bits_set]
            cap = f'"{word}": bit {zeros[0]} is 0 → definitely no'
        save(f'query "{word}" → verdict',
             bits_set=set(bits_set), op=op, phase="result", verdict=verdict,
             caption=cap)

print(f"\nwrote {step} frames to {PREFIX}NN.png")
