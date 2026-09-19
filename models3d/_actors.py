"""Humanoid and car meshes — procedural multi-part Ursina primitives."""
from __future__ import annotations

from models3d._base import _rgb


def _tint(col, amount):
    if hasattr(col, 'tint'):
        try:
            return col.tint(amount)
        except Exception:
            pass
    return col



def _mesh(preferred='sphere'):
    """Ursina mesh name; fall back to cube if sphere/cylinder missing."""
    return preferred  # resolved at Entity create time via _entity


def _entity(Entity, *, model='cube', **kw):
    """Create Entity; if model fails (missing sphere), retry as cube."""
    try:
        return Entity(model=model, **kw)
    except Exception:
        if model != 'cube':
            try:
                return Entity(model='cube', **kw)
            except Exception:
                pass
        raise

def _hair_from_shirt(color, shirt, style, detail):
    """Pick a readable hair color from style / shirt."""
    if style == 'michelle':
        return _rgb(color, 236, 198, 92)
    if style == 'player':
        return _rgb(color, 52, 38, 28)
    if detail in ('named', 'michelle'):
        # darker relative to shirt so named NPCs read as having hair
        return _tint(shirt, -0.42) if shirt is not None else _rgb(color, 40, 30, 50)
    # crowd: muted from shirt
    return _tint(shirt, -0.55) if shirt is not None else _rgb(color, 55, 45, 50)


