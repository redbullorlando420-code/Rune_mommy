/** Data-driven content accessors. Works in Node (fs) and browser (fetch). */

import { xpToLevel } from './constants.js';

export const MOBS = {
  gloom_wolf: {
    id: 'gloom_wolf',
    name: 'Gloom Wolf',
    hp: 42,
    atk: 7,
    def: 2,
    speed: 2.4,
    range: 1.3,
    aggro: 5.2,
    leash: 10,
    xp: 22,
    cooldown: 1400,
    respawnMs: 18000,
    color: '#6d6875',
    size: 0.92,
  },
  ash_imp: {
    id: 'ash_imp',
    name: 'Ash Imp',
    hp: 28,
    atk: 9,
    def: 1,
    speed: 2.1,
    range: 2.6,
    aggro: 4.6,
    leash: 9,
    xp: 18,
    cooldown: 1600,
    respawnMs: 16000,
    color: '#e85d04',
    size: 0.7,
    ranged: true,
  },
  hollow_stag: {
    id: 'hollow_stag',
    name: 'Hollow Stag',
    hp: 120,
    atk: 14,
    def: 5,
    speed: 2.8,
    range: 1.4,
    aggro: 6.5,
    leash: 14,
    xp: 80,
    cooldown: 1300,
    respawnMs: 90000,
    color: '#b8f2e6',
    size: 1.25,
    rare: true,
  },
  dust_raccoon: {
    id: 'dust_raccoon',
    name: 'Dust Raccoon',
    hp: 24,
    atk: 5,
    def: 1,
    speed: 2.6,
    range: 1.2,
    aggro: 4.0,
    leash: 8,
    xp: 12,
    cooldown: 1500,
    respawnMs: 14000,
    color: '#6d4c41',
    size: 0.62,
  },
  bramble_boar: {
    id: 'bramble_boar',
    name: 'Bramble Boar',
    hp: 58,
    atk: 10,
    def: 3,
    speed: 2.2,
    range: 1.35,
    aggro: 5.0,
    leash: 11,
    xp: 28,
    cooldown: 1450,
    respawnMs: 22000,
    color: '#8d6e63',
    size: 1.05,
  },
  dusk_walker: {
    id: 'dusk_walker',
    name: 'Dusk Walker',
    hp: 38,
    atk: 8,
    def: 2,
    speed: 1.55,
    range: 1.25,
    aggro: 4.6,
    leash: 9,
    xp: 16,
    cooldown: 1700,
    respawnMs: 20000,
    color: '#7a8a6a',
    size: 0.96,
  },
  feral_dog: {
    id: 'feral_dog',
    name: 'Feral Dog',
    hp: 22,
    atk: 6,
    def: 1,
    speed: 2.7,
    range: 1.2,
    aggro: 5.4,
    leash: 10,
    xp: 10,
    cooldown: 1200,
    respawnMs: 15000,
    color: '#5c4033',
    size: 0.68,
  },
  road_thug: {
    id: 'road_thug',
    name: 'Road Thug',
    hp: 50,
    atk: 11,
    def: 3,
    speed: 2.5,
    range: 1.4,
    aggro: 5.5,
    leash: 12,
    xp: 30,
    cooldown: 1250,
    respawnMs: 24000,
    color: '#c1121f',
    size: 0.96,
  },
  cinder_hound: {
    id: 'cinder_hound',
    name: 'Cinder Hound',
    hp: 36,
    atk: 12,
    def: 1,
    speed: 3.1,
    range: 1.2,
    aggro: 6.8,
    leash: 13,
    xp: 24,
    cooldown: 1100,
    respawnMs: 17000,
    color: '#9d0208',
    size: 0.78,
  },
  mine_crawler: {
    id: 'mine_crawler',
    name: 'Mine Crawler',
    hp: 72,
    atk: 13,
    def: 5,
    speed: 1.9,
    range: 1.5,
    aggro: 4.8,
    leash: 9,
    xp: 36,
    cooldown: 1500,
    respawnMs: 28000,
    color: '#6c757d',
    size: 1.12,
  },
};

