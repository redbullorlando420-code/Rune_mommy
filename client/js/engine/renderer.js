import { TILE, MAP_W, MAP_H, hueFromName } from '/shared/constants.js';
import { T } from '/shared/tiles.js';
import { camera, worldToScreen } from './camera.js';

const PAL = {
  [T.VOID]: '#07060a',
  [T.GRASS]: '#243326',
  [T.GRASS_D]: '#1c2a1e',
  [T.TALL]: '#2c3e2c',
  [T.PATH]: '#6a5640',
  [T.STONE]: '#4e4b48',
  [T.DIRT]: '#4a3b2c',
  [T.WATER]: '#173246',
  [T.WATER_D]: '#0e2133',
  [T.SAND]: '#7a6b52',
  [T.WOOD]: '#4a3224',
  [T.RUG]: '#5a2428',
  [T.FLAG]: '#4a4743',
  [T.ASH]: '#3a3532',
  [T.MOSS]: '#314538',
  [T.FLOWER]: '#2e3344',
  [T.HEARTH]: '#8a3c18',
  [T.DOCK]: '#5c4030',
  [T.SHRINE]: '#3e2e52',
  [T.LEAVES]: '#33422c',
};

let canvas, ctx, dpr = 1, viewW = 0, viewH = 0;
const floats = [];

export function initRenderer(el) {
  canvas = el;
  ctx = canvas.getContext('2d');
  resize();
  window.addEventListener('resize', resize);
}

