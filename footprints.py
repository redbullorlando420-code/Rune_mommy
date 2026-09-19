"""Building / POI footprint occupancy — keep houses/shops/POIs off each other and roads/lakes.

AABB in XZ. Used at boot by densify / deferred retail and (if present) map_layout placer.
"""
from __future__ import annotations

# Hwy 50 asphalt corridor (match crowd.is_on_road)
ROAD_Z0, ROAD_Z1 = -19.5, -12.5
# Soft keep-out pads (cx, cz, half_w, half_d)
KEEP_OUT = (
    (16.0, -42.0, 10.0, 10.0),   # deep lake
    (-44.0, 2.0, 5.5, 5.5),      # west pond
    (62.0, -18.0, 14.0, 10.0),   # walmart box
    (80.0, 80.0, 16.0, 16.0),    # safe yard
)


class FootprintGrid:
    def __init__(self):
        self.boxes = []  # (minx, maxx, minz, maxz, label)
        self.fixed = 0
        self.rejected = 0
        # Seed keep-outs as reserved
        for cx, cz, hw, hd in KEEP_OUT:
            self.boxes.append((cx - hw, cx + hw, cz - hd, cz + hd, 'keepout'))
        # Road strip
        self.boxes.append((-80.0, 90.0, ROAD_Z0, ROAD_Z1, 'hwy50'))

    def overlaps(self, minx, maxx, minz, maxz) -> bool:
        for a0, a1, b0, b1, _ in self.boxes:
            if minx < a1 and maxx > a0 and minz < b1 and maxz > b0:
                return True
        return False

    def register(self, x, z, w, d, label='bldg'):
        hw, hd = w * 0.5, d * 0.5
        self.boxes.append((x - hw, x + hw, z - hd, z + hd, label))

    def place(self, x, z, w=3.5, d=3.2, label='bldg', nudges=12, step=2.5):
        """Return (x, z, ok). Nudge in a spiral if colliding; reject if exhausted."""
        hw, hd = w * 0.5 + 0.4, d * 0.5 + 0.4
        if not self.overlaps(x - hw, x + hw, z - hd, z + hd):
            self.register(x, z, w + 0.8, d + 0.8, label)
            return x, z, True
        # spiral nudge
        for i in range(1, nudges + 1):
            for dx, dz in ((i, 0), (-i, 0), (0, i), (0, -i), (i, i), (-i, i), (i, -i), (-i, -i)):
                nx, nz = x + dx * step * 0.5, z + dz * step * 0.5
                # never into road band center
                if ROAD_Z0 - 0.5 <= nz <= ROAD_Z1 + 0.5:
                    continue
                if not self.overlaps(nx - hw, nx + hw, nz - hd, nz + hd):
                    self.register(nx, nz, w + 0.8, d + 0.8, label)
                    self.fixed += 1
                    return nx, nz, True
        self.rejected += 1
        return x, z, False

    def summary(self) -> str:
        bldg = sum(1 for *_, lab in self.boxes if lab not in ('keepout', 'hwy50'))
        return 'footprints: placed=%d fixed=%d rejected=%d' % (bldg, self.fixed, self.rejected)


def boot(game):
    grid = FootprintGrid()
    game.footprints = grid
    return grid


def get(game) -> FootprintGrid:
    g = getattr(game, 'footprints', None)
    if g is None:
        g = boot(game)
    return g


def place_or_nudge(game, x, z, w=3.5, d=3.2, label='bldg'):
    return get(game).place(x, z, w=w, d=d, label=label)


def log_summary(game):
    g = getattr(game, 'footprints', None)
    if g:
        print(' ', g.summary())
