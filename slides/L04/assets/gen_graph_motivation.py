"""Graph motivation panels for the graphs chapter opener.

Emits four PNGs:
  * graph_motivation_weighted.png
  * graph_motivation_directed.png
  * graph_motivation_dag.png
  * graph_motivation_flow.png

Why it exists
-------------
The opener uses RevealJS fragments to show one graph flavour after the
other. Each panel is rendered independently with Graphviz so the slide
can reveal richer examples in sequence rather than cramming them into
one static collage.

Implementation note
-------------------
The machine has the Graphviz `dot` binary but not the Python `graphviz`
package. So this generator writes DOT directly and invokes `dot`
through subprocess.
"""

from __future__ import annotations

import pathlib
import subprocess
import textwrap

HERE = pathlib.Path(__file__).resolve().parent

COMMON = r'''
graph [
  bgcolor="transparent",
  rankdir="LR",
  pad="0.10",
  nodesep="0.30",
  ranksep="0.48",
  dpi="200",
  fontname="Helvetica"
];
node [
  shape="box",
  style="filled,rounded",
  color="#e0e0e0",
  fontcolor="white",
  penwidth="1.2",
  fontname="Helvetica-Bold",
  fontsize="20",
  margin="0.14,0.10"
];
edge [
  color="#f39c12",
  fontcolor="#f5c97b",
  penwidth="1.8",
  arrowsize="0.75",
  fontsize="14",
  fontname="Helvetica"
];
'''


def panel_dot(name: str, title: str, subtitle: str, body: str) -> str:
    return textwrap.dedent(
        f'''
        digraph {name} {{
          {COMMON}
          label=<
            <FONT POINT-SIZE="24"><B>{title}</B></FONT><BR/>
            <FONT POINT-SIZE="14">{subtitle}</FONT>
          >;
          labelloc="t";
          labeljust="l";
          {body}
        }}
        '''
    ).strip() + "\n"


def render(stem: str, dot: str) -> None:
    dot_path = HERE / f"{stem}.dot"
    png_path = HERE / f"{stem}.png"
    dot_path.write_text(dot, encoding="utf-8")
    subprocess.run(["dot", "-Tpng", "-o", str(png_path), str(dot_path)], check=True)
    print(f"Saved {png_path}")


def main() -> None:
    render(
        "graph_motivation_weighted",
        panel_dot(
            "RouteGraph",
            "Weighted directed graph",
            "route planning / travel times / latency",
            r'''
            rA [label="Depot", fillcolor="#3a6b8c"];
            rB [label="Hub", fillcolor="#4ea8de"];
            rC [label="Bridge", fillcolor="#4ea8de"];
            rD [label="Airport", fillcolor="#8e5ea2"];
            { rank=same; rA; rB; rC; rD; }
            rA -> rB [label="7 min"];
            rA -> rC [label="11 min"];
            rB -> rC [label="3 min"];
            rC -> rB [label="5 min", color="#9fb3c8", fontcolor="#b8c0cc"];
            rB -> rD [label="9 min"];
            rC -> rD [label="4 min"];
            ''',
        ),
    )

    render(
        "graph_motivation_directed",
        panel_dot(
            "CitationGraph",
            "Directed graph",
            "citation / influence / hyperlinks",
            r'''
            c1 [label="Transformer\n(2017)", fillcolor="#3a6b8c"];
            c2 [label="BERT\n(2018)", fillcolor="#5a9e5a"];
            c3 [label="GPT\n(2018)", fillcolor="#5a9e5a"];
            c4 [label="Modern\nsurvey", fillcolor="#8e5ea2"];
            { rank=same; c1; c2; c3; c4; }
            c2 -> c1;
            c3 -> c1;
            c4 -> c2;
            c4 -> c3;
            ''',
        ),
    )

    render(
        "graph_motivation_dag",
        panel_dot(
            "BuildGraph",
            "DAG",
            "build systems / task scheduling / prerequisites",
            r'''
            b1 [label="lexer.o", fillcolor="#3a6b8c"];
            b2 [label="parser.o", fillcolor="#3a6b8c"];
            b3 [label="frontend.a", fillcolor="#4ea8de"];
            b4 [label="app", fillcolor="#8e5ea2"];
            { rank=same; b1; b2; b3; b4; }
            b1 -> b3;
            b2 -> b3;
            b3 -> b4;
            ''',
        ),
    )

    render(
        "graph_motivation_flow",
        panel_dot(
            "FlowGraph",
            "Bipartite / capacitated graph",
            "matching, logistics, max-flow",
            r'''
            s  [label="Source", fillcolor="#3a6b8c"];
            w1 [label="Warehouse 1", fillcolor="#5a9e5a"];
            w2 [label="Warehouse 2", fillcolor="#5a9e5a"];
            t  [label="Customers", fillcolor="#8e5ea2"];
            { rank=same; s; w1; w2; t; }
            s  -> w1 [label="cap 8"];
            s  -> w2 [label="cap 5"];
            w1 -> t  [label="cost 2"];
            w2 -> t  [label="cost 3"];
            ''',
        ),
    )


if __name__ == "__main__":
    main()
