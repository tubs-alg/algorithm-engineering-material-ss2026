"""Generate the relative-vs-absolute aggregation figure (relative_vs_absolute.png).

What this contains
  One small benchmark (six instances, two solvers A and B) shown two ways, stacked:
    top    = relative view: speedup factor max(A/B, B/A) per instance
    bottom = absolute view: |runtime A - runtime B| in seconds per instance
  Instances are colored by category and the SAME color is used in both panels, so
  the eye can see that different instances dominate each view.

Why it exists
  Relative and absolute aggregation give opposite verdicts on the same data, and
  both are misleading. Sub-0.1 s runtimes sit in the measurement-noise floor
  (process startup, timer resolution), so their ratios explode and dominate any
  relative average. Conversely, a handful of large instances dominate any
  absolute sum, drowning out everything small. The same trap appears with MIP
  optimality tolerances: a near-zero optimum makes the relative gap blow up.

How to use
  python gen_relative_vs_absolute.py  ->  relative_vs_absolute.png (dark, transparent)

When it should change
  Keep A/B values consistent with the table on the slide. Keep at least two sub-0.1 s
  instances (so the relative view is dominated by noise) and at least one large
  instance (so the absolute view is dominated by scale).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG = "none"
FG = "#e0e0e0"
GRID = "#555555"
NOISY = "#e69138"   # sub-0.1 s: dominated by measurement noise
LARGE = "#4ea8de"   # reliably timed instances

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "text.color": FG,
    "axes.labelcolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "font.size": 12,
})

LABELS = ["I1", "I2", "I3", "I4", "I5", "I6"]
A = [0.02, 0.05, 0.04, 2.0, 60.0, 120.0]
B = [0.20, 0.30, 0.01, 2.2, 45.0, 90.0]

NOISE_FLOOR = 0.1
noisy = [min(a, b) < NOISE_FLOOR for a, b in zip(A, B)]
colors = [NOISY if n else LARGE for n in noisy]

speedup = [max(a / b, b / a) for a, b in zip(A, B)]
absdiff = [abs(a - b) for a, b in zip(A, B)]

x = range(len(LABELS))
fig, (ax_rel, ax_abs) = plt.subplots(2, 1, figsize=(7.6, 4.5))

# --- relative view ---
ax_rel.bar(x, speedup, color=colors, alpha=0.9)
ax_rel.axhline(1.0, color=FG, lw=1.0, ls=":", alpha=0.5)
ax_rel.set_ylabel("speedup factor\nmax(A/B, B/A)")
ax_rel.set_ylim(0, max(speedup) * 1.35)
ax_rel.set_title("Relative view: the sub-0.1 s instances dominate",
                 fontsize=12, fontweight="bold", color=NOISY)
# Plain label above the I2 bar (no arrow).
ax_rel.text(1.35, speedup[1] + max(speedup) * 0.04,
            "noise floor:\nratios are artifacts", fontsize=10, color=NOISY,
            ha="center", va="bottom")

# --- absolute view ---
ax_abs.bar(x, absdiff, color=colors, alpha=0.9)
ax_abs.set_ylabel("|runtime A - B|  (s)")
ax_abs.set_ylim(0, max(absdiff) * 1.35)
ax_abs.set_title("Absolute view: the two large instances dominate",
                 fontsize=12, fontweight="bold", color=LARGE)
# Plain label above the I5 bar (no arrow).
ax_abs.text(4.0, absdiff[4] + max(absdiff) * 0.04,
            "scale buries\neverything small", fontsize=10, color=LARGE,
            ha="center", va="bottom")

for ax in (ax_rel, ax_abs):
    ax.set_xticks(list(x))
    ax.set_xticklabels(LABELS)
    ax.grid(True, axis="y", color=GRID, lw=0.5, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

fig.tight_layout()
fig.savefig("relative_vs_absolute.png", dpi=200, bbox_inches="tight",
            transparent=True, edgecolor="none")
print("Saved relative_vs_absolute.png")
gm = 1.0
for a, b in zip(A, B):
    gm *= a / b
gm = gm ** (1 / len(A))
print(f"  geomean A/B = {gm:.3f}  -> relative says A is {1/gm:.2f}x faster")
print(f"  total A = {sum(A):.2f}s, total B = {sum(B):.2f}s -> absolute says B faster by {sum(A)-sum(B):.1f}s")
