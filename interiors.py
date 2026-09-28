"""Walk-in interiors — co-located with building footprints (no far-XYZ teleport).

Exterior builders (retail / Walmart / tire / gas / spa / Club 27 / shake stalls /
Sanctuary) provide hollow shells with a door gap. This module fills shelves,
counters, and lights inside the same AABB and tracks who is "inside".

Walk through the doorway. E opens shop UI when inside a retail zone.
Walk out to leave — no orange-mat pocket teleport.

Look polish: _safe_tex floor/shelf fallbacks, denser shelf/counter props, wall plaques.
"""
from __future__ import annotations

import math

try:
    from models3d._base import _safe_tex
except Exception:
    def _safe_tex(*_a, **_k):
        return None


FLOOR_Y = 0.06


def _rgb(color, r, g, b):
    return color.rgb32(r, g, b)


def _prop(Entity, pos, scale, col, collider=None, texture=None, texture_scale=None):
    kw = {}
    if collider:
        kw['collider'] = collider
    if texture is not None:
        kw['texture'] = texture
        if texture_scale is not None:
            kw['texture_scale'] = texture_scale
    return Entity(model='cube', scale=scale, position=pos, color=col, **kw)


def _shelf_stock(Entity, color, ox, oz, dx, y, dz, n=3):
    """Cheap product cubes on a shelf face (no collider — walk-through safe)."""
    parts = []
    cols = (
        (220, 80, 100), (80, 160, 220), (255, 200, 80),
        (120, 200, 120), (200, 120, 220), (255, 140, 60),
    )
    span = 0.7
    for i in range(n):
        t = (i / max(1, n - 1)) - 0.5
        cr, cg, cb = cols[i % len(cols)]
        parts.append(_prop(
            Entity, (ox + dx + t * span, y, oz + dz),
            (0.14, 0.16, 0.12), _rgb(color, cr, cg, cb),
        ))
    return parts


def _sign_plaque(Entity, color, Text, ox, oz, title, *, y=2.55, z_off=None, w=2.4):
    """Readable wall plaque + Text — denser contrast than floating Text alone."""
    parts = []
    zz = oz if z_off is None else oz + z_off
    # dark plaque + neon edge
    parts.append(Entity(
        model='cube', scale=(w, 0.42, 0.08),
        position=(ox, y, zz), color=_rgb(color, 28, 22, 36),
    ))
    parts.append(Entity(
        model='cube', scale=(w + 0.08, 0.06, 0.06),
        position=(ox, y + 0.22, zz), color=_rgb(color, 255, 90, 200),
    ))
    if Text:
        short = (title or '')[:28]
        t = Text(text=short, position=(ox, y + 0.02, zz + 0.06), origin=(0, 0),
                 billboard=True, color=_rgb(color, 255, 240, 255))
        try:
            t.world_scale = 1.05
        except Exception:
            pass
        parts.append(t)
    return parts


def _resolve_xz(game, *, stall_id=None, poi_id=None, fixed=None):
    """Prefer live stall/poi position after footprint nudge; else fixed (x,z)."""
    if stall_id:
        for s in getattr(game, 'stalls', []) or []:
            if s.get('id') == stall_id:
                pos = s.get('pos')
                if pos:
                    # stall interact is in front — pull back into building center
                    return float(pos[0]), float(pos[2]) + 1.8
    if poi_id:
        for p in getattr(game, 'pois', []) or []:
            if p.get('id') == poi_id:
                pos = p.get('pos')
                if pos:
                    return float(pos[0]), float(pos[2]) + 2.0
    if fixed:
        return float(fixed[0]), float(fixed[1])
    return 0.0, 0.0


