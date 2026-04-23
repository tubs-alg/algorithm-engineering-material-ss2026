"""
Progressive test suite for the TSP heuristic.

Tests instances in order of increasing size. Stops as soon as one
instance fails — if the smallest instance times out, the larger ones
won't even be attempted.

Run with:  python -m pytest tests/test_tsp.py -v -s
"""

import gzip
import math
import time
from pathlib import Path

import pytest

INSTANCE_DIR = Path(__file__).parent.parent / "instances"
TIME_LIMIT = 10.0  # seconds

# Instances ordered by difficulty. Baseline tour lengths are provided as
# thresholds — your implementation must produce a tour no longer than
# the baseline to earn the points for that instance.
INSTANCES = [
    {
        "name": "sw24978",
        "file": "sw24978.tsp.gz",
        "n": 24978,
        "baseline": 1_074_991,
        "points_awarded": 2,
        "best_known": 855_597,
        "optimal": True,
    },
    {
        "name": "ch71009",
        "file": "ch71009.tsp.gz",
        "n": 71009,
        "baseline": 5_636_267,
        "points_awarded": 2,
        "best_known": 4_566_563,
        "optimal": False,
    },
    {
        "name": "mona-lisa100K",
        "file": "mona-lisa100K.tsp.gz",
        "n": 100000,
        "baseline": 6_886_143,
        "points_awarded": 4,
        "best_known": 5_757_191,
        "optimal": False,
    },
    {
        "name": "lra498378",
        "file": "lra498378.tsp.gz",
        "n": 498378,
        "baseline": 2_700_652,
        "points_awarded": 12,
        "best_known": 2_168_039,
        "optimal": False,
    },
]


def load_tsplib(filepath):
    """Parse a TSPLIB .tsp or .tsp.gz file with NODE_COORD_SECTION (EUC_2D)."""
    filepath = Path(filepath)
    opener = gzip.open if filepath.suffix == ".gz" else open
    points = []
    in_coords = False
    with opener(filepath, "rt") as f:
        for line in f:
            line = line.strip()
            if line == "NODE_COORD_SECTION":
                in_coords = True
                continue
            if line in ("EOF", ""):
                if in_coords:
                    break
                continue
            if in_coords:
                parts = line.split()
                points.append((float(parts[1]), float(parts[2])))
    return points


def tour_length(points, tour):
    n = len(tour)
    total = 0.0
    for k in range(n):
        ax, ay = points[tour[k]]
        bx, by = points[tour[(k + 1) % n]]
        total += math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
    return total


def is_valid_tour(points, tour):
    return sorted(tour) == list(range(len(points)))


def _check_instance(info):
    """Run and verify a single instance."""
    from tsp_heuristic import cpp_tsp

    filepath = INSTANCE_DIR / info["file"]
    if not filepath.exists():
        pytest.skip(f"Instance file not found: {filepath}")

    points = load_tsplib(filepath)
    assert len(points) == info["n"], f"Expected {info['n']} points, got {len(points)}"

    t0 = time.perf_counter()
    tour = cpp_tsp(points)
    elapsed = time.perf_counter() - t0

    assert is_valid_tour(points, tour), "Tour is not a valid permutation of 0..n-1."

    length = tour_length(points, tour)
    opt_label = "optimal" if info["optimal"] else "best known"
    gap = (length / info["best_known"] - 1) * 100

    print(f"\n  {info['name']}: tour = {length:,.0f}  ({elapsed:.2f}s)  "
          f"gap to {opt_label}: {gap:+.1f}%")

    assert elapsed <= TIME_LIMIT, (
        f"Time limit exceeded: {elapsed:.2f}s > {TIME_LIMIT}s"
    )
    assert length <= info["baseline"], (
        f"Tour too long: {length:,.0f} > baseline {info['baseline']:,}"
    )

    # Congratulate if they closed at least 20% of the gap between baseline
    # and best known — that takes real effort beyond a basic solution.
    gap_total = info["baseline"] - info["best_known"]
    gap_closed = info["baseline"] - length
    if gap_total > 0 and gap_closed >= 0.20 * gap_total:
        pct_closed = gap_closed / gap_total * 100
        if pct_closed >= 80:
            msg = f"Wow -- {pct_closed:.0f}% of the gap closed. Are you sure you're not Concorde?"
        elif pct_closed >= 50:
            msg = f"{pct_closed:.0f}% of the gap closed -- impressive work!"
        else:
            msg = f"{pct_closed:.0f}% of the gap closed -- nice, you're going beyond the basics!"
        print(f"\n  >>> {msg} <<<")


# ── Single progressive test ─────────────────────────────────────────────
#
# One test function that runs all instances in order and stops at the
# first failure. This guarantees that a timeout on a small instance
# won't cause the larger ones to run, regardless of how pytest is
# invoked (no -x flag needed, no parallelization issues).

def test_tsp_progressive():
    """Run all instances in order of increasing size."""
    for info in INSTANCES:
        _check_instance(info)
