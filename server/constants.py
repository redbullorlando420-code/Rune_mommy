"""Port of shared/constants.js."""
import math
import os
import random
import re
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
PORT = int(os.environ.get("PORT", "8080"))
MAX_PLAYERS = 48
SPAWN = {"x": 28.5, "y": 20.5}
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 _-]{1,15}$")

CHANNELS = {"GLOBAL": "global", "LOCAL": "local", "SYSTEM": "system"}
EQUIP_SLOTS = ("weapon", "armor", "charm")
ACTION = {
    "IDLE": "idle",
    "WALK": "walk",
    "ATTACK": "attack",
    "GATHER": "gather",
    "CRAFT": "craft",
    "TALK": "talk",
}

def xp_to_level(xp):
    level = 1
    need = 40
    remain = xp
    while remain >= need and level < 50:
        remain -= need
        level += 1
        need = math.floor(40 * level * (1.12 ** (level - 1)))
    return {"level": level, "into": remain, "need": need}

def _xy(o):
    if isinstance(o, dict):
        return o["x"], o["y"]
    return o.x, o.y

def dist(a, b):
    ax, ay = _xy(a)
    bx, by = _xy(b)
    return math.hypot(ax - bx, ay - by)

def clamp(v, a, b):
    return max(a, min(b, v))

def hue_from_name(name):
    h = 0
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h % 360

def uid(prefix="id"):
    return f"{prefix}_{random.randbytes(4).hex()[:7]}{int(time.time() * 1000) % 36**4:x}"[-24:]
