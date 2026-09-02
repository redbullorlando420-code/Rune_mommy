"""Authoritative player: stats, pack, bank, equipment, skills."""
from __future__ import annotations

from constants import SPAWN, INV_SIZE, BANK_SIZE, EQUIP_SLOTS, uid, ACTION, xp_to_level, hue_from_name, now
from protocol import pack, S2C
from catalog import item, player_stats, skill_level
from systems.inventory import empty_inv, add_item as inv_add, remove_item as inv_remove, count_of, can_fit, serialize_inv
from netutil import send_ws


class Player:
    def __init__(self, ws, name):
        self.id = uid("p")
        self.ws = ws
        self.name = name
        self.x = SPAWN["x"]
        self.y = SPAWN["y"]
        self.dir = 0
        self.path = []
        self.hp = 40
        self.maxHp = 40
        self.inv = empty_inv(INV_SIZE)
        self.bank = empty_inv(BANK_SIZE)
        self.equip = {"weapon": None, "armor": None, "charm": None}
        self.skills = {"combat": {"xp": 0}, "foraging": {"xp": 0}, "binding": {"xp": 0}}
        self.action = ACTION["IDLE"]
        self.target = None
        self.tradeId = None
        self.tradeAsk = None
        self.tradeAskTo = None
        self.intent = None
        self.channel = None
        self.buff = None
        self.lastSwing = 0
        self.nextSwing = 0
        self.atk = 4
        self.def_ = 2
        self.joinedAt = now()
        self.lastChat = 0
        self.regenAcc = 0
        self.hue = hue_from_name(name)
        self.deadFor = 0
        self.talking = None
        self.talkingId = None

    def send(self, typ, payload=None):
        send_ws(self.ws, pack(typ, payload or {}))

    def add_item(self, iid, qty):
        return inv_add(self.inv, iid, qty)

    def remove_item(self, iid, qty):
        return inv_remove(self.inv, iid, qty)

    def count_item(self, iid):
        return count_of(self.inv, iid)

    def has_items(self, lst):
        for row in lst:
            if count_of(self.inv, row["id"]) < row["qty"]:
                return False
        return True

    def can_fit(self, iid, qty):
        return can_fit(self.inv, iid, qty)

    def bonus_atk(self):
        n = 0
        for slot in EQUIP_SLOTS:
            it = item(self.equip[slot]) if self.equip.get(slot) else None
            if it:
                n += it.get("atk") or 0
        return n

    def bonus_def(self):
        n = 0
        for slot in EQUIP_SLOTS:
            it = item(self.equip[slot]) if self.equip.get(slot) else None
            if it:
                n += it.get("def") or 0
        return n

    def bonus_hp(self):
        n = 0
        for slot in EQUIP_SLOTS:
            it = item(self.equip[slot]) if self.equip.get(slot) else None
            if it:
                n += it.get("hp") or 0
        return n

    def refresh(self):
        s = player_stats(self)
        ratio = self.hp / self.maxHp if self.maxHp > 0 else 1
        self.maxHp = s["maxHp"]
        self.atk = s["atk"]
        self.def_ = s["def"]
        self.hp = max(0, min(s["maxHp"], round(ratio * s["maxHp"])))

    def add_xp(self, skill_id, amount):
        if skill_id not in self.skills:
            self.skills[skill_id] = {"xp": 0}
        before = skill_level(self, skill_id)
        self.skills[skill_id]["xp"] += max(0, int(amount or 0))
        after = skill_level(self, skill_id)
        prog = xp_to_level(self.skills[skill_id]["xp"])
        self.send(S2C["XP"], {
            "skill": skill_id, "xp": self.skills[skill_id]["xp"], "amount": amount,
            "level": after, "into": prog["into"], "need": prog["need"],
        })
        if after > before:
            self.refresh()
            self.hp = min(self.maxHp, self.hp + 8)
            self.send(S2C["NOTIFY"], {"text": f"{label_skill(skill_id)} rises to {after}.", "kind": "xp"})
        return after

    def public_view(self):
        return {
            "id": self.id,
            "name": self.name,
            "x": r2(self.x),
            "y": r2(self.y),
            "hp": round(self.hp),
            "maxHp": self.maxHp,
            "action": self.action if isinstance(self.action, str) else (self.action or {}).get("type") if isinstance(self.action, dict) else "idle",
            "dir": r2(self.dir),
        }

    def private_view(self):
        pv = self.public_view()
        pv.update({
            "inv": serialize_inv(self.inv),
            "bank": serialize_inv(self.bank),
            "equip": {"weapon": self.equip.get("weapon"), "armor": self.equip.get("armor"), "charm": self.equip.get("charm")},
            "skills": {
                "combat": self.skills["combat"]["xp"],
                "foraging": self.skills["foraging"]["xp"],
                "binding": self.skills["binding"]["xp"],
            },
            "atk": self.atk,
            "def": self.def_,
            "target": self.target,
            "coins": self.count_item("ember_coin"),
            "channel": {"type": self.channel["type"], "until": self.channel["until"]} if self.channel else None,
        })
        return pv


def label_skill(sid):
    return {"combat": "Ashen Combat", "foraging": "Dusk Foraging", "binding": "Hearth Binding"}.get(sid, sid)


def r2(n):
    return round(n * 100) / 100


def give_starter(player):
    player.equip["weapon"] = "worn_dirk"
    player.equip["armor"] = "cloth_wrap"
    inv_add(player.inv, "hearthbread", 3)
    inv_add(player.inv, "ember_coin", 80)
    inv_add(player.inv, "tutor_note", 1)
    player.refresh()
    player.hp = player.maxHp
