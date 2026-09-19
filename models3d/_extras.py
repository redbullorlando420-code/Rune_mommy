"""Food trucks, Walmart box, map densify helpers. Pitched roofs use ±28 A-frame."""
from __future__ import annotations
import random
from models3d._base import _t, _safe_tex, _rgb, hollow_shell
from models3d._build import _pitched_roof, make_house, make_billboard, make_street_sign


# Unique ground Ys (match game highway/lot convention)
Y_LOT = 0.02
Y_SIDEWALK = 0.07
Y_HWY = 0.09
Y_PAINT = 0.12


def make_food_truck(Entity, color, Text, scene_parent, x, z, *, name='Food Truck',
                    body_rgb=(244, 211, 94), accent_rgb=(238, 150, 75), yaw=0):
    """Florida-style box food truck with awning + service window."""
    n = 0
    body = _rgb(color, *body_rgb)
    accent = _rgb(color, *accent_rgb)
    dark = _rgb(color, 30, 28, 34)
    # chassis / box
    Entity(model='cube', scale=(4.2, 2.2, 2.4), position=(x, 1.35, z), color=body,
           texture=_t('stucco') or _t('metal'), texture_scale=(2, 1.2),
           rotation_y=yaw, collider='box')
    n += 1
    # roof lip
    Entity(model='cube', scale=(4.4, 0.15, 2.55), position=(x, 2.55, z), color=accent, rotation_y=yaw)
    n += 1
    # awning
    Entity(model='cube', scale=(3.0, 0.08, 1.1), position=(x, 2.15, z - 1.5), color=accent, rotation_y=yaw)
    n += 1
    # service window
    Entity(model='cube', scale=(1.8, 0.9, 0.08), position=(x, 1.55, z - 1.22),
           color=_rgb(color, 180, 220, 240), rotation_y=yaw)
    n += 1
    # wheels
    for dx in (-1.3, 1.3):
        for dz in (-0.9, 0.9):
            Entity(model='cube', scale=(0.35, 0.35, 0.2), position=(x + dx, 0.3, z + dz),
                   color=dark, rotation_y=yaw)
            n += 1
    # menu board
    Entity(model='cube', scale=(1.4, 1.0, 0.08), position=(x + 2.0, 1.6, z - 0.2),
           color=_rgb(color, 20, 20, 28), rotation_y=yaw)
    n += 1
    # lot pad
    Entity(model='cube', scale=(6.0, 0.04, 4.0), position=(x, Y_LOT, z),
           color=_rgb(color, 40, 38, 42), texture=_t('asphalt'), texture_scale=(3, 2))
    n += 1
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=name, position=(x, 3.1, z), origin=(0, 0),
                 billboard=True, color=_rgb(color, 255, 230, 180))
        try:
            t.world_scale = 2.5
        except Exception:
            pass
    return n, (x, 0, z - 2.0)


def make_walmart(Entity, color, Text, scene_parent, x, z):
    """Large big-box — true walk-in shell (south door gap, no solid front collider)."""
    n = 0
    blue = _rgb(color, 0, 113, 206)
    yellow = _rgb(color, 255, 194, 32)
    grey = _rgb(color, 210, 210, 215)
    w, d, h = 22.0, 14.0, 5.5
    tex = _safe_tex('concrete', 'stucco')
    hn, _door = hollow_shell(
        Entity, color, x, z, w, d, h, grey,
        door_gap=3.2, door_face='s',
        floor_col=_rgb(color, 200, 200, 205),
        ceil_col=_rgb(color, 235, 235, 240),
        wall_tex=tex, floor_tex=_safe_tex('concrete'),
    )
    n += hn
    # blue fascia band (outside south face)
    Entity(model='cube', scale=(22.4, 0.8, 0.3), position=(x, 5.0, z - d / 2 - 0.1), color=blue)
    Entity(model='cube', scale=(8.0, 1.4, 0.25), position=(x, 4.2, z - d / 2 - 0.15), color=blue)
    n += 2
    # yellow spark accent
    Entity(model='cube', scale=(2.2, 2.2, 0.2), position=(x - 7.5, 3.8, z - d / 2 - 0.2), color=yellow)
    n += 1
    # open entry canopy (no collider — walk under)
    Entity(model='cube', scale=(4.0, 0.2, 1.8), position=(x, 3.2, z - d / 2 - 0.9),
           color=_rgb(color, 180, 190, 200))
    Entity(model='cube', scale=(3.2, 2.6, 0.08), position=(x - 1.7, 1.4, z - d / 2 - 0.05),
           color=_rgb(color, 120, 180, 220))  # glass left of door
    Entity(model='cube', scale=(3.2, 2.6, 0.08), position=(x + 1.7, 1.4, z - d / 2 - 0.05),
           color=_rgb(color, 120, 180, 220))
    n += 3
    # parking lot (unique Y)
    Entity(model='cube', scale=(28.0, 0.04, 12.0), position=(x, Y_LOT, z - 14.0),
           color=_rgb(color, 36, 34, 38), texture=_safe_tex('asphalt'), texture_scale=(8, 4))
    n += 1
    # parking stripes
    for i in range(-4, 5):
        Entity(model='cube', scale=(0.15, 0.05, 2.2), position=(x + i * 2.5, Y_PAINT, z - 12.5),
               color=_rgb(color, 230, 220, 80))
        n += 1
    # cart corral
    Entity(model='cube', scale=(3.0, 1.2, 2.0), position=(x + 8.0, 0.6, z - 10.0),
           color=_rgb(color, 120, 120, 130), collider='box')
    n += 1
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text='WALMART', position=(x, 6.4, z - 7.0),
                 origin=(0, 0), billboard=True, color=yellow)
        try:
            t.world_scale = 3.6
        except Exception:
            pass
    return n, (x, 0, z - 9.0)



