import { C2S } from '/shared/protocol.js';
import { send } from '../net/client.js';
import { screenToWorld, camera } from './camera.js';
import { viewSize } from './renderer.js';
import { TILE } from '/shared/constants.js';

export function bindInput(canvas, state) {
  const ctxMenu = document.getElementById('ctx');

  canvas.addEventListener('contextmenu', (e) => e.preventDefault());

  canvas.addEventListener('mousedown', (e) => {
    if (e.button !== 0 && e.button !== 2) return;
    const rect = canvas.getBoundingClientRect();
    const { w, h } = viewSize();
    const sx = (e.clientX - rect.left) * (w / rect.width);
    const sy = (e.clientY - rect.top) * (h / rect.height);
    const world = screenToWorld(sx, sy, w, h);
    hideCtx();

    const hit = pick(state, world.x, world.y);
    if (hit) {
      state.selected = hit.id;
      if (hit.kind === 'player') {
        showCtx(e.clientX, e.clientY, hit);
        return;
      }
      if (hit.kind === 'mob') {
        send(C2S.ATTACK, { id: hit.id });
        return;
      }
      if (hit.kind === 'npc' || hit.kind === 'node' || hit.kind === 'ground') {
        send(C2S.INTERACT, { id: hit.id, x: world.x, y: world.y });
        return;
      }
    }
    state.selected = null;
    state.dest = { x: world.x, y: world.y };
    send(C2S.MOVE, { x: world.x, y: world.y });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const inp = document.getElementById('chat-input');
      if (document.activeElement === inp) return;
      e.preventDefault();
      inp.focus();
    }
    if (e.key === 'i' || e.key === 'I') {
      if (typing()) return;
      document.getElementById('inv-panel').classList.toggle('collapsed');
    }
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal').forEach((m) => m.classList.add('hidden'));
      document.getElementById('npc-box')?.classList.add('hidden');
      hideCtx();
    }
    if ((e.key === 'c' || e.key === 'C') && !typing()) {
      document.getElementById('chat-input').focus();
    }
    if ((e.key === 'k' || e.key === 'K') && !typing()) {
      document.getElementById('craft')?.classList.toggle('hidden');
    }
  });

  ctxMenu.addEventListener('click', (e) => {
    const act = e.target.closest('button')?.dataset.act;
    const id = ctxMenu.dataset.id;
    hideCtx();
    if (act === 'trade' && id) send(C2S.TRADE_REQ, { id });
  });

  document.addEventListener('click', (e) => {
    if (!ctxMenu.contains(e.target)) hideCtx();
  });

  function showCtx(x, y, hit) {
    ctxMenu.dataset.id = hit.id;
    ctxMenu.classList.remove('hidden');
    ctxMenu.style.left = x + 'px';
    ctxMenu.style.top = y + 'px';
  }
  function hideCtx() { ctxMenu.classList.add('hidden'); }
}

function typing() {
  const a = document.activeElement;
  return a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA');
}

function pick(state, x, y) {
  let best = null, bestD = 0.62;
  const consider = (ent, kind, px, py) => {
    const d = Math.hypot((px ?? ent.dx ?? ent.x) - x, (py ?? ent.dy ?? ent.y) - y);
    const r = kind === 'mob' ? 0.7 : 0.55;
    if (d < r && d < bestD) { bestD = d; best = { ...ent, kind }; }
  };
  for (const n of state.npcs || []) consider(n, 'npc');
  for (const n of state.nodes || []) if (n.alive) consider(n, 'node');
  for (const m of state.mobs || []) if (m.alive) consider(m, 'mob');
  for (const g of state.ground || []) consider(g, 'ground');
  for (const p of state.players || []) consider(p, 'player');
  return best;
}

export { TILE, camera };
