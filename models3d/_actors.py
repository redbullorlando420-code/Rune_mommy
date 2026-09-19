"""Humanoid + car meshes — procedural multi-part Ursina primitives.

Adult-only proportions. Michelle = first name only (never a surname / deadname).
Outfit states for adult feminine: clothed -> underwear -> nude
(via style suffixes _underwear/_nude or outfit= kwarg).
"""
from __future__ import annotations

from models3d._base import _rgb


OUTFITS = ('clothed', 'underwear', 'nude')


def _tint(col, amount):
    if hasattr(col, 'tint'):
        try:
            return col.tint(amount)
        except Exception:
            pass
    return col


def _mesh(preferred='sphere'):
    return preferred


def _entity(Entity, *, model='cube', **kw):
    try:
        return Entity(model=model, **kw)
    except Exception:
        if model != 'cube':
            try:
                return Entity(model='cube', **kw)
            except Exception:
                pass
        raise


def parse_style_outfit(style, outfit=None):
    """Return (base_style, outfit) from style name and optional outfit override."""
    base = style
    out = (outfit or 'clothed').lower()
    if isinstance(base, str):
        b = base.lower()
        if b.endswith('_nude'):
            out = 'nude'
            base = base[: -len('_nude')] or None
        elif b.endswith('_underwear'):
            out = 'underwear'
            base = base[: -len('_underwear')] or None
    if out not in OUTFITS:
        out = 'clothed'
    return base, out


def _hair_from_shirt(color, shirt, style, detail):
    if style == 'michelle':
        return _rgb(color, 236, 198, 92)
    if style == 'player':
        return _rgb(color, 52, 38, 28)
    if detail in ('named', 'michelle', 'anime_f'):
        return _tint(shirt, -0.42) if shirt is not None else _rgb(color, 40, 30, 50)
    return _tint(shirt, -0.55) if shirt is not None else _rgb(color, 55, 45, 50)


def clear_humanoid_parts(parent):
    """Remove mesh children so outfit variants can re-attach (hitbox ghost re-added by attach)."""
    try:
        for ch in list(getattr(parent, 'children', []) or []):
            # Keep non-body attachments tagged keep_on_outfit_swap (e.g. portrait billboard)
            if getattr(ch, 'keep_on_outfit_swap', False):
                continue
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
    for attr in ('chest', 'humanoid_style', 'outfit_state'):
        try:
            if attr == 'chest':
                parent.chest = None
        except Exception:
            pass


