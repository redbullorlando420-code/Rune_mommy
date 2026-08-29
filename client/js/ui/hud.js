import { xpToLevel } from '/shared/constants.js';
import { drawMinimap } from '../engine/renderer.js';

export function toast(text, kind = 'info') {
  const host = document.getElementById('notify');
  const n = document.createElement('div');
  n.className = 'toast ' + kind;
  n.textContent = text;
  host.appendChild(n);
  setTimeout(() => n.remove(), 3400);
}

export function bindHud(state, map) {
  document.querySelectorAll('[data-close]').forEach((b) => {
    b.addEventListener('click', () => {
      document.getElementById(b.dataset.close)?.classList.add('hidden');
    });
  });
  document.getElementById('btn-craft')?.addEventListener('click', () => {
    document.getElementById('craft').classList.toggle('hidden');
  });
}

export function renderHud(state, map) {
  const you = state.you;
  if (!you) return;
  const hp = Math.round(you.hp || 0);
  const max = you.maxHp || 40;
  document.getElementById('hp-text').textContent = `${hp} / ${max}`;
  document.getElementById('hp-fill').style.width = `${Math.max(0, Math.min(100, (hp / max) * 100))}%`;
  const skills = you.skills || {};
  for (const id of ['combat', 'foraging', 'binding']) {
    const el = document.querySelector(`.sk[data-sk="${id}"] span`);
    if (el) el.textContent = String(xpToLevel(skills[id] || 0).level);
  }
  const coin = document.getElementById('coin-count');
  if (coin) coin.textContent = `${you.coins || 0} ember`;
  const chip = document.getElementById('target-chip');
  if (state.selected) {
    const ent = find(state, state.selected);
    if (ent) {
      chip.classList.remove('hidden');
      chip.textContent = ent.name || ent.type || 'target';
    } else chip.classList.add('hidden');
  } else chip.classList.add('hidden');
  drawMinimap(document.getElementById('minimap'), state, map);
}

function find(state, id) {
  for (const a of [state.npcs, state.nodes, state.mobs, state.players, state.ground]) {
    const h = (a || []).find((e) => e.id === id);
    if (h) return h;
  }
  return null;
}
