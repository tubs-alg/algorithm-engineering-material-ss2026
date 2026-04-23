"""Minimal red-black, B-tree, and B+ tree implementations for teaching.

What this file contains
-----------------------
Three tree classes with only what is needed for the L04 slides:
  * ``RedBlackTree``  — CLRS-style insertion, no deletion.
  * ``BTree``         — configurable order, node-splitting insertion.
  * ``BPlusTree``     — configurable order, leaf-linked, insertion only.

Each class exposes ``insert(key, value=None)`` and a ``to_graphviz()``
method that returns a ``graphviz.Digraph`` ready to ``render()``. The
visual style matches ``gen_rbtree.py`` so the three trees sit next to
each other in the deck.

Why it exists
-------------
The sorted-containers section needs pictures of the same dataset in all
three shapes. Standard-library trees are opaque and library B-trees are
compiled, so we need a small Python reference implementation we can
both feed arbitrary keys and visualise. Correctness and clarity matter;
performance does not.

How to use
----------
    from trees import RedBlackTree, BTree, BPlusTree
    t = BTree(order=4)
    for k in [10, 20, 5, 6, 12, 30, 7, 17]:
        t.insert(k)
    t.to_graphviz().render("btree_demo", cleanup=True)

When to change
--------------
If the slides later need deletion, an iteration/range-scan demo, or a
cache-miss-counting wrapper, extend the classes here rather than
forking. Keep the invariants checkable — the ``_check()`` helpers are
used by the tests in ``gen_tree_comparison.py``.
"""

from __future__ import annotations

import graphviz

# Palette aligned with gen_rbtree.py so the three trees read as one set.
FG = "#e0e0e0"
RED = "#c0392b"
BLACK = "#2c3e50"
BLUE = "#3a6b8c"
GREEN = "#2ecc71"
EDGE = "#f39c12"
LEAF_LINK = "#4ea8de"


def _html_row(keys, fill: str) -> str:
    """HTML-like label for a multi-key B-tree / B+ tree node.

    Uses a single-row table of coloured cells. We need HTML labels (not
    ``shape=record``) because record shapes break ``dot``'s flat-edge
    routing for the B+ leaf chain.
    """
    if not keys:
        cells = (
            f'<TD BGCOLOR="{fill}" WIDTH="24" HEIGHT="22" '
            f'BORDER="1" COLOR="{FG}"> </TD>'
        )
    else:
        cells = "".join(
            f'<TD BGCOLOR="{fill}" BORDER="1" COLOR="{FG}" '
            f'CELLPADDING="6"><FONT COLOR="white" '
            f'FACE="Helvetica-Bold"><B>{k}</B></FONT></TD>'
            for k in keys
        )
    return (
        '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" '
        f'CELLPADDING="0"><TR>{cells}</TR></TABLE>>'
    )


# ---------------------------------------------------------------------------
# Red-black tree
# ---------------------------------------------------------------------------

