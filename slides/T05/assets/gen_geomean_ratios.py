"""Generate the geomean-for-ratios figure (geomean_ratios.png).

What this contains
  A single log-scaled axis of speedup ratios for a symmetric two-instance example
  (one 2x faster, one 2x slower). The two ratios 0.5x and 2x sit symmetrically
  around parity (1x) on a log axis. Marked: the geometric mean (at 1x, the true
  center) and the arithmetic mean (at 1.25x, pulled toward the larger ratio).

Why it exists
  The slide demonstrates that ratios must be averaged geometrically. On a log axis
  the geomean is visibly the center of the symmetric ratios, while the arithmetic
  mean drifts right, which is exactly the bias that makes "average of ratios"
  self-contradictory under inversion.

How to use
  python gen_geomean_ratios.py  ->  geomean_ratios.png (dark, transparent)

When it should change
  Keep the example symmetric (r and 1/r) so the geomean lands exactly on parity
  and the arithmetic-mean bias is unambiguous.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG = "none"
FG = "#e0e0e0"
GRID = "#555555"
DOT = "#4ea8de"
C_GEO = "#7fbf7b"   # geometric mean (correct)
C_ARI = "#e06666"   # arithmetic mean (biased)

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "text.color": FG,
    "axes.labelcolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "font.size": 12,
})

ratios = [0.5, 2.0]
arith = sum(ratios) / len(ratios)          # 1.25
geo = (ratios[0] * ratios[1]) ** 0.5       # 1.0

fig, ax = plt.subplots(figsize=(7.8, 2.7))
ax.set_xscale("log")

ax.axvline(1.0, color=GRID, lw=1.0, ls=":", alpha=0.7)
ax.scatter(ratios, [0, 0], s=130, color=DOT, zorder=4)
ax.annotate("2x faster", (0.5, 0), textcoords="offset points", xytext=(0, 14),
            ha="center", fontsize=11, color=DOT)
ax.annotate("2x slower", (2.0, 0), textcoords="offset points", xytext=(0, 14),
            ha="center", fontsize=11, color=DOT)

ax.axvline(geo, color=C_GEO, lw=2.4, label=f"geometric mean = {geo:.2f}x  (equal)")
ax.axvline(arith, color=C_ARI, lw=2.4, ls="--",
           label=f"arithmetic mean = {arith:.2f}x  (biased)")

ax.set_xlim(0.4, 2.6)
ax.minorticks_off()
ax.set_xticks([0.5, 1.0, 2.0])
ax.set_xticklabels(["0.5x", "1x", "2x"])
ax.xaxis.set_minor_formatter(plt.NullFormatter())
ax.set_yticks([])
ax.set_ylim(-0.6, 0.9)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.legend(loc="upper center", framealpha=0.0, fontsize=10, labelcolor=FG,
          ncol=2, bbox_to_anchor=(0.5, 1.18))

fig.tight_layout()
fig.savefig("geomean_ratios.png", dpi=200, bbox_inches="tight",
            transparent=True, edgecolor="none")
print("Saved geomean_ratios.png")
print(f"  arithmetic mean = {arith:.3f}, geometric mean = {geo:.3f}")
