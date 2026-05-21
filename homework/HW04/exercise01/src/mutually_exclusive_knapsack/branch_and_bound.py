from __future__ import annotations

import itertools
from time import perf_counter_ns
from typing import Any, Sequence, cast

from highspy import Highs, HighsModelStatus, HighsStatus, HighsVarType

from .models import KnapsackInstance, Solution
from .validate import validate_solution

# Tolerance for validating whether a cut is sufficiently violated by the current solution.
# Do not accept/generate cuts that are only violated by less than this.
CUT_VIOLATION_TOLERANCE = 1e-4

# Tolerance for integrality checks.
INTEGRALITY_TOLERANCE = 1e-5

# Limits introduced to prevent excessive cut generation;
# entries are in (max_depth, max_cut_rounds) format,
# and the first applicable entry will be used to determine
# the maximum number of cut rounds to perform at a given depth.
# You can tune this; the code that uses these limits is already in place.
CUT_ROUND_LIMITS = [
    (0, 1_000_000),  # no real limit at the root
    (2, 10),  # limit at low depths
    (5, 4),  # stricter limit at lowish depths
    (8, 1),  # only single round at medium depths
    # no cuts at all at the even deeper nodes
]

# ---------- LATER EXTENSION: BRANCH VARIABLE SELECTION ----------
# Limit from what amount of samples on we do not use
# a simple average but an exponential decay approach
# for updating pseudocost scores.
PSEUDOCOST_PURE_AVERAGE_LIMIT = 5

# The relative weight of the old pseudocast value compared
# to the new sample when we update pseudocost scores.
PSEUDOCOST_OLD_VALUE_WEIGHT = 0.8

# The number of samples required in each branching direction
# before we consider the pseudocost score of a variable to
# be stable enough without further exploration/strong branching.
PSEUDOCOST_STABILITY_THRESHOLD = 3

# The depth up to which we consider strong branching if
# the pseudocost scores are not yet stable enough.
SOMETIMES_STRONG_BRANCH_DEPTH = 9

# The number of top candidates to consider for strong branching at the top
# of the tree, by depth in the search tree.
STRONG_BRANCHING_TOP_MAX_CANDIDATES = [20, 10, 8, 5]

# The maximum number of unstable candidates to consider
# for strong branching in the upper part of the tree
# below the top, i.e., below depth len(STRONG_BRANCHING_TOP_MAX_CANDIDATES)
# and up to SOMETIMES_STRONG_BRANCH_DEPTH.
STRONG_BRANCHING_MAX_UNSTABLE_CANDIDATES = 2
# The maximum number of stable candidates to consider for strong branching
# in the upper part of the tree below the top.
STRONG_BRANCHING_MAX_STABLE_CANDIDATES = 2
# ----------------------------------------------------------------


class VariableStatistics:
    """
    Dummy class for collecting variable-specific statistics.
    This is useful for tracking data that can inform branching decisions.
    """
    pass


class BNBNode:
    """
    Represents a node in the branch-and-bound search tree.
     - partial_assignment: A list indicating the current assignment of items,
       where True means included, False means excluded, and None means unassigned.
     - bound: The bound this node inherited from its parent after the parent was processed,
              which is also an upper bound on the objective value of any solution
              in the subtree rooted at this node.
      - depth: The depth of this node in the search tree, with the root node having depth 0.
      - id: A unique identifier for this node. If you, e.g.,
            want to visualize the search tree, you can use this id
            and add a parent id field to track the edges in the tree.
     - branched_variable_index: The index of the variable that was
                                branched on to create this node from its parent.
     - parent_relaxation_value: The value of the variable that was branched on in the
                                parent's LP relaxation solution.
    """

    def __init__(
        self,
        partial_assignment: list[bool | None],
        bound: float,
        depth: int,
        id: int,
        branched_variable_index: int | None = None,
        parent_relaxation_value: float | None = None,
    ):
        self.partial_assignment = partial_assignment
        self.bound = bound
        self.depth = depth
        self.id = id
        self.branched_variable_index = branched_variable_index
        self.parent_relaxation_value = parent_relaxation_value


