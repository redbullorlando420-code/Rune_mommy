"""Car crash / destruction helpers — impulse, damage, smoke, cheap debris.

Cheap continuous physics only: cooldown-gated impacts, capped debris cubes,
far FX cull. Does not replace vendor.bicycle_step / _bicycle_step_safe.
"""
from __future__ import annotations

import math
import random

MAX_DEBRIS = 18
CULL_FX = 42.0
IMPACT_CD = 0.28
DEBRIS_LIFE = 1.35


def _dist2(ax, az, bx, bz):
    dx = ax - bx
    dz = az - bz
    return dx * dx + dz * dz


def ensure_pools(game):
    if not hasattr(game, 'debris') or game.debris is None:
        game.debris = []
    if not hasattr(game, '_debris_budget'):
        game._debris_budget = MAX_DEBRIS


def apply_impulse_xz(car, ix, iz, yaw_kick=0.0):
    """Nudge position + optional yaw; store residual speed along impulse."""
    if car is None:
        return
    try:
        car.x = float(car.x) + float(ix)
        car.z = float(car.z) + float(iz)
    except Exception:
        return
    if abs(yaw_kick) > 1e-4:
        try:
            car.rotation_y = float(car.rotation_y) + float(yaw_kick)
        except Exception:
            pass
    # Convert leftover impulse into speed along car forward (rough)
    try:
        rad = math.radians(float(car.rotation_y))
        along = float(ix) * math.sin(rad) + float(iz) * math.cos(rad)
        car.speed = float(getattr(car, 'speed', 0.0) or 0.0) + along * 8.0
        # Cap residual so AI / player stay sane
        vmax = 22.0
        car.speed = max(-vmax * 0.35, min(vmax, car.speed))
    except Exception:
        pass


def take_damage(game, car, impact_speed, *, source='world'):
    """Accumulate damage; disable + toast + sfx at 100. Returns True if applied."""
    if car is None:
        return False
    # Cooldown — avoid per-frame shredding while lodged in a wall
    cd = float(getattr(car, 'impact_cd', 0.0) or 0.0)
    if cd > 0.0:
        return False
    spd = abs(float(impact_speed))
    if spd < 1.8 and source != 'ram':
        return False
    car.impact_cd = IMPACT_CD
    add = min(48.0, max(4.0, spd * 2.6))
    if source == 'car':
        add *= 1.15
    elif source == 'ram':
        add *= 0.85
    before = float(getattr(car, 'damage', 0.0) or 0.0)
    car.damage = min(100.0, before + add)
    try:
        import sfx
        sfx.impact(spd)
    except Exception:
        pass
    if car.damage >= 100.0 and not getattr(car, 'disabled', False):
        car.disabled = True
        car.speed = 0.0
        try:
            import sfx
            sfx.disable_crunch()
        except Exception:
            pass
        if game is not None and getattr(game, 'in_car', None) is car:
            try:
                game.toast('Car totaled.')
            except Exception:
                pass
        # Burst debris on total
        try:
            spawn_debris(game, float(car.x), float(car.z), count=6, speed=spd)
        except Exception:
            pass
    elif spd >= 8.0:
        try:
            spawn_debris(game, float(car.x), float(car.z), count=3, speed=spd)
        except Exception:
            pass
    return True


