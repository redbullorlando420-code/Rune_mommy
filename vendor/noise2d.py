"""Seeded value noise and fBm. Original impl of classic lattice value noise."""
from __future__ import annotations

import math


def _hash01(ix: int, iz: int, seed: int) -> float:
    n = (ix * 374761393 + iz * 668265263 + int(seed) * 1274126177) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n = (n ^ (n >> 16)) & 0xFFFFFFFF
    return n / 4294967295.0


def _fade(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def noise2(x, z, seed=0):
    """Value noise in roughly [-1, 1] at (x, z). Deterministic for a seed."""
    x = float(x)
    z = float(z)
    ix = math.floor(x)
    iz = math.floor(z)
    fx = x - ix
    fz = z - iz
    u = _fade(fx)
    v = _fade(fz)
    n00 = _hash01(ix, iz, seed)
    n10 = _hash01(ix + 1, iz, seed)
    n01 = _hash01(ix, iz + 1, seed)
    n11 = _hash01(ix + 1, iz + 1, seed)
    nx0 = n00 + (n10 - n00) * u
    nx1 = n01 + (n11 - n01) * u
    return (nx0 + (nx1 - nx0) * v) * 2.0 - 1.0


def fbm2(x, z, octaves=4, seed=0, lacunarity=2.0, gain=0.5):
    """Fractal Brownian motion: summed octaves of noise2. Range ~[-1, 1]."""
    octaves = max(1, int(octaves))
    amp = 1.0
    freq = 1.0
    total = 0.0
    norm = 0.0
    x = float(x)
    z = float(z)
    for i in range(octaves):
        total += noise2(x * freq, z * freq, seed=int(seed) + i * 101) * amp
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm if norm else 0.0
