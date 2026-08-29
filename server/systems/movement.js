import { WALK_SPEED, TICK_MS, dist } from '../../shared/constants.js';
import { astar, nearestWalkable } from '../../shared/pathfinding.js';
import { walkableAt } from '../../shared/worldmap.js';

export function setDestination(world, player, x, y) {
  const w = world.map.w, h = world.map.h;
  const start = nearestWalkable(world.map.walk, w, h, player.x, player.y);
  const goal = nearestWalkable(world.map.walk, w, h, x, y);
  const path = astar(world.map.walk, w, h, start.x, start.y, goal.x, goal.y);
  if (!path.length) {
    player.path = [];
    return false;
  }
  // If first waypoint is behind us, drop it
  if (path.length > 1 && dist(player, path[0]) < 0.35) path.shift();
  player.path = path;
  player.action = null;
  player.target = null;
  return true;
}

export function tickMove(world, player, dt) {
  if (!player.path || !player.path.length) return;
  const speed = WALK_SPEED * (dt / 1000);
  let remain = speed;
  while (remain > 0 && player.path.length) {
    const wp = player.path[0];
    const d = dist(player, wp);
    if (d < 0.04) {
      player.path.shift();
      continue;
    }
    const step = Math.min(remain, d);
    player.x += ((wp.x - player.x) / d) * step;
    player.y += ((wp.y - player.y) / d) * step;
    player.dir = Math.atan2(wp.y - player.y, wp.x - player.x);
    remain -= step;
    if (step >= d - 0.001) player.path.shift();
  }
  // Keep inside walkable
  if (!walkableAt(world.map, player.x, player.y)) {
    const n = nearestWalkable(world.map.walk, world.map.w, world.map.h, player.x, player.y);
    player.x = n.x + 0.5;
    player.y = n.y + 0.5;
    player.path = [];
  }
}

export function moveToward(world, ent, tx, ty, speed, dt) {
  const d = Math.hypot(tx - ent.x, ty - ent.y);
  if (d < 0.05) return true;
  const step = speed * (dt / 1000);
  const nx = ent.x + ((tx - ent.x) / d) * Math.min(step, d);
  const ny = ent.y + ((ty - ent.y) / d) * Math.min(step, d);
  if (walkableAt(world.map, nx, ny)) {
    ent.x = nx;
    ent.y = ny;
    ent.dir = Math.atan2(ty - ent.y, tx - ent.x);
  }
  return Math.hypot(tx - ent.x, ty - ent.y) < 0.08;
}

export { TICK_MS };
