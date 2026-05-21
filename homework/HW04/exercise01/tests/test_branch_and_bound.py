import pytest

from mutually_exclusive_knapsack import BranchAndBoundSolver, KnapsackInstance
from mutually_exclusive_knapsack.baseline import HighsSolver
from mutually_exclusive_knapsack.branch_and_bound import BNBNode
from mutually_exclusive_knapsack.models import Item
from mutually_exclusive_knapsack.validate import validate_solution


class RecordingCutSolver(BranchAndBoundSolver):
    def __init__(
        self,
        instance: KnapsackInstance,
        *,
        cover_cut: list[int] | None,
        clique_cut: list[int] | None,
    ) -> None:
        self.call_order: list[str] = []
        self.added_cover_cut: tuple[list[int], list[float]] | None = None
        self.added_clique_cut: tuple[list[int], list[float]] | None = None
        self._cover_cut = cover_cut
        self._clique_cut = clique_cut
        super().__init__(instance)

    def knapsack_cover_cut_separation(self, solution) -> list[int] | None:
        self.call_order.append("cover")
        return self._cover_cut

    def clique_cut_separation(self, solution) -> list[int] | None:
        self.call_order.append("clique")
        return self._clique_cut

    def _add_cover_cut(self, indices: list[int], solution):
        self.added_cover_cut = (indices, list(solution))

    def _add_clique_cut(self, indices: list[int], solution):
        self.added_clique_cut = (indices, list(solution))


class RecordingChildSolver(BranchAndBoundSolver):
    def __init__(self, instance: KnapsackInstance) -> None:
        self.created_children: list[tuple[int, list[bool | None], float, int, int, float]] = []
        super().__init__(instance)

    def create_child_node(
        self,
        parent: BNBNode,
        partial_assignment: list[bool | None],
        bound: float,
        id: int,
        branched_variable_index: int,
        parent_relaxation_value: float,
    ) -> BNBNode:
        self.created_children.append(
            (
                parent.id,
                partial_assignment.copy(),
                bound,
                id,
                branched_variable_index,
                parent_relaxation_value,
            )
        )
        return super().create_child_node(
            parent,
            partial_assignment,
            bound,
            id,
            branched_variable_index,
            parent_relaxation_value,
        )


def test_solver_solves_empty_instance_without_special_setup() -> None:
    instance = KnapsackInstance(capacity=10.0, items=())

    solution = BranchAndBoundSolver(instance).solve()

    assert solution.chosen_items == ()
    assert solution.objective_value == 0.0
    assert solution.total_weight == 0.0


def test_solver_initializes_index_and_exclusion_graph() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=5.0, weight=2.0, excludes=frozenset({"b"})),
            Item(name="b", profit=4.0, weight=3.0, excludes=frozenset({"a"})),
        ),
    )
    solver = BranchAndBoundSolver(instance)

    assert solver.item_to_index == {"a": 0, "b": 1}
    assert [item.name for item in solver.index_to_item] == ["a", "b"]
    assert solver.exclusion_graph == [{1}, {0}]


def test_integrate_partial_assignment_updates_lp_bounds() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(Item(name="a", profit=5.0, weight=2.0),),
    )
    solver = BranchAndBoundSolver(instance)

    assert solver._solve_relaxation([None]) == pytest.approx(5.0)
    assert solver._solve_relaxation([False]) == pytest.approx(0.0)
    assert solver._solve_relaxation([True]) == pytest.approx(5.0)


def test_branch_rejects_integral_solution() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(Item(name="a", profit=5.0, weight=2.0),),
    )
    solver = BranchAndBoundSolver(instance)
    node = BNBNode(partial_assignment=[None], bound=5.0, depth=0, id=0)

    with pytest.raises(ValueError, match="No fractional variable"):
        solver.branch(node, bound=5.0, solution=[1.0])