def resolve_player_hit(game, car, *, hit_world, hit_other, impact_speed, nx, nz, nspd, nyaw):
    """Resolve a proposed bicycle step that collided. Returns (nx, nz, nyaw, nspd)."""
    ensure_pools(game)
    spd = abs(float(impact_speed))
    other = hit_other

    if other is not None:
        # Car-vs-car: mutual impulse along separation
        ox = float(getattr(other, 'x', nx))
        oz = float(getattr(other, 'z', nz))
        dx = float(nx) - ox
        dz = float(nz) - oz
        d = math.hypot(dx, dz) or 1.0
        ux, uz = dx / d, dz / d
        # Push apart proportional to impact
        push = min(1.4, 0.35 + spd * 0.06)
        apply_impulse_xz(other, -ux * push * 0.55, -uz * push * 0.55, yaw_kick=random.uniform(-8, 8) * min(1.0, spd / 16.0))
        # Player car: bounce back + reverse fraction of speed
        bounce = min(0.9, 0.25 + spd * 0.02)
        nx = float(car.x) + ux * bounce * 0.4
        nz = float(car.z) + uz * bounce * 0.4
        nspd = -abs(float(nspd)) * (0.22 + min(0.28, spd / 40.0))
        nyaw = float(nyaw) + random.uniform(-4, 4) * min(1.0, spd / 14.0)
        take_damage(game, car, spd, source='car')
        # Traffic / parked also take damage (player ram)
        take_damage(game, other, spd * 0.9, source='ram')
        # Wake parked → slight unpark wobble only (do not steal traffic route)
        if getattr(other, 'parked', False) and not getattr(other, 'traffic', False):
            other.parked = False
        return nx, nz, nyaw, nspd

    if hit_world:
        # World hit: stay mostly put, reverse speed, small yaw kick
        take_damage(game, car, spd, source='world')
        nspd = -abs(float(nspd)) * (0.18 + min(0.25, spd / 45.0))
        nyaw = float(car.rotation_y) + random.uniform(-6, 6) * min(1.0, spd / 12.0)
        # Tiny separation along travel so we don't stick
        try:
            rad = math.radians(float(car.rotation_y))
            nx = float(car.x) - math.sin(rad) * 0.15
            nz = float(car.z) - math.cos(rad) * 0.15
        except Exception:
            nx, nz = float(car.x), float(car.z)
        return nx, nz, nyaw, nspd

    return nx, nz, nyaw, nspd


def spawn_debris(game, x, z, count=3, speed=10.0):
    ensure_pools(game)
    if game is None:
        return
    # Cull far from player
    player = getattr(game, 'player', None)
    if player is not None:
        if _dist2(x, z, float(player.x), float(player.z)) > (CULL_FX + 8) ** 2:
            return
    try:
        from ursina import Entity, color, Vec3
    except Exception:
        return
    living = [d for d in game.debris if d is not None and getattr(d, 'enabled', True)]
    game.debris = living
    budget = max(0, int(getattr(game, '_debris_budget', MAX_DEBRIS)) - len(living))
    n = min(int(count), budget, 6)
    if n <= 0:
        # Recycle oldest
        while len(game.debris) >= MAX_DEBRIS and game.debris:
            old = game.debris.pop(0)
            try:
                from ursina import destroy
                destroy(old)
            except Exception:
                try:
                    old.enabled = False
                except Exception:
                    pass
        budget = max(0, MAX_DEBRIS - len(game.debris))
        n = min(int(count), budget, 4)
    if n <= 0:
        return
    col = color.rgb32(90, 90, 95)
    try:
        base = getattr(game, 'color', None)
        if base is not None:
            col = base.rgb32(70 + random.randint(0, 40), 70, 75)
    except Exception:
        pass
    for _ in range(n):
        ang = random.uniform(0, 6.283)
        dist = random.uniform(0.4, 1.1)
        ent = Entity(
            model='cube',
            color=col,
            scale=random.uniform(0.08, 0.18),
            position=(x + math.cos(ang) * dist, 0.35, z + math.sin(ang) * dist),
            collider=None,
        )
        ent._debris = True
        ent._life = DEBRIS_LIFE * random.uniform(0.75, 1.15)
        ent._vx = math.cos(ang) * (1.5 + speed * 0.08) * random.uniform(0.6, 1.2)
        ent._vz = math.sin(ang) * (1.5 + speed * 0.08) * random.uniform(0.6, 1.2)
        ent._vy = random.uniform(1.2, 2.8)
        game.debris.append(ent)


