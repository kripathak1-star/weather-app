// Builds the voice track from narration.json + per-line WAVs, then mixes voice, music, rain/wind and muxes the video.
//   node mix.mjs <voDir> <music.wav> <video.mp4> <out.mp4>
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const [voDir, music, video, out] = process.argv.slice(2);
const SR = 24000, DUR = 600, N = SR * DUR;
const lines = JSON.parse(fs.readFileSync(new URL('./narration.json', import.meta.url)));
const voice = new Float32Array(N);
const readWav = f => { const b = fs.readFileSync(f); const d = new Int16Array(b.buffer.slice(b.byteOffset + 44, b.byteOffset + b.length)); return Float32Array.from(d, x => x / 32768); };
const place = (file, t) => { const s = readWav(file), o = Math.floor(t * SR); for (let i = 0; i < s.length && o + i < N; i++) voice[o + i] += s[i]; };

lines.forEach((l, i) => {
  if (['Three.', 'Two.', 'One.'].includes(l.text)) return;   // replaced by one countdown clip
  place(path.join(voDir, `n${String(i).padStart(2, '0')}.wav`), l.t);
});
place(path.join(voDir, 'cd.wav'), 534.9);

const wavBuf = Buffer.alloc(44 + N * 2);
wavBuf.write('RIFF', 0); wavBuf.writeUInt32LE(36 + N * 2, 4); wavBuf.write('WAVEfmt ', 8); wavBuf.writeUInt32LE(16, 16);
wavBuf.writeUInt16LE(1, 20); wavBuf.writeUInt16LE(1, 22); wavBuf.writeUInt32LE(SR, 24); wavBuf.writeUInt32LE(SR * 2, 28);
wavBuf.writeUInt16LE(2, 32); wavBuf.writeUInt16LE(16, 34); wavBuf.write('data', 36); wavBuf.writeUInt32LE(N * 2, 40);
for (let i = 0; i < N; i++) wavBuf.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(voice[i] * 32767))), 44 + i * 2);
const voiceWav = path.join(path.dirname(out), 'build', 'voice.wav');
fs.writeFileSync(voiceWav, wavBuf);

// rain/wind bed that follows the chapters (same curve as before, a bit quieter under the music)
const loud = '0.7*between(t,0,6)+0.25*between(t,6,20)+0.4*between(t,150,240)+0.2*between(t,300,320)+0.8*between(t,320,400)+0.55*between(t,400,470)+0.7*between(t,530,572)+0.05';
const filter = [
  `[1]aresample=44100,pan=stereo|c0=c0|c1=c0,highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,volume=2.0,asplit=2[vo][sc]`,
  `[3]lowpass=f=900,volume='${loud}':eval=frame[rain]`,
  `[2][rain]amix=inputs=2:normalize=0[bed]`,
  `[bed][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]`,
  `[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]`,
].join(';');
const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', video, '-i', voiceWav, '-i', music,
  '-f', 'lavfi', '-i', `anoisesrc=color=brown:amplitude=0.5:d=${DUR}:r=44100`,
  '-filter_complex', filter, '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '44100',
  '-shortest', '-movflags', '+faststart', out], { stdio: 'inherit' });
if (r.status) process.exit(r.status);
console.log('wrote', out);
