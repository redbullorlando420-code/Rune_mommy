"""Lot crowd for Rune Mommy — cube humanoids, wander / run crazy / panic.

Named NPCs (Mira, Gage, Michelle) live in game.py and are NOT in this loot crowd.
"""
from __future__ import annotations

import math
import random

from lighting import should_sim, set_visible, CULL_PED

PED_COUNT = 52

CIVILIAN_SHIRTS = (
    (255, 90, 180),
    (90, 220, 255),
    (255, 210, 60),
    (190, 90, 255),
    (255, 120, 80),
    (80, 255, 190),
    (255, 160, 210),
    (120, 180, 255),
    (255, 80, 140),
    (70, 230, 210),
)

LOT_RAT_SHIRTS = (
    (110, 70, 90),
    (80, 62, 72),
    (140, 88, 100),
    (70, 55, 68),
)


def _atan_yaw(dx, dz):
    return math.degrees(math.atan2(dx, dz))


def _role_mix(i):
    if i < 20:
        return 'civilian'
    if i < 32:
        return 'lot_rat'
    if i < 42:
        return 'walker'
    return 'thug'


def _spot(i, rng):
    band = i % 5
    if band == 0:
        return rng.uniform(-22, 26), rng.uniform(-7.5, 3.5)
    if band == 1:
        return rng.uniform(-38, 40), rng.choice((-10.6, -21.4)) + rng.uniform(-0.4, 0.4)
    if band == 2:
        return rng.uniform(-30, 34), rng.uniform(-40, -26)
    if band == 3:
        return rng.uniform(-36, 38), rng.uniform(2.5, 9.0)
    return rng.uniform(-16, 20), rng.uniform(-20, -6)


def spawn_crowd(game):
    """Spawn 50+ wanderers. Reuses game._humanoid. Does not touch named NPCs."""
    color = game.color
    rng = random.Random(50)
    walker_col = (74, 99, 80)
    thug_col = (193, 18, 31)
    if not hasattr(game, 'peds') or game.peds is None:
        game.peds = []
    for i in range(PED_COUNT):
        role = _role_mix(i)
        x, z = _spot(i, rng)
        run_crazy = (i % 5 != 0) and (role in ('civilian', 'lot_rat', 'thug') or rng.random() < 0.45)
        if role == 'civilian':
            rgb = CIVILIAN_SHIRTS[i % len(CIVILIAN_SHIRTS)]
            pants = color.rgb32(36, 24, 48)
            skin = color.rgb32(255, 200, 160)
            hp = rng.randint(18, 26)
            name = 'lot civilian'
            kind = 'civilian'
            walk = rng.uniform(1.3, 2.0)
        elif role == 'lot_rat':
            rgb = LOT_RAT_SHIRTS[i % len(LOT_RAT_SHIRTS)]
            pants = color.rgb32(28, 22, 26)
            skin = color.rgb32(230, 180, 140)
            hp = rng.randint(20, 30)
            name = 'lot rat'
            kind = 'lot_rat'
            walk = rng.uniform(1.6, 2.4)
        elif role == 'walker':
            rgb = walker_col
            pants = color.rgb32(24, 28, 26)
            skin = color.rgb32(170, 190, 150)
            hp = rng.randint(36, 54)
            name = 'Dusk Walker'
            kind = 'walker'
            walk = rng.uniform(0.9, 1.4)
            run_crazy = False
        else:
            rgb = thug_col
            pants = color.rgb32(20, 16, 18)
            skin = color.rgb32(220, 160, 120)
            hp = rng.randint(34, 50)
            name = 'Road Thug'
            kind = 'thug'
            walk = rng.uniform(2.0, 2.8)

        shirt = color.rgb32(*rgb)
        ped = game._humanoid(x, z, shirt=shirt, pants=pants, skin=skin, hitbox=True)
        ped.npc_id = f'ped_{i}'
        ped.npc_name = name
        ped.kind = kind
        ped.role = role
        ped.hp = hp
        ped.max_hp = hp
        ped.xp = 6 if role == 'civilian' else 10
        ped.hittable = True
        ped.heading = rng.uniform(0, 360)
        ped.rotation_y = ped.heading
        ped.wander_t = rng.uniform(0.2, 2.4)
        ped.walk_speed = walk
        ped.run_crazy = bool(run_crazy)
        ped.crazy_speed = rng.uniform(6.2, 8.8)
        ped.sprint_t = 0.0
        ped.melee_cd = 0.0
        ped.panic_speed = rng.uniform(7.6, 10.2) if run_crazy else rng.uniform(6.4, 8.4)
        game.peds.append(ped)
        game.npcs.append(ped)
        game.targets.append(ped)
    return len(game.peds)


