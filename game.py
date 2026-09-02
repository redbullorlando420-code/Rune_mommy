#!/usr/bin/env python3
"""Rune Mommy — Clermont / Hwy 50. Third-person Ursina desktop game.

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

from loaders import load_shops, portrait_texture_path, load_npcs, load_mobs, load_items

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
    loadPrcFileData('', 'audio-library-name null')
    loadPrcFileData('', 'notify-level-audio fatal')
    loadPrcFileData('', 'notify-level-glgsg warning')
    if window_type in ('offscreen', 'none'):
        loadPrcFileData('', f'window-type {window_type}')

    from ursina import Ursina
    app = Ursina(
        title='Rune Mommy  —  Clermont / Hwy 50',
        borderless=False,
        fullscreen=False,
        development_mode=False,
        vsync=True,
        size=(1280, 720),
        editor_ui_enabled=False,
        show_ursina_splash=False,
        window_type=window_type,
    )
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

        self.gold = 200
        self.pack = []
        self.owned_pistol = False
        self.ammo = 0
        self.pistol_drawn = False
        self.shoot_cd = 0.0
        self.y_vel = 0.0
        self.grounded = True
        self.in_car = None
        self.ui_open = False
        self.ui_choices = []
        self.toast_timer = 0.0
        self.prompt = ''

        self.player = None
        self.cam_pivot = None
        self.visual = None
        self.gun_model = None
        self.cars = []
        self.npcs = []
        self.stalls = []
        self.targets = []
        self.ignore = []
        self.shake_spawned = []

        self.panel_bg = None
        self.panel_portrait = None
        self.panel_name = None
        self.panel_body = None
        self.panel_choices = []
        self.hud_gold = None
        self.hud_ammo = None
        self.hud_pack = None
        self.hud_prompt = None
        self.hud_toast = None
        self.crosshair = None
        self.cam_in_car = False

        mira_p = portrait_texture_path('mira')
        self.mira_portrait_path = mira_p if mira_p else (ROOT / 'client/portraits/mira-coffee.jpg')
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

        self.Sky(color=color.rgb32(20, 8, 34))
        try:
            sun = DirectionalLight(shadows=False)
            sun.look_at(self.Vec3(1, -1.4, 0.4))
            sun.color = color.rgb32(210, 160, 190)
            AmbientLight(color=color.rgb32(90, 60, 110))
            PointLight(position=(0, 5, 0), color=color.rgb32(255, 90, 210))
        except Exception:
            pass

        self._lock_mouse(True)

        self._build_ground()
        self._build_highway()
        self._build_skyline()
        self._build_stalls()
        self._build_npcs()
        self._build_cars()
        self._build_targets()
        self._build_player()
        self._build_hud()

        self.ignore = [self.player, self.visual, self.cam_pivot]
        if self.gun_model:
            self.ignore.append(self.gun_model)

        self.toast('Clermont dusk. Mira is on the neon stool. Cars in the median.')

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

    # ----- world ----------------------------------------------------------

    def _build_ground(self):
        Entity = self.Entity
        color = self.color
        Entity(
            model='plane',
            scale=(140, 1, 110),
            color=color.rgb32(32, 24, 36),
            texture='white_cube',
            texture_scale=(70, 55),
            collider=None,
            y=0,
        )
        # lot asphalt patch
        Entity(
            model='cube',
            scale=(78, 0.04, 52),
            position=(2, 0.02, -14),
            color=color.rgb32(24, 18, 28),
            texture='white_cube',
            texture_scale=(24, 16),
        )

    def _build_highway(self):
        Entity = self.Entity
        color = self.color
        # Hwy 50 east-west between the two stall rows
        Entity(
            model='cube',
            scale=(88, 0.08, 9.5),
            position=(2, 0.05, -16),
            color=color.rgb32(18, 16, 20),
        )
        for x in range(-40, 44, 5):
            Entity(
                model='cube',
                scale=(2.2, 0.09, 0.18),
                position=(x, 0.1, -16),
                color=color.rgb32(230, 200, 60),
            )
        # sidewalks
        Entity(model='cube', scale=(88, 0.07, 1.6), position=(2, 0.06, -10.4), color=color.rgb32(48, 38, 52))
        Entity(model='cube', scale=(88, 0.07, 1.6), position=(2, 0.06, -21.6), color=color.rgb32(48, 38, 52))
        # street lamps
        for x in (-28, -12, 0, 14, 28):
            for z in (-10.2, -21.8):
                Entity(model='cube', scale=(0.12, 3.2, 0.12), position=(x, 1.6, z), color=color.rgb32(40, 30, 50))
                Entity(model='sphere', scale=0.35, position=(x, 3.3, z), color=color.rgb32(255, 90, 200))

    def _build_skyline(self):
        Entity = self.Entity
        color = self.color
        rng = random.Random(50)
        # background buildings north and south
        for i in range(10):
            w, h, d = rng.uniform(3, 7), rng.uniform(4, 14), rng.uniform(3, 6)
            x = -40 + i * 9 + rng.uniform(-1, 1)
            z = 16 + rng.uniform(0, 4)
            Entity(
                model='cube',
                scale=(w, h, d),
                position=(x, h / 2, z),
                color=color.rgb32(rng.randint(28, 55), rng.randint(16, 40), rng.randint(40, 70)),
                collider='box',
            )
        for i in range(8):
            w, h, d = rng.uniform(3, 6), rng.uniform(3, 9), rng.uniform(3, 5)
            x = -34 + i * 10
            z = -48
            Entity(
                model='cube',
                scale=(w, h, d),
                position=(x, h / 2, z),
                color=color.rgb32(rng.randint(30, 60), rng.randint(18, 36), rng.randint(28, 50)),
                collider='box',
            )
        # palm-ish trees
        for x, z in ((-30, 6), (26, 8), (-22, -38), (24, -38), (40, -10), (-36, -8)):
            Entity(model='cube', scale=(0.28, 2.4, 0.28), position=(x, 1.2, z), color=color.rgb32(70, 42, 28), collider='box')
            Entity(model='sphere', scale=1.6, position=(x, 2.8, z), color=color.rgb32(30, 110, 55))

    def _build_stalls(self):
        Entity = self.Entity
        color = self.color
        Text = self.Text
        shops = list((self.shops_data or {}).get('shops') or [])
        for shop in shops:
            sid = shop.get('id', '')
            name = shop.get('name', sid)
            pal = shop.get('palette') or ['#ff4fd8', '#5af0ff', '#1a081c']
            is_gun = sid == 'gun_hut' or 'gun' in name.lower()
            if is_gun:
                x, z = 36.0, 4.0
                w, d, h = 4.2, 3.6, 3.1
                body_col = hex_color(pal[0])
                accent = hex_color(pal[1])
                Entity(
                    model='cube',
                    scale=(w, h, d),
                    position=(x, h / 2, z),
                    color=body_col,
                    collider='box',
                )
                Entity(model='cube', scale=(w + 0.6, 0.18, d + 0.5), position=(x, h + 0.1, z), color=accent)
                Entity(model='cube', scale=(1.4, 0.9, 1.1), position=(x + 2.6, 0.45, z - 1.4), color=color.rgb32(90, 70, 40), collider='box')
                Entity(model='cube', scale=(0.35, 1.4, 0.12), position=(x - 1.4, 1.6, z - 1.9), color=color.rgb32(196, 90, 24))
            else:
                x, z = tile_to_world(shop.get('tileX', 16), shop.get('tileY', 7))
                w = max(3.2, float(shop.get('w', 4)) * 0.85)
                d = max(2.8, float(shop.get('h', 4)) * 0.7)
                h = 2.35 if shop.get('flagship') else 2.05
                body_col = hex_color(pal[2] if len(pal) > 2 else pal[0]).tint(-0.15)
                neon = hex_color(pal[0])
                trim = hex_color(pal[1] if len(pal) > 1 else pal[0])
                Entity(
                    model='cube',
                    scale=(w, h, d),
                    position=(x, h / 2, z),
                    color=body_col,
                    collider='box',
                )
                Entity(model='cube', scale=(w + 0.55, 0.12, d + 0.4), position=(x, h + 0.12, z), color=neon)
                Entity(model='cube', scale=(w + 0.2, 0.08, 0.12), position=(x, h + 0.28, z - d / 2 - 0.05), color=trim)
                # counter
                Entity(model='cube', scale=(w * 0.7, 0.7, 0.45), position=(x, 0.45, z - d / 2 - 0.2), color=trim.tint(-0.3))
            label = Text(
                parent=self._scene(),
                text=name,
                position=(x, (3.35 if is_gun else 2.85), z),
                origin=(0, 0),
                billboard=True,
                color=color.rgb32(255, 210, 255) if not is_gun else color.rgb32(255, 180, 90),
            )
            try:
                label.world_scale = 1.8 if is_gun else 1.45
            except Exception:
                pass
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

    def _scene(self):
        from ursina import scene
        return scene

    def _build_npcs(self):
        Entity = self.Entity
        color = self.color
        portrait = None
        if self.mira_portrait_path.exists():
            try:
                from ursina import load_texture
                portrait = load_texture(str(self.mira_portrait_path))
                self.mira_texture = portrait
            except Exception:
                portrait = str(self.mira_portrait_path)
                self.mira_texture = portrait

        shake = next((s for s in self.stalls if s['id'] == 'shake_bar'), None)
        mx, mz = (0.0, -2.6)
        if shake:
            mx, mz = shake['pos'][0], shake['pos'][2] - 2.4

        mira = self._humanoid(mx, mz, shirt=color.rgb32(255, 70, 180), pants=color.rgb32(40, 12, 40), skin=color.rgb32(255, 206, 166))
        mira.npc_id = 'mira'
        mira.npc_name = 'Mama Mira'
        mira.kind = 'mira'
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
        gage = self._humanoid(gx, gz, shirt=color.rgb32(90, 55, 30), pants=color.rgb32(30, 24, 20), skin=color.rgb32(210, 170, 130))
        gage.npc_id = 'gage'
        gage.npc_name = 'Gage'
        gage.kind = 'gun'
        self.npcs.append(gage)

        steak = next((s for s in self.stalls if s['id'] == 'steak_n_shake'), None)
        if steak:
            deb = self._humanoid(steak['pos'][0], steak['pos'][2] - 2.2, shirt=color.rgb32(245, 210, 50), pants=color.rgb32(20, 20, 20))
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
        }
        for nid, (nx, nz) in talk_spots.items():
            spec = (self.npcs_data or {}).get(nid) or {'id': nid, 'name': nid.title(), 'greet': '...'}
            shirt = hex_color(spec.get('color') or '#ff8fab')
            npc = self._humanoid(nx, nz, shirt=shirt, pants=color.rgb32(36, 24, 40), skin=color.rgb32(255, 200, 160))
            npc.npc_id = nid
            npc.npc_name = spec.get('name', nid.title())
            npc.kind = 'talk'
            npc.line = spec.get('greet') or spec.get('lines', ['...'])[0]
            npc.portrait_tex = None
            pp = portrait_texture_path(nid)
            if pp and Path(pp).is_file():
                try:
                    from ursina import load_texture
                    tex = load_texture(str(pp))
                except Exception:
                    tex = str(pp)
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
            self.npcs.append(npc)

    def _humanoid(self, x, z, shirt, pants, skin=None, hitbox=False):
        Entity = self.Entity
        color = self.color
        skin = skin or color.rgb32(255, 206, 166)
        root = Entity(position=(x, 0, z))
        Entity(parent=root, model='cube', color=pants, scale=(0.42, 0.55, 0.28), y=0.28)
        Entity(parent=root, model='cube', color=shirt, scale=(0.5, 0.62, 0.32), y=0.82, collider='box' if hitbox else None)
        Entity(parent=root, model='sphere', color=skin, scale=0.32, y=1.32)
        Entity(parent=root, model='cube', color=shirt, scale=(0.12, 0.5, 0.12), x=0.34, y=0.78)
        Entity(parent=root, model='cube', color=shirt, scale=(0.12, 0.5, 0.12), x=-0.34, y=0.78)
        if hitbox:
            Entity(parent=root, model='cube', scale=(0.55, 1.55, 0.42), y=0.85, collider='box', visible=False)
        return root

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
            (-3.5, -12.6, 88),
            (2.0, -12.4, 92),
            (7.5, -12.7, 86),
            (14.0, -19.5, 0),
            (-14.0, -19.2, 8),
            (22.0, -12.8, 90),
            (30.5, -6.0, 10),
        ]
        for i, (x, z, yaw) in enumerate(spots[:8]):
            car = self._make_car((x, 0, z), yaw, paints[i % len(paints)])
            self.cars.append(car)

    def _make_car(self, pos, yaw, paint):
        Entity = self.Entity
        color = self.color
        car = Entity(position=pos, rotation_y=yaw)
        car.speed = 0.0
        car.paint = paint
        car.kind = 'car'
        car.body = Entity(parent=car, model='cube', color=paint, scale=(1.65, 0.52, 3.35), y=0.58, collider='box')
        Entity(parent=car, model='cube', color=paint.tint(-0.25), scale=(1.45, 0.42, 1.55), y=1.02, z=-0.15)
        Entity(parent=car, model='cube', color=color.rgb32(40, 80, 120), scale=(1.35, 0.28, 1.35), y=1.12, z=-0.15)
        for wx, wz in ((-0.82, 1.05), (0.82, 1.05), (-0.82, -1.05), (0.82, -1.05)):
            Entity(parent=car, model='cube', color=color.rgb32(18, 18, 18), scale=(0.28, 0.38, 0.42), x=wx, y=0.22, z=wz)
        Entity(parent=car, model='cube', color=color.rgb32(255, 220, 120), scale=(1.2, 0.08, 0.08), y=0.55, z=1.68)
        car.cam_pivot = Entity(parent=car, y=1.35, z=0.2)
        return car

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

        self.player = Entity(position=(0, 0, -8.5), rotation_y=0)
        self.visual = Entity(parent=self.player)
        Entity(parent=self.visual, model='cube', color=color.rgb32(30, 40, 55), scale=(0.44, 0.55, 0.3), y=0.28)
        Entity(parent=self.visual, model='cube', color=color.rgb32(40, 190, 200), scale=(0.52, 0.62, 0.34), y=0.82)
        Entity(parent=self.visual, model='sphere', color=color.rgb32(255, 210, 175), scale=0.33, y=1.32)
        Entity(parent=self.visual, model='cube', color=color.rgb32(40, 190, 200), scale=(0.12, 0.5, 0.12), x=0.34, y=0.78)
        Entity(parent=self.visual, model='cube', color=color.rgb32(40, 190, 200), scale=(0.12, 0.5, 0.12), x=-0.34, y=0.78)
        self.gun_model = Entity(
            parent=self.visual,
            model='cube',
            color=color.rgb32(40, 42, 48),
            scale=(0.08, 0.16, 0.42),
            position=(0.38, 1.05, 0.28),
            enabled=False,
        )
        Entity(parent=self.gun_model, model='cube', color=color.rgb32(30, 30, 32), scale=(0.7, 0.45, 0.35), position=(0, -0.4, -0.15))

        self.cam_pivot = Entity(parent=self.player, y=1.35)
        camera.parent = self.cam_pivot
        camera.position = Vec3(0, 1.65, -8.8)
        camera.rotation = Vec3(12, 0, 0)
        camera.fov = 80

    def _build_hud(self):
        Entity = self.Entity
        Text = self.Text
        color = self.color
        camera = self.camera

        Text(text='RUNE MOMMY', position=(-0.86, 0.48), origin=(-0.5, 0.5), color=color.rgb32(255, 90, 210))
        Text(text='Clermont / Hwy 50', position=(-0.86, 0.445), origin=(-0.5, 0.5), color=color.rgb32(140, 230, 255), scale=0.75)
        self.hud_gold = Text(text='Gold  200', position=(-0.86, 0.40), origin=(-0.5, 0.5), color=color.rgb32(255, 220, 90))
        self.hud_ammo = Text(text='Pistol  —', position=(-0.86, 0.365), origin=(-0.5, 0.5), color=color.rgb32(200, 200, 210), scale=0.85)
        self.hud_pack = Text(text='Pack  0', position=(-0.86, 0.330), origin=(-0.5, 0.5), color=color.rgb32(180, 230, 200), scale=0.85)
        self.hud_prompt = Text(text='', position=(0, -0.42), origin=(0, 0), color=color.rgb32(255, 240, 180), scale=0.9)
        self.hud_toast = Text(text='', position=(0, 0.32), origin=(0, 0), color=color.rgb32(255, 180, 220), scale=0.85)
        self.crosshair = Entity(parent=camera.ui, model='quad', color=color.rgb32(255, 255, 255), scale=0.008, rotation_z=45)

        self.panel_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba32(10, 4, 18, 235),
            scale=(1.58, 0.50),
            position=(0.06, -0.28),
            enabled=False,
            z=0.1,
        )
        self.panel_portrait = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.22, 0.38),
            position=(-0.68, -0.26),
            enabled=False,
            z=-0.05,
        )
        if self.mira_texture:
            self.panel_portrait.texture = self.mira_texture
        self.panel_name = Text(text='', position=(-0.52, -0.08), origin=(-0.5, 0.5), color=color.rgb32(255, 120, 210), enabled=False)
        self.panel_body = Text(text='', position=(-0.52, -0.13), origin=(-0.5, 0.5), color=color.rgb32(245, 230, 255), enabled=False, scale=0.8)
        self.panel_choices = []
        for i in range(4):
            t = Text(
                text='',
                position=(-0.52, -0.34 - i * 0.045),
                origin=(-0.5, 0.5),
                color=color.rgb32(160, 230, 255),
                enabled=False,
                scale=0.75,
            )
            self.panel_choices.append(t)
        Text(
            text='WASD walk   mouse look   E use   1 pistol   LMB shoot   ESC quit',
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

        self._wander_targets(dt)

        if self.ui_open:
            self._refresh_hud()
            return

        if self.in_car:
            self._drive(dt)
        else:
            self._walk(dt)

        if self.pistol_drawn and self.owned_pistol and held_keys['left mouse'] and self.shoot_cd <= 0:
            self._shoot()

        self._refresh_hud()

    def _walk(self, dt):
        from ursina import held_keys, mouse, raycast, Vec3, time
        player = self.player
        if getattr(mouse, 'locked', False):
            player.rotation_y += mouse.velocity[0] * 140
            self.cam_pivot.rotation_x -= mouse.velocity[1] * 140
            self.cam_pivot.rotation_x = max(-35, min(40, self.cam_pivot.rotation_x))

        wish = Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s'],
        )
        if wish.length() > 0:
            wish = wish.normalized()
            move = (player.forward * wish.z + player.right * wish.x) * 7.2 * dt
            origin = player.world_position + Vec3(0, 0.9, 0)
            hit = raycast(origin, move.normalized(), distance=0.7 + move.length(), ignore=self.ignore, debug=False)
            if not hit.hit:
                player.position += move
            player.x = max(-48, min(52, player.x))
            player.z = max(-52, min(22, player.z))

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
            car.cam_pivot.rotation_x -= mouse.velocity[1] * 80
            car.cam_pivot.rotation_x = max(-20, min(25, car.cam_pivot.rotation_x))

        accel, brake, vmax = 16.0, 28.0, 24.0
        if held_keys['w']:
            car.speed += accel * dt
        elif held_keys['s']:
            if car.speed > 0.6:
                car.speed -= brake * dt
            else:
                car.speed -= accel * 0.55 * dt
        else:
            if abs(car.speed) < 0.4:
                car.speed = 0
            else:
                car.speed -= math.copysign(8.0 * dt, car.speed)
        if held_keys['space']:
            car.speed *= max(0.0, 1 - 3.5 * dt)
        car.speed = max(-9.0, min(vmax, car.speed))

        steer = (held_keys['a'] - held_keys['d'])
        if abs(car.speed) > 0.25:
            turn = steer * 95 * (abs(car.speed) / vmax) * dt
            if car.speed < 0:
                turn = -turn
            car.rotation_y += turn

        move = car.forward * car.speed * dt
        origin = car.world_position + Vec3(0, 0.7, 0)
        ign = list(self.ignore) + [car, car.body]
        hit = raycast(origin, move.normalized() if move.length() else car.forward, distance=2.0, ignore=ign, debug=False)
        if hit.hit and move.length() > 0:
            car.speed *= -0.25
        else:
            car.position += move
        car.y = 0
        car.x = max(-48, min(52, car.x))
        car.z = max(-52, min(22, car.z))

        self.player.position = car.position
        self.player.y = 0
        self.player.rotation_y = car.rotation_y
        if self.visual.enabled:
            self.visual.enabled = False
        if not self.cam_in_car:
            self._set_camera_follow(True)

    def _set_camera_follow(self, in_car):
        from ursina import Vec3, camera
        self.cam_in_car = bool(in_car)
        if in_car:
            camera.parent = self.in_car.cam_pivot
            camera.position = Vec3(0, 2.4, -10.5)
            camera.rotation = Vec3(14, 0, 0)
        else:
            camera.parent = self.cam_pivot
            camera.position = Vec3(0, 1.65, -8.8)
            camera.rotation = Vec3(12, 0, 0)

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
                tagged.hp = getattr(tagged, 'hp', 10) - 18
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

    def _refresh_hud(self):
        if self.hud_gold:
            self.hud_gold.text = f'Gold  {self.gold}'
        if self.hud_ammo:
            if not self.owned_pistol:
                self.hud_ammo.text = 'Pistol  not owned'
            elif self.pistol_drawn:
                self.hud_ammo.text = f'Pistol  DRAWN   ammo {self.ammo}'
            else:
                self.hud_ammo.text = f'Pistol  holstered   ammo {self.ammo}'
        if self.hud_pack:
            self.hud_pack.text = f'Pack  {len(self.pack)}'
        if self.gun_model:
            self.gun_model.enabled = bool(self.pistol_drawn and self.owned_pistol and not self.in_car)
        if self.ui_open:
            if self.hud_prompt:
                self.hud_prompt.text = '1-4 choose    ESC close'
            return
        prompt = self._nearest_prompt()
        if self.hud_prompt:
            self.hud_prompt.text = prompt

    def _nearest_prompt(self):
        pos = self._actor_pos()
        if self.in_car:
            return 'E  exit car'
        car, cd = self._nearest_car(pos, 3.2)
        npc, nd = self._nearest_npc(pos, 3.0)
        stall, sd = self._nearest_stall(pos, 3.6)
        options = []
        if car:
            options.append((cd, f'E  enter car'))
        if npc:
            kind = getattr(npc, 'kind', '')
            if kind == 'mira':
                options.append((nd, 'E  talk to Mama Mira'))
            elif kind == 'gun':
                options.append((nd, 'E  Hancock Gun Hut (Gage)'))
            elif kind not in ('target', 'mob'):
                options.append((nd, f'E  talk to {getattr(npc, "npc_name", "NPC")}'))
        if stall and (not npc or sd + 0.4 < nd):
            if stall['kind'] == 'gun':
                options.append((sd, 'E  Hancock Gun Hut'))
            else:
                options.append((sd, f'E  {stall["name"]}'))
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
            d = dist_xz(pos, (car.x, 0, car.z))
            if d < best_d:
                best, best_d = car, d
        return best, best_d

    def _nearest_npc(self, pos, radius):
        best, best_d = None, radius
        for npc in self.npcs:
            if not npc:
                continue
            if getattr(npc, 'kind', '') in ('target', 'mob'):
                continue
            if getattr(npc, 'enabled', True) is False:
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
        if key == 'escape':
            if self.ui_open:
                self.close_panel()
                return
            application.quit()
            return
        if self.ui_open:
            if key in ('1', '2', '3', '4'):
                self._pick_choice(int(key) - 1)
            return
        if key == 'e':
            self._interact()
            return
        if key == '1':
            self._toggle_pistol()
            return
        if key == 'left mouse down':
            if self.pistol_drawn:
                self._shoot()
            return
        if key == 'tab':
            self._lock_mouse(not bool(getattr(mouse, 'locked', True)))

    def _toggle_pistol(self):
        if not self.owned_pistol:
            self.toast('No pistol. Buy one from Gage at Hancock Gun Hut (east).')
            return
        self.pistol_drawn = not self.pistol_drawn
        if self.gun_model and not self.in_car:
            self.gun_model.enabled = self.pistol_drawn
        self.toast('Pistol drawn.' if self.pistol_drawn else 'Holstered.')

    def _interact(self):
        pos = self._actor_pos()
        if self.in_car:
            self._exit_car()
            return
        car, cd = self._nearest_car(pos, 3.2)
        npc, nd = self._nearest_npc(pos, 3.0)
        stall, sd = self._nearest_stall(pos, 3.6)

        # prefer NPC / stall over car if closer
        if npc and nd <= 3.0 and (car is None or nd <= cd + 0.15):
            kind = getattr(npc, 'kind', '')
            if kind == 'mira':
                self.open_mira('start')
                return
            if kind == 'gun':
                self.open_gun_shop()
                return
            if kind == 'talk':
                self.open_talk(
                    getattr(npc, 'npc_name', 'NPC'),
                    getattr(npc, 'line', '...'),
                    getattr(npc, 'portrait_tex', None),
                )
                return
        if stall and sd <= 3.6 and (car is None or sd < cd):
            if stall['kind'] == 'gun':
                self.open_gun_shop()
                return
            self._buy_first_stock(stall)
            return
        if car:
            self._enter_car(car)
            return
        self.toast('Nothing in range. Cars in the median. Mira at The Shake Bar.')

    def _enter_car(self, car):
        from ursina import camera, Vec3
        self.in_car = car
        car.speed = 0
        self.visual.enabled = False
        self.pistol_drawn = False
        if self.gun_model:
            self.gun_model.enabled = False
        self.player.position = car.position
        self._set_camera_follow(True)
        self.toast('W accel  S brake  A/D steer  E exit')

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
        self.toast('On foot.')

    # ----- UI panels ------------------------------------------------------

    def open_panel(self, title, body, choices, portrait=False, portrait_tex=None):
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
            except Exception:
                pass
            self.panel_portrait.enabled = True
        else:
            self.panel_portrait.enabled = False
        for i, slot in enumerate(self.panel_choices):
            if i < len(choices):
                slot.enabled = True
                slot.text = f'{i + 1}  {choices[i][0]}'
            else:
                slot.enabled = False
                slot.text = ''

    def close_panel(self):
        from ursina import mouse
        self.ui_open = False
        self.ui_choices = []
        self._lock_mouse(True)
        self.panel_bg.enabled = False
        self.panel_portrait.enabled = False
        self.panel_name.enabled = False
        self.panel_body.enabled = False
        for slot in self.panel_choices:
            slot.enabled = False

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
        self.open_panel('Mama Mira', node.get('text', ''), choices, portrait=True)

    def open_talk(self, name, line, portrait_tex=None):
        self.open_panel(name, line, [('Later.', self.close_panel)], portrait=bool(portrait_tex), portrait_tex=portrait_tex)

    def open_gun_shop(self):
        pistol = self.items.get('pistol', {})
        ammo = self.items.get('ammo', {})
        p_name = pistol.get('name', 'Lot Pistol')
        a_name = ammo.get('name', 'Pistol Ammo')
        body = "Cash on the plank. Pistol if you want polite. Ammo is not a suggestion."
        choices = [
            (f'{p_name}  —  70g', self._buy_pistol),
            (f'{a_name} x12  —  48g', self._buy_ammo),
            ('Leave.', self.close_panel),
        ]
        self.open_panel('Gage  ·  Hancock Gun Hut', body, choices)

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

    def open_shake_shop(self, stall):
        shop = stall.get('shop') or {}
        greeting = shop.get('greeting') or shop.get('blurb') or stall['name']
        stock = list(shop.get('stock') or [])
        choices = []
        for entry in stock[:3]:
            item_id = entry.get('itemId')
            price = int(entry.get('price', 10))
            item = self.items.get(item_id, {})
            label = f"{item.get('name', item_id)}  —  {price}g"

            def make(iid=item_id, pr=price, nm=item.get('name', item_id)):
                def cb():
                    self._buy_item(iid, pr, nm, stall)
                return cb

            choices.append((label, make()))
        choices.append(('Leave.', self.close_panel))
        title = f"{stall.get('npc') or stall['name']}  ·  {stall['name']}"
        self.open_panel(title, greeting, choices, portrait=stall.get('id') == 'shake_bar')

    def _buy_item(self, item_id, price, name, stall):
        if self.gold < price:
            self.toast('Not enough gold.')
            self.open_shake_shop(stall)
            return
        self.gold -= price
        self.pack.append(name)
        self.toast(name)
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
        print('RUNE_MOMMY_TEST ok  shakes=%s cars=%s' % (
            len(GAME.shake_spawned) if GAME else 0,
            len(GAME.cars) if GAME else 0,
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

    print('Rune Mommy  —  Clermont / Hwy 50')
    print('  WASD walk   mouse look   Space jump')
    print('  E enter/exit car, talk, buy')
    print('  1 draw pistol   LMB shoot   ESC quit')
    rep = data_report()
    print('  shops:', ', '.join(rep['shake_names']))
    print('  mira portrait:', 'yes' if rep['mira_portrait'] else 'missing')

    app = boot_ursina(window_type=window_type)
    GAME = Game()
    GAME.setup()
    print('  spawned shakes:', len(GAME.shake_spawned), GAME.shake_spawned)
    print('  cars:', len(GAME.cars), ' npcs:', len(GAME.npcs))
    app.run()


if __name__ == '__main__':
    run()
