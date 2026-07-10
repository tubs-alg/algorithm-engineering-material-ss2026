"""robust_feasible: geometry for nominal versus robust feasible sets.

For `_06-robust.qmd`. Generates two geometry panels:

* robust_nominal_geometry.*: uncertainty set with two realizations.
* robust_intersection_geometry.*: scenario-dependent feasible regions and their
  actual common intersection, computed with Shapely.

Slide headings and optimization formulas belong in Quarto. Geometry labels
belong in the figures.
Run: python gen_robust_feasible.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Polygon as MplPolygon
from shapely.geometry import Polygon as ShapelyPolygon

OUT = os.path.dirname(os.path.abspath(__file__))


def scenario_polygons() -> list[tuple[np.ndarray, str, str, tuple[float, float]]]:
    return [
        (np.array([[0.16, 0.43], [0.31, 0.66], [0.58, 0.78],
                   [0.78, 0.58], [0.65, 0.33], [0.34, 0.25]]),
         T.BLUE, r"$\mathcal{X}(\xi_1)$", (0.16, 0.70)),
        (np.array([[0.25, 0.44], [0.34, 0.72], [0.63, 0.89],
                   [0.86, 0.72], [0.80, 0.40], [0.53, 0.30]]),
         T.ORANGE, r"$\mathcal{X}(\xi_2)$", (0.64, 0.78)),
        (np.array([[0.20, 0.32], [0.42, 0.61], [0.60, 0.72],
                   [0.76, 0.48], [0.62, 0.24], [0.37, 0.15]]),
         T.PURPLE, r"$\mathcal{X}(\xi_3)$", (0.18, 0.27)),
    ]


def intersect_polygons(polygons: list[np.ndarray]) -> np.ndarray:
    intersection = ShapelyPolygon(polygons[0])
    for poly in polygons[1:]:
        intersection = intersection.intersection(ShapelyPolygon(poly))
    if intersection.is_empty:
        raise RuntimeError("Scenario polygons have no common intersection.")
    if intersection.geom_type != "Polygon":
        raise RuntimeError(f"Expected polygon intersection, got {intersection.geom_type}.")
    return np.asarray(intersection.exterior.coords[:-1])


def save_nominal() -> None:
    T.init_style(base_fontsize=11)
    fig, ax = plt.subplots(figsize=(4.8, 2.75))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ell = Ellipse((0.46, 0.50), width=0.76, height=0.48, angle=14,
                  facecolor=T.GREEN, edgecolor=T.MUTED, lw=2.0, alpha=0.65)
    ax.add_patch(ell)
    ax.text(0.36, 0.50, r"$\mathcal{U}$", fontsize=20, color=T.FG,
            ha="center", va="center")

    xi1 = np.array([0.60, 0.62])
    xi2 = np.array([0.70, 0.51])
    ax.scatter([xi1[0], xi2[0]], [xi1[1], xi2[1]], s=55,
               color=T.FG, edgecolor="#0f1724", zorder=3)
    ax.text(xi1[0] - 0.10, xi1[1] + 0.04, r"$\xi_1$", fontsize=16)
    ax.text(xi2[0] - 0.08, xi2[1] - 0.10, r"$\xi_2$", fontsize=16)

    T.save(fig, os.path.join(OUT, "robust_nominal_geometry"), pad=0.04)


def save_intersection() -> None:
    T.init_style(base_fontsize=11)
    fig, ax = plt.subplots(figsize=(4.8, 2.75))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    origin = np.array([0.08, 0.08])
    ax.annotate("", xy=(0.95, origin[1]), xytext=origin,
                arrowprops=dict(arrowstyle="-|>", color=T.FG, lw=1.4))
    ax.annotate("", xy=(origin[0], 0.95), xytext=origin,
                arrowprops=dict(arrowstyle="-|>", color=T.FG, lw=1.4))
    ax.text(0.95, 0.015, r"$x_1$", ha="center", va="top", fontsize=13)
    ax.text(0.015, 0.95, r"$x_2$", ha="right", va="center", fontsize=13)

    regions = scenario_polygons()
    for poly, color, label, text_xy in regions:
        ax.add_patch(MplPolygon(poly, closed=True, facecolor=color, edgecolor=color,
                                lw=2.0, alpha=0.33))
        ax.text(*text_xy, label, color=color, fontsize=13)

    core = intersect_polygons([poly for poly, *_ in regions])
    ax.add_patch(MplPolygon(core, closed=True, facecolor=T.GREEN, edgecolor=T.GREEN,
                            lw=2.4, alpha=0.75, zorder=5))
    core_center = core.mean(axis=0)
    ax.text(core_center[0], core_center[1],
            r"$\bigcap_{\xi\in\mathcal{U}}\mathcal{X}(\xi)$",
            ha="center", va="center", fontsize=12, color="#0f1724", zorder=6)

    T.save(fig, os.path.join(OUT, "robust_intersection_geometry"), pad=0.04)


def main() -> None:
    save_nominal()
    save_intersection()


if __name__ == "__main__":
    main()
