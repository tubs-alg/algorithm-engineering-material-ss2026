"""
Generate the black-box-optimization explainer for `_04-tuning-search.qmd`
(slide "Tuning is black-box optimization") as a MULTI-STEP animation.

The point this figure makes
---------------------------
Configuration is black-box optimization with TWO compounding difficulties:
  1. the box is opaque -- no formula, no gradient to optimize over; and
  2. even at a FIXED input, the output is not a single number. Each run is a
     *draw* from a distribution P(y | x) controlled by the parameters. Run the
     same config again, get a different number (cf. the seed-variance slide).
So we don't just lack a gradient: every "value" we read is one noisy sample of a
distribution we can only estimate by paying for more (expensive) runs.

What this contains (and non-goals)
-----------------------------------
A sequence of frames `blackbox_{1..N}.png` (+ `.svg`):
  - LEFT  : the configuration x (input arrows: num_workers, linearization_level,
            ...), the SAME every frame -- we are not changing the config here;
  - CENTER: the BLACK BOX -- one full solver run over the whole benchmark set;
  - RIGHT : an objective panel. Each frame runs the box once more on the SAME x
            and drops one more sample y_k onto the axis, so the dots accumulate
            and trace out the hidden distribution P(y | x) (drawn faint). The
            empirical mean updates as samples come in.
  - a "run again" loop arrow: same x, new draw.
Clicking through the frames is repeated sampling of one configuration: the spread
is the message.
NON-goals: not a real optimizer, not a real benchmark; the config and the sample
values are illustrative toy data.

How to use it
-------------
    python gen_blackbox.py
writes `blackbox_1.png` ... `_N.png` (+ `.svg`). In the slide, stack them in an
`.r-stack` with one `.fragment` per frame (one frame per click).

CRITICAL (r-stack alignment)
----------------------------
Fade overlays demand PIXEL-IDENTICAL frames or the shared scaffold jumps between
clicks. Every frame uses the SAME figsize, the SAME fixed axes limits, axis off,
and is saved with `bbox_inches=None` (full canvas) -- never the rcParams "tight"
crop. Per-frame differences are added dots / the moving mean line only; the
scaffold (box, arrows, density curve, labels) is byte-for-byte identical.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- dark-theme palette (transparent fig, light fg) ----
C_FG = "#e6e6e6"
C_MUTED = "#9aa6b5"
C_GRID = "#3a4757"
C_BOX = "#16202b"        # the black box fill
C_BOXEDGE = "#5b6b7e"
C_IN = "#4ea8de"         # configuration / input flow
C_OUT = "#7fbf7b"        # objective / output flow
C_DIST = "#7fbf7b"       # hidden distribution
C_SAMP = "#9ad0f5"       # samples taken so far
C_NEW = "#ff8c42"        # the sample drawn this frame
C_LOOP = "#b48ead"       # "run again" loop

# Illustrative draws from P(y | x): SAME config, different numbers each run.
SAMPLES = [72.0, 95.0, 64.0, 131.0, 81.0]
JITTER = [0.55, 1.05, 0.35, 0.80, 0.70]   # x-offset of each dot inside the panel
N_FRAMES = len(SAMPLES)

# input-arrow rows (the knobs), fixed every frame: (label, value)
KNOBS = [
    ("num_workers", "8"),
    ("linearization_level", "max_lp"),
    ("LNS settings", "on"),
    ("presolve toggles", "2"),
]

# ---- fixed geometry (axis units; identical every frame) ----
XLIM = (0.0, 10.0)
YLIM = (0.0, 6.4)

BOX = dict(x0=3.55, y0=3.30, x1=5.55, y1=5.30)
KNOB_YS = [4.98, 4.52, 4.06, 3.60]
ARROW_X0, ARROW_X1 = 2.45, BOX["x0"]
MIDY = (BOX["y0"] + BOX["y1"]) / 2.0
OUT_X0, OUT_X1 = BOX["x1"], 6.80

# objective panel (right): objective on the vertical axis, density bulges right
PANEL_X0 = 6.95           # baseline / objective axis
PANEL_X1 = 9.55
OBJ_LO, OBJ_HI = 40.0, 150.0
PY_LO, PY_HI = 1.65, 5.55   # axis-y span the objective range maps onto


def _obj_to_y(obj):
    return PY_LO + (np.asarray(obj) - OBJ_LO) / (OBJ_HI - OBJ_LO) * (PY_HI - PY_LO)


def _density(obj):
    """Hidden, right-skewed P(y | x) (runtimes are skewed). Lognormal in (obj-30)."""
    t = np.asarray(obj) - 30.0
    mu, sig = np.log(40.0) + 0.45 ** 2, 0.45
    pdf = np.exp(-(np.log(t) - mu) ** 2 / (2 * sig ** 2)) / (t * sig * np.sqrt(2 * np.pi))
    return pdf


def _arrow(ax, xy0, xy1, color, lw=2.2, alpha=1.0, ls="-", rad=0.0,
           mut=14, zorder=3, shrink=0.0):
    ax.add_patch(FancyArrowPatch(
        xy0, xy1, arrowstyle="-|>", mutation_scale=mut, lw=lw, color=color,
        alpha=alpha, linestyle=ls, zorder=zorder, shrinkA=shrink, shrinkB=shrink,
        connectionstyle=f"arc3,rad={rad}"))


def _box(ax, x0, y0, x1, y1, fc, ec, lw=2.0, rounding=0.06, alpha=1.0, z=2):
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0,
        boxstyle=f"round,pad=0,rounding_size={rounding}",
        linewidth=lw, edgecolor=ec, facecolor=fc, alpha=alpha, zorder=z))


def _render(frame_idx):
    """frame_idx is 1-based: how many times we've run the SAME config."""
    fig, ax = plt.subplots(figsize=(9.6, 6.0))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.axis("off")

    # ---------- the black box ----------
    _box(ax, BOX["x0"], BOX["y0"], BOX["x1"], BOX["y1"], C_BOX, C_BOXEDGE, lw=2.2)
    cx = (BOX["x0"] + BOX["x1"]) / 2.0
    ax.text(cx, 4.86, "BLACK BOX", ha="center", va="center", color=C_MUTED,
            fontsize=10, fontweight="bold", zorder=4)
    ax.text(cx, 4.42, "one solver run", ha="center", va="center", color=C_FG,
            fontsize=14, fontweight="bold", zorder=4)
    ax.text(cx, 3.98, "full solve over the\nwhole benchmark set", ha="center",
            va="center", color=C_FG, fontsize=10.5, zorder=4)
    ax.text(cx, 3.50, "no formula · no gradient", ha="center", va="center",
            color=C_IN, fontsize=9.5, fontstyle="italic", zorder=4)

    # ---------- inputs: the SAME configuration x every run ----------
    ax.text((ARROW_X0 + 0.05), 5.78, "configuration  $x$", ha="center",
            va="center", color=C_IN, fontsize=13, fontweight="bold", zorder=4)
    ax.text((ARROW_X0 + 0.05), 5.45, "(identical every run)", ha="center",
            va="center", color=C_MUTED, fontsize=9.5, fontstyle="italic", zorder=4)
    for (label, value), y in zip(KNOBS, KNOB_YS):
        ax.text(ARROW_X0 - 0.18, y, label, ha="right", va="center", color=C_FG,
                fontsize=10.5, family="DejaVu Sans Mono", zorder=4)
        _arrow(ax, (ARROW_X0, y), (ARROW_X1, y), C_IN, lw=2.0)
        ax.text((ARROW_X0 + ARROW_X1) / 2.0, y + 0.15, value, ha="center",
                va="bottom", color=C_IN, fontsize=10, fontweight="bold", zorder=5)

    # ---------- output arrow: one draw y_k ----------
    _arrow(ax, (OUT_X0, MIDY), (OUT_X1, MIDY), C_OUT, lw=2.6, mut=18)
    ax.text((OUT_X0 + OUT_X1) / 2.0 + 0.05, MIDY + 0.34, "$y_k$", ha="center",
            va="bottom", color=C_OUT, fontsize=13, fontweight="bold", zorder=4)
    ax.text((OUT_X0 + OUT_X1) / 2.0 + 0.05, MIDY - 0.30, "one\ndraw", ha="center",
            va="top", color=C_MUTED, fontsize=8.5, zorder=4)

    # ---------- "run again" loop: same x, new draw (above the box) ----------
    loop = FancyArrowPatch(
        (cx + 0.62, BOX["y1"] + 0.18), (cx - 0.62, BOX["y1"] + 0.18),
        arrowstyle="-|>", mutation_scale=13, lw=1.7, color=C_LOOP,
        linestyle=(0, (5, 3)), zorder=4,
        connectionstyle="arc3,rad=0.85", shrinkA=2, shrinkB=2)
    ax.add_patch(loop)
    ax.text(cx, BOX["y1"] + 0.72, "run again → new draw", ha="center",
            va="bottom", color=C_LOOP, fontsize=9.5, zorder=4)

    # ---------- objective panel: P(y | x) revealed by sampling ----------
    # hidden true distribution (faint), same every frame
    og = np.linspace(OBJ_LO, OBJ_HI, 300)
    dens = _density(og)
    dens = dens / dens.max() * (PANEL_X1 - PANEL_X0)   # scale to panel width
    yg = _obj_to_y(og)
    ax.fill_betweenx(yg, PANEL_X0, PANEL_X0 + dens, color=C_DIST, alpha=0.13,
                     lw=0, zorder=1)
    ax.plot(PANEL_X0 + dens, yg, color=C_DIST, lw=1.6, alpha=0.55, zorder=2)
    # objective axis
    ax.plot([PANEL_X0, PANEL_X0], [PY_LO - 0.1, PY_HI + 0.25], color=C_GRID,
            lw=1.4, zorder=2)
    ax.text(PANEL_X0 + (PANEL_X1 - PANEL_X0) * 0.55, PY_HI + 0.55,
            "objective  $y$", ha="center", va="bottom", color=C_OUT,
            fontsize=12, fontweight="bold", zorder=4)
    ax.text(PANEL_X0 + (PANEL_X1 - PANEL_X0) * 0.55, PY_HI + 0.22,
            "hidden distribution  $P(y\\,|\\,x)$", ha="center", va="bottom",
            color=C_MUTED, fontsize=9, fontstyle="italic", zorder=4)
    ax.text(PANEL_X0 - 0.12, PY_LO - 0.05, "better", ha="right", va="center",
            color=C_MUTED, fontsize=8.5, zorder=4)
    ax.text(PANEL_X0 - 0.12, PY_HI + 0.05, "worse", ha="right", va="center",
            color=C_MUTED, fontsize=8.5, zorder=4)

    # samples drawn so far
    for i in range(frame_idx):
        is_new = (i == frame_idx - 1)
        yi = _obj_to_y(SAMPLES[i])
        ax.scatter([PANEL_X0 + JITTER[i]], [yi],
                   s=150 if is_new else 80,
                   c=C_NEW if is_new else C_SAMP,
                   edgecolors="#2a1605" if is_new else "#10202e",
                   linewidths=1.0, zorder=6)
        if is_new:
            ax.text(PANEL_X0 + JITTER[i] + 0.22, yi, f"{SAMPLES[i]:.0f}",
                    ha="left", va="center", color=C_NEW, fontsize=10.5,
                    fontweight="bold", zorder=6)

    # empirical mean so far (updates per frame)
    m = _obj_to_y(np.mean(SAMPLES[:frame_idx]))
    ax.plot([PANEL_X0, PANEL_X1 + 0.05], [m, m], color=C_SAMP, lw=1.3,
            ls="--", alpha=0.8, zorder=5)
    ax.text(PANEL_X1 + 0.05, m, " mean\n so far", ha="left", va="center",
            color=C_SAMP, fontsize=8.5, zorder=5)

    # ---------- the two compounding problems (bottom) ----------
    by = 1.02
    ax.text(0.55, by, "1.", ha="left", va="center", color=C_IN,
            fontsize=12, fontweight="bold", zorder=4)
    ax.text(0.95, by, "no gradient: the box is opaque, nothing to differentiate",
            ha="left", va="center", color=C_FG, fontsize=11, zorder=4)
    ax.text(0.55, by - 0.55, "2.", ha="left", va="center", color=C_NEW,
            fontsize=12, fontweight="bold", zorder=4)
    ax.text(0.95, by - 0.55,
            "each $y_k$ is a noisy sample of $P(y\\,|\\,x)$: same input, different "
            "number every run",
            ha="left", va="center", color=C_FG, fontsize=11, zorder=4)

    ax.text(PANEL_X1 + 0.30, PY_LO - 0.55, f"run {frame_idx} of {N_FRAMES}",
            ha="right", va="center", color=C_MUTED, fontsize=9.5, zorder=4)

    stem = os.path.join(OUT_DIR, f"blackbox_{frame_idx}")
    for ext in ("png", "svg"):
        fig.savefig(f"{stem}.{ext}", bbox_inches=None)
    plt.close(fig)
    return f"blackbox_{frame_idx}.png"


def main() -> None:
    plt.rcParams.update({
        "savefig.dpi": 200,
        "savefig.transparent": True,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "font.family": "DejaVu Sans",
        "text.color": C_FG,
    })
    for k in range(1, N_FRAMES + 1):
        print(f"  wrote {_render(k)}")


if __name__ == "__main__":
    main()
