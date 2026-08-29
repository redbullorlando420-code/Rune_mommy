import { dist } from '../../shared/constants.js';
import { npcs as npcTable, item } from '../../shared/catalog.js';
import { addItem, canFit, countOf, removeItem, takeSlot } from './inventory.js';

export function interactNpc(world, player, eid) {
  const e = world.entities.get(eid);
  if (!e || e.kind !== 'npc') return 'no one there';
  if (dist(player, e) > 2.1) return 'step closer';
  player.path = [];
  const def = npcTable()?.[e.type];
  if (!def) return 'silence';
  player.talking = e.type;
  player.talkingId = e.id;
  const payload = {
    id: def.id, name: def.name, title: def.title, kind: def.kind,
    greet: def.greet, lines: def.lines || [],
    dialogue: def.dialogue, portrait: def.portrait, start: def.start,
    shop: def.kind === 'shop', bank: def.kind === 'shop' || def.kind === 'bank',
  };
  world.to(player, { t: 'npc', p: payload });
  if (def.kind === 'shop' || def.kind === 'bank') {
    if (def.shop) world.to(player, { t: 'shop', p: { list: def.shop, name: def.name, shopId: def.id } });
    world.to(player, { t: 'bank', p: { items: player.bank } });
  }
  return null;
}

function talkingNpc(world, player) {
  if (player.talkingId && world.entities.get(player.talkingId)) return world.entities.get(player.talkingId);
  for (const e of world.entities.values()) {
    if (e.kind === 'npc' && e.type === player.talking) return e;
  }
  for (const e of world.entities.values()) {
    if (e.kind === 'npc' && e.type === 'voss') return e;
  }
  return null;
}

function shopDef(player) {
  const table = npcTable() || {};
  if (player.talking && table[player.talking]?.shop) return table[player.talking];
  return table.voss;
}

export function shopBuy(world, player, itemId, qty) {
  qty = Math.max(1, Math.min(50, qty | 0));
  const npc = talkingNpc(world, player);
  if (!npc || dist(player, npc) > 2.6) return 'too far from the stall';
  const def = shopDef(player);
  const row = def?.shop?.find((s) => s.id === itemId);
  if (!row) return 'not sold here';
  const it = item(itemId);
  if (!it) return 'unknown item';
  const cost = row.buy * qty;
  if (countOf(player.inv, 'ember_coin') < cost) return `need ${cost} ember coins`;
  if (!canFit(player.inv, itemId, qty)) return 'inventory full';
  removeItem(player.inv, 'ember_coin', cost);
  addItem(player.inv, itemId, qty);
  world.sendInv(player);
  world.to(player, { t: 'notify', p: { text: `Bought ${qty} ${it.name} for ${cost}.`, kind: 'shop' } });
  return null;
}

export function shopSell(world, player, slot, qty) {
  const npc = talkingNpc(world, player);
  if (!npc || dist(player, npc) > 2.6) return 'too far from the stall';
  const s = player.inv[slot];
  if (!s) return 'empty';
  const def = shopDef(player);
  const row = def?.shop?.find((r) => r.id === s.id);
  const it = item(s.id);
  const unit = row?.sell ?? Math.max(1, Math.floor((it?.value || 1) * 0.4));
  const take = qty > 0 ? Math.min(qty, s.qty) : s.qty;
  const got = takeSlot(player.inv, slot, take);
  if (!got) return 'empty';
  addItem(player.inv, 'ember_coin', unit * got.qty);
  world.sendInv(player);
  world.to(player, { t: 'notify', p: { text: `Sold ${got.qty} ${it.name} for ${unit * got.qty}.`, kind: 'shop' } });
  return null;
}

export function bankPut(world, player, slot, qty) {
  const npc = talkingNpc(world, player);
  if (!npc || dist(player, npc) > 2.6) return 'too far from the vault';
  const s = player.inv[slot];
  if (!s) return 'empty';
  const take = qty > 0 ? Math.min(qty, s.qty) : s.qty;
  if (!canFit(player.bank, s.id, take)) return 'vault full';
  const got = takeSlot(player.inv, slot, take);
  addItem(player.bank, got.id, got.qty);
  world.sendInv(player);
  world.to(player, { t: 'bank', p: { items: player.bank } });
  return null;
}

export function bankGet(world, player, slot, qty) {
  const npc = talkingNpc(world, player);
  if (!npc || dist(player, npc) > 2.6) return 'too far from the vault';
  const s = player.bank[slot];
  if (!s) return 'empty';
  const take = qty > 0 ? Math.min(qty, s.qty) : s.qty;
  if (!canFit(player.inv, s.id, take)) return 'inventory full';
  const got = takeSlot(player.bank, slot, take);
  addItem(player.inv, got.id, got.qty);
  world.sendInv(player);
  world.to(player, { t: 'bank', p: { items: player.bank } });
  return null;
}
