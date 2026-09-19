"""Parking lots + stall occupancy. Empty cars sit here; moving cars need drivers (traffic.py)."""
from __future__ import annotations

import math
import random
from typing import Any, Optional, Tuple

from models3d._base import _t, _rgb

Y_LOT = 0.02
Y_PAINT = 0.12

# lot_id -> stalls (x, z, yaw_deg)
# Edge lots only — keep downtown / Hwy 50 plaza clear for NPCs & retail.
# Each lot sits in open space with an exit toward a main road (Hwy 50 or side arterial).
LOTS: dict[str, list[tuple[float, float, float]]] = {
    # NW edge — exits south onto W Hwy 50 approach
    'edge_nw': [
        (-54.0, 10.0, 180), (-50.5, 10.0, 180), (-47.0, 10.0, 180), (-43.5, 10.0, 180),
        (-54.0, 7.0, 0), (-50.5, 7.0, 0), (-47.0, 7.0, 0), (-43.5, 7.0, 0),
    ],
    # SW edge — exits north/east toward W Hwy 50
    'edge_sw': [
        (-54.0, -40.0, 90), (-50.5, -40.0, 90), (-47.0, -40.0, 90), (-43.5, -40.0, 90),
        (-54.0, -43.5, -90), (-50.5, -43.5, -90), (-47.0, -43.5, -90),
    ],
    # NE edge — exits south onto E spur / toward Best Buy row
    'edge_ne': [
        (68.0, 12.0, 180), (71.5, 12.0, 180), (75.0, 12.0, 180), (78.5, 12.0, 180),
        (68.0, 8.5, 0), (71.5, 8.5, 0), (75.0, 8.5, 0), (78.5, 8.5, 0),
    ],
    # SE edge past Walmart — exits west onto E Hwy 50
    'edge_se': [
        (70.0, -42.0, 90), (73.5, -42.0, 90), (77.0, -42.0, 90), (80.5, -42.0, 90),
        (70.0, -45.5, -90), (73.5, -45.5, -90), (77.0, -45.5, -90),
    ],
    # Far-east highway shoulder lot (not downtown) — direct onto E Hwy 50
    'edge_hwy_e': [
        (74.0, -12.0, 0), (77.5, -12.0, 0), (81.0, -12.0, 0),
        (74.0, -20.0, 180), (77.5, -20.0, 180), (81.0, -20.0, 180),
    ],
}


def all_stalls():
    out = []
    for lid, stalls in LOTS.items():
        for i, (x, z, yaw) in enumerate(stalls):
            out.append((lid, i, x, z, yaw))
    return out


def boot(game) -> int:
    if getattr(game, 'parking_booted', False):
        return int(getattr(game, 'parking_stall_count', 0) or 0)
    Entity = game.Entity
    color = game.color
    n = 0
    pads = (
        # Open-space pads at map edge (no downtown / central Hwy 50 plaza stack)
        ('edge_nw', -48.5, 8.5, 16.0, 8.0),
        ('edge_sw', -48.5, -41.5, 16.0, 8.0),
        ('edge_ne', 73.0, 10.0, 16.0, 8.0),
        ('edge_se', 75.0, -43.5, 16.0, 8.0),
        ('edge_hwy_e', 77.5, -16.0, 12.0, 12.0),
    )
    # Painted exit arrows toward main roads (visual only)
    exits = (
        (-48.5, 5.5, 0),      # NW -> south to W Hwy
        (-40.0, -41.5, 90),   # SW -> east
        (73.0, 6.0, 0),       # NE -> south
        (68.0, -43.5, -90),   # SE -> west to E Hwy
        (70.0, -16.0, -90),   # hwy_e -> west onto E Hwy 50
    )
    for _lid, cx, cz, w, d in pads:
        try:
            Entity(
                model='cube', scale=(w, 0.04, d), position=(cx, Y_LOT, cz),
                color=_rgb(color, 38, 36, 40),
                texture=_t('asphalt'), texture_scale=(4, 2),
            )
            Entity(
                model='cube', scale=(max(2.0, w * 0.15), 0.05, 0.18),
                position=(cx, Y_PAINT, cz), color=_rgb(color, 230, 220, 80),
            )
            n += 2
        except Exception as exc:
            print('  parking pad skip', _lid, exc)
    for cx, cz, yaw in exits:
        try:
            Entity(
                model='cube', scale=(1.8, 0.06, 0.35),
                position=(cx, Y_PAINT, cz), rotation_y=yaw,
                color=_rgb(color, 80, 200, 120),
            )
            n += 1
        except Exception:
            pass
    for _lid, _i, x, z, yaw in all_stalls():
        try:
            Entity(
                model='cube', scale=(0.12, 0.05, 2.0),
                position=(x, Y_PAINT, z), rotation_y=yaw,
                color=_rgb(color, 235, 225, 90),
            )
            n += 1
        except Exception:
            pass
    game.parking_occ = {}
    for lid, i, *_ in all_stalls():
        game.parking_occ[f'{lid}:{i}'] = None
    game.parking_stall_count = len(game.parking_occ)
    game.parking_booted = True
    game.drivers = list(getattr(game, 'drivers', None) or [])
    print(f'  parking: lots={len(LOTS)} stalls={game.parking_stall_count} meshes≈{n}')
    return game.parking_stall_count


