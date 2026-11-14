// node render.mjs shots 1 2 3 ...  -> shots/epNN_k.png (4 key frames each, 540x960)
// node render.mjs video 1 2 3 ...  -> out/silent/epNN.mp4 (1080x1920, 30fps)
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const here = path.dirname(new URL(import.meta.url).pathname), root = path.dirname(here);
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.json': 'application/json' };
const srv = http.createServer((q, r) => {
  const p = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p)) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'content-type': mime[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(r);
}).listen(0);
const [mode, ...eps] = process.argv.slice(2);
const full = mode === 'video';
fs.mkdirSync(`${here}/shots`, { recursive: true }); fs.mkdirSync(`${here}/out/silent`, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: full ? { width: 1080, height: 1920 } : { width: 540, height: 960 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('PAGEERROR', e.message));
page.on('requestfailed', q => console.error('REQFAIL', q.url()));
for (const ep of eps) {
  const id = String(ep).padStart(2, '0');
  await page.goto(`http://127.0.0.1:${srv.address().port}/daily/short.html?ep=${ep}`);
  await page.evaluate(() => window.__ready);
  const dur = await page.evaluate(() => window.__dur);
  if (!full) {
    const fd = await page.evaluate(() => FD);
    const ts = [1.4, fd * 0.5 + 0.9, fd - 0.2, dur - 0.3];
    for (let k = 0; k < ts.length; k++) { await page.evaluate(t => window.__seek(t), ts[k]); await page.screenshot({ path: `${here}/shots/ep${id}_${k}.png` }); }
    continue;
  }
  const n = Math.round(dur * 30);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', '30', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-preset', 'medium', `${here}/out/silent/ep${id}.mp4`], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.__seek(t), i / 30);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('ep', id, 'frames', n);
}
await browser.close(); srv.close();
