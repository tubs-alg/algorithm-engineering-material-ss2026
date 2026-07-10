"""saa_convergence: sample average approximation of the newsvendor loss.

For `_07-stochastic.qmd`. Expected newsvendor loss (Cu=6, Co=3, D ~
Normal(100, 20^2)) estimated with N=20 and N=200 samples against a large-sample
proxy of the true curve: small samples give a jagged objective and a shifted
minimizer. Run: python gen_saa.py
"""

import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

CU, CO = 6.0, 3.0
MU, SIGMA = 100.0, 20.0


def nv_loss(q, d):
    return CU * np.maximum(d - q, 0) + CO * np.maximum(q - d, 0)


def main() -> None:
    T.init_style()
    rng = np.random.default_rng(7)
    q_grid = np.linspace(50, 160, 250)

    d_true = rng.normal(MU, SIGMA, size=200_000)
    true_loss = np.array([nv_loss(q, d_true).mean() for q in q_grid])

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.plot(q_grid, true_loss, lw=3, color=T.GOLD, label="true expectation (proxy)")
    for n, color in [(20, T.RED), (200, T.BLUE)]:
        d = rng.normal(MU, SIGMA, size=n)
        loss = np.array([nv_loss(q, d).mean() for q in q_grid])
        ax.plot(q_grid, loss, lw=2, alpha=0.9, color=color, label=f"SAA with N = {n}")
        qmin = q_grid[np.argmin(loss)]
        ax.axvline(qmin, ls=":", lw=1.5, color=color, alpha=0.7)
    ax.axvline(q_grid[np.argmin(true_loss)], ls=":", lw=1.8, color=T.GOLD,
               alpha=0.8)
    ax.set_xlabel("order quantity $q$")
    ax.set_ylabel("estimated expected loss")
    ax.legend(loc="upper right", fontsize=11)
    T.save(fig, os.path.join(OUT, "saa_convergence"))


if __name__ == "__main__":
    main()
