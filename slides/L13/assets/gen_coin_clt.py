"""coin_clt: is a 60%-heads result suspicious? A concrete CLT / risk example.

For `_06-robust.qmd`, placed between the central-limit-theorem statement and the
CLT-based uncertainty set. The de Moivre-Laplace coin example: the fraction of
heads over n fair flips has mean 0.5 and spread 0.5/sqrt(n). Two panels:

  left  -- the exact distribution of the head fraction for n = 5, 20, 100,
           narrowing from a coarse spread into a sharp bell at 0.5;
  right -- the exact risk P(fraction >= 0.6) against n: about one half at n = 5
           (unremarkable) down to a ~2-sigma tail near 3% at n = 100 (suspicious).

All distributions are exact binomial pmfs, so the risk numbers are correct rather
than a normal-tail approximation. Run: python gen_coin_clt.py
"""

import math
import os

import numpy as np

import _theme as T
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

P = 0.5                      # fair coin
SIGMA = 0.5                  # per-flip standard deviation
THRESH = 0.6                 # "60% heads or more"


def binom_pmf(n: int) -> np.ndarray:
    """Exact pmf of the head count for n fair flips, indexed by k = 0..n.

    dtype=float is essential: math.comb overflows int64 for large n, which would
    otherwise make numpy build an object array that matplotlib cannot plot.
    """
    return np.array([math.comb(n, k) for k in range(n + 1)], dtype=float) / 2.0 ** n


def tail_ge(n: int, frac: float) -> float:
    """Exact P(fraction of heads >= frac) for n fair flips."""
    pmf = binom_pmf(n)
    ks = np.arange(n + 1)
    return float(pmf[ks / n >= frac - 1e-12].sum())


def main() -> None:
    T.init_style()
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.4, 4.3))

    # -- Left: the head fraction concentrates on 0.5 -----------------------
    panels = [(5, T.FADED, "n = 5"), (20, T.BLUE, "n = 20"), (100, T.ORANGE, "n = 100")]
    for n, color, label in panels:
        pmf = binom_pmf(n)
        frac = np.arange(n + 1) / n
        dens = pmf * n                             # step is 1/n -> density
        axL.fill_between(frac, dens, step="mid", color=color, alpha=0.18)
        axL.plot(frac, dens, drawstyle="steps-mid", lw=2.2, color=color, label=label)

    axL.axvline(THRESH, ls="--", lw=1.6, color=T.RED)
    axL.text(THRESH + 0.008, axL.get_ylim()[1] * 0.92, "60% heads", color=T.RED,
             fontsize=11.5, ha="left", va="top")
    axL.axvline(P, ls=":", lw=1.2, color=T.MUTED)
    axL.text(P - 0.008, axL.get_ylim()[1] * 0.55, "fair: 0.5", color=T.MUTED,
             fontsize=11.5, ha="right", va="center")
    axL.set_xlim(0.1, 0.9)
    axL.set_ylim(bottom=0)
    axL.set_xlabel("fraction of heads in $n$ flips")
    axL.set_ylabel("density")
    axL.set_title("the fraction concentrates on 0.5", fontsize=14)
    axL.legend(loc="upper left", fontsize=11)

    # -- Right: a mild 60% deviation vs the all-win box corner -------------
    # Sample the exact tail at representative n: the raw P(frac >= 0.6) curve
    # sawtooths because ceil(0.6 n) jumps with parity; sampling draws the clean
    # trend while the annotated points below stay exact.
    sample_ns = np.array([5, 10, 20, 30, 50, 70, 100])
    risk = np.array([tail_ge(n, THRESH) for n in sample_ns])
    ns = np.arange(1, 101)
    all_win = 0.5 ** ns                            # every throw won = box corner
    axR.plot(sample_ns, risk, "-o", lw=2.4, color=T.ORANGE, label=r"$\geq 60\%$ heads")
    axR.plot(ns, all_win, ls="--", lw=2.4, color=T.RED,
             label=r"every throw won ($2^{-n}$)")
    for n, note, xt, yt in [(5, "realistic", 26, 0.40), (100, "suspicious", 74, 0.15)]:
        r = tail_ge(n, THRESH)
        axR.annotate(f"{note}\n$\\approx${r*100:.0f}%", xy=(n, r), xytext=(xt, yt),
                     color=T.FG, fontsize=11.5, ha="center",
                     arrowprops=dict(arrowstyle="->", color=T.MUTED))
    axR.set_ylim(0, 0.55)
    axR.set_xlim(0, 100)
    axR.set_xlabel("number of flips $n$")
    axR.set_ylabel("probability")
    axR.set_title("mild deviation vs the all-win corner", fontsize=14)
    axR.legend(loc="upper right", fontsize=10.5)

    T.save(fig, os.path.join(OUT, "coin_clt"), pad=0.1)

    # Print exact figures for the slide text.
    print(f"z(60pct) = 0.2 * sqrt(n);  sigma per flip = {SIGMA:.2f}")
    for n in (5, 10, 20, 50, 100):
        z = (THRESH - P) / (SIGMA / np.sqrt(n))
        print(f"  n={n:4d}: P(frac>=0.6)={tail_ge(n, THRESH):.4g}  z={z:.2f}sigma"
              f"  P(all heads)=2^-n={0.5 ** n:.3g}")


if __name__ == "__main__":
    main()
