"""Florida wildlife: deep lakes + alligators (idle → chase → bite).

Lake is not a flat decal — surface + basin depth. Player y sinks while wading.
Gators are hittable targets; loot gator_meat / gator_hide on kill.
"""
from __future__ import annotations

import math
import random

from lighting import set_visible


# Unique lake surface Y (below sidewalk 0.07 / hwy 0.09, above void)
LAKE_SURFACE_Y = 0.015
LAKE_BED_Y = -1.35


def _rgb(color, r, g, b):
    return color.rgb32(r, g, b)


def build_lake(game, cx=16.0, cz=-42.0, radius=9.0):
    """Deep lake near waterfront / SE. Visual depth: darker center, lighter rim."""
    Entity = game.Entity
    color = game.color
    parts = []
    # Basin walls (submerged ring)
    parts.append(Entity(
        model='cube',
        scale=(radius * 2.2, 1.4, radius * 2.2),
        position=(cx, LAKE_BED_Y + 0.7, cz),
        color=_rgb(color, 24, 48, 40),
        collider='box',
    ))
    # Soft disable collider on basin so player can enter — use trigger only
    try:
        parts[-1].collider = None
    except Exception:
        pass

    # Deep center water (darker)
    water_tex = None
    try:
        water_tex = (getattr(game, 'world_textures', {}) or {}).get('water')
    except Exception:
        water_tex = None
    deep = Entity(
        model='cube',
        scale=(radius * 1.1, 0.08, radius * 1.1),
        position=(cx, LAKE_SURFACE_Y - 0.02, cz),
        color=_rgb(color, 20, 70, 110),
        texture=water_tex,
        texture_scale=(4, 4),
    )
    parts.append(deep)
    # Mid ring
    mid = Entity(
        model='cube',
        scale=(radius * 1.6, 0.06, radius * 1.6),
        position=(cx, LAKE_SURFACE_Y, cz),
        color=_rgb(color, 40, 120, 160),
        texture=water_tex,
        texture_scale=(5, 5),
    )
    parts.append(mid)
    # Rim / shallows (lighter)
    rim = Entity(
        model='cube',
        scale=(radius * 2.0, 0.05, radius * 2.0),
        position=(cx, LAKE_SURFACE_Y + 0.01, cz),
        color=_rgb(color, 70, 160, 180),
        texture=water_tex,
        texture_scale=(6, 6),
    )
    parts.append(rim)
    # Reed props
    for i in range(8):
        ang = i * (math.pi * 2 / 8)
        rx = cx + math.cos(ang) * (radius * 0.95)
        rz = cz + math.sin(ang) * (radius * 0.95)
        parts.append(Entity(model='cube', scale=(0.12, 1.1, 0.12),
                            position=(rx, 0.55, rz), color=_rgb(color, 40, 90, 40)))

    lake = {
        'pos': (cx, 0.0, cz),
        'radius': radius,
        'deep_radius': radius * 0.45,
        'surface_y': LAKE_SURFACE_Y,
        'bed_y': LAKE_BED_Y,
        'parts': parts,
    }
    if not hasattr(game, 'lakes') or game.lakes is None:
        game.lakes = []
    game.lakes.append(lake)
    return lake


def _make_gator(game, x, z):
    Entity = game.Entity
    color = game.color
    body = Entity(
        model='cube',
        scale=(1.8, 0.35, 0.7),
        position=(x, 0.2, z),
        color=_rgb(color, 50, 90, 45),
        collider='box',
    )
    snout = Entity(parent=body, model='cube', scale=(0.55, 0.22, 0.35),
                   position=(0.85, 0.0, 0), color=_rgb(color, 45, 80, 40))
    tail = Entity(parent=body, model='cube', scale=(0.7, 0.18, 0.25),
                  position=(-0.95, -0.02, 0), color=_rgb(color, 40, 75, 38))
    for dx in (-0.4, 0.2):
        Entity(parent=body, model='cube', scale=(0.25, 0.12, 0.55),
               position=(dx, -0.12, 0.35), color=_rgb(color, 40, 70, 35))
        Entity(parent=body, model='cube', scale=(0.25, 0.12, 0.55),
               position=(dx, -0.12, -0.35), color=_rgb(color, 40, 70, 35))
    # eyes
    Entity(parent=body, model='sphere', scale=0.12, position=(0.55, 0.18, 0.18),
           color=_rgb(color, 220, 200, 40))
    Entity(parent=body, model='sphere', scale=0.12, position=(0.55, 0.18, -0.18),
           color=_rgb(color, 220, 200, 40))

    body.npc_id = f'gator_{len(getattr(game, "gators", []) or [])}'
    body.npc_name = 'alligator'
    body.kind = 'gator'
    body.hittable = True
    body.hp = 40
    body.max_hp = 40
    body.xp = 14
    body.gator_state = 'idle'
    body.bite_cd = 0.0
    body.home = (x, z)
    body.wander_t = random.uniform(0.5, 2.0)
    body.heading = random.uniform(0, 360)
    body.walk_speed = 1.2
    body.chase_speed = 4.2
    body.aggro_r = 9.0
    body.leash_r = 18.0
    return body


