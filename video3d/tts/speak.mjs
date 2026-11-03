// Offline Kokoro TTS: node speak.mjs lines.json outdir [voice] [speed]
// lines.json: [{ "id": "l01", "text": "..." }, ...] -> outdir/<id>.wav (24 kHz mono)
import fs from 'node:fs';
import path from 'node:path';
import ort from 'onnxruntime-node';
import { phonemize } from './node_modules/kokoro-js/dist/kokoro-ph.js';

const here = path.dirname(new URL(import.meta.url).pathname);
const [linesFile, outDir, voice = 'am_michael', speedArg = '1'] = process.argv.slice(2);
const speed = Number(speedArg);
const vocab = JSON.parse(fs.readFileSync(path.join(here, 'kokoro-config.json'))).vocab;
const session = await ort.InferenceSession.create(path.join(here, 'kokoro-q8.onnx'));
const vbuf = fs.readFileSync(path.join(here, 'node_modules/kokoro-js/voices', voice + '.bin'));
const voiceData = new Float32Array(vbuf.buffer, vbuf.byteOffset, vbuf.byteLength / 4);
fs.mkdirSync(outDir, { recursive: true });

function wav(samples, rate = 24000) {
  const b = Buffer.alloc(44 + samples.length * 2);
  b.write('RIFF', 0); b.writeUInt32LE(36 + samples.length * 2, 4); b.write('WAVEfmt ', 8);
  b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22); b.writeUInt32LE(rate, 24);
  b.writeUInt32LE(rate * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36);
  b.writeUInt32LE(samples.length * 2, 40);
  samples.forEach((s, i) => b.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(s * 32767))), 44 + i * 2));
  return b;
}

for (const { id, text } of JSON.parse(fs.readFileSync(linesFile))) {
  const ph = await phonemize(text, voice[0]);
  const ids = [0, ...[...ph].map(c => vocab[c]).filter(v => v !== undefined), 0].slice(0, 512);
  const n = Math.min(Math.max(ids.length - 2, 0), 509);
  const style = voiceData.slice(n * 256, n * 256 + 256);
  const outp = await session.run({
    input_ids: new ort.Tensor('int64', BigInt64Array.from(ids.map(BigInt)), [1, ids.length]),
    style: new ort.Tensor('float32', style, [1, 256]),
    speed: new ort.Tensor('float32', Float32Array.from([speed]), [1]),
  });
  const audio = outp[Object.keys(outp)[0]].data;
  fs.writeFileSync(path.join(outDir, id + '.wav'), wav(audio));
  console.log(id, (audio.length / 24000).toFixed(2) + 's', '|', ph.slice(0, 60));
}