def tick_fx(game, dt):
    """Advance debris + impact cooldowns; cull far crash FX. Call from tick."""
    ensure_pools(game)
    dt = float(dt)
    player = getattr(game, 'player', None)
    px = float(getattr(player, 'x', 0.0) or 0.0) if player else 0.0
    pz = float(getattr(player, 'z', 0.0) or 0.0) if player else 0.0

    # Cooldowns on cars
    for car in list(getattr(game, 'cars', None) or []):
        if not car:
            continue
        cd = float(getattr(car, 'impact_cd', 0.0) or 0.0)
        if cd > 0.0:
            car.impact_cd = max(0.0, cd - dt)

    alive = []
    for ent in list(game.debris):
        if ent is None:
            continue
        try:
            ent._life = float(getattr(ent, '_life', 0.0)) - dt
            if ent._life <= 0.0:
                raise RuntimeError('expire')
            if player and _dist2(float(ent.x), float(ent.z), px, pz) > CULL_FX * CULL_FX:
                raise RuntimeError('far')
            ent.x += float(getattr(ent, '_vx', 0.0)) * dt
            ent.z += float(getattr(ent, '_vz', 0.0)) * dt
            ent._vy = float(getattr(ent, '_vy', 0.0)) - 9.0 * dt
            ent.y += float(ent._vy) * dt
            if ent.y < 0.05:
                ent.y = 0.05
                ent._vy *= -0.25
                ent._vx *= 0.7
                ent._vz *= 0.7
            # Shrink near end of life
            if ent._life < 0.35:
                s = max(0.02, float(ent.scale_x) * (1.0 - 2.5 * dt))
                ent.scale = s
            alive.append(ent)
        except Exception:
            try:
                from ursina import destroy
                destroy(ent)
            except Exception:
                try:
                    ent.enabled = False
                except Exception:
                    pass
    game.debris = alive


def update_damage_visual(game, car, dt=0.016):
    """Paint darken + capped smoke puffs. Safe no-op if meshes missing."""
    if car is None:
        return
    dmg = float(getattr(car, 'damage', 0.0) or 0.0)
    base = getattr(car, 'base_paint', None) or getattr(car, 'paint', None)
    if base is not None and getattr(car, 'body', None):
        t = min(1.0, dmg / 100.0)
        try:
            if hasattr(base, 'r'):
                r = int(base.r * 255 * (1 - 0.55 * t) + 180 * t)
                g = int(base.g * 255 * (1 - 0.75 * t) + 30 * t)
                b = int(base.b * 255 * (1 - 0.75 * t) + 25 * t)
                col_fn = getattr(game, 'color', None)
                if col_fn is not None:
                    col = col_fn.rgb32(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
                else:
                    from ursina import color as ucolor
                    col = ucolor.rgb32(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            else:
                col = base.tint(-0.55 * t) if hasattr(base, 'tint') else base
            car.body.color = col
            cabin = getattr(car, 'cabin', None)
            if cabin is not None:
                cabin.color = col.tint(-0.15) if hasattr(col, 'tint') else col
        except Exception:
            pass

    # Smoke — only near player, rate-limited
    car.smoke_cd = max(0.0, float(getattr(car, 'smoke_cd', 0.0) or 0.0) - dt)
    if dmg < 55.0:
        return
    player = getattr(game, 'player', None) if game else None
    if player is not None:
        if _dist2(float(car.x), float(car.z), float(player.x), float(player.z)) > CULL_FX * CULL_FX:
            return
    if car.smoke_cd > 0.0:
        return
    if random.random() > min(0.4, dt * 5.0):
        return
    car.smoke_cd = 0.20 if dmg < 85 else 0.12
    try:
        from ursina import Entity, destroy
        col_fn = getattr(game, 'color', None)
        smoke_c = col_fn.rgb32(30, 30, 32) if col_fn else None
        if smoke_c is None:
            from ursina import color as ucolor
            smoke_c = ucolor.rgb32(30, 30, 32)
        smoke = Entity(
            model='cube',
            color=smoke_c,
            scale=0.16 + 0.08 * (dmg / 100.0),
            position=(
                float(car.x) + random.uniform(-0.35, 0.35),
                1.15,
                float(car.z) + random.uniform(-0.35, 0.35),
            ),
            collider=None,
        )
        try:
            smoke.animate_y(smoke.y + 1.5, duration=0.65)
            smoke.animate_scale(0.03, duration=0.65)
        except Exception:
            pass
        destroy(smoke, delay=0.7)
    except Exception:
        pass
