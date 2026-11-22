import { chromium } from 'playwright'; import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const root=path.dirname(new URL(import.meta.url).pathname);
const mime={'.html':'text/html','.js':'text/javascript','.jpg':'image/jpeg','.png':'image/png','.woff2':'font/woff2'};
const srv=http.createServer((q,r)=>{const p=path.join(root,decodeURIComponent(q.url.split('?')[0])); if(!fs.existsSync(p)){r.writeHead(404);return r.end();} r.writeHead(200,{'content-type':mime[path.extname(p)]||'application/octet-stream'}); fs.createReadStream(p).pipe(r);}).listen(0);
const b=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']}); const pg=await b.newPage({viewport:{width:270,height:480}});
await pg.goto(`http://127.0.0.1:${srv.address().port}/index.html`); await pg.evaluate(()=>window.__ready);
fs.writeFileSync(root+'/out/pairs.json',JSON.stringify(await pg.evaluate(()=>window.__pairs))); await b.close(); srv.close();
