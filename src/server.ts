import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { WebSocketServer, WebSocket } from "ws";
import {
  ROOT, PORT, TICK, SPEED, MAX_HP, MAX_EN, ITEMS, item,
  REGIONS, buildings, shops, npcs, nodes, trades, players, names,
  blocked, hue, skill, qtyOf, take, spaceFor, give,
  send, toast, publicChat, snapshot, mePayload, pushMe, uniqueName, starterInv,
  type Player, type Slot, type Trade
} from "./world.ts";

let nextId = 1;
function join(ws: WebSocket, name: string) {
  const n = uniqueName(name);
  const id = "p" + (nextId++);
  const p: Player = {
    id, name: n, color: hue(n),
    x: (Math.random() - 0.5) * 6, y: 0, z: 8 + (Math.random() - 0.5) * 4,
    tx: 0, tz: 8, facing: 0,
    hp: MAX_HP, energy: MAX_EN, gold: 180,
    inv: starterInv(), forageXp: 0, combatXp: 0, buffs: [],
    ws, lastChat: 0,
  };
  p.tx = p.x; p.tz = p.z;
  players.set(id, p);
  names.set(n.toLowerCase(), id);
  send(p, {
    t: "welcome", items: ITEMS, shops, regions: REGIONS, buildings,
    world: { min: -180, max: 180 },
    motd: "Clermont Square. Neon north is Shake Row -- Mama Mira sells The Cool Down. Press M for the world map.",
    ...snapshot(), me: mePayload(p),
  });
  publicChat("System", n + " walked into Clermont.", "system");
}

function stepToward(p: { x: number; z: number; tx: number; tz: number }, spd: number, dt: number) {
  const dx = p.tx - p.x, dz = p.tz - p.z;
  const dist = Math.hypot(dx, dz);
  if (dist < 0.08) { p.x = p.tx; p.z = p.tz; return 0; }
  const step = Math.min(dist, spd * dt);
  const nx = p.x + (dx / dist) * step;
  const nz = p.z + (dz / dist) * step;
  if (!blocked(nx, nz)) { p.x = nx; p.z = nz; }
  else if (!blocked(nx, p.z)) p.x = nx;
  else if (!blocked(p.x, nz)) p.z = nz;
  return step;
}

function tick() {
  const now = Date.now();
  const dt = TICK / 1000;
  for (const p of players.values()) {
    p.buffs = p.buffs.filter(b => b.until > now);
    const spd = SPEED * (1 + p.buffs.reduce((a, b) => a + (b.speed || 0), 0));
    const moved = stepToward(p, spd, dt);
    if (moved > 0) p.facing = Math.atan2(p.tx - p.x, p.tz - p.z);
    if (p.energy < MAX_EN) p.energy = Math.min(MAX_EN, p.energy + 3 * dt);
    if (p.hp < MAX_HP && !p.target) p.hp = Math.min(MAX_HP, p.hp + 1.2 * dt);
    if (p.gather && now >= p.gather.until) {
      const node = nodes.find(n => n.id === p.gather!.id);
      p.gather = undefined;
      if (node && Math.hypot(p.x - node.x, p.z - node.z) < 2.4) {
        if (give(p.inv, node.item, 1)) {
          p.forageXp += 8;
          node.ready = false;
          node.busyUntil = now + 18000 + Math.random() * 8000;
          toast(p, "You pick " + (item(node.item)?.name || node.item) + ".");
          pushMe(p);
        } else toast(p, "Inventory is full.", "warn");
      }
    }
    if (p.target) {
      const n = npcs.find(x => x.id === p.target);
      if (!n || n.kind !== "hostile" || n.hp <= 0) p.target = undefined;
      else if (Math.hypot(p.x - n.x, p.z - n.z) > 2.6) { p.tx = n.x; p.tz = n.z; }
      else if (p.energy >= 3) {
        const power = 7 + skill(p.combatXp) + p.buffs.reduce((a, b) => a + (b.power || 0), 0);
        n.hp -= Math.max(1, power + Math.floor(Math.random() * 5) - (n.maxHp > 40 ? 2 : 0));
        p.energy -= 3; p.combatXp += 3;
        if (Math.random() < 0.35) {
          const armor = p.buffs.reduce((a, b) => a + (b.armor || 0), 0);
          p.hp -= Math.max(1, 4 + Math.floor(Math.random() * 5) - armor);
        }
        if (p.hp <= 0) {
          p.hp = MAX_HP * 0.6; p.x = 0; p.z = 8; p.tx = 0; p.tz = 8; p.target = undefined;
          toast(p, "You faint and wake at the fountain.", "warn");
        }
        if (n.hp <= 0) {
          p.target = undefined; p.combatXp += 18;
          p.gold += 4 + Math.floor(Math.random() * 8);
          const drop = n.loot?.[Math.floor(Math.random() * (n.loot.length || 1))];
          if (drop) give(p.inv, drop, 1);
          n.respawn = now + 22000;
          toast(p, "You down the " + n.name + ".");
        }
        pushMe(p);
      }
    }
  }
  for (const n of npcs) {
    if (n.kind !== "hostile") continue;
    if (n.hp <= 0 && n.respawn && now >= n.respawn) { n.hp = n.maxHp; n.x = n.hx; n.z = n.hz; n.respawn = undefined; }
    if (n.hp > 0) {
      n.x = n.hx + Math.sin(now / 900 + n.hx) * 1.6;
      n.z = n.hz + Math.cos(now / 1100 + n.hz) * 1.6;
    }
  }
  for (const node of nodes) if (!node.ready && now >= node.busyUntil) node.ready = true;
}

