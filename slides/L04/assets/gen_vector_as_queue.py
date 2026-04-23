"""vector-as-queue walkthrough — one PNG per narrated step.

What this file contains
-----------------------
Emits vector_as_queue_step_00..step_NN.png with identical axes. Each
frame shows the *same single array* with head/tail markers in their
current positions, plus a running operation log on the right side.
The slide stacks them with `.r-stack` + `.fragment` and each click
applies one operation to the same vector.

Also emits vector_as_queue.png — a stacked view of all states in one
figure — for printed handouts / thumbnails.

Why it exists
-------------
Showing one array that mutates over clicks (rather than four separate
rows) lets the speaker narrate each push / pop and point at head and
tail as they move. Matches the grid and BVH animations in _08-spatial.

How to use
----------
Run from the assets/ directory:

    python gen_vector_as_queue.py

When to change
--------------
Edit OPS to change the narrated sequence. Every op is applied in order
to a capacity-N vector; the driver below records the snapshot after
each op and emits a frame per snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import matplotlib.pyplot as plt

from _viz_style import (
    CELL, CELL_GAP, CELL_H, CELL_W, FG,
    draw_cell, save, setup_mpl,
)

setup_mpl()

N = 10
FIG_WIDTH = 13.0
FIG_HEIGHT = 4.2
ARRAY_X0 = 1.4          # left edge of first cell
LOG_X = ARRAY_X0 + N * CELL_W + 1.0
LOG_MAX_LINES = 9       # keep the panel compact; older lines scroll off


# Each op is ("push", value) or ("pop", None) or ("compact", None).
# The driver below turns this into frames with head/tail/values snapshots.
OPS: list[tuple[str, object]] = [
    # initial empty frame is implicit (step_00)
    ("push", 3),
    ("push", 1),
    ("push", 4),
    ("push", 1),
    ("push", 5),
    ("push", 9),
    ("pop", None),
    ("pop", None),
    ("pop", None),
    ("push", 2),
    ("push", 6),
    ("pop", None),
    ("pop", None),
    ("pop", None),
    ("push", 5),
    ("push", 3),   # vector now full
    ("compact", None),
]


@dataclass
class Frame:
    head: int
    tail: int
    values: list  # length N; None for empty slots
    log: list[str] = field(default_factory=list)
    highlight: str = ""   # one of "", "push", "pop", "compact", "full"
    note: str = ""        # short caption shown under the array


def build_frames() -> list[Frame]:
    """Apply OPS in order, returning one Frame per step (including the
    initial empty state)."""
    values: list = [None] * N
    head = 0
    tail = 0
    log: list[str] = []
    frames = [Frame(head, tail, list(values), [], "", "fresh vector, capacity " + str(N))]

    for kind, arg in OPS:
        note = ""
        if kind == "push":
            if tail >= N:
                # Should not happen in this scripted sequence; the script
                # triggers compact before overflowing.
                raise RuntimeError("push past capacity without compacting")
            values[tail] = arg
            tail += 1
            log.append(f"push({arg})")
            note = f"push({arg}) → tail advances"
            if tail == N:
                note = f"push({arg}) → vector full ⚠"
                highlight = "full"
            else:
                highlight = "push"
        elif kind == "pop":
            popped = values[head]
            # Leave the husk visible — we don't clear the slot.
            head += 1
            log.append(f"pop() → {popped}")
            note = f"pop() → {popped}; head advances, husk stays"
            highlight = "pop"
        elif kind == "compact":
            live = [v for v in values[head:tail]]
            values = live + [None] * (N - len(live))
            tail = len(live)
            head = 0
            log.append("compact()")
            note = "compact: move live window to index 0, reset head"
            highlight = "compact"
        else:
            raise ValueError(kind)

        frames.append(
            Frame(head, tail, list(values), list(log), highlight, note)
        )
    return frames


def draw_array(ax, frame: Frame):
    head, tail, values = frame.head, frame.tail, frame.values

    for i in range(N):
        v = values[i]
        if i < head:
            color = CELL["cold"]
            text_color = "#888"
            text = str(v) if v is not None else "·"
        elif i < tail:
            # Highlight the newly-pushed cell on a push frame.
            is_new_push = (
                frame.highlight in ("push", "full")
                and i == tail - 1
            )
            color = CELL["ok"] if is_new_push else CELL["data"]
            text_color = "white"
            text = str(v) if v is not None else "·"
        else:
            color = "#1a1a2e"
            text_color = "#555"
            text = "·"
        draw_cell(ax, ARRAY_X0 + i * CELL_W, 1.6, text, color, text_color=text_color)

    # Index ruler below the cells, so viewers can read positions.
    for i in range(N):
        cx = ARRAY_X0 + i * CELL_W + (CELL_W - CELL_GAP) / 2
        ax.text(
            cx, 1.6 - 0.22, str(i),
            ha="center", va="top", color="#666",
            fontsize=7, fontfamily="monospace",
        )

    # head / tail markers as small triangles above the cells.
    def marker(idx, label, color):
        cx = ARRAY_X0 + idx * CELL_W + (CELL_W - CELL_GAP) / 2
        ax.annotate(
            label, xy=(cx, 1.6 + CELL_H + 0.02),
            xytext=(cx, 1.6 + CELL_H + 0.4),
            ha="center", va="bottom", color=color,
            fontsize=9, fontfamily="monospace", fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1),
        )

    marker(head, "head", CELL["warn"])
    tail_idx = min(tail, N - 1) if tail >= N else tail
    # For the "tail past the end" case, draw the tail marker just past
    # the last cell so it still reads as a half-open upper bound.
    if tail >= N:
        cx = ARRAY_X0 + N * CELL_W + 0.05
        ax.annotate(
            "tail", xy=(cx, 1.6 + CELL_H + 0.02),
            xytext=(cx, 1.6 + CELL_H + 0.4),
            ha="center", va="bottom", color=CELL["ok"],
            fontsize=9, fontfamily="monospace", fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color=CELL["ok"], lw=1.1),
        )
    else:
        marker(tail, "tail", CELL["ok"])

    # Note line under the array.
    if frame.note:
        ax.text(
            ARRAY_X0, 1.6 - 0.7, frame.note,
            ha="left", va="top",
            color=FG, fontsize=10, fontstyle="italic",
        )


def draw_log(ax, frame: Frame):
    ax.text(
        LOG_X, 1.6 + CELL_H + 0.42, "ops",
        ha="left", va="bottom", color=FG,
        fontsize=10, fontweight="bold", fontfamily="monospace",
    )
    lines = frame.log[-LOG_MAX_LINES:]
    # Draw older lines faded, newest line highlighted.
    for k, line in enumerate(lines):
        y = 1.6 + CELL_H + 0.15 - k * 0.25
        is_newest = (k == len(lines) - 1)
        if is_newest:
            if frame.highlight == "push":
                color = CELL["ok"]
            elif frame.highlight == "pop":
                color = CELL["warn"]
            elif frame.highlight == "compact":
                color = CELL["hot"]
            elif frame.highlight == "full":
                color = CELL["hot"]
            else:
                color = FG
            weight = "bold"
        else:
            color = "#777"
            weight = "normal"
        ax.text(
            LOG_X, y, line,
            ha="left", va="top",
            color=color, fontsize=9,
            fontfamily="monospace", fontweight=weight,
        )


def render_frame(frame: Frame):
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
    ax.set_title(
        "vector-as-queue — push to the back, advance a read index",
        fontsize=12, fontweight="bold", color=FG, loc="left", pad=8,
    )
    draw_array(ax, frame)
    draw_log(ax, frame)
    ax.set_xlim(0, LOG_X + 4.5)
    ax.set_ylim(0, 3.4)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    return fig


def main() -> None:
    frames = build_frames()
    for i, frame in enumerate(frames):
        fig = render_frame(frame)
        save(fig, f"vector_as_queue_step_{i:02d}.png")
        plt.close(fig)

    # Combined summary figure — the key inflection points stacked.
    key_indices = [0, 6, 9, 16, 17]  # start, full push, first compact-ready, full, compacted
    key_indices = [i for i in key_indices if i < len(frames)]
    ROW_H = 1.3
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, ROW_H * len(key_indices) + 0.8))
    ax.set_title(
        "vector-as-queue — key states",
        fontsize=12, fontweight="bold", color=FG, loc="left", pad=8,
    )
    for row, idx in enumerate(key_indices):
        f = frames[idx]
        y = (len(key_indices) - 1 - row) * ROW_H
        for i in range(N):
            v = f.values[i]
            if i < f.head:
                color, tc, txt = CELL["cold"], "#888", str(v) if v is not None else "·"
            elif i < f.tail:
                color, tc, txt = CELL["data"], "white", str(v) if v is not None else "·"
            else:
                color, tc, txt = "#1a1a2e", "#555", "·"
            draw_cell(ax, ARRAY_X0 + i * CELL_W, y, txt, color, text_color=tc)
        ax.text(
            0.8, y + CELL_H / 2, f"t{row}",
            ha="right", va="center", color=FG,
            fontfamily="monospace", fontsize=10, fontweight="bold",
        )
        ax.text(
            ARRAY_X0 + N * CELL_W + 0.4, y + CELL_H / 2, f.note,
            ha="left", va="center", color=FG,
            fontsize=9, fontstyle="italic",
        )
    ax.set_xlim(0, FIG_WIDTH)
    ax.set_ylim(-0.3, len(key_indices) * ROW_H + 0.3)
    ax.axis("off")
    plt.tight_layout()
    save(fig, "vector_as_queue.png")
    plt.close(fig)

    print(f"{len(frames)} frames emitted.")


if __name__ == "__main__":
    main()
