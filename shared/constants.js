/** One source of truth for Rune Mommy. Imported by server and client. */

export const TICK_RATE = 20;
export const TICK_MS = 1000 / TICK_RATE;
export const TILE = 48;
export const MAP_W = 112;
export const MAP_H = 76;
export const WALK_SPEED = 3.35;
export const PLAYER_RADIUS = 0.32;
export const INTERACT_RANGE = 1.65;
export const ATTACK_MELEE = 1.5;
export const TRADE_RANGE = 3.2;
export const LOCAL_CHAT_RANGE = 9;
export const MAX_NAME = 16;
export const INV_SIZE = 24;
export const BANK_SIZE = 32;
export const GROUND_DESPAWN_MS = 90_000;
export const MAX_CHAT = 160;
export const PORT = Number((typeof process !== 'undefined' && process.env && process.env.PORT) || 8080);
export const MAX_PLAYERS = 48;
export const SPAWN = { x: 28.5, y: 20.5 };
export const NAME_RE = /^[A-Za-z][A-Za-z0-9 _-]{1,15}$/;

export const CHANNELS = Object.freeze({
  GLOBAL: 'global',
  LOCAL: 'local',
  SYSTEM: 'system',
});

export const EQUIP_SLOTS = Object.freeze(['weapon', 'armor', 'charm']);

export const ACTION = Object.freeze({
  IDLE: 'idle',
  WALK: 'walk',
  ATTACK: 'attack',
  GATHER: 'gather',
  CRAFT: 'craft',
  TALK: 'talk',
});

export function xpToLevel(xp) {
  let level = 1;
  let need = 40;
  let remain = xp;
  while (remain >= need && level < 50) {
    remain -= need;
    level += 1;
    need = Math.floor(40 * level * Math.pow(1.12, level - 1));
  }
  return { level, into: remain, need };
}

export function totalXpForLevel(level) {
  let xp = 0;
  for (let l = 1; l < level; l++) {
    xp += Math.floor(40 * l * Math.pow(1.12, l - 1));
  }
  return xp;
}

export function dist(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.hypot(dx, dy);
}

export function clamp(v, a, b) {
  return Math.max(a, Math.min(b, v));
}

export function lerp(a, b, t) {
  return a + (b - a) * t;
}

export function hueFromName(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return h % 360;
}

export function now() {
  return Date.now();
}

export function uid(prefix = 'id') {
  return prefix + '_' + Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-4);
}
