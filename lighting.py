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
    q = (os.environ.get('RUNE_MOMMY_QUALITY') or 'med').strip().lower()
    if q in ('low', 'med', 'medium', 'high', 'ultra'):
        return 'med' if q == 'medium' else q
    return 'med'


def target_fps() -> int:
    """Hard floor 60. RUNE_MOMMY_FPS raises the cap/target (e.g. 72, 120)."""
    raw = (os.environ.get('RUNE_MOMMY_FPS') or '60').strip()
    try:
        fps = int(float(raw))
    except Exception:
        fps = 60
    return max(60, fps)


def apply_lighting(color, Vec3, Sky=None, DirectionalLight=None, AmbientLight=None, PointLight=None):
    """Install neon-dusk light kit. Shadows only on ultra (high stays lit, no shadow maps).

    Look polish: punchier sun/ambient on med/high; capped point lights (FPS-safe).
    Default quality is med. Shadows remain ultra-only.
    Returns light kit dict (sky/sun/ambient/point_lights) for day/night tick.
    """
    q = quality()
    sky = None
    if Sky is not None:
        try:
            # Slightly richer dusk sky on med+ for punch without extra lights
            if q == 'ultra':
                sky = Sky(color=color.rgb32(14, 4, 28))
            elif q == 'high':
                sky = Sky(color=color.rgb32(15, 5, 30))
            elif q == 'med':
                sky = Sky(color=color.rgb32(17, 6, 32))
            else:
                sky = Sky(color=color.rgb32(20, 8, 34))
        except Exception:
            sky = None

    shadows = (q == 'ultra')
    sun = None
    try:
        sun = DirectionalLight(shadows=shadows)
        # Slightly steeper key for clearer silhouette on faces/meshes
        sun.look_at(Vec3(1.05, -1.45, 0.40))
        if q == 'ultra':
            sun.color = color.rgb32(255, 215, 195)
        elif q == 'high':
            sun.color = color.rgb32(255, 205, 185)
        elif q == 'low':
            sun.color = color.rgb32(200, 150, 170)
        else:  # med — punchier warm key
            sun.color = color.rgb32(255, 198, 178)
        if shadows:
            try:
                res = (2048, 2048) if q == 'ultra' else (1024, 1024)
                sun.shadow_map_resolution = res
            except Exception:
                pass
    except Exception:
        sun = None

    ambient = None
    try:
        if q == 'ultra':
            ambient = AmbientLight(color=color.rgb32(118, 88, 148))
        elif q == 'high':
            ambient = AmbientLight(color=color.rgb32(108, 80, 135))
        elif q == 'low':
            ambient = AmbientLight(color=color.rgb32(70, 48, 95))
        else:  # med
            ambient = AmbientLight(color=color.rgb32(102, 76, 128))
    except Exception:
        ambient = None

    # Point-light budget: each is expensive with multipart meshes.
    # med: 3 (was 2). high: 4 (was 2). ultra: full POI set. Shadows ultra-only.
    if q == 'low':
        accents = [((0, 6, -16), (255, 110, 215))]
    elif q == 'med':
        accents = [
            ((0, 6, -16), (255, 105, 220)),     # plaza neon
            ((-28, 5, 10), (100, 230, 255)),    # NW cyan
            ((18, 5.5, -10), (255, 180, 90)),   # gas/Hwy warm fill
        ]
    elif q == 'high':
        accents = [
            ((0, 6, -16), (255, 110, 225)),
            ((-28, 5, 10), (105, 235, 255)),
            ((18, 5.5, -10), (255, 185, 95)),
            ((40, 6, -18), (255, 95, 200)),     # Club 27
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
    accent_base = []
    for pos, rgb in accents:
        try:
            pl = PointLight(position=pos, color=color.rgb32(*rgb))
            lights.append(pl)
            accent_base.append((pos, rgb))
        except Exception:
            pass
    return {
        'quality': q,
        'shadows': shadows,
        'point_lights': lights,
        'accent_base': accent_base,
        'sky': sky,
        'sun': sun,
        'ambient': ambient,
        'color_mod': color,
        'Vec3': Vec3,
    }


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
            else:  # med — clearer mid so meshes/neon read
                scene.fog_color = color.rgb32(18, 7, 32)
                scene.fog_density = 0.010
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
        cull_ped, cull_traffic = 40.0, 52.0
        lod_ped_near, lod_ped_mid = 16.0, 28.0
        lod_traffic_near, lod_traffic_mid = 22.0, 40.0
    elif q == 'med':
        cull_ped, cull_traffic = 32.0, 42.0
        lod_ped_near, lod_ped_mid = 14.0, 24.0
        lod_traffic_near, lod_traffic_mid = 18.0, 32.0

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
        'ai_far_interval': 4 if q == 'ultra' else (5 if q == 'high' else 6),
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
    """level: 'near' | 'mid' | 'far'.

    Aggressive: mid hides anything not lod_keep; far hides whole ent.
    Humanoid multipart meshes must mark core parts lod_keep=True.
    """
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
                if getattr(ch, 'hitbox_ghost', False):
                    ch.visible = False
                    continue
                keep = bool(getattr(ch, 'lod_keep', False))
                tag = getattr(ch, 'lod_detail', None)
                if keep:
                    ch.visible = True
                elif tag == 'high':
                    ch.visible = show_detail
                elif tag == 'mid':
                    ch.visible = show_mid
                else:
                    # Untagged extras (hair clips, props) — near only
                    ch.visible = show_detail
                for gch in list(getattr(ch, 'children', []) or []):
                    if getattr(gch, 'hitbox_ghost', False):
                        gch.visible = False
                        continue
                    gkeep = bool(getattr(gch, 'lod_keep', False))
                    gtag = getattr(gch, 'lod_detail', None)
                    if gkeep:
                        gch.visible = True
                    elif gtag == 'high' or gtag is None:
                        gch.visible = show_detail
                    elif gtag == 'mid':
                        gch.visible = show_mid
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



# ---------------------------------------------------------------------------
# Day / night cycle (World pass) — hooks life_sim clock; quality-aware.
# Toggle: RUNE_MOMMY_DAY_NIGHT=0 freezes. Debug: nudge_time / [ ] keys.
# Start hour: RUNE_MOMMY_TIME=14 (optional 0-23).
# ---------------------------------------------------------------------------

# Keyframes: hour -> (sky_rgb, sun_rgb, amb_rgb, fog_rgb, fog_density, sun_dir, neon_mul)
# neon_mul scales point-light brightness (night neon pops).
_DN_KEYS = (
    # midnight deep
    (0.0,  ((8, 4, 22),   (90, 70, 120),  (48, 36, 78),  (10, 4, 22), 0.018, (0.55, -0.35, 0.55), 1.35)),
    # predawn
    (5.0,  ((18, 10, 36), (140, 100, 130),(62, 48, 95),  (16, 8, 30), 0.014, (0.85, -0.55, 0.35), 1.15)),
    # dawn
    (6.5,  ((255, 160, 110),(255, 190, 140),(110, 85, 120),(40, 22, 48), 0.010, (1.1, -0.85, 0.25), 0.85)),
    # morning
    (9.0,  ((135, 185, 255),(255, 240, 210),(125, 120, 140),(70, 95, 130), 0.007, (1.0, -1.2, 0.2), 0.55)),
    # noon
    (12.0, ((110, 170, 255),(255, 250, 235),(140, 135, 150),(90, 120, 160), 0.005, (0.35, -1.55, 0.15), 0.40)),
    # afternoon
    (15.5, ((150, 175, 240),(255, 230, 195),(128, 115, 140),(60, 80, 120), 0.007, (-0.55, -1.35, 0.25), 0.55)),
    # golden hour / dusk
    (18.0, ((255, 120, 70), (255, 170, 110),(115, 80, 110),(55, 25, 45), 0.011, (-1.0, -0.75, 0.35), 0.95)),
    # nightfall
    (20.0, ((28, 10, 48),  (160, 110, 150),(70, 50, 105), (18, 6, 34), 0.015, (-0.7, -0.4, 0.5), 1.25)),
    # late
    (22.5, ((12, 5, 28),   (100, 75, 130), (52, 38, 85),  (12, 4, 24), 0.017, (0.2, -0.3, 0.6), 1.35)),
    # wrap toward midnight
    (24.0, ((8, 4, 22),    (90, 70, 120),  (48, 36, 78),  (10, 4, 22), 0.018, (0.55, -0.35, 0.55), 1.35)),
)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_rgb(a, b, t):
    return tuple(int(_lerp(float(a[i]), float(b[i]), t) + 0.5) for i in range(3))


def _sample_day_night(hour: float):
    h = hour % 24.0
    keys = _DN_KEYS
    for i in range(len(keys) - 1):
        h0, v0 = keys[i][0], keys[i][1]
        h1, v1 = keys[i + 1][0], keys[i + 1][1]
        if h0 <= h <= h1:
            span = max(1e-6, h1 - h0)
            t = (h - h0) / span
            sky = _lerp_rgb(v0[0], v1[0], t)
            sun = _lerp_rgb(v0[1], v1[1], t)
            amb = _lerp_rgb(v0[2], v1[2], t)
            fog = _lerp_rgb(v0[3], v1[3], t)
            dens = _lerp(v0[4], v1[4], t)
            direction = tuple(_lerp(v0[5][j], v1[5][j], t) for j in range(3))
            neon = _lerp(v0[6], v1[6], t)
            return sky, sun, amb, fog, dens, direction, neon
    return keys[0][1]


def day_night_enabled() -> bool:
    raw = (os.environ.get('RUNE_MOMMY_DAY_NIGHT') or '1').strip().lower()
    return raw not in ('0', 'off', 'false', 'no')


def phase_name(hour: float) -> str:
    h = hour % 24.0
    if 5.0 <= h < 7.0:
        return 'dawn'
    if 7.0 <= h < 17.0:
        return 'day'
    if 17.0 <= h < 19.5:
        return 'dusk'
    if 19.5 <= h < 24.0 or h < 5.0:
        return 'night'
    return 'day'


def _set_rgb(ent, color_mod, rgb):
    if ent is None or color_mod is None:
        return
    try:
        ent.color = color_mod.rgb32(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    except Exception:
        pass


def boot_day_night(game, kit=None):
    """Attach day/night kit to game. Safe on slim boot (kit may be partial)."""
    if kit is None:
        kit = getattr(game, 'light_kit', None) or {}
    game.light_kit = kit
    game.day_night_on = day_night_enabled()
    # Optional start hour override
    raw = (os.environ.get('RUNE_MOMMY_TIME') or '').strip()
    if raw:
        try:
            hh = float(raw) % 24.0
            game.life_sim_minutes = hh * 60.0
        except Exception:
            pass
    game._dn_accum = 0.0
    game._dn_last_bucket = -1
    game._dn_force = True
    # Apply once so menu/safe yard already matches clock
    try:
        tick_day_night(game, 0.0, force=True)
    except Exception as exc:
        print('  day_night boot skip:', exc)
    print('  day_night: %s (phase=%s) — [ ] skip 2h, RUNE_MOMMY_DAY_NIGHT=0 freezes' % (
        'ON' if game.day_night_on else 'OFF',
        phase_name(_hour_from_game(game)),
    ))


def _hour_from_game(game) -> float:
    mins = float(getattr(game, 'life_sim_minutes', 10 * 60.0))
    return (mins / 60.0) % 24.0


def nudge_time(game, hours: float = 2.0):
    """Debug: jump in-game clock by `hours` (wrap 24h)."""
    game.life_sim_minutes = float(getattr(game, 'life_sim_minutes', 10 * 60.0)) + float(hours) * 60.0
    if game.life_sim_minutes < 0:
        game.life_sim_minutes %= (24 * 60)
    if game.life_sim_minutes >= 24 * 60:
        game.life_sim_minutes %= (24 * 60)
    game._dn_force = True
    try:
        tick_day_night(game, 0.0, force=True)
    except Exception:
        pass
    h = _hour_from_game(game)
    return h, phase_name(h)


def tick_day_night(game, dt: float = 0.0, force: bool = False):
    """Shift sky/sun/ambient/fog/neon with in-game hour. Throttled for FPS."""
    if not getattr(game, 'day_night_on', True):
        return
    kit = getattr(game, 'light_kit', None)
    if not kit:
        return
    force = force or bool(getattr(game, '_dn_force', False))
    game._dn_force = False
    game._dn_accum = float(getattr(game, '_dn_accum', 0.0)) + float(dt or 0.0)
    hour = _hour_from_game(game)
    # Bucket ~6 min in-game (~8 real sec at CLOCK_SCALE 45) — cheap updates
    bucket = int(hour * 10)  # 0.1h steps
    if not force and bucket == getattr(game, '_dn_last_bucket', -1) and game._dn_accum < 0.35:
        return
    if not force and game._dn_accum < 0.20 and bucket == getattr(game, '_dn_last_bucket', -1):
        return
    game._dn_accum = 0.0
    game._dn_last_bucket = bucket

    sky_rgb, sun_rgb, amb_rgb, fog_rgb, dens, direction, neon = _sample_day_night(hour)
    color = kit.get('color_mod')
    q = kit.get('quality') or quality()

    # Quality: low skips fog + neon scale; med+ full
    _set_rgb(kit.get('sky'), color, sky_rgb)
    _set_rgb(kit.get('sun'), color, sun_rgb)
    _set_rgb(kit.get('ambient'), color, amb_rgb)

    sun = kit.get('sun')
    Vec3 = kit.get('Vec3')
    if sun is not None and Vec3 is not None:
        try:
            sun.look_at(Vec3(float(direction[0]), float(direction[1]), float(direction[2])))
        except Exception:
            pass

    if q != 'low' and color is not None:
        try:
            from ursina import scene
            scene.fog_color = color.rgb32(*fog_rgb)
            # med stays readable; night denser
            base = 0.010 if q == 'med' else (0.008 if q == 'high' else 0.006)
            scene.fog_density = max(base * 0.6, dens * (0.85 if q == 'ultra' else 1.0))
        except Exception:
            cam = getattr(game, 'camera', None)
            if cam is not None:
                try:
                    cam.fog = True
                    cam.fog_color = color.rgb32(*fog_rgb)
                    cam.fog_density = dens
                except Exception:
                    pass

    # Neon accents — brighter at night, dimmer midday (no extra lights)
    if q != 'low' and color is not None:
        lights = kit.get('point_lights') or []
        bases = kit.get('accent_base') or []
        for i, pl in enumerate(lights):
            if i >= len(bases):
                break
            _pos, rgb = bases[i]
            scaled = tuple(max(20, min(255, int(c * neon))) for c in rgb)
            _set_rgb(pl, color, scaled)

    game.day_phase = phase_name(hour)
    game.day_hour = hour
