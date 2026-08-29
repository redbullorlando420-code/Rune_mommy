/** Deterministic Clermont + Emberfen. 72x56 tiles, 10 shake shops, wilds, mine. */
import { MAP_W as W, MAP_H as H } from './constants.js';
import { T, TILE_WALK } from './tiles.js';

function mulberry32(a) {
  return function () {
    let t = (a += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function fill(arr, v) { for (let i = 0; i < arr.length; i++) arr[i] = v; }
function setRect(g, x, y, w, h, v) {
  for (let yy = y; yy < y + h; yy++) {
    for (let xx = x; xx < x + w; xx++) {
      if (xx >= 0 && yy >= 0 && xx < W && yy < H) g[yy * W + xx] = v;
    }
  }
}
function stamp(g, x, y, v) {
  if (x >= 0 && y >= 0 && x < W && y < H) g[y * W + x] = v;
}
function line(g, x0, y0, x1, y1, v, jitter, rng) {
  const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
  for (let i = 0; i <= n; i++) {
    const t = n === 0 ? 0 : i / n;
    let x = Math.round(x0 + (x1 - x0) * t);
    let y = Math.round(y0 + (y1 - y0) * t);
    if (jitter && rng() < 0.35) {
      x += rng() < 0.5 ? -1 : 1;
      y += rng() < 0.5 ? 0 : rng() < 0.5 ? -1 : 1;
    }
    stamp(g, x, y, v);
    stamp(g, x + 1, y, v);
  }
}

/** Ten Clermont shake shops. North row = Hwy 50, south row = Johns Lake. */
export const SHOP_LAYOUT = [
  { id: 'baskin', x: 4, y: 5, w: 4, h: 4, hgt: 3.4, flagship: false, palette: ['#e91e8c', '#3b2a1a', '#4aa3ff'] },
  { id: 'brusters', x: 12, y: 5, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#d62828', '#ffffff', '#4a90d9'] },
  { id: 'shake_bar', x: 20, y: 5, w: 5, h: 4, hgt: 4.2, flagship: true, palette: ['#ff4fd8', '#5af0ff', '#1a081c'] },
  { id: 'steak_n_shake', x: 28, y: 5, w: 4, h: 4, hgt: 3.3, flagship: false, palette: ['#f5d547', '#1a1a1a', '#c0392b'] },
  { id: 'ritters', x: 36, y: 5, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#ff8fab', '#fff4e6', '#5b2c6f'] },
  { id: 'dairy_queen', x: 6, y: 40, w: 4, h: 4, hgt: 3.4, flagship: false, palette: ['#e31837', '#003da5', '#ffffff'] },
  { id: 'five_guys', x: 14, y: 40, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#d32f2f', '#ffffff', '#111111'] },
  { id: 'culvers', x: 22, y: 40, w: 4, h: 4, hgt: 3.3, flagship: false, palette: ['#1e4b8e', '#ffffff', '#c8102e'] },
  { id: 'mcdonalds', x: 30, y: 40, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#ffc72c', '#da291c', '#27251f'] },
  { id: 'wendys', x: 38, y: 40, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#e41c38', '#1c1c1c', '#f7a81b'] },
];

export function generateWorld() {
  const rng = mulberry32(0x524d4d31);
  const tiles = new Uint8Array(W * H);
  const block = new Uint8Array(W * H);
  fill(tiles, T.GRASS);

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const n = rng();
      if (n < 0.08) tiles[y * W + x] = T.GRASS_D;
      else if (n < 0.14) tiles[y * W + x] = T.TALL;
      else if (n < 0.17) tiles[y * W + x] = T.MOSS;
      else if (n < 0.19) tiles[y * W + x] = T.FLOWER;
    }
  }

  // west water / Johns Lake
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const shore = 4 + Math.sin(y * 0.35) * 1.4;
      if (x < shore) tiles[y * W + x] = x < shore - 1.8 ? T.WATER_D : T.WATER;
      else if (x < shore + 1.2) tiles[y * W + x] = T.SAND;
    }
  }

  // Hwy 50
  setRect(tiles, 3, 4, 44, 3, T.ROAD);
  setRect(tiles, 3, 9, 44, 2, T.PATH);

  // Johns Lake strip road
  setRect(tiles, 4, 38, 42, 3, T.ROAD);
  setRect(tiles, 4, 44, 42, 1, T.PATH);

  // plaza / spawn
  setRect(tiles, 16, 14, 14, 8, T.FLAG);
  setRect(tiles, 20, 16, 6, 5, T.NEON);
  stamp(tiles, 22, 18, T.HEARTH);
  stamp(tiles, 23, 18, T.HEARTH);

  // ash wilds between plaza and Johns Lake
  for (let y = 24; y < 38; y++) {
    for (let x = 10; x < 44; x++) {
      if (rng() < 0.45) tiles[y * W + x] = rng() < 0.55 ? T.ASH : T.DIRT;
    }
  }

  // Emberfen east copse
  for (let y = 8; y < 30; y++) {
    for (let x = 48; x < W - 1; x++) {
      if (rng() < 0.4) tiles[y * W + x] = T.LEAVES;
      if (rng() < 0.12) tiles[y * W + x] = T.MOSS;
    }
  }

  // Agate Mine SE
  setRect(tiles, 56, 44, 12, 8, T.STONE);
  setRect(tiles, 58, 46, 8, 5, T.DIRT);

  line(tiles, 22, 22, 22, 38, T.PATH, true, rng);
  line(tiles, 23, 18, 52, 16, T.PATH, true, rng);
  line(tiles, 38, 22, 58, 46, T.DIRT, true, rng);
  line(tiles, 8, 18, 16, 16, T.PATH, false, rng);

  // Emberfen second town
  setRect(tiles, 50, 12, 5, 5, T.WOOD);
  stamp(tiles, 52, 14, T.RUG);
  setRect(tiles, 57, 12, 6, 5, T.WOOD);
  stamp(tiles, 59, 14, T.RUG);
  setRect(tiles, 53, 19, 5, 4, T.STONE);
  stamp(tiles, 55, 20, T.SHRINE);
  stamp(tiles, 56, 20, T.SHRINE);

  // dock west of plaza
  setRect(tiles, 6, 16, 4, 3, T.DOCK);

  for (let x = 0; x < W; x++) {
    block[0 * W + x] = 1;
    block[1 * W + x] = 1;
    block[(H - 1) * W + x] = 1;
    block[(H - 2) * W + x] = 1;
  }
  for (let y = 0; y < H; y++) {
    block[y * W + 0] = 1;
    block[y * W + (W - 1)] = 1;
    block[y * W + (W - 2)] = 1;
  }

  const trees = [];
  const rocks = [];
  const lights = [];
  const props = [];
  const buildings = [];

  function canTree(x, y) {
    if (x < 2 || y < 2 || x >= W - 2 || y >= H - 2) return false;
    const t = tiles[y * W + x];
    if ([T.WATER, T.WATER_D, T.WOOD, T.FLAG, T.HEARTH, T.SHRINE, T.DOCK, T.STONE, T.RUG, T.PATH, T.ROAD, T.NEON].includes(t)) return false;
    if (block[y * W + x]) return false;
    return true;
  }

  for (let i = 0; i < 90; i++) {
    const x = 48 + (rng() * 20) | 0;
    const y = 6 + (rng() * 22) | 0;
    if (!canTree(x, y)) continue;
    block[y * W + x] = 1;
    trees.push({ x, y, variant: (rng() * 3) | 0, hue: 120 + rng() * 40 });
  }
  for (let i = 0; i < 20; i++) {
    const x = 10 + (rng() * 30) | 0;
    const y = 26 + (rng() * 10) | 0;
    if (!canTree(x, y)) continue;
    block[y * W + x] = 1;
    trees.push({ x, y, variant: 3, hue: 25 + rng() * 20 });
  }
  for (let i = 0; i < 16; i++) {
    const x = 56 + (rng() * 12) | 0;
    const y = 44 + (rng() * 8) | 0;
    if (block[y * W + x]) continue;
    block[y * W + x] = 1;
    rocks.push({ x, y, variant: (rng() * 2) | 0 });
  }

  function hutWalls(x, y, w, h, pal) {
    for (let xx = x; xx < x + w; xx++) {
      block[y * W + xx] = 1;
      const southDoor = xx === x + ((w / 2) | 0);
      if (!southDoor) block[(y + h - 1) * W + xx] = 1;
    }
    for (let yy = y; yy < y + h; yy++) {
      block[yy * W + x] = 1;
      block[yy * W + (x + w - 1)] = 1;
    }
    props.push({ kind: 'hut', x, y, w, h });
    buildings.push({ kind: 'hut', x, y, w, h, hgt: 3.2, palette: pal || ['#4a2018', '#2a1c14', '#d4a017'] });
  }
  hutWalls(50, 12, 5, 5, ['#6b3fa0', '#2a1830', '#c77dff']);
  hutWalls(57, 12, 6, 5, ['#f4a261', '#3a2010', '#e76f51']);

  const npcs = [
    { type: 'maera', x: 52.2, y: 17.4 },
    { type: 'voss', x: 59.4, y: 17.3 },
    { type: 'nima', x: 8.2, y: 17.6 },
    { type: 'brin', x: 28.6, y: 28.4 },
    { type: 'selva', x: 55.6, y: 22.3 },
    { type: 'kesh', x: 20.4, y: 19.6 },
    { type: 'oren', x: 22.6, y: 12.4 },
    { type: 'tavi', x: 36.4, y: 33.5 },
    { type: 'rook', x: 24.5, y: 46.4 },
    { type: 'lila', x: 18.6, y: 17.4 },
    { type: 'yara', x: 32.4, y: 32.2 },
  ];

  for (const s of SHOP_LAYOUT) {
    setRect(tiles, s.x, s.y, s.w, s.h, s.flagship ? T.NEON : T.WOOD);
    for (let yy = s.y; yy < s.y + s.h; yy++) {
      for (let xx = s.x; xx < s.x + s.w; xx++) {
        const southDoor = yy === s.y + s.h - 1 && xx === s.x + ((s.w / 2) | 0);
        if (!southDoor) block[yy * W + xx] = 1;
      }
    }
    buildings.push({
      id: s.id, kind: 'shop', x: s.x, y: s.y, w: s.w, h: s.h, hgt: s.hgt,
      palette: s.palette, flagship: !!s.flagship,
    });
    npcs.push({ type: s.id, x: s.x + s.w / 2, y: s.y + s.h + 0.55 });
    lights.push({
      x: s.x + s.w / 2, y: s.y + s.h / 2, r: s.flagship ? 6 : 3.4,
      color: s.flagship ? [255, 80, 216] : [255, 170, 80], flicker: s.flagship ? 1.1 : 0.5,
    });
  }

  buildings.push({ kind: 'mine', x: 58, y: 46, w: 8, h: 5, hgt: 2.4, palette: ['#4a4e56', '#2a2c30', '#8a8a9a'] });

  for (let i = 0; i < 18; i++) {
    const x = 12 + (rng() * 28) | 0;
    const y = 26 + (rng() * 10) | 0;
    if (block[y * W + x]) continue;
    const t = tiles[y * W + x];
    if (t === T.WATER || t === T.WATER_D) continue;
    block[y * W + x] = 1;
    rocks.push({ x, y, variant: (rng() * 2) | 0 });
  }

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const t = tiles[y * W + x];
      if (!TILE_WALK[t]) block[y * W + x] = 1;
    }
  }

  lights.push({ x: 22.5, y: 18.5, r: 6.2, color: [255, 140, 50], flicker: 1 });
  lights.push({ x: 55.5, y: 20.5, r: 4.0, color: [180, 120, 255], flicker: 0.8 });
  lights.push({ x: 8.5, y: 17.5, r: 2.8, color: [80, 180, 220], flicker: 0.4 });
  lights.push({ x: 24.5, y: 32.5, r: 3.0, color: [255, 90, 40], flicker: 1.2 });
  lights.push({ x: 62, y: 48, r: 3.2, color: [180, 180, 200], flicker: 0.5 });

  const walk = new Uint8Array(W * H);
  for (let i = 0; i < walk.length; i++) walk[i] = block[i] ? 0 : 1;

  const pois = [
    { id: 'plaza', name: 'Clermont Square', x: 22.5, y: 18.5 },
    { id: 'shake_row', name: 'Shake Row / Hwy 50', x: 22.5, y: 10 },
    { id: 'johns_lake', name: 'Johns Lake Strip', x: 24, y: 45 },
    { id: 'tutor', name: "Maera's Hut", x: 52, y: 18 },
    { id: 'keeper', name: "Voss's Hall", x: 59.5, y: 18 },
    { id: 'shrine', name: 'Binding Shrine', x: 55.5, y: 21.5 },
    { id: 'dock', name: 'Silt Dock', x: 8, y: 17.5 },
    { id: 'wood', name: 'Emberwood Copse', x: 60, y: 12 },
    { id: 'mine', name: 'Agate Mine', x: 62, y: 48 },
    { id: 'wolves', name: 'Ash Den', x: 28, y: 32 },
    { id: 'imps', name: 'Cinder Circle', x: 16, y: 30 },
    { id: 'walkers', name: 'Walker Drift', x: 28, y: 36 },
    { id: 'strip', name: 'Thug Strip', x: 24, y: 45.5 },
  ];

  const nodes = [
    { type: 'emberwood_tree', x: 54.5, y: 9.5 },
    { type: 'emberwood_tree', x: 61.5, y: 11.5 },
    { type: 'emberwood_tree', x: 64.2, y: 14.4 },
    { type: 'emberwood_tree', x: 58.8, y: 24.2 },
    { type: 'emberwood_tree', x: 50.5, y: 26.6 },
    { type: 'moonbloom_patch', x: 63.2, y: 18.5 },
    { type: 'moonbloom_patch', x: 48.4, y: 20.8 },
    { type: 'moonbloom_patch', x: 12.5, y: 14.5 },
    { type: 'moon_berry_bush', x: 18.2, y: 28.4 },
    { type: 'moon_berry_bush', x: 32.5, y: 30.2 },
    { type: 'wild_mint_patch', x: 10.5, y: 34.2 },
    { type: 'iron_outcrop', x: 60.5, y: 48.5 },
    { type: 'iron_outcrop', x: 64.2, y: 46.8 },
    { type: 'iron_outcrop', x: 58.4, y: 50.4 },
    { type: 'iron_outcrop', x: 36.5, y: 34.5 },
  ];

  const mobs = [
    { type: 'gloom_wolf', x: 26.5, y: 30.5 },
    { type: 'gloom_wolf', x: 30.5, y: 33.2 },
    { type: 'gloom_wolf', x: 22.2, y: 34.4 },
    { type: 'gloom_wolf', x: 34.8, y: 31.8 },
    { type: 'ash_imp', x: 16.5, y: 29.5 },
    { type: 'ash_imp', x: 14.2, y: 32.1 },
    { type: 'ash_imp', x: 19.1, y: 31.8 },
    { type: 'dust_raccoon', x: 40.2, y: 28.5 },
    { type: 'dust_raccoon', x: 8.5, y: 26.4 },
    { type: 'bramble_boar', x: 44.5, y: 34.2 },
    { type: 'bramble_boar', x: 50.2, y: 38.5 },
    { type: 'hollow_stag', x: 66.2, y: 10.5 },
    { type: 'dusk_walker', x: 24.8, y: 36.2 },
    { type: 'dusk_walker', x: 29.4, y: 35.6 },
    { type: 'dusk_walker', x: 33.2, y: 37.1 },
    { type: 'dusk_walker', x: 20.6, y: 37.4 },
    { type: 'road_thug', x: 10.5, y: 45.4 },
    { type: 'road_thug', x: 18.2, y: 45.8 },
    { type: 'road_thug', x: 34.6, y: 45.2 },
    { type: 'cinder_hound', x: 15.4, y: 28.2 },
    { type: 'cinder_hound', x: 18.8, y: 33.6 },
    { type: 'mine_crawler', x: 60.4, y: 47.6 },
    { type: 'mine_crawler', x: 63.8, y: 49.2 },
    { type: 'feral_dog', x: 12.4, y: 26.8 },
    { type: 'feral_dog', x: 41.6, y: 32.4 },
  ];

  return {
    w: W, h: H, tiles, walk, trees, rocks, lights, props, buildings, pois, npcs, nodes, mobs,
    zone: {
      id: 'clermont',
      name: 'Clermont Square',
      blurb: 'Hwy 50 shake row to the north. Johns Lake south. Emberfen and the mine to the east.',
    },
  };
}

export function walkableAt(world, x, y) {
  const tx = Math.floor(x);
  const ty = Math.floor(y);
  if (tx < 0 || ty < 0 || tx >= world.w || ty >= world.h) return false;
  return !!world.walk[ty * world.w + tx];
}

export function tileAt(world, x, y) {
  const tx = Math.floor(x);
  const ty = Math.floor(y);
  if (tx < 0 || ty < 0 || tx >= world.w || ty >= world.h) return T.VOID;
  return world.tiles[ty * world.w + tx];
}
