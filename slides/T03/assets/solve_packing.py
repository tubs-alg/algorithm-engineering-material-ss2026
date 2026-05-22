"""Solve a 20-square min-bounding-box packing MIP with ortools/HiGHS.

Defines a fixed instance of 20 axis-aligned squares with varied sizes
and solves the standard Big-M packing model — minimize the container
side B subject to containment plus four-direction disjunctive
non-overlap constraints with one binary per branch.

Saves the resulting B* and per-square centers to `packing_solution.json`
for `gen_packing_lp_relax.py` to consume. The solver runs with a
time limit; the resulting solution may be sub-optimal but is good
enough to make the LP-vs-MIP gap visible on a slide.

Why this exists. The figure generator should not have a heavy solver
dependency at draw time; we solve once, cache the result, and let the
plotting script stay matplotlib-only. Re-run this script when the
instance changes.

Usage. `python assets/solve_packing.py` from the slides/ directory.
"""

import json
import time
from datetime import timedelta
from pathlib import Path

from ortools.math_opt.python import mathopt

OUT = Path(__file__).parent

# Fixed instance: 20 squares with varied full-side lengths.
SIDES = [2.0, 1.7, 1.5, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.8,
         0.7, 0.6, 0.6, 0.5, 0.5, 0.5, 0.4, 0.4, 0.4, 0.3]
TIME_LIMIT_S = 180


def main():
    s_list = [side / 2 for side in SIDES]
    n = len(s_list)
    U_B = sum(SIDES)             # trivial diagonal upper bound on B
    M = U_B                      # Big-M valid for every separation constraint

    model = mathopt.Model(name="packing")
    B = model.add_variable(lb=0, ub=U_B, name="B")
    x = [model.add_variable(lb=0, ub=U_B, name=f"x_{i}") for i in range(n)]
    y = [model.add_variable(lb=0, ub=U_B, name=f"y_{i}") for i in range(n)]
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    bL = {p: model.add_binary_variable(name=f"bL_{p}") for p in pairs}
    bR = {p: model.add_binary_variable(name=f"bR_{p}") for p in pairs}
    bA = {p: model.add_binary_variable(name=f"bA_{p}") for p in pairs}
    bBt = {p: model.add_binary_variable(name=f"bB_{p}") for p in pairs}

    for i in range(n):
        model.add_linear_constraint(x[i] >= s_list[i])
        model.add_linear_constraint(y[i] >= s_list[i])
        model.add_linear_constraint(x[i] + s_list[i] <= B)
        model.add_linear_constraint(y[i] + s_list[i] <= B)

    for (i, j) in pairs:
        sij = s_list[i] + s_list[j]
        model.add_linear_constraint(x[i] - x[j] >= sij - M * (1 - bL[i, j]))
        model.add_linear_constraint(x[j] - x[i] >= sij - M * (1 - bR[i, j]))
        model.add_linear_constraint(y[j] - y[i] >= sij - M * (1 - bA[i, j]))
        model.add_linear_constraint(y[i] - y[j] >= sij - M * (1 - bBt[i, j]))
        model.add_linear_constraint(bL[i, j] + bR[i, j] + bA[i, j] + bBt[i, j] == 1)

    model.minimize(B)

    params = mathopt.SolveParameters(time_limit=timedelta(seconds=TIME_LIMIT_S))
    t0 = time.time()
    result = mathopt.solve(model, mathopt.SolverType.HIGHS, params=params)
    elapsed = time.time() - t0

    B_star = result.objective_value()
    centers = [(result.variable_values()[x[i]],
                result.variable_values()[y[i]]) for i in range(n)]

    data = {
        "sides": SIDES,
        "B_star": B_star,
        "centers": centers,
        "termination": str(result.termination.reason),
        "solve_seconds": elapsed,
        "time_limit_s": TIME_LIMIT_S,
    }
    out = OUT / "packing_solution.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"solved in {elapsed:.1f}s — B* = {B_star:.4f} "
          f"({result.termination.reason}); wrote {out}")


if __name__ == "__main__":
    main()
