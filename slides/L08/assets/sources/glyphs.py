"""
Abstract glyph marks for the L08 graph-algorithm problem families.

What this file contains
-----------------------
One small drawing function per problem family, each painting a minimal iconic
mark (a "glyph") for a single matplotlib Axes: shortest path, matching, max
flow, min-cost flow, min cut, and MST. The glyphs are deliberately unlabeled,
square-ish, and instantly recognizable. A registry (GLYPHS) maps a family key
to (title, draw_fn) so callers can iterate.
Non-goal: these draw icons, not solved instances. The labeled worked examples
that actually run networkx live in solve.py, not here.

Why it exists
-------------
Both the section-2 overview grid (problem-gallery) and the section-7 lecture
map (summary) must use the SAME glyph look. Factoring the glyph painters here
lets the summary folder import this module so the two packs rhyme visually.

How to use it
-------------
    import glyphs
    glyphs.init()                      # palette + a deterministic style
    fig, ax = plt.subplots()
    glyphs.draw_shortest_path(ax)      # paint one glyph onto an axes
    # or iterate the registry:
    for key, (title, fn) in glyphs.GLYPHS.items():
        fn(ax); ax.set_title(title)

When it should change
---------------------
Add a family (new key + painter + registry entry) or retune a mark when the
deck's iconography changes. Keep every painter axes-local and side-effect free
so it composes into grids and maps.
"""

from __future__ import annotations

import sys
import pathlib

from matplotlib.patches import Circle, FancyArrowPatch

# Pull the shared palette so glyphs match the rest of the deck.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))  # -> snippets/
import aeviz  # noqa: E402

P = aeviz.PALETTE
DOT = P["settled"]        # default node fill
DOT_EDGE = "#ffffff"      # node ring
FADE = P["faded"]         # de-emphasized edges
PATH = P["path"]          # blue highlight (paths / tree)
ACCENT = P["accent"]      # vermillion highlight (matching / cut / flow)
GOOD = P["good"]          # green: source
WARN = P["warn"]          # amber: sink


def init() -> None:
    """Initialize the shared aeviz style. Call once before drawing glyphs."""
    aeviz.init_style()


# --- low-level primitives ---------------------------------------------------
def _frame(ax) -> None:
    """Square, axis-off canvas with a little margin. Glyphs live in [0,1]^2."""
    ax.set_xlim(-0.08, 1.08)
    ax.set_ylim(-0.08, 1.08)
    ax.set_aspect("equal")
    ax.axis("off")


def _dot(ax, xy, r=0.055, fc=DOT, ec=DOT_EDGE, lw=1.6, z=3):
    ax.add_patch(Circle(xy, r, facecolor=fc, edgecolor=ec, lw=lw, zorder=z))


def _line(ax, a, b, color=FADE, lw=2.0, z=1, ls="-"):
    ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=lw, ls=ls,
            zorder=z, solid_capstyle="round")


def _arrow(ax, a, b, color=DOT, lw=2.2, z=2, rad=0.0, shrink=9.0, ms=12):
    ax.add_patch(FancyArrowPatch(
        a, b, connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>",
        mutation_scale=ms, lw=lw, color=color, shrinkA=shrink, shrinkB=shrink,
        zorder=z))


# --- one painter per family -------------------------------------------------
def draw_shortest_path(ax) -> None:
    """An s->t path threading through scattered dots; the path is highlighted."""
    _frame(ax)
    on = [(0.07, 0.30), (0.33, 0.62), (0.6, 0.42), (0.93, 0.74)]   # the path
    off = [(0.27, 0.12), (0.7, 0.12), (0.5, 0.9), (0.82, 0.3)]     # other nodes
    # faint background edges to off-path nodes
    _line(ax, on[0], off[0])
    _line(ax, on[1], off[2])
    _line(ax, off[1], on[2])
    _line(ax, on[2], off[3])
    _line(ax, off[3], on[3])
    # the highlighted path
    for a, b in zip(on, on[1:]):
        _line(ax, a, b, color=PATH, lw=4.2, z=2)
    for xy in off:
        _dot(ax, xy, fc=FADE, ec="#ffffff")
    for xy in on[1:-1]:
        _dot(ax, xy, fc=PATH)
    _dot(ax, on[0], fc=GOOD)    # s
    _dot(ax, on[-1], fc=WARN)   # t


def draw_matching(ax) -> None:
    """A denser graph with a maximum matching highlighted: bold disjoint edges,
    matched dots colored, faint context edges, one node left unmatched."""
    _frame(ax)
    n = {
        0: (0.10, 0.82), 1: (0.34, 0.96), 2: (0.40, 0.64), 3: (0.66, 0.93),
        4: (0.92, 0.80), 5: (0.15, 0.33), 6: (0.45, 0.18), 7: (0.71, 0.41),
        8: (0.91, 0.16),
    }
    match = [(0, 5), (1, 3), (2, 6), (4, 7)]   # disjoint: 8 matched, node 8 free
    context = [(0, 1), (2, 3), (3, 4), (5, 6), (6, 7), (7, 8), (2, 7), (4, 8)]
    matched = {v for e in match for v in e}
    for u, v in context:
        _line(ax, n[u], n[v])
    for u, v in match:
        _line(ax, n[u], n[v], color=ACCENT, lw=4.2, z=2)
    for k, xy in n.items():
        _dot(ax, xy, fc=ACCENT if k in matched else FADE, r=0.05)


