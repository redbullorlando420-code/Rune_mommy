import { C2S, S2C } from '/shared/protocol.js';
import { loadCatalog, item, recipes, items as itemTable } from '/shared/catalog.js';
import { NAME_RE, xpToLevel, INV_SIZE, BANK_SIZE } from '/shared/constants.js';
import { connect, send, on } from './net/client.js';
import { createRenderer } from './render.js';

const state = {
  you: null,
  me: null,
  players: new Map(),
  entities: new Map(),
  tiles: null,
  w: 0,
  h: 0,
  trees: [],
  rocks: [],
  lights: [],
  props: [],
  buildings: [],
  pois: [],
  dest: null,
  selected: null,
  shopOpen: false,
  bankOpen: false,
};

let running = false;
let last = performance.now();
let itemsReady = false;

await loadCatalog(async (name) => {
  const r = await fetch('/data/' + name);
  if (!r.ok) throw new Error('missing ' + name);
  return r.json();
});
itemsReady = true;

const canvas = document.getElementById('view');
const mini = document.getElementById('minimap');
const gfx = createRenderer(canvas, mini);
function listOf(m) { return m instanceof Map ? [...m.values()] : (m || []); }
function toMap(arr) {
  const m = new Map();
  for (const x of arr || []) if (x && x.id) m.set(x.id, x);
  return m;
}

function $(id) { return document.getElementById(id); }
function toast(text, kind) {
  const host = $('toasts');
  if (!host) return;
  const n = document.createElement('div');
  n.className = 'toast ' + (kind || 'info');
  n.textContent = text;
  host.appendChild(n);
  setTimeout(() => n.remove(), 3200);
}
function show(id, on) {
  const el = $(id);
  if (!el) return;
  el.classList.toggle('hidden', on === false);
}

const saved = localStorage.getItem('rm-name');
if (saved && $('nameIn')) $('nameIn').value = saved;

$('joinForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const err = $('loginErr');
  err.textContent = '';
  const name = $('nameIn').value.trim();
  if (!NAME_RE.test(name)) {
    err.textContent = 'Name: start with a letter, 2-16 characters.';
    return;
  }
  localStorage.setItem('rm-name', name);
  try { await connect(); }
  catch { err.textContent = 'Could not reach the server.'; return; }
  send(C2S.JOIN, { name });
});

on(S2C.REJECT, (p) => { $('loginErr').textContent = p.reason || 'Turned away.'; });

on(S2C.WELCOME, (p) => {
  $('login').classList.add('hidden');
  state.you = p.you;
  state.me = p.me;
  state.w = p.w; state.h = p.h;
  state.tiles = p.tiles;
  state.trees = p.trees || [];
  state.rocks = p.rocks || [];
  state.lights = p.lights || [];
  state.props = p.props || [];
  state.buildings = p.buildings || [];
  state.pois = p.pois || [];
  state.players = toMap(p.players);
  state.entities = toMap(p.entities);
  if (p.zone?.name && $('zoneName')) $('zoneName').textContent = p.zone.name;
  fillPois();
  fillRecipes();
  renderInv();
  renderHud();
  running = true;
  gfx.resize();
  requestAnimationFrame(loop);
  pushChat({ channel: 'system', from: 'Hollow', text: p.zone?.blurb || 'Welcome to Clermont.' });
});

on(S2C.DELTA, (p) => {
  if (p.players) state.players = toMap(p.players);
  if (p.entities) state.entities = toMap(p.entities);
  const me = state.players.get(state.you);
  if (me && state.me) Object.assign(state.me, me);
  if (p.floats) for (const f of p.floats) toast(f.text, 'info');
  renderHud();
  renderMinimap();
});

