/** Bind recipes at the shrine. */
import { ACTION, dist, INTERACT_RANGE } from '../../shared/constants.js';
import { S2C } from '../../shared/protocol.js';
import { recipes, skillLevel, item } from '../../shared/catalog.js';
import { T } from '../../shared/tiles.js';
import { tileAt } from '../../shared/worldmap.js';
import { addItem, removeItem, countOf, canFit, serializeInv, spawnGround } from './inventory.js';

export function nearShrine(world, player) {
  const t = tileAt(world.map, player.x, player.y);
  if (t === T.SHRINE) return true;
  const poi = world.map.pois?.find((p) => p.id === 'shrine');
  if (poi && dist(player, poi) <= 2.4) return true;
  const x0 = Math.floor(player.x) - 2, y0 = Math.floor(player.y) - 2;
  for (let y = y0; y <= y0 + 4; y++) {
    for (let x = x0; x <= x0 + 4; x++) {
      if (tileAt(world.map, x + 0.5, y + 0.5) === T.SHRINE) {
        if (Math.hypot(player.x - (x + 0.5), player.y - (y + 0.5)) <= 2.2) return true;
      }
    }
  }
  return false;
}

export function onCraft(world, player, payload) {
  const rec = recipes()?.[payload?.id];
  if (!rec) {
    player.send(S2C.NOTIFY, { text: 'Unknown binding.', kind: 'info' });
    return;
  }
  if (!nearShrine(world, player)) {
    player.send(S2C.NOTIFY, { text: 'Stand at the binding shrine.', kind: 'warn' });
    return;
  }
  if (skillLevel(player, rec.skill || 'binding') < (rec.level || 1)) {
    player.send(S2C.NOTIFY, { text: `Binding ${rec.level} is required.`, kind: 'warn' });
    return;
  }
  for (const inp of rec.inputs) {
    if (countOf(player.inv, inp.id) < inp.qty) {
      player.send(S2C.NOTIFY, { text: `Need ${inp.qty} ${item(inp.id)?.name || inp.id}.`, kind: 'warn' });
      return;
    }
  }
  player.path = [];
  player.intent = null;
  player.action = ACTION.CRAFT;
  player.channel = { type: 'craft', recipe: rec.id, until: Date.now() + (rec.timeMs || 2000) };
  player.send(S2C.NOTIFY, { text: `Binding ${rec.name}…`, kind: 'info' });
}

export function tickCraft(world) {
  const now = Date.now();
  for (const player of world.players.values()) {
    if (!player.channel || player.channel.type !== 'craft') continue;
    if (!nearShrine(world, player)) {
      player.channel = null;
      player.action = ACTION.IDLE;
      player.send(S2C.NOTIFY, { text: 'You stepped away from the shrine.', kind: 'info' });
      continue;
    }
    if (now < player.channel.until) continue;
    const rec = recipes()?.[player.channel.recipe];
    player.channel = null;
    player.action = ACTION.IDLE;
    if (!rec) continue;
    for (const inp of rec.inputs) {
      if (countOf(player.inv, inp.id) < inp.qty) {
        player.send(S2C.NOTIFY, { text: 'The ingredients scattered.', kind: 'warn' });
        return;
      }
    }
    for (const inp of rec.inputs) removeItem(player.inv, inp.id, inp.qty);
    const out = rec.output;
    if (canFit(player.inv, out.id, out.qty) && addItem(player.inv, out.id, out.qty)) {
      player.send(S2C.NOTIFY, { text: `Bound ${out.qty} ${item(out.id)?.name || out.id}.`, kind: 'loot' });
    } else {
      spawnGround(world, player.x, player.y, out.id, out.qty);
      player.send(S2C.NOTIFY, { text: 'No room — the binding falls to stone.', kind: 'info' });
    }
    player.addXp('binding', rec.xp || 22);
    player.send(S2C.CRAFT_OK, { id: rec.id });
    player.send(S2C.INV, { inv: serializeInv(player.inv) });
  }
}

export { INTERACT_RANGE };
