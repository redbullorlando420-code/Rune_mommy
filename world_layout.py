"""Deterministic district/lot planner for the playable world."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lot:
    name: str
    kind: str
    x: float
    z: float
    width: float
    depth: float

    def overlaps(self, other: 'Lot', margin: float = 0.35) -> bool:
        return (
            abs(self.x - other.x) * 2 < self.width + other.width + margin * 2
            and abs(self.z - other.z) * 2 < self.depth + other.depth + margin * 2
        )


class LayoutPlanner:
    """Reject overlapping building/road footprints unless override=True."""
    def __init__(self):
        self.lots: list[Lot] = []

    def reserve(self, name: str, kind: str, x: float, z: float, width: float, depth: float, *, override=False) -> bool:
        candidate = Lot(name, kind, float(x), float(z), float(width), float(depth))
        if not override and any(candidate.overlaps(existing) for existing in self.lots):
            return False
        self.lots.append(candidate)
        return True

    def district(self, kind: str) -> list[Lot]:
        return [lot for lot in self.lots if lot.kind == kind]
