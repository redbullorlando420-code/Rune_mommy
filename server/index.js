/** Rune Mommy — HTTP static + WebSocket MMO on one port. */
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { WebSocketServer } from 'ws';
import { PORT, TICK_MS, NAME_RE, MAX_PLAYERS, MAX_NAME } from '../shared/constants.js';
import { C2S, S2C, pack, unpack } from '../shared/protocol.js';
import { loadCatalog } from '../shared/catalog.js';
import { createWorld, findEntity } from './world.js';
import { Player, giveStarter } from './player.js';
import { tick, broadcastSnapshots, onPickup, onUse, onEquip, onUnequip, onDrop } from './sim.js';
import { onMove } from './systems/move.js';
import { handleChat, announce } from './systems/chat.js';
import { startAttack } from './systems/combat.js';
import { startGather } from './systems/gather.js';
import { interactNpc, shopBuy, shopSell, bankPut, bankGet } from './systems/npc.js';
import {
  requestTrade, respondTrade, offerSlot, takeBack, setLock, accept, cancel,
} from './systems/trade.js';
import { onCraft, nearShrine } from './systems/craft.js';
import { T } from '../shared/tiles.js';
import { tileAt } from '../shared/worldmap.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.txt': 'text/plain; charset=utf-8',
  '.md': 'text/plain; charset=utf-8',
};

await loadCatalog(async (name) => {
  const p = path.join(ROOT, 'data', name);
  return JSON.parse(fs.readFileSync(p, 'utf8'));
});

const world = createWorld();

function resolveFile(urlPath) {
  let u = decodeURIComponent((urlPath || '/').split('?')[0]);
  if (u.includes('..')) u = '/';
  if (u === '/' || u === '') return path.join(ROOT, 'client', 'index.html');
  const rel = u.replace(/^\/+/ , '');
  if (rel.startsWith('shared/') || rel.startsWith('data/') || rel.startsWith('client/')) {
    return path.join(ROOT, rel);
  }
  return path.join(ROOT, 'client', rel);
}

function handleHttp(req, res) {
  try {
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.writeHead(405); res.end(); return;
    }
    const file = resolveFile(req.url || '/');
    const resolved = path.resolve(file);
    if (!resolved.startsWith(ROOT)) {
      res.writeHead(403); res.end('forbidden'); return;
    }
    let stat;
    try { stat = fs.statSync(resolved); } catch {
      if ((req.url || '').startsWith('/favicon')) {
        res.writeHead(204); res.end(); return;
      }
      res.writeHead(404, { 'content-type': 'text/plain' }); res.end('not found'); return;
    }
    const target = stat.isDirectory() ? path.join(resolved, 'index.html') : resolved;
    const ext = path.extname(target).toLowerCase();
    const mime = MIME[ext] || 'application/octet-stream';
    const body = fs.readFileSync(target);
    res.writeHead(200, {
      'content-type': mime,
      'cache-control': ext === '.html' ? 'no-cache' : 'public, max-age=30',
    });
    if (req.method === 'HEAD') { res.end(); return; }
    res.end(body);
  } catch (err) {
    res.writeHead(500, { 'content-type': 'text/plain' });
    res.end('error');
    console.error(err);
  }
}

const server = http.createServer(handleHttp);
const wss = new WebSocketServer({ server });

function nameTaken(name) {
  const lower = name.toLowerCase();
  for (const p of world.players.values()) if (p.name.toLowerCase() === lower) return true;
  return false;
}

function tryJoin(ws, payload) {
  const name = String(payload?.name || '').trim().slice(0, MAX_NAME);
  if (!NAME_RE.test(name)) {
    ws.send(pack(S2C.REJECT, { reason: 'Name must start with a letter, 2–16 characters.' }));
    return null;
  }
  if (nameTaken(name)) {
    ws.send(pack(S2C.REJECT, { reason: 'That name already walks Emberfen.' }));
    return null;
  }
  if (world.players.size >= MAX_PLAYERS) {
    ws.send(pack(S2C.REJECT, { reason: 'The Hollow is full.' }));
    return null;
  }
  const player = new Player(ws, name);
  giveStarter(player);
  world.players.set(player.id, player);
  const snap = world.snapshotFor(player);
  player.ws.send(pack(snap.t, snap.p));
  announce(world, player.name + " arrives at the first fire.");
  return player;
}