def spawn_gators(game, lake, count=5):
    cx, _, cz = lake['pos']
    r = lake['radius'] * 0.85
    if not hasattr(game, 'gators') or game.gators is None:
        game.gators = []
    for i in range(count):
        ang = random.uniform(0, math.tau)
        rad = random.uniform(r * 0.35, r)
        x = cx + math.cos(ang) * rad
        z = cz + math.sin(ang) * rad
        g = _make_gator(game, x, z)
        game.gators.append(g)
        if hasattr(game, 'targets'):
            game.targets.append(g)
        if hasattr(game, 'npcs'):
            # not talkable — combat only
            pass
    print('  gators: %d near lake' % len(game.gators))


def build_florida_water(game):
    """Primary deep lake + gators. Optional small pond west."""
    main = build_lake(game, cx=16.0, cz=-42.0, radius=9.0)
    spawn_gators(game, main, count=5)
    # smaller pond NW of sanctuary for densify / ambiance
    pond = build_lake(game, cx=-44.0, cz=2.0, radius=4.5)
    spawn_gators(game, pond, count=2)


def lake_depth_at(game, x, z):
    """Return (in_water: bool, target_y: float, deep: bool)."""
    for lake in getattr(game, 'lakes', []) or []:
        cx, _, cz = lake['pos']
        dist = math.hypot(x - cx, z - cz)
        if dist <= lake['radius']:
            if dist <= lake['deep_radius']:
                # deep swim — sink more
                return True, -0.85, True
            # wade
            t = dist / lake['radius']
            y = -0.15 - (1.0 - t) * 0.55
            return True, y, False
    return False, 0.0, False


def apply_player_water(game):
    """Call from walk after gravity — sink player in lakes."""
    player = getattr(game, 'player', None)
    if not player or getattr(game, 'in_car', None):
        return
    if getattr(game, 'active_interior', None):
        return
    in_water, ty, deep = lake_depth_at(game, float(player.x), float(player.z))
    game.in_water = in_water
    game.in_deep_water = deep
    if in_water:
        # blend toward water depth
        try:
            cur = float(player.y)
            player.y = cur * 0.7 + ty * 0.3
            if hasattr(game, 'y_vel'):
                game.y_vel = min(game.y_vel, 0.0)
            if deep and random.random() < 0.01:
                game.toast('Deep water — watch for gators.')
        except Exception:
            pass


def _atan_yaw(dx, dz):
    return math.degrees(math.atan2(dx, dz))


def tick_gators(game, dt):
    player = getattr(game, 'player', None)
    if not player:
        return
    if getattr(game, 'mode', 'play') != 'play':
        return
    px, pz = float(player.x), float(player.z)
    for g in list(getattr(game, 'gators', []) or []):
        if not g or getattr(g, 'hp', 0) <= 0:
            continue
        dx = g.x - px
        dz = g.z - pz
        dist = math.hypot(dx, dz) or 0.01
        if dist > 55:
            set_visible(g, False)
            continue
        set_visible(g, True)

        state = getattr(g, 'gator_state', 'idle')
        g.bite_cd = max(0.0, getattr(g, 'bite_cd', 0.0) - dt)

        if dist < g.aggro_r and (getattr(game, 'in_water', False) or dist < 6.0):
            state = 'chase'
        elif dist > g.leash_r:
            state = 'idle'
        g.gator_state = state

        if state == 'chase':
            g.heading = _atan_yaw(px - g.x, pz - g.z)
            speed = g.chase_speed
        else:
            g.wander_t = getattr(g, 'wander_t', 0.0) - dt
            if g.wander_t <= 0:
                hx, hz = g.home
                g.heading = _atan_yaw(
                    hx + random.uniform(-3, 3) - g.x,
                    hz + random.uniform(-3, 3) - g.z,
                )
                g.wander_t = random.uniform(1.2, 3.0)
            speed = g.walk_speed

        g.rotation_y = g.heading
        rad = math.radians(g.heading)
        g.x += math.sin(rad) * speed * dt
        g.z += math.cos(rad) * speed * dt
        # keep near home leash
        hx, hz = g.home
        if math.hypot(g.x - hx, g.z - hz) > g.leash_r:
            g.heading = _atan_yaw(hx - g.x, hz - g.z)
        # float on water surface-ish
        in_w, ty, _deep = lake_depth_at(game, g.x, g.z)
        g.y = (ty + 0.25) if in_w else 0.15

        if state == 'chase' and dist < 1.6 and g.bite_cd <= 0:
            g.bite_cd = 1.1
            if hasattr(game, '_hurt'):
                game._hurt(11)
            game.toast('Alligator bite!')


def on_gator_killed(game, gator):
    """Loot hook — call from shoot kill path when kind==gator."""
    from random import random as _r
    loot_name = 'Gator Meat'
    if _r() < 0.45:
        loot_name = 'Gator Hide'
        game.pack.append('Gator Hide')
        # also try item id form
    else:
        game.pack.append('Gator Meat')
    # gold already granted by shoot kill path
    game.toast(f'Alligator down. Looted {loot_name}.')
