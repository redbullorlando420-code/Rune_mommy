import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { T } from "/shared/tiles.js";

const PAL = {
  [T.VOID]: 0x07050c, [T.GRASS]: 0x1e3a24, [T.GRASS_D]: 0x16301c, [T.TALL]: 0x245230,
  [T.PATH]: 0x6b5344, [T.STONE]: 0x4a4e56, [T.DIRT]: 0x5c4030, [T.WATER]: 0x163a52,
  [T.WATER_D]: 0x0c2438, [T.SAND]: 0x7a6a4e, [T.WOOD]: 0x3d2918, [T.RUG]: 0x6b2d3c,
  [T.FLAG]: 0x6a5c4a, [T.ASH]: 0x3a3530, [T.MOSS]: 0x2d4a32, [T.FLOWER]: 0x3a3a28,
  [T.HEARTH]: 0x8a3a12, [T.DOCK]: 0x4a3828, [T.SHRINE]: 0x4a3a62, [T.LEAVES]: 0x2a4028,
  [T.ROAD]: 0x2a2a30, [T.NEON]: 0x1a3040,
};
const dummy = new THREE.Object3D();
const _follow = new THREE.Vector3();
const _desired = new THREE.Vector3();
const _mouse = new THREE.Vector2();
const _raycaster = new THREE.Raycaster();
let renderer, scene, camera, controls, canvas;
let terrainGroup = null, groundPlane = null, terrainKey = "";
let pointerDown = { x: 0, y: 0 };
const playerMap = new Map();
const entityMap = new Map();

