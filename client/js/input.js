/** Canvas clicks to world coords. Empty=MOVE, entity=INTERACT, other player=TRADE_REQ. */
import { dist } from '/shared/constants.js';

const TYPING = new Set(['INPUT', 'TEXTAREA', 'SELECT']);

export function bindInput(canvas, api) {
  const { state, net, renderer, ui } = api;

  canvas.addEventListener('click', (ev) => {
    ev.preventDefault();
    hideCtx();
    if (!state.you) return;
    const wpt = renderer.worldFromEvent(ev);
    if (!wpt) return;
    const hit = renderer.hitTest(wpt.x, wpt.y, state);
    state.clickMarker = { x: wpt.x, y: wpt.y, t: performance.now() };

    if (hit && hit.kind === 'player' && hit.id !== state.you) {
      state.lastPlayerId = hit.id;
      state.selected = { kind: 'player', id: hit.id };
      ui.showTarget(hit);
      net.tradeReq(hit.id);
      ui.toast('Trade offered.', 'trade');
      return;
    }
    if (hit && hit.id !== state.you) {
      state.selected = { kind: hit.kind, id: hit.id };
      ui.showTarget(hit);
      const me = state.players.get(state.you);
      if (me && dist(me, hit) > 1.7) {
        net.move(hit.x, hit.y);
        state.pendingInteract = { id: hit.id, kind: hit.kind, until: Date.now() + 8000 };
      }
      net.interact(hit.id);
      return;
    }
    state.selected = null;
    ui.hideTarget();
    net.move(wpt.x, wpt.y);
  });

  canvas.addEventListener('contextmenu', (ev) => {
    ev.preventDefault();
    if (!state.you) return;
    const wpt = renderer.worldFromEvent(ev);
    const hit = renderer.hitTest(wpt.x, wpt.y, state);
    if (hit && hit.kind === 'player' && hit.id !== state.you) {
      state.lastPlayerId = hit.id;
      showCtx(ev.clientX, ev.clientY, [
        { label: 'Trade with ' + hit.name, fn: () => net.tradeReq(hit.id) },
        { label: 'Walk there', fn: () => net.move(hit.x, hit.y) },
      ]);
      return;
    }
    if (hit && hit.kind === 'mob') {
      showCtx(ev.clientX, ev.clientY, [
        { label: 'Attack ' + (hit.name || 'beast'), fn: () => net.attack(hit.id) },
        { label: 'Walk there', fn: () => net.move(hit.x, hit.y) },
      ]);
      return;
    }
    if (hit) {
      showCtx(ev.clientX, ev.clientY, [
        { label: 'Use ' + (hit.name || 'it'), fn: () => net.interact(hit.id) },
        { label: 'Walk there', fn: () => net.move(hit.x, hit.y) },
      ]);
    }
  });

  canvas.addEventListener('mousemove', (ev) => {
    const wpt = renderer.worldFromEvent(ev);
    if (!wpt) { state.hover = null; return; }
    state.hover = renderer.hitTest(wpt.x, wpt.y, state);
    canvas.style.cursor = state.hover ? 'pointer' : 'crosshair';
  });

  window.addEventListener('keydown', (ev) => {
    const tag = (ev.target && ev.target.tagName) || '';
    const typing = TYPING.has(tag);
    if (ev.key === 'Escape') {
      ui.closeModals();
      hideCtx();
      if (typing) ev.target.blur();
      return;
    }
    if (ev.key === 'Enter') {
      if (typing) return;
      ev.preventDefault();
      document.getElementById('chatIn').focus();
      return;
    }
    if (typing) return;
    const k = ev.key.toLowerCase();
    if (k === 'i') { ev.preventDefault(); ui.toggle('panelInv'); }
    else if (k === 'k') { ev.preventDefault(); ui.toggle('panelSkills'); }
    else if (k === 'm') { ev.preventDefault(); ui.toggle('panelMap'); }
    else if (k === 'b') { ev.preventDefault(); ui.toggle('panelCraft'); }
    else if (k === 'c') {
      ev.preventDefault();
      document.getElementById('chatIn').focus();
    } else if (k === 't') {
      ev.preventDefault();
      if (state.lastPlayerId) net.tradeReq(state.lastPlayerId);
      else ui.toast('Click a wanderer first.', 'warn');
    }
  });

  document.addEventListener('click', (ev) => {
    const ctx = document.getElementById('ctx');
    if (ctx && !ctx.contains(ev.target) && ev.target !== canvas) hideCtx();
  });

  function showCtx(x, y, items) {
    const el = document.getElementById('ctx');
    el.innerHTML = '';
    for (const it of items) {
      const b = document.createElement('button');
      b.textContent = it.label;
      b.addEventListener('click', () => { hideCtx(); it.fn(); });
      el.appendChild(b);
    }
    el.classList.remove('hidden');
    el.style.left = x + 'px';
    el.style.top = y + 'px';
  }

  function hideCtx() {
    document.getElementById('ctx').classList.add('hidden');
  }

  return {
    tickPending() {
      const pend = state.pendingInteract;
      if (!pend || !state.you) return;
      if (Date.now() > pend.until) { state.pendingInteract = null; return; }
      const me = state.players.get(state.you);
      const e = find(state, pend.id);
      if (!me || !e) { state.pendingInteract = null; return; }
      if (dist(me, e) <= 1.65) {
        net.interact(pend.id);
        state.pendingInteract = null;
      }
    },
  };
}

function find(state, id) {
  const p = state.players.get(id);
  if (p) return p;
  return state.entities.get(id);
}
