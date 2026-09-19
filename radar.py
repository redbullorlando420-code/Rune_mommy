"""Minimap + quest waypoint markers (UI radar + world beacon).

Simple top-down radar: player, active quest target, key POIs.
World: floating chevron above the quest NPC / POI.
"""
from __future__ import annotations

import math
from typing import Any, Optional, Tuple

# UI layout (Ursina camera.ui space)
MAP_POS = (0.72, -0.32)
MAP_SCALE = 0.28
WORLD_RANGE = 55.0  # world meters mapped onto radar


def _xz(ent) -> Optional[Tuple[float, float]]:
    if not ent:
        return None
    try:
        return float(ent.x), float(ent.z)
    except Exception:
        try:
            p = ent.position
            return float(p[0]), float(p[2])
        except Exception:
            return None


def resolve_quest_target(game) -> Optional[Tuple[float, float, str]]:
    """Return (x, z, label) for the first active quest target, or None."""
    active = list(getattr(game, 'quest_active', None) or getattr(game, 'quest_active', None) or [])
    for qid in list(active):
        q = None
        if hasattr(game, '_quest_def'):
            q = game._quest_def(qid)
        elif hasattr(game, '_quest_def'):
            q = game._quest_def(qid)
        if not q:
            continue
        label = q.get('name') or qid
        npc_id = q.get('npc')
        if npc_id:
            for npc in list(getattr(game, 'npcs', None) or []):
                if not npc:
                    continue
                if getattr(npc, 'npc_id', None) == npc_id or getattr(npc, 'kind', None) == npc_id:
                    xz = _xz(npc)
                    if xz:
                        return xz[0], xz[1], label
            # POI interact tied to this npc
            for poi in list(getattr(game, 'pois', None) or []):
                if poi.get('npc_id') == npc_id:
                    pos = poi.get('pos') or poi.get('position')
                    if pos:
                        return float(pos[0]), float(pos[2] if len(pos) > 2 else pos[1]), label
        poi_id = q.get('poi') or q.get('place')
        if poi_id:
            for poi in list(getattr(game, 'pois', None) or []):
                if poi.get('id') == poi_id or poi.get('kind') == poi_id:
                    pos = poi.get('pos') or poi.get('position')
                    if pos:
                        return float(pos[0]), float(pos[2] if len(pos) > 2 else pos[1]), label
        # buy / buy_pistol — aim at related npc if any
        if q.get('type') in ('buy', 'buy_pistol') and npc_id:
            continue
        # visit already handled via poi
    return None


def boot(game) -> None:
    """Build minimap UI + world waypoint beacon. Idempotent."""
    if getattr(game, 'radar_booted', False):
        return
    Entity = game.Entity
    Text = game.Text
    color = game.color
    camera = game.camera

    root = Entity(parent=camera.ui, position=MAP_POS, z=-0.08)
    # frame
    bg = Entity(
        parent=root, model='quad',
        color=color.rgba32(8, 4, 18, 200),
        scale=MAP_SCALE,
        z=0.02,
    )
    ring = Entity(
        parent=root, model='circle',
        color=color.rgba32(255, 90, 210, 90),
        scale=MAP_SCALE * 1.02,
        z=0.01,
    )
    try:
        ring.model = 'circle'
    except Exception:
        # fallback square rim
        pass

    title = Text(
        parent=camera.ui,
        text='MAP',
        position=(MAP_POS[0] - 0.06, MAP_POS[1] + MAP_SCALE * 0.55),
        origin=(0, 0),
        color=color.rgb32(255, 140, 220),
        scale=0.55,
    )

    player_dot = Entity(
        parent=root, model='quad',
        color=color.rgb32(255, 255, 255),
        scale=0.018, z=-0.01, rotation_z=45,
    )
    quest_dot = Entity(
        parent=root, model='quad',
        color=color.rgb32(255, 230, 60),
        scale=0.022, z=-0.02, enabled=False, rotation_z=45,
    )
    # POI dots pool
    poi_dots = []
    for _ in range(14):
        d = Entity(
            parent=root, model='quad',
            color=color.rgb32(80, 220, 255),
            scale=0.012, z=-0.015, enabled=False,
        )
        poi_dots.append(d)

    # compass arrow (screen center-top-ish) pointing toward quest
    compass = Entity(
        parent=camera.ui, model='quad',
        color=color.rgb32(255, 210, 40),
        scale=(0.035, 0.055),
        position=(0.0, 0.38),
        enabled=False, z=-0.05,
    )
    compass_lbl = Text(
        parent=camera.ui, text='',
        position=(0.0, 0.34), origin=(0, 0),
        color=color.rgb32(255, 230, 120), scale=0.6, enabled=False,
    )

    # world-space beacon (chevron)
    beacon = Entity(
        model='cube',
        color=color.rgb32(255, 220, 40),
        scale=(0.35, 0.55, 0.35),
        position=(0, -50, 0),
        enabled=False,
    )
    beacon_glow = Entity(
        parent=beacon, model='cube',
        color=color.rgb32(255, 100, 200),
        scale=(1.4, 0.15, 1.4), y=-0.4,
    )

    game.radar = {
        'root': root,
        'bg': bg,
        'player_dot': player_dot,
        'quest_dot': quest_dot,
        'poi_dots': poi_dots,
        'compass': compass,
        'compass_lbl': compass_lbl,
        'beacon': beacon,
        'title': title,
    }
    game.radar_booted = True
    print('  radar: minimap + waypoint ready')