class RedBlackTree:
    """Left-leaning-free, CLRS-style red-black tree (insertion only)."""

    _RED = 0
    _BLACK = 1

    class _Node:
        __slots__ = ("key", "value", "color", "left", "right", "parent")

        def __init__(self, key, value, color):
            self.key = key
            self.value = value
            self.color = color
            self.left = None
            self.right = None
            self.parent = None

    def __init__(self) -> None:
        # Sentinel NIL used internally to avoid None checks during fixup.
        # It is not rendered — see to_graphviz().
        self._NIL = self._Node(None, None, self._BLACK)
        self.root = self._NIL

    # -- public API ---------------------------------------------------------
    def insert(self, key, value=None) -> None:
        z = self._Node(key, value, self._RED)
        z.left = z.right = self._NIL
        y = None
        x = self.root
        while x is not self._NIL:
            y = x
            x = x.left if key < x.key else x.right
        z.parent = y
        if y is None:
            self.root = z
        elif key < y.key:
            y.left = z
        else:
            y.right = z
        self._fix(z)

    # -- rotations and fixup ------------------------------------------------
    def _left_rotate(self, x) -> None:
        y = x.right
        x.right = y.left
        if y.left is not self._NIL:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _right_rotate(self, x) -> None:
        y = x.left
        x.left = y.right
        if y.right is not self._NIL:
            y.right.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x is x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        y.right = x
        x.parent = y

    def _fix(self, z) -> None:
        while z.parent is not None and z.parent.color == self._RED:
            gp = z.parent.parent
            if gp is None:
                break
            if z.parent is gp.left:
                u = gp.right
                if u.color == self._RED:
                    z.parent.color = self._BLACK
                    u.color = self._BLACK
                    gp.color = self._RED
                    z = gp
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                    z.parent.color = self._BLACK
                    z.parent.parent.color = self._RED
                    self._right_rotate(z.parent.parent)
            else:
                u = gp.left
                if u.color == self._RED:
                    z.parent.color = self._BLACK
                    u.color = self._BLACK
                    gp.color = self._RED
                    z = gp
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = self._BLACK
                    z.parent.parent.color = self._RED
                    self._left_rotate(z.parent.parent)
        self.root.color = self._BLACK

    # -- invariant check (for tests) ----------------------------------------
    def _check(self) -> int:
        """Return black-height. Raises AssertionError on any violation."""
        assert self.root is self._NIL or self.root.color == self._BLACK

        def walk(n):
            if n is self._NIL:
                return 1
            if n.color == self._RED:
                assert n.left.color == self._BLACK
                assert n.right.color == self._BLACK
            if n.left is not self._NIL:
                assert n.left.key < n.key
            if n.right is not self._NIL:
                assert n.right.key > n.key
            lh = walk(n.left)
            rh = walk(n.right)
            assert lh == rh
            return lh + (1 if n.color == self._BLACK else 0)

        return walk(self.root)

    # -- visualisation ------------------------------------------------------
    def to_graphviz(self, *, title: str | None = None) -> graphviz.Digraph:
        dot = graphviz.Digraph("RBTree", format="png")
        dot.attr(
            bgcolor="transparent",
            rankdir="TB",
            nodesep="0.30",
            ranksep="0.50",
            ordering="out",
            dpi="200",
        )
        if title:
            dot.attr(label=title, labelloc="t", fontcolor=FG,
                     fontname="Helvetica-Bold", fontsize="14")
        dot.attr("node", shape="circle", style="filled,bold",
                 fontname="Helvetica-Bold", fontsize="16", fontcolor="white",
                 color=FG, penwidth="1.2", width="0.5", fixedsize="true")
        dot.attr("edge", color=EDGE, penwidth="1.2",
                 arrowhead="vee", arrowsize="0.6")

        def nid(n) -> str:
            return f"n{id(n)}"

        def emit(n) -> None:
            fill = RED if n.color == self._RED else BLACK
            dot.node(nid(n), label=str(n.key), fillcolor=fill)
            for child in (n.left, n.right):
                if child is self._NIL:
                    continue
                emit(child)
                dot.edge(nid(n), nid(child))

        if self.root is not self._NIL:
            emit(self.root)
        return dot


# ---------------------------------------------------------------------------
# B-tree (CLRS-style)
# ---------------------------------------------------------------------------