def make_retail_box(Entity, color, Text, scene_parent, x, z, *, name='Shop',
                    w=8.0, d=6.0, h=3.4, body_rgb=(0, 70, 190), accent_rgb=(255, 242, 0),
                    yaw=0, sign_rgb=None):
    """Walk-in retail shell — south door gap, shelves filled by interiors.py."""
    n = 0
    body = _rgb(color, *body_rgb)
    accent = _rgb(color, *accent_rgb)
    sign_c = _rgb(color, *(sign_rgb or accent_rgb))
    dark = _rgb(color, 28, 28, 32)
    # lot pad (unique Y)
    Entity(model='cube', scale=(w + 4.0, 0.04, d + 5.0), position=(x, Y_LOT, z - 1.0),
           color=_rgb(color, 42, 40, 44), texture=_safe_tex('asphalt'), texture_scale=(4, 3))
    n += 1
    # sidewalk strip in front
    Entity(model='cube', scale=(w + 2.0, 0.05, 2.2), position=(x, Y_SIDEWALK, z - d / 2 - 1.2),
           color=_rgb(color, 160, 158, 150), texture=_safe_tex('concrete', 'stucco'), texture_scale=(3, 1))
    n += 1
    # hollow walk-in shell
    tex = _safe_tex('stucco', 'concrete')
    hn, _door = hollow_shell(
        Entity, color, x, z, w, d, h, body,
        door_gap=min(1.8, w * 0.35), door_face='s',
        floor_col=_rgb(color, 180, 180, 190),
        ceil_col=_rgb(color, 230, 230, 235),
        wall_tex=tex, floor_tex=_safe_tex('concrete'),
    )
    n += hn
    # fascia / sign band
    Entity(model='cube', scale=(w + 0.2, 0.7, 0.25), position=(x, h - 0.2, z - d / 2 - 0.05),
           color=accent, rotation_y=yaw)
    n += 1
    # glass panes flanking door (no collider)
    gap = min(1.8, w * 0.35)
    pane_w = max(0.4, (w * 0.7 - gap) / 2.0)
    Entity(model='cube', scale=(pane_w, h * 0.45, 0.08),
           position=(x - gap / 2 - pane_w / 2, h * 0.45, z - d / 2 - 0.08),
           color=_rgb(color, 140, 190, 220), rotation_y=yaw)
    Entity(model='cube', scale=(pane_w, h * 0.45, 0.08),
           position=(x + gap / 2 + pane_w / 2, h * 0.45, z - d / 2 - 0.08),
           color=_rgb(color, 140, 190, 220), rotation_y=yaw)
    n += 2
    # ridge-up roof (A-frame ±28 via helper)
    _pitched_roof(Entity, color, x, h, z, w + 0.4, d + 0.3, dark)
    n += 1
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=name, position=(x, h + 1.1, z - d / 2),
                 origin=(0, 0), billboard=True, color=sign_c)
        try:
            t.world_scale = 3.2
        except Exception:
            pass
    # interact point: front sidewalk
    interact = (x, 0, z - d / 2 - 1.6)
    return n, interact


