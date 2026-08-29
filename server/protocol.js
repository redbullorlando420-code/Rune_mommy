import { C2S, unpack } from '../shared/protocol.js';
import { NAME_RE, MAX_PLAYERS, MAX_CHAT } from '../shared/constants.js';
import { setDestination } from './systems/movement.js';
import { startAttack } from './systems/combat.js';
import { startGather, startCraft } from './systems/gather.js';
import { handleChat } from './systems/chat.js';
import { requestTrade, respondTrade, offerSlot, takeBack, setLock, accept, cancel } from './systems/trade.js';
import { pickup, dropFromSlot, equipFromSlot, unequip } from './systems/inventory.js';
import { interactNpc, shopBuy, shopSell, bankPut, bankGet } from './systems/npc.js';
import { item } from '../shared/catalog.js';

export function onMessage(world, player, raw) {
  let msg;
  try { msg = unpack(raw); } catch { return; }
  const t = msg.t;
  const p = msg.p || {};
  if (t === C2S.PING) {
    world.to(player, { t: 'pong', p: { t: p.t } });
    return;
  }
  if (!player) return;

  const err = dispatch(world, player, t, p);
  if (err) world.to(player, { t: 'notify', p: { text: err, kind: 'warn' } });
}

function dispatch(world, player, t, p) {
  switch (t) {
    case C2S.MOVE:
      if (player.hp <= 0) return 'you are down';
      if (player.tradeId) return 'finish the trade first';
      setDestination(world, player, Number(p.x), Number(p.y));
      return null;
    case C2S.CHAT:
      handleChat(world, player, p.channel, String(p.text || '').slice(0, MAX_CHAT));
      return null;
    case C2S.INTERACT:
      return interact(world, player, p.id);
    case C2S.ATTACK:
      return startAttack(world, player, p.id);
    case C2S.PICKUP:
      { const e = pickup(world, player, p.id); if (!e) world.sendInv(player); return e; }
    case C2S.USE:
      return useItem(world, player, p.slot | 0);
    case C2S.EQUIP:
      { const e = equipFromSlot(player, p.slot | 0); if (!e) world.sendInv(player); return e; }
    case C2S.UNEQUIP:
      { const e = unequip(player, p.slot); if (!e) world.sendInv(player); return e; }
    case C2S.DROP:
      { const e = dropFromSlot(world, player, p.slot | 0, p.qty | 0); if (!e) world.sendInv(player); return e; }
    case C2S.TRADE_REQ:
      return requestTrade(world, player, p.id);
    case C2S.TRADE_RESP:
      return respondTrade(world, player, !!p.yes);
    case C2S.TRADE_SET:
      if (p.back != null) return takeBack(world, player, p.back | 0);
      return offerSlot(world, player, p.slot | 0, p.qty | 0);
    case C2S.TRADE_LOCK:
      return setLock(world, player, p.lock !== false);
    case C2S.TRADE_ACCEPT:
      return accept(world, player);
    case C2S.TRADE_CANCEL:
      return cancel(world, player, 'cancelled');
    case C2S.SHOP_BUY:
      return shopBuy(world, player, p.id, p.qty | 0);
    case C2S.SHOP_SELL:
      return shopSell(world, player, p.slot | 0, p.qty | 0);
    case C2S.BANK_PUT:
      return bankPut(world, player, p.slot | 0, p.qty | 0);
    case C2S.BANK_GET:
      return bankGet(world, player, p.slot | 0, p.qty | 0);
    case C2S.CRAFT:
      return startCraft(world, player, p.id);
    default:
      return null;
  }
}

function interact(world, player, id) {
  const e = world.entities.get(id);
  if (!e) {
    if (world.players.has(id) && id !== player.id) return requestTrade(world, player, id);
    return 'nothing there';
  }
  if (e.kind === 'npc') return interactNpc(world, player, id);
  if (e.kind === 'node') return startGather(world, player, id);
  if (e.kind === 'mob') return startAttack(world, player, id);
  if (e.kind === 'ground') {
    const err = pickup(world, player, id);
    if (!err) world.sendInv(player);
    return err;
  }
  return null;
}

function useItem(world, player, slot) {
  const s = player.inv[slot];
  if (!s) return 'empty';
  const def = item(s.id);
  if (!def) return 'unknown';
  if (def.kind === 'consumable') {
    if (def.heal) {
      player.hp = Math.min(player.maxHp, player.hp + def.heal);
      world.float(player.x, player.y, `+${def.heal}`, '#80ed99', player.id);
    }
    if (def.atkBuff) {
      player.buff = { atk: def.atkBuff, until: Date.now() + (def.buffMs || 30000) };
      world.to(player, { t: 'notify', p: { text: 'Your hand steadies.', kind: 'buff' } });
    }
    s.qty -= 1;
    if (s.qty <= 0) player.inv[slot] = null;
    world.sendInv(player);
    return null;
  }
  if (def.slot) {
    const err = equipFromSlot(player, slot);
    if (!err) world.sendInv(player);
    return err;
  }
  if (def.id === 'tutor_note') {
    world.to(player, { t: 'notify', p: { text: 'Walk. Gather. Hunt. Trade. The Hollow remembers those who share.', kind: 'system' } });
    return null;
  }
  return 'cannot use that';
}

export function tryJoin(world, ws, raw) {
  let msg;
  try { msg = unpack(raw); } catch { return { err: 'bad handshake' }; }
  if (msg.t !== C2S.JOIN) return { err: 'send join first' };
  let name = String(msg.p?.name || '').trim();
  if (!NAME_RE.test(name)) return { err: 'name: 2–16 letters, numbers, space, _ -' };
  if (world.players.size >= MAX_PLAYERS) return { err: 'the Hollow is full' };
  for (const p of world.players.values()) {
    if (p.name.toLowerCase() === name.toLowerCase()) return { err: 'that name is already walking' };
  }
  const player = world.addPlayer(ws, name);
  return { player };
}
