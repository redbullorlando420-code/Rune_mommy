"""Akihabara district — far-XYZ pocket with real named POIs + JP crowd.

Built by tokyo.boot(game). Does not alter Clermont title→yard→gate flow.
"""
from __future__ import annotations

import random

from lighting import set_visible

# Far east pocket — clear of Walmart (~62) and Clermont lot
ORIGIN = (480.0, 0.0, 0.0)

# Named real locations (local offsets from ORIGIN)
POIS = (
    ('akihabara_station', 'Akihabara Station', 0.0, 8.0, 'station'),
    ('radio_kaikan', 'Radio Kaikan', -8.0, -2.0, 'shop'),
    ('super_potato', 'Super Potato', -3.0, -6.0, 'shop'),
    ('animate_akihabara', 'Animate Akihabara', 4.0, -5.5, 'shop'),
    ('don_quijote', 'Don Quijote (Donki)', 12.0, -3.0, 'donki'),
    ('mandarake', 'Mandarake', -12.0, -8.0, 'shop'),
    ('yodobashi', 'Yodobashi Camera', 18.0, 2.0, 'shop'),
    ('udx', 'Akihabara UDX', 8.0, 10.0, 'tower'),
    ('electric_town', 'Electric Town', 0.0, -10.0, 'arcade'),
)

# Named talkable JP district NPCs (English lines for playability)
NAMED_NPCS = (
    ('yuki', 'Yuki', -2.5, -4.0, (255, 120, 180), (40, 30, 50),
     "Welcome to Electric Town! Super Potato is downstairs energy — don't blink."),
    ('kenji', 'Kenji', 5.0, -3.5, (60, 90, 200), (30, 30, 40),
     "Animate just dropped a new figure line. Line starts at the neon corner."),
    ('mio', 'Mio', 11.0, -2.0, (255, 80, 60), (20, 20, 28),
     "Donki never sleeps. If you need snacks at 3am, that's the flashing clown."),
    ('sora', 'Sora', -7.0, -1.0, (80, 220, 180), (35, 35, 45),
     "Radio Kaikan — floors of parts and nostalgia. I'm hunting a rare PCB."),
)


def oxz(lx, lz):
    return ORIGIN[0] + lx, ORIGIN[2] + lz


