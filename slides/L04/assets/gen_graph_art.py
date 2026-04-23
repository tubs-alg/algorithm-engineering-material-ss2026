"""Candidate "graph art" figures for the graphs-chapter opener.

What this file contains
-----------------------
Generates a batch of decorative but honest graph figures — random graphs
from classical models (scale-free, small-world, community, geometric,
tree) rendered with networkx embeddings. Each PNG is a standalone
candidate the author picks from; the chosen one lands on the "Why graphs
matter" opener slide as pure visual texture while bullet points do the
talking.

Why it exists
-------------
The slide's message is deliberately abstract: *graphs are the dominant
abstraction in combinatorial optimisation — they model everything from
people to states.* Concrete mini-icons (person-node, map-pin-node)
trivialise the point. A large, pretty, structure-rich graph does the
opposite: it invites the viewer to read structure into it and primes
them for the representation question the rest of the section answers.

How to use
----------
    python gen_graph_art.py

Writes ``graph_art_<model>_<layout>.png`` files next to this script.
Pick the favourite, reference it from ``_07-graphs.qmd``, delete the
rest or keep them for swap-outs.

When to change
--------------
Add a new ``(name, builder, layout, palette)`` tuple to ``VARIANTS`` to
generate another candidate. Keep the figure aspect ratio roughly 3:2 so
a 1/3-width bullet column still leaves the figure legible on a 16:9
slide.
"""

from __future__ import annotations

import pathlib
import random

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from _viz_style import setup_mpl

HERE = pathlib.Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Palettes — pick node/edge colours that sit well on the dark slide theme
# ---------------------------------------------------------------------------

PALETTES = {
    "cool": {
        "node_cmap": plt.cm.viridis,
        "edge": "#7fa9c9",
        "edge_alpha": 0.35,
        "glow": "#4ea8de",
    },
    "warm": {
        "node_cmap": plt.cm.plasma,
        "edge": "#d89a5a",
        "edge_alpha": 0.32,
        "glow": "#f39c12",
    },
    "mono": {
        "node_cmap": plt.cm.Blues,
        "edge": "#8fb3d6",
        "edge_alpha": 0.30,
        "glow": "#4ea8de",
    },
    "spectrum": {
        "node_cmap": plt.cm.turbo,
        "edge": "#a0a8b8",
        "edge_alpha": 0.28,
        "glow": "#e0e0e0",
    },
}


# ---------------------------------------------------------------------------
# Graph builders — each returns an undirected nx.Graph
# ---------------------------------------------------------------------------

def build_scale_free(seed: int = 7) -> nx.Graph:
    """Barabási–Albert: hubs + many leaves. Reads as a 'social network'."""
    return nx.barabasi_albert_graph(n=140, m=2, seed=seed)


def build_small_world(seed: int = 11) -> nx.Graph:
    """Watts–Strogatz: mostly local with a few rewires. Reads 'structured'."""
    return nx.watts_strogatz_graph(n=120, k=6, p=0.08, seed=seed)


def build_communities(seed: int = 5) -> nx.Graph:
    """Stochastic block model: four visible communities, sparse bridges."""
    sizes = [28, 32, 26, 30]
    p_in, p_out = 0.18, 0.012
    probs = [[p_in if i == j else p_out for j in range(len(sizes))]
             for i in range(len(sizes))]
    return nx.stochastic_block_model(sizes, probs, seed=seed)


def build_geometric(seed: int = 3) -> nx.Graph:
    """Random geometric: proximity graph. Reads 'spatial / wireless'."""
    return nx.random_geometric_graph(n=150, radius=0.18, seed=seed)


def build_tree(seed: int = 13) -> nx.Graph:
    """Random tree: no cycles, branching structure."""
    return nx.random_labeled_tree(n=90, seed=seed)


def build_powerlaw_cluster(seed: int = 17) -> nx.Graph:
    """Holme-Kim: scale-free with higher clustering. Denser hubs."""
    return nx.powerlaw_cluster_graph(n=160, m=3, p=0.4, seed=seed)


