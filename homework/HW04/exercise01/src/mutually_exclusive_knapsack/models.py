from __future__ import annotations

from typing import FrozenSet, Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Item(BaseModel):
    """Single item that may be placed in the knapsack."""

    model_config = ConfigDict(frozen=True)
    name: str
    profit: float = Field(ge=0)
    weight: float = Field(ge=0)
    excludes: FrozenSet[str] = Field(default_factory=frozenset)

    @model_validator(mode="after")
    def validate_item(self) -> Item:
        if self.name in self.excludes:
            raise ValueError("An item cannot exclude itself.")
        return self


class KnapsackInstance(BaseModel):
    """Problem definition for one mutually exclusive knapsack instance."""

    model_config = ConfigDict(frozen=True)
    capacity: float = Field(ge=0)
    items: tuple[Item, ...]

    @model_validator(mode="after")
    def validate_instance(self) -> KnapsackInstance:
        items_by_name = {item.name: item for item in self.items}
        item_names = [item.name for item in self.items]
        item_name_set = set(item_names)

        if len(item_names) != len(item_name_set):
            raise ValueError("Item names must be unique within an instance.")

        missing_exclusions: list[str] = []
        asymmetric_exclusions: list[str] = []
        for item in self.items:
            unknown = sorted(name for name in item.excludes if name not in item_name_set)
            if unknown:
                missing_exclusions.append(
                    f"{item.name} excludes unknown items: {', '.join(unknown)}"
                )

            asymmetric = sorted(
                excluded_name
                for excluded_name in item.excludes
                if excluded_name in item_name_set
                and item.name not in items_by_name[excluded_name].excludes
            )
            if asymmetric:
                asymmetric_exclusions.append(
                    f"{item.name} excludes items without reciprocal "
                    f"exclusion: {', '.join(asymmetric)}"
                )
        if missing_exclusions:
            raise ValueError("; ".join(missing_exclusions))
        if asymmetric_exclusions:
            raise ValueError("; ".join(asymmetric_exclusions))
        return self

    def solution_from_items(self, chosen_item_names: Iterable[str]) -> Solution:
        """Build a validated solution from an iterable of chosen item names."""

        chosen_items = tuple(chosen_item_names)
        available_items = {item.name: item for item in self.items}
        unknown_items = sorted({name for name in chosen_items if name not in available_items})
        if unknown_items:
            raise ValueError(
                "Cannot create a solution with items that are not part of the instance: "
                + ", ".join(unknown_items)
            )

        solution = Solution(
            chosen_items=chosen_items,
            objective_value=sum(available_items[name].profit for name in chosen_items),
            total_weight=sum(available_items[name].weight for name in chosen_items),
        )

        from .validate import validate_solution

        validate_solution(self, solution)
        return solution


class Solution(BaseModel):
    """Minimal solution container returned by a solver."""

    model_config = ConfigDict(frozen=True)
    chosen_items: tuple[str, ...]
    objective_value: float
    total_weight: float
