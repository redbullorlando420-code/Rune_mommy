"""Japan / Akihabara building kits — narrow tall shops, neon JP billboards, arcade.

Distinct from Florida stucco/Hwy kits. Flat roofs + upright sign towers only
(no pitched A-frame — avoids upside-down roof risk).
"""
from __future__ import annotations

from models3d._base import _rgb, _t


Y_STREET = 0.03
Y_SIDEWALK = 0.06


def _flat_roof(Entity, color, x, y, z, w, d, col, lip=0.12):
    """Simple upright flat roof slab + thin lip (never inverted)."""
    Entity(model='cube', scale=(w, 0.12, d), position=(x, y, z), color=col)
    Entity(
        model='cube', scale=(w + lip, 0.06, d + lip),
        position=(x, y + 0.08, z),
        color=col.tint(0.08) if hasattr(col, 'tint') else col,
    )


def make_torii_portal(Entity, color, Text, scene_parent, x, z, *, label='AKIHABARA', yaw=0):
    """Japan-flavored gate/arch marking a teleport portal. Returns (n, interact_pos)."""
    n = 0
    vermillion = _rgb(color, 210, 55, 40)
    black = _rgb(color, 24, 20, 22)
    gold = _rgb(color, 240, 200, 80)
    # pillars
    for sx in (-1.35, 1.35):
        Entity(model='cube', scale=(0.28, 3.4, 0.28), position=(x + sx, 1.7, z),
               color=vermillion, rotation_y=yaw, collider='box')
        n += 1
    # crossbeams
    Entity(model='cube', scale=(3.4, 0.22, 0.35), position=(x, 3.15, z),
           color=vermillion, rotation_y=yaw)
    Entity(model='cube', scale=(3.8, 0.18, 0.28), position=(x, 3.45, z),
           color=vermillion, rotation_y=yaw)
    n += 2
    # kasagi tips
    Entity(model='cube', scale=(0.35, 0.18, 0.28), position=(x - 1.95, 3.45, z), color=black)
    Entity(model='cube', scale=(0.35, 0.18, 0.28), position=(x + 1.95, 3.45, z), color=black)
    n += 2
    # glowing mat (walk-in / E)
    mat = Entity(model='cube', scale=(2.2, 0.08, 2.2), position=(x, 0.05, z),
                 color=_rgb(color, 255, 80, 160))
    mat.kind = 'tokyo_portal'
    n += 1
    # sign plate
    Entity(model='cube', scale=(2.4, 0.55, 0.08), position=(x, 2.55, z - 0.2),
           color=black, rotation_y=yaw)
    Entity(model='cube', scale=(2.2, 0.12, 0.06), position=(x, 2.75, z - 0.22),
           color=gold, rotation_y=yaw)
    n += 2
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=label, position=(x, 4.0, z), origin=(0, 0),
                 billboard=True, color=gold)
        try:
            t.world_scale = 2.2
        except Exception:
            pass
        n += 1
    return n, (x, 0, z)


def make_jp_narrow_shop(Entity, color, Text, scene_parent, x, z, *, name='SHOP',
                        w=2.4, d=3.2, floors=3, body_rgb=(40, 42, 55),
                        neon_rgb=(255, 40, 160), sign='店', yaw=0):
    """Tall narrow electronics/anime storefront — denser than Florida strip malls."""
    n = 0
    h = 2.2 * floors
    body = _rgb(color, *body_rgb)
    neon = _rgb(color, *neon_rgb)
    dark = _rgb(color, 18, 18, 24)
    glass = _rgb(color, 120, 200, 230)
    # tower body
    Entity(model='cube', scale=(w, h, d), position=(x, h / 2, z), color=body,
           texture=_t('concrete') or _t('metal'), texture_scale=(1.4, floors),
           rotation_y=yaw, collider='box')
    n += 1
    _flat_roof(Entity, color, x, h + 0.05, z, w + 0.15, d + 0.15, dark)
    n += 2
    # floor band neon
    for fi in range(floors):
        fy = 0.9 + fi * 2.2
        Entity(model='cube', scale=(w + 0.08, 0.08, 0.1),
               position=(x, fy, z - d / 2 - 0.02), color=neon, rotation_y=yaw)
        Entity(model='cube', scale=(w * 0.7, 0.7, 0.06),
               position=(x, fy + 0.55, z - d / 2 - 0.03), color=glass, rotation_y=yaw)
        n += 2
    # vertical sign tower
    Entity(model='cube', scale=(0.35, h * 0.85, 0.12),
           position=(x - w / 2 - 0.25, h * 0.45, z - d / 2 + 0.2),
           color=neon, rotation_y=yaw)
    Entity(model='cube', scale=(0.32, 0.5, 0.08),
           position=(x - w / 2 - 0.25, h * 0.85, z - d / 2 + 0.2),
           color=dark, rotation_y=yaw)
    n += 2
    # ground entry recess
    Entity(model='cube', scale=(w * 0.55, 1.8, 0.4),
           position=(x, 0.9, z - d / 2 - 0.15), color=_rgb(color, 30, 30, 40),
           rotation_y=yaw)
    n += 1
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=name[:18], position=(x, h + 0.6, z),
                 origin=(0, 0), billboard=True, color=neon)
        try:
            t.world_scale = 1.6
        except Exception:
            pass
        s = Text(parent=scene_parent, text=sign, position=(x - w / 2 - 0.25, h * 0.55, z - d / 2 + 0.25),
                 origin=(0, 0), billboard=True, color=_rgb(color, 255, 255, 220))
        try:
            s.world_scale = 1.3
        except Exception:
            pass
        n += 2
    interact = (x, 0, z - d / 2 - 1.1)
    return n, interact


