"""Shared helper for heap-tree figures.

What this file contains
-----------------------
Two functions:
  - :func:`draw_heap_tree` draws a complete binary tree into a given
    matplotlib Axes, shading each node by its depth and optionally
    highlighting a specific array index (the node that is "moving"
    in a push or pop animation).
  - :func:`draw_heap_array` draws the same keys as a flat row of
    cells (the array backing), using the identical depth palette.
    Used under :func:`draw_heap_tree` so each slide shows the tree
    and its array in lock-step.

Why it exists
-------------
``gen_heap_push.py`` and ``gen_heap_pop.py`` both need to draw a
sequence of heap snapshots side by side. Centralising the tree-drawing
code keeps the two figures visually consistent and the generator
scripts short.

How to use
----------
    draw_heap_tree(ax, keys=[2, 5, 3, 9, 7, 4, 8], highlight=[3])

When to change
--------------
If the generator adds a d-ary variant, extend this helper to take a
``d`` parameter rather than forking a second module.
"""

from __future__ import annotations

import matplotlib.patches as mpatches

from _viz_style import CELL, CELL_GAP, CELL_H, CELL_W, FG

# Depth palette — distinct hues per level so successive depths are
# unambiguous at projection distance. Chosen to stay clear of the
# status colours (orange CELL["warn"], pale-yellow CELL["cache"],
# red CELL["hot"]) so highlights and cache-line overlays still pop.
DEPTH_COLORS = [
    "#234e8a",  # depth 0 — deep blue (root)
    "#1f8a5e",  # depth 1 — emerald
    "#8b4a9a",  # depth 2 — royal purple
    "#bf7c36",  # depth 3 — ochre (rarely hit; 5-level binary heap only)
]

HIGHLIGHT_EDGE = CELL["warn"]   # orange ring around the moving node
SWAP_EDGE = CELL["hot"]         # red edge for the swap being performed


def depth_of(i: int) -> int:
    d = 0
    n = i + 1
    while n >> 1:
        d += 1
        n >>= 1
    return d


def draw_heap_tree(
    ax,
    keys,
    *,
    highlight: list[int] | None = None,
    swap_edge: tuple[int, int] | None = None,
    title: str | None = None,
    x_span: tuple[float, float] = (0.0, 1.0),
    y_top: float = 0.92,
    level_height: float = 0.22,
    cell_w: float = 0.14,
    cell_h: float = 0.14,
    font_size: int = 10,
):
    """Draw a binary heap (array ``keys``) as a tree inside ``ax``.

    Parameters
    ----------
    highlight
        Array indices to draw with an extra orange outline.
    swap_edge
        Optional ``(parent_idx, child_idx)`` pair; the edge between
        those two nodes is drawn in red to mark the swap that is
        about to happen (or just happened).
    title
        Short caption printed above the tree.
    x_span, y_top, level_height
        Placement inside the Axes coordinate space. The helper draws
        in data coordinates and expects the caller to set xlim/ylim.
    """
    highlight = highlight or []
    n = len(keys)
    levels = depth_of(n - 1) + 1 if n > 0 else 0

    left, right = x_span

    def pos(i: int) -> tuple[float, float]:
        level = depth_of(i)
        idx_in_level = i - ((1 << level) - 1)
        count_in_level = 1 << level
        if count_in_level == 1:
            x = (left + right) / 2
        else:
            x = left + (right - left) * (idx_in_level + 0.5) / count_in_level
        y = y_top - level * level_height
        return x, y

    # Parent-child edges first, so nodes overdraw them cleanly.
    # ``None`` entries represent empty slots; their nodes and edges
    # are skipped so the viewer sees only the real tree shape.
    for i in range(n):
        if keys[i] is None:
            continue
        for child in (2 * i + 1, 2 * i + 2):
            if child >= n or keys[child] is None:
                continue
            xp, yp = pos(i)
            xc, yc = pos(child)
            is_swap = swap_edge is not None and (i, child) == swap_edge
            ax.plot(
                [xp, xc],
                [yp - cell_h / 2, yc + cell_h / 2],
                color=SWAP_EDGE if is_swap else FG,
                lw=2.2 if is_swap else 0.9,
                solid_capstyle="round",
                zorder=1,
            )

    # Nodes.
    for i, k in enumerate(keys):
        if k is None:
            continue
        x, y = pos(i)
        color = DEPTH_COLORS[min(depth_of(i), len(DEPTH_COLORS) - 1)]
        rect = mpatches.FancyBboxPatch(
            (x - cell_w / 2, y - cell_h / 2),
            cell_w, cell_h,
            boxstyle="round,pad=0.005",
            facecolor=color, edgecolor=FG, linewidth=0.6,
            zorder=2,
        )
        ax.add_patch(rect)
        ax.text(
            x, y, str(k),
            ha="center", va="center",
            fontsize=font_size, color="white",
            fontfamily="monospace", fontweight="bold",
            zorder=3,
        )
        if i in highlight:
            ring = mpatches.FancyBboxPatch(
                (x - cell_w / 2 - 0.01,
                 y - cell_h / 2 - 0.01),
                cell_w + 0.02, cell_h + 0.02,
                boxstyle="round,pad=0.005",
                facecolor="none", edgecolor=HIGHLIGHT_EDGE, linewidth=2.0,
                zorder=4,
            )
            ax.add_patch(ring)

    if title is not None:
        ax.text(
            (left + right) / 2,
            y_top + cell_h / 2 + 0.06,
            title,
            ha="center", va="bottom",
            fontsize=10, color=FG, fontstyle="italic",
        )

    ax.axis("off")


