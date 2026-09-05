"""Overflowing Hwy 50 / lot traffic. Reuses game._make_car."""
from __future__ import annotations

import math
import random

from lighting import should_sim, set_visible, CULL_TRAFFIC

TRAFFIC_COUNT = 22
LOT_WPS = (
    (-18.0, -8.8),
    (18.0, -8.8),
    (20.0, -23.2),
    (-18.0, -23.2),
)

PAINTS = (
    (200, 30, 40),
    (20, 20, 24),
    (230, 230, 235),
    (30, 170, 190),
    (240, 190, 40),
    (120, 40, 180),
    (230, 90, 20),
    (40, 90, 160),
    (255, 80, 180),
    (80, 255, 210),
    (255, 160, 60),
    (160, 70, 220),
)


def spawn_traffic(game):
    """20+ auto-driving cars. Existing parked cars stay parked."""
    color = game.color
    rng = random.Random(50)
    n = 0
    for i in range(8):
        x = -44 + i * 11.2 + rng.uniform(-1.2, 1.2)
        z = -14.15 + rng.uniform(-0.15, 0.15)
        paint = color.rgb32(*PAINTS[i % len(PAINTS)])
        car = game._make_car((x, 0, z), 90, paint)
        _tag_traffic(car, 'hwy_e', rng.uniform(9.5, 14.0), z)
        game.cars.append(car)
        n += 1
    for i in range(8):
        x = 44 - i * 11.0 + rng.uniform(-1.0, 1.0)
        z = -17.85 + rng.uniform(-0.15, 0.15)
        paint = color.rgb32(*PAINTS[(i + 3) % len(PAINTS)])
        car = game._make_car((x, 0, z), -90, paint)
        _tag_traffic(car, 'hwy_w', rng.uniform(9.0, 13.5), z)
        game.cars.append(car)
        n += 1
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
        game.cars.append(car)
        n += 1
    game.traffic_count = n
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


def tick_traffic(game, dt):
    player = getattr(game, 'player', None)
    opts = getattr(game, 'render_opts', None) or {}
    cull = float(opts.get('cull_traffic', CULL_TRAFFIC))
    px = getattr(player, 'x', 0.0) if player else 0.0
    pz = getattr(player, 'z', 0.0) if player else 0.0
    for car in game.cars:
        if not car:
            continue
        if not getattr(car, 'traffic', False):
            continue
        if game.in_car is car:
            continue
        if player and not should_sim(px, pz, car.x, car.z, cull):
            set_visible(car, False)
            continue
        set_visible(car, True)
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
