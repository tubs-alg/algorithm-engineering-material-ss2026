"""Measure CP-SAT runtime variance across random seeds on ONE fixed instance.

What this contains
  A self-contained benchmark: build a single hard-but-solvable number-partitioning
  instance (split n large integers into two sets minimizing the larger sum --
  the makespan / P||Cmax problem on two machines), then solve that *same* model
  20 times, changing only the solver's random seed. Every run is recorded with
  its wall-clock time, status, and proven objective. Results -> seed_variance.json.

Why it exists
  Feeds the "high variance" slide. The instance sits near the partitioning phase
  transition, where a single search path is extremely seed-sensitive. With one
  worker (so the portfolio cannot hedge the variance away), the same model, same
  machine, and same parameters produce wildly different runtimes -- a ~200x spread
  -- while every run still proves the identical optimum. One run is not a measurement.

How to use
  python run_seed_variance.py            # 20 seeds, 1 worker (the slide's data)
  python run_seed_variance.py --workers 8 --seeds 20   # contrast: portfolio hedges
  -> writes seed_variance.json next to this script.

When it should change
  Retune N_ITEMS / SIZE_BITS / INSTANCE_SEED only if the example instance must
  change. Keep num_workers=1 as the default: the multi-worker portfolio damps the
  variance (~1.2x here), which would hide the very effect the slide is about.
"""

import argparse
import json
import random
import statistics
from pathlib import Path

from ortools.sat.python import cp_model

# Fixed instance. n large integers, two bins, minimize the larger bin sum.
# n=27 with ~27-bit magnitudes sits at the partitioning phase transition: hard
# to prove optimal, and the single-worker search time depends heavily on the seed.
N_ITEMS = 27
SIZE_BITS = 27
INSTANCE_SEED = 42
N_BINS = 2

SEEDS = range(20)
TIME_LIMIT_S = 60.0


def make_instance() -> list[int]:
    rng = random.Random(INSTANCE_SEED)
    return [rng.randint(1, 2 ** SIZE_BITS) for _ in range(N_ITEMS)]


def build_model(sizes: list[int]) -> cp_model.CpModel:
    """Two-machine makespan: assign each item to a bin, minimize the larger sum."""
    model = cp_model.CpModel()
    n, total = len(sizes), sum(sizes)
    x = {(j, i): model.NewBoolVar(f"x_{j}_{i}")
         for j in range(n) for i in range(N_BINS)}
    for j in range(n):
        model.AddExactlyOne(x[j, i] for i in range(N_BINS))
    loads = []
    for i in range(N_BINS):
        load = model.NewIntVar(0, total, f"load_{i}")
        model.Add(load == sum(sizes[j] * x[j, i] for j in range(n)))
        loads.append(load)
    makespan = model.NewIntVar(0, total, "makespan")
    model.AddMaxEquality(makespan, loads)
    model.Minimize(makespan)
    return model


def run(num_workers: int, seeds) -> dict:
    sizes = make_instance()
    rows = []
    for seed in seeds:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = TIME_LIMIT_S
        solver.parameters.random_seed = seed
        solver.parameters.num_workers = num_workers
        status = solver.Solve(build_model(sizes))
        rows.append({
            "seed": seed,
            "status": solver.status_name(status),
            "wall_time": round(solver.wall_time, 3),
            "objective": int(solver.objective_value),
        })
        print(f"seed={seed:2d} {rows[-1]['status']:8s} "
              f"t={rows[-1]['wall_time']:7.3f}s  obj={rows[-1]['objective']}",
              flush=True)

    times = [r["wall_time"] for r in rows]
    objectives = {r["objective"] for r in rows if r["status"] == "OPTIMAL"}
    return {
        "instance": {"n_items": N_ITEMS, "size_bits": SIZE_BITS,
                     "instance_seed": INSTANCE_SEED, "n_bins": N_BINS},
        "num_workers": num_workers,
        "time_limit_s": TIME_LIMIT_S,
        "n_runs": len(rows),
        "all_optimal": all(r["status"] == "OPTIMAL" for r in rows),
        "unique_optima": sorted(objectives),
        "min": round(min(times), 3),
        "max": round(max(times), 3),
        "ratio_max_min": round(max(times) / min(times), 1),
        "mean": round(statistics.mean(times), 3),
        "median": round(statistics.median(times), 3),
        "pstdev": round(statistics.pstdev(times), 3),
        "runs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seeds", type=int, default=20)
    args = parser.parse_args()

    summary = run(args.workers, range(args.seeds))
    out = Path(__file__).with_name("seed_variance.json")
    out.write_text(json.dumps(summary, indent=2))
    print(f"\nworkers={summary['num_workers']}  all_optimal={summary['all_optimal']}  "
          f"unique_optima={summary['unique_optima']}")
    print(f"min={summary['min']}s  max={summary['max']}s  "
          f"ratio={summary['ratio_max_min']}x  median={summary['median']}s  "
          f"mean={summary['mean']}s  stdev={summary['pstdev']}s")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
