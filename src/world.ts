import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { WebSocket } from "ws";
import { ITEMS, item } from "./items.ts";
export { ITEMS, item };

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.join(__dirname, "..");
export const PORT = Number(process.env.PORT || 3333);
export const TICK = 50;
export const SPEED = 6.2;
export const INV = 24;
export const MAX_HP = 100;
export const MAX_EN = 100;

export type Slot = { id: string; qty: number };
export type Buff = { id: string; label: string; until: number; speed?: number; power?: number; armor?: number };

type ShopFile = {
  shops: {
    id: string; name: string; flagship?: boolean; address: string;
    npcName: string; blurb: string; zip?: string;
    stock: { itemId: string; price: number }[];
  }[];
};

const SHOP_POS: Record<string, { x: number; z: number; color: string }> = {
  shake_bar: { x: -28, z: -72, color: "#ff4fd8" },
  steak_n_shake: { x: -12, z: -72, color: "#f5d547" },
  ritters: { x: 10, z: -72, color: "#ff8fab" },
  brusters: { x: -52, z: -72, color: "#d62828" },
  baskin: { x: -78, z: -72, color: "#e91e8c" },
  culvers: { x: -24, z: 48, color: "#1e4b8e" },
  five_guys: { x: -52, z: 48, color: "#d32f2f" },
  dairy_queen: { x: -80, z: 48, color: "#e31837" },
  mcdonalds: { x: 6, z: 48, color: "#ffc72c" },
  wendys: { x: 34, z: 48, color: "#e41c38" },
};

export const REGIONS = [
  { id: "square", name: "Clermont Square", x: 0, z: 0, r: 28 },
  { id: "shake_row", name: "Shake Row / Hwy 50", x: -30, z: -72, r: 55 },
  { id: "johns_lake", name: "Johns Lake Strip", x: -20, z: 48, r: 55 },
  { id: "wilds", name: "Hwy 50 Wilds", x: -20, z: 120, r: 70 },
  { id: "mine", name: "Agate Mine", x: 130, z: 110, r: 40 },
  { id: "ruins", name: "Goblin Rest Stop", x: 140, z: 10, r: 40 },
  { id: "dock", name: "Johns Lake Dock", x: 10, z: -150, r: 45 },
];

type Building = { x: number; z: number; w: number; d: number; kind: string; ref?: string };
export const buildings: Building[] = [
  { x: 22, z: 8, w: 10, d: 8, kind: "bank" },
  { x: 0, z: 0, w: 3, d: 3, kind: "fountain" },
  { x: 130, z: 118, w: 8, d: 6, kind: "mine" },
  { x: 8, z: -162, w: 9, d: 7, kind: "dockhouse" },
];

const shopFile: ShopFile = JSON.parse(
  fs.readFileSync(path.join(ROOT, "data", "shops.json"), "utf8")
);

export type Shop = ShopFile["shops"][number] & { x: number; z: number; color: string };
export const shops: Shop[] = shopFile.shops.map((s) => {
  const p = SHOP_POS[s.id] || { x: 0, z: 0, color: "#888" };
  buildings.push({ x: p.x, z: p.z, w: s.flagship ? 12 : 8, d: s.flagship ? 10 : 7, kind: "shop", ref: s.id });
  return { ...s, ...p };
});

export function blocked(x: number, z: number, ignoreFountain = true): boolean {
  for (const b of buildings) {
    if (ignoreFountain && b.kind === "fountain") continue;
    const hw = b.w * 0.5 - 0.4, hd = b.d * 0.5 - 0.4;
    if (Math.abs(x - b.x) < hw && Math.abs(z - b.z) < hd) return true;
  }
  if (x < -178 || x > 178 || z < -178 || z > 178) return true;
  return false;
}

export function regionAt(x: number, z: number): string {
  let best = REGIONS[0], bestD = 1e9;
  for (const r of REGIONS) {
    const d = Math.hypot(x - r.x, z - r.z);
    if (d < bestD) { bestD = d; best = r; }
  }
  return best.name;
}

export type Player = {
  id: string; name: string; color: string;
  x: number; y: number; z: number; tx: number; tz: number; facing: number;
  hp: number; energy: number; gold: number;
  inv: Slot[]; forageXp: number; combatXp: number;
  buffs: Buff[]; ws: WebSocket; lastChat: number;
  target?: string; gather?: { id: string; until: number };
};
export const players = new Map<string, Player>();
export const names = new Map<string, string>();

