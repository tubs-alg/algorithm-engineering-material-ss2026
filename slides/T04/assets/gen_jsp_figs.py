"""Generate Gantt-chart visualizations for the JSP family README.

Each figure is hand-crafted, illustrative — *not* a solver output.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import matplotlib.lines as mlines
from pathlib import Path

import _dark_style

OUT = Path(__file__).parent
# Consistent palette by job index
PALETTE = [
    "#4C78A8", "#F58518", "#54A24B", "#E45756",
    "#72B7B2", "#EECA3B", "#B279A2", "#9D755D",
]

_dark_style.apply()
def gantt(ax, schedule, machines, title, xmax=None,
          breaks=None, setups=None, hatches=None, ylabel="Machine"):
    """schedule: list of (machine_idx, start, dur, job_idx, label)."""
    n = len(machines)
    for m_idx, m_name in enumerate(machines):
        ax.axhline(m_idx, color="#555555", linewidth=0.5, zorder=0)
    for entry in schedule:
        m_idx, start, dur, job, label = entry[:5]
        color = PALETTE[job % len(PALETTE)]
        hatch = (hatches or {}).get(label)
        ax.barh(m_idx, dur, left=start, height=0.7,
                color=color, edgecolor="#888888", linewidth=0.6, hatch=hatch)
        if label:
            ax.text(start + dur / 2, m_idx, label,
                    ha="center", va="center", fontsize=9, color="white",
                    fontweight="bold")
    # Breaks
    for (mi, b0, b1) in (breaks or []):
        ax.barh(mi, b1 - b0, left=b0, height=0.7,
                color="#888888", edgecolor="#888888", linewidth=0.6,
                hatch="///", alpha=0.7)
        ax.text((b0 + b1) / 2, mi, "break",
                ha="center", va="center", fontsize=8, color="white")
    # Setup times: shown as light gray boxes
    for (mi, s0, s1) in (setups or []):
        ax.barh(mi, s1 - s0, left=s0, height=0.7,
                color="#cccccc", edgecolor="#888888", linewidth=0.4)
        ax.text((s0 + s1) / 2, mi, "s",
                ha="center", va="center", fontsize=8, color="#333333", style="italic")

    ax.set_yticks(range(n))
    ax.set_yticklabels(machines)
    ax.invert_yaxis()
    ax.set_xlabel("Time")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if xmax:
        ax.set_xlim(0, xmax)
    ax.set_ylim(n - 0.5, -0.5)
    ax.grid(axis="x", linestyle=":", alpha=0.4)


def job_legend(ax, n_jobs, loc="upper right"):
    handles = [mpatches.Patch(color=PALETTE[i], label=f"Job {i+1}")
               for i in range(n_jobs)]
    ax.legend(handles=handles, loc=loc, fontsize=8, framealpha=0.9)


# ---------------------------------------------------------------------------
# 1) Classical Job Shop — small 3x3
# ---------------------------------------------------------------------------
def fig_basic_jsp():
    # Jobs (machine, dur) sequences:
    # J1: M1(3) -> M2(2) -> M3(2)
    # J2: M2(2) -> M3(1) -> M1(4)
    # J3: M3(4) -> M1(3) -> M2(3)
    # Feasible schedule:
    sched = [
        # (machine, start, dur, job, label)
        (0, 0, 3, 0, "J1.1"),
        (1, 3, 2, 0, "J1.2"),
        (2, 5, 2, 0, "J1.3"),
        (1, 0, 2, 1, "J2.1"),
        (2, 4, 1, 1, "J2.2"),
        (0, 5, 4, 1, "J2.3"),
        (2, 0, 4, 2, "J3.1"),
        (0, 9, 3, 2, "J3.2"),
        (1, 12, 3, 2, "J3.3"),
    ]
    fig, ax = plt.subplots(figsize=(14, 2.4))
    gantt(ax, sched, ["M1", "M2", "M3"],
          "Classical Job Shop — 3 jobs × 3 machines",
          xmax=16)
    job_legend(ax, 3)
    fig.savefig(OUT / "jsp_01_basic_jsp.png")
    plt.close(fig)


def fig_basic_routings():
    """Illustration of the per-job routings used in the basic JSP example."""
    fig, ax = plt.subplots(figsize=(14, 2.2))
    routings = {
        "Job 1": [("M1", 3), ("M2", 2), ("M3", 2)],
        "Job 2": [("M2", 2), ("M3", 1), ("M1", 4)],
        "Job 3": [("M3", 4), ("M1", 3), ("M2", 3)],
    }
    for r, (job, ops) in enumerate(routings.items()):
        ax.text(-0.6, r, job, ha="right", va="center", fontweight="bold")
        x = 0
        color = PALETTE[r]
        for i, (m, d) in enumerate(ops):
            ax.add_patch(FancyBboxPatch((x, r - 0.3), d, 0.6,
                                        boxstyle="round,pad=0.02",
                                        linewidth=0.8, edgecolor="#888888",
                                        facecolor=color))
            ax.text(x + d / 2, r, f"{m}\n({d})",
                    ha="center", va="center", color="white",
                    fontsize=9, fontweight="bold")
            x_next = x + d
            if i < len(ops) - 1:
                ax.annotate("", xy=(x_next + 0.5, r), xytext=(x_next, r),
                            arrowprops=dict(arrowstyle="->", color="#cccccc"))
            x = x_next + 0.5
    ax.set_xlim(-2, 13)
    ax.set_ylim(-0.8, len(routings) - 0.2)
    ax.invert_yaxis()
    ax.set_axis_off()
    ax.set_title("Routings: each job has a fixed sequence of (machine, duration) operations")
    fig.savefig(OUT / "jsp_02_routings.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2) Flexible JSP — operations have alternative machines
# ---------------------------------------------------------------------------
def fig_flexible_jsp():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 3.2),
                                   gridspec_kw={"width_ratios": [1, 1.4]})
    # Left: choice illustration
    ax1.set_title("Each operation can pick from eligible machines")
    ax1.set_axis_off()
    # Op box -> three machine choices
    ax1.add_patch(FancyBboxPatch((0.05, 0.45), 0.22, 0.1,
                                 boxstyle="round,pad=0.02",
                                 facecolor=PALETTE[0], edgecolor="#888888"))
    ax1.text(0.16, 0.5, "Op J1.2", ha="center", va="center",
             color="white", fontweight="bold", fontsize=10)
    for (m, d) in [("M1, dur 2", 0.85), ("M2, dur 4", 0.5), ("M3, dur 3", 0.15)]:
        ax1.annotate("", xy=(0.65, d), xytext=(0.28, 0.5),
                     arrowprops=dict(arrowstyle="->", color="#888888"))
        ax1.text(0.67, d, m, fontsize=10, va="center", ha="left")
    ax1.set_xlim(0, 1); ax1.set_ylim(0, 1)

    # Right: a feasible flexible schedule
    sched = [
        (0, 0, 3, 0, "J1.1"),
        (2, 3, 3, 0, "J1.2"),  # flexible: chose M3 dur 3
        (1, 6, 2, 0, "J1.3"),
        (1, 0, 2, 1, "J2.1"),
        (0, 3, 1, 1, "J2.2"),
        (2, 6, 2, 1, "J2.3"),
        (2, 0, 3, 2, "J3.1"),
        (1, 3, 2, 2, "J3.2"),
        (0, 4, 2, 2, "J3.3"),
    ]
    gantt(ax2, sched, ["M1", "M2", "M3"],
          "A feasible flexible schedule",
          xmax=10)
    job_legend(ax2, 3)
    fig.savefig(OUT / "jsp_03_flexible_jsp.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3) Open shop
# ---------------------------------------------------------------------------
def fig_open_shop():
    # Same processing requirements (each job visits each machine once) but
    # no precedence between operations of the same job.
    sched = [
        (0, 0, 2, 0, "J1.M1"),
        (1, 2, 3, 0, "J1.M2"),
        (2, 5, 2, 0, "J1.M3"),
        (1, 0, 2, 1, "J2.M2"),
        (2, 2, 3, 1, "J2.M3"),
        (0, 5, 1, 1, "J2.M1"),
        (2, 0, 2, 2, "J3.M3"),
        (0, 2, 3, 2, "J3.M1"),
        (1, 5, 2, 2, "J3.M2"),
    ]
    fig, ax = plt.subplots(figsize=(14, 2.6))
    gantt(ax, sched, ["M1", "M2", "M3"],
          "Open Shop — every job uses every machine, order is free",
          xmax=8)
    job_legend(ax, 3)
    fig.savefig(OUT / "jsp_04_open_shop.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4) Flow shop
# ---------------------------------------------------------------------------
def fig_flow_shop():
    # Routing M1 -> M2 -> M3 for all jobs
    durations = [
        [3, 2, 4],
        [2, 4, 1],
        [4, 1, 3],
    ]
    # A simple non-permutation: jobs may pass each other on later machines.
    # Schedule J1, J2, J3 on M1 in order, but J3 jumps J2 on M2.
    sched = [
        (0, 0, 3, 0, "J1"),
        (0, 3, 2, 1, "J2"),
        (0, 5, 4, 2, "J3"),
        (1, 3, 2, 0, "J1"),
        (1, 9, 1, 2, "J3"),   # J3 ahead of J2 here
        (1, 10, 4, 1, "J2"),
        (2, 5, 4, 0, "J1"),
        (2, 10, 3, 2, "J3"),
        (2, 14, 1, 1, "J2"),
    ]
    fig, ax = plt.subplots(figsize=(14, 2.6))
    gantt(ax, sched, ["M1", "M2", "M3"],
          "Flow Shop — all jobs share the routing M1 → M2 → M3",
          xmax=16)
    job_legend(ax, 3)
    fig.savefig(OUT / "jsp_05_flow_shop.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5) Permutation flow shop
# ---------------------------------------------------------------------------
def fig_permutation_flow_shop():
    # All machines see jobs in the same sequence (J1, J2, J3)
    sched = [
        (0, 0, 3, 0, "J1"),
        (0, 3, 2, 1, "J2"),
        (0, 5, 4, 2, "J3"),
        (1, 3, 2, 0, "J1"),
        (1, 5, 4, 1, "J2"),
        (1, 9, 1, 2, "J3"),
        (2, 5, 4, 0, "J1"),
        (2, 9, 1, 1, "J2"),
        (2, 10, 3, 2, "J3"),
    ]
    fig, ax = plt.subplots(figsize=(14, 2.6))
    gantt(ax, sched, ["M1", "M2", "M3"],
          "Permutation Flow Shop — identical job order on every machine",
          xmax=14)
    job_legend(ax, 3)
    fig.savefig(OUT / "jsp_06_permutation_flow_shop.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 6) Hybrid flow shop
# ---------------------------------------------------------------------------
def fig_hybrid_flow_shop():
    # Stage 1: 2 machines, Stage 2: 1 machine, Stage 3: 2 machines
    sched = [
        # Stage 1
        (0, 0, 3, 0, "J1.S1"),
        (1, 0, 4, 1, "J2.S1"),
        (0, 3, 2, 2, "J3.S1"),
        (1, 4, 3, 3, "J4.S1"),
        # Stage 2 (one machine) -- m index 2
        (2, 3, 2, 0, "J1.S2"),
        (2, 5, 3, 2, "J3.S2"),  # J3 finishes S1 at 5
        (2, 8, 2, 1, "J2.S2"),
        (2, 10, 2, 3, "J4.S2"),
        # Stage 3 (two machines) -- m index 3,4
        (3, 5, 3, 0, "J1.S3"),
        (4, 8, 2, 2, "J3.S3"),
        (3, 10, 3, 1, "J2.S3"),
        (4, 12, 2, 3, "J4.S3"),
    ]
    fig, ax = plt.subplots(figsize=(14, 3.4))
    gantt(ax, sched,
          ["S1-M1", "S1-M2", "S2-M1", "S3-M1", "S3-M2"],
          "Hybrid Flow Shop — parallel machines at each stage",
          xmax=16)
    # stage separators
    for y in (1.5, 2.5):
        ax.axhline(y, color="#888888", linewidth=1.2, linestyle="--", zorder=3)
    ax.text(15.7, 0.5, "Stage 1", fontsize=9, va="center",
            ha="right", color="#bbbbbb", style="italic")
    ax.text(15.7, 2.0, "Stage 2", fontsize=9, va="center",
            ha="right", color="#bbbbbb", style="italic")
    ax.text(15.7, 3.5, "Stage 3", fontsize=9, va="center",
            ha="right", color="#bbbbbb", style="italic")
    # Place legend outside the plot to avoid hiding bars
    handles = [mpatches.Patch(color=PALETTE[i], label=f"Job {i+1}")
               for i in range(4)]
    ax.legend(handles=handles, loc="center left",
              bbox_to_anchor=(1.01, 0.5), fontsize=8, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(OUT / "jsp_07_hybrid_flow_shop.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 7) RCPSP — project precedence + resource capacity profile
# ---------------------------------------------------------------------------
def fig_rcpsp():
    # Activities with demands on one renewable resource (capacity 4)
    # A(2,3) -> B(3,2)
    # A      -> C(2,2)
    # B,C    -> D(2,3)
    # Plus parallel  E(4,1)
    acts = [
        ("A", 0, 2, 3, 0),   # name, start, dur, demand, color idx
        ("B", 2, 3, 2, 1),
        ("C", 2, 2, 2, 2),
        ("D", 5, 2, 3, 3),
        ("E", 0, 4, 1, 4),
    ]
    pos = {name: i for i, (name, *_) in enumerate(acts)}      # row index by name
    span = {name: (s, s + d) for name, s, d, *_ in acts}      # (start, end) by name
    # Precedence: predecessor must finish before successor starts.
    prec = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]   # E runs in parallel

    fig, axes = plt.subplots(2, 1, figsize=(14, 5.0),
                             gridspec_kw={"height_ratios": [1, 1.1]},
                             sharex=True)
    ax1, ax2 = axes

    # Gantt above
    for i, (name, s, d, q, c) in enumerate(acts):
        ax1.barh(i, d, left=s, height=0.7,
                 color=PALETTE[c], edgecolor="#888888", linewidth=0.6)
        ax1.text(s + d / 2, i, f"{name}  (q={q})",
                 ha="center", va="center", color="white",
                 fontsize=11, fontweight="bold")

    # Precedence arrows: end of predecessor -> start of successor
    for u, v in prec:
        ax1.annotate(
            "", xy=(span[v][0], pos[v]), xytext=(span[u][1], pos[u]),
            arrowprops=dict(arrowstyle="-|>", color="#cccccc", lw=1.4,
                            shrinkA=2, shrinkB=2,
                            connectionstyle="arc3,rad=0.15"),
            zorder=5,
        )
    ax1.set_yticks(range(len(acts)))
    ax1.set_yticklabels([a[0] for a in acts])
    ax1.invert_yaxis()
    ax1.set_title("RCPSP — activities with precedence and renewable-resource demand")
    ax1.grid(axis="x", linestyle=":", alpha=0.4)
    ax1.set_xlim(0, 8)

    # Capacity profile below
    T = 8
    profile = [0] * T
    for _, s, d, q, _ in acts:
        for t in range(s, s + d):
            profile[t] += q
    cap = 4
    # Portion within capacity (blue) and the over-capacity excess (red)
    within = [min(p, cap) for p in profile]
    excess = [max(p - cap, 0) for p in profile]
    ax2.bar(range(T), within, width=1.0, align="edge",
            color="#A0C8E0", edgecolor="#888888", linewidth=0.6)
    ax2.bar(range(T), excess, width=1.0, align="edge", bottom=within,
            color="#E05050", edgecolor="#888888", linewidth=0.6)
    ax2.axhline(cap, color="red", linestyle="--", linewidth=1.5)
    ax2.text(7.6, 4.15, "capacity = 4", color="red", fontsize=11, ha="right")
    # Label the over-capacity region
    over = [t for t, e in enumerate(excess) if e > 0]
    if over:
        mid = (over[0] + over[-1] + 1) / 2
        ax2.annotate("over capacity", xy=(mid, cap + 0.5),
                     xytext=(mid, 5.6), ha="center", color="#E05050",
                     fontsize=11, fontweight="bold",
                     arrowprops=dict(arrowstyle="-|>", color="#E05050", lw=1.4))
    ax2.set_ylim(0, 6)
    ax2.set_ylabel("Resource use")
    ax2.set_xlabel("Time")
    ax2.set_title("Resource profile exceeds the capacity line — this schedule is infeasible")
    ax2.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(OUT / "jsp_08_rcpsp.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 8) Multi-mode RCPSP
# ---------------------------------------------------------------------------
def fig_multimode():
    fig, ax = plt.subplots(figsize=(14, 2.6))
    modes = [
        ("Mode 1: fast & expensive", 2, 4, PALETTE[0]),
        ("Mode 2: standard",          4, 2, PALETTE[1]),
        ("Mode 3: slow & cheap",      6, 1, PALETTE[2]),
    ]
    for i, (label, d, q, c) in enumerate(modes):
        ax.barh(i, d, left=0, height=0.7,
                color=c, edgecolor="#888888", linewidth=0.6)
        ax.text(d + 0.2, i, f"  dur={d}, demand q={q}",
                va="center", fontsize=10)
    ax.set_yticks(range(len(modes)))
    ax.set_yticklabels([m[0] for m in modes])
    ax.invert_yaxis()
    ax.set_xlim(0, 11)
    ax.set_xlabel("Time")
    ax.set_title("Multi-mode: pick one (duration, demand) pair per activity")
    fig.savefig(OUT / "jsp_09_multimode.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 9) Sequence-dependent setup times
# ---------------------------------------------------------------------------
def fig_setup_times():
    fig, (ax, axm) = plt.subplots(
        1, 2, figsize=(13, 2.8),
        gridspec_kw={"width_ratios": [3, 1.15]})
    # Three families of products: A, B, C. Setup needed when family switches.
    sched = [
        (0, 0, 3, 0, "A1"),
        (0, 3, 3, 0, "A2"),   # no setup (same family)
        (0, 6, 2, 0, ""),     # setup gap
        (0, 8, 3, 1, "B1"),
        (0, 11, 3, 2, ""),    # bigger setup B->C
        (0, 14, 2, 2, "C1"),
    ]
    setups = [(0, 6, 8), (0, 11, 14)]
    # Replace last two "" entries with actual bars first.
    fig_sched = [s for s in sched if s[4]]
    gantt(ax, fig_sched, ["M1"],
          "Sequence-dependent setup times — gaps depend on which task came before",
          xmax=17, setups=setups)
    # Annotate setup blocks
    ax.text(7, -0.55, "setup A→B = 2", ha="center", fontsize=8, color="#bbbbbb")
    ax.text(12.5, -0.55, "setup B→C = 3", ha="center", fontsize=8, color="#bbbbbb")
    ax.set_ylim(0.6, -0.8)
    # No legend: bars are labeled by family (A1/A2/B1/C1) in family colors,
    # the grey "s" blocks + "setup X→Y" annotations explain the setup gaps,
    # and the matrix axes label the families A/B/C.

    # Setup-cost matrix (from row -> to col); asymmetric, zero on the diagonal.
    fams = ["A", "B", "C"]
    cost = [
        [0, 2, 4],   # from A
        [1, 0, 3],   # from B  (B->C = 3 matches the Gantt)
        [3, 1, 0],   # from C
    ]
    n = len(fams)
    vmax = max(max(row) for row in cost)
    axm.imshow(cost, cmap="YlOrRd", vmin=0, vmax=vmax, aspect="equal")
    axm.set_anchor("W")   # left-align the square so it sits near the Gantt
    for r in range(n):
        for c in range(n):
            v = cost[r][c]
            # white text on the darker (high-cost) cells, dark text otherwise
            tc = "white" if v > 0.6 * vmax else "#333333"
            axm.text(c, r, str(v), ha="center", va="center",
                     fontsize=11, fontweight="bold", color=tc)
    axm.set_xticks(range(n))
    axm.set_yticks(range(n))
    axm.set_xticklabels(fams)
    axm.set_yticklabels(fams)
    axm.set_xlabel("to", fontsize=9, color=_dark_style.FG)
    axm.set_ylabel("from", fontsize=9, color=_dark_style.FG)
    axm.xaxis.set_label_position("top")
    axm.xaxis.tick_top()
    axm.tick_params(length=0)
    for spine in axm.spines.values():
        spine.set_visible(False)
    axm.set_title("Setup cost matrix", fontsize=11, color=_dark_style.FG, pad=18)

    fig.tight_layout()
    fig.savefig(OUT / "jsp_10_setup_times.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 10) No-wait and blocking flow shop
# ---------------------------------------------------------------------------
def fig_no_wait_blocking():
    fig, axes = plt.subplots(1, 2, figsize=(14, 3.0))
    # Left: no-wait — each job's tasks chain immediately end-to-end
    # Jobs: J1 (3,2,2), J2 (1,3,2)
    sched_nw = [
        (0, 0, 3, 0, "J1"),
        (1, 3, 2, 0, "J1"),
        (2, 5, 2, 0, "J1"),
        (0, 7, 1, 1, "J2"),   # delayed so M2/M3 are free at the right moment
        (1, 8, 3, 1, "J2"),
        (2, 11, 2, 1, "J2"),
    ]
    gantt(axes[0], sched_nw, ["M1", "M2", "M3"],
          "No-Wait — no idle time between job's consecutive ops",
          xmax=14)
    # Right: blocking — job stays on machine until the next is free.
    # J1 holds M2 for a long stretch (2..6); J2 finishes M1 at 4 but
    # cannot move to M2 until 6, so M1 is held in "blocked" state [4..6].
    sched_bl = [
        (0, 0, 2, 0, "J1"),      # J1 on M1 [0..2]
        (1, 2, 4, 0, "J1"),      # J1 on M2 [2..6]  (long stay)
        (2, 6, 2, 0, "J1"),      # J1 on M3 [6..8]
        (0, 2, 2, 1, "J2"),      # J2 on M1 [2..4]
        (0, 4, 2, 1, "block"),   # blocked on M1 [4..6] because M2 busy until 6
        (1, 6, 2, 1, "J2"),      # J2 on M2 [6..8]
        (2, 8, 2, 1, "J2"),      # J2 on M3 [8..10]
    ]
    # Render manually so the "block" can use hatch
    ax2 = axes[1]
    for entry in sched_bl:
        m_idx, start, dur, job, label = entry
        if label == "block":
            ax2.barh(m_idx, dur, left=start, height=0.7,
                     color=PALETTE[job], edgecolor="#888888", linewidth=0.6,
                     hatch="xx", alpha=0.85)
            ax2.text(start + dur / 2, m_idx, "blocked",
                     ha="center", va="center", fontsize=8, color="white",
                     fontweight="bold")
        else:
            ax2.barh(m_idx, dur, left=start, height=0.7,
                     color=PALETTE[job], edgecolor="#888888", linewidth=0.6)
            ax2.text(start + dur / 2, m_idx, label,
                     ha="center", va="center", fontsize=9, color="white",
                     fontweight="bold")
    ax2.set_yticks(range(3)); ax2.set_yticklabels(["M1", "M2", "M3"])
    ax2.invert_yaxis()
    ax2.set_xlim(0, 11); ax2.set_xlabel("Time"); ax2.set_ylabel("Machine")
    ax2.set_title("Blocking — finished job holds machine until next stage free")
    ax2.grid(axis="x", linestyle=":", alpha=0.4)
    for ax in axes:
        job_legend(ax, 2)
    fig.savefig(OUT / "jsp_11_nowait_blocking.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 11) Resource breaks
# ---------------------------------------------------------------------------
def fig_breaks():
    fig, axes = plt.subplots(1, 2, figsize=(12, 2.6))
    # Left: tasks must avoid the break entirely. Same break and task lengths
    # as the right, but T2 (3u) cannot fit in the 1u gap before the break, so
    # the machine idles and T2 runs whole after the break.
    ax = axes[0]
    sched = [(0, 0, 3, 0, "T1"), (0, 5, 3, 1, "T2")]
    gantt(ax, sched, ["M1"],
          "Tasks must avoid the break",
          xmax=10, breaks=[(0, 4, 5)])
    # Right: tasks may be interrupted, stretching duration
    ax = axes[1]
    # T2 starts at 3, work 1u then pauses 1u for break, then resumes
    sched = [(0, 0, 3, 0, "T1"), (0, 3, 1, 1, "T2a"),
             (0, 5, 2, 1, "T2b")]
    gantt(ax, sched, ["M1"],
          "Tasks may be interrupted by breaks",
          xmax=10, breaks=[(0, 4, 5)])
    fig.savefig(OUT / "jsp_12_breaks.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 12) Optional tasks / alternative process plans
# ---------------------------------------------------------------------------
def fig_optional():
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.0))
    # Left: two alternative paths, illustrated as boxes
    ax = axes[0]
    ax.set_axis_off()
    ax.set_xlim(0, 10); ax.set_ylim(0, 6)
    ax.set_title("Two alternative plans for one product")
    # Plan 1: A -> B
    ax.add_patch(FancyBboxPatch((0.5, 4), 1.8, 1.0,
                                boxstyle="round,pad=0.05",
                                facecolor=PALETTE[0], edgecolor="#888888"))
    ax.text(1.4, 4.5, "A (dur 2)", ha="center", va="center",
            color="white", fontweight="bold")
    ax.annotate("", xy=(3, 4.5), xytext=(2.4, 4.5),
                arrowprops=dict(arrowstyle="->"))
    ax.add_patch(FancyBboxPatch((3.0, 4), 1.8, 1.0,
                                boxstyle="round,pad=0.05",
                                facecolor=PALETTE[1], edgecolor="#888888"))
    ax.text(3.9, 4.5, "B (dur 2)", ha="center", va="center",
            color="white", fontweight="bold")
    ax.text(0.1, 5.4, "Plan 1", fontsize=10, fontweight="bold")
    # Plan 2: C
    ax.add_patch(FancyBboxPatch((0.5, 1.5), 4.3, 1.0,
                                boxstyle="round,pad=0.05",
                                facecolor=PALETTE[2], edgecolor="#888888"))
    ax.text(2.65, 2.0, "C (dur 5)", ha="center", va="center",
            color="white", fontweight="bold")
    ax.text(0.1, 2.9, "Plan 2", fontsize=10, fontweight="bold")
    ax.text(6.0, 3.5, "select exactly one\nof {A+B, C}",
            fontsize=10, style="italic")

    # Right: chosen schedule
    sched = [(0, 0, 2, 0, "A"), (0, 2, 2, 1, "B")]
    gantt(axes[1], sched, ["M1"],
          "Chosen schedule (Plan 1 — A then B)",
          xmax=6)
    fig.savefig(OUT / "jsp_13_optional.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 13) Objectives
# ---------------------------------------------------------------------------
def fig_objectives():
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.0))
    # Two schedules for the same 3 jobs; J1 has due date 4, J2 due 7, J3 due 9
    due = [4, 7, 9]
    schedules = [
        # makespan-optimal: ends at 9 but J1 misses its due date
        [(0, 0, 5, 1, "J2"),
         (0, 5, 4, 2, "J3"),
         (0, 9, 3, 0, "J1")],
        # tardiness-optimal: J1 first to meet deadline
        [(0, 0, 3, 0, "J1"),
         (0, 3, 5, 1, "J2"),
         (0, 8, 4, 2, "J3")],
    ]
    titles = ["Minimize makespan: J1 finishes very late",
              "Minimize total tardiness: J1 first"]
    for ax, sched, title in zip(axes, schedules, titles):
        gantt(ax, sched, ["M1"], title, xmax=13)
        ax.set_ylim(0.7, -0.7)
        for i, d in enumerate(due):
            ax.axvline(d, color=PALETTE[i], linestyle=":", linewidth=1.3)
            ax.text(d + 0.15, -0.55, f"d{i+1}", ha="left", fontsize=9,
                    color=PALETTE[i], fontweight="bold")
        job_legend(ax, 3)
    fig.suptitle("Different objectives → different schedules", fontsize=12,
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "jsp_14_objectives.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 14) Release dates / deadlines / due dates summary
# ---------------------------------------------------------------------------
def fig_time_windows():
    fig, ax = plt.subplots(figsize=(15, 3.3))
    # Three jobs, each scheduled on its own row so release/due/deadline
    # markers sit clearly on the job's own lane.
    # Three regimes:
    #   J1 finishes early (well within due);
    #   J2 finishes after its due date but before its deadline (tardy but legal);
    #   J3 finishes right at its due date (on time).
    # Markers are spread along x so no two share the same column.
    sched = [(0, 1, 2, 0, "J1"),
             (1, 4, 3, 1, "J2"),
             (2, 8, 3, 2, "J3")]
    gantt(ax, sched, ["J1", "J2", "J3"],
          "Each job: release date $r_j$, due date $d_j$, hard deadline $D_j$",
          xmax=14, ylabel="Job")

    # (job_index, release, due, deadline)
    annots = [(0, 1, 4, 5),
              (1, 3, 6, 9),
              (2, 7, 11, 13)]

    release_c = "#0f766e"  # teal
    due_c = "#b45309"      # amber
    dead_c = "#b91c1c"     # red
    half = 0.38            # half row-height for markers

    label_off = 0.02  # small gap above the marker top; larger values push
                      # the label into the row above (axis is inverted)

    for job, r, due, dl in annots:
        y = job  # gantt machine index == row position (y-axis inverted)

        # Release: solid green vertical with right-pointing arrow head
        ax.annotate("", xy=(r + 0.35, y), xytext=(r, y),
                    arrowprops=dict(arrowstyle="-|>", color=release_c,
                                    lw=2.0), zorder=5)
        ax.plot([r, r], [y - half, y + half], color=release_c,
                lw=2.0, zorder=5)
        ax.text(r, y - half - label_off, f"$r_{{{job+1}}}$",
                ha="center", va="bottom", fontsize=10,
                color=release_c, fontweight="bold")

        # Due: dotted amber
        ax.plot([due, due], [y - half, y + half], color=due_c,
                linestyle=":", lw=2.0, zorder=5)
        ax.text(due, y - half - label_off, f"$d_{{{job+1}}}$",
                ha="center", va="bottom", fontsize=10,
                color=due_c, fontweight="bold")

        # Deadline: solid red barrier
        ax.plot([dl, dl], [y - half, y + half], color=dead_c,
                lw=2.5, zorder=5)
        ax.add_patch(Rectangle((dl, y - half), 0.18, 2 * half,
                               facecolor=dead_c, alpha=0.25,
                               edgecolor="none", zorder=4))
        ax.text(dl, y - half - label_off, f"$D_{{{job+1}}}$",
                ha="center", va="bottom", fontsize=10,
                color=dead_c, fontweight="bold")

    # Compact legend in the upper-right (above the existing job legend)
    legend = [
        mlines.Line2D([], [], color=release_c, lw=2.0,
                      label=r"release $r_j$ — earliest start"),
        mlines.Line2D([], [], color=due_c, lw=2.0, linestyle=":",
                      label=r"due $d_j$ — soft target"),
        mlines.Line2D([], [], color=dead_c, lw=2.5,
                      label=r"deadline $D_j$ — hard cutoff"),
    ]
    ax.legend(handles=legend, loc="upper left",
              bbox_to_anchor=(0.0, -0.18), ncol=3,
              fontsize=9, frameon=False)

    ax.set_ylim(2.7, -0.7)
    fig.tight_layout()
    fig.savefig(OUT / "jsp_15_time_windows.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 15) Consumable resources
# ---------------------------------------------------------------------------
def fig_consumable():
    fig, axes = plt.subplots(2, 1, figsize=(14, 3.6),
                             gridspec_kw={"height_ratios": [1, 1.1]},
                             sharex=True)
    ax1, ax2 = axes
    # Activities that produce or consume from a stock (e.g. raw material).
    acts = [
        ("Deliver-1", 0, 1, +5, 4),
        ("Produce-A", 1, 3, -3, 0),
        ("Deliver-2", 2, 1, +4, 4),
        ("Produce-B", 4, 3, -4, 1),
        ("Produce-C", 5, 2, -2, 2),
    ]
    for i, (name, s, d, q, c) in enumerate(acts):
        col = PALETTE[c]
        ax1.barh(i, d, left=s, height=0.7,
                 color=col, edgecolor="#888888", linewidth=0.6)
        # quantity inside bar
        if d >= 2:
            ax1.text(s + d / 2, i, f"{q:+d}",
                     ha="center", va="center", color="white",
                     fontsize=10, fontweight="bold")
        else:
            ax1.text(s + d + 0.05, i, f"{q:+d}",
                     ha="left", va="center", color=col,
                     fontsize=10, fontweight="bold")
    ax1.set_yticks(range(len(acts)))
    ax1.set_yticklabels([a[0] for a in acts])
    ax1.invert_yaxis()
    ax1.set_title("Consumable resource — stock is produced and consumed over time")
    ax1.grid(axis="x", linestyle=":", alpha=0.4)
    ax1.set_xlim(0, 8)

    # Stock profile: increment at activity start (lump-sum convention here)
    T = 9
    stock = [0] * (T + 1)
    for _, s, d, q, _ in acts:
        # produce at end, consume at start (typical convention)
        if q > 0:
            stock[s + d] += q
        else:
            stock[s] += q
    # cumulative
    profile = []
    cur = 0
    for v in stock:
        cur += v
        profile.append(cur)
    ax2.step(range(T + 1), profile, where="post",
             color="#4C78A8", linewidth=2.0)
    ax2.fill_between(range(T + 1), 0, profile, step="post",
                     alpha=0.2, color="#4C78A8")
    ax2.axhline(0, color="red", linestyle="--", linewidth=1.2)
    ax2.text(7.7, 0.2, "stock ≥ 0 required", color="red", fontsize=9, ha="right")
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Stock level")
    ax2.set_title("Cumulative stock — must remain non-negative at all times")
    ax2.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(OUT / "jsp_16_consumable.png")
    plt.close(fig)


def main():
    for f in [
        fig_basic_routings,
        fig_basic_jsp,
        fig_flexible_jsp,
        fig_open_shop,
        fig_flow_shop,
        fig_permutation_flow_shop,
        fig_hybrid_flow_shop,
        fig_rcpsp,
        fig_multimode,
        fig_setup_times,
        fig_no_wait_blocking,
        fig_breaks,
        fig_optional,
        fig_objectives,
        fig_time_windows,
        fig_consumable,
    ]:
        f()
        print(f"  ✓ {f.__name__}")


if __name__ == "__main__":
    main()
