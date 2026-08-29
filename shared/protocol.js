/** Wire protocol. Keep payloads small and versioned. */

export const PROTO = 1;

export const C2S = Object.freeze({
  JOIN: 'join',
  MOVE: 'move',
  CHAT: 'chat',
  INTERACT: 'interact',
  ATTACK: 'attack',
  PICKUP: 'pickup',
  USE: 'use',
  EQUIP: 'equip',
  UNEQUIP: 'unequip',
  DROP: 'drop',
  TRADE_REQ: 'trade_req',
  TRADE_RESP: 'trade_resp',
  TRADE_SET: 'trade_set',
  TRADE_LOCK: 'trade_lock',
  TRADE_ACCEPT: 'trade_accept',
  TRADE_CANCEL: 'trade_cancel',
  SHOP_BUY: 'shop_buy',
  SHOP_SELL: 'shop_sell',
  BANK_PUT: 'bank_put',
  BANK_GET: 'bank_get',
  CRAFT: 'craft',
  PING: 'ping',
});

export const S2C = Object.freeze({
  WELCOME: 'welcome',
  REJECT: 'reject',
  SNAPSHOT: 'snapshot',
  DELTA: 'delta',
  CHAT: 'chat',
  FLOAT: 'float',
  XP: 'xp',
  INV: 'inv',
  BANK: 'bank',
  EQUIP: 'equip',
  TRADE: 'trade',
  NPC: 'npc',
  SHOP: 'shop',
  CRAFT_OK: 'craft_ok',
  NOTIFY: 'notify',
  PONG: 'pong',
});

export function pack(type, payload = {}) {
  return JSON.stringify({ t: type, p: payload, v: PROTO });
}

export function unpack(raw) {
  const msg = JSON.parse(raw);
  if (!msg || typeof msg.t !== 'string') throw new Error('bad message');
  return msg;
}
