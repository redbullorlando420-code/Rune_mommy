import { dist, SPAWN, xpToLevel } from '../../shared/constants.js';
import { MOBS, item, playerStats, rollDrops, skillLevel } from '../../shared/catalog.js';
import { spawnGround } from './inventory.js';
import { moveToward } from './movement.js';

export function startAttack(world, player, eid) {
  const e = world.entities.get(eid);
  if (!e || e.kind !== 'mob' || e.dead || e.alive === false) return 'no target';
  player.target = eid;
  player.action = { type: 'attack', id: eid };
  player.path = [];
  return null;
}

function weaponOf(player) {
  const id = player.equip.weapon;
  return id ? item(id) : { atk: 0, style: 'melee', range: 1.35, speed: 1.6 };
}

export function tickCombat(world, dt) {
  const now = Date.now();
  for (const p of world.players.values()) {
    if (p.hp <= 0) {
      p.deadFor = (p.deadFor || 0) + dt;
      if (p.deadFor > 2500) respawnPlayer(world, p);
      continue;
    }
    if (p.buff && p.buff.until < now) p.buff = null;
    const act = p.action;
    if (!act || (act !== 'attack' && act.type !== 'attack')) continue;
    const e = world.entities.get(p.target);
    if (!e || e.kind !== 'mob' || e.dead || e.alive === false) {
      p.action = null;
      p.target = null;
      continue;
    }
    const wpn = weaponOf(p);
    const range = wpn.range || 1.4;
    const d = dist(p, e);
    if (d > range) {
      moveToward(world, p, e.x, e.y, 3.2, dt);
      continue;
    }
    p.path = [];
    if (now < (p.nextSwing || 0)) continue;
    const cd = Math.max(700, (wpn.speed || 1.5) * 900);
    p.nextSwing = now + cd;
    const stats = playerStats(p);
    const def = MOBS[e.type]?.def || 0;
    const raw = stats.atk + (wpn.atk || 0) * 0.25 + Math.random() * 4;
    const dmg = Math.max(1, Math.round(raw - def * 0.7 + (Math.random() * 3 - 1)));
    applyDamage(world, e, dmg, p);
    world.float(e.x, e.y, `-${dmg}`, wpn.style === 'magic' ? '#c77dff' : '#ff6b6b', p.id);
    gainXp(world, p, 'combat', 6 + Math.floor(dmg * 0.2));
  }

  for (const e of world.entities.values()) {
    if (e.kind !== 'mob') continue;
    tickMob(world, e, dt, now);
  }
}

function applyDamage(world, e, dmg, from) {
  e.hp -= dmg;
  e.aggro = from.id;
  e.lastHit = Date.now();
  if (e.hp <= 0) killMob(world, e, from);
}

function killMob(world, e, killer) {
  e.dead = true;
  e.alive = false;
  e.hp = 0;
  e.deadAt = Date.now();
  e.diedAt = e.deadAt;
  const def = MOBS[e.type];
  if (killer) gainXp(world, killer, 'combat', def.xp || 16);
  const loot = rollDrops(e.type);
  for (const drop of loot) spawnGround(world, e.x, e.y, drop.id, drop.qty);
  world.broadcast({ t: 'notify', p: { text: `${killer?.name || 'Someone'} felled a ${def.name}.`, kind: 'combat' } });
}

function tickMob(world, e, dt, now) {
  const def = MOBS[e.type];
  if (!def) return;
  if (e.dead || e.alive === false) {
    if (now - (e.deadAt || e.diedAt || 0) > def.respawnMs) {
      e.dead = false;
      e.alive = true;
      e.hp = e.maxHp;
      e.x = e.spawnX;
      e.y = e.spawnY;
      e.aggro = null;
    }
    return;
  }
  let target = e.aggro ? world.players.get(e.aggro) : null;
  if (target && (target.hp <= 0 || dist(e, target) > def.leash)) {
    e.aggro = null;
    target = null;
  }
  if (!target) {
    let best = null, bestD = def.aggro;
    for (const p of world.players.values()) {
      if (p.hp <= 0) continue;
      const d = dist(e, p);
      if (d < bestD) { bestD = d; best = p; }
    }
    if (best) { e.aggro = best.id; target = best; }
  }
  if (!target) {
    moveToward(world, e, e.spawnX, e.spawnY, def.speed * 0.6, dt);
    e.hp = Math.min(e.maxHp, e.hp + dt * 0.004);
    return;
  }
  const d = dist(e, target);
  if (d > def.range) {
    moveToward(world, e, target.x, target.y, def.speed, dt);
    return;
  }
  if (now < (e.nextSwing || 0)) return;
  e.nextSwing = now + def.cooldown;
  const pst = playerStats(target);
  const dmg = Math.max(1, Math.round(def.atk + Math.random() * 3 - pst.def * 0.55));
  target.hp -= dmg;
  world.float(target.x, target.y, `-${dmg}`, '#ffa8a8', target.id);
  if (target.hp <= 0) {
    target.hp = 0;
    target.path = [];
    target.action = null;
    target.deadFor = 0;
    world.to(target, { t: 'notify', p: { text: 'You fall. The hearth pulls you back.', kind: 'death' } });
  }
}

export function respawnPlayer(world, p) {
  p.x = SPAWN.x;
  p.y = SPAWN.y;
  const st = playerStats(p);
  p.maxHp = st.maxHp;
  p.hp = Math.max(12, Math.floor(st.maxHp * 0.6));
  p.deadFor = 0;
  p.path = [];
  p.action = null;
  p.target = null;
  world.to(p, { t: 'notify', p: { text: 'You wake beside the First Fire.', kind: 'system' } });
}

export function gainXp(world, player, skill, amount) {
  if (!player.skills[skill]) player.skills[skill] = { xp: 0 };
  const rec = player.skills[skill];
  if (typeof rec === 'number') player.skills[skill] = { xp: rec };
  const before = xpToLevel(player.skills[skill].xp).level;
  player.skills[skill].xp += amount;
  const after = xpToLevel(player.skills[skill].xp);
  const st = playerStats(player);
  const hpFrac = player.hp / Math.max(1, player.maxHp);
  player.maxHp = st.maxHp;
  player.hp = Math.min(st.maxHp, Math.max(1, Math.round(st.maxHp * hpFrac)));
  world.to(player, { t: 'xp', p: { skill, amount, xp: player.skills[skill].xp, level: after.level, into: after.into, need: after.need } });
  if (after.level > before) {
    player.hp = player.maxHp;
    world.to(player, { t: 'notify', p: { text: `${skillName(skill)} rises to ${after.level}.`, kind: 'level' } });
    world.float(player.x, player.y, `Lv ${after.level}`, '#ffd166', player.id);
  }
}

function skillName(id) {
  return id === 'combat' ? 'Ashen Combat' : id === 'foraging' ? 'Dusk Foraging' : id === 'binding' ? 'Hearth Binding' : id;
}

export { skillLevel };
