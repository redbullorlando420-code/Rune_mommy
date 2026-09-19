"""Composed Ursina meshes for Rune Mommy — houses, stalls, humanoids, cars, POIs.

Prefer primitives (cube/sphere/cylinder/quad). Keeps draw cost modest.
"""
from __future__ import annotations

import math
import random

_MESH_CACHE = {}

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


def round_cylinder(segments=16):
    """Return a project-local capped cylinder mesh; never depends on a named asset."""
    key = ('cylinder', int(segments))
    if key in _MESH_CACHE:
        return _MESH_CACHE[key]
    from ursina import Mesh
    segments = max(6, int(segments))
    vertices = []
    uvs = []
    for y in (-0.5, 0.5):
        for i in range(segments):
            angle = math.tau * i / segments
            vertices.append((math.cos(angle), y, math.sin(angle)))
            uvs.append((i / segments, 0 if y < 0 else 1))
    bottom_center, top_center = len(vertices), len(vertices) + 1
    vertices.extend(((0, -0.5, 0), (0, 0.5, 0)))
    uvs.extend(((0.5, 0.5), (0.5, 0.5)))
    triangles = []
    for i in range(segments):
        nxt = (i + 1) % segments
        triangles.extend(((i, nxt, segments + nxt), (i, segments + nxt, segments + i)))
        triangles.append((bottom_center, nxt, i))
        triangles.append((top_center, segments + i, segments + nxt))
    _MESH_CACHE[key] = Mesh(vertices=vertices, triangles=triangles, uvs=uvs, mode='triangle', static=True)
    return _MESH_CACHE[key]


def round_head(segments=24, rings=16):
    """Higher-density UV sphere for hero and named-character heads."""
    key = ('head', int(segments), int(rings))
    if key in _MESH_CACHE:
        return _MESH_CACHE[key]
    from ursina import Mesh
    segments, rings = max(8, int(segments)), max(6, int(rings))
    vertices = []
    for row in range(rings + 1):
        phi = math.pi * row / rings
        y = math.cos(phi) * 0.5
        radius = math.sin(phi) * 0.5
        for col in range(segments):
            theta = math.tau * col / segments
            vertices.append((math.cos(theta) * radius, y, math.sin(theta) * radius))
    triangles = []
    for row in range(rings):
        for col in range(segments):
            nxt = (col + 1) % segments
            a = row * segments + col
            b = row * segments + nxt
            c = (row + 1) * segments + col
            d = (row + 1) * segments + nxt
            triangles.extend(((a, b, d), (a, d, c)))
    _MESH_CACHE[key] = Mesh(vertices=vertices, triangles=triangles, mode='triangle', static=True)
    return _MESH_CACHE[key]


def _pitched_roof(Entity, color, x, y, z, w, d, roof_col, pitch=0.35):
    """Stable low-pitch roof cap with a ridge; never uses detached rotations."""
    edge = roof_col.tint(0.1) if hasattr(roof_col, 'tint') else roof_col
    # Rotated primitive slabs produced inverted/floating roofs on some Panda
    # builds. A stepped cap and ridge preserve the suburban silhouette using
    # only stable axis-aligned geometry.
    Entity(model='cube', scale=(w + 0.28, 0.18, d + 0.28), position=(x, y, z), color=roof_col)
    Entity(model='cube', scale=(w * 0.72, 0.15, d * 0.72), position=(x, y + 0.14, z), color=edge)
    Entity(model='cube', scale=(w * 0.14, 0.11, d + 0.16), position=(x, y + 0.24, z), color=edge)