def _fill_props(Entity, color, Text, ox, oz, style, title, w, d):
    """Interior furniture only — walls/floor come from exterior hollow shell.

    Uses _safe_tex when registered (solid color fallback if missing — no pink).
    """
    parts = []
    floor_tex = _safe_tex('concrete', 'stucco')
    shelf_tex = _safe_tex('stucco', 'concrete')
    # Soft interior floor overlay
    floor_cols = {
        'house': (150, 120, 90),
        'spa': (185, 205, 200),
        'club': (32, 14, 40),
        'shop': (58, 58, 64),
        'walmart': (205, 205, 210),
        'retail': (185, 185, 195),
        'tire': (52, 52, 58),
        'nail': (245, 205, 225),
        'shake': (65, 52, 58),
    }
    fr, fg, fb = floor_cols.get(style, (90, 85, 80))
    floor_kw = {}
    if floor_tex is not None and style in ('walmart', 'retail', 'shop', 'tire'):
        floor_kw['texture'] = floor_tex
        floor_kw['texture_scale'] = (3, 2)
    parts.append(Entity(
        model='cube', scale=(max(2.0, w - 0.6), 0.04, max(2.0, d - 0.6)),
        position=(ox, FLOOR_Y, oz), color=_rgb(color, fr, fg, fb), **floor_kw,
    ))
    # Ceiling light strips (brighter)
    parts.append(Entity(
        model='cube', scale=(max(1.5, w * 0.55), 0.07, 0.22),
        position=(ox, 2.65, oz), color=_rgb(color, 255, 252, 235),
    ))
    if w > 5.0:
        parts.append(Entity(
            model='cube', scale=(max(1.0, w * 0.35), 0.05, 0.16),
            position=(ox, 2.55, oz + d * 0.2), color=_rgb(color, 255, 245, 220),
        ))

    if style == 'house':
        parts.append(_prop(Entity, (ox - 1.5, 0.45, oz + 1.0), (2.0, 0.4, 1.4), _rgb(color, 225, 215, 205)))
        parts.append(_prop(Entity, (ox + 1.8, 0.9, oz + 0.4), (1.1, 1.5, 0.55), _rgb(color, 95, 72, 55),
                           texture=shelf_tex, texture_scale=(1.2, 1.5)))
        parts.append(_prop(Entity, (ox + 0.2, 0.55, oz - 1.2), (1.5, 0.7, 0.7), _rgb(color, 185, 155, 125)))
        # side table lamp glow
        parts.append(_prop(Entity, (ox - 1.5, 0.85, oz + 1.0), (0.25, 0.35, 0.25), _rgb(color, 255, 230, 180)))
    elif style == 'spa':
        parts.append(_prop(Entity, (ox, 0.45, oz), (1.8, 0.5, 0.9), _rgb(color, 205, 225, 225)))
        parts.append(_prop(Entity, (ox - 1.8, 0.7, oz + 1.0), (0.7, 1.1, 0.7), _rgb(color, 125, 100, 60)))
        parts.append(_prop(Entity, (ox + 1.6, 0.55, oz - 0.6), (0.9, 0.9, 0.7), _rgb(color, 170, 200, 195)))
        parts.append(Entity(model='cube', scale=(1.4, 0.08, 0.08),
                            position=(ox, 2.4, oz + 0.8), color=_rgb(color, 180, 230, 215)))
    elif style == 'club':
        # bar counter: top + front face
        parts.append(_prop(Entity, (ox, 0.55, oz + 1.0), (3.5, 0.7, 1.0), _rgb(color, 95, 22, 55)))
        parts.append(_prop(Entity, (ox, 0.95, oz + 1.0), (3.6, 0.08, 1.05), _rgb(color, 40, 12, 30)))
        parts.append(Entity(model='cube', scale=(max(2.0, w - 1.5), 0.1, 0.1),
                            position=(ox, 2.5, oz + d / 2 - 0.5),
                            color=_rgb(color, 255, 50, 170)))
        for dx in (-1.5, 1.5):
            parts.append(_prop(Entity, (ox + dx, 0.4, oz - 0.8), (0.7, 0.55, 0.7), _rgb(color, 45, 12, 35)))
        # bottle shelf
        parts.append(_prop(Entity, (ox, 1.5, oz + 1.5), (2.4, 0.8, 0.3), _rgb(color, 60, 20, 40)))
        parts.extend(_shelf_stock(Entity, color, ox, oz, 0.0, 1.55, 1.35, n=4))
    elif style == 'shop':
        # counter + register top
        parts.append(_prop(Entity, (ox, 0.55, oz + 0.6), (2.8, 0.85, 0.7), _rgb(color, 52, 52, 62)))
        parts.append(_prop(Entity, (ox, 1.02, oz + 0.6), (2.9, 0.08, 0.75), _rgb(color, 70, 70, 80)))
        parts.append(_prop(Entity, (ox - 1.5, 0.9, oz - 0.4), (0.8, 1.5, 0.5), _rgb(color, 75, 95, 55),
                           texture=shelf_tex, texture_scale=(1, 1.5)))
        parts.extend(_shelf_stock(Entity, color, ox, oz, -1.5, 1.1, -0.15, n=3))
        parts.append(_prop(Entity, (ox + 1.4, 0.9, oz - 0.3), (0.7, 1.4, 0.45), _rgb(color, 80, 70, 55)))
    elif style == 'walmart':
        for dx in (-5.0, -2.0, 2.0, 5.0):
            parts.append(_prop(Entity, (ox + dx, 1.0, oz + 0.5), (1.1, 1.9, 5.0), _rgb(color, 232, 232, 238),
                               texture=shelf_tex, texture_scale=(1, 2)))
            # stock on aisle face toward center
            face = -0.55 if dx > 0 else 0.55
            parts.extend(_shelf_stock(Entity, color, ox, oz, dx + face, 1.2, 0.5, n=3))
            parts.extend(_shelf_stock(Entity, color, ox, oz, dx + face, 0.7, -0.8, n=3))
        # blue register counter
        parts.append(_prop(Entity, (ox, 0.55, oz - d / 2 + 2.0), (4.0, 0.9, 1.0), _rgb(color, 0, 113, 206)))
        parts.append(_prop(Entity, (ox, 1.05, oz - d / 2 + 2.0), (4.1, 0.08, 1.05), _rgb(color, 20, 90, 170)))
        parts.append(Entity(model='cube', scale=(3.8, 0.55, 0.12),
                            position=(ox, 2.55, oz + d / 2 - 0.4),
                            color=_rgb(color, 255, 194, 32)))
    elif style == 'retail':
        for dx in (-2.2, 0.0, 2.2):
            if abs(dx) > w / 2 - 0.8:
                continue
            parts.append(_prop(Entity, (ox + dx, 0.95, oz + 0.3), (0.9, 1.7, max(2.5, d * 0.55)),
                               _rgb(color, 225, 225, 235), texture=shelf_tex, texture_scale=(1, 1.8)))
            parts.extend(_shelf_stock(Entity, color, ox, oz, dx, 1.15, 0.0, n=3))
            parts.extend(_shelf_stock(Entity, color, ox, oz, dx, 0.65, -0.6, n=2))
        # counter: body + top
        cw = min(3.2, w * 0.55)
        parts.append(_prop(Entity, (ox, 0.55, oz - d / 2 + 1.6), (cw, 0.85, 0.8),
                           _rgb(color, 42, 42, 52)))
        parts.append(_prop(Entity, (ox, 1.02, oz - d / 2 + 1.6), (cw + 0.1, 0.08, 0.85),
                           _rgb(color, 60, 60, 72)))
    elif style == 'tire':
        parts.append(_prop(Entity, (ox, 0.65, oz + 0.5), (3.2, 1.1, 1.6), _rgb(color, 62, 62, 68),
                           texture=shelf_tex, texture_scale=(2, 1)))
        for dx in (-1.8, 1.8):
            for k in range(3):
                parts.append(_prop(Entity, (ox + dx, 0.22 + k * 0.2, oz - 1.0),
                                   (0.55, 0.18, 0.55), _rgb(color, 22, 22, 22)))
        parts.append(_prop(Entity, (ox, 0.55, oz - d / 2 + 1.5), (2.6, 0.85, 0.7),
                           _rgb(color, 255, 107, 0)))
        parts.append(_prop(Entity, (ox, 1.02, oz - d / 2 + 1.5), (2.7, 0.08, 0.75),
                           _rgb(color, 255, 140, 40)))
        # wall tool board
        parts.append(_prop(Entity, (ox + 2.2, 1.4, oz + 0.8), (0.12, 1.2, 1.6), _rgb(color, 90, 90, 95)))
    elif style == 'nail':
        for dx in (-1.8, 0.0, 1.8):
            if abs(dx) > w / 2 - 0.7:
                continue
            parts.append(_prop(Entity, (ox + dx, 0.5, oz + 0.5), (1.0, 0.85, 1.2),
                               _rgb(color, 255, 155, 195)))
            parts.append(_prop(Entity, (ox + dx, 0.95, oz + 0.5), (1.05, 0.06, 1.25),
                               _rgb(color, 255, 200, 220)))
        parts.append(_prop(Entity, (ox, 0.45, oz - d / 2 + 1.5), (2.6, 0.65, 0.7),
                           _rgb(color, 255, 105, 180)))
        parts.append(Entity(model='cube', scale=(2.2, 0.12, 0.12),
                            position=(ox, 2.4, oz + 0.8), color=_rgb(color, 255, 90, 190)))
        parts.extend(_shelf_stock(Entity, color, ox, oz, 0.0, 1.3, 1.2, n=4))
    elif style == 'shake':
        parts.append(_prop(Entity, (ox, 0.5, oz + 0.3), (min(2.4, w * 0.7), 0.8, 0.55),
                           _rgb(color, 255, 125, 185)))
        parts.append(_prop(Entity, (ox, 0.95, oz + 0.3), (min(2.5, w * 0.72), 0.06, 0.58),
                           _rgb(color, 255, 180, 210)))
        parts.append(_prop(Entity, (ox - w * 0.25, 0.85, oz - 0.2), (0.5, 1.3, 0.4),
                           _rgb(color, 85, 205, 255)))
        parts.extend(_shelf_stock(Entity, color, ox, oz, -w * 0.25, 1.2, -0.05, n=2))
        parts.append(Entity(model='cube', scale=(min(1.8, w * 0.5), 0.08, 0.08),
                            position=(ox, 2.2, oz), color=_rgb(color, 255, 90, 210)))

    # Readable signage plaque (replaces bare floating Text alone)
    z_off = (d / 2 - 0.55) if style != 'house' else 0.0
    parts.extend(_sign_plaque(Entity, color, Text, ox, oz, title, y=2.55, z_off=z_off,
                              w=min(3.2, max(1.8, w * 0.45))))
    return parts


