"""Generate the small network-flow example figure for the intro slide.

Produces one PNG (transparent background, dark-theme palette matching gen_pwla.py):

  network_flow.png   2:1 landscape — source on the left, sink on the right,
                     five nodes, edges labelled "flow / capacity".

Why this exists. The Network-Flow slide in _00-intro.qmd shows the abstract
form on the left and a list of real-world siblings on the right. A small
worked instance gives students one concrete picture to anchor the abstract
variables x_e on edges, supplies/demands b_v on vertices, and capacities u_e.

How to use. `python assets/gen_network_flow.py` from the slides/ directory.

When to change. Edit the EDGES / NODES lists if the flow values or the graph
shape need to change. Keep the 1:2 portrait aspect so the slide layout holds.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
from pathlib import Path

OUT = Path(__file__).parent

FG = "#e0e0e0"
NODE_FILL = "#2d4059"
NODE_EDGE = "#9ad0f5"
EDGE = "#9ad0f5"
LABEL = "#f5d76e"
SUPPLY = "#7fbf7b"
DEMAND = "#e69138"

plt.rcParams.update({
    "savefig.transparent": True,
    "text.color": FG,
    "font.size": 14,
})

# (name, x, y, b_v) — b_v > 0 supply (source side), < 0 demand (sink side), 0 transit
NODES = {
    "s": (0.0, 1.5, -5),
    "a": (1.6, 2.7,  0),
    "b": (1.6, 1.5,  0),
    "c": (1.6, 0.3,  0),
    "d": (3.2, 2.7,  0),
    "e": (3.2, 1.5,  0),
    "f": (3.2, 0.3,  0),
    "t": (4.8, 1.5, +5),
}

# (u, v, flow, capacity)
EDGES = [
    ("s", "a", 2, 3),
    ("s", "b", 2, 3),
    ("s", "c", 1, 2),
    ("a", "d", 1, 2),
    ("a", "e", 1, 2),
    ("b", "d", 1, 2),
    ("b", "e", 1, 2),
    ("b", "f", 0, 2),
    ("c", "e", 0, 2),
    ("c", "f", 1, 2),
    ("d", "t", 2, 3),
    ("e", "t", 2, 3),
    ("f", "t", 1, 2),
]


def draw():
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set_xlim(-0.4, 5.5)
    ax.set_ylim(-0.2, 3.2)
    ax.set_aspect("equal")
    ax.axis("off")

    # Edges
    for (u, v, f, cap) in EDGES:
        x1, y1, _ = NODES[u]
        x2, y2, _ = NODES[v]
        active = f > 0
        lw = 2.4 if active else 1.2
        alpha = 1.0 if active else 0.45
        arr = FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle="-|>", mutation_scale=14,
            shrinkA=18, shrinkB=18,
            color=EDGE, linewidth=lw, alpha=alpha, zorder=1,
        )
        ax.add_patch(arr)
        # Label "f / cap" at midpoint, slightly offset perpendicular to the edge
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        norm = (dx * dx + dy * dy) ** 0.5
        ox, oy = -dy / norm * 0.18, dx / norm * 0.18
        ax.text(mx + ox, my + oy, f"{f}/{cap}",
                color=LABEL, fontsize=10, ha="center", va="center",
                zorder=3)

    # Nodes
    for name, (x, y, b) in NODES.items():
        c = Circle((x, y), 0.22, facecolor=NODE_FILL, edgecolor=NODE_EDGE,
                   linewidth=1.8, zorder=2)
        ax.add_patch(c)
        ax.text(x, y, name, color=FG, fontsize=12, ha="center", va="center",
                zorder=3, fontweight="bold")
        if b != 0:
            tag_color = SUPPLY if b < 0 else DEMAND
            tag = f"$b_{{{name}}} = {b:+d}$"
            ax.text(x, y - 0.40, tag, color=tag_color, fontsize=12,
                    ha="center", va="top", zorder=3)

    fig.tight_layout(pad=0.2)
    out = OUT / "network_flow.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", transparent=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    draw()