def _face(Entity, color, parent, head_y, head_s, head_col, *, fancy, michelle, anime_f, feminine, player):
    """Higher-fidelity face cues (still primitives)."""
    # Ears
    if fancy:
        ear = _tint(head_col, -0.04)
        _entity(Entity, parent=parent, model='sphere', color=ear, scale=0.08, x=-head_s * 0.48, y=head_y)
        _entity(Entity, parent=parent, model='sphere', color=ear, scale=0.08, x=head_s * 0.48, y=head_y)

    # Brows
    if fancy:
        brow = _rgb(color, 60, 42, 36) if not michelle else _rgb(color, 180, 140, 70)
        for ex in (-0.09, 0.09):
            Entity(parent=parent, model='cube', color=brow,
                   scale=(0.10, 0.02, 0.03), x=ex, y=head_y + 0.10, z=head_s * 0.38)

    # Eyes
    if michelle or anime_f or (feminine and not player):
        eye_w = _rgb(color, 250, 250, 255)
        iris = _rgb(color, 55, 140, 120) if michelle else _rgb(color, 60, 90, 140)
        eye_scale = (0.13, 0.14, 0.07) if michelle else (0.10, 0.11, 0.06)
        iris_scale = (0.065, 0.075, 0.045) if michelle else (0.05, 0.06, 0.04)
        spread = 0.09 if michelle else 0.08
        for ex in (-spread, spread):
            Entity(parent=parent, model='sphere', color=eye_w,
                   scale=eye_scale, x=ex, y=head_y + 0.03, z=head_s * 0.40)
            Entity(parent=parent, model='sphere', color=iris,
                   scale=iris_scale, x=ex, y=head_y + 0.03, z=head_s * 0.48)
            Entity(parent=parent, model='sphere', color=_rgb(color, 20, 24, 30),
                   scale=(0.03, 0.035, 0.02) if michelle else (0.022, 0.025, 0.015),
                   x=ex, y=head_y + 0.03, z=head_s * 0.52)
            Entity(parent=parent, model='sphere', color=_rgb(color, 255, 255, 255),
                   scale=(0.025, 0.025, 0.015) if michelle else (0.018, 0.018, 0.01),
                   x=ex - 0.02, y=head_y + 0.05, z=head_s * 0.53)
        if michelle or anime_f:
            for ex in (-spread, spread):
                Entity(parent=parent, model='cube', color=_rgb(color, 40, 30, 45),
                       scale=(0.12 if michelle else 0.09, 0.02, 0.03),
                       x=ex, y=head_y + 0.09, z=head_s * 0.42)
            Entity(parent=parent, model='sphere', color=_rgb(color, 255, 160, 170),
                   scale=(0.08, 0.04, 0.03), x=-0.14, y=head_y - 0.02, z=head_s * 0.36)
            Entity(parent=parent, model='sphere', color=_rgb(color, 255, 160, 170),
                   scale=(0.08, 0.04, 0.03), x=0.14, y=head_y - 0.02, z=head_s * 0.36)
    elif fancy:
        # named / player — smaller realistic eyes
        eye_w = _rgb(color, 245, 245, 250)
        iris = _rgb(color, 70, 90, 120) if player else _rgb(color, 90, 70, 50)
        for ex in (-0.07, 0.07):
            Entity(parent=parent, model='sphere', color=eye_w,
                   scale=(0.07, 0.06, 0.04), x=ex, y=head_y + 0.02, z=head_s * 0.42)
            Entity(parent=parent, model='sphere', color=iris,
                   scale=(0.035, 0.035, 0.03), x=ex, y=head_y + 0.02, z=head_s * 0.48)

    # Nose
    if fancy or michelle:
        Entity(parent=parent, model='cube', color=_tint(head_col, -0.06),
               scale=(0.05, 0.06, 0.07), y=head_y - 0.02, z=head_s * 0.42)

    # Lips
    if michelle:
        Entity(parent=parent, model='cube', color=_rgb(color, 220, 80, 110),
               scale=(0.12, 0.035, 0.045), y=head_y - 0.08, z=head_s * 0.44)
    elif anime_f or (feminine and not player):
        Entity(parent=parent, model='cube', color=_rgb(color, 210, 90, 120),
               scale=(0.10, 0.03, 0.04), y=head_y - 0.08, z=head_s * 0.42)
    elif fancy:
        Entity(parent=parent, model='cube', color=_tint(head_col, -0.12),
               scale=(0.08, 0.025, 0.03), y=head_y - 0.08, z=head_s * 0.40)


def _hair_michelle(Entity, parent, hair, head_y):
    # Long wavy blonde cascade — anime twin-volume
    Entity(parent=parent, model='sphere', color=hair,
           scale=(0.48, 0.40, 0.46), y=head_y + 0.10, z=-0.02)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.04),
           scale=(0.50, 0.12, 0.24), y=head_y + 0.18, z=0.10)
    Entity(parent=parent, model='cube', color=_tint(hair, 0.02),
           scale=(0.22, 0.08, 0.12), y=head_y + 0.14, z=0.16)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.06),
           scale=(0.20, 0.48, 0.16), x=-0.26, y=head_y - 0.10, z=-0.02)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.06),
           scale=(0.20, 0.48, 0.16), x=0.26, y=head_y - 0.10, z=-0.02)
    Entity(parent=parent, model='sphere', color=_tint(hair, -0.08),
           scale=(0.32, 0.44, 0.24), y=head_y - 0.14, z=-0.22)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.12),
           scale=(0.26, 0.55, 0.14), y=head_y - 0.32, z=-0.24)
    Entity(parent=parent, model='sphere', color=_tint(hair, -0.10),
           scale=(0.22, 0.30, 0.16), y=head_y - 0.48, z=-0.20)
    Entity(parent=parent, model='sphere', color=_tint(hair, -0.02),
           scale=(0.16, 0.28, 0.16), x=-0.28, y=head_y - 0.28, z=0.04)
    Entity(parent=parent, model='sphere', color=_tint(hair, -0.02),
           scale=(0.16, 0.28, 0.16), x=0.28, y=head_y - 0.28, z=0.04)
    Entity(parent=parent, model='sphere', color=_tint(hair, -0.05),
           scale=(0.14, 0.22, 0.14), x=-0.30, y=head_y - 0.48, z=0.02)
    Entity(parent=parent, model='sphere', color=_tint(hair, -0.05),
           scale=(0.14, 0.22, 0.14), x=0.30, y=head_y - 0.48, z=0.02)


