/** Canvas 2D world. TILE 48. No external images. */
import { TILE, hueFromName, lerp, clamp } from '/shared/constants.js';
import { T } from '/shared/tiles.js';
import { MOBS, NODES, item, npcs as npcTable } from '/shared/catalog.js';

const PAL = {
  [T.VOID]:     ['#05040a', '#030208'],
  [T.GRASS]:    ['#1a2c18', '#243a22'],
  [T.GRASS_D]:  ['#142214', '#1a2c18'],
  [T.TALL]:     ['#1c341c', '#274428'],
  [T.PATH]:     ['#4a3a26', '#5c4a32'],
  [T.STONE]:    ['#4a4640', '#3a3834'],
  [T.DIRT]:     ['#3a2c1e', '#2e2218'],
  [T.WATER]:    ['#163848', '#1c4a5c'],
  [T.WATER_D]:  ['#0c2430', '#123040'],
  [T.SAND]:     ['#5c4c34', '#6a5840'],
  [T.WOOD]:     ['#4a301c', '#3a2416'],
  [T.RUG]:      ['#5a2030', '#6e2840'],
  [T.FLAG]:     ['#3e3c38', '#4c4a44'],
  [T.ASH]:      ['#2a2420', '#342c28'],
  [T.MOSS]:     ['#243a22', '#2c4a28'],
  [T.FLOWER]:   ['#2a2840', '#3a3060'],
  [T.HEARTH]:   ['#c45c18', '#e87828'],
  [T.DOCK]:     ['#3a2a16', '#4a3820'],
  [T.SHRINE]:   ['#3a2860', '#4c3890'],
  [T.LEAVES]:   ['#2a3418', '#324020'],
  [T.ROAD]:     ['#2a2a2e', '#3a3a40'],
  [T.NEON]:     ['#2a1030', '#4a1850'],
  [T.FENCE]:    ['#4a3820', '#3a2c18'],
  [T.CONCRETE]: ['#3a3a40', '#44444c'],
};

function hash(x, y) {
  let n = (x * 374761393 + y * 668265263) | 0;
  n = (n ^ (n >>> 13)) * 1274126177;
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
}

