// film.js: «كلّش تحت سقف واحد», Elegance Story, Dark Tech Keynote, 1080×1920
import * as E from './engine.js';
import { K, DUR, STORM, TABS, PREV, CHIPS, CODES, LAND, PUTROW, LOCKS, BLOCKS, RETRACT, LINES } from './timeline.js';
const { clamp, lerp, seg, ss, eo, ei, eio, back, spring, mulberry, hash, TAU, PAL, CX } = E;
export { DUR };

let IMG = [], LOGO = null, LOGOW = null;
export async function loadAssets() {
  const ld = src => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
  IMG = await Promise.all(Array.from({ length: 12 }, (_, i) => ld(`img/${String(i + 1).padStart(2, '0')}.jpg`)));
  LOGO = await ld('img/logo3d.jpg'); LOGOW = await ld('img/logo_white.png');
}
const im = n => IMG[n - 1];
const within = (t, a, b) => t >= a && t < b;

// ───────── transforms
function withRect(g, dst, cur, fn) {   // draw fn laid out in dst, mapped onto cur
  g.save(); g.translate(cur.x, cur.y); g.scale(cur.w / dst.w, cur.h / dst.h); g.translate(-dst.x, -dst.y); fn(); g.restore();
}
function squash(g, cx, cy, p, fn) {    // CRT-off collapse of the real surface
  if (p >= 1) return; const { sx, sy } = E.crtOff(p); if (sx < 0.01) return;
  g.save(); g.translate(cx, cy); g.scale(sx, sy); g.translate(-cx, -cy);
  if (p > 0.45) { fn(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = seg(p, 0.45, 0.8) * 0.8; g.fillStyle = PAL.accent; g.fillRect(0, cy - 3, E.W, 6); }
  else fn();
  g.restore();
}
/** chapter surface life: expand from a centre line at a, collapse at b */
function life(g, t, a, b, rect, fn, o = {}) {
  const { from = { x: rect.x + rect.w / 2 - 4, y: rect.y + rect.h / 2 - 2, w: 8, h: 4 }, ein = 0.35, eout = 0.22 } = o;
  if (t < a || t >= b) return;
  const cx = rect.x + rect.w / 2, cy = rect.y + rect.h / 2;
  const pin = seg(t, a, a + ein), pout = seg(t, b - eout, b);
  squash(g, cx, cy, pout, () => { if (pin < 1) withRect(g, rect, E.expand(from, rect, pin), fn); else fn(); });
}

// ───────── S1–S3 storm / freeze / click
const NEEDS = ['لوغو؟', 'كارطات فيزيت؟', 'ستيكرز؟', 'لافتة مضوّية؟', 'رول أب؟', 'تيشرتات؟', 'فيديو؟', 'موقع ويب؟', 'طباعة على الزجاج؟', 'واجهة كبيرة؟', 'بروشورات؟', 'كاسكيطات؟', 'كؤوس بالشعار؟', 'ستاند معرض؟', 'بطاقات دعوة؟'];
const BADGES = ['مشغول', 'بعيد', 'ما كاينش', 'غدوة؟', 'مشغول', '!'];
const TILE = { x: CX, y: 860, s: 150 };
const CARDS = STORM.map((t, i) => {
  const R = mulberry(i * 977 + 31);
  let x = 130 + R() * 760, y = 250 + R() * 1180;
  if (Math.hypot(x - TILE.x, y - TILE.y) < 170) y += 260;
  return { t, i, x, y, rot: (R() - 0.5) * 0.24, kind: i % 3, label: NEEDS[i % NEEDS.length], badge: BADGES[Math.floor(R() * BADGES.length)], px: 30 + R() * 6 };
});
function card(g, c, tt, gs) {
  const w = E.measure(g, c.label, c.px, 700) + 150, h = c.px * 2.9;
  g.save(); g.translate(c.x, c.y); g.rotate(c.rot); g.scale(gs, gs);
  E.panel(g, -w / 2, -h / 2, w, h, { r: h * 0.3, fill: PAL.surf2, cheap: true });
  g.fillStyle = 'rgba(255,255,255,.08)'; g.beginPath(); g.arc(w / 2 - h * 0.5, 0, h * 0.24, 0, TAU); g.fill();
  E.text(g, '؟', w / 2 - h * 0.5, 2, { px: c.px * 0.8, wt: 700, color: PAL.dim });
  E.text(g, c.label, w / 2 - h * 0.92, 2, { px: c.px, wt: 700, align: 'right' });
  E.redBadge(g, -w / 2 + 8, -h / 2 + 6, c.badge, c.px / 34);
  g.restore();
}
function stormCam(t) {
  if (t < K.freeze) return E.camera({ x: CX, y: 860, zoom: lerp(1.0, 1.08, ss(t / K.freeze)), rot: 0.07 });
  if (t < K.click) { const p = eio(seg(t, K.freeze, K.click)); return E.camera({ x: CX, y: lerp(860, TILE.y, p), zoom: lerp(1.08, 1.28, p), rot: lerp(0.07, 0.035, p) }); }
  const p = eo(seg(t, K.click, K.click + 0.5)); return E.camera({ x: CX, y: 860, zoom: lerp(1.28, 1.0, p), rot: lerp(0.035, 0, p) });
}
function sceneStorm(g, t) {
  if (t >= 6.0) return;
  const cam = stormCam(t), tf = Math.min(t, K.freeze);
  cam.apply(g);
  const trem = seg(tf, 3.5, 4.0) * 2.4;
  for (const c of CARDS) {
    if (tf < c.t) continue;
    const d = tf - c.t, p = clamp(d / 0.24);
    let dx = 0, dy = 0, s = 1;
    if (c.kind === 0) dy = -38 * (1 - E.back(p, 2.2));
    else if (c.kind === 1) dx = 110 * (1 - eo(p));
    else s = lerp(0.9, 1, E.back(p, 2));
    dx += Math.sin(t * 61 + c.i) * trem; dy += Math.cos(t * 53 + c.i * 2) * trem;
    // collapse when the click ring passes
    const dist = Math.hypot(c.x - TILE.x, c.y - TILE.y), tc = K.click + dist / 2600;
    const pc = seg(t, tc, tc + 0.22);
    if (pc >= 1) continue;
    const cc = { ...c, x: c.x + dx, y: c.y + dy };
    squash(g, cc.x, cc.y, pc, () => card(g, cc, d, s));
  }
  // the tile, the cursor, the click
  if (t >= K.tile) {
    const pt = E.back(seg(t, K.tile, K.tile + 0.25), 2), press = t >= 4.96 && t < 5.04 ? 0.9 : 1;
    const rel = t >= 5.04 ? 1 - (1 - spring(t - 5.04, 9, 0.4)) * 0.1 : press;
    const s = TILE.s * pt * rel, pin = seg(t, K.click, K.click + 0.2);
    squash(g, TILE.x, TILE.y, pin, () => {
      E.panel(g, TILE.x - s / 2, TILE.y - s / 2, s, s, { r: s * 0.26, fill: PAL.surf3 });
      E.logo(g, LOGO, TILE.x, TILE.y, s * 1.15, 1);
      if (t > 4.6) { g.save(); g.strokeStyle = E.rgba(PAL.accent, 0.7 * seg(t, 4.6, 4.9)); g.lineWidth = 2; g.shadowColor = PAL.accent; g.shadowBlur = 20; E.rr(g, TILE.x - s / 2, TILE.y - s / 2, s, s, s * 0.26); g.stroke(); g.restore(); }
    });
    if (t >= 4.2 && t < 5.6) {
      const p = seg(t, 4.2, 4.72), from = { x: 860, y: 1330 }, to = { x: TILE.x + 18, y: TILE.y + 14 };
      const q = E.curve(from, to, eio(p), 0.18, 1.0);
      let sx = 1, sy = 1;
      if (t >= 4.72 && t < 4.96) { const w = ei(seg(t, 4.72, 4.96)); sx = 1 - 0.12 * w; sy = 1 + 0.18 * w; q.y -= 10 * w; }
      else if (t >= 4.96 && t < 5.04) { sx = 1.25; sy = 0.72; }
      else if (t >= 5.04) { const k = spring(t - 5.04, 8, 0.35); sx = lerp(1.25, 1, k); sy = lerp(0.72, 1, k); }
      const a = 1 - seg(t, 5.3, 5.6);
      if (p < 1) { const pts = []; for (let k = 0; k < 9; k++) pts.push(Object.values(E.curve(from, to, eio(clamp(p - k * 0.03)), 0.18, 1.0))); E.trail(g, pts.reverse(), { width: 5, alpha: 0.6 }); }
      E.pointer(g, q.x, q.y, 1.25, { sx, sy, alpha: a });
    }
    if (t >= K.click && t < K.click + 0.7) {   // the ring
      const r = (t - K.click) * 2600; g.save(); g.strokeStyle = E.rgba(PAL.accent, 0.55 * (1 - seg(t, K.click, K.click + 0.7))); g.lineWidth = 3; g.shadowColor = PAL.accent; g.shadowBlur = 24;
      g.beginPath(); g.arc(TILE.x, TILE.y, r, 0, TAU); g.stroke(); g.restore();
    }
  }
  g.setTransform(1, 0, 0, 1, 0, 0);
}
/** logo with a light-sweep reveal (unlit at base) */
function logoReveal(g, cx, cy, size, p, base = 0.07) {
  const [c, t] = E.buf('lr', 1024, 1024);
  t.drawImage(LOGO, 0, 0, 1024, 1024); t.globalCompositeOperation = 'destination-in';
  const m = t.createRadialGradient(512, 512, 330, 512, 512, 512); m.addColorStop(0, 'rgba(0,0,0,1)'); m.addColorStop(1, 'rgba(0,0,0,0)'); t.fillStyle = m; t.fillRect(0, 0, 1024, 1024);
  const [c1, t1] = E.buf('lr1', 1024, 1024); t1.drawImage(c, 0, 0);
  if (p < 1) {
    t1.globalCompositeOperation = 'destination-in';
    const L = 1024 * 1.5, soft = 420, front = -soft + p * (L + soft * 2), ca = Math.cos(0.62), sa = Math.sin(0.62);
    const p0 = [512 - ca * L / 2, 512 - sa * L / 2], at = d => [p0[0] + ca * d, p0[1] + sa * d];
    const A = at(front - soft), B = at(front); const gr = t1.createLinearGradient(A[0], A[1], B[0], B[1]);
    gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); t1.fillStyle = gr; t1.fillRect(0, 0, 1024, 1024);
  }
  g.save(); g.globalCompositeOperation = 'lighten';
  g.globalAlpha = base; g.drawImage(c, cx - size / 2, cy - size / 2, size, size);
  g.globalAlpha = 1; g.drawImage(c1, cx - size / 2, cy - size / 2, size, size); g.restore();
}
function sceneReveal(g, t) {
  if (t < K.click || t >= 9.75) return;
  const grow = E.back(seg(t, K.click, K.click + 0.6), 1.3), size = lerp(TILE.s * 1.15, 760, grow);
  const pout = seg(t, 9.5, 9.72);
  squash(g, CX, 820, pout, () => {
    const lit = seg(t, K.sweep0, K.sweep1);
    logoReveal(g, CX, lerp(TILE.y, 820, grow), size, lit, lerp(0.35, 0.07, seg(t, K.click, K.click + 0.25)));
  });
  const ph = seg(t, K.head3, K.head3 + 0.2), hout = seg(t, 9.28, 9.5);
  if (ph > 0) squash(g, CX, 1290, hout, () => E.text(g, 'حكايتك… بكل أناقة', CX, 1290 + (1 - eo(ph)) * 14, { px: 80, wt: 800, alpha: eo(ph) }));
}

