"""Lot crowd for Rune Mommy — procedural multi-part humanoids, wander / run crazy / panic.

Named NPCs (Mira, Gage, Michelle) live in game.py and are NOT in this loot crowd.
Pathing stays on sidewalks / lots — never camps on Hwy 50 asphalt.
"""
from __future__ import annotations

import math
import random

from lighting import should_sim, set_visible, set_lod, CULL_PED

PED_COUNT = 80

# Hwy 50 asphalt Y-band corridor (traffic lanes ≈ -14.15 east / -17.85 west).
# Sidewalks sit near z≈-10.6 (north) and z≈-21.4 (south).
HWY_Z_LO = -19.5
HWY_Z_HI = -12.5
# Secondary asphalt strips (gas apron / plaza drive) — soft avoid
LOT_DRIVE_BANDS = (
    # (z_lo, z_hi, x_lo, x_hi) — empty x range = full
    (-16.5, -13.5, None, None),  # main hwy core
)

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

# Crowd talk lines — variety beyond Michelle
CROWD_LINES = (
    "You seen the Cool Down line? Mira's slamming them tonight.",
    "Don't stand in the road — Hwy 50 cooks rubber and tourists.",
    "Heat's up. Keep your pistol low if you got one.",
    "Walmart's still open east. Carts scream like dying birds.",
    "Club 27 cover's twenty. Or a smile, if Nova likes you.",
    "Quiet Spa's the only soft light on this strip.",
    "Tire shop by Hancock — Rico'll tell you your grip's trash.",
    "GameStop tried to sell me PowerUp again. I walked.",
    "Best Buy open-box earbuds. One side's a rumor.",
    "Pet store goldfish look judgmental. Same.",
    "Gage only takes gold. Don't argue with the plank.",
    "Michelle's on Sanctuary. Don't deadname. Don't stare.",
    "Lot rats run crazy after dark. I'm not one. Today.",
    "Food truck cuban's the real dinner. Neon shakes are dessert.",
    "Akihabara portal's by the pink torii — if you trust pink.",
    "Parking stalls fill fast. Don't block the paint.",
    "Gators in the lake. Don't wade drunk.",
    "I'm just walking the sidewalk. Asphalt's for cars.",
    "You smell like gas station coffee and bad decisions.",
    "Keep moving. Standing still gets you heat.",
)


def is_on_road(x, z) -> bool:
    """True if xz sits on Hwy 50 asphalt corridor (avoid for foot traffic)."""
    try:
        z = float(z)
        x = float(x)
    except Exception:
        return False
    if HWY_Z_LO <= z <= HWY_Z_HI:
        # Allow extreme east/west shoulder beyond map retail (still road though)
        return True
    return False


def nearest_sidewalk_z(z) -> float:
    """Snap toward nearest sidewalk / lot band off the hwy asphalt."""
    z = float(z)
    north = -10.6
    south = -21.4
    if abs(z - north) <= abs(z - south):
        return north
    return south


def steer_off_road(ent, dt=0.016):
    """If ent is on road asphalt, nudge toward nearest sidewalk and re-aim heading."""
    if not ent:
        return False
    try:
        x, z = float(ent.x), float(ent.z)
    except Exception:
        return False
    if not is_on_road(x, z):
        return False
    target_z = nearest_sidewalk_z(z)
    dz = target_z - z
    # Push off-road quickly
    step = max(2.8, abs(dz) * 3.0) * float(dt)
    if dz > 0:
        ent.z = min(target_z, z + step)
    else:
        ent.z = max(target_z, z - step)
    # Face off the road
    try:
        ent.heading = 0.0 if dz > 0 else 180.0
        ent.rotation_y = ent.heading
    except Exception:
        pass
    # Soft x drift toward lot center if deep in corridor
    try:
        if abs(ent.z - target_z) > 0.4:
            ent.x += (0.0 - float(ent.x)) * min(0.4, 1.5 * float(dt))
    except Exception:
        pass
    return True