def test_root_node_has_no_branching_metadata() -> None:
    root = BNBNode(partial_assignment=[None], bound=float("inf"), depth=0, id=0)

    assert root.branched_variable_index is None
    assert root.parent_relaxation_value is None


def test_generate_cuts_prefers_cover_before_clique() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=5.0, weight=2.0),
            Item(name="b", profit=4.0, weight=3.0),
        ),
    )
    solver = RecordingCutSolver(instance, cover_cut=[0, 1], clique_cut=None)

    cut_added = solver.generate_cuts([0.6, 0.7])

    assert cut_added is True
    assert solver.call_order == ["cover"]
    assert solver.added_cover_cut == ([0, 1], [0.6, 0.7])
    assert solver.last_cut_was_clique is False


def test_generate_cuts_switches_to_clique_first_after_clique_cut() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=5.0, weight=2.0, excludes=frozenset({"b"})),
            Item(name="b", profit=4.0, weight=3.0, excludes=frozenset({"a"})),
        ),
    )
    solver = RecordingCutSolver(instance, cover_cut=None, clique_cut=[0, 1])
    solver.last_cut_was_clique = True

    cut_added = solver.generate_cuts([0.6, 0.7])

    assert cut_added is True
    assert solver.call_order == ["clique"]
    assert solver.added_clique_cut == ([0, 1], [0.6, 0.7])
    assert solver.last_cut_was_clique is True


def test_heuristic_returns_all_false_when_no_item_fits() -> None:
    instance = KnapsackInstance(
        capacity=1.0,
        items=(
            Item(name="a", profit=5.0, weight=2.0),
            Item(name="b", profit=4.0, weight=3.0),
        ),
    )

    assignment = BranchAndBoundSolver(instance).heuristic()

    assert assignment == [False, False]


def test_heuristic_returns_valid_assignment_on_nontrivial_instance() -> None:
    instance = KnapsackInstance(
        capacity=6.0,
        items=(
            Item(name="a", profit=10.0, weight=5.0),
            Item(name="b", profit=7.0, weight=3.0),
            Item(name="c", profit=7.0, weight=3.0),
        ),
    )
    solver = BranchAndBoundSolver(instance)

    assignment = solver.heuristic()
    assert len(assignment) == len(instance.items)
    assert all(isinstance(value, bool) for value in assignment)

    solution = instance.solution_from_items(
        item.name for item, assigned in zip(instance.items, assignment, strict=False) if assigned
    )

    validate_solution(instance, solution)


def test_heuristic_respects_mutual_exclusions() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=9.0, weight=3.0, excludes=frozenset({"b"})),
            Item(name="b", profit=8.0, weight=3.0, excludes=frozenset({"a"})),
            Item(name="c", profit=4.0, weight=2.0),
        ),
    )
    solver = BranchAndBoundSolver(instance)

    assignment = solver.heuristic()
    solution = instance.solution_from_items(
        item.name for item, assigned in zip(instance.items, assignment, strict=False) if assigned
    )

    validate_solution(instance, solution)
    assert not (assignment[0] and assignment[1])


def test_heuristic_returns_valid_solution_with_exclusions() -> None:
    instance = KnapsackInstance(
        capacity=10.0,
        items=(
            Item(name="a", profit=10.0, weight=2.0, excludes=frozenset({"b", "c"})),
            Item(name="b", profit=12.0, weight=5.0, excludes=frozenset({"a"})),
            Item(name="c", profit=12.0, weight=5.0, excludes=frozenset({"a"})),
        ),
    )
    solver = BranchAndBoundSolver(instance)

    assignment = solver.heuristic()

    solution = instance.solution_from_items(
        item.name for item, assigned in zip(instance.items, assignment, strict=False) if assigned
    )

    validate_solution(instance, solution)


