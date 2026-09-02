"""Uniform spatial hash for nearby queries. Original, classic cell-hash."""
from __future__ import annotations

import math


class SpatialHash:
    """2D (x, z) hash. insert/remove/nearby. cell size defaults to 6."""

    def __init__(self, cell=6):
        self.cell = float(cell) if cell else 6.0
        self._cells = {}
        self._where = {}

    def _key(self, x, z):
        c = self.cell
        return (math.floor(x / c), math.floor(z / c))

    def insert(self, key, x, z):
        """Place or move `key` to (x, z)."""
        self.remove(key)
        cxz = self._key(float(x), float(z))
        bucket = self._cells.get(cxz)
        if bucket is None:
            bucket = {}
            self._cells[cxz] = bucket
        bucket[key] = (float(x), float(z))
        self._where[key] = cxz

    def remove(self, key):
        loc = self._where.pop(key, None)
        if loc is None:
            return
        bucket = self._cells.get(loc)
        if not bucket:
            return
        bucket.pop(key, None)
        if not bucket:
            self._cells.pop(loc, None)

    def nearby(self, x, z, r):
        """Return list of (key, px, pz) within radius r of (x, z)."""
        r = float(r)
        if r < 0:
            return []
        c = self.cell
        r2 = r * r
        min_cx = math.floor((x - r) / c)
        max_cx = math.floor((x + r) / c)
        min_cz = math.floor((z - r) / c)
        max_cz = math.floor((z + r) / c)
        out = []
        cells = self._cells
        for cx in range(min_cx, max_cx + 1):
            for cz in range(min_cz, max_cz + 1):
                bucket = cells.get((cx, cz))
                if not bucket:
                    continue
                for key, (px, pz) in bucket.items():
                    dx = px - x
                    dz = pz - z
                    if dx * dx + dz * dz <= r2:
                        out.append((key, px, pz))
        return out

    def __len__(self):
        return len(self._where)

    def clear(self):
        self._cells.clear()
        self._where.clear()
