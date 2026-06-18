from time import perf_counter

from ortools.sat.python import cp_model


class NQueensCPSAT:
    def _build_model(self):
        """
        Build the model (i.e., create a list of variables via 
        `self.model.new_bool_var` and add constraints like 
        `self.model.add_exactly_one` or
        `self.model.add_at_most_one`).
        """
        # TODO
        raise NotImplementedError()

    def _decode_solution(self):
        """
        Decode the solution found by and stored in self.solver;
        you can access the value of some boolean variable like
        `self.solver.boolean_value(x)`.
        """
        # TODO
        raise NotImplementedError()

    def __init__(self, n):
        self.n = n
        self.model = cp_model.CpModel()
        before = perf_counter()
        self._build_model()
        after = perf_counter()
        self.model_build_time = after - before

    def solve(self, time_limit: float | None = None) -> bool | None | list[list[bool]]:
        before = perf_counter()
        self.solver = cp_model.CpSolver()
        if time_limit is not None:
            self.solver.parameters.max_time_in_seconds = time_limit
        status = self.solver.solve(self.model)
        after = perf_counter()
        self.solve_time = after - before
        if status in (cp_model.CpSolverStatus.FEASIBLE, cp_model.CpSolverStatus.OPTIMAL):
            return self._decode_solution()
        if status == cp_model.CpSolverStatus.INFEASIBLE:
            return False
        return None