def attach_humanoid_parts(
    Entity, color, parent, shirt, pants, skin=None,
    hitbox=False, detail='crowd', style=None,
):
    """Attach a multi-part humanoid under `parent`. Overall height ~1.65–1.72.

    Styles:
      michelle — teal dress + sandals + blonde hair + body silhouette
      player   — casual tee + jeans + sneakers (Alec)
      (else)   — shirt/pants; named gets more hair/hands detail
    """
    skin = skin or _rgb(color, 255, 206, 166)
    named = detail in ('named', 'michelle', 'player') or style in ('michelle', 'player')
    fancy = named or style == 'michelle'
    michelle = style == 'michelle'
    player = style == 'player'
    hair = _hair_from_shirt(color, shirt, style, detail)

    # --- proportions (meters-ish Ursina units) ---
    # Keep crown near y=1.55 and feet on ground so talk ranges / cam stay valid.
    hip_w = 0.46 if michelle else (0.40 if player else 0.42)
    shoulder_w = 0.48 if michelle else (0.54 if player else 0.50)
    torso_d = 0.30 if michelle else 0.28
    leg_gap = 0.13 if michelle else 0.12

    # Hips / pelvis
    if michelle:
        # under-dress hips (skin tone peek + dress sits on top)
        Entity(parent=parent, model='cube', color=skin,
               scale=(hip_w * 0.92, 0.18, 0.24), y=0.78)
    else:
        Entity(parent=parent, model='cube', color=pants,
               scale=(hip_w, 0.22, 0.26), y=0.78)

    # Upper + lower legs
    if michelle:
        # bare legs under dress hem
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=skin,
                   scale=(0.12, 0.34, 0.12), x=sx, y=0.52)
            Entity(parent=parent, model='cube', color=_tint(skin, -0.05),
                   scale=(0.11, 0.32, 0.11), x=sx, y=0.22)
    else:
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=pants,
                   scale=(0.13, 0.34, 0.13), x=sx, y=0.52)
            Entity(parent=parent, model='cube', color=_tint(pants, -0.08),
                   scale=(0.12, 0.32, 0.12), x=sx, y=0.22)

    # Feet — sandals (Michelle) / sneakers (player) / dark shoes (crowd)
    if michelle:
        shoe = _rgb(color, 245, 232, 210)
        strap = _rgb(color, 46, 196, 182)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=shoe,
                   scale=(0.15, 0.05, 0.30), x=sx, y=0.04, z=0.05)
            Entity(parent=parent, model='cube', color=strap,
                   scale=(0.14, 0.03, 0.06), x=sx, y=0.08, z=0.02)
    elif player:
        shoe = _rgb(color, 28, 32, 40)
        sole = _rgb(color, 220, 220, 230)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=shoe,
                   scale=(0.15, 0.08, 0.28), x=sx, y=0.05, z=0.04)
            Entity(parent=parent, model='cube', color=sole,
                   scale=(0.15, 0.03, 0.28), x=sx, y=0.02, z=0.04)
    else:
        shoe = _rgb(color, 30, 24, 28)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=shoe,
                   scale=(0.14, 0.07, 0.26), x=sx, y=0.04, z=0.03)

    # --- torso / clothing ---
    if michelle:
        dress = shirt
        # fitted bodice
        Entity(parent=parent, model='cube', color=dress,
               scale=(0.46, 0.42, torso_d), y=1.12)
        # waist cinch
        Entity(parent=parent, model='cube', color=_tint(dress, -0.08),
               scale=(0.40, 0.10, torso_d * 0.95), y=0.92)
        # skirt flare (A-line)
        Entity(parent=parent, model='cube', color=_tint(dress, 0.04),
               scale=(0.58, 0.36, 0.36), y=0.70)
        Entity(parent=parent, model='cube', color=_tint(dress, 0.08),
               scale=(0.66, 0.14, 0.40), y=0.54)
        # body shape (existing NSFW tone — improve fidelity, don't strip)
        parent.chest = Entity(
            parent=parent, model='sphere', color=dress,
            scale=(0.50, 0.28, 0.34), y=1.20, z=-0.04,
        )
        Entity(parent=parent, model='sphere', color=_tint(dress, 0.06),
               scale=(0.20, 0.18, 0.18), x=-0.12, y=1.22, z=-0.10)
        Entity(parent=parent, model='sphere', color=_tint(dress, 0.06),
               scale=(0.20, 0.18, 0.18), x=0.12, y=1.22, z=-0.10)
        # soft neckline / collarbone
        Entity(parent=parent, model='cube', color=skin,
               scale=(0.28, 0.08, 0.16), y=1.34, z=0.02)
    else:
        # shirt torso
        torso = Entity(
            parent=parent, model='cube', color=shirt,
            scale=(shoulder_w * 0.92, 0.48, torso_d), y=1.10,
            collider='box' if hitbox and not fancy else None,
        )
        parent.chest = torso
        # slight belly / lower shirt tuck into pants
        Entity(parent=parent, model='cube', color=_tint(shirt, -0.06),
               scale=(hip_w * 0.95, 0.14, torso_d * 0.95), y=0.88)
        if player:
            # casual tee hem + collar strip
            Entity(parent=parent, model='cube', color=_tint(shirt, 0.10),
                   scale=(0.22, 0.05, 0.18), y=1.34, z=0.02)
            Entity(parent=parent, model='cube', color=_rgb(color, 24, 28, 36),
                   scale=(hip_w * 0.88, 0.06, 0.22), y=0.86)  # belt
        if fancy:
            # soft chest volume for named (non-michelle) female-coded shirts stay modest;
            # male / player get shoulder pads via extra cubes
            Entity(parent=parent, model='cube', color=_tint(shirt, -0.05),
                   scale=(shoulder_w, 0.10, torso_d + 0.02), y=1.30)

    # Neck
    Entity(parent=parent, model='cube', color=skin,
           scale=(0.12, 0.10, 0.12), y=1.38)

    # Head
    head_y = 1.52
    head_s = 0.34 if fancy else 0.30
    head_col = _rgb(color, 255, 220, 170) if michelle else skin
    Entity(parent=parent, model='sphere', color=head_col, scale=head_s, y=head_y)

    # Ears (named / michelle / player — silhouette cue)
    if fancy:
        ear = _tint(head_col, -0.04)
        Entity(parent=parent, model='sphere', color=ear, scale=0.08, x=-0.18, y=head_y)
        Entity(parent=parent, model='sphere', color=ear, scale=0.08, x=0.18, y=head_y)

    # Hair / silhouette — never a bare cube head
    if michelle:
        # blonde volume + bangs + side fall
        Entity(parent=parent, model='sphere', color=hair,
               scale=(0.40, 0.34, 0.38), y=head_y + 0.06, z=-0.02)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.05),
               scale=(0.44, 0.10, 0.20), y=head_y + 0.14, z=0.06)  # bangs
        Entity(parent=parent, model='cube', color=_tint(hair, -0.08),
               scale=(0.16, 0.28, 0.12), x=-0.20, y=head_y - 0.02, z=-0.06)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.08),
               scale=(0.16, 0.28, 0.12), x=0.20, y=head_y - 0.02, z=-0.06)
        # short ponytail / back fall
        Entity(parent=parent, model='sphere', color=_tint(hair, -0.10),
               scale=(0.22, 0.28, 0.18), y=head_y - 0.06, z=-0.18)
    elif player:
        # short dark crop
        Entity(parent=parent, model='sphere', color=hair,
               scale=(0.36, 0.20, 0.36), y=head_y + 0.10)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.08),
               scale=(0.34, 0.08, 0.16), y=head_y + 0.14, z=0.08)
    elif named:
        Entity(parent=parent, model='sphere', color=hair,
               scale=(0.36, 0.20, 0.36), y=head_y + 0.10)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.10),
               scale=(0.32, 0.10, 0.14), y=head_y + 0.12, z=0.06)
    else:
        # crowd: simple hair cap so heads aren't bare
        Entity(parent=parent, model='sphere', color=hair,
               scale=(0.32, 0.14, 0.32), y=head_y + 0.08)

    # Shoulders + upper / lower arms + hands
    arm_x = shoulder_w * 0.58
    sleeve = dress if michelle else shirt
    for sx in (-arm_x, arm_x):
        # shoulder
        Entity(parent=parent, model='sphere', color=sleeve,
               scale=0.14 if fancy else 0.12, x=sx * 0.92, y=1.28)
        # upper arm (sleeve)
        Entity(parent=parent, model='cube', color=sleeve,
               scale=(0.11, 0.26, 0.11), x=sx, y=1.12)
        # lower arm (skin — short sleeves / dress)
        Entity(parent=parent, model='cube', color=skin,
               scale=(0.10, 0.26, 0.10), x=sx, y=0.88)
        if fancy:
            Entity(parent=parent, model='sphere', color=skin,
                   scale=0.09, x=sx, y=0.72)
        elif detail == 'crowd':
            # tiny hand nub so crowd isn't stump-armed
            Entity(parent=parent, model='cube', color=skin,
                   scale=(0.08, 0.08, 0.08), x=sx, y=0.72)

    # Invisible full-body collider (keeps E-talk / combat ranges stable)
    if hitbox:
        ghost = Entity(
            parent=parent, model='cube',
            scale=(0.55, 1.60, 0.42), y=0.85,
            collider='box', visible=False,
        )
        try:
            ghost.hitbox_ghost = True
        except Exception:
            pass

    parent.humanoid_style = style or detail
    return parent


