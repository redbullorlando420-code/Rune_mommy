/** Lightweight pixel VN overlay. Load trees from /data/dialogue/. Esc closes. */
const TALK_FILE = {
  lila: 'lila', yara: 'yara', maera: 'yara', rosa: 'rosa',
  mira: 'mira', shake_bar: 'mira',
};

const trees = new Map();
let open = false;
let tree = null;
let nodeId = null;
let payload = null;
let portraitDrawn = '';

const PAL = {
  lila: {
    skin: '#c68642', skin2: '#a86832', hair: '#1a0a06', hair2: '#3a1a10',
    cloth: '#f3e6d4', cloth2: '#d9c4a8', accent: '#c1121f', ink: '#2a1010',
    sandal: '#6b3a18', nail: '#c45c78', bg: '#2a1620',
  },
  mira: {
    skin: '#8d5524', skin2: '#6f3f18', hair: '#1c0c06', hair2: '#3d1c0c',
    cloth: '#ff4fd8', cloth2: '#c430a8', accent: '#5af0ff', ink: '#1a081c',
    sandal: '#f4e8d0', nail: '#ff4fd8', bg: '#1a081c',
  },
  rosa: {
    skin: '#b5683a', skin2: '#934e28', hair: '#2a1008', hair2: '#4a2010',
    cloth: '#f4a5c0', cloth2: '#e07a9a', accent: '#ff8fab', ink: '#2a1018',
    sandal: '#fff4e6', nail: '#e91e8c', bg: '#241018',
  },
  yara: {
    skin: '#a86b45', skin2: '#8a5234', hair: '#140806', hair2: '#2c140c',
    cloth: '#4a2018', cloth2: '#2a1410', accent: '#d4a017', ink: '#1a0c08',
    sandal: '#2a1c14', nail: '#c77dff', bg: '#161018',
  },
};

function $(id) { return document.getElementById(id); }

function ensureDom() {
  if ($('vnOverlay')) return;
  const wrap = document.createElement('div');
  wrap.id = 'vnOverlay';
  wrap.className = 'hidden';
  wrap.setAttribute('aria-hidden', 'true');
  wrap.innerHTML = `
    <div id="vnStage">
      <canvas id="vnPortrait" width="192" height="240" aria-hidden="true"></canvas>
      <div id="vnBox">
        <div id="vnName"></div>
        <p id="vnText"></p>
        <div id="vnChoices"></div>
        <div id="vnTools"></div>
      </div>
      <button id="vnClose" type="button" title="Close (Esc)">×</button>
    </div>`;
  (document.getElementById('game') || document.body).appendChild(wrap);
  $('vnClose').addEventListener('click', closeVN);
  wrap.addEventListener('click', (e) => { if (e.target === wrap) closeVN(); });
}

export async function loadTree(id) {
  const file = TALK_FILE[id] || id;
  if (trees.has(file)) return trees.get(file);
  const r = await fetch('/data/dialogue/' + file + '.json');
  if (!r.ok) throw new Error('no dialogue ' + file);
  const data = await r.json();
  trees.set(file, data);
  return data;
}

function fileFor(p) {
  return p.dialogue || TALK_FILE[p.id] || TALK_FILE[p.name?.toLowerCase()] || null;
}

export function isVNOpen() { return open; }

export function closeVN() {
  if (!open) return;
  open = false;
  tree = null;
  nodeId = null;
  const el = $('vnOverlay');
  if (el) {
    el.classList.add('hidden');
    el.setAttribute('aria-hidden', 'true');
  }
}

function showShop() {
  $('panelShop')?.classList.remove('hidden');
  $('panelInv')?.classList.remove('hidden');
}
function showBank() {
  $('panelBank')?.classList.remove('hidden');
}

function go(next, action) {
  if (action === 'shop') showShop();
  if (action === 'bank') showBank();
  if (action === 'close' || next === null || next === 'close' || next === undefined) {
    if (action === 'shop' || action === 'bank') return;
    closeVN();
    return;
  }
  renderNode(next);
}

