"""Generate the facility-location intro picture.

Produces one PNG (transparent background, dark-theme palette matching
gen_network_flow.py):

  facility_location_intro.png   landscape — three candidate sites (two opened,
                                one closed), six customers, dashed assignment
                                lines from each customer to its serving site.
                                One opening cost f_j and one shipping cost
                                c_ij are annotated to anchor the symbols.

Why this exists. The strong-vs-weak section dives into two LP formulations of
capacitated facility location. The slide before "two ways to link" needs a
single concrete picture that names the players (customers, candidate sites,
opening costs f_j, shipping costs c_ij) so the formulas land.

How to use. `python assets/gen_facility_location_intro.py` from slides/.

When to change. Edit CUSTOMERS / SITES / OPEN if the layout needs to change.
Keep the ~16:9 aspect so the slide column layout holds.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from pathlib import Path

OUT = Path(__file__).parent

FG = "#e0e0e0"
SITE_OPEN_FILL = "#7fbf7b"
SITE_OPEN_EDGE = "#7fbf7b"
SITE_CLOSED_FILL = "#2d4059"
SITE_CLOSED_EDGE = "#9aa0a6"
CUSTOMER_FILL = "#9ad0f5"
CUSTOMER_EDGE = "#9ad0f5"
ASSIGN = "#f5d76e"
ASSIGN_HILITE = "#e69138"
LABEL = "#f5d76e"

plt.rcParams.update({
    "savefig.transparent": True,
    "text.color": FG,
    "font.size": 14,
})

# (name, x, y) — five candidate sites in a square layout, three opened and two
# closed. The closed sites B (center) and E (bottom-left) are deliberately
# tempting: customers cluster around them but have to travel further.
SITES = {
    "A": (2.0, 8.0),
    "B": (5.0, 5.3),
    "C": (8.0, 8.3),
    "D": (8.0, 2.0),
    "E": (2.0, 2.0),
}
OPEN = {"A": True, "B": False, "C": True, "D": True, "E": False}

# (name, x, y, served_by) — assignments go to the *open* site, which is not
# always the nearest candidate; the tempting closed sites B and E are why.
CUSTOMERS = [
    ("1",  0.5, 9.2, "A"),
    ("2",  2.6, 9.4, "A"),
    ("3",  0.4, 6.4, "A"),
    ("4",  3.6, 7.6, "A"),
    ("5",  6.4, 8.6, "C"),
    ("6",  9.2, 9.1, "C"),
    ("7",  9.4, 6.2, "C"),
    ("8",  5.6, 4.7, "C"),    # nearest is closed B; forced up to open C
    ("9",  4.5, 3.0, "D"),
    ("10", 1.0, 4.2, "A"),    # nearest is closed E; forced up to open A
    ("11", 0.8, 0.8, "A"),    # right beside closed E; long diagonal up to A
    ("12", 6.8, 1.2, "D"),
    ("13", 9.3, 3.6, "D"),
    ("14", 3.1, 0.6, "D"),
]

# (customer, site) edge to draw with extra weight, marking the most striking
# "closed site forces a long detour" case in the picture.
HILITE = ("11", "A")


def draw():
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_aspect("equal")
    ax.set_xlim(-0.3, 10.3)
    ax.set_ylim(-1.2, 10.2)
    ax.axis("off")

    # Assignment lines first so they sit beneath the markers.
    for name, x, y, j in CUSTOMERS:
        jx, jy = SITES[j]
        ax.plot([x, jx], [y, jy], linestyle="--", color=ASSIGN,
                linewidth=1.4, alpha=0.85, zorder=1)

    # Sites: squares. Opened = filled green, closed = hollow grey.
    for name, (x, y) in SITES.items():
        opened = OPEN[name]
        ax.scatter([x], [y],
                   s=560,
                   marker="s",
                   facecolor=SITE_OPEN_FILL if opened else SITE_CLOSED_FILL,
                   edgecolor=SITE_OPEN_EDGE if opened else SITE_CLOSED_EDGE,
                   linewidths=2.0,
                   zorder=3)
        ax.text(x, y, name, ha="center", va="center",
                color="#1e1e2e" if opened else FG,
                fontsize=13, fontweight="bold", zorder=4)

    # Customers: circles.
    for name, x, y, j in CUSTOMERS:
        ax.scatter([x], [y],
                   s=240,
                   facecolor=CUSTOMER_FILL,
                   edgecolor=CUSTOMER_EDGE,
                   linewidths=1.5,
                   zorder=3)
        ax.text(x, y, name, ha="center", va="center",
                color="#1e1e2e", fontsize=11, fontweight="bold", zorder=4)

    # Legend strip across the bottom.
    legend_y = -0.85
    ax.scatter([0.4], [legend_y], s=240, facecolor=CUSTOMER_FILL,
               edgecolor=CUSTOMER_EDGE, linewidths=1.5)
    ax.text(0.8, legend_y, "customer",
            color=FG, fontsize=12, va="center")
    ax.scatter([3.4], [legend_y], s=360, marker="s",
               facecolor=SITE_OPEN_FILL, edgecolor=SITE_OPEN_EDGE, linewidths=2.0)
    ax.text(3.75, legend_y, "opened site",
            color=FG, fontsize=12, va="center")
    ax.scatter([6.6], [legend_y], s=360, marker="s",
               facecolor=SITE_CLOSED_FILL, edgecolor=SITE_CLOSED_EDGE, linewidths=2.0)
    ax.text(6.95, legend_y, "closed candidate",
            color=FG, fontsize=12, va="center")

    plt.tight_layout(pad=0.3)
    out = OUT / "facility_location_intro.png"
    plt.savefig(out, dpi=180)
    print(f"wrote {out}")


if __name__ == "__main__":
    draw()
