"""Generate VRP family illustrations.

Each figure is hand-crafted, illustrative — *not* a solver output.
Mirrors the conventions used in sections/jsp/_make_figs.py.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Ellipse
from matplotlib.lines import Line2D
from pathlib import Path
from PIL import Image

import _dark_style

OUT = Path(__file__).parent

# Every single-figure "banner" slide shows its image at width=100% (see
# _03-vrp.qmd) — full-bleed reads cleaner than a centred 70% block. For the
# top-of-slide band to have the SAME height on every slide AND for the content
# to actually fill the width, each figure is *designed* wide (content aspect ≳
# BANNER_ASPECT) and then padded to exactly BANNER_ASPECT. When content is
# already ≥ target we add only top/bottom margin (invisible, content still spans
# full width); a figure that needs left/right padding is too narrow and should
# be redesigned wider — pad_to_banner_aspect() warns when that happens.
BANNER_ASPECT = 3.6  # width : height; at width 100% of a 1600px slide -> ~444px tall
BANNER_FIGURES = [
    "vrp_01-core-vrp", "vrp_02-capacity", "vrp_03-pickup-delivery",
    "vrp_04-time-windows", "vrp_05-shifts", "vrp_06-breaks",
    "vrp_07-multi-depot", "vrp_08-profiles", "vrp_09-reloading",
    "vrp_10-prizes",
]
# Per-figure aspect overrides for dense figures that need a taller band.
# Reloading carries four panels, so it gets ~25% more height (3.6 / 1.25).
BANNER_ASPECT_OVERRIDES = {
    "vrp_09-reloading": 2.88,
}


def pad_to_banner_aspect(name, target=BANNER_ASPECT):
    """Pad a saved PNG with transparent margins so its aspect == target.

    Returns the natural (pre-pad) aspect and a flag for side-padding, so the
    caller can flag figures that are still too narrow to fill the width.
    """
    path = OUT / f"{name}.png"
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    natural = w / h
    too_narrow = natural < target
    if too_narrow:              # add left/right padding -> content won't fill width
        new_w, new_h = int(round(h * target)), h
        off = ((new_w - w) // 2, 0)
    else:                        # add top/bottom padding -> content still full-width
        new_w, new_h = w, int(round(w / target))
        off = (0, (new_h - h) // 2)
    canvas = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    canvas.paste(im, off, im)
    canvas.save(path)
    return natural, too_narrow
# Consistent palette
PALETTE = [
    "#4C78A8",  # 0 blue (route A / van / trip 1)
    "#F58518",  # 1 orange (route B / truck / trip 2)
    "#54A24B",  # 2 green (good / feasible)
    "#E45756",  # 3 red (infeasible / forbidden)
    "#72B7B2",  # 4 teal
    "#EECA3B",  # 5 yellow
    "#B279A2",  # 6 purple (groups)
    "#9D755D",  # 7 brown
]

_dark_style.apply()
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def draw_depot(ax, x, y, size=0.6, label=None, color="#dddddd", fontsize=9):
    ax.add_patch(Rectangle((x - size / 2, y - size / 2), size, size,
                           facecolor=color, edgecolor="#888888", linewidth=1.0,
                           zorder=5))
    if label:
        ax.text(x, y - size / 2 - 0.25, label, ha="center", va="top",
                fontsize=fontsize, color=color)


def draw_client(ax, x, y, r=0.28, facecolor="white", edgecolor="#888888",
                label=None, label_color="#222222", fontsize=9, ls="-"):
    ax.add_patch(plt.Circle((x, y), r, facecolor=facecolor, edgecolor=edgecolor,
                            linewidth=1.2, linestyle=ls, zorder=4))
    if label is not None:
        ax.text(x, y, str(label), ha="center", va="center",
                fontsize=fontsize, color=label_color, zorder=6)


def draw_route(ax, coords, color, lw=2.0, ls="-", alpha=1.0):
    """Draw arrows between consecutive coords, slightly shortened to avoid
    overlapping with the node markers."""
    for (x1, y1), (x2, y2) in zip(coords[:-1], coords[1:]):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                            shrinkA=10, shrinkB=12, linestyle=ls, alpha=alpha),
            zorder=3,
        )


def square_axes(ax, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


# ---------------------------------------------------------------------------
# 1) Core VRP — one depot, two routes
# ---------------------------------------------------------------------------
def fig_core_vrp():
    # Wide flat layout: central depot, a left lobe and a right lobe spread far
    # apart so the content fills a full-width (100%) banner.
    fig, ax = plt.subplots(figsize=(15, 4))
    depot = (11.5, 2.9)
    A = [(3.0, 4.6), (1.0, 2.9), (3.0, 1.2)]
    B = [(20.0, 4.7), (22.5, 3.1), (20.5, 1.1), (15.5, 0.9)]
    draw_route(ax, [depot] + A + [depot], PALETTE[0])
    draw_route(ax, [depot] + B + [depot], PALETTE[1])
    draw_depot(ax, *depot, label="Depot")
    for x, y in A + B:
        draw_client(ax, x, y)
    legend = [
        Line2D([0], [0], color=PALETTE[0], lw=2.0, label="Route A"),
        Line2D([0], [0], color=PALETTE[1], lw=2.0, label="Route B"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#dddddd",
               markersize=9, label="Depot"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
               markeredgecolor="#888888", markersize=10, label="Client"),
    ]
    ax.legend(handles=legend, loc="lower center", ncol=4,
              bbox_to_anchor=(0.5, -0.04), frameon=False, fontsize=9)
    ax.set_title("Core VRP — one depot, several clients, two routes")
    square_axes(ax, (-1.0, 24.0), (0.0, 5.8))
    fig.savefig(OUT / "vrp_01-core-vrp.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2) Capacity — infeasible single route vs feasible split
# ---------------------------------------------------------------------------
def fig_capacity():
    fig, axes = plt.subplots(1, 2, figsize=(16, 4.2),
                             gridspec_kw={"wspace": 0.04})
    depot = (6.0, 3.9)
    clients = [
        (1.5, 5.8, 5),
        (5.0, 6.6, 4),
        (9.0, 6.0, 3),
        (10.8, 3.8, 6),
        (8.0, 1.8, 4),
        (2.3, 2.0, 6),
    ]

    # Left: single overcapacity route
    ax = axes[0]
    pts = [(x, y) for x, y, _ in clients]
    draw_route(ax, [depot] + pts + [depot], PALETTE[3])
    draw_depot(ax, *depot)
    for x, y, q in clients:
        draw_client(ax, x, y, r=0.34, facecolor="#fde2e2",
                    edgecolor=PALETTE[3], label=q, fontsize=9)
    ax.set_title("Q = 20 — single route overloaded (Σ q = 28)",
                 color=PALETTE[3])
    square_axes(ax, (0, 13.0), (1.3, 7.0))

    # Right: two feasible routes
    ax = axes[1]
    A = clients[:3]  # 5 + 4 + 3 = 12
    B = clients[3:]  # 6 + 4 + 6 = 16
    draw_route(ax, [depot] + [(x, y) for x, y, _ in A] + [depot], PALETTE[0])
    draw_route(ax, [depot] + [(x, y) for x, y, _ in B] + [depot], PALETTE[1])
    draw_depot(ax, *depot)
    for x, y, q in A:
        draw_client(ax, x, y, r=0.34, facecolor="#dbeafe",
                    edgecolor=PALETTE[0], label=q)
    for x, y, q in B:
        draw_client(ax, x, y, r=0.34, facecolor="#ffedd5",
                    edgecolor=PALETTE[1], label=q)
    ax.set_title("Q = 20 — two routes (loads 12 and 16)", color=PALETTE[2])
    square_axes(ax, (0, 13.0), (1.3, 7.0))

    fig.suptitle("Capacity forces splitting the customers across vehicles",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "vrp_02-capacity.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3) Pickup and delivery — three flow styles
# ---------------------------------------------------------------------------
def fig_pickup_delivery():
    fig, axes = plt.subplots(1, 3, figsize=(18, 4.2),
                             gridspec_kw={"wspace": 0.06})
    depot = (4, 1.5)
    cs = [(1.5, 4.0), (4.0, 5.5), (6.5, 4.0)]

    # A: deliveries only
    ax = axes[0]
    draw_route(ax, [depot] + cs + [depot], PALETTE[0])
    draw_depot(ax, *depot, label="depot")
    for x, y in cs:
        draw_client(ax, x, y, r=0.32, facecolor="#dbeafe",
                    edgecolor=PALETTE[0])
    ax.set_title("Deliveries only")
    ax.text(4, 0.4, "freight flows  depot → clients",
            ha="center", fontsize=9, color="#bbbbbb")
    square_axes(ax, (0, 8.5), (0.2, 6.8))

    # B: simultaneous pickup & delivery
    ax = axes[1]
    # Stops can be pure-delivery (only blue), pure-pickup (only yellow), or
    # mixed (both). The running load along the route — not just the total —
    # must stay under capacity.
    cs_b = [(1.5, 4.0), (4.0, 5.5), (6.5, 4.0)]   # C1 left, C2 top, C3 right
    dp = [(3, 0), (0, 2), (2, 1)]                  # (delivery, pickup)
    capacity = 6
    # Initial load = sum of deliveries; load update at stop i: -d_i + p_i.
    loads = [sum(d for d, _ in dp)]
    for d, p in dp:
        loads.append(loads[-1] - d + p)
    path_b = [depot] + cs_b + [depot]
    draw_route(ax, path_b, PALETTE[4])
    draw_depot(ax, *depot, label="depot")
    deliv_c = "#dbeafe"
    pickup_c = "#fde68a"
    for (x, y), (d, p) in zip(cs_b, dp):
        if d > 0 and p > 0:
            ax.add_patch(mpatches.Wedge((x, y), 0.32, 90, 270,
                                        facecolor=deliv_c, edgecolor="#888888",
                                        linewidth=1.0, zorder=4))
            ax.add_patch(mpatches.Wedge((x, y), 0.32, 270, 90,
                                        facecolor=pickup_c, edgecolor="#888888",
                                        linewidth=1.0, zorder=4))
            label = f"d={d}, p={p}"
        elif d > 0:
            ax.add_patch(plt.Circle((x, y), 0.32, facecolor=deliv_c,
                                    edgecolor="#888888", linewidth=1.0,
                                    zorder=4))
            label = f"d={d}"
        else:
            ax.add_patch(plt.Circle((x, y), 0.32, facecolor=pickup_c,
                                    edgecolor="#888888", linewidth=1.0,
                                    zorder=4))
            label = f"p={p}"
        ax.text(x, y - 0.55, label, ha="center", va="top",
                fontsize=8, color="#cccccc")
    # Load labels at the midpoint of each leg (above the arrow).
    for (x1, y1), (x2, y2), L in zip(path_b[:-1], path_b[1:], loads):
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.25, f"load {L}", ha="center", va="center",
                fontsize=8, color=PALETTE[4], fontweight="bold",
                bbox=dict(facecolor="white", edgecolor="none",
                          alpha=0.85, pad=1.0))
    ax.set_title(f"Simultaneous pickup & delivery  (capacity {capacity})")
    legend = [
        mpatches.Patch(facecolor="#dbeafe", edgecolor="#888888", label="delivery"),
        mpatches.Patch(facecolor="#fde68a", edgecolor="#888888", label="pickup"),
    ]
    ax.legend(handles=legend, loc="lower center", ncol=2,
              bbox_to_anchor=(0.5, -0.04), frameon=False, fontsize=9)
    ax.text(4, 0.4, "load changes at every stop",
            ha="center", fontsize=9, color="#bbbbbb")
    square_axes(ax, (0, 8.5), (0.2, 6.8))

    # C: paired pickup -> delivery (three interleaved requests)
    ax = axes[2]
    pair_colors = ["#2563eb", "#16a34a", "#b91c1c"]
    # Nodes laid out around a loop so the interleaved route below has no
    # arrow crossings. Visiting order: P1, P2, D1, P3, D3, D2.
    requests = [
        ((1.5, 3.5), (3.0, 6.2)),  # request 1: P1 left-low, D1 top-left
        ((1.5, 5.0), (6.0, 3.5)),  # request 2: P2 left-high, D2 right-low
        ((4.5, 6.2), (6.0, 5.0)),  # request 3: P3 top-right, D3 right-high
    ]
    # Interleaved visiting sequence — each P_i still precedes its own D_i.
    seq_idx = [(0, "P"), (1, "P"), (0, "D"),
               (2, "P"), (2, "D"), (1, "D")]
    path = [depot]
    for i, kind in seq_idx:
        path.append(requests[i][0] if kind == "P" else requests[i][1])
    path.append(depot)
    draw_route(ax, path, "#6b7280")
    draw_depot(ax, *depot, label="depot")
    for i, ((px, py), (dx, dy)) in enumerate(requests):
        c = pair_colors[i]
        draw_client(ax, px, py, r=0.34, facecolor="#fde68a",
                    edgecolor=c, label=f"P{i+1}")
        draw_client(ax, dx, dy, r=0.34, facecolor="#dbeafe",
                    edgecolor=c, label=f"D{i+1}")
    ax.set_title("Paired pickup → delivery")
    ax.text(4, 0.4, "each $P_i$ must precede its $D_i$ on the route",
            ha="center", fontsize=9, color="#bbbbbb")
    square_axes(ax, (0, 8.5), (0.2, 6.8))

    fig.suptitle("Three freight-flow styles",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "vrp_03-pickup-delivery.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4) Time windows
# ---------------------------------------------------------------------------
def fig_time_windows():
    fig, ax = plt.subplots(figsize=(14.5, 3.8))

    a, b = 8.0, 11.0
    s_dur = 1.0

    win_color = "#86efac"
    ax.axvspan(a, b, ymin=0.08, ymax=0.92,
               color="#86efac", alpha=0.18, zorder=0)
    ax.axvline(a, color=win_color, lw=1.5, zorder=1)
    ax.axvline(b, color=win_color, lw=1.5, zorder=1)
    ax.text((a + b) / 2, 3.6, f"time window [{int(a)}, {int(b)}]",
            ha="center", color=win_color, fontsize=12, fontweight="bold")
    ax.text(a, 3.15, "$a_i$", ha="center", color=win_color, fontsize=12, fontweight="bold")
    ax.text(b, 3.15, "$b_i$", ha="center", color=win_color, fontsize=12, fontweight="bold")

    rows = [
        ("arrive 7:00 — early",   7.0,  "early"),
        ("arrive 9:30 — on time", 9.5,  "ontime"),
        ("arrive 12:00 — late",   12.0, "late"),
    ]

    feasible_color = "#4ade80"
    wait_face = "#fde68a"
    wait_edge = "#b45309"
    wait_text = "#fbbf24"
    infeas_color = "#f87171"

    for i, (lbl, arr, kind) in enumerate(rows):
        y = 2.4 - i * 0.95
        ax.text(5.4, y, lbl, ha="right", va="center", fontsize=10)
        ax.scatter([arr], [y + 0.32], marker="v", s=55,
                   color="#e0e0e0", zorder=4)

        if kind == "early":
            ax.add_patch(Rectangle((arr, y - 0.2), a - arr, 0.4,
                                   facecolor=wait_face, edgecolor=wait_edge,
                                   linewidth=0.9, zorder=3))
            ax.text((arr + a) / 2, y, "wait", ha="center", va="center",
                    fontsize=9, color=wait_edge, fontweight="bold")
            ax.add_patch(Rectangle((a, y - 0.2), s_dur, 0.4,
                                   facecolor=feasible_color, edgecolor="black",
                                   linewidth=0.9, zorder=3))
            ax.text(a + s_dur / 2, y, "service", ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
            ax.text(14.8, y, "feasible ✓", ha="left", va="center",
                    color=feasible_color, fontsize=10, fontweight="bold")

        elif kind == "ontime":
            ax.add_patch(Rectangle((arr, y - 0.2), s_dur, 0.4,
                                   facecolor=feasible_color, edgecolor="black",
                                   linewidth=0.9, zorder=3))
            ax.text(arr + s_dur / 2, y, "service", ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
            ax.text(14.8, y, "feasible ✓", ha="left", va="center",
                    color=feasible_color, fontsize=10, fontweight="bold")

        else:  # late
            ax.add_patch(Rectangle((arr, y - 0.2), s_dur, 0.4,
                                   facecolor="none", edgecolor=infeas_color,
                                   linewidth=1.2, hatch="///", zorder=3))
            cx, cy = arr + s_dur / 2, y
            dx, dy = 0.45, 0.28
            ax.plot([cx - dx, cx + dx], [cy - dy, cy + dy],
                    color=infeas_color, lw=3.0, solid_capstyle="round",
                    zorder=4)
            ax.plot([cx - dx, cx + dx], [cy + dy, cy - dy],
                    color=infeas_color, lw=3.0, solid_capstyle="round",
                    zorder=4)
            ax.text(14.8, y, "infeasible ✗", ha="left", va="center",
                    color=infeas_color, fontsize=10, fontweight="bold")

    ax.set_xlim(5.4, 17)
    ax.set_ylim(-0.6, 4.0)
    ax.set_yticks([])
    ax.set_xticks(range(6, 15))
    ax.set_xlabel("time of day (h)")
    ax.set_title("Time window: wait if early, infeasible if late "
                 "(service duration 1 h)")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "vrp_04-time-windows.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5) Shifts and overtime
# ---------------------------------------------------------------------------
def fig_shifts():
    fig, ax = plt.subplots(figsize=(14, 3.25))
    # shift band
    ax.add_patch(Rectangle((0, 0.4), 8, 0.5,
                           facecolor="#dbeafe", edgecolor="#1e3a8a",
                           linewidth=1.0))
    ax.text(4, 1.05, "regular shift (8 h)", ha="center", color="#1e3a8a",
            fontsize=10, fontweight="bold")
    # overtime
    ax.add_patch(Rectangle((8, 0.4), 2, 0.5,
                           facecolor="#fde68a", edgecolor="#92400e",
                           linewidth=1.0))
    ax.text(9, 1.05, "overtime (penalized)", ha="center", color="#92400e",
            fontsize=10, fontweight="bold")
    # dashed boundary markers
    for x, lbl in [(0, "earliest start"), (8, "latest regular end"),
                   (10, "hard latest end")]:
        ax.axvline(x, color="#cccccc", linestyle="--", linewidth=1.0)
        ax.text(x, 0.25, lbl, ha="center", va="top", fontsize=9)

    # actual route duration arrow
    ax.annotate("", xy=(7, -0.4), xytext=(0.5, -0.4),
                arrowprops=dict(arrowstyle="<->", color=PALETTE[4], lw=2.4))
    ax.text(3.75, -0.55, "actual route duration", ha="center",
            color=PALETTE[4], fontsize=10, fontweight="bold")
    ax.text(0.5, -0.25, "depot leave", ha="center", fontsize=8)
    ax.text(7, -0.25, "depot return", ha="center", fontsize=8)

    ax.set_xlim(-1, 11)
    ax.set_ylim(-1, 1.6)
    ax.set_axis_off()
    ax.set_title("Driver shift: regular band, overtime band, route duration")
    fig.savefig(OUT / "vrp_05-shifts.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 6) Breaks — break inserted into a route
# ---------------------------------------------------------------------------
def fig_breaks():
    fig, axes = plt.subplots(2, 1, figsize=(13.5, 3.6), sharex=True)
    # Top: without break
    ax = axes[0]
    blocks = [(0, 2.5, "#cbd5e1", "drive"),
              (2.5, 1.0, PALETTE[2], "C1"),
              (3.5, 2.0, "#cbd5e1", "drive"),
              (5.5, 1.0, PALETTE[2], "C2"),
              (6.5, 2.0, "#cbd5e1", "drive"),
              (8.5, 1.0, PALETTE[2], "C3"),
              (9.5, 1.5, "#cbd5e1", "drive")]
    for s, d, c, lbl in blocks:
        ax.add_patch(Rectangle((s, -0.3), d, 0.6, facecolor=c,
                               edgecolor="#888888", linewidth=0.6))
        if lbl != "drive":
            ax.text(s + d / 2, 0, lbl, ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.7, 0.7)
    ax.set_title("Without break")
    ax.set_yticks([])
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)

    # Bottom: with break
    ax = axes[1]
    blocks = [(0, 2.5, "#cbd5e1", "drive"),
              (2.5, 1.0, PALETTE[2], "C1"),
              (3.5, 2.0, "#cbd5e1", "drive"),
              (5.5, 1.0, PALETTE[2], "C2"),
              (6.5, 1.5, "#fca5a5", "break"),  # inserted
              (8.0, 2.0, "#cbd5e1", "drive"),
              (10.0, 1.0, PALETTE[2], "C3"),
              (11.0, 1.5, "#cbd5e1", "drive")]
    for s, d, c, lbl in blocks:
        edge = "#7f1d1d" if lbl == "break" else "black"
        ax.add_patch(Rectangle((s, -0.3), d, 0.6, facecolor=c,
                               edgecolor=edge, linewidth=0.8))
        if lbl != "drive":
            color = "#7f1d1d" if lbl == "break" else "white"
            ax.text(s + d / 2, 0, lbl, ha="center", va="center",
                    fontsize=9, color=color, fontweight="bold")
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.7, 0.7)
    ax.set_title("With regulatory break — later clients shift right")
    ax.set_yticks([])
    ax.set_xlabel("time")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)

    legend = [
        mpatches.Patch(facecolor="#cbd5e1", edgecolor="#888888", label="drive"),
        mpatches.Patch(facecolor=PALETTE[2], edgecolor="#888888", label="service"),
        mpatches.Patch(facecolor="#fca5a5", edgecolor="#7f1d1d", label="break"),
    ]
    axes[0].legend(handles=legend, loc="upper right", ncol=3,
                   fontsize=8, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(OUT / "vrp_06-breaks.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 7) Multi-depot
# ---------------------------------------------------------------------------
def fig_multi_depot():
    # Two depots set moderately apart (NOT at the extremes — that reads as two
    # separate instances). Both vehicles' routes reach into the centre, and a
    # contested pair of clients sits on the frontier: an A-client and a B-client
    # side by side near x=12, so the depot-assignment boundary is visibly a
    # decision rather than pure geography.
    fig, ax = plt.subplots(figsize=(15, 4))
    dA = (6.0, 2.7)
    dB = (18.0, 2.7)

    # Routes as node lists (depot -> clients -> depot); clients derived below.
    A_upper = [dA, (1.6, 4.3), (4.3, 4.7), (9.6, 4.6), (11.8, 3.6), dA]
    A_lower = [dA, (1.4, 1.0), (5.0, 0.7), (9.0, 0.9), dA]
    B_upper = [dB, (22.4, 4.3), (19.2, 4.7), (14.4, 4.6), (12.2, 3.4), dB]
    B_lower = [dB, (22.6, 1.0), (19.0, 0.7), (14.6, 0.9), dB]

    for route in (A_upper, A_lower):
        draw_route(ax, route, PALETTE[0])
    for route in (B_upper, B_lower):
        draw_route(ax, route, PALETTE[1])

    draw_depot(ax, *dA, label="depot A", color="#93c5fd")
    draw_depot(ax, *dB, label="depot B", color="#fdba74")
    for route in (A_upper, A_lower):
        for x, y in route[1:-1]:
            draw_client(ax, x, y, r=0.28, facecolor="#dbeafe", edgecolor=PALETTE[0])
    for route in (B_upper, B_lower):
        for x, y in route[1:-1]:
            draw_client(ax, x, y, r=0.28, facecolor="#ffedd5", edgecolor=PALETTE[1])

    ax.set_title("Multi-depot — depot assignment is part of the decision")
    square_axes(ax, (-0.6, 24.6), (-0.2, 5.4))
    fig.savefig(OUT / "vrp_07-multi-depot.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 8) Routing profiles — truck detours around a low-emission zone
# ---------------------------------------------------------------------------
def fig_profiles():
    # Wide corridor: depot at each end, the forbidden zone in the middle,
    # van straight through and truck arcing over the top.
    fig, ax = plt.subplots(figsize=(15, 4))
    start = (0.9, 2.6)
    end = (23.1, 2.6)
    # zone rectangle
    zone = Rectangle((8.0, 1.2), 8.0, 3.0,
                     facecolor="#fee2e2", edgecolor=PALETTE[3],
                     linewidth=1.5, linestyle="--")
    ax.add_patch(zone)
    ax.text(12.0, 4.55, "low-emission zone (trucks forbidden)",
            ha="center", color=PALETTE[3], fontsize=10)

    # van path through
    van = [start, (8.8, 2.0), (12.0, 3.0), (15.2, 2.0), end]
    draw_route(ax, van, PALETTE[0], lw=2.2)
    # truck detour
    truck = [start, (6.0, 5.2), (18.0, 5.3), end]
    draw_route(ax, truck, PALETTE[1], lw=2.2, ls="--")

    # depot squares at start/end
    draw_depot(ax, *start, label="depot")
    draw_depot(ax, *end, label="depot")

    # clients in zone
    for x, y in [(8.8, 2.0), (12.0, 3.0), (15.2, 2.0)]:
        draw_client(ax, x, y, r=0.22, facecolor="#dbeafe",
                    edgecolor=PALETTE[0])

    legend = [
        Line2D([0], [0], color=PALETTE[0], lw=2.2, label="van — may enter zone"),
        Line2D([0], [0], color=PALETTE[1], lw=2.2, ls="--",
               label="truck — must detour"),
    ]
    ax.legend(handles=legend, loc="lower center", ncol=2,
              bbox_to_anchor=(0.5, -0.05), frameon=False, fontsize=9)
    ax.set_title("Routing profiles — distance/duration depend on the vehicle")
    square_axes(ax, (-0.3, 24.3), (0.2, 6.0))
    fig.savefig(OUT / "vrp_08-profiles.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 9) Reloading — one shift, two trips
# ---------------------------------------------------------------------------
def fig_reloading():
    # Denser than the other banners (four panels), so it runs ~25% taller —
    # see BANNER_ASPECT_OVERRIDES. Fonts are bumped to match the extra height.
    TITLE_FS, BAR_FS, NOTE_FS = 14, 11, 11
    fig = plt.figure(figsize=(20, 5.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[4, 1], hspace=0.6, wspace=0.1)

    depot = (6.0, 3.6)
    # Wide landscape spread so each map fills its panel: vehicle A's LONG loop
    # sweeps the left, the two SHORT loops sit upper/lower on the right, depot
    # centered. Colours are explained by the titles and the bottom timelines
    # (which name A/B/C and each trip), so no per-map legend is needed.
    trip_long   = [(2.6, 5.6), (0.8, 4.2), (1.4, 2.2), (3.8, 1.4)]
    trip_short1 = [(8.2, 5.4), (9.6, 4.9), (8.8, 4.1)]
    trip_short2 = [(8.4, 2.7), (9.8, 2.2), (8.9, 1.5)]
    MAP_XLIM, MAP_YLIM = (0, 12), (1.0, 6.2)

    # ---- LEFT: classical CVRP — 3 vehicles, one route each
    axL = fig.add_subplot(gs[0, 0])
    draw_route(axL, [depot] + trip_long + [depot], PALETTE[0])
    draw_route(axL, [depot] + trip_short1 + [depot], PALETTE[1])
    draw_route(axL, [depot] + trip_short2 + [depot], PALETTE[2])
    draw_depot(axL, *depot, label="depot", fontsize=NOTE_FS)
    for x, y in trip_long:
        draw_client(axL, x, y, r=0.30, facecolor="#dbeafe", edgecolor=PALETTE[0])
    for x, y in trip_short1:
        draw_client(axL, x, y, r=0.30, facecolor="#ffedd5", edgecolor=PALETTE[1])
    for x, y in trip_short2:
        draw_client(axL, x, y, r=0.30, facecolor="#dcfce7", edgecolor=PALETTE[2])
    axL.set_title("CVRP — 3 vehicles, one route each", fontsize=TITLE_FS)
    square_axes(axL, MAP_XLIM, MAP_YLIM)

    # ---- RIGHT: multi-trip — 2 vehicles, vehicle B chains both short trips
    axR = fig.add_subplot(gs[0, 1])
    draw_route(axR, [depot] + trip_long + [depot], PALETTE[0])
    draw_route(axR, [depot] + trip_short1 + [depot], PALETTE[1], ls="-")
    draw_route(axR, [depot] + trip_short2 + [depot], PALETTE[1], ls="--")
    draw_depot(axR, *depot, label="depot (reload)", fontsize=NOTE_FS)
    for x, y in trip_long:
        draw_client(axR, x, y, r=0.30, facecolor="#dbeafe", edgecolor=PALETTE[0])
    for x, y in trip_short1:
        draw_client(axR, x, y, r=0.30, facecolor="#ffedd5", edgecolor=PALETTE[1])
    for x, y in trip_short2:
        draw_client(axR, x, y, r=0.30, facecolor="#ffedd5",
                    edgecolor=PALETTE[1], ls="--")
    axR.set_title("Multi-trip — 2 vehicles, B reloads and goes again",
                  fontsize=TITLE_FS)
    square_axes(axR, MAP_XLIM, MAP_YLIM)

    # ---- BOTTOM-LEFT: CVRP shift timeline — three vehicles, each one trip, plenty of slack
    axTL = fig.add_subplot(gs[1, 0])
    SHIFT = 9.0
    for i, (start, dur, color, label) in enumerate([
        (0.0, 7.5, PALETTE[0], "A: long trip"),
        (0.0, 2.5, PALETTE[1], "B: short"),
        (0.0, 2.6, PALETTE[2], "C: short"),
    ]):
        y = 0.7 - i * 0.6
        axTL.add_patch(Rectangle((start, y - 0.22), dur, 0.44, facecolor=color,
                                 alpha=0.85, edgecolor="#888888"))
        axTL.text(start + dur / 2, y, label, ha="center", va="center",
                  color="white", fontsize=BAR_FS, fontweight="bold")
    axTL.axvline(SHIFT, color="#bbbbbb", lw=1.0, ls=":")
    axTL.text(SHIFT, 1.05, "shift end", ha="center", va="bottom",
              fontsize=NOTE_FS, color="#bbbbbb")
    axTL.set_xlim(-0.3, SHIFT + 0.6)
    axTL.set_ylim(-0.9, 1.2)
    axTL.set_yticks([])
    axTL.set_xlabel("time within shift")
    axTL.set_title("3 vehicle-shifts used", fontsize=TITLE_FS)
    for spine in ("top", "right", "left"):
        axTL.spines[spine].set_visible(False)

    # ---- BOTTOM-RIGHT: multi-trip timeline — only two vehicles, B chains
    axTR = fig.add_subplot(gs[1, 1])
    # A
    axTR.add_patch(Rectangle((0, 0.48), 7.5, 0.44, facecolor=PALETTE[0],
                             alpha=0.85, edgecolor="#888888"))
    axTR.text(3.75, 0.7, "A: long trip", ha="center", va="center",
              color="white", fontsize=BAR_FS, fontweight="bold")
    # B trip 1
    axTR.add_patch(Rectangle((0, -0.12), 2.5, 0.44, facecolor=PALETTE[1],
                             alpha=0.85, edgecolor="#888888"))
    axTR.text(1.25, 0.10, "B: trip 1", ha="center", va="center",
              color="white", fontsize=BAR_FS, fontweight="bold")
    # reload
    axTR.add_patch(Rectangle((2.5, -0.12), 0.6, 0.44, facecolor="#fca5a5",
                             edgecolor="#7f1d1d"))
    axTR.text(2.8, 0.10, "rl", ha="center", va="center", color="#7f1d1d",
              fontsize=BAR_FS - 1, fontweight="bold")
    # B trip 2
    axTR.add_patch(Rectangle((3.1, -0.12), 2.6, 0.44, facecolor=PALETTE[1],
                             alpha=0.45, edgecolor="#888888", hatch="//"))
    axTR.text(4.4, 0.10, "B: trip 2", ha="center", va="center",
              color="white", fontsize=BAR_FS, fontweight="bold")
    axTR.axvline(SHIFT, color="#bbbbbb", lw=1.0, ls=":")
    axTR.text(SHIFT, 1.05, "shift end", ha="center", va="bottom",
              fontsize=NOTE_FS, color="#bbbbbb")
    axTR.set_xlim(-0.3, SHIFT + 0.6)
    axTR.set_ylim(-0.9, 1.2)
    axTR.set_yticks([])
    axTR.set_xlabel("time within shift")
    axTR.set_title("2 vehicle-shifts used", fontsize=TITLE_FS)
    for spine in ("top", "right", "left"):
        axTR.spines[spine].set_visible(False)

    fig.savefig(OUT / "vrp_09-reloading.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 10) Optional clients with prizes
# ---------------------------------------------------------------------------
def fig_prizes():
    # Visited clients strung out horizontally near the depot; the high-detour
    # client sits far to the right and is skipped — a wide, shallow scene.
    fig, ax = plt.subplots(figsize=(15, 4))
    depot = (2.0, 2.6)
    visited = [(6.5, 4.1), (12.0, 4.5), (17.5, 3.9)]
    skipped = (23.0, 1.2)

    draw_route(ax, [depot] + visited + [depot], PALETTE[0])
    draw_depot(ax, *depot, label="depot")
    for (x, y), pr in zip(visited, [500, 500, 500]):
        draw_client(ax, x, y, r=0.45, facecolor="#bbf7d0",
                    edgecolor=PALETTE[2], label=pr, fontsize=10)
    # skipped client: dashed red
    draw_client(ax, *skipped, r=0.45, facecolor="#fecaca",
                edgecolor=PALETTE[3], label="120", fontsize=10, ls="--")
    ax.text(skipped[0], skipped[1] - 0.95,
            "skipped — detour cost > prize",
            ha="center", fontsize=9, color=PALETTE[3])

    legend = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#bbf7d0",
               markeredgecolor=PALETTE[2], markersize=12,
               label="visited (prize collected)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#fecaca",
               markeredgecolor=PALETTE[3], markersize=12,
               label="optional, skipped"),
    ]
    ax.legend(handles=legend, loc="lower center", ncol=2,
              bbox_to_anchor=(0.5, -0.05), frameon=False, fontsize=9)
    ax.set_title("Optional clients — the solver weighs prize vs detour cost")
    square_axes(ax, (-0.3, 24.5), (0.0, 5.6))
    fig.savefig(OUT / "vrp_10-prizes.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 11) Mutually exclusive groups
# ---------------------------------------------------------------------------
def fig_groups():
    fig, ax = plt.subplots(figsize=(10, 6.2))
    depot = (1.6, 5.0)

    # Three mutually-exclusive groups. The tour visits exactly one member of
    # each (filled, in the route colour); the other members stay unvisited
    # (hollow, dashed). Each group gets its own colour to read like a proper
    # VRP solution rather than an abstract sketch.
    groups = [
        dict(center=(5.3, 7.7), w=3.8, h=2.8,
             edge="#8E5A82", fill="#efe6f3", text="#5e2b52", label_at=(5.3, 9.4),
             chosen=(4.6, 7.0), alts=[(6.4, 8.3)]),
        dict(center=(12.6, 6.6), w=3.4, h=4.2,
             edge="#3F8A85", fill="#dcefed", text="#1d5f5a",
             label_at=(12.6, 9.0), chosen=(11.5, 7.2),
             alts=[(13.6, 7.6), (13.1, 5.2)]),
        dict(center=(7.6, 2.0), w=4.4, h=2.6,
             edge="#C07A1C", fill="#fbecd4", text="#7a4a06", label_at=(7.6, 0.4),
             chosen=(8.5, 2.7), alts=[(6.0, 1.4)]),
    ]

    # Clean convex loop: depot -> group 1 -> group 2 -> group 3 -> depot.
    tour = [depot] + [g["chosen"] for g in groups] + [depot]

    # 1) Group clouds + their "choose one" captions (drawn first, behind route).
    for g in groups:
        ax.add_patch(Ellipse(g["center"], width=g["w"], height=g["h"],
                             facecolor=g["fill"], edgecolor=g["edge"],
                             linestyle="--", linewidth=1.6, alpha=0.75, zorder=1))
        ax.text(*g["label_at"], "choose one", ha="center", va="center",
                color=g["text"], fontsize=13, fontweight="bold", zorder=2)

    # 2) The tour itself.
    draw_route(ax, tour, PALETTE[0])
    draw_depot(ax, *depot, label="depot")

    # 3) Members: hollow alternatives in the group colour, the visited member
    #    filled in the route colour with a check mark.
    for g in groups:
        for x, y in g["alts"]:
            draw_client(ax, x, y, r=0.34, facecolor="white",
                        edgecolor=g["edge"], ls="--")
        cx, cy = g["chosen"]
        draw_client(ax, cx, cy, r=0.42, facecolor="#cfe3f5",
                    edgecolor=PALETTE[0], label="✓", fontsize=15)

    ax.set_title("Mutually exclusive groups — the tour visits one member of each")
    square_axes(ax, (-0.5, 15.8), (-0.3, 10.2))
    fig.savefig(OUT / "vrp_11-groups.png")
    plt.close(fig)


def main():
    for f in [
        fig_core_vrp,
        fig_capacity,
        fig_pickup_delivery,
        fig_time_windows,
        fig_shifts,
        fig_breaks,
        fig_multi_depot,
        fig_profiles,
        fig_reloading,
        fig_prizes,
        fig_groups,
    ]:
        f()
        print(f"  ✓ {f.__name__}")
    for name in BANNER_FIGURES:
        target = BANNER_ASPECT_OVERRIDES.get(name, BANNER_ASPECT)
        natural, too_narrow = pad_to_banner_aspect(name, target)
        flag = "  ⚠ TOO NARROW (side-padded)" if too_narrow else ""
        print(f"  ▸ {name}: natural {natural:.2f}:1 -> {target}:1{flag}")


if __name__ == "__main__":
    main()