def test_correct_result_on_small_instance() -> None:
    json_data = """
    {
        "capacity": 15.0,
        "items": [
            {
            "name": "I_0",
            "profit": 1.4504837908635466,
            "weight": 1.1862765330053668,
            "excludes": []
            },
            {
            "name": "I_1",
            "profit": 1.6841846994947491,
            "weight": 1.795322473903417,
            "excludes": [
                "I_11"
            ]
            },
            {
            "name": "I_2",
            "profit": 2.157319040342987,
            "weight": 1.9147771615394134,
            "excludes": [
                "I_4",
                "I_12",
                "I_10"
            ]
            },
            {
            "name": "I_3",
            "profit": 2.0460658109039573,
            "weight": 1.902986575565583,
            "excludes": [
                "I_14",
                "I_19",
                "I_11"
            ]
            },
            {
            "name": "I_4",
            "profit": 1.3652149736582473,
            "weight": 1.2634094641058304,
            "excludes": [
                "I_10",
                "I_2"
            ]
            },
            {
            "name": "I_5",
            "profit": 1.677111708075764,
            "weight": 1.3693722348375212,
            "excludes": [
                "I_13"
            ]
            },
            {
            "name": "I_6",
            "profit": 1.798933954019253,
            "weight": 1.6207099217875702,
            "excludes": [
                "I_12"
            ]
            },
            {
            "name": "I_7",
            "profit": 2.2615649810617806,
            "weight": 1.8574747610293503,
            "excludes": [
                "I_13"
            ]
            },
            {
            "name": "I_8",
            "profit": 1.3516376527705471,
            "weight": 1.25498201978841,
            "excludes": [
                "I_15"
            ]
            },
            {
            "name": "I_9",
            "profit": 1.5797016243321698,
            "weight": 1.6087763928920498,
            "excludes": [
                "I_12"
            ]
            },
            {
            "name": "I_10",
            "profit": 1.2959087251450168,
            "weight": 1.1913203252693547,
            "excludes": [
                "I_4",
                "I_2"
            ]
            },
            {
            "name": "I_11",
            "profit": 1.2923547041385948,
            "weight": 1.1317162379569452,
            "excludes": [
                "I_1",
                "I_3"
            ]
            },
            {
            "name": "I_12",
            "profit": 1.551314309567154,
            "weight": 1.8672020626844068,
            "excludes": [
                "I_6",
                "I_9",
                "I_2"
            ]
            },
            {
            "name": "I_13",
            "profit": 1.737091048825936,
            "weight": 1.6025116547338147,
            "excludes": [
                "I_5",
                "I_7"
            ]
            },
            {
            "name": "I_14",
            "profit": 1.4801478234850691,
            "weight": 1.372083892420608,
            "excludes": [
                "I_3",
                "I_17"
            ]
            },
            {
            "name": "I_15",
            "profit": 2.2933256873819716,
            "weight": 1.9355159408110372,
            "excludes": [
                "I_8",
                "I_17"
            ]
            },
            {
            "name": "I_16",
            "profit": 1.3121114339240294,
            "weight": 1.4161530510220794,
            "excludes": []
            },
            {
            "name": "I_17",
            "profit": 1.7918996131956095,
            "weight": 1.5153401063848426,
            "excludes": [
                "I_14",
                "I_15"
            ]
            },
            {
            "name": "I_18",
            "profit": 1.5060633860187354,
            "weight": 1.949816615102291,
            "excludes": []
            },
            {
            "name": "I_19",
            "profit": 1.5913665904670196,
            "weight": 1.5499985817372899,
            "excludes": [
                "I_3"
            ]
            }
        ]
    }
    """
    instance = KnapsackInstance.model_validate_json(json_data)
    solver = BranchAndBoundSolver(instance, validate_cuts=True)
    solution = solver.solve()
    validate_solution(instance, solution)
    assert solution.objective_value == pytest.approx(16.7902)

    baseline_solver = HighsSolver(instance)
    baseline_solution = baseline_solver.solve()
    validate_solution(instance, baseline_solution)
    assert baseline_solution.objective_value == pytest.approx(16.7902)
    assert set(solution.chosen_items) == set(baseline_solution.chosen_items)