export type Npc = {
  id: string; kind: "shop" | "friendly" | "hostile";
  name: string; shopId?: string; x: number; z: number; hx: number; hz: number;
  hp: number; maxHp: number; color: string; respawn?: number; loot?: string[];
};
export const npcs: Npc[] = [];

for (const s of shops) {
  const doorZ = s.z + (s.z < 0 ? 6 : -6);
  npcs.push({
    id: "npc-" + s.id, kind: "shop", name: s.npcName, shopId: s.id,
    x: s.x, z: doorZ, hx: s.x, hz: doorZ, hp: 999, maxHp: 999,
    color: s.color,
  });
}
npcs.push({ id: "npc-banker", kind: "friendly", name: "Teller Bo", x: 22, z: 14, hx: 22, hz: 14, hp: 999, maxHp: 999, color: "#f0d78c" });
npcs.push({ id: "npc-crier", kind: "friendly", name: "Plaza Nia", x: -6, z: 6, hx: -6, hz: 6, hp: 999, maxHp: 999, color: "#80deea" });
npcs.push({ id: "npc-dock", kind: "friendly", name: "Captain Dew", x: 4, z: -150, hx: 4, hz: -150, hp: 999, maxHp: 999, color: "#90caf9" });

function hostile(id: string, name: string, x: number, z: number, color: string, hp: number, loot: string[]): Npc {
  return { id, kind: "hostile", name, x, z, hx: x, hz: z, hp, maxHp: hp, color, loot };
}
npcs.push(
  hostile("h1", "Dust Raccoon", -10, 118, "#6d4c41", 28, ["raccoon_pelt", "moon_berry"]),
  hostile("h2", "Dust Raccoon", 12, 130, "#5d4037", 28, ["raccoon_pelt"]),
  hostile("h3", "Bramble Boar", 30, 108, "#8d6e63", 46, ["boar_bristle", "sun_petal"]),
  hostile("h4", "Hwy Gremlin", 95, 40, "#78909c", 36, ["gremlin_bolt", "lucky_cap"]),
  hostile("h5", "Hwy Gremlin", 150, -8, "#607d8b", 36, ["gremlin_bolt"]),
  hostile("h6", "Ruin Crow", 138, 22, "#37474f", 22, ["crow_feather"]),
  hostile("h7", "Ruin Crow", 155, 18, "#263238", 22, ["crow_feather", "lucky_cap"]),
  hostile("h8", "Cave Tick", 128, 100, "#4e342e", 32, ["moss_agate", "pine_resin"]),
  hostile("h9", "Dust Raccoon", -40, 140, "#6d4c41", 28, ["raccoon_pelt", "wild_mint"]),
  hostile("h10", "Bramble Boar", 50, 145, "#8d6e63", 50, ["boar_bristle"])
);

export type Node = { id: string; kind: string; name: string; x: number; z: number; item: string; busyUntil: number; ready: boolean };
export const nodes: Node[] = [
  { id: "n1", kind: "berry", name: "Moon Berry Bush", x: -36, z: 112, item: "moon_berry", busyUntil: 0, ready: true },
  { id: "n2", kind: "berry", name: "Moon Berry Bush", x: 8, z: 122, item: "moon_berry", busyUntil: 0, ready: true },
  { id: "n3", kind: "mint", name: "Wild Mint", x: -58, z: 98, item: "wild_mint", busyUntil: 0, ready: true },
  { id: "n4", kind: "hive", name: "Roadside Hive", x: 22, z: 96, item: "honeycomb", busyUntil: 0, ready: true },
  { id: "n5", kind: "shroom", name: "Dusk Patch", x: -14, z: 148, item: "dusk_mushroom", busyUntil: 0, ready: true },
  { id: "n6", kind: "flower", name: "Sun Petals", x: 44, z: 118, item: "sun_petal", busyUntil: 0, ready: true },
  { id: "n7", kind: "resin", name: "Pine Wound", x: 70, z: 132, item: "pine_resin", busyUntil: 0, ready: true },
  { id: "n8", kind: "berry", name: "Moon Berry Bush", x: 118, z: 88, item: "moon_berry", busyUntil: 0, ready: true },
  { id: "n9", kind: "shroom", name: "Dusk Patch", x: 148, z: 96, item: "dusk_mushroom", busyUntil: 0, ready: true },
];

