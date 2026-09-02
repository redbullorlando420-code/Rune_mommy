"""Click-to-walk A* and tick along the path. Port of move.js + movement.js."""
from __future__ import annotations

import math

from constants import WALK_SPEED, TICK_MS, dist, ACTION
from pathfinding import astar, nearest_walkable
from worldmap import walkable_at


def set_path(world, player, x, y):
    w, h = world.map["w"], world.map["h"]
    start = nearest_walkable(world.map["walk"], w, h, player.x, player.y)
    goal = nearest_walkable(world.map["walk"], w, h, x, y)
    path = astar(world.map["walk"], w, h, start["x"], start["y"], goal["x"], goal["y"])
    if not path:
        player.path = []
        return False
    if len(path) > 1 and dist(player, path[0]) < 0.35:
        path = path[1:]
    player.path = path
    return True


def on_move(world, player, payload):
    try:
        x = float(payload.get("x"))
        y = float(payload.get("y"))
    except (TypeError, ValueError):
        return
    if not math.isfinite(x) or not math.isfinite(y):
        return
    player.intent = None
    player.channel = None
    player.target = None
    player.action = ACTION["IDLE"]
    set_path(world, player, x, y)
    if player.path:
        player.action = ACTION["WALK"]


def walk_to(world, player, x, y):
    return set_path(world, player, x, y)


def set_destination(world, player, x, y):
    w, h = world.map["w"], world.map["h"]
    start = nearest_walkable(world.map["walk"], w, h, player.x, player.y)
    goal = nearest_walkable(world.map["walk"], w, h, x, y)
    path = astar(world.map["walk"], w, h, start["x"], start["y"], goal["x"], goal["y"])
    if not path:
        player.path = []
        return False
    if len(path) > 1 and dist(player, path[0]) < 0.35:
        path = path[1:]
    player.path = path
    player.action = None
    player.target = None
    return True


def tick_move(world, player, dt):
    if not player.path:
        return
    speed = WALK_SPEED * (dt / 1000)
    remain = speed
    while remain > 0 and player.path:
        wp = player.path[0]
        d = dist(player, wp)
        if d < 0.04:
            player.path.pop(0)
            continue
        step = min(remain, d)
        player.x += ((wp["x"] - player.x) / d) * step
        player.y += ((wp["y"] - player.y) / d) * step
        player.dir = math.atan2(wp["y"] - player.y, wp["x"] - player.x)
        remain -= step
        if step >= d - 0.001:
            player.path.pop(0)
    if not walkable_at(world.map, player.x, player.y):
        n = nearest_walkable(world.map["walk"], world.map["w"], world.map["h"], player.x, player.y)
        player.x = n["x"] + 0.5
        player.y = n["y"] + 0.5
        player.path = []


def move_toward(world, ent, tx, ty, speed, dt):
    d = math.hypot(tx - ent.x, ty - ent.y)
    if d < 0.05:
        return True
    step = speed * (dt / 1000)
    nx = ent.x + ((tx - ent.x) / d) * min(step, d)
    ny = ent.y + ((ty - ent.y) / d) * min(step, d)
    if walkable_at(world.map, nx, ny):
        ent.x = nx
        ent.y = ny
        ent.dir = math.atan2(ty - ent.y, tx - ent.x)
    return math.hypot(tx - ent.x, ty - ent.y) < 0.08