def _hair_feminine(Entity, parent, hair, head_y):
    Entity(parent=parent, model='sphere', color=hair,
           scale=(0.42, 0.30, 0.40), y=head_y + 0.10)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.06),
           scale=(0.42, 0.10, 0.16), y=head_y + 0.16, z=0.08)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.10),
           scale=(0.24, 0.52, 0.14), y=head_y - 0.20, z=-0.16)
    Entity(parent=parent, model='sphere', color=_tint(hair, -0.04),
           scale=(0.16, 0.30, 0.14), x=-0.22, y=head_y - 0.16)
    Entity(parent=parent, model='sphere', color=_tint(hair, -0.04),
           scale=(0.16, 0.30, 0.14), x=0.22, y=head_y - 0.16)


def _hair_player(Entity, parent, hair, head_y):
    Entity(parent=parent, model='sphere', color=hair,
           scale=(0.36, 0.20, 0.36), y=head_y + 0.10)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.08),
           scale=(0.34, 0.08, 0.16), y=head_y + 0.14, z=0.08)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.12),
           scale=(0.30, 0.10, 0.12), y=head_y + 0.06, z=-0.14)


def _hair_named(Entity, parent, hair, shirt, head_y):
    Entity(parent=parent, model='sphere', color=hair,
           scale=(0.38, 0.24, 0.38), y=head_y + 0.10)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.10),
           scale=(0.34, 0.10, 0.15), y=head_y + 0.13, z=0.07)
    Entity(parent=parent, model='sphere', color=_tint(hair, -0.08),
           scale=(0.18, 0.22, 0.14), y=head_y - 0.06, z=-0.14)
    Entity(parent=parent, model='cube', color=_tint(shirt, 0.08),
           scale=(0.22, 0.04, 0.12), y=1.30, z=0.12)


def _hair_crowd(Entity, parent, hair, head_y):
    Entity(parent=parent, model='sphere', color=hair,
           scale=(0.33, 0.16, 0.33), y=head_y + 0.08)
    Entity(parent=parent, model='cube', color=_tint(hair, -0.08),
           scale=(0.28, 0.06, 0.10), y=head_y + 0.12, z=0.08)


def _arms(Entity, parent, *, sleeve, skin, shoulder_w, fancy, detail):
    arm_x = shoulder_w * 0.58
    for sx in (-arm_x, arm_x):
        Entity(parent=parent, model='sphere', color=sleeve,
               scale=0.15 if fancy else 0.12, x=sx * 0.92, y=1.28)
        Entity(parent=parent, model='cube', color=sleeve,
               scale=(0.12, 0.28, 0.12), x=sx, y=1.12)
        Entity(parent=parent, model='cube', color=skin,
               scale=(0.10, 0.26, 0.10), x=sx, y=0.88)
        if fancy:
            # hand + slight finger nubs
            Entity(parent=parent, model='sphere', color=skin, scale=0.10, x=sx, y=0.72)
            Entity(parent=parent, model='cube', color=_tint(skin, -0.04),
                   scale=(0.08, 0.04, 0.10), x=sx, y=0.66, z=0.04)
        elif detail == 'crowd':
            Entity(parent=parent, model='cube', color=skin,
                   scale=(0.08, 0.08, 0.08), x=sx, y=0.72)


def _hitbox_ghost(Entity, parent):
    ghost = Entity(
        parent=parent, model='cube',
        scale=(0.55, 1.60, 0.42), y=0.85,
        collider='box', visible=False,
    )
    try:
        ghost.hitbox_ghost = True
    except Exception:
        pass
    return ghost