def clamp_destination(x, z):
    """Rewrite a path target off the hwy asphalt onto sidewalk/lot."""
    x, z = float(x), float(z)
    if is_on_road(x, z):
        z = nearest_sidewalk_z(z)
    # Prefer lot / sidewalk bands
    if -19.0 < z < -12.8:
        z = nearest_sidewalk_z(z)
    return x, z


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
    """Spawn on sidewalks / lots — never on hwy asphalt Y-band."""
    band = i % 5
    if band == 0:
        return rng.uniform(-22, 26), rng.uniform(-7.5, 3.5)
    if band == 1:
        # north / south sidewalks along Hwy 50
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
        x, z = clamp_destination(x, z)
        run_crazy = (i % 5 != 0) and (role in ('civilian', 'lot_rat', 'thug') or rng.random() < 0.45)
        if role == 'civilian':
            rgb = CIVILIAN_SHIRTS[i % len(CIVILIAN_SHIRTS)]
            pants = color.rgb32(36 + (i * 7) % 40, 24 + (i * 3) % 28, 48 + (i * 5) % 36)
            skin = color.rgb32(255, 200, 160)
            hp = rng.randint(18, 26)
            name = 'lot civilian'
            kind = 'civilian'
            walk = rng.uniform(1.3, 2.0)
        elif role == 'lot_rat':
            rgb = LOT_RAT_SHIRTS[i % len(LOT_RAT_SHIRTS)]
            pants = color.rgb32(28 + (i * 5) % 24, 22 + (i * 3) % 18, 26 + (i * 4) % 20)
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
        # Adult feminine anime for civilian / lot_rat; male thug/walker stay utilitarian
        fem = role in ('civilian', 'lot_rat')
        style = 'anime_f' if fem else None
        detail = 'anime_f' if fem else 'crowd'
        ped = game._humanoid(x, z, shirt=shirt, pants=pants, skin=skin, hitbox=True, detail=detail, style=style)
        ped.npc_id = f'ped_{i}'
        ped.npc_name = name
        ped.kind = kind
        ped.role = role
        ped.feminine = fem
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
        ped.line = CROWD_LINES[i % len(CROWD_LINES)]
        ped.talkable = True
        ped.ai_accum = rng.uniform(0, 1)
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
    x, z = clamp_destination(x, z)
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
    ped.line = "Heat's on you. Run or draw."
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
    lod_near = float(opts.get('lod_ped_near', 22.0))
    lod_mid = float(opts.get('lod_ped_mid', 36.0))
    far_interval = max(1, int(opts.get('ai_far_interval', 3)))
    # frame counter for far-AI throttle
    game._crowd_frame = int(getattr(game, '_crowd_frame', 0)) + 1
    frame = game._crowd_frame

    for idx, npc in enumerate(game.peds):
        if not npc:
            continue
        if getattr(npc, 'enabled', True) is False:
            continue
        if getattr(npc, 'hp', 0) <= 0:
            continue
        if getattr(npc, 'district', None) == 'akihabara':
            continue
        if getattr(npc, 'driving', False):
            continue
        role = getattr(npc, 'role', 'civilian')
        kind = getattr(npc, 'kind', '')
        dx = npc.x - px
        dz = npc.z - pz
        dist = math.hypot(dx, dz) or 0.01
        if dist > cull:
            set_visible(npc, False)
            continue

        # LOD + AI throttle
        if dist <= lod_near:
            set_lod(npc, 'near')
            do_ai = True
        elif dist <= lod_mid:
            set_lod(npc, 'mid')
            do_ai = ((frame + idx) % 2) == 0
        else:
            set_lod(npc, 'mid')
            do_ai = ((frame + idx) % far_interval) == 0

        if not do_ai:
            # Still peel off road even when AI throttled
            steer_off_road(npc, dt)
            continue

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
                        # Aim at sidewalk / lot — not hwy center
                        tx = random.uniform(-10, 12)
                        tz = random.choice((-10.6, -21.4, -6.0, 4.0))
                        npc.heading = _atan_yaw(tx - npc.x, tz - npc.z)
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

        # Peel off asphalt if we drifted onto Hwy 50
        if steer_off_road(npc, dt):
            pass
        npc.y = 0
        npc.x = max(-55, min(72, npc.x))
        npc.z = max(-55, min(22, npc.z))

        if charging and dist < 1.45 and hasattr(game, '_hurt'):
            npc.melee_cd = getattr(npc, 'melee_cd', 0.0) - dt
            if npc.melee_cd <= 0:
                npc.melee_cd = 0.72
                game._hurt(7)