def make_neon_billboard_jp(Entity, color, Text, scene_parent, x, z, text='秋葉原',
                           face_yaw=0, neon_rgb=(80, 255, 200)):
    """Tall JP-style billboard / LED wall."""
    n = 0
    neon = _rgb(color, *neon_rgb)
    dark = _rgb(color, 16, 16, 22)
    Entity(model='cube', scale=(0.2, 4.5, 0.2), position=(x, 2.25, z), color=dark)
    Entity(model='cube', scale=(3.6, 2.2, 0.15), position=(x, 3.6, z),
           color=dark, rotation_y=face_yaw)
    Entity(model='cube', scale=(3.5, 2.05, 0.08), position=(x, 3.6, z - 0.02),
           color=neon, rotation_y=face_yaw)
    n += 3
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=text, position=(x, 3.6, z), origin=(0, 0),
                 billboard=True, color=_rgb(color, 10, 10, 20))
        try:
            t.world_scale = 2.0
        except Exception:
            pass
        n += 1
    return n


def make_covered_arcade(Entity, color, Text, scene_parent, x, z, *, length=28.0, width=6.0,
                        name='Electric Town'):
    """Covered shopping street vibe — canopy over a walk spine."""
    n = 0
    canopy = _rgb(color, 55, 50, 70)
    frame = _rgb(color, 200, 60, 90)
    # floor
    Entity(model='cube', scale=(width, 0.05, length), position=(x, Y_STREET, z),
           color=_rgb(color, 45, 45, 52), texture=_t('asphalt') or _t('concrete'),
           texture_scale=(2, 6))
    n += 1
    # canopy roof (flat, upright)
    Entity(model='cube', scale=(width + 0.4, 0.12, length), position=(x, 3.4, z), color=canopy)
    n += 1
    # support posts + neon edge
    step = 4.0
    half_l = length / 2
    i = -half_l + 2
    while i <= half_l - 2:
        for sx in (-width / 2 + 0.2, width / 2 - 0.2):
            Entity(model='cube', scale=(0.15, 3.3, 0.15), position=(x + sx, 1.65, z + i),
                   color=frame)
            n += 1
        Entity(model='cube', scale=(width, 0.06, 0.08), position=(x, 3.35, z + i),
               color=_rgb(color, 255, 90, 180))
        n += 1
        i += step
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=name, position=(x, 3.9, z - half_l + 1.5),
                 origin=(0, 0), billboard=True, color=_rgb(color, 255, 200, 230))
        try:
            t.world_scale = 2.4
        except Exception:
            pass
        n += 1
    return n


def make_station_facade(Entity, color, Text, scene_parent, x, z, *, name='Akihabara Station'):
    """Rail / station cue — wide facade + canopy + track hint."""
    n = 0
    silver = _rgb(color, 180, 185, 195)
    green = _rgb(color, 40, 160, 90)
    dark = _rgb(color, 30, 32, 40)
    Entity(model='cube', scale=(16.0, 5.0, 6.0), position=(x, 2.5, z), color=silver,
           texture=_t('concrete') or _t('metal'), texture_scale=(3, 1.5), collider='box')
    n += 1
    _flat_roof(Entity, color, x, 5.1, z, 16.4, 6.4, dark)
    n += 2
    # JR-ish green band
    Entity(model='cube', scale=(16.2, 0.45, 0.2), position=(x, 4.4, z - 3.05), color=green)
    n += 1
    # entry glass
    Entity(model='cube', scale=(5.0, 2.8, 0.15), position=(x, 1.5, z - 3.1),
           color=_rgb(color, 140, 200, 230))
    n += 1
    # canopy
    Entity(model='cube', scale=(8.0, 0.12, 2.2), position=(x, 2.9, z - 4.2), color=silver)
    n += 1
    # track hint behind
    Entity(model='cube', scale=(18.0, 0.2, 1.2), position=(x, 0.35, z + 4.2),
           color=_rgb(color, 50, 50, 55))
    Entity(model='cube', scale=(18.0, 0.08, 0.15), position=(x, 0.5, z + 3.8),
           color=_rgb(color, 180, 160, 40))
    Entity(model='cube', scale=(18.0, 0.08, 0.15), position=(x, 0.5, z + 4.6),
           color=_rgb(color, 180, 160, 40))
    n += 3
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=name, position=(x, 5.8, z), origin=(0, 0),
                 billboard=True, color=_rgb(color, 40, 200, 120))
        try:
            t.world_scale = 2.8
        except Exception:
            pass
        n += 1
    return n, (x, 0, z - 4.5)


def make_donki_box(Entity, color, Text, scene_parent, x, z, *, name='Don Quijote'):
    """Donki-style loud box with crazy sign spine."""
    n = 0
    red = _rgb(color, 200, 30, 40)
    yellow = _rgb(color, 255, 220, 40)
    white = _rgb(color, 240, 240, 245)
    Entity(model='cube', scale=(8.0, 4.5, 6.0), position=(x, 2.25, z), color=white,
           texture=_t('stucco') or _t('concrete'), texture_scale=(2, 1.5), collider='box')
    n += 1
    _flat_roof(Entity, color, x, 4.6, z, 8.3, 6.3, red)
    n += 2
    # clownish vertical signs
    for i, sx in enumerate((-3.2, -1.0, 1.2, 3.0)):
        col = yellow if i % 2 == 0 else red
        Entity(model='cube', scale=(1.4, 3.8, 0.2), position=(x + sx, 2.4, z - 3.1), color=col)
        n += 1
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=name, position=(x, 5.3, z), origin=(0, 0),
                 billboard=True, color=yellow)
        try:
            t.world_scale = 2.2
        except Exception:
            pass
        n += 1
    return n, (x, 0, z - 3.8)
