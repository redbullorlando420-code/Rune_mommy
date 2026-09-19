"""Chunk / micro-chunk streaming stub — coarse grid hide/sleep for far agents.

CHUNK=32, MICRO=8. Full streaming next green; boot tags + tick hides far peds/cars.
"""
from __future__ import annotations
from lighting import set_visible

CHUNK = 32.0
MICRO = 8.0
ACTIVE = 2

def _cell(x, z, size):
    return int(x // size), int(z // size)

def boot(game):
    game.chunk_state = {'frames': 0, 'last': None}
    print('  chunks: stub on (size=%.0f micro=%.0f)' % (CHUNK, MICRO))

def tick(game, dt):
    st = getattr(game, 'chunk_state', None)
    player = getattr(game, 'player', None)
    if not st or not player:
        return
    st['frames'] = st.get('frames', 0) + 1
    if st['frames'] % 4 != 0:
        return
    cx, cz = _cell(float(player.x), float(player.z), CHUNK)
    if st.get('last') == (cx, cz) and st['frames'] % 60 != 0:
        return
    st['last'] = (cx, cz)
    active = {(cx + dx, cz + dz) for dx in range(-ACTIVE, ACTIVE + 1) for dz in range(-ACTIVE, ACTIVE + 1)}
    for ped in list(getattr(game, 'peds', []) or []):
        if not ped:
            continue
        try:
            cell = _cell(float(ped.x), float(ped.z), CHUNK)
            set_visible(ped, cell in active)
        except Exception:
            pass
    in_car = getattr(game, 'in_car', None)
    for car in list(getattr(game, 'cars', []) or []):
        if not car or car is in_car:
            continue
        try:
            cell = _cell(float(car.x), float(car.z), CHUNK)
            set_visible(car, cell in active)
        except Exception:
            pass

def assign(ent, x=None, z=None):
    pass
