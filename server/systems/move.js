/** Click-to-walk: A* on the authoritative grid, then tick along the path. */
import { dist, ACTION } from '../../shared/constants.js';
import { astar, nearestWalkable } from '../../shared/pathfinding.js';
import { tickMove, moveToward } from './movement.js';

export { tickMove, moveToward };

export function setPath(world, player, x, y) {
  const w = world.map.w, h = world.map.h;
  const start = nearestWalkable(world.map.walk, w, h, player.x, player.y);
  const goal = nearestWalkable(world.map.walk, w, h, x, y);
  const path = astar(world.map.walk, w, h, start.x, start.y, goal.x, goal.y);
  if (!path.length) {
    player.path = [];
    return false;
  }
  if (path.length > 1 && dist(player, path[0]) < 0.35) path.shift();
  player.path = path;
  return true;
}

export function onMove(world, player, payload) {
  const x = Number(payload?.x);
  const y = Number(payload?.y);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return;
  player.intent = null;
  player.channel = null;
  player.target = null;
  player.action = ACTION.IDLE;
  setPath(world, player, x, y);
  if (player.path?.length) player.action = ACTION.WALK;
}

export function walkTo(world, player, x, y) {
  return setPath(world, player, x, y);
}
