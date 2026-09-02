"""Weighted picks and gold drops. Original tables, classic weighted-choice."""
from __future__ import annotations

import random

GOLD_RANGE = {
    "civilian": (8, 16),
    "thug": (12, 25),
    "walker": (10, 20),
    "barrel": (3, 6),
}


def weighted_choice(pairs, rng=None):
    """pairs: iterable of (item, weight). Returns one item. Weight <= 0 skipped."""
    rng = rng or random
    items = []
    weights = []
    for item, w in pairs:
        w = float(w)
        if w <= 0:
            continue
        items.append(item)
        weights.append(w)
    if not items:
        raise ValueError("weighted_choice needs at least one positive weight")
    total = sum(weights)
    r = rng.random() * total
    acc = 0.0
    for item, w in zip(items, weights):
        acc += w
        if r <= acc:
            return item
    return items[-1]


def gold_drop(kind, rng=None):
    """Integer gold for a kill/break. Unknown kinds use the civilian band."""
    rng = rng or random
    lo, hi = GOLD_RANGE.get(str(kind).lower(), GOLD_RANGE["civilian"])
    return int(rng.randint(lo, hi))