def _to_radar(dx: float, dz: float) -> Tuple[float, float]:
    """Map world delta into radar local UI coords."""
    s = (MAP_SCALE * 0.42) / WORLD_RANGE
    # Ursina UI: +x right, +y up. World +z is "north" on radar.
    rx = max(-MAP_SCALE * 0.42, min(MAP_SCALE * 0.42, dx * s))
    ry = max(-MAP_SCALE * 0.42, min(MAP_SCALE * 0.42, dz * s))
    return rx, ry


def tick(game, dt: float = 0.0) -> None:
    if not getattr(game, 'radar_booted', False):
        return
    if getattr(game, 'mode', 'play') in ('menu', 'settings'):
        try:
            game.radar['root'].enabled = False
            game.radar['compass'].enabled = False
            game.radar['compass_lbl'].enabled = False
            game.radar['beacon'].enabled = False
        except Exception:
            pass
        return

    r = game.radar
    try:
        r['root'].enabled = True
    except Exception:
        return

    player = getattr(game, 'player', None)
    pxz = _xz(player)
    if not pxz:
        return
    px, pz = pxz

    # player always center
    r['player_dot'].x = 0
    r['player_dot'].y = 0
    # face indicator — rotate player dot with yaw
    try:
        r['player_dot'].rotation_z = -float(player.rotation_y)
    except Exception:
        pass

    # POIs
    pois = list(getattr(game, 'pois', None) or [])[: len(r['poi_dots'])]
    for i, dot in enumerate(r['poi_dots']):
        if i >= len(pois):
            dot.enabled = False
            continue
        pos = pois[i].get('pos') or pois[i].get('position')
        if not pos:
            dot.enabled = False
            continue
        wx, wz = float(pos[0]), float(pos[2] if len(pos) > 2 else pos[1])
        rx, ry = _to_radar(wx - px, wz - pz)
        if abs(wx - px) > WORLD_RANGE or abs(wz - pz) > WORLD_RANGE:
            dot.enabled = False
            continue
        dot.enabled = True
        dot.x, dot.y = rx, ry
        # gas tint
        if pois[i].get('is_gas'):
            try:
                dot.color = game.color.rgb32(255, 180, 60)
            except Exception:
                pass
        else:
            try:
                dot.color = game.color.rgb32(80, 220, 255)
            except Exception:
                pass

    target = resolve_quest_target(game)
    compass = r['compass']
    clbl = r['compass_lbl']
    beacon = r['beacon']
    qdot = r['quest_dot']

    if not target:
        qdot.enabled = False
        compass.enabled = False
        clbl.enabled = False
        beacon.enabled = False
        return

    tx, tz, label = target
    dx, dz = tx - px, tz - pz
    dist = math.hypot(dx, dz)

    # radar quest dot
    rx, ry = _to_radar(dx, dz)
    qdot.enabled = True
    qdot.x, qdot.y = rx, ry

    # compass arrow (screen) — angle from player forward to target
    try:
        yaw = float(player.rotation_y)
    except Exception:
        yaw = 0.0
    # world angle of target (atan2 x,z) vs player yaw
    ang = math.degrees(math.atan2(dx, dz))
    rel = (ang - yaw + 180) % 360 - 180
    compass.enabled = True
    compass.rotation_z = -rel
    clbl.enabled = True
    clbl.text = f'{label}  {int(dist)}m'

    # world beacon
    beacon.enabled = True
    bob = 2.4 + 0.25 * math.sin(py_time() * 3.0)
    beacon.position = (tx, bob, tz)
    try:
        beacon.rotation_y += 90 * max(dt, 0.016)
    except Exception:
        pass


def py_time() -> float:
    try:
        import time as _t
        return _t.time()
    except Exception:
        return 0.0
