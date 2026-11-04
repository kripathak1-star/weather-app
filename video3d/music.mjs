// Procedural soundtrack for long.html: chord pads, arpeggio, drums, chapter impacts and thunder.
//   node music.mjs out.wav
import fs from 'node:fs';

const CFG = process.env.MUSIC_CFG ? JSON.parse(fs.readFileSync(process.env.MUSIC_CFG)) : null;
const SR = 44100, DUR = CFG ? CFG.dur : 600, N = SR * DUR;
const L = new Float32Array(N), R = new Float32Array(N);
let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647) * 2 - 1;

// chapter intensity (0 calm .. 1 full drums)
const SECTIONS = [[0, 20, 1.0], [20, 60, 0.45], [60, 150, 0.65], [150, 240, 0.8], [240, 300, 0.3], [300, 320, 1.0],
  [320, 400, 0.85], [400, 470, 0.55], [470, 530, 0.5], [530, 572, 1.0], [572, 600, 0.35]];
if (CFG) SECTIONS.splice(0, SECTIONS.length, ...CFG.sections);
const BOUNDS = SECTIONS.map(s => s[0]).filter(t => t > 0);
const intensityAt = t => { for (const [a, b, v] of SECTIONS) if (t >= a && t < b) return v; return 0.3; };

const BPM = 100, BEAT = 60 / BPM, BAR = BEAT * 4;
const midi = m => 440 * Math.pow(2, (m - 69) / 12);
// Am - F - C - G  (epic minor loop), Dm-Am-E-Am in calm parts would add variety; keep one loop for cohesion
const PROG = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]];

// ---- pad: detuned saws through a one-pole lowpass, crossfaded per bar ----
{
  let lpL = 0, lpR = 0; const ph = new Float64Array(12);
  for (let i = 0; i < N; i++) {
    const t = i / SR, bar = Math.floor(t / BAR), chord = PROG[bar % 4];
    const inten = intensityAt(t);
    let sL = 0, sR = 0;
    chord.forEach((m, k) => {
      for (let d = 0; d < 2; d++) {
        const idx = k * 4 + d, f = midi(m - 12) * (d ? 1.004 : 0.996);
        ph[idx] = (ph[idx] + f / SR) % 1;
        const saw = ph[idx] * 2 - 1;
        if (d) sR += saw; else sL += saw;
      }
      // sub bass on root
      if (k === 0) { ph[10] = (ph[10] + midi(m - 24) / SR) % 1; const sub = Math.sin(2 * Math.PI * ph[10]) * 0.9; sL += sub; sR += sub; }
    });
    const cut = 0.02 + 0.05 * inten + 0.02 * Math.sin(t * 0.3);
    lpL += (sL - lpL) * cut; lpR += (sR - lpR) * cut;
    const barPos = (t % BAR) / BAR, env = Math.min(1, barPos * 12) * (1 - 0.15 * barPos);
    const g = 0.055 * env * (0.7 + 0.3 * inten);
    L[i] += lpL * g; R[i] += lpR * g;
  }
}

// ---- arpeggio plucks (16ths in high intensity, 8ths otherwise) ----
function pluck(t0, f, amp, pan) {
  const len = Math.floor(SR * 0.45), s0 = Math.floor(t0 * SR);
  for (let j = 0; j < len && s0 + j < N; j++) {
    const tt = j / SR, e = Math.exp(-tt * 9) * Math.min(1, tt * 400);
    const v = (Math.sin(2 * Math.PI * f * tt) + 0.35 * Math.sin(4 * Math.PI * f * tt) + 0.15 * Math.sin(6 * Math.PI * f * tt)) * e * amp;
    L[s0 + j] += v * (1 - pan); R[s0 + j] += v * pan;
  }
}
for (let t = 0; t < DUR; t += BEAT / 4) {
  const inten = intensityAt(t), step = Math.round(t / (BEAT / 4));
  if (inten < 0.6 && step % 2) continue;
  const chord = PROG[Math.floor(t / BAR) % 4], pat = [0, 1, 2, 1, 2, 0, 1, 2];
  const note = chord[pat[step % 8]] + 12 + (step % 16 >= 8 && inten > 0.7 ? 12 : 0);
  pluck(t, midi(note), 0.05 * (0.5 + 0.5 * inten), 0.5 + 0.3 * Math.sin(step * 0.7));
}