export const NODES = {
  emberwood_tree: {
    id: 'emberwood_tree',
    name: 'Emberwood',
    skill: 'foraging',
    level: 1,
    timeMs: 2400,
    xp: 14,
    respawnMs: 14000,
    uses: 1,
  },
  moonbloom_patch: {
    id: 'moonbloom_patch',
    name: 'Moonbloom',
    skill: 'foraging',
    level: 1,
    timeMs: 2000,
    xp: 12,
    respawnMs: 11000,
    uses: 1,
  },
  iron_outcrop: {
    id: 'iron_outcrop',
    name: 'Iron Vein',
    skill: 'foraging',
    level: 2,
    timeMs: 3200,
    xp: 18,
    respawnMs: 20000,
    uses: 1,
  },
  moon_berry_bush: {
    id: 'moon_berry_bush',
    name: 'Moon Berry Bush',
    skill: 'foraging',
    level: 1,
    timeMs: 1800,
    xp: 10,
    respawnMs: 10000,
    uses: 1,
  },
  wild_mint_patch: {
    id: 'wild_mint_patch',
    name: 'Wild Mint',
    skill: 'foraging',
    level: 1,
    timeMs: 1600,
    xp: 9,
    respawnMs: 9000,
    uses: 1,
  },
  kitchen_stash: {
    id: 'kitchen_stash',
    name: 'Kitchen Cabinets',
    skill: 'foraging',
    level: 1,
    timeMs: 2200,
    xp: 11,
    respawnMs: 24000,
    uses: 1,
  },
  closet_stash: {
    id: 'closet_stash',
    name: 'Bedroom Closet',
    skill: 'foraging',
    level: 1,
    timeMs: 2000,
    xp: 10,
    respawnMs: 24000,
    uses: 1,
  },
  toolbox: {
    id: 'toolbox',
    name: 'Toolbox',
    skill: 'foraging',
    level: 1,
    timeMs: 2400,
    xp: 12,
    respawnMs: 26000,
    uses: 1,
  },
  dumpster: {
    id: 'dumpster',
    name: 'Dumpster',
    skill: 'foraging',
    level: 1,
    timeMs: 2600,
    xp: 10,
    respawnMs: 18000,
    uses: 1,
  },
  med_cabinet: {
    id: 'med_cabinet',
    name: 'Medicine Cabinet',
    skill: 'foraging',
    level: 1,
    timeMs: 2100,
    xp: 13,
    respawnMs: 28000,
    uses: 1,
  },
  scrap_pile: {
    id: 'scrap_pile',
    name: 'Scrap Pile',
    skill: 'foraging',
    level: 1,
    timeMs: 2300,
    xp: 11,
    respawnMs: 16000,
    uses: 1,
  },
  dusk_mushroom_patch: {
    id: 'dusk_mushroom_patch',
    name: 'Dusk Mushrooms',
    skill: 'foraging',
    level: 1,
    timeMs: 1800,
    xp: 10,
    respawnMs: 12000,
    uses: 1,
  },
  honeycomb_hive: {
    id: 'honeycomb_hive',
    name: 'Wild Hive',
    skill: 'foraging',
    level: 2,
    timeMs: 2800,
    xp: 16,
    respawnMs: 22000,
    uses: 1,
  },
  gas_canister: {
    id: 'gas_canister',
    name: 'Fuel Canister',
    skill: 'foraging',
    level: 1,
    timeMs: 2500,
    xp: 12,
    respawnMs: 30000,
    uses: 1,
  },
};

let _items = null;
let _npcs = null;
let _skills = null;
let _drops = null;
let _recipes = null;
let _shops = null;

export async function loadCatalog(readJson) {
  const [items, npcs, skills, drops, recipes, shopsFile, mobsFile] = await Promise.all([
    readJson('items.json'),
    readJson('npcs.json'),
    readJson('skills.json'),
    readJson('drops.json'),
    readJson('recipes.json'),
    readJson('shops.json').catch(() => ({ shops: [] })),
    readJson('mobs.json').catch(() => ({})),
  ]);
  _items = items;
  _npcs = npcs;
  _skills = skills;
  _drops = drops;
  _recipes = recipes;
  _shops = shopsFile;
  if (mobsFile && typeof mobsFile === 'object') {
    for (const [id, def] of Object.entries(mobsFile)) {
      if (def && def.id) MOBS[id] = { ...MOBS[id], ...def };
    }
  }
  for (const s of shopsFile.shops || []) {
    npcs[s.id] = {
      id: s.id,
      name: s.npcName,
      title: s.npcTitle || s.name,
      kind: 'shop',
      color: (s.palette && s.palette[0]) || '#ff4fd8',
      greet: s.greeting || s.blurb,
      lines: [s.blurb, s.address, s.examine].filter(Boolean),
      dialogue: s.dialogue,
      portrait: s.portrait,
      start: s.start,
      shop: (s.stock || []).map((row) => ({
        id: row.itemId,
        stock: 99,
        buy: row.price,
        sell: Math.max(1, Math.floor(row.price * 0.4)),
      })),
    };
  }
  return { items, npcs, skills, drops, recipes, shops: shopsFile };
}

export function items() { return _items; }
export function npcs() { return _npcs; }
export function skills() { return _skills; }
export function drops() { return _drops; }
export function recipes() { return _recipes; }
export function shops() { return _shops; }
export function item(id) { return _items?.[id] || null; }

export function skillLevel(player, skillId) {
  const s = player.skills[skillId] || { xp: 0 };
  return xpToLevel(s.xp).level;
}

export function rollDrops(tableId, rng = Math.random) {
  const table = _drops?.[tableId] || [];
  const out = [];
  for (const row of table) {
    if (rng() <= row.chance) {
      const qty = row.min + Math.floor(rng() * (row.max - row.min + 1));
      if (qty > 0) out.push({ id: row.id, qty });
    }
  }
  return out;
}

export function playerStats(player) {
  const combatLv = skillLevel(player, 'combat');
  let atk = 3 + combatLv;
  let def = 2 + Math.floor(combatLv * 0.6);
  let hp = 40 + combatLv * 6;
  const eq = player.equip || {};
  for (const slot of ['weapon', 'armor', 'charm']) {
    const it = eq[slot] ? item(eq[slot]) : null;
    if (!it) continue;
    atk += it.atk || 0;
    def += it.def || 0;
    hp += it.hp || 0;
  }
  if (player.buff && player.buff.until > Date.now()) {
    atk += player.buff.atk || 0;
  }
  return { atk, def, maxHp: hp };
}