on(S2C.CHAT, (p) => pushChat(p));
on(S2C.NOTIFY, (p) => toast(p.text, p.kind || 'info'));
on(S2C.INV, (p) => {
  if (state.me) {
    if (p.inv) state.me.inv = p.inv;
    if (p.equip) state.me.equip = p.equip;
  }
  renderInv();
  renderHud();
});
on(S2C.BANK, (p) => {
  if (state.me) state.me.bank = p.items || p.bank;
  renderBank();
});
on(S2C.XP, (p) => {
  if (state.me) {
    state.me.skills = state.me.skills || {};
    if (typeof p.xp === 'number') state.me.skills[p.skill] = { xp: p.xp };
  }
  renderHud();
});
on(S2C.NPC, (p) => {
  show('panelNpc', true);
  $('npcTitle').textContent = (p.name || '') + (p.title ? ' — ' + p.title : '');
  $('npcBody').textContent = p.greet || (p.lines && p.lines[0]) || '';
  const acts = $('npcActions');
  acts.innerHTML = '';
  if (p.shop) {
    const b = document.createElement('button');
    b.className = 'gold';
    b.textContent = 'Shop';
    b.onclick = () => show('panelShop', true);
    acts.appendChild(b);
  }
  if (p.bank) {
    const b = document.createElement('button');
    b.textContent = 'Vault';
    b.onclick = () => { show('panelBank', true); renderBank(); };
    acts.appendChild(b);
  }
});
on(S2C.SHOP, (p) => {
  state.shopOpen = true;
  show('panelShop', true);
  if (p.name) $('shopTitle').textContent = p.name;
  const box = $('shopBuy');
  box.innerHTML = '';
  for (const row of p.list || []) {
    const def = item(row.id);
    const btn = document.createElement('button');
    btn.textContent = (def?.name || row.id) + ' — ' + row.buy + 'c';
    btn.onclick = () => send(C2S.SHOP_BUY, { id: row.id, qty: 1 });
    box.appendChild(btn);
  }
  show('panelInv', true);
  renderInv();
});
on(S2C.TRADE, (p) => onTrade(p));
on('close', () => toast('Connection faded.', 'warn'));

function loop(t) {
  if (!running) return;
  const dt = t - last;
  last = t;
  const me = state.players.get(state.you) || state.me;
  state.me = me ? { ...state.me, ...me } : state.me;
  gfx.draw(state, dt, t);
  requestAnimationFrame(loop);
}

canvas.addEventListener('contextmenu', (e) => e.preventDefault());
canvas.addEventListener('pointerup', (e) => {
  if (e.button !== 0) return;
  const g = gfx.worldFromEvent(e); const hit = gfx.hitTest(g.x, g.y, state);
  if (hit) {
    state.selected = hit.id;
    if (hit.kind === 'player' && hit.id !== state.you) {
      showCtx(e.clientX, e.clientY, hit);
      return;
    }
    if (hit.kind === 'mob') { send(C2S.ATTACK, { id: hit.id }); return; }
    send(C2S.INTERACT, { id: hit.id });
    return;
  }
  /* ground */
  send(C2S.MOVE, { x: g.x, y: g.y });
});

document.addEventListener('keydown', (e) => {
  if (typing()) return;
  if (e.key === 'i' || e.key === 'I') show('panelInv', $('panelInv').classList.contains('hidden'));
  if (e.key === 'k' || e.key === 'K') show('panelSkills', $('panelSkills').classList.contains('hidden'));
  if (e.key === 'm' || e.key === 'M') show('panelMap', $('panelMap').classList.contains('hidden'));
  if (e.key === 'b' || e.key === 'B') show('panelCraft', $('panelCraft').classList.contains('hidden'));
  if (e.key === 'Enter') { e.preventDefault(); $('chatIn').focus(); }
  if (e.key === 'Escape') {
    document.querySelectorAll('.panel, #trade, #tradeAsk, #ctx').forEach((n) => n.classList.add('hidden'));
    state.shopOpen = false;
  }
});

document.querySelectorAll('[data-close]').forEach((b) => {
  b.addEventListener('click', () => show(b.dataset.close, false));
});
document.querySelectorAll('#actionBar [data-act]').forEach((b) => {
  b.addEventListener('click', () => {
    const map = { inv: 'panelInv', skills: 'panelSkills', map: 'panelMap', craft: 'panelCraft' };
    const id = map[b.dataset.act];
    if (id) show(id, $(id).classList.contains('hidden'));
  });
});

$('chatForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const text = $('chatIn').value.trim();
  if (!text) return;
  $('chatIn').value = '';
  const ch = document.querySelector('#chatTabs .on')?.dataset.ch || 'global';
  send(C2S.CHAT, { channel: ch, text });
});
document.querySelectorAll('#chatTabs button').forEach((b) => {
  b.addEventListener('click', () => {
    document.querySelectorAll('#chatTabs button').forEach((x) => x.classList.remove('on'));
    b.classList.add('on');
  });
});

