const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const mode = process.argv[2];
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const srv = http.createServer((q, r) => { const f = path.join(path.resolve(__dirname,'..'), decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' }); r.end(d); }); });
const FPS = 30;
srv.listen(0, async () => {
  const port = srv.address().port;
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: mode === 'thumb' ? 1.5 : (+process.env.DSF || 1) });
  p.on('pageerror', e => console.log('ERR', e.message));
  p.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await p.goto(`http://127.0.0.1:${port}/engine/engine.html`);
  await p.waitForFunction(() => window.READY);
  await p.evaluate(() => window.READY);
  const TL = await p.evaluate(() => window.TIMELINE);
  if (mode === 'events') { fs.writeFileSync(process.argv[3]||'events.json', JSON.stringify({ events: await p.evaluate(() => window.EVENTS), starts: TL.starts })); }
  else if (mode === 'thumb') {
    const th = JSON.parse(fs.readFileSync(process.argv[3]));
    await p.evaluate(t => renderAt(t), TL.starts[th.scene || 0] + TL.durs[th.scene || 0] * (th.f ?? 0.5));
    await p.evaluate(th => {
      document.querySelectorAll('.scene,#prog,#cap,#flash').forEach(e => e.style.display = 'none');
      document.getElementById('shade').style.cssText = 'position:absolute;inset:0;opacity:1;background:linear-gradient(90deg,rgba(2,3,10,.92) 0%,rgba(2,3,10,.65) 45%,rgba(2,3,10,0) 65%)';
      const d = document.createElement('div');
      const st = 'position:absolute;left:52px;font-family:"Inter Display","Baloo 2";font-weight:900;line-height:1.02;-webkit-text-stroke:4px rgba(0,0,0,.6);paint-order:stroke fill;text-shadow:0 8px 40px rgba(0,0,0,.9)';
      d.innerHTML = `<div style='${st};top:70px;font-size:${th.s1||110}px;color:#38f3ff;max-width:760px'>${th.line1}</div>
        <div style='${st};top:${th.top2||200}px;font-size:${th.s2||100}px;color:#ffb627;max-width:760px'>${th.line2||''}</div>
        <div style='position:absolute;left:56px;top:${th.top3||470}px;font:900 44px "Inter Display","Baloo 2";color:#fff;background:#ff2d55;border:5px solid #fff;border-radius:16px;padding:8px 22px;transform:rotate(-3deg)'>${th.badge||''}</div>`;
      document.getElementById('ov').appendChild(d);
    }, th);
    await p.screenshot({ path: process.argv[4], type: 'jpeg', quality: 92 });
  }
  else if (mode === 'probe') {
    let n = 0;
    for (const spec of process.argv.slice(3)) { const [i, f] = spec.split(':').map(Number);
      const t0 = Date.now(); await p.evaluate(t => renderAt(t), TL.starts[i] + TL.durs[i] * f);
      await p.screenshot({ path: `pr_${String(n++).padStart(2, '0')}.jpg`, type: 'jpeg', quality: 80 }); console.log('frame ms', Date.now() - t0); }
  } else {
    const N = Math.round(TL.T_END * FPS); const a = +process.argv[3], z = Math.min(N, +process.argv[4]);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-pix_fmt', 'yuv420p', process.argv[5]], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = a; i < z; i++) {
      await p.evaluate(t => renderAt(t), i / FPS);
      const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if ((i - a) % 300 === 0) console.log(`${process.argv[5]} ${i - a}/${z - a} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r)); console.log(`${process.argv[5]} done`);
  }
  await b.close(); srv.close();
});
