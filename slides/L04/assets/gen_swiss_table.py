"""Swiss table — metadata row scanned in one SIMD instruction.

Emits swiss_table.png. Top row: 16 one-byte metadata tags (7-bit H2 + flag).
Bottom row: 16 (key, value) data slots, wider. A highlighted group of 16
metadata bytes is framed with the label "one SSE2 compare"; two of them
match the target tag, and arrows go from just those down to the data row.
"""

import matplotlib.pyplot as plt

from _viz_style import (
    ACCENT, CELL, CELL_GAP, CELL_H, CELL_W, FG, PTR,
    draw_annotation, draw_cell, draw_composite_cell, draw_pointer,
    save, setup_mpl,
)

setup_mpl()

N = 16
# Metadata: "E" empty, "D" deleted, otherwise a two-hex-nibble H2 value.
# Two slots match the target tag 0x42 — these are probed in full.
META = [
    "E",  "9c", "42", "7a", "E",  "13", "a1", "42",
    "5f", "E",  "c8", "03", "D",  "E",  "22", "e7",
]
TARGET = "42"
MATCHES = [i for i, m in enumerate(META) if m == TARGET]

# Data slots: only the probed ones carry a visible payload.
DATA = {
    2: ("cat", "C"),
    7: ("bee", "B"),
    0: None, 1: ("ink", "I"), 3: ("owl", "O"), 5: ("pig", "P"),
    6: ("ant", "A"), 8: ("dog", "D"), 10: ("rat", "R"),
    11: ("fox", "F"), 14: ("cow", "Z"), 15: ("hen", "H"),
}

META_W = CELL_W * 0.55
META_H = CELL_H * 0.65
META_Y = 2.8

DATA_K_W = CELL_W * 0.85
DATA_V_W = CELL_W * 0.55
DATA_PAIR_W = DATA_K_W + DATA_V_W                    # pitch
DATA_INNER_W = DATA_PAIR_W - CELL_GAP                # visible slot width
DATA_K_INNER = DATA_K_W * (DATA_INNER_W / DATA_PAIR_W)
DATA_V_INNER = DATA_INNER_W - DATA_K_INNER
DATA_Y = 0.6

FIG_W = 13.0

fig, ax = plt.subplots(figsize=(FIG_W, 4.2))
ax.set_title(
    "Swiss table — 16 metadata bytes scanned in one SIMD compare, only matches load data",
    fontsize=12, fontweight="bold", color=FG, loc="left", pad=10,
)

# -- Metadata row ---------------------------------------------------------
ax.text(
    0.3, META_Y + META_H / 2, "H2 →",
    ha="right", va="center", color=CELL["index"],
    fontfamily="monospace", fontweight="bold", fontsize=10,
)
META_X0 = 0.6
for i, tag in enumerate(META):
    x = META_X0 + i * META_W
    if tag == "E":
        color, text_color = CELL["cold"], "#888"
    elif tag == "D":
        color, text_color = "#4a2e2e", "#b88"
    elif i in MATCHES:
        color, text_color = CELL["hot"], "white"
    else:
        color, text_color = CELL["control"], "white"
    draw_cell(ax, x, META_Y, tag, color, w=META_W, h=META_H,
              fontsize=7, text_color=text_color)

# Frame around all 16 metadata cells — "one SSE2 compare".
frame_x = META_X0 - 0.04
frame_w = N * META_W - CELL_GAP + 0.02
ax.plot(
    [frame_x, frame_x + frame_w, frame_x + frame_w, frame_x, frame_x],
    [META_Y - 0.1, META_Y - 0.1,
     META_Y + META_H + 0.1, META_Y + META_H + 0.1, META_Y - 0.1],
    color=CELL["cache"], lw=1.4, linestyle=(0, (2, 2)),
)
ax.text(
    frame_x + frame_w / 2, META_Y + META_H + 0.22,
    f"one SIMD compare vs tag = 0x{TARGET}",
    ha="center", va="bottom",
    fontsize=8, color=CELL["cache"], fontstyle="italic", fontweight="bold",
)

# -- Data row -------------------------------------------------------------
ax.text(
    0.3, DATA_Y + CELL_H / 2, "data →",
    ha="right", va="center", color=CELL["index"],
    fontfamily="monospace", fontweight="bold", fontsize=10,
)
DATA_X0 = 0.6
# Align data columns to the metadata columns (both have 16 equally spaced
# entries, so use the same x formula with a different pitch).
for i in range(N):
    x = DATA_X0 + i * DATA_PAIR_W
    entry = DATA.get(i)
    if entry is None:
        segs = [
            {"w": DATA_K_INNER, "text": "·", "color": CELL["cold"], "text_color": "#666"},
            {"w": DATA_V_INNER, "text": "·", "color": CELL["cold"], "text_color": "#666"},
        ]
    else:
        k, v = entry
        # Highlight matches, grey everything else so the eye follows arrows.
        key_color = CELL["hot"] if i in MATCHES else CELL["data"]
        val_color = CELL["warn"] if i in MATCHES else CELL["index"]
        segs = [
            {"w": DATA_K_INNER, "text": k, "color": key_color},
            {"w": DATA_V_INNER, "text": v, "color": val_color},
        ]
    draw_composite_cell(ax, x, DATA_Y, segs)

# -- Arrows from the matching metadata cells down to their data rows -----
for i in MATCHES:
    src_x = META_X0 + i * META_W + (META_W - CELL_GAP) / 2
    dst_x = DATA_X0 + i * DATA_PAIR_W + DATA_K_INNER / 2
    draw_pointer(
        ax,
        (src_x, META_Y - 0.02),
        (dst_x, DATA_Y + CELL_H + 0.02),
    )

# Annotation
draw_annotation(
    ax, FIG_W - 0.5, (META_Y + DATA_Y) / 2 + 0.3,
    "only matches\ntouch the data row",
    color=ACCENT, ha="right",
)

ax.set_xlim(-0.3, FIG_W + 0.3)
ax.set_ylim(-0.3, META_Y + META_H + 0.8)
ax.axis("off")

plt.tight_layout()
save(fig, "swiss_table.png")