def make_humanoid(Entity, color, x, z, shirt, pants, skin=None, hitbox=False, detail='crowd', style=None):
    """Root entity at (x,0,z) with multi-part body. Named / Michelle get more parts."""
    root = Entity(position=(x, 0, z))
    try:
        attach_humanoid_parts(
            Entity, color, root, shirt, pants, skin=skin,
            hitbox=hitbox, detail=detail, style=style,
        )
    except Exception as exc:
        # Sphere/mesh failure — fall back to cube-only silhouette so NPCs still spawn
        print('  humanoid parts fallback:', exc)
        try:
            for ch in list(getattr(root, 'children', []) or []):
                try:
                    ch.disable()
                except Exception:
                    pass
        except Exception:
            pass
        body = Entity(parent=root, model='cube', color=shirt, scale=(0.45, 0.7, 0.28), y=1.05)
        Entity(parent=root, model='cube', color=pants or shirt, scale=(0.4, 0.55, 0.25), y=0.45)
        Entity(parent=root, model='cube', color=skin or shirt, scale=(0.32, 0.32, 0.32), y=1.55)
        root.chest = body
        if hitbox:
            ghost = Entity(parent=root, model='cube', scale=(0.55, 1.60, 0.42), y=0.85, collider='box', visible=False)
            try:
                ghost.hitbox_ghost = True
            except Exception:
                pass
        root.humanoid_style = style or detail
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
    car.cabin = Entity(
        parent=car, model='cube',
        color=_tint(paint, -0.18),
        scale=(1.50, 0.48, 1.55), y=1.05, z=-0.20,
    )
    # Distinct roof slab so vehicles read as cars (not open convertibles)
    car.roof = Entity(
        parent=car, model='cube',
        color=_tint(paint, -0.30),
        scale=(1.52, 0.10, 1.48), y=1.34, z=-0.18,
    )
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