def spawn_heat_hunter(game):
    """One extra aggressive walker. Cap is enforced by the caller."""
    color = game.color
    px = getattr(game.player, 'x', 0.0) if game.player else 0.0
    pz = getattr(game.player, 'z', -8.5) if game.player else -8.5
    ang = random.uniform(0, math.tau)
    x = max(-40, min(44, px + math.cos(ang) * 15.0))
    z = max(-44, min(12, pz + math.sin(ang) * 15.0))
    ped = game._humanoid(
        x, z,
        shirt=color.rgb32(90, 40, 70),
        pants=color.rgb32(20, 12, 24),
        skin=color.rgb32(180, 200, 160),
        hitbox=False,
    )
    ped.npc_id = f'heat_{len(getattr(game, "heat_hunters", []) or [])}'
    ped.npc_name = 'heat walker'
    ped.kind = 'heat_hunter'
    ped.role = 'thug'
    ped.hp = 44
    ped.max_hp = 44
    ped.xp = 12
    ped.hittable = True
    ped.heading = 0
    ped.wander_t = 0
    ped.walk_speed = 5.6
    ped.run_crazy = True
    ped.crazy_speed = 7.4
    ped.sprint_t = 0
    ped.melee_cd = 0.2
    ped.panic_speed = 8.2
    if not hasattr(game, 'heat_hunters') or game.heat_hunters is None:
        game.heat_hunters = []
    game.heat_hunters.append(ped)
    game.peds.append(ped)
    game.npcs.append(ped)
    game.targets.append(ped)
    if ped not in game.ignore:
        game.ignore.append(ped)
    return ped


def tick_crowd(game, dt):
    player = game.player
    if not player:
        return
    px, pz = player.x, player.z
    armed = bool(game.pistol_drawn or getattr(game, 'panic_t', 0) > 0)
    heat = getattr(game, 'heat', 0.0)
    opts = getattr(game, 'render_opts', None) or {}
    cull = float(opts.get('cull_ped', CULL_PED))
    for npc in game.peds:
        if not npc:
            continue
        if getattr(npc, 'enabled', True) is False:
            continue
        if getattr(npc, 'hp', 0) <= 0:
            continue
        role = getattr(npc, 'role', 'civilian')
        kind = getattr(npc, 'kind', '')
        dx = npc.x - px
        dz = npc.z - pz
        dist = math.hypot(dx, dz) or 0.01
        if dist > cull:
            set_visible(npc, False)
            continue
        set_visible(npc, True)

        speed = getattr(npc, 'walk_speed', 1.6)
        charging = False

        if kind == 'heat_hunter' and heat >= 1.6:
            npc.heading = _atan_yaw(px - npc.x, pz - npc.z)
            speed = 6.1
            charging = True
        elif armed and dist < 19.0:
            if role == 'thug' or kind in ('thug', 'heat_hunter'):
                npc.heading = _atan_yaw(px - npc.x, pz - npc.z)
                speed = 7.4
                charging = True
            else:
                npc.heading = _atan_yaw(dx, dz)
                speed = getattr(npc, 'panic_speed', 8.0)
        else:
            npc.wander_t = getattr(npc, 'wander_t', 0.0) - dt
            npc.sprint_t = max(0.0, getattr(npc, 'sprint_t', 0.0) - dt)
            if npc.wander_t <= 0:
                if getattr(npc, 'run_crazy', False):
                    npc.heading = random.uniform(0, 360)
                    npc.wander_t = random.uniform(0.28, 1.05)
                    if random.random() < 0.28:
                        npc.heading = _atan_yaw(random.uniform(-10, 12) - npc.x, -16.0 - npc.z)
                        npc.sprint_t = random.uniform(0.7, 1.9)
                else:
                    npc.heading = random.uniform(0, 360)
                    npc.wander_t = random.uniform(1.5, 3.2)
            if getattr(npc, 'run_crazy', False):
                speed = 8.4 if npc.sprint_t > 0 else getattr(npc, 'crazy_speed', 6.6)

        npc.rotation_y = npc.heading
        try:
            step = npc.forward * speed * dt
            npc.position += step
        except Exception:
            rad = math.radians(npc.heading)
            npc.x += math.sin(rad) * speed * dt
            npc.z += math.cos(rad) * speed * dt
        npc.y = 0
        npc.x = max(-46, min(50, npc.x))
        npc.z = max(-50, min(16, npc.z))

        if charging and dist < 1.45 and hasattr(game, '_hurt'):
            npc.melee_cd = getattr(npc, 'melee_cd', 0.0) - dt
            if npc.melee_cd <= 0:
                npc.melee_cd = 0.72
                game._hurt(7)
