"""Neon-dusk lighting + render opts for Rune Mommy (Ursina / Panda3D).

Patterns from Panda3D public docs (render attributes, light counts, fog, MSAA,
anisotropic filtering) and common MIT/BSD game-perf practice.

Quality via RUNE_MOMMY_QUALITY: low | med | high | ultra
  ultra / high: shadows, more accent lights, MSAA, anisotropic filtering (NVIDIA-friendly PRC).
No Project Zomboid code.
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
    q = (os.environ.get('RUNE_MOMMY_QUALITY') or 'high').strip().lower()
    if q in ('low', 'med', 'medium', 'high', 'ultra'):
        return 'med' if q == 'medium' else q
    return 'high'


def apply_lighting(color, Vec3, Sky=None, DirectionalLight=None, AmbientLight=None, PointLight=None):
    """Install neon-dusk light kit. Shadows on for high/ultra."""
    q = quality()
    if Sky is not None:
        try:
            Sky(color=color.rgb32(16, 5, 30) if q in ('high', 'ultra') else color.rgb32(18, 6, 32))
        except Exception:
            pass

    shadows = q in ('high', 'ultra')
    try:
        sun = DirectionalLight(shadows=shadows)
        sun.look_at(Vec3(1, -1.35, 0.35))
        if q == 'ultra':
            sun.color = color.rgb32(255, 205, 185)
        elif q == 'high':
            sun.color = color.rgb32(255, 190, 170)
        elif q == 'low':
            sun.color = color.rgb32(200, 150, 170)
        else:
            sun.color = color.rgb32(240, 180, 165)
        if shadows:
            try:
                res = (2048, 2048) if q == 'ultra' else (1024, 1024)
                sun.shadow_map_resolution = res
            except Exception:
                pass
    except Exception:
        pass

    try:
        if q == 'ultra':
            AmbientLight(color=color.rgb32(110, 82, 140))
        elif q == 'low':
            AmbientLight(color=color.rgb32(70, 48, 95))
        else:
            AmbientLight(color=color.rgb32(95, 70, 120))
    except Exception:
        pass

    if q == 'low':
        accents = [((0, 6, -16), (255, 100, 210))]
    elif q == 'med':
        accents = [
            ((0, 6, -16), (255, 90, 210)),
            ((-28, 5, 10), (90, 220, 255)),
        ]
    elif q == 'high':
        accents = [
            ((0, 6, -16), (255, 90, 210)),
            ((-28, 5, 10), (90, 220, 255)),
            ((22, 5, -6), (255, 160, 60)),
            ((40, 6, -20), (255, 70, 180)),   # Club 27
        ]
    else:  # ultra
        accents = [
            ((0, 6, -16), (255, 95, 220)),
            ((-28, 5, 10), (100, 230, 255)),
            ((22, 5, -6), (255, 170, 70)),
            ((40, 6, -20), (255, 80, 190)),
            ((-36, 5, -16), (120, 255, 230)),  # Quiet Spa
            ((36, 8, 6), (255, 210, 90)),      # Citrus Tower
            ((16, 5, -42), (80, 180, 255)),    # Waterfront
            ((62, 6, -18), (255, 220, 100)),   # Walmart
        ]

    lights = []
    for pos, rgb in accents:
        try:
            pl = PointLight(position=pos, color=color.rgb32(*rgb))
            lights.append(pl)
        except Exception:
            pass
    return {'quality': q, 'shadows': shadows, 'point_lights': lights}


def apply_perf(window=None, camera=None, color=None):
    """Frame budget + fog + MSAA / anisotropic (NVIDIA-friendly PRC)."""
    q = quality()
    try:
        from panda3d.core import loadPrcFileData
        if q == 'low':
            loadPrcFileData('', 'framebuffer-multisample 0')
            loadPrcFileData('', 'multisamples 0')
            loadPrcFileData('', 'texture-anisotropic-degree 0')
        elif q == 'med':
            loadPrcFileData('', 'framebuffer-multisample 1')
            loadPrcFileData('', 'multisamples 2')
            loadPrcFileData('', 'texture-anisotropic-degree 4')
        elif q == 'high':
            loadPrcFileData('', 'framebuffer-multisample 1')
            loadPrcFileData('', 'multisamples 4')
            loadPrcFileData('', 'texture-anisotropic-degree 8')
            loadPrcFileData('', 'sync-video true')
        else:  # ultra — push quality for strong PCs / NVIDIA
            loadPrcFileData('', 'framebuffer-multisample 1')
            loadPrcFileData('', 'multisamples 8')
            loadPrcFileData('', 'texture-anisotropic-degree 16')
            loadPrcFileData('', 'sync-video true')
            loadPrcFileData('', 'texture-minfilter linear-mipmap-linear')
            loadPrcFileData('', 'texture-magfilter linear')
            # Prefer compressed textures off so neon/albedo stay crisp
            loadPrcFileData('', 'compressed-textures 0')
    except Exception:
        pass

    if window is not None:
        try:
            window.fps_counter.enabled = True
        except Exception:
            pass

    if camera is not None and color is not None and q != 'low':
        try:
            from ursina import scene
            if q == 'ultra':
                scene.fog_color = color.rgb32(18, 6, 32)
                scene.fog_density = 0.006
            elif q == 'high':
                scene.fog_color = color.rgb32(20, 8, 34)
                scene.fog_density = 0.008
            else:
                scene.fog_color = color.rgb32(20, 8, 34)
                scene.fog_density = 0.012
        except Exception:
            try:
                camera.fog = True
                camera.fog_color = color.rgb32(20, 8, 34)
                camera.fog_density = 0.008 if q in ('high', 'ultra') else 0.01
            except Exception:
                pass

    cull_ped = CULL_PED
    cull_traffic = CULL_TRAFFIC
    if q == 'low':
        cull_ped, cull_traffic = 32.0, 40.0
    elif q == 'ultra':
        cull_ped, cull_traffic = 56.0, 72.0
    elif q == 'high':
        cull_ped, cull_traffic = 48.0, 64.0

    return {
        'quality': q,
        'cull_ped': cull_ped,
        'cull_traffic': cull_traffic,
    }


def xz_dist(ax, az, bx, bz) -> float:
    dx = ax - bx
    dz = az - bz
    return (dx * dx + dz * dz) ** 0.5


def set_visible(ent, on: bool):
    """Show/hide ent and mesh children. Hitbox ghosts stay invisible when shown."""
    if not ent:
        return
    try:
        if getattr(ent, 'hitbox_ghost', False):
            ent.visible = False
            return
        ent.visible = on
    except Exception:
        pass
    try:
        for ch in list(getattr(ent, 'children', []) or []):
            try:
                if getattr(ch, 'hitbox_ghost', False):
                    ch.visible = False
                    continue
                ch.visible = on
                for gch in list(getattr(ch, 'children', []) or []):
                    if getattr(gch, 'hitbox_ghost', False):
                        gch.visible = False
                    else:
                        gch.visible = on
            except Exception:
                pass
    except Exception:
        pass


def should_sim(px, pz, x, z, radius: float) -> bool:
    return xz_dist(px, pz, x, z) <= radius
