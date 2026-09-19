"""Tokyo / Akihabara portal — Clermont torii → Akihabara district round-trip.

Thin API for game.py hooks. Michelle stays Clermont-only.
"""
from __future__ import annotations

import math

import akihabara

# Clermont portal — north of Hwy 50 near plaza / gas strip (findable)
CLERMONT_PORTAL_XZ = (16.0, 3.5)
RETURN_HOME_XZ = (14.0, 2.0)  # land near portal on return


def _dist(ax, az, bx, bz):
    return math.hypot(ax - bx, az - bz)


def boot(game):
    """Build Clermont→Akihabara portal arch + Akihabara district pocket."""
    from models3d._tokyo import make_torii_portal

    Entity = game.Entity
    color = game.color
    Text = game.Text
    scene = game._scene()

    game.district = getattr(game, 'district', None) or 'clermont'
    game.tokyo_portal = None
    game.akihabara_return_portal = None

    cx, cz = CLERMONT_PORTAL_XZ
    try:
        n, pos = make_torii_portal(
            Entity, color, Text, scene, cx, cz,
            label='AKIHABARA',
        )
        game.tokyo_portal = {
            'pos': pos,
            'kind': 'tokyo_portal',
            'prompt': 'E  portal to Akihabara',
        }
        game.pois.append({
            'id': 'tokyo_portal',
            'name': 'Akihabara Portal',
            'pos': (pos[0], 0, pos[2]),
            'npc_id': None,
            'line': None,
            'is_gas': False,
            'pump_r': 3.0,
        })
        game.building_count = int(getattr(game, 'building_count', 0) or 0) + 1
        print(f'  Tokyo portal @ ({cx}, {cz}) parts≈{n}')
    except Exception as exc:
        print('  tokyo portal skip:', exc)

    # PERF: do NOT build Akihabara at boot — only the Clermont portal.
    # District meshes+crowd spawn on first portal enter (ensure_akihabara).
    game.akihabara_built = False


def ensure_akihabara(game):
    """Lazy-build Akihabara district the first time the portal is used."""
    if getattr(game, 'akihabara_built', False):
        return
    try:
        akihabara.build(game)
        game.akihabara_built = True
    except Exception as exc:
        print('  akihabara skip:', exc)


def teleport_to_akihabara(game):
    ensure_akihabara(game)

    ox, _, oz = akihabara.ORIGIN
    # Spawn on Electric Town spine facing station
    sx, sz = ox, oz - 6.0
    if game.in_car:
        try:
            game._exit_car()
        except Exception:
            game.in_car = None
    game.player.position = (sx, 0, sz)
    game.player.y = 0
    game.player.rotation_y = 0
    game.district = 'akihabara'
    game.toast('Akihabara — Electric Town. Torii near station returns to Clermont.')
    try:
        game._quest_event('visit', poi_id='akihabara')
    except Exception:
        pass


def teleport_to_clermont(game):
    hx, hz = RETURN_HOME_XZ
    if game.in_car:
        try:
            game._exit_car()
        except Exception:
            game.in_car = None
    game.player.position = (hx, 0, hz)
    game.player.y = 0
    game.player.rotation_y = 180
    game.district = 'clermont'
    game.toast('Back in Clermont. Sanctuary Drive is west — Michelle at the door.')


def _portal_near(game, radius=2.4):
    pos = game.player.position
    px, pz = float(pos[0]), float(pos[2])
    district = getattr(game, 'district', 'clermont')

    if district != 'akihabara':
        p = getattr(game, 'tokyo_portal', None)
        if p:
            pp = p['pos']
            if _dist(px, pz, float(pp[0]), float(pp[2])) <= radius:
                return 'to_akihabara', p
    else:
        p = getattr(game, 'akihabara_return_portal', None)
        if p:
            pp = p['pos']
            if _dist(px, pz, float(pp[0]), float(pp[2])) <= radius:
                return 'to_clermont', p
    return None, None


def try_interact(game) -> bool:
    """E on portal mat. Returns True if handled."""
    kind, _p = _portal_near(game, radius=2.6)
    if kind == 'to_akihabara':
        teleport_to_akihabara(game)
        return True
    if kind == 'to_clermont':
        teleport_to_clermont(game)
        return True
    return False


def try_walk_in(game) -> bool:
    """Auto teleport when standing on portal (slightly tighter radius)."""
    kind, _p = _portal_near(game, radius=1.35)
    if kind == 'to_akihabara':
        teleport_to_akihabara(game)
        return True
    if kind == 'to_clermont':
        teleport_to_clermont(game)
        return True
    return False


def prompt_line(game):
    kind, p = _portal_near(game, radius=2.8)
    if kind and p:
        return p.get('prompt') or 'E  portal'
    return None


def tick(game, dt):
    """Walk-in portal + light Akihabara crowd wander when player is in district."""
    if getattr(game, 'mode', 'play') != 'play':
        return
    if getattr(game, 'ui_open', False):
        return
    # walk-in (cooldown via attribute)
    cd = float(getattr(game, 'tokyo_portal_cd', 0) or 0)
    if cd > 0:
        game.tokyo_portal_cd = cd - dt
    else:
        if try_walk_in(game):
            game.tokyo_portal_cd = 2.5

    if getattr(game, 'district', 'clermont') != 'akihabara':
        return

    # Keep named + crowd visible and lightly wandering
    pos = game.player.position
    px, pz = float(pos[0]), float(pos[2])
    for ped in list(getattr(game, 'akihabara_crowd', []) or []):
        try:
            set_visible = __import__('lighting', fromlist=['set_visible']).set_visible
            set_visible(ped, True)
            ped.y = 0
            origin = getattr(ped, 'wander_origin', None)
            if not origin:
                continue
            # simple orbit wander
            ang = float(getattr(ped, 'wander_ang', 0) or 0) + dt * 0.4
            ped.wander_ang = ang
            r = float(getattr(ped, 'wander_r', 3) or 3)
            ped.x = origin[0] + math.cos(ang) * r * 0.35
            ped.z = origin[1] + math.sin(ang) * r * 0.35
        except Exception:
            pass
    for npc in list(getattr(game, 'akihabara_named', []) or []):
        try:
            from lighting import set_visible
            set_visible(npc, True)
            npc.y = 0
        except Exception:
            pass