function renderNode(id) {
  const nodes = tree.nodes || tree;
  const node = nodes[id] || nodes[tree.start] || nodes.start;
  if (!node) { closeVN(); return; }
  nodeId = node.id || id;
  const name = node.speaker || tree.speaker || payload?.name || '';
  const title = payload?.title ? ' — ' + payload.title : '';
  $('vnName').textContent = name + title;
  $('vnText').textContent = node.text || payload?.greet || '';
  const box = $('vnChoices');
  box.innerHTML = '';
  const choices = (node.choices && node.choices.length) ? node.choices.slice(0, 4) : [{ label: '…', next: null }];
  choices.forEach((c, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'vn-choice' + (c.action === 'shop' ? ' gold' : '');
    b.textContent = (i + 1) + '.  ' + (c.label || '…');
    b.addEventListener('click', () => go(c.next, c.action));
    box.appendChild(b);
  });
  const tools = $('vnTools');
  if (tools) {
    tools.innerHTML = '';
    if (payload?.shop) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'gold';
      b.textContent = 'Shop';
      b.addEventListener('click', showShop);
      tools.appendChild(b);
    }
    if (payload?.bank) {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = 'Vault';
      b.addEventListener('click', showBank);
      tools.appendChild(b);
    }
  }
  paintPortrait(node.portrait || tree.portrait || payload?.portrait, node.expression || 'smile');
}

function paintPortrait(who, expr) {
  const canvas = $('vnPortrait');
  if (!canvas) return;
  const key = who + ':' + expr;
  if (portraitDrawn === key) return;
  portraitDrawn = key;
  const pal = PAL[who] || PAL.lila;
  const src = document.createElement('canvas');
  src.width = 64; src.height = 80;
  const c = src.getContext('2d');
  c.imageSmoothingEnabled = false;
  drawFigure(c, pal, expr || 'smile', who);
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(src, 0, 0, canvas.width, canvas.height);
}

function R(c, x, y, w, h, col) { c.fillStyle = col; c.fillRect(x | 0, y | 0, w, h); }