def make_tire_shop(Entity, color, Text, scene_parent, x, z, *, name='Tire Shop'):
    """Garage bay tire shop — walk-in bay gap on south face."""
    n = 0
    body = _rgb(color, 45, 45, 48)
    accent = _rgb(color, 255, 107, 0)
    # apron
    Entity(model='cube', scale=(10.0, 0.04, 8.0), position=(x, Y_LOT, z - 1.0),
           color=_rgb(color, 38, 36, 40), texture=_safe_tex('asphalt'), texture_scale=(4, 3))
    n += 1
    Entity(model='cube', scale=(8.0, 0.05, 2.0), position=(x, Y_SIDEWALK, z - 4.2),
           color=_rgb(color, 150, 148, 140))
    n += 1
    # hollow garage with wide bay
    w, d, h = 7.0, 5.5, 3.2
    hn, _door = hollow_shell(
        Entity, color, x, z, w, d, h, body,
        door_gap=3.4, door_face='s',
        floor_col=_rgb(color, 50, 50, 55),
        ceil_col=_rgb(color, 60, 60, 65),
        wall_tex=_safe_tex('stucco', 'concrete'),
    )
    n += hn
    # sign
    Entity(model='cube', scale=(6.5, 0.6, 0.2), position=(x, 3.3, z - 2.8), color=accent)
    n += 1
    _pitched_roof(Entity, color, x, 3.2, z, 7.4, 5.8, _rgb(color, 30, 30, 34))
    n += 1
    # stacked tire props
    for i, (dx, dz) in enumerate(((-2.8, -3.2), (-2.8, -3.6), (2.6, -3.0))):
        for k in range(3):
            Entity(model='cube', scale=(0.55, 0.18, 0.55),
                   position=(x + dx, 0.2 + k * 0.2, z + dz),
                   color=_rgb(color, 18, 18, 18))
            n += 1
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=name, position=(x, 4.2, z - 2.8),
                 origin=(0, 0), billboard=True, color=accent)
        try:
            t.world_scale = 3.0
        except Exception:
            pass
    return n, (x, 0, z - 4.5)


