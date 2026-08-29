/** Deterministic Clermont town slice. 112x76 tiles, shops, houses, woods, gas, park. */
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
  { id: 'baskin', x: 10, y: 2, w: 4, h: 4, hgt: 3.4, flagship: false, palette: ['#e91e8c', '#3b2a1a', '#4aa3ff'] },
  { id: 'brusters', x: 18, y: 2, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#d62828', '#ffffff', '#4a90d9'] },
  { id: 'shake_bar', x: 26, y: 2, w: 5, h: 4, hgt: 4.2, flagship: true, palette: ['#ff4fd8', '#5af0ff', '#1a081c'] },
  { id: 'steak_n_shake', x: 35, y: 2, w: 4, h: 4, hgt: 3.3, flagship: false, palette: ['#f5d547', '#1a1a1a', '#c0392b'] },
  { id: 'ritters', x: 43, y: 2, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#ff8fab', '#fff4e6', '#5b2c6f'] },
  { id: 'dairy_queen', x: 10, y: 58, w: 4, h: 4, hgt: 3.4, flagship: false, palette: ['#e31837', '#003da5', '#ffffff'] },
  { id: 'five_guys', x: 18, y: 58, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#d32f2f', '#ffffff', '#111111'] },
  { id: 'culvers', x: 26, y: 58, w: 4, h: 4, hgt: 3.3, flagship: false, palette: ['#1e4b8e', '#ffffff', '#c8102e'] },
  { id: 'mcdonalds', x: 34, y: 58, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#ffc72c', '#da291c', '#27251f'] },
  { id: 'wendys', x: 42, y: 58, w: 4, h: 4, hgt: 3.2, flagship: false, palette: ['#e41c38', '#1c1c1c', '#f7a81b'] },
];

export function generateWorld() {
  const rng = mulberry32(0x524d4d32);
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
      const shore = 4 + Math.sin(y * 0.28) * 1.5;
      if (x < shore) tiles[y * W + x] = x < shore - 1.8 ? T.WATER_D : T.WATER;
      else if (x < shore + 1.2) tiles[y * W + x] = T.SAND;
    }
  }

  // Hwy 50
  setRect(tiles, 8, 6, 72, 3, T.ROAD);
  setRect(tiles, 8, 9, 56, 3, T.CONCRETE);

  // Johns Lake strip road
  setRect(tiles, 8, 54, 50, 3, T.ROAD);
  setRect(tiles, 8, 63, 50, 1, T.PATH);

  // plaza / spawn
  setRect(tiles, 20, 16, 18, 10, T.FLAG);
  setRect(tiles, 26, 18, 8, 6, T.NEON);
  stamp(tiles, 28, 20, T.HEARTH);
  stamp(tiles, 29, 20, T.HEARTH);

  // highway to plaza
  setRect(tiles, 27, 12, 4, 5, T.PATH);
  // plaza south to Maple
  setRect(tiles, 37, 26, 3, 7, T.PATH);

  // residential streets
  setRect(tiles, 12, 32, 52, 2, T.ROAD); // Maple
  setRect(tiles, 12, 44, 52, 2, T.ROAD); // Oak
  setRect(tiles, 16, 26, 2, 28, T.ROAD); // Pine
  setRect(tiles, 44, 26, 2, 28, T.ROAD); // Cedar

  // ash lots between Oak and Johns Lake road
  for (let y = 47; y < 54; y++) {
    for (let x = 12; x < 52; x++) {
      if (rng() < 0.5) tiles[y * W + x] = rng() < 0.55 ? T.ASH : T.DIRT;
    }
  }

  // Willow Park
  setRect(tiles, 66, 24, 16, 14, T.GRASS);
  setRect(tiles, 70, 28, 8, 2, T.PATH);
  setRect(tiles, 72, 26, 2, 8, T.PATH);
  for (let y = 24; y < 38; y++) {
    for (let x = 66; x < 82; x++) {
      if (rng() < 0.16) tiles[y * W + x] = T.FLOWER;
      else if (rng() < 0.12) tiles[y * W + x] = T.MOSS;
    }
  }

  // gas station lot
  setRect(tiles, 66, 8, 16, 14, T.CONCRETE);
  setRect(tiles, 68, 9, 6, 5, T.WOOD);
  stamp(tiles, 70, 11, T.RUG);

  // Emberfen copse
  for (let y = 6; y < 46; y++) {
    for (let x = 84; x < W - 1; x++) {
      if (rng() < 0.42) tiles[y * W + x] = T.LEAVES;
      if (rng() < 0.1) tiles[y * W + x] = T.MOSS;
    }
  }

  // Agate Mine SE
  setRect(tiles, 92, 60, 16, 12, T.STONE);
  setRect(tiles, 95, 63, 10, 7, T.DIRT);

  // Emberfen floors before walls
  setRect(tiles, 86, 14, 5, 5, T.WOOD);
  stamp(tiles, 88, 16, T.RUG);
  setRect(tiles, 94, 14, 6, 5, T.WOOD);
  stamp(tiles, 96, 16, T.RUG);
  setRect(tiles, 88, 22, 5, 4, T.STONE);
  stamp(tiles, 90, 23, T.SHRINE);
  stamp(tiles, 91, 23, T.SHRINE);

  // dock west of plaza
  setRect(tiles, 6, 18, 4, 3, T.DOCK);

  // motel lot
  setRect(tiles, 8, 47, 8, 1, T.CONCRETE);

  line(tiles, 28, 26, 28, 32, T.PATH, false, rng);
  line(tiles, 50, 34, 66, 30, T.PATH, true, rng);
  line(tiles, 80, 18, 86, 16, T.DIRT, true, rng);
  line(tiles, 60, 46, 94, 62, T.DIRT, true, rng);

  const trees = [];
  const rocks = [];
  const lights = [];
  const props = [];
  const buildings = [];
  const nodes = [];
  const mobs = [];
  const npcs = [
    { type: 'maera', x: 88.5, y: 19.45 },
    { type: 'voss', x: 97.0, y: 19.4 },
    { type: 'nima', x: 8.2, y: 17.6 },
    { type: 'brin', x: 30.5, y: 49.2 },
    { type: 'selva', x: 90.5, y: 25.4 },
    { type: 'kesh', x: 24.4, y: 21.6 },
    { type: 'oren', x: 34.6, y: 18.4 },
    { type: 'rita', x: 75.4, y: 16.3 },
    { type: 'tavi', x: 38.5, y: 34.4 },
    { type: 'rook', x: 48.5, y: 56.6 },
    { type: 'lila', x: 26.4, y: 22.4 },
    { type: 'yara', x: 33.5, y: 48.6 },
    { type: 'shake_bar', x: 28.4, y: 6.6 },
    { type: 'rosa', x: 27.2, y: 7.4 },
  ];

  function inBounds(x, y) {
    return x >= 0 && y >= 0 && x < W && y < H;
  }

  function house(x, y, w, h, pal, opts = {}) {
    setRect(tiles, x, y, w, h, T.WOOD);
    stamp(tiles, x + ((w / 2) | 0), y + ((h / 2) | 0), T.RUG);
    const doorX = x + ((w / 2) | 0);
    const doorSide = opts.door || 's';
    for (let xx = x; xx < x + w; xx++) {
      block[y * W + xx] = 1;
      const southDoor = doorSide === 's' && xx === doorX;
      if (!southDoor) block[(y + h - 1) * W + xx] = 1;
    }
    for (let yy = y; yy < y + h; yy++) {
      block[yy * W + x] = 1;
      block[yy * W + (x + w - 1)] = 1;
    }
    if (doorSide === 's') block[(y + h - 1) * W + doorX] = 0;
    props.push({ kind: 'house', x, y, w, h, palette: pal });
    buildings.push({ kind: 'house', x, y, w, h, hgt: 2.8, palette: pal || ['#4a2018', '#2a1c14', '#d4a017'] });
    const cx = x + w / 2;
    const cy = y + h / 2;
    return { x, y, w, h, cx, cy, doorX, doorY: y + h - 0.4 };
  }

  function fenceThree(x, y, w, h) {
    const fx = x - 1, fy = y - 1, fw = w + 2, fh = h + 1;
    for (let xx = fx; xx < fx + fw; xx++) stamp(tiles, xx, fy, T.FENCE);
    for (let yy = fy; yy < fy + fh; yy++) {
      stamp(tiles, fx, yy, T.FENCE);
      stamp(tiles, fx + fw - 1, yy, T.FENCE);
    }
  }

  const housePal = [
    ['#6b3a2a', '#2a1810', '#c4a574'],
    ['#3a4a38', '#1a2418', '#8aa07a'],
    ['#4a3050', '#241428', '#c77dff'],
    ['#5a3a18', '#2a1c0c', '#e0a045'],
    ['#3a3a48', '#181820', '#8ab4c8'],
    ['#6a2830', '#2a1014', '#e8a0b0'],
    ['#2a3a4a', '#101820', '#7ec8e0'],
  ];

  const h1 = house(19, 26, 7, 6, housePal[0]);
  const h2 = house(28, 26, 7, 6, housePal[1]);
  const h3 = house(47, 26, 7, 6, housePal[2]);
  const h4 = house(19, 36, 7, 6, housePal[3]);
  const h5 = house(28, 36, 7, 6, housePal[4]);
  const h6 = house(47, 36, 7, 6, housePal[5]);
  const h7 = house(56, 36, 8, 6, housePal[6]);
  fenceThree(19, 26, 7, 6);
  fenceThree(47, 26, 7, 6);
  fenceThree(47, 36, 7, 6);

  // motel rooms (enterable row)
  const motel = house(8, 48, 7, 5, ['#5a4030', '#2a2018', '#d4a017']);
  setRect(tiles, 8, 47, 7, 1, T.CONCRETE);

  // gas bay — enterable
  const gasB = house(68, 9, 6, 5, ['#c45c18', '#2a1c10', '#f0d060']);

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
  hutWalls(86, 14, 5, 5, ['#6b3fa0', '#2a1830', '#c77dff']);
  hutWalls(94, 14, 6, 5, ['#f4a261', '#3a2010', '#e76f51']);

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

  buildings.push({ kind: 'mine', x: 95, y: 63, w: 10, h: 7, hgt: 2.4, palette: ['#4a4e56', '#2a2c30', '#8a8a9a'] });

  // parked wrecks on lots
  function placeCar(x, y, hue) {
    if (!inBounds(x, y) || !inBounds(x + 1, y)) return;
    block[y * W + x] = 1;
    block[y * W + (x + 1)] = 1;
    props.push({ kind: 'car', x, y, w: 2, h: 1, hue: hue ?? (rng() * 360) });
  }
  placeCar(12, 10, 20);
  placeCar(22, 10, 200);
  placeCar(38, 10, 0);
  placeCar(74, 18, 40);
  placeCar(78, 18, 180);
  placeCar(10, 47, 30);

  // pumps
  props.push({ kind: 'pump', x: 76, y: 14 });
  props.push({ kind: 'pump', x: 78, y: 14 });
  block[14 * W + 76] = 1;
  block[14 * W + 78] = 1;

  function canTree(x, y) {
    if (x < 2 || y < 2 || x >= W - 2 || y >= H - 2) return false;
    const t = tiles[y * W + x];
    if ([T.WATER, T.WATER_D, T.WOOD, T.FLAG, T.HEARTH, T.SHRINE, T.DOCK, T.STONE, T.RUG, T.PATH, T.ROAD, T.NEON, T.FENCE, T.CONCRETE].includes(t)) return false;
    if (block[y * W + x]) return false;
    return true;
  }

  for (let i = 0; i < 140; i++) {
    const x = 84 + (rng() * 24) | 0;
    const y = 6 + (rng() * 38) | 0;
    if (!canTree(x, y)) continue;
    block[y * W + x] = 1;
    trees.push({ x, y, variant: (rng() * 3) | 0, hue: 120 + rng() * 40 });
  }
  for (let i = 0; i < 18; i++) {
    const x = 66 + (rng() * 16) | 0;
    const y = 24 + (rng() * 14) | 0;
    if (!canTree(x, y)) continue;
    block[y * W + x] = 1;
    trees.push({ x, y, variant: (rng() * 3) | 0, hue: 110 + rng() * 30 });
  }
  for (let i = 0; i < 28; i++) {
    const x = 12 + (rng() * 40) | 0;
    const y = 47 + (rng() * 7) | 0;
    if (!canTree(x, y)) continue;
    block[y * W + x] = 1;
    trees.push({ x, y, variant: 3, hue: 25 + rng() * 20 });
  }
  for (let i = 0; i < 22; i++) {
    const x = 94 + (rng() * 14) | 0;
    const y = 60 + (rng() * 12) | 0;
    if (x >= W - 2 || y >= H - 2) continue;
    if (block[y * W + x]) continue;
    block[y * W + x] = 1;
    rocks.push({ x, y, variant: (rng() * 2) | 0 });
  }
  for (let i = 0; i < 16; i++) {
    const x = 14 + (rng() * 36) | 0;
    const y = 47 + (rng() * 6) | 0;
    if (block[y * W + x]) continue;
    const t = tiles[y * W + x];
    if ([T.WATER, T.WATER_D, T.ROAD, T.WOOD, T.RUG, T.CONCRETE, T.FENCE, T.FLAG, T.NEON].includes(t)) continue;
    block[y * W + x] = 1;
    rocks.push({ x, y, variant: (rng() * 2) | 0 });
  }

  // house / POI loot nodes on interiors
  function addNode(type, x, y) {
    nodes.push({ type, x, y });
  }
  addNode('kitchen_stash', h1.cx, h1.cy);
  addNode('closet_stash', h1.x + 2.4, h1.y + 2.4);
  addNode('kitchen_stash', h2.cx, h2.cy);
  addNode('med_cabinet', h2.x + 5.3, h2.y + 2.5);
  addNode('closet_stash', h3.cx, h3.cy);
  addNode('kitchen_stash', h4.cx, h4.cy);
  addNode('toolbox', h5.x + 2.5, h5.y + 2.5);
  addNode('closet_stash', h6.cx, h6.cy);
  addNode('kitchen_stash', h7.cx, h7.cy);
  addNode('med_cabinet', h7.x + 6.2, h7.y + 2.4);
  addNode('closet_stash', motel.x + 2.5, motel.y + 2.5);
  addNode('kitchen_stash', motel.x + 4.5, motel.y + 2.5);
  addNode('toolbox', gasB.cx, gasB.cy);
  addNode('gas_canister', 76.5, 16.5);
  addNode('gas_canister', 79.2, 16.6);

  addNode('dumpster', 14.5, 10.5);
  addNode('dumpster', 23.5, 10.5);
  addNode('dumpster', 40.5, 10.5);
  addNode('dumpster', 16.5, 63.5);
  addNode('dumpster', 36.5, 63.5);
  addNode('scrap_pile', 22.5, 49.5);
  addNode('scrap_pile', 38.5, 50.2);
  addNode('scrap_pile', 48.5, 49.4);

  addNode('emberwood_tree', 88.5, 10.5);
  addNode('emberwood_tree', 96.5, 11.5);
  addNode('emberwood_tree', 102.2, 16.4);
  addNode('emberwood_tree', 91.8, 32.2);
  addNode('emberwood_tree', 86.5, 38.6);
  addNode('emberwood_tree', 104.4, 28.5);
  addNode('emberwood_tree', 98.2, 40.5);
  addNode('moonbloom_patch', 100.2, 20.5);
  addNode('moonbloom_patch', 85.4, 26.8);
  addNode('moonbloom_patch', 12.5, 14.5);
  addNode('moonbloom_patch', 72.5, 32.5);
  addNode('moon_berry_bush', 70.2, 26.4);
  addNode('moon_berry_bush', 78.5, 34.2);
  addNode('moon_berry_bush', 32.5, 50.2);
  addNode('moon_berry_bush', 18.2, 50.4);
  addNode('wild_mint_patch', 10.5, 12.2);
  addNode('wild_mint_patch', 52.5, 12.4);
  addNode('wild_mint_patch', 64.5, 22.2);
  addNode('iron_outcrop', 98.5, 65.5);
  addNode('iron_outcrop', 102.2, 64.8);
  addNode('iron_outcrop', 96.4, 68.4);
  addNode('iron_outcrop', 105.5, 67.5);
  addNode('dusk_mushroom_patch', 92.5, 36.5);
  addNode('dusk_mushroom_patch', 107.2, 22.4);
  addNode('dusk_mushroom_patch', 74.5, 36.2);
  addNode('honeycomb_hive', 101.5, 12.5);
  addNode('honeycomb_hive', 87.2, 8.8);

  // walkers on streets, dogs near lots, original fauna in ash/woods
  function addMob(type, x, y) { mobs.push({ type, x, y }); }
  addMob('dusk_walker', 22.5, 33.5);
  addMob('dusk_walker', 34.5, 33.2);
  addMob('dusk_walker', 50.5, 33.6);
  addMob('dusk_walker', 22.5, 45.4);
  addMob('dusk_walker', 38.5, 45.2);
  addMob('dusk_walker', 52.5, 45.6);
  addMob('dusk_walker', 60.5, 38.4);
  addMob('dusk_walker', 14.5, 50.5);
  addMob('dusk_walker', 72.5, 20.5);
  addMob('feral_dog', 14.5, 11.6);
  addMob('feral_dog', 40.8, 11.4);
  addMob('feral_dog', 76.5, 20.2);
  addMob('feral_dog', 24.5, 50.8);
  addMob('gloom_wolf', 26.5, 50.5);
  addMob('gloom_wolf', 32.5, 51.2);
  addMob('gloom_wolf', 40.2, 49.4);
  addMob('gloom_wolf', 18.8, 51.8);
  addMob('ash_imp', 28.5, 49.5);
  addMob('ash_imp', 36.2, 50.1);
  addMob('ash_imp', 44.1, 51.8);
  addMob('dust_raccoon', 70.2, 36.5);
  addMob('dust_raccoon', 78.5, 27.4);
  addMob('dust_raccoon', 8.5, 36.4);
  addMob('bramble_boar', 90.5, 40.2);
  addMob('bramble_boar', 104.2, 34.5);
  addMob('bramble_boar', 50.2, 50.5);
  addMob('hollow_stag', 106.2, 10.5);
  addMob('road_thug', 20.5, 8.5);
  addMob('road_thug', 40.5, 8.6);
  addMob('road_thug', 56.5, 7.8);
  addMob('road_thug', 22.5, 55.5);
  addMob('cinder_hound', 24.5, 48.6);
  addMob('cinder_hound', 42.5, 51.2);
  addMob('mine_crawler', 99.5, 66.5);
  addMob('mine_crawler', 104.2, 68.4);

  for (let y = 0; y < H; y++) {
    block[y * W + 0] = 1;
    block[y * W + 1] = 1;
    block[y * W + (W - 1)] = 1;
    block[y * W + (W - 2)] = 1;
  }
  for (let x = 0; x < W; x++) {
    block[0 * W + x] = 1;
    block[1 * W + x] = 1;
    block[(H - 1) * W + x] = 1;
    block[(H - 2) * W + x] = 1;
  }

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const t = tiles[y * W + x];
      if (!TILE_WALK[t]) block[y * W + x] = 1;
    }
  }

  lights.push({ x: 28.5, y: 20.5, r: 6.2, color: [255, 140, 50], flicker: 1 });
  lights.push({ x: 90.5, y: 23.5, r: 4.0, color: [180, 120, 255], flicker: 0.8 });
  lights.push({ x: 8.5, y: 17.5, r: 2.8, color: [80, 180, 220], flicker: 0.4 });
  lights.push({ x: 32.5, y: 50.5, r: 3.0, color: [255, 90, 40], flicker: 1.2 });
  lights.push({ x: 100, y: 66, r: 3.2, color: [180, 180, 200], flicker: 0.5 });
  lights.push({ x: 74, y: 14, r: 4.2, color: [255, 180, 60], flicker: 0.7 });
  lights.push({ x: 74, y: 31, r: 3.4, color: [120, 200, 140], flicker: 0.4 });

  const walk = new Uint8Array(W * H);
  for (let i = 0; i < walk.length; i++) walk[i] = block[i] ? 0 : 1;

  function isWalk(x, y) {
    const tx = Math.floor(x), ty = Math.floor(y);
    if (tx < 0 || ty < 0 || tx >= W || ty >= H) return false;
    return !!walk[ty * W + tx];
  }
  function snap(ent) {
    if (isWalk(ent.x, ent.y)) return ent;
    for (let r = 1; r <= 6; r++) {
      for (let dy = -r; dy <= r; dy++) {
        for (let dx = -r; dx <= r; dx++) {
          const x = Math.floor(ent.x) + dx + 0.5;
          const y = Math.floor(ent.y) + dy + 0.5;
          if (isWalk(x, y)) return { ...ent, x, y };
        }
      }
    }
    return ent;
  }

  const npcsS = npcs.map(snap);
  const nodesS = nodes.map(snap);
  const mobsS = mobs.map(snap);

  const pois = [
    { id: 'plaza', name: 'Clermont Square', x: 28.5, y: 20.5 },
    { id: 'shake_row', name: 'Shake Row / Hwy 50', x: 28.5, y: 8 },
    { id: 'johns_lake', name: 'Johns Lake Strip', x: 28, y: 61 },
    { id: 'maple', name: 'Maple Street', x: 34, y: 33 },
    { id: 'oak', name: 'Oak Street', x: 34, y: 45 },
    { id: 'gas', name: 'Hancock Pumps', x: 74, y: 14 },
    { id: 'park', name: 'Willow Park', x: 74, y: 31 },
    { id: 'motel', name: 'Riverside Motel', x: 14, y: 50 },
    { id: 'tutor', name: "Maera's Hut", x: 88.5, y: 19 },
    { id: 'keeper', name: "Voss's Hall", x: 97, y: 19 },
    { id: 'shrine', name: 'Binding Shrine', x: 90.5, y: 24.5 },
    { id: 'dock', name: 'Silt Dock', x: 8, y: 19.5 },
    { id: 'wood', name: 'Emberwood Copse', x: 98, y: 18 },
    { id: 'mine', name: 'Agate Mine', x: 100, y: 66 },
    { id: 'wolves', name: 'Ash Lots', x: 32, y: 50 },
    { id: 'imps', name: 'Cinder Circle', x: 36, y: 50 },
  ];

  return {
    w: W, h: H, tiles, walk, trees, rocks, lights, props, buildings, pois,
    npcs: npcsS, nodes: nodesS, mobs: mobsS,
    zone: {
      id: 'clermont',
      name: 'Clermont Town',
      blurb: 'Hwy 50 shake row north. Maple and Oak houses. Hancock pumps and Willow Park east. Emberfen and the mine further east.',
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
