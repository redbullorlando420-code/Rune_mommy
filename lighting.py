"""Neon-dusk lighting + render opts for Rune Mommy (Ursina / Panda3D).

Patterns from Panda3D public docs (render attributes, light counts, fog, MSAA,
anisotropic filtering) and common MIT/BSD game-perf practice.

Quality via RUNE_MOMMY_QUALITY: low | med | high | ultra
FPS via RUNE_MOMMY_FPS: target FPS (default 60, minimum 60). Caps via vsync /
  explicit frame pacing so med/high/ultra aim ≥60 on strong NVIDIA.
  ultra: keep fancy graphics; rely on cull/LOD/AI throttle for budget.
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
# LOD bands (near = full mesh/AI, mid = throttled AI, far = hide)
LOD_PED_NEAR = 22.0
LOD_PED_MID = 36.0
LOD_TRAFFIC_NEAR = 28.0
LOD_TRAFFIC_MID = 48.0


def quality() -> str:
    q = (os.environ.get('RUNE_MOMMY_QUALITY') or 'high').strip().lower()
    if q in ('low', 'med', 'medium', 'high', 'ultra'):
        return 'med' if q == 'medium' else q
    return 'high'


def target_fps() -> int:
    """Hard floor 60. RUNE_MOMMY_FPS raises the cap/target (e.g. 72, 120)."""
    raw = (os.environ.get('RUNE_MOMMY_FPS') or '60').strip()
    try:
        fps = int(float(raw))
    except Exception:
        fps = 60
    return max(60, fps)


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
            ((28, 6, 8), (0, 70, 190)),        # Best Buy
            ((42, 5, -6), (255, 100, 30)),     # Tire shop
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
    """Frame budget + fog + MSAA / anisotropic + FPS lock (≥60)."""
    q = quality()
    fps = target_fps()
    try:
        from panda3d.core import loadPrcFileData
        # Lock / target FPS — floor 60. Prefer limited clock over GPU vsync so
        # Ursina apply_settings(vsync=True→MNormal) cannot leave us uncapped/slow.
        loadPrcFileData('', 'clock-mode limited')
        loadPrcFileData('', f'clock-frame-rate {fps}')
        # sync-video false: MLimited is the authority (avoids 20/30Hz weirdness)
        loadPrcFileData('', 'sync-video false')
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
        else:  # ultra — push quality for strong PCs / NVIDIA; LOD keeps 60
            loadPrcFileData('', 'framebuffer-multisample 1')
            loadPrcFileData('', 'multisamples 8')
            loadPrcFileData('', 'texture-anisotropic-degree 16')
            loadPrcFileData('', 'texture-minfilter linear-mipmap-linear')
            loadPrcFileData('', 'texture-magfilter linear')
            loadPrcFileData('', 'compressed-textures 0')
    except Exception:
        pass

    if window is not None:
        try:
            window.fps_counter.enabled = True
        except Exception:
            pass
        # Ursina: int vsync => ClockObject.MLimited + setFrameRate (post-base)
        try:
            window.vsync = int(fps)
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
    lod_ped_near, lod_ped_mid = LOD_PED_NEAR, LOD_PED_MID
    lod_traffic_near, lod_traffic_mid = LOD_TRAFFIC_NEAR, LOD_TRAFFIC_MID
    if q == 'low':
        cull_ped, cull_traffic = 28.0, 36.0
        lod_ped_near, lod_ped_mid = 14.0, 22.0
        lod_traffic_near, lod_traffic_mid = 18.0, 28.0
    elif q == 'ultra':
        # Keep long draw for ultra beauty, but mid LOD still throttles AI
        cull_ped, cull_traffic = 56.0, 72.0
        lod_ped_near, lod_ped_mid = 26.0, 42.0
        lod_traffic_near, lod_traffic_mid = 32.0, 56.0
    elif q == 'high':
        cull_ped, cull_traffic = 48.0, 64.0
        lod_ped_near, lod_ped_mid = 22.0, 36.0
        lod_traffic_near, lod_traffic_mid = 28.0, 48.0
    elif q == 'med':
        cull_ped, cull_traffic = 38.0, 50.0
        lod_ped_near, lod_ped_mid = 18.0, 30.0
        lod_traffic_near, lod_traffic_mid = 22.0, 40.0

    return {
        'quality': q,
        'target_fps': fps,
        'cull_ped': cull_ped,
        'cull_traffic': cull_traffic,
        'lod_ped_near': lod_ped_near,
        'lod_ped_mid': lod_ped_mid,
        'lod_traffic_near': lod_traffic_near,
        'lod_traffic_mid': lod_traffic_mid,
        # Far agents tick every N frames (approx); near every frame
        'ai_far_interval': 3 if q != 'low' else 4,
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


def set_lod(ent, level: str):
    """level: 'near' | 'mid' | 'far' — hide detail children marked lod_detail on mid/far."""
    if not ent:
        return
    show_detail = level == 'near'
    show_mid = level in ('near', 'mid')
    try:
        if not show_mid:
            set_visible(ent, False)
            return
        set_visible(ent, True)
        for ch in list(getattr(ent, 'children', []) or []):
            try:
                tag = getattr(ch, 'lod_detail', None)
                if tag == 'high':
                    ch.visible = show_detail
                elif tag == 'mid':
                    ch.visible = show_mid
                for gch in list(getattr(ch, 'children', []) or []):
                    gtag = getattr(gch, 'lod_detail', None)
                    if gtag == 'high':
                        gch.visible = show_detail
            except Exception:
                pass
    except Exception:
        pass


def should_sim(px, pz, x, z, radius: float) -> bool:
    return xz_dist(px, pz, x, z) <= radius


def apply_fps_cap(app=None):
    """Re-assert FPS after Ursina boot.

    Ursina window.apply_settings() forces vsync=True → ClockObject.MNormal after
    ShowBase starts, which undoes pre-boot PRC limits and can leave frame pacing
    to the GPU (often ~20 dt=0.050 on some Windows setups). Always re-apply
    MLimited + setFrameRate here, and poke window.vsync with an int target.
    """
    fps = target_fps()
    try:
        from ursina import application
        application.time_scale = 1.0
    except Exception:
        pass
    try:
        from panda3d.core import loadPrcFileData, ClockObject
        loadPrcFileData('', 'sync-video false')
        loadPrcFileData('', 'clock-mode limited')
        loadPrcFileData('', f'clock-frame-rate {fps}')
        clock = ClockObject.getGlobalClock()
        clock.setMode(ClockObject.MLimited)
        clock.setFrameRate(float(fps))
        try:
            # Average-frame / dt max so one hitch does not report forever-20
            if hasattr(clock, 'setAverageFrameRateInterval'):
                clock.setAverageFrameRateInterval(0.5)
        except Exception:
            pass
    except Exception as exc:
        print('  apply_fps_cap clock skip:', exc)
    try:
        from ursina import window
        # int → MLimited + setFrameRate (see ursina.window.vsync setter)
        window.vsync = int(fps)
        try:
            window.fps_counter.enabled = True
        except Exception:
            pass
    except Exception:
        pass
    if app is not None:
        try:
            app.setFrameRateMeter(True)
        except Exception:
            pass
    return fps


def pre_boot_fps_prc():
    """Call BEFORE Ursina() so clock-frame-rate exists before ShowBase."""
    fps = target_fps()
    try:
        from panda3d.core import loadPrcFileData
        loadPrcFileData('', 'sync-video false')
        loadPrcFileData('', 'clock-mode limited')
        loadPrcFileData('', f'clock-frame-rate {fps}')
    except Exception:
        pass
    return fps
