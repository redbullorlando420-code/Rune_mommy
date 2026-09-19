"""Enterable interior rooms — Sanctuary house, Quiet Spa, Club 27, gas, Walmart.

Outdoor colliders stay. Interiors live in a far +X/+Z pocket.
Enter via E at a door trigger; exit via E at the green exit mat.
"""
from __future__ import annotations

import math


FLOOR_Y = 0.03


def _rgb(color, r, g, b):
    return color.rgb32(r, g, b)


def _prop(Entity, pos, scale, col):
    return Entity(model='cube', scale=scale, position=pos, color=col)


def _make_room(Entity, color, Text, origin, title, w=10.0, d=8.0, h=3.2, wall_col=None, floor_col=None):
    ox, _, oz = origin
    wall_col = wall_col or _rgb(color, 210, 200, 190)
    floor_col = floor_col or _rgb(color, 90, 80, 70)
    parts = []
    parts.append(Entity(model='cube', scale=(w, 0.1, d), position=(ox, FLOOR_Y, oz),
                        color=floor_col, collider='box'))
    parts.append(Entity(model='cube', scale=(w, 0.1, d), position=(ox, h, oz),
                        color=_rgb(color, 230, 230, 235)))
    gap = 1.4
    parts.append(Entity(model='cube', scale=(w, h, 0.2), position=(ox, h / 2, oz + d / 2),
                        color=wall_col, collider='box'))
    parts.append(Entity(model='cube', scale=(0.2, h, d), position=(ox - w / 2, h / 2, oz),
                        color=wall_col, collider='box'))
    parts.append(Entity(model='cube', scale=(0.2, h, d), position=(ox + w / 2, h / 2, oz),
                        color=wall_col, collider='box'))
    span = (w - gap) / 2.0
    parts.append(Entity(model='cube', scale=(span, h, 0.2),
                        position=(ox - gap / 2 - span / 2, h / 2, oz - d / 2),
                        color=wall_col, collider='box'))
    parts.append(Entity(model='cube', scale=(span, h, 0.2),
                        position=(ox + gap / 2 + span / 2, h / 2, oz - d / 2),
                        color=wall_col, collider='box'))
    exit_m = Entity(model='cube', scale=(1.4, 0.08, 1.2),
                    position=(ox, 0.05, oz - d / 2 + 0.4),
                    color=_rgb(color, 80, 220, 140))
    exit_m.kind = 'interior_exit'
    exit_m.prompt = 'E  exit outside'
    parts.append(exit_m)
    if Text:
        t = Text(text=title, position=(ox, h - 0.4, oz), origin=(0, 0),
                 billboard=True, color=_rgb(color, 255, 230, 255))
        try:
            t.world_scale = 1.4
        except Exception:
            pass
        parts.append(t)
    return parts, exit_m


def _make_door(Entity, color, x, z, label, interior_id):
    Entity(
        model='cube',
        scale=(1.1, 2.2, 0.12),
        position=(x, 1.1, z),
        color=_rgb(color, 60, 40, 30),
    )
    marker = Entity(
        model='cube',
        scale=(1.6, 0.08, 1.6),
        position=(x, 0.045, z - 0.85),
        color=_rgb(color, 255, 180, 80),
    )
    marker.kind = 'interior_door'
    marker.interior_id = interior_id
    marker.prompt = f'E  enter {label}'
    return marker


