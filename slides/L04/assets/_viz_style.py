"""Shared visual style for L04 data-structure diagrams.

What this file contains
-----------------------
One place to define the colour palette, matplotlib rcParams, and small
drawing primitives (cells, pointer arrows, annotation boxes) used across
all `gen_*.py` generators in this deck.

Why it exists
-------------
The L04 deck makes heavy use of memory-layout diagrams. Keeping one style
module means every figure uses identical colours, arrow heads, cell
rounding, and font conventions — so slides read as one visual language.

The palette is aligned with the T01 deck (`gen_adjlist_vs_csr_memory.py`,
`gen_aos_soa.py`) so the two decks do not look foreign next to each
other.

How to use
----------
    from _viz_style import (
        setup_mpl, CELL, PTR, ACCENT, FG,
        draw_cell, draw_pointer, draw_annotation,
    )

    setup_mpl()
    fig, ax = plt.subplots(figsize=(12, 3))
    draw_cell(ax, 0, 0, "42", CELL["data"])
    draw_pointer(ax, (1, 0.3), (3, 0.3))
    ax.axis("off")

When to change
--------------
Extend the palette here rather than redefining colours in a single
generator. If a new primitive is reused across more than one figure,
promote it into this module.
"""

from __future__ import annotations

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

matplotlib.use("Agg")

BG = "none"            # transparent — slides use a dark theme
FG = "#e0e0e0"         # default foreground (labels, axes, brackets)

# Cell fill colours by semantic role. Reuse these rather than picking new
# ones so the figures share a consistent vocabulary.
CELL = {
    "data":     "#3a6b8c",   # generic data cell (vector element, struct field)
    "index":    "#4ea8de",   # index / offset / size
    "pointer":  "#8e5ea2",   # heap-allocated node
    "hot":      "#e74c3c",   # accessed / hot field
    "cold":     "#3a3a5c",   # unused / cold slot
    "ok":       "#2ecc71",   # success / cache-friendly
    "warn":     "#f39c12",   # attention / pointer-chasing
    "control":  "#5a6680",   # control block (ptr/size/cap triple)
    "cache":    "#f5c97b",   # cache-line overlay (used translucent)
}

PTR = CELL["warn"]        # pointer arrows — always the warning colour
ACCENT = CELL["ok"]       # positive annotations
NEGATIVE = CELL["hot"]    # negative annotations

# Geometry — keep consistent across generators so cells line up visually.
CELL_W = 0.7
CELL_H = 0.55
CELL_GAP = 0.06


def setup_mpl() -> None:
    """Apply the shared rcParams. Call once before building a figure."""
    plt.rcParams.update({
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "text.color": FG,
        "font.family": "sans-serif",
    })


def draw_cell(
    ax,
    x: float,
    y: float,
    text: str | int,
    color: str,
    *,
    w: float = CELL_W,
    h: float = CELL_H,
    fontsize: int = 9,
    text_color: str = "white",
) -> None:
    """Draw one rounded memory cell with a monospace label."""
    rect = mpatches.FancyBboxPatch(
        (x, y), w - CELL_GAP, h,
        boxstyle="round,pad=0.04",
        facecolor=color, edgecolor=FG, linewidth=0.6,
    )
    ax.add_patch(rect)
    ax.text(
        x + (w - CELL_GAP) / 2, y + h / 2, str(text),
        ha="center", va="center",
        fontsize=fontsize, color=text_color,
        fontfamily="monospace", fontweight="bold",
    )


def draw_composite_cell(
    ax,
    x: float,
    y: float,
    segments: list,
    *,
    h: float = CELL_H,
    rounding: float = 0.12,
    border_color: str = FG,
    border_lw: float = 1.1,
) -> tuple[float, float]:
    """Draw N abutting flat sub-cells with one rounded outer boundary.

    ``segments`` is a list of dicts with keys ``w``, ``text``, ``color``,
    and optional ``fontsize`` (default 9) and ``text_color`` (default "white").
    The inner cells have sharp corners and no gaps; the outer rounded outline
    overdraws the shared edges, so the node reads as one unit.

    Returns ``(left_x, right_x)``.
    """
    cursor = x
    for seg in segments:
        w = seg["w"]
        rect = mpatches.Rectangle(
            (cursor, y), w, h,
            facecolor=seg["color"], edgecolor="none", linewidth=0,
        )
        ax.add_patch(rect)
        ax.text(
            cursor + w / 2, y + h / 2, str(seg["text"]),
            ha="center", va="center",
            fontsize=seg.get("fontsize", 9),
            color=seg.get("text_color", "white"),
            fontfamily="monospace", fontweight="bold",
        )
        cursor += w
    total_w = cursor - x
    outline = mpatches.FancyBboxPatch(
        (x, y), total_w, h,
        boxstyle=f"round,pad=0,rounding_size={rounding}",
        facecolor="none", edgecolor=border_color, linewidth=border_lw,
    )
    ax.add_patch(outline)
    return x, cursor