def build(game):
    """Spawn Akihabara meshes, shop stalls, return portal mat, walkable crowd."""
    from models3d._tokyo import (
        make_torii_portal, make_jp_narrow_shop, make_neon_billboard_jp,
        make_covered_arcade, make_station_facade, make_donki_box, Y_STREET,
    )

    Entity = game.Entity
    color = game.color
    Text = game.Text
    scene = game._scene()
    ox, _, oz = ORIGIN

    game.akihabara_parts = []
    game.akihabara_pois = []
    game.akihabara_crowd = []
    game.akihabara_named = []
    n = 0

    # Ground pad
    Entity(model='cube', scale=(56, 0.04, 40), position=(ox, Y_STREET, oz),
           color=color.rgb32(36, 36, 44), texture=None)
    n += 1

    # Covered Electric Town spine
    n += make_covered_arcade(Entity, color, Text, scene, ox, oz - 10.0,
                             length=30.0, width=7.0, name='Electric Town')

    # Station
    sn, s_interact = make_station_facade(Entity, color, Text, scene, ox, oz + 8.0)
    n += sn

    # Neon boards
    for bx, bz, label, rgb in (
        (ox - 14, oz + 2, 'AKIHABARA', (80, 255, 200)),
        (ox + 14, oz - 6, 'RADIO', (255, 60, 160)),
        (ox + 6, oz + 4, 'GAMES', (120, 180, 255)),
    ):
        n += make_neon_billboard_jp(Entity, color, Text, scene, bx, bz, text=label,
                                    neon_rgb=rgb)

    shop_lookup = {s.get('id'): s for s in (game.shops_data or {}).get('shops') or []}
    game.akihabara_stalls = []

    # Named storefronts
    store_specs = [
        # ASCII signs only — Ursina default font has no CJK (avoids Text warning spam)
        ('radio_kaikan', 'Radio Kaikan', -8.0, -2.0, 4, (45, 48, 70), (255, 90, 40), 'RK'),
        ('super_potato', 'Super Potato', -3.0, -6.0, 5, (50, 40, 30), (255, 200, 40), 'SP'),
        ('animate_akihabara', 'Animate', 4.0, -5.5, 4, (40, 55, 90), (255, 100, 180), 'AN'),
        ('mandarake', 'Mandarake', -12.0, -8.0, 3, (60, 35, 45), (220, 60, 90), 'MD'),
        ('yodobashi', 'Yodobashi', 18.0, -1.0, 4, (30, 50, 90), (80, 140, 255), 'YO'),
        ('udx', 'UDX', 8.0, 10.0, 5, (55, 60, 75), (100, 255, 220), 'UDX'),
    ]
    for sid, name, lx, lz, floors, body, neon, sign in store_specs:
        wx, wz = oxz(lx, lz)
        bn, interact = make_jp_narrow_shop(
            Entity, color, Text, scene, wx, wz, name=name, floors=floors,
            body_rgb=body, neon_rgb=neon, sign=sign, w=2.6 if floors >= 4 else 2.3,
        )
        n += bn
        shop = shop_lookup.get(sid) or {'id': sid, 'name': name, 'stock': []}
        rec = {
            'id': sid,
            'name': shop.get('name', name),
            'kind': 'akihabara_shop',
            'pos': (interact[0], 0, interact[2]),
            'shop': shop,
            'npc': shop.get('npcName', ''),
            'district': 'akihabara',
        }
        game.akihabara_stalls.append(rec)
        game.stalls.append(rec)
        game.akihabara_pois.append({
            'id': sid, 'name': name, 'pos': rec['pos'], 'kind': 'shop',
        })

    # Donki
    dx, dz = oxz(12.0, -3.0)
    dn, d_interact = make_donki_box(Entity, color, Text, scene, dx, dz)
    n += dn
    donki = shop_lookup.get('don_quijote') or {'id': 'don_quijote', 'name': 'Don Quijote', 'stock': []}
    drec = {
        'id': 'don_quijote',
        'name': donki.get('name', 'Don Quijote'),
        'kind': 'akihabara_shop',
        'pos': (d_interact[0], 0, d_interact[2]),
        'shop': donki,
        'npc': donki.get('npcName', ''),
        'district': 'akihabara',
    }
    game.akihabara_stalls.append(drec)
    game.stalls.append(drec)
    game.akihabara_pois.append({
        'id': 'don_quijote', 'name': 'Don Quijote (Donki)', 'pos': drec['pos'], 'kind': 'shop',
    })

    # Station POI
    game.akihabara_pois.append({
        'id': 'akihabara_station',
        'name': 'Akihabara Station',
        'pos': (s_interact[0], 0, s_interact[2]),
        'kind': 'station',
    })
    game.akihabara_pois.append({
        'id': 'electric_town',
        'name': 'Electric Town',
        'pos': (ox, 0, oz - 10.0),
        'kind': 'arcade',
    })

    # Return portal (torii) near station plaza
    rn, rpos = make_torii_portal(
        Entity, color, Text, scene, ox - 6.0, oz + 4.0,
        label='CLERMONT <-',
    )
    n += rn
    game.akihabara_return_portal = {
        'pos': rpos,
        'kind': 'tokyo_return',
        'prompt': 'E  return to Clermont',
    }
    # Tag mat kind for walk-in
    # (mat already kind=tokyo_portal — tokyo.py distinguishes by district)

    # Named NPCs
    for nid, name, lx, lz, shirt, pants, line in NAMED_NPCS:
        wx, wz = oxz(lx, lz)
        try:
            npc = game._humanoid(
                wx, wz,
                shirt=color.rgb32(*shirt),
                pants=color.rgb32(*pants),
                skin=color.rgb32(255, 210, 180),
                detail='named',
            )
        except Exception as exc:
            print('  akihabara npc skip', nid, exc)
            continue
        npc.npc_id = nid
        npc.npc_name = name
        npc.kind = 'talk'
        npc.hittable = False
        npc.line = line
        npc.district = 'akihabara'
        npc.emotion = 'curious'
        try:
            set_visible(npc, True)
        except Exception:
            pass
        game.npcs.append(npc)
        game.akihabara_named.append(npc)

    # Walkable crowd
    rng = random.Random(4801)
    shirts = (
        (255, 60, 140), (60, 200, 255), (255, 220, 60), (120, 80, 255),
        (40, 220, 120), (255, 100, 80), (200, 200, 220),
    )
    for i in range(8):
        lx = rng.uniform(-16, 20)
        lz = rng.uniform(-14, 6)
        wx, wz = oxz(lx, lz)
        shirt = shirts[i % len(shirts)]
        try:
            ped = game._humanoid(
                wx, wz,
                shirt=color.rgb32(*shirt),
                pants=color.rgb32(30, 30, 38),
                skin=color.rgb32(rng.randint(180, 255), rng.randint(160, 220), rng.randint(140, 200)),
                detail='crowd',
            )
        except Exception:
            continue
        ped.kind = 'crowd'
        ped.district = 'akihabara'
        ped.hittable = False
        ped.wander_origin = (wx, wz)
        ped.wander_r = 4.0
        ped.npc_name = 'ped'
        try:
            set_visible(ped, True)
        except Exception:
            pass
        game.akihabara_crowd.append(ped)
        # Do NOT append to game.peds — Clermont tick_crowd would cull/yank them.

    game.building_count = int(getattr(game, 'building_count', 0) or 0) + max(1, n // 8)
    game.akihabara_built = True
    print(f'  Akihabara district @ {ORIGIN}  pois={len(game.akihabara_pois)} crowd={len(game.akihabara_crowd)}')
    return n
