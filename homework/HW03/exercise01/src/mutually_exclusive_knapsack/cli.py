from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

from .baseline import HighsSolver
from .branch_and_bound import BranchAndBoundSolver
from .instance_generation import generate_uniform_instance
from .models import KnapsackInstance


def _write_json_output(payload: dict[str, Any], output_path: Path | None) -> None:
    serialized = json.dumps(payload, indent=2, sort_keys=True)
    if output_path is None:
        sys.stdout.write(serialized)
        sys.stdout.write("\n")
        return
    output_path.write_text(serialized + "\n", encoding="utf-8")


def _build_generate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mek-generate-instance",
        description="Generate a random mutually exclusive knapsack instance as JSON.",
    )
    parser.add_argument("output", type=Path, help="Path of the JSON instance file to write.")
    parser.add_argument("--num-items", type=int, required=True)
    parser.add_argument("--capacity", type=float, required=True)
    parser.add_argument("--min-weight", type=float, required=True)
    parser.add_argument("--max-weight", type=float, required=True)
    parser.add_argument("--min-efficiency", type=float, required=True)
    parser.add_argument("--max-efficiency", type=float, required=True)
    parser.add_argument("--mutual-exclusivity-p", type=float, required=True)
    return parser


def _build_solve_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mek-solve",
        description="Solve a mutually exclusive knapsack instance from JSON.",
    )
    parser.add_argument("instance", type=Path, help="Path of the JSON instance file to solve.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the JSON solve result. Defaults to stdout.",
    )
    return parser


def _build_baseline_solve_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mek-baseline-solve",
        description="Solve a mutually exclusive knapsack instance"
        " from JSON with the HiGHS baseline solver.",
    )
    parser.add_argument("instance", type=Path, help="Path of the JSON instance file to solve.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the JSON solve result. Defaults to stdout.",
    )
    return parser


def generate_instance_main(argv: Sequence[str] | None = None) -> int:
    parser = _build_generate_parser()
    args = parser.parse_args(argv)

    instance = generate_uniform_instance(
        num_items=args.num_items,
        capacity=args.capacity,
        min_weight=args.min_weight,
        max_weight=args.max_weight,
        min_efficiency=args.min_efficiency,
        max_efficiency=args.max_efficiency,
        mutual_exclusivity_p=args.mutual_exclusivity_p,
    )
    args.output.write_text(instance.model_dump_json(indent=2), encoding="utf-8")
    return 0


def solve_instance_main(argv: Sequence[str] | None = None) -> int:
    parser = _build_solve_parser()
    args = parser.parse_args(argv)

    instance = KnapsackInstance.model_validate_json(args.instance.read_text(encoding="utf-8"))
    solver = BranchAndBoundSolver(instance)

    start_time = perf_counter()
    solution = solver.solve()
    elapsed = perf_counter() - start_time

    payload = {
        "solution": solution.model_dump(mode="json"),
        "statistics": {
            "solve_time_seconds": elapsed,
            "lp_time_seconds": solver.total_lp_time,
            "node_count": solver.node_count,
            **solver.statistics,
        },
    }
    _write_json_output(payload, args.output)
    return 0


def baseline_solve_instance_main(argv: Sequence[str] | None = None) -> int:
    parser = _build_baseline_solve_parser()
    args = parser.parse_args(argv)

    instance = KnapsackInstance.model_validate_json(args.instance.read_text(encoding="utf-8"))
    solver = HighsSolver(instance)

    start_time = perf_counter()
    solution = solver.solve()
    elapsed = perf_counter() - start_time

    payload = {
        "solution": solution.model_dump(mode="json"),
        "statistics": {
            "solve_time_seconds": elapsed,
            "highs_solve_time_seconds": solver.total_solve_time,
        },
    }
    _write_json_output(payload, args.output)
    return 0
