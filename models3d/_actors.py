"""Humanoid and car meshes."""
from __future__ import annotations

from models3d._base import _rgb, round_cylinder, round_head

_HERO_FABRIC = 'assets/textures/hero_fabric_v1.png'


def make_humanoid(Entity, color, x, z, shirt, pants, skin=None, hitbox=False, detail='crowd', style=None, parent=None):
    """Tiered humanoid: dense rounded hero/named meshes, economical crowd meshes."""
    skin = skin or _rgb(color, 255, 206, 166)
    root = Entity(parent=parent, position=(x, 0, z))
    named = detail in ('named', 'michelle', 'hero') or style in ('michelle', 'hero')
    hero = detail == 'hero' or style == 'hero'
    if hero:
        # Authored faces point forward into the world; the third-person camera
        # follows behind, so the player sees a back rather than a face.
        root.rotation_y = 180
    hero_texture = _HERO_FABRIC if hero else None
    limb_model = round_cylinder(14) if named and not hero else 'cube'
    head_model = round_head(24, 16) if named else 'sphere'
    # pelvis / lower torso
    Entity(parent=root, model='cube', color=pants, scale=(0.40, 0.28, 0.26), y=0.42)
    # upper / lower legs
    leg_col = pants
    for sx in (-0.14, 0.14):
        Entity(parent=root, model=limb_model, color=leg_col, scale=(0.14, 0.32, 0.14), x=sx, y=0.22)
        Entity(parent=root, model=limb_model, color=leg_col.tint(-0.08) if hasattr(leg_col, 'tint') else leg_col,
               scale=(0.13, 0.30, 0.13), x=sx, y=0.05)
    # shoes / sandals
    shoe = _rgb(color, 240, 230, 210) if style == 'michelle' else _rgb(color, 30, 24, 28)
    for sx in (-0.14, 0.14):
        Entity(parent=root, model='cube', color=shoe, scale=(0.16, 0.08, 0.28), x=sx, y=0.04, z=0.04)

    if style == 'michelle':
        # teal dress silhouette (longer torso, skirt flare)
        dress = shirt
        Entity(parent=root, model='cube', color=dress, scale=(0.52, 0.72, 0.34), y=0.95)
        skirt = Entity(parent=root, model='cube', color=dress.tint(0.05) if hasattr(dress, 'tint') else dress,
                       scale=(0.62, 0.38, 0.40), y=0.58)
        root.chest = Entity(parent=root, model='sphere', color=dress, scale=(0.55, 0.32, 0.38), y=1.12, z=-0.02)
        # blonde head
        head = Entity(parent=root, model=head_model, color=_rgb(color, 255, 220, 170), scale=(0.38, 0.44, 0.37), y=1.42)
        Entity(parent=root, model=head_model, color=_rgb(color, 245, 220, 120), scale=(0.42, 0.22, 0.40), y=1.56, z=-0.02)
        Entity(parent=root, model='cube', color=_rgb(color, 240, 210, 90), scale=(0.42, 0.12, 0.18), y=1.58, z=0.02)  # bangs
    else:
        torso = Entity(parent=root, model='cube', color=shirt,
                       texture=hero_texture, texture_scale=(1.2, 1.8), scale=(0.44, 0.62, 0.28), y=0.88,
                       collider='box' if hitbox else None)
        root.chest = torso
        if named:
            # Physical neck bridges the torso and head so the higher-detail
            # player cannot read as disconnected floating shapes.
            Entity(parent=root, model='cube', color=skin,
                   scale=(0.13, 0.16, 0.13), y=1.22)
        head = Entity(parent=root, model=head_model, color=skin,
                      scale=(0.38, 0.44, 0.37) if named else 0.32, y=1.38)
        if named:
            # hair cap
            hair = shirt.tint(-0.35) if hasattr(shirt, 'tint') else _rgb(color, 40, 30, 50)
            Entity(parent=root, model='sphere', color=hair, scale=(0.42, 0.22, 0.40), y=1.53)
            if hero:
                # Small sculpted face details make the hero read as a person
                # at normal third-person distance rather than a blank sphere.
                eye_col = _rgb(color, 48, 78, 92)
                for sx in (-0.10, 0.10):
                    Entity(parent=root, model='sphere', color=eye_col, scale=0.045, x=sx, y=1.42, z=-0.185)
                Entity(parent=root, model='sphere', color=skin.tint(-0.06) if hasattr(skin, 'tint') else skin,
                       scale=(0.06, 0.08, 0.06), y=1.35, z=-0.20)
                Entity(parent=root, model='cube', color=_rgb(color, 160, 84, 96), scale=(0.13, 0.025, 0.02), y=1.27, z=-0.19)

    # upper / lower arms
    for sx in (-0.34, 0.34):
        Entity(parent=root, model=limb_model, color=shirt, scale=(0.11, 0.28, 0.11), x=sx, y=1.05)
        Entity(parent=root, model=limb_model, color=skin, scale=(0.10, 0.26, 0.10), x=sx, y=0.78)
    if named:
        # hands
        for sx in (-0.34, 0.34):
            Entity(parent=root, model=head_model, color=skin, scale=0.11, x=sx, y=0.62)

    if hitbox:
        Entity(parent=root, model='cube', scale=(0.55, 1.55, 0.42), y=0.85, collider='box', visible=False)
    return root


