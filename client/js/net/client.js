import { pack, unpack } from '/shared/protocol.js';

const handlers = new Map();
let ws = null;
let queue = [];

export function on(type, fn) {
  if (!handlers.has(type)) handlers.set(type, []);
  handlers.get(type).push(fn);
}

export function send(type, payload = {}) {
  const raw = pack(type, payload);
  if (ws && ws.readyState === 1) ws.send(raw);
  else queue.push(raw);
}

export function connect() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = proto + '//' + location.host + '/ws';
  return new Promise((resolve, reject) => {
    ws = new WebSocket(url);
    ws.onopen = () => {
      for (const q of queue) ws.send(q);
      queue = [];
      resolve(ws);
    };
    ws.onerror = () => reject(new Error('socket failed'));
    ws.onclose = () => {
      for (const fn of handlers.get('close') || []) fn();
    };
    ws.onmessage = (ev) => {
      let msg;
      try { msg = unpack(ev.data); } catch { return; }
      for (const fn of handlers.get(msg.t) || []) fn(msg.p || {}, msg);
    };
  });
}

export function connected() {
  return ws && ws.readyState === 1;
}
