import { C2S } from '/shared/protocol.js';
import { send } from '../net/client.js';
import { item, recipes, skillLevel } from '/shared/catalog.js';
import { INV_SIZE, BANK_SIZE, EQUIP_SLOTS } from '/shared/constants.js';

let stateRef = null;
let shopTab = 'stall';

const KIND_COL = {
  weapon: '#e0a045', armor: '#6b8f5a', charm: '#c77dff',
  resource: '#90be6d', consumable: '#f0e6d4', currency: '#f4d35e', quest: '#9b8ec4',
  junk: '#9a8b78', tool: '#c4b49a', key: '#e8d48a', bag: '#a67c6d',
};

function glyph(id) {
  const def = item(id);
  if (!def) return '?';
  return (def.name || id).slice(0, 2).toUpperCase();
}

function paintSlot(el, stack, extra = '') {
  el.className = 'slot ' + extra + (stack ? '' : ' empty');
  el.innerHTML = '';
  el.title = '';
  if (!stack) { el.textContent = ''; return; }
  const def = item(stack.id);
  el.style.color = KIND_COL[def?.kind] || '#d8cbb8';
  el.textContent = glyph(stack.id);
  const q = document.createElement('span');
  q.className = 'qty';
  q.textContent = stack.qty > 1 ? String(stack.qty) : '';
  el.appendChild(q);
  el.title = `${def?.name || stack.id}${stack.qty > 1 ? ' ×' + stack.qty : ''}\n${def?.desc || ''}`;
}

export function bindInventory(state) {
  stateRef = state;
  const inv = document.getElementById('inv');
  const eq = document.getElementById('equip');
  inv.innerHTML = '';
  eq.innerHTML = '';
  for (const slot of EQUIP_SLOTS) {
    const d = document.createElement('div');
    d.className = 'slot empty ' + slot;
    d.dataset.eq = slot;
    d.title = slot;
    d.addEventListener('click', () => send(C2S.UNEQUIP, { slot }));
    eq.appendChild(d);
  }
  for (let i = 0; i < INV_SIZE; i++) {
    const d = document.createElement('div');
    d.className = 'slot empty';
    d.dataset.slot = String(i);
    d.addEventListener('click', () => onInvClick(i, false));
    d.addEventListener('contextmenu', (e) => { e.preventDefault(); onInvClick(i, true); });
    inv.appendChild(d);
  }

  const vault = document.getElementById('shop-vault');
  vault.innerHTML = '';
  for (let i = 0; i < BANK_SIZE; i++) {
    const d = document.createElement('div');
    d.className = 'slot empty';
    d.dataset.bank = String(i);
    d.addEventListener('click', () => send(C2S.BANK_GET, { slot: i }));
    vault.appendChild(d);
  }

  document.querySelectorAll('#shop .tab').forEach((t) => {
    t.addEventListener('click', () => {
      shopTab = t.dataset.tab;
      document.querySelectorAll('#shop .tab').forEach((x) => x.classList.toggle('on', x === t));
      document.getElementById('shop-stall').classList.toggle('hidden', shopTab !== 'stall');
      document.getElementById('shop-vault').classList.toggle('hidden', shopTab !== 'vault');
    });
  });
}

function shopOpen() { return !document.getElementById('shop').classList.contains('hidden'); }
function tradeOpen() { return !document.getElementById('trade').classList.contains('hidden'); }

function onInvClick(slot, drop) {
  const you = stateRef?.you;
  if (!you) return;
  const s = (you.inv || [])[slot];
  if (drop) {
    if (s) send(C2S.DROP, { slot, qty: s.qty });
    return;
  }
  if (tradeOpen() && s) {
    const offer = (stateRef.tradeOffer || []).slice();
    const i = offer.findIndex((o) => o.id === s.id);
    if (i >= 0) offer[i] = { id: s.id, qty: offer[i].qty + 1 };
    else offer.push({ id: s.id, qty: 1 });
    stateRef.tradeOffer = offer;
    send(C2S.TRADE_SET, { slots: offer });
    return;
  }
  if (shopOpen() && s) {
    if (shopTab === 'vault') send(C2S.BANK_PUT, { slot });
    else send(C2S.SHOP_SELL, { slot, qty: 1 });
    return;
  }
  if (s) send(C2S.USE, { slot });
}

export function renderInv(state) {
  const you = state.you;
  if (!you) return;
  const inv = you.inv || [];
  document.querySelectorAll('#inv .slot').forEach((el, i) => paintSlot(el, inv[i]));
  for (const slot of EQUIP_SLOTS) {
    const el = document.querySelector(`#equip .slot[data-eq="${slot}"]`);
    const id = you.equip?.[slot];
    paintSlot(el, id ? { id, qty: 1 } : null, slot);
  }
  const bank = you.bank || [];
  document.querySelectorAll('#shop-vault .slot').forEach((el, i) => paintSlot(el, bank[i]));
}

export function showShop(p) {
  document.getElementById('shop').classList.remove('hidden');
  document.getElementById('shop-title').textContent = (p.vendor || 'Voss') + "'s Stall";
  const list = document.getElementById('shop-stall');
  list.innerHTML = '';
  for (const row of p.items || []) {
    const div = document.createElement('div');
    div.className = 'shop-row';
    div.innerHTML = `<span>${esc(row.name)}</span><span>${row.stock} left</span><span>${row.buy}c</span>`;
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = 'Buy';
    b.addEventListener('click', () => send(C2S.SHOP_BUY, { id: row.id, qty: 1 }));
    div.appendChild(b);
    list.appendChild(div);
  }
}

export function showNpc(p) {
  const box = document.getElementById('npc-box');
  document.getElementById('npc-name').textContent = p.title ? `${p.name} — ${p.title}` : p.name;
  document.getElementById('npc-lines').innerHTML = (p.lines || []).map((l) => `<p>${esc(l)}</p>`).join('');
  box.classList.remove('hidden');
}

export function bindCraft(state) {
  const list = document.getElementById('craft-list');
  const recs = recipes() || {};
  list.innerHTML = '';
  for (const rec of Object.values(recs)) {
    const div = document.createElement('div');
    div.className = 'shop-row';
    const need = rec.inputs.map((i) => `${i.qty} ${item(i.id)?.name || i.id}`).join(', ');
    div.innerHTML = `<span>${esc(rec.name)}</span><span>Lv ${rec.level}</span><span>${esc(need)}</span>`;
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = 'Bind';
    b.addEventListener('click', () => send(C2S.CRAFT, { id: rec.id }));
    div.appendChild(b);
    list.appendChild(div);
  }
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

export { skillLevel };
