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



def clear_humanoid_parts(parent):
    """Remove mesh children so outfit variants can re-attach (hitbox ghost preserved if re-added)."""
    try:
        for ch in list(getattr(parent, 'children', []) or []):
            try:
                ch.disable()
            except Exception:
                pass
            try:
                from ursina import destroy
                destroy(ch)
            except Exception:
                try:
                    ch.enabled = False
                    ch.visible = False
                    ch.parent = None
                except Exception:
                    pass
    except Exception:
        pass
    for attr in ('chest', 'humanoid_style'):
        try:
            if attr == 'chest':
                parent.chest = None
        except Exception:
            pass


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
    # Adult feminine anime styles ONLY — never underage proportions.
    michelle = style in ('michelle', 'michelle_nude')
    michelle_nude = style == 'michelle_nude'
    anime_f = style == 'anime_f' or detail == 'anime_f'
    player = style == 'player'
    named = detail in ('named', 'michelle', 'player', 'anime_f') or style in (
        'michelle', 'michelle_nude', 'player', 'anime_f')
    feminine = michelle or anime_f or (named and not player and style != 'male')
    fancy = feminine or named or michelle
    hair = _hair_from_shirt(color, shirt, 'michelle' if michelle else style, detail)

    # --- proportions (adult) ---
    # Keep crown near y=1.55. Feminine: hourglass, longer legs read, never childlike.
    if michelle:
        hip_w, shoulder_w, torso_d, leg_gap = 0.64, 0.42, 0.38, 0.15
    elif anime_f or (feminine and not player):
        hip_w, shoulder_w, torso_d, leg_gap = 0.56, 0.44, 0.34, 0.14
    elif named and not player:
        hip_w, shoulder_w, torso_d, leg_gap = 0.48, 0.50, 0.30, 0.12
    elif player:
        hip_w, shoulder_w, torso_d, leg_gap = 0.40, 0.54, 0.30, 0.12
    else:
        hip_w, shoulder_w, torso_d, leg_gap = 0.42, 0.50, 0.28, 0.12

    # Hips / pelvis
    if michelle:
        Entity(parent=parent, model='cube', color=skin,
               scale=(hip_w * 0.92, 0.18, 0.24), y=0.78)
    elif anime_f:
        Entity(parent=parent, model='cube', color=skin,
               scale=(hip_w * 0.95, 0.18, 0.26), y=0.78)
        Entity(parent=parent, model='cube', color=_tint(shirt, -0.15),
               scale=(hip_w * 0.7, 0.08, 0.22), y=0.86)  # panty line under skirt
    else:
        Entity(parent=parent, model='cube', color=pants,
               scale=(hip_w, 0.22, 0.26), y=0.78)
        Entity(parent=parent, model='cube', color=_tint(pants, -0.25),
               scale=(hip_w * 1.02, 0.05, 0.27), y=0.88)

    # Upper + lower legs
    if michelle:
        # bare toned legs under dress hem (thicker thigh read)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=skin,
                   scale=(0.15, 0.34, 0.14), x=sx, y=0.52)
            Entity(parent=parent, model='cube', color=_tint(skin, -0.05),
                   scale=(0.13, 0.32, 0.12), x=sx, y=0.22)
    elif anime_f:
        # bare adult thighs + calves under mini skirt
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=skin,
                   scale=(0.15, 0.30, 0.14), x=sx, y=0.52)
            Entity(parent=parent, model='cube', color=_tint(skin, -0.04),
                   scale=(0.13, 0.28, 0.12), x=sx, y=0.24)
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
    elif anime_f or (feminine and not player and not michelle):
        # heeled sandal cue for adult feminine
        shoe = _rgb(color, 240, 220, 210)
        accent = _tint(shirt, -0.2) if shirt is not None else _rgb(color, 200, 80, 140)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=shoe,
                   scale=(0.14, 0.05, 0.28), x=sx, y=0.04, z=0.05)
            Entity(parent=parent, model='cube', color=accent,
                   scale=(0.12, 0.03, 0.05), x=sx, y=0.08, z=0.02)
    else:
        shoe = _rgb(color, 30, 24, 28)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=shoe,
                   scale=(0.14, 0.07, 0.26), x=sx, y=0.04, z=0.03)

    # --- torso / clothing ---
    dress = shirt
    if michelle and michelle_nude:
        # Adult nude anime-feminine variant (Michelle intimacy scene). Not underage.
        Entity(parent=parent, model='cube', color=skin,
               scale=(0.36, 0.42, torso_d * 0.85), y=1.12)  # slim waist torso
        Entity(parent=parent, model='cube', color=_tint(skin, -0.04),
               scale=(0.28, 0.10, torso_d * 0.8), y=0.94)
        Entity(parent=parent, model='sphere', color=_tint(skin, -0.02),
               scale=(hip_w * 0.95, 0.28, 0.36), y=0.78, z=0.06)
        parent.chest = Entity(
            parent=parent, model='sphere', color=skin,
            scale=(0.70, 0.42, 0.48), y=1.24, z=-0.06,
        )
        Entity(parent=parent, model='sphere', color=_tint(skin, 0.04),
               scale=(0.30, 0.28, 0.28), x=-0.17, y=1.26, z=-0.12)
        Entity(parent=parent, model='sphere', color=_tint(skin, 0.04),
               scale=(0.30, 0.28, 0.28), x=0.17, y=1.26, z=-0.12)
        # soft nipples cue (tiny, adult)
        Entity(parent=parent, model='sphere', color=_rgb(color, 220, 140, 140),
               scale=0.05, x=-0.17, y=1.26, z=-0.22)
        Entity(parent=parent, model='sphere', color=_rgb(color, 220, 140, 140),
               scale=0.05, x=0.17, y=1.26, z=-0.22)
        # earrings stay
        Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
               scale=0.05, x=-0.20, y=1.48, z=0.02)
        Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
               scale=0.05, x=0.20, y=1.48, z=0.02)
    elif michelle:
        # fitted bodice (narrower waist read)
        Entity(parent=parent, model='cube', color=dress,
               scale=(0.42, 0.40, torso_d), y=1.14)
        Entity(parent=parent, model='cube', color=_tint(dress, -0.10),
               scale=(0.28, 0.12, torso_d * 0.90), y=0.94)
        Entity(parent=parent, model='cube', color=_tint(dress, -0.04),
               scale=(hip_w * 0.98, 0.16, 0.34), y=0.82)
        Entity(parent=parent, model='cube', color=_tint(dress, 0.04),
               scale=(0.74, 0.38, 0.44), y=0.64)
        Entity(parent=parent, model='cube', color=_tint(dress, 0.08),
               scale=(0.82, 0.18, 0.48), y=0.48)
        Entity(parent=parent, model='sphere', color=_tint(dress, -0.06),
               scale=(0.54, 0.28, 0.36), y=0.76, z=0.12)
        parent.chest = Entity(
            parent=parent, model='sphere', color=dress,
            scale=(0.70, 0.42, 0.48), y=1.22, z=-0.08,
        )
        Entity(parent=parent, model='sphere', color=_tint(dress, 0.08),
               scale=(0.30, 0.28, 0.28), x=-0.17, y=1.25, z=-0.14)
        Entity(parent=parent, model='sphere', color=_tint(dress, 0.08),
               scale=(0.30, 0.28, 0.28), x=0.16, y=1.25, z=-0.14)
        Entity(parent=parent, model='cube', color=skin,
               scale=(0.28, 0.10, 0.14), y=1.36, z=-0.02)
        Entity(parent=parent, model='cube', color=_tint(dress, 0.05),
               scale=(0.05, 0.22, 0.04), x=-0.16, y=1.40, z=-0.02)
        Entity(parent=parent, model='cube', color=_tint(dress, 0.05),
               scale=(0.05, 0.22, 0.04), x=0.16, y=1.40, z=-0.02)
        Entity(parent=parent, model='cube', color=_rgb(color, 20, 18, 22),
               scale=(0.28, 0.06, 0.06), y=1.54, z=0.14)
        Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
               scale=0.05, x=-0.20, y=1.48, z=0.02)
        Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
               scale=0.05, x=0.20, y=1.48, z=0.02)
        Entity(parent=parent, model='cube', color=_tint(skin, 0.06),
               scale=(0.17, 0.22, 0.13), x=-0.14, y=0.40, z=-0.02)
        Entity(parent=parent, model='cube', color=_tint(skin, 0.06),
               scale=(0.17, 0.22, 0.13), x=0.14, y=0.40, z=-0.02)
    elif anime_f:
        # Adult feminine crowd/named: skirt + hourglass + thighs
        Entity(parent=parent, model='cube', color=shirt,
               scale=(0.40, 0.38, torso_d), y=1.14)
        Entity(parent=parent, model='cube', color=_tint(shirt, -0.12),
               scale=(0.30, 0.10, torso_d * 0.9), y=0.96)
        parent.chest = Entity(
            parent=parent, model='sphere', color=_tint(shirt, 0.05),
            scale=(0.58, 0.32, 0.36), y=1.22, z=-0.06,
        )
        Entity(parent=parent, model='cube', color=_tint(shirt, 0.06),
               scale=(0.68, 0.30, 0.40), y=0.68)  # mini skirt
        Entity(parent=parent, model='sphere', color=_tint(shirt, -0.05),
               scale=(0.48, 0.22, 0.30), y=0.78, z=0.10)
        # bare thighs under skirt
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=skin,
                   scale=(0.14, 0.28, 0.13), x=sx, y=0.48)
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
        if fancy and not player:
            # soft bust for named talk NPCs (modest vs Michelle)
            Entity(parent=parent, model='sphere', color=_tint(shirt, 0.05),
                   scale=(0.46, 0.22, 0.28), y=1.20, z=-0.04)
            Entity(parent=parent, model='sphere', color=_tint(shirt, 0.10),
                   scale=(0.16, 0.14, 0.14), x=-0.10, y=1.22, z=-0.10)
            Entity(parent=parent, model='sphere', color=_tint(shirt, 0.10),
                   scale=(0.16, 0.14, 0.14), x=0.10, y=1.22, z=-0.10)

    # Neck
    Entity(parent=parent, model='cube', color=skin,
           scale=(0.12, 0.10, 0.12), y=1.38)

    # Head — slightly larger for adult anime feminine read
    head_y = 1.52
    head_s = 0.38 if michelle else (0.36 if anime_f or feminine else (0.34 if fancy else 0.30))
    head_col = _rgb(color, 255, 220, 170) if michelle else skin
    Entity(parent=parent, model='sphere', color=head_col, scale=head_s, y=head_y)

    # Ears
    if fancy:
        ear = _tint(head_col, -0.04)
        Entity(parent=parent, model='sphere', color=ear, scale=0.08, x=-0.18, y=head_y)
        Entity(parent=parent, model='sphere', color=ear, scale=0.08, x=0.18, y=head_y)

    # Bigger anime-ish eyes (adult feminine only)
    if michelle or anime_f or (feminine and not player):
        eye_w = _rgb(color, 250, 250, 255)
        iris = _rgb(color, 60, 90, 140) if not michelle else _rgb(color, 70, 110, 90)
        for ex in (-0.08, 0.08):
            Entity(parent=parent, model='sphere', color=eye_w,
                   scale=(0.10, 0.11, 0.06), x=ex, y=head_y + 0.02, z=0.14)
            Entity(parent=parent, model='sphere', color=iris,
                   scale=(0.05, 0.06, 0.04), x=ex, y=head_y + 0.02, z=0.17)

    # Hair / silhouette — never a bare cube head
    if michelle:
        # long wavy blonde volume + soft bangs + side fall (adult silhouette)
        Entity(parent=parent, model='sphere', color=hair,
               scale=(0.42, 0.36, 0.40), y=head_y + 0.08, z=-0.02)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.04),
               scale=(0.46, 0.11, 0.22), y=head_y + 0.16, z=0.08)  # bangs
        Entity(parent=parent, model='cube', color=_tint(hair, -0.06),
               scale=(0.18, 0.36, 0.14), x=-0.22, y=head_y - 0.06, z=-0.04)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.06),
               scale=(0.18, 0.36, 0.14), x=0.22, y=head_y - 0.06, z=-0.04)
        # longer back fall / waves
        Entity(parent=parent, model='sphere', color=_tint(hair, -0.08),
               scale=(0.26, 0.36, 0.20), y=head_y - 0.10, z=-0.20)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.12),
               scale=(0.20, 0.40, 0.12), y=head_y - 0.22, z=-0.22)
        # side curls
        Entity(parent=parent, model='sphere', color=_tint(hair, -0.02),
               scale=(0.14, 0.22, 0.14), x=-0.24, y=head_y - 0.18, z=0.02)
        Entity(parent=parent, model='sphere', color=_tint(hair, -0.02),
               scale=(0.14, 0.22, 0.14), x=0.24, y=head_y - 0.18, z=0.02)
        # lips cue
        Entity(parent=parent, model='cube', color=_rgb(color, 210, 90, 110),
               scale=(0.10, 0.03, 0.04), y=head_y - 0.06, z=0.16)
    elif player:
        # short dark crop
        Entity(parent=parent, model='sphere', color=hair,
               scale=(0.36, 0.20, 0.36), y=head_y + 0.10)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.08),
               scale=(0.34, 0.08, 0.16), y=head_y + 0.14, z=0.08)
    elif anime_f or (feminine and not player and not michelle):
        # long adult feminine hair
        Entity(parent=parent, model='sphere', color=hair,
               scale=(0.40, 0.28, 0.38), y=head_y + 0.10)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.06),
               scale=(0.40, 0.10, 0.16), y=head_y + 0.16, z=0.08)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.10),
               scale=(0.22, 0.48, 0.14), y=head_y - 0.18, z=-0.16)
        Entity(parent=parent, model='sphere', color=_tint(hair, -0.04),
               scale=(0.16, 0.28, 0.14), x=-0.22, y=head_y - 0.14)
        Entity(parent=parent, model='sphere', color=_tint(hair, -0.04),
               scale=(0.16, 0.28, 0.14), x=0.22, y=head_y - 0.14)
        Entity(parent=parent, model='cube', color=_rgb(color, 220, 90, 120),
               scale=(0.10, 0.03, 0.04), y=head_y - 0.08, z=0.16)
    elif named:
        Entity(parent=parent, model='sphere', color=hair,
               scale=(0.37, 0.22, 0.37), y=head_y + 0.10)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.10),
               scale=(0.34, 0.10, 0.15), y=head_y + 0.13, z=0.07)
        Entity(parent=parent, model='sphere', color=_tint(hair, -0.08),
               scale=(0.18, 0.20, 0.14), y=head_y - 0.06, z=-0.14)
        Entity(parent=parent, model='cube', color=_tint(shirt, 0.08),
               scale=(0.22, 0.04, 0.12), y=1.30, z=0.12)
    else:
        # utilitarian crowd / male
        Entity(parent=parent, model='sphere', color=hair,
               scale=(0.33, 0.15, 0.33), y=head_y + 0.08)
        Entity(parent=parent, model='cube', color=_tint(hair, -0.08),
               scale=(0.28, 0.06, 0.10), y=head_y + 0.12, z=0.08)

    # Neck stump (all styles) — reduces floating-head look
    Entity(parent=parent, model='cube', color=skin,
           scale=(0.12, 0.10, 0.12), y=head_y - 0.18)

    # Soft nose cue
    if named or detail == 'crowd':
        Entity(parent=parent, model='cube', color=_tint(skin, -0.06),
               scale=(0.05, 0.05, 0.06), y=head_y - 0.02, z=0.15)

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
    """Higher-def body: cabin, roof, trim, mirrors, better wheels — LOD tags on extras."""
    car = Entity(position=pos, rotation_y=yaw)
    car.speed = 0.0
    car.paint = paint
    car.base_paint = paint
    car.kind = 'car'
    car.fuel = 55.0
    car.damage = 0.0
    car.tire_wear = 0.0
    car.disabled = False
    car.smoke_cd = 0.0
    car.out_of_gas_toasted = False
    chrome = _rgb(color, 190, 195, 205)
    glass = _rgb(color, 50, 90, 130)
    rubber = _rgb(color, 18, 18, 18)
    rim = _rgb(color, 160, 160, 170)
    # Main body + lower rocker
    car.body = Entity(parent=car, model='cube', color=paint, scale=(1.70, 0.50, 3.40), y=0.55, collider='box')
    rocker = Entity(parent=car, model='cube', color=_tint(paint, -0.22),
                    scale=(1.74, 0.12, 3.35), y=0.28)
    try:
        rocker.lod_detail = 'mid'
    except Exception:
        pass
    car.cabin = Entity(
        parent=car, model='cube',
        color=_tint(paint, -0.18),
        scale=(1.50, 0.48, 1.55), y=1.05, z=-0.20,
    )
    car.roof = Entity(
        parent=car, model='cube',
        color=_tint(paint, -0.30),
        scale=(1.52, 0.10, 1.48), y=1.34, z=-0.18,
    )
    # Pillars / window frames
    for zx, zz in ((0.55, 0.72), (-0.95, 0.55)):
        ent = Entity(parent=car, model='cube', color=_tint(paint, -0.35),
                     scale=(1.42, 0.36, 0.06), y=1.12, z=zx)
        try:
            ent.lod_detail = 'mid'
        except Exception:
            pass
    # Glass
    Entity(parent=car, model='cube', color=glass, scale=(1.40, 0.32, 0.08), y=1.12, z=0.55)
    Entity(parent=car, model='cube', color=_rgb(color, 40, 70, 110), scale=(1.40, 0.28, 0.08), y=1.10, z=-0.95)
    # Side windows
    for sx in (-0.78, 0.78):
        w = Entity(parent=car, model='cube', color=glass,
                   scale=(0.06, 0.28, 1.20), x=sx, y=1.10, z=-0.15)
        try:
            w.lod_detail = 'high'
        except Exception:
            pass
    # Chrome bumper trim
    for zz, sy in ((1.72, 0.42), (-1.72, 0.42)):
        b = Entity(parent=car, model='cube', color=chrome,
                   scale=(1.55, 0.10, 0.12), y=sy, z=zz)
        try:
            b.lod_detail = 'mid'
        except Exception:
            pass
    # Wheels: rubber + rim disc
    car.wheels = []
    for wx, wz in ((-0.88, 1.10), (0.88, 1.10), (-0.88, -1.10), (0.88, -1.10)):
        tire = Entity(parent=car, model='cube', color=rubber,
                      scale=(0.24, 0.38, 0.38), x=wx, y=0.22, z=wz)
        hub = Entity(parent=car, model='cube', color=rim,
                     scale=(0.10, 0.22, 0.22), x=wx + (0.08 if wx > 0 else -0.08), y=0.22, z=wz)
        try:
            hub.lod_detail = 'high'
        except Exception:
            pass
        car.wheels.append(tire)
    # Side mirrors
    for sx in (-0.92, 0.92):
        m = Entity(parent=car, model='cube', color=_tint(paint, -0.1),
                   scale=(0.14, 0.08, 0.18), x=sx, y=1.05, z=0.55)
        try:
            m.lod_detail = 'high'
        except Exception:
            pass
        Entity(parent=car, model='cube', color=glass,
               scale=(0.06, 0.06, 0.10), x=sx, y=1.05, z=0.58)
    # Door seam / trim line
    for sx in (-0.86, 0.86):
        t = Entity(parent=car, model='cube', color=_tint(paint, -0.28),
                   scale=(0.03, 0.28, 1.6), x=sx, y=0.70, z=-0.05)
        try:
            t.lod_detail = 'high'
        except Exception:
            pass
    # Lights
    Entity(parent=car, model='cube', color=_rgb(color, 255, 240, 180), scale=(0.28, 0.12, 0.08), x=-0.45, y=0.55, z=1.72)
    Entity(parent=car, model='cube', color=_rgb(color, 255, 240, 180), scale=(0.28, 0.12, 0.08), x=0.45, y=0.55, z=1.72)
    Entity(parent=car, model='cube', color=_rgb(color, 220, 40, 40), scale=(0.28, 0.10, 0.06), x=-0.50, y=0.55, z=-1.72)
    Entity(parent=car, model='cube', color=_rgb(color, 220, 40, 40), scale=(0.28, 0.10, 0.06), x=0.50, y=0.55, z=-1.72)
    # Grill
    g = Entity(parent=car, model='cube', color=_rgb(color, 30, 30, 34),
               scale=(0.90, 0.16, 0.06), y=0.52, z=1.74)
    try:
        g.lod_detail = 'high'
    except Exception:
        pass
    car.cam_pivot = Entity(parent=car, y=1.35, z=0.2)
    car.parked = getattr(car, 'parked', True)
    car.traffic = getattr(car, 'traffic', False)
    return car