class BranchAndBoundSolver:
    """
    Skeleton solver for the exercise.
    """

    def __init__(
        self,
        /,
        instance: KnapsackInstance,
        validate_cuts=True,
    ) -> None:
        self.instance = instance
        self.item_to_index = {item.name: i for i, item in enumerate(instance.items)}
        self.index_to_item = list(instance.items)
        self.exclusion_graph = [
            set(self.item_to_index[excluded] for excluded in item.excludes)
            for item in instance.items
        ]
        self.validate_cuts = validate_cuts
        self.best_assignment = None
        self.lower_bound = -float("inf")
        self.last_cut_was_clique = False
        # statistics that are also included in the final output;
        # you can add any additional statistics tracking to this
        self.statistics: dict[str, Any] = {}
        # our primary performance measure:
        # total time spent in the LP solver
        self.total_lp_time = 0.0
        # total number of branch-and-bound nodes explored
        self.node_count = 0
        # the integrated LP model, which you do not have to modify yourself
        self._build_basic_lp_model()
        # variable statistics
        self.variable_statistics = [VariableStatistics() for _ in instance.items]

    def clique_cut_separation(self, solution: Sequence[float]) -> list[int] | None:
        """
        Placeholder for a method that would separate clique cuts (see task d)).
        Args:
            solution (list[float]):
                The current LP solution,
                as a list of variable values corresponding
                to the items in the instance.
        Returns:
            list[int] | None:
                A list of item indices that form a clique cut,
                or None if no violated cut is found.
        """
        return None

    def knapsack_cover_cut_separation(self, solution: Sequence[float]) -> list[int] | None:
        """
        Placeholder for a method that would separate knapsack cover cuts (see task c)).
        Args:
            solution (list[float]):
                The current LP solution,
                as a list of variable values corresponding
                to the items in the instance.
        Returns:
            list[int] | None:
                A list of item indices that form a knapsack cover cut,
                or None if no violated cut is found.
        """
        return None

    def constraint_propagation(self, partial_assignment: list[bool | None]):
        """
        Placeholder for a method that would perform constraint propagation
        based on the current partial assignment of items; see subtask a).
        Args:
            partial_assignment (list[bool | None]):
                A list indicating the current assignment of items,
                where True means included, False means excluded,
                and None means unassigned.
        Returns:
            No value is returned, the partial_assignment list is supposed
            to be modified in-place to reflect any deductions made through
            constraint propagation.
        """
        pass

    def bound(self, node: BNBNode) -> tuple[float, Sequence[float] | None]:
        """
        Compute a bound for the given node,
        including potential cut generation.
        If the solution is integral, also update the
        best solution found so far if the new solution is better.
        Args:
            node (BNBNode):
                The branch-and-bound node whose partial assignment
                should be evaluated.
        Returns:
            tuple[float, Sequence[float] | None]:
                A tuple containing the computed bound and the corresponding
                solution as a list of variable values if the solution is integral,
                or None otherwise.
        """
        partial_assignment = node.partial_assignment
        self._integrate_partial_assignment(partial_assignment)
        cut_found = True
        bound = float("inf")
        values = None
        max_cut_rounds = 0
        for max_depth, mcr_entry in CUT_ROUND_LIMITS:
            if node.depth <= max_depth:
                max_cut_rounds = mcr_entry
                break
        cut_rounds = 0
        while cut_found:
            bound = self._solve_relaxation(partial_assignment)
            if bound <= self.lower_bound:
                return bound, None
            values = self.lp_model.allVariableValues()
            all_integral = all(
                value < INTEGRALITY_TOLERANCE or value > 1.0 - INTEGRALITY_TOLERANCE
                for value in values
            )
            if all_integral:
                self.best_assignment = [bool(value > 0.5) for value in values]
                self.lower_bound = bound
                return self.lower_bound, values
            if cut_rounds < max_cut_rounds:
                cut_found = self.generate_cuts(values)
                cut_rounds += 1
            else:
                cut_found = False
        return bound, values

    def generate_cuts(self, solution: Sequence[float]) -> bool:
        """
        Generate cuts based on the current LP solution.
        Args:
            solution (list[float]):
                The current LP solution, as a list of variable
                values corresponding to the items in the instance.
        Returns:
            bool: True if a cut was added, False otherwise.
        """
        order = ["clique", "cover"] if self.last_cut_was_clique else ["cover", "clique"]
        for cut_type in order:
            if cut_type == "clique":
                cut_indices = self.clique_cut_separation(solution)
                if not cut_indices:
                    continue
                self._add_clique_cut(cut_indices, solution)
                self.last_cut_was_clique = True
                return True
            else:
                cut_indices = self.knapsack_cover_cut_separation(solution)
                if not cut_indices:
                    continue
                self._add_cover_cut(cut_indices, solution)
                self.last_cut_was_clique = False
                return True
        return False

    def branch(self, node: BNBNode, bound: float, solution: Sequence[float]) -> list[BNBNode]:
        """
        Create child nodes for branching on the given node,
        based on the given LP solution.
        Args:
            node (BNBNode): The current node to branch on.
            bound (float): The bound computed for the current node.
            solution (Sequence[float]):
                The current LP solution, as a list of variable
                values corresponding to the items in the instance.
        Returns:
            list[BNBNode]: A list of child nodes created from
                           branching on the current node.
        """
        index = self._max_distance_to_integrality(solution)
        return self._branch_on_variable(node, bound, index, solution)

    def create_child_node(
        self,
        parent: BNBNode,
        partial_assignment: list[bool | None],
        bound: float,
        id: int,
        branched_variable_index: int,
        parent_relaxation_value: float,
        single_child: bool = False,
    ) -> BNBNode:
        """Create a non-root node derived from a parent node."""
        return BNBNode(
            partial_assignment=partial_assignment,
            bound=bound,
            depth=parent.depth + 1 if not single_child else parent.depth,
            id=id,
            branched_variable_index=branched_variable_index,
            parent_relaxation_value=parent_relaxation_value,
        )

    def create_queue_ds(self, root: BNBNode):
        """
        Create the data structure used for the branch-and-bound search.
        """
        return [root]

    def enqueue(self, queue_ds, nodes: list[BNBNode]):
        """
        Enqueue new nodes to the data structure used for the branch-and-bound search.
        """
        queue_ds += nodes

    def dequeue(self, queue_ds) -> BNBNode:
        """
        Dequeue a node from the data structure used for the branch-and-bound search.
        """
        return queue_ds.pop()

    def queue_nonempty(self, queue_ds) -> bool:
        """
        Check if the data structure used for the branch-and-bound search is non-empty.
        """
        return len(queue_ds) > 0

    def update_statistics(
        self,
        node: BNBNode,
        child_bound: float,
        child_relaxation_solution: Sequence[float] | None,
    ):
        """
        Called to update any relevant variable statistics
        after a node is evaluated, i.e., had bound() called on it.
        """
        pass

    def heuristic(self) -> list[bool]:
        """
        Placeholder for a heuristic method that
        computes an initial solution to be used
        as initial lower bound; see task b).
        """
        # naive solution: just take the most profitable item that fits
        fitting_items = [
            item for item in self.instance.items if item.weight <= self.instance.capacity
        ]
        if not fitting_items:
            return [False] * len(self.instance.items)
        best_item = max(fitting_items, key=lambda item: item.profit)
        result = [False] * len(self.instance.items)
        result[self.item_to_index[best_item.name]] = True
        return result

    def solve(self) -> Solution:
        """
        Solve a knapsack instance.
        """
        stack = self.create_queue_ds(
            BNBNode(
                partial_assignment=[None] * len(self.instance.items),
                bound=float("inf"),
                depth=0,
                id=0,
                branched_variable_index=None,
                parent_relaxation_value=None,
            )
        )
        # call initial heuristic, validate it and set it as lower bound
        self._validate_solution(self.heuristic())
        self.node_count += 1
        while self.queue_nonempty(stack):
            node = self.dequeue(stack)
            partial_assignment = node.partial_assignment
            if node.bound <= self.lower_bound:
                # drop nodes for which the parent's bound is good enough;
                # can happen on finding a better solution (better LB)
                continue
            # perform constraint propagation
            self.constraint_propagation(partial_assignment)
            # compute bound, including any potential cuts
            bound, solution = self.bound(node)
            self.update_statistics(node, bound, solution)
            if bound <= self.lower_bound:
                continue
            if solution is None:
                raise ValueError(
                    "Bound method cannot return None for a solution that needs to be explored."
                )
            branches = self.branch(node, bound, solution)
            self.enqueue(stack, branches)
        if self.best_assignment is None:
            raise ValueError("No feasible solution found.")
        solution = self.instance.solution_from_items(
            item.name
            for item, assigned in zip(self.index_to_item, self.best_assignment, strict=False)
            if assigned
        )
        validate_solution(self.instance, solution)
        return solution

    # ------------------------ IMPLEMENTATION DETAILS BELOW THIS LINE ------------------------

    # the following methods are for internal use and should not need to be modified
    def _build_basic_lp_model(self):
        """
        Build and populate the LP model.
        """
        self.lp_model = Highs()
        self.lp_model.setOptionValue("output_flag", False)
        n = len(self.instance.items)
        self.variables = self.lp_model.addVariables(
            n,
            obj=[item.profit for item in self.instance.items],
            lb=[0.0] * n,
            ub=[1.0] * n,
            type=[HighsVarType.kContinuous] * n,
            out_array=True,
        )
        self.lp_model.setMaximize()
        # Build a true linear expression explicitly. In highspy 1.14, matrix
        # multiplication returns a HighspyArray rather than a constraint-ready
        # linear expression.
        if n > 0:
            capacity_expression = sum(
                self.variables[i] * self.instance.items[i].weight for i in range(n)
            )
            capacity_constraint = cast(Any, capacity_expression <= self.instance.capacity)
            self.lp_model.addConstr(capacity_constraint)
        # add mutual exclusion constraints
        for i, item in enumerate(self.instance.items):
            for j in item.excludes:
                j_index = self.item_to_index[j]
                self.lp_model.addConstr(self.variables[i] + self.variables[j_index] <= 1.0)  # type: ignore

    def _integrate_partial_assignment(self, partial_assignment: list[bool | None]):
        """
        Set the variable bounds in the LP model according
        to the given partial assignment.
        Args:
            partial_assignment (list[bool | None]):
                A list indicating the current assignment of items,
                where True means included, False means excluded,
                and None means unassigned.
        """
        indices = [self.variables[i].index for i in range(len(partial_assignment))]  # type: ignore

        def to_lb_value(x: bool | None):
            return 1.0 if x is True else 0.0

        def to_ub_value(x: bool | None):
            return 0.0 if x is False else 1.0

        lower_bounds: list[float] = [to_lb_value(x) for x in partial_assignment]
        upper_bounds: list[float] = [to_ub_value(x) for x in partial_assignment]
        self.lp_model.changeColsBounds(
            len(indices),
            cast(Any, indices),
            cast(Any, lower_bounds),
            cast(Any, upper_bounds),
        )

    def _raw_call_solver(self) -> float:
        start_time = perf_counter_ns()
        status = self.lp_model.solve()
        end_time = perf_counter_ns()
        self.total_lp_time += (end_time - start_time) * 1e-9
        if status != HighsStatus.kOk:
            raise RuntimeError(f"LP solver failed with status {status}.")
        status = self.lp_model.getModelStatus()
        if status == HighsModelStatus.kInfeasible:
            return -float("inf")
        elif status == HighsModelStatus.kModelEmpty:
            return 0.0
        elif status != HighsModelStatus.kOptimal:
            raise RuntimeError(
                f"LP solver did not return an optimal solution: model status {status}."
            )
        return self.lp_model.getObjectiveValue()

    def _solve_relaxation(self, partial_assignment: list[bool | None]) -> float:
        """
        The actual bounding method, based on the LP relaxation of the
        problem. You do not have to modify this method yourself.
        """
        self._integrate_partial_assignment(partial_assignment)
        return self._raw_call_solver()

    def _add_clique_cut(self, indices: list[int], solution: Sequence[float]):
        """
        Add a clique cut to the model, given the indices
        of the items that form the clique.
        """
        if self.validate_cuts:
            for i, j in itertools.combinations(indices, 2):
                if j not in self.exclusion_graph[i]:
                    raise ValueError(
                        f"Invalid clique cut: items {self.index_to_item[i].name} "
                        f"and {self.index_to_item[j].name} are not mutually exclusive."
                    )
            if sum(solution[i] for i in indices) < 1.0 + CUT_VIOLATION_TOLERANCE:
                raise ValueError(
                    "Clique cut not violated (or not violated enough) by the current solution."
                )
        self.lp_model.addConstr(sum(self.variables[i] for i in indices) <= 1.0)  # type: ignore

    def _add_cover_cut(self, indices: list[int], solution: Sequence[float]):
        """
        Add a knapsack cover cut to the model, given the indices
        of the items that form the cover.
        """
        cut_rhs = len(indices) - 1
        if self.validate_cuts:
            total_weight = sum(self.index_to_item[i].weight for i in indices)
            if total_weight <= self.instance.capacity:
                raise ValueError(
                    "Invalid cover cut: total weight of the cover "
                    "is not (strictly) greater than the Knapsack's capacity."
                )
            if sum(solution[i] for i in indices) < cut_rhs + CUT_VIOLATION_TOLERANCE:
                raise ValueError(
                    "Cover cut not violated (or not violated enough) by the current solution."
                )
        self.lp_model.addConstr(sum(self.variables[i] for i in indices) <= cut_rhs)  # type: ignore

    def _validate_solution(self, solution: list[bool]):
        chosen_items = [
            item.name
            for item, assigned in zip(self.index_to_item, solution, strict=False)
            if assigned
        ]
        sol = self.instance.solution_from_items(chosen_items)
        validate_solution(self.instance, sol)
        if self.lower_bound < sol.objective_value:
            self.lower_bound = sol.objective_value
            self.best_assignment = solution

    def _max_distance_to_integrality(self, solution: Sequence[float]) -> int:
        """
        Find the index of the variable that is furthest from being integral
        in the given solution.
        Args:
            solution (list[float]):
                The current LP solution, as a list of variable
                values corresponding to the items in the instance.
        Returns:
            int: The index of the variable that is furthest from being integral.
        Raises:
            ValueError: If all variables are integral (within the integrality tolerance).
        """
        index, value = max(enumerate(solution), key=lambda pair: min(pair[1], 1.0 - pair[1]))
        max_dist = min(value, 1.0 - value)
        if max_dist < INTEGRALITY_TOLERANCE:
            raise ValueError("No fractional variable to branch on.")
        return index

    def _branch_on_variable(
        self, node: BNBNode, bound: float, variable_index: int, solution: Sequence[float]
    ) -> list[BNBNode]:
        """
        Auxiliary method to actually create children for branching on a given variable index.
        Arguments:
            node: the node to branch on
            bound: the bound computed for the current node, to be inherited by the children
            variable_index: the index of the variable to branch on
            solution: node's LP relaxation solution
        """
        partial1 = node.partial_assignment.copy()
        partial1[variable_index] = True
        partial2 = node.partial_assignment.copy()
        partial2[variable_index] = False
        parent_relaxation_value = solution[variable_index]
        self.node_count += 2
        return [
            self.create_child_node(
                parent=node,
                partial_assignment=partial1,
                bound=bound,
                id=self.node_count - 2,
                branched_variable_index=variable_index,
                parent_relaxation_value=parent_relaxation_value,
            ),
            self.create_child_node(
                parent=node,
                partial_assignment=partial2,
                bound=bound,
                id=self.node_count - 1,
                branched_variable_index=variable_index,
                parent_relaxation_value=parent_relaxation_value,
            ),
        ]

    def _solve_and_reset_bounds(self, old: list[bool | None], new: list[bool | None]) -> float:
        """
        Auxiliary method to solve the new partial assignment
        while the currently integrated LP relaxation (old) 
        is in place before and then reset the variable bounds
        that were modified to go back to the old partial assignment, 
        to prepare for the next iteration.
        """
        diff = [
            (i, old_val, new_val)
            for i, (old_val, new_val) in enumerate(zip(old, new, strict=False))
            if old_val != new_val
        ]
        self.lp_model.changeColsBounds(
            len(diff),
            cast(Any, [t[0] for t in diff]),
            cast(Any, [1.0 if t[2] is True else 0.0 for t in diff]),
            cast(Any, [0.0 if t[2] is False else 1.0 for t in diff]),
        )
        bound = self._raw_call_solver()
        self.lp_model.changeColsBounds(
            len(diff),
            cast(Any, [t[0] for t in diff]),
            cast(Any, [1.0 if t[1] is True else 0.0 for t in diff]),
            cast(Any, [0.0 if t[1] is False else 1.0 for t in diff]),
        )
        return bound
