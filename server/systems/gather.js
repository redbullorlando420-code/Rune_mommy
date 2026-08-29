import { dist } from '../../shared/constants.js';
import { NODES, rollDrops, skillLevel, recipes as recipeTable, item } from '../../shared/catalog.js';
import { addItem, canFit, removeItem, countOf } from './inventory.js';
import { gainXp } from './combat.js';
import { T } from '../../shared/tiles.js';
import { tileAt } from '../../shared/worldmap.js';

export function startGather(world, player, eid) {
  const e = world.entities.get(eid);
  if (!e || e.kind !== 'node') return 'not a resource';
  if (e.depleted || e.alive === false) return 'nothing left — wait';
  const def = NODES[e.type];
  if (!def) return 'not a resource';
  const lv = skillLevel(player, def.skill);
  if (lv < def.level) return `need ${def.skill} ${def.level}`;
  player.target = eid;
  player.path = [];
  player.action = { type: 'gather', id: eid, start: Date.now(), time: def.timeMs * gatherTimeMult(lv) };
  return null;
}

function gatherTimeMult(level) {
  return Math.max(0.55, 1 - (level - 1) * 0.04);
}

export function tickGather(world, dt) {
  const now = Date.now();
  for (const p of world.players.values()) {
    const act = p.action;
    if (!act || act.type !== 'gather') continue;
    const e = world.entities.get(act.id);
    if (!e || e.kind !== 'node' || e.depleted || e.alive === false) { p.action = null; continue; }
    if (dist(p, e) > 1.7) {
      p.action = null;
      continue;
    }
    p.path = [];
    if (now - act.start < act.time) continue;
    finishGather(world, p, e);
  }

  for (const e of world.entities.values()) {
    if (e.kind !== 'node') continue;
    if ((e.depleted || e.alive === false) && now >= (e.respawnAt || (e.depletedAt + (e.respawnMs || 14000)))) {
      e.depleted = false;
      e.alive = true;
      e.hp = e.maxHp || 1;
    }
  }

  for (const p of world.players.values()) {
    const act = p.action;
    if (!act || act.type !== 'craft') continue;
    if (now - act.start < act.time) continue;
    finishCraft(world, p, act.recipe);
  }
}

function finishGather(world, player, e) {
  const def = NODES[e.type];
  const loot = rollDrops(e.type);
  const lv = skillLevel(player, def.skill);
  if (lv >= 5 && Math.random() < 0.12) {
    for (const d of loot) d.qty += 1;
  }
  for (const d of loot) {
    if (!canFit(player.inv, d.id, d.qty)) {
      world.to(player, { t: 'notify', p: { text: 'Pack is full.', kind: 'warn' } });
      player.action = null;
      return;
    }
    addItem(player.inv, d.id, d.qty);
    const it = item(d.id);
    world.to(player, { t: 'notify', p: { text: `Gathered ${d.qty} ${it?.name || d.id}.`, kind: 'loot' } });
  }
  gainXp(world, player, def.skill, def.xp);
  e.depleted = true;
  e.alive = false;
  e.depletedAt = Date.now();
  e.respawnAt = Date.now() + (def.respawnMs || e.respawnMs || 14000);
  player.action = null;
  world.sendInv(player);
}

export function startCraft(world, player, recipeId) {
  const rec = recipeTable()?.[recipeId];
  if (!rec) return 'unknown recipe';
  if (tileAt(world.map, player.x, player.y) !== T.SHRINE && dist(player, { x: 55.5, y: 21.5 }) > 2.2) {
    return 'stand at the Binding Shrine';
  }
  const lv = skillLevel(player, rec.skill);
  if (lv < rec.level) return `need Binding ${rec.level}`;
  for (const inp of rec.inputs) {
    if (countOf(player.inv, inp.id) < inp.qty) return `need ${inp.qty} ${item(inp.id)?.name || inp.id}`;
  }
  if (!canFit(player.inv, rec.output.id, rec.output.qty)) return 'inventory full';
  player.path = [];
  player.action = { type: 'craft', recipe: recipeId, start: Date.now(), time: rec.timeMs };
  world.to(player, { t: 'notify', p: { text: `Binding ${rec.name}…`, kind: 'craft' } });
  return null;
}

function finishCraft(world, player, recipeId) {
  const rec = recipeTable()?.[recipeId];
  player.action = null;
  if (!rec) return;
  for (const inp of rec.inputs) {
    if (countOf(player.inv, inp.id) < inp.qty) {
      world.to(player, { t: 'notify', p: { text: 'Missing materials.', kind: 'warn' } });
      return;
    }
  }
  for (const inp of rec.inputs) removeItem(player.inv, inp.id, inp.qty);
  addItem(player.inv, rec.output.id, rec.output.qty);
  gainXp(world, player, rec.skill, rec.xp);
  const out = item(rec.output.id);
  world.to(player, { t: 'notify', p: { text: `Bound ${rec.output.qty} ${out?.name}.`, kind: 'craft' } });
  world.to(player, { t: 'craft_ok', p: { recipe: recipeId } });
  world.sendInv(player);
}
