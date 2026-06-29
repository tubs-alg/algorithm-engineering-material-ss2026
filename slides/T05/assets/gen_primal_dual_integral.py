"""Generate the primal-dual integral figure (primal_dual_integral.png).

What this contains
  One run of a minimization solver shown as two step curves over time: the
  incumbent (primal) falling from above toward the optimum, and the bound (dual)
  rising from below toward it. The shaded band BETWEEN them is the primal-dual
  gap; its area over time IS the primal-dual integral. The optimum is the value
  where the two curves meet.

Why it exists
  The integral-metrics slide names three scalars (primal / dual / primal-dual
  integral). The first two are areas under a single gap curve; the primal-dual
  integral is the area of the band between bound and incumbent, and it only
  shrinks as the *true* gap closes from both sides. This figure makes that band
  literal so the slide is not bullets alone.

How to use
  python gen_primal_dual_integral.py  ->  primal_dual_integral.png (dark, transparent)

When it should change
  Adjust INCUMBENT / BOUND breakpoints if the narrative changes; keep both ending
  at OPT so the band closes (proven optimality) before the time limit.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG = "none"
FG = "#e0e0e0"
GRID = "#555555"
PRIMAL = "#4ea8de"   # incumbent (upper)
DUAL = "#7fbf7b"     # bound (lower)
BAND = "#c792ea"     # the gap between them

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "text.color": FG,
    "axes.labelcolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "font.size": 12,
})

TIME_LIMIT = 25.0
OPT = 50.0

# (time, objective value) breakpoints, held constant until the next change.
INCUMBENT = [(0, 100), (2, 80), (5, 66), (9, 57), (14, 52), (18, OPT)]  # primal, from above
BOUND = [(0, 12), (3, 28), (7, 39), (12, 46), (18, OPT)]                # dual, from below


def step_xy(points, t_end):
    """Expand breakpoints into a piecewise-constant (post-step) curve."""
    xs, ys = [], []
    for i, (t, v) in enumerate(points):
        xs.append(t)
        ys.append(v)
        nxt = points[i + 1][0] if i + 1 < len(points) else t_end
        xs.append(nxt)
        ys.append(v)
    return xs, ys


def value_at(points, t):
    """Post-step value of a breakpoint curve at time t."""
    v = points[0][1]
    for bt, bv in points:
        if bt <= t:
            v = bv
        else:
            break
    return v


fig, ax = plt.subplots(figsize=(5.6, 5.6))

# Shade the primal-dual gap band on a fine grid so the step edges stay crisp.
grid = [i * TIME_LIMIT / 600 for i in range(601)]
hi = [value_at(INCUMBENT, t) for t in grid]
lo = [value_at(BOUND, t) for t in grid]
ax.fill_between(grid, lo, hi, color=BAND, alpha=0.22, lw=0,
                label="primal-dual gap")

xs_p, ys_p = step_xy(INCUMBENT, TIME_LIMIT)
xs_d, ys_d = step_xy(BOUND, TIME_LIMIT)
ax.plot(xs_p, ys_p, color=PRIMAL, lw=2.4, label="incumbent (primal)")
ax.plot(xs_d, ys_d, color=DUAL, lw=2.4, label="bound (dual)")

# optimum line + the moment the gap closes
ax.axhline(OPT, color=FG, lw=1.0, ls=":", alpha=0.5)
ax.annotate("optimum", (0.3, OPT), textcoords="offset points",
            xytext=(0, 6), fontsize=10, color=FG, alpha=0.8)
ax.scatter([18], [OPT], color=FG, s=45, zorder=5)
ax.annotate("gap closed @ 18s", (18, OPT), textcoords="offset points",
            xytext=(6, -22), fontsize=10, color=FG, alpha=0.85)

ax.set_xlabel("wall-clock time (s)")
ax.set_ylabel("objective value")
ax.set_xlim(0, TIME_LIMIT)
ax.set_ylim(0, 105)
ax.grid(True, color=GRID, lw=0.5, alpha=0.5)
for spine in ax.spines.values():
    spine.set_color(GRID)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(loc="upper right", framealpha=0.0, fontsize=10, labelcolor=FG)

fig.tight_layout()
fig.savefig("primal_dual_integral.png", dpi=200, bbox_inches="tight",
            transparent=True, edgecolor="none")
print("Saved primal_dual_integral.png")