class BTree:
    """Classical B-tree with top-down splitting. ``order`` = max children."""

    class _Node:
        __slots__ = ("keys", "values", "children", "leaf")

        def __init__(self, leaf: bool = True) -> None:
            self.keys: list = []
            self.values: list = []
            self.children: list = []
            self.leaf = leaf

    def __init__(self, order: int = 4) -> None:
        if order < 3:
            raise ValueError("order must be >= 3")
        self.order = order
        self._max_keys = order - 1
        self.root = self._Node(leaf=True)

    # -- public API ---------------------------------------------------------
    def insert(self, key, value=None) -> None:
        r = self.root
        if len(r.keys) == self._max_keys:
            s = self._Node(leaf=False)
            s.children.append(r)
            self._split_child(s, 0)
            self.root = s
            self._insert_nonfull(s, key, value)
        else:
            self._insert_nonfull(r, key, value)

    # -- insertion internals ------------------------------------------------
    def _split_child(self, parent, i: int) -> None:
        y = parent.children[i]
        z = self._Node(leaf=y.leaf)
        mid = len(y.keys) // 2
        median_k = y.keys[mid]
        median_v = y.values[mid]
        z.keys = y.keys[mid + 1:]
        z.values = y.values[mid + 1:]
        y.keys = y.keys[:mid]
        y.values = y.values[:mid]
        if not y.leaf:
            z.children = y.children[mid + 1:]
            y.children = y.children[:mid + 1]
        parent.keys.insert(i, median_k)
        parent.values.insert(i, median_v)
        parent.children.insert(i + 1, z)

    def _insert_nonfull(self, node, key, value) -> None:
        i = len(node.keys) - 1
        if node.leaf:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            node.keys.insert(i + 1, key)
            node.values.insert(i + 1, value)
            return
        while i >= 0 and key < node.keys[i]:
            i -= 1
        i += 1
        if len(node.children[i].keys) == self._max_keys:
            self._split_child(node, i)
            if key > node.keys[i]:
                i += 1
        self._insert_nonfull(node.children[i], key, value)

    # -- invariant check ----------------------------------------------------
    def _check(self) -> int:
        """Return tree height. Raises AssertionError on any violation."""

        def walk(n, is_root: bool) -> int:
            assert 0 <= len(n.keys) <= self._max_keys
            if not is_root:
                assert len(n.keys) >= (self.order // 2) - 1 or n is self.root
            assert n.keys == sorted(n.keys)
            if n.leaf:
                return 1
            assert len(n.children) == len(n.keys) + 1
            heights = {walk(c, False) for c in n.children}
            assert len(heights) == 1, "leaves at different depths"
            return next(iter(heights)) + 1

        return walk(self.root, True)

    # -- visualisation ------------------------------------------------------
    def to_graphviz(self, *, title: str | None = None) -> graphviz.Digraph:
        dot = graphviz.Digraph("BTree", format="png")
        dot.attr(bgcolor="transparent", rankdir="TB",
                 nodesep="0.25", ranksep="0.55", ordering="out", dpi="200")
        if title:
            dot.attr(label=title, labelloc="t", fontcolor=FG,
                     fontname="Helvetica-Bold", fontsize="14")
        dot.attr("node", shape="plaintext")
        dot.attr("edge", color=EDGE, penwidth="1.2",
                 arrowhead="vee", arrowsize="0.6")

        def nid(n) -> str:
            return f"n{id(n)}"

        def emit(n) -> None:
            dot.node(nid(n), label=_html_row(n.keys, BLUE))
            if not n.leaf:
                for c in n.children:
                    emit(c)
                    dot.edge(nid(n), nid(c))

        emit(self.root)
        return dot


# ---------------------------------------------------------------------------
# B+ tree
# ---------------------------------------------------------------------------

class BPlusTree:
    """B+ tree: routing keys in internal nodes, (key, value) pairs in leaves.

    Leaves are linked in a singly-linked list for range scans.
    ``order`` = max children per internal node; leaves hold up to
    ``order - 1`` key-value pairs.
    """

    class _Node:
        __slots__ = ("keys", "children", "values", "next", "leaf")

        def __init__(self, leaf: bool = True) -> None:
            self.keys: list = []
            self.children: list = []   # internal only
            self.values: list = []     # leaf only
            self.next: "BPlusTree._Node | None" = None
            self.leaf = leaf

    def __init__(self, order: int = 4) -> None:
        if order < 3:
            raise ValueError("order must be >= 3")
        self.order = order
        self._max_keys = order - 1
        self.root = self._Node(leaf=True)

    # -- public API ---------------------------------------------------------
    def insert(self, key, value=None) -> None:
        r = self.root
        if len(r.keys) == self._max_keys:
            s = self._Node(leaf=False)
            s.children.append(r)
            self._split_child(s, 0)
            self.root = s
        self._insert_nonfull(self.root, key, value)

    def leaves(self) -> list:
        """Return the leaf chain in key order (for range-scan demos)."""
        n = self.root
        while not n.leaf:
            n = n.children[0]
        out = []
        while n is not None:
            out.append(n)
            n = n.next
        return out

    # -- insertion internals ------------------------------------------------
    def _split_child(self, parent, i: int) -> None:
        y = parent.children[i]
        z = self._Node(leaf=y.leaf)
        if y.leaf:
            mid = (len(y.keys) + 1) // 2
            z.keys = y.keys[mid:]
            z.values = y.values[mid:]
            y.keys = y.keys[:mid]
            y.values = y.values[:mid]
            z.next = y.next
            y.next = z
            # Copy-up: first key of right half becomes the routing key.
            parent.keys.insert(i, z.keys[0])
            parent.children.insert(i + 1, z)
        else:
            mid = len(y.keys) // 2
            median = y.keys[mid]
            z.keys = y.keys[mid + 1:]
            z.children = y.children[mid + 1:]
            y.keys = y.keys[:mid]
            y.children = y.children[:mid + 1]
            # Move-up: median is removed from the child.
            parent.keys.insert(i, median)
            parent.children.insert(i + 1, z)

    def _insert_nonfull(self, node, key, value) -> None:
        if node.leaf:
            i = len(node.keys) - 1
            while i >= 0 and key < node.keys[i]:
                i -= 1
            node.keys.insert(i + 1, key)
            node.values.insert(i + 1, value)
            return
        i = len(node.keys) - 1
        while i >= 0 and key < node.keys[i]:
            i -= 1
        i += 1
        if len(node.children[i].keys) == self._max_keys:
            self._split_child(node, i)
            if key >= node.keys[i]:
                i += 1
        self._insert_nonfull(node.children[i], key, value)

    # -- invariant check ----------------------------------------------------
    def _check(self) -> int:
        """Return tree height. Asserts ordering, fanout, leaf linkage."""

        def walk(n) -> int:
            assert 0 <= len(n.keys) <= self._max_keys
            assert n.keys == sorted(n.keys)
            if n.leaf:
                return 1
            assert len(n.children) == len(n.keys) + 1
            heights = {walk(c) for c in n.children}
            assert len(heights) == 1
            return next(iter(heights)) + 1

        h = walk(self.root)
        # Leaf-list should enumerate all keys in order.
        keys_seen: list = []
        for leaf in self.leaves():
            keys_seen.extend(leaf.keys)
        assert keys_seen == sorted(keys_seen)
        return h

    # -- visualisation ------------------------------------------------------
    def to_graphviz(self, *, title: str | None = None) -> graphviz.Digraph:
        dot = graphviz.Digraph("BPlusTree", format="png")
        dot.attr(bgcolor="transparent", rankdir="TB",
                 nodesep="0.25", ranksep="0.55", ordering="out", dpi="200")
        if title:
            dot.attr(label=title, labelloc="t", fontcolor=FG,
                     fontname="Helvetica-Bold", fontsize="14")
        dot.attr("node", shape="plaintext")
        dot.attr("edge", color=EDGE, penwidth="1.2",
                 arrowhead="vee", arrowsize="0.6")

        def nid(n) -> str:
            return f"n{id(n)}"

        def emit_internal(n) -> None:
            dot.node(nid(n), label=_html_row(n.keys, BLUE))
            for c in n.children:
                if c.leaf:
                    emit_leaf(c)
                else:
                    emit_internal(c)
                dot.edge(nid(n), nid(c))

        def emit_leaf(n) -> None:
            # Leaves styled distinctively (green) to separate them from
            # internal routing nodes.
            dot.node(nid(n), label=_html_row(n.keys, GREEN))

        if self.root.leaf:
            emit_leaf(self.root)
        else:
            emit_internal(self.root)

        # Leaf-link chain (dashed, distinct colour) plus rank=same so the
        # leaves stay on one row — makes the B+ range-scan chain visible.
        leaves = self.leaves()
        if leaves:
            with dot.subgraph() as s:  # type: ignore[union-attr]
                s.attr(rank="same")
                for leaf in leaves:
                    s.node(nid(leaf))
            for a, b in zip(leaves, leaves[1:]):
                dot.edge(
                    nid(a), nid(b),
                    color=LEAF_LINK, penwidth="1.2",
                    style="dashed", arrowhead="vee", arrowsize="0.6",
                    constraint="false",
                )
        return dot