def draw_maxflow(ax) -> None:
    """A flow from s to t that routes through SOME arcs (bold, uniform width, so
    the flow is conserved at every node) while other arcs carry no flow (faded).
    Two unit paths s->a->c->t and s->b->d->t; the two cross arcs stay unused."""
    _frame(ax)
    s = (0.05, 0.5)
    a, b = (0.34, 0.80), (0.34, 0.20)
    c, d = (0.66, 0.80), (0.66, 0.20)
    t = (0.95, 0.5)
    used = [(s, a), (a, c), (c, t), (s, b), (b, d), (d, t)]
    unused = [(a, d), (b, c)]   # available arcs the flow does not use
    for p, q in unused:
        _arrow(ax, p, q, color=FADE, lw=1.8, ms=11)
    for p, q in used:
        _arrow(ax, p, q, color=PATH, lw=3.6, ms=15)
    for m in (a, b, c, d):
        _dot(ax, m, fc=DOT, r=0.05)
    _dot(ax, s, fc=GOOD, r=0.06)   # source
    _dot(ax, t, fc=WARN, r=0.06)   # sink


def draw_mincostflow(ax) -> None:
    """Like max flow but arcs carry costs: a small currency mark sits on the arcs.
    Used only as a small icon in the summary complexity band (not the overview)."""
    _frame(ax)
    s = (0.06, 0.5)
    mid = [(0.46, 0.76), (0.46, 0.24)]
    t = (0.94, 0.5)
    arcs = [(s, mid[0]), (s, mid[1]), (mid[0], t), (mid[1], t)]
    for a, b in arcs:
        _arrow(ax, a, b, color=PATH, lw=3.4, ms=13)
    # currency marks on each arc midpoint
    for a, b in arcs:
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        ax.text(mx, my, "$", color=ACCENT, fontsize=15, fontweight="bold",
                ha="center", va="center", zorder=4,
                bbox=dict(boxstyle="circle,pad=0.12", fc=(0.10, 0.14, 0.20, 0.92),
                          ec=ACCENT, lw=1.4))
    for m in mid:
        _dot(ax, m, fc=DOT)
    _dot(ax, s, fc=GOOD, r=0.062)
    _dot(ax, t, fc=WARN, r=0.062)


def draw_mincut(ax) -> None:
    """Two clusters split by a dashed line; the few edges crossing it (the cut)
    are bold, intra-cluster edges faded."""
    _frame(ax)
    left = [(0.13, 0.78), (0.27, 0.42), (0.09, 0.14)]    # s-side; left[0] = s
    right = [(0.73, 0.80), (0.91, 0.46), (0.77, 0.14)]   # t-side; right[2] = t
    intra = [(left[0], left[1]), (left[1], left[2]), (left[0], left[2]),
             (right[0], right[1]), (right[1], right[2]), (right[0], right[2])]
    cut = [(left[0], right[0]), (left[1], right[1])]     # cross the divide
    for a, b in intra:
        _line(ax, a, b, color=FADE, lw=2.2)
    for a, b in cut:
        _line(ax, a, b, color=ACCENT, lw=4.0, z=2)
    # the dashed slicing line down the middle
    _line(ax, (0.5, 0.04), (0.5, 0.96), color=P["ink"], lw=2.0, z=4,
          ls=(0, (5, 4)))
    _dot(ax, left[0], fc=GOOD)
    _dot(ax, left[1], fc=DOT)
    _dot(ax, left[2], fc=DOT)
    _dot(ax, right[0], fc=DOT)
    _dot(ax, right[1], fc=DOT)
    _dot(ax, right[2], fc=WARN)


def draw_mst(ax) -> None:
    """A branching spanning tree (bold) reaching every scattered dot; non-tree
    links faded. Branches at three nodes so it reads as a tree, not a path."""
    _frame(ax)
    nodes = {
        "a": (0.10, 0.52), "b": (0.34, 0.84), "c": (0.30, 0.18),
        "d": (0.56, 0.97), "e": (0.58, 0.58), "f": (0.50, 0.14),
        "g": (0.86, 0.76), "h": (0.88, 0.34),
    }
    tree = [("a", "b"), ("a", "c"), ("b", "d"), ("b", "e"),
            ("c", "f"), ("e", "g"), ("e", "h")]
    extra = [("b", "c"), ("d", "e"), ("f", "h"), ("g", "h")]
    for u, v in extra:
        _line(ax, nodes[u], nodes[v], color=FADE, lw=2.0)
    for u, v in tree:
        _line(ax, nodes[u], nodes[v], color=PATH, lw=4.0, z=2)
    for xy in nodes.values():
        _dot(ax, xy, fc=DOT, r=0.05)


# Registry: stable order = lecture order. Title is the on-grid caption.
GLYPHS = {
    "shortest_path": ("Shortest path", draw_shortest_path),
    "matching": ("Matching", draw_matching),
    "maxflow": ("Max flow", draw_maxflow),
    "mincostflow": ("Min-cost flow", draw_mincostflow),
    "mincut": ("Min cut", draw_mincut),
    "mst": ("Spanning tree (MST)", draw_mst),
}


def draw_legend_dots(ax) -> None:
    """Tiny shared key explaining the source/sink/highlight dot colors."""
    items = [(GOOD, "source / start"), (WARN, "sink / target"),
             (PATH, "solution (path / tree / flow)"), (ACCENT, "matching / cut")]
    y = 0.9
    for color, text in items:
        ax.add_patch(Circle((0.06, y), 0.03, facecolor=color,
                            edgecolor="white", lw=1.2))
        ax.text(0.13, y, text, fontsize=10, va="center", color=P["ink"])
        y -= 0.28
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
