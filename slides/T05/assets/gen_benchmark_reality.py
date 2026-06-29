"""
Generate the "benchmarking reality" figure sequence for `_01-benchmarking-pitfalls.qmd`.

What this contains (and non-goals)
-----------------------------------
Five PNG/SVG figures that walk from the fantasy of clean runtime curves to the
messy reality of censored point samples:

    reality_1_wish.png      three algorithms, a clean and constant ranking
    reality_2_nfl.png       the curves actually cross (no-free-lunch)
    reality_3_samples.png   we only have noisy point samples, and they overlap
    reality_4_sparse.png    instances are unevenly distributed -> wide CI where sparse
    reality_5_timeouts.png  some runs time out (crosses on the limit line)

All five share ONE synthetic ground truth (three algorithms A/B/C with
crossing runtime means), so the sequence reads as the same study getting more
honest panel by panel. NON-goals: this is an illustration of the *shape* of the
problem, not a real benchmark; the numbers are synthetic-but-plausible.

Why it exists
-------------
The pitfalls section needs a visual build-up that motivates everything after it:
why a single ranking is wishful, why means lie, why censored data is the rule.
A reader who has seen these five panels already understands why the next section
needs cactus / performance / split plots.

How to use it
-------------
    python gen_benchmark_reality.py
writes reality_1_wish .. reality_5_timeouts (.png + .svg) next to this script.

When it should change
---------------------
Tune REAL_PARAMS (the crossing means), SIGMA (sample spread), TIME_LIMIT_S, or
the sampling grids. Keep the three invariants the panels rely on: (1) the ideal
ranking never crosses, (2) the real means cross twice inside the n-range, and
(3) at the largest n every algorithm has at least a chance of timing out.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- dark-theme palette (matches the course decks: transparent fig, light fg) ----
C_FG = "#e6e6e6"        # light foreground: titles, labels, ticks
C_MUTED = "#9aa6b5"     # secondary text / captions
C_GRID = "#3a4757"      # grid lines
C_LIMIT = "#ff8c42"     # time-limit line (warm orange)
C_GREY = "#5d6b7a"      # greyed-out / under-sampled points
COLORS = {"A": "#9ad0f5", "B": "#7fbf7b", "C": "#c792ea"}  # blue / green / violet

# Real means: coef * exp(n / scale). Chosen so A wins small n, B wins medium,
# C wins large (crossings at n ~ 81 and n ~ 140).
REAL_PARAMS = {"A": (1.0, 38.0), "B": (3.0, 78.0), "C": (9.0, 150.0)}
# Ideal means: coef * n**1.3 -- scalar multiples, so the ranking never crosses.
IDEAL_PARAMS = {"A": 0.05, "B": 0.11, "C": 0.20}

N_LO, N_HI = 20, 255
SIGMA = 0.42           # log-scale spread of per-instance samples (high on purpose)
TAIL_DF = 2.5          # Student-t dof: low -> heavy right tail (rare huge runs)
N_PTS = 140            # instances per algorithm (one run each): dense enough to
                       # see a trend, noisy enough to block a clean verdict
TIME_LIMIT_S = 90.0
SEED = 11
NS_SEED = 111          # separate stream for instance sizes (so panels 3 & 5 share them)

# All five panels share one scale so they overlay mentally as the story builds.
FIGSIZE = (8.8, 6.2)
XLIM = (N_LO - 6, N_HI + 6)
YLIM = (1.3, 260.0)        # log seconds; puts the 90 s time limit at ~80% height
                           # (curves/heavy-tail samples above the top simply run off it)


def mean_real(n: np.ndarray, key: str) -> np.ndarray:
    coef, scale = REAL_PARAMS[key]
    return coef * np.exp(n / scale)


def mean_ideal(n: np.ndarray, key: str) -> np.ndarray:
    return IDEAL_PARAMS[key] * np.power(n, 1.3)


def _style() -> None:
    plt.rcParams.update({
        "savefig.dpi": 200,
        "savefig.transparent": True,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "font.family": "DejaVu Sans",
        "text.color": C_FG,
    })


def _new_ax():
    """A log-runtime axis with the shared scale used by every panel."""
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.set_xlabel("instance size  n", color=C_FG, fontsize=13)
    ax.set_ylabel("runtime (s, log scale)", color=C_FG, fontsize=13)
    ax.set_yscale("log")
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    for spine in ax.spines.values():
        spine.set_color(C_GRID)
    ax.tick_params(colors=C_MUTED)
    ax.grid(True, which="both", color=C_GRID, linewidth=0.5, alpha=0.45)
    return fig, ax


def _even_ns() -> np.ndarray:
    """Shared instance sizes for panels 3 and 5 (same instances, then censored)."""
    rng_n = np.random.default_rng(NS_SEED)
    return np.sort(rng_n.uniform(N_LO, N_HI, N_PTS))


def _legend(ax, **kw):
    leg = ax.legend(framealpha=0.0, fontsize=12, labelcolor=C_FG, **kw)
    return leg


def _save(fig, name: str) -> None:
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(OUT_DIR, f"{name}.{ext}"),
                    bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    print(f"wrote {name}.png / .svg")


def _samples(rng: np.random.Generator, ns: np.ndarray) -> dict[str, np.ndarray]:
    """One noisy sample per algorithm at each n.

    Multiplier is log-Student-t, not lognormal: combinatorial-solver runtimes
    have heavy right tails (Gomes et al.), so a few runs take orders of magnitude
    longer than the median. That heavy tail is what produces realistic timeouts.
    """
    return {k: mean_real(ns, k) * np.exp(SIGMA * rng.standard_t(TAIL_DF, size=ns.shape))
            for k in COLORS}


# ----------------------------------------------------------------------------- #
# Panel 1: the wish -- a clean, constant ranking.
# ----------------------------------------------------------------------------- #
def fig_wish() -> None:
    fig, ax = _new_ax()
    n = np.linspace(N_LO, N_HI, 300)
    for key in ("A", "B", "C"):
        ax.plot(n, mean_ideal(n, key), color=COLORS[key], linewidth=3.0,
                label=f"Algorithm {key}")
    _legend(ax, loc="upper left")
    _save(fig, "reality_1_wish")


# ----------------------------------------------------------------------------- #
# Panel 2: no-free-lunch -- the curves cross.
# ----------------------------------------------------------------------------- #
def _crossing(key_lo: str, key_hi: str) -> float:
    """n where mean_real(key_lo) == mean_real(key_hi) (key_lo cheaper below it)."""
    c1, s1 = REAL_PARAMS[key_lo]
    c2, s2 = REAL_PARAMS[key_hi]
    return float(np.log(c2 / c1) / (1.0 / s1 - 1.0 / s2))


def fig_nfl() -> None:
    fig, ax = _new_ax()
    n = np.linspace(N_LO, N_HI, 300)
    x_ab = _crossing("A", "B")   # ~81: A best below, B best above
    x_bc = _crossing("B", "C")   # ~179: B best below, C best above

    # faint "who wins here" bands
    for lo, hi, key in [(N_LO, x_ab, "A"), (x_ab, x_bc, "B"), (x_bc, N_HI, "C")]:
        ax.axvspan(lo, hi, color=COLORS[key], alpha=0.07)
        ax.text((lo + hi) / 2, YLIM[1] * 0.6, f"{key} best", color=COLORS[key],
                fontsize=12, ha="center", va="top")
    for x in (x_ab, x_bc):
        ax.axvline(x, color=C_MUTED, linewidth=1.0, linestyle=":")

    for key in ("A", "B", "C"):
        ax.plot(n, mean_real(n, key), color=COLORS[key], linewidth=3.0,
                label=f"Algorithm {key}")
    _legend(ax, loc="lower right")
    _save(fig, "reality_2_nfl")


# ----------------------------------------------------------------------------- #
# Panel 3: only noisy point samples, and they overlap.
# ----------------------------------------------------------------------------- #
def fig_samples() -> None:
    fig, ax = _new_ax()
    rng = np.random.default_rng(SEED)
    ns = _even_ns()
    s = _samples(rng, ns)
    for key in ("A", "B", "C"):
        ax.scatter(ns, s[key], s=18, color=COLORS[key], alpha=1.0,
                   edgecolors="none", label=f"Algorithm {key}")
    _legend(ax, loc="lower right")
    _save(fig, "reality_3_samples")


# ----------------------------------------------------------------------------- #
# Panel 4: uneven instances -> confidence band balloons where data is sparse.
# ----------------------------------------------------------------------------- #
def _sigma_local(n: np.ndarray) -> np.ndarray:
    """Effective spread: small where we sampled densely, large in the gap."""
    return 0.28 + 0.6 * np.exp(-(((n - 120.0) / 33.0) ** 2))


def fig_sparse() -> None:
    fig, ax = _new_ax()
    rng = np.random.default_rng(SEED + 3)
    gap_lo, gap_hi = 72.0, 168.0   # the under-sampled middle

    ax.axvspan(gap_lo, gap_hi, color=C_GREY, alpha=0.12)
    ax.text((gap_lo + gap_hi) / 2, YLIM[1] * 0.6, "few / no instances here",
            color=C_MUTED, fontsize=12, ha="center", va="top")

    n = np.linspace(N_LO, N_HI, 300)
    half = _sigma_local(n)
    for key in ("A", "B", "C"):
        mu = mean_real(n, key)
        ax.fill_between(n, mu * np.exp(-half), mu * np.exp(half),
                        color=COLORS[key], alpha=0.13, linewidth=0)
        ax.plot(n, mu, color=COLORS[key], linewidth=1.4, linestyle="--",
                alpha=0.55, label=f"Algorithm {key}")

    # uneven sampling: dense edges, almost empty middle
    half_pts = N_PTS // 2
    ns_dense = np.concatenate([rng.uniform(N_LO, gap_lo - 2, half_pts),
                               rng.uniform(gap_hi + 2, N_HI, half_pts)])
    ns_gap = rng.uniform(gap_lo + 4, gap_hi - 4, 8)
    for ns, in_gap in [(ns_dense, False), (ns_gap, True)]:
        s = _samples(rng, ns)
        for key in ("A", "B", "C"):
            ax.scatter(ns, s[key], s=20,
                       color=C_GREY if in_gap else COLORS[key],
                       alpha=1.0, edgecolors="none")
    _legend(ax, loc="lower right")
    _save(fig, "reality_4_sparse")


# ----------------------------------------------------------------------------- #
# Panel 5: timeouts -- censored runs become crosses on the limit line.
# ----------------------------------------------------------------------------- #
def fig_timeouts() -> None:
    fig, ax = _new_ax()
    rng = np.random.default_rng(SEED)   # same seed + sizes as panel 3: same runs, censored
    ns = _even_ns()
    s = _samples(rng, ns)

    # everything above the limit is unobserved territory
    ax.axhspan(TIME_LIMIT_S, YLIM[1], color=C_LIMIT, alpha=0.05)
    ax.axhline(TIME_LIMIT_S, color=C_LIMIT, linewidth=1.8, linestyle="--")
    ax.text(N_LO, TIME_LIMIT_S * 1.08, "time limit", color=C_LIMIT,
            fontsize=12, va="bottom", ha="left")

    for key in ("A", "B", "C"):
        t = s[key]
        solved = t <= TIME_LIMIT_S
        ax.scatter(ns[solved], t[solved], s=18, color=COLORS[key], alpha=1.0,
                   edgecolors="none", label=f"Algorithm {key}")
        ax.scatter(ns[~solved], np.full((~solved).sum(), TIME_LIMIT_S),
                   s=42, color=COLORS[key], marker="x", linewidths=1.6, alpha=0.85)
    _legend(ax, loc="lower right")
    _save(fig, "reality_5_timeouts")


def main() -> None:
    _style()
    fig_wish()
    fig_nfl()
    fig_samples()
    fig_sparse()
    fig_timeouts()


if __name__ == "__main__":
    main()
