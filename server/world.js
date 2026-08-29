import { SPAWN, INV_SIZE, BANK_SIZE, hueFromName, uid } from '../shared/constants.js';
import { generateWorld } from '../shared/worldmap.js';
import { MOBS, NODES, npcs as npcTable, playerStats } from '../shared/catalog.js';
import { emptyInv, addItem, serializeInv, tickGround } from './systems/inventory.js';
import { tickMove } from './systems/movement.js';
import { tickCombat } from './systems/combat.js';
import { tickGather } from './systems/gather.js';
import { tickTrade, onDisconnect } from './systems/trade.js';
import { tickCraft } from './systems/craft.js';
import { announce } from './systems/chat.js';
import { pack, S2C } from '../shared/protocol.js';

export class World {
  constructor() {
    this.map = generateWorld();
    this.players = new Map();
    this.entities = new Map();
    this.trades = new Map();
    this.floats = [];
    this.tickN = 0;
    this.npcs = [];
    this.nodes = [];
    this.mobs = [];
    this.shop = [];
    this.bootEntities();
  }

  bootEntities() {
    for (const n of this.map.npcs) {
      const def = npcTable()?.[n.type] || { name: n.type };
      const ent = {
        id: n.type,
        kind: 'npc',
        type: n.type,
        name: def.name,
        title: def.title || '',
        color: def.color || '#c77dff',
        x: n.x,
        y: n.y,
        hp: 1,
        maxHp: 1,
        lines: def.lines ? def.lines.slice() : [],
        greet: def.greet || '',
        npcKind: def.kind || 'flavor',
        shop: def.shop ? def.shop.map((s) => ({ ...s })) : null,
        lineAt: 0,
      };
      this.entities.set(ent.id, ent);
      this.npcs.push(ent);
      if (n.type === 'voss' && ent.shop) this.shop = ent.shop;
    }
    for (const n of this.map.nodes) {
      const id = uid('n');
      const def = NODES[n.type] || { name: n.type, respawnMs: 14000, uses: 1 };
      const ent = {
        id,
        kind: 'node',
        type: n.type,
        name: def.name,
        x: n.x,
        y: n.y,
        depleted: false,
        alive: true,
        respawnAt: 0,
        depletedAt: 0,
        hp: def.uses || 1,
        maxHp: def.uses || 1,
        respawnMs: def.respawnMs || 14000,
      };
      this.entities.set(id, ent);
      this.nodes.push(ent);
    }
    for (const m of this.map.mobs) {
      const id = uid('m');
      const def = MOBS[m.type];
      if (!def) continue;
      const ent = {
        id,
        kind: 'mob',
        type: m.type,
        name: def.name,
        x: m.x,
        y: m.y,
        spawnX: m.x,
        spawnY: m.y,
        hp: def.hp,
        maxHp: def.hp,
        dead: false,
        alive: true,
        aggro: null,
        target: null,
        atk: def.atk,
        def: def.def,
        speed: def.speed,
        range: def.range,
        leash: def.leash,
        xp: def.xp,
        cooldown: def.cooldown,
        respawnMs: def.respawnMs,
        color: def.color,
        size: def.size,
        ranged: !!def.ranged,
        rare: !!def.rare,
        lastSwing: 0,
        diedAt: 0,
        dir: 0,
      };
      this.entities.set(id, ent);
      this.mobs.push(ent);
    }
  }

  addPlayer(ws, name) {
    const id = uid('p');
    const inv = emptyInv(INV_SIZE);
    addItem(inv, 'worn_dirk', 1);
    addItem(inv, 'cloth_wrap', 1);
    addItem(inv, 'hearthbread', 5);
    addItem(inv, 'ember_coin', 80);
    addItem(inv, 'tutor_note', 1);
    const p = {
      id, ws, name,
      x: SPAWN.x + (Math.random() - 0.5) * 0.6,
      y: SPAWN.y + (Math.random() - 0.5) * 0.6,
      dir: 0, path: [], hp: 46, maxHp: 46,
      skills: { combat: { xp: 0 }, foraging: { xp: 0 }, binding: { xp: 0 } },
      inv, bank: emptyInv(BANK_SIZE),
      equip: { weapon: 'worn_dirk', armor: 'cloth_wrap', charm: null },
      action: null, target: null, tradeId: null, intent: null, channel: null, buff: null,
      lastSwing: 0, hue: hueFromName(name), joined: Date.now(), lastChat: 0,
    };
    for (let i = 0; i < inv.length; i++) {
      if (inv[i]?.id === 'worn_dirk') inv[i] = null;
      if (inv[i]?.id === 'cloth_wrap') inv[i] = null;
    }
    const st = playerStats(p);
    p.maxHp = st.maxHp; p.hp = st.maxHp; p.atk = st.atk; p.def = st.def;
    this.players.set(id, p);
    announce(this, `${name} steps into Emberfen Hollow.`);
    return p;
  }

