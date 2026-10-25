const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const mode = process.argv[2];
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png' };
const srv = http.createServer((q, r) => { const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); });
srv.listen(0, async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: +(process.env.DSF || 1) });
  p.on('pageerror', e => console.log('ERR', e.message));
  p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await p.goto(`http://127.0.0.1:${srv.address().port}/ad3.html`);
  await p.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  if (mode === 'probe') {
    let n = 0;
    for (const t of process.argv.slice(3).map(Number)) { await p.evaluate(t => renderAt(t), t);
      await p.screenshot({ path: `pr_${String(n++).padStart(2, '0')}.jpg`, type: 'jpeg', quality: 80 }); }
  } else {
    const FPS = 30, a = +process.argv[3], z = +process.argv[4];
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', process.argv[5]], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = a; i < z; i++) { await p.evaluate(t => renderAt(t), i / FPS);
      const buf = await p.screenshot({ type: 'jpeg', quality: 93 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if ((i - a) % 150 === 0) console.log(`${process.argv[5]} ${i - a}/${z - a}`); }
    ff.stdin.end(); await new Promise(r => ff.on('close', r)); console.log(`${process.argv[5]} done`);
  }
  await b.close(); srv.close();
});
