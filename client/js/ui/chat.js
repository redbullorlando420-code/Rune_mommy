import { C2S } from '/shared/protocol.js';
import { send } from '../net/client.js';

export function bindChat() {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const log = document.getElementById('chat');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    send(C2S.CHAT, { text });
    input.value = '';
    input.blur();
  });
  return log;
}

export function pushChat(p) {
  const log = document.getElementById('chat');
  const row = document.createElement('div');
  const ch = p.channel || 'global';
  row.className = 'row ' + ch;
  if (ch === 'system') {
    row.innerHTML = `<span class="system">${esc(p.text)}</span>`;
  } else {
    row.innerHTML = `<span class="from">${esc(p.from)}</span>: ${esc(p.text)}`;
  }
  log.appendChild(row);
  log.scrollTop = log.scrollHeight;
  while (log.children.length > 80) log.removeChild(log.firstChild);
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}
