"""Shared texture/color helpers for models3d."""
from __future__ import annotations

_WORLD_TEX = {}


def set_world_textures(tex_map=None):
    """Register textures: grass, asphalt, concrete, brick, stucco, water."""
    _WORLD_TEX.clear()
    if tex_map:
        _WORLD_TEX.update(tex_map)


def _t(name):
    return _WORLD_TEX.get(name)


def _rgb(color, r, g, b):
    return color.rgb32(r, g, b)
