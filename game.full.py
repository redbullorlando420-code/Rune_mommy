#!/usr/bin/env python3
"""Rune Mommy  -  Clermont / Hwy 50. Third-person Ursina desktop game.

Windows 11:
    py -3 -m pip install -r requirements.txt
    py -3 game.py
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time as pytime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

# Ensure ground/building textures exist (GitHub zip may omit binary jpgs).
try:
    from assets.generate_textures import ensure_all as _ensure_textures
    _ensure_textures()
except Exception as _tex_exc:
    print('[textures] fallback skip:', _tex_exc)


from loaders import (
    load_shops, portrait_texture_path, portrait_asset_path, load_npcs, load_mobs, load_items,
    load_oss_items, load_skills, load_progression, load_vehicles,
)
from crowd import spawn_crowd, tick_crowd, spawn_heat_hunter
from traffic import spawn_traffic, tick_traffic
from lighting import apply_lighting, apply_perf, apply_fps_cap, pre_boot_fps_prc, set_visible, target_fps
import footprints
try:
    import chunks as world_chunks
except Exception:
    world_chunks = None
from models3d import (
    make_humanoid, make_car, make_house, make_shop_stall,
    make_billboard, make_street_sign, make_poi_building,
    set_world_textures, hollow_shell,
    make_food_truck, make_walmart, densify_hwy50,
    make_retail_box, make_tire_shop,
)
try:
    from models3d import attach_humanoid_parts
except ImportError:  # older zips missing re-export
    from models3d._actors import attach_humanoid_parts
try:
    from models3d._actors import tick_jiggle as _tick_jiggle
except Exception:
    def _tick_jiggle(*a, **k): pass

import life_sim
import interiors
import wildlife

def _bicycle_step_safe(*args, **kwargs):
    """Call vendor.bicycle_step; drop unknown kwargs for older vendor zips."""
    import inspect
    from vendor.vehicle import bicycle_step as _bs
    try:
        sig = inspect.signature(_bs)
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            return _bs(*args, **kwargs)
        allowed = set(sig.parameters)
        # positional params names
        filtered = {k: v for k, v in kwargs.items() if k in allowed}
        return _bs(*args, **filtered)
    except TypeError:
        # last resort: positional-only classic signature
        return _bs(*args[:7], **{k: kwargs[k] for k in ('vmax', 'wheelbase', 'drag') if k in kwargs})

import tokyo
import radar
import parking
import adult_minigames
try:
    import sfx
except Exception:
    sfx = None
try:
    import crash
except Exception:
    crash = None

_TEX_CACHE = {}


def load_tex(name):
    """Load a texture from assets/textures/<name>.jpg|.png|.webp (Ursina or relative path)."""
    key = str(name).lower().strip()
    if key in _TEX_CACHE:
        return _TEX_CACHE[key]
    folders = (ROOT / 'assets' / 'textures', ROOT / 'textures')
    for folder in folders:
        for ext in ('.jpg', '.jpeg', '.png', '.webp'):
            path = folder / f'{key}{ext}'
            if path.is_file():
                rel = str(path.relative_to(ROOT)).replace(chr(92), '/')
                tex = None
                try:
                    from ursina import load_texture
                    tex = load_texture(rel)
                except Exception:
                    tex = None
                if tex is None:
                    try:
                        # Absolute path fallback — some Ursina builds want it
                        tex = load_texture(str(path))
                    except Exception:
                        tex = rel  # let Entity sample the file path
                _TEX_CACHE[key] = tex
                return tex
    print('  load_tex MISS:', key)
    _TEX_CACHE[key] = None
    return None


SHAKE_IDS = (
    'shake_bar',
    'steak_n_shake',
    'ritters',
    'brusters',
    'baskin',
    'culvers',
    'five_guys',
    'dairy_queen',
    'mcdonalds',
    'wendys',
)

GAME = None
TEST_SECONDS = 0.0
TEST_T0 = 0.0


def load_json(rel, default=None):
    path = ROOT / rel
    if not path.exists():
        return default
    with path.open(encoding='utf-8') as fh:
        return json.load(fh)


def shake_shop_names():
    data = load_json('data/shops.json', {}) or {}
    names = []
    for shop in data.get('shops', []):
        if shop.get('id') in SHAKE_IDS:
            names.append(shop.get('name', shop['id']))
    return names


def hex_color(value):
    from ursina import color
    if not value:
        return color.rgb32(200, 80, 180)
    if not str(value).startswith('#'):
        value = '#' + str(value)
    return color.hex(value)


def dist_xz(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def tile_to_world(tx, ty):
    x = (float(tx) - 16.0) * 2.15
    z = (7.0 - float(ty)) * 1.85
    return x, z


def wrap_text(text, width=58):
    text = (text or '').replace('\n', ' ')
    words = text.split()
    lines, line = [], ''
    for word in words:
        trial = (line + ' ' + word).strip()
        if len(trial) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return '\n'.join(lines[:8])


# ---------------------------------------------------------------------------
# Data-only helpers (safe to import without opening a window)
# ---------------------------------------------------------------------------

def data_report():
    shops = load_shops()
    names = shake_shop_names()
    mira = load_json('data/dialogue/mira.json', {}) or {}
    items = load_items()
    portrait = portrait_texture_path('mira')
    return {
        'shake_count': len(names),
        'shake_names': names,
        'shop_total': len(shops.get('shops', [])),
        'mira_nodes': len((mira.get('nodes') or {})),
        'has_pistol': 'pistol' in items,
        'has_ammo': 'ammo' in items,
        'mira_portrait': bool(portrait and Path(portrait).exists()),
    }


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

def boot_ursina(window_type='onscreen'):
    from panda3d.core import loadPrcFileData
    from pathlib import Path as _Path
    # Feel: enable OpenAL unless RUNE_MOMMY_AUDIO=0 / headless test.
    # Missing devices fall back to NullAudioManager; sfx stubs stay silent.
    _want_audio = True
    try:
        import sfx as _sfx_boot
        _want_audio = _sfx_boot.audio_wanted()
    except Exception:
        _want_audio = (os.environ.get('RUNE_MOMMY_AUDIO') or '1').strip().lower() not in (
            '0', 'off', 'false', 'no', 'null')
    if (not _want_audio) or window_type in ('offscreen', 'none'):
        loadPrcFileData('', 'audio-library-name null')
    loadPrcFileData('', 'notify-level-audio fatal')
    loadPrcFileData('', 'notify-level-glgsg warning')
    if window_type in ('offscreen', 'none'):
        loadPrcFileData('', f'window-type {window_type}')
    # PRC before ShowBase — Ursina apply_settings later forces vsync=True→MNormal
    fps = pre_boot_fps_prc()
    # Prefer tiny valid BMP-ICO we ship; skip icon entirely if missing/corrupt
    # (bad ICO paths spam Windows "failed to open file" and cost boot time).
    _ico = _Path(__file__).resolve().parent / 'textures' / 'ursina.ico'
    icon = None
    try:
        if _ico.is_file() and _ico.stat().st_size >= 22 and _ico.read_bytes()[:4] == b'\x00\x00\x01\x00':
            icon = str(_ico)
    except Exception:
        icon = None

    from ursina import Ursina
    kw = dict(
        title='Rune Mommy   -   Clermont / Hwy 50',
        borderless=False,
        fullscreen=False,
        development_mode=False,
        # False here; apply_settings still sets True→MNormal — we re-cap after
        vsync=False,
        size=(1280, 720),
        editor_ui_enabled=False,
        show_ursina_splash=False,
        window_type=window_type,
    )
    if icon:
        kw['icon'] = icon
    app = Ursina(**kw)
    # Critical: re-assert MLimited after Ursina.apply_settings()
    try:
        apply_fps_cap(app)
    except Exception as exc:
        print('  boot fps re-cap skip:', exc)
    print('  boot fps_target=%s (limited clock)' % fps)
    return app


class Game:
    def __init__(self):
        from ursina import Vec3, color, camera, mouse, window, Sky, Entity, Text, held_keys
        self.Vec3 = Vec3
        self.color = color
        self.camera = camera
        self.mouse = mouse
        self.window = window
        self.Sky = Sky
        self.Entity = Entity
        self.Text = Text
        self.held_keys = held_keys

        self.shops_data = load_shops()
        self.items = load_items()
        self.npcs_data = load_npcs()
        self.mobs_data = load_mobs()
        self.mira_dlg = load_json('data/dialogue/mira.json', {}) or {}
        self.lila_dlg = load_json('data/dialogue/lila.json', {}) or {}
        self.rosa_dlg = load_json('data/dialogue/rosa.json', {}) or {}
        self.yara_dlg = load_json('data/dialogue/yara.json', {}) or {}
        self.michelle_dlg = load_json('data/dialogue/michelle.json', {}) or {}
        self.oss_items = load_oss_items()
        self.skills = load_skills()
        self.progression = load_progression()
        self.vehicle_catalog = load_vehicles()
        self.quests_data = load_json('data/quests.json', {}) or {}
        oss_sk = (self.skills or {}).get('oss') or {}
        n_skills = len(oss_sk.get('skills') or []) if isinstance(oss_sk, dict) else 0
        n_veh = len((self.vehicle_catalog or {}).get('oss') or [])
        print('  oss_items:', len(self.oss_items or {}))
        print('  oss skills:', n_skills)
        print('  oss vehicles:', n_veh)

        self.gold = 200
        self.hp = 100
        self.max_hp = 100
        self.heat = 0.0
        self.breed = 0
        self.preg = False
        self.michelle_seen = False
        self.house_rooms = {}
        self.pack = []
        self.owned_pistol = False
        self.ammo = 0
        self.pistol_drawn = False
        self.shoot_cd = 0.0
        self.y_vel = 0.0
        self.grounded = True
        self.in_car = None
        self.ui_open = False
        self.talk_target = None
        self.mouse_free = False
        self.debug_on = True
        self.debug_hud = None
        self._dbg_t = 0.0
        self._dbg_last_key = '-'
        self._dbg_moved = False
        self._dbg_wish = False
        self._dbg_stuck_t = 0.0
        self.ui_choices = []
        self.toast_timer = 0.0
        self.prompt = ''
        self.panic_t = 0.0
        self.heat_spawn_cd = 0.0
        self.michelle_auto_opened = False
        self.michelle_node = 'door'
        self.michelle_open_idx = 0
        self.mode = 'menu'  # menu | settings | safe | play
        self.world_paused = True
        self.intro_started = False
        self.mouse_sens = 140.0
        self.cam_mode = 'follow'  # follow | near | far | hood (car)
        self.fullscreen_stub = False
        self.menu_ents = []
        self.menu_title = None
        self.menu_lines = []
        self.menu_backdrop = None
        self.safe_gate = None
        self.safe_yard_center = (80.0, 0.0, 80.0)
        self.clermont_spawn = (-18.0, 0.0, 12.0)
        self.talk_npcs = []
        self.house_vols = []
        self.sanctuary_door = None
        self.michelle = None
        self.building_count = 0
        self.pois = []
        self.quest_defs = list((self.quests_data or {}).get('quests') or [])
        self.quest_active = []
        self.quest_completed = set()
        self.quest_progress = {}
        self.hud_quest = None
        self.hud_mode = None
        self.tutorial_active = False
        self.tutorial_step = 0
        self.tutorial_overlay = None
        self.tutorial_text = None
        self.kill_quest_count = 0

        self.player = None
        self.cam_pivot = None
        self.visual = None
        self.gun_model = None
        self.cars = []
        self.debris = []
        self.npcs = []
        self.peds = []
        self.heat_hunters = []
        self.drops = []
        self.stalls = []
        self.targets = []
        self.ignore = []
        self.shake_spawned = []
        self.traffic_count = 0
        self.parked_count = 0

        self.panel_bg = None
        self.panel_portrait = None
        self.panel_name = None
        self.panel_body = None
        self.panel_choices = []
        self.hud_gold = None
        self.hud_hp = None
        self.hud_heat = None
        self.hud_ammo = None
        self.hud_pack = None
        self.hud_breed = None
        self.hud_prompt = None
        self.hud_toast = None
        self.crosshair = None
        self.cam_in_car = False

        try:
            mira_p = portrait_texture_path('mira')
        except Exception:
            mira_p = None
        self.mira_portrait_path = mira_p  # optional; None if missing
        self.mira_texture = None

    def setup(self):
        from ursina import DirectionalLight, AmbientLight, PointLight, destroy  # noqa: F401
        color = self.color
        Entity = self.Entity
        Text = self.Text
        camera = self.camera
        window = self.window
        mouse = self.mouse

        window.color = color.rgb32(12, 6, 22)
        window.exit_button.visible = True
        try:
            window.fps_counter.enabled = True
        except Exception:
            pass

        self.render_opts = apply_perf(window=window, camera=camera, color=color)
        try:
            self.render_opts['target_fps'] = apply_fps_cap()
        except Exception:
            self.render_opts['target_fps'] = target_fps()
        print('  render: quality=%s fps_target=%s' % (
            self.render_opts.get('quality'), self.render_opts.get('target_fps')))
        try:
            footprints.boot(self)
        except Exception as exc:
            print('  footprints skip:', exc)
        try:
            if sfx is not None:
                sfx.boot()
        except Exception as exc:
            print('  sfx skip:', exc)
        try:
            if crash is not None:
                crash.ensure_pools(self)
        except Exception as exc:
            print('  crash pools skip:', exc)
        try:
            if world_chunks is not None:
                world_chunks.boot(self)
        except Exception as exc:
            print('  chunks skip:', exc)
        try:
            apply_lighting(
                color, self.Vec3,
                Sky=self.Sky,
                DirectionalLight=DirectionalLight,
                AmbientLight=AmbientLight,
                PointLight=PointLight,
            )
        except Exception:
            self.Sky(color=color.rgb32(20, 8, 34))

        self._lock_mouse(False)  # boot unlocked; menu owns cursor

        # CC0 / procedural ground + building textures
        tex_map = {
            'grass': load_tex('grass'),
            'asphalt': load_tex('asphalt'),
            'concrete': load_tex('concrete'),
            'brick': load_tex('brick'),
            'stucco': load_tex('stucco'),
            'water': load_tex('water'),
        }
        set_world_textures(tex_map)
        self.world_textures = tex_map

        # PERF: title menu must stay light. Build ONLY safe yard + player + HUD + menu.
        # Full Clermont / crowd / traffic / Tokyo / densify / wildlife wait until gate.
        self._world_populated = False
        self.peds = []
        self.cars = getattr(self, 'cars', None) or []
        self.npcs = getattr(self, 'npcs', None) or []
        self.building_count = int(getattr(self, 'building_count', 0) or 0)

        # Texture sanity — blocky walls usually mean None textures
        loaded = [k for k, v in tex_map.items() if v]
        missing = [k for k, v in tex_map.items() if not v]
        print('  textures loaded=%s missing=%s' % (loaded, missing or 'none'))
        try:
            from assets.generate_textures import ensure_all as _ensure_tex2
            _ensure_tex2()
            # reload any that were missing
            for k in list(missing):
                tex_map[k] = load_tex(k)
            set_world_textures(tex_map)
            self.world_textures = tex_map
        except Exception as _tx:
            print('  textures re-ensure skip:', _tx)

        self._build_safe_yard()
        self._build_player()
        self._build_hud()
        try:
            radar.boot(self)
        except Exception as _radar_exc:
            print('  radar skip:', _radar_exc)
        self._build_menu()
        self._init_quests()
        self._init_tutorial()
        self._rebuild_ignore()

        print('  boot: SLIM (menu/safe only) — world deferred until pink gate')
        print('  buildings=%d quests=%d (world pending)' % (
            self.building_count, len(self.quest_defs)))
        print('named_npcs=0 crowd=0 (deferred)')
        self._show_menu()


    def _tick_named_visibility(self):
        """Keep Michelle / Mira / talk NPCs visible and on the ground near the player."""
        player = self.player
        if not player:
            return
        px, pz = float(player.x), float(player.z)
        for npc in list(getattr(self, 'npcs', None) or []):
            if not npc:
                continue
            kind = getattr(npc, 'kind', '')
            if kind not in ('mira', 'michelle', 'gun', 'talk', 'lila', 'rosa', 'yara'):
                # still un-bury any npc on the list
                pass
            try:
                if getattr(npc, 'y', None) is not None and float(npc.y) < -0.05:
                    npc.y = 0.0
                dx = float(getattr(npc, 'x', 0)) - px
                dz = float(getattr(npc, 'z', 0)) - pz
                if (dx * dx + dz * dz) ** 0.5 <= 52.0:
                    set_visible(npc, True)
            except Exception:
                pass

    def _lock_mouse(self, locked):
        mouse = self.mouse
        try:
            mouse.locked = bool(locked)
            mouse.visible = not locked
        except Exception:
            try:
                mouse.visible = not locked
            except Exception:
                pass

    # ----- title / safe yard ----------------------------------------------

    def _build_safe_yard(self):
        """Fenced practice yard NE of map — WASD/look test; E at gate enters Clermont."""
        Entity = self.Entity
        color = self.color
        Text = self.Text
        cx, cy, cz = self.safe_yard_center
        grass = load_tex('grass')
        # grass pad
        Entity(
            model='cube',
            scale=(28, 0.06, 28),
            position=(cx, 0.03, cz),
            color=color.rgb32(55, 120, 55) if grass else color.rgb32(40, 80, 40),
            texture=grass or 'white_cube',
            texture_scale=(12, 12),
        )
        half = 13.0
        post_c = color.rgb32(90, 70, 50)
        rail_c = color.rgb32(70, 55, 40)
        gate_gap = 1.6  # half-width of west gate opening
        # east / west posts + rails (west leaves gate gap at cz)
        for dx in (-half, half):
            for zi in range(int(cz - half), int(cz + half) + 1, 3):
                if dx < 0 and abs(zi - cz) < gate_gap + 0.5:
                    continue
                Entity(model='cube', scale=(0.18, 1.6, 0.18), position=(cx + dx, 0.8, zi), color=post_c, collider='box')
            if dx > 0:
                Entity(model='cube', scale=(0.12, 0.12, half * 2), position=(cx + dx, 1.15, cz), color=rail_c)
            else:
                # two rail segments around gate
                Entity(model='cube', scale=(0.12, 0.12, half - gate_gap), position=(cx + dx, 1.15, cz - (half + gate_gap) / 2), color=rail_c)
                Entity(model='cube', scale=(0.12, 0.12, half - gate_gap), position=(cx + dx, 1.15, cz + (half + gate_gap) / 2), color=rail_c)
        # north / south full rails
        for dz in (-half, half):
            for xi in range(int(cx - half), int(cx + half) + 1, 3):
                Entity(model='cube', scale=(0.18, 1.6, 0.18), position=(xi, 0.8, cz + dz), color=post_c, collider='box')
            Entity(model='cube', scale=(half * 2, 0.12, 0.12), position=(cx, 1.15, cz + dz), color=rail_c)
        # pink gate (west)
        gate_x, gate_z = cx - half, cz
        self.safe_gate = Entity(
            model='cube',
            scale=(0.35, 2.2, 2.4),
            position=(gate_x, 1.1, gate_z),
            color=color.rgb32(255, 90, 200),
            collider='box',
        )
        self.safe_gate.kind = 'safe_gate'
        # practice props
        cone_c = color.rgb32(255, 120, 40)
        for ox, oz in ((-4, -3), (-2, -5), (3, -4), (5, 2), (-5, 4)):
            Entity(model='cube', scale=(0.35, 0.7, 0.35), position=(cx + ox, 0.35, cz + oz), color=cone_c)
            Entity(model='cube', scale=(0.15, 0.15, 0.15), position=(cx + ox, 0.75, cz + oz), color=color.rgb32(255, 255, 255))
        try:
            dummy = make_car(Entity, color, (cx + 5.5, 0, cz + 5.0), yaw=40, paint=color.rgb32(80, 90, 110))
            if dummy:
                dummy.parked = True
                dummy.traffic = False
                dummy.fuel = 0
                dummy.safe_yard = True
                self.cars.append(dummy)
        except Exception:
            Entity(model='cube', scale=(2.2, 1.0, 4.0), position=(cx + 5.5, 0.55, cz + 5.0), color=color.rgb32(80, 90, 110), collider='box')
        barrel = Entity(model='cube', scale=(0.85, 1.15, 0.85), position=(cx + 4, 0.55, cz - 6), color=color.rgb32(160, 70, 40), collider='box')
        barrel.kind = 'barrel'
        barrel.hittable = True
        barrel.hp = 30
        barrel.npc_name = 'barrel'
        self.targets.append(barrel)
        # labels / billboard controls
        make_billboard(Entity, color, Text, self._scene(), cx, cz + half - 1.0, 'SAFE YARD', face_yaw=0)
        make_billboard(
            Entity, color, Text, self._scene(),
            cx + 8.0, cz - 8.0,
            'CLICK window · WASD · E gate · Tab cursor',
            face_yaw=0,
        )
        make_street_sign(Entity, color, Text, self._scene(), gate_x - 0.8, gate_z, 'LEAVE ->')

    def _build_menu(self):
        from ursina import Button, color as u_color
        Entity = self.Entity
        Text = self.Text
        color = self.color
        camera = self.camera
        self.menu_ents = []
        self.menu_buttons = []
        self.menu_backdrop = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba32(6, 2, 14, 230),
            scale=(2.2, 1.4),
            position=(0, 0),
            z=2,
            enabled=False,
        )
        self.menu_ents.append(self.menu_backdrop)
        neon = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba32(255, 40, 180, 50),
            scale=(1.1, 0.02),
            position=(0, 0.22),
            z=1.9,
            enabled=False,
        )
        self.menu_ents.append(neon)
        self.menu_title = Text(
            text='RUNE MOMMY',
            position=(0, 0.30),
            origin=(0, 0),
            color=color.rgb32(255, 90, 210),
            scale=2.0,
            enabled=False,
            z=-0.1,
        )
        self.menu_ents.append(self.menu_title)
        sub = Text(
            text='Clermont - click a button or press 1 / 2 / 3',
            position=(0, 0.22),
            origin=(0, 0),
            color=color.rgb32(140, 230, 255),
            scale=0.9,
            enabled=False,
            z=-0.1,
        )
        self.menu_ents.append(sub)
        self.menu_lines = []
        # Keep text lines for settings mode reuse
        for i in range(5):
            tline = Text(
                text='',
                position=(0, 0.06 - i * 0.07),
                origin=(0, 0),
                color=color.rgb32(255, 230, 255),
                scale=1.0,
                enabled=False,
                z=-0.1,
            )
            self.menu_lines.append(tline)
            self.menu_ents.append(tline)
        self.settings_lines = []
        for i in range(5):
            tline = Text(
                text='',
                position=(0, 0.08 - i * 0.07),
                origin=(0, 0),
                color=color.rgb32(255, 230, 255),
                scale=1.0,
                enabled=False,
                z=-0.1,
            )
            self.settings_lines.append(tline)
            self.menu_ents.append(tline)

        def mk_btn(label, y, action):
            # Empty Button text + child Text — avoids Ursina Button font-atlas garbage
            # (white pixel blocks) when text_entity scale/parent fights the panel.
            btn = Button(
                text='',
                scale=(0.55, 0.09),
                position=(0, y),
                color=color.rgba32(40, 10, 50, 220),
                highlight_color=color.rgba32(255, 60, 180, 220),
                pressed_color=color.rgba32(180, 40, 120, 240),
                parent=camera.ui,
                enabled=False,
                z=1.5,
            )
            try:
                btn.text_entity.text = ''
                btn.text_entity.enabled = False
            except Exception:
                pass
            # Text parented to UI (not button) with readable scale/color
            lbl = Text(
                text=label,
                parent=camera.ui,
                position=(0, y),
                origin=(0, 0),
                color=color.rgb32(255, 245, 255),
                scale=1.35,
                enabled=False,
                z=1.4,
            )
            btn._label = lbl
            btn.on_click = action
            self.menu_buttons.append(btn)
            self.menu_ents.append(btn)
            self.menu_ents.append(lbl)
            return btn

        self.btn_start = mk_btn('1  Start', 0.06, lambda: self._enter_safe_zone(from_load=False))
        self.btn_load = mk_btn('2  Load', -0.02, lambda: self._try_load_game())
        self.btn_settings = mk_btn('3  Settings', -0.10, lambda: self._enter_settings())
        hint = Text(
            text='Esc quit',
            position=(0, -0.22),
            origin=(0, 0),
            color=color.rgb32(160, 140, 180),
            scale=0.85,
            enabled=False,
            z=-0.1,
        )
        self.menu_ents.append(hint)
        self.menu_hint = hint


    def _set_menu_visible(self, visible):
        vis = bool(visible)
        for e in getattr(self, 'menu_ents', []) or []:
            try:
                e.enabled = vis
            except Exception:
                pass
        # Settings: hide Start/Load/Settings buttons + labels
        if vis and getattr(self, 'mode', '') == 'settings':
            for b in getattr(self, 'menu_buttons', []) or []:
                try:
                    b.enabled = False
                    lab = getattr(b, '_label', None)
                    if lab is not None:
                        lab.enabled = False
                except Exception:
                    pass
            if getattr(self, 'menu_hint', None):
                try:
                    self.menu_hint.enabled = False
                except Exception:
                    pass
        elif vis:
            for b in getattr(self, 'menu_buttons', []) or []:
                try:
                    b.enabled = True
                    lab = getattr(b, '_label', None)
                    if lab is not None:
                        lab.enabled = True
                except Exception:
                    pass
            if getattr(self, 'menu_hint', None):
                try:
                    self.menu_hint.enabled = True
                except Exception:
                    pass
            # spare menu_lines are settings-only; hide on main menu
            for line in getattr(self, 'menu_lines', []) or []:
                try:
                    line.enabled = False
                except Exception:
                    pass
        else:
            for b in getattr(self, 'menu_buttons', []) or []:
                try:
                    b.enabled = False
                    lab = getattr(b, '_label', None)
                    if lab is not None:
                        lab.enabled = False
                except Exception:
                    pass
        if vis:
            self._refresh_menu_labels()
            self.mouse_free = True
            self._lock_mouse(False)
            try:
                self.mouse.visible = True
                self.mouse.locked = False
            except Exception:
                pass


    def _refresh_menu_labels(self):
        if self.mode == 'settings':
            for t in self.menu_lines:
                t.enabled = False
            sens = int(self.mouse_sens)
            fs = 'ON' if getattr(self, 'fullscreen_stub', False) else 'OFF'
            specs = [
                'SETTINGS',
                f'1  Mouse sensitivity  {sens}',
                f'2  Fullscreen (stub)  {fs}',
                '3  Back',
                'Esc back',
            ]
            for i, t in enumerate(self.settings_lines):
                t.text = specs[i] if i < len(specs) else ''
                t.enabled = True
                if i == 0:
                    t.color = self.color.rgb32(255, 90, 210)
            if self.menu_title:
                self.menu_title.enabled = False
        else:
            for t in self.settings_lines:
                t.enabled = False
                t.text = ''
            for t in self.menu_lines:
                t.enabled = True
            if self.menu_title:
                self.menu_title.enabled = True

    def _hide_play_hud(self, hide):
        bits = [
            self.hud_gold, self.hud_hp, self.hud_heat, self.hud_ammo,
            self.hud_pack, self.hud_breed, self.hud_quest, self.hud_mode,
            self.hud_prompt, self.crosshair,
        ]
        for b in bits:
            if b is None:
                continue
            try:
                b.enabled = not hide
            except Exception:
                pass
        # tutorial overlay stays off until play
        if hide:
            try:
                if self.tutorial_overlay:
                    self.tutorial_overlay.enabled = False
                if self.tutorial_text:
                    self.tutorial_text.enabled = False
            except Exception:
                pass

    def _show_menu(self):
        self.mode = 'menu'
        self.world_paused = True
        self.ui_open = False
        self.mouse_free = True
        self._lock_mouse(False)
        try:
            self.mouse.visible = True
            self.mouse.locked = False
        except Exception:
            pass
        self._set_menu_visible(True)
        self._hide_play_hud(True)
        if self.hud_toast:
            self.hud_toast.text = ''

    def _enter_menu(self):
        """Alias — prefer _show_menu."""
        self._show_menu()

    def _enter_settings(self):
        self.mode = 'settings'
        self.world_paused = True
        self.mouse_free = True
        self._lock_mouse(False)
        self._set_menu_visible(True)
        self._hide_play_hud(True)
        self._refresh_menu_labels()

    def _enter_safe_zone(self, from_load=False):
        from ursina import invoke
        self.mode = 'safe'
        self.world_paused = True
        self.ui_open = False
        self.mouse_free = True
        self._set_menu_visible(False)
        self._hide_play_hud(False)
        self._lock_mouse(False)
        try:
            self.mouse.visible = True
            self.mouse.locked = False
        except Exception:
            pass
        cx, cy, cz = self.safe_yard_center
        if self.player:
            # Spawn high and drop so we never clip into floor/props.
            self.player.position = (cx, 6.0, cz)
            self.player.rotation_y = 180
            self.y_vel = 0.0
            self.grounded = False
        msg = 'SAFE YARD — WASD / arrows move, Q/E turn, mouse look. Esc = menu. E at pink gate = Clermont.'
        if from_load:
            msg = 'Loaded. ' + msg
        if not getattr(self, '_safe_yard_toasted', False) or from_load:
            self._safe_yard_toasted = True
            self.toast(msg)  # toast() already prints once — do not print again
        # Refocus after UI button steals keyboard on Windows.
        def _refocus():
            try:
                from ursina import application
                win = application.base.win
                props = win.get_properties() if hasattr(win, 'get_properties') else None
                from panda3d.core import WindowProperties
                wp = WindowProperties()
                wp.setForeground(True)
                win.request_properties(wp)
            except Exception as exc:
                print('[Rune Mommy] refocus skip:', exc)
            try:
                self.mouse.visible = True
                self.mouse.locked = False
            except Exception:
                pass
        try:
            invoke(_refocus, delay=0.05)
            invoke(_refocus, delay=0.25)
        except Exception:
            _refocus()



    def _ensure_world_populated(self):
        """Build Clermont + agents once — called on yard→gate (not at title)."""
        if getattr(self, '_world_populated', False):
            return
        self._world_populated = True
        print('  populating Clermont world (deferred from title)...')
        try:
            self._build_ground()
            self._build_highway()
            self._build_skyline()
            self._build_town_slice()
            self._build_pois()
            self._build_house()
            self._build_stalls()
            self._build_npcs()
            self._build_cars()
            self._build_targets()
            self._build_crowd()
            self._build_traffic()
            self._build_deferred_content()
        except Exception as exc:
            print('  world populate FAILED:', exc)
        try:
            self._rebuild_ignore()
        except Exception:
            pass
        named_n = sum(
            1 for n in (self.npcs or [])
            if n and getattr(n, 'kind', '') in (
                'mira', 'michelle', 'gun', 'talk', 'lila', 'rosa', 'yara'
            )
        )
        crowd_n = len(getattr(self, 'peds', None) or [])
        print('  world ready: buildings=%d named_npcs=%d crowd=%d cars=%d' % (
            self.building_count, named_n, crowd_n, len(getattr(self, 'cars', None) or [])))

    def _leave_safe_to_world(self):
        """Gate exit: jump into Clermont, enable systems."""
        self._ensure_world_populated()
        self.mode = 'play'
        self.world_paused = False
        self.intro_started = True
        self.mouse_free = False
        self._set_menu_visible(False)
        self._hide_play_hud(False)
        self._lock_mouse(True)
        sx, sy, sz = self.clermont_spawn
        if self.player:
            self.player.position = (sx, 0, sz)
            self.player.rotation_y = -90
        # restore tutorial UI if still active
        if self.tutorial_active:
            try:
                if self.tutorial_overlay:
                    self.tutorial_overlay.enabled = True
                if self.tutorial_text:
                    self.tutorial_text.enabled = True
                    self._refresh_tutorial_text()
            except Exception:
                pass
        self._write_local_save()
        flags = self._load_flags()
        flags['intro_started'] = True
        self._save_flags(flags)
        # Reveal ALL named NPCs + crowd after safe-yard → play (cull / y bury / multipart hide).
        try:
            n_show = 0
            for ped in list(getattr(self, 'peds', None) or []) + list(getattr(self, 'npcs', None) or []):
                if not ped:
                    continue
                try:
                    set_visible(ped, True)
                    if getattr(ped, 'y', None) is not None and float(ped.y) < -0.05:
                        ped.y = 0.0
                    try:
                        ped.enabled = True
                    except Exception:
                        pass
                    n_show += 1
                except Exception:
                    pass
            print('  reveal_npcs=%d (named+crowd) after yard→gate' % n_show)
        except Exception as exc:
            print('  reveal_npcs skip:', exc)
        self.toast('Clermont. Michelle is at Sanctuary Drive — E to talk.')

    def _save_path(self):
        return ROOT / 'data' / 'local_save.json'

    def _write_local_save(self):
        flags = self._load_flags()
        tutorial_done = bool(flags.get('tutorial_done')) or (not self.tutorial_active)
        data = {
            'gold': int(self.gold),
            'hp': int(self.hp),
            'breed': int(self.breed),
            'preg': bool(self.preg),
            'owned_pistol': bool(self.owned_pistol),
            'pistol': bool(self.owned_pistol),
            'ammo': int(self.ammo),
            'pack': list(self.pack),
            'tutorial_done': tutorial_done,
            'intro_started': bool(self.intro_started),
            'michelle_seen': bool(self.michelle_seen),
            'mouse_sens': float(self.mouse_sens),
            'cam_mode': str(getattr(self, 'cam_mode', 'follow') or 'follow'),
        }
        path = self._save_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        except Exception as exc:
            print('  local_save failed:', exc)

    def _load_local_save(self):
        path = self._save_path()
        if not path.exists():
            # honor flags-only as a soft save marker? require local_save for Load
            return None
        try:
            return json.loads(path.read_text(encoding='utf-8')) or {}
        except Exception:
            return None

    def _apply_local_save(self, data):
        if not data:
            return
        self.gold = int(data.get('gold', self.gold))
        self.hp = int(data.get('hp', self.hp))
        self.breed = int(data.get('breed', self.breed))
        self.preg = bool(data.get('preg', self.preg))
        self.owned_pistol = bool(data.get('pistol', data.get('owned_pistol', self.owned_pistol)))
        self.ammo = int(data.get('ammo', self.ammo))
        self.pack = list(data.get('pack') or [])
        self.intro_started = bool(data.get('intro_started', False))
        self.michelle_seen = bool(data.get('michelle_seen', False))
        if 'mouse_sens' in data:
            try:
                self.mouse_sens = float(data['mouse_sens'])
            except Exception:
                pass
        if 'cam_mode' in data:
            try:
                cm = str(data.get('cam_mode') or 'follow').strip().lower()
                if cm in ('follow', 'near', 'far', 'hood'):
                    self.cam_mode = cm
            except Exception:
                pass
        if data.get('tutorial_done'):
            self.tutorial_active = False
            try:
                if self.tutorial_overlay:
                    self.tutorial_overlay.enabled = False
                if self.tutorial_text:
                    self.tutorial_text.enabled = False
            except Exception:
                pass
            flags = self._load_flags()
            flags['tutorial_done'] = True
            self._save_flags(flags)
        if self.preg:
            try:
                self._apply_preg_look()
            except Exception:
                pass

    def _try_load_game(self):
        data = self._load_local_save()
        if not data:
            self.toast('No save yet')
            return
        self._apply_local_save(data)
        if data.get('intro_started'):
            self.mode = 'play'
            self.world_paused = False
            self._set_menu_visible(False)
            self._hide_play_hud(False)
            self.mouse_free = False
            self._lock_mouse(True)
            sx, sy, sz = self.clermont_spawn
            if self.player:
                self.player.position = (sx, 0, sz)
                self.player.rotation_y = -90
            self.toast('Clermont. Michelle is at Sanctuary Drive — E to talk.')
        else:
            self._enter_safe_zone(from_load=True)

    # ----- world ----------------------------------------------------------

    def _build_ground(self):
        Entity = self.Entity
        color = self.color
        grass = load_tex('grass')
        asphalt = load_tex('asphalt')
        Entity(
            model='plane',
            scale=(220, 1, 200),
            color=color.rgb32(48, 90, 42) if grass else color.rgb32(32, 24, 36),
            texture=grass or 'white_cube',
            texture_scale=(70, 55),
            collider=None,
            y=0,
        )
        # Lot asphalt split N/S of Hwy 50 — unique Y, no stack under highway footprint.
        lot_col = color.rgb32(36, 34, 38) if asphalt else color.rgb32(24, 18, 28)
        lot_tex = asphalt or 'white_cube'
        # North lot (stalls side): z center -5.5, depth ~9 → avoids hwy ~-20.75..-11.25
        Entity(
            model='cube',
            scale=(78, 0.04, 10),
            position=(2, 0.02, -5.5),
            color=lot_col,
            texture=lot_tex,
            texture_scale=(8, 2),
        )
        # South lot (town side)
        Entity(
            model='cube',
            scale=(78, 0.04, 22),
            position=(2, 0.02, -32),
            color=lot_col,
            texture=lot_tex,
            texture_scale=(8, 2),
        )

    def _build_highway(self):
        Entity = self.Entity
        color = self.color
        # Hwy 50 east-west between the two stall rows — Y unique vs lot/paint/sidewalk
        asphalt = load_tex('asphalt')
        concrete = load_tex('concrete')
        Entity(
            model='cube',
            scale=(88, 0.08, 9.5),
            position=(2, 0.09, -16),
            color=color.rgb32(28, 26, 30) if asphalt else color.rgb32(18, 16, 20),
            texture=asphalt,
            texture_scale=(8, 2),
        )
        for x in range(-40, 44, 5):
            Entity(
                model='cube',
                scale=(2.2, 0.09, 0.18),
                position=(x, 0.12, -16),
                color=color.rgb32(230, 200, 60),
            )
        # sidewalks
        Entity(model='cube', scale=(88, 0.07, 1.6), position=(2, 0.07, -10.4),
               color=color.rgb32(120, 115, 110) if concrete else color.rgb32(48, 38, 52),
               texture=concrete, texture_scale=(40, 1))
        Entity(model='cube', scale=(88, 0.07, 1.6), position=(2, 0.07, -21.6),
               color=color.rgb32(120, 115, 110) if concrete else color.rgb32(48, 38, 52),
               texture=concrete, texture_scale=(40, 1))
        # street lamps
        for x in (-28, -12, 0, 14, 28):
            for z in (-10.2, -21.8):
                Entity(model='cube', scale=(0.12, 3.2, 0.12), position=(x, 1.6, z), color=color.rgb32(40, 30, 50))
                Entity(model='sphere', scale=0.35, position=(x, 3.3, z), color=color.rgb32(255, 90, 200))

    def _build_skyline(self):
        Entity = self.Entity
        color = self.color
        Text = self.Text
        rng = random.Random(50)
        # denser background strip-mall / midrise — composed, not single cubes
        for i in range(12):
            w, h, d = rng.uniform(3.2, 6.5), rng.uniform(4.5, 11.0), rng.uniform(3.0, 5.5)
            x = -42 + i * 7.8 + rng.uniform(-0.6, 0.6)
            z = 18 + rng.uniform(0, 3)
            if math.hypot(x + 32.0, z - 12.0) < 14.0:
                continue
            body = color.rgb32(rng.randint(28, 55), rng.randint(16, 40), rng.randint(40, 70))
            Entity(model='cube', scale=(w, h, d), position=(x, h / 2, z), color=body,
                   texture=load_tex('brick') or load_tex('stucco'), texture_scale=(2.5, 2.0), collider='box')
            Entity(model='cube', scale=(w + 0.3, 0.2, d + 0.3), position=(x, h + 0.1, z), color=body.tint(0.15) if hasattr(body, 'tint') else body)
            # window grid
            for wy in (0.35, 0.55, 0.75):
                Entity(model='cube', scale=(w * 0.7, 0.18, 0.06), position=(x, h * wy, z - d / 2 - 0.02),
                       color=color.rgb32(80, 160, 220))
            self.building_count += 1
        for i in range(8):
            w, h, d = rng.uniform(3, 5.5), rng.uniform(3.2, 8.0), rng.uniform(3, 5)
            x = -34 + i * 10
            z = -50
            Entity(model='cube', scale=(w, h, d), position=(x, h / 2, z),
                   color=color.rgb32(rng.randint(30, 60), rng.randint(18, 36), rng.randint(28, 50)),
                   texture=load_tex('stucco') or load_tex('brick'), texture_scale=(2.2, 1.8), collider='box')
            Entity(model='cube', scale=(w + 0.2, 0.15, d + 0.2), position=(x, h + 0.08, z), color=color.rgb32(60, 40, 80))
            self.building_count += 1
        for x, z in ((-30, 6), (26, 8), (-22, -38), (24, -38), (40, -10), (-36, -8), (8, 10), (-8, -42)):
            if math.hypot(x + 32.0, z - 12.0) < 12.0:
                continue
            Entity(model='cube', scale=(0.28, 2.4, 0.28), position=(x, 1.2, z), color=color.rgb32(70, 42, 28), collider='box')
            Entity(model='sphere', scale=1.6, position=(x, 2.8, z), color=color.rgb32(30, 110, 55))

    def _build_town_slice(self):
        """Residential south of Hwy 50 + Sanctuary Drive row (~12 labeled houses)."""
        Entity = self.Entity
        color = self.color
        Text = self.Text
        rng = random.Random(77)
        # older south row
        houses = (
            (-28, -34, 'Maple Ct'), (-18, -38, 'Oak Lane'), (-6, -36, 'Cypress'),
            (8, -39, 'Pine Row'), (20, -35, 'Bay St'), (32, -37, 'Lakeview'),
            (-32, -42, 'Hickory'), (12, -44, 'Magnolia'),
        )
        for x, z, label in houses:
            w, h, d = rng.uniform(2.8, 4.0), rng.uniform(2.4, 3.4), rng.uniform(2.6, 3.4)
            try:
                x, z, ok = footprints.place_or_nudge(self, x, z, w=w, d=d, label=label)
                if not ok:
                    continue
            except Exception:
                pass
            make_house(
                Entity, color, Text, self._scene(), x, z,
                w=w, h=h, d=d, label=label, porch=True, garage=(rng.random() < 0.4), rng=rng,
            )
            self.building_count += 1
        # Sanctuary Drive neighborhood — 10 more houses west/north of Michelle
        sanctuary_row = (
            (-40, 8, '412 Sanctuary'), (-40, 16, '418 Sanctuary'),
            (-36, 20, '422 Sanctuary'), (-28, 20, '428 Sanctuary'),
            (-24, 18, '430 Sanctuary'), (-20, 14, '434 Sanctuary'),
            (-44, 12, '408 Sanctuary'), (-38, 4, '410 Sanctuary'),
            (-26, 8, '436 Sanctuary'), (-22, 6, '438 Sanctuary'),
        )
        teal = color.rgb32(46, 196, 182)
        for i, (x, z, label) in enumerate(sanctuary_row):
            if math.hypot(x + 32.0, z - 12.0) < 9.0:
                continue
            ww, dd = rng.uniform(3.2, 4.2), rng.uniform(2.8, 3.6)
            try:
                x, z, ok = footprints.place_or_nudge(self, x, z, w=ww, d=dd, label=label)
                if not ok:
                    continue
            except Exception:
                pass
            roof = teal if i % 3 == 0 else color.rgb32(rng.randint(50, 100), rng.randint(80, 140), rng.randint(100, 160))
            make_house(
                Entity, color, Text, self._scene(), x, z,
                w=ww, h=rng.uniform(2.5, 3.3), d=dd,
                roof_col=roof, label=label, porch=True, garage=(i % 2 == 0), rng=rng,
            )
            self.building_count += 1
        for x in (-32, -16, 4, 18, 34):
            z = -32.0
            Entity(model='cube', scale=(0.12, 3.0, 0.12), position=(x, 1.5, z), color=color.rgb32(40, 30, 50))
            Entity(model='sphere', scale=0.32, position=(x, 3.15, z), color=color.rgb32(255, 90, 200))
        make_street_sign(Entity, color, Text, self._scene(), -30.0, 10.5, 'Sanctuary Dr')
        make_street_sign(Entity, color, Text, self._scene(), 2.0, -22.5, 'E Hwy 50')
        make_billboard(Entity, color, Text, self._scene(), -10.0, -8.5, 'COOL DOWN\n@ MIRA', face_yaw=0)
        make_billboard(Entity, color, Text, self._scene(), 28.0, -20.5, 'HANCOCK\nGUN HUT', face_yaw=0)
        self.building_count += 4

    def _build_pois(self):
        """Gas, motel, laundry, Starbucks-ish, pharmacy, park + Clermont landmarks."""
        Entity = self.Entity
        color = self.color
        Text = self.Text
        self.pois = []
        specs = (
            ('gas', 18.0, -8.0, 'rita'),
            # Hwy 27 Fuel — US-27 near Club 27 / east
            ('gas_hwy27', 38.0, -14.0, None),
            ('motel', -8.0, 6.5, 'motel_clerk'),
            ('laundromat', 8.0, 5.0, 'lot_attendant'),
            ('starbucks', -20.0, -10.5, 'barista'),
            ('pharmacy', 30.0, -28.0, 'pharmacist'),
            ('park', -14.0, -28.0, 'amanda_friend'),
            # Club 27 Cabaret — 215 US Hwy 27, Clermont FL 34714 (east/south of Hwy 50)
            ('club27', 40.0, -20.0, 'club27_host'),
            # Quiet Spa — Hwy 50 west of shake row
            ('quiet_spa', -36.0, -16.0, 'quiet_spa_tech'),
            # Citrus Tower — US-27 north of Hwy 50
            ('citrus_tower', 36.0, 6.0, 'citrus_guide'),
            # Waterfront Park / Lake Minneola — SE of downtown slice
            ('waterfront', 16.0, -42.0, 'park_ranger'),
            # roadside kitsch density (buildings only — no shared NPC overwrite)
            ('showcase_citrus', 28.0, -6.0, None),
            ('presidents_hall', 44.0, -8.0, None),
        )
        for kind, x, z, npc_id in specs:
            try:
                x, z, ok = footprints.place_or_nudge(self, x, z, w=6.0, d=5.0, label='poi_'+kind)
                if not ok:
                    print('  poi skip (footprint):', kind)
                    continue
            except Exception:
                pass
            parts, interact, label = make_poi_building(Entity, color, Text, self._scene(), kind, x, z)
            self.building_count += 1
            is_gas = kind in ('gas', 'gas_hwy27') or (label or '').lower().find('gas') >= 0 or (label or '').lower().find('fuel') >= 0
            self.pois.append({
                'id': kind,
                'name': label,
                'pos': (interact[0], 0, interact[2]),
                'npc_id': npc_id,
                'line': None,
                'is_gas': is_gas,
                'pump_r': 4.2 if is_gas else 3.4,
            })

    def _build_house(self):
        """Suburban cubes at about (-32, 0, 12). Body, teal roof, garage, door, back lawn, Sanctuary Drive."""
        Entity = self.Entity
        color = self.color
        Text = self.Text
        teal = color.rgb32(46, 196, 182)
        body_col = color.rgb32(232, 214, 188)
        wood = color.rgb32(90, 55, 40)
        hx, hz = -32.0, 12.0
        self.house_vols = []
        self.sanctuary_pos = (hx, 0.0, hz)
        try:
            footprints.get(self).register(hx, hz, 10.0, 8.0, 'michelle_house')
        except Exception:
            pass

        # lot grass + darker back-lawn swamp strip (west) + driveway (east)
        grass = load_tex('grass')
        asphalt = load_tex('asphalt')
        stucco = load_tex('stucco')
        concrete = load_tex('concrete')
        Entity(model='cube', scale=(16, 0.05, 14), position=(hx - 1.0, 0.025, hz),
               color=color.rgb32(34, 88, 46), texture=grass, texture_scale=(8, 7))
        Entity(model='cube', scale=(7.5, 0.06, 12), position=(hx - 7.2, 0.03, hz),
               color=color.rgb32(16, 42, 28), texture=grass, texture_scale=(4, 6))
        Entity(model='cube', scale=(6.2, 0.07, 5.6), position=(hx + 6.4, 0.035, hz),
               color=color.rgb32(48, 44, 50), texture=asphalt or concrete, texture_scale=(3, 2.5))

        # Walk-in body shell — east door gap (no solid front collider)
        _stucco = stucco if stucco is not None and not isinstance(stucco, str) else None
        hollow_shell(
            Entity, color, hx, hz, 8.0, 6.4, 3.2, body_col,
            door_gap=1.2, door_face='e',
            floor_col=color.rgb32(140, 110, 80),
            ceil_col=color.rgb32(232, 214, 188),
            wall_tex=_stucco,
        )
        # A-frame roof: ridge above wall top (h=3.2 → ridge ~3.75), ±28 slopes
        Entity(model='cube', scale=(8.6, 0.22, 3.6), position=(hx - 1.2, 3.63, hz), color=teal, rotation_z=-28)
        Entity(model='cube', scale=(8.6, 0.22, 3.6), position=(hx + 1.2, 3.63, hz), color=teal, rotation_z=28)
        Entity(model='cube', scale=(0.22, 0.14, 7.0), position=(hx, 3.83, hz), color=color.rgb32(245, 248, 252))
        for wz in (-1.6, 1.6):
            Entity(model='cube', scale=(0.08, 0.7, 0.7), position=(hx + 4.05, 1.7, hz + wz), color=color.rgb32(120, 200, 230))
        Entity(model='cube', scale=(2.8, 0.14, 2.2), position=(hx + 5.2, 0.1, hz),
               color=color.rgb32(170, 160, 140), texture=concrete, texture_scale=(2, 1.5))
        Entity(model='cube', scale=(0.14, 2.0, 0.14), position=(hx + 5.8, 1.05, hz + 0.9), color=wood)
        Entity(model='cube', scale=(0.14, 2.0, 0.14), position=(hx + 5.8, 1.05, hz - 0.9), color=wood)
        Entity(model='cube', scale=(0.7, 0.5, 0.55), position=(hx - 4.3, 0.4, hz + 2.2), color=color.rgb32(70, 78, 90))
        # garage south of body
        Entity(model='cube', scale=(5.4, 2.5, 4.6), position=(hx + 0.2, 1.25, hz - 5.4),
               color=color.rgb32(210, 196, 176), texture=stucco, texture_scale=(2, 1.4), collider='box')
        Entity(model='cube', scale=(5.6, 0.28, 4.8), position=(hx + 0.2, 2.62, hz - 5.4), color=teal)
        Entity(model='cube', scale=(3.4, 1.9, 0.12), position=(hx + 2.7, 1.0, hz - 5.4), color=color.rgb32(70, 78, 90))
        door = Entity(model='cube', scale=(0.16, 2.15, 1.05), position=(hx + 4.08, 1.12, hz), color=wood)
        self.sanctuary_door = door
        Entity(model='cube', scale=(1.5, 0.16, 1.7), position=(hx + 4.9, 0.1, hz), color=color.rgb32(180, 180, 175))
        self.building_count += 2

        # guest bed + shower markers inside
        Entity(model='cube', scale=(2.2, 0.42, 1.5), position=(hx + 1.8, 0.45, hz + 1.5), color=color.rgb32(220, 210, 200))
        Entity(model='cube', scale=(1.35, 1.9, 1.35), position=(hx - 2.1, 1.05, hz + 1.7), color=color.rgb32(180, 220, 215))

        door_xz = (hx + 4.1, hz)
        guest_xz = (hx + 1.8, hz + 1.5)
        garage_xz = (hx + 0.2, hz - 5.4)
        shower_xz = (hx - 2.1, hz + 1.7)
        lawn_xz = (hx - 7.2, hz)
        self.house_rooms = {
            'door': door_xz,
            'guest': guest_xz,
            'garage': garage_xz,
            'shower': shower_xz,
            'lawn': lawn_xz,
        }

        def vol(xz, sx, sz, col, node):
            e = Entity(model='cube', scale=(sx, 0.06, sz), position=(xz[0], 0.12, xz[1]), color=col)
            e.room_node = node
            self.house_vols.append(e)
            return e

        vol(guest_xz, 3.0, 2.4, color.rgb32(70, 180, 170), 'guest')
        vol(garage_xz, 3.6, 3.2, color.rgb32(70, 70, 78), 'garage')
        vol(shower_xz, 2.2, 2.2, color.rgb32(90, 200, 210), 'shower')
        vol(lawn_xz, 4.2, 5.0, color.rgb32(22, 58, 32), 'lawn')
        vol(door_xz, 2.2, 2.2, color.rgb32(90, 70, 55), 'door')

        Entity(model='cube', scale=(0.14, 2.8, 0.14), position=(hx + 7.4, 1.4, hz + 3.4), color=color.rgb32(70, 60, 50))
        Entity(model='cube', scale=(2.8, 0.7, 0.08), position=(hx + 7.4, 2.7, hz + 3.4), color=teal)
        _sd = Text(
            parent=self._scene(),
            text='Sanctuary Drive',
            position=(hx + 7.4, 3.4, hz + 3.4),
            origin=(0, 0),
            billboard=True,
            color=teal,
        )
        try:
            _sd.world_scale = 2.6
        except Exception:
            pass

        # Michelle at the door — teal shirt, not hittable
        michelle = self._humanoid(
            door_xz[0],
            door_xz[1],
            shirt=color.rgb32(46, 196, 182),
            pants=color.rgb32(245, 245, 240),
            skin=color.rgb32(255, 214, 170),
            detail='named',
            style='michelle',
        )
        michelle.npc_id = 'michelle'
        michelle.npc_name = 'Michelle'
        michelle.kind = 'michelle'
        michelle.hittable = False
        michelle.line = "Alec, I just got off the plane, can you not stare at my tits for five seconds?"
        michelle.portrait_tex = None
        try:
            rel = portrait_asset_path('michelle')
        except Exception:
            rel = None
        if rel:
            try:
                from ursina import load_texture
                tex = load_texture(rel)
                michelle.portrait_tex = tex
                bill = Entity(
                    parent=michelle,
                    model='quad',
                    texture=tex,
                    scale=(1.05, 1.4),
                    position=(0, 1.45, -0.55),
                    double_sided=True,
                )
                try:
                    bill.billboard = True
                except Exception:
                    pass
                try:
                    bill.keep_on_outfit_swap = True
                except Exception:
                    pass
            except Exception:
                michelle.portrait_tex = None
        self.npcs.append(michelle)
        self.michelle = michelle
        michelle._feminine_adult = True
        michelle._base_style = 'michelle'

    def _build_stalls(self):

        Entity = self.Entity
        color = self.color
        Text = self.Text
        shops = list((self.shops_data or {}).get('shops') or [])
        for shop in shops:
            # Food trucks / big-box placed by densify helpers — do not double-spawn as shake stalls
            if shop.get('kind') in ('food_truck', 'big_box', 'retail', 'tire_shop', 'nail_salon', 'akihabara_shop'):
                continue
            sid = shop.get('id', '')
            name = shop.get('name', sid)
            pal = shop.get('palette') or ['#ff4fd8', '#5af0ff', '#1a081c']
            is_gun = sid == 'gun_hut' or 'gun' in name.lower()
            if is_gun:
                x, z = 36.0, 4.0
                w, d, h = 4.2, 3.6, 3.1
                body_col = hex_color(pal[0])
                accent = hex_color(pal[1])
                try:
                    x, z, ok = footprints.place_or_nudge(self, x, z, w=w, d=d, label=sid or 'gun_hut')
                    if not ok:
                        continue
                except Exception:
                    pass
                make_shop_stall(Entity, color, Text, self._scene(), x, z, w, d, h, body_col, accent, accent, name, is_gun=True)
            else:
                x, z = tile_to_world(shop.get('tileX', 16), shop.get('tileY', 7))
                w = max(3.2, float(shop.get('w', 4)) * 0.85)
                d = max(2.8, float(shop.get('h', 4)) * 0.7)
                h = 2.35 if shop.get('flagship') else 2.05
                try:
                    x, z, ok = footprints.place_or_nudge(self, x, z, w=w, d=d, label=sid or name or 'stall')
                    if not ok:
                        continue
                except Exception:
                    pass
                body_col = hex_color(pal[2] if len(pal) > 2 else pal[0]).tint(-0.15)
                neon = hex_color(pal[0])
                trim = hex_color(pal[1] if len(pal) > 1 else pal[0])
                make_shop_stall(Entity, color, Text, self._scene(), x, z, w, d, h, body_col, neon, trim, name, is_gun=False)
            self.building_count += 1
            rec = {
                'id': sid,
                'name': name,
                'kind': 'gun' if is_gun else 'shake',
                'pos': (x, 0, z),
                'shop': shop,
                'npc': shop.get('npcName', ''),
            }
            self.stalls.append(rec)
            if sid in SHAKE_IDS:
                self.shake_spawned.append(name)

        # fill any missing shake names as extra labeled boxes so all 10 exist
        have = {s['id'] for s in self.stalls}
        lookup = {s.get('id'): s for s in shops}
        for sid in SHAKE_IDS:
            if sid in have:
                continue
            shop = lookup.get(sid, {'id': sid, 'name': sid, 'palette': ['#ff4fd8']})
            x, z = tile_to_world(shop.get('tileX', 0), shop.get('tileY', 7))
            Entity(model='cube', scale=(3.2, 2.0, 2.8), position=(x, 1.0, z), color=hex_color((shop.get('palette') or ['#ff4fd8'])[0]), collider='box')
            self.stalls.append({'id': sid, 'name': shop.get('name', sid), 'kind': 'shake', 'pos': (x, 0, z), 'shop': shop, 'npc': shop.get('npcName', '')})
            self.shake_spawned.append(shop.get('name', sid))


    def _build_deferred_content(self):
        """Life-sim, interiors, food trucks, Walmart, lakes/gators, Hwy densify."""
        Entity = self.Entity
        color = self.color
        Text = self.Text
        # densify map
        try:
            added = densify_hwy50(Entity, color, Text, self._scene(), game=self)
            self.building_count += int(added or 0)
        except Exception as exc:
            print('  densify skip:', exc)
        # Walmart exterior (far east)
        try:
            n, interact = make_walmart(Entity, color, Text, self._scene(), 62.0, -18.0)
            self.building_count += 1
            self.pois.append({
                'id': 'walmart', 'name': 'Walmart', 'pos': (interact[0], 0, interact[2]),
                'npc_id': None, 'line': None, 'is_gas': False, 'pump_r': 3.4,
            })
        except Exception as exc:
            print('  walmart skip:', exc)
        # Retail: Pet Store / Best Buy / GameStop / Tire shop (shops.json append-only)
        shop_lookup_early = {s.get('id'): s for s in (self.shops_data or {}).get('shops') or []}
        retail_specs = [
            ('pet_store_clermont', -22.0, 6.5, 7.0, 5.5, 3.2, (126, 200, 227), (255, 159, 28)),
            ('bestbuy_clermont', 28.0, 7.5, 10.0, 7.0, 3.6, (0, 70, 190), (255, 242, 0)),
            ('gamestop_clermont', 8.0, 6.0, 6.0, 5.0, 3.0, (20, 20, 24), (227, 24, 55)),
        ]
        for sid, x, z, w, d, h, body, accent in retail_specs:
            shop = shop_lookup_early.get(sid) or {'id': sid, 'name': sid, 'stock': []}
            try:
                try:
                    x, z, ok = footprints.place_or_nudge(self, x, z, w=w, d=d, label=sid)
                    if not ok:
                        print('  retail overlap skip', sid)
                        continue
                except Exception:
                    pass
                n, interact = make_retail_box(
                    Entity, color, Text, self._scene(), x, z,
                    name=shop.get('name', sid), w=w, d=d, h=h,
                    body_rgb=body, accent_rgb=accent,
                )
                self.building_count += 1
                rec = {
                    'id': sid, 'name': shop.get('name', sid), 'kind': 'retail',
                    'pos': (interact[0], 0, interact[2]), 'shop': shop,
                    'npc': shop.get('npcName', ''),
                }
                self.stalls.append(rec)
                self.pois.append({
                    'id': sid, 'name': shop.get('name', sid),
                    'pos': (interact[0], 0, interact[2]),
                    'npc_id': None, 'line': None, 'is_gas': False, 'pump_r': 3.0,
                })
            except Exception as exc:
                print('  retail skip', sid, exc)
        try:
            shop = shop_lookup_early.get('tire_shop_clermont') or {
                'id': 'tire_shop_clermont', 'name': 'Hwy 50 Tire & Lube', 'stock': []}
            n, interact = make_tire_shop(
                Entity, color, Text, self._scene(), 42.0, -6.5,
                name=shop.get('name', 'Tire Shop'),
            )
            self.building_count += 1
            rec = {
                'id': 'tire_shop_clermont', 'name': shop.get('name', 'Tire Shop'),
                'kind': 'tire_shop', 'pos': (interact[0], 0, interact[2]),
                'shop': shop, 'npc': shop.get('npcName', 'Rico'),
            }
            self.stalls.append(rec)
            self.pois.append({
                'id': 'tire_shop_clermont', 'name': shop.get('name', 'Tire Shop'),
                'pos': (interact[0], 0, interact[2]),
                'npc_id': None, 'line': None, 'is_gas': False, 'pump_r': 3.0,
            })
        except Exception as exc:
            print('  tire shop skip:', exc)
        try:
            shop = shop_lookup_early.get('nail_salon_clermont') or {
                'id': 'nail_salon_clermont', 'name': 'Neon Toes Nail Salon', 'stock': []}
            n, interact = make_retail_box(
                Entity, color, Text, self._scene(), -14.0, 7.2,
                name=shop.get('name', 'Neon Toes'), w=6.5, d=5.0, h=3.0,
                body_rgb=(255, 105, 180), accent_rgb=(255, 240, 245),
            )
            self.building_count += 1
            rec = {
                'id': 'nail_salon_clermont', 'name': shop.get('name', 'Neon Toes'),
                'kind': 'nail_salon', 'pos': (interact[0], 0, interact[2]),
                'shop': shop, 'npc': shop.get('npcName', 'Vee'),
            }
            self.stalls.append(rec)
            self.pois.append({
                'id': 'nail_salon_clermont', 'name': shop.get('name', 'Nail Salon'),
                'pos': (interact[0], 0, interact[2]),
                'npc_id': None, 'line': None, 'is_gas': False, 'pump_r': 3.0,
            })
        except Exception as exc:
            print('  nail salon skip:', exc)

        # Food trucks from shops.json
        self.food_trucks = []
        trucks = [
            ('foodtruck_cuban', -12.0, -8.5, 90, (244, 211, 94), (238, 150, 75)),
            ('foodtruck_gator', 22.0, -9.0, -90, (42, 157, 143), (233, 196, 106)),
            ('foodtruck_midnight', -6.0, 4.5, 180, (231, 111, 81), (244, 162, 97)),
        ]
        shop_lookup = {s.get('id'): s for s in (self.shops_data or {}).get('shops') or []}
        for sid, x, z, yaw, body, accent in trucks:
            shop = shop_lookup.get(sid) or {'id': sid, 'name': sid, 'stock': []}
            try:
                n, interact = make_food_truck(
                    Entity, color, Text, self._scene(), x, z,
                    name=shop.get('name', sid), body_rgb=body, accent_rgb=accent, yaw=yaw,
                )
            except Exception as exc:
                print('  foodtruck skip', sid, exc)
                continue
            rec = {
                'id': sid,
                'name': shop.get('name', sid),
                'kind': 'food_truck',
                'pos': (interact[0], 0, interact[2]),
                'shop': shop,
                'npc': shop.get('npcName', ''),
            }
            self.food_trucks.append(rec)
            self.stalls.append(rec)
            self.building_count += 1
        # interiors + wildlife + life-sim
        try:
            interiors.build_all(self)
        except Exception as exc:
            print('  interiors skip:', exc)
        try:
            wildlife.build_florida_water(self)
        except Exception as exc:
            print('  wildlife skip:', exc)
        try:
            life_sim.boot(self)
        except Exception as exc:
            print('  life_sim skip:', exc)
        # Tokyo / Akihabara portal + far district (after Clermont world exists)
        try:
            tokyo.boot(self)
        except Exception as exc:
            print('  tokyo skip:', exc)
        try:
            footprints.log_summary(self)
        except Exception:
            pass

    def _scene(self):
        from ursina import scene
        return scene

    def _build_npcs(self):
        Entity = self.Entity
        color = self.color
        portrait = None
        mp = self.mira_portrait_path
        mp_ok = False
        try:
            mp_ok = Path(mp).exists() if mp else False
        except Exception:
            mp_ok = False
        if mp_ok:
            try:
                from ursina import load_texture
                _rel = portrait_asset_path('mira') or (str(mp) if mp else None)
                portrait = load_texture(_rel) if _rel else None
                self.mira_texture = portrait
            except Exception:
                portrait = None
                self.mira_texture = None

        shake = next((s for s in self.stalls if s['id'] == 'shake_bar'), None)
        mx, mz = (0.0, -2.6)
        if shake:
            mx, mz = shake['pos'][0], shake['pos'][2] - 2.4

        mira = self._humanoid(mx, mz, shirt=color.rgb32(255, 70, 180), pants=color.rgb32(40, 12, 40), skin=color.rgb32(255, 206, 166), detail='named', style='anime_f')
        mira.npc_id = 'mira'
        mira.npc_name = 'Mama Mira'
        mira.kind = 'mira'
        mira.hittable = False
        self.talk_npcs.append({'ent': mira, 'name': 'Mama Mira', 'talk': 'Neons loud tonight.', 'killable': False})
        if portrait:
            bill = Entity(
                parent=mira,
                model='quad',
                texture=portrait,
                scale=(1.15, 1.55),
                position=(0, 1.45, -0.55),
                double_sided=True,
            )
            try:
                bill.billboard = True
            except Exception:
                pass
        self.npcs.append(mira)

        gun = next((s for s in self.stalls if s['kind'] == 'gun'), None)
        gx, gz = (36.0, 2.2)
        if gun:
            gx, gz = gun['pos'][0], gun['pos'][2] - 2.3
        gage = self._humanoid(gx, gz, shirt=color.rgb32(90, 55, 30), pants=color.rgb32(30, 24, 20), skin=color.rgb32(210, 170, 130), detail='named')
        gage.npc_id = 'gage'
        gage.npc_name = 'Gage'
        gage.kind = 'gun'
        gage.hittable = False
        self.npcs.append(gage)
        self.talk_npcs.append({'ent': gage, 'name': 'Gage', 'talk': 'Cash on the plank.', 'killable': False})

        steak = next((s for s in self.stalls if s['id'] == 'steak_n_shake'), None)
        if steak:
            deb = self._humanoid(steak['pos'][0], steak['pos'][2] - 2.2, shirt=color.rgb32(245, 210, 50), pants=color.rgb32(20, 20, 20), detail='named')
            deb.npc_id = 'deb'
            deb.npc_name = 'Diner Deb'
            deb.kind = 'talk'
            deb.line = 'Same lot as Mira. Vanilla, chocolate, strawberry, or the black-and-white.'
            self.npcs.append(deb)

        # Extra talkable Clermont NPCs from npcs.json. Keep them off Mira.
        talk_spots = {
            'lila': (-14.0, 5.5),
            'yara': (8.0, -26.5),
            'rosa': (mx - 3.2, mz + 0.4),
            'tavi': (-24.0, -20.0),
            'rook': (26.0, 7.0),
            'rita': (18.0, -13.0),
            'motel_clerk': (-8.0, 4.2),
            'barista': (-20.0, -12.8),
            'pharmacist': (30.0, -30.2),
            'neighbor': (-40.0, 10.5),
            'lot_attendant': (8.0, 2.8),
            'amanda_friend': (-14.0, -30.0),
        }
        # place POI NPCs from self.pois (adds new ids + refreshes positions)
        for poi in getattr(self, 'pois', []) or []:
            nid = poi.get('npc_id')
            if nid:
                talk_spots[nid] = (poi['pos'][0], poi['pos'][2])
        for nid, (nx, nz) in talk_spots.items():
            spec = (self.npcs_data or {}).get(nid) or {'id': nid, 'name': nid.title(), 'greet': '...'}
            shirt = hex_color(spec.get('color') or '#ff8fab')
            female_ids = ('lila', 'rosa', 'yara', 'rita', 'deb', 'neighbor', 'barista', 'amanda_friend', 'motel_clerk', 'pharmacist', 'tavi')
            named = nid in ('lila', 'rosa', 'yara', 'rita', 'deb')
            fem = nid in female_ids
            npc = self._humanoid(
                nx, nz, shirt=shirt, pants=color.rgb32(36, 24, 40),
                skin=color.rgb32(255, 200, 160),
                detail='anime_f' if fem else ('named' if named else 'crowd'),
                style='anime_f' if fem else None,
            )
            npc.npc_id = nid
            npc.npc_name = spec.get('name', nid.title())
            npc.kind = nid if nid in ('lila', 'rosa', 'yara') else 'talk'
            base_line = spec.get('greet') or (spec.get('lines') or ['...'])[0]
            extras = {
                'rita': "Pumps're open. Don't block the apron — and watch the hwy asphalt.",
                'neighbor': "Sanctuary's quiet if you keep the music down after nine.",
                'lot_attendant': "Stalls fill fast. Empty cars get chalked.",
                'barista': "Oat milk's out. Neon's free.",
                'pharmacist': "Heat rash aisle's picked clean. Hydrate.",
                'motel_clerk': "Rooms by the hour. Don't ask about the lake smell.",
                'amanda_friend': "Michelle's at Sanctuary — first name only, yeah?",
                'tavi': "Club 27 after dark. Cover's twenty.",
                'rook': "Gage takes gold. I take gossip.",
                'lila': "Cool Down if you're spinning. I'm not Mira's understudy.",
                'rosa': "Lot lights flatter nobody. Still cute though.",
                'yara': "Waterfront's prettier when the gators nap.",
            }
            npc.line = extras.get(nid) or base_line
            npc.talkable = True
            npc.portrait_tex = None
            try:
                rel = portrait_asset_path(nid)
            except Exception:
                rel = None
            if rel:
                try:
                    from ursina import load_texture
                    tex = load_texture(rel)
                    npc.portrait_tex = tex
                    bill = Entity(
                        parent=npc,
                        model='quad',
                        texture=tex,
                        scale=(1.05, 1.4),
                        position=(0, 1.45, -0.55),
                        double_sided=True,
                    )
                    try:
                        bill.billboard = True
                    except Exception:
                        pass
                except Exception:
                    npc.portrait_tex = None
            self.npcs.append(npc)
            self.talk_npcs.append({
                'ent': npc,
                'name': npc.npc_name,
                'talk': npc.line,
                'killable': False,
            })

    def _humanoid(self, x, z, shirt, pants, skin=None, hitbox=False, detail='crowd', style=None, outfit=None):
        ent = make_humanoid(
            self.Entity, self.color, x, z, shirt, pants,
            skin=skin, hitbox=hitbox, detail=detail, style=style, outfit=outfit,
        )
        try:
            base = (style or '')
            if base.endswith('_nude') or base.endswith('_underwear'):
                base = base.rsplit('_', 1)[0]
            ent._base_style = base or style
            fem = base in ('michelle', 'anime_f') or detail in ('anime_f',) or (
                detail == 'named' and base not in ('player', 'male', None, '') and style != 'male'
            )
            # Only mark clearly feminine styles; named males stay False
            if base in ('michelle', 'anime_f') or detail == 'anime_f':
                ent._feminine_adult = True
            elif style == 'michelle' or style == 'anime_f':
                ent._feminine_adult = True
        except Exception:
            pass
        return ent

    def _build_cars(self):
        paints = [
            self.color.rgb32(200, 30, 40),
            self.color.rgb32(20, 20, 24),
            self.color.rgb32(230, 230, 235),
            self.color.rgb32(30, 170, 190),
            self.color.rgb32(240, 190, 40),
            self.color.rgb32(120, 40, 180),
            self.color.rgb32(230, 90, 20),
            self.color.rgb32(40, 90, 160),
        ]
        spots = [
            (-8.0, -12.5, 90),
            (2.0, -12.4, 92),
            (14.0, -19.5, 0),
            (22.0, -12.8, 90),
        ]
        for i, (x, z, yaw) in enumerate(spots[:4]):
            car = self._make_car((x, 0, z), yaw, paints[i % len(paints)])
            car.parked = True
            car.traffic = False
            car.fuel = float(random.uniform(35, 70))
            car.damage = 0.0
            car.disabled = False
            self.cars.append(car)
        self.parked_count = len(self.cars)

    def _make_car(self, pos, yaw, paint):
        car = make_car(self.Entity, self.color, pos, yaw, paint)
        if not hasattr(car, 'tire_wear'):
            car.tire_wear = 0.0
        if not hasattr(car, 'damage'):
            car.damage = 0.0
        if not hasattr(car, 'disabled'):
            car.disabled = False
        car.impact_cd = 0.0
        # Traffic cars ignore fuel; parked/enterable get a tank below in _build_cars.
        if not getattr(car, 'traffic', False):
            if not hasattr(car, 'fuel') or car.fuel is None:
                car.fuel = float(random.uniform(35, 70))
        return car

    def _build_crowd(self):
        try:
            spawn_crowd(self)
        except Exception as exc:
            print('  spawn_crowd FAILED:', exc)
            if not getattr(self, 'peds', None):
                self.peds = []
        # Ensure list exists even if spawn partially failed
        if not hasattr(self, 'peds') or self.peds is None:
            self.peds = []
        hx, hz = -32.0, 12.0
        for ped in self.peds:
            if not ped:
                continue
            if abs(getattr(ped, 'x', 0) - hx) < 14 and abs(getattr(ped, 'z', 0) - hz) < 10:
                ped.x = min(46, ped.x + 18)

    def _build_traffic(self):
        spawn_traffic(self)

    def _rebuild_ignore(self):
        ign = [self.player, self.visual, self.cam_pivot]
        if self.gun_model:
            ign.append(self.gun_model)
        for npc in self.npcs:
            if npc:
                ign.append(npc)
        for car in self.cars:
            if not car:
                continue
            ign.append(car)
            body = getattr(car, 'body', None)
            if body:
                ign.append(body)
        self.ignore = ign

    def _build_targets(self):
        color = self.color
        # Six shootable hostiles from mobs.json, south of Hwy 50 (z < -16).
        mix = ('dusk_walker', 'road_thug', 'cinder_hound', 'dusk_walker', 'road_thug', 'cinder_hound')
        spots = [(-12, -32), (2, -34), (14, -31), (22, -36), (-22, -30), (6, -40)]
        for i, (mid, (x, z)) in enumerate(zip(mix, spots)):
            spec = (self.mobs_data or {}).get(mid) or {'id': mid, 'name': mid, 'hp': 30, 'xp': 10, 'color': '#6d6875'}
            shirt = hex_color(spec.get('color') or '#6d6875')
            skin = color.rgb32(170, 190, 150) if 'walker' in mid else color.rgb32(220, 160, 120)
            t = self._humanoid(x, z, shirt=shirt, pants=color.rgb32(24, 24, 28), skin=skin, hitbox=True)
            t.npc_id = f"{mid}_{i}"
            t.mob_id = mid
            t.npc_name = spec.get('name', mid)
            t.kind = 'mob'
            t.hp = int(spec.get('hp', 30))
            t.max_hp = t.hp
            t.xp = int(spec.get('xp', 10))
            t.heading = random.uniform(0, 360)
            t.wander_t = random.uniform(0, 2)
            t.hittable = True
            try:
                sz = float(spec.get('size') or 1.0)
                t.scale = sz
            except Exception:
                pass
            self.targets.append(t)
            self.npcs.append(t)
        # barrels
        Entity = self.Entity
        for x, z in ((12, -8), (11.2, -8.6), (-6, -22)):
            b = Entity(model='cube', color=color.rgb32(150, 70, 30), scale=(0.7, 1.0, 0.7), position=(x, 0.5, z), collider='box')
            b.kind = 'barrel'
            b.hittable = True
            b.hp = 15
            b.xp = 0
            b.npc_name = 'barrel'
            self.targets.append(b)

    def _build_player(self):
        Entity = self.Entity
        color = self.color
        camera = self.camera
        Vec3 = self.Vec3

        self.player = Entity(position=(-18.0, 0, 12.0), rotation_y=-90)
        self.visual = Entity(parent=self.player)
        # Alec — casual cyan tee / dark jeans (procedural multi-part)
        attach_humanoid_parts(
            Entity, color, self.visual,
            shirt=color.rgb32(40, 190, 200),
            pants=color.rgb32(30, 40, 55),
            skin=color.rgb32(255, 210, 175),
            detail='named',
            style='player',
        )
        self.gun_model = Entity(
            parent=self.visual,
            model='cube',
            color=color.rgb32(40, 42, 48),
            scale=(0.08, 0.16, 0.42),
            position=(0.38, 1.05, 0.28),
            enabled=False,
        )
        try:
            self.gun_model.keep_on_outfit_swap = True
        except Exception:
            pass
        Entity(parent=self.gun_model, model='cube', color=color.rgb32(30, 30, 32), scale=(0.7, 0.45, 0.35), position=(0, -0.4, -0.15))

        self.cam_pivot = Entity(parent=self.player, y=1.35)
        camera.parent = self.cam_pivot
        camera.position = Vec3(0, 1.65, -8.8)
        camera.rotation = Vec3(12, 0, 0)
        camera.fov = 80
        try:
            flags = self._load_flags()
            cm = str(flags.get('cam_mode') or getattr(self, 'cam_mode', 'follow') or 'follow').strip().lower()
            if cm in ('follow', 'near', 'far', 'hood'):
                self.cam_mode = cm
        except Exception:
            pass
        try:
            self._apply_camera_mode()
        except Exception:
            pass

    def _build_hud(self):
        Entity = self.Entity
        Text = self.Text
        color = self.color
        camera = self.camera

        Text(text='RUNE MOMMY', position=(-0.86, 0.48), origin=(-0.5, 0.5), color=color.rgb32(255, 90, 210))
        Text(text='Clermont / Hwy 50', position=(-0.86, 0.445), origin=(-0.5, 0.5), color=color.rgb32(140, 230, 255), scale=0.75)
        self.hud_gold = Text(text='Gold  200', position=(-0.86, 0.40), origin=(-0.5, 0.5), color=color.rgb32(255, 220, 90))
        self.hud_hp = Text(text='HP  100', position=(-0.86, 0.370), origin=(-0.5, 0.5), color=color.rgb32(255, 120, 170), scale=0.85)
        self.hud_heat = Text(text='HEAT  0.0', position=(-0.86, 0.340), origin=(-0.5, 0.5), color=color.rgb32(255, 90, 90), scale=0.85)
        self.hud_ammo = Text(text='Pistol  --', position=(-0.86, 0.310), origin=(-0.5, 0.5), color=color.rgb32(200, 200, 210), scale=0.85)
        self.hud_pack = Text(text='Pack  0', position=(-0.86, 0.280), origin=(-0.5, 0.5), color=color.rgb32(180, 230, 200), scale=0.85)
        self.hud_breed = Text(text='BREED  0%', position=(-0.86, 0.250), origin=(-0.5, 0.5), color=color.rgb32(46, 196, 182), scale=0.85)
        self.hud_quest = Text(text='QUEST  —', position=(-0.86, 0.220), origin=(-0.5, 0.5), color=color.rgb32(180, 255, 200), scale=0.8)
        self.hud_mode = Text(text='WALK', position=(-0.86, 0.190), origin=(-0.5, 0.5), color=color.rgb32(200, 220, 255), scale=0.8)
        self.hud_prompt = Text(text='', position=(0, -0.42), origin=(0, 0), color=color.rgb32(255, 240, 180), scale=0.9)
        self.hud_toast = Text(text='', position=(0, 0.32), origin=(0, 0), color=color.rgb32(255, 180, 220), scale=0.85)
        self.crosshair = Entity(parent=camera.ui, model='quad', color=color.rgb32(255, 255, 255), scale=0.008, rotation_z=45)
        self.debug_hud = Text(
            text='',
            position=(-0.86, -0.36),
            origin=(-0.5, 0.5),
            color=color.rgb32(180, 255, 180),
            scale=0.65,
            enabled=True,
        )

        self.panel_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba32(10, 4, 18, 235),
            scale=(1.58, 0.78),
            position=(0.06, -0.28),
            enabled=False,
            z=0.1,
        )
        self.panel_portrait = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.34, 0.60),
            position=(-0.68, -0.26),
            enabled=False,
            z=-0.05,
        )
        if self.mira_texture:
            self.panel_portrait.texture = self.mira_texture
        self.panel_name = Text(text='', position=(-0.52, -0.02), origin=(-0.5, 0.5), color=color.rgb32(255, 120, 210), enabled=False)
        self.panel_body = Text(text='', position=(-0.52, -0.07), origin=(-0.5, 0.5), color=color.rgb32(245, 230, 255), enabled=False, scale=0.75)
        # Clickable dialogue choice buttons (mouse) + number keys 1-8
        from ursina import Button
        self.panel_choices = []
        for i in range(8):
            btn = Button(
                text='',
                scale=(0.78, 0.036),
                position=(0.08, -0.22 - i * 0.042),
                origin=(0, 0),
                color=color.rgba32(30, 12, 48, 230),
                highlight_color=color.rgba32(255, 70, 170, 230),
                pressed_color=color.rgba32(180, 40, 120, 240),
                text_color=color.rgb32(180, 235, 255),
                parent=camera.ui,
                enabled=False,
                z=-0.02,
            )
            try:
                btn.text_entity.scale = 0.55
            except Exception:
                pass
            btn._choice_index = i
            self.panel_choices.append(btn)
        Text(
            text='WASD walk   mouse look   E use   1-8 choices   LMB shoot   ESC quit',
            position=(-0.86, -0.48),
            origin=(-0.5, 0.5),
            color=color.rgb32(160, 140, 180),
            scale=0.65,
        )

    # ----- tick -----------------------------------------------------------

    def tick(self):
        from ursina import time, held_keys, mouse, raycast, Vec3, destroy, color
        dt = min(time.dt, 0.05)
        self.shoot_cd = max(0.0, self.shoot_cd - dt)
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0 and self.hud_toast:
                self.hud_toast.text = ''

        mode = getattr(self, 'mode', 'play')
        if mode in ('menu', 'settings'):
            # title / settings — no world sim, no walk
            if getattr(self, 'debug_on', True):
                try:
                    self._debug_tick(dt)
                except Exception:
                    pass
            return

        self.panic_t = max(0.0, getattr(self, 'panic_t', 0.0) - dt)
        self._wander_targets(dt)

        if mode == 'play':
            tick_crowd(self, dt)
            try:
                life_sim.tick(self, dt)
            except Exception:
                pass
            try:
                tokyo.tick(self, dt)
            except Exception:
                pass
            # Named NPCs are not in peds[] — keep them un-buried / visible near player
            try:
                self._tick_named_visibility()
            except Exception:
                pass
            try:
                wildlife.tick_gators(self, dt)
            except Exception:
                pass
            tick_traffic(self, dt)
            try:
                if crash is not None:
                    crash.tick_fx(self, dt)
            except Exception:
                pass
            try:
                if world_chunks is not None:
                    world_chunks.tick(self, dt)
            except Exception:
                pass
            self._tick_heat(dt)
            self._tick_tutorial(dt)
        # safe: skip crowd/traffic/heat; walk only

        if self.ui_open:
            self._refresh_hud()
            return

        if mode == 'play' and self.in_car:
            self._drive(dt)
        else:
            self._walk(dt)
            try:
                wildlife.apply_player_water(self)
            except Exception:
                pass

        if mode == 'play':
            self._maybe_auto_michelle()
            self._tick_visit_quests()
            if self.pistol_drawn and self.owned_pistol and held_keys['left mouse'] and self.shoot_cd <= 0:
                self._shoot()

        try:
            radar.tick(self, dt)
        except Exception:
            pass


        # Adult jiggle — damped spring; Michelle + nearby feminine; skip culled/LOD mid-far
        try:
            moving = bool(getattr(self, '_was_moving', False))
            vis = getattr(self, 'visual', None) or self.player
            if vis is not None:
                _tick_jiggle(vis, dt, moving=moving)
            px = float(self.player.x); pz = float(self.player.z)
            near_r2 = 22.0 * 22.0
            cands = []
            m = getattr(self, 'michelle', None)
            if m is not None:
                cands.append(m)
            for n in list(getattr(self, 'npcs', None) or []):
                if n is not None and n is not m and getattr(n, 'jiggle_parts', None):
                    cands.append(n)
            for n in list(getattr(self, 'crowd', None) or [])[:24]:
                if n is not None and getattr(n, '_feminine_adult', False) and getattr(n, 'jiggle_parts', None):
                    cands.append(n)
            seen = set()
            for n in cands:
                i = id(n)
                if i in seen:
                    continue
                seen.add(i)
                if getattr(n, 'visible', True) is False or getattr(n, 'enabled', True) is False:
                    continue
                try:
                    dx = float(n.x) - px; dz = float(n.z) - pz
                    if dx * dx + dz * dz > near_r2:
                        continue
                except Exception:
                    continue
                last = getattr(n, '_jiggle_last_xz', None)
                try:
                    nx, nz = float(n.x), float(n.z)
                except Exception:
                    continue
                n_moving = False
                if last is not None:
                    n_moving = (nx - last[0]) ** 2 + (nz - last[1]) ** 2 > 1e-6
                n._jiggle_last_xz = (nx, nz)
                _tick_jiggle(n, dt, moving=n_moving)
        except Exception:
            pass

        self._refresh_hud()
        if getattr(self, 'debug_on', True):
            try:
                self._debug_tick(dt)
            except Exception as exc:
                print('[Rune Mommy][DBGERR]', exc)

    def _walk(self, dt):
        from ursina import held_keys, mouse, raycast, Vec3
        player = self.player
        mode = getattr(self, 'mode', 'play')

        # Free look always (locked OR unlocked OR right-mouse). Never soft-lock rotation.
        sens = float(getattr(self, 'mouse_sens', 140) or 140)
        player.rotation_y += mouse.velocity[0] * sens
        self.cam_pivot.rotation_x -= mouse.velocity[1] * sens
        self.cam_pivot.rotation_x = max(-35, min(40, self.cam_pivot.rotation_x))
        # Q/E and arrows turn even if mouse is dead
        if held_keys['q'] or held_keys['left arrow']:
            player.rotation_y += 90 * dt
        if held_keys['e'] and mode == 'safe':
            # E is gate in safe — only turn with E if not near gate; use right arrow instead
            pass
        if held_keys['right arrow']:
            player.rotation_y -= 90 * dt


        wish_x = held_keys['d'] - held_keys['a']
        wish_z = held_keys['w'] - held_keys['s']
        # Arrow keys as backup movement
        wish_x += held_keys['right arrow'] * 0  # right arrow is turn
        wish_z += 0
        if held_keys['up arrow']:
            wish_z += 1
        if held_keys['down arrow']:
            wish_z -= 1
        wish = Vec3(wish_x, 0, wish_z)
        self._was_moving = bool(wish.length() > 0)
        if wish.length() > 0:
            wish = wish.normalized()
            speed = 10.0 if mode == 'safe' else 8.5
            move = (player.forward * wish.z + player.right * wish.x) * speed * dt
            if mode == 'safe':
                # Nuclear: no clip tests in the yard — just move and clamp.
                player.position += move
                cx, _cy, cz = getattr(self, 'safe_yard_center', (80.0, 0.0, 80.0))
                player.x = max(cx - 12.0, min(cx + 12.0, player.x))
                player.z = max(cz - 12.0, min(cz + 12.0, player.z))
            else:
                origin = player.world_position + Vec3(0, 0.9, 0)
                ign = list(self.ignore)
                hit = raycast(origin, move.normalized(), distance=0.55 + move.length(), ignore=ign, debug=False)
                if not hit.hit:
                    player.position += move
                else:
                    mx = Vec3(move.x, 0, 0)
                    mz = Vec3(0, 0, move.z)
                    if mx.length() > 1e-5:
                        hx = raycast(origin, mx.normalized(), distance=0.55 + mx.length(), ignore=ign, debug=False)
                        if not hx.hit:
                            player.x += mx.x
                    if mz.length() > 1e-5:
                        hz = raycast(origin, mz.normalized(), distance=0.55 + mz.length(), ignore=ign, debug=False)
                        if not hz.hit:
                            player.z += mz.z
                player.x = max(-60, min(78, player.x))
                player.z = max(-58, min(30, player.z))

        self.y_vel -= 32 * dt
        player.y += self.y_vel * dt
        if player.y <= 0:
            player.y = 0
            self.y_vel = 0
            self.grounded = True
        else:
            self.grounded = False

        if held_keys['space'] and self.grounded:
            self.y_vel = 8.2
            self.grounded = False

        if not self.visual.enabled:
            self.visual.enabled = True
        if self.cam_in_car:
            self._set_camera_follow(False)


    def _drive(self, dt):
        from ursina import held_keys, mouse, raycast, Vec3
        car = self.in_car
        if getattr(mouse, 'locked', False):
            # Clamp mouse look while driving (pitch only on cam_pivot)
            car.cam_pivot.rotation_x -= mouse.velocity[1] * (float(getattr(self, "mouse_sens", 140) or 140) * 0.57)
            car.cam_pivot.rotation_x = max(-20, min(25, car.cam_pivot.rotation_x))

        dmg = float(getattr(car, 'damage', 0.0) or 0.0)
        dmg_mul = max(0.18, 1.0 - 0.55 * (dmg / 100.0))
        wear = float(getattr(car, 'tire_wear', 0.0) or 0.0)
        wear_n = max(0.0, min(1.0, wear / 100.0))
        steer_gain = 1.18 * (1.0 - 0.55 * wear_n)
        coast_drag = 2.8 + 2.6 * wear_n
        accel_drag = 0.42 + 0.85 * wear_n
        # Feel: snappier accel / higher top end; damage & tires still bite
        base_vmax, base_accel = 26.0, 20.0
        vmax = base_vmax * dmg_mul * (1.0 - 0.18 * wear_n)
        accel_force = base_accel * dmg_mul * (1.0 - 0.12 * wear_n)
        brake_force = 0.0
        accel = 0.0
        handbrake = 0.0

        fuel = float(getattr(car, 'fuel', 100.0) or 0.0)
        out_of_gas = fuel <= 0.0 or getattr(car, 'disabled', False)

        if out_of_gas:
            brake_force = 16.0
            if not getattr(car, 'out_of_gas_toasted', False) and fuel <= 0.0 and not getattr(car, 'disabled', False):
                car.out_of_gas_toasted = True
                self.toast('Out of gas. Find a pump.')
        else:
            if held_keys['w']:
                accel = accel_force
            elif held_keys['s']:
                if car.speed > 0.55:
                    brake_force = 38.0
                else:
                    accel = -accel_force * 0.58
            if held_keys['space']:
                brake_force = max(brake_force, 58.0)
                handbrake = 1.0

        steer = float(held_keys['a'] - held_keys['d'])
        nx, nz, nyaw, nspd = _bicycle_step_safe(
            car.x, car.z, car.rotation_y, car.speed,
            steer, accel, dt,
            vmax=vmax, wheelbase=2.6, drag=2.2 + 1.4 * wear_n,
            steer_gain=steer_gain, brake_force=brake_force,
            coast_drag=coast_drag, accel_drag=accel_drag,
            handbrake=handbrake,
        )
        # Tire wear: speed / hard turns / off-road (lots & grass harsher than hwy asphalt)
        try:
            from crowd import is_on_road
            on_hwy = is_on_road(nx, nz)
        except Exception:
            on_hwy = True
        spd = abs(float(nspd))
        hard = abs(steer) > 0.55 and spd > 6.0
        rate = 0.32 * (spd / 26.0) ** 1.4
        if hard:
            rate += 1.05 * abs(steer) * (spd / 18.0)
        if not on_hwy:
            rate += 1.55 * (spd / 16.0)
        if brake_force >= 40 and spd > 8:
            rate += 0.85
        if handbrake > 0.0 and spd > 5:
            rate += 1.1 * abs(steer)
        car.tire_wear = min(100.0, wear + rate * dt)
        if car.tire_wear >= 85.0 and not getattr(car, 'tire_warn_hi', False):
            car.tire_warn_hi = True
            self.toast('Tires shredded — grip gone. Find Hwy 50 Tire & Lube.')
        elif car.tire_wear >= 55.0 and not getattr(car, 'tire_warn_mid', False):
            car.tire_warn_mid = True
            self.toast('Tire wear high. Handling soft — visit Rico.')

        # Fuel burn ~ full tank lasts a few minutes of continuous drive
        if not getattr(car, 'traffic', False) and not out_of_gas:
            burn = (0.028 * abs(nspd) + 0.045 * max(0.0, accel)) * dt
            fuel = max(0.0, fuel - burn)
            car.fuel = fuel
            if fuel <= 0.0 and not getattr(car, 'out_of_gas_toasted', False):
                car.out_of_gas_toasted = True
                self.toast('Out of gas. Find a pump.')

        # Collision: buildings via raycast; traffic / parked via proximity
        proposed = Vec3(nx - car.x, 0, nz - car.z)
        hit_world = False
        hit_other = None
        impact_speed = abs(nspd)
        if proposed.length() > 0.001:
            origin = car.world_position + Vec3(0, 0.7, 0)
            ign = [self.player, self.visual, self.cam_pivot, car, getattr(car, 'body', None)]
            if self.gun_model:
                ign.append(self.gun_model)
            for npc in self.npcs:
                if not npc:
                    continue
                kind = getattr(npc, 'kind', '')
                named = getattr(npc, 'npc_id', '')
                if kind in ('mira', 'michelle', 'gun', 'talk', 'lila', 'rosa', 'yara') or named in (
                    'mira', 'michelle', 'gage', 'lila', 'rosa', 'yara', 'rita', 'deb',
                    'motel_clerk', 'barista', 'pharmacist', 'neighbor', 'lot_attendant',
                    'amanda_friend', 'club27_host', 'quiet_spa_tech', 'citrus_guide', 'park_ranger',
                ):
                    ign.append(npc)
            # Ignore other car bodies for ray — proximity handles car-vs-car
            for other in self.cars:
                if other and other is not car:
                    ign.append(other)
                    body = getattr(other, 'body', None)
                    if body:
                        ign.append(body)
            ign = [e for e in ign if e]
            direction = proposed.normalized()
            hit = raycast(origin, direction, distance=max(2.0, proposed.length() + 1.2), ignore=ign, debug=False)
            if hit.hit:
                hit_world = True

        if not hit_world:
            best_d = 2.55
            for other in self.cars:
                if not other or other is car:
                    continue
                d = dist_xz((nx, 0, nz), (other.x, 0, other.z))
                if d < best_d:
                    best_d = d
                    hit_other = other

        if hit_world or hit_other is not None:
            if crash is not None:
                nx, nz, nyaw, nspd = crash.resolve_player_hit(
                    self, car,
                    hit_world=hit_world,
                    hit_other=hit_other,
                    impact_speed=impact_speed,
                    nx=nx, nz=nz, nspd=nspd, nyaw=nyaw,
                )
            else:
                self._car_take_damage(car, impact_speed)
                nspd *= -0.25
                nx, nz = car.x, car.z
            car.x, car.z = nx, nz
            car.rotation_y = nyaw
        else:
            car.x, car.z = nx, nz
            car.rotation_y = nyaw

        car.speed = nspd
        car.y = 0
        car.x = max(-48, min(52, car.x))
        car.z = max(-52, min(22, car.z))

        self._update_car_damage_visual(car, dt)

        # Engine loop (soft)
        try:
            if sfx is not None:
                sfx.engine_update(car, dt)
        except Exception:
            pass

        # Slight camera follow lag (lerp cam_pivot local z toward target)
        try:
            if str(getattr(self, 'cam_mode', 'follow') or 'follow') != 'hood':
                target_z = -0.15 if abs(car.speed) > 8 else 0.2
                cur = float(getattr(car.cam_pivot, 'z', 0.2) or 0.2)
                car.cam_pivot.z = cur + (target_z - cur) * min(1.0, 3.5 * dt)
        except Exception:
            pass

        self.player.position = car.position
        self.player.y = 0
        self.player.rotation_y = car.rotation_y
        if self.visual.enabled:
            self.visual.enabled = False
        if not self.cam_in_car:
            self._set_camera_follow(True)

    def _car_take_damage(self, car, impact_speed):
        if crash is not None:
            crash.take_damage(self, car, impact_speed, source='world')
            return
        if getattr(car, 'traffic', False) and self.in_car is not car:
            return
        add = min(42.0, max(3.0, abs(float(impact_speed)) * 2.4))
        car.damage = min(100.0, float(getattr(car, 'damage', 0.0) or 0.0) + add)
        if car.damage >= 100.0 and not getattr(car, 'disabled', False):
            car.disabled = True
            car.speed = 0.0
            self.toast('Car totaled.')

    def _update_car_damage_visual(self, car, dt=0.016):
        if crash is not None:
            crash.update_damage_visual(self, car, dt)
            return
        dmg = float(getattr(car, 'damage', 0.0) or 0.0)
        base = getattr(car, 'base_paint', None) or getattr(car, 'paint', None)
        if base is not None and getattr(car, 'body', None):
            t = min(1.0, dmg / 100.0)
            try:
                if hasattr(base, 'r'):
                    r = int(base.r * 255 * (1 - 0.55 * t) + 180 * t)
                    g = int(base.g * 255 * (1 - 0.75 * t) + 30 * t)
                    b = int(base.b * 255 * (1 - 0.75 * t) + 25 * t)
                    col = self.color.rgb32(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
                else:
                    col = base.tint(-0.55 * t) if hasattr(base, 'tint') else base
                car.body.color = col
            except Exception:
                pass

    def _set_camera_follow(self, in_car):
        self.cam_in_car = bool(in_car)
        self._apply_camera_mode()

    def _camera_mode_list(self):
        # On foot: follow / near / far. In car: + hood-cam.
        if self.in_car or getattr(self, 'cam_in_car', False):
            return ('follow', 'near', 'far', 'hood')
        return ('follow', 'near', 'far')

    def _camera_mode_label(self, mode=None):
        mode = mode or getattr(self, 'cam_mode', 'follow')
        return {
            'follow': 'Camera: Follow',
            'near': 'Camera: Near / Shoulder',
            'far': 'Camera: Far / Chase',
            'hood': 'Camera: Hood',
        }.get(mode, 'Camera: Follow')

    def _persist_cam_pref(self):
        # Light persist -- flags only (survives without full Save).
        try:
            flags = self._load_flags()
            flags['cam_mode'] = str(getattr(self, 'cam_mode', 'follow') or 'follow')
            self._save_flags(flags)
        except Exception:
            pass

    def _cycle_camera_mode(self, delta=1):
        mode = getattr(self, 'mode', 'play')
        if mode not in ('play', 'safe'):
            return
        if getattr(self, 'ui_open', False):
            return
        modes = self._camera_mode_list()
        cur = str(getattr(self, 'cam_mode', 'follow') or 'follow').lower()
        if cur not in modes:
            cur = 'follow'
        i = modes.index(cur)
        self.cam_mode = modes[(i + int(delta)) % len(modes)]
        self._apply_camera_mode()
        self.toast(self._camera_mode_label(self.cam_mode))
        self._persist_cam_pref()

    def _apply_camera_mode(self):
        from ursina import Vec3, camera
        mode = str(getattr(self, 'cam_mode', 'follow') or 'follow').lower()
        in_car = bool(getattr(self, 'cam_in_car', False) and self.in_car)
        if not in_car and mode == 'hood':
            mode = 'follow'
            self.cam_mode = mode
        # tuple: y, z, pitch, x_off, fov
        if in_car:
            table = {
                'follow': (2.4, -10.5, 14.0, 0.0, 80.0),
                'near': (1.55, -4.2, 10.0, 0.55, 78.0),
                'far': (5.2, -16.5, 26.0, 0.0, 82.0),
                'hood': (1.05, 1.85, 8.0, 0.0, 75.0),
            }
            parent = self.in_car.cam_pivot
        else:
            table = {
                'follow': (1.65, -8.8, 12.0, 0.0, 80.0),
                'near': (1.35, -3.4, 8.0, 0.62, 78.0),
                'far': (4.2, -15.0, 24.0, 0.0, 82.0),
                'hood': (1.65, -8.8, 12.0, 0.0, 80.0),
            }
            parent = self.cam_pivot
        y, z, pitch, x_off, fov = table.get(mode, table['follow'])
        if parent is None:
            return
        camera.parent = parent
        camera.position = Vec3(x_off, y, z)
        camera.rotation = Vec3(pitch, 0, 0)
        try:
            camera.fov = fov
        except Exception:
            pass

    def _cycle_outfit(self, delta=1):
        """Adult feminine NPCs / Michelle / player: clothed -> underwear -> nude."""
        from models3d._actors import cycle_humanoid_outfit
        if getattr(self, 'mode', 'play') not in ('play', 'safe'):
            return
        if getattr(self, 'ui_open', False):
            return
        Entity = self.Entity
        color = self.color
        target = None
        # Prefer Michelle if near, else nearest feminine adult NPC, else player visual
        try:
            px, pz = self.player.x, self.player.z
        except Exception:
            return
        best_d = 3.2
        m = getattr(self, 'michelle', None)
        if m is not None:
            try:
                d = ((m.x - px) ** 2 + (m.z - pz) ** 2) ** 0.5
                if d <= best_d:
                    target, best_d = m, d
            except Exception:
                pass
        for npc in list(getattr(self, 'npcs', []) or []):
            if npc is None or npc is m:
                continue
            if not (getattr(npc, '_feminine_adult', False) or getattr(npc, 'feminine', False)
                    or str(getattr(npc, '_base_style', '') or getattr(npc, 'humanoid_style', '') or '').startswith(('michelle', 'anime_f'))
                    or getattr(npc, 'kind', '') in ('michelle', 'mira', 'lila', 'rosa', 'yara')):
                continue
            try:
                d = ((npc.x - px) ** 2 + (npc.z - pz) ** 2) ** 0.5
            except Exception:
                continue
            if d < best_d:
                target, best_d = npc, d
        if target is None:
            target = getattr(self, 'visual', None)
            if target is None:
                return
            # player undress allowed (adult)
            try:
                target._feminine_adult = True
                if not getattr(target, '_base_style', None):
                    target._base_style = 'player'
            except Exception:
                pass
        try:
            nxt = cycle_humanoid_outfit(Entity, color, target, delta=delta)
        except Exception as exc:
            print('  outfit cycle skip:', exc)
            return
        label = {'clothed': 'Outfit: Clothed', 'underwear': 'Outfit: Underwear', 'nude': 'Outfit: Nude'}.get(nxt, 'Outfit')
        who = getattr(target, 'npc_name', None) or ('Michelle' if target is m else 'You')
        # Never print a surname / deadname
        if isinstance(who, str) and who.lower().startswith('lewis'):
            who = 'Michelle'
        self.toast('%s — %s' % (who, label))


    def _wander_targets(self, dt):
        from ursina import Vec3, raycast
        for t in self.targets:
            if getattr(t, 'kind', '') not in ('target', 'mob'):
                continue
            if not t or getattr(t, 'hp', 0) <= 0:
                continue
            t.wander_t += dt
            if t.wander_t > 2.8:
                t.heading = random.uniform(0, 360)
                t.wander_t = 0
            t.rotation_y = t.heading
            step = t.forward * 1.15 * dt
            t.position += step
            t.y = 0
            t.x = max(-40, min(40, t.x))
            t.z = max(-40, min(8, t.z))

    def _shoot(self):
        from ursina import camera, raycast, Vec3, Entity, color, destroy, mouse
        if not self.owned_pistol or not self.pistol_drawn:
            return
        if self.shoot_cd > 0:
            return
        if self.ammo <= 0:
            self.toast('Empty. Buy ammo at Hancock Gun Hut.')
            self.shoot_cd = 0.35
            return
        self.ammo -= 1
        self.shoot_cd = 0.22
        self.panic_t = max(self.panic_t, 4.5)
        origin = camera.world_position
        direction = camera.forward
        ign = list(self.ignore)
        if self.in_car:
            ign += [self.in_car, self.in_car.body]
        hit = raycast(origin, direction, distance=48, ignore=ign, debug=False)
        end = hit.world_point if hit.hit else origin + direction * 48
        mid = origin + (end - origin) * 0.5
        length = max(0.2, (end - origin).length())
        tracer = Entity(model='cube', color=color.rgb32(255, 230, 80), scale=(0.04, 0.04, min(length, 18)), position=mid, collider=None)
        try:
            tracer.look_at(end)
        except Exception:
            pass
        destroy(tracer, delay=0.07)
        flash = Entity(model='sphere', color=color.rgb32(255, 240, 180), scale=0.18, position=origin + direction * 1.2)
        destroy(flash, delay=0.05)
        if hit.hit and hit.entity:
            ent = hit.entity
            # walk up to a tagged parent
            cur = ent
            tagged = None
            for _ in range(6):
                if cur is None:
                    break
                if getattr(cur, 'hittable', False):
                    tagged = cur
                    break
                cur = getattr(cur, 'parent', None)
            if tagged is None:
                # maybe we hit a child of a target
                for t in list(self.targets):
                    if not t:
                        continue
                    if ent == t or getattr(ent, 'parent', None) == t:
                        tagged = t
                        break
            if tagged is not None:
                kind = getattr(tagged, 'kind', '')
                named = getattr(tagged, 'npc_id', '')
                if kind in ('mira', 'michelle', 'gun', 'talk', 'lila', 'rosa', 'yara') or named in ('mira', 'michelle', 'gage', 'lila', 'rosa', 'yara', 'rita', 'deb', 'motel_clerk', 'barista', 'pharmacist', 'neighbor', 'lot_attendant', 'amanda_friend'):
                    self.toast('Not a target.')
                    return
                tagged.hp = getattr(tagged, 'hp', 10) - 18
                if kind in ('civilian', 'lot_rat', 'walker', 'thug', 'heat_hunter', 'mob'):
                    self.heat = min(3.0, self.heat + 0.4)
                try:
                    tagged.blink(color.red)
                except Exception:
                    pass
                if tagged.hp <= 0:
                    name = getattr(tagged, 'npc_name', 'target')
                    loot = 12 if name != 'barrel' else 4
                    xp = int(getattr(tagged, 'xp', 0) or 0)
                    self.gold += loot
                    tagged.hittable = False
                    try:
                        tagged.enabled = False
                    except Exception:
                        try:
                            tagged.visible = False
                        except Exception:
                            pass
                    extra = f' +{xp}xp' if xp else ''
                    self.toast(f'{name} down. +{loot}g{extra}')
                    if kind == 'gator' or getattr(tagged, 'npc_name', '') == 'alligator':
                        try:
                            wildlife.on_gator_killed(self, tagged)
                        except Exception:
                            pass
                    self._quest_event('kill', kind=kind, mob_id=getattr(tagged, 'mob_id', ''))

    def _refresh_hud(self):
        if self.hud_gold:
            self.hud_gold.text = f'Gold  {self.gold}'
        if self.hud_hp:
            self.hud_hp.text = f'HP  {int(self.hp)}'
        if self.hud_heat:
            self.hud_heat.text = f'HEAT  {self.heat:.1f}'
        if getattr(self, 'hud_breed', None):
            flag = '  PREG' if self.preg else ''
            self.hud_breed.text = f'Breed  {int(self.breed)}%{flag}'
        if self.hud_ammo:
            if not self.owned_pistol:
                self.hud_ammo.text = 'Pistol  not owned'
            elif self.pistol_drawn:
                self.hud_ammo.text = f'Pistol  DRAWN   ammo {self.ammo}'
            else:
                self.hud_ammo.text = f'Pistol  holstered   ammo {self.ammo}'
        if self.hud_pack:
            self.hud_pack.text = f'Pack  {len(self.pack)}'
        if getattr(self, 'hud_quest', None):
            self.hud_quest.text = self._quest_hud_line()
        if getattr(self, 'hud_mode', None):
            if self.in_car:
                fuel = int(getattr(self.in_car, 'fuel', 0) or 0)
                dmg = int(getattr(self.in_car, 'damage', 0) or 0)
                tw = int(getattr(self.in_car, 'tire_wear', 0) or 0)
                self.hud_mode.text = f'DRIVE   FUEL {fuel}%   DMG {dmg}%   TIRES {tw}%'
            else:
                self.hud_mode.text = 'WALK'
        if self.gun_model:
            self.gun_model.enabled = bool(self.pistol_drawn and self.owned_pistol and not self.in_car)
        if getattr(self, 'mode', 'play') in ('menu', 'settings'):
            if self.hud_prompt:
                self.hud_prompt.text = ''
            return
        if self.ui_open:
            if self.hud_prompt:
                self.hud_prompt.text = '1-8 choose / click    ESC close'
            return
        prompt = self._nearest_prompt()
        if self.hud_prompt:
            self.hud_prompt.text = prompt

    def _nearest_prompt(self):
        if getattr(self, 'mode', 'play') in ('menu', 'settings'):
            return ''
        pos = self._actor_pos()
        if getattr(self, 'mode', '') == 'safe' and getattr(self, 'safe_gate', None):
            g = self.safe_gate
            if dist_xz(pos, (g.x, 0, g.z)) < 3.5:
                return 'E  leave safe yard — start game'
        gas = self._nearest_gas(pos)
        if self.in_car:
            if gas:
                car = self.in_car
                fuel = float(getattr(car, 'fuel', 100) or 0)
                dmg = float(getattr(car, 'damage', 0) or 0)
                need = max(0.0, 100.0 - fuel)
                cost = max(1, int(math.ceil(need / 2.0))) if need > 0.5 else 0
                if need > 0.5:
                    return f'E  fill tank ({cost}g)'
                if dmg >= 5:
                    return 'E  repair (50g)'
                return 'E  exit car  ·  tank full'
            return 'E  exit car'
        car, cd = self._nearest_car(pos, 3.2)
        npc, nd = self._nearest_npc(pos, 3.0)
        stall, sd = self._nearest_stall(pos, 3.6)
        options = []
        try:
            ip = interiors.prompt(self, pos)
            if ip:
                options.append((0.05, ip))
        except Exception:
            pass
        try:
            tp = tokyo.prompt_line(self)
            if tp:
                options.append((0.02, tp))
        except Exception:
            pass
        if gas:
            near_car, _ncd = self._nearest_car(pos, 5.0)
            if near_car and not getattr(near_car, 'traffic', False):
                fuel = float(getattr(near_car, 'fuel', 100) or 0)
                need = max(0.0, 100.0 - fuel)
                cost = max(1, int(math.ceil(need / 2.0))) if need > 0.5 else 0
                dmg = float(getattr(near_car, 'damage', 0) or 0)
                if need > 0.5:
                    options.append((0.1, f'E  fill tank ({cost}g)'))
                elif dmg >= 5:
                    options.append((0.1, 'E  repair (50g)'))
                else:
                    options.append((0.15, 'E  gas station'))
            else:
                options.append((0.2, 'E  gas pump'))
        if car and not getattr(car, 'disabled', False):
            options.append((cd, f'E  enter car'))
        if npc:
            kind = getattr(npc, 'kind', '')
            if kind == 'mira':
                options.append((nd, 'E  talk to Mama Mira'))
            elif kind == 'michelle':
                options.append((nd, 'E  talk to Michelle'))
            elif kind == 'gun':
                options.append((nd, 'E  Hancock Gun Hut (Gage)'))
            elif kind not in ('target', 'mob'):
                options.append((nd, f'E  talk to {getattr(npc, "npc_name", "NPC")}'))
        if stall and (not npc or sd + 0.4 < nd):
            if stall['kind'] == 'gun':
                options.append((sd, 'E  Hancock Gun Hut'))
            else:
                options.append((sd, f'E  {stall["name"]}'))
        door_xz = (self.house_rooms or {}).get('door')
        if door_xz and not self.michelle_seen:
            dd = dist_xz(pos, (door_xz[0], 0, door_xz[1]))
            if dd < 3.0:
                options.append((dd, 'E  Sanctuary Drive'))
        for poi in getattr(self, 'pois', []) or []:
            if poi.get('is_gas'):
                continue
            pd = dist_xz(pos, poi['pos'])
            if pd < 3.4:
                options.append((pd, f"E  {poi.get('name', 'POI')}"))
        if not options:
            return ''
        options.sort(key=lambda x: x[0])
        return options[0][1]

    def _actor_pos(self):
        if self.in_car:
            p = self.in_car.world_position
            return (p.x, p.y, p.z)
        p = self.player.world_position
        return (p.x, p.y, p.z)

    def _nearest_car(self, pos, radius):
        best, best_d = None, radius
        for car in self.cars:
            if not car:
                continue
            if getattr(car, 'disabled', False):
                continue
            d = dist_xz(pos, (car.x, 0, car.z))
            if d < best_d:
                best, best_d = car, d
        return best, best_d

    def _nearest_gas(self, pos, radius=None):
        best, best_d = None, 99.0
        for poi in getattr(self, 'pois', []) or []:
            if not poi.get('is_gas'):
                continue
            r = float(radius if radius is not None else poi.get('pump_r', 4.2))
            d = dist_xz(pos, poi['pos'])
            if d < r and d < best_d:
                best, best_d = poi, d
        return best

    def _nearest_npc(self, pos, radius):
        best, best_d = None, radius
        for npc in self.npcs:
            if not npc:
                continue
            kind = getattr(npc, 'kind', '')
            talkable = bool(getattr(npc, 'talkable', False) or kind == 'talk')
            # Crowd combat kinds skipped unless marked talkable (life_sim subset / lines)
            if kind in ('target', 'mob', 'barrel'):
                continue
            if kind in ('civilian', 'lot_rat', 'walker', 'thug', 'heat_hunter') and not talkable:
                continue
            if getattr(npc, 'hittable', False) and not talkable:
                continue
            if getattr(npc, 'enabled', True) is False:
                continue
            if getattr(npc, 'driving', False):
                continue
            d = dist_xz(pos, (npc.x, 0, npc.z))
            if d < best_d:
                best, best_d = npc, d
        return best, best_d

    def _nearest_stall(self, pos, radius):
        best, best_d = None, radius
        for st in self.stalls:
            d = dist_xz(pos, st['pos'])
            if d < best_d:
                best, best_d = st, d
        return best, best_d

    # ----- input ----------------------------------------------------------

    def on_input(self, key):
        from ursina import application, mouse
        self._dbg_last_key = str(key)
        mode = getattr(self, 'mode', 'play')

        if mode in ('menu', 'settings'):
            if key == 'escape':
                if mode == 'settings':
                    self._show_menu()
                else:
                    application.quit()
                return
            if mode == 'menu':
                if key == '1':
                    self._enter_safe_zone(from_load=False)
                    return
                if key == '2':
                    self._try_load_game()
                    return
                if key == '3':
                    self._enter_settings()
                    return
                return
            # settings
            if key == '1':
                # mouse sens — bump through presets
                presets = (80.0, 110.0, 140.0, 180.0, 220.0)
                try:
                    i = presets.index(float(self.mouse_sens))
                    self.mouse_sens = presets[(i + 1) % len(presets)]
                except ValueError:
                    self.mouse_sens = 140.0
                self._refresh_menu_labels()
                self.toast('Mouse sensitivity %d' % int(self.mouse_sens))
                return
            if key == '2':
                self.fullscreen_stub = not bool(getattr(self, 'fullscreen_stub', False))
                try:
                    self.window.fullscreen = self.fullscreen_stub
                except Exception:
                    pass
                self._refresh_menu_labels()
                self.toast('Fullscreen stub ' + ('ON' if self.fullscreen_stub else 'OFF'))
                return
            if key == '3':
                self._show_menu()
                return
            return

        if key == 'f3':
            self.debug_on = not bool(getattr(self, 'debug_on', True))
            if self.debug_hud:
                self.debug_hud.enabled = self.debug_on
            print('[Rune Mommy] debug', 'ON' if self.debug_on else 'OFF')
            return

        # Safe yard: Esc always returns to title (never soft-lock).
        if mode == 'safe' and key == 'escape':
            self._show_menu()
            self.toast('Title menu.')
            return

        if key in ('enter', 'return') and getattr(self, 'tutorial_active', False) and mode == 'play':
            self._finish_tutorial()
            return
        if key == 'escape':
            if self.ui_open:
                self.close_panel()
                return
            if mode == 'safe':
                self._show_menu()
                return
            # Play: first Esc frees cursor (WASD still works); second Esc quits.
            if not getattr(self, 'mouse_free', False) and getattr(self.mouse, 'locked', False):
                self.mouse_free = True
                self._lock_mouse(False)
                self.toast('Cursor free — click window to look again. Esc again quits.')
                return
            application.quit()
            return
        if self.ui_open:
            if key in ('1', '2', '3', '4', '5', '6', '7', '8'):
                self._pick_choice(int(key) - 1)
            return
        if key == 'e':
            if mode == 'safe':
                self._try_safe_gate()
                return
            self._interact()
            return
        if mode != 'play':
            # safe: camera cycle + mouse lock / tab
            if key in ('v', 'V', 'scroll up'):
                self._cycle_camera_mode(+1)
                return
            if key in ('c', 'C', 'scroll down'):
                self._cycle_camera_mode(-1)
                return
            if key in ('u', 'U'):
                self._cycle_outfit(+1)
                return
            if key == 'left mouse down':
                if not getattr(self.mouse, 'locked', False):
                    self._lock_mouse(True)
                    self.mouse_free = False
                    self.toast('Mouse locked. WASD walk. E at pink gate.')
                return
            if key == 'tab':
                self.mouse_free = not getattr(self, 'mouse_free', False)
                self._lock_mouse(not self.mouse_free)
                self.toast('Cursor free (Tab to recapture)' if self.mouse_free else 'Mouse locked. WASD to walk.')
            return
        if key in ('v', 'V', 'scroll up'):
            self._cycle_camera_mode(+1)
            return
        if key in ('c', 'C', 'scroll down'):
            self._cycle_camera_mode(-1)
            return
        if key in ('u', 'U'):
            self._cycle_outfit(+1)
            return
        if key == '1':
            self._toggle_pistol()
            return
        if key in ('f', 'F'):
            if self.in_car:
                try:
                    if sfx is not None:
                        sfx.horn()
                except Exception:
                    pass
                self.toast('Beep beep.')
            else:
                self.toast('Horn works in a car (F).')
            return
        if key in ('h', 'H'):
            self._eat_food()
            return
        if key == 'left mouse down':
            # Clicking the window should capture the mouse for look+WASD.
            if not self.ui_open and not getattr(self.mouse, 'locked', False):
                self._lock_mouse(True)
                self.mouse_free = False
                self.toast('Mouse locked. WASD walk. E talk. Tab frees cursor.')
                return
            if self.pistol_drawn:
                self._shoot()
            return
        if key == 'tab':
            self.mouse_free = not getattr(self, 'mouse_free', False)
            self._lock_mouse(not self.mouse_free)
            self.toast('Cursor free (Tab to recapture)' if self.mouse_free else 'Mouse locked. WASD to walk.')

    def _try_safe_gate(self):
        gate = getattr(self, 'safe_gate', None)
        if not gate or not self.player:
            self.toast('No gate.')
            return
        pos = self._actor_pos()
        d = dist_xz(pos, (gate.x, 0, gate.z))
        if d <= 3.2:
            self._leave_safe_to_world()
        else:
            self.toast('Walk to the pink gate, then E.')

    def _toggle_pistol(self):
        if not self.owned_pistol:
            self.toast('No pistol. Buy one from Gage at Hancock Gun Hut (east).')
            return
        self.pistol_drawn = not self.pistol_drawn
        if self.gun_model and not self.in_car:
            self.gun_model.enabled = self.pistol_drawn
        if self.pistol_drawn:
            self.panic_t = max(self.panic_t, 3.5)
            self.toast('Pistol drawn.')
        else:
            self.toast('Holstered.')

    def _interact(self):
        if getattr(self, 'mode', 'play') in ('menu', 'settings'):
            return
        try:
            if tokyo.try_interact(self):
                return
            if interiors.try_interact(self):
                return
        except Exception:
            pass
        pos = self._actor_pos()
        if getattr(self, 'mode', '') == 'safe':
            if getattr(self, 'safe_gate', None):
                g = self.safe_gate
                if dist_xz(pos, (g.x, 0, g.z)) < 3.5:
                    self._leave_safe_to_world()
                    return
            self.toast('Walk to the pink gate (west) — E to start Clermont.')
            return
        gas = self._nearest_gas(pos)
        if self.in_car:
            if gas:
                self.open_gas_station(gas, self.in_car)
                return
            self._exit_car()
            return
        if gas:
            near_car, _ncd = self._nearest_car(pos, 5.0)
            # Prefer parked/player car near pump; traffic ignored for service
            service = None
            if near_car and not getattr(near_car, 'traffic', False):
                service = near_car
            if service is not None:
                self.open_gas_station(gas, service)
                return
            # No car: allow NPC talk (e.g. Rita); otherwise nudge
            npc_chk, nd_chk = self._nearest_npc(pos, 3.0)
            if not (npc_chk and nd_chk <= 3.0):
                self.toast('Bring a car.')
                return
        car, cd = self._nearest_car(pos, 3.2)
        npc, nd = self._nearest_npc(pos, 3.0)
        stall, sd = self._nearest_stall(pos, 3.6)

        # prefer NPC / stall over car if closer
        if npc and nd <= 3.0 and (car is None or nd <= cd + 0.15):
            kind = getattr(npc, 'kind', '')
            if kind == 'mira':
                self._set_talk_target(npc)
                self.open_mira('start')
                return
            if kind == 'michelle':
                try:
                    from michelle_talk import pick_michelle_opening
                    nid = pick_michelle_opening(self)
                except Exception:
                    nid = 'door' if not self.michelle_seen else 'hi'
                self.michelle_seen = True
                self.michelle_auto_opened = True
                self._set_talk_target(npc)
                self.open_michelle(nid)
                self._quest_event('talk', npc_id='michelle')
                self._tutorial_note('talk')
                return
            if kind == 'gun':
                self._set_talk_target(npc)
                self.open_gun_shop()
                return
            named = getattr(npc, 'npc_id', '')
            if kind in ('lila', 'rosa', 'yara') or named in ('lila', 'rosa', 'yara'):
                self._set_talk_target(npc)
                self.open_vn(kind if kind in ('lila', 'rosa', 'yara') else named)
                return
            if kind == 'talk' or getattr(npc, 'talkable', False):
                _line = getattr(npc, 'line', None) or getattr(npc, 'life_line', None) or '...'
                try:
                    _line = life_sim.decorate_talk_line(npc, _line)
                except Exception:
                    pass
                self._set_talk_target(npc)
                self.open_talk(
                    getattr(npc, 'npc_name', 'NPC'),
                    _line,
                    getattr(npc, 'portrait_tex', None),
                )
                self._quest_event('talk', npc_id=getattr(npc, 'npc_id', ''))
                return
        if self.michelle_seen and self.house_rooms:
            best_room, best_rd = None, 2.8
            for rname in ('guest', 'garage', 'shower', 'lawn'):
                xz = self.house_rooms.get(rname)
                if not xz:
                    continue
                d = dist_xz(pos, (xz[0], 0, xz[1]))
                if d < best_rd:
                    best_room, best_rd = rname, d
            if best_room and (car is None or best_rd <= cd + 0.1):
                if best_room in ('guest', 'shower') and self.michelle_seen:
                    # Offer intimacy mini-game from bedroom/shower after meeting Michelle
                    self._set_talk_target(getattr(self, 'michelle', None))
                    self.open_panel(
                        'Michelle',
                        "The room's warm. Michelle's teal is already half a suggestion.\n"
                        "First name only.",
                        [
                            ('Start intimacy scene', lambda: adult_minigames.start_michelle_sex(self)),
                            ('Just talk', lambda: self.open_michelle(best_room)),
                            ('Leave', self.close_panel),
                        ],
                        portrait=True,
                        portrait_tex=self._michelle_portrait(),
                    )
                else:
                    self.open_michelle(best_room)
                self._quest_event('michelle_room', room=best_room)
                return
        if stall and sd <= 3.6 and (car is None or sd < cd):
            if stall['kind'] == 'gun':
                self.open_gun_shop()
                return
            if stall.get('kind') == 'tire_shop' or stall.get('id') == 'tire_shop_clermont':
                self.open_tire_shop()
                return
            if stall.get('kind') == 'nail_salon' or stall.get('id') == 'nail_salon_clermont':
                try:
                    adult_minigames.start_nail_salon(self)
                except Exception as exc:
                    print('  nail interact skip:', exc)
                return
            if stall.get('kind') in ('food_truck', 'retail', 'big_box', 'shake') or stall.get('shop'):
                self.open_shake_shop(stall)
                return
            self._buy_first_stock(stall)
            return
        if car:
            self._enter_car(car)
            return
        self.toast('Nothing in range. Cars in the median. Mira at The Shake Bar.')

    def _enter_car(self, car):
        from ursina import camera, Vec3
        if getattr(car, 'disabled', False) or float(getattr(car, 'damage', 0) or 0) >= 100:
            self.toast('Car totaled.')
            return
        self.in_car = car
        car.speed = 0
        was_traffic = bool(getattr(car, 'traffic', False))
        car.traffic = False
        car.parked = True
        # Kick NPC driver out when player takes the car
        try:
            if getattr(car, 'has_driver', False) or getattr(car, 'driver', None):
                parking.unseat_driver(self, car, to_crowd=True)
        except Exception:
            car.driver = None
            car.has_driver = False
        if was_traffic or not hasattr(car, 'fuel'):
            car.fuel = float(random.uniform(35, 70))
        car.out_of_gas_toasted = False
        self.visual.enabled = False
        self.pistol_drawn = False
        if self.gun_model:
            self.gun_model.enabled = False
        self.player.position = car.position
        self._set_camera_follow(True)
        self.toast('W accel  S brake/rev  Space handbrake  F horn  E exit/pump')
        try:
            if sfx is not None:
                sfx.engine_update(car, 0.016)
        except Exception:
            pass

    def _exit_car(self):
        from ursina import camera, Vec3
        car = self.in_car
        if not car:
            return
        offset = car.right * 2.2
        self.player.position = car.world_position + offset
        self.player.y = 0
        self.player.rotation_y = car.rotation_y
        car.speed = 0
        self.in_car = None
        self.visual.enabled = True
        self._set_camera_follow(False)
        try:
            if sfx is not None:
                sfx.engine_stop()
        except Exception:
            pass
        self.toast('On foot.')

    # ----- Gas stations ---------------------------------------------------

    def open_gas_station(self, poi, car):
        name = (poi or {}).get('name') or 'Gas'
        fuel = float(getattr(car, 'fuel', 0) or 0)
        dmg = float(getattr(car, 'damage', 0) or 0)
        need = max(0.0, 100.0 - fuel)
        fill_cost = max(1, int(math.ceil(need / 2.0))) if need > 0.5 else 0
        body = f'{name}\nFuel {int(fuel)}%   Damage {int(dmg)}%\n1g per 2% fuel · repair 50g'
        choices = []
        if fill_cost > 0:
            choices.append((f'Fill tank ({fill_cost}g)', lambda c=car, cost=fill_cost: self._gas_fill(c, cost)))
        else:
            choices.append(('Tank is full.', self.close_panel))
        if dmg >= 5:
            choices.append(('Repair (50g)', lambda c=car: self._gas_repair(c)))
        choices.append(('Leave.', self.close_panel))
        self.open_panel(f'{name}   ·   pump', body, choices)

    def _gas_fill(self, car, cost):
        if not car:
            self.close_panel()
            return
        cost = int(cost)
        if self.gold < cost:
            self.toast('Not enough gold.')
            self.close_panel()
            return
        self.gold -= cost
        car.fuel = 100.0
        car.out_of_gas_toasted = False
        self.toast(f'Tank filled. -{cost}g')
        self._quest_event('refuel')
        self.close_panel()

    def _gas_repair(self, car):
        if not car:
            self.close_panel()
            return
        if self.gold < 50:
            self.toast('Not enough gold.')
            self.close_panel()
            return
        self.gold -= 50
        before = float(getattr(car, 'damage', 0) or 0)
        car.damage = max(0.0, before - 60.0)
        if car.damage < 100.0:
            car.disabled = False
        self._update_car_damage_visual(car, 0.016)
        self.toast(f'Repaired. DMG {int(before)}→{int(car.damage)}  -50g')
        self.close_panel()

    # ----- UI panels ------------------------------------------------------

    def _set_talk_target(self, ent):
        """Freeze this NPC while dialogue is open; face player; hold position."""
        self._clear_talk_target()
        self.talk_target = ent
        if ent is None:
            return
        try:
            ent.talk_frozen = True
            ent._talk_hold_pos = (
                float(ent.x),
                float(getattr(ent, 'y', 0) or 0),
                float(ent.z),
            )
        except Exception:
            pass

    def _clear_talk_target(self):
        ent = getattr(self, 'talk_target', None)
        if ent is not None:
            try:
                ent.talk_frozen = False
            except Exception:
                pass
        self.talk_target = None

    def open_panel(self, title, body, choices, portrait=False, portrait_tex=None):
        try:
            if sfx is not None:
                sfx.ui_beep()
        except Exception:
            pass
        from ursina import mouse
        self.ui_open = True
        self.ui_choices = choices
        self._lock_mouse(False)
        self.panel_bg.enabled = True
        self.panel_name.enabled = True
        self.panel_body.enabled = True
        self.panel_name.text = title
        self.panel_body.text = wrap_text(body, 62)
        tex = portrait_tex or (self.mira_texture if portrait else None)
        if tex:
            try:
                self.panel_portrait.texture = tex
                self.panel_portrait.color = self.color.white
            except Exception:
                pass
            self.panel_portrait.enabled = True
        else:
            self.panel_portrait.enabled = False
            try:
                self.panel_portrait.texture = None
            except Exception:
                pass
        shown = list(choices)[: len(self.panel_choices)]
        for i, slot in enumerate(self.panel_choices):
            if i < len(shown):
                slot.enabled = True
                slot.text = f'{i + 1}  {shown[i][0]}'
                # mouse-clickable choice (number keys still work via input)
                slot.on_click = (lambda idx=i: self._pick_choice(idx))
            else:
                slot.enabled = False
                slot.text = ''
                try:
                    slot.on_click = None
                except Exception:
                    pass

    def close_panel(self):
        from ursina import mouse
        self._clear_talk_target()
        self.ui_open = False
        self.ui_choices = []
        self._lock_mouse(True)
        self.panel_bg.enabled = False
        self.panel_portrait.enabled = False
        self.panel_name.enabled = False
        self.panel_body.enabled = False
        for slot in self.panel_choices:
            slot.enabled = False
            try:
                slot.on_click = None
            except Exception:
                pass

    def _pick_choice(self, index):
        if index < 0 or index >= len(self.ui_choices):
            return
        _label, cb = self.ui_choices[index]
        if cb:
            cb()

    def open_mira(self, node_id='start'):
        nodes = (self.mira_dlg or {}).get('nodes') or {}
        node = nodes.get(node_id) or nodes.get('start')
        if not node:
            self.open_talk(
                'Mama Mira',
                "Welcome in, sugar. Cool Down's the one everyone off 50 asks for.",
            )
            return
        choices = []
        for ch in node.get('choices') or []:
            label = ch.get('label', '...')
            nxt = ch.get('next')
            action = ch.get('action')

            def make(n=nxt, a=action):
                def cb():
                    if a == 'shop':
                        shake = next((s for s in self.stalls if s['id'] == 'shake_bar'), None)
                        if shake:
                            self.open_shake_shop(shake)
                        else:
                            self.close_panel()
                    elif n:
                        self.open_mira(n)
                    else:
                        self.close_panel()
                return cb

            choices.append((label, make()))
        if not choices:
            choices = [('Walk away.', self.close_panel)]
        expr = node.get('expression') or 'smile'
        who = node.get('portrait') or 'mira'
        tex_path = portrait_texture_path(who, expr)
        tex = str(tex_path) if tex_path else None
        self.open_panel('Mama Mira', node.get('text', ''), choices, portrait=True, portrait_tex=tex)

    def open_vn(self, who, node_id=None):
        if who == 'michelle':
            self.open_michelle(node_id or 'door')
            return
        if who == 'mira':
            self.open_mira(node_id or 'start')
            return
        dlg_map = {
            'mira': self.mira_dlg,
            'lila': self.lila_dlg,
            'rosa': self.rosa_dlg,
            'yara': self.yara_dlg,
            'michelle': self.michelle_dlg,
        }
        dlg = dlg_map.get(who)
        titles = {
            'lila': 'Lila',
            'rosa': 'Rosa',
            'yara': 'Yara',
            'mira': 'Mama Mira',
            'michelle': 'Michelle',
        }
        title = titles.get(who, (who or 'NPC').title())
        if not dlg:
            self.open_talk(title, '...')
            return
        nodes = (dlg or {}).get('nodes') or {}
        start = node_id or dlg.get('start') or 'start'
        node = nodes.get(start) or nodes.get('start')
        if not node:
            self.open_talk(title, '...')
            return
        choices = []
        for ch in node.get('choices') or []:
            label = ch.get('label', '...')
            nxt = ch.get('next')
            action = ch.get('action')

            def make(n=nxt, a=action, w=who):
                def cb():
                    if a == 'shop':
                        self.close_panel()
                    elif a == 'close' or not n:
                        self.close_panel()
                    else:
                        self.open_vn(w, n)
                return cb

            choices.append((label, make()))
        if not choices:
            choices = [('Walk away.', self.close_panel)]
        expr = node.get('expression') or 'default'
        por = node.get('portrait') or who
        tex = self._tex_for(por, expr)
        if tex is None:
            pp = portrait_texture_path(por, expr)
            tex = str(pp) if pp else None
        self.open_panel(title, node.get('text', ''), choices, portrait=True, portrait_tex=tex)

    def open_talk(self, name, line, portrait_tex=None):
        try:
            # If caller passed an NPC entity via getattr chain elsewhere, skip; string path stays.
            pass
        except Exception:
            pass
        self.open_panel(name, line, [('Later.', self.close_panel)], portrait=bool(portrait_tex), portrait_tex=portrait_tex)

    def open_gun_shop(self):
        pistol = self.items.get('pistol', {})
        ammo = self.items.get('ammo', {})
        p_name = pistol.get('name', 'Lot Pistol')
        a_name = ammo.get('name', 'Pistol Ammo')
        body = "Cash on the plank. Pistol if you want polite. Ammo is not a suggestion."
        choices = [
            (f'{p_name}   -   70g', self._buy_pistol),
            (f'{a_name} x12   -   48g', self._buy_ammo),
            ('Leave.', self.close_panel),
        ]
        self.open_panel('Gage   ·   Hancock Gun Hut', body, choices)

    def _buy_pistol(self):
        if self.owned_pistol:
            self.toast('You already have the lot pistol.')
            self.open_gun_shop()
            return
        if self.gold < 70:
            self.toast('Not enough gold.')
            self.open_gun_shop()
            return
        self.gold -= 70
        self.owned_pistol = True
        self.ammo += 6
        self.toast('Lot Pistol bought. 1 to draw, LMB to shoot. +6 rounds.')
        self._quest_event('buy_pistol')
        self._tutorial_note('gun')
        self.open_gun_shop()

    def _buy_ammo(self):
        if self.gold < 48:
            self.toast('Not enough gold.')
            self.open_gun_shop()
            return
        self.gold -= 48
        self.ammo += 12
        self.toast('12 pistol rounds.')
        self.open_gun_shop()

    def open_tire_shop(self):
        """Rico — patch / balance / full set. Needs a nearby player car."""
        pos = self._actor_pos()
        car = self.in_car
        if car is None:
            car, cd = self._nearest_car(pos, 6.0)
            if car and getattr(car, 'traffic', False):
                car = None
        wear = float(getattr(car, 'tire_wear', 0.0) or 0.0) if car else 0.0
        if car:
            body = (
                "Rico's Tire & Lube. Speed, hard turns, and off-road chew rubber.\n"
                f"This car tire wear: {int(wear)}% — steer/grip fall off as it climbs."
            )
        else:
            body = "Rico's. Bring a car onto the apron (or drive in)."
        choices = []
        if car:
            def _patch(c=car):
                self._tire_service(c, 'patch', 25, 40.0)
            def _balance(c=car):
                self._tire_service(c, 'balance', 35, 22.0)
            def _replace(c=car):
                self._tire_service(c, 'replace', 90, 100.0)
            choices.append(('Patch plug   -   25g  (-40 wear)', _patch))
            choices.append(('Balance & rotate   -   35g  (-22 wear)', _balance))
            choices.append(('New tire set   -   90g  (reset)', _replace))
        choices.append(('Leave.', self.close_panel))
        self.open_panel("Rico   ·   Hwy 50 Tire & Lube", body, choices)

    def _tire_service(self, car, kind, cost, amount):
        if not car:
            self.toast('Bring a car.')
            self.open_tire_shop()
            return
        if self.gold < cost:
            self.toast('Not enough gold.')
            self.open_tire_shop()
            return
        self.gold -= cost
        wear = float(getattr(car, 'tire_wear', 0.0) or 0.0)
        if kind == 'replace':
            car.tire_wear = 0.0
            car.tire_warn_mid = False
            car.tire_warn_hi = False
            self.toast('New tires mounted. Grip restored.')
        else:
            car.tire_wear = max(0.0, wear - float(amount))
            if car.tire_wear < 55:
                car.tire_warn_mid = False
            if car.tire_wear < 85:
                car.tire_warn_hi = False
            self.toast(f'Tires serviced. Wear now {int(car.tire_wear)}%.')
        if kind == 'patch':
            self.pack.append('Tire Patch Kit')
        self._quest_event('tire_service', kind=kind)
        self.open_tire_shop()

    def open_shake_shop(self, stall):
        shop = stall.get('shop') or {}
        greeting = shop.get('greeting') or shop.get('blurb') or stall['name']
        stock = list(shop.get('stock') or [])
        choices = []
        for entry in stock[:3]:
            item_id = entry.get('itemId')
            price = int(entry.get('price', 10))
            item = self.items.get(item_id, {})
            label = f"{item.get('name', item_id)}   -   {price}g"

            def make(iid=item_id, pr=price, nm=item.get('name', item_id)):
                def cb():
                    self._buy_item(iid, pr, nm, stall)
                return cb

            choices.append((label, make()))
        choices.append(('Leave.', self.close_panel))
        title = f"{stall.get('npc') or stall['name']}   ·   {stall['name']}"
        self.open_panel(title, greeting, choices, portrait=stall.get('id') == 'shake_bar')

    def _buy_item(self, item_id, price, name, stall):
        if self.gold < price:
            self.toast('Not enough gold.')
            self.open_shake_shop(stall)
            return
        self.gold -= price
        self.pack.append(name)
        self.toast(name)
        self._quest_event('buy', item_id=item_id)
        self.open_shake_shop(stall)

    def _buy_first_stock(self, stall):
        shop = stall.get('shop') or {}
        stock = list(shop.get('stock') or [])
        if not stock:
            self.toast(f"{stall.get('name', 'Stall')} is empty.")
            return
        entry = stock[0]
        item_id = entry.get('itemId')
        price = int(entry.get('price', 0))
        item = self.items.get(item_id, {})
        name = item.get('name', item_id or 'item')
        if self.gold < price:
            self.toast(f'Need {price}g for {name}.')
            return
        self.gold -= price
        self.pack.append(name)
        self.toast(name)
        self._quest_event('buy', item_id=item_id)

    def _tex_for(self, who, expr='default'):
        # Ursina load_texture needs a path relative to cwd/ROOT, not an absolute Windows path.
        rel = portrait_asset_path(who, expr)
        if not rel:
            for fb in ('smile', 'default', 'sassy', 'tease', 'wink', 'lean'):
                rel = portrait_asset_path(who, fb)
                if rel:
                    break
        if not rel:
            return None
        try:
            from ursina import load_texture
            return load_texture(rel)
        except Exception:
            return None


    def _nearest_house_vol(self, pos, radius):
        best, best_d = None, radius
        for ent in self.house_vols:
            if not ent:
                continue
            d = dist_xz(pos, (ent.x, 0, ent.z))
            if d < best_d:
                best, best_d = getattr(ent, 'room_node', None), d
        if best:
            return best, best_d
        return None

    def _maybe_auto_michelle(self):
        # Never auto-open on spawn — it sets ui_open and freezes WASD.
        # Player must press E at Michelle / the door.
        return

    def open_michelle(self, node_id='door'):
        if getattr(self, 'talk_target', None) is None and getattr(self, 'michelle', None) is not None:
            self._set_talk_target(self.michelle)
        nodes = (self.michelle_dlg or {}).get('nodes') or {}
        start = (self.michelle_dlg or {}).get('start') or 'door'
        node = nodes.get(node_id) or nodes.get(start)
        self.michelle_seen = True
        self.michelle_auto_opened = True
        if not node:
            greet = "Alec, I just got off the plane, can you not stare at my tits for five seconds?"
            self.open_talk('Michelle', greet, self._tex_for('michelle'))
            return
        self.michelle_node = node.get('id') or node_id
        choices = []
        for ch in node.get('choices') or []:
            label = ch.get('label', '...')
            nxt = ch.get('next')
            action = ch.get('action')

            def make(n=nxt, a=action):
                def cb():
                    if a == 'breed':
                        self.breed = min(100, int(self.breed) + 18)
                        self.toast('BREED  %d%%' % int(self.breed))
                        if self.breed >= 100 and not self.preg:
                            self.open_michelle('bun')
                        elif n:
                            self.open_michelle(n)
                        else:
                            self.close_panel()
                    elif a == 'preg':
                        self.preg = True
                        try:
                            self._apply_preg_look()
                        except Exception:
                            pass
                        if n:
                            self.open_michelle(n)
                        else:
                            self.open_michelle('preg')
                    elif a == 'sex_minigame' or a == 'intimacy':
                        try:
                            adult_minigames.start_michelle_sex(self)
                        except Exception as exc:
                            print('  michelle sex minigame skip:', exc)
                            if n:
                                self.open_michelle(n)
                    elif a == 'nail_salon':
                        try:
                            adult_minigames.start_nail_salon(self)
                        except Exception as exc:
                            print('  nail minigame skip:', exc)
                    elif a == 'close' or not n:
                        self.close_panel()
                    else:
                        self.open_michelle(n)
                return cb

            choices.append((label, make()))
        if not choices:
            choices = [('Close.', self.close_panel)]
        who = node.get('portrait') or 'michelle'
        expr = node.get('expression') or 'sassy'
        tex = self._tex_for(who, expr)
        body = node.get('text', '')
        try:
            from michelle_talk import decorate_michelle_text
            body = decorate_michelle_text(self, body)
        except Exception:
            pass
        self.open_panel('Michelle', body, choices, portrait=True, portrait_tex=tex)

    def _michelle_portrait(self):
        if self.michelle is not None and getattr(self.michelle, 'portrait_tex', None):
            return self.michelle.portrait_tex
        return self._tex_for('michelle')

    def _tick_heat(self, dt):
        if self.heat > 0:
            self.heat = max(0.0, self.heat - 0.07 * dt)
        self.heat_spawn_cd = max(0.0, self.heat_spawn_cd - dt)
        if self.heat >= 1.6 and self.heat_spawn_cd <= 0 and len(self.heat_hunters) < 4:
            spawn_heat_hunter(self)
            self.heat_spawn_cd = 2.8

    def _hurt(self, dmg):
        self.hp = max(0, self.hp - dmg)
        if self.hp <= 0:
            self.hp = self.max_hp
            self.gold = self.gold // 2
            self.heat = 0.0
            if self.in_car:
                self._exit_car()
            self.player.position = (0, 0, -8.5)
            self.player.rotation_y = 0
            self.toast('Woke up on the lot. Gold halved.')

    def _eat_food(self):
        if not self.pack:
            self.toast('No shakes. Mira sells Cool Downs.')
            return
        name = self.pack.pop(0)
        self.hp = min(self.max_hp, self.hp + 28)
        self.toast(f'{name}  +28 HP')

    def _apply_preg_look(self):
        m = self.michelle
        if not m:
            return
        chest = getattr(m, 'chest', None)
        if chest:
            chest.scale = (0.78, 0.48, 0.52)

    def _init_quests(self):
        self.quest_active = []
        self.quest_completed = set()
        self.quest_progress = {}
        self.kill_quest_count = 0
        for q in self.quest_defs:
            if q.get('auto_start'):
                self.quest_active.append(q['id'])
                self.quest_progress[q['id']] = 0
        self._quest_unlock_ready()

    def _quest_def(self, qid):
        for q in self.quest_defs:
            if q.get('id') == qid:
                return q
        return None

    def _quest_unlock_ready(self):
        for q in self.quest_defs:
            qid = q.get('id')
            if not qid or qid in self.quest_completed or qid in self.quest_active:
                continue
            reqs = q.get('requires') or []
            if all(r in self.quest_completed for r in reqs):
                self.quest_active.append(qid)
                self.quest_progress[qid] = 0

    def _quest_hud_line(self):
        for qid in self.quest_active:
            q = self._quest_def(qid)
            if not q:
                continue
            hud = q.get('hud') or q.get('name') or qid
            prog = self.quest_progress.get(qid, 0)
            if '{progress}' in hud:
                hud = hud.replace('{progress}', str(prog))
            return f'QUEST  {hud}'
        if self.quest_completed:
            return 'QUEST  done for now'
        return 'QUEST  —'

    def _quest_complete(self, qid):
        if qid in self.quest_completed:
            return
        q = self._quest_def(qid)
        if not q:
            return
        if qid in self.quest_active:
            self.quest_active.remove(qid)
        self.quest_completed.add(qid)
        gold = int(q.get('reward_gold') or 0)
        if gold:
            self.gold += gold
        self.toast(f"Quest complete: {q.get('name', qid)}  +{gold}g")
        self._quest_unlock_ready()

    def _quest_event(self, etype, **kw):
        for qid in list(self.quest_active):
            q = self._quest_def(qid)
            if not q:
                continue
            qtype = q.get('type')
            if etype == 'talk' and qtype == 'talk':
                if kw.get('npc_id') == q.get('npc'):
                    self._quest_complete(qid)
            elif etype == 'buy' and qtype == 'buy':
                if kw.get('item_id') == q.get('item'):
                    self._quest_complete(qid)
            elif etype == 'buy_pistol' and qtype == 'buy_pistol':
                self._quest_complete(qid)
            elif etype == 'kill' and qtype == 'kill':
                kinds = set(q.get('kinds') or [])
                kind = kw.get('kind') or ''
                mob = kw.get('mob_id') or ''
                if kind in kinds or mob in kinds or any(k in (kind, mob) for k in kinds):
                    self.quest_progress[qid] = self.quest_progress.get(qid, 0) + 1
                    need = int(q.get('count') or 3)
                    if self.quest_progress[qid] >= need:
                        self._quest_complete(qid)
            elif etype == 'michelle_room' and qtype == 'michelle_room':
                rooms = set(q.get('rooms') or [])
                if kw.get('room') in rooms:
                    self._quest_complete(qid)
            elif etype == 'visit' and qtype == 'visit':
                poi = q.get('poi') or q.get('place')
                if poi and kw.get('poi_id') == poi:
                    self._quest_complete(qid)
            elif etype == 'refuel' and qtype == 'refuel':
                self._quest_complete(qid)

    def _flags_path(self):
        return ROOT / 'data' / 'local_flags.json'

    def _load_flags(self):
        path = self._flags_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding='utf-8')) or {}
            except Exception:
                return {}
        # also honor legacy save_flags.json
        alt = ROOT / 'data' / 'save_flags.json'
        if alt.exists():
            try:
                return json.loads(alt.read_text(encoding='utf-8')) or {}
            except Exception:
                return {}
        return {}

    def _save_flags(self, data):
        path = self._flags_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        except Exception as exc:
            print('  flags save failed:', exc)

    def _tick_visit_quests(self):
        """Complete visit-type quests when player is near matching POI interact pos."""
        if not self.quest_active:
            return
        pos = self._actor_pos()
        for poi in getattr(self, 'pois', []) or []:
            pid = poi.get('id')
            ppos = poi.get('pos')
            if not pid or not ppos:
                continue
            if dist_xz(pos, ppos) <= 4.5:
                self._quest_event('visit', poi_id=pid)

    def _init_tutorial(self):
        flags = self._load_flags()
        done = bool(flags.get('tutorial_done'))
        self.tutorial_active = not done
        self.tutorial_step = 0
        Entity = self.Entity
        Text = self.Text
        color = self.color
        camera = self.camera
        if not self.tutorial_active:
            self.tutorial_overlay = None
            self.tutorial_text = None
            return
        self.tutorial_overlay = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba32(8, 2, 16, 160),
            scale=(1.1, 0.28),
            position=(0, 0.38),
            z=1,
        )
        self.tutorial_text = Text(
            text='',
            position=(0, 0.40),
            origin=(0, 0),
            color=color.rgb32(255, 230, 255),
            scale=0.85,
        )
        self._refresh_tutorial_text()

    def _tutorial_steps(self):
        return [
            'WASD — walk toward Michelle (Sanctuary Drive door)',
            'E — talk to Michelle',
            'Mouse — look around  |  Enter skips tutorial',
            '1 / LMB — pistol after buying from Gage',
            'H — drink a shake from your pack',
        ]

    def _refresh_tutorial_text(self):
        if not self.tutorial_text:
            return
        steps = self._tutorial_steps()
        i = min(self.tutorial_step, len(steps) - 1)
        self.tutorial_text.text = f'TUTORIAL  {i + 1}/{len(steps)}:  {steps[i]}   (Enter to dismiss)'

    def _tick_tutorial(self, dt):
        if not self.tutorial_active:
            return
        from ursina import held_keys
        # step 0: any WASD movement
        if self.tutorial_step == 0:
            if any(held_keys[k] for k in ('w', 'a', 's', 'd')):
                self.tutorial_step = 1
                self._refresh_tutorial_text()
        elif self.tutorial_step == 2:
            # mouse look — advance after a moment if mouse locked
            if getattr(self.mouse, 'locked', False):
                self.tutorial_step = 3
                self._refresh_tutorial_text()
        # completing talk (step 1) finishes early via _tutorial_note

    def _tutorial_note(self, what):
        if not self.tutorial_active:
            return
        if what == 'talk' and self.tutorial_step <= 1:
            self.tutorial_step = 2
            self._refresh_tutorial_text()
            # completing steps 1-2 can dismiss
            self._finish_tutorial()
            return
        if what == 'gun' and self.tutorial_step >= 3:
            self.tutorial_step = 4
            self._refresh_tutorial_text()

    def _finish_tutorial(self):
        if not self.tutorial_active and not getattr(self, 'tutorial_overlay', None):
            flags = self._load_flags()
            if not flags.get('tutorial_done'):
                flags['tutorial_done'] = True
                self._save_flags(flags)
            return
        self.tutorial_active = False
        try:
            if self.tutorial_overlay:
                self.tutorial_overlay.enabled = False
            if self.tutorial_text:
                self.tutorial_text.enabled = False
                self.tutorial_text.text = ''
        except Exception:
            pass
        flags = self._load_flags()
        flags['tutorial_done'] = True
        self._save_flags(flags)
        self.toast('Tutorial done. Explore Hwy 50.')


    def _debug_tick(self, dt):
        """Console + HUD breadcrumbs when lagging or input-stuck."""
        from ursina import held_keys, mouse, time as u_time
        self._dbg_t += dt
        wish = any(held_keys[k] for k in ('w', 'a', 's', 'd', 'up arrow', 'down arrow'))
        self._dbg_wish = wish
        if wish and getattr(self, 'mode', '') in ('safe', 'play') and not self.in_car:
            # approximate movement by checking position change
            pos = (round(float(self.player.x), 2), round(float(self.player.z), 2))
            last = getattr(self, '_dbg_pos', None)
            moved = last is not None and pos != last
            self._dbg_pos = pos
            if wish and not moved and not self.ui_open:
                self._dbg_stuck_t += dt
            else:
                self._dbg_stuck_t = 0.0
        else:
            self._dbg_stuck_t = 0.0

        # Real frame pacing (unscaled); sim `dt` may be clamped to 0.05
        try:
            raw_dt = float(getattr(u_time, 'dt_unscaled', None) or u_time.dt or dt)
        except Exception:
            raw_dt = float(dt)
        fps = 1.0 / raw_dt if raw_dt > 1e-6 else 0.0
        lag = raw_dt > 0.08
        stuck = self._dbg_stuck_t > 0.7
        # Periodically re-assert FPS cap (Ursina may flip clock back to MNormal)
        if int(self._dbg_t * 2) % 10 == 0:
            try:
                apply_fps_cap()
            except Exception:
                pass
        line = (
            "DBG mode=%s paused=%s ui=%s locked=%s free=%s fps=%.0f dt=%.3f key=%s pos=(%.1f,%.1f) stuck=%.1fs"
            % (
                getattr(self, 'mode', '?'),
                bool(getattr(self, 'world_paused', False)),
                bool(self.ui_open),
                bool(getattr(mouse, 'locked', False)),
                bool(getattr(self, 'mouse_free', False)),
                fps,
                raw_dt,
                getattr(self, '_dbg_last_key', '-'),
                float(self.player.x) if self.player else 0,
                float(self.player.z) if self.player else 0,
                self._dbg_stuck_t,
            )
        )
        if self.debug_hud:
            self.debug_hud.enabled = bool(getattr(self, 'debug_on', True))
            if self.debug_on:
                self.debug_hud.text = line
        # Print on lag, stuck, or every 2s
        if lag or stuck or self._dbg_t >= 2.0:
            self._dbg_t = 0.0
            tag = 'LAG' if lag else ('STUCK' if stuck else 'ok')
            print('[Rune Mommy][%s] %s' % (tag, line))
            if stuck:
                print('[Rune Mommy][STUCK] tip: Esc=menu | click 3D view | arrows move | Q/right-arrow turn')


    def toast(self, msg):
        self.toast_timer = 2.6
        if self.hud_toast:
            self.hud_toast.text = msg
        print(f'[Rune Mommy] {msg}')


def update():
    if GAME:
        GAME.tick()
    if TEST_SECONDS > 0 and (pytime.time() - TEST_T0) >= TEST_SECONDS:
        from ursina import application
        print('RUNE_MOMMY_TEST ok  shakes=%s cars=%s peds=%s traffic=%s parked=%s' % (
            len(GAME.shake_spawned) if GAME else 0,
            len(GAME.cars) if GAME else 0,
            len(getattr(GAME, 'peds', []) or []) if GAME else 0,
            getattr(GAME, 'traffic_count', 0) if GAME else 0,
            getattr(GAME, 'parked_count', 0) if GAME else 0,
        ))
        application.quit()


def input(key):
    if GAME:
        GAME.on_input(key)


def run():
    global GAME, TEST_SECONDS, TEST_T0
    test = os.environ.get('RUNE_MOMMY_TEST', '').strip().lower() in ('1', 'true', 'yes')
    TEST_SECONDS = float(os.environ.get('RUNE_MOMMY_TEST_SEC', '2' if test else '0') or 0)
    window_type = os.environ.get('URSINA_WINDOW', 'offscreen' if test else 'onscreen')
    TEST_T0 = pytime.time()

    print('Rune Mommy   -   Clermont / Hwy 50')
    print('  >>> CLICK THE GAME WINDOW once, then WASD to move <<<')
    print('  WASD walk   mouse look   Space jump')
    print('  If a pink talk panel is open: press Esc, then WASD')
    print('  E enter/exit car, talk, buy')
    print('  1 draw pistol   LMB shoot   H shake   F horn (in car)   V/C camera   U outfit   ESC quit')
    rep = data_report()
    print('  shops:', ', '.join(rep['shake_names']))
    print('  mira portrait:', 'yes' if rep['mira_portrait'] else 'missing')

    app = boot_ursina(window_type=window_type)
    GAME = Game()
    GAME.setup()
    print('  spawned shakes:', len(GAME.shake_spawned), GAME.shake_spawned)
    print('  cars:', len(GAME.cars), ' npcs:', len(GAME.npcs),
          ' crowd=%d' % len(getattr(GAME, 'peds', []) or []),
          ' aki_crowd=%d' % len(getattr(GAME, 'akihabara_crowd', []) or []))
    # buildings/quests already printed once in setup()
    app.run()


if __name__ == '__main__':
    run()
