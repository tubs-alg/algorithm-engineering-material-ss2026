"""Matplotlib renderer for BTree / BPlusTree (trees.py).

What this file contains
-----------------------
A single entry point ``draw_tree(ax, tree, ...)`` that lays out a B-tree
or B+ tree on an axis using the shared L04 style (``_viz_style``).
Arrows are positioned analytically so each child pointer emerges from
the correct slot in the parent node — between key[i-1] and key[i] for
middle children, flush against the outer edges for the first and last.

Why it exists
-------------
Graphviz centres all outgoing edges on the middle of the parent node,
which is wrong for B-trees: a child pointer must visually correspond to
the key interval it guards. Matplotlib gives us direct control over
every coordinate, and B(+) trees follow a predictable layered schema,
so an analytical layout is both simple and honest.

How to use
----------
    fig, ax = plt.subplots(figsize=(12, 4))
    draw_tree(ax, my_btree)              # B-tree
    draw_tree(ax, my_bplus, bplus=True)   # B+ tree (leaves in green,
                                          # linked list drawn between)
    save(fig, "tree.png")

When to change
--------------
If the deck grows a visualisation for deletion or range-query probes,
extend ``draw_tree`` with optional highlight callbacks rather than
forking the layout. Keep ``_compute_layout`` pure — it produces
coordinates only.
"""

from __future__ import annotations

from dataclasses import dataclass

from _viz_style import (
    CELL, CELL_GAP, CELL_H, CELL_W, FG,
    draw_cell, draw_pointer,
)

LEAF_SIBLING_GAP = 0.35       # extra space between adjacent leaves
LEVEL_H = 1.50                # vertical distance between row tops
INTERNAL_FILL = CELL["data"]  # routing / internal node cell colour
LEAF_FILL = CELL["data"]      # B-tree: same as internal; B+ leaves override
BPLUS_LEAF_FILL = CELL["ok"]  # B+ tree: green leaves to separate them
LEAF_LINK_COLOUR = "#4ea8de"  # same blue as the other "index" highlights

VALUE_STUB_LEN = 0.32         # length of the "→ value" pointer under a key
VALUE_COLOUR = "#8899aa"      # muted slate, subordinate to child pointers


@dataclass
class _NodeBox:
    """Placed rectangle for one tree node.

    ``x_left`` / ``y_bottom`` are in the same coordinate system expected
    by ``draw_cell``: bottom-left of the first key cell.
    """

    node: object
    depth: int
    x_left: float
    y_bottom: float
    keys: list
    is_leaf: bool

    @property
    def num_keys(self) -> int:
        return max(1, len(self.keys))

    @property
    def visual_width(self) -> float:
        # n cells edge-to-edge with an internal gap already baked into CELL_W
        return self.num_keys * CELL_W - CELL_GAP

    @property
    def x_right(self) -> float:
        return self.x_left + self.visual_width

    @property
    def x_center(self) -> float:
        return self.x_left + self.visual_width / 2

    @property
    def y_top(self) -> float:
        return self.y_bottom + CELL_H


def _max_depth(root) -> int:
    if root.leaf:
        return 0
    return 1 + max(_max_depth(c) for c in root.children)


def _compute_layout(root) -> dict[int, _NodeBox]:
    """Place every node. Leaves left-to-right by insertion order; internal
    nodes centred over the horizontal span of their children.

    Returns a dict keyed by ``id(node)`` — the tree classes don't promise
    hashable nodes, so we key by identity.
    """
    depth = _max_depth(root)
    boxes: dict[int, _NodeBox] = {}
    leaf_cursor = [0.0]

    def y_for(d: int) -> float:
        # Depth 0 = root, drawn at the top.
        return (depth - d) * LEVEL_H

    def place(n, d: int) -> _NodeBox:
        if n.leaf:
            num = max(1, len(n.keys))
            width = num * CELL_W - CELL_GAP
            x_left = leaf_cursor[0]
            leaf_cursor[0] = x_left + width + LEAF_SIBLING_GAP
        else:
            for c in n.children:
                place(c, d + 1)
            first = boxes[id(n.children[0])]
            last = boxes[id(n.children[-1])]
            span_center = (first.x_left + last.x_right) / 2
            num = max(1, len(n.keys))
            width = num * CELL_W - CELL_GAP
            x_left = span_center - width / 2
        box = _NodeBox(
            node=n, depth=d, x_left=x_left, y_bottom=y_for(d),
            keys=list(n.keys), is_leaf=n.leaf,
        )
        boxes[id(n)] = box
        return box

    place(root, 0)
    return boxes