def build_all(game):
    Entity = game.Entity
    color = game.color
    Text = getattr(game, 'Text', None)
    game.interiors = {}
    game.interior_doors = []  # kept for API compat; no teleport mats
    game.active_interior = None
    game.interior_return_pos = None

    # Specs: co-located with exterior footprints (resolve live positions when possible)
    specs = [
        dict(id='sanctuary', title='Sanctuary Drive — Inside', style='house',
             fixed=(-32.0, 12.0), w=7.2, d=5.6, shop_id=None, door_face='e'),
        dict(id='quiet_spa', title='Quiet Spa — Treatment Room', style='spa',
             poi_id='quiet_spa', fixed=(-36.0, -16.0), w=5.4, d=3.6, shop_id=None),
        dict(id='club27', title='Club 27 — Lounge', style='club',
             poi_id='club27', fixed=(40.0, -20.0), w=8.5, d=5.5, shop_id=None),
        dict(id='gas_shop', title='Hancock Gas — Counter', style='shop',
             poi_id='gas', fixed=(18.0, -8.0), w=4.5, d=3.2, shop_id=None),
        dict(id='walmart', title='Walmart Supercenter', style='walmart',
             poi_id='walmart', fixed=(62.0, -18.0), w=18.0, d=11.0,
             shop_id='walmart_clermont'),
        dict(id='pet_store', title='Paws on 50 — Aisles', style='retail',
             stall_id='pet_store_clermont', fixed=(-22.0, 6.5), w=6.2, d=4.5,
             shop_id='pet_store_clermont'),
        dict(id='bestbuy', title='Best Buy — Floor', style='retail',
             stall_id='bestbuy_clermont', fixed=(28.0, 7.5), w=9.0, d=6.0,
             shop_id='bestbuy_clermont'),
        dict(id='gamestop', title='GameStop — Floor', style='retail',
             stall_id='gamestop_clermont', fixed=(8.0, 6.0), w=5.2, d=4.2,
             shop_id='gamestop_clermont'),
        dict(id='tire_shop', title='Hwy 50 Tire & Lube', style='tire',
             stall_id='tire_shop_clermont', fixed=(42.0, -6.5), w=6.2, d=4.5,
             shop_id='tire_shop_clermont'),
        dict(id='nail_salon', title='Neon Toes Nail Salon', style='nail',
             stall_id='nail_salon_clermont', fixed=(-14.0, 7.2), w=5.5, d=4.2,
             shop_id='nail_salon_clermont'),
    ]

    # Shake bars — main walk-in set from spawned stalls
    for stall in getattr(game, 'stalls', []) or []:
        if stall.get('kind') != 'shake':
            continue
        sid = stall.get('id') or ''
        pos = stall.get('pos')
        if not pos:
            continue
        specs.append(dict(
            id='shake_' + sid,
            title=(stall.get('name') or sid) + ' — Counter',
            style='shake',
            stall_id=sid,
            fixed=(float(pos[0]), float(pos[2]) + 1.2),
            w=2.6, d=2.2,
            shop_id=sid,
        ))

    for spec in specs:
        iid = spec['id']
        ox, oz = _resolve_xz(
            game,
            stall_id=spec.get('stall_id'),
            poi_id=spec.get('poi_id'),
            fixed=spec.get('fixed'),
        )
        # Sanctuary: exact house center
        if iid == 'sanctuary':
            sp = getattr(game, 'sanctuary_pos', None)
            if sp:
                ox, oz = float(sp[0]), float(sp[2])
        w = float(spec.get('w', 8.0))
        d = float(spec.get('d', 6.0))
        parts = _fill_props(Entity, color, Text, ox, oz, spec['style'], spec['title'], w, d)

        # Subtle door mat (visual only — NOT a teleport trigger)
        door_face = spec.get('door_face', 's')
        if door_face == 'e':
            mat_pos = (ox + w / 2 + 0.35, 0.04, oz)
            mat_scale = (1.1, 0.06, 1.4)
        else:
            mat_pos = (ox, 0.04, oz - d / 2 - 0.35)
            mat_scale = (1.4, 0.06, 1.1)
        mat = Entity(model='cube', scale=mat_scale, position=mat_pos,
                     color=_rgb(color, 255, 170, 90))
        mat.kind = 'walkin_mat'
        mat.interior_id = iid
        parts.append(mat)

        game.interiors[iid] = {
            'id': iid,
            'title': spec['title'],
            'origin': (ox, 0.0, oz),
            'spawn': (ox, 0.0, oz),  # unused — no teleport
            'exit': None,
            'parts': parts,
            'shop_id': spec.get('shop_id'),
            'door_pos': mat_pos,
            'return_pos': mat_pos,
            'half_w': w * 0.45,
            'half_d': d * 0.45,
            'walk_in': True,
        }

    print('  interiors: %d walk-in rooms (no pocket teleport)' % len(game.interiors))


