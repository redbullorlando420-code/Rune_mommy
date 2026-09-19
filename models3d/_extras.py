"""Food trucks, Walmart box, map densify helpers. Pitched roofs use ±28 A-frame."""
from __future__ import annotations
import random
from models3d._base import _t, _rgb
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
            t.world_scale = 1.3
        except Exception:
            pass
    return n, (x, 0, z - 2.0)


def make_walmart(Entity, color, Text, scene_parent, x, z):
    """Large big-box store footprint — enterable via interiors door."""
    n = 0
    blue = _rgb(color, 0, 113, 206)
    yellow = _rgb(color, 255, 194, 32)
    grey = _rgb(color, 210, 210, 215)
    # main box
    Entity(model='cube', scale=(22.0, 5.5, 14.0), position=(x, 2.75, z), color=grey,
           texture=_t('concrete') or _t('stucco'), texture_scale=(4, 2), collider='box')
    n += 1
    # blue fascia band
    Entity(model='cube', scale=(22.4, 0.8, 0.3), position=(x, 5.0, z - 7.1), color=blue)
    Entity(model='cube', scale=(8.0, 1.4, 0.25), position=(x, 4.2, z - 7.15), color=blue)
    n += 2
    # yellow spark accent
    Entity(model='cube', scale=(2.2, 2.2, 0.2), position=(x - 7.5, 3.8, z - 7.2), color=yellow)
    n += 1
    # entry recess
    Entity(model='cube', scale=(4.0, 3.2, 1.5), position=(x, 1.6, z - 7.8), color=_rgb(color, 180, 190, 200),
           collider='box')
    Entity(model='cube', scale=(3.2, 2.6, 0.12), position=(x, 1.4, z - 8.55), color=_rgb(color, 120, 180, 220))
    n += 2
    # parking lot (unique Y)
    Entity(model='cube', scale=(28.0, 0.04, 12.0), position=(x, Y_LOT, z - 14.0),
           color=_rgb(color, 36, 34, 38), texture=_t('asphalt'), texture_scale=(8, 4))
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
            t.world_scale = 2.2
        except Exception:
            pass
    return n, (x, 0, z - 9.0)


def densify_hwy50(Entity, color, Text, scene_parent, building_count_ref=None):
    """Extra houses / strip POIs along Hwy 50 / Clermont gaps. Pitched ±28 roofs."""
    rng = random.Random(50)
    n = 0
    # Fill east Hwy 50 corridor toward Walmart
    east_houses = (
        (48.0, -6.0, 'E Hwy 50'), (52.0, -10.0, 'Lakeview Ct'),
        (56.0, -4.0, 'Orange Ave'), (46.0, 4.0, 'Hancock N'),
        (50.0, 8.0, 'Citrus Edge'),
    )
    for x, z, label in east_houses:
        make_house(
            Entity, color, Text, scene_parent, x, z,
            w=rng.uniform(3.0, 4.0), h=rng.uniform(2.5, 3.2), d=rng.uniform(2.8, 3.5),
            label=label, porch=True, garage=(rng.random() < 0.4), rng=rng,
        )
        n += 1
    # West densify past Quiet Spa
    west_houses = (
        (-44.0, -10.0, 'W Hwy 50'), (-48.0, -18.0, 'Serenity Ln'),
        (-42.0, -24.0, 'Palm Ct'), (-50.0, 6.0, 'Grove St'),
    )
    for x, z, label in west_houses:
        make_house(
            Entity, color, Text, scene_parent, x, z,
            w=rng.uniform(3.0, 3.8), h=rng.uniform(2.4, 3.0), d=rng.uniform(2.6, 3.4),
            roof_col=_rgb(color, rng.randint(40, 100), rng.randint(80, 140), rng.randint(100, 160)),
            label=label, porch=True, rng=rng,
        )
        n += 1
    # Strip plazas (flat roof ok for plazas; add A-frame kiosk)
    for x, z, name in ((-28.0, -8.0, 'Plaza Kiosk'), (10.0, -24.0, 'Lot Snacks'), (34.0, -32.0, 'Bait Shed')):
        Entity(model='cube', scale=(3.5, 2.2, 3.0), position=(x, 1.1, z),
               color=_rgb(color, rng.randint(80, 140), rng.randint(70, 120), rng.randint(90, 150)),
               texture=_t('stucco'), texture_scale=(2, 1.2), collider='box')
        _pitched_roof(Entity, color, x, 2.2, z, 3.9, 3.2, _rgb(color, 60, 50, 70))
        n += 1
        if Text and scene_parent is not None:
            Text(parent=scene_parent, text=name, position=(x, 3.4, z), origin=(0, 0),
                 billboard=True, color=_rgb(color, 255, 210, 255))
    make_street_sign(Entity, color, Text, scene_parent, 54.0, -16.0, 'E Hwy 50')
    make_street_sign(Entity, color, Text, scene_parent, -46.0, -14.0, 'W Hwy 50')
    make_billboard(Entity, color, Text, scene_parent, 58.0, -20.0, 'WALMART\nAHEAD', face_yaw=0)
    n += 3
    if isinstance(building_count_ref, list) and building_count_ref:
        building_count_ref[0] += n
    return n
