"""Render the same dataset as a red-black tree, B-tree, and B+ tree.

Emits three PNGs:
  * tree_rbtree_demo.png   — graphviz (circle nodes suit single-key RB)
  * tree_btree_demo.png    — matplotlib (analytical layout, slot-aligned arrows)
  * tree_bplus_demo.png    — matplotlib (adds leaf-link chain)

Why it exists
-------------
The sorted-containers section benefits from one picture per structure
built from the same keys, so the differences in depth, fanout, and leaf
linkage are a direct visual comparison rather than three unrelated
diagrams.

When to change
--------------
Swap ``KEYS`` for a different insertion order, or raise ``ORDER`` to
show how fanout collapses depth. Keep the dataset identical across the
three calls so the comparison remains honest.
"""

from __future__ import annotations

import pathlib

import matplotlib.pyplot as plt

from _viz_style import save, setup_mpl
from tree_viz import draw_tree
from trees import BPlusTree, BTree, RedBlackTree

HERE = pathlib.Path(__file__).resolve().parent

# A 30-key insertion sequence. Double the earlier 15-key set, chosen so
# the red-black tree has several rotation cascades and the B / B+ trees
# (order 5, i.e. up to 4 keys per node) split at least twice at the
# internal level — enough depth to make the fan-out contrast with the
# RB picture visually honest.
KEYS = [
    10, 20, 5, 6, 12, 30, 7, 17, 2, 15, 25, 22, 27, 1, 8,
    35, 40, 3, 45, 18, 33, 9, 42, 14, 28, 4, 38, 11, 23, 50,
]
ORDER = 5


def main() -> None:
    setup_mpl()

    rb = RedBlackTree()
    bt = BTree(order=ORDER)
    bp = BPlusTree(order=ORDER)
    for k in KEYS:
        rb.insert(k)
        bt.insert(k)
        bp.insert(k)

    # Fail loudly if any invariant broke during construction.
    rb._check()
    bt._check()
    bp._check()

    # RB tree: keep graphviz — single-key nodes don't have the
    # slot-alignment problem and circle nodes read naturally.
    rb.to_graphviz(title="Red-black tree (std::map shape)").render(
        filename=HERE / "tree_rbtree_demo", cleanup=True,
    )
    print(f"Saved {HERE / 'tree_rbtree_demo.png'}")

    # B-tree and B+ tree: matplotlib so arrows emerge from the correct
    # slot boundaries between keys.
    fig, ax = plt.subplots(figsize=(16, 5))
    draw_tree(ax, bt)
    save(fig, str(HERE / "tree_btree_demo.png"))

    fig, ax = plt.subplots(figsize=(17, 5))
    draw_tree(ax, bp, bplus=True)
    save(fig, str(HERE / "tree_bplus_demo.png"))


if __name__ == "__main__":
    main()