def _inside(inter, pos):
    ox, _, oz = inter['origin']
    hw = float(inter.get('half_w', 3.0))
    hd = float(inter.get('half_d', 2.5))
    return abs(pos[0] - ox) <= hw and abs(pos[2] - oz) <= hd


def _update_active(game, pos):
    """Set active_interior from physical position (true walk-in)."""
    best = None
    for iid, inter in (game.interiors or {}).items():
        if _inside(inter, pos):
            best = iid
            break
    prev = getattr(game, 'active_interior', None)
    game.active_interior = best
    if best and best != prev:
        title = (game.interiors.get(best) or {}).get('title')
        if title and not getattr(game, '_interior_toast_id', None) == best:
            game._interior_toast_id = best
            try:
                game.toast(title)
            except Exception:
                pass
    if not best:
        game._interior_toast_id = None
    return best


def nearest_door(game, pos, radius=2.8):
    """Near a walk-in mat (prompt only — no teleport)."""
    best, best_d = None, radius
    for inter in (getattr(game, 'interiors', {}) or {}).values():
        dp = inter.get('door_pos')
        if not dp:
            continue
        d = math.hypot(pos[0] - dp[0], pos[2] - dp[2])
        if d < best_d:
            # fake marker-like object
            class _M:
                pass
            m = _M()
            m.x, m.z = dp[0], dp[2]
            m.interior_id = inter['id']
            m.prompt = 'Walk in  ·  E shop' if inter.get('shop_id') else 'Walk in'
            best, best_d = m, d
    return best, best_d