def _body_nude_feminine(Entity, color, parent, skin, hip_w, torso_d, leg_gap, *, michelle=False):
    """Adult nude silhouette — hourglass. Never underage."""
    waist = 0.28 if michelle else 0.32
    bust = (0.82, 0.50, 0.56) if michelle else (0.64, 0.38, 0.42)
    Entity(parent=parent, model='cube', color=skin,
           scale=(waist, 0.44, torso_d * 0.82), y=1.12)
    Entity(parent=parent, model='cube', color=_tint(skin, -0.04),
           scale=(waist * 0.85, 0.10, torso_d * 0.78), y=0.92)
    Entity(parent=parent, model='sphere', color=_tint(skin, -0.02),
           scale=(hip_w * 1.00, 0.34 if michelle else 0.28, 0.40 if michelle else 0.34),
           y=0.76, z=0.08)
    parent.chest = Entity(
        parent=parent, model='sphere', color=skin,
        scale=bust, y=1.26, z=-0.08,
    )
    bx = 0.20 if michelle else 0.14
    bs = (0.36, 0.34, 0.34) if michelle else (0.26, 0.24, 0.24)
    Entity(parent=parent, model='sphere', color=_tint(skin, 0.04),
           scale=bs, x=-bx, y=1.28, z=-0.14)
    Entity(parent=parent, model='sphere', color=_tint(skin, 0.04),
           scale=bs, x=bx, y=1.28, z=-0.14)
    Entity(parent=parent, model='sphere', color=_rgb(color, 220, 140, 140),
           scale=0.055 if michelle else 0.04, x=-bx, y=1.28, z=-0.26)
    Entity(parent=parent, model='sphere', color=_rgb(color, 220, 140, 140),
           scale=0.055 if michelle else 0.04, x=bx, y=1.28, z=-0.26)
    Entity(parent=parent, model='sphere', color=_tint(skin, -0.08),
           scale=0.04, y=1.00, z=-0.14)
    # legs already from shared bare-leg path


def _body_underwear_feminine(Entity, color, parent, skin, shirt, hip_w, torso_d, leg_gap, *, michelle=False):
    """Bra + panties — adult feminine only."""
    bra = _rgb(color, 245, 230, 235) if michelle else _tint(shirt, 0.25)
    panty = _rgb(color, 40, 36, 42) if michelle else _tint(shirt, -0.35)
    # bra band + cups
    Entity(parent=parent, model='cube', color=bra,
           scale=(0.42 if michelle else 0.38, 0.10, torso_d * 0.9), y=1.18)
    parent.chest = Entity(
        parent=parent, model='sphere', color=bra,
        scale=(0.78, 0.44, 0.50) if michelle else (0.58, 0.32, 0.36),
        y=1.24, z=-0.08,
    )
    bx = 0.19 if michelle else 0.13
    Entity(parent=parent, model='sphere', color=_tint(bra, 0.06),
           scale=(0.32, 0.30, 0.30) if michelle else (0.22, 0.20, 0.20),
           x=-bx, y=1.26, z=-0.14)
    Entity(parent=parent, model='sphere', color=_tint(bra, 0.06),
           scale=(0.32, 0.30, 0.30) if michelle else (0.22, 0.20, 0.20),
           x=bx, y=1.26, z=-0.14)
    # straps
    Entity(parent=parent, model='cube', color=bra,
           scale=(0.04, 0.22, 0.03), x=-0.16, y=1.40, z=-0.02)
    Entity(parent=parent, model='cube', color=bra,
           scale=(0.04, 0.22, 0.03), x=0.16, y=1.40, z=-0.02)
    # slim midriff
    Entity(parent=parent, model='cube', color=skin,
           scale=(0.30 if michelle else 0.34, 0.28, torso_d * 0.8), y=1.02)
    # panties
    Entity(parent=parent, model='cube', color=panty,
           scale=(hip_w * 0.92, 0.14, 0.30), y=0.80)
    Entity(parent=parent, model='sphere', color=_tint(panty, -0.05),
           scale=(hip_w * 0.85, 0.18, 0.28), y=0.74, z=0.06)