// ───────── chapter windows
const WIN = { x: 60, y: 290, w: 880, h: 1110 };
const DESIGN_LBL = ['من فكرة على ورقة… لهوية كاملة', 'هوية بصرية متناسقة', 'الألوان لي تشبهك', 'تصميم قبل كل طباعة'];
function sceneDesign(g, t) {
  const a = K.design, b = K.print;
  life(g, t, a, b, WIN, () => {
    const dx = lerp(14, -14, ss(seg(t, a, b)));
    g.save(); g.translate(dx, 0);
    E.windowBox(g, WIN.x, WIN.y, WIN.w, WIN.h, { title: 'تصميم', code: '01/04' });
    const P = { x: 80, y: 374, w: 840, h: 640 };
    E.panel(g, P.x, P.y, P.w, P.h, { r: 18, fill: '#0B0D12', shadow: 0 });
    const tw = 190, gap = 26, ty = 1150;
    const tabR = i => ({ x: 80 + 840 - tw - i * (tw + gap), y: ty, w: tw, h: tw });
    // preview stack: each new image expands out of its tab
    for (let i = 0; i < 4; i++) {
      if (t < PREV[i]) break;
      const r = E.expand(tabR(i), P, eo(seg(t, PREV[i], PREV[i] + 0.32)));
      E.pic(g, im(i + 1), r.x, r.y, r.w, r.h, { r: 18 });
    }
    const cur = PREV.filter(x => t >= x).length - 1;
    if (cur >= 0) {
      const pl = seg(t, PREV[cur] + 0.1, PREV[cur] + 0.3);
      E.text(g, DESIGN_LBL[cur], 920, 1076, { px: 38, wt: 700, align: 'right', alpha: eo(pl) });
      E.mono(g, `0${cur + 1}/04`, 80, 1078, { px: 24, color: PAL.mute, align: 'left', alpha: eo(pl) });
    }
    for (let i = 0; i < 4; i++) {
      if (t < TABS[i]) continue;
      const p = seg(t, TABS[i], TABS[i] + 0.24), r = tabR(i);
      g.save(); g.translate(120 * (1 - eo(p)) * -1, 0); g.globalAlpha = clamp(p * 3);
      E.pic(g, im(i + 1), r.x, r.y, r.w, r.h, { r: 16, bright: i === cur ? 1 : 0.55 });
      if (i === cur) { g.strokeStyle = PAL.accent; g.lineWidth = 3; g.shadowColor = PAL.accent; g.shadowBlur = 16; E.rr(g, r.x - 1, r.y - 1, r.w + 2, r.h + 2, 17); g.stroke(); }
      g.restore();
    }
    g.restore();
  }, { from: { x: CX - 190, y: 820 - 190, w: 380, h: 380 } });
}
const MATS = ['زجاج', 'خشب', 'جلد', 'معدن', 'أكريليك'];
function scenePrint(g, t) {
  const a = K.print, b = K.prod;
  life(g, t, a, b, WIN, () => {
    const s = lerp(1, 1.03, ss(seg(t, a, b)));
    g.save(); g.translate(CX, 845); g.scale(s, s); g.translate(-CX, -845);
    E.windowBox(g, WIN.x, WIN.y, WIN.w, WIN.h, { title: 'طباعة UV على أي سطح', code: '02/04' });
    E.lightReveal(g, im(5), 80, 374, 840, 840, seg(t, K.uv0, K.uv1), { angle: Math.PI, base: 0.07, tint: '190,205,255', glint: 0.2 });
    // material chips, RTL, land on beats
    g.save(); g.font = E.font(30, 600); g.direction = 'rtl';
    const ws = MATS.map(m => g.measureText(m).width + 42), gap = 16, total = ws.reduce((x, y) => x + y, 0) + gap * (ws.length - 1); g.restore();
    let x = CX + total / 2;
    MATS.forEach((m, i) => {
      const w = ws[i], cx = x - w / 2; x -= w + gap;
      if (t < CHIPS[i]) return;
      const p = seg(t, CHIPS[i], CHIPS[i] + 0.22), on = 1 - seg(t, CHIPS[i] + 0.1, CHIPS[i] + 0.7);
      E.chip(g, m, cx, 1270 - 34 * (1 - E.back(p, 2.2)), { px: 30, a: clamp(p * 4), on });
    });
    if (t >= CODES) {
      const p = seg(t, CODES, CODES + 0.22);
      E.chip(g, '60×90 cm', CX + 150, 1346 - 30 * (1 - E.back(p, 2)), { px: 24, fam: 'mono', a: clamp(p * 4), wt: 500 });
      E.chip(g, 'CMYK+W+V', CX - 150, 1346 - 30 * (1 - E.back(p, 2)), { px: 24, fam: 'mono', a: clamp(p * 4), wt: 500 });
    }
    g.restore();
  });
}
const ROWS = [
  { img: 6, title: 'كارطات فيزيت', code: 'A3+', col: PAL.blue },
  { img: 8, title: 'ستيكرز مقصوصة', code: 'CUT', col: PAL.purple },
  { img: 7, title: 'تيشرتات وكاسكيطات', code: '1 → 1000+', col: PAL.magenta },
];
function sceneProducts(g, t) {
  if (t < K.prod || t >= K.num) return;
  const O = { x: CX, y: 845 };
  ROWS.forEach((r, i) => {
    const y = 330 + i * 370, R = { x: 60, y, w: 880, h: 330 }, land = LAND[i], fly0 = land - 0.4;
    const pin = seg(t, K.prod + i * 0.12, K.prod + i * 0.12 + 0.24), pout = seg(t, PUTROW[i], PUTROW[i] + 0.22);
    if (pin <= 0 || pout >= 1) return;
    squash(g, CX, y + 165, pout, () => {
      g.save(); g.translate(CX, y + 165); g.scale(lerp(0.96, 1, E.back(pin, 2)), lerp(0.96, 1, E.back(pin, 2))); g.translate(-CX, -(y + 165));
      const filled = t >= land;
      if (filled) E.panel(g, R.x, R.y, R.w, R.h, { r: 26, alpha: clamp(pin * 3) });
      else { g.save(); g.globalAlpha = clamp(pin * 3); g.setLineDash([8, 8]); g.strokeStyle = 'rgba(255,255,255,.14)'; g.lineWidth = 1.5; E.rr(g, R.x + 0.5, R.y + 0.5, R.w - 1, R.h - 1, 26); g.stroke(); g.restore(); }
      const T = { x: 760, y: y + 165 }, sz = 300;
      if (filled) {
        E.pic(g, im(r.img), T.x - sz / 2, T.y - sz / 2, sz, sz, { r: 18 });
        const pl = seg(t, land + 0.05, land + 0.3);
        E.text(g, r.title, 580, y + 135, { px: 44, wt: 800, align: 'right', alpha: eo(pl) });
        E.mono(g, r.code, 580, y + 205, { px: 30, align: 'right', color: PAL.dim, alpha: eo(pl) });
        E.check(g, 130, y + 165, 34, seg(t, land + 0.22, land + 0.5));
      }
      g.restore();
    });
    if (t >= fly0 && t < land + 0.05) {   // the flight, curved, with a trail in its category colour
      const p = seg(t, fly0, land), from = O, to = { x: 760, y: y + 165 };
      const pos = E.curve(from, to, p, 0.28, 1.2), sz = lerp(110, 300, eo(p));
      const pts = []; for (let k = 8; k >= 0; k--) { const q = E.curve(from, to, clamp(p - k * 0.04), 0.28, 1.2); pts.push([q.x, q.y]); }
      E.trail(g, pts, { color: r.col, width: 10, alpha: 0.8 });
      E.pic(g, im(r.img), pos.x - sz / 2, pos.y - sz / 2, sz, sz, { r: 18 });
    }
  });
}
// ───────── S7 the number
function sceneNumber(g, t) {
  if (t < K.num || t >= K.signs) return;
  const s = '3.20', px = 380, y = 1000;
  g.save(); g.font = E.font(px, 600, 'disp'); const ws = [...s].map(c => g.measureText(c).width + -0.045 * px); g.restore();
  const total = ws.reduce((a, b) => a + b, 0) + 0.045 * px, zx = CX - total / 2 + ws.slice(0, 3).reduce((a, b) => a + b, 0) + (ws[3] + 0.045 * px) / 2, zy = y - px * 0.36;
  const dz = t < K.dive ? 1 : Math.exp(Math.log(16) * ei(seg(t, K.dive, K.dive + 0.7)));
  if (dz < 15.5 && t < K.facade + 0.14) {
    g.save(); g.translate(zx, zy); g.scale(dz, dz); g.translate(-zx, -zy);
    E.scramble(g, s, CX, y, t, LOCKS, { px, color: PAL.accent, glowC: E.rgba(PAL.accent, 0.5) });
    const pu = seg(t, 26.3, 26.5);
    E.text(g, 'متر', CX, y + 110 - (1 - eo(pu)) * 12, { px: 64, wt: 700, color: PAL.dim, alpha: eo(pu) });
    const pl = seg(t, 25.7, 25.9);
    E.text(g, 'طباعة بالحجم الكبير', CX, 660, { px: 36, wt: 600, color: PAL.mute, alpha: eo(pl) });
    g.restore();
  }
  // match cut: the facade expands out of the zero
  if (t >= K.facade) {
    const R = { x: 60, y: 330, w: 880, h: 880 };
    const pout = seg(t, K.signs - 0.0, K.signs + 0.22);
    const r = E.expand({ x: CX - 20, y: 900, w: 40, h: 40 }, R, eo(seg(t, K.facade, K.facade + 0.35)));
    E.pic(g, im(10), r.x, r.y, r.w, r.h, { r: 22 });
    if (t > K.facade + 0.3) E.chip(g, '3.20 m', R.x + 120, R.y + 60, { px: 28, fam: 'mono', wt: 600, a: seg(t, K.facade + 0.3, K.facade + 0.5), on: 1 });
  }
}
// ───────── S8 signs: light from the top, whip pull-out to the roll-up
function sceneSigns(g, t) {
  if (t < K.signs || t >= K.digi) return;
  // facade collapses (overlap)
  if (t < K.signs + 0.22) squash(g, CX, 770, seg(t, K.signs, K.signs + 0.22), () => E.pic(g, im(10), 60, 330, 880, 880, { r: 22 }));
  const pw = eo(seg(t, K.whip, K.whip + 0.5));
  const cam = E.camera({ x: CX, y: lerp(860, 1350, pw), zoom: lerp(1, 0.56, pw) });
  const A = { x: 60, y: 420, w: 880, h: 880 }, B = { x: 60, y: 1340, w: 880, h: 880 };
  const pout = seg(t, K.digi - 0.22, K.digi);
  squash(g, CX, 960, pout, () => {
    cam.apply(g);
    if (t >= 29.6) {
      const r = E.expand({ x: CX - 4, y: 860 - 2, w: 8, h: 4 }, A, eo(seg(t, 29.6, 29.95)));
      g.save(); withRect(g, A, r, () => E.lightReveal(g, im(9), A.x, A.y, A.w, A.h, seg(t, K.sign0, K.sign1), { angle: Math.PI / 2, base: 0.08, tint: '255,238,215', glint: 0.18, r: 22 })); g.restore();
    }
    if (t >= K.whip - 0.05) E.lightReveal(g, im(11), B.x, B.y, B.w, B.h, seg(t, K.whip, K.whip + 0.7), { angle: Math.PI / 2, base: 0.1, glint: 0.15, r: 22 });
    g.setTransform(1, 0, 0, 1, 0, 0);
    // labels in screen space, at the projected rect corners
    const prj = (x, y) => ({ x: E.W / 2 + (x - cam.x) * cam.zoom, y: E.H / 2 + (y - cam.y) * cam.zoom });
    const a1 = seg(t, 30.6, 30.85), a2 = seg(t, 32.0, 32.25);
    const pa = prj(A.x + A.w, A.y), pb = prj(B.x + B.w, B.y);
    if (a1 > 0) { const w = E.measure(g, 'لافتات مضوّية', 30, 700) + 42; E.chip(g, 'لافتات مضوّية', pa.x - w / 2 - 22, pa.y + 46, { px: 30, wt: 700, a: a1, on: 1 }); }
    if (a2 > 0) { const w = E.measure(g, 'رول أب · ستاندات', 30, 700) + 42; E.chip(g, 'رول أب · ستاندات', pb.x - w / 2 - 22, pb.y + 46, { px: 30, wt: 700, a: a2, on: 1 }); }
  });
  g.setTransform(1, 0, 0, 1, 0, 0);
}
// ───────── S9 digital: video timeline + web page built from blocks
const VW = { x: 60, y: 300, w: 880, h: 520 }, WW = { x: 60, y: 860, w: 880, h: 540 };
function sceneDigital(g, t) {
  if (t < K.digi || t >= K.snapFly) return;
  const s = lerp(1, 1.05, ss(seg(t, K.digi, K.snapFly)));
  g.save(); g.translate(CX, 850); g.scale(s, s); g.translate(-CX, -850);
  life(g, t, K.digi, 36.55, VW, () => {
    E.windowBox(g, VW.x, VW.y, VW.w, VW.h, { title: 'موشن ديزاين', code: '4K' });
    const frames = [{ w: 300, h: 169, l: '16:9' }, { w: 132, h: 234, l: '9:16' }, { w: 200, h: 200, l: '1:1' }];
    let x = 900; const cy = 520;
    frames.forEach((f, i) => {
      const fx = x - f.w, p = seg(t, 33.9 + i * 0.25, 34.15 + i * 0.25); x = fx - 46;
      if (p <= 0) return;
      g.save(); g.globalAlpha = clamp(p * 3);
      const yy = cy - f.h / 2 - 20 * (1 - E.back(p, 2));
      E.panel(g, fx, yy, f.w, f.h, { r: 12, fill: '#0B0D12', shadow: 0.5 });
      g.save(); E.rr(g, fx, yy, f.w, f.h, 12); g.clip();
      const k = 0.55 + 0.08 * Math.sin((t - 34) * 3 + i);
      E.logo(g, LOGO, fx + f.w / 2, yy + f.h / 2, Math.min(f.w, f.h) * 1.25 * k / 0.55 * 0.62, 1);
      g.restore();
      E.mono(g, f.l, fx + f.w / 2, yy + f.h + 28, { px: 22, color: PAL.dim });
      g.restore();
    });
    // track + clips + playhead
    const ty = 730; g.fillStyle = 'rgba(255,255,255,.06)'; E.rr(g, 100, ty - 12, 800, 24, 12); g.fill();
    [[110, 300, .35], [320, 520, .2], [540, 690, .35], [710, 890, .2]].forEach(([a, b, al], i) => {
      const p = seg(t, 34.2 + i * 0.125, 34.4 + i * 0.125); if (p <= 0) return;
      g.fillStyle = E.rgba('#8A90A0', al + 0.1); E.rr(g, a, ty - 9, (b - a) * eo(p), 18, 9); g.fill();
    });
    const ph = lerp(100, 900, seg(t, 34.4, 36.4));
    if (t > 34.4) { g.fillStyle = PAL.accent; g.shadowColor = PAL.accent; g.shadowBlur = 14; g.fillRect(ph - 2, ty - 34, 4, 68); g.shadowBlur = 0; }
  });
  life(g, t, K.digi + 0.15, 36.55, WW, () => {
    E.windowBox(g, WW.x, WW.y, WW.w, WW.h, { title: 'مواقع ويب', code: 'www' });
    const B = BLOCKS, pop = i => E.back(seg(t, B[i], B[i] + 0.22), 2), al = i => clamp(seg(t, B[i], B[i] + 0.22) * 3);
    const X = 90, Wd = 820;
    // nav
    if (t >= B[0]) { g.save(); g.globalAlpha = al(0); g.fillStyle = 'rgba(255,255,255,.05)'; E.rr(g, X, 944, Wd, 56, 14); g.fill();
      const lh = 40, lw = lh * LOGOW.width / LOGOW.height; g.drawImage(LOGOW, X + Wd - lw - 22, 972 - lh / 2, lw, lh);
      [0, 1, 2].forEach(k => { g.fillStyle = 'rgba(255,255,255,.12)'; E.rr(g, X + 30 + k * 90, 966, 64, 12, 6); g.fill(); }); g.restore(); }
    // hero
    if (t >= B[1]) { const p = pop(1); g.save(); g.globalAlpha = al(1); g.translate(CX, 1090); g.scale(p, p); g.translate(-CX, -1090);
      E.pic(g, im(2), X, 1016, Wd, 150, { r: 14, bright: 0.45, fy: 0.3 });
      E.text(g, 'حكايتك… بكل أناقة', X + Wd - 30, 1091, { px: 40, wt: 800, align: 'right' }); g.restore(); }
    // three cards
    [6, 8, 9].forEach((n, k) => { const i = 2 + k; if (t < B[i]) return; const p = pop(i), cw = 258, cx = X + Wd - cw - k * (cw + 23);
      g.save(); g.globalAlpha = al(i); g.translate(cx + cw / 2, 1265); g.scale(p, p); g.translate(-(cx + cw / 2), -1265);
      E.pic(g, im(n), cx, 1184, cw, 150, { r: 12 }); g.fillStyle = 'rgba(255,255,255,.1)'; E.rr(g, cx + cw - 150, 1346, 150, 10, 5); g.fill(); g.restore(); });
    // button
    if (t >= B[5]) { const p = pop(5); g.save(); g.globalAlpha = al(5); const bw = 220, bx = X + Wd - bw;
      g.translate(X + 30 + bw / 2, 1091); g.scale(p, p); g.translate(-(X + 30 + bw / 2), -1091);
      g.fillStyle = PAL.accent; g.shadowColor = E.rgba(PAL.accent, 0.7); g.shadowBlur = 18; E.rr(g, X + 30, 1065, bw, 52, 26); g.fill(); g.shadowBlur = 0;
      E.text(g, 'اتصل بينا', X + 30 + bw / 2, 1093, { px: 28, wt: 800, color: '#04161A' });
      g.restore(); }
  });
  g.restore();
}
// ───────── S10 snap grid, S11 put-away + end card
const T_SZ = 250, T_GAP = 22, GX0 = CX - (3 * T_SZ + 2 * T_GAP) / 2, GY0 = 330;
const SLOT = k => { const r = Math.floor(k / 3), c = k % 3; return { x: GX0 + (2 - c) * (T_SZ + T_GAP) + T_SZ / 2, y: GY0 + r * (T_SZ + T_GAP) + T_SZ / 2 }; };
const START = Array.from({ length: 12 }, (_, k) => { const R = mulberry(k * 433 + 9), a = R() * TAU; return { x: CX + Math.cos(a) * (900 + R() * 300), y: 900 + Math.sin(a) * (1100 + R() * 200), rot: (R() - 0.5) * 1.2, s: 0.6 }; });
const LAST = 4;   // the tile that stays: centre of row 2
function sceneSnap(g, t) {
  if (t < K.snapFly || t >= K.end + 0.5) return;
  const z = lerp(1, 0.96, ss(seg(t, K.snap, K.put)));
  g.save(); g.translate(CX, 870); g.scale(z, z); g.translate(-CX, -870);
  for (let k = 11; k >= 0; k--) {
    const to = SLOT(k), p = seg(t, K.snapFly, K.snap);
    const P = E.flyPose(START[k], { x: to.x, y: to.y, rot: 0, s: 1 }, p, { over: 1.25 });
    const ri = k === LAST ? -1 : (11 - k) - (k > LAST ? 0 : 1);   // retract order: last image first, LAST stays
    const tr = ri >= 0 ? RETRACT[ri] : 1e9, pr = seg(t, tr, tr + 0.2);
    if (pr >= 1) continue;
    if (k === LAST && t >= K.endTile) continue;   // handed to the end card
    squash(g, P.x, P.y, pr, () => {
      g.save(); g.translate(P.x, P.y); g.rotate(P.rot); g.scale(P.s, P.s);
      E.pic(g, im(k + 1), -T_SZ / 2, -T_SZ / 2, T_SZ, T_SZ, { r: 18 });
      const flash = 1 - seg(t, K.snap, K.snap + 0.5);
      if (t >= K.snap && flash > 0) { g.strokeStyle = E.rgba(PAL.accent, flash); g.lineWidth = 3; g.shadowColor = PAL.accent; g.shadowBlur = 20; E.rr(g, -T_SZ / 2, -T_SZ / 2, T_SZ, T_SZ, 18); g.stroke(); }
      g.restore();
    });
  }
  g.restore();
  const ph = seg(t, K.snap + 0.1, K.snap + 0.3), hout = seg(t, K.put, K.put + 0.22);
  if (ph > 0) squash(g, CX, 238, hout, () => E.text(g, 'كلّش تحت سقف واحد', CX, 238 + (1 - eo(ph)) * 14, { px: 74, wt: 800, alpha: eo(ph) }));
}
const PHONES = ['0772 65 83 01', '0668 89 79 07', '0553 04 54 07'];
function sceneEnd(g, t) {
  if (t < K.endTile) return;
  // the last tile lights, then its logo expands into the end card
  const s0 = SLOT(LAST), z = 0.96, sx = CX + (s0.x - CX) * z, sy = 870 + (s0.y - 870) * z, ts = T_SZ * z;
  const grow = E.back(seg(t, K.end, K.end + 0.45), 1.2);
  const pTile = seg(t, K.end, K.end + 0.2);
  squash(g, sx, sy, pTile, () => {
    E.panel(g, sx - ts / 2, sy - ts / 2, ts, ts, { r: 18, fill: PAL.surf3 });
    g.save(); g.strokeStyle = PAL.accent; g.lineWidth = 3; g.shadowColor = PAL.accent; g.shadowBlur = 22; E.rr(g, sx - ts / 2, sy - ts / 2, ts, ts, 18); g.stroke(); g.restore();
  });
  E.logo(g, LOGO, lerp(sx, CX, grow), lerp(sy, 610, grow), lerp(ts * 1.1, 600, grow), 1);
  const row = (i, d) => seg(t, 42.0 + d, 42.22 + d);
  const ptl = row(0, 0);
  E.text(g, 'إشهار و حلول طباعة ذكية', CX, 950 + (1 - eo(ptl)) * 12, { px: 40, wt: 700, color: PAL.dim, alpha: eo(ptl) });
  PHONES.forEach((n, i) => {
    const p = row(i, 0.2 + i * 0.125); if (p <= 0) return;
    const y = 1052 + i * 74, dx = 60 * (1 - eo(p));
    g.save(); g.globalAlpha = clamp(p * 3); g.translate(-dx, 0);
    E.mono(g, n, i === 0 ? CX - 70 : CX, y, { px: 48, wt: 600, color: PAL.text });
    if (i === 0) E.chip(g, 'واتساب', CX + 210, y + 2, { px: 28, wt: 700, on: 1 });
    g.restore();
  });
  const pe = row(0, 0.8);
  E.mono(g, 'elegancestory19@gmail.com', CX, 1290 + (1 - eo(pe)) * 12, { px: 34, color: PAL.dim, alpha: eo(pe) });
  const pl = row(0, 0.95);
  if (pl > 0) { const sw = E.measure(g, 'سطيف', 44, 800); E.text(g, 'سطيف', CX, 1362 + (1 - eo(pl)) * 12, { px: 44, wt: 800, alpha: eo(pl) }); g.save(); g.globalAlpha = eo(pl); g.fillStyle = PAL.accent; g.shadowColor = PAL.accent; g.shadowBlur = 12; g.beginPath(); g.arc(CX + sw / 2 + 22, 1366, 7, 0, TAU); g.fill(); g.restore(); }
}

