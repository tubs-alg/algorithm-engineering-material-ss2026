"""
Generate the model-based-search explainer for `_04-tuning-search.qmd`
(slide "Model-based search: learn where to look next") as a MULTI-STEP animation.

What this contains (and non-goals)
-----------------------------------
A sequence of frames `surrogate_acquisition_{1..N}.png` (+ `.svg`) showing
Bayesian optimization advancing one sample at a time over a 1-D parameter:
  top    -- the (hidden) true objective, the evaluations so far, and the cheap
            SURROGATE (posterior mean + uncertainty band);
  bottom -- the ACQUISITION function built from that surrogate, with a marker on
            the next configuration it picks (its peak).
Frame k shows k+1 observations and the point the acquisition wants next; frame
k+1 has added exactly that point. So clicking through the frames shows the
uncertainty band collapse as samples accumulate -- the whole idea of the method.
NON-goals: not a working optimizer and not tied to CP-SAT; one fixed toy surface.

Why it exists
-------------
The three-panel `search_grid_random_tpe.png` shows model-based search
*concentrates* near the optimum, but not *why*. This animation supplies the
mechanism the slide names -- surrogate (exploit) + acquisition (explore) -- and,
per Dominik's request, makes the interval-update dynamic explicit across clicks.

How to use it
-------------
    python gen_surrogate_acquisition.py
writes `surrogate_acquisition_1.png` ... `_N.png` (+ `.svg`). In the slide, stack
them in an `.r-stack` with one `.fragment` per frame (one frame per click).
Self-contained: a tiny RBF Gaussian-process posterior is computed inline
(numpy only) -- no scikit-learn/GPy dependency.

CRITICAL (r-stack alignment)
----------------------------
Fade overlays demand PIXEL-IDENTICAL frames or the shared content jumps between
clicks. So every frame uses the SAME figsize, the SAME fixed axes limits, and is
saved with `bbox_inches=None` (full canvas) -- never the rcParams "tight" crop,
which would size each frame to its own content. Acquisition is min-max
normalized per frame so the bottom axis scale is constant across frames.

When it should change
---------------------
Adjust `N_FRAMES`, the initial `X_INIT`, or `truth()` if the slide's emphasis
moves. Keep an un-sampled valley early so the first acquisition visibly points
into high uncertainty -- that is the exploration half of the story.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- dark-theme palette (transparent fig, light fg) ----
C_FG = "#e6e6e6"
C_MUTED = "#9aa6b5"
C_GRID = "#3a4757"
C_TRUTH = "#6b7585"     # hidden true objective: muted (we don't get to see it)
C_MEAN = "#4ea8de"      # surrogate posterior mean
C_BAND = "#4ea8de"      # uncertainty band (alpha)
C_OBS = "#9ad0f5"       # observed evaluations
C_NEWOBS = "#ff8c42"    # the evaluation added since the previous frame
C_ACQ = "#ff8c42"       # acquisition function
C_NEXT = "#7fbf7b"      # next point the acquisition picks

X_INIT = np.array([0.08, 0.95])   # two cold-start evals -> very uncertain frame 1
N_FRAMES = 5                       # frames 1..5: 2,3,4,5,6 observations
KAPPA = 2.0                        # exploration weight in the LCB acquisition
ELL = 0.12                         # RBF length scale
# Fixed axis box, identical for every frame (pixel-aligned r-stack overlay):
YLIM_TOP = (-1.7, 2.0)


def truth(x: np.ndarray) -> np.ndarray:
    """Hidden, expensive objective over [0,1] (lower is better)."""
    return np.sin(3.0 * np.pi * x) * 0.5 + (x - 0.55) ** 2 * 2.2 - 0.15 * x


def _rbf(a: np.ndarray, b: np.ndarray, sf: float = 1.0) -> np.ndarray:
    d = a[:, None] - b[None, :]
    return sf ** 2 * np.exp(-0.5 * (d / ELL) ** 2)


def _gp_posterior(x_obs, y_obs, x_grid, noise=1e-4):
    """Standard GP regression posterior (mean, std) with an RBF kernel."""
    k = _rbf(x_obs, x_obs) + noise * np.eye(len(x_obs))
    k_s = _rbf(x_obs, x_grid)
    k_ss = _rbf(x_grid, x_grid)
    k_inv = np.linalg.inv(k)
    mean = k_s.T @ k_inv @ y_obs
    cov = k_ss - k_s.T @ k_inv @ k_s
    std = np.sqrt(np.clip(np.diag(cov), 1e-9, None))
    return mean, std


def _acquisition(mean, std):
    """Lower-confidence-bound for MINIMIZATION, flipped so its MAX = next point.

    We want low predicted objective (exploit) and high uncertainty (explore):
    score = -(mean - kappa*std). Min-max normalized to [0,1] so the bottom axis
    scale is identical across frames.
    """
    raw = -(mean - KAPPA * std)
    lo, hi = raw.min(), raw.max()
    return (raw - lo) / (hi - lo + 1e-12)


def _bo_sequence():
    """Replay BO: start from X_INIT, repeatedly add the acquisition's argmax.

    Returns a list of frames; frame k carries the observations visible at step k,
    the surrogate over the grid, the acquisition, and the next x it picks.
    """
    x_grid = np.linspace(0, 1, 400)
    x_obs = list(X_INIT)
    frames = []
    for _ in range(N_FRAMES):
        xo = np.array(x_obs)
        yo = truth(xo)
        mean, std = _gp_posterior(xo, yo, x_grid)
        acq = _acquisition(mean, std)
        nxt = float(x_grid[int(np.argmax(acq))])
        frames.append(dict(x_obs=xo.copy(), y_obs=yo.copy(), mean=mean,
                           std=std, acq=acq, nxt=nxt))
        x_obs.append(nxt)
    return x_grid, frames


def _render(x_grid, frame, idx, prev_nxt):
    """Render one frame to a fixed-size, fixed-limits figure (pixel-aligned)."""
    fig, (ax, axa) = plt.subplots(
        2, 1, figsize=(9.2, 6.4), height_ratios=[3, 1.25], sharex=True,
    )
    fig.subplots_adjust(left=0.10, right=0.97, top=0.90, bottom=0.10, hspace=0.08)

    mean, std = frame["mean"], frame["std"]
    x_obs, y_obs = frame["x_obs"], frame["y_obs"]

    # ---- top: truth, surrogate, observations ----
    ax.plot(x_grid, truth(x_grid), color=C_TRUTH, lw=1.6, ls=":",
            label="true objective (hidden)")
    ax.fill_between(x_grid, mean - 2 * std, mean + 2 * std, color=C_BAND,
                    alpha=0.18, lw=0, label="surrogate uncertainty (±2σ)")
    ax.plot(x_grid, mean, color=C_MEAN, lw=2.2, label="surrogate mean")

    # split observations: the one added since the previous frame is highlighted
    if prev_nxt is None:
        is_new = np.zeros(len(x_obs), dtype=bool)
    else:
        is_new = np.isclose(x_obs, prev_nxt, atol=1e-6)
    ax.scatter(x_obs[~is_new], y_obs[~is_new], s=70, c=C_OBS,
               edgecolors="#10202e", linewidths=0.8, zorder=5,
               label="evaluations so far")
    if is_new.any():
        ax.scatter(x_obs[is_new], y_obs[is_new], s=110, c=C_NEWOBS,
                   edgecolors="#2a1605", linewidths=1.0, zorder=6,
                   label="just evaluated")

    ax.axvline(frame["nxt"], color=C_NEXT, lw=1.4, ls="--", alpha=0.9, zorder=2)
    ax.set_ylabel("objective  (lower is better)", color=C_FG, fontsize=12)
    ax.set_title(f"Step {idx}: {len(x_obs)} evaluations — surrogate tightens, "
                 "acquisition picks the next run", color=C_FG, fontsize=14, pad=10)
    leg = ax.legend(loc="upper center", fontsize=9.5, ncol=2, frameon=True,
                    handletextpad=0.4, columnspacing=1.2)
    leg.get_frame().set_facecolor((0.10, 0.14, 0.20, 0.88))
    leg.get_frame().set_edgecolor(C_GRID)
    for t in leg.get_texts():
        t.set_color(C_FG)

    # ---- bottom: acquisition ----
    acq = frame["acq"]
    axa.plot(x_grid, acq, color=C_ACQ, lw=2.0)
    axa.fill_between(x_grid, 0.0, acq, color=C_ACQ, alpha=0.16, lw=0)
    axa.axvline(frame["nxt"], color=C_NEXT, lw=1.4, ls="--", alpha=0.9)
    axa.scatter([frame["nxt"]], [1.0], s=120, marker="v", c=C_NEXT,
                edgecolors="#10261a", linewidths=0.8, zorder=5, clip_on=False)
    axa.annotate("next", xy=(frame["nxt"], 1.0),
                 xytext=(frame["nxt"] + 0.015, 0.86), ha="left", va="center",
                 color=C_NEXT, fontsize=11)
    axa.set_ylabel("acquisition", color=C_FG, fontsize=12)
    axa.set_xlabel("parameter value", color=C_FG, fontsize=12)
    axa.set_yticks([])

    # fixed limits on BOTH axes so every frame is pixel-identical
    ax.set_ylim(*YLIM_TOP)
    axa.set_ylim(0.0, 1.08)
    for a in (ax, axa):
        a.set_xlim(0, 1)
        a.tick_params(colors=C_MUTED, labelsize=10)
        for s in a.spines.values():
            s.set_color(C_GRID)

    stem = os.path.join(OUT_DIR, f"surrogate_acquisition_{idx}")
    for ext in ("png", "svg"):
        # bbox_inches=None (NOT the rcParams tight crop) -> identical canvas size
        fig.savefig(f"{stem}.{ext}", bbox_inches=None)
    plt.close(fig)
    return f"surrogate_acquisition_{idx}.png"


def main() -> None:
    plt.rcParams.update({
        "savefig.dpi": 200,
        "savefig.transparent": True,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "font.family": "DejaVu Sans",
        "text.color": C_FG,
    })

    x_grid, frames = _bo_sequence()
    prev_nxt = None
    for i, frame in enumerate(frames, start=1):
        name = _render(x_grid, frame, i, prev_nxt)
        print(f"  wrote {name}")
        prev_nxt = frame["nxt"]


if __name__ == "__main__":
    main()
