from mutually_exclusive_knapsack import HighsSolver, Item, KnapsackInstance


def test_highs_solver_solves_empty_instance() -> None:
    instance = KnapsackInstance(capacity=10.0, items=())

    solution = HighsSolver(instance).solve()

    assert solution.chosen_items == ()
    assert solution.objective_value == 0.0
    assert solution.total_weight == 0.0


def test_highs_solver_finds_best_feasible_selection() -> None:
    instance = KnapsackInstance(
        capacity=4.0,
        items=(
            Item(name="a", profit=5.0, weight=2.0, excludes=frozenset({"b"})),
            Item(name="b", profit=6.0, weight=3.0, excludes=frozenset({"a"})),
            Item(name="c", profit=4.0, weight=2.0),
        ),
    )

    solution = HighsSolver(instance).solve()

    assert solution.chosen_items == ("a", "c")
    assert solution.objective_value == 9.0
    assert solution.total_weight == 4.0
