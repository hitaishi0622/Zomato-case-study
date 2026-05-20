"""Load budget tier cost ranges from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from restaurant_rec.domain.preferences import Budget

# Inclusive min/max for cost_for_two (INR)
BudgetRange = tuple[int, int]


def load_budget_tiers(path: Path) -> dict[Budget, BudgetRange]:
    """Load global budget tiers from config/budget_tiers.yaml."""
    if not path.is_file():
        raise FileNotFoundError(f"Budget tiers config not found: {path}")

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    global_tiers: dict[str, Any] = data.get("global") or data
    result: dict[Budget, BudgetRange] = {}

    for budget in Budget:
        raw = global_tiers.get(budget.value)
        if not raw or not isinstance(raw, (list, tuple)) or len(raw) != 2:
            raise ValueError(f"Invalid range for budget tier '{budget.value}' in {path}")
        low, high = int(raw[0]), int(raw[1])
        result[budget] = (low, high)

    return result


def cost_in_budget(cost: float, budget: Budget, tiers: dict[Budget, BudgetRange]) -> bool:
    """Return True if cost falls within the tier range (inclusive both ends)."""
    low, high = tiers[budget]
    return low <= cost <= high
