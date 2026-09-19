"""Lightweight schedule / FSM life-sim for Michelle, named NPCs, and a crowd subset.

States: home | work | shop | wander | talkable
Clock: in-game minutes advanced from real dt (accelerated).
Dialogue (E) can mention current state via state_line().
"""
from __future__ import annotations

import math
import random
from typing import Any

from lighting import set_visible
from vendor.fsm import FSM
from crowd import is_on_road, steer_off_road, clamp_destination, CROWD_LINES

# Accelerated clock: 1 real second ~= 45 in-game seconds
CLOCK_SCALE = 45.0

# Michelle never given a last name / deadname. First name only.
MICHELLE_SCHEDULE = (
    # (start_hour inclusive, end_hour exclusive, state, x, z, line)
    (0, 7, 'home', -27.9, 12.0, "Michelle yawns in the doorway, still half in last night."),
    (7, 10, 'home', -27.9, 12.0, "Michelle's at Sanctuary Drive — coffee breath and that teal dress."),
    (10, 14, 'shop', 0.0, -4.5, "Michelle's grabbing a Cool Down from Mira's neon hut. Don't stare."),
    (14, 18, 'wander', -18.0, -8.0, "Michelle's walking the Hwy 50 sidewalk like she owns the heat."),
    (18, 22, 'home', -27.9, 12.0, "Michelle's back at Sanctuary. Door cracked. Waiting."),
    (22, 24, 'home', -27.9, 12.0, "Late. Michelle's porch light is the only soft thing on the block."),
)

NAMED_SCHEDULES = {
    'mira': (
        (0, 9, 'home', 0.0, -2.6, "Mira's prepping the shake bar — neon still warming up."),
        (9, 22, 'work', 0.0, -2.6, "Mira's on the Cool Down counter. Line's moving."),
        (22, 24, 'home', 0.0, -2.6, "Mira wiped the stainless. She's winding down."),
    ),
    'gage': (
        (0, 10, 'home', 36.0, 2.2, "Gage is counting cash in the Gun Hut dark."),
        (10, 20, 'work', 36.0, 2.2, "Gage leans on the plank. Cash only."),
        (20, 24, 'wander', 30.0, -6.0, "Gage took a smoke walk toward the lot."),
    ),
    'club27_host': (
        (0, 16, 'home', 40.0, -22.0, "Nova's still off. Club 27 doors look locked from here."),
        (16, 24, 'work', 40.0, -24.5, "Nova's on the Club 27 rope. Cover's twenty — or a smile."),
    ),
    'quiet_spa_tech': (
        (0, 10, 'home', -36.0, -16.0, "Sori's Quiet Spa is dim. Towels stacked."),
        (10, 20, 'work', -36.0, -18.8, "Sori waves you in soft. Shoes off. Phone silent."),
        (20, 24, 'home', -36.0, -16.0, "Spa lights low. Sori's closing out."),
    ),
    'neighbor': (
        (0, 8, 'home', -40.0, 10.5, "Carol's blinds are shut on Sanctuary."),
        (8, 12, 'wander', -34.0, 8.0, "Carol's walking the cul-de-sac with a coffee."),
        (12, 18, 'shop', -20.0, -12.0, "Carol's on an errand toward the kiosk."),
        (18, 24, 'home', -40.0, 10.5, "Carol's back. Keep the music down after nine."),
    ),
    'rita': (
        (0, 7, 'home', 18.0, -13.0, "Rita's gas booth is dark."),
        (7, 21, 'work', 18.0, -13.0, "Rita at the pumps. Bring a car or don't."),
        (21, 24, 'home', 18.0, -13.0, "Rita closed the till. Lot lights only."),
    ),
}

STATE_VERBS = {
    'home': 'home',
    'work': 'working',
    'shop': 'out shopping',
    'wander': 'wandering',
    'talkable': 'hanging around',
}


def _hour_float(game) -> float:
    mins = float(getattr(game, 'life_sim_minutes', 10 * 60.0))  # default 10:00
    return (mins / 60.0) % 24.0


def clock_label(game) -> str:
    h = _hour_float(game)
    hh = int(h) % 24
    mm = int((h - int(h)) * 60) % 60
    return f'{hh:02d}:{mm:02d}'


def _pick_slot(schedule, hour: float):
    for start, end, state, x, z, line in schedule:
        if start <= hour < end:
            return state, x, z, line
    # fallback last
    row = schedule[-1]
    return row[2], row[3], row[4], row[5]


