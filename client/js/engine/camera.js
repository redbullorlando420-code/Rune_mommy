import { lerp, TILE, MAP_W, MAP_H } from '/shared/constants.js';

export const camera = {
  x: 18.5,
  y: 10.5,
  zoom: 1,
};

export function follow(target, dt) {
  if (!target) return;
  const k = 1 - Math.exp(-(dt / 1000) * 7.5);
  camera.x = lerp(camera.x, target.x, k);
  camera.y = lerp(camera.y, target.y, k);
}

export function snap(target) {
  if (!target) return;
  camera.x = target.x;
  camera.y = target.y;
}

export function worldToScreen(wx, wy, viewW, viewH) {
  return {
    x: (wx - camera.x) * TILE * camera.zoom + viewW / 2,
    y: (wy - camera.y) * TILE * camera.zoom + viewH / 2,
  };
}

export function screenToWorld(sx, sy, viewW, viewH) {
  return {
    x: (sx - viewW / 2) / (TILE * camera.zoom) + camera.x,
    y: (sy - viewH / 2) / (TILE * camera.zoom) + camera.y,
  };
}

export function clampCam() {
  camera.x = Math.max(2, Math.min(MAP_W - 2, camera.x));
  camera.y = Math.max(2, Math.min(MAP_H - 2, camera.y));
}
