"""Overflowing Hwy 50 / lot traffic. Reuses game._make_car."""
from __future__ import annotations

import math
import random

from lighting import should_sim, set_visible, CULL_TRAFFIC

TRAFFIC_COUNT = 30
LOT_WPS = ((-42.0, -14.2), (42.0, -14.2))

# Named road graph. Cars prefer these closed circuits over teleporting at a map
# edge, so traffic visibly travels through the regional gateways and race loop.
REGION_LOOPS = {
    'hwy_loop': ((-295, -16), (295, -16), (305, -145), (305, 175), (-305, 175), (-305, -145)),
    'race_loop': ((25, -28), (51, -28), (53, -42), (45, -47), (27, -47), (22, -39)),
    'orlando_loop': ((58, -10), (72, -10), (76, 2), (70, 12), (58, 10)),
}

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
        # Service traffic stays on the east/west highway lanes, avoiding the
        # old off-road parking-lot rectangle.
        x = -40 + i * 14.0 + rng.uniform(-1.0, 1.0)
        z = -14.15 if i % 2 == 0 else -17.85
        yaw = 90 if i % 2 == 0 else -90
        paint = color.rgb32(*PAINTS[(i + 6) % len(PAINTS)])
        car = game._make_car((x, 0, z), yaw, paint)
        _tag_traffic(car, 'hwy_e' if i % 2 == 0 else 'hwy_w', rng.uniform(7.2, 10.4), z)
        game.cars.append(car)
        n += 1
    # A smaller set of node cars makes the world read as connected regions:
    # they turn through actual loops instead of simply wrapping at the edge.
    for route, count in (('hwy_loop', 3), ('race_loop', 3), ('orlando_loop', 2)):
        nodes = REGION_LOOPS[route]
        for i in range(count):
            wp = (i * 2) % len(nodes)
            x, z = nodes[wp]
            nx, nz = nodes[(wp + 1) % len(nodes)]
            yaw = math.degrees(math.atan2(nx - x, nz - z))
            paint = color.rgb32(*PAINTS[(n + i) % len(PAINTS)])
            car = game._make_car((x, 0, z), yaw, paint)
            _tag_traffic(car, route, rng.uniform(7.5, 11.0), z)
            car.route_nodes = nodes
            car.wp = (wp + 1) % len(nodes)
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
    car.turn_rate = random.uniform(72.0, 102.0)  # degrees/sec; no snap turns


def _turn_toward(car, target_yaw, dt):
    """Apply a bounded yaw change and return whether the car is cornering."""
    current = float(getattr(car, 'rotation_y', 0.0) or 0.0)
    delta = (target_yaw - current + 180.0) % 360.0 - 180.0
    limit = float(getattr(car, 'turn_rate', 86.0) or 86.0) * dt
    applied = max(-limit, min(limit, delta))
    car.rotation_y = current + applied
    return abs(applied) / max(0.001, limit)


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
        elif route == 'lot':
            wps = LOT_WPS
            i = int(getattr(car, 'wp', 0)) % len(wps)
            tx, tz = wps[i]
            dx, dz = tx - car.x, tz - car.z
            if math.hypot(dx, dz) < 1.8:
                i = (i + 1) % len(wps)
                car.wp = i
                tx, tz = wps[i]
                dx, dz = tx - car.x, tz - car.z
            sharp = _turn_toward(car, math.degrees(math.atan2(dx, dz)), dt)
            moving_speed = cruise * (0.58 if sharp > 0.82 else 1.0)
            try:
                car.position += car.forward * moving_speed * dt
            except Exception:
                rad = math.radians(car.rotation_y)
                car.x += math.sin(rad) * moving_speed * dt
                car.z += math.cos(rad) * moving_speed * dt
            car.y = 0
            car.x = max(-46, min(50, car.x))
            car.z = max(-40, min(10, car.z))
        else:
            # Node traffic follows region and race loops. Each car chooses the
            # next waypoint, turns toward it, and continuously advances.
            wps = getattr(car, 'route_nodes', None) or REGION_LOOPS.get(route) or LOT_WPS
            i = int(getattr(car, 'wp', 0)) % len(wps)
            tx, tz = wps[i]
            dx, dz = tx - car.x, tz - car.z
            if math.hypot(dx, dz) < 2.0:
                i = (i + 1) % len(wps)
                car.wp = i
                tx, tz = wps[i]
                dx, dz = tx - car.x, tz - car.z
            sharp = _turn_toward(car, math.degrees(math.atan2(dx, dz)), dt)
            moving_speed = cruise * (0.54 if sharp > 0.82 else 1.0)
            try:
                car.position += car.forward * moving_speed * dt
            except Exception:
                rad = math.radians(car.rotation_y)
                car.x += math.sin(rad) * moving_speed * dt
                car.z += math.cos(rad) * moving_speed * dt
            car.y = 0
