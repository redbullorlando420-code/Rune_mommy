/** A* on the tile grid. Shared by client prediction and server authority. */

const DIRS = [
  [1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1],
  [1, 1, 1.414], [1, -1, 1.414], [-1, 1, 1.414], [-1, -1, 1.414],
];

function key(x, y) { return x + ',' + y; }

export function astar(walk, w, h, sx, sy, gx, gy) {
  sx = Math.max(0, Math.min(w - 1, sx | 0));
  sy = Math.max(0, Math.min(h - 1, sy | 0));
  gx = Math.max(0, Math.min(w - 1, gx | 0));
  gy = Math.max(0, Math.min(h - 1, gy | 0));
  if (!walk[sy * w + sx] || !walk[gy * w + gx]) return [];
  if (sx === gx && sy === gy) return [{ x: gx + 0.5, y: gy + 0.5 }];

  const open = [];
  const came = new Map();
  const gScore = new Map();
  const fScore = new Map();
  const start = key(sx, sy);
  gScore.set(start, 0);
  fScore.set(start, Math.hypot(gx - sx, gy - sy));
  open.push({ x: sx, y: sy, f: fScore.get(start) });

  const closed = new Set();
  let guard = w * h * 4;

  while (open.length && guard-- > 0) {
    let bi = 0;
    for (let i = 1; i < open.length; i++) if (open[i].f < open[bi].f) bi = i;
    const cur = open.splice(bi, 1)[0];
    const ck = key(cur.x, cur.y);
    if (closed.has(ck)) continue;
    closed.add(ck);
    if (cur.x === gx && cur.y === gy) {
      const path = [];
      let k = ck;
      while (k) {
        const [px, py] = k.split(',').map(Number);
        path.push({ x: px + 0.5, y: py + 0.5 });
        k = came.get(k);
      }
      path.reverse();
      return simplify(path, walk, w);
    }
    for (const [dx, dy, cost] of DIRS) {
      const nx = cur.x + dx;
      const ny = cur.y + dy;
      if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
      if (!walk[ny * w + nx]) continue;
      if (dx !== 0 && dy !== 0) {
        if (!walk[cur.y * w + nx] || !walk[ny * w + cur.x]) continue;
      }
      const nk = key(nx, ny);
      if (closed.has(nk)) continue;
      const g = (gScore.get(ck) ?? 1e9) + cost;
      if (g < (gScore.get(nk) ?? 1e9)) {
        came.set(nk, ck);
        gScore.set(nk, g);
        const f = g + Math.hypot(gx - nx, gy - ny);
        fScore.set(nk, f);
        open.push({ x: nx, y: ny, f });
      }
    }
  }
  return [];
}

function lineClear(walk, w, x0, y0, x1, y1) {
  const steps = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) * 2 + 1;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = Math.floor(x0 + (x1 - x0) * t);
    const y = Math.floor(y0 + (y1 - y0) * t);
    if (!walk[y * w + x]) return false;
  }
  return true;
}

function simplify(path, walk, w) {
  if (path.length < 3) return path;
  const out = [path[0]];
  let i = 0;
  while (i < path.length - 1) {
    let j = path.length - 1;
    for (; j > i + 1; j--) {
      if (lineClear(walk, w, path[i].x, path[i].y, path[j].x, path[j].y)) break;
    }
    out.push(path[j]);
    i = j;
  }
  return out;
}

export function nearestWalkable(walk, w, h, x, y) {
  let tx = Math.floor(x), ty = Math.floor(y);
  if (tx >= 0 && ty >= 0 && tx < w && ty < h && walk[ty * w + tx]) {
    return { x: tx, y: ty };
  }
  let best = null, bestD = 1e9;
  for (let r = 1; r < 8; r++) {
    for (let dy = -r; dy <= r; dy++) {
      for (let dx = -r; dx <= r; dx++) {
        const nx = tx + dx, ny = ty + dy;
        if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
        if (!walk[ny * w + nx]) continue;
        const d = dx * dx + dy * dy;
        if (d < bestD) { bestD = d; best = { x: nx, y: ny }; }
      }
    }
    if (best) return best;
  }
  return { x: tx, y: ty };
}
