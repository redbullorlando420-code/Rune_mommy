/** Authoritative inventory, equipment, ground items. No negative stacks. */
import { INV_SIZE, BANK_SIZE, EQUIP_SLOTS, GROUND_DESPAWN_MS, uid } from '../../shared/constants.js';
import { item } from '../../shared/catalog.js';

export function emptyInv(n = INV_SIZE) {
  return Array.from({ length: n }, () => null);
}

export function countOf(inv, id) {
  let n = 0;
  for (const s of inv) if (s && s.id === id) n += s.qty;
  return n;
}

export function firstEmpty(inv) {
  return inv.findIndex((s) => !s);
}

export function canFit(inv, id, qty) {
  const def = item(id);
  if (!def) return false;
  const stack = def.stack || 1;
  let left = qty;
  for (const s of inv) {
    if (!s) { left -= stack; }
    else if (s.id === id) left -= Math.max(0, stack - s.qty);
    if (left <= 0) return true;
  }
  return left <= 0;
}

export function addItem(inv, id, qty) {
  const def = item(id);
  if (!def || qty <= 0) return false;
  const stack = def.stack || 1;
  let left = qty;
  for (const s of inv) {
    if (s && s.id === id && s.qty < stack) {
      const take = Math.min(stack - s.qty, left);
      s.qty += take;
      left -= take;
      if (left <= 0) return true;
    }
  }
  for (let i = 0; i < inv.length && left > 0; i++) {
    if (!inv[i]) {
      const take = Math.min(stack, left);
      inv[i] = { id, qty: take };
      left -= take;
    }
  }
  return left <= 0;
}

export function removeItem(inv, id, qty) {
  if (countOf(inv, id) < qty) return false;
  let left = qty;
  for (let i = 0; i < inv.length && left > 0; i++) {
    const s = inv[i];
    if (!s || s.id !== id) continue;
    const take = Math.min(s.qty, left);
    s.qty -= take;
    left -= take;
    if (s.qty <= 0) inv[i] = null;
  }
  return left <= 0;
}

export function takeSlot(inv, slot, qty = 0) {
  const s = inv[slot];
  if (!s) return null;
  if (!qty || qty >= s.qty) {
    inv[slot] = null;
    return { id: s.id, qty: s.qty };
  }
  s.qty -= qty;
  return { id: s.id, qty };
}

export function compact(inv) {
  return inv;
}

export function serializeInv(inv) {
  return inv.map((s) => (s ? { id: s.id, qty: s.qty } : null));
}

export function equipFromSlot(player, slot) {
  const s = player.inv[slot];
  if (!s) return 'empty slot';
  const def = item(s.id);
  if (!def || !def.slot || !EQUIP_SLOTS.includes(def.slot)) return 'cannot equip that';
  if (s.qty !== 1) return 'cannot equip a stack';
  const prev = player.equip[def.slot];
  player.inv[slot] = null;
  if (prev) {
    if (!addItem(player.inv, prev, 1)) {
      player.inv[slot] = s;
      return 'no room to swap';
    }
  }
  player.equip[def.slot] = s.id;
  return null;
}

export function unequip(player, slotName) {
  const id = player.equip[slotName];
  if (!id) return 'nothing there';
  if (!addItem(player.inv, id, 1)) return 'inventory full';
  player.equip[slotName] = null;
  return null;
}

export function dropFromSlot(world, player, slot, qty) {
  const s = player.inv[slot];
  if (!s) return 'empty';
  const take = qty > 0 ? Math.min(qty, s.qty) : s.qty;
  const got = takeSlot(player.inv, slot, take);
  if (!got) return 'empty';
  spawnGround(world, player.x, player.y, got.id, got.qty);
  return null;
}

export function spawnGround(world, x, y, id, qty) {
  const e = {
    id: uid('g'),
    kind: 'ground',
    type: id,
    x: x + (Math.random() - 0.5) * 0.5,
    y: y + (Math.random() - 0.5) * 0.5,
    qty,
    born: Date.now(),
  };
  world.entities.set(e.id, e);
  return e;
}

export function pickup(world, player, eid) {
  const e = world.entities.get(eid);
  if (!e || e.kind !== 'ground') return 'nothing there';
  const dx = e.x - player.x, dy = e.y - player.y;
  if (Math.hypot(dx, dy) > 1.8) return 'too far';
  if (!canFit(player.inv, e.type, e.qty)) return 'inventory full';
  addItem(player.inv, e.type, e.qty);
  world.entities.delete(eid);
  return null;
}

export function tickGround(world, now) {
  for (const [id, e] of world.entities) {
    if (e.kind === 'ground' && now - e.born > GROUND_DESPAWN_MS) world.entities.delete(id);
  }
}

export { INV_SIZE, BANK_SIZE };