def prompt(game, pos):
    active = _update_active(game, pos)
    if active:
        inter = (game.interiors or {}).get(active) or {}
        if inter.get('shop_id') == 'tire_shop_clermont':
            return 'E  tire service'
        if inter.get('shop_id') == 'nail_salon_clermont':
            return 'E  pedicure lounge'
        if inter.get('shop_id'):
            return 'E  shop shelves'
        return 'Inside  ·  walk out to leave'
    door, _d = nearest_door(game, pos, 2.2)
    if door:
        return getattr(door, 'prompt', 'Walk in')
    return ''


def try_interact(game):
    pos = game._actor_pos()
    active = _update_active(game, pos)
    if active:
        inter = (game.interiors or {}).get(active) or {}
        if inter.get('shop_id'):
            _open_shop(game, inter['shop_id'])
            return True
        game.toast(inter.get('title') or 'Inside. Walk out the door to leave.')
        return True
    # Near doorway but not yet inside — nudge
    door, d = nearest_door(game, pos, 2.2)
    if door:
        game.toast('Walk through the doorway.')
        return True
    return False


def _open_shop(game, shop_id):
    shops = list((getattr(game, 'shops_data', None) or {}).get('shops') or [])
    shop = next((s for s in shops if s.get('id') == shop_id), None)
    if not shop:
        # shake stalls may only live on game.stalls
        stall = next((s for s in (getattr(game, 'stalls', []) or []) if s.get('id') == shop_id), None)
        if stall and hasattr(game, 'open_shake_shop'):
            game.open_shake_shop(stall)
            return
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
