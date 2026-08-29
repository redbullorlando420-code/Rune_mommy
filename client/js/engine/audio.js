/** Tiny procedural mixer. No assets required. */
export class Audio {
  constructor() {
    this.ctx = null;
    this.master = null;
    this.muted = false;
    this.amb = null;
  }
  unlock() {
    if (this.ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.22;
    this.master.connect(this.ctx.destination);
    this.ambient();
  }
  ambient() {
    if (!this.ctx || this.amb) return;
    const ctx = this.ctx;
    const osc = ctx.createOscillator();
    osc.type = 'sine';
    osc.frequency.value = 62;
    const osc2 = ctx.createOscillator();
    osc2.type = 'triangle';
    osc2.frequency.value = 93;
    const g = ctx.createGain();
    g.gain.value = 0.08;
    const f = ctx.createBiquadFilter();
    f.type = 'lowpass';
    f.frequency.value = 240;
    osc.connect(f); osc2.connect(f); f.connect(g); g.connect(this.master);
    osc.start(); osc2.start();
    this.amb = { osc, osc2, g };
    // sparse high bell
    this._bellIv = setInterval(() => { if (!this.muted && Math.random() < 0.4) this.bell(880 + Math.random() * 200, 0.04); }, 6000);
  }
  beep(freq, dur = 0.08, type = 'square', gain = 0.12, slide = 0) {
    if (!this.ctx || this.muted) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(40, freq + slide), t + dur);
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + dur);
    o.connect(g); g.connect(this.master);
    o.start(t); o.stop(t + dur + 0.02);
  }
  click() { this.beep(720, 0.04, 'square', 0.07); }
  hit() { this.beep(140, 0.12, 'sawtooth', 0.16, -80); }
  gather() { this.beep(520, 0.09, 'triangle', 0.1, 200); }
  level() { this.beep(523, 0.12, 'square', 0.12); setTimeout(() => this.beep(659, 0.12, 'square', 0.12), 90); setTimeout(() => this.beep(784, 0.18, 'square', 0.14), 180); }
  trade() { this.beep(660, 0.1, 'sine', 0.1); setTimeout(() => this.beep(990, 0.16, 'sine', 0.12), 100); }
  ui() { this.beep(880, 0.05, 'sine', 0.06); }
  death() { this.beep(200, 0.4, 'sawtooth', 0.12, -140); }
  bell(f, g = 0.05) { this.beep(f, 0.8, 'sine', g, 0); }
}
