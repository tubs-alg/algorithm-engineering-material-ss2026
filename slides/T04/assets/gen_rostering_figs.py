"""Generate roster-matrix visualizations for the Employee Rostering README.

Each figure is illustrative — hand-built, not solver output. The goal is
a clean visual vocabulary that recurs across the document so readers
quickly recognize shift codes, off days, unavailable slots, etc.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from pathlib import Path

import _dark_style

OUT = Path(__file__).parent
# Shift codes and colours
SHIFTS = {
    "M": ("Morning", "#7FB3D5"),
    "A": ("Afternoon", "#F4A261"),
    "N": ("Night", "#5D4E8C"),
    "-": ("Off", "#2a2a2a"),
    "U": ("Unavailable", "#BBBBBB"),
    "P": ("Preferred off", "#C7E9C0"),
    "V": ("Vacation", "#D4A6E0"),
}

_dark_style.apply()
DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su",
        "Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def draw_roster(ax, roster, employees, days=None, title="",
                highlight=None, hatch_cells=None, annotate=None,
                equal_aspect=True):
    """Draw a roster matrix.

    roster: 2D list of strings (one of SHIFTS keys)
    employees: row labels
    days: column labels (defaults to DAYS[:n])
    highlight: list of (row, col, color) — draw a coloured border
    hatch_cells: list of (row, col, hatch) — overlay a hatch pattern
    annotate: list of (row, col, text, color) — add a small annotation
    """
    n_emp = len(employees)
    n_days = len(roster[0])
    days = days or DAYS[:n_days]
    for r in range(n_emp):
        for c in range(n_days):
            code = roster[r][c]
            label, color = SHIFTS[code]
            ax.add_patch(Rectangle((c, n_emp - 1 - r), 1, 1,
                                   facecolor=color, edgecolor="#888888",
                                   linewidth=0.6))
            txt_color = "white" if code in ("N", "U", "V") else "#222"
            if code == "-":
                txt_color = "#aaaaaa"
            ax.text(c + 0.5, n_emp - 1 - r + 0.5, code,
                    ha="center", va="center", fontsize=10,
                    fontweight="bold", color=txt_color)

    # Weekend shading
    for c, d in enumerate(days):
        if d in ("Sa", "Su"):
            ax.add_patch(Rectangle((c, 0), 1, n_emp,
                                   facecolor="#8a6a30",
                                   alpha=0.30, edgecolor="none", zorder=-1))

    for (r, c, col) in (highlight or []):
        ax.add_patch(Rectangle((c, n_emp - 1 - r), 1, 1,
                               facecolor="none", edgecolor=col,
                               linewidth=2.5, zorder=5))
    for (r, c, hatch) in (hatch_cells or []):
        ax.add_patch(Rectangle((c, n_emp - 1 - r), 1, 1,
                               facecolor="none", edgecolor="#888888",
                               hatch=hatch, linewidth=0.4, zorder=4))
    for (r, c, text, color) in (annotate or []):
        ax.text(c + 0.5, n_emp - 1 - r + 0.5, text,
                ha="center", va="center", fontsize=10,
                color=color, fontweight="bold")

    ax.set_xlim(0, n_days)
    ax.set_ylim(0, n_emp)
    ax.set_xticks([c + 0.5 for c in range(n_days)])
    ax.set_xticklabels(days, fontsize=9)
    ax.set_yticks([n_emp - 1 - r + 0.5 for r in range(n_emp)])
    ax.set_yticklabels(employees, fontsize=10)
    ax.xaxis.tick_top()
    if equal_aspect:
        ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(title, pad=12)


def shift_legend(ax, keys=("M", "A", "N", "-"), loc="center left", ncol=1):
    handles = [mpatches.Patch(facecolor=SHIFTS[k][1], edgecolor="#888888",
                              label=f"{k} — {SHIFTS[k][0]}") for k in keys]
    ax.legend(handles=handles, loc=loc, fontsize=8, framealpha=0.95,
              ncol=ncol, bbox_to_anchor=(1.01, 0.5))


# ---------------------------------------------------------------------------
# 1) Basic roster: 5 employees × 14 days, 3 shifts
# ---------------------------------------------------------------------------
def fig_basic_roster():
    employees = ["Anna", "Ben", "Carla", "Dan", "Eva"]
    # 14-day roster. Each day needs at least one M, one A, one N.
    roster = [
        list("MMM--AANN--MMM"),
        list("AA--NNMMA--AAN"),
        list("NN-MM-AANN-MM-"),
        list("--AANNM--AANN-"),
        list("---MM-NNMA--AA"),
    ]
    # Make every column have at least M/A/N coverage. Quick verify:
    fig, ax = plt.subplots(figsize=(10, 3.0))
    draw_roster(ax, roster, employees,
                title="A 2-week roster — 5 employees, three shift types")
    shift_legend(ax)
    fig.savefig(OUT / "ros_01_basic_roster.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2) Coverage requirements — how many people per shift per day
# ---------------------------------------------------------------------------
def fig_coverage():
    days = DAYS[:7]
    demand = {
        "Morning":   [3, 3, 4, 4, 3, 2, 2],
        "Afternoon": [3, 3, 3, 3, 4, 4, 3],
        "Night":     [2, 2, 2, 2, 2, 3, 3],
    }
    fig, ax = plt.subplots(figsize=(15, 3.3))
    x = np.arange(len(days))
    bottom = np.zeros(len(days))
    colors = [SHIFTS["M"][1], SHIFTS["A"][1], SHIFTS["N"][1]]
    for (name, vals), col in zip(demand.items(), colors):
        ax.bar(x, vals, bottom=bottom, color=col, edgecolor="#888888",
               linewidth=0.6, label=name, width=0.7)
        for i, v in enumerate(vals):
            ax.text(x[i], bottom[i] + v / 2, str(v),
                    ha="center", va="center", fontweight="bold",
                    color="white" if name == "Night" else "#222",
                    fontsize=9)
        bottom += np.array(vals)
    ax.set_xticks(x)
    ax.set_xticklabels(days)
    ax.set_ylabel("Required headcount")
    ax.set_title("Shift demand varies by day and shift type")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)
    fig.savefig(OUT / "ros_02_coverage.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3) Skills / qualifications matrix
# ---------------------------------------------------------------------------
def fig_skills():
    employees = ["Anna", "Ben", "Carla", "Dan", "Eva"]
    skills = ["First Aid", "Forklift", "Cashier", "Night cert.", "Trainer"]
    mat = np.array([
        [1, 0, 1, 0, 1],
        [1, 1, 0, 1, 0],
        [0, 1, 1, 0, 0],
        [1, 1, 0, 1, 1],
        [0, 0, 1, 0, 0],
    ])
    fig, ax = plt.subplots(figsize=(7, 3))
    for r in range(len(employees)):
        for c in range(len(skills)):
            color = "#54A24B" if mat[r, c] else "#2a2a2a"
            ax.add_patch(Rectangle((c, len(employees) - 1 - r), 1, 1,
                                   facecolor=color, edgecolor="#888888",
                                   linewidth=0.6))
            ax.text(c + 0.5, len(employees) - 1 - r + 0.5,
                    "✓" if mat[r, c] else "",
                    ha="center", va="center", fontsize=12,
                    color="white", fontweight="bold")
    ax.set_xlim(0, len(skills))
    ax.set_ylim(0, len(employees))
    ax.set_xticks([c + 0.5 for c in range(len(skills))])
    ax.set_xticklabels(skills, fontsize=9, rotation=20, ha="left")
    ax.xaxis.tick_top()
    ax.set_yticks([len(employees) - 1 - r + 0.5 for r in range(len(employees))])
    ax.set_yticklabels(employees, fontsize=10)
    ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title("Skill matrix — only certified employees may take certain shifts",
                 pad=12)
    fig.savefig(OUT / "ros_03_skills.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4) Availability and time-off
# ---------------------------------------------------------------------------
def fig_availability():
    employees = ["Anna", "Ben", "Carla", "Dan", "Eva"]
    # Show only requested off / unavailable / vacation, no shifts assigned yet
    roster = [
        list("---PP----V-VVV"),  # Anna: prefers Th/Fr off, vacation later
        list("UU-----U------"),  # Ben: unavailable Mo/Tu and next Mo
        list("-------P------"),  # Carla: prefers next Mo off
        list("-V-V------U---"),  # Dan: split vacation
        list("------UU------"),  # Eva: unavailable weekend
    ]
    fig, ax = plt.subplots(figsize=(10, 3.0))
    draw_roster(ax, roster, employees,
                title="Availability inputs from employees (before scheduling)")
    shift_legend(ax, keys=("U", "P", "V", "-"))
    fig.savefig(OUT / "ros_04_availability.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5) Hard vs soft constraints — same roster, two views
# ---------------------------------------------------------------------------
def fig_hard_soft():
    employees = ["Anna", "Ben", "Carla", "Dan", "Eva"]
    roster = [
        list("MMM--AANN--MMM"),
        list("AANNMM-A--AANN"),   # Ben: M after N on day 4 (rest violation)
        list("NN-MM-AANN-MM-"),
        list("--AANNM--AANN-"),
        list("---MM-NNMA--AA"),
    ]
    highlight = [
        (1, 3, "red"),
        (1, 4, "red"),
    ]
    fig, ax = plt.subplots(figsize=(11, 3.4))
    draw_roster(ax, roster, employees,
                title="Hard violation: Night (We) directly followed by Morning (Th)",
                highlight=highlight)
    # Label sits directly above the highlighted transition (seam at x=4,
    # top of Ben's row at y=4) with a short vertical arrow pointing down.
    ax.annotate("Night → Morning\n< 11h rest ✗",
                xy=(4.0, 4.0), xytext=(4.0, 5.4),
                fontsize=10, color="#ff5566", fontweight="bold",
                ha="center", va="bottom",
                arrowprops=dict(arrowstyle="->", color="#ff5566", lw=1.6))
    ax.set_ylim(0, 6.6)
    shift_legend(ax)
    fig.savefig(OUT / "ros_05_hard_soft.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 6) Rest periods / consecutive shifts
# ---------------------------------------------------------------------------
def fig_rest():
    fig, ax = plt.subplots(figsize=(16, 3.4))
    ax.set_xlim(-2, 50); ax.set_ylim(-1.8, 3.0)
    ax.set_axis_off()
    ax.set_title("Minimum rest between shifts (e.g. ≥ 11 hours)", pad=12)
    # Day strips
    for d in range(2):
        ax.text(d * 24 + 12, 2.6, f"Day {d+1}",
                ha="center", fontsize=10, fontweight="bold")
        for h in [0, 6, 12, 18, 24]:
            ax.axvline(d * 24 + h, color="#555555", linewidth=0.5)
    # Top row: legal scenario — Afternoon 14–22 day 1, Morning 09–17 day 2
    ax.text(-1, 1.6, "Legal", ha="right", va="center",
            fontweight="bold", color="#7ed957")
    ax.add_patch(Rectangle((14, 1.3), 8, 0.6,
                           facecolor=SHIFTS["A"][1], edgecolor="#888888"))
    ax.text(18, 1.6, "Afternoon 14–22", ha="center", color="white",
            fontweight="bold", fontsize=9)
    ax.add_patch(Rectangle((33, 1.3), 8, 0.6,
                           facecolor=SHIFTS["M"][1], edgecolor="#888888"))
    ax.text(37, 1.6, "Morning 09–17", ha="center", color="white",
            fontweight="bold", fontsize=9)
    ax.annotate("", xy=(33, 1.05), xytext=(22, 1.05),
                arrowprops=dict(arrowstyle="<->", color="#7ed957", lw=1.6))
    ax.text(27.5, 0.55, "11 h rest ✓", ha="center",
            color="#7ed957", fontweight="bold")

    # Bottom row: illegal scenario — Afternoon 14–22 day 1, Morning 05–13 day 2
    ax.text(-1, -0.5, "Illegal", ha="right", va="center",
            fontweight="bold", color="#ff5566")
    ax.add_patch(Rectangle((14, -0.8), 8, 0.6,
                           facecolor=SHIFTS["A"][1], edgecolor="#888888"))
    ax.text(18, -0.5, "Afternoon 14–22", ha="center", color="white",
            fontweight="bold", fontsize=9)
    ax.add_patch(Rectangle((29, -0.8), 8, 0.6,
                           facecolor=SHIFTS["M"][1], edgecolor="#888888",
                           hatch="///"))
    ax.text(33, -0.5, "Morning 05–13", ha="center", color="white",
            fontweight="bold", fontsize=9)
    ax.annotate("", xy=(29, -1.1), xytext=(22, -1.1),
                arrowprops=dict(arrowstyle="<->", color="#ff5566", lw=1.6))
    ax.text(25.5, -1.5, "7 h rest ✗", ha="center", color="#ff5566",
            fontweight="bold")
    fig.savefig(OUT / "ros_06_rest.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 7) Weekend constraints
# ---------------------------------------------------------------------------
def fig_weekends():
    employees = ["Anna", "Ben", "Carla", "Dan"]
    # 4-week roster, focus on Sat/Sun columns
    weeks = 4
    days_per_row = 7 * weeks
    days = (["Mo","Tu","We","Th","Fr","Sa","Su"]) * weeks
    # Build with mostly "-" and shifts only on weekends to focus the eye
    roster = [
        list("--M--MM" + "--A--A-" + "--N--MM" + "--M--MM"),
        list("--A----" + "--A--AA" + "-----AA" + "--A----"),
        list("--N--NN" + "------N" + "--M--NN" + "------N"),
        list("-----MM" + "-----MM" + "-----MA" + "-----AM"),
    ]
    # Count weekends worked per employee
    fig, ax = plt.subplots(figsize=(12, 3.3))
    draw_roster(ax, roster, employees, days=days,
                title="Weekend workload — every Sat/Sun shift is sensitive")
    # Make room and add Week N labels well above the day-header row
    ax.set_ylim(0, len(employees) + 1.4)
    for w in range(weeks):
        ax.text(7 * w + 3.5, len(employees) + 1.05,
                f"Week {w+1}", ha="center", fontsize=10,
                fontweight="bold", color="#888888")
    shift_legend(ax)
    fig.savefig(OUT / "ros_07_weekends.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 8) Fairness — hours worked per employee
# ---------------------------------------------------------------------------
def fig_fairness():
    employees = ["Anna", "Ben", "Carla", "Dan", "Eva"]
    unfair = [168, 96, 140, 184, 80]
    fair = [136, 132, 140, 144, 132]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3),
                                   sharey=True)
    for ax, vals, title in [(ax1, unfair, "Without fairness objective"),
                            (ax2, fair, "With fairness objective")]:
        bars = ax.bar(employees, vals,
                      color=["#4C78A8", "#F58518", "#54A24B",
                             "#E45756", "#72B7B2"],
                      edgecolor="#888888", linewidth=0.6)
        ax.axhline(np.mean(vals), color="black",
                   linestyle="--", linewidth=1, label="avg")
        ax.set_title(title)
        ax.set_ylabel("Hours over 4 weeks")
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 3, str(v),
                    ha="center", fontsize=9)
        ax.set_ylim(0, 210)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        ax.set_axisbelow(True)
    fig.suptitle("Fairness — same total work, very different distributions",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "ros_08_fairness.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 9) Contracts — min/max hours, days off
# ---------------------------------------------------------------------------
def fig_contracts():
    contracts = [
        ("Full-time perm.", "Anna",  150, 160, 168, 10),
        ("Part-time 60%",   "Ben",    80,  96, 100, 8),
        ("Mini-job",        "Carla",  30,  40,  45, 8),
        ("Senior on-call",  "Dan",    60, 120, 180, 12),
        ("Temp / student",  "Eva",    20,  60, 100, 6),
    ]
    fig, ax = plt.subplots(figsize=(15, 3.2))
    for i, (kind, name, mn, planned, mx, rest) in enumerate(contracts):
        y = len(contracts) - 1 - i
        # Range bar
        ax.barh(y, mx - mn, left=mn, height=0.45,
                color="#3a3a3a", edgecolor="#888", linewidth=0.6)
        # Planned hours marker
        ax.plot(planned, y, marker="o", markersize=11,
                color="#4C78A8", markeredgecolor="#888888")
        ax.text(planned, y + 0.35, f"{planned}h", ha="center",
                fontsize=9, color="#4C78A8", fontweight="bold")
        ax.text(mn - 2, y, f"{mn}", ha="right", va="center",
                fontsize=8, color="#888888")
        ax.text(mx + 2, y, f"{mx}", ha="left", va="center",
                fontsize=8, color="#888888")
        # Labels
        ax.text(-30, y + 0.1, name, ha="right", va="center", fontweight="bold")
        ax.text(-30, y - 0.18, kind, ha="right", va="center",
                fontsize=8, color="#888888", style="italic")
        # Rest days
        ax.text(195, y, f"≥{rest} rest days / 4w", va="center",
                fontsize=9, color="#bbbbbb")
    ax.set_xlim(-32, 240)
    ax.set_ylim(-0.7, len(contracts) - 0.3)
    ax.set_xlabel("Monthly hours")
    ax.set_yticks([])
    ax.set_title("Contracts — each employee has a personal hour range and rest quota")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)
    fig.savefig(OUT / "ros_09_contracts.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 10) Preferences — soft requests, satisfied or not
# ---------------------------------------------------------------------------
def fig_preferences():
    employees = ["Anna", "Ben", "Carla", "Dan"]
    roster = [
        list("MM--AANN--MMM-"),
        list("AAMM--N--MMAAN"),
        list("--NN--MMAA--NN"),
        list("MMAA--NNMM--AA"),
    ]
    # Anna requested off on day 2/3 (granted), prefers Mornings (granted)
    # Ben requested off day 4 (not granted -> N), prefers no nights (violated)
    highlight = [
        (0, 2, "#54A24B"), (0, 3, "#54A24B"),  # granted
        (1, 6, "#B0413E"),                       # violated
        (1, 7, "#B0413E"),
        (2, 11, "#54A24B"),                      # granted
    ]
    annotate = [
        (0, 2, "✓", "#54A24B"),
        (0, 3, "✓", "#54A24B"),
        (1, 6, "✗", "#B0413E"),
        (1, 7, "✗", "#B0413E"),
    ]
    fig, ax = plt.subplots(figsize=(15, 3.2))
    # Need to draw annotate with offset; reuse draw_roster but overlay
    draw_roster(ax, roster, employees,
                title="Preferences — green = granted, red = violated",
                highlight=highlight, equal_aspect=False)
    # Add tick marks above existing shift letters
    n_emp = len(employees)
    for (r, c, sym, col) in annotate:
        ax.text(c + 0.85, n_emp - 1 - r + 0.85, sym,
                ha="center", va="center", fontsize=11,
                color=col, fontweight="bold")
    shift_legend(ax)
    fig.savefig(OUT / "ros_10_preferences.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 11) Shift patterns / rotations
# ---------------------------------------------------------------------------
def fig_rotations():
    employees = ["Team A", "Team B", "Team C"]
    # 3-week rotation: MMMMM, AAAAA, NNNNN
    roster = [
        list("MMMMM--AAAAA--"),
        list("AAAAA--NNNNN--"),
        list("NNNNN--MMMMM--"),
    ]
    fig, ax = plt.subplots(figsize=(14, 2.7))
    draw_roster(ax, roster, employees,
                title="A rotating shift pattern — predictable weekly cycle",
                equal_aspect=False)
    shift_legend(ax)
    fig.savefig(OUT / "ros_11_rotations.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 12) Pairing / location
# ---------------------------------------------------------------------------
def fig_pairing():
    employees = ["Mentor (Anna)", "Trainee (Tim)", "Solo (Ben)", "Solo (Eva)"]
    roster = [
        list("MM--AA-NN-MM--"),
        list("MM--AA-NN-MM--"),
        list("--NN-MMAA--NN-"),
        list("AA--MMA--NN--A"),
    ]
    # Highlight the paired cells
    highlight = []
    for c, code in enumerate(roster[0]):
        if code != "-":
            highlight.append((0, c, "#4C78A8"))
            highlight.append((1, c, "#4C78A8"))
    fig, ax = plt.subplots(figsize=(15, 3.0))
    draw_roster(ax, roster, employees,
                title="Pairing constraint — mentor and trainee always on the same shift",
                highlight=highlight, equal_aspect=False)
    shift_legend(ax)
    fig.savefig(OUT / "ros_12_pairing.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 13) Soft constraint weights — objective trade-offs
# ---------------------------------------------------------------------------
def fig_objective_weights():
    cats = ["Coverage\nshortfall", "Rest\nviolations", "Preference\nmismatches",
            "Fairness\ngap", "Weekend\nimbalance", "Overtime\nhours"]
    hard = [1, 1, 0, 0, 0, 0]
    soft_weights = [0, 0, 5, 3, 2, 10]
    fig, ax = plt.subplots(figsize=(10, 3))
    x = np.arange(len(cats))
    ax.bar(x - 0.2, [h * 1000 for h in hard], width=0.4,
           color="#B0413E", label="Hard (∞ penalty)", edgecolor="#888888")
    ax.bar(x + 0.2, soft_weights, width=0.4,
           color="#4C78A8", label="Soft (weighted)", edgecolor="#888888")
    ax.set_yscale("symlog")
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=9)
    ax.set_ylabel("Penalty weight (log)")
    ax.set_title("Multi-criteria objective — hard rules trump soft weighted preferences")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.set_axisbelow(True)
    fig.savefig(OUT / "ros_13_objective_weights.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 14) The decision matrix — what we are actually solving
# ---------------------------------------------------------------------------
def fig_problem_overview():
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_axis_off()
    ax.set_xlim(0, 10); ax.set_ylim(0, 6)

    def box(x, y, w, h, text, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.08",
                                    facecolor=color, edgecolor="#888888"))
        ax.text(x + w / 2, y + h / 2, text,
                ha="center", va="center", fontsize=10, fontweight="bold",
                color="white")

    box(0.5, 3.6, 2.6, 1.6,
        "Demand\n(shift slots\nto fill)", "#4C78A8")
    box(0.5, 1.0, 2.6, 1.8,
        "Employees\n(skills, contract,\navailability,\npreferences)",
        "#54A24B")

    ax.annotate("", xy=(4.4, 3.0), xytext=(3.1, 4.4),
                arrowprops=dict(arrowstyle="->", color="#222222", lw=1.5))
    ax.annotate("", xy=(4.4, 3.0), xytext=(3.1, 1.9),
                arrowprops=dict(arrowstyle="->", color="#222222", lw=1.5))

    box(4.4, 2.2, 2.5, 1.6,
        "Assignment\n(who works\nwhich shift)", "#F58518")

    ax.annotate("", xy=(7.6, 3.0), xytext=(6.9, 3.0),
                arrowprops=dict(arrowstyle="->", color="#222222", lw=1.5))

    box(7.6, 2.2, 2.0, 1.6,
        "Score:\nhard +\nsoft penalties", "#B0413E")

    ax.text(5.0, 0.5,
            "Objective: minimize soft penalties subject to all hard rules",
            ha="center", style="italic", fontsize=10, color="#bbbbbb")
    ax.text(5.0, 5.7, "The rostering decision",
            ha="center", fontsize=12, fontweight="bold")
    fig.savefig(OUT / "ros_00_overview.png")
    plt.close(fig)


def main():
    for f in [
        fig_problem_overview,
        fig_basic_roster,
        fig_coverage,
        fig_skills,
        fig_availability,
        fig_hard_soft,
        fig_rest,
        fig_weekends,
        fig_fairness,
        fig_contracts,
        fig_preferences,
        fig_rotations,
        fig_pairing,
        fig_objective_weights,
    ]:
        f()
        print(f"  ✓ {f.__name__}")


if __name__ == "__main__":
    main()