function findByName(name: string) {
  const id = names.get(name.toLowerCase());
  return id ? players.get(id) : undefined;
}
function openShop(p: Player, shopId: string) {
  const s = shops.find(x => x.id === shopId);
  if (!s) return;
  if (Math.hypot(p.x - s.x, p.z - (s.z + (s.z < 0 ? 6 : -6))) > 5 && Math.hypot(p.x - s.x, p.z - s.z) > 8) {
    toast(p, "Walk closer to the stall."); return;
  }
  send(p, { t: "shop", shop: s });
}
function buy(p: Player, shopId: string, itemId: string, qty: number) {
  const s = shops.find(x => x.id === shopId);
  const line = s?.stock.find(l => l.itemId === itemId);
  const n = Math.max(1, Math.min(20, qty | 0));
  if (!s || !line || !item(itemId)) { toast(p, "They do not sell that."); return; }
  const cost = line.price * n;
  if (p.gold < cost) { toast(p, "Not enough gold.", "warn"); return; }
  if (!spaceFor(p.inv, itemId, n)) { toast(p, "Inventory is full.", "warn"); return; }
  p.gold -= cost; give(p.inv, itemId, n);
  toast(p, "Bought " + item(itemId)!.name + " x" + n + " from " + s.name + ".");
  pushMe(p);
}
function useItem(p: Player, id: string) {
  const def = item(id);
  if (!def || qtyOf(p.inv, id) < 1) return;
  if (!def.heal && !def.energy && !def.buff) { toast(p, def.examine); return; }
  take(p.inv, id, 1);
  if (def.heal) p.hp = Math.min(MAX_HP, p.hp + def.heal);
  if (def.energy) p.energy = Math.min(MAX_EN, p.energy + def.energy);
  if (def.buff) {
    p.buffs = p.buffs.filter(b => b.id !== def.buff!.id);
    p.buffs.push({ ...def.buff, until: Date.now() + def.buff.ms });
  }
  toast(p, "You enjoy " + def.name + ".");
  pushMe(p);
}
function tradeKey(a: string, b: string) { return [a, b].sort().join(":"); }
function tradeState(tr: Trade) {
  const A = players.get(tr.a), B = players.get(tr.b);
  return {
    t: "trade",
    a: A ? { id: A.id, name: A.name, offer: tr.offerA, ok: tr.okA } : null,
    b: B ? { id: B.id, name: B.name, offer: tr.offerB, ok: tr.okB } : null,
  };
}
function pushTrade(tr: Trade) {
  const st = tradeState(tr);
  const A = players.get(tr.a), B = players.get(tr.b);
  if (A) send(A, st); if (B) send(B, st);
}
function cancelTrade(id: string, why = "Trade cancelled.") {
  for (const [k, tr] of trades) {
    if (tr.a === id || tr.b === id) {
      trades.delete(k);
      const A = players.get(tr.a), B = players.get(tr.b);
      if (A) { send(A, { t: "trade", closed: true }); toast(A, why); }
      if (B) { send(B, { t: "trade", closed: true }); toast(B, why); }
    }
  }
}
function cloneSlots(s: Slot[]) { return s.map(x => ({ id: x.id, qty: x.qty })); }
function hasOffer(p: Player, offer: { items: Slot[]; gold: number }) {
  if (offer.gold < 0 || offer.gold > p.gold) return false;
  const need: Record<string, number> = {};
  for (const s of offer.items) need[s.id] = (need[s.id] || 0) + s.qty;
  for (const [id, n] of Object.entries(need)) if (qtyOf(p.inv, id) < n) return false;
  return true;
}
function applyTrade(tr: Trade): string | null {
  const A = players.get(tr.a), B = players.get(tr.b);
  if (!A || !B) return "Player left.";
  if (!hasOffer(A, tr.offerA) || !hasOffer(B, tr.offerB)) return "Offer no longer valid.";
  const invA = cloneSlots(A.inv), invB = cloneSlots(B.inv);
  for (const s of tr.offerA.items) if (!take(invA, s.id, s.qty)) return "Offer no longer valid.";
  for (const s of tr.offerB.items) if (!take(invB, s.id, s.qty)) return "Offer no longer valid.";
  for (const s of tr.offerB.items) if (!give(invA, s.id, s.qty)) return "Not enough inventory space.";
  for (const s of tr.offerA.items) if (!give(invB, s.id, s.qty)) return "Not enough inventory space.";
  A.inv = invA; B.inv = invB;
  A.gold -= tr.offerA.gold; A.gold += tr.offerB.gold;
  B.gold -= tr.offerB.gold; B.gold += tr.offerA.gold;
  return null;
}
function handle(p: Player, m: Record<string, unknown>) {
  const t = m.t;
  if (t === "walk") {
    const x = Number(m.x), z = Number(m.z);
    if (!Number.isFinite(x) || !Number.isFinite(z)) return;
    p.tx = Math.max(-178, Math.min(178, x));
    p.tz = Math.max(-178, Math.min(178, z));
    p.target = undefined; p.gather = undefined;
  } else if (t === "chat") {
    const now = Date.now();
    if (now - p.lastChat < 250) return;
    p.lastChat = now;
    const text = String(m.text || "").slice(0, 160).trim();
    if (!text) return;
    const w = text.match(/^\/(w|whisper)\s+(\S+)\s+(.+)$/i);
    if (w) {
      const to = findByName(w[2]);
      if (!to) { toast(p, "No one by that name."); return; }
      publicChat(p.name, w[3], "whisper", to.name);
    } else publicChat(p.name, text);
  } else if (t === "interact") {
    const kind = String(m.kind || "");
    const id = String(m.id || "");
    if (kind === "npc") {
      const n = npcs.find(x => x.id === id);
      if (!n) return;
      if (n.kind === "shop" && n.shopId) openShop(p, n.shopId);
      else if (n.kind === "hostile") { p.target = n.id; p.tx = n.x; p.tz = n.z; toast(p, "You square up to the " + n.name + "."); }
      else {
        const lines: Record<string, string> = {
          "npc-banker": "Bank's a vibe, not a vault yet. Keep gold on you. Shake Row is north -- Mira's neon stall.",
          "npc-crier": "Clermont Square! Hwy 50 Shake Row to the north. Wilds and the mine further out. Press M.",
          "npc-dock": "Johns Lake Dock. Culver's is back toward town on Johns Lake Rd. Don't fall in.",
        };
        toast(p, lines[n.id] || (n.name + " nods."));
        send(p, { t: "examine", text: lines[n.id] || n.name });
      }
    } else if (kind === "node") {
      const node = nodes.find(x => x.id === id);
      if (!node || !node.ready) { toast(p, "Nothing to gather yet."); return; }
      if (Math.hypot(p.x - node.x, p.z - node.z) > 2.5) { p.tx = node.x; p.tz = node.z; }
      if (p.energy < 8) { toast(p, "You're winded."); return; }
      p.energy -= 8;
      p.gather = { id: node.id, until: Date.now() + 2200 };
      toast(p, "Gathering " + node.name + "...");
      pushMe(p);
    } else if (kind === "shop") openShop(p, id);
  } else if (t === "examine") {
    const id = String(m.id || "");
    const it = item(id);
    if (it) send(p, { t: "examine", text: it.examine });
    const s = shops.find(x => x.id === id);
    if (s) send(p, { t: "examine", text: s.name + " -- " + s.address + ". " + s.blurb });
  } else if (t === "buy") buy(p, String(m.shopId || ""), String(m.itemId || ""), Number(m.qty || 1));
  else if (t === "use") useItem(p, String(m.itemId || m.id || ""));
  else if (t === "tradeAsk") {
    const o = players.get(String(m.playerId || ""));
    if (!o || o.id === p.id) return;
    if (Math.hypot(p.x - o.x, p.z - o.z) > 6) { toast(p, "Too far to trade."); return; }
    const k = tradeKey(p.id, o.id);
    if (!trades.has(k)) trades.set(k, { a: p.id, b: o.id, offerA: { items: [], gold: 0 }, offerB: { items: [], gold: 0 }, okA: false, okB: false });
    pushTrade(trades.get(k)!);
  } else if (t === "tradeOffer") {
    const k = [...trades.values()].find(tr => tr.a === p.id || tr.b === p.id);
    if (!k) return;
    const offer = {
      items: Array.isArray(m.items) ? (m.items as Slot[]).filter(s => s && item(s.id) && s.qty > 0).slice(0, 8) : [],
      gold: Math.max(0, Math.min(p.gold, Number(m.gold) || 0)),
    };
    if (!hasOffer(p, offer)) { toast(p, "You don't have that."); return; }
    if (k.a === p.id) { k.offerA = offer; k.okA = false; k.okB = false; }
    else { k.offerB = offer; k.okA = false; k.okB = false; }
    pushTrade(k);
  } else if (t === "tradeAccept") {
    const k = [...trades.values()].find(tr => tr.a === p.id || tr.b === p.id);
    if (!k) return;
    if (k.a === p.id) k.okA = true; else k.okB = true;
    if (k.okA && k.okB) {
      const err = applyTrade(k);
      const A = players.get(k.a), B = players.get(k.b);
      trades.delete(tradeKey(k.a, k.b));
      if (err) {
        if (A) { send(A, { t: "trade", closed: true }); toast(A, err, "warn"); }
        if (B) { send(B, { t: "trade", closed: true }); toast(B, err, "warn"); }
      } else {
        if (A) { send(A, { t: "trade", closed: true, done: true }); toast(A, "Trade complete."); pushMe(A); }
        if (B) { send(B, { t: "trade", closed: true, done: true }); toast(B, "Trade complete."); pushMe(B); }
      }
    } else pushTrade(k);
  } else if (t === "tradeCancel") cancelTrade(p.id);
}

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json", ".map": "application/json",
};
function serveFile(urlPath: string, res: http.ServerResponse) {
  let rel = decodeURIComponent(urlPath.split("?")[0]);
  if (rel === "/") rel = "/index.html";
  const abs = rel.startsWith("/three/")
    ? path.join(ROOT, "node_modules", "three", rel.slice("/three/".length))
    : path.join(ROOT, "public", rel);
  const rootA = rel.startsWith("/three/") ? path.join(ROOT, "node_modules", "three") : path.join(ROOT, "public");
  if (!abs.startsWith(rootA)) { res.writeHead(403); res.end(); return; }
  fs.readFile(abs, (err, buf) => {
    if (err) { res.writeHead(404); res.end("not found"); return; }
    res.writeHead(200, { "Content-Type": MIME[path.extname(abs)] || "application/octet-stream", "Cache-Control": "no-cache" });
    res.end(buf);
  });
}
const server = http.createServer((req, res) => serveFile(req.url || "/", res));
const wss = new WebSocketServer({ server, path: "/ws" });
wss.on("connection", (ws) => {
  let me: Player | undefined;
  ws.on("message", (raw) => {
    let m: Record<string, unknown>;
    try { m = JSON.parse(String(raw)); } catch { return; }
    if (!me) {
      if (m.t === "join") join(ws, String(m.name || ""));
      me = [...players.values()].find(p => p.ws === ws);
      return;
    }
    handle(me, m);
  });
  ws.on("close", () => {
    if (!me) return;
    cancelTrade(me.id, me.name + " stepped away.");
    names.delete(me.name.toLowerCase());
    players.delete(me.id);
    publicChat("System", me.name + " left Clermont.", "system");
  });
});
setInterval(tick, TICK);
setInterval(() => {
  const raw = JSON.stringify({ t: "state", ...snapshot() });
  for (const p of players.values()) if (p.ws.readyState === WebSocket.OPEN) p.ws.send(raw);
}, 80);
server.listen(PORT, () => {
  console.log("Rune Mommy 3D on http://localhost:" + PORT);
  console.log("Shops loaded: " + shops.map(s => s.name).join(", "));
});
