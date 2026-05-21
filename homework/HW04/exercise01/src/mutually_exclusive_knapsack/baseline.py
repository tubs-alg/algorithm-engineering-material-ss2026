from __future__ import annotations

from time import perf_counter_ns
from typing import Any, cast

from highspy import Highs, HighsModelStatus, HighsStatus, HighsVarType

from .models import KnapsackInstance, Solution
from .validate import validate_solution


class HighsSolver:
    """Simple HiGHS-based baseline solver using binary item variables."""

    def __init__(self, /, instance: KnapsackInstance) -> None:
        self.instance = instance
        self.item_to_index = {item.name: i for i, item in enumerate(instance.items)}
        self.index_to_item = list(instance.items)
        self.total_solve_time = 0.0
        self._build_model()

    def solve(self) -> Solution:
        """Solve the instance as a binary MIP in HiGHS."""

        start_time = perf_counter_ns()
        status = self.model.solve()
        end_time = perf_counter_ns()
        self.total_solve_time += (end_time - start_time) * 1e-9

        if status != HighsStatus.kOk:
            raise RuntimeError(f"HiGHS failed with status {status}.")

        model_status = self.model.getModelStatus()
        if model_status == HighsModelStatus.kModelEmpty:
            solution = self.instance.solution_from_items(())
            validate_solution(self.instance, solution)
            return solution
        if model_status != HighsModelStatus.kOptimal:
            raise RuntimeError(f"HiGHS did not return an optimal solution: {model_status}.")

        variable_values = self.model.allVariableValues()
        solution = self.instance.solution_from_items(
            item.name
            for item, value in zip(self.index_to_item, variable_values, strict=False)
            if value > 0.5
        )
        validate_solution(self.instance, solution)
        return solution

    def _build_model(self) -> None:
        self.model = Highs()
        self.model.setOptionValue("output_flag", False)

        item_count = len(self.instance.items)
        self.variables = self.model.addVariables(
            item_count,
            obj=[item.profit for item in self.instance.items],
            lb=[0.0] * item_count,
            ub=[1.0] * item_count,
            type=[HighsVarType.kInteger] * item_count,
            out_array=True,
        )
        self.model.setMaximize()

        if item_count > 0:
            capacity_expression = sum(
                self.variables[i] * self.instance.items[i].weight for i in range(item_count)
            )
            self.model.addConstr(cast(Any, capacity_expression <= self.instance.capacity))

        added_exclusions: set[tuple[int, int]] = set()
        for i, item in enumerate(self.instance.items):
            for excluded_name in item.excludes:
                excluded_index = self.item_to_index[excluded_name]
                left, right = sorted((i, excluded_index))
                pair = (left, right)
                if pair in added_exclusions:
                    continue
                added_exclusions.add(pair)
                self.model.addConstr(self.variables[i] + self.variables[excluded_index] <= 1.0)
