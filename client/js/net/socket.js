import { pack, unpack, C2S, S2C } from '/shared/protocol.js';

export class Net {
  constructor() {
    this.ws = null;
    this.handlers = new Map();
    this.ready = false;
  }
  connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/ws`);
    this.ws = ws;
    return new Promise((resolve, reject) => {
      ws.onopen = () => resolve();
      ws.onerror = () => reject(new Error('socket failed'));
      ws.onmessage = (ev) => {
        let msg;
        try { msg = unpack(ev.data); } catch { return; }
        const fn = this.handlers.get(msg.t);
        if (fn) fn(msg.p, msg);
        const any = this.handlers.get('*');
        if (any) any(msg);
      };
    });
  }
  on(t, fn) { this.handlers.set(t, fn); }
  send(t, p = {}) {
    if (!this.ws || this.ws.readyState !== 1) return;
    this.ws.send(pack(t, p));
  }
  join(name) { this.send(C2S.JOIN, { name }); }
  move(x, y) { this.send(C2S.MOVE, { x, y }); }
  chat(text, channel) { this.send(C2S.CHAT, { text, channel }); }
  interact(id) { this.send(C2S.INTERACT, { id }); }
  attack(id) { this.send(C2S.ATTACK, { id }); }
  pickup(id) { this.send(C2S.PICKUP, { id }); }
  use(slot) { this.send(C2S.USE, { slot }); }
  equip(slot) { this.send(C2S.EQUIP, { slot }); }
  unequip(slot) { this.send(C2S.UNEQUIP, { slot }); }
  drop(slot, qty) { this.send(C2S.DROP, { slot, qty }); }
  tradeReq(id) { this.send(C2S.TRADE_REQ, { id }); }
  tradeResp(yes) { this.send(C2S.TRADE_RESP, { yes }); }
  tradeSet(slot, qty) { this.send(C2S.TRADE_SET, { slot, qty }); }
  tradeBack(i) { this.send(C2S.TRADE_SET, { back: i }); }
  tradeLock(lock) { this.send(C2S.TRADE_LOCK, { lock }); }
  tradeAccept() { this.send(C2S.TRADE_ACCEPT); }
  tradeCancel() { this.send(C2S.TRADE_CANCEL); }
  shopBuy(id, qty) { this.send(C2S.SHOP_BUY, { id, qty }); }
  shopSell(slot, qty) { this.send(C2S.SHOP_SELL, { slot, qty }); }
  bankPut(slot, qty) { this.send(C2S.BANK_PUT, { slot, qty }); }
  bankGet(slot, qty) { this.send(C2S.BANK_GET, { slot }); }
  craft(id) { this.send(C2S.CRAFT, { id }); }
}

export { C2S, S2C };
