import { pickup, dropFromSlot, equipFromSlot, unequip } from "./systems/inventory.js";
import { item } from "../shared/catalog.js";
import { S2C } from "../shared/protocol.js";
export function tick(world, dt) { world.tick(dt); }
export function broadcastSnapshots() {}
export function onPickup(world, player, payload) {
  const err = pickup(world, player, payload && payload.id);
  if (err) player.send(S2C.NOTIFY, { text: err, kind: "warn" });
  else world.sendInv(player);
}
export function onUse(world, player, payload) {
  const slot = (payload && payload.slot) | 0;
  const s = player.inv[slot];
  if (!s) return;
  const def = item(s.id);
  if (!def) return;
  if (def.kind === "consumable") {
    if (def.heal) player.hp = Math.min(player.maxHp, player.hp + def.heal);
    if (def.atkBuff) player.buff = { atk: def.atkBuff, until: Date.now() + (def.buffMs || 30000) };
    s.qty -= 1;
    if (s.qty <= 0) player.inv[slot] = null;
    world.sendInv(player);
    return;
  }
  if (def.slot) onEquip(world, player, { slot });
}
export function onEquip(world, player, payload) {
  const err = equipFromSlot(player, (payload && payload.slot) | 0);
  if (err) player.send(S2C.NOTIFY, { text: err, kind: "warn" });
  else { if (player.refresh) player.refresh(); world.sendInv(player); }
}
export function onUnequip(world, player, payload) {
  const err = unequip(player, payload && payload.slot);
  if (err) player.send(S2C.NOTIFY, { text: err, kind: "warn" });
  else { if (player.refresh) player.refresh(); world.sendInv(player); }
}
export function onDrop(world, player, payload) {
  const err = dropFromSlot(world, player, (payload && payload.slot) | 0, (payload && payload.qty) | 0);
  if (err) player.send(S2C.NOTIFY, { text: err, kind: "info" });
  else world.sendInv(player);
}