function typing() {
  const a = document.activeElement;
  return a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA');
}

function pushChat(p) {
  const ol = $('chatLog');
  const li = document.createElement('li');
  const ch = p.channel || 'global';
  li.className = ch;
  const who = p.from || 'Hollow';
  li.textContent = (ch === 'whisper' ? '[w] ' : ch === 'system' ? '' : who + ': ') + (p.text || '');
  if (ch === 'system') li.textContent = p.text || '';
  ol.appendChild(li);
  ol.scrollTop = ol.scrollHeight;
}

function renderHud() {
  const me = state.me;
  if (!me) return;
  if ($('meName')) $('meName').textContent = me.name || '';
  const hp = Math.round(me.hp || 0), max = me.maxHp || 40;
  if ($('hpText')) $('hpText').textContent = hp + '/' + max;
  if ($('hpFill')) $('hpFill').style.width = Math.max(0, Math.min(100, (hp / max) * 100)) + '%';
  const skills = me.skills || {};
  const cv = (s) => (typeof s === 'object' ? s.xp : s) || 0;
  const cLv = xpToLevel(cv(skills.combat));
  if ($('meLevel')) $('meLevel').textContent = cLv.level;
  if ($('lvCombat')) $('lvCombat').textContent = cLv.level;
  if ($('lvForage')) $('lvForage').textContent = xpToLevel(cv(skills.foraging)).level;
  if ($('lvBind')) $('lvBind').textContent = xpToLevel(cv(skills.binding)).level;
  if ($('xpFill')) $('xpFill').style.width = (cLv.need ? (cLv.into / cLv.need) * 100 : 0) + '%';
  if ($('xpText')) $('xpText').textContent = 'combat ' + cLv.level;
  const coins = (me.inv || []).reduce((n, s) => n + (s && s.id === 'ember_coin' ? s.qty : 0), 0);
  if ($('coinCount')) $('coinCount').textContent = coins;
  if ($('online')) $('online').textContent = String(state.players.size);
}

function slotEl(stack, i, kind) {
  const d = document.createElement('button');
  d.className = 'slot' + (stack ? '' : ' empty');
  d.dataset.i = i;
  d.dataset.kind = kind;
  if (stack) {
    const def = item(stack.id);
    d.textContent = (def?.name || stack.id).slice(0, 2).toUpperCase();
    d.title = (def?.name || stack.id) + (stack.qty > 1 ? ' x' + stack.qty : '');
    if (stack.qty > 1) {
      const q = document.createElement('span');
      q.className = 'qty';
      q.textContent = stack.qty;
      d.appendChild(q);
    }
  }
  d.onclick = (ev) => onSlot(kind, i, ev.shiftKey);
  return d;
}

function onSlot(kind, i, shift) {
  if (kind === 'inv') {
    if ($('trade') && !$('trade').classList.contains('hidden')) {
      send(C2S.TRADE_SET, { slot: i, qty: 0 });
      return;
    }
    if (state.shopOpen && shift) { send(C2S.SHOP_SELL, { slot: i, qty: 0 }); return; }
    if (state.shopOpen) { send(C2S.SHOP_SELL, { slot: i, qty: 0 }); return; }
    if ($('panelBank') && !$('panelBank').classList.contains('hidden') && shift) {
      send(C2S.BANK_PUT, { slot: i, qty: 0 }); return;
    }
    if (shift) send(C2S.DROP, { slot: i, qty: 0 });
    else send(C2S.USE, { slot: i });
  }
  if (kind === 'equip') {
    const names = ['weapon', 'armor', 'charm'];
    send(C2S.UNEQUIP, { slot: names[i] });
  }
  if (kind === 'bank') send(C2S.BANK_GET, { slot: i, qty: 0 });
  if (kind === 'tradeYou') send(C2S.TRADE_SET, { back: i });
}

function renderInv() {
  const me = state.me;
  if (!me) return;
  const grid = $('invGrid');
  const eq = $('equipSlots');
  if (!grid) return;
  grid.innerHTML = '';
  const inv = me.inv || [];
  for (let i = 0; i < INV_SIZE; i++) grid.appendChild(slotEl(inv[i], i, 'inv'));
  if (eq) {
    eq.innerHTML = '';
    const e = me.equip || {};
    ['weapon', 'armor', 'charm'].forEach((s, i) => {
      eq.appendChild(slotEl(e[s] ? { id: e[s], qty: 1 } : null, i, 'equip'));
    });
  }
}

