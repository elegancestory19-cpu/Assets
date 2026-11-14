import { chromium } from 'playwright';
import path from 'node:path';
const root = path.dirname(new URL(import.meta.url).pathname);
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await p.goto('file://' + root + '/cover.html');
await p.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.fonts].map(f => f.load())); });
await p.screenshot({ path: root + '/out/cover.png' });
await b.close();
