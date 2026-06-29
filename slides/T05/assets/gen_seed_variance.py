"""Plot the seed-variance distribution (seed_variance.png).

What this contains
  Reads seed_variance.json (produced by run_seed_variance.py) and draws the 20
  per-seed wall-clock times as sorted bars: solved (proven-optimal) runs in blue,
  with the bars above the mean in red to flag the heavy tail, and any run that
  hit the time limit without proving optimality drawn hatched and capped (a
  censored observation, not a real runtime). The median and mean of the *solved*
  runs are marked. The point the figure makes: the same model on the same machine,
  changing only the random seed, scatters across two-plus orders of magnitude and
  one seed does not even finish, yet every finished run proves the identical optimum.

Why it exists
  Centerpiece of the "high variance" slide. Sorting the bars turns the raw seed
  list into a readable distribution and exposes the heavy right tail; separating
  the censored run keeps us honest about what was and was not measured.

How to use
  python gen_seed_variance.py   ->  writes seed_variance.png (dark, transparent)

When it should change
  If the experiment is re-run, regenerate from the new JSON; the script adapts to
  whatever runs (and however many timeouts) the JSON contains.
"""

import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG = "none"
FG = "#e0e0e0"
GRID = "#555555"
BAR = "#4ea8de"
TAIL = "#e74c3c"      # solved bars above the mean: the dangerous tail
TIMEOUT = "#999999"   # censored run (hit the limit, not solved)
MEDIAN = "#6aa84f"
MEAN = "#e69138"

data = json.loads((Path(__file__).with_name("seed_variance.json")).read_text())
limit = data["time_limit_s"]

solved = sorted(r["wall_time"] for r in data["runs"] if r["status"] == "OPTIMAL")
n_timeout = sum(1 for r in data["runs"] if r["status"] != "OPTIMAL")
median = statistics.median(solved)
mean = statistics.mean(solved)
ratio = solved[-1] / solved[0]

# all runs sorted; censored runs (status != OPTIMAL) sort to the far right at the limit
ordered = sorted(data["runs"], key=lambda r: (r["status"] != "OPTIMAL", r["wall_time"]))

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "text.color": FG,
    "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG, "font.size": 12,
})

fig, ax = plt.subplots(figsize=(16, 4.5))

for k, r in enumerate(ordered):
    t = r["wall_time"]
    if r["status"] != "OPTIMAL":
        ax.bar(k, t, color="none", width=0.78, zorder=3,
               edgecolor=TIMEOUT, hatch="////", linewidth=1.3)
        ax.annotate("timeout\n(not solved)", xy=(k, t), xytext=(0, 6),
                    textcoords="offset points", ha="center", va="bottom",
                    fontsize=9, color=TIMEOUT)
    else:
        ax.bar(k, t, color=TAIL if t > mean else BAR, width=0.78, zorder=3)

ax.axhline(median, color=MEDIAN, lw=2, ls="--", zorder=4,
           label=f"median = {median:.1f} s")
ax.axhline(mean, color=MEAN, lw=2, ls="--", zorder=4,
           label=f"mean = {mean:.1f} s")

ax.set_xlabel("the 20 runs, sorted by runtime (same model, one random seed each)")
ax.set_ylabel("time to proven optimum (s)")
ax.set_xticks([])
ax.set_ylim(0, limit * 1.12)
ax.grid(True, axis="y", color=GRID, lw=0.5, alpha=0.5)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(GRID)

ax.annotate(
    f"solved runs span {solved[0]:.2f} s to {solved[-1]:.1f} s  =  {ratio:.0f}x   ·   "
    f"{n_timeout} of {data['n_runs']} never proved optimality",
    xy=(0.5, 1.04), xycoords="axes fraction", ha="center", va="bottom",
    fontsize=13.5, fontweight="bold", color=FG)

ax.legend(loc="upper left", fontsize=11, facecolor=(0, 0, 0, 0.35),
          edgecolor=GRID, labelcolor=FG)

fig.tight_layout()
fig.savefig("seed_variance.png", dpi=200, bbox_inches="tight",
            transparent=True, edgecolor="none")
print("Saved seed_variance.png")
print(f"  all proved the same optimum: {data['unique_optima']} "
      f"(solved {data['n_runs'] - n_timeout}/{data['n_runs']})")
print(f"  solved: min={solved[0]} max={solved[-1]} ratio={ratio:.0f}x "
      f"median={median:.2f} mean={mean:.2f}")
