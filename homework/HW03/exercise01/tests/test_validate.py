import pytest

from mutually_exclusive_knapsack import Item, KnapsackInstance, Solution, validate_solution


def test_validate_solution_accepts_feasible_solution() -> None:
    instance = KnapsackInstance(
        capacity=5.0,
        items=(
            Item(name="a", profit=4.0, weight=2.0, excludes=frozenset({"c"})),
            Item(name="b", profit=3.0, weight=2.5),
            Item(name="c", profit=6.0, weight=4.0, excludes=frozenset({"a"})),
        ),
    )
    solution = Solution(chosen_items=("a", "b"), objective_value=7.0, total_weight=4.5)
    validate_solution(instance, solution)


def test_validate_solution_accepts_small_rounding_deviations() -> None:
    instance = KnapsackInstance(
        capacity=5.0,
        items=(
            Item(name="a", profit=4.0, weight=2.0),
            Item(name="b", profit=3.0, weight=2.5),
        ),
    )
    solution = Solution(
        chosen_items=("a", "b"),
        objective_value=7.0 * (1 + 5e-7),
        total_weight=4.5 * (1 - 5e-7),
    )
    validate_solution(instance, solution)


def test_validate_solution_rejects_duplicate_item_selection() -> None:
    instance = KnapsackInstance(
        capacity=5.0,
        items=(Item(name="a", profit=4.0, weight=2.0),),
    )
    solution = Solution(chosen_items=("a", "a"), objective_value=8.0, total_weight=4.0)
    with pytest.raises(ValueError, match="more than once"):
        validate_solution(instance, solution)


def test_validate_solution_rejects_unknown_items() -> None:
    instance = KnapsackInstance(
        capacity=5.0,
        items=(Item(name="a", profit=4.0, weight=2.0),),
    )
    solution = Solution(chosen_items=("b",), objective_value=3.0, total_weight=1.0)
    with pytest.raises(ValueError, match="not part of the instance"):
        validate_solution(instance, solution)


def test_validate_solution_rejects_capacity_violations() -> None:
    instance = KnapsackInstance(
        capacity=3.0,
        items=(
            Item(name="a", profit=4.0, weight=2.0),
            Item(name="b", profit=3.0, weight=2.0),
        ),
    )
    solution = Solution(chosen_items=("a", "b"), objective_value=7.0, total_weight=4.0)
    with pytest.raises(ValueError, match="exceeds capacity"):
        validate_solution(instance, solution)


def test_validate_solution_rejects_exclusion_violations() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=4.0, weight=2.0, excludes=frozenset({"b"})),
            Item(name="b", profit=3.0, weight=2.0, excludes=frozenset({"a"})),
        ),
    )
    solution = Solution(chosen_items=("a", "b"), objective_value=7.0, total_weight=4.0)
    with pytest.raises(ValueError, match="mutual exclusions"):
        validate_solution(instance, solution)


def test_validate_solution_rejects_total_weight_mismatch() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=4.0, weight=2.0),
            Item(name="b", profit=3.0, weight=2.5),
        ),
    )
    solution = Solution(
        chosen_items=("a", "b"),
        objective_value=7.0,
        total_weight=4.5 * (1 + 2e-6),
    )
    with pytest.raises(ValueError, match="total_weight does not match"):
        validate_solution(instance, solution)


def test_validate_solution_rejects_objective_value_mismatch() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=4.0, weight=2.0),
            Item(name="b", profit=3.0, weight=2.5),
        ),
    )
    solution = Solution(
        chosen_items=("a", "b"),
        objective_value=7.0 * (1 - 2e-6),
        total_weight=4.5,
    )
    with pytest.raises(ValueError, match="objective_value does not match"):
        validate_solution(instance, solution)
