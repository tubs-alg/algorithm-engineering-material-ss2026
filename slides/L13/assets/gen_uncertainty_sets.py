"""uncertainty_sets: box, budgeted, and ellipsoidal uncertainty sets.

For `_06-robust.qmd`. Three panels around the same nominal estimate: a full
box (allows all corners: every coefficient at its extreme at once), a budgeted
set (box intersected with a Gamma budget: only a few severe deviations at a
time; corners cut), and an ellipsoid. Run: python gen_uncertainty_sets.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Polygon, Rectangle

OUT = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    T.init_style()
    rng = np.random.default_rng(3)
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.2))

    for ax, title in zip(axes, ["box", "budgeted ($\\Gamma$)", "ellipsoidal"]):
        ax.set_xlim(-1.6, 1.6)
        ax.set_ylim(-1.6, 1.6)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=15)
        ax.scatter([0], [0], s=110, color=T.ORANGE, zorder=5)
        ax.text(0.09, 0.13, r"$\hat a$", fontsize=15, color=T.ORANGE)

    # Box: the full rectangle, corners included.
    axes[0].add_patch(Rectangle((-1.05, -1.05), 2.1, 2.1, fill=False,
                                lw=2.5, edgecolor=T.BLUE))
    corners = np.array([[-1.05, -1.05], [-1.05, 1.05], [1.05, -1.05], [1.05, 1.05]])
    axes[0].scatter(*corners.T, s=70, color=T.RED, zorder=4)
    axes[0].text(0, -1.45, "all extremes at once", ha="center", fontsize=11.5,
                 color=T.RED)

    # Budgeted: box intersected with an L1 budget -> octagon (cut corners).
    g = 0.52  # corner cut fraction
    b = 1.05
    octagon = [(-b, -b + g * b), (-b, b - g * b), (-b + g * b, b), (b - g * b, b),
               (b, b - g * b), (b, -b + g * b), (b - g * b, -b), (-b + g * b, -b)]
    axes[1].add_patch(Polygon(octagon, fill=False, lw=2.5, edgecolor=T.BLUE))
    axes[1].add_patch(Rectangle((-b, -b), 2 * b, 2 * b, fill=False, lw=1.2,
                                edgecolor=T.FADED, ls="--"))
    axes[1].text(0, -1.45, "corners cut: few severe deviations", ha="center",
                 fontsize=11.5, color=T.MUTED)

    # Ellipsoid: aligned with the correlated cloud below (same 28-degree tilt).
    axes[2].add_patch(Ellipse((0, 0), 2.4, 1.25, angle=28, fill=False, lw=2.5,
                              edgecolor=T.BLUE))
    axes[2].text(0, -1.45, "correlated, smooth boundary", ha="center",
                 fontsize=11.5, color=T.MUTED)

    # One correlated cloud of plausible realizations, reused in every panel:
    # elongated along 28 degrees. The sets cover most scenarios, not all -- a
    # few realizations fall outside each boundary, as in a calibrated set.
    th = np.deg2rad(28)
    rot = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    raw = (rng.normal(size=(60, 2)) * np.array([0.60, 0.32])) @ rot.T
    pts = raw[(np.abs(raw) < 1.5).all(axis=1)][:24]
    for ax in axes:
        ax.scatter(*pts.T, s=28, color=T.BLUE, alpha=0.5, zorder=3)

    T.save(fig, os.path.join(OUT, "uncertainty_sets"), pad=0.1)


if __name__ == "__main__":
    main()
