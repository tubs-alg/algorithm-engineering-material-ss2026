"""Shared dark-theme matplotlib rcParams for slide figures.

Imported by gen_jsp_figs.py, gen_rostering_figs.py, gen_vrp_figs.py so the
three families share one visual style. Mirrors the convention used in
week01-l01 and week02-t01: transparent background, light grey foreground,
keep the bright accent colors of the data layer untouched.
"""
from __future__ import annotations

import matplotlib.pyplot as plt

# Foreground / accent colors — kept in sync with T01 (gen_amdahl.py et al.)
BG = "none"
FG = "#e0e0e0"
GRID = "#555555"
EDGE = "#888888"      # neutral bar edge that reads on dark
MUTED = "#999999"     # secondary text (captions, source notes)
GOOD = "#54A24B"
BAD = "#E45756"
ACCENT = "#4ea8de"


def apply():
    plt.rcParams.update({
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.edgecolor": FG,
        "axes.labelcolor": FG,
        "axes.linewidth": 0.8,
        "xtick.color": FG,
        "ytick.color": FG,
        "text.color": FG,
        "legend.labelcolor": FG,
        "legend.edgecolor": EDGE,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "savefig.transparent": True,
        "figure.facecolor": BG,
        "axes.facecolor": BG,
    })
