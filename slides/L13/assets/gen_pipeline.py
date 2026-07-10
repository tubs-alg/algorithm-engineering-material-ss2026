"""uncertainty_pipeline: where uncertainty enters the decision pipeline.

For `_05-diagnosis.qmd`. Box chain (true world state -> measurement ->
forecast -> optimization model -> planned decision -> execution) with the four
error mechanisms attached to the interfaces where they strike. Box widths are
measured from actual rendered text extents (single-line labels vary a lot in
length), not guessed as equal fractions.
Run: python gen_pipeline.py
"""

import os

import _theme as T
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = os.path.dirname(os.path.abspath(__file__))

LABELS = [
    "true world state",
    "measurement / sensing",
    "forecast",
    "optimization model",
    "planned decision",
    "execution / control",
]

# (label text, index of the box whose entrance it strikes)
ERRORS = [
    ("measurement\nerror", 1),
    ("forecast\nerror", 2),
    ("model / parameter\nerror", 3),
    ("implementation\nerror", 5),
]

FONTSIZE = 18
PAD_X = 0.55
GAP = 0.75
ARROW_MARGIN = 0.18  # clearance between arrow tip/tail and box border
H = 0.72
Y = 1.65
SIDE_MARGIN = 0.35


def measure_widths(labels, fontsize) -> list:
    """Render each label once to measure its width in inches at this fontsize."""
    fig = plt.figure(figsize=(1, 1))
    renderer = fig.canvas.get_renderer()
    widths = []
    for label in labels:
        t = fig.text(0, 0, label, fontsize=fontsize)
        bbox = t.get_window_extent(renderer=renderer)
        widths.append(bbox.width / fig.dpi)
        t.remove()
    plt.close(fig)
    return widths


def main() -> None:
    T.init_style()

    text_widths = measure_widths(LABELS, FONTSIZE)
    box_widths = [w + 2 * PAD_X for w in text_widths]
    total_width = 2 * SIDE_MARGIN + sum(box_widths) + GAP * (len(LABELS) - 1)
    total_height = 3.35

    fig, ax = plt.subplots(figsize=(total_width, total_height))
    ax.set_xlim(0, total_width)
    ax.set_ylim(0, total_height)
    ax.axis("off")

    x = SIDE_MARGIN
    spans = []
    for label, w in zip(LABELS, box_widths):
        box = FancyBboxPatch((x, Y), w, H,
                             boxstyle="round,pad=0.03,rounding_size=0.05",
                             lw=2, facecolor=T.NAVY, edgecolor=T.BLUE)
        ax.add_patch(box)
        ax.text(x + w / 2, Y + H / 2, label, ha="center", va="center",
                fontsize=FONTSIZE, color=T.FG)
        spans.append((x, x + w))
        x += w + GAP

    for i in range(len(LABELS) - 1):
        x1 = spans[i][1] + ARROW_MARGIN
        x2 = spans[i + 1][0] - ARROW_MARGIN
        ax.add_patch(FancyArrowPatch((x1, Y + H / 2), (x2, Y + H / 2),
                                     arrowstyle="-|>", mutation_scale=18,
                                     lw=2.4, color=T.BLUE,
                                     shrinkA=0, shrinkB=0))

    for text, box_idx in ERRORS:
        ex = sum(spans[box_idx]) / 2
        ax.text(ex, 0.34, text, ha="center", va="center", fontsize=15.5,
                color=T.ORANGE)
        ax.add_patch(FancyArrowPatch((ex, 0.86), (ex, Y - 0.14),
                                     arrowstyle="-|>", mutation_scale=17,
                                     lw=2.0, color=T.ORANGE,
                                     shrinkA=0, shrinkB=0))

    T.save(fig, os.path.join(OUT, "uncertainty_pipeline"), pad=0.1)


if __name__ == "__main__":
    main()
