"""
Lecture-map recap for the L08 graph-algorithm lecture (section 7, the closing
"how it all connects" slide).

DECK-ADAPTED COPY (Christofides removed)
----------------------------------------
Verbatim-derived from snippets/examples/00-concepts/summary/solve.py, with two
deliberate edits for the deck, which skips Christofides:
  1. Figure 1 (lecture map): the Christofides tile and its two incoming arrows
     (mst -> christofides, matching -> christofides) are dropped. Five pillars
     remain with the four connections the deck actually draws.
  2. Figure 2 (complexity framing): the NP-hard band no longer shows Christofides.
     It now names the NP-hard EDGES the deck actually crosses: the resource
     budget (RCSP, _04), and multi-commodity / fixed-activation-cost flows (_07).
     This matches the plan's intent for 02_complexity_framing ("one side
     constraint flips a polynomial problem to NP-hard; the bridge to MIP/LP").

Import paths are absolute (this copy lives in the deck's assets/sources/, not in
the snippet tree), consistent with the other deck generators. glyphs.py is the
shared painter from problem-gallery; a copy also sits beside this file.

How to run
----------
    python summary_solve.py     # writes 01_lecture_map.{png,svg} + 02_*.{png,svg}
                                 # to the current directory (original stems)
"""

# %%
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

# Absolute paths (this copy runs from the deck, not the snippet tree).
_SNIPPETS = (
    "/home/krupke/Cloud/Dropbox/Secretary/cases/course-ae-ss26-internal/"
    "week07-l08-graph-algorithms/snippets"
)
_GALLERY = _SNIPPETS + "/examples/00-concepts/problem-gallery"
sys.path.insert(0, _SNIPPETS)
sys.path.insert(0, _GALLERY)
import aeviz  # noqa: E402
import glyphs  # noqa: E402  (the shared glyph painters, from problem-gallery)

glyphs.init()
P = aeviz.PALETTE


# %% Layout: hand-placed map positions (axes fraction coords) ----------------
# A loose left-to-right pipeline of the five pillars (Christofides dropped).
TILES = {
    # key:            (cx, cy)   center of the glyph tile
    "shortest_path":  (0.16, 0.74),
    "maxflow":        (0.50, 0.74),
    "mincut":         (0.84, 0.74),
    "matching":       (0.50, 0.26),
    "mst":            (0.16, 0.26),
}
TILE_W, TILE_H = 0.22, 0.30   # tile footprint (axes fraction)

# Connections the lecture draws: (from, to, label, style).
# style: "solid" = builds-on / uses; "double" = duality (drawn as <->).
LINKS = [
    ("shortest_path", "maxflow", "augmenting paths\nbuild flow", "solid"),
    ("maxflow", "mincut", "max flow = min cut\n(duality)", "double"),
    ("matching", "maxflow", "matching is a\nspecial flow", "solid"),
    ("mst", "shortest_path", "both connect\nthe network", "solid"),
]


def _tile_axes(fig, key):
    """Create an inset axes for one glyph tile, centered on its map position."""
    cx, cy = TILES[key]
    rect = (cx - TILE_W / 2, cy - TILE_H / 2, TILE_W, TILE_H)
    ax = fig.add_axes(rect)
    return ax


def _edge_point(key_from, key_to):
    """Attach points a fixed fraction along the line, just outside each tile."""
    fx, fy = TILES[key_from]
    tx, ty = TILES[key_to]
    dx, dy = tx - fx, ty - fy
    p0 = (fx + dx * 0.30, fy + dy * 0.30)
    p1 = (tx - dx * 0.30, ty - dy * 0.30)
    return p0, p1


# %% Figure 1: the lecture map -----------------------------------------------
fig = plt.figure(figsize=(11.0, 7.2))
base = fig.add_axes((0, 0, 1, 1))
base.set_xlim(0, 1)
base.set_ylim(0, 1)
base.axis("off")

# Draw connection arrows FIRST (behind the tiles).
SOLID = P["faded_dark"]
DUAL = P["accent"]
for key_from, key_to, label, style in LINKS:
    p0, p1 = _edge_point(key_from, key_to)
    color = DUAL if style == "double" else SOLID
    arrowstyle = "<|-|>" if style == "double" else "-|>"
    base.add_patch(FancyArrowPatch(
        p0, p1, connectionstyle="arc3,rad=0.0", arrowstyle=arrowstyle,
        mutation_scale=16, lw=2.4, color=color, shrinkA=2, shrinkB=2,
        zorder=1, alpha=0.95))
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    base.text(mx, my, label, fontsize=9.5, ha="center", va="center",
              color=(DUAL if style == "double" else P["ink"]),
              zorder=2, bbox=dict(boxstyle="round,pad=0.2",
                                  fc=(0.10, 0.14, 0.20, 0.85),
                                  ec="none"))

