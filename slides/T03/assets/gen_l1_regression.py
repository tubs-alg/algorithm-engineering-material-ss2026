"""Generate the L1 linear regression figure for the LP-preserving section.

Produces `l1_regression.png` — scatter of data points with two outliers, the
L1-fit line, and vertical orange segments showing the absolute residuals being
summed in the LP objective.

Why this exists. The L1-regression slide claims that statisticians' L1
linear regression is *just an LP*. The plot has to make that visceral by
showing exactly what the LP is minimizing: the sum of vertical-segment
lengths, with outliers contributing linearly rather than quadratically.

Palette matches gen_pwla.py so the eye recognises the same axis style
across the deck.

Usage. `python assets/gen_l1_regression.py` from the slides/ directory.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy.optimize import linprog

OUT = Path(__file__).parent

BG = "none"
FG = "#e0e0e0"
POINT = "#9ad0f5"        # data (light blue, matches CURVE in gen_pwla)
LINE = "#7fbf7b"         # L1 fit (green)
RESID = "#e69138"        # residual segments (orange)
GRID = "#37474f"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.transparent": True,
    "text.color": FG,
    "axes.labelcolor": FG,
    "axes.titlecolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "font.size": 14,
})


def make_data(seed=7, n=12):
    rng = np.random.default_rng(seed)
    xi = np.linspace(0.5, 9.5, n)
    eta = 0.7 * xi + 1.0 + rng.normal(0, 0.35, size=n)
    eta[3] += 3.2   # outlier above
    eta[8] -= 2.8   # outlier below
    return xi, eta


def l1_fit(xi, eta):
    """Solve  min sum d_i  s.t.  d_i >= +/- (eta_i - alpha xi_i - beta)."""
    n = len(xi)
    n_vars = 2 + n  # alpha, beta, d_1..d_n
    c = np.zeros(n_vars)
    c[2:] = 1.0
    A_ub = []
    b_ub = []
    for i in range(n):
        # d_i >= eta_i - alpha xi_i - beta  =>  -alpha xi_i - beta - d_i <= -eta_i
        row = np.zeros(n_vars)
        row[0] = -xi[i]; row[1] = -1.0; row[2 + i] = -1.0
        A_ub.append(row); b_ub.append(-eta[i])
        # d_i >= alpha xi_i + beta - eta_i  =>   alpha xi_i + beta - d_i <=  eta_i
        row = np.zeros(n_vars)
        row[0] = xi[i];  row[1] = 1.0;  row[2 + i] = -1.0
        A_ub.append(row); b_ub.append(eta[i])
    bounds = [(None, None), (None, None)] + [(0, None)] * n
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    assert res.success, res.message
    return float(res.x[0]), float(res.x[1])


def main():
    xi, eta = make_data()
    alpha, beta = l1_fit(xi, eta)
    eta_pred = alpha * xi + beta

    fig, ax = plt.subplots(figsize=(6.5, 5.0))
    # Residual segments (drawn first, behind points and line)
    for xv, ev, epv in zip(xi, eta, eta_pred):
        ax.plot([xv, xv], [ev, epv], color=RESID, linewidth=2.0, alpha=0.9,
                solid_capstyle="round")
    # L1 fit line
    xl = np.array([xi.min() - 0.3, xi.max() + 0.3])
    ax.plot(xl, alpha * xl + beta, color=LINE, linewidth=2.6,
            label=fr"$\eta \approx {alpha:.2f}\,\xi + {beta:.2f}$")
    # Data points (on top)
    ax.scatter(xi, eta, color=POINT, s=70, zorder=5,
               edgecolor=FG, linewidth=0.8, label=r"data $(\xi_i, \eta_i)$")
    # Residual legend marker
    ax.plot([], [], color=RESID, linewidth=2.4,
            label=r"$|\eta_i - (\alpha\,\xi_i + \beta)|$")

    ax.set_xlabel(r"$\xi$")
    ax.set_ylabel(r"$\eta$")
    ax.grid(True, color=GRID, alpha=0.4, linewidth=0.7)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(FG)
    ax.legend(loc="upper left", frameon=False, fontsize=12)

    fig.tight_layout()
    out = OUT / "l1_regression.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", transparent=True)
    print(f"wrote {out}  (alpha={alpha:.3f}, beta={beta:.3f})")


if __name__ == "__main__":
    main()
