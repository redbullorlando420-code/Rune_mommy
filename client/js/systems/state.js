import { lerp, WALK_SPEED } from '/shared/constants.js';
import { astar, nearestWalkable } from '/shared/pathfinding.js';

export class ClientState {
  constructor() {
    this.you = null;
    this.me = null;
    this.players = [];
    this.entities = [];
    this.remote = new Map();
    this.eremo = new Map();
    this.walk = null;
    this.w = 0;
    this.h = 0;
    this.pois = [];
    this.zone = null;
    this.inv = [];
    this.equip = {};
    this.bank = [];
    this.skills = {};
    this.localPath = [];
    this.dest = null;
    this.snap = null;
  }

  welcome(p) {
    this.snap = p;
    this.you = p.you;
    this.w = p.w; this.h = p.h;
    this.walk = p.walk instanceof Uint8Array ? p.walk : Uint8Array.from(p.walk);
    this.pois = p.pois;
    this.zone = p.zone;
    this.applyMe(p.me);
    this.applyDelta(p);
    const me = this.remote.get(this.you);
    if (me) { me.x = p.me.x; me.y = p.me.y; me.tx = p.me.x; me.ty = p.me.y; }
  }

  applyMe(me) {
    this.me = Object.assign(this.me || {}, me);
    if (me.inv) this.inv = me.inv;
    if (me.equip) this.equip = me.equip;
    if (me.bank) this.bank = me.bank;
    if (me.skills) this.skills = me.skills;
  }

  applyDelta(p) {
    this.players = p.players || this.players;
    this.entities = p.entities || this.entities;
    const seen = new Set();
    for (const pl of this.players) {
      seen.add(pl.id);
      let r = this.remote.get(pl.id);
      if (!r) {
        r = { ...pl, tx: pl.x, ty: pl.y };
        this.remote.set(pl.id, r);
      } else {
        r.tx = pl.x; r.ty = pl.y;
        r.name = pl.name; r.hp = pl.hp; r.maxHp = pl.maxHp; r.hue = pl.hue;
        r.action = pl.action; r.walking = pl.walking; r.dir = pl.dir;
        r.id = pl.id;
      }
      if (pl.id === this.you && Math.hypot(r.x - pl.x, r.y - pl.y) > 1.8) {
        r.x = pl.x; r.y = pl.y;
        this.localPath = [];
      }
    }
    for (const id of [...this.remote.keys()]) if (!seen.has(id)) this.remote.delete(id);

    const eseen = new Set();
    for (const e of this.entities) {
      eseen.add(e.id);
      let r = this.eremo.get(e.id);
      if (!r) {
        r = { ...e, tx: e.x, ty: e.y };
        this.eremo.set(e.id, r);
      } else {
        Object.assign(r, e, { x: r.x, y: r.y, tx: e.x, ty: e.y });
      }
    }
    for (const id of [...this.eremo.keys()]) if (!eseen.has(id)) this.eremo.delete(id);
  }

  tick(dt) {
    const k = 1 - Math.pow(0.00035, dt / 1000);
    for (const r of this.remote.values()) {
      if (r.id === this.you && this.localPath.length) {
        this.advanceLocal(r, dt);
        continue;
      }
      r.x = lerp(r.x, r.tx, k);
      r.y = lerp(r.y, r.ty, k);
    }
    for (const r of this.eremo.values()) {
      r.x = lerp(r.x, r.tx, k);
      r.y = lerp(r.y, r.ty, k);
    }
  }

  clickMove(x, y) {
    const me = this.remote.get(this.you);
    if (!me || !this.walk) return null;
    const start = nearestWalkable(this.walk, this.w, this.h, me.x, me.y);
    const goal = nearestWalkable(this.walk, this.w, this.h, x, y);
    const path = astar(this.walk, this.w, this.h, start.x, start.y, goal.x, goal.y);
    this.localPath = path;
    this.dest = { x: goal.x + 0.5, y: goal.y + 0.5 };
    me.walking = true;
    return this.dest;
  }

  advanceLocal(me, dt) {
    let remain = WALK_SPEED * (dt / 1000);
    while (remain > 0 && this.localPath.length) {
      const wp = this.localPath[0];
      const d = Math.hypot(wp.x - me.x, wp.y - me.y);
      if (d < 0.05) { this.localPath.shift(); continue; }
      const step = Math.min(remain, d);
      me.x += ((wp.x - me.x) / d) * step;
      me.y += ((wp.y - me.y) / d) * step;
      me.walking = true;
      remain -= step;
      if (step >= d - 0.001) this.localPath.shift();
    }
    if (!this.localPath.length) { me.walking = false; this.dest = null; }
  }

  mePos() { return this.remote.get(this.you) || this.me; }

  drawState() {
    return {
      players: [...this.remote.values()],
      entities: [...this.eremo.values()],
    };
  }
}