def draw_pointer(
    ax,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = PTR,
    lw: float = 1.3,
    style: str = "-|>",
    curve: float = 0.0,
) -> None:
    """Draw a pointer-style arrow. Positive `curve` bends it upward."""
    if curve == 0.0:
        connectionstyle = "arc3,rad=0"
    else:
        connectionstyle = f"arc3,rad={curve}"
    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops=dict(
            arrowstyle=style,
            color=color,
            lw=lw,
            connectionstyle=connectionstyle,
            shrinkA=2, shrinkB=2,
        ),
    )


def draw_routed_pointer(
    ax,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    clearance: float = 0.45,
    over: bool = True,
    color: str = PTR,
    lw: float = 1.3,
    style: str = "-|>",
) -> None:
    """Draw a 3-segment pointer (up/down, across, down/up) that skirts a box.

    Use when a straight arrow would cross through cells between `start` and
    `end`. `clearance` is how far above (or below, when ``over=False``) the
    higher of the two endpoints the horizontal leg runs.
    """
    x1, y1 = start
    x2, y2 = end
    if over:
        yh = max(y1, y2) + clearance
    else:
        yh = min(y1, y2) - clearance
    ax.plot([x1, x1], [y1, yh], color=color, lw=lw, solid_capstyle="round")
    ax.plot([x1, x2], [yh, yh], color=color, lw=lw, solid_capstyle="round")
    ax.annotate(
        "", xy=end, xytext=(x2, yh),
        arrowprops=dict(
            arrowstyle=style, color=color, lw=lw,
            shrinkA=0, shrinkB=2,
        ),
    )


def check_no_overlap(
    rects: list[tuple[float, float, float, float]],
    *,
    pad: float = 0.0,
    labels: list[str] | None = None,
) -> None:
    """Warn (print) when any two axis-aligned rects overlap.

    Each rect is ``(x, y, w, h)`` — same convention as ``draw_cell``. Pass an
    optional ``labels`` list of the same length to get readable messages.
    """
    import warnings

    def overlap(a, b):
        ax0, ay0, aw, ah = a
        bx0, by0, bw, bh = b
        return not (
            ax0 + aw + pad <= bx0 or bx0 + bw + pad <= ax0
            or ay0 + ah + pad <= by0 or by0 + bh + pad <= ay0
        )

    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            if overlap(rects[i], rects[j]):
                li = labels[i] if labels else f"#{i}"
                lj = labels[j] if labels else f"#{j}"
                warnings.warn(
                    f"box overlap: {li} {rects[i]} vs {lj} {rects[j]}",
                    stacklevel=2,
                )


def draw_annotation(
    ax,
    x: float,
    y: float,
    text: str,
    *,
    color: str = ACCENT,
    fontsize: int = 9,
    ha: str = "center",
    va: str = "center",
) -> None:
    """Draw a framed caption used for 'cache-friendly' / 'cache miss' labels."""
    ax.text(
        x, y, text,
        fontsize=fontsize, color=color, fontstyle="italic",
        ha=ha, va=va,
        bbox=dict(
            boxstyle="round,pad=0.3",
            facecolor=(0, 0, 0, 0.5),
            edgecolor=color,
            linewidth=0.8,
            alpha=0.9,
        ),
    )


def draw_cache_line(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    label: str | None = None,
) -> None:
    """Draw a translucent rectangle marking one cache line, optional label."""
    rect = mpatches.Rectangle(
        (x, y), w, h,
        facecolor="none",
        edgecolor=CELL["cache"], linewidth=1.4, linestyle=(0, (2, 2)),
        zorder=5,
    )
    ax.add_patch(rect)
    if label:
        ax.text(
            x + w / 2, y + h + 0.05, label,
            ha="center", va="bottom",
            fontsize=8, color=CELL["cache"], fontstyle="italic",
            fontweight="bold", zorder=5,
        )


def draw_bracket(
    ax,
    x1: float,
    x2: float,
    y: float,
    label: str,
    *,
    down: bool = True,
    color: str = FG,
) -> None:
    """Square bracket under (or over) a range of cells with a centered label."""
    tick = 0.07 if down else -0.07
    ax.plot(
        [x1, x1, x2, x2],
        [y + tick, y, y, y + tick],
        color=color, lw=0.8,
    )
    ax.text(
        (x1 + x2) / 2, y - 0.15 if down else y + 0.15,
        label, ha="center",
        va="top" if down else "bottom",
        fontsize=8, color=color, fontfamily="monospace",
    )


def save(fig, path: str, *, dpi: int = 200, tight: bool = True) -> None:
    """Save with the deck's standard parameters (transparent, no edge)."""
    kwargs = dict(dpi=dpi, transparent=True, edgecolor="none")
    if tight:
        kwargs["bbox_inches"] = "tight"
    fig.savefig(path, **kwargs)
    plt.close(fig)
    print(f"Saved {path}")
