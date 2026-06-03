"""Visual proof that bipartite perfect matching LP has only integer vertices.

Three-panel figure on a dark slide background:

  Panel 1: A fractional LP solution. Four edges with x = 1/2 form a 4-cycle
           (the only way for fractional values to satisfy the equality
           constraints is along an even closed walk in a bipartite graph).
           Alternating +/-eps markers are placed on cycle edges.

  Panel 2: x^+ = x + eps * (+1, -1, +1, -1) around the cycle.
           At eps = 1/2: two edges saturate to 1, two drop to 0.

  Panel 3: x^- = x - eps * (+1, -1, +1, -1) around the cycle.
           At eps = 1/2: the opposite two edges saturate.

  Caption (on the slide, not in the figure): x = (x^+ + x^-)/2, so x is the
  midpoint of two feasible points and cannot be an LP vertex. The objective
  is linear in eps, so one of the two directions weakly improves. Iterate.

How to use. `python assets/gen_bipartite_cycle_perturb.py` from slides/.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from pathlib import Path

OUT = Path(__file__).parent

FG = "#e0e0e0"
L_COLOR = "#3d85c6"
R_COLOR = "#e69138"
INT_EDGE = "#f5d76e"
FRAC_EDGE = "#9ad0f5"
PLUS = "#7fbf7b"
MINUS = "#c27ba0"
DIM = "#5a6b78"

plt.rcParams.update({
    "savefig.transparent": True,
    "text.color": FG,
    "axes.titlecolor": FG,
    "font.size": 11,
})

L_POS = {"a": (0.2, 3.2), "b": (0.2, 2.0), "c": (0.2, 0.8)}
R_POS = {"1": (2.4, 3.2), "2": (2.4, 2.0), "3": (2.4, 0.8)}

CYCLE = [("a", "1"), ("b", "1"), ("b", "2"), ("a", "2")]
CYCLE_SIGNS = [+1, -1, +1, -1]

EDGES_INIT = {
    ("a", "1"): 0.5,
    ("b", "1"): 0.5,
    ("b", "2"): 0.5,
    ("a", "2"): 0.5,
    ("c", "3"): 1.0,
}


def draw_node(ax, x, y, label, color):
    c = Circle((x, y), 0.16, facecolor=color, edgecolor=FG,
               linewidth=1.4, zorder=3)
    ax.add_patch(c)
    ax.text(x, y, label, color="#1e1e2e", fontsize=11, ha="center",
            va="center", zorder=4, fontweight="bold")


def edge_style(val):
    if val <= 1e-6:
        return DIM, 0.8, 0.5, "dotted"
    if abs(val - 1.0) < 1e-6:
        return INT_EDGE, 3.2, 1.0, "solid"
    return FRAC_EDGE, 2.4, 0.95, "solid"


def value_text(val):
    if val <= 1e-6:
        return "0", DIM
    if abs(val - 1.0) < 1e-6:
        return "1", INT_EDGE
    if abs(val - 0.5) < 1e-6:
        return r"$\frac{1}{2}$", FRAC_EDGE
    return f"{val:.2g}", FRAC_EDGE


EDGE_LABEL_OFFSET = {
    ("a", "1"): 0.12,
    ("b", "1"): -0.14,
    ("a", "2"): 0.14,
    ("b", "2"): -0.12,
    ("c", "3"): 0.14,
}


def draw_edge(ax, u, v, val, arrow_sign=None):
    pu = L_POS[u]
    pv = R_POS[v]
    color, lw, alpha, ls = edge_style(val)
    ax.plot([pu[0], pv[0]], [pu[1], pv[1]], color=color, lw=lw,
            alpha=alpha, zorder=1, linestyle=ls,
            solid_capstyle="round")
    text, text_color = value_text(val)
    mx, my = (pu[0] + pv[0]) / 2, (pu[1] + pv[1]) / 2
    offset_y = EDGE_LABEL_OFFSET.get((u, v), 0.0)
    ax.text(mx, my + offset_y, text, color=text_color, fontsize=11,
            ha="center", va="center", zorder=4,
            bbox=dict(facecolor="#1e1e2e", edgecolor="none", pad=1.2))

    if arrow_sign is not None:
        marker_color = PLUS if arrow_sign > 0 else MINUS
        sym = r"$+\varepsilon$" if arrow_sign > 0 else r"$-\varepsilon$"
        ax.text(mx + 0.55, my - offset_y, sym, color=marker_color,
                fontsize=11, ha="left", va="center", zorder=5,
                fontweight="bold")


def draw_graph(ax, x_values, title, signs=None):
    ax.set_xlim(-0.3, 3.8)
    ax.set_ylim(-0.1, 4.1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, pad=8, fontsize=12.5)

    for (u, v), val in x_values.items():
        sign = None
        if signs is not None and (u, v) in signs:
            sign = signs[(u, v)]
        draw_edge(ax, u, v, val, arrow_sign=sign)

    for name, (x, y) in L_POS.items():
        draw_node(ax, x, y, name, L_COLOR)
    for name, (x, y) in R_POS.items():
        draw_node(ax, x, y, name, R_COLOR)


def perturb(x0, eps):
    x = dict(x0)
    for (u, v), sign in zip(CYCLE, CYCLE_SIGNS):
        x[(u, v)] = x0[(u, v)] + sign * eps
    return x


def save_single(name, x_values, title, signs=None):
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    draw_graph(ax, x_values, title, signs=signs)
    fig.tight_layout(pad=0.3)
    out = OUT / name
    fig.savefig(out, dpi=180, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"wrote {out}")


def main():
    signs_init = {e: s for e, s in zip(CYCLE, CYCLE_SIGNS)}
    x_plus = perturb(EDGES_INIT, +0.5)
    x_minus = perturb(EDGES_INIT, -0.5)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    draw_graph(axes[0], EDGES_INIT,
               r"$x$:  fractional 4-cycle",
               signs=signs_init)
    draw_graph(axes[1], x_plus,
               r"$x^{+} = x + \frac{1}{2}\delta$")
    draw_graph(axes[2], x_minus,
               r"$x^{-} = x - \frac{1}{2}\delta$")
    fig.tight_layout(pad=0.5)
    out = OUT / "bipartite_cycle_perturb.png"
    fig.savefig(out, dpi=170, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"wrote {out}")

    save_single("bipartite_cycle_perturb_1.png", EDGES_INIT,
                r"$x$:  fractional 4-cycle", signs=signs_init)
    save_single("bipartite_cycle_perturb_2.png", x_plus,
                r"$x^{+} = x + \frac{1}{2}\delta$")
    save_single("bipartite_cycle_perturb_3.png", x_minus,
                r"$x^{-} = x - \frac{1}{2}\delta$")


if __name__ == "__main__":
    main()