def draw_heap_array(
    ax,
    keys,
    *,
    highlight: list[int] | None = None,
    y: float = 0.5,
    x_span: tuple[float, float] = (0.05, 0.95),
    cell_h: float = 0.35,
    font_size: int = 12,
    show_indices: bool = True,
    label: str | None = "heap[]",
    depth_fn=None,
):
    """Draw the flat-array view of a heap inside ``ax``.

    Cells are shaded by depth using the same palette as
    :func:`draw_heap_tree`, and ``highlight`` indices get the same
    orange ring. The caller sets xlim/ylim.

    ``depth_fn`` lets a d-ary generator pass in its own
    ``index -> depth`` mapping so the array colouring matches the
    tree it sits beneath. Defaults to binary-heap depth.
    """
    depth_for = depth_fn if depth_fn is not None else depth_of
    highlight = highlight or []
    n = len(keys)
    if n == 0:
        return

    left, right = x_span
    total_w = right - left
    cell_w = total_w / n

    for i, k in enumerate(keys):
        x = left + i * cell_w
        if k is None:
            # Empty slot — dashed outline, no fill.
            rect = mpatches.Rectangle(
                (x + cell_w * 0.05, y - cell_h / 2),
                cell_w * 0.9, cell_h,
                facecolor="none", edgecolor=FG, linewidth=0.6,
                linestyle=(0, (3, 2)),
                zorder=2,
            )
            ax.add_patch(rect)
        else:
            color = DEPTH_COLORS[min(depth_for(i), len(DEPTH_COLORS) - 1)]
            rect = mpatches.Rectangle(
                (x + cell_w * 0.05, y - cell_h / 2),
                cell_w * 0.9, cell_h,
                facecolor=color, edgecolor=FG, linewidth=0.6,
                zorder=2,
            )
            ax.add_patch(rect)
            ax.text(
                x + cell_w / 2, y, str(k),
                ha="center", va="center",
                fontsize=font_size, color="white",
                fontfamily="monospace", fontweight="bold",
                zorder=3,
            )
        if show_indices:
            ax.text(
                x + cell_w / 2, y - cell_h / 2 - 0.04,
                str(i),
                ha="center", va="top",
                fontsize=8, color=FG, fontfamily="monospace",
            )
        if i in highlight:
            ring = mpatches.Rectangle(
                (x + cell_w * 0.05 - 0.006, y - cell_h / 2 - 0.006),
                cell_w * 0.9 + 0.012, cell_h + 0.012,
                facecolor="none", edgecolor=HIGHLIGHT_EDGE, linewidth=2.0,
                zorder=4,
            )
            ax.add_patch(ring)

    if label is not None:
        ax.text(
            left - 0.015, y,
            label,
            ha="right", va="center",
            fontsize=10, color=FG,
            fontfamily="monospace", fontweight="bold",
        )