def make_car(Entity, color, pos, yaw, paint):
    """Rounded car visuals over an economical collision shell."""
    car = Entity(position=pos, rotation_y=yaw)
    car.speed = 0.0
    car.paint = paint
    car.base_paint = paint
    car.kind = 'car'
    car.fuel = 55.0
    car.damage = 0.0
    car.max_damage = 240.0
    car.model_name = 'Model 3-inspired electric sedan'
    car.disabled = False
    car.smoke_cd = 0.0
    car.out_of_gas_toasted = False
    # One simple collider, with a layered sedan silhouette over it.
    car.body = Entity(parent=car, model='cube', color=paint, scale=(1.72, 0.46, 3.42), y=0.52, collider='box')
    Entity(parent=car, model='cube', color=paint.tint(0.05) if hasattr(paint, 'tint') else paint, scale=(1.68, 0.34, 1.15), y=0.76, z=0.95)  # hood
    Entity(parent=car, model='cube', color=paint.tint(-0.08) if hasattr(paint, 'tint') else paint, scale=(1.64, 0.30, 0.82), y=0.72, z=-1.28)  # trunk
    # Cabin stays addressable for damage tint but is no longer a featureless blob.
    # Curved glass canopy gives the local sedan a restrained Model-3-inspired
    # profile without using Tesla branding or external model files.
    car.cabin = Entity(parent=car, model=round_head(20, 12), color=paint.tint(-0.18) if hasattr(paint, 'tint') else paint,
           scale=(1.38, 0.58, 1.55), y=1.07, z=-0.12)
    glass = _rgb(color, 50, 90, 130)
    Entity(parent=car, model='cube', color=glass, scale=(1.22, 0.29, 0.06), y=1.14, z=0.66)
    Entity(parent=car, model='cube', color=_rgb(color, 40, 70, 110), scale=(1.22, 0.26, 0.06), y=1.12, z=-0.86)
    for sx in (-0.72, 0.72):
        Entity(parent=car, model='cube', color=glass, scale=(0.06, 0.30, 1.20), x=sx, y=1.13, z=-0.10)
        Entity(parent=car, model='cube', color=_rgb(color, 22, 22, 28), scale=(0.08, 0.08, 0.35), x=sx * 1.02, y=0.70, z=0.1)  # door handle
    Entity(parent=car, model='cube', color=_rgb(color, 28, 30, 34), scale=(1.82, 0.12, 0.16), y=0.46, z=1.74)
    Entity(parent=car, model='cube', color=_rgb(color, 28, 30, 34), scale=(1.82, 0.12, 0.16), y=0.46, z=-1.74)
    Entity(parent=car, model='cube', color=_rgb(color, 230, 242, 255), scale=(1.10, 0.09, 0.05), y=0.62, z=1.75)  # full-width LED
    # Reused project-local wheels; no missing named-cylinder dependency.
    for wx, wz in ((-0.88, 1.10), (0.88, 1.10), (-0.88, -1.10), (0.88, -1.10)):
        wheel = Entity(parent=car, model=round_cylinder(16), color=_rgb(color, 18, 18, 18),
                       scale=(0.42, 0.18, 0.42), x=wx, y=0.28, z=wz, rotation_z=90)
        Entity(parent=wheel, model=round_cylinder(12), color=_rgb(color, 125, 135, 150),
               scale=(0.23, 1.04, 0.23), rotation_z=90)
    # headlights + taillights
    Entity(parent=car, model='cube', color=_rgb(color, 255, 240, 180), scale=(0.28, 0.12, 0.08), x=-0.45, y=0.55, z=1.72)
    Entity(parent=car, model='cube', color=_rgb(color, 255, 240, 180), scale=(0.28, 0.12, 0.08), x=0.45, y=0.55, z=1.72)
    Entity(parent=car, model='cube', color=_rgb(color, 220, 40, 40), scale=(0.28, 0.10, 0.06), x=-0.50, y=0.55, z=-1.72)
    Entity(parent=car, model='cube', color=_rgb(color, 220, 40, 40), scale=(0.28, 0.10, 0.06), x=0.50, y=0.55, z=-1.72)
    car.cam_pivot = Entity(parent=car, y=1.35, z=0.2)
    car.parked = getattr(car, 'parked', True)
    car.traffic = getattr(car, 'traffic', False)
    return car