function leave(player) {
  if (!player) return;
  cancel(world, player, 'left');
  world.players.delete(player.id);
  announce(world, player.name + " fades into dusk.");
}

function note(player, err) {
  if (err) player.send(S2C.NOTIFY, { text: err, kind: 'warn' });
}

function onInteract(world, player, payload) {
  const ent = findEntity(world, payload?.id);
  if (!ent) {
    const x = Number(payload?.x), y = Number(payload?.y);
    if (Number.isFinite(x) && tileAt(world.map, x, y) === T.SHRINE) {
      if (nearShrine(world, player)) {
        player.send(S2C.NOTIFY, { text: 'The shrine waits. Bind what you have gathered.', kind: 'info' });
      }
    }
    return;
  }
  if (ent.kind === 'npc') return note(player, interactNpc(world, player, ent.id));
  if (ent.kind === 'node') return note(player, startGather(world, player, ent.id));
  if (ent.kind === 'ground') return onPickup(world, player, { id: ent.id });
  if (ent.kind === 'mob' && !ent.dead) return note(player, startAttack(world, player, ent.id));
}

function handle(player, msg) {
  const p = msg.p || {};
  switch (msg.t) {
    case C2S.MOVE: return onMove(world, player, p);
    case C2S.CHAT: return handleChat(world, player, p.channel, p.text);
    case C2S.INTERACT: return onInteract(world, player, p);
    case C2S.ATTACK: return note(player, startAttack(world, player, p.id));
    case C2S.PICKUP: return onPickup(world, player, p);
    case C2S.USE: return onUse(world, player, p);
    case C2S.EQUIP: return onEquip(world, player, p);
    case C2S.UNEQUIP: return onUnequip(world, player, p);
    case C2S.DROP: return onDrop(world, player, p);
    case C2S.TRADE_REQ: return note(player, requestTrade(world, player, p.id));
    case C2S.TRADE_RESP: return note(player, respondTrade(world, player, !!p.yes));
    case C2S.TRADE_SET: return note(player, (p.back != null) ? takeBack(world, player, p.back | 0) : offerSlot(world, player, p.slot | 0, p.qty | 0));
    case C2S.TRADE_LOCK: return note(player, setLock(world, player, p.lock !== false));
    case C2S.TRADE_ACCEPT: return note(player, accept(world, player));
    case C2S.TRADE_CANCEL: return note(player, cancel(world, player, 'cancelled'));
    case C2S.SHOP_BUY: return note(player, shopBuy(world, player, p.id, p.qty | 0));
    case C2S.SHOP_SELL: return note(player, shopSell(world, player, p.slot | 0, p.qty | 0));
    case C2S.BANK_PUT: return note(player, bankPut(world, player, p.slot | 0, p.qty | 0));
    case C2S.BANK_GET: return note(player, bankGet(world, player, p.slot | 0, p.qty | 0));
    case C2S.CRAFT: return onCraft(world, player, p);
    case C2S.PING: return player.send(S2C.PONG, { t: p.t || Date.now() });
    default: break;
  }
}

wss.on('connection', (ws) => {
  let player = null;
  ws.on('message', (raw) => {
    let msg;
    try { msg = unpack(raw.toString()); } catch { return; }
    if (!player) {
      if (msg.t !== C2S.JOIN) return;
      player = tryJoin(ws, msg.p);
      return;
    }
    try { handle(player, msg); } catch (err) {
      console.error('handle', err);
    }
  });
  ws.on('close', () => leave(player));
  ws.on('error', () => {});
});

setInterval(() => {
  try {
    tick(world, TICK_MS);
    broadcastSnapshots(world);
  } catch (err) {
    console.error('tick', err);
  }
}, TICK_MS);

server.listen(PORT, () => {
  console.log(`Rune Mommy — the first fire is lit at http://localhost:${PORT}`);
});