def find_empty_stall(game, prefer_lots=None, near=None):
    occ = getattr(game, 'parking_occ', None)
    if not occ:
        return None
    prefer = set(prefer_lots or [])
    cands = []
    for lid, i, x, z, yaw in all_stalls():
        if prefer and lid not in prefer:
            continue
        key = f'{lid}:{i}'
        if occ.get(key) is not None:
            continue
        dist = 0.0
        if near is not None:
            dist = math.hypot(x - near[0], z - near[1])
        cands.append((dist, key, x, z, yaw))
    if not cands and prefer:
        return find_empty_stall(game, prefer_lots=None, near=near)
    if not cands:
        return None
    cands.sort(key=lambda t: t[0])
    _d, key, x, z, yaw = cands[0]
    return key, x, z, yaw


def release_stall(game, car):
    occ = getattr(game, 'parking_occ', None)
    if not occ or not car:
        return
    key = getattr(car, 'parking_stall', None)
    if key and occ.get(key) is car:
        occ[key] = None
    car.parking_stall = None


def claim_stall(game, car, key, x, z, yaw):
    occ = getattr(game, 'parking_occ', None)
    if occ is None:
        return
    release_stall(game, car)
    occ[key] = car
    car.parking_stall = key
    car.parked = True
    car.route = 'parked'
    car.traffic = False
    car.speed = 0.0
    try:
        car.position = (x, 0, z)
        car.rotation_y = yaw
    except Exception:
        car.x, car.y, car.z = x, 0, z
        car.rotation_y = yaw


def seat_driver(game, car, ped=None):
    color = game.color
    if ped is None:
        paints = (
            (255, 90, 180), (90, 220, 255), (255, 210, 60),
            (190, 90, 255), (80, 255, 190), (255, 120, 80),
        )
        rgb = random.choice(paints)
        ped = game._humanoid(
            float(getattr(car, 'x', 0)), float(getattr(car, 'z', 0)),
            shirt=color.rgb32(*rgb),
            pants=color.rgb32(30, 28, 40),
            skin=color.rgb32(255, 200, 160),
            hitbox=False,
            detail='crowd',
        )
    ped.driving = True
    ped.driver_of = car
    ped.kind = 'driver'
    ped.npc_name = getattr(ped, 'npc_name', None) or 'driver'
    ped.hittable = False
    try:
        ped.parent = car
        ped.position = (0, 0.55, -0.15)
        ped.rotation_y = 0
        ped.scale = 0.92
    except Exception:
        try:
            ped.x = float(car.x)
            ped.z = float(car.z)
            ped.y = 0.55
        except Exception:
            pass
    car.driver = ped
    car.has_driver = True
    if not hasattr(game, 'drivers') or game.drivers is None:
        game.drivers = []
    if ped not in game.drivers:
        game.drivers.append(ped)
    ignore = getattr(game, 'ignore', None)
    if ignore is not None and ped not in ignore:
        try:
            ignore.append(ped)
        except Exception:
            pass
    return ped


def unseat_driver(game, car, to_crowd=True):
    ped = getattr(car, 'driver', None)
    car.driver = None
    car.has_driver = False
    if not ped:
        return None
    ped.driving = False
    ped.driver_of = None
    try:
        ped.parent = game.scene if hasattr(game, 'scene') else None
    except Exception:
        try:
            ped.parent = None
        except Exception:
            pass
    try:
        ped.scale = 1
        ped.position = (float(car.x) + 1.6, 0, float(car.z))
        ped.y = 0
    except Exception:
        pass
    if to_crowd:
        if not getattr(game, 'peds', None):
            game.peds = []
        if ped not in game.peds:
            ped.role = 'civilian'
            ped.walk_speed = random.uniform(1.2, 1.9)
            ped.wander_t = random.uniform(0.5, 2.0)
            ped.heading = random.uniform(0, 360)
            ped.run_crazy = False
            ped.hittable = True
            game.peds.append(ped)
            if ped not in (game.npcs or []):
                try:
                    game.npcs.append(ped)
                except Exception:
                    pass
    return ped


def sync_driver_pose(car):
    ped = getattr(car, 'driver', None)
    if not ped or not getattr(ped, 'driving', False):
        return
    try:
        if getattr(ped, 'parent', None) is car:
            return
    except Exception:
        pass
    try:
        ped.x = float(car.x)
        ped.z = float(car.z)
        ped.y = 0.55
        ped.rotation_y = float(car.rotation_y)
    except Exception:
        pass


def spawn_empty_parked(game, count=10):
    """Park empty (no-driver) cars in stalls — they do not drive."""
    color = game.color
    paints = (
        (200, 30, 40), (20, 20, 24), (230, 230, 235), (30, 170, 190),
        (240, 190, 40), (120, 40, 180), (230, 90, 20), (40, 90, 160),
    )
    n = 0
    for i in range(count):
        slot = find_empty_stall(game)
        if not slot:
            break
        key, x, z, yaw = slot
        paint = color.rgb32(*paints[i % len(paints)])
        car = game._make_car((x, 0, z), yaw, paint)
        car.parked = True
        car.traffic = False
        car.has_driver = False
        car.driver = None
        car.route = 'parked'
        car.fuel = float(random.uniform(20, 70))
        car.damage = 0.0
        claim_stall(game, car, key, x, z, yaw)
        game.cars.append(car)
        n += 1
    return n
