"""Generate memory layout diagrams for AdjacencyList vs CSR.

Emits three PNGs:
  - adjlist_vs_csr_memory.png  — combined figure (both panels stacked)
  - adjlist_memory.png          — AdjList panel only
  - csr_memory.png              — CSR panel only

The two single-panel variants are generated so the slide can reveal them
sequentially (CSR as a fragment below AdjList). To keep the content
visually aligned when stacked, both single-panel PNGs use:

  - the same figure width (12 inches)
  - the same axis x-range (SHARED_XLIM)
  - the same figure-relative left/right margins (subplots_adjust)
  - no bbox_inches="tight"

so that data coordinate x=0.5 (the first cell) lands at the same pixel
column in both PNGs.

Shows the same 4-vertex graph stored in both representations:
  AdjacencyList: vector<vector<int>> — each vertex points to a separate heap block
  CSR: two flat arrays (offsets + targets) — all neighbors contiguous

Uses the example from graph.h:
  adj[0]=[2,3]  adj[1]=[0]  adj[2]=[0,1,3]  adj[3]=[0,2]
  offsets=[0, 2, 3, 6, 8]  targets=[2,3, 0, 0,1,3, 0,2]
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
matplotlib.use("Agg")

BG = "none"
FG = "#e0e0e0"
PTR_COLOR = "#f39c12"
CELL_OFFSET = "#4ea8de"
CELL_TARGET = "#e74c3c"
CELL_VEC = "#3a6b8c"
CELL_HEAP = "#8e5ea2"

CW = 0.7   # cell width
CH = 0.55  # cell height
GAP = 0.06

# Shared horizontal layout: both single-panel figures use the same figure
# width, the same axis x-range, and the same subplot margins. That guarantees
# axis coordinate x=0.5 maps to the same pixel column in both PNGs.
FIG_WIDTH_IN = 12.0
SHARED_XLIM = (-1.2, 11.0)
MARGIN_LEFT = 0.02
MARGIN_RIGHT = 0.98

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "text.color": FG,
})


def draw_cell(ax, x, y, text, color, w=CW, h=CH, fontsize=9):
    rect = mpatches.FancyBboxPatch(
        (x, y), w - GAP, h,
        boxstyle="round,pad=0.04", facecolor=color,
        edgecolor=FG, linewidth=0.6)
    ax.add_patch(rect)
    ax.text(x + (w - GAP) / 2, y + h / 2, str(text),
            ha="center", va="center", fontsize=fontsize,
            color="white", fontfamily="monospace", fontweight="bold")


def draw_adjlist(ax):
    ax.set_title("AdjacencyList: vector<vector<int>> — scattered heap blocks",
                 fontsize=12, fontweight="bold", color=FG, loc="left", pad=8)

    # Layout: outer vector on the left, heap blocks on the right.
    # All 4 rows share y-levels, arrows go straight right.
    heap_data = [[2, 3], [0], [0, 1, 3], [0, 2]]
    row_spacing = CH + 0.35
    outer_x = 0.5
    outer_w = 1.2
    # Scatter heap blocks horizontally to suggest random heap addresses.
    heap_x_offsets = [4.0, 6.5, 3.2, 7.0]

    n_rows = len(heap_data)
    top_y = (n_rows - 1) * row_spacing

    for i, neighbors in enumerate(heap_data):
        y = top_y - i * row_spacing

        # Outer vector cell
        draw_cell(ax, outer_x, y, f"adj_[{i}]", CELL_VEC, w=outer_w, fontsize=8)

        # Heap block
        hx = heap_x_offsets[i]
        for j, nb in enumerate(neighbors):
            draw_cell(ax, hx + j * CW, y, nb, CELL_HEAP)

        # Arrow from vector cell to heap block
        ax.annotate("",
                    xy=(hx - 0.08, y + CH / 2),
                    xytext=(outer_x + outer_w - GAP + 0.08, y + CH / 2),
                    arrowprops=dict(arrowstyle="-|>", color=PTR_COLOR, lw=1.2))

        # "v=i" label above each block
        block_mid = hx + len(neighbors) * CW / 2 - GAP / 2
        ax.text(block_mid, y + CH + 0.1, f"v={i}",
                ha="center", fontsize=7, color=FG, fontstyle="italic")

    # Annotation — top right
    ax.text(7.5, top_y + CH + 0.35,
            "each pointer →\npotential cache miss",
            fontsize=9, color=PTR_COLOR, fontstyle="italic",
            ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=(0, 0, 0, 0.5),
                      edgecolor=PTR_COLOR, linewidth=0.8, alpha=0.9))

    ax.set_xlim(*SHARED_XLIM)
    # Tight vertical content bounds: the lowest artist (bottom of adj_[3]) sits
    # at y=0, so just a small padding below avoids wasted whitespace when the
    # single-panel figure is saved without bbox_inches="tight".
    ax.set_ylim(-0.1, top_y + CH + 0.9)
    ax.axis("off")


def draw_csr(ax):
    ax.set_title("CSR: two flat arrays — all neighbors contiguous",
                 fontsize=12, fontweight="bold", color=FG, loc="left", pad=8)

    # offsets[]
    offsets = [0, 2, 3, 6, 8]
    ox_start = 0.5
    oy = 1.5
    ax.text(ox_start - 0.15, oy + CH / 2, "offsets[]", fontsize=9,
            color=CELL_OFFSET, fontweight="bold", fontfamily="monospace",
            ha="right", va="center")
    for k, val in enumerate(offsets):
        draw_cell(ax, ox_start + k * CW, oy, val, CELL_OFFSET)

    # targets[]
    targets = [2, 3, 0, 0, 1, 3, 0, 2]
    tx_start = 0.5
    ty = 0.3
    ax.text(tx_start - 0.15, ty + CH / 2, "targets[]", fontsize=9,
            color=CELL_TARGET, fontweight="bold", fontfamily="monospace",
            ha="right", va="center")
    for k, val in enumerate(targets):
        draw_cell(ax, tx_start + k * CW, ty, val, CELL_TARGET)

    # Vertex-range brackets under targets
    vertex_ranges = [(0, 2, "v=0"), (2, 3, "v=1"), (3, 6, "v=2"), (6, 8, "v=3")]
    for start, end, label in vertex_ranges:
        bx1 = tx_start + start * CW
        bx2 = tx_start + end * CW - GAP
        mid = (bx1 + bx2) / 2
        bracket_y = ty - 0.15
        ax.plot([bx1, bx1, bx2, bx2],
                [bracket_y + 0.07, bracket_y, bracket_y, bracket_y + 0.07],
                color=FG, lw=0.8)
        ax.text(mid, bracket_y - 0.15, label, ha="center", fontsize=8,
                color=FG, fontfamily="monospace")

    # Dashed guides from offsets to target positions
    for i, (start, _end, _lbl) in enumerate(vertex_ranges):
        ox_mid = ox_start + i * CW + (CW - GAP) / 2
        tx_mid = tx_start + start * CW + (CW - GAP) / 2
        ax.plot([ox_mid, tx_mid], [oy - 0.04, ty + CH + 0.04],
                color="#4ea8de", lw=1.2, alpha=0.7, linestyle="--")

    # Cache-friendly annotation — right
    ax.text(7.5, 0.6,
            "sequential memory walk\n→ cache-friendly",
            fontsize=9, color="#2ecc71", fontstyle="italic", ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=(0, 0, 0, 0.5),
                      edgecolor="#2ecc71", linewidth=0.8, alpha=0.9))

    ax.set_xlim(*SHARED_XLIM)
    ax.set_ylim(-0.55, 2.4)
    ax.axis("off")


# Absolute vertical reservations (in inches) for the title above the axis
# and the margin below it. Fixed absolute sizes mean a short panel (CSR)
# and a tall panel (AdjList) both get the same amount of space for the title
# — no over-reservation on the taller figure.
TITLE_AREA_IN = 0.35   # enough for a 12pt title + 8pt pad
BOTTOM_AREA_IN = 0.05  # minimal — content already has its own ylim padding


def save_single_panel(draw_fn, path, fig_height):
    """Save a single-panel figure with the shared horizontal layout.

    Using the same figure width and the same left/right subplot margins on
    both panels means axis coordinate x=0 sits at the same pixel column in
    every generated PNG — so the two single-panel images align horizontally
    when stacked vertically in the slide.
    """
    fig, ax = plt.subplots(figsize=(FIG_WIDTH_IN, fig_height))
    draw_fn(ax)
    fig.subplots_adjust(
        left=MARGIN_LEFT, right=MARGIN_RIGHT,
        top=1.0 - TITLE_AREA_IN / fig_height,
        bottom=BOTTOM_AREA_IN / fig_height,
    )
    # No bbox_inches="tight" here — tight-cropping would trim the axes to
    # content bounds, which differ between the two panels and would break
    # horizontal alignment.
    fig.savefig(path, dpi=200, transparent=True, edgecolor="none")
    plt.close(fig)
    print(f"Saved {path}")


# Combined figure (unchanged output for anyone who wants the full diagram)
fig, (ax_top, ax_bot) = plt.subplots(
    2, 1, figsize=(FIG_WIDTH_IN, 5.0),
    gridspec_kw={"height_ratios": [5, 3]})
draw_adjlist(ax_top)
draw_csr(ax_bot)
plt.tight_layout()
fig.savefig("adjlist_vs_csr_memory.png", dpi=200, bbox_inches="tight",
            transparent=True, edgecolor="none")
plt.close(fig)
print("Saved adjlist_vs_csr_memory.png")

# Single-panel variants — horizontally aligned by construction
save_single_panel(draw_adjlist, "adjlist_memory.png", fig_height=3.1)
save_single_panel(draw_csr, "csr_memory.png", fig_height=1.9)
