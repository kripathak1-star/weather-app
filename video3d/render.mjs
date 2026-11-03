// Renders scene.html frame-by-frame with headless Chromium and encodes an MP4 with ffmpeg.
// Usage: node render.mjs [fps]
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const FPS = Number(process.argv[2] || 30);
const root = path.dirname(new URL(import.meta.url).pathname);

const types = { '.html': 'text/html', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  const file = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!file.startsWith(root) || !fs.existsSync(file)) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.error('[page error]', e));
await page.goto(`http://localhost:${port}/scene.html?capture`);
await page.waitForFunction(() => window.ready);
const duration = await page.evaluate(() => window.DURATION);

const out = path.join(root, 'weather-planet-3d.mp4');
const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', out],
  { stdio: ['pipe', 'ignore', 'inherit'] });

const total = Math.round(duration * FPS);
for (let i = 0; i < total; i++) {
  const b64 = await page.evaluate(t => { window.renderFrame(t); return document.querySelector('canvas').toDataURL('image/png').split(',')[1]; }, i / FPS);
  ff.stdin.write(Buffer.from(b64, 'base64'));
  if (i % 30 === 0) console.log(`frame ${i}/${total}`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
server.close();
console.log('wrote', out);