export type Trade = {
  a: string; b: string;
  offerA: { items: Slot[]; gold: number }; offerB: { items: Slot[]; gold: number };
  okA: boolean; okB: boolean;
};
export const trades = new Map<string, Trade>();

export function hue(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return `hsl(${h % 360} 70% 62%)`;
}
export function skill(xp: number) { return Math.floor(Math.sqrt(xp / 12)) + 1; }
export function qtyOf(inv: Slot[], id: string) { return inv.filter(s => s.id === id).reduce((a, s) => a + s.qty, 0); }
export function take(inv: Slot[], id: string, n: number): boolean {
  if (qtyOf(inv, id) < n) return false;
  let left = n;
  for (const s of inv) {
    if (s.id !== id) continue;
    const k = Math.min(s.qty, left);
    s.qty -= k; left -= k;
  }
  for (let i = inv.length - 1; i >= 0; i--) if (inv[i].qty <= 0) inv.splice(i, 1);
  return true;
}
export function spaceFor(inv: Slot[], id: string, n: number): boolean {
  const def = item(id);
  if (!def) return false;
  if (def.stack) {
    const existing = inv.find(s => s.id === id);
    if (existing) return true;
  }
  return inv.length + (def.stack ? 1 : n) <= INV;
}
export function give(inv: Slot[], id: string, n: number): boolean {
  const def = item(id);
  if (!def || !spaceFor(inv, id, n)) return false;
  if (def.stack) {
    const s = inv.find(x => x.id === id);
    if (s) s.qty += n; else inv.push({ id, qty: n });
    return true;
  }
  for (let i = 0; i < n; i++) {
    if (inv.length >= INV) return i > 0;
    inv.push({ id, qty: 1 });
  }
  return true;
}

export function send(p: Player, o: unknown) {
  if (p.ws.readyState === WebSocket.OPEN) p.ws.send(JSON.stringify(o));
}
export function toast(p: Player, msg: string, kind = "info") { send(p, { t: "toast", msg, kind }); }
export function publicChat(from: string, text: string, mode = "public", to?: string) {
  const msg = { t: "chat", from, text, mode, to };
  for (const p of players.values()) {
    if (mode === "whisper") {
      if (p.name === from || p.name === to) send(p, msg);
    } else send(p, msg);
  }
}

export function snapshot() {
  return {
    players: [...players.values()].map(p => ({
      id: p.id, name: p.name, color: p.color, x: p.x, y: p.y, z: p.z, facing: p.facing, hp: p.hp,
    })),
    npcs: npcs.map(n => ({
      id: n.id, kind: n.kind, name: n.name, shopId: n.shopId, x: n.x, z: n.z, hp: n.hp, maxHp: n.maxHp, color: n.color,
    })),
    nodes: nodes.map(n => ({ id: n.id, kind: n.kind, name: n.name, x: n.x, z: n.z, ready: n.ready })),
  };
}
export function mePayload(p: Player) {
  return {
    t: "me",
    id: p.id, name: p.name, color: p.color,
    x: p.x, y: p.y, z: p.z, hp: p.hp, energy: p.energy, gold: p.gold,
    inv: p.inv, forage: skill(p.forageXp), combat: skill(p.combatXp),
    forageXp: p.forageXp, combatXp: p.combatXp,
    buffs: p.buffs.map(b => ({ ...b, left: Math.max(0, b.until - Date.now()) })),
    region: regionAt(p.x, p.z),
  };
}
export function pushMe(p: Player) { send(p, mePayload(p)); }

export function uniqueName(raw: string) {
  let n = (raw || "Wanderer").replace(/[^\w \-']/g, "").trim().slice(0, 16) || "Wanderer";
  if (!names.has(n.toLowerCase())) return n;
  for (let i = 2; i < 99; i++) {
    const c = `${n}${i}`.slice(0, 16);
    if (!names.has(c.toLowerCase())) return c;
  }
  return n + Math.floor(Math.random() * 9);
}

export function starterInv(): Slot[] {
  return [
    { id: "berry_basket", qty: 1 },
    { id: "copper_knife", qty: 1 },
    { id: "empty_cup", qty: 1 },
    { id: "picnic_cloth", qty: 1 },
  ];
}
