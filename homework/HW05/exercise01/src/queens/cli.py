import argparse
from collections.abc import Sequence

from queens.model_cpsat import NQueensCPSAT
from queens.model_sat import solve_with_sat


def _positive_int(value: str) -> int:
    try:
        n = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("n must be an integer") from exc
    if n < 1:
        raise argparse.ArgumentTypeError("n must be a positive integer")
    return n


def _positive_float(value: str) -> float:
    try:
        time_limit = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("time limit must be a number") from exc
    if time_limit <= 0:
        raise argparse.ArgumentTypeError("time limit must be positive")
    return time_limit


def _build_parser(program_name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=program_name)
    parser.add_argument("n", type=_positive_int, help="size of the n x n board")
    parser.add_argument(
        "--time-limit",
        type=_positive_float,
        default=None,
        help="optional solver time limit in seconds",
    )
    return parser


def _print_result(
    n: int, result: list[list[bool]] | bool | None, build_time: float, solve_time: float
):
    if isinstance(result, list):
        status = f"solution found for n={n}"
    elif result is False:
        status = f"n={n} is unsatisfiable"
    else:
        status = f"timeout occurred for n={n}"
    print(f"Status: {status}")
    print(f"Model build time: {build_time:.6f}s")
    print(f"Solve time: {solve_time:.6f}s")


def sat_main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser("queens-sat").parse_args(argv)
    times: dict[str, float] = {}
    result = solve_with_sat(args.n, time_limit=args.time_limit, times=times)
    _print_result(args.n, result, times["build_time"], times["solve_time"])
    return 0


def cpsat_main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser("queens-cpsat").parse_args(argv)
    model = NQueensCPSAT(args.n)
    result = model.solve(time_limit=args.time_limit)
    _print_result(args.n, result, model.model_build_time, model.solve_time)
    return 0
