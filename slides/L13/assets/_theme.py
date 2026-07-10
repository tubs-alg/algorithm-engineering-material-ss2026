"""Shared dark-theme style for the L13 figure generators in this directory.

Matches the course deck conventions (transparent background, light foreground,
see e.g. week09-t05 gen_*.py). Import from the sibling gen_*.py scripts only;
keep it dependency-free (matplotlib + numpy).
"""

import matplotlib.pyplot as plt

FG = "#e6e6e6"        # light foreground: titles, labels, ticks
MUTED = "#9aa6b5"     # secondary text / captions
GRID = "#3a4757"      # grid lines
BLUE = "#9ad0f5"      # primary highlight (nondominated, selected curves)
DEEPBLUE = "#4ea8de"  # stronger blue for lines
ORANGE = "#ff8c42"    # secondary highlight / warnings in figures
GOLD = "#ffd27f"      # tertiary highlight (reference curves)
GREEN = "#7fbf7b"     # good / selected
RED = "#e05c5c"       # bad / violated
PURPLE = "#b58cd6"    # extra series
FADED = "#6b7585"     # de-emphasized points
NAVY = "#2d4059"      # slide navy: node/box fills

# Translucent dark backing so light text reads over lines and the dark slide.
LABEL_BBOX = dict(boxstyle="round,pad=0.25", fc=(0.10, 0.14, 0.20, 0.85), ec="none")


def init_style(base_fontsize: int = 14) -> None:
    """Set uniform rcParams; call once at the top of every generator."""
    plt.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.transparent": True,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "text.color": FG,
        "axes.labelcolor": FG,
        "axes.edgecolor": GRID,
        "axes.titlecolor": FG,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.alpha": 0.5,
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": base_fontsize,
        "axes.titlesize": base_fontsize + 2,
        "font.family": "DejaVu Sans",
        # Match Quarto/RevealJS math (MathJax default = Computer Modern serif),
        # so inline $...$ labels in figures read the same as slide equations.
        "mathtext.fontset": "cm",
        "svg.fonttype": "none",
        "legend.framealpha": 0.0,
        "legend.labelcolor": FG,
    })


def save(fig, stem: str, pad: float = 0.06) -> None:
    """Save PNG + SVG; stem is a path without extension."""
    for ext in ("png", "svg"):
        fig.savefig(f"{stem}.{ext}", bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    print(f"wrote {stem}.png/.svg")
