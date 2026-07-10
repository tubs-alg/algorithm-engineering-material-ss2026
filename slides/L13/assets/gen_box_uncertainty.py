"""box_uncertainty: the box set drawn as a constraint of distributions.

For `_06-robust.qmd`. Motivates the box uncertainty set as the naive choice by
drawing the uncertain constraint

    a_1 x_1 + a_2 x_2 <= b

with a density plot in place of every coefficient. Two build steps:

* box_dist_plain.*: each coefficient shown as its own distribution.
* box_dist_worstcase.*: red bars mark the tail the box selects for each
  coefficient at once -- 95% quantile for the a's (large -> constraint tighter),
  5% quantile for b (small -> less room). Taking every worst tail simultaneously
  is the box, and is what makes it overly pessimistic.

The two figures share an identical layout so the deck can r-stack them and fade
the worst-case bars in on click.

Run: python gen_box_uncertainty.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

Z95 = 1.6449  # standard-normal 95% (and, negated, 5%) quantile

# Each uncertain coefficient: label, mean, sd, worst-case tail direction, fill.
#   tail "upper" -> worst case is a large value (the a's on the LHS)
#   tail "lower" -> worst case is a small value (the bound b on the RHS)
COEFFS = [
    dict(label=r"$a_1$", mu=2.0, sd=0.42, tail="upper", color=T.BLUE),
    dict(label=r"$a_2$", mu=1.4, sd=0.30, tail="upper", color=T.BLUE),
    dict(label=r"$b$", mu=10.0, sd=1.30, tail="lower", color=T.GOLD),
]

# Figure-fraction geometry: [left, width] of each density panel, left to right.
PANELS = [(0.030, 0.205), (0.325, 0.205), (0.620, 0.205)]
PANEL_BOTTOM, PANEL_HEIGHT = 0.16, 0.66
# Operators typeset on a full-figure overlay, placed in the gaps between panels.
OPERATORS = [(0.272, r"$\cdot\,x_1\;+$"), (0.567, r"$\cdot\,x_2\;\leq$")]


def gaussian(x: np.ndarray, mu: float, sd: float) -> np.ndarray:
    return np.exp(-0.5 * ((x - mu) / sd) ** 2)


def draw_panel(ax, spec: dict, worstcase: bool) -> None:
    mu, sd, tail, color = spec["mu"], spec["sd"], spec["tail"], spec["color"]
    x = np.linspace(mu - 3.6 * sd, mu + 3.6 * sd, 400)
    y = gaussian(x, mu, sd)

    ax.fill_between(x, 0, y, color=color, alpha=0.32, lw=0)
    ax.plot(x, y, color=color, lw=2.0)
    ax.axhline(0.0, color=T.MUTED, lw=1.0)

    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(0, 1.28)
    ax.axis("off")

    if not worstcase:
        return

    q = mu + (Z95 if tail == "upper" else -Z95) * sd
    if tail == "upper":
        tail_mask = x >= q
        pct = "95%"
    else:
        tail_mask = x <= q
        pct = "5%"

    ax.fill_between(x[tail_mask], 0, y[tail_mask], color=T.RED, alpha=0.30, lw=0)
    ax.plot([q, q], [0, 1.06], color=T.RED, lw=2.6)
    ax.scatter([q], [0], s=42, color=T.RED, zorder=5, clip_on=False)
    ax.text(q, 1.15, pct, color=T.RED, ha="center", va="bottom", fontsize=13)


def render(worstcase: bool, stem: str) -> None:
    T.init_style(base_fontsize=13)
    fig = plt.figure(figsize=(11.0, 3.0))

    for (left, width), spec in zip(PANELS, COEFFS):
        ax = fig.add_axes([left, PANEL_BOTTOM, width, PANEL_HEIGHT])
        draw_panel(ax, spec, worstcase)
        # Coefficient name sits inside its distribution, level with the
        # x_1 / x_2 operators (op_y = PANEL_BOTTOM + 0.34 * PANEL_HEIGHT).
        ax.text(0.5, 0.34, spec["label"], transform=ax.transAxes,
                ha="center", va="center", fontsize=30, color=T.FG)

    over = fig.add_axes([0, 0, 1, 1])
    over.set_xlim(0, 1)
    over.set_ylim(0, 1)
    over.axis("off")
    op_y = PANEL_BOTTOM + 0.34 * PANEL_HEIGHT
    for xpos, text in OPERATORS:
        over.text(xpos, op_y, text, ha="center", va="center",
                  fontsize=26, color=T.FG)

    T.save(fig, os.path.join(OUT, stem), pad=0.05)


def main() -> None:
    render(worstcase=False, stem="box_dist_plain")
    render(worstcase=True, stem="box_dist_worstcase")


if __name__ == "__main__":
    main()
