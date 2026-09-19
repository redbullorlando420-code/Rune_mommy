"""Hwy 50 / lot traffic. Cars only move when they have an NPC driver.

Empty / idle cars go to parking stalls (see parking.py).
Does not touch vendor.vehicle / _bicycle_step_safe.
"""
from __future__ import annotations

import math
import random

from lighting import should_sim, set_visible, set_lod, CULL_TRAFFIC
import parking

TRAFFIC_COUNT = 22
LOT_WPS = (
    # Cruise loops near edge lots / hwy shoulders — not downtown plaza pads
    (-44.0, -10.6),
    (44.0, -10.6),
    (70.0, -16.0),
    (-48.0, 6.0),
)

PAINTS = (
    (200, 30, 40), (20, 20, 24), (230, 230, 235), (30, 170, 190),
    (240, 190, 40), (120, 40, 180), (230, 90, 20), (40, 90, 160),
    (255, 80, 180), (80, 255, 210), (255, 160, 60), (160, 70, 220),
)


def spawn_traffic(game):
    """Spawn highway cars WITH drivers + empty parked lot cars."""
    try:
        parking.boot(game)
    except Exception as exc:
        print('  parking.boot skip:', exc)

    color = game.color
    rng = random.Random(50)
    n = 0

    # Empty parked cars in lots
    try:
        n += parking.spawn_empty_parked(game, count=12)
    except Exception as exc:
        print('  empty parked skip:', exc)

    # Eastbound Hwy — driven
    for i in range(8):
        x = -44 + i * 11.2 + rng.uniform(-1.2, 1.2)
        z = -14.15 + rng.uniform(-0.15, 0.15)
        paint = color.rgb32(*PAINTS[i % len(PAINTS)])
        car = game._make_car((x, 0, z), 90, paint)
        _tag_traffic(car, 'hwy_e', rng.uniform(9.5, 14.0), z)
        parking.seat_driver(game, car)
        game.cars.append(car)
        n += 1
    # Westbound
    for i in range(8):
        x = 44 - i * 11.0 + rng.uniform(-1.0, 1.0)
        z = -17.85 + rng.uniform(-0.15, 0.15)
        paint = color.rgb32(*PAINTS[(i + 3) % len(PAINTS)])
        car = game._make_car((x, 0, z), -90, paint)
        _tag_traffic(car, 'hwy_w', rng.uniform(9.0, 13.5), z)
        parking.seat_driver(game, car)
        game.cars.append(car)
        n += 1
    # Cruising lot loop — driven
    for i in range(6):
        wp = i % len(LOT_WPS)
        x, z = LOT_WPS[wp]
        x += rng.uniform(-2.5, 2.5)
        z += rng.uniform(-1.2, 1.2)
        nxt = LOT_WPS[(wp + 1) % len(LOT_WPS)]
        yaw = math.degrees(math.atan2(nxt[0] - x, nxt[1] - z))
        paint = color.rgb32(*PAINTS[(i + 6) % len(PAINTS)])
        car = game._make_car((x, 0, z), yaw, paint)
        _tag_traffic(car, 'lot', rng.uniform(5.2, 8.4), z)
        car.wp = (wp + 1) % len(LOT_WPS)
        parking.seat_driver(game, car)
        game.cars.append(car)
        n += 1

    game.traffic_count = n
    print(f'  traffic: cars≈{n} drivers={len(getattr(game, "drivers", []) or [])}')
    return n


def _tag_traffic(car, route, cruise, lane_z):
    car.parked = False
    car.traffic = True
    car.route = route
    car.cruise = cruise
    car.speed = cruise
    car.lane_z = lane_z
    car.wobble = random.uniform(0, 6.28)
    car.wp = 0
    car.drive_t = random.uniform(25.0, 55.0)  # then seek parking
    car.seeking_park = False


def _has_live_driver(car) -> bool:
    ped = getattr(car, 'driver', None)
    if not ped or not getattr(car, 'has_driver', False):
        return False
    if getattr(ped, 'hp', 1) is not None and float(getattr(ped, 'hp', 1) or 0) <= 0:
        return False
    return bool(getattr(ped, 'driving', True))


def _seek_parking(game, car):
    """Send car toward nearest empty stall; park + unseat on arrival."""
    slot = find_or_cached_slot(game, car)
    if not slot:
        return
    key, tx, tz, yaw = slot
    dx, dz = tx - float(car.x), tz - float(car.z)
    dist = math.hypot(dx, dz)
    if dist < 2.2:
        parking.claim_stall(game, car, key, tx, tz, yaw)
        parking.unseat_driver(game, car, to_crowd=True)
        car.traffic = False
        car.seeking_park = False
        car.speed = 0
        return
    car.rotation_y = math.degrees(math.atan2(dx, dz))
    cruise = min(getattr(car, 'cruise', 8.0), 7.0)
    try:
        car.position += car.forward * cruise * 0.016  # tick supplies dt below
    except Exception:
        rad = math.radians(car.rotation_y)
        car.x += math.sin(rad) * cruise * 0.016
        car.z += math.cos(rad) * cruise * 0.016
    car._park_step = (key, tx, tz, yaw, cruise)