def _body_michelle_dress(Entity, color, parent, dress, skin, hip_w, torso_d):
    """Sexier teal anime-waifu dress — cinched waist, deep neckline, short flare."""
    Entity(parent=parent, model='cube', color=dress,
           scale=(0.36, 0.42, torso_d), y=1.14)
    Entity(parent=parent, model='cube', color=_tint(dress, -0.12),
           scale=(0.24, 0.12, torso_d * 0.88), y=0.92)
    Entity(parent=parent, model='cube', color=_tint(dress, -0.04),
           scale=(hip_w * 1.00, 0.14, 0.36), y=0.80)
    Entity(parent=parent, model='cube', color=_tint(dress, 0.05),
           scale=(0.80, 0.32, 0.46), y=0.62)
    Entity(parent=parent, model='cube', color=_tint(dress, 0.10),
           scale=(0.88, 0.16, 0.50), y=0.46)
    Entity(parent=parent, model='sphere', color=_tint(dress, -0.06),
           scale=(0.62, 0.30, 0.40), y=0.74, z=0.14)
    parent.chest = Entity(
        parent=parent, model='sphere', color=dress,
        scale=(0.80, 0.48, 0.54), y=1.24, z=-0.10,
    )
    Entity(parent=parent, model='sphere', color=_tint(dress, 0.10),
           scale=(0.34, 0.32, 0.32), x=-0.20, y=1.27, z=-0.16)
    Entity(parent=parent, model='sphere', color=_tint(dress, 0.10),
           scale=(0.34, 0.32, 0.32), x=0.20, y=1.27, z=-0.16)
    Entity(parent=parent, model='cube', color=skin,
           scale=(0.30, 0.14, 0.12), y=1.38, z=-0.04)
    Entity(parent=parent, model='sphere', color=_tint(skin, 0.04),
           scale=(0.22, 0.12, 0.10), y=1.34, z=-0.12)
    Entity(parent=parent, model='cube', color=_tint(dress, 0.08),
           scale=(0.04, 0.26, 0.035), x=-0.18, y=1.42, z=-0.02)
    Entity(parent=parent, model='cube', color=_tint(dress, 0.08),
           scale=(0.04, 0.26, 0.035), x=0.18, y=1.42, z=-0.02)
    Entity(parent=parent, model='cube', color=_rgb(color, 20, 18, 22),
           scale=(0.30, 0.05, 0.06), y=1.54, z=0.12)
    Entity(parent=parent, model='sphere', color=_rgb(color, 255, 180, 200),
           scale=0.04, y=1.54, z=0.16)
    Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
           scale=0.055, x=-0.22, y=1.50, z=0.02)
    Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
           scale=0.055, x=0.22, y=1.50, z=0.02)


def _body_anime_f_clothed(Entity, parent, shirt, skin, hip_w, torso_d, leg_gap):
    Entity(parent=parent, model='cube', color=shirt,
           scale=(0.40, 0.38, torso_d), y=1.14)
    Entity(parent=parent, model='cube', color=_tint(shirt, -0.12),
           scale=(0.30, 0.10, torso_d * 0.9), y=0.96)
    parent.chest = Entity(
        parent=parent, model='sphere', color=_tint(shirt, 0.05),
        scale=(0.60, 0.34, 0.38), y=1.22, z=-0.06,
    )
    Entity(parent=parent, model='cube', color=_tint(shirt, 0.06),
           scale=(0.70, 0.32, 0.42), y=0.68)
    Entity(parent=parent, model='sphere', color=_tint(shirt, -0.05),
           scale=(0.50, 0.24, 0.32), y=0.78, z=0.10)
    # collar
    Entity(parent=parent, model='cube', color=_tint(shirt, 0.12),
           scale=(0.24, 0.05, 0.16), y=1.34, z=0.02)


def _body_player(Entity, color, parent, shirt, pants, hip_w, shoulder_w, torso_d):
    torso = Entity(
        parent=parent, model='cube', color=shirt,
        scale=(shoulder_w * 0.92, 0.50, torso_d), y=1.10,
    )
    parent.chest = torso
    Entity(parent=parent, model='cube', color=_tint(shirt, -0.06),
           scale=(hip_w * 0.95, 0.14, torso_d * 0.95), y=0.88)
    # tee collar + hem + pocket
    Entity(parent=parent, model='cube', color=_tint(shirt, 0.12),
           scale=(0.24, 0.05, 0.18), y=1.36, z=0.02)
    Entity(parent=parent, model='cube', color=_tint(shirt, -0.08),
           scale=(0.14, 0.16, 0.02), x=0.16, y=1.12, z=-torso_d * 0.52)
    Entity(parent=parent, model='cube', color=_rgb(color, 24, 28, 36),
           scale=(hip_w * 0.88, 0.06, 0.22), y=0.86)
    # jeans layering
    Entity(parent=parent, model='cube', color=pants,
           scale=(hip_w, 0.22, 0.26), y=0.78)
    Entity(parent=parent, model='cube', color=_tint(pants, -0.25),
           scale=(hip_w * 1.02, 0.05, 0.27), y=0.88)


