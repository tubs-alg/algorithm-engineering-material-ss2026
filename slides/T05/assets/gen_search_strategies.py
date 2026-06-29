"""
Generate the centerpiece figure for `_04-tuning-search.qmd`:
three search strategies (grid / random / model-based) spending the SAME budget
of evaluations over the SAME 2-D response surface.

What this contains (and non-goals)
-----------------------------------
A single 3-panel PNG/SVG, `search_grid_random_tpe.png`. Each panel shows the
same loss surface (one important parameter on x, one near-irrelevant one on y)
with the points an evaluation budget lands on, plus a top marginal histogram of
where the IMPORTANT parameter got sampled. That marginal is the Bergstra & Bengio
argument made visible: grid spends its budget on only a few distinct x-values,
random and model-based sample many. NON-goals: this is an illustration of *how*
the strategies spend a budget, not a benchmark of which wins (the surface is a
fixed toy, not a CP-SAT run).

Why it exists
-------------
`_04` walks left-to-right through grid -> random -> model-based. The slide needs
one honest picture where the only thing that changes between panels is the
sampler. We get that for free by driving all three panels with the actual Optuna
samplers (GridSampler / RandomSampler / TPESampler) over one objective -- the
same `optuna.create_study(sampler=...)` swap the `_05` tutorial teaches. So the
figure and the code example describe literally the same mechanism.

How to use it
-------------
    python gen_search_strategies.py
writes `search_grid_random_tpe.png` (+ `.svg`) next to this script.

When it should change
---------------------
Tweak `BUDGET`, `GRID_PER_AXIS`, or `loss()` if the pedagogy shifts (e.g. a
different effective-dimensionality story). Keep the surface anisotropic
(important x, flat y) -- that anisotropy is the whole point of the marginals.
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
import optuna

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- dark-theme palette (matches the course decks: transparent fig, light fg) ----
C_FG = "#e6e6e6"        # light foreground: titles, labels, ticks
C_MUTED = "#9aa6b5"     # secondary text / captions
C_GRID = "#3a4757"      # contour lines
C_POINT = "#9ad0f5"     # static evaluation points (grid / random)
C_OPT = "#7fbf7b"       # true optimum marker (green)
C_BEST = "#ff8c42"      # model-based incumbent / best-found (warm orange)
C_BAR = "#4ea8de"       # marginal histogram bars
SURFACE_CMAP = "mako" if "mako" in plt.colormaps() else "viridis"

BUDGET = 36             # evaluations per strategy (fair budget across all three)
GRID_PER_AXIS = 6       # 6 x 6 = 36, so grid exactly spends the budget
SEED = 7

# Optuna is chatty; we only want the sampled points, not a log per trial.
optuna.logging.set_verbosity(optuna.logging.WARNING)


def loss(x: float, y: float) -> float:
    """Toy response surface over [0,1]^2.

    Anisotropic on purpose: x is the IMPORTANT parameter (steep, with a little
    multimodality so model-based search has something to learn), y is nearly
    irrelevant (a shallow basin). The global optimum sits at roughly (0.78, 0.55).
    Lower is better -- think PAR2 / runtime.
    """
    x_term = 0.6 * (1.0 - np.exp(-((x - 0.78) ** 2) / 0.02))  # sharp well in x
    ripple = 0.18 * (np.sin(3.2 * np.pi * x) ** 2)            # secondary dips in x
    y_term = 0.12 * (y - 0.55) ** 2                            # shallow -> y barely matters
    return float(x_term + ripple + y_term)


def _objective(trial: optuna.Trial) -> float:
    x = trial.suggest_float("x", 0.0, 1.0)
    y = trial.suggest_float("y", 0.0, 1.0)
    return loss(x, y)


def _run(sampler) -> tuple[np.ndarray, np.ndarray]:
    """Run BUDGET trials with `sampler`; return sampled (x, y) in trial order."""
    study = optuna.create_study(direction="minimize", sampler=sampler)
    study.optimize(_objective, n_trials=BUDGET, show_progress_bar=False)
    xs = np.array([t.params["x"] for t in study.trials])
    ys = np.array([t.params["y"] for t in study.trials])
    return xs, ys


def _samplers():
    grid_axis = np.linspace(0.06, 0.94, GRID_PER_AXIS)
    search_space = {"x": list(grid_axis), "y": list(grid_axis)}
    return [
        ("Grid search", optuna.samplers.GridSampler(search_space, seed=SEED),
         "every combination: only 6 distinct x"),
        ("Random search", optuna.samplers.RandomSampler(seed=SEED),
         "36 distinct x: denser on what matters"),
        ("Model-based (TPE)", optuna.samplers.TPESampler(seed=SEED, n_startup_trials=8),
         "learns to concentrate near the optimum"),
    ]


def _draw_surface(ax) -> None:
    gx = np.linspace(0, 1, 220)
    gy = np.linspace(0, 1, 220)
    gxx, gyy = np.meshgrid(gx, gy)
    zz = np.vectorize(loss)(gxx, gyy)
    ax.contourf(gxx, gyy, zz, levels=22, cmap=SURFACE_CMAP, alpha=0.55, zorder=0)
    ax.contour(gxx, gyy, zz, levels=8, colors=C_GRID, linewidths=0.6, alpha=0.7, zorder=1)


def main() -> None:
    plt.rcParams.update({
        "savefig.dpi": 200,
        "savefig.transparent": True,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "font.family": "DejaVu Sans",
        "text.color": C_FG,
    })

    # true optimum, for a reference marker in every panel
    gx = np.linspace(0, 1, 400)
    gy = np.linspace(0, 1, 400)
    gxx, gyy = np.meshgrid(gx, gy)
    zz = np.vectorize(loss)(gxx, gyy)
    oi = np.unravel_index(np.argmin(zz), zz.shape)
    opt_x, opt_y = gxx[oi], gyy[oi]

    panels = _samplers()
    fig = plt.figure(figsize=(15, 5.6))
    gs = fig.add_gridspec(
        2, 3, height_ratios=[1, 5.0], hspace=0.06, wspace=0.17,
        left=0.04, right=0.985, top=0.82, bottom=0.12,
    )

    for col, (title, sampler, caption) in enumerate(panels):
        xs, ys = _run(sampler)
        ax = fig.add_subplot(gs[1, col])
        axm = fig.add_subplot(gs[0, col], sharex=ax)

        _draw_surface(ax)

        # true optimum reference (same in all three)
        ax.scatter([opt_x], [opt_y], marker="*", s=320, c=C_OPT,
                   edgecolors="#10261a", linewidths=0.8, zorder=5,
                   label="true optimum")
        if col == 0:
            leg = ax.legend(loc="lower left", fontsize=10, frameon=True,
                            handletextpad=0.3, borderpad=0.4)
            leg.get_frame().set_facecolor((0.10, 0.14, 0.20, 0.82))
            leg.get_frame().set_edgecolor(C_GRID)
            for t in leg.get_texts():
                t.set_color(C_FG)

        if col < 2:
            # static strategies: all points equal
            ax.scatter(xs, ys, s=55, c=C_POINT, edgecolors="#10202e",
                       linewidths=0.6, alpha=0.95, zorder=4)
        else:
            # model-based: color by trial order, mark the best-found incumbent
            order = np.arange(len(xs))
            ax.scatter(xs, ys, s=58, c=order, cmap="autumn_r",
                       edgecolors="#2a1605", linewidths=0.6, zorder=4)
            losses = np.array([loss(x, y) for x, y in zip(xs, ys)])
            bi = int(np.argmin(losses))
            ax.scatter([xs[bi]], [ys[bi]], marker="D", s=120, facecolors="none",
                       edgecolors=C_BEST, linewidths=2.2, zorder=6)
            ax.annotate(
                "best found", xy=(xs[bi], ys[bi]), xytext=(0.06, 0.10),
                textcoords="axes fraction", color=C_BEST, fontsize=11,
                arrowprops=dict(arrowstyle="->", color=C_BEST, lw=1.3,
                                connectionstyle="arc3,rad=0.2"),
            )

        # top marginal: how the IMPORTANT parameter x was sampled
        axm.hist(xs, bins=np.linspace(0, 1, 21), color=C_BAR,
                 edgecolor="#10202e", linewidth=0.4)
        axm.axvline(opt_x, color=C_OPT, lw=1.4, ls="--", alpha=0.9)
        axm.set_yticks([])
        axm.tick_params(axis="x", labelbottom=False, length=0)
        for s in ("top", "right", "left"):
            axm.spines[s].set_visible(False)
        axm.spines["bottom"].set_color(C_GRID)
        axm.set_title(title, color=C_FG, fontsize=16, pad=8)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("important parameter  $x$", color=C_FG, fontsize=12)
        if col == 0:
            ax.set_ylabel("near-irrelevant parameter  $y$", color=C_FG, fontsize=12)
        ax.set_xticks([0, 0.5, 1.0])
        ax.set_yticks([0, 0.5, 1.0])
        ax.tick_params(colors=C_MUTED, labelsize=10)
        for s in ax.spines.values():
            s.set_color(C_GRID)
        ax.text(0.5, -0.165, caption, transform=ax.transAxes, ha="center",
                va="top", color=C_MUTED, fontsize=11.5, style="italic")

    fig.text(0.5, 0.95, "Same surface, same budget of 36 evaluations — only the sampler changes",
             ha="center", color=C_FG, fontsize=14)
    fig.text(0.5, 0.905,
             "Top strips: where the budget actually sampled the important parameter $x$ "
             "(dashed green = optimum's $x$)",
             ha="center", color=C_MUTED, fontsize=10.5)

    out = os.path.join(OUT_DIR, "search_grid_random_tpe")
    for ext in ("png", "svg"):
        path = f"{out}.{ext}"
        fig.savefig(path, bbox_inches="tight", pad_inches=0.06)
        print(f"  wrote {os.path.basename(path)} ({os.path.getsize(path) / 1024:.0f}K)")
    plt.close(fig)


if __name__ == "__main__":
    main()
