import { C2S } from '/shared/protocol.js';
import { send } from '../net/client.js';
import { item } from '/shared/catalog.js';
import { toast } from './hud.js';

function paintOffer(host, slots) {
  host.innerHTML = '';
  const list = slots || [];
  for (let i = 0; i < 8; i++) {
    const d = document.createElement('div');
    d.className = 'slot' + (list[i] ? '' : ' empty');
    if (list[i]) {
      const def = item(list[i].id);
      d.textContent = (def?.name || list[i].id).slice(0, 2).toUpperCase();
      const q = document.createElement('span');
      q.className = 'qty';
      q.textContent = list[i].qty > 1 ? String(list[i].qty) : '';
      d.appendChild(q);
      d.title = `${def?.name || list[i].id} ×${list[i].qty}`;
    }
    host.appendChild(d);
  }
}

export function bindTrade(state) {
  document.getElementById('trade-lock').addEventListener('click', () => send(C2S.TRADE_LOCK, {}));
  document.getElementById('trade-accept').addEventListener('click', () => send(C2S.TRADE_ACCEPT, {}));
  document.getElementById('trade-cancel').addEventListener('click', () => send(C2S.TRADE_CANCEL, {}));
}

export function onTrade(state, p) {
  const modal = document.getElementById('trade');
  if (p.phase === 'req') {
    const ok = confirm(`${p.name} wants to trade. Accept?`);
    send(C2S.TRADE_RESP, { tradeId: p.tradeId, ok });
    if (!ok) return;
    modal.classList.remove('hidden');
    return;
  }
  if (p.phase === 'close' || p.phase === 'done') {
    modal.classList.add('hidden');
    state.tradeOffer = [];
    if (p.phase === 'close' && p.reason) toast('Trade ' + p.reason, 'info');
    return;
  }
  if (p.phase === 'open') {
    modal.classList.remove('hidden');
    document.getElementById('trade-peer').textContent = p.peer?.name || 'wanderer';
    paintOffer(document.getElementById('trade-theirs'), p.offerPeer);
    paintOffer(document.getElementById('trade-mine'), p.offerSelf);
    state.tradeOffer = p.offerSelf || [];
    const flags = [];
    if (p.lockPeer) flags.push('they locked');
    if (p.lockSelf) flags.push('you locked');
    if (p.acceptPeer) flags.push('they accept');
    if (p.acceptSelf) flags.push('you accept');
    document.getElementById('trade-peer-flags').textContent = flags.join(' · ');
    document.getElementById('trade-lock').textContent = p.lockSelf ? 'Unlock' : 'Lock';
  }
}
