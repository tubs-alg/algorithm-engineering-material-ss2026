"""Red-black tree — the structure hiding inside std::map.

Emits rbtree.png. A small, valid red-black tree rendered with Graphviz.
The visual goal is to make three things obvious at a glance:

  1. This is a *binary* tree — two children per node, no fan-out.
  2. Red and black nodes follow the RB invariants (root black, no red
     node has a red child, every root-to-NIL path has the same number
     of black nodes). This signals "red-black tree", not a plain BST.
  3. Every node is its own object, reached through a pointer from its
     parent. Paired with the slide text, this drives home the
     "one allocation per key, one key per cache line" story.

Why it exists
-------------
`_04-sorted.qmd` opens with "std::map is std::list with a sorting
invariant". That slide needs one picture that makes the tree nature and
the pointer-chase pattern land. Matplotlib is awkward for trees;
Graphviz gets the layout for free.

How to use
----------
    python3 gen_rbtree.py

Requires the `dot` binary (graphviz system package) and the
``graphviz`` Python module.

When to change
--------------
If a second tree diagram is added (e.g. a BST vs B-tree height
comparison), factor the colour palette and graph attributes into a
small helper so the trees read as one visual language.
"""

from __future__ import annotations

import pathlib

import graphviz

HERE = pathlib.Path(__file__).resolve().parent

# Colours aligned with _viz_style.py so the tree sits next to the other
# L04 figures without looking foreign. The red is the deck's "hot / warn"
# colour; the black is the "cold slot" slate.
FG = "#e0e0e0"
RED = "#c0392b"
BLACK = "#2c3e50"
EDGE = "#f39c12"       # same as the pointer-arrow colour elsewhere
NIL_FG = "#8899aa"

# A small, valid red-black tree. Every root-to-NIL path contains exactly
# two black nodes (counting NIL but not the root), so the black-height
# invariant holds. No red node has a red child.
#
#            [13 B]
#           /      \
#       [8 R]     [17 R]
#       /  \      /   \
#    [1 B][11 B][15 B][25 B]
#         \
#        [6 R]       (6 > 1  ⇒  6 is the *right* child of 1)
NODES: list[tuple[str, str, str]] = [
    ("n13", "13", BLACK),
    ("n8",  "8",  RED),
    ("n17", "17", RED),
    ("n1",  "1",  BLACK),
    ("n11", "11", BLACK),
    ("n15", "15", BLACK),
    ("n25", "25", BLACK),
    ("n6",  "6",  RED),
]

# Each internal node's (left, right) children. `None` means a NIL leaf,
# drawn as a small black rectangle. Child order here determines draw
# order — combined with ``ordering=out`` on the graph, this forces
# "smaller keys on the left, larger on the right" to match BST reading
# order. Without this, Graphviz would be free to flip the children and
# produce a picture that violates the BST invariant.
CHILDREN: list[tuple[str, str | None, str | None]] = [
    ("n13", "n8",  "n17"),
    ("n8",  "n1",  "n11"),
    ("n17", "n15", "n25"),
    ("n1",  None,  "n6"),     # 6 > 1, so it is the right child
    ("n6",  None,  None),
    ("n11", None,  None),
    ("n15", None,  None),
    ("n25", None,  None),
]


def _add_nil(dot: graphviz.Digraph, nil_id: str) -> None:
    dot.node(
        nil_id,
        label="NIL",
        shape="box",
        width="0.35",
        height="0.25",
        fixedsize="true",
        fontsize="9",
        fontcolor=NIL_FG,
        fillcolor=BLACK,
        color=NIL_FG,
        penwidth="0.8",
    )


def _add_edge(dot: graphviz.Digraph, parent: str, child: str, *, nil: bool) -> None:
    if nil:
        dot.edge(
            parent, child,
            color=NIL_FG, penwidth="0.8",
            arrowhead="none", style="dashed",
        )
    else:
        dot.edge(parent, child)


def build_graph() -> graphviz.Digraph:
    dot = graphviz.Digraph("RBTree", format="png")
    # ``ordering=out`` makes Graphviz honour the order in which we emit a
    # node's outgoing edges. Combined with the left-then-right loop over
    # CHILDREN below, this guarantees that smaller keys are drawn to the
    # left of their parent and larger keys to the right — matching BST
    # reading order. Without it, dot is free to flip children to reduce
    # edge crossings and the picture silently lies about key ordering.
    dot.attr(
        bgcolor="transparent",
        rankdir="TB",
        nodesep="0.35",
        ranksep="0.55",
        ordering="out",
        dpi="200",
    )
    dot.attr(
        "node",
        shape="circle",
        style="filled,bold",
        fontname="Helvetica-Bold",
        fontsize="18",
        fontcolor="white",
        color=FG,
        penwidth="1.4",
        width="0.55",
        fixedsize="true",
    )
    dot.attr(
        "edge",
        color=EDGE,
        penwidth="1.3",
        arrowhead="vee",
        arrowsize="0.7",
    )

    for node_id, label, fill in NODES:
        dot.node(node_id, label=label, fillcolor=fill)

    # Emit each internal node's edges strictly left-then-right. Missing
    # real children are replaced by NIL leaves so every internal node
    # has exactly two outgoing edges in the picture — this is both the
    # BST reality and what makes ``ordering=out`` do the right thing.
    for parent, left, right in CHILDREN:
        for side, child_id in (("L", left), ("R", right)):
            if child_id is None:
                nil_id = f"nil_{parent}_{side}"
                _add_nil(dot, nil_id)
                _add_edge(dot, parent, nil_id, nil=True)
            else:
                _add_edge(dot, parent, child_id, nil=False)

    return dot


def main() -> None:
    dot = build_graph()
    # render() writes <outfile>.png and a .gv source file; we only want
    # the PNG, so clean up the source after.
    out_stem = HERE / "rbtree"
    dot.render(filename=out_stem, cleanup=True)
    print(f"Saved {out_stem.with_suffix('.png')}")


if __name__ == "__main__":
    main()
