from queens.model_sat import solve_with_sat
from queens.verify import verify_assignment


def test_satisfiable_no_symmetry_breaking():
    for n in range(4, 20):
        times = {}
        result = solve_with_sat(n, break_symmetries=False, time_limit=10, times=times)
        assert isinstance(result, list)
        assert len(result) == n
        assert all(isinstance(row, list) for row in result)
        assert all(len(row) == n for row in result)
        assert times["build_time"] < 1.0
        assert times["solve_time"] < 1.0
        verify_assignment(n, result)


def test_satisfiable_with_symmetry_breaking():
    for n in range(4, 20):
        times = {}
        result = solve_with_sat(n, break_symmetries=True, time_limit=10, times=times)
        assert isinstance(result, list)
        assert len(result) == n
        assert all(isinstance(row, list) for row in result)
        assert all(len(row) == n for row in result)
        assert times["build_time"] < 1.0
        assert times["solve_time"] < 1.0
        verify_assignment(n, result)


def test_unsatisfiable():
    for n in range(2, 4):
        times = {}
        result = solve_with_sat(n, break_symmetries=False, time_limit=2, times=times)
        assert isinstance(result, bool)
        assert result is not None
        assert result is False
        assert times["build_time"] < 1.0
        assert times["solve_time"] < 1.0