// ───────── captions
function captions(g, t) {
  for (const L of LINES) {
    if (!L.cap) continue; const [a, b] = L.cap;
    if (t < a || t >= b) continue;
    const ai = seg(t, a, a + 0.16), ao = 1 - seg(t, b - 0.12, b);
    E.toast(g, L.srt || L.say, Math.min(ai, ao), { dense: t < K.click ? 1 : 0 });
  }
}
export function subs() { return LINES.map(L => ({ t0: L.cap ? L.cap[0] : L.t0, t1: L.cap ? L.cap[1] : L.t1 + 0.4, text: L.srt || L.say })); }
export function texts(t) {
  const out = [];
  if (within(t, K.head3 + 0.2, 9.28)) out.push({ id: 'h3', text: 'حكايتك… بكل أناقة', x0: 200, y0: 1240, x1: 800, y1: 1340 });
  if (within(t, K.snap + 0.3, K.put)) out.push({ id: 'h10', text: 'كلّش تحت سقف واحد', x0: 180, y0: 190, x1: 820, y1: 290 });
  if (within(t, LOCKS[0], K.dive)) out.push({ id: 'num', text: '3.20', x0: 160, y0: 700, x1: 840, y1: 1010 });
  if (within(t, 42.2, DUR)) out.push({ id: 'end', text: 'إشهار و حلول طباعة ذكية', x0: 200, y0: 920, x1: 800, y1: 980 });
  return out;
}
export function events() {
  const ev = [];
  STORM.forEach((t, i) => ev.push({ t, type: 'storm', i }));
  ev.push({ t: K.click, type: 'click' });
  TABS.forEach(t => ev.push({ t, type: 'tab' })); CHIPS.forEach(t => ev.push({ t, type: 'chip' }));
  LAND.forEach(t => ev.push({ t, type: 'land' })); LOCKS.forEach(t => ev.push({ t, type: 'digit' }));
  BLOCKS.forEach(t => ev.push({ t, type: 'block' })); ev.push({ t: K.snap, type: 'snap' }); RETRACT.forEach(t => ev.push({ t, type: 'retract' }));
  return ev.sort((a, b) => a.t - b.t);
}

export function renderFilm(g, t, o = {}) {
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  E.bg(g); E.grid(g, { ox: 12, oy: 0 });
  sceneStorm(g, t); sceneReveal(g, t); sceneDesign(g, t); scenePrint(g, t); sceneProducts(g, t);
  sceneNumber(g, t); sceneSigns(g, t); sceneDigital(g, t); sceneSnap(g, t); sceneEnd(g, t);
  g.setTransform(1, 0, 0, 1, 0, 0);
  E.vignette(g, 0.5);
  if (!o.nosub) captions(g, t);
}