def _body_named_or_crowd(Entity, color, parent, shirt, pants, skin, hip_w, shoulder_w, torso_d,
                         *, fancy, player, feminine, hitbox):
    torso = Entity(
        parent=parent, model='cube', color=shirt,
        scale=(shoulder_w * 0.92, 0.48, torso_d), y=1.10,
        collider='box' if hitbox and not fancy else None,
    )
    parent.chest = torso
    Entity(parent=parent, model='cube', color=_tint(shirt, -0.06),
           scale=(hip_w * 0.95, 0.14, torso_d * 0.95), y=0.88)
    if fancy:
        Entity(parent=parent, model='cube', color=_tint(shirt, -0.05),
               scale=(shoulder_w, 0.10, torso_d + 0.02), y=1.30)
        Entity(parent=parent, model='cube', color=_tint(shirt, 0.10),
               scale=(0.20, 0.04, 0.14), y=1.34, z=0.02)  # collar
    if fancy and not player and feminine:
        Entity(parent=parent, model='sphere', color=_tint(shirt, 0.05),
               scale=(0.48, 0.24, 0.30), y=1.20, z=-0.04)
        Entity(parent=parent, model='sphere', color=_tint(shirt, 0.10),
               scale=(0.16, 0.14, 0.14), x=-0.10, y=1.22, z=-0.10)
        Entity(parent=parent, model='sphere', color=_tint(shirt, 0.10),
               scale=(0.16, 0.14, 0.14), x=0.10, y=1.22, z=-0.10)
    # pants hips
    Entity(parent=parent, model='cube', color=pants,
           scale=(hip_w, 0.22, 0.26), y=0.78)
    Entity(parent=parent, model='cube', color=_tint(pants, -0.25),
           scale=(hip_w * 1.02, 0.05, 0.27), y=0.88)


