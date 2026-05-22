"""Generate PWLA figures for slides 27-30 of T03 (LP/MIP Modeling).

Produces four PNGs sharing one dark-theme palette (transparent background):

  pwla_inner_vs_outer.png   slide 27 — three panels: true f, outer (tangent), inner (chord)
  pwla_lambda.png           slide 28 — chord-based PWL with breakpoints and one
                                       interior convex-combination point annotated
  pwla_tangent_envelope.png slide 29 — tangent lower envelope on f(x)=x^2, epigraph shaded
  pwla_step.png             slide 30 — step function (tiered pricing) on three intervals

Why this exists. The PWLA section of the deck needs a single visual story
because the inner-vs-outer choice is geometric — students have to *see*
which side of f the approximation lies on. The other figures (lambda
breakpoints, tangent envelope, step) reuse the same axis style so the eye
recognises the running example across four slides.

Usage. `python assets/gen_pwla.py` from the slides/ directory regenerates
all four PNGs into assets/. Re-run after any palette change.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent

BG = "none"
FG = "#e0e0e0"
CURVE = "#9ad0f5"        # true function (light blue)
OUTER = "#7fbf7b"        # outer / tangent (green) — lies below for convex f
INNER = "#e69138"        # inner / chord  (orange) — lies above for convex f
BREAKPT = "#c27ba0"      # breakpoint markers (mauve)
GRID = "#37474f"
EPI = "#7fbf7b"          # epigraph shading

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.transparent": True,
    "text.color": FG,
    "axes.labelcolor": FG,
    "axes.titlecolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "font.size": 12,
})


def style_ax(ax, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.grid(True, color=GRID, alpha=0.4, linewidth=0.7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(FG)
    ax.set_xlabel("x")
    ax.set_ylabel("y")


def f(x):
    return x ** 2


def f_motiv(x):
    """Motivating example for the PWLA section opener — smooth, non-convex,
    not linearisable by any of the earlier tricks. Multiple oscillations
    with a mild upward drift so the curve has visible bumps the chord
    approximation has to track."""
    return 2.0 * np.sin(x) + x / 3.0


def f_motiv_dd(x):
    """Second derivative of f_motiv — drives adaptive breakpoint spacing."""
    return -2.0 * np.sin(x)


def adaptive_breakpoints(a, b, n, ddf, eps=0.2):
    """Equidistribute breakpoints by cumulative sqrt(|f''|).

    Chord error on a segment of width h is bounded by h^2 |f''| / 8, so the
    error is balanced across segments when each carries equal cumulative
    sqrt(|f''|). A small floor eps keeps spacing finite where f''=0.
    """
    xs = np.linspace(a, b, 4001)
    w = np.sqrt(np.abs(ddf(xs)) + eps)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (w[:-1] + w[1:]) * np.diff(xs))])
    targets = np.linspace(0.0, cum[-1], n)
    return np.interp(targets, cum, xs)


# ---------- Section opener: motivating example ----------
def motivating():
    """Two figures sharing the same axes — the smooth function alone, then
    the same function overlaid with a chord-PWL on equally spaced
    breakpoints. Used on the first two slides of the PWLA section to
    motivate the approximation visually before any encoding."""
    x_fine = np.linspace(0, 12, 500)
    y_true = f_motiv(x_fine)
    breakpoints = adaptive_breakpoints(0.0, 12.0, 8, f_motiv_dd)
    y_bp = f_motiv(breakpoints)
    xlim = (-0.5, 12.5)
    ylim = (-1.5, 6.0)

    # Opaque dark background so the two figures can be swapped via reveal.js
    # fragments at the same slide position without text bleed-through.
    SLIDE_BG = "#191919"

    # Figure 1: smooth function alone
    fig, ax = plt.subplots(figsize=(7.5, 4.6), constrained_layout=True,
                           facecolor=SLIDE_BG)
    ax.set_facecolor(SLIDE_BG)
    ax.plot(x_fine, y_true, color=CURVE, lw=3,
            label=r"$f(x) = 2\sin(x) + x/3$")
    style_ax(ax, xlim, ylim)
    ax.set_title("How do we model this in a MIP?")
    ax.legend(loc="upper left", facecolor=(0, 0, 0, 0.3), edgecolor=FG,
              labelcolor=FG)
    out = OUT / "pwla_motivating.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=SLIDE_BG,
                transparent=False)
    plt.close(fig)
    print(f"wrote {out.name}")

    # Figure 2: function + chord PWL on the same axes
    fig, ax = plt.subplots(figsize=(7.5, 4.6), constrained_layout=True,
                           facecolor=SLIDE_BG)
    ax.set_facecolor(SLIDE_BG)
    ax.plot(x_fine, y_true, color=CURVE, lw=2.4, alpha=0.5,
            label=r"$f(x)$")
    ax.plot(breakpoints, y_bp, color=INNER, lw=3.0,
            label="PWL approximation")
    ax.scatter(breakpoints, y_bp, color=BREAKPT, s=70, zorder=5,
               label=r"breakpoints $(X_k, Y_k)$")
    style_ax(ax, xlim, ylim)
    ax.set_title("Piecewise-linear approximation")
    ax.legend(loc="upper left", facecolor=(0, 0, 0, 0.3), edgecolor=FG,
              labelcolor=FG)
    out = OUT / "pwla_motivating_pwl.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=SLIDE_BG,
                transparent=False)
    plt.close(fig)
    print(f"wrote {out.name}")


# ---------- Slide 27: inner vs outer ----------
def inner_vs_outer():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), constrained_layout=True)

    x_fine = np.linspace(0, 4, 400)
    y_true = f(x_fine)
    breakpoints = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    y_bp = f(breakpoints)

    xlim = (-0.3, 4.3)
    ylim = (-1.5, 17.5)

    # Panel 1 — true function
    ax = axes[0]
    ax.plot(x_fine, y_true, color=CURVE, lw=3, label=r"$f(x)=x^2$")
    ax.scatter(breakpoints, y_bp, color=BREAKPT, s=45, zorder=5,
               label="breakpoints")
    style_ax(ax, xlim, ylim)
    ax.set_title("Smooth $f$")
    ax.legend(loc="upper left", facecolor=(0, 0, 0, 0.3), edgecolor=FG,
              labelcolor=FG)

    # Panel 2 — outer (tangent) lies below
    ax = axes[1]
    ax.plot(x_fine, y_true, color=CURVE, lw=2.5, alpha=0.35,
            label=r"$f(x)=x^2$")
    tangents = [2 * xk * x_fine - xk ** 2 for xk in breakpoints]
    for tan in tangents:
        ax.plot(x_fine, tan, color=OUTER, lw=1.0, alpha=0.55)
    env = np.max(tangents, axis=0)
    ax.plot(x_fine, env, color=OUTER, lw=3.0, label="outer (tangent)")
    ax.scatter(breakpoints, y_bp, color=BREAKPT, s=45, zorder=5)
    style_ax(ax, xlim, ylim)
    ax.set_title("Outer — lies below $f$")
    ax.legend(loc="upper left", facecolor=(0, 0, 0, 0.3), edgecolor=FG,
              labelcolor=FG)

    # Panel 3 — inner (chord) lies above
    ax = axes[2]
    ax.plot(x_fine, y_true, color=CURVE, lw=2.5, alpha=0.35,
            label=r"$f(x)=x^2$")
    ax.plot(breakpoints, y_bp, color=INNER, lw=3.0, label="inner (chord)")
    ax.scatter(breakpoints, y_bp, color=BREAKPT, s=45, zorder=5)
    style_ax(ax, xlim, ylim)
    ax.set_title("Inner — lies above $f$")
    ax.legend(loc="upper left", facecolor=(0, 0, 0, 0.3), edgecolor=FG,
              labelcolor=FG)

    out = OUT / "pwla_inner_vs_outer.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"wrote {out.name}")


# ---------- Slide 28: lambda formulation ----------
LAMBDA_EXAMPLES = [
    # (segment k, lambda_k, lambda_{k+1}, absolute label position, ha)
    # Active segment is X_3=(5.11, -0.14) -> X_4=(7.10, 3.83), steep upward.
    # Labels are placed on alternating sides so they never overlap.
    (3, 0.7, 0.3, (3.9, 2.3), "center"),   # mid point: label upper-left
    (3, 0.9, 0.1, (5.4, -1.1), "center"),  # near X_3: label below
    (3, 0.1, 0.9, (8.0, 1.0), "left"),     # near X_4: label below-right
]


def _draw_lambda_figure(filename, n_examples, title):
    SLIDE_BG = "#191919"
    fig, ax = plt.subplots(figsize=(7.5, 4.6), constrained_layout=True,
                           facecolor=SLIDE_BG)
    ax.set_facecolor(SLIDE_BG)

    x_fine = np.linspace(0, 12, 500)
    y_true = f_motiv(x_fine)
    breakpoints = adaptive_breakpoints(0.0, 12.0, 8, f_motiv_dd)
    y_bp = f_motiv(breakpoints)

    ax.plot(x_fine, y_true, color=CURVE, lw=2.2, alpha=0.5,
            label=r"$f(x)$")
    ax.plot(breakpoints, y_bp, color=INNER, lw=2.8,
            label=r"$\lambda$-formulation PWL")
    ax.scatter(breakpoints, y_bp, color=BREAKPT, s=70, zorder=5,
               label=r"breakpoints $(X_k, Y_k)$")

    # Highlight the active segment used by the examples (all share segment k).
    if n_examples > 0:
        k = LAMBDA_EXAMPLES[0][0]
        xk, xk1 = breakpoints[k], breakpoints[k + 1]
        yk, yk1 = f_motiv(xk), f_motiv(xk1)
        ax.plot([xk, xk1], [yk, yk1], color="#ffffff", lw=5.5, alpha=0.25,
                zorder=2)

    for k, lam_k, lam_k1, label_xy, ha in LAMBDA_EXAMPLES[:n_examples]:
        xk, xk1 = breakpoints[k], breakpoints[k + 1]
        yk, yk1 = f_motiv(xk), f_motiv(xk1)
        x_q = lam_k * xk + lam_k1 * xk1
        y_q = lam_k * yk + lam_k1 * yk1
        ax.scatter([x_q], [y_q], color="#ffffff", s=80, zorder=6,
                   edgecolor="#1e1e2e", linewidth=1.5)
        ax.annotate(rf"$\lambda_{k} = {lam_k:.1f},\ \lambda_{k+1} = {lam_k1:.1f}$",
                    xy=(x_q, y_q), xytext=label_xy,
                    color=FG, fontsize=11, ha=ha,
                    arrowprops=dict(arrowstyle="->", color=FG, lw=1.2))

    style_ax(ax, (-0.5, 12.5), (-1.5, 6.0))
    ax.set_title(title)
    ax.legend(loc="upper left", facecolor=(0, 0, 0, 0.3), edgecolor=FG,
              labelcolor=FG)

    out = OUT / filename
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=SLIDE_BG,
                transparent=False)
    plt.close(fig)
    print(f"wrote {out.name}")


def lambda_breakpoints():
    """Three progressive figures showing how convex combinations slide a
    point along the active segment. Re-uses f_motiv so the visual flows
    from the opening two slides without a function change."""
    title = r"Active segment: at most two adjacent $\lambda_k$ non-zero"
    _draw_lambda_figure("pwla_lambda.png", 1, title)
    _draw_lambda_figure("pwla_lambda_2.png", 2, title)
    _draw_lambda_figure("pwla_lambda_3.png", 3, title)


def lambda_breakpoints_hull():
    """Same breakpoints as lambda_breakpoints, but with the convex hull of
    all breakpoints shaded — the LP-relaxation feasible region when the
    adjacency constraint is dropped. A non-adjacent interior point is
    plotted inside the hull to make the failure mode concrete."""
    from scipy.spatial import ConvexHull

    SLIDE_BG = "#191919"
    fig, ax = plt.subplots(figsize=(7.5, 4.6), constrained_layout=True,
                           facecolor=SLIDE_BG)
    ax.set_facecolor(SLIDE_BG)

    x_fine = np.linspace(0, 12, 500)
    y_true = f_motiv(x_fine)
    breakpoints = adaptive_breakpoints(0.0, 12.0, 8, f_motiv_dd)
    y_bp = f_motiv(breakpoints)

    pts = np.column_stack([breakpoints, y_bp])
    hull = ConvexHull(pts)
    hull_pts = pts[hull.vertices]

    ax.fill(hull_pts[:, 0], hull_pts[:, 1], color=BREAKPT, alpha=0.18,
            label="convex hull of breakpoints", zorder=1)
    ax.plot(x_fine, y_true, color=CURVE, lw=2.2, alpha=0.5,
            label=r"$f(x)$")
    ax.plot(breakpoints, y_bp, color=INNER, lw=2.8,
            label=r"$\lambda$-formulation PWL")
    ax.scatter(breakpoints, y_bp, color=BREAKPT, s=70, zorder=5,
               label=r"breakpoints $(X_k, Y_k)$")

    # A non-adjacent combination: weight on breakpoints 1 and 6 only.
    i, j = 1, 6
    lam_i, lam_j = 0.55, 0.45
    x_q = lam_i * breakpoints[i] + lam_j * breakpoints[j]
    y_q = lam_i * y_bp[i] + lam_j * y_bp[j]
    ax.plot([breakpoints[i], breakpoints[j]],
            [y_bp[i], y_bp[j]], color="#ffffff", lw=1.5, alpha=0.5,
            linestyle="--", zorder=3)
    ax.scatter([x_q], [y_q], color="#ffffff", s=80, zorder=6,
               edgecolor="#1e1e2e", linewidth=1.5)
    ax.annotate(rf"$\lambda_{i} = {lam_i:.2f},\ \lambda_{j} = {lam_j:.2f}$",
                xy=(x_q, y_q), xytext=(x_q + 0.5, y_q - 1.2),
                color=FG, fontsize=11, ha="left",
                arrowprops=dict(arrowstyle="->", color=FG, lw=1.2))

    style_ax(ax, (-0.5, 12.5), (-1.5, 6.0))
    ax.set_title(r"Without adjacency: any point in the convex hull is feasible")
    ax.legend(loc="upper left", facecolor=(0, 0, 0, 0.3), edgecolor=FG,
              labelcolor=FG, fontsize=9)

    out = OUT / "pwla_lambda_hull.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=SLIDE_BG,
                transparent=False)
    plt.close(fig)
    print(f"wrote {out.name}")


# ---------- Slide 29: tangent lower envelope ----------
def tangent_envelope():
    fig, ax = plt.subplots(figsize=(7.5, 4.6), constrained_layout=True)

    x_fine = np.linspace(0, 4, 400)
    y_true = f(x_fine)
    support = np.array([0.5, 1.5, 2.5, 3.5])
    y_sup = f(support)

    tangents = [2 * xk * x_fine - xk ** 2 for xk in support]
    env = np.max(tangents, axis=0)

    # Shade the epigraph (LP-feasible region above the envelope)
    ax.fill_between(x_fine, env, 17.5, color=EPI, alpha=0.10,
                    label="LP-feasible epigraph")

    for tan in tangents:
        ax.plot(x_fine, tan, color=OUTER, lw=1.0, alpha=0.5)
    ax.plot(x_fine, env, color=OUTER, lw=3.0, label="lower envelope")
    ax.plot(x_fine, y_true, color=CURVE, lw=2.2, alpha=0.7,
            label=r"$f(x)=x^2$")
    ax.scatter(support, y_sup, color=BREAKPT, s=60, zorder=5,
               label="support points $X_k$")

    style_ax(ax, (-0.3, 4.3), (-1.5, 17.5))
    ax.set_title("Epigraph as intersection of tangent half-planes")
    ax.legend(loc="upper left", facecolor=(0, 0, 0, 0.3), edgecolor=FG,
              labelcolor=FG, fontsize=10)

    out = OUT / "pwla_tangent_envelope.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"wrote {out.name}")


# ---------- Slide 30: step function ----------
def step_function():
    fig, ax = plt.subplots(figsize=(7.5, 4.6), constrained_layout=True)

    # Tiered pricing: three closed-open intervals
    tiers = [
        (0, 50, 1.20, "tier 1"),
        (50, 200, 0.95, "tier 2"),
        (200, 500, 0.80, "tier 3"),
    ]

    for i, (L, U, v, label) in enumerate(tiers):
        ax.hlines(v, L, U, color=INNER, lw=3.5, zorder=4,
                  label=label if i == 0 else None)
        # closed-on-left
        ax.scatter([L], [v], color=INNER, s=70, zorder=5)
        # open-on-right
        ax.scatter([U], [v], color="#1e1e2e", s=70, zorder=5,
                   edgecolor=INNER, linewidth=2.2)

    for (L, _, _, _) in tiers:
        ax.axvline(L, color=GRID, linestyle=":", alpha=0.6)
    ax.axvline(tiers[-1][1], color=GRID, linestyle=":", alpha=0.6)

    # Mark a current x in tier 2
    x_now = 120
    v_now = 0.95
    ax.scatter([x_now], [v_now], color=BREAKPT, s=90, zorder=6,
               label=fr"$x={x_now},\ f(x)={v_now}$")
    ax.vlines(x_now, 0.4, v_now, color=BREAKPT, lw=1.5, alpha=0.5,
              linestyle="--")

    style_ax(ax, (-25, 525), (0.5, 1.45))
    ax.set_xlabel("x (units)")
    ax.set_ylabel("$f(x)$ (price per unit)")
    ax.set_title("Step function — tiered pricing, three intervals")
    ax.legend(loc="upper right", facecolor=(0, 0, 0, 0.3), edgecolor=FG,
              labelcolor=FG, fontsize=10)

    out = OUT / "pwla_step.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    motivating()
    lambda_breakpoints()
    lambda_breakpoints_hull()
    inner_vs_outer()
    tangent_envelope()