def find_or_cached_slot(game, car):
    cached = getattr(car, 'park_target', None)
    if cached:
        key = cached[0]
        occ = getattr(game, 'parking_occ', {}) or {}
        if occ.get(key) in (None, car):
            return cached
    slot = parking.find_empty_stall(game, near=(float(car.x), float(car.z)))
    if slot:
        car.park_target = slot
    return slot


def tick_traffic(game, dt):
    player = getattr(game, 'player', None)
    opts = getattr(game, 'render_opts', None) or {}
    cull = float(opts.get('cull_traffic', CULL_TRAFFIC))
    px = getattr(player, 'x', 0.0) if player else 0.0
    pz = getattr(player, 'z', 0.0) if player else 0.0

    for car in list(getattr(game, 'cars', None) or []):
        if not car:
            continue
        # Player-driven / parked empty: no AI move
        if game.in_car is car:
            continue
        if getattr(car, 'parked', False) and not getattr(car, 'traffic', False):
            set_visible(car, True if not player else should_sim(px, pz, car.x, car.z, cull))
            continue
        if not getattr(car, 'traffic', False):
            continue

        dist = 0.0
        if player:
            dist = ((car.x - px) ** 2 + (car.z - pz) ** 2) ** 0.5
        if player and dist > cull:
            set_visible(car, False)
            continue
        lod_near = float(opts.get('lod_traffic_near', 28.0))
        lod_mid = float(opts.get('lod_traffic_mid', 48.0))
        far_interval = max(1, int(opts.get('ai_far_interval', 3)))
        if dist <= lod_near:
            set_lod(car, 'near')
            do_ai = True
        elif dist <= lod_mid:
            set_lod(car, 'mid')
            do_ai = (int(getattr(game, '_crowd_frame', 0)) % 2) == 0
        else:
            set_lod(car, 'mid')
            do_ai = (int(getattr(game, '_crowd_frame', 0)) % far_interval) == 0
        if not do_ai:
            continue

        # No driver → seek lot / stay still
        if not _has_live_driver(car):
            car.has_driver = False
            if not getattr(car, 'seeking_park', False):
                car.seeking_park = True
            _move_to_park(game, car, dt)
            continue

        parking.sync_driver_pose(car)

        # After cruise timer, peel off to park (idle empty traffic → lots)
        car.drive_t = float(getattr(car, 'drive_t', 40.0)) - dt
        if car.drive_t <= 0 and not getattr(car, 'seeking_park', False):
            car.seeking_park = True

        if getattr(car, 'seeking_park', False):
            _move_to_park(game, car, dt)
            continue

        route = getattr(car, 'route', 'hwy_e')
        cruise = getattr(car, 'cruise', 10.0)
        car.speed = cruise
        if route == 'hwy_e':
            car.rotation_y = 90
            try:
                car.position += car.forward * cruise * dt
            except Exception:
                car.x += cruise * dt
            car.y = 0
            car.z = getattr(car, 'lane_z', -14.2)
            if car.x > 52:
                car.x = -50
        elif route == 'hwy_w':
            car.rotation_y = -90
            try:
                car.position += car.forward * cruise * dt
            except Exception:
                car.x -= cruise * dt
            car.y = 0
            car.z = getattr(car, 'lane_z', -17.8)
            if car.x < -52:
                car.x = 50
        else:
            wps = LOT_WPS
            i = int(getattr(car, 'wp', 0)) % len(wps)
            tx, tz = wps[i]
            dx, dz = tx - car.x, tz - car.z
            if math.hypot(dx, dz) < 1.8:
                i = (i + 1) % len(wps)
                car.wp = i
                tx, tz = wps[i]
                dx, dz = tx - car.x, tz - car.z
            car.rotation_y = math.degrees(math.atan2(dx, dz))
            try:
                car.position += car.forward * cruise * dt
            except Exception:
                rad = math.radians(car.rotation_y)
                car.x += math.sin(rad) * cruise * dt
                car.z += math.cos(rad) * cruise * dt
            car.y = 0
            car.x = max(-46, min(50, car.x))
            car.z = max(-40, min(10, car.z))


def _move_to_park(game, car, dt):
    slot = find_or_cached_slot(game, car)
    if not slot:
        car.speed = 0
        return
    key, tx, tz, yaw = slot
    dx, dz = tx - float(car.x), tz - float(car.z)
    dist = math.hypot(dx, dz)
    if dist < 2.2:
        parking.claim_stall(game, car, key, tx, tz, yaw)
        if _has_live_driver(car):
            parking.unseat_driver(game, car, to_crowd=True)
        car.traffic = False
        car.seeking_park = False
        car.speed = 0
        return
    car.rotation_y = math.degrees(math.atan2(dx, dz))
    cruise = min(float(getattr(car, 'cruise', 8.0) or 8.0), 7.5)
    car.speed = cruise
    try:
        car.position += car.forward * cruise * dt
    except Exception:
        rad = math.radians(car.rotation_y)
        car.x += math.sin(rad) * cruise * dt
        car.z += math.cos(rad) * cruise * dt
    car.y = 0
