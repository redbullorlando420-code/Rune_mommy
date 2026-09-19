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
    # Visual quality is the product default. Low and medium remain explicit
    # opt-ins for machines that need a smaller frame budget.
    q = (os.environ.get('RUNE_MOMMY_QUALITY') or 'high').strip().lower()
    if q in ('low', 'med', 'medium', 'high'):
        return 'med' if q == 'medium' else q
    return 'high'


def configure_renderer():
    """Apply renderer quality before Ursina creates its window."""
    try:
        from panda3d.core import loadPrcFileData
        q = quality()
        # Anti-aliasing is especially noticeable on palm fronds, power lines,
        # and the new low-profile particle layer.  Keep the default modest.
        if q == 'high':
            loadPrcFileData('', 'framebuffer-multisample 1')
            loadPrcFileData('', 'multisamples 4')
            loadPrcFileData('', 'texture-anisotropic-degree 4')
        else:
            loadPrcFileData('', 'framebuffer-multisample 0')
            loadPrcFileData('', 'multisamples 0')
        loadPrcFileData('', 'gl-cube-map-seamless 1')
    except Exception:
        pass


def apply_lighting(color, Vec3, Sky=None, DirectionalLight=None, AmbientLight=None, PointLight=None):
    """Install a layered Florida-blue-hour light kit without per-prop lights."""
    q = quality()
    sky = None
    if Sky is not None:
        try:
            # Local texture avoids the incomplete Ursina-package sky_default
            # fallback and gives the neon scene a real blue-hour horizon.
            sky = Sky(texture='assets/textures/sky_dusk_v1.png',
                      color=color.rgb32(235, 235, 255) if q == 'high' else color.rgb32(190, 185, 225))
        except Exception:
            pass

    shadows = q == 'high'
    sun = None
    try:
        sun = DirectionalLight(shadows=shadows)
        sun.look_at(Vec3(1, -1.35, 0.35))
        # Warm horizon key: readable pavement, cool shadows, preserved neon.
        sun.color = color.rgb32(255, 196, 160) if q != 'low' else color.rgb32(200, 150, 170)
        if shadows:
            try:
                sun.shadow_map_resolution = (2048, 2048)
            except Exception:
                pass
    except Exception:
        pass

    # Mid fill so silhouettes stay readable on Hwy 50
    ambient = None
    try:
        ambient = AmbientLight(color=color.rgb32(62, 52, 88) if q == 'low' else color.rgb32(82, 96, 142))
    except Exception:
        pass

    if q == 'low':
        # One accent only
        accents = [((0, 6, -16), (255, 100, 210))]
    else:
        accents = [
            ((0, 6, -16), (255, 80, 205)),   # Hwy 50 neon
            ((-28, 5, 10), (80, 210, 255)),  # Sanctuary Drive cool porch
            ((28, 4, -42), (76, 150, 255)),  # waterfront spill
        ]
        if q == 'high':
            accents.extend([
                ((22, 5, -6), (255, 160, 60)),   # Gun Hut warm
                ((40, 5, -20), (255, 45, 150)),  # Club 27 sign wash
            ])

    lights = []
    for pos, rgb in accents:
        try:
            pl = PointLight(position=pos, color=color.rgb32(*rgb))
            lights.append(pl)
        except Exception:
            pass
    return {'quality': q, 'shadows': shadows, 'point_lights': lights, 'sun': sun, 'ambient': ambient, 'sky': sky}


def tick_day_night(rig, color, elapsed: float):
    """Small visual-only day/night cycle; it never creates per-frame objects."""
    if not rig:
        return
    # One cycle is 7.5 real-time minutes: quick enough to notice, slow enough
    # not to flicker during ordinary play.
    phase = (float(elapsed) % 450.0) / 450.0
    daylight = max(0.08, __import__('math').sin(phase * __import__('math').tau) * 0.5 + 0.5)
    sun = rig.get('sun')
    if sun:
        try:
            sun.rotation_x = -18.0 + daylight * 72.0
            sun.color = color.rgb32(int(125 + 130 * daylight), int(80 + 125 * daylight), int(125 + 90 * daylight))
        except Exception:
            pass
    ambient = rig.get('ambient')
    if ambient:
        try:
            ambient.color = color.rgb32(int(34 + 58 * daylight), int(42 + 66 * daylight), int(78 + 70 * daylight))
        except Exception:
            pass
    sky = rig.get('sky')
    if sky:
        try:
            sky.color = color.rgba32(int(90 + 145 * daylight), int(72 + 145 * daylight), int(145 + 100 * daylight), 255)
        except Exception:
            pass


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
            scene.fog_color = color.rgb32(20, 24, 54)
            scene.fog_density = 0.010 if q == 'med' else 0.0065
        except Exception:
            try:
                camera.fog = True
                camera.fog_color = color.rgb32(20, 24, 54)
                camera.fog_density = 0.009
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
