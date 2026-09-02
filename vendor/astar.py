"""Grid A*. Original implementation of the classic public algorithm."""
from __future__ import annotations

import heapq
from typing import Iterable, Sequence

DIRS8 = (
    (1, 0, 1.0),
    (-1, 0, 1.0),
    (0, 1, 1.0),
    (0, -1, 1.0),
    (1, 1, 1.41421356237),
    (1, -1, 1.41421356237),
    (-1, 1, 1.41421356237),
    (-1, -1, 1.41421356237),
)


def astar(start, goal, blocked=None, bounds=None):
    """Shortest 8-connected path from start to goal.

    start, goal: (x, y) cells (ints or numeric; floored).
    blocked: set of (x, y) cells that cannot be entered.
    bounds: optional (minx, miny, maxx, maxy) inclusive clamp. If omitted a
            pad around start/goal is used so an open grid still terminates.
    Returns a list of (x, y) including start and goal, or [] if none.
    """
    blocked = set(blocked) if blocked else set()
    sx, sy = int(start[0]), int(start[1])
    gx, gy = int(goal[0]), int(goal[1])
    start = (sx, sy)
    goal = (gx, gy)
    if start == goal:
        return [start] if start not in blocked else []
    if start in blocked or goal in blocked:
        return []

    if bounds is None:
        pad = 64
        minx = min(sx, gx) - pad
        maxx = max(sx, gx) + pad
        miny = min(sy, gy) - pad
        maxy = max(sy, gy) + pad
    else:
        minx, miny, maxx, maxy = bounds

    def heuristic(ax, ay):
        dx, dy = abs(ax - gx), abs(ay - gy)
        return (dx + dy) + (0.41421356237 * min(dx, dy))

    open_heap = [(heuristic(sx, sy), 0.0, start)]
    came = {}
    gscore = {start: 0.0}
    closed = set()

    while open_heap:
        _f, g, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        if cur == goal:
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            path.reverse()
            return path
        closed.add(cur)
        cx, cy = cur
        for dx, dy, cost in DIRS8:
            nx, ny = cx + dx, cy + dy
            nxt = (nx, ny)
            if nxt in blocked or nxt in closed:
                continue
            if nx < minx or nx > maxx or ny < miny or ny > maxy:
                continue
            if dx and dy:
                if (cx + dx, cy) in blocked or (cx, cy + dy) in blocked:
                    continue
            ng = g + cost
            if ng < gscore.get(nxt, 1e18):
                gscore[nxt] = ng
                came[nxt] = cur
                heapq.heappush(open_heap, (ng + heuristic(nx, ny), ng, nxt))
    return []
