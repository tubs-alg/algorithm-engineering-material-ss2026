"""Generate the aggregation-summaries figure (aggregation_summaries.png).

What this contains
  A histogram of per-instance runtimes drawn from a heavy-tailed distribution,
  with vertical markers for the common summary statistics: arithmetic mean,
  median, geometric mean, and the 90th percentile, plus a shaded interquartile
  range (IQR). The point is spatial: on skewed data these summaries land in very
  different places, so the choice of summary changes the story.

Why it exists
  The aggregation slide lists mean / median / geomean / quantiles / CI. This figure
  makes the failure of the arithmetic mean visible: a few expensive instances drag
  it far into the right tail, away from where most instances actually are (the
  median). The geometric mean sits between the two. Quantiles describe the tail
  the median hides.

How to use
  python gen_aggregation.py  ->  aggregation_summaries.png (dark, transparent)

When it should change
  Adjust SIGMA / SCALE / SEED to change the skew. Keep the distribution clearly
  right-skewed so mean > geomean > median stays visually obvious.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BG = "none"
FG = "#e0e0e0"
GRID = "#555555"
BARS = "#4ea8de"
IQR = "#7fbf7b"
C_MEAN = "#e06666"     # arithmetic mean (dragged into the tail)
C_MED = "#f1c232"      # median
C_GEO = "#c792ea"      # geometric mean
C_P90 = "#e69138"      # 90th percentile

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "text.color": FG,
    "axes.labelcolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "font.size": 12,
})

SEED = 7
SCALE = 2.0
SIGMA = 0.85
rng = np.random.default_rng(SEED)
runtimes = SCALE * rng.lognormal(mean=0.0, sigma=SIGMA, size=240)

mean = float(np.mean(runtimes))
median = float(np.median(runtimes))
geomean = float(np.exp(np.mean(np.log(runtimes))))
p90 = float(np.percentile(runtimes, 90))
q25 = float(np.percentile(runtimes, 25))
q75 = float(np.percentile(runtimes, 75))

fig, ax = plt.subplots(figsize=(5.6, 5.6))
xmax = float(np.percentile(runtimes, 99)) * 1.05
ax.hist(runtimes, bins=44, range=(0, xmax), color=BARS, alpha=0.55, edgecolor="none")

ax.axvspan(q25, q75, color=IQR, alpha=0.28, zorder=0)
for q in (q25, q75):
    ax.axvline(q, color=IQR, lw=1.8, ls="--", alpha=0.9, zorder=1)
ax.annotate("", xy=(q75, ax.get_ylim()[1] * 0.88), xytext=(q25, ax.get_ylim()[1] * 0.88),
            arrowprops=dict(arrowstyle="<->", color=IQR, lw=1.8))
ax.text((q25 + q75) / 2, ax.get_ylim()[1] * 0.92, "IQR", ha="center",
        va="bottom", fontsize=11, fontweight="bold", color=IQR)

ymax = ax.get_ylim()[1]
# Note: for a lognormal, geomean == median, so a separate geomean line would just
# overlap the median. We mark median / mean / p90 (the spatial point) and leave
# geomean to the slide text, where its real role (averaging ratios) belongs.
for val, color, label in [
    (median, C_MED, f"median = {median:.1f}s"),
    (mean, C_MEAN, f"arithmetic mean = {mean:.1f}s"),
    (p90, C_P90, f"90th pct = {p90:.1f}s"),
]:
    ax.axvline(val, color=color, lw=2.2, label=label)

ax.set_xlabel("runtime per instance (s)")
ax.set_ylabel("instances")
ax.set_xlim(0, xmax)
ax.grid(True, axis="y", color=GRID, lw=0.5, alpha=0.4)
for spine in ax.spines.values():
    spine.set_color(GRID)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(loc="upper right", framealpha=0.0, fontsize=10, labelcolor=FG)

fig.tight_layout()
fig.savefig("aggregation_summaries.png", dpi=200, bbox_inches="tight",
            transparent=True, edgecolor="none")
print("Saved aggregation_summaries.png")
print(f"  median={median:.2f}  geomean={geomean:.2f}  mean={mean:.2f}  p90={p90:.2f}")