function disposeObject(obj) {
  obj.traverse((o) => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) {
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) { if (m.map) m.map.dispose(); m.dispose(); }
    }
  });
}
function makeNameSprite(text, color = "#efe6d2") {
  const c = document.createElement("canvas");
  c.width = 256; c.height = 64;
  const g = c.getContext("2d");
  g.clearRect(0, 0, 256, 64);
  g.font = "600 28px sans-serif"; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillStyle = "rgba(0,0,0,0.45)"; g.fillRect(16, 12, 224, 40);
  g.fillStyle = color; g.fillText(String(text || "").slice(0, 18), 128, 34);
  const tex = new THREE.CanvasTexture(c); tex.needsUpdate = true;
  const spr = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
  spr.scale.set(2.4, 0.6, 1); spr.position.y = 1.85;
  spr.userData.canvas = c; spr.userData.label = text;
  return spr;
}
function updateNameSprite(spr, text, color) {
  if (spr.userData.label === text) return;
  spr.userData.label = text;
  const c = spr.userData.canvas; const g = c.getContext("2d");
  g.clearRect(0, 0, 256, 64);
  g.font = "600 28px sans-serif"; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillStyle = "rgba(0,0,0,0.45)"; g.fillRect(16, 12, 224, 40);
  g.fillStyle = color; g.fillText(String(text || "").slice(0, 18), 128, 34);
  spr.material.map.needsUpdate = true;
}
function makeTree(tr) {
  const g = new THREE.Group();
  const trunkH = tr.variant === 3 ? 1.1 : 1.35;
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, trunkH, 6), new THREE.MeshStandardMaterial({ color: tr.variant === 3 ? 0x3a2a18 : 0x2a1810, roughness: 0.9 }));
  trunk.position.y = trunkH / 2;
  const hue = (tr.hue || 110) / 360;
  const foliage = new THREE.Mesh(new THREE.ConeGeometry(tr.variant === 3 ? 0.7 : 0.85, tr.variant === 3 ? 1.4 : 1.8, 7), new THREE.MeshStandardMaterial({ color: new THREE.Color().setHSL(hue, 0.4, 0.28), roughness: 0.85 }));
  foliage.position.y = trunkH + 0.55;
  g.add(trunk, foliage);
  g.position.set((tr.x || 0) + 0.5, 0, (tr.y || 0) + 0.5);
  return g;
}
function makeRock(r) {
  const s = 0.28 + (r.variant || 0) * 0.12;
  const mesh = new THREE.Mesh(new THREE.IcosahedronGeometry(s, 0), new THREE.MeshStandardMaterial({ color: 0x5a5854, roughness: 0.95, flatShading: true }));
  mesh.position.set((r.x || 0) + 0.5, s * 0.45, (r.y || 0) + 0.5);
  return mesh;
}
function makePlayer(p, isMe) {
  const g = new THREE.Group();
  const hue = p.hue || 20;
  const bodyCol = isMe ? 0xc47a12 : new THREE.Color().setHSL(hue / 360, 0.55, 0.48);
  const headCol = isMe ? 0xf0d48a : new THREE.Color().setHSL(hue / 360, 0.4, 0.7);
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, 0.55, 4, 8), new THREE.MeshStandardMaterial({ color: bodyCol, roughness: 0.55, emissive: isMe ? 0xe85d04 : 0x000000, emissiveIntensity: isMe ? 0.35 : 0 }));
  body.position.y = 0.72;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.18, 10, 8), new THREE.MeshStandardMaterial({ color: headCol, roughness: 0.5 }));
  head.position.y = 1.28;
  if (isMe) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.035, 8, 20), new THREE.MeshStandardMaterial({ color: 0xffba08, emissive: 0xe85d04, emissiveIntensity: 0.8 }));
    ring.rotation.x = Math.PI / 2; ring.position.y = 0.04; g.add(ring);
  }
  const name = makeNameSprite(p.name || "wanderer", isMe ? "#f0d48a" : "#efe6d2");
  g.add(body, head, name);
  g.userData.body = body; g.userData.nameSpr = name; g.userData.isMe = isMe; g.userData.kind = "player";
  return g;
}
function entityColor(e) {
  if (e.kind === "mob") {
    if (e.type === "ash_imp") return 0xe85d04;
    if (e.type === "hollow_stag") return 0xb8f2e6;
    return 0x8a3030;
  }
  if (e.kind === "npc") {
    if (e.type === "voss") return 0xf4a261;
    if (e.type === "nima") return 0x4cc9f0;
    return 0xc77dff;
  }
  if (e.kind === "node") {
    if (e.depleted) return 0x3a3530;
    if (e.type && String(e.type).includes("tree")) return 0xe85d04;
    if (e.type && String(e.type).includes("moon")) return 0xc77dff;
    return 0x8a8a9a;
  }
  if (e.kind === "ground") return 0xffba08;
  return 0x9b8a70;
}
function makeEntity(e) {
  const g = new THREE.Group();
  const col = entityColor(e);
  let mesh;
  if (e.kind === "mob") {
    const rad = e.type === "hollow_stag" ? 0.42 : e.type === "ash_imp" ? 0.22 : 0.32;
    mesh = new THREE.Mesh(new THREE.SphereGeometry(rad, 10, 8), new THREE.MeshStandardMaterial({ color: col, roughness: 0.6, emissive: 0x4a0808, emissiveIntensity: 0.25 }));
    mesh.position.y = rad;
  } else if (e.kind === "npc") {
    mesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.2, 0.5, 4, 8), new THREE.MeshStandardMaterial({ color: col, roughness: 0.5 }));
    mesh.position.y = 0.65;
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 6), new THREE.MeshStandardMaterial({ color: 0xefe6d2 }));
    head.position.y = 1.15; g.add(head);
  } else if (e.kind === "node") {
    if (e.type && String(e.type).includes("tree")) {
      mesh = new THREE.Mesh(new THREE.ConeGeometry(0.4, 1.1, 6), new THREE.MeshStandardMaterial({ color: col, roughness: 0.7 }));
      mesh.position.y = 0.55;
    } else if (e.type && String(e.type).includes("moon")) {
      mesh = new THREE.Mesh(new THREE.SphereGeometry(0.28, 10, 8), new THREE.MeshStandardMaterial({ color: col, emissive: 0xc77dff, emissiveIntensity: 0.55 }));
      mesh.position.y = 0.35;
    } else {
      mesh = new THREE.Mesh(new THREE.BoxGeometry(0.45, 0.45, 0.45), new THREE.MeshStandardMaterial({ color: col, roughness: 0.8 }));
      mesh.position.y = 0.25;
    }
  } else {
    mesh = new THREE.Mesh(new THREE.SphereGeometry(0.18, 8, 6), new THREE.MeshStandardMaterial({ color: col, emissive: 0xffba08, emissiveIntensity: 0.6 }));
    mesh.position.y = 0.2;
  }
  g.add(mesh);
  if (e.kind === "mob" || e.kind === "npc") g.add(makeNameSprite(e.name || e.kind, e.kind === "npc" ? "#c77dff" : "#efe6d2"));
  g.userData.kind = e.kind;
  return g;
}
function clearGroup(g) { if (!g) return; scene.remove(g); disposeObject(g); }
function rebuildTerrain(state) {
  clearGroup(terrainGroup);
  terrainGroup = new THREE.Group();
  const w = state.w || 0, h = state.h || 0, tiles = state.tiles || [];
  const buckets = new Map();
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const t = tiles[y * w + x] | 0;
      let list = buckets.get(t); if (!list) { list = []; buckets.set(t, list); }
      list.push(x, y);
    }
  }
  const geo = new THREE.BoxGeometry(1, 0.16, 1);
  for (const [t, xy] of buckets) {
    const n = xy.length / 2;
    const isWater = t === T.WATER || t === T.WATER_D;
    const isHearth = t === T.HEARTH, isShrine = t === T.SHRINE;
    const mat = new THREE.MeshStandardMaterial({ color: PAL[t] ?? 0x112211, roughness: isWater ? 0.22 : 0.88, metalness: isWater ? 0.18 : 0, emissive: isHearth ? 0x8a3a12 : isShrine ? 0x4a3a62 : 0x000000, emissiveIntensity: isHearth ? 0.7 : isShrine ? 0.35 : 0 });
    const mesh = new THREE.InstancedMesh(geo, mat, n);
    const yOff = isWater ? -0.14 : isHearth ? 0.05 : 0;
    for (let i = 0; i < n; i++) {
      dummy.position.set(xy[i * 2] + 0.5, yOff, xy[i * 2 + 1] + 0.5);
      dummy.rotation.set(0, 0, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    }
    mesh.instanceMatrix.needsUpdate = true; terrainGroup.add(mesh);
  }
  for (const tr of state.trees || []) terrainGroup.add(makeTree(tr));
  for (const r of state.rocks || []) terrainGroup.add(makeRock(r));
  for (const pr of state.props || []) {
    const bw = pr.w || 1, bh = pr.h || 1;
    const box = new THREE.Mesh(new THREE.BoxGeometry(bw, 0.45, bh), new THREE.MeshStandardMaterial({ color: 0x3d2918, roughness: 0.85 }));
    box.position.set((pr.x || 0) + bw / 2, 0.25, (pr.y || 0) + bh / 2);
    terrainGroup.add(box);
  }
  for (const b of state.buildings || []) {
    const bw = b.w || 4, bd = b.h || 4, bhgt = b.hgt || 3.2;
    const pal = b.palette || ["#6b3fa0", "#2a1830", "#c77dff"];
    const col = new THREE.Color(pal[0] || "#6b3fa0");
    const box = new THREE.Mesh(new THREE.BoxGeometry(Math.max(0.8, bw - 0.3), bhgt, Math.max(0.8, bd - 0.3)), new THREE.MeshStandardMaterial({ color: col, roughness: 0.55, emissive: b.flagship ? col : 0x000000, emissiveIntensity: b.flagship ? 0.45 : 0 }));
    box.position.set((b.x || 0) + bw / 2, bhgt / 2, (b.y || 0) + bd / 2);
    terrainGroup.add(box);
    const roof = new THREE.Mesh(new THREE.ConeGeometry(Math.max(bw, bd) * 0.55, 1.1, 4), new THREE.MeshStandardMaterial({ color: pal[2] || "#222", roughness: 0.7 }));
    roof.position.set(box.position.x, bhgt + 0.5, box.position.z); roof.rotation.y = Math.PI / 4;
    terrainGroup.add(roof);
  }
  for (const L of state.lights || []) {
    const c = L.color || [255, 140, 50];
    const pl = new THREE.PointLight(new THREE.Color(c[0] / 255, c[1] / 255, c[2] / 255), 1.6, (L.r || 5) * 2.4, 1.5);
    pl.position.set(L.x, 1.35, L.y); terrainGroup.add(pl);
  }
  scene.add(terrainGroup);
}
function syncMap(map, list, factory, skip) {
  const seen = new Set();
  for (const item of list || []) {
    if (skip && skip(item)) continue;
    seen.add(item.id);
    let obj = map.get(item.id);
    if (!obj) { obj = factory(item); obj.userData.id = item.id; obj.userData.kind = item.kind || obj.userData.kind; map.set(item.id, obj); scene.add(obj); }
    obj.userData.id = item.id; obj.userData.kind = item.kind || obj.userData.kind;
    obj.position.set(item.x, 0, item.y); obj.visible = true;
  }
  for (const [id, obj] of map) {
    if (!seen.has(id)) { scene.remove(obj); disposeObject(obj); map.delete(id); }
  }
}
function followPlayer(state) {
  const me = state.me; if (!me) return;
  _desired.set(me.x, 0.45, me.y); _follow.lerp(_desired, 0.14);
  const ox = camera.position.x - controls.target.x;
  const oy = camera.position.y - controls.target.y;
  const oz = camera.position.z - controls.target.z;
  controls.target.copy(_follow);
  camera.position.set(_follow.x + ox, Math.max(1.2, _follow.y + oy), _follow.z + oz);
}
export function init(el) {
  canvas = el;
  renderer = new THREE.WebGLRenderer({ canvas, alpha: false, antialias: true });
  renderer.setClearColor(0x07050c, 1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x07050c);
  scene.fog = new THREE.Fog(0x07050c, 22, 62);
  camera = new THREE.PerspectiveCamera(50, 1, 0.1, 220);
  camera.position.set(18, 16, 30);
  controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.minPolarAngle = 0.25; controls.maxPolarAngle = 1.2;
  controls.minDistance = 6; controls.maxDistance = 28; controls.enablePan = false;
  controls.mouseButtons = { LEFT: -1, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE };
  controls.target.set(22.5, 0.45, 18.5); _follow.copy(controls.target);
  scene.add(new THREE.HemisphereLight(0x8a7aaa, 0x1a1008, 0.62));
  scene.add(new THREE.AmbientLight(0x2a2438, 0.28));
  const dir = new THREE.DirectionalLight(0xc4b8a0, 0.4); dir.position.set(18, 28, 12); scene.add(dir);
  groundPlane = new THREE.Mesh(new THREE.PlaneGeometry(800, 800), new THREE.MeshBasicMaterial({ visible: false, side: THREE.DoubleSide }));
  groundPlane.rotation.x = -Math.PI / 2; scene.add(groundPlane);
  canvas.addEventListener("pointerdown", (e) => { if (e.button !== 0 && e.button !== 2) return; pointerDown.x = e.clientX; pointerDown.y = e.clientY; });
  resize();
}
export function resize() {
  if (!renderer || !canvas) return;
  const w = innerWidth, h = Math.max(1, innerHeight), dpr = Math.min(devicePixelRatio || 1, 2);
  renderer.setPixelRatio(dpr); renderer.setSize(w, h, false);
  canvas.style.width = w + "px"; canvas.style.height = h + "px";
  camera.aspect = w / h; camera.updateProjectionMatrix();
}
export function pick(event) {
  if (!camera || !canvas) return null;
  if (Math.hypot(event.clientX - pointerDown.x, event.clientY - pointerDown.y) > 6) return null;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  _mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  _mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  _raycaster.setFromCamera(_mouse, camera);
  const hits = _raycaster.intersectObject(groundPlane, false);
  if (!hits.length) return null;
  const p = hits[0].point; return { x: p.x, y: p.z };
}
export function getObjectAt(event) {
  if (!camera || !canvas) return null;
  const rect = canvas.getBoundingClientRect();
  _mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  _mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  _raycaster.setFromCamera(_mouse, camera);
  const hits = _raycaster.intersectObjects([...playerMap.values(), ...entityMap.values()], true);
  return hits.length ? hits[0].object : null;
}
export function tick(state) {
  if (!renderer) return;
  const key = `${state.w}x${state.h}:${(state.tiles && state.tiles.length) || 0}`;
  if (state.tiles && state.tiles.length && key !== terrainKey) { terrainKey = key; rebuildTerrain(state); }
  syncMap(playerMap, state.players, (p) => makePlayer(p, p.id === state.you));
  for (const p of state.players || []) {
    const g = playerMap.get(p.id); if (!g) continue;
    updateNameSprite(g.userData.nameSpr, p.name || "wanderer", p.id === state.you ? "#f0d48a" : "#efe6d2");
  }
  syncMap(entityMap, state.entities, makeEntity, (e) => e.kind === "mob" && e.dead);
  followPlayer(state); controls.update(); renderer.render(scene, camera);
}
export function pickEntity(event) {
  const obj = getObjectAt(event); if (!obj) return null;
  let o = obj;
  while (o) {
    if (o.userData && o.userData.id) return { id: o.userData.id, kind: o.userData.kind || "entity" };
    o = o.parent;
  }
  return null;
}
