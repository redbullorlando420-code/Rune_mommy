"""A* on the tile grid. Port of shared/pathfinding.js."""
from __future__ import annotations

import math

DIRS = [
    (1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1),
    (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414),
]


def _key(x, y):
    return f"{x},{y}"


def astar(walk, w, h, sx, sy, gx, gy):
    sx = max(0, min(w - 1, int(sx)))
    sy = max(0, min(h - 1, int(sy)))
    gx = max(0, min(w - 1, int(gx)))
    gy = max(0, min(h - 1, int(gy)))
    if not walk[sy * w + sx] or not walk[gy * w + gx]:
        return []
    if sx == gx and sy == gy:
        return [{"x": gx + 0.5, "y": gy + 0.5}]

    open_ = []
    came = {}
    g_score = {}
    start = _key(sx, sy)
    g_score[start] = 0
    f0 = math.hypot(gx - sx, gy - sy)
    open_.append({"x": sx, "y": sy, "f": f0})

    closed = set()
    guard = w * h * 4

    while open_ and guard > 0:
        guard -= 1
        bi = 0
        for i in range(1, len(open_)):
            if open_[i]["f"] < open_[bi]["f"]:
                bi = i
        cur = open_.pop(bi)
        ck = _key(cur["x"], cur["y"])
        if ck in closed:
            continue
        closed.add(ck)
        if cur["x"] == gx and cur["y"] == gy:
            path = []
            k = ck
            while k:
                px, py = map(int, k.split(","))
                path.append({"x": px + 0.5, "y": py + 0.5})
                k = came.get(k)
            path.reverse()
            return simplify(path, walk, w)
        for dx, dy, cost in DIRS:
            nx = cur["x"] + dx
            ny = cur["y"] + dy
            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                continue
            if not walk[ny * w + nx]:
                continue
            if dx != 0 and dy != 0:
                if not walk[cur["y"] * w + nx] or not walk[ny * w + cur["x"]]:
                    continue
            nk = _key(nx, ny)
            if nk in closed:
                continue
            g = g_score.get(ck, 1e9) + cost
            if g < g_score.get(nk, 1e9):
                came[nk] = ck
                g_score[nk] = g
                f = g + math.hypot(gx - nx, gy - ny)
                open_.append({"x": nx, "y": ny, "f": f})
    return []


def line_clear(walk, w, x0, y0, x1, y1):
    steps = max(abs(x1 - x0), abs(y1 - y0)) * 2 + 1
    for i in range(int(steps) + 1):
        t = i / steps if steps else 0
        x = math.floor(x0 + (x1 - x0) * t)
        y = math.floor(y0 + (y1 - y0) * t)
        if not walk[y * w + x]:
            return False
    return True


def simplify(path, walk, w):
    if len(path) < 3:
        return path
    out = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1:
            if line_clear(walk, w, path[i]["x"], path[i]["y"], path[j]["x"], path[j]["y"]):
                break
            j -= 1
        out.append(path[j])
        i = j
    return out


def nearest_walkable(walk, w, h, x, y):
    tx = math.floor(x)
    ty = math.floor(y)
    if tx >= 0 and ty >= 0 and tx < w and ty < h and walk[ty * w + tx]:
        return {"x": tx, "y": ty}
    best = None
    best_d = 1e9
    for r in range(1, 8):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                nx = tx + dx
                ny = ty + dy
                if nx < 0 or ny < 0 or nx >= w or ny >= h:
                    continue
                if not walk[ny * w + nx]:
                    continue
                d = dx * dx + dy * dy
                if d < best_d:
                    best_d = d
                    best = {"x": nx, "y": ny}
        if best:
            return best
    return {"x": tx, "y": ty}
