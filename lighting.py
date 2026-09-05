"""Neon-dusk lighting + render opts for Rune Mommy (Ursina / Panda3D).

Patterns from Panda3D public docs (render attributes, light counts, fog) and
common MIT/BSD game-perf practice: few lights, shadows off by default,
distance cull for dense crowds/traffic.

No Project Zomboid code. Quality: low | med | high via RUNE_MOMMY_QUALITY.
"""
from __future__ import annotations

import os

# Distance (XZ) beyond which peds/traffic skip AI and hide meshes.
CULL_PED = 42.0
CULL_TRAFFIC = 55.0
# Soft fog so distant cubes melt into dusk instead of popping.
FOG_NEAR = 28.0
FOG_FAR = 95.0


def quality() -> str:
    q = (os.environ.get('RUNE_MOMMY_QUALITY') or 'med').strip().lower()
    if q in ('low', 'med', 'medium', 'high'):
        return 'med' if q == 'medium' else q
    return 'med'


def apply_lighting(color, Vec3, Sky=None, DirectionalLight=None, AmbientLight=None, PointLight=None):
    """Install a small neon-dusk light kit. Shadows off unless quality=high."""
    q = quality()
    if Sky is not None:
        try:
            Sky(color=color.rgb32(18, 6, 32))
        except Exception:
            pass

    shadows = q == 'high'
    try:
        sun = DirectionalLight(shadows=shadows)
        sun.look_at(Vec3(1, -1.35, 0.35))
        # Warm dusk key — readable without washing neon
        sun.color = color.rgb32(255, 190, 170) if q != 'low' else color.rgb32(200, 150, 170)
        if shadows:
            try:
                sun.shadow_map_resolution = (1024, 1024)
            except Exception:
                pass
    except Exception:
        pass

    # Mid fill so silhouettes stay readable on Hwy 50
    try:
        AmbientLight(color=color.rgb32(70, 48, 95) if q == 'low' else color.rgb32(95, 70, 120))
    except Exception:
        pass

    if q == 'low':
        # One accent only
        accents = [((0, 6, -16), (255, 100, 210))]
    else:
        accents = [
            ((0, 6, -16), (255, 90, 210)),   # Hwy 50 neon
            ((-28, 5, 10), (90, 220, 255)),  # Sanctuary Drive cool porch
        ]
        if q == 'high':
            accents.append(((22, 5, -6), (255, 160, 60)))  # Gun Hut warm

    lights = []
    for pos, rgb in accents:
        try:
            pl = PointLight(position=pos, color=color.rgb32(*rgb))
            lights.append(pl)
        except Exception:
            pass
    return {'quality': q, 'shadows': shadows, 'point_lights': lights}


def apply_perf(window=None, camera=None, color=None):
    """Frame budget + fog. Safe no-ops if APIs missing."""
    q = quality()
    try:
        from panda3d.core import loadPrcFileData
        # Cap work; vsync left to Ursina
        if q == 'low':
            loadPrcFileData('', 'framebuffer-multisample 0')
            loadPrcFileData('', 'multisamples 0')
        elif q == 'med':
            loadPrcFileData('', 'framebuffer-multisample 0')
            loadPrcFileData('', 'multisamples 0')
        # high: leave defaults
    except Exception:
        pass

    if window is not None:
        try:
            window.fps_counter.enabled = True
        except Exception:
            pass

    # Exponential fog via Ursina camera if available
    if camera is not None and color is not None and q != 'low':
        try:
            from ursina import scene
            # Ursina Scene has fog attrs on some versions
            scene.fog_color = color.rgb32(20, 8, 34)
            scene.fog_density = 0.012 if q == 'med' else 0.008
        except Exception:
            try:
                camera.fog = True
                camera.fog_color = color.rgb32(20, 8, 34)
                camera.fog_density = 0.01
            except Exception:
                pass

    return {
        'quality': q,
        'cull_ped': CULL_PED if q != 'low' else 32.0,
        'cull_traffic': CULL_TRAFFIC if q != 'low' else 40.0,
    }


def xz_dist(ax, az, bx, bz) -> float:
    dx = ax - bx
    dz = az - bz
    return (dx * dx + dz * dz) ** 0.5


def set_visible(ent, on: bool):
    if not ent:
        return
    try:
        if getattr(ent, 'enabled', None) is not None and ent.enabled != on:
            # Prefer .visible so we don't drop from lists; fall back to enabled
            pass
    except Exception:
        pass
    try:
        ent.visible = on
    except Exception:
        try:
            for ch in getattr(ent, 'children', []) or []:
                ch.visible = on
        except Exception:
            pass


def should_sim(px, pz, x, z, radius: float) -> bool:
    return xz_dist(px, pz, x, z) <= radius
