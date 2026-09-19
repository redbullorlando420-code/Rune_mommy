"""Composed Ursina meshes for Rune Mommy — houses, stalls, humanoids, cars, POIs.

Prefer primitives (cube/sphere/cylinder/quad). Keeps draw cost modest.
"""
from __future__ import annotations

import math
import random

# Optional world textures set by game.load_tex / set_world_textures (tint + texture).
_WORLD_TEX = {}

# star-imports skip _names unless listed here
__all__ = [
    'set_world_textures',
    '_t',
    '_safe_tex',
    'hollow_shell',
    '_rgb',
    '_pitched_roof',
    'random',
    'math',
]


def set_world_textures(tex_map=None):
    """Register textures: grass, asphalt, concrete, brick, stucco, water."""
    _WORLD_TEX.clear()
    if tex_map:
        _WORLD_TEX.update(tex_map)


def _t(name):
    return _WORLD_TEX.get(name)


def _safe_tex(*names):
    """First registered texture that is not a bare path string (avoids pink/miss)."""
    for name in names:
        t = _WORLD_TEX.get(name)
        if t is not None and not isinstance(t, str):
            return t
    return None


def _rgb(color, r, g, b):
    return color.rgb32(r, g, b)


def _pitched_roof(Entity, color, x, y, z, w, d, roof_col, pitch=0.35):
    """Reliable A-frame: ridge above walls, left/right slopes, thin ridge beam.

    `y` should be wall-top (e.g. h); ridge sits at y + 0.55. pitch unused (kept for API).
    """
    ridge_y = y + 0.55
    # Left slope (+28) and right slope (-28). Flip signs if Ursina still looks inverted.
    # Left slope (-28) / right (+28) → ridge UP in Ursina (was inverted with opposite signs)
    Entity(model='cube', scale=(w * 0.58, 0.16, d + 0.18), position=(x - w * 0.22, ridge_y - 0.12, z),
           color=roof_col, rotation_z=-28)
    Entity(model='cube', scale=(w * 0.58, 0.16, d + 0.18), position=(x + w * 0.22, ridge_y - 0.12, z),
           color=roof_col, rotation_z=28)
    # Thin ridge beam on top
    Entity(model='cube', scale=(0.16, 0.12, d + 0.25), position=(x, ridge_y + 0.08, z),
           color=roof_col.tint(0.1) if hasattr(roof_col, 'tint') else roof_col)


def hollow_shell(Entity, color, x, z, w, d, h, wall_col, *,
                 door_gap=1.6, door_face='s', floor_col=None, ceil_col=None,
                 wall_tex=None, floor_tex=None, thick=0.22):
    """Walk-in room shell co-located with footprint. Door gap has NO collider.

    door_face: 's' open toward -Z (storefront), 'e' open toward +X (Sanctuary).
    Returns (parts_count, door_world_xz).
    """
    n = 0
    floor_col = floor_col or _rgb(color, 70, 68, 72)
    ceil_col = ceil_col or _rgb(color, 220, 220, 225)
    kw_w = {}
    if wall_tex is not None:
        kw_w['texture'] = wall_tex
        kw_w['texture_scale'] = (2.5, 1.5)
    kw_f = {}
    if floor_tex is not None:
        kw_f['texture'] = floor_tex
        kw_f['texture_scale'] = (3, 2)
    # floor + ceiling (no wall collider on floor)
    Entity(model='cube', scale=(w, 0.08, d), position=(x, 0.04, z),
           color=floor_col, **kw_f)
    n += 1
    Entity(model='cube', scale=(w, 0.08, d), position=(x, h - 0.04, z), color=ceil_col)
    n += 1
    # back / sides depend on door face
    if door_face == 'e':
        # open +X: back=-X, sides=+/-Z, front split on +X
        Entity(model='cube', scale=(thick, h, d), position=(x - w / 2 + thick / 2, h / 2, z),
               color=wall_col, collider='box', **kw_w)
        Entity(model='cube', scale=(w, h, thick), position=(x, h / 2, z - d / 2 + thick / 2),
               color=wall_col, collider='box', **kw_w)
        Entity(model='cube', scale=(w, h, thick), position=(x, h / 2, z + d / 2 - thick / 2),
               color=wall_col, collider='box', **kw_w)
        n += 3
        span = max(0.4, (d - door_gap) / 2.0)
        Entity(model='cube', scale=(thick, h, span),
               position=(x + w / 2 - thick / 2, h / 2, z - door_gap / 2 - span / 2),
               color=wall_col, collider='box', **kw_w)
        Entity(model='cube', scale=(thick, h, span),
               position=(x + w / 2 - thick / 2, h / 2, z + door_gap / 2 + span / 2),
               color=wall_col, collider='box', **kw_w)
        n += 2
        door_xz = (x + w / 2 + 0.3, z)
    else:
        # open -Z (south storefront)
        Entity(model='cube', scale=(w, h, thick), position=(x, h / 2, z + d / 2 - thick / 2),
               color=wall_col, collider='box', **kw_w)
        Entity(model='cube', scale=(thick, h, d), position=(x - w / 2 + thick / 2, h / 2, z),
               color=wall_col, collider='box', **kw_w)
        Entity(model='cube', scale=(thick, h, d), position=(x + w / 2 - thick / 2, h / 2, z),
               color=wall_col, collider='box', **kw_w)
        n += 3
        span = max(0.4, (w - door_gap) / 2.0)
        Entity(model='cube', scale=(span, h, thick),
               position=(x - door_gap / 2 - span / 2, h / 2, z - d / 2 + thick / 2),
               color=wall_col, collider='box', **kw_w)
        Entity(model='cube', scale=(span, h, thick),
               position=(x + door_gap / 2 + span / 2, h / 2, z - d / 2 + thick / 2),
               color=wall_col, collider='box', **kw_w)
        n += 2
        door_xz = (x, z - d / 2 - 0.2)
    return n, door_xz

