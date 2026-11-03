// Renders long.html into a 10-minute MP4 using several headless Chromium workers in parallel,
// then adds a generated ambient soundtrack (pad + rain/wind) with ffmpeg.
//   node render-long.mjs [fps=30] [workers=3]
//   node render-long.mjs --preview 5 65 160 ...   (writes PNG stills for the given seconds)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const root = path.dirname(new URL(import.meta.url).pathname);
const outDir = path.join(root, 'build'); fs.mkdirSync(outDir, { recursive: true });

const types = { '.html': 'text/html', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  const file = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!file.startsWith(root) || !fs.existsSync(file)) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}).listen(0);
const url = `http://localhost:${server.address().port}/long.html?capture`;

async function openPage() {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('pageerror', e => console.error('[page error]', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('[page]', m.text()); });
  await page.goto(url);
  await page.waitForFunction(() => window.ready);
  return { browser, page };
}
const grab = (page, t, fmt) => page.evaluate(([t, fmt]) => {
  window.renderFrame(t);
  return document.querySelectorAll('canvas')[1].toDataURL(fmt, 0.93).split(',')[1];
}, [t, fmt]);
const run = (args) => new Promise((ok, bad) => { const p = spawn('ffmpeg', args, { stdio: ['ignore', 'ignore', 'inherit'] }); p.on('close', c => c ? bad(new Error('ffmpeg ' + c)) : ok()); });

const argv = process.argv.slice(2);
if (argv[0] === '--preview') {
  const { browser, page } = await openPage();
  for (const s of argv.slice(1)) {
    const t0 = Date.now();
    fs.writeFileSync(path.join(outDir, `p_${s}.png`), Buffer.from(await grab(page, Number(s), 'image/png'), 'base64'));
    console.log('still', s, Date.now() - t0, 'ms');
  }
  await browser.close(); server.close(); process.exit(0);
}

const FPS = Number(argv[0] || 30), WORKERS = Number(argv[1] || 3);
const DURATION = 600, total = DURATION * FPS, per = Math.ceil(total / WORKERS);
const started = Date.now();
await Promise.all([...Array(WORKERS).keys()].map(async w => {
  const from = w * per, to = Math.min(total, from + per);
  const { browser, page } = await openPage();
  const file = path.join(outDir, `chunk_${w}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'veryfast', file], { stdio: ['pipe', 'ignore', 'inherit'] });
  for (let i = from; i < to; i++) {
    const buf = Buffer.from(await grab(page, i / FPS, 'image/jpeg'), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((i - from) % 300 === 0) {
      const done = i - from, el = (Date.now() - started) / 1000;
      console.log(`worker ${w}: ${done}/${to - from} frames, ${el.toFixed(0)}s elapsed`);
    }
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await browser.close();
}));
server.close();

// soundtrack: A-minor pad with slow swell + brown-noise rain/wind that follows the chapters
const loud = '0.9*between(t,0,6)+0.35*between(t,6,20)+0.5*between(t,150,240)+0.25*between(t,300,320)+1.0*between(t,320,400)+0.7*between(t,400,470)+1.0*between(t,530,572)+0.08';
const pad = ['110', '164.81', '220', '261.63', '329.63'].map((f, i) => `0.05*sin(2*PI*${f}*t)*(0.6+0.4*sin(2*PI*${(0.05 + i * 0.013).toFixed(3)}*t))`).join('+');
await run(['-y', '-loglevel', 'error',
  '-f', 'lavfi', '-i', `aevalsrc='${pad}':s=44100:d=${DURATION}`,
  '-f', 'lavfi', '-i', `anoisesrc=color=brown:amplitude=0.6:d=${DURATION}:r=44100`,
  '-filter_complex', `[0]lowpass=f=1200,aecho=0.8:0.7:400|900:0.35|0.25[p];[1]lowpass=f=900,volume='${loud}':eval=frame[n];[p][n]amix=inputs=2:normalize=0,afade=t=in:d=2,afade=t=out:st=${DURATION - 3}:d=3,alimiter=limit=0.9[a]`,
  '-map', '[a]', '-c:a', 'aac', '-b:a', '160k', path.join(outDir, 'audio.m4a')]);

const list = path.join(outDir, 'list.txt');
fs.writeFileSync(list, [...Array(WORKERS).keys()].map(w => `file 'chunk_${w}.mp4'`).join('\n'));
const final = path.join(root, 'every-sky-10min.mp4');
await run(['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-i', path.join(outDir, 'audio.m4a'),
  '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy', '-shortest', '-movflags', '+faststart', final]);
console.log('wrote', final, `in ${((Date.now() - started) / 60000).toFixed(1)} min`);
