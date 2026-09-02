"""Wire protocol. JSON {t, p, v} matching shared/protocol.js. PROTO=1."""
from __future__ import annotations

import json
import re

PROTO = 1

C2S = {
    "JOIN": "join",
    "MOVE": "move",
    "CHAT": "chat",
    "INTERACT": "interact",
    "ATTACK": "attack",
    "PICKUP": "pickup",
    "USE": "use",
    "EQUIP": "equip",
    "UNEQUIP": "unequip",
    "DROP": "drop",
    "TRADE_REQ": "trade_req",
    "TRADE_RESP": "trade_resp",
    "TRADE_SET": "trade_set",
    "TRADE_LOCK": "trade_lock",
    "TRADE_ACCEPT": "trade_accept",
    "TRADE_CANCEL": "trade_cancel",
    "SHOP_BUY": "shop_buy",
    "SHOP_SELL": "shop_sell",
    "BANK_PUT": "bank_put",
    "BANK_GET": "bank_get",
    "CRAFT": "craft",
    "PING": "ping",
}

S2C = {
    "WELCOME": "welcome",
    "REJECT": "reject",
    "SNAPSHOT": "snapshot",
    "DELTA": "delta",
    "CHAT": "chat",
    "FLOAT": "float",
    "XP": "xp",
    "INV": "inv",
    "BANK": "bank",
    "EQUIP": "equip",
    "TRADE": "trade",
    "NPC": "npc",
    "SHOP": "shop",
    "CRAFT_OK": "craft_ok",
    "NOTIFY": "notify",
    "PONG": "pong",
}


def pack(typ, payload=None):
    if payload is None:
        payload = {}
    return json.dumps({"t": typ, "p": payload, "v": PROTO}, separators=(",", ":"))


def unpack(raw):
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    msg = json.loads(raw)
    if not msg or not isinstance(msg.get("t"), str):
        raise ValueError("bad message")
    return msg