def densify_hwy50(Entity, color, Text, scene_parent, building_count_ref=None, game=None):
    """Expand Clermont: more grid blocks, houses, strip plazas along Hwy 50 + side streets.

    Unique ground Ys; ridge-up roofs. Avoids lake / parking lot cores.
    Uses footprints AABB when `game` is provided so houses never overlap.
    """
    rng = random.Random(50)
    n = 0
    fp = None
    if game is not None:
        try:
            import footprints as _fp
            fp = _fp.get(game)
        except Exception:
            fp = None
    # Fill east Hwy 50 corridor toward Walmart
    east_houses = (
        (48.0, -6.0, 'E Hwy 50'), (52.0, -10.0, 'Lakeview Ct'),
        (56.0, -4.0, 'Orange Ave'), (46.0, 4.0, 'Hancock N'),
        (50.0, 8.0, 'Citrus Edge'), (60.0, 2.0, 'Spar Blvd'),
        (54.0, -28.0, 'Lake Spur'), (58.0, -8.0, 'Cart Path'),
        (66.0, -8.0, 'East Spur'), (44.0, 10.0, 'Grove N'),
    )
    for x, z, label in east_houses:
        w, d = rng.uniform(3.0, 4.0), rng.uniform(2.8, 3.5)
        if fp is not None:
            x, z, ok = fp.place(x, z, w=w, d=d, label=label)
            if not ok:
                continue
        make_house(
            Entity, color, Text, scene_parent, x, z,
            w=w, h=rng.uniform(2.5, 3.2), d=d,
            label=label, porch=True, garage=(rng.random() < 0.4), rng=rng,
        )
        n += 1
    # West densify past Quiet Spa
    west_houses = (
        (-44.0, -10.0, 'W Hwy 50'), (-48.0, -18.0, 'Serenity Ln'),
        (-42.0, -24.0, 'Palm Ct'), (-50.0, 6.0, 'Grove St'),
        (-54.0, -8.0, 'Cypress W'), (-46.0, 10.0, 'Sanctuary W'),
        (-52.0, -28.0, 'Palm Deep'), (-40.0, -32.0, 'Spa Spur'),
    )
    for x, z, label in west_houses:
        w, d = rng.uniform(3.0, 3.8), rng.uniform(2.6, 3.4)
        if fp is not None:
            x, z, ok = fp.place(x, z, w=w, d=d, label=label)
            if not ok:
                continue
        make_house(
            Entity, color, Text, scene_parent, x, z,
            w=w, h=rng.uniform(2.4, 3.0), d=d,
            roof_col=_rgb(color, rng.randint(40, 100), rng.randint(80, 140), rng.randint(100, 160)),
            label=label, porch=True, rng=rng,
        )
        n += 1
    # North residential grid (Sanctuary / side streets) — fill NPC destinations
    # Keep densify north of Hwy 50 but OUTSIDE spawn plaza (~-18,12 r=32) / Sanctuary yard
    north_grid = (
        (-8.0, 10.0), (0.0, 10.0), (8.0, 10.0), (16.0, 10.0), (24.0, 10.0),
        (-12.0, 14.0), (4.0, 14.0), (20.0, 14.0), (12.0, 6.5),
        (32.0, 10.0), (28.0, 14.0), (-48.0, 14.0), (-52.0, 8.0),
    )
    for i, (x, z) in enumerate(north_grid):
        w, d = rng.uniform(2.8, 3.6), rng.uniform(2.5, 3.2)
        label = f'Block {i + 1}'
        if fp is not None:
            x, z, ok = fp.place(x, z, w=w, d=d, label=label)
            if not ok:
                continue
        make_house(
            Entity, color, Text, scene_parent, x, z,
            w=w, h=rng.uniform(2.3, 3.0), d=d,
            label=label, porch=(rng.random() < 0.55), rng=rng,
        )
        n += 1
    # South of hwy (waterfront / lake-adjacent — keep clear of deep lake SE core ~16,-42)
    south_houses = (
        (-24.0, -28.0, 'S Lot'), (-12.0, -32.0, 'Canal St'),
        (4.0, -34.0, 'Pond Side'), (24.0, -30.0, 'Bait Row'),
        (36.0, -28.0, 'Club Spur'), (-32.0, -36.0, 'Wetland'),
        (12.0, -38.0, 'Boardwalk'), (48.0, -24.0, 'East Lot'),
    )
    for x, z, label in south_houses:
        w, d = rng.uniform(2.8, 3.5), rng.uniform(2.4, 3.1)
        if fp is not None:
            x, z, ok = fp.place(x, z, w=w, d=d, label=label)
            if not ok:
                continue
        make_house(
            Entity, color, Text, scene_parent, x, z,
            w=w, h=rng.uniform(2.2, 2.9), d=d,
            label=label, porch=True, rng=rng,
        )
        n += 1
    # Strip plazas (flat roof ok for plazas; add A-frame kiosk)
    plazas = (
        (-28.0, -8.0, 'Plaza Kiosk'), (10.0, -24.0, 'Lot Snacks'), (34.0, -32.0, 'Bait Shed'),
        (-8.0, -24.0, 'S Strip'), (20.0, 4.0, 'N Kiosk'), (-18.0, 4.0, 'Yard Mart'),
        (52.0, -22.0, 'Cart Hut'), (-40.0, -8.0, 'Spa Strip'),
        (4.0, -8.0, 'Median Mart'), (30.0, -8.0, 'Hancock Mini'),
    )
    for x, z, name in plazas:
        if fp is not None:
            x, z, ok = fp.place(x, z, w=3.5, d=3.0, label=name)
            if not ok:
                continue
        Entity(model='cube', scale=(3.5, 2.2, 3.0), position=(x, 1.1, z),
               color=_rgb(color, rng.randint(80, 140), rng.randint(70, 120), rng.randint(90, 150)),
               texture=_t('stucco'), texture_scale=(2, 1.2), collider='box')
        _pitched_roof(Entity, color, x, 2.2, z, 3.9, 3.2, _rgb(color, 60, 50, 70))
        n += 1
        if Text and scene_parent is not None:
            kt = Text(parent=scene_parent, text=name, position=(x, 3.4, z), origin=(0, 0),
                 billboard=True, color=_rgb(color, 255, 210, 255))
            try:
                kt.world_scale = 2.4
            except Exception:
                pass
    # Sidewalk ribbons (visual only) along hwy shoulders — unique Y
    for z in (-10.6, -21.4):
        Entity(model='cube', scale=(110.0, 0.04, 1.6), position=(8.0, Y_SIDEWALK, z),
               color=_rgb(color, 155, 152, 145), texture=_t('concrete') or _t('stucco'),
               texture_scale=(20, 1))
        n += 1
    make_street_sign(Entity, color, Text, scene_parent, 54.0, -16.0, 'E Hwy 50')
    make_street_sign(Entity, color, Text, scene_parent, -46.0, -14.0, 'W Hwy 50')
    make_street_sign(Entity, color, Text, scene_parent, -22.0, 6.0, 'Pet Plaza')
    make_street_sign(Entity, color, Text, scene_parent, 28.0, 6.0, 'Electronics Row')
    make_billboard(Entity, color, Text, scene_parent, 58.0, -20.0, 'WALMART\nAHEAD', face_yaw=0)
    make_billboard(Entity, color, Text, scene_parent, 24.0, 4.0, 'BEST BUY\nOPEN-BOX', face_yaw=180)
    n += 6
    if isinstance(building_count_ref, list) and building_count_ref:
        building_count_ref[0] += n
    return n
