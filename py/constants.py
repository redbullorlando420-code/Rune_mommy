"""One source of truth for Rune Mommy. Port of shared/constants.js."""
from __future__ import annotations

import math
import os
import random
import time

TICK_RATE = 20
TICK_MS = 1000 / TICK_RATE
TILE = 48
MAP_W = 112
MAP_H = 76
WALK_SPEED = 3.35
PLAYER_RADIUS = 0.32
INTERACT_RANGE = 1.65
ATTACK_MELEE = 1.5
TRADE_RANGE = 3.2
LOCAL_CHAT_RANGE = 9
MAX_NAME = 16
INV_SIZE = 24
BANK_SIZE = 32
GROUND_DESPAWN_MS = 90_000
MAX_CHAT = 160
PORT = int(os.environ.get("PORT") or 8080)
MAX_PLAYERS = 48
SPAWN = {"x": 28.5, "y": 20.5}
NAME_RE = r"^[A-Za-z][A-Za-z0-9 _-]{1,15}$"

CHANNELS = {
    "GLOBAL": "global",
    "LOCAL": "local",
    "SYSTEM": "system",
}

EQUIP_SLOTS = ("weapon", "armor", "charm")

ACTION = {
    "IDLE": "idle",
    "WALK": "walk",
    "ATTACK": "attack",
    "GATHER": "gather",
    "CRAFT": "craft",
    "TALK": "talk",
}

_ALPH = "0123456789abcdefghijklmnopqrstuvwxyz"


def _to36(n: int) -> str:
    n = int(n)
    if n <= 0:
        return "0"
    chars = []
    while n:
        n, r = divmod(n, 36)
        chars.append(_ALPH[r])
    return "".join(reversed(chars))


def xp_to_level(xp):
    level = 1
    need = 40
    remain = xp
    while remain >= need and level < 50:
        remain -= need
        level += 1
        need = math.floor(40 * level * (1.12 ** (level - 1)))
    return {"level": level, "into": remain, "need": need}


def total_xp_for_level(level):
    xp = 0
    for l in range(1, level):
        xp += math.floor(40 * l * (1.12 ** (l - 1)))
    return xp


def dist(a, b):
    dx = _x(a) - _x(b)
    dy = _y(a) - _y(b)
    return math.hypot(dx, dy)


def _x(o):
    return o["x"] if isinstance(o, dict) else o.x


def _y(o):
    return o["y"] if isinstance(o, dict) else o.y


def clamp(v, a, b):
    return max(a, min(b, v))


def lerp(a, b, t):
    return a + (b - a) * t


def hue_from_name(name):
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h % 360


def now():
    return int(time.time() * 1000)


def uid(prefix="id"):
    frac = random.random()
    # Approximate JS Math.random().toString(36).slice(2, 9)
    n = int(frac * (36 ** 8))
    rand_part = (_to36(n) + "0000000")[:7]
    time_part = (_to36(now())[-4:])
    return f"{prefix}_{rand_part}{time_part}"
