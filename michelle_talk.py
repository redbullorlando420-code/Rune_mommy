"""Michelle dialogue opening picker — branching starts from flags / life-sim / breed.

First name only. Never Lewis / last name / deadname.
"""
from __future__ import annotations

import random


def pick_michelle_opening(game) -> str:
    """Choose a start node id for E-talk with Michelle (not mid-tree room nodes)."""
    nodes = ((getattr(game, 'michelle_dlg', None) or {}).get('nodes') or {})

    def has(nid: str) -> bool:
        return nid in nodes

    if not getattr(game, 'michelle_seen', False):
        return 'door' if has('door') else 'hi'

    if getattr(game, 'preg', False) and has('open_preg'):
        return 'open_preg'

    breed = int(getattr(game, 'breed', 0) or 0)
    if breed >= 70 and has('open_breed_high'):
        return 'open_breed_high'

    m = getattr(game, 'michelle', None)
    state = getattr(m, 'life_state', None) if m else None
    if state == 'wander' and has('open_wander'):
        return 'open_wander'
    if state == 'shop' and has('open_shop'):
        return 'open_shop'

    heat = float(getattr(game, 'heat', 0) or 0)
    if heat >= 1.0 and has('open_heat'):
        return 'open_heat'

    # In-game hour from life_sim minutes (accelerated clock)
    minutes = float(getattr(game, 'life_sim_minutes', 12 * 60) or 0)
    hour = int((minutes / 60.0) % 24)
    if hour < 9 and has('open_morning'):
        return 'open_morning'
    if hour >= 22 and has('open_late'):
        return 'open_late'

    # Rotate soft return openings so E is not always the same path
    pool = [n for n in ('hi', 'open_soft', 'open_tease', 'door') if has(n)]
    if not pool:
        return 'door'
    idx = int(getattr(game, 'michelle_open_idx', 0) or 0)
    game.michelle_open_idx = idx + 1
    return pool[idx % len(pool)]


def decorate_michelle_text(game, text: str) -> str:
    """Append life-sim flavor under node text when useful."""
    if not text:
        return text
    m = getattr(game, 'michelle', None)
    if not m:
        return text
    try:
        import life_sim
        extra = life_sim.state_line(m)
    except Exception:
        extra = None
    if not extra or extra in text:
        return text
    return f"{text}\n\n({extra})"
