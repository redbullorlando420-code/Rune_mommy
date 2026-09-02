"""Inventory handlers + tick glue. Port of server/sim.js."""
from __future__ import annotations

from systems.inventory import pickup, drop_from_slot, equip_from_slot, unequip
from catalog import item
from protocol import S2C


def tick(world, dt):
    world.tick(dt)


def broadcast_snapshots(world=None):
    pass


def on_pickup(world, player, payload):
    err = pickup(world, player, payload.get("id") if payload else None)
    if err:
        player.send(S2C["NOTIFY"], {"text": err, "kind": "warn"})
    else:
        world.send_inv(player)


def on_use(world, player, payload):
    slot = int((payload or {}).get("slot") or 0)
    s = player.inv[slot] if 0 <= slot < len(player.inv) else None
    if not s:
        return
    defn = item(s["id"])
    if not defn:
        return
    if defn.get("kind") == "consumable":
        if defn.get("heal"):
            player.hp = min(player.maxHp, player.hp + defn["heal"])
        if defn.get("atkBuff"):
            from constants import now
            player.buff = {"atk": defn["atkBuff"], "until": now() + (defn.get("buffMs") or 30000)}
        s["qty"] -= 1
        if s["qty"] <= 0:
            player.inv[slot] = None
        world.send_inv(player)
        return
    if defn.get("slot"):
        on_equip(world, player, {"slot": slot})
    elif defn.get("id") == "tutor_note":
        player.send(S2C["NOTIFY"], {
            "text": "Walk. Gather. Hunt. Trade. The Hollow remembers those who share.",
            "kind": "system",
        })


def on_equip(world, player, payload):
    err = equip_from_slot(player, int((payload or {}).get("slot") or 0))
    if err:
        player.send(S2C["NOTIFY"], {"text": err, "kind": "warn"})
    else:
        if hasattr(player, "refresh"):
            player.refresh()
        world.send_inv(player)


def on_unequip(world, player, payload):
    err = unequip(player, (payload or {}).get("slot"))
    if err:
        player.send(S2C["NOTIFY"], {"text": err, "kind": "warn"})
    else:
        if hasattr(player, "refresh"):
            player.refresh()
        world.send_inv(player)


def on_drop(world, player, payload):
    err = drop_from_slot(
        world, player,
        int((payload or {}).get("slot") or 0),
        int((payload or {}).get("qty") or 0),
    )
    if err:
        player.send(S2C["NOTIFY"], {"text": err, "kind": "info"})
    else:
        world.send_inv(player)
