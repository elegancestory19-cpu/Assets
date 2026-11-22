import { chromium } from 'playwright';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const root = path.dirname(new URL(import.meta.url).pathname);
const mime={'.html':'text/html','.js':'text/javascript','.jpg':'image/jpeg','.png':'image/png','.woff2':'font/woff2'};
const srv=http.createServer((q,r)=>{const p=path.join(root,decodeURIComponent(q.url.split('?')[0])); if(!p.startsWith(root)||!fs.existsSync(p)){r.writeHead(404);return r.end();} r.writeHead(200,{'content-type':mime[path.extname(p)]||'application/octet-stream'}); fs.createReadStream(p).pipe(r);}).listen(0);
const b = await chromium.launch({ args: ['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
const page = process.argv[2] || 'index.html';
await pg.goto(`http://127.0.0.1:${srv.address().port}/${page}`);
if (page === 'index.html') { await pg.evaluate(() => window.__ready); await pg.evaluate(() => window.__cover()); await pg.waitForTimeout(200); }
else { await pg.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.fonts].map(f => f.load())); await Promise.all([...document.images].map(i => i.decode())); }); }
await pg.screenshot({ path: root + '/' + (process.argv[3] || 'assets/cover_bg.png') });
await b.close(); srv.close();
