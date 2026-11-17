import { chromium } from 'playwright';
import fs from 'node:fs';
const svg = fs.readFileSync('assets/dielines/03_boite-gable-patisserie.svg','utf8');
const b = await chromium.launch(); const p = await b.newPage();
await p.setContent(`<body>${svg}</body>`);
const r = await p.evaluate(() => {
  const g = document.querySelector('#MARQUAGE');
  const out = [...g.children].map(c => { const bb = c.getBBox(); return [c.tagName, c.getAttribute('transform')||'', +bb.x.toFixed(1), +bb.y.toFixed(1), +bb.width.toFixed(1), +bb.height.toFixed(1)]; });
  const vb = document.querySelector('svg').getAttribute('viewBox');
  return {vb, n: out.length, out: out.slice(0, 40)};
});
console.log(JSON.stringify(r));
await b.close();