def build_all(game):
    Entity = game.Entity
    color = game.color
    Text = getattr(game, 'Text', None)
    game.interiors = {}
    game.interior_doors = []
    game.active_interior = None
    game.interior_return_pos = None

    specs = [
        dict(id='sanctuary', title='Sanctuary Drive — Inside', door=(-27.9, 10.6),
             label='Michelle house', origin=(120.0, 0.0, 120.0), style='house', shop_id=None),
        dict(id='quiet_spa', title='Quiet Spa — Treatment Room', door=(-36.0, -18.5),
             label='Quiet Spa', origin=(135.0, 0.0, 120.0), style='spa', shop_id=None),
        dict(id='club27', title='Club 27 — Lounge', door=(40.0, -24.0),
             label='Club 27', origin=(150.0, 0.0, 120.0), style='club', shop_id=None),
        dict(id='gas_shop', title='Hancock Gas — Counter', door=(18.0, -11.5),
             label='Gas shop', origin=(165.0, 0.0, 120.0), style='shop', shop_id=None),
        dict(id='walmart', title='Walmart Supercenter', door=(62.0, -27.0),
             label='Walmart', origin=(185.0, 0.0, 120.0), style='walmart',
             shop_id='walmart_clermont', w=16.0, d=12.0),
        dict(id='pet_store', title='Paws on 50 — Aisles', door=(-22.0, 5.2),
             label='Pet Store', origin=(200.0, 0.0, 120.0), style='retail',
             shop_id='pet_store_clermont', w=10.0, d=8.0),
        dict(id='bestbuy', title='Best Buy — Floor', door=(28.0, 5.8),
             label='Best Buy', origin=(215.0, 0.0, 120.0), style='retail',
             shop_id='bestbuy_clermont', w=12.0, d=9.0),
        dict(id='gamestop', title='GameStop — Floor', door=(8.0, 4.6),
             label='GameStop', origin=(230.0, 0.0, 120.0), style='retail',
             shop_id='gamestop_clermont', w=8.0, d=7.0),
        dict(id='tire_shop', title='Hwy 50 Tire & Lube', door=(42.0, -8.8),
             label='Tire Shop', origin=(245.0, 0.0, 120.0), style='tire',
             shop_id='tire_shop_clermont', w=10.0, d=8.0),
        dict(id='nail_salon', title='Neon Toes Nail Salon', door=(-14.0, 5.8),
             label='Nail Salon', origin=(260.0, 0.0, 120.0), style='nail',
             shop_id='nail_salon_clermont', w=9.0, d=7.0),
    ]

    for spec in specs:
        iid = spec['id']
        origin = spec['origin']
        w = float(spec.get('w', 10.0))
        d = float(spec.get('d', 8.0))
        wall = floor = None
        if spec['style'] == 'spa':
            wall, floor = _rgb(color, 220, 230, 225), _rgb(color, 180, 200, 195)
        elif spec['style'] == 'club':
            wall, floor = _rgb(color, 40, 16, 48), _rgb(color, 30, 12, 36)
        elif spec['style'] == 'walmart':
            wall, floor = _rgb(color, 240, 240, 245), _rgb(color, 200, 200, 205)
        elif spec['style'] == 'retail':
            wall, floor = _rgb(color, 235, 235, 240), _rgb(color, 180, 180, 190)
        elif spec['style'] == 'tire':
            wall, floor = _rgb(color, 70, 70, 75), _rgb(color, 50, 50, 55)
        elif spec['style'] == 'nail':
            wall, floor = _rgb(color, 255, 220, 235), _rgb(color, 240, 200, 220)
        elif spec['style'] == 'house':
            wall, floor = _rgb(color, 232, 214, 188), _rgb(color, 140, 110, 80)

        parts, exit_m = _make_room(
            Entity, color, Text, origin, spec['title'],
            w=w, d=d, wall_col=wall, floor_col=floor,
        )
        ox, _, oz = origin
        if spec['style'] == 'house':
            parts.append(_prop(Entity, (ox - 2.0, 0.45, oz + 1.2), (2.2, 0.4, 1.5), _rgb(color, 220, 210, 200)))
            parts.append(_prop(Entity, (ox + 2.2, 0.9, oz + 0.5), (1.2, 1.6, 0.6), _rgb(color, 90, 70, 55)))
            parts.append(_prop(Entity, (ox + 0.2, 0.55, oz - 1.5), (1.6, 0.7, 0.8), _rgb(color, 180, 150, 120)))
        elif spec['style'] == 'spa':
            parts.append(_prop(Entity, (ox, 0.45, oz), (2.0, 0.5, 1.0), _rgb(color, 200, 220, 220)))
            parts.append(_prop(Entity, (ox - 2.5, 0.7, oz + 1.5), (0.8, 1.2, 0.8), _rgb(color, 120, 95, 55)))
        elif spec['style'] == 'club':
            parts.append(_prop(Entity, (ox, 0.6, oz + 1.5), (4.0, 0.8, 1.2), _rgb(color, 90, 20, 50)))
            parts.append(Entity(model='cube', scale=(w - 1.0, 0.1, 0.1),
                                position=(ox, 2.6, oz + d / 2 - 0.3),
                                color=_rgb(color, 255, 40, 160)))
        elif spec['style'] == 'shop':
            parts.append(_prop(Entity, (ox, 0.55, oz + 1.0), (3.5, 0.9, 0.8), _rgb(color, 50, 50, 60)))
        elif spec['style'] == 'walmart':
            for dx in (-5.0, -2.0, 2.0, 5.0):
                parts.append(_prop(Entity, (ox + dx, 1.1, oz + 1.0), (1.2, 2.0, 6.0), _rgb(color, 230, 230, 235)))
            parts.append(_prop(Entity, (ox, 0.55, oz - 4.0), (4.0, 0.9, 1.0), _rgb(color, 0, 113, 206)))
            parts.append(Entity(model='cube', scale=(3.5, 0.8, 0.1),
                                position=(ox, 2.8, oz + d / 2 - 0.25),
                                color=_rgb(color, 255, 194, 32)))
        elif spec['style'] == 'retail':
            for dx in (-3.0, 0.0, 3.0):
                parts.append(_prop(Entity, (ox + dx, 1.0, oz + 0.8), (1.0, 1.8, 4.0), _rgb(color, 220, 220, 230)))
            parts.append(_prop(Entity, (ox, 0.55, oz - 2.5), (3.5, 0.9, 0.9), _rgb(color, 40, 40, 50)))
        elif spec['style'] == 'tire':
            parts.append(_prop(Entity, (ox, 0.7, oz + 1.0), (4.0, 1.2, 2.0), _rgb(color, 60, 60, 65)))
            for dx in (-2.0, 2.0):
                for k in range(3):
                    parts.append(_prop(Entity, (ox + dx, 0.25 + k * 0.22, oz - 1.5), (0.6, 0.2, 0.6), _rgb(color, 20, 20, 20)))
            parts.append(_prop(Entity, (ox, 0.55, oz - 2.8), (3.0, 0.9, 0.8), _rgb(color, 255, 107, 0)))
        elif spec['style'] == 'nail':
            # pedicure chairs
            for dx in (-2.5, 0.0, 2.5):
                parts.append(_prop(Entity, (ox + dx, 0.55, oz + 1.0), (1.2, 0.9, 1.4), _rgb(color, 255, 150, 190)))
            parts.append(_prop(Entity, (ox, 0.45, oz - 2.0), (3.0, 0.7, 0.8), _rgb(color, 255, 105, 180)))
            parts.append(Entity(model='cube', scale=(2.5, 0.15, 0.15),
                                position=(ox, 2.6, oz + 2.0), color=_rgb(color, 255, 80, 180)))

        dx, dz = spec['door']
        marker = _make_door(Entity, color, dx, dz, spec['label'], iid)
        game.interior_doors.append(marker)
        spawn = (ox, 0.0, oz - d / 2 + 1.5)
        game.interiors[iid] = {
            'id': iid,
            'title': spec['title'],
            'origin': origin,
            'spawn': spawn,
            'exit': exit_m,
            'parts': parts,
            'shop_id': spec.get('shop_id'),
            'door_pos': (dx, 0.0, dz),
            'return_pos': (dx, 0.0, dz - 1.5),
        }

    print('  interiors: %d rooms' % len(game.interiors))


