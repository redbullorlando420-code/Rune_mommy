"""Humanoid and car meshes."""
from __future__ import annotations
from models3d._base import _rgb

def make_humanoid(Entity, color, x, z, shirt, pants, skin=None, hitbox=False, detail='crowd', style=None):
    """torso + pelvis + head + upper/lower arms/legs + shoes. Named NPCs get more parts."""
    skin = skin or _rgb(color, 255, 206, 166)
    root = Entity(position=(x, 0, z))
    named = detail in ('named', 'michelle') or style == 'michelle'
    Entity(parent=root, model='cube', color=pants, scale=(0.40, 0.28, 0.26), y=0.42)
    leg_col = pants
    for sx in (-0.14, 0.14):
        Entity(parent=root, model='cube', color=leg_col, scale=(0.14, 0.32, 0.14), x=sx, y=0.22)
        Entity(parent=root, model='cube', color=leg_col.tint(-0.08) if hasattr(leg_col, 'tint') else leg_col,
               scale=(0.13, 0.30, 0.13), x=sx, y=0.05)
    shoe = _rgb(color, 240, 230, 210) if style == 'michelle' else _rgb(color, 30, 24, 28)
    for sx in (-0.14, 0.14):
        Entity(parent=root, model='cube', color=shoe, scale=(0.16, 0.08, 0.28), x=sx, y=0.04, z=0.04)

    if style == 'michelle':
        dress = shirt
        Entity(parent=root, model='cube', color=dress, scale=(0.52, 0.72, 0.34), y=0.95)
        Entity(parent=root, model='cube', color=dress.tint(0.05) if hasattr(dress, 'tint') else dress,
                       scale=(0.62, 0.38, 0.40), y=0.58)
        root.chest = Entity(parent=root, model='sphere', color=dress, scale=(0.55, 0.32, 0.38), y=1.12, z=-0.02)
        Entity(parent=root, model='sphere', color=_rgb(color, 255, 220, 170), scale=0.34, y=1.42)
        Entity(parent=root, model='sphere', color=_rgb(color, 245, 220, 120), scale=(0.38, 0.36, 0.36), y=1.48, z=-0.02)
        Entity(parent=root, model='cube', color=_rgb(color, 240, 210, 90), scale=(0.42, 0.12, 0.18), y=1.58, z=0.02)
    else:
        torso = Entity(parent=root, model='cube', color=shirt, scale=(0.50, 0.58, 0.32), y=0.88,
                       collider='box' if hitbox else None)
        root.chest = torso
        Entity(parent=root, model='sphere', color=skin, scale=0.32 if not named else 0.34, y=1.38)
        if named:
            Entity(parent=root, model='sphere', color=shirt.tint(-0.35) if hasattr(shirt, 'tint') else _rgb(color, 40, 30, 50),
                   scale=(0.34, 0.18, 0.34), y=1.52)

    for sx in (-0.34, 0.34):
        Entity(parent=root, model='cube', color=shirt, scale=(0.11, 0.28, 0.11), x=sx, y=1.05)
        Entity(parent=root, model='cube', color=skin, scale=(0.10, 0.26, 0.10), x=sx, y=0.78)
    if named:
        for sx in (-0.34, 0.34):
            Entity(parent=root, model='sphere', color=skin, scale=0.10, x=sx, y=0.62)

    if hitbox:
        Entity(parent=root, model='cube', scale=(0.55, 1.55, 0.42), y=0.85, collider='box', visible=False)
    return root


def make_car(Entity, color, pos, yaw, paint):
    """body + cabin + windshield + 4 wheels + headlights."""
    car = Entity(position=pos, rotation_y=yaw)
    car.speed = 0.0
    car.paint = paint
    car.base_paint = paint
    car.kind = 'car'
    car.fuel = 55.0
    car.damage = 0.0
    car.disabled = False
    car.smoke_cd = 0.0
    car.out_of_gas_toasted = False
    car.body = Entity(parent=car, model='cube', color=paint, scale=(1.70, 0.50, 3.40), y=0.55, collider='box')
    car.cabin = Entity(parent=car, model='cube', color=paint.tint(-0.18) if hasattr(paint, 'tint') else paint,
           scale=(1.50, 0.48, 1.55), y=1.05, z=-0.20)
    Entity(parent=car, model='cube', color=_rgb(color, 50, 90, 130), scale=(1.40, 0.32, 0.08), y=1.12, z=0.55)
    Entity(parent=car, model='cube', color=_rgb(color, 40, 70, 110), scale=(1.40, 0.28, 0.08), y=1.10, z=-0.95)
    for wx, wz in ((-0.88, 1.10), (0.88, 1.10), (-0.88, -1.10), (0.88, -1.10)):
        Entity(parent=car, model='cube', color=_rgb(color, 18, 18, 18),
               scale=(0.22, 0.36, 0.36), x=wx, y=0.22, z=wz)
    Entity(parent=car, model='cube', color=_rgb(color, 255, 240, 180), scale=(0.28, 0.12, 0.08), x=-0.45, y=0.55, z=1.72)
    Entity(parent=car, model='cube', color=_rgb(color, 255, 240, 180), scale=(0.28, 0.12, 0.08), x=0.45, y=0.55, z=1.72)
    Entity(parent=car, model='cube', color=_rgb(color, 220, 40, 40), scale=(0.28, 0.10, 0.06), x=-0.50, y=0.55, z=-1.72)
    Entity(parent=car, model='cube', color=_rgb(color, 220, 40, 40), scale=(0.28, 0.10, 0.06), x=0.50, y=0.55, z=-1.72)
    car.cam_pivot = Entity(parent=car, y=1.35, z=0.2)
    car.parked = getattr(car, 'parked', True)
    car.traffic = getattr(car, 'traffic', False)
    return car