export function resize() {
  if (!canvas) return;
  dpr = Math.min(2, window.devicePixelRatio || 1);
  viewW = canvas.clientWidth || window.innerWidth;
  viewH = canvas.clientHeight || window.innerHeight;
  canvas.width = Math.floor(viewW * dpr);
  canvas.height = Math.floor(viewH * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

export function viewSize() { return { w: viewW, h: viewH }; }

export function addFloat(f) {
  floats.push({ ...f, born: performance.now() });
}

function lerpPos(e, k) {
  if (e.dx == null) { e.dx = e.x; e.dy = e.y; }
  e.dx += (e.x - e.dx) * k;
  e.dy += (e.y - e.dy) * k;
  return { x: e.dx, y: e.dy };
}

export function draw(state, map, now) {
  if (!ctx) return;
  const k = 0.22;
  ctx.fillStyle = '#07060a';
  ctx.fillRect(0, 0, viewW, viewH);

  const t0x = Math.max(0, Math.floor(camera.x - viewW / TILE / 2 - 2));
  const t0y = Math.max(0, Math.floor(camera.y - viewH / TILE / 2 - 2));
  const t1x = Math.min(MAP_W - 1, Math.ceil(camera.x + viewW / TILE / 2 + 2));
  const t1y = Math.min(MAP_H - 1, Math.ceil(camera.y + viewH / TILE / 2 + 2));

  for (let ty = t0y; ty <= t1y; ty++) {
    for (let tx = t0x; tx <= t1x; tx++) {
      const t = map.tiles[ty * MAP_W + tx];
      const s = worldToScreen(tx, ty, viewW, viewH);
      ctx.fillStyle = PAL[t] || '#111';
      ctx.fillRect(s.x, s.y, TILE + 0.6, TILE + 0.6);
      if (t === T.WATER || t === T.WATER_D) {
        const wave = Math.sin(now / 420 + tx * 0.7 + ty * 0.45);
        ctx.fillStyle = `rgba(80,160,190,${0.07 + wave * 0.05})`;
        ctx.fillRect(s.x, s.y + (wave * 6 + 12), TILE, 4);
      }
      if (t === T.FLOWER && ((tx * 13 + ty * 7) % 3 === 0)) {
        ctx.fillStyle = '#7a6bb0';
        ctx.beginPath();
        ctx.arc(s.x + 18, s.y + 20, 2.2, 0, 7);
        ctx.fill();
      }
      if (t === T.HEARTH) {
        const g = 0.45 + Math.sin(now / 180 + tx) * 0.12;
        ctx.fillStyle = `rgba(255,140,40,${g})`;
        ctx.fillRect(s.x + 8, s.y + 8, TILE - 16, TILE - 16);
      }
      if (t === T.SHRINE) {
        ctx.fillStyle = `rgba(160,120,255,${0.18 + Math.sin(now / 400) * 0.06})`;
        ctx.fillRect(s.x, s.y, TILE, TILE);
      }
    }
  }

  for (const p of map.props || []) {
    if (p.kind !== 'hut') continue;
    const s = worldToScreen(p.x, p.y, viewW, viewH);
    ctx.fillStyle = 'rgba(28, 16, 12, 0.55)';
    ctx.fillRect(s.x - 4, s.y - 10, p.w * TILE + 8, p.h * TILE + 6);
    ctx.fillStyle = '#3a241c';
    ctx.beginPath();
    ctx.moveTo(s.x - 8, s.y + 8);
    ctx.lineTo(s.x + (p.w * TILE) / 2, s.y - 22);
    ctx.lineTo(s.x + p.w * TILE + 8, s.y + 8);
    ctx.closePath();
    ctx.fill();
  }

  const you = state.you;
  if (you) lerpPos(you, k);

  const drawList = [];
  for (const t of map.trees || []) drawList.push({ y: t.y + 0.4, kind: 'tree', t });
  for (const r of map.rocks || []) drawList.push({ y: r.y + 0.2, kind: 'rock', r });
  for (const n of state.nodes || []) if (n.alive) drawList.push({ y: n.y, kind: 'node', n, ...lerpPos(n, k) });
  for (const g of state.ground || []) drawList.push({ y: g.y, kind: 'ground', g });
  for (const m of state.mobs || []) if (m.alive) drawList.push({ y: m.y, kind: 'mob', m, ...lerpPos(m, k) });
  for (const n of state.npcs || []) drawList.push({ y: n.y, kind: 'npc', n });
  for (const p of state.players || []) drawList.push({ y: p.y, kind: 'player', p, ...lerpPos(p, k) });
  if (you) drawList.push({ y: you.dy ?? you.y, kind: 'you', p: you });

  drawList.sort((a, b) => a.y - b.y);
  const sel = state.selected;

  for (const e of drawList) {
    if (e.kind === 'tree') drawTree(e.t, now);
    else if (e.kind === 'rock') drawRock(e.r);
    else if (e.kind === 'node') drawNode(e.n, e.x, e.y, sel);
    else if (e.kind === 'ground') drawGround(e.g);
    else if (e.kind === 'mob') drawMob(e.m, e.x, e.y, sel);
    else if (e.kind === 'npc') drawNpc(e.n, sel);
    else if (e.kind === 'player' || e.kind === 'you') {
      drawPerson(e.p, e.x ?? e.p.dx ?? e.p.x, e.y ?? e.p.dy ?? e.p.y, e.kind === 'you', sel);
    }
  }

  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (const L of map.lights || []) {
    const s = worldToScreen(L.x, L.y, viewW, viewH);
    const flick = 1 + Math.sin(now / 140 * (L.flicker || 1) + L.x) * 0.08 * (L.flicker || 1);
    const r = L.r * TILE * 0.85 * flick;
    const [cr, cg, cb] = L.color;
    const g = ctx.createRadialGradient(s.x, s.y, 4, s.x, s.y, r);
    g.addColorStop(0, `rgba(${cr},${cg},${cb},0.22)`);
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(s.x, s.y, r, 0, 7); ctx.fill();
  }
  ctx.restore();

  const vg = ctx.createRadialGradient(viewW / 2, viewH / 2, viewH * 0.2, viewW / 2, viewH / 2, viewH * 0.78);
  vg.addColorStop(0, 'rgba(0,0,0,0)');
  vg.addColorStop(1, 'rgba(4,2,8,0.62)');
  ctx.fillStyle = vg;
  ctx.fillRect(0, 0, viewW, viewH);

  drawFloats(now);
  if (state.dest) {
    const s = worldToScreen(state.dest.x, state.dest.y, viewW, viewH);
    ctx.strokeStyle = 'rgba(224,160,69,0.7)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(s.x - 6, s.y); ctx.lineTo(s.x + 6, s.y);
    ctx.moveTo(s.x, s.y - 6); ctx.lineTo(s.x, s.y + 6);
    ctx.stroke();
  }
}

function shadow(sx, sy, rx = 14, ry = 6) {
  ctx.fillStyle = 'rgba(0,0,0,0.4)';
  ctx.beginPath(); ctx.ellipse(sx, sy + 10, rx, ry, 0, 0, 7); ctx.fill();
}

function drawTree(t) {
  const s = worldToScreen(t.x + 0.5, t.y + 0.5, viewW, viewH);
  shadow(s.x, s.y, 16, 6);
  const dead = t.variant === 3;
  ctx.fillStyle = dead ? '#3a2a22' : '#2a1c14';
  ctx.fillRect(s.x - 3.5, s.y - 8, 7, 16);
  ctx.fillStyle = dead ? '#4a3a30' : `hsl(${t.hue}, 28%, 20%)`;
  ctx.beginPath(); ctx.arc(s.x, s.y - 18, dead ? 11 : 16, 0, 7); ctx.fill();
  ctx.fillStyle = dead ? '#5a4030' : `hsl(${t.hue}, 32%, 26%)`;
  ctx.beginPath(); ctx.arc(s.x - 8, s.y - 12, 9, 0, 7); ctx.fill();
}

function drawRock(r) {
  const s = worldToScreen(r.x + 0.5, r.y + 0.5, viewW, viewH);
  shadow(s.x, s.y, 10, 4);
  ctx.fillStyle = '#4a4642';
  ctx.beginPath();
  ctx.moveTo(s.x - 10, s.y + 4);
  ctx.lineTo(s.x - 4, s.y - 8);
  ctx.lineTo(s.x + 8, s.y - 4);
  ctx.lineTo(s.x + 10, s.y + 6);
  ctx.closePath(); ctx.fill();
}

function ring(sx, sy, r, on) {
  if (!on) return;
  ctx.strokeStyle = 'rgba(224,160,69,0.9)';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(sx, sy + 4, r, 0, 7); ctx.stroke();
}

function drawNode(n, x, y, sel) {
  const s = worldToScreen(x, y, viewW, viewH);
  shadow(s.x, s.y, 12, 5);
  ring(s.x, s.y, 16, sel === n.id);
  if (n.type === 'emberwood_tree') {
    ctx.fillStyle = '#3a2214'; ctx.fillRect(s.x - 3, s.y - 6, 6, 14);
    ctx.fillStyle = '#8a3a18';
    ctx.beginPath(); ctx.arc(s.x, s.y - 16, 13, 0, 7); ctx.fill();
    ctx.fillStyle = '#c45a20';
    ctx.beginPath(); ctx.arc(s.x + 6, s.y - 18, 6, 0, 7); ctx.fill();
  } else if (n.type === 'moonbloom_patch') {
    ctx.fillStyle = '#2a3348';
    ctx.beginPath(); ctx.ellipse(s.x, s.y, 12, 7, 0, 0, 7); ctx.fill();
    ctx.fillStyle = '#c8c0f0';
    for (let i = 0; i < 5; i++) {
      ctx.beginPath();
      ctx.arc(s.x - 8 + i * 4, s.y - 6 - (i % 2) * 3, 2.4, 0, 7);
      ctx.fill();
    }
  } else {
    ctx.fillStyle = '#6a6e74';
    ctx.beginPath();
    ctx.moveTo(s.x - 11, s.y + 6);
    ctx.lineTo(s.x - 2, s.y - 12);
    ctx.lineTo(s.x + 12, s.y + 4);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#8a9098';
    ctx.fillRect(s.x - 3, s.y - 4, 8, 5);
  }
  label(s.x, s.y - 28, n.name, '#c9c2b8');
}

function drawGround(g) {
  const s = worldToScreen(g.x, g.y, viewW, viewH);
  ctx.fillStyle = '#e0a045';
  ctx.beginPath(); ctx.arc(s.x, s.y, 5, 0, 7); ctx.fill();
  ctx.fillStyle = '#f4e4c4';
  ctx.beginPath(); ctx.arc(s.x, s.y, 2, 0, 7); ctx.fill();
}

function drawMob(m, x, y, sel) {
  const s = worldToScreen(x, y, viewW, viewH);
  const sz = (m.size || 0.9) * 16;
  shadow(s.x, s.y, sz * 0.7, 5);
  ring(s.x, s.y, sz + 6, sel === m.id);
  ctx.fillStyle = m.color || '#6d6875';
  if (m.type === 'gloom_wolf') {
    ctx.beginPath(); ctx.ellipse(s.x, s.y, sz, sz * 0.62, -0.3, 0, 7); ctx.fill();
    ctx.fillStyle = '#3a353c';
    ctx.beginPath(); ctx.ellipse(s.x + sz * 0.7, s.y - 2, 7, 5, 0, 0, 7); ctx.fill();
  } else if (m.type === 'ash_imp') {
    ctx.beginPath(); ctx.arc(s.x, s.y, sz * 0.7, 0, 7); ctx.fill();
    ctx.fillStyle = '#ffb703';
    ctx.beginPath(); ctx.arc(s.x, s.y - sz, 4, 0, 7); ctx.fill();
  } else {
    ctx.beginPath(); ctx.ellipse(s.x, s.y - 4, sz * 0.7, sz, 0, 0, 7); ctx.fill();
    ctx.strokeStyle = '#d8fff4';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(s.x - 8, s.y - sz - 4);
    ctx.lineTo(s.x - 14, s.y - sz - 16);
    ctx.moveTo(s.x + 8, s.y - sz - 4);
    ctx.lineTo(s.x + 14, s.y - sz - 16);
    ctx.stroke();
  }
  hpBar(s.x, s.y - sz - 12, m.hp, m.maxHp, 28);
  label(s.x, s.y - sz - 22, m.name, m.rare ? '#b8f2e6' : '#d0c8c0');
}

function drawNpc(n, sel) {
  const s = worldToScreen(n.x, n.y, viewW, viewH);
  shadow(s.x, s.y);
  ring(s.x, s.y, 18, sel === n.id);
  ctx.fillStyle = n.color || '#c77dff';
  ctx.beginPath(); ctx.moveTo(s.x, s.y - 22); ctx.lineTo(s.x + 12, s.y + 8); ctx.lineTo(s.x - 12, s.y + 8); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#f0e6d4';
  ctx.beginPath(); ctx.arc(s.x, s.y - 16, 6, 0, 7); ctx.fill();
  label(s.x, s.y - 34, n.name, n.color || '#c77dff');
  if (n.title) label(s.x, s.y - 22, n.title, '#8a837a', 10);
}

function drawPerson(p, x, y, isYou, sel) {
  const s = worldToScreen(x, y, viewW, viewH);
  const hue = p.hue ?? hueFromName(p.name || '');
  shadow(s.x, s.y);
  ring(s.x, s.y, 17, sel === p.id || isYou);
  ctx.fillStyle = `hsl(${hue}, 32%, 22%)`;
  ctx.beginPath();
  ctx.moveTo(s.x - 11, s.y + 10);
  ctx.lineTo(s.x + 11, s.y + 10);
  ctx.lineTo(s.x + 7, s.y - 6);
  ctx.lineTo(s.x - 7, s.y - 6);
  ctx.closePath(); ctx.fill();
  ctx.fillStyle = `hsl(${hue}, 40%, 48%)`;
  ctx.beginPath(); ctx.arc(s.x, s.y - 12, 7, 0, 7); ctx.fill();
  if (isYou) {
    ctx.strokeStyle = 'rgba(224,160,69,0.85)';
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(s.x, s.y + 4, 16, 0, 7); ctx.stroke();
  }
  hpBar(s.x, s.y - 28, p.hp, p.maxHp, 26);
  label(s.x, s.y - 38, p.name, isYou ? '#e0a045' : '#f0e6d4');
}

function hpBar(x, y, hp, max, w) {
  const t = Math.max(0, Math.min(1, (hp || 0) / (max || 1)));
  ctx.fillStyle = '#1a1010';
  ctx.fillRect(x - w / 2, y, w, 4);
  ctx.fillStyle = t > 0.45 ? '#6b8f5a' : t > 0.2 ? '#e0a045' : '#c23b3b';
  ctx.fillRect(x - w / 2, y, w * t, 4);
}

function label(x, y, text, color, size = 11) {
  ctx.font = `${size}px Spectral, serif`;
  ctx.textAlign = 'center';
  ctx.fillStyle = 'rgba(0,0,0,0.65)';
  ctx.fillText(text, x + 1, y + 1);
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}

function drawFloats(now) {
  for (let i = floats.length - 1; i >= 0; i--) {
    const f = floats[i];
    const age = now - f.born;
    if (age > 1100) { floats.splice(i, 1); continue; }
    const s = worldToScreen(f.x, f.y - age / 900, viewW, viewH);
    ctx.globalAlpha = 1 - age / 1100;
    ctx.font = '700 14px Cinzel, serif';
    ctx.textAlign = 'center';
    ctx.fillStyle = f.color || '#f4d35e';
    ctx.fillText(f.text, s.x, s.y);
    ctx.globalAlpha = 1;
  }
}

export function drawMinimap(el, state, map) {
  const c = el.getContext('2d');
  const w = el.width, h = el.height;
  c.fillStyle = '#0a080c';
  c.fillRect(0, 0, w, h);
  const sx = w / MAP_W, sy = h / MAP_H;
  for (let y = 0; y < MAP_H; y++) {
    for (let x = 0; x < MAP_W; x++) {
      c.fillStyle = PAL[map.tiles[y * MAP_W + x]] || '#111';
      c.fillRect(x * sx, y * sy, sx + 0.5, sy + 0.5);
    }
  }
  const dot = (x, y, col, r = 2.2) => {
    c.fillStyle = col;
    c.beginPath(); c.arc(x * sx, y * sy, r, 0, 7); c.fill();
  };
  for (const n of state.npcs || []) dot(n.x, n.y, n.color || '#c77dff', 2.4);
  for (const m of state.mobs || []) if (m.alive) dot(m.x, m.y, '#c23b3b', 2);
  for (const p of state.players || []) dot(p.dx ?? p.x, p.dy ?? p.y, '#d8d0c8', 2);
  if (state.you) dot(state.you.dx ?? state.you.x, state.you.dy ?? state.you.y, '#e0a045', 3);
  c.strokeStyle = 'rgba(224,160,69,0.4)';
  c.strokeRect(0.5, 0.5, w - 1, h - 1);
}
