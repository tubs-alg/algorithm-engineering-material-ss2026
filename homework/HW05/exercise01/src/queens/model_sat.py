from threading import Timer
from time import perf_counter

from pysat.formula import CNF
from pysat.solvers import Solver


class NQueensSATModeler:
    """
    Modeler class for the n queens problem using SAT.
    """

    def __init__(self, n):
        self.n = n
        self.cnf: CNF | None = None
        self._cnf_breaks_symmetries = False

    def create_formula(self, break_symmetries=False) -> CNF:
        """
        Create a CNF formula representing the N-queens problem.
        If break_symmetries is True, this method may add additional
        constraints that break a mirror symmetry of the problem,
        which may help some SAT solvers find solutions faster.
        The only hard requirement is that, if break_symmetries is False,
        the returned formula must be satisfied by all valid N-queens solutions.
        """
        if self.cnf is not None and self._cnf_breaks_symmetries == break_symmetries:
            return self.cnf
        self.cnf = CNF()
        self._cnf_breaks_symmetries = break_symmetries
        # TODO: add clauses to self.cnf (via self.cnf.append or self.cnf.extend);
        # e.g., self.cnf.append([1, -2, 3, 4]) for (x1 OR NOT x2 OR x3 OR x4)
        raise NotImplementedError()
        return self.cnf

    def decode_solution(self, model: list[int]) -> list[list[bool]]:
        """
        Decodes a model (list of literals like [1, -2, 3, -4, ...])
        as returned by a PySAT SAT solver into a 2D list of booleans.
        """
        # TODO
        raise NotImplementedError()

    def encode_assignment(self, assignment: list[list[bool]]) -> list[int]:
        """
        Encodes a 2D list of booleans representing an N-queens solution
        into a list of literals (like [1, -2, 3, -4, ...]) that can be used
        as input to a PySAT SAT solver or be used by debug/test methods to
        check that the formula is satisfied by what should be a satisfying assignment.
        As long as the formula created by create_formula was created with
        break_symmetries=False, the returned list of literals should satisfy
        the formula if and only if the input assignment is a valid N-queens solution.
        """
        # TODO
        raise NotImplementedError()


def solve_with_sat(
    n,
    break_symmetries=False,
    solver_name="Cadical300",
    time_limit: float | None = None,
    times: dict | None = None,
) -> list[list[bool]] | bool | None:
    """
    Run the named SAT solver on the given n (potentially with symmetry breaking
    constraints, if implemented) and with a time limit.
    This method should not need to be changed; all necessary changes should be
    local to the NQueensSATModeler class.
    """
    before = perf_counter()
    modeler = NQueensSATModeler(n)
    formula = modeler.create_formula(break_symmetries=break_symmetries)
    solver = Solver(name=solver_name)
    timer = None

    def interrupt():
        solver.interrupt()

    try:
        solver.append_formula(formula.clauses, no_return=True)
        build = perf_counter()
        if times is not None:
            times["build_time"] = build - before
        if time_limit is not None:
            timer = Timer(time_limit, interrupt, [solver])
            timer.start()
            r = solver.solve_limited(expect_interrupt=True)
        else:
            r = solver.solve()
        after = perf_counter()
        if times is not None:
            times["solve_time"] = after - build
        if r is None:
            return None
        if r is False:
            return False
        model: list[int] = solver.get_model()  # type: ignore
        return modeler.decode_solution(model)
    finally:
        if timer is not None:
            timer.cancel()
        solver.delete()
