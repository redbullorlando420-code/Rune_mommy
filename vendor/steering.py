"""Reynolds-style steering helpers. Original impl of the classic public formulas."""
from __future__ import annotations

import math


def _norm(x, z):
    mag = math.hypot(x, z)
    if mag < 1e-9:
        return (0.0, 0.0)
    return (x / mag, z / mag)


def seek(px, pz, tx, tz):
    """Unit xz vector from (px,pz) toward (tx,tz)."""
    return _norm(tx - px, tz - pz)


def flee(px, pz, tx, tz):
    """Unit xz vector from (tx,tz) away — i.e. run from the threat."""
    return _norm(px - tx, pz - tz)


def wander_heading(heading, t):
    """Noisy wander: heading in radians, t seconds. Returns an xz unit vector."""
    jitter = math.sin(t * 1.73) * 0.85 + math.sin(t * 0.41 + 2.1) * 0.45
    a = float(heading) + jitter
    return (math.sin(a), math.cos(a))