# ---------------------------------------------------------------------------
# Layouts
# ---------------------------------------------------------------------------

def layout_spring(G: nx.Graph, seed: int) -> dict:
    return nx.spring_layout(G, seed=seed, iterations=250, k=None)


def layout_kk(G: nx.Graph, seed: int) -> dict:
    return nx.kamada_kawai_layout(G)


def layout_geo(G: nx.Graph, seed: int) -> dict:
    # Random geometric graphs carry their own positions
    return {n: G.nodes[n]["pos"] for n in G.nodes}


def layout_spectral(G: nx.Graph, seed: int) -> dict:
    return nx.spectral_layout(G)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def draw(
    G: nx.Graph,
    pos: dict,
    palette: dict,
    out_path: pathlib.Path,
    *,
    figsize: tuple[float, float] = (11, 7),
    node_size_scale: float = 120.0,
    draw_glow: bool = True,
) -> None:
    setup_mpl()

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_axis_off()
    ax.set_aspect("equal")

    degs = np.array([G.degree(n) for n in G.nodes])
    # Node size grows sublinearly with degree so hubs stand out but don't crush
    sizes = node_size_scale * (0.35 + 0.65 * (degs / max(degs.max(), 1)) ** 0.8)
    node_colors = degs  # colour-by-degree reads naturally

    # --- edges ------------------------------------------------------------
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color=palette["edge"],
        alpha=palette["edge_alpha"],
        width=0.9,
    )

    # --- glow halo (scatter with large alpha) ----------------------------
    if draw_glow:
        xs = np.array([pos[n][0] for n in G.nodes])
        ys = np.array([pos[n][1] for n in G.nodes])
        for r, a in [(3.2, 0.06), (2.2, 0.10), (1.6, 0.15)]:
            ax.scatter(
                xs, ys,
                s=sizes * r,
                c=palette["glow"],
                alpha=a, linewidths=0,
                zorder=2,
            )

    # --- nodes -----------------------------------------------------------
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_size=sizes,
        node_color=node_colors,
        cmap=palette["node_cmap"],
        linewidths=0.6,
        edgecolors="#0e1e2e",
    )

    fig.tight_layout(pad=0.3)
    fig.savefig(out_path, dpi=200, bbox_inches="tight", transparent=True)
    plt.close(fig)
    print(f"Saved {out_path}")


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------

VARIANTS = [
    ("scalefree_spring",      build_scale_free,       layout_spring,   "cool",     7),
    ("scalefree_kk",          build_scale_free,       layout_kk,       "spectrum", 7),
    ("smallworld_kk",         build_small_world,      layout_kk,       "warm",    11),
    ("smallworld_spring",     build_small_world,      layout_spring,   "mono",    11),
    ("communities_spring",    build_communities,      layout_spring,   "spectrum", 5),
    ("communities_kk",        build_communities,      layout_kk,       "cool",     5),
    ("geometric_geo",         build_geometric,        layout_geo,      "cool",     3),
    ("geometric_spring",      build_geometric,        layout_spring,   "warm",     3),
    ("tree_kk",               build_tree,             layout_kk,       "mono",    13),
    ("tree_spring",           build_tree,             layout_spring,   "cool",    13),
    ("powerlaw_spring",       build_powerlaw_cluster, layout_spring,   "warm",    17),
    ("powerlaw_kk",           build_powerlaw_cluster, layout_kk,       "spectrum",17),
]


def main() -> None:
    random.seed(0)
    for stem, builder, layout_fn, palette_key, seed in VARIANTS:
        G = builder(seed=seed)
        # Keep only the largest connected component — isolated dots hurt aesthetics
        if not nx.is_connected(G):
            biggest = max(nx.connected_components(G), key=len)
            G = G.subgraph(biggest).copy()
        pos = layout_fn(G, seed=seed)
        out = HERE / f"graph_art_{stem}.png"
        draw(G, pos, PALETTES[palette_key], out)


if __name__ == "__main__":
    main()