function drawFigure(c, p, expr, who) {
  const lean = expr === 'lean' ? 2 : 0;
  const heat = expr === 'heat' || expr === 'blush' || expr === 'tease';
  R(c, 0, 0, 64, 80, p.bg);
  R(c, 4, 62, 56, 18, '#1a1210');
  R(c, 6, 64, 52, 2, p.accent);

  const hx = 22 + lean, hy = 8;
  R(c, hx + 4, hy + 22, 12, 6, p.skin2);
  R(c, hx + 2, hy + 26, 16, 18, p.cloth);
  R(c, hx + 3, hy + 28, 14, 4, p.cloth2);
  if (who === 'lila') {
    R(c, hx + 8, hy + 30, 6, 6, p.accent);
    R(c, hx + 10, hy + 28, 2, 10, p.accent);
  }
  if (who === 'mira') {
    R(c, hx + 2, hy + 26, 16, 3, p.accent);
    R(c, hx + 1, hy + 40, 18, 3, p.accent);
  }
  if (who === 'yara') {
    R(c, hx + 2, hy + 32, 16, 2, p.accent);
    R(c, hx + 16, hy + 28, 3, 4, p.accent);
  }

  R(c, hx - 2, hy + 28, 5, 14, p.skin);
  R(c, hx + 17, hy + 28, 5, 14, p.skin);
  R(c, hx - 1, hy + 40, 4, 4, p.skin2);
  R(c, hx + 17, hy + 40, 4, 4, p.skin2);

  R(c, hx + 3, hy + 42, 7, 12, p.cloth2);
  R(c, hx + 10, hy + 42, 7, 12, p.cloth2);
  R(c, hx + 4, hy + 52, 6, 10, p.skin);
  R(c, hx + 11, hy + 52, 6, 10, p.skin);

  const bare = expr === 'rest' || expr === 'heat' || expr === 'tease' || expr === 'care' || who === 'rosa' || who === 'lila';
  if (bare) {
    R(c, hx + 3, hy + 62, 8, 4, p.skin);
    R(c, hx + 12, hy + 62, 8, 4, p.skin);
    R(c, hx + 2, hy + 64, 3, 2, p.skin2);
    R(c, hx + 6, hy + 65, 2, 2, p.skin);
    R(c, hx + 9, hy + 65, 2, 2, p.skin);
    R(c, hx + 12, hy + 64, 3, 2, p.skin2);
    R(c, hx + 16, hy + 65, 2, 2, p.skin);
    R(c, hx + 19, hy + 65, 2, 2, p.skin);
    R(c, hx + 3, hy + 63, 2, 1, p.nail);
    R(c, hx + 7, hy + 64, 2, 1, p.nail);
    R(c, hx + 10, hy + 64, 1, 1, p.nail);
    R(c, hx + 13, hy + 63, 2, 1, p.nail);
    R(c, hx + 17, hy + 64, 2, 1, p.nail);
    R(c, hx + 20, hy + 64, 1, 1, p.nail);
    if (who === 'mira' || who === 'rosa') {
      R(c, hx + 1, hy + 62, 10, 2, p.sandal);
      R(c, hx + 12, hy + 62, 10, 2, p.sandal);
    }
  } else {
    R(c, hx + 3, hy + 61, 8, 5, p.sandal);
    R(c, hx + 12, hy + 61, 8, 5, p.sandal);
    R(c, hx + 3, hy + 64, 2, 1, p.nail);
    R(c, hx + 13, hy + 64, 2, 1, p.nail);
  }

  R(c, hx + 4, hy + 6, 14, 16, p.skin);
  R(c, hx + 3, hy + 8, 16, 12, p.skin);
  R(c, hx + 2, hy + 2, 18, 10, p.hair);
  R(c, hx + 1, hy + 6, 4, 16, p.hair);
  R(c, hx + 17, hy + 6, 5, 18, p.hair2);
  if (who === 'mira') {
    R(c, hx + 6, hy + 0, 10, 6, p.hair);
    R(c, hx + 4, hy + 12, 2, 2, p.accent);
    R(c, hx + 16, hy + 12, 2, 2, p.accent);
  }
  if (who === 'lila') {
    R(c, hx + 14, hy + 4, 4, 4, p.accent);
  }
  if (who === 'rosa') {
    R(c, hx + 0, hy + 10, 3, 14, p.hair2);
    R(c, hx + 19, hy + 10, 4, 16, p.hair2);
  }

  const eyeY = hy + 12;
  if (expr === 'wink') {
    R(c, hx + 7, eyeY, 3, 2, p.ink);
    R(c, hx + 8, eyeY + 1, 2, 1, p.ink);
    R(c, hx + 13, eyeY, 3, 3, '#f4e8d0');
    R(c, hx + 14, eyeY + 1, 1, 1, p.ink);
  } else if (expr === 'rest') {
    R(c, hx + 7, eyeY + 1, 3, 1, p.ink);
    R(c, hx + 13, eyeY + 1, 3, 1, p.ink);
  } else {
    R(c, hx + 7, eyeY, 3, 3, '#f4e8d0');
    R(c, hx + 13, eyeY, 3, 3, '#f4e8d0');
    R(c, hx + 8, eyeY + 1, 1, 1, p.ink);
    R(c, hx + 14, eyeY + 1, 1, 1, expr === 'look' ? p.ink : p.ink);
    if (expr === 'look') R(c, hx + 15, eyeY + 1, 1, 1, p.ink);
  }
  if (heat) {
    R(c, hx + 5, hy + 16, 3, 2, '#e07a7a');
    R(c, hx + 14, hy + 16, 3, 2, '#e07a7a');
  }
  if (expr === 'smirk' || expr === 'tease') {
    R(c, hx + 9, hy + 18, 5, 1, p.ink);
    R(c, hx + 13, hy + 17, 1, 1, p.ink);
  } else if (expr === 'smile' || expr === 'wink' || expr === 'care') {
    R(c, hx + 9, hy + 18, 4, 1, p.ink);
  } else {
    R(c, hx + 10, hy + 18, 2, 1, p.ink);
  }

  R(c, 8, 4, 48, 1, p.accent);
  R(c, 8, 76, 48, 1, p.accent);
}

export async function openVN(p) {
  ensureDom();
  const file = fileFor(p);
  if (!file) return false;
  try {
    tree = await loadTree(file);
  } catch {
    return false;
  }
  payload = p;
  open = true;
  portraitDrawn = '';
  const el = $('vnOverlay');
  el.classList.remove('hidden');
  el.setAttribute('aria-hidden', 'false');
  renderNode(p.node || p.start || tree.start || 'start');
  return true;
}

document.addEventListener('keydown', (e) => {
  if (!open) return;
  if (e.key === 'Escape') {
    e.preventDefault();
    e.stopPropagation();
    closeVN();
    return;
  }
  const n = e.key === '1' ? 0 : e.key === '2' ? 1 : e.key === '3' ? 2 : e.key === '4' ? 3 : -1;
  if (n >= 0) {
    const btns = document.querySelectorAll('#vnChoices .vn-choice');
    if (btns[n]) { e.preventDefault(); btns[n].click(); }
  }
}, true);

ensureDom();
window.RuneVN = { open: openVN, close: closeVN, isOpen: isVNOpen, load: loadTree };