def _move_toward(ent, tx, tz, speed, dt):
    tx, tz = clamp_destination(tx, tz)
    # If currently on asphalt, prioritize sidewalk peel
    try:
        if is_on_road(ent.x, ent.z):
            steer_off_road(ent, dt)
            return False
    except Exception:
        pass
    dx = tx - float(ent.x)
    dz = tz - float(ent.z)
    dist = math.hypot(dx, dz)
    if dist < 0.35:
        try:
            ent.x, ent.z = tx, tz
        except Exception:
            pass
        return True
    step = min(speed * dt, dist)
    ent.x += dx / dist * step
    ent.z += dz / dist * step
    try:
        ent.rotation_y = math.degrees(math.atan2(dx, dz))
    except Exception:
        pass
    try:
        if is_on_road(ent.x, ent.z):
            steer_off_road(ent, dt)
    except Exception:
        pass
    return False


def state_line(ent) -> str | None:
    line = getattr(ent, 'life_line', None)
    state = getattr(ent, 'life_state', None)
    if line:
        return line
    if state:
        name = getattr(ent, 'npc_name', 'They')
        return f"{name} is {STATE_VERBS.get(state, state)}."
    return None


def _ensure_fsm(ent, initial='wander'):
    fsm = getattr(ent, 'life_fsm', None)
    if fsm is not None:
        return fsm
    fsm = FSM(initial)

    def _noop_enter():
        pass

    for st in ('home', 'work', 'shop', 'wander', 'talkable'):
        fsm.add(st, on_enter=_noop_enter, on_update=None, on_exit=None)
    try:
        fsm.set(initial)
    except Exception:
        pass
    ent.life_fsm = fsm
    return fsm


def boot(game):
    """Attach schedule brains after NPCs / crowd exist."""
    game.life_sim_minutes = float(getattr(game, 'life_sim_minutes', 10 * 60.0))
    game.life_sim_named = []
    michelle = getattr(game, 'michelle', None)
    if michelle:
        michelle.life_schedule = MICHELLE_SCHEDULE
        michelle.life_home = (-27.9, 12.0)
        michelle.talkable = True
        _ensure_fsm(michelle, 'home')
        game.life_sim_named.append(michelle)

    # Index npcs by id
    by_id = {}
    for npc in getattr(game, 'npcs', []) or []:
        nid = getattr(npc, 'npc_id', None) or getattr(npc, 'id', None)
        if nid:
            by_id[str(nid)] = npc

    for nid, sched in NAMED_SCHEDULES.items():
        npc = by_id.get(nid)
        if not npc:
            # soft alias: gage/gun hut npc
            if nid == 'gage':
                npc = next((n for n in (game.npcs or []) if getattr(n, 'kind', '') == 'gun'), None)
            elif nid == 'mira':
                npc = next((n for n in (game.npcs or []) if getattr(n, 'kind', '') == 'mira'), None)
        if not npc:
            continue
        npc.life_schedule = sched
        npc.talkable = True
        _ensure_fsm(npc, 'work')
        if npc not in game.life_sim_named:
            game.life_sim_named.append(npc)

    # Subset of crowd: every 4th ped gets a simple home/work/wander loop
    game.life_sim_crowd = []
    # Sidewalk / lot / plaza destinations across expanded Clermont (off hwy asphalt)
    anchors = [
        (-20.0, -10.0), (8.0, -12.0), (24.0, -8.0), (-8.0, 4.0),
        (16.0, -28.0), (-30.0, -20.0), (32.0, -20.0), (0.0, -30.0),
        (40.0, -20.0), (-36.0, -16.0), (36.0, 6.0), (16.0, -42.0),
        (62.0, -22.0), (-8.0, 6.5), (-20.0, -10.5), (30.0, -28.0),
        (18.0, -8.0), (8.0, 5.0), (-14.0, -28.0), (44.0, -8.0),
        (-22.0, 6.5), (8.0, 6.0), (28.0, 7.5), (42.0, -6.5),  # pet/gs/bb/tire
        (-48.0, -10.0), (-44.0, 6.0), (52.0, -8.0), (56.0, 4.0),
        (-10.0, -36.0), (20.0, -36.0), (48.0, -28.0), (-28.0, 8.0),
        (12.0, -10.6), (-24.0, -21.4), (34.0, -10.6), (-40.0, -21.4),
        (70.0, -12.0), (-52.0, -20.0), (4.0, 8.0), (-16.0, 8.0),
    ]
    for i, ped in enumerate(getattr(game, 'peds', []) or []):
        if i % 3 != 0:
            continue
        ax, az = anchors[i % len(anchors)]
        ax, az = clamp_destination(ax, az)
        ped.life_home = clamp_destination(ax + random.uniform(-2, 2), az + random.uniform(-2, 2))
        wx, wz = clamp_destination(random.uniform(-40, 55), random.choice((-10.6, -21.4, -6.0, 4.0, 7.0, -28.0)))
        ped.life_work = (wx, wz)
        sx, sz = clamp_destination(random.uniform(-24, 48), random.choice((-10.6, -8.0, 5.0, 6.5, -21.4)))
        line = CROWD_LINES[i % len(CROWD_LINES)]
        ped.life_schedule = (
            (0, 8, 'home', ped.life_home[0], ped.life_home[1], line),
            (8, 17, 'work', ped.life_work[0], ped.life_work[1], 'A local is on a shift errand.'),
            (17, 21, 'shop', sx, sz, 'A local ducks into a shop strip.'),
            (21, 24, 'wander', ped.life_home[0], ped.life_home[1], 'A local wanders the lot sidewalk.'),
        )
        ped.talkable = True
        ped.life_line = line
        if not getattr(ped, 'line', None):
            ped.line = line
        _ensure_fsm(ped, 'wander')
        # Make a few talkable for E
        if not getattr(ped, 'npc_name', None) or ped.npc_name in ('lot civilian', 'lot rat'):
            ped.npc_name = ped.npc_name or 'local'
        game.life_sim_crowd.append(ped)

    print('  life_sim: named=%d crowd_subset=%d' % (
        len(game.life_sim_named), len(game.life_sim_crowd)))