  removePlayer(id) {
    const p = this.players.get(id);
    if (!p) return;
    onDisconnect(this, p);
    this.players.delete(id);
    announce(this, `${p.name} fades from the Hollow.`);
  }

  to(player, msg) {
    if (!player?.ws || player.ws.readyState !== 1) return;
    try { player.ws.send(typeof msg === 'string' ? msg : pack(msg.t, msg.p)); } catch {}
  }

  broadcast(msg) {
    const raw = typeof msg === 'string' ? msg : pack(msg.t, msg.p);
    for (const p of this.players.values()) this.to(p, raw);
  }

  sendInv(player) {
    this.to(player, { t: S2C.INV, p: { inv: serializeInv(player.inv), equip: { ...player.equip } } });
  }

  float(x, y, text, color, toId) {
    this.floats.push({ x, y, text, color, toId, t: Date.now() });
  }

  publicPlayer(p) {
    const act = p.action;
    const action = typeof act === 'string' ? act : (act?.type || (p.path?.length ? 'walk' : 'idle'));
    return {
      id: p.id, name: p.name,
      x: +p.x.toFixed(3), y: +p.y.toFixed(3),
      dir: +((p.dir || 0).toFixed(2)),
      hp: Math.max(0, Math.round(p.hp)), maxHp: p.maxHp, hue: p.hue, action,
      walking: !!(p.path && p.path.length),
    };
  }

  publicEntity(e) {
    if (e.kind === 'mob' && (e.dead || e.alive === false)) {
      return { id: e.id, kind: 'mob', type: e.type, name: e.name, x: e.x, y: e.y, hp: 0, maxHp: e.maxHp, dead: true, alive: false, color: e.color, size: e.size };
    }
    const o = { id: e.id, kind: e.kind, type: e.type, name: e.name, x: +e.x.toFixed(3), y: +e.y.toFixed(3) };
    if (e.kind === 'mob') {
      o.hp = Math.max(0, Math.round(e.hp)); o.maxHp = e.maxHp; o.dead = !!e.dead;
      o.alive = e.alive !== false && !e.dead; o.color = e.color; o.size = e.size;
    }
    if (e.kind === 'node') { o.depleted = !!e.depleted || e.alive === false; o.alive = e.alive !== false && !e.depleted; }
    if (e.kind === 'ground') { o.qty = e.qty; o.item = e.type; }
    if (e.kind === 'npc') { o.color = e.color; o.title = e.title; }
    return o;
  }

  snapshotFor(player) {
    const players = [...this.players.values()].map((p) => this.publicPlayer(p));
    const entities = [...this.entities.values()].map((e) => this.publicEntity(e));
    return {
      t: S2C.WELCOME,
      p: {
        you: player.id, name: player.name, zone: this.map.zone,
        w: this.map.w, h: this.map.h,
        tiles: Array.from(this.map.tiles), walk: Array.from(this.map.walk),
        trees: this.map.trees, rocks: this.map.rocks, lights: this.map.lights,
        props: this.map.props, buildings: this.map.buildings || [], pois: this.map.pois,
        players, entities,
        me: { ...this.publicPlayer(player), skills: player.skills, inv: serializeInv(player.inv), bank: serializeInv(player.bank), equip: { ...player.equip } },
      },
    };
  }

  delta() {
    const players = [...this.players.values()].map((p) => this.publicPlayer(p));
    const entities = [...this.entities.values()].map((e) => this.publicEntity(e));
    const floats = this.floats.splice(0, this.floats.length);
    return { t: S2C.DELTA, p: { n: this.tickN, players, entities, floats } };
  }

  tick(dt) {
    this.tickN++;
    for (const p of this.players.values()) {
      if (p.hp <= 0) continue;
      const act = p.action;
      const atk = act && (act === 'attack' || act.type === 'attack');
      if (!act || atk || (p.path && p.path.length)) tickMove(this, p, dt);
    }
    tickCombat(this, dt);
    tickGather(this, dt);
    tickGround(this, Date.now());
    tickCraft(this);
    if (this.tickN % 10 === 0) tickTrade(this);
    if (this.tickN % 2 === 0) {
      const d = this.delta();
      const raw = pack(d.t, d.p);
      for (const p of this.players.values()) this.to(p, raw);
    }
  }
}

export function createWorld() { return new World(); }

export function findEntity(world, id) {
  if (!id || !world) return null;
  if (world.players.has(id)) return world.players.get(id);
  if (world.entities.has(id)) return world.entities.get(id);
  return null;
}

export function pushFloat(world, x, y, text, color = '#f4d35e', toId) {
  world.float(x, y, text, color, toId);
}