def _child_anchor_x(parent: _NodeBox, i: int) -> float:
    """x coordinate at which the pointer to child ``i`` leaves the parent.

    ``i == 0`` → flush to the left edge of the first cell.
    ``i == n`` → flush to the right edge of the last cell.
    Otherwise → centre of the gap between cell ``i-1`` and cell ``i``.
    """
    n = len(parent.keys)
    if i == 0:
        return parent.x_left
    if i == n:
        return parent.x_left + n * CELL_W - CELL_GAP
    return parent.x_left + i * CELL_W - CELL_GAP / 2


def _draw_value_stub(ax, x_center: float, y_cell_bottom: float) -> None:
    """Short arrow from a key cell down to a small 'value' marker.

    Represents "this key owns a pointer to its value record". Drawn
    thin and muted so it reads as payload metadata, not as a primary
    tree edge.
    """
    y_tip = y_cell_bottom - VALUE_STUB_LEN
    ax.plot(
        [x_center, x_center], [y_cell_bottom, y_tip],
        color=VALUE_COLOUR, lw=0.9, solid_capstyle="round",
    )
    # Small filled square at the tip — reads as a tiny payload cell.
    ax.plot(
        x_center, y_tip,
        marker="s", color=VALUE_COLOUR, ms=5, mec="none",
    )


def draw_tree(ax, tree, *, bplus: bool = False) -> None:
    """Render ``tree`` on ``ax``. Set ``bplus=True`` for B+ tree styling
    (green leaves, leaf-link chain, and value pointers only on leaves).

    B-tree: every key — internal and leaf — has a value pointer.
    B+ tree: only leaf keys have value pointers; internal nodes route.
    """
    boxes = _compute_layout(tree.root)

    # Cells. Default draw_cell fontsize (9) looks tiny inside the 0.7×0.55
    # B(+) tree cells — the number only fills about a third of the box.
    # Bump it so the glyph roughly fills the cell vertically.
    cell_fontsize = 16
    for box in boxes.values():
        fill = BPLUS_LEAF_FILL if (bplus and box.is_leaf) else INTERNAL_FILL
        if not box.keys:
            draw_cell(ax, box.x_left, box.y_bottom, "\u2205", CELL["cold"],
                      fontsize=cell_fontsize)
            continue
        for i, k in enumerate(box.keys):
            draw_cell(
                ax,
                box.x_left + i * CELL_W,
                box.y_bottom,
                str(k),
                fill,
                fontsize=cell_fontsize,
            )

    # Value pointers. B-tree: every key slot. B+ tree: leaves only.
    for box in boxes.values():
        if bplus and not box.is_leaf:
            continue
        for i in range(len(box.keys)):
            x_c = box.x_left + i * CELL_W + (CELL_W - CELL_GAP) / 2
            _draw_value_stub(ax, x_c, box.y_bottom)

    # Child pointers. Drawn after value stubs so the tree edges visually
    # dominate the payload stubs where they share vertical space.
    for box in boxes.values():
        if box.is_leaf:
            continue
        for i, c in enumerate(box.node.children):
            child = boxes[id(c)]
            x_from = _child_anchor_x(box, i)
            y_from = box.y_bottom
            draw_pointer(
                ax,
                (x_from, y_from),
                (child.x_center, child.y_top),
            )

    # B+ leaf-link chain — drawn through the vertical middle of each leaf
    # so the arrows are visually distinct from child pointers.
    if bplus:
        leaves = tree.leaves()
        for a, b in zip(leaves, leaves[1:]):
            la = boxes[id(a)]
            lb = boxes[id(b)]
            y_mid = la.y_bottom + CELL_H / 2
            draw_pointer(
                ax,
                (la.x_right, y_mid),
                (lb.x_left, y_mid),
                color=LEAF_LINK_COLOUR,
                lw=1.1,
            )

    # Axis framing. Include the value-stub tips in the lower bound.
    xs = [b.x_left for b in boxes.values()] + [b.x_right for b in boxes.values()]
    ys = [b.y_bottom for b in boxes.values()] + [b.y_top for b in boxes.values()]
    lowest_stub = min(b.y_bottom for b in boxes.values() if b.is_leaf)
    ys.append(lowest_stub - VALUE_STUB_LEN)
    pad_x = 0.4
    pad_y = 0.3
    ax.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
    ax.set_ylim(min(ys) - pad_y, max(ys) + pad_y)
    ax.set_aspect("equal")
    ax.axis("off")
