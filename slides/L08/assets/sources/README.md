# Figure generators (travel copies)

Each `*_solve.py` here is a **verbatim copy** of the generator that produced the
matching figures in `../` (the deck's `assets/`). They live beside the slides so a
figure can be adapted without hunting through `snippets/`.

- `import aeviz` uses an absolute path to `snippets/`, so these run from anywhere.
- `aeviz.save(fig, stem)` writes `stem.png` + `stem.svg` to the **current directory**
  using the *original* stems (`01_*`, `02_*`, ...). After regenerating, copy the one
  you want up to `../<prefix>_<name>.svg` (the name the slides reference).
- Canonical source (with README + instance notes) stays under `snippets/examples/...`.

| Generator | Origin (`snippets/examples/`) | Deck assets (`../`) |
|-----------|-------------------------------|---------------------|
| `graphbasics_solve.py` (+ `helpers.py`) | `00-concepts/graph-basics` | `graph_nodes.svg` (01), `graph_weighted.svg` (02), `graph_directed.svg` (03), `graph_dag.svg` (04), `graph_cycle.svg` (04b) |
| `gallery_solve.py` (+ `glyphs.py`) | `00-concepts/problem-gallery` | `glyph_shortest_path.svg`, `glyph_matching.svg`, `glyph_flow.svg`, `glyph_mst.svg` (the four labeled "what we will cover" overview glyphs, dropped into the slide as individual fragments; min cut and min-cost flow are not separate overview tiles), `sp_definition.svg`, `match_bipartite.svg` (21), `match_general.svg` (22), `maxflow_def.svg` (31), `mincostflow_def.svg` (41), `mst_def.svg` (61) (and the other `*_example` definition figures used by later pillars; gallery also produces `51_mincut_example`, not currently used in the deck) |
| `street_solve.py` | `01-shortest-paths/street-network-routing` | `street_network.svg` (01_network), `street_route.svg` (02_route). Real OSM data (central Hannover); caches `street_hannover.graphml` in the snippet dir on first run. |
| `shift_solve.py` | `01-shortest-paths/dag-shift-planning-pricing` | `shift_demand.svg` (03), `shift_greedy.svg` (04), `shift_dag.svg` (01), `shift_solution.svg` (02) |
| `dijkstra_solve.py` | `01-shortest-paths/dijkstra-walkthrough` | `dijkstra_instance.svg`, `dijkstra_step1..5.png`, `dijkstra_solution.svg` |
| `astar_solve.py` | `01-shortest-paths/astar-vs-dijkstra` | `astar_side_by_side.svg`, `astar_counts.svg` |
| `td_solve.py` | `01-shortest-paths/time-dependent-fifo` | `td_route.svg`, `td_profiles.svg` |
| `implicit_solve.py` | `01-shortest-paths/implicit-graph-search` | `implicit_boards.svg`, `implicit_tree.svg` |
| `rcsp_solve.py` | `01-shortest-paths/capacitated-shortest-path` | `rcsp_two_paths.svg`, `rcsp_pareto.svg` |
| `kidney_solve.py` | `02-matching/kidney-exchange` | `kidney_anatomy.svg` (00), `kidney_graph.svg` (01), `kidney_matching.svg` (02), `kidney_lp.svg` (03) |
| `assign_solve.py` | `02-matching/assignment-orders-machines` | `assign_matrix.svg` (01), `assign_matching.svg` (02) |
| `wind_solve.py` | `03-flows/wind-power-maxflow` | `wind_network.svg` (01), `wind_maxflow.svg` (02, incl. min cut). Shares turbine geometry with the MST callback in `_08`. |
| `factory_solve.py` | `03-flows/factory-shift-scheduling` | `factory_timeline.svg` (01), `factory_network.svg` (02), `factory_greedy.svg` (04). (Also produces `03_worker_schedule`, not currently used.) Distinct from `shift_solve.py` (the SP DAG roster in `_02`). |
| `residual_solve.py` | `03-flows/residual-graph` | `residual_flow1..3.svg` (01–03 flow), `residual_res1..3.svg` (01–03 residual), `residual_final.svg` (04) |
| `windmst_solve.py` | `05-spanning-trees/wind-power-mst` | `windmst_network.svg` (01), `windmst_mst.svg` (02). **Same wind farm as `wind_solve.py`** (geometry kept byte-for-byte in sync) for the `_06` → `_08` callback. |
| `summary_solve.py` (+ `glyphs.py`) | `00-concepts/summary` (**deck-adapted**) | `summary_map.svg` (01_lecture_map), `summary_complexity.svg` (02_complexity_framing). **Christofides removed** vs. the snippet original: map drops the Christofides tile + its 2 arrows; the NP-hard band names the deck's real NP-hard edges (RCSP budget, multi-commodity / activation-cost flows). Import paths are absolute so it runs from here. |