function renderBank() {
  const grid = $('bankGrid');
  if (!grid || !state.me) return;
  grid.innerHTML = '';
  const bank = state.me.bank || [];
  for (let i = 0; i < BANK_SIZE; i++) grid.appendChild(slotEl(bank[i], i, 'bank'));
}

function fillPois() {
  const ul = $('poiList');
  if (!ul) return;
  ul.innerHTML = '';
  for (const p of state.pois || []) {
    const li = document.createElement('li');
    li.textContent = p.name;
    li.onclick = () => send(C2S.MOVE, { x: p.x, y: p.y });
    ul.appendChild(li);
  }
}

function fillRecipes() {
  const box = $('recipeList');
  if (!box) return;
  box.innerHTML = '';
  const recs = recipes() || {};
  for (const rec of Object.values(recs)) {
    const b = document.createElement('button');
    b.textContent = rec.name;
    b.onclick = () => send(C2S.CRAFT, { id: rec.id });
    box.appendChild(b);
  }
}

function renderMinimap() {
  const c = $('minimap');
  if (!c || !state.tiles) return;
  const ctx = c.getContext('2d');
  const w = state.w, h = state.h;
  ctx.fillStyle = '#0a0810';
  ctx.fillRect(0, 0, c.width, c.height);
  const sx = c.width / w, sy = c.height / h;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const t = state.tiles[y * w + x];
      ctx.fillStyle = t === 7 || t === 8 ? '#163a52' : t === 20 ? '#333' : t === 12 || t === 21 ? '#ff4fd8' : '#1e3a24';
      ctx.fillRect(x * sx, y * sy, sx + 0.4, sy + 0.4);
    }
  }
  for (const p of listOf(state.players)) {
    ctx.fillStyle = p.id === state.you ? '#ffba08' : '#efe6d2';
    ctx.fillRect(p.x * sx - 1, p.y * sy - 1, 3, 3);
  }
}

function onTrade(p) {
  if (p.phase === 'ask') {
    show('tradeAsk', true);
    $('tradeAskText').textContent = (p.from || 'Someone') + ' wants to trade.';
    $('askYes').onclick = () => { send(C2S.TRADE_RESP, { yes: true }); show('tradeAsk', false); };
    $('askNo').onclick = () => { send(C2S.TRADE_RESP, { yes: false }); show('tradeAsk', false); };
    return;
  }
  if (p.phase === 'cancel') {
    show('trade', false); show('tradeAsk', false); return;
  }
  show('trade', true);
  show('panelInv', true);
  $('tradeName').textContent = p.partner || '—';
  $('lockYou').textContent = p.lockYou ? 'locked' : '';
  $('lockThem').textContent = p.lockThem ? 'locked' : '';
  const you = $('tradeYou'), them = $('tradeThem');
  you.innerHTML = ''; them.innerHTML = '';
  (p.you || []).forEach((s, i) => you.appendChild(slotEl(s, i, 'tradeYou')));
  (p.them || []).forEach((s, i) => them.appendChild(slotEl(s, i, 'tradeThem')));
  $('btnAccept').disabled = !(p.lockYou && p.lockThem);
}

$('btnLock').addEventListener('click', () => send(C2S.TRADE_LOCK, { lock: true }));
$('btnAccept').addEventListener('click', () => send(C2S.TRADE_ACCEPT, {}));
$('btnCancel').addEventListener('click', () => send(C2S.TRADE_CANCEL, {}));
$('tradeX').addEventListener('click', () => send(C2S.TRADE_CANCEL, {}));

function showCtx(x, y, hit) {
  const ctx = $('ctx');
  ctx.classList.remove('hidden');
  ctx.style.left = x + 'px';
  ctx.style.top = y + 'px';
  ctx.innerHTML = '';
  const b = document.createElement('button');
  b.textContent = 'Trade';
  b.onclick = () => { send(C2S.TRADE_REQ, { id: hit.id }); ctx.classList.add('hidden'); };
  ctx.appendChild(b);
}

function findEnt(id) {
  return state.entities.get(id) || state.players.get(id);
}