export function createRenderer(canvas, mini) {
  const ctx = canvas.getContext('2d');
  const mctx = mini.getContext('2d');
  let cssW = 0, cssH = 0, dpr = 1;
  let cam = { x: 18.5, y: 10.5 };
  let snapped = false;

  function resize() {
    dpr = Math.min(2, window.devicePixelRatio || 1);
    cssW = canvas.clientWidth || window.innerWidth;
    cssH = canvas.clientHeight || window.innerHeight;
    canvas.width = Math.max(1, Math.floor(cssW * dpr));
    canvas.height = Math.max(1, Math.floor(cssH * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener('resize', resize);

  function follow(state, dt) {
    const me = state.you ? state.players.get(state.you) : null;
    if (!me) return;
    const tx = me.rx ?? me.x;
    const ty = me.ry ?? me.y;
    if (!snapped) {
      cam.x = tx; cam.y = ty; snapped = true;
      return;
    }
    const k = 1 - Math.pow(0.0008, (dt || 16) / 16);
    cam.x = lerp(cam.x, tx, k);
    cam.y = lerp(cam.y, ty, k);
  }

  function sx(x) { return (x - cam.x) * TILE + cssW / 2; }
  function sy(y) { return (y - cam.y) * TILE + cssH / 2; }

  function worldFromEvent(ev) {
    const r = canvas.getBoundingClientRect();
    const px = (ev.clientX - r.left) * (cssW / r.width);
    const py = (ev.clientY - r.top) * (cssH / r.height);
    return {
      x: cam.x + (px - cssW / 2) / TILE,
      y: cam.y + (py - cssH / 2) / TILE,
    };
  }

  function hitTest(wx, wy, state) {
    let best = null, bestD = 0.55;
    for (const p of state.players.values()) {
      if (p.id === state.you) continue;
      const d = Math.hypot(wx - (p.rx ?? p.x), wy - (p.ry ?? p.y));
      if (d < bestD) {
        bestD = d;
        best = { kind: 'player', id: p.id, name: p.name, x: p.x, y: p.y, hp: p.hp, maxHp: p.maxHp };
      }
    }
    for (const e of state.entities.values()) {
      if (e.kind === 'mob' && (e.dead || e.alive === false)) continue;
      if (e.kind === 'node' && (e.depleted || e.alive === false)) continue;
      const rad = e.kind === 'mob' ? (e.size || 0.7) * 0.55 : 0.48;
      const d = Math.hypot(wx - (e.rx ?? e.x), wy - (e.ry ?? e.y));
      if (d < Math.max(bestD, rad)) {
        bestD = d;
        best = {
          kind: e.kind, id: e.id, name: e.name, type: e.type,
          x: e.x, y: e.y, hp: e.hp, maxHp: e.maxHp, qty: e.qty,
        };
      }
    }
    return best;
  }

  function draw(state, dt, now) {
    follow(state, dt);
    ctx.clearRect(0, 0, cssW, cssH);
    ctx.fillStyle = '#07050c';
    ctx.fillRect(0, 0, cssW, cssH);
    const w = state.w || 0, h = state.h || 0;
    if (!w || !state.tiles) return;

    const t = now || performance.now();
    const x0 = Math.max(0, Math.floor(cam.x - cssW / TILE / 2) - 1);
    const y0 = Math.max(0, Math.floor(cam.y - cssH / TILE / 2) - 1);
    const x1 = Math.min(w, Math.ceil(cam.x + cssW / TILE / 2) + 1);
    const y1 = Math.min(h, Math.ceil(cam.y + cssH / TILE / 2) + 1);

    drawTiles(state, x0, y0, x1, y1, t);
    drawWater(state, x0, y0, x1, y1, t);
    drawProps(state);
    drawGroundItems(state);
    const sprites = collectSprites(state, t);
    sprites.sort((a, b) => a.y - b.y);
    for (const s of sprites) s.draw();
    drawLights(state, t);
    drawVignette();
    drawSelection(state);
    drawMarker(state, t);
    drawFloats(state, t);
    drawMinimap(state);
  }

  function tileAt(state, x, y) {
    if (x < 0 || y < 0 || x >= state.w || y >= state.h) return 0;
    return state.tiles[y * state.w + x] | 0;
  }

  function drawTiles(state, x0, y0, x1, y1, t) {
    for (let y = y0; y < y1; y++) {
      for (let x = x0; x < x1; x++) {
        const id = tileAt(state, x, y);
        const pal = PAL[id] || PAL[T.GRASS];
        const n = hash(x, y);
        const px = sx(x), py = sy(y);
        ctx.fillStyle = n > 0.55 ? pal[1] : pal[0];
        ctx.fillRect(px, py, TILE + 0.6, TILE + 0.6);
        if (id === T.FLOWER && n > 0.4) {
          ctx.fillStyle = n > 0.7 ? '#c77dff' : '#90be6d';
          ctx.beginPath();
          ctx.arc(px + 10 + n * 28, py + 12 + (1 - n) * 24, 2.2, 0, Math.PI * 2);
          ctx.fill();
        }
        if (id === T.HEARTH) {
          const g = ctx.createRadialGradient(px + 24, py + 24, 2, px + 24, py + 24, 26);
          const pulse = 0.55 + Math.sin(t * 0.006 + x) * 0.2;
          g.addColorStop(0, `rgba(255,200,80,${pulse})`);
          g.addColorStop(1, 'rgba(180,40,0,0.15)');
          ctx.fillStyle = g;
          ctx.fillRect(px, py, TILE, TILE);
        }
        if (id === T.SHRINE) {
          ctx.strokeStyle = 'rgba(180,140,255,0.35)';
          ctx.lineWidth = 1.5;
          ctx.strokeRect(px + 8, py + 8, TILE - 16, TILE - 16);
        }
        if (id === T.TALL) {
          ctx.fillStyle = 'rgba(40,80,40,0.35)';
          ctx.fillRect(px + n * 20, py + 8, 3, 18);
        }
        if (id === T.ROAD) {
          ctx.fillStyle = 'rgba(200,180,80,0.28)';
          if (y % 2 === 0) ctx.fillRect(px + TILE * 0.42, py + 6, 4, 10);
          ctx.fillStyle = 'rgba(220,220,230,0.18)';
          ctx.fillRect(px, py + 2, TILE, 1.5);
          ctx.fillRect(px, py + TILE - 3, TILE, 1.5);
        }
        if (id === T.FENCE) {
          ctx.fillStyle = '#2a1c10';
          ctx.fillRect(px + 6, py + 10, 4, 28);
          ctx.fillRect(px + 22, py + 8, 4, 30);
          ctx.fillRect(px + 38, py + 11, 4, 26);
          ctx.fillStyle = '#5a4030';
          ctx.fillRect(px + 2, py + 16, TILE - 4, 4);
          ctx.fillRect(px + 2, py + 28, TILE - 4, 4);
        }
        if (id === T.CONCRETE && n > 0.72) {
          ctx.strokeStyle = 'rgba(255,255,255,0.08)';
          ctx.lineWidth = 1;
          ctx.strokeRect(px + 4, py + 4, TILE - 8, TILE - 8);
        }
        if (id === T.WOOD) {
          ctx.fillStyle = 'rgba(0,0,0,0.12)';
          ctx.fillRect(px, py + 16, TILE, 1);
          ctx.fillRect(px, py + 32, TILE, 1);
        }
      }
    }
  }

  function drawWater(state, x0, y0, x1, y1, t) {
    ctx.save();
    for (let y = y0; y < y1; y++) {
      for (let x = x0; x < x1; x++) {
        const id = tileAt(state, x, y);
        if (id !== T.WATER && id !== T.WATER_D) continue;
        const px = sx(x), py = sy(y);
        const wave = Math.sin(t * 0.003 + x * 0.7 + y * 0.5) * 4;
        ctx.strokeStyle = id === T.WATER_D ? 'rgba(80,160,190,0.18)' : 'rgba(120,200,220,0.22)';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(px, py + 18 + wave);
        ctx.quadraticCurveTo(px + 24, py + 14 + wave, px + TILE, py + 20 + wave);
        ctx.stroke();
        if (hash(x, y) > 0.82) {
          ctx.fillStyle = 'rgba(200,240,255,0.15)';
          ctx.fillRect(px + 16, py + 10 + wave * 0.4, 6, 1.5);
        }
      }
    }
    ctx.restore();
  }

  function drawProps(state) {
    for (const p of state.props || []) {
      const x = sx(p.x), y = sy(p.y);
      if (p.kind === 'hut') {
        const bw = p.w * TILE, bh = p.h * TILE;
        ctx.fillStyle = 'rgba(20,12,8,0.35)';
        ctx.fillRect(x - 4, y - 10, bw + 8, 18);
        ctx.strokeStyle = 'rgba(70,40,20,0.9)';
        ctx.lineWidth = 6;
        ctx.strokeRect(x + 3, y + 3, bw - 6, bh - 6);
        ctx.fillStyle = 'rgba(90,40,20,0.55)';
        ctx.beginPath();
        ctx.moveTo(x - 6, y + 8);
        ctx.lineTo(x + bw / 2, y - 18);
        ctx.lineTo(x + bw + 6, y + 8);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = 'rgba(40,20,10,0.8)';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      } else if (p.kind === 'house') {
        const bw = p.w * TILE, bh = p.h * TILE;
        const pal = p.palette || ['#4a2018', '#2a1c14'];
        ctx.strokeStyle = pal[0];
        ctx.lineWidth = 5;
        ctx.strokeRect(x + 2, y + 2, bw - 4, bh - 4);
        ctx.fillStyle = 'rgba(140,180,200,0.35)';
        ctx.fillRect(x + TILE * 0.7, y + 5, 16, 7);
        ctx.fillRect(x + bw - TILE * 0.7 - 16, y + 5, 16, 7);
        const doorX = x + ((p.w / 2) | 0) * TILE;
        ctx.fillStyle = pal[1] || '#2a1c14';
        ctx.fillRect(doorX + 10, y + bh - 8, TILE - 20, 8);
      } else if (p.kind === 'car') {
        const hue = p.hue || 20;
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.fillRect(x + 2, y + 18, TILE * 1.8, 8);
        ctx.fillStyle = `hsl(${hue},45%,28%)`;
        ctx.fillRect(x + 4, y + 6, TILE * 1.7, 22);
        ctx.fillStyle = 'rgba(160,200,220,0.35)';
        ctx.fillRect(x + 14, y + 8, 18, 10);
        ctx.fillRect(x + TILE + 8, y + 8, 14, 10);
      } else if (p.kind === 'pump') {
        ctx.fillStyle = '#2a2a30';
        ctx.fillRect(x + 8, y + 4, 16, 28);
        ctx.fillStyle = '#c45c18';
        ctx.fillRect(x + 10, y + 8, 12, 8);
        ctx.strokeStyle = '#888';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x + 24, y + 16);
        ctx.lineTo(x + 32, y + 22);
        ctx.stroke();
      }
    }
    for (const b of state.buildings || []) {
      if (b.kind !== 'shop') continue;
      const x = sx(b.x), y = sy(b.y);
      const bw = b.w * TILE, bh = b.h * TILE;
      const pal = b.palette || ['#4a2018'];
      ctx.strokeStyle = pal[0];
      ctx.lineWidth = b.flagship ? 5 : 3.5;
      ctx.strokeRect(x + 2, y + 2, bw - 4, bh - 4);
      ctx.fillStyle = pal[0] + '55';
      ctx.fillRect(x + 6, y + 6, bw - 12, 10);
    }
  }

  function drawGroundItems(state) {
    for (const e of state.entities.values()) {
      if (e.kind !== 'ground') continue;
      const x = sx(e.rx ?? e.x), y = sy(e.ry ?? e.y);
      const def = item(e.item || e.type);
      ctx.fillStyle = def?.kind === 'currency' ? '#ffba08' : def?.kind === 'consumable' ? '#80ed99' : '#c9b8a0';
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.4)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }

  function collectSprites(state, t) {
    const out = [];
    for (const tr of state.trees || []) {
      out.push({ y: tr.y, draw: () => drawTree(tr, t) });
    }
    for (const rk of state.rocks || []) {
      out.push({ y: rk.y, draw: () => drawRock(rk) });
    }
    for (const e of state.entities.values()) {
      if (e.kind === 'ground') continue;
      out.push({ y: e.ry ?? e.y, draw: () => drawEntity(e, t) });
    }
    for (const p of state.players.values()) {
      out.push({ y: p.ry ?? p.y, draw: () => drawPlayer(p, p.id === state.you, t) });
    }
    return out;
  }

  function drawTree(tr, t) {
    const x = sx(tr.x + 0.5), y = sy(tr.y + 0.5);
    const dead = tr.variant === 3;
    const hue = tr.hue ?? (dead ? 30 : 130);
    ctx.fillStyle = 'rgba(0,0,0,0.28)';
    ctx.beginPath();
    ctx.ellipse(x, y + 8, 10, 4, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = dead ? '#3a2a1c' : '#2a1c10';
    ctx.fillRect(x - 3, y - 8, 6, 18);
    if (dead) {
      ctx.strokeStyle = `hsla(${hue},30%,35%,0.9)`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x, y - 8);
      ctx.lineTo(x - 10, y - 22);
      ctx.moveTo(x, y - 6);
      ctx.lineTo(x + 12, y - 20);
      ctx.stroke();
      return;
    }
    const sway = Math.sin(t * 0.0015 + tr.x) * 2;
    ctx.fillStyle = `hsla(${hue},40%,22%,0.95)`;
    ctx.beginPath();
    ctx.ellipse(x + sway, y - 22, 18, 16, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = `hsla(${hue},45%,28%,0.9)`;
    ctx.beginPath();
    ctx.ellipse(x - 8 + sway, y - 16, 12, 10, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawRock(rk) {
    const x = sx(rk.x + 0.5), y = sy(rk.y + 0.5);
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    ctx.beginPath();
    ctx.ellipse(x, y + 4, 9, 3.5, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = rk.variant ? '#5a534c' : '#3e3a36';
    ctx.beginPath();
    ctx.moveTo(x - 10, y + 4);
    ctx.lineTo(x - 4, y - 8);
    ctx.lineTo(x + 8, y - 5);
    ctx.lineTo(x + 11, y + 5);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.08)';
    ctx.fillRect(x - 2, y - 6, 4, 3);
  }

  function drawPlayer(p, mine, t) {
    const x = sx(p.rx ?? p.x), y = sy(p.ry ?? p.y);
    const hue = p.hue ?? hueFromName(p.name || '?');
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.beginPath();
    ctx.ellipse(x, y + 10, 9, 4, 0, 0, Math.PI * 2);
    ctx.fill();
    const bob = (p.walking || p.action === 'walk') ? Math.sin(t * 0.012) * 1.5 : 0;
    ctx.fillStyle = `hsl(${hue},55%,48%)`;
    ctx.beginPath();
    ctx.arc(x, y - 2 + bob, mine ? 11 : 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = mine ? '#ffba08' : 'rgba(0,0,0,0.5)';
    ctx.lineWidth = mine ? 2 : 1;
    ctx.stroke();
    ctx.fillStyle = `hsl(${hue},40%,72%)`;
    ctx.beginPath();
    ctx.arc(x, y - 12 + bob, 6, 0, Math.PI * 2);
    ctx.fill();
    const hp = Math.max(0, p.hp / Math.max(1, p.maxHp));
    drawHpBar(x, y - 24 + bob, hp, 22);
    ctx.fillStyle = mine ? '#ffd166' : '#efe6d2';
    ctx.font = '600 11px "Source Sans 3", sans-serif';
    ctx.textAlign = 'center';
    ctx.strokeStyle = 'rgba(0,0,0,0.7)';
    ctx.lineWidth = 3;
    ctx.strokeText(p.name, x, y - 28 + bob);
    ctx.fillText(p.name, x, y - 28 + bob);
  }

  function drawEntity(e, t) {
    const x = sx(e.rx ?? e.x), y = sy(e.ry ?? e.y);
    if (e.kind === 'npc') {
      const def = npcTable()?.[e.type];
      const col = e.color || def?.color || '#c77dff';
      ctx.fillStyle = 'rgba(0,0,0,0.3)';
      ctx.beginPath();
      ctx.ellipse(x, y + 10, 8, 3.5, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.moveTo(x, y - 16);
      ctx.lineTo(x + 11, y + 6);
      ctx.lineTo(x - 11, y + 6);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = '#efe6d2';
      ctx.beginPath();
      ctx.arc(x, y - 6, 5.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = col;
      ctx.font = '600 11px "Source Sans 3", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(e.name || def?.name || '?', x, y - 22);
      return;
    }
    if (e.kind === 'mob') {
      if (e.dead || e.alive === false) return;
      const def = MOBS[e.type] || {};
      const col = e.color || def.color || '#6d6875';
      const size = (e.size || def.size || 0.9) * 14;
      ctx.fillStyle = 'rgba(0,0,0,0.32)';
      ctx.beginPath();
      ctx.ellipse(x, y + size * 0.55, size * 0.7, size * 0.28, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.ellipse(x, y, size, size * 0.72, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#1a1010';
      ctx.beginPath();
      ctx.arc(x - size * 0.3, y - 2, 2.2, 0, Math.PI * 2);
      ctx.arc(x + size * 0.25, y - 2, 2.2, 0, Math.PI * 2);
      ctx.fill();
      const hp = Math.max(0, (e.hp || 0) / Math.max(1, e.maxHp || 1));
      drawHpBar(x, y - size - 8, hp, size * 1.6, '#e85d04');
      ctx.fillStyle = '#c9b8a0';
      ctx.font = '10px "Source Sans 3", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(e.name || def.name || 'beast', x, y - size - 12);
      return;
    }
    if (e.kind === 'node') {
      const spent = e.depleted || e.alive === false;
      const def = NODES[e.type] || {};
      ctx.globalAlpha = spent ? 0.35 : 1;
      const typ = e.type || '';
      if (typ.includes('tree') || typ === 'emberwood_tree' || typ === 'honeycomb_hive') {
        ctx.fillStyle = spent ? '#3a2a18' : (typ === 'honeycomb_hive' ? '#d4a017' : '#c45c18');
        ctx.fillRect(x - 3, y - 6, 6, 14);
        ctx.fillStyle = spent ? '#2a2418' : (typ === 'honeycomb_hive' ? '#e8c84a' : '#6a994e');
        ctx.beginPath();
        ctx.arc(x, y - 14, 12, 0, Math.PI * 2);
        ctx.fill();
      } else if (typ.includes('iron') || typ === 'iron_outcrop' || typ === 'scrap_pile') {
        ctx.fillStyle = spent ? '#3a3a40' : '#8d99ae';
        ctx.beginPath();
        ctx.moveTo(x - 10, y + 6);
        ctx.lineTo(x, y - 12);
        ctx.lineTo(x + 12, y + 6);
        ctx.closePath();
        ctx.fill();
      } else if (typ === 'dumpster') {
        ctx.fillStyle = spent ? '#2a3030' : '#3d5c4a';
        ctx.fillRect(x - 12, y - 8, 24, 16);
        ctx.fillStyle = 'rgba(0,0,0,0.25)';
        ctx.fillRect(x - 12, y - 8, 24, 4);
      } else if (typ === 'toolbox' || typ === 'kitchen_stash' || typ === 'closet_stash' || typ === 'med_cabinet') {
        ctx.fillStyle = spent ? '#3a3028' : (typ === 'med_cabinet' ? '#8ab4c8' : '#6a4a30');
        ctx.fillRect(x - 10, y - 10, 20, 18);
        ctx.fillStyle = 'rgba(255,255,255,0.15)';
        ctx.fillRect(x - 8, y - 6, 7, 6);
        ctx.fillRect(x + 1, y - 6, 7, 6);
      } else if (typ === 'gas_canister') {
        ctx.fillStyle = spent ? '#3a2010' : '#c45c18';
        ctx.fillRect(x - 7, y - 10, 14, 18);
        ctx.fillStyle = '#2a2a30';
        ctx.fillRect(x - 3, y - 14, 6, 5);
      } else {
        ctx.fillStyle = spent ? '#2a3040' : '#c77dff';
        ctx.beginPath();
        ctx.arc(x, y, 7, 0, Math.PI * 2);
        ctx.fill();
        if (!spent) {
          ctx.fillStyle = 'rgba(255,255,255,0.45)';
          ctx.beginPath();
          ctx.arc(x - 2, y - 2, 2, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
      ctx.fillStyle = spent ? '#6b5e4a' : '#efe6d2';
      ctx.font = '10px "Source Sans 3", sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(e.name || def.name || 'node', x, y - 20);
    }
  }

  function drawHpBar(x, y, frac, width, color) {
    const w = width || 22;
    ctx.fillStyle = '#1a1010';
    ctx.fillRect(x - w / 2, y, w, 4);
    ctx.fillStyle = color || (frac > 0.4 ? '#80ed99' : '#e85d04');
    ctx.fillRect(x - w / 2, y, w * clamp(frac, 0, 1), 4);
  }

  function drawLights(state, t) {
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = 'rgba(18, 10, 28, 0.55)';
    ctx.fillRect(0, 0, cssW, cssH);
    ctx.globalCompositeOperation = 'lighter';
    for (const L of state.lights || []) {
      const x = sx(L.x), y = sy(L.y);
      const flick = 0.82 + Math.sin(t * 0.007 * (L.flicker || 1) + L.x) * 0.12 * (L.flicker || 1);
      const col = L.color || [255, 140, 50];
      const r = (L.r || 4) * TILE * flick;
      const g = ctx.createRadialGradient(x, y, 4, x, y, r);
      g.addColorStop(0, `rgba(${col[0]},${col[1]},${col[2]},${0.28 * flick})`);
      g.addColorStop(0.45, `rgba(${col[0]},${col[1]},${col[2]},${0.08 * flick})`);
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function drawVignette() {
    const g = ctx.createRadialGradient(cssW / 2, cssH / 2, cssH * 0.25, cssW / 2, cssH / 2, cssH * 0.78);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(1, 'rgba(4,2,8,0.55)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, cssW, cssH);
  }

  function drawSelection(state) {
    const sel = state.selected;
    if (!sel) return;
    let pos = null;
    if (sel.kind === 'player') pos = state.players.get(sel.id);
    else pos = state.entities.get(sel.id);
    if (!pos) return;
    const x = sx(pos.rx ?? pos.x), y = sy(pos.ry ?? pos.y);
    ctx.strokeStyle = 'rgba(255, 186, 8, 0.85)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(x, y + 12, 14, 6, 0, 0, Math.PI * 2);
    ctx.stroke();
  }

  function drawMarker(state, t) {
    const m = state.clickMarker;
    if (!m) return;
    const age = t - m.t;
    if (age > 900) { state.clickMarker = null; return; }
    const a = 1 - age / 900;
    const x = sx(m.x), y = sy(m.y);
    ctx.strokeStyle = `rgba(232,93,4,${a})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, 8 + (1 - a) * 10, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x - 5, y); ctx.lineTo(x + 5, y);
    ctx.moveTo(x, y - 5); ctx.lineTo(x, y + 5);
    ctx.stroke();
  }

  function drawFloats(state, t) {
    const keep = [];
    for (const f of state.floats) {
      const age = t - (f.born || f.t || t);
      if (age > 1400) continue;
      keep.push(f);
      const a = 1 - age / 1400;
      const x = sx(f.x);
      const y = sy(f.y) - age * 0.04;
      ctx.globalAlpha = a;
      ctx.fillStyle = f.color || '#ffd166';
      ctx.font = '700 13px Cinzel, serif';
      ctx.textAlign = 'center';
      ctx.strokeStyle = 'rgba(0,0,0,0.6)';
      ctx.lineWidth = 3;
      ctx.strokeText(String(f.text), x, y);
      ctx.fillText(String(f.text), x, y);
      ctx.globalAlpha = 1;
    }
    state.floats = keep;
  }

  function drawMinimap(state) {
    const mw = mini.width, mh = mini.height;
    mctx.fillStyle = '#0a0810';
    mctx.fillRect(0, 0, mw, mh);
    const tw = state.w, th = state.h;
    if (!tw) return;
    const sxm = mw / tw, sym = mh / th;
    for (let y = 0; y < th; y++) {
      for (let x = 0; x < tw; x++) {
        const id = tileAt(state, x, y);
        mctx.fillStyle = (PAL[id] || PAL[1])[0];
        mctx.fillRect(x * sxm, y * sym, sxm + 0.4, sym + 0.4);
      }
    }
    mctx.fillStyle = '#90be6d';
    for (const e of state.entities.values()) {
      if (e.kind !== 'node' || e.depleted || e.alive === false) continue;
      mctx.fillRect(e.x * sxm - 1, e.y * sym - 1, 3, 3);
    }
    mctx.fillStyle = '#e85d04';
    for (const e of state.entities.values()) {
      if (e.kind !== 'mob' || e.dead || e.alive === false) continue;
      mctx.fillRect(e.x * sxm - 1.5, e.y * sym - 1.5, 3, 3);
    }
    mctx.fillStyle = '#c77dff';
    for (const e of state.entities.values()) {
      if (e.kind !== 'npc') continue;
      mctx.fillRect(e.x * sxm - 2, e.y * sym - 2, 4, 4);
    }
    for (const p of state.players.values()) {
      mctx.fillStyle = p.id === state.you ? '#ffba08' : `hsl(${p.hue || 0},70%,60%)`;
      mctx.beginPath();
      mctx.arc((p.rx ?? p.x) * sxm, (p.ry ?? p.y) * sym, p.id === state.you ? 3.2 : 2.4, 0, Math.PI * 2);
      mctx.fill();
    }
    const vw = (cssW / TILE) * sxm, vh = (cssH / TILE) * sym;
    mctx.strokeStyle = 'rgba(240,212,138,0.5)';
    mctx.strokeRect(cam.x * sxm - vw / 2, cam.y * sym - vh / 2, vw, vh);
  }

  function resetCam() { snapped = false; }

  return { draw, worldFromEvent, hitTest, resize, resetCam, get cam() { return cam; } };
}
