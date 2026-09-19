"""Parking lots + stall occupancy. Empty cars sit here; moving cars need drivers (traffic.py)."""
from __future__ import annotations

import math
import random
from typing import Any, Optional, Tuple

from models3d._base import _t, _rgb

Y_LOT = 0.02
Y_PAINT = 0.12

# lot_id -> stalls (x, z, yaw_deg)
LOTS: dict[str, list[tuple[float, float, float]]] = {
    'plaza': [
        (-10.0, -11.2, 90), (-6.5, -11.2, 90), (-3.0, -11.2, 90),
        (0.5, -11.2, 90), (4.0, -11.2, 90), (7.5, -11.2, 90),
        (11.0, -11.2, 90), (14.5, -11.2, 90),
        (-10.0, -13.8, -90), (-6.5, -13.8, -90), (-3.0, -13.8, -90),
        (0.5, -13.8, -90), (4.0, -13.8, -90), (7.5, -13.8, -90),
    ],
    'gas': [
        (16.0, -10.5, 0), (18.5, -10.5, 0), (21.0, -10.5, 0),
        (16.0, -15.5, 180), (18.5, -15.5, 180), (21.0, -15.5, 180),
    ],
    'club27': [
        (36.0, -20.0, 90), (39.5, -20.0, 90), (43.0, -20.0, 90),
        (36.0, -26.0, -90), (39.5, -26.0, -90), (43.0, -26.0, -90),
    ],
    'spa': [
        (-38.0, -14.0, 0), (-34.5, -14.0, 0), (-31.0, -14.0, 0),
        (-38.0, -20.0, 180), (-34.5, -20.0, 180),
    ],
    'walmart': [
        (54.0, -28.0, 90), (57.5, -28.0, 90), (61.0, -28.0, 90),
        (54.0, -32.0, -90), (57.5, -32.0, -90), (61.0, -32.0, -90),
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
        ('plaza', 0.0, -12.5, 28.0, 8.0),
        ('gas', 18.5, -13.0, 10.0, 8.0),
        ('club27', 39.5, -23.0, 14.0, 10.0),
        ('spa', -34.5, -17.0, 12.0, 9.0),
        ('walmart', 57.5, -30.0, 14.0, 8.0),
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
