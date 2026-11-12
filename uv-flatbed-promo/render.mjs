// node render.mjs shots 1.0 3.2 ...   -> out/shots/*.png (540x960)
// node render.mjs video               -> out/silent.mp4 (1080x1920, 30fps)
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const root = path.dirname(new URL(import.meta.url).pathname);
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.json': 'application/json' };
const srv = http.createServer((q, r) => {
  const p = path.join(root, decodeURIComponent(q.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p)) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'content-type': mime[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(r);
}).listen(0);
const url = `http://127.0.0.1:${srv.address().port}/index.html`;
const [mode, ...args] = process.argv.slice(2);
const full = mode === 'video';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: full ? { width: 1080, height: 1920 } : { width: 540, height: 960 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('PAGEERROR', e.message));
page.on('requestfailed', q => console.error('REQFAIL', q.url()));
await page.goto(url);
await page.evaluate(() => window.__ready);
const dur = await page.evaluate(() => window.__dur);
if (mode === 'shots') {
  fs.mkdirSync(`${root}/out/shots`, { recursive: true });
  for (const a of args) {
    await page.evaluate(t => window.__seek(t), +a);
    await page.screenshot({ path: `${root}/out/shots/${(+a).toFixed(2).padStart(5, '0')}.png` });
  }
} else {
  const n = Math.round(dur * 30);
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', '30', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'slow', `${root}/out/silent.mp4`], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.__seek(t), i / 30);
    const buf = await page.screenshot({ type: 'jpeg', quality: 96 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i === Math.round(21.6 * 30)) fs.writeFileSync(`${root}/out/poster.jpg`, buf);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('frames', n);
}
await browser.close(); srv.close();