// ---- drums ----
function kick(t0, amp) {
  const s0 = Math.floor(t0 * SR), len = Math.floor(SR * 0.4); let p = 0;
  for (let j = 0; j < len && s0 + j < N; j++) {
    const tt = j / SR, f = 45 + 110 * Math.exp(-tt * 30); p += f / SR;
    const v = Math.sin(2 * Math.PI * p) * Math.exp(-tt * 7) * amp; L[s0 + j] += v; R[s0 + j] += v;
  }
}
function noiseHit(t0, amp, decay, hp) {
  const s0 = Math.floor(t0 * SR), len = Math.floor(SR * 0.3); let prev = 0;
  for (let j = 0; j < len && s0 + j < N; j++) {
    const n = rnd(), h = hp ? n - prev : n; prev = n;
    const v = h * Math.exp(-(j / SR) * decay) * amp; L[s0 + j] += v; R[s0 + j] += v * 0.9;
  }
}
for (let t = 0; t < DUR; t += BEAT) {
  const inten = intensityAt(t), b = Math.round(t / BEAT) % 4;
  if (inten >= 0.5) kick(t, 0.32 * inten);
  if (inten >= 0.75 && (b === 1 || b === 3)) noiseHit(t, 0.12 * inten, 18, false);   // snare-ish
  if (inten >= 0.6) noiseHit(t + BEAT / 2, 0.06 * inten, 60, true);                   // hat
}

// ---- chapter transitions: riser whoosh into a deep impact ----
for (const tb of BOUNDS) {
  const rs = Math.floor((tb - 1.5) * SR), re = Math.floor(tb * SR); let lp = 0;
  for (let i = Math.max(0, rs); i < re; i++) { const k = (i - rs) / (re - rs); lp += (rnd() - lp) * (0.02 + k * 0.3); const v = lp * k * k * 0.25; L[i] += v; R[i] += v; }
  const s0 = re, len = SR * 3; let p = 0;
  for (let j = 0; j < len && s0 + j < N; j++) {
    const tt = j / SR, f = 32 + 60 * Math.exp(-tt * 6); p += f / SR;
    const v = Math.sin(2 * Math.PI * p) * Math.exp(-tt * 1.6) * 0.45; L[s0 + j] += v; R[s0 + j] += v;
  }
}

// ---- thunder on every scripted lightning strike (times copied from long.html) ----
const HB = [12, 19, 27.5, 33, 41, 47.2, 54, 61, 66.5, 72, 78.3, 84].map(x => x + 150);
const OB = [3, 7.5, 9.1, 14, 19.5, 24, 24.2, 30, 34.5, 39, 44.2, 48, 52.5, 57, 57.25, 62, 66.4, 70, 73.5, 76.8].map(x => x + 320);
const FB = [6, 8.3, 9, 11.2, 13, 14.6, 15.1, 17.4, 19, 20.5, 22, 22.3, 24.1, 25.6, 27, 28.8, 30, 30.4, 32.2, 34, 35.5, 37].map(x => x + 530);
const HOOK = [0.4, 4.9];
function thunder(t0, amp) {
  const s0 = Math.floor(t0 * SR), len = SR * 3.5; let a = 0, b = 0;
  for (let j = 0; j < len && s0 + j < N; j++) {
    const tt = j / SR, n = rnd();
    a += (n - a) * 0.5; b += (n - b) * 0.015;                  // crack (bright) + rumble (dark)
    const crack = a * Math.exp(-tt * 14), rumble = b * 6 * Math.exp(-tt * 0.9) * (0.6 + 0.4 * Math.sin(tt * 9 + Math.sin(tt * 3)));
    const v = (crack * 0.5 + rumble) * amp; L[s0 + j] += v; R[s0 + j] += v * 0.85;
  }
}
if (!CFG || CFG.thunder) { [...HB, ...OB, ...HOOK].forEach(t => thunder(t, 0.55)); FB.forEach(t => thunder(t, 0.4)); }
// optional tanpura-style drone (Sa-Pa-Sa) with slow pluck cycle
if (CFG && CFG.drone) { const notes = [45, 52, 57, 45]; for (let t = 0; t < DUR; t += 0.9) { const f = midi(notes[Math.round(t / 0.9) % 4]); const s0 = Math.floor(t * SR), len = SR * 3.2; for (let j = 0; j < len && s0 + j < N; j++) { const tt = j / SR, e = Math.exp(-tt * 1.1) * Math.min(1, tt * 60); let v = 0; for (let h = 1; h <= 7; h++) v += Math.sin(2 * Math.PI * f * h * tt + h) / (h * (1 + Math.abs(h - 4) * 0.3)); v *= e * 0.022; L[s0 + j] += v; R[s0 + j] += v * 0.9; } } }

// ---- master: fades + soft clip ----
let peak = 0;
for (let i = 0; i < N; i++) {
  const t = i / SR, f = Math.min(1, t / 0.5, (DUR - t) / 3);
  L[i] = Math.tanh(L[i] * f * 1.2); R[i] = Math.tanh(R[i] * f * 1.2);
  peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
}
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVEfmt ', 8); buf.writeUInt32LE(16, 16);
buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 4, 28);
buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) { buf.writeInt16LE(Math.round(L[i] * 32000), 44 + i * 4); buf.writeInt16LE(Math.round(R[i] * 32000), 46 + i * 4); }
fs.writeFileSync(process.argv[2] || 'music.wav', buf);
console.log('music written, peak', peak.toFixed(2));
