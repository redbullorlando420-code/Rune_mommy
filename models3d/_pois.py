from models3d._base import *

def make_poi_building(Entity, color, Text, scene_parent, kind, x, z):
    """Gas, motel, laundromat, starbucks kiosk, pharmacy, park benches. Returns (parts, interact_pos, label)."""
    n = 0
    label = kind
    interact = (x, 0, z - 2.2)
    label_y = 3.5
    if kind in ('gas', 'gas_hwy27'):
        if kind == 'gas_hwy27':
            label = 'Hwy 27 Fuel'
            canopy = _rgb(color, 40, 140, 90)
            pump_col = _rgb(color, 40, 90, 180)
        else:
            label = 'Hancock Gas'
            canopy = _rgb(color, 220, 180, 40)
            pump_col = _rgb(color, 200, 40, 40)
        Entity(model='cube', scale=(5.5, 2.4, 4.0), position=(x, 1.2, z), color=_rgb(color, 40, 50, 70),
               texture=_t('concrete') or _t('stucco'), texture_scale=(2, 1.5), collider='box')
        Entity(model='cube', scale=(7.0, 0.2, 5.5), position=(x, 2.8, z), color=canopy)
        Entity(model='cube', scale=(8.5, 0.05, 6.5), position=(x, 0.03, z - 1.5),
               color=_rgb(color, 36, 34, 38), texture=_t('asphalt'), texture_scale=(4, 3))
        n += 1
        for dx in (-1.6, 1.6):
            Entity(model='cube', scale=(0.55, 1.5, 0.55), position=(x + dx, 0.75, z - 2.8), color=pump_col, collider='box')
            Entity(model='cube', scale=(0.7, 0.15, 0.7), position=(x + dx, 1.55, z - 2.8), color=_rgb(color, 240, 220, 60))
            n += 2
        n += 2
        interact = (x, 0, z - 3.2)
    elif kind == 'motel':
        label = 'Palm Court Motel'
        Entity(model='cube', scale=(10.0, 2.6, 4.5), position=(x, 1.3, z), color=_rgb(color, 180, 140, 160),
               texture=_t('stucco'), texture_scale=(3, 1.5), collider='box')
        Entity(model='cube', scale=(10.4, 0.25, 4.9), position=(x, 2.75, z), color=_rgb(color, 90, 40, 80))
        for i in range(4):
            Entity(model='cube', scale=(0.7, 1.3, 0.08), position=(x - 3.5 + i * 2.3, 0.9, z - 2.3), color=_rgb(color, 60, 40, 50))
            Entity(model='cube', scale=(0.9, 0.7, 0.06), position=(x - 3.5 + i * 2.3 + 0.9, 1.3, z - 2.3), color=_rgb(color, 100, 180, 220))
            n += 2
        Entity(model='cube', scale=(2.2, 1.0, 0.12), position=(x, 3.4, z - 2.4), color=_rgb(color, 255, 80, 160))
        n += 3
        interact = (x, 0, z - 3.0)
    elif kind == 'laundromat':
        label = '50 Coin Laundry'
        Entity(model='cube', scale=(5.0, 2.5, 3.8), position=(x, 1.25, z), color=_rgb(color, 70, 90, 140),
               texture=_t('stucco') or _t('brick'), texture_scale=(2, 1.4), collider='box')
        Entity(model='cube', scale=(5.3, 0.18, 4.1), position=(x, 2.6, z), color=_rgb(color, 200, 210, 230))
        Entity(model='cube', scale=(3.2, 1.2, 0.08), position=(x, 1.4, z - 1.95), color=_rgb(color, 140, 200, 255))
        n += 3
    elif kind == 'starbucks':
        label = 'Green Siren Kiosk'
        Entity(model='cube', scale=(3.2, 2.2, 3.0), position=(x, 1.1, z), color=_rgb(color, 20, 80, 50), collider='box')
        Entity(model='cube', scale=(3.6, 0.2, 3.4), position=(x, 2.3, z), color=_rgb(color, 240, 240, 230))
        Entity(model='sphere', scale=0.9, position=(x, 2.7, z), color=_rgb(color, 40, 140, 70))
        Entity(model='cube', scale=(2.0, 0.9, 0.7), position=(x, 0.55, z - 1.7), color=_rgb(color, 180, 160, 120))
        n += 4
        interact = (x, 0, z - 2.4)
    elif kind == 'pharmacy':
        label = 'Clermont Rx'
        Entity(model='cube', scale=(5.5, 2.8, 4.2), position=(x, 1.4, z), color=_rgb(color, 240, 245, 250),
               texture=_t('stucco') or _t('concrete'), texture_scale=(2.2, 1.5), collider='box')
        Entity(model='cube', scale=(5.8, 0.2, 4.5), position=(x, 2.9, z), color=_rgb(color, 0, 120, 90))
        Entity(model='cube', scale=(1.2, 1.2, 0.1), position=(x - 1.5, 1.6, z - 2.15), color=_rgb(color, 0, 160, 120))
        Entity(model='cube', scale=(0.15, 1.0, 0.15), position=(x - 1.5, 1.6, z - 2.2), color=_rgb(color, 255, 255, 255))
        Entity(model='cube', scale=(1.0, 0.15, 0.15), position=(x - 1.5, 1.6, z - 2.2), color=_rgb(color, 255, 255, 255))
        n += 5
    elif kind == 'park':
        label = 'Willow Pocket Park'
        Entity(model='cube', scale=(10, 0.06, 8), position=(x, 0.04, z), color=_rgb(color, 30, 100, 50),
               texture=_t('grass'), texture_scale=(6, 5))
        for dx, dz in ((-2.5, -1.5), (2.0, 1.0), (-1.0, 2.0), (2.5, -2.0)):
            Entity(model='cube', scale=(1.4, 0.35, 0.45), position=(x + dx, 0.25, z + dz), color=_rgb(color, 90, 60, 40))
            Entity(model='cube', scale=(0.12, 0.55, 0.45), position=(x + dx - 0.65, 0.35, z + dz), color=_rgb(color, 70, 50, 30))
            Entity(model='cube', scale=(0.12, 0.55, 0.45), position=(x + dx + 0.65, 0.35, z + dz), color=_rgb(color, 70, 50, 30))
            n += 3
        Entity(model='cube', scale=(0.28, 2.4, 0.28), position=(x, 1.2, z), color=_rgb(color, 70, 42, 28))
        Entity(model='sphere', scale=2.0, position=(x, 2.8, z), color=_rgb(color, 30, 110, 55))
        n += 3
        interact = (x, 0, z - 2.0)
    elif kind == 'club27':
        label = 'Club 27'
        dark = _rgb(color, 18, 8, 28)
        neon = _rgb(color, 255, 40, 160)
        vip = _rgb(color, 120, 20, 60)
        Entity(model='cube', scale=(9.5, 3.4, 6.5), position=(x, 1.7, z), color=dark,
               texture=_t('stucco') or _t('brick'), texture_scale=(2.5, 1.8), collider='box')
        Entity(model='cube', scale=(9.9, 0.22, 6.9), position=(x, 3.5, z), color=_rgb(color, 40, 10, 50))
        Entity(model='cube', scale=(9.7, 0.12, 0.18), position=(x, 3.35, z - 3.3), color=neon)
        Entity(model='cube', scale=(4.2, 0.12, 2.0), position=(x, 2.55, z - 4.2), color=vip)
        Entity(model='cube', scale=(0.18, 1.6, 0.18), position=(x - 1.9, 1.7, z - 4.9), color=_rgb(color, 60, 20, 40))
        Entity(model='cube', scale=(0.18, 1.6, 0.18), position=(x + 1.9, 1.7, z - 4.9), color=_rgb(color, 60, 20, 40))
        Entity(model='cube', scale=(1.1, 2.0, 0.12), position=(x, 1.1, z - 3.3), color=_rgb(color, 30, 10, 40))
        Entity(model='cube', scale=(1.6, 1.0, 0.08), position=(x - 2.6, 1.8, z - 3.28), color=_rgb(color, 255, 60, 180))
        Entity(model='cube', scale=(1.6, 1.0, 0.08), position=(x + 2.6, 1.8, z - 3.28), color=_rgb(color, 255, 60, 180))
        Entity(model='cube', scale=(12.0, 0.05, 5.5), position=(x, 0.03, z - 6.2), color=_rgb(color, 28, 22, 34),
               texture=_t('asphalt'), texture_scale=(5, 2.5))
        Entity(model='cube', scale=(0.18, 4.0, 0.18), position=(x + 5.8, 2.0, z - 5.5), color=_rgb(color, 50, 40, 60), collider='box')
        Entity(model='cube', scale=(3.4, 1.6, 0.12), position=(x + 5.8, 3.5, z - 5.5), color=_rgb(color, 20, 6, 24))
        Entity(model='cube', scale=(3.1, 1.3, 0.05), position=(x + 5.8, 3.5, z - 5.58), color=neon)
        n += 13
        interact = (x, 0, z - 4.5)
        label_y = 4.6
    elif kind == 'quiet_spa':
        label = 'Quiet Spa'
        soft = _rgb(color, 210, 200, 190)
        bamboo = _rgb(color, 120, 95, 55)
        frost = _rgb(color, 180, 210, 220)
        Entity(model='cube', scale=(6.2, 2.6, 4.4), position=(x, 1.3, z), color=soft,
               texture=_t('stucco'), texture_scale=(2.2, 1.4), collider='box')
        Entity(model='cube', scale=(6.6, 0.18, 4.8), position=(x, 2.7, z), color=_rgb(color, 90, 120, 100))
        Entity(model='cube', scale=(8.0, 0.05, 4.0), position=(x, 0.03, z - 4.0),
               color=_rgb(color, 40, 38, 42), texture=_t('asphalt'), texture_scale=(4, 2))
        n += 1
        Entity(model='cube', scale=(4.0, 1.3, 0.08), position=(x, 1.5, z - 2.25), color=frost)
        Entity(model='cube', scale=(0.7, 1.7, 0.1), position=(x + 2.0, 0.95, z - 2.25), color=bamboo)
        for dx in (-2.6, -2.2, 2.2, 2.6):
            Entity(model='cube', scale=(0.14, 2.2, 0.14), position=(x + dx, 1.2, z - 2.1), color=bamboo)
            n += 1
        Entity(model='cube', scale=(1.8, 0.35, 0.12), position=(x - 0.4, 2.95, z - 2.3), color=_rgb(color, 40, 70, 55))
        n += 6
        interact = (x, 0, z - 2.8)
        label_y = 3.6
    elif kind == 'citrus_tower':
        label = 'Citrus Tower'
        orange = _rgb(color, 230, 110, 30)
        white = _rgb(color, 245, 245, 240)
        Entity(model='cube', scale=(5.5, 2.4, 5.5), position=(x, 1.2, z), color=_rgb(color, 240, 235, 220),
               texture=_t('stucco') or _t('concrete'), texture_scale=(2, 1.4), collider='box')
        Entity(model='cube', scale=(5.8, 0.2, 5.8), position=(x, 2.5, z), color=orange)
        h = 0.0
        for i, (rad, hh, col) in enumerate((
            (2.4, 4.0, orange),
            (2.1, 4.0, white),
            (1.85, 4.0, orange),
            (1.6, 3.5, white),
            (1.35, 3.0, orange),
        )):
            y0 = 2.5 + h + hh / 2
            try:
                Entity(model='cylinder', scale=(rad, hh, rad), position=(x, y0, z), color=col, collider='box' if i == 0 else None)
            except Exception:
                Entity(model='cube', scale=(rad * 1.6, hh, rad * 1.6), position=(x, y0, z), color=col, collider='box' if i == 0 else None)
            h += hh
            n += 1
        deck_y = 2.5 + h
        try:
            Entity(model='cylinder', scale=(2.6, 0.35, 2.6), position=(x, deck_y, z), color=_rgb(color, 200, 200, 210))
        except Exception:
            Entity(model='cube', scale=(4.2, 0.35, 4.2), position=(x, deck_y, z), color=_rgb(color, 200, 200, 210))
        Entity(model='cube', scale=(0.35, 1.2, 0.35), position=(x, deck_y + 0.9, z), color=white)
        n += 4
        interact = (x, 0, z - 3.5)
        label_y = deck_y + 2.2
    elif kind == 'waterfront':
        label = 'Lake Minneola'
        Entity(model='cube', scale=(14, 0.06, 10), position=(x, 0.04, z), color=_rgb(color, 34, 110, 50),
               texture=_t('grass'), texture_scale=(8, 6))
        Entity(model='cube', scale=(12, 0.08, 8), position=(x + 1.5, 0.02, z + 6.5), color=_rgb(color, 40, 120, 200),
               texture=_t('water'), texture_scale=(4, 3))
        Entity(model='cube', scale=(2.2, 0.35, 2.2), position=(x - 3.0, 0.25, z - 1.5), color=_rgb(color, 180, 220, 240))
        Entity(model='cube', scale=(0.25, 1.1, 0.25), position=(x - 3.0, 0.9, z - 1.5), color=_rgb(color, 100, 180, 230))
        for dx, dz in ((-5.0, -2.5), (0.5, -3.0), (4.0, -1.5)):
            Entity(model='cube', scale=(1.5, 0.35, 0.45), position=(x + dx, 0.25, z + dz), color=_rgb(color, 90, 60, 40))
            Entity(model='cube', scale=(0.12, 0.55, 0.45), position=(x + dx - 0.7, 0.35, z + dz), color=_rgb(color, 70, 50, 30))
            Entity(model='cube', scale=(0.12, 0.55, 0.45), position=(x + dx + 0.7, 0.35, z + dz), color=_rgb(color, 70, 50, 30))
            n += 3
        n += 4
        interact = (x, 0, z - 2.5)
        label_y = 3.2
    elif kind == 'showcase_citrus':
        label = 'Showcase of Citrus'
        Entity(model='cube', scale=(4.5, 2.2, 3.2), position=(x, 1.1, z), color=_rgb(color, 250, 240, 220),
               texture=_t('stucco'), texture_scale=(2, 1.3), collider='box')
        Entity(model='cube', scale=(4.9, 0.15, 3.6), position=(x, 2.3, z), color=_rgb(color, 230, 100, 30))
        Entity(model='cube', scale=(3.2, 0.9, 1.0), position=(x, 0.55, z - 1.9), color=_rgb(color, 160, 90, 40))
        for dx in (-1.0, 0.0, 1.0):
            Entity(model='sphere', scale=0.45, position=(x + dx, 1.15, z - 1.7), color=_rgb(color, 240, 120, 30))
            n += 1
        n += 3
        interact = (x, 0, z - 2.6)
        label_y = 3.4
    elif kind == 'presidents_hall':
        label = "Presidents Hall"
        Entity(model='cube', scale=(5.0, 2.0, 3.0), position=(x, 1.0, z), color=_rgb(color, 120, 100, 80),
               texture=_t('brick') or _t('stucco'), texture_scale=(2.2, 1.3), collider='box')
        Entity(model='cube', scale=(5.4, 0.2, 3.4), position=(x, 2.15, z), color=_rgb(color, 90, 70, 55))
        for i, dx in enumerate((-1.5, -0.5, 0.5, 1.5)):
            Entity(model='cube', scale=(0.7, 1.1, 0.55), position=(x + dx, 2.9, z - 0.2), color=_rgb(color, 200 - i * 8, 190 - i * 6, 170))
            n += 1
        n += 2
        interact = (x, 0, z - 2.4)
        label_y = 4.2
    else:
        Entity(model='cube', scale=(4, 2.5, 3.5), position=(x, 1.25, z), color=_rgb(color, 80, 50, 90), collider='box')
        n += 1
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=label, position=(x, label_y, z), origin=(0, 0),
                 billboard=True, color=_rgb(color, 255, 220, 255))
        try:
            t.world_scale = 1.35
        except Exception:
            pass
    return n, interact, label