def attach_humanoid_parts(
    Entity, color, parent, shirt, pants, skin=None,
    hitbox=False, detail='crowd', style=None, outfit=None,
):
    """Attach multi-part humanoid under `parent`. Height ~1.65–1.72.

    Styles: michelle (anime-waifu teal dress), player, anime_f, named/crowd.
    Outfit (adult feminine): clothed | underwear | nude
      Also accepts style suffixes michelle_nude / anime_f_underwear etc.
    """
    skin = skin or _rgb(color, 255, 206, 166)
    base_style, outfit_state = parse_style_outfit(style, outfit)
    style = base_style

    michelle = style == 'michelle'
    anime_f = style == 'anime_f' or detail == 'anime_f'
    player = style == 'player'
    named = detail in ('named', 'michelle', 'player', 'anime_f') or style in (
        'michelle', 'player', 'anime_f')
    feminine = michelle or anime_f or (named and not player and style != 'male')
    fancy = feminine or named or michelle

    # Underwear/nude: adult feminine NPCs + player (adult). Never underage styles.
    allow_undress = bool(michelle or anime_f or (feminine and not player) or player)
    if not allow_undress and outfit_state != 'clothed':
        outfit_state = 'clothed'

    hair = _hair_from_shirt(color, shirt, 'michelle' if michelle else style, detail)

    # --- proportions (adult) ---
    if michelle:
        hip_w, shoulder_w, torso_d, leg_gap = 0.76, 0.38, 0.36, 0.16
    elif anime_f or (feminine and not player):
        hip_w, shoulder_w, torso_d, leg_gap = 0.60, 0.42, 0.34, 0.14
    elif named and not player:
        hip_w, shoulder_w, torso_d, leg_gap = 0.48, 0.50, 0.30, 0.12
    elif player:
        hip_w, shoulder_w, torso_d, leg_gap = 0.40, 0.54, 0.30, 0.12
    else:
        hip_w, shoulder_w, torso_d, leg_gap = 0.42, 0.50, 0.28, 0.12

    bare_legs = michelle or anime_f or outfit_state in ('underwear', 'nude') or (
        feminine and not player and outfit_state != 'clothed')

    # Hips / pelvis foundation
    if michelle or (feminine and outfit_state != 'clothed'):
        Entity(parent=parent, model='cube', color=skin,
               scale=(hip_w * 0.98, 0.20, 0.28), y=0.76)
        if michelle:
            Entity(parent=parent, model='sphere', color=_tint(skin, -0.03),
                   scale=(hip_w * 1.02, 0.30, 0.34), y=0.74, z=0.08)
    elif anime_f and outfit_state == 'clothed':
        Entity(parent=parent, model='cube', color=skin,
               scale=(hip_w * 0.95, 0.18, 0.26), y=0.78)
        Entity(parent=parent, model='cube', color=_tint(shirt, -0.15),
               scale=(hip_w * 0.7, 0.08, 0.22), y=0.86)
    elif not player:
        Entity(parent=parent, model='cube', color=pants,
               scale=(hip_w, 0.22, 0.26), y=0.78)
        Entity(parent=parent, model='cube', color=_tint(pants, -0.25),
               scale=(hip_w * 1.02, 0.05, 0.27), y=0.88)

    # Legs
    if bare_legs or michelle or anime_f:
        thigh = (0.18, 0.36, 0.16) if michelle else (0.15, 0.32, 0.14)
        calf = (0.14, 0.34, 0.13) if michelle else (0.13, 0.30, 0.12)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=skin,
                   scale=thigh, x=sx, y=0.50)
            Entity(parent=parent, model='cube', color=_tint(skin, -0.05),
                   scale=calf, x=sx, y=0.20)
    else:
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=pants,
                   scale=(0.13, 0.34, 0.13), x=sx, y=0.52)
            Entity(parent=parent, model='cube', color=_tint(pants, -0.08),
                   scale=(0.12, 0.32, 0.12), x=sx, y=0.22)

    # Feet
    if michelle:
        shoe = _rgb(color, 245, 232, 210)
        strap = _rgb(color, 46, 196, 182)
        heel = _rgb(color, 36, 160, 150)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=shoe,
                   scale=(0.16, 0.05, 0.32), x=sx, y=0.05, z=0.06)
            Entity(parent=parent, model='cube', color=strap,
                   scale=(0.14, 0.03, 0.06), x=sx, y=0.09, z=0.02)
            Entity(parent=parent, model='cube', color=heel,
                   scale=(0.08, 0.08, 0.08), x=sx, y=0.03, z=-0.08)
    elif player:
        shoe = _rgb(color, 28, 32, 40)
        sole = _rgb(color, 220, 220, 230)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=shoe,
                   scale=(0.15, 0.08, 0.28), x=sx, y=0.05, z=0.04)
            Entity(parent=parent, model='cube', color=sole,
                   scale=(0.15, 0.03, 0.28), x=sx, y=0.02, z=0.04)
    elif anime_f or (feminine and not player):
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

    # --- torso / clothing by outfit ---
    dress = shirt
    if outfit_state == 'nude' and allow_undress:
        _body_nude_feminine(Entity, color, parent, skin, hip_w, torso_d, leg_gap, michelle=michelle)
        if michelle:
            Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
                   scale=0.055, x=-0.22, y=1.50, z=0.02)
            Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
                   scale=0.055, x=0.22, y=1.50, z=0.02)
    elif outfit_state == 'underwear' and allow_undress:
        _body_underwear_feminine(Entity, color, parent, skin, shirt, hip_w, torso_d, leg_gap, michelle=michelle)
        if michelle:
            Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
                   scale=0.055, x=-0.22, y=1.50, z=0.02)
            Entity(parent=parent, model='sphere', color=_rgb(color, 255, 220, 120),
                   scale=0.055, x=0.22, y=1.50, z=0.02)
    elif michelle:
        _body_michelle_dress(Entity, color, parent, dress, skin, hip_w, torso_d)
        # thigh cue under short hem
        Entity(parent=parent, model='cube', color=_tint(skin, 0.06),
               scale=(0.18, 0.24, 0.14), x=-0.16, y=0.38, z=-0.02)
        Entity(parent=parent, model='cube', color=_tint(skin, 0.06),
               scale=(0.18, 0.24, 0.14), x=0.16, y=0.38, z=-0.02)
    elif anime_f:
        _body_anime_f_clothed(Entity, parent, shirt, skin, hip_w, torso_d, leg_gap)
        for sx in (-leg_gap, leg_gap):
            Entity(parent=parent, model='cube', color=skin,
                   scale=(0.14, 0.28, 0.13), x=sx, y=0.48)
    elif player:
        _body_player(Entity, color, parent, shirt, pants, hip_w, shoulder_w, torso_d)
    else:
        _body_named_or_crowd(
            Entity, color, parent, shirt, pants, skin, hip_w, shoulder_w, torso_d,
            fancy=fancy, player=player, feminine=feminine, hitbox=hitbox,
        )

    # Neck
    Entity(parent=parent, model='cube', color=skin,
           scale=(0.12, 0.10, 0.12), y=1.38)

    # Head
    head_y = 1.52
    head_s = 0.42 if michelle else (0.36 if anime_f or feminine else (0.34 if fancy else 0.30))
    head_col = _rgb(color, 255, 220, 170) if michelle else skin
    Entity(parent=parent, model='sphere', color=head_col, scale=head_s, y=head_y)

    _face(Entity, color, parent, head_y, head_s, head_col,
          fancy=fancy, michelle=michelle, anime_f=anime_f, feminine=feminine, player=player)

    # Hair
    if michelle:
        _hair_michelle(Entity, parent, hair, head_y)
    elif player:
        _hair_player(Entity, parent, hair, head_y)
    elif anime_f or (feminine and not player and not michelle):
        _hair_feminine(Entity, parent, hair, head_y)
    elif named:
        _hair_named(Entity, parent, hair, shirt, head_y)
    else:
        _hair_crowd(Entity, parent, hair, head_y)

    # Neck stump
    Entity(parent=parent, model='cube', color=skin,
           scale=(0.12, 0.10, 0.12), y=head_y - 0.18)

    # Arms — sleeveless when underwear/nude
    if outfit_state in ('underwear', 'nude') and allow_undress:
        sleeve = skin
    else:
        sleeve = dress if michelle else shirt
    _arms(Entity, parent, sleeve=sleeve, skin=skin, shoulder_w=shoulder_w, fancy=fancy, detail=detail)

    if hitbox:
        _hitbox_ghost(Entity, parent)

    # Style string includes outfit for nude/underwear back-compat
    if outfit_state == 'nude' and style:
        stored = f'{style}_nude'
    elif outfit_state == 'underwear' and style:
        stored = f'{style}_underwear'
    else:
        stored = style or detail

    parent.humanoid_style = stored
    parent.outfit_state = outfit_state
    parent._base_style = style or detail
    parent._shirt_col = shirt
    parent._pants_col = pants
    parent._skin_col = skin
    parent._parts_detail = detail
    parent._parts_hitbox = bool(hitbox)
    parent._parts_ready = True
    parent._feminine_adult = bool(allow_undress)
    return parent


