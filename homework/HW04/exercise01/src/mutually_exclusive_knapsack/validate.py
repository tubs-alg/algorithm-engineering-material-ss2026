from __future__ import annotations

import math

from .models import KnapsackInstance, Solution

RELATIVE_TOLERANCE = 1e-6


def validate_solution(instance: KnapsackInstance, solution: Solution) -> None:
    """Validate that a solution is feasible for a given instance.

    Raises:
            ValueError: If the solution violates instance feasibility constraints.
    """

    available_items = {item.name: item for item in instance.items}
    chosen_items = solution.chosen_items
    chosen_item_set = set(chosen_items)

    if len(chosen_items) != len(chosen_item_set):
        raise ValueError("A solution cannot select the same item more than once.")

    unknown_items = sorted(name for name in chosen_item_set if name not in available_items)
    if unknown_items:
        raise ValueError(
            "Solution selects items that are not part of the instance: " + ", ".join(unknown_items)
        )

    total_weight = sum(available_items[name].weight for name in chosen_items)
    if total_weight > instance.capacity:
        raise ValueError(
            f"Solution exceeds capacity: total weight {total_weight} > {instance.capacity}."
        )

    if not math.isclose(solution.total_weight, total_weight, rel_tol=RELATIVE_TOLERANCE):
        raise ValueError(
            "Solution total_weight does not match the selected items: "
            f"reported {solution.total_weight}, computed {total_weight}."
        )

    objective_value = sum(available_items[name].profit for name in chosen_items)
    if not math.isclose(
        solution.objective_value,
        objective_value,
        rel_tol=RELATIVE_TOLERANCE,
    ):
        raise ValueError(
            "Solution objective_value does not match the selected items: "
            f"reported {solution.objective_value}, computed {objective_value}."
        )

    conflicting_pairs: set[tuple[str, str]] = set()
    for item_name in chosen_items:
        item = available_items[item_name]
        for excluded_name in item.excludes:
            if excluded_name in chosen_item_set:
                left, right = sorted((item_name, excluded_name))
                conflicting_pairs.add((left, right))

    if conflicting_pairs:
        formatted_pairs = ", ".join(f"{left}/{right}" for left, right in sorted(conflicting_pairs))
        raise ValueError(f"Solution violates mutual exclusions: {formatted_pairs}.")
