"""Tile ids and walkability. Port of shared/tiles.js."""

class T:
    VOID = 0
    GRASS = 1
    GRASS_D = 2
    TALL = 3
    PATH = 4
    STONE = 5
    DIRT = 6
    WATER = 7
    WATER_D = 8
    SAND = 9
    WOOD = 10
    RUG = 11
    FLAG = 12
    ASH = 13
    MOSS = 14
    FLOWER = 15
    HEARTH = 16
    DOCK = 17
    SHRINE = 18
    LEAVES = 19
    ROAD = 20
    NEON = 21
    FENCE = 22
    CONCRETE = 23


TILE_WALK = {
    T.VOID: False,
    T.GRASS: True,
    T.GRASS_D: True,
    T.TALL: True,
    T.PATH: True,
    T.STONE: True,
    T.DIRT: True,
    T.WATER: False,
    T.WATER_D: False,
    T.SAND: True,
    T.WOOD: True,
    T.RUG: True,
    T.FLAG: True,
    T.ASH: True,
    T.MOSS: True,
    T.FLOWER: True,
    T.HEARTH: True,
    T.DOCK: True,
    T.SHRINE: True,
    T.LEAVES: True,
    T.ROAD: True,
    T.NEON: True,
    T.FENCE: False,
    T.CONCRETE: True,
}

TILE_NAME = {
    T.GRASS: "grass",
    T.GRASS_D: "deep grass",
    T.TALL: "tall grass",
    T.PATH: "worn path",
    T.STONE: "flagstones",
    T.DIRT: "dirt",
    T.WATER: "dark water",
    T.WATER_D: "deep water",
    T.SAND: "silt",
    T.WOOD: "hearth boards",
    T.RUG: "woven rug",
    T.FLAG: "plaza stone",
    T.ASH: "ash",
    T.MOSS: "moss",
    T.FLOWER: "moonflowers",
    T.HEARTH: "the hearth",
    T.DOCK: "dock boards",
    T.SHRINE: "binding shrine",
    T.LEAVES: "leaf litter",
    T.ROAD: "stone road",
    T.NEON: "sigil plaza",
    T.FENCE: "weathered fence",
    T.CONCRETE: "parking lot",
}