def set_humanoid_outfit(Entity, color, parent, outfit, shirt=None, pants=None, skin=None,
                        hitbox=None, detail=None, style=None):
    """Swap outfit clothed|underwear|nude via clear + re-attach. Adult feminine only."""
    outfit = (outfit or 'clothed').lower()
    if outfit not in OUTFITS:
        outfit = 'clothed'
    base = style or getattr(parent, '_base_style', None) or getattr(parent, 'humanoid_style', None)
    base, _ = parse_style_outfit(base, None)
    shirt = shirt if shirt is not None else getattr(parent, '_shirt_col', None)
    pants = pants if pants is not None else getattr(parent, '_pants_col', None)
    skin = skin if skin is not None else getattr(parent, '_skin_col', None)
    detail = detail if detail is not None else getattr(parent, '_parts_detail', 'named')
    hitbox = bool(getattr(parent, '_parts_hitbox', False) if hitbox is None else hitbox)
    if shirt is None:
        shirt = _rgb(color, 46, 196, 182)
    if pants is None:
        pants = shirt
    clear_humanoid_parts(parent)
    attach_humanoid_parts(
        Entity, color, parent, shirt, pants, skin=skin,
        hitbox=hitbox, detail=detail, style=base, outfit=outfit,
    )
    return parent


def cycle_humanoid_outfit(Entity, color, parent, delta=1, **kw):
    """Advance clothed -> underwear -> nude -> clothed."""
    cur = str(getattr(parent, 'outfit_state', 'clothed') or 'clothed').lower()
    if cur not in OUTFITS:
        cur = 'clothed'
    nxt = OUTFITS[(OUTFITS.index(cur) + int(delta)) % len(OUTFITS)]
    set_humanoid_outfit(Entity, color, parent, nxt, **kw)
    return nxt


def make_humanoid(Entity, color, x, z, shirt, pants, skin=None, hitbox=False, detail='crowd', style=None, outfit=None):
    """Root entity at (x,0,z) with multi-part body."""
    root = Entity(position=(x, 0, z))
    try:
        attach_humanoid_parts(
            Entity, color, root, shirt, pants, skin=skin,
            hitbox=hitbox, detail=detail, style=style, outfit=outfit,
        )
    except Exception as exc:
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
