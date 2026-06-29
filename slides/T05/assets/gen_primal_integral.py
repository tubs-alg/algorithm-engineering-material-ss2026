"""Generate the primal-integral comparison figure (primal_integral.png).

What this contains
  Two configurations solving the *same* instance, each shown as a primal-gap
  step curve over time (gap = distance of the incumbent from the known optimum,
  in percent). The shaded area under each curve IS the primal integral.

Why it exists
  The slide asks "which config performed better?". The two runs are built to
  *tie* on the obvious milestone: both prove the optimum at the same wall-clock
  time (24 s), so time-to-optimality cannot separate them. The primal integral
  breaks the tie: config A finds good solutions far earlier and stays close,
  giving it the *smaller* integral, while config B drifts down slowly. The
  integral is the single scalar that captures the whole convergence trajectory
  instead of one moment, and here it is the only metric that distinguishes them.

How to use
  python gen_primal_integral.py  ->  writes primal_integral.png (dark, transparent)

When it should change
  Adjust the STEP data if the narrative numbers change; keep both runs reaching
  gap 0 at the *same* time (tie on time-to-optimality) so the integral, not the
  milestone, is the tiebreak.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG = "none"
FG = "#e0e0e0"
GRID = "#555555"
BLUE = "#4ea8de"   # config A
ORANGE = "#e69138"  # config B

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "text.color": FG,
    "axes.labelcolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "font.size": 12,
})

TIME_LIMIT = 30.0

# (time, gap%) breakpoints; gap is held constant until the next improvement.
# Both runs reach gap 0 at the SAME time (24 s) -> tie on time-to-optimality;
# the primal integral is what separates them.
CONFIG_A = [(0, 100), (1, 30), (4, 14), (9, 6), (16, 2), (24, 0)]
CONFIG_B = [(0, 100), (2, 55), (6, 35), (12, 18), (19, 6), (24, 0)]


def step_xy(points, t_end):
    """Expand breakpoints into a piecewise-constant (post-step) curve."""
    xs, ys = [], []
    for i, (t, g) in enumerate(points):
        xs.append(t)
        ys.append(g)
        nxt = points[i + 1][0] if i + 1 < len(points) else t_end
        xs.append(nxt)
        ys.append(g)
    return xs, ys


def integral(points, t_end):
    """Primal integral = area under the post-step gap curve."""
    area = 0.0
    for i, (t, g) in enumerate(points):
        nxt = points[i + 1][0] if i + 1 < len(points) else t_end
        area += g * (nxt - t)
    return area


def opt_time(points):
    """First time the gap reaches 0 (proven optimum)."""
    for t, g in points:
        if g == 0:
            return t
    return None


fig, axes = plt.subplots(1, 2, figsize=(17, 4.2), sharey=True)

panels = [
    ("Config A", CONFIG_A, BLUE, axes[0]),
    ("Config B", CONFIG_B, ORANGE, axes[1]),
]

for name, pts, color, ax in panels:
    xs, ys = step_xy(pts, TIME_LIMIT)
    pi = integral(pts, TIME_LIMIT)
    topt = opt_time(pts)

    ax.fill_between(xs, ys, step=None, color=color, alpha=0.22)
    ax.plot(xs, ys, color=color, lw=2.4)

    # mark the moment optimality is reached
    ax.scatter([topt], [0], color=color, s=55, zorder=5)
    ax.annotate(f"optimum @ {topt:.0f}s", (topt, 0), textcoords="offset points",
                xytext=(6, 14), fontsize=10, color=color)

    ax.set_title(f"{name}    primal integral = {pi:.0f}",
                 fontsize=13, fontweight="bold", color=color)
    ax.set_xlabel("wall-clock time (s)")
    ax.set_xlim(0, TIME_LIMIT)
    ax.set_ylim(0, 105)
    ax.grid(True, color=GRID, lw=0.5, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

axes[0].set_ylabel("primal gap to optimum (%)")

fig.tight_layout()
fig.savefig("primal_integral.png", dpi=200, bbox_inches="tight",
            transparent=True, edgecolor="none")
print("Saved primal_integral.png")
print(f"  A integral = {integral(CONFIG_A, TIME_LIMIT):.0f}, opt @ {opt_time(CONFIG_A)}s")
print(f"  B integral = {integral(CONFIG_B, TIME_LIMIT):.0f}, opt @ {opt_time(CONFIG_B)}s")
