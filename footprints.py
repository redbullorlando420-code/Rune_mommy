"""Building / POI footprint occupancy — AABB in XZ.

Keeps houses/shops/POIs/food-trucks/densify off each other, roads, lakes,
and the Clermont spawn / gate / Sanctuary clear plazas.
"""
from __future__ import annotations

ROAD_Z0, ROAD_Z1 = -19.5, -12.5

# Soft keep-out pads (cx, cz, half_w, half_d)
KEEP_OUT = (
    (16.0, -42.0, 10.0, 10.0),   # deep lake
    (-44.0, 2.0, 5.5, 5.5),      # west pond
    (62.0, -18.0, 14.0, 10.0),   # walmart box
    (80.0, 80.0, 16.0, 16.0),    # safe yard
)

# Clear plazas (cx, cz, radius, label) — no shops/houses/retail/densify
SPAWN_PLAZAS = (
    (-18.0, 12.0, 32.0, 'spawn_plaza'),       # clermont_spawn / gate exit
    (-32.0, 12.0, 14.0, 'sanctuary_plaza'),   # Michelle yard
)


class FootprintGrid:
    def __init__(self):
        self.boxes = []  # (minx, maxx, minz, maxz, label)
        self.fixed = 0
        self.rejected = 0
        self.spawn_blocked = 0
        self._spawn_circles = list(SPAWN_PLAZAS)
        for cx, cz, hw, hd in KEEP_OUT:
            self.boxes.append((cx - hw, cx + hw, cz - hd, cz + hd, 'keepout'))
        for cx, cz, radius, lab in self._spawn_circles:
            self.boxes.append((cx - radius, cx + radius, cz - radius, cz + radius, lab))
        self.boxes.append((-80.0, 90.0, ROAD_Z0, ROAD_Z1, 'hwy50'))

    def set_spawn(self, x, z, radius=32.0):
        """Re-center spawn plaza on live clermont_spawn."""
        self.boxes = [b for b in self.boxes if b[4] != 'spawn_plaza']
        self._spawn_circles = [
            (float(x), float(z), float(radius), 'spawn_plaza'),
            (-32.0, 12.0, 14.0, 'sanctuary_plaza'),
        ]
        for cx, cz, r, lab in self._spawn_circles:
            self.boxes.append((cx - r, cx + r, cz - r, cz + r, lab))

    def in_spawn_plaza(self, x, z) -> bool:
        for cx, cz, radius, _lab in self._spawn_circles:
            if (x - cx) ** 2 + (z - cz) ** 2 <= radius * radius:
                return True
        return False

    def overlaps(self, minx, maxx, minz, maxz) -> bool:
        for a0, a1, b0, b1, _ in self.boxes:
            if minx < a1 and maxx > a0 and minz < b1 and maxz > b0:
                return True
        return False

    def register(self, x, z, w, d, label='bldg'):
        hw, hd = w * 0.5, d * 0.5
        self.boxes.append((x - hw, x + hw, z - hd, z + hd, label))

    def place(self, x, z, w=3.5, d=3.2, label='bldg', nudges=12, step=2.5):
        """Return (x, z, ok). Reject spawn plaza hard; spiral-nudge otherwise."""
        if self.in_spawn_plaza(x, z):
            self.rejected += 1
            self.spawn_blocked += 1
            return x, z, False
        hw, hd = w * 0.5 + 0.4, d * 0.5 + 0.4
        if not self.overlaps(x - hw, x + hw, z - hd, z + hd):
            self.register(x, z, w + 0.8, d + 0.8, label)
            return x, z, True
        for i in range(1, nudges + 1):
            for dx, dz in (
                (i, 0), (-i, 0), (0, i), (0, -i),
                (i, i), (-i, i), (i, -i), (-i, -i),
            ):
                nx = x + dx * step * 0.5
                nz = z + dz * step * 0.5
                if ROAD_Z0 - 0.5 <= nz <= ROAD_Z1 + 0.5:
                    continue
                if self.in_spawn_plaza(nx, nz):
                    continue
                if not self.overlaps(nx - hw, nx + hw, nz - hd, nz + hd):
                    self.register(nx, nz, w + 0.8, d + 0.8, label)
                    self.fixed += 1
                    return nx, nz, True
        self.rejected += 1
        return x, z, False

    def remaining_overlaps(self):
        skip = {'keepout', 'hwy50', 'spawn_plaza', 'sanctuary_plaza'}
        bldgs = [b for b in self.boxes if b[4] not in skip]
        hits = []
        for i, (a0, a1, b0, b1, la) in enumerate(bldgs):
            for c0, c1, d0, d1, lb in bldgs[i + 1:]:
                if a0 < c1 and a1 > c0 and b0 < d1 and b1 > d0:
                    hits.append((la, lb))
        return hits

    def summary(self) -> str:
        skip = {'keepout', 'hwy50', 'spawn_plaza', 'sanctuary_plaza'}
        bldg = sum(1 for *_, lab in self.boxes if lab not in skip)
        return (
            'footprints: placed=%d fixed=%d rejected=%d spawn_blocked=%d'
            % (bldg, self.fixed, self.rejected, self.spawn_blocked)
        )


def boot(game):
    grid = FootprintGrid()
    game.footprints = grid
    try:
        spawn = getattr(game, 'clermont_spawn', None) or (-18.0, 0.0, 12.0)
        sx, _sy, sz = spawn
        grid.set_spawn(sx, sz, radius=32.0)
    except Exception:
        pass
    print('  footprints: spawn plaza r=32 + sanctuary r=14 (open near gate)')
    return grid


def get(game) -> FootprintGrid:
    g = getattr(game, 'footprints', None)
    if g is None:
        g = boot(game)
    return g


def place_or_nudge(game, x, z, w=3.5, d=3.2, label='bldg'):
    """Public API — game retail / town / densify."""
    return get(game).place(x, z, w=w, d=d, label=label)


def log_summary(game):
    g = get(game)
    print(' ', g.summary())
    hits = g.remaining_overlaps()
    if hits:
        print('  footprints OVERLAPS remaining=%d' % len(hits))
        for a, b in hits[:12]:
            print('    overlap:', a, '<->', b)
        if len(hits) > 12:
            print('    ... +%d more' % (len(hits) - 12))
    else:
        print('  footprints OVERLAPS remaining=0')
    return g.summary()
