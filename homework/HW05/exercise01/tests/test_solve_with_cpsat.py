from queens.model_cpsat import NQueensCPSAT
from queens.verify import verify_assignment


def test_solve_satisfiable():
    for n in range(4, 20):
        model = NQueensCPSAT(n)
        solution = model.solve()
        assert solution is not False
        assert solution is not None
        assert isinstance(solution, list)
        assert model.solve_time < 1.0
        verify_assignment(n, solution)


def test_solve_unsatisfiable():
    for n in range(2, 4):
        model = NQueensCPSAT(n)
        solution = model.solve()
        assert solution is False
        assert model.solve_time < 1.0
