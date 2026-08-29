/** WebSocket client. JSON {t,p,v:1} via shared pack/unpack. */
import { pack, unpack, C2S, S2C } from '/shared/protocol.js';

export { C2S, S2C };

export class Net {
  constructor() {
    this.ws = null;
    this.handlers = new Map();
    this.connected = false;
    this.joined = false;
    this.rtt = 0;
    this._pingAt = 0;
    this._pingIv = null;
  }

  on(type, fn) {
    const list = this.handlers.get(type) || [];
    list.push(fn);
    this.handlers.set(type, list);
    return () => {
      const next = (this.handlers.get(type) || []).filter((h) => h !== fn);
      this.handlers.set(type, next);
    };
  }

  emit(type, payload) {
    for (const fn of this.handlers.get(type) || []) {
      try { fn(payload || {}, type); } catch (err) { console.error('[net]', type, err); }
    }
    for (const fn of this.handlers.get('*') || []) {
      try { fn(payload || {}, type); } catch (err) { console.error('[net]', type, err); }
    }
  }

  url() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    return proto + '//' + location.host + '/ws';
  }

  connect() {
    if (this.ws && (this.ws.readyState === 0 || this.ws.readyState === 1)) {
      return Promise.resolve();
    }
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(this.url());
      this.ws = ws;
      let opened = false;
      ws.onopen = () => {
        opened = true;
        this.connected = true;
        this._startPing();
        this.emit('open', {});
        resolve();
      };
      ws.onerror = () => {
        if (!opened) reject(new Error('could not reach the Hollow'));
      };
      ws.onclose = () => {
        this.connected = false;
        this.joined = false;
        this._stopPing();
        this.emit('close', {});
      };
      ws.onmessage = (ev) => {
        let msg;
        try { msg = unpack(ev.data); } catch { return; }
        if (msg.t === S2C.PONG) {
          if (this._pingAt) this.rtt = Date.now() - this._pingAt;
        }
        this.emit(msg.t, msg.p || {});
      };
    });
  }

  _startPing() {
    this._stopPing();
    this._pingIv = setInterval(() => {
      if (!this.connected) return;
      this._pingAt = Date.now();
      this.send(C2S.PING, { t: this._pingAt });
    }, 5000);
  }

  _stopPing() {
    if (this._pingIv) { clearInterval(this._pingIv); this._pingIv = null; }
  }

  send(t, p = {}) {
    if (!this.ws || this.ws.readyState !== 1) return false;
    this.ws.send(pack(t, p));
    return true;
  }

  join(name) { this.joined = true; return this.send(C2S.JOIN, { name }); }
  move(x, y) { return this.send(C2S.MOVE, { x, y }); }
  chat(text, channel = 'global') { return this.send(C2S.CHAT, { text, channel }); }
  interact(id) { return this.send(C2S.INTERACT, { id }); }
  attack(id) { return this.send(C2S.ATTACK, { id }); }
  pickup(id) { return this.send(C2S.PICKUP, { id }); }
  use(slot) { return this.send(C2S.USE, { slot }); }
  equip(slot) { return this.send(C2S.EQUIP, { slot }); }
  unequip(slot) { return this.send(C2S.UNEQUIP, { slot }); }
  drop(slot, qty = 0) { return this.send(C2S.DROP, { slot, qty }); }
  tradeReq(id) { return this.send(C2S.TRADE_REQ, { id }); }
  tradeResp(yes) { return this.send(C2S.TRADE_RESP, { yes: !!yes }); }
  tradeSet(slot, qty = 0) { return this.send(C2S.TRADE_SET, { slot, qty }); }
  tradeBack(index) { return this.send(C2S.TRADE_SET, { back: index }); }
  tradeLock(lock = true) { return this.send(C2S.TRADE_LOCK, { lock: !!lock }); }
  tradeAccept() { return this.send(C2S.TRADE_ACCEPT); }
  tradeCancel() { return this.send(C2S.TRADE_CANCEL); }
  shopBuy(id, qty = 1) { return this.send(C2S.SHOP_BUY, { id, qty }); }
  shopSell(slot, qty = 0) { return this.send(C2S.SHOP_SELL, { slot, qty }); }
  bankPut(slot, qty = 0) { return this.send(C2S.BANK_PUT, { slot, qty }); }
  bankGet(slot, qty = 0) { return this.send(C2S.BANK_GET, { slot, qty }); }
  craft(id) { return this.send(C2S.CRAFT, { id }); }
  ping() { return this.send(C2S.PING, { t: Date.now() }); }

  close() {
    this._stopPing();
    try { this.ws?.close(); } catch {}
    this.ws = null;
    this.connected = false;
    this.joined = false;
  }
}
