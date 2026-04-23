"""Animated traversal race: std::vector vs std::list.

What this file contains
-----------------------
A single Manim scene, `VectorVsListTraversal`, that visualises the cost of
pointer-chasing vs. contiguous access. A cursor walks a 12-element vector,
then the same 12 values stored as a scattered linked list. A "cycles
elapsed" counter advances by one per vector hop and by one hundred per
list hop — the 100× ratio between L1 and main-memory latency.

Why it exists
-------------
The static PNG diagrams (gen_vector_vs_list.py) show the layout; this
animation shows the *consequence* — the list cursor visibly waits for
memory on every step while the vector streams through.

How to use
----------
    manim -qm -o vector_vs_list_traversal manim_vector_vs_list.py \\
        VectorVsListTraversal

Produces `media/videos/manim_vector_vs_list/720p30/VectorVsListTraversal.mp4`
by default; the `-o` flag renames the output file. Embed in the slide
with a `{{< video ... >}}` Quarto shortcode or an HTML `<video>` tag.

When to change
--------------
If the palette in `_viz_style.py` changes, sync the colours here. If the
point of the animation shifts (e.g. to cache-line-level detail rather
than per-element hops), rewrite — do not patch.
"""

from __future__ import annotations

import random

from manim import (
    BLACK,
    DOWN,
    GREEN,
    LEFT,
    ORIGIN,
    RED,
    RIGHT,
    UP,
    Arrow,
    Create,
    FadeIn,
    FadeOut,
    ManimColor,
    Scene,
    Text,
    VGroup,
    Write,
)
from manim_dsa import MArray, MArrayStyle

# Palette aligned with _viz_style.py so the animation reads as part of the
# same visual language as the static PNGs used elsewhere in the deck.
BG = ManimColor("#1e1e2e")
FG = ManimColor("#e0e0e0")
POINTER = ManimColor("#f39c12")   # PTR colour — same orange as static diagrams
OK = ManimColor("#2ecc71")        # cache-friendly annotation
BAD = ManimColor("#e74c3c")       # cache-miss annotation

VALUES = [7, 3, 9, 1, 4, 8, 2, 6, 5, 0, 11, 13]
N = len(VALUES)

# Cycles per hop — vector hits L1, list pays DRAM latency. The ratio is
# the teaching point; absolute numbers are illustrative.
CYCLES_VEC = 1
CYCLES_LIST = 100


class VectorVsListTraversal(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text(
            "Traversal: std::vector vs std::list",
            font_size=40, color=FG,
        ).to_edge(UP, buff=0.3)
        self.play(Write(title), run_time=0.8)

        # ---- Vector row ---------------------------------------------------
        vector = (
            MArray(VALUES, style=MArrayStyle.BLUE)
            .scale(0.55)
            .next_to(title, DOWN, buff=0.9)
        )
        vec_label = Text("std::vector", font_size=24, color=FG).next_to(
            vector, LEFT, buff=0.4
        )
        vec_counter = Text("0 cycles", font_size=22, color=OK).next_to(
            vector, RIGHT, buff=0.5
        )
        self.play(Create(vector), FadeIn(vec_label), FadeIn(vec_counter), run_time=0.8)

        # ---- Scattered list row -------------------------------------------
        # Place 12 cells at jittered positions inside a horizontal band.
        # Seed for reproducibility.
        rng = random.Random(7)
        x_slots = [-6.0 + i * (12.0 / (N - 1)) for i in range(N)]
        # Visit order follows the values' logical sequence, not their x-pos,
        # so arrows criss-cross — the whole point.
        shuffled = list(range(N))
        rng.shuffle(shuffled)
        positions = [None] * N
        y_band_top = -1.6
        y_band_bot = -3.0
        for logical_idx, slot_idx in enumerate(shuffled):
            x = x_slots[slot_idx]
            y = rng.uniform(y_band_bot, y_band_top)
            positions[logical_idx] = (x, y)

        # Each list node = a one-cell MArray, scaled and placed individually.
        list_nodes = []
        for i, value in enumerate(VALUES):
            node = MArray([value], style=MArrayStyle.PURPLE).scale(0.55)
            node.move_to([positions[i][0], positions[i][1], 0])
            list_nodes.append(node)
        list_group = VGroup(*list_nodes)

        list_label = Text("std::list", font_size=24, color=FG).to_edge(LEFT, buff=0.4)
        list_label.shift(UP * (y_band_top - 0.4) + DOWN * 0.1)
        # Cycle counter lives top-right of the list region so both counters
        # sit at the same y-level relative to their structures.
        list_counter = Text("0 cycles", font_size=22, color=BAD).to_edge(RIGHT, buff=0.5)
        list_counter.shift(UP * (y_band_top - 0.4) + DOWN * 0.1)

        self.play(
            FadeIn(list_group, lag_ratio=0.05),
            FadeIn(list_label),
            FadeIn(list_counter),
            run_time=1.0,
        )

        # Orange arrows connecting list nodes in traversal order.
        arrows = []
        for i in range(N - 1):
            start = list_nodes[i].get_right()
            end = list_nodes[i + 1].get_left()
            arrow = Arrow(
                start=start, end=end,
                color=POINTER, stroke_width=3,
                buff=0.08, max_tip_length_to_length_ratio=0.15,
            )
            arrows.append(arrow)
        self.play(*[Create(a) for a in arrows], run_time=1.2)

        self.wait(0.5)

        # ---- Vector traversal --------------------------------------------
        # Fast walk: each cell highlighted briefly, counter ticks by 1.
        cycles = 0
        for i in range(N):
            cycles += CYCLES_VEC
            new_counter = Text(
                f"{cycles} cycles", font_size=22, color=OK,
            ).move_to(vec_counter)
            self.play(
                vector[i].animate.highlight(stroke_color=OK, stroke_width=6),
                vec_counter.animate.become(new_counter),
                run_time=0.18,
            )
        self.wait(0.3)

        # ---- List traversal -----------------------------------------------
        # Slow walk: each hop pauses as if waiting for memory; arrow also
        # flashes so the pointer-chase is explicit.
        cycles = 0
        for i in range(N):
            cycles += CYCLES_LIST
            new_counter = Text(
                f"{cycles} cycles", font_size=22, color=BAD,
            ).move_to(list_counter)
            anims = [
                list_nodes[i][0].animate.highlight(stroke_color=BAD, stroke_width=6),
                list_counter.animate.become(new_counter),
            ]
            if i > 0:
                anims.append(arrows[i - 1].animate.set_color(BAD))
            self.play(*anims, run_time=0.55)

        self.wait(0.6)

        # ---- Final summary -------------------------------------------------
        summary = Text(
            "same work, 100× the time",
            font_size=34, color=FG,
        ).to_edge(DOWN, buff=0.4)
        self.play(Write(summary), run_time=0.8)
        self.wait(1.5)
