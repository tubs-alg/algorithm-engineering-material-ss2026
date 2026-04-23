try:
    from ._core import cpp_tsp
except ModuleNotFoundError as exc:
    if exc.name != "tsp_heuristic._core":
        raise