def nearest_door(game, pos, radius=2.8):
    best, best_d = None, radius
    for m in getattr(game, 'interior_doors', []) or []:
        d = math.hypot(pos[0] - m.x, pos[2] - m.z)
        if d < best_d:
            best, best_d = m, d
    return best, best_d


def prompt(game, pos):
    active = getattr(game, 'active_interior', None)
    if active:
        inter = (game.interiors or {}).get(active) or {}
        ex = inter.get('exit')
        if ex and math.hypot(pos[0] - ex.x, pos[2] - ex.z) < 2.2:
            return 'E  exit outside'
        if inter.get('shop_id') == 'tire_shop_clermont':
            return 'E  tire service'
        if inter.get('shop_id') == 'nail_salon_clermont':
            return 'E  pedicure lounge'
        if inter.get('shop_id'):
            return 'E  shop shelves'
        return ''
    door, _d = nearest_door(game, pos)
    if door:
        return getattr(door, 'prompt', 'E  enter')
    return ''


def try_interact(game):
    pos = game._actor_pos()
    active = getattr(game, 'active_interior', None)
    if active:
        inter = (game.interiors or {}).get(active) or {}
        ex = inter.get('exit')
        if ex and math.hypot(pos[0] - ex.x, pos[2] - ex.z) < 2.4:
            _exit_interior(game)
            return True
        if inter.get('shop_id'):
            _open_shop(game, inter['shop_id'])
            return True
        game.toast('Walk to the green exit mat, then E.')
        return True

    door, _d = nearest_door(game, pos, 2.8)
    if door:
        _enter(game, door.interior_id)
        return True
    return False


def _enter(game, interior_id):
    inter = (getattr(game, 'interiors', {}) or {}).get(interior_id)
    if not inter:
        game.toast('Door jammed.')
        return
    if getattr(game, 'in_car', None):
        game.toast('Exit the car first.')
        return
    pos = game._actor_pos()
    game.interior_return_pos = inter.get('return_pos') or (pos[0], 0.0, pos[2])
    game.active_interior = interior_id
    sx, _sy, sz = inter['spawn']
    game.player.position = (sx, 0.0, sz)
    game.toast(inter.get('title') or 'Inside.')


def _exit_interior(game):
    inter = (getattr(game, 'interiors', {}) or {}).get(game.active_interior) or {}
    rx, _ry, rz = game.interior_return_pos or inter.get('return_pos') or (0, 0, -8)
    game.active_interior = None
    game.interior_return_pos = None
    game.player.position = (rx, 0.0, rz)
    game.toast('Back outside.')


def _open_shop(game, shop_id):
    shops = list((getattr(game, 'shops_data', None) or {}).get('shops') or [])
    shop = next((s for s in shops if s.get('id') == shop_id), None)
    if not shop:
        game.toast('Shelves empty.')
        return
    if shop_id == 'tire_shop_clermont' and hasattr(game, 'open_tire_shop'):
        game.open_tire_shop()
        return
    if shop_id == 'nail_salon_clermont':
        try:
            import adult_minigames
            adult_minigames.start_nail_salon(game)
            return
        except Exception as exc:
            print('  nail salon open skip:', exc)
    stall = {
        'id': shop_id,
        'name': shop.get('name', shop_id),
        'kind': shop.get('kind') or 'big_box',
        'pos': game._actor_pos(),
        'shop': shop,
        'npc': shop.get('npcName', 'Greeter'),
    }
    if hasattr(game, 'open_shake_shop'):
        game.open_shake_shop(stall)
    else:
        game.toast(shop.get('greeting') or shop.get('name'))