# Draw the five glyph tiles on top.
for key in ("shortest_path", "maxflow", "mincut", "matching", "mst"):
    ax = _tile_axes(fig, key)
    title, fn = glyphs.GLYPHS[key]
    fn(ax)
    ax.set_title(title, fontsize=12, pad=2, color=P["ink"])

base.text(0.5, 0.985, "How the pillars connect", fontsize=17,
          fontweight="bold", ha="center", va="top", color=P["ink"])

# small key for the two link types
base.add_patch(FancyArrowPatch((0.04, 0.04), (0.12, 0.04), arrowstyle="-|>",
               mutation_scale=14, lw=2.2, color=SOLID))
base.text(0.13, 0.04, "builds on / uses", fontsize=9.5, va="center",
          color=P["ink"])
base.add_patch(FancyArrowPatch((0.40, 0.04), (0.48, 0.04), arrowstyle="<|-|>",
               mutation_scale=14, lw=2.2, color=DUAL))
base.text(0.49, 0.04, "duality (max flow = min cut)", fontsize=9.5,
          va="center", color=DUAL)

aeviz.save(fig, "01_lecture_map")
plt.close(fig)


# %% Figure 2: complexity framing (polynomial core vs NP-hard edges) ---------
fig = plt.figure(figsize=(10.5, 4.2))
base = fig.add_axes((0, 0, 1, 1))
base.set_xlim(0, 1)
base.set_ylim(0, 1)
base.axis("off")

# Two bands: polynomial (left, green tint) and the NP-hard edges (right, amber).
from matplotlib.patches import FancyBboxPatch  # noqa: E402
base.add_patch(FancyBboxPatch((0.02, 0.16), 0.66, 0.66,
               boxstyle="round,pad=0.01", fc=P["good"], alpha=0.10,
               ec=P["good"], lw=1.5, zorder=0))
base.add_patch(FancyBboxPatch((0.72, 0.16), 0.26, 0.66,
               boxstyle="round,pad=0.01", fc=P["warn"], alpha=0.14,
               ec=P["warn"], lw=1.5, zorder=0))
base.text(0.35, 0.88, "Polynomial-time core", fontsize=14, ha="center",
          fontweight="bold", color=P["good"])
base.text(0.85, 0.88, "NP-hard edges", fontsize=14, ha="center",
          fontweight="bold", color=P["warn"])

poly = ["shortest_path", "matching", "maxflow", "mincostflow", "mincut", "mst"]
xs = [0.075 + i * (0.60 / 5) for i in range(6)]
for key, x in zip(poly, xs):
    ax = fig.add_axes((x, 0.30, 0.10, 0.30))
    title, fn = glyphs.GLYPHS[key]
    fn(ax)
    ax.set_title(title.split(" (")[0], fontsize=8.5, pad=1, color=P["ink"])

# The NP-hard edges the deck actually crosses (text, not glyphs): one side
# constraint added to a polynomial problem.
nphard = [
    "+ resource budget\n(RCSP)",
    "multi-commodity\nflow",
    "fixed / activation\ncosts",
]
for i, label in enumerate(nphard):
    base.text(0.85, 0.66 - i * 0.20, label, fontsize=10.5, ha="center",
              va="center", color=P["warn"], zorder=2)

base.text(0.5, 0.06, "We solve the left exactly. One side constraint (a budget, "
          "shared capacity, a fixed cost) flips it to NP-hard: the bridge to "
          "MIP and LP.", fontsize=10, ha="center", color=P["ink"])

aeviz.save(fig, "02_complexity_framing")
plt.close(fig)


# %% Stdout summary ----------------------------------------------------------
print("=== L08 summary lecture map (section 7, Christofides removed) ===")
print(f"Tiles placed: {len(TILES)}  (5 pillars, no Christofides)")
print("Connections drawn:")
for a, b, label, style in LINKS:
    arrow = "<->" if style == "double" else "->"
    print(f"  {a:14s} {arrow} {b:14s}  {label.replace(chr(10), ' ')}")
print("\nGlyph style reused from problem-gallery/glyphs.py (packs rhyme).")
print("Wrote: 01_lecture_map, 02_complexity_framing  (PNG + SVG)")
