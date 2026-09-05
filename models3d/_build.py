from models3d._base import *

def make_house(Entity, color, Text, scene_parent, x, z, *, w=3.6, h=2.8, d=3.2, body_col=None,
               roof_col=None, label=None, porch=True, garage=False, rng=None):
    """Multi-part house: base, pitched roof, windows, door recess, porch, AC."""
    rng = rng or random.Random(int(abs(x * 10 + z)))
    body_col = body_col or _rgb(color, rng.randint(180, 235), rng.randint(160, 210), rng.randint(150, 200))
    roof_col = roof_col or _rgb(color, rng.randint(40, 90), rng.randint(100, 180), rng.randint(120, 190))
    wood = _rgb(color, 90, 55, 40)
    n = 0
    # base (stucco/brick texture + tint so walls are not blank)
    wall_tex = _t('stucco') or _t('brick')
    Entity(model='cube', scale=(w, h, d), position=(x, h / 2, z), color=body_col,
           texture=wall_tex, texture_scale=(2.2, 1.6), collider='box')
    n += 1
    # pitched roof
    _pitched_roof(Entity, color, x, h + 0.15, z, w + 0.4, d + 0.2, roof_col)
    n += 3
    # windows (front)
    win = _rgb(color, 120, 200, 230)
    Entity(model='cube', scale=(0.55, 0.55, 0.06), position=(x - w * 0.22, h * 0.55, z - d / 2 - 0.02), color=win)
    Entity(model='cube', scale=(0.55, 0.55, 0.06), position=(x + w * 0.22, h * 0.55, z - d / 2 - 0.02), color=win)
    n += 2
    # door recess
    Entity(model='cube', scale=(0.70, 1.35, 0.12), position=(x, 0.72, z - d / 2 - 0.04), color=wood)
    Entity(model='cube', scale=(0.55, 1.15, 0.08), position=(x, 0.68, z - d / 2 - 0.10), color=_rgb(color, 60, 40, 30))
    n += 2
    if porch:
        Entity(model='cube', scale=(w * 0.7, 0.12, 1.1), position=(x, 0.08, z - d / 2 - 0.7),
               color=_rgb(color, 160, 140, 110), texture=_t('concrete'), texture_scale=(2, 1))
        Entity(model='cube', scale=(0.12, 1.4, 0.12), position=(x - w * 0.28, 0.75, z - d / 2 - 1.1), color=wood)
        Entity(model='cube', scale=(0.12, 1.4, 0.12), position=(x + w * 0.28, 0.75, z - d / 2 - 1.1), color=wood)
        Entity(model='cube', scale=(w * 0.65, 0.08, 1.2), position=(x, 1.45, z - d / 2 - 0.7), color=roof_col)
        n += 4
    # AC unit
    Entity(model='cube', scale=(0.55, 0.45, 0.45), position=(x + w / 2 + 0.35, 0.35, z + 0.4), color=_rgb(color, 70, 78, 90))
    n += 1
    if garage:
        Entity(model='cube', scale=(w * 0.7, h * 0.75, d * 0.7), position=(x + w * 0.55, h * 0.38, z + 0.2),
               color=body_col.tint(-0.08) if hasattr(body_col, 'tint') else body_col,
               texture=wall_tex, texture_scale=(1.6, 1.2), collider='box')
        Entity(model='cube', scale=(w * 0.55, h * 0.55, 0.1), position=(x + w * 0.55, h * 0.35, z - d * 0.35),
               color=_rgb(color, 55, 60, 70))
        n += 2
    if label and Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=label, position=(x, h + 1.1, z), origin=(0, 0),
                 billboard=True, color=_rgb(color, 255, 210, 255))
        try:
            t.world_scale = 1.2
        except Exception:
            pass
    return n



def make_shop_stall(Entity, color, Text, scene_parent, x, z, w, d, h, body_col, neon, trim, name, is_gun=False):
    """Strip-mall / shake stall with neon trim, awning, counter."""
    n = 0
    stall_tex = _t('stucco') or _t('brick')
    Entity(model='cube', scale=(w, h, d), position=(x, h / 2, z), color=body_col,
           texture=stall_tex, texture_scale=(2.0, 1.4), collider='box')
    n += 1
    # flat roof + neon edge
    Entity(model='cube', scale=(w + 0.55, 0.14, d + 0.4), position=(x, h + 0.1, z), color=neon)
    n += 1
    # awning
    Entity(model='cube', scale=(w + 0.2, 0.08, 0.85), position=(x, h * 0.72, z - d / 2 - 0.4), color=trim)
    n += 1
    # window strip
    Entity(model='cube', scale=(w * 0.7, 0.7, 0.06), position=(x, h * 0.55, z - d / 2 - 0.02), color=_rgb(color, 80, 180, 220))
    n += 1
    # door
    Entity(model='cube', scale=(0.7, 1.4, 0.1), position=(x + w * 0.28, 0.75, z - d / 2 - 0.05), color=_rgb(color, 40, 30, 50))
    n += 1
    # counter
    Entity(model='cube', scale=(w * 0.7, 0.7, 0.45), position=(x, 0.45, z - d / 2 - 0.25), color=trim.tint(-0.3) if hasattr(trim, 'tint') else trim)
    n += 1
    if is_gun:
        Entity(model='cube', scale=(1.4, 0.9, 1.1), position=(x + 2.6, 0.45, z - 1.4), color=_rgb(color, 90, 70, 40), collider='box')
        Entity(model='cube', scale=(0.35, 1.4, 0.12), position=(x - 1.4, 1.6, z - 1.9), color=_rgb(color, 196, 90, 24))
        n += 2
    if Text and scene_parent is not None:
        label = Text(parent=scene_parent, text=name, position=(x, (3.35 if is_gun else h + 0.85), z),
                      origin=(0, 0), billboard=True,
                      color=_rgb(color, 255, 180, 90) if is_gun else _rgb(color, 255, 210, 255))
        try:
            label.world_scale = 1.8 if is_gun else 1.45
        except Exception:
            pass
    return n



def make_billboard(Entity, color, Text, scene_parent, x, z, text, face_yaw=0):
    Entity(model='cube', scale=(0.18, 4.2, 0.18), position=(x, 2.1, z), color=_rgb(color, 50, 40, 60), collider='box')
    Entity(model='cube', scale=(3.6, 1.8, 0.12), position=(x, 3.6, z), color=_rgb(color, 20, 8, 28), rotation_y=face_yaw)
    Entity(model='cube', scale=(3.4, 1.5, 0.04), position=(x, 3.6, z - 0.08), color=_rgb(color, 255, 60, 180), rotation_y=face_yaw)
    if Text and scene_parent is not None:
        t = Text(parent=scene_parent, text=text, position=(x, 3.6, z - 0.2), origin=(0, 0),
                 billboard=True, color=_rgb(color, 255, 240, 255))
        try:
            t.world_scale = 1.5
        except Exception:
            pass
    return 3



def make_street_sign(Entity, color, Text, scene_parent, x, z, text):
    Entity(model='cube', scale=(0.1, 2.4, 0.1), position=(x, 1.2, z), color=_rgb(color, 60, 60, 70))
    Entity(model='cube', scale=(1.8, 0.55, 0.08), position=(x, 2.35, z), color=_rgb(color, 40, 120, 80))
    if Text and scene_parent is not None:
        Text(parent=scene_parent, text=text, position=(x, 2.5, z), origin=(0, 0),
             billboard=True, color=_rgb(color, 240, 255, 240))
    return 2



