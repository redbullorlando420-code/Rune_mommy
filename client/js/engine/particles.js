export class Particles {
  constructor() { this.list = []; }
  emit(x, y, n, opt = {}) {
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2;
      const sp = (opt.speed || 18) * (0.4 + Math.random());
      this.list.push({
        x, y,
        vx: Math.cos(a) * sp * 0.02,
        vy: Math.sin(a) * sp * 0.02 - (opt.up || 0.05),
        life: opt.life || 700 + Math.random() * 400,
        age: 0,
        col: opt.col || 'rgba(232,93,4,.9)',
        s: opt.s || 2 + Math.random() * 2,
      });
    }
  }
  ember(x, y) { this.emit(x, y, 1, { col: 'rgba(255,186,8,.85)', speed: 8, up: 0.12, life: 1200, s: 1.8 }); }
  hit(x, y, magic) { this.emit(x, y, 10, { col: magic ? 'rgba(199,125,255,.9)' : 'rgba(255,80,60,.9)', speed: 40, up: 0.02, life: 420 }); }
  sparkle(x, y) { this.emit(x, y, 8, { col: 'rgba(128,237,153,.9)', speed: 16, up: 0.08, life: 600 }); }
  tick(dt) {
    for (const p of this.list) {
      p.age += dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.vy -= 0.00002 * dt;
    }
    this.list = this.list.filter((p) => p.age < p.life);
  }
  draw(g, cam, tile) {
    for (const p of this.list) {
      const a = 1 - p.age / p.life;
      g.globalAlpha = a;
      g.fillStyle = p.col;
      g.fillRect(p.x * tile - cam.x, p.y * tile - cam.y, p.s, p.s);
    }
    g.globalAlpha = 1;
  }
}