def tick(game, dt: float):
    if getattr(game, 'mode', 'play') != 'play':
        return
    if getattr(game, 'world_paused', False):
        return
    game.life_sim_minutes = float(getattr(game, 'life_sim_minutes', 10 * 60.0)) + dt * CLOCK_SCALE / 60.0
    # keep minutes bounded
    if game.life_sim_minutes > 24 * 60:
        game.life_sim_minutes %= (24 * 60)
    hour = _hour_float(game)

    player = getattr(game, 'player', None)
    px = float(getattr(player, 'x', 0.0)) if player else 0.0
    pz = float(getattr(player, 'z', 0.0)) if player else 0.0

    for ent in list(getattr(game, 'life_sim_named', []) or []) + list(getattr(game, 'life_sim_crowd', []) or []):
        if not ent or getattr(ent, 'hp', 1) <= 0:
            continue
        # Hold still + face player while dialogue panel is open on this NPC
        if getattr(ent, 'talk_frozen', False) or ent is getattr(game, 'talk_target', None):
            try:
                hold = getattr(ent, '_talk_hold_pos', None)
                if hold is not None:
                    ent.x, ent.y, ent.z = float(hold[0]), float(hold[1]), float(hold[2])
                else:
                    ent._talk_hold_pos = (float(ent.x), float(getattr(ent, 'y', 0) or 0), float(ent.z))
                if player is not None:
                    dx = px - float(ent.x)
                    dz = pz - float(ent.z)
                    if abs(dx) + abs(dz) > 0.05:
                        import math as _m
                        yaw = _m.degrees(_m.atan2(dx, dz))
                        ent.rotation_y = yaw
                        try:
                            ent.heading = yaw
                        except Exception:
                            pass
                ent.y = 0.0
            except Exception:
                pass
            continue
        sched = getattr(ent, 'life_schedule', None)
        if not sched:
            continue
        state, tx, tz, line = _pick_slot(sched, hour)
        tx, tz = clamp_destination(tx, tz)
        prev = getattr(ent, 'life_state', None)
        ent.life_state = state
        ent.life_line = line
        ent.talkable = True
        fsm = _ensure_fsm(ent, state)
        if prev != state:
            try:
                fsm.set(state)
            except Exception:
                pass

        # Keep visible near player / after yard exit (y>=0 + set_visible)
        try:
            if getattr(ent, 'y', 0) is not None and float(ent.y) < -0.05:
                ent.y = 0.0
        except Exception:
            pass
        dist = math.hypot(float(ent.x) - px, float(ent.z) - pz)
        if dist < 48.0:
            set_visible(ent, True)
        # Far life-sim agents: lower update rate (LOD-ish)
        far = dist > 36.0
        if far and int(getattr(game, '_crowd_frame', 0)) % 2 != 0:
            continue
        speed = 1.7 if state == 'wander' else 1.35
        if state == 'work':
            speed = 1.1
        _move_toward(ent, tx, tz, speed, dt)

        # Soft clamp — expanded Clermont bounds
        try:
            ent.x = max(-58, min(78, float(ent.x)))
            ent.z = max(-58, min(28, float(ent.z)))
            ent.y = 0.0
        except Exception:
            pass


def decorate_talk_line(ent, base: str) -> str:
    """Prefix / suffix dialogue with schedule flavor + crowd variety."""
    extra = state_line(ent)
    line = getattr(ent, 'line', None)
    if line and line not in (base or ''):
        if not base or base in ('...', '…', '.'):
            base = line
        elif line not in base:
            base = f"{base}\n\n{line}"
    if not extra:
        return base
    if not base:
        return extra
    if extra in base:
        return base
    return f"{base}\n\n({extra})"
