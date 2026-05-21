import random

from .models import Item, KnapsackInstance


def generate_uniform_instance(
    num_items: int,
    capacity: float,
    min_weight: float,
    max_weight: float,
    min_efficiency: float,
    max_efficiency: float,
    mutual_exclusivity_p: float,
) -> KnapsackInstance:
    """
    Generate a random instance of the Knapsack problem with mutual exclusivity constraints.
    Each item is assigned a random weight uniformly distributed between `min_weight`
    and `max_weight`, and a random profit determined by multiplying the weight by a
    random efficiency uniformly distributed between `min_efficiency` and `max_efficiency`.
    Each pair of items is independently assigned to be mutually exclusive with probability
    `mutual_exclusivity_p`.
    """
    rng = random.Random()
    items = []
    for _ in range(num_items):
        weight = rng.uniform(min_weight, max_weight)
        efficiency = rng.uniform(min_efficiency, max_efficiency)
        profit = weight * efficiency
        items.append(Item(name=f"I_{len(items)}", profit=profit, weight=weight))

    excludes = [set() for _ in range(num_items)]
    for i in range(num_items):
        for j in range(i + 1, num_items):
            if rng.random() < mutual_exclusivity_p:
                excludes[i].add(items[j].name)
                excludes[j].add(items[i].name)
    for i in range(num_items):
        items[i] = Item(
            name=items[i].name,
            profit=items[i].profit,
            weight=items[i].weight,
            excludes=frozenset(excludes[i]),
        )
    return KnapsackInstance(capacity=capacity, items=tuple(items))
