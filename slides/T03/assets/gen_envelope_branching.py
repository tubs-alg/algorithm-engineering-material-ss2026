"""Generate envelope-branching figure for the "solvers refine on the fly" slide.

Produces one PNG (transparent background, dark-theme palette matching gen_pwla.py):

  envelope_branching.png   3 panels: root envelope, after 1 branch, after 3 branches

Why this exists. The PWLA section closes by noting that modern MIP solvers accept
non-linear constraints directly and refine internally. The mechanism is spatial
branch-and-bound: build a convex underestimator + concave overestimator on a
domain, branch on x to split the domain, and rebuild tighter local envelopes on
each child. Students see PWLA at the user level on the previous slides; this
figure shows what the solver does behind the scenes.

How to use. `python assets/gen_envelope_branching.py` from the slides/ directory.
Regenerate after palette changes.

When to change. If the visual story shifts (e.g. McCormick for bilinear terms
instead of univariate lower/upper hulls), replace the hull computation but keep
the 3-panel root → 1 branch → 3 branches arc.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent

BG = "none"
FG = "#e0e0e0"
CURVE = "#9ad0f5"
LOWER = "#7fbf7b"   # convex underestimator
UPPER = "#e69138"   # concave overestimator
BRANCH = "#c27ba0"  # branching cuts
GRID = "#37474f"
FILL = "#9ad0f5"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.transparent": True,
    "text.color": FG,
    "axes.labelcolor": FG,
    "axes.titlecolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "font.size": 11,
})


def f(x):
    return np.sin(x) + 0.4 * np.sin(2.3 * x)


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def lower_hull(xs, ys):
    """Andrew monotone chain, lower side."""
    pts = sorted(zip(xs, ys))
    hull = []
    for p in pts:
        while len(hull) >= 2 and _cross(hull[-2], hull[-1], p) <= 0:
            hull.pop()
        hull.append(p)
    return np.array(hull)


def upper_hull(xs, ys):
    pts = sorted(zip(xs, ys))
    hull = []
    for p in pts:
        while len(hull) >= 2 and _cross(hull[-2], hull[-1], p) >= 0:
            hull.pop()
        hull.append(p)
    return np.array(hull)


def envelope_on(a, b, n=400):
    xs = np.linspace(a, b, n)
    ys = f(xs)
    lo = lower_hull(xs, ys)
    up = upper_hull(xs, ys)
    return xs, ys, lo, up


def style_ax(ax, xlim, ylim, title):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.grid(True, color=GRID, alpha=0.35, linewidth=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(FG)
    ax.set_xlabel("x")
    ax.set_title(title, pad=8)
    ax.tick_params(labelleft=False)


def draw_envelope(ax, segments):
    """segments: list of (a, b) sub-intervals."""
    for (a, b) in segments:
        xs, ys, lo, up = envelope_on(a, b)
        ax.plot(xs, ys, color=CURVE, lw=2.2, zorder=3)
        # Fill the gap between upper and lower envelopes
        # Build a closed polygon: upper left-to-right, then lower right-to-left
        poly_x = np.concatenate([up[:, 0], lo[::-1, 0]])
        poly_y = np.concatenate([up[:, 1], lo[::-1, 1]])
        ax.fill(poly_x, poly_y, color=FILL, alpha=0.10, zorder=1)
        ax.plot(lo[:, 0], lo[:, 1], color=LOWER, lw=1.8, zorder=2)
        ax.plot(up[:, 0], up[:, 1], color=UPPER, lw=1.8, zorder=2)


def draw_branch_lines(ax, cuts, ylim):
    for c in cuts:
        ax.axvline(c, color=BRANCH, lw=1.0, ls=(0, (3, 3)), alpha=0.8, zorder=4)


def main():
    A, B = 0.0, 2 * np.pi
    ylim = (-1.7, 1.7)
    xlim = (A - 0.1, B + 0.1)

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))

    # Panel 1: root, single domain
    style_ax(axes[0], xlim, ylim, "Root: one domain")
    draw_envelope(axes[0], [(A, B)])

    # Panel 2: one branch at π
    cuts2 = [np.pi]
    style_ax(axes[1], xlim, ylim, "After 1 branch")
    draw_envelope(axes[1], [(A, cuts2[0]), (cuts2[0], B)])
    draw_branch_lines(axes[1], cuts2, ylim)

    # Panel 3: three branches → four sub-intervals
    cuts3 = [np.pi / 2, np.pi, 3 * np.pi / 2]
    edges = [A] + cuts3 + [B]
    segs = list(zip(edges[:-1], edges[1:]))
    style_ax(axes[2], xlim, ylim, "After 3 branches")
    draw_envelope(axes[2], segs)
    draw_branch_lines(axes[2], cuts3, ylim)

    # Single legend on the figure
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color=CURVE, lw=2.2, label=r"$f(x)$"),
        Line2D([0], [0], color=LOWER, lw=1.8, label="convex underestimator"),
        Line2D([0], [0], color=UPPER, lw=1.8, label="concave overestimator"),
        Line2D([0], [0], color=BRANCH, lw=1.0, ls=(0, (3, 3)), label="branching cut"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, -0.02))

    fig.tight_layout(rect=(0, 0.06, 1, 1))
    out = OUT / "envelope_branching.png"
    fig.savefig(out, dpi=160, bbox_inches="tight", transparent=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
