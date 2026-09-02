#!/usr/bin/env python3
"""Tiny vendor self-check. No Ursina. Run: python3 vendor/_smoke.py"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from vendor.astar import astar
from vendor.loot import gold_drop
from vendor.noise2d import noise2, fbm2
from vendor.spatial import SpatialHash
from vendor.steering import seek, flee
from vendor.vehicle import bicycle_step
from vendor.fsm import FSM

p = astar((0, 0), (4, 0), blocked={(2, 1)})
assert p and p[0] == (0, 0) and p[-1] == (4, 0), p
g = gold_drop("civilian")
assert isinstance(g, int) and 8 <= g <= 16, g
assert -1.0 <= noise2(1.5, 2.5, seed=7) <= 1.0
assert -1.0 <= fbm2(0.2, 0.3, octaves=4, seed=3) <= 1.0
h = SpatialHash(cell=6)
h.insert("a", 0, 0)
h.insert("b", 20, 0)
near = h.nearby(0, 0, 7)
assert any(k == "a" for k, _, _ in near) and not any(k == "b" for k, _, _ in near)
sx, sz = seek(0, 0, 10, 0)
assert abs(sx - 1) < 1e-6 and abs(sz) < 1e-6
fx, fz = flee(0, 0, 10, 0)
assert fx < 0
x, z, yaw, spd = bicycle_step(0, 0, 0, 5, 0, 0, 0.1, vmax=24)
assert z > 0 and abs(x) < 1e-6
m = FSM()
m.add("idle")
m.add("run")
m.set("idle")
m.update(0.016, {})
m.set("run")
assert m.current == "run"
print("OK")
