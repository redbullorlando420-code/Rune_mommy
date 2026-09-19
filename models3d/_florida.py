"""Low-poly Florida set dressing built from Ursina's MIT-licensed primitives.

The game intentionally keeps these as composed meshes instead of shipping an
unvetted third-party asset pack: they load immediately, have no licensing
ambiguity, and remain inexpensive enough for the Highway 50 scene.
"""
from __future__ import annotations

import math
import random

from models3d._base import _rgb, _t, round_cylinder


def _palm(Entity, color, x, z, height=6.0, lean=0.0):
    """A tapered trunk plus eight broad fronds; one root entity per tree."""
    root = Entity(position=(x, 0, z), rotation_z=lean)
    bark = _rgb(color, 91, 62, 38)
    leaf = _rgb(color, 36, 116, 57)
    leaf_light = _rgb(color, 64, 148, 74)
    Entity(parent=root, model=round_cylinder(14), scale=(0.22, height, 0.22), y=height * 0.5,
           color=bark, texture=_t('brick'))
    # Trunk bands make even a distant palm read as a real object, not a pole.
    for y in range(1, int(height), 2):
        Entity(parent=root, model=round_cylinder(14), scale=(0.255, 0.045, 0.255), y=y,
               color=_rgb(color, 120, 86, 51))
    for i in range(8):
        yaw = i * 45.0
        frond = Entity(parent=root, model='cube', scale=(0.16, 0.045, 2.45),
                       position=(0, height - 0.1, 0), rotation=(18, yaw, 0),
                       color=leaf if i % 2 else leaf_light)
        # A slim lower frond breaks up the perfectly radial silhouette.
        if i % 2 == 0:
            Entity(parent=root, model='cube', scale=(0.12, 0.035, 1.45),
                   position=(0, height - 0.22, 0), rotation=(31, yaw + 18, 0), color=leaf)
    return root


def _live_oak(Entity, color, x, z, size=1.0):
    """Broad-canopy oak / cypress hybrid used for the Clermont treeline."""
    root = Entity(position=(x, 0, z))
    bark = _rgb(color, 77, 51, 34)
    dark = _rgb(color, 24, 82, 43)
    mid = _rgb(color, 35, 112, 57)
    Entity(parent=root, model=round_cylinder(16), scale=(0.26 * size, 3.2 * size, 0.26 * size),
           y=1.6 * size, color=bark)
    for yaw in (0, 55, 120, 185, 250, 305):
        Entity(parent=root, model='cube', scale=(0.15 * size, 0.15 * size, 2.1 * size),
               position=(0, 2.2 * size, 0), rotation=(0, yaw, 24), color=bark)
    for dx, dy, dz, scale in ((0, 3.45, 0, 2.15), (-0.65, 3.15, 0.3, 1.45),
                              (0.65, 3.2, -0.15, 1.55), (0.2, 4.0, 0.35, 1.25)):
        Entity(parent=root, model='sphere', scale=scale * size,
               position=(dx * size, dy * size, dz * size), color=mid if dy > 3.3 else dark)
    return root


def _power_pole(Entity, color, x, z, yaw=0.0):
    root = Entity(position=(x, 0, z), rotation_y=yaw)
    wood = _rgb(color, 74, 55, 42)
    wire = _rgb(color, 27, 22, 35)
    Entity(parent=root, model=round_cylinder(12), scale=(0.13, 5.7, 0.13), y=2.85, color=wood)
    Entity(parent=root, model='cube', scale=(2.25, 0.14, 0.12), y=5.05, color=wood)
    for dx in (-0.85, 0, 0.85):
        Entity(parent=root, model='sphere', scale=0.12, position=(dx, 4.92, 0), color=wire)
    return root


class FloridaAtmosphere:
    """Small pooled ambient-particle layer; no per-frame allocation."""
    def __init__(self, Entity, color, quality='med', seed=34714):
        self.Entity = Entity
        self.color = color
        self.rng = random.Random(seed)
        self.t = 0.0
        self.root = Entity()
        count = 0 if quality == 'low' else (18 if quality == 'med' else 30)
        self.particles = []
        for i in range(count):
            warm = i % 3 == 0
            p = Entity(
                parent=self.root,
                model='sphere',
                scale=0.035 if warm else 0.025,
                color=color.rgba32(255, 198, 95, 175) if warm else color.rgba32(185, 135, 255, 105),
                unlit=True,
            )
            p._phase = self.rng.random() * math.tau
            p._radius = self.rng.uniform(5.5, 19.0)
            p._height = self.rng.uniform(0.35, 3.8)
            p._rise = self.rng.uniform(0.10, 0.32)
            self.particles.append(p)

    def tick(self, anchor, dt):
        if not anchor:
            return
        self.t += min(dt, 0.05)
        ax, az = float(anchor.x), float(anchor.z)
        for i, p in enumerate(self.particles):
            phase = p._phase + self.t * (0.26 + (i % 5) * 0.045)
            p.x = ax + math.cos(phase) * p._radius
            p.z = az + math.sin(phase * 1.31) * p._radius
            p.y = 0.35 + ((p._height + self.t * p._rise) % 4.2)
            # Gentle shimmer rather than hard blinking.
            s = 0.7 + 0.3 * math.sin(phase * 2.0)
            p.scale = (0.032 if i % 3 == 0 else 0.022) * s


def make_florida_environment(Entity, color, quality='med'):
    """Add a readable Florida horizon and return its atmosphere controller."""
    # A small water shelf gives the south-east park a reflective destination.
    water = Entity(
        model='cube', scale=(25, 0.035, 13), position=(29, 0.018, -47),
        color=color.rgba32(42, 112, 178, 190), texture=_t('water'), texture_scale=(7, 4),
    )
    water.name = 'Lake Minneola inspired water shelf'

    for x, z, h, lean in ((-47, -5, 6.8, -4), (-43, -24, 5.7, 3), (-7, -46, 6.4, -2),
                           (24, -49, 7.4, 5), (42, 10, 7.2, -4), (48, -32, 5.8, 2)):
        _palm(Entity, color, x, z, h, lean)
    for x, z, s in ((-48, 21, 1.2), (-12, 22, 1.05), (7, 19, 0.9), (47, -46, 1.15),
                     (33, -43, 0.9), (-40, -44, 0.95)):
        _live_oak(Entity, color, x, z, s)
    for x, z, yaw in ((-42, -13, 0), (-24, -13, 0), (-6, -13, 0), (12, -13, 0),
                      (30, -13, 0), (46, -13, 0)):
        _power_pole(Entity, color, x, z, yaw)

    # The line itself is deliberately decorative and collider-free.
    for x in (-33, -15, 3, 21, 39):
        Entity(model='cube', scale=(18.2, 0.035, 0.035), position=(x, 4.9, -13),
               color=_rgb(color, 24, 19, 31))
    return FloridaAtmosphere(Entity, color, quality=quality)
