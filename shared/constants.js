/** One source of truth for Rune Mommy. Imported by server and client. */

export const TICK_RATE = 20;
export const TICK_MS = 1000 / TICK_RATE;
export const TILE = 48;
export const MAP_W = 44;
export const MAP_H = 34;
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
export const PORT = Number(process.env.PORT || 8080);
export const MAX_PLAYERS = 48;
export const SPAWN = { x: 18.5, y: 10.5 };
export const NAME_RE = /^[A-Za-z][A-Za-z0-9 _-]{1,15}$/;

export const CHANNELS = Object.freeze({
  GLOBAL: 'global',
  LOCAL: 'local',
  SYSTEM: 'system',
});

export const EQUIP_SLOTS = Object.freeze(['weapon', 'armor', 'charm']);
