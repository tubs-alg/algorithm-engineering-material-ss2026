import pytest
from pydantic import ValidationError

from mutually_exclusive_knapsack import Item, KnapsackInstance


def test_instance_accepts_consistent_items() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=5.0, weight=2.0, excludes=frozenset({"b"})),
            Item(name="b", profit=4.0, weight=3.0, excludes=frozenset({"a"})),
        ),
    )

    assert instance.capacity == 10.0
    assert tuple(item.name for item in instance.items) == ("a", "b")


def test_instance_rejects_duplicate_item_names() -> None:
    with pytest.raises(ValidationError, match="Item names must be unique"):
        KnapsackInstance(
            capacity=10.0,
            items=(
                Item(name="a", profit=5.0, weight=2.0),
                Item(name="a", profit=4.0, weight=3.0),
            ),
        )


def test_instance_rejects_unknown_excluded_items() -> None:
    with pytest.raises(ValidationError, match="excludes unknown items"):
        KnapsackInstance(
            capacity=10.0,
            items=(
                Item(name="a", profit=5.0, weight=2.0, excludes=frozenset({"missing"})),
                Item(name="b", profit=4.0, weight=3.0),
            ),
        )


def test_instance_reports_all_unknown_excluded_items() -> None:
    with pytest.raises(
        ValidationError,
        match="a excludes unknown items: x; b excludes unknown items: y",
    ):
        KnapsackInstance(
            capacity=10.0,
            items=(
                Item(name="a", profit=5.0, weight=2.0, excludes=frozenset({"x"})),
                Item(name="b", profit=4.0, weight=3.0, excludes=frozenset({"y"})),
            ),
        )


def test_instance_rejects_asymmetric_exclusions() -> None:
    with pytest.raises(ValidationError, match="without reciprocal exclusion"):
        KnapsackInstance(
            capacity=10.0,
            items=(
                Item(name="a", profit=5.0, weight=2.0, excludes=frozenset({"b"})),
                Item(name="b", profit=4.0, weight=3.0),
            ),
        )


def test_solution_from_items_computes_weight_and_objective() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=5.0, weight=2.0),
            Item(name="b", profit=4.0, weight=3.0),
        ),
    )

    solution = instance.solution_from_items(["b", "a"])

    assert solution.chosen_items == ("b", "a")
    assert solution.objective_value == 9.0
    assert solution.total_weight == 5.0


def test_solution_from_items_rejects_unknown_item_names() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(Item(name="a", profit=5.0, weight=2.0),),
    )

    with pytest.raises(ValueError, match="not part of the instance"):
        instance.solution_from_items(["a", "missing"])


def test_solution_from_items_rejects_infeasible_selection() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=5.0, weight=2.0, excludes=frozenset({"b"})),
            Item(name="b", profit=4.0, weight=3.0, excludes=frozenset({"a"})),
        ),
    )

    with pytest.raises(ValueError, match="mutual exclusions"):
        instance.solution_from_items(["a", "b"])
