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


def _rgb(color, r, g, b):
    return color.rgb32(r, g, b)


def _pitched_roof(Entity, color, x, y, z, w, d, roof_col, pitch=0.35):
    """Two rotated cubes forming a simple pitched roof."""
    Entity(model='cube', scale=(w * 0.55, 0.22, d + 0.15), position=(x - w * 0.22, y, z),
           color=roof_col, rotation_z=pitch * 55)
    Entity(model='cube', scale=(w * 0.55, 0.22, d + 0.15), position=(x + w * 0.22, y, z),
           color=roof_col, rotation_z=-pitch * 55)
    Entity(model='cube', scale=(0.18, 0.14, d + 0.2), position=(x, y + 0.35, z),
           color=roof_col.tint(0.1) if hasattr(roof_col, 'tint') else roof_col)
